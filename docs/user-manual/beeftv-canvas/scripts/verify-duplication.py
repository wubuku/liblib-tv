#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 37「同一段解析逻辑被手写了几遍」（Batch 256 新增）。

**背景是一次普查，不是一次事故**：Batch 256 把全树每个脚本里的正则字面量抽出来、
归一化之后统计跨文件重复，**结果是 6 条**，而排在最前面的两条各 **3 份**：

| 概念 | 收敛前 | 收敛后 |
|---|---|---|
| 读表格行首格 `^\\|\\s*([^|]*?)\\s*\\|` | **3 份（md5 逐字节相同）** | 1（`tablerow.py`） |
| 按未转义竖线切 `(?<!\\\\)\\|` | **3 份** | 1（`tablerow.py`） |
| 批次号 `^\\d+[a-z]?$` | 2 份（**另有第三种写法** `re.fullmatch`） | 1（`tablerow.py`） |

**纪律 274：共享概念只能有一份实现。** 而**「同一件事被手写几遍，就会有几套判真条件」**——
**这三条在本项目里已经出现过一次真实后果**（Batch 252 改闸 5 的表格行判据时，
**如果另外两份没被一起看过，就会出现「三份改了两份」而没有任何判据会报这件事**）。

**本闸做什么**：把普查变成常驻信号。
**一条正则字面量出现在两个及以上文件里，就必须在下表的 `ACCEPTED` 里带理由登记**；
**没登记的重复一律报红**。
**登记表只能变短**——收敛掉一条就从表里删掉，**而它不会自己变短**。

**它明确不做什么**：
**它不比「这两份是不是真的在问同一件事」**——那是人的判断，
本闸只问「这两段文字一模一样吗」。**而这正是它能机械判定的那一半**
（纪律 171：行为可判、写法不可判——**这里退一步，只核写法，因为写法就是这里要防的东西**）。

**为什么白名单要带理由**：一份没有理由的白名单就是一份「我批准了」的名单，
而**理由会被下一个人读到**。
"""

import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")

#: **`#:` 形式的行注释不参与统计**——本项目大量用注释解释判据，
#: **而注释里贴一份正则原文是常规写法**（Batch 252、254 都这么写过）。
#: **把它们算成「重复」会让本闸第一天就误报几十处**。
_COMMENT = re.compile(r"^\s*#")

#: **抽出 `re.compile(r"…")` 的字面量**。
#: **`grep -E` 那类模式也统计**——它们同样是「同一段判真逻辑被手写几遍」的形态。
_RX = re.compile(r'''re\.compile\(\s*r?(?P<q>["'])(?P<body>.+?)(?P=q)''', re.S)
_GREP = re.compile(r'''(?:grep|awk)\s+(?:-[A-Za-z]+\s+)*(?P<q>["'])(?P<body>[^"']{4,})(?P=q)''')

#: **已登记的重复**：键是 `md5(归一化后的字面量)` 的前 12 位。
#: **值是 `(字面量, 涉及文件, 为什么现在可以各自一份)`。**
ACCEPTED = {
    # ── 三条「已确认是同一个概念、但本批没有收敛」的 ──
    "25eecbe17b93": (
        "找前端 API 调用点",
        ["verify-endpoints.py", "verify-exclusions.py"],
        "**同一个概念的第三份拷贝**（端点清单 vs 排除条件表各要一份）。"
        "**本批没收敛是因为收敛它要跨两个闸的数据结构一起动**——"
        "**而那是一次独立工作，不该混在「收敛表格正则」这一批里**。"
        "**这一条登记的是「欠着」，不是「合格」。**"),
    "4ca9fa24681d": (
        "夹具文件名的形态",
        ["verify-meta.py", "verify-selftest-bootable.py"],
        "**方向五重放夹具前提（闸 18）与方向五的登记表（闸 9）各要一份**。"
        "同上：已确认同源，**待收敛**。"),
    "0ffab7a538d5": (
        "解析闸输出里的一个块",
        ["verify-shot-integrity.py", "verify-shot-version-source.py"],
        "**两个截图闸各自解析同一种报告块**。"
        "**而它们的输入格式本身是各自闸的输出**——"
        "**收敛的前提是先统一那两个闸的输出格式**，那比收敛一条正则大得多。"
        "**如实记为待收敛。**"),
}


def scan():
    """返回 `{归一化字面量: 出现过它的文件集合}`，注释行不算。"""
    out = {}
    try:
        files = sorted(f for f in os.listdir(SCRIPTS)
                       if f.endswith((".py", ".sh")))
    except OSError:
        return out
    for f in files:
        try:
            with open(os.path.join(SCRIPTS, f), encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            continue
        for line in text.split("\n"):
            if _COMMENT.match(line):
                continue
            for rx in (_RX, _GREP):
                m = rx.search(line)
                if not m:
                    continue
                body = m.group("body").strip()
                #: **最短 8 个字符——这条是首跑当场撞出来的**：
                #: 上限放宽到 4 时，本闸把 **`$want`（5 个字符的 shell 变量名，
                #: 在四份反验里都出现）**报成「同一段解析逻辑被手写四遍」——
                #: **而它根本不是一段逻辑，就是个变量名。**
                #: **字面量越短，偶然重合的概率越高**：
                #: `$want` / `$line` / `$tmp` 这类名字在任何几份文件里都会同时出现。
                #: **真实的重复（本批实测的三条）分别是 30 / 31 / 46 个字符**，
                #: **离 8 还远得很，所以这条阈值不会漏掉任何一条真的**。
                if len(body) < 8:
                    continue
                key = hashlib.md5(body.encode("utf-8")).hexdigest()[:12]
                out.setdefault(body, set()).add(f)
                break
    return out


def main():
    try:
        found = scan()
    except OSError as exc:
        print(f"[未能核对] 读不了 scripts/：{exc}")
        return 2
    dup = {k: v for k, v in found.items() if len(v) > 1}
    if not found:
        print("[未能核对] 一个正则字面量都没扫到——**判据退化了，按规则不得当成通过**")
        return 2

    problems = []
    for body, files in sorted(dup.items()):
        key = hashlib.md5(body.encode("utf-8")).hexdigest()[:12]
        entry = ACCEPTED.get(key)
        if entry is None:
            problems.append(
                (body, sorted(files),
                 "**同一段字面量出现在 %d 个文件里，而登记表里没有它**"
                 "　→ 要么收敛成一份（`tablerow.py` 那种共享模块），"
                 "要么在 `ACCEPTED` 里带理由登记；"
                 "**理由要写清「为什么现在可以各自一份」**（纪律 274）"))
        elif sorted(entry[1]) != sorted(files):
            problems.append(
                (body, sorted(files),
                 "**登记时是 %s，而现在是 %s**——**涉及的文件变了，"
                 "而理由是照着旧的那份写的**"
                 "　→ 登记表的「涉及文件」必须跟着现实改，"
                 "否则一条过期的理由会替一份新的重复背书" % (sorted(entry[1]), sorted(files))))

    print("重复普查：%d 条正则字面量，%d 条出现在多个文件里（登记表已登记 %d 条）"
          % (len(found), len(dup), len(ACCEPTED)))
    if problems:
        for body, files, why in problems:
            print("  ✗ `%s`" % body[:70])
            print("      文件：%s" % "、".join(files))
            print("      %s" % why)
        print("判据重复核对：%d 处问题" % len(problems))
        return 1
    print("判据重复核对通过：跨文件重复的 %d 条字面量全部在登记表里且带理由"
          % len(dup))
    return 0


if __name__ == "__main__":
    sys.exit(main())
