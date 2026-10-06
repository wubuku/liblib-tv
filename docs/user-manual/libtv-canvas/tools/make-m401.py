#!/usr/bin/env python3
# 合成 Batch GD 的成品图：
#   M-401  ⭐「剧本生成」芯片点开的是**题材抽屉**，不是节点（证据 gd3）
#   M-402  五枚芯片实测对照：4 枚建节点、1 枚开抽屉（证据 gd2-视频生成 + gd2-智能剪辑）
#
# ⚠️ 排版规则（FO 定的）：图上只放圈号，说明写在空白处。
# ⚠️ ⛔⛔ **图例一律 ASCII** —— PIL 默认字体无 CJK 字形。中文放 Markdown。
# ⚠️ 证据图是**裁剪后**的 ⇒ 圈号坐标必须减掉 clip 起点再乘 K=2（Batch FW §153.2）。
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
E = os.path.join(HERE, '.evidence')
SH = os.path.abspath(os.path.join(HERE, '..', 'screenshots'))

蓝 = (150, 165, 255); 橙 = (255, 190, 90); 绿 = (180, 255, 140); 粉 = (255, 150, 190)
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


def 圈(d, x, y, 序, 色, r=18):
    d.ellipse([x - r, y - r, x + r, y + r], outline=色, width=4)
    t = str(序); bb = d.textbbox((0, 0), t, font=F20)
    d.text((x - (bb[2]-bb[0])/2, y - (bb[3]-bb[1])/2 - 4), t, font=F20, fill=色)


def 底板(图们, 图例, 标题=None):
    边, 圈带, 例行高 = 16, (24 if 标题 else 12), 26
    图宽 = sum(im.width for im in 图们) + 边*(len(图们)+1)
    例行宽 = 边 + 12 + max(int(d_测.textlength(行, font=F18)) for 行 in 图例)
    宽 = max(图宽, 例行宽)
    高 = 边*2 + 圈带 + max(im.height for im in 图们) + 14 + 例行高*len(图例) + (24 if 标题 else 0)
    out = Image.new('RGB', (宽, 高), (18, 18, 20)); d = ImageDraw.Draw(out)
    x = 边
    for im in 图们:
        out.paste(im, (x, 边+圈带+(24 if 标题 else 0))); x += im.width + 边
    if 标题: d.text((边+4, 边-2), 标题, font=F20, fill=(230,230,235))
    y = 边+圈带+(24 if 标题 else 0) + max(im.height for im in 图们) + 14
    for 行 in 图例:
        d.text((边+6, y), 行, font=F18, fill=(210,210,215)); y += 例行高
    return out, d


def m401():
    im = Image.open(os.path.join(E, 'gd3-剧本生成-题材抽屉.png')).convert('RGB')
    图例 = [
        'Chips 1, 2, 3 and 5 all drop a node straight onto the canvas.',
        'Chip 4 ("script") is the odd one out: it opens this drawer instead',
        'and the canvas stays empty (0 nodes).',
        'The drawer lists eight hot genres, each with a rank badge (#1 to #8):',
        'xianxia-cultivation, ancient female romance, workplace growth,',
        'rule-based mystery, apocalypse survival, rebirth revenge,',
        'intangible-heritage trend, sect doting slice-of-life.',
        'At the bottom it names the tool: "script creator - original" and',
        'the model "Doubao Seed Evolving".',
    ]
    out, d = 底板([im], 图例)
    P = (16, 16+12)
    CX, CY = 1004, 134          # clip = drawer box (1024,154) 外扩 20
    圈(d, P[0] + (1060-CX)*K, P[1] + (190-CY)*K, 1, 蓝)
    圈(d, P[0] + (1105-CX)*K, P[1] + (270-CY)*K, 2, 橙)
    圈(d, P[0] + (1390-CX)*K, P[1] + (640-CY)*K, 3, 绿)
    p = os.path.join(SH, 'M-401-剧本生成芯片-打开题材抽屉.png')
    out.save(p); print('写出', p, out.size)


def m402():
    a = Image.open(os.path.join(E, 'gd2-视频生成.png')).convert('RGB')
    b = Image.open(os.path.join(E, 'gd2-智能剪辑.png')).convert('RGB')
    图例 = [
        'Left: clicking "video" chip dropped a 622 x 350 node titled',
        'Left: "video node 1".',
        'Right: clicking "smart clip" chip dropped a 350 x 350 node titled',
        'Right: "smart clip 1", which asks for a video to be connected first.',
        '=> The chip label names the node type; the number restarts at 1',
        'because each of these was built on a FRESH empty canvas.',
    ]
    out, d = 底板([a, b], 图例, 标题='chip "video" (a)   /   chip "smart clip" (b)')
    P = (16, 16+12+24)
    左 = 16; 右 = 16 + a.width + 16
    # a 的 clip = node box (545,258,622,350) 外扩 60 ⇒ (485,198)
    圈(d, 左 + (600-485)*K, P[1] + (285-198)*K, 1, 蓝)
    圈(d, 左 + (820-485)*K, P[1] + (270-198)*K, 2, 橙)
    # b 的 clip = node box (545,258,350,350) 外扩 60 ⇒ (485,198)
    圈(d, 右 + (600-485)*K, P[1] + (285-198)*K, 3, 绿)
    圈(d, 右 + (760-485)*K, P[1] + (330-198)*K, 4, 粉)
    p = os.path.join(SH, 'M-402-芯片建出的节点-视频与智能剪辑.png')
    out.save(p); print('写出', p, out.size)


if __name__ == '__main__':
    m401(); m402()
