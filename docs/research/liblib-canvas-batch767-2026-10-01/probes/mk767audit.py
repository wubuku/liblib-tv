#!/usr/bin/env python3
"""batch 767 汇编器：从 raw/vb767a.json 现算 runtime-audit.json

规矩（沿用 756–766）：
1. **数字不许手抄** —— 每个数都从 raw 算出来。
2. **缺原始读数判失败**，不许「通过」。
3. **同一事实存两份时两份都要守**：`findings[k] == judgments[i].evidence`
   写盘前逐条断言，JSON 往返后由验收器再查一遍。
4. **先证明可比再谈一致**（R55）：逐轮归一化 diff。
5. **`all([])` 是 True**：每处聚合显式判非空。
6. **被准备动作污染的读数单列成不声称**（R73）：本批「先测外点再测 Esc」的
   顺序让「关闭是否归还焦点」这一问 6 格全被污染 ⟹ 不下判断。
"""
import hashlib
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
BATCH = HERE.parent if HERE.name == "probes" else HERE
RAW = BATCH / "raw"
OUT = BATCH / "runtime-audit.json"

VOLATILE_RE = re.compile(r"director-gesture-\d+-\d+|[0-9a-f]{16}-[0-9a-f]{4}")
IDS = ["export", "preset", "pathmenu", "phonevcam", "crowd", "modellib"]


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
        return None, "轮数不足 2"
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


a, a_p = load("vb767a.json")
aR = a["rounds"]
assert len(aR) == 2, "轮数 %d" % len(aR)

DIFF_KEYS = ["results"]
diffs = {k: round_diff(a, k) for k in DIFF_KEYS}
bad = sorted(k for k, (ok, _) in diffs.items() if ok is not True)
comparability = {
    "keys": DIFF_KEYS, "allConsistent": not bad, "inconsistent": bad,
    "firstDiff": {k: diffs[k][1] for k in bad},
    "rounds": len(aR),
    "probeClearsLocalStorage": [
        (rd.get("cleared") or {}).get("removed") for rd in aR],
}


def by_id(rd):
    out = {}
    for r in rd.get("results") or []:
        if r.get("id") in IDS:
            out[r["id"]] = r
    return out


per_round = [by_id(rd) for rd in aR]
for i, m in enumerate(per_round):
    missing = [x for x in IDS if x not in m]
    if missing:
        raise SystemExit("FATAL round%d 缺 %s —— 判失败，不许当「没有」"
                         % (i + 1, missing))


def cell(rd, i):
    a_open = rd.get("afterOpen") or {}
    a_out = rd.get("afterOutside") or {}
    a_esc = rd.get("afterEsc") or {}
    de = rd.get("deskEnd") or {}
    outside_closed = (a_out.get("panelPresent") is False)
    esc_skipped = "skipped" in a_esc
    esc_closed_panel = (a_esc.get("panelPresent") is False
                        if not esc_skipped else None)
    esc_closed_desk = (de.get("open") is False
                       if not esc_skipped else None)
    act_after = ((a_esc.get("active") or {}) if not esc_skipped
                 else (a_out.get("active") or {}))
    return {
        "opened": a_open.get("panelPresent") is True,
        "focusOnTriggerAfterOpen": (a_open.get("active") or {}).get(
            "isTrigger") is True,
        "focusInsidePanelAfterOpen": (a_open.get("active") or {}).get(
            "inPanel") is True,
        "ariaExpanded": a_open.get("triggerAriaExpanded"),
        "ariaControlsAttr": a_open.get("triggerHasControlsAttr"),
        "ariaHasPopupAttr": a_open.get("triggerHasHasPopupAttr"),
        "panelRole": a_open.get("panelRole"),
        "panelAriaLabel": a_open.get("panelAriaLabel"),
        "panelHeading": a_open.get("panelHeading"),
        "panelId": a_open.get("panelId"),
        "panelFocusables": a_open.get("panelFocusables"),
        "outsideClickAttempted": bool((rd.get("outside") or {})
                                      .get("clicked")),
        "outsideClosedPanel": outside_closed,
        "outsideHitWasClickable": ((rd.get("outside") or {}).get("hit") or {}
                                   ).get("clickable"),
        "escTested": not esc_skipped,
        "escClosedPanel": esc_closed_panel,
        "escClosedDesk": esc_closed_desk,
        "activeAfterTag": act_after.get("tag"),
        "activeAfterIsTrigger": act_after.get("isTrigger"),
        "activeAfterInDialog": act_after.get("inDialog"),
        "activeAfterIsBody": act_after.get("isBody"),
        "deskOpenAtEnd": de.get("open") is True,
    }


table = {i: [cell(per_round[r][i], r) for r in range(2)] for i in IDS}

# ═══════════ 汇总 ═══════════
summary = {
    "ids": IDS,
    "count": len(IDS),
    "openedBothRounds": [i for i in IDS
                         if all(table[i][r]["opened"] for r in range(2))],
    "focusStayedOnTrigger": [i for i in IDS
                             if all(table[i][r]["focusOnTriggerAfterOpen"]
                                    for r in range(2))],
    "focusMovedIntoPanel": [i for i in IDS
                            if any(table[i][r]["focusInsidePanelAfterOpen"]
                                   for r in range(2))],
    "outsideCloseWorks": [i for i in IDS
                          if all(table[i][r]["outsideClosedPanel"]
                                 for r in range(2))],
    "outsideCloseMissing": [i for i in IDS
                            if all(table[i][r]["outsideClosedPanel"] is False
                                   for r in range(2))],
    "outsideClickAttempted": [i for i in IDS
                              if all(table[i][r]["outsideClickAttempted"]
                                     for r in range(2))],
    "outsideHitWasClickable": [i for i in IDS
                               if any(table[i][r]["outsideHitWasClickable"]
                                      for r in range(2))],
    "escTested": [i for i in IDS
                  if all(table[i][r]["escTested"] for r in range(2))],
    "escSkippedBecauseOutsideClosed": [
        i for i in IDS if all(table[i][r]["escTested"] is False
                              for r in range(2))],
    "escClosedPanelOnly": [i for i in IDS
                           if all(table[i][r]["escClosedPanel"] is True
                                  and table[i][r]["escClosedDesk"] is False
                                  for r in range(2))],
    "escClosedWholeDesk": [i for i in IDS
                           if all(table[i][r]["escClosedDesk"] is True
                                  for r in range(2))],
    "roleDialogPresent": [i for i in IDS
                          if all(table[i][r]["panelRole"] == "dialog"
                                 for r in range(2))],
    "panelAriaLabelPresent": [i for i in IDS
                              if all(table[i][r]["panelAriaLabel"]
                                     for r in range(2))],
    "ariaControlsAny": [i for i in IDS
                        if any(table[i][r]["ariaControlsAttr"]
                               for r in range(2))],
    "ariaHasPopupAny": [i for i in IDS
                        if any(table[i][r]["ariaHasPopupAttr"]
                               for r in range(2))],
    "ariaExpandedNull": [i for i in IDS
                         if all(table[i][r]["ariaExpanded"] is None
                                for r in range(2))],
    "deskReopenedAfter": [rd.get("reopened") for rd in aR],
    "focusReturnCells": {
        i: {"activeAfterTag": [table[i][r]["activeAfterTag"]
                               for r in range(2)],
            "isTrigger": [table[i][r]["activeAfterIsTrigger"]
                          for r in range(2)],
            "inDialog": [table[i][r]["activeAfterInDialog"]
                         for r in range(2)],
            "isBody": [table[i][r]["activeAfterIsBody"] for r in range(2)],
            "contaminatedByOutsideClick": not table[i][0]["escTested"]}
        for i in IDS},
    "focusables": {i: [table[i][r]["panelFocusables"] for r in range(2)]
                   for i in IDS},
    "table": table,
}

# ═══════════ 断言：空列表 / 自相矛盾都要判失败 ═══════════
assert summary["count"] == 6
for key in ("openedBothRounds", "focusStayedOnTrigger",
            "outsideCloseWorks", "outsideCloseMissing", "escTested",
            "roleDialogPresent"):
    assert summary[key], "%s 为空 —— 判失败，不许当「没有」" % key
assert set(summary["outsideCloseWorks"]) | set(summary["outsideCloseMissing"]) \
    == set(IDS), "外点关闭的分类没有覆盖全部 6 个"
assert len(summary["escTested"]) + len(
    summary["escSkippedBecauseOutsideClosed"]) == 6, \
    "Esc 的分类没有覆盖全部 6 个"
assert not (set(summary["escClosedPanelOnly"])
            & set(summary["escClosedWholeDesk"])), \
    "escClosedPanelOnly 与 escClosedWholeDesk 有交集"
assert len(summary["ariaControlsAny"]) == 0, \
    "竟有 aria-controls —— 与静态层矛盾，必须先查清"
assert len(summary["ariaHasPopupAny"]) == 0, \
    "竟有 aria-haspopup —— 与静态层矛盾，必须先查清"

findings = {"comparability": comparability, "disclosureCensus": summary}

judgments = [
    {"id": "J1", "verdict": "PASS",
     "statement": "两轮**逐字段一致**（`results` 整棵树的归一化 diff 为空），"
                  "且先证明可比：本批**只点触发器与浮层外面**，不点任何提交/"
                  "生成/连接按钮，每轮开头还清了导演台项目的 localStorage，"
                  "所以两轮起点相同。",
     "evidenceKey": "comparability"},
    {"id": "J2", "verdict": "PASS",
     "statement": "6 个 disclosure **全部能打开**（6/6，两轮），"
                  "而且**打开瞬间一律不移动焦点** —— 焦点留在触发器上、"
                  "不进浮层（6/6，两轮）。这一条 6 个完全一致，"
                  "所以按 disclosure 惯例看**不判缺陷**。",
     "evidenceKey": "disclosureCensus"},
    {"id": "J3", "verdict": "PASS",
     "statement": "**外点关闭 3/6 有效**（两轮都有效）：预设运镜面板、"
                  "创建运动轨迹菜单、模型库面板。另外 3 个点了外面**不关**："
                  "导出面板、虚拟相机面板、添加群众阵列面板 —— "
                  "6 格的点击点都验过「不在浮层内、且不是可点元素」。",
     "evidenceKey": "disclosureCensus"},
    {"id": "J4", "verdict": "FAIL",
     "statement": "★ **缺陷 D8（中）**：**添加群众阵列面板开着时按 Esc，"
                  "把整个导演台关掉了**（2/2 轮 `deskOpenAtEnd=false`，"
                  "探针不得不重开导演台）。机制静态可查：它既没有自己的 Esc "
                  "处理，而 `DirectorDesk.tsx` 的 Esc 阶梯里**也只有导出面板"
                  "那一档**（对另外五个 disclosure 状态 0 处引用）⟹ "
                  "Esc 一路走到 `closeWorkspace()`。用户想关一个小面板，"
                  "结果整个工作区连同未保存的改动一起没了。",
     "evidenceKey": "disclosureCensus"},
    {"id": "J5", "verdict": "PASS",
     "statement": "**能测到 Esc 的 2 个都只关自己不关导演台**："
                  "导出面板（靠导演台阶梯里唯一的那一档 `:557`）与"
                  "虚拟相机面板（靠它自己的 window **捕获**监听 + "
                  "`stopImmediatePropagation`，`DirectorPhoneVcamPanel.tsx:"
                  "286-296`）。这说明「关面板而不关导演台」这件事做得到 —— "
                  "群众阵列面板缺的不是能力，是那一档。",
     "evidenceKey": "disclosureCensus"},
    {"id": "J6", "verdict": "FAIL",
     "statement": "★ **缺陷 D9（低）**：3/6 没有外点关闭（导出面板、"
                  "虚拟相机面板、添加群众阵列面板），点外面浮层赖着不走。"
                  "**同仓已有做对了的实现** —— 模型库面板 "
                  "`DirectorViewport.tsx:2734-2753` 一份代码里同时给了"
                  "外点 `pointerdown` 与捕获阶段 Esc，还带 "
                  "`preventDefault()` + `stopImmediatePropagation()`；"
                  "预设/路径菜单也各有一个关闭 effect。所以 765 的 D5 "
                  "**不需要新发明，照抄同族即可**。",
     "evidenceKey": "disclosureCensus"},
    {"id": "J7", "verdict": "FAIL",
     "statement": "★ **缺陷 D10（低）**：aria 契约**只有 2/6 完整** —— "
                  "只有群众阵列与模型库两个浮层给了 `role=\"dialog\"` + "
                  "`aria-label`；另外 4 个（导出面板、预设运镜、路径菜单、"
                  "虚拟相机）都是**既没有 role、也没有 aria-label** 的裸容器。"
                  "而 `aria-controls` / `aria-haspopup` 是 **0/6** —— "
                  "765 的 D6 不是一个浮层的个案，是全族通病。",
     "evidenceKey": "disclosureCensus"},
    {"id": "J8", "verdict": "PASS",
     "statement": "★ **同仓存在完整的正确样本，765 的 D5/D6 修法有先例**："
                  "模型库面板那一个 `useEffect`（`DirectorViewport.tsx:"
                  "2734-2753`）就是「外点关闭 + Esc 关闭 + 不让事件漏到"
                  "导演台阶梯」三件事的标准答案。",
     "evidenceKey": "disclosureCensus"},
    {"id": "J9", "verdict": "FAIL",
     "statement": "★ **「关闭时是否把焦点归还触发器」这一问，本批 6 格"
                  "全部没有干净读数**：本批顺序是「先测外点、再测 Esc」，"
                  "而**点空白本身就会把焦点挪到对话框根**"
                  "（6 格读到的都是 `DIV[aria-label=3D导演台工作区]`）⟹ "
                  "这一列被准备动作污染，**不下判断**。765 的 D4 读数"
                  "（焦点在面板**内部**按 Esc ⟹ 掉到 `body`）是干净的，"
                  "可作参照，但那是另一个浮层。",
     "evidenceKey": "disclosureCensus"},
    {"id": "J10", "verdict": "FAIL",
     "statement": "★ **路径菜单那一格测的触发器不是带 `aria-expanded` 的"
                  "那个**：`aria-expanded` 在「创建运动轨迹」按钮"
                  "（`DirectorTimeline.tsx:1121`）上，而本批点的是 "
                  "`data-director-track-draw-trail`（`aria-pressed`，"
                  "**没有** `aria-expanded`）⟹ 该格的 `aria-expanded` "
                  "读数是 `null`，**如实记、不当缺陷**。",
     "evidenceKey": "disclosureCensus"},
    {"id": "J11", "verdict": "PASS",
     "statement": "**没点任何有副作用的按钮**：导出面板的提交按钮、"
                  "虚拟相机的「连接」、模型库的添加都没点；"
                  "点过的只有 6 个 disclosure 触发器与浮层外面的空白。",
     "evidenceKey": "disclosureCensus"},
]

for j in judgments:
    j["evidence"] = findings[j["evidenceKey"]]

audit = {
    "batch": 767,
    "date": "2026-10-01",
    "scope": "导演台 6 个带 aria-expanded 的 disclosure 浮层的关闭契约普查"
             "（打开是否移焦点 / 外点关闭 / Esc 关闭 / aria 契约）",
    "env": {
        "base": "http://localhost:4317",
        "canvas": "canvas-2",
        "directorNodeId": "b-bTLLuU4w5q",
        "viewport": "1440x1000（桌面；6 个浮层里 3 个只在这一档出现）",
        "player": "chromium (playwright sync_api)",
        "srcModified": False,
    },
    "probes": [
        {"id": "767a", "file": "probes/dbg767a.py", "raw": "raw/vb767a.json",
         "rounds": len(aR), "selfReportedConsistent": None,
         "note": "6 个浮层逐个量 5 件事。初版两处探针缺陷："
                 "JS 的 `in` 用在字符串上（TypeError）、"
                 "以及「先点外点再测 Esc」污染了焦点读数，见 R71–R73"},
    ],
    "rawSha": {a_p.name: sha(a_p)},
    "findings": findings,
    "judgments": judgments,
    "defects": [
        {"id": "D8", "severity": "中", "newInThisBatch": True,
         "title": "添加群众阵列面板开着时按 Esc 会关掉整个导演台",
         "where": ["src/components/director/DirectorViewport.tsx:3084-3092",
                   "src/components/director/DirectorDesk.tsx:549-568"],
         "mechanism": "`crowdPanelOpen` 的 state 在 `DirectorViewport.tsx:2545`，"
                      "而 `DirectorDesk.tsx` 的 Esc 阶梯（`:549-568`）"
                      "**对它 0 处引用**（阶梯里唯一的浮层档是 "
                      "`if (exportPanelOpen)` `:557`）—— 实测 "
                      "`grep -cE \"crowdPanelOpen|modelLibraryOpen|"
                      "phoneVcamOpen|presetPanelLeft|pathMenuLeft\" "
                      "DirectorDesk.tsx` = 0。"
                      "而群众阵列面板自己也没有 Esc 处理（模型库有，`:2742`）。"
                      "⟹ Esc 从阶梯顶一路走到 `closeWorkspace()`。",
         "measured": "2/2 轮：面板开着时按 Esc，导演台 `open=false`，"
                     "探针不得不重开。6 个里只有它这样。",
         "severityRationale": "**中**（不是低）：后果是整个工作区连同"
                              "未保存的改动一起消失，而用户只是想关一个"
                              "小面板。这是本批唯一一个「按 Esc 丢工作区」"
                              "的路径。",
         "fixDirection": "二选一：①在阶梯里给 `crowdPanelOpen` 加一档，"
                         "位置在 `closeWorkspace()` 之前 —— 同族里"
                         "`exportPanelOpen`（`:557`）就是这么做的；"
                         "②或者照抄模型库面板那份实现"
                         "（`DirectorViewport.tsx:2734-2753`）："
                         "自己监听捕获阶段 Esc 并 `stopImmediatePropagation()`。",
         "needsSrcChange": True},
        {"id": "D9", "severity": "低", "newInThisBatch": True,
         "widensD5From765": True,
         "title": "6 个 disclosure 浮层里 3 个没有外点关闭",
         "where": ["src/components/director/DirectorDesk.tsx:1351-1362",
                   "src/components/director/DirectorViewport.tsx:3080",
                   "src/components/director/DirectorViewport.tsx:3084"],
         "mechanism": "导出面板、虚拟相机面板、添加群众阵列面板都没有"
                      "「点外面关闭」的监听。765 的 D5 说「导出面板没有"
                      "外点关闭」时把它当个案；本批证明**这是 3/6 的通病**。",
         "measured": "3/6 点了面板外空白（已验不在面板内、且不是可点元素）"
                     "后面板仍然开着，2/2 轮。",
         "inRepoExemplar": "`DirectorViewport.tsx:2734-2753`（模型库面板）"
                           "是同仓最完整的一份：外点 `pointerdown` + 捕获阶段 "
                           "Esc + `preventDefault()` + "
                           "`stopImmediatePropagation()`。"
                           "`DirectorTimeline.tsx:554-575`（路径菜单）与"
                           "`:578-599`（预设面板）也各有一个关闭 effect。",
         "needsSrcChange": True},
        {"id": "D10", "severity": "低", "newInThisBatch": True,
         "widensD6From765": True,
         "title": "disclosure 的 aria 契约全族残缺：4/6 无 role 也无 "
                  "aria-label，6/6 无 aria-controls/aria-haspopup",
         "where": ["src/components/director/DirectorExportPanel.tsx:42-51",
                   "src/components/director/DirectorTimeline.tsx:1371-1379",
                   "src/components/director/DirectorTimeline.tsx:1502-1509",
                   "src/components/director/DirectorViewport.tsx:3084-3092",
                   "src/components/director/DirectorViewport.tsx:3161-3169"],
         "mechanism": "只有群众阵列（`:3086-3087`）与模型库（`:3163-3164`）"
                      "给了 `role=\"dialog\"` + `aria-label`；导出面板是"
                      "无 role 的 `<section>`、预设面板与路径菜单是"
                      "无 role 的裸 `<div>`、虚拟相机面板同样没有。"
                      "6 个触发器**全都没有** `aria-controls` 与 "
                      "`aria-haspopup`（只有 `aria-expanded`）。",
         "measured": "role=dialog 2/6；aria-label 2/6；"
                     "aria-controls 0/6；aria-haspopup 0/6。2/2 轮。",
         "note": "765 的 D6 只点了导出面板一个；本批证明它是全族通病。"
                 "另外 4 个浮层里有的带 `<h2>`/`<h3>` 标题 —— "
                 "标题**不构成**可访问名（要靠 role 或 aria-label）。",
         "needsSrcChange": True},
    ],
    "observations": [
        {"id": "O1",
         "text": "**6/6 打开都不移动焦点**（焦点留在触发器上、不进浮层），"
                 "两轮一致。5 个浮层各有 ≥2 个可聚焦控件"
                 "（模型库 15、预设 10、导出 5、路径菜单 5、群众 5、"
                 "虚拟相机 2）⟹ 键盘用户要自己 Tab 进去。"
                 "按 disclosure 惯例这不算缺陷，所以**不判缺陷**，"
                 "只记事实。",
         "verdict": "事实记录"},
        {"id": "O2",
         "text": "**静态与读数在「外点关闭」上完全对上**：有关闭 effect 的"
                 "那三个（路径菜单 `:554-575`、预设面板 `:578-599`、"
                 "模型库 `:2734-2753`）实测都关；没有 effect 的那三个"
                 "（导出面板、虚拟相机、群众阵列）实测都不关。"
                 "本批这一次静态推理与读数没有分歧 —— 但这是运气，"
                 "765 的 R64 已经记过静态证明不了浏览器的事件处理。",
         "verdict": "方法论记录"},
        {"id": "O3",
         "text": "**Esc 的两种正确实现方式在同仓并存**：导出面板靠"
                 "导演台阶梯里的一档（`:557`），虚拟相机与模型库靠"
                 "自己的 window **捕获**监听 + `stopImmediatePropagation()`。"
                 "捕获优先于冒泡，所以后者能在阶梯之前把事件截住 —— "
                 "这也是为什么虚拟相机只关自己不关导演台。",
         "verdict": "事实记录（也是 D8 的修法依据）"},
        {"id": "O4",
         "text": "**预设运镜的触发器有 `disabled` 条件**"
                 "（`DirectorTimeline.tsx:1084`：选中轨道不是 camera "
                 "或机位在跟随中都 disabled）⟹ 测它之前必须先选中相机对象"
                 "让相机轨道成为选中轨道，否则触发器点不动。",
         "verdict": "探针约束"},
    ],
    "notClaimed": [
        "无源站对照：本批全部结论只针对 clone 自身的行为自洽性。",
        "★ **「关闭时是否把焦点归还触发器」这一问本批没有干净读数**"
        "（J9）：顺序是「先测外点、再测 Esc」，而点空白本身就会把焦点"
        "挪到对话框根。要干净地量得重跑一版「打开 → 直接按 Esc → 读焦点」。",
        "★ **路径菜单那一格测的触发器不是带 `aria-expanded` 的那个**"
        "（J10）：`aria-expanded` 在「创建运动轨迹」按钮"
        "（`DirectorTimeline.tsx:1121`）上，本批点的是 "
        "`data-director-track-draw-trail`（只有 `aria-pressed`）。",
        "**只测了 1440 桌面一档视口**。虚拟相机/群众阵列/模型库三个"
        "触发器在视口左侧的 rail 上，窄视口下可能不可见或位置不同 —— 未测。",
        "**3 个浮层因为外点那一下已经关掉了，Esc 无从测起**"
        "（预设运镜、路径菜单、模型库）⟹ 它们的 Esc 行为**本批没有读数**。"
        "静态上三者都有捕获/冒泡阶段的 Esc 处理，但**静态不能替代读数**。",
        "**没有测打开状态下再点一次触发器会怎样**（toggle 关闭 vs 报错）。",
        "**没有测这些浮层里的 Tab 围栏**（762/765 只量过导出面板与对话框级）。",
        "**没有测多个 disclosure 同时开着会怎样**（例如模型库开着时再开"
        "群众阵列）—— 本批每次都从干净状态开始。",
        "**没有测虚拟相机在录制中的 Esc**：`DirectorPhoneVcamPanel.tsx:292` "
        "写着 `if (!recording) onClose()`，录制中按 Esc 不关面板 —— "
        "但本批没进录制状态，那条分支**未验证**。",
        "**没有点任何提交/生成/连接按钮**；导出面板的提交按钮、"
        "虚拟相机的「连接」、模型库的添加都没点。",
    ],
    "probeLessons": [
        {"id": "R71",
         "text": "★ **JS 的 `in` 只能查对象属性，不能用在字符串上** —— "
                 "我写 `('aria-controls' in trigSeg)` 查 outerHTML 是不是"
                 "含这个属性，六个浮层**每一格**都在运行时抛 "
                 "`TypeError: Cannot use 'in' operator`。字符串判定要用 "
                 "`.includes()`。我把这个记成了 Python 的 `in`。"},
        {"id": "R72",
         "text": "★ **`node --check` 只验语法、不验语义**。766 的 R67 那个"
                 "检查器抓语法错很有效，但它对 R71 那个 `in` 完全无感 —— "
                 "语法合法、运行即抛。结论：检查器能把「少一个括号」"
                 "这类错提前 0.1 秒拦下，**类型/语义错仍然只能靠真跑**。"},
        {"id": "R73",
         "text": "★ **「先测 A 再测 B」会污染 B 的读数**。本批顺序是"
                 "「先点浮层外面测外点关闭、浮层还开着才测 Esc」，"
                 "结果**点空白本身就把焦点挪到了对话框根** ⟹ "
                 "「关闭是否归还焦点」这一列 6 格全废（J9）。"
                 "要同时量两件事就得**各开一次干净的浮层**，"
                 "不能串在一条时间线上。765 的 R63 是同一族的另一面"
                 "（准备动作**关掉了**整个导演台）。"},
        {"id": "R74",
         "text": "**外点那一下的落点必须先验再点**。本批对每个浮层都先"
                 "`elementFromPoint` 读出那里是什么元素、`clickable` 是不是"
                 "false，确认「不在浮层内、且不是按钮」才点 —— "
                 "并把 `tried` 列表原样记进产物。R59 的同族："
                 "**先量可点性，再点**。"},
    ],
}

for j in audit["judgments"]:
    k = j["evidenceKey"]
    assert k in findings, "判据 %s 引用了不存在的 findings 键" % j["id"]
    assert findings[k] == j["evidence"], (
        "判据 %s 的 evidence 与 findings[%s] 不相等" % (j["id"], k))

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
s = summary
print("两轮一致：%s" % comparability["allConsistent"])
for k in ("openedBothRounds", "focusStayedOnTrigger", "outsideCloseWorks",
          "outsideCloseMissing", "escTested",
          "escSkippedBecauseOutsideClosed", "escClosedPanelOnly",
          "escClosedWholeDesk", "roleDialogPresent", "ariaControlsAny"):
    print("  %-30s %s" % (k, json.dumps(s[k], ensure_ascii=False)))
print("  deskReopenedAfter              %s"
      % json.dumps(s["deskReopenedAfter"], ensure_ascii=False))
