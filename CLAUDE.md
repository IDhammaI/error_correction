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
