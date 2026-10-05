#!/usr/bin/env python3
# 合成 Batch FQ 的第四张图：
#   M-389  「自己编写分镜脚本」打开的全屏分镜表编辑器（脚本 V2 的核心界面）
#
# 证据图（本轮实拍，@2x 全屏 2880×1620）：
#   fq6-1-自己编写分镜脚本.png
#
# ⭐ 这张图一次坐实 `scriptV2*` 93 条里 20 条：
#   确认镜头 / 准备资产 / 合成提示词（三步进度）
#   {count}个镜头待核对 · 暂无资产 · {ready}/{total} 已合成
#   {ready}/3 完成后可批量生视频 · 关闭(ESC)
#   表格十列：镜号 时长 画面描述 景别 光影氛围 对白·旁白 音效 运镜 最终提示词 操作
#   添加镜头 / → 下一步：准备资产 / 待生成提示词
#
# ⚠️ 排版规则（FO 定的）：图上只放圈号，说明写在空白处。
#    这张图下半部是大片空白表格 ⇒ 图例放底部，不压内容。
# ⚠️ ⛔⛔ **图例一律 ASCII** —— 第一版图例里写的中文在 PIL 默认字体下
#    全变成 □□□（无 CJK 字形）。中文放 Markdown 的 alt 和正文。
# ⚠️ 坐标换算：原图 2880 宽 = CSS 1440 宽 ⇒ K=2.0。
#    先在 2000 宽的预览图上量（显示坐标），再 ×1.44 得 CSS 坐标，最后 ×K 得像素。
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
E = os.path.join(HERE, '.evidence')
SH = os.path.abspath(os.path.join(HERE, '..', 'screenshots'))

蓝 = (150, 165, 255)
橙 = (255, 190, 90)
绿 = (180, 255, 140)
红 = (255, 130, 130)
紫 = (215, 175, 255)
底 = (18, 18, 20)


def 字体(sz):
    for p in ('/System/Library/Fonts/Supplemental/Arial Bold.ttf',
              '/System/Library/Fonts/Supplemental/Arial.ttf'):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


F22, F20 = 字体(22), 字体(19)


def 圈(d, x, y, 序, 色, r=26):
    d.ellipse([x - r, y - r, x + r, y + r], fill=色, outline=(10, 10, 12), width=3)
    t = str(序)
    tw = d.textlength(t, font=F22)
    d.text((x - tw / 2, y - 15), t, font=F22, fill=(12, 12, 12))


src = os.path.join(E, 'fq6-1-自己编写分镜脚本.png')
if not os.path.exists(src):
    raise SystemExit('⛔ 缺证据图 ' + src)

im = Image.open(src).convert('RGB')
d = ImageDraw.Draw(im)
W, H = im.size
K = W / 1440.0
显示K = 1.44          # 预览图 2000 宽 → 原图 2880 宽
print(f'证据图 {W}×{H}，K={K}，显示换算 {显示K}')


def px(显示x, 显示y):
    # ⛔ 显示 2000 宽 → 原图 2880 宽 ⇒ ×1.44 即可。
    #    （第一版写成 ×1.44×2.0 = ×2.88，多乘了一次 K，所有圈号跑到两倍远的地方。）
    return 显示x * 显示K, 显示y * 显示K


# 坐标：全部在 2000 宽的预览图上量。
# ⚠️ 圈号一律落在**元素旁边的空白**上 —— 第一轮直接压在文字上，
#    11 个圈里有 8 个糊住了要说明的字（正是 FO 定排版规则要避免的那件事）。
标注 = [
    (540, 96, 1, 蓝),     # 「确认镜头」左下空白
    (768, 62, 2, 橙),     # 「1个镜头待核对」右侧空白
    (1002, 78, 3, 绿),    # 「准备资产 / 暂无资产」左侧空白
    (1400, 78, 4, 紫),    # 「合成提示词 / 0/1 已合成」左侧空白
    (1798, 78, 5, 红),    # 「0/3 完成后可批量生视频」下方空白
    (1962, 96, 6, 红),    # 「×」下方空白
    (248, 160, 7, 蓝),    # 列头「画面描述」左下空白
    (1002, 160, 8, 蓝),   # 列头「对白·旁白」左下空白
    (762, 190, 9, 橙),    # 单元格里的 + 左侧空白
    (1748, 1064, 10, 绿), # 「→ 下一步：准备资产」左侧空白
    (78, 1064, 11, 紫),   # 「＋ 添加镜头」左侧空白
]
for sx, sy, 序, 色 in 标注:
    x, y = px(sx, sy)
    圈(d, x, y, 序, 色)

图例 = [
    (1, 蓝, 'step 1  Confirm shots   (active step)'),
    (2, 橙, 'status under step 1: "1 shot(s) to review"'),
    (3, 绿, 'step 2  Prepare assets  /  "no assets yet"'),
    (4, 紫, 'step 3  Compose prompts  /  "0/1 synthesised"'),
    (5, 红, '"0/3 done before batch video" -- a gate, not a button'),
    (6, 红, 'X = close. Escape alone did NOT close this layer'),
    (7, 蓝, 'column header: shot description'),
    (8, 蓝, 'column header: dialogue / camera move'),
    (9, 橙, 'every empty cell is a "+" placeholder, click to fill'),
    (10, 绿, 'primary button: next step (Prepare assets)'),
    (11, 紫, 'add a shot row'),
]
行高 = 34
h = 30 + 行高 * len(图例)
out = Image.new('RGB', (W, H + h), 底)
out.paste(im, (0, 0))
d2 = ImageDraw.Draw(out)
for i, (序, 色, 文字) in enumerate(图例):
    y = H + 30 + i * 行高
    圈(d2, 34, y, 序, 色, r=22)
    d2.text((70, y - 12), 文字, font=F20, fill=(228, 228, 234))

p = os.path.join(SH, 'M-389-分镜表编辑器全屏.png')
out.save(p)
print('✅ M-389-分镜表编辑器全屏.png', out.size)
