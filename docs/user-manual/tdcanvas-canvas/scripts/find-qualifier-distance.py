#!/usr/bin/env python3
"""A/C 类限定词与它限定的那句话之间的行距分布（M256 测量，非门禁）

**先量分布，再决定判据。** 这是 M195 那条纪律的直接应用：
窄不到能全对，就别假装是门禁。

用法：
    python3 scripts/find-qualifier-distance.py .
    python3 scripts/find-qualifier-distance.py . --json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HEADING = "## 14. 绝对断言登记表"
KINDS = ("A 有限定词", "B 绝对成立", "C 已订正")
EMPHASIS = re.compile(r"[*`_]")


def strip_markup(text: str) -> str:
    return EMPHASIS.sub("", text)


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    as_json = "--json" in sys.argv
    src = root / "SOURCE_OBSERVATIONS.md"
    text = src.read_text(encoding="utf-8")
    if HEADING not in text:
        print("[skip] 找不到 §14")
        return 0
    body = text.split(HEADING, 1)[1]
    rows = []
    for line in body.split("\n"):
        if line.startswith("## ") and "14." not in line[:8]:
            break
        if not line.startswith("| A") and "| A" not in line[:6]:
            continue
        cells = line.split("|")
        if len(cells) < 6:
            continue
        rows.append([c.strip() for c in cells[1:5]])

    out = []
    for rid, frag, kind, qual in rows:
        if kind not in ("A 有限定词", "C 已订正"):
            continue
        if "#" not in frag:
            out.append({"id": rid, "error": "片段没有 #", "frag": frag})
            continue
        fname, anchor = frag.split("#", 1)
        fname = fname.strip().strip("`").strip()
        anchor = strip_markup(anchor)
        target = root / fname
        if not target.is_file():
            out.append({"id": rid, "error": "文件不存在", "fname": fname})
            continue
        lines = target.read_text(encoding="utf-8").splitlines()

        # needle 命中行
        hits = [i + 1 for i, l in enumerate(lines) if anchor in strip_markup(l)]
        # 限定词命中行（沿用门禁的切法：按 ; 切，每段 >= 6 字）
        needles = [n.strip() for n in re.split(r"[；;]", strip_markup(qual)) if len(n.strip()) >= 6]
        qhits = {n: [i + 1 for i, l in enumerate(lines) if n in strip_markup(l)] for n in needles}

        # ★ 关键量：**每个 needle 片段到 needle 命中行集合的最近行距**
        gaps = []
        for n, hl in qhits.items():
            if not hits:
                gaps.append(None)
                continue
            if not hl:
                gaps.append(-1)          # 片段在这页里根本找不到
                continue
            gaps.append(min(abs(h - q) for h in hits for q in hl))

        out.append({
            "id": rid, "kind": kind, "file": fname,
            "anchor": anchor, "anchor_lines": hits,
            "needle_count": len(neededs if (neededs := needles) else []),
            "min_gap": min(g for g in gaps if g is not None) if gaps else None,
            "gaps": gaps,
            "qual": qual,
        })

    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0

    print(f"{'ID':5} {'类型':10} {'最小行距':>8}  文件 / 锚点")
    print("-" * 78)
    for r in sorted(out, key=lambda x: (x.get("min_gap") is None, x.get("min_gap") if x.get("min_gap") is not None else 10**6)):
        if "error" in r:
            print(f"{r['id']:5} {'—':10} {'ERR':>8}  {r['error']}: {r.get('frag') or r.get('fname')}")
            continue
        g = r["min_gap"]
        mark = "" if (g is not None and g <= 3) else "   ←"
        print(f"{r['id']:5} {r['kind']:10} {str(g):>8}  {r['file']}  锚点行 {r['anchor_lines']}{mark}")
        if r["gaps"] and len(r["gaps"]) > 1:
            print(f"{'':5} {'':10} {'':>8}  各片段行距 {r['gaps']}")

    finite = [r["min_gap"] for r in out if isinstance(r.get("min_gap"), int) and r["min_gap"] >= 0]
    if finite:
        import statistics
        print()
        print(f"可量行数 = {len(finite)}  中位数 = {statistics.median(finite)}  最大 = {max(finite)}")
        for w in (0, 1, 2, 3, 5, 10, 20):
            inside = sum(1 for g in finite if g <= w)
            print(f"  窗口 ±{w:2d} 行：{inside}/{len(finite)} 条在窗内  ({inside * 100 // len(finite)}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
