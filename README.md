# 错题本生成系统

基于 PaddleOCR + LangChain Agent 的智能错题本生成系统。上传试卷 PDF 或图片，自动识别文档结构、智能分割题目，导出为 Markdown 错题本。

## 项目结构

```
├── backend/              # Flask 后端（API + 静态资源托管）
│   ├── src/              # 核心模块（workflow、OCR 客户端、工具函数）
│   ├── error_correction_agent/  # LangChain Agent（分割、纠错）
│   ├── solve_agent/      # 解题智能体
│   ├── benchmark/        # 模型评测
│   ├── db/               # SQLite 数据库（CRUD、模型）
│   └── tests/            # 后端测试
├── frontend/             # Vue 3 + Vite + Tailwind CSS 前端
│   └── src/__tests__/    # 前端测试
├── example_uploads/      # 示例测试文件（图片 + PDF）
├── .env.example          # 环境变量模板
└── requirements.txt      # Python 依赖
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
# DeepSeek API（Agent 智能分割题目）
DEEPSEEK_API_KEY=your_key
DEEPSEEK_BASE_URL=https://api.deepseek.com

# PaddleOCR API（文档结构解析，V2 异步任务接口）
PADDLEOCR_API_URL=https://paddleocr.aistudio-app.com/api/v2/ocr/jobs
PADDLEOCR_API_TOKEN=your_token
PADDLEOCR_MODEL=PaddleOCR-VL-1.5
```

可选配置见 `.env.example`。

### 3. 启动

**开发模式**（前后端分离，支持热更新）：

```bash
cd backend && python web_app.py
```

前端开发服务器会自动将 `/api`、`/images`、`/download` 请求代理到后端。

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

PDF 文件直接发送至 PaddleOCR API 处理，无需本地安装 poppler 等 PDF 转图工具。

## 测试

```bash
# 后端测试
cd backend && python -m pytest tests/ -v

# 前端测试
cd frontend && npm test
```

详见 [backend/tests/README.md](backend/tests/README.md) 和 [frontend/src/__tests__/README.md](frontend/src/__tests__/README.md)。

## 许可证

MIT License
