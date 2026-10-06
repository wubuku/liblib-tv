#!/usr/bin/env python3
# 合成 Batch GF 的成品图：
#   M-403  顶栏「项目名称」输入框（证据 gf1）
#
# ⭐ 这张图坐实：顶栏那枚输入框**真的能改**，而且改完**标签页标题跟着变** ——
# 手册此前只写「改画布名不会改项目名」，从来没说项目名自己能不能改。
#
# ⚠️ 排版规则（FO 定的）：图上只放圈号，说明写在空白处。
# ⚠️ ⛔⛔ **图例一律 ASCII** —— PIL 默认字体无 CJK 字形。中文放 Markdown。
# ⚠️ 证据图是**裁剪后**的 ⇒ 圈号坐标必须减掉 clip 起点再乘 K=2（Batch FW §153.2）。
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
E = os.path.join(HERE, '.evidence')
SH = os.path.abspath(os.path.join(HERE, '..', 'screenshots'))
蓝 = (150, 165, 255); 橙 = (255, 190, 90); 绿 = (180, 255, 140)
K = 2
d_测 = ImageDraw.Draw(Image.new('RGB', (10, 10)))


def 字体(sz):
    for p in ('/System/Library/Fonts/Supplemental/Arial Bold.ttf',
              '/System/Library/Fonts/Supplemental/Arial.ttf'):
        if os.path.exists(p):
            try: return ImageFont.truetype(p, sz)
            except Exception: pass
    return ImageFont.load_default()


F20, F18 = 字体(20), 字体(18)


def 圈(d, x, y, 序, 色, r=16):
    d.ellipse([x-r, y-r, x+r, y+r], outline=色, width=4)
    t = str(序); bb = d.textbbox((0, 0), t, font=F20)
    d.text((x-(bb[2]-bb[0])/2, y-(bb[3]-bb[1])/2-4), t, font=F20, fill=色)


def m403():
    im = Image.open(os.path.join(E, 'gf1-顶栏项目名已改.png')).convert('RGB')
    图例 = [
        'Top bar, left to right:',
        '1 the PROJECT name - a real editable text input (aria="project name"),',
        '   min-width 30 px, max-width 100 px, maxLength 120.',
        '   It was typed here, and the browser tab now reads',
        '   "GF-title check - canvas 2 - LibTV".',
        '2 the CANVAS name - plain text, no box, no aria-label of its own;',
        '   change it from the canvas dropdown instead.',
    ]
    边, 圈带, 例行高 = 16, 12, 26
    图宽 = im.width + 边*2
    例行宽 = 边 + 12 + max(int(d_测.textlength(行, font=F18)) for 行 in 图例)
    宽 = max(图宽, 例行宽)
    高 = 边*2 + 圈带 + im.height + 30 + 例行高*len(图例)
    out = Image.new('RGB', (宽, 高), (18, 18, 20)); d = ImageDraw.Draw(out)
    out.paste(im, (边, 边+圈带))
    y = 边+圈带+im.height+30
    for 行 in 图例:
        d.text((边+6, y), 行, font=F18, fill=(210,210,215)); y += 例行高
    # clip = (0,0,520,44)
    圈(d, 边 + (118-0)*K, 边+圈带 + (52-0)*K, 1, 蓝)   # 输入框正下方（页面 y=52）
    圈(d, 边 + (250-0)*K, 边+圈带 + (52-0)*K, 2, 橙)  # 画布名下方
    p = os.path.join(SH, 'M-403-顶栏-项目名与画布名.png')
    out.save(p); print('写出', p, out.size)


if __name__ == '__main__':
    m403()
