#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 1032-⑫：**媒体播放契约门**（复刻侧当前行为）。

## 这道门答的是哪一个问题
  「用户手册 10-tasks/media-playback.md 描述的那套操作，在**当前这版复刻**上
  到底成不成立 —— 有没有**假播放**、**假交互**、**假源站标注**。」

## 它在 1032 审计里查出的三处「糊弄」
  ① **全屏预览层只有一张海报 `<img>`** ⇒ 全屏里画面永远静止，而时间码在走
     ⇒ **假播放**（卡面在 1032-④-B C11 换成了真 `<video>`，全屏层漏了）；
  ② **音量滑杆是静态 `<span role="slider">`** ⇒ `aria-valuenow` 写死 60、
     **零事件处理器** ⇒ 拖了没反应 ⇒ **假交互**
     （且 1034 的假交互扫描器**结构上**看不见它：R1 只扫带事件属性的元素）；
  ③ **中央播放钮的 `32px` 被注释成 SOURCE_FACT** ⇒ 源站实测是 **44×44**
     ⇒ 那是**假源站标注**（注释说的出处与手册记的源站读数对不上）。

## 口径纪律
  · 手册正文记的是**源站**读数；本门量的是**复刻**当前行为 ⇒
    两者不一致**不是缺陷**，但必须**逐条写进手册的「复刻口径」一节**（P15 把关）。
  · 产物里**不许出现随机量**（时间戳 / currentTime / pid / 耗时）
    ⇒ 凡是会随时间漂的读数，运行时探针已经折成布尔/计数。
  · **三态退出码**：0=全绿 / 1=判据红 / 2=仪器崩（探针没跑成或读数不新鲜）。
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jimeng_node_toolchain import readings_fresh, run_node_probe  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
GDIR = ROOT / "docs/research/jimeng-canvas"
READINGS = Path(os.environ.get(
    "JIMENG_MEDIA_JSON", str(GDIR / "inputs" / "media-playback-runtime-1039.json")))
PROBE = ROOT / "scripts/jimeng_probe1039_media_playback_runtime.mjs"
OUT = GDIR / "media-playback-contract-1039.json"

CARD = ROOT / "src/components/jimeng/nodes/JimengVideoMediaCard.tsx"
PREVIEW = ROOT / "src/components/jimeng/JimengVideoPreview.tsx"
STORE = ROOT / "src/store/jimengStore.ts"
MANUAL = ROOT / "docs/user-manual/jimeng-canvas/10-tasks/media-playback.md"

CRIT_KEYS = ("P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10",
             "P11", "P12", "P13", "P14", "P15")

# ── 跑探针（读数不存在时现跑；跑不动 ⇒ 降级，不判红） ──────────────────
_readings = None
_run_info = "not attempted"
_crashed = False
_t0 = 0.0
if os.environ.get("JIMENG_MEDIA_SKIP_PROBE") != "1":
    _t0 = time.time()
    _res = run_node_probe(PROBE, cwd=str(ROOT), timeout=300, nonzero_is_crash=True)
    _run_info = _res["run_info"]
    _crashed = _res["crashed"]
else:
    _run_info = "skipped by env"
    # ⭐⭐⭐ 跳过 ⇒ 本轮探针没跑 ⇒ 同样不许拿旧读数冒充
    _crashed = True

try:
    if READINGS.exists():
        _readings = json.loads(READINGS.read_text(encoding="utf-8"))
except Exception:  # noqa: BLE001
    _readings = None
# ⭐⭐⭐ 读数必须新鲜 ⇒「文件在」≠「是本轮的」
_readings_fresh = (readings_fresh(READINGS, _t0) if not _crashed else False)
if _crashed or not _readings_fresh:
    _readings = None
    _crashed = True


def _judge(r):
    """给定读数算出各条判据；读数缺 ⇒ 该条为 None（降级不是红）。"""
    if not r:
        return {k: None for k in CRIT_KEYS}
    states = r.get("states") or []
    un = next((s for s in states if s.get("label") == "unselected"), {})
    pl = next((s for s in states if s.get("label") == "playing"), {})
    de = next((s for s in states if s.get("label") == "deselected"), {})
    pv = r.get("preview") or {}
    vd = r.get("volume_drag") or {}
    vk = r.get("volume_keyboard") or {}
    cm = r.get("ctx_menu") or {}
    items = cm.get("items") or []
    dl = next((i for i in items if "下载" in str(i.get("text", ""))), None)
    cpx = r.get("central_button_canvas_px")
    c_ok = (isinstance(cpx, list) and len(cpx) == 2
            and all(abs(float(x) - 44.0) <= 0.6 for x in cpx))
    return {
        # ① 中央播放钮 44×44（画布像素）—— 源站事实口径
        "P1": c_ok,
        # ② 播放中时间码真的在走
        "P2": (r.get("playing_advances") or {}).get("moved") is True,
        # ③ 取消选中 ⇒ 停播（currentTime 冻住）
        "P3": (r.get("deselect_freezes") or {}).get("frozen") is True,
        # ④ 取消选中 ⇒ `<video>` 仍留在 DOM（与手册源站口径逐字对上）
        "P4": r.get("video_still_in_dom_after_deselect") is True,
        # ⑤ 全屏预览里是**真 <video>** 且在播（此前只有海报 ⇒ 假播放）
        "P5": (pv.get("has_video_element") is True
               and pv.get("video_paused") is False),
        # ⑥ 音量滑杆真能拖（aria 变 + 变小 + 落点贴近目标）
        "P6": (vd.get("aria_changed") is True and vd.get("decreased") is True
               and vd.get("landed_near_target") is True),
        # ⑦ 音量真的落到 `<video>.volume` 上（不是只改 aria）
        "P7": (vd.get("video_volume_follows") is True
               and vd.get("video_volume_changed") is True),
        # ⑧ 口径 0–1（源站口径）＋ 键盘可调
        "P8": (pv.get("slider_aria_min") == "0" and pv.get("slider_aria_max") == "1"
               and vk.get("aria_changed") is True and vk.get("increased") is True),
        # ⑨ 带媒体的视频节点右键菜单 8 项，「下载」可用
        "P9": (len(items) == 8 and dl is not None and dl.get("disabled") is False),
        # ⑩ 页面无脚本错误
        "P10": not r.get("pageerrors"),
        # ⑪ 全仓没有「带交互 ARIA role 却零处理器」的元素
        "P11": len(r.get("aria_dead_census") or []) == 0,
        # ⑫ 普查器自身：阳性对照（能抓到死的）＋ 阴性对照（不误报活的）
        "P12": ((r.get("aria_dead_census_selftest") or {}).get("detects_dead_widget") is True
                and (r.get("aria_dead_census_selftest") or {}).get(
                    "ignores_delegated_widget") is True),
        # ⑬ 静态防回归（源码形状）
        "P13": None,   # 下面算（静态）
        # ⑭ 判据级阳性对照（注入式反证）—— 下面算
        "P14": None,
        # ⑮ 手册对账：复刻口径那一节必须写出来
        "P15": None,   # 下面算（静态）
        # 供 detail 用（不改判据）
        "_states": {"unselected": un, "playing": pl, "deselected": de},
    }


# ── P13：静态防回归 ───────────────────────────────────────────────────
def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:  # noqa: BLE001
        return ""


_card = _read(CARD)
_prev = _read(PREVIEW)
_store = _read(STORE)
# ⭐⭐⭐ 「32px 残留」只抓**声明式**残留，不抓解释性叙述 ——
#   整改后的注释里**必然**要提到「此前是 32px」⇒ ⇒ 抓「任何 32px」会恒红。
#   ⇒ ⇒ 只抓「把 32px 说成中央播放钮/半透明圆钮的规格」那种**断言**。
_STALE_32PX = [
    r"中央[^\n]{0,24}32\s*px",          # 「中央 … 32px …」
    r"32\s*px[^\n]{0,16}半透明",         # 「32px 半透明（圆钮）」
    r"半透明[^\n]{0,16}播放圆钮[^\n]{0,8}32\s*px",
]
_stale_hits = []
for _pat in _STALE_32PX:
    for _m in re.finditer(_pat, _card + "\n" + _prev):
        _stale_hits.append(_m.group(0)[:40])
_p13 = {
    "central_button_is_44px": "size-11" in _card,
    "no_stale_32px_source_fact": not _stale_hits,
    "volume_slider_has_pointer_handler": "onPointerDown" in _prev,
    "volume_slider_has_key_handler": "onKeyDown" in _prev,
    "volume_slider_aria_0_1": 'aria-valuemax={1}' in _prev,
    "preview_renders_video_element": "jimeng-video-preview-element" in _prev,
    "store_has_set_volume": "setVolume: (id" in _store,
    "card_pauses_when_preview_open": "previewOpen" in _card,
}

# ── P15：手册对账 ─────────────────────────────────────────────────────
_manual = _read(MANUAL)
_p15 = {
    "manual_has_clone_wording_section": "复刻口径" in _manual,
    "manual_states_44x44": "44×44" in _manual,
    "manual_covers_volume_slider": "音量滑杆" in _manual,
    "manual_covers_context_menu_download": "右键菜单" in _manual,
}

# ── P14：判据级阳性对照（把读数改坏 ⇒ 同一套判据必须红） ──────────────
_mut = None
if _readings:
    _c0 = _judge(_readings)
    _bad = json.loads(json.dumps(_readings))
    _bad["central_button_canvas_px"] = [32.0, 32.0]
    _bad["volume_drag"]["aria_changed"] = False
    _mc = _judge(_bad)
    _mut = {
        "n_p1_before": _c0["P1"],
        "n_p1_after": _mc["P1"],
        "n_p6_after": _mc["P6"],
        "p1_turned_red": (_c0["P1"] is True and _mc["P1"] is False),
        "p6_turned_red": (_c0["P6"] is True and _mc["P6"] is False),
        "note": "⭐ 判据级变异：只改读数、不碰真源 ⇒ 真源产物零污染",
    }

_c = _judge(_readings)
_c["P13"] = all(_p13.values()) if _p13 else None
_c["P15"] = all(_p15.values()) if _p15 else None
_c["P14"] = (_mut["p1_turned_red"] and _mut["p6_turned_red"]) if _mut else None

# ⚠️ 去掉 _states 这类内部键（它只是给 detail 用的）
_states = _c.pop("_states", None) or {}

out = {
    "generated_by": "jimeng_probe1039_media_playback_contract.py",
    "target": "jimeng-canvas-media-playback",
    "question": "⭐⭐⭐⭐⭐ **手册那一页描述的媒体播放操作，在当前复刻上成不成立？**",
    "probe_run": _run_info,
    "probe_crashed": bool(_crashed),
    "readings_available": bool(_readings),
    "readings_fresh": bool(_readings_fresh),
    "readings_file": str(READINGS.relative_to(ROOT)) if READINGS.exists() else None,
    "criteria": {k: _c.get(k) for k in CRIT_KEYS},
    "p13_static": _p13,
    "p15_manual": _p15,
    "p14_mutation": _mut,
    "detail": {
        "central_button_canvas_px": (_readings or {}).get("central_button_canvas_px"),
        "n_states_measured": len(_states),
        "state_labels": sorted(_states.keys()),
        "control_row_opacity_unselected": (_states.get("unselected") or {}).get("bar_opacity"),
        "control_row_opacity_playing": (_states.get("playing") or {}).get("bar_opacity"),
        "time_text_present_unselected": (_states.get("unselected") or {}).get("time_text_present"),
        "time_text_shape": (_states.get("unselected") or {}).get("time_text_shape"),
        "n_node_buttons": len((_states.get("unselected") or {}).get("node_button_arias") or []),
        "video_paused_playing_state": (_states.get("playing") or {}).get("video_paused"),
        "video_paused_deselected_state": (_states.get("deselected") or {}).get("video_paused"),
        "ctx_menu_n_items": len((( _readings or {}).get("ctx_menu") or {}).get("items") or []),
        "preview_has_video_element": ((_readings or {}).get("preview") or {}).get("has_video_element"),
        "preview_slider_aria": {
            "min": ((_readings or {}).get("preview") or {}).get("slider_aria_min"),
            "max": ((_readings or {}).get("preview") or {}).get("slider_aria_max"),
        },
        "volume_drag_landed_near_target": ((_readings or {}).get("volume_drag") or {}).get(
            "landed_near_target"),
        "n_aria_dead_candidates": len((_readings or {}).get("aria_dead_census") or []),
        "n_pageerrors": len((_readings or {}).get("pageerrors") or []),
    },
    "known_differences_vs_source": [
        "手册正文记的是**源站**读数；本门量的是**复刻**当前行为。"
        "两者的结构性差异（控件行用 opacity 门控而非条件挂载、`<video>` 常驻、"
        "中央播放钮三态都在）已在手册「复刻口径与源站口径的差异」一节逐条写明。",
        "源站当前画布上**没有带媒体的视频节点**（2026-10-25 复验："
        "76 个节点、0 个含 video 的元素）⇒ 源站侧读数只能取手册归档证据，"
        "本轮无法复验。",
    ],
}

false_list = [k for k, v in out["criteria"].items() if v is False]
none_list = [k for k, v in out["criteria"].items() if v is None]
out["n_false"] = len(false_list)
out["false_criteria"] = false_list
out["degraded_criteria"] = none_list

# ⭐⭐⭐ 判据台账：一条判据红了是「缺陷」还是「结论」——必须逐条定性
out["criterion_kinds_1039"] = {k: "failure" for k in CRIT_KEYS}
out["criterion_kinds_complete_1039"] = (
    set(out["criterion_kinds_1039"]) == set(out["criteria"]))
out["criteria_n_1039"] = len(out["criteria"])

OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

print("probe: %s | readings=%s" % (_run_info, "有" if _readings else "无"))
print("P1..P15 =", [out["criteria"].get(k) for k in CRIT_KEYS])
print("为假的：", false_list or "无", "| 降级：", none_list or "无")
print("PROBE_1039_MEDIA_PLAYBACK_DONE ->", OUT)

# ⭐⭐⭐ 三态退出码：2=仪器崩　1=判据红　0=全绿
if _crashed or not _readings:
    sys.exit(2)
sys.exit(1 if false_list else 0)
