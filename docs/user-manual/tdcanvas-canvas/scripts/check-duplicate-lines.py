#!/usr/bin/env python3
"""正文里不许出现连续两行完全相同的非空行（第二十三道门禁，M201 新增）。

**起因是一次真实的编辑事故，不是一次假想故障**：

M201 复查 `edit-nodes.md` 时发现，M137 那段引用块的**同一行连续出现了两遍**：

    > **2026-10-03 M137 补 ComfyUI 行、并订正那句汇总**：本表此前**整类漏掉了 ComfyUI 工作流节点**。
    > **2026-10-03 M137 补 ComfyUI 行、并订正那句汇总**：本表此前**整类漏掉了 ComfyUI 工作流节点**。

**它不会被任何一道既有门禁抓到**：表格语法是对的、链接是对的、锚点是对的、
`check-claims.py` 看的是「强断言有没有证据」而这行有证据、`check-retractions.py`
盯的是已订正说法有没有复活而这行不是订正、**可数断言台账**盯的是「短语还对不对得上」
而这行根本不在台账里。**21 道门禁全绿，页面上就是多了一行。**

**为什么它是个真问题而不是排版洁癖**：引用块里的重复行会让读者以为**说了两遍**，
进而以为后面那句是补充或强调；实际上它是同一句话。而 M201 正是被它绊了一下——
**读的时候先看到那行重复，才回头去查「这一段到底测过没有」**。

**判据为什么能全对**：全手册扫下来命中 **0 处**（M201 实测，26 个文件）。
窄到没有误报余地，才配当门禁（M195 立的规矩）。

**唯一的合法例外已排除**：围栏代码块里**两行相同的示例输出**（比如控制台连打三行 `OK`）
是完全正常的写法。所以判据**跳过围栏内部**——只管散文。
反向对照也钉住了这一点，见 `selftest-gates.py` 的 `mutate_dupe_line_in_code_fence_ok`。

用法：
    python3 scripts/check-duplicate-lines.py .
"""

from __future__ import annotations

import sys
from pathlib import Path

SKIP_DIRS = ("node_modules", ".vitepress", "dist")
FENCE = ("```", "~~~")


def md_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for p in sorted(root.rglob("*.md")):
        rel = str(p.relative_to(root))
        if any(rel.startswith(d) or f"/{d}/" in rel or rel.endswith(f"/{d}")
               for d in SKIP_DIRS):
            continue
        out.append(p)
    return out


def scan(text: str) -> list[tuple[int, str]]:
    """返回 [(行号, 该行)]，只报围栏之外的连续重复非空行。"""
    hits: list[tuple[int, str]] = []
    prev = ""
    in_fence = False
    marker = ""
    for i, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        # 围栏判定：整行以 ``` 或 ~~~ 开头即开/合；记录是哪一种，闭合要用同一种
        if line.startswith(FENCE):
            m = line[:3]
            if not in_fence:
                in_fence, marker = True, m
            elif m == marker:
                in_fence, marker = False, ""
            prev = ""          # 围栏行本身不参与「与上一行比较」
            continue
        if in_fence:
            prev = ""              # ★ 围栏内部的重复是合法的，不报
            continue
        if line and line == prev:
            hits.append((i, line))
        prev = line
    return hits


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    files = md_files(root)
    if not files:
        print("[重复行] 一份 Markdown 都没找到，判据多半失效了。")
        return 1

    problems: list[str] = []
    total = 0
    for p in files:
        for lineno, line in scan(p.read_text(encoding="utf-8")):
            problems.append(f"{p.relative_to(root)}:{lineno}  {line[:100]}")

    if problems:
        print(f"[重复行] {len(problems)} 处连续重复行：")
        for s in problems:
            print("  - " + s)
        print(
            "\n  连续两行一模一样，读者会以为「说了两遍」。多半是打补丁时重复写入了一行。\n"
            "  删掉其中一行即可。**围栏代码块内部的重复不报**——示例输出连打两行 `OK` 是正常的。"
        )
        return 1

    print(f"  [ ok ] 重复行：{len(files)} 个文件、{total} 处（围栏内部已排除）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
