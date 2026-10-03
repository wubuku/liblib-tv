#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三十六道闸：被撤回的说法不许活在**可执行文本**里。

背景（Batch 247）：纪律 270 写着「**订正一处不够——那句话被抄过几次就要订正几次**」。
**而这句话被抄过几次，从来没有任何东西数过。**
Batch 245 照着纪律 270 去找「VitePress 给同名标题生成同一个锚点」这句话的全部拷贝，
数出四处并全部订正——**然后它自己漏了两处**，其中一处是：

  `verify-heading-uniqueness.py` 的 `problems.append()` 里那句**真正会打印给用户看的报错文案**。

**为什么漏的是这一处、而且它比另外三处更要紧**：
Batch 245 改的四处（脚本头、A 类风险表、闸门清单表、纪律 250）**全是存档性质**——
读过的人不会照着它们去改数据。**而报错文案是判据的「使用说明书」**：
纪律 246/247/248 早就写过「**判据不只是发现问题的工具，它还是指示动作的说明书**」，
Batch 231 还因此把「不要为了配平去补闭合符」直接写进了报错里。
**照着旧文案去查「锚点撞车」，会查一个在 vitepress 1.6.4 上不存在的东西。**

本闸的判据（**只扫 `scripts/verify-*.py`，且只扫剥掉注释与 docstring 之后的部分**）：
  1. 用 `ast` 取每个文件里**所有** docstring 覆盖的行号（含结束行）；
  2. 跳过整行以 `#` 开头的行；
  3. 剩下的就是**会被执行、会被打印**的文本——登记表里的说法出现在这里，一律报。

**为什么范围只到「可执行文本」**（这一步收窄是量出来的，不是想出来的）：
  · 文档上下文里**必须**能引述被撤回的说法——不引述就没法说清「曾经错在哪」；
    实测 17 处拷贝里 15 处在文档/注释里，且**全部处在订正语境中**
    （「假」「证伪」「原写的是」「实测说不是这样」…）。
  · 而**可执行文本里没有这个自由度**：那里出现的每一句要么会被打印、要么会被执行，
    **而它周围通常没有订正语境**（实测 2 处，一处都没有）。
  · **所以本闸不是「禁止引述」，是「引述必须放在能写清楚它已被推翻的地方」**。
    闸 36 **不覆盖** `build-site.sh` 的注释、`selftest-*.sh` 的注释与任何 `.md`
    ——**那条边界写在这里，而不是留在代码里当免责**（纪律 269）。

**登记表（`_RETRACTED`）就是「被撤回的说法」这份清单本身**：
  · 它为空 → rc=2（**零输入不许报绿**，纪律 156）。一条空表等于「什么都没有被撤回」，
    而真实情况是**撤回过五条**，空表只说明这份清单被清空了。
  · 它满了以后每一条都要能说出**在哪一批、靠什么量出来的**——
    **一份没有出处的撤回清单，等于一份没有出处的判据。**

退出码：0 干净；1 可执行文本里出现了已撤回的说法；2 登记表为空 / 没找到任何闸脚本。
"""

import ast
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: 被撤回的说法：**判别正则** + **撤回依据（量它的那一批与结论）**。
#: 加条目时三样都要齐：正则、依据、**首次证伪的批次**。
#: **判别正则要挑只有「断言这个说法」的行才会命中的片段**——
#: 实测踩过一次：先写 `行尾.*竖线`，结果把「行尾竖线省掉了照样渲染」这类
#: **正确陈述**一起命中；改成 `行尾(必须|未闭合|没有竖线)` 之后只剩真正在断言它的地方。
_RETRACTED = [
    ("slugify-同名撞锚点",
     re.compile(r"落到(前一个|第一个)|同名[^。\n]{0,24}生成[^。\n]{0,12}\*\*同一个"),
     "Batch 245 实测：VitePress 的 slugify **会去重**（同名加 -1/-2），"
     "十种形态零例外，目录里的 href 各自指向自己"),
    ("行尾竖线是表格行规范形态",
     re.compile(r"行尾(必须|未闭合|没有竖线)"),
     "Batch 246 实测：GFM 表格行的**首尾竖线都是可选的**，"
     "表头/分隔行/数据行省掉行尾竖线全都照常渲染"),
    ("多一个字面竖线→多切一列",
     re.compile(r"多(切|出)一列|凭空多出一列"),
     "Batch 246 实测：多出来的那格**被静默丢弃**，表格仍是原列数——"
     "危害是真的（内容丢失），机制不是「多出一列」"),
    ("容器必须配平",
     re.compile(r"容器(必须)?配平|不配对"),
     "Batch 231 实测：markdown-it-container 会自动闭合，"
     "**少一个闭合符渲染完全正常**；多一个才会变成正文 `<p>:::</p>`"),
    ("VitePress 按冒号个数分层",
     re.compile(r"冒号个数"),
     "Batch 240 实测：嵌套深度**不是**按冒号个数算的"),
]


def _registry_lines(tree):
    """`_RETRACTED = [...]` 这个赋值语句覆盖的行号（**整段**）。

    **为什么必须精确豁免这一段，而不是豁免整个文件**：
    登记表里必须**逐字**写着那些被撤回的说法（正则要能匹配到它们，标签要能报出来），
    所以**本闸的源码天然含有全部五条**。
    豁免整个文件会让本闸对自己的五条完全失明——**而那五条恰恰是最该被盯的**。
    豁免这一段赋值则只放行「登记」，不放行「使用」：
    **往别处抄一条照样被抓。**
    """
    out = set()
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = ([node.target] if isinstance(node, ast.AnnAssign)
                   else node.targets)
        for t in targets:
            if isinstance(t, ast.Name) and t.id == "_RETRACTED":
                for k in range(node.lineno, (node.end_lineno or node.lineno) + 1):
                    out.add(k)
    return out


def live_lines(path):
    """返回 [(行号, 原文)]，只含**会被执行或打印**的行。"""
    src = io.open(path, encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return None, f"语法错（第 {e.lineno} 行：{e.msg}）"
    doc = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef,
                                 ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)):
            for k in range(first.lineno, (first.end_lineno or first.lineno) + 1):
                doc.add(k)
    doc |= _registry_lines(tree)
    out = []
    for i, line in enumerate(src.split("\n"), 1):
        if i in doc:
            continue
        if line.strip().startswith("#"):
            continue
        out.append((i, line))
    return out, None


def main():
    root = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else ROOT
    scripts = os.path.join(root, "scripts")

    # **零输入不许报绿**（纪律 156）。空表与「没有闸脚本」是两种不同的空转，分开报。
    if not _RETRACTED:
        print("[未能核对] 被撤回说法的登记表是空的——本闸本轮什么也没检查，"
              "**不能按「没有假话泄漏」通过**（撤回记录是真的有五条）")
        return 2
    for rid, pat, why in _RETRACTED:
        try:
            pat.search("x")
        except re.error as e:
            print(f"[未能核对] 登记表第 {rid} 条的正则编译失败：{e}")
            return 2
        if not why.strip():
            print(f"[未能核对] 登记表第 {rid} 条没写撤回依据——"
                  "**一份没有出处的撤回清单等于一份没有出处的判据**")
            return 2

    if not os.path.isdir(scripts):
        print(f"[未能核对] 找不到闸脚本目录：{scripts}")
        return 2
    files = sorted(n for n in os.listdir(scripts)
                   if n.startswith("verify-") and n.endswith(".py"))
    if not files:
        print(f"[未能核对] {scripts} 下没有 verify-*.py——"
              "本闸本轮什么也没检查，**不能按「没有假话泄漏」通过**")
        return 2

    problems = []
    scanned = 0
    for name in files:
        path = os.path.join(scripts, name)
        rows, err = live_lines(path)
        if rows is None:
            # 闸脚本自己语法错 = 本闸读不懂它，**不能当干净放行**
            problems.append((name, 0, "-", f"解析失败：{err}"))
            continue
        scanned += 1
        for lineno, line in rows:
            for rid, pat, _why in _RETRACTED:
                if pat.search(line):
                    problems.append((name, lineno, rid, line.strip()[:90]))

    if problems:
        print(f"被撤回说法的泄漏：{scanned} 个闸脚本里 {len(problems)} 处"
              f"（登记表 {len(_RETRACTED)} 条）")
        for name, lineno, rid, excerpt in problems:
            where = f"{name}:{lineno}" if lineno else name
            print(f"      {where}  [{rid}]  {excerpt}")
        print("  → 被撤回的说法只能出现在**注释或 docstring** 里，"
              "而且要写明它已被证伪；**可执行文本里的那句会被打印给人看**")
        return 1

    print(f"被撤回说法的泄漏：{scanned} 个闸脚本的可执行文本，"
          f"{len(_RETRACTED)} 条已撤回说法，零处泄漏")
    return 0


if __name__ == "__main__":
    sys.exit(main())
