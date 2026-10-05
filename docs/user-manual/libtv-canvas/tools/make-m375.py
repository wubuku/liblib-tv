#!/usr/bin/env python3
# 合成 M-375：节点参数条上五枚「aria / title / 文字三处都没有」的控件。
#
# ⭐ 这批的结论：它们的像素坐标**完全可复现**（同节点连读两次、
#    取消重选后再读、换走再换回来，全部逐字相同）——
#    未验清单里那条「坐标不可复现」到此结掉。
# ⭐⭐ 另外两枚其实**有名字**，只是名字只存在于悬停气泡里。
#
# ⚠️ 证据图 @2x ⇒ CSS 坐标必须乘 K。
# ⚠️ PIL 默认字体无 CJK 字形 ⇒ 标注一律用 ASCII 数字，中文放 Markdown 的 alt。
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
E = os.path.join(HERE, '.evidence')
SH = os.path.abspath(os.path.join(HERE, '..', 'screenshots'))


def 字体(sz):
    for p in ('/System/Library/Fonts/Supplemental/Arial.ttf',
              '/System/Library/Fonts/Supplemental/Arial Bold.ttf'):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


F15, F14, F12 = 字体(15), 字体(14), 字体(12)
C_MARK = (255, 190, 90)
C_NONE = (255, 120, 120)
C_NOTE = (175, 175, 175)
C_TXT = (215, 215, 215)

im = Image.open(os.path.join(E, 'fa1-参数条-无名控件.png')).convert('RGB')
K = im.width / 1440.0
print('K =', K)


def px(v):
    return int(round(v * K))


# 参数卡片整块（含顶部工具排与底部参数排）
裁 = im.crop((px(640), px(205), px(1045), px(400)))
pad, top, bot = 14, 96, 96
W = 裁.width + pad * 2
H = top + 裁.height + bot
画 = Image.new('RGB', (W, H), (13, 13, 15))
d = ImageDraw.Draw(画)
画.paste(裁, (pad, top))

d.text((pad, 6), 'The five controls with no aria-label, no title and no text', fill=C_TXT, font=F15)
d.text((pad, 28), 'all five sit inside this parameter card; only the tooltip knows what two of them are', fill=C_NOTE, font=F12)
d.text((pad, 48), 'boxes below are the measured pixel rects (CSS px), identical across three separate re-reads', fill=C_NOTE, font=F12)

# 五枚（CSS 坐标 → 裁图内 → 加 pad/top）
点 = [
    (1, 828, 363, 32, 32, C_MARK),   # 悬停气泡：提示词优化
    (2, 864, 363, 32, 32, C_MARK),   # 悬停气泡：翻译提示词
    (3, 904, 363, 32, 32, C_NONE),   # 滑块图标，无气泡
    (4, 997, 363, 32, 32, C_MARK),   # 生成键，气泡解释为什么点不动
    (5, 1001, 221, 28, 28, C_NONE),  # 卡片右上角的放大箭头，无气泡
]
for 号, cx, cy, w, h, 色 in 点:
    x = px(cx) - px(640) + pad
    y = px(cy) - px(205) + top
    ww, hh = px(w), px(h)
    d.rectangle([x, y, x + ww, y + hh], outline=色, width=3)
    d.ellipse([x + ww // 2 - 11, y - 26, x + ww // 2 + 11, y - 4], fill=(40, 40, 44), outline=色, width=2)
    d.text((x + ww // 2 - 4, y - 24), str(号), fill=色, font=F14)

d.text((pad, H - 72), '1 and 2 are 32x32 and look anonymous, yet hovering them reveals their real names.', fill=C_NOTE, font=F12)
d.text((pad, H - 52), '3 is a slider-shaped icon with no tooltip at all; 5 is the 28x28 expand arrow, also nameless.', fill=C_NOTE, font=F12)
d.text((pad, H - 28), 'The same controls reappear on an image node - 4 of the 5 share a byte-identical SVG path.', fill=C_MARK, font=F12)
d.text((pad, H - 10), 'Coordinates: reproduced byte-for-byte, so they are safe to hard-code.', fill=C_MARK, font=F12)

画.save(os.path.join(SH, 'M-375-参数条五枚无名控件.png'))
print('M-375', 画.size)
