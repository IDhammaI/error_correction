# Benchmark 评测模块

基于 [C-Eval](https://huggingface.co/datasets/ceval/ceval-exam) 数据集评测解题智能体准确率。C-Eval 包含 52 个科目、共 13948 道四选一选择题。

## 快速开始

```bash
cd backend

# 列出所有可用科目
python -m benchmark.evaluate --list-subjects

# 评测单科（val 集）
python -m benchmark.evaluate --subjects high_school_mathematics

# 评测多个科目
python -m benchmark.evaluate --subjects high_school_mathematics,high_school_physics,high_school_chemistry

# 评测全部 52 个科目
python -m benchmark.evaluate

# 使用 test 集（题目更多）
python -m benchmark.evaluate --subjects high_school_mathematics --split test

# 指定模型
python -m benchmark.evaluate --provider ernie

# 调整每批题目数
python -m benchmark.evaluate --batch-size 5
```

## 数据集说明

| 分割 | 用途 | 有答案 |
|------|------|--------|
| `dev` | 少样本示例（每科 5 题） | 有 |
| `val` | 验证集（每科约 20 题） | 有 |
| `test` | 测试集（每科约 100+ 题） | 有 |

每道题格式：`question + A/B/C/D 四个选项 + answer（正确选项字母）`

## 输出

评测报告保存在 `benchmark/results/` 目录：

```json
{
  "provider": "deepseek",
  "split": "val",
  "overall_accuracy": 0.72,
  "total": 18,
  "correct": 13,
  "by_subject": {
    "high_school_mathematics": {"total": 18, "correct": 13, "accuracy": 0.72}
  }
}
```

## 依赖

- `datasets` — HuggingFace 数据集加载
- `solve_agent` — 本系统解题智能体
- 环境变量：`DEEPSEEK_API_KEY` 或 ERNIE 相关配置
