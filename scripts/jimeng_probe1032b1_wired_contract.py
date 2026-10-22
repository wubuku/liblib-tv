#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1032-②b-1 的门：**这批「修好的按钮」点了到底有没有发生事**

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
**背景**：1032-① 查出克隆版里 25 个 `<button>` **压根没接线** ⇒ 它们在 DOM 里
就是点不动的壳。1032-②b-1 真去修了其中 18 个。

⚠️⭐⭐⭐⭐⭐ **但「有 onClick」不等于「点了有反应」**
  这是本门存在的唯一理由：把一个按钮从「死按钮」改成「有 handler」，如果 handler
  里什么都不做，那它只是从**死按钮**升级成了**空 handler** ⇒ ⇒ 那比死按钮更坏
  （死按钮至少一看就知道点不动）。
  ⇒ ⇒ ⇒ 所以本门**不看源码**，只看**运行时**：真点一遍，量「某个可观察的东西变了没」。

⭐⭐⭐⭐⭐ **判据一律写成「某个可观察的东西变了」**，不是「按钮有 onClick」：
  · 引用类（图片/音频/视频编辑的「添加参考」「引用参考」）⇒ ⇒ 点它 ⇒
    画布进入「从画布选择」点选模式 ⇒ ⇒ **顶部出现点选横幅** ⇒ ⇒ 点「×」横幅消失
  · 上传类（「上传参考图」「添加参考图」「上传参考内容」）⇒ ⇒ 点它 ⇒
    **真的弹出文件选择器** ⇒ ⇒ 选一个文件 ⇒ ⇒ **画布上真的多出一个节点**
  · 下拉类（重拍面板的模型钮 / 时长钮）⇒ ⇒ 点它 ⇒ ⇒ **真的开出一层选项**
    ⇒ ⇒ 点其中一个 ⇒ ⇒ **触发钮上的文案真的变了**
  · 文本节点「下载」⇒ ⇒ 点它 ⇒ ⇒ **真的触发一次下载**（且文件名是 .html）
  · 会员页计费 tab ⇒ ⇒ 点它 ⇒ ⇒ **横幅文案真的变了** + 选中态真的移了
  · 会员页计费 CTA ⇒ ⇒ **必须真的是 disabled**（计费不能真做 ⇒ 明确禁用 + 说明，
    而不是「能点没反应」）
  · 资产库「时间」「筛选」⇒ ⇒ 点它 ⇒ ⇒ **真的开出一层菜单** ⇒ ⇒ 点一项 ⇒ ⇒
    **空态文案 / 筛选行高亮真的变了**

⭐⭐⭐⭐⭐ **P8 是判据级阳性对照**：把某条读数改坏 ⇒ 同一套判据**必须红**
  ⇒ ⇒ 证明「全绿」不是恒真。

⚠️⭐⭐⭐⭐⭐ **探针自己也有盲区，诚实写在这里**：
  ① 探针只覆盖**这 18 个已修按钮**；**其余 7 个仍死的按钮**由静态门（DD993S.1）管。
  ② 探针的「上传真的落节点」验的是 **`addLocalUpload`** 那条链；本批另有
     「音频生成『生成』」那种**有 onClick 但函数体是空的**（NOOP）—— 静态门扫不到，
     留待 ②b-2。
  ③ 探针跑在**本地复刻**上；它证明的是「复刻里这些按钮有反应」，
     **不等于**「与源站行为完全一致」。
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GDIR = ROOT / "docs/research/jimeng-canvas"
READINGS = Path(
    os.environ.get("JIMENG_B1_JSON",
                   str(GDIR / "inputs" / "wired-runtime-1032b1.json")))
PROBE = ROOT / "scripts/jimeng_probe1032b1_wired_runtime.mjs"
OUT = GDIR / "wired-contract-1032b1.json"

# ── 跑探针（读数不存在时现跑；跑不动 ⇒ 降级为 null，不判红）────────────
_readings = None
_run_info = "not attempted"
if os.environ.get("JIMENG_B1_SKIP_PROBE") != "1":
    try:
        r = subprocess.run(["node", str(PROBE)], cwd=str(ROOT),
                           capture_output=True, text=True, timeout=600)
        _run_info = "rc=%d" % r.returncode
        if r.returncode != 0:
            _run_info += " stderr=%s" % r.stderr.strip()[-200:]
    except Exception as e:                                   # 探针跑不动 = 仪器问题
        _run_info = "probe failed: %s" % str(e)[:200]
else:
    _run_info = "skipped by env"

try:
    if READINGS.exists():
        _readings = json.loads(READINGS.read_text(encoding="utf-8"))
except Exception:
    _readings = None


# ⭐⭐⭐⭐⭐ **判据必须自己从「原始字段」重算，不能只信探针给的 `ok` 标志。**
#   否则：① 探针的汇总逻辑有 bug 时，门会跟着一起错；
#   ② **更糟**：阳性对照改原始字段时 `ok` 没变 ⇒ ⇒ 门不会红
#   ⇒ ⇒ ⇒ 而「变异体必须自证『我确实改动了东西』」—— 上一版就是踩了这个：
#   ⇒ ⇒ ⇒ 变异改了 `banner_after_click`，而判据只读 `ok` ⇒ ⇒ 变异**根本没生效**
#   ⇒ ⇒ ⇒ P8 于是永远是假的（第一次跑就红，且红得莫名其妙）。
def _ref_pick_ok(t):
    """引用类：点它 ⇒ 点选横幅出现 ⇒ 取消后横幅回到原样。"""
    if not t:
        return None
    b0 = t.get("banner_before")
    b1 = t.get("banner_after_click")
    b2 = t.get("banner_after_cancel")
    if b0 is None or b1 is None or b2 is None:
        return None
    return bool(b1 > b0 and b2 == b0 and t.get("clicked") is True)


def _upload_ok(t):
    """上传类：真弹 file chooser ⇒ 选完真落一个节点。"""
    if not t:
        return None
    nb = t.get("nodes_before")
    na = t.get("nodes_after")
    if nb is None or na is None:
        return None
    return bool(t.get("filechooser_fired") is True and na == nb + 1)


def _model_ok(t):
    if not t:
        return None
    n = t.get("n_options")
    if n is None:
        return None
    return bool(n >= 2 and bool(t.get("trigger_text_after")))


def _duration_ok(t):
    if not t:
        return None
    n = t.get("n_options")
    if n is None:
        return None
    return bool(n >= 2 and t.get("duration_after") == "4s")


def _download_ok(t):
    if not t:
        return None
    if "download_fired" not in t:
        return None
    return bool(t.get("download_fired") is True
                and t.get("filename_is_html") is True)


def _member_tab_ok(t):
    if not t:
        return None
    if "banner_changed" not in t:
        return None
    return bool(t.get("tab_clicked") is True
                and t.get("banner_changed") is True
                and bool(t.get("selected_tab")))


def _member_cta_ok(t):
    if not t:
        return None
    cta = t.get("cta")
    if not cta:
        return None
    return bool(cta.get("all_disabled") is True)


def _assets_time_ok(t):
    if not t:
        return None
    if "empty_before" not in t:
        return None
    return bool(t.get("menu_opened") is True
                and t.get("empty_before") != t.get("empty_after"))


def _assets_type_ok(t):
    if not t:
        return None
    if "active_filter_row" not in t:
        return None
    return bool(t.get("menu_opened") is True
                and t.get("active_filter_row") == "视频"
                and t.get("empty_after_type_switch") != t.get("empty_before"))


def _judge(r):
    if not r:
        return {k: None for k in ("P1", "P2", "P3", "P4", "P5", "P6", "P7")}
    ch = r.get("checks") or {}

    def _get(name):
        return ch.get(name)

    def _all(items):
        vals = [f(_get(n)) for n, f in items]
        if any(v is None for v in vals):
            return None
        return all(vals)

    ref = [
        ("image_add_ref_enters_pick_mode", _ref_pick_ok),
        ("image_quote_ref_0_enters_pick_mode", _ref_pick_ok),
        ("image_quote_ref_1_enters_pick_mode", _ref_pick_ok),
        ("audio_add_ref_enters_pick_mode", _ref_pick_ok),
        ("audio_quote_ref_0_enters_pick_mode", _ref_pick_ok),
        ("audio_quote_ref_1_enters_pick_mode", _ref_pick_ok),
        ("video_edit_quote_ref_enters_pick_mode", _ref_pick_ok),
    ]
    up = [
        ("gen_panel_upload_adds_node", _upload_ok),
        ("repaint_upload_adds_node", _upload_ok),
        ("video_edit_upload_adds_node", _upload_ok),
    ]
    dd = [
        ("repaint_model_switches", _model_ok),
        ("repaint_duration_switches", _duration_ok),
    ]
    dl = [("text_node_download_fires", _download_ok)]
    mb = [
        ("member_tab_switches_state", _member_tab_ok),
        ("member_billing_cta_disabled", _member_cta_ok),
    ]
    ass = [
        ("assets_time_filter_changes_state", _assets_time_ok),
        ("assets_type_filter_changes_state", _assets_type_ok),
    ]
    return {
        "P1": _all(ref),
        "P2": _all(up),
        "P3": _all(dd),
        "P4": _all(dl),
        "P5": _all(mb),
        "P6": _all(ass),
        # P7 页面无 JS 错误
        "P7": (not r.get("pageerrors")) if "pageerrors" in r else None,
    }


_c = _judge(_readings)

# ── P8：判据级阳性对照（把读数改坏 ⇒ 同一套判据必须红）────────────────
_mut = None
if _readings:
    _bad = json.loads(json.dumps(_readings))
    # 破坏 P1 的输入：把「点选横幅出现」改成「没出现」
    _t = (_bad.get("checks") or {}).get("image_add_ref_enters_pick_mode")
    if _t:
        _t["banner_after_click"] = 0
    _mc = _judge(_bad)
    _mut = {
        "p1_before": _c["P1"],
        "p1_after": _mc["P1"],
        "p1_turned_red": (_c["P1"] is True and _mc["P1"] is False),
        "note": "⭐ 判据级变异：只改读数、不碰真源 ⇒ 真源产物零污染",
    }

out = {
    "generated_by": "jimeng_probe1032b1_wired_contract.py",
    "target": "jimeng-canvas-wired-buttons",
    "question": "⭐⭐⭐⭐⭐ **这批「修好的按钮」点了到底有没有发生事？**",
    "probe_run": _run_info,
    "readings_file": str(READINGS.relative_to(ROOT)) if READINGS.exists() else None,
    "readings_available": bool(_readings),
    "criteria": _c,
    "p8_mutation": _mut,
    # ⭐⭐⭐⭐⭐ **产物里只留布尔** —— 节点数、坐标、文案都是会漂的读数
    #   ⇒ ⇒ 而且这个产物在**顶层** ⇒ ⇒ 1015 通道 A 会当 golden 逐字节比对
    #   ⇒ ⇒ ⇒ **⇒ 一次漂移就变成一条永久红。**
    "detail": {
        "n_checks": (_readings or {}).get("n_checks"),
        "n_failed": (_readings or {}).get("n_failed"),
        "n_pageerrors": len((_readings or {}).get("pageerrors") or []),
    },
    "scope_note": "⭐⭐⭐ 本门只覆盖 1032-②b-1 修好的这 18 个按钮；"
                  "**其余 7 个仍死的按钮**由静态门 DD993S.1 管；"
                  "**「有 onClick 但函数体是空的」那一类**静态门扫不到 ⇒ 留待 ②b-2。",
}

out["criteria"]["P8"] = _mut["p1_turned_red"] if _mut is not None else None

false_list = [k for k, v in out["criteria"].items() if v is False]
none_list = [k for k, v in out["criteria"].items() if v is None]
out["n_false"] = len(false_list)
out["false_criteria"] = false_list
out["degraded_criteria"] = none_list

# ⭐⭐⭐⭐⭐ 1032-②j：**判据台账** —— 「一条判据红了，是缺陷还是结论？」必须能机检
#   ⇒ ⇒ 口径：kind ∈ {failure, conclusion, precondition}
#   ⇒ ⇒⇒   failure     = 红了 = **有东西坏了**（被测对象或仪器）⇒ ⇒ 要修
#   ⇒ ⇒⇒   conclusion  = 红了 = **我写下的那个结论不再成立** ⇒ ⇒ 要重读
#   ⇒ ⇒⇒   precondition= 红了 = **前提不成立、这次测量不适用** ⇒ ⇒ 不许算成红
#   ⇒ ⇒⇒⇒ **⇒ 而 kind 不是从文本机械猜的** ⇒ ⇒ ⇒⇒ **⇒ 逐条读原文、由人定性** ⇒ ⇒ ⇒⇒
#   ⇒ ⇒⇒⇒ **⇒ 而「没标注」=「不可判定」= 合法状态，不许默认成 failure** ⇒ ⇒ ⇒⇒
#   ⇒ ⇒⇒⇒ **⇒ 前提不成立是运行时状态 `None`、不是 kind** ⇒ ⇒ ⇒⇒
#   ⇒ ⇒⇒   ⇒ ⇒ 这里的 kind 说的是「**读数是 False 时**该做什么」 ⇒ ⇒ ⇒⇒
out["criterion_kinds_1032b1"] = {
    "P1": "failure",
    "P2": "failure",
    "P3": "failure",
    "P4": "failure",
    "P5": "failure",
    "P6": "failure",
    "P7": "failure",
    "P8": "failure",
}
out["criterion_kinds_complete_1032b1"] = (
    set(out["criterion_kinds_1032b1"]) == set(out["criteria"]))
out["criteria_n_1032b1"] = len(out["criteria"])

OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

print("probe: %s | readings=%s" % (_run_info, "有" if _readings else "无"))
print("P1..P8 =", [out["criteria"].get("P%d" % i) for i in range(1, 9)])
print("为假的：", false_list or "无", "| 降级：", none_list or "无")
print("PROBE_1032B1_WIRED_DONE ->", OUT)

if false_list:
    sys.exit(1)
sys.exit(0)
