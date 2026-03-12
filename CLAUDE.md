# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 常用命令

### 开发模式（前后端分离，热更新）

```bash
# 终端 1：后端
cd backend && python web_app.py          # Flask on localhost:5001

# 终端 2：前端
cd frontend && npm run dev               # Vite dev server, proxy /api → :5001
```

### 生产构建

```bash
cd frontend && npm run build             # 输出到 backend 静态目录
cd backend && python web_app.py          # Flask 托管前端产物，访问 :5001
```

### 测试

```bash
# 后端（工作目录必须是 backend/）
cd backend
C:/ProgramData/miniconda3/envs/da/python.exe -m pytest tests/ -v          # 全量
C:/ProgramData/miniconda3/envs/da/python.exe -m pytest tests/test_utils.py -v  # 单个模块
C:/ProgramData/miniconda3/envs/da/python.exe -m pytest tests/test_utils.py::test_name -v  # 单个用例

# 前端（工作目录必须是 frontend/）
cd frontend
npm test                                 # vitest run（单次）
npm run test:watch                       # vitest watch 模式
```

### 依赖安装

```bash
pip install -r requirements.txt          # 后端（Python 3.11+）
cd frontend && npm install               # 前端（Node 18+）
```

### 环境配置

复制 `.env.example` → `.env`，至少配置一组 LLM API key（DeepSeek 或 ERNIE）和 PaddleOCR token。详见 `.env.example` 注释。

---

## 系统架构

**错题本生成系统**：上传试卷 PDF/图片 → OCR 结构化识别 → LLM Agent 智能分割题目 → 纠错 → 导出 Markdown / 存入错题库。

### 核心数据流

```
用户上传文件
  → prepare_input（PDF 转图片）
  → PaddleOCR API（异步任务，asyncio.gather 并行）
  → simplify_ocr_results()（block_label 归一化，唯一转换点）
  → split_batch（2 页/批滑动窗口，ThreadPoolExecutor 并行，上限 3）
  → LLM Agent 分割题目（invoke_split）
  → _dedup_questions()（跨批次去重）
  → LLM Agent 纠错（invoke_correction）
  → 导出 / 保存数据库
```

### 关键模块关系

- **`backend/src/workflow.py`** — LangGraph StateGraph 主工作流，串联所有处理步骤
- **`backend/error_correction_agent/`** — 题目分割 + OCR 纠错 Agent（`create_agent` 工厂函数）
- **`backend/solve_agent/`** — 独立的解题 Agent
- **`backend/web_app.py`** — Flask 主应用，路由 + 全局会话状态（`session_lock` 保护）
- **`backend/config.py`** — 所有运行时路径集中管理，`ensure_dirs()` 显式初始化
- **`backend/llm.py`** — `init_model()` 统一 LLM 初始化，支持 deepseek / ernie
- **`backend/db/`** — SQLite + SQLAlchemy ORM，错题库持久化
- **`frontend/src/App.vue`** — 根组件，全局状态集中于此（无 Pinia/Vuex）

### Flask 路由

- `GET /` → 介绍页 | `GET /app` → Vue 工作台
- `POST /api/upload` / `/api/split` / `/api/export` / `/api/cancel_file` — 业务 API
- `GET /api/status` — 系统状态（OCR 配置、可用模型列表）

---

## 本地 LangChain 文档

本项目包含 LangChain（Python）本地文档快照，入口为 `docs/INDEX.md`。

**使用原则**：按需检索、最小读取。先读 `docs/INDEX.md` 定位章节，再只打开 1–3 个相关片段（禁止整库加载）。

覆盖主题：Core components（Agents, Models, Messages, Tools, Streaming, Structured output）、Middleware、Advanced usage（Guardrails, MCP, Multi-agent, Retrieval）、Agent development、Deploy with LangSmith。超出覆盖范围的问题必须明确说明。

---

## 前端开发规范

### 技术栈

- Vue 3 + `<script setup>`（Composition API，不使用 Options API）
- Vite 多页面入口：`index.html`（介绍页）+ `app.html`（工作台）
- Tailwind CSS 3（utility-first，class-based dark mode）
- HeadlessUI Vue 用于可访问交互组件
- DOMPurify 用于 HTML 净化（白名单在 `utils.js` 的 `ALLOWED_HTML_TAGS`）
- 纯 JavaScript（不使用 TypeScript），原生 fetch（不使用 axios），文件上传用 XHR
- CDN 外部依赖（非 npm）：Font Awesome 6.5、MathJax 3、SortableJS 1.15、Chart.js 4

### 布局

- **PC 端**：左侧固定侧边栏（`aside w-64`）+ 右侧主内容区
- **移动端**：底部 Tab 导航栏（`fixed bottom-0`）+ 全宽内容区
- `currentView` ref 控制 `'workspace'` / `'dashboard'` 视图（`v-show` 切换）

### 设计风格

- 配色：slate 中性色系，blue/indigo 主操作，emerald 成功，rose 错误
- 圆角：卡片 `rounded-2xl`/`rounded-3xl`，按钮 `rounded-xl`，pill `rounded-full`
- 玻璃态：`bg-white/70 backdrop-blur-xl`（亮色）/ `bg-[#0A0A0F]/60 backdrop-blur-xl`（暗色）
- 边框：`border-slate-200/60`（亮色）/ `border-white/10`（暗色）
- **所有元素必须包含 `dark:` 变体**，暗色背景用 `slate-900/950` 或 `[#0A0A0F]`
- 主题切换支持 View Transitions API 圆形扩散动画

### 按钮样式

- 主按钮：`bg-blue-600 text-white rounded-xl h-12` + 渐变光晕
- 成功按钮：`border-emerald-500/30 bg-emerald-50/80 text-emerald-700`
- 次按钮：`border-slate-200/60 bg-white/60 text-slate-700`
- 通用：`inline-flex items-center justify-center gap-2 text-sm font-bold transition-all`
- 禁用：`disabled:cursor-not-allowed disabled:opacity-50`

### 状态管理与代码规范

- 无状态管理库，全局状态集中在 `App.vue`（ref/reactive/computed/watch）
- 父子通信：props 向下，emits 向上
- UI 文案使用中文，API 路径前缀 `/api/`
- 新功能提取为独立 `.vue` 组件放 `src/components/`
- 关键 DOM 元素添加语义类名或 `data-testid`

---

## 后端开发规范

### 模块级副作用

- **禁止在模块顶层执行有副作用的操作**（创建目录、写文件、启动连接等）
- `config.py` 目录创建通过 `ensure_dirs()` 显式调用
- `load_dotenv()` 仅在入口文件或需要环境变量的模块中调用

### 数据库

- `with SessionLocal() as db:` 管理会话生命周期
- 写操作必须 `try/except` + `db.rollback()`
- ORM→dict 用 `_serialize_question()` 等统一辅助函数

### 线程安全

- Flask 全局状态修改必须在 `session_lock` 保护下
- 锁内用原地修改（`.remove()`, `.append()`），**不要用推导式重新赋值**
- Agent 缓存通过 `_agent_cache_lock` 保护并发初始化

### LLM 与 Agent

- 结构化输出优先用 `create_agent` + `ToolStrategy`
- 已知问题：`ToolStrategy` 与 DeepSeek 的 `handle_errors` 重试不兼容，大数据量可能触发 400
- ernie 用 `model.with_structured_output()`（不支持 function calling）
- 轻量任务用 `DEEPSEEK_LIGHT_MODEL_NAME` / `ERNIE_LIGHT_MODEL_NAME` 小模型
- `invoke_split` / `invoke_correction` 是统一调用入口，屏蔽 provider 差异

### OCR 数据处理

- `simplify_ocr_results()` 是 OCR → Agent 输入的唯一转换点，负责 block_label 归一化
- 新增 block_label 类型时必须在此函数添加映射
- 批次构建：2 页/批、1 页重叠滑动窗口；去重按内容丰富度保留

### 文件与路径

- 所有运行时路径通过 `config.py` 集中管理，禁止硬编码
- 文件名解析用 `os.path.splitext()`，**不要用 `rsplit('.', 1)`**
- 文件上传用 `uuid.uuid4().hex` 生成安全文件名

### 环境变量

- `.env` 不入版本控制，`.env.example` 作为模板
- 新增配置项必须同步更新 `.env.example`
- 可选项用 `os.getenv("KEY")` + 代码中提供默认值

---

## 测试规范

### 测试组织

- 单元测试（无外部依赖）：`test_utils.py`, `test_crud.py`, `test_web_routes.py`, `test_web_helpers.py`, `test_schemas.py` 等
- 集成测试（依赖 API）：`test_split_integration.py`, `test_solve_integration.py`, `test_ocr_api.py`
- 集成测试必须添加 `skip_no_api_key` 保护
- 已知兼容性问题用 `@pytest.mark.xfail(reason="...")` 标记，不要删除测试
- 公共 fixture 在 `conftest.py`（`db` 内存数据库、`make_question` 工厂），优先复用
- 测试数据文件放 `tests/fixtures/`
- 前端测试环境：jsdom + @vue/test-utils，HeadlessUI 通过 `stubs` 跳过

### 测试原则

- **不要为了通过测试而修改测试脚本**——修复代码逻辑，而非放宽断言
- 新增功能/修复 bug 时同步补充测试
- 重构组件时同步更新选择器（类名、文本）

---

## Git 提交规范

格式：`<type>(<scope>): <中文描述>`

Type：`feat`（新功能）、`fix`（修复）、`refactor`（重构）、`test`、`docs`、`config`

原则：按逻辑拆分 commit，描述用中文，`.env` 永不提交。
