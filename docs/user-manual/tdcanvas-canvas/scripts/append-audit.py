#!/usr/bin/env python3
"""往 AUDIT.md / PROGRESS.md 追加内容，并强制校验表格行的收尾竖线。

**为什么需要这个工具（M65 → M71 连续四次）**：

「已知问题清单」是一张**跨批次连续**的大表，每批都在文件末尾追加若干行。追加
的内容以 `|` 开头、以 ` |` 结尾。这些行都很长（每行两三句话），手写时**漏掉
结尾竖线的笔误已经连续发生四次**：

| 批次 | 后果 |
|---|---|
| M65 | 引用的 blockquote 插进表格中间，13 行表被劈成 8 + 5 两条，后者渲染成原始管道文本 |
| M68 | 追加行漏写收尾 `|`，把表从中间截断 |
| M69 | 同上——直接导致 M69 自己的追加行成了没有表头的孤立块，构建当场 FAIL |
| M70 | 同上，被 M71 构建时抓到 |

四次里 `check-tables.py` 抓到了三次（第四次是 M69 自己踩的），但每次都是
**构建失败后回头排查**才发现，代价是一轮返工。**靠记性解决不了这种"长行末尾
少一个字符"的错误**——所以交给工具。

用法：

    python3 scripts/append-audit.py AUDIT.md <<'EOF'
    | Major(产品) | 某问题 | 某影响 | 某处置 |
    |---|---|---|---|
    EOF

行为：
* 逐行校验——以 `|` 开头的行必须也以 `|` 结尾，缺则**自动补齐**并打印提示；
* 校验衔接——追加的第一行是表格行、而文件最后一行**不是**表格行时，说明新内容
  脱离了原表，直接报错退出（不写盘），避免造出孤立块；
* 追加后立刻用 `check-tables.py` 的判据复查整份文件，语法有问题就整体回滚。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_helpers():
    spec = importlib.util.spec_from_file_location("_ct", HERE / "check-tables.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.is_table_row, module.is_delimiter_row


def main() -> int:
    if len(sys.argv) < 2:
        print("用法：python3 scripts/append-audit.py <目标文件> < 待追加内容", file=sys.stderr)
        return 2
    target = Path(sys.argv[1])
    if not target.is_file():
        print(f"[FAIL] 目标文件不存在：{target}", file=sys.stderr)
        return 2

    is_table_row, is_delimiter_row = load_helpers()
    original = target.read_text(encoding="utf-8")
    incoming = sys.stdin.read()

    # --- 1. 自动补齐收尾竖线 ---
    fixed_lines: list[str] = []
    fixed = 0
    for line in incoming.splitlines():
        if line.startswith("|") and not line.rstrip().endswith("|"):
            line = line.rstrip() + " |"
            fixed += 1
        fixed_lines.append(line)
    patched = "\n".join(fixed_lines) + ("\n" if incoming.endswith("\n") else "")

    # --- 2. 衔接校验：新表格行不能凭空起块 ---
    if fixed_lines and is_table_row(original.splitlines()[-1] if original.splitlines() else ""):
        pass  # 正常延续
    elif fixed_lines and is_table_row(fixed_lines[0]) and original.strip():
        print(
            f"[FAIL] 目标文件最后一行不是表格行，而追加内容的第一行是表格行——"
            f"这会造出一个没有表头的孤立块。先补上表头再追加：\n"
            f"      目标最后一行：{original.splitlines()[-1][:70]!r}\n"
            f"      追加第一行：  {fixed_lines[0][:70]!r}",
            file=sys.stderr,
        )
        return 1

    # --- 3. 追加后整体复查，语法有问题就回滚 ---
    # 判据直接复用 check-tables.py，不另立一套——两套规则迟早会漂移，
    # 而"这个工具说没问题、门禁说有���题"是最难排查的一类矛盾。
    merged = original + ("" if original.endswith("\n") or not original else "\n") + patched
    lines = merged.splitlines()
    index = 0
    while index < len(lines):
        if not is_table_row(lines[index]):
            index += 1
            continue
        start = index
        while index < len(lines) and is_table_row(lines[index]):
            index += 1
        block = lines[start:index]
        has_header_pair = any(
            is_delimiter_row(row) and pos > 0 for pos, row in enumerate(block)
        )
        if len(block) < 2 or not has_header_pair:
            print(
                f"[FAIL] 追加后 {target.name}:{start + 1} 起的 {len(block)} 行表格行"
                f"没有「表头 + |---| 分隔行」结构，已回滚，文件未改动。",
                file=sys.stderr,
            )
            return 1

    target.write_text(merged, encoding="utf-8")
    if fixed:
        print(f"[fix] 自动为 {fixed} 行补上了收尾竖线（长表格行末尾最容易漏）")
    print(f"[ ok ] 已追加 {len(fixed_lines)} 行到 {target.name}，表格语法复查通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
