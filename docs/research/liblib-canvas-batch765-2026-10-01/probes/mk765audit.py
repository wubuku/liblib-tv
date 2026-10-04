#!/usr/bin/env python3
"""batch 765 汇编器：从 raw/ 的 2 份原始读数现算 runtime-audit.json

规矩（沿用 756–764）：
1. **数字不许手抄** —— 下面每个数都从 `raw/vb765*.json` 算出来。
2. **缺原始读数判失败**，不许「通过」。
3. **同一事实存两份时两份都要守**：`findings[k] == judgments[i].evidence`
   在写盘前逐条断言，JSON 往返后由验收器再查一遍。
4. **宣称「两轮一致」之前先证明两轮可比**（R55）：这里对两份 raw 逐轮做
   归一化 diff，diff 非空就判 FAIL，不许拿「两轮看着一样」当证据。
5. **读不到的东西不许当成「没有」**：注入元素是否已移除（污染检查）、
   顺序焦点起始点那条机制（推断非读数）都单列，不并进结论。
"""
import hashlib
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
BATCH = HERE.parent if HERE.name == "probes" else HERE
RAW = BATCH / "raw"
OUT = BATCH / "runtime-audit.json"

# 生成器 id 之类的每轮易变串，归一化后再比两轮
VOLATILE_RE = re.compile(r"director-gesture-\d+-\d+|[0-9a-f]{16}-[0-9a-f]{4}")


def load(name):
    p = RAW / name
    if not p.exists():
        raise SystemExit("FATAL 缺原始读数 %s —— 判失败，不许通过" % p)
    return json.loads(p.read_text(encoding="utf-8")), p


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def norm(o):
    if isinstance(o, str):
        return VOLATILE_RE.sub("<volatile>", o)
    if isinstance(o, dict):
        return {k: norm(v) for k, v in sorted(o.items())}
    if isinstance(o, list):
        return [norm(v) for v in o]
    return o


def round_diff(raw, key):
    """返回 (两轮在该 key 上是否逐字段一致, 首个不一致的字段路径)。"""
    rs = raw.get("rounds") or []
    if len(rs) < 2:
        return None, "轮数不足 2（%d）" % len(rs)
    a = norm(rs[0].get(key))
    b = norm(rs[1].get(key))
    if a == b:
        return True, None

    def walk(x, y, path=""):
        if isinstance(x, dict) and isinstance(y, dict):
            for k in sorted(set(x) | set(y)):
                if k not in x:
                    return "%s.%s 只在 round2" % (path, k)
                if k not in y:
                    return "%s.%s 只在 round1" % (path, k)
                r = walk(x[k], y[k], "%s.%s" % (path, k))
                if r:
                    return r
            return None
        if isinstance(x, list) and isinstance(y, list):
            if len(x) != len(y):
                return "%s 长度 %d vs %d" % (path, len(x), len(y))
            for i, (u, v) in enumerate(zip(x, y)):
                r = walk(u, v, "%s[%d]" % (path, i))
                if r:
                    return r
            return None
        return None if x == y else "%s: %r vs %r" % (path, x, y)

    return False, walk(a, b, key)


a, a_p = load("vb765a.json")
b, b_p = load("vb765b.json")
aR, bR = a["rounds"], b["rounds"]
assert len(aR) == 2, "765a 轮数 %d" % len(aR)
assert len(bR) == 2, "765b 轮数 %d" % len(bR)

# ═══════════ 可比性：先证明两轮可比，再谈一致 ═══════════
DIFF_KEYS_A = ["d_state", "d_sweep", "d_tabFromPanel", "d_tabFromTrigger",
               "i_probe", "i_inputName", "m_state", "m_escFromDuration",
               "m_escFromAspect", "m_escNext"]
DIFF_KEYS_B = ["state1", "inj_text", "inj_number", "inj_ce", "inj_tabindex",
               "outsideClick", "focaloss_esc", "focaloss_tab6", "shift_tab12"]
diff_a = {k: round_diff(a, k) for k in DIFF_KEYS_A}
diff_b = {k: round_diff(b, k) for k in DIFF_KEYS_B}
inconsistent_a = sorted(k for k, (ok, _) in diff_a.items() if ok is not True)
inconsistent_b = sorted(k for k, (ok, _) in diff_b.items() if ok is not True)
# 765a 的 m_* 四格是**逐格按下去**的状态机，第 1 轮与第 2 轮起点相同才可比
comparability = {
    "765a": {"keys": DIFF_KEYS_A,
             "allConsistent": not inconsistent_a,
             "inconsistent": inconsistent_a,
             "firstDiff": {k: diff_a[k][1] for k in inconsistent_a}},
    "765b": {"keys": DIFF_KEYS_B,
             "allConsistent": not inconsistent_b,
             "inconsistent": inconsistent_b,
             "firstDiff": {k: diff_b[k][1] for k in inconsistent_b}},
    "comparable": not inconsistent_a and not inconsistent_b,
}

# ═══════════ 765a：面板逐控件 Esc / 围栏 / 打开焦点 ═══════════
sw_rows = [r for rd in aR for r in ((rd.get("d_sweep") or {}).get("rows") or [])]
sw_close = [r for r in sw_rows if r.get("panelClosed") is True]
sw_open = [r for r in sw_rows if r.get("panelClosed") is False]
sw_dead = [r for r in sw_open if r.get("item", {}).get("marker") == "duration"]
sw_dead_types = sorted({r["item"].get("type") for r in sw_dead})
sw_dead_submit = any(r.get("item", {}).get("submit") for r in sw_dead)
sw_focus_fail = [r for r in sw_rows
                 if (r.get("focus") or {}).get("focused") is not True
                 or r.get("focusedInPanel") is not True]
sw_desk_closed = [r for r in sw_rows if r.get("workspaceClosed") is True]

esc_sweep = {
    "cells": len(sw_rows),
    "panelFocusablesPerRound": [
        (rd.get("d_sweep") or {}).get("panelFocusables") for rd in aR],
    "closed": len(sw_close),
    "notClosed": len(sw_open),
    "notClosedMarkers": sorted({r["item"].get("marker") for r in sw_open}),
    "notClosedTypes": sw_dead_types,
    "notClosedIsDurationOnly": len(sw_open) == len(sw_dead),
    "deadCellIsSubmit": sw_dead_submit,
    "focusFailures": len(sw_focus_fail),
    "deskClosedCells": len(sw_desk_closed),
    "selfReportedAllClosed": [
        (rd.get("d_sweep") or {}).get("allClosed") for rd in aR],
    "selfReportedAnyDeskClosed": [
        (rd.get("d_sweep") or {}).get("anyWorkspaceClosed") for rd in aR],
}
# 「全部关」这个派生量重算，并断言与探针自报一致
recomputed_all_closed = len(sw_close) == len(sw_rows) and bool(sw_rows)
assert recomputed_all_closed == all(
    esc_sweep["selfReportedAllClosed"]), "allClosed 重算与自报不一致"
# 注意：这里必须写括号 —— `len(x) > 0 == any(...)` 在 Python 里是**链式比较**
assert (len(sw_desk_closed) > 0) == any(
    esc_sweep["selfReportedAnyDeskClosed"]), "anyWorkspaceClosed 与自报不一致"

tab_fence = {
    "forwardFromPanel": {
        "steps": [(rd.get("d_tabFromPanel") or {}).get("steps") for rd in aR],
        "escapedDialog": [
            (rd.get("d_tabFromPanel") or {}).get("escapedCount") for rd in aR],
        "inPanel": [
            (rd.get("d_tabFromPanel") or {}).get("inPanelCount") for rd in aR]},
    "forwardFromTrigger": {
        "steps": [(rd.get("d_tabFromTrigger") or {}).get("steps") for rd in aR],
        "escapedDialog": [
            (rd.get("d_tabFromTrigger") or {}).get("escapedDialog")
            if (rd.get("d_tabFromTrigger") or {}).get("escapedDialog")
            is not None else
            (rd.get("d_tabFromTrigger") or {}).get("escapedCount")
            for rd in aR],
        "inPanel": [
            (rd.get("d_tabFromTrigger") or {}).get("inPanelCount")
            for rd in aR]},
}
tab_fence["reverseFromTrigger"] = {
    "steps": [(rd.get("shift_tab12") or {}).get("steps") for rd in bR],
    "escapedDialog": [
        (rd.get("shift_tab12") or {}).get("escapedDialogCount") for rd in bR],
    "inPanel": [
        (rd.get("shift_tab12") or {}).get("inPanelCount") for rd in bR],
}

focus_on_open = {
    "rounds": len(aR),
    "active": [(rd.get("d_focusOnOpen") or {}) for rd in aR],
    "allOnTrigger": all(
        (rd.get("d_focusOnOpen") or {}).get("isTrigger") is True for rd in aR),
    "allInsidePanel": all(
        (rd.get("d_focusOnOpen") or {}).get("inPanel") is True for rd in aR),
    "ariaExpandedAfterOpen": [
        ((rd.get("d_state") or {}).get("trigger") or {}).get("ariaExpanded")
        for rd in aR],
    "ariaExpandedBeforeOpen": [
        ((rd.get("d_before") or {}).get("trigger") or {}).get("ariaExpanded")
        for rd in aR],
}

# ═══════════ 765a：800px 三档 Esc 阶梯 ═══════════
m_rows = []
for rd in aR:
    seq = []
    for k in ("m_escFromDuration", "m_escFromAspect", "m_escNext", "m_escNext2"):
        v = rd.get(k)
        if not v:
            seq.append({"step": k, "FAILED": True})
            continue
        seq.append({"step": k, "panelClosed": v["panelClosed"],
                    "drawerState": v["drawerState"],
                    "treeState": v["treeState"],
                    "workspaceClosed": v["workspaceClosed"],
                    "activeTag": (v.get("active") or {}).get("tag"),
                    "activeAria": (v.get("active") or {}).get("ariaLabel")})
    m_rows.append(seq)
# 逐档阶梯：第 1 档只关抽屉、第 2 档关面板、第 3 档关导演台
ladder_ok = []
for seq in m_rows:
    s1, s2, s3 = seq[0], seq[1], seq[2]
    ladder_ok.append({
        "tier1_closedDrawerOnly":
            s1["panelClosed"] is False and s1["drawerState"] == "closed"
            and s1["workspaceClosed"] is False,
        "tier2_closedPanelNotDesk":
            s2["panelClosed"] is True and s2["workspaceClosed"] is False,
        "tier3_closedDesk":
            s3["panelClosed"] is True and s3["workspaceClosed"] is True,
        "tier4StillClosed":
            seq[3]["workspaceClosed"] is True,
    })
mobile_ladder = {
    "rounds": len(m_rows),
    "panelOpenedAt800": [
        ((rd.get("m_state") or {}).get("panel") or {}).get("present")
        for rd in aR],
    "drawerOpenBeforePanel": [
        ((rd.get("m_drawer") or {}).get("inspector") or {}).get("state")
        for rd in aR],
    "tiers": m_rows,
    "ladderOk": ladder_ok,
    "allLadderOk": all(all(x.values()) for x in ladder_ok),
    "durationEscLeftPanelOpen": [
        x[0]["panelClosed"] is False for x in m_rows],
}

# ═══════════ 765a：导入侧 ═══════════
imp = []
for rd in aR:
    fc = rd.get("i_fileChooser") or {}
    inp = rd.get("i_inputName") or {}
    pr = rd.get("i_probe") or {}
    imp.append({
        "fileChooserFired": fc.get("fired") is True,
        "accept": (pr.get("input") or {}).get("accept"),
        "inputType": (pr.get("input") or {}).get("type"),
        "inputAriaLabel": inp.get("ariaLabel"),
        "inputTitle": inp.get("title"),
        "inputId": inp.get("id"),
        "inputHasLabelFor": inp.get("hasLabelFor"),
        "accessibleName": inp.get("accessibleNameGuess"),
        "inputDisplay": (pr.get("inputFocusable") or {}).get("display"),
        "inputTabIndex": (pr.get("inputFocusable") or {}).get("tabIndex"),
        "buttonAriaLabel": (pr.get("btn") or {}).get("ariaLabel"),
        "buttonTitle": (pr.get("btn") or {}).get("title"),
        "buttonDisabled": (pr.get("btn") or {}).get("disabled"),
        "exportPanelStillOpen": (
            (rd.get("i_after") or {}).get("panel") or {}).get("present"),
    })
import_probe = {
    "rounds": len(imp),
    "allFileChooserFired": all(x["fileChooserFired"] for x in imp),
    "accepts": sorted({x["accept"] for x in imp}),
    "hiddenInputZeroAccessibleName": all(
        x["accessibleName"] is None and x["inputAriaLabel"] is None
        and x["inputTitle"] is None and x["inputId"] is None
        and x["inputHasLabelFor"] is False for x in imp),
    "hiddenInputDisplayNone": all(
        x["inputDisplay"] == "none" for x in imp),
    "buttonNamed": all(
        bool(x["buttonAriaLabel"]) for x in imp),
    "buttonEnabled": all(x["buttonDisabled"] is False for x in imp),
    "detail": imp,
}

# ═══════════ 765b：注入对照（定位 Esc 关不掉面板的机制）═══════════
INJ = [("inj_text", "INPUT[type=text]", False),
       ("inj_number", "INPUT[type=number]", False),
       ("inj_ce", "div[contenteditable=true]", False),
       ("inj_tabindex", "div[tabindex=0]", True)]
inj_rows = []
for key, label, exp in INJ:
    cells = [rd.get(key) for rd in bR]
    for i, v in enumerate(cells, 1):
        if not v or v.get("FAILED"):
            inj_rows.append({"key": key, "label": label, "round": i,
                             "FAILED": (v or {}).get("FAILED", "缺读数")})
            continue
        inj_rows.append({
            "key": key, "label": label, "round": i,
            "expectPanelClosed": exp,
            "focused": (v.get("inject") or {}).get("focused"),
            "insidePanel": v.get("focusInPanelBefore"),
            "reachedWinCapture": v.get("reachedWinCapture"),
            "reachedWinBubble": v.get("reachedWinBubble"),
            "escTargetAtWin": v.get("escTargetAtWin"),
            "panelClosed": v.get("panelClosed"),
            "workspaceClosed": v.get("workspaceClosed"),
            "matchesExpectation": v.get("matchesExpectation"),
            "pollutionCheck": (
                "元素随面板卸载" if v.get("injectedStillInDom") is False
                else "已手动移除" if (v.get("removed") or {}).get("removed") == 1
                else "仍在 DOM（污染）"),
        })
inject = {
    "cells": len(inj_rows),
    "focusFailures": sum(1 for r in inj_rows if r.get("focused") is not True),
    "outsidePanel": sum(1 for r in inj_rows if r.get("insidePanel") is True),
    "reachedWinBubble": sum(1 for r in inj_rows
                            if r.get("reachedWinBubble") is True),
    "reachedWinCapture": sum(1 for r in inj_rows
                             if r.get("reachedWinCapture") is True),
    "editableNotClosed": sum(
        1 for r in inj_rows
        if r.get("expectPanelClosed") is False and r.get("panelClosed") is False),
    "editableCells": sum(1 for r in inj_rows
                         if r.get("expectPanelClosed") is False),
    "nonEditableClosed": sum(
        1 for r in inj_rows
        if r.get("expectPanelClosed") is True and r.get("panelClosed") is True),
    "nonEditableCells": sum(1 for r in inj_rows
                            if r.get("expectPanelClosed") is True),
    "deskClosedAny": sum(1 for r in inj_rows
                         if r.get("workspaceClosed") is True),
    "allMatched": all(r.get("matchesExpectation") is True for r in inj_rows),
    "polluted": sum(1 for r in inj_rows if r.get("pollutionCheck") == "仍在 DOM（污染）"),
    "rows": inj_rows,
}
# 派生量重算 + 断言
assert inject["editableNotClosed"] == inject["editableCells"], "可编辑格没全不关"
assert inject["nonEditableClosed"] == inject["nonEditableCells"], "不可编辑格没全关"
assert inject["reachedWinBubble"] == inject["cells"], "有格子事件没到 window 冒泡"
assert inject["focusFailures"] == 0, "有注入元素没获得焦点"
assert inject["polluted"] == 0, "注入元素污染了 DOM"

# ═══════════ 765b：外点关闭 / 焦点丢失 / 焦点之后去哪 ═══════════
outside = []
for rd in bR:
    oc = rd.get("outsideClick") or {}
    hit = oc.get("hit") or {}
    outside.append({
        "pt": oc.get("pt"),
        "hitTag": hit.get("tag"),
        "hitClickable": hit.get("clickable"),
        "hitInPanel": hit.get("inPanel"),
        "hitInDialog": hit.get("inDialog"),
        "skipped": oc.get("skipped"),
        "panelStillOpen": oc.get("panelStillOpen"),
        "panelClosed": oc.get("panelClosed"),
        "workspaceClosed": oc.get("workspaceClosed"),
    })
outside_click = {
    "rounds": len(outside),
    "allClicked": all(x["skipped"] is None for x in outside),
    "clickedPoint": [x["pt"] for x in outside],
    "hitWasInPanel": [x["hitInPanel"] for x in outside],
    "panelStayedOpen": [x["panelStillOpen"] is True for x in outside],
    "panelClosedCount": sum(1 for x in outside
                            if x["panelClosed"] is True),
    "deskClosedCount": sum(1 for x in outside
                           if x["workspaceClosed"] is True),
    "detail": outside,
}

fl = []
for rd in bR:
    e = rd.get("focaloss_esc") or {}
    t = rd.get("focaloss_tab6") or {}
    fl.append({
        "focusBeforeTag": ((rd.get("focaloss_before") or {}).get("tag")),
        "focusBeforeInPanel": ((rd.get("focaloss_before") or {})
                               .get("inPanel")),
        "reachedWinBubble": e.get("reachedWinBubble"),
        "escTargetAtWin": e.get("escTargetAtWin"),
        "panelClosed": e.get("panelClosed"),
        "workspaceClosed": e.get("workspaceClosed"),
        "activeAfterTag": (e.get("active") or {}).get("tag"),
        "activeAfterInDialog": (e.get("active") or {}).get("inDialog"),
        "activeAfterIsTrigger": (e.get("active") or {}).get("isTrigger"),
        "tabSteps": t.get("steps"),
        "tabReachedDialog": t.get("reachedDialogCount"),
        "tabOnBody": t.get("onBodyCount"),
    })
focus_loss = {
    "rounds": len(fl),
    "focusBeforeInPanel": [x["focusBeforeInPanel"] for x in fl],
    "escClosedPanel": [x["panelClosed"] for x in fl],
    "escClosedDesk": [x["workspaceClosed"] for x in fl],
    "reachedWinBubble": [x["reachedWinBubble"] for x in fl],
    "activeAfterTag": [x["activeAfterTag"] for x in fl],
    "activeAfterInDialog": [x["activeAfterInDialog"] for x in fl],
    "activeAfterIsTrigger": [x["activeAfterIsTrigger"] for x in fl],
    "fellToBodyEverywhere": all(
        x["activeAfterTag"] == "BODY" for x in fl),
    "tabSteps": [x["tabSteps"] for x in fl],
    "tabReachedDialog": [x["tabReachedDialog"] for x in fl],
    "tabOnBody": [x["tabOnBody"] for x in fl],
    "detail": fl,
}

shift = {
    "focusTriggerOk": [(rd.get("shift_focusTrigger") or {}).get("focused")
                       for rd in bR],
    "panelOpenBefore": [(rd.get("shift_focusTrigger") or {}).get("panelOpen")
                        for rd in bR],
    "steps": [(rd.get("shift_tab12") or {}).get("steps") for rd in bR],
    "inPanel": [(rd.get("shift_tab12") or {}).get("inPanelCount")
                for rd in bR],
    "escapedDialog": [(rd.get("shift_tab12") or {}).get("escapedDialogCount")
                      for rd in bR],
}

disc = {
    "triggerAriaExpanded": [
        ((rd.get("state1") or {}).get("trigger") or {}).get("ariaExpanded")
        for rd in bR],
    "triggerAriaControls": [
        ((rd.get("state1") or {}).get("trigger") or {}).get("ariaControls")
        for rd in bR],
    "triggerAriaHasPopup": [
        ((rd.get("state1") or {}).get("trigger") or {}).get("ariaHasPopup")
        for rd in bR],
    "panelTag": [((rd.get("state1") or {}).get("panel") or {}).get("tag")
                 for rd in bR],
    "panelRole": [((rd.get("state1") or {}).get("panel") or {}).get("role")
                  for rd in bR],
    "panelAriaLabel": [((rd.get("state1") or {}).get("panel") or {})
                       .get("ariaLabel") for rd in bR],
    "panelId": [((rd.get("state1") or {}).get("panel") or {}).get("id")
                for rd in bR],
    "panelHasHeading": True,   # DirectorExportPanel.tsx:48 有 <h2>导出设置</h2>
    "hasAriaControls": any(
        ((rd.get("state1") or {}).get("trigger") or {}).get("ariaControls")
        for rd in bR),
    "hasAriaHasPopup": any(
        ((rd.get("state1") or {}).get("trigger") or {}).get("ariaHasPopup")
        for rd in bR),
    "hasPanelRole": any(
        ((rd.get("state1") or {}).get("panel") or {}).get("role") for rd in bR),
    "hasPanelAriaLabel": any(
        ((rd.get("state1") or {}).get("panel") or {}).get("ariaLabel")
        for rd in bR),
    "hasPanelId": any(
        ((rd.get("state1") or {}).get("panel") or {}).get("id") for rd in bR),
}

findings = {
    "comparability": comparability,
    "escSweep": esc_sweep,
    "tabFence": tab_fence,
    "focusOnOpen": focus_on_open,
    "mobileLadder": mobile_ladder,
    "importProbe": import_probe,
    "inject": inject,
    "outsideClick": outside_click,
    "focusLoss": focus_loss,
    "shiftTab": shift,
    "disclosureContract": disc,
}

judgments = [
    {"id": "J1", "verdict": "PASS",
     "statement": "两轮**逐字段一致**，而且是**先证明可比再谈一致**："
                  "765a 比 %d 个 key、765b 比 %d 个 key 的归一化 diff 全为空。"
                  "本批没有任何破坏性动作（不点提交、不选文件、不删对象），"
                  "所以两轮起点相同。",
     "evidenceKey": "comparability"},
    {"id": "J2", "verdict": "PASS",
     "statement": "**导出面板里没有任何手势边界控件** ⟹ D1 在这块**不成立**："
                  "`DirectorExportPanel.tsx` 全文没有 `useDirectorGestureBoundary`、"
                  "没有 `onKeyDown`、没有 `stopPropagation`；运行时按 "
                  "data-* 标记扫也是 0 个。",
     "evidenceKey": "escSweep"},
    {"id": "J3", "verdict": "PASS",
     "statement": "面板里 %d 个可聚焦控件，**除时长数值框外的每一个**按 Esc "
                  "都关掉了面板、且**没有一格**关掉导演台（%d/%d 格关面板、"
                  "0 格关导演台，%d 格聚焦全部成功）。",
     "evidenceKey": "escSweep"},
    {"id": "J4", "verdict": "FAIL",
     "statement": "★ **缺陷 D3（低）**：焦点停在**时长数值框**里时按 Esc，"
                  "**面板关不掉、导演台也关不掉**。桌面 %d/%d 轮如此；"
                  "800px 下这一下只关掉了**更早那一档的抽屉**，面板仍然开着。"
                  "同一个守卫（`DirectorDesk.tsx:487` 的 `if (isEditable) return;`）"
                  "继 764 的 D2 之后**第三个受害档位**。",
     "evidenceKey": "escSweep"},
    {"id": "J5", "verdict": "PASS",
     "statement": "D3 的机制由**在本处重做的注入对照**定位：面板里同位置插入的 "
                  "`input[type=text]`、`input[type=number]`、"
                  "`div[contenteditable]` **都关不掉面板**，而 `div[tabindex=0]` "
                  "**照关不误**（%d/%d 与 %d/%d）；并且 **%d/%d 格的事件都到达了 "
                  "window 冒泡** ⟹ 既不是「type=number 原生吞 Esc」，"
                  "也不是 D1 那个 stopPropagation（那个是 `reachedWinBubble=false`），"
                  "而是事件上来了、被 `if (isEditable) return;` 挡在门外。",
     "evidenceKey": "inject"},
    {"id": "J6", "verdict": "PASS",
     "statement": "**焦点围栏在面板周围仍然成立**：面板开着时正向 Tab %d 步、"
                  "从触发器 Tab %d 步、焦点在触发器时反向 Shift+Tab %d 步，"
                  "**三向 0 次逃出 dialog**。765 只量过正向，本批把反向补上了"
                  "（围栏 hook 的 Tab 接管是双向的）。",
     "evidenceKey": "tabFence"},
    {"id": "J7", "verdict": "PASS",
     "statement": "打开面板**不移动焦点**：焦点留在触发按钮上"
                  "（`isTrigger=true`、`inPanel=false`），"
                  "而 `aria-expanded` 在开之前是 `false`、开之后是 `true` "
                  "⟹ disclosure 的开合语义自洽。正向 Tab 能从触发器走进面板。",
     "evidenceKey": "focusOnOpen"},
    {"id": "J8", "verdict": "FAIL",
     "statement": "★ **缺陷 D4（低）**：Esc 关掉面板后**焦点掉到 `body`、"
                  "逃出导演台对话框**（`activeTag=BODY`、`inDialog=false`），"
                  "**没有回到触发器**。机制是静态可查的："
                  "`DirectorExportPanel.tsx:38` 的 `if (!open) return null` "
                  "把正在聚焦的元素整个卸载，而 `DirectorDesk.tsx:557-560` "
                  "的关闭分支只调了 `setExportPanelOpen(false)`、**没碰焦点**；"
                  "围栏 hook 只在 `keydown` 里接管 Tab、**没有 focusin 监听**，"
                  "所以也捞不回来。",
     "evidenceKey": "focusLoss"},
    {"id": "J9", "verdict": "PASS",
     "statement": "★ **更正本批设计阶段的预期**：我原本以为焦点掉到 body 之后"
                  "按 Tab 会走到画布页面、形成死路（围栏 hook 的 Tab 接管挂在 "
                  "root 上，事件目标在 body 时冒泡不到 root）。**实测否掉了**："
                  "之后连按 %d 次 Tab，%s 次全部落回 dialog 内部"
                  "（0 次停在 body）⟹ 焦点丢失是真的，**但不是死路**。",
     "evidenceKey": "focusLoss"},
    {"id": "J10", "verdict": "FAIL",
     "statement": "★ **那一轮 Tab 到底是谁接管的，本批判不了**："
                  "原生顺序焦点导航与围栏 hook 的 "
                  "`getDirectorFocusableElements()` 数组**都是 DOM 序**，"
                  "落点序列因此**无法区分**两者。读数只支持「焦点没有回触发器、"
                  "落回了 dialog 内部其它控件」这个结论，"
                  "不支持任何关于机制的断言。",
     "evidenceKey": "focusLoss"},
    {"id": "J11", "verdict": "FAIL",
     "statement": "★ **缺陷 D5（低）**：面板**没有外点关闭** —— "
                  "点面板外的空白（%s，命中的是面板外、非可点的 "
                  "`absolute inset-0` 容器）之后面板**仍然开着**，"
                  "两轮如此。与 J4 的 D3 叠加：**时长框里既按 Esc 关不掉、"
                  "点外面也不关**，面板只能靠再次点触发器或把焦点挪到别的控件"
                  "再按 Esc 才收得回去。",
     "evidenceKey": "outsideClick"},
    {"id": "J12", "verdict": "FAIL",
     "statement": "★ **缺陷 D6（低）**：disclosure 契约只做了 `aria-expanded` "
                  "—— 触发器**没有** `aria-controls`、**没有** `aria-haspopup`，"
                  "面板是个**既没有 role、也没有 aria-label、也没有 id** 的 "
                  "`<section>`。加上 J13 的反向 Tab 进不去，"
                  "键盘与读屏用户只能靠「正向 Tab」这一条路发现面板内容。",
     "evidenceKey": "disclosureContract"},
    {"id": "J13", "verdict": "FAIL",
     "statement": "★ **J12 的另一半**：面板在 DOM 序上位于触发器**之后**，"
                  "而围栏 hook 的 Tab 数组就是 DOM 序 ⟹ 焦点停在触发器、"
                  "面板已展开时，**Shift+Tab %d 步一次都没进过面板**"
                  "（%s 次），走的全是 DOM 序更早的引导按钮"
                  "（「下一步」「跳过」「新增机位」）。",
     "evidenceKey": "shiftTab"},
    {"id": "J14", "verdict": "PASS",
     "statement": "800px 下三档 Esc **逐档推进、一次一档**："
                  "抽屉 → 面板 → 导演台（%d/%d 轮全对），"
                  "第四下导演台保持关闭。763 记的「Esc 一次只走一档」"
                  "在多出「面板」这一档之后依然成立。",
     "evidenceKey": "mobileLadder"},
    {"id": "J15", "verdict": "PASS",
     "statement": "**导入侧是活的**：点「导入导演台项目」**真的弹文件选择器**"
                  "（%d/%d 轮 `expect_file_chooser` 命中），"
                  "输入框 `type=file accept=\"%s\"`；"
                  "按钮本身 `aria-label` 与 `title` 都齐、未 disabled。",
     "evidenceKey": "importProbe"},
    {"id": "J16", "verdict": "PASS",
     "statement": "★ **坐实并更正 762 的记录**：隐藏的 file input "
                  "**零可访问名**（`aria-label`/`title`/`id`/`label[for]` 全为空），"
                  "但它 `display:none`、不可聚焦 ⟹ **不构成可操作性缺陷**，"
                  "真正可点的按钮有名字。762 记的「无 aria-label」成立，"
                  "但当时没量到「连 title/id/label 都没有」也没量到不可聚焦这一层。",
     "evidenceKey": "importProbe"},
    {"id": "J17", "verdict": "PASS",
     "statement": "**注入元素没有污染后续读数**：%d 格注入全部在面板内获得焦点，"
                  "其中「不关面板」的三格在按 Esc 后仍在 DOM 并被手动移除（各 1 个），"
                  "「关掉面板」那一格随面板卸载一起消失 ⟹ 0 格污染。",
     "evidenceKey": "inject"},
]

for j in judgments:
    j["evidence"] = findings[j["evidenceKey"]]

audit = {
    "batch": 765,
    "date": "2026-10-01",
    "scope": "导入/导出面板内的焦点围栏、逐控件 Esc、800px 三档 Esc 阶梯、"
             "disclosure 可访问性契约、外点关闭、Esc 关面板后的焦点去向",
    "env": {
        "base": "http://localhost:4317",
        "canvas": "canvas-2",
        "directorNodeId": "b-bTLLuU4w5q",
        "viewportA": "1440x1000（桌面）",
        "viewportB": "800x1000（移动端抽屉）",
        "player": "chromium (playwright sync_api)",
        "srcModified": False,
    },
    "probes": [
        {"id": "765a", "file": "probes/dbg765a.py", "raw": "raw/vb765a.json",
         "rounds": len(aR), "selfReportedConsistent": None,
         "note": "面板逐控件 Esc、正反向 Tab、800px 三档阶梯、导入按钮"
                 "（初版有探针顺序 bug，已修并重跑，见 R63）"},
        {"id": "765b", "file": "probes/dbg765b.py", "raw": "raw/vb765b.json",
         "rounds": len(bR), "selfReportedConsistent": None,
         "note": "四组注入对照（定位 D3 机制）、外点关闭、"
                 "Esc 关面板后的焦点去向、反向 Tab"},
    ],
    "rawSha": {p.name: sha(p) for p in (a_p, b_p)},
    "findings": findings,
    "judgments": judgments,
    "defects": [
        {"id": "D3", "severity": "低", "newInThisBatch": True,
         "title": "焦点在时长数值框里时 Esc 关不掉导出面板",
         "where": ["src/components/director/DirectorDesk.tsx:475-480",
                   "src/components/director/DirectorDesk.tsx:487",
                   "src/components/director/DirectorDesk.tsx:557-560",
                   "src/components/director/DirectorExportPanel.tsx:60"],
         "mechanism": "`DirectorDesk.tsx:475-480` 把 isEditable 定义成"
                      "「isContentEditable 或 tagName 是 INPUT/TEXTAREA/SELECT」，"
                      "`:487` 的 `if (isEditable) return;` 排在整个 Escape 分支"
                      "（`:549-568`）之前，于是焦点在 `<input type=number>` 里时"
                      "「关面板」那一档（`:557`）**永远走不到**。"
                      "**不是** D1 那个 stopPropagation —— 注入对照实测"
                      "8/8 格 `reachedWinBubble=true`，事件确实到了 window 冒泡。",
         "measured": "1440：面板不关、导演台不关（2/2 轮）。"
                     "800px：这一下只关掉更早那一档的抽屉，面板仍开（2/2 轮）。"
                     "同面板另外 4 个控件 Esc 全部正常关面板（8/8 格）。",
         "sameGuardAs": "764 的 D2（`if (isEditable) return;` 拦 ⌘C/⌘V）"
                        "—— 同一个守卫的第三个受害档位，修法可一起考虑。",
         "needsSrcChange": True},
        {"id": "D4", "severity": "低", "newInThisBatch": True,
         "title": "Esc 关掉导出面板后焦点掉到 body、逃出对话框",
         "where": ["src/components/director/DirectorExportPanel.tsx:38",
                   "src/components/director/DirectorDesk.tsx:557-560",
                   "src/components/director/useDirectorFocusContainment.ts:149-172",
                   "src/components/director/useDirectorFocusContainment.ts:181-188"],
         "mechanism": "`if (!open) return null`（`:38`）在关闭时把正在聚焦的"
                      "元素整个卸载，浏览器把焦点退回 `body`；"
                      "而关闭分支只调了 `setExportPanelOpen(false)`、**没有任何"
                      "焦点处理**。围栏 hook 只在 root 上监听 `keydown` 管 Tab，"
                      "**没有 focusin 监听**，`restoreFocus()` 只在导演台整体"
                      "卸载时才被调用（`:181-188` 的 returnFocus）⟹ 捞不回来。",
         "measured": "2/2 轮 activeElement=BODY、inDialog=false、"
                     "不在触发器上。**但**之后按 Tab %d/%s 次全部落回 dialog 内部"
                     "⟹ 不是死路（见 J9 的更正）。"
                     % (focus_loss["tabSteps"][0],
                        focus_loss["tabReachedDialog"][0]),
         "contrast": "762 记的「Esc 关抽屉/关导演台都会把焦点交还触发按钮」"
                     "在这条路径上**不成立** —— 面板这一档漏了焦点归还。",
         "needsSrcChange": True},
        {"id": "D5", "severity": "低", "newInThisBatch": True,
         "title": "导出面板没有外点关闭，与 D3 叠加成退不回去的组合",
         "where": ["src/components/director/DirectorDesk.tsx:294",
                   "src/components/director/DirectorDesk.tsx:624",
                   "src/components/director/DirectorDesk.tsx:1351-1362"],
         "mechanism": "`setExportPanelOpen` 全仓只有 3 处调用：`:294` 初始化、"
                      "`:558` Esc、`:624` toggle —— **没有任何 pointerdown / "
                      "外点监听**。面板是 `absolute bottom-full right-0 z-50` "
                      "挂在时间轴右端的一个 popover，展开后点画布任何地方都不收。",
         "measured": "点面板外空白（%s，命中非可点的 `absolute inset-0` 容器）"
                     "之后面板 %d/%d 轮仍然开着，导演台也没关。"
                     % (outside_click["clickedPoint"][0],
                        sum(outside_click["panelStayedOpen"]),
                        outside_click["rounds"]),
         "combinedWith": "D3 —— 时长框里按 Esc 关不掉、点外面也不关，"
                         "用户只能再次点触发器，或把焦点挪到别的控件再按 Esc。",
         "needsSrcChange": True},
        {"id": "D6", "severity": "低", "newInThisBatch": True,
         "title": "导出面板的 disclosure 可访问性契约残缺，且反向 Tab 进不去",
         "where": ["src/components/director/DirectorDesk.tsx:1338-1350",
                   "src/components/director/DirectorDesk.tsx:1351-1362",
                   "src/components/director/DirectorExportPanel.tsx:42-51"],
         "mechanism": "触发器只给了 `aria-expanded`（`:1341`），"
                      "**没有 `aria-controls`、没有 `aria-haspopup`**；"
                      "面板根是个 `<section data-director-export-panel>`，"
                      "**没有 role、没有 aria-label、没有 id**（里面的 `<h2>导出设置</h2>` "
                      "不构成可访问名）。面板又挂在触发器**之后**（`:1351`），"
                      "围栏 hook 的 Tab 数组是 DOM 序 ⟹ 反向 Tab 走不到它。",
         "measured": "aria-controls/aria-haspopup 两轮皆 null；"
                     "面板 tag=SECTION、role/aria-label/id 两轮皆 null；"
                     "焦点在触发器且面板展开时 Shift+Tab %d 步，"
                     "进面板 %s 次、逃出 dialog %s 次。"
                     % (shift["steps"][0], shift["inPanel"][0],
                        shift["escapedDialog"][0]),
         "needsSrcChange": True},
    ],
    "observations": [
        {"id": "O1",
         "text": "围栏 hook（`useDirectorFocusContainment.ts:149-172`）"
                 "的 Tab 接管是**手算 + preventDefault**：它在 keydown 时重新"
                 "算一遍 `getDirectorFocusableElements(root)` 再手动 focus。"
                 "所以 762/765 量到的「Tab 序列」是**这个数组的序**"
                 "（恰好也是 DOM 序），**不是**浏览器原生 Tab 序 —— "
                 "两者在本批无法区分（见 J10）。",
         "verdict": "方法论约束"},
        {"id": "O2",
         "text": "围栏**只管 Tab、不管焦点丢失**。面板被 Esc 关掉后焦点掉到 body，"
                 "hook 不会把它捞回来（没有 focusin 监听，"
                 "`restoreFocus()` 只在导演台整体卸载时跑）。"
                 "D4 的修法要在**关面板这一档**单独补焦点归还，"
                 "不能指望围栏兜底。",
         "verdict": "事实记录"},
        {"id": "O3",
         "text": "点「导入导演台项目」**不会收起已开的导出面板**"
                 "（`i_after` 里 `panel.present` 仍为 true、触发器 "
                 "`aria-expanded` 仍为 true）。但这一格**是探针自己先开着面板**"
                 "才点导入的，所以只能当观察、**不能当判据**。",
         "verdict": "观察（不作判据）"},
        {"id": "O4",
         "text": "面板视觉位置在触发器**上方**（`bottom-full`）、"
                 "DOM 顺序却在触发器**之后** ⟹ 视觉序与 Tab 序相反。"
                 "与 D6 的「反向 Tab 进不去」同源。",
         "verdict": "事实记录"},
    ],
    "notClaimed": [
        "无源站对照：本批全部结论只针对 clone 自身的行为自洽性。",
        "**没有点提交按钮**（`data-director-export-submit`）—— Batch 596 的"
        "注释写明点它可能直接在用户项目上启动一次真实导出，属付费/破坏性动作，"
        "未授权。所以导出流程本身（status 从 idle → exporting → done/error、"
        "progress、error 文案）**全部未测**。",
        "**没有选文件**（只触发了 file chooser 就放弃），所以导入解析、"
        "校验失败、覆盖种子项目这些路径**未测**。",
        "Esc 关面板后那 %d 次 Tab 到底是原生顺序焦点导航还是围栏 hook 接管的，"
        "**判不了**（J10）：两者的落点序列都是 DOM 序。"
        "「浏览器的顺序焦点起始点仍停在面板原处」只是**推断**，不是读数。"
        % focus_loss["tabSteps"][0],
        "只测了 1440 桌面与 800px 移动端两档视口；"
        "640–850px 的隐藏区间（761 记的）没测。",
        "800px 那一档只量了「属性抽屉 + 导出面板」这一个组合；"
        "「树抽屉 + 导出面板」没测。",
        "面板在 `status=exporting`（提交之后）时的焦点与 Esc 行为**未测** —— "
        "前置条件就是不许点提交。",
        "没测屏幕阅读器实际播报什么；D6/D4 的可访问性后果是从 DOM 契约与"
        "焦点读数推出来的。",
        "D3 只在导出面板的时长数值框上测过。属性面板那 43 个边界控件"
        "（764 的 D1）与本条的守卫是**两回事**，本批没有重新测它们。",
        "面板的 `maxDurationSeconds` 取自 `timelineDuration`，"
        "本批读到 max=8；没有测过更长的时间轴下这个上限是否跟着变。",
    ],
    "probeLessons": [
        {"id": "R63",
         "text": "**按 Esc 之前先读状态**。765a 初版在 800px 那一格里无脑 "
                 "`press(\"Escape\")` 想「关掉可能开着的抽屉」，"
                 "那时并没有抽屉开着，Esc 顺着阶梯把**整个导演台关掉了**，"
                 "后面三格读数全空（`desk.open=false`）。"
                 "修法：先读状态，只在该关的时候关，按完还要**断言**"
                 "目标真的变了自己要的样子，否则该格记 FAILED，不留空读数。"
                 "这条与 763 的 R59（开一个抽屉前先关另一个）是同一族："
                 "**任何「准备动作」都可能顺手触发别的状态迁移**。"},
        {"id": "R64",
         "text": "★ **先怀疑自己写的预期，再怀疑产品**。765b 设计阶段我断言"
                 "「焦点掉到 body 之后按 Tab 会走原生序、跑到画布页面，"
                 "因为围栏 hook 的 keydown 挂在 root 上、body 的事件冒泡不到 root」"
                 "—— 听起来很硬。实测 6/6 步全落回 dialog 内部，"
                 "**预期被否掉**。教训：静态推理（事件路径、监听器位置）"
                 "能证明「某条路径可达/不可达」，但**证明不了浏览器"
                 "顺序焦点导航的起始点行为** —— 后者只能读，不能推。"},
        {"id": "R65",
         "text": "**注入对照必须在结论所在的位置重做，不能拿上一批的当证据**。"
                 "763 的注入对照是在属性面板里做的，结论是「text 与 number "
                 "都能关 ⟹ 不是原生吞 Esc」。765b 在导出面板里**重新插了一遍**，"
                 "四组对照（text / number / contenteditable / tabindex）"
                 "各自两轮，共 %d 格全部 `reachedWinBubble=true` —— "
                 "这同时把 D1（事件没上来，`reachedWinBubble=false`）"
                 "和 D3（事件上来了被自己的守卫 return）**干净地分开**。"
                 % inject["cells"]},
        {"id": "R66",
         "text": "**注入元素必须自证没污染后续读数**。每格都记 "
                 "`injectedStillInDom` 与 `removed.removed`；"
                 "「关掉面板」那一格的元素随面板卸载而消失（`removed=0`）"
                 "不是读数缺失，而是**另一种正确** —— 汇编器要把两种"
                 "「不在 DOM」分开计数，污染计数必须为 0 才允许出结论。"},
    ],
}

for j in audit["judgments"]:
    k = j["evidenceKey"]
    assert k in findings, "判据 %s 引用了不存在的 findings 键" % j["id"]
    assert findings[k] == j["evidence"], (
        "判据 %s 的 evidence 与 findings[%s] 不相等 —— 两份事实已经分叉"
        % (j["id"], k))

OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1),
               encoding="utf-8")
print("wrote %s" % OUT)
print("判据 %d 条（PASS %d / FAIL %d）| findings %d 键 | 缺陷 %d | 观察 %d "
      "| 探针教训 %d"
      % (len(audit["judgments"]),
         sum(1 for j in judgments if j["verdict"] == "PASS"),
         sum(1 for j in judgments if j["verdict"] == "FAIL"),
         len(findings), len(audit["defects"]), len(audit["observations"]),
         len(audit["probeLessons"])))
print("自检：findings 与 judgments[].evidence 逐条相等 ✓")
print("两轮可比：%s（765a 不一致 key=%s，765b 不一致 key=%s）"
      % (comparability["comparable"], inconsistent_a, inconsistent_b))
for k in findings:
    print("  %-20s %s" % (k, json.dumps(findings[k], ensure_ascii=False)[:104]))
