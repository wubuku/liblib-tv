#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 862 阴性对照（补）：**batch 35 判据迁移**必须有牙。

★ 背景：batch 860 按源站实测把**初始取景比例**改成「自适应」⟹ ⟹
  「刚打开导演台时取景框不在场」（源站逐字 `if(!e) return void p(null)`）
  ⟹ ⟹ `verify-liblib-batch35.py` 那条「**直接读**取景框」的判据**必然超时**
  ⟹ ⟹ 它是 **batch 860 引入的老门禁旧前提**（本批扩大回归清单才第一次看见）。
★ 本批把它**迁移**成结构性判据：**先选比例，再读框**。

## ★ 两条变异（都要能翻红）

| # | 变异 | 期望 |
|---|---|---|
| M1 | 还原**旧前提**（去掉「先选比例」那一步）⟹ ⟹ 直接读框 ⟹ ⟹ 必然超时 | 红（TimeoutError） |
| M2 | 把比例断言的期望值改错（16/9 → 4/3）⟹ ⟹ 证明**比例断言本身**有牙 | 红（AssertionError） |

★ 变异**行数中性**（只改同一行内的内容，不增删行）；
★ 跑完**字节级**复原 ＋ SHA-256 自检。

## 输出
  docs/research/liblib-canvas-batch862-2026-10-01/raw/negative-migration35.json
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE = ROOT / "scripts/verify-liblib-batch35.py"
OUT = ROOT / ("docs/research/liblib-canvas-batch862-2026-10-01/raw/"
              "negative-migration35.json")

MUTATIONS = [
    {
        "id": "M1",
        "desc": "还原旧前提（去掉「先选比例」，直接读框）",
        "pairs": [
            # ★ ★ 两行换两行 ⟹ ⟹ **行数中性**（第一版把两行并成一行 ⟹ ⟹
            #   行数减 1 ⟹ ⟹ 判据里的「行数中性」项是 False ⟹ ⟹ 不算通过）
            ("    page.locator('[data-director-aspect=\"16:9\"]').click()\n"
             "    frame = page.locator(\"[data-director-aspect-frame]\")",
             "    # ★ 变异 M1：还原旧前提 ⟹ ⟹ 去掉「先选比例」这一步\n"
             "    frame = page.locator(\"[data-director-aspect-frame]\")"),
            ("    frame.wait_for(state=\"visible\", timeout=15_000)",
             "    pass  # ★ 变异 M1：去掉「等框出现」⟹ ⟹ 直接读 ⟹ ⟹ 必然超时"),
        ],
        "expect": "TimeoutError",
    },
    {
        "id": "M2",
        "desc": "比例断言的期望值改错（16/9 → 4/3）",
        "pairs": [
            ("    assert abs(frame_16_9[\"width\"] / frame_16_9[\"height\"] - 16 / 9) < 0.02",
             "    assert abs(frame_16_9[\"width\"] / frame_16_9[\"height\"] - 4 / 3) < 0.02"),
        ],
        "expect": "AssertionError",
    },
]


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_gate() -> tuple[int, str]:
    proc = subprocess.run([sys.executable, str(GATE)], cwd=ROOT,
                          capture_output=True, text=True, timeout=1800)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def main() -> int:
    original = GATE.read_bytes()
    base_sha = hashlib.sha256(original).hexdigest()
    report = []
    try:
        for m in MUTATIONS:
            src = original.decode("utf-8")
            for old, new in m["pairs"]:
                if old not in src:
                    report.append({"id": m["id"], "结果": "锚点不存在",
                                   "锚点": old[:60]})
                    src = None
                    break
                src = src.replace(old, new, 1)
            if src is None:
                continue
            GATE.write_text(src, encoding="utf-8")
            lines_before = original.decode("utf-8").count("\n")
            lines_after = GATE.read_text(encoding="utf-8").count("\n")
            rc, out = run_gate()
            tail = [x.strip() for x in out.splitlines() if x.strip()][-6:]
            hit = m["expect"] in out
            report.append({
                "id": m["id"], "desc": m["desc"],
                "行数中性": lines_before == lines_after,
                "rc": rc, "红": rc != 0, "命中期望签名": hit,
                "尾部": tail,
                "结果": "PASS" if (rc != 0 and hit
                                  and lines_before == lines_after) else "FAIL",
            })
            print(f"[{m['id']}] {m['desc']} ⟹ rc={rc} 红={rc != 0} "
                  f"命中签名={hit} 行数中性={lines_before == lines_after}")
            for t in tail[-3:]:
                print("    ", t[:160])
            # 复原
            GATE.write_bytes(original)
    finally:
        GATE.write_bytes(original)

    restored = sha(GATE) == base_sha
    bad = [r for r in report if r.get("结果") != "PASS"]
    OUT.write_text(json.dumps({"报告": report, "字节级还原": restored},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n迁移阴性 {len(report) - len(bad)}/{len(report)} 通过；字节级还原={restored}")
    for r in bad:
        print("  FAILED:", r.get("id"), r.get("desc"), r.get("尾部"))
    return 1 if bad or not restored else 0


if __name__ == "__main__":
    raise SystemExit(main())
