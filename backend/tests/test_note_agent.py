from types import SimpleNamespace

from agents.note import agent


def _note_payload_json():
    return """
```json
{
  "title": "三角函数复习",
  "subject": "高中数学",
  "content_markdown": "# 三角函数\n\n- 诱导公式",
  "knowledge_tags": ["三角函数", "诱导公式"]
}
```
"""


def test_note_agent_falls_back_when_tool_choice_is_unsupported():
    class FailingRunnable:
        def invoke(self, messages):
            raise RuntimeError("Thinking mode does not support this tool_choice")

    class FakeModel:
        def with_structured_output(self, schema, **kwargs):
            assert kwargs.get("method") == "function_calling"
            return FailingRunnable()

        def invoke(self, messages):
            return SimpleNamespace(content=_note_payload_json())

    result = agent._invoke_once(
        FakeModel(),
        "原始 OCR 文本",
        provider="openai",
        supports_function_calling=True,
    )

    assert result.title == "三角函数复习"
    assert result.subject == "高中数学"
    assert result.knowledge_tags == ["三角函数", "诱导公式"]
