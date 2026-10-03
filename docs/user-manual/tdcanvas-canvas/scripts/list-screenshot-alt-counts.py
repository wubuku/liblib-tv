#!/usr/bin/env python3
"""列出正文里所有「带计数的截图 alt」，并把**序数**单独标出来。

**为什么需要它（M204）**：M202 记下手册有「**59 张**截图的 alt 文本里带可数断言」，
并列了 6 张逐一核过的表。**但 59 这个数复现不出来**——M204 试了 8 种判据变体
（单位词表宽窄 × 是否剔除序数），得到的数是 49 / 50 / 56 / 57 / 61 / 63 / 64 / 66，
**没有一个是 59**，59 正好卡在「57」与「61」两个任意选择之间。

**这是 M203 那把从不报警的量具的同一个病**：一个看起来一直在维护的数字，
实际没有任何人能用同样的办法得到它。**手数的计数就是这样——它记录的是当时那一次的
手感，不是一条可重复的规则。** 所以把这个清单固化成工具，让它变成可复现的。

★ **为什么单独标序数**：M199 立可数台账时已经栽过一次——把「第 2/3/4 个图标」这种
  **序数**当成了计数，于是台账里混进了一批根本不是计数的条目。
  M204 实物坐实了这一点：`20-config-en.png` 的 alt 写「**第一步**按钮为 Join AI Tudou · Get API key」，
  「第一步」是**流程上的第几步**，不是「一共有几步」。**这类不能进计数。**

用法：
    python3 scripts/list-screenshot-alt-counts.py            # 打印全量清单
    python3 scripts/list-screenshot-alt-counts.py --summary  # 只打印两个总数

只依赖标准库。只读——**不修改任何文件**。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BODY_PAGES = ["README.md", "00-quickstart.md", "20-reference.md", "30-concepts.md", "90-troubleshooting.md"]
TASK_GLOB = "10-tasks/*.md"

CN = "一二三四五六七八九十两"
# 单位词表（M204 试过宽窄四档，见文件头；这里固定用最宽的一档，
# **故意过包含**，让序数那批也进候选，由 --summary 与人眼去剔）。
UNITS = "个项条档组级步像素行列款张层根道支处次页屏块串"
COUNT_RE = re.compile(rf"(?:共\s*)?[{CN}]\s*[{UNITS}]|\d+\s*[{UNITS}]")
# 序数：第 N 个 / 第 N 步 —— **是流程位置，不是数量**（M199 踩过，M204 实物复现）
#
# ★ **这里踩过一个坑，且是本轮第二次**：`rf"第\s*(?:{CN}|\d)+..."` 里的 `{CN}` 是
#   **十一个字的字面串**不是字符类，正则会去匹配「一二三四五六七八九十两」这一整串，
#   于是「第一步」**永远匹配不上**，序数一条都标不出来。
#   正确写法是 `[{CN}\d]+`。**零结果先怀疑判据**——若不是先看那句「序数 0 条」合不合理，
#   这条错判据会一直安静地输出 0。
ORDINAL_RE = re.compile(rf"第\s*[{CN}\d]+\s*[个项步档章节部分]")

ALT_RE = re.compile(r"^!\[(.*)\]\(([^)]+)\)\s*$")


def iter_alt_lines(root: Path):
    for name in BODY_PAGES:
        path = root / name
        if not path.is_file():
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            m = ALT_RE.match(line.strip())
            if m:
                yield name, lineno, m.group(1), m.group(2)
    for path in sorted(root.glob(TASK_GLOB)):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            m = ALT_RE.match(line.strip())
            if m:
                yield path.name, lineno, m.group(1), m.group(2)


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    root = Path(args[0]).resolve() if args else ROOT
    summary_only = "--summary" in sys.argv

    rows = []
    for page, lineno, alt, img in iter_alt_lines(root):
        if not COUNT_RE.search(alt):
            continue
        hits = sorted({m.group(0) for m in COUNT_RE.finditer(alt)})
        rows.append((img.split("/")[-1], page, lineno, hits, bool(ORDINAL_RE.search(alt))))

    total = len(rows)
    ordinal = [r for r in rows if r[4]]
    real = [r for r in rows if not r[4]]

    if summary_only:
        print(f"[alt-counts] 正文 alt 行 {total} 条带计数候选")
        print(f"  其中含序数（不是计数，应剔） {len(ordinal)} 条")
        print(f"  去掉序数后                  {len(real)} 条")
        return 0

    print(f"{'图片':46} {'位置':34} 命中片段 / 序数")
    print("-" * 118)
    for img, page, lineno, hits, is_ord in sorted(rows):
        where = f"{page}:{lineno}"
        tag = "  ← 序数，非计数" if is_ord else ""
        print(f"{img[:44]:46} {where[:32]:34} {'、'.join(hits)}{tag}")
    print("-" * 118)
    print(f"带计数候选 {total} 条 / 涉及图片 {len({r[0] for r in rows})} 张")
    print(f"  含序数 {len(ordinal)} 条（不是计数，读的时候直接剔掉）")
    print(f"  去掉序数后 {len(real)} 条")
    print()
    print("★ M202 记的「59 张」用本工具**复现不出来**（本工具给的是上面的数）。")
    print("  那是个手数的计数，不是可重复规则的结果——与 M203 那把从不报警的量具同一个病。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
