"""每日免费体验额度辅助逻辑。"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func

from core.config import settings
from db import crud
from db.models import QuotaUsageEvent

DEFAULT_DAILY_FREE_QUOTA = settings.daily_free_quota
QUOTA_EXCEEDED_CODE = "DAILY_FREE_QUOTA_EXCEEDED"
QUOTA_EXCEEDED_ERROR = "今日免费体验次数已用完"
QUOTA_ACTION_META = {
    "chat": {"label": "AI 对话", "unit": "次"},
    "erase": {"label": "擦除笔记", "unit": "次"},
    "split": {"label": "分割题目", "unit": "页"},
    "note": {"label": "整理笔记", "unit": "次"},
    "other": {"label": "其他操作", "unit": "次"},
}
QUOTA_DAILY_CHART_ACTIONS = ("chat", "erase", "split")


def _today_str() -> str:
    return datetime.utcnow().date().isoformat()


def _next_reset_at() -> str:
    next_day = datetime.utcnow().date() + timedelta(days=1)
    return f"{next_day.isoformat()}T00:00:00Z"


def _normalize_action_type(action_type: str | None) -> str:
    action = (action_type or "other").strip().lower()
    return action if action in QUOTA_ACTION_META else "other"


def _build_usage_summary(action_type: str, amount: int, summary: str | None = None) -> str:
    if summary:
        return summary
    meta = QUOTA_ACTION_META.get(action_type, QUOTA_ACTION_META["other"])
    if action_type == "split":
        return f"{meta['label']}（{amount}{meta['unit']}）"
    return meta["label"]


def _record_quota_usage_event(db, user, *, action_type: str, amount: int, summary: str | None = None) -> None:
    normalized_action = _normalize_action_type(action_type)
    normalized_amount = max(int(amount or 0), 0)
    if normalized_amount <= 0:
        return
    db.add(
        QuotaUsageEvent(
            user_id=user.id,
            action_type=normalized_action,
            amount=normalized_amount,
            summary=_build_usage_summary(normalized_action, normalized_amount, summary),
            quota_date=getattr(user, "daily_free_quota_date", None) or _today_str(),
        )
    )


def _get_quota_usage_stats(db, user, used: int) -> dict:
    quota_date = getattr(user, "daily_free_quota_date", None) or _today_str()
    rows = (
        db.query(
            QuotaUsageEvent.action_type,
            func.sum(QuotaUsageEvent.amount).label("amount"),
            func.count(QuotaUsageEvent.id).label("event_count"),
        )
        .filter(
            QuotaUsageEvent.user_id == user.id,
            QuotaUsageEvent.quota_date == quota_date,
        )
        .group_by(QuotaUsageEvent.action_type)
        .all()
    )
    breakdown_map = {
        row.action_type: {
            "action_type": row.action_type,
            "amount": int(row.amount or 0),
            "event_count": int(row.event_count or 0),
        }
        for row in rows
    }
    breakdown = []
    for action_type in ("chat", "erase", "split", "note", "other"):
        item = breakdown_map.get(action_type)
        if not item or item["amount"] <= 0:
            continue
        meta = QUOTA_ACTION_META[action_type]
        breakdown.append(
            {
                **item,
                "label": meta["label"],
                "unit": meta["unit"],
                "percent": round((item["amount"] / used) * 100) if used > 0 else 0,
            }
        )
    breakdown.sort(key=lambda item: item["amount"], reverse=True)

    recent_rows = (
        db.query(QuotaUsageEvent)
        .filter(
            QuotaUsageEvent.user_id == user.id,
            QuotaUsageEvent.quota_date == quota_date,
        )
        .order_by(QuotaUsageEvent.created_at.desc(), QuotaUsageEvent.id.desc())
        .limit(6)
        .all()
    )
    recent_events = []
    for row in recent_rows:
        meta = QUOTA_ACTION_META.get(row.action_type, QUOTA_ACTION_META["other"])
        recent_events.append(
            {
                "action_type": row.action_type,
                "label": meta["label"],
                "summary": row.summary or meta["label"],
                "amount": int(row.amount or 0),
                "unit": meta["unit"],
                "created_at": row.created_at.isoformat() + "Z" if row.created_at else None,
            }
        )

    return {
        "breakdown": breakdown,
        "recent_events": recent_events,
        "total_events": sum(item["event_count"] for item in breakdown),
        "daily_chart": _get_daily_usage_chart(db, user.id),
    }


def _get_daily_usage_chart(db, user_id: int, days: int = 14) -> dict:
    today = datetime.utcnow().date()
    normalized_days = max(int(days or 0), 1)
    start_date = today - timedelta(days=normalized_days - 1)
    start_date_str = start_date.isoformat()

    rows = (
        db.query(
            QuotaUsageEvent.quota_date,
            QuotaUsageEvent.action_type,
            func.sum(QuotaUsageEvent.amount).label("amount"),
        )
        .filter(
            QuotaUsageEvent.user_id == user_id,
            QuotaUsageEvent.quota_date >= start_date_str,
            QuotaUsageEvent.action_type.in_(QUOTA_DAILY_CHART_ACTIONS),
        )
        .group_by(QuotaUsageEvent.quota_date, QuotaUsageEvent.action_type)
        .all()
    )

    amount_map: dict[str, dict[str, int]] = {}
    for row in rows:
        day_map = amount_map.setdefault(row.quota_date, {})
        day_map[row.action_type] = int(row.amount or 0)

    chart_days = []
    cursor = start_date
    while cursor <= today:
        date_str = cursor.isoformat()
        item = {
            "date": date_str,
            "label": cursor.strftime("%m/%d"),
            "chat": int(amount_map.get(date_str, {}).get("chat", 0)),
            "erase": int(amount_map.get(date_str, {}).get("erase", 0)),
            "split": int(amount_map.get(date_str, {}).get("split", 0)),
        }
        item["total"] = item["chat"] + item["erase"] + item["split"]
        chart_days.append(item)
        cursor += timedelta(days=1)

    return {
        "days": chart_days,
        "range_days": normalized_days,
        "actions": [
            {
                "key": action_type,
                "label": QUOTA_ACTION_META[action_type]["label"],
                "unit": QUOTA_ACTION_META[action_type]["unit"],
            }
            for action_type in QUOTA_DAILY_CHART_ACTIONS
        ],
    }


def sync_daily_quota_state(db, user):
    """按当天日期修正用户额度状态。"""
    changed = False
    today = _today_str()
    target_quota = max(int(settings.daily_free_quota or DEFAULT_DAILY_FREE_QUOTA), 0)

    if getattr(user, "daily_free_quota", None) != target_quota:
        user.daily_free_quota = target_quota
        changed = True
    if getattr(user, "daily_free_used", None) is None:
        user.daily_free_used = 0
        changed = True

    if getattr(user, "daily_free_quota_date", None) != today:
        user.daily_free_quota_date = today
        user.daily_free_used = 0
        changed = True

    if changed:
        db.flush()
    return user


def get_daily_quota_snapshot(db, user) -> dict:
    """返回当前用户的额度信息，并在必要时按天重置。"""
    sync_daily_quota_state(db, user)
    quota = max(int(getattr(user, "daily_free_quota", DEFAULT_DAILY_FREE_QUOTA) or 0), 0)
    used = max(int(getattr(user, "daily_free_used", 0) or 0), 0)
    remaining = max(quota - used, 0)
    return {
        "daily_free_quota": quota,
        "daily_free_used": used,
        "remaining": remaining,
        "quota_date": user.daily_free_quota_date,
        "reset_at": _next_reset_at(),
        "usage_stats": _get_quota_usage_stats(db, user, used),
    }


def consume_daily_free_quota(
    db,
    user,
    amount: int = 1,
    *,
    action_type: str = "other",
    summary: str | None = None,
) -> dict:
    """扣减用户免费额度并返回最新快照。"""
    sync_daily_quota_state(db, user)
    normalized_amount = max(int(amount or 0), 0)
    user.daily_free_used = max(int(user.daily_free_used or 0), 0) + normalized_amount
    _record_quota_usage_event(
        db,
        user,
        action_type=action_type,
        amount=normalized_amount,
        summary=summary,
    )
    db.commit()
    db.refresh(user)
    return get_daily_quota_snapshot(db, user)


def build_quota_exceeded_payload(db, user, amount: int = 1) -> dict:
    quota = get_daily_quota_snapshot(db, user)
    required = max(int(amount or 1), 1)
    remaining = quota["remaining"]
    if required > 1 and remaining < required:
        error = f"本次操作需要 {required} 个额度，当前仅剩 {remaining} 个"
    else:
        error = QUOTA_EXCEEDED_ERROR
    return {
        "success": False,
        "error": error,
        "code": QUOTA_EXCEEDED_CODE,
        "quota": quota,
        "required_amount": required,
    }


def quota_exceeded_response(db, user, amount: int = 1):
    return build_quota_exceeded_payload(db, user, amount=amount), 429


def has_daily_free_quota(db, user, amount: int = 1) -> bool:
    quota = get_daily_quota_snapshot(db, user)
    required = max(int(amount or 1), 1)
    return quota["remaining"] >= required


def uses_server_provider(db, user_id: int | None, category: str) -> bool:
    """是否走服务器托管 provider。"""
    if not user_id:
        return True
    provider = crud.get_active_provider(db, user_id, category)
    return provider is None


def uses_server_llm(db, user_id: int | None, provider: str) -> bool:
    return uses_server_provider(db, user_id, provider)


def uses_server_llm_selection(
    provider_source: str | None,
    *,
    db=None,
    user_id: int | None = None,
    provider: str | None = None,
) -> bool:
    if provider_source == "system":
        return True
    if provider_source == "personal":
        return False
    if db is None or provider is None:
        return True
    return uses_server_llm(db, user_id, provider)


def uses_server_ocr(db, user_id: int | None) -> bool:
    return uses_server_provider(db, user_id, "paddleocr")
