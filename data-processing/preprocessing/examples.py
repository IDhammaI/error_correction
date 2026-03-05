"""
预处理模块使用示例
"""
from data_preprocessing import run_pipeline
import glob
import os

# ==========================================
# 示例 1: 单张图片预处理（自动模式）
# ==========================================
def example_single_image_auto():
    """单张图片自动预处理"""
    test_file = r"test_image/sample.png"

    if os.path.exists(test_file):
        run_pipeline(
            file_path=test_file,
            mode="auto",  # 自动选择最佳策略
            save_log=True
        )


# ==========================================
# 示例 2: 单张图片预处理（指定模式）
# ==========================================
def example_single_image_manual():
    """单张图片手动指定模式"""
    test_file = r"test_image/sample.png"

    if os.path.exists(test_file):
        run_pipeline(
            file_path=test_file,
            mode="lightweight",  # 手动指定轻量级模式
            save_log=True
        )


# ==========================================
# 示例 3: 批量处理文件夹
# ==========================================
def example_batch_processing():
    """批量处理文件夹中的所有图片"""
    test_dir = r"test_image/batch"

    # 获取所有图片文件
    image_files = glob.glob(os.path.join(test_dir, "*.*"))

    print(f"\n启动批处理: {test_dir} (共 {len(image_files)} 个文件)")

    for img_path in image_files:
        # 仅处理常见图像格式
        if img_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp')):
            print(f"\n处理: {os.path.basename(img_path)}")
            run_pipeline(
                file_path=img_path,
                mode="auto",  # 批处理推荐使用 auto 模式
                save_log=True
            )



if __name__ == "__main__":
    # 取消注释以运行相应示例

    # example_single_image_auto()
    # example_single_image_manual()
    # example_batch_processing()

    print("请取消注释相应的示例函数以运行")
