#!/usr/bin/env python3
# ⭐⭐⭐ 从**截图像素**里量点阵的周期 —— 一条完全不依赖 DOM 属性名的路。
#
# 为什么要有这条路：DOM 里 `<pattern width="16.0517">` 有两种读法
#   ① user space 是屏幕像素 ⇒ 画布步长 35
#   ② 已被 zoom 预乘       ⇒ 画布步长 16.05
# 同一组数字、相反的结论。**属性名裁不出这个，必须看像素。**
#
# 做法：把裁图转灰度，对每一行做自相关（autocorrelation）。
#   点阵是周期性的 ⇒ 自相关会在周期处出现峰值。
#   取 4~60 像素范围内**所有**峰，两两求最大公约数样式的基频，
#   报告每个候选周期及其强度，这样不会一上来就假定答案。
#
# 用法：python3 tools/grid-period.py <png> [zoom]
import sys
from PIL import Image
import numpy as np


def 列行自相关(灰, lo=10, hi=70):
    """对**列方向**和**行方向**各做一次归一化自相关，返回 [(方向, 峰列表)]。

    ⚠️ 判据踩过的坑（2026-10-05，EV-3）：
      ① 点阵是**亚像素淡点**（背景灰度 20，点只有 21~45），
         整图直接算自相关会得到「每个周期都是峰」的无用结果
         —— 因为右下角混进了 TV Director 面板的高对比内容。
         ⇒ **必须先裁掉非网格区域**，再**逐方向**算。
      ② 只报「自相关值」不够，必须**先减去中位数**再找**局部极大**，
         否则噪声也会被当成峰。
    """
    列 = 灰.mean(axis=0); 列 = 列 - 列.min()
    行 = 灰.mean(axis=1); 行 = 行 - 行.min()
    出 = []
    for 名, v in [('列方向', 列), ('行方向', 行)]:
        v = v - v.mean()
        var = float(v.var()) + 1e-9
        ac = np.array([float(np.dot(v[:-p], v[p:])) / (len(v) - p) / var for p in range(lo, hi + 1)])
        中位 = float(np.median(ac))
        峰 = []
        for i in range(1, len(ac) - 1):
            if ac[i] > ac[i - 1] and ac[i] >= ac[i + 1] and ac[i] > max(中位 * 1.5, 0.3):
                峰.append((i + lo, round(float(ac[i]), 4)))
        出.append((名, 峰, 中位))
    return 出


def 主():
    路径 = sys.argv[1]
    # 裁掉非网格区域。⚠️ 默认只取**左上角** 1000×600 图像像素：
    #    右下角那块会被 TV Director 面板盖住，左侧偶尔压到节点。
    裁x = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    裁y = int(sys.argv[3]) if len(sys.argv) > 3 else 600
    im = Image.open(路径).convert('L')
    a = np.asarray(im, dtype=np.float64)
    灰 = a[0:裁y, 0:裁x]
    print(f'{路径}  整图 {a.shape[1]}×{a.shape[0]}  裁用 {灰.shape[1]}×{灰.shape[0]}（图像像素）')
    print(f'  裁出区 min={灰.min():.0f} max={灰.max():.0f} mean={灰.mean():.2f} std={灰.std():.2f}')

    for 名, 峰, 中位 in 列行自相关(灰):
        print(f'\n  【{名}】自相关中位数={中位:.4f}')
        print('    峰(周期 图像px, 强度):', 峰)
        if 峰:
            基 = 峰[0][0]
            print(f'    ⇒ 基频 {基} 图像像素 = {基/2:.1f} CSS px（截图 @2x）')
            for zoom in (0.458621,):
                print(f'       ÷ zoom {zoom} = **{基/2/zoom:.2f} 画布单位**')


if __name__ == '__main__':
    主()
