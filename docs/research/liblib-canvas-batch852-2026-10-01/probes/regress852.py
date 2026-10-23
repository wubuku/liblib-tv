#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 852 回归：跑既有门禁清单 ⟹ ⟹ 看本批有没有把别的批次弄坏。

## ★ 本批动过的两处**被跟踪**的源码

- `src/components/director/DirectorViewport.tsx`
  （新增 V／R／F／X 快捷键分支；`translationSnap` 的步长由 0.5 改为 1）
- `src/components/director/directorViewportMath.ts`
  （新增 `DIRECTOR_TRANSFORM_SHORTCUT_MODES`／`DIRECTOR_GRID_SNAP_STEP`／
  `resolveDirectorTransformShortcutMode`）

## ★ 清单里**特意加上**吸附相关的五条

★ 本批把吸附步长从 0.5 改成 **1**（源站 `p7(e,t){e.translationSnap=t?1:null}` 逐字），
⟹ ⟹ 所有**引用 snapToGrid** 的门禁都要进回归清单 ⟹ ⟹ 否则「步长改对了」与
「开关语义被改坏了」分不开。★ 清单：`550`／`588`／`741`／`797`／`798`。

## ★ 已知旧账（在 HEAD 上也是红的 ⟹ ⟹ 不是本批引入）

★ `736`／`748`／`749`／`782`／`831` ⟹ ⟹ 受控对照在 `attrib852.py` 里另做
（把源码换回 HEAD 再跑一遍 ⟹ 读数必须逐条相同）。

## 输出

  /tmp/b852-regression.json
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")

BATCHES = [
    "852",  # 本批
    "851", "850", "849", "848", "847", "846", "845", "844", "843", "842", "841",
    "840", "839",
    "830", "831", "543",
    "783", "827", "826", "838", "835",
    "62", "111", "112", "113", "146b", "169",
    "556", "557", "536", "540", "575",
    "46", "36", "720", "42", "43",
    # ★ 吸附相关（本批改了吸附步长 ⟹ ⟹ 这五条必须在清单里）
    "550", "588", "741", "797", "798",
    # ★ 旧账（HEAD 上也红）
    "736", "748", "749", "782",
]

# ★ 本批**动过其比对对象**的门禁（应当全绿 ⟹ ⟹ 红了就说明本批改坏了）
WATCH = ["852", "851", "830", "831", "543", "850", "840", "550", "588"]


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
    outp = pathlib.Path("/tmp/b852-regression.json")
    outp.write_text(json.dumps(results, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    red = [r["batch"] for r in results if r["rc"] not in (0, None)]
    watch_red = [b for b in red if b in WATCH]
    print("\n== 回归：%d 条，红 %d 条 %s ==" % (len(results), len(red), red))
    print("== 盯的 %d 条里红的：%s ==" % (len(WATCH), watch_red))
    return 1 if watch_red else 0


if __name__ == "__main__":
    sys.exit(main())
