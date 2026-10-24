#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 863 阴性对照（负控）：**注入缺陷 ⟹ 门禁必须红 ⟹ 字节级还原**。

## ★ 纪律

① 每条变异都**独立**地从原文件开始（不做链式叠加 ⟹ ⟹ 互不污染）；
② 变异必须**行数中性**（只改同一行内的字符串 ⟹ ⟹ 不改变文件行数）；
③ 跑完必须**字节级还原**（sha256 比对）；
④ ★ 归因关键字要**先跑一次变异、读首条红灯的原文，再决定**
   —— 不能按「我以为的落点」写（本脚本的 `--observe` 模式就是干这个的）。
⑤ ★ ★ **锚点必须带属性前缀**（`className="…"` / `maskComposite: "…"`）
   —— ★ 因为**注释里逐字抄了同一串**（batch 859/862 的教训）：
   按裸字面量替换会**先命中注释** ⟹ ⟹ 代码没变 ⟹ ⟹ 门禁绿是**假绿**
   ⟹ ⟹ 负控打空。

## ★ 变异清单（每条都对应门禁里的一条判据）

| # | 变异 | 应命中的判据 |
|---|---|---|
| N1 | `maskComposite: "exclude"` → `"add"` | clone:the-red-probe-proves-the-mask-hollows-the-frame |
| N2 | 遮罩类 `bg-black/20` → `bg-black/40` | clone:the-mask-is-black-at-20-percent-for- |
| N3 | 遮罩类 `backdrop-blur-md` → `backdrop-blur-sm` | clone:the-mask-blurs-the-backdrop-for- |
| N4 | mask 尺寸 `${frameRect.height}px` → `${frameRect.height - 10}px` | clone:the-mask-hole-matches-the-frame-size-for- |
| N5 | mask 位置 `${frameRect.top}px` → `${frameRect.top + 10}px` | clone:the-mask-hole-matches-the-frame-position-for- |
| N6 | 把框的 `9999px` box-shadow 加回来 | source:the-frame-no-longer-carries-a-9999px-box-shadow |
| N7 | 容器类去掉 `z-10` | clone:the-container-pierces-no-pointer-for- |

## 用法
  python3 neg863.py --observe     # 只打印每条变异后的首条红灯（用来定归因关键字）
  python3 neg863.py              # 正式模式：断言「红」且「红在预期判据上」
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE = ROOT / "scripts/verify-liblib-batch863.py"
VIEW = ROOT / "src/components/director/DirectorViewport.tsx"

# ★ ★ 每条变异都**独立**注入 ⟹ ⟹ 互不污染
MUTATIONS = [
    {
        "id": "N1",
        "desc": "mask 合成改成 add（不再挖空）",
        "old": 'maskComposite: "exclude"',
        "new": 'maskComposite: "add"',
        "expect": "clone:the-red-probe-proves-the-mask-hollows-the-frame",
    },
    {
        "id": "N2",
        "desc": "遮罩黑度 20% 改 40%",
        "old": 'className="absolute inset-0 bg-black/20 backdrop-blur-md"',
        "new": 'className="absolute inset-0 bg-black/40 backdrop-blur-md"',
        "expect": "clone:the-mask-is-black-at-20-percent-for-",
    },
    {
        "id": "N3",
        "desc": "背景模糊 md 改 sm",
        # ★ ★ 锚点必须带**换行** ⟹ ⟹ 否则会先命中注释里那一份
        #   （`//   (0,i.jsx)("div",{className:"absolute inset-0 bg-black/20 backdrop-blur-md",`
        #   ⟹ ⟹ 代码没变 ⟹ ⟹ 负控打空 ⟹ ⟹ 假绿）。
        "old": 'backdrop-blur-md"\n',
        "new": 'backdrop-blur-sm"\n',
        "expect": "clone:the-mask-blurs-the-backdrop-for-",
    },
    {
        "id": "N4",
        "desc": "mask 挖空的高度 −10px",
        "old": "${frameRect.height}px",
        "new": "${frameRect.height - 10}px",
        "expect": "clone:the-mask-hole-matches-the-frame-size-for-",
    },
    {
        "id": "N5",
        "desc": "mask 挖空的位置 +10px",
        "old": "${frameRect.top}px",
        "new": "${frameRect.top + 10}px",
        "expect": "clone:the-mask-hole-matches-the-frame-position-for-",
    },
    {
        "id": "N6",
        "desc": "把框的 9999px box-shadow 加回来",
        "old": 'borderRadius: "12px",',
        "new": 'borderRadius: "12px", boxShadow: "0 0 0 9999px rgba(0,0,0,0.24)",',
        "expect": "source:the-frame-no-longer-carries-a-9999px-box-shadow",
    },
    {
        "id": "N7",
        "desc": "容器类去掉 z-10",
        "old": 'className="pointer-events-none absolute bottom-0 left-0 right-0 '
               'top-0 z-10"',
        "new": 'className="pointer-events-none absolute bottom-0 left-0 right-0 '
               'top-0"',
        "expect": "clone:the-container-pierces-no-pointer-for-",
    },
]


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def apply_mutation(src: str, m: dict) -> tuple[bool, str, str]:
    """★ 返回 (成功, 原因, **变异后的源码**)。

    ★ ★ 第一版这里算出了 `mutated` 却**没返回** ⟹ ⟹ 调用方写回的是**原文**
    ⟹ ⟹ 7 条变异**一条都没落地** ⟹ ⟹ 门禁全绿 ⟹ ⟹ 负控 0/7 打空。
    ⟹ ⟹ 「负控打空」的第一嫌疑永远是「变异根本没注入」。
    """
    if m["old"] not in src:
        return False, f"锚点不存在：{m['old']!r}", src
    if m["old"] == m["new"]:
        return False, "锚点与替换值相同", src
    idx = src.index(m["old"])
    mutated = src[:idx] + m["new"] + src[idx + len(m["old"]):]
    if mutated == src:
        return False, "替换后内容没变", src
    return True, "", mutated


def run_gate() -> tuple[int, list[str]]:
    proc = subprocess.run([sys.executable, str(GATE)], cwd=ROOT,
                          capture_output=True, text=True, timeout=1200)
    fails = [ln.strip() for ln in proc.stdout.splitlines()
             if ln.strip().startswith("FAILED:")]
    if not fails:
        # ★ 门禁若**崩了**（CRASH），首条红灯可能不在 stdout ⟹ ⟹ 把 stderr 也带出来
        for ln in (proc.stderr or "").splitlines():
            if ln.strip():
                fails.append("CRASH-STDERR: " + ln.strip())
                break
    return proc.returncode, fails


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--observe", action="store_true",
                    help="只打印首条红灯（定归因关键字用）")
    args = ap.parse_args()

    original = VIEW.read_bytes()
    report: list[dict] = []
    try:
        for m in MUTATIONS:
            VIEW.write_bytes(original)
            src = original.decode("utf-8")
            ok, why, mutated = apply_mutation(src, m)
            if not ok:
                report.append({"id": m["id"], "desc": m["desc"], "结果": "无法注入",
                               "原因": why})
                print(f"[{m['id']}] 无法注入：{why}")
                continue
            # ★ 行数中性自检
            lines_before = src.count("\n")
            VIEW.write_text(mutated, encoding="utf-8")
            lines_after = VIEW.read_text(encoding="utf-8").count("\n")
            # ★ ★ 注入自检：**文件里必须真的出现了新值**（不然就是「变异没落地」）
            injected = m["new"].rstrip("\n") in VIEW.read_text(encoding="utf-8")
            # ★ 等 dev server 重编（运行时判据要看到新源码）
            time.sleep(10)
            rc, fails = run_gate()
            # ★ 字节级还原
            VIEW.write_bytes(original)
            restored = sha_bytes(VIEW.read_bytes()) == sha_bytes(original)
            entry = {
                "id": m["id"],
                "desc": m["desc"],
                "行数中性": lines_before == lines_after,
                "变异已落地": injected,
                "门禁rc": rc,
                "红条数": len(fails),
                "首条红灯": fails[0] if fails else "",
                "命中预期判据": any(m["expect"] in f for f in fails),
                "字节级还原": restored,
            }
            if not args.observe:
                entry["结果"] = ("PASS" if (rc != 0 and entry["命中预期判据"]
                                           and entry["行数中性"] and injected
                                           and restored)
                                 else "FAIL")
            report.append(entry)
            print(f"[{m['id']}] {m['desc']} ⟹ rc={rc} 红{len(fails)}条 "
                  f"命中预期={entry['命中预期判据']} 行数中性={entry['行数中性']} "
                  f"已落地={injected} 还原={restored}", flush=True)
            if fails:
                print("    首条红灯:", fails[0][:200])
    finally:
        VIEW.write_bytes(original)
        restored_all = sha_bytes(VIEW.read_bytes()) == sha_bytes(original)
        print(f"★ 最终还原自检：{restored_all}")

    out = ROOT / ("docs/research/liblib-canvas-batch863-2026-10-01/raw/"
                  "negative-audit.json")
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    if args.observe:
        print("\n（观察模式：未断言）")
        return 0
    bad = [e for e in report if e.get("结果") != "PASS"]
    print(f"\n阴性对照 {len(report) - len(bad)}/{len(report)} 通过")
    for e in bad:
        print("  FAILED:", e.get("id"), e.get("desc"), e.get("首条红灯", "")[:200])
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
