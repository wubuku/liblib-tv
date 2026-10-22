#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1032-②b-3 的门：重拍面板 / 视频编辑态里那两枚「提及主体」@ 钮
**点了到底有没有发生事**。

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
**这一批修的是「整枚没有 onClick」那一类糊弄** ⇒ 1032 静态门抓得到
（DEAD_NO_HANDLER）⇒ 本批把它销账（**死按钮 6 → 4**）。

⚠️⚠️⚠️ **但「有 onClick」不等于「点了有反应」** ⇒ ⇒ 所以本门
**不查源码里有没有 onClick**，而是**真点一遍**，验「某个可观察的东西变了」：

  · 点「提及主体」⇒ ⇒ 面板真的出现（`[data-testid="mention-panel"]`）
  · 面板是一级 listbox，aria 逐字 **`可能@的内容`**（SOURCE_FACT 批次 33）
  · 一级 4 个 role=option：主体 / 图片 / 视频 / 音频（批次 34：视频宿主 4 类）
  · 点某一级 ⇒ ⇒ **二级子菜单出现**（`[data-testid="mention-submenu"]`）
  · 二级**只列有可用资源的节点**（批次 114）；**没有时逐字「暂无相关节点」**
  · 选中一条 ⇒ ⇒ **提示词行多出一个引用 chip**（可观察的 DOM 变化）
  · ⭐ **负控 1**：「主体」这一级在**没有资源**时 ⇒ 逐字「暂无相关节点」
  · ⭐ **负控 2**：`Esc` ⇒ ⇒ 面板**关掉**、提示词**保留**
    （SOURCE_FACT 手册「退出路径」表：Esc → 面板关、提示词保留）
  · ⭐ **负控 3**：视频编辑态那一枚 @ 钮**也**能开面板

⭐⭐⭐⭐⭐ **P2..P10 每条判据都自己从**原始字段**重算**，**不信上游的 `ok` 标志**
  ⇒ ⇒ 上游 `ok` 是探针自己下的结论；门若只读它，探针算错时门也跟着错。

⭐⭐⭐⭐⭐ **P8 是判据级阳性对照**：把某条读数的**原始字段**改坏 ⇒ 同一套判据**必须红**
  ⇒ ⇒ 证明「全绿」不是恒真。
  ⇒ ⇒ 做法照 ②b-0 的教训：**只改读数副本、不碰真源** ⇒ ⇒ 真源产物零污染。
  ⇒ ⇒ ⭐ 改的是**原始字段**（`chips_after`），**不碰上游 `ok` 标志** ⇒
      变异后上游标志仍是 `true` 而门仍判红 ⇒ ⇒ 这才证明门是**重算**的。

⚠️ 盲区（诚实写在这里）：
  ① 面板的**几何**（240×244 / 232×48 / 二级 240×76）是 SOURCE_FACT，
     但本门**只验结构与行为**，**不钉几何**（几何会随宿主面板变化而变）。
  ② 源站上「重拍/视频编辑」态的 @ 面板**未直接实测**（源站画布上**没有
     有资源的视频节点** ⇒ 进不了编辑态；v3 探针上传后节点仍在
     `0 ready, 1 processing` ⇒ 拿不到 ready 态的编辑入口）⇒
     ⇒ 本门验的是「复刻里 @ 钮的行为符合**已实测的 @ 面板规格**」，
     **不等于**「复刻与源站逐字一致」。
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GDIR = ROOT / "docs/research/jimeng-canvas"
READINGS = Path(
    os.environ.get("JIMENG_B3_JSON",
                   str(GDIR / "inputs" / "mention-runtime-1032b3.json")))
PROBE = ROOT / "scripts/jimeng_probe1032b3_mention_runtime.mjs"
OUT = GDIR / "mention-contract-1032b3.json"

# ── 跑探针（读数不存在时现跑；跑不动 ⇒ 降级为 null，不判红）────────────
_readings = None
_run_info = "not attempted"
_crashed = False
if os.environ.get("JIMENG_B3_SKIP_PROBE") != "1":
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
#   ⇒ ⇒ 否则「本轮没跑」会被伪装成「本轮跑过了」⇒ ⇒ 门报绿 ⇒ ⇒ **假绿**
#   ⇒ ⇒⇒ 而这正是 1015 抓到的那个漂移的另一半：探针崩 ⇒ 契约产物多出 200 多字节
#   ⇒ ⇒⇒   ⇒ ⇒ 1014 的指纹跟着变 ⇒ ⇒ 两本 golden 一起漂。
if _crashed:
    _readings = None

out = {
    "generated_by": "jimeng_probe1032b3_mention_contract.py",
    "measured_at": "2026-10-21",
    "probe": str(PROBE.relative_to(ROOT)),
    "probe_run": _run_info,
    "probe_crashed": bool(_crashed),
    "source_fact": "面板规格 = 手册批次 33/34/113/114（@ 面板全量实测）；"
                   "退出路径 = 手册「退出路径」表。",
    "P": {},
}

checks = (_readings or {}).get("checks") or {}


def _ok(name):
    c = checks.get(name)
    return bool(c) and c.get("ok") is True


def _detail(name):
    c = checks.get(name)
    return c if isinstance(c, dict) else {}


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _judge_chip(checks_map):
    """P6 的判据：自己从**原始字段**重算，不信上游给的 ok 标志。

    上游 ok 标志是探针自己算的结论；门若只读它，探针算错时门也跟着错。
    所以这里只认 chips_before / chips_after 两个原始读数。
    """
    c = (checks_map or {}).get("picking_candidate_inserts_chip")
    if not isinstance(c, dict):
        return False, "读数缺失"
    before = c.get("chips_before")
    after = c.get("chips_after")
    if not _is_int(before) or not _is_int(after):
        return False, "原始字段缺失或非整数: before=%r after=%r" % (before, after)
    ok = (after > before) and (after >= 1)
    return bool(ok), "chips_before=%r chips_after=%r" % (before, after)


# ── P1：探针真的跑起来了（**仪器没跑 ≠ 产品坏了**）────────────────────
# ⭐⭐⭐⭐⭐ **P1 = 「本轮探针真的跑成了」** —— 不是「读数文件存在」
#   ⇒ ⇒ 读数文件**上一轮就留下了** ⇒ ⇒ 只查它存在 ⇒ ⇒ **探针崩了门照样绿**
#   ⇒ ⇒⇒ 所以必须同时看「这一轮探针的退出码」与「读数是不是本轮的」。
_upstream_all_ok = bool(_readings) and all(
    (c.get("ok") is True) for c in checks.values() if isinstance(c, dict))
_p1 = (bool(_readings) and (not _crashed)
       and isinstance(_readings.get("n_checks"), int)
       and _readings.get("n_checks", 0) >= 10)
out["P"]["P1_probe_actually_ran_1032b3"] = bool(_p1)
out["P1_detail"] = {"run": _run_info, "crashed": bool(_crashed),
                     "n_checks": (_readings or {}).get("n_checks"),
                     "n_failed": (_readings or {}).get("n_failed"),
                     "upstream_all_ok": bool(_upstream_all_ok),
                     "n_raw_checks": len(checks)}

# ── P2：面板真的能打开（点 @ ⇒ 面板出现）─────────────────────────────
_c2 = _detail("mention_panel_opens")
_p2 = (_c2.get("panel_count", 0) >= 1) and (_c2.get("panel_visible") is True)
out["P"]["P2_mention_panel_opens_1032b3"] = bool(_p2)
out["P2_detail"] = _c2

# ── P3：面板是 listbox，aria 逐字「可能@的内容」（SOURCE_FACT 批次 33）──
_c3 = _detail("mention_panel_is_listbox_may_at_content")
_p3 = (_c3.get("role") == "listbox") and (_c3.get("aria") == "可能@的内容") \
    and (_c3.get("n_options") == 4)
out["P"]["P3_panel_is_listbox_may_at_content_1032b3"] = bool(_p3)
out["P3_detail"] = _c3

# ── P4：一级四类齐全（批次 34：视频宿主 4 类）────────────────────────
_c4 = _detail("mention_panel_has_four_categories")
_p4 = _c4.get("labels") == ["主体", "图片", "视频", "音频"]
out["P"]["P4_four_categories_1032b3"] = bool(_p4)
out["P4_detail"] = _c4

# ── P5：二级子菜单出现**且**列出有资源的节点（批次 114）─────────────
_c5 = _detail("mention_submenu_opens_with_resource_nodes")
_p5 = (_c5.get("submenu_count", 0) >= 1) and (_c5.get("n_items", 0) >= 1)
out["P"]["P5_submenu_lists_resource_nodes_1032b3"] = bool(_p5)
out["P5_detail"] = _c5

# ── P6：选中候选 ⇒ 真的插出引用 chip（**从原始字段重算**）────────────
_p6, _p6_why = _judge_chip(checks)
out["P"]["P6_pick_inserts_chip_1032b3"] = bool(_p6)
out["P6_detail"] = dict(_detail("picking_candidate_inserts_chip"))
out["P6_detail"]["recomputed_from_raw"] = _p6_why

# ── P7：负控 —— 无资源 ⇒ 逐字「暂无相关节点」；Esc ⇒ 面板关、提示词保留
_c7a = _detail("subject_category_empty_when_no_resource")
_c7b = _detail("escape_closes_panel_and_keeps_prompt")
_p7a = (_c7a.get("empty_text") == "暂无相关节点") and (_c7a.get("n_items") == 0)
_p7b = (_c7b.get("panel_before", 0) >= 1) and (_c7b.get("panel_after") == 0) \
    and bool(_c7b.get("prompt_value"))
out["P"]["P7_negative_controls_1032b3"] = bool(_p7a and _p7b)
out["P7_detail"] = {"empty": _c7a, "escape": _c7b,
                     "empty_ok": bool(_p7a), "escape_ok": bool(_p7b)}

# ── P8：判据级阳性对照 —— 改坏一条**原始字段** ⇒ 同一套判据**必须红** ─
#   ⭐ 只改读数副本，**不碰真源产物** ⇒ 真源零污染。
#   ⭐⭐ 改的是**原始字段**（chips_after），**不碰上游 ok 标志** ⇒
#       若门只信 ok 标志，变异后仍会绿 ⇒ 门必须红才证明它从原始字段重算。
_mutation = None
_mut_ok = False
if _readings:
    import copy
    mutated = copy.deepcopy(_readings)
    mchecks = mutated.get("checks", {})
    tgt = mchecks.get("picking_candidate_inserts_chip")
    if isinstance(tgt, dict) and _is_int(tgt.get("chips_after")):
        orig_after = tgt.get("chips_after")
        orig_before = tgt.get("chips_before")
        tgt["chips_after"] = orig_before if _is_int(orig_before) else orig_after - 1
        _mutation = ("把原始字段 chips_after 从 %r 改成 %r"
                     "（只改读数副本，不碰真源产物）" % (orig_after, tgt["chips_after"]))
        mut_j, mut_why = _judge_chip(mchecks)
        base_j, base_why = _judge_chip(checks)
        _mut_ok = (base_j is True) and (mut_j is False) \
            and (tgt["chips_after"] != orig_after)
        out["P8_detail"] = {
            "mutation": _mutation,
            "base_judgement_green": bool(base_j),
            "base_why": base_why,
            "mutated_judgement_red": bool(mut_j is False),
            "mutated_why": mut_why,
            "field_actually_changed": tgt["chips_after"] != orig_after,
            "upstream_ok_flag_left_untouched": tgt.get("ok"),
            "note": "变异后上游 ok 标志仍是 true 而门仍判红"
                    " => 门是从原始字段重算的，不信 ok 标志",
        }
    else:
        _mutation = "目标判据的原始字段不在读数里 => 阳性对照没跑成（不是通过了）"
        out["P8_detail"] = {"mutation": _mutation, "mutated_ok": None,
                            "judgement_is_red": None}
    out["P"]["P8_mutation_makes_judgement_red_1032b3"] = bool(_mut_ok)
else:
    out["P"]["P8_mutation_makes_judgement_red_1032b3"] = False
    out["P8_detail"] = {"mutation": "无读数 => 阳性对照没跑成", "mutated_ok": None,
                        "judgement_is_red": None}

# ── P9：视频编辑态那一枚 @ 钮也是活的（两处都接上了）─────────────────
_c9 = _detail("video_edit_mention_panel_opens")
_p9 = (_c9.get("panel_count", 0) >= 1) and (_c9.get("panel_visible") is True)
out["P"]["P9_video_edit_mention_panel_opens_1032b3"] = bool(_p9)
out["P9_detail"] = _c9

# ── P10：无 JS 错误 ─────────────────────────────────────────────────
_c10 = _detail("no_page_errors")
out["P"]["P10_no_page_errors_1032b3"] = (_c10.get("n") == 0)
out["P10_detail"] = _c10

flags = list(out["P"].values())
out["n_checks"] = len(flags)
out["n_failed"] = sum(1 for f in flags if f is not True)
out["all_ok"] = all(f is True for f in flags)

OUT.parent.mkdir(parents=True, exist_ok=True)
# ⭐⭐⭐⭐⭐ 1032-②j：**判据台账** —— 「一条判据红了，是缺陷还是结论？」必须能机检
#   ⇒ ⇒ 口径：kind ∈ {failure, conclusion, precondition}
#   ⇒ ⇒⇒   failure     = 红了 = **有东西坏了**（被测对象或仪器）⇒ ⇒ 要修
#   ⇒ ⇒⇒   conclusion  = 红了 = **我写下的那个结论不再成立** ⇒ ⇒ 要重读
#   ⇒ ⇒⇒   precondition= 红了 = **前提不成立、这次测量不适用** ⇒ ⇒ 不许算成红
#   ⇒ ⇒⇒⇒ **⇒ 而 kind 不是从文本机械猜的** ⇒ ⇒ ⇒⇒ **⇒ 逐条读原文、由人定性** ⇒ ⇒ ⇒⇒
#   ⇒ ⇒⇒⇒ **⇒ 而「没标注」=「不可判定」= 合法状态，不许默认成 failure** ⇒ ⇒ ⇒⇒
#   ⇒ ⇒⇒⇒ **⇒ 前提不成立是运行时状态 `None`、不是 kind** ⇒ ⇒ ⇒⇒
#   ⇒ ⇒⇒   ⇒ ⇒ 这里的 kind 说的是「**读数是 False 时**该做什么」 ⇒ ⇒ ⇒⇒
out["criterion_kinds_1032b3"] = {
    "P1_probe_actually_ran_1032b3": "precondition",
    "P2_mention_panel_opens_1032b3": "failure",
    "P3_panel_is_listbox_may_at_content_1032b3": "failure",
    "P4_four_categories_1032b3": "failure",
    "P5_submenu_lists_resource_nodes_1032b3": "failure",
    "P6_pick_inserts_chip_1032b3": "failure",
    "P7_negative_controls_1032b3": "failure",
    "P8_mutation_makes_judgement_red_1032b3": "failure",
    "P9_video_edit_mention_panel_opens_1032b3": "failure",
    "P10_no_page_errors_1032b3": "failure",
}
out["criterion_kinds_complete_1032b3"] = (
    set(out["criterion_kinds_1032b3"]) == set(out["P"]))
out["criteria_n_1032b3"] = len(out["P"])

OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

print("P 判据 =", flags)
bad = [k for k, v in out["P"].items() if v is not True]
print("P 为假的：", ("、".join(bad) if bad else "无"), "| 共 %d 条" % len(flags))
print("PROBE_1032B3_MENTION_CONTRACT_DONE ->", OUT)
sys.exit(0 if out["all_ok"] else 1)
