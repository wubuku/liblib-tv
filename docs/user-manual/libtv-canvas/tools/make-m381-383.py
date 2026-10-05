#!/usr/bin/env python3
# 合成 Batch FO 的三张图：
#   M-381  「生成历史」面板全景（空态）—— 手册此前**一张都没有**
#   M-382  「所有评级」下拉的六档
#   M-383  「批量操作」展开出来的底部操作条
#
# 证据图（本轮实拍，@2x）：
#   fo1-01-生成历史-空态.png   → M-381
#   fo1-04-所有评级-六档.png    → M-382
#   fo3-02-批量操作-操作条.png  → M-383
#
# ⚠️ 证据图 @2x ⇒ 裁剪坐标乘 K（K = 图宽 / 视口宽 = 2880/1440 = 2.0）。
# ⚠️ 标注直接量在「裁剪+缩放后的画布」坐标系上，不做二次换算。
# ⚠️ PIL 默认字体无 CJK 字形 ⇒ 图上一律 ASCII，中文放 Markdown 的 alt。
# ⭐ 排版规则（沿用 FN 的修正）：**图上只放圈号，说明写在空白处的图例里**。
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
E = os.path.join(HERE, '.evidence')
SH = os.path.abspath(os.path.join(HERE, '..', 'screenshots'))

橙 = (255, 190, 90)
绿 = (180, 255, 140)
蓝 = (150, 165, 255)
红 = (255, 130, 130)


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
    if 缩放 != 1.0:
        px = px.resize((int(px.width * 缩放), int(px.height * 缩放)), Image.LANCZOS)
    return px


# ── M-381 面板全景 ──────────────────────────────────────────────────
# 面板壳实测 [73,158,1294,571]；只裁到 y=628，把标题栏 + 筛选栏 + 空态都收进来
OX, OY, SC = 63, 100, 0.80
im = 裁('fo1-01-生成历史-空态.png', (OX, OY, 1314, 528), 缩放=SC)
d = ImageDraw.Draw(im)


def P1(x, y):   # CSS → 本图坐标（⛔ 别忘了 K=2，v1 就是漏了它，四个框全画歪）
    return (int((x - OX) * 2 * SC), int((y - OY) * 2 * SC))


# ① 标题栏右侧：密度滑块 + ×
d.rounded_rectangle([*P1(1150, 100), *P1(1215, 130)], outline=橙, width=3)
圈(d, *P1(1150, 100), 1, 橙)
# ② 两个画布范围页签
d.rounded_rectangle([*P1(95, 168), *P1(250, 208)], outline=绿, width=3)
圈(d, *P1(95, 168), 2, 绿)
# ③ 三个类型 + 计数
d.rounded_rectangle([*P1(282, 168), *P1(466, 208)], outline=蓝, width=3)
圈(d, *P1(282, 168), 3, 蓝)
# ④ 右侧三枚：评级 / 排序 / 批量
d.rounded_rectangle([*P1(1045, 168), *P1(1348, 208)], outline=橙, width=3)
圈(d, *P1(1045, 168), 4, 橙)
图例(d, *P1(120, 540), 1, 'density slider (0-4, default 2) + close', 橙)
图例(d, *P1(120, 580), 2, 'all canvases / this canvas', 绿)
图例(d, *P1(120, 620), 3, 'image / video / audio + counts', 蓝)
图例(d, *P1(760, 540), 4, 'rating / sort / batch ops', 橙)
im.save(os.path.join(SH, 'M-381-生成历史-面板全景.png'))

# ── M-382 评级下拉六档 ──────────────────────────────────────────────
# 下拉实测 [935,208,200,230]；按钮 [1049,172,86,32]。图例统一挂在下方追加的一条深色带里。
def 做(证据, 裁框, 缩放, 框列, 图例列, 出图):
    im = 裁(证据, 裁框, 缩放=缩放)
    d = ImageDraw.Draw(im)
    ox, oy = 裁框[0], 裁框[1]
    k = 2 * 缩放            # ⭐ CSS 像素 → 证据图像素（K=2）再乘缩放
    def Q(x, y):
        return (int((x - ox) * k), int((y - oy) * k))
    for 序, (x, y, w, h), 色 in 框列:
        a, b = Q(x, y), Q(x + w, y + h)
        d.rounded_rectangle([a[0], a[1], b[0], b[1]], outline=色, width=3)
        圈(d, a[0], a[1], 序, 色)
    带 = 34 + 32 * len(图例列)
    out = Image.new('RGB', (im.width, im.height + 带), (8, 8, 8))
    out.paste(im, (0, 0))
    d2 = ImageDraw.Draw(out)
    for i, (序, 文, 色) in enumerate(图例列):
        图例(d2, 16, im.height + 30 + i * 32, 序, 文, 色)
    out.save(os.path.join(SH, 出图))
    return out.size


做('fo1-04-所有评级-六档.png', (920, 160, 250, 292), 1.0,
   [(1, (1049, 172, 86, 32), 橙), (2, (935, 208, 200, 230), 绿)],
   [(1, 'button: All ratings (the current one has a tick)', 橙),
    (2, 'dropdown: 6 rows - All, 1, 2, 3, 4, 5', 绿),
    (3, 'each row shows ONE orange star icon + a number, no text', 蓝)],
   'M-382-所有评级-六档下拉.png')

# ── M-383 批量操作的操作条 ──────────────────────────────────────────
# 操作条实测：已选择 0 项 @x≈101；五枚按钮都在 y=669、高 36
做('fo3-02-批量操作-操作条.png', (90, 648, 1270, 66), 0.6,
   [(1, (839, 669, 80, 36), 红),
    (2, (927, 669, 80, 36), 绿), (2, (1015, 669, 80, 36), 绿), (2, (1103, 669, 117, 36), 绿),
    (3, (1228, 669, 115, 36), 蓝),
    (4, (99, 678, 110, 18), 橙)],
   [(1, 'delete - red text rgb(231,76,60), the only dangerous one', 红),
    (2, 'download / rate / save-to-assets - all 36px tall, same row', 绿),
    (3, 'add to canvas - primary button, white bg + black text', 蓝),
    (4, 'left side: how many you picked (0 here, nothing to act on)', 橙)],
   'M-383-批量操作-底部操作条.png')

for f in ('M-381-生成历史-面板全景.png', 'M-382-所有评级-六档下拉.png', 'M-383-批量操作-底部操作条.png'):
    print(f, Image.open(os.path.join(SH, f)).size)
