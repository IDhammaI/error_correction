# 错题本生成系统

基于PaddleOCR和LangChain Agent的智能错题本生成系统。

## 项目结构

```
error_correction/
├── error_correction_agent/     # Agent相关代码
│   ├── prompts.py              # Agent系统提示词
│   ├── agent.py                # Agent创建和配置
│   └── tools/                  # Agent工具集
│       ├── __init__.py
│       ├── question_tools.py   # 题目处理工具
│       └── file_tools.py       # 文件操作工具
│
├── src/                        # 核心功能模块
│   ├── paddleocr_client.py     # PaddleOCR API客户端
│   ├── workflow.py             # 工作流编排
│   └── utils.py                # 通用工具函数
│
├── input/                      # 输入文件目录
├── output/                     # 输出目录
│   ├── pages/                  # 标准化后的图片
│   ├── struct/                 # PaddleOCR解析结果
│   └── assets/                 # 图片资源
│
├── results/                    # 最终结果
│   ├── questions.json          # 分割后的题目
│   ├── preview.html            # 题目预览页面
│   └── wrongbook.md            # 导出的错题本
│
├── .env                        # 环境变量配置
├── test_paddleocr.py           # PaddleOCR测试
└── test_workflow.py            # 工作流测试
```

## 工作流程

### 简化的5步流程

1. **prepare_input** (确定性) - 将PDF/图片转换为标准化图片
2. **paddleocr_parse** (确定性) - 调用PaddleOCR API解析文档结构
3. **split_questions** (智能) - 使用LLM Agent智能分割题目
4. **build_preview** (确定性) - 生成HTML预览页面
5. **export_wrongbook** (确定性) - 导出Markdown格式错题本

### 技术架构

- **步骤1-2, 4-5**: 确定性逻辑，不需要LLM
- **步骤3**: 核心智能步骤，使用LangChain Agent
  - 模型: DeepSeek Chat
  - 工具: save_questions, log_issue, download_image, read_ocr_result
  - 提示词: 定义在 `error_correction_agent/prompts.py`

## 快速开始

### 1. 环境配置

复制 `.env.example` 为 `.env` 并填写配置:

```bash
# PaddleOCR API
PADDLEOCR_API_URL=https://...
PADDLEOCR_API_TOKEN=your_token

# DeepSeek API (用于Agent)
DEEPSEEK_API_KEY=your_key
DEEPSEEK_BASE_URL=https://api.deepseek.com

# LangSmith (可选，用于追踪)
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_key
LANGSMITH_PROJECT=error-correction
```

### 2. 测试PaddleOCR

```bash
# 在 input/ 目录放置测试图片 test.jpg
python test_paddleocr.py
```

### 3. 运行工作流

#### 方式1: 不使用Agent（仅测试步骤1-2）

```python
from src.workflow import ErrorCorrectionWorkflow

workflow = ErrorCorrectionWorkflow()
workflow.run("input/test.jpg", auto_split=False)
```

#### 方式2: 使用Agent完整流程

```python
from src.workflow import ErrorCorrectionWorkflow

# 创建工作流
workflow = ErrorCorrectionWorkflow()

# 步骤1-2: 准备和解析
workflow.run("input/test.jpg", auto_split=False)

# 步骤3: Agent分割题目
questions = workflow.split_questions_with_agent()

# 步骤4: 查看HTML预览（自动生成）
# 打开 results/preview.html

# 步骤5: 导出选中的题目
workflow.export_selected(["1", "2", "3"])
```

或使用测试脚本:

```bash
# 测试步骤1-2
python test_workflow.py

# 测试完整流程（包含Agent）
python test_workflow.py --with-agent
```

## Agent工具说明

### 1. save_questions
保存分割后的题目列表到JSON文件

```python
save_questions(
    questions=[{
        "question_id": "1",
        "question_type": "选择题",
        "content_blocks": [...],
        "options": ["A. ...", "B. ..."],
        ...
    }]
)
```

### 2. log_issue
记录分割过程中的问题

```python
log_issue(
    issue_type="unclear_boundary",
    description="题号不清晰，难以判断题目起始位置",
    block_info={...}
)
```

### 3. download_image
下载PaddleOCR返回的图片

```python
download_image(
    image_url="https://...",
    save_path="imgs/figure_1.jpg"
)
```

### 4. read_ocr_result
读取OCR结果JSON

```python
result = read_ocr_result("output/struct/test_struct.json")
```

## 开发指南

### 修改Agent提示词

编辑 `error_correction_agent/prompts.py` 中的 `SYSTEM_PROMPT`

### 添加新工具

1. 在 `error_correction_agent/tools/` 下创建新文件
2. 使用 `@tool` 装饰器定义工具函数
3. 在 `__init__.py` 中导出
4. 在 `agent.py` 中添加到工具列表

### 自定义工作流

修改 `src/workflow.py` 中的 `ErrorCorrectionWorkflow` 类

## 输出格式

### 题目JSON格式

```json
{
  "question_id": "1",
  "question_type": "选择题/填空题/解答题/判断题",
  "content_blocks": [
    {
      "block_type": "text",
      "content": "题干内容...",
      "bbox": [x1, y1, x2, y2],
      "block_id": 1
    },
    {
      "block_type": "display_formula",
      "content": "x^2 + y^2 = r^2",
      "bbox": [...],
      "block_id": 2
    }
  ],
  "options": ["A. 选项1", "B. 选项2"],
  "has_formula": true,
  "has_image": false,
  "image_refs": []
}
```

### 错题本Markdown格式

```markdown
# 错题本

> 共收录 3 道题目

---

## 1. 题目 1 (选择题)

下列关于平行四边形的说法，正确的是（  ）

A. 对边相等
B. 对角相等
...

### 我的答案
_（请在此处填写你的答案）_

### 正确答案
_（请在此处填写正确答案）_

### 解析
_（请在此处填写解题思路和知识点）_

---
```

## 常见问题

### Q: Agent分割效果不好怎么办?

A: 可以调整以下方面:
1. 修改 `prompts.py` 中的系统提示词
2. 增加示例题目（few-shot）
3. 调整模型temperature（在 `agent.py` 中）
4. 使用更强大的模型

### Q: 如何查看Agent执行日志?

A: 如果启用了LangSmith追踪（`.env` 中设置 `LANGSMITH_TRACING=true`），可以在LangSmith控制台查看详细的执行轨迹。

### Q: 支持哪些文件格式?

A:
- PDF: `.pdf`
- 图片: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.webp`

## 许可证

MIT License
