#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 864 阴性对照（负控）：**注入缺陷 ⟹ 门禁必须红 ⟹ 字节级还原**。

## ★ 纪律

① 每条变异都**独立**地从原文件开始（不做链式叠加 ⟹ ⟹ 互不污染）；
② 变异必须**行数中性**（只改同一行内的字符串 ⟹ ⟹ 不改变文件行数）；
③ 跑完必须**字节级还原**（sha256 比对）；
④ ★ **锚点必须落在代码行** —— ★ 本批的注释里**逐字抄了**源站的字符串
   （`libtv.canvas.director.camera.update`／`right_panel`／`aspect_ratio`…）
   ⟹ ⟹ 按裸字面量替换会**先命中注释** ⟹ ⟹ 代码没变 ⟹ ⟹ 负控打空（batch 862 教训）；
⑤ ★ 每条变异都要有**「变异已落地」自检**（batch 863 教训：算出变异却没写回文件）。

## ★ 变异清单（每条都对应门禁里的一条判据）

| # | 变异 | 应命中的判据 |
|---|---|---|
| N1 | 事件名改一个字符 | source:the-event-name-is-verbatim |
| N2 | `operation_source` 从 `right_panel` 改成别的 | source:the-operation-source-is-verbatim |
| N3 | 在埋点实现里塞一个 `fetch(` | source:the-local-telemetry-never-touches-the-network（★ 底线门禁） |
| N4 | 参考线的取值反转（`showThirds ? 0 : 1` → `? 1 : 0`） | clone:toggling-the-reference-line-records-a-numeric-value |
| N5 | 「自适应」也记成字符串（不再记 `null`） | clone:picking-auto-records-a-null-value |
| N6 | 在 store 的机位对象里造一个 `aspect_ratio` 字段（D17 的**假字段**） | source:the-aspect-ratio-is-not-written-onto-a-camera-object |
| N7 | `camera_uuid` 写死成常量 | clone:the-recorded-camera-is-the-selected-one |

## 用法
  python3 neg864.py --observe     # 只打印每条变异后的首条红灯（用来定归因关键字）
  python3 neg864.py              # 正式模式：断言「红」且「红在预期判据上」
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
GATE = ROOT / "scripts/verify-liblib-batch864.py"

TELEMETRY = ROOT / "src/lib/directorTelemetry.ts"
STORE = ROOT / "src/store/directorStore.ts"
PANEL = ROOT / "src/components/director/DirectorAspectPanel.tsx"
VIEW = ROOT / "src/components/director/DirectorViewport.tsx"

FILES = {
    "telemetry": TELEMETRY,
    "store": STORE,
    "panel": PANEL,
    "view": VIEW,
}

MUTATIONS = [
    {
        "id": "N1",
        "desc": "事件名改一个字符",
        "file": "telemetry",
        "old": '  "libtv.canvas.director.camera.update";',
        "new": '  "libtv.canvas.director.camera.updatX";',
        "expect": "source:the-event-name-is-verbatim",
    },
    {
        "id": "N2",
        "desc": "operation_source 改成别的",
        "file": "telemetry",
        "old": 'export const DIRECTOR_TELEMETRY_OPERATION_SOURCE = "right_panel" as const;',
        "new": 'export const DIRECTOR_TELEMETRY_OPERATION_SOURCE = "viewport" as const;',
        "expect": "source:the-operation-source-is-verbatim",
    },
    {
        "id": "N3",
        "desc": "埋点实现里塞一个网络调用（底线门禁）",
        "file": "telemetry",
        "old": "      camera_uuid: input.cameraId,",
        "new": '      camera_uuid: (fetch("/telemetry", { method: "POST" }), input.cameraId),',
        "expect": "source:the-local-telemetry-never-touches-the-network",
    },
    {
        "id": "N4",
        "desc": "参考线取值反转",
        "file": "view",
        "old": "settingValue: showThirds ? 0 : 1,",
        "new": "settingValue: showThirds ? 1 : 0,",
        "expect": "clone:toggling-the-reference-line-records-a-numeric-value",
    },
    {
        "id": "N5",
        "desc": "「自适应」不再记 null",
        "file": "panel",
        "old": 'settingValue: ratio === "自适应" ? null : ratio,',
        "new": "settingValue: ratio,",
        "expect": "clone:picking-auto-records-a-null-value",
    },
    {
        "id": "N6",
        "desc": "在机位对象上造出 D17 那个假字段",
        "file": "store",
        "old": '    primitive: "camera",',
        "new": '    primitive: "camera", aspect_ratio: null,',
        "expect": "source:the-aspect-ratio-is-not-written-onto-a-camera-object",
    },
    {
        "id": "N7",
        "desc": "camera_uuid 写死成常量",
        "file": "panel",
        # ★ ★ 写死的值必须**与真值不同** ⟹ ⟹ 否则这条变异**探测不到任何东西**
        #   （clone 的 `activeCameraId` 恰好就是 `director-camera-main`
        #   ⟹ ⟹ 第一版写死成它 ⟹ ⟹ 门禁照样绿 ⟹ ⟹ 负控打空）
        "old": '        cameraId,\n        settingName: "aspect_ratio",',
        "new": '        cameraId: "director-camera-X",\n        settingName: "aspect_ratio",',
        "expect": "clone:the-recorded-camera-is-the-selected-one",
    },
]


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def apply_mutation(src: str, m: dict) -> tuple[bool, str, str]:
    """★ 返回 (成功, 原因, **变异后的源码**)。

    ★ ★ batch 863 的教训：算出变异却**没写回文件** ⟹ ⟹ 7 条变异一条都没落地
    ⟹ ⟹ 门禁全绿 ⟹ ⟹ 负控 0/7 打空 ⟹ ⟹ 这里必须**返回变异后的源码**。
    """
    if m["old"] not in src:
        return False, f"锚点不存在：{m['old']!r}", src
    if m["old"] == m["new"]:
        return False, "锚点与替换值相同", src
    mutated = src.replace(m["old"], m["new"], 1)
    if mutated == src:
        return False, "替换后内容没变", src
    return True, "", mutated


def run_gate() -> tuple[int, list[str]]:
    proc = subprocess.run([sys.executable, str(GATE)], cwd=ROOT,
                          capture_output=True, text=True, timeout=1800)
    fails = [ln.strip() for ln in proc.stdout.splitlines()
             if ln.strip().startswith("FAILED:")]
    if not fails:
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

    original = {k: FILES[k].read_bytes() for k in FILES}
    report: list[dict] = []
    try:
        for m in MUTATIONS:
            path = FILES[m["file"]]
            path.write_bytes(original[m["file"]])
            src = original[m["file"]].decode("utf-8")
            ok, why, mutated = apply_mutation(src, m)
            if not ok:
                report.append({"id": m["id"], "desc": m["desc"], "结果": "无法注入",
                               "原因": why})
                print(f"[{m['id']}] 无法注入：{why}")
                continue
            lines_before = src.count("\n")
            path.write_text(mutated, encoding="utf-8")
            lines_after = path.read_text(encoding="utf-8").count("\n")
            injected = m["new"].split("\n")[0] in path.read_text(encoding="utf-8")
            # ★ 等 dev server 重编（运行时判据要看到新源码）
            time.sleep(10)
            rc, fails = run_gate()
            path.write_bytes(original[m["file"]])
            restored = sha_bytes(path.read_bytes()) == sha_bytes(original[m["file"]])
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
        for k, data in original.items():
            FILES[k].write_bytes(data)
        print("★ 最终还原自检：",
              all(sha_bytes(FILES[k].read_bytes()) == sha_bytes(original[k])
                  for k in FILES))

    out = ROOT / ("docs/research/liblib-canvas-batch864-2026-10-01/raw/"
                  "negative-audit.json")
    out.parent.mkdir(parents=True, exist_ok=True)
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
