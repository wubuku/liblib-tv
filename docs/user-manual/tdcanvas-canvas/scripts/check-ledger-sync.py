#!/usr/bin/env python3
"""正文改动与账本同步的提示性校验（第二十一道门禁，M155 新增）。

**背景（M155 查的是一次真实缺口，不是一次假想故障）**：

M154 实测：M105 之后有 18 个批次改过面向读者的正文页，
而账本 `task-inventory.yml` 的 `review_note` **最新只到 M104**——
M136/M137 那种实测结论（含 M137 **补上整类缺失的 ComfyUI 节点**）在账本里查不到出处。
M154 补了 15 条。**但「记得补」靠的是记性，而记性已经在 M108 到 M154 之间失效过两次**
（`RETRACTIONS` 停在 M108、账本停在 M104）。

**★ 这道门禁刻意「不判定对错」，只负责把该看的批次列出来。**

原因是一个真实的失败：**M155 第一版尝试用 PROGRESS 里的词频自动区分
「运行时取证批次」与「审计/门禁批次」，结果完全不可靠**——
M137 是明确的逐节点实测却被判成「偏审计」（因为它也提了两次"门禁"），
M134 是全书对撞复查却被判成「偏运行时」。**又是一次「用不可靠的方式建立分类，然后信了它」。**

所以本门禁**不猜批次性质**。它只报一行事实：

    这一批改了正文页，但没同步 task-inventory.yml

**这不是错误，是提醒。** 改审计措辞、补可达性出口这类批次**本来就不该动账本**——
把它们算成错误，只会逼着维护者往账本里灌流水账（M154 明确拒绝过这么做）。

**它是门禁，但退出码恒为 0**，并且在输出里写明这一点——
**一个永远不会失败的检查，就不该假装是检查**。
真正的把关在 `check-inventory-evidence.py`（账本自身是否自洽）与人的判断上。

**为什么仍值得做成脚本**：M154 那次靠的是我临时 `git log` 一遍。
**下一次谁还会记得去跑？** 把它固定下来，代价只有几十行。

用法：

    python3 scripts/check-ledger-sync.py <手册根>
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

MAN_DIR = "docs/user-manual/tdcanvas-canvas/"
BODY_PREFIXES = (
    "10-tasks/", "README.md", "00-quickstart.md", "20-reference.md",
    "30-concepts.md", "90-troubleshooting.md",
)
LEDGER = "task-inventory.yml"
INTERNAL = ("AUDIT.md", "PROGRESS.md", "PUBLISH.md", "SOURCE_OBSERVATIONS.md")
DEPTH = 40


def collect(repo: Path) -> list[tuple[str, str, list[str], list[str]]]:
    """返回 [(批次号, 标题, 改过的正文页, 是否动了账本)]。"""
    try:
        done = subprocess.run(
            ["git", "log", "--format=%H%x09%s", "--name-only", f"-{DEPTH}", "--", MAN_DIR],
            capture_output=True, text=True, cwd=str(repo), timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"  [账本同步] 读不到 git 历史：{exc}")
        print("           手册仓若是从别处拷贝的、没有 .git，本检查直接跳过。")
        return []
    if done.returncode != 0:
        print(f"  [账本同步] git log 失败，跳过（退出码 {done.returncode}）")
        return []

    commits, cur = [], None
    for line in done.stdout.splitlines():
        if re.match(r"^[0-9a-f]{40}\t", line):
            if cur:
                commits.append(cur)
            sha, subj = line.split("\t", 1)
            cur = {"subj": subj, "files": []}
        elif cur is not None and line.strip().startswith(MAN_DIR):
            cur["files"].append(line.strip()[len(MAN_DIR):])
    if cur:
        commits.append(cur)

    rows = []
    for c in commits:
        body = [f for f in c["files"]
                if f.startswith(BODY_PREFIXES) and not f.startswith(INTERNAL)]
        if not body:
            continue
        led = [f for f in c["files"] if f == LEDGER]
        m = re.search(r"\bM(\d{2,3})\b", c["subj"])
        rows.append((f"M{m.group(1)}" if m else "(无批次号)", c["subj"], body, led))
    return rows


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    repo = root
    for _ in range(6):  # scripts/ → tdcanvas-canvas/ → user-manual/ → docs/ → 仓根
        if (repo / ".git").exists():
            break
        repo = repo.parent
    else:
        print("  [账本同步] 没找到 .git，跳过（手册仓不带版本历史时无从核对）")
        return 0

    rows = collect(repo)
    if not rows:
        print("  [账本同步] 无可核对的历史提交，跳过")
        return 0

    unsynced = [r for r in rows if not r[3]]
    if unsynced:
        print(f"  [提醒] 以下 {len(unsynced)} 个批次改了正文页、但那个提交里没有同时改 {LEDGER}——")
        print("         ★ **读法务必看清：这说的是「那一批当时没同步」，"
              "不是「账本现在缺内容」。**")
        print("         后续批次完全可以回头补（M154 就是回头给 M107–M137 补了 15 条），"
              "补完之后这些批次**仍然会出现在这份清单里**——"
              "因为它看的是提交历史，不是账本的当前状态。")
        print("         **它也不判断对错**：改审计措辞、补可达性出口这类批次本就不该动账本。")
        print("         只有**新增或修改了某个任务的实测结论**时，才需要同步。")
        for tag, subj, body, _ in unsynced[:12]:
            print(f"           {tag:10} {', '.join(f.split('/')[-1] for f in body[:3])}")
        if len(unsynced) > 12:
            print(f"           ……另有 {len(unsynced) - 12} 个批次（只看最近 {DEPTH} 个提交）")

    print(
        f"  [ ok ] 账本同步提示：核对最近 {DEPTH} 个提交里改过本目录的 {len(rows)} 个批次，"
        f"其中 {len(unsynced)} 个「当批未同步账本」"
        "（提示性检查，**退出码恒为 0，不阻断构建**；"
        "**账本内容的完整性由 check-inventory-evidence.py 负责**）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
