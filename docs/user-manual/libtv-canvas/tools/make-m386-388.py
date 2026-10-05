#!/usr/bin/env python3
# 合成 Batch FQ 的三张图：三个「添加节点面板里有、但手册从未单独讲过」的节点
#
#   M-386  智能剪辑节点（空态：空空如也 + 四个「尝试」）
#   M-387  逐帧拉片节点（视频素材 / 拆解维度三选一 / 灰态「开始拉片」）
#   M-388  脚本生成器节点（三个入口）
#
# 证据图（本轮实拍，@2x，主画布 zoom 0.4827）：
#   fq5-2-智能剪辑节点.png → M-386   图 442×442
#   fq5-3-逐帧拉片节点.png → M-387   图 412×480
#   fq5-1-脚本V2节点.png  → M-388   图 442×442
#
# ⚠️ ⛔⛔ **图例一律 ASCII**：第一版图例里写中文，PIL 默认字体没有 CJK 字形，
#    全部渲染成 □□□。中文放 Markdown 的 alt 和正文。
# ⚠️ ⛔⛔ **圈号坐标直接量成图内像素**，不要再用「裁剪偏移 + 余量」的算式 ——
#    第二版用算式出来，5 个圈里 4 个落在了错误的行上。
# ⚠️ 排版规则（FO 定的）：**图上只放圈号，说明写在空白处的图例里**。
#    圈号也必须落在**元素旁边的空白**上，不能压住要说明的字。
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
灰 = (140, 140, 150)
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


F13, F12, F11 = 字体(13), 字体(11), 字体(10)


def 圈(d, x, y, 序, 色, r=11):
    d.ellipse([x - r, y - r, x + r, y + r], fill=色, outline=(12, 12, 12), width=2)
    t = str(序)
    tw = d.textlength(t, font=F12)
    d.text((x - tw / 2, y - 7), t, font=F12, fill=(12, 12, 12))


def 出(src, dst, 标注, 图例, 台宽=430):
    p = os.path.join(E, src)
    if not os.path.exists(p):
        print('⛔ 缺证据图', p)
        return
    im = Image.open(p).convert('RGB')
    d = ImageDraw.Draw(im)
    for x, y, 序, 色 in 标注:
        圈(d, x, y, 序, 色)
    行 = [r for r in 图例 if r]
    h = 16 + 15 * len(行)
    台图 = Image.new('RGB', (台宽, h), 底)
    d2 = ImageDraw.Draw(台图)
    for i, (序, 色, 文字) in enumerate(行):
        y = 16 + i * 15 + 7
        圈(d2, 12, y, 序, 色, r=7)
        d2.text((24, y - 6), 文字, font=F11, fill=(226, 226, 232))
    out = Image.new('RGB', (im.width + 台宽, max(im.height, h)), 底)
    out.paste(im, (0, 0))
    out.paste(台图, (im.width, 0))
    p2 = os.path.join(SH, dst)
    out.save(p2)
    print('✅', dst, out.size)


# ── M-386 智能剪辑节点（图 442×442）坐标直接量自 M-386 预览
出('fq5-2-智能剪辑节点.png', 'M-386-智能剪辑节点.png',
   标注=[(30, 42, 1, 蓝), (252, 182, 2, 橙), (45, 204, 3, 绿)],
   图例=[
       (1, 蓝, 'title + a number (see the manual for what it is)'),
       (2, 橙, 'empty state: connect a video node first'),
       (3, 绿, 'four ready-made starting points'),
       (4, 橙, 'the four presets, top to bottom'),
   ])

# ── M-387 逐帧拉片节点（图 412×480）
出('fq5-3-逐帧拉片节点.png', 'M-387-逐帧拉片节点.png',
   标注=[(45, 100, 1, 蓝), (240, 100, 2, 紫), (75, 215, 3, 绿), (35, 323, 4, 橙), (75, 400, 5, 红)],
   图例=[
       (1, 蓝, 'card title + a yellow diamond badge'),
       (2, 紫, 'model version badge: SD 2.5'),
       (3, 绿, 'upload dropzone (no file yet)'),
       (4, 橙, 'breakdown dimension: 3 pill buttons'),
       (5, 红, 'disabled: disabled=true cursor=not-allowed'),
       (6, 灰, 'NOTE opacity stays 1.00 -- grey is NOT a fade'),
   ])

# ── M-388 脚本生成器节点（图 442×442）
出('fq5-1-脚本V2节点.png', 'M-388-脚本生成器节点.png',
   标注=[(35, 42, 1, 蓝), (35, 204, 2, 橙), (70, 246, 3, 绿), (70, 285, 4, 绿), (70, 324, 5, 紫)],
   图例=[
       (1, 蓝, 'node title  (class = node-script-v2)'),
       (2, 橙, 'three ways in'),
       (3, 绿, 'plot -> shot breakdown script'),
       (4, 绿, 'characters -> shot breakdown script'),
       (5, 紫, 'write the script yourself -> full-screen table'),
       (6, 灰, 'all three are ENTRY points, not submit buttons'),
   ])
print('done')
