import base64
import os
import requests
import time
import json
import math
import cv2
import numpy as np
from typing import Dict, Any
from dotenv import load_dotenv
from PIL import Image

# ==========================================
# 全局配置参数
# ==========================================
load_dotenv()  # 从 .env 文件加载环境变量
API_URL = os.getenv("PADDLEOCR_API_URL")  
TOKEN = os.getenv("PADDLEOCR_API_TOKEN")  

OUTPUT_DIR = "output"                 # API 识别结果、标记图片和日志保存目录
PROCESSED_DIR = "processed_exam_images"    # 预处理后的中间图片保存目录
CONFIG_FILE = "preprocessing_mode.json" # 预处理配置文件路径

# ==========================================
# 模块一：配置加载
# ==========================================
def load_preprocessing_config(mode_name=None):
    """加载预处理策略配置"""
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"配置文件 {CONFIG_FILE} 不存在！请先创建。")
        
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
        
    if mode_name is None:
        mode_name = config_data.get("default_mode", "standard")
        
    if mode_name not in config_data["modes"]:
        raise ValueError(f"未找到预处理模式 '{mode_name}'，请检查配置文件。")
        
    print(f"[Config] 已加载预处理模式: '{mode_name}'")
    print(f"[Config] 策略描述: {config_data['modes'][mode_name].get('description', '')}")
    return config_data["modes"][mode_name]

# ==========================================
# 模块1.5：图像特征分析 (自适应诊断)
# ==========================================
def get_file_size_kb(path: str) -> float:
    return round(os.path.getsize(path) / 1024.0, 2)

def get_dpi(path: str, default: int = 72) -> int:
    try:
        with Image.open(path) as im:
            dpi = im.info.get('dpi')
            if dpi and isinstance(dpi, tuple):
                return int(dpi[0])
    except Exception:
        pass
    return default

def to_gray(img: np.ndarray) -> np.ndarray:
    if len(img.shape) == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img

def estimate_brightness_and_contrast(gray: np.ndarray) -> Dict[str, float]:
    arr = gray.astype(np.float32)
    mean = float(np.mean(arr))
    std = float(np.std(arr))
    return {"brightness": round(mean, 2), "contrast": round(std, 2)}

def estimate_sharpness(gray: np.ndarray) -> float:
    # Variance of Laplacian (常用的清晰度测量)
    var_lap = cv2.Laplacian(gray, cv2.CV_64F).var()
    return float(var_lap)

def estimate_noise(img: np.ndarray) -> float:
    # 通过原图与高斯模糊图之差估计高频噪声
    blur = cv2.GaussianBlur(img, (3, 3), 0)
    if img.ndim == 3:
        diff = cv2.cvtColor(cv2.absdiff(img, blur), cv2.COLOR_BGR2GRAY)
    else:
        diff = cv2.absdiff(img, blur)
    return float(np.std(diff))

def estimate_edge_density(gray: np.ndarray) -> float:
    edges = cv2.Canny(gray, 100, 200)
    edge_ratio = float(np.count_nonzero(edges)) / (gray.shape[0] * gray.shape[1])
    return round(edge_ratio, 4)

def estimate_text_density(gray: np.ndarray) -> float:
    # 自适应二值化后计算黑色像素比例，作为文本/线条密度的近似
    th = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY_INV, 25, 15)
    density = float(np.count_nonzero(th)) / (gray.shape[0] * gray.shape[1])
    return round(density, 4)

def detect_color_mode(img: np.ndarray) -> str:
    if len(img.shape) == 2:
        return "grayscale"
    # 如果三通道间差异很小，认为是灰度图
    channel_diff = np.max(img.astype(np.int32) - img[..., 0:1].astype(np.int32))
    if channel_diff < 5:
        return "grayscale"
    return "color"

def estimate_skew_angle(gray: np.ndarray) -> float:
    # 使用 Hough 直线检测（在边缘图上）来估计主方向角度
    h, w = gray.shape[:2]
    # Resize reduce cost
    scale = 600.0 / max(h, w) if max(h, w) > 600 else 1.0
    small = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    edges = cv2.Canny(small, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=50, minLineLength=30, maxLineGap=10)
    angles = []
    if lines is None:
        return 0.0
    for l in lines:
        x1, y1, x2, y2 = l[0]
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        # 只考虑接近水平的直线，过滤垂直线
        if abs(angle) < 45:
            angles.append(angle)
    if not angles:
        return 0.0
    # 取中位数以减少离群点影响
    med = float(np.median(np.array(angles)))
    # 返回图片坐标系下的倾斜角（度），正值表示逆时针旋转
    return round(med / scale if scale != 1.0 else med, 2)

def analyze_image(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    pil_img = Image.open(path)
    w, h = pil_img.size
    file_size_kb = get_file_size_kb(path)
    dpi = get_dpi(path)

    # Load as OpenCV image
    img_cv = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if img_cv is None:
        # fallback via PIL
        img_cv = cv2.cvtColor(np.array(pil_img.convert('RGB')), cv2.COLOR_RGB2BGR)

    gray = to_gray(img_cv)

    bc = estimate_brightness_and_contrast(gray)
    sharpness = estimate_sharpness(gray)
    noise = estimate_noise(img_cv)
    edge_density = estimate_edge_density(gray)
    text_density = estimate_text_density(gray)
    color_mode = detect_color_mode(img_cv)
    skew = estimate_skew_angle(gray)

    aspect_ratio = round(w / h, 4) if h != 0 else None

    return {
        "file": os.path.basename(path),
        "path": path,
        "file_size_kb": file_size_kb,
        "dpi": dpi,
        "resolution": f"{w}x{h}",
        "aspect_ratio": aspect_ratio,
        "color_mode": color_mode,
        "brightness": bc["brightness"],
        "contrast": bc["contrast"],
        "sharpness_variance_laplacian": round(sharpness, 2),
        "noise_stddev": round(noise, 2),
        "edge_density": edge_density,
        "text_density": text_density,
        "skew_angle_degrees": skew,
        "is_blurry": sharpness < 100.0
    }

# ==========================================
# 模块二：图像 DPI 读取与真实重采样
# ==========================================
def get_image_dpi(file_path):
    """读取图像文件的 DPI 元数据标签"""
    try:
        with Image.open(file_path) as img:
            dpi = img.info.get('dpi')
            if dpi:
                return f"{int(dpi[0])} x {int(dpi[1])}"
            else:
                return "Not Set (System Default)"
    except Exception as e:
        return f"Read Failed: {e}"

def resample_image_by_dpi(image_path, target_dpi=150, default_original_dpi=72):
    """真正的 DPI 转换器：不仅修改标签，还会物理缩放像素矩阵。"""
    with Image.open(image_path) as img:
        orig_dpi_tuple = img.info.get('dpi')
        original_dpi = orig_dpi_tuple[0] if orig_dpi_tuple else default_original_dpi
            
        scale_factor = target_dpi / original_dpi
        
        if scale_factor == 1.0:
            return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            
        new_width = int(img.width * scale_factor)
        new_height = int(img.height * scale_factor)
        
        print(f"[Preprocess] DPI Resampling: {original_dpi} -> {target_dpi} DPI")
        
        # 执行高质量重采样 (Lanczos)
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return cv2.cvtColor(np.array(resized_img), cv2.COLOR_RGB2BGR)

# ==========================================
# 模块三：核心 CV 预处理算法
# ==========================================
def resize_image_for_paddle(image, max_side_len=1920):
    """限制图像的最大边长"""
    h, w = image.shape[:2]
    if max(h, w) > max_side_len:
        if h > w:
            new_h = max_side_len
            new_w = int(w * (max_side_len / h))
        else:
            new_w = max_side_len
            new_h = int(h * (max_side_len / w))
        image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        print(f"[Preprocess] Size Truncation: ({w}x{h}) -> ({new_w}x{new_h})")
    return image

def deskew_image(image):
    """倾斜校正"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=10)
    
    if lines is not None:
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            if -45 < angle < 45:
                angles.append(angle)
                
        if angles:
            median_angle = np.median(angles)
            if abs(median_angle) > 0.5: 
                h, w = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
                print(f"[Preprocess] Deskew applied: {median_angle:.2f} degrees")
                return rotated
    return image

def enhance_contrast_clahe(image, clip_limit=2.0, tile_size=8):
    """CLAHE 增强图像局部对比度"""
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_size, tile_size))
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    final = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    print(f"[Preprocess] Contrast enhanced (CLAHE: clip={clip_limit}, tile={tile_size})")
    return final

def remove_moire_pattern(image):
    """高斯滤波弱化摩尔纹"""
    blurred = cv2.GaussianBlur(image, (3, 3), 0)
    print("[Preprocess] Moire pattern removed (Gaussian Blur)")
    return blurred

# ==========================================
# 模块四：基于配置的预处理调度器
# ==========================================
def preprocess_image(input_path, config):
    """根据传入的配置字典执行预处理流水线"""
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    base_name = os.path.basename(input_path)
    file_name_without_ext = os.path.splitext(base_name)[0]
    file_ext = os.path.splitext(base_name)[1]

    # 保存为原始文件名（保持原扩展名或使用 jpg）
    if file_ext.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
        output_path = os.path.join(PROCESSED_DIR, base_name)
    else:
        output_path = os.path.join(PROCESSED_DIR, f"{file_name_without_ext}.jpg")
    
    print(f"\n[Step 1/3] Local Preprocessing: {input_path}")
    
    try:
        image = resample_image_by_dpi(input_path, target_dpi=config.get('target_dpi', 150))
    except Exception as e:
        raise ValueError(f"Image read/resample failed: {e}")

    # 根据配置执行流水线
    image = resize_image_for_paddle(image, max_side_len=config.get('max_side_len', 1920))
    
    if config.get('enable_deskew', False):
        image = deskew_image(image)
        
    if config.get('enable_moire_removal', False):
        image = remove_moire_pattern(image)
        
    if config.get('enable_contrast_enhance', False):
        clip_limit = config.get('clahe_clip_limit', 2.0)
        tile_size = config.get('clahe_tile_size', 8)
        image = enhance_contrast_clahe(image, clip_limit=clip_limit, tile_size=tile_size)

    # 统一转换色彩空间并使用 PIL 保存，应用 jpeg_quality 压缩参数
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(image_rgb)
    
    target_dpi = config.get('target_dpi', 150)
    jpeg_quality = config.get('jpeg_quality', 95)
    
    pil_img.save(output_path, format="JPEG", quality=jpeg_quality, dpi=(target_dpi, target_dpi))
    
    file_size_kb = os.path.getsize(output_path) / 1024
    print(f"[Preprocess] Completed! Saved to: {output_path} (Size: {file_size_kb:.2f} KB, Quality: {jpeg_quality})")
    return output_path

# ==========================================
# 模块五：云端 API 调用与结果解析
# ==========================================
def get_file_type(file_path):
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == ".pdf": return 0
    elif ext in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]: return 1
    else: raise ValueError(f"Unsupported file format: {ext}")

def call_paddleocr_api(file_path):
    print(f"\n[Step 2/3] Calling Cloud API...")
    file_type = get_file_type(file_path)
    with open(file_path, "rb") as file:
        file_bytes = file.read()
        file_data = base64.b64encode(file_bytes).decode("ascii")

    headers = {"Authorization": f"token {TOKEN}", "Content-Type": "application/json"}
    payload = {
        "file": file_data,
        "fileType": file_type, 
        "useDocOrientationClassify": False,
        "useDocUnwarping": False,
        "useChartRecognition": False,
    }

    start_time = time.perf_counter()
    response = requests.post(API_URL, json=payload, headers=headers)
    response.raise_for_status()
    api_latency = time.perf_counter() - start_time
    
    return response.json(), api_latency, response.json()

def analyze_and_save(original_file_path, api_target_file, light_data, api_latency, raw_data, suffix="", save_log=False):
    print(f"\n[Step 3/3] Parsing response...")
    base_name = os.path.splitext(os.path.basename(original_file_path))[0]
    test_output_dir = os.path.join(OUTPUT_DIR, f"{base_name}_{suffix}" if suffix else base_name)
    os.makedirs(test_output_dir, exist_ok=True)

    if save_log:
        log_file_path = os.path.join(test_output_dir, "api_analysis.log")
        with open(log_file_path, "w", encoding="utf-8") as log_file:
            json.dump(light_data, log_file, ensure_ascii=False, indent=2)
        print(f"[Preprocess] API info logged to {log_file_path}")

    try:
        res = light_data.get('result', {})
        layout_results = res.get('layoutParsingResults', [{}])[0]
        width, height = res.get('dataInfo', {}).get('width', 0), res.get('dataInfo', {}).get('height', 0)
        num_blocks = len(layout_results.get('prunedResult', {}).get('parsing_res_list', []))
        
        text_content = layout_results.get('markdown', {}).get('text', '')
        text_length = len(text_content)
        actual_dpi = get_image_dpi(api_target_file) if get_file_type(api_target_file) == 1 else "PDF"

        print("-" * 50)
        print(f"[{suffix.upper()}] API Data Metrics")
        print("-" * 50)
        print(f"Latency     : {api_latency:.2f} s")
        print(f"DPI Tag     : {actual_dpi}")
        print(f"Resolution  : {width} x {height}")
        print(f"Blocks      : {num_blocks}")
        print(f"Text Length : {text_length} chars")
        print("-" * 50)
    except Exception:
        pass 

# ==========================================
# 最终运行入口
# ==========================================
def run_pipeline(file_path, mode="auto", save_log=False):
    """
    端到端总控调度
    :param file_path: 目标文件路径
    :param mode: "auto" 会触发自动图像诊断路由，也可直接指定配置文件里的模式
    """
    print(f"\n{'='*60}")
    print(f"Task Started: {file_path} | Requested Mode: {mode}")
    print(f"{'='*60}")
    
    if not os.path.exists(file_path):
        print(f"[Error] File not found: {file_path}")
        return

    is_image = (get_file_type(file_path) == 1)
    diagnosis_info = None

    # Step 0: 如果是图片，我们先进行物理体检（改动最小的解耦融合方案）
    if is_image:
        print("\n[Step 0/3] Image Auto-Diagnosis...")
        try:
            diagnosis_info = analyze_image(file_path)
            print(f"  -> Features: Brightness={diagnosis_info['brightness']}, Blur={diagnosis_info['is_blurry']}, Skew={diagnosis_info['skew_angle_degrees']}")

            # 核心融合点：如果开启了 Auto 模式，则利用诊断结果决定该用哪套 JSON 预设
            if mode == "auto":
                # 判断是否为数学公式密集文档（高文本密度 + 高边缘密度 + 较高清晰度）
                is_math_heavy = (
                    diagnosis_info['text_density'] > 0.08 and
                    diagnosis_info['edge_density'] > 0.05 and
                    diagnosis_info['sharpness_variance_laplacian'] > 150
                )

                # 判断是否为质量已经较好的文档
                is_good_quality = (
                    diagnosis_info['brightness'] >= 120 and
                    diagnosis_info['brightness'] <= 200 and
                    diagnosis_info['contrast'] >= 50 and
                    not diagnosis_info['is_blurry'] and
                    abs(diagnosis_info['skew_angle_degrees']) < 2.0
                )

                # 智能路由逻辑
                if is_math_heavy or is_good_quality:
                    # 数学公式密集或质量已经很好的文档，使用轻量级模式
                    mode = "lightweight"
                    print(f"  -> [Auto-Routing] Detected high-quality or math-heavy document, using lightweight mode")
                elif diagnosis_info['brightness'] < 100 or diagnosis_info['brightness'] > 220 or diagnosis_info['contrast'] < 40:
                    # 光照问题明显，使用光照拯救模式
                    mode = "illumination_rescue"
                    print(f"  -> [Auto-Routing] Detected illumination issues, using illumination_rescue mode")
                elif diagnosis_info['noise_stddev'] > 3.0 and not diagnosis_info['is_blurry']:
                    # 噪声明显但不模糊，可能是屏幕翻拍
                    mode = "screen_photography"
                    print(f"  -> [Auto-Routing] Detected screen photography patterns, using screen_photography mode")
                elif diagnosis_info['file_size_kb'] > 3000 and diagnosis_info['text_density'] < 0.03:
                    # 文件大但文本少，需要压缩
                    mode = "aggressive_compression"
                    print(f"  -> [Auto-Routing] Large file with low text density, using aggressive_compression mode")
                else:
                    # 默认使用标准模式
                    mode = "standard"
                    print(f"  -> [Auto-Routing] Using standard mode for general document")
        except Exception as e:
            print(f"  -> [Warning] Diagnosis failed: {e}")
            if mode == "auto": mode = "standard"

    if is_image and mode != "raw": 
        # 读取配置并预处理
        config = load_preprocessing_config(mode_name=mode)
        api_target_file = preprocess_image(file_path, config)
        suffix = f"processed_{mode}" 
    else:
        print(f"\n[Step 1/3] Skipping preprocessing, using raw file...")
        api_target_file = file_path
        suffix = "raw"
        
    try:
        light_log, latency, raw_json = call_paddleocr_api(api_target_file)
    except Exception as e:
        print(f"[Error] API call failed: {e}")
        return

    # 把物理特征的诊断记录随同 API 结果一并写入 log 文件，辅助后期深度分析
    if diagnosis_info and isinstance(light_log, dict):
        light_log["image_diagnosis"] = diagnosis_info

    analyze_and_save(file_path, api_target_file, light_log, latency, raw_json, suffix=suffix, save_log=save_log)
    print("\n[Done] Pipeline execution completed successfully.")

if __name__ == "__main__":
    # ==========================================
    # 1. 单张图片测试示例
    # ==========================================
    # test_file = r"test_image/raw_image/raw_test_1_copy.png"
    
    # # 使用自适应模式 "auto"，系统将自己进行体检并匹配预处理
    # run_pipeline(
    #     file_path=test_file, 
    #     mode="standard",  # 可选: auto, standard, aggressive_compression, illumination_rescue, screen_photography, raw
    #     save_log=True # 开启 Log 可以将诊断特征一并写入结果中
    # )
    
    # ==========================================
    # 2. 文件夹批处理测试示例 (若需使用，请取消下方注释)
    # ==========================================
    import glob
    test_dir = r"D:\my_data\code\error_correction\data-processing\processing\sample_image\exam"
    # 获取目录下所有的文件
    image_files = glob.glob(os.path.join(test_dir, "*.*"))
    
    print(f"\n📁 启动文件夹批处理模式: {test_dir} (共找到 {len(image_files)} 个文件)")
    for img_path in image_files:
        # 仅处理常见图像格式
        if img_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp')):
            run_pipeline(
                file_path=img_path, 
                mode="auto",      # 批处理强烈建议用 auto 模式
                save_log=True     # 批处理时建议开启日志以便后续分析
            )