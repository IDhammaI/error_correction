# CLAUDE.md — LangChain（Python）本地文档按需检索与编码规范

本项目包含一份 LangChain（Python）本地文档快照。你（Claude Code）在实现功能或回答问题时，必须遵循“按需检索、最小读取、可追溯引用”的原则：**不要一次性阅读全部文档**，而是先定位章节，再只打开最相关的少量片段。

---

## 1) 文档范围（仅限本地快照所覆盖的主题）

本地文档导航结构如下（以侧边栏为准）：

- Core components
  - Agents
  - Models
  - Messages
  - Tools
  - Short-term memory
  - Streaming
    - Overview
    - Frontend
  - Structured output
- Middleware
  - Overview
  - Built-in middleware
  - Custom middleware
- Advanced usage
  - Guardrails
  - Runtime
  - Context engineering
  - Model Context Protocol (MCP)
  - Human-in-the-loop
  - Multi-agent
    - Overview
    - Subagents
    - Handoffs
    - Skills
    - Router
    - Custom workflow
  - Retrieval
  - Long-term memory
- Agent development
  - LangSmith Studio
  - Test
  - Agent Chat UI
- Deploy with LangSmith
  - Deployment
  - Observability

**注意**：如果用户问题超出上述主题覆盖范围，必须明确说明“本地快照未覆盖”，再给出合理替代方案（例如：建议查阅官方在线文档或补充资料）。

---

## 2) 文档目录约定（需要你先自检并使用实际路径）

默认约定文档位于（示例）：
- `docs/langchain-python/` 或 `docs/` 或 `documentation/`

你必须先通过目录查看确认真实根路径：
- 在 VS Code 中使用 `@` 引用目录（只获取目录列表，不读取全文）
- 或使用 Glob/文件树查看

一旦确认根路径，将其在本次会话中作为 `DOC_ROOT` 使用。


当需要使用本地 LangChain 文档时，必须优先读取 docs/langchain/INDEX.md；除非 INDEX.md 无法定位，再按需读取 1–3 个相关页面片段（禁止整库加载）。

---

## 3) 前端开发规范

进行前端开发时，必须严格遵循以下技术栈和代码风格。

### 技术栈

- Vue 3 + `<script setup>`（Composition API，不使用 Options API）
- Vite 构建（多页面入口：`index.html` 介绍页 + `app.html` 工作台）
- Tailwind CSS 3（utility-first，class-based dark mode）
- HeadlessUI Vue（`@headlessui/vue`）用于可访问的交互组件
- DOMPurify（`dompurify`）用于 OCR 题目文本的 HTML 净化
- 纯 JavaScript（不使用 TypeScript）
- 原生 fetch API 进行网络请求（不使用 axios）；文件上传使用 XHR（支持进度回调）
- CDN 外部依赖（在 `app.html` 中引入，非 npm 包）：
  - Font Awesome 6.5 — 图标（fa-solid / fa-regular）
  - MathJax 3 — LaTeX 公式渲染
  - SortableJS 1.15 — 题目拖拽排序
  - Chart.js 4 — Dashboard 图表（可选，离线降级）

### 前端项目结构

```
frontend/
├── index.html                 # 介绍落地页（纯 HTML + Tailwind CDN）
├── app.html                   # Vue 工作台入口（含 CDN preload）
├── vite.config.js             # 多页面构建，dev proxy → localhost:5001
├── tailwind.config.js         # class-based dark mode
├── src/
│   ├── main.js                # createApp + mount
│   ├── App.vue                # 根组件（布局 + 视图路由 + 全局状态）
│   ├── api.js                 # fetch/XHR 封装（upload, split, export, status）
│   ├── utils.js               # 纯函数（fileKey, sanitizeHtml, clampScale）
│   ├── style.css              # Tailwind 指令 + 自定义样式（进度环、toast 动画等）
│   ├── components/
│   │   ├── StatusBar.vue      # 系统状态 + 模型选择器（HeadlessUI Listbox）
│   │   ├── StepIndicator.vue  # 4 步工作流进度指示器
│   │   ├── FileUploader.vue   # 文件拖放 + 进度环
│   │   ├── QuestionList.vue   # 题目网格 + SortableJS 拖拽排序
│   │   ├── QuestionCard.vue   # 单题卡片（题干 / 选项 / 图片）
│   │   ├── ActionBar.vue      # 分割 / 导出 / 重置按钮组
│   │   ├── ImageModal.vue     # 全屏图片查看器（滚轮缩放）
│   │   ├── ToastContainer.vue # Toast 通知栈
│   │   ├── Dashboard.vue      # 错题本数据看板（Chart.js）
│   │   └── CatLoading.vue     # 像素猫 loading 遮罩
│   └── __tests__/             # Vitest 测试套件
│       ├── api.test.js        # API 交互与按钮状态测试
│       ├── state.test.js      # 组件状态逻辑测试
│       └── utils.test.js      # 纯函数单元测试
```

### 布局架构

- **PC 端**：左侧固定侧边栏（`aside w-64`）+ 右侧主内容区
- **移动端**：底部 Tab 导航栏（`fixed bottom-0`）+ 全宽内容区
- 视图切换：`currentView` ref 控制 `'workspace'` / `'dashboard'` 两个视图（`v-show` 切换）
- 返回介绍页链接使用 `href="/"`（匹配 Flask 根路由）

### 设计风格

- 配色：slate 中性色系，blue / indigo 主操作，emerald 成功，rose 错误
- 圆角：卡片 `rounded-2xl` / `rounded-3xl`，按钮 `rounded-xl`，pill 标签 `rounded-full`
- 阴影：轻量 `shadow-sm`，hover `shadow-md`，主按钮 `shadow-xl`
- 边框：`border-slate-200/60`（亮色）/ `border-white/10`（暗色），半透明风格
- 玻璃态：`bg-white/70 backdrop-blur-xl`（亮色）/ `bg-[#0A0A0F]/60 backdrop-blur-xl`（暗色）
- 字重：标题和按钮用 `font-bold` / `font-extrabold`，正文用默认
- 间距：容器 `max-w-5xl mx-auto`，内容区 `p-5 sm:p-8`
- 暗色模式：所有元素必须包含 `dark:` 变体，暗色背景用 `slate-900/950` 或 `[#0A0A0F]`
- 主题切换：支持 View Transitions API 圆形扩散动画，降级为即时切换

### 按钮样式规范

- 主按钮（分割）：渐变光晕 + `bg-blue-600 text-white`，`rounded-xl h-12`
- 成功按钮（导出）：`border-emerald-500/30 bg-emerald-50/80 text-emerald-700`
- 次按钮（重置）：`border-slate-200/60 bg-white/60 text-slate-700`
- 所有按钮：`inline-flex items-center justify-center gap-2 text-sm font-bold transition-all duration-200/300`
- 禁用态：`disabled:cursor-not-allowed disabled:opacity-50`

### 状态管理

- 无状态管理库（Pinia/Vuex），全局状态集中在 `App.vue`
- 用 `ref()` 管理简单状态，`reactive()` 管理对象/数组/Set
- 用 `computed()` 派生状态
- 用 `watch()` 响应数据变化
- 父子通信：props 向下传递，emits 向上通知

### 代码规范

- UI 文案使用中文
- API 路径前缀 `/api/`，dev 环境通过 Vite proxy 转发到 `localhost:5001`
- 错误处理：`try/catch` + toast 通知用户
- HTML 渲染使用 `DOMPurify` 净化，白名单在 `utils.js` 的 `ALLOWED_HTML_TAGS` 定义
- 新功能优先提取为独立 `.vue` 单文件组件放在 `src/components/` 下，使用 `<script setup>` + props/emits 通信
- 关键 DOM 元素添加语义类名（如 `.step-circle`）或 `data-testid`，供测试定位

---

## 4) 后端开发规范

### 项目结构

```
backend/
├── config.py                  # 集中配置（路径、目录），ensure_dirs() 显式初始化
├── llm.py                     # 公共 LLM 初始化（init_model），支持 deepseek / ernie
├── web_app.py                 # Flask 主应用，路由 + 全局会话状态
├── db/
│   ├── models.py              # SQLAlchemy ORM 模型
│   └── crud.py                # 数据库 CRUD 操作
├── src/
│   ├── workflow.py            # 主工作流（OCR → 分割 → 纠错 → 保存）
│   ├── paddleocr_client.py    # PaddleOCR V2 异步任务 API 客户端
│   └── utils.py               # 共享工具函数（simplify_ocr_results, run_async 等）
├── error_correction_agent/    # 题目分割 + OCR 纠错智能体
│   ├── agent.py               # Agent 工厂（create_agent + ToolStrategy）
│   ├── prompts.py             # 系统提示词
│   ├── schemas.py             # Pydantic 结构化输出 Schema
│   └── tools/                 # LangChain Tool 定义
├── solve_agent/               # 解题智能体
├── benchmark/                 # 模型评测模块
└── tests/                     # 测试套件
    ├── conftest.py            # 公共 fixture（db, make_question）
    ├── fixtures/              # 测试数据文件
    └── test_*.py              # 测试模块
```

### 模块级副作用

- **禁止在模块顶层执行有副作用的操作**（创建目录、写文件、启动连接等）
- `config.py` 的目录创建通过 `ensure_dirs()` 显式调用，不在 `import` 时触发
- `load_dotenv()` 仅在入口文件（`web_app.py`）或需要环境变量的模块中调用，不在公共库模块调用

### 数据库操作

- 使用 `with SessionLocal() as db:` 上下文管理器管理会话生命周期
- 涉及写操作的函数必须包含 `try/except` + `db.rollback()`，防止事务损坏
- ORM→dict 序列化使用 `_serialize_question()` 等统一辅助函数，避免重复代码

### 线程安全

- Flask 全局会话状态（`session_files`, `session_file_order` 等）的修改必须在 `session_lock`（`threading.Lock`）保护下进行
- 锁内操作列表时使用原地修改（`.remove()`, `.append()`），**不要用推导式重新赋值**
- Agent 缓存（`_agent_cache`）通过 `_agent_cache_lock` 保护并发初始化

### LLM 与 Agent

- 结构化输出优先使用 `create_agent` + `ToolStrategy`，保证输出质量
- 已知问题：`ToolStrategy` 与 DeepSeek API 的 `handle_errors` 重试存在兼容性问题，大数据量时可能触发 400 错误
- ernie 使用 `model.with_structured_output()` 替代方案（因不支持 function calling）
- 轻量任务（如科目识别）使用 `DEEPSEEK_LIGHT_MODEL_NAME` / `ERNIE_LIGHT_MODEL_NAME` 配置的小模型，降低成本
- `invoke_split` / `invoke_correction` 是统一调用入口，屏蔽不同 provider 的实现差异

### OCR 数据处理

- `simplify_ocr_results()` 是 OCR 原始结果到 Agent 输入的唯一转换点
- 该函数负责 block_label 归一化（如 `display_formula` → `formula`，`number` → `text`），下游代码只应接收已知标签
- 新增 OCR block_label 类型时，必须在此函数中添加归一化映射
- OCR 数据流向：PaddleOCR API → `simplify_ocr_results()` → `split_batch` → LLM Agent

### 并行处理

- **LLM 分割**：`ThreadPoolExecutor` 并行，上限 `min(len(batches), 3)`（`workflow.py`）
- **OCR 图片解析**：`asyncio.gather()` 并行，目前无并发上限（仅 stagger_delay=1s 错峰）
- 批次构建使用 2 页/批、1 页重叠的滑动窗口策略，去重使用 `_dedup_questions()` 按内容丰富度保留

### 文件与路径

- 所有运行时路径通过 `config.py` 集中管理（`RESULTS_DIR`, `PAGES_DIR` 等），禁止硬编码
- 文件名解析使用 `os.path.splitext()`，**不要用 `rsplit('.', 1)`**（无扩展名时会崩溃）
- 文件上传使用 `uuid.uuid4().hex` 生成安全文件名

### 环境变量

- `.env` 不纳入版本控制，`.env.example` 作为配置模板纳入版本控制
- 新增配置项时必须同步更新 `.env.example`，附带注释说明
- 可选配置项使用 `os.getenv("KEY")` 返回 `None`，在代码中提供回退默认值

---

## 5) 测试规范

### 运行方式

```bash
# 工作目录必须是 backend/
cd backend
C:/ProgramData/miniconda3/envs/da/python.exe -m pytest tests/ -v
```

### 测试组织

- 单元测试（无外部依赖）：`test_utils.py`, `test_crud.py`, `test_web_routes.py` 等
- 集成测试（依赖 API）：`test_split_integration.py`, `test_solve_integration.py`, `test_ocr_api.py`
- 集成测试必须添加 `skip_no_api_key` 保护，无 API key 时自动跳过
- 已知兼容性问题的测试用 `@pytest.mark.xfail(reason="...")` 标记，不要删除测试

### 公共 Fixture

- `conftest.py` 提供共享 fixture（`db` 内存数据库、`make_question` 工厂函数）
- 新增测试模块应优先复用 `conftest.py` 中的 fixture，避免重复定义
- 测试数据文件放在 `tests/fixtures/` 目录下

### 测试原则

- **不要为了通过测试而修改测试脚本**——测试应反映项目的实际需求
- 测试失败时应修复代码逻辑，而非放宽断言条件
- 新增功能或修复 bug 时应同步补充对应的测试用例

---

## 6) Git 提交规范

### Commit 格式

```
<type>(<scope>): <中文描述>

```

### Type 类型

- `feat` — 新功能
- `fix` — 修复 bug
- `refactor` — 重构（不改变行为）
- `test` — 测试相关
- `docs` — 文档
- `config` — 配置变更

### 原则

- 按逻辑拆分 commit，每个 commit 聚焦一个变更主题
- 描述使用中文，简洁明确
- `.env` 文件永远不要提交到版本控制
