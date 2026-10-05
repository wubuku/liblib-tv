#!/usr/bin/env python3
# 合成 Batch FW 的两张图：
#   M-391  底部中央七枚工具按钮
#   M-392  左下角六枚（含「资产管理」文字按钮与「48%」缩放）
#
# 证据图（本轮实拍）：
#   fw1-0-底部中央七枚.png   clip x=566 y=743 w=309 h=60  （@2x ⇒ 618×120）
#   fw1-1-左下角五枚.png     clip x=0   y=750 w=290 h=56  （@2x ⇒ 580×112）
#
# ⭐ 本图坐实的最重要一条：**底部中央第二枚的 aria 叫「移动」，
#    而左下角第二枚的 aria 叫「整理画布，Option+Shift+F」——
#    同一个功能、两个入口、两个天差地别的名字。**
#
# ⚠️ 排版规则（FO 定的）：图上只放圈号，说明写在空白处。
# ⚠️ ⛔⛔ **图例一律 ASCII** —— PIL 默认字体无 CJK 字形，中文会变 □□□。
#    中文放 Markdown 的 alt 和正文。
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
E = os.path.join(HERE, '.evidence')
SH = os.path.abspath(os.path.join(HERE, '..', 'screenshots'))

蓝 = (150, 165, 255)
橙 = (255, 190, 90)
绿 = (180, 255, 140)
红 = (255, 130, 130)
K = 2  # 证据图 @2x


def 字体(sz):
    for p in ('/System/Library/Fonts/Supplemental/Arial Bold.ttf',
              '/System/Library/Fonts/Supplemental/Arial.ttf'):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


F20, F18 = 字体(20), 字体(18)


def 圈(d, x, y, 序, 色, r=24):
    """画一个圈号。图上只放圈号，说明放图例。"""
    d.ellipse([x - r, y - r, x + r, y + r], outline=色, width=4)
    t = str(序)
    bb = d.textbbox((0, 0), t, font=F20)
    d.text((x - (bb[2] - bb[0]) / 2, y - (bb[3] - bb[1]) / 2 - 4), t, font=F20, fill=色)


def 底部中央():
    src = os.path.join(E, 'fw1-0-底部中央七枚.png')
    im = Image.open(src).convert('RGB')
    # 图例区（ASCII）
    图例 = [
        '1 add node        5 history',
        '2 move (=TIDY!)   6 shortcuts',
        '3 material lib    7 help',
        '4 character studio',
    ]
    边 = 16
    例行高 = 26
    圈带 = 52                      # ⭐ 证据图裁得紧，圈号画在自己的带子上
    W = max(im.width, 560)
    H = 边 * 2 + 圈带 + im.height + 14 + 例行高 * len(图例)
    out = Image.new('RGB', (W, H), (18, 18, 20))
    圈y = 边 + 圈带 // 2
    d = ImageDraw.Draw(out)
    out.paste(im, (边, 边 + 圈带))
    y = 边 + 圈带 + im.height + 14
    for 行 in 图例:
        d.text((边 + 6, y), 行, font=F18, fill=(210, 210, 215))
        y += 例行高
    # ⭐ 圈号坐标必须**减掉 clip 起点**（clip x=566），
    #    否则圈号会整体右移 566×2 像素、落到画面外 —— 这正是第一版没画出来的原因。
    # ⭐ 直接用 batchFW1.json 里的**实测 x**，不要用「起点 + 步进」的公式 ——
    #    第 5→6 枚之间夹着一条竖分隔线，步进是 49 而不是 40（第一版就栽在这）。
    CLIP_X = 566
    实测X = [580, 620, 660, 700, 740, 789, 829]     # ← 逐枚量出来的
    序 = [蓝, 红, 蓝, 绿, 绿, 蓝, (215, 175, 255)]
    for i, x in enumerate(实测X):
        圈(d, 边 + (x + 16 - CLIP_X) * K, 圈y, i + 1, 序[i], r=20)
    p = os.path.join(SH, 'M-391-底部中央七枚工具按钮.png')
    out.save(p)
    print('写出', p, out.size)


def 紫():
    return (215, 175, 255)


def 左下角():
    src = os.path.join(E, 'fw1-1-左下角五枚.png')
    im = Image.open(src).convert('RGB')
    图例 = [
        '1 asset manager (text button, 94x28)',
        '2 tidy canvas  Option+Shift+F',
        '3 minimap      aria says "switch", tip says "canvas minimap"',
        '4 hide links',
        '5 grid snap',
        '6 zoom 48%',
    ]
    边 = 16
    例行高 = 26
    圈带 = 52
    W = max(im.width, 700)
    H = 边 * 2 + 圈带 + im.height + 14 + 例行高 * len(图例)
    out = Image.new('RGB', (W, H), (18, 18, 20))
    圈y = 边 + 圈带 // 2
    d = ImageDraw.Draw(out)
    out.paste(im, (边, 边 + 圈带))
    y = 边 + 圈带 + im.height + 14
    for 行 in 图例:
        d.text((边 + 6, y), 行, font=F18, fill=(210, 210, 215))
        y += 例行高
    序 = [蓝, 橙, 绿, 绿, 蓝, (215, 175, 255)]
    # 左下角的 clip x=0 ⇒ 不用减；六枚的中心 x 分别是
    中心 = [14 + 47, 112 + 14, 144 + 14, 176 + 14, 208 + 14, 240 + 18]
    for i, cx in enumerate(中心):
        圈(d, 边 + cx * K, 圈y, i + 1, 序[i], r=20)
    p = os.path.join(SH, 'M-392-左下角六枚工具按钮.png')
    out.save(p)
    print('写出', p, out.size)


if __name__ == '__main__':
    底部中央()
    左下角()
