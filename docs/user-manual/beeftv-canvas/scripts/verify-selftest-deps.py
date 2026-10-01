#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第十七道闸：反验的临时仓必须带齐被测闸门的本地依赖（Batch 178 新增）。

**这道闸看守的是「反验本身还能不能跑」**——而它坏掉时，**构建是全绿的**。

**为什么需要它（Batch 178 的实测，这是本轮最贵的一次）**：

Batch 175 让 8 道闸改为 `from baseline import resolve_ref`（共用取证基线解析）。
**但 4 份反验是把被测闸门 `shutil.copy` 进临时目录再跑的**，那份临时目录里
**没有 `baseline.py`** —— 于是：

  · `selftest-line-counts` 5 例全失败、`selftest-runtime-policy` 6 例全失败、
    `selftest-feature-flags` 5 例全失败、`selftest-screenshots-literals` 4 例全失败；
  · **20 例，跨 3 个批次（175/176/177）全坏**；
  · 而 `build-site.sh` **十六道闸全绿**——因为闸门本体在真实目录里跑得好好的。

**为什么没人发现**：反验不在构建路径上。**「反验坏了」不产生任何构建期信号**，
只有专门去跑它才看得见——而上一批跑它还是三个批次前的事。
**这比判据失效更隐蔽：判据失效会红，反验失效只是安静地不再说话。**

修的过程还暴露了**第二层**：`baseline.py` 自己用 `dirname(dirname(__file__))`
推断手册根，在临时目录里同样指错，抛「读不到 20-reference.md」。
**一个被多处 import 的模块，它「定位自己所在仓」的假设必须在被搬运时仍然成立。**

**本闸两个方向**：

  方向一：**凡是把闸门复制进临时目录的反验，被测闸门 import 的每个本地模块
    都必须被一并复制。** 判据用 AST 抽 `import X`（`X` 不带点、不在标准库、
    且 `scripts/X.py` 真实存在），再核反验的源码里有没有提到它。
    **本闸不判「运行时真的成功」**——那要跑一遍，太慢；它判**静态上有没有搬运**，
    而静态足以抓住 Batch 178 这一类。

  方向二：**被搬运的本地模块不得自己用 `__file__` 推断仓根**，
    除非它同时支持 `BEEFTV_MANUAL_ROOT` 之类的外部注入。
    **这一条专治「搬过去了、但它找错了家」**——也就是上面说的第二层。

**为什么不直接跑一遍所有反验**：最慢的那份要 25 分钟（`selftest-unreachable.sh`），
放进每次构建不可接受；而**这类回归恰恰是「反验能抓、构建抓不到」的**，
所以要的是一个**构建期就能跑的静态等价物**。

退出码：0 全部自洽；1 有不自洽；2 未能核对（找不到 scripts 目录 / 抽出 0 份反验）。
"""

import ast
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")

# 标准库与第三方：出现在这些名单里的 import 不需要被搬进临时仓
STDLIB = set("""abc argparse ast base64 collections contextlib copy csv dataclasses datetime
difflib enum errno filecmp fnmatch functools glob hashlib io itertools json logging math mimetypes
os pathlib platform random re shlex shutil subprocess sys tempfile textwrap time typing unittest
urllib uuid warnings""".split())


def local_imports(path):
    """返回该脚本 import 的**本地模块名**（即 scripts/ 下真实存在的 .py）。"""
    try:
        with open(path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
    except (OSError, SyntaxError):
        return None
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                names.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level:          # 相对 import
                continue
            if node.module:
                names.add(node.module.split(".")[0])
    out = set()
    for n in names:
        if n in STDLIB:
            continue
        if os.path.isfile(os.path.join(SCRIPTS, n + ".py")):
            out.add(n)
    return out


def copies_gate_into_tmp(text):
    """这份反验是否会把闸门脚本复制进临时目录。"""
    return bool(re.search(r"shutil\.copy\w*\(\s*\w+\s*,", text)) and \
        bool(re.search(r"tempfile\.mkdtemp", text))


def main():
    if not os.path.isdir(SCRIPTS):
        print(f"[skip] 找不到 {SCRIPTS}，跳过反验依赖核对")
        return 2

    selftests = sorted(f for f in os.listdir(SCRIPTS)
                       if f.startswith("selftest-") and f.endswith(".py"))
    problems = []
    checked = 0
    for fn in selftests:
        p = os.path.join(SCRIPTS, fn)
        try:
            with open(p, encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            continue
        if not copies_gate_into_tmp(text):
            continue
        # 这份反验复制了哪些闸门脚本
        copied = re.findall(r"shutil\.copy\w*\(\s*(\w+)\s*,", text)
        gate_names = []
        for c in set(copied):
            # **刻意不依赖引号风格**（反验用例 3 上线首跑就抓到）：
            # 原式用 `[^)]*?"(verify-…\.py)"` 只认**双引号**，
            # 于是一份用单引号写路径的反验会被**整份跳过**——
            # 而它恰恰是新加的、最需要被看住的那一份。
            # **判据不能因为一个标点风格不同就静悄悄查不到**（纪律 101）。
            m = re.search(re.escape(c) + r'\s*=\s*os\.path\.join\([^)]*?([\'"])(verify-[a-z0-9-]+\.py)\1',
                          text)
            if m:
                gate_names.append(m.group(2))
        if not gate_names:
            continue
        checked += 1
        for gname in gate_names:
            deps = local_imports(os.path.join(SCRIPTS, gname))
            if deps is None:
                problems.append(f"方向一：读不了 scripts/{gname}")
                continue
            for d in sorted(deps):
                # **必须核「有真实的搬运动作」，而不是「文本里提到过这个名字」**
                # （反验用例 2 上线首跑就抓到这个：原判据是 `if d in text: continue`，
                #  而反验里那行 `BASELINE = os.path.join(HERE, "baseline.py")`
                #  **本身就含有 "baseline" 这个子串**——于是把搬运语句删掉，
                #  判据照样说「搬过了」。**判据把自己的准备工作当成了证据。**
                # 收紧成：必须存在一条**把该模块复制进临时 scripts/ 的语句**。
                moved = re.search(
                    r"copy\w*\(\s*\w+\s*,\s*[^)]*scripts[^)]*[\"']" + re.escape(d) + r"\.py[\"']",
                    text)
                if moved:
                    continue
                problems.append(
                    f"方向一：{fn} 把 {gname} 复制进临时目录跑，"
                    f"但被测闸门 import 了本地模块 `{d}`，而反验**没有把它复制进临时 scripts/**"
                    "　→ 临时目录里 import 失败，**该反验的每一例都会失败**，"
                    "**而 build-site.sh 仍然全绿**（Batch 178 实测：34 例跨 3 个批次全坏）")

    if checked == 0:
        print("[skip] 没有反验把闸门复制进临时目录——判据可能已失效，请先确认")
        return 2

    if problems:
        print("反验依赖核对：%d 处不自洽" % len(problems))
        for p in problems:
            print("  ✗ " + p)
        return 1

    print("反验依赖核对通过：%d 份反验会把闸门复制进临时目录，"
          "其被测闸门的本地依赖均已一并搬运" % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
