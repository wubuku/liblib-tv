#!/usr/bin/env python3
"""Batch FV-1：普查文案表里所有**带插值占位符**的句子。

起因（Batch FU-3 顺手撞出来的）：`canvas:selectedCount` 的真身是
`已选择 {count} 项` —— 表里存的是**模板**，不是最终句子。

⭐ 为什么值得单独普查这类：
  手册正文里凡是写死「已选择 0 项」「共 1 节点」这种句子，
  都是**某一次的读数**，而产品真正给用户看的是带变量的模板。
  两者的差别不在措辞，在**它会随操作变**。
  ⇒ 一旦正文把某一句写死成「就是 0」，用户照着做就会对不上。

本脚本只读、幂等，正文里只准引用本脚本的输出（沿用 i18n-census.py 的规矩）。
"""
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENSUS = os.path.join(ROOT, 'tools', '.evidence', 'i18n-canvas.json')
OUT = os.path.join(ROOT, 'tools', '.evidence', 'i18n-interpolation.json')

# {name} / {{name}} 两种都算
PH = re.compile(r'\{+([A-Za-z_][A-Za-z0-9_]*)\}+')


def main():
    if not os.path.isfile(CENSUS):
        print(f'!! 找不到 {CENSUS}，先跑 i18n-census.py')
        return 1
    d = json.load(open(CENSUS, encoding='utf-8'))
    表 = d['表'] if '表' in d else d          # ⛔ 真表在 '表' 这一层（缺陷 485）

    命中 = []
    变量计数 = Counter()
    for k, v in 表.items():
        if not isinstance(v, str):
            continue
        vs = PH.findall(v)
        if not vs:
            continue
        变量计数.update(vs)
        命中.append({'key': k, '文案': v, '变量': vs})

    手册 = os.path.join(ROOT, '10-tasks', 'image-presets.md')
    print(f'全表 {len(表)} 条；带插值占位符的 **{len(命中)}** 条')
    print(f'出现过的变量共 **{len(变量计数)}** 种\n')
    print('变量出现次数（前 20）：')
    for name, c in 变量计数.most_common(20):
        print(f'  {name:<20} {c}')
    print('\n带「数字单位」的占位符（{count} / {number} / {time} 之类，最容易在正文被写死）：')
    带单位 = [h for h in 命中 if any(
        re.search(r'count|number|num|total|sum|len|size|amount|time|duration|price|credit|point', v, re.I)
        for v in h['变量'])]
    print(f'  共 {len(带单位)} 条，前 40：')
    for h in 带单位[:40]:
        print(f'  {h["key"]:<40} {h["文案"]}')

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({'总数': len(表), '带占位符': len(命中),
               '变量': dict(变量计数), '带单位': 带单位, '全部': 命中},
              open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f'\n明细已写入 {os.path.relpath(OUT, ROOT)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
