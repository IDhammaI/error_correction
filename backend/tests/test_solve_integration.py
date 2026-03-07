"""
solve_agent + C-Eval 集成测试

从 C-Eval 数据集加载真实高中数学题目，验证解题智能体的准确率。
需要配置 API Key 环境变量（DEEPSEEK_API_KEY 或 ERNIE 相关变量）。

用法:
    cd backend
    python -m pytest tests/test_solve_integration.py -v -s
    python -m pytest tests/test_solve_integration.py -v -s --model-provider ernie
"""

import pytest
from benchmark.metrics import compare_answers


@pytest.fixture(scope="session")
def ceval_data():
    """加载 C-Eval 高中数学 dev 集（5 题，最小消耗）"""
    from benchmark.evaluate import load_ceval, ceval_to_solve_format

    subject = "high_school_mathematics"
    items = load_ceval(subject, split="dev")
    questions = ceval_to_solve_format(items, subject)
    answer_map = {f"{subject}_{item['id']}": item["answer"] for item in items}
    return questions, answer_map


@pytest.fixture(scope="session")
def solve_results(ceval_data, model_provider):
    """session 级 fixture：调用一次 API 解答 dev 集"""
    from solve_agent import invoke_solve

    questions, _ = ceval_data
    return invoke_solve(questions, provider=model_provider)


class TestSolveIntegration:
    """解题智能体 C-Eval 集成测试"""

    def test_returns_all_answers(self, solve_results, ceval_data):
        """应返回与输入题目数量相同的答案"""
        questions, _ = ceval_data
        assert len(solve_results.results) == len(questions)

    def test_question_ids_match(self, solve_results, ceval_data):
        """返回的 question_id 应与输入一致"""
        questions, _ = ceval_data
        returned_ids = {r.question_id for r in solve_results.results}
        expected_ids = {q["question_id"] for q in questions}
        assert returned_ids == expected_ids

    def test_answers_are_valid_options(self, solve_results):
        """每道题的答案应为 A/B/C/D"""
        for r in solve_results.results:
            normalized = r.answer.strip().upper()
            assert normalized in ("A", "B", "C", "D"), \
                f"{r.question_id}: answer='{r.answer}' 不是有效选项"

    def test_has_reasoning(self, solve_results):
        """每道题应包含非空的推理过程"""
        for r in solve_results.results:
            assert r.reasoning.strip(), f"{r.question_id} 缺少推理过程"

    def test_confidence_in_range(self, solve_results):
        """置信度应在 0-1 范围内"""
        for r in solve_results.results:
            assert 0.0 <= r.confidence <= 1.0, f"{r.question_id} confidence={r.confidence}"

    def test_accuracy_above_threshold(self, solve_results, ceval_data):
        """在 dev 集上正确率应不低于 40%（基线要求）"""
        _, answer_map = ceval_data
        correct = 0
        for r in solve_results.results:
            if compare_answers(r.answer, answer_map.get(r.question_id, "")):
                correct += 1
        accuracy = correct / len(solve_results.results)
        print(f"\nC-Eval dev 正确率: {accuracy:.0%} ({correct}/{len(solve_results.results)})")
        assert accuracy >= 0.4, f"正确率 {accuracy:.0%} 低于 40% 基线"
