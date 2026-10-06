#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""方向十四反验用例 52（能抓）：把任务页上的版本标注改成一个上游不存在的 tag。

**注入的是纪律 360 治的那一族**：版本号写错 / 凭空写一个版本。
`v1.9.9` 是**故意挑的**——它形态完全合法（三段数字），
**所以任何只看形态的判据都抓不住它**，
**而方向十四的判据读的是上游 `git tag -l`，它不在那 34 个 tag 里**。

**锚点用结构而不是字符串**（纪律 318 / 320）：
取「以 `> ` 开头且含 `v1.6.22 起不再弹` 的那一行」，
**断言恰好 1 行**——`director-basics.md` 里 `v1.6.22` 出现多次，
**而本用例要改的是「标注」那一处，不是全文替换**。
"""
import re
import sys

s = sys.stdin.read()
lines = s.split("\n")

idx = [i for i, l in enumerate(lines)
       if l.lstrip().startswith(">") and "v1.6.22 起不再弹" in l]
assert len(idx) == 1, ("锚点未命中：引用块里含「v1.6.22 起不再弹」的行应当恰好 1 行，"
                       "实得 %d —— **全文替换会把同版本的其他几处一起改掉，"
                       "而那是在做另一件事**" % len(idx))
i = idx[0]
m = re.search(r"v(\d+)\.(\d+)\.(\d+)\s*起", lines[i])
assert m, "锚点未命中：那一行没有「vX.Y.Z 起」形态：%r" % lines[i][:70]
assert m.group(0) == "v1.6.22 起", ("锚点未命中：真实形态是 %r，而本用例钉的是「v1.6.22 起」"
                                     % m.group(0))
lines[i] = lines[i].replace("v1.6.22 起", "v1.9.9 起", 1)
out = "\n".join(lines)
assert out != s, "空转：文件没变"
assert "v1.9.9 起" in out and "v1.6.22 起不再弹" not in out, "空转：改后内容不符合预期"
sys.stdout.write(out)
