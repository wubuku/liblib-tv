#!/usr/bin/env python3
# 合成 Batch GJ 的成品图：
#   M-407  ⭐⭐⭐ 「放大图片 / 放大视频」两枚按钮是坏的：谁被点谁活，另一列被整列吃掉
#   M-408  ⭐⭐ 视频列右下角「剪辑」点开是什么：内嵌时间轴剪辑器 + 14 枚工具条按钮
#
# ⭐ 坐实（GJ-10 / GJ-11，两组完全对称的读数）：
#   态1 基准   图片列 [495,48,463,762]  视频列 [969,48,463,762]  两枚放大键各自可点
#   态2 点视频  图片列 [495,48,937,762]  视频列 [495,48,937,762]  收起图片 中心是它=false
#   态3 点图片  图片列 [495,48,937,762]  视频列 [495,48,937,762]  收起视频 中心是它=false
#   ⇒ 放大时两列被拉到**同一个框**，后渲染的那列盖住前一个。
#   ⇒ 三个取样点（左半/右半/最右）全归同一列 ⇒ 被吃掉的列**一张卡都看不到**。
#   ⇒ 两枚「收起」键框也变成**完全相同**的 [1387,57,28,28]，只有活着那枚能点。
#   ⇒ Esc 可完整还原（A→B→C 三态闭环读数逐字相同）。
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


def m407():
    # 三张素材 clip 起点同为 (452,40)，竖排
    a = Image.open(os.path.join(E, 'gj11-1-基准.png')).convert('RGB')
    b = Image.open(os.path.join(E, 'gj11-2-放大视频后.png')).convert('RGB')
    c = Image.open(os.path.join(E, 'gj11-3-放大图片后.png')).convert('RGB')
    # ⭐ 只留「列头 + 第一张卡 + 模型标签」这一段，证据全在里面，不必贴 1540px 的全图
    裁高 = 1100
    a, b, c = a.crop((0, 0, a.width, 裁高)), b.crop((0, 0, b.width, 裁高)), c.crop((0, 0, c.width, 裁高))
    图例 = [
        'Each of the IMAGE and VIDEO column headers carries one 28 x 28 button:',
        '"zoom image" and "zoom video". In the normal storyboard they both work -',
        '1 image column  [495, 48, 463, 762]      video column [969, 48, 463, 762]',
        '   two separate boxes, each button reachable.',
        '',
        'Press "zoom video" and BOTH columns jump to the SAME box [495, 48, 937, 762].',
        'The video column is drawn on top, so the two image nodes are gone:',
        '2 the image column is still in the DOM at the same box, but its own',
        '   "collapse image" button now reads 中心是它 = false - covered.',
        'Hit-testing the left half, the right half and the far right all return',
        'the VIDEO column. There is no scrolling that brings the images back.',
        '',
        'Press "zoom image" instead and the mirror image happens:',
        '3 now the IMAGE column is on top, and the video column is the one that',
        '   disappears - its "collapse video" button reads 中心是它 = false.',
        'In both expanded states the two collapse buttons share the identical box',
        '[1387, 57, 28, 28], so only the surviving column can be closed.',
        'ESC restores the normal four columns in every case.',
        '=> The feature is broken either way: it enlarges one column by hiding the other.',
    ]
    边, 标高, 例行高 = 16, 30, 24
    图宽 = a.width
    例行宽 = 边 + 12 + max(int(d_测.textlength(行, font=F18)) for 行 in 图例)
    宽 = max(图宽, 例行宽)
    高 = 边*2 + 标高*3 + 10*(3-1) + a.height*3 + 26*3 + 例行高*len(图例)
    out = Image.new('RGB', (宽, 高), (18, 18, 20)); d = ImageDraw.Draw(out)

    CX, CY = 452, 40          # 三张素材的 clip 起点
    标 = ['1  normal storyboard: two boxes, two reachable buttons',
          '2  after "zoom video": the IMAGE column is covered',
          '3  after "zoom image": the VIDEO column is covered']
    y = 边
    for 图, 说明 in zip((a, b, c), 标):
        d.text((边+4, y-2), 说明, font=F20, fill=(230, 230, 235))
        out.paste(图, (边, y+标高))
        y += 标高 + 图.height + 26
    yl = y + 6
    for 行 in 图例:
        d.text((边+6, yl), 行, font=F18, fill=(210, 210, 215)); yl += 例行高

    顶 = [边, 边 + 标高 + a.height + 26, 边 + 2*(标高 + a.height + 26)]
    # 态1：两枚放大键都可达
    圈(d, 边 + (926-CX)*K, 顶[0] + (71-CY)*K, 1, 蓝)
    圈(d, 边 + (1401-CX)*K, 顶[0] + (71-CY)*K, 1, 蓝)
    # 态2：被盖住的收起图片键（框与收起视频键完全相同）
    圈(d, 边 + (1401-CX)*K, 顶[1] + (71-CY)*K, 2, 红)
    # 态3：被盖住的收起视频键
    圈(d, 边 + (1401-CX)*K, 顶[2] + (71-CY)*K, 3, 红)
    p = os.path.join(SH, 'M-407-放大按钮会把另一列整列吃掉.png')
    out.save(p); print('写出', p, out.size)


def m408():
    a = Image.open(os.path.join(E, 'gj11-4-剪辑器.png')).convert('RGB')
    b = Image.open(os.path.join(E, 'gj11-5-工具条.png')).convert('RGB')
    图例 = [
        'Pressing the round "edit" button floating in the bottom-right of the',
        'VIDEO column opens a full built-in timeline editor. It is NOT a dialog:',
        'no overlay, no backdrop - it replaces the right half of the storyboard',
        'in place, and it is itself a fifth storyboard column titled "smart edit".',
        'Its box is [495, 48, 937, 762], the same geometry the "zoom" buttons',
        'produce - which is why zoom and edit look almost identical.',
        '',
        'Top bar of the editor:',
        '1 "export" with a caret - the button is NOT disabled, but its tooltip',
        '   reads "no clip on the timeline yet, cannot render". Do not click it.',
        '2 "X" (title = exit editing), 32 x 32, at [1387, 57, 32, 32] -',
        '   the very spot the "zoom video" button used to occupy.',
        'The preview area sits at [504, 98, 919, 419] and says "preparing preview"',
        'forever while the clips have not been rendered yet.',
        '',
        'The toolbar below it holds 14 buttons in a box [505, 530, 917, 44]:',
        '3 the first five are greyed out to 40% opacity and unclickable - undo',
        '   (the circle is drawn here because the icon itself is nearly invisible),',
        '   redo, split, trim left, trim right - the timeline is empty.',
        '4 of the rest only three really edit: add text, add subtitle,',
        '   add transition - the circle sits on the film-strip icon.',
        '5 play (its tooltip is "preparing preview"), full screen preview,',
        '   snapping, zoom out, zoom in, hide preview.',
        'The timeline itself is a <canvas> at [593, 574, 813, 407] - its tracks',
        'are painted, so they cannot be read from the DOM. The zoom slider next',
        'to it is a range input, 0 to 100, currently sitting at 20.',
        '=> Nothing on this toolbar is usable until a real video exists in the column.',
    ]
    边, 标高, 例行高 = 16, 30, 24
    图例宽 = 边 + 12 + max(int(d_测.textlength(行, font=F18)) for 行 in 图例)
    宽 = max(a.width, b.width, 图例宽)
    高 = 边*2 + 标高*2 + 14 + a.height + 40 + b.height + 16 + 例行高*len(图例)
    out = Image.new('RGB', (宽, 高), (18, 18, 20)); d = ImageDraw.Draw(out)
    d.text((边+4, 边-2), 'the timeline editor opened by "edit"  (right half of the screen)',
           font=F20, fill=(230, 230, 235))
    y = 边 + 标高
    out.paste(a, (边, y))
    d.text((边+4, y+a.height+6), 'its toolbar, captured separately at native size',
           font=F20, fill=(230, 230, 235))
    yb = y + a.height + 6 + 标高
    out.paste(b, (边, yb))
    yl = yb + b.height + 16
    for 行 in 图例:
        d.text((边+6, yl), 行, font=F18, fill=(210, 210, 215)); yl += 例行高

    # ①② 画在整幅图上（素材 clip 起点 (452,40)）
    CX, CY = 452, 40
    圈(d, 边 + (1372-CX)*K, y + (73-CY)*K, 1, 橙)     # 「导出」右侧空白，避开「出」字
    圈(d, 边 + (1403-CX)*K, y + (73-CY)*K, 2, 绿)     # ✕
    # ③④⑤ 画在工具条特写上（素材 clip 起点 (500,520)）
    BX, BY = 500, 520
    圈(d, 边 + (537-BX)*K,  yb + (550-BY)*K, 3, 蓝)   # 撤销（灰）
    圈(d, 边 + (817-BX)*K,  yb + (550-BY)*K, 4, 粉)   # 添加转场
    圈(d, 边 + (1031-BX)*K, yb + (550-BY)*K, 5, 橙)   # 全屏预览
    p = os.path.join(SH, 'M-408-剪辑按钮点开是内嵌时间轴剪辑器.png')
    out.save(p); print('写出', p, out.size)


if __name__ == '__main__':
    m407()
    m408()
