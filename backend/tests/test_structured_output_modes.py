from types import SimpleNamespace

from agents.error_correction import agent
from agents.error_correction.schemas import CorrectionResult


class DummyProviderConfig:
    base_url = "https://api.example.test"

    def __init__(self, *, supports_function_calling=True):
        self.supports_function_calling = supports_function_calling

    def resolve_model_name(self, model_name=None, *, use_light=False):
        return model_name or "example-model"


def _correction_payload_json():
    return """
```json
{
  "corrected_questions": [
    {
      "question_id": "1",
      "question_type": "选择题",
      "content_blocks": [{"block_type": "text", "content": "题干"}],
      "knowledge_tags": ["力学"],
      "corrections_applied": ["补全知识点标签"]
    }
  ]
}
```
"""


def test_prompt_json_mode_validates_model_json(monkeypatch):
    class FakeModel:
        def invoke(self, messages):
            return SimpleNamespace(content=_correction_payload_json())

    monkeypatch.setattr(agent, "_init_model", lambda **kwargs: FakeModel())
    monkeypatch.setattr(
        type(agent.settings),
        "get_provider",
        lambda self, provider: DummyProviderConfig(supports_function_calling=False),
    )
    monkeypatch.setattr(
        agent,
        "_resolve_structured_mode",
        lambda **kwargs: agent.STRUCTURED_PROMPT_JSON,
    )

    result = agent._invoke_structured(
        prompt="处理题目",
        provider="openai",
        model_name="deepseek-v4-flash",
        temperature=0.0,
        schema=CorrectionResult,
        system_prompt_fallback="只输出 JSON",
        cache_key="correction",
        agent_factory=None,
    )

    assert result.corrected_questions[0].question_id == "1"
    assert result.corrected_questions[0].knowledge_tags == ["力学"]


def test_structured_mode_falls_back_to_prompt_json(monkeypatch):
    class FailingRunnable:
        def invoke(self, messages):
            raise RuntimeError("This response_format type is unavailable now")

    class FakeModel:
        def with_structured_output(self, schema, **kwargs):
            return FailingRunnable()

        def invoke(self, messages):
            return SimpleNamespace(content=_correction_payload_json())

    monkeypatch.setattr(agent, "_init_model", lambda **kwargs: FakeModel())
    monkeypatch.setattr(
        type(agent.settings),
        "get_provider",
        lambda self, provider: DummyProviderConfig(supports_function_calling=False),
    )
    monkeypatch.setattr(
        agent,
        "_resolve_structured_mode",
        lambda **kwargs: agent.STRUCTURED_PROVIDER,
    )

    result = agent._invoke_structured(
        prompt="处理题目",
        provider="openai",
        model_name="deepseek-v4-flash",
        temperature=0.0,
        schema=CorrectionResult,
        system_prompt_fallback="只输出 JSON",
        cache_key="correction",
        agent_factory=None,
    )

    assert result.corrected_questions[0].question_id == "1"


def test_probe_selects_json_mode_when_stricter_modes_fail(monkeypatch):
    class ProbeRunnable:
        def __init__(self, schema, method):
            self.schema = schema
            self.method = method

        def invoke(self, messages):
            if self.method in {"json_schema", "function_calling"}:
                raise RuntimeError(f"{self.method} unsupported")
            return self.schema.model_validate({"ok": True})

    class FakeModel:
        def with_structured_output(self, schema, **kwargs):
            return ProbeRunnable(schema, kwargs.get("method"))

    cfg = DummyProviderConfig(supports_function_calling=True)
    agent._structured_mode_cache.clear()
    monkeypatch.setattr(agent, "_init_model", lambda **kwargs: FakeModel())

    mode = agent._resolve_structured_mode(
        provider="openai",
        model_name="example-model",
        cfg=cfg,
        candidate_modes=[
            agent.STRUCTURED_PROVIDER,
            agent.STRUCTURED_TOOL,
            agent.STRUCTURED_JSON_MODE,
            agent.STRUCTURED_PROMPT_JSON,
        ],
    )

    assert mode == agent.STRUCTURED_JSON_MODE


def test_tool_mode_uses_structured_model_without_agent_loop(monkeypatch):
    class ToolRunnable:
        def __init__(self, schema, method):
            self.schema = schema
            self.method = method

        def invoke(self, messages):
            assert self.method == "function_calling"
            return self.schema.model_validate(
                {
                    "corrected_questions": [
                        {
                            "question_id": "1",
                            "question_type": "选择题",
                            "content_blocks": [{"block_type": "text", "content": "题干"}],
                            "knowledge_tags": ["力学"],
                            "corrections_applied": ["补全知识点标签"],
                        }
                    ]
                }
            )

    class FakeModel:
        def with_structured_output(self, schema, **kwargs):
            return ToolRunnable(schema, kwargs.get("method"))

    def fail_agent_factory(**kwargs):
        raise AssertionError("Tool mode should not enter create_agent/ToolStrategy")

    monkeypatch.setattr(agent, "_init_model", lambda **kwargs: FakeModel())

    result = agent._invoke_structured_by_mode(
        mode=agent.STRUCTURED_TOOL,
        prompt="处理题目",
        provider="openai",
        model_name="example-model",
        temperature=0.0,
        schema=CorrectionResult,
        system_prompt_fallback="只输出 JSON",
        cache_key="correction",
        agent_factory=fail_agent_factory,
    )

    assert result.corrected_questions[0].question_id == "1"
