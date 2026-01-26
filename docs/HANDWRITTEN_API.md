# 手写体 vs 印刷体识别 API

## 概述

`printed-vs-handwritten/app.py` 提供了一个 Flask Web API，用于分类图片内容是手写还是印刷体。

## 技术架构

- **框架**: Flask
- **模型**: TypegroupsClassifier (OCR-D typegroups classifier)
- **端口**: 5000
- **模型路径**: `ocrd_typegroups_classifier/models/classifier.tgc`

## API 端点

### 1. 健康检查

```http
GET /
```

**响应示例**:
```json
{
  "status": "ok",
  "message": "Printed vs Handwritten Classification API",
  "endpoints": {
    "/classify": "POST - Classify an image (multipart/form-data with 'image' field)",
    "/classify_base64": "POST - Classify a base64 encoded image (JSON with 'image' field)"
  }
}
```

### 2. 分类图片（文件上传）

```http
POST /classify
Content-Type: multipart/form-data
```

**请求参数**:
- `image`: 图片文件 (multipart/form-data)

**响应示例**:
```json
{
  "success": true,
  "prediction": "printed",
  "confidence": 0.9523,
  "probabilities": {
    "printed": 0.9523,
    "handwritten": 0.0477
  }
}
```

### 3. 分类图片（Base64）

```http
POST /classify_base64
Content-Type: application/json
```

**请求体**:
```json
{
  "image": "base64_encoded_image_string"
}
```

**响应示例**:
```json
{
  "success": true,
  "prediction": "handwritten",
  "confidence": 0.8745,
  "probabilities": {
    "printed": 0.1255,
    "handwritten": 0.8745
  }
}
```

## 分类结果

### 可能的预测值

- `"printed"` - 印刷体
- `"handwritten"` - 手写体

### 置信度

- `confidence`: 预测类别的置信度 (0-1)
- `probabilities`: 所有类别的概率分布

## 使用示例

### Python 调用示例

#### 方式1: 文件上传

```python
import requests

url = "http://localhost:5000/classify"
files = {"image": open("test_image.jpg", "rb")}

response = requests.post(url, files=files)
result = response.json()

print(f"预测结果: {result['prediction']}")
print(f"置信度: {result['confidence']:.2%}")
```

#### 方式2: Base64 编码

```python
import requests
import base64

# 读取并编码图片
with open("test_image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode("ascii")

url = "http://localhost:5000/classify_base64"
payload = {"image": image_data}

response = requests.post(url, json=payload)
result = response.json()

print(f"预测结果: {result['prediction']}")
print(f"置信度: {result['confidence']:.2%}")
```

### 工具函数封装

```python
import requests
import base64
from typing import Dict, Any


def classify_image_file(image_path: str, api_url: str = "http://localhost:5000") -> Dict[str, Any]:
    """
    分类图片文件（文件上传方式）

    Args:
        image_path: 图片文件路径
        api_url: API服务地址

    Returns:
        分类结果字典
    """
    url = f"{api_url}/classify"
    files = {"image": open(image_path, "rb")}

    response = requests.post(url, files=files)
    return response.json()


def classify_image_base64(image_path: str, api_url: str = "http://localhost:5000") -> Dict[str, Any]:
    """
    分类图片文件（Base64方式）

    Args:
        image_path: 图片文件路径
        api_url: API服务地址

    Returns:
        分类结果字典
    """
    # 读取并编码图片
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("ascii")

    url = f"{api_url}/classify_base64"
    payload = {"image": image_data}

    response = requests.post(url, json=payload)
    return response.json()


# 使用示例
if __name__ == "__main__":
    result = classify_image_file("test.jpg")

    if result.get("success"):
        print(f"✓ 预测结果: {result['prediction']}")
        print(f"  置信度: {result['confidence']:.2%}")
        print(f"  概率分布: {result['probabilities']}")
    else:
        print(f"✗ 错误: {result.get('error')}")
```

## 启动服务

```bash
cd printed-vs-handwritten
python app.py
```

服务将在 `http://0.0.0.0:5000` 启动。

## 集成到错题本工作流

### 应用场景

在错题本生成流程中，可以用手写体识别来：

1. **题目分类优化**
   - 识别题目区域是手写还是印刷
   - 为手写题目提供不同的OCR参数或处理策略

2. **答案区域检测**
   - 检测学生是否已经手写作答
   - 区分原始题目和学生答案

3. **质量控制**
   - 过滤掉手写笔记区域
   - 只保留印刷体题目进行结构化处理

### 集成方式

可以作为 Agent 工具集成：

```python
from langchain_core.tools import tool
import requests

@tool
def classify_text_type(image_path: str) -> str:
    """
    判断图片中的文字是手写还是印刷体

    Args:
        image_path: 图片路径

    Returns:
        "printed" 或 "handwritten"
    """
    try:
        url = "http://localhost:5000/classify"
        files = {"image": open(image_path, "rb")}

        response = requests.post(url, files=files)
        result = response.json()

        if result.get("success"):
            return f"{result['prediction']} (置信度: {result['confidence']:.2%})"
        else:
            return f"分类失败: {result.get('error')}"
    except Exception as e:
        return f"调用API出错: {str(e)}"
```

## 模型参数

在代码中使用的模型参数：

```python
result = tgc.classify(
    img,
    stride=75,        # 滑动窗口步长
    batch_size=64,    # 批处理大小
    score_as_key=False
)
```

这些参数可以根据实际需求调整以优化速度和精度。

## 注意事项

1. **图片格式**: 自动转换为 RGB 模式
2. **模型加载**: 首次调用时加载模型（约需几秒）
3. **并发**: Flask 默认单线程，高并发需要使用 gunicorn 等
4. **内存**: 模型会常驻内存（约200-500MB）

## 性能优化建议

1. **生产部署**: 使用 gunicorn 代替 Flask 开发服务器
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

2. **批量处理**: 如果需要处理多张图片，可以扩展 API 支持批量接口

3. **缓存**: 对于相同图片可以缓存结果避免重复计算
