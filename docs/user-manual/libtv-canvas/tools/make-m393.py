#!/usr/bin/env python3
# 合成 Batch FX 的成品图：
#   M-393  小地图面板（Batch FX-1 实拍 fx1-2-小地图特写.png）
#
# ⭐ 这张图坐实两件事：
#   ① 小地图在**左下角**（x=145），浮在左下工具条**正上方** ——
#      而它的 class 叫 `bottom right`，手册因此写错过一次「右下角」
#   ② 面板里那 12 个灰块就是画布上的 12 个节点（`rect.react-flow__minimap-node`）
#
# ⚠️ 排版规则（FO 定的）：图上只放圈号，说明写在空白处。
# ⚠️ ⛔⛔ **图例一律 ASCII** —— PIL 默认字体无 CJK 字形。
#    中文放 Markdown 的 alt 和正文。
# ⚠️ 证据图是**裁剪后**的 ⇒ 圈号坐标必须减掉 clip 起点再乘 K=2（Batch FW §153.2 踩过）。
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
E = os.path.join(HERE, '.evidence')
SH = os.path.abspath(os.path.join(HERE, '..', 'screenshots'))

蓝 = (150, 165, 255)
橙 = (255, 190, 90)
绿 = (180, 255, 140)
K = 2


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


def 圈(d, x, y, 序, 色, r=20):
    d.ellipse([x - r, y - r, x + r, y + r], outline=色, width=4)
    t = str(序)
    bb = d.textbbox((0, 0), t, font=F20)
    d.text((x - (bb[2] - bb[0]) / 2, y - (bb[3] - bb[1]) / 2 - 4), t, font=F20, fill=色)


def main():
    src = os.path.join(E, 'fx1-2-小地图特写.png')
    im = Image.open(src).convert('RGB')
    图例 = [
        '1 minimap panel  150x110  (bottom-LEFT, not bottom-right)',
        '2 12 grey blocks = 12 nodes  (rect.react-flow__minimap-node, 16x16 each)',
        '3 the button row below it  [organize][minimap][links][snap]48%',
        '4 a node card behind, partly covered by the panel',
    ]
    边 = 16
    圈带 = 12
    例行高 = 26
    W = max(im.width, 640)
    H = 边 * 2 + 圈带 + im.height + 14 + 例行高 * len(图例)
    out = Image.new('RGB', (W, H), (18, 18, 20))
    d = ImageDraw.Draw(out)
    out.paste(im, (边, 边 + 圈带))
    y = 边 + 圈带 + im.height + 14
    for 行 in 图例:
        d.text((边 + 6, y), 行, font=F18, fill=(210, 210, 215))
        y += 例行高

    # ⭐ 圈号坐标：证据图 fx1-2 的 clip 是
    #    x = 145-30 = 115, y = 647-30 = 617, w = 150+60 = 210, h = 110+60 = 170
    CLIP_X, CLIP_Y = 115, 617
    # ⭐ 圈号要落在**图内**的真实目标上，不能停在图例带里 ——
    #    第一版把 ①③ 放在圈号带上，四个圈挤在左上角，读者对不上号。
    图y = 边 + 圈带                       # 图内坐标 y=0
    # ① 面板本体左上角：面板框 [145,647,150,110] ⇒ 图内 (30,30)
    圈(d, 边 + (145 - CLIP_X) * K, 图y + (647 - CLIP_Y) * K, 1, 蓝, r=18)
    # ② 面板里的灰块群（面板中部偏左）
    圈(d, 边 + (200 - CLIP_X) * K, 图y + (702 - CLIP_Y) * K, 2, 橙, r=18)
    # ③ 底部按钮行里被高亮的那枚小地图按钮（截图里深色圆底那一枚）
    圈(d, 边 + (188 - CLIP_X) * K, 图y + (778 - CLIP_Y) * K, 3, 绿, r=18)
    # ④ 面板右侧被它盖住的节点卡边缘
    圈(d, 边 + (300 - CLIP_X) * K, 图y + (690 - CLIP_Y) * K, 4, (215, 175, 255), r=18)

    p = os.path.join(SH, 'M-393-小地图面板-十二个节点缩略.png')
    out.save(p)
    print('写出', p, out.size)


if __name__ == '__main__':
    main()
