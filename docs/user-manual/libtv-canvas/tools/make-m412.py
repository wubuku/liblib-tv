#!/usr/bin/env python3
# 合成 Batch GM 的成品图：
#   M-412  ⭐⭐⭐⭐⭐ 底栏第 ② 枚按钮不是「整理画布」，它是**平移工具切换器**，
#                    而且它换工具时**换的是图标**：箭头 ↔ 张开的手掌。
#
# ⭐ 坐实（gm5a / gm5b / gm5c / gm6 / gm7 五轮，stdout 全部落盘在 tools/.evidence/）：
#   1) 底栏第 ② 枚 框全程不变 [620,757,32,32]；点它 ⇒ 画布中下方浮出两行常驻提示条
#      `移动`[593,663,77,20] / `V`[678,663,25,20] / `抓手工具`[593,703,76,20] / `H`[677,703,26,20]
#   2) 按 H（或直接点提示条里「抓手工具」那一行）⇒ 该按钮 aria-label 变 `抓手工具`
#   3) 抓手态下画布空白处拖 +220,+120 ⇒ 视口位移**精确 (220,120)**，1:1
#      同落点下，普通态与「移动」态都是**精确 (0,0)**（落点距最近节点 44.8px，13 采样点全空）
#   4) 「移动」态下拖节点 = 搬节点（屏幕 +6,+6 ⇒ 画布坐标 +12,+12，缩放 0.482682），不产生框选矩形
#   5) ⭐ **按钮背景色不能当状态判据**：两轮实测给出相反读数
#      （gm5c/gm6 读到 rgba(0,0,0,0)，gm7 读到 rgba(255,255,255,0.15)）⇒ 标 📖
#   6) ⭐ 可靠判据是**图标**和**提示条里亮底药丸落在哪一行**（见 [3]/[4]/[1]/[2]）
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
边 = 26
行高 = 28
格间 = 34


def 字体(sz):
    for p in ('/System/Library/Fonts/Supplemental/Arial Bold.ttf',
              '/System/Library/Fonts/Supplemental/Arial.ttf'):
        if os.path.exists(p):
            try: return ImageFont.truetype(p, sz)
            except Exception: pass
    return ImageFont.load_default()


F18 = 字体(18)
F17 = 字体(17)


def 圈(d, x, y, 序, 色, r=14):
    """圈号画在**标题行**里，绝不压在图上。"""
    d.ellipse([x - r, y - r, x + r, y + r], outline=色, width=4)
    t = str(序); bb = d.textbbox((0, 0), t, font=F18)
    d.text((x - (bb[2] - bb[0]) / 2, y - (bb[3] - bb[1]) / 2 - 4), t, font=F18, fill=色)


def 放大(f, box, 倍=6):
    im = Image.open(os.path.join(E, f)).convert('RGB').crop(box)
    return im.resize((im.width * 倍, im.height * 倍), Image.LANCZOS)


def m412():
    # 上排：提示条两态（clip 起点 (556,652)，@2x ⇒ 600x176）
    卡1 = Image.open(os.path.join(E, 'gm7-a-亮态底栏条.png')).convert('RGB')
    卡2 = Image.open(os.path.join(E, 'gm7-c-灭态底栏条.png')).convert('RGB')
    # 下排：底栏第 ② 枚放大。clip 起点 (556,744) ⇒ 按钮 [620,757,32,32]
    #        相对 (64,13)，@2x ⇒ (128,26)，取 64x64 再外扩到 76 见方
    图3 = 放大('gm7-b-亮态底栏按钮.png', (120, 18, 196, 94), 6)
    图4 = 放大('gm7-d-灭态底栏按钮.png', (120, 18, 196, 94), 6)

    标题 = [
        (1, 'Toolbar card, 1.6s after clicking bottom-bar button #2', 蓝),
        (2, 'Same card, 1.5s after pressing H', 橙),
        (3, 'Move active - ARROW icon, 6x', 绿),
        (4, 'Grab Hand active - OPEN HAND icon, 6x', 粉),
    ]
    图例 = [
        'BOTTOM BAR, 7 BUTTONS - measured on 1440x810@2x, main canvas 34226ef1.',
        'Row 2 shows the SAME button (bottom-bar #2, box [620,757,32,32]) twice.',
        '',
        '[1] Appears only after clicking button #2. The whole card is lit',
        '    (white 15% over dark). Two rows: "Move" + "V", "Grab Hand" + "H".',
        '[2] After pressing H the card turns dark and ONLY the "Grab Hand" row',
        '    keeps a lit pill behind it. That pill is the visible state readout.',
        '[3] / [4] The button face is pixel-identical in both states (measured:',
        '    888 differing pixels, all inside the 64x64 icon box). The ICON is',
        '    the only thing that changes - arrow vs open hand.',
        '',
        'NOT a state indicator: the button background colour. Two rounds gave',
        'opposite readings (rgba(0,0,0,0) vs rgba(255,255,255,0.15)), so it is',
        'left unverified here. The accessible name is the reliable readout:',
        '"Move" <-> "Grab Hand".',
        '',
        'Rebuild: tools/gm7.mjs -> gm7-a..d.png, tools/gm6.mjs, tools/gm5c.mjs',
    ]

    w1, w2 = 卡1.width, 图3.width
    宽 = 边 * 2 + w1 + 格间 + 卡2.width
    高 = (边 + 行高 + 卡1.height + 格间 + 行高 + max(图3.height, 图4.height)
          + 格间 + 24 + len(图例) * 22 + 边)
    底 = Image.new('RGB', (宽, 高), (14, 14, 16))
    d = ImageDraw.Draw(底)

    # ⛔ 先验标题不互相压：每格标题宽度必须小于本格宽 − 36
    x1 = 边; x2 = 边 + w1 + 格间
    for (序, 文, 色), x, 格宽 in zip(标题, [x1, x2, x1, x2], [w1, 卡2.width, w2, w2]):
        bb = d.textbbox((0, 0), 文, font=F17)
        需 = 36 + (bb[2] - bb[0]) + 4
        assert 需 <= 格宽, f'标题「{文}」需 {需}px，本格只有 {格宽}px —— 会压到右邻'
    print('标题宽度自检: 通过')

    y = 边
    # ---- 上排：提示条两态
    for i, (图, (序, 文, 色)) in enumerate(zip([卡1, 卡2], 标题[:2])):
        x = 边 + (0 if i == 0 else w1 + 格间)
        cy = y + 行高 // 2
        圈(d, x + 15, cy, 序, 色)
        d.text((x + 36, cy - 10), 文, font=F17, fill=(228, 228, 232))
        底.paste(图, (x, y + 行高))
    y += 行高 + 卡1.height + 格间
    # ---- 下排：放大图标
    for i, (图, (序, 文, 色)) in enumerate(zip([图3, 图4], 标题[2:])):
        x = 边 + (0 if i == 0 else w2 + 格间)
        cy = y + 行高 // 2
        圈(d, x + 15, cy, 序, 色)
        d.text((x + 36, cy - 10), 文, font=F17, fill=(228, 228, 232))
        底.paste(图, (x, y + 行高))
    y += 行高 + max(图3.height, 图4.height) + 格间
    # ---- 图例
    for 文 in 图例:
        d.text((边, y), 文, font=F17, fill=(196, 196, 204))
        y += 22

    出 = os.path.join(SH, 'M-412-底栏第二枚是平移工具切换器-箭头换手掌.png')
    底.save(出)
    print('写出', 出, 底.size)
    # 自查：图例最长行不能超出版面
    最长 = max(图例, key=len)
    bb = d.textbbox((0, 0), 最长, font=F17)
    print('图例最长行宽度', bb[2] - bb[0], '版宽', 宽, '⇒', 'OK' if bb[2] - bb[0] < 宽 - 边 else '超宽!')
    print('U+FFFD 检查:', '有' if '�' in 最长 else '无')


if __name__ == '__main__':
    m412()
