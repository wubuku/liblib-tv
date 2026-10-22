#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 843 回归：跑一批历史门禁，汇总每一条的 verdict。

★ 门禁**一个一个**跑（★ 4317 多人共用 ⟹ ⟹ **不并发**跑多个浏览器脚本）。
★ 回归**副产物**（各批的 runtime-audit.json 等）**不**带进本批提交
  ⟹ ⟹ 跑完用 `git checkout --` 复原（★ 不动本批自己的产物）。
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")

# ★ 本批自己 + 历史批次
BATCHES = [
    "843",  # 本批
    "842", "841", "840", "839",
    "783", "827", "826", "838", "835",
    "62", "111", "112", "113", "146b", "169",
    "556", "557", "536", "540", "575",
    "46", "36", "720", "42", "43",
    # ★ 旧账（受控对照在 attrib843.py 里另做）
    "736", "748", "749", "782",
]


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
    outp = pathlib.Path("/tmp/b843-regression.json")
    outp.write_text(json.dumps(results, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    print("\n写入", outp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
