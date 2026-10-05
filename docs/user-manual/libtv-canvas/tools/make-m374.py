#!/usr/bin/env python3
# 合成 M-374：`合并分镜组` 的**可用**一态，与 M-358 的**灰**态并排对照。
#
# 这张图补的是手册挂了很久的那个 📖：「选区刚好是 2 个纯图片节点时它会变亮」
# —— 当年取不到阳性对照，所以那一条一直只是源码条件。
#
# ⚠️ 证据图是 @2x（2880x1620），CSS 坐标必须乘 K 才能裁。
# ⚠️ PIL 默认字体无 CJK 字形 ⇒ 图上标签一律 ASCII。
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SH = os.path.abspath(os.path.join(HERE, '..', 'screenshots'))
E = os.path.join(HERE, '.evidence')


def 字体(sz):
    for p in ('/System/Library/Fonts/Supplemental/Arial.ttf',
              '/System/Library/Fonts/Supplemental/Arial Bold.ttf'):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


F15, F13, F12 = 字体(15), 字体(13), 字体(12)
C_ON = (140, 225, 255)
C_OFF = (255, 170, 120)
C_NOTE = (175, 175, 175)
C_TXT = (215, 215, 215)

# 左：既有 M-358（灰态）
左 = Image.open(os.path.join(SH, 'M-358-打组下拉.png')).convert('RGB').crop((40, 40, 380, 320))

# 右：本轮实测（可用态）—— CSS 坐标 × K
右全 = Image.open(os.path.join(E, 'ez1g-2-两个纯图片节点-打组下拉.png')).convert('RGB')
K = 右全.width / 1440.0
def px(v):
    return int(round(v * K))
右 = 右全.crop((px(520), px(222), px(706), px(362)))
print('K =', K, '左', 左.size, '右', 右.size)

h = max(左.height, 右.height)
pad, gap, top, bot = 14, 22, 92, 86
W = pad * 2 + 左.width + gap + 右.width
H = top + h + bot
画 = Image.new('RGB', (W, H), (13, 13, 15))
d = ImageDraw.Draw(画)
画.paste(左, (pad, top))
画.paste(右, (pad + 左.width + gap, top))

d.text((pad, 6), 'The same menu item, two states - "merge into storyboard group"', fill=C_TXT, font=F15)
d.text((pad, 28), 'left: selection is NOT 2 pure image nodes   |   right: selection IS 2 pure image nodes', fill=C_NOTE, font=F12)
d.text((pad, 48), 'disabled signal = opacity 0.45 + cursor not-allowed, while button.disabled stays false', fill=C_NOTE, font=F12)

d.rectangle([pad, top, pad + 左.width, top + 左.height], outline=C_OFF, width=3)
d.text((pad, top - 22), '[L] 2 images + 1 audio  ->  GRAY', fill=C_OFF, font=F13)

x2 = pad + 左.width + gap
d.rectangle([x2, top, x2 + 右.width, top + 右.height], outline=C_ON, width=3)
d.text((x2, top - 22), '[R] exactly 2 image nodes  ->  USABLE', fill=C_ON, font=F13)

d.text((pad, H - 62), 'Measured on the second one: the whole row computes to opacity 1 with cursor pointer,', fill=C_NOTE, font=F12)
d.text((pad, H - 42), 'and "group" right next to it reads the same. The only variable is the selection.', fill=C_NOTE, font=F12)
d.text((pad, H - 18), 'This is the positive control that the manual had been missing for many batches.', fill=C_ON, font=F12)
画.save(os.path.join(SH, 'M-374-合并分镜组-可用与灰两态对照.png'))
print('M-374', 画.size)
