#!/usr/bin/env python3
# 合成 M-370：「新功能：支持真人」这枚常驻标记的结案图。
#
# ⭐ 这张图最要紧的一处，是**角色库 按钮底色变亮了**（指针正压在它上面），
#    而它**没有弹出任何气泡** —— 画面上那枚「新功能：支持真人」是常驻的，
#    不是角色库被悬停出来的。同一批实验里悬停「参考」是会正常弹出
#    「在当前画布中添加参考」的（阳性对照）。
#
# ⚠️ PIL 默认字体无 CJK 字形 ⇒ 图上标签一律 ASCII，中文放 Markdown 的 alt。
import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
E = os.path.join(HERE, '.evidence')
OUT = os.path.abspath(os.path.join(HERE, '..', 'screenshots', 'M-370-新功能支持真人-常驻引导标记.png'))

def 字体(sz):
    for p in ('/System/Library/Fonts/Supplemental/Arial.ttf',
              '/System/Library/Fonts/Helvetica.ttc'):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()

F14, F13, F12 = 字体(14), 字体(13), 字体(12)
C_STICKY = (255, 190, 90)
C_HOVER = (120, 220, 255)
C_NOTE = (170, 170, 170)

im = Image.open(os.path.join(E, 'ew9-悬停角色库.png')).convert('RGB')
K = 2
大 = im.resize((im.width * K, im.height * K), Image.LANCZOS)
大 = ImageEnhance.Brightness(大).enhance(1.25)

pad = 14
top = 96
W = 大.width + pad * 2
H = top + 大.height + 96
画 = Image.new('RGB', (W, H), (13, 13, 15))
d = ImageDraw.Draw(画)
画.paste(大, (pad, top))

d.text((pad, 6), 'PERSISTENT "new feature" callout on the selected video node card', fill=(210, 210, 210), font=F14)

# ① 框住那枚常驻气泡（CSS [541,191,114,27] ⇒ 截图内 [161,31] 起 114×27；合成后 ×2 再位移）
#    截图是 clip {x:380,y:190,w:460,h:110} 的 @2x，⇒ 图内 CSS 坐标 = (css - 380, css - 190) ×2
# ⚠️ 截图是 clip{x:380,y:190} 的 @2x 图，再被本脚本放大 K 倍 ⇒ 系数是 2*K，不是 K
DPR = 2
def to_img(cx, cy):
    return ((cx - 380) * DPR * K + pad, (cy - 190) * DPR * K + top)

x0, y0 = to_img(541, 191)
x1, y1 = to_img(541 + 114, 191 + 27)
d.rectangle([x0 - 4, y0 - 4, x1 + 4, y1 + 4], outline=C_STICKY, width=2)
d.line([(x0 - 30, y0 + 4), (x0 - 6, y0 + 4)], fill=C_STICKY, width=2)
d.text((pad, 26), '1  the callout  -  always on screen while this node is selected', fill=C_STICKY, font=F13)
d.text((pad, 46), '   its bottom arrow points at the button below', fill=C_STICKY, font=F12)

# ② 框住角色库按钮（CSS [565,225,66,26]）
bx0, by0 = to_img(565, 225)
bx1, by1 = to_img(565 + 66, 225 + 26)
d.rectangle([bx0 - 3, by0 - 3, bx1 + 3, by1 + 3], outline=C_HOVER, width=2)
TX = 1210        # 右侧空白区，避开「运镜」按钮
d.line([(bx1 + 4, by0 + 13), (TX - 8, by0 + 13)], fill=C_HOVER, width=1)
d.text((TX, by0 - 12), '2  pointer is ON this button', fill=C_HOVER, font=F13)
d.text((TX, by0 + 4), '   (its background is lighter) - yet NO', fill=C_HOVER, font=F12)
d.text((TX, by0 + 20), '   tooltip popped: not a hover bubble', fill=C_HOVER, font=F12)

# ③ 底部注解
d.line([(pad, H - 74), (W - pad, H - 74)], fill=(60, 60, 66), width=1)
d.text((pad, H - 66), 'Positive control in the SAME run: hovering the first button DID pop up its own bubble', fill=(150, 200, 150), font=F13)
d.text((pad, H - 46), '("add a reference to the current canvas").  So the detector works - the callout above is not hover-driven.', fill=(150, 200, 150), font=F12)
d.text((pad, H - 24), 'raw screenshot, brightened x1.25 for visibility; no other retouching', fill=(125, 125, 125), font=F12)

画.save(OUT)
print('已写', OUT, 画.size)
