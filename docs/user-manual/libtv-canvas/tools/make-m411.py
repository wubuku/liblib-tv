#!/usr/bin/env python3
# 合成 Batch GL 的成品图：
#   M-411  ⭐⭐⭐⭐ 故事板态下整条左下底栏被分栏卡盖住，7 枚按钮一枚都点不到
#          （外加顶栏那枚手册从没提过的「积分超市」）
#
# ⭐ 坐实（GL-5，同一块底栏、同一组按钮的两态读数）：
#   底栏容器 [571,748,299,50]，7 枚按钮 框/aria 两态**逐字相同**：
#     添加节点 [580,757] / 移动 [620,757] / 素材库 [660,757] / 角色造型室 [700,757]
#     / 生成历史 [740,757] / 快捷键 [789,757] / 教程 [829,757]，各 32×32
#   两态里它们的**框宽高、opacity、visibility 全部一样**，元素都还在；
#   ⭐ 但 `elementFromPoint` 的落点：
#     工作流态 = 按钮自己（空字符串）
#     故事板态 = **`【故事板列】`**（7/7 全被 `.assetboard-panel` 吃掉）
#   ⇒ 故事板态下这条底栏**整条报废**，不是「按钮不见了」，是「按钮在那儿但点不到」。
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


def m411():
    工 = Image.open(os.path.join(E, 'gl5-a-工作流态-底栏.png')).convert('RGB')  # clip (0,745)
    故 = Image.open(os.path.join(E, 'gl5-b-故事板态-底栏.png')).convert('RGB')  # clip (0,745)
    顶 = Image.open(os.path.join(E, 'gl5-d-故事板态-顶栏右.png')).convert('RGB')  # clip (900,0)
    图例 = [
        'TOP: the right end of the top bar, storyboard mode.',
        '3 a 32 x 32 button this manual never mentions, sitting between',
        '   "publish and share" [954, 8, 32, 32] and the credit counter [1201, 8,',
        '   58, 32]. Its accessible name is "points store" and its tooltip says',
        '   the same thing; inside there is only an <svg> and a <path>, no text.',
        '   Its wrapper carries the class mantine-visible-from-md, so it hides',
        '   itself on narrow windows. What it opens was NOT tested here - it may',
        '   lead to a purchase page. Everything else on this bar is a normal',
        '   button and does respond.',
        '',
        'BOTTOM ROW 1 - workflow mode, the left-bottom toolbar:',
        '1 the whole bar is drawn and usable. "asset library" [14, 764, 94, 28]',
        '   on the left, then four icons, the zoom readout "48%", and seven',
        '   32 x 32 buttons: "add node" [580, 757], "move" [620, 757],',
        '   "asset library" [660, 757], "character styling" [700, 757],',
        '   "generation history" [740, 757], "shortcuts" [789, 757],',
        '   "tutorial" [829, 757]. The bar itself is [571, 748, 299, 50].',
        '',
        'BOTTOM ROW 2 - storyboard mode, the very same toolbar:',
        '2 nothing is drawn there at all. Every one of those buttons is still',
        '   in the DOM with an identical box, opacity and visibility - but a hit',
        '   test at the centre of each one now returns a storyboard column, not',
        '   the button. All of them are covered, so none can be clicked - and the',
        '   "asset library" button at the far left is covered the same way, which',
        '   is why its drawer will not open either.',
        '',
        '=> "The button is gone" is the wrong diagnosis. It is there, it looks',
        '   normal, and a storyboard column is sitting on top of it.',
    ]
    边, 标高, 例行高 = 16, 30, 24
    例行宽 = 边 + 12 + max(int(d_测.textlength(行, font=F18)) for 行 in 图例)
    宽 = max(工.width, 故.width, 顶.width, 例行宽)
    高 = (边*2 + 标高*3 + 16*2 + 顶.height + 工.height + 故.height
          + 24*2 + 例行高*len(图例))
    out = Image.new('RGB', (宽, 高), (18, 18, 20)); d = ImageDraw.Draw(out)

    d.text((边+4, 边-2), 'top bar, storyboard mode', font=F20, fill=(230, 230, 235))
    y0 = 边 + 标高
    out.paste(顶, (边, y0))
    y1 = y0 + 顶.height + 16
    d.text((边+4, y1-26), 'LEFT-BOTTOM TOOLBAR - workflow mode: seven buttons, all clickable',
           font=F20, fill=(230, 230, 235))
    out.paste(工, (边, y1))
    y2 = y1 + 工.height + 16
    d.text((边+4, y2-26), 'the same toolbar in storyboard mode: nothing drawn, all seven covered',
           font=F20, fill=(230, 230, 235))
    out.paste(故, (边, y2))
    yl = y2 + 故.height + 24
    for 行 in 图例:
        d.text((边+6, yl), 行, font=F18, fill=(210, 210, 215)); yl += 例行高

    TX, TY = 900, 0        # 顶栏 clip 起点
    圈(d, 边 + (966-TX)*K, y0 + (24-TY)*K, 3, 橙)     # 「积分超市」左侧空白
    BX, BY = 0, 745        # 两张底栏 clip 起点相同
    圈(d, 边 + (450-BX)*K, y1 + (786-BY)*K, 1, 绿)     # 工作流态底栏：48% 右边的空白
    圈(d, 边 + (450-BX)*K, y2 + (786-BY)*K, 2, 红)     # 故事板态：同一段已经什么都没有了
    p = os.path.join(SH, 'M-411-故事板态底栏整条被盖住.png')
    out.save(p); print('写出', p, out.size)


if __name__ == '__main__':
    m411()
