#!/usr/bin/env python3
# 合成 Batch GK 的成品图：
#   M-409  ⭐⭐ 四列的形态完全不同（列头按钮、卡片形状、能不能进编辑态）
#   M-410  ⭐⭐⭐ 故事板里点卡片 = 那张卡片自己撑成编辑态（不是弹窗），四列都试过
#
# ⭐ 坐实（GK-1 / GK-2 / GK-6 / GK-7 / GK-8）：
#   ① 音频列的卡是**唯一的 `<BUTTON>`**（67×91，两枚并排），文本行 / 图片卡 / 视频卡都是 DIV
#   ② 列头按钮数：音频 **0 枚**、文本 **0 枚**、图片 **1 枚**（放大图片）、视频 **2 枚**（全部▾ + 放大视频）
#      ⇒ ⭐⭐ **只有视频列有筛选；图片列有放大键但没有筛选**
#   ③ 四列的卡片点开后**都是 `.node-floating-ui` 面板，且一律 903 宽、从 x=512 起**
#      ⇒ 面板一律**向左溢出、盖住图片列**
#   ④ Esc 能关掉编辑态
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
红 = (255, 120, 120)
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


def m409():
    a = Image.open(os.path.join(E, 'gk1-b-左半两列.png')).convert('RGB')   # clip (0,40)
    b = Image.open(os.path.join(E, 'gk1-c-右半两列.png')).convert('RGB')   # clip (495,40)
    图例 = [
        'The four storyboard columns are not four copies of the same thing.',
        'Left half - the two columns that carry no header controls at all:',
        '1 AUDIO, box [8, 48, 475, 153] - only 153 px tall, the shortest of',
        '   the four. Its two cards are 67 x 91 and sit side by side. These',
        '   are the only cards in the whole storyboard that are real <BUTTON>',
        '   elements; every other column uses plain <DIV>.',
        '2 TEXT, box [8, 213, 475, 597] - two rows, 441 x 44 each, with no',
        '   card border at all, just an icon plus the name.',
        'Neither column has a single button in its header.',
        '',
        'Right half - the two columns that do:',
        '3 IMAGE, box [495, 48, 463, 762] - its header carries exactly one',
        '   button, "zoom image" at [912, 57, 28, 28]. It has NO filter.',
        '4 VIDEO, box [969, 48, 463, 762] - the only column with a filter:',
        '   the "all" dropdown at [1328, 57, 55, 28], plus "zoom video"',
        '   at [1387, 57, 28, 28].',
        '',
        '=> The "all / finished / clip" filter exists for video only. If you',
        '   went looking for it above the image column, it is not there.',
    ]
    边, 标高, 例行高 = 16, 30, 24
    图宽 = max(a.width, b.width)
    例行宽 = 边 + 12 + max(int(d_测.textlength(行, font=F18)) for 行 in 图例)
    宽 = max(图宽, 例行宽)
    高 = 边*2 + 标高*2 + 12 + a.height + b.height + 20 + 例行高*len(图例)
    out = Image.new('RGB', (宽, 高), (18, 18, 20)); d = ImageDraw.Draw(out)
    d.text((边+4, 边-2), 'left half: audio + text (no header controls)',
           font=F20, fill=(230, 230, 235))
    ya = 边 + 标高
    out.paste(a, (边, ya))
    yb = ya + a.height + 12
    d.text((边+4, yb-26), 'right half: image + video (one and two header buttons)',
           font=F20, fill=(230, 230, 235))
    out.paste(b, (边, yb))
    yl = yb + b.height + 20
    for 行 in 图例:
        d.text((边+6, yl), 行, font=F18, fill=(210, 210, 215)); yl += 例行高

    AX, AY = 0, 40        # gk1-b 的 clip 起点
    BX, BY = 495, 40      # gk1-c 的 clip 起点
    # ⭐ 圈号一律落在**空白处**，不压图标、不压字（读图验收过两轮）
    圈(d, 边 + (76-AX)*K,  ya + (108-AY)*K, 1, 蓝)     # 第一枚音频卡的右上空白
    圈(d, 边 + (430-AX)*K, ya + (280-AY)*K, 2, 绿)     # 文本行右端空白
    圈(d, 边 + (888-BX)*K, yb + (71-BY)*K, 3, 橙)      # 放大图片 左侧空白
    圈(d, 边 + (1300-BX)*K, yb + (71-BY)*K, 4, 粉)     # 全部 ▾ 左侧空白
    p = os.path.join(SH, 'M-409-四列的形态和列头按钮完全不同.png')
    out.save(p); print('写出', p, out.size)


def m410():
    图 = {}
    for 名, 键 in [('前', 'gk9-1-前'), ('音', 'gk9-2-音频'), ('视', 'gk9-4-视频')]:
        图[名] = Image.open(os.path.join(E, 键 + '.png')).convert('RGB')
    说明 = {'前': '1 before: two ordinary cards, 429 px wide',
            '音': '2 the AUDIO card was clicked',
            '视': '3 the VIDEO card was clicked'}
    图例 = [
        'Clicking a card in the storyboard is not read-only, and it does not',
        'open a dialog either. The card itself stretches into an edit view and',
        'overflows to the LEFT, so it ends up covering the image column.',
        'All readings come from the same .node-floating-ui element - the very',
        'component the workflow view uses, mounted inside the video column.',
        '',
        '1 nothing clicked - the image and video cards sit side by side inside',
        '   their own columns, 429 px wide each.',
        '2 AUDIO card clicked - panel [512, 609, 903, 188]. Header reads',
        '   "< audio node 1" on the left and three icons on the right',
        '   (send-to-director, more, close). Inside: "reference", a prompt box',
        '   reading "describe the audio effect you want, @ to reference audio",',
        '   model Seed Audio 1.0, format "chinese - 24k - wav", a 0/2000 counter,',
        '   then "advanced settings" with speed / pitch / volume.',
        '3 VIDEO card clicked - panel [512, 549, 903, 248]. The header reads',
        '   "< video node 3" with the same three icons on the right. The toolbar',
        '   has "effects", "character library" and "camera move" next to',
        '   "reference", plus an @ chip. Model 2.0, "16:9 - 720P - 5s - 1",',
        '   and 135 credits beside the white send key. "advanced settings" is',
        '   COLLAPSED (grid-template-rows 0fr, height 0), so web search /',
        '   auto-validate / smart reference stay hidden - which is why the video',
        '',
        '   panel too, but it has NO "advanced settings" section at all.',
        '=> Both panels are exactly 903 px wide and both start at x=512, so both',
        '   panel is 60 px taller than the audio one. The image column behaves',
        '   the same way: panel [512, 605, 903, 192] with "style" next to',
        '   "reference" and model Lib Image 2.5 Pro. The text column opens a',
        '=> ESC closes the edit view. One thing to know: while a panel is open',
        '   it covers the neighbouring column, so clicking another card does',
        '   nothing until you close it.',
        '=> Nothing on the canvas changed: still 12 nodes, URL unchanged, and',
        '   no request was sent - the white send key was never pressed.',
    ]
    边, 标高, 例行高 = 16, 30, 24
    cw = max(im.width for im in 图.values())
    ch = max(im.height for im in 图.values())
    例行宽 = 边 + 12 + max(int(d_测.textlength(行, font=F18)) for 行 in 图例)
    宽 = cw*3 + 边*4
    高 = 边*2 + 标高 + ch + 24 + 例行高*len(图例)
    宽 = max(宽, 例行宽)
    out = Image.new('RGB', (宽, 高), (18, 18, 20)); d = ImageDraw.Draw(out)
    for n, 名 in enumerate(['前', '音', '视']):
        x = 边 + n*(cw + 边)
        d.text((x+4, 边-2), 说明[名], font=F20, fill=(230, 230, 235))
        out.paste(图[名], (x, 边+标高))
    yl = 边 + 标高 + ch + 24
    for 行 in 图例:
        d.text((边+6, yl), 行, font=F18, fill=(210, 210, 215)); yl += 例行高

    CX, CY = 490, 40      # gk9-* 三张的 clip 起点完全相同
    圈(d, 边 + (1330-CX)*K, 边+标高 + (104-CY)*K, 1, 蓝)
    圈(d, 边 + (cw+边) + (700-CX)*K,  边+标高 + (625-CY)*K, 2, 绿)
    圈(d, 边 + 2*(cw+边) + (900-CX)*K,  边+标高 + (65-CY)*K, 3, 粉)   # 顶栏标题右侧空白
    p = os.path.join(SH, 'M-410-故事板里点卡片会撑成编辑态.png')
    out.save(p); print('写出', p, out.size)


if __name__ == '__main__':
    m409()
    m410()
