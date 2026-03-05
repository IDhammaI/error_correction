# Data Processing

OCR 图像预处理与识别准确率评估系统。

## 目录结构

```
data-processing/
├── preprocessing/              # 图像预处理模块
│   ├── data_preprocessing.py   # 预处理核心
│   ├── preprocessing_mode.json # 预处理几种方案
│   └── README.md
│   
│
├── processing/                    # 基于OmniDocBench的识别评估模块
│   ├── evaluation_recognition.py  # 记录识别结果
│   ├── exam_accuracy_results.json      # 试卷样例识别结果
│   ├── jiaocai_accuracy_results.json   #教程样例识别结果
│   ├── OmniDocBench.json         # OmniDocBench数据集答案
│   └── sample_image              # 优秀样例图片
│       ├──exam/                  # 试卷
│       └──jiaocai                # 教材
│
├── standard_doc/                 # 图像扫描规范文档、数据标注规范
│   ├── DATA_LABELING_STANDARDS.md # 数据标注
│   └── SCANNING_STANDARDS.md      # 扫描规范
└── README.md
```

## 快速开始

### 1. 原始图片识别评估

```bash
cd processing
python evaluation_recognition.py
```

评估原始图片的 OCR 识别准确率，与 OmniDocBench 标注对比，生成 `exam_accuracy_results.json`。

### 2. 图像预处理

```python
from preprocessing.data_preprocessing import run_pipeline

# 单张图片
run_pipeline(file_path="test.png", mode="auto", save_log=True)

# 批量处理
import glob
for img in glob.glob("sample_image/exam/*.png"):
    run_pipeline(file_path=img, mode="auto", save_log=True)
```

**预处理模式**：

| 模式 | 适用场景 |
|------|---------|
| `auto` | 自动选择最佳策略（推荐） |
| `standard` | 一般文档 |
| `lightweight` | 高质量文档、数学公式密集 |
| `illumination_rescue` | 光照不均、阴影、反光 |
| `screen_photography` | 屏幕翻拍、摩尔纹 |
| `aggressive_compression` | 文件压缩 |


```

## 实验结果

基于 OmniDocBench 数据集：

- **原始平均准确率**: 83.97%
- **预处理后平均准确率**: 85.50%
- **平均提升**: 1.5-2%
- **中文试卷**: illumination_rescue 模式提升 2-7%
- **英文数学试卷**: lightweight 模式保持原有准确率

## 配置

### 环境变量

创建 `.env` 文件：

```env
PADDLEOCR_API_URL=https://your-api-endpoint
PADDLEOCR_API_TOKEN=your-token-here
```

### 自定义预处理参数

编辑 `preprocessing/preprocessing_mode.json` 添加自定义模式。

## 注意事项

1. **API 限流**: 建议 `MAX_WORKERS` 不超过 5
2. **文件命名**: 图片文件名需与 `OmniDocBench.json` 中的 `image_path` 匹配
3. **预处理策略**: 数学公式密集文档避免使用 `illumination_rescue`

## 相关文档

- [预处理模块详细说明](preprocessing/README.md)
- [数据标注规范](standard_doc/DATA_LABELING_STANDARDS.md)
- [扫描规范](standard_doc/SCANNING_STANDARDS.md)
