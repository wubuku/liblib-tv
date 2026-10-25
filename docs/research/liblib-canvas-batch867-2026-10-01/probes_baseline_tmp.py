#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""★ batch 867 取证：★ 跑「依赖已消失的 `/tmp` 文件」的那批门禁 ⟹ ⟹ 拿基线。

★ 为什么要跑它们：★ batch 866 建立的纪律是「回归清单是一份旧前提普查表」
⟹ ⟹ ★ 那么「**清单之外**」的门禁坏了 ⟹ ⟹ 就没人知道
⟹ ⟹ ★ 本批先普查：**哪些门禁依赖 `/tmp` 下已经消失的文件**
⟹ ⟹   ⟹ ⟹ 那些门禁**必然红** ⟹ ⟹ 而且它们的红**从来没人看见**。
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUT = ROOT / "docs/research/liblib-canvas-batch867-2026-10-01/raw/baseline-tmp-deps.json"

# ★ 清单：★ 「依赖已消失的 /tmp 文件」的门禁（★ 由普查脚本算出 ⟹ ⟹ 不手打）
TARGETS = [
    "554", "562", "565", "719", "750", "751", "753", "754", "755",
    "756", "757", "758", "759", "760", "761", "802", "542", "546",
]


def run(batch: str) -> dict:
    script = ROOT / ("scripts/verify-liblib-batch%s.py" % batch)
    if not script.exists():
        return {"batch": batch, "rc": None, "verdict": "（无此门禁）"}
    try:
        r = subprocess.run([sys.executable, str(script)], capture_output=True,
                           text=True, timeout=1800, cwd=str(ROOT))
    except subprocess.TimeoutExpired:
        return {"batch": batch, "rc": "timeout", "verdict": "超时"}
    out = (r.stdout or "") + (r.stderr or "")
    tail = [x.strip() for x in out.splitlines() if x.strip()][-4:]
    verdict = None
    for ln in out.splitlines():
        if ln.strip().endswith("通过") and "/" in ln:
            verdict = ln.strip().split()[-1]
    if verdict is None:
        verdict = "rc=%s ／ %s" % (r.returncode, " ／ ".join(tail)[-200:])
    return {"batch": batch, "rc": r.returncode, "verdict": verdict}


def main() -> int:
    results = []
    for b in TARGETS:
        res = run(b)
        results.append(res)
        print("%-5s rc=%-6s %s" % (res["batch"], res["rc"], res["verdict"][:110]), flush=True)
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    red = [r["batch"] for r in results if r["rc"] not in (0, None)]
    print("\n★ 共 %d 条，红 %d 条：%s" % (len(results), len(red), red))
    print("★ 读数已落盘：%s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
