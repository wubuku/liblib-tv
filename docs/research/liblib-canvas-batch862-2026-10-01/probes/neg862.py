#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 862 阴性对照（负控）：**注入缺陷 ⟹ 门禁必须红 ⟹ 字节级还原**。

## ★ 纪律

① 每条变异都**独立**地从原文件开始（不做链式叠加 ⟹ ⟹ 互不污染）；
② 变异必须**行数中性**（只改同一行内的字符串 ⟹ ⟹ 不改变文件行数）；
③ 跑完必须**字节级还原**（sha256 比对）；
④ ★ 归因关键字要**先跑一次变异、读首条红灯的原文，再决定**
   —— 不能按「我以为的落点」写（本脚本的 `--observe` 模式就是干这个的）。

## ★ 变异清单（每条都对应门禁里的一条判据）

| # | 变异 | 应命中的判据 |
|---|---|---|
| N1 | 位置公式 `left: frameWidth - 40` → `- 30` | clone:toggle-sits-at-the-frame-corner-for-* |
| N2 | `title="构图参考线"` → `title="构图参考X"` | clone:toggle-title-for-* |
| N3 | 三分线颜色 `rgba(255,255,255,0.5)` → `0.4` | clone:thirds-are-white-at-50-percent |
| N4 | 框描边 `rgba(255,255,255,0.18)` → `0.28` | source:frame-uses-outline-not-border |
| N5 | 框上开关的 svg path 改一个字符 | source:toggle-icon-path-matches-the-source-verbatim |
| N6 | 三分线恒显示（`{showThirds ? (` → `{true ? (`） | clone:thirds-are-off-before-the-click |
| N7 | 面板 `disabled={!hasCameras}` → `disabled={false}` | source:aspect-panel-keeps-the-source-disabled-contract |

## 用法
  python3 neg862.py --observe     # 只打印每条变异后的首条红灯（用来定归因关键字）
  python3 neg862.py              # 正式模式：断言「红」且「红在预期判据上」
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE = ROOT / "scripts/verify-liblib-batch862.py"
VIEW = ROOT / "src/components/director/DirectorViewport.tsx"
PANEL = ROOT / "src/components/director/DirectorAspectPanel.tsx"

# ★ 源站逐字的 svg path（★ 期望值来自入库的源站原文）
ICON_RAW = ROOT / ("docs/research/liblib-canvas-batch862-2026-10-01/raw/"
                   "source-862-frame-thirds-icon.json")
SOURCE_PATH = ""
try:
    _paths = (json.loads(ICON_RAW.read_text(encoding="utf-8"))
              .get("关态") or {}).get("path") or []
    if _paths:
        SOURCE_PATH = re.search(r'd="([^"]+)"', _paths[0]).group(1)
except Exception:  # noqa: BLE001
    SOURCE_PATH = ""

MUTATIONS = [
    {
        "id": "N1",
        "file": "view",
        "desc": "位置公式 −40 改 −30",
        "old": "left: frameWidth - 40",
        "new": "left: frameWidth - 30",
        "expect": "clone:toggle-sits-at-the-frame-corner-for-",
    },
    {
        "id": "N2",
        "file": "view",
        "desc": "开关 title 改字",
        "old": 'title="构图参考线"',
        "new": 'title="构图参考X"',
        "expect": "clone:toggle-title-for-",
    },
    {
        "id": "N3",
        "file": "view",
        "desc": "三分线颜色 0.5 改 0.4",
        "old": '"rgba(255,255,255,0.5)"',
        "new": '"rgba(255,255,255,0.4)"',
        "expect": "clone:thirds-are-white-at-50-percent",
    },
    {
        "id": "N4",
        "file": "view",
        "desc": "框描边 0.18 改 0.28",
        "old": '"1px solid rgba(255,255,255,0.18)"',
        "new": '"1px solid rgba(255,255,255,0.28)"',
        "expect": "source:frame-uses-outline-not-border",
    },
    {
        "id": "N5",
        "file": "view",
        "desc": "框上开关的 svg path 改一个字符",
        "old": None,          # ★ 运行期按源站 path 定位并改一个字符
        "new": None,
        "expect": "source:toggle-icon-path-matches-the-source-verbatim",
    },
    {
        "id": "N6",
        "file": "view",
        "desc": "三分线恒显示（绕过 showThirds）",
        "old": "{showThirds ? (",
        "new": "{true ? (",
        "expect": "clone:thirds-are-off-before-the-click",
    },
    {
        "id": "N7",
        "file": "panel",
        "desc": "面板 disabled 契约去掉",
        # ★ ★ 锚点必须**带缩进的完整代码行** ⟹ ⟹ 才会命中代码那处，
        #   而不是注释里同名的那份（★ 第一版按裸字面量替换 ⟹ ⟹ 先命中注释
        #   ⟹ ⟹ 代码没变 ⟹ ⟹ 门禁绿是**假绿** ⟹ ⟹ 负控打空）。
        "old": "\n            disabled={!hasCameras}",
        "new": "\n            disabled={false}",
        "expect": "source:aspect-panel-keeps-the-source-disabled-contract",
    },
]

FILES = {"view": VIEW, "panel": PANEL}


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply_mutation(m: dict) -> tuple[bool, str]:
    path = FILES[m["file"]]
    src = path.read_text(encoding="utf-8")
    if m["id"] == "N5":
        if not SOURCE_PATH or SOURCE_PATH not in src:
            return False, "源站 path 不在源码里"
        # ★ 改 path 里的**一个字符**（保持等长 ⟹ 行数与长度都不变）
        mutated = SOURCE_PATH[:20] + ("A" if SOURCE_PATH[20] != "A" else "B") \
            + SOURCE_PATH[21:]
        src = src.replace(SOURCE_PATH, mutated)
    else:
        if m["old"] not in src:
            return False, f"锚点不存在：{m['old']!r}"
        src = src.replace(m["old"], m["new"], 1)
    path.write_text(src, encoding="utf-8")
    return True, ""


def run_gate() -> tuple[int, list[str]]:
    proc = subprocess.run([sys.executable, str(GATE)], cwd=ROOT,
                          capture_output=True, text=True, timeout=900)
    fails = [ln.strip() for ln in proc.stdout.splitlines()
             if ln.strip().startswith("FAILED:")]
    return proc.returncode, fails


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--observe", action="store_true",
                    help="只打印首条红灯（定归因关键字用）")
    args = ap.parse_args()

    backup = ROOT / "docs/research/liblib-canvas-batch862-2026-10-01/raw/.neg-backup"
    backup.mkdir(parents=True, exist_ok=True)
    original = {k: FILES[k].read_bytes() for k in FILES}

    report: list[dict] = []
    for m in MUTATIONS:
        path = FILES[m["file"]]
        path.write_bytes(original[m["file"]])
        ok, why = apply_mutation(m)
        if not ok:
            report.append({"id": m["id"], "desc": m["desc"], "结果": "无法注入",
                           "原因": why})
            continue
        # ★ 行数中性自检
        lines_before = original[m["file"]].decode("utf-8").count("\n")
        lines_after = path.read_text(encoding="utf-8").count("\n")
        rc, fails = run_gate()
        # ★ 字节级还原
        path.write_bytes(original[m["file"]])
        restored = sha(path) == hashlib.sha256(original[m["file"]]).hexdigest()
        entry = {
            "id": m["id"],
            "desc": m["desc"],
            "行数中性": lines_before == lines_after,
            "门禁rc": rc,
            "红条数": len(fails),
            "首条红灯": fails[0] if fails else "",
            "命中预期判据": any(m["expect"] in f for f in fails),
            "字节级还原": restored,
        }
        if not args.observe:
            entry["结果"] = ("PASS" if (rc != 0 and entry["命中预期判据"]
                                       and entry["行数中性"] and restored)
                             else "FAIL")
        report.append(entry)
        print(f"[{m['id']}] {m['desc']} ⟹ rc={rc} 红{len(fails)}条 "
              f"命中预期={entry['命中预期判据']} 行数中性={entry['行数中性']} "
              f"还原={restored}")
        if fails:
            print("    首条红灯:", fails[0][:180])

    for k, data in original.items():
        FILES[k].write_bytes(data)
    shutil.rmtree(backup, ignore_errors=True)

    out = ROOT / ("docs/research/liblib-canvas-batch862-2026-10-01/raw/"
                  "negative-audit.json")
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    if args.observe:
        print("\n（观察模式：未断言）")
        return 0
    bad = [e for e in report if e.get("结果") != "PASS"]
    print(f"\n阴性对照 {len(report) - len(bad)}/{len(report)} 通过")
    for e in bad:
        print("  FAILED:", e.get("id"), e.get("desc"), e.get("首条红灯", "")[:160])
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
