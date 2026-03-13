## Summary

- 新增**分割历史记录**功能：每次题目分割完成后自动保存结果到数据库，支持按时间倒序查询
- 新增 `SplitRecord` ORM 模型及对应的 `split_records` 数据库表
- 新增 CRUD 操作：保存、列表查询（延迟加载大字段）、按 ID 查询详情
- 新增 REST API：`GET /api/split-records`（分页列表）、`GET /api/split-records/<id>`（详情）
- 自动清理机制：记录数超过上限（默认 20 条）时自动删除最旧数据
- 提取 `_read_split_subject()` 复用逻辑，消除 `split_questions` 与 `save_to_db` 中的重复代码
- 同步更新 CLAUDE.md：补充路由文档与 teach_agent 模块说明

## 改动文件

| 文件 | 说明 |
|------|------|
| `backend/db/models.py` | 新增 `SplitRecord` ORM 模型 |
| `backend/db/migrate.py` | 新增 `split_records` 表迁移脚本 |
| `backend/db/crud.py` | 新增 `save_split_record`、`get_recent_split_records`、`get_split_record_by_id`、`_cleanup_old_split_records`；常量 `MAX_SPLIT_RECORDS = 20` |
| `backend/web_app.py` | 新增 `/api/split-records` 和 `/api/split-records/<id>` 端点；`split_questions` 中自动保存记录；提取 `_read_split_subject()` 和 `_serialize_split_record()` |
| `CLAUDE.md` | 补充 Flask 路由文档与 teach_agent 模块说明 |

## 安全审查

已完成安全审查，未发现新增安全漏洞：
- SQL 注入：所有查询通过 SQLAlchemy ORM 参数化
- `limit` 参数限制范围 1~100，`record_id` 由 Flask `<int:>` 路由转换器验证
- `_read_split_subject()` 路径由固定配置拼接，无用户输入参与

## Test plan

- [ ] 手动验证：执行分割操作后，调用 `GET /api/split-records` 确认记录已保存
- [ ] 手动验证：调用 `GET /api/split-records/<id>` 确认返回完整题目数据
- [ ] 手动验证：连续分割超过 20 次后，确认旧记录被自动清理
- [ ] 验证不存在的 record_id 返回 404
