#!/usr/bin/env python3
# 合成 Batch GI 的成品图：
#   M-406  ⭐ 故事板只有四列 + 视频列右下角那枚「剪辑」浮动按钮（并被抽屉压住）
#
# ⭐ 坐实三件事：
#   ① `.assetboard-panel` 实测**只有 4 个**（音频/文本/图片/视频）——
#      「剪辑」**不是第五列**，它是视频列右下角一枚 60×60 的浮动按钮
#   ② ⭐⭐ 抽屉开着时那枚按钮**被 Send 键整块压住点不到**（落点属主 = Send）
#   ③ 关掉抽屉立刻恢复（落点属主 = 按钮内的 IMG）
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


def m406():
    a = Image.open(os.path.join(E, 'gi2-视频列-剪辑按钮被挡.png')).convert('RGB')
    b = Image.open(os.path.join(E, 'gi3-视频列-剪辑按钮可点.png')).convert('RGB')
    图例 = [
        'The video column is 463 px wide. In its bottom-right corner floats',
        'a 60 x 60 round button with a scissor icon and the label "edit".',
        'Left - the TV Director drawer is open and its Send button covers it:',
        '1 the floating "edit" button, and the hit test at its centre returns',
        '   Send, so a click there would hit the chat box, not this button.',
        'Right - same canvas, drawer closed. The very same button is now',
        '2 reachable: the hit test returns the icon inside the button.',
        'Also on the column header:',
        '3 a 28 x 28 magnifier named "zoom video" - never covered.',
        'The storyboard has FOUR columns only: audio / text / image / video.',
        '"edit" is not a fifth column.',
        '=> Press ESC (or the drawer close button) before using "edit".',
    ]
    边, 圈带, 例行高 = 16, (24 if True else 12), 26
    图宽 = a.width + b.width + 边*3
    例行宽 = 边 + 12 + max(int(d_测.textlength(行, font=F18)) for 行 in 图例)
    宽 = max(图宽, 例行宽)
    高 = 边*2 + 圈带 + 24 + max(a.height, b.height) + 30 + 例行高*len(图例)
    out = Image.new('RGB', (宽, 高), (18, 18, 20)); d = ImageDraw.Draw(out)
    d.text((边+4, 边-2), 'left: drawer open     right: drawer closed', font=F20, fill=(230,230,235))
    out.paste(a, (边, 边+圈带+24)); out.paste(b, (边+a.width+边, 边+圈带+24))
    y = 边+圈带+24+max(a.height,b.height)+30
    for 行 in 图例:
        d.text((边+6, y), 行, font=F18, fill=(210,210,215)); y += 例行高
    # 两张的 clip 起点同为 (960,40)
    CX, CY = 960, 40
    左 = 边; 右 = 边 + a.width + 边
    圈(d, 左 + (1385-CX)*K, 边+圈带+24 + (763-CY)*K, 1, 蓝)
    圈(d, 右 + (1385-CX)*K, 边+圈带+24 + (763-CY)*K, 2, 橙)
    圈(d, 右 + (1401-CX)*K, 边+圈带+24 + (71-CY)*K, 3, 绿)
    p = os.path.join(SH, 'M-406-故事板-剪辑按钮被抽屉压住.png')
    out.save(p); print('写出', p, out.size)


if __name__ == '__main__':
    m406()
