# 图像预处理模块

智能图像预处理系统，用于优化 OCR 识别效果。

## 核心文件

- `data_preprocessing.py` - 主预处理程序
- `preprocessing_mode.json` - 预处理策略配置


## 快速开始

### 1. 单张图片预处理

```python
from data_preprocessing import run_pipeline

# 自动模式（推荐）
run_pipeline(
    file_path="your_image.png",
    mode="auto",  # 自动选择最佳策略
    save_log=True
)

# 手动指定模式
run_pipeline(
    file_path="your_image.png",
    mode="lightweight",  # 可选: standard, lightweight, illumination_rescue, screen_photography, aggressive_compression
    save_log=True
)
```

### 2. 批量处理

```python
import glob
from data_preprocessing import run_pipeline

image_files = glob.glob("your_folder/*.png")
for img_path in image_files:
    run_pipeline(file_path=img_path, mode="auto", save_log=True)
```



## 预处理模式说明

| 模式 | 适用场景 | 特点 |
|------|---------|------|
| `auto` | 所有场景（推荐） | 自动诊断并选择最佳策略 |
| `standard` | 一般文档 | 平衡速度与精度 |
| `lightweight` | 高质量文档、数学公式密集 | 仅做基础优化，保护细节 |
| `illumination_rescue` | 光照不均、阴影、反光 | 对比度增强，光照修复 |
| `screen_photography` | 屏幕翻拍、摩尔纹 | 去除摩尔纹 |
| `aggressive_compression` | 网络差、文件大 | 极限压缩 |

## Auto 模式智能路由

系统会自动分析图像特征并选择最佳策略：

- **数学公式密集 / 高质量文档** → `lightweight`
- **光照问题明显** → `illumination_rescue`
- **屏幕翻拍特征** → `screen_photography`
- **大文件低文本密度** → `aggressive_compression`
- **其他** → `standard`

## 输出结构

```
output/
├── image_name_processed_strategy/
│   └── api_analysis.log          # API 识别结果
processed_exam_images/
└── image_name.png                 # 预处理后的图片
```

## 配置自定义

编辑 `preprocessing_mode.json` 可自定义预处理参数：

```json
{
  "modes": {
    "your_custom_mode": {
      "description": "自定义模式说明",
      "target_dpi": 150,
      "max_side_len": 1920,
      "jpeg_quality": 95,
      "enable_deskew": true,
      "enable_contrast_enhance": false,
      "enable_moire_removal": false
    }
  }
}
```

## 性能优化建议

1. **中文试卷**：auto 模式会自动选择 `illumination_rescue`，提升 2-7%
2. **英文数学试卷**：auto 模式会自动选择 `lightweight`，避免符号识别下降
3. **批量处理**：建议使用 auto 模式，系统会为每张图片选择最优策略
