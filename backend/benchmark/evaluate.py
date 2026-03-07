"""
基于 C-Eval 数据集评测解题智能体准确率

数据集: https://huggingface.co/datasets/ceval/ceval-exam
C-Eval 包含 52 个科目，全部为四选一选择题（A/B/C/D）。

用法:
    cd backend
    python -m benchmark.evaluate                                           # val 集，全部科目
    python -m benchmark.evaluate --subjects high_school_mathematics         # 单科目
    python -m benchmark.evaluate --subjects high_school_mathematics,high_school_physics  # 多科目
    python -m benchmark.evaluate --split test                              # 使用 test 集
    python -m benchmark.evaluate --provider ernie                          # 指定模型
    python -m benchmark.evaluate --batch-size 5                            # 每批 5 题
    python -m benchmark.evaluate --list-subjects                           # 列出所有科目
"""

import argparse
import json
import logging
import os
import sys
from typing import Dict, Any, List

from .metrics import compare_answers, compute_accuracy

# 确保 backend/ 在 sys.path 中
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

logger = logging.getLogger(__name__)

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")

# C-Eval 科目中文名映射（常用科目）
SUBJECT_ZH = {
    "high_school_mathematics": "高中数学",
    "high_school_physics": "高中物理",
    "high_school_chemistry": "高中化学",
    "high_school_biology": "高中生物",
    "high_school_chinese": "高中语文",
    "high_school_history": "高中历史",
    "high_school_geography": "高中地理",
    "high_school_politics": "高中政治",
    "middle_school_mathematics": "初中数学",
    "middle_school_physics": "初中物理",
    "middle_school_chemistry": "初中化学",
    "middle_school_biology": "初中生物",
    "middle_school_history": "初中历史",
    "middle_school_geography": "初中地理",
    "middle_school_politics": "初中政治",
    "advanced_mathematics": "高等数学",
    "college_physics": "大学物理",
    "college_chemistry": "大学化学",
    "college_programming": "大学编程",
    "discrete_mathematics": "离散数学",
    "probability_and_statistics": "概率统计",
    "computer_architecture": "计算机体系结构",
    "computer_network": "计算机网络",
    "operating_system": "操作系统",
    "accountant": "会计",
    "law": "法律",
    "education_science": "教育学",
    "clinical_medicine": "临床医学",
    "physician": "医师",
}


def load_ceval(subject: str, split: str = "val") -> List[Dict[str, Any]]:
    """从 HuggingFace 加载 C-Eval 数据集

    Args:
        subject: 科目英文名（如 high_school_mathematics）
        split: 数据集分割（val/test/dev）

    Returns:
        题目列表，每项包含 id, question, A, B, C, D, answer
    """
    from datasets import load_dataset

    ds = load_dataset("ceval/ceval-exam", subject, split=split)
    items = []
    for row in ds:
        items.append({
            "id": row["id"],
            "question": row["question"],
            "A": row["A"],
            "B": row["B"],
            "C": row["C"],
            "D": row["D"],
            "answer": row["answer"],
        })
    return items


def ceval_to_solve_format(items: List[Dict], subject: str) -> List[Dict]:
    """将 C-Eval 数据转换为 solve_agent 输入格式"""
    questions = []
    for item in items:
        questions.append({
            "question_id": f"{subject}_{item['id']}",
            "question_type": "选择题",
            "content_blocks": [{"block_type": "text", "content": item["question"]}],
            "options": [
                f"A. {item['A']}",
                f"B. {item['B']}",
                f"C. {item['C']}",
                f"D. {item['D']}",
            ],
        })
    return questions


def run_evaluation(
    provider: str,
    subjects: List[str],
    split: str = "val",
    batch_size: int = 10,
) -> Dict[str, Any]:
    """对指定模型和科目进行评测

    Args:
        provider: 模型供应商
        subjects: 科目列表
        split: 数据集分割
        batch_size: 每批发送的题目数（避免 token 溢出）

    Returns:
        评测报告
    """
    from solve_agent import invoke_solve

    all_results = []

    for subject in subjects:
        zh_name = SUBJECT_ZH.get(subject, subject)
        print(f"\n{'─'*40}")
        print(f"科目: {zh_name} ({subject})")

        # 加载数据
        items = load_ceval(subject, split=split)
        print(f"题目数: {len(items)}")

        # 分批调用
        questions = ceval_to_solve_format(items, subject)
        answer_map = {f"{subject}_{item['id']}": item["answer"] for item in items}

        for i in range(0, len(questions), batch_size):
            batch = questions[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(questions) + batch_size - 1) // batch_size
            print(f"  批次 {batch_num}/{total_batches} ({len(batch)} 题)...", end=" ", flush=True)

            try:
                solve_result = invoke_solve(batch, provider=provider)
                predicted_map = {r.question_id: r for r in solve_result.results}

                correct_count = 0
                for q in batch:
                    qid = q["question_id"]
                    predicted = predicted_map.get(qid)
                    target = answer_map[qid]

                    if predicted is None:
                        all_results.append({
                            "question_id": qid,
                            "subject": subject,
                            "predicted": "",
                            "target": target,
                            "correct": False,
                        })
                        continue

                    correct = compare_answers(predicted.answer, target)
                    if correct:
                        correct_count += 1
                    all_results.append({
                        "question_id": qid,
                        "subject": subject,
                        "predicted": predicted.answer,
                        "target": target,
                        "correct": correct,
                        "reasoning": predicted.reasoning,
                        "confidence": predicted.confidence,
                    })

                print(f"{correct_count}/{len(batch)} 正确")
            except Exception as e:
                logger.error(f"批次 {batch_num} 失败: {e}")
                print(f"失败: {e}")
                for q in batch:
                    all_results.append({
                        "question_id": q["question_id"],
                        "subject": subject,
                        "predicted": "",
                        "target": answer_map[q["question_id"]],
                        "correct": False,
                    })

    # 计算整体和分科目正确率
    report = _build_report(all_results, provider, split)
    return report


def _build_report(results: List[Dict], provider: str, split: str) -> Dict[str, Any]:
    """构建评测报告"""
    total = len(results)
    correct = sum(1 for r in results if r["correct"])

    # 按科目统计
    by_subject = {}
    for r in results:
        subj = r.get("subject", "unknown")
        if subj not in by_subject:
            by_subject[subj] = {"total": 0, "correct": 0}
        by_subject[subj]["total"] += 1
        if r["correct"]:
            by_subject[subj]["correct"] += 1

    for stats in by_subject.values():
        stats["accuracy"] = stats["correct"] / stats["total"] if stats["total"] > 0 else 0.0

    return {
        "provider": provider,
        "split": split,
        "overall_accuracy": correct / total if total > 0 else 0.0,
        "total": total,
        "correct": correct,
        "by_subject": by_subject,
        "details": results,
    }


def save_report(report: Dict[str, Any]) -> str:
    """保存评测报告"""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    provider = report["provider"]
    split = report["split"]
    path = os.path.join(RESULTS_DIR, f"report_{provider}_{split}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return path


def print_report(report: Dict[str, Any]):
    """打印评测报告"""
    print(f"\n{'='*50}")
    print(f"模型: {report['provider']}  |  数据集: C-Eval ({report['split']})")
    print(f"总正确率: {report['overall_accuracy']:.1%} ({report['correct']}/{report['total']})")
    print(f"{'─'*50}")
    for subj, stats in sorted(report["by_subject"].items()):
        zh = SUBJECT_ZH.get(subj, subj)
        print(f"  {zh}: {stats['accuracy']:.1%} ({stats['correct']}/{stats['total']})")
    print(f"{'='*50}")

    wrong = [d for d in report["details"] if not d["correct"]]
    if wrong and len(wrong) <= 20:
        print(f"\n错误题目 ({len(wrong)} 道):")
        for d in wrong:
            print(f"  {d['question_id']}: 预测={d.get('predicted','')}, 标准={d['target']}")


def list_subjects():
    """列出所有 C-Eval 科目"""
    from datasets import get_dataset_config_names
    configs = sorted(get_dataset_config_names("ceval/ceval-exam"))
    print(f"C-Eval 共 {len(configs)} 个科目:\n")
    for c in configs:
        zh = SUBJECT_ZH.get(c, "")
        suffix = f"  ({zh})" if zh else ""
        print(f"  {c}{suffix}")


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    parser = argparse.ArgumentParser(description="基于 C-Eval 数据集评测解题智能体")
    parser.add_argument("--provider", "-p", choices=["deepseek", "ernie"], default="deepseek",
                        help="模型供应商（默认 deepseek）")
    parser.add_argument("--subjects", "-s", default=None,
                        help="科目（逗号分隔），不指定则评测全部")
    parser.add_argument("--split", choices=["val", "test", "dev"], default="val",
                        help="数据集分割（默认 val）")
    parser.add_argument("--batch-size", "-b", type=int, default=10,
                        help="每批题目数（默认 10）")
    parser.add_argument("--list-subjects", action="store_true",
                        help="列出所有可用科目")
    args = parser.parse_args()

    if args.list_subjects:
        list_subjects()
        return

    # 确定科目列表
    if args.subjects:
        subjects = [s.strip() for s in args.subjects.split(",")]
    else:
        from datasets import get_dataset_config_names
        subjects = sorted(get_dataset_config_names("ceval/ceval-exam"))

    report = run_evaluation(
        provider=args.provider,
        subjects=subjects,
        split=args.split,
        batch_size=args.batch_size,
    )
    path = save_report(report)
    print_report(report)
    print(f"\n报告已保存: {path}")


if __name__ == "__main__":
    main()
