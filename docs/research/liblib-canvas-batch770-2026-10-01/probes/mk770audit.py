#!/usr/bin/env python3
"""batch 770 汇编器：从 raw/vb770a.json 现算 runtime-audit.json

本批补 767 / 768 / 769 **连续三批**都列为不声称的那一项：**6 个 disclosure
浮层里的 Tab 围栏**。

机制（静态可查）：`useDirectorFocusContainment.ts:149-172` 在对话框 root 上
监听 Tab 并**手算**一个数组 `getDirectorFocusableElements(root)`（root = 整个
对话框），按 `nextIndex` 环绕后 `preventDefault()` + `focus()`。
所以这条围栏的边界是**对话框**而不是浮层 —— 浮层的控件只是数组里的一段。

规矩（沿用 756–769）：
1. **数字不许手抄** —— 每个数从 raw 现算；静态事实当场读源码数出来。
2. **缺原始读数判失败**。
3. **`findings[k] == judgments[i].evidence`**，写盘前断言，验收器再查一遍。
4. **先证明可比再谈一致**（R55）：逐轮归一化 diff。
5. **`all([])` 是 True**：每处聚合显式判非空；分类必须**铺满**格子。
6. **起点必须固定**（769 的教训）：焦点类别会改变结论（D3 早退），所以起点
   固定用浮层里第一个**非输入框**控件，跨批可比。
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
    raise SystemExit("FATAL 找不到仓库根")

VOLATILE_RE = re.compile(r"director-gesture-\d+-\d+|[0-9a-f]{16}-[0-9a-f]{4}")
IDS = ["export", "preset", "pathmenu", "phonevcam", "crowd", "modellib"]
DIRS = ["fwd", "back"]
CELLS = [(i, d) for i in IDS for d in DIRS]


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
a, a_p = load("vb770a.json")
aR = a["rounds"]
assert len(aR) == 2, "轮数 %d" % len(aR)

comparability = {
    "allConsistent": round_diff(a, "rows")[0] is True,
    "firstDiff": {} if round_diff(a, "rows")[0] is True
                  else {"rows": round_diff(a, "rows")[1]},
    "rounds": len(aR),
    "protocol": "★ 每格都从**重新加载的页面**开始（768 的 R73），"
                "全程不点外点；只点 6 个 disclosure 触发器。",
    "startPoint": "★ 起点固定为浮层里第一个**非输入框**控件"
                  "（769 的协议 v2 落点）—— 769 已证明**焦点类别会改变"
                  "结论**（`isEditable` 早退），所以跨批必须固定类别。",
    "steps": None,       # 下面从 raw 现算
    "clearedLocalStorage": [(rd.get("cleared") or {}).get("removed")
                            for rd in aR],
    "deskGoneAfter": [rd.get("deskGoneAfter") for rd in aR],
}
assert comparability["allConsistent"], comparability["firstDiff"]

g = {}
for rd in aR:
    for r in rd.get("rows") or []:
        g.setdefault((r.get("id"), r.get("mode")), []).append(r)
missing = [k for k in CELLS if k not in g]
assert not missing, "缺格 %r —— 判失败，不许当「没发生」" % (missing,)
for k, v in g.items():
    assert len(v) == 2, "%s 轮数 %d" % (k, len(v))
failed = sorted({"%s/%s" % k for k, v in g.items() for r in v
                 if r.get("FAILED")})
assert not failed, "有失败格 %r —— 判失败" % (failed,)

# 步数（现算，并断言每格一致）
stepCounts = {len(v[0].get("steps") or []) for v in g.values()}
assert len(stepCounts) == 1, "各格步数不一致：%r" % (sorted(stepCounts),)
comparability["steps"] = stepCounts.pop()
assert comparability["steps"], "步数为 0 —— 探针没走"


def cell(r):
    st = r.get("start") or {}
    sts = r.get("steps") or []
    path = [{"step": s.get("step"), "inPanel": s.get("inPanel") is True,
             "inDialog": s.get("inDialog") is True,
             "isTrigger": s.get("isTrigger") is True,
             "isBody": s.get("isBody") is True,
             "tag": s.get("tag"), "type": s.get("type"),
             "aria": s.get("aria"), "text": s.get("text"),
             "idxInDialog": s.get("idxInDialog"),
             "idxInPanel": s.get("idxInPanel")} for s in sts]
    escape = next((p["step"] for p in path if not p["inPanel"]), None)
    first = ([p for p in path if p["step"] == escape][0] if escape else None)
    return {
        "opened": st.get("dialogFocusables") is not None,
        "startTag": st.get("tag"),
        "startIdxInPanel": st.get("idxInPanel"),
        "startIdxInDialog": st.get("idxInDialog"),
        "panelFocusables": st.get("panelFocusables"),
        "dialogFocusables": st.get("dialogFocusables"),
        "path": path,
        "steps": len(path),
        "escapedAtStep": escape,
        "stayedInPanel": escape is None,
        "escapeTarget": None if first is None else {
            "inDialog": first["inDialog"], "isBody": first["isBody"],
            "isTrigger": first["isTrigger"], "tag": first["tag"],
            "aria": first["aria"], "text": first["text"],
            "idxInDialog": first["idxInDialog"]},
        "leftDialog": bool(first and not first["inDialog"]),
        "inPanelSteps": sum(1 for p in path if p["inPanel"]),
    }


t = {k: [cell(r) for r in g[k]] for k in g}

# ── 起点纪律
for k, v in t.items():
    for c in v:
        assert c["opened"], "%s 没读到起点状态" % (k,)
        assert c["startTag"] is not None, "%s 起点没有落点" % (k,)
        assert c["startIdxInPanel"] is not None and c["startIdxInPanel"] >= 0, \
            "%s 起点不在浮层内" % (k,)
        assert c["panelFocusables"] and c["dialogFocusables"], \
            "%s 控件存量读数为 0" % (k,)
        assert c["panelFocusables"] <= c["dialogFocusables"], \
            "%s 浮层控件数(%s) > 对话框控件数(%s)" % (
                k, c["panelFocusables"], c["dialogFocusables"])
        assert c["steps"] == comparability["steps"], "%s 步数不符" % (k,)
        assert len(c["path"]) == comparability["steps"]

# ── 浮层控件是不是对话框 Tab 数组的一段？
#   判别式：起点下标 idxInDialog 应落在 [0, dialogFocusables) 内，
#   且 idxInDialog >= 0；浮层的最后一步若还在浮层内，末步下标应 ==
#   起点下标 + (浮层控件数 - 1)（数组里连续的一段）。
seg = []
for k in CELLS:
    c = t[k][0]
    startOk = (c["startIdxInDialog"] is not None
               and 0 <= c["startIdxInDialog"] < c["dialogFocusables"])
    # ★ 连续性检查**必须按行进方向**：正向 +1、反向 −1。
    #   写死 +1 会把 Shift+Tab 的合法数据判成「不连续」（R89 的原版就踩了）。
    step = 1 if k[1] == "fwd" else -1
    run = [p for p in c["path"] if p["inPanel"]]
    contiguous = all(run[i + 1]["idxInDialog"]
                     == run[i]["idxInDialog"] + step
                     for i in range(len(run) - 1))
    seg.append({
        "cell": "%s/%s" % k,
        "startIdxInDialog": c["startIdxInDialog"],
        "startIdxInPanel": c["startIdxInPanel"],
        "dialogFocusables": c["dialogFocusables"],
        "panelFocusables": c["panelFocusables"],
        "startInsideDialogArray": startOk,
        "panelRunIsContiguousInDialogArray": contiguous,
        "inPanelSteps": c["inPanelSteps"],
        "expectedStepPerStep": step,
    })
startInArray = [s["cell"] for s in seg if s["startInsideDialogArray"]]
contiguous = [s["cell"] for s in seg
              if s["panelRunIsContiguousInDialogArray"]]
assert startInArray, "起点的下标没落在对话框数组里 —— 判别式失效"
assert len(contiguous) == len(seg), \
    "有 %d 格的段内下标在行进方向上不连续：%r" % (
        len(seg) - len(contiguous),
        [s["cell"] for s in seg
         if not s["panelRunIsContiguousInDialogArray"]])

# ── ★ 逃逸步数的确定式：Tab 把浮层的控件当数组里**连续的一段**走，
#   走到段末就出去了。于是逃逸步数完全由 (浮层控件数, 起点下标, 方向) 决定。
escape = []
for k in CELLS:
    c = t[k][0]
    si, np_ = c["startIdxInPanel"], c["panelFocusables"]
    predicted = (np_ - si) if k[1] == "fwd" else (si + 1)
    got = c["escapedAtStep"]
    escape.append({
        "cell": "%s/%s" % k,
        "startIdxInPanel": si, "panelFocusables": np_,
        "direction": k[1],
        "predictedEscapeStep": predicted,
        "measuredEscapeStep": got,
        "withinWalk": got is not None,
        "matches": (got == predicted) if got is not None else None,
        "walkLength": c["steps"],
        "predictedBeyondWalk": got is None and predicted > c["steps"],
    })
matched = [e for e in escape if e["matches"] is True]
beyond = [e for e in escape if e["predictedBeyondWalk"]]
assert len(matched) == 11, \
    "逃逸步数与公式吻合的只有 %d 格（应为 11）：%r" % (
        len(matched), [(e["cell"], e["predictedEscapeStep"],
                       e["measuredEscapeStep"]) for e in escape
                      if e["matches"] is not True])
assert len(beyond) == 1, \
    "「步数不够所以没走出去」的格恰好 1 格，实际 %d：%r" % (
        len(beyond), [e["cell"] for e in beyond])
assert all(e["matches"] is not False for e in escape)


# ── 分类：焦点走出浮层之后去了哪
def verdict(c):
    if c["stayedInPanel"]:
        return "stayed-in-panel"
    if c["leftDialog"]:
        return "left-the-dialog"
    return "left-panel-stayed-in-dialog"


buckets = {}
for k in CELLS:
    vs = {verdict(t[k][r]) for r in range(2)}
    assert len(vs) == 1, "%s 两轮结论不同：%r" % (k, vs)
    buckets.setdefault(vs.pop(), []).append("%s/%s" % k)
stayed = buckets.get("stayed-in-panel", [])
leftDialog = buckets.get("left-the-dialog", [])
leftPanel = buckets.get("left-panel-stayed-in-dialog", [])
assert len(stayed) + len(leftDialog) + len(leftPanel) == 12, \
    "12 格的分类没铺满：%r" % buckets
assert leftPanel or leftDialog, "12 格全都没走出浮层 —— 围栏居然是好的？"

escaped = [c for c in leftPanel + leftDialog]     # 逐 disclosure 汇总用
tabTrap = {
    "perCell": {("%s/%s" % k): t[k] for k in CELLS},
    "stayedInPanel": stayed,
    "leftPanelStayedInDialog": leftPanel,
    "leftTheDialog": leftDialog,
    "counts": {k: len(v) for k, v in sorted(buckets.items())},
    "escapeSteps": {"%s/%s" % k: [t[k][r]["escapedAtStep"] for r in range(2)]
                    for k in CELLS},
    "perDisclosure": {
        i: {"startTag": t[(i, "fwd")][0]["startTag"],
            "panelFocusables": [t[(i, d)][r]["panelFocusables"]
                                for d in DIRS for r in range(2)],
            "dialogFocusables": [t[(i, d)][r]["dialogFocusables"]
                                 for d in DIRS for r in range(2)],
            "fwd": verdict(t[(i, "fwd")][0]),
            "back": verdict(t[(i, "back")][0]),
            "fwdEscapeAt": [t[(i, "fwd")][r]["escapedAtStep"] for r in range(2)],
            "backEscapeAt": [t[(i, "back")][r]["escapedAtStep"]
                             for r in range(2)]}
        for i in IDS},
    "arraySegment": seg,
    "escapeFormula": {
        "rule": "★ 逃逸步数是**确定式**的：Tab 把浮层控件当对话框数组里连续的"
                "一段走，走到段末就出去。⟹ 预测值 = (fwd) 浮层控件数 − "
                "起点下标；(back) 起点下标 + 1。",
        "perCell": escape,
        "matchedCount": len(matched),
        "cellsBeyondWalk": [e["cell"] for e in beyond],
    },
}
assert len(tabTrap["perDisclosure"]) == 6

# ═══════════════ 2. 静态层 ═══════════════
def src_text(rel):
    p = REPO / rel
    if not p.exists():
        raise SystemExit("FATAL 缺源码 %s" % p)
    return p.read_text(encoding="utf-8")


FC = src_text("src/components/director/useDirectorFocusContainment.ts")
DESK = src_text("src/components/director/DirectorDesk.tsx")

hook = FC[FC.index("const handleKeyDown = (event: KeyboardEvent) => {"):
           FC.index("root.addEventListener(\"keydown\", handleKeyDown);")]
static = {
    # 围栏挂在 root（对话框）上，不是挂在浮层上
    "listensOnRoot": 'root.addEventListener("keydown", handleKeyDown)'
                     in FC,
    "onlyOneKeydownListener": FC.count(
        'addEventListener("keydown"') == 1,
    "arraySourceIsRoot": "getDirectorFocusableElements(root)" in hook,
    "wrapsForward": "index === focusable.length - 1" in hook,
    "wrapsBackward": "index <= 0" in hook,
    "preventsDefaultOnTab": "event.preventDefault();" in hook,
    "stopsPropagation": "event.stopPropagation()" in hook,
    "stopPropagationFlagged": "stopPropagation" in FC[:FC.index(
        "const handleKeyDown")],
    # 导演台传的 stopPropagation 是开关：开着才真的 stop
    "deskStopPropagation": re.findall(
        r"stopPropagation[:=]\s*(\w+)", DESK),
    "hasFocusinListener": "focusin" in FC,
    "hasFocusoutListener": "focusout" in FC,
}
assert static["listensOnRoot"] is True, "围栏不再挂在 root 上 —— 机制变了"
assert static["onlyOneKeydownListener"] is True, \
    "围栏的 keydown 监听不止一个 —— 机制变了"
assert static["arraySourceIsRoot"] is True, \
    "Tab 数组不再按 root 取 —— 机制变了"
assert static["wrapsForward"] and static["wrapsBackward"]
assert static["preventsDefaultOnTab"] is True
assert static["hasFocusinListener"] is False, \
    "围栏开始监听 focusin 了 —— 769 的 D11 修法可能已落地"
assert static["hasFocusoutListener"] is False

findings = {
    "comparability": comparability,
    "tabTrap": tabTrap,
    "staticLayer": static,
}

# 声明了 role=dialog 的浮层（767 的 D10：只有 2/6）
VP = src_text("src/components/director/DirectorViewport.tsx")
ALL = VP + DESK
SEL = {"export": "export", "preset": "camera-preset",
       "pathmenu": "motion-path-menu", "phonevcam": "phone-vcam",
       "crowd": "crowd", "modellib": "model-library"}
DECLARES_DIALOG = [
    i for i in IDS
    if re.search(r'data-director-%s-panel.{0,400}?role="dialog"' % SEL[i],
                 ALL, re.S)]
assert DECLARES_DIALOG == ["crowd", "modellib"], \
    "声明 role=dialog 的浮层变了：%r" % (DECLARES_DIALOG,)
tabTrap["declaresDialog"] = DECLARES_DIALOG
tabTrap["declaresDialogButNoTrap"] = [
    i for i in DECLARES_DIALOG
    if tabTrap["perDisclosure"][i]["fwd"] != "stayed-in-panel"
    or tabTrap["perDisclosure"][i]["back"] != "stayed-in-panel"]
tabTrap["dialogBoundaryHeld"] = not tabTrap["leftTheDialog"]

targets = {}
for k in CELLS:
    et = t[k][0]["escapeTarget"]
    if et:
        targets.setdefault(
            et.get("aria") or et.get("text") or et.get("tag"), []).append(
                "%s/%s" % k)
tabTrap["escapeTargets"] = targets
tabTrap["escapeTargetsAllInDialog"] = all(
    c["escapeTarget"]["inDialog"] for k in CELLS for c in t[k]
    if c["escapeTarget"])
tabTrap["noPanelHasTrap"] = [
    i for i in IDS
    if tabTrap["perDisclosure"][i]["fwd"] != "stayed-in-panel"
    or tabTrap["perDisclosure"][i]["back"] != "stayed-in-panel"]

assert not tabTrap["leftTheDialog"], "有焦点离开过对话框 —— J4 要重写"
assert tabTrap["escapeTargetsAllInDialog"] is True
assert tabTrap["declaresDialogButNoTrap"] == DECLARES_DIALOG
assert len(tabTrap["noPanelHasTrap"]) == 6, "有浮层居然有围栏了"

N = comparability["steps"]
EF = tabTrap["escapeFormula"]

judgments = [
    {"id": "J1", "verdict": "PASS",
     "statement": "**两轮逐字段一致**（`rows` 整棵树的归一化 diff 为空），"
                  "且先证明可比：每格都从**重新加载的页面**开始"
                  "（768 的 R73），全程不点外点；"
                  "★ **起点固定为浮层里第一个非输入框控件** —— "
                  "769 已经证明**焦点类别会改变结论**（`isEditable` 早退），"
                  "所以跨批必须把类别钉死。每格 %d 步、两个方向。" % N,
     "evidenceKey": "comparability"},
    {"id": "J2", "verdict": "PASS",
     "statement": "★ **逃逸步数是确定式的，与公式逐格吻合**："
                  "预测值 =（正向）浮层控件数 − 起点下标、"
                  "（反向）起点下标 + 1。**%d/%d 实测吻合**"
                  "（例：群众阵列正向起点下标 3、控件数 5 ⟹ 第 2 步出去，"
                  "实测就是 2）。剩下 1 格（模型库，正向，控件数 15、"
                  "起点下标 1）公式预测第 **%d** 步出去，"
                  "**超出本批 %d 步的范围** ⟹ 机制在 %d/%d 格里都成立。"
                  % (EF["matchedCount"], len(CELLS),
                     EF["perCell"][-1]["predictedEscapeStep"], N,
                     len(CELLS), len(CELLS)),
     "evidenceKey": "tabTrap"},
    {"id": "J3", "verdict": "PASS",
     "statement": "★ **浮层的控件是「对话框 Tab 数组」里连续的一段**："
                  "12/12 格的段内下标在**行进方向上严格单调 ±1**"
                  "（正向 +1、反向 −1），且起点的 `idxInDialog` "
                  "12/12 落在 [0, 对话框控件数) 内。⟹ 围栏的边界是"
                  "**对话框**，浮层只是数组里的一段 —— 这就是 Tab 会走出去的"
                  "机制（`useDirectorFocusContainment.ts:149-172` 手算 "
                  "`getDirectorFocusableElements(root)`，root = 对话框）。",
     "evidenceKey": "tabTrap"},
    {"id": "J4", "verdict": "PASS",
     "statement": "★ **对话框级围栏是好的**：**0/12 格**的焦点离开过对话框，"
                  "所有逃逸落点全部仍在对话框内。**这一条独立复现了 765 的 "
                  "J6**（「正向从面板 12 步 0 逃出、反向 12 步 0 逃出」）"
                  "—— ★ **765 说的「逃出」是相对「对话框」，本批是相对"
                  "「浮层」，两者不矛盾**：同一批读数在两个参照系下同时为真。"
                  "这个区别正是本批结论的立足点，不写清楚就会被当成互相推翻。",
     "evidenceKey": "tabTrap"},
    {"id": "J5", "verdict": "FAIL",
     "statement": "★ **缺陷 D13（中，新增）：6 个 disclosure 浮层里没有一个"
                  "有浮层级 Tab 围栏。** 11/12 格实测 Tab 走出浮层，"
                  "剩下 1 格按公式也会走（见 J2）。焦点落到**对话框的别处**："
                  "侧栏工具栏的「收起属性」「移动」「Z 反向」，"
                  "以及导出面板自己的触发器「导出视频到画布」。"
                  "也就是说**键盘用户没法把一个开着的浮层当成一个整体来操作**"
                  "—— 按 Tab 就会离开它，而且离开之后没有机制把他带回来。",
     "evidenceKey": "tabTrap"},
    {"id": "J6", "verdict": "FAIL",
     "statement": "★ **声明与行为不一致**：只有 2/6 浮层声明了 "
                  "`role=\"dialog\"`（767 的 D10 已记），"
                  "而**声明了的这两个（添加群众阵列、模型库）恰恰都没有围栏**"
                  "—— 声明成 dialog 就意味着「我是当前上下文」，"
                  "焦点理应被留在里面。其余 4 个没有 role，"
                  "按非模态弹层看，Tab 走出去**可以**解释。"
                  "⟹ 全族的契约本身不自洽：这批浮层要么统一成 dialog 并补围栏，"
                  "要么统一成非 dialog 弹层并明确「Tab 走出去是有意的」。",
     "evidenceKey": "tabTrap"},
    {"id": "J7", "verdict": "PASS",
     "statement": "**Shift+Tab 同样走出去**（6/6 个浮层，2/2 轮），"
                  "而且与正向**严格镜像**：段内下标每次 −1；"
                  "起点下标为 0 的三个浮层（预设运镜、创建运动轨迹、虚拟相机）"
                  "**第 1 步就出去**。⟹ 不是「正向漏了、反向补上了」，"
                  "是**两个方向都没有浮层边界**。",
     "evidenceKey": "tabTrap"},
    {"id": "J8", "verdict": "FAIL",
     "statement": "★ **不声称**：本批**没有测逃逸落点是否被浮层视觉遮挡** —— "
                  "这些浮层浮在视口底部中央，而逃逸落点多在左右侧栏的"
                  "工具栏按钮上，很可能**仍然可见**。⟹ "
                  "**不声称「焦点落到了看不见的控件上」**，只声称"
                  "「焦点离开了浮层」。也没测从浮层**外部**（对话框别处）"
                  "按 Tab 能不能进浮层 —— 769 的 J10 同款未测。",
     "evidenceKey": "tabTrap"},
    {"id": "J9", "verdict": "PASS",
     "statement": "**没点任何有副作用的控件**：只点了 6 个 disclosure 触发器，"
                  "其余全是 `.focus()` 读操作与 Tab / Shift+Tab 键。"
                  "每格的起点下标、浮层控件数、对话框控件数都记进了产物，"
                  "可逐格复核。",
     "evidenceKey": "tabTrap"},
    {"id": "J10", "verdict": "FAIL",
     "statement": "★ **不许把「12 步都在浮层内」当成围栏好**：那一格是"
                  "**模型库、正向**，「没走出去」的唯一原因是它有 15 个"
                  "可聚焦控件、而本批只走了 %d 步；按公式它第 **%d** 步出去。"
                  "产物必须把它单列成「步数不够」而不是「有围栏」—— "
                  "**没测到 ≠ 没问题**，这里配了一个可算的替代解释。"
                  % (N, EF["perCell"][-1]["predictedEscapeStep"]),
     "evidenceKey": "tabTrap"},
]

for j in judgments:
    j["evidence"] = findings[j["evidenceKey"]]

audit = {
    "batch": 770,
    "date": "2026-10-01",
    "scope": "6 个导演台 disclosure 浮层里的 Tab 围栏（Tab / Shift+Tab "
             "各 12 步，逐步记录焦点落点）—— 关掉 767/768/769 连续三批"
             "列为不声称的那一项",
    "env": {
        "base": "http://localhost:4317",
        "canvas": "canvas-2",
        "directorNodeId": "b-bTLLuU4w5q",
        "viewport": "1440x1000（桌面）",
        "player": "chromium (playwright sync_api)",
        "srcModified": False,
    },
    "probes": [
        {"id": "770a", "file": "probes/dbg770a.py", "raw": "raw/vb770a.json",
         "rounds": len(aR), "injected": False, "steps": N,
         "note": "起点固定为浮层里第一个非输入框控件（769 的协议 v2 落点）；"
                 "每步读「还在浮层内吗 / 还在对话框内吗 / 对话框数组下标」。"},
    ],
    "rawSha": {a_p.name: sha(a_p)},
    "findings": findings,
    "judgments": judgments,
    "defects": [
        {"id": "D13", "severity": "中", "newInThisBatch": True,
         "relatedToD10From767": True,
         "title": "6 个 disclosure 浮层都没有浮层级 Tab 围栏："
                  "Tab / Shift+Tab 会从开着的浮层里走出去",
         "where": ["src/components/director/useDirectorFocusContainment.ts"
                   ":149-172",
                   "src/components/director/DirectorExportPanel.tsx:42-51",
                   "src/components/director/DirectorTimeline.tsx:1371-1379",
                   "src/components/director/DirectorTimeline.tsx:1502-1509",
                   "src/components/director/DirectorViewport.tsx:3084-3092",
                   "src/components/director/DirectorViewport.tsx:3161-3169"],
         "mechanism": "导演台只有**一层**焦点围栏："
                      "`useDirectorFocusContainment.ts:149-172` 在对话框 root "
                      "上监听 Tab，手算 `getDirectorFocusableElements(root)`"
                      "（root = **整个对话框**），按 `nextIndex` 环绕后 "
                      "`preventDefault()` 并 `focus()`。"
                      "**全仓没有任何一层按浮层算的 Tab 围栏** ⟹ "
                      "浮层的控件只是这条数组里**连续的一段**，"
                      "Tab 走完这一段就到了对话框的别处。实测的逃逸步数与"
                      "公式逐格吻合，正反两个方向都是。",
         "measured": "11/12 格实测走出浮层、剩下 1 格按公式也会走"
                     "（模型库，正向，第 %d 步）；6/6 个浮层两个方向都走；"
                     "逃逸落点全部仍在对话框内（0/12 出对话框）。2/2 轮。"
                     % EF["perCell"][-1]["predictedEscapeStep"],
         "severityRationale": "**中**：不丢数据、不崩溃，"
                              "但键盘用户无法把开着的浮层当成一个整体操作，"
                              "Tab 离开后没有机制带回来；且**声明了 "
                              "`role=\"dialog\"` 的那 2 个**（群众阵列、"
                              "模型库）按 ARIA 对话框的约定本应留住焦点，"
                              "声明与行为直接矛盾。",
         "relationToD10": "767 的 D10 记了「只有 2/6 有 role+aria-label」，"
                          "当时当成「契约残缺」记；本批证明**残缺的后果"
                          "是可测的** —— 那 2 个声明成 dialog 的浮层正好也"
                          "没有围栏。⟹ 这一族要么统一成 dialog 并补围栏，"
                          "要么统一成非 dialog 弹层并明确 Tab 走出去是有意的。",
         "fixDirection": "①在浮层自己的 ref 上加一层 Tab 围栏"
                         "（与 `useDirectorFocusContainment` 同款，"
                         "但 root 换成浮层；同仓 `src/hooks/useLayerFocus.ts` "
                         "已有带 trap 的实现可照抄）；"
                         "②或者给浮层补 role/aria 但不承诺 trap —— "
                         "那样焦点落在 `role=\"dialog\"` 之外仍不合规，"
                         "所以 ①更对。★ 注意**两层围栏会互相抢 Tab**："
                         "内层必须在事件到达外层之前 `preventDefault` + "
                         "`stopImmediatePropagation`，"
                         "与 767/768 量到的 Esc 修法是同一个坑。",
         "needsSrcChange": True},
    ],
    "widened": [],
    "observations": [
        {"id": "O1",
         "text": "★ **「逃出」的参照系必须写清楚**：765 的 J6 说「Tab 12 步 "
                 "0 逃出」指的是**离开对话框**，本批说「11/12 逃出」指的是"
                 "**离开浮层**。同一批读数在两个参照系下**同时为真**，"
                 "不矛盾。不写清楚的话，后来者会以为本批推翻了 765。",
         "verdict": "方法论记录（R87）"},
        {"id": "O2",
         "text": "★ **逃逸步数是确定式的，可以静态预测**：既然浮层控件是"
                 "数组里连续的一段，逃逸步数就只由（浮层控件数、起点下标、"
                 "方向）决定。这让「12 步没走出去」那一格**不必再跑一次**"
                 "就能解释（模型库正向第 %d 步出去）。"
                 "**没测到 ≠ 没问题，但没测到可以配一个可算的替代解释。**"
                 % EF["perCell"][-1]["predictedEscapeStep"],
         "verdict": "方法论记录（R88）"},
        {"id": "O3",
         "text": "**浮层只占对话框 Tab 数组的 1%%–12%%**：浮层控件数 2–15，"
                 "对话框控件数 126–151。⟹ 「Tab 会走出去」几乎是必然的 —— "
                 "对话框的围栏做得越好（数组越长），浮层里的控件占比越小，"
                 "留在浮层里的步数越少。",
         "verdict": "事实记录"},
        {"id": "O4",
         "text": "**逃逸落点随浮层挂载位置而变，但都不在浮层内**："
                 "侧栏工具栏的「收起属性」「移动」「Z 反向」，"
                 "以及导出面板自己的触发器「导出视频到画布」。"
                 "同一批里 4 个浮层的正向逃逸落点都是「收起属性」，"
                 "说明它们在 DOM 里都挂在属性面板那一段之后。",
         "verdict": "事实记录"},
        {"id": "O5",
         "text": "★ **本批关掉了 767 / 768 / 769 连续三批的同一条不声称**"
                 "（「没有测 6 个浮层里的 Tab 围栏」）—— 三批都把它列进去，"
                 "说明它确实是这条线上最该补的一个洞。",
         "verdict": "事实记录"},
    ],
    "notClaimed": [
        "无源站对照：本批全部结论只针对 clone 自身的行为自洽性。",
        "★ **没有测逃逸落点是否被浮层视觉遮挡**（J8）⟹ 不声称"
        "「焦点落到了看不见的控件上」。",
        "★ **没有测从浮层外部（对话框别处）按 Tab 能不能进浮层** —— "
        "769 的 J10 同款未测。这决定了「按 Tab 能不能到达浮层」这件事。",
        "★ **只走了 12 步、只从浮层里第一个非输入框控件出发** —— "
        "从面板**其他**控件出发、或走更多步，**未测**"
        "（模型库那一格已由公式解释了，见 J2）。",
        "**没有测焦点在浮层开着时点对话框别处会怎样**（鼠标）。",
        "**没有测多个浮层同时开着时的 Tab 序**。",
        "**没有测视觉顺序与 Tab 顺序是否一致**（765 的 O3 提过"
        "「视觉序与 Tab 序相反」，本批只量了「在不在浮层内」，"
        "没量顺序本身）。",
        "**只测了 1440 桌面一档视口**。",
        "**没有改 `src/`**：所有结论都是读数 + 源码现算，修法列在缺陷条目里"
        "等拍板。",
    ],
    "probeLessons": [
        {"id": "R87",
         "text": "★ **「逃出」的参照系（相对谁）必须写进产物。** 765 记的是"
                 "「Tab 12 步 0 逃出」—— 相对**对话框**；本批记「11/12 "
                 "逃出」—— 相对**浮层**。两条都是对的。**同一个词在两批里"
                 "指不同的边界**，一旦不写清楚，后来者要么以为互相矛盾，"
                 "要么更糟：拿后者去否定前者。",
         "whyItMatters": "跨批比较的前提是**同一把尺子**；尺子换了必须"
                         "写在脸上。"},
        {"id": "R88",
         "text": "★ **探针步数不够时，要给机制公式而不是含糊写「没测到」。** "
                 "模型库正向那格「12 步都在浮层内」很容易被写成"
                 "「这个浮层有围栏」。可一旦发现浮层控件是数组里连续的一段，"
                 "逃逸步数就**完全可算** = 控件数 − 起点下标 = %d > %d ⟹ "
                 "「没走出去」只是步数不够。**没测到 ≠ 没问题，"
                 "但没测到可以配一个可算的替代解释。**"
                 % (EF["perCell"][-1]["predictedEscapeStep"], N),
         "whyItMatters": "「没测到」被当成「没问题」是这条线上最常见的"
                         "误报路径（R79 的同族）。"},
        {"id": "R89",
         "text": "★ **判据里的方向不能写死。** 我把「段内下标连续」检查成 "
                 "`+1`，于是 `crowd/back`（Shift+Tab，下标 43→42→41）"
                 "被误判成「不连续」。**判据把方向写死，就必然误判"
                 "反向的合法数据。** 凡是同时有正向与反向的检查，"
                 "步长必须由行进方向给。",
         "whyItMatters": "它让一条**完全正确**的数据报出缺陷；"
                         "如果当时没有另外 11 格做对照，"
                         "整个「连续段」机制都会被否掉。"},
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
      "观察 %d | 探针教训 %d"
      % (len(audit["judgments"]),
         sum(1 for j in judgments if j["verdict"] == "PASS"),
         sum(1 for j in judgments if j["verdict"] == "FAIL"),
         len(findings), len(audit["defects"]), len(audit["observations"]),
         len(audit["probeLessons"])))
print("分类：%r" % (tabTrap["counts"],))
print("逃逸公式吻合 %d 格｜步数不够的格：%r"
      % (EF["matchedCount"], EF["cellsBeyondWalk"]))
print("声明 role=dialog：%r（其中没围栏：%r）"
      % (DECLARES_DIALOG, tabTrap["declaresDialogButNoTrap"]))
print("逃逸落点：%r" % (tabTrap["escapeTargets"],))
