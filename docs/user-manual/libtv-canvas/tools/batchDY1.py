#!/usr/bin/env python3
"""Batch DY-1：把反向核对的 **B 档 370 条**收敛掉。

DQ-1 做了反向核对（手册写了、chunk 里搜不到），输出三档：
  · 搜得到 → 通过
  · ⭐ A 档：搜不到、但**长得像界面文案**（短、无空格）—— DQ 批逐条过了，抓到 `缩放至800%`
  · ⭐ **B 档：搜不到、且带空格/标点或长度 > 14 ⇒「多半是描述句」，370 条从未逐条过**

⚠️ §232 记的判据缺陷：**B 档是「多半正常」而不是「已确认正常」**。
「带空格所以像描述句」是**形态学猜测**，不是证据 —— 万一某条界面文案
本身就带空格（多词短语）呢？本步就是去把这类漏网的捞出来。

⭐⭐ 本步给 B 档加 **DQ 批没有的三个独立判据**：

  ① **去空格检索**：界面文案在 chunk 里可能写成 `"全 角适配"` 也可能 `"全角适配"`。
     DQ-1 只做原文连续匹配 ⇒ 带空格的短语会**假阴性**。
  ② ⭐⭐ **文案表值检索**（最硬）：`3xjlk8cm1g3m9.js` 是 **key → 中文** 的完整文案表。
     若某短语作为**值**出现在文案表里 ⇒ 它**一定是真实界面文案**，
     哪怕它不在渲染 chunk、不在任何调用点。
  ③ ⭐ **上下文判据**：只看它出现的那句话**有没有声称是界面原文**
     （附近出现「界面上」「文案」「按钮上」「写着」这类词）。
     没声称的 ⇒ 本来就是本手册自造的描述，搜不到**完全正常**，直接出局。

⇒ 三条都判「不是界面文案」的，才算 B 档结清。
"""
import glob
import os
import re
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHUNKS = sorted(glob.glob('/tmp/libtv-chunks/*.js'))
文案表 = '/tmp/libtv-chunks/3xjlk8cm1g3m9.js'

CORPUS = []
for f in CHUNKS:
    try:
        CORPUS.append(open(f, encoding='utf-8', errors='ignore').read())
    except OSError:
        pass
ALL = '\n'.join(CORPUS)
print('chunk 库：%d 个文件，%.1f MB' % (len(CORPUS), len(ALL) / 1024 / 1024))

手册 = []
for p in glob.glob(os.path.join(ROOT, '**', '*.md'), recursive=True):
    if 'node_modules' in p or '.vitepress' in p:
        continue
    if os.path.basename(p) in ('PROGRESS.md', 'AUDIT.md'):
        continue
    手册.append((os.path.relpath(p, ROOT), open(p, encoding='utf-8', errors='ignore').read()))

QUOTE = re.compile(r'[「『]([^「」『』\n]{2,24})[」』]')
BACKT = re.compile(r'`([^`\n]{2,24})`')
CJK = re.compile(r'[一-鿿]')

候选 = Counter()
出处 = {}
上下文 = {}
for name, text in 手册:
    for pat in (QUOTE, BACKT):
        for m in pat.finditer(text):
            s = m.group(1).strip()
            if not CJK.search(s):
                continue
            if s.startswith(('**', '📖', '⛔', '⭐')) or s.endswith(('**', '、')):
                continue
            候选[s] += 1
            出处.setdefault(s, set()).add(name)
            上下文.setdefault(s, set()).add(text[max(0, m.start() - 160):m.end() + 120])

print('手册里的中文引号/反引号内容：%d 条（去重）' % len(候选))

未命中 = [(s, n) for s, n in 候选.items() if s not in ALL]
print('  在 chunk 里搜到：%d' % (len(候选) - len(未命中)))
print('  ⭐ 搜不到：%d' % len(未命中))

# 复刻 DQ-1 的 A/B 分档
B档 = []
for s, n in sorted(未命中, key=lambda x: -x[1]):
    if re.search(r'[，。；、]| |^#|^\*', s) or len(s) > 14:
        B档.append((s, n))
print('\n=== B 档（沿用 DQ-1 判据）%d 条 ===' % len(B档))

# ---------- 判据 ②：文案表值检索 ----------
表值 = set()
if os.path.exists(文案表):
    raw = open(文案表, encoding='utf-8', errors='ignore').read()
    for m in re.finditer(r'"((?:[^"\\]|\\.){1,80})"\s*:\s*"((?:[^"\\]|\\.){1,120})"', raw):
        v = m.group(2)
        if CJK.search(v):
            表值.add(v)
    # 也收 `"key":"中文"` 这种相邻写法
    for m in re.finditer(r':"((?:[^"\\]|\\.){1,120})"', raw):
        v = m.group(1)
        if CJK.search(v):
            表值.add(v)
print('文案表里抽到的中文值：%d 条' % len(表值))

# ---------- 判据 ①：去空格检索 ----------
去空 = lambda x: re.sub(r'\s+', '', x)
ALL去空 = re.sub(r'\s+', '', ALL)

# ---------- 判据 ③：上下文是否声称是界面原文 ----------
声称词 = re.compile(r'界面上|文案|按钮上|写着|读数|原文|逐字|悬停提示|提示语|aria-label|title=')

真信号 = []
出局 = []
for s, n in B档:
    判 = []
    紧凑 = 去空(s)
    if len(紧凑) >= 3 and 紧凑 in ALL去空:
        判.append('去空格命中')
    if s in 表值 or (len(紧凑) >= 3 and 紧凑 in 表值):
        判.append('文案表值命中')
    声称 = any(声称词.search(c) for c in 上下文.get(s, set()))
    if 声称:
        判.append('上下文声称界面原文')
    if 判:
        真信号.append((s, n, 判, sorted(出处[s])))
    else:
        出局.append((s, n, sorted(出处[s])))

print('\n' + '=' * 68)
print('⭐ 三判据命中（B 档里的真信号）%d 条' % len(真信号))
for s, n, 判, src in 真信号:
    print('  「%s」 ×%d  ← %s' % (s, n, ' / '.join(判)))
    print('      出现在: %s' % ', '.join(x.split('/')[-1] for x in src))

print('\n出局的 %d 条：三条判据都判「不是界面文案」⇒ 搜不到完全正常' % len(出局))
print('（前 20 条抽样，确认它们确实是本手册自造的描述）')
for s, n, src in 出局[:20]:
    print('  「%s」 ×%d  ← %s' % (s, n, ', '.join(x.split('/')[-1] for x in src)))

# 落盘
import json
json.dump({
    'chunk库': len(CORPUS),
    '候选总数': len(候选),
    '未命中': len(未命中),
    'B档': len(B档),
    '文案表值数': len(表值),
    '真信号': [{'文本': s, '次数': n, '判据': j, '出处': src} for s, n, j, src in 真信号],
    '出局数': len(出局),
    '出局样本': [{'文本': s, '次数': n, '出处': src} for s, n, src in 出局[:40]],
}, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'batchDY1.json'), 'w'),
    ensure_ascii=False, indent=2)
print('\n=== 已写 tools/batchDY1.json ===')
