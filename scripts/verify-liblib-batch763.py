"""batch 763 验收器：导演台未覆盖面（移动端 focus scope / 快捷键 / 逐控件 Esc）

三层结构（与 753–762 同）：
  1. **静态层** —— 直接从 `src/` 复核判据与缺陷依赖的实现事实，
     包括「移动端关抽屉那一档**排在** isEditable 早退之前」这种**顺序**断言
  2. **产物层** —— 判据条数、探针轮次、缺陷/观察/教训条目、README 结构、
     台账行、以及**表格首格不许是裸数字**（pre-commit 钩子的正则）
  3. **原始读数交叉核对** —— 从 `docs/research/.../raw/` 的 8 份原始输出
     **按正确键名重算**全部派生量，与产物逐项对账；缺失时**判失败而不是通过**。

⚠ 本批盯住两件容易自欺的事：
  - **763b 的两轮不可比**（探针自伤：round 1 删的种子对象经 localStorage 带进
    round 2）。产物必须**如实**标注这件事，不许把 B1 的两轮说成一致。
  - **763f 的 `consistent=false` 只是 gesture id 里的时间戳**（R53–R57 里的
    归一化问题）。验收器按归一化后的读数判断，不按探针自报的那个布尔。

判据 **14 条**。
"""
import copy
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch763-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAWDIR = OUTDIR / "raw"
PROBEDIR = OUTDIR / "probes"
README = OUTDIR / "README.md"
LEDGER = ROOT / "docs/research/VERIFICATION_LEDGER.md"

RAW_FILES = ["vb763a.json", "vb763b.json", "vb763c.json", "vb763d.json",
             "vb763e.json", "vb763f.json", "vb763g.json", "vb763h.json"]
PROBE_FILES = ["dbg763a.py", "dbg763b.py", "dbg763c.py", "dbg763d.py",
               "dbg763e.py", "dbg763f.py", "dbg763g.py", "dbg763h.py",
               "mk763audit.py"]
GESTURE_RE = re.compile(r"director-gesture-\d+-\d+")
BARE_NUM_CELL = re.compile(r"^\|\s*\d+[a-z]?\s*\|")


def src(p):
    return (ROOT / p).read_text(encoding="utf-8")


def static_side():
    boundary = src("src/components/director/useDirectorGestureBoundary.ts")
    insp = src("src/components/director/DirectorInspector.tsx")
    desk = src("src/components/director/DirectorDesk.tsx")
    store = src("src/store/directorStore.ts") if (
        ROOT / "src/store/directorStore.ts").exists() else ""

    esc_branch = boundary.find('if (event.key === "Escape")')
    esc_tail = boundary[esc_branch:esc_branch + 220] if esc_branch >= 0 else ""
    on_focus = boundary.find("onFocus: begin")
    # ★ 这个守卫串在 commit()(:57) 与 cancel()(:63) 里**本来就有**，
    #   搜整份文件会误判成「已经修好」。必须只搜 onKeyDown 那一段。
    keydown_at = boundary.find("onKeyDown:")
    keydown_block = (boundary[keydown_at:keydown_at + 700]
                     if keydown_at >= 0 else "")

    # ★ 顺序断言：移动端关抽屉那一档必须排在 isEditable 早退**之前**
    mobile_esc = desk.find('event.key === "Escape" && activeMobilePanel')
    is_editable = desk.find("if (isEditable) return;")
    desk_listener = desk.find('window.addEventListener("keydown", handleKeyDown)')

    # 这个 hook 一共被几处用（缺陷影响面）
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
        "boundaryEscBranch": esc_branch >= 0,
        "boundaryEscPreventDefault": "event.preventDefault();" in esc_tail,
        "boundaryEscStopPropagation": "event.stopPropagation();" in esc_tail,
        "boundaryEscCancel": "cancel();" in esc_tail,
        "boundaryOnFocusBegin": on_focus >= 0,
        "boundaryNoUnconditionalEscapeGuard": (
            "if (!activeRef.current) return;" not in keydown_block
            and "if (!activeRef.current) return;" not in esc_tail),
        "inspSpreadsGestureOnNumberInput": (
            "data-director-transform-field={field}" in insp
            and "{...(isAxisDisabled(index) ? {} : gesture)}" in insp),
        "inspNumberInputType": 'type="number"' in insp,
        "deskListenerOnWindow": desk_listener >= 0,
        "mobileEscBeforeIsEditable": (
            0 <= mobile_esc < is_editable and is_editable >= 0),
        "boundaryUsers": users,
        "boundaryUserCount": sum(u["count"] for u in users),
        "persistenceKeyInSrc": "liblib-tv-director-project-v1" in (
            store + "".join(
                (ROOT / p).read_text(encoding="utf-8")
                for p in [q for q in (ROOT / "src").rglob("*.ts*")
                          if "director" in q.name.lower()]
                if True)),
    }


def load_raw():
    """缺文件 → 抛错 → 判失败而不是通过。"""
    miss = [f for f in RAW_FILES if not (RAWDIR / f).exists()]
    if miss:
        raise RuntimeError("缺原始读数 %s" % miss)
    return {f[:-5]: json.loads((RAWDIR / f).read_text(encoding="utf-8"))
            for f in RAW_FILES}


def raw_side():
    r = load_raw()
    out = raw_side_from(r)
    out["__raw__"] = r          # 供阴性对照改原始读数后重算
    return out


def raw_side_from(r):
    """按正确键名从 8 份原始读数重算全部派生量。"""
    out = {"filesOk": True}
    out["rawRounds"] = {
        "763a": len(r["vb763a"]["rounds"]), "763b": len(r["vb763b"]["rounds"]),
        "763c": r["vb763c"].get("rounds"), "763d": len(r["vb763d"]["rounds"]),
        "763e": len(r["vb763e"]["rounds"]), "763f": len(r["vb763f"]["rounds"]),
        "763g": len(r["vb763g"]["rounds"]), "763h": len(r["vb763h"]["rounds"])}

    # —— 763a 断点缝
    bp = []
    for row in r["vb763a"]["rounds"][0]["breakpoint"]:
        w = row["innerWidth"]
        t, i = row["tree"], row["inspector"]
        tfc = row.get("treeFirstControl") or {}
        mobile = w <= 898
        bp.append({
            "width": w,
            "jsCssAgree": row["jsSaysMobile"] == row["cssSaysMobile"],
            "jsCssMatchBreakpoint": row["jsSaysMobile"] == mobile,
            "mobileVerdict": (t["inert"] and t["rect"]["x"] < 0
                              and i["rect"]["x"] >= w),
            "desktopVerdict": ((not t["inert"]) and t["ariaHidden"] is None
                               and t["rect"]["x"] >= 0
                               and i["rect"]["x"] < w
                               and tfc.get("insideTree") is True)})
    out["breakpointOk"] = all(
        x["jsCssAgree"] and x["jsCssMatchBreakpoint"]
        and (x["mobileVerdict"] if x["width"] <= 898 else x["desktopVerdict"])
        for x in bp)
    out["breakpointWidths"] = [x["width"] for x in bp]
    out["escLadderSteps"] = [s["step"]
                             for s in r["vb763a"]["rounds"][0]["escLadder"]]

    # —— 763b 抽屉（焦点相关字段）
    FOCUS_FIELDS = ["panel", "stateAfterOpen", "focusScopeAfterOpen",
                    "inertAfterOpen", "focusOnOpenInDialog", "focusOnOpenInPanel",
                    "tabSteps", "tabEscaped", "drawerClosedByEsc",
                    "workspaceClosedByEsc"]

    def rows(rd):
        o = []
        for dw in rd.get("B1_drawers", []):
            if "FAILED" in dw:
                o.append({"panel": dw.get("panel"), "FAILED": dw["FAILED"]})
                continue
            p = dw["panel"]
            st = dw["before"].get(p) or {}
            o.append({"panel": p, "stateAfterOpen": st.get("state"),
                      "focusScopeAfterOpen": st.get("focusScope"),
                      "inertAfterOpen": st.get("inert"),
                      "focusOnOpenInDialog": dw["focusOnOpen"]["inDialog"],
                      "focusOnOpenInPanel": dw["focusOnOpen"]["inPanel"],
                      "tabSteps": dw["tab"]["steps"],
                      "tabEscaped": dw["tab"]["escapedCount"],
                      "drawerClosedByEsc": dw["drawerClosedByEsc"],
                      "workspaceClosedByEsc": dw["workspaceClosedByEsc"],
                      "reachableInPanel": (dw.get("panelFocusable")
                                           or {}).get("reachable")})
        return o

    r1d, r2d = rows(r["vb763b"]["rounds"][0]), rows(r["vb763b"]["rounds"][1])
    out["drawerFocusEqual"] = [
        {"panel": p,
         "equal": all(
             (next((x for x in r1d if x.get("panel") == p), {}).get(k)
              == next((x for x in r2d if x.get("panel") == p), {}).get(k))
             for k in FOCUS_FIELDS),
         "reachableRound1": next((x for x in r1d if x.get("panel") == p), {}
                                 ).get("reachableInPanel"),
         "reachableRound2": next((x for x in r2d if x.get("panel") == p), {}
                                 ).get("reachableInPanel")}
        for p in ("tree", "inspector")]
    out["drawerFocusAllEqual"] = all(x["equal"]
                                     for x in out["drawerFocusEqual"])
    out["reachableDiffersAcrossRounds"] = any(
        x["reachableRound1"] != x["reachableRound2"]
        for x in out["drawerFocusEqual"])

    # —— 763b 快捷键
    for tag, rd in (("undoRedo1", r["vb763b"]["rounds"][0]),
                    ("undoRedo2", r["vb763b"]["rounds"][1])):
        ks = rd.get("B2_undoRedo", [])
        out[tag + "Keys"] = [k["key"] for k in ks]
        # ★ 判**方向**而不是判「有没有变」：撤销必须 past-1 且 future+1，
        #   重做必须 past+1 且 future-1。用「变了没有」这种判法，
        #   只改一格就能蒙过去（阴性对照抓的就是这个）。
        def _dir_ok(k):
            try:
                p0, p1 = int(k["past"][0]), int(k["past"][1])
                f0, f1 = int(k["future"][0]), int(k["future"][1])
            except (TypeError, ValueError):
                return False
            if k["key"] == "Cmd+Z":
                return (p1 == p0 - 1 and f1 == f0 + 1)
            if k["key"] in ("Cmd+Y", "Cmd+Shift+Z"):
                return (p1 == p0 + 1 and f1 == f0 - 1)
            return False

        out[tag + "AllMoved"] = bool(ks) and all(_dir_ok(k) for k in ks)
        out[tag + "DirDetail"] = [k["key"] for k in ks if not _dir_ok(k)]
        out[tag + "LastCommands"] = [k["lastCommand"] for k in ks]
        out[tag + "LastCommandsAfter"] = [k["lastCommand"][1] for k in ks]

    # —— 763b 删除（判效应，不判标签）
    dele = []
    for rd in r["vb763b"]["rounds"]:
        for de in rd.get("B3_delete", []):
            pick = de.get("pick") or {}
            objs_after = de.get("objectsAfter")
            final = len(objs_after) if isinstance(objs_after, list) else None
            dele.append({
                "key": de["key"],
                "pastMoved": de["past"][0] != de["past"][1],
                "pickedCountBefore": pick.get("countBefore"),
                "finalCount": final,
                "countDroppedByOne": (isinstance(final, int)
                                      and pick.get("countBefore") is not None
                                      and pick["countBefore"] - 1 == final),
                "rowGone": de["pickedRowNowExists"] is False,
                "labelChanged": de["changed"],
                "hitOk": (pick.get("hit") or {}).get("ok")})
    out["deleteRows"] = dele
    out["deleteBothFired"] = bool(dele) and all(
        x["pastMoved"] and x["countDroppedByOne"] and x["rowGone"]
        and x["hitOk"] for x in dele)
    out["deleteLabelBlindRow"] = [x["key"] for x in dele
                                 if x["labelChanged"] is False]

    # —— 763c resize 后 fitView
    ts = r["vb763c"]["trials"]
    out["resizeTrials"] = len(ts)
    out["resizeAllExpected"] = all(t["landed"] == "expected"
                                   and t["centerHit"] for t in ts)
    out["resizeBtnXs"] = sorted({t["btnX"] for t in ts})

    # —— 763d / 763e 逐控件 Esc
    def sweep(pr, key):
        o = []
        for i, R in enumerate(pr["rounds"], 1):
            s = R.get(key) or {}
            if "rows" not in s:
                o.append({"round": i, "FAILED": True})
                continue
            def escfield(row, key):
                # ★ 763d 的行里 esc 是**列表**（原始记录），
                #   763e 才是带 reachedWinBubble 的字典。两种形状都要容得下。
                e = row.get("esc")
                return e.get(key) if isinstance(e, dict) else None

            def escdp(row):
                e = row.get("esc")
                if isinstance(e, dict):
                    return [x.get("dpFinal") for x in (e.get("events") or [])]
                if isinstance(e, list):
                    return [x.get("dpFinal") for x in e]
                return None

            bad = []
            for row in s["rows"]:
                # ★ 763d 的行用 panelClosed、763e 才用 drawerClosed。
                #   读错键名会让 bad 变空列表，而 all([]) 是 True —— 静默通过。
                if row.get("drawerClosed", row.get("panelClosed")) is not False:
                    continue
                bad.append({
                    "i": row["i"], "type": row["item"].get("type"),
                    "tf": row["item"].get("tf"),
                    "ta": row["item"].get("ta"),
                    "reachedWinBubble": escfield(row, "reachedWinBubble"),
                    "reachedWinCapture": escfield(row, "reachedWinCapture"),
                    "dpFinal": escdp(row),
                    "stateAfter": row.get("stateAfter")})
            good = [row for row in s["rows"]
                    if row.get("drawerClosed", row.get("panelClosed")) is True]
            bub = [escfield(g, "reachedWinBubble") for g in good]
            nci = s.get("notClosedIdx", s.get("notClosed"))
            o.append({"round": i, "count": s["count"],
                      "notClosedIdx": nci,
                      "notClosedTypes": sorted({b["type"] for b in bad}),
                      "bad": bad, "goodCount": len(good),
                      # 763d 没有这个埋点，值会是 None —— 交叉核对只对 763e 断言
                      "closedAllReachedWinBubble": (
                          (all(bub) and None not in bub) if bub else None)})
        return o

    out["treeSweep"] = sweep(r["vb763d"], "tree_sweep")
    out["inspSweepD"] = sweep(r["vb763d"], "inspector_sweep")
    out["inspSweepE"] = sweep(r["vb763e"], "inspector_sweep")
    out["treeZeroNotClosed"] = all(not x.get("notClosedIdx")
                                   for x in out["treeSweep"])
    out["inspNotClosedIdx"] = [x.get("notClosedIdx") for x in out["inspSweepD"]]
    out["inspNotClosedStable"] = (out["inspSweepD"][0].get("notClosedIdx")
                                  == out["inspSweepD"][1].get("notClosedIdx"))
    out["inspNotClosedAllNumber"] = all(
        (x.get("notClosedTypes") or []) and
        all(t == "number" for t in x["notClosedTypes"])
        for x in out["inspSweepD"])
    out["badNeverReachedWinBubble"] = all(
        b["reachedWinBubble"] is False
        for x in out["inspSweepE"] for b in x["bad"])
    out["badReachedWinCapture"] = all(
        b["reachedWinCapture"] is True
        for x in out["inspSweepE"] for b in x["bad"])
    out["closedAllReachedWinBubble"] = all(
        x["closedAllReachedWinBubble"] is True for x in out["inspSweepE"])
    out["notClosedCount"] = len(out["inspSweepD"][0].get("bad") or [])

    # —— 763e 注入对照
    def inj(pr, key):
        return [{"round": i, "type": (R.get(key) or {}).get("type"),
                 "drawerClosed": (R.get(key) or {}).get("drawerClosed"),
                 "focused": ((R.get(key) or {}).get("focus") or {}).get(
                     "focused"),
                 "reachedWinBubble": ((R.get(key) or {}).get("esc") or {}
                                      ).get("reachedWinBubble")}
                for i, R in enumerate(pr["rounds"], 1)]

    out["injectedText"] = inj(r["vb763e"], "injectedText")
    out["injectedNumber"] = inj(r["vb763e"], "injectedNumber")
    out["injectionAllClosed"] = all(
        x["drawerClosed"] is True and x["focused"] is True
        for x in out["injectedText"] + out["injectedNumber"])

    # —— 763f 后果
    cells = []
    for i, R in enumerate(r["vb763f"]["rounds"], 1):
        cs = R.get("cells") or {}
        A, B, C, D2, E = (cs.get("A_focusOnly") or {}, cs.get("B_esc1") or {},
                          cs.get("C_esc2") or {}, cs.get("D_escapeHatch") or {},
                          cs.get("E_editKey") or {})
        cells.append({
            "round": i,
            "target": (E.get("target") or A.get("targetItem") or {}),
            "focusOpensGesture": A.get("gestureOpenedByFocusOnly"),
            "focusPast": A.get("historyPastOnFocus"),
            "esc1": B.get("result"), "esc1GestureCleared":
                B.get("gestureClearedByEsc"),
            "esc2First": C.get("afterEsc1"), "esc2Second": C.get("afterEsc2"),
            "focusStillIn": C.get("focusStillInBoundary"),
            "tabLeft": D2.get("leftBoundaryOnTab"),
            "tabLandedAria": (D2.get("tabLandedOn") or {}).get("aria"),
            "tabEsc": D2.get("result"),
            "editPastBeforeBlur": (E.get("afterEdit") or {}).get("historyPast"),
            "editPastAfterBlur": (E.get("afterBlur") or {}).get("historyPast"),
            "gestureOnBlur": [GESTURE_RE.sub("director-gesture-<gen>", x)
                              for x in (E.get("gestureOnBlur") or [])],
            "lastCommandAfterBlur": (E.get("afterBlur") or {}).get(
                "lastCommand")})
    out["cells"] = cells
    out["focusOpensGesture"] = all(c["focusOpensGesture"] is True
                                   for c in cells)
    out["focusNoHistory"] = all(c["focusPast"] == ["0", "0"] for c in cells)
    out["escNeverCloses"] = all(
        c["esc1"] and c["esc1"]["drawerClosed"] is False
        and c["esc2First"]["drawerClosed"] is False
        and c["esc2Second"]["drawerClosed"] is False
        and c["esc1"]["workspaceClosed"] is False for c in cells)
    out["tabHatch"] = all(
        c["tabLeft"] is True and c["tabEsc"]
        and c["tabEsc"]["drawerClosed"] is True
        and c["tabEsc"]["workspaceClosed"] is False for c in cells)
    out["gestureCommitsOnBlur"] = all(
        c["editPastBeforeBlur"] == "0"
        and c["editPastAfterBlur"] == "1"
        and c["gestureOnBlur"][1] == ""
        and c["lastCommandAfterBlur"] == "GESTURE_COMMIT" for c in cells)

    # —— 763g 种子
    # ★ 从 samples 重算，不采信探针自报的 countSeries；两者不一致要看得出来
    out["seedSeries"] = [[s.get("count") for s in (R.get("samples") or [])]
                         for R in r["vb763g"]["rounds"]]
    out["seedSeriesSelfReported"] = [R.get("countSeries")
                                     for R in r["vb763g"]["rounds"]]
    out["seedSeriesAgreesWithProbe"] = all(
        x == y for x, y in zip(out["seedSeries"],
                               out["seedSeriesSelfReported"]))
    out["seedGrew"] = [R.get("grewOverTime") for R in r["vb763g"]["rounds"]]
    out["seedDup"] = [R.get("duplicateIdsFinal") for R in r["vb763g"]["rounds"]]
    out["seedDeterministic"] = all(
        len(set(s)) == 1 and not g and not d
        for s, g, d in zip(out["seedSeries"], out["seedGrew"], out["seedDup"]))
    out["seedCount"] = (out["seedSeries"][0][-1] if out["seedSeries"] and
                        out["seedSeries"][0] else None)

    # —— 763h 持久化
    pers = []
    for i, R in enumerate(r["vb763h"]["rounds"], 1):
        v = R.get("verdict") or {}
        keys = [x["key"] for x in
                ((R.get("storageAfterReload") or {}).get("local") or [])]
        pers.append({"round": i, "verdict": v, "localKeys": keys,
                     "sameKeyBeforeAfter":
                         keys == [x["key"] for x in
                                  ((R.get("storageBeforeReload") or {})
                                   .get("local") or [])]})
    out["persistence"] = pers
    out["addSurvivedReload"] = all(
        x["verdict"].get("addSurvivedReload") is True for x in pers)
    out["reloadLostAdd"] = any(
        x["verdict"].get("reloadLostAdd") is True for x in pers)
    out["persistenceKeys"] = sorted({k for x in pers for k in x["localKeys"]})
    out["persistenceKeyIsDirectorProject"] = all(
        k.startswith("liblib-tv-director-project-v1") for k in
        out["persistenceKeys"]) and bool(out["persistenceKeys"])
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
    ck("静态：边界在 Escape 上 preventDefault",
       st["boundaryEscPreventDefault"])
    ck("静态：边界在 Escape 上 stopPropagation（缺陷的机制）",
       st["boundaryEscStopPropagation"])
    ck("静态：边界在 Escape 上 cancel()",
       st["boundaryEscCancel"])
    ck("静态：边界的 onFocus 直接 begin()（为什么只加守卫不够）",
       st["boundaryOnFocusBegin"])
    ck("静态：边界目前**没有**「没有待取消手势就放行」的守卫",
       st["boundaryNoUnconditionalEscapeGuard"])
    ck("静态：变换数值框 spread 了 gesture",
       st["inspSpreadsGestureOnNumberInput"])
    ck("静态：那些框确实是 type=number",
       st["inspNumberInputType"])
    ck("静态：DirectorDesk 的 Esc 阶梯挂在 window 上",
       st["deskListenerOnWindow"])
    ck("静态：移动端关抽屉那一档排在 isEditable 早退**之前**",
       st["mobileEscBeforeIsEditable"])
    ck("静态：useDirectorGestureBoundary 至少 5 处调用（影响面）",
       st["boundaryUserCount"] >= 5, st["boundaryUserCount"])
    ck("静态：导演台项目持久化键在 src/ 里",
       st["persistenceKeyInSrc"])

    # ═════════ 2. 产物层 ═════════
    ck("产物：判据 14 条", len(J) == 14, len(J))
    ck("产物：判据 id 连号 J1..J14",
       [j.get("id") for j in J] == ["J%d" % i for i in range(1, 15)])
    ck("产物：每条判据都有 statement 与 verdict",
       all(j.get("statement") and j.get("verdict") for j in J))
    ck("★ 产物：14 条判据的 verdict 全是 PASS（不许偷偷改成 FAIL 蒙混）",
       [j.get("verdict") for j in J] == ["PASS"] * 14,
       sorted({str(j.get("verdict")) for j in J}))
    ck("产物：判据 id 在 README 里都被引用",
       all(("| %s |" % j["id"]) in R for j in J))
    ck("产物：findings 与 judgments[].evidence **逐条**同源",
       all(f.get(j.get("evidenceKey")) == j.get("evidence") for j in J),
       [j.get("id") for j in J
        if f.get(j.get("evidenceKey")) != j.get("evidence")])
    ck("产物：每条判据都引用的键真实存在",
       all(j.get("evidenceKey") in f for j in J))
    ck("产物：缺陷恰好 1 条且是 D1",
       [d.get("id") for d in a.get("defects") or []] == ["D1"])
    ck("★ 产物：README 里 D1 的严重度与产物一致（不许产物降级、README 还写着中）",
       ("（%s）" % (a.get("defects") or [{}])[0].get("severity")) in R,
       (a.get("defects") or [{}])[0].get("severity"))
    ck("产物：D1 标了需要改 src/",
       (a.get("defects") or [{}])[0].get("needsSrcChange") is True)
    ck("产物：D1 点了 useDirectorGestureBoundary.ts:92-98",
       any("useDirectorGestureBoundary.ts:92-98" in w
           for w in (a.get("defects") or [{}])[0].get("where") or []))
    ck("产物：D1 给了修法提示",
       bool((a.get("defects") or [{}])[0].get("fixHint")))
    ck("产物：观察 2 条（事实更正 + 待拍板）",
       len(a.get("observations") or []) == 2)
    ck("产物：探针教训 5 条 R53..R57",
       [x.get("id") for x in a.get("probeLessons") or []]
       == ["R53", "R54", "R55", "R56", "R57"])
    ck("产物：教训在 README 里都有出处",
       all(x["id"] in R for x in a.get("probeLessons") or []))
    ck("产物：不声称清单非空", len(a.get("notClaimed") or []) >= 6)
    ck("产物：明说不声称源站对照",
       any("源站" in s for s in a.get("notClaimed") or []))
    ck("产物：明说 763b 两轮不可比",
       any("不可比" in s for s in a.get("notClaimed") or []))
    ck("产物：探针清单 8 个",
       len(a.get("probes") or []) == 8)
    ck("★ 产物：每个探针自报的轮次与原始读数的轮次一致（不许谎报）",
       all(p.get("rounds") == (rw.get("rawRounds") or {}).get(p.get("id"))
           for p in a.get("probes") or []),
       [(p.get("id"), p.get("rounds"),
         (rw.get("rawRounds") or {}).get(p.get("id")))
        for p in a.get("probes") or []])
    ck("产物：每个探针都指向存在的 raw 文件",
       all((OUTDIR / p["raw"]).exists() for p in a.get("probes") or []))
    ck("产物：每个探针都指向存在的 probes 文件",
       all((OUTDIR / p["file"]).exists() for p in a.get("probes") or []))
    ck("产物：raw/ 下正好 8 份原始读数",
       sorted(x.name for x in RAWDIR.glob("vb763*.json")) == sorted(RAW_FILES))
    ck("产物：probes/ 下 8 个探针 + 1 个汇编器",
       sorted(x.name for x in PROBEDIR.glob("*.py")) == sorted(PROBE_FILES))
    ck("产物：8 份原始读数都记了 sha",
       len(a.get("rawSha") or {}) == 8)
    ck("产物：本批 src 未改动",
       (a.get("env") or {}).get("srcModified") is False)

    # —— README 结构与 pre-commit 钩子
    ck("README：存在且非空", len(R) > 2000, len(R))
    for need in ("## 判据", "## 缺陷", "## 探针教训", "## 不声称",
                 "## 复现", "## 观察"):
        ck("README：含章节 %s" % need, need in R)
    bare = [i + 1 for i, l in enumerate(R.splitlines())
            if BARE_NUM_CELL.match(l)]
    ck("README：表格首格没有裸数字（pre-commit 钩子的正则）",
       not bare, bare)
    ck("README：缺陷章节点名了 useDirectorGestureBoundary",
       "useDirectorGestureBoundary" in R)
    ck("README：写了修法要两处一起改",
       "两处一起改" in R)
    ck("README：如实写了 763c 0/8 复现",
       "0/8 复现" in R)
    ck("README：如实写了重复 id 是打印截断造成的",
       "截断" in R)

    # —— 台账
    row763 = [l for l in ledLines if l.startswith("| Batch 763 |")]
    ck("台账：恰好一行 Batch 763", len(row763) == 1, len(row763))
    ck("台账：Batch 763 行没有 U+FFFD",
       row763 and "\ufffd" not in row763[0])
    ck("台账：行数 626（本批只追加一行）", len(ledLines) == 626, len(ledLines))
    ck("台账：历史 U+FFFD 仍只在 522/583/587",
       [i + 1 for i, l in enumerate(ledLines) if "\ufffd" in l]
       == [522, 583, 587],
       [i + 1 for i, l in enumerate(ledLines) if "\ufffd" in l])

    # ═════════ 3. 原始读数交叉核对 ═════════
    ck("原始：8 份读数全部可读", rw.get("filesOk") is True)

    # J1
    ck("J1 交叉：六档宽度齐全 896..901",
       rw.get("breakpointWidths") == [896, 897, 898, 899, 900, 901],
       rw.get("breakpointWidths"))
    ck("J1 交叉：重算后六档零错位", rw.get("breakpointOk") is True)
    ck("J1：产物 breakpointAllOk 与重算一致",
       f.get("breakpointAllOk") is True
       and f.get("breakpointAllOk") == rw.get("breakpointOk"))
    ck("J1：产物 breakpointZeroMismatch 与重算一致",
       f.get("breakpointZeroMismatch") is True)
    ck("J1：产物里的六档 verdict 逐档与重算一致",
       [x.get("ok") for x in f.get("breakpointRows") or []]
       == [True] * 6, [x.get("ok") for x in f.get("breakpointRows") or []])

    # J2
    ck("J2 交叉：Esc 阶梯五步都在（无面板/导出面板/第二次/可编辑控件内/离开后）",
       rw.get("escLadderSteps")
       == ["baseline-no-panel", "export-panel-open", "second-esc",
           "esc-in-editable", "esc-after-leaving-editable"],
       rw.get("escLadderSteps"))
    ck("J2：产物 escLadderRows 与判据 2 证据一致",
       f.get("escLadderRows") == (J[1].get("evidence")
                                  if len(J) > 1 else None))

    # J3 / J4
    ck("J3 交叉：两轮焦点相关字段逐字段一致",
       rw.get("drawerFocusAllEqual") is True,
       rw.get("drawerFocusEqual"))
    ck("J3：产物 drawerFocusAllEqual 与重算一致",
       f.get("drawerFocusAllEqual") == rw.get("drawerFocusAllEqual"))
    ck("J4：两个抽屉都验证了「只关抽屉不关导演台」",
       all(row.get("drawerClosedByEsc") is True
           and row.get("workspaceClosedByEsc") is False
           for x in (f.get("drawerFocusRoundEqual") or [])
           for row in [x.get("round1") or {}, x.get("round2") or {}]))
    ck("J3/J4：两抽屉 Tab 12 步 0 逃出",
       all(x.get("tabSteps") == 12 and x.get("tabEscaped") == 0
           for row in (f.get("drawerFocusRoundEqual") or [])
           for x in [row.get("round1") or {}]))
    ck("★ 如实标注：reachable 两轮不同（探针自伤），不判等",
       rw.get("reachableDiffersAcrossRounds") is True
       and all(x.get("reachableRound1") != x.get("reachableRound2")
               for x in (rw.get("drawerFocusEqual") or [])),
       rw.get("drawerFocusEqual"))
    ck("★ 如实标注：产物里 reachable 也是单列不判等",
       all("reachableEqual" in x for x in f.get("drawerFocusRoundEqual") or []))

    # J5
    ck("J5 交叉：两轮四步都动了历史",
       rw.get("undoRedo1AllMoved") is True
       and rw.get("undoRedo2AllMoved") is True)
    ck("J5 交叉：四键顺序为 ⌘Z/⌘Y/⌘Z/⌘⇧Z",
       rw.get("undoRedo1Keys") == ["Cmd+Z", "Cmd+Y", "Cmd+Z", "Cmd+Shift+Z"],
       rw.get("undoRedo1Keys"))
    ck("J5 交叉：每步之后的 lastCommand 依次 UNDO/REDO/UNDO/REDO",
       rw.get("undoRedo1LastCommandsAfter")
       == ["UNDO", "REDO", "UNDO", "REDO"],
       rw.get("undoRedo1LastCommandsAfter"))
    ck("J5：产物 undoRedoAllMoved 与重算一致",
       f.get("undoRedoAllMoved") is True)
    ck("J5：产物两轮读数都在",
       bool(f.get("undoRedoRound1")) and bool(f.get("undoRedoRound2")))

    # J6
    ck("J6 交叉：Delete/Backspace × 两轮都真删（判效应）",
       rw.get("deleteBothFired") is True, rw.get("deleteRows"))
    ck("J6 交叉：四行都在（2 键 × 2 轮）", len(rw.get("deleteRows") or []) == 4)
    ck("J6：产物 deleteBothFired 与重算一致",
       f.get("deleteBothFired") == rw.get("deleteBothFired"))
    ck("J6：★ 产物里如实记下「按标签判会看漏」的那一行",
       set(f.get("deleteLabelBlindSpot") or []) == {"Backspace"}
       and set(rw.get("deleteLabelBlindRow") or []) == {"Backspace"},
       [f.get("deleteLabelBlindSpot"), rw.get("deleteLabelBlindRow")])
    ck("J6：产物每一行都带上了「点中时对象数」这个效应证据",
       all(x.get("pickedCountBefore") is not None
           for x in (f.get("deleteRowsRound1") or [])
           + (f.get("deleteRowsRound2") or [])))

    # J7
    ck("J7 交叉：树面板 20 个控件 0 个关不掉",
       rw.get("treeZeroNotClosed") is True, rw.get("treeSweep"))
    ck("J7 交叉：失效序号读到了真列表（防「读错键名拿到 null 还判一致」）",
       isinstance(rw.get("inspNotClosedIdx"), list)
       and all(isinstance(x, list) and all(isinstance(y, int) for y in x)
               for x in rw["inspNotClosedIdx"]),
       rw.get("inspNotClosedIdx"))
    ck("J7 交叉：属性面板 9 个关不掉",
       rw.get("notClosedCount") == 9, rw.get("notClosedCount"))
    ck("J7 交叉：失效序号两轮稳定且是 6/9/12/…/30",
       rw.get("inspNotClosedStable") is True
       and rw.get("inspNotClosedIdx") == [[6, 9, 12, 15, 18, 21, 24, 27, 30]]
       * 2, rw.get("inspNotClosedIdx"))
    ck("J7 交叉：失效控件 type 全是 number",
       rw.get("inspNotClosedAllNumber") is True)
    ck("J7：产物 sweepInspectorNotClosedIdx 与重算一致",
       f.get("sweepInspectorNotClosedIdx") == rw.get("inspNotClosedIdx"))
    ck("J7：产物 sweepTreeZeroNotClosed 与重算一致",
       f.get("sweepTreeZeroNotClosed") == rw.get("treeZeroNotClosed"))
    ck("J7：两轮属性面板控件数都是 35",
       [x.get("count") for x in rw.get("inspSweepD") or []] == [35, 35],
       [x.get("count") for x in rw.get("inspSweepD") or []])

    # J8
    ck("★ 前置：失效控件列表两轮都非空（否则 all([]) 会静默通过）",
       all(len(x.get("bad") or []) == 9 for x in rw.get("inspSweepE") or [])
       and all(len(x.get("bad") or []) == 9 for x in rw.get("inspSweepD") or []),
       [len(x.get("bad") or []) for x in (rw.get("inspSweepE") or [])])
    ck("J8 交叉：失效控件的 Esc 从未到达 window 冒泡",
       rw.get("badNeverReachedWinBubble") is True)
    ck("J8 交叉：但 window 捕获照样触发（事件确实发出去了）",
       rw.get("badReachedWinCapture") is True)
    ck("J8 交叉：能关掉的控件全部触发了 window 冒泡",
       rw.get("closedAllReachedWinBubble") is True)
    ck("J8：产物 notClosedNeverReachedWindowBubble 与重算一致",
       f.get("notClosedNeverReachedWindowBubble") is True)
    ck("J8：产物 notClosedReachedWindowCapture 与重算一致",
       f.get("notClosedReachedWindowCapture") is True)
    ck("J8：产物 closedAlwaysReachedWindowBubble 与重算一致",
       f.get("closedAlwaysReachedWindowBubble") is True)

    # J9
    ck("J9 交叉：注入的 text 与 number 四格都关掉了抽屉",
       rw.get("injectionAllClosed") is True,
       rw.get("injectedText") + rw.get("injectedNumber"))
    ck("J9：产物 injectionRefutesNativeNumber 与重算一致",
       f.get("injectionRefutesNativeNumber") is True)
    ck("J9：★ 注入对照否掉原生假设这件事在 README 里写明了",
       "否掉" in R and "type=number" in R)

    # J10
    ck("J10 交叉：Esc 连按两次都关不掉抽屉、也没关导演台",
       rw.get("escNeverCloses") is True)
    ck("J10：产物 escNeverClosesDrawer 与重算一致",
       f.get("escNeverClosesDrawer") is True)
    ck("J10：产物 escDidNotCloseWorkspaceEither 为真",
       f.get("escDidNotCloseWorkspaceEither") is True)
    ck("J10 交叉：Tab 离开边界后 Esc 恢复正常（逃生门）",
       rw.get("tabHatch") is True, rw.get("cells"))
    ck("J10：Tab 落点是关键帧按钮（不是数值框）",
       all(c["tabLandedAria"] == "当前帧有关键帧"
           for c in rw.get("cells") or []),
       [c["tabLandedAria"] for c in rw.get("cells") or []])
    ck("J10：产物 tabHatchWorks 与重算一致",
       f.get("tabHatchWorks") is True)

    # J11
    ck("J11 交叉：只聚焦就开 gesture、但不写历史",
       rw.get("focusOpensGesture") is True
       and rw.get("focusNoHistory") is True)
    ck("J11 交叉：失焦才 commit（past 0→1、GESTURE_COMMIT）",
       rw.get("gestureCommitsOnBlur") is True)
    ck("J11：产物 focusAloneOpensGesture / focusAloneNoHistory 与重算一致",
       f.get("focusAloneOpensGesture") is True
       and f.get("focusAloneNoHistory") is True)
    ck("J11：产物 gestureCommitsOnBlur 与重算一致",
       f.get("gestureCommitsOnBlur") is True)
    ck("J11：因链验的代表控件是 position/x",
       all((c["target"] or {}).get("tf") == "position"
           and (c["target"] or {}).get("ta") == "x"
           for c in rw.get("cells") or []))

    # J12
    ck("J12 交叉：两轮新增的机位都扛过 reload",
       rw.get("addSurvivedReload") is True, rw.get("persistence"))
    ck("J12 交叉：没有任何一轮丢了新增",
       rw.get("reloadLostAdd") is False)
    ck("J12 交叉：持久化键就是 director-project",
       rw.get("persistenceKeyIsDirectorProject") is True,
       rw.get("persistenceKeys"))
    ck("J12 交叉：重载前后是同一个键",
       all(x["sameKeyBeforeAfter"] for x in rw.get("persistence") or []))
    ck("J12：产物 addSurvivesReload / reloadNeverLostAdd 与重算一致",
       f.get("addSurvivesReload") is True
       and f.get("reloadNeverLostAdd") is True
       and rw.get("addSurvivedReload") is True
       and rw.get("reloadLostAdd") is False)
    ck("J12：产物记下了持久化键",
       str(f.get("persistenceKey") or "").startswith(
           "liblib-tv-director-project-v1"))
    ck("★ 事实更正：README 明确推翻「两个 store 都无持久化」",
       "两个 store 都无持久化" in R and "更正" in R)

    # J13
    ck("J13 交叉：两轮种子都是 5 个对象、一次到位、零重复 id",
       rw.get("seedDeterministic") is True
       and rw.get("seedCount") == 5,
       [rw.get("seedSeries"), rw.get("seedGrew"), rw.get("seedDup")])
    ck("J13：产物 seedDeterministic / seedCount 与重算一致",
       f.get("seedDeterministic") is True
       and f.get("seedCount") == rw.get("seedCount"))

    # J14
    ck("J14 交叉：8 次 trial 全部落在期望落点",
       rw.get("resizeTrials") == 8 and rw.get("resizeAllExpected") is True,
       rw.get("resizeBtnXs"))
    ck("J14 交叉：落点只有 276 一个值（没有旧宽度的 596）",
       rw.get("resizeBtnXs") == [276], rw.get("resizeBtnXs"))
    ck("J14：产物 resizeFitViewAllExpected 与重算一致",
       f.get("resizeFitViewAllExpected") is True)
    ck("J14：产物 resizeFitViewTrials 有 8 行",
       len(f.get("resizeFitViewTrials") or []) == 8)
    return checks


def negative_controls(a, st, rw):
    cases = []

    def inj(name, mutate):
        bad = copy.deepcopy(a)
        mutate(bad)
        failed = [c["label"] for c in run_checks(bad, st, rw) if not c["pass"]]
        cases.append({"name": name, "caught": len(failed) > 0,
                      "firstFail": failed[0] if failed else None})

    def inj_rw(name, mutate):
        """★ 注入必须打到**真正被检查**的键。

        改中间列表没用 —— 检查读的是派生布尔。所以这里直接改**原始读数**
        再跑一遍 `raw_side_from` 重算：既验证检查项承重，也验证「数字不许手抄」
        这条规矩真的靠重算兜着。
        """
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

    def inj_static(name, mutate):
        bad = copy.deepcopy(st)
        mutate(bad)
        failed = [c["label"] for c in run_checks(a, bad, rw) if not c["pass"]]
        cases.append({"name": name, "caught": len(failed) > 0,
                      "firstFail": failed[0] if failed else None})

    # —— 伪造「缺陷不存在」（本批最容易自欺的一类）
    inj("★ 删掉缺陷 D1", lambda x: x.__setitem__("defects", []))
    inj("★ 把 D1 的 needsSrcChange 改成 false", lambda x:
        x["defects"][0].__setitem__("needsSrcChange", False))
    inj("★ 把 D1 的定位行删掉", lambda x:
        x["defects"][0].__setitem__("where", ["src/app/page.tsx:1"]))
    inj("★ 把 D1 的修法提示抹掉", lambda x:
        x["defects"][0].__setitem__("fixHint", ""))
    inj("★ 把 D1 降级成「观察」", lambda x:
        x.__setitem__("defects", [x["observations"][0]]))
    inj("★ 把观察 O1 的事实更正删掉（等于把错的话又写回去）", lambda x:
        x.__setitem__("observations", [x["observations"][1]]))
    inj("★ 把 D1 严重度改成「低」而 README 还写着「中」", lambda x:
        x["defects"][0].__setitem__("severity", "低"))

    # —— 只改一份事实（两份事实分叉）
    inj("只改 findings.escNeverClosesDrawer（判据证据那一份不动）", lambda x:
        x["findings"].__setitem__("escNeverClosesDrawer", False))
    inj("只改 findings.sweepInspectorNotClosedIdx[0]", lambda x:
        x["findings"]["sweepInspectorNotClosedIdx"][0].__setitem__(0, 7))
    inj("只改 findings.notClosedNeverReachedWindowBubble", lambda x:
        x["findings"].__setitem__("notClosedNeverReachedWindowBubble", False))
    inj("只改 findings.injectionRefutesNativeNumber", lambda x:
        x["findings"].__setitem__("injectionRefutesNativeNumber", False))
    inj("只改 findings.addSurvivesReload", lambda x:
        x["findings"].__setitem__("addSurvivesReload", False))
    inj("只改 findings.persistenceKey", lambda x:
        x["findings"].__setitem__("persistenceKey", "some-other-key"))
    inj("只改 findings.seedCount（6 个而不是 5 个）", lambda x:
        x["findings"].__setitem__("seedCount", 6))
    inj("只改 findings.tabHatchWorks", lambda x:
        x["findings"].__setitem__("tabHatchWorks", False))
    inj("只改 findings.focusAloneOpensGesture", lambda x:
        x["findings"].__setitem__("focusAloneOpensGesture", False))
    inj("只改 findings.gestureCommitsOnBlur", lambda x:
        x["findings"].__setitem__("gestureCommitsOnBlur", False))
    inj("只改 findings.deleteBothFired", lambda x:
        x["findings"].__setitem__("deleteBothFired", False))
    inj("只改 findings.deleteLabelBlindSpot（把看漏的那行抹掉）", lambda x:
        x["findings"].__setitem__("deleteLabelBlindSpot", []))
    inj("只改 findings.breakpointRows[3].ok", lambda x:
        x["findings"]["breakpointRows"][3].__setitem__("ok", False))
    inj("只改 findings.breakpointAllOk", lambda x:
        x["findings"].__setitem__("breakpointAllOk", False))
    inj("只改 findings.resizeFitViewAllExpected", lambda x:
        x["findings"].__setitem__("resizeFitViewAllExpected", False))

    # —— 改判据那一侧
    inj("把判据 7 的证据换成树面板的读数", lambda x:
        x["judgments"][6].__setitem__("evidence", x["findings"]["sweepTree"]))
    inj("把判据 8 的 verdict 改成 FAIL", lambda x:
        x["judgments"][7].__setitem__("verdict", "FAIL"))
    inj("删掉判据 14", lambda x: x.__setitem__(
        "judgments", [j for j in x["judgments"] if j["id"] != "J14"]))
    inj("把判据 id 从 J7 改成 J8（制造重号）", lambda x:
        x["judgments"][6].__setitem__("id", "J8"))
    inj("把某条判据的 evidenceKey 指向不存在的键", lambda x:
        x["judgments"][3].__setitem__("evidenceKey", "noSuchKey"))

    # —— 元信息造假
    inj("把探针轮次从 2 谎报成 3", lambda x:
        x["probes"][1].__setitem__("rounds", 3))
    inj("把 srcModified 改成 true 之外的谎话（谎称没改 src 却改成 true）",
        lambda x: x["env"].__setitem__("srcModified", "false"))
    inj("把 rawSha 删掉两份", lambda x: x.__setitem__(
        "rawSha", {k: v for k, v in list(x["rawSha"].items())[:6]}))
    inj("清空不声称清单", lambda x: x.__setitem__("notClaimed", []))
    inj("把不声称里的「不可比」那条删掉", lambda x: x.__setitem__(
        "notClaimed", [s for s in x["notClaimed"] if "不可比" not in s]))
    inj("删掉探针教训 R55（两轮可比性）", lambda x: x.__setitem__(
        "probeLessons", [l for l in x["probeLessons"] if l["id"] != "R55"]))

    # —— 原始读数被改成「更好看」的样子（改 raw，再重算）
    def bad_bubble(x):
        for R in x["vb763e"]["rounds"]:
            for row in R["inspector_sweep"]["rows"]:
                if row.get("drawerClosed") is False:
                    row["esc"]["reachedWinBubble"] = True

    def drop_two_bad(x):
        for R in x["vb763d"]["rounds"]:
            s = R["inspector_sweep"]
            s["rows"] = [r for r in s["rows"]
                         if r.get("panelClosed") is not False][:8]
            s["notClosed"] = [r["i"] for r in s["rows"]
                              if r.get("panelClosed") is False]

    def inj_number_fails(x):
        for R in x["vb763e"]["rounds"]:
            R["injectedNumber"]["drawerClosed"] = False

    def esc2_closes(x):
        for R in x["vb763f"]["rounds"]:
            R["cells"]["C_esc2"]["afterEsc2"] = {
                "deskOpen": True, "inspectorState": "closed",
                "treeState": "closed", "drawerClosed": True,
                "workspaceClosed": False}

    def hatch_broken(x):
        for R in x["vb763f"]["rounds"]:
            R["cells"]["D_escapeHatch"]["result"] = {
                "deskOpen": True, "inspectorState": "open",
                "treeState": "closed", "drawerClosed": False,
                "workspaceClosed": False}

    def focus_no_gesture(x):
        for R in x["vb763f"]["rounds"]:
            R["cells"]["A_focusOnly"]["gestureOpenedByFocusOnly"] = False

    def gesture_dies_on_edit(x):
        for R in x["vb763f"]["rounds"]:
            c = R["cells"]["E_editKey"]
            c["afterBlur"] = dict(c["afterBlur"] or {},
                                  historyPast="0", lastCommand="")

    def wrong_persistence_key(x):
        for R in x["vb763h"]["rounds"]:
            for side in ("storageBeforeReload", "storageAfterReload"):
                for item in (R.get(side) or {}).get("local") or []:
                    item["key"] = "some-other-key"

    def add_did_not_survive(x):
        for R in x["vb763h"]["rounds"]:
            R["verdict"] = dict(R["verdict"] or {},
                                addSurvivedReload=False, reloadLostAdd=True)

    def seed_six(x):
        for R in x["vb763g"]["rounds"]:
            for s in R["samples"]:
                rows = s.get("rows") or []
                rows.append({"id": "director-prop-extra", "kind": "prop",
                             "selected": "false", "text": "多一个"})
                s["count"] = 6
                s["kinds"] = {"character": 1, "prop": 4, "camera": 1}

    def seed_grows(x):
        for R in x["vb763g"]["rounds"]:
            for s in R["samples"]:
                s["count"] = 3 if s["atMs"] == 600 else 5
            R["countSeries"] = [s["count"] for s in R["samples"]]
            R["grewOverTime"] = True

    def dup_ids(x):
        for R in x["vb763g"]["rounds"]:
            R["duplicateIdsFinal"] = ["director-camera-main"]

    def one_width_off(x):
        for row in x["vb763a"]["rounds"][0]["breakpoint"]:
            if row["innerWidth"] == 899:
                row["inspector"]["rect"]["x"] = 900

    def esc_never_ran(x):
        for R in x["vb763e"]["rounds"]:
            for row in R["inspector_sweep"]["rows"]:
                if row.get("drawerClosed") is False:
                    row["esc"]["reachedWinCapture"] = False

    def stale_landing(x):
        for t in x["vb763c"]["trials"][:1]:
            t["btnX"] = 596

    def drawer_fields_differ(x):
        x["vb763b"]["rounds"][1]["B1_drawers"][1]["tab"]["escapedCount"] = 2

    def delete_no_history(x):
        for R in x["vb763b"]["rounds"]:
            for de in R.get("B3_delete") or []:
                de["past"] = [de["past"][0], de["past"][0]]

    def backspace_label_moved(x):
        for R in x["vb763b"]["rounds"]:
            for de in R.get("B3_delete") or []:
                if de["key"] == "Backspace":
                    de["changed"] = True

    def undo_did_not_move(x):
        x["vb763b"]["rounds"][0]["B2_undoRedo"][0]["past"] = ["1", "1"]

    inj_rw("伪造：失效控件全都到达了 window 冒泡", bad_bubble)
    inj_rw("伪造：失效控件只剩 1 个（且序号被改小）", drop_two_bad)
    inj_rw("伪造：window 捕获也没触发", esc_never_ran)
    inj_rw("伪造：注入的 number 输入框也关不掉抽屉", inj_number_fails)
    inj_rw("伪造：Esc 第二次把抽屉关掉了", esc2_closes)
    inj_rw("伪造：Tab 之后 Esc 也关不掉（逃生门没了）", hatch_broken)
    inj_rw("伪造：只聚焦不再开 gesture", focus_no_gesture)
    inj_rw("伪造：编辑完立刻 commit（不经失焦）", gesture_dies_on_edit)
    inj_rw("伪造：持久化键不是 director-project", wrong_persistence_key)
    inj_rw("伪造：新增的机位没扛过 reload", add_did_not_survive)
    inj_rw("伪造：种子变成 6 个对象", seed_six)
    inj_rw("伪造：种子随时间增长（异步加载）", seed_grows)
    inj_rw("伪造：种子出现重复 id", dup_ids)
    inj_rw("伪造：六档里有一档错位", one_width_off)
    inj_rw("伪造：resize 落点出现旧宽度的 596", stale_landing)
    inj_rw("伪造：两轮焦点字段其实不一致（Tab 逃出 2 次）", drawer_fields_differ)
    inj_rw("伪造：Delete 只删掉了对象但历史没动", delete_no_history)
    inj_rw("伪造：Backspace 的 lastCommand 也变了（标签不再看漏）",
           backspace_label_moved)
    inj_rw("伪造：⌘Z 没有推动历史", undo_did_not_move)

    # —— 静态层被改成「代码已经修好了」
    inj_static("伪造：边界里已经有「没有手势就放行」的守卫", lambda x:
               x.__setitem__("boundaryNoUnconditionalEscapeGuard", False))
    inj_static("伪造：边界不再 stopPropagation", lambda x:
               x.__setitem__("boundaryEscStopPropagation", False))
    inj_static("伪造：onFocus 不再 begin()", lambda x:
               x.__setitem__("boundaryOnFocusBegin", False))
    inj_static("伪造：移动端关抽屉那一档挪到了 isEditable 之后", lambda x:
               x.__setitem__("mobileEscBeforeIsEditable", False))
    inj_static("伪造：那些框不再是 type=number", lambda x:
               x.__setitem__("inspNumberInputType", False))
    inj_static("伪造：Esc 阶梯不再挂在 window 上", lambda x:
               x.__setitem__("deskListenerOnWindow", False))
    inj_static("伪造：影响面只剩 1 处", lambda x:
               x.__setitem__("boundaryUserCount", 1))
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
        {"label": "原始读数可用（raw/ 下 8 份）", "pass": False, "got": rawErr}]
    neg = [] if rawErr else negative_controls(a, st, rw)

    npass = sum(1 for c in checks if c["pass"])
    total = len(checks)
    neg_ok = sum(1 for n in neg if n["caught"])
    ok = npass == total and neg_ok == len(neg)

    REPORT.write_text(json.dumps(
        {"batch": 763, "checks": checks, "pass": npass, "total": total,
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
    print("batch 763 %s" % ("通过" if ok else "不通过"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
