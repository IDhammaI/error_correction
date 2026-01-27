# 错题本生成系统 - 项目技术文档

## 📋 项目概述

### 系统简介
这是一个基于 **LangChain Agent** 和 **PaddleOCR API** 的智能错题本生成系统。系统能够自动识别、分割和导出试卷/作业中的题目，生成结构化的错题本，支持选择题、填空题、解答题、判断题等多种题型。

### 核心功能
- ✅ PDF/图片文件自动标准化处理
- ✅ 基于PaddleOCR的文档结构化解析（支持公式、图片、布局识别）
- ✅ 基于DeepSeek的智能题目分割（AI自动识别题号、题型、选项）
- ✅ 交互式HTML预览（可视化选择题目）
- ✅ Markdown格式错题本导出

### 技术栈
- **LLM框架**: LangChain + LangGraph
- **Agent**: DeepSeek Chat (via `create_deep_agent`)
- **OCR**: PaddleOCR-VL API
- **文档处理**: pdf2image, Pillow
- **CLI**: Rich (美化输出)
- **配置**: python-dotenv

---

## 🗂️ 目录结构

```
error_correction/
│
├── error_correction_agent/          # 🤖 Agent智能层
│   ├── agent.py                     # Agent工厂函数和配置
│   ├── prompts.py                   # 系统提示词（题目分割规则）
│   └── tools/                       # Agent工具集
│       ├── __init__.py              # 工具统一导出
│       ├── question_tools.py        # 题目处理工具
│       └── file_tools.py            # 文件I/O工具
│
├── src/                             # ⚙️ 确定性业务逻辑层
│   ├── paddleocr_client.py          # PaddleOCR API客户端
│   ├── workflow.py                  # 5步工作流编排
│   └── utils.py                     # 通用工具函数
│
├── network_search_agent/            # 🔍 网络搜索Agent（独立模块）
│   ├── prompts.py
│   └── tools.py
│
├── printed-vs-handwritten/          # ✍️ 手写/印刷识别子项目
│   ├── app.py                       # Flask API服务（端口5000）
│   ├── classify.py                  # 分类器CLI
│   ├── train-model.py               # 模型训练
│   └── ocrd_typegroups_classifier/  # 分类器核心库
│
├── input/                           # 📥 输入文件目录
├── output/                          # 📤 输出目录
│   ├── pages/                       # 标准化后的PNG图片
│   ├── struct/                      # PaddleOCR解析结果（JSON）
│   └── assets/                      # 下载的图片资源
│
├── results/                         # 🎯 最终结果目录
│   ├── questions.json               # Agent分割后的题目
│   ├── split_issues.jsonl           # 分割过程问题日志
│   ├── preview.html                 # 交互式预览页面
│   └── wrongbook.md                 # 最终错题本
│
├── docs/                            # 📚 文档
│   ├── INDEX.md                     # LangChain文档索引
│   ├── HANDWRITTEN_API.md           # 手写体识别API文档
│   └── PROJECT_STRUCTURE.md         # 本文档
│
├── langgraph.json                   # LangGraph配置文件
├── .env                             # 环境变量配置（不提交）
├── .env.example                     # 配置模板
├── README.md                        # 快速开始指南
├── requirements.txt                 # Python依赖
├── test_paddleocr.py                # PaddleOCR测试脚本
├── test_workflow.py                 # 工作流测试脚本
└── agent.py                         # network_search_agent入口
```

---

## 🔧 核心模块详解

### 1. error_correction_agent/ - Agent智能层

#### 📄 agent.py

**作用**: 创建和配置题目分割Agent

**核心函数**:

```python
def create_question_split_agent() -> Agent:
    """
    创建题目分割Agent

    使用DeepSeek模型和定义的工具创建一个专门用于分割题目的Agent。

    Returns:
        配置好的Agent实例
    """
    # 初始化DeepSeek模型
    model = init_chat_model(
        model="deepseek:deepseek-chat",
        temperature=0.1,  # 低温度确保稳定输出
    )

    # 绑定4个工具
    tools = [
        save_questions,
        log_issue,
        download_image,
        read_ocr_result,
    ]

    # 创建Agent
    agent = create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )

    return agent
```

**全局导出**:
```python
agent = create_question_split_agent()  # 供langgraph.json使用
```

**依赖关系**:
```
create_question_split_agent()
├─→ init_chat_model()           [langchain.chat_models]
├─→ create_deep_agent()         [deepagents]
├─→ SYSTEM_PROMPT               [.prompts]
└─→ 4 Tools                     [.tools]
    ├─→ save_questions
    ├─→ log_issue
    ├─→ download_image
    └─→ read_ocr_result
```

---

#### 📄 prompts.py

**作用**: 定义Agent的系统提示词，指导题目分割行为

**核心内容**:

```python
SYSTEM_PROMPT = """# 错题本题目分割专家

你是一个专业的试卷题目分割专家。你的任务是分析OCR识别的文档结构，智能分割出独立的题目。

## 核心任务
从PaddleOCR解析的结构化数据中：
1. 识别题目边界（题号是关键标志）
2. 提取题干内容
3. 识别并提取选项（如果是选择题）
4. 识别公式块（display_formula 和 inline_formula）
5. 识别图片块并保留引用
6. 按阅读顺序组织内容

## 题目类型识别
- 选择题: 包含A/B/C/D选项
- 填空题: 包含下划线或括号
- 解答题: 要求"解答"、"证明"、"计算"
- 判断题: 要求判断"正确/错误"

## 题号识别规则
- 1. / 2. / 3. ...
- 1、/ 2、/ 3、...
- （1）/（2）/（3）...
- 一、/ 二、/ 三、...

## 工作流程
1. 分析block顺序（使用block_order）
2. 识别题目起点（查找题号）
3. 收集题目内容（直到下一个题号）
4. 结构化输出

...（详见完整提示词）
"""
```

**输出格式规范**:
```json
{
  "question_id": "1",
  "question_type": "选择题",
  "content_blocks": [
    {
      "block_type": "text|display_formula|inline_formula|image",
      "content": "内容文本",
      "bbox": [x1, y1, x2, y2],
      "block_id": 原始ID
    }
  ],
  "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
  "has_formula": true,
  "has_image": false,
  "image_refs": ["imgs/xxx.jpg"]
}
```

---

#### 📄 tools/question_tools.py

**工具1: save_questions**

```python
@tool(parse_docstring=True)
def save_questions(
    questions: List[Dict[str, Any]],
    output_path: str = None
) -> str:
    """
    保存分割后的题目列表到JSON文件

    Args:
        questions: 题目列表，每个题目包含:
            - question_id: 题号
            - question_type: 题型
            - content_blocks: 内容块列表
            - options: 选项（选择题）
            - has_formula: 是否包含公式
            - has_image: 是否包含图片
            - image_refs: 图片引用路径列表
        output_path: 输出路径（默认: {RESULTS_DIR}/questions.json）

    Returns:
        保存结果消息
    """
```

**使用场景**: Agent分割完成后，调用此工具保存题目列表

**工具2: log_issue**

```python
@tool(parse_docstring=True)
def log_issue(
    issue_type: str,
    description: str,
    block_info: Dict[str, Any] = None
) -> str:
    """
    记录题目分割过程中遇到的问题

    Args:
        issue_type: 问题类型
            - "unclear_boundary": 边界不清
            - "missing_question_number": 缺少题号
            - "complex_structure": 复杂结构
        description: 问题详细描述
        block_info: 相关block信息（可选）

    Returns:
        记录结果消息
    """
```

**输出**: 追加到 `{RESULTS_DIR}/split_issues.jsonl`

**使用场景**: Agent遇到不确定情况时记录，供人工审核或算法改进

---

#### 📄 tools/file_tools.py

**工具3: download_image**

```python
@tool(parse_docstring=True)
def download_image(image_url: str, save_path: str) -> str:
    """
    从URL下载图片到本地

    Args:
        image_url: 图片URL地址
        save_path: 保存路径（相对于ASSETS_DIR）

    Returns:
        下载结果消息
    """
```

**使用场景**: 下载PaddleOCR返回的图片资源

**工具4: read_ocr_result**

```python
@tool(parse_docstring=True)
def read_ocr_result(result_path: str) -> Dict[str, Any]:
    """
    读取PaddleOCR的解析结果

    Args:
        result_path: OCR结果文件路径（JSON）

    Returns:
        OCR解析结果字典或错误信息
    """
```

**使用场景**: Agent需要重新读取或分析OCR结果时

---

### 2. src/ - 确定性业务逻辑层

#### 📄 paddleocr_client.py

**类: PaddleOCRClient**

**初始化方法**:
```python
def __init__(self):
    """
    初始化客户端，从环境变量读取配置

    环境变量:
        PADDLEOCR_API_URL: API端点
        PADDLEOCR_API_TOKEN: 认证令牌
        PADDLEOCR_USE_DOC_ORIENTATION: 启用方向检测
        PADDLEOCR_USE_DOC_UNWARPING: 启用文档展平
        PADDLEOCR_USE_CHART_RECOGNITION: 启用图表识别
    """
```

**主要方法**:

**1️⃣ parse_image**
```python
def parse_image(
    self,
    image_path: str,
    save_output: bool = True,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    解析图片并返回结构化结果

    流程:
        1. 读取图片并转为Base64
        2. 构建API请求payload
        3. 调用PaddleOCR API
        4. 保存JSON结果到 {STRUCT_DIR}/{filename}_struct.json
        5. 下载并保存响应中的图片和Markdown

    Args:
        image_path: 图片文件路径
        save_output: 是否保存输出（默认True）
        output_dir: 输出目录（默认从STRUCT_DIR读取）

    Returns:
        PaddleOCR API返回的结构化结果
    """
```

**返回结构示例**:
```python
{
    "layoutParsingResults": [
        {
            "prunedResult": {
                "parsing_res_list": [
                    {
                        "block_id": 1,
                        "block_type": "text",
                        "block_label": "paragraph_title",
                        "block_content": "1. 题目内容...",
                        "block_bbox": [x1, y1, x2, y2],
                        "block_order": 1,
                        "group_id": 1
                    },
                    {
                        "block_type": "display_formula",
                        "block_content": "x^2 + y^2 = r^2",
                        ...
                    }
                ]
            },
            "block_order": [1, 2, 3, 4, ...],  # 推荐阅读顺序
            "markdown": {
                "text": "## 第一题\n\n1. ...",
                "images": {
                    "imgs/figure_1.jpg": "https://..."
                }
            },
            "outputImages": {
                "layout": "https://...",
                "table": "https://..."
            }
        }
    ]
}
```

**2️⃣ parse_pdf**
```python
def parse_pdf(
    self,
    pdf_path: str,
    save_output: bool = True,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    解析PDF并返回结构化结果

    功能同parse_image，但处理PDF文件
    """
```

**3️⃣ _save_images**
```python
def _save_images(self, result: Dict[str, Any], output_dir: str):
    """
    下载并保存结果中的图片资源

    保存内容:
        1. Markdown文档 (doc_0.md, doc_1.md, ...)
        2. Markdown中的图片
        3. outputImages中的可视化图片
    """
```

---

#### 📄 workflow.py

**类: ErrorCorrectionWorkflow**

**作用**: 编排5步完整工作流

**初始化**:
```python
def __init__(self):
    """
    初始化工作流

    属性:
        paddleocr_client: PaddleOCR客户端实例
        image_paths: 步骤1输出（标准化图片路径）
        ocr_results: 步骤2输出（OCR解析结果）
        questions: 步骤3输出（Agent分割的题目）
    """
```

**5步工作流**:

| 步骤 | 方法 | 类型 | 输入 | 输出 |
|-----|------|------|------|------|
| 1 | `prepare_input` | 确定性 | `file_path: str` | `image_paths: List[str]` |
| 2 | `paddleocr_parse` | 确定性 | `image_paths: List[str]` | `ocr_results: List[Dict]` |
| 3 | `split_questions_with_agent` | 🤖智能 | `ocr_results: List[Dict]` | `questions: List[Dict]` |
| 4 | `build_preview` | 确定性 | `questions: List[Dict]` | `preview.html` |
| 5 | `export_selected` | 确定性 | `questions, selected_ids` | `wrongbook.md` |

**核心方法详解**:

**主入口: run**
```python
def run(self, input_file: str, auto_split: bool = False) -> Dict[str, Any]:
    """
    运行完整工作流

    Args:
        input_file: 输入文件路径（PDF或图片）
        auto_split: 是否自动调用Agent分割（默认False）

    Returns:
        包含各步骤结果的字典:
            - image_paths: 标准化图片路径列表
            - ocr_results: OCR解析结果列表
            - questions: 分割后的题目列表

    执行步骤:
        1. 准备输入文件（调用utils.prepare_input）
        2. PaddleOCR解析（调用self.paddleocr_parse）
        3. (可选) Agent分割题目
        4. (如有题目) 生成HTML预览
    """
```

**步骤2实现**:
```python
def paddleocr_parse(self, image_paths: List[str]) -> List[Dict[str, Any]]:
    """
    调用PaddleOCR解析文档结构

    Args:
        image_paths: 图片路径列表

    Returns:
        每张图片的PaddleOCR解析结果列表

    过程:
        对每张图片调用 PaddleOCRClient.parse_image()
        自动保存JSON和图片资源
    """
```

**步骤3实现**（核心智能步骤）:
```python
def split_questions_with_agent(self) -> List[Dict[str, Any]]:
    """
    使用Agent智能分割题目

    Returns:
        分割后的题目列表

    执行流程:
        1. 创建Agent实例
        2. 简化OCR结果为Agent友好格式
        3. 构建提示词
        4. 调用Agent.invoke()
        5. 从 {RESULTS_DIR}/questions.json 读取Agent保存的结果

    简化格式:
        simplified_results = [
            {
                "blocks": [...],        # parsing_res_list
                "block_order": [...]    # 推荐阅读顺序
            }
        ]
    """
```

**步骤5实现**:
```python
def export_selected(
    self,
    selected_ids: List[str],
    output_path: str = None
) -> str:
    """
    导出选中的题目为错题本

    Args:
        selected_ids: 用户选择的题目ID列表
        output_path: 输出路径（可选）

    Returns:
        导出文件路径

    过程:
        1. 过滤选中题目
        2. 调用 utils.export_wrongbook()
        3. 返回Markdown文件路径
    """
```

---

#### 📄 utils.py

**函数1: prepare_input (步骤1)**

```python
def prepare_input(file_path: str) -> List[str]:
    """
    准备输入文件 - 统一转换为标准PNG图片

    Args:
        file_path: 输入文件路径（PDF或图片）

    Returns:
        标准化后的PNG图片路径列表

    处理逻辑:
        如果是PDF:
            1. 使用pdf2image转换为300dpi的图片
            2. 逐页保存为PNG格式
            3. 命名: {stem}_page_001.png, {stem}_page_002.png, ...

        如果是图片:
            1. 打开图片
            2. 转换为RGB模式
            3. 保存为PNG格式
            4. 命名: {stem}.png

    输出目录: {PAGES_DIR}

    支持格式:
        - PDF: .pdf
        - 图片: .jpg, .jpeg, .png, .bmp, .tiff, .webp

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 不支持的文件格式
    """
```

**函数2: build_preview (步骤4)**

```python
def build_preview(
    questions: List[Dict[str, Any]],
    output_path: str = None
) -> str:
    """
    生成HTML预览页面

    Args:
        questions: 题目列表
        output_path: 输出路径（默认: {RESULTS_DIR}/preview.html）

    Returns:
        HTML文件路径

    页面功能:
        1. 展示所有题目（题号、题型、内容）
        2. 支持点击选择题目
        3. 选中状态可视化（按钮变色）
        4. 底部导出按钮（显示选中题目ID）

    样式特点:
        - 题目卡片布局
        - 题型色标（选择题=绿色）
        - 公式高亮显示
        - 图片引用标记
        - 响应式设计
    """
```

**函数3: export_wrongbook (步骤5)**

```python
def export_wrongbook(
    questions: List[Dict[str, Any]],
    selected_ids: List[str],
    output_path: str = None
) -> str:
    """
    导出错题本为Markdown格式

    Args:
        questions: 题目列表
        selected_ids: 选中的题目ID列表
        output_path: 输出路径（默认: {RESULTS_DIR}/wrongbook.md）

    Returns:
        Markdown文件路径

    Markdown格式:
        # 错题本
        > 共收录 N 道题目
        ---

        ## 1. 题目 X (题型)

        [题干内容]
        [选项或公式]
        [图片引用]

        ### 我的答案
        _（请在此处填写你的答案）_

        ### 正确答案
        _（请在此处填写正确答案）_

        ### 解析
        _（请在此处填写解题思路和知识点）_

        ---

    特性:
        - 支持LaTeX公式（$...$和$$...$$）
        - 图片Markdown引用
        - 预留答案和解析填写区域
    """
```

---

## 🔗 模块依赖关系图

```
┌─────────────────────────────────────────────────────────────┐
│                    User Entry Point                         │
│              ErrorCorrectionWorkflow.run()                   │
└──────────────┬──────────────────────────────────────────────┘
               │
               ├── [步骤1] prepare_input(file_path)
               │            │
               │            ├─ PDF? → pdf2image.convert_from_path()
               │            └─ 图片? → PIL.Image.open() → save PNG
               │            │
               │            └→ List[image_paths]
               │
               ├── [步骤2] paddleocr_parse(image_paths)
               │            │
               │            └─ for each image:
               │                ├─ PaddleOCRClient.parse_image()
               │                │   ├─ base64编码
               │                │   ├─ requests.post(API_URL)
               │                │   ├─ 保存JSON结果
               │                │   └─ _save_images()
               │                │       ├─ 下载markdown图片
               │                │       ├─ 下载output图片
               │                │       └─ 保存markdown文档
               │                │
               │                └→ List[ocr_results]
               │
               ├── [步骤3] split_questions_with_agent() 🤖
               │            │
               │            ├─ create_question_split_agent()
               │            │   ├─ init_chat_model("deepseek:deepseek-chat")
               │            │   ├─ tools = [save_questions, log_issue, ...]
               │            │   └─ create_deep_agent(model, tools, SYSTEM_PROMPT)
               │            │
               │            ├─ 简化OCR结果:
               │            │   simplified_results = [
               │            │       {"blocks": [...], "block_order": [...]}
               │            │   ]
               │            │
               │            ├─ 构建提示词
               │            │
               │            ├─ agent.invoke({
               │            │       "messages": [
               │            │           {"role": "user", "content": prompt},
               │            │           {"role": "user", "content": OCR数据}
               │            │       ]
               │            │   })
               │            │   │
               │            │   └─ Agent内部流程:
               │            │       ├─ 分析题号和内容结构
               │            │       ├─ 识别题型
               │            │       ├─ 可能调用: download_image()
               │            │       ├─ 可能调用: log_issue()
               │            │       └─ 调用: save_questions()
               │            │           └─ 保存到 results/questions.json
               │            │
               │            └─ 读取 questions.json → List[questions]
               │
               ├── [步骤4] build_preview(questions)
               │            │
               │            ├─ 构建HTML内容
               │            │   ├─ 题目卡片
               │            │   ├─ 选择按钮
               │            │   └─ JavaScript交互
               │            │
               │            └─ 保存到 results/preview.html
               │
               └── [步骤5] export_selected(questions, selected_ids)
                            │
                            ├─ 过滤选中题目
                            ├─ 生成Markdown内容
                            │   ├─ 题干
                            │   ├─ 选项/公式
                            │   ├─ 答案区域（空白）
                            │   └─ 解析区域（空白）
                            │
                            └─ 保存到 results/wrongbook.md
```

---

## ⚙️ 环境变量配置表

| 变量 | 必需? | 用途 | 示例值 | 默认值 |
|-----|------|------|--------|--------|
| **PaddleOCR配置** | | | | |
| `PADDLEOCR_API_URL` | ✅ | PaddleOCR API端点 | `https://api.xxx.com/layout-parsing` | - |
| `PADDLEOCR_API_TOKEN` | ✅ | API认证令牌 | `token_abc123` | - |
| `PADDLEOCR_USE_DOC_ORIENTATION` | ❌ | 启用文档方向检测 | `true` / `false` | `false` |
| `PADDLEOCR_USE_DOC_UNWARPING` | ❌ | 启用文档展平 | `true` / `false` | `false` |
| `PADDLEOCR_USE_CHART_RECOGNITION` | ❌ | 启用图表识别 | `true` / `false` | `false` |
| **DeepSeek配置** | | | | |
| `DEEPSEEK_API_KEY` | ✅ | DeepSeek API密钥 | `sk-xxx` | - |
| `DEEPSEEK_BASE_URL` | ❌ | DeepSeek基础URL | `https://api.deepseek.com` | 自动 |
| **LangSmith配置** | | | | |
| `LANGSMITH_TRACING` | ❌ | 启用LangSmith追踪 | `true` / `false` | `false` |
| `LANGSMITH_API_KEY` | ❌ | LangSmith认证密钥 | `lsv2_pt_xxx` | - |
| `LANGSMITH_PROJECT` | ❌ | LangSmith项目名称 | `error-correction` | - |
| `LANGSMITH_ENDPOINT` | ❌ | LangSmith端点 | `https://api.smith.langchain.com` | 默认 |
| **其他API** | | | | |
| `TAVILY_API_KEY` | ❌ | Tavily搜索API密钥 | `tvly-xxx` | - |
| `ANTHROPIC_API_KEY` | ❌ | Anthropic API密钥 | `sk-ant-xxx` | - |
| **输出目录配置** | | | | |
| `OUTPUT_DIR` | ❌ | 总输出目录 | `output` | `output` |
| `PAGES_DIR` | ❌ | 标准化图片目录 | `output/pages` | `output/pages` |
| `STRUCT_DIR` | ❌ | OCR结果目录 | `output/struct` | `output/struct` |
| `ASSETS_DIR` | ❌ | 资源目录 | `output/assets` | `output/assets` |
| `RESULTS_DIR` | ❌ | 最终结果目录 | `results` | `results` |

---

## 💻 使用流程示例

### 方式1: 分步骤手动控制

```python
from src.workflow import ErrorCorrectionWorkflow

# 创建工作流实例
workflow = ErrorCorrectionWorkflow()

# 步骤1-2: 准备输入和OCR解析
result = workflow.run("input/exam_paper.pdf", auto_split=False)

print(f"已处理 {len(result['image_paths'])} 张图片")
print(f"OCR解析完成，结果保存在 output/struct/")

# 步骤3: 手动调用Agent分割题目
questions = workflow.split_questions_with_agent()

print(f"分割出 {len(questions)} 道题目")

# 步骤4: 自动生成HTML预览
# (在run()中已自动调用)

# 步骤5: 导出选中的题目
selected_ids = ["1", "2", "5", "7"]
wrongbook_path = workflow.export_selected(selected_ids)

print(f"错题本已导出: {wrongbook_path}")
```

### 方式2: 自动完整流程

```python
from src.workflow import ErrorCorrectionWorkflow

# 创建工作流实例
workflow = ErrorCorrectionWorkflow()

# 自动执行步骤1-4
workflow.run("input/exam_paper.pdf", auto_split=True)

# 打开 results/preview.html 查看题目
# 选择题目后，手动导出
workflow.export_selected(["1", "3", "5"])
```

### 方式3: 仅测试PaddleOCR

```python
from src.paddleocr_client import PaddleOCRClient

client = PaddleOCRClient()

# 解析单张图片
result = client.parse_image("input/page1.jpg")

# 查看结果
print(f"识别的块数量: {len(result['layoutParsingResults'][0]['prunedResult']['parsing_res_list'])}")

# 结果自动保存到 output/struct/page1_struct.json
```

### 方式4: 使用测试脚本

```bash
# 测试步骤1-2（不调用Agent）
python test_workflow.py

# 测试完整流程（包含Agent）
python test_workflow.py --with-agent

# 测试PaddleOCR
python test_paddleocr.py
```

---

## 🤖 Agent执行流程详解

### Agent接收的数据格式

```python
simplified_results = [
    {
        "blocks": [
            {
                "block_id": 1,
                "block_type": "text",
                "block_label": "paragraph_title",
                "block_content": "1. 下列关于平行四边形的说法，正确的是（  ）",
                "block_bbox": [120, 300, 800, 350],
                "block_order": 1,
                "group_id": 1
            },
            {
                "block_id": 2,
                "block_type": "text",
                "block_label": "text",
                "block_content": "A. 对边相等",
                "block_bbox": [150, 360, 400, 390],
                "block_order": 2,
                "group_id": 1
            },
            {
                "block_id": 3,
                "block_type": "display_formula",
                "block_content": "\\sum_{i=1}^{n} x_i = S",
                "block_bbox": [200, 400, 600, 450],
                "block_order": 3,
                "group_id": 1
            }
        ],
        "block_order": [1, 2, 3, 4, 5, ...]
    }
]
```

### Agent的思考过程

```
1️⃣ 接收OCR数据
   ↓
2️⃣ 分析block_order，按推荐顺序扫描
   ↓
3️⃣ 识别题号模式
   - 检测 "1." / "1、" / "（1）" 等
   - 记录题目起始位置
   ↓
4️⃣ 收集题目内容
   - 从题号开始收集后续block
   - 遇到下一个题号停止
   - 包括text、formula、image等
   ↓
5️⃣ 识别题型
   - 是否包含选项 (A/B/C/D) → 选择题
   - 是否包含下划线 → 填空题
   - 是否要求"解答" → 解答题
   ↓
6️⃣ 提取选项（如果是选择题）
   - 识别A. B. C. D.模式
   - 或A) B) C) D)模式
   ↓
7️⃣ 处理特殊内容
   - 公式: has_formula = true
   - 图片: has_image = true, image_refs = [...]
   ↓
8️⃣ 可能的工具调用
   - download_image() - 如需保存图片
   - log_issue() - 如遇到不确定情况
   ↓
9️⃣ 结构化输出
   ↓
🔟 调用 save_questions() 保存结果
```

### Agent工具调用时机

| 工具 | 调用时机 | 示例场景 |
|-----|---------|---------|
| `save_questions` | 必须 | 分割完成后保存题目列表 |
| `log_issue` | 可选 | 题号识别不确定时记录 |
| `download_image` | 可选 | OCR结果包含图片URL时 |
| `read_ocr_result` | 可选 | 需要重新分析OCR数据时 |

### Agent执行日志示例

```
[Agent] 正在分析OCR数据...
[Agent] 识别到题号: "1."
[Agent] 题型判断: 选择题 (检测到选项A、B、C、D)
[Agent] 收集内容块: block_1, block_2, block_3, block_4
[Agent] 检测到公式块: display_formula
[Tool] 调用 save_questions: 保存1道题目
[Agent] 识别到题号: "2."
[Agent] 题型判断: 填空题 (检测到下划线)
[Tool] 调用 log_issue: 题号2的边界不清晰
[Tool] 调用 save_questions: 保存2道题目
[Agent] 分割完成，共处理2道题目
```

---

## 🔧 扩展性设计

### 1. 添加新Agent工具

#### 步骤1: 创建工具文件

在 `error_correction_agent/tools/` 创建新文件（如 `image_tools.py`）:

```python
from langchain_core.tools import tool
from PIL import Image

@tool(parse_docstring=True)
def crop_question_region(image_path: str, bbox: list) -> str:
    """
    根据bbox坐标裁剪题目区域

    Args:
        image_path: 原始图片路径
        bbox: 边界框坐标 [x1, y1, x2, y2]

    Returns:
        裁剪后的图片路径
    """
    img = Image.open(image_path)
    cropped = img.crop(tuple(bbox))

    output_path = f"output/assets/cropped_{os.path.basename(image_path)}"
    cropped.save(output_path)

    return f"已裁剪并保存到: {output_path}"
```

#### 步骤2: 导出工具

在 `error_correction_agent/tools/__init__.py` 添加:

```python
from .image_tools import crop_question_region

__all__ = [
    "save_questions",
    "log_issue",
    "download_image",
    "read_ocr_result",
    "crop_question_region",  # 新增
]
```

#### 步骤3: 绑定到Agent

在 `error_correction_agent/agent.py` 添加:

```python
from .tools import (
    save_questions,
    log_issue,
    download_image,
    read_ocr_result,
    crop_question_region  # 新增
)

def create_question_split_agent():
    tools = [
        save_questions,
        log_issue,
        download_image,
        read_ocr_result,
        crop_question_region,  # 新增
    ]
    ...
```

### 2. 自定义工作流

#### 在现有流程中插入步骤

编辑 `src/workflow.py`:

```python
class ErrorCorrectionWorkflow:

    def run(self, input_file: str, auto_split: bool = False):
        # 原有步骤
        self.image_paths = prepare_input(input_file)
        self.ocr_results = self.paddleocr_parse(self.image_paths)

        # 新增步骤: 手写体识别
        self.classify_handwritten()

        # 继续原有流程
        if auto_split:
            self.questions = self.split_questions_auto()
        ...

    def classify_handwritten(self):
        """新步骤: 识别手写/印刷体"""
        import requests

        for image_path in self.image_paths:
            files = {"image": open(image_path, "rb")}
            response = requests.post(
                "http://localhost:5000/classify",
                files=files
            )
            result = response.json()

            if result["prediction"] == "handwritten":
                console.print(f"[yellow]检测到手写内容: {image_path}[/yellow]")
```

#### 创建新工作流变体

```python
class InteractiveWorkflow(ErrorCorrectionWorkflow):
    """交互式工作流，每步都请求确认"""

    def run(self, input_file: str):
        # 步骤1
        self.image_paths = prepare_input(input_file)
        input("按Enter继续步骤2...")

        # 步骤2
        self.ocr_results = self.paddleocr_parse(self.image_paths)
        input("按Enter继续步骤3...")

        # 步骤3
        self.questions = self.split_questions_with_agent()
        ...
```

### 3. 调整Agent行为

#### 修改提示词

编辑 `error_correction_agent/prompts.py`:

```python
SYSTEM_PROMPT = """# 错题本题目分割专家

...（原有内容）

## 新增规则

### 识别小题
如果题目包含子题（如1. (1) (2) (3)），请拆分为独立题目：
- question_id: "1-1", "1-2", "1-3"
- parent_id: "1"

### 数学题型细分
对于解答题，进一步识别：
- "计算题": 要求计算具体数值
- "证明题": 要求证明结论
- "应用题": 实际问题情景
"""
```

#### 调整模型参数

编辑 `error_correction_agent/agent.py`:

```python
def create_question_split_agent():
    model = init_chat_model(
        model="deepseek:deepseek-chat",
        temperature=0.3,  # 提高温度以增加创造性
        # max_tokens=4000,  # 限制输出长度
    )
    ...
```

#### 添加Few-shot示例

在提示词中添加示例：

```python
SYSTEM_PROMPT = """
...（原有内容）

## 示例

### 示例1: 选择题
输入:
{
  "blocks": [
    {"content": "1. 下列说法正确的是（  ）", ...},
    {"content": "A. 选项1", ...},
    {"content": "B. 选项2", ...}
  ]
}

输出:
{
  "question_id": "1",
  "question_type": "选择题",
  "options": ["A. 选项1", "B. 选项2"],
  ...
}

### 示例2: 填空题
...
"""
```

---

## 📊 技术指标

### 代码规模

| 文件 | 行数 | 主要功能 | 复杂度 |
|-----|------|---------|--------|
| `agent.py` | 56 | Agent创建 | ⭐ |
| `prompts.py` | 133 | 系统提示词 | ⭐⭐ |
| `question_tools.py` | 82 | 题目工具 | ⭐⭐ |
| `file_tools.py` | 68 | 文件工具 | ⭐ |
| `paddleocr_client.py` | 262 | PaddleOCR客户端 | ⭐⭐⭐ |
| `workflow.py` | 214 | 工作流编排 | ⭐⭐⭐⭐ |
| `utils.py` | 365 | 工具函数 | ⭐⭐⭐ |
| **总计** | **1180** | | |

### 核心依赖包

```txt
# Agent框架
deepagents==0.3.5
langchain==1.2.3
langchain-core==1.2.7
langgraph==1.0.5
langchain-deepseek==1.0.1

# 文档处理
pdf2image>=1.16.3
Pillow>=10.0.0

# OCR
# (通过API调用，无需本地依赖)

# 配置和工具
python-dotenv==1.2.1
requests>=2.31.0
rich==14.2.0
pydantic>=2.0.0

# 可选: 手写体识别
torch>=2.0.0
torchvision>=0.15.0
```

### 性能指标

| 步骤 | 平均耗时 | 依赖 |
|-----|---------|------|
| 1. 准备输入 | ~2-5秒/PDF页 | PDF转图片 |
| 2. OCR解析 | ~5-10秒/页 | PaddleOCR API |
| 3. Agent分割 | ~10-30秒/页 | DeepSeek API |
| 4. 生成预览 | <1秒 | 本地HTML生成 |
| 5. 导出错题本 | <1秒 | 本地Markdown生成 |

**总耗时估算**: 约20-50秒/页（主要取决于API响应速度）

---

## 🔍 常见问题

### Q1: Agent分割效果不好怎么办？

**方案1**: 调整提示词
- 编辑 `prompts.py`，添加更详细的规则
- 添加few-shot示例

**方案2**: 调整温度参数
- 在 `agent.py` 中修改 `temperature`
- 建议范围: 0.1-0.3

**方案3**: 查看问题日志
- 检查 `results/split_issues.jsonl`
- 分析Agent记录的不确定情况

### Q2: 如何调试Agent执行过程？

**方法1**: 启用LangSmith追踪
```bash
# 在.env中设置
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_key
LANGSMITH_PROJECT=error-correction
```

**方法2**: 添加日志输出
```python
# 在workflow.py的split_questions_with_agent中
response = agent.invoke(...)
print(f"Agent响应: {response}")
```

### Q3: 如何处理大文件？

**方案1**: 分批处理
```python
workflow = ErrorCorrectionWorkflow()

# 每次只处理几页
for i in range(0, len(pdf_pages), 5):
    batch = pdf_pages[i:i+5]
    workflow.run(batch, auto_split=True)
```

**方案2**: 调整API参数
- 减少DPI（默认300）
- 关闭部分OCR功能开关

### Q4: 如何集成手写体识别？

参考 `docs/HANDWRITTEN_API.md`：

1. 启动服务: `cd printed-vs-handwritten && python app.py`
2. 添加工具到Agent
3. 在工作流中调用分类

---

## 📝 开发规范

### 代码风格
- 遵循PEP 8
- 使用类型提示（Type Hints）
- 函数必须包含Docstring

### 工具定义规范
```python
@tool(parse_docstring=True)  # 必须使用parse_docstring
def tool_name(param: type) -> return_type:
    """
    简短描述（一句话）

    详细说明（可选，多段落）

    Args:
        param: 参数说明

    Returns:
        返回值说明
    """
```

### 提交规范
- 使用语义化提交消息
- 示例: `feat: 添加手写体识别工具`
- 类型: `feat`, `fix`, `docs`, `refactor`, `test`

---

## 🎯 未来计划

### 短期（v1.1）
- [ ] 添加手写体识别集成
- [ ] 优化Agent提示词（few-shot示例）
- [ ] 完善错误处理和日志

### 中期（v1.2）
- [ ] 支持批量处理多个文件
- [ ] Web UI界面
- [ ] 题目难度自动分级

### 长期（v2.0）
- [ ] 支持更多题型（完形填空、阅读理解）
- [ ] 答案自动校对
- [ ] 知识点自动标注

---

## 📚 相关文档

- [README.md](../README.md) - 快速开始指南
- [INDEX.md](INDEX.md) - LangChain文档索引
- [HANDWRITTEN_API.md](HANDWRITTEN_API.md) - 手写体识别API
- [.env.example](../.env.example) - 环境配置模板

---

**文档版本**: v1.0.0
**最后更新**: 2026-01-27
**维护者**: Claude Code Assistant
