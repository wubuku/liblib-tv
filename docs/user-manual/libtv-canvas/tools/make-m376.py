#!/usr/bin/env python3
# 合成 M-376：框选之后画布上多出来的东西。
#
# 证据图：tools/.evidence/fd4-01-框选两个.png（FD-4 实拍，@2x）
# 这张图一次说清四件事，全是本轮新测出来的：
#   ① 框选成功后，画布上多出一圈**虚线选区框**；
#   ② 选中的节点各自带着一圈 **⊕ 圆环** —— 那是**每个节点自己的连接端口**（handle），
#      ⭐ 印证 FD-5 的结论：连线和投放都走这些圆环，**不是拖节点本体**；
#   ③ 选区上方浮出**多选工具条**：排列 / 保存到资产 / 创建副本 / 打组 /
#      批量下载 / 添加到Chat / 创建为Skill；
#   ④ 被选中节点之间的连线**高亮成发光蓝色**。
#
# ⚠️ 证据图 @2x ⇒ 裁剪坐标必须乘 K（K = 图宽 / 视口宽 = 2880/1440 = 2.0）。
# ⛔ 本版起，**标注一律直接量在「裁剪+缩放后的画布」坐标系上**，
#    不再用「视口坐标 → 画布坐标」二次换算 ——
#    v1 就是因为二次换算把标注 ②④ 画到了裁剪区外（整条标注被裁掉，图上看不见）。
#    ⭐ 判据：画完自己看一眼图，每个标注数字都必须在图内可见、且指向对的东西。
# ⚠️ PIL 默认字体无 CJK 字形 ⇒ 标注一律用 ASCII，中文放 Markdown 的 alt。
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


F14, F13, F12 = 字体(14), 字体(13), 字体(12)
C_A = (255, 190, 90)     # ① 选区框
C_B = (120, 200, 255)    # ② 端口
C_C = (180, 255, 140)    # ③ 工具条
C_D = (255, 130, 200)    # ④ 连线高亮

im = Image.open(os.path.join(E, 'fd4-01-框选两个.png')).convert('RGB')
K = im.width / 1440.0
print('K =', K)

# ---- 裁剪区（视口坐标）→ 裁剪+缩放后的画布尺寸 ----
X0, Y0, X1, Y1 = 30, 196, 820, 760
SC = 1.5
c = im.crop((int(X0 * K), int(Y0 * K), int(X1 * K), int(Y1 * K)))
c = c.resize((int(c.width / SC), int(c.height / SC)), Image.LANCZOS)
W, H = c.size
print('画布', c.size)
d = ImageDraw.Draw(c)


def 断言在图内(x, y, 名字):
    if not (0 <= x < W and 0 <= y < H):
        raise SystemExit('!! 标注 %s 落在图外 (%.0f, %.0f)，画布只有 %dx%d' % (名字, x, y, W, H))


# ---- ① 虚线选区框：沿框内缩一圈，标签放框内左下空白 ----
d.rectangle([9, 109, 1019, 719], outline=C_A, width=3)
断言在图内(20, 700, '①标签')
d.text((18, 697), '1  selection frame (dashed)', font=F14, fill=C_A)

# ---- ② 节点的 ⊕ 端口圆环：圈 3 个并标 a/b/c，**不画长引线** ----
# ⛔ v1 画了从端口拉到标签的长引线，三条线横穿节点卡片，可读性差 —— 引线省掉。
端口 = [(36, 269, 'a'), (988, 269, 'b'), (36, 592, 'c')]
标签2 = (18, 345)
断言在图内(标签2[0], 标签2[1], '②标签')
d.text((标签2[0], 标签2[1]), "2  each node's own ports", font=F14, fill=C_B)
d.text((标签2[0], 标签2[1] + 17), 'drag a / b / c to link nodes,', font=F13, fill=C_B)
d.text((标签2[0], 标签2[1] + 33), 'NOT the node card itself', font=F13, fill=C_B)
for px, py, 字 in 端口:
    d.ellipse([px - 13, py - 13, px + 13, py + 13], outline=C_B, width=3)
    ox = px + 15 if px < W / 2 else px - 30
    d.text((ox, py - 15), 字, font=F14, fill=C_B)

# ---- ③ 多选工具条：沿条框一圈，标签塞在条框和选区框之间的 23px 缝里 ----
d.rectangle([86, 28, 940, 85], outline=C_C, width=3)
断言在图内(94, 88, '③标签')
d.text((92, 88), '3  multi-select toolbar', font=F14, fill=C_C)

# ---- ④ 连线高亮：**开口细框包住**那条发光的边，不用粗线盖住它 ----
# ⛔ v1 用 7px 粉线直接压在连线上，等于把真实颜色涂掉了，读者会以为线本来是粉的。
d.rectangle([450, 261, 586, 279], outline=C_D, width=2)
断言在图内(594, 236, '④标签')
d.text((594, 234), '4  the edge between', font=F13, fill=C_D)
d.text((594, 250), '   2 selected nodes', font=F13, fill=C_D)
d.text((594, 266), '   lights up blue', font=F13, fill=C_D)

out = os.path.join(SH, 'M-376-框选之后画布上多出了什么.png')
c.save(out)
print('wrote', out, c.size)
