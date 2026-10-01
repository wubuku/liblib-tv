#!/usr/bin/env python3
"""把本次构建的实测数字回填进 README 的构建统计表。

为什么要有这个脚本：页数 / 截图数 / 体积是**派生数据**。手工维护它们必然过期
——M47 到 M53 连着加了 9 张图，README 里的「76 张截图 / 19M」就再没被更新过，
读者照着它判断手册规模会得到一个静悄悄错掉的答案。

所以让构建直接把实测值写回去。只改表格里**日期为今天**的那一行（没有就新建
一行），历史行保留成一份构建记录。
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

# 表格行形如： | 2026-10-01 | 22 | 85 | 21M |
ROW_RE = re.compile(r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\S+?)\s*\|\s*$")
HEADER_RE = re.compile(r"^\|\s*构建日期\s*\|")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", required=True)
    ap.add_argument("--images", required=True)
    ap.add_argument("--size", required=True)
    ap.add_argument("--readme", default="README.md")
    args = ap.parse_args()

    path = Path(args.readme)
    if not path.is_file():
        print(f"找不到 {args.readme}，跳过回填")
        return 0

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    header_idx = next((i for i, l in enumerate(lines) if HEADER_RE.match(l)), None)
    if header_idx is None:
        print("[warn] README 里找不到构建统计表头（| 构建日期 | 页数 | 截图数 | 体积 |），跳过回填")
        return 0

    today = dt.date.today().isoformat()
    new_row = f"| {today} | {args.pages} | {args.images} | {args.size} |"

    replaced = False
    for i in range(header_idx + 2, len(lines)):
        m = ROW_RE.match(lines[i])
        if m and m.group(1) == today:
            if lines[i] != new_row:
                lines[i] = new_row
            replaced = True
            break
        if m and m.group(1) > today:
            lines.insert(i, new_row)
            replaced = True
            break
        if m and m.group(1) < today:
            continue
        if lines[i].strip() == "":
            lines.insert(i, new_row)
            replaced = True
            break

    if not replaced:
        lines.insert(header_idx + 2, new_row)

    new_text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    if new_text == text:
        print(f"[ ok ] 构建统计表已是最新：{args.pages} 页 / {args.images} 图 / {args.size}")
        return 0

    path.write_text(new_text, encoding="utf-8")
    print(f"[update] 已回填 README 构建统计（今日行）：{args.pages} 页 / {args.images} 图 / {args.size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
