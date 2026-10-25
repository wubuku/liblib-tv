#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 1032-⑬：**浮层可达性门**（浮层必须落在视口内、控件必须点得到）。

## 这道门答的是哪一个问题
  「画布上弹出来的浮层，**用户是不是够得着**」。

## 它在 1032-⑬ 里查出的根因
  「**全音色**」面板是 `absolute bottom-[calc(100%+8px)]` ⇒ **永远向上开**；
  而节点工具条在节点**上方** ⇒ 节点靠近视口顶边时，面板顶边跑到 **y=-318**，
  4 枚筛选芯片落在 **y=-278** ⇒ `elementFromPoint` 落空 ⇒ **鼠标点不到**
  ⇒ ⇒ 「音色筛选」这条功能在那一处**整个不可用**。
  ⚠️ 而它**不报错、不变红**：面板照样渲染、DOM 照样有节点
  ⇒ ⇒ ⇒ 只有「它在不在屏内、点不点得到」能判出来。

## 与 1039 同款的纪律
  · 产物里**不许出现随机量**（时间戳 / 耗时 / pid）⇒ 运行时探针只落布尔与计数；
  · **三态退出码**：0=全绿 / 1=判据红 / 2=仪器崩（探针没跑成或读数不新鲜）。
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jimeng_node_toolchain import readings_fresh, run_node_probe  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
GDIR = ROOT / "docs/research/jimeng-canvas"
READINGS = Path(os.environ.get(
    "JIMENG_REACH_JSON", str(GDIR / "inputs" / "floating-reachability-1040.json")))
PROBE = ROOT / "scripts/jimeng_probe1040_floating_reachability_runtime.mjs"
OUT = GDIR / "floating-reachability-1040.json"

CRIT_KEYS = ("P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8")

_readings = None
_run_info = "not attempted"
_crashed = False
_t0 = 0.0
if os.environ.get("JIMENG_REACH_SKIP_PROBE") != "1":
    _t0 = time.time()
    _res = run_node_probe(PROBE, cwd=str(ROOT), timeout=300, nonzero_is_crash=True)
    _run_info = _res["run_info"]
    _crashed = _res["crashed"]
else:
    _run_info = "skipped by env"
    _crashed = True

try:
    if READINGS.exists():
        _readings = json.loads(READINGS.read_text(encoding="utf-8"))
except Exception:  # noqa: BLE001
    _readings = None
_readings_fresh = (readings_fresh(READINGS, _t0) if not _crashed else False)
if _crashed or not _readings_fresh:
    _readings = None
    _crashed = True

N_CHIPS = 4


def _judge(r):
    if not r:
        return {k: None for k in CRIT_KEYS}
    po = r.get("panel_open") or {}
    ac = r.get("after_chip_click") or {}
    chips_open = po.get("chips") or []
    chips_after = ac.get("chips") or []
    return {
        # ① 面板开得出来
        "P1": po.get("panel_present") is True,
        # ② 4 枚筛选芯片都在
        "P2": (len(chips_open) == N_CHIPS
               and all(c.get("present") is True for c in chips_open)),
        # ③ 4 枚芯片**都在视口内**（看得见）
        "P3": (len(chips_open) == N_CHIPS
               and all(c.get("in_viewport") is True for c in chips_open)),
        # ④ 4 枚芯片**都点得到**（elementFromPoint 落在它自己身上）
        "P4": (len(chips_open) == N_CHIPS
               and all(c.get("hittable") is True for c in chips_open)),
        # ⑤ 面板刚开时没有筛选下拉常驻（批 870 的语义）
        "P5": po.get("n_dropdowns_open") == 0,
        # ⑥ 点一枚芯片 ⇒ 恰好开出 1 枚下拉，且那 4 枚芯片仍都可达
        "P6": (ac.get("n_dropdowns_open") == 1
               and len(chips_after) == N_CHIPS
               and all(c.get("hittable") is True for c in chips_after)),
        # ⑦ 页面无脚本错误
        "P7": not r.get("pageerrors"),
        # ⑧ 判据级阳性对照（下面算）
        "P8": None,
    }


_c = _judge(_readings)

# ── P8：判据级阳性对照（把读数改坏 ⇒ 同一套判据必须红） ──────────────
_mut = None
if _readings:
    _c0 = _judge(_readings)
    _bad = json.loads(json.dumps(_readings))
    _bad["panel_open"]["chips"][0]["hittable"] = False
    _bad["panel_open"]["chips"][0]["in_viewport"] = False
    _mc = _judge(_bad)
    _mut = {
        "n_p3_before": _c0["P3"],
        "n_p3_after": _mc["P3"],
        "n_p4_before": _c0["P4"],
        "n_p4_after": _mc["P4"],
        "p3_turned_red": (_c0["P3"] is True and _mc["P3"] is False),
        "p4_turned_red": (_c0["P4"] is True and _mc["P4"] is False),
        "note": "⭐ 判据级变异：只改读数、不碰真源 ⇒ 真源产物零污染",
    }
_c["P8"] = (_mut["p3_turned_red"] and _mut["p4_turned_red"]) if _mut else None

out = {
    "generated_by": "jimeng_probe1040_floating_reachability.py",
    "target": "jimeng-canvas-floating-reachability",
    "question": "⭐⭐⭐⭐⭐ **画布弹出来的浮层，用户够得着吗？**",
    "probe_run": _run_info,
    "probe_crashed": bool(_crashed),
    "readings_available": bool(_readings),
    "readings_fresh": bool(_readings_fresh),
    "readings_file": str(READINGS.relative_to(ROOT)) if READINGS.exists() else None,
    "criteria": {k: _c.get(k) for k in CRIT_KEYS},
    "p8_mutation": _mut,
    "detail": {
        "viewport": [
            ((_readings or {}).get("panel_open") or {}).get("vw"),
            ((_readings or {}).get("panel_open") or {}).get("vh"),
        ],
        "panel_present": ((_readings or {}).get("panel_open") or {}).get("panel_present"),
        "panel_in_viewport": ((_readings or {}).get("panel_open") or {}).get("panel_in_viewport"),
        "panel_hits_itself": ((_readings or {}).get("panel_open") or {}).get("panel_hits_itself"),
        "n_chips": len((( _readings or {}).get("panel_open") or {}).get("chips") or []),
        "chips_present": sum(
            1 for c in (((_readings or {}).get("panel_open") or {}).get("chips") or [])
            if c.get("present") is True),
        "chips_in_viewport": sum(
            1 for c in (((_readings or {}).get("panel_open") or {}).get("chips") or [])
            if c.get("in_viewport") is True),
        "chips_hittable": sum(
            1 for c in (((_readings or {}).get("panel_open") or {}).get("chips") or [])
            if c.get("hittable") is True),
        "n_dropdowns_after_chip_click": ((_readings or {}).get("after_chip_click") or {}).get(
            "n_dropdowns_open"),
        "n_pageerrors": len((_readings or {}).get("pageerrors") or []),
    },
    "why_this_gate_exists": (
        "⭐⭐⭐⭐⭐ 1032-⑬ 的根因：**面板开到视口外**（顶边 y=-318、芯片 y=-278）"
        "⇒ 鼠标点不到 ⇒ 功能不可用。⚠️ 而它**不报错、不变红**（面板照样渲染、"
        "DOM 照样有节点）⇒ ⇒ ⇒ 只有「在不在屏内 / 点不点得到」能判出来。"
    ),
}

false_list = [k for k, v in out["criteria"].items() if v is False]
none_list = [k for k, v in out["criteria"].items() if v is None]
out["n_false"] = len(false_list)
out["false_criteria"] = false_list
out["degraded_criteria"] = none_list
out["criterion_kinds_1040"] = {k: "failure" for k in CRIT_KEYS}
out["criterion_kinds_complete_1040"] = (
    set(out["criterion_kinds_1040"]) == set(out["criteria"]))
out["criteria_n_1040"] = len(out["criteria"])

OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

print("probe: %s | readings=%s" % (_run_info, "有" if _readings else "无"))
print("P1..P8 =", [out["criteria"].get(k) for k in CRIT_KEYS])
print("为假的：", false_list or "无", "| 降级：", none_list or "无")
print("PROBE_1040_FLOATING_REACHABILITY_DONE ->", OUT)

if _crashed or not _readings:
    sys.exit(2)
sys.exit(1 if false_list else 0)
