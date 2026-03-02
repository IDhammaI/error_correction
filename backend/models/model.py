import math

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from torch import nn
from torchvision.models import vgg16


class CBAM(nn.Module):
    def __init__(self, in_channels, reduction=16):
        super().__init__()
        # 通道注意力（标准实现）
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)
        self.mlp = nn.Sequential(
            nn.Linear(in_channels, in_channels // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(in_channels // reduction, in_channels, bias=False)
        )
        self.sigmoid = nn.Sigmoid()

        # 空间注意力（关键修正：7×7卷积 + 无BatchNorm）
        self.spatial = nn.Sequential(
            nn.Conv2d(2, 1, kernel_size=7, padding=3, bias=False),  # ✅ 7×7
            nn.Sigmoid()  # ✅ 无BatchNorm
        )

    def forward(self, x):
        b, c, h, w = x.shape

        # ========== 通道注意力 ==========
        avg_out = self.mlp(self.avg_pool(x).view(b, c)).view(b, c, 1, 1)
        max_out = self.mlp(self.max_pool(x).view(b, c)).view(b, c, 1, 1)
        channel_att = self.sigmoid(avg_out + max_out)
        x = x * channel_att  # 广播相乘 [B,C,H,W] * [B,C,1,1]

        # ========== 空间注意力 ==========
        avg_out = torch.mean(x, dim=1, keepdim=True)  # [B,1,H,W]
        max_out, _ = torch.max(x, dim=1, keepdim=True)  # [B,1,H,W]
        spatial_att = self.spatial(torch.cat([avg_out, max_out], dim=1))  # [B,1,H,W]
        x = x * spatial_att  # 广播相乘 [B,C,H,W] * [B,1,H,W]

        return x


# 空洞卷积块（Refine网络用）
class DilatedConvBlock(nn.Module):
    def __init__(self, in_channels, out_channels, dilation=2):
        super().__init__()
        padding = dilation * (3 - 1) // 2
        self.block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 3, padding=padding, dilation=dilation, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        return self.block(x)


# U-Net下采样块（Coarse/Refine网络编码器）
class DownSample(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 4, 2, 1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.LeakyReLU(0.2, inplace=True)
        )

    def forward(self, x):
        x = self.conv(x)
        return x


# U-Net上采样块（Coarse网络解码器）
class UpSample(nn.Module):
    def __init__(self, in_channels, out_channels, use_cbam=False):
        super().__init__()
        self.conv = nn.Sequential(
            nn.ConvTranspose2d(in_channels, out_channels, 4, 2, 1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
        self.cbam = CBAM(out_channels) if use_cbam else nn.modules.Identity()

    def forward(self, x):
        x = self.conv(x)
        x = self.cbam(x)
        return x


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
        self.down1 = DownSample(in_channels, 64)  # 1/2
        self.down2 = DownSample(64, 128)  # 1/4
        self.down3 = DownSample(128, 256)  # 1/8
        self.down4 = DownSample(256, 512)  # 1/16
        self.down5 = DownSample(512, 512)  # 1/32
        # 解码器：上采样
        self.up1 = UpSample(512, 512, use_cbam=True)  # 1/16
        self.up2 = UpSample(1024, 256, use_cbam=True)  # 1/8
        self.up3 = UpSample(512, 128, use_cbam=True)  # 1/4 → Ic4
        self.up4 = UpSample(256, 64, use_cbam=True)  # 1/2 → Ic2
        self.up5 = UpSample(128, 64, use_cbam=True)  # 1/1 → Ic1
        # 输出层：Ms(笔画掩码), Mb(文本块掩码), 多尺度Ic
        self.up1_seg = UpSample(512, 512, use_cbam=True)
        self.up2_seg = UpSample(1024, 256, use_cbam=True)
        self.up3_seg = UpSample(512, 128, use_cbam=True)
        self.up4_seg = UpSample(256, 64, use_cbam=True)
        self.up5_seg = UpSample(128, 64, use_cbam=True)

        self.out_ms = nn.Conv2d(64, 1, 3, 1, 1, bias=True)
        self.out_mb = nn.Conv2d(64, 1, 3, 1, 1, bias=True)
        self.out_ic4 = nn.Conv2d(128, 3, 3, 1, 1, bias=False)
        self.out_ic2 = nn.Conv2d(64, 3, 3, 1, 1, bias=False)
        self.out_ic1 = nn.Conv2d(64, 3, 3, 1, 1, bias=False)

    def forward(self, x):
        # 编码器（下采样）
        d1 = self.down1(x)  # H/2
        d2 = self.down2(d1)  # H/4
        d3 = self.down3(d2)  # H/8
        d4 = self.down4(d3)  # H/16
        d5 = self.down5(d4)  # H/32

        # 解码器（上采样 + 跳跃连接）
        u1 = self.up1(d5)
        u1 = torch.cat([u1, d4], dim=1)  # 拼接H/16特征

        u2 = self.up2(u1)
        u2 = torch.cat([u2, d3], dim=1)  # 拼接H/8特征

        u3 = self.up3(u2)  # H/4 → 输出 Ic4
        Ic4 = torch.tanh(self.out_ic4(u3))
        u3 = torch.cat([u3, d2], dim=1)  # 拼接H/4特征

        u4 = self.up4(u3)  # H/2 → 输出 Ic2
        Ic2 = torch.tanh(self.out_ic2(u4))
        u4 = torch.cat([u4, d1], dim=1)  # 拼接H/2特征

        u5 = self.up5(u4)  # H → 输出 Ic1, Mb, Ms
        Ic1 = torch.tanh(self.out_ic1(u5))

        u1_seg = self.up1_seg(d5)
        u1_seg = torch.cat([u1_seg, d4], dim=1)
        u2_seg = self.up2_seg(u1_seg)
        u2_seg = torch.cat([u2_seg, d3], dim=1)
        u3_seg = self.up3_seg(u2_seg)
        u3_seg = torch.cat([u3_seg, d2], dim=1)
        u4_seg = self.up4_seg(u3_seg)
        u4_seg = torch.cat([u4_seg, d1], dim=1)
        u5_seg = self.up5_seg(u4_seg)
        Mb = torch.sigmoid(self.out_mb(u5_seg))
        Ms = torch.sigmoid(self.out_ms(u5_seg))

        return Ms, Mb, Ic4, Ic2, Ic1


# Refine网络
class RefineNet(nn.Module):
    def __init__(self, in_channels=7):  # 3(Iin)+1(Ms)+3(Ic1) =7
        super().__init__()
        # 编码器：下采样
        self.down1 = DownSample(in_channels, 64)  # 1/2
        self.down2 = DownSample(64, 128)  # 1/4
        self.down3 = DownSample(128, 256)  # 1/8
        self.down4 = DownSample(256, 512)  # 1/16
        # 解码器：带空洞卷积的上采样
        self.up1 = DilatedUpSample(512, 256)  # 1/8
        self.up2 = DilatedUpSample(512, 128)  # 1/4
        self.up3 = DilatedUpSample(256, 64)  # 1/2
        self.up4 = DilatedUpSample(128, 64)  # 1/1
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
        u1 = torch.cat([u1, d3], dim=1)

        u2 = self.up2(u1)
        u2 = torch.cat([u2, d2], dim=1)

        u3 = self.up3(u2)
        u3 = torch.cat([u3, d1], dim=1)

        u4 = self.up4(u3)
        # 输出
        Ire = torch.tanh(self.out_ire(u4))
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
        # 全局判别器：输出标量（适配任意尺寸）
        self.global_disc = nn.Sequential(
            DiscBlock(in_channels, 64),
            DiscBlock(64, 128),
            DiscBlock(128, 256),
            DiscBlock(256, 512),
            nn.Conv2d(512, 1, 4, 1, 0, bias=False)  # [B,1,1,1]
        )
        # 局部判别器：输出特征图（用于掩码加权）
        self.local_disc = nn.Sequential(
            DiscBlock(in_channels, 64),
            DiscBlock(64, 128),
            DiscBlock(128, 256),
            DiscBlock(256, 512),
            nn.Conv2d(512, 1, 1, 1, 0, bias=False)  # [B,1,H',W']
        )

    def forward(self, x, local_mask=None):
        """
        :param x: [B,3,H,W] 归一化到[-1,1]的图像
        :param local_mask: [B,1,H,W] 真实文本掩码（训练时必需）
        :return:
            global_score: [B,1,1,1] 全局判别logits
            local_score: [B,1,H',W'] 掩码加权后的局部判别logits
        """
        global_score = self.global_disc(x)
        local_score = 0

        if local_mask is not None:
            # 1. 计算局部判别特征图
            local_feat = self.local_disc(x)  # [B,1,H',W']
            # 2. 将local_mask下采样到local_feat的尺寸
            _, _, h_feat, w_feat = local_feat.shape
            local_mask_scaled = F.interpolate(local_mask, size=(h_feat, w_feat), mode='nearest')
            # 3. 关键修复：用掩码加权局部特征（仅关注文本区域）
            local_score = local_feat * local_mask_scaled

        return global_score, local_score


# 加载预训练VGG16（用于感知/风格损失）
class VGG16Feature(nn.Module):
    def __init__(self):
        super().__init__()
        vgg = vgg16(pretrained=True).features
        self.feat1 = nn.Sequential(*vgg[:5])  # 第1个池化层前
        self.feat2 = nn.Sequential(*vgg[5:10])  # 第2个池化层前
        self.feat3 = nn.Sequential(*vgg[10:17])  # 第3个池化层前
        # 冻结参数
        for param in self.parameters():
            param.requires_grad = False

            # 【关键修正】ImageNet归一化参数
        # self.mean = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1).cuda()
        # self.std = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1).cuda()
        self.register_buffer('mean', torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1))
        self.register_buffer('std', torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1))

    def forward(self, x):
        # x: [B,3,H,W] 归一化到ImageNet标准
        # x: [-1,1] → [0,1] → ImageNet归一化
        x = (x + 1) / 2.0  # [-1,1] → [0,1]
        x = F.interpolate(x, size=(224, 224), mode='bilinear', align_corners=False)
        x = (x - self.mean) / self.std
        f1 = self.feat1(x)
        f2 = self.feat2(f1)
        f3 = self.feat3(f2)
        return [f1, f2, f3]


# Gram矩阵计算
def gram_matrix(x):
    b, c, h, w = x.shape
    x = x.view(b, c, h * w)
    return torch.bmm(x, x.transpose(1, 2)) / (c * h * w)


# 全量Loss计算类
class EnsExamLoss(nn.Module):
    def __init__(self):
        super().__init__()
        self.vgg_feat = VGG16Feature()
        # LR Loss权重：Ic4, Ic2, Ic1, Ire
        self.lambda_n = [5, 6, 8, 10]  # 原[5,6,8,10] → 缩小10倍
        self.beta_n = [0.8, 0.8, 0.8, 2]  # 原[0.8,0.8,0.8,2] → 缩小10倍
        # 总损失权重
        self.lambda_lr = 1.0
        self.lambda_p = 0.05  # 感知损失权重降低（原0.05）
        self.lambda_style = 120  # 风格损失权重降低（原120）
        self.lambda_sn = 1  # SN损失权重降低（原1.0）
        self.lambda_b = 0.4  # Block损失权重降低（原0.4）

    def sn_loss(self, Ms, Ms_gt):
        """SN损失"""
        l1_sum = torch.sum(torch.abs(Ms - Ms_gt), dim=[1, 2, 3])
        # 这里的归一化是为了解决笔迹稀疏问题
        normalization = torch.min(torch.sum(Ms, dim=[1, 2, 3]), torch.sum(Ms_gt, dim=[1, 2, 3]))
        return (l1_sum / (normalization + 1e-6)).mean()

    def block_loss(self, Mb, Mb_gt):
        # 逐样本计算
        intersection = (Mb * Mb_gt).sum(dim=[1, 2, 3])  # [B]
        mb_sq = (Mb ** 2).sum(dim=[1, 2, 3])  # [B]
        mbgt_sq = (Mb_gt ** 2).sum(dim=[1, 2, 3])  # [B]

        dice = (2 * intersection) / (mb_sq + mbgt_sq + 1e-8)  # [B]
        return (1 - dice).mean()  # 平均所有样本

    def lr_loss(self, Iouts, Igt_list, Mb_gt):
        """LR损失（修复多尺度掩码维度匹配问题）"""
        lr_loss = 0.0
        for i, (Iout, Igt) in enumerate(zip(Iouts, Igt_list)):
            # 关键修复：将Mb_gt下采样到当前Iout/Igt的尺度
            # 获取当前Iout的高/宽
            _, _, h, w = Iout.shape
            # 下采样Mb_gt到(h, w)，保持通道数不变
            Mb_gt_scaled = F.interpolate(Mb_gt, size=(h, w), mode='nearest')

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
                per_loss += F.l1_loss(f1, f2, reduction='mean')
        return per_loss

    def style_loss(self, I_list, Igt):
        style_loss = 0.0
        gt_feats = self.vgg_feat(Igt)
        for I in I_list:
            I_feats = self.vgg_feat(I)
            for f1, f2 in zip(I_feats, gt_feats):
                b, c, h, w = f1.shape
                gram1 = gram_matrix(f1)  # [B, C, C]
                gram2 = gram_matrix(f2)  # [B, C, C]
                # 关键：除以 H*W*C 归一化
                norm = h * w * c
                style_loss += F.l1_loss(gram1, gram2, reduction='mean') / norm
        return style_loss

    # 判别器损失（训练D时用）
    @staticmethod
    def hinge_loss_D(real_score, fake_score):
        loss_real = torch.mean(F.relu(1.0 - real_score))
        loss_fake = torch.mean(F.relu(1.0 + fake_score))
        return loss_real + loss_fake

    # 生成器损失（训练G时用）
    @staticmethod
    def hinge_loss_G(fake_score):
        return -torch.mean(F.relu(1.0 + fake_score))  # 注意：ReLU(1+score)

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

        L_adv_global = self.hinge_loss_G(global_score)
        L_adv_local = self.hinge_loss_G(local_score)
        L_adv = (L_adv_global + L_adv_local) / 2

        # 总损失
        L_total = L_adv + L_lr + L_per + L_style + L_sn + L_block
        return L_total, [L_adv, L_lr, L_per, L_style, L_sn, L_block]