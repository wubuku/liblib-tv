#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 861 回归：跑既有门禁清单 ⟹ ⟹ 看本批有没有把别的批次弄坏。

## ★ 本批动过的**被跟踪**源码（本批：画幅比例**真的驱动机位取景框**）

- `src/store/directorStore.ts`
  （新增**取景比例**状态 `frameAspectRatio`（七档数值 ＋ `null`＝自适应）
  ＋ action `setFrameAspectRatio` ＋ 数值表；★ **导出比例 `aspectRatio` 不动**）
- `src/components/director/directorViewportMath.ts`
  （`getDirectorFrameRect` 改成吃**任意数值比例**；`null` ⟹ ⟹ 不画框）
- `src/components/director/DirectorAspectPanel.tsx`
  （★ 七格**接到 store** —— 此前是组件内 `useState` ⟹ ⟹ 点哪档都不动）
- `src/components/director/DirectorViewport.tsx`
  （`AspectFrame` 改读取景比例 ＋ 底部那三枚也接同一状态 ＋
  截图链的导出比例另起变量名）

★ ★ 本批**动了左侧资源栏的呈现模型** ⟹ ⟹ 所有**看那个区域**的门禁都必须进清单
（`45`／`536`／`541`／`589`／`590`／`613`／`617`／`619`／`625`／`626`／
`648`／`738`／`857`）⟹ ⟹ 否则「面板对了」与「别的地方塌了」分不开。

## ★ 清单覆盖两类门禁

- **`.py`** ＝ 既有 Python 门禁（有的会起浏览器 ⟹ ⟹ **串行**跑）
- **`.mjs`** ＝ 静态断言门禁（`node` 跑）

## 输出

  /tmp/b860-regression.json
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
NODE = pathlib.Path.home() / ".nvm/versions/node/v24.6.0/bin/node"

# ★ (批次号, 扩展名) ⟹ ⟹ 显式写清楚，不靠「猜扩展名」
GATES = [
    ("856", "py"),
    ("854", "py"),
    ("853", "py"),
    ("852", "py"),
    ("851", "py"),
    ("850", "py"),
    ("849", "py"),
    ("848", "py"),
    ("847", "py"),
    ("846", "py"),
    ("845", "py"),
    ("844", "py"),
    ("843", "py"),
    ("842", "py"),
    ("841", "py"),
    ("840", "py"),
    ("839", "py"),
    ("830", "py"),
    ("831", "py"),
    ("543", "py"),
    ("783", "py"),
    ("827", "py"),
    ("826", "py"),
    ("838", "py"),
    ("835", "py"),
    ("62", "py"),
    ("111", "py"),
    ("112", "py"),
    ("113", "py"),
    ("146b", "py"),
    ("169", "py"),
    ("556", "py"),
    ("557", "py"),
    ("536", "py"),
    ("538", "py"),
    ("540", "py"),
    ("575", "py"),
    ("46", "py"),
    ("36", "py"),
    ("720", "py"),
    ("42", "py"),
    ("43", "py"),
    ("550", "py"),
    ("588", "py"),
    ("741", "py"),
    ("797", "py"),
    ("798", "py"),
    ("45", "py"),
    ("47", "py"),
    ("48", "py"),
    ("49", "py"),
    ("50", "py"),
    ("91", "py"),
    ("59", "py"),
    ("792", "py"),
    ("96", "py"),
    ("67", "mjs"),
    ("68", "mjs"),
    ("74", "mjs"),
    ("79", "mjs"),
    ("80", "mjs"),
    ("81", "mjs"),
    ("69", "mjs"),
    ("70", "mjs"),
    ("71", "mjs"),
    ("72", "mjs"),
    ("75", "mjs"),
    ("84", "mjs"),
    ("85", "mjs"),
    ("86", "mjs"),
    ("87", "mjs"),
    ("88", "mjs"),
    ("89", "mjs"),
    ("90", "mjs"),
    ("91", "mjs"),
    ("736", "py"),
    ("748", "py"),
    ("749", "py"),
    ("782", "py"),
    ("857", "py"),
    ("625", "py"),
    ("590", "py"),
    ("626", "py"),
    ("613", "py"),
    ("617", "py"),
    ("619", "py"),
    ("541", "py"),
    ("589", "py"),
    ("546", "py"),
    ("624", "py"),
    ("861", "py"),
    ("542", "py"),
    ("738", "py"),
    ("656", "py"),
    ("858", "py"),
    ("648", "py"),
    ("859", "py"),
    ("860", "py"),
]

# ★ 本批**动过其比对对象**的门禁（应当全绿 ⟹ ⟹ 红了就说明本批改坏了）
WATCH = [
    "856",
    "854",
    "853",
    "852",
    "851",
    "850",
    "849",
    "848",
    "847",
    "830",
    "543",
    "540",
    "550",
    "588",
    "45",
    "50",
    "96",
    "67",
    "68",
    "74",
    "79",
    "80",
    "81",
    "69",
    "70",
    "71",
    "72",
    "75",
    "84",
    "85",
    "86",
    "89",
    "90",
    "91",
    "857",
    "625",
    "590",
    "626",
    "613",
    "617",
    "619",
    "541",
    "589",
    "546",
    "624",
    "542",
    "536",
    "538",
    "738",
    "656",
    "858",
    "648",
    "859",
    "860",
]


def run(batch: str, ext: str) -> dict:
    script = ROOT / ("scripts/verify-liblib-batch%s.%s" % (batch, ext))
    if not script.exists():
        return {"batch": batch, "ext": ext, "rc": None, "verdict": "（无此门禁）"}
    cmd = ([str(NODE), str(script)] if ext == "mjs"
           else [sys.executable, str(script)])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=3600, cwd=str(ROOT))
    except subprocess.TimeoutExpired:
        return {"batch": batch, "ext": ext, "rc": "timeout", "verdict": "超时"}
    out = (r.stdout or "") + (r.stderr or "")
    verdict = None
    for ln in out.splitlines():
        if ln.strip().endswith("通过") and "/" in ln:
            verdict = ln.strip().split()[-1]
    if verdict is None:
        tail = [x.strip() for x in out.splitlines() if x.strip()][-3:]
        verdict = "rc=%s " % r.returncode + " ／ ".join(tail)[-160:]
    return {"batch": batch, "ext": ext, "rc": r.returncode, "verdict": verdict}


def main() -> int:
    results = []
    for batch, ext in GATES:
        res = run(batch, ext)
        results.append(res)
        print("%-6s %-4s rc=%-5s %s"
              % (res["batch"], res["ext"], res["rc"], res["verdict"]), flush=True)
    outp = pathlib.Path("/tmp/b861-regression.json")
    outp.write_text(json.dumps(results, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    red = ["%s.%s" % (r["batch"], r["ext"]) for r in results
           if r["rc"] not in (0, None)]
    watch_red = [b for b in red if b.split(".")[0] in WATCH]
    print("\n== 回归：%d 条，红 %d 条 %s ==" % (len(results), len(red), red))
    print("== 盯的 %d 条里红的：%s ==" % (len(WATCH), watch_red))
    return 1 if watch_red else 0


if __name__ == "__main__":
    sys.exit(main())
