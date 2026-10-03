#!/usr/bin/env python3
"""Batch DP-1：把「素材库 / 节点 / 广场」这几族文案从 chunk 里精确抽出来。

ⓘ DP-0 给了 7508 条，但范围太宽。DO 破 `z-[180]` 靠的是**定位到调用点**，
这回同样：**先圈定 key 族，再看渲染代码**，不靠猜。
"""
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAIRS = re.compile(r'"([A-Za-z][A-Za-z0-9_]{2,60})"\s*:\s*"((?:[^"\\]|\\.)*)"')

# 只取**画布素材库这一块**的 key 族（DO 的渲染代码里它们同处一个文案表）
族前缀 = ('material', 'style', 'lens', 'commercial', 'model', 'preferred', 'other',
          'allAdapted', 'currentlyInUse', 'search', 'addStyle', 'addLens', 'selectStyle',
          'selectLens', 'replaceLens', 'loadingMore', 'allLoaded', 'sref', 'copySref')
# 以及节点 / 连线 / 画布本体
族前缀 += ('node', 'canvas', 'connect', 'disconnect', 'group', 'align', 'snap',
           'rating', 'lock', 'copy', 'paste', 'rename', 'remove', 'edge', 'port')

out = {}
for f in sorted(glob.glob('/tmp/libtv-chunks/*.js')):
    s = open(f, encoding='utf-8', errors='ignore').read()
    for k, v in PAIRS.findall(s):
        if not any(k.startswith(p) or p in k for p in 族前缀):
            continue
        if not re.search(r'[一-鿿]', v):
            continue
        if re.search(r'[<>{}$\\]|https?://|=>', v):
            continue
        if len(v) > 70:
            continue
        out.setdefault(k, {'文案': v, 'chunk': os.path.basename(f)})

print('素材库/节点/画布 相关 key：%d 条\n' % len(out))
for k in sorted(out):
    print('  %-44s %s' % (k, out[k]['文案']))

json.dump(out, open(os.path.join(ROOT, 'tools', 'batchDP1.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('\n=== 已写 tools/batchDP1.json ===')
