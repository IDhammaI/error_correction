import torch
import torch.nn.functional as F
from torch import nn


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
