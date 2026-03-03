# 设备
import math
import os

import numpy as np
import torch
from torch import optim
from torch.utils.data import Dataset, DataLoader
from torchvision.transforms import transforms
import torch.nn.functional as F
from tqdm import tqdm

from src.adcj.EnsExam.model import Generator, Discriminator, EnsExamLoss

import os
import torch
import numpy as np
import cv2
from torch.utils.data import Dataset
from torchvision import transforms
import torch.nn.functional as F


def generate_mask_from_pair(Iin, Igt, threshold=20, debug=False):
    """
    单块（512x512）软笔画掩码生成 - 修正版本
    :param Iin: 单块图像 (H,W,3) RGB 0-255
    :param Igt: 单块GT图 (H,W,3) RGB 0-255
    :param threshold: 差异阈值，默认20
    :param debug: 是否返回中间结果用于调试
    :return: Ms_gt(软掩码), Mb_gt(基础掩码), [debug_dict]
    """
    H, W = Iin.shape[:2]

    # ========== 1. 生成粗笔画掩码 ==========
    # 使用int16避免溢出，计算RGB三通道的平均差异
    diff = np.abs(Iin.astype(np.int16) - Igt.astype(np.int16)).mean(axis=-1)
    # print(f"Diff统计: min={diff.min()}, max={diff.max()}, 90%={np.percentile(diff, 90)}")
    coarse_mask = (diff > threshold).astype(np.uint8)

    # ========== 2. 形态学去噪 ==========
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    # 开运算去除散点噪声 + 闭运算连接断裂笔画
    denoised_mask = cv2.morphologyEx(coarse_mask, cv2.MORPH_OPEN, kernel)
    denoised_mask = cv2.morphologyEx(denoised_mask, cv2.MORPH_CLOSE, kernel)

    # ========== 3. 生成 Mb_gt（基础文本块掩码） ==========
    # 对去噪后的掩码适度膨胀，作为文本区域指导
    Mb_gt = cv2.dilate(denoised_mask, kernel, iterations=2).astype(np.float32)

    # ========== 4. 生成软笔画掩码 Ms_gt ==========
    # 4.1 骨架：笔画收缩1像素（论文明确要求）
    skeleton = cv2.erode(denoised_mask, kernel, iterations=1)

    # 4.2 外边界区域：原始笔画扩张5像素
    kernel_large = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    outer_region = cv2.dilate(denoised_mask, kernel_large, iterations=5)

    # 4.3 距离变换：计算outer_region内每个像素到边缘的最短距离
    # 输入要求：uint8, 0=背景, >0=前景；输出：float32，单位像素
    dist_map = cv2.distanceTransform(outer_region, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)

    # 4.4 SAF 参数 (论文明确值)
    alpha = 3.0
    L = 5.0
    exp_neg_alpha = np.exp(-alpha)
    C = (1 + exp_neg_alpha) / (1 - exp_neg_alpha + 1e-8)  # +eps防除零

    # 4.5 向量化计算软掩码（避免循环，提速100x）
    Ms_gt = np.zeros((H, W), dtype=np.float32)

    # 区域划分mask
    mask_skeleton = skeleton > 0  # 骨架区域 → 值=1
    mask_outer = outer_region > 0  # 扩张区域（含骨架）
    mask_middle = mask_outer & (~mask_skeleton)  # 中间环形区域 → 用SAF

    # (a) 骨架区域强制=1
    Ms_gt[mask_skeleton] = 1.0

    # (b) 中间区域应用SAF衰减
    if np.any(mask_middle):
        D = np.clip(dist_map[mask_middle], 0, L)  # 距离截断到[0, L]
        # SAF公式: C * (2/(1+exp(-α*D/L)) - 1)
        exp_term = np.exp(-alpha * D / L)
        saf_vals = C * (2.0 / (1.0 + exp_term + 1e-8) - 1.0)
        Ms_gt[mask_middle] = np.clip(saf_vals, 0.0, 1.0)

    # (c) 外边界及以外区域保持=0（已初始化为0）

    # ========== 5. 调试信息（可选） ==========
    if debug:
        debug_info = {
            'coarse_mask': coarse_mask,
            'denoised_mask': denoised_mask,
            'skeleton': skeleton,
            'outer_region': outer_region,
            'dist_map': dist_map,
            'mask_middle': mask_middle.astype(np.uint8) * 255
        }
        return Ms_gt, Mb_gt, debug_info

    return Ms_gt, Mb_gt


# -------------------------- 真实数据集加载类（核心修复：统一图像尺寸） --------------------------
# class EnsExamRealDataset(Dataset):
#     """
#     适配“仅含原始图+擦除GT图”的数据集加载类
#     ✅ 修复：所有图像读取后先resize到img_size，保证批量尺寸一致
#     """
#
#     def __init__(self, data_root, img_size=512, is_train=True):
#         self.data_root = data_root
#         self.img_size = img_size  # 统一目标尺寸（512×512）
#         self.is_train = is_train
#
#         # 1. 定义图像预处理：归一化到[-1,1]（匹配GAN训练）
#         self.img_transform = transforms.Compose([
#             transforms.ToTensor(),  # HWC→CHW，0-255→0-1
#             transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])  # 0-1→[-1,1]
#         ])
#
#         # 2. 加载文件列表（保证images和gt目录下文件同名）
#         split = "train" if is_train else "test"
#         self.img_dir = os.path.join(data_root, split, "all_images")
#         self.gt_dir = os.path.join(data_root, split, "all_labels")
#
#         # 过滤有效文件（仅保留png/jpg/jpeg）
#         self.file_names = [
#             f for f in os.listdir(self.img_dir)
#             if f.endswith((".png", ".jpg", ".jpeg")) and os.path.exists(os.path.join(self.gt_dir, f))
#         ]
#         assert len(self.file_names) > 0, f"未找到匹配的图像文件！检查{self.img_dir}和{self.gt_dir}目录"
#
#     def __len__(self):
#         return len(self.file_names)
#
#     def __getitem__(self, idx):
#         # 1. 加载原始图和擦除GT图
#         file_name = self.file_names[idx]
#         img_path = os.path.join(self.img_dir, file_name)
#         gt_path = os.path.join(self.gt_dir, file_name)
#
#         # 读取图像（BGR→RGB，避免OpenCV默认BGR格式问题）
#         Iin = cv2.imread(img_path)[:, :, ::-1]  # (H,W,3)，0-255，RGB
#         Igt = cv2.imread(gt_path)[:, :, ::-1]  # (H,W,3)，0-255，RGB
#
#         # ✅ 核心修复1：先统一resize到img_size×img_size（所有样本尺寸一致）
#         Iin = cv2.resize(Iin, (self.img_size, self.img_size), interpolation=cv2.INTER_LINEAR)
#         Igt = cv2.resize(Igt, (self.img_size, self.img_size), interpolation=cv2.INTER_LINEAR)
#
#         # 2. 自动生成Ms_gt（软笔画掩码）、Mb_gt（文本块掩码）
#         # ✅ 核心修复2：传入已resize的图像，函数内不再重复resize
#         Ms_gt_np, Mb_gt_np = generate_mask_from_pair(Iin, Igt, threshold=20)
#
#         # 3. 图像预处理（归一化到[-1,1]）
#         Iin = self.img_transform(Iin)  # (3,512,512)，[-1,1]
#         Igt = self.img_transform(Igt)  # (3,512,512)，[-1,1]
#
#         # 4. 掩码预处理（归一化到[0,1]，扩展通道维度）
#         Ms_gt = torch.from_numpy(Ms_gt_np).unsqueeze(0).float()  # (1,512,512)，[0,1]
#         Mb_gt = torch.from_numpy(Mb_gt_np).unsqueeze(0).float()  # (1,512,512)，[0,1]
#
#         # 5. 生成多尺度擦除GT（1/4, 1/2, 1/1）
#         # Igt4：512→128，Igt2：512→256，Igt1：原尺寸
#         Igt4 = F.interpolate(Igt.unsqueeze(0), size=(self.img_size // 4, self.img_size // 4), mode='bilinear',
#                              align_corners=False).squeeze(0)
#         Igt2 = F.interpolate(Igt.unsqueeze(0), size=(self.img_size // 2, self.img_size // 2), mode='bilinear',
#                              align_corners=False).squeeze(0)
#         Igt1 = Igt  # 1:1尺度
#
#         # 返回顺序：Iin, Ms_gt, Mb_gt, Igt4, Igt2, Igt1, Igt
#         return Iin, Ms_gt, Mb_gt, Igt4, Igt2, Igt1, Igt

class EnsExamRealDataset(Dataset):
    """
    适配“仅含原始图 + 擦除 GT 图”的数据集加载类
    ✅ 修改：不再 resize 原图，而是将大图裁剪为多个 512x512 的样本块
    """

    def __init__(self, data_root, img_size=512, is_train=True, overlap=0):
        """
        :param data_root: 数据集根目录
        :param img_size: 裁剪块尺寸 (默认 512)
        :param is_train: 是否训练模式
        :param overlap: 裁剪重叠像素 (默认 0，即不重叠；训练时可设为 128 增加数据量)
        """
        self.data_root = data_root
        self.img_size = img_size
        self.is_train = is_train
        self.overlap = overlap

        # 1. 定义图像预处理：归一化到 [-1,1]
        self.img_transform = transforms.Compose([
            transforms.ToTensor(),  # HWC→CHW, 0-255→0-1
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])

        # 2. 获取文件路径
        split = "train" if is_train else "test"
        self.img_dir = os.path.join(data_root, split, "all_images")
        self.gt_dir = os.path.join(data_root, split, "all_labels")

        # 3. ✅ 核心修改：构建“样本索引列表”
        # 不再是一对一 (1 图=1 样本)，而是一对多 (1 图=N 个样本块)
        self.patch_index_map = []

        valid_extensions = (".png", ".jpg", ".jpeg")
        all_files = [f for f in os.listdir(self.img_dir) if f.endswith(valid_extensions)]

        print(f"🔍 正在扫描数据集并构建裁剪索引 (Overlap={overlap})...")
        for fname in all_files:
            if not os.path.exists(os.path.join(self.gt_dir, fname)):
                continue

            img_path = os.path.join(self.img_dir, fname)
            gt_path = os.path.join(self.gt_dir, fname)

            # 读取尺寸 (仅读取头信息，不加载像素，速度快)
            # 如果 cv2.imread 太慢，可用 imageio 或 PIL 获取 size，这里为了兼容直接用 cv2
            # 注意：这里必须加载一次获取 H,W，或者用 cv2.imread + IMREAD_UNCHANGED
            img_temp = cv2.imread(img_path)
            if img_temp is None: continue
            H, W = img_temp.shape[:2]
            del img_temp  # 释放内存

            # 计算步长
            step = self.img_size - self.overlap
            if step <= 0: step = 1  # 防止 overlap 过大导致步长为 0

            # 计算该图能切多少块 (覆盖全图，边缘不足补黑)
            # 使用 math.ceil 确保覆盖整张图
            num_h = math.ceil((H - self.overlap) / step) if H > self.img_size else 1
            num_w = math.ceil((W - self.overlap) / step) if W > self.img_size else 1

            # 如果原图小于 512，也作为一个样本 (后续会 padding)
            if H <= self.img_size and W <= self.img_size:
                num_h, num_w = 1, 1

            for i in range(num_h):
                for j in range(num_w):
                    # 计算裁剪坐标
                    y1 = i * step
                    x1 = j * step

                    # 如果是最后一块，确保覆盖到边缘
                    y2 = min(y1 + self.img_size, H)
                    x2 = min(x1 + self.img_size, W)

                    # 如果是第一块且图很小，直接取全图
                    if H <= self.img_size: y1, y2 = 0, H
                    if W <= self.img_size: x1, x2 = 0, W

                    # 记录样本信息：(图路径，GT 路径，裁剪坐标，是否需要 padding)
                    need_pad_h = (y2 - y1) < self.img_size
                    need_pad_w = (x2 - x1) < self.img_size

                    self.patch_index_map.append({
                        'img_path': img_path,
                        'gt_path': gt_path,
                        'y1': y1, 'y2': y2,
                        'x1': x1, 'x2': x2,
                        'pad_h': need_pad_h,
                        'pad_w': need_pad_w
                    })

        print(f"✅ 索引构建完成：共 {len(self.patch_index_map)} 个样本块 (来自 {len(all_files)} 张图)")
        assert len(self.patch_index_map) > 0, "未找到有效样本！"

    def __len__(self):
        return len(self.patch_index_map)

    def __getitem__(self, idx):
        # 1. 获取当前样本的裁剪信息
        info = self.patch_index_map[idx]

        # print(f"🔎 Loading: {info['img_path']}")
        # print(f"   Exists: {os.path.exists(info['img_path'])}")

        # 2. 加载完整原图 (RGB)
        Iin_full = cv2.imread(info['img_path'])[:, :, ::-1]
        Igt_full = cv2.imread(info['gt_path'])[:, :, ::-1]

        # 3. ✅ 核心修改：根据坐标裁剪
        Iin = Iin_full[info['y1']:info['y2'], info['x1']:info['x2']]
        Igt = Igt_full[info['y1']:info['y2'], info['x1']:info['x2']]

        Iin = np.ascontiguousarray(Iin)
        Igt = np.ascontiguousarray(Igt)

        # 4. ✅ 边缘填充 (确保输入模型的都是 512x512)
        if info['pad_h'] or info['pad_w']:
            pad_h = self.img_size - Iin.shape[0]
            pad_w = self.img_size - Iin.shape[1]
            # 使用 REPLICATE 填充比 CONSTANT(黑边) 更好，减少边界伪影
            Iin = cv2.copyMakeBorder(Iin, 0, pad_h, 0, pad_w, cv2.BORDER_REPLICATE)
            Igt = cv2.copyMakeBorder(Igt, 0, pad_h, 0, pad_w, cv2.BORDER_REPLICATE)

        # 5. 生成掩码 (输入已经是 512x512)
        # 注意：这里调用的是单块生成函数，不是滑动拼接函数
        Ms_gt_np, Mb_gt_np = generate_mask_from_pair(Iin, Igt, threshold=20)

        # 6. 图像预处理 (归一化)
        Iin = self.img_transform(Iin)  # (3, 512, 512)
        Igt = self.img_transform(Igt)  # (3, 512, 512)

        # 7. 掩码转 Tensor
        Ms_gt = torch.from_numpy(Ms_gt_np).unsqueeze(0).float()
        Mb_gt = torch.from_numpy(Mb_gt_np).unsqueeze(0).float()

        # 8. 生成多尺度 GT (1/4, 1/2, 1/1)
        Igt_unsqueeze = Igt.unsqueeze(0)
        Igt4 = F.interpolate(Igt_unsqueeze, size=(self.img_size // 4, self.img_size // 4),
                             mode='bilinear', align_corners=False).squeeze(0)
        Igt2 = F.interpolate(Igt_unsqueeze, size=(self.img_size // 2, self.img_size // 2),
                             mode='bilinear', align_corners=False).squeeze(0)
        Igt1 = Igt

        # 返回：Iin, Ms_gt, Mb_gt, Igt4, Igt2, Igt1, Igt
        return Iin, Ms_gt, Mb_gt, Igt4, Igt2, Igt1, Igt

# ====================== 3. 核心训练函数 ======================
def train_ensexam(
        epochs=100,
        batch_size=4,
        lr=0.0001,
        device='cuda',
        save_dir='./checkpoints',
        resume=False,  # 是否断点续训
        resume_path='./checkpoints/latest.pth',
        data_root='./data',
):
    # 0. 初始化目录
    os.makedirs(save_dir, exist_ok=True)

    # 1. 数据加载
    train_dataset = EnsExamRealDataset(data_root=data_root)
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,  # Windows下建议设为0，避免多进程问题
        drop_last=True
    )

    # 2. 模型初始化
    G = Generator().to(device)
    D = Discriminator().to(device)
    criterion = EnsExamLoss().to(device)

    # 3. 优化器
    optimizer_G = optim.Adam(G.parameters(), lr=lr, betas=(0.5, 0.9))
    optimizer_D = optim.Adam(D.parameters(), lr=lr, betas=(0.5, 0.9))

    # 4. 断点续训
    start_epoch = 0
    if resume and os.path.exists(resume_path):
        checkpoint = torch.load(resume_path, map_location=device)
        G.load_state_dict(checkpoint['G_state_dict'])
        D.load_state_dict(checkpoint['D_state_dict'])
        optimizer_G.load_state_dict(checkpoint['optimizer_G'])
        optimizer_D.load_state_dict(checkpoint['optimizer_D'])
        start_epoch = checkpoint['epoch']
        print(f"断点续训：从第{start_epoch}Epoch恢复")

    # 5. 训练循环
    G.train()
    D.train()
    for epoch in range(start_epoch, epochs):
        epoch_loss_G = 0.0  # 生成器总损失
        epoch_loss_D = 0.0  # 判别器总损失
        pbar = tqdm(train_loader, desc=f"Epoch {epoch + 1}/{epochs}")

        for batch_idx, (Iin, Ms_gt, Mb_gt, Igt4, Igt2, Igt1, Igt) in enumerate(pbar):
            # 数据移到设备
            Iin = Iin.to(device)
            Ms_gt = Ms_gt.to(device)
            Mb_gt = Mb_gt.to(device)
            Igt4 = Igt4.to(device)
            Igt2 = Igt2.to(device)
            Igt1 = Igt1.to(device)
            Igt = Igt.to(device)
            gt = (Ms_gt, Mb_gt, Igt4, Igt2, Igt1, Igt)

            # ---------------------- 步骤1：训练判别器D ----------------------
            optimizer_D.zero_grad()

            # 1.1 真实图像判别
            real_global, real_local = D(Igt, Mb_gt)
            # 1.2 生成图像判别
            gen_out = G(Iin)
            Icomp = gen_out[-1]  # 取最后一个输出Icomp
            fake_global, fake_local = D(Icomp.detach(), Mb_gt)
            # 1.3 计算D损失（使用Model中的hinge_loss_D）
            loss_D_global = EnsExamLoss.hinge_loss_D(real_global, fake_global)
            loss_D_local = EnsExamLoss.hinge_loss_D(real_local, fake_local)
            loss_D = (loss_D_global + loss_D_local) / 2

            loss_D.backward()
            optimizer_D.step()

            # ---------------------- 步骤2：训练生成器G ----------------------
            optimizer_G.zero_grad()

            # 2.1 重新计算生成图像的判别分数
            fake_global, fake_local = D(Icomp, Mb_gt)
            disc_score = (fake_global, fake_local)
            # 2.2 计算G的全量损失（Model中的EnsExamLoss.forward）
            loss_G, loss_parts = criterion(gen_out, gt, disc_score)

            loss_G.backward()
            optimizer_G.step()

            # ---------------------- 步骤3：日志记录 ----------------------
            epoch_loss_G += loss_G.item()
            epoch_loss_D += loss_D.item()

            # 进度条显示
            pbar.set_postfix({
                'Loss_D': f"{loss_D.item():.4f}",
                'Loss_G': f"{loss_G.item():.4f}",
                'Loss_G_adv': f"{loss_parts[0].item():.4f}",
                'Loss_G_lr': f"{loss_parts[1].item():.4f}"
            })

        # ---------------------- 步骤4：Epoch结束处理 ----------------------
        # 计算Epoch平均损失
        avg_loss_G = epoch_loss_G / len(train_loader)
        avg_loss_D = epoch_loss_D / len(train_loader)
        print(f"Epoch {epoch + 1} 平均损失：Loss_G={avg_loss_G:.4f}, Loss_D={avg_loss_D:.4f}")

        # 保存模型（每5个Epoch保存一次，同时保存最新模型）
        if (epoch + 1) % 5 == 0 or epoch == epochs - 1:
            checkpoint = {
                'epoch': epoch + 1,
                'G_state_dict': G.state_dict(),
                'D_state_dict': D.state_dict(),
                'optimizer_G': optimizer_G.state_dict(),
                'optimizer_D': optimizer_D.state_dict(),
                'avg_loss_G': avg_loss_G,
                'avg_loss_D': avg_loss_D
            }
            # 保存最新模型（用于断点续训）
            torch.save(checkpoint, os.path.join(save_dir, 'latest.pth'))
            # 保存Epoch模型
            torch.save(checkpoint, os.path.join(save_dir, f'ensexam_epoch_{epoch + 1}.pth'))
            print(f"模型已保存：{os.path.join(save_dir, f'ensexam_epoch_{epoch + 1}.pth')}")


# ====================== 4. 启动训练 ======================
if __name__ == "__main__":
    # 设备选择
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"使用设备：{device}")

    # 启动训练
    train_ensexam(
        epochs=100,
        batch_size=4,
        lr=0.0001,
        device=device,
        save_dir='./ensexam_checkpoints',
        resume=False,
        data_root=r"D:\PythonProject1\LLM\adcj\src\adcj\EnsExam\SCUT-EnsExam\SCUT-EnsExam",
    )