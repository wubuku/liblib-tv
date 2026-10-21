#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1032-②b-4 的门：「**已展开的生成器**」浮层 —— 点「展开」到底有没有发生事。

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
**这一批销掉的是最后一批死按钮**（静态门 DEAD_NO_HANDLER）：
三条「展开面板」+ 一条「展开视频生成器」此前**整枚没有 onClick**
⇒ ⇒ 死按钮 **4 → 0**。

⚠️⚠️⚠️ **但「有 onClick」不等于「点了有反应」** ⇒ ⇒ 所以本门
**不查源码里有没有 onClick**，而是**真点一遍**，验「某个可观察的东西变了」。

⭐⭐⭐⭐⭐ **P2..P14 每条判据都自己从**原始字段**重算**，**不信上游的 `ok` 标志**
  ⇒ ⇒ 上游 `ok` 是探针自己下的结论；门若只读它，探针算错时门也跟着错。

⭐⭐⭐⭐⭐ **P15 是判据级阳性对照**：把某条读数的**原始字段**改坏 ⇒ 同一套判据**必须红**
  ⇒ ⇒ 证明「全绿」不是恒真。
  ⇒ ⇒ 做法：**只改读数副本、不碰真源** ⇒ 真源产物零污染；
  ⇒ ⇒ ⭐ 改的是**原始字段**、**不碰上游 `ok` 标志** ⇒ 变异后上游标志仍是 `true`
      而门仍判红 ⇒ ⇒ 这才证明门是**重算**的。

⚠️ 盲区（诚实写在这里）：
  ① 源站只实测过**视频**这一种展开浮层（批次 1032-②b-1 产物
     `source-expanded-gen-1032b1.json`）⇒ ⇒ 图片 / 音频两种是 **CLONE_DECISION**。
  ② 源站 5 枚类型按钮（全部/图片/视频/音频/文本）的**确切作用未逐项验证**
     ⇒ ⇒ 复刻实现为「参考类型筛选」（`aria-pressed` + 「引用参考」aria 随类型变）。
  ③ 源站「退出路径」表只覆盖 @ 面板 ⇒ ⇒ 「Esc 关浮层但提示词不保留」是 CLONE_DECISION。
  ④ 本门**不钉**「死按钮总数」这种会合法漂移的数。
"""
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GDIR = ROOT / "docs/research/jimeng-canvas"
READINGS = Path(
    os.environ.get("JIMENG_B4_JSON",
                   str(GDIR / "inputs" / "expanded-runtime-1032b4.json")))
PROBE = ROOT / "scripts/jimeng_probe1032b4_expanded_runtime.mjs"
OUT = GDIR / "expanded-contract-1032b4.json"

# ── 跑探针（读数不存在时现跑；跑不动 ⇒ 降级为 null，不判红）────────────
_readings = None
_run_info = "not attempted"
_crashed = False
if os.environ.get("JIMENG_B4_SKIP_PROBE") != "1":
    try:
        r = subprocess.run(["node", str(PROBE)], cwd=str(ROOT),
                           capture_output=True, text=True, timeout=900)
        _run_info = "rc=%d" % r.returncode
        # ⭐⭐⭐⭐⭐ **「仪器故障」有独立退出码（2）** ⇒ ⇒ 本门据此知道
        #   「这轮探针没跑成」⇒ ⇒ 而不是把它当成「产品坏了」。
        if r.returncode == 2 or "INSTRUMENT_CRASH" in (r.stdout or ""):
            _crashed = True
            _run_info = "rc=2 instrument-crash"
        elif r.returncode != 0:
            _run_info += " stderr=%s" % r.stderr.strip()[-200:]
    except Exception as e:                                   # 探针跑不动 = 仪器问题
        _crashed = True
        _run_info = "probe failed: %s" % str(e)[:200]
else:
    _run_info = "skipped by env"
    # ⭐⭐⭐⭐⭐ 跳过 ⇒ **本轮探针没跑** ⇒ ⇒ 同样不许拿旧读数冒充
    _crashed = True

try:
    _readings = json.loads(READINGS.read_text(encoding="utf-8"))
except Exception:                                             # noqa: BLE001
    _readings = None
# ⭐⭐⭐⭐⭐ **探针崩了 ⇒ 不许拿「上一轮留下的旧读数」冒充本轮读数。**
if _crashed:
    _readings = None

out = {
    "generated_by": "jimeng_probe1032b4_expanded_contract.py",
    "measured_at": "2026-10-21",
    "probe": str(PROBE.relative_to(ROOT)),
    "probe_run": _run_info,
    "probe_crashed": bool(_crashed),
    "source_fact": "浮层规格 = 批次 1032-②b-1 实测（**只覆盖视频这一种**）；"
                   "图片 / 音频两种是 CLONE_DECISION。",
    "P": {},
}

checks = (_readings or {}).get("checks") or {}


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _c(checks_map, name):
    v = (checks_map or {}).get(name)
    return v if isinstance(v, dict) else {}


# ── 判据函数：全部只认**原始字段**，不看上游 ok 标志 ────────────────────
def j_open_layer(m):
    d = _c(m, "expand_button_opens_layer")
    if not d:
        return False, "读数缺失"
    ok = (d.get("clicked") is True) and (d.get("layer_count") == 1) \
        and (d.get("layer_visible") is True)
    return bool(ok), "clicked=%r layer_count=%r layer_visible=%r" % (
        d.get("clicked"), d.get("layer_count"), d.get("layer_visible"))


def j_dialog_aria(m):
    d = _c(m, "layer_is_dialog_with_source_aria")
    if not d:
        return False, "读数缺失"
    ok = (d.get("role") == "dialog") and (d.get("aria") == "已展开的视频生成器")
    return bool(ok), "role=%r aria=%r" % (d.get("role"), d.get("aria"))


def j_geometry(m):
    d = _c(m, "layer_geometry_matches_source")
    if not d:
        return False, "读数缺失"
    for k in ("w", "h", "center_dx", "center_dy"):
        if not _is_int(d.get(k)):
            return False, "字段缺失或非整数: %s=%r" % (k, d.get(k))
    ok = (d.get("w") == 920) and (d.get("h") == 480) \
        and (d.get("position") == "fixed") \
        and (d.get("border_radius") == "20px") \
        and (str(d.get("z_index")) == "50") \
        and (abs(d.get("center_dx")) <= 1) and (abs(d.get("center_dy")) <= 1)
    return bool(ok), ("w=%r h=%r pos=%r radius=%r z=%r dx=%r dy=%r" % (
        d.get("w"), d.get("h"), d.get("position"), d.get("border_radius"),
        d.get("z_index"), d.get("center_dx"), d.get("center_dy")))


def j_no_input(m):
    d = _c(m, "layer_has_no_input_or_textarea")
    if not d:
        return False, "读数缺失"
    ok = (d.get("n_input") == 0) and (d.get("n_textarea") == 0) \
        and (_is_int(d.get("n_contenteditable")) and d.get("n_contenteditable") >= 1)
    return bool(ok), "n_input=%r n_textarea=%r n_contenteditable=%r" % (
        d.get("n_input"), d.get("n_textarea"), d.get("n_contenteditable"))


def j_five_buttons(m):
    d = _c(m, "layer_has_five_ref_type_buttons")
    found = d.get("found")
    if not isinstance(found, list):
        return False, "found 不是数组"
    ok = (len(found) == 5) and (d.get("n_tab") == 0) \
        and all(isinstance(f, dict) and f.get("w") == 42 and f.get("h") == 36
                and not f.get("role") for f in found) \
        and not d.get("bad")
    return bool(ok), "n=%d n_tab=%r bad=%r sizes=%r" % (
        len(found), d.get("n_tab"), d.get("bad"),
        [(f.get("t"), f.get("w"), f.get("h")) for f in found
         if isinstance(f, dict)])


def j_ref_switch(m):
    d = _c(m, "ref_type_switch_is_observable")
    if not d:
        return False, "读数缺失"
    before = d.get("aria_before")
    after = d.get("aria_after")
    ok = (d.get("clicked") is True) and isinstance(before, str) \
        and isinstance(after, str) and (before != after)
    return bool(ok), "clicked=%r before=%r after=%r" % (
        d.get("clicked"), before, after)


def j_empty_prompt(m):
    d = _c(m, "empty_prompt_generate_does_nothing")
    if not d:
        return False, "读数缺失"
    ok = (d.get("clicked") is True) and (d.get("generating_visible") is False)
    return bool(ok), "clicked=%r generating_visible=%r" % (
        d.get("clicked"), d.get("generating_visible"))


def j_generating(m):
    d = _c(m, "generate_enters_generating")
    if not d:
        return False, "读数缺失"
    ok = (d.get("typed") is True) and (d.get("clicked") is True) \
        and (d.get("generating_visible") is True)
    return bool(ok), "typed=%r clicked=%r generating_visible=%r" % (
        d.get("typed"), d.get("clicked"), d.get("generating_visible"))


def j_collapse(m):
    d = _c(m, "collapse_button_closes_layer")
    if not d:
        return False, "读数缺失"
    ok = (d.get("has") is True) and (d.get("clicked") is True) \
        and (d.get("layer_count") == 0)
    return bool(ok), "has=%r clicked=%r layer_count=%r" % (
        d.get("has"), d.get("clicked"), d.get("layer_count"))


def j_escape(m):
    d = _c(m, "escape_closes_layer_but_keeps_edit_mode")
    if not d:
        return False, "读数缺失"
    ok = (d.get("clicked") is True) and (d.get("layer_before") == 1) \
        and (d.get("layer_after") == 0) and (d.get("node_still_selected") is True)
    return bool(ok), "clicked=%r before=%r after=%r still_selected=%r" % (
        d.get("clicked"), d.get("layer_before"), d.get("layer_after"),
        d.get("node_still_selected"))


def j_backdrop(m):
    d = _c(m, "backdrop_click_closes_layer")
    if not d:
        return False, "读数缺失"
    ok = (d.get("clicked") is True) and (d.get("layer_before") == 1) \
        and (d.get("backdrop_clicked") is True) and (d.get("layer_after") == 0)
    return bool(ok), "clicked=%r backdrop=%r before=%r after=%r" % (
        d.get("clicked"), d.get("backdrop_clicked"),
        d.get("layer_before"), d.get("layer_after"))


def j_insert_select(m):
    d = _c(m, "insert_selects_only_the_new_node")
    if not d:
        return False, "读数缺失"
    ok = (d.get("n_selected") == 1) and (d.get("new_is_selected") is True)
    return bool(ok), "n_selected=%r new_is_selected=%r" % (
        d.get("n_selected"), d.get("new_is_selected"))


def j_no_errors(m):
    d = _c(m, "no_page_errors")
    return (d.get("n") == 0), "n=%r" % (d.get("n"),)


# ── P1：探针真的跑起来了（**仪器没跑 ≠ 产品坏了**）────────────────────
_upstream_all_ok = bool(_readings) and all(
    (c.get("ok") is True) for c in checks.values() if isinstance(c, dict))
_p1 = (bool(_readings) and (not _crashed)
       and isinstance(_readings.get("n_checks"), int)
       and _readings.get("n_checks", 0) >= 14)
out["P"]["P1_probe_actually_ran_1032b4"] = bool(_p1)
out["P1_detail"] = {"run": _run_info, "crashed": bool(_crashed),
                     "n_checks": (_readings or {}).get("n_checks"),
                     "n_failed": (_readings or {}).get("n_failed"),
                     "upstream_all_ok": bool(_upstream_all_ok),
                     "n_raw_checks": len(checks)}

# ── P2..P14 ─────────────────────────────────────────────────────────
_JUDGES = [
    ("P2", "P2_expand_button_opens_layer_1032b4", j_open_layer,
     "expand_button_opens_layer"),
    ("P3", "P3_layer_is_dialog_source_aria_1032b4", j_dialog_aria,
     "layer_is_dialog_with_source_aria"),
    ("P4", "P4_layer_geometry_matches_source_1032b4", j_geometry,
     "layer_geometry_matches_source"),
    ("P5", "P5_no_input_or_textarea_1032b4", j_no_input,
     "layer_has_no_input_or_textarea"),
    ("P6", "P6_five_ref_type_buttons_1032b4", j_five_buttons,
     "layer_has_five_ref_type_buttons"),
    ("P7", "P7_ref_type_switch_observable_1032b4", j_ref_switch,
     "ref_type_switch_is_observable"),
    ("P8", "P8_empty_prompt_generate_does_nothing_1032b4", j_empty_prompt,
     "empty_prompt_generate_does_nothing"),
    ("P9", "P9_generate_enters_generating_1032b4", j_generating,
     "generate_enters_generating"),
    ("P10", "P10_collapse_closes_layer_1032b4", j_collapse,
     "collapse_button_closes_layer"),
    ("P11", "P11_escape_closes_layer_keeps_edit_mode_1032b4", j_escape,
     "escape_closes_layer_but_keeps_edit_mode"),
    ("P12", "P12_backdrop_click_closes_layer_1032b4", j_backdrop,
     "backdrop_click_closes_layer"),
    ("P13", "P13_insert_selects_only_new_node_1032b4", j_insert_select,
     "insert_selects_only_the_new_node"),
    ("P14", "P14_no_page_errors_1032b4", j_no_errors,
     "no_page_errors"),
]
for _short, _key, _fn, _upname in _JUDGES:
    _ok_, _why = _fn(checks)
    out["P"][_key] = bool(_ok_)
    out[_short + "_detail"] = {
        "recomputed_from_raw": _why,
        "upstream_check": _upname,
        "upstream_ok": _c(checks, _upname).get("ok"),
    }

# ── P15：判据级阳性对照 —— 改坏一条**原始字段** ⇒ 同一套判据**必须红** ─
#   ⭐ 只改读数副本，**不碰真源产物** ⇒ 真源零污染。
#   ⭐⭐ 改的是**原始字段**（几何的 w），**不碰上游 ok 标志** ⇒
#       若门只信 ok 标志，变异后仍会绿 ⇒ 门必须红才证明它从原始字段重算。
_mut_ok = False
_mut_detail = {"mutation": "无读数 => 阳性对照没跑成", "mutated_ok": None,
               "judgement_is_red": None}
if _readings:
    mutated = copy.deepcopy(_readings)
    mchecks = mutated.get("checks", {})
    tgt = mchecks.get("layer_geometry_matches_source")
    if isinstance(tgt, dict) and _is_int(tgt.get("w")):
        orig_w = tgt.get("w")
        tgt["w"] = orig_w - 1
        mut_j, mut_why = j_geometry(mchecks)
        base_j, base_why = j_geometry(checks)
        _mut_ok = (base_j is True) and (mut_j is False) and (tgt["w"] != orig_w)
        _mut_detail = {
            "mutation": "把原始字段 w 从 %r 改成 %r（只改读数副本，不碰真源产物）"
                        % (orig_w, tgt["w"]),
            "base_judgement_green": bool(base_j),
            "base_why": base_why,
            "mutated_judgement_red": bool(mut_j is False),
            "mutated_why": mut_why,
            "field_actually_changed": tgt["w"] != orig_w,
            "upstream_ok_flag_left_untouched": tgt.get("ok"),
            "note": "变异后上游 ok 标志仍是 true 而门仍判红"
                    " => 门是从原始字段重算的，不信 ok 标志",
        }
    else:
        _mut_detail = {"mutation": "目标判据的原始字段不在读数里 => 阳性对照没跑成",
                       "mutated_ok": None, "judgement_is_red": None}
out["P"]["P15_mutation_makes_judgement_red_1032b4"] = bool(_mut_ok)
out["P15_detail"] = _mut_detail

flags = list(out["P"].values())
out["n_checks"] = len(flags)
out["n_failed"] = sum(1 for f in flags if f is not True)
out["all_ok"] = all(f is True for f in flags)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

print("P 判据 =", flags)
bad = [k for k, v in out["P"].items() if v is not True]
print("P 为假的：", ("、".join(bad) if bad else "无"), "| 共 %d 条" % len(flags))
print("PROBE_1032B4_EXPANDED_CONTRACT_DONE ->", OUT)
sys.exit(0 if out["all_ok"] else 1)
