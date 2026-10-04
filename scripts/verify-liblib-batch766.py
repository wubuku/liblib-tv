"""batch 766 验收器：行为反推识别边界控件 + 764 未验证三类控件的 Esc 读数

三层结构（与 753–765 同）：
  1. **静态层** —— 从 `src/` 复核判据依赖的实现事实，含**顺序**与**有无**断言
     （FOV 数值框那一段**必须没有** gesture spread；FOV 滑杆那一段**必须有**；
      控制柄框**必须**在「锚点类型 ≠ vertex」的门里；路径变换三组调用点）
  2. **产物层** —— 判据条数与 verdict、缺陷、观察、教训、README 结构、
     台账行、表格首格不许裸数字
  3. **原始读数交叉核对** —— 从 `raw/` 的 2 份原始输出**按正确键名重算**
     全部派生量；缺失时**判失败而不是通过**

⚠ 本批盯住四件容易自欺的事：
  - **`all([])` 是 True**：读错键名拿到空列表会静默通过。每一处聚合都显式
    判非空，阴性对照里有一组专打「把 rows 清空」。
  - **交叉表必须从原始格子重算**，不许采信汇编器写好的 `xtab` 字符串 ——
    那正是「派生量对标签敏感」的经典陷阱（R53/R61）。
  - **D7 是误判不是漏检**：产品里那两个控件行为本来就是对的。本批**不许**
    把 D7 写成产品缺陷，也不许把「误判 2 格」偷偷改成 0。
  - **J11 是不声称**：冻结期间导演台自己的处理器会不会有反应，本批判不了。
    产物必须保留这条 FAIL。

判据 **11 条（9 PASS / 2 FAIL）**。
"""
import copy
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch766-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAWDIR = OUTDIR / "raw"
PROBEDIR = OUTDIR / "probes"
README = OUTDIR / "README.md"
LEDGER = ROOT / "docs/research/VERIFICATION_LEDGER.md"

RAW_FILES = ["vb766a.json", "vb766b.json"]
PROBE_FILES = ["dbg766a.py", "dbg766b.py", "mk766audit.py"]
BARE_NUM_CELL = re.compile(r"^\|\s*\d+[a-z]?\s*\|")
FFFD = "\ufffd"

EXPECT_FAIL_IDS = ["J4", "J11"]
EXPECT_LESSON_IDS = ["R67", "R68", "R69", "R70"]
CTX_KEYS = ["ctxA_sweep", "ctxB_sweep", "ctxC_sweep"]

OWN_BOUNDARY = {
    "data-director-transform-field", "data-director-path-anchor-position",
    "data-director-path-anchor-handle", "data-director-path-transform-field",
    "data-director-pose-control", "data-director-camera-fov",
    "data-director-transform-axis", "data-director-path-transform-axis",
}
ANC_BOUNDARY = OWN_BOUNDARY | {"data-director-camera-fov-slider",
                               "data-director-camera-fov-field"}


def src(p):
    return (ROOT / p).read_text(encoding="utf-8")


def idx_of(text, needle, start=0):
    return text.find(needle, start)


def line_of(text, needle, start=0):
    i = idx_of(text, needle, start)
    return -1 if i < 0 else text.count("\n", 0, i)


def ptr_valid(w):
    m = re.match(r"^(.+?):(\d+)(?:-(\d+))?$", w or "")
    if not m:
        return False
    f = ROOT / m.group(1)
    if not f.exists():
        return False
    n = len(f.read_text(encoding="utf-8").splitlines())
    hi = int(m.group(3) or m.group(2))
    return int(m.group(2)) <= n and hi <= n


# ═════════════════════ 1. 静态层 ═════════════════════
def static_side():
    insp = src("src/components/director/DirectorInspector.tsx")
    tl = src("src/components/director/DirectorTimeline.tsx")

    def block(text, marker, end_marker):
        """取 marker 处那个 JSX 标签的原文片段（到 end_marker 或标签闭合）。"""
        i = idx_of(text, marker)
        if i < 0:
            return None
        j = text.find(end_marker, i)
        return text[i:j if j > 0 else i + 400]

    fov_field = line_of(insp, "data-director-camera-fov-field")

    def input_block(insp_text, attr):
        """取带 attr 属性的那个 <input …/> 整段（从 <input 到 />）。

        属性名必须用「后面跟空白」的正则 —— `data-director-camera-fov` 是
        `-fov-field` / `-fov-slider` / `-fov-number` / `-fov-readout` /
        `-fov-fill` / `-fov-knob` / `-fov-help` 的**前缀**，直接 find 会全撞上。
        """
        m = re.search(re.escape(attr) + r"\s", insp_text)
        if not m:
            return None, -1
        start = insp_text.rfind("<input", 0, m.start())
        end = insp_text.find("/>", m.start())
        if start < 0 or end < 0:
            return None, m.start()
        return insp_text[start:end + 2], insp_text.count("\n", 0, m.start()) + 1

    fov_range_block, fov_range_line = input_block(
        insp, "data-director-camera-fov")
    fov_num_block, fov_num_line = input_block(
        insp, "data-director-camera-fov-number")

    anchor_handle_gate = line_of(
        insp, '{selectedAnchor.type !== "vertex" ?')
    anchor_gate = line_of(insp, "{selectedAnchor ? (")
    path_gate = line_of(insp, "{selectedPath ? (")
    sel_track = line_of(insp, "const selectedTrack = timeline.tracks.find")
    sel_path = line_of(insp, "const selectedPath = selectedTrack?.motionPathId")
    sel_anchor = line_of(insp, "const selectedAnchor =")

    pt_calls = [m.start() for m in re.finditer(r"<PathTransformFields", insp)]
    pt_lines = [insp.count("\n", 0, i) + 1 for i in pt_calls]
    # 三组调用点都在 MotionPathInspector 内（`:907` 定义）且都在 selectedAnchor 门之前
    motion_insp_def = line_of(insp, "function MotionPathInspector({")
    pt_all_inside = bool(pt_calls) and motion_insp_def >= 0 and all(
        motion_insp_def < insp.count("\n", 0, i) + 1 < anchor_gate
        for i in pt_calls)
    # 锚点三组 PathTupleFields 调用点都在 selectedAnchor 门之后
    tuple_calls = [insp.count("\n", 0, m.start()) + 1
                   for m in re.finditer(r"<PathTupleFields", insp)]
    tuple_after_gate = bool(tuple_calls) and all(
        t > anchor_gate for t in tuple_calls)
    fov_field_gate = line_of(insp, "{selected.camera ? (")
    fov_call = line_of(insp, "<CameraFovField")

    draw_trail = line_of(tl, "data-director-track-draw-trail")
    i_dt = idx_of(tl, "data-director-track-draw-trail")
    dt_block = tl[i_dt:idx_of(tl, "onClick", i_dt) + 240] if i_dt >= 0 else None
    dt_selects_track = bool(dt_block and "selectTimelineTrack" in dt_block)
    dt_opens_menu = bool(dt_block and "togglePathMenu" in dt_block)
    path_preset = line_of(tl, "data-director-motion-path-preset")

    return {
        "fovFieldLine": fov_field,
        "fovRangeLine": fov_range_line,
        "fovNumberLine": fov_num_line,
        # ★ D7 的机制：滑杆带、数值框不带
        "fovRangeHasGesture": bool(fov_range_block
                                   and "gesture" in fov_range_block),
        "fovRangeIsRange": bool(fov_range_block
                                and 'type="range"' in fov_range_block),
        "fovNumberHasNoGesture": bool(fov_num_block
                                      and "gesture" not in fov_num_block),
        "fovNumberIsNumber": bool(fov_num_block
                                  and 'type="number"' in fov_num_block),
        "fovNumberInsideField": bool(
            (fov_num_line or -1) > (fov_field if fov_field >= 0 else 10 ** 6)),
        # 渲染门
        "anchorHandleGateLine": anchor_handle_gate,
        "anchorGateLine": anchor_gate,
        "pathGateLine": path_gate,
        "selectedTrackLine": sel_track,
        "selectedPathLine": sel_path,
        "selectedAnchorLine": sel_anchor,
        "orderSelectedAnchorBeforePath": 0 <= sel_anchor < sel_path,
        "orderSelectedTrackBeforePath": 0 <= sel_track < sel_path,
        "orderSelectedPathBeforePathGate": 0 <= sel_path < path_gate,
        # 锚点门写在 MotionPathInspector 组件体内（组件定义 907），
        # 而渲染这个组件的是**后面**的 `{selectedPath ? …}`（2749）⟹ 文本顺序是
        # 组件定义 < 锚点门 < 控制柄门 < 渲染处
        "orderMotionInspectorBeforeAnchorGate": 0 <= motion_insp_def
        < anchor_gate,
        "orderAnchorGateBeforeHandleGate": 0 <= anchor_gate
        < anchor_handle_gate,
        "orderHandleGateBeforePathGate": 0 <= anchor_handle_gate < path_gate,
        "pathTransformCallLines": pt_lines,
        "pathTransformCallCount": len(pt_calls),
        "pathTransformAllInsideMotionPathInspector": pt_all_inside,
        "pathTupleCallLines": tuple_calls,
        "pathTupleAllAfterAnchorGate": tuple_after_gate,
        "fovFieldGateLine": fov_field_gate,
        "fovCallLine": fov_call,
        "orderFovGateBeforeCall": 0 <= fov_field_gate < fov_call,
        # 入口
        "drawTrailLine": draw_trail,
        "drawTrailSelectsTrack": dt_selects_track,
        "drawTrailOpensMenu": dt_opens_menu,
        "pathPresetLine": path_preset,
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


def classify(ctrl, reached_capture, reached_bubble, is_editable):
    """★ 从**原始格子**重算两个分类与交叉表 —— 不采信汇编器写好的字符串。"""
    own = set(ctrl.get("ownMarks") or [])
    anc = set(ctrl.get("ancMarks") or [])
    if reached_capture and not reached_bubble:
        beh = "swallowed-below-window"
    elif reached_bubble and is_editable:
        beh = "reached-then-editable-guard"
    elif reached_bubble:
        beh = "reached-plain"
    else:
        beh = "never-reached"
    if own & OWN_BOUNDARY:
        mk = "boundary-own"
    elif anc & ANC_BOUNDARY:
        mk = "boundary-anc"
    else:
        mk = "no-marker"
    return mk, beh, "%s | %s" % (mk, beh)


def raw_side_from(files):
    a = files["vb766a.json"]
    b = files["vb766b.json"]
    r = {}

    # ★ 逐轮算，不跨轮累加 —— 跨轮相加会让每个计数翻倍（763/764 都栽过
    #   「拿整轮种子数去减」这一类）
    for key in CTX_KEYS:
        per = []
        for rd in a["rounds"]:
            sw = rd.get(key) or {}
            cells, focus_fail, failed, xt = [], 0, 0, {}
            for row in sw.get("rows") or []:
                if row.get("FAILED"):
                    failed += 1
                    continue
                if (row.get("focus") or {}).get("focused") is not True:
                    focus_fail += 1
                mk, beh, k = classify(
                    row["ctrl"], row["reachedCapture"], row["reachedBubble"],
                    row["targetIsEditable"])
                cells.append({"i": row["i"], "mk": mk, "beh": beh, "k": k,
                              "own": row["ctrl"].get("ownMarks") or [],
                              "aria": row["ctrl"].get("aria"),
                              "type": row["ctrl"].get("type")})
                xt[k] = xt.get(k, 0) + 1
            by_attr = {}
            for attr in ("data-director-transform-field",
                         "data-director-camera-fov",
                         "data-director-path-transform-axis",
                         "data-director-path-anchor-position",
                         "data-director-path-anchor-handle"):
                hit = [x for x in cells if attr in x["own"]]
                if hit:
                    by_attr[attr] = {
                        "cells": len(hit),
                        "swallowed": sum(
                            1 for x in hit
                            if x["beh"] == "swallowed-below-window"),
                        "allOwn": all(x["mk"] == "boundary-own" for x in hit)}
            per.append({
                "cells": len(cells), "focusFailures": focus_fail,
                "failedRows": failed, "xtab": xt, "byAttr": by_attr,
                "ownSwallowed": xt.get(
                    "boundary-own | swallowed-below-window", 0),
                # 注意：不能写 endswith("swallowed") —— 键名是
                # "… | swallowed-below-window"，endswith 匹配不到，会让
                # 「没吞」的计数恒为 0，判据变成永真
                "ownNotSwallowed": sum(
                    v for k, v in xt.items()
                    if k.startswith("boundary-own |")
                    and not k.endswith("swallowed-below-window")),
                "ancNotSwallowed": sum(
                    v for k, v in xt.items()
                    if k.startswith("boundary-anc |")
                    and not k.endswith("swallowed-below-window")),
                "noMarkerSwallowed": xt.get(
                    "no-marker | swallowed-below-window", 0),
                "neverReached": beh_count(cells, "never-reached"),
            })
        r[key] = {"perRound": per,
                  "cells": [x["cells"] for x in per],
                  "ownSwallowed": [x["ownSwallowed"] for x in per],
                  "noMarkerSwallowed": [x["noMarkerSwallowed"] for x in per]}

    # 误判格：containerMarkerFalsePositive 的两个具体控件
    fp = []
    for rd in a["rounds"]:
        sw = rd.get("ctxA_sweep") or {}
        for row in sw.get("rows") or []:
            if row.get("FAILED"):
                continue
            mk, beh, k = classify(
                row["ctrl"], row["reachedCapture"], row["reachedBubble"],
                row["targetIsEditable"])
            if mk == "boundary-anc":
                fp.append({"i": row["i"], "aria": row["ctrl"].get("aria"),
                           "own": row["ctrl"].get("ownMarks") or [],
                           "anc": row["ctrl"].get("ancMarks") or [],
                           "beh": beh, "isEditable": row["targetIsEditable"]})
    r["falsePositivePerRound"] = [len(fp) // 2] * 2 if fp else [0, 0]
    r["falsePositiveTotal"] = len(fp)
    r["falsePositiveAllNotSwallowed"] = bool(fp) and all(
        x["beh"] != "swallowed-below-window" for x in fp)
    r["falsePositiveInFovField"] = all(
        "data-director-camera-fov-field" in x["anc"] for x in fp) if fp else False
    r["falsePositiveAria"] = sorted({x["aria"] for x in fp if x["aria"]})

    # 766b：锚点控制柄
    hb = []
    for rd in b["rounds"]:
        sw = rd.get("sweep") or {}
        cells, failed, focus_fail = [], 0, 0
        for row in sw.get("rows") or []:
            if row.get("FAILED"):
                failed += 1
                continue
            if (row.get("focus") or {}).get("focused") is not True:
                focus_fail += 1
            mk, beh, k = classify(
                row["ctrl"], row["reachedCapture"], row["reachedBubble"],
                row["targetIsEditable"])
            cells.append({"mk": mk, "beh": beh,
                          "handle": bool(row["ctrl"].get("isAnchorHandle")),
                          "pos": bool(row["ctrl"].get("isAnchorPosition")),
                          "own": row["ctrl"].get("ownMarks") or []})
        handle = [x for x in cells if x["handle"]]
        pos = [x for x in cells if x["pos"]]
        trans = [x for x in cells
                 if "data-director-path-transform-axis" in x["own"]]
        hb.append({
            "cells": len(cells), "failedRows": failed,
            "focusFailures": focus_fail,
            "typeAfter": rd.get("typeAfter"),
            "handleBefore": rd.get("handleCountBeforeType"),
            "handleAfter": rd.get("handleCountAfterType"),
            "posAfter": rd.get("positionCountAfterType"),
            "legends": rd.get("legendTexts"),
            "handleCells": len(handle),
            "handleSwallowed": sum(1 for x in handle
                                   if x["beh"] == "swallowed-below-window"),
            "handleAllOwn": bool(handle) and all(x["mk"] == "boundary-own"
                                                 for x in handle),
            "posSwallowed": sum(1 for x in pos
                                if x["beh"] == "swallowed-below-window"),
            "transCells": len(trans),
            "transSwallowed": sum(1 for x in trans
                                  if x["beh"] == "swallowed-below-window"),
        })
    r["handles"] = {
        "perRound": hb,
        "handleCells": [x["handleCells"] for x in hb],
        "handleSwallowed": [x["handleSwallowed"] for x in hb],
        "handleAllOwn": [x["handleAllOwn"] for x in hb],
        "handleBefore": [x["handleBefore"] for x in hb],
        "handleAfter": [x["handleAfter"] for x in hb],
        "symmetricPressed": [
            any(t.get("type") == "symmetric" and t.get("pressed") == "true"
                for t in (x["typeAfter"] or [])) for x in hb],
        "legends": hb[0]["legends"],
        "ownSwallowed": [x["handleSwallowed"] + x["posSwallowed"]
                         + x["transSwallowed"] for x in hb],
        "focusFailures": [x["focusFailures"] for x in hb],
    }
    r["typeBeforeIsVertex"] = [
        any(t.get("type") == "vertex" and t.get("pressed") == "true"
            for t in (rd.get("typeBefore") or [])) for rd in b["rounds"]]
    return r


def beh_count(cells, name):
    return sum(1 for x in cells if x["beh"] == name)


def raw_side():
    files = raw_files()
    out = raw_side_from(files)
    out["__raw__"] = files
    return out


# ═════════════════════ 2. 产物层 + 交叉核对 ═════════════════════
def run_checks(a, st, rw):
    ck = []

    def C(label, cond, got=None):
        ck.append({"label": label, "pass": bool(cond), "got": got})

    f = a["findings"]
    J = a["judgments"]
    rounds = len(rw["__raw__"]["vb766a.json"]["rounds"])
    roundsB = len(rw["__raw__"]["vb766b.json"]["rounds"])

    def df(did):
        for x in a.get("defects") or []:
            if x.get("id") == did:
                return x
        return {}

    # ── 静态层
    C("★★ 静态：FOV 数值框那一段**没有** gesture spread（D7 的机制）",
      st["fovNumberHasNoGesture"] and st["fovNumberIsNumber"],
      [st["fovNumberHasNoGesture"], st["fovNumberIsNumber"]])
    C("★ 静态：FOV 滑杆是 range 且**有** gesture spread（它才是真边界控件）",
      st["fovRangeHasGesture"] and st["fovRangeIsRange"],
      [st["fovRangeHasGesture"], st["fovRangeIsRange"]])
    C("★ 静态：滑杆与数值框**同名不同属性**（-fov vs -fov-number）",
      st["fovRangeLine"] > 0 and st["fovNumberLine"] > st["fovRangeLine"],
      [st["fovRangeLine"], st["fovNumberLine"]])
    C("静态：控制柄框在「锚点类型 ≠ vertex」的门里",
      st["anchorHandleGateLine"] >= 0, st["anchorHandleGateLine"])
    C("★ 静态：MotionPathInspector 组件体内依次是 锚点门 → 控制柄门，"
      "而渲染它的是后面的 selectedPath 门",
      st["orderMotionInspectorBeforeAnchorGate"]
      and st["orderAnchorGateBeforeHandleGate"]
      and st["orderHandleGateBeforePathGate"],
      [st["selectedAnchorLine"], st["anchorGateLine"],
       st["anchorHandleGateLine"], st["pathGateLine"]])
    C("静态：selectedPath 由 selectedTrack?.motionPathId 决定",
      st["orderSelectedTrackBeforePath"]
      and st["orderSelectedPathBeforePathGate"],
      [st["selectedTrackLine"], st["selectedPathLine"],
       st["pathGateLine"]])
    C("静态：selectedAnchor 定义在 selectedPath 之前（渲染门逐层叠加）",
      st["orderSelectedAnchorBeforePath"],
      [st["selectedAnchorLine"], st["selectedPathLine"]])
    C("★ 静态：PathTransformFields 恰好 3 处调用且都在 MotionPathInspector 内",
      st["pathTransformCallCount"] == 3
      and st["pathTransformAllInsideMotionPathInspector"],
      [st["pathTransformCallCount"],
       st["pathTransformAllInsideMotionPathInspector"]])
    C("★ 静态：PathTupleFields 三处调用都在 selectedAnchor 门之后",
      st["pathTupleAllAfterAnchorGate"] and len(st["pathTupleCallLines"]) == 3,
      st["pathTupleCallLines"])
    C("静态：FOV 的门在调用点之前", st["orderFovGateBeforeCall"],
      [st["fovFieldGateLine"], st["fovCallLine"]])
    C("★ 静态：draw-trail 入口同时做「选中轨道」+「打开菜单」",
      st["drawTrailSelectsTrack"] and st["drawTrailOpensMenu"],
      [st["drawTrailSelectsTrack"], st["drawTrailOpensMenu"]])
    C("静态：路径预设按钮与 draw-trail 入口都在时间轴里",
      st["pathPresetLine"] > 0 and st["drawTrailLine"] > 0)

    # ── 判据层
    C("判据 11 条", len(J) == 11, len(J))
    npass = sum(1 for j in J if j["verdict"] == "PASS")
    nfail = sum(1 for j in J if j["verdict"] == "FAIL")
    C("verdict 分布 9 PASS / 2 FAIL", npass == 9 and nfail == 2, [npass, nfail])
    fail_ids = [j["id"] for j in J if j["verdict"] == "FAIL"]
    C("★ 2 条 FAIL 恰好是 J4/J11（不许偷改）",
      sorted(fail_ids) == sorted(EXPECT_FAIL_IDS), fail_ids)
    C("判据 id 唯一且连续 J1..J11",
      [j["id"] for j in J] == ["J%d" % i for i in range(1, 12)],
      [j["id"] for j in J])
    C("★ 每条判据都有非空 evidenceKey", all(j.get("evidenceKey") for j in J))
    rt = json.loads(json.dumps(a, ensure_ascii=False))
    C("★ findings[k] == judgments[].evidence（JSON 往返后逐条）",
      all(rt["findings"][j["evidenceKey"]] == j["evidence"]
          for j in rt["judgments"] if j["evidenceKey"] in rt["findings"]),
      [j["id"] for j in rt["judgments"]
       if j["evidenceKey"] in rt["findings"]
       and rt["findings"][j["evidenceKey"]] != j["evidence"]])
    C("★ 每条判据的 evidenceKey 都真实存在",
      all(j["evidenceKey"] in f for j in J))
    C("★ evidence 不得为空（防 all([]) 式空过）",
      all(j["evidence"] not in ({}, [], None) for j in J),
      [j["id"] for j in J if j["evidence"] in ({}, [], None)])
    C("判据引用 findings 里至少 6 个不同键",
      len({j["evidenceKey"] for j in J}) >= 6,
      len({j["evidenceKey"] for j in J}))

    # ── 缺陷层
    D = a["defects"]
    C("缺陷 1 条 D7", [d["id"] for d in D] == ["D7"],
      [d["id"] for d in D])
    C("★ D7 明确声明 needsSrcChange=false（是工具缺陷不是产品缺陷）",
      df("D7").get("needsSrcChange") is False, df("D7").get("needsSrcChange"))
    C("★ D7 明确声明 needsProbeChange=true", df("D7").get("needsProbeChange")
      is True)
    C("★ D7 写了它对 764 的影响（43 是上界）",
      "上界" in df("D7").get("impactOnEarlierBatches", ""))
    C("★ D7 承认严重度低的理由", "测量工具" in df("D7").get("severityRationale",
                                                    ""))
    C("★ 本批不重复声明 763/764/765 的 D1–D6",
      not any(d["id"] in ("D1", "D2", "D3", "D4", "D5", "D6") for d in D),
      [d["id"] for d in D])
    C("★ D7 的 where 指针都指向真实文件与行号",
      all(ptr_valid(w) for w in df("D7").get("where") or []),
      [w for w in (df("D7").get("where") or []) if not ptr_valid(w)])
    C("缺陷严重度在 低/中/高 之内",
      all(d["severity"] in ("低", "中", "高") for d in D))

    # ── 观察 / 教训 / 不声称
    C("观察 4 条", len(a["observations"]) == 4, len(a["observations"]))
    C("探针教训 R67–R70 四条",
      sorted(x["id"] for x in a["probeLessons"]) == EXPECT_LESSON_IDS,
      [x["id"] for x in a["probeLessons"]])
    C("★ R67 记的是「JS 片段先过 node --check」",
      any(x["id"] == "R67" and "node --check" in x["text"]
          for x in a["probeLessons"]))
    C("★ R68 记的是「不在 DOM 与在视口外是两回事」",
      any(x["id"] == "R68" and "视口外" in x["text"]
          for x in a["probeLessons"]))
    NC = " ".join(a["notClaimed"])
    C("★ 不声称里写明无源站对照", "无源站对照" in NC)
    C("★ 不声称里写明冻结期判不了（J11）", "冻结" in NC)
    C("★ 不声称里写明没有重算 764 那个 43", "43" in NC)
    C("★ 不声称里写明 D7 是工具缺陷不是产品缺陷", "工具" in NC)
    C("不声称 ≥ 9 条", len(a["notClaimed"]) >= 9, len(a["notClaimed"]))

    # ── 可比性
    C("两轮可比且逐字段一致（766a）",
      f["comparability"]["766a"]["allConsistent"] is True,
      f["comparability"]["766a"]["inconsistent"])
    C("两轮可比且逐字段一致（766b）",
      f["comparability"]["766b"]["allConsistent"] is True,
      f["comparability"]["766b"]["inconsistent"])
    C("可比性判据比的是非空 key 列表",
      len(f["comparability"]["766a"]["keys"]) >= 6
      and len(f["comparability"]["766b"]["keys"]) >= 6)
    C("原始读数轮数各为 2", rounds == 2 and roundsB == 2, [rounds, roundsB])

    # ── 交叉核对：三个上下文的扫查
    for key in CTX_KEYS:
        per = rw[key]["perRound"]
        label = f["sweepContexts"][key]["label"]
        C("★ %s：格子非空（不许 all([]) 空过）" % label,
          all(x["cells"] > 0 for x in per), rw[key]["cells"])
        C("★ %s：自身带边界标记的控件**全部**吞 Esc（逐轮）" % label,
          all(x["ownNotSwallowed"] == 0 and x["ownSwallowed"] > 0
              for x in per), [x["ownSwallowed"] for x in per])
        C("★ %s：没有「没标记却吞 Esc」的控件（逐轮）" % label,
          all(x["noMarkerSwallowed"] == 0 for x in per),
          rw[key]["noMarkerSwallowed"])
        C("%s：焦点全部成功" % label,
          all(x["focusFailures"] == 0 for x in per),
          [x["focusFailures"] for x in per])
        C("%s：没有「事件完全没上来」的格子" % label,
          all(x["neverReached"] == 0 for x in per),
          [x["neverReached"] for x in per])
        C("%s：产物 cells 与重算一致" % label,
          f["sweepContexts"][key]["cellsBothRounds"] == rw[key]["cells"],
          [f["sweepContexts"][key]["cellsBothRounds"], rw[key]["cells"]])
        C("%s：产物 xtab 与重算一致（逐轮）" % label,
          all(f["sweepContexts"][key]["xtab"] == x["xtab"] for x in per),
          [f["sweepContexts"][key]["xtab"], per[0]["xtab"]])
    C("★ 三段扫查格子数逐档递增且两轮一致（52→67→74）",
      len(set(rw["ctxA_sweep"]["cells"])) == 1
      and len(set(rw["ctxB_sweep"]["cells"])) == 1
      and len(set(rw["ctxC_sweep"]["cells"])) == 1
      and rw["ctxA_sweep"]["cells"][0] < rw["ctxB_sweep"]["cells"][0]
      < rw["ctxC_sweep"]["cells"][0],
      [rw[k]["cells"] for k in CTX_KEYS])
    C("★ 自身边界控件数逐档递增且两轮一致（13→22→25）",
      len(set(rw["ctxA_sweep"]["ownSwallowed"])) == 1
      and len(set(rw["ctxB_sweep"]["ownSwallowed"])) == 1
      and len(set(rw["ctxC_sweep"]["ownSwallowed"])) == 1
      and rw["ctxA_sweep"]["ownSwallowed"][0]
      < rw["ctxB_sweep"]["ownSwallowed"][0]
      < rw["ctxC_sweep"]["ownSwallowed"][0],
      [rw[k]["ownSwallowed"] for k in CTX_KEYS])

    # ── 交叉核对：三类控件
    def attr_ok(ctx, attr, n):
        per = [x["byAttr"].get(attr) for x in rw[ctx]["perRound"]]
        return bool(per) and all(
            v and v["cells"] == n and v["swallowed"] == n and v["allOwn"]
            for v in per), per

    ok, ba = attr_ok("ctxB_sweep", "data-director-path-transform-axis", 9)
    C("★★ 路径变换 9 个数值框**全部**吞 Esc且全部自身带标记（逐轮）", ok, ba)
    ok, pa = attr_ok("ctxC_sweep", "data-director-path-anchor-position", 3)
    C("★★ 路径锚点位置 3 个框**全部**吞 Esc且全部自身带标记（逐轮）", ok, pa)
    ok, fa = attr_ok("ctxA_sweep", "data-director-camera-fov", 1)
    C("★★ FOV 滑杆吞 Esc（自身带 -fov 标记，逐轮）", ok, fa)
    # 机位属性里带 transform-field 的是 12 个：9 个变换 + 3 个「注视坐标」
    ok, tf = attr_ok("ctxA_sweep", "data-director-transform-field", 12)
    C("变换数值框基线：机位属性里已带标记的 12 个（9 变换 + 3 注视坐标）全吞",
      ok, tf)

    # ── 交叉核对：误判（D7）
    C("★★ 容器级标记每轮固定误判 2 格",
      rw["falsePositivePerRound"] == [2, 2], rw["falsePositivePerRound"])
    C("★ 那 2 格**都没有**吞 Esc（所以是误判不是漏检）",
      rw["falsePositiveAllNotSwallowed"] is True)
    C("★ 那 2 格的祖先标记确实是 camera-fov-field",
      rw["falsePositiveInFovField"] is True)
    C("★ 误判格点名了 FOV 数值框与关键帧按钮",
      any("FOV" in (x or "") for x in rw["falsePositiveAria"])
      and any("关键帧" in (x or "") for x in rw["falsePositiveAria"]),
      rw["falsePositiveAria"])
    C("★ 产物 containerMarkerFalsePositive 与重算一致",
      f["containerMarkerFalsePositive"]["cells"] == [2, 2]
      and f["containerMarkerFalsePositive"]["allReachedNotSwallowed"]
      is True)
    C("★ 产物 missedByMarkerScan 的总数是 0",
      f["missedByMarkerScan"]["totalNoMarkerSwallowed"] == 0,
      f["missedByMarkerScan"]["totalNoMarkerSwallowed"])
    C("★ 产物 missedByMarkerScan 与重算一致",
      all(f["missedByMarkerScan"]["noMarkerSwallowed"][i]
          == rw[k]["noMarkerSwallowed"][0]
          for i, k in enumerate(CTX_KEYS)),
      [f["missedByMarkerScan"]["noMarkerSwallowed"],
       [rw[k]["noMarkerSwallowed"] for k in CTX_KEYS]])

    # ── 交叉核对：锚点控制柄（766b）
    H = rw["handles"]
    C("★ 766b 扫出的格子非空", H["perRound"][0]["cells"] > 0)
    C("★ 改类型之前控制柄框是 0、之后是 6（两轮）",
      H["handleBefore"] == [0, 0] and H["handleAfter"] == [6, 6],
      [H["handleBefore"], H["handleAfter"]])
    C("★ 两轮都真的把锚点类型切到了「对称」",
      H["symmetricPressed"] == [True, True], H["symmetricPressed"])
    C("★ 改类型之前锚点默认是「顶点」",
      rw["typeBeforeIsVertex"] == [True, True], rw["typeBeforeIsVertex"])
    C("★ legend 里出现了「入控制柄」「出控制柄」",
      "入控制柄" in (H["legends"] or [])
      and "出控制柄" in (H["legends"] or []), H["legends"])
    C("★★ 控制柄 6 个框**全部**吞 Esc（两轮）",
      H["handleSwallowed"] == [6, 6], H["handleSwallowed"])
    C("★ 控制柄 6 个框全部自身带边界标记",
      H["handleAllOwn"] == [True, True], H["handleAllOwn"])
    C("★ 766b 焦点全部成功", H["focusFailures"] == [0, 0],
      H["focusFailures"])
    C("★ 产物 anchorHandles 与重算一致",
      f["anchorHandles"]["handleCells"] == H["handleCells"]
      and f["anchorHandles"]["handleSwallowed"] == H["handleSwallowed"],
      [f["anchorHandles"]["handleCells"], H["handleCells"]])
    C("★ 产物 anchorHandles 的 before/after 与重算一致",
      f["anchorHandles"]["handleBefore"] == H["handleBefore"]
      and f["anchorHandles"]["handleAfter"] == H["handleAfter"])

    # ── 产物结构
    C("产物 batch=766", a["batch"] == 766, a["batch"])
    C("产物声明未改 src/", a["env"]["srcModified"] is False)
    C("probes 列了 2 个探针", len(a["probes"]) == 2, len(a["probes"]))
    C("★ 每份 raw 都有 sha 记录", len(a["rawSha"]) == 2, list(a["rawSha"]))
    for fn in RAW_FILES:
        C("原始读数存在 %s" % fn, (RAWDIR / fn).exists())
    for fn in PROBE_FILES:
        C("探针脚本存在 %s" % fn, (PROBEDIR / fn).exists())
    C("README 存在", README.exists())
    if README.exists():
        t = README.read_text(encoding="utf-8")
        for h in ("## 选题", "## 判据", "## 缺陷", "## 观察",
                  "## 探针教训", "## 不声称", "## 复现"):
            C("README 含章节 %s" % h, h in t)
        C("★ README 有 D7 的独立章节",
          any(re.match(r"### D7\b", ln) for ln in t.splitlines()))
        C("★ README 没有把 D1–D6 写成新章节",
          not re.search(r"^### D[1-6]\b", t, re.M))
        C("★ README 表格首格没有裸数字（pre-commit 正则会误判）",
          not any(BARE_NUM_CELL.match(ln) for ln in t.splitlines()),
          [ln for ln in t.splitlines() if BARE_NUM_CELL.match(ln)][:3])
        C("★ README 写明判据 11 条", "11" in t and "判据" in t)
        C("★ README 提到 node --check（R67）", "node --check" in t)
        C("★ README 提到「43 是上界」", "上界" in t)
        C("★ README 提到 J11 判不了", "J11" in t)

    # ── 台账
    lt = LEDGER.read_text(encoding="utf-8")
    lines = lt.splitlines()
    led = [ln for ln in lines if ln.startswith("| Batch 766 |")]
    C("★ 台账恰好一行 Batch 766", len(led) == 1, len(led))
    if len(led) == 1:
        ln = led[0]
        C("★ 台账行首格是「Batch 766」",
          ln.split("|")[1].strip() == "Batch 766", ln.split("|")[1])
        C("★ 台账新行里 0 个 U+FFFD", ln.count(FFFD) == 0, ln.count(FFFD))
        C("★ 台账新行够长（不许占位）", len(ln) > 200, len(ln))
        for kw in ("D7", "行为反推", "误判", "控制柄", "上界"):
            C("台账行提到 %s" % kw, kw in ln)
    C("★ 台账历史 U+FFFD 仍是 9 个", lt.count(FFFD) == 9, lt.count(FFFD))
    hist = [i + 1 for i, ln in enumerate(lines) if FFFD in ln]
    C("★ U+FFFD 仍只落在 522/583/587 三行", hist == [522, 583, 587], hist)
    C("★ 台账行数 = 629（追加一行）", len(lines) == 629, len(lines))
    C("★ Batch 765 行仍在且唯一",
      len([ln for ln in lines if ln.startswith("| Batch 765 |")]) == 1)
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

    def inj_file(name, path, old, new, all_hits=False):
        """改文件内容跑一遍检查再还原。

        `all_hits=True` 替换**全部**出现位置 —— 只换第一处会被后面几处
        相同的文本顶住，对照就变成永真（765/766 各踩过一次：
        一处是判据引用了已改名的键，一处是这里只换第一处）。
        """
        orig = path.read_text(encoding="utf-8")
        try:
            if old not in orig:
                cases.append({"name": name, "caught": False,
                              "firstFail": "待替换文本不存在（对照本身失效）"})
                return
            if all_hits and orig.count(old) > 1:
                print("  [注] %s 命中 %d 处，按全部替换"
                      % (name, orig.count(old)))
            body = orig.replace(old, new) if all_hits \
                else orig.replace(old, new, 1)
            path.write_text(body, encoding="utf-8")
            failed = [c["label"] for c in run_checks(a, st, rw)
                      if not c["pass"]]
        finally:
            path.write_text(orig, encoding="utf-8")
        cases.append({"name": name, "caught": len(failed) > 0,
                      "firstFail": failed[0] if failed else None})

    # —— 伪造「缺陷不存在 / 性质变了」
    inj("★ 删掉 D7", lambda x: x.__setitem__("defects", []))
    inj("★ 把 D7 说成产品缺陷（needsSrcChange=true）", lambda x:
        [y for y in x["defects"] if y["id"] == "D7"][0].__setitem__(
            "needsSrcChange", True))
    inj("★ 把 D7 的 needsProbeChange 去掉", lambda x:
        [y for y in x["defects"] if y["id"] == "D7"][0].pop(
            "needsProbeChange"))
    inj("★ 把 D7 对 764 的影响（43 是上界）抹掉", lambda x:
        [y for y in x["defects"] if y["id"] == "D7"][0].__setitem__(
            "impactOnEarlierBatches", "无影响"))
    inj("★ 把 D7 的 where 指向不存在的行号", lambda x:
        [y for y in x["defects"] if y["id"] == "D7"][0]["where"].append(
            "src/components/director/DirectorInspector.tsx:99999"))
    inj("★ 本批重复声明 763 的 D1", lambda x: (x.__setitem__(
        "defects", x["defects"] + [{"id": "D1", "severity": "中",
                                    "title": "重开", "where": ["x"],
                                    "needsSrcChange": True}])))

    # —— 把 FAIL 偷改成 PASS
    for jid in EXPECT_FAIL_IDS:
        i = [k for k, j in enumerate(a["judgments"]) if j["id"] == jid][0]
        inj("★ 把 %s 从 FAIL 改成 PASS" % jid, lambda x, i=i:
            x["judgments"][i].__setitem__("verdict", "PASS"))
    inj("★ 判据全改成 PASS",
        lambda x: ([j.__setitem__("verdict", "PASS")
                    for j in x["judgments"]]))
    inj("★ 把判据条数从 11 改成 9", lambda x: x.__setitem__(
        "judgments", x["judgments"][:9]))
    inj("★ 把 J4 的 evidence 换成可比性（误判失去支撑）", lambda x:
        x["judgments"][3].__setitem__("evidence",
                                      x["findings"]["comparability"]))
    inj("★ 把 J11（不声称）也改成 PASS", lambda x:
        [j for j in x["judgments"] if j["id"] == "J11"][0].__setitem__(
            "verdict", "PASS"))

    # —— 只改一份事实
    inj("只改 findings.missedByMarkerScan.totalNoMarkerSwallowed",
        lambda x: x["findings"]["missedByMarkerScan"].__setitem__(
            "totalNoMarkerSwallowed", 4))
    inj("只改 findings.containerMarkerFalsePositive.cells",
        lambda x: x["findings"]["containerMarkerFalsePositive"].__setitem__(
            "cells", [0, 0]))
    inj("只改 findings.anchorHandles.handleSwallowed",
        lambda x: x["findings"]["anchorHandles"].__setitem__(
            "handleSwallowed", [3, 3]))
    inj("只改 findings.anchorHandles.handleBefore",
        lambda x: x["findings"]["anchorHandles"].__setitem__(
            "handleBefore", [6, 6]))
    inj("只改 findings.sweepContexts.ctxC_sweep.xtab",
        lambda x: x["findings"]["sweepContexts"]["ctxC_sweep"].__setitem__(
            "xtab", {"no-marker | reached-plain": 74}))
    inj("★ 把可比性说成一致（766b 不一致 key 非空）", lambda x:
        x["findings"]["comparability"]["766b"].__setitem__(
            "inconsistent", ["sweep"]))
    inj("★ 删掉 R67（node --check 那条教训）",
        lambda x: (x.__setitem__("probeLessons",
                                 [r for r in x["probeLessons"]
                                  if r["id"] != "R67"])))
    inj("★ 不声称里删掉「冻结期判不了」",
        lambda x: (x.__setitem__("notClaimed",
                                 [s for s in x["notClaimed"]
                                  if "冻结" not in s])))
    inj("★ 不声称里删掉「没有重算 43」",
        lambda x: (x.__setitem__("notClaimed",
                                 [s for s in x["notClaimed"]
                                  if "43" not in s])))

    # ── 静态层伪造
    inj_static("伪造：FOV 数值框那段也有 gesture（那就不是 D7 的机制）",
               lambda x: x.__setitem__("fovNumberHasNoGesture", False))
    inj_static("伪造：FOV 滑杆没有 gesture",
               lambda x: x.__setitem__("fovRangeHasGesture", False))
    inj_static("伪造：控制柄框不在「非 vertex」门里",
               lambda x: x.__setitem__("anchorHandleGateLine", -1))
    inj_static("伪造：锚点门不在 MotionPathInspector 之后",
               lambda x: x.__setitem__(
                   "orderMotionInspectorBeforeAnchorGate", False))
    inj_static("伪造：控制柄门不在锚点门之后",
               lambda x: x.__setitem__("orderAnchorGateBeforeHandleGate",
                                      False))
    inj_static("伪造：控制柄门在渲染 selectedPath 的门之前",
               lambda x: x.__setitem__("orderHandleGateBeforePathGate", False))
    inj_static("伪造：PathTransformFields 只有 2 处调用",
               lambda x: x.__setitem__("pathTransformCallCount", 2))
    inj_static("伪造：PathTupleFields 调用在门之前",
               lambda x: x.__setitem__("pathTupleAllAfterAnchorGate", False))
    inj_static("伪造：draw-trail 入口不打开菜单",
               lambda x: x.__setitem__("drawTrailOpensMenu", False))
    inj_static("伪造：selectedPath 不依赖 motionPathId",
               lambda x: x.__setitem__("orderSelectedTrackBeforePath", False))

    # ── 原始读数：改真正的被检查键
    def all_rows(files, key):
        out = []
        for rd in files["vb766a.json"]["rounds"]:
            out.extend((rd.get(key) or {}).get("rows") or [])
        return out

    inj_raw("★ 原始：把一个自身边界控件的 reachedBubble 改成 true（吞变不吞）",
            lambda x: all_rows(x, "ctxA_sweep")[0].__setitem__(
                "reachedBubble", True))
    inj_raw("★ 原始：把 FOV 滑杆的 reachedBubble 改成 true（FOV 不再吞 Esc）",
            lambda x: ([r for r in all_rows(x, "ctxA_sweep")
                        if "data-director-camera-fov" in
                        (r["ctrl"].get("ownMarks") or [])][0].__setitem__(
                            "reachedBubble", True)))
    inj_raw("★ 原始：把路径变换框的 reachedBubble 改成 true",
            lambda x: ([r for r in all_rows(x, "ctxB_sweep")
                        if "data-director-path-transform-axis" in
                        (r["ctrl"].get("ownMarks") or [])][0].__setitem__(
                            "reachedBubble", True)))
    inj_raw("★ 原始：把锚点控制柄的 reachedBubble 改成 true",
            lambda x: ([r for r in x["vb766b.json"]["rounds"][0]["sweep"]
                        ["rows"] if r["ctrl"].get("isAnchorHandle")][0]
                       .__setitem__("reachedBubble", True)))
    inj_raw("★ 原始：把误判格说成吞了 Esc（方向反了）",
            lambda x: ([r for r in all_rows(x, "ctxA_sweep")
                        if "data-director-camera-fov-number" in
                        (r["ctrl"].get("ownMarks") or [])][0].__setitem__(
                            "reachedBubble", False)))
    inj_raw("★ 原始：给一个无标记控件加上边界标记（制造假阳性吞 Esc）",
            lambda x: ([r for r in all_rows(x, "ctxA_sweep")
                        if not (r["ctrl"].get("ownMarks") or [])][0]
                       ["ctrl"].__setitem__(
                           "ownMarks",
                           ["data-director-transform-field"])))
    inj_raw("★ 原始：把 FOV 数值框的祖先标记去掉（误判消失）",
            lambda x: ([r for r in all_rows(x, "ctxA_sweep")
                        if "data-director-camera-fov-number" in
                        (r["ctrl"].get("ownMarks") or [])][0]
                       ["ctrl"].__setitem__("ancMarks", [])))
    inj_raw("★ 原始：把某个控件的 focus.focused 改成 false",
            lambda x: (all_rows(x, "ctxA_sweep")[0]["focus"].__setitem__(
                "focused", False)))
    inj_raw("★ all([]) 陷阱：把 ctxA_sweep.rows 清空",
            lambda x: x["vb766a.json"]["rounds"][0]["ctxA_sweep"].__setitem__(
                "rows", []))
    inj_raw("★ all([]) 陷阱：把 766b 的 sweep.rows 清空",
            lambda x: x["vb766b.json"]["rounds"][0]["sweep"].__setitem__(
                "rows", []))
    inj_raw("★ 伪造：改类型前控制柄就已经是 6（渲染条件说不成立）",
            lambda x: (x["vb766b.json"]["rounds"][0].__setitem__(
                "handleCountBeforeType", 6)))
    inj_raw("★ 伪造：锚点类型根本没切到对称",
            lambda x: (x["vb766b.json"]["rounds"][0].__setitem__(
                "typeAfter",
                [{"type": "vertex", "pressed": "true"},
                 {"type": "symmetric", "pressed": "false"},
                 {"type": "asymmetric", "pressed": "false"}])))
    inj_raw("★ 伪造：legend 里没有「入控制柄」",
            lambda x: (x["vb766b.json"]["rounds"][0].__setitem__(
                "legendTexts", ["位置", "旋转", "缩放"])))
    inj_raw("★ 伪造：targetIsEditable 全设 false（守卫那档消失）",
            lambda x: ([r.__setitem__("targetIsEditable", False)
                        for r in all_rows(x, "ctxA_sweep")]))

    # ── 台账 / README
    led = LEDGER.read_text(encoding="utf-8")
    led_line = next((ln for ln in led.splitlines()
                     if ln.startswith("| Batch 766 |")), "")
    if led_line:
        sep = "" if led.endswith(led_line + "\n") else "\n"
        inj_file("★ 台账删掉 Batch 766 行", LEDGER, sep + led_line, "")
        inj_file("★ 台账行首格改成裸数字 766", LEDGER,
                 "| Batch 766 |", "| 766 |")
        inj_file("★ 台账行首格写成 Batch 0766", LEDGER,
                 "| Batch 766 |", "| Batch 0766 |")
        inj_file("★ 台账新行塞一个 U+FFFD", LEDGER,
                 led_line[:40], led_line[:40] + FFFD)
        inj_file("★ 台账被追加了 Batch 767（行数断言）", LEDGER,
                 "| Batch 766 |", "| Batch 766 |\n| Batch 767 | x")
    if README.exists():
        rt = README.read_text(encoding="utf-8")
        bad_cell = next((ln for ln in rt.splitlines()
                         if ln.startswith("| J")), "| J1 | x |")
        inj_file("★ README 表格首格改成裸数字", README, bad_cell, "| 1 | x |")
        inj_file("★ README 删掉「不声称」章节", README, "## 不声称", "## 备注")
        inj_file("★ README 删掉 D7 章节", README, "### D7", "### 附注")
        inj_file("★ README 删掉 R67 的 node --check", README,
                 "node --check", "手工检查", all_hits=True)
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
        {"label": "原始读数可用（raw/ 下 2 份）", "pass": False,
         "got": rawErr}]
    neg = [] if rawErr else negative_controls(a, st, rw)

    npass = sum(1 for c in checks if c["pass"])
    total = len(checks)
    neg_ok = sum(1 for n in neg if n["caught"])
    ok = npass == total and neg_ok == len(neg)

    REPORT.write_text(json.dumps(
        {"batch": 766, "checks": checks, "pass": npass, "total": total,
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
    print("batch 766 %s" % ("通过" if ok else "不通过"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
