"""batch 764 验收器：D1 影响面普查 + ⌘C/⌘V 与可编辑控件里的修饰键

三层结构（与 753–763 同）：
  1. **静态层** —— 从 `src/` 复核判据依赖的实现事实，含**顺序**断言
     （`isEditable` 早退必须排在 ⌘C 分支之前；移动端关抽屉那一档排在它之前）
  2. **产物层** —— 判据条数与 verdict、缺陷、观察、教训、README 结构、
     台账行、表格首格不许裸数字
  3. **原始读数交叉核对** —— 从 `raw/` 的 3 份原始输出**按正确键名重算**
     全部派生量；缺失时**判失败而不是通过**

⚠ 本批盯住三件容易自欺的事：
  - **J5 是 FAIL**：路径上下文两轮不可比。产物必须**如实**保留这条 FAIL，
    不许把它改成 PASS、也不许悄悄把路径上下文从统计里删掉。
  - **两轮起点不同**（5 vs 6 个对象，763 O1 的持久化）：跨轮比较只能比
    「派生量逐字段相等」，绝对值不同是正常的 —— 但也不能因此放松成
    「什么都不比」。
  - **R58 的教训**：探针自报的两轮一致**不能**当作它对的证据。阴性对照里
    有一组专打「把读法错误读成结论」。

判据 **11 条（9 PASS / 2 FAIL）**。
"""
import copy
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch764-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAWDIR = OUTDIR / "raw"
PROBEDIR = OUTDIR / "probes"
README = OUTDIR / "README.md"
LEDGER = ROOT / "docs/research/VERIFICATION_LEDGER.md"

RAW_FILES = ["vb764a.json", "vb764b.json", "vb764c.json"]
PROBE_FILES = ["dbg764a.py", "dbg764b.py", "dbg764c.py", "mk764audit.py"]
GESTURE_RE = re.compile(r"director-gesture-\d+-\d+")
BARE_NUM_CELL = re.compile(r"^\|\s*\d+[a-z]?\s*\|")
BOUNDARY_MARKERS = ["data-director-transform-field",
                    "data-director-path-anchor-position",
                    "data-director-path-anchor-handle",
                    "data-director-path-transform-field",
                    "data-director-pose-control",
                    "data-director-camera-fov-slider"]


def src(p):
    return (ROOT / p).read_text(encoding="utf-8")


def static_side():
    boundary = src("src/components/director/useDirectorGestureBoundary.ts")
    insp = src("src/components/director/DirectorInspector.tsx")
    desk = src("src/components/director/DirectorDesk.tsx")
    store = src("src/store/directorStore.ts")
    tree = src("src/components/director/DirectorObjectTree.tsx")
    timeline = src("src/components/director/DirectorTimeline.tsx")

    # ★ 必须用 rindex：文件顶部第 23 行还有一处 `onKeyDown:` 在**类型声明**里，
    #   find() 会命中那处，后面的 700 字符根本到不了实现。
    keydown_at = boundary.rfind("onKeyDown:")
    keydown = boundary[keydown_at:keydown_at + 700] if keydown_at >= 0 else ""
    esc_at = keydown.find('if (event.key === "Escape")')
    esc_block = keydown[esc_at:esc_at + 200] if esc_at >= 0 else ""

    is_editable = desk.find("if (isEditable) return;")
    copy_branch = desk.find('event.key.toLowerCase() === "c"')
    paste_branch = desk.find('event.key.toLowerCase() === "v"')
    mobile_esc = desk.find('event.key === "Escape" && activeMobilePanel')

    # copyDirectorSelection 的每条分支是否都写 lastCommandResult
    ci = store.find("copyDirectorSelection: () => {")
    copy_body = store[ci:ci + 2400] if ci >= 0 else ""
    pi = store.find("pasteDirectorClipboard: () => {")
    paste_body = store[pi:pi + 2400] if pi >= 0 else ""

    users = []
    for p in sorted((ROOT / "src").rglob("*.tsx")):
        try:
            t = p.read_text(encoding="utf-8")
        except Exception:
            continue
        n = t.count("useDirectorGestureBoundary({")
        if n:
            users.append({"file": str(p.relative_to(ROOT)), "count": n})

    return {
        "boundaryEscPreventDefault": "event.preventDefault();" in esc_block,
        "boundaryEscStopPropagation": "event.stopPropagation();" in esc_block,
        "boundaryNoEscapeGuard": ("if (!activeRef.current) return;"
                                  not in esc_block),
        "boundaryOnFocusBegin": "onFocus: begin" in boundary,
        "boundaryBeginSkipsModifierKeys": all(
            k in keydown for k in ('"Tab"', '"Shift"', '"Alt"', '"Control"',
                                   '"Meta"')),
        "isEditableBeforeCopy": (0 <= is_editable < copy_branch
                                 and copy_branch >= 0),
        "isEditableBeforePaste": (0 <= is_editable < paste_branch
                                  and paste_branch >= 0),
        "mobileEscBeforeIsEditable": (0 <= mobile_esc < is_editable
                                      and is_editable >= 0),
        "deskListenerOnWindow": 'window.addEventListener("keydown", handleKeyDown)'
        in desk,
        "inspSpreadsGestureOnNumber": (
            "data-director-transform-field={field}" in insp
            and "{...(isAxisDisabled(index) ? {} : gesture)}" in insp),
        "boundaryCallSites": users,
        "boundaryCallSiteCount": sum(u["count"] for u in users),
        "poseRangeHasMarker": "data-director-pose-control={control.key}" in insp,
        "fovRangeMarker": "data-director-camera-fov-slider" in insp,
        "pathAnchorMarkers": ("data-director-path-anchor-position" in insp
                              and "data-director-path-anchor-handle" in insp),
        "pathTransformMarker": "data-director-path-transform-field" in insp,
        "copyWritesLastResultEveryBranch": (
            copy_body.count("lastCommandResult: result") >= 4
            and "EMPTY_SELECTION" in copy_body
            and "COMMITTED" in copy_body),
        "copyNeverWritesHistory": ("historyEntries: 0" in copy_body),
        "pasteWritesLastResult": ("lastCommandResult: result" in paste_body),
        "selectionActions": [
            'data-director-selection-action="copy"' in tree,
            'data-director-selection-action="delete"' in tree,
            'data-director-selection-action="clear"' in tree],
        "pathPresetHook": "data-director-motion-path-preset" in timeline,
        "createMotionPath": "createMotionPath" in timeline,
    }


def load_raw():
    miss = [f for f in RAW_FILES if not (RAWDIR / f).exists()]
    if miss:
        raise RuntimeError("缺原始读数 %s" % miss)
    return {f[:-5]: json.loads((RAWDIR / f).read_text(encoding="utf-8"))
            for f in RAW_FILES}


def raw_side():
    r = load_raw()
    out = raw_side_from(r)
    out["__raw__"] = r
    return out


def raw_side_from(r):
    a, b, c = r["vb764a"], r["vb764b"], r["vb764c"]
    out = {"filesOk": True}
    out["rawRounds"] = {"764a": len(a["rounds"]), "764b": len(b["rounds"]),
                        "764c": len(c["rounds"])}

    # ── 764a：逐上下文
    def ctx(rd):
        rows = []
        for c_ in rd.get("contexts") or []:
            if "rows" not in c_:
                rows.append({"label": c_.get("label"), "FAILED": True})
                continue
            bad, good, skipped = [], [], []
            for rr in c_["rows"]:
                esc = rr.get("esc") or {}
                rec = {"i": rr["i"], "type": rr["item"].get("type"),
                       "boundary": rr["item"].get("boundary"),
                       "focused": (rr.get("focus") or {}).get("focused"),
                       "reachedWinBubble": esc.get("reachedWinBubble"),
                       "reachedWinCapture": esc.get("reachedWinCapture"),
                       "drawerClosed": rr.get("drawerClosed")}
                if "skipped" in rr:
                    rec["skipped"] = rr["skipped"]
                    skipped.append(rec)
                elif rr["item"].get("boundary"):
                    bad.append(rec)
                else:
                    good.append(rec)
            rows.append({
                "label": c_["label"],
                "totalFocusable": c_["totalFocusable"],
                "boundaryCount": c_["boundaryCount"],
                "boundaryTypes": c_["boundaryTypes"],
                "boundaryRows": bad, "nonBoundaryRows": good,
                "boundarySwallowed": [x["i"] for x in bad
                                      if x["reachedWinBubble"] is False],
                "nonBoundarySwallowed": [x["i"] for x in good
                                         if x["reachedWinBubble"] is False],
                "skipped": skipped})
        return rows

    r1, r2 = ctx(a["rounds"][0]), ctx(a["rounds"][1])
    out["contextsRound1"] = r1
    out["contextsRound2"] = r2
    comp, incomp = [], []
    for x, y in zip(r1, r2):
        same = all(x.get(k) == y.get(k) for k in
                   ("label", "totalFocusable", "boundaryCount",
                    "boundaryTypes", "boundarySwallowed",
                    "nonBoundarySwallowed"))
        row = {"label": x.get("label"), "comparable": same,
               "round1": {k: x.get(k) for k in
                          ("totalFocusable", "boundaryCount", "boundaryTypes",
                           "boundarySwallowed", "nonBoundarySwallowed")},
               "round2": {k: y.get(k) for k in
                          ("totalFocusable", "boundaryCount", "boundaryTypes",
                           "boundarySwallowed", "nonBoundarySwallowed")}}
        (comp if same else incomp).append(row)
    out["comparable"] = comp
    out["incomparable"] = incomp
    out["incomparableLabels"] = [x["label"] for x in incomp]
    out["comparableLabels"] = [x["label"] for x in comp]
    labels = {x["label"] for x in comp}
    brows = [x for y in r1 if y["label"] in labels for x in y["boundaryRows"]]
    nrows = [x for y in r1 if y["label"] in labels
             for x in y["nonBoundaryRows"]]
    out["boundaryRows"] = brows
    out["nonBoundaryRows"] = nrows
    out["boundaryCount"] = len(brows)
    out["nonBoundaryCount"] = len(nrows)
    out["allBoundarySwallowed"] = bool(brows) and all(
        x["reachedWinBubble"] is False for x in brows)
    out["allBoundaryNotReachedWindowBubble"] = bool(brows) and all(
        x["reachedWinBubble"] is False for x in brows)
    out["allBoundaryReachedCapture"] = bool(brows) and all(
        x["reachedWinCapture"] is True for x in brows)
    out["allBoundaryFocused"] = bool(brows) and all(
        x["focused"] is True for x in brows)
    out["noNonBoundarySwallowed"] = bool(nrows) and all(
        x["reachedWinBubble"] is not False for x in nrows)
    out["boundaryTypes"] = sorted({str(x["type"]) for x in brows})
    by = {x["label"]: x for x in r1}
    for key, label in (("defaultContext", "default"),
                       ("poseContext", "character:pose"),
                       ("cameraContext", "camera:properties")):
        x = by.get(label) or {}
        out[key] = {"label": x.get("label"),
                    "totalFocusable": x.get("totalFocusable"),
                    "boundaryCount": x.get("boundaryCount"),
                    "boundaryTypes": x.get("boundaryTypes"),
                    "swallowedCount": len(x.get("boundarySwallowed") or []),
                    "types": sorted({str(y.get("type")) for y in
                                     x.get("boundaryRows") or []})}
    out["poseTypes"] = out["poseContext"]["types"]
    out["defaultTypes"] = out["defaultContext"]["types"]
    out["emptyContexts"] = [{"label": x["label"],
                             "totalFocusable": x["totalFocusable"],
                             "boundaryCount": x["boundaryCount"]}
                            for x in r1 if x.get("boundaryCount") == 0]
    out["pathCreated"] = a["rounds"][0].get("pathCreated")
    out["pathTrigger"] = a["rounds"][0].get("pathTrigger")
    out["markersNeverSeen"] = {
        m: not any(any(m in (str(y.get("marks") or []))
                       for y in x.get("boundaryRows") or [])
                   for x in r1)
        for m in BOUNDARY_MARKERS}
    out["summaryRound1"] = a["rounds"][0].get("summary")

    # ── 764b：⌘C/⌘V 与鼠标等价物
    def kb(rd):
        return {k: rd.get(k) for k in
                ("C1_pasteWithEmptyClipboard", "C2_copy", "C3_paste",
                 "C4_pasteAgain", "C5_copyFromField")}

    def ms(rd):
        return {k: rd.get(k) for k in
                ("C6_copyButton", "C6_clearButton", "C6_deleteButton")}

    kb1, kb2 = kb(b["rounds"][0]), kb(b["rounds"][1])
    out["keyboard"] = {"r1": kb1, "r2": kb2}
    def _d(rec, field="count"):
        a_, b_ = rec.get(field) or [0, 0]
        return b_ - a_

    def _dh(rec):
        a_, b_ = rec.get("past") or ["0", "0"]
        return int(b_) - int(a_)

    out["copyFromTreeCommand"] = [x["C2_copy"]["lastCommand"][1]
                                  for x in (kb1, kb2)]
    # ★ Δ 从 count/past **重算**，不采信探针自报的 countDelta/historyDelta；
    #   两者不一致要看得出来（763 的 seedSeriesSameLesson）。
    out["pasteDeltas"] = [_d(x["C3_paste"]) for x in (kb1, kb2)]
    out["pasteAgainDeltas"] = [_d(x["C4_pasteAgain"]) for x in (kb1, kb2)]
    out["pasteHistoryDeltas"] = [_dh(x["C3_paste"]) for x in (kb1, kb2)]
    out["probeSelfDeltaAgrees"] = all(
        _d(x[k]) == x[k].get("countDelta") and _dh(x[k]) == x[k].get(
            "historyDelta")
        for x in (kb1, kb2)
        for k in ("C1_pasteWithEmptyClipboard", "C3_paste", "C4_pasteAgain"))
    out["emptyPaste"] = [{"lastCommand":
                          x["C1_pasteWithEmptyClipboard"]["lastCommand"][1],
                          "countDelta":
                              x["C1_pasteWithEmptyClipboard"]["countDelta"],
                          "historyDelta":
                              x["C1_pasteWithEmptyClipboard"]["historyDelta"]}
                         for x in (kb1, kb2)]
    out["copyFromField764b"] = [
        {"lastCommand": x["C5_copyFromField"]["lastCommand"][1],
         "countDelta": _d(x["C5_copyFromField"]),
         "historyDelta": _dh(x["C5_copyFromField"])}
        for x in (kb1, kb2)]
    out["mouse"] = {"r1": ms(b["rounds"][0]), "r2": ms(b["rounds"][1])}
    out["mouseActions"] = [
        {"action": (ms(rd).get(k) or {}).get("action"),
         "countDelta": _d(ms(rd).get(k) or {}),      # 重算，不读自报
         "count": (ms(rd).get(k) or {}).get("count"),
         "selfReported": (ms(rd).get(k) or {}).get("countDelta"),
         "lastCommand": ((ms(rd).get(k) or {}).get("lastCommand")
                         or [None, None])[1]}
        for rd in b["rounds"] for k in ("C6_copyButton", "C6_clearButton",
                                        "C6_deleteButton")]
    out["mouseSelfDeltaAgrees"] = all(
        x["countDelta"] == x["selfReported"] for x in out["mouseActions"])

    # ── 764c：可编辑控件里的修饰键
    def case(rd):
        A, B, C, D = (rd.get("A_emptyPaste") or {},
                      rd.get("B_copyFromTree") or {},
                      rd.get("C_copyFromField") or {},
                      rd.get("D_paste") or {})
        f = rd.get("C_focusField") or {}
        return {
            "focusField": {"focused": f.get("focused"), "tf": f.get("tf"),
                           "ta": f.get("ta")},
            "copyFromTree": {"lastCommand": B.get("lastCommand"),
                             "lastDisposition": B.get("lastDisposition"),
                             "count": B.get("count"), "past": B.get("past")},
            "copyFromField": {
                "lastCommand": C.get("lastCommand"),
                "lastDisposition": C.get("lastDisposition"),
                "count": C.get("count"), "past": C.get("past"),
                "gestureBefore": GESTURE_RE.sub(
                    "director-gesture-<gen>",
                    C.get("activeGestureBefore") or ""),
                "gestureAfter": GESTURE_RE.sub(
                    "director-gesture-<gen>",
                    C.get("activeGestureAfter") or ""),
                "gestureUnchanged": (C.get("activeGestureBefore")
                                     == C.get("activeGestureAfter")),
                "lastCommandUnchanged": (
                    len(C.get("lastCommand") or []) == 2
                    and C["lastCommand"][0] == C["lastCommand"][1])},
            "pasteFromField": {
                "lastCommand": D.get("lastCommand"),
                "count": D.get("count"), "past": D.get("past"),
                "countDelta": ((D.get("count") or [0, 0])[1]
                               - (D.get("count") or [0, 0])[0]),
                "historyDelta": (int((D.get("past") or ["0", "0"])[1])
                                 - int((D.get("past") or ["0", "0"])[0]))},
            "emptyPaste": {"lastCommand": A.get("lastCommand"),
                           "lastDisposition": A.get("lastDisposition"),
                           "countDelta": ((A.get("count") or [0, 0])[1]
                                          - (A.get("count") or [0, 0])[0]),
                           "historyDelta": (int((A.get("past")
                                                 or ["0", "0"])[1])
                                            - int((A.get("past")
                                                   or ["0", "0"])[0]))},
            "picksFailed": sorted(k for k in ("B_pickA", "B_pickA2", "C_pickB",
                                              "C_pickB2", "D_pickC")
                                  if isinstance(rd.get(k), dict)
                                  and rd[k].get("err"))}

    cases = [case(rd) for rd in c["rounds"]]
    out["cases"] = cases
    out["copyFromTreeWorks"] = all(
        x["copyFromTree"]["lastCommand"][1] == "COPY_SELECTION"
        and x["copyFromTree"]["lastDisposition"][1] == "COMMITTED"
        for x in cases)
    out["copyFromFieldDead"] = all(
        x["copyFromField"]["lastCommandUnchanged"]
        and x["copyFromField"]["count"][0] == x["copyFromField"]["count"][1]
        and x["copyFromField"]["past"][0] == x["copyFromField"]["past"][1]
        for x in cases)
    out["pasteFromFieldDead"] = all(
        x["pasteFromField"]["countDelta"] == 0
        and x["pasteFromField"]["historyDelta"] == 0 for x in cases)
    out["boundaryDidNotBlock"] = all(x["copyFromField"]["gestureUnchanged"]
                                     for x in cases)
    out["emptyPasteNoop"] = all(
        x["emptyPaste"]["lastDisposition"][1] == "NOOP"
        and x["emptyPaste"]["countDelta"] == 0
        and x["emptyPaste"]["historyDelta"] == 0 for x in cases)
    out["picksFailed"] = cases[0]["picksFailed"]
    out["casesAllEqual"] = len({json.dumps(x, sort_keys=True, ensure_ascii=False)
                                for x in cases}) == 1
    return out


def run_checks(a, st, rw):
    checks = []

    def ck(label, cond, got=None):
        checks.append({"label": label, "pass": bool(cond), "got": got})

    f = a.get("findings") or {}
    J = a.get("judgments") or []
    R = README.read_text(encoding="utf-8") if README.exists() else ""
    led = LEDGER.read_text(encoding="utf-8") if LEDGER.exists() else ""
    ledLines = led.splitlines()

    # ═════════ 1. 静态层 ═════════
    ck("静态：边界在 Escape 上 preventDefault", st["boundaryEscPreventDefault"])
    ck("静态：边界在 Escape 上 stopPropagation（D1 的机制）",
       st["boundaryEscStopPropagation"])
    ck("静态：边界的 onKeyDown 至今**没有**「没有手势就放行」的守卫",
       st["boundaryNoEscapeGuard"])
    ck("静态：边界 onFocus 仍是 begin()（所以守卫必须两处一起改）",
       st["boundaryOnFocusBegin"])
    ck("静态：边界对 Tab/Shift/Alt/Ctrl/Meta 不 begin（所以 ⌘C 不会被它拦）",
       st["boundaryBeginSkipsModifierKeys"])
    ck("★ 静态：isEditable 早退排在 ⌘C 分支之前（D2 的机制）",
       st["isEditableBeforeCopy"])
    ck("★ 静态：isEditable 早退排在 ⌘V 分支之前",
       st["isEditableBeforePaste"])
    ck("静态：移动端关抽屉那一档排在 isEditable 早退之前",
       st["mobileEscBeforeIsEditable"])
    ck("静态：Esc 阶梯挂在 window 上", st["deskListenerOnWindow"])
    ck("静态：变换数值框 spread 了 gesture", st["inspSpreadsGestureOnNumber"])
    ck("静态：边界 hook 至少 5 处调用", st["boundaryCallSiteCount"] >= 5,
       st["boundaryCallSiteCount"])
    ck("静态：姿势滑杆确实有 data-director-pose-control 标记",
       st["poseRangeHasMarker"])
    ck("静态：路径锚点与路径变换的标记在 src/ 里存在（渲染不出来 ≠ 不存在）",
       st["pathAnchorMarkers"] and st["pathTransformMarker"])
    ck("静态：copyDirectorSelection 每条分支都写 lastCommandResult",
       st["copyWritesLastResultEveryBranch"])
    ck("静态：copyDirectorSelection 明写 historyEntries: 0（复制不改历史）",
       st["copyNeverWritesHistory"])
    ck("静态：树里 copy/delete/clear 三枚 action 都在",
       all(st["selectionActions"]), st["selectionActions"])
    ck("静态：时间轴的路径预设钩子存在（764a 建路径用的就是它）",
       st["pathPresetHook"] and st["createMotionPath"])

    # ═════════ 2. 产物层 ═════════
    ck("产物：判据 11 条", len(J) == 11, len(J))
    ck("产物：判据 id 连号 J1..J11",
       [j.get("id") for j in J] == ["J%d" % i for i in range(1, 12)])
    ck("★ 产物：9 PASS + 2 FAIL，且 FAIL 正好是 J5/J9（不许偷偷改判）",
       [j.get("verdict") for j in J]
       == (["PASS"] * 4 + ["FAIL"] + ["PASS"] * 3 + ["FAIL"] + ["PASS"] * 2),
       [j.get("id") + ":" + str(j.get("verdict")) for j in J])
    ck("产物：每条判据都有 statement",
       all(j.get("statement") for j in J))
    ck("产物：findings 与 judgments[].evidence 逐条同源",
       all(f.get(j.get("evidenceKey")) == j.get("evidence") for j in J),
       [j.get("id") for j in J
        if f.get(j.get("evidenceKey")) != j.get("evidence")])
    ck("产物：每条判据引用的键都存在",
       all(j.get("evidenceKey") in f for j in J))
    ck("产物：判据 id 在 README 里都被引用",
       all(("| %s |" % j["id"]) in R for j in J))
    # ★ 按 id 取，不按下标 —— 少一条缺陷时检查要「失败」而不是「崩掉」
    dbyid = {d.get("id"): d for d in a.get("defects") or []}
    ck("产物：缺陷恰好 D1 与 D2 两条",
       sorted(dbyid) == ["D1", "D2"], sorted(dbyid))
    ck("产物：D1 标了承自 763", (dbyid.get("D1") or {}).get("carriedOverFrom")
       == 763)
    ck("★ 产物：D1 明确写了「更正 763 的全是 type=number」",
       "type=number" in ((dbyid.get("D1") or {}).get("widenedBy764") or "")
       or "更正" in ((dbyid.get("D1") or {}).get("widenedBy764") or ""))
    ck("★ 产物：D1 明确记了「仍然未验证」的三类控件",
       all(k in ((dbyid.get("D1") or {}).get("stillUnverified") or "")
           for k in (":825", ":866", ":1579")))
    ck("★ 产物：D2 标了低严重度且有实测过的替代路径",
       (dbyid.get("D2") or {}).get("severity") == "低"
       and bool((dbyid.get("D2") or {}).get("workaroundMeasured")))
    ck("★ 产物：D2 明确写了「不是 D1 那个 stopPropagation」",
       "isEditable" in ((dbyid.get("D2") or {}).get("mechanism") or "")
       and "不是" in ((dbyid.get("D2") or {}).get("mechanism") or "")
       and "stopPropagation" in ((dbyid.get("D2") or {}).get("mechanism") or ""))
    ck("产物：两个缺陷都标了需要改 src/",
       all(d.get("needsSrcChange") is True for d in a.get("defects") or []))
    ck("产物：观察 3 条", len(a.get("observations") or []) == 3)
    ck("产物：探针教训 5 条 R58..R62",
       [x.get("id") for x in a.get("probeLessons") or []]
       == ["R58", "R59", "R60", "R61", "R62"])
    ck("产物：R58（读标志顺序）确实写了 TAKE 会清标志",
       any("TAKE" in x.get("text", "") and "PEEK" in x.get("text", "")
           for x in a.get("probeLessons") or []))
    ck("产物：不声称清单非空", len(a.get("notClaimed") or []) >= 7)
    ck("产物：明说路径上下文不可比",
       any("不可比" in s for s in a.get("notClaimed") or []))
    ck("★ 产物：明说路径锚点/FOV 那三类**没有测过**",
       any("没有测过" in s for s in a.get("notClaimed") or []))
    ck("★ 产物：明说边界检测是按标记做的、可能漏检",
       any("标记" in s and "漏检" in s for s in a.get("notClaimed") or []))
    ck("产物：明说没读原生剪贴板",
       any("clipboard" in s for s in a.get("notClaimed") or []))
    ck("产物：探针清单 3 个", len(a.get("probes") or []) == 3)
    ck("产物：每个探针指向的文件都存在",
       all((OUTDIR / p["raw"]).exists() and (OUTDIR / p["file"]).exists()
           for p in a.get("probes") or []))
    ck("产物：raw/ 下正好 3 份原始读数",
       sorted(x.name for x in RAWDIR.glob("vb764*.json")) == sorted(RAW_FILES))
    ck("产物：probes/ 下 3 个探针 + 1 个汇编器",
       sorted(x.name for x in PROBEDIR.glob("*.py")) == sorted(PROBE_FILES))
    ck("产物：3 份原始读数都记了 sha", len(a.get("rawSha") or {}) == 3)
    ck("产物：本批 src 未改动",
       (a.get("env") or {}).get("srcModified") is False)

    # ── README
    ck("README：存在且非空", len(R) > 2000, len(R))
    for need in ("## 判据", "## 缺陷", "## 观察", "## 探针教训", "## 不声称",
                 "## 复现"):
        ck("README：含章节 %s" % need, need in R)
    bare = [i + 1 for i, l in enumerate(R.splitlines())
            if BARE_NUM_CELL.match(l)]
    ck("README：表格首格没有裸数字（pre-commit 钩子的正则）", not bare, bare)
    ck("★ README：写了「更正 763 的全是 type=number」", "更正 763" in R)
    ck("★ README：写了 J5 是 FAIL 且是范围声明",
       "J5" in R and "不是产品缺陷" in R)
    ck("★ README：写了 D2 有可用替代路径", "替代" in R or "三枚按钮" in R)
    ck("README：写了 D1 两处必须一起改", "两处必须一起改" in R)
    ck("★ README：写了 764c 五次 pick 全部失败（探针自伤如实记账）",
       "五次" in R and "pick" in R)

    # ── 台账
    row = [l for l in ledLines if l.startswith("| Batch 764 |")]
    ck("台账：恰好一行 Batch 764", len(row) == 1, len(row))
    ck("台账：Batch 764 行没有 U+FFFD", row and "\ufffd" not in row[0])
    ck("台账：行数 627", len(ledLines) == 627, len(ledLines))
    ck("台账：历史 U+FFFD 仍只在 522/583/587",
       [i + 1 for i, l in enumerate(ledLines) if "\ufffd" in l]
       == [522, 583, 587],
       [i + 1 for i, l in enumerate(ledLines) if "\ufffd" in l])

    # ═════════ 3. 原始读数交叉核对 ═════════
    ck("原始：3 份读数全部可读", rw.get("filesOk") is True)
    ck("原始：三个探针都是两轮",
       rw.get("rawRounds") == {"764a": 2, "764b": 2, "764c": 2},
       rw.get("rawRounds"))

    # J1 / J3
    ck("J1 交叉：可比上下文至少 3 个", len(rw.get("comparable") or []) >= 3,
       len(rw.get("comparable") or []))
    ck("★ J1 交叉：可比上下文里每一个边界控件都被吞",
       rw.get("allBoundarySwallowed") is True)
    ck("★ J1 交叉：非边界控件一个都没被吞",
       rw.get("noNonBoundarySwallowed") is True)
    ck("★ J1 交叉：阴性对照至少 3 个（不能一个都没有）",
       (rw.get("nonBoundaryCount") or 0) >= 3, rw.get("nonBoundaryCount"))
    ck("J1 交叉：边界控件至少 30 个", (rw.get("boundaryCount") or 0) >= 30,
       rw.get("boundaryCount"))
    ck("J1：产物 boundaryCountComparable 与重算一致",
       f.get("boundaryCountComparable") == rw.get("boundaryCount"))
    ck("J1：产物 nonBoundaryCountComparable 与重算一致",
       f.get("nonBoundaryCountComparable") == rw.get("nonBoundaryCount"))
    ck("J1：产物 boundarySwallowedAll 与重算一致",
       f.get("boundarySwallowedAll") is True
       and f.get("boundarySwallowedAll") == rw.get("allBoundarySwallowed"))
    ck("J1：产物 nonBoundaryNeverSwallowed 与重算一致",
       f.get("nonBoundaryNeverSwallowed") is True
       and f.get("nonBoundaryNeverSwallowed")
       == rw.get("noNonBoundarySwallowed"))
    ck("★ J3 交叉：全部边界控件 reachedWinBubble=false",
       rw.get("allBoundaryNotReachedWindowBubble") is True)
    ck("★ J3 交叉：全部边界控件 window 捕获照样触发",
       rw.get("allBoundaryReachedCapture") is True)
    ck("★ J3 交叉：全部边界控件焦点确实落上（排除「没聚焦到」）",
       rw.get("allBoundaryFocused") is True)
    ck("J3：产物 boundaryNeverReachedWindowBubble / reachedWindowCapture 一致",
       f.get("boundaryNeverReachedWindowBubble") is True
       and f.get("boundaryReachedWindowCapture") is True)
    ck("J3：产物 boundaryFocusAllSucceeded 与重算一致",
       f.get("boundaryFocusAllSucceeded") is True
       and f.get("boundaryFocusAllSucceeded") == rw.get("allBoundaryFocused"))

    # J2
    ck("★ J2 交叉：姿势上下文里出现 type=range 的边界控件",
       "range" in (rw.get("poseTypes") or []), rw.get("poseTypes"))
    ck("★ J2 交叉：默认上下文里是 type=number",
       rw.get("defaultTypes") == ["number"], rw.get("defaultTypes"))
    ck("★ J2 交叉：两类合起来覆盖 number 与 range",
       rw.get("boundaryTypes") == ["number", "range"], rw.get("boundaryTypes"))
    ck("★ J2：产物 boundaryTypesComparable 与重算一致",
       f.get("boundaryTypesComparable") == rw.get("boundaryTypes"))
    ck("★ J2：产物 poseContext 与重算一致（边界数与被吞数）",
       f.get("poseContext", {}).get("boundaryCount")
       == rw.get("poseContext", {}).get("boundaryCount")
       and f.get("poseContext", {}).get("boundarySwallowedCount")
       == rw.get("poseContext", {}).get("swallowedCount"),
       [f.get("poseContext"), rw.get("poseContext")])
    ck("★ J2：README 与台账都写了「更正 763 的全是 type=number」",
       "更正 763" in R
       and any("type=number" in l or "全是 type=number" in l
               for l in row))

    # J4
    ck("J4 交叉：确实有上下文一个边界控件都没有（如实记空）",
       len(rw.get("emptyContexts") or []) >= 2,
       rw.get("emptyContexts"))
    ck("J4：产物 emptyContexts 与重算一致",
       f.get("emptyContexts") == rw.get("emptyContexts"))
    ck("J4：产物如实写了那两个上下文可聚焦控件很少",
       all(x["totalFocusable"] <= 10 for x in rw.get("emptyContexts") or []))

    # J5（FAIL，必须保留）
    ck("★ J5 交叉：确实存在不可比上下文（FAIL 的前提）",
       len(rw.get("incomparable") or []) >= 1,
       rw.get("incomparableLabels"))
    ck("★ J5 交叉：不可比的正是 path+camera 那一组 + camera:properties",
       set(rw.get("incomparableLabels") or [])
       <= {"camera:properties", "path+camera:properties",
           "path+camera:motion", "path+camera:captures"},
       rw.get("incomparableLabels"))
    ck("★ J5：产物 incomparableLabels 与重算一致",
       f.get("incomparableLabels") == rw.get("incomparableLabels"))
    ck("★ J5：判据 5 的 verdict 是 FAIL", J[4].get("verdict") == "FAIL")
    ck("★ J5：不可比上下文没有混进可比统计里",
       not (set(f.get("comparableLabels") or [])
            & set(rw.get("incomparableLabels") or [])))

    # J6
    ck("J6 交叉：路径确实建出来了（lastCommand=PROJECT_MUTATION）",
       (rw.get("pathCreated") or {}).get("lastCommand")
       == "PROJECT_MUTATION", rw.get("pathCreated"))
    ck("★ J6 交叉：路径锚点/路径变换/FOV 三个标记两轮都没出现在任何行上",
       all(rw.get("markersNeverSeen", {}).get(m) for m in
           ("data-director-path-anchor-position",
            "data-director-path-transform-field",
            "data-director-camera-fov-slider")),
       rw.get("markersNeverSeen"))
    ck("★ J6：产物 pathCreated 与重算一致",
       f.get("pathCreated") == rw.get("pathCreated"))
    ck("★ J6：README 明说这三类「仍然未验证」",
       "仍然未验证" in R or "没渲染" in R)

    # J7
    ck("J7 交叉：两轮里树上的 ⌘C 都落 COPY_SELECTION",
       rw.get("copyFromTreeCommand") == ["COPY_SELECTION"] * 2,
       rw.get("copyFromTreeCommand"))
    ck("J7 交叉：两次粘贴都是 +1 个对象",
       rw.get("pasteDeltas") == [1, 1], rw.get("pasteDeltas"))
    ck("J7 交叉：连按第二次 ⌘V 也是 +1",
       rw.get("pasteAgainDeltas") == [1, 1], rw.get("pasteAgainDeltas"))
    ck("J7 交叉：粘贴确实写历史（historyDelta=1）",
       rw.get("pasteHistoryDeltas") == [1, 1], rw.get("pasteHistoryDeltas"))
    ck("J7：产物 pasteDeltas / pasteAgainDeltas 与重算一致",
       f.get("pasteDeltas") == rw.get("pasteDeltas")
       and f.get("pasteAgainDeltas") == rw.get("pasteAgainDeltas"))
    ck("★ 前置：探针自报的 Δ 与我从 count/past 重算的 Δ 一致",
       rw.get("probeSelfDeltaAgrees") is True
       and rw.get("mouseSelfDeltaAgrees") is True,
       [rw.get("probeSelfDeltaAgrees"), rw.get("mouseSelfDeltaAgrees")])
    ck("J7：产物 keyboard764b 就是原始读数（两轮逐格相等）",
       f.get("keyboard764b") == [rw.get("keyboard", {}).get("r1"),
                                 rw.get("keyboard", {}).get("r2")],
       type(f.get("keyboard764b")).__name__)

    # J8
    ck("★ J8 交叉：空剪贴板粘贴的 disposition 是 NOOP",
       rw.get("emptyPasteNoop") is True, rw.get("emptyPaste"))
    ck("J8 交叉：空剪贴板粘贴对象数与历史都不动",
       all(x["countDelta"] == 0 and x["historyDelta"] == 0
           for x in rw.get("emptyPaste") or []))
    ck("★ J8：产物 emptyPasteDispositionNoop 与重算一致",
       f.get("emptyPasteDispositionNoop") is True)
    ck("★ J8：README 明确写了这**不是缺陷**", "不是缺陷" in R)

    # J9
    ck("★ J9 交叉：数值框里 ⌘C 完全没反应（标签都没换）",
       rw.get("copyFromFieldDead") is True,
       [x["copyFromField"] for x in rw.get("cases") or []])
    ck("★ J9 交叉：数值框里 ⌘V 完全没反应（Δ 全 0）",
       rw.get("pasteFromFieldDead") is True,
       [x["pasteFromField"] for x in rw.get("cases") or []])
    ck("★ J9 交叉：两轮逐字段一致",
       rw.get("casesAllEqual") is True)
    ck("★ J9：产物 copyFromFieldDead / pasteFromFieldDead 与重算一致",
       f.get("copyFromFieldDead") is True
       and f.get("pasteFromFieldDead") is True)
    ck("★ J9：产物 editableAllRoundsSame 与重算一致",
       f.get("editableAllRoundsSame") is True
       and f.get("editableAllRoundsSame") == rw.get("casesAllEqual"))
    ck("★ J9：判据 9 的 verdict 是 FAIL", J[8].get("verdict") == "FAIL")

    # J10
    ck("★ J10 交叉：按 ⌘C 前后 activeGesture 逐字符不变（D1 没拦）",
       rw.get("boundaryDidNotBlock") is True,
       [(x["copyFromField"]["gestureBefore"],
         x["copyFromField"]["gestureAfter"])
        for x in rw.get("cases") or []])
    ck("★ J10 交叉：对照组「树里 ⌘C」是成功的（所以不是环境问题）",
       rw.get("copyFromTreeWorks") is True)
    ck("★ J10：产物 boundaryDidNotBlockModifierKeys 与重算一致",
       f.get("boundaryDidNotBlockModifierKeys") is True)
    ck("★ J10：README 写明 D2 与 D1 是两个独立机制",
       "stopPropagation" in R and "isEditable" in R)

    # J11
    ck("J11 交叉：鼠标三枚按钮都点到过（copy/delete/clear 各 2 次）",
       len(rw.get("mouseActions") or []) == 6, rw.get("mouseActions"))
    ck("J11 交叉：copy 不改对象数、delete 减 1、clear 也不改对象数",
       [x["countDelta"] for x in rw.get("mouseActions") or []]
       == [0, 0, -1, 0, 0, -1],
       [(x["action"], x["countDelta"]) for x in rw.get("mouseActions") or []])
    ck("J11 交叉：delete 落 DELETE_OBJECTS、copy 落 COPY_SELECTION",
       [x["lastCommand"] for x in rw.get("mouseActions") or []]
       == ["COPY_SELECTION", "COPY_SELECTION", "DELETE_OBJECTS"] * 2,
       [x["lastCommand"] for x in rw.get("mouseActions") or []])
    def _proj(rows):
        return [{k: x.get(k) for k in ("action", "countDelta", "lastCommand")}
                for x in (rows or [])]
    ck("J11：产物 mouseActions 与重算一致（比对共有字段）",
       _proj(f.get("mouseActions")) == _proj(rw.get("mouseActions")),
       [_proj(f.get("mouseActions")), _proj(rw.get("mouseActions"))])

    # 前置守卫
    ck("★ 前置：764c 的五次 pick 失败被如实记账",
       len(rw.get("picksFailed") or []) == 5, rw.get("picksFailed"))
    ck("★ 前置：产物 picksFailedIn764c 与重算一致",
       f.get("picksFailedIn764c") == rw.get("picksFailed"))
    return checks


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
        badraw = copy.deepcopy(rw.get("__raw__") or {})
        if not badraw:
            cases.append({"name": name, "caught": False,
                          "firstFail": "拿不到原始读数副本"})
            return
        mutate(badraw)
        try:
            bad = raw_side_from(badraw)
            bad["__raw__"] = badraw
            failed = [c["label"] for c in run_checks(a, st, bad)
                      if not c["pass"]]
        except Exception as e:
            failed = ["重算抛错：%s" % e]
        cases.append({"name": name, "caught": len(failed) > 0,
                      "firstFail": failed[0] if failed else None})

    # —— 伪造「缺陷不存在」
    inj("★ 删掉 D1", lambda x: x.__setitem__("defects", [x["defects"][1]]))
    inj("★ 删掉 D2", lambda x: x.__setitem__("defects", [x["defects"][0]]))
    inj("★ 把 D2 降级成观察", lambda x: x.__setitem__(
        "observations", x["observations"] + [{"id": "O9", "text": "D2"}]))
    inj("★ 把 D2 的替代路径抹掉（那会让 D2 变严重）", lambda x:
        x["defects"][1].__setitem__("workaroundMeasured", ""))
    inj("★ 把 D2 的机制改回「就是 D1 那个 stopPropagation」", lambda x:
        x["defects"][1].__setitem__("mechanism",
                                    "边界在 Escape 与 ⌘C 上都 stopPropagation"))
    inj("★ 把 D1 的「更正 763」那段删掉", lambda x:
        x["defects"][0].__setitem__("widenedBy764", "和 763 一样，只有数值框"))
    inj("★ 把 D1 的「仍然未验证」三类控件删掉", lambda x:
        x["defects"][0].__setitem__("stillUnverified", ""))
    inj("★ 把 D1 说成「本批新发现」", lambda x:
        x["defects"][0].pop("carriedOverFrom", None))

    # —— 把 FAIL 偷偷改成 PASS（本批最需要防的一类）
    inj("★ 把 J5 从 FAIL 改成 PASS", lambda x:
        x["judgments"][4].__setitem__("verdict", "PASS"))
    inj("★ 把 J9 从 FAIL 改成 PASS", lambda x:
        x["judgments"][8].__setitem__("verdict", "PASS"))
    inj("★ 把不可比上下文从统计里悄悄删掉（让 J5 失去前提）", lambda x:
        x["findings"].__setitem__("incomparableLabels", []))
    inj("★ 把 camera:properties 从不可比挪进可比", lambda x:
        x["findings"]["incomparableLabels"].remove("camera:properties"))
    inj("★ 谎报 pick 失败次数（5 次说成 1 次）", lambda x:
        x["findings"].__setitem__("picksFailedIn764c", ["B_pickA"]))
    inj("★ 把 J5 的证据换成可比上下文（FAIL 失去支撑）", lambda x:
        x["judgments"][4].__setitem__("evidence",
                                      x["findings"]["comparableLabels"]))

    # —— 只改一份事实
    inj("只改 findings.boundaryCountComparable", lambda x:
        x["findings"].__setitem__("boundaryCountComparable", 9))
    inj("只改 findings.boundarySwallowedAll", lambda x:
        x["findings"].__setitem__("boundarySwallowedAll", False))
    inj("只改 findings.nonBoundaryNeverSwallowed", lambda x:
        x["findings"].__setitem__("nonBoundaryNeverSwallowed", False))
    inj("只改 findings.copyFromFieldDead", lambda x:
        x["findings"].__setitem__("copyFromFieldDead", False))
    inj("只改 findings.pasteFromFieldDead", lambda x:
        x["findings"].__setitem__("pasteFromFieldDead", False))
    inj("只改 findings.boundaryDidNotBlockModifierKeys", lambda x:
        x["findings"].__setitem__("boundaryDidNotBlockModifierKeys", False))
    inj("只改 findings.emptyPasteDispositionNoop", lambda x:
        x["findings"].__setitem__("emptyPasteDispositionNoop", False))
    inj("只改 findings.editableAllRoundsSame", lambda x:
        x["findings"].__setitem__("editableAllRoundsSame", False))
    inj("只改 findings.poseContext.boundaryCount（25 说成 9）", lambda x:
        x["findings"]["poseContext"].__setitem__("boundaryCount", 9))
    inj("只改 findings.boundaryTypesComparable（去掉 range）", lambda x:
        x["findings"].__setitem__("boundaryTypesComparable", ["number"]))
    inj("只改 findings.mouseActions 里的 delete 那一格", lambda x:
        x["findings"]["mouseActions"][2].__setitem__("countDelta", 0))
    inj("只改 findings.pasteDeltas", lambda x:
        x["findings"].__setitem__("pasteDeltas", [1, 0]))
    inj("只改 findings.emptyContexts（把空上下文抹掉）", lambda x:
        x["findings"].__setitem__("emptyContexts", []))
    inj("只改 findings.pathCreated（假装路径没建出来）", lambda x:
        x["findings"].__setitem__("pathCreated", None))

    # —— 改判据那一侧
    inj("把判据 2 的证据换成默认上下文（丢掉 25 个滑杆）", lambda x:
        x["judgments"][1].__setitem__("evidence", x["findings"]
                                      ["defaultContext"]))
    inj("删掉判据 6（未验证那三类）", lambda x: x.__setitem__(
        "judgments", [j for j in x["judgments"] if j["id"] != "J6"]))
    inj("把判据 id 从 J7 改成 J8（制造重号）", lambda x:
        x["judgments"][6].__setitem__("id", "J8"))
    inj("把判据 10 的 evidenceKey 指向不存在的键", lambda x:
        x["judgments"][9].__setitem__("evidenceKey", "noSuchKey"))

    # —— 元信息造假
    inj("把 srcModified 改成 true 之外的谎话", lambda x:
        x["env"].__setitem__("srcModified", "false"))
    inj("把 rawSha 删掉一份", lambda x: x.__setitem__(
        "rawSha", {k: v for k, v in list(x["rawSha"].items())[:2]}))
    inj("清空不声称清单", lambda x: x.__setitem__("notClaimed", []))
    inj("把不声称里的「没有测过」那条删掉", lambda x: x.__setitem__(
        "notClaimed", [s for s in x["notClaimed"] if "没有测过" not in s]))
    inj("删掉探针教训 R58（读标志顺序）", lambda x: x.__setitem__(
        "probeLessons", [l for l in x["probeLessons"] if l["id"] != "R58"]))
    inj("删掉观察 O2（抽屉互相遮挡）", lambda x: x.__setitem__(
        "observations", [o for o in x["observations"] if o["id"] != "O2"]))

    # —— 原始读数被改成「更好看」的样子
    def all_reach(x):
        for rd in x["vb764a"]["rounds"]:
            for c_ in rd["contexts"]:
                for rr in c_["rows"]:
                    if rr.get("skipped"):
                        continue
                    rr["esc"]["reachedWinBubble"] = True

    def hide_range(x):
        for rd in x["vb764a"]["rounds"]:
            for c_ in rd["contexts"]:
                for rr in c_["rows"]:
                    if rr["item"].get("type") == "range":
                        rr["esc"]["reachedWinBubble"] = True

    def make_comparable(x):
        a1 = x["vb764a"]["rounds"][0]["contexts"]
        a2 = x["vb764a"]["rounds"][1]["contexts"]
        m1 = {c["label"]: c for c in a1}
        for c in a2:
            s = m1.get(c["label"])
            if not s:
                continue
            c["totalFocusable"] = s["totalFocusable"]
            c["notClosed"] = s.get("notClosed")

    def fewer_controls(x):
        for rd in x["vb764a"]["rounds"]:
            for c_ in rd["contexts"]:
                c_["rows"] = c_["rows"][:3]

    def field_copy_alive(x):
        for rd in x["vb764c"]["rounds"]:
            rd["C_copyFromField"]["lastCommand"] = ["", "COPY_SELECTION"]
            rd["C_copyFromField"]["count"] = [7, 7]

    def field_paste_alive(x):
        for rd in x["vb764c"]["rounds"]:
            rd["D_paste"]["count"] = [5, 6]
            rd["D_paste"]["past"] = ["0", "1"]

    def gesture_moved(x):
        for rd in x["vb764c"]["rounds"]:
            rd["C_copyFromField"]["activeGestureBefore"] = "gesture-a"
            rd["C_copyFromField"]["activeGestureAfter"] = "gesture-b"

    def empty_paste_lies(x):
        for rd in x["vb764c"]["rounds"]:
            rd["A_emptyPaste"]["lastDisposition"] = ["", "COMMITTED"]
        for rd in x["vb764b"]["rounds"]:
            rd["C1_pasteWithEmptyClipboard"]["lastDisposition"] = [
                "", "COMMITTED"]

    def delete_does_nothing(x):
        for rd in x["vb764b"]["rounds"]:
            for k in ("C6_deleteButton",):
                if isinstance(rd.get(k), dict) and "count" in rd[k]:
                    rd[k]["count"] = [rd[k]["count"][0], rd[k]["count"][0]]

    def paste_noop(x):
        for rd in x["vb764b"]["rounds"]:
            for k in ("C3_paste", "C4_pasteAgain"):
                rd[k]["count"] = [5, 5]
                rd[k]["historyDelta"] = 0

    def path_never_built(x):
        x["vb764a"]["rounds"][0]["pathCreated"] = None

    inj_raw("伪造：所有边界控件都到达了 window 冒泡", all_reach)
    inj_raw("伪造：只有 number 中招、range 不中招", hide_range)
    inj_raw("伪造：把不可比的上下文说成可比", make_comparable)
    inj_raw("伪造：每个上下文只扫了 3 个控件", fewer_controls)
    inj_raw("伪造：数值框里 ⌘C 其实生效了", field_copy_alive)
    inj_raw("伪造：数值框里 ⌘V 其实生效了", field_paste_alive)
    inj_raw("伪造：按 ⌘C 时 gesture 变了（D1 确实拦了）", gesture_moved)
    inj_raw("伪造：空剪贴板粘贴的 disposition 是 COMMITTED", empty_paste_lies)
    inj_raw("伪造：delete 按钮其实没删", delete_does_nothing)
    inj_raw("伪造：粘贴其实没造对象", paste_noop)
    inj_raw("伪造：路径根本没建出来", path_never_built)

    # —— 静态层被改成「代码已经修好了」
    inj_static("伪造：边界里已经有「没有手势就放行」的守卫", lambda x:
               x.__setitem__("boundaryNoEscapeGuard", False))
    inj_static("伪造：边界不再 stopPropagation", lambda x:
               x.__setitem__("boundaryEscStopPropagation", False))
    inj_static("伪造：onFocus 不再 begin()", lambda x:
               x.__setitem__("boundaryOnFocusBegin", False))
    inj_static("伪造：边界对 Meta 键也 begin（D2 也会变成 D1 的锅）", lambda x:
               x.__setitem__("boundaryBeginSkipsModifierKeys", False))
    inj_static("伪造：isEditable 早退挪到了 ⌘C 分支之后（D2 已修）", lambda x:
               x.__setitem__("isEditableBeforeCopy", False))
    inj_static("伪造：copy 不再每条分支都写 lastCommandResult", lambda x:
               x.__setitem__("copyWritesLastResultEveryBranch", False))
    inj_static("伪造：copy 开始写历史了", lambda x:
               x.__setitem__("copyNeverWritesHistory", False))
    inj_static("伪造：树里少了一枚 action 按钮", lambda x:
               x.__setitem__("selectionActions", [True, True, False]))
    inj_static("伪造：时间轴没有路径预设钩子了", lambda x:
               x.__setitem__("pathPresetHook", False))
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
        {"label": "原始读数可用（raw/ 下 3 份）", "pass": False, "got": rawErr}]
    neg = [] if rawErr else negative_controls(a, st, rw)

    npass = sum(1 for c in checks if c["pass"])
    total = len(checks)
    neg_ok = sum(1 for n in neg if n["caught"])
    ok = npass == total and neg_ok == len(neg)

    REPORT.write_text(json.dumps(
        {"batch": 764, "checks": checks, "pass": npass, "total": total,
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
    print("batch 764 %s" % ("通过" if ok else "不通过"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
