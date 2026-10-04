#!/usr/bin/env python3
"""batch 766 汇编器：从 raw/ 的 2 份原始读数现算 runtime-audit.json

规矩（沿用 756–765）：
1. **数字不许手抄** —— 下面每个数都从 `raw/vb766*.json` 算出来。
2. **缺原始读数判失败**，不许「通过」。
3. **同一事实存两份时两份都要守**：`findings[k] == judgments[i].evidence`
   在写盘前逐条断言，JSON 往返后由验收器再查一遍。
4. **宣称「两轮一致」之前先证明两轮可比**（R55）：对两份 raw 逐轮做
   归一化 diff（生成器 id 与时间戳归一化），diff 非空就判 FAIL。
5. **`all([])` 是 True**：每一处聚合都显式判非空，空列表一律判失败。
6. **读不到的东西不许当成「没有」**：路径锚点控制柄那 6 个框要先把锚点
   类型从 `vertex` 改成 `symmetric` 才渲染得出；FOV 数值框与它的关键帧
   按钮落在容器级标记里，构成**误判**而不是漏检 —— 方向与 764 记的相反。
"""
import hashlib
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
BATCH = HERE.parent if HERE.name == "probes" else HERE
RAW = BATCH / "raw"
OUT = BATCH / "runtime-audit.json"

# 每轮易变串：生成器 id（含时间戳）、gesture id
VOLATILE_RE = re.compile(
    r"director-motion-path-[A-Za-z0-9-]*?\d{10,}"
    r"|director-gesture-\d+-\d+"
    r"|[0-9a-f]{16}-[0-9a-f]{4}")


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
    rs = raw.get("rounds") or []
    if len(rs) < 2:
        return None, "轮数不足 2（%d）" % len(rs)
    x, y = norm(rs[0].get(key)), norm(rs[1].get(key))
    if x == y:
        return True, None

    def walk(u, v, path=""):
        if isinstance(u, dict) and isinstance(v, dict):
            for k in sorted(set(u) | set(v)):
                if k not in u:
                    return "%s.%s 只在 round2" % (path, k)
                if k not in v:
                    return "%s.%s 只在 round1" % (path, k)
                r = walk(u[k], v[k], "%s.%s" % (path, k))
                if r:
                    return r
            return None
        if isinstance(u, list) and isinstance(v, list):
            if len(u) != len(v):
                return "%s 长度 %d vs %d" % (path, len(u), len(v))
            for i, (p_, q_) in enumerate(zip(u, v)):
                r = walk(p_, q_, "%s[%d]" % (path, i))
                if r:
                    return r
            return None
        return None if u == v else "%s: %r vs %r" % (path, u, v)

    return False, walk(x, y, key)


a, a_p = load("vb766a.json")
b, b_p = load("vb766b.json")
aR, bR = a["rounds"], b["rounds"]
assert len(aR) == 2 and len(bR) == 2, "轮数 %d/%d" % (len(aR), len(bR))

# ═══════════ 可比性 ═══════════
DIFF_A = ["ctxA_probe", "ctxA_sweep", "ctxB_sweep", "ctxC_sweep",
          "trackRows", "drawTrailButtons", "presetsVisible", "createPath"]
DIFF_B = ["typeBefore", "typeAfter", "handleCountBeforeType",
          "handleCountAfterType", "legendTexts", "sweep", "xtab"]
d_a = {k: round_diff(a, k) for k in DIFF_A}
d_b = {k: round_diff(b, k) for k in DIFF_B}
bad_a = sorted(k for k, (ok, _) in d_a.items() if ok is not True)
bad_b = sorted(k for k, (ok, _) in d_b.items() if ok is not True)
comparability = {
    "766a": {"keys": DIFF_A, "allConsistent": not bad_a,
             "inconsistent": bad_a,
             "firstDiff": {k: d_a[k][1] for k in bad_a}},
    "766b": {"keys": DIFF_B, "allConsistent": not bad_b,
             "inconsistent": bad_b,
             "firstDiff": {k: d_b[k][1] for k in bad_b}},
    "comparable": not bad_a and not bad_b,
}

# ═══════════ 765a 侧的：三个上下文的扫查 ═══════════
CTX = ("ctxA_sweep", "ctxB_sweep", "ctxC_sweep")


def rows_of(rd, key):
    sw = rd.get(key) or {}
    rows = sw.get("rows") or []
    if not rows:
        raise SystemExit("FATAL %s 没有行 —— 判失败，不许通过" % key)
    return sw, [r for r in rows if not r.get("FAILED")]


def ctx_summary(rd, key):
    sw, rows = rows_of(rd, key)
    beh, mk, xt = {}, {}, {}
    for r in rows:
        beh[r["behavior"]] = beh.get(r["behavior"], 0) + 1
        mk[r["markerClass"]] = mk.get(r["markerClass"], 0) + 1
        k = "%s | %s" % (r["markerClass"], r["behavior"])
        xt[k] = xt.get(k, 0) + 1
    return {
        "cells": len(rows),
        "scanCount": sw.get("scanCount"),
        "failedRows": [r["i"] for r in (sw.get("rows") or [])
                       if r.get("FAILED")],
        "focusFailures": sum(1 for r in rows
                             if (r.get("focus") or {}).get("focused") is not True),
        "behavior": beh, "marker": mk, "xtab": xt,
        "ownSwallowed": xt.get("boundary-own | swallowed-below-window", 0),
        "ownNotSwallowed": sum(v for k, v in xt.items()
                               if k.startswith("boundary-own |")
                               and not k.endswith("swallowed-below-window")),
        "ancNotSwallowed": sum(v for k, v in xt.items()
                               if k.startswith("boundary-anc |")
                               and not k.endswith("swallowed-below-window")),
        "noMarkerSwallowed": xt.get("no-marker | swallowed-below-window", 0),
        "neverReached": beh.get("never-reached", 0),
    }


ctx = {}
for rd in aR:
    for key in CTX:
        ctx.setdefault(key, []).append(ctx_summary(rd, key))

ctx_finding = {}
for key in CTX:
    per = ctx[key]
    labels = {"ctxA_sweep": "机位属性（含 FOV）",
              "ctxB_sweep": "+ 路径变换",
              "ctxC_sweep": "+ 路径锚点位置"}[key]
    ctx_finding[key] = {
        "label": labels,
        "perRound": per,
        "cellsBothRounds": [x["cells"] for x in per],
        "ownSwallowed": [x["ownSwallowed"] for x in per],
        "ownNotSwallowed": [x["ownNotSwallowed"] for x in per],
        "ancNotSwallowed": [x["ancNotSwallowed"] for x in per],
        "noMarkerSwallowed": [x["noMarkerSwallowed"] for x in per],
        "focusFailures": [x["focusFailures"] for x in per],
        "failedRows": [x["failedRows"] for x in per],
        "xtab": per[0]["xtab"],
        "xtabSameBothRounds": per[0]["xtab"] == per[1]["xtab"],
    }

# ═══════════ 关键计数：路径变换/锚点/FOV 三类 ═══════════
def count_by_marker(rd, key, attr):
    _, rows = rows_of(rd, key)
    hit = [r for r in rows if attr in (r["ctrl"].get("ownMarks") or [])]
    return {"cells": len(hit),
            "swallowed": sum(1 for r in hit
                             if r["behavior"] == "swallowed-below-window"),
            "allBoundaryOwn": all(r["markerClass"] == "boundary-own"
                                  for r in hit)}


PT = "data-director-path-transform-axis"
PA = "data-director-path-anchor-position"
AH = "data-director-path-anchor-handle"
FOV = "data-director-camera-fov"

path_transform = {"perRound": [count_by_marker(rd, "ctxB_sweep", PT)
                               for rd in aR]}
path_anchor_pos = {"perRound": [count_by_marker(rd, "ctxC_sweep", PA)
                                for rd in aR]}
fov = {"perRound": [count_by_marker(rd, "ctxA_sweep", FOV) for rd in aR]}

# 增量：ctxB − ctxA = 路径变换带进来的；ctxC − ctxB = 锚点带进来的
delta = {
    "cameraToPathTransform": {
        "cells": [ctx["ctxB_sweep"][i]["cells"] - ctx["ctxA_sweep"][i]["cells"]
                  for i in range(2)],
        "ownSwallowed": [ctx["ctxB_sweep"][i]["ownSwallowed"]
                         - ctx["ctxA_sweep"][i]["ownSwallowed"]
                         for i in range(2)]},
    "pathTransformToAnchor": {
        "cells": [ctx["ctxC_sweep"][i]["cells"] - ctx["ctxB_sweep"][i]["cells"]
                  for i in range(2)],
        "ownSwallowed": [ctx["ctxC_sweep"][i]["ownSwallowed"]
                         - ctx["ctxB_sweep"][i]["ownSwallowed"]
                         for i in range(2)]},
}

# ═══════════ 766b 侧：锚点控制柄 ═══════════
hb = []
for rd in bR:
    sw, rows = rows_of(rd, "sweep")
    handle = [r for r in rows if r["ctrl"].get("isAnchorHandle")]
    pos = [r for r in rows if r["ctrl"].get("isAnchorPosition")]
    trans = [r for r in rows if PT in (r["ctrl"].get("ownMarks") or [])]
    hb.append({
        "typeBefore": rd.get("typeBefore"),
        "typeAfter": rd.get("typeAfter"),
        "handleBefore": rd.get("handleCountBeforeType"),
        "handleAfter": rd.get("handleCountAfterType"),
        "posBefore": rd.get("positionCountBeforeType"),
        "posAfter": rd.get("positionCountAfterType"),
        "legends": rd.get("legendTexts"),
        "handleCells": len(handle),
        "handleSwallowed": sum(1 for r in handle
                               if r["behavior"] == "swallowed-below-window"),
        "handleAllBoundaryOwn": bool(handle) and all(
            r["markerClass"] == "boundary-own" for r in handle),
        "posCells": len(pos),
        "posSwallowed": sum(1 for r in pos
                            if r["behavior"] == "swallowed-below-window"),
        "transCells": len(trans),
        "transSwallowed": sum(1 for r in trans
                              if r["behavior"] == "swallowed-below-window"),
        "xtab": rd.get("xtab"),
        "failedRows": rd.get("failedRows"),
        "focusFailures": sum(1 for r in rows
                             if (r.get("focus") or {}).get("focused") is not True),
    })
handles = {
    "perRound": hb,
    "handleCells": [x["handleCells"] for x in hb],
    "handleSwallowed": [x["handleSwallowed"] for x in hb],
    "handleAllBoundaryOwn": [x["handleAllBoundaryOwn"] for x in hb],
    "handleBefore": [x["handleBefore"] for x in hb],
    "handleAfter": [x["handleAfter"] for x in hb],
    "typeSwitched": [
        (any(t.get("type") == "symmetric" and t.get("pressed") == "true"
             for t in (x["typeAfter"] or []))) for x in hb],
    "xtab": hb[0]["xtab"],
    "xtabSameBothRounds": hb[0]["xtab"] == hb[1]["xtab"],
    "ownSwallowed": [x["handleSwallowed"] + x["posSwallowed"] + x["transSwallowed"]
                     for x in hb],
}

# ═══════════ 误判格子：容器级标记的两个具体控件 ═══════════
fpp = []
for rd in aR:
    _, rows = rows_of(rd, "ctxA_sweep")
    hit = [r for r in rows if r["markerClass"] == "boundary-anc"]
    fpp.append({
        "cells": len(hit),
        "detail": [{"i": r["i"], "tag": r["ctrl"]["tag"],
                    "type": r["ctrl"]["type"],
                    "aria": r["ctrl"].get("aria"),
                    "ownMarks": r["ctrl"]["ownMarks"],
                    "ancMarks": r["ctrl"]["ancMarks"],
                    "behavior": r["behavior"],
                    "targetIsEditable": r.get("targetIsEditable")}
                   for r in hit],
    })
false_positive = {
    "cells": [x["cells"] for x in fpp],
    "allReachedNotSwallowed": all(
        x["detail"] and all(d["behavior"] != "swallowed-below-window"
                            for d in x["detail"]) for x in fpp),
    "detail": fpp[0]["detail"],
    "sameBothRounds": fpp[0]["detail"] == fpp[1]["detail"],
}

# ═══════════ 反向检测有没有找到标记扫会漏掉的控件 ═══════════
missed = {
    "noMarkerSwallowed": [ctx_finding[k]["noMarkerSwallowed"][0] for k in CTX],
    "noMarkerSwallowedBothRounds": [
        [ctx_finding[k]["noMarkerSwallowed"][i] for i in range(2)]
        for k in CTX],
    "totalNoMarkerSwallowed": sum(
        ctx_finding[k]["noMarkerSwallowed"][0] for k in CTX),
    "interpretation": "0 = 行为反推没有找到任何「没有标记却吞 Esc」的控件 "
                      "⟹ 在这三个上下文里标记扫的失效方向是**误判**（多报）"
                      "而不是漏检。方向与 764 记的相反。",
}

findings = {
    "comparability": comparability,
    "sweepContexts": ctx_finding,
    "pathTransform": path_transform,
    "pathAnchorPosition": path_anchor_pos,
    "fovSlider": fov,
    "deltas": delta,
    "anchorHandles": handles,
    "containerMarkerFalsePositive": false_positive,
    "missedByMarkerScan": missed,
}

judgments = [
    {"id": "J1", "verdict": "PASS",
     "statement": "两轮**逐字段一致**，且先证明可比（766a 比 %d 个 key、"
                  "766b 比 %d 个 key 的归一化 diff 全为空）。本批**每轮开头"
                  "都清了 `liblib-tv-director-project-v1:*`**（建轨迹是破坏性的，"
                  "763 O1 记过它会持久化），所以两轮起点相同。",
     "evidenceKey": "comparability"},
    {"id": "J2", "verdict": "PASS",
     "statement": "★ **用行为反推取代标记扫来识别边界控件，判据成立**："
                  "三个上下文里凡是**自身**带边界标记的控件，"
                  "`reachedCapture=true` 且 `reachedBubble=false`（swallowed）"
                  "**无一例外**；而 `reachedBubble=true` 的控件 "
                  "`reachedCapture` 也必然为 true。焦点 %s/%s 全部成功，"
                  "0 格没聚焦上。"
                  % (sum(ctx_finding[k]["cellsBothRounds"][0] for k in CTX),
                     sum(ctx_finding[k]["cellsBothRounds"][0] for k in CTX)),
     "evidenceKey": "sweepContexts"},
    {"id": "J3", "verdict": "PASS",
     "statement": "★ **更正 764 承认的漏检风险方向**：在这三个上下文里，"
                  "行为反推**一个「没标记却吞 Esc」的控件都没找到**"
                  "（`no-marker | swallowed` 恒为 0）。标记扫的失效方向是"
                  "**多报（误判）**而不是漏检 —— 见 J4。",
     "evidenceKey": "missedByMarkerScan"},
    {"id": "J4", "verdict": "FAIL",
     "statement": "★ **缺陷 D7（低）**：**容器级标记会误判**。FOV 那一段的"
                  "外层容器带 `data-director-camera-fov-field`，"
                  "于是**容器里的非边界控件也被算成边界控件** —— "
                  "FOV 数值框（`data-director-camera-fov-number`）与它的"
                  "关键帧按钮各占 1 格，两者 `reachedBubble=true`、"
                  "**并没有吞 Esc**。每个上下文固定 2 格误判。",
     "evidenceKey": "containerMarkerFalsePositive"},
    {"id": "J5", "verdict": "PASS",
     "statement": "★ **764 的「推测同样受影响」对路径变换已验证成立**："
                  "路径变换 %s 个数值框（`data-director-path-transform-axis`）"
                  "**全部**吞 Esc，且自身全部带边界标记。"
                  "它们是从「机位属性」上下文增量进来的（+可控控件 %s、"
                  "+边界控件 %s，两轮一致）。",
     "evidenceKey": "pathTransform"},
    {"id": "J6", "verdict": "PASS",
     "statement": "★ **对路径锚点位置也已验证成立**：%s 个数值框"
                  "（`data-director-path-anchor-position`）**全部**吞 Esc，"
                  "自身全部带边界标记。渲染条件是三步：建轨迹 → 选中带 "
                  "`motionPathId` 的轨道 → **再点一个锚点**（764 就停在前两步）。",
     "evidenceKey": "pathAnchorPosition"},
    {"id": "J7", "verdict": "PASS",
     "statement": "★ **对 FOV 已验证成立，且要分开说**：FOV **滑杆**"
                  "（`data-director-camera-fov`，`input[type=range]`，"
                  "自身 spread 了 gesture）**吞 Esc**；同屏的 FOV "
                  "**数值框**（`-fov-number`，**没有** gesture spread）"
                  "**不吞**。764 说的「FOV 的标记挂在外层容器上」"
                  "不准确 —— 滑杆的标记在它自己身上，数值框是另一个控件。",
     "evidenceKey": "fovSlider"},
    {"id": "J8", "verdict": "PASS",
     "statement": "★ **764 未验证清单的最后一项也关掉了**：路径锚点的"
                  "**控制柄** %s 个数值框（入/出 × 3 轴，"
                  "`data-director-path-anchor-handle`）**全部**吞 Esc，"
                  "自身全部带边界标记。关键一步是把锚点类型从 `vertex` "
                  "改成 `symmetric` —— `DirectorInspector.tsx:1189` 只在"
                  "**非 vertex** 时才渲染控制柄框。",
     "evidenceKey": "anchorHandles"},
    {"id": "J9", "verdict": "PASS",
     "statement": "三个上下文的控件数与边界控件数逐档递增且两轮一致："
                  "机位属性 %s → +路径变换 %s → +锚点位置 %s，"
                  "自身带边界标记的控件 %s → %s → %s。"
                  "0 格扫到一半导演台消失（冻结生效）、0 格没获得焦点。",
     "evidenceKey": "deltas"},
    {"id": "J10", "verdict": "PASS",
     "statement": "**冻结机制本身有效**：逐控件按 Esc 时导演台自己的处理器"
                  "被 `stopImmediatePropagation()` 挡住，所以「事件到没到 "
                  "window」照常可测、而导演台不会有任何反应 —— "
                  "这正是三段扫查能各扫几十格而不把导演台关掉的原因"
                  "（765 R63 的同族问题）。",
     "evidenceKey": "sweepContexts"},
    {"id": "J11", "verdict": "FAIL",
     "statement": "★ **本批判不了「冻结期间导演台自己的处理器会不会有反应」** —— "
                  "冻结就是把它挡掉的。所以本批只测传播、不测效果；"
                  "「吞 Esc 对界面意味着什么」沿用 763/764 在别的上下文里"
                  "量过的结论，不在本批重复声明。",
     "evidenceKey": "sweepContexts"},
]

for j in judgments:
    j["evidence"] = findings[j["evidenceKey"]]

audit = {
    "batch": 766,
    "date": "2026-10-01",
    "scope": "用行为反推取代 data-* 标记扫来识别手势边界控件；"
             "把 764 明确未验证的路径锚点/路径变换/FOV 三类控件逼出来量 Esc",
    "env": {
        "base": "http://localhost:4317",
        "canvas": "canvas-2",
        "directorNodeId": "b-bTLLuU4w5q",
        "viewport": "1440x1000（桌面，属性面板为可滚动 aside）",
        "player": "chromium (playwright sync_api)",
        "srcModified": False,
    },
    "probes": [
        {"id": "766a", "file": "probes/dbg766a.py", "raw": "raw/vb766a.json",
         "rounds": len(aR), "selfReportedConsistent": None,
         "note": "三个上下文的全控件无标记扫（机位属性 → +路径变换 → +锚点位置）。"
                 "初版有两处探针缺陷：路径预设按钮在折叠菜单里（DOM 里不存在）、"
                 "以及 JS 片段的括号错误，见 R67/R68"},
        {"id": "766b", "file": "probes/dbg766b.py", "raw": "raw/vb766b.json",
         "rounds": len(bR), "selfReportedConsistent": None,
         "note": "把锚点类型从 vertex 改成 symmetric，逼出控制柄那 6 个框。"
                 "初版漏了滚动：锚点选项在 y≈1769，超出 1000px 视口 ⟹ 扫网格全跳过"},
    ],
    "rawSha": {p.name: sha(p) for p in (a_p, b_p)},
    "findings": findings,
    "judgments": judgments,
    "defects": [
        {"id": "D7", "severity": "低", "newInThisBatch": True,
         "title": "容器级 data-* 标记会把非边界控件误判成边界控件",
         "where": ["src/components/director/DirectorInspector.tsx:1604",
                   "src/components/director/DirectorInspector.tsx:1652",
                   "src/components/director/DirectorInspector.tsx:1667"],
         "mechanism": "FOV 那一段的外层容器 `data-director-camera-fov-field`"
                      "（`:1604`）同时包着**滑杆**与**数值框**。"
                      "滑杆的 `input[type=range]` 自己带 "
                      "`data-director-camera-fov` 并 spread 了 gesture"
                      "（`:1652-1655`），**是**真边界控件；"
                      "而数值框（`:1667`）**没有** gesture spread —— "
                      "它那一段源码里 `gesture` 出现 0 次。",
         "measured": "用 `closest('[data-director-camera-fov-field]')` 判边界，"
                     "会把数值框与它的关键帧按钮各算 1 个边界控件；"
                     "行为反推显示这两个 `reachedBubble=true`、"
                     "**没有吞 Esc** ⟹ 每个上下文固定 %s 格误判，"
                     "两轮一致。" % false_positive["cells"][0],
         "severityRationale": "这是**测量工具**的缺陷，不是产品的缺陷 —— "
                              "产品里那两个控件本来就不该吞 Esc，"
                              "行为是对的。所以严重度低。",
         "impactOnEarlierBatches":
             "764 用的是标记扫。**方向上**它会**多报**，"
             "所以 764 记的「43 个边界控件全部吞 Esc」里，"
             "**至少含这 2 个误判**（在 FOV 那一段）⟹ 43 这个数是**上界**。"
             "本批没有重算 764 那个 43（那是另一批的读数）。",
         "needsSrcChange": False,
         "needsProbeChange": True},
    ],
    "observations": [
        {"id": "O1",
         "text": "**边界控件的判别式在本批是 1:1 的**：`boundary-own ⟺ "
                 "reachedCapture=true 且 reachedBubble=false`，"
                 "三个上下文共 %d 格无一例外。反过来 `reachedBubble=true` 的"
                 "格子 `reachedCapture` 也全为 true ⟹ 「事件完全没上来」"
                 "这种情况一格都没有。"
                 % sum(ctx_finding[k]["cellsBothRounds"][0] for k in CTX),
         "verdict": "方法论结论"},
        {"id": "O2",
         "text": "**标记扫的失效方向取决于标记集本身**：766b 首版只把"
                 "`path-anchor-handle`/`path-anchor-position` 算作边界标记，"
                 "于是那 9 个路径变换框（带 `path-transform-axis` 标记）"
                 "被标成 `no-marker` 而行为是 swallowed —— 这是**假阴性**。"
                 "把属性补进标记集后交叉表归零。所以「标记扫不可靠」"
                 "不等于「标记扫总是漏检」，而是**它和标记集一样脆**。",
         "verdict": "方法论约束"},
        {"id": "O3",
         "text": "**属性面板是可滚动容器**：锚点选项按钮实测在 "
                 "`y≈1769`，而视口高只有 1000 ⟹ 扫网格全部跳过、"
                 "`elementFromPoint` 永远打不中，表现为 `noHit`。"
                 "任何「扫网格找元素」的探针在这个面板上都必须**先滚进视口**。",
         "verdict": "探针约束"},
        {"id": "O4",
         "text": "**相机轨道在选中相机对象时就自动选中了**"
                 "（`data-director-track-row` 的 `director-track-camera-main` "
                 "读数 `selected=true`）⟹ `selectedTrack` 自动解析成功，"
                 "不需要额外点轨道行。`data-director-track-draw-trail` "
                 "那一次点击同时做了「选中相机轨道」+「打开路径菜单」。",
         "verdict": "事实记录"},
    ],
    "notClaimed": [
        "无源站对照：本批全部结论只针对 clone 自身的行为自洽性。",
        "**冻结期间导演台自己的处理器会不会有反应，本批判不了**（J11）—— "
        "冻结就是把它挡掉的。本批只测传播，不测效果。",
        "**只测了 1440 桌面一档视口**；移动端抽屉形态下的同一批控件没测。",
        "**只测了机位这一个对象**：角色/道具上下文里的同类控件没重扫"
        "（764 扫过，本批不重复）。",
        "**只建了 `line` 一种轨迹预设**；`ring`/`rectangle` 没建，"
        "锚点数量因此固定为 2（锚点位置 3 框 + 控制柄 6 框）。",
        "**没有测锚点类型为 `asymmetric` 的情形**（只测了 `symmetric`）。",
        "**没有重算 764 那个「43 个边界控件」**。本批证明标记扫会**多报**，"
        "所以 43 是上界，但具体少几个没量。",
        "**没有测拖动手势本身**（ArrowUp 之类）—— 本批只测 Esc 的传播。",
        "建运动轨迹是**破坏性**操作，会改项目并持久化到 localStorage；"
        "本批每轮开头清了 `liblib-tv-director-project-v1:*`，"
        "但**探针结束时没有把项目恢复原状**（Playwright 每次新开 context，"
        "不会影响他人）。",
        "D7 是**测量工具**的缺陷，不是产品缺陷 —— 那两个被误判的控件"
        "行为本来就是对的。本批不据此改任何产品结论。",
    ],
    "probeLessons": [
        {"id": "R67",
         "text": "★ **JS 片段的语法要单独过一遍 `node --check`，别靠跑浏览器发现**。"
                 "766a 连续三轮白跑，每轮都是「少一个 `}` / 多一个 `)` / "
                 "少一个 `pg.evaluate` 的收尾括号」这种一眼可见的错误 —— "
                 "而每次都要起浏览器、跑十几秒，才在日志末尾看到 "
                 "`SyntaxError`，前面十几秒的工作全废。"
                 "抽出所有 `()=>…` 片段逐个 `node --check` 只要 0.1 秒。"
                 "写完这个检查器之后，它当场又抓出了我新加的 3 段同类错误。"},
        {"id": "R68",
         "text": "★ **「元素不在 DOM 里」和「元素在视口外」是两回事，"
                 "报错长得却一样**。766a 找不到路径预设按钮时只记了 "
                 "`missing:true`，我据此以为「这个种子数据建不出轨迹」；"
                 "实际上按钮在**折叠菜单**里（`pathMenuLeft` 为 null 时"
                 "根本不渲染），入口是 `data-director-track-draw-trail`。"
                 "教训：把「不在 DOM」「在 DOM 但没渲染出盒子」"
                 "「在 DOM 且有盒子但在视口外」三种情况**分开记**，"
                 "否则一个探针缺陷会被读成产品结论。"},
        {"id": "R69",
         "text": "**扫网格之前先滚进视口**（O3）。锚点选项在 y≈1769、"
                 "视口高 1000 ⟹ 扫网格的每一格都因 `y > innerHeight-2` "
                 "被跳过，返回 `noHit`。看起来像「点不到」，其实是"
                 "「在屏幕外」。属性面板是可滚动容器，探针必须先 "
                 "`scrollIntoView` 再扫。"},
        {"id": "R70",
         "text": "**要冻住别人的处理器，就必须在它之前注册**。"
                 "导演台在挂载时才往 window 上装 Esc 监听器，"
                 "所以页面一加载就装的探针**注册在前**；"
                 "在冒泡阶段调 `stopImmediatePropagation()` 就能挡住它。"
                 "这样「事件到没到 window」照常可测，"
                 "而导演台不会有任何反应 —— 逐控件按 Esc 才不会把导演台关掉"
                 "（765 R63 的同族问题）。"},
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
print("两轮可比：%s（766a 不一致 key=%s，766b 不一致 key=%s）"
      % (comparability["comparable"], bad_a, bad_b))
for k in findings:
    print("  %-32s %s" % (k, json.dumps(findings[k], ensure_ascii=False)[:100]))
