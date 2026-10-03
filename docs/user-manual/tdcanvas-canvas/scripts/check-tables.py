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


def cell_count(line: str) -> int | None:
    """数一行的**未转义**竖线分段数；不是表格行时返回 None。

    **转义的竖线（`\|`）不算分隔符**——单元格里出现字面 `|` 时必须写成 `\|`，
    那是 M175 踩过的坑。`append-audit.py` 追加的表格行全是未转义竖线，
    所以本函数能如实数出「两行被拼成一行」造成的多余格子。
    """
    stripped = line.strip()
    if not stripped.startswith("|"):
        return None
    body = re.split(r"(?<!\\)\|", stripped)
    # 首尾两个空段对应行首与行尾的竖线，不算内容格子
    inner = body[1:-1] if len(body) >= 2 else []
    return len(inner)


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


# M184：这四份是**内部账本**，由 config.mjs 的 srcExclude 排除、读者看不到。
# 它们的表格欠账是 M65 就在册的历史问题（表被引用块从中间劈开的 61 行），
# 一次性清完不属于本门禁的职责；**但欠账不许再长**——
# 超过下面这个基线仍然报错，并在输出里逐处点名。
INTERNAL_PAGES = {"AUDIT.md", "PROGRESS.md", "SOURCE_OBSERVATIONS.md", "TEST_MEDIA_ASSETS.md"}

# 基线 = 引入本检查时各内部页的「格子数多于表头」存量条数。
# **刻意用计数而不是行号**：这些文件天天在追加，行号会漂，计数不会。
# 有人顺手修掉一处，计数下降是好事；门禁只在**增长**时报错。
KNOWN_MORE_CELLS_BASELINE = {"AUDIT.md": 0, "PROGRESS.md": 0, "SOURCE_OBSERVATIONS.md": 0, "TEST_MEDIA_ASSETS.md": 0}


def check_file(path: Path, rel: str, known: dict | None = None, short: dict | None = None) -> list[str]:
    # M184 自己踩过的坑：**形参同名局部变量会把传进来的字典整个遮掉**，
    # 收集器永远填不上、统计恒为 0，而门禁照样报 ok——**静默失效最难发现**。
    # 这里的两个收集器都必须挂在形参上，任何「再起一个同名变量」的写法都不许回来。
    known = known if known is not None else {}
    short_rows = short if short is not None else {}
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
        # M184：**列数必须与表头一致**。
        # 此前这道检查不存在，于是 M183 把 4 行拼成 1 行写进 AUDIT（中间 3 个 `||` 产生空单元格），
        # 整行 21 格混进 4 列表格——**渲染器会把多余的格子连同内容一起丢弃**，
        # 而 check-tables 报 ok、check-render 也报 ok，**两道门禁同时失明**。
        # 判据：按未转义的 `|` 切分（`\|` 不算分隔），表头、分隔行与每一行的列数必须全等。
        head_cols = cell_count(block[0])
        if head_cols is not None:
            for offset, row in enumerate(block):
                cols = cell_count(row)
                if cols is None or cols == head_cols:
                    continue
                if cols < head_cols:
                    # **少格在 CommonMark 里是合法的**——缺的格子渲染成空单元格，不会丢内容。
                    # 所以它不算错，只记数（`short_rows`），**不阻断构建**。
                    # 一律报错会让这道门禁变成噪声源，而噪声源会被无视。
                    short_rows.setdefault(rel, []).append(f"{rel}:{start + 1 + offset}")
                    continue
                detail = (
                    f"{rel}:{start + 1 + offset}: 这一行有 {cols} 个格子，"
                    f"而表头是 {head_cols} 列（第 {start + 1 + offset} 行起算于表头）。"
                    f"**多余的格子连同里面的内容会被渲染器直接丢弃**——"
                    f"最常见的原因是**把两行拼成了一行**："
                    f"相邻两行各以竖线结尾又以竖线开头，中间就成了两个相连的竖线"
                )
                if rel in INTERNAL_PAGES:
                    # 内部页：只记进欠账，**但不让它再长**
                    known.setdefault(rel, []).append(detail)
                else:
                    # 发布页：读者看得见，**一律报错**
                    problems.append(detail)
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
    known: dict[str, list[str]] = {}
    short: dict[str, list[str]] = {}
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
        problems.extend(check_file(path, rel, known, short))

    # M184：内部账本的存量欠账**逐处点名**——不点名就等于「已知不管」，
    # 而点名之后，谁新增了一处一眼就能看见，也就不用等到计数越线才知道。
    for rel in sorted(INTERNAL_PAGES):
        items = known.get(rel, [])
        base = KNOWN_MORE_CELLS_BASELINE.get(rel)
        tag = "内部页" if rel in INTERNAL_PAGES else "发布页"
        if base is None:
            print(f"  [表格欠账·{tag}] {rel}：{len(items)} 处，但基线未登记（这本身是漏登记）")
            problems.append(
                f"{rel} 有 {len(items)} 处「格子数多于表头」的表格行，"
                f"但 KNOWN_MORE_CELLS_BASELINE 里没有登记它的基线——"
                f"**欠账必须先有基线才能被守住**，请补登记"
            )
        elif len(items) > base:
            problems.append(
                f"{rel} 的「格子数多于表头」从基线 {base} 处涨到了 {len(items)} 处"
                f"（新增 {len(items) - base} 处）。**内部页的表格欠账不许增长**——"
                f"新增处见下：\n    " + "\n    ".join(items[base:])
            )
        else:
            state = "持平" if len(items) == base else "已修掉 %d 处" % (base - len(items))
            print(f"  [表格欠账·{tag}] {rel}：{len(items)} 处（基线 {base}，{state}）")

    for rel, items in sorted(short.items()):
        print(
            f"  [表格·少格·不算错] {rel}：{len(items)} 行格子数少于表头。"
            f"CommonMark 里这是合法的（缺格渲染成空），**不阻断构建**"
        )

    for problem in problems:
        print(f"  [表格] {problem}")
    if problems:
        print(f"表格语法校验失败：{len(problems)} 项")
        return 1
    print(f"  [ ok ] 表格语法校验：{len(md_files)} 个文件、{table_count} 个表格块语法完整，行内代码反引号全部成对")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
