## 项目重构：代码质量全面改进、安全加固、测试补全与前端规范化

本 PR 对后端和前端进行了全面的代码质量改进，共涉及 37 个文件，净增约 1659 行代码（含大量测试）。

---

### 后端重构与修复（16 个 commit）

#### 1. 提取共享工具函数，消除重复代码
**文件**: `backend/src/utils.py`, `backend/src/workflow.py`, `backend/error_correction_agent/tools/question_tools.py`

- 将 `simplify_ocr_results()` 提取到 `utils.py`，消除两处完全相同的实现
- 将 `run_async()` 提取到 `utils.py`，统一处理同步上下文中运行异步协程的兼容逻辑
- 移除硬编码路径拼接，改为从 `config.py` 导入 `PAGES_DIR`

#### 2. 合并 PaddleOCR 重复的解析方法
**文件**: `backend/src/paddleocr_client.py`

- `parse_image()` 和 `parse_pdf()` 合并为 `_parse_file(file_path, file_type)` 统一方法
- 适配 PaddleOCR V2 异步任务 API，支持 PDF 直传（移除 PDF 转图片流程）
- `_poll_job` 添加 300s 超时上限，防止无限轮询

#### 3. 统一数据库会话管理与序列化
**文件**: `backend/web_app.py`

- 4 个路由统一使用 `with SessionLocal() as db:` 上下文管理器
- 提取 `_serialize_question()` 辅助函数，消除重复的 ORM→dict 序列化
- 修复无扩展名文件上传导致 `rsplit` 崩溃（改用 `os.path.splitext`）
- 修复锁内列表推导式重新赋值的线程安全问题（改为 `remove()` 原地修改）

#### 4. Agent 模块安全加固与健壮性改进
**文件**: `backend/error_correction_agent/agent.py`, `backend/solve_agent/agent.py`

- Agent 缓存访问添加 `threading.Lock` 保护，防止并发竞态
- `solve_agent` 添加重试逻辑和错误处理

#### 5. 消除模块级副作用
**文件**: `backend/config.py`, `backend/llm.py`

- `config.py` 目录创建改为显式调用 `ensure_dirs()`，避免导入时产生副作用
- `llm.py` 移除模块级 `load_dotenv()`，添加 provider 校验
- `benchmark/evaluate.py` 中 `RESULTS_DIR` 重命名为 `BENCHMARK_RESULTS_DIR` 避免语义混淆

#### 6. CRUD 安全修复
**文件**: `backend/db/crud.py`

- `delete_question` 添加 try/except/rollback 事务保护，防止删除失败后会话损坏

#### 7. 修复 Prompt 编号错误
**文件**: `backend/error_correction_agent/prompts.py`

- `SPLIT_PROMPT` 注意事项编号重复问题修正

---

### 测试补全（6 个 commit）

#### 后端测试
**文件**: `backend/tests/` 下多个文件

- 新增 `test_ocr_api.py`：PaddleOCR API 集成测试（异步提交、轮询、结果解析）
- 新增 `test_web_routes.py`：Flask 路由集成测试（status、history、search、stats、delete）
- 新增 `conftest.py`：提取公共 fixture（`db`、`make_question`）供多个测试模块复用
- 新增 `fixtures/sample_ocr_data.json`：固化测试数据，避免依赖运行时文件
- 集成测试添加 `skip_no_api_key` 保护，无 API key 时自动跳过
- `test_crud.py` 改用共享 fixture，`test_utils.py` / `test_workflow_helpers.py` 补充测试用例
- PDF 直传与混合文件类型分发测试

#### 前端测试
**文件**: `frontend/src/__tests__/`

- 新增 `api.test.js`、`state.test.js`、`utils.test.js` 三组前端单元测试
- 提取纯函数到 `utils.js` 以提升可测试性
- 配置 Vite 测试环境

---

### 前端改进（2 个 commit）

**文件**: `frontend/src/App.vue`, `frontend/src/style.css`, `frontend/package.json`

#### 安全加固
- 引入 `dompurify`，对 `v-html` 渲染的 OCR 内容进行 XSS 过滤
- 所有 `fetch` 调用添加 `if (!resp.ok) throw` 防护

#### 样式规范化
- 重复按钮类名提取为 `.btn-primary` / `.btn-success` / `.btn-secondary`
- 修复暗色模式按钮使用半透明背景（改为实色 `dark:bg-slate-900`）

#### 可访问性
- 图片预览弹窗：ESC 关闭、`role="dialog"`、`aria-modal="true"`
- 图片预览弹窗：滚轮缩放（0.25x ~ 5x）、平滑过渡、背景滚动锁定
- 上传拖拽区：`role="button"`、`tabindex="0"`、键盘支持
- 图标按钮：添加 `aria-label`

#### 其他
- 移除多余的 `isUploadBusy()` 包装函数
- `doReset()` 自动选取首个已配置模型，不再硬编码 `deepseek`

---

### 文档更新

- 更新项目 `README.md` 和测试 `tests/README.md`
- 新增 `.env.example` 配置说明
- 新增前端测试 `__tests__/README.md`

---

### Commit 列表

| Commit | 说明 |
|--------|------|
| `03a0cff` | refactor(backend): 提取共享工具函数到 utils.py，消除重复代码 |
| `18fc35c` | refactor(backend): 合并 PaddleOCR 重复的解析方法 |
| `4933550` | refactor(backend): 统一 web_app.py 数据库会话管理与序列化 |
| `e5eaeb9` | fix(backend): 修复 SPLIT_PROMPT 注意事项编号重复 |
| `91d26f9` | feat(frontend): 安全加固、样式提取与可访问性改进 |
| `780c6fe` | feat(frontend): 图片预览弹窗滚轮缩放 |
| `2a11c45` | refactor(frontend): 提取纯函数到 utils.js |
| `01e2a5c` | test(frontend): 新增前端测试脚本 |
| `c719536` | refactor(backend): 适配 PaddleOCR V2 异步任务 API |
| `ee95fd8` | test(backend): 新增 PaddleOCR API 集成测试 |
| `bd2d2c7` | refactor(backend): 移除 PDF 转图片，PDF 直传 OCR API |
| `1bc5470` | test(backend): 补充 PDF 直传与混合文件类型分发测试 |
| `d1c522e` | docs: 更新项目 README 和测试文档 |
| `203a6e9` | fix(backend): web_app 安全加固与健壮性修复 |
| `d2253b1` | fix(backend): Agent 模块安全加固与健壮性改进 |
| `c2d2fd3` | refactor(config): 消除模块级副作用，目录创建改为显式调用 |
| `fd051fe` | fix(llm): 移除模块级 load_dotenv，添加 provider 校验 |
| `f1eeb0b` | refactor(benchmark): RESULTS_DIR 重命名为 BENCHMARK_RESULTS_DIR |
| `2971c1e` | test: 集成测试添加 skip 保护，测试数据固化到 fixtures |
| `451d942` | test: 提取公共 fixture 到 conftest，新增路由测试，修复 OCR 断言 |
| `9195641` | docs(tests): README 移除硬编码计数，补充新增文件说明 |
| `8039314` | fix(web): 修复文件名解析崩溃和锁内列表赋值的线程安全问题 |
| `8dd57a2` | fix(crud): delete_question 添加事务回滚保护 |
| `cbcd727` | fix(ocr): _poll_job 添加 300s 超时上限，防止无限轮询 |
| `12e74ac` | fix(agent): 解决 rebase 残留的冲突标记 |

---

### 测试计划

- [ ] 上传 PDF/图片，验证 OCR 解析和题目分割流程正常
- [ ] 验证暗色模式下按钮样式一致（无半透明背景）
- [ ] 验证图片预览弹窗 ESC 关闭、滚轮缩放、键盘可访问性
- [ ] 验证历史记录、搜索、统计、删除等数据库相关接口正常
- [ ] 验证 v-html 内容已被 DOMPurify 过滤
- [ ] 运行 `pytest` 后端测试全部通过
- [ ] 运行 `npm test` 前端测试全部通过
- [ ] 验证无 API key 时集成测试自动跳过
