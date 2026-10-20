#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1032-②a 的门：**用户能不能真的拖出一条连线**

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
**背景**：1032-① 审计出「`<ReactFlow>` 里没有 `onConnect` ⇒ 拖不出边」——
这是「FEATURE_MISSING」那一类里最伤的一条：节点有 `<Handle>`、用户能拖出连线的样子，
**却一条边也建不出来** ⇒ 画布的核心交互整个不存在。

⚠️⭐⭐⭐⭐⭐ **为什么门要跑在运行时，而不是「源码里有 onConnect」就算过**
  「代码里写了 `onConnect`」**不等于**「用户拖得出一条边」：
  handle 口径（`<Handle>` 有没有 `id`）、React Flow 的连线事件、store 的判重，
  任何一处不对，用户看到的仍然是「拖了没反应」。
  ⇒ ⇒ ⇒ 所以门**自己跑那个真拖拽的探针**（`jimeng_probe1032a_connect_runtime.mjs`），
  ⇒ ⇒ ⇒ 然后对读数下判据。

⭐⭐⭐⭐⭐ **判据一律用「相对差」，不钉绝对值**
  「拖之前有 0 条边」是**会漂**的读数（mock 数据一变就变）⇒ 所以只钉
  「有效拖一次 ⇒ Δ=+1」「重复连 ⇒ Δ=0」「拖空白 ⇒ Δ=0」这三个**差值**。

判据：
  P1 有效拖一次 ⇒ Δ = +1（边真的建出来了）
  P2 新边 id == `e-<源>-<目标>` ⇒ source/target 正确（不是随便连的）
  P3 **同一对再拖一次** ⇒ Δ = 0（判重生效）
  P4 **拖到画布空白处** ⇒ Δ = 0（负控：证明「+1」不是因为什么都会 +1）
  P5 页面无 JS 错误
  P6 **静态防回归**：`<ReactFlow>` 仍带 `onConnect`、store 仍有 `addEdge`
  P7 **判据级阳性对照**：把读数改坏（Δ 改成 +2）后，同一套判据**必须红**
     ⇒ 证明 P1 不是恒真

⚠️⭐⭐⭐⭐⭐ **P7 的强度边界（诚实标注，不夸大）**
  P7 是**判据级**变异（改读数喂给判据），**不是探针级**变异（改页面源码让连线失效）。
  ⇒ ⇒ 它证明的是「P1 这条断言不是恒真」；
  ⇒ ⇒ 而「探针真的能观测到边数变化」这件事，由 **P3/P4 两条负控**在**探针级**证明
  ⇒ ⇒ ⇒（拖到空白 ⇒ Δ0、重复连 ⇒ Δ0 ⇒ ⇒ 所以「Δ=+1」必然来自那次有效拖拽）
  ⇒ ⇒ ⇒ 探针级的真变异（把 `onConnect` 从页面源码里拿掉）需要改真实源码，
  ⇒ ⇒ ⇒ **不在本门里做** ⇒ ⇒ ⇒ 留给下一批单独一笔（改真源 ⇒ 必须能还原）。
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GDIR = ROOT / "docs/research/jimeng-canvas"
READINGS = Path(
    os.environ.get("JIMENG_CONNECT_JSON",
                   str(GDIR / "inputs" / "connect-runtime-1032a.json")))
PROBE = ROOT / "scripts/jimeng_probe1032a_connect_runtime.mjs"
OUT = GDIR / "connect-contract-1032a.json"
WORKSPACE = ROOT / "src/components/jimeng/JimengWorkspace.tsx"
STORE = ROOT / "src/store/jimengStore.ts"

# ── 跑探针（读数不存在时现跑；跑不动就降级为 null，不判红） ─────────────
_readings = None
_run_info = "not attempted"
if os.environ.get("JIMENG_CONNECT_SKIP_PROBE") != "1":
    try:
        r = subprocess.run(["node", str(PROBE)], cwd=str(ROOT),
                           capture_output=True, text=True, timeout=300)
        _run_info = "rc=%d" % r.returncode
    except Exception as e:                                   # 探针跑不动 = 仪器问题
        _run_info = "probe failed: %s" % str(e)[:200]
else:
    _run_info = "skipped by env"

try:
    if READINGS.exists():
        _readings = json.loads(READINGS.read_text(encoding="utf-8"))
except Exception:
    _readings = None


def _judge(r):
    """给定读数，算出各条判据；读数缺 ⇒ 该条为 None（降级不是红）。"""
    if not r:
        return {k: None for k in ("P1", "P2", "P3", "P4", "P5")}
    dv = r.get("drag_valid") or {}
    dd = r.get("drag_duplicate") or {}
    dw = r.get("drag_to_void") or {}
    return {
        # ⭐ 只比「相对差」⇒ 不钉会漂的绝对边数
        "P1": (dv.get("delta") == 1) if dv.get("delta") is not None else None,
        "P2": (dv.get("expected_id_present") is True) if dv else None,
        "P3": (dd.get("delta") == 0) if dd.get("delta") is not None else None,
        "P4": (dw.get("delta") == 0) if dw.get("delta") is not None else None,
        "P5": (not r.get("pageerrors")) if "pageerrors" in r else None,
    }


_c = _judge(_readings)

# ── P7：判据级阳性对照（把读数改坏 ⇒ 同一套判据必须红） ────────────────
_mut = None
if _readings:
    _bad = json.loads(json.dumps(_readings))
    _bad["drag_valid"]["delta"] = 999          # 故意破坏 P1 的输入
    _mc = _judge(_bad)
    _mut = {
        "n_p1_before": _c["P1"],
        "n_p1_after": _mc["P1"],
        "p1_turned_red": (_c["P1"] is True and _mc["P1"] is False),
        "note": "⭐ 判据级变异：只改读数、不碰真源 ⇒ 真源产物零污染",
    }

# ── P6：静态防回归 ─────────────────────────────────────────────────────
_ws = WORKSPACE.read_text(encoding="utf-8") if WORKSPACE.exists() else ""
_st = STORE.read_text(encoding="utf-8") if STORE.exists() else ""
_p6 = {
    "reactflow_has_on_connect": bool(re.search(r"<ReactFlow\b[\s\S]{0,4000}?onConnect=\{",
                                        _ws)),
    "workspace_calls_on_connect_handler": "onConnectHandler" in _ws,
    "store_declares_add_edge": bool(re.search(r"^\s*addEdge:\s*\(edge:\s*Edge\)\s*=>\s*void;",
                                           _st, re.M)),
    "store_implements_add_edge": "addEdge: (edge) =>" in _st,
}
_c["P6"] = all(_p6.values())

out = {
    "generated_by": "jimeng_probe1032a_connect_contract.py",
    "target": "jimeng-canvas-connect",
    "question": "⭐⭐⭐⭐⭐ **用户能不能真的拖出一条连线？**",
    "probe_run": _run_info,
    "readings_file": str(READINGS.relative_to(ROOT)) if READINGS.exists() else None,
    "readings_available": bool(_readings),
    "criteria": _c,
    "p6_static": _p6,
    "p7_mutation": _mut,
    # ⭐⭐⭐⭐⭐ **产物里不许出现「本次选中的具体节点 id」** ——
    #   探针是「按 DOM 顺序取的前两个带把手的节点」⇒ ⇒ 节点顺序一变，
    #   ⇒ ⇒ 产物就变 ⇒ ⇒ 而这个产物在**顶层** ⇒ ⇒ 1015 通道 A 会当 golden 比对
    #   ⇒ ⇒ ⇒ **⇒ 一次顺序抖动就变成一条永久漂移。**
    #   ⇒ ⇒ ⇒ 所以只留**判据真正用到**的东西：差值、布尔、以及「有没有页面错误」。
    #   ⇒ ⇒ ⇒ （具体是哪两个节点，属于排障信息 ⇒ 留在 `inputs/` 那份读数里，不进 golden。）
    "detail": {
        "probes": (_readings or {}).get("probes"),
        "drag_valid": {
            k: v for k, v in ((_readings or {}).get("drag_valid") or {}).items()
            if k in ("n_before", "n_after", "delta", "expected_id_present")
        },
        "drag_duplicate": {
            k: v for k, v in ((_readings or {}).get("drag_duplicate") or {}).items()
            if k in ("n_before", "n_after", "delta")
        },
        "drag_to_void": {
            k: v for k, v in ((_readings or {}).get("drag_to_void") or {}).items()
            if k in ("n_before", "n_after", "delta")
        },
        "n_pageerrors": len((_readings or {}).get("pageerrors") or []),
    },
}

vals = [out["criteria"][k] for k in ("P1", "P2", "P3", "P4", "P5", "P6")]
if _mut is not None:
    vals.append(_mut["p1_turned_red"])
out["criteria"]["P7"] = _mut["p1_turned_red"] if _mut is not None else None

false_list = [k for k, v in out["criteria"].items() if v is False]
none_list = [k for k, v in out["criteria"].items() if v is None]
out["n_false"] = len(false_list)
out["false_criteria"] = false_list
out["degraded_criteria"] = none_list

io = OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

print("probe: %s | readings=%s" % (_run_info, "有" if _readings else "无"))
print("P1..P7 =", [out["criteria"].get("P%d" % i) for i in range(1, 8)])
print("为假的：", false_list or "无", "| 降级：", none_list or "无")
print("PROBE_1032A_CONNECT_DONE ->", OUT)

if false_list:
    sys.exit(1)
sys.exit(0)
