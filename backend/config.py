import os

# backend 目录和项目根目录
BACKEND_ROOT = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_ROOT, ".."))

# 统一运行产物根目录：
# - 默认：backend/runtime_data
# - 可通过环境变量 APP_RUNTIME_DIR 覆盖
DEFAULT_RUNTIME_ROOT = os.path.join(BACKEND_ROOT, "runtime_data")
RUNTIME_ROOT = os.environ.get("APP_RUNTIME_DIR", DEFAULT_RUNTIME_ROOT)

# 各类子目录（都挂在统一的 RUNTIME_ROOT 下）
UPLOAD_DIR = os.path.join(RUNTIME_ROOT, "uploads")
PAGES_DIR = os.path.join(RUNTIME_ROOT, "pages")
STRUCT_DIR = os.path.join(RUNTIME_ROOT, "struct")
RESULTS_DIR = os.path.join(RUNTIME_ROOT, "results")

# 上传 & 请求限制
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "bmp", "tiff", "webp"}
MAX_FILE_SIZE_MB = 50

# 确保必要目录存在
for _d in [UPLOAD_DIR, PAGES_DIR, STRUCT_DIR, RESULTS_DIR]:
    os.makedirs(_d, exist_ok=True)