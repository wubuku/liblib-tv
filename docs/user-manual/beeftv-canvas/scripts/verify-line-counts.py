#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第十一道闸：上游源码行数快照核对（手册声明的行数 == 上游实修行数）。

**为什么要有这道闸**：手册里散着几句用**代码行数**论证「这个页面多重要」的话。
**行数是最容易过期的数字**——上游每改一次文件它就变，而**没有任何机制会提醒**。

**Batch 171 的实测（这是本闸的由来，不是假想）**：
`10-tasks/create-workspace.md` 写「源码 **2023** 行」，v1.6.16 的 `origin/main` 实为
**2790** 行，差 **767** 行；同一句里的排名「**仅次于**画布工作区」也已被 `projects`（5192 行）
超过。**行数本身没错，错的是没人看着它**——而它长得像一句客观描述，
读者会拿它当「这个页面有多大」的结论。

**口径（必须按这个算，否则数对不上）**：
  · 目录 → 其下所有 `.ts` / `.tsx` 文件行数之和；
  · 文件 → 单文件行数；
  · 对照 **BeefTV `origin/main`**（可用 `BEEFTV_REF` 覆盖）。

**它故意会在上游改动时报错**：那时该做的是**更新快照表或删掉那句话里的论据**，
不是把判据放宽——**放宽判据等于把这次发现再埋一次**。

**覆盖不到什么（如实说明）**：本闸只核**行数**。上游把一个 3000 行的文件拆成三个
1000 行的，数会变而**页面并没有变小**。所以行数只能当**量级参考**、不能当重要性结论；
这也是手册那两句话现在写「体量第三大」而不是「第二大门户」的原因。

退出码：0 全部相符；1 有不符；2 未能核对（找不到上游源码 / 找不到快照表 / 表里 0 行）。
"""
import os
import re
import subprocess
import sys
from baseline import resolve_ref, BaselineError, module_ref, baseline_guard

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANUAL = os.path.join(ROOT, "20-reference.md")
SRC = os.environ.get("BEEFTV_SRC", "/Users/yangjiefeng/Documents/glanderness/BeefTV")
REF = module_ref()
CODE_EXT = (".ts", ".tsx")


def _git(*args):
    return subprocess.run(["git", "-C", SRC] + list(args),
                          capture_output=True, text=True)


def count_lines(path):
    """返回 (行数, 错误说明)。目录按 .ts/.tsx 全量求和，文件按自身。"""
    listing = _git("ls-tree", "-r", "--name-only", REF, "--", path)
    if listing.returncode != 0:
        return None, f"git ls-tree 失败：{(listing.stderr or '').strip()[:120]}"
    names = [n for n in listing.stdout.split("\n")
             if n.strip() and n.endswith(CODE_EXT)]
    if not names:
        return None, f"在 {REF} 的 {path} 下找不到任何 .ts/.tsx（路径可能已改名）"
    total = 0
    for n in names:
        blob = _git("show", f"{REF}:{n}")
        if blob.returncode != 0:
            return None, f"读不到 {n}：{(blob.stderr or '').strip()[:120]}"
        # 与 wc -l 对齐：末尾无换行时最后一行也算一行
        text = blob.stdout
        total += text.count("\n") + (1 if text and not text.endswith("\n") else 0)
    return total, None


def parse_table():
    """返回 [(路径, 声明行数, 用途)]；找不到小节或没有数据行时抛 ValueError。"""
    if not os.path.isfile(MANUAL):
        raise ValueError(f"找不到 {MANUAL}")
    text = open(MANUAL, encoding="utf-8").read()
    m = re.search(r"###\s*上游源码行数快照[^\n]*\n(.*?)(?=\n##\s|\n###\s)", text, re.S)
    if not m:
        raise ValueError("20-reference.md 里找不到「上游源码行数快照」小节")
    rows = []
    for line in m.group(1).split("\n"):
        if not line.startswith("|") or re.match(r"\|\s*:?-", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or cells[0] in ("路径", ""):
            continue
        path = cells[0].strip("`")
        if not re.match(r"^\d+$", cells[1]):
            raise ValueError(f"快照表里 {path} 的行数不是整数：[{cells[1]}]")
        rows.append((path, int(cells[1]), cells[2] if len(cells) > 2 else ""))
    if not rows:
        raise ValueError("快照表里没有数据行")
    return rows


@baseline_guard
def main():
    try:
        rows = parse_table()
    except ValueError as exc:
        print(f"[skip] {exc}，上游行数核对本轮未能进行")
        return 2
    if not os.path.isdir(SRC):
        print(f"[skip] 未找到 BeefTV 源码 {SRC}，上游行数核对本轮未能进行")
        return 2

    bad, void = [], []
    for path, declared, usage in rows:
        real, err = count_lines(path)
        if real is None:
            void.append(f"{path}：{err}")
        elif real != declared:
            bad.append(f"{path}：手册写 {declared} 行，实测 {real} 行"
                       + (f"（用于「{usage}」）" if usage else ""))
    if void:
        for v in void:
            print(f"[skip] {v}")
    if bad:
        print(f"上游行数核对：{len(bad)}/{len(rows)} 条声明与上游不符")
        for b in bad:
            print("  " + b)
        print("→ 更新 20-reference.md 的快照表，或删掉手册里依赖这个数的论据；"
              "**不要放宽判据**（放宽等于把这次发现再埋一次）")
        return 1
    if void:
        # 一部分核对不了 = 整轮结论不完整，不能报「全部通过」
        print(f"[skip] {len(void)}/{len(rows)} 条本轮未能核对，"
              f"其余 {len(rows) - len(void)} 条相符 —— **不是全部通过**")
        return 2
    print(f"上游行数核对通过：{len(rows)} 条声明的行数与 {REF} 逐一相符"
          f"（目录按 .ts/.tsx 求和，文件按自身）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
