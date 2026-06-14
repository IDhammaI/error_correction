import argparse
import json
import logging
import random
from dataclasses import dataclass

from sqlalchemy.orm import joinedload

from core.config import settings
from db import SessionLocal, init_db
from db.models import Question, QuestionTagMapping, UploadBatch

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class QueryItem:
    question_id: int
    user_id: int | None
    project_id: int | None
    subject: str
    tags: frozenset[str]
    query_text: str


def _safe_json_loads(value, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return fallback


def _blocks_text(content_json: str) -> str:
    blocks = _safe_json_loads(content_json, [])
    parts: list[str] = []
    for block in blocks or []:
        if isinstance(block, dict):
            content = (block.get("content") or block.get("text") or "").strip()
            if content:
                parts.append(content)
        elif isinstance(block, str):
            content = block.strip()
            if content:
                parts.append(content)
    return "\n".join(parts).strip()


def _options_text(options_json: str) -> str:
    options = _safe_json_loads(options_json, [])
    parts: list[str] = []
    if isinstance(options, dict):
        options = list(options.values())
    for opt in options or []:
        if isinstance(opt, dict):
            label = str(opt.get("label") or "").strip()
            content = str(opt.get("content") or "").strip()
            if not (label or content):
                continue
            parts.append(f"{label}. {content}" if label else content)
        elif isinstance(opt, str):
            content = opt.strip()
            if content:
                parts.append(content)
    return "\n".join(parts).strip()


def _build_query_text(q: Question) -> str:
    subject = q.batch.subject if q.batch else ""
    tags: list[str] = []
    for mapping in q.tags or []:
        if mapping.tag and mapping.tag.tag_name:
            tags.append(mapping.tag.tag_name)
    content_text = _blocks_text(q.content_json)
    options_text = _options_text(q.options_json)
    parts: list[str] = []
    if subject:
        parts.append(f"科目：{subject}")
    if q.question_type:
        parts.append(f"题型：{q.question_type}")
    if tags:
        parts.append(f"知识点：{'、'.join(tags)}")
    if content_text:
        parts.append(f"题干：{content_text}")
    if options_text:
        parts.append(f"选项：{options_text}")
    text = "\n".join(parts).strip()
    return text[:4000]


def _load_queries(*, limit: int, seed: int | None) -> list[QueryItem]:
    with SessionLocal() as db:
        questions = (
            db.query(Question)
            .options(joinedload(Question.batch), joinedload(Question.tags).joinedload(QuestionTagMapping.tag))
            .order_by(Question.id.desc())
            .all()
        )

    items: list[QueryItem] = []
    if questions:
        for q in questions:
            subject = q.batch.subject if q.batch else ""
            tags = []
            for mapping in q.tags or []:
                if mapping.tag and mapping.tag.tag_name:
                    tags.append(mapping.tag.tag_name)
            items.append(
                QueryItem(
                    question_id=q.id,
                    user_id=q.user_id,
                    project_id=q.project_id,
                    subject=subject or "",
                    tags=frozenset(tags),
                    query_text=_build_query_text(q),
                )
            )
    else:
        runs_dir = settings.runs_dir
        candidates = sorted(runs_dir.glob("**/questions.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        latest = candidates[0] if candidates else None
        if latest and latest.exists():
            payload = _safe_json_loads(latest.read_text(encoding="utf-8"), [])
            if isinstance(payload, list):
                for row in payload:
                    if not isinstance(row, dict):
                        continue
                    qid_raw = row.get("question_id")
                    try:
                        qid = int(qid_raw)
                    except (TypeError, ValueError):
                        qid = len(items) + 1
                    tags = row.get("knowledge_tags") or []
                    if not isinstance(tags, list):
                        tags = []
                    content_blocks = row.get("content_blocks") or []
                    options = row.get("options") or []
                    content_json = json.dumps(content_blocks, ensure_ascii=False)
                    options_json = json.dumps(options, ensure_ascii=False)
                    q_stub = Question(
                        id=qid,
                        user_id=None,
                        project_id=None,
                        question_type=row.get("question_type") or "",
                        content_json=content_json,
                        options_json=options_json,
                    )
                    q_stub.batch = UploadBatch(subject="")
                    q_stub.tags = []
                    items.append(
                        QueryItem(
                            question_id=qid,
                            user_id=None,
                            project_id=None,
                            subject="",
                            tags=frozenset(str(t).strip() for t in tags if str(t).strip()),
                            query_text=_build_query_text(q_stub),
                        )
                    )

    if seed is not None:
        rnd = random.Random(seed)
        rnd.shuffle(items)
    if limit > 0:
        items = items[:limit]
    return items


def _group_relevance(items: list[QueryItem]) -> dict[tuple[int | None, int | None], dict[str, set[int]]]:
    by_scope: dict[tuple[int | None, int | None], dict[str, set[int]]] = {}
    for item in items:
        key = (item.user_id, item.project_id)
        tag_map = by_scope.setdefault(key, {})
        for tag in item.tags:
            tag_map.setdefault(tag, set()).add(item.question_id)
    return by_scope


def _relevant_ids(
    item: QueryItem,
    *,
    tag_index: dict[tuple[int | None, int | None], dict[str, set[int]]],
) -> set[int]:
    key = (item.user_id, item.project_id)
    tag_map = tag_index.get(key, {})
    relevant: set[int] = set()
    for tag in item.tags:
        relevant.update(tag_map.get(tag, set()))
    relevant.discard(item.question_id)
    return relevant


def _hash_retrieve_ids(*, query_text: str, user_id: int | None, project_id: int | None, top_k: int) -> list[int]:
    from db import crud

    with SessionLocal() as db:
        matches = crud.find_questions_by_natural_language(
            db,
            query_text=query_text,
            limit=top_k,
            user_id=user_id,
            project_id=project_id,
        )
    ids: list[int] = []
    for match in matches:
        q = match.get("question")
        if q and getattr(q, "id", None) is not None:
            ids.append(q.id)
    return ids


def _hash_retrieve_ids_in_memory(
    *,
    query_index: int,
    items: list[QueryItem],
    vectors: list[list[float]],
    top_k: int,
) -> list[int]:
    query_vec = vectors[query_index]
    scored: list[tuple[int, float]] = []
    for idx, item in enumerate(items):
        if idx == query_index:
            continue
        score = sum(a * b for a, b in zip(query_vec, vectors[idx]))
        scored.append((item.question_id, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [qid for qid, _ in scored[:top_k]]


def _rag_retrieve_ids(*, query_text: str, user_id: int | None, project_id: int | None, top_k: int) -> list[int] | None:
    try:
        from core.rag import retrieve_context
    except Exception as e:
        logger.warning("RAG 模块不可用: %s", e)
        return None

    with SessionLocal() as db:
        results = retrieve_context(
            db,
            query=query_text,
            user_id=user_id,
            project_id=project_id,
            top_k=top_k,
        )
    return [int(r["source_id"]) for r in results if r.get("source_id") is not None]


def _evaluate(
    items: list[QueryItem],
    *,
    top_ks: list[int],
    method: str,
) -> dict:
    tag_index = _group_relevance(items)
    max_k = max(top_ks)

    use_in_memory_hash = False
    hash_vectors: list[list[float]] = []
    if method == "hash":
        with SessionLocal() as db:
            has_db_questions = bool(db.query(Question.id).limit(1).first())
        if not has_db_questions:
            from db.crud.questions import _hash_embedding
            use_in_memory_hash = True
            hash_vectors = [_hash_embedding(item.query_text) for item in items]

    valid = 0
    skipped_no_relevant = 0
    hit_counts = {k: 0 for k in top_ks}
    recall_sums = {k: 0.0 for k in top_ks}

    for idx, item in enumerate(items):
        relevant = _relevant_ids(item, tag_index=tag_index)
        if not relevant:
            skipped_no_relevant += 1
            continue

        if method == "hash":
            if use_in_memory_hash:
                retrieved = _hash_retrieve_ids_in_memory(
                    query_index=idx,
                    items=items,
                    vectors=hash_vectors,
                    top_k=max_k,
                )
            else:
                retrieved = _hash_retrieve_ids(
                    query_text=item.query_text,
                    user_id=item.user_id,
                    project_id=item.project_id,
                    top_k=max_k,
                )
        elif method == "rag":
            retrieved = _rag_retrieve_ids(
                query_text=item.query_text,
                user_id=item.user_id,
                project_id=item.project_id,
                top_k=max_k,
            )
            if retrieved is None:
                return {
                    "method": method,
                    "error": "RAG 不可用（导入失败或未配置 embedding）",
                }
        else:
            raise ValueError(f"unknown method: {method}")

        valid += 1
        for k in top_ks:
            topk = set(retrieved[:k])
            hit = bool(topk & relevant)
            if hit:
                hit_counts[k] += 1
            recall_sums[k] += (len(topk & relevant) / len(relevant))

    report = {
        "method": method,
        "total_queries": len(items),
        "evaluated_queries": valid,
        "skipped_no_relevant": skipped_no_relevant,
        "top_ks": top_ks,
        "hit_at_k": {},
        "recall_at_k": {},
    }
    if valid == 0:
        return {**report, "error": "没有可评测的样本（可能是没有知识点标签或只有单题）"}

    for k in top_ks:
        report["hit_at_k"][str(k)] = round(hit_counts[k] / valid, 4)
        report["recall_at_k"][str(k)] = round(recall_sums[k] / valid, 4)
    return report


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    parser = argparse.ArgumentParser(description="Recall@K（召回率）评测")
    parser.add_argument("--method", choices=["hash", "rag"], default="hash")
    parser.add_argument("--k", default="1,3,5,10", help="K 值列表，如 1,3,5,10")
    parser.add_argument("--limit", type=int, default=200, help="最多评测多少条 query（0 表示全部）")
    parser.add_argument("--seed", type=int, default=42, help="随机采样种子")
    args = parser.parse_args()

    init_db()

    top_ks = sorted({int(x) for x in str(args.k).split(",") if str(x).strip().isdigit() and int(x) > 0})
    if not top_ks:
        raise SystemExit("k 参数非法")

    items = _load_queries(limit=args.limit, seed=args.seed)
    report = _evaluate(items, top_ks=top_ks, method=args.method)

    print(f"DB: {settings.database_url}")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
