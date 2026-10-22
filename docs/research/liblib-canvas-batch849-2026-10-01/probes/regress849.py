#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 849 回归：跑一批历史门禁，汇总每一条的 verdict。

★ 门禁**一个一个**跑（★ 4317 多人共用 ⟹ ⟹ **不并发**跑多个浏览器脚本）。
★ 回归**副产物**（各批的 runtime-audit.json 等）**不**带进本批提交
  ⟹ ⟹ 跑完用 `git checkout --` 复原（★ 不动本批自己的产物）。

★★ 本批有一处**特别**要注意：batch 849 把第四段的「服装」「AI 生成」两页
**实测并实现**了 ⟹ ⟹ 842／843 的「那一页未实测」断言**翻了期望**
（见 `probes/migrate849.py`）⟹ ⟹ 所以 842／843 在回归里**必须绿**
⟹ ⟹ 若红 ⟹ ⟹ 说明**迁移**把东西改坏了。
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")

# ★ 本批自己 + 历史批次
BATCHES = [
    "849",  # 本批
    "848", "847", "846", "845", "844", "843", "842", "841", "840", "839",
    "783", "827", "826", "838", "835",
    "62", "111", "112", "113", "146b", "169",
    "556", "557", "536", "540", "575",
    "46", "36", "720", "42", "43",
    # ★ 旧账（受控对照在 attrib849.py 里另做）
    "736", "748", "749", "782",
]

# ★ 本批**换靶**过的三个门禁（应当全绿 ⟹ ⟹ 红了就说明迁移改坏了东西）
# ★ ★ batch 849 的**第九次迁移**翻了**三条**门禁（846／842／843）
MIGRATED = ["846", "843", "842"]


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
    outp = pathlib.Path("/tmp/b849-regression.json")
    outp.write_text(json.dumps(results, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    print("\n写入", outp)

    # ★★ 换靶过的门禁**必须全绿**（★ 否则说明「迁移」改坏了东西）
    mig = [r for r in results if r["batch"] in MIGRATED]
    bad = [r for r in mig if r["rc"] not in (0,)]
    print("\n=== 本批换靶过的两个门禁 ===")
    for r in mig:
        print("  %-6s %s" % (r["batch"], r["verdict"]))
    print("  %s" % ("全部绿 ✓" if not bad else "★★ 有红的 ⟹ 迁移可能改坏了东西"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
