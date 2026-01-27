# Web应用使用指南

## 📱 功能简介

Web应用提供了一个可视化界面，用于测试错题本生成系统的完整工作流程。

### 主要功能

1. ✅ **文件上传** - 支持拖拽或点击上传PDF/图片
2. ✅ **自动OCR解析** - 调用PaddleOCR API进行文档结构化解析
3. ✅ **AI题目分割** - 使用DeepSeek Agent智能分割题目
4. ✅ **题目预览** - 可视化展示分割后的题目
5. ✅ **选择导出** - 勾选需要的题目并导出为Markdown格式

---

## 🚀 快速启动

### 1. 确保环境配置完成

检查 `.env` 文件是否包含必要的配置：

```bash
# 必需配置
PADDLEOCR_API_URL=https://...
PADDLEOCR_API_TOKEN=your_token
DEEPSEEK_API_KEY=your_key

# 可选配置
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_key
```

### 2. 启动Web服务

```bash
python web_app.py
```

### 3. 访问界面

打开浏览器访问：**http://localhost:5001**

---

## 📋 使用流程

### 步骤1: 上传文件

- **方式1**: 点击上传区域选择文件
- **方式2**: 拖拽文件到上传区域

**支持格式**:
- PDF: `.pdf`
- 图片: `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff`, `.webp`

**文件大小**: 最大 50MB

### 步骤2: OCR解析

文件上传后，系统会自动：
1. 将PDF转换为图片（如果是PDF）
2. 调用PaddleOCR API进行文档结构化解析
3. 保存OCR结果到 `output/struct/` 目录

**进度显示**:
- 图片数量
- OCR解析完成状态

### 步骤3: 分割题目

点击 **"🤖 开始分割题目"** 按钮：

1. 系统调用DeepSeek Agent
2. Agent分析OCR结果
3. 智能识别题号、题型、选项
4. 保存分割结果到 `results/questions.json`

**预计时间**: 10-30秒/页（取决于API响应速度）

### 步骤4: 预览和导出

分割完成后：

1. **预览题目**: 查看所有识别的题目
2. **选择题目**: 勾选需要导出的题目
3. **导出错题本**: 点击 **"📥 导出错题本"** 按钮
4. **下载文件**: 点击下载链接获取Markdown文件

---

## 🔧 API端点说明

### 1. 系统状态检查

```http
GET /api/status
```

**响应**:
```json
{
  "success": true,
  "status": {
    "paddleocr_configured": true,
    "deepseek_configured": true,
    "langsmith_enabled": false,
    "output_dirs": {
      "pages": "output/pages",
      "struct": "output/struct",
      "results": "results"
    }
  }
}
```

### 2. 文件上传和OCR解析

```http
POST /api/upload
Content-Type: multipart/form-data

file: <文件>
```

**响应**:
```json
{
  "success": true,
  "message": "文件处理成功",
  "result": {
    "image_count": 3,
    "ocr_count": 3,
    "image_paths": ["output/pages/test_page_001.png", ...]
  }
}
```

### 3. Agent分割题目

```http
POST /api/split
```

**响应**:
```json
{
  "success": true,
  "message": "成功分割 5 道题目",
  "questions": [
    {
      "question_id": "1",
      "question_type": "选择题",
      "content_blocks": [...],
      "options": ["A. ...", "B. ..."],
      ...
    }
  ]
}
```

### 4. 导出错题本

```http
POST /api/export
Content-Type: application/json

{
  "selected_ids": ["1", "2", "3"]
}
```

**响应**:
```json
{
  "success": true,
  "message": "错题本导出成功",
  "output_path": "results/wrongbook.md"
}
```

### 5. 获取题目列表

```http
GET /api/questions
```

**响应**:
```json
{
  "success": true,
  "questions": [...]
}
```

### 6. 下载文件

```http
GET /download/wrongbook.md
```

直接下载Markdown文件

---

## 🎨 界面功能说明

### 系统状态指示器

顶部显示系统配置状态：
- ✓ **PaddleOCR**: API已配置
- ✓ **DeepSeek**: API已配置
- ✓ **LangSmith追踪**: 调试追踪已启用

### 步骤指示器

4步流程可视化：
1. **上传文件** - 上传PDF或图片
2. **OCR解析** - 文档结构化识别
3. **分割题目** - AI智能分割
4. **预览导出** - 选择和导出

### 题目卡片

每道题目显示：
- 题号（如"题目 1"）
- 题型标签（选择题/填空题/解答题）
- 题目内容（文本、公式、图片引用）
- 选项（如果是选择题）
- 复选框（用于选择导出）

---

## ⚙️ 配置说明

### 端口配置

默认端口: **5001**

修改端口（在 `web_app.py` 最后一行）:
```python
app.run(host='0.0.0.0', port=8080, debug=True)
```

### 文件大小限制

默认: **50MB**

修改限制（在 `web_app.py` 配置部分）:
```python
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
```

### 上传目录

默认: `uploads/`

修改目录（在 `web_app.py` 配置部分）:
```python
UPLOAD_FOLDER = 'my_uploads'
```

---

## 🐛 常见问题

### Q1: 上传文件后长时间没有响应？

**原因**: PaddleOCR API响应较慢或网络问题

**解决**:
1. 检查网络连接
2. 查看浏览器控制台的网络请求
3. 检查 `.env` 中的API配置是否正确

### Q2: Agent分割失败？

**原因**: DeepSeek API配置错误或OCR结果为空

**解决**:
1. 检查 `DEEPSEEK_API_KEY` 是否正确
2. 查看 `output/struct/` 目录下是否有OCR结果
3. 检查 `results/split_issues.jsonl` 查看Agent记录的问题

### Q3: 题目预览显示为空？

**原因**: Agent未能正确识别题目或保存失败

**解决**:
1. 检查 `results/questions.json` 是否存在
2. 手动查看JSON文件内容
3. 启用LangSmith追踪查看Agent执行日志

### Q4: 导出的Markdown文件在哪里？

**位置**: `results/wrongbook.md`

**下载**: 点击页面上的下载链接，或直接访问 `/download/wrongbook.md`

---

## 🔍 调试技巧

### 1. 查看系统日志

启动Web应用后，终端会显示所有请求日志：
```
127.0.0.1 - - [27/Jan/2026 10:30:15] "POST /api/upload HTTP/1.1" 200 -
127.0.0.1 - - [27/Jan/2026 10:30:45] "POST /api/split HTTP/1.1" 200 -
```

### 2. 检查中间结果

**标准化图片**:
```bash
ls output/pages/
# test_page_001.png, test_page_002.png, ...
```

**OCR结果**:
```bash
ls output/struct/
# test_page_001_struct.json, ...
```

**题目JSON**:
```bash
cat results/questions.json
```

**问题日志**:
```bash
cat results/split_issues.jsonl
```

### 3. 启用LangSmith追踪

在 `.env` 中设置：
```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_key
LANGSMITH_PROJECT=error-correction-web
```

然后访问 https://smith.langchain.com 查看Agent执行轨迹。

### 4. 浏览器开发者工具

按 `F12` 打开开发者工具：
- **Console**: 查看JavaScript错误
- **Network**: 查看API请求和响应
- **Application**: 查看本地存储

---

## 📊 性能优化

### 1. 减少处理时间

**方法1**: 降低图片DPI
```python
# 在 src/utils.py 的 prepare_input 函数中
images = convert_from_path(file_path, dpi=200)  # 默认300
```

**方法2**: 关闭部分OCR功能
```bash
# .env
PADDLEOCR_USE_DOC_ORIENTATION=false
PADDLEOCR_USE_DOC_UNWARPING=false
PADDLEOCR_USE_CHART_RECOGNITION=false
```

### 2. 提高并发处理能力

使用 gunicorn 代替 Flask 开发服务器：
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 web_app:app
```

### 3. 添加缓存

对于相同文件，可以缓存OCR结果避免重复调用API。

---

## 🔒 安全注意事项

### 1. 文件上传安全

- ✅ 已限制文件扩展名
- ✅ 已使用 `secure_filename` 处理文件名
- ✅ 已限制文件大小（50MB）

### 2. API密钥保护

- ⚠️ 不要将 `.env` 文件提交到版本控制
- ⚠️ 生产环境使用更安全的密钥管理方案

### 3. 部署建议

如果部署到公网：
- 添加用户认证
- 使用HTTPS
- 限制请求频率
- 定期清理临时文件

---

## 🎯 扩展功能建议

### 1. 批量处理

支持一次上传多个文件并批量处理

### 2. 历史记录

保存处理历史，支持查看和重新导出

### 3. 自定义模板

允许用户自定义错题本的Markdown模板

### 4. 在线编辑

在导出前支持在线编辑题目内容

---

## 📞 技术支持

如遇到问题：

1. 查看本文档的"常见问题"部分
2. 检查 `docs/PROJECT_STRUCTURE.md` 了解系统架构
3. 查看终端日志和浏览器控制台
4. 启用LangSmith追踪进行调试

---

**文档版本**: v1.0.0
**最后更新**: 2026-01-27
