#!/usr/bin/env python3
"""Batch EA-1：把 DZ 批的纪律扩到**全树** —— 扫出「结论早已结案、别处还标着 📖」的副本。

⭐ DZ 批只在 `asset-library.md` 里手工抓到 6 处过期副本。那是**运气**，
不是方法。本步把方法固化成脚本：

  对每一个带 📖 的行/段，检查它附近是否出现**已结案结论的关键词**。
  出现 ⇒ 说明这一处的「📖 没验」其实**已经有答案了** ⇒ 候选过期副本。

⭐ 关键词表来自 DR / DS / DU / DV / DW / DX / DY / DZ 各批已结案的结论。
  ⭐ **关键词表本身要能维护** —— 每批新增结案结论就往里加一条。

⚠️ 本脚本**只产出候选，不自动改**：上下文判定仍有歧义，
    「附近有 runCount」不等于「这句 📖 说的是 runCount」（§256 教训）。
⇒ 输出后必须**逐条回读上下文**再决定改不改。
"""
import glob
import json
import os
import re

ROOT = '/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/user-manual/libtv-canvas'

# ---------- 已结案结论的关键词 → 它对应的批次 ----------
已结案 = {
    'runCount': 'DU/DV/DX：卡面数字 = 被使用次数，99 样本，缩写规则 14/14',
    '万字口径': 'DU：缩写规则（<10000 原样，≥10000 四舍五入 1 位小数 + w）',
    '1.1w': 'DU：1.1w 对应 10700（早期记的 1100 是千字口径，作废）',
    '738': 'DR：风格插画不勾 = 738（阳性对照）',
    '681': 'DR：勾上 = 681，被筛掉 96',
    '仅看可商用': 'DR：筛除量已测出（738→681）',
    '其余适配模型': 'DS：多模型卡已测到（M-353，4 项）',
    'baseType': 'DS/DT：长度 = 适配模型数，分布 80/22/5/1/7/6',
    '生成内容可商用': 'DS：已在界面上见过（M-353）',
    '首选推荐模型': 'DS：源码+界面双向确认',
    '全部适配模型': 'DT：baseType 个数 = 下拉行数，一对一',
    '当前使用': 'DT：广场里不出现（带阳性对照的可信阴性）',
    '特效广场': 'DW/DX：是独立广场，页签第一项不同，走 video/stream',
    'model/video/stream': 'DX：特效广场的接口',
    'model/feed/stream': 'DX：风格广场的接口',
    '协作': 'DW：横幅 4 层祖先链，opacity 连乘后为 0 ⇒ 不可见',
    'z-[180]': 'DO：= collab-follow-border（跟随边框）',
    'z-[305]': 'DO/DW：= collab-follow-banner，常驻但 opacity:0',
    '没有更多了': 'DP：i18n key = noMore',
    '63 个字段': 'DU/DX：卡记录顶层 63 个字段（早期记的 58 作废）',
    '58 个字段': 'DU/DX：⛔ 这个数是错的，应为 63',
}

标记 = re.compile(r'📖')
文件 = []
for p in sorted(glob.glob(os.path.join(ROOT, '*.md')) + glob.glob(os.path.join(ROOT, '10-tasks', '*.md'))):
    if os.path.basename(p) in ('PROGRESS.md',):
        continue
    文件.append(p)

候选 = []
统计 = {'带📖的文件': 0, '带📖的段落': 0, '命中候选': 0}
for p in 文件:
    text = open(p, encoding='utf-8', errors='ignore').read()
    if not 标记.search(text):
        continue
    统计['带📖的文件'] += 1
    rel = os.path.relpath(p, ROOT)
    # 按段落切（空行分隔）
    for para in re.split(r'\n\s*\n', text):
        if not 标记.search(para):
            continue
        统计['带📖的段落'] = 统计.get('带📖的段落', 0) + 1
        命中 = [k for k in 已结案 if k in para]
        if not 命中:
            continue
        统计['命中候选'] += 1
        line_no = text[:text.find(para)].count('\n') + 1
        候选.append({
            '文件': rel, '行': line_no,
            '命中关键词': 命中,
            '对应已结案结论': [已结案[k] for k in 命中],
            '原文': re.sub(r'\s+', ' ', para)[:300],
        })

print('带 📖 的文件：%d 个' % 统计['带📖的文件'])
print('带 📖 的段落：%d 段' % 统计['带📖的段落'])
print('⭐ 其中**命中已结案关键词**的候选：%d 段' % 统计['命中候选'])
print('\n' + '=' * 76)
for c in 候选:
    print('\n─── %s:%d ───' % (c['文件'], c['行']))
    print('  命中: %s' % '、'.join(c['命中关键词']))
    for s in c['对应已结案结论']:
        print('        ↳ %s' % s)
    print('  原文: %s' % c['原文'])

json.dump({'统计': 统计, '候选': 候选, '关键词表': 已结案},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'batchEA1.json'), 'w'),
          ensure_ascii=False, indent=2)
print('\n=== 已写 tools/batchEA1.json ===')
