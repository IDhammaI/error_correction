# AGENTS

本文件用于说明项目规则目录 `rules/` 的结构，方便在开始开发或修改代码前快速定位需要查看的规范。

## 规则目录

### `rules/development`

- `development/架构规则.md`：项目架构、核心入口和本地文档使用原则。
- `development/前端规则.md`：Vue、API 调用、主题、组件和设计规则。
- `development/后端规则.md`：模块副作用、数据库、线程安全、Agent、OCR 和文件路径规则。
- `development/测试规则.md`：测试组织、断言原则和外部依赖保护。
- `development/代码注释规则.md`：注释意图、前端注释位置和推荐写法。

### `rules/workflow`

- `workflow/提交规则.md`：commit message 格式和强制 checklist 要求。
- `workflow/常用命令索引.md`：本地命令类规则入口。
- `workflow/环境配置规则.md`：依赖安装、环境变量和 Provider 配置。
- `workflow/开发启动规则.md`：前后端开发服务、conda 环境和端口检查。
- `workflow/测试构建规则.md`：后端测试、前端测试和生产构建。
- `workflow/变更同步规则.md`：跨后端、前端、文档、配置和测试的同步要求。
- `workflow/协作提交流程规则.md`：fork、个人分支、PR 和 review 流程要求。

## 使用建议

- 开始任务前，先查看本文件。
- 涉及前端改动时，优先查看 `development/前端规则.md`。
- 涉及后端改动时，优先查看 `development/后端规则.md`。
- 涉及测试、构建、提交流程时，查看 `development/测试规则.md` 和 `workflow/` 下对应文件。
- 修改规则时，优先更新对应规则文件，而不是只改本文件。
