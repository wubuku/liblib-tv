"""batch 765 验收器：导入/导出面板内的焦点围栏 + disclosure 契约 + Esc 关面板后的焦点

三层结构（与 753–764 同）：
  1. **静态层** —— 从 `src/` 复核判据依赖的实现事实，含**顺序**断言
     （`if (isEditable) return;` 必须排在 Escape 分支与「关面板」那一档之前；
      移动端关抽屉那一档排在它之前；面板必须挂在触发器**之后**；
      关面板那一档里**不许**出现任何焦点处理）
  2. **产物层** —— 判据条数与 verdict、缺陷、观察、教训、README 结构、
     台账行、表格首格不许裸数字
  3. **原始读数交叉核对** —— 从 `raw/` 的 2 份原始输出**按正确键名重算**
     全部派生量；缺失时**判失败而不是通过**

⚠ 本批盯住三件容易自欺的事：
  - **6 条 FAIL 里有 4 条是缺陷**（D3/D4/D5/D6）、1 条是不声称（J10）。
    产物必须**如实**保留这些 FAIL，不许改成 PASS、不许把缺陷降级成观察。
  - **`all([])` 是 True**：读错键名拿到空列表会静默通过。所以每一处聚合
    都显式判非空，阴性对照里有一组专打「把 rows 清空」。
  - **注入对照的 `reachedWinBubble` 是本批的判别点**：D1 是 `false`
    （事件没上来），D3 是 `true`（事件上来了被自己的守卫 return）。
    验收器不许采信探针自报的派生字段，一律从原始格子重算。

判据 **17 条（11 PASS / 6 FAIL）**。
"""
import copy
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch765-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAWDIR = OUTDIR / "raw"
PROBEDIR = OUTDIR / "probes"
README = OUTDIR / "README.md"
LEDGER = ROOT / "docs/research/VERIFICATION_LEDGER.md"

RAW_FILES = ["vb765a.json", "vb765b.json"]
PROBE_FILES = ["dbg765a.py", "dbg765b.py", "mk765audit.py"]
BARE_NUM_CELL = re.compile(r"^\|\s*\d+[a-z]?\s*\|")
FFFD = "\ufffd"

EXPECT_FAIL_IDS = ["J4", "J8", "J10", "J11", "J12", "J13"]
EXPECT_DEFECT_IDS = ["D3", "D4", "D5", "D6"]
EXPECT_LESSON_IDS = ["R63", "R64", "R65", "R66"]


def src(p):
    return (ROOT / p).read_text(encoding="utf-8")


def ptr_valid(w):
    """`src/foo.tsx:123` 形式的指针：文件存在且行号在范围内。"""
    m = re.match(r"^(.+?):(\d+)(?:-(\d+))?$", w or "")
    if not m:
        return False
    f = ROOT / m.group(1)
    if not f.exists():
        return False
    n = len(f.read_text(encoding="utf-8").splitlines())
    hi = int(m.group(3) or m.group(2))
    return 1 <= m.group(2).isdigit() and int(m.group(2)) <= n and hi <= n


def idx_of(text, needle, start=0):
    """needle 第一次出现的**字符下标**；找不到返回 -1。切片用这个。"""
    return text.find(needle, start)


def line_of(text, needle, start=0):
    """needle 第一次出现的 0 基**行号**；找不到返回 -1。只用于报告。"""
    i = idx_of(text, needle, start)
    if i < 0:
        return -1
    return text.count("\n", 0, i)


# ═════════════════════ 1. 静态层 ═════════════════════
def static_side():
    desk = src("src/components/director/DirectorDesk.tsx")
    panel = src("src/components/director/DirectorExportPanel.tsx")
    fence = src("src/components/director/useDirectorFocusContainment.ts")

    d_editable = line_of(desk, "if (isEditable) return;")
    d_drawer = line_of(desk, 'event.key === "Escape" && activeMobilePanel')
    d_escgate = line_of(desk, 'if (event.key !== "Escape") return;')
    d_panel = line_of(desk, "if (exportPanelOpen) {")
    d_trig = line_of(desk, "data-director-export-trigger")
    d_mount = line_of(desk, "<DirectorExportPanel")
    d_set_calls = len(re.findall(r"setExportPanelOpen", desk))
    # 关面板那一档的函数体：取出到下一档之间，断言里面没有焦点处理
    i_panel = idx_of(desk, "if (exportPanelOpen) {")
    seg = desk[i_panel:idx_of(desk, "if (followTargetId)", i_panel)]
    d_focus_in_close = bool(re.search(r"\.focus\(|restoreFocus", seg))

    p_null = line_of(panel, "if (!open) return null;")
    i_root = idx_of(panel, "<section")
    p_root_seg = panel[i_root:idx_of(panel, ">", i_root)] if i_root >= 0 else ""
    p_root = i_root
    p_boundary = bool(re.search(r"useDirectorGestureBoundary", panel))
    p_keydown = bool(re.search(r"onKeyDown", panel))
    p_stopprop = bool(re.search(r"stopPropagation", panel))
    p_has_role = bool(re.search(r"\brole=", p_root_seg))
    p_has_aria = bool(re.search(r"aria-label=", p_root_seg))
    p_has_id = bool(re.search(r"\bid=", p_root_seg))
    p_h2 = line_of(panel, "<h2")
    p_duration = line_of(panel, "data-director-export-duration")

    i_trig = idx_of(desk, "data-director-export-trigger")
    i_btn_end = idx_of(desk, "</button>", i_trig)
    trig_seg = desk[i_trig:i_btn_end] if i_trig >= 0 else ""
    t_aria_expanded = "aria-expanded" in trig_seg
    t_aria_controls = "aria-controls" in trig_seg
    t_aria_haspopup = "aria-haspopup" in trig_seg

    f_keydown = bool(re.search(r'addEventListener\("keydown"', fence))
    f_focusin = bool(re.search(r'addEventListener\("focusin"', fence))
    f_focusout = bool(re.search(r'addEventListener\("focusout"', fence))
    f_restore_calls = len(re.findall(r"restoreFocus\(\)", fence))
    f_prevent = "event.preventDefault();" in fence
    f_ragged = 'querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)' in fence

    return {
        "editableEarlyReturnLine": d_editable,
        "mobileDrawerLine": d_drawer,
        "escGateLine": d_escgate,
        "exportPanelLine": d_panel,
        "editableBeforeEscGate": 0 <= d_editable < d_escgate,
        "editableBeforeExportPanel": 0 <= d_editable < d_panel,
        "mobileDrawerBeforeEditable": 0 <= d_drawer < d_editable,
        "escGateBeforeExportPanel": 0 <= d_escgate < d_panel,
        "setExportPanelCallCount": d_set_calls,
        "noFocusHandlingInPanelClose": not d_focus_in_close,
        "panelMountedAfterTrigger": 0 <= d_trig < d_mount,
        "triggerAriaExpanded": t_aria_expanded,
        "triggerAriaControls": t_aria_controls,
        "triggerAriaHasPopup": t_aria_haspopup,
        "panelNullGateLine": p_null,
        "panelRootTag": re.search(r"<(\w+)", p_root_seg).group(1)
        if p_root_seg else None,
        "panelRootHasRole": p_has_role,
        "panelRootHasAriaLabel": p_has_aria,
        "panelRootHasId": p_has_id,
        "panelHasGestureBoundary": p_boundary,
        "panelHasOnKeyDown": p_keydown,
        "panelHasStopPropagation": p_stopprop,
        "panelHasH2": 0 <= p_h2,
        "panelDurationLine": p_duration,
        "fenceKeydownListener": f_keydown,
        "fenceFocusinListener": f_focusin,
        "fenceFocusoutListener": f_focusout,
        "fenceRestoreCallCount": f_restore_calls,
        "fencePreventsDefault": f_prevent,
        "fenceArrayIsDomOrder": f_ragged,
    }


# ═════════════════════ 3. 原始读数交叉核对 ═════════════════════
def raw_files():
    out = {}
    for f in RAW_FILES:
        p = RAWDIR / f
        if not p.exists():
            raise SystemExit("FATAL 缺原始读数 %s" % p)
        out[f] = json.loads(p.read_text(encoding="utf-8"))
    return out


def raw_side():
    """重算后的派生量 + `__raw__` 挂一份原始读数（阴性对照要改真正的被检查键）。"""
    files = raw_files()
    out = raw_side_from(files)
    out["__raw__"] = files
    return out


def raw_side_from(rw):
    """从原始读数**按正确键名重算**全部派生量。空列表必须显式判失败。"""
    a = rw["vb765a.json"]
    b = rw["vb765b.json"]
    r = {}

    # —— 765a 逐控件 Esc
    rows = [x for rd in a["rounds"]
            for x in ((rd.get("d_sweep") or {}).get("rows") or [])]
    r["sweepCells"] = len(rows)
    r["sweepClosed"] = sum(1 for x in rows if x.get("panelClosed") is True)
    r["sweepNotClosed"] = sum(1 for x in rows
                              if x.get("panelClosed") is False)
    r["sweepNotClosedMarkers"] = sorted({
        (x.get("item") or {}).get("marker") for x in rows
        if x.get("panelClosed") is False})
    r["sweepNotClosedIsDurationOnly"] = (
        r["sweepNotClosed"] > 0
        and r["sweepNotClosedMarkers"] == ["duration"])
    r["sweepDeskClosed"] = sum(1 for x in rows
                               if x.get("workspaceClosed") is True)
    r["sweepFocusFailures"] = sum(
        1 for x in rows
        if (x.get("focus") or {}).get("focused") is not True
        or x.get("focusedInPanel") is not True)
    r["sweepAllClosedSelfReported"] = [
        (rd.get("d_sweep") or {}).get("allClosed") for rd in a["rounds"]]
    r["panelFocusables"] = [
        (rd.get("d_sweep") or {}).get("panelFocusables") for rd in a["rounds"]]

    # —— Tab 围栏（三向）
    r["tabEscapedForwardPanel"] = [
        (rd.get("d_tabFromPanel") or {}).get("escapedCount")
        for rd in a["rounds"]]
    r["tabEscapedForwardTrigger"] = [
        (rd.get("d_tabFromTrigger") or {}).get("escapedCount")
        for rd in a["rounds"]]
    r["tabStepsForward"] = [
        (rd.get("d_tabFromPanel") or {}).get("steps") for rd in a["rounds"]]
    r["tabInPanelFromTrigger"] = [
        (rd.get("d_tabFromTrigger") or {}).get("inPanelCount")
        for rd in a["rounds"]]
    r["shiftSteps"] = [(rd.get("shift_tab12") or {}).get("steps")
                       for rd in b["rounds"]]
    r["shiftInPanel"] = [(rd.get("shift_tab12") or {}).get("inPanelCount")
                         for rd in b["rounds"]]
    r["shiftEscaped"] = [(rd.get("shift_tab12") or {})
                         .get("escapedDialogCount") for rd in b["rounds"]]

    # —— 打开瞬间焦点
    r["focusOnOpenIsTrigger"] = [
        (rd.get("d_focusOnOpen") or {}).get("isTrigger") for rd in a["rounds"]]
    r["focusOnOpenInPanel"] = [
        (rd.get("d_focusOnOpen") or {}).get("inPanel") for rd in a["rounds"]]
    r["ariaExpandedBefore"] = [
        ((rd.get("d_before") or {}).get("trigger") or {}).get("ariaExpanded")
        for rd in a["rounds"]]
    r["ariaExpandedAfter"] = [
        ((rd.get("d_state") or {}).get("trigger") or {}).get("ariaExpanded")
        for rd in a["rounds"]]

    # —— 800px 三档阶梯
    LAD = ("m_escFromDuration", "m_escFromAspect", "m_escNext", "m_escNext2")
    tiers = [[rd.get(k) for k in LAD] for rd in a["rounds"]]
    r["tierCount"] = sum(len(t) for t in tiers)
    r["tier1ClosedDrawerOnly"] = sum(
        1 for t in tiers if t[0] and t[0]["panelClosed"] is False
        and t[0]["drawerState"] == "closed"
        and t[0]["workspaceClosed"] is False)
    r["tier2ClosedPanelNotDesk"] = sum(
        1 for t in tiers if t[1] and t[1]["panelClosed"] is True
        and t[1]["workspaceClosed"] is False)
    r["tier3ClosedDesk"] = sum(
        1 for t in tiers if t[2] and t[2]["panelClosed"] is True
        and t[2]["workspaceClosed"] is True)
    r["roundsWithLadder"] = sum(
        1 for t in tiers if t[0] and t[1] and t[2] and t[3])
    r["durationEscLeftPanelOpen"] = sum(
        1 for t in tiers if t[0] and t[0]["panelClosed"] is False)
    r["panelOpenAt800"] = [
        ((rd.get("m_state") or {}).get("panel") or {}).get("present")
        for rd in a["rounds"]]

    # —— 导入侧
    r["fileChooserFired"] = [
        (rd.get("i_fileChooser") or {}).get("fired") for rd in a["rounds"]]
    r["hiddenInputName"] = [
        (rd.get("i_inputName") or {}).get("accessibleNameGuess")
        for rd in a["rounds"]]
    r["hiddenInputAria"] = [
        (rd.get("i_inputName") or {}).get("ariaLabel") for rd in a["rounds"]]
    r["hiddenInputTitle"] = [
        (rd.get("i_inputName") or {}).get("title") for rd in a["rounds"]]
    r["hiddenInputId"] = [
        (rd.get("i_inputName") or {}).get("id") for rd in a["rounds"]]
    r["hiddenInputHasLabelFor"] = [
        (rd.get("i_inputName") or {}).get("hasLabelFor")
        for rd in a["rounds"]]
    r["hiddenInputDisplay"] = [
        ((rd.get("i_probe") or {}).get("inputFocusable") or {}).get("display")
        for rd in a["rounds"]]
    r["importBtnAria"] = [
        ((rd.get("i_probe") or {}).get("btn") or {}).get("ariaLabel")
        for rd in a["rounds"]]
    r["importBtnDisabled"] = [
        ((rd.get("i_probe") or {}).get("btn") or {}).get("disabled")
        for rd in a["rounds"]]
    r["importAccept"] = [
        ((rd.get("i_probe") or {}).get("input") or {}).get("accept")
        for rd in a["rounds"]]

    # —— 注入对照（本批的判别点）
    INJ = [("inj_text", False), ("inj_number", False),
           ("inj_ce", False), ("inj_tabindex", True)]
    cells = []
    for key, exp in INJ:
        for i, rd in enumerate(b["rounds"], 1):
            v = rd.get(key)
            if not isinstance(v, dict) or v.get("FAILED"):
                cells.append({"key": key, "round": i, "FAILED": True})
                continue
            cells.append({
                "key": key, "round": i, "expect": exp,
                "focused": (v.get("inject") or {}).get("focused"),
                "insidePanel": v.get("focusInPanelBefore"),
                "bubble": v.get("reachedWinBubble"),
                "capture": v.get("reachedWinCapture"),
                "closed": v.get("panelClosed"),
                "desk": v.get("workspaceClosed"),
                "stillInDom": v.get("injectedStillInDom"),
                "removed": (v.get("removed") or {}).get("removed"),
            })
    r["injCells"] = len(cells)
    r["injFailed"] = sum(1 for c in cells if c.get("FAILED"))
    good = [c for c in cells if not c.get("FAILED")]
    r["injFocusFailures"] = sum(1 for c in good
                                if c.get("focused") is not True)
    r["injOutsidePanel"] = sum(1 for c in good
                               if c.get("insidePanel") is not True)
    r["injBubbleTrue"] = sum(1 for c in good if c.get("bubble") is True)
    r["injCaptureTrue"] = sum(1 for c in good if c.get("capture") is True)
    r["injEditableCells"] = sum(1 for c in good if c.get("expect") is False)
    r["injEditableNotClosed"] = sum(
        1 for c in good
        if c.get("expect") is False and c.get("closed") is False)
    r["injNonEditableCells"] = sum(1 for c in good if c.get("expect") is True)
    r["injNonEditableClosed"] = sum(
        1 for c in good
        if c.get("expect") is True and c.get("closed") is True)
    r["injDeskClosed"] = sum(1 for c in good if c.get("desk") is True)
    r["injPolluted"] = sum(
        1 for c in good
        if c.get("stillInDom") is True and c.get("removed") == 0)

    # —— 外点关闭
    r["outsideAllClicked"] = [
        (rd.get("outsideClick") or {}).get("skipped") is None
        for rd in b["rounds"]]
    r["outsidePanelStillOpen"] = [
        (rd.get("outsideClick") or {}).get("panelStillOpen")
        for rd in b["rounds"]]
    r["outsideHitInPanel"] = [
        ((rd.get("outsideClick") or {}).get("hit") or {}).get("inPanel")
        for rd in b["rounds"]]
    r["outsideHitClickable"] = [
        ((rd.get("outsideClick") or {}).get("hit") or {}).get("clickable")
        for rd in b["rounds"]]
    r["outsideDeskClosed"] = [
        (rd.get("outsideClick") or {}).get("workspaceClosed")
        for rd in b["rounds"]]

    # —— 焦点丢失
    r["flBeforeInPanel"] = [
        (rd.get("focaloss_before") or {}).get("inPanel")
        for rd in b["rounds"]]
    r["flActiveTag"] = [
        ((rd.get("focaloss_esc") or {}).get("active") or {}).get("tag")
        for rd in b["rounds"]]
    r["flActiveInDialog"] = [
        ((rd.get("focaloss_esc") or {}).get("active") or {}).get("inDialog")
        for rd in b["rounds"]]
    r["flActiveIsTrigger"] = [
        ((rd.get("focaloss_esc") or {}).get("active") or {}).get("isTrigger")
        for rd in b["rounds"]]
    r["flClosedPanel"] = [
        (rd.get("focaloss_esc") or {}).get("panelClosed")
        for rd in b["rounds"]]
    r["flClosedDesk"] = [
        (rd.get("focaloss_esc") or {}).get("workspaceClosed")
        for rd in b["rounds"]]
    r["flBubble"] = [
        (rd.get("focaloss_esc") or {}).get("reachedWinBubble")
        for rd in b["rounds"]]
    r["flTabSteps"] = [
        (rd.get("focaloss_tab6") or {}).get("steps") for rd in b["rounds"]]
    r["flTabReachedDialog"] = [
        (rd.get("focaloss_tab6") or {}).get("reachedDialogCount")
        for rd in b["rounds"]]
    r["flTabSeqLen"] = [
        len((rd.get("focaloss_tab6") or {}).get("seq") or [])
        for rd in b["rounds"]]

    # —— disclosure 契约
    r["trigAriaExpanded"] = [
        ((rd.get("state1") or {}).get("trigger") or {}).get("ariaExpanded")
        for rd in b["rounds"]]
    r["trigAriaControls"] = [
        ((rd.get("state1") or {}).get("trigger") or {}).get("ariaControls")
        for rd in b["rounds"]]
    r["trigAriaHasPopup"] = [
        ((rd.get("state1") or {}).get("trigger") or {}).get("ariaHasPopup")
        for rd in b["rounds"]]
    r["panelTag"] = [((rd.get("state1") or {}).get("panel") or {}).get("tag")
                     for rd in b["rounds"]]
    r["panelRole"] = [((rd.get("state1") or {}).get("panel") or {}).get("role")
                      for rd in b["rounds"]]
    r["panelAriaLabel"] = [
        ((rd.get("state1") or {}).get("panel") or {}).get("ariaLabel")
        for rd in b["rounds"]]
    r["panelId"] = [((rd.get("state1") or {}).get("panel") or {}).get("id")
                    for rd in b["rounds"]]
    r["shiftFocusOk"] = [
        (rd.get("shift_focusTrigger") or {}).get("focused")
        for rd in b["rounds"]]
    r["shiftPanelOpenBefore"] = [
        (rd.get("shift_focusTrigger") or {}).get("panelOpen")
        for rd in b["rounds"]]
    return r


# ═════════════════════ 2. 产物层 + 交叉核对 ═════════════════════
def run_checks(a, st, rw):
    ck = []

    def C(label, cond, got=None):
        ck.append({"label": label, "pass": bool(cond), "got": got})

    f = a["findings"]
    J = a["judgments"]

    def df(did):
        """按 id 安全取缺陷；取不到返回空字典（阴性对照会删缺陷，索引会炸）。"""
        for x in a.get("defects") or []:
            if x.get("id") == did:
                return x
        return {}

    rounds = len(rw["__raw__"]["vb765a.json"]["rounds"])
    roundsB = len(rw["__raw__"]["vb765b.json"]["rounds"])

    # ── 静态层
    C("静态：isEditable 早退排在 Escape 分支之前", st["editableBeforeEscGate"],
      st["editableEarlyReturnLine"])
    C("静态：isEditable 早退排在「关导出面板」那一档之前",
      st["editableBeforeExportPanel"],
      [st["editableEarlyReturnLine"], st["exportPanelLine"]])
    C("静态：移动端关抽屉那一档排在 isEditable 早退之前",
      st["mobileDrawerBeforeEditable"],
      [st["mobileDrawerLine"], st["editableEarlyReturnLine"]])
    C("静态：Escape 分支的入口排在「关导出面板」那一档之前",
      st["escGateBeforeExportPanel"],
      [st["escGateLine"], st["exportPanelLine"]])
    C("静态：setExportPanelOpen 全仓恰好 3 处调用（无外点关闭）",
      st["setExportPanelCallCount"] == 3, st["setExportPanelCallCount"])
    C("静态：关面板那一档里没有任何焦点处理（D4 的机制）",
      st["noFocusHandlingInPanelClose"], st["noFocusHandlingInPanelClose"])
    C("静态：面板挂在触发器之后（D6 反向 Tab 进不去的前提）",
      st["panelMountedAfterTrigger"], st["panelMountedAfterTrigger"])
    C("静态：触发器只有 aria-expanded，没有 aria-controls/aria-haspopup",
      st["triggerAriaExpanded"] and not st["triggerAriaControls"]
      and not st["triggerAriaHasPopup"],
      [st["triggerAriaExpanded"], st["triggerAriaControls"],
       st["triggerAriaHasPopup"]])
    C("静态：面板 if (!open) return null 存在（会卸载聚焦元素）",
      st["panelNullGateLine"] >= 0, st["panelNullGateLine"])
    C("静态：面板根是 <section> 且无 role/aria-label/id（D6）",
      st["panelRootTag"] == "section" and not st["panelRootHasRole"]
      and not st["panelRootHasAriaLabel"] and not st["panelRootHasId"],
      [st["panelRootTag"], st["panelRootHasRole"],
       st["panelRootHasAriaLabel"], st["panelRootHasId"]])
    C("静态：面板里没有手势边界/没有 onKeyDown/没有 stopPropagation（D1 不适用）",
      not st["panelHasGestureBoundary"] and not st["panelHasOnKeyDown"]
      and not st["panelHasStopPropagation"],
      [st["panelHasGestureBoundary"], st["panelHasOnKeyDown"],
       st["panelHasStopPropagation"]])
    C("静态：围栏 hook 有 keydown 监听、没有 focusin/focusout（D4 捞不回来）",
      st["fenceKeydownListener"] and not st["fenceFocusinListener"]
      and not st["fenceFocusoutListener"],
      [st["fenceKeydownListener"], st["fenceFocusinListener"],
       st["fenceFocusoutListener"]])
    C("静态：围栏 hook 只在整体卸载时调 restoreFocus",
      st["fenceRestoreCallCount"] == 1, st["fenceRestoreCallCount"])

    # ── 判据层
    C("判据 17 条", len(J) == 17, len(J))
    npass = sum(1 for j in J if j["verdict"] == "PASS")
    nfail = sum(1 for j in J if j["verdict"] == "FAIL")
    C("verdict 分布 11 PASS / 6 FAIL", npass == 11 and nfail == 6,
      [npass, nfail])
    fail_ids = [j["id"] for j in J if j["verdict"] == "FAIL"]
    C("★ 6 条 FAIL 恰好是 J4/J8/J10/J11/J12/J13（不许偷改）",
      sorted(fail_ids) == sorted(EXPECT_FAIL_IDS), fail_ids)
    C("判据 id 唯一且连续 J1..J17",
      [j["id"] for j in J] == ["J%d" % i for i in range(1, 18)],
      [j["id"] for j in J])
    C("★ 每条判据都有非空 evidenceKey",
      all(j.get("evidenceKey") for j in J))
    # 同一事实存两份：JSON 往返后仍要逐条相等（R33→R70）
    rt = json.loads(json.dumps(a, ensure_ascii=False))
    C("★ findings[k] == judgments[].evidence（JSON 往返后逐条）",
      all(rt["findings"][j["evidenceKey"]] == j["evidence"] for j in rt["judgments"]
          if j["evidenceKey"] in rt["findings"]),
      [j["id"] for j in rt["judgments"]
       if j["evidenceKey"] in rt["findings"]
       and rt["findings"][j["evidenceKey"]] != j["evidence"]])
    C("★ 每条判据的 evidenceKey 都真实存在",
      all(j["evidenceKey"] in f for j in J))
    C("★ evidence 不得为空对象（防止 all([]) 式空过）",
      all(j["evidence"] not in ({}, [], None) for j in J),
      [j["id"] for j in J if j["evidence"] in ({}, [], None)])
    C("判据 4 条引用 findings 里的不同键（不许全挂一个）",
      len({j["evidenceKey"] for j in J}) >= 6,
      len({j["evidenceKey"] for j in J}))

    # ── 缺陷层
    D = a["defects"]
    C("缺陷 4 条 D3/D4/D5/D6", sorted(d["id"] for d in D)
      == EXPECT_DEFECT_IDS, [d["id"] for d in D])
    C("★ 四条缺陷都标 needsSrcChange", all(df(d).get("needsSrcChange") is True
                                       for d in EXPECT_DEFECT_IDS))
    C("★ 四条缺陷都有 where 且每处指向真实行",
      all(df(d).get("where") and len(df(d)["where"]) >= 3
          for d in EXPECT_DEFECT_IDS))
    C("★ 本批不重复声明 763/764 的 D1/D2",
      not any(d["id"] in ("D1", "D2") for d in D),
      [d["id"] for d in D])
    C("★ D3 声明了与 764 D2 同守卫", bool(df("D3").get("sameGuardAs")))
    C("★★ D3 的机制点名了判别点 reachedWinBubble=true"
      "（否则「就是 D1 那个 stopPropagation」也能蒙混过关）",
      "reachedWinBubble" in df("D3").get("mechanism", ""),
      df("D3").get("mechanism", "")[:80])
    C("★ D3 的机制点名了 isEditable 早退这一行",
      "isEditable" in df("D3").get("mechanism", ""))
    C("★ D4 的机制点名了 if (!open) return null",
      "return null" in df("D4").get("mechanism", ""))
    C("★ D4 的机制点名了「没碰焦点 / 没有 focusin 监听」",
      "focusin" in df("D4").get("mechanism", ""))
    C("★ D4 引用了 762 的对照结论", bool(df("D4").get("contrast")))
    C("★ D5 引用了与 D3 的叠加", bool(df("D5").get("combinedWith")))
    C("★ 缺陷 where 的每处指针都指向真实文件与行号",
      all(ptr_valid(w) for d in EXPECT_DEFECT_IDS
          for w in df(d).get("where") or []),
      [w for d in EXPECT_DEFECT_IDS for w in (df(d).get("where") or [])
       if not ptr_valid(w)])
    C("缺陷严重度都在 低/中/高 之内",
      all(d["severity"] in ("低", "中", "高") for d in D),
      [d["severity"] for d in D])

    # ── 观察 / 教训 / 不声称
    C("观察 4 条", len(a["observations"]) == 4, len(a["observations"]))
    C("★ O3 明确标了「不作判据」",
      any(o["id"] == "O3" and "不作判据" in o["verdict"]
          for o in a["observations"]))
    C("探针教训 R63–R66 四条",
      sorted(x["id"] for x in a["probeLessons"]) == EXPECT_LESSON_IDS,
      [x["id"] for x in a["probeLessons"]])
    C("★ R63 记的是「按 Esc 之前先读状态」",
      any(x["id"] == "R63" and "先读状态" in x["text"]
          for x in a["probeLessons"]))
    C("★ R64 记的是「预期被实测否掉」",
      any(x["id"] == "R64" and "预期被否掉" in x["text"]
          for x in a["probeLessons"]))
    NC = " ".join(a["notClaimed"])
    C("★ 不声称里写明「没有点提交按钮」", "没有点提交按钮" in NC)
    C("★ 不声称里写明「没有选文件」", "没有选文件" in NC)
    C("★ 不声称里写明那 %d 次 Tab 谁接管判不了" % rw["flTabSteps"][0],
      "判不了" in NC or "无法区分" in NC)
    C("★ 不声称里写明无源站对照", "无源站对照" in NC)
    C("不声称 ≥ 8 条", len(a["notClaimed"]) >= 8, len(a["notClaimed"]))

    # ── 两轮可比
    C("两轮可比且逐字段一致（765a）",
      f["comparability"]["765a"]["allConsistent"] is True,
      f["comparability"]["765a"]["inconsistent"])
    C("两轮可比且逐字段一致（765b）",
      f["comparability"]["765b"]["allConsistent"] is True,
      f["comparability"]["765b"]["inconsistent"])
    C("★ 可比性判据比的是非空 key 列表",
      len(f["comparability"]["765a"]["keys"]) >= 8
      and len(f["comparability"]["765b"]["keys"]) >= 8,
      [len(f["comparability"]["765a"]["keys"]),
       len(f["comparability"]["765b"]["keys"])])
    C("原始读数轮数各为 2", rounds == 2 and roundsB == 2, [rounds, roundsB])
    C("产物声明的轮数与原始读数一致",
      all(p["rounds"] == 2 for p in a["probes"]),
      [p["rounds"] for p in a["probes"]])

    # ── 交叉核对：逐控件 Esc
    C("★ 逐控件 Esc：格子数 = 2 轮 × 5 控件",
      rw["sweepCells"] == 10, rw["sweepCells"])
    C("★ 关面板 8 格 / 不关 2 格",
      rw["sweepClosed"] == 8 and rw["sweepNotClosed"] == 2,
      [rw["sweepClosed"], rw["sweepNotClosed"]])
    C("★ 不关的只有 duration（时长框）",
      rw["sweepNotClosedIsDurationOnly"], rw["sweepNotClosedMarkers"])
    C("★ 没有一格把导演台关掉", rw["sweepDeskClosed"] == 0,
      rw["sweepDeskClosed"])
    C("★ 全部格子聚焦都成功（不许拿「没聚焦到」解释）",
      rw["sweepFocusFailures"] == 0, rw["sweepFocusFailures"])
    C("★ 探针自报的 allClosed 与重算一致（重算=False）",
      all(v is False for v in rw["sweepAllClosedSelfReported"])
      and not (rw["sweepClosed"] == rw["sweepCells"]),
      rw["sweepAllClosedSelfReported"])
    C("面板可聚焦控件两轮都是 5", rw["panelFocusables"] == [5, 5],
      rw["panelFocusables"])

    # ── 交叉核对：注入对照（本批判别点）
    C("★ 注入 8 格且 0 格失败", rw["injCells"] == 8 and rw["injFailed"] == 0,
      [rw["injCells"], rw["injFailed"]])
    C("★ 8 格全部获得焦点", rw["injFocusFailures"] == 0,
      rw["injFocusFailures"])
    C("★ 8 格焦点全在面板内", rw["injOutsidePanel"] == 0, rw["injOutsidePanel"])
    C("★★ 8/8 格 reachedWinBubble=true（D3 不是 D1 的 stopPropagation）",
      rw["injBubbleTrue"] == rw["injCells"] == 8,
      [rw["injBubbleTrue"], rw["injCells"]])
    C("8/8 格 reachedWinCapture=true", rw["injCaptureTrue"] == rw["injCells"],
      rw["injCaptureTrue"])
    C("★ 可编辑的 6 格（text/number/ce × 2 轮）全部关不掉面板",
      rw["injEditableCells"] == 6
      and rw["injEditableNotClosed"] == 6,
      [rw["injEditableCells"], rw["injEditableNotClosed"]])
    C("★ 不可编辑的 2 格（tabindex）都关掉了面板",
      rw["injNonEditableCells"] == 2 and rw["injNonEditableClosed"] == 2,
      [rw["injNonEditableCells"], rw["injNonEditableClosed"]])
    C("★ 注入对照里没有任何一格关掉导演台", rw["injDeskClosed"] == 0,
      rw["injDeskClosed"])
    C("★ 注入元素 0 污染（要么被移除、要么随面板卸载）",
      rw["injPolluted"] == 0, rw["injPolluted"])
    C("产物 inject 派生量与重算一致",
      f["inject"]["reachedWinBubble"] == rw["injBubbleTrue"]
      and f["inject"]["polluted"] == rw["injPolluted"]
      and f["inject"]["allMatched"] is True,
      [f["inject"]["reachedWinBubble"], rw["injBubbleTrue"]])

    # ── 交叉核对：外点关闭
    C("外点：两轮都真点了、命中点确实在面板外",
      all(rw["outsideAllClicked"]) and all(v is False
                                            for v in rw["outsideHitInPanel"]),
      [rw["outsideAllClicked"], rw["outsideHitInPanel"]])
    C("★ 点外面后面板仍然开着（2/2）",
      rw["outsidePanelStillOpen"] == [True, True], rw["outsidePanelStillOpen"])
    C("外点：导演台没被关掉", rw["outsideDeskClosed"] == [False, False],
      rw["outsideDeskClosed"])

    # ── 交叉核对：焦点丢失
    C("焦点丢失：按 Esc 之前焦点在面板内", rw["flBeforeInPanel"] == [True, True],
      rw["flBeforeInPanel"])
    C("★ 按 Esc 之前焦点在面板内 ⟹ 事件已到 window 冒泡",
      rw["flBubble"] == [True, True], rw["flBubble"])
    C("★ 那一档确实关掉了面板、没关导演台",
      rw["flClosedPanel"] == [True, True]
      and rw["flClosedDesk"] == [False, False],
      [rw["flClosedPanel"], rw["flClosedDesk"]])
    C("★ Esc 之后焦点两轮都掉到 BODY", rw["flActiveTag"] == ["BODY", "BODY"],
      rw["flActiveTag"])
    C("★ Esc 之后焦点两轮都逃出 dialog",
      rw["flActiveInDialog"] == [False, False], rw["flActiveInDialog"])
    C("★ Esc 之后焦点不在触发器上（D4 不是「焦点回触发器」）",
      rw["flActiveIsTrigger"] == [False, False], rw["flActiveIsTrigger"])
    C("★ Tab 落点序列长度与步数一致（不许少读）",
      rw["flTabSeqLen"] == rw["flTabSteps"], [rw["flTabSeqLen"],
                                             rw["flTabSteps"]])
    C("★ Tab 之后 %d 步全部落回 dialog（J9 的更正）" % rw["flTabSteps"][0],
      rw["flTabReachedDialog"] == rw["flTabSteps"],
      [rw["flTabReachedDialog"], rw["flTabSteps"]])

    # ── 交叉核对：反向 Tab
    C("反向 Tab：焦点确实落在触发器上、面板确实开着",
      rw["shiftFocusOk"] == [True, True]
      and rw["shiftPanelOpenBefore"] == [True, True],
      [rw["shiftFocusOk"], rw["shiftPanelOpenBefore"]])
    C("★ 反向 Tab %d 步 0 次进面板" % rw["shiftSteps"][0],
      rw["shiftInPanel"] == [0, 0], rw["shiftInPanel"])
    C("★ 反向 Tab 也没有逃出 dialog（围栏反向也守得住）",
      rw["shiftEscaped"] == [0, 0], rw["shiftEscaped"])

    # ── 交叉核对：Tab 围栏与打开焦点
    C("★ 正向从面板 Tab 0 次逃出 dialog",
      rw["tabEscapedForwardPanel"] == [0, 0], rw["tabEscapedForwardPanel"])
    C("★ 正向从触发器 Tab 0 次逃出 dialog",
      rw["tabEscapedForwardTrigger"] == [0, 0], rw["tabEscapedForwardTrigger"])
    C("正向从触发器 Tab 能走进面板",
      all(v > 0 for v in rw["tabInPanelFromTrigger"]),
      rw["tabInPanelFromTrigger"])
    C("★ 打开瞬间焦点留在触发器上",
      rw["focusOnOpenIsTrigger"] == [True, True], rw["focusOnOpenIsTrigger"])
    C("★ 打开瞬间焦点不在面板内",
      rw["focusOnOpenInPanel"] == [False, False], rw["focusOnOpenInPanel"])
    C("aria-expanded 开之前 false、开之后 true",
      rw["ariaExpandedBefore"] == ["false", "false"]
      and rw["ariaExpandedAfter"] == ["true", "true"],
      [rw["ariaExpandedBefore"], rw["ariaExpandedAfter"]])

    # ── 交叉核对：800px 阶梯
    C("800px 下导出面板两轮都打开", rw["panelOpenAt800"] == [True, True],
      rw["panelOpenAt800"])
    C("★ 阶梯四档读齐了两轮", rw["roundsWithLadder"] == 2,
      rw["roundsWithLadder"])
    C("★ 第 1 档只关抽屉（面板不关、导演台不关）",
      rw["tier1ClosedDrawerOnly"] == 2, rw["tier1ClosedDrawerOnly"])
    C("★ 第 2 档关面板不关导演台", rw["tier2ClosedPanelNotDesk"] == 2,
      rw["tier2ClosedPanelNotDesk"])
    C("★ 第 3 档关导演台", rw["tier3ClosedDesk"] == 2, rw["tier3ClosedDesk"])
    C("★ 时长框那一档两轮都留着面板（D3 在移动端同样成立）",
      rw["durationEscLeftPanelOpen"] == 2, rw["durationEscLeftPanelOpen"])

    # ── 交叉核对：导入侧
    C("★ 导入按钮两轮都真的弹了文件选择器",
      rw["fileChooserFired"] == [True, True], rw["fileChooserFired"])
    C("★ 隐藏 file input 两轮都是零可访问名（坐实 762）",
      rw["hiddenInputName"] == [None, None]
      and rw["hiddenInputAria"] == [None, None]
      and rw["hiddenInputTitle"] == [None, None]
      and rw["hiddenInputId"] == [None, None]
      and rw["hiddenInputHasLabelFor"] == [False, False],
      [rw["hiddenInputName"], rw["hiddenInputAria"], rw["hiddenInputTitle"],
       rw["hiddenInputId"], rw["hiddenInputHasLabelFor"]])
    C("★ 隐藏 file input 是 display:none（所以不可聚焦、不算缺陷）",
      rw["hiddenInputDisplay"] == ["none", "none"], rw["hiddenInputDisplay"])
    C("导入按钮本身有可访问名且未 disabled",
      all(rw["importBtnAria"]) and rw["importBtnDisabled"] == [False, False],
      [rw["importBtnAria"], rw["importBtnDisabled"]])
    C("文件类型限定为 json",
      all(".json" in (v or "") for v in rw["importAccept"]),
      rw["importAccept"])

    # ── 交叉核对：disclosure 契约
    C("★ 运行时：触发器两轮都没有 aria-controls / aria-haspopup",
      rw["trigAriaControls"] == [None, None]
      and rw["trigAriaHasPopup"] == [None, None],
      [rw["trigAriaControls"], rw["trigAriaHasPopup"]])
    C("★ 运行时：面板两轮都是无 role/无 aria-label/无 id 的 SECTION",
      rw["panelTag"] == ["SECTION", "SECTION"]
      and rw["panelRole"] == [None, None]
      and rw["panelAriaLabel"] == [None, None]
      and rw["panelId"] == [None, None],
      [rw["panelTag"], rw["panelRole"], rw["panelAriaLabel"], rw["panelId"]])

    # ── 产物结构
    C("产物 batch=765", a["batch"] == 765, a["batch"])
    C("产物声明未改 src/", a["env"]["srcModified"] is False)
    C("probes 列了 2 个探针", len(a["probes"]) == 2, len(a["probes"]))
    C("★ 每份 raw 都有 sha 记录", len(a["rawSha"]) == 2, list(a["rawSha"]))
    for fn in RAW_FILES:
        p = RAWDIR / fn
        C("原始读数存在 %s" % fn, p.exists())
    for fn in PROBE_FILES:
        C("探针脚本存在 %s（原始读数与探针必须随产物提交）" % fn,
          (PROBEDIR / fn).exists())
    C("README 存在", README.exists())
    if README.exists():
        t = README.read_text(encoding="utf-8")
        for h in ("## 选题", "## 判据", "## 缺陷", "## 观察",
                  "## 探针教训", "## 不声称", "## 复现"):
            C("README 含章节 %s" % h, h in t)
        for d in EXPECT_DEFECT_IDS:
            C("★ README 有缺陷 %s 的独立章节" % d,
              any(re.match(r"### %s\b" % d, ln) for ln in t.splitlines()))
        C("★ README 没有把 D1/D2 说成本批新发现",
          not re.search(r"### (D1|D2)\b", t))
        C("★ README 表格首格没有裸数字（pre-commit 正则会误判）",
          not any(BARE_NUM_CELL.match(ln) for ln in t.splitlines()),
          [ln for ln in t.splitlines() if BARE_NUM_CELL.match(ln)][:3])
        C("★ README 写明判据 17 条", "17" in t and "判据" in t)
        C("★ README 提到了没有点提交按钮", "提交按钮" in t)
        C("★ README 提到了 J9 的更正（预期被否掉）", "J9" in t)

    # ── 台账
    lt = LEDGER.read_text(encoding="utf-8")
    lines = lt.splitlines()
    led = [ln for ln in lines if ln.startswith("| Batch 765 |")]
    C("★ 台账恰好一行 Batch 765", len(led) == 1, len(led))
    if len(led) == 1:
        ln = led[0]
        C("★ 台账行首格是「Batch 765」", ln.split("|")[1].strip() == "Batch 765",
          ln.split("|")[1])
        C("★ 台账新行里 0 个 U+FFFD", ln.count(FFFD) == 0, ln.count(FFFD))
        C("★ 台账新行非空且够长（不许占位）", len(ln) > 200, len(ln))
        for kw in ("D3", "D4", "D5", "D6", "注入对照", "死路"):
            C("台账行提到 %s" % kw, kw in ln)
    C("★ 台账历史 U+FFFD 仍是 9 个（522/583/587 未被动）",
      lt.count(FFFD) == 9, lt.count(FFFD))
    hist = [i + 1 for i, ln in enumerate(lines) if FFFD in ln]
    C("★ U+FFFD 仍只落在 522/583/587 三行", hist == [522, 583, 587], hist)
    C("★ 台账行数 = 628（追加一行，不加前导空行）", len(lines) == 628,
      len(lines))
    C("★ Batch 764 行仍在且唯一",
      len([ln for ln in lines if ln.startswith("| Batch 764 |")]) == 1)
    return ck


# ═════════════════════ 阴性对照 ═════════════════════
def negative_controls(a, st, rw):
    cases = []

    def inj(name, mutate):
        bad = copy.deepcopy(a)
        mutate(bad)
        failed = [c["label"] for c in run_checks(bad, st, rw) if not c["pass"]]
        cases.append({"name": name, "caught": len(failed) > 0,
                      "firstFail": failed[0] if failed else None})

    def inj_static(name, mutate):
        bad = copy.deepcopy(st)
        mutate(bad)
        failed = [c["label"] for c in run_checks(a, bad, rw) if not c["pass"]]
        cases.append({"name": name, "caught": len(failed) > 0,
                      "firstFail": failed[0] if failed else None})

    def inj_raw(name, mutate):
        # 改**原始读数**再重算 —— 改派生量或改中间列表都没用（R46/R52）
        files = copy.deepcopy(rw.get("__raw__") or {})
        if not files:
            cases.append({"name": name, "caught": False,
                          "firstFail": "拿不到原始读数副本"})
            return
        mutate(files)
        try:
            badr = raw_side_from(files)
            failed = [c["label"] for c in run_checks(a, st, badr)
                      if not c["pass"]]
        except Exception as e:
            failed = ["重算抛错：%s" % e]
        cases.append({"name": name, "caught": len(failed) > 0,
                      "firstFail": failed[0] if failed else None})

    # —— 伪造「缺陷不存在」
    for i, d in enumerate(EXPECT_DEFECT_IDS):
        def drop(x, i=i):
            x["defects"] = [y for y in x["defects"] if y["id"] != d]
        inj("★ 删掉缺陷 %s" % d, drop)
    inj("★ 把 D3 降级成观察", lambda x: x.__setitem__(
        "observations", x["observations"] + [{"id": "O9", "text": "D3"}]))
    inj("★ 把 D3 的 needsSrcChange 去掉", lambda x: [y for y in x["defects"]
        if y["id"] == "D3"][0].pop("needsSrcChange"))
    inj("★ 把 D3 的机制改回「就是 D1 那个 stopPropagation」", lambda x:
        [y for y in x["defects"] if y["id"] == "D3"][0].__setitem__(
            "mechanism", "手势边界的 stopPropagation 吞掉了 Esc"))
    inj("★ 把 D3 的 sameGuardAs 抹掉（会掩盖与 764 D2 的关系）", lambda x:
        [y for y in x["defects"] if y["id"] == "D3"][0].pop("sameGuardAs"))
    inj("★ 把 D3 的机制改成不提判别点的说法", lambda x:
        [y for y in x["defects"] if y["id"] == "D3"][0].__setitem__(
            "mechanism", "手势边界的 stopPropagation 吞掉了 Esc"))
    inj("★ 把 D4 的机制改成不提 focusin", lambda x:
        [y for y in x["defects"] if y["id"] == "D4"][0].__setitem__(
            "mechanism", "面板卸载了聚焦元素，焦点就没了"))
    inj("★ 把 D3 的 where 指向不存在的行号", lambda x:
        [y for y in x["defects"] if y["id"] == "D3"][0]["where"].append(
            "src/components/director/DirectorDesk.tsx:99999"))
    inj("★ 把 D3 的 where 指向不存在的文件", lambda x:
        [y for y in x["defects"] if y["id"] == "D3"][0]["where"].append(
            "src/components/director/NoSuchFile.tsx:1"))
    inj("★ 把 D4 的对照（762 焦点回触发器）抹掉", lambda x:
        [y for y in x["defects"] if y["id"] == "D4"][0].pop("contrast"))
    inj("★ 把 D5 与 D3 的叠加抹掉", lambda x:
        [y for y in x["defects"] if y["id"] == "D5"][0].pop("combinedWith"))
    inj("★ 本批重复声明 763/764 的 D1", lambda x: x.__setitem__(
        "defects", x["defects"] + [{"id": "D1", "severity": "中",
                                    "title": "重开", "where": ["x"],
                                    "needsSrcChange": True}]))

    # —— 把 FAIL 偷偷改成 PASS
    for jid in EXPECT_FAIL_IDS:
        i = [k for k, j in enumerate(a["judgments"]) if j["id"] == jid][0]
        inj("★ 把 %s 从 FAIL 改成 PASS" % jid, lambda x, i=i:
            x["judgments"][i].__setitem__("verdict", "PASS"))
    inj("★ 把判据条数从 17 改成 12", lambda x: x.__setitem__(
        "judgments", x["judgments"][:12]))
    inj("★ 把 J10（不声称）也改成 PASS",
        lambda x: [j for j in x["judgments"] if j["id"] == "J10"][0]
        .__setitem__("verdict", "PASS"))
    inj("★ 判据全改成 PASS",
        lambda x: [j.__setitem__("verdict", "PASS") for j in x["judgments"]])

    # —— 只改一份事实
    inj("只改 findings.inject.reachedWinBubble",
        lambda x: x["findings"]["inject"].__setitem__("reachedWinBubble", 0))
    inj("只改 findings.inject.polluted",
        lambda x: x["findings"]["inject"].__setitem__("polluted", 1))
    inj("只改 findings.focusLoss.fellToBodyEverywhere",
        lambda x: x["findings"]["focusLoss"].__setitem__(
            "fellToBodyEverywhere", False))
    inj("只改 findings.shiftTab.inPanel",
        lambda x: x["findings"]["shiftTab"].__setitem__("inPanel", [3, 3]))
    inj("只改 findings.outsideClick.panelStayedOpen",
        lambda x: x["findings"]["outsideClick"].__setitem__(
            "panelStayedOpen", [False, False]))
    inj("只改 findings.mobileLadder.allLadderOk",
        lambda x: x["findings"]["mobileLadder"].__setitem__("allLadderOk", False))
    inj("只改 findings.disclosureContract.hasAriaControls",
        lambda x: x["findings"]["disclosureContract"].__setitem__(
            "hasAriaControls", True))
    inj("★ 把 J5 的 evidence 换成别的键（让 FAIL 失去支撑）", lambda x:
        x["judgments"][4].__setitem__("evidence",
                                      x["findings"]["escSweep"]))
    inj("★ 把 J8 的 evidence 换成可比性（焦点丢失失去支撑）", lambda x:
        x["judgments"][7].__setitem__("evidence",
                                      x["findings"]["comparability"]))
    inj("★ 把可比性说成一致（765a 不一致 key 非空）", lambda x:
        x["findings"]["comparability"]["765a"].__setitem__(
            "inconsistent", ["d_sweep"]))
    inj("★ 把 O3 的「不作判据」标成「事实记录」", lambda x:
        [o for o in x["observations"] if o["id"] == "O3"][0].__setitem__(
            "verdict", "事实记录"))
    inj("★ 不声称里删掉「没有点提交按钮」",
        lambda x: x.__setitem__("notClaimed",
                                [s for s in x["notClaimed"]
                                 if "提交按钮" not in s]))
    inj("★ 不声称里删掉「没有选文件」",
        lambda x: x.__setitem__("notClaimed",
                                [s for s in x["notClaimed"]
                                 if "选文件" not in s]))
    inj("★ 删掉 R64（预期被否掉那条教训）",
        lambda x: x.__setitem__("probeLessons",
                                [r for r in x["probeLessons"]
                                 if r["id"] != "R64"]))
    inj("★ 把 R63 的内容换成别的", lambda x:
        [r for r in x["probeLessons"] if r["id"] == "R63"][0].__setitem__(
            "text", "随便写点什么"))

    # —— 台账 / README
    def led_mutate(path_old, path_new=None):
        def f(x):
            pass
        return f
    C_LEDGER = LEDGER

    def inj_file(name, path, old, new):
        orig = path.read_text(encoding="utf-8")
        try:
            if old not in orig:
                cases.append({"name": name, "caught": False,
                              "firstFail": "待替换文本不存在（对照本身失效）"})
                return
            path.write_text(orig.replace(old, new, 1), encoding="utf-8")
            failed = [c["label"] for c in run_checks(a, st, rw)
                      if not c["pass"]]
        finally:
            path.write_text(orig, encoding="utf-8")
        cases.append({"name": name, "caught": len(failed) > 0,
                      "firstFail": failed[0] if failed else None})

    led = LEDGER.read_text(encoding="utf-8")
    led_line = next(ln for ln in led.splitlines()
                    if ln.startswith("| Batch 765 |"))
    # 末行没有换行符，所以要连**它前面的换行**一起删，否则删不掉
    _sep = "" if led.endswith(led_line + "\n") else "\n"
    inj_file("★ 台账删掉 Batch 765 行", LEDGER, _sep + led_line, "")
    inj_file("★ 台账行首格改成裸数字 765", LEDGER,
             "| Batch 765 |", "| 765 |")
    inj_file("★ 台账行首格写成 Batch 0765", LEDGER,
             "| Batch 765 |", "| Batch 0765 |")
    inj_file("★ 台账新行塞一个 U+FFFD", LEDGER,
             led_line[:40], led_line[:40] + FFFD)
    inj_file("★ 台账被追加了一行 Batch 766（行数断言）", LEDGER,
             "| Batch 765 |", "| Batch 765 |\n| Batch 766 | x")
    if README.exists():
        rt = README.read_text(encoding="utf-8")
        bad_cell = next((ln for ln in rt.splitlines()
                         if ln.startswith("| J")), "| J1 | x |")
        inj_file("★ README 表格首格改成裸数字", README, bad_cell, "| 1 | x |")
        inj_file("★ README 删掉「不声称」章节", README, "## 不声称", "## 备注")
        inj_file("★ README 删掉 D4", README, "### D4", "### 附注")

    # —— 静态层伪造
    inj_static("伪造：isEditable 早退排在 Escape 之后",
               lambda x: x.__setitem__("editableBeforeEscGate", False))
    inj_static("伪造：isEditable 早退排在「关面板」之后",
               lambda x: x.__setitem__("editableBeforeExportPanel", False))
    inj_static("伪造：移动端关抽屉那档排在 isEditable 早退之后",
               lambda x: x.__setitem__("mobileDrawerBeforeEditable", False))
    inj_static("伪造：setExportPanelOpen 有 4 处调用（有外点关闭）",
               lambda x: x.__setitem__("setExportPanelCallCount", 4))
    inj_static("伪造：关面板那一档里有焦点处理",
               lambda x: x.__setitem__("noFocusHandlingInPanelClose", False))
    inj_static("伪造：面板挂在触发器之前",
               lambda x: x.__setitem__("panelMountedAfterTrigger", False))
    inj_static("伪造：触发器有 aria-controls",
               lambda x: x.__setitem__("triggerAriaControls", True))
    inj_static("伪造：面板根有 role=dialog",
               lambda x: x.__setitem__("panelRootHasRole", True))
    inj_static("伪造：面板里有手势边界（D1 会适用）",
               lambda x: x.__setitem__("panelHasGestureBoundary", True))
    inj_static("伪造：围栏 hook 有 focusin 监听（能捞回焦点）",
               lambda x: x.__setitem__("fenceFocusinListener", True))
    inj_static("伪造：围栏 hook 多处调 restoreFocus",
               lambda x: x.__setitem__("fenceRestoreCallCount", 2))
    inj_static("伪造：面板没有 if (!open) return null",
               lambda x: x.__setitem__("panelNullGateLine", -1))

    # —— 原始读数：改真正的被检查键（R46/R52）
    inj_raw("★ 原始：把时长格的 panelClosed 改成 True（缺陷消失）",
            lambda x: x["vb765a.json"]["rounds"][0]["d_sweep"]["rows"][0]
            .__setitem__("panelClosed", True))
    inj_raw("★ 原始：把 tabindex 格的 panelClosed 改成 False",
            lambda x: x["vb765b.json"]["rounds"][0]["inj_tabindex"]
            .__setitem__("panelClosed", False))
    inj_raw("★ 原始：把注入对照的 reachedWinBubble 全改成 false（D1 混进来）",
            lambda x: [rd[k].__setitem__("reachedWinBubble", False)
                       for rd in x["vb765b.json"]["rounds"]
                       for k in ("inj_text", "inj_number", "inj_ce",
                                 "inj_tabindex")])
    inj_raw("★ 原始：把 contentEditable 格的 panelClosed 改成 True",
            lambda x: x["vb765b.json"]["rounds"][0]["inj_ce"].__setitem__(
                "panelClosed", True))
    inj_raw("★ 原始：把焦点掉到 BODY 改成 BUTTON（D4 消失）",
            lambda x: x["vb765b.json"]["rounds"][0]["focaloss_esc"]
            ["active"].__setitem__("tag", "BUTTON"))
    inj_raw("★ 原始：把 Esc 后焦点改成在触发器上",
            lambda x: x["vb765b.json"]["rounds"][0]["focaloss_esc"]
            ["active"].__setitem__("isTrigger", True))
    inj_raw("★ 原始：把 Tab 6 步的落点序列清空（不许少读）",
            lambda x: x["vb765b.json"]["rounds"][0]["focaloss_tab6"]
            .__setitem__("seq", []))
    inj_raw("★ 原始：把 reachedDialogCount 改成 0（死路）",
            lambda x: x["vb765b.json"]["rounds"][0]["focaloss_tab6"]
            .__setitem__("reachedDialogCount", 0))
    inj_raw("★ 原始：把反向 Tab 的 inPanelCount 改成 3",
            lambda x: x["vb765b.json"]["rounds"][0]["shift_tab12"]
            .__setitem__("inPanelCount", 3))
    inj_raw("★ 原始：把反向 Tab 的 escapedDialogCount 改成 1（围栏漏了）",
            lambda x: x["vb765b.json"]["rounds"][0]["shift_tab12"]
            .__setitem__("escapedDialogCount", 1))
    inj_raw("★ 原始：把外点点击后面板改成已关",
            lambda x: x["vb765b.json"]["rounds"][0]["outsideClick"]
            .__setitem__("panelStillOpen", False))
    inj_raw("★ 原始：把外点命中改成在面板内（点法就错了）",
            lambda x: x["vb765b.json"]["rounds"][0]["outsideClick"]["hit"]
            .__setitem__("inPanel", True))
    inj_raw("★ 原始：把第 3 档的 workspaceClosed 改成 False（阶梯错）",
            lambda x: x["vb765a.json"]["rounds"][0]["m_escNext"]
            .__setitem__("workspaceClosed", False))
    inj_raw("★ 原始：把第 1 档的 panelClosed 改成 True",
            lambda x: x["vb765a.json"]["rounds"][0]["m_escFromDuration"]
            .__setitem__("panelClosed", True))
    inj_raw("★ 原始：把文件选择器改成没弹",
            lambda x: x["vb765a.json"]["rounds"][0]["i_fileChooser"]
            .__setitem__("fired", False))
    inj_raw("★ 原始：把隐藏 input 的 accessibleName 填上",
            lambda x: x["vb765a.json"]["rounds"][0]["i_inputName"]
            .__setitem__("accessibleNameGuess", "导入项目"))
    inj_raw("★ 原始：把隐藏 input 的 display 改成 block（那就可聚焦了）",
            lambda x: x["vb765a.json"]["rounds"][0]["i_probe"]
            ["inputFocusable"].__setitem__("display", "block"))
    inj_raw("★ 原始：把触发器的 aria-controls 填上",
            lambda x: x["vb765b.json"]["rounds"][0]["state1"]["trigger"]
            .__setitem__("ariaControls", "export-panel"))
    inj_raw("★ 原始：把面板的 role 填成 dialog",
            lambda x: x["vb765b.json"]["rounds"][0]["state1"]["panel"]
            .__setitem__("role", "dialog"))
    inj_raw("★ 原始：把打开瞬间焦点改成进了面板",
            lambda x: x["vb765a.json"]["rounds"][0]["d_focusOnOpen"]
            .__setitem__("inPanel", True))
    inj_raw("★ 原始：把逐控件 Esc 的 focus 改成没聚焦上（不许这样解释）",
            lambda x: x["vb765a.json"]["rounds"][0]["d_sweep"]["rows"][0]
            ["focus"].__setitem__("focused", False))
    inj_raw("★ 原始：把某格的 workspaceClosed 改成 True（面板关到导演台了）",
            lambda x: x["vb765a.json"]["rounds"][0]["d_sweep"]["rows"][1]
            .__setitem__("workspaceClosed", True))
    inj_raw("★ all([]) 陷阱：把 d_sweep.rows 清空",
            lambda x: x["vb765a.json"]["rounds"][0]["d_sweep"]
            .__setitem__("rows", []))
    inj_raw("★ all([]) 陷阱：把注入对照某一格整个删掉",
            lambda x: x["vb765b.json"]["rounds"][0].pop("inj_ce"))
    inj_raw("★ all([]) 陷阱：把 shift_tab12 的 seq 清空",
            lambda x: x["vb765b.json"]["rounds"][0]["shift_tab12"]
            .__setitem__("seq", []))
    inj_raw("★ 伪造污染：注入元素既没移除也还在 DOM",
            lambda x: x["vb765b.json"]["rounds"][0]["inj_text"].__setitem__(
                "injectedStillInDom", True))
    return cases


def main():
    if not AUDIT.exists():
        print("缺少 runtime-audit.json")
        return 1
    a = json.loads(AUDIT.read_text(encoding="utf-8"))
    st = static_side()
    try:
        rw = raw_side()
        rawErr = None
    except Exception as e:
        rw, rawErr = {}, str(e)

    checks = run_checks(a, st, rw) if not rawErr else [
        {"label": "原始读数可用（raw/ 下 2 份）", "pass": False, "got": rawErr}]
    neg = [] if rawErr else negative_controls(a, st, rw)

    npass = sum(1 for c in checks if c["pass"])
    total = len(checks)
    neg_ok = sum(1 for n in neg if n["caught"])
    ok = npass == total and neg_ok == len(neg)

    REPORT.write_text(json.dumps(
        {"batch": 765, "checks": checks, "pass": npass, "total": total,
         "negativeControls": neg, "negativeCaught": neg_ok,
         "negativeTotal": len(neg), "rawError": rawErr, "ok": ok},
        ensure_ascii=False, indent=1), encoding="utf-8")

    for c in checks:
        if not c["pass"]:
            print("FAIL  %s  got=%s" % (c["label"], json.dumps(
                c["got"], ensure_ascii=False)[:220]))
    print("\n验收 %d/%d 通过" % (npass, total))
    print("阴性对照 %d/%d 全部拦下" % (neg_ok, len(neg)))
    for n in neg:
        if not n["caught"]:
            print("  ✗ 漏放：%s" % n["name"])
    print("batch 765 %s" % ("通过" if ok else "不通过"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
