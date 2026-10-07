#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Batch 328：把「闸与文档说它读哪个 ref」这条约定钉成可执行判据。

**它守的是什么**：本项目里曾有 6 处文档/脚本 docstring 写着「对照 / 读上游 `origin/main`」，
而**6 道闸实测全部走 `baseline.resolve_ref()` / `module_ref()`**，
读的是**手册声明的取证基线**（`bcc3b05` = v1.6.22），没有一道写死 ref。
最狠的一处不是口径写错，而是同一段里那句「**上游一改这里就会红**」——
**实测是假的**：上游 `origin/main` 已领先基线 **34 个提交**，行数表 7 条仍全部相符。
**一句关于机制的假话，比一个过期的数字危险得多**——它的实际作用是让读者以为这张表被持续守着。

**本判据刻意只钉死这 6 处，不做全库扫描——而这是量过的结论，不是省事**：
扫「提到 `origin/main` 的段落」实测命中 **54 段**，其中 **6 段是正当的历史说明**
（「在此之前 8 道闸把 ref 写死成 origin/main」「Batch 171 的实测」「剔的范围是量过的」
「本闸此前是十道闸里唯一没有反向验证的」……），**而这 6 段全部不含「基线」二字**。
于是「段落提到 origin/main 就要求它提到基线」会得到 **抓 1 处 / 误伤 6 处**。
**词面上「历史说明」与「当前陈述」不可分**——而误伤比漏报更坏（纪律 248）。
所以：**全集靠「已实测的错误清单」而不是靠扫描**，边界就写在文件头上。

**合法例外从代码推出，不建人工登记表**（纪律 242）：
`verify-baseline-landmark.py`（闸 40）**代码里真的用 `origin/main^{commit}`**，
而且这是对的——它问的是「读者现在能撞到什么」，不是「手册照哪版写的」。
本判据只覆盖**走基线机制**的那些脚本的 docstring，闸 40 因代码用 `origin/main` 而天然不在其中。

## 三态退出码（纪律 101：退化必须是 rc=2，不是 rc=1）

- **0**：6 处全部已改正
- **1**：有 1+ 处**说得不对**（锚点认得出、但那处没提基线机制）
- **2**：**未能核对**（文件缺失 / 锚点命中 0 段或 >1 段——判据退化，不是内容错）

**③为什么锚点必须是稳定片段、不能是「改正后的措辞」**：
第一版把锚点写成「本脚本抽取上游在\*\*手册声明的取证基线提交\*\*」，
于是「**没改正**」会表现为**锚点认不出** → 报 rc=2「未能核对」，
而它其实是 rc=1「不一致」——**两者的处置完全不同**（前者修工具、后者修内容）。
所以锚点一律取「旧措辞与新措辞都有」的片段（`本脚本抽取上游` / `脚本读的是上游`），
由「该段必须含基线标识」来区分对错。

## 为什么按**段落**切、不是按**句**切

口径说明天然是**一整个引用块 / 一整个 docstring 段**。
第一版按 `。；;` 切句，于是锚点与基线标识被劈到两句里，实测 5 处只认出 4 处。
**判据的输入不是「那段文字写了什么」，而是「它挂在哪个东西上」**（纪律 361③）。

## ④最阴的一处：**判据的锚点被我自己写的「更正说明」命中**

第五段锚点原本是 `脚本读的是上游`（旧措辞与新措辞都有）。
而在补 Batch 327 那一处漏写时，我在更正说明里**原样引用了这六个字**——
于是**同一个文件里出现了两段都命中**，判据立刻报 **rc=2「锚点命中 2 段」**。
**它没有报错、没有放行，而是老实报「认不出」——这是三态设计的价值**，
可处置仍然要多花一轮。
**修法两处一起做**：①锚点换成**段首的稳定片段**（`只检查「不可达是否仍成立」`），
②**更正说明改成不复述锚点原文**。
**教训：判据的锚点必须对「围绕它的说明文字」免疫**——
而最容易写进判据周边说明的，恰恰就是「这里原来写的是什么」。

## 自测

`--self-test` 跑 13 个已知答案（正样本 / 负样本 / 认不出三态），
其中**负样本刻意包含「措辞正是改坏之后的样子」**——
**一个只会认正确形态的判据，在真被改坏时会报 rc=2 而不是 rc=1。**

`--expect <n>` 用于副本树承重核对。
"""
import argparse
import os
import re
import sys

#: (相对路径, 稳定锚点, 该段必须出现的基线标识, 人读的说明)
ANCHORS = [
    ("20-reference.md",
     re.compile(r"文件 = 单文件行数"),
     "bcc3b05", "行数快照的口径段"),
    ("20-reference.md",
     re.compile(r"\*\*口径\*\*：两列都必须与"),
     "bcc3b05", "部署模式表的口径段"),
    ("scripts/verify-line-counts.py",
     re.compile(r"· 对照 "),
     "resolve_ref", "闸 11 docstring 的口径行"),
    ("scripts/verify-endpoints.py",
     re.compile(r"本脚本抽取上游"),
     "resolve_ref", "闸 3 docstring 的抽取来源行"),
    ("scripts/verify-unreachable.py",
     re.compile(r"只检查「不可达是否仍成立」"),
     "module_ref", "闸 7 docstring 的读取来源段"),
    ("scripts/verify-unreachable.py",
     re.compile(r"方向一（登记项是否仍成立）"),
     "module_ref", "闸 7 docstring 的方向一句"),
]

#: 段落分隔：空行（含只含空白与引号的行）
PARA_SPLIT = re.compile(r"\n[ \t>]*\n")


def paragraphs(text):
    """按「空行 / 只有引号的空行」切段。**口径说明天然是一整段。**"""
    flat = text.replace("\r\n", "\n")
    return [p.strip() for p in PARA_SPLIT.split(flat) if p.strip()]


def check(root, only=None):
    """返回 (ok, bad, unreadable)。

    `unreadable` = 文件缺失 / 锚点命中 0 段或 >1 段 —— 这两种都是
    **「没找到可判的东西」**，按纪律 101 归 rc=2，不与「不一致」混在一起。
    """
    ok, bad, unreadable = [], [], []
    for idx, (rel, anchor, needle, desc) in enumerate(ANCHORS):
        if only is not None and idx != only:
            continue
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            unreadable.append("%s 整个文件不存在" % rel)
            continue
        paras = paragraphs(open(p, encoding="utf-8").read())
        hit = [s for s in paras if anchor.search(s)]
        if len(hit) != 1:
            unreadable.append("%s「%s」：锚点命中 %d 段（应为 1）" % (rel, desc, len(hit)))
            continue
        if needle not in hit[0]:
            bad.append("%s「%s」：该段没有基线标识 `%s`，实测为「%s」"
                       % (rel, desc, needle, " ".join(hit[0].split())[:90]))
        else:
            ok.append("%s「%s」" % (rel, desc))
    return ok, bad, unreadable


#: 自测样本：(锚点下标, 文件正文, 期望结果)
#:   "ok" = 认出并通过；"bad" = 认出但没提基线（rc=1）；"unreadable" = 认不出（rc=2）
SAMPLES = [
    (0, "20-reference.md\n> 文件 = 单文件行数。对照 **手册声明的取证基线 `bcc3b05`**。\n", "ok"),
    (0, "20-reference.md\n> 文件 = 单文件行数。对照 **BeefTV `origin/main`**。\n", "bad"),
    # 锚点命中 1 段、而基线标识落在**另一段** —— 这是「不一致」，不是「认不出」
    (0, "20-reference.md\n> 文件 = 单文件行数。\n\n> 对照 `bcc3b05`。\n", "bad"),
    (1, "20-reference.md\n> **口径**：两列都必须与**取证基线 `bcc3b05`** 的取值相符。\n", "ok"),
    (1, "20-reference.md\n> **口径**：两列都必须与 `origin/main` 的取值相符，\n", "bad"),
    (2, "scripts/verify-line-counts.py\n  · 对照 **手册声明的取证基线提交**（经 `baseline.resolve_ref()` 解析）。\n",
     "ok"),
    (2, "scripts/verify-line-counts.py\n  · 对照 **BeefTV `origin/main`**（可用 `BEEFTV_REF` 覆盖）。\n", "bad"),
    (3, "scripts/verify-endpoints.py\n本脚本抽取上游在**手册声明的取证基线提交**（经 `baseline.resolve_ref()` 解析）。\n",
     "ok"),
    (3, "scripts/verify-endpoints.py\n本脚本抽取上游的路由。\n", "bad"),
    (3, "scripts/verify-endpoints.py\n抽取路由并与手册比对。\n", "unreadable"),
    (4, "scripts/verify-unreachable.py\n只检查「不可达是否仍成立」，不判断该不该修。脚本读的是上游在**取证基线提交**（`module_ref()`）上的对象。\n",
     "ok"),
    (4, "scripts/verify-unreachable.py\n只检查「不可达是否仍成立」，不判断该不该修。脚本读的是上游 `origin/main` 的对象。\n",
     "bad"),
    (4, "scripts/verify-unreachable.py\n只检查断言是否仍成立。脚本读的是上游 `origin/main` 的对象。\n", "unreadable"),
    (5, "scripts/verify-unreachable.py\n**方向一（登记项是否仍成立）**：逐条取上游在取证基线（`module_ref()`）的源码。\n",
     "ok"),
    (5, "scripts/verify-unreachable.py\n**方向一（登记项是否仍成立）**：逐条取上游 `origin/main` 的源码。\n", "bad"),
    (5, "scripts/verify-unreachable.py\n**方向一（登记项是否已过期）**：逐条跑该条专属判据。\n", "unreadable"),
]


def classify(ok, bad, unreadable):
    if unreadable:
        return "unreadable"
    if bad:
        return "bad"
    return "ok" if ok else "unreadable"


def self_test():
    import shutil
    import tempfile
    fails = 0
    for i, (idx, body, want) in enumerate(SAMPLES, 1):
        rel = ANCHORS[idx][0]
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            head, rest = body.split("\n", 1)
            open(p, "w", encoding="utf-8").write(head + "\n")
            with open(p, "a", encoding="utf-8") as fh:
                fh.write(rest)
            got = classify(*check(td, only=idx))
            if got != want:
                fails += 1
                print("  ✗ 样本 %d 期望 %s、实测 %s" % (i, want, got), file=sys.stderr)
        shutil.rmtree(td, ignore_errors=True)
    if fails:
        print("自测 %d/%d 样本不过" % (fails, len(SAMPLES)), file=sys.stderr)
        return 1
    counts = {k: sum(1 for s in SAMPLES if s[2] == k) for k in ("ok", "bad", "unreadable")}
    print("锚点定位自检：%d 个已知答案（%d 正 / %d 负 / %d 认不出），全过"
          % (len(SAMPLES), counts["ok"], counts["bad"], counts["unreadable"]))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root")
    ap.add_argument("--only", type=int, default=None)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.root:
        print("  ✗ 缺 --root，不猜", file=sys.stderr)
        return 2
    ok, bad, unreadable = check(a.root, only=a.only)
    for o in ok:
        print("  ok   %s" % o)
    for b in bad:
        print("  ✗ %s" % b, file=sys.stderr)
    for u in unreadable:
        print("  ?   未能核对：%s" % u, file=sys.stderr)
    if unreadable:
        print("ref 描述核对**未能核对**（%d 处），不报通过" % len(unreadable), file=sys.stderr)
        return 2
    if bad:
        print("ref 描述核对**不一致**（%d 处）" % len(bad), file=sys.stderr)
        return 1
    print("ref 描述核对通过：%d 处 ref 描述全部已改正" % len(ok))
    return 0


if __name__ == "__main__":
    sys.exit(main())