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

═══════════ M231 追加：同一族的第二个字段「截图拍摄日期」═══════════

`screenshots/manifest.yml` 的 `captured_at` 是**同一族的手写日期**——
它同样是「人打上去的断言」，而不是机器派生的值，所以同样会写错。**判据同样是单向的**：

  · **判据一（构建门禁，瞬时零依赖）**：`captured_at` **晚于今天** ⇒ 报出来。
    这条能抓住「把日期填到未来」，抓不住本批实测的那一类——见下。
  · **判据二（`--git` 深度对账）**：**一张图不可能在它入库之后才被拍出来。**
    所以 `captured_at` **晚于该 PNG 最后一次被提交的日期** ⇒ 报出来。
    ★ **M231 实测抓到 6 条**：这 6 条 PNG 各自只有一次提交（作者日与提交者日都是 2026-10-02），
    而清单里写的是 `captured_at: '2026-10-03'`——**晚了一天，在物理上不可能**。
    它们与「生成结果 > 历史版本 > 节点内容」无关，纯粹是**日期写错了一天**。

★ **为什么判据二不做进构建，而 `--git` 模式值得每批跑一次**：
判据二必须知道 git 历史，**没克隆就没法判**，所以它留在深度模式里；
但它**只需一次 `git log --name-only`**（实测 **0.63 秒**拿到全部 112 张图的入库日），
**比这个文件里原有的逐批 pickaxe 对账（实测 5.3 秒）便宜一个数量级**——
**所以 `--git` 从「偶尔想起来跑」变成了「每批都跑得动」。**

另附一个**只在人愿意时跑**的深度对账（不进构建）：
`python3 scripts/check-batch-dates.py . --git` 会额外拿每个批次的
「首次落库日期」对账，能查出「改了旧标题的日期」这一类改坏了的情况；
M231 又给它加上了上面那条「拍摄日期 vs 入库日」的全量对账。
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
    ap.add_argument("--no-manifest", action="store_true",
                    help="只校批次标题，不校截图清单的 captured_at")
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

    # ---- 判据一（构建门禁）第二项：截图清单的 captured_at 不得晚于今天 ----
    shots_future = []
    shots: list[tuple[str, str]] = []
    mf = root / "screenshots" / "manifest.yml"
    if not args.no_manifest and mf.is_file():
        for i, line in enumerate(mf.read_text(encoding="utf-8").split("\n"), 1):
            m = re.match(r"\s*captured_at:\s*'?(\d{4}-\d{2}-\d{2})'?", line)
            if not m:
                continue
            ds = m.group(1)
            shots.append((f"screenshots/manifest.yml:{i}", ds))
            try:
                if dt.date.fromisoformat(ds) > today:
                    shots_future.append((i, ds))
            except ValueError:
                print(f"[FAIL] manifest.yml:{i} 的 captured_at 不是合法日期：{ds}")
                return 1

    print("=" * 76)
    print(f"[batch-dates] 今天 {today}；PROGRESS.md 带日期批次标题 {len(heads)} 条；"
          f"截图清单 captured_at {len(shots)} 条")
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
    for ln, ds in shots_future:
        problems.append(
            f"screenshots/manifest.yml:{ln} 的 captured_at 是 {ds}，**晚于今天 {today}** —— "
            f"这张图声称拍摄于一个还没到的日子里")

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
        shots_deep_bad = []
        shots_git_covered = 0
        # ★ M231：截图清单的全量对账。**一次 git log 就够**——
        #   `git log --name-only` 会把每个文件**最后一次**被改动的提交日吐出来，
        #   而这正是我们要的上界（重拍的图只会更晚，不会更早）。
        #   实测 0.63 秒拿满 112 张，比下面那个逐批 pickaxe 便宜一个数量级。
        # ★ 必须先算出**手册目录相对 repo 根的路径**再传给 git log。
        #   清单里的 `file:` 是手册内相对路径（`screenshots/x.png`），而 git log
        #   的 cwd 是 repo 根，**pathspec 按 cwd 解释**。第一版漏了这个前缀，
        #   于是 git log 匹配到 0 个文件、`last` 是空字典、循环空转，
        #   门禁一路报「全部通过」——**一个一直在假装通过的假阴性门禁**。
        #   ⚠ 这个坑是靠 M231 的注入验证抓到的，不是靠读代码看出来的：
        #   注入一条「日期是过去、但晚于入库日」的坏数据，深度模式居然 exit 0。
        #   **零结果先怀疑判据和实现，别急着宣布通过。**
        sub = rel.rsplit("/", 1)[0] if "/" in rel else ""
        if (repo / ".git").exists() and shots and str((repo / rel)) == str(prog):
            rels: list[str] = []
            for line in mf.read_text(encoding="utf-8").split("\n"):
                m = re.match(r"\s*-\s*file:\s*(\S+)", line)
                if m:
                    rels.append(f"{sub}/{m.group(1)}" if sub else m.group(1))
            shots_git_covered = 0
            if rels:
                r2 = subprocess.run(
                    ["git", "log", "--pretty=format:%x01%ad", "--date=short", "--name-only", "--"] + rels,
                    cwd=repo, capture_output=True, text=True)
                last: dict[str, str] = {}
                cur = None
                for line in r2.stdout.split("\n"):
                    if line.startswith("\x01"):
                        cur = line[1:].strip()
                        continue
                    name = line.strip()
                    if name and cur and name not in last:
                        last[name] = cur
                shots_git_covered = len(last)
                # 建立 file -> captured_at 的映射（按清单出现顺序）
                # ⚠ 键必须和上面 git log 吐出来的名字同一形状（都带手册前缀），
                #   否则 get() 永远落空、判据静默失效。
                fmap: dict[str, str] = {}
                cur_f = None
                for line in mf.read_text(encoding="utf-8").split("\n"):
                    m2 = re.match(r"\s*-\s*file:\s*(\S+)", line)
                    if m2:
                        cur_f = f"{sub}/{m2.group(1)}" if sub else m2.group(1)
                        continue
                    mc = re.match(r"\s*captured_at:\s*'?(\d{4}-\d{2}-\d{2})'?", line)
                    if mc and cur_f:
                        fmap[cur_f] = mc.group(1)
                        cur_f = None
                for name, cdate in sorted(last.items()):
                    ds = fmap.get(name)
                    if ds and ds > cdate:
                        shots_deep_bad.append((name, ds, cdate))
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
        for name, ds, cdate in shots_deep_bad:
            problems.append(
                f"{name} 的 captured_at 是 {ds}，**晚于它最后一次入库的日期 {cdate}** —— "
                f"一张图不可能在提交之后才被拍出来")
        # ★ 覆盖不全**本身就是一条问题**。第一版就是靠这一条缺失而假装通过的：
        #   判据零结果时，先问「判据看到了多少条」，再问「判据说没问题吗」。
        shots_git_missing = max(0, len(shots) - shots_git_covered) if args.git else 0
        if shots_git_missing:
            problems.append(
                f"截图清单有 {shots_git_missing} 张图在 git 历史里查不到，"
                f"所以这一轮只对账了 {shots_git_covered}/{len(shots)} 张 —— "
                f"**没被对账到的图不等于没问题**，请先确认路径对不对")
        deep_note = (f"（深度对账：最近 {min(args.deep, len(heads))} 个批次"
                     f" + 截图清单拍摄日对账 {shots_git_covered}/{len(shots)} 张："
                     f"{'异常 ' + str(len(shots_deep_bad)) + ' 条' if shots_deep_bad else '全部通过'}）")

    if problems:
        print(f"\n[FAIL] 有 {len(problems)} 处批次日期晚于今天{deep_note}：\n")
        for p in problems:
            print(f"  ★ {p}")
        print("\n  提示：把日期改成这批工作**真正发生**的那一天。")
        print("        「当天写、次日提交」的滞后**不算错**，本门禁只报「晚于今天」这一侧。")
        print("        要看更深的「与 git 首次落库日」对账，跑 --git。")
        return 1

    print(f"[ ok ] {len(heads)} 个批次标题与正文标注的日期均不晚于今天 {today}")
    if shots:
        print(f"[ ok ] 截图清单 {len(shots)} 条 captured_at 均不晚于今天 {today}")
    if deep_note:
        print(f"[ ok ] 深度对账也没发现「改了旧标题日期」的情况{deep_note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
