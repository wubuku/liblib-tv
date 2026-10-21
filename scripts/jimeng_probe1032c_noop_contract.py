#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1032-②b-c 的门：**每一个可点元素点了到底有没有发生事**。

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
**这一批要抓的那一类糊弄：NOOP —— 有 onClick，但函数体是空的。**
静态门把它算成 WIRED ⇒ ⇒ **静态门看不见这一类** ⇒ ⇒ 只有运行时能抓。
⭐ 而「点了只弹一句 toast」（FAKE_SUCCESS）是同一族 ⇒ ⇒ 一并量出来。

⭐⭐⭐⭐⭐ **本门最重要的一条是 P2（仪器有牙）** ——
普查探针第一版报「NOOP 0 个」，看起来是满分 ⇒ ⇒ **而真相是 208 个点击里 178 个超时失败**
（某个点击打开了遮罩 ⇒ ⇒ 后面的按钮全被盖住 ⇒ ⇒ Playwright 的可操作性检查一直等不到）
⇒ ⇒ ⇒ **「0 个 NOOP」在那种读数下是假零，比不报更坏。**
⇒ ⇒⇒⇒ 处置：① 每个按钮前重载到干净态；② 用 DOM 派发点击（绕开命中测试）；
③ **把「点击失败数」做成读数**，并由 **P2 断言它为 0** ⇒ ⇒ **门自己知道自己的读数可不可信。**

⭐⭐⭐⭐⭐ **P2..P8 每条判据都自己从**原始字段**重算**，**不信上游的 `ok` 标志**
  ⇒ ⇒ 上游 `ok` 是探针自己下的结论；门若只读它，探针算错时门也跟着错。

⭐⭐⭐⭐⭐ **P7 是判据级阳性对照**：把某一行读数的**原始字段**改坏 ⇒ 同一套判据**必须红**
  ⇒ ⇒ 证明「全绿」不是恒真；⇒ ⇒ 做法：**只改读数副本、不碰真源** ⇒ 真源产物零污染。

⚠️ 盲区（诚实写在这里）：
  ① 本门用 **DOM 派发点击**（验的是「这个 handler 有没有做事」），
     **不是**「用户能不能点到它」⇒ ⇒ 后者由 ②b-1 的**真实鼠标**探针管。
  ② 场景只覆盖 **5 种**（无选中 / 视频 / 文本 / 音频 / 时间线节点）；
     **画布上根本没有图片节点** ⇒ ⇒ 「图片」场景记为 `not_applicable`。
  ③ 「生成 / 发送 / 购买 / 充值」一族按纪律**跳过**（记为 `SKIPPED_BY_POLICY`）。
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
    os.environ.get("JIMENG_C4_JSON",
                   str(GDIR / "inputs" / "noop-census-1032c.json")))
PROBE = ROOT / "scripts/jimeng_probe1032c_noop_census.mjs"
OUT = GDIR / "noop-contract-1032c.json"

# ── 跑探针（读数不存在时现跑；跑不动 ⇒ 降级为 null，不判红）────────────
_readings = None
_run_info = "not attempted"
_crashed = False
if os.environ.get("JIMENG_C4_SKIP_PROBE") != "1":
    try:
        r = subprocess.run(["node", str(PROBE)], cwd=str(ROOT),
                           capture_output=True, text=True, timeout=3600)
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
    _crashed = True

try:
    _readings = json.loads(READINGS.read_text(encoding="utf-8"))
except Exception:                                             # noqa: BLE001
    _readings = None
# ⭐⭐⭐⭐⭐ **探针崩了 ⇒ 不许拿「上一轮留下的旧读数」冒充本轮读数。**
if _crashed:
    _readings = None

out = {
    "generated_by": "jimeng_probe1032c_noop_contract.py",
    "measured_at": "2026-10-21",
    "probe": str(PROBE.relative_to(ROOT)),
    "probe_run": _run_info,
    "probe_crashed": bool(_crashed),
    "source_fact": "「点了有没有发生事」= 运行时量；源站**不参与**（本门只验复刻侧自洽）。",
    "P": {},
}

KNOWN_CLASSES = {"REAL", "DISABLED", "SKIPPED_BY_POLICY", "NOOP",
                 "TOAST_ONLY", "NAVIGATED", "ERROR", "CLICK_FAILED",
                 "SCENARIO_GONE"}


def _rows(readings):
    """把各场景的行摊平（**原始字段**，不认任何汇总数）"""
    out_rows = []
    sc = (readings or {}).get("scenarios") or {}
    for sid in sorted(sc.keys()):
        s = sc[sid] or {}
        for r in (s.get("buttons") or []):
            if isinstance(r, dict):
                out_rows.append((sid, r))
    return out_rows


def _cls_counts(rows):
    n = {}
    for _, r in rows:
        c = r.get("cls")
        n[c] = n.get(c, 0) + 1
    return n


def j_no_noop(rows):
    """P4：没有任何一枚按钮「点了什么也没发生」"""
    bad = [{"scenario": sid, "name": r.get("name"), "where": r.get("where")}
           for sid, r in rows if r.get("cls") == "NOOP"]
    return (len(bad) == 0), ("NOOP %d 条：%r" % (len(bad), bad[:6]))


def j_no_toast_only(rows):
    """P5：没有任何一枚按钮「只弹了一句 toast」"""
    bad = [{"scenario": sid, "name": r.get("name"), "where": r.get("where")}
           for sid, r in rows if r.get("cls") == "TOAST_ONLY"]
    return (len(bad) == 0), ("TOAST_ONLY %d 条：%r" % (len(bad), bad[:6]))


def j_instrument_teeth(rows):
    """P2 ⭐⭐⭐：**仪器自己有牙吗** —— 点击失败 / 报错 / 找不到元素，一个都不许有"""
    bad = [{"scenario": sid, "name": r.get("name"), "cls": r.get("cls"),
            "click_result": r.get("click_result")}
           for sid, r in rows
           if r.get("cls") in ("CLICK_FAILED", "ERROR", "SCENARIO_GONE")]
    return (len(bad) == 0), ("不可信 %d 条：%r" % (len(bad), bad[:6]))


def j_all_classified(rows):
    """P3：每一枚按钮都拿到了一个**已知**的判决（不许有没判的）"""
    bad = [{"scenario": sid, "name": r.get("name"), "cls": r.get("cls")}
           for sid, r in rows if r.get("cls") not in KNOWN_CLASSES]
    return (len(bad) == 0), ("无判决/未知判决 %d 条：%r" % (len(bad), bad[:6]))


def j_summary_consistent(rows, readings):
    """P6：探针自报的汇总数与**从行重算**的汇总数必须一致（同一件事的两份读数）"""
    if not readings:
        return False, "无读数"
    counts = _cls_counts(rows)
    recomputed = {
        "n_noop": counts.get("NOOP", 0),
        "n_toast_only": counts.get("TOAST_ONLY", 0),
        "n_click_failed": counts.get("CLICK_FAILED", 0) + counts.get("ERROR", 0),
        "n_buttons": len(rows),
    }
    ok = (readings.get("n_noop") == recomputed["n_noop"]
          and readings.get("n_toast_only") == recomputed["n_toast_only"]
          and readings.get("n_click_failed") == recomputed["n_click_failed"]
          and readings.get("n_buttons") == recomputed["n_buttons"])
    return bool(ok), "自报=%r 重算=%r" % (
        {k: readings.get(k) for k in ("n_noop", "n_toast_only",
                                       "n_click_failed", "n_buttons")},
        recomputed)


# ── P1：探针真的跑起来了（**仪器没跑 ≠ 产品坏了**）────────────────────
_rows_flat = _rows(_readings)
_upstream_all_ok = bool(_readings) and all(
    (c.get("ok") is True) for c in (_readings.get("checks") or {}).values()
    if isinstance(c, dict))
_p1 = (bool(_readings) and (not _crashed)
       and isinstance(_readings.get("n_buttons"), int)
       and _readings.get("n_buttons", 0) > 0)
out["P"]["P1_probe_actually_ran_1032c"] = bool(_p1)
out["P1_detail"] = {"run": _run_info, "crashed": bool(_crashed),
                     "n_buttons": (_readings or {}).get("n_buttons"),
                     "n_rows": len(_rows_flat),
                     "n_scenarios": len((_readings or {}).get("scenarios") or {})}

# ── P2..P6 ─────────────────────────────────────────────────────────
_p2, _w2 = j_instrument_teeth(_rows_flat)
out["P"]["P2_instrument_had_teeth_1032c"] = bool(_p2)
out["P2_detail"] = {"recomputed_from_raw": _w2}

_p3, _w3 = j_all_classified(_rows_flat)
out["P"]["P3_every_button_got_a_verdict_1032c"] = bool(_p3)
out["P3_detail"] = {"recomputed_from_raw": _w3,
                    "class_counts": _cls_counts(_rows_flat)}

_p4, _w4 = j_no_noop(_rows_flat)
out["P"]["P4_no_button_is_a_noop_1032c"] = bool(_p4)
out["P4_detail"] = {"recomputed_from_raw": _w4}

_p5, _w5 = j_no_toast_only(_rows_flat)
out["P"]["P5_no_button_only_toasts_1032c"] = bool(_p5)
out["P5_detail"] = {"recomputed_from_raw": _w5}

_p6, _w6 = j_summary_consistent(_rows_flat, _readings)
out["P"]["P6_summary_matches_rows_1032c"] = bool(_p6)
out["P6_detail"] = {"recomputed_from_raw": _w6}

# ── P7：判据级阳性对照 —— 改坏一行**原始字段** ⇒ 同一套判据**必须红** ─
#   ⭐ 只改读数副本，**不碰真源产物** ⇒ 真源零污染。
#   ⭐⭐ 改的是**原始字段**（把一行的 `cls` 从 REAL 改成 NOOP），
#         **不碰任何 `ok` 标志** ⇒ 若门只信 `ok`，变异后仍会绿 ⇒ 门必须红。
_mut_ok = False
_mut_detail = {"mutation": "无读数 => 阳性对照没跑成", "mutated_ok": None,
               "judgement_is_red": None}
if _readings:
    mutated = copy.deepcopy(_readings)
    mrows = _rows(mutated)
    hit = None
    for sid, r in mrows:
        if r.get("cls") == "REAL":
            hit = r
            break
    if hit is not None:
        orig = hit.get("cls")
        hit["cls"] = "NOOP"
        mut_j, mut_why = j_no_noop(mrows)
        base_j, base_why = j_no_noop(_rows_flat)
        _mut_ok = (base_j is True) and (mut_j is False) and (hit.get("cls") != orig)
        _mut_detail = {
            "mutation": "把一行的原始字段 cls 从 %r 改成 'NOOP'（只改读数副本，不碰真源产物）"
                        % (orig,),
            "base_judgement_green": bool(base_j),
            "base_why": base_why,
            "mutated_judgement_red": bool(mut_j is False),
            "mutated_why": mut_why,
            "field_actually_changed": hit.get("cls") != orig,
            "note": "变异后门仍判红 => 门是从原始字段重算的，不信上游汇总数",
        }
    else:
        _mut_detail = {"mutation": "读数里没有一行 REAL => 阳性对照没跑成",
                       "mutated_ok": None, "judgement_is_red": None}
out["P"]["P7_mutation_makes_judgement_red_1032c"] = bool(_mut_ok)
out["P7_detail"] = _mut_detail

# ── P8：无未捕获异常 ───────────────────────────────────────────────
_pe = (_readings or {}).get("pageerrors") or []
out["P"]["P8_no_page_errors_1032c"] = (len(_pe) == 0)
out["P8_detail"] = {"n": len(_pe)}

flags = list(out["P"].values())
out["n_checks"] = len(flags)
out["n_failed"] = sum(1 for f in flags if f is not True)
out["all_ok"] = all(f is True for f in flags)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

print("P 判据 =", flags)
bad = [k for k, v in out["P"].items() if v is not True]
print("P 为假的：", ("、".join(bad) if bad else "无"), "| 共 %d 条" % len(flags))
print("PROBE_1032C_NOOP_CONTRACT_DONE ->", OUT)
sys.exit(0 if out["all_ok"] else 1)
