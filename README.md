# 错题本生成系统

基于 PaddleOCR + LangChain Agent 的智能错题本生成系统。上传试卷 PDF 或图片，自动识别文档结构、智能分割题目、OCR 纠错，导出为 Markdown 错题本并存入错题库，支持 AI 解题与教学讲解。

## 功能

- **智能分割**：LLM Agent 自动识别题目边界，支持批次并行处理
- **OCR 纠错**：LLM 对识别结果进行结构化纠错，还原原题格式
- **错题库**：SQLite 持久化存储，支持按科目、题型、日期筛选和统计
- **AI 解题**：独立解题 Agent，逐步给出解题过程
- **AI 分析**：教学讲解 Agent，深度分析题目知识点
- **AI 对话**：多轮对话，支持 SSE 流式输出
- **导出**：导出为 Markdown 文件

## 项目结构

```
├── backend/                         # Flask 后端（API + 静态资源托管）
│   ├── config.py                    # 集中配置（路径、目录）
│   ├── llm.py                       # LLM 初始化（DeepSeek / 文心）
│   ├── web_app.py                   # Flask 主应用（路由 + 会话状态）
│   ├── src/                         # 核心模块（LangGraph workflow、OCR 客户端、工具函数）
│   ├── error_correction_agent/      # LangChain Agent（题目分割、OCR 纠错、科目识别）
│   ├── solve_agent/                 # 解题 Agent
│   ├── teach_agent/                 # 教学讲解 Agent（AI 分析功能）
│   ├── benchmark/                   # 模型评测（数据采集、评测运行、指标计算）
│   ├── db/                          # SQLite 数据库（ORM 模型、CRUD）
│   └── tests/                       # 后端测试（19 个测试模块）
├── frontend/                        # Vue 3 + Vite + Tailwind CSS 前端
│   ├── index.html                   # 介绍落地页
│   ├── app.html                     # Vue 工作台入口
│   └── src/
│       ├── App.vue                  # 根组件（侧边栏布局 + 视图路由）
│       ├── components/              # 18 个功能组件
│       └── __tests__/               # 前端测试（Vitest）
├── example_uploads/                 # 示例测试文件（图片 + PDF）
├── .env.example                     # 环境变量模板
└── requirements.txt                 # Python 依赖
```

## 环境部署

### 1. 安装依赖

需要 Python 3.11+、Node.js 18+。

```bash
# 后端依赖
pip install -r requirements.txt

# 前端依赖
cd frontend && npm install
```

### 2. 配置环境变量

```bash
copy .env.example .env
```

编辑 `.env`，填写以下必需项：

```dotenv
# LLM API（OpenAI 兼容接口，支持 OpenAI / DeepSeek / Qwen / Moonshot 等）
OPENAI_API_KEY=your_key
# OPENAI_BASE_URL=https://api.deepseek.com   # 留空则使用 OpenAI 官方；填写后可切换 DeepSeek 等供应商
# OPENAI_MODEL_NAME=gpt-4o-mini              # 默认模型（可选）

# Anthropic API（可选，与 OpenAI 兼容接口二选一或同时配置）
# ANTHROPIC_API_KEY=your_key

# PaddleOCR API（文档结构解析，V2 异步任务接口）
PADDLEOCR_API_URL=https://paddleocr.aistudio-app.com/api/v2/ocr/jobs
PADDLEOCR_API_TOKEN=your_token
PADDLEOCR_MODEL=PaddleOCR-VL-1.5
```

> LLM 至少配置一种（OpenAI 兼容接口或 Anthropic），前端会自动检测可用模型。轻量模型、LangSmith 追踪、PaddleOCR 特性开关等可选配置见 `.env.example`。

### 3. 启动

**开发模式**（前后端分离，支持热更新）：

```bash
# 终端 1：启动后端
cd backend && python web_app.py

# 终端 2：启动前端开发服务器
cd frontend && npm run dev
```

前端开发服务器会自动将 `/api`、`/images`、`/download` 请求代理到后端 `localhost:5001`。

**生产模式**（Flask 托管前端静态资源）：

```bash
# 构建前端
cd frontend && npm run build

# 启动后端（自动托管构建产物）
cd backend && python web_app.py
```

访问 **http://localhost:5001** 即可使用。

## 支持的文件格式

PDF(`.pdf`)、图片(`.jpg` `.jpeg` `.png` `.bmp` `.tiff` `.webp`)，单次上传限制 50 MB。

## 测试

```bash
# 后端测试
cd backend && python -m pytest tests/ -v

# 前端测试
cd frontend && npm test
```

详见 [backend/tests/README.md](backend/tests/README.md) 和 [frontend/src/__tests__/README.md](frontend/src/__tests__/README.md)。

## 许可证

本项目基于 [AGPL-3.0](LICENSE) 开源。任何修改或基于本项目的衍生作品（包括网络服务部署）均须以相同许可证开源。
