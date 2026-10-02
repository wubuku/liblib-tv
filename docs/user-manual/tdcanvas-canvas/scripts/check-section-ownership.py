#!/usr/bin/env python3
"""内容归属校验（第十九道门禁，M146 新增）。

**背景（M146 查的是一次真实的错位，不是一次假想故障）**：

M145 给 15 条排障条目批量补上「→ 相关任务页」出口。**第一版把其中 2 处
插到了章节标题（`##`）下，而不是目标条目（`###`）下**。症状极隐蔽：

- 文件结构没坏，`###` 条目数仍是 36；
- **十八道既有门禁全部全绿**；
- 但那两条出口挂在了错误的章节上，**读者点进去到的是另一个问题**。

**为什么既有门禁全都抓不到**：它们各自负责的判据是——语法（`check-tables`）、
链接指向的文件存在（`check-anchors`）、链接目标的文件存在（`check-dist-links`）、
锚点在产物里真实存在（`check-render`）、页面闭环（`check-structure`）……
**没有一道问「你这段内容属于哪个标题」**。位置是所有判据的盲区。

**判据要机械可判，否则就是假门禁**：本门禁只管一件事——
**「→ 相关任务页」这类出口行，必须归属于某个 `###` 条目，不能落在 `##` 章节标题下。**
这是从 M145 那 2 处真实错位里数出来的唯一形态，**不是照惯例编的**。

**它的边界（必须如实说清）**：

- 只校验**出口标记行**，不校验普通正文——普通正文换个段落位置不影响语义，
  而出口行是给读者导航的，**挂错章节就是导向了另一个问题**；
- 只在有 `###` 条目结构的页面（排障页等）生效，没有条目结构的页面直接跳过；
- **不校验出口指向的任务页对不对**——那是内容判断，由人负责。

用法：

    python3 scripts/check-section-ownership.py .
"""

from __future__ import annotations

import sys
from pathlib import Path

EXIT_MARK = "→ **相关任务页**"


def check_page(page: Path, rel: str, problems: list[str]) -> int:
    """返回本页出口行总数；归属失败的写进 problems。"""
    lines = page.read_text(encoding="utf-8").splitlines()
    if not any(l.startswith("### ") for l in lines):
        return 0  # 没有条目结构，跳过（不是所有页都有 ### 条目）
    in_fence = False
    cur_item: str | None = None
    exits = 0
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("### "):
            cur_item = line[4:].strip()
        elif line.startswith("## "):
            cur_item = None  # 进入新章节，本章节开头处还没进任何条目
        if EXIT_MARK in line:
            exits += 1
            if cur_item is None:
                owner = "（未归属任何 ### 条目，很可能挂在 ## 章节标题下）"
                problems.append(f"{rel}:{i + 1}: 出口行归属错误 → {owner}")
    return exits


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    skip = {"node_modules", ".vitepress", "dist", ".git"}
    pages = [p for p in sorted(root.rglob("*.md")) if not skip & set(p.parts)]

    problems: list[str] = []
    total = 0
    for page in pages:
        total += check_page(page, page.relative_to(root).as_posix(), problems)

    for p in problems:
        print(f"  [归属] {p}")
    if problems:
        print(f"内容归属校验失败：{len(problems)} 处出口行挂在错误位置")
        return 1
    print(f"  [ ok ] 内容归属校验：{total} 处「相关任务页」出口全部归属于正确的条目")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
