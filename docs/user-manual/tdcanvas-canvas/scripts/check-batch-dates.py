#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批次自述日期不得晚于「今天」——第 24 道构建门禁（M227 建立）。

★ **判据只有一条，而且必须是单向的**：

    批次自述的日期 **晚于** 运行这道门禁当天  ⇒  报出来

- **晚于** = 这个批次声称自己发生在一个**还没到**的日子里。**M226 实测就是这个**：
  M193–M199 明明是 10-03 傍晚落库的，标题却写着 10-04。
- **早于或等于** = 当天写的、或跨零点次日提交的，**都不算错**。
  ⚠ **初版想把「与 git 首次落库日不一致」也报出来，那是错的**——
  「当天写、次日提交」很常见（M225 就是声明 10-04、提交 10-05）。
  **只报「晚于」这一侧，判据才窄到能全对。**

★ **为什么这道门禁不看 git**（这正是它能在构建里跑的原因）：
  一个刚写好、**还没提交**的新批次在 git 里根本查不到，
  「与首次落库日比」这种判据**恰恰在最需要它的那一批上失效**。
  而「不得晚于今天」**对新旧批次一视同仁、当场可判、零依赖、瞬时完成**。

另附一个**只在人愿意时跑**的深度对账（不进构建、退出码恒为 0）：
`python3 scripts/check-batch-dates.py . --git` 会额外拿每个批次的
「首次落库日期」对账，能查出「改了旧标题的日期」这一类改坏了的情况。
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

HEADING = re.compile(r"^#{2,4}\s*\*?\*?M(\d+)\s*\*?\*?\s*[（(]\s*(\d{4}-\d{2}-\d{2})", re.M)
# 正文/账本里另一种语序：「2026-10-04 M196」「M194 复核（2026-10-04，…」
# ⚠ 年份**不能写死**：M227 第一版写的是 `2026-`，于是自检注入的「今天+一年」
#   （2027-）内联标注当场漏掉——**这正是本文件注释里警告的「写死日期的锚点会过期」，
#   而它自己就犯了**。判据要能活过跨年。
_DATE_HINT = re.compile(r"\d{4}-\d{2}-\d{2}")
INLINE = re.compile(r"\d{4}-\d{2}-\d{2}[^\n]{0,10}?M(\d+)\b|\bM(\d+)\b[（(]?[^\n]{0,12}?\d{4}-\d{2}-\d{2}")


def main() -> int:
    ap = argparse.ArgumentParser(description="批次自述日期校验")
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--git", action="store_true",
                    help="追加深度对账：与该批次首次落库的提交日期比（慢，不用于构建）")
    ap.add_argument("--deep", type=int, default=6, help="--git 时查最近 N 个批次（默认 6）")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    prog = root / "PROGRESS.md"
    if not prog.is_file():
        print(f"[skip] 找不到 {prog}")
        return 0

    today = dt.date.today()
    heads = HEADING.findall(prog.read_text(encoding="utf-8"))
    if not heads:
        print("[skip] PROGRESS.md 里没有带日期的批次标题")
        return 0

    # ---- 判据一（构建门禁）：自述日期不得晚于今天 ----
    future = []
    for m, ds in heads:
        try:
            d = dt.date.fromisoformat(ds)
        except ValueError:
            print(f"[FAIL] M{m} 的日期不是合法日期：{ds}")
            return 1
        if d > today:
            future.append((m, ds, d))

    # 正文/账本里的内联标注同样受这条约束
    inline_future = []
    for f in sorted(root.rglob("*.md")):
        if ".vitepress" in str(f):
            continue
        txt = f.read_text(encoding="utf-8")
        for i, line in enumerate(txt.split("\n"), 1):
            # ⚠ 这里也不能写死年份。M227 第一版写的是 `if "2026-" not in line`，
            #   于是自检注入的 2027- 内联标注被这一行直接跳过——
            #   **同一个函数里栽了两次同一个坑，而那个坑正是本文件开头警告的**
            #   「写死日期的锚点会过期」。判据要能活过跨年。
            if not _DATE_HINT.search(line):
                continue
            for mo in INLINE.finditer(line):
                ds = mo.group(0)[:10]
                try:
                    d = dt.date.fromisoformat(ds)
                except ValueError:
                    continue
                if d > today:
                    inline_future.append((f.relative_to(root), i, ds, line.strip()[:70]))

    print("=" * 76)
    print(f"[batch-dates] 今天 {today}；PROGRESS.md 带日期批次标题 {len(heads)} 条")
    print("=" * 76)

    problems: list[str] = []
    if future:
        for m, ds, d in future:
            problems.append(
                f"PROGRESS.md 里 M{m} 的标题自述 {ds}，**晚于今天 {today}** —— "
                f"这个批次声称自己发生在一个还没到的日子里（M226 实测过这个病："
                f"M193–M199 是 10-03 傍晚落库的、标题却写着 10-04）")
    if inline_future:
        for rel, ln, ds, snippet in inline_future:
            problems.append(f"{rel}:{ln} 标着 {ds}，**晚于今天 {today}**　{snippet}")

    # ---- 判据二（可选深度对账，不参与构建判定）----
    deep_note = ""
    if args.git:
        repo = root
        for _ in range(8):
            if (repo / ".git").exists():
                break
            repo = repo.parent
        rel = "docs/user-manual/tdcanvas-canvas/PROGRESS.md"
        deep_bad = []
        if (repo / ".git").exists() and str((repo / rel)) == str(prog):
            for m, ds in heads[-max(1, args.deep):]:
                r = subprocess.run(
                    ["git", "log", "--reverse", "--format=%ad", "--date=short",
                     "--pickaxe-regex", "-S", f"^#+ M{m}", "--", rel],
                    cwd=repo, capture_output=True, text=True)
                out = [x.strip() for x in r.stdout.strip().split("\n") if x.strip()]
                if out and ds > out[0]:
                    deep_bad.append((m, ds, out[0]))
        for m, ds, cdate in deep_bad:
            problems.append(f"M{m} 自述 {ds}，晚于该批次首次落库日 {cdate}（git 对账）")
        deep_note = f"（深度对账：最近 {min(args.deep, len(heads))} 个批次）"

    if problems:
        print(f"\n[FAIL] 有 {len(problems)} 处批次日期晚于今天{deep_note}：\n")
        for p in problems:
            print(f"  ★ {p}")
        print("\n  提示：把日期改成这批工作**真正发生**的那一天。")
        print("        「当天写、次日提交」的滞后**不算错**，本门禁只报「晚于今天」这一侧。")
        print("        要看更深的「与 git 首次落库日」对账，跑 --git。")
        return 1

    print(f"[ ok ] {len(heads)} 个批次标题与正文标注的日期均不晚于今天 {today}")
    if deep_note:
        print(f"[ ok ] 深度对账也没发现「改了旧标题日期」的情况{deep_note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
