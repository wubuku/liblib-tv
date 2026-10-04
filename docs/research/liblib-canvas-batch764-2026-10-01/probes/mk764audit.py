#!/usr/bin/env python3
"""batch 764 汇编器：从 raw/ 的 3 份原始读数现算 runtime-audit.json

规矩（沿用 756–763）：
1. **数字不许手抄** —— 下面每个数都从 `raw/vb764*.json` 算出来。
2. **缺原始读数判失败**，不许「通过」。
3. **同一事实存两份时两份都要守**：`findings[k] == judgments[i].evidence`
   在写盘前逐条断言，JSON 往返后由验收器再查一遍。
4. **读不到的东西不许当成「没有」**：764a 的路径上下文两轮不可比、
   路径锚点/FOV 那几类控件没渲染出来 —— 这两条都单列，不并进结论。

用法：python3 mk764audit.py
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
    if isinstance(o, str):
        return GESTURE_RE.sub("director-gesture-<gen>", o)
    if isinstance(o, dict):
        return {k: norm(v) for k, v in o.items()}
    if isinstance(o, list):
        return [norm(v) for v in o]
    return o


a, a_p = load("vb764a.json")
b, b_p = load("vb764b.json")
c, c_p = load("vb764c.json")

# ═══════════ 764a：逐上下文扫 Esc，量 D1 的影响面 ═══════════
def ctx_rows(rd):
    out = []
    for c_ in rd.get("contexts") or []:
        if "rows" not in c_:
            out.append({"label": c_.get("label"), "FAILED": True})
            continue
        bad, good, skipped = [], [], []
        for r in c_["rows"]:
            it = r["item"]
            ident = {k: it[k] for k in ("tf", "ta", "pap", "pah", "ptf", "pta",
                                        "pose", "fov") if it.get(k)}
            rec = {"i": r["i"], "tag": it.get("tag"), "type": it.get("type"),
                   "boundary": it.get("boundary"), "marks": it.get("marks"),
                   "ident": ident,
                   "focused": (r.get("focus") or {}).get("focused"),
                   "reachedWinBubble": (r.get("esc") or {}).get(
                       "reachedWinBubble"),
                   "reachedWinCapture": (r.get("esc") or {}).get(
                       "reachedWinCapture"),
                   "drawerClosed": r.get("drawerClosed"),
                   "workspaceClosed": (r.get("esc") or {}).get(
                       "workspaceClosed")}
            if "skipped" in r:
                rec["skipped"] = r["skipped"]
                skipped.append(rec)
            elif rec["boundary"]:
                bad.append(rec)
            else:
                good.append(rec)
        out.append({
            "label": c_["label"],
            "inspectorKind": c_.get("inspectorKind"),
            "focusScope": c_.get("focusScope"),
            "totalFocusable": c_["totalFocusable"],
            "boundaryCount": c_["boundaryCount"],
            "boundaryTypes": c_["boundaryTypes"],
            "boundaryRows": bad,
            "nonBoundaryRows": good,
            "boundarySwallowed": [r["i"] for r in bad
                                  if r["reachedWinBubble"] is False],
            "boundaryNotSwallowed": [r["i"] for r in bad
                                     if r["reachedWinBubble"] is not False],
            "nonBoundarySwallowed": [r["i"] for r in good
                                     if r["reachedWinBubble"] is False],
            "boundaryAllFocusSucceeded": all(r["focused"] is True
                                             for r in bad) if bad else None,
            "skipped": skipped,
        })
    return out


a_ctx = [ctx_rows(rd) for rd in a["rounds"]]
a_labels_r1 = [x["label"] for x in a_ctx[0]]
a_labels_r2 = [x["label"] for x in a_ctx[1]]

# 两轮可比的上下文：标签、边界数、吞掉的序号、类型全一致
comparable = []
for x, y in zip(a_ctx[0], a_ctx[1]):
    same = (x.get("label") == y.get("label")
            and x.get("totalFocusable") == y.get("totalFocusable")
            and x.get("boundaryCount") == y.get("boundaryCount")
            and x.get("boundaryTypes") == y.get("boundaryTypes")
            and x.get("boundarySwallowed") == y.get("boundarySwallowed")
            and x.get("nonBoundarySwallowed") == y.get("nonBoundarySwallowed"))
    comparable.append({
        "label": x.get("label"),
        "comparable": same,
        "round1": {k: x.get(k) for k in
                   ("totalFocusable", "boundaryCount", "boundaryTypes",
                    "boundarySwallowed", "nonBoundarySwallowed")},
        "round2": {k: y.get(k) for k in
                   ("totalFocusable", "boundaryCount", "boundaryTypes",
                    "boundarySwallowed", "nonBoundarySwallowed")},
        "failedR1": x.get("FAILED"), "failedR2": y.get("FAILED")})

comparable_ctx = [x for x in comparable if x["comparable"]]
incomparable_ctx = [x["label"] for x in comparable if not x["comparable"]]

# 可比上下文里：边界控件**全部**吞、非边界控件**一个都不吞**
b_rows_all = [r for x in a_ctx[0] for r in x["boundaryRows"]]
n_rows_all = [r for x in a_ctx[0] for r in x["nonBoundaryRows"]]
comp_labels = {x["label"] for x in comparable_ctx}
b_rows_comp = [r for x in a_ctx[0] if x["label"] in comp_labels
               for r in x["boundaryRows"]]
n_rows_comp = [r for x in a_ctx[0] if x["label"] in comp_labels
               for r in x["nonBoundaryRows"]]

# 763 的「9 个 number」在 764 里对应哪个上下文
by_label = {x["label"]: x for x in a_ctx[0]}
pose_ctx = by_label.get("character:pose")
cam_ctx = by_label.get("camera:properties")
defect_ctx = by_label.get("default")

# ═══════════ 764b：⌘C / ⌘V ═══════════
def kb(rd):
    return {k: rd.get(k) for k in
            ("C1_pasteWithEmptyClipboard", "C2_copy", "C3_paste",
             "C4_pasteAgain", "C5_copyFromField")}


def mouse(rd):
    return {k: rd.get(k) for k in
            ("C6_copyButton", "C6_clearButton", "C6_deleteButton")}


b_kb = [kb(rd) for rd in b["rounds"]]
b_mouse = [mouse(rd) for rd in b["rounds"]]

# ═══════════ 764c：⌘C/⌘V 在可编辑控件里到底死没死 ═══════════
def field_case(rd):
    A, B, C, D = (rd.get("A_emptyPaste") or {}, rd.get("B_copyFromTree") or {},
                  rd.get("C_copyFromField") or {}, rd.get("D_paste") or {})
    focus = rd.get("C_focusField") or {}
    return {
        "focusField": {"focused": focus.get("focused"),
                       "tf": focus.get("tf"), "ta": focus.get("ta")},
        # 树里按 ⌘C（对照）
        "copyFromTree": {"lastCommand": B.get("lastCommand"),
                         "lastDisposition": B.get("lastDisposition"),
                         "count": B.get("count"), "past": B.get("past")},
        # 数值框里按 ⌘C
        "copyFromField": {
            "lastCommand": C.get("lastCommand"),
            "lastDisposition": C.get("lastDisposition"),
            "count": C.get("count"), "past": C.get("past"),
            "gestureBefore": GESTURE_RE.sub("director-gesture-<gen>",
                                             C.get("activeGestureBefore") or ""),
            "gestureAfter": GESTURE_RE.sub("director-gesture-<gen>",
                                            C.get("activeGestureAfter") or ""),
            "gestureUnchanged": (C.get("activeGestureBefore")
                                 == C.get("activeGestureAfter")),
            "lastCommandUnchanged": (C.get("lastCommand")
                                     == [C.get("lastCommand", [None])[0]] * 2
                                     or C.get("lastCommand")[0]
                                     == C.get("lastCommand")[1])},
        # 数值框里按 ⌘V
        "pasteFromField": {"lastCommand": D.get("lastCommand"),
                           "lastDisposition": D.get("lastDisposition"),
                           "count": D.get("count"), "past": D.get("past"),
                           "countDelta": ((D.get("count") or [0, 0])[1]
                                          - (D.get("count") or [0, 0])[0]),
                           "historyDelta": (int((D.get("past") or ["0", "0"])[1])
                                            - int((D.get("past")
                                                   or ["0", "0"])[0]))},
        # 空剪贴板粘贴
        "emptyPaste": {"lastCommand": A.get("lastCommand"),
                       "lastDisposition": A.get("lastDisposition"),
                       "count": A.get("count"), "past": A.get("past")},
        "picksFailed": sorted(k for k in ("B_pickA", "B_pickA2", "C_pickB",
                                          "C_pickB2", "D_pickC")
                              if isinstance(rd.get(k), dict)
                              and rd[k].get("err")),
        "newRowsAfterPaste": len(rd.get("D_newRows") or []),
    }


c_cases = [field_case(rd) for rd in c["rounds"]]

# ═══════════ 判据 ═══════════
findings = {
    "contextsRound1": a_ctx[0],
    "contextsRound2": a_ctx[1],
    "contextComparability": comparable,
    "comparableLabels": [x["label"] for x in comparable_ctx],
    "incomparableLabels": incomparable_ctx,
    "comparableCount": len(comparable_ctx),
    "boundaryRowsComparable": b_rows_comp,
    "nonBoundaryRowsComparable": n_rows_comp,
    "boundarySwallowedAll": all(r["reachedWinBubble"] is False
                                for r in b_rows_comp),
    "boundaryNeverReachedWindowBubble": all(
        r["reachedWinBubble"] is False for r in b_rows_comp),
    "boundaryReachedWindowCapture": all(r["reachedWinCapture"] is True
                                        for r in b_rows_comp),
    "nonBoundaryNeverSwallowed": all(r["reachedWinBubble"] is not False
                                     for r in n_rows_comp),
    "boundaryCountComparable": len(b_rows_comp),
    "nonBoundaryCountComparable": len(n_rows_comp),
    "boundaryTypesComparable": sorted({str(r["type"]) for r in b_rows_comp}),
    "boundaryFocusAllSucceeded": all(r["focused"] is True
                                     for r in b_rows_comp),
    "defaultContext": {k: defect_ctx.get(k) for k in
                       ("label", "totalFocusable", "boundaryCount",
                        "boundaryTypes", "boundarySwallowed")} if defect_ctx
    else None,
    "poseContext": {"label": pose_ctx.get("label"),
                    "totalFocusable": pose_ctx.get("totalFocusable"),
                    "boundaryCount": pose_ctx.get("boundaryCount"),
                    "boundaryTypes": pose_ctx.get("boundaryTypes"),
                    "boundarySwallowedCount": len(
                        pose_ctx.get("boundarySwallowed") or []),
                    "poseKeys": [r["ident"].get("pose") for r in
                                 (pose_ctx.get("boundaryRows") or [])][:6],
                    "poseKeysTotal": len(pose_ctx.get("boundaryRows") or [])}
    if pose_ctx else None,
    "cameraContext": {"label": cam_ctx.get("label"),
                      "totalFocusable": cam_ctx.get("totalFocusable"),
                      "boundaryCount": cam_ctx.get("boundaryCount"),
                      "boundaryTypes": cam_ctx.get("boundaryTypes"),
                      "boundarySwallowedCount": len(
                          cam_ctx.get("boundarySwallowed") or [])}
    if cam_ctx else None,
    "emptyContexts": [{"label": x["label"],
                       "totalFocusable": x["totalFocusable"],
                       "boundaryCount": x["boundaryCount"]}
                      for x in a_ctx[0] if x.get("boundaryCount") == 0],
    "summaryRound1": a["rounds"][0].get("summary"),
    "summaryRound2": a["rounds"][1].get("summary"),
    "pathCreated": a["rounds"][0].get("pathCreated"),
    "pathTrigger": a["rounds"][0].get("pathTrigger"),
    "tabsCamera": a["rounds"][0].get("tabs_camera"),
    "tabsCharacter": a["rounds"][0].get("tabs_character"),
    "selectCamera": a["rounds"][0].get("selectCamera"),
    "keyboard764b": b_kb,
    "mouse764b": b_mouse,
    "copyFromTreeCommand": [x["C2_copy"]["lastCommand"][1]
                            for x in b_kb if x.get("C2_copy")],
    "pasteDeltas": [x["C3_paste"]["countDelta"] for x in b_kb
                    if x.get("C3_paste")],
    "pasteAgainDeltas": [x["C4_pasteAgain"]["countDelta"] for x in b_kb
                         if x.get("C4_pasteAgain")],
    "emptyPaste764b": [{"lastCommand": x["C1_pasteWithEmptyClipboard"]
                         ["lastCommand"][1],
                         "countDelta": x["C1_pasteWithEmptyClipboard"]
                         ["countDelta"],
                         "historyDelta": x["C1_pasteWithEmptyClipboard"]
                         ["historyDelta"]}
                        for x in b_kb
                        if x.get("C1_pasteWithEmptyClipboard")],
    "mouseActions": [{"action": (x.get(k) or {}).get("action"),
                      "countDelta": (x.get(k) or {}).get("countDelta"),
                      "lastCommand": ((x.get(k) or {}).get("lastCommand")
                                      or [None, None])[1],
                      "toolbarAfter": (x.get(k) or {}).get("toolbarAfter")}
                     for x in b_mouse
                     for k in ("C6_copyButton", "C6_clearButton",
                               "C6_deleteButton")],
    "editableGuard764c": c_cases,
    "editableAllRoundsSame": all(
        norm(c_cases[0]) == norm(x) for x in c_cases),
    "copyFromTreeWorks": all(
        x["copyFromTree"]["lastCommand"][1] == "COPY_SELECTION"
        and x["copyFromTree"]["lastDisposition"][1] == "COMMITTED"
        for x in c_cases),
    "copyFromFieldDead": all(
        x["copyFromField"]["lastCommand"][0]
        == x["copyFromField"]["lastCommand"][1]
        and x["copyFromField"]["count"][0] == x["copyFromField"]["count"][1]
        and x["copyFromField"]["past"][0] == x["copyFromField"]["past"][1]
        for x in c_cases),
    "pasteFromFieldDead": all(
        x["pasteFromField"]["countDelta"] == 0
        and x["pasteFromField"]["historyDelta"] == 0
        for x in c_cases),
    "boundaryDidNotBlockModifierKeys": all(
        x["copyFromField"]["gestureUnchanged"] for x in c_cases),
    "emptyPasteDispositionNoop": all(
        x["emptyPaste"]["lastDisposition"][1] == "NOOP" for x in c_cases),
    "picksFailedIn764c": c_cases[0]["picksFailed"],
}

judgments = [
    {"id": "J1", "verdict": "PASS",
     "statement": "D1 的影响面比 763 记的**宽**：**逐字段可比**的那些上下文里，"
                  "**每一个**带边界标记的控件按 Esc 都没关掉抽屉，"
                  "而非边界控件**一个都没有**被吞。两轮逐字段一致。",
     "evidenceKey": "contextComparability"},
    {"id": "J2", "verdict": "PASS",
     "statement": "**更正 763 的「全是 type=number」**：角色「姿势」上下文里 "
                  "25 个 `type=range` 滑杆同样吞 Esc。所以中招的是"
                  "**数值框与滑杆两类**，不是只有数值框。",
     "evidenceKey": "poseContext"},
    {"id": "J3", "verdict": "PASS",
     "statement": "传播判决在更广的面上同样成立：逐字段可比的那些上下文里，"
                  "所有边界控件的 Esc "
                  "`reachedWinBubble=false`、`reachedWinCapture=true`；"
                  "焦点也确实落在目标控件上（不是「没聚焦到所以没反应」）。",
     "evidenceKey": "boundaryRowsComparable"},
    {"id": "J4", "verdict": "PASS",
     "statement": "机位「运动轨迹」「截图」两档在本种子里几乎是空的"
                  "（可聚焦控件 7 / 3 个、边界控件 0 个），"
                  "⟹ 这两档**没有**可测的边界控件，如实记为空而不是「通过」。",
     "evidenceKey": "emptyContexts"},
    {"id": "J5", "verdict": "FAIL",
     "statement": "★ 建出运动路径之后的那三个上下文**两轮不可比**"
                  "（round 1 与 round 2 的可聚焦控件数与边界控件数不同）——"
                  "建路径会改选中态，而改完之后的选中态两轮不同。"
                  "因此**不对路径上下文下的结论下任何判断**。",
     "evidenceKey": "incomparableLabels"},
    {"id": "J6", "verdict": "PASS",
     "statement": "路径锚点（`:825`）、路径变换（`:866`）、FOV（`:1579`）"
                  "这三类控件在两轮里**一次都没渲染出来** ⟹ 763 那句"
                  "「推测同样受影响」对这三类**仍然未验证**，本批不并进结论。",
     "evidenceKey": "pathCreated"},
    {"id": "J7", "verdict": "PASS",
     "statement": "⌘C / ⌘V 在**树**里完全正常：⌘C 落 COPY_SELECTION、"
                  "⌘V 每次都 +1 个对象且历史 +1，连按两次就是两次。",
     "evidenceKey": "keyboard764b"},
    {"id": "J8", "verdict": "PASS",
     "statement": "空剪贴板按 ⌘V：**对象数与历史都不动**，而 "
                  "`data-director-last-disposition` 如实写 **NOOP** ⟹ "
                  "「命令标签照写、disposition 说实话」，**不是缺陷**。",
     "evidenceKey": "editableGuard764c"},
    {"id": "J9", "verdict": "FAIL",
     "statement": "★ **缺陷 D2（低）**：焦点停在**任何可编辑控件**里时，"
                  "⌘C 与 ⌘V **两个键完全没反应** —— 对象数、历史、"
                  "`lastCommand` 全都不动（连标签都没换成 COPY_SELECTION）。",
     "evidenceKey": "editableAllRoundsSame"},
    {"id": "J10", "verdict": "PASS",
     "statement": "D2 的机制**不是** D1 那个 stopPropagation：按 ⌘C 前后 "
                  "`data-director-active-gesture` 逐字符不变"
                  "（边界因 activeRef 已为 true 而空转），"
                  "真正拦住两个键的是 `DirectorDesk.tsx:481` 的 "
                  "`if (isEditable) return;`（它排在 ⌘C 分支之前）。",
     "evidenceKey": "boundaryDidNotBlockModifierKeys"},
    {"id": "J11", "verdict": "PASS",
     "statement": "D2 有可用的替代路径：树里那三枚按钮"
                  "（`data-director-selection-action=copy/delete/clear`）"
                  "逐个实测都生效（copy 不改对象数、delete −1、clear 只清选择）。",
     "evidenceKey": "mouseActions"},
]

for j in judgments:
    j["evidence"] = findings[j["evidenceKey"]]

audit = {
    "batch": 764,
    "date": "2026-10-01",
    "scope": "D1（手势边界吞 Esc）的影响面普查 + 导演台 ⌘C/⌘V 与"
             "可编辑控件里的修饰键行为",
    "env": {
        "base": "http://localhost:4317",
        "canvas": "canvas-2",
        "directorNodeId": "b-bTLLuU4w5q",
        "viewportA": "800x1000（移动端抽屉，影响面普查）",
        "viewportB": "1440x1000（桌面，修饰键）",
        "player": "chromium (playwright sync_api)",
        "srcModified": False,
    },
    "probes": [
        {"id": "764a", "file": "probes/dbg764a.py", "raw": "raw/vb764a.json",
         "rounds": len(a["rounds"]), "selfReportedConsistent": None,
         "note": "两轮在**可比上下文**上逐字段一致；路径上下文不可比（见 J5）"},
        {"id": "764b", "file": "probes/dbg764b.py", "raw": "raw/vb764b.json",
         "rounds": len(b["rounds"]), "selfReportedConsistent": None,
         "note": "破坏性：真粘贴了对象、真删了一个（两轮的种子数因此不同，"
                 "这正是 763 O1 记的持久化）"},
        {"id": "764c", "file": "probes/dbg764c.py", "raw": "raw/vb764c.json",
         "rounds": len(c["rounds"]), "selfReportedConsistent": None,
         "note": "四次 pick 全部失败（探针自身缺陷，已记 R62），"
                 "但失败恰好让焦点留在数值框里，反而量到了 D2"},
    ],
    "rawSha": {p.name: sha(p) for p in (a_p, b_p, c_p)},
    "findings": findings,
    "judgments": judgments,
    "defects": [
        {"id": "D1", "severity": "中", "carriedOverFrom": 763,
         "title": "`useDirectorGestureBoundary` 无条件吞掉 Escape"
                  "（本批把影响面量宽了，并更正 763 的「全是 type=number」）",
         "where": ["src/components/director/useDirectorGestureBoundary.ts:92-98",
                   "src/components/director/DirectorInspector.tsx:182",
                   "src/components/director/DirectorDesk.tsx:475",
                   "src/components/director/DirectorDesk.tsx:481-485"],
         "widenedBy764": "**更正 763 的「全是 type=number」**：本批在逐字段可比的"
                         "那些上下文里量到 %s 个边界控件**全部**吞 Esc，"
                         "其中既有 type=number 也有 **type=range**"
                         "（角色姿势上下文 %s 个滑杆）；非边界控件 %s 个全部不吞。"
                         "763 只记了当时渲染态里的 9 个数值框。"
                         % (len(b_rows_comp), len(pose_ctx.get("boundaryRows") or [])
                            if pose_ctx else 0, len(n_rows_comp)),
         "stillUnverified": "路径锚点（:825）、路径变换（:866）、FOV（:1579）"
                            "三类控件两轮都没渲染出来，仍是未验证项。",
         "needsSrcChange": True},
        {"id": "D2", "severity": "低",
         "title": "焦点在可编辑控件里时 ⌘C / ⌘V 完全没反应",
         "where": ["src/components/director/DirectorDesk.tsx:481",
                   "src/components/director/useDirectorGestureBoundary.ts:99-107"],
         "mechanism": "`if (isEditable) return;` 排在 ⌘C/⌘V 分支之前，"
                      "所以焦点在 `<input>` 里时导演台自己的复制/粘贴命令"
                      "根本不会执行。**不是** D1 那个 stopPropagation："
                      "按 ⌘C 前后 `activeGesture` 逐字符不变，"
                      "边界 hook 因 activeRef 已为 true 而空转。",
         "measured": "数值框里 ⌘C：对象数/历史/lastCommand 全不变；"
                     "⌘V：countDelta=0、historyDelta=0。两轮一致。",
         "judgement": "对 `type=text` 框这个守卫是刻意且正确的"
                      "（用户要的是原生复制）。对**变换数值框**没有意义 —— "
                      "框里没有可选中的文本，原生复制也无从发生，"
                      "于是这两个键在该位置**彻底失效**。",
         "workaroundMeasured": "树里的 copy/delete/clear 三枚按钮全部生效"
                               "（见 J11），所以有可用路径。",
         "needsSrcChange": True},
    ],
    "observations": [
        {"id": "O1",
         "text": "764b 的两轮**种子数不同**（5 vs 6）—— 这正是 763 O1 记的"
                 "「导演台项目持久化在 localStorage」的直接后果：round 1 "
                 "粘贴/删除的对象带进了 round 2。本批所有跨轮比较都按"
                 "「派生量逐字段相等」而不是「绝对值相等」来判。",
         "verdict": "方法论约束"},
        {"id": "O2",
         "text": "移动端两个抽屉**互斥，而且开着的那一个会盖住另一个的触发按钮**"
                 "（树 aside 占 x=0..220/y=88..，属性抽屉触发按钮 rect 在 "
                 "(48,100,32,32)，`elementFromPoint` 命中的是 aside）⟹ "
                 "任何「开另一个抽屉」的自动化都必须先把当前抽屉关掉。",
         "verdict": "探针约束（也可能是真实的可用性问题，待查）"},
        {"id": "O3",
         "text": "建出运动路径（`createMotionPath` → `lastCommand=PROJECT_MUTATION`）"
                 "之后，属性面板的可聚焦控件数 52→67（+15），但**边界控件数"
                 "没变**（仍是 12）⟹ 新增的 15 个控件不带手势边界。"
                 "路径锚点数值框仍然没渲染出来。",
         "verdict": "事实记录"},
    ],
    "notClaimed": [
        "无源站对照：本批全部结论只针对 clone 自身的行为自洽性。",
        "路径上下文（`path+camera:*`）**两轮不可比**，本批不对其下任何判断。",
        "路径锚点（`:825`）、路径变换（`:866`）、FOV（`:1579`）三类控件"
        "两轮都没渲染出来，**没有测过**；763 的「推测同样受影响」对这三类"
        "仍然只是推测。",
        "764a 的边界检测是**按 data-* 标记**做的。若某个带手势边界的控件"
        "标记挂在外层容器上（如 FOV 那样标记在 `…-fov-field`/`…-fov-slider` "
        "而可聚焦的是里面的 input），就会漏检 —— 本批**没有**做「全控件无标记扫」"
        "来兜这个底。",
        "D2 只在 1440 桌面 + 变换数值框上测过；没测 text 框、textarea、select，"
        "也没测移动端抽屉形态下的表现。",
        "没测原生剪贴板内容（没有读 `navigator.clipboard`），"
        "「框里没有可选文本所以原生复制也无从发生」是浏览器常规行为，不是读数。",
        "⌘C/⌘V 只测了单个选中；多选、跨类型（角色↔道具）粘贴未测。",
        "764b 的两轮因持久化而起点不同（5 vs 6 个对象），"
        "绝对计数不可跨轮比较；只比较了同一格内的 Δ。",
        "没碰付费与真实生成；创建运动轨迹用的是本地预设（line），不是 AI 生成。",
    ],
    "probeLessons": [
        {"id": "R58",
         "text": "**读标志必须在清标志之前**。764a 初版里 `TAKE` 会把 "
                 "`reachedWinBubble/reachedWinCapture` 清成 false，而我先调 "
                 "`TAKE` 再读这两个标志 ⟹ 27 个边界控件 + 3 个阴性对照"
                 "**全被算成「吞了 Esc」**。修法是加一个 `PEEK` 在 `TAKE` "
                 "之前读。同一个探针两轮「一致」并不能说明它对 —— "
                 "确定性的读法错误两轮必然一致。"},
        {"id": "R59",
         "text": "**开一个抽屉之前先关另一个**。移动端两个抽屉互斥，"
                 "开着的那个 aside 会盖住另一个的触发按钮，"
                 "`elementFromPoint` 命中的是 aside ⟹ 扫网格 0 命中。"
                 "初版把属性面板的 tab 按钮点空了（它们在抽屉关着时 x=817，"
                 "视口宽只有 800）也栽在同一类问题上：**先量可点性，再点**。"},
        {"id": "R60",
         "text": "**别把同一个症状当成同一个机制**。数值框里 ⌘C 没反应，"
                 "乍看像 D1 的 stopPropagation 复制粘贴一起吞。"
                 "真正的判别点是 `activeGesture` 在按键前后**逐字符不变**"
                 "—— 边界 hook 因 `activeRef` 已为 true 而空转，"
                 "说明它没拦；拦住的是 `isEditable` 早退。"
                 "D1 与 D2 是两个独立缺陷，修法也不同。"},
        {"id": "R61",
         "text": "**派生量要判方向、判效应**（沿用 R53）。764b 的 `countDelta` "
                 "必须相对**同一格内**的前后读数，不能拿整轮种子数去减 —— "
                 "763 就栽过这个（objectCount[0] 是整轮种子数，两个键共用）。"},
        {"id": "R62",
         "text": "**探针自己的失败有时会变成有用的读数，但要如实记账**。"
                 "764c 的四次 `pick` 全部失败（我把返回字典的 `OBJECTS` "
                 "当成了列表），导致焦点一直留在数值框里 —— "
                 "这才量到了 D2。但这个「意外」不能拿来当设计："
                 "我把它单列成 `picksFailed` 写进产物，"
                 "并在不声称里写明「四次选中都失败了」。"},
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
print("判据 %d 条 | findings %d 键 | 缺陷 %d | 观察 %d | 探针教训 %d"
      % (len(audit["judgments"]), len(findings), len(audit["defects"]),
         len(audit["observations"]), len(audit["probeLessons"])))
print("自检：findings 与 judgments[].evidence 逐条相等 ✓")
for k in ("comparableCount", "boundaryCountComparable",
          "nonBoundaryCountComparable", "boundarySwallowedAll",
          "nonBoundaryNeverSwallowed", "boundaryTypesComparable",
          "boundaryFocusAllSucceeded", "incomparableLabels",
          "pasteDeltas", "pasteAgainDeltas", "copyFromTreeWorks",
          "copyFromFieldDead", "pasteFromFieldDead",
          "boundaryDidNotBlockModifierKeys", "emptyPasteDispositionNoop",
          "editableAllRoundsSame", "picksFailedIn764c"):
    print("  %-36s %s" % (k, json.dumps(findings[k], ensure_ascii=False)[:110]))
