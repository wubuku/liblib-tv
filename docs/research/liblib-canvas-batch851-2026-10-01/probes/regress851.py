#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 851 回归：确认本批改动**没有翻掉**既有门禁的期望值。

## ★ 本批动过什么（会影响哪些门禁）

1. `src/components/director/DirectorViewport.tsx`
   - 新增 `DirectorViewShortcutController`（T／Y／H／裸 WASDQE）
   - `OrbitControls` 的 `target` 从**字面量** `[0,1,0]` 改成**引用稳定的 state**
     （drei 把 restProps 透传给 `<primitive object={controls}>` ⟹ ⟹ 字面量每次 render
     都会被 R3F apply ⟹ ⟹ 会被 WASDQE 的平移打回）
   - `DirectorCameraSnapshotBridge` 的导演视角 target 从**硬编码** `[0,1,0]`
     改成**读真实 orbit 中心**（默认态仍是 `[0,1,0]` ⟹ ⟹ 零行为变化）
   - 视口 `<section>` 上新增三个 `data-` 属性
2. `src/components/director/directorViewportMath.ts`（新增纯函数，未删改既有导出）

## ★ 批次集合

★ 沿用 batch 850 的同一份列表（便于与上一批横向对比），
★ 再补上与本批**直接相关**的三个：830（导演台快捷键面板）、831（快捷键对话框）、
★ 543（重置视角）⟹ ⟹ 以及本批 851 自己。
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")

BATCHES = [
    "851",  # 本批
    "850", "849", "848", "847", "846", "845", "844", "843", "842", "841", "840", "839",
    "830", "831", "543",
    "783", "827", "826", "838", "835",
    "62", "111", "112", "113", "146b", "169",
    "556", "557", "536", "540", "575",
    "46", "36", "720", "42", "43",
    # ★ 旧账（受控对照在 attrib851.py 里另做）
    "736", "748", "749", "782",
]

# ★ 本批**动过其比对对象**的门禁（应当全绿 ⟹ ⟹ 红了就说明本批改坏了）
WATCH = ["851", "830", "831", "543", "850", "840"]


def run(batch: str) -> dict:
    script = ROOT / ("scripts/verify-liblib-batch%s.py" % batch)
    if not script.exists():
        return {"batch": batch, "rc": None, "verdict": "（无此门禁）"}
    try:
        r = subprocess.run([sys.executable, str(script)], capture_output=True,
                           text=True, timeout=3600, cwd=str(ROOT))
    except subprocess.TimeoutExpired:
        return {"batch": batch, "rc": "timeout", "verdict": "超时"}
    out = (r.stdout or "") + (r.stderr or "")
    verdict = None
    for ln in out.splitlines():
        if ln.strip().endswith("通过") and "/" in ln:
            verdict = ln.strip().split()[-1]
    if verdict is None:
        tail = [x.strip() for x in out.splitlines() if x.strip()][-3:]
        verdict = "rc=%s " % r.returncode + " ／ ".join(tail)[-160:]
    return {"batch": batch, "rc": r.returncode, "verdict": verdict}


def main() -> int:
    results = []
    for b in BATCHES:
        res = run(b)
        results.append(res)
        print("%-6s rc=%-5s %s" % (res["batch"], res["rc"], res["verdict"]), flush=True)
    outp = pathlib.Path("/tmp/b851-regression.json")
    outp.write_text(json.dumps(results, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    print("\n写入", outp)

    watch = [r for r in results if r["batch"] in WATCH]
    bad = [r for r in watch if r["rc"] not in (0,)]
    print("\n=== 本批动过其比对对象的门禁 ===")
    for r in watch:
        print("  %-6s rc=%-5s %s" % (r["batch"], r["rc"], r["verdict"]))
    print("  %s" % ("全部绿 ✓" if not bad else
                    "★★ 有红的 ⟹ 本批改坏了旧门禁的比对 ⟹ ⟹ 需要迁移"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
