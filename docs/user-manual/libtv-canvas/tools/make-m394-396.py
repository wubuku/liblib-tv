#!/usr/bin/env python3
# 合成 Batch GA 的成品图：
#   M-394  新建画布的「行内命名框」（证据 ga8-3-命名框.png）
#   M-395  画布下拉全貌 ↔ 悬停某行（证据 ga8-1 + ga8-2，左右并排）
#   M-396  列表里的自定义名与重名（证据 ga8-4-自定义名列表.png）
#
# ⭐ 这三张图各坐实一条手册此前没写（或写错）的机制：
#   M-394  点「+」不是弹浮层，而是**就地替换列表第一行**成一个行内输入框
#   M-395  「更多操作」不是悬停才出现 —— 它一直在 DOM 里，只是 opacity:0
#   M-396  画布名允许重名，且纯数字名不会被格式化成「画布 N」
#
# ⚠️ 排版规则（FO 定的）：图上只放圈号，说明写在空白处。
# ⚠️ ⛔⛔ **图例一律 ASCII** —— PIL 默认字体无 CJK 字形。中文放 Markdown。
# ⚠️ 证据图是**裁剪后**的 ⇒ 圈号坐标必须减掉 clip 起点再乘 K=2（Batch FW §153.2）。
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
E = os.path.join(HERE, '.evidence')
SH = os.path.abspath(os.path.join(HERE, '..', 'screenshots'))

蓝 = (150, 165, 255)
橙 = (255, 190, 90)
绿 = (180, 255, 140)
粉 = (255, 150, 190)
K = 2

# ⭐ 四张 ga8-* 证据图的 clip 起点（tools/ga8.mjs 的 CLIP）
CLIP_X, CLIP_Y = 150, 38

# 贴图时的左上角：底板() 里第一张图的 x 与 y
PAD_X, PAD_Y = 16, 16 + 12


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


def 圈(d, x, y, 序, 色, r=18):
    d.ellipse([x - r, y - r, x + r, y + r], outline=色, width=4)
    t = str(序)
    bb = d.textbbox((0, 0), t, font=F20)
    d.text((x - (bb[2] - bb[0]) / 2, y - (bb[3] - bb[1]) / 2 - 4), t, font=F20, fill=色)


d_测 = ImageDraw.Draw(Image.new('RGB', (10, 10)))


def 底板(图们, 图例, 标题=None):
    """把若干张图横向排开，下方留出图例带。返回 (画布, 贴图函数)。"""
    边, 圈带, 例行高 = 16, (24 if 标题 else 12), 26
    图宽 = sum(im.width for im in 图们) + 边 * (len(图们) + 1)
    例行宽 = 边 + 12 + max(int(d_测.textlength(行, font=F18)) for 行 in 图例)
    宽 = max(图宽, 例行宽)
    高 = 边 * 2 + 圈带 + max(im.height for im in 图们) + 14 + 例行高 * len(图例) + (24 if 标题 else 0)
    out = Image.new('RGB', (宽, 高), (18, 18, 20))
    d = ImageDraw.Draw(out)
    x = 边
    for im in 图们:
        out.paste(im, (x, 边 + 圈带 + (24 if 标题 else 0)))
        x += im.width + 边
    if 标题:
        d.text((边 + 4, 边 - 2), 标题, font=F20, fill=(230, 230, 235))
    y = 边 + 圈带 + (24 if 标题 else 0) + max(im.height for im in 图们) + 14
    for 行 in 图例:
        d.text((边 + 6, y), 行, font=F18, fill=(210, 210, 215))
        y += 例行高
    return out, d


def m394():
    im = Image.open(os.path.join(E, 'ga8-3-命名框.png')).convert('RGB')
    图例 = [
        '1  that row became an inline input - NO popup box at all',
        '2  the "+" button (aria = new canvas)',
        '3  the input: next number pre-filled, all text selected,',
    ]
    out, d = 底板([im], 图例)
    # ① 那一行（div.bg-canvas-controls-active 框 [174,91,196,28]）的左边缘
    圈(d, PAD_X + (167 - CLIP_X) * K, PAD_Y + (131 - CLIP_Y) * K, 1, 蓝)
    # ② 加号按钮 aria="新建画布" 框 [346,57,24,24] 的中心
    圈(d, PAD_X + (358 - CLIP_X) * K, PAD_Y + (69 - CLIP_Y) * K, 2, 橙)
    # ③ 输入框 [182,95,186,21] 的右端
    圈(d, PAD_X + (352 - CLIP_X) * K, PAD_Y + (105 - CLIP_Y) * K, 3, 绿)
    p = os.path.join(SH, 'M-394-新建画布-行内命名框.png')
    out.save(p)
    print('写出', p, out.size)


def m395():
    a = Image.open(os.path.join(E, 'ga8-1-面板全貌.png')).convert('RGB')
    b = Image.open(os.path.join(E, 'ga8-2-更多操作显现.png')).convert('RGB')
    图例 = [
        '1  the dropdown: fixed 214 x 274, only ~6 rows fit',
        '2  row 3, mouse elsewhere - nothing visible on its right',
        '3  row 3 after hover - exactly ONE button shows up,',
    ]
    out, d = 底板([a, b], 图例, 标题='left: just opened     right: mouse hovering row 3')
    图y = 16 + 12 + 24
    左 = 16
    右 = 16 + a.width + 16
    # ① 面板左上角 [165,46]
    圈(d, 左 + (167 - CLIP_X) * K, PAD_Y + (48 - CLIP_Y) * K, 1, 蓝)
    # ② 左图：第 3 行 mo 的位置（此刻是透明的，但**在 DOM 里**）
    圈(d, 左 + (356 - CLIP_X) * K, PAD_Y + (177 - CLIP_Y) * K, 2, 橙)
    # ③ 右图：同一位置，此刻可见
    圈(d, 右 + (356 - CLIP_X) * K, PAD_Y + (177 - CLIP_Y) * K, 3, 绿)
    p = os.path.join(SH, 'M-395-画布下拉-更多操作悬停才显现.png')
    out.save(p)
    print('写出', p, out.size)


def m396():
    im = Image.open(os.path.join(E, 'ga8-4-自定义名列表.png')).convert('RGB')
    图例 = [
        '1  a custom name, kept verbatim in the list',
        '2  a name typed as plain digits stays digits -',
        '3  a SECOND canvas with the SAME name is allowed',
    ]
    out, d = 底板([im], 图例)
    图y = 16 + 12
    圈(d, PAD_X + (200 - CLIP_X) * K, PAD_Y + (105 - CLIP_Y) * K, 1, 蓝)
    圈(d, PAD_X + (200 - CLIP_X) * K, PAD_Y + (141 - CLIP_Y) * K, 2, 橙)
    圈(d, PAD_X + (200 - CLIP_X) * K, PAD_Y + (177 - CLIP_Y) * K, 3, 绿)
    p = os.path.join(SH, 'M-396-画布名-自定义与重名.png')
    out.save(p)
    print('写出', p, out.size)


def m397():
    im = Image.open(os.path.join(E, 'ga9-确认框裁切.png')).convert('RGB')
    图例 = [
        '1  the confirm dialog: 344 x 132, centred on screen',
        '2  "Cancel" - 50 x 28',
        '3  "Confirm" - 50 x 28, immediately to its right',
    ]
    out, d = 底板([im], 图例)
    # ⭐ 这张证据图是**设备像素**（@2x），clip 起点 = (513, 304) 页面 px
    CX, CY = 513, 304
    P = (16, 16 + 12)
    圈(d, P[0] + (550 - CX) * K, P[1] + (345 - CY) * K, 1, 蓝)
    圈(d, P[0] + (792 - CX) * K, P[1] + (440 - CY) * K, 2, 橙)
    圈(d, P[0] + (850 - CX) * K, P[1] + (440 - CY) * K, 3, 绿)
    p = os.path.join(SH, 'M-397-删除画布-二次确认复核.png')
    out.save(p)
    print('写出', p, out.size)


if __name__ == '__main__':
    m394()
    m395()
    m396()
    m397()