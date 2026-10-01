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


def fenced_code_lines(lines: list[str]) -> set[int]:
    """返回处于围栏代码块内的行号（0-based）。

    **为什么需要（M71 实测）**：手册多处需要**展示**表格写法本身，例如
    `PUBLISH.md` 教人怎么往账本追加记录时给出一行 `| 级别 | 描述 | 影响 | 处置 |`。
    这类行以 `|` 开头、以 `|` 结尾，**形态与真表格完全一样**，但它们在代码块里——
    markdown 不会把它们解析成表格。第一版判据因此把示例报成了"孤立表格块"，
    而如果为了绕过它去改示例，就等于**让判据迁就错误**。

    围栏代码块以 ``` 或 ~~~ 开头（缩进不超过 3 个空格），块内一切内容都跳过。
    """
    inside: set[int] = set()
    fence: str | None = None
    for number, line in enumerate(lines):
        stripped = line.strip()
        if fence is None:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                fence = stripped[:3]
                inside.add(number)
            continue
        inside.add(number)
        if stripped.startswith(fence):
            fence = None
    return inside


def check_code_spans(lines: list[str], code: set[int], rel: str) -> list[str]:
    """检查围栏代码块之外，行内代码（`code`）的反引号是否成对。

    **为什么需要这道检查（M84 实测）**：本脚本原先只管**列数**与**表头结构**，
    抓不到一类"列数完全正确、渲染却是坏的"的错误——**行内代码里嵌了行内代码**。

    M84 往 `PROGRESS.md` 写源码引用时写了这么一行：

        | 源码 | `title={port.description \\|\\| \\`${port.label}\\`}` —— 原生 title |

    列数是对的（本脚本报 ok），但按 CommonMark，**行内代码段内部不处理反斜杠转义**：
    里面那个反引号会被当成收尾标记，于是外层代码段在它这里就结束了，产物里这一格
    的代码高亮从中间断掉、后面半截变成正文。同批还有一处更隐蔽的落单反引号
    （`父文本「90%`」`），会在**整段**末尾开一个永远不闭合的代码段。

    判据分两种粒度：

    - **表格行按单元格判**——GFM 是"先切单元格、再解析行内内容"，所以跨单元格的
      行内代码根本不成立。嵌套反引号写在单元格里时，一格的反引号数必然是奇数
      （外层 1 个 + 内层成对 2 个），而**整行的列数完全正确**。这正是列数校验的盲区。
    - **其余行按段落判**（空行分隔的连续非围栏行累计）。markdown 允许行内代码跨行，
      按行数会误报，按段落累计既能覆盖跨行，又能把"整个列表 6 个反引号、其中一个
      条目少一个"这种真实错误抓出来。
    """
    problems: list[str] = []
    start: int | None = None
    count = 0

    def flush() -> None:
        nonlocal start, count
        if start is not None and count % 2 == 1:
            problems.append(
                f"{rel}:{start + 1}: 这一段共 {count} 个反引号（奇数），"
                f"有行内代码没闭合，会把后面的正文一起吞进代码高亮："
                f"{lines[start].strip()[:52]}"
            )
        start, count = None, 0

    for number, line in enumerate(lines):
        if number in code:
            continue
        if is_table_row(line):
            # 表格行：与段落累计分开，逐个单元格判奇偶。
            # 注意**只能按未转义的竖线切**——单元格里常出现 `\|\|`（表格内的
            # 逻辑或），按裸 `|` 切会把一格劈成两半，两半的反引号数都是奇数，
            # 变成纯误报。GFM 的切分规则同样忽略转义竖线。
            for cell in re.split(r"(?<!\\)\|", line.strip().strip("|")):
                ticks = cell.count("`")
                if ticks % 2 == 1:
                    problems.append(
                        f"{rel}:{number + 1}: 表格单元格里出现 {ticks} 个反引号（奇数），"
                        f"多半是在行内代码里又嵌了行内代码——列数是对的，但这一格的"
                        f"代码高亮会从中间断掉：{cell.strip()[:44]}"
                    )
            flush()
            continue
        if not line.strip():
            flush()
            continue
        if start is None:
            start = number
            count = 0
        count += line.replace("\\|", "").count("`")
    flush()
    return problems


def check_file(path: Path, rel: str) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    code = fenced_code_lines(lines)
    problems: list[str] = []
    index = 0
    while index < len(lines):
        if index in code or not is_table_row(lines[index]):
            index += 1
            continue
        start = index
        while index < len(lines) and index not in code and is_table_row(lines[index]):
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
    problems.extend(check_code_spans(lines, code, rel))
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
        code = fenced_code_lines(lines)
        index = 0
        while index < len(lines):
            if index in code or not is_table_row(lines[index]):
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
    print(f"  [ ok ] 表格语法校验：{len(md_files)} 个文件、{table_count} 个表格块语法完整，行内代码反引号全部成对")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
