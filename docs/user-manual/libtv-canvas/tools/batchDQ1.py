#!/usr/bin/env python3
"""Batch DQ-1：**反向核对** —— 手册里声称是「界面原文」的那些字，在 JS chunk 里搜得到吗？

⭐ DP 批只做了一个方向：「chunk 有、而手册没写」。
本步做**反方向**：「手册写了、而 chunk 里搜不到」。

⚠️ 这个方向的价值特别大：搜不到的，**要么是手册记错了**（界面根本没这字），
要么是别的原因（文案在别的 chunk / 由变量拼接 / 来自服务端 i18n）。
**两种都需要人工过一遍。**

判据纪律（照 §93.5）：
  ① **只取「明确声称是界面原文」的中文**：`「…」` 或反引号包裹、含中文、长度 2~24。
     ⛔ 排除：节点名、卡名、作者名、分类名、文件名、本手册自造的标签 —— 
        这些不是界面固定文案，搜不到是正常的。
  ② 搜的范围是**全部 chunk 全文**（151 个文件），命中即通过
  ③ **不合并同义**：逐条独立判断，因为「两个写法只有一个对」正是要找的错误
  ④ 输出分三档：搜得到 / 搜不到但可疑 / 搜不到且像专有名词（正常）
"""
import glob
import os
import re
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHUNKS = sorted(glob.glob('/tmp/libtv-chunks/*.js'))

# 把全部 chunk 拼成一个大字符串（19MB，一次读入够快）
CORPUS = []
for f in CHUNKS:
    try:
        CORPUS.append(open(f, encoding='utf-8', errors='ignore').read())
    except OSError:
        pass
ALL = '\n'.join(CORPUS)
print('chunk 库：%d 个文件，%.1f MB' % (len(CORPUS), len(ALL) / 1024 / 1024))

# 提取手册正文（排除工作账本）
手册 = []
for p in glob.glob(os.path.join(ROOT, '**', '*.md'), recursive=True):
    if 'node_modules' in p or '.vitepress' in p:
        continue
    if os.path.basename(p) in ('PROGRESS.md', 'AUDIT.md'):
        continue
    手册.append((os.path.relpath(p, ROOT), open(p, encoding='utf-8', errors='ignore').read()))

# 候选：中文 + 引号包裹，长度 2~24
QUOTE = re.compile(r'[「『]([^「」『』\n]{2,24})[」』]')
BACKT = re.compile(r'`([^`\n]{2,24})`')
CJK = re.compile(r'[一-鿿]')

候选 = Counter()
出处 = {}
for name, text in 手册:
    for pat in (QUOTE, BACKT):
        for m in pat.finditer(text):
            s = m.group(1).strip()
            if not CJK.search(s):
                continue
            # 排除明显不是界面文案的
            if s.startswith(('**', '📖', '⛔', '⭐')) or s.endswith(('**', '、')):
                continue
            候选[s] += 1
            出处.setdefault(s, set()).add(name)

print('手册里的中文引号/反引号内容：%d 条（去重）' % len(候选))

命中, 未命中 = [], []
for s, n in 候选.items():
    (命中 if s in ALL else 未命中).append((s, n, sorted(出处[s])))

print('  在 chunk 里搜到：%d' % len(命中))
print('  ⭐ 搜不到：%d' % len(未命中))

# 未命中里再分类：像专有名词/长句的，多半是手册自造的描述，不是界面文案
专有 = re.compile(r'^(素材-|Group |节点$)|^M-\d|^[a-z]+-[a-z]+')
描述 = []
可疑 = []
for s, n, src in sorted(未命中, key=lambda x: -x[1]):
    # 界面文案通常短、含动词或名词性短语；带空格/句号/逗号的多半是描述句
    if re.search(r'[，。；、]| |^#|^\*', s) or len(s) > 14:
        描述.append((s, n, src))
    else:
        可疑.append((s, n, src))

print('\n=== A 档：搜不到、且长得像**界面文案**（重点复核对象）%d 条 ===' % len(可疑))
for s, n, src in 可疑:
    print('  「%s」 ×%d  ← %s' % (s, n, ', '.join(x.split('/')[-1] for x in src)))

print('\n=== B 档：搜不到、但更像描述句/专有名词（多半正常）%d 条，只列前 25 ===' % len(描述))
for s, n, src in 描述[:25]:
    print('  「%s」 ×%d' % (s, n))
if len(描述) > 25:
    print('  … 还有 %d 条' % (len(描述) - 25))
