#!/usr/bin/env python3
"""stale-scan.py —— 全树「过期副本扫描器」：找出「结论早已结案、别处还标着 📖/旧数字」的正文副本。

⭐ 起因（Batch DZ）：DZ 批只在 `asset-library.md` 里**手工**抓到 6 处
  「结论早就改了、正文没跟」的过期副本。那是**运气**，不是方法。
  本脚本把方法固化成可复跑工具：

  对每一个带 📖 的段落，检查它附近是否出现**已结案结论的关键词**。
  出现 ⇒ 说明这一处的「📖 没验」其实**已经有答案了** ⇒ 候选过期副本。

⭐ 关键词表来自 DR / DS / DU / DV / DW / DX / DY / DZ / EA 各批已结案的结论。
  ⭐ **关键词表本身要能维护** —— 每批新增结案结论就往 `已结案` 里加一条，
     然后 `python3 tools/stale-scan.py` 一键复扫整棵树。

⚠️ 本脚本**只产出候选，不自动改**：上下文判定仍有歧义，
    「附近有 runCount」不等于「这句 📖 说的是 runCount」（§256 教训）。
⇒ 输出后必须**逐条回读上下文**再决定改不改。
  「命中」只是**候选**，绝大多数是「附近恰好有关键词、但那句 📖 说的是别的事」。
"""
import glob
import json
import os
import re

ROOT = '/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/user-manual/libtv-canvas'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stale-scan.json')

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
    # ⭐⭐ EC 批新增：i18n 表里「界面上找不到」的 key —— 去渲染代码数引用数，
    #    0 处 = 僵尸 key（压根没被用），>0 = 真有 UI（是我找错地方了）。
    'canvasStoreDelete': 'EC：⛔ 不是菜单文案，是 store 记操作日志时传给 translate 的字符串',
    'canvasStoreDelete2': 'EC：⛔ 同上（批量版 deleteEdgesBatch）',
    'zoomTo200': 'EB：僵尸 key，渲染代码 0 处引用，界面永不出现',
    'zoomReset': 'EB：僵尸 key，渲染代码 0 处引用，界面永不出现',
    'disconnectEdgeTitle': 'EC：断开连线确认框文案，属另一条代码路径，界面未捕捉到 📖',
    'disconnectConfirmText': 'EC：确定断开，同上',
    'openingDeleteNodeConfirm': 'EE：僵尸 key，删除节点路径用的是 deleteNodeConfirmText，界面永不出现',
    'openingDeleteNodeCancel': 'EE：僵尸 key，同上（删除节点用的是 common:cancel）',
}

# ---------- ⭐⭐ 已被推翻的**具体值**：这些字面本身就该从正文消失 ----------
# 命中 ⇒ 要么是「已加删除线/作废标注」的正确写法，要么是**真残留**（需逐条看）。
作废值 = {
    'runCount = 1100': 'DU：⛔ 1.1w 对应 10700，1100 是千字口径（作废）',
    'runCount = 4200': 'DU：⛔ 4.2w 对应 42300，4200 是千字口径（作废）',
    '58 个字段': 'DU/DX：⛔ 应为 63',
    '58 个顶层字段': 'DU/DX：⛔ 应为 63',
}

标记 = re.compile(r'📖')
文件 = []
for p in sorted(glob.glob(os.path.join(ROOT, '*.md'))
                + glob.glob(os.path.join(ROOT, '10-tasks', '*.md'))):
    if os.path.basename(p) in ('PROGRESS.md',):
        continue
    文件.append(p)

候选 = []
统计 = {'带📖的文件': 0, '带📖的段落': 0, '命中候选': 0}
for p in 文件:
    text = open(p, encoding='utf-8', errors='ignore').read()
    rel = os.path.relpath(p, ROOT)

    # ── 扫描 2：作废旧值（不看有没有 📖，整段整行都算）──
    for bad, why in 作废值.items():
        for mt in re.finditer(re.escape(bad), text):
            s = text.rfind('\n', 0, mt.start()) + 1
            e = text.find('\n', mt.end())
            line = text[max(s, mt.start() - 200):e if e > 0 else len(text)]
            候选.append({
                '类型': '作废旧值', '文件': rel, '行': text[:mt.start()].count('\n') + 1,
                '命中': [bad], '说明': why,
                '原文': re.sub(r'\s+', ' ', line).strip()[:300],
            })

    if not 标记.search(text):
        continue
    统计['带📖的文件'] += 1
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
            '类型': '📖旁有已结案关键词', '文件': rel, '行': line_no,
            '命中关键词': 命中,
            '对应已结案结论': [已结案[k] for k in 命中],
            '原文': re.sub(r'\s+', ' ', para)[:300],
        })

print('带 📖 的文件：%d 个' % 统计['带📖的文件'])
print('带 📖 的段落：%d 段' % 统计['带📖的段落'])
print('⭐ 其中**命中已结案关键词**的候选：%d 段' % 统计['命中候选'])
print('\n' + '=' * 76)
for c in 候选:
    print('\n─── [%s] %s:%d ───' % (c['类型'], c['文件'], c['行']))
    print('  命中: %s' % '、'.join(c.get('命中关键词') or c.get('命中')))
    for s in c.get('对应已结案结论') or [c.get('说明', '')]:
        print('        ↳ %s' % s)
    print('  原文: %s' % c['原文'])

json.dump({'统计': 统计, '候选': 候选, '关键词表': 已结案, '作废值表': 作废值},
          open(OUT, 'w'), ensure_ascii=False, indent=2)
print('\n=== 已写 tools/stale-scan.json ===')
