"""
correct_questions_node 合并逻辑的单元测试

不调用真实 LLM，只测试标记筛选 + 结果合并逻辑。
"""

import json
import os
from pathlib import Path
import shutil
from unittest.mock import patch
from src.workflow import correct_questions_node


def _work_dir(name):
    root = Path(__file__).resolve().parents[1] / "runtime_data" / "test_correct_node" / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _q(
    qid,
    text="内容",
    needs_correction=False,
    ocr_issues=None,
    knowledge_tags=None,
    source_pages=None,
):
    """构造题目 dict"""
    q = {
        "question_id": qid,
        "question_type": "选择题",
        "content_blocks": [{"block_type": "text", "content": text}],
        "needs_correction": needs_correction,
    }
    if ocr_issues:
        q["ocr_issues"] = ocr_issues
    if knowledge_tags is not None:
        q["knowledge_tags"] = knowledge_tags
    if source_pages is not None:
        q["source_pages"] = source_pages
    return q


class TestCorrectQuestionsNode:
    """correct_questions_node 合并逻辑测试"""

    def test_skip_when_no_questions(self):
        state = {"questions": []}
        result = correct_questions_node(state)
        assert result["questions"] == []

    def test_skip_when_no_flagged(self):
        """无需纠错且已有知识点标签时应直接跳过"""
        qs = [_q("1", knowledge_tags=["函数"]), _q("2", knowledge_tags=["导数"])]
        state = {"questions": qs}
        result = correct_questions_node(state)
        assert result["questions"] == qs

    @patch("agents.error_correction.tools.correct_batch")
    def test_merge_corrected(self, mock_correct_batch):
        """纠错结果应按 question_id 合并回原列表"""
        q1 = _q("1", knowledge_tags=["集合"])
        q2 = _q("2", text="有错误", needs_correction=True, ocr_issues=["乱码"])
        q3 = _q("3", knowledge_tags=["函数"])

        # 模拟 correct_batch 返回纠错后的题目
        corrected_q2 = {
            "question_id": "2",
            "question_type": "选择题",
            "content_blocks": [{"block_type": "text", "content": "已修复内容"}],
            "knowledge_tags": ["导数"],
            "corrections_applied": ["替换乱码字符"],
        }
        mock_correct_batch.invoke.return_value = json.dumps([corrected_q2], ensure_ascii=False)

        # 创建 agent_input.json 供纠错节点读取
        results_dir = str(_work_dir("merge_corrected"))
        agent_input = json.dumps([{"page_index": 0, "blocks": []}])
        with open(os.path.join(results_dir, "agent_input.json"), "w") as f:
            f.write(agent_input)

        with patch("core.config.settings.results_dir", Path(results_dir)):
            state = {"questions": [q1, q2, q3]}
            result = correct_questions_node(state)

        merged = result["questions"]
        assert len(merged) == 3

        # q2 应被替换为纠错版本
        merged_q2 = next(q for q in merged if q["question_id"] == "2")
        assert merged_q2["content_blocks"][0]["content"] == "已修复内容"
        assert merged_q2["knowledge_tags"] == ["导数"]
        assert merged_q2["needs_correction"] is False
        assert merged_q2["ocr_issues"] is None

        # q1, q3 不受影响
        merged_q1 = next(q for q in merged if q["question_id"] == "1")
        assert merged_q1["content_blocks"][0]["content"] == "内容"

    @patch("agents.error_correction.tools.correct_batch")
    def test_invalid_json_keeps_original(self, mock_correct_batch):
        """后处理返回无效 JSON 时应保留原始题目"""
        q1 = _q("1", needs_correction=True)
        mock_correct_batch.invoke.return_value = "not valid json"

        results_dir = str(_work_dir("invalid_json"))
        with open(os.path.join(results_dir, "agent_input.json"), "w") as f:
            f.write("{}")

        with patch("core.config.settings.results_dir", Path(results_dir)):
            state = {"questions": [q1]}
            result = correct_questions_node(state)

        # 应保留原始题目
        assert result["questions"] == [q1]

    @patch("agents.error_correction.tools.correct_batch")
    def test_missing_tags_are_postprocessed(self, mock_correct_batch):
        """没有 OCR 错误但缺少 knowledge_tags 的题目也应进入后处理"""
        q1 = _q("1", needs_correction=False, source_pages=[1])
        q1["source_regions"] = [{"page_index": 1, "region_index": 0}]
        corrected_q1 = {
            "question_id": "1",
            "question_type": "选择题",
            "content_blocks": q1["content_blocks"],
            "knowledge_tags": ["函数"],
            "corrections_applied": ["补全知识点标签"],
        }
        mock_correct_batch.invoke.return_value = json.dumps([corrected_q1], ensure_ascii=False)

        results_dir = str(_work_dir("missing_tags"))
        pages = [
            {"page_index": 0, "blocks": [{"block_content": "page0"}]},
            {"page_index": 1, "blocks": [{"block_content": "page1"}]},
            {"page_index": 2, "blocks": [{"block_content": "page2"}]},
        ]
        with open(os.path.join(results_dir, "agent_input.json"), "w", encoding="utf-8") as f:
            json.dump(pages, f, ensure_ascii=False)

        with patch("core.config.settings.results_dir", Path(results_dir)):
            result = correct_questions_node({"questions": [q1]})

        merged_q1 = result["questions"][0]
        assert merged_q1["knowledge_tags"] == ["函数"]
        assert merged_q1["needs_correction"] is False
        assert merged_q1["source_pages"] == [1]
        assert merged_q1["source_regions"] == [{"page_index": 1, "region_index": 0}]

        payload = mock_correct_batch.invoke.call_args.args[0]
        context_pages = json.loads(payload["ocr_context"])
        assert [p["page_index"] for p in context_pages] == [1]
        assert payload["subject"] == ""
        assert "existing_tags" in payload
