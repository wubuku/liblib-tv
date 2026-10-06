#!/usr/bin/env python3
# 合成 Batch GG 的成品图：
#   M-404  顶栏「工作流 / 故事板」两枚切换键（证据 gg1）
#
# ⭐ 坐实：两枚键靠 aria-pressed 表达状态；⭐⭐ **切换不写进 URL** ——
# 同一个地址栏参数在两种模式下完全一样，刷新后回到默认的工作流。
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


def m404():
    im = Image.open(os.path.join(E, 'gg1-故事板态.png')).convert('RGB')
    # 再裁出顶栏一小条，主体更清楚
    im = im.crop((0, 0, im.width, 200))
    图例 = [
        '1 STORYBOARD is the active one (aria-pressed=true, dark pill background).',
        '2 WORKFLOW, now inactive.',
        '3 The storyboard columns underneath: audio / text / image / video / clip,',
        '   each node re-rendered as a card. The canvas underneath never moved -',
        '   all 12 nodes kept their exact coordinates, and both edges survived.',
        'NOTE: the URL does NOT record the mode. Reloading the page returns you',
        'to the workflow view.',
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
    # clip 起点 = (0,0) —— 按钮框 工作流 [244,8,32,32]、故事板 [276,8,32,32]
    圈(d, 边 + (260-0)*K, 边+圈带 + (24-0)*K, 1, 蓝)
    圈(d, 边 + (292-0)*K, 边+圈带 + (24-0)*K, 2, 橙)
    圈(d, 边 + (39-0)*K, 边+圈带 + (71-0)*K, 3, 绿)
    p = os.path.join(SH, 'M-404-顶栏-工作流与故事板切换.png')
    out.save(p); print('写出', p, out.size)


if __name__ == '__main__':
    m404()
