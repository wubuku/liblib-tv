#!/usr/bin/env python3
# 合成 Batch GC 的成品图：
#   M-398  空画布正中央的「生成芯片」整排（证据 gc3，无遮挡）
#   M-399  ⭐ 第 5 枚被 TV Director 抽屉整片盖住（证据 gc1 + gc2 上下并排）
#   M-400  点「智能剪辑」芯片建出来的节点（证据 gc4）
#
# ⭐ 这批图坐实三件事：
#   ① 芯片是 **200×56 的卡片**（FZ 量到的 116×22 只是里面的文字），步进 208
#   ② ⭐⭐ 第 5 枚（智能剪辑）**被 TV Director 抽屉压住点不到** —— 真实可复现的界面冲突
#   ③ 点芯片 = 建一个对应类型的节点（本批：智能剪辑 → video-clip，零生成请求）
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

d_测 = ImageDraw.Draw(Image.new('RGB', (10, 10)))


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


def 底板(图们, 图例, 标题=None):
    """把若干张图横向排开，下方留出图例带。"""
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


def m398():
    im = Image.open(os.path.join(E, 'gc3-芯片排-无遮挡.png')).convert('RGB')
    图例 = [
        'five chips sit dead centre of an EMPTY canvas, each card 200 x 56,',
        'step 208 px between them. Left to right:',
        '1 image   2 video   3 audio   4 script   5 smart-clip',
        'They are the quickest way to drop the matching node on the canvas.',
    ]
    out, d = 底板([im], 图例)
    P = (16, 16 + 12)
    # CLIP = (180,330)，五枚芯片中心分别是页面 x = 304/512/720/928/1136，y = 437
    CX, CY = 180, 330
    for i, x in enumerate([304, 512, 720, 928, 1136], start=1):
        色 = (蓝, 橙, 绿, 粉, (200, 200, 210))[i - 1]
        圈(d, P[0] + (x - CX) * K, P[1] + (437 - CY) * K, i, 色)
    p = os.path.join(SH, 'M-398-空画布-中央生成芯片五连排.png')
    out.save(p)
    print('写出', p, out.size)


def m399():
    a = Image.open(os.path.join(E, 'gc1-芯片排与抽屉叠压.png')).convert('RGB')
    b = Image.open(os.path.join(E, 'gc2-第五枚被遮特写.png')).convert('RGB')
    图例 = [
        'The TV Director chat drawer opens on top of the chip row and',
        'swallows the 5th chip: the drawer starts at x=1025, that chip at',
        'x=1036, so 175 of its 200 px sit under the drawer and the click',
        'lands on the chat welcome text instead.',
        'Close the drawer and the very same chip becomes clickable again.',
        '=> Hit ESC (or the close button) before clicking the rightmost chip.',
        'Close-up: the drawer edge cuts the 5th card in half; only its',
        'left 25 px stay reachable, so most of the card is dead area.',
    ]
    out, d = 底板([a, b], 图例, 标题='the drawer is open (a full view)   /   close-up of the overlap (b)')
    P = (16, 16 + 12 + 24)
    左 = 16
    右 = 16 + a.width + 16
    # ① 抽屉左缘（页面 x=1025, y 取芯片行中部 437）
    圈(d, 左 + (1025 - 180) * K, P[1] + (437 - 330) * K, 1, 蓝)
    # ② 第 5 枚芯片被盖住的位置（页面 x=1136）
    圈(d, 左 + (1136 - 180) * K, P[1] + (437 - 330) * K, 2, 橙)
    # ③ 抽屉顶栏那枚关闭按钮
    圈(d, 左 + (1393 - 180) * K, P[1] + (179 - 330) * K, 3, 绿)
    # ④⑤ 特写图 gc2 的 clip = (960,380)；它紧贴在左图**下方**（底板对两张图是横向排的，
    #    这里特写图与全景图同高，只需各自在自己的行内定位）
    圈(d, 右 + (1030 - 960) * K, P[1] + (437 - 380) * K, 4, 粉)
    圈(d, 右 + (1140 - 960) * K, P[1] + (437 - 380) * K, 5, (215, 175, 255))
    p = os.path.join(SH, 'M-399-空画布-第五枚芯片被抽屉压住.png')
    out.save(p)
    print('写出', p, out.size)


def m400():
    im = Image.open(os.path.join(E, 'gc4-点芯片建出的智能剪辑节点.png')).convert('RGB')
    图例 = [
        'Clicking the 5th chip dropped exactly one node on the canvas,',
        'named "smart clip 1" (the number counts within this node type),',
        '350 x 350, still empty - it says "connect a video node to go on".',
        'No generation request was sent: a chip creates a node, it does',
        'not start any generation.',
    ]
    out, d = 底板([im], 图例)
    P = (16, 16 + 12)
    # gc4 的 clip 由脚本算出：node box [545,258,350,350]，外扩 40 ⇒ clip = (505,218)
    CX, CY = 505, 218
    圈(d, P[0] + (545 - CX) * K, P[1] + (272 - CY) * K, 1, 蓝)
    圈(d, P[0] + (720 - CX) * K, P[1] + (430 - CY) * K, 2, 橙)
    p = os.path.join(SH, 'M-400-空画布-点芯片建出智能剪辑节点.png')
    out.save(p)
    print('写出', p, out.size)


if __name__ == '__main__':
    m398()
    m399()
    m400()