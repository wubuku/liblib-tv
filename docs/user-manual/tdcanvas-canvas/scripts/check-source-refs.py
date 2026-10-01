#!/usr/bin/env python3
"""源码引用校验：手册里每处 `文件.ts:行号` 必须指向应用仓里**真实存在的那一行**。

背景（M109）：手册通篇用 `file:line` 指向源码，全书共 140 处。它们是读者唯一能自己
复核"这条结论从哪来"的把手——**但行号会随源码推进而漂移，而没有任何机制守着它**。
账本锁定门禁（`check-ledger-pin.py`）只在**应用仓 HEAD 变了**时报错，可一旦有人
把账本 sha 一起更新到新提交，这道门禁就重新变绿，而正文里那 140 处行号可能早已
指向别处。**读者点着行号跳过去，看到的不是那行代码，结论就无法复核。**

本批的触发点很具体：我在 M108 的 AUDIT 里把 `canvas-node.tsx:1117` 误写成
`1103`——同一行内容，两处行号差 14。这类错误肉眼极难发现，正是该机械拦下的。

本门禁只做**能被完全机械判定**的那一半：

* 从正文页抽出 `路径:行号` 与 `路径:起-止` 两种引用；
* 按**路径后缀**在应用仓里解析文件（`index.tsx` 在仓内有 6 个同名文件，
  只按文件名匹配必然误判，后缀匹配是唯一可靠解法）；
* 校验起止行号都落在该文件实际行数之内；
* 路径在本机不存在时**跳过而不是失败**——手册仓会被 clone 到别的机器，
  硬编码本地路径不能变成"在别人机器上必然红"的门禁（与 check-ledger-pin.py 同）。

**明确不做什么**：不判断"那一行的内容是否真的是手册说的那件事"。那需要理解语义，
没有可靠机械判据，硬凑只会重演 M62（654 条误报）、M93（43 条）、M105（17 条）。
本门禁管的是**行号有没有指空**，语义正确性靠逐条人工核对。

用法：

    python3 scripts/check-source-refs.py .
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

APP_REPO = Path("/Users/yangjiefeng/Documents/AICoderTudou/TDCanvas")
SRC_ROOT = "web/src"

# 与 check-retractions.py 保持同一套扫描面：排除的是「订正史」载体
# （它们必须原样记下"当时写的是什么"），账本要扫——它记的是当前事实。
EXCLUDED = {"AUDIT.md", "PROGRESS.md", "TEST_MEDIA_ASSETS.md", "PUBLISH.md"}
BODY_PAGES = [
    "README.md",
    "00-quickstart.md",
    "20-reference.md",
    "30-concepts.md",
    "90-troubleshooting.md",
    "SOURCE_OBSERVATIONS.md",
]
BODY_GLOBS = ["10-tasks/*.md"]

# 路径可含目录分隔符；行号可写成 N 或 N-M
REF_RE = re.compile(r"([A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:ts|tsx|js|jsx|mjs|mts|css)):(\d+)(?:-(\d+))?")
SOURCE_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".mts", ".css"}


def iter_body_pages(root: Path):
    for name in BODY_PAGES:
        page = root / name
        if page.is_file() and name not in EXCLUDED:
            yield page
    for pattern in BODY_GLOBS:
        for page in sorted(root.glob(pattern)):
            if page.name not in EXCLUDED:
                yield page


def build_index(src_root: Path) -> list[Path]:
    return [p for p in src_root.rglob("*") if p.is_file() and p.suffix in SOURCE_SUFFIXES]


def resolve(files: list[Path], ref_path: str) -> tuple[Path | None, int]:
    """按路径后缀解析。返回 (唯一命中的文件, 命中数)。"""
    want = ref_path.replace("\\", "/").lstrip("./")
    hits = [p for p in files if p.as_posix().endswith(want)]
    return (hits[0] if len(hits) == 1 else None), len(hits)


def main(argv: list[str]) -> int:
    root = Path(argv[1] if len(argv) > 1 else ".").resolve()
    src_root = APP_REPO / SRC_ROOT

    if not src_root.is_dir():
        print(f"  [skip] 本机没有应用仓源码（{src_root}），跳过源码引用校验")
        print("[ ok ] 源码引用校验：本机无应用仓，已跳过")
        return 0

    files = build_index(src_root)
    if not files:
        print(f"[FAIL] 应用仓源码目录存在但一个源文件都没扫到：{src_root}")
        return 1

    problems: list[str] = []
    checked = 0
    per_file: dict[str, set[tuple[int, int]]] = {}
    line_count: dict[Path, int] = {}

    def n_lines(p: Path) -> int:
        if p not in line_count:
            with p.open(encoding="utf-8", errors="replace") as fh:
                line_count[p] = sum(1 for _ in fh)
        return line_count[p]

    for page in iter_body_pages(root):
        for lineno, line in enumerate(page.read_text(encoding="utf-8").splitlines(), 1):
            for m in REF_RE.finditer(line):
                ref_path, start, end_s = m.group(1), int(m.group(2)), m.group(3)
                end = int(end_s) if end_s else start
                checked += 1
                hit, n = resolve(files, ref_path)
                where = f"{page.relative_to(root)}:{lineno}"
                if n == 0:
                    problems.append(
                        f"[{where}] 引用了不存在的文件：{ref_path}:{m.group(2)}"
                        f"（在 {src_root} 下按路径后缀找不到同名文件）"
                    )
                elif n > 1:
                    problems.append(
                        f"[{where}] 引用路径有歧义：{ref_path}:{m.group(2)}"
                        f" 在 {src_root} 下匹配到 {n} 个文件，请写够目录前缀"
                    )
                elif end > n_lines(hit) or start > n_lines(hit):
                    problems.append(
                        f"[{where}] 行号越界：{ref_path}:{m.group(2)}"
                        f"（该文件实际只有 {n_lines(hit)} 行）"
                    )
                elif start > end:
                    # 区间写成 `foo.ts:999999-269` 这种倒挂时，光看终点是发现不了的
                    # ——终点 269 完全合法。**起点和终点都必须校验，且起点不得大于终点。**
                    problems.append(
                        f"[{where}] 区间倒挂：{ref_path}:{m.group(2)}"
                        f"（起点 {start} 大于终点 {end}，这处引用已经不是一次正常的行号漂移）"
                    )
                else:
                    per_file.setdefault(ref_path, set()).add((start, end))

    if problems:
        print(f"[FAIL] 源码引用校验未通过（{len(problems)} 项）：")
        for p in problems:
            print(f"  {p}")
        print("    这些行号是读者复核结论的唯一把手。请逐条核对：")
        print("      ① 内容没变、只是行号漂了 → 更新行号；")
        print("      ② 内容也变了 → 复核结论本身是否仍成立，变了就登记订正。")
        return 1

    files_n = len(per_file)
    print(
        f"[ ok ] 源码引用校验：{checked} 处 file:line 引用（{files_n} 个源文件）"
        f"全部指向真实存在的行"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
