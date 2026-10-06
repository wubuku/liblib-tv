#!/usr/bin/env python3
# 合成 Batch GH 的成品图：
#   M-405  故事板点「对话」之后：TV Director 抽屉停在欢迎页 + 输入框里挂上附件 chip
#
# ⭐ 坐实两件事：
#   ① 点「对话」**不会自动发消息** —— 抽屉停在欢迎页，消息区一字未增
#   ② ⭐⭐ **Send 键在只挂附件、没打一个字的时候就已经可点**（disabled=false）
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


def 圈(d, x, y, 序, 色, r=16):
    d.ellipse([x-r, y-r, x+r, y+r], outline=色, width=4)
    t = str(序); bb = d.textbbox((0, 0), t, font=F20)
    d.text((x-(bb[2]-bb[0])/2, y-(bb[3]-bb[1])/2-4), t, font=F20, fill=色)


def m405():
    im = Image.open(os.path.join(E, 'gh1-故事板-点对话之后.png')).convert('RGB')
    图例 = [
        'After clicking the "chat" button on a storyboard node row:',
        '1 the drawer is still sitting on its welcome screen - four entry',
        '   buttons, and NOT ONE message from you. Nothing was submitted.',
        '2 the composer at the bottom now carries a single attachment chip',
        '   naming that node.',
        '3 the Send arrow is already enabled even though you typed nothing',
        '   (disabled = false). One stray click and the request goes out.',
        '=> Read the chip, then decide. Do not treat "I only attached it"',
        '   as "I did not act".',
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
    # clip = (1000,140,440,680)  ⇒ 页面坐标 = 1000 + 图内px/2
    CX, CY = 1000, 140
    圈(d, 边 + (1220-CX)*K, 边+圈带 + (300-CY)*K, 1, 蓝)     # 欢迎语区
    圈(d, 边 + (1020-CX)*K, 边+圈带 + (680-CY)*K, 2, 橙)     # 附件 chip 左侧空白
    圈(d, 边 + (1360-CX)*K, 边+圈带 + (700-CY)*K, 3, 粉)     # Send 左上
    p = os.path.join(SH, 'M-405-故事板-对话按钮只挂附件不发送.png')
    out.save(p); print('写出', p, out.size)


if __name__ == '__main__':
    m405()
