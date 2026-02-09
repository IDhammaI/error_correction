import math

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from torch import nn
from torchvision.models import vgg16


def generate_soft_stroke_mask(Iin, Igt, alpha=3, L=5, threshold=20):
    """
    生成软笔画掩码
    :param Iin: 原始图像
    :param Igt: 擦除GT图像
    :param alpha: SAF函数参数
    :param L: 最大距离
    :param threshold: 粗掩码阈值
    :return: 软笔画掩码Ms [H, W] 0-1
    """
    diff = np.abs(Igt - Iin).mean(axis=-1)
    coarse_mask = (diff > threshold).astype(np.uint8) * 255

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
    denoised_mask = cv2.morphologyEx(coarse_mask, cv2.MORPH_CLOSE, kernel)

    skeleton = cv2.erode(denoised_mask, kernel, iterations=1)
    outer = cv2.dilate(denoised_mask, kernel, iterations=1)

    dist = cv2.distanceTransform(255-outer, cv2.DIST_L2, 5)
    dist = np.clip(dist, 0, L)

    C = (1 + math.exp(-alpha)) / (1 - math.exp(-alpha))
    saf = C * (2 / (1 + np.exp(-alpha * dist / L)) - 1)
    saf = np.clip(saf, 0, 1)

    saf[skeleton > 0] = 1.0
    return saf

# CBAM注意力模块（轻量版，适配U-Net）
class CBAM(nn.Module):
    def __init__(self, in_channels, reduction=16):
        super().__init__()
        # 通道注意力
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(in_channels, in_channels//reduction),
            nn.ReLU(inplace=True),
            nn.Linear(in_channels//reduction, in_channels)
        )
        # 空间注意力
        self.spatial = nn.Sequential(
            nn.Conv2d(2, 1, 3, padding=1, bias=False),
            nn.Sigmoid()
        )
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        b, c, h, w = x.shape
        # 通道注意力
        avg_out = self.fc(self.avg_pool(x).view(b,c)).view(b,c,1,1)
        max_out = self.fc(self.max_pool(x).view(b,c)).view(b,c,1,1)
        channel_att = self.sigmoid(avg_out + max_out)
        x = x * channel_att
        # 空间注意力
        avg_out = torch.mean(x, dim=1, keepdim=True)
        max_out, _ = torch.max(x, dim=1, keepdim=True)
        spatial_att = self.spatial(torch.cat([avg_out, max_out], dim=1))
        x = x * spatial_att
        return x

# 空洞卷积块（Refine网络用）
class DilatedConvBlock(nn.Module):
    def __init__(self, in_channels, out_channels, dilation=2):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 3, padding=dilation, dilation=dilation, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
    def forward(self, x):
        return self.block(x)

# U-Net下采样块（Coarse/Refine网络编码器）
class DownSample(nn.Module):
    def __init__(self, in_channels, out_channels, use_cbam=False):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 4, 2, 1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.LeakyReLU(0.2, inplace=True)
        )
        self.cbam = CBAM(out_channels) if use_cbam else nn.Identity()
    def forward(self, x):
        x = self.conv(x)
        x = self.cbam(x)
        return x

# U-Net上采样块（Coarse网络解码器）
class UpSample(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv = nn.Sequential(
            nn.ConvTranspose2d(in_channels, out_channels, 4, 2, 1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
    def forward(self, x):
        return self.conv(x)

# 带空洞卷积的上采样块（Refine网络解码器）
class DilatedUpSample(nn.Module):
    def __init__(self, in_channels, out_channels, dilation=2):
        super().__init__()
        self.conv = nn.Sequential(
            nn.ConvTranspose2d(in_channels, out_channels, 4, 2, 1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
        self.dilated = DilatedConvBlock(out_channels, out_channels, dilation)
    def forward(self, x):
        x = self.conv(x)
        x = self.dilated(x)
        return x

# Coarse网络
class CoarseNet(nn.Module):
    def __init__(self, in_channels=3):
        super().__init__()
        # 编码器：下采样+CBAM
        self.down1 = DownSample(in_channels, 64, use_cbam=False)  # 1/2
        self.down2 = DownSample(64, 128, use_cbam=True)          # 1/4
        self.down3 = DownSample(128, 256, use_cbam=True)         # 1/8
        self.down4 = DownSample(256, 512, use_cbam=True)         # 1/16
        self.down5 = DownSample(512, 512, use_cbam=True)         # 1/32
        # 解码器：上采样
        self.up1 = UpSample(512, 512)    # 1/16
        self.up2 = UpSample(1024, 256)   # 1/8
        self.up3 = UpSample(512, 128)    # 1/4 → Ic4
        self.up4 = UpSample(256, 64)     # 1/2 → Ic2
        self.up5 = UpSample(128, 64)     # 1/1 → Ic1
        # 输出层：Ms(笔画掩码), Mb(文本块掩码), 多尺度Ic
        self.out_ms = nn.Conv2d(64, 1, 3, 1, 1)
        self.out_mb = nn.Conv2d(64, 1, 3, 1, 1)
        self.out_ic4 = nn.Conv2d(128, 3, 3, 1, 1)
        self.out_ic2 = nn.Conv2d(64, 3, 3, 1, 1)
        self.out_ic1 = nn.Conv2d(64, 3, 3, 1, 1)

    def forward(self, x):
        # 编码器
        d1 = self.down1(x)
        d2 = self.down2(d1)
        d3 = self.down3(d2)
        d4 = self.down4(d3)
        d5 = self.down5(d4)
        # 解码器
        u1 = self.up1(d5)
        u2 = self.up2(torch.cat([u1, d4], dim=1))
        u3 = self.up3(torch.cat([u2, d3], dim=1))  # 1/4
        u4 = self.up4(torch.cat([u3, d2], dim=1))  # 1/2
        u5 = self.up5(torch.cat([u4, d1], dim=1))  # 1/1
        # 输出
        Ic4 = self.out_ic4(u3)
        Ic2 = self.out_ic2(u4)
        Ic1 = self.out_ic1(u5)
        Ms = self.out_ms(u5)
        Mb = self.out_mb(u5)
        return Ms, Mb, Ic4, Ic2, Ic1

# Refine网络
class RefineNet(nn.Module):
    def __init__(self, in_channels=7):  # 3(Iin)+1(Ms)+3(Ic1) =7
        super().__init__()
        # 编码器：下采样
        self.down1 = DownSample(in_channels, 64, use_cbam=False)  # 1/2
        self.down2 = DownSample(64, 128, use_cbam=False)          # 1/4
        self.down3 = DownSample(128, 256, use_cbam=False)         # 1/8
        self.down4 = DownSample(256, 512, use_cbam=False)         # 1/16
        # 解码器：带空洞卷积的上采样
        self.up1 = DilatedUpSample(512, 256)    # 1/8
        self.up2 = DilatedUpSample(512, 128)     # 1/4
        self.up3 = DilatedUpSample(256, 64)      # 1/2
        self.up4 = DilatedUpSample(128, 64)      # 1/1
        # 输出层：精细化擦除结果Ire
        self.out_ire = nn.Conv2d(64, 3, 3, 1, 1)

    def forward(self, x):
        # 编码器
        d1 = self.down1(x)
        d2 = self.down2(d1)
        d3 = self.down3(d2)
        d4 = self.down4(d3)
        # 解码器
        u1 = self.up1(d4)
        u2 = self.up2(torch.cat([u1, d3], dim=1))
        u3 = self.up3(torch.cat([u2, d2], dim=1))
        u4 = self.up4(torch.cat([u3, d1], dim=1))
        # 输出
        Ire = self.out_ire(u4)
        return Ire

# 生成器整体
class Generator(nn.Module):
    def __init__(self):
        super().__init__()
        self.coarse = CoarseNet()
        self.refine = RefineNet()

    def forward(self, Iin):
        # Coarse网络输出
        Ms, Mb, Ic4, Ic2, Ic1 = self.coarse(Iin)
        # 拼接输入：Iin + Ms + Ic1（通道维度）
        refine_in = torch.cat([Iin, Ms, Ic1], dim=1)
        # Refine网络输出
        Ire = self.refine(refine_in)
        # 融合得到最终结果Icomp
        Icomp = Ire * Mb + Iin * (1 - Mb)
        return Ms, Mb, Ic4, Ic2, Ic1, Ire, Icomp



# 基础判别器块
class DiscBlock(nn.Module):
    def __init__(self, in_channels, out_channels, stride=2):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 4, stride, 1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.LeakyReLU(0.2, inplace=True)
        )
    def forward(self, x):
        return self.block(x)

# Local-Global判别器
class Discriminator(nn.Module):
    def __init__(self, in_channels=3):
        super().__init__()
        # 全局判别器：判整图
        self.global_disc = nn.Sequential(
            DiscBlock(in_channels, 64),
            DiscBlock(64, 128),
            DiscBlock(128, 256),
            DiscBlock(256, 512),
            nn.Conv2d(512, 1, 4, 1, 0, bias=False)
        )
        # 局部判别器：仅判文本区域（结构同全局）
        self.local_disc = nn.Sequential(
            DiscBlock(in_channels, 64),
            DiscBlock(64, 128),
            DiscBlock(128, 256),
            DiscBlock(256, 512),
            nn.Conv2d(512, 1, 4, 1, 0, bias=False)
        )

    def forward(self, x, local_mask=None):
        """
        :param x: 输入图像 [B,3,H,W]
        :param local_mask: 文本区域掩码GT [B,1,H,W] 用于提取局部区域
        :return: global_score, local_score
        """
        # 全局判别分数
        global_score = self.global_disc(x)
        # 局部判别分数：仅对文本区域做判别
        local_score = 0
        if local_mask is not None:
            # 提取文本区域的特征
            local_x = x * local_mask
            local_score = self.local_disc(local_x)
        return global_score, local_score


# 加载预训练VGG16（用于感知/风格损失）
class VGG16Feature(nn.Module):
    def __init__(self):
        super().__init__()
        vgg = vgg16(pretrained=True).features
        self.feat1 = nn.Sequential(*vgg[:5])   # 第1个池化层前
        self.feat2 = nn.Sequential(*vgg[5:10]) # 第2个池化层前
        self.feat3 = nn.Sequential(*vgg[10:17])# 第3个池化层前
        # 冻结参数
        for param in self.parameters():
            param.requires_grad = False

    def forward(self, x):
        # x: [B,3,H,W] 归一化到ImageNet标准
        x = F.interpolate(x, size=(224,224), mode='bilinear', align_corners=False)
        f1 = self.feat1(x)
        f2 = self.feat2(f1)
        f3 = self.feat3(f2)
        return [f1, f2, f3]

# Gram矩阵计算
def gram_matrix(x):
    b, c, h, w = x.shape
    x = x.view(b, c, h*w)
    return torch.bmm(x, x.transpose(1,2)) / (c*h*w)

# 全量Loss计算类
class EnsExamLoss(nn.Module):
    def __init__(self):
        super().__init__()
        self.vgg_feat = VGG16Feature().cuda()
        # LR Loss权重：Ic4, Ic2, Ic1, Ire
        self.lambda_n = [0.5, 0.6, 0.8, 1.0]  # 原[5,6,8,10] → 缩小10倍
        self.beta_n = [0.08, 0.08, 0.08, 0.2]  # 原[0.8,0.8,0.8,2] → 缩小10倍
        # 总损失权重
        self.lambda_lr = 1.0
        self.lambda_p = 0.005  # 感知损失权重降低（原0.05）
        self.lambda_style = 12.0  # 风格损失权重降低（原120）
        self.lambda_sn = 0.1  # SN损失权重降低（原1.0）
        self.lambda_b = 0.04  # Block损失权重降低（原0.4）

    def sn_loss(self, Ms, Ms_gt):
        """SN损失"""
        l1 = F.l1_loss(Ms, Ms_gt, reduction='sum')
        sum_ms = Ms.sum()
        sum_ms_gt = Ms_gt.sum()
        min_sum = torch.min(sum_ms, sum_ms_gt) + 1e-8  # 避免除0
        return l1 / min_sum

    def block_loss(self, Mb, Mb_gt):
        """Block损失（Dice Loss）"""
        intersection = (Mb * Mb_gt).sum()
        union = (Mb**2).sum() + (Mb_gt**2).sum() + 1e-8
        dice = 2 * intersection / union
        return 1 - dice

    def lr_loss(self, Iouts, Igt_list, Mb_gt):
        """LR损失（修复多尺度掩码维度匹配问题）"""
        lr_loss = 0.0
        for i, (Iout, Igt) in enumerate(zip(Iouts, Igt_list)):
            # 关键修复：将Mb_gt下采样到当前Iout/Igt的尺度
            # 获取当前Iout的高/宽
            _, _, h, w = Iout.shape
            # 下采样Mb_gt到(h, w)，保持通道数不变
            Mb_gt_scaled = F.interpolate(Mb_gt, size=(h, w), mode='bilinear', align_corners=False)

            # 文本区域损失（使用下采样后的掩码）
            loss_text = F.l1_loss(Iout * Mb_gt_scaled, Igt * Mb_gt_scaled, reduction='mean')
            # 非文本区域损失（使用下采样后的掩码）
            loss_nontext = F.l1_loss(Iout * (1 - Mb_gt_scaled), Igt * (1 - Mb_gt_scaled), reduction='mean')
            # 加权求和
            lr_loss += self.lambda_n[i] * loss_text + self.beta_n[i] * loss_nontext
        return lr_loss

    def perceptual_loss(self, I_list, Igt):
        """感知损失"""
        per_loss = 0.0
        gt_feats = self.vgg_feat(Igt)
        for I in I_list:
            I_feats = self.vgg_feat(I)
            for f1, f2 in zip(I_feats, gt_feats):
                per_loss += F.l1_loss(f1, f2, reduction='sum')
        return per_loss

    def style_loss(self, I_list, Igt):
        """风格损失"""
        style_loss = 0.0
        gt_feats = self.vgg_feat(Igt)
        gt_grams = [gram_matrix(f) for f in gt_feats]
        for I in I_list:
            I_feats = self.vgg_feat(I)
            I_grams = [gram_matrix(f) for f in I_feats]
            for g1, g2 in zip(I_grams, gt_grams):
                style_loss += F.l1_loss(g1, g2, reduction='sum')
        return style_loss

    def adversarial_loss(self, score, is_real):
        """Hinge对抗损失"""
        if is_real:
            loss = torch.mean(F.relu(1 - score))
        else:
            loss = torch.mean(F.relu(1 + score))
        return loss

    def forward(self, gen_out, gt, disc_score):
        """
        总损失计算
        :param gen_out: 生成器输出 (Ms, Mb, Ic4, Ic2, Ic1, Ire, Icomp)
        :param gt: 标签 (Ms_gt, Mb_gt, Igt4, Igt2, Igt1, Igt)
        :param disc_score: 判别器分数 (global_score, local_score)
        :return: 总损失，各分项损失
        """
        Ms, Mb, Ic4, Ic2, Ic1, Ire, Icomp = gen_out
        Ms_gt, Mb_gt, Igt4, Igt2, Igt1, Igt = gt
        global_score, local_score = disc_score

        # 各分项损失
        L_sn = self.sn_loss(Ms, Ms_gt) * self.lambda_sn
        L_block = self.block_loss(Mb, Mb_gt) * self.lambda_b
        L_lr = self.lr_loss([Ic4, Ic2, Ic1, Ire], [Igt4, Igt2, Igt1, Igt], Mb_gt) * self.lambda_lr
        L_per = self.perceptual_loss([Ire, Icomp], Igt) * self.lambda_p
        L_style = self.style_loss([Ire, Icomp], Igt) * self.lambda_style
        L_adv = (self.adversarial_loss(global_score, False) + self.adversarial_loss(local_score, False)) / 2

        # 总损失
        L_total = L_adv + L_lr + L_per + L_style + L_sn + L_block
        return L_total, [L_adv, L_lr, L_per, L_style, L_sn, L_block]