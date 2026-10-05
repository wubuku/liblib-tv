#!/usr/bin/env python3
# 合成 Batch EY 的三张结案图。
#
# ⚠️ PIL 默认字体无 CJK 字形 ⇒ 图上标签一律 ASCII，中文放 Markdown 的 alt。
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


F15, F13, F12 = 字体(15), 字体(13), 字体(12)
C_A = (255, 205, 110)      # 已收藏
C_B = (130, 210, 255)      # 未收藏
C_WARN = (255, 120, 120)
C_NOTE = (175, 175, 175)
C_TXT = (215, 215, 215)


# ================= M-371：收藏星的两态 =================
a = Image.open(os.path.join(E, 'ey6-卡0-已收藏态.png')).convert('RGB')
b = Image.open(os.path.join(E, 'ey6-卡1-未收藏态.png')).convert('RGB')
h = max(a.height, b.height)
pad, gap, top, bot = 14, 18, 88, 78
W = pad * 2 + a.width + gap + b.width
H = top + h + bot
画 = Image.new('RGB', (W, H), (13, 13, 15))
d = ImageDraw.Draw(画)
画.paste(a, (pad, top))
画.paste(b, (pad + a.width + gap, top))

d.text((pad, 6), 'Favorite star: two states, same card component in the STYLE plaza', fill=C_TXT, font=F15)
d.text((pad, 28), 'state read from aria-label AND from whether the star is FILLED', fill=C_NOTE, font=F12)

# 左：实心星 + 取消收藏
d.rectangle([pad, top, pad + a.width, top + a.height], outline=C_A, width=3)
d.text((pad, top - 22), '[L] aria-label = "un-favorite"   FILLED star', fill=C_A, font=F13)
d.text((pad, top + a.height + 8), 'card #0 - the hot-pick card type, no "commercial" badge', fill=C_NOTE, font=F12)

# 右：描边星 + 收藏
x2 = pad + a.width + gap
d.rectangle([x2, top, x2 + b.width, top + b.height], outline=C_B, width=3)
d.text((x2, top - 22), '[R] aria-label = "favorite"     OUTLINE star', fill=C_B, font=F13)
d.text((x2, top + b.height + 8), 'card #1 - a normal card, it carries a "commercial" badge', fill=C_NOTE, font=F12)

d.text((pad, H - 58),
       'The two icons are genuinely different SVG paths: the filled one has 1 sub-path,',
       fill=C_NOTE, font=F12)
d.text((pad, H - 40),
       'the outline one has 2 (an inner hole). So aria-label and the picture always agree.',
       fill=C_NOTE, font=F12)
d.text((pad, H - 18),
       'UNEXPLAINED: both plazas report "no items" in their favorites tab.  See M-372.',
       fill=C_WARN, font=F12)

画.save(os.path.join(SH, 'M-371-收藏星-实心与描边两态.png'))
print('M-371', 画.size)


# ================= M-372：特效广场的「我的收藏」里有一张卡，仍然没有详情 =================
c = Image.open(os.path.join(E, 'ey4-特效-我的收藏-有1张.png')).convert('RGB')
# ⚠️ 同样是 @2x，第一版忘了乘 K，裁出来只有页签那一行。
K2 = c.width / 1440.0
print('K2 =', K2)
def px2(v):
    return int(round(v * K2))
裁 = c.crop((px2(100), px2(85), px2(700), px2(455)))
pad, top, bot = 14, 84, 84
W = 裁.width + pad * 2
H = top + 裁.height + bot
画2 = Image.new('RGB', (W, H), (13, 13, 15))
d2 = ImageDraw.Draw(画2)
画2.paste(裁, (pad, top))
d2.text((pad, 6), 'LENS plaza > favorites tab, right after favoriting one effect', fill=C_TXT, font=F15)
d2.text((pad, 26), 'exactly 1 card, 0 detail buttons, and its star reads aria-label = "un-favorite"', fill=C_NOTE, font=F12)
d2.text((pad, 46), 'the card is byte-for-byte the same component as in the main LENS tab', fill=C_NOTE, font=F12)
d2.rectangle([pad, top, pad + 裁.width, top + 裁.height], outline=(90, 90, 95), width=2)
d2.text((pad, H - 60), 'So the favorites list is NOT a place where a hidden detail button shows up:', fill=C_NOTE, font=F12)
d2.text((pad, H - 40), 'it reuses the very same card, still only the three-dot entry and the star.', fill=C_NOTE, font=F12)
d2.text((pad, H - 16), 'That closes the last untried route to the effect-side detail panel.', fill=C_A, font=F12)
画2.save(os.path.join(SH, 'M-372-特效广场-我的收藏-收藏后仍无详情.png'))
print('M-372', 画2.size)


# ================= M-373：特效卡右下角空着（没有 ⤢ 详情）=====================
# ⚠️ 证据图是 @2x（2880x1620），CSS 坐标必须先乘 2 再裁。
#    第一版忘了乘，标注框全落在页签行上。
e = Image.open(os.path.join(E, 'ey2-特效库打开.png')).convert('RGB')
K = e.width / 1440.0            # 实测倍率，不写死 2
print('K =', K)
def px(v):
    return int(round(v * K))
裁 = e.crop((px(100), px(185), px(700), px(455)))
pad, top, bot = 14, 84, 82
W = 裁.width + pad * 2
H = top + 裁.height + bot
画3 = Image.new('RGB', (W, H), (13, 13, 15))
d3 = ImageDraw.Draw(画3)
画3.paste(裁, (pad, top))
d3.text((pad, 6), 'LENS plaza cards: the bottom-right corner is empty', fill=C_TXT, font=F15)
d3.text((pad, 26), 'in the STYLE plaza a diagonal-arrow button sits exactly here, on every card', fill=C_NOTE, font=F12)
d3.text((pad, 46), '(on the STYLE plaza it appears only while the card is hovered)', fill=C_NOTE, font=F12)

# 卡1 [117,197,191,240] 卡2 [320,197,191,240]；标注预览图右下角 ≈ (w-9, 197+185)
for cx, top_y in ((117, 197), (320, 197)):
    x = px(cx + 191 - 10) - px(100) + pad
    y = px(top_y + 188) - px(185) + top
    d3.rectangle([x - 32, y - 32, x + 8, y + 8], outline=C_WARN, width=3)
    # 标签放进预览图内部（深色底才读得清），别压在标题行上
    d3.rectangle([x - 34, y - 54, x + 62, y - 34], fill=(60, 20, 20))
    d3.text((x - 30, y - 51), 'empty corner', fill=C_WARN, font=F12)

d3.text((pad, H - 60), 'Same session, same detector: the STYLE plaza reported a detail button on 30 of 30', fill=C_NOTE, font=F12)
d3.text((pad, H - 40), 'cards; LENS plaza reported 0 out of 42 cards rendered in the panel.', fill=C_NOTE, font=F12)
d3.text((pad, H - 16), 'The zero is a real zero, not a miss - that is what the control proves.', fill=C_A, font=F12)
画3.save(os.path.join(SH, 'M-373-特效卡-没有详情按钮.png'))
print('M-373', 画3.size)

# ---- 自检：图上标签里不该有 CJK（PIL 默认字体渲染成方框）----
import re
本体 = [m for m in re.findall(r"d3?\.text\([^\n]*'([^']*)'", open(__file__, encoding='utf-8').read())
       if re.search(r'[\u4e00-\u9fff]', m)]
print('CJK-in-labels:', 本体 if 本体 else 'none')
