#!/usr/bin/env python3
"""校验手册里每个 Markdown 表格的语法完整：表头行必须紧跟一行分隔行。

**为什么需要这道检查（M65 实测）**：`shortcuts-help.md` 的「弹窗里的十三条」
表格，被一段多选提示的引用块从**第 8 行和第 9 行之间**劈开了。渲染后果是：

- 前 8 行仍然是一个正常表格；
- 后 5 行（重做 / 重做 / 删除 / Esc / 拖入）**不是表格**——它们没有表头也没有
  分隔行，markdown 解析器把它们当普通段落，产物 HTML 里就是一团
  `| <code>Ctrl / Cmd</code> + <code>Y</code> | 重做 | | ...` 的原始管道文本，
  而且因为引用块在前面，这团乱码还被包进了 blockquote 里。

也就是说，这一页正文写着「逐字抄录，一行不落」，读者实际只能看到 8 条表格 +
5 条乱码。`audit_manual.py` 的全部检查项、`check-claims.py` 的强断言校验、
`check-anchors.py` 的锚点核对**没有一个会报错**——因为从源文件看每一行都还在，
坏掉的只是渲染。这是一类"谁都不会报错、但页面已经坏了"的缺陷。

本脚本按 markdown 的表格语法逐块判定：连续的表格行（以 `|` 开头并以 `|` 结尾）
构成一个块；一个合法的表格块，块内**必须存在一行 `|---|---|` 形式的分隔行，且它前面
至少还有一行**（那一行就是表头）。只有数据行、没有表头与分隔行的块，就是被劈开后
剩下的后半截，或者被误插进正文中间的孤立表格行。

注意这里**不要求分隔行紧跟块首行**：markdown 允许表格跨行延续，先前判定"第 2 行
必须是分隔行"会把「表头 + 分隔行 + 若干数据行」这种完全正常的表格误判为断裂
（AUDIT.md 的三张表就是这样被误报的）。

引用块里的表格行以 `>` 开头，天然不匹配；`node_modules/` 与构建产物目录不在扫描
范围内，本脚本不会去检查第三方 README。

退出码 0 表示所有表格语法完整，1 表示存在被劈开或缺表头的表格。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

DELIMITER_CELL_RE = re.compile(r"^:?-{1,}:?$")


def is_table_row(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|")


def is_delimiter_row(line: str) -> bool:
    if not is_table_row(line):
        return False
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return bool(cells) and all(DELIMITER_CELL_RE.match(cell) for cell in cells)


SKIP_DIRS = {"node_modules", ".vitepress", "dist", ".git"}


def check_file(path: Path, rel: str) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    problems: list[str] = []
    index = 0
    while index < len(lines):
        if not is_table_row(lines[index]):
            index += 1
            continue
        start = index
        while index < len(lines) and is_table_row(lines[index]):
            index += 1
        block = lines[start:index]
        head = block[0].strip()[:52]
        if len(block) < 2:
            problems.append(
                f"{rel}:{start + 1}: 表格块只有 1 行、没有表头与分隔行，"
                f"会渲染成普通段落：{head}"
            )
            continue
        # 合法条件：块内存在分隔行，且它前面至少有一行作表头
        has_header_pair = any(
            is_delimiter_row(row) and pos > 0 for pos, row in enumerate(block)
        )
        if not has_header_pair:
            problems.append(
                f"{rel}:{start + 1}: 这 {len(block)} 行表格行里没有「表头 + |---| 分隔行」"
                f"结构，会整体渲染成原始管道文本（多半是被插在中间的引用块或列表劈开的）："
                f"{head}"
            )
    return problems


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    md_files = sorted(
        path
        for path in root.rglob("*.md")
        if not SKIP_DIRS.intersection(path.relative_to(root).parts)
    )
    if not md_files:
        print("  [表格] 没有找到任何 .md 文件")
        return 1

    problems: list[str] = []
    table_count = 0
    for path in md_files:
        rel = path.relative_to(root).as_posix()
        lines = path.read_text(encoding="utf-8").splitlines()
        index = 0
        while index < len(lines):
            if not is_table_row(lines[index]):
                index += 1
                continue
            table_count += 1
            while index < len(lines) and is_table_row(lines[index]):
                index += 1
        problems.extend(check_file(path, rel))

    for problem in problems:
        print(f"  [表格] {problem}")
    if problems:
        print(f"表格语法校验失败：{len(problems)} 项")
        return 1
    print(f"  [ ok ] 表格语法校验：{len(md_files)} 个文件、{table_count} 个表格块语法完整")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
