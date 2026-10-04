#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批次自述日期 vs 实际落库日期的对账。

★ **它是分析工具，不是门禁，退出码恒为 0。**
  理由是它依赖 `git log -S`（每次查询约 0.7 秒），逐批扫全史要 25 秒，
  **放进 build-site.sh 不划算**；而且加门禁会牵动「二十三道门禁」这个被自检用例
  写死的数字（M193 / M203 两次栽过同一个坑）。**升级成第 24 道门禁是已知的下一步**，
  届时要一并改 build-site.sh、PUBLISH.md 的门禁表与那几处计数锚点。

它抓到什么（M226）：`PROGRESS.md` 里 **M193–M199 共 7 个批次标题自述 2026-10-04，
而它们其实是 2026-10-03 傍晚 18:17–23:46 落库的**；同样的错日期还漏进了 9 处正文与账本。

★ **判据只有一条，而且只有这一条**：

    自述日期 **晚于** 该批次首次落库的提交日期  ⇒  报出来

- **晚于**（`声明 > 提交`）= 这个批次声称自己在一个**它还没发生**的日子里干的 → 错。
- **早于或等于**（`声明 ≤ 提交`）= 当天写、次日提交，**跨零点，属正常**，不报。

用法：
    python3 scripts/audit-batch-dates.py .              # 只查最近 6 个带日期的批次（快）
    python3 scripts/audit-batch-dates.py . --window 99  # 查更多（慢，每个约 0.7 秒）
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

HEADING = re.compile(r"^#{2,4}\s*\*?\*?M(\d+)\s*\*?\*?\s*[（(]\s*(\d{4}-\d{2}-\d{2})", re.M)


def git_first_commit_date(repo: Path, rel: str, needle: str) -> str | None:
    """最早一次让 needle 出现的提交日期；找不到返回 None（多半是还没提交）。"""
    r = subprocess.run(
        ["git", "log", "--reverse", "--format=%ad", "--date=short",
         "--pickaxe-regex", "-S", f"^{needle}", "--", rel],
        cwd=repo, capture_output=True, text=True)
    out = [x.strip() for x in r.stdout.strip().split("\n") if x.strip()]
    return out[0] if out else None


def main() -> int:
    ap = argparse.ArgumentParser(description="批次自述日期 vs 实际落库日期（分析工具，非门禁）")
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--window", type=int, default=6,
                    help="只查最近 N 个带日期的批次标题（默认 6；越大越慢）")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    repo = root
    for _ in range(8):                      # 一路往上找 .git
        if (repo / ".git").exists():
            break
        if repo.parent == repo:
            break
        repo = repo.parent
    if not (repo / ".git").exists():
        print(f"[skip] 从 {root} 往上找不到 .git，如实跳过。")
        return 0

    rel = "docs/user-manual/tdcanvas-canvas/PROGRESS.md"
    prog = repo / rel
    if not prog.is_file():
        print(f"[skip] 找不到 {rel}，如实跳过。")
        return 0

    heads = HEADING.findall(prog.read_text(encoding="utf-8"))
    if not heads:
        print("[skip] PROGRESS.md 里没有带日期的批次标题")
        return 0
    print(f"[读数] PROGRESS.md 带日期的批次标题 {len(heads)} 条：M{heads[0][0]}–M{heads[-1][0]}")

    todo = heads[-max(1, args.window):]
    print(f"[读数] 本次查最近 {len(todo)} 个：{'、'.join('M' + m for m, _ in todo)}"
          f"（查全部 {len(heads)} 个约需 {len(heads) * 0.7:.0f} 秒）")

    bad, ok, skipped = [], [], []
    for m, declared in todo:
        cdate = git_first_commit_date(repo, rel, f"#+ M{m}")
        if cdate is None:
            skipped.append((m, declared))
            continue
        (bad if declared > cdate else ok).append((m, declared, cdate))

    print("=" * 72)
    print(f"[结论] 相符或「跨零点滞后」 {len(ok)}　★ **自述晚于落库（不可能）** {len(bad)}　"
          f"尚未提交、查不到 {len(skipped)}")
    print("=" * 72)
    if bad:
        print("\n--- ★ 自述日期晚于该批次的首次落库日期：这批次声称自己在还没发生的日子里干的 ---")
        for m, d, c in bad:
            print(f"  M{m:<5} 自述 {d}　实际首次落库 {c}")
    if skipped:
        print("\n--- 尚未提交（新批次就是这种），跳过 ---")
        print("  ", '、'.join(f'M{m}({d})' for m, d in skipped))
    if ok:
        print("\n--- 通过（声明 ≤ 提交，属跨零点或补记，不算错）---")
        print("  ", '、'.join(f'M{m}: {d}→{c}' for m, d, c in ok))

    print(
        "\n★ 判读：只有「自述 **晚于** 落库」是错；「自述早于落库」是当天写、次日提交，正常。\n"
        "  ★ 用 `--window` 调大可以回溯更早的批次；发现历史遗留时按同样的判据改。\n"
        "[info] 本工具退出码恒为 0，不参与 build-site.sh 的门禁序列。"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
