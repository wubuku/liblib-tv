#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 850 回归：跑一批历史门禁，汇总每一条的 verdict。

★ 门禁**一个一个**跑（★ 4317 多人共用 ⟹ ⟹ **不并发**跑多个浏览器脚本）。
★ 回归**副产物**（各批的 runtime-audit.json 等）**不**带进本批提交
  ⟹ ⟹ 跑完用 `git checkout --` 复原（★ 不动本批自己的产物）。

## ★★ 本批要特别盯 batch 840

★ batch 840 的门禁有一份 `CRITICAL_SELECTORS` ⟹ ⟹ 里面**有** `.ce-tool`／`.ce-figure`／
`.ce-preview-tools` ⟹ ⟹ 而这三条**本批全都动过**
（★ `.ce-tool` 的 base 复原但取景按钮的修饰类变了；★ `.ce-figure` 多了一层包裹；
★ `.ce-preview-tools` 从「left/top 绝对定位」改成「left:50%/bottom:16px 居中」）。
⟹ ⟹ ★ 所以 840 在本批回归里**必须绿**
⟹ ⟹ 若红 ⟹ ⟹ 说明本批的改动**破坏**了 batch 840 已经对照过的几何
⟹ ⟹ ⟹ ⟹ 那就要**迁移**（第十次）⟹ ⟹ 而不是放着不管。
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")

# ★ 本批自己 + 历史批次
BATCHES = [
    "850",  # 本批
    "849", "848", "847", "846", "845", "844", "843", "842", "841", "840", "839",
    "783", "827", "826", "838", "835",
    "62", "111", "112", "113", "146b", "169",
    "556", "557", "536", "540", "575",
    "46", "36", "720", "42", "43",
    # ★ 旧账（受控对照在 attrib850.py 里另做）
    "736", "748", "749", "782",
]

# ★ 本批**动过它们比对的选择器**的门禁（应当全绿 ⟹ ⟹ 红了就说明本批改坏了）
# ★ ★ batch 840 的 `CRITICAL_SELECTORS` 里有 `.ce-tool`／`.ce-figure`／`.ce-preview-tools`
WATCH = ["840"]


def run(batch: str) -> dict:
    script = ROOT / ("scripts/verify-liblib-batch%s.py" % batch)
    if not script.exists():
        return {"batch": batch, "rc": None, "verdict": "（无此门禁）"}
    r = subprocess.run([sys.executable, str(script)], capture_output=True,
                       text=True, timeout=3600, cwd=str(ROOT))
    out = (r.stdout or "") + (r.stderr or "")
    verdict = None
    for ln in out.splitlines():
        if ln.strip().endswith("通过") and "/" in ln:
            verdict = ln.strip().split()[-1]
    if verdict is None:
        tail = [x.strip() for x in out.splitlines() if x.strip()][-3:]
        verdict = "rc=%d " % r.returncode + " ／ ".join(tail)[-160:]
    return {"batch": batch, "rc": r.returncode, "verdict": verdict}


def main() -> int:
    results = []
    for b in BATCHES:
        res = run(b)
        results.append(res)
        print("%-6s %s" % (res["batch"], res["verdict"]), flush=True)
    outp = pathlib.Path("/tmp/b850-regression.json")
    outp.write_text(json.dumps(results, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    print("\n写入", outp)

    watch = [r for r in results if r["batch"] in WATCH]
    bad = [r for r in watch if r["rc"] not in (0,)]
    print("\n=== 本批动过其比对选择器的门禁 ===")
    for r in watch:
        print("  %-6s %s" % (r["batch"], r["verdict"]))
    print("  %s" % ("全部绿 ✓" if not bad else
                    "★★ 有红的 ⟹ 本批改坏了旧门禁比对的几何何 ⟹ ⟹ 需要迁移"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
