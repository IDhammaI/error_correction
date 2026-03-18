# TODO

## 用户级 API Key 存储

每个用户独立配置自己的 LLM API Key（AES-256 加密存 DB），替代系统全局 .env 配置。

- [ ] DB：用户表新增加密 api_key 字段（per provider）
- [ ] 后端：加解密工具函数（AES-256，密钥从 .env 读取）
- [ ] 后端：设置接口（POST 保存 / DELETE 删除 / GET 状态查询，不返回明文）
- [ ] 后端：调用 LLM 时优先使用用户 key，fallback 到系统全局 key
- [ ] 前端：设置页 API Key 管理 UI（输入、保存、删除、状态显示）
- [ ] .env.example：新增 API_KEY_ENCRYPTION_SECRET 配置项
