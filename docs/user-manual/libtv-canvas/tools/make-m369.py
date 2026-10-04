#!/usr/bin/env python3
# 合成 M-369：「网格吸附」结案图（第 2 版）。
#
# ⚠️ 第 1 版的三处错，记账：
#   ① 状态标签画在图片**下面一层**，被 paste 盖住了 → 标签挪到图片**下方**
#   ② 放大插图按 ×4 放大后，一个周期在放大图里是 **128 像素**，我却按 32 画刻度
#      → 改成：先按源图周期算，再乘放大倍数
#   ③ 刻度标签重复 8 遍太吵 → 只标首、中、尾三个
#
# ⚠️ PIL 默认字体没有 CJK 字形 ⇒ 图上标签一律 ASCII，中文放 Markdown 的 alt。
import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
E = os.path.join(HERE, '.evidence')
OUT = os.path.abspath(os.path.join(HERE, '..', 'screenshots', 'M-369-网格吸附-开关两态与网格步长.png'))

周期 = 32          # 图像像素，grid-period.py 三次实测都是 32
ZOOM = 0.458621

def 字体(sz):
    for p in ('/System/Library/Fonts/Supplemental/Arial.ttf',
              '/System/Library/Fonts/Helvetica.ttc',
              '/Library/Fonts/Arial.ttf'):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()

F14, F13, F12, F11 = 字体(14), 字体(13), 字体(12), 字体(11)

关 = Image.open(os.path.join(E, 'ev8-底栏关态.png')).convert('RGB')
开 = Image.open(os.path.join(E, 'ev8-底栏开态.png')).convert('RGB')
格全 = Image.open(os.path.join(E, 'ev8-点网格原样.png')).convert('RGB')
格 = 格全.crop((0, 0, 880, 440))          # 少留空白，并给右侧插图腾位置

pad = 12
W = 1340
r0y = 22                                        # 第一行图片顶
r0sub = r0y + 关.height + 5                    # 第一行状态标签（在图下方）
r1y = r0sub + 42                                # 第二行图片顶（留够标题行）
H = r1y + 格.height + 50   # 插图宽 128*3=384，须整块放得下

画 = Image.new('RGB', (W, H), (14, 14, 16))
d = ImageDraw.Draw(画)

# ── 第一行：两态 ──
d.text((pad, 3), 'BOTTOM BAR  --  the "snap to grid" button, same button, two states', fill=(200, 200, 200), font=F14)
画.paste(关, (pad, r0y))
画.paste(开, (pad + 关.width + 26, r0y))
d.rectangle([pad + 8, r0y + 8, pad + 关.width - 8, r0y + 关.height - 8], outline=(120, 220, 255), width=2)
d.rectangle([pad + 关.width + 34, r0y + 8, pad + 关.width + 26 + 开.width - 8, r0y + 开.height - 8], outline=(255, 200, 120), width=2)
d.text((pad + 6, r0sub), 'OFF - plain grid icon, 1 <svg> inside', fill=(120, 220, 255), font=F13)
d.text((pad + 关.width + 32, r0sub), 'ON - same icon + a slash laid over it, 2 <svg> inside', fill=(255, 200, 120), font=F13)

# ── 第二行：点网格 ──
gx, gy = pad, r1y
d.text((pad, r1y - 20), 'DOT GRID on empty canvas   measured pitch = 16 CSS px on screen = 35 canvas units (zoom 46%)', fill=(200, 200, 200), font=F14)
画.paste(格, (gx, gy))

# 刻度：每 4 个周期一根线，只标首/中/尾
刻 = []
x0 = gx + 24
while x0 < gx + 格.width - 6:
    刻.append(x0)
    x0 += 周期 * 4
for i, xx in enumerate(刻):
    d.line([(xx, gy + 格.height - 26), (xx, gy + 格.height - 10)], fill=(120, 220, 255), width=1)
    if i in (0, len(刻) // 2, len(刻) - 1):
        d.text((xx + 2, gy + 格.height - 9), '64px', fill=(120, 220, 255), font=F11)

# 比例尺
bx, by = gx + 24, gy + 格.height - 48
bw = 周期 * 4
d.line([(bx, by), (bx + bw, by)], fill=(255, 110, 110), width=2)
for xx in (bx, bx + bw):
    d.line([(xx, by - 5), (xx, by + 5)], fill=(255, 110, 110), width=2)
d.text((bx, by - 19), '4 cells = 64 CSS px on screen', fill=(255, 110, 110), font=F12)

# ── 放大插图：源 96×64，×3 → 288×192，含 3 个周期 ──
sx, sy, sw, sh = 240, 24, 128, 96
K = 3
小 = 格全.crop((sx, sy, sx + sw, sy + sh)).resize((sw * K, sh * K), Image.NEAREST)
小 = ImageEnhance.Brightness(小).enhance(3.4)
ix, iy = gx + 格.width + 16, gy
d.text((ix, r1y - 20), 'x3 zoom, brightened', fill=(200, 200, 200), font=F13)
画.paste(小, (ix, iy))
d.rectangle([ix - 1, iy - 1, ix + sw * K, iy + sh * K], outline=(120, 220, 255), width=2)
# ⭐ 放大后的一个周期 = 周期 × K
for k in range(1, int(sw * K / (周期 * K)) + 1):
    xx = ix + k * 周期 * K
    d.line([(xx, iy + sh * K), (xx, iy + sh * K + 9)], fill=(120, 220, 255), width=1)
d.text((ix, iy + sh * K + 12), 'each tick = 1 cell = 16 CSS px', fill=(120, 220, 255), font=F12)

d.text((pad, H - 20), 'main panels are raw screenshots (no retouching); only the inset is brightened so the faint dots are visible', fill=(135, 135, 135), font=F11)

画.save(OUT)
print('已写', OUT, 画.size)
