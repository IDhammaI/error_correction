# 设备
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


# -------------------------- 核心工具函数：自动生成掩码 --------------------------
def generate_mask_from_pair(Iin, Igt, threshold=20):
    """
    从已resize的原始图(Iin)和擦除GT图(Igt)生成掩码：
    ✅ 修复：移除函数内的resize，改用外部统一resize后的图像
    :param Iin: 已resize的原始图像（H,W,3），0-255，RGB格式
    :param Igt: 已resize的擦除GT图像（H,W,3），0-255，RGB格式
    :param threshold: 像素差异阈值（适配手写文本）
    :return: Ms_gt (H,W)、Mb_gt (H,W)，均为0-1的numpy数组
    """
    # 1. 生成粗笔画掩码（像素差异法）
    diff = np.abs(Iin - Igt).mean(axis=-1)  # 灰度化相减，计算像素差异
    coarse_mask = (diff > threshold).astype(np.uint8) * 255  # 二值化

    # 2. 生成Mb_gt（文本块掩码：膨胀+闭运算，扩大文本区域）
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    Mb_gt = cv2.dilate(coarse_mask, kernel, iterations=2)  # 膨胀扩大文本块
    Mb_gt = cv2.morphologyEx(Mb_gt, cv2.MORPH_CLOSE, kernel)  # 闭运算填充孔洞
    Mb_gt = Mb_gt / 255.0  # 归一化到0-1

    # 3. 生成Ms_gt（软笔画掩码：细化+渐变）
    # 步骤1：去噪（腐蚀+膨胀）
    denoised_mask = cv2.morphologyEx(coarse_mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
    # 步骤2：提取骨架（细化笔画）
    skeleton = np.zeros_like(denoised_mask)
    temp_mask = denoised_mask.copy()
    while True:
        eroded = cv2.erode(temp_mask, kernel)
        temp = cv2.dilate(eroded, kernel)
        temp = cv2.subtract(temp_mask, temp)
        skeleton = cv2.bitwise_or(skeleton, temp)
        temp_mask = eroded.copy()
        if cv2.countNonZero(temp_mask) == 0:
            break
    # 步骤3：生成软掩码（骨架=1，边界渐变）
    dist = cv2.distanceTransform(255 - denoised_mask, cv2.DIST_L2, 5)
    dist = np.clip(dist, 0, 5)
    alpha = 3
    L = 5
    C = (1 + np.exp(-alpha)) / (1 - np.exp(-alpha))
    saf = C * (2 / (1 + np.exp(-alpha * dist / L)) - 1)
    saf = np.clip(saf, 0, 1)
    saf[skeleton > 0] = 1.0  # 骨架区域强制为1
    Ms_gt = saf

    return Ms_gt, Mb_gt


# -------------------------- 真实数据集加载类（核心修复：统一图像尺寸） --------------------------
class EnsExamRealDataset(Dataset):
    """
    适配“仅含原始图+擦除GT图”的数据集加载类
    ✅ 修复：所有图像读取后先resize到img_size，保证批量尺寸一致
    """

    def __init__(self, data_root, img_size=512, is_train=True):
        self.data_root = data_root
        self.img_size = img_size  # 统一目标尺寸（512×512）
        self.is_train = is_train

        # 1. 定义图像预处理：归一化到[-1,1]（匹配GAN训练）
        self.img_transform = transforms.Compose([
            transforms.ToTensor(),  # HWC→CHW，0-255→0-1
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])  # 0-1→[-1,1]
        ])

        # 2. 加载文件列表（保证images和gt目录下文件同名）
        split = "train" if is_train else "test"
        self.img_dir = os.path.join(data_root, split, "all_images")
        self.gt_dir = os.path.join(data_root, split, "all_labels")

        # 过滤有效文件（仅保留png/jpg/jpeg）
        self.file_names = [
            f for f in os.listdir(self.img_dir)
            if f.endswith((".png", ".jpg", ".jpeg")) and os.path.exists(os.path.join(self.gt_dir, f))
        ]
        assert len(self.file_names) > 0, f"未找到匹配的图像文件！检查{self.img_dir}和{self.gt_dir}目录"

    def __len__(self):
        return len(self.file_names)

    def __getitem__(self, idx):
        # 1. 加载原始图和擦除GT图
        file_name = self.file_names[idx]
        img_path = os.path.join(self.img_dir, file_name)
        gt_path = os.path.join(self.gt_dir, file_name)

        # 读取图像（BGR→RGB，避免OpenCV默认BGR格式问题）
        Iin = cv2.imread(img_path)[:, :, ::-1]  # (H,W,3)，0-255，RGB
        Igt = cv2.imread(gt_path)[:, :, ::-1]  # (H,W,3)，0-255，RGB

        # ✅ 核心修复1：先统一resize到img_size×img_size（所有样本尺寸一致）
        Iin = cv2.resize(Iin, (self.img_size, self.img_size), interpolation=cv2.INTER_LINEAR)
        Igt = cv2.resize(Igt, (self.img_size, self.img_size), interpolation=cv2.INTER_LINEAR)

        # 2. 自动生成Ms_gt（软笔画掩码）、Mb_gt（文本块掩码）
        # ✅ 核心修复2：传入已resize的图像，函数内不再重复resize
        Ms_gt_np, Mb_gt_np = generate_mask_from_pair(Iin, Igt, threshold=20)

        # 3. 图像预处理（归一化到[-1,1]）
        Iin = self.img_transform(Iin.astype(np.float32))  # (3,512,512)，[-1,1]
        Igt = self.img_transform(Igt.astype(np.float32))  # (3,512,512)，[-1,1]

        # 4. 掩码预处理（归一化到[0,1]，扩展通道维度）
        Ms_gt = torch.from_numpy(Ms_gt_np).unsqueeze(0).float()  # (1,512,512)，[0,1]
        Mb_gt = torch.from_numpy(Mb_gt_np).unsqueeze(0).float()  # (1,512,512)，[0,1]

        # 5. 生成多尺度擦除GT（1/4, 1/2, 1/1）
        # Igt4：512→128，Igt2：512→256，Igt1：原尺寸
        Igt4 = F.interpolate(Igt.unsqueeze(0), size=(self.img_size // 4, self.img_size // 4), mode='bilinear',
                             align_corners=False).squeeze(0)
        Igt2 = F.interpolate(Igt.unsqueeze(0), size=(self.img_size // 2, self.img_size // 2), mode='bilinear',
                             align_corners=False).squeeze(0)
        Igt1 = Igt  # 1:1尺度

        # 返回顺序：Iin, Ms_gt, Mb_gt, Igt4, Igt2, Igt1, Igt
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

            # 1.1 真实图像的判别损失（label=real）
            real_global_score, real_local_score = D(Igt, Mb_gt)
            loss_D_real = (criterion.adversarial_loss(real_global_score, is_real=True) +
                           criterion.adversarial_loss(real_local_score, is_real=True)) / 2

            # 1.2 生成图像的判别损失（label=fake）
            gen_out = G(Iin)
            Icomp = gen_out[-1]  # 生成的最终擦除结果
            fake_global_score, fake_local_score = D(Icomp.detach(), Mb_gt)  # detach避免更新G
            loss_D_fake = (criterion.adversarial_loss(fake_global_score, is_real=False) +
                           criterion.adversarial_loss(fake_local_score, is_real=False)) / 2

            # 1.3 D总损失 & 反向传播
            loss_D = (loss_D_real + loss_D_fake) / 2
            loss_D.backward()
            optimizer_D.step()

            # ---------------------- 步骤2：训练生成器G ----------------------
            optimizer_G.zero_grad()

            # 2.1 重新计算生成图像的判别分数（用于G的对抗损失）
            fake_global_score, fake_local_score = D(Icomp, Mb_gt)
            disc_score = (fake_global_score, fake_local_score)

            # 2.2 计算G的全量损失
            loss_G, loss_parts = criterion(gen_out, gt, disc_score)

            # 2.3 G反向传播
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