#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""复算「画布文案表」的全部数字。

为什么需要这个（Batch FQ-1）：
    FK（§141）把 8189 条文案抓下来后，把「≤14 字的短文案 6342 条」
    「手册一次都没出现的 4850 条」和 9 个分组条数**手抄**进了
    `20-reference.md`。重跑一遍发现：6342→6746、4850→4978，
    9 个分组条数里 **7 个错的**（scriptV2 记 42 实为 93、clip 记 89 实为 348、
    director 记 ~385 实为 859 …）。JSON 本身没变（各文件字节数与 FK 当年一致），
    是**当时算错了 / 手抄错了**。

⭐ 教训：能从一个落盘文件**重算出来**的数字，不该手抄进正文 ——
    正文里手抄的数字既会算错，也会随手册增补而过期
    （「手册没出现」这一项会随着每批新页而变化）。

用法：
    python3 tools/i18n-census.py              # 人读的表
    python3 tools/i18n-census.py --markdown   # 贴进 Markdown 的表格
    python3 tools/i18n-census.py --missing    # 列出 20 个最长的未出现短文案

⛔ 只读：不写任何文件、不联网。
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TABLE = os.path.join(HERE, '.evidence', 'i18n-canvas.json')

# 口径写死在这里，正文里只准引用本脚本的输出。
SHORT_MAX = 14  # 「短文案」的字数上限（含标点，不含空格）

# 正文里出现过的分组。写死的目的是让「改一个前缀名」有明确的落点。
PREFIXES = [
    'director',        # 导演台 3D（下面 directorPrompt 单独列）
    'directorPrompt',  # 提示词优化链
    'characterStudio', # 角色造型室
    'clip',            # 智能剪辑的时间线与字幕
    'imgEditor',       # 图片编辑器
    'interactiveImageEdit',
    'scriptV2',        # 脚本 V2
    'videoContinuation',  # 视频智能续写
    'chatTool',        # Agent 工具调用
    'canvasStore',     # ⚠️ 被复用的命名空间，见 20-reference.md 的更正
    'createSubject',
    'publish',
    'share',
]


def load():
    with open(TABLE, encoding='utf-8') as f:
        d = json.load(f)
    return d, d['表']


def manual_text():
    files = sorted(glob.glob(os.path.join(ROOT, '*.md')) +
                   glob.glob(os.path.join(ROOT, '10-tasks', '*.md')))
    return files, ''.join(open(f, encoding='utf-8').read() for f in files)


def main():
    argv = sys.argv[1:]
    d, t = load()
    files, txt = manual_text()

    short = {k: v for k, v in t.items() if len(v) <= SHORT_MAX}
    missing = {k: v for k, v in short.items() if v not in txt}

    if '--missing' in argv:
        top = sorted(missing.items(), key=lambda kv: -len(kv[1]))[:20]
        for k, v in top:
            print(f'{len(v):3d}  {k} = {v}')
        return

    rows = []
    for p in PREFIXES:
        n = sum(1 for k in t if k.startswith(p))
        m = sum(1 for k, v in missing.items() if k.startswith(p))
        rows.append((p, n, m))
    # director 去掉 directorPrompt 的重叠
    d_only = sum(1 for k in t
                 if k.startswith('director') and not k.startswith('directorPrompt'))

    if '--markdown' in argv:
        print('| 分组 | 全表条数 | 其中「手册没出现过」 |')
        print('|---|---|---|')
        print(f'| **全表** | **{len(t)}** | **{len(missing)}** |')
        for p, n, m in rows:
            print(f'| `{p}*` | {n} | {m} |')
        return

    print(f'表来源      {TABLE}')
    print(f'全表        {len(t)} 条')
    print(f'≤{SHORT_MAX} 字短文案  {len(short)} 条')
    print(f'其中手册没出现过  {len(missing)} 条'
          f'（{len(missing) * 100 // max(len(short), 1)}%）')
    print(f'手册正文    {len(files)} 个 md / {len(txt)} 字符')
    print()
    print(f'{"前缀":22s} {"全表":>6s} {"未出现":>6s}')
    for p, n, m in rows:
        print(f'{p:22s} {n:6d} {m:6d}')
    print()
    print(f'注：director* 去掉与 directorPrompt* 的重叠后 = {d_only}')


if __name__ == '__main__':
    main()
