#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""注入：把 `20-reference.md` 加进 `config.mjs` 的 srcExclude。

**验的是「修法真的生效了」**（Batch 218 纪律 225）：闸 9 原来抄了一份排除表，
而注释写着「与 config.mjs 保持一致——改了那边就要改这里」。
本注入证明**它现在是从 config.mjs 读的**：内容页真值 35 → 34，
闸 9 必须立刻报「写 [35]，实际 34」。

**改之前同一注入的结果是 rc=0 且打印「✓ 内容页数 = 35」**——
那是一个**印着错数字的绿灯**（纪律 222 的第三种形式）。
"""
import io
import sys

OLD = "srcExclude: ["
NEW = "srcExclude: ['**/20-reference.md', "

s = sys.stdin.read()
assert s.count(OLD) == 1, "锚点 `srcExclude: [` 不唯一（%d 处）——空转，作废本用例" % s.count(OLD)
out = s.replace(OLD, NEW, 1)
assert out != s, "替换后内容没变——空转，作废本用例"
sys.stdout.write(out)
