# 项目规范 (Project Rules)

本文档总结了当前“基于 LLM + OCR 的智能错题本生成系统”的项目规范、架构设计、技术栈以及开发工作流，以确保团队开发的一致性。

## 1. 项目概述与核心架构

本项目采用前后端分离架构，核心业务流为：**上传试卷（PDF/图片） → OCR 结构化识别 → LLM Agent 智能分割题目 → 纠错 → 导出 / 存入错题库**。

- **后端工作流控制**：使用 LangGraph (`backend/src/workflow.py`) 串联所有处理步骤。
- **Agent 设计**：分为题目分割纠错 (`error_correction`)、解题 (`solve`)、教学对话 (`teach`)、笔记整理 (`note`) 等多个独立 Agent。
- **纯 API 服务**：Flask 后端仅提供 API 接口（监听 5001 端口），不负责前端页面的渲染和托管。

## 2. 技术栈规范

### 2.1 前端 (Frontend)
- **核心框架**：Vue 3 + Vite + Vue Router 4。
- **代码风格**：
  - 必须使用 `<script setup>` (Composition API)，**严禁**使用 Options API。
  - 使用纯 JavaScript 开发，**不使用 TypeScript**。
- **样式与 UI**：
  - Tailwind CSS 3 (Utility-first，基于 class 的暗色模式) + `@tailwindcss/typography`。
  - 使用 HeadlessUI Vue 处理可访问交互组件。
  - 设计风格采用 **Glass Morphism + Linear**（以暗色为主，兼容亮色），大量使用 `backdrop-blur` 和透明度处理。
- **网络请求**：使用原生 `fetch` 统一封装在 `api.js` 中，**不使用 Axios**；文件上传使用原生 XHR。
- **第三方库引入**：部分依赖（如 Font Awesome 6.5, MathJax 3, SortableJS, Chart.js, marked）通过 CDN 外部引入，而非 npm。
- **安全性**：渲染富文本必须通过 DOMPurify 净化（`utils.js` 中的 `sanitizeHtml`）。

### 2.2 后端 (Backend)
- **核心语言与框架**：Python 3.11+，Flask (3.1.2)。
- **AI 与大模型**：LangChain, LangGraph, 默认支持 OpenAI / Anthropic / DeepSeek / PaddleOCR。
- **数据库**：SQLite + SQLAlchemy ORM (位于 `backend/db/`)。
- **架构规范**：
  - Flask 应用采用工厂模式 (`web_app.py`)。
  - 路由必须在 `backend/routes/` 下以 Blueprint 模块化拆分（如 upload, questions, chat 等）。
  - 全局状态管理通过 `backend/core/state.py` 维护。
  - 环境与配置统一由 `backend/core/config.py` 读取项目根目录的 `.env`。

## 3. 目录结构规范

### 3.1 前端结构 (`frontend/src/`)
- `components/`: 页面可复用组件（如 `base/`, `auth/`, `workspace/` 等）。
- `composables/`: Vue 3 组合式函数，统一命名为 `useXXX.js`（如 `useAuth.js`, `useTheme.js`）。
- `views/`: 页面级组件，通过路由直接映射。
- `api.js`: 集中式 API 请求层。
- `utils.js`: 通用工具函数。

### 3.2 后端结构 (`backend/`)
- `agents/`: 各类 LLM Agent 的定义、Prompt 和 Schema。
- `core/`: 系统核心配置、全局状态、LLM 初始化逻辑等。
- `db/`: 数据库模型、迁移脚本及 CRUD 操作封装。
- `routes/`: Flask Blueprint 路由控制器。
- `src/`: 核心业务逻辑（如 `workflow.py`，`utils.py`）。

## 4. 开发与运行规范

### 4.1 环境配置
- 必须将 `backend/.env.example` 复制为项目根目录的 `.env`。
- 必须配置 `SECRET_KEY`。LLM API Provider 现已支持在系统前端页面（数据库）中动态配置，SMTP 等配置通过环境变量加载。

### 4.2 开发模式（热更新）
前后端需分别启动独立终端：
- **后端**：`cd backend && python web_app.py` (运行在 localhost:5001)
- **前端**：`cd frontend && npm run dev` (Vite 开发服务器，默认代理 `/api` 请求至 5001 端口)

### 4.3 测试规范
- **后端**：在 `backend/` 目录下运行 `pytest tests/ -v`。
- **前端**：在 `frontend/` 目录下运行 `npm test` (使用 Vitest)。

### 4.4 生产构建
- 前端产物通过 `cd frontend && npm run build` 生成，供独立的 Web 服务器（如 Nginx）托管部署。
- 后端仅需运行 `python web_app.py` 作为纯 API 提供服务。

## 5. 代码注释规范

注释用于解释代码背后的意图、约束、原因和边界，不用于重复代码表面行为。项目中应优先写“为什么这样做”，少写“这行代码做了什么”。

### 5.1 基本原则
- **不要翻译代码**：避免写“设置 loading 为 true”“调用某函数”这类从代码本身即可读出的注释。
- **解释原因和约束**：当代码涉及业务规则、兼容处理、状态同步、布局避让、权限判断、异步时序时，应写明原因。
- **注释应保持可维护**：不要写容易随 UI 数量、样式细节变化而过期的描述。
- **优先注释复杂流程入口**：路由守卫、上传流程、OCR 流程、AI 分析流程、错题迁移流程等应在入口处说明整体意图。
- **边界条件必须说明**：例如移动端与桌面端逻辑不同、登录态恢复、防止重复提交、避免白屏或遮挡等。

### 5.2 前端注释规则
- `main.js`：只说明应用启动链路，如创建 Vue 应用、注册路由、挂载入口。
- `App.vue`：只说明全局能力，如路由出口、全局 Toast、全局 Loading、主题初始化；避免在根组件堆放具体业务判断。
- `router/index.js`：说明页面分组、鉴权规则、重定向规则和跨布局过渡逻辑。
- `composables/useXXX.js`：说明该 composable 管理的状态职责、业务规则和边界条件。
- `components/base/`：基础 UI 组件少写注释，只注释特殊 props、无障碍处理、兼容处理、定位或层级约束。
- `views/` 与业务组件：优先注释交互流程、接口调用时序、异常分支和非显然的状态转换。
- `<template>` 中少写注释；只有结构不直观、插槽/浮层/固定定位/条件渲染有特殊原因时才写。

### 5.3 推荐写法

推荐：

```js
// 首次导航时刷新登录态，避免页面刷新后本地状态丢失导致误跳登录页。
await refreshCurrentUser()
```

推荐：

```js
// 只有工作台布局存在侧边栏，非 app 页面不需要为全局浮层预留左侧空间。
if (!isInAppLayout.value || isMobile.value) return 0
```

不推荐：

```js
// 设置 loading 为 true
loading.value = true
```

不推荐：

```js
// 循环 toast 列表
toasts.value.forEach(...)
```

### 5.4 文件顶部注释

文件顶部注释只写职责，不写流水账，不记录容易过期的实现细节。

推荐：

```js
/**
 * useWorkspaceNav
 * 管理工作台路由视图、侧边栏状态和导航项配置。
 */
```

不推荐：

```js
/**
 * 这里定义了很多变量、很多函数，然后导出 useWorkspaceNav。
 */
```
