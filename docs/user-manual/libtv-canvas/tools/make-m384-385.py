#!/usr/bin/env python3
# 合成 Batch FP 的两张图：
#   M-384  图片节点的参数条：六枚控件逐个对上名字（含悬停才读得到的那几枚）
#   M-385  「预设」面板：15 张卡、两栏四组，全灰态
#
# 证据图（本轮实拍，@2x）：
#   fp2-01-参数条全貌.png  → M-384
#   fp2-02-预设面板.png    → M-385
#
# ⚠️ 证据图 @2x ⇒ 裁剪坐标乘 K（K = 图宽 / 视口宽 = 2880/1440 = 2.0）。
# ⚠️ 标注直接量在「裁剪+缩放后的画布」坐标系上，不做二次换算。
# ⚠️ PIL 默认字体无 CJK 字形 ⇒ 图上一律 ASCII，中文放 Markdown 的 alt。
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
E = os.path.join(HERE, '.evidence')
SH = os.path.abspath(os.path.join(HERE, '..', 'screenshots'))

橙 = (255, 190, 90)
绿 = (180, 255, 140)
蓝 = (150, 165, 255)
红 = (255, 130, 130)
紫 = (215, 175, 255)


def 字体(sz):
    for p in ('/System/Library/Fonts/Supplemental/Arial Bold.ttf',
              '/System/Library/Fonts/Supplemental/Arial.ttf'):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


F13, F12 = 字体(13), 字体(11)


def 圈(d, x, y, 序, 色):
    d.ellipse([x - 11, y - 11, x + 11, y + 11], fill=色, outline=(12, 12, 12), width=2)
    d.text((x - 4, y - 8), str(序), font=F12, fill=(12, 12, 12))


def 图例(d, x, y, 序, 文, 色):
    圈(d, x, y - 5, 序, 色)
    d.text((x + 18, y - 12), 文, font=F13, fill=(228, 228, 228))


def 裁(名, 框_css, 缩放=1.0):
    im = Image.open(os.path.join(E, 名)).convert('RGB')
    K = im.width / 1440.0
    x, y, w, h = 框_css
    px = im.crop((int(x * K), int(y * K), int((x + w) * K), int((y + h) * K)))
    return px.resize((int(px.width * 缩放), int(px.height * 缩放)), Image.LANCZOS)


# ── M-384 参数条 ────────────────────────────────────────────────────
OX, OY, SC = 0, 612, 1.45
im = 裁('fp2-01-参数条全貌.png', (OX, OY, 780, 104), 缩放=SC)
d = ImageDraw.Draw(im)


def Q(x, y):
    return (int((x - OX) * 2 * SC), int((y - OY) * 2 * SC))


# 实测框：模型 [63,657] / 规格 [63? 用 16:9 那枚] / 预设 273 / 309 / 384 / 424 / 504 / ⬆
for 序, (x, y, w, h), 色 in [
    (1, (273, 657, 32, 32), 橙),
    (2, (309, 657, 32, 32), 紫),
    (3, (384, 657, 32, 32), 绿),
    (4, (424, 657, 32, 32), 红),
    (5, (504, 657, 32, 32), 蓝),
]:
    a, b = Q(x, y), Q(x + w, y + h)
    d.rounded_rectangle([a[0], a[1], b[0], b[1]], outline=色, width=3)
    圈(d, a[0], a[1], 序, 色)
带 = 34 + 30 * 5
out = Image.new('RGB', (im.width, im.height + 带), (8, 8, 8))
out.paste(im, (0, 0))
d2 = ImageDraw.Draw(out)
for i, (序, 文, 色) in enumerate([
    (1, 'presets  (also the entry to the 15-card panel)', 橙),
    (2, 'hover says: "Panavision DXL2 off / Arri Signature Prime"', 紫),
    (3, 'translate prompt  (the 文A icon)', 绿),
    (4, 'NO tooltip at all - three reads, same result', 红),
    (5, 'generate  (says why it is disabled: no prompt / no ref)', 蓝),
]):
    图例(d2, 16, im.height + 30 + i * 30, 序, 文, 色)
out.save(os.path.join(SH, 'M-384-图片节点-参数条六枚控件.png'))

# ── M-385 预设面板 ──────────────────────────────────────────────────
OX2, OY2, SC2 = 265, 101, 1.10
im2 = 裁('fp2-02-预设面板.png', (OX2, OY2, 530, 556), 缩放=SC2)
d = ImageDraw.Draw(im2)


def Q2(x, y):
    return (int((x - OX2) * 2 * SC2), int((y - OY2) * 2 * SC2))


# 四个分组标题（实测 y：分镜叙事≈137 / 空间与机位≈137 / 设定图≈290 / 质感调节≈514）
for 序, (x, y, w, h), 色 in [
    (1, (282, 124, 90, 20), 橙),
    (2, (528, 124, 100, 20), 绿),
    (3, (528, 277, 70, 20), 蓝),
    (4, (282, 501, 90, 20), 紫),
]:
    a, b = Q2(x, y), Q2(x + w, y + h)
    d.rounded_rectangle([a[0], a[1], b[0], b[1]], outline=色, width=3)
    圈(d, a[0], a[1], 序, 色)
# 三枚带蓝点的卡
for 序, (x, y, w, h) in [(5, (282, 155, 238, 52)), (5, (282, 211, 238, 52)), (5, (282, 532, 238, 52))]:
    a, b = Q2(x, y), Q2(x + w, y + h)
    d.rounded_rectangle([a[0], a[1], b[0], b[1]], outline=橙, width=3)
圈(d, *Q2(521, 155), 5, 橙)
带2 = 40 + 30 * 5 + 26
out2 = Image.new('RGB', (im2.width, im2.height + 带2), (8, 8, 8))
out2.paste(im2, (0, 0))
d3 = ImageDraw.Draw(out2)
for i, (序, 文, 色) in enumerate([
    (1, 'group: storyboarding  (6 cards)', 橙),
    (2, 'group: space & camera  (2 cards)', 绿),
    (3, 'group: spec sheets  (5 cards)', 蓝),
    (4, 'group: texture  (2 cards)', 紫),
    (5, 'these 3 carry a 6x6 cyan dot - meaning unverified', 橙),
]):
    图例(d3, 16, im2.height + 30 + i * 30, 序, 文, 色)
d3.text((16, im2.height + 30 + 5 * 30 + 4),
        'ALL 15 cards: opacity 0.45 + cursor:not-allowed  (this node has no picture yet)',
        font=F13, fill=(255, 140, 140))
out2.save(os.path.join(SH, 'M-385-预设面板-十五张卡全灰态.png'))

for f in ('M-384-图片节点-参数条六枚控件.png', 'M-385-预设面板-十五张卡全灰态.png'):
    print(f, Image.open(os.path.join(SH, f)).size)
