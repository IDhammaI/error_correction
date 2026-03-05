import os
import json
import base64
import requests
import time
import glob
from concurrent.futures import ThreadPoolExecutor, as_completed
import difflib
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 全局配置参数
# ==========================================

API_URL = os.getenv("PADDLEOCR_API_URL")
TOKEN = os.getenv("PADDLEOCR_API_TOKEN")

# 文件夹与文件配置
GT_JSON_FILE = "OmniDocBench.json"                  # 官方下载的标注文件
RAW_DIR = "sample_image/jiaocai"          # 存放样例原图的目录
OUTPUT_LOG_FILE = "jiaocai_accuracy_results.json"       # 样例原图识别结果

# 并发线程数 (不建议过高，避免触发 API 限流)
MAX_WORKERS = 5

# ==========================================
# 模块一：解析 OmniDocBench 官方真值 (Ground Truth)
# ==========================================
def load_omnidocbench_gt(json_path):
    print(f"正在加载官方标准答案库: {json_path}...")
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"找不到文件 {json_path}，请确保已下载并放置在同级目录。")
        
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    gt_dict = {}
    for page in data:
        img_name = os.path.basename(page['page_info']['image_path'])
        
        page_texts = []
        for det in page.get('layout_dets', []):
            if det.get('ignore', False): 
                continue 
                
            if 'text' in det and det['text'].strip():
                page_texts.append(det['text'].strip())
            elif 'latex' in det and det['latex'].strip():
                page_texts.append(det['latex'].strip())
                
        gt_dict[img_name] = "\n".join(page_texts)
        
    print(f"成功加载 {len(gt_dict)} 张图片的标准答案！\n")
    return gt_dict

def calculate_accuracy(gt_text, pred_text):
    gt_clean = gt_text.strip().lower()
    pred_clean = pred_text.strip().lower()
    
    if not gt_clean and not pred_clean: return 100.0
    if not gt_clean or not pred_clean: return 0.0
    
    matcher = difflib.SequenceMatcher(None, gt_clean, pred_clean)
    return round(matcher.ratio() * 100, 2)

# ==========================================
# 模块二：云端 API 调用
# ==========================================
def call_api(file_path):
    with open(file_path, "rb") as f:
        file_data = base64.b64encode(f.read()).decode("ascii")
        
    payload = {
        "file": file_data, 
        "fileType": 1, 
        "useDocOrientationClassify": False, 
        "useDocUnwarping": False
    }
    headers = {"Authorization": f"token {TOKEN}", "Content-Type": "application/json"}
    
    for i in range(3): 
        try:
            start = time.perf_counter()
            response = requests.post(API_URL, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            latency = time.perf_counter() - start
            return latency, response.json()
        except Exception as e:
            time.sleep(2 ** i)
    return None, {"error": "API 请求失败"}

# ==========================================
# 模块三：多线程任务单元
# ==========================================
def process_single_task(img_path, gt_dict):
    filename = os.path.basename(img_path)
    file_size_kb = round(os.path.getsize(img_path) / 1024, 2)
    
    # Raw 文件名就是标准答案的 Key
    if filename not in gt_dict:
        return filename, {"error": f"未在官方 JSON 中找到对应的标准答案: {filename}"}
        
    gt_text = gt_dict[filename]
    strategy = "raw"
    
    latency, res = call_api(img_path)
    if not latency:
        return filename, {"error": "API 调用失败"}
        
    try:
        data = res.get('result', {})
        layout = data.get('layoutParsingResults', [{}])[0]
        pred_text = layout.get('markdown', {}).get('text', '')
        blocks_count = len(layout.get('prunedResult', {}).get('parsing_res_list', []))
    except Exception:
        pred_text = ""
        blocks_count = 0
        
    accuracy = calculate_accuracy(gt_text, pred_text)
    
    return filename, {
        "original_img": filename,
        "strategy": strategy,
        "latency_s": round(latency, 2),
        "size_kb": file_size_kb,
        "text_len": len(pred_text),
        "true_accuracy_pct": accuracy,
        "blocks": blocks_count
    }

# ==========================================
# 模块四：主控引擎 (多线程并发)
# ==========================================
def run_raw_evaluation():
    try:
        gt_dict = load_omnidocbench_gt(GT_JSON_FILE)
    except Exception as e:
        print(e)
        return

    final_results = {}
    if os.path.exists(OUTPUT_LOG_FILE):
        with open(OUTPUT_LOG_FILE, "r", encoding="utf-8") as f:
            try:
                final_results = json.load(f)
                print(f"发现已有成绩单，已加载 {len(final_results)} 条记录。")
            except:
                pass

    if not os.path.exists(RAW_DIR):
        print(f"错误: 找不到文件夹 {RAW_DIR}，请检查路径。")
        return
        
    files = glob.glob(os.path.join(RAW_DIR, "*.*"))
    image_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            
    # 剔除已完成
    pending_files = [f for f in image_files if os.path.basename(f) not in final_results]
    
    if not pending_files:
        print("所有 RAW 图片均已测试完毕！")
        return
    
    total_files = len(pending_files)
    print(f"开始测试 RAW 图片，共 {total_files} 个样本...")
    
    completed = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_img = {executor.submit(process_single_task, img_path, gt_dict): img_path for img_path in pending_files}
        
        for future in as_completed(future_to_img):
            filename, metrics = future.result()
            final_results[filename] = metrics 
            
            completed += 1
            acc = metrics.get('true_accuracy_pct', 'N/A')
            lat = metrics.get('latency_s', 'N/A')
            print(f"[{completed}/{total_files}] RAW 处理完成: {filename[:30]}... | 准确率: {acc}% | 耗时: {lat}s")
            
            with open(OUTPUT_LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(final_results, f, ensure_ascii=False, indent=4)

    total_time = round(time.time() - start_time, 2)
    print(f"\nRAW 图片测试全部完成！总耗时: {total_time} 秒")

if __name__ == "__main__":
    run_raw_evaluation()