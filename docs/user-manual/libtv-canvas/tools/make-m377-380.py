#!/usr/bin/env python3
# 合成 FN 批次的四张图：
#   M-377  官方角色库的完整真实界面（角色造型室第二个页签）
#   M-378  素材库浮层：副标题是「悬停才淡出来」的
#   M-379  添加节点面板里的「素材库 ›」只有两项，没有「打开工具箱」
#   M-380  卡上是**实心星**，「我的收藏」里却**空空如也** —— 两张拼在一起才说得清
#
# 证据图（本轮实拍，@2x）：
#   fn1-01-角色造型室-横滚后.png    → M-377
#   fn4-01-素材库-悬停出副标题.png   → M-378
#   fn4-04-添加节点里的素材库.png    → M-379
#   fn4-02-风格广场.png / fn4-03-风格广场-我的收藏.png → M-380
#
# ⚠️ 证据图 @2x ⇒ 裁剪坐标乘 K（K = 图宽 / 视口宽 = 2880/1440 = 2.0）。
# ⚠️ 标注一律直接量在「裁剪+缩放后的画布」坐标系上，不做二次换算。
# ⚠️ PIL 默认字体无 CJK 字形 ⇒ 图上一律 ASCII，中文放 Markdown 的 alt。
# ⭐ 排版规则：**图上只放圈号，文字说明放在空白处的图例里** ——
#   第一版把说明文字直接压在内容上，四个标注有两个糊住了关键信息，重做。
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
E = os.path.join(HERE, '.evidence')
SH = os.path.abspath(os.path.join(HERE, '..', 'screenshots'))

橙 = (255, 190, 90)
绿 = (180, 255, 140)
蓝 = (150, 165, 255)
红 = (255, 140, 140)


def 字体(sz, 粗=True):
    名单 = ['/System/Library/Fonts/Supplemental/Arial Bold.ttf',
            '/System/Library/Fonts/Supplemental/Arial.ttf'] if 粗 else \
           ['/System/Library/Fonts/Supplemental/Arial.ttf']
    for p in 名单:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


F13, F12 = 字体(13), 字体(11)


def 圈(d, x, y, 序, 色):
    """在图上打一个带序号的实心圆点。序是 ASCII 数字，避免字体缺字。"""
    d.ellipse([x - 11, y - 11, x + 11, y + 11], fill=色, outline=(12, 12, 12), width=2)
    t = str(序)
    d.text((x - 4, y - 8), t, font=F12, fill=(12, 12, 12))


def 图例(d, x, y, 行, 缩进=0):
    """在图上空白处写一行图例文字。"""
    xx = x + 缩进
    序, 文, 色 = 行
    圈(d, xx, y - 5, 序, 色)
    d.text((xx + 18, y - 12), 文, font=F13, fill=(228, 228, 228))


def 裁(名, 框_css, 缩放=1.0):
    im = Image.open(os.path.join(E, 名)).convert('RGB')
    K = im.width / 1440.0
    x, y, w, h = 框_css
    px = im.crop((int(x * K), int(y * K), int((x + w) * K), int((y + h) * K)))
    if 缩放 != 1.0:
        px = px.resize((int(px.width * 缩放), int(px.height * 缩放)), Image.LANCZOS)
    return px


# ── M-378 素材库浮层：副标题悬停才出现 ───────────────────────────────
# 裁剪往右多留 300 CSS px 的空画布，专门放图例
im = 裁('fn4-01-素材库-悬停出副标题.png', (532, 492, 452, 272))
d = ImageDraw.Draw(im)
d.rounded_rectangle([66, 150, 518, 238], outline=橙, width=3)
d.rounded_rectangle([160, 194, 302, 222], outline=橙, width=2)
d.rounded_rectangle([66, 262, 518, 352], outline=蓝, width=3)
圈(d, 66, 150, 1, 橙)
圈(d, 302, 194, 2, 橙)
圈(d, 66, 262, 3, 蓝)
图例(d, 552, 90, (1, 'row under the cursor', 橙))
图例(d, 552, 124, (2, 'subtitle fades in (0.2s)', 橙))
图例(d, 552, 158, (3, 'no subtitle until hover', 蓝))
im.save(os.path.join(SH, 'M-378-素材库浮层-悬停出副标题.png'))

# ── M-379 添加节点里的素材库：只有两项 ──────────────────────────────
# 只裁「素材库」那一行 + 它展开出来的子菜单
im = 裁('fn4-04-添加节点里的素材库.png', (468, 560, 486, 168))
d = ImageDraw.Draw(im)
d.rounded_rectangle([50, 66, 496, 142], outline=橙, width=3)
d.rounded_rectangle([462, 66, 918, 238], outline=红, width=3)
圈(d, 50, 66, 1, 橙)
圈(d, 918, 66, 2, 红)
图例(d, 478, 272, (1, 'clicked this row in the + menu', 橙))
图例(d, 478, 302, (2, 'submenu: 2 items, NO toolbox', 红))
im.save(os.path.join(SH, 'M-379-添加节点里的素材库-只有两项.png'))

# ── M-377 官方角色库完整界面 ────────────────────────────────────────
im = 裁('fn1-01-角色造型室-横滚后.png', (114, 24, 1214, 762), 缩放=0.5)
d = ImageDraw.Draw(im)
d.rounded_rectangle([138, 22, 232, 54], outline=橙, width=3)
d.rounded_rectangle([28, 70, 392, 110], outline=橙, width=3)
d.ellipse([1160, 366, 1186, 392], outline=绿, width=3)
d.rounded_rectangle([540, 618, 680, 652], outline=蓝, width=3)
圈(d, 138, 22, 1, 橙)
圈(d, 28, 70, 2, 橙)
圈(d, 1173, 379, 3, 绿)
圈(d, 540, 618, 4, 蓝)
图例(d, 24, 604, (1, '2nd tab: official library', 橙))
图例(d, 24, 636, (2, 'gender / age / culture + search', 橙))
图例(d, 24, 668, (3, '5 portraits, arrows to page', 绿))
图例(d, 24, 700, (4, 'current char name + sparkle', 蓝))
im.save(os.path.join(SH, 'M-377-官方角色库-完整界面.png'))

# ── M-380 实心星 vs 空收藏：上下两片拼起来 ───────────────────────────
上 = 裁('fn4-02-风格广场.png', (100, 74, 1240, 450), 缩放=0.62)
下 = 裁('fn4-03-风格广场-我的收藏.png', (100, 74, 1240, 450), 缩放=0.62)
im = Image.new('RGB', (上.width, 上.height + 下.height + 10), (10, 10, 10))
im.paste(上, (0, 0))
im.paste(下, (0, 上.height + 10))
d = ImageDraw.Draw(im)
圈(d, 394, 184, 1, 橙)
圈(d, 690, 上.height + 10 + 474, 2, 蓝)
图例(d, 620, 40, (1, 'plaza tab: this card shows a FILLED star', 橙))
图例(d, 620, 上.height + 130, (2, 'same account, Favorites tab: EMPTY', 蓝))
d.line([0, 上.height + 5, im.width, 上.height + 5], fill=(70, 70, 70), width=2)
im.save(os.path.join(SH, 'M-380-风格广场-我的收藏-暂无素材.png'))

for f in ('M-377-官方角色库-完整界面.png', 'M-378-素材库浮层-悬停出副标题.png',
          'M-379-添加节点里的素材库-只有两项.png', 'M-380-风格广场-我的收藏-暂无素材.png'):
    print(f, Image.open(os.path.join(SH, f)).size)
