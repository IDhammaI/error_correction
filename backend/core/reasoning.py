from __future__ import annotations


def supports_deepseek_thinking(model_name: str | None) -> bool:
    normalized = (model_name or "").strip().lower()
    return normalized in {"deepseek-v4-flash", "deepseek-v4-pro"}


def bind_reasoning_options(model, *, provider: str, model_name: str | None, deep_think: bool):
    if not deep_think:
        return model

    if provider == "openai" and supports_deepseek_thinking(model_name):
        return model.bind(
            reasoning_effort="high",
            extra_body={"thinking": {"type": "enabled"}},
        )

    return model
