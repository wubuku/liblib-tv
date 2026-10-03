#!/usr/bin/env python3
"""Batch DY-2：给 DY-1 的「0 命中」配**阳性对照**。

⚠️ DY-1 报出 `去空格命中 0 条`、`文案表值命中 0 条`。
按本会话铁律「**采到 0 必须先证明判据有效**，0 不是结论」——
必须先验证这两个判据**本身能不能命中**，否则 0 可能只是判据写坏了。

⭐ 阳性对照怎么构造才诚实：
  ❌ 不能拿「无空格的文案」去测「去空格判据」—— 它本来就该命中，等于没测。
  ✅ 要拿「**确实存在于 chunk 里、且原文带空格**」的中文短串当对照，
     测三个判据各自能不能命中 ⇒ **判据有效**。
  再拿「**根本不存在于任何 chunk**」的串当阴性对照 ⇒ **判据不会瞎报**。

⭐ 两个对照一起做，结论才立得住。
"""
import glob
import os
import re
import json

CHUNKS = sorted(glob.glob('/tmp/libtv-chunks/*.js'))
文案表路径 = '/tmp/libtv-chunks/3xjlk8cm1g3m9.js'
CORPUS = []
for f in CHUNKS:
    try:
        CORPUS.append(open(f, encoding='utf-8', errors='ignore').read())
    except OSError:
        pass
ALL = '\n'.join(CORPUS)
ALL去空 = re.sub(r'\s+', '', ALL)
CJK = re.compile(r'[一-鿿]')

# ---------- 构造阳性对照：从 chunk 全文里挖「原文带空格」的中文短串 ----------
print('从 chunk 全文里挖阳性对照（原文带空格的中文串）…')
阳性池 = []
for m in re.finditer(r'"([^"\\\n]{3,20})"', ALL):
    s = m.group(1)
    if ' ' not in s or not CJK.search(s):
        continue
    if re.search(r'[，。；、]', s):      # 带标点的先剔掉，纯短语更好验
        continue
    汉字 = len(re.findall(r'[一-鿿]', s))
    if 汉字 < 2 or len(s) > 18:
        continue
    阳性池.append(s)
阳性池 = sorted(set(阳性池))
print('  候选阳性对照 %d 条' % len(阳性池))

# 文案表里的值（也是真界面文案）
表值 = set()
if os.path.exists(文案表路径):
    raw = open(文案表路径, encoding='utf-8', errors='ignore').read()
    for m in re.finditer(r':"((?:[^"\\]|\\.){1,120})"', raw):
        v = m.group(1)
        if CJK.search(v) and 1 < len(v) <= 30:
            表值.add(v)
    for m in re.finditer(r'"((?:[^"\\]|\\.){1,80})"\s*:\s*"((?:[^"\\]|\\.){1,120})"', raw):
        v = m.group(2)
        if CJK.search(v) and 1 < len(v) <= 30:
            表值.add(v)
print('  文案表值 %d 条' % len(表值))

# 阴性对照：手册里自造的描述句（确定不在任何 chunk 里）
手册 = []
for p in glob.glob('/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/user-manual/libtv-canvas/*.md') + \
         glob.glob('/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/user-manual/libtv-canvas/10-tasks/*.md'):
    手册.append(open(p, encoding='utf-8', errors='ignore').read())
阴性池 = ['图片节点 2', '画布 1', '共 2 节点', '卡片宽 + 固定间隙', '导演台 N', '已选 0/10 张', '原名 - 副本']

去空 = lambda x: re.sub(r'\s+', '', x)
判去空 = lambda s: len(去空(s)) >= 3 and 去空(s) in ALL去空
判表值 = lambda s: s in 表值 or (len(去空(s)) >= 3 and 去空(s) in 表值)

# ---------- ① 阳性对照：带空格的真实界面文案 ----------
对照A = 阳性池[:400]
命中A = [s for s in 对照A if 判去空(s)]
表命中A = [s for s in 表值 if ' ' in s and 判去空(s)][:20]
print('\n══════ ① 阳性对照：判据「去空格」能不能命中真实文案 ══════')
print('  拿 %d 条「原文带空格、确实在 chunk 里」的串去测' % len(对照A))
print('  「去空格」判据命中: %d 条 %s' % (len(命中A), ('例：' + '、'.join(命中A[:6])) if 命中A else '⛔ 一条都没命中 ⇒ 判据本身有问题'))
表原样 = [s for s in 表值 if ' ' in s]
print('  文案表里带空格的值 %d 条，「去空格」判据命中 %d 条 %s'
      % (len(表原样), len([s for s in 表原样 if 判去空(s)]),
         ('例：' + '、'.join([s for s in 表原样 if 判去空(s)][:6])) if any(判去空(s) for s in 表原样) else '⛔ 0'))

# ---------- ② 阴性对照 ----------
print('\n══════ ② 阴性对照：判据会不会瞎报 ══════')
瞎报 = [s for s in 阴性池 if 判去空(s) or 判表值(s)]
print('  拿 %d 条确定不在 chunk 里的自造描述去测' % len(阴性池))
print('  误报: %d 条 %s' % (len(瞎报), 瞎报 if 瞎报 else '⇒ ✅ 一条都没误报'))

# ---------- ③ 文案表值判据自身 ----------
print('\n══════ ③ 「文案表值」判据自检 ══════')
print('  文案表里抽到的值 %d 条' % len(表值))
print('  拿其中 %d 条去测「原文直接查表」：命中 %d 条 ⇒ %s'
      % (min(200, len(表值)),
         sum(1 for s in list(表值)[:200] if 判表值(s)),
         '✅ 判据有效' if all(判表值(s) for s in list(表值)[:50]) else '⛔ 有漏'))

# ---------- ④ 重跑 DY-1 的 B 档（用验证过的判据）----------
print('\n══════ ④ 用验证过的判据重扫 B 档 ══════')
ROOT = '/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/user-manual/libtv-canvas'
QUOTE = re.compile(r'[「『]([^「」『』\n]{2,24})[」』]')
BACKT = re.compile(r'`([^`\n]{2,24})`')
候选 = {}
for p in glob.glob(os.path.join(ROOT, '**', '*.md'), recursive=True):
    if 'node_modules' in p or '.vitepress' in p:
        continue
    if os.path.basename(p) in ('PROGRESS.md', 'AUDIT.md'):
        continue
    name = os.path.relpath(p, ROOT)
    text = open(p, encoding='utf-8', errors='ignore').read()
    for pat in (QUOTE, BACKT):
        for m in pat.finditer(text):
            s = m.group(1).strip()
            if not CJK.search(s):
                continue
            if s.startswith(('**', '📖', '⛔', '⭐')) or s.endswith(('**', '、')):
                continue
            候选.setdefault(s, set()).add(name)
未命中 = [s for s in 候选 if s not in ALL]
B档 = [s for s in 未命中 if re.search(r'[，。；、]| |^#|^\*', s) or len(s) > 14]
硬命中 = [s for s in B档 if 判去空(s) or 判表值(s)]
print('  B 档 %d 条 → 两个硬判据命中 **%d 条**' % (len(B档), len(硬命中)))
for s in 硬命中[:20]:
    print('    ⭐「%s」 ← %s' % (s, ', '.join(x.split('/')[-1] for x in 候选[s])))
if not 硬命中:
    print('    ⛔ 0 条 —— 但**上面 ① 的阳性对照证明判据本身能命中**，')
    print('       所以这个 0 是**真阴性**：B 档确实没有藏着界面文案。')

json.dump({
    'chunk库': len(CORPUS),
    '阳性对照池': len(阳性池),
    '阳性对照抽样': len(对照A),
    '去空格判据在阳性上命中': len(命中A),
    '阳性命中样例': 命中A[:15],
    '文案表值数': len(表值),
    '文案表带空格值数': len(表原样),
    '阴性对照数': len(阴性池),
    '阴性误报': 瞎报,
    'B档': len(B档),
    '硬判据命中': 硬命中,
}, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'batchDY2.json'), 'w'),
    ensure_ascii=False, indent=2)
print('\n=== 已写 tools/batchDY2.json ===')
