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
- Vite 构建
- Tailwind CSS 3（utility-first，class-based dark mode）
- HeadlessUI Vue（`@headlessui/vue`）用于可访问的交互组件
- Font Awesome 图标（fa-solid / fa-regular）
- 纯 JavaScript（不使用 TypeScript）
- 原生 fetch API 进行网络请求（不使用 axios）

### 设计风格

- 配色：slate 作为中性色系，blue 用于主操作，emerald 用于成功状态，rose 用于错误/危险
- 圆角：卡片用 `rounded-2xl`，按钮用 `rounded-lg`，pill 标签用 `rounded-full`
- 阴影：轻量 `shadow-sm`，hover 时 `shadow-md`
- 边框：`border-slate-200`（亮色）/ `border-slate-800`（暗色）
- 字重：标题和按钮用 `font-semibold`，正文用默认
- 间距：容器 `max-w-5xl mx-auto`，内容区 `p-4 sm:p-6`
- 暗色模式：所有元素必须包含 `dark:` 变体，暗色背景用 `slate-900/950`

### 按钮样式规范

- 主按钮：`bg-blue-700 text-white hover:bg-blue-800 focus:ring-4 focus:ring-blue-200`
- 次按钮：`border border-slate-200 bg-white text-slate-700 hover:bg-slate-50`（暗色对应 `dark:border-slate-800 dark:bg-slate-900`）
- 所有按钮：`inline-flex items-center justify-center gap-2 px-4/5 py-2/2.5 text-sm font-semibold transition-colors duration-200 active:scale-[0.98]`
- 禁用态：`disabled:cursor-not-allowed disabled:opacity-50`

### 状态管理

- 用 `ref()` 管理简单状态，`reactive()` 管理对象/数组
- 用 `computed()` 派生状态
- 用 `watch()` 响应数据变化

### 代码规范

- UI 文案使用中文
- API 路径前缀 `/api/`
- 错误处理：`try/catch` + toast 通知用户
- 文件上传使用 `FormData` + XHR（支持进度回调）
- 新功能优先提取为独立 `.vue` 单文件组件放在 `src/components/` 下，使用 `<script setup>` + props/emits 通信
