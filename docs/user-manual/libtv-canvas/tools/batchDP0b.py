#!/usr/bin/env python3
"""Batch DP-0b：把 DP-0 的 7508 条按**前缀族群**切开，圈出属于「画布」的那几族。

为什么要再切一刀：DP-0 直接拿整站 chunk 跟画布手册做差集，
结果 6015 条「手册没提」里绝大多数是**账户/团队/会员/Access key/发票** ——
它们根本不属于画布手册的范围。⇒ **差集本身没错，是范围没圈定。**

⭐ 判断一个 key 是否属于画布，靠它**前缀的语义族**，不靠猜：
  `canvas*` `collab*` `node*` `storyboard*` `director*` `asset*` `generate*`
  `workflow*` `character*` `model*` `agent*` `toolbox*` `script*` `audio*` …
先统计每个前缀族的量与代表文案，再决定哪些族进范围。
"""
import json
import os
import re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, 'tools', 'batchDP0.json'), encoding='utf-8'))
缺 = d['手册没提']

# 取 key 的第一个「词」：驼峰/下划线都切
def 词(k):
    parts = re.split(r'[A-Z_]', k)
    return (parts[0] or k[:6]).lower()

族 = defaultdict(list)
for r in 缺:
    族[词(r['key'])].append(r)

print('%-22s %5s  代表文案' % ('前缀族', '条数'))
print('-' * 92)
for name, rs in sorted(族.items(), key=lambda x: -len(x[1]))[:40]:
    样 = ' / '.join(x['文案'] for x in rs[:3])
    print('%-22s %5d  %s' % (name, len(rs), 样[:60]))

# 明确进「画布范围」的族
画布族前缀 = {
    'canvas', 'collab', 'node', 'storyboard', 'director', 'asset', 'generate',
    'workflow', 'character', 'model', 'agent', 'toolbox', 'script', 'audio',
    'image', 'video', 'text', 'group', 'line', 'connect', 'history', 'frame',
    'camera', 'skill', 'plugin', 'seedance', 'lora', 'task', 'tvd', 'prompt',
    'role', 'story', 'shot', 'edit', 'material', 'library', 'style', 'effect',
    'upload', 'download', 'rename', 'delete', 'copy', 'move', 'align', 'layer',
}
进范围 = {k: v for k, v in 族.items() if k in 画布族前缀}
print('\n=== 圈进「画布范围」的 %d 个族，合计 %d 条 ===' % (len(进范围), sum(len(v) for v in 进范围.values())))
for name in sorted(进范围, key=lambda x: -len(进范围[x])):
    print('  %-16s %4d' % (name, len(进范围[name])))

out = {'进范围族': {k: v for k, v in sorted(进范围.items())}}
json.dump(out, open(os.path.join(ROOT, 'tools', 'batchDP0b.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n=== 已写 tools/batchDP0b.json ===')
