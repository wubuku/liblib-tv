#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 853 回归：跑既有门禁清单 ⟹ ⟹ 看本批有没有把别的批次弄坏。

## ★ 本批动过的**被跟踪**源码

- `src/components/director/DirectorDesk.tsx`
  （新增 g／d 快捷键分支 ＋ 两个 action 的绑定 ＋ 依赖数组补项）
- `src/components/director/directorShortcutRules.ts`（**新增文件**）

★ ★ 本批**没有删改**任何既有导出／既有分支 ⟹ ⟹ 凡是读 `DirectorDesk.tsx`
  的门禁都必须在回归清单里。

## ★ 清单里**特意加上**组相关的十四条

★ 本批接线的正是**打组／解组**这条通路 ⟹ ⟹ 所有**读组状态**
（`selectedGroupId`／`data-director-group-action`）的门禁都要进清单 ⟹ ⟹
否则「快捷键接对了」与「组本身被改坏了」分不开。

## ★ 已知旧账（在 HEAD 上也是红的 ⟹ ⟹ 不是本批引入）

★ `736`／`748`／`749`／`782`／`831`／`741` ⟹ ⟹ 受控对照在 `attrib853.py` 里另做
（把源码换回 HEAD 再跑一遍 ⟹ 读数必须逐条相同）。

## 输出

  /tmp/b853-regression.json
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")

BATCHES = [
    "853",  # 本批
    "852", "851", "850", "849", "848", "847", "846", "845", "844", "843", "842",
    "841", "840", "839",
    "830", "831", "543",
    "783", "827", "826", "838", "835",
    "62", "111", "112", "113", "146b", "169",
    "556", "557", "536", "540", "575",
    "46", "36", "720", "42", "43",
    # ★ 吸附相关（上一批改过吸附步长 ⟹ ⟹ 顺带盯着）
    "550", "588", "741", "797", "798",
    # ★ ★ 组相关（本批接线的正是这条通路 ⟹ ⟹ 必须在清单里）
    "45", "47", "48", "49", "50", "59", "72", "75", "85", "86", "87", "88",
    "91", "792",
    # ★ 旧账（HEAD 上也红）
    "736", "748", "749", "782",
]

# ★ 本批**动过其比对对象**的门禁（应当全绿 ⟹ ⟹ 红了就说明本批改坏了）
WATCH = ["853", "852", "851", "850", "830", "543", "840", "550", "588",
         "835", "45", "50", "85", "87", "88", "792"]


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
    outp = pathlib.Path("/tmp/b853-regression.json")
    outp.write_text(json.dumps(results, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    red = [r["batch"] for r in results if r["rc"] not in (0, None)]
    watch_red = [b for b in red if b in WATCH]
    print("\n== 回归：%d 条，红 %d 条 %s ==" % (len(results), len(red), red))
    print("== 盯的 %d 条里红的：%s ==" % (len(WATCH), watch_red))
    return 1 if watch_red else 0


if __name__ == "__main__":
    sys.exit(main())
