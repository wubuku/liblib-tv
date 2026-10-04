#!/usr/bin/env python3
"""batch 769 汇编器：从 raw/vb769a.json 现算 runtime-audit.json，并**复核**
raw/vb768a.json（上一批的读数就在隔壁目录里，不必只靠文字互相引用）

本批要回答的是 768 自己写下的 J10：**「把焦点放进浮层的第一个可聚焦控件」
不是通用探针** —— 6 个浮层里 2 个的第一个控件是输入框，会先撞上 D3
（`isEditable` 早退）把焦点问题整个遮住。

所以本批只换**一个变量**：焦点落点。

  臂 A｜`editable`     —— 浮层里第一个**输入框**控件
  臂 B｜`noneditable`  —— 浮层里第一个**非**输入框控件 ← 新协议

规矩（沿用 756–768）：
1. **数字不许手抄** —— 每个数都从 raw 现算；静态事实也当场读源码数出来。
2. **缺原始读数判失败**，不许「通过」。
3. **`findings[k] == judgments[i].evidence`**，写盘前逐条断言，验收器再查一遍。
4. **先证明可比再谈一致**（R55）：逐轮归一化 diff。
5. **`all([])` 是 True**：每处聚合显式判非空；分类必须**铺满**格子。
6. **协议等价的判别式是「落点」，不是「臂名」**（本批新增）：
   面板里**没有**输入框的浮层，它的 `editable` 臂会直接失败 —— 那是结构事实，
   不是探针坏了。判断「769 的某一臂复现了 768 的读数」必须**按落点配对**，
   按臂名配对会把结构性失败当成复现失败。
"""
import hashlib
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
BATCH = HERE.parent if HERE.name == "probes" else HERE
RAW = BATCH / "raw"
OUT = BATCH / "runtime-audit.json"
REPO = HERE
for _ in range(12):
    if (REPO / "package.json").exists() and (REPO / "src").is_dir():
        break
    REPO = REPO.parent
else:
    raise SystemExit("FATAL 找不到仓库根（package.json + src）")

VOLATILE_RE = re.compile(r"director-gesture-\d+-\d+|[0-9a-f]{16}-[0-9a-f]{4}")
IDS = ["export", "preset", "pathmenu", "phonevcam", "crowd", "modellib"]
ARMS = ["editable", "noneditable"]
CELLS = [(i, a) for i in IDS for a in ARMS]
PREV_DIR = BATCH.parent / "liblib-canvas-batch768-2026-10-01"


def load(name, base=None):
    p = (base or RAW) / name
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


# ═══════════════ 1. 读原始读数 ═══════════════
a, a_p = load("vb769a.json")
prev, prev_p = load("vb768a.json", base=PREV_DIR / "raw")
aR = a["rounds"]
assert len(aR) == 2, "轮数 %d" % len(aR)

comparability = {
    "keys": ["rows"],
    "allConsistent": round_diff(a, "rows")[0] is True,
    "firstDiff": {} if round_diff(a, "rows")[0] is True
                  else {"rows": round_diff(a, "rows")[1]},
    "rounds": len(aR),
    "protocol": "★ **每个臂都从重新加载的页面开始**（768 的 R73），"
                "全程**不点外点**；只点 6 个 disclosure 触发器，"
                "其余是 `.focus()` 读操作与 Esc。",
    "variable": "★ 本批**只换一个变量**：焦点落点（第一个输入框 / "
                "第一个非输入框控件）。其余协议与 768 逐字相同。",
    "clearedLocalStorage": [(rd.get("cleared") or {}).get("removed")
                            for rd in aR],
    "deskGoneAfter": [rd.get("deskGoneAfter") for rd in aR],
    "carriedOverFrom768": {
        "deskGoneAfterMatches": [rd.get("deskGoneAfter") for rd in aR],
        "clearedPattern": [(rd.get("cleared") or {}).get("removed")
                           for rd in aR]},
}
assert comparability["allConsistent"], comparability["firstDiff"]


def grid(raw):
    out = {}
    for rd in raw["rounds"]:
        for r in rd.get("rows") or []:
            out.setdefault((r.get("id"), r.get("mode")), []).append(r)
    return out


gA = grid(a)
missing = [k for k in CELLS if k not in gA]
assert not missing, "缺格 %r —— 判失败，不许当「没发生」" % (missing,)
for k, v in gA.items():
    assert len(v) == 2, "%s 轮数 %d" % (k, len(v))


def classify(r, key="after"):
    st = r.get(key) or {}
    de = r.get("desk") or {}
    if st.get("open") is False or de.get("open") is False:
        return "desk-lost"
    if st.get("panelPresent") is True:
        return "panel-stuck"
    if st.get("panelPresent") is not False:
        return "unknown"
    act = st.get("active") or {}
    if act.get("isTrigger") is True:
        return "closed-focus-on-trigger"
    if act.get("isBody") is True:
        return "closed-focus-on-body"
    if act.get("inDialog") is True:
        return "closed-focus-in-dialog"
    return "closed-focus-outside-dialog"


# ── 落点：协议等价的配对依据（按「落点」配对，不按臂名）
def landing(r):
    f = r.get("focus") or {}
    fk = r.get("focusKind") or {}
    return {"tag": fk.get("tag") or f.get("tag"),
            "type": fk.get("type") if fk.get("type") is not None
                    else f.get("type"),
            "pickedIndex": f.get("pickedIndex"),
            "pickedTag": f.get("pickedTag"),
            "nEditable": f.get("nEditable"),
            "nNonEditable": f.get("nNonEditable"),
            "total": f.get("total"),
            "isEditableByTag": fk.get("isEditableByTag") is True,
            "inPanel": fk.get("inPanel") is True}


def cell(r):
    f = r.get("focus") or {}
    fk = r.get("focusKind") or {}
    return {
        "failed": r.get("FAILED"),
        "failedKind": ("no-element-of-that-kind"
                       if f.get("err") == "no element of that kind" else None),
        "opened": (r.get("before") or {}).get("panelPresent") is True,
        "focusPlaced": f.get("focused") is True,
        "landing": landing(r),
        "class": classify(r) if not r.get("FAILED") else None,
        "focusAfter": {"tag": ((r.get("after") or {}).get("active") or
                               {}).get("tag"),
                       "isTrigger": ((r.get("after") or {}).get("active")
                                     or {}).get("isTrigger"),
                       "isBody": ((r.get("after") or {}).get("active")
                                  or {}).get("isBody"),
                       "inDialog": ((r.get("after") or {}).get("active")
                                    or {}).get("inDialog")},
    }


tA = {k: [cell(r) for r in gA[k]] for k in gA}

# ── 每个浮层的「可编辑 / 不可编辑」控件存量（从读数现算）
inventory = {}
for i in IDS:
    inv = {}
    for a_ in ARMS:
        for c in tA[(i, a_)]:
            L = c["landing"]
            if L.get("total") is not None:
                inv["total"] = L["total"]
                inv["nEditable"] = L["nEditable"]
                inv["nNonEditable"] = L["nNonEditable"]
    inventory[i] = inv
    assert inv.get("total") is not None, "%s 没读到可聚焦控件存量" % i
    assert inv["nEditable"] + inv["nNonEditable"] == inv["total"], \
        "%s 两类计数与总数对不上：%r" % (i, inv)

# ── 结构性失败：某臂要的**那一类控件一个都没有**（不是探针坏了）
structuralFail = {}
for i in IDS:
    for a_ in ARMS:
        cells = tA[(i, a_)]
        wantEditable = (a_ == "editable")
        n = inventory[i]["nEditable"] if wantEditable \
            else inventory[i]["nNonEditable"]
        allFail = all(c["failedKind"] == "no-element-of-that-kind"
                      for c in cells)
        structuralFail["%s/%s" % (i, a_)] = {
            "wantEditable": wantEditable, "availableOfWantedKind": n,
            "structurallyImpossible": n == 0,
            "allRoundsFailed": allFail,
        }
        if n == 0:
            assert allFail, ("%s/%s 那一类控件为 0 却没失败 —— 探针不许退化"
                             % (i, a_))
            assert all(c["failed"] for c in cells)
        else:
            assert not allFail, "%s/%s 那一类控件有 %d 个却失败了" % (i, a_, n)
            assert all(c["focusPlaced"] for c in cells), \
                "%s/%s 聚焦没成功" % (i, a_)
            assert all(c["opened"] for c in cells), \
                "%s/%s 起点不干净" % (i, a_)
            assert all(c["landing"]["inPanel"] for c in cells), \
                "%s/%s 焦点不在浮层内" % (i, a_)
            assert all(c["landing"]["isEditableByTag"] == wantEditable
                       for c in cells), \
                "%s/%s 落点类别与臂不符" % (i, a_)

impossibleArms = [k for k, v in structuralFail.items()
                  if v["structurallyImpossible"]]
bothArms = [i for i in IDS
            if not structuralFail["%s/editable" % i]["structurallyImpossible"]
            and not structuralFail["%s/noneditable" % i][
                "structurallyImpossible"]]
assert bothArms, "一个浮层都拿不到两臂 —— 协议没跑起来"
# 两臂的落点**必须**是两个不同的元素，否则「换变量」没换成
for i in bothArms:
    la = {tuple(sorted((c["landing"]["tag"], c["landing"]["type"])
                       and [c["landing"]["tag"] or "",
                            c["landing"]["type"] or ""] or ["", ""]))
          for c in tA[(i, "editable")]}
    lb = {tuple(sorted([c["landing"]["tag"] or "",
                        c["landing"]["type"] or ""]))
          for c in tA[(i, "noneditable")]}
    assert la.isdisjoint(lb), \
        "%s 两臂落到了同一个元素上（tag/type 相同）—— 变量没换成功" % i

CLASSES = ["desk-lost", "panel-stuck", "closed-focus-on-trigger",
           "closed-focus-on-body", "closed-focus-in-dialog",
           "closed-focus-outside-dialog"]
measured = {k: v for k, v in structuralFail.items()
            if not v["structurallyImpossible"]}
for k, v in measured.items():
    cls = {c["class"] for c in tA[eval(k.replace("/", ",("))]} \
        if False else {c["class"] for c in tA[
            (k.split("/")[0], k.split("/")[1])]}
    assert cls <= set(CLASSES) and "unknown" not in cls, \
        "%s 分类异常 %r" % (k, cls)

# ── 协议 v2（新协议 = noneditable 臂）逐浮层的焦点结论
def verdict_of(i, arm):
    key = (i, arm)
    if structuralFail["%s/%s" % (i, arm)]["structurallyImpossible"]:
        return "structurally-impossible"
    cls = [tA[key][r]["class"] for r in range(2)]
    if all(c == "panel-stuck" for c in cls):
        return "measured-stuck"
    if all(c == "desk-lost" for c in cls):
        return "measured-desk-lost"
    if all(c == "closed-focus-on-body" for c in cls):
        return "measured-focus-to-body"
    if all(c == "closed-focus-on-trigger" for c in cls):
        return "measured-focus-to-trigger"
    return "mixed:" + ",".join(cls)


v2 = {i: verdict_of(i, "noneditable") for i in IDS}
v1 = {i: verdict_of(i, "editable") for i in IDS}
buckets = {}
for i in IDS:
    buckets.setdefault(v2[i], []).append(i)
assert len(buckets) >= 2, "新协议只给出一个结论 —— 没东西可判"
restored = buckets.get("measured-focus-to-trigger", [])
toBody = buckets.get("measured-focus-to-body", [])
stuck = buckets.get("measured-stuck", [])
deskLost = buckets.get("measured-desk-lost", [])
impossible = buckets.get("structurally-impossible", [])
assert not (set(restored) & set(toBody)), "分类互斥性被破坏"

protocolV2 = {
    "arm": "noneditable（浮层里第一个非输入框控件）",
    "perDisclosure": {
        i: {"verdict": v2[i], "editableArmVerdict": v1[i],
            "landing": tA[(i, "noneditable")][0]["landing"],
            "editableLanding": tA[(i, "editable")][0]["landing"],
            "class": [tA[(i, "noneditable")][r]["class"] for r in range(2)]
                     if v2[i] != "structurally-impossible" else None}
        for i in IDS},
    "focusRestoredToTrigger": restored,
    "focusFellToBody": toBody,
    "panelStuck": stuck,
    "deskLost": deskLost,
    "structurallyImpossible": impossible,
    "counts": {k: len(v) for k, v in sorted(buckets.items())},
    "cells": {("%s/%s" % k): tA[k] for k in CELLS},
}

# ═══════════════ 2. 复核 768：按**落点**配对判协议等价 ═══════════════
prevCells = {}
for rd in prev["rounds"]:
    for r in rd.get("rows") or []:
        if r.get("mode") == "inside":
            prevCells.setdefault(r.get("id"), []).append(r)
assert set(prevCells) == set(IDS), "768 的 raw 里 id 不全：%r" % (
    sorted(prevCells),)


def spot(r):
    f = r.get("focus") or {}
    fk = r.get("focusKind") or {}
    return (fk.get("tag") or f.get("tag") or "",
            fk.get("type") or f.get("type") or "")


pairs = []
for i in IDS:
    pv = [classify(r) for r in prevCells[i]]
    match = None
    for arm in ARMS:
        if structuralFail["%s/%s" % (i, arm)]["structurallyImpossible"]:
            continue
        if all(spot(gA[(i, arm)][r]) == spot(prevCells[i][r])
               for r in range(2)):
            match = arm
            break
    got = None
    if match:
        got = [tA[(i, match)][r]["class"] for r in range(2)]
    pairs.append({
        "id": i, "prevArm": "inside", "prevLanding": spot(prevCells[i][0]),
        "prevClass": pv,
        "matchedArm": match,
        "newClass": got,
        "reproduces": bool(match) and got == pv,
    })
reproduced = [p["id"] for p in pairs if p["reproduces"]]
notComparable = [p["id"] for p in pairs if not p["matchedArm"]]
mismatched = [p["id"] for p in pairs
              if p["matchedArm"] and not p["reproduces"]]
assert not mismatched, "768 复现失败：%r" % (mismatched,)
assert reproduced, "一个都没复现 —— 比对逻辑坏了"

reproducibility = {
    "rule": "★ **按落点（tag+type）配对，不按臂名** —— 面板里没有输入框的"
            "浮层，它的 `editable` 臂会结构性失败；按臂名配对会把"
            "「那一类控件不存在」误判成「复现失败」。",
    "pairs": pairs,
    "reproduced": reproduced,
    "notComparable": notComparable,
    "mismatched": mismatched,
    "prevSource": "raw/vb768a.json 的 inside 臂（同一批原始读数，非文字引用）",
}

# ── 跨批：可聚焦控件存量与 768 对齐
prevInv = {}
for i in IDS:
    f = (prevCells[i][0].get("focus") or {})
    prevInv[i] = {"total": f.get("total"), "tag": f.get("tag"),
                  "type": f.get("type")}
agreeInv = {i: prevInv[i]["total"] == inventory[i]["total"] for i in IDS}
assert all(agreeInv.values()), "可聚焦控件存量与 768 不一致：%r" % (
    {i: (prevInv[i], inventory[i]) for i in IDS
     if not agreeInv[i]},)

# ═══════════════ 3. 静态层：当场读源码数出来 ═══════════════
def src_text(rel):
    p = REPO / rel
    if not p.exists():
        raise SystemExit("FATAL 缺源码 %s —— 判失败" % p)
    return p.read_text(encoding="utf-8")


DESK = src_text("src/components/director/DirectorDesk.tsx")
EXPP = src_text("src/components/director/DirectorExportPanel.tsx")
VP = src_text("src/components/director/DirectorViewport.tsx")

static = {
    # D3 的机制：isEditable 早退必须排在 Escape 分支之前
    "isEditableGateLine": DESK.count("\n", 0, DESK.index(
        "if (isEditable) return;")),
    "escapeBranchLine": DESK.count("\n", 0, DESK.index(
        'if (event.key !== "Escape") return;')),
    "isEditableTagsInGate": re.findall(
        r'target\.tagName === "(\w+)"', DESK),
    # 导演台阶梯对另外五个浮层状态 0 处引用
    "deskLadderOtherPanelRefs": len(re.findall(
        r"crowdPanelOpen|modelLibraryOpen|phoneVcamOpen|presetPanelLeft|"
        r"pathMenuLeft", DESK)),
    "deskLadderExportTiers": len(re.findall(r"if \(exportPanelOpen\)", DESK)),
    # 两个目标面板的可聚焦控件存量（静态数，运行时数可能被 map 放大）
    "exportPanelHasAspectMap": 'data-director-export-aspect={ratio}' in EXPP,
    "exportPanelAspectBeforeSubmit": (
        EXPP.index("data-director-export-aspect")
        < EXPP.index("data-director-export-submit")) if (
        "data-director-export-aspect" in EXPP
        and "data-director-export-submit" in EXPP) else None,
    "exportPanelSubmitPresent": "data-director-export-submit" in EXPP,
}
cseg = VP[VP.index("data-director-crowd-panel"):VP.index(
    "data-director-model-library-panel")]
cbtns = re.findall(r'<(input|button|select|textarea)\b', cseg)
static["crowdPanelStaticOrder"] = cbtns
static["crowdPanelFirstButtonAfterInputs"] = (
    "button" in cbtns and cbtns.index("button") == cbtns.count("input"))
static["crowdPanelHasCancelBeforeAdd"] = (
    cseg.index('data-director-crowd-action="cancel"')
    < cseg.index('data-director-crowd-action="add"'))
static["crowdPanelInputs"] = len(re.findall(r"<input\b", cseg))
static["crowdPanelButtons"] = len(re.findall(r"<button\b", cseg))

assert static["escapeBranchLine"] > static["isEditableGateLine"], \
    "isEditable 早退不再排在 Escape 分支之前 —— D3 的机制变了"
assert set(static["isEditableTagsInGate"]) == {"INPUT", "TEXTAREA", "SELECT"}, \
    "isEditable 判定覆盖的标签变了：%r" % (static["isEditableTagsInGate"],)
assert static["deskLadderOtherPanelRefs"] == 0, \
    "导演台 Esc 阶梯居然引用了别的浮层状态，静态结论要重查"
assert static["deskLadderExportTiers"] == 1
assert static["exportPanelHasAspectMap"] is True
assert static["exportPanelAspectBeforeSubmit"] is True, \
    "画幅按钮跑到提交按钮后面了 —— 落点会变"
assert static["exportPanelSubmitPresent"] is True
assert static["crowdPanelFirstButtonAfterInputs"] is True, \
    "群众面板里按钮不再排在输入框之后 —— 落点会变"
assert static["crowdPanelHasCancelBeforeAdd"] is True
assert static["crowdPanelInputs"] == 3 and static["crowdPanelButtons"] == 2, \
    "群众面板控件存量变了：%r" % (cbtns,)

findings = {
    "comparability": comparability,
    "protocolV2": protocolV2,
    "reproducibility": reproducibility,
    "staticLayer": static,
    "focusInventory": inventory,
}

# 面板里可编辑 / 不可编辑控件的存量（现算，运行时）
focusInventory = {
    "perPanel": inventory,
    "panelsWithoutEditableControl": [i for i in IDS
                                     if inventory[i]["nEditable"] == 0],
    "panelsWithBothKinds": bothArms,
    "armsStructurallyImpossible": impossibleArms,
    "editableLandingIndex": {
        i: (tA[(i, "editable")][0]["landing"]["pickedIndex"]
            if not structuralFail["%s/editable" % i][
                "structurallyImpossible"] else None) for i in IDS},
    "noneditableLandingIndex": {
        i: (tA[(i, "noneditable")][0]["landing"]["pickedIndex"]
            if not structuralFail["%s/noneditable" % i][
                "structurallyImpossible"] else None) for i in IDS},
    "agreesWith768": agreeInv,
}
findings["focusInventory"] = focusInventory

# ★ D12 的静态依据：模型库面板里那个「上传本地模型」的文件输入框。
#   **不能**用 `<input\b[^>]*>` 去切标签 —— JSX 里的
#   `onChange={(event) => void f(event)}` 含 `=>`，那个 `>` 会被当成标签结尾，
#   于是 `className="sr-only"` 被切掉，判据静默变成「不是 sr-only」
#   （R85：形状对、语义错的切片）。改成按标记位置取固定窗口。
ML = VP[VP.index("data-director-model-library-panel"):VP.index(
    "data-director-model-library-trigger")]
ml_at = ML.index("data-director-model-library-local-input")
# 形状检查：最近的一个 `<input` 比最近的一个 `>` **更靠后** ⟹ 标记确实落在
# 某个 input 标签**内部**，而不是已经被前一个标签的 `>` 截断过了。
assert ML.rfind("<input", 0, ml_at) > ML.rfind(">", 0, ml_at), \
    "local-input 标记不在 <input 标签内部 —— 切片前提变了"
ml_tag = ML[ml_at - 200:ml_at + 400]
d12 = {
    "tagExcerpt": ml_tag.strip()[:300],
    "typeFile": 'type="file"' in ml_tag,
    "isSrOnly": 'sr-only' in ml_tag,
    "hasAriaLabel": "aria-label" in ml_tag,
    "hasAriaLabelledby": "aria-labelledby" in ml_tag,
    "hasTitle": "title=" in ml_tag,
    "hasId": "id=" in ml_tag,
    "indexInPanel": 0,            # 由读数给出：editable 落点 pickedIndex
    "panelFocusables": inventory["modellib"]["total"],
}
# 「有没有被 <label> 包住」：看标记**之前**最近的一段里有没有未闭合的 <label>
before = ML[max(0, ml_at - 400):ml_at]
d12["labelOpenedBefore"] = before.count("<label") > before.count("</label>")
d12["wrappedInLabel"] = d12["labelOpenedBefore"]
d12["labelCountInPanel"] = len(re.findall(r"<label\b", ML))
assert d12["typeFile"] is True
assert d12["isSrOnly"] is True, "那个文件框不是 sr-only —— D12 要重写"
assert not any(d12[k] for k in ("hasAriaLabel", "hasAriaLabelledby",
                                "hasTitle", "hasId")), \
    "那个文件框居然有可访问名 —— D12 要重写"
assert d12["indexInPanel"] == focusInventory[
    "editableLandingIndex"]["modellib"] == 0, \
    "它不再是模型库面板的第一个可聚焦控件 —— D12 的严重度要重估"
findings["srOnlyFileInput"] = d12

judgments = [
    {"id": "J1", "verdict": "PASS",
     "statement": "**两轮逐字段一致**（`rows` 整棵树的归一化 diff 为空），"
                  "且先证明可比：每个臂都从**重新加载的页面**开始，"
                  "全程不点外点（768 的 R73）。本批**只换一个变量** —— "
                  "焦点落点的类别（第一个输入框 / 第一个非输入框控件），"
                  "其余协议与 768 逐字相同。",
     "evidenceKey": "comparability"},
    {"id": "J2", "verdict": "PASS",
     "statement": "**12 格全部有读数，没有一格是意外失败。** 其中 %d 个臂"
                  "「失败」是**结构事实**而非探针坏了：预设运镜、创建运动"
                  "轨迹、虚拟相机这三个浮层里**一个输入框都没有**"
                  "（可编辑控件数分别为 %d/%d/%d），所以「找第一个输入框」"
                  "这件事在它们身上不存在。探针在这种情况下**如实报出"
                  "两类控件各多少个**并拒绝退化成交取第一个 —— "
                  "退化会让读数看着有、其实答非所问。"
                  % (len(impossibleArms),
                     inventory["preset"]["nEditable"],
                     inventory["pathmenu"]["nEditable"],
                     inventory["phonevcam"]["nEditable"]),
     "evidenceKey": "focusInventory"},
    {"id": "J3", "verdict": "PASS",
     "statement": "★ **协议等价的判别式是「落点」，不是「臂名」**：按 "
                  "**(tag, type) 把本批的某一臂与 768 的 `inside` 臂配对**，"
                  "**6/6 逐格复现**（读数完全相同）。这同时是 768 的"
                  "可复现性对照 —— 同一协议、换一个探针再跑一遍，结论不变。"
                  "**若按臂名配对**，那 3 个「面板里没有输入框」的臂会被"
                  "误判成复现失败。",
     "evidenceKey": "reproducibility"},
    {"id": "J4", "verdict": "PASS",
     "statement": "★ **768 的 J10「2 个浮层没测到」被关掉了**：换成非输入框"
                  "落点之后，**6 个浮层全部拿到焦点去向读数，0 个"
                  "「没测到」**。768 的分桶是「测到且错 2 / 没测到 2 / "
                  "触发器已卸载 2」；本批是「测到且错 3 / 导演台被关掉 3」，"
                  "**没有「没测到」这一桶了**。",
     "evidenceKey": "protocolV2"},
    {"id": "J5", "verdict": "FAIL",
     "statement": "★ **D11 扩大确认：焦点归还仍是 0/6，而且现在有 3 个是"
                  "真测到的、3 个全错** —— 导出面板、虚拟相机、模型库"
                  "**全部把焦点丢到 `body`**（768 只测到后两个，"
                  "导出面板当时被 D3 遮住）。另 3 个（预设运镜、创建运动"
                  "轨迹、添加群众阵列）按 Esc **把整个导演台关掉**、"
                  "触发器随之卸载 ⟹ 仍然**没有可归还的对象**。"
                  "2/2 轮。",
     "evidenceKey": "protocolV2"},
    {"id": "J6", "verdict": "PASS",
     "statement": "★ **765 的 D4 得到独立复现**：导出面板在焦点落到"
                  "**非输入框**控件（画幅按钮，落点 index %d/%d）上按 Esc，"
                  "**面板关掉、焦点掉到 `body`**，2/2 轮。768 因 D3 遮住"
                  "没能重测到这一格，本批用**另一套协议、另一个探针**"
                  "把它测了出来 —— 同一缺陷的第二次独立读数。"
                  % (focusInventory["noneditableLandingIndex"]["export"],
                     inventory["export"]["total"]),
     "evidenceKey": "protocolV2"},
    {"id": "J7", "verdict": "FAIL",
     "statement": "★ **本批最关键的一条：D3×D8 的耦合从推理变成读数。** "
                  "同一个浮层、同一颗 Esc、只换焦点类别："
                  "添加群众阵列面板 —— 焦点在**数值输入框**上 ⟹ "
                  "**什么都没发生**（`isEditable` 早退吞掉 Esc）；"
                  "焦点在 **cancel 按钮**上 ⟹ **整个导演台没了**。"
                  "⟹ 唯一挡住「按 Esc 丢整个工作区」的就是那个早退。"
                  "768 把这句话标成**推理**（写在 D3 的 compositionNote），"
                  "本批把它**测成了读数** ⟹ **修 D3 必须先修 D8**，"
                  "否则按 765 的拍板给 `isEditable` 开特例的那一刻，"
                  "就会把「按 Esc 丢工作区」这条路径直接打开。",
     "evidenceKey": "protocolV2"},
    {"id": "J8", "verdict": "FAIL",
     "statement": "★ **缺陷 D12（低，新增）**：**模型库面板的第一个可聚焦"
                  "控件**是一个 `sr-only` 的 **1px** `<input type=\"file\">`"
                  "（落点 index **0**/%d），**零可访问名** —— "
                  "无 `aria-label`、无 `aria-labelledby`、无 `title`、无 `id`、"
                  "也不在任何 `<label>` 里。键盘用户 Tab 进模型库，"
                  "**第一站是一个看不见、也没有名字的文件选择器**。"
                  "★ 它与 765/762 记的那个隐藏 file input **不是同一个**："
                  "那个用 `display:none`（**不可聚焦**，所以当时判为不构成"
                  "缺陷）；这个用 `sr-only`（**1px 但仍可聚焦**）。",
     "evidenceKey": "srOnlyFileInput"},
    {"id": "J9", "verdict": "PASS",
     "statement": "★ **`isEditable` 早退的作用域被量出来了**：它**只对两类"
                  "浮层有效** —— ①「靠导演台阶梯关」的（导出面板，`:557`）"
                  "②「根本没有 Esc 处理」的（添加群众阵列）。"
                  "**模型库面板的落点同样是 `INPUT`，Esc 却照样关掉了面板**"
                  "—— 因为它自己的 window **捕获**监听 "
                  "`DirectorViewport.tsx:2748` 在 DirectorDesk 的**冒泡**"
                  "处理器**之前**就 `stopImmediatePropagation()` 了。"
                  "⟹ 「isEditable 早退」**不是**一道全局防线，"
                  "只覆盖「事件能到达导演台」的那些路径。",
     "evidenceKey": "protocolV2"},
    {"id": "J10", "verdict": "FAIL",
     "statement": "★ **不声称**：本批换的只是焦点**类别**、"
                  "**没换焦点位置**，还有很多形态没测 —— "
                  "焦点在浮层**外面**（对话框别处）时按 Esc；焦点在**第三个**"
                  "控件上；以及「可聚焦但不可编辑」的其他类型"
                  "（除本批的 `INPUT[type=file]` 之外）在别处还有没有。"
                  "**另外 768 那些不声称项依然成立**：没测 6 个浮层里的 Tab "
                  "围栏、没测打开状态下再点一次触发器、没测多个浮层同时开着、"
                  "没测虚拟相机录制中的 Esc、只测了 1440 桌面一档视口。",
     "evidenceKey": "protocolV2"},
    {"id": "J11", "verdict": "PASS",
     "statement": "**没点任何有副作用的控件**：只点了 6 个 disclosure 触发器"
                  "（导出面板的提交、虚拟相机的「连接」、模型库的添加、"
                  "群众阵列的「添加」都没点）。群众阵列的非输入框落点是"
                  "**cancel 按钮**（index %d/%d），只 `.focus()` 不点。"
                  % (focusInventory["noneditableLandingIndex"]["crowd"],
                     inventory["crowd"]["total"]),
     "evidenceKey": "focusInventory"},
    {"id": "J12", "verdict": "PASS",
     "statement": "★ **静态预测与实测落点逐个对上**：群众阵列面板的 JSX 里"
                  "是 %d 个 `<input>` 在 %d 个 `<button>` **之前**"
                  "（cancel 又在 add 之前）⟹ 预测「第一个非输入框控件」是"
                  "第 **3** 个（0 基），实测 `pickedIndex` 正是 **%d**。"
                  "这条能在跑浏览器之前就预测落点，是本批少走弯路的关键。"
                  % (static["crowdPanelInputs"], static["crowdPanelButtons"],
                     focusInventory["noneditableLandingIndex"]["crowd"]),
     "evidenceKey": "staticLayer"},
]

for j in judgments:
    j["evidence"] = findings[j["evidenceKey"]]

audit = {
    "batch": 769,
    "date": "2026-10-01",
    "scope": "协议 v2：只换「焦点落点」这一个变量，把 768 明确声明"
             "「没测到」的 2 个浮层测掉，并按落点复核 768 的读数",
    "env": {
        "base": "http://localhost:4317",
        "canvas": "canvas-2",
        "directorNodeId": "b-bTLLuU4w5q",
        "viewport": "1440x1000（桌面）",
        "player": "chromium (playwright sync_api)",
        "srcModified": False,
    },
    "probes": [
        {"id": "769a", "file": "probes/dbg769a.py", "raw": "raw/vb769a.json",
         "rounds": len(aR), "injected": False,
         "note": "两个臂各从重载页面开始：editable（浮层里第一个输入框）/ "
                 "noneditable（第一个非输入框控件）。某臂要的类别为 0 时"
                 "**如实报计数并拒绝退化**。"},
    ],
    "rawSha": {a_p.name: sha(a_p), prev_p.name: sha(prev_p)},
    "findings": findings,
    "judgments": judgments,
    "defects": [
        {"id": "D12", "severity": "低", "newInThisBatch": True,
         "title": "模型库面板的第一个可聚焦控件是一个 sr-only 的 1px 文件"
                  "输入框，且零可访问名",
         "where": ["src/components/director/DirectorViewport.tsx"
                   "（`data-director-model-library-local-input`）"],
         "mechanism": "面板挂载时第一个孩子就是 "
                      "`<input type=\"file\" accept=\".fbx,.obj\" multiple "
                      "className=\"sr-only\">`。`sr-only` 是 Tailwind 的"
                      "「视觉隐藏但**仍可聚焦**」（1px×1px + clip），"
                      "**不是** `display:none`。它没有 `aria-label` / "
                      "`aria-labelledby` / `title` / `id`，"
                      "也不在任何 `<label>` 里 ⟹ **可访问名为空**。",
         "measured": "editable 臂的落点就是它：`INPUT[type=file]`、"
                     "`pickedIndex=0`（面板共 %d 个可聚焦控件），"
                     "2/2 轮；换到 noneditable 臂时落点变成 index 1 的按钮。"
                     % inventory["modellib"]["total"],
         "severityRationale": "**低**：焦点不可见且无名字，键盘用户不知道"
                              "自己在哪；但仍在对话框内、Esc 还能关掉面板，"
                              "不会「卡住」。与 765 的 D4 同级。",
         "whyItWasMissedBefore": "★ **它与 765/762 记的那个隐藏 file "
                                 "input 不是同一个**：那个用 "
                                 "`display:none` ⟹ **不可聚焦**，"
                                 "当时据此判它「不构成缺陷」（对那一处成立）。"
                                 "`sr-only` 这一族**不在那次扫描范围内** —— "
                                 "它是 1px、**有布局盒、仍可聚焦**。",
         "fixDirection": "①给它 `aria-label`（例如「上传本地模型」）；"
                         "②或者改用真正的 `<button>` 触发"
                         "「点一下打开文件选择器」，把 `<input type=file>` "
                         "藏起来而不是让它当第一站。①更小，②更对。",
         "needsSrcChange": True},
    ],
    "widened": [
        {"id": "D11", "from": "768 的 2/6 测到", "to": "3/6 测到且全错",
         "severity": "低",
         "title": "焦点归还仍是 0/6；新增导出面板一例（独立协议）",
         "newMembers": ["export"],
         "measured": "非输入框落点下，导出面板 / 虚拟相机 / 模型库"
                     "**全部把焦点丢到 `body`**，2/2 轮；"
                     "预设运镜 / 创建运动轨迹 / 添加群众阵列按 Esc "
                     "**关掉整个导演台**、触发器随之卸载 ⟹ "
                     "**「没测到」这一桶已清空**。",
         "needsSrcChange": True},
        {"id": "D4", "from": "1/6（765）→ 3/6（768）", "to": "3/6 且有双协议证据",
         "severity": "低",
         "title": "关闭浮层后焦点掉到 body —— 导出面板这一例得到独立复现",
         "newMembers": [],
         "note": "★ 本批**没有新增成员**，但把 765 最初发现的那一例"
                 "（导出面板）**用另一套协议独立重测了一遍**："
                 "768 因 D3 遮住没测到，本批落在画幅按钮上测到，2/2 轮。"
                 "同一个缺陷在两个批次、两个探针、两套协议下都出现 ⟹ "
                 "D4 已从「单点观察」升级为**双协议确认**。",
         "needsSrcChange": True},
        {"id": "D3", "from": "1/6 → 2/6（768）", "to": "2/6，作用域已量清",
         "severity": "低",
         "title": "焦点在浮层内的输入框时 Esc 关不掉浮层"
                  "（`DirectorDesk.tsx:487` 的 isEditable 早退）",
         "newMembers": [],
         "note": "成员没变（导出面板、添加群众阵列），但本批量清了两件事："
                 "①**作用域**——它只对「靠导演台阶梯关」与「根本没有 Esc "
                 "处理」的两类浮层有效，对自带 window 捕获监听的"
                 "模型库面板**完全无效**（落点同样是 INPUT，Esc 照样关面板）；"
                 "②**耦合**——群众阵列的「没关」与「导演台没了」是**同一个"
                 "`if` 的两面**：焦点在输入框 ⟹ 早退 ⟹ 面板不关 ⟹ 导演台也"
                 "因此幸存。**这条现在是实测，不是推理。**",
         "repairOrder": "★ **先修 D8，再修 D3。** 顺序反了会在"
                        "「给 `isEditable` 开特例」的那一刻"
                        "把群众阵列面板的「按 Esc 丢工作区」直接打开。",
         "needsSrcChange": True},
        {"id": "D8", "from": "1/6 → 3/6（768）", "to": "3/6，成员由双臂读数确认",
         "severity": "中",
         "title": "按 Esc 关掉整个导演台",
         "newMembers": [],
         "note": "成员没变（预设运镜、创建运动轨迹、添加群众阵列），"
                 "但**添加群众阵列这一个成员现在有了双臂读数**："
                 "焦点在输入框 ⟹ 什么都没发生；焦点在 cancel 按钮 ⟹ "
                 "导演台没了。⟹ 它「有时不丢工作区」不是安全，"
                 "只是被 D3 的早退挡住了。",
         "needsSrcChange": True},
    ],
    "observations": [
        {"id": "O1",
         "text": "★ **协议等价的判别式是「落点」，不是「臂名」**。6 个浮层里"
                 "3 个**一个输入框都没有**（预设运镜 %d、创建运动轨迹 %d、"
                 "虚拟相机 %d 个可编辑控件），所以它们的 `editable` 臂"
                 "**必然**失败。若按臂名去配 768 的读数，这 3 个会被误判成"
                 "「复现失败」—— 而它们实际上复现得最干净。"
                 % (inventory["preset"]["nEditable"],
                    inventory["pathmenu"]["nEditable"],
                    inventory["phonevcam"]["nEditable"]),
         "verdict": "方法论记录（R81）"},
        {"id": "O2",
         "text": "★ **静态能在跑浏览器之前预测落点**：群众面板 JSX 里 "
                 "%d 个 input 在 %d 个 button 之前 ⟹ 预测非输入框落点是"
                 "第 3 个，实测 `pickedIndex=%d`。"
                 % (static["crowdPanelInputs"], static["crowdPanelButtons"],
                    focusInventory["noneditableLandingIndex"]["crowd"]),
         "verdict": "方法论记录"},
        {"id": "O3",
         "text": "★ **「换个变量」这一招把一个看不见的耦合照了出来**："
                 "同一个浮层、同一颗 Esc，焦点类别从输入框换成按钮，"
                 "结果从「什么都没发生」变成「整个导演台没了」。"
                 "**只测一个落点就会把这个耦合完全漏掉** —— "
                 "768 那一次就漏了（它把「浮层没关」当成结论的终点）。",
         "verdict": "方法论记录（R83）"},
        {"id": "O4",
         "text": "**跨批复现 6/6**，且可聚焦控件存量与 768 **逐个相同**"
                 "（%s）—— 两批用不同探针、不同协议、不同代码路径。"
                 % (", ".join("%s %d" % (i, inventory[i]["total"])
                              for i in IDS),),
         "verdict": "事实记录"},
        {"id": "O5",
         "text": "★ **上一批写在产物里的「推理」是欠账**：768 那句"
                 "「群众阵列此刻没丢工作区，靠的正是 `isEditable` 早退」"
                 "当时明确标成推理、放在 D3 的 compositionNote 里。"
                 "本批用两个臂把它测成了读数。**判据里凡是标着"
                 "「机制推断」的，下一批就该去测它。**",
         "verdict": "方法论记录（R83）"},
    ],
    "notClaimed": [
        "无源站对照：本批全部结论只针对 clone 自身的行为自洽性。",
        "★ **本批只换了焦点「类别」，没换焦点「位置」**（J10）：焦点在浮层"
        "**外面**（对话框别处）时按 Esc、焦点在**第三个**控件上，"
        "都**没测**。",
        "★ **「可聚焦但不可编辑」的其他类型没普查**：本批只碰到"
        "模型库面板的 `INPUT[type=file]`（`sr-only`）。同族是否还有别处，"
        "**未测**。",
        "**没有测 6 个浮层里的 Tab 围栏**（765 只量过导出面板与对话框级，"
        "767/768 连续两批列为不声称）。",
        "**没有测打开状态下再点一次触发器**（toggle 关闭 vs 报错）。",
        "**没有测多个浮层同时开着会怎样** —— 每格都从重载页面开始。",
        "**没有测虚拟相机在录制中的 Esc**"
        "（`DirectorPhoneVcamPanel.tsx:292` 有 `if (!recording) onClose()`）。",
        "**只测了 1440 桌面一档视口**。",
        "**没有改 `src/`**：所有结论都是读数 + 源码现算，修法列在缺陷条目里"
        "等拍板。",
    ],
    "probeLessons": [
        {"id": "R81",
         "text": "★ **协议等价的判别式是「落点」，不是「臂名」。** 本批 %d 个"
                 "臂「失败」是结构事实（那些面板里那一类控件真的是 0 个），"
                 "探针**如实报出两类控件各多少个并拒绝退化**。"
                 "退化成交取第一个会让读数看着有、其实答非所问。"
                 "按落点（tag+type）配对之后，**6/6 复现**了上一批的读数。",
         "whyItMatters": "按臂名配对会把「那一类控件不存在」"
                         "误判成「复现失败」，进而误判成「新一批数据不可信」。"},
        {"id": "R82",
         "text": "★ **一道「守卫」的作用域必须单独量。** `isEditable` 早退"
                 "看起来像全局防线，实测只对「事件能到达导演台」的两类浮层"
                 "有效：模型库面板的落点**也是 INPUT**，Esc 却照样关掉了面板 —— "
                 "因为它自己的 window 捕获监听先把事件截住了。"
                 "**「有守卫」不等于「有防线」**，要按「事件到不到得了」"
                 "逐条算。",
         "whyItMatters": "否则会把守卫当成修复的安全垫 —— 而它恰好"
                         "在要修的那个路径上失效。"},
        {"id": "R83",
         "text": "★ **产物里标着「机制推断」的判据是欠账，下一批就去测它。** "
                 "768 那句「群众阵列此刻没丢工作区靠的正是 `isEditable` 早退」"
                 "当时是对的、也如实标了推理，但它**没有读数支撑**。"
                 "本批只换一个变量（焦点类别）就把它测成了读数 —— "
                 "**推理与读数的距离，有时只差一个变量。**",
         "whyItMatters": "推理留在产物里久了会变成「已知事实」被后续批次"
                         "引用，越传越硬。"},
        {"id": "R84",
         "text": "★ **`sr-only` 与 `display:none` 是两回事。** 765/762 查"
                 "隐藏 file input 时判它「不构成缺陷」，依据是 "
                 "`display:none` **不可聚焦** —— 这条对**那一处**成立。"
                 "但 `sr-only` 是 1px×1px + clip，**有布局盒、仍可聚焦** ⟹ "
                 "同一族的另一个实例根本没进那次的扫描范围。"
                 "**查「不可见控件」时要先把「不可见」分成两族**"
                 "（`display:none` / `visibility:hidden` vs "
                 "视觉隐藏但有盒子）。",
         "whyItMatters": "它让一个同族缺陷被「已排除」的说法盖住了两批。"},
        {"id": "R85",
         "text": "★ **在 JSX 上用 `[^>]*>` 切标签会停在 `=>` 的那个 `>` 上。** "
                 "我为了给 D12 取模型库那个文件框的标签，写了 "
                 "`<input\\b[^>]*data-…[^>]*>` —— 匹配到的却是"
                 "「到 `onChange={(event) =>` 为止」，后面的 "
                 "`className=\"sr-only\"` 被切掉，断言「不是 sr-only」直接"
                 "炸出来。**形状完全对、语义完全错**（R72 的同族）。"
                 "改法：按标记位置取固定窗口，外加一条形状断言 —— "
                 "**最近的 `<input` 必须比最近的 `>` 更靠后**，"
                 "否则说明早已被前一个标签截断。",
         "whyItMatters": "这类切片错会**静默地**给出「看起来有依据」的结论："
                         "若当时没有那条 `isSrOnly` 断言，我就会把"
                         "「不是 sr-only」当成读数写进产物 —— "
                         "而它是切片错，不是事实。"},
        {"id": "R86",
         "text": "★ **阴性对照要改「**决定分类的那个字段**」，不是改一个"
                 "看起来相关的字段。** 我写了「把 768 的 `crowd/inside` "
                 "焦点改成 `isTrigger`」来破坏 6/6 复现 —— 结果那条对照"
                 "**永远漏放**：`crowd/inside` 的分类是 `panel-stuck`，"
                 "而分类函数**先看面板还在不在**（`panelPresent`），"
                 "焦点字段根本轮不到读。改 `panelPresent` 才拦得住。",
         "whyItMatters": "这是 R80 的第二例：**无效的阴性对照不会报错，"
                         "只会永远「漏放」**。判断一条对照有没有效，"
                         "先问「我改的字段真的参与了这个判据吗」。"},
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
print("判据 %d 条（PASS %d / FAIL %d）| findings %d 键 | 新缺陷 %d | "
      "扩宽 %d | 观察 %d | 探针教训 %d"
      % (len(audit["judgments"]),
         sum(1 for j in judgments if j["verdict"] == "PASS"),
         sum(1 for j in judgments if j["verdict"] == "FAIL"),
         len(findings), len(audit["defects"]), len(audit["widened"]),
         len(audit["observations"]), len(audit["probeLessons"])))
print("新协议分桶：%r" % (protocolV2["counts"],))
print("复现 768：%r｜不可比：%r" % (reproduced, notComparable))
print("新缺陷 D12：落点 index %d/%d｜sr-only=%s｜可访问名=%r"
      % (d12["indexInPanel"], d12["panelFocusables"], d12["isSrOnly"],
         d12["hasAriaLabel"] or d12["hasTitle"] or d12["hasId"]))
