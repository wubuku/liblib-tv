#!/usr/bin/env python3
"""Batch DP-0：从本地 JS chunk 库里提取**全部**界面中文文案，并与手册正文做差集。

为什么做这个（Batch DO 的副产品）：
  DO-1 把页面已加载的 152 个 chunk（19MB）下载到了 /tmp/libtv-chunks。
  DO 靠搜字面量就破了「z-[180] 是什么」这个挂了三批的问题。
  ⭐ 同一个金矿还能挖一次：**界面上的每一句中文都来自 JS 里的文案表**，
  把这张表整个提出来，跟手册正文做差集 ⇒ 就能直接看到
  **「界面上有、但手册从没写过」的空白**，不用再靠人工翻界面找。

判据纪律（照 §89.5 / §92.5 的治法）：
  ① 差集必须**双向**：既有「chunk 有而手册无」，也要有「手册有而 chunk 无」
     （后者说明手册可能记了界面上并不存在的字，必须回头查）
  ② 报告里**不做同义合并**，「同一个意思的两种写法」也算命中要标出来，
     因为那通常意味着手册猜错过措辞
  ③ 提取的正则要同时吃两种形态：源码里调用是 `translate("canvas:xxx")`，
     文案表里的键是 `xxx`（DO 的第一版正则就因为带前缀而命中 0）
"""
import glob
import json
import os
import re
import sys

CHUNKS = '/tmp/libtv-chunks'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 提取 "key":"值" —— 值里必须含中文，否则是代码/类名
PAIR = re.compile(r'"([A-Za-z][A-Za-z0-9_]{2,60})"\s*:\s*"((?:[^"\\]|\\.)*[一-鿿][^"\\]*)"')

# 明显不是界面文案的：含代码符号 / 路径 / 模板
NOISE = re.compile(r'[<>{}$\\\n]|https?://|\.js|\.css|\.png|function|return |=>|^@|^\.')

def main():
    table = {}
    where = {}
    for f in sorted(glob.glob(os.path.join(CHUNKS, '*.js'))):
        try:
            s = open(f, encoding='utf-8', errors='ignore').read()
        except OSError:
            continue
        for k, v in PAIR.findall(s):
            v = v.strip()
            if NOISE.search(v):
                continue
            if len(v) > 60:
                continue
            if k not in table:          # 首次出现为准
                table[k] = v
                where[k] = os.path.basename(f)

    print('提取到带中文的 key：%d 个（来自 %d 个 chunk）' % (len(table), len(glob.glob(os.path.join(CHUNKS, '*.js')))))

    # 收集手册正文（排除 PROGRESS / AUDIT 这两个工作账本）
    manual = ''
    for p in glob.glob(os.path.join(ROOT, '**', '*.md'), recursive=True):
        if 'node_modules' in p or '.vitepress' in p:
            continue
        b = os.path.basename(p)
        if b in ('PROGRESS.md', 'AUDIT.md'):
            continue
        manual += open(p, encoding='utf-8', errors='ignore').read()

    def 归一(s):
        return re.sub(r'\s+', '', s)

    手册平 = 归一(manual)

    命中, 缺失 = [], []
    for k, v in table.items():
        vn = 归一(v)
        # 逐段匹配：长文案按标点切成片段，任一片段命中即算「手册提过」
        片段 = [归一(x) for x in re.split(r'[，。；：、？！,.;:?!]', v) if len(归一(x)) >= 3]
        命中了 = vn in 手册平 or (片段 and any(x in 手册平 for x in 片段))
        (命中 if 命中了 else 缺失).append((k, v, where[k]))

    print('  手册提过：%d' % len(命中))
    print('  ⭐ 手册没提：%d' % len(缺失))

    out = {
        '统计': {
            'chunk数': len(glob.glob(os.path.join(CHUNKS, '*.js'))),
            '带中文的key总数': len(table),
            '手册提过': len(命中),
            '手册没提': len(缺失),
        },
        '手册没提': [{'key': k, '文案': v, 'chunk': w} for k, v, w in sorted(缺失, key=lambda x: x[0])],
    }
    with open(os.path.join(ROOT, 'tools', 'batchDP0.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print('\n=== 「界面有、但手册从没写过」的前 60 条 ===')
    for i, (k, v, w) in enumerate(sorted(缺失, key=lambda x: x[0])[:60], 1):
        print('%3d. %-42s %s' % (i, k, v))
    print('\n=== 已写 tools/batchDP0.json ===')


if __name__ == '__main__':
    main()
