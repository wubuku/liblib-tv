#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 1035：**手册说的 ⟷ 复刻做的** —— 主体标注一致性门。

## 这道门答的是哪一个问题
  「手册正文里那些读者会照着做的句子，在复刻上是否还成立」。

  1035 的运行时实测（clone-persistence-1035.json）量到三条事实：
    1) 复刻刷新后**回到初始 mock 态**（改名、加节点都丢，localStorage 0 个键）；
    2) 「发现离线编辑」对话框在**界面上没有任何触发点**；
    3) 但它**经 dev hook 可达**（`__jimengStore.getState().setOfflineDialog(true)`）。

  而手册正文（canvas-context / 90-troubleshooting / 20-reference）里：
    · 重命名的「成功判据」写的是「刷新后仍是新名」——那是**源站**的判据；
    · 「内容跨刷新持久（实测）」——也是**源站**的实测；
    · 「出现『发现离线编辑』对话框」的处置段——复刻里那个弹窗没有自动触发路径。

  ⇒ 三处都是**源站事实被写成了通用说法** ⇒ 照着做的复刻用户必然失败，
    而失败长得像「复刻坏了」。

## 本门钉的是什么
  **不是**「复刻刷新即复位」这件事本身（那是本原型的取舍），
  而是**文档必须逐条标明主体**、并且**给复刻侧一条可执行的替代动作**。

  ⇒ 所以将来若实现了持久化，这道门会红 —— 它会提醒「手册该改了」。

## 三态退出码
  0 = 判据全绿 / 1 = 判据红 / 2 = 仪器崩（数据侧问题）。
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANUAL = ROOT / "docs" / "user-manual" / "jimeng-canvas"
RUNTIME_PRODUCT = (
    ROOT / "docs" / "research" / "jimeng-canvas" / "inputs" / "clone-persistence-1035.json"
)
OUT = ROOT / "docs" / "research" / "jimeng-canvas" / "manual-clone-parity-1035.json"

# 标注词（手册正文里用它标出「这一条在复刻上不同」）
MARK = "复刻差异"

# 每一条要求：文件 / 锚句 / 必须在锚句之后多少行内出现标注 / 标注块里必须出现的词
REQUIREMENTS = [
    {
        "id": "R1_canvas_context_rename_success_criterion",
        "file": "10-tasks/canvas-context.md",
        "anchor": "刷新后仍是新名",
        "window_lines": 14,
        "must_contain": ["源站", "复刻", "刷新"],
        "why": "重命名的「成功判据」是复刻用户会照着做的动作，而它写的是源站的判据",
    },
    {
        "id": "R2_canvas_context_persist_claim",
        "file": "10-tasks/canvas-context.md",
        "anchor": "内容跨刷新持久",
        "window_lines": 14,
        "must_contain": ["源站", "复刻"],
        "why": "「内容跨刷新持久（实测）」是源站实测，复刻刷新即复位",
    },
    {
        "id": "R3_troubleshooting_saved_doubt",
        "file": "90-troubleshooting.md",
        "anchor": "怀疑改动未保存",
        "window_lines": 16,
        "must_contain": ["源站", "复刻", "刷新"],
        "why": "排障页教用户「刷新页面核对」，而复刻刷新一定复位",
    },
    {
        "id": "R4_troubleshooting_offline_dialog",
        "file": "90-troubleshooting.md",
        "anchor": "发现离线编辑",
        "window_lines": 16,
        "must_contain": ["源站", "复刻", "__jimengStore"],
        "why": "复刻里这个弹窗界面上不可达，必须给出 dev hook 这条可执行的测试路径",
    },
    {
        "id": "R5_reference_persistence_layers",
        "file": "20-reference.md",
        "anchor": "持久化：三层各存在哪",
        "window_lines": 16,
        "must_contain": ["源站", "复刻"],
        "why": "「三层各存在哪」整节都是源站取证，复刻的持久化面与之不同",
    },
]


def _lines(text):
    return text.split("\n")


def _section_bounds(ls, a):
    """锚句所在小节的行号区间 [start, end)。

    小节 = 最近一个在它之前的标题行，到下一个标题行为止。
    ⇒ 「标注必须在这一小节里」比「在这一小节附近」严得多，
    ⇒ 也避免了「两个相邻小节各有一处标注 ⇒ 串味」。
    """
    start = 0
    for i in range(a, -1, -1):
        if re.match(r"^#{2,6}\s", ls[i]):
            start = i
            break
    end = len(ls)
    for i in range(a + 1, len(ls)):
        if re.match(r"^#{2,6}\s", ls[i]):
            end = i
            break
    return start, end


def find_marker(text, req):
    """锚句所在小节里，是否有一段带「复刻差异」标注的说明块。

    返回 (行号, 块文本) 或 None。
    """
    ls = _lines(text)
    hits = [i for i, l in enumerate(ls) if req["anchor"] in l]
    if not hits:
        return None
    a = hits[0]
    start, end = _section_bounds(ls, a)
    for m in range(start, end):
        if MARK in ls[m]:
            block = "\n".join(ls[m : m + 10])
            return (m + 1, block)
    return None


def requirement_ok(text, req):
    """一条要求是否满足：找到标注块，且块里含全部 must_contain 词。"""
    got = find_marker(text, req)
    if got is None:
        return False, "no_marker_near_anchor"
    line, block = got
    missing = [w for w in req["must_contain"] if w not in block]
    if missing:
        return False, "marker_missing_words:" + ",".join(missing)
    return True, "ok@line%d" % line


def strip_markers(text):
    """负控用：把带标注的块整段抠掉（标注行 + 其后连续的引用行）。

    只动内存里的副本 —— 手册文件本身绝不改。
    """
    ls = _lines(text)
    out = []
    i = 0
    removed = 0
    while i < len(ls):
        if MARK in ls[i]:
            removed += 1
            i += 1
            while i < len(ls) and ls[i].lstrip().startswith(">"):
                i += 1
            continue
        out.append(ls[i])
        i += 1
    return "\n".join(out), removed


def _read(path):
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def main():
    crit = {}
    detail = {}
    kinds = {}
    per_req = []

    # ── 运行时事实 ───────────────────────────────────────────────────────
    rt = None
    try:
        rt = json.loads(RUNTIME_PRODUCT.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        sys.stderr.write("RUNTIME_PRODUCT_UNREADABLE (data-side, rc=2): %s\n" % e)
        return 2
    r = rt.get("readings") or {}

    def g(path, default=None):
        cur = r
        for k in path.split("."):
            if not isinstance(cur, dict) or k not in cur:
                return default
            cur = cur[k]
        return cur

    # P1 探针有牙：改完不刷新时读数确实变了
    crit["P1_probe_can_read_a_change_1035"] = bool(
        g("probe_can_read_change.name_changed") and g("probe_can_read_change.n_nodes_changed")
    )
    kinds["P1_probe_can_read_a_change_1035"] = "failure"

    # P2 刷新确实复位（复刻没有持久化）
    crit["P2_refresh_resets_the_clone_1035"] = bool(
        g("refresh_resets.name_reset_to_initial") and g("refresh_resets.n_nodes_reset_to_initial")
    )
    kinds["P2_refresh_resets_the_clone_1035"] = "failure"

    # P3 离线弹窗在界面上不可达
    crit["P3_offline_dialog_unreachable_from_ui_1035"] = (
        g("offline_dialog_ui.n_trigger_candidates", 1) == 0
        and g("offline_dialog_ui.in_dom_at_start", True) is False
    )
    kinds["P3_offline_dialog_unreachable_from_ui_1035"] = "failure"

    # P4 离线弹窗经 dev hook 可达（=> 手册可以给出这条测试路径）
    crit["P4_offline_dialog_reachable_via_devhook_1035"] = bool(
        g("offline_dialog_devhook.dialog_opened") and g("offline_dialog_devhook.dialog_in_dom_after_hook")
    )
    kinds["P4_offline_dialog_reachable_via_devhook_1035"] = "failure"

    # P5 每一条要求都必须在手册里贴着那条说、标明主体
    all_ok = True
    for req in REQUIREMENTS:
        path = MANUAL / req["file"]
        text = _read(path)
        if text is None:
            ok, why = False, "manual_file_unreadable"
        else:
            ok, why = requirement_ok(text, req)
        per_req.append(
            {
                "id": req["id"],
                "file": req["file"],
                "anchor": req["anchor"],
                "ok": ok,
                "why": why,
                "why_this_matters": req["why"],
            }
        )
        if not ok:
            all_ok = False
    crit["P5_every_requirement_is_marked_in_place_1035"] = all_ok
    kinds["P5_every_requirement_is_marked_in_place_1035"] = "failure"

    # P6 负控：把标注抠掉，判据必须翻红（否则上面那条是恒真）
    neg_all_red = True
    neg_rows = []
    for req in REQUIREMENTS:
        text = _read(MANUAL / req["file"])
        if text is None:
            neg_all_red = False
            neg_rows.append({"id": req["id"], "ok": False, "why": "manual_file_unreadable"})
            continue
        stripped, removed = strip_markers(text)
        ok_after, why_after = requirement_ok(stripped, req)
        red = (ok_after is False) and removed >= 1
        neg_rows.append(
            {
                "id": req["id"],
                "n_markers_removed": removed,
                "still_ok_after_removal": ok_after,
                "why_after_removal": why_after,
                "went_red": red,
            }
        )
        if not red:
            neg_all_red = False
    crit["P6_negative_control_turns_the_claim_red_1035"] = neg_all_red
    kinds["P6_negative_control_turns_the_claim_red_1035"] = "failure"

    # P7 手册必须写清「复刻侧用户该怎么办」而不仅是「不一样」
    actionable = True
    for req in REQUIREMENTS:
        text = _read(MANUAL / req["file"])
        got = find_marker(text or "", req)
        if got is None:
            actionable = False
            continue
        block = got[1]
        if not re.search(r"刷新|复位|回到初始|控制台|__jimengStore", block):
            actionable = False
    crit["P7_every_marker_gives_an_actionable_alternative_1035"] = actionable
    kinds["P7_every_marker_gives_an_actionable_alternative_1035"] = "failure"

    crit["P8_scope_and_limits_published_1035"] = bool(
        rt.get("what_this_is_not") and rt.get("scan_scope")
    )
    kinds["P8_scope_and_limits_published_1035"] = "failure"

    red = [k for k, v in crit.items() if v is not True]
    out = {
        "generated_by": "jimeng_probe1035_manual_clone_parity_gate.py",
        "what_this_gate_asks": "手册正文里那些读者会照着做的句子，在复刻上是否还成立；不成立的地方必须贴着标明主体并给出复刻侧可执行的动作。",
        "what_this_is_not": "这不是「复刻刷新即复位」的判决 —— 那是本原型的取舍；这道门钉的是「文档有没有标明主体」。",
        "criteria_1035": crit,
        "criterion_kinds_1035": kinds,
        "criterion_kinds_complete_1035": True,
        "n_criteria_1035": len(crit),
        "requirements_1035": per_req,
        "negative_control_1035": neg_rows,
        "runtime_product": str(RUNTIME_PRODUCT.relative_to(ROOT)),
        "runtime_readings_1035": r,
        "rule": "⭐⭐⭐⭐⭐ **「源站事实」写成通用说法，等于给复刻用户一条必然失败的操作步骤** ⇒ ⇒⇒ 而失败长得像「复刻坏了」 ⇒ ⇒⇒ ⇒ 所以本门只钉「有没有标明主体」，不钉「复刻该不该持久化」。",
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("判据逐条 = " + " | ".join("%s=%s" % (k, crit[k]) for k in crit))
    print("P 为假的： " + ("无" if not red else ", ".join(red)))
    print("PROBE_1035_MANUAL_CLONE_PARITY_DONE -> %s" % OUT)
    return 0 if not red else 1


if __name__ == "__main__":
    sys.exit(main())
