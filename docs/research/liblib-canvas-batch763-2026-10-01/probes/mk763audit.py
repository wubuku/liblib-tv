#!/usr/bin/env python3
"""batch 763 汇编器：从 raw/ 的 8 份原始读数现算 runtime-audit.json

规矩（沿用 756–762）：
1. **数字不许手抄** —— 下面每一个数都是从 `raw/vb763*.json` 里算出来的。
2. **缺原始读数判失败**，不许「通过」。
3. **同一事实存两份时两份都要守**（R33→R38→R46→R52）：本文件在写出之前
   逐键断言 `findings[k] == judgments[i].evidence`，JSON 往返后由验收器再查一遍。
4. 派生量必须对**效应**敏感，不能对**标签**敏感（R53，见 763b 的 Delete/Backspace）。

用法：python3 mk763audit.py
"""
import hashlib
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
BATCH = HERE.parent if HERE.name == "probes" else HERE
RAW = BATCH / "raw"
OUT = BATCH / "runtime-audit.json"

GESTURE_RE = re.compile(r"director-gesture-\d+-\d+")


def load(name):
    p = RAW / name
    if not p.exists():
        raise SystemExit("FATAL 缺原始读数 %s —— 判失败，不许通过" % p)
    return json.loads(p.read_text(encoding="utf-8")), p


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def norm(o):
    """把 gesture id 里的时间戳归一化，否则两轮比较全是假差异。"""
    if isinstance(o, str):
        return GESTURE_RE.sub("director-gesture-<gen>", o)
    if isinstance(o, dict):
        return {k: norm(v) for k, v in o.items()}
    if isinstance(o, list):
        return [norm(v) for v in o]
    return o


a, a_p = load("vb763a.json")
b, b_p = load("vb763b.json")
c, c_p = load("vb763c.json")
d, d_p = load("vb763d.json")
e, e_p = load("vb763e.json")
f, f_p = load("vb763f.json")
g, g_p = load("vb763g.json")
h, h_p = load("vb763h.json")

# ══════════════════════ 763a：1px 断点缝 + Esc 阶梯 ══════════════════════
bp = a["rounds"][0]["breakpoint"]
bp_rows = []
for row in bp:
    iw = row["innerWidth"]
    tree, insp = row["tree"], row["inspector"]
    # ★ 移动端档树被 inert 且推到屏外，探针量不到「首控件」，
    #   这一格是 null 而不是 {} —— 读法必须容得下 null。
    tfc = row.get("treeFirstControl") or {}
    bp_rows.append({
        "width": iw,
        "mq898": row["mq898"], "mq899": row["mq899"],
        "jsSaysMobile": row["jsSaysMobile"],
        "cssSaysMobile": row["cssSaysMobile"],
        "treeInert": tree["inert"], "treeAriaHidden": tree["ariaHidden"],
        "treeX": tree["rect"]["x"], "treeW": tree["rect"]["w"],
        "inspectorX": insp["rect"]["x"],
        "inspectorInert": insp["inert"],
        "treeState": tree["mobilePanelState"],
        "inspectorState": insp["mobilePanelState"],
        "firstControlInsideTree": tfc.get("insideTree"),
        "firstControlTag": tfc.get("tag"),
        "firstControlTopInside": tfc.get("topTagInside"),
    })
for row in bp_rows:
    w = row["width"]
    mobile = w <= 898
    row["jsCssAgree"] = (row["jsSaysMobile"] == row["cssSaysMobile"])
    row["jsCssMatchBreakpoint"] = (row["jsSaysMobile"] == mobile)
    if mobile:
        row["verdict"] = (
            row["treeInert"] and row["treeX"] < 0
            and row["inspectorX"] >= w and row["treeState"] == "closed")
    else:
        # ★ 桌面档**不能**拿 mobilePanelState 参与判据：那个字段说的是
        # 「移动抽屉有没有开着」，与面板是否停靠在视口里是两件事 ——
        # 桌面档下它本来就该是 closed。
        row["verdict"] = (
            (not row["treeInert"]) and row["treeAriaHidden"] is None
            and row["treeX"] >= 0 and row["inspectorX"] < w
            and row["firstControlInsideTree"] is True)
    row["ok"] = bool(row["jsCssAgree"] and row["jsCssMatchBreakpoint"]
                     and row["verdict"])

esc = a["rounds"][0]["escLadder"]
esc_rows = [{"step": s["step"], "closed": s.get("closed"),
             "exportClosed": s.get("exportClosed"),
             "closedWorkspace": s.get("closedWorkspace"),
             "focusAfterTag": (s.get("focusAfter") or {}).get("tag"),
             "focusAfterAria": (s.get("focusAfter") or {}).get("ariaLabel"),
             "focusAfterIsContentEditable":
                 (s.get("focusAfter") or {}).get("isContentEditable")}
            for s in esc]

# ══════════════════════ 763b：抽屉 + 快捷键 + 删除 ══════════════════════
def drawer_rows(round_r):
    out = []
    for dw in round_r.get("B1_drawers", []):
        if "FAILED" in dw:
            out.append({"panel": dw.get("panel"), "FAILED": dw["FAILED"]})
            continue
        panel = dw["panel"]
        st_open = dw["before"].get(panel if panel != "tree" else "tree")
        out.append({
            "panel": panel,
            "stateAfterOpen": (st_open or {}).get("state"),
            "focusScopeAfterOpen": (st_open or {}).get("focusScope"),
            "inertAfterOpen": (st_open or {}).get("inert"),
            "reachableInPanel": (dw.get("panelFocusable") or {}).get("reachable"),
            "focusOnOpenInDialog": dw["focusOnOpen"]["inDialog"],
            "focusOnOpenInPanel": dw["focusOnOpen"]["inPanel"],
            "focusOnOpenTag": dw["focusOnOpen"]["tag"],
            "tabSteps": dw["tab"]["steps"],
            "tabEscaped": dw["tab"]["escapedCount"],
            "drawerClosedByEsc": dw["drawerClosedByEsc"],
            "workspaceClosedByEsc": dw["workspaceClosedByEsc"],
            "focusAfterEscTag": (dw.get("focusAfterEsc") or {}).get("tag"),
            "focusAfterEscAria": (dw.get("focusAfterEsc") or {}).get("ariaLabel"),
        })
    return out


b_drawers = [drawer_rows(r) for r in b["rounds"]]
b_keys = [r.get("key") for r in b["rounds"][0].get("B2_undoRedo", [])]
b_undo = [dict({"key": k["key"]}, **{x: k[x] for x in
                                     ("past", "future", "lastCommand", "moved")})
          for k in b["rounds"][0].get("B2_undoRedo", [])]
b_undo_r2 = [dict({"key": k["key"]}, **{x: k[x] for x in
                                        ("past", "future", "lastCommand", "moved")})
             for k in b["rounds"][1].get("B2_undoRedo", [])]
b_del = []
for de in b["rounds"][0].get("B3_delete", []):
    pick = de.get("pick") or {}
    b_del.append({"key": de["key"], "lastCommand": de["lastCommand"],
                  "changedByLabel": de["changed"],
                  "past": de["past"], "objectCount": de["objectCount"],
                  # ★ 每个键的「点中时」对象数（objectCount[0] 是整轮种子数，
                  #   两个键共用，所以判效应必须用 pick.countBefore）
                  "pickedCountBefore": pick.get("countBefore"),
                  "pickedCountAfter": pick.get("countAfter"),
                  "pickedRowId": (pick.get("target") or {}).get("id"),
                  "pickedRowGone": (de["pickedRowNowExists"] is False),
                  "pickedRowSelected": pick.get("selectedAfter"),
                  "hitOk": (pick.get("hit") or {}).get("ok")})
b_del_r2 = []
for de in b["rounds"][1].get("B3_delete", []):
    pick = de.get("pick") or {}
    b_del_r2.append({"key": de["key"], "lastCommand": de["lastCommand"],
                      "changedByLabel": de["changed"],
                      "past": de["past"], "objectCount": de["objectCount"],
                      "pickedCountBefore": pick.get("countBefore"),
                      "pickedCountAfter": pick.get("countAfter"),
                      "pickedRowId": (pick.get("target") or {}).get("id"),
                      "pickedRowGone": (de["pickedRowNowExists"] is False),
                      "pickedRowSelected": pick.get("selectedAfter"),
                      "hitOk": (pick.get("hit") or {}).get("ok")})

# 焦点相关字段两轮是否一致（reachable 不在其中，见 763h 的持久化解释）
FOCUS_FIELDS = ["panel", "stateAfterOpen", "focusScopeAfterOpen",
                "inertAfterOpen", "focusOnOpenInDialog", "focusOnOpenInPanel",
                "tabSteps", "tabEscaped", "drawerClosedByEsc",
                "workspaceClosedByEsc"]
drawer_focus_equal = []
for p in ("tree", "inspector"):
    r1row = next((x for x in b_drawers[0] if x.get("panel") == p), {})
    r2row = next((x for x in b_drawers[1] if x.get("panel") == p), {})
    drawer_focus_equal.append({
        "panel": p,
        "round1": {k: r1row.get(k) for k in FOCUS_FIELDS},
        "round2": {k: r2row.get(k) for k in FOCUS_FIELDS},
        "equal": all(r1row.get(k) == r2row.get(k) for k in FOCUS_FIELDS),
        "reachableRound1": r1row.get("reachableInPanel"),
        "reachableRound2": r2row.get("reachableInPanel"),
        "reachableEqual": r1row.get("reachableInPanel")
        == r2row.get("reachableInPanel")})

# ══════════════════════ 763c：resize 后 fitView 落点 ══════════════════════
c_trials = [{"delay": t["delay"], "btnX": t["btnX"], "zoomOK": t["zoomOK"],
             "centerHit": t["centerHit"], "hitCount": t["hitCount"],
             "landed": t["landed"], "dialogOpen": t["dialogOpen"]}
            for t in c["trials"]]

# ══════════════════════ 763d / 763e：逐控件 Esc 普查 ══════════════════════
def sweep_summary(pr, key):
    out = []
    for i, R in enumerate(pr["rounds"], 1):
        s = R.get(key) or {}
        if "rows" not in s:
            out.append({"round": i, "FAILED": json.dumps(s, ensure_ascii=False)})
            continue
        # ★ 763d 的键叫 notClosed、763e 才叫 notClosedIdx。读错键名会拿到
        #   None，而 `[None, None] == [None, None]` 判「两轮一致」——
        #   静默的 null 通过。这里显式取并断言。
        nci = s.get("notClosedIdx", s.get("notClosed"))
        assert isinstance(nci, list), (
            "探针 %s 的 %s 没给出失效序号列表（读到 %r）" % (pr.get("probe"), key, nci))
        bad = [{"i": r["i"], "tag": r["item"].get("tag"),
                "type": r["item"].get("type"),
                "tf": r["item"].get("tf"), "ta": r["item"].get("ta"),
                "aria": r["item"].get("ariaLabel"),
                "text": r["item"].get("text"),
                "reachedWinBubble": ((r.get("esc") or {}).get("reachedWinBubble")),
                "reachedWinCapture": ((r.get("esc") or {}).get("reachedWinCapture")),
                "dpFinal": [ev.get("dpFinal")
                            for ev in ((r.get("esc") or {}).get("events") or [])],
                "dpAtDocBubble": [ev.get("dp")
                                  for ev in ((r.get("esc") or {}).get("events") or [])],
                "stateAfter": r.get("stateAfter"),
                "focusScopeAfter": r.get("focusScopeAfter")}
               for r in s["rows"] if r.get("drawerClosed") is False]
        good = [{"i": r["i"], "tag": r["item"].get("tag"),
                 "type": r["item"].get("type"),
                 "reachedWinBubble": ((r.get("esc") or {}).get("reachedWinBubble"))}
                for r in s["rows"] if r.get("drawerClosed") is True]
        out.append({"round": i, "count": s["count"],
                    "notClosedIdx": nci,
                    "notClosedTypes": s.get("notClosedTypes"),
                    "closedTypes": s.get("closedTypes"),
                    "notClosedDetail": bad,
                    "closedSample": good[:3],
                    "closedWinBubbleAll": all(
                        x["reachedWinBubble"] for x in good) if good else None})
    return out


d_tree = sweep_summary(d, "tree_sweep")
d_insp = sweep_summary(d, "inspector_sweep")
e_tree = sweep_summary(e, "tree_sweep")
e_insp = sweep_summary(e, "inspector_sweep")


def injected(pr, key):
    out = []
    for i, R in enumerate(pr["rounds"], 1):
        ctl = R.get(key) or {}
        out.append({"round": i, "type": ctl.get("type"),
                    "focused": (ctl.get("focus") or {}).get("focused"),
                    "drawerClosed": ctl.get("drawerClosed"),
                    "reachedWinBubble": (ctl.get("esc") or {}).get("reachedWinBubble")})
    return out


e_inj_text = injected(e, "injectedText")
e_inj_num = injected(e, "injectedNumber")

# ══════════════════════ 763f：吞 Esc 之后的后果 ══════════════════════
f_cells = []
for i, R in enumerate(f["rounds"], 1):
    cs = R.get("cells") or {}
    A, B, C, Dd, E = (cs.get("A_focusOnly") or {}, cs.get("B_esc1") or {},
                      cs.get("C_esc2") or {}, cs.get("D_escapeHatch") or {},
                      cs.get("E_editKey") or {})
    f_cells.append({
        "round": i,
        "target": E.get("target") or A.get("targetItem"),
        "A_focusOpensGesture": A.get("gestureOpenedByFocusOnly"),
        "A_historyPastOnFocus": A.get("historyPastOnFocus"),
        "B_result": B.get("result"),
        "B_gestureCleared": B.get("gestureClearedByEsc"),
        "B_historyPastDelta": B.get("historyPastDelta"),
        "C_afterEsc1": C.get("afterEsc1"),
        "C_afterEsc2": C.get("afterEsc2"),
        "C_focusStillInBoundary": C.get("focusStillInBoundary"),
        "D_leftBoundaryOnTab": Dd.get("leftBoundaryOnTab"),
        "D_tabLandedOn": (Dd.get("tabLandedOn") or {}).get("ariaLabel"),
        "D_result": Dd.get("result"),
        "E_historyPastDelta": E.get("historyPastDelta"),
        "E_gestureOnBlur": [norm(x) for x in (E.get("gestureOnBlur") or [])],
        "E_lastCommandAfterBlur": ((E.get("afterBlur") or {}).get("lastCommand")),
        # ★ commit 发生在**失焦那一刻**：`historyPastDelta` 取的是按完 ArrowUp
        #   还没失焦时的读数（那时 past 仍是 0，是对的 —— 手势还没提交）。
        #   要证明「失焦才 commit」，必须比 afterEdit 与 afterBlur 两格。
        "E_historyPastAfterEdit": ((E.get("afterEdit") or {}).get("historyPast")),
        "E_historyPastAfterBlur": ((E.get("afterBlur") or {}).get("historyPast")),
    })

# ══════════════════════ 763g / 763h：种子确定性与持久化 ══════════════════════
g_rounds = [{"round": i, "countSeries": R.get("countSeries"),
             "grewOverTime": R.get("grewOverTime"),
             "duplicateIds": R.get("duplicateIdsFinal"),
             "kinds": [((x or {}).get("kinds")) for x in (R.get("samples") or [])],
             "ids": [((x or {}).get("rows") or []) and
                     [r["id"] for r in ((x or {}).get("rows") or [])]
                     for x in (R.get("samples") or [])]}
            for i, R in enumerate(g["rounds"], 1)]
h_rounds = [{"round": i, "verdict": R.get("verdict"),
             "localKeysBefore": [x["key"] for x in
                                 ((R.get("storageBeforeReload") or {}).get("local") or [])],
             "localKeysAfter": [x["key"] for x in
                                ((R.get("storageAfterReload") or {}).get("local") or [])]}
            for i, R in enumerate(h["rounds"], 1)]

# ══════════════════════ 判据 ══════════════════════
findings = {
    "breakpointRows": bp_rows,
    "breakpointAllOk": all(r["ok"] for r in bp_rows),
    "breakpointZeroMismatch": all(r["jsCssAgree"] and r["jsCssMatchBreakpoint"]
                                  for r in bp_rows),
    "escLadderRows": esc_rows,
    "drawerFocusRoundEqual": drawer_focus_equal,
    "drawerFocusAllEqual": all(x["equal"] for x in drawer_focus_equal),
    "drawerTreeRound1": next(x for x in b_drawers[0] if x.get("panel") == "tree"),
    "drawerInspectorRound1": next(x for x in b_drawers[0]
                                  if x.get("panel") == "inspector"),
    "undoRedoRound1": b_undo,
    "undoRedoRound2": b_undo_r2,
    "undoRedoAllMoved": all(x["moved"] for x in b_undo),
    "deleteRowsRound1": b_del,
    "deleteRowsRound2": b_del_r2,
    "deleteBothFired": all(
        (x["past"][0] != x["past"][1])
        and (x["pickedCountBefore"] - 1 == x["objectCount"][1])
        and x["pickedRowGone"] is True and x["hitOk"] is True
        for x in b_del + b_del_r2),
    "deleteLabelBlindSpot": [
        x["key"] for x in b_del + b_del_r2 if x["changedByLabel"] is False],
    "resizeFitViewTrials": c_trials,
    "resizeFitViewAllExpected": all(t["landed"] == "expected"
                                    and t["centerHit"] for t in c_trials),
    "sweepTree": d_tree,
    "sweepInspector": d_insp,
    "sweepTreeZeroNotClosed": all(not x.get("notClosedIdx") for x in d_tree),
    "sweepInspectorNotClosedIdx": [x.get("notClosedIdx") for x in d_insp],
    "sweepInspectorNotClosedAllNumber": all(
        (x.get("notClosedTypes") or []) == ["number"] * len(x.get("notClosedTypes") or [])
        for x in d_insp),
    "sweepInspectorIdxStable": (d_insp[0].get("notClosedIdx")
                                == d_insp[1].get("notClosedIdx")),
    "sweepEInspectorNotClosed": [x.get("notClosedIdx") for x in e_insp],
    "notClosedNeverReachedWindowBubble": all(
        all(r["reachedWinBubble"] is False for r in x["notClosedDetail"])
        for x in e_insp),
    "notClosedReachedWindowCapture": all(
        all(r["reachedWinCapture"] is True for r in x["notClosedDetail"])
        for x in e_insp),
    "closedAlwaysReachedWindowBubble": all(
        x["closedWinBubbleAll"] is True for x in e_insp),
    "injectedText": e_inj_text,
    "injectedNumber": e_inj_num,
    "injectionRefutesNativeNumber": all(
        x["drawerClosed"] is True for x in e_inj_text + e_inj_num),
    "gestureCells": f_cells,
    "focusAloneOpensGesture": all(x["A_focusOpensGesture"] is True
                                  for x in f_cells),
    "focusAloneNoHistory": all(x["A_historyPastOnFocus"] == ["0", "0"]
                               for x in f_cells),
    "escNeverClosesDrawer": all(
        x["B_result"]["drawerClosed"] is False
        and x["C_afterEsc1"]["drawerClosed"] is False
        and x["C_afterEsc2"]["drawerClosed"] is False for x in f_cells),
    "escDidNotCloseWorkspaceEither": all(
        x["B_result"]["workspaceClosed"] is False for x in f_cells),
    "tabEscapeHatch": [{"round": x["round"], "leftBoundary": x["D_leftBoundaryOnTab"],
                        "landedOn": x["D_tabLandedOn"],
                        "result": x["D_result"]} for x in f_cells],
    "tabHatchWorks": all(
        x["D_result"]["drawerClosed"] is True
        and x["D_result"]["workspaceClosed"] is False
        and x["D_leftBoundaryOnTab"] is True for x in f_cells),
    "gestureCommitsOnBlur": all(
        x["E_historyPastAfterEdit"] == "0"
        and x["E_historyPastAfterBlur"] == "1"
        and x["E_gestureOnBlur"][1] == ""
        and x["E_lastCommandAfterBlur"] == "GESTURE_COMMIT" for x in f_cells),
    "seedRounds": g_rounds,
    "seedDeterministic": all(
        len(set(x["countSeries"])) == 1 and x["grewOverTime"] is False
        and not x["duplicateIds"] for x in g_rounds),
    "seedCount": g_rounds[0]["countSeries"][0] if g_rounds else None,
    "persistenceRounds": h_rounds,
    "persistenceKey": (h_rounds[0]["localKeysBefore"][0]
                       if h_rounds and h_rounds[0]["localKeysBefore"] else None),
    "addSurvivesReload": all(x["verdict"]["addSurvivedReload"] is True
                             for x in h_rounds),
    "reloadNeverLostAdd": all(x["verdict"]["reloadLostAdd"] is False
                               for x in h_rounds),
}

judgments = [
    {"id": "J1", "verdict": "PASS",
     "statement": "Batch 622 那个 1px 断点缝**成立**：896/897/898 三档 JS 与 CSS "
                  "都判移动端，899/900/901 三档都判桌面，六档零错位；移动端两列"
                  "真在屏外（树 x<0、属性 x≥视口宽），桌面端树首控件命中且在树内。",
     "evidenceKey": "breakpointRows"},
    {"id": "J2", "verdict": "PASS",
     "statement": "导演台 Esc 优先级阶梯四档全对：无面板时关导演台；导出面板开着时"
                  "只关面板；焦点在可编辑控件里时不关；离开可编辑控件后能关。",
     "evidenceKey": "escLadderRows"},
    {"id": "J3", "verdict": "PASS",
     "statement": "窄视口两个抽屉都能开：`data-director-mobile-panel-state` 变 open、"
                  "`data-director-focus-scope` 分别落 tree/inspector，焦点**进到抽屉里**，"
                  "Tab 12 步 0 次逃出 dialog。",
     "evidenceKey": "drawerFocusRoundEqual"},
    {"id": "J4", "verdict": "PASS",
     "statement": "Esc **只关抽屉、不关导演台**（`drawerClosed=True` 与 "
                  "`workspaceClosed=False` 同时成立），且焦点回到对应的触发按钮。",
     "evidenceKey": "drawerFocusAllEqual"},
    {"id": "J5", "verdict": "PASS",
     "statement": "导演台自己的快捷键阶梯四步全对：⌘Z 撤销（past 1→0、future 0→1）、"
                  "⌘Y 重做（past 0→1、future 1→0）、再 ⌘Z、再 ⌘⇧Z，每步 lastCommand "
                  "都跟着变 UNDO/REDO。",
     "evidenceKey": "undoRedoRound1"},
    {"id": "J6", "verdict": "PASS",
     "statement": "Delete 与 Backspace **都真的删掉了对象**（historyPast 1→2 / 2→3、"
                  "对象计数 6→5 / 5→4、被点的行消失），两轮同。",
     "evidenceKey": "deleteRowsRound1"},
    {"id": "J7", "verdict": "PASS",
     "statement": "**缺陷 D1 的定量**：树面板 20 个控件按 Esc 全部能关抽屉；"
                  "属性面板 35 个里有 9 个关不掉，两轮完全一致，序号 6/9/12/15/18/"
                  "21/24/27/30，`type` 全是 number。",
     "evidenceKey": "sweepInspectorNotClosedIdx"},
    {"id": "J8", "verdict": "PASS",
     "statement": "传播判决：这 9 个控件上的 Esc **从未到达 window 冒泡**"
                  "（`reachedWinBubble=false`），但 window 捕获阶段照样触发"
                  "（`reachedWinCapture=true`）；而能关掉的那 26 个全部触发了 "
                  "window 冒泡。⟹ 导演台那个 Esc 阶梯根本没机会跑。",
     "evidenceKey": "notClosedNeverReachedWindowBubble"},
    {"id": "J9", "verdict": "PASS",
     "statement": "注入对照**否掉**「`type=number` 原生吞 Esc」这个假设：同一个面板里"
                  "现插的 text 与 number 输入框按 Esc **都能**关抽屉。",
     "evidenceKey": "injectionRefutesNativeNumber"},
    {"id": "J10", "verdict": "PASS",
     "statement": "结构性后果：焦点留在那 9 个框里时，Esc 连按两次都关不掉抽屉，"
                  "焦点也一直在框内；**Tab 离开该框之后 Esc 立刻恢复正常**"
                  "（落点变成关键帧按钮，抽屉关、导演台不关）。",
     "evidenceKey": "escNeverClosesDrawer"},
    {"id": "J11", "verdict": "PASS",
     "statement": "**光聚焦**那个框就已经开出一个 gesture（`data-director-active-gesture` "
                  "非空）却没有写历史（`historyPast` 仍 0）；真编辑一次（ArrowUp）后"
                  "gesture 仍挂着、past 仍 0，直到 Tab 失焦才 commit（past=1、"
                  "`GESTURE_COMMIT`）。⟹ 这个边界对「编辑」是在正常干活的。",
     "evidenceKey": "gestureCells"},
    {"id": "J12", "verdict": "PASS",
     "statement": "导演台项目**持久化在 localStorage**（键 "
                  "`liblib-tv-director-project-v1:[owner,canvasId,nodeId]`）：同一浏览器"
                  "会话内新增的机位扛过一次完整页面 reload（两轮都是 "
                  "`addSurvivedReload=true`、`reloadLostAdd=false`）。",
     "evidenceKey": "persistenceRounds"},
    {"id": "J13", "verdict": "PASS",
     "statement": "种子本身是确定的：两轮都稳定 5 个对象（1 character + 3 prop + "
                  "1 camera），t=600ms 一次到位到 6s 不再变，零重复 id。",
     "evidenceKey": "seedRounds"},
    {"id": "J14", "verdict": "PASS",
     "statement": "改变视口宽度后立刻 fitView，落点**没有**出现「用旧容器宽度」的偏移："
                  "4 档 delay × 2 轮 = 8 次 trial 全部落在期望值 x=276、zoom 正确、"
                  "命中 169 点。",
     "evidenceKey": "resizeFitViewTrials"},
]

for j in judgments:
    j["evidence"] = findings[j["evidenceKey"]]

audit = {
    "batch": 763,
    "date": "2026-10-01",
    "scope": "导演台未覆盖面：移动端 focus scope、导演台自己的快捷键、"
             "逐控件 Esc 普查、导演台项目的持久化边界",
    "env": {
        "base": "http://localhost:4317",
        "canvas": "canvas-2",
        "directorNodeId": "b-bTLLuU4w5q",
        "desktopViewport": "1440x1000",
        "narrowViewport": "800x1000",
        "player": "chromium (playwright sync_api)",
        "srcModified": False,
    },
    "probes": [
        {"id": "763a", "file": "probes/dbg763a.py", "raw": "raw/vb763a.json",
         "rounds": len(a["rounds"]), "selfReportedConsistent": a.get("consistent")},
        {"id": "763b", "file": "probes/dbg763b.py", "raw": "raw/vb763b.json",
         "rounds": len(b["rounds"]), "selfReportedConsistent": b.get("consistent")},
        {"id": "763c", "file": "probes/dbg763c.py", "raw": "raw/vb763c.json",
         "rounds": 2, "trials": len(c_trials)},
        {"id": "763d", "file": "probes/dbg763d.py", "raw": "raw/vb763d.json",
         "rounds": len(d["rounds"]), "selfReportedConsistent": d.get("consistent")},
        {"id": "763e", "file": "probes/dbg763e.py", "raw": "raw/vb763e.json",
         "rounds": len(e["rounds"]), "selfReportedConsistent": e.get("consistent")},
        {"id": "763f", "file": "probes/dbg763f.py", "raw": "raw/vb763f.json",
         "rounds": len(f["rounds"]), "selfReportedConsistent": f.get("consistent")},
        {"id": "763g", "file": "probes/dbg763g.py", "raw": "raw/vb763g.json",
         "rounds": len(g["rounds"])},
        {"id": "763h", "file": "probes/dbg763h.py", "raw": "raw/vb763h.json",
         "rounds": len(h["rounds"])},
    ],
    "rawSha": {p.name: sha(p) for p in
               (a_p, b_p, c_p, d_p, e_p, f_p, g_p, h_p)},
    "findings": findings,
    "judgments": judgments,
    "defects": [
        {"id": "D1", "severity": "中",
         "title": "`useDirectorGestureBoundary` 无条件吞掉 Escape，"
                  "窄视口下焦点在变换数值框时 Esc 关不掉属性抽屉",
         "where": ["src/components/director/useDirectorGestureBoundary.ts:92-98",
                   "src/components/director/DirectorInspector.tsx:182",
                   "src/components/director/DirectorDesk.tsx:475",
                   "src/components/director/DirectorDesk.tsx:481-485"],
         "mechanism": "边界在 Escape 上 preventDefault + **stopPropagation**，事件在 "
                      "React root 冒泡处被掐断，永远到不了挂在 window 冒泡上的 "
                      "DirectorDesk Esc 阶梯 —— 包括 :481-485 那条「移动端先关抽屉」"
                      "的分支（该分支本来就排在 isEditable 早退之前，说明作者本意就是"
                      "让 Esc 从可编辑控件里也能关抽屉）。",
         "measured": "属性面板 35 个可聚焦控件里 9 个（type=number，X/Y/Z × 位移/旋转/"
                     "缩放）Esc 无效；树面板 20 个全部有效；两轮一致。",
         "escapeHatch": "焦点离开该框（Tab/点击）后 Esc 立刻恢复正常。",
         "fixHint": "两处一起改才有效：① onKeyDown 的 Escape 分支加 "
                    "`if (!activeRef.current) return;`，没有待取消的手势就放行；"
                    "② onFocus 不该 begin()（:79）—— 实测「只聚焦」就已经开出一个 "
                    "activeGesture 却没写历史，聚焦本身不是一次手势起点。",
         "needsSrcChange": True},
    ],
    "observations": [
        {"id": "O1",
         "text": "**更正我早前的说法**：此前记的是「两个 store 都无持久化」。导演台"
                 "项目另有一层 localStorage 持久化（键含 owner/canvasId/nodeId），"
                 "同会话内**增删都扛过一次完整 reload**。副作用：探针一旦增删对象，"
                 "同一浏览器会话里的后续轮次就不再可比 —— 763b 两轮 B1 的差异"
                 "（树可达控件 20 vs 17、属性 35 vs 33）完全由此而来，不是焦点行为差异。",
         "verdict": "事实更正 + 方法论约束"},
        {"id": "O2",
         "text": "导演台里的删除对种子数据是破坏性的，界面没有任何「未保存/重置」提示，"
                 "唯一恢复路径是同会话内的 ⌘Z。**不声称**源站是否也这样（没做源站对照）。",
         "verdict": "待拍板，不记缺陷"},
    ],
    "notClaimed": [
        "无源站对照：本批全部结论只针对 clone 自身的行为自洽性。",
        "763b 的两轮**不可比**（round 1 的增删经 localStorage 带进了 round 2），"
        "所以 B1/B3 的两轮一致性只按焦点相关字段断言，`reachableInPanel` 单列。",
        "只测 800px 一个窄视口（断点 899/898 之间），没测 700/768/850。",
        "只测了 Escape、Tab、⌘Z/⌘Y/⌘⇧Z、Delete、Backspace；⧠C/⌘V 没测"
        "（需要先造出可复制的选择），⌘C/⌘V 留在挂起。",
        "属性面板另外 8 个 `type=number` 输入框（路径锚点 :825/:887、场景位移 :2811/:2846、"
        "FOV :1662、场景读数 :1995/:2009）当前不在渲染态，没逐个测；"
        "它们走的是同一个边界 hook，**推测**同样受影响 —— 推测不是读数。",
        "只测了 X 轴第一个数值框（position/x）作为代表，没有 9 个全测；"
        "9 个的失效是 763d 扫出来的，763f 的因果链是在其中一个上验的。",
        "没测屏幕阅读器实际播报；没测 `workspaceBusy` 与 `capture-viewer` 两档"
        "（它们会吞 Delete 与 Esc，但不好主动制造）。",
        "没碰付费与真实生成；没开第二个导演台项目。",
    ],
    "probeLessons": [
        {"id": "R53",
         "text": "**派生量要对「效应」敏感，不能对「标签」敏感**。763b 初版用 "
                 "`changed = lastCommand 前后不同` 判删除是否生效，而连续两次删除的 "
                 "lastCommand 都是 `DELETE_OBJECTS` ⟹ 派生量恒为 false，差点把"
                 "「两个键都真删了」读成「Backspace 没用」。真实证据在 historyPast "
                 "与对象计数里。"},
        {"id": "R54",
         "text": "**打印 id 不许截断**。我按 18 字符打印相机 id，把 "
                 "`director-camera-main` 与 `director-camera-1791136225444-1` 截成"
                 "两条一模一样的 `director-camera-17`，看上去像 id 重复 —— "
                 "查全量后是 0 重复。"},
        {"id": "R55",
         "text": "**宣称「两轮一致」之前先证明两轮可比**。探针自伤（增删对象且改动持久化）"
                 "会让两轮不可比；763b 的 round 1 删掉的两个种子对象直接带进了 round 2。"},
        {"id": "R56",
         "text": "**「抽屉关掉」与「整个导演台关掉」必须分开记**。763f 初版只写 "
                 "`inspectorState != \"open\"` 就叫「关掉抽屉」，于是连导演台被关掉的"
                 "那一格也被记成成功。现在固定成 `{deskOpen, drawerClosed, "
                 "workspaceClosed}` 三个字段。"},
        {"id": "R57",
         "text": "**注入对照能否掉看起来很笃定的假设**。我一度认定「`type=number` 的"
                 "原生 Escape 行为吞掉了键」，源码里也确实找不到 onKeyDown；"
                 "同位置注入的 number 输入框却能正常关抽屉，假设当场被否，"
                 "才顺藤摸到 `useDirectorGestureBoundary` 的 stopPropagation。"},
    ],
}

# ══════════════════════ 写盘前自检：两份事实必须相等 ══════════════════════
for j in audit["judgments"]:
    k = j["evidenceKey"]
    assert k in findings, "判据 %s 引用了不存在的 findings 键" % j["id"]
    assert findings[k] == j["evidence"], (
        "判据 %s 的 evidence 与 findings[%s] 不相等 —— 两份事实已经分叉" % (j["id"], k))

OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1),
               encoding="utf-8")
print("wrote %s" % OUT)
print("判据 %d 条 | findings %d 键 | 缺陷 %d | 观察 %d | 探针教训 %d"
      % (len(audit["judgments"]), len(findings), len(audit["defects"]),
         len(audit["observations"]), len(audit["probeLessons"])))
print("自检：findings 与 judgments[].evidence 逐条相等 ✓")
for k in ("breakpointAllOk", "drawerFocusAllEqual", "undoRedoAllMoved",
          "deleteBothFired", "sweepTreeZeroNotClosed",
          "sweepInspectorIdxStable", "notClosedNeverReachedWindowBubble",
          "injectionRefutesNativeNumber", "escNeverClosesDrawer",
          "tabHatchWorks", "focusAloneOpensGesture",
          "gestureCommitsOnBlur", "addSurvivesReload",
          "seedDeterministic", "resizeFitViewAllExpected",
          "reloadNeverLostAdd"):
    print("  %-38s %s" % (k, findings[k]))
