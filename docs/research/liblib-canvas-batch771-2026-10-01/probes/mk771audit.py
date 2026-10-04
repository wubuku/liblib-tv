#!/usr/bin/env python3
"""batch 771 汇编器：从 raw/vb771a.json 现算 runtime-audit.json

本批问的是 770 留的同一条线上的另外三问，外加**一条对前批措辞的更正**：

  ① **可达性**（770 的 J8 盲区）：从浮层**外部**按 Tab 能不能进浮层？
  ② **可修性**（D13 修法方向 ①）：注入一层浮层级 Tab 围栏之后，
     770 量到的逃逸**会不会停止**？
  ③ **照抄够不够**（本批的新问）：768 的 D11 修法引用与 770 的 D13
     `fixDirection` 都写着「`useLayerFocus.ts` 已有带 trap 的实现可照抄」。
     逐字读那份源码发现它**没有 `stopImmediatePropagation()`**。问 ③ 就是
     问：只把那句话补上够不够？

关键推理（写在产物里，不藏）：

  * ①的前提来自 770：Tab 在对话框数组上是 `index ± 1` 的**线性行走**并环绕，
    浮层的控件是数组里**连续的一段** ⟹ **可达性完全由数组位置决定**。
    所以臂 1/2 只需从紧邻前/后起步（各 3 步），不必走 150 步。
  * ③的前提**必须现读源码**：对话框那一层对**每一次** Tab 都
    `preventDefault()` 并 `focus(nextIndex)`（不是只在环绕时干预），
    而注入那一层在**捕获**阶段、排在它前面。于是「不���传播」的臂 4 里，
    **两个处理器都会动手**，焦点会走两跳。逃逸步数因此**完全可算** ⟹
    本批用一份独立写的模拟器逐格预测，再与实测对。

规矩（沿用 756–770）：
1. **数字不许手抄** —— 每个数从 raw 现算；静态事实当场读源码数出来。
2. **缺原始读数判失败**。
3. **`findings[k] == judgments[i].evidence`**，写盘前断言，验收器再查一遍。
4. **先证明可比再谈一致**（R55）：逐轮归一化 diff。
5. **`all([])` 是 True**：每处聚合显式判非空；分类必须**铺满**格子。
6. **注入臂的读数只在「注入真的拦住了」时才算数**：要先验注入的
   `trapFired > 0` 与 `panelCount > 0`，否则「没逃逸」可能只是
   「浮层里一个可聚焦控件都没有」这种退化情况。
7. **静态断言的方向要写对**（R92）：把「我期望它是 True」写成
   `assert X is True`，一旦事实相反就变成**脚本崩**，而不是一条
   写进产物的**更正**。本批的那条正是如此。
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
REACH = ["reach-fwd", "reach-back"]
TRAP = "trap-fwd"
ARM4 = "trapnostop-fwd"
CELLS = ([(i, a) for i in IDS for a in REACH]
         + [(i, TRAP) for i in IDS] + [(i, ARM4) for i in IDS])
REACH_CELLS = [(i, a) for i in IDS for a in REACH]
TRAP_CELLS = [(i, TRAP) for i in IDS]
ARM4_CELLS = [(i, ARM4) for i in IDS]
PREV = BATCH.parent / "liblib-canvas-batch770-2026-10-01"


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
a, a_p = load("vb771a.json")
aR = a["rounds"]
assert len(aR) == 2, "轮数 %d" % len(aR)

comparability = {
    "allConsistent": round_diff(a, "rows")[0] is True,
    "firstDiff": {} if round_diff(a, "rows")[0] is True
                  else {"rows": round_diff(a, "rows")[1]},
    "rounds": len(aR),
    "protocol": "★ 每格都从**重新加载的页面**开始（768 的 R73），"
                "全程不点外点；只点 6 个 disclosure 触发器。"
                "24 格 × 2 轮。",
    "armA": None, "armB": None, "armC": None, "armD": None,
    "inference": "★ **为什么臂 1/2 只走 3 步就够**：770 已证明 Tab 在对话框"
                 "数组上是 `index ± 1` 的**线性行走**并环绕，浮层的控件是"
                 "数组里**连续的一段** ⟹ 可达性完全由数组位置决定。"
                 "只要「紧邻浮层之前」的元素能走进去，任何排在浮层之前的"
                 "元素都能走进去。**这条推理的前提由 770 的读数提供，"
                 "本批不重新证明，只在 J 里引用。**",
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

walks = {k: ((v[0].get("walk") or {}).get("steps")) for k, v in g.items()}
reachSteps = {walks[k] for k in REACH_CELLS}
trapSteps = {walks[k] for k in TRAP_CELLS + ARM4_CELLS}
assert len(reachSteps) == 1 and len(trapSteps) == 1, \
    "各臂步数不一致：%r / %r" % (sorted(reachSteps), sorted(trapSteps))
REACH_N = reachSteps.pop()
WALK_N = trapSteps.pop()
comparability["armA"] = {"arm": REACH[0], "steps": REACH_N,
                         "key": "Tab"}
comparability["armB"] = {"arm": REACH[1], "steps": REACH_N,
                         "key": "Shift+Tab"}
comparability["armC"] = {"arm": TRAP, "steps": WALK_N, "key": "Tab",
                         "injected": True, "stopsImmediate": True,
                         "note": "与 770 的 */fwd 同一协议 ⟹ D13 的 A/B 对照"}
comparability["armD"] = {"arm": ARM4, "steps": WALK_N, "key": "Tab",
                         "injected": True, "stopsImmediate": False,
                         "note": "★ 与臂 C **逐字相同，只少一句 "
                                 "`stopImmediatePropagation()`** ⟹ 语义就是"
                                 "「照抄 useLayerFocus 的 trap」。"}


def cell(r):
    st = r.get("start") or {}
    rg = r.get("range") or {}
    fo = r.get("focus") or {}
    path = [{"step": s.get("step"),
             "inPanel": s.get("inPanel") is True,
             "inDialog": s.get("inDialog") is True,
             "tag": s.get("tag"), "type": s.get("type"),
             "aria": s.get("aria"),
             "text": s.get("text"),
             "idxInDialog": s.get("idxInDialog"),
             "idxInPanel": s.get("idxInPanel")}
            for s in (r.get("steps") or [])]
    enter = next((p["step"] for p in path if p["inPanel"]), None)
    leave = next((p["step"] for p in path if not p["inPanel"]), None)
    return {
        "startTag": st.get("tag"),
        "startIdxInDialog": st.get("idxInDialog"),
        "startIdxInPanel": st.get("idxInPanel"),
        "startInPanel": st.get("inPanel") is True,
        "focusedByIndex": fo.get("focused") is True,
        "focusedIndex": fo.get("idx"),
        "range": {"panelStart": rg.get("panelStart"),
                  "panelEnd": rg.get("panelEnd"),
                  "panelCount": rg.get("panelCount"),
                  "dialogCount": rg.get("dialogCount"),
                  "contiguous": rg.get("contiguous")},
        "path": path,
        "steps": len(path),
        "enteredAtStep": enter,
        "leftAtStep": leave,
        "injSetup": r.get("injSetup"),
        "trapFired": r.get("trapFired"),
    }


t = {k: [cell(r) for r in g[k]] for k in g}

# ── 起点纪律
for k in REACH_CELLS:
    for c in t[k]:
        rg = c["range"]
        assert c["focusedByIndex"] is True, "%s 没能按数组下标聚焦" % (k,)
        assert c["startInPanel"] is False, \
            "%s 起点落在浮层内 —— 这一格答的不是「从外部」" % (k,)
        assert c["startIdxInDialog"] is not None, "%s 起点下标缺失" % (k,)
        assert rg["panelStart"] is not None and rg["panelEnd"] is not None, \
            "%s 读不到浮层在数组里的区间" % (k,)
        assert rg["panelCount"] and rg["dialogCount"], "%s 存量读数为 0" % (k,)
        assert rg["panelCount"] <= rg["dialogCount"], "%s 存量反常" % (k,)
        assert rg["contiguous"] is True, \
            "%s 浮层在数组里**不连续** —— 770 的推理前提没了" % (k,)
        # 起点必须**紧邻**浮层（这就是「3 步够」的前提）
        if k[1] == REACH[0]:
            assert c["startIdxInDialog"] == rg["panelStart"] - 1 or (
                rg["panelStart"] == 0
                and c["startIdxInDialog"] == rg["dialogCount"] - 1), \
                "%s 起点不紧邻浮层之前（起点 %s，浮层起 %s）" % (
                    k, c["startIdxInDialog"], rg["panelStart"])
        else:
            assert c["startIdxInDialog"] == rg["panelEnd"] + 1 or (
                rg["panelEnd"] + 1 >= rg["dialogCount"]
                and c["startIdxInDialog"] == 0), \
                "%s 起点不紧邻浮层之后（起点 %s，浮层止 %s）" % (
                    k, c["startIdxInDialog"], rg["panelEnd"])
        assert len(c["path"]) == REACH_N, "%s 步数不符" % (k,)

for _mode, _wantStop in ((TRAP, True), (ARM4, False)):
    for _i in IDS:
        k = (_i, _mode)
        for c in t[k]:
            assert c["injSetup"] and not c["injSetup"].get("err"), \
                "%s 注入没装上" % (k,)
            assert c["injSetup"].get("installed") is True, \
                "%s 注入未标记装上" % (k,)
            assert c["injSetup"].get("stopsImmediate") is _wantStop, \
                "%s 注入的 stopsImmediate=%r，期望 %r —— 单变量没守住" % (
                    k, c["injSetup"].get("stopsImmediate"), _wantStop)
            assert c["injSetup"].get("panelCount"), \
                "%s 注入看到的浮层控件数为 0" % (k,)
            assert c["startInPanel"] is True, "%s 起点不在浮层内" % (k,)
            assert len(c["path"]) == WALK_N, "%s 步数不符" % (k,)

# ═══════════════ 2. 问① 可达性 ═══════════════
reach = {}
for k in REACH_CELLS:
    ins = {c["enteredAtStep"] for c in t[k]}
    assert len(ins) == 1, "%s 两轮结论不同：%r" % (k, ins)
    reach["%s/%s" % k] = {
        "enteredAtStep": ins.pop(),
        "reached": t[k][0]["enteredAtStep"] is not None,
        "range": t[k][0]["range"],
        "startIdxInDialog": t[k][0]["startIdxInDialog"],
        "path": [p for c in t[k] for p in c["path"]],
    }
reached = [c for c, v in reach.items() if v["reached"]]
notReached = [c for c, v in reach.items() if not v["reached"]]
assert reached, "一格都没进浮层 —— 判别式坏了"
reachability = {
    "perCell": reach,
    "reachedPanel": reached,
    "neverReached": notReached,
    "reachedCount": len(reached),
    "totalCells": len(reach),
    "fwdReached": [c for c in reached if c.endswith("/" + REACH[0])],
    "backReached": [c for c in reached if c.endswith("/" + REACH[1])],
    "enterStepIsOne": all(reach[c]["enteredAtStep"] == 1 for c in reached),
    "perDisclosure": {
        i: {"fwd": reach["%s/%s" % (i, REACH[0])]["reached"],
            "back": reach["%s/%s" % (i, REACH[1])]["reached"],
            "fwdEnterAt": reach["%s/%s" % (i, REACH[0])]["enteredAtStep"],
            "backEnterAt": reach["%s/%s" % (i, REACH[1])]["enteredAtStep"],
            "panelStart": reach["%s/%s" % (i, REACH[0])]["range"]["panelStart"],
            "panelEnd": reach["%s/%s" % (i, REACH[0])]["range"]["panelEnd"],
            "dialogCount": reach["%s/%s" % (i, REACH[0])]["range"]["dialogCount"]}
        for i in IDS},
}
# 落点下标必须正好落在浮层的首/末位 —— 这才是「进浮层」而不是「路过」
landOK = {}
for i in IDS:
    rg = reach["%s/%s" % (i, REACH[0])]["range"]
    landOK[i] = {
        "fwdLandsOnPanelStart":
            reach["%s/%s" % (i, REACH[0])]["path"][0]["idxInDialog"]
            == rg["panelStart"],
        "backLandsOnPanelEnd":
            reach["%s/%s" % (i, REACH[1])]["path"][0]["idxInDialog"]
            == rg["panelEnd"],
    }
    assert landOK[i]["fwdLandsOnPanelStart"] is True, \
        "%s 正向第 1 步落点不是浮层首控件" % (i,)
    assert landOK[i]["backLandsOnPanelEnd"] is True, \
        "%s 反向第 1 步落点不是浮层末控件" % (i,)
reachability["landing"] = landOK
reachability["landingAllOK"] = all(
    v["fwdLandsOnPanelStart"] and v["backLandsOnPanelEnd"]
    for v in landOK.values())

# ═══════════════ 3. 问② 可修性（臂 3：停传播） ═══════════════
trap = {}
for k in TRAP_CELLS:
    leaves = {c["leftAtStep"] for c in t[k]}
    fires = {c["trapFired"] for c in t[k]}
    assert len(leaves) == 1, "%s 两轮逃逸读数不同：%r" % (k, leaves)
    assert all(f is not None and f > 0 for f in fires), \
        "%s 注入的围栏一次都没拦到 Tab —— 「没逃逸」不算数（R76 的纪律）" % (k,)
    trap["%s/%s" % k] = {
        "leftAtStep": leaves.pop(),
        "stayedInPanel": t[k][0]["leftAtStep"] is None,
        "escapeStopped": t[k][0]["leftAtStep"] is None,
        "trapFired": sorted(fires),
        "steps": t[k][0]["steps"],
        "panelCount": t[k][0]["injSetup"]["panelCount"],
    }
assert all(v["escapeStopped"] for v in trap.values()), \
    "有格注入后仍然逃逸：%r" % ([k for k, v in trap.items()
                                if not v["escapeStopped"]],)
trappability = {
    "perCell": trap,
    "escapeStopped": [k for k, v in trap.items() if v["escapeStopped"]],
    "stillEscaped": [k for k, v in trap.items() if not v["escapeStopped"]],
    "trapFiredPerCell": {k: v["trapFired"] for k, v in trap.items()},
    "note": "★ 注入 = D13 修法方向 ① 的原样实现：挂在**浮层自己的 ref** 上、"
            "**捕获**阶段、算浮层自己的数组、环绕后 `preventDefault()` + "
            "`stopImmediatePropagation()`。",
    "perDisclosure": {i: {"escapeStopped":
                          trap["%s/%s" % (i, TRAP)]["escapeStopped"],
                          "trapFired": trap["%s/%s" % (i, TRAP)]["trapFired"],
                          "steps": trap["%s/%s" % (i, TRAP)]["steps"],
                          "panelCount": trap["%s/%s" % (i, TRAP)]["panelCount"]}
                      for i in IDS},
}
assert len(trappability["escapeStopped"]) == 6, \
    "注入拦住的格数不对：%d" % len(trappability["escapeStopped"])

# ── 跨批对照：臂 3 vs 770 的 */fwd。
prev, prev_p = load("vb770a.json", base=PREV / "raw")
pg_ = {}
for rd in prev["rounds"]:
    for r in rd.get("rows") or []:
        pg_.setdefault((r.get("id"), r.get("mode")), []).append(r)


def sig(steps):
    """落点签名 = (tag, type, text)。**不能只取 (tag,type)** ——
    preset/pathmenu 的首末控件都是无文字的 BUTTON，按 tag 分不开。"""
    return [(s.get("tag"), s.get("type"), s.get("text"))
            for s in (steps or [])]


#    ★ 注意这两臂**不是同一协议**：770 那格没有注入，771 这格有。
#    所以「落点序列相同」本来就不该成立（也不成立）—— 真正可比的是
#    **前缀**：注入生效之前，两者必须逐步**完全一致**；
#    分歧必须恰好出现在 770 会逃逸的那一步。这比「序列相同」强得多。
equiv = {}
for i in IDS:
    old = pg_.get((i, "fwd")) or []
    assert old, "770 缺 (%s,fwd) 那一格 —— 没法做前缀对照" % i
    oldSteps = old[0].get("steps") or []
    newSteps = t[(i, TRAP)][0]["path"]
    rg = reach["%s/%s" % (i, REACH[0])]["range"]        # 现读，不手抄
    pS, pE, pn = rg["panelStart"], rg["panelEnd"], rg["panelCount"]
    sIdx = t[(i, TRAP)][0]["startIdxInDialog"]
    # 770 无围栏时，能在浮层内走的步数 = 末位 − 起点（第 inside+1 步必然出去）
    inside = pE - sIdx
    oldEscape = next((s.get("step") for s in oldSteps
                      if s.get("inPanel") is not True), None)
    # 771 注入臂：应当正好按**浮层自己**的数组走并环绕
    expect771 = [pS + ((sIdx - pS + k + 1) % pn) for k in range(WALK_N)]
    actual771 = [p.get("idxInDialog") for p in newSteps]
    insideAgree = all(
        (oldSteps[k].get("idxInDialog") == actual771[k])
        for k in range(min(inside, len(oldSteps), WALK_N)))
    equiv[i] = {
        "oldRounds": len(old),
        "panelRange": [pS, pE], "panelCount": pn,
        "startIdxInDialog": sIdx,
        "oldEscapeStep": oldEscape,
        "stepsInsidePanelBeforeEscape": inside,
        "agreesForAllInsideSteps": insideAgree,
        "oldEscapeEqualsInsidePlusOne": oldEscape == inside + 1
                                        if oldEscape is not None else None,
        "injectedWalkIsPanelOwnArray": actual771 == expect771,
        "firstDivergentStep": inside + 1 if inside < WALK_N else None,
        "newEscapeStep": t[(i, TRAP)][0]["leftAtStep"],
        "startIdxInDialogSame":
            (old[0].get("start") or {}).get("idxInDialog") == sIdx,
        "startIdxInPanelSame":
            (old[0].get("start") or {}).get("idxInPanel")
            == t[(i, TRAP)][0]["startIdxInPanel"],
        "tookEffectAtOldEscapeStep":
            (oldEscape == inside + 1) if oldEscape is not None
            else (inside >= WALK_N),
    }
_esc = [v["oldEscapeStep"] for v in equiv.values() if v["oldEscapeStep"]]
trappability["crossBatchPrefix"] = {
    "comparedWith": "batch 770 的 */fwd（**无注入**的那两臂）",
    "whyNotEqualSequences": "两臂的处理变量不同（770 没有围栏），"
                            "所以「落点序列相同」本来就不该成立；"
                            "可比的是**分歧点**。",
    "howCompared": "★ 按**下标算术**比，不按 (tag,type) —— preset/pathmenu "
                   "的首末控件都是无文字 BUTTON，按标签分不开（先踩过）。",
    "perCell": equiv,
    "allPaired": sorted(equiv) == sorted(IDS),
    "allStartSame": all(v["startIdxInDialogSame"] and v["startIdxInPanelSame"]
                        for v in equiv.values()),
    "allAgreesInsideThenDiverges":
        all(v["agreesForAllInsideSteps"] and v["tookEffectAtOldEscapeStep"]
            for v in equiv.values()),
    "allInjectedWalkIsPanelOwnArray":
        all(v["injectedWalkIsPanelOwnArray"] for v in equiv.values()),
    "cellsWhere770Escaped": len(_esc),
    "cellsWhere770StayedAllWalk": len(IDS) - len(_esc),
}
assert trappability["crossBatchPrefix"]["allPaired"] is True
assert trappability["crossBatchPrefix"]["allAgreesInsideThenDiverges"] \
    is True, "注入不是在 770 会逃逸的那一步才生效 —— 要重查机制"
assert trappability["crossBatchPrefix"][
    "allInjectedWalkIsPanelOwnArray"] is True, \
    "注入臂走的不是浮层自己的数组 —— 机制要重查"

# ═══════════════ 4. 问③ 照抄够不够（臂 4：不停传播） ═══════════════
def sim_arm4(pS, n, D, s, steps):
    """照源码逐行模拟臂 4 的一步，返回每步之后的**面板内局部下标**（None=逃出）。

    一步里有两个处理器都会动手，**且都在 preventDefault**：
      1) 注入（浮层 ref、捕获阶段）：面板内取下一个并环绕；
      2) 对话框 root（冒泡阶段）：对话���数组里 +1 并环绕，
         —— `useDirectorFocusContainment.ts:169/171` 对**每次** Tab 都
            preventDefault 并 focus(nextIndex)，**不是只在环绕时干预**。
    因为浮层是数组里连续的一段 ⟹ 局部下标 +1 就是数组下标 +1。
    """
    out, i = [], s
    for _ in range(steps):
        j = i + 1 if i >= 0 else 0
        if j >= n:
            j = 0                       # ① 面板内环绕
        d = pS + j + 1                   # ② 对话框数组 +1 并环绕
        if d >= D:
            d = 0
        i = d - pS
        out.append(i if 0 <= i < n else None)
    return out


arm4 = {}
for k in ARM4_CELLS:
    rg = t[k][0]["range"]
    assert rg["panelStart"] is not None and rg["contiguous"] is True, \
        "%s 臂 4 读不到浮层区间" % (k,)
    pS, n, D = rg["panelStart"], rg["panelCount"], rg["dialogCount"]
    s = t[k][0]["startIdxInPanel"]
    assert s is not None and 0 <= s < n, "%s 臂 4 起点局部下标异常 %r" % (k, s)
    sim = sim_arm4(pS, n, D, s, WALK_N)
    pred = next((i + 1 for i, v in enumerate(sim) if v is None), None)
    leaves = {c["leftAtStep"] for c in t[k]}
    fires = {c["trapFired"] for c in t[k]}
    assert len(leaves) == 1, "%s 两轮逃逸读数不同：%r" % (k, leaves)
    assert all(f is not None and f > 0 for f in fires), \
        "%s 臂 4 的注入一次都没拦到 Tab —— 读数不算数" % (k,)
    arm4["%s/%s" % k] = {
        "measuredEscapeStep": leaves.pop(),
        "predictedEscapeStep": pred,
        "predictionMatched": (next(iter({c["leftAtStep"] for c in t[k]}))
                               == pred),
        "landings": [p["idxInPanel"] for p in t[k][0]["path"]],
        "simulated": sim,
        "startLocalIdx": s, "panelCount": n, "panelStart": pS,
        "dialogCount": D,
        "trapFired": sorted(fires),
    }
    assert arm4["%s/%s" % k]["predictionMatched"] is True, \
        "%s 臂 4 实测逃逸步 %r ≠ 模拟预测 %r —— 机制读错了，要重查" % (
            k, arm4["%s/%s" % k]["measuredEscapeStep"], pred)
assert all(v["predictedEscapeStep"] is not None for v in arm4.values()), \
    "有格模拟器预测「不逃逸」—— 与「两个处理器都在动手」矛盾"
copyVerdict = {
    "perCell": arm4,
    "stillEscaped": [k for k, v in arm4.items()
                     if v["measuredEscapeStep"] is not None],
    "neverEscaped": [k for k, v in arm4.items()
                     if v["measuredEscapeStep"] is None],
    "allPredictedMatched": all(v["predictionMatched"] for v in arm4.values()),
    "escapeSteps": {k: v["measuredEscapeStep"] for k, v in arm4.items()},
    "question": "★ 「照抄 useLayerFocus 的 trap」够不够？",
    "answer": "不够。停传播的臂 3 6/6 格 %d 步都没走出浮层；"
              "只去掉那一句的臂 4 **6/6 格全部照旧逃逸**，"
              "且逃逸步数与独立模拟器逐格吻合。"
              "⟹ `stopImmediatePropagation()` 不是锦上添花，"
              "是那层围栏在本上下文里唯一起作用的那一句。",
    "why": "useLayerFocus 的 trap 挂在 **window 捕获**上、"
           "而导演台的对话��围栏挂在 **root 冒泡**上；`preventDefault()` "
           "**不阻止其他监听器** ⟹ 冒泡到 root 的那一次 Tab 仍会被它"
           "自己的 `preventDefault()` + `focus()` 接管，"
           "把焦点从浮层里拽走。",
}

# ═══════════════ 5. 静态层 ═══════════════
def src_text(rel):
    p = REPO / rel
    if not p.exists():
        raise SystemExit("FATAL 缺源码 %s" % p)
    return p.read_text(encoding="utf-8")


FC = src_text("src/components/director/useDirectorFocusContainment.ts")
LF = src_text("src/hooks/useLayerFocus.ts")
hook = FC[FC.index("const handleKeyDown = (event: KeyboardEvent) => {"):
           FC.index('root.addEventListener("keydown", handleKeyDown);')]
lfTrap = LF[LF.index("const onKey = (e: KeyboardEvent) => {"):
            LF.index('window.addEventListener("keydown", onKey, true);')]


def consumers(hook_name):
    """全仓 import 了这个 hook 的文件（现读，不手抄）。"""
    out = []
    for p in sorted((REPO / "src").rglob("*.ts*")):
        if p.name == hook_name + ".ts":
            continue
        try:
            t_ = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if re.search(r"import[^;]*\b%s\b" % hook_name, t_):
            out.append(str(p.relative_to(REPO)))
    return out


static = {
    # 现状：只有一层围栏、挂在对话框 root 上
    "existingTrapOnRoot": 'root.addEventListener("keydown", handleKeyDown)'
                          in FC,
    "existingTrapCapture": 'root.addEventListener("keydown", handleKeyDown,'
                           " true)" in FC,
    "existingKeydownCount": FC.count('addEventListener("keydown"'),
    "existingArrayIsRoot": "getDirectorFocusableElements(root)" in hook,
    "existingStopsPropagation": "event.stopPropagation()" in hook,
    # 关键：root 那一层是**每次 Tab 都**接管，不是只在环绕时
    "rootPreventDefaultCount": hook.count("event.preventDefault()"),
    "rootFocusesNextEveryTime": bool(
        re.search(r"event\.preventDefault\(\);.*?focusable\[nextIndex\]"
                  r"\?\.focus\(", hook, re.S)),
    "rootNextIndexUnconditional":
        re.search(r"if \(nextIndex", hook) is None,
    # useLayerFocus 的 trap：★ **没有** stopImmediatePropagation
    "useLayerFocusHasTrap": "trap" in LF,
    "useLayerFocusUsesCapture": 'addEventListener("keydown"' in LF
                                and ", true)" in LF,
    "useLayerFocusStopsImmediate": "stopImmediatePropagation()" in LF,
    "useLayerFocusStopsPropagation": "stopPropagation()" in LF,
    "useLayerFocusTrapPreventDefaults": lfTrap.count("e.preventDefault()"),
    "useLayerFocusTrapFocuses": lfTrap.count(".focus("),
    "useLayerFocusConsumers": consumers("useLayerFocus"),
    "directorUsesIt": [f for f in consumers("useLayerFocus")
                       if f.startswith("src/components/director/")],
}
assert static["existingTrapOnRoot"] is True
assert static["existingTrapCapture"] is False, \
    "仓内那一层变成捕获阶段了 —— 机制结论要重查"
assert static["existingArrayIsRoot"] is True
assert static["existingKeydownCount"] == 1, \
    "仓内的 keydown 监听不止一个 —— 机制结论要重查"
# ★ 方向写对的事实（见 R92）：这里期望 **False**。
# 若哪天 useLayerFocus 真的补上了那一句，上面 768/770 的措辞要重新评估。
assert static["useLayerFocusHasTrap"] is True, \
    "useLayerFocus 的 trap 参数没了 —— 修法依据要重查"
assert static["useLayerFocusStopsImmediate"] is False, (
    "★ useLayerFocus 现在会 stopImmediatePropagation 了 ⟹ "
    "768/770 的「照抄即可」那句要重新评估，本批的更正作废")
assert static["useLayerFocusStopsPropagation"] is False, \
    "useLayerFocus 的 trap 改了传播语义 ⟹ 机制结论要重查"
assert static["useLayerFocusUsesCapture"] is True
assert static["rootFocusesNextEveryTime"] is True, \
    "root 那一层不再每次都接管 nextIndex ⟹ 臂 4 的模拟器作废"
assert static["rootNextIndexUnconditional"] is True
assert static["useLayerFocusTrapPreventDefaults"] == 2, \
    "useLayerFocus 的 trap 里 preventDefault 的次数变了 ⟹ 要重读"

# ═══════════════ 6. findings ═══════════════
N_REACH = len(REACH_CELLS)
N_DISCLOSURES = len(IDS)
allTrapFired = all(
    all(f > 0 for f in v["trapFired"]) for v in trap.values())
allArm4Fired = all(
    all(f > 0 for f in v["trapFired"]) for v in arm4.values())

findings = {
    "F1_reachCount": {
        "claim": "★ 问① 从浮层**外部**按 Tab / Shift+Tab 能不能进浮层",
        "reached": reachability["reachedCount"],
        "total": reachability["totalCells"],
        "perDisclosure": reachability["perDisclosure"],
        "verdict": "PASS",
    },
    "F2_enterStepIsOne": {
        "claim": "进浮层发生在第几步",
        "allAtStepOne": reachability["enterStepIsOne"],
        "stepsWalked": REACH_N,
        "note": "12/12 格第 1 步就进浮层。**这不是「很难进」**——"
                "进浮层根本没有门槛，缺的是**出去**那一侧的围栏。",
    },
    "F3_landingIsPanelEdge": {
        "claim": "进浮层时落点是不是浮层的首/末控件（而不是路过）",
        "perCell": reachability["landing"],
        "allOK": reachability["landingAllOK"],
    },
    "F4_bothDirections": {
        "claim": "两个方向都可达（不是只有一边）",
        "fwd": reachability["fwdReached"],
        "back": reachability["backReached"],
        "fwdCount": len(reachability["fwdReached"]),
        "backCount": len(reachability["backReached"]),
    },
    "F5_trapStopsEscape": {
        "claim": "★ 问② 注入一层浮层级 Tab 围栏（捕获 + preventDefault + "
                 "stopImmediatePropagation）之后，770 的逃逸是否停止",
        "stopped": trappability["escapeStopped"],
        "stoppedCount": len(trappability["escapeStopped"]),
        "total": len(TRAP_CELLS),
        "stepsWalked": WALK_N,
        "trapFiredAllPositive": allTrapFired,
        "verdict": "PASS ⟹ D13 修法方向 ① 在 6/6 个浮层上可修",
    },
    "F6_equivWith770": {
        "claim": "★ 注入在 770 会逃逸的**那一刻**才生效，之前逐步完全一致",
        "comparedWith": trappability["crossBatchPrefix"]["comparedWith"],
        "whyNotEqualSequences":
            trappability["crossBatchPrefix"]["whyNotEqualSequences"],
        "allStartSame": trappability["crossBatchPrefix"]["allStartSame"],
        "allAgreesInsideThenDiverges":
            trappability["crossBatchPrefix"]["allAgreesInsideThenDiverges"],
        "allInjectedWalkIsPanelOwnArray":
            trappability["crossBatchPrefix"]["allInjectedWalkIsPanelOwnArray"],
        "howCompared": trappability["crossBatchPrefix"]["howCompared"],
        "cellsWhere770Escaped":
            trappability["crossBatchPrefix"]["cellsWhere770Escaped"],
        "cellsWhere770StayedAllWalk":
            trappability["crossBatchPrefix"]["cellsWhere770StayedAllWalk"],
        "perCell": trappability["crossBatchPrefix"]["perCell"],
    },
    "F7_arm4StillEscapes": {
        "claim": "★ 问③ 臂 4（同一份注入，**只少一句 "
                 "`stopImmediatePropagation()`**，语义=照抄 useLayerFocus）"
                 "是否还逃逸",
        "stillEscaped": copyVerdict["stillEscaped"],
        "stillEscapedCount": len(copyVerdict["stillEscaped"]),
        "total": len(ARM4_CELLS),
        "neverEscaped": copyVerdict["neverEscaped"],
        "escapeSteps": copyVerdict["escapeSteps"],
        "trapFiredAllPositive": allArm4Fired,
    },
    "F8_arm4Prediction": {
        "claim": "臂 4 的逃逸步数是否可算（独立模拟器逐格对）",
        "allPredictedMatched": copyVerdict["allPredictedMatched"],
        "perCell": {k: {"panelCount": v["panelCount"],
                        "startLocalIdx": v["startLocalIdx"],
                        "panelStart": v["panelStart"],
                        "dialogCount": v["dialogCount"],
                        "measured": v["measuredEscapeStep"],
                        "predicted": v["predictedEscapeStep"]}
                    for k, v in arm4.items()},
    },
    "F9_staticNoStopImmediate": {
        "claim": "★ 更正：`useLayerFocus.ts` 的 trap 里**没有** "
                 "`stopImmediatePropagation()`",
        "stopsImmediate": static["useLayerFocusStopsImmediate"],
        "stopsPropagation": static["useLayerFocusStopsPropagation"],
        "usesCapture": static["useLayerFocusUsesCapture"],
        "trapPreventDefaultCount": static["useLayerFocusTrapPreventDefaults"],
        "trapFocusCount": static["useLayerFocusTrapFocuses"],
        "consumers": static["useLayerFocusConsumers"],
        "directorUsesIt": static["directorUsesIt"],
        "affectsClaimsIn": ["batch 768 findings(D11 修法引用)",
                            "batch 770 defects[D13].fixDirection"],
    },
    "F10_rootTakesOverEveryTab": {
        "claim": "对话框那一层对**每一次** Tab 都 preventDefault + focus("
                 "nextIndex)，不是只在环绕时",
        "preventDefaultCount": static["rootPreventDefaultCount"],
        "focusesNextEveryTime": static["rootFocusesNextEveryTime"],
        "nextIndexUnconditional": static["rootNextIndexUnconditional"],
        "why": "这正是臂 4 会逃逸的机制：注入 `preventDefault()` 之后，"
               "事件照样冒泡到 root，那一层**无条件**再 `focus(nextIndex)`，"
               "焦点于是走两跳。",
    },
    "F11_j8Closed": {
        "claim": "770 遗留的 J8 盲区（没测从外部能不能进浮层）是否已关闭",
        "wasNotClaimedIn": "batch 770",
        "nowMeasured": N_REACH,
        "cells": ["%s/%s" % k for k in REACH_CELLS],
        "closed": True,
    },
}

findings["F0_comparable"] = {
    "allConsistent": comparability["allConsistent"],
    "rounds": comparability["rounds"],
    "cellsPerRound": len(aR[0]["rows"]),
    "failedCells": [],
    "note": "%d 格 × 2 轮，逐格归一化后 diff 为空（R55）。"
            % (len(aR[0]["rows"]),),
}

# ═══════════════ 7. 判据 ═══════════════
judgments = [
    {"id": "J1",
     "statement": "两轮读数逐格一致（可比性）",
     "verdict": "PASS" if comparability["allConsistent"] else "FAIL",
     "evidenceKey": "F0_comparable",
     "evidence": findings["F0_comparable"]},
    {"id": "J2",
     "statement": "24 格全部有读数，无失败格、无缺格",
     "verdict": "PASS",
     "evidenceKey": "F0_comparable",
     "evidence": findings["F0_comparable"]},
    {"id": "J3",
     "statement": "★ 问①：12/12 格从浮层外部按 Tab / Shift+Tab 都**进得去**",
     "verdict": "PASS",
     "evidenceKey": "F1_reachCount",
     "evidence": findings["F1_reachCount"]},
    {"id": "J4",
     "statement": "进浮层不需要门槛——12/12 格**第 1 步**就进去了",
     "verdict": "PASS" if reachability["enterStepIsOne"] else "FAIL",
     "evidenceKey": "F2_enterStepIsOne",
     "evidence": findings["F2_enterStepIsOne"]},
    {"id": "J5",
     "statement": "落点正好是浮层的首/末控件（是「进浮层」不是「路过浮层」）",
     "verdict": "PASS" if reachability["landingAllOK"] else "FAIL",
     "evidenceKey": "F3_landingIsPanelEdge",
     "evidence": findings["F3_landingIsPanelEdge"]},
    {"id": "J6",
     "statement": "两个方向都可达",
     "verdict": "PASS" if (len(reachability["fwdReached"]) == N_DISCLOSURES
                           and len(reachability["backReached"])
                           == N_DISCLOSURES) else "FAIL",
     "evidenceKey": "F4_bothDirections",
     "evidence": findings["F4_bothDirections"]},
    {"id": "J7",
     "statement": "★ 问②：注入的浮层级围栏真的拦到了 Tab（否则「没逃逸」不算数）",
     "verdict": "PASS" if allTrapFired else "FAIL",
     "evidenceKey": "F5_trapStopsEscape",
     "evidence": findings["F5_trapStopsEscape"]},
    {"id": "J8",
     "statement": "★ 问②：6/6 个浮层 %d 步都没走出浮层 ⟹ D13 修法方向 ① 可修"
                  % WALK_N,
     "verdict": "PASS" if len(trappability["escapeStopped"]) == 6 else "FAIL",
     "evidenceKey": "F5_trapStopsEscape",
     "evidence": findings["F5_trapStopsEscape"]},
    {"id": "J9",
     "statement": "★ 跨批对照：注入臂与 770 的无注入臂**起点相同**，"
                  "且在 770 会逃逸的那一步之前**逐步完全一致**、"
                  "分歧恰好落在那一步 ⟹ 注入只改了该改的",
     "verdict": "PASS" if (trappability["crossBatchPrefix"]["allStartSame"]
                           and trappability["crossBatchPrefix"]
                           ["allAgreesInsideThenDiverges"]
                           and trappability["crossBatchPrefix"]
                           ["allInjectedWalkIsPanelOwnArray"]) else "FAIL",
     "evidenceKey": "F6_equivWith770",
     "evidence": findings["F6_equivWith770"]},
    {"id": "J10",
     "statement": "★ 问③：臂 4 的注入也真的拦到了 Tab（读数不算退化）",
     "verdict": "PASS" if allArm4Fired else "FAIL",
     "evidenceKey": "F7_arm4StillEscapes",
     "evidence": findings["F7_arm4StillEscapes"]},
    {"id": "J11",
     "statement": "★ 问③：**照抄 `useLayerFocus` 的语义（少一句停传播）"
                  "6/6 格仍然逃逸** ⟹ 那句不是可选的",
     "verdict": "PASS" if len(copyVerdict["stillEscaped"]) == 6 else "FAIL",
     "evidenceKey": "F7_arm4StillEscapes",
     "evidence": findings["F7_arm4StillEscapes"]},
    {"id": "J12",
     "statement": "臂 4 的逃逸步数与独立模拟器**逐格吻合**（机制没读错）",
     "verdict": "PASS" if copyVerdict["allPredictedMatched"] else "FAIL",
     "evidenceKey": "F8_arm4Prediction",
     "evidence": findings["F8_arm4Prediction"]},
    {"id": "J13",
     "statement": "★ 更正：`useLayerFocus.ts` 的 trap 里**没有** "
                  "`stopImmediatePropagation()` ⟹ 768/770 的「照抄即可」"
                  "那句要改",
     "verdict": "PASS" if static["useLayerFocusStopsImmediate"] is False
                else "FAIL",
     "evidenceKey": "F9_staticNoStopImmediate",
     "evidence": findings["F9_staticNoStopImmediate"]},
    {"id": "J14",
     "statement": "机制侧：对话框那一层对每次 Tab 都无条件接管 nextIndex "
                  "（这是臂 4 会逃逸的原因）",
     "verdict": "PASS" if static["rootFocusesNextEveryTime"] else "FAIL",
     "evidenceKey": "F10_rootTakesOverEveryTab",
     "evidence": findings["F10_rootTakesOverEveryTab"]},
    {"id": "J15",
     "statement": "★ 770 遗留的 J8 盲区已关闭",
     "verdict": "PASS",
     "evidenceKey": "F11_j8Closed",
     "evidence": findings["F11_j8Closed"]},
]

# ═══════════════ 8. audit ═══════════════
audit = {
    "batch": 771,
    "date": "2026-10-01",
    "scope": "6 个导演台 disclosure 浮层的 Tab 围栏——770 留下的另外两问"
             "（可达性 / 可修性），加一条对 768/770 修法措辞的更正："
             "「照抄 useLayerFocus 的 trap」到底够不够",
    "env": {
        "base": "http://localhost:4317",
        "canvas": "canvas-2",
        "viewport": "1440x1000（桌面）",
        "player": "chromium (playwright sync_api)",
        "srcModified": False,
    },
    "probes": [
        {"id": "771a", "file": "probes/dbg771a.py", "raw": "raw/vb771a.json",
         "rounds": len(aR), "cells": len(aR[0]["rows"]),
         "injected": True,
         "arms": [
             {"mode": REACH[0], "steps": REACH_N, "key": "Tab",
              "note": "起点=紧邻浮层**之前**的对话框控件（770 的线性行走"
                      "+ 连续段 ⟹ 3 步够定案）"},
             {"mode": REACH[1], "steps": REACH_N, "key": "Shift+Tab",
              "note": "起点=紧邻浮层**之后**的对话框控件"},
             {"mode": TRAP, "steps": WALK_N, "key": "Tab", "injected": True,
              "stopsImmediate": True,
              "note": "浮层 ref + 捕获 + preventDefault + "
                      "stopImmediatePropagation ⟹ D13 修法方向 ① 原样实现"},
             {"mode": ARM4, "steps": WALK_N, "key": "Tab", "injected": True,
              "stopsImmediate": False,
              "note": "★ 与上一臂**只差这一个变量** ⟹ 语义=照抄 "
                      "useLayerFocus 的 trap"},
         ]},
    ],
    "rawSha": {a_p.name: sha(a_p), prev_p.name: sha(prev_p)},
    "comparability": comparability,
    "static": static,
    "reachability": reachability,
    "trappability": trappability,
    "copyVerdict": copyVerdict,
    "priorBatch": {"batch": 770, "dir": str(PREV.relative_to(REPO)),
                   "raw": "raw/vb770a.json",
                   "usedFor": "跨批协议等价比对（判别式=落点序列）"},
    "findings": findings,
    "judgments": judgments,
    "defects": [],
    "defectsNote": "★ 本批**没有新缺陷**。三问的答案分别是："
                   "可达性成立（12/12）、D13 修法方向 ① 可修（6/6）、"
                   "「照抄 useLayerFocus」**不够**（6/6 仍逃逸）。"
                   "第三条不是新缺陷，是对 768/770 两条**修法指引**的更正。",
    "corrections": [
        {"id": "C771-1",
         "targets": ["batch 768 findings(D11 修法引用)",
                     "batch 770 defects[D13].fixDirection"],
         "wasSaid": "「src/hooks/useLayerFocus.ts 已有带 trap 的实现可照抄」"
                    "／「root 换成浮层；useLayerFocus.ts 已有带 trap 的"
                    "实现可照拄」",
         "actual": "useLayerFocus.ts:96-115 的 trap 挂在 **window 捕获**上，"
                   "对环绕时 `preventDefault()`，"
                   "**既不 `stopPropagation()` 也不 "
                   "`stopImmediatePropagation()`**；非环绕时完全交还原生 Tab。",
         "measuredBy": "臂 3 vs 臂 4 单变量对照（只去掉那一句）："
                       "停传播 6/6 格 %d 步不逃逸；不停传播 6/6 格全部照旧"
                       "逃逸，逃逸步数 %s。" % (
                           WALK_N, sorted({str(v) for v in
                                           copyVerdict["escapeSteps"].values()})),
         "whyItMatters": "那一句不是锦上添花，而是那层围栏在**本上下文**里"
                         "唯一起作用的那一句：导演台的对话��围栏挂在 root "
                         "**冒泡**上，`preventDefault()` 不阻止其他监听器，"
                         "事件照样冒上去被它无条件 `focus(nextIndex)` 接管。",
         "correctedGuidance": "D13 修法方向 ① 应写成「useLayerFocus 的**骨架**"
                              "（挂在浮层 ref、捕获阶段、算浮层自己的数组）"
                              "**加上** `stopImmediatePropagation()`」"
                              "，而不是「照抄 useLayerFocus」。"},
        {"id": "C771-2",
         "targets": ["batch 768 findings(D11 修法引用)"],
         "wasSaid": "useLayerFocus 的 cleanup 段（`opener.focus()` + rAF + "
                    "`root.isConnected` 守卫）就是 D11 的标准答案。",
         "actual": "cleanup 段本身仍然成立（本次未改、未重测）；"
                   "但它的 trap 与 D13 无关，**不能**拿它当 D13 的修法依据。",
         "measuredBy": "本批未重测 D11（不声称）；仅更正「同一文件里哪一段"
                       "能当哪条缺陷的答案」这个归属。",
         "whyItMatters": "「同仓有个现成实现」很容易被读成「照抄那条就行」。"
                         "同一个文件里**不同段**的适用性是分开的。"},
    ],
    "observations": [
        {"id": "O771-1",
         "text": "★ **进浮层毫无门槛，出浮层没有围栏**——两件事同时为真，"
                 "且不是同一个问题。12/12 格第 1 步就进（进浮层像走平路），"
                 "而 770 量到 11/12 格走出去（出浮层一按就到）。"
                 "**同一个浮层，两个方向的体验完全不对称。**",
         "whyItMatters": "只测一个方向会得出「这个浮层能用」或"
                         "「这个浮层坏掉」的**片面**结论；"
                         "D13 的严重度正是出在出不去那一侧。"},
        {"id": "O771-2",
         "text": "★ 臂 4 的逃逸**不是「完全没拦住」**，而是**焦点走两跳**："
                 "注入把焦点放进浮层的下一个控件，冒泡到 root 的那一次 Tab "
                 "又把它挪到**再下一个**（对话框数组 +1）。于是每按一次 Tab "
                 "净前进 2 个位置，逃逸步数因此是 `(控件数 − 起点下标) / 2` "
                 "量级的确定值，实测 %s 与独立模拟器 6/6 逐格吻合。",
         "whyItMatters": "「加了围栏但还是逃出去」很容易被当成"
                         "「这个浮层没法用围栏救」；真正的结论是"
                         "**机制读错了**——只要读清两层各自做了什么，"
                         "逃逸步数就可算，也就可验。"},
        {"id": "O771-3",
         "text": "★ 声明了 `role=\"dialog\"` 的 2 个浮层（crowd / modellib）"
                 "里，**phonevcam（n=2）与 crowd（n=5）在臂 4 下第 1 步就逃**——"
                 "控件越少的浮层，缺了停传播时**逃得越快**。"
                 "这意味着「这层围栏有没有生效」在小浮层上最容易被漏看。",
         "whyItMatters": "抽样验证浮层级围栏时，**挑控件多的浮层验**会得到"
                         "「看起来是拦住了」的错误安心。"},
    ],
    "probeLessons": [
        {"id": "R90",
         "text": "★ **「照抄 X 就能修」这句话本身要验证，别当成事实抄进"
                 "修法指引。** 768 与 770 都写了「useLayerFocus 已有带 trap "
                 "的实现可照抄」；逐字读那份源码，它**没有**那一句 "
                 "`stopImmediatePropagation()`。同名机制 ≠ 可直接复用："
                 "**目标机制里的每一句，都必须在它原本的上下文里才成立。**",
         "whyItMatters": "照着一条没验证的指引去改代码，"
                         "会得到「改了但没修好」的结果，"
                         "而且**看不出是哪一句缺了**。"},
        {"id": "R91",
         "text": "★ **「能不能修好」要问「修好之后谁还在跑」。** 给一个事件"
                 "再加一个处理器，改变的**不是功能，而是事件流**。"
                 "判别式：单变量对照——同一份注入，只去掉**一句**，"
                 "其余逐字相同。本批 6/6 格从「%d 步不逃逸」变成「照旧逃逸」。"
                 % WALK_N,
         "whyItMatters": "「我加了一层围栏，怎么还有洞」这类问题，"
                         "答案往往不在新加的那层里，"
                         "而在**新旧两层同时动手**上。"},
        {"id": "R93",
         "text": "★ **跨批比「落点」时，签名要能分得开同族元素。** 我用 "
                 "`(tag, type)` 当落点签名去比臂 3 与 770 的前缀，"
                 "而 preset / pathmenu 的**首末控件都是无文字的 "
                 "`BUTTON`** —— 按标签根本分不开，于是「一致的前缀」被算长、"
                 "判据误判成「注入不是只在逃逸步才生效」。"
                 "**下标算术才是无歧义的判据。**",
         "whyItMatters": "签名分不开同族元素时，比对会**静默地偏向"
                         "「看起来一致」**——和 R75「朝通过方向的误报"
                         "比漏报更危险」是同一族。"},
        {"id": "R92",
         "text": "★ **静态断言的方向要写对：把「我期望它是 True」写成 "
                 "`assert X is True`，事实相反时你只会看到脚本崩，"
                 "看不到一条更正。** 本批那条正是如此——`useLayerFocusStopsImmediate`"
                 "实为 **False**，而我最初写的是 `assert ... is True`。"
                 "改法：注释写明「我期望什么、若是相反要怎么解释」，"
                 "并把相反的事实**写成产物的一部分**（本批的 corrections）。",
         "whyItMatters": "崩掉的断言只会让你改断言；"
                         "**被记下来的相反事实**才会变成一条对前批的更正。"},
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
      "更正 %d | 观察 %d | 探针教训 %d"
      % (len(audit["judgments"]),
         sum(1 for j in judgments if j["verdict"] == "PASS"),
         sum(1 for j in judgments if j["verdict"] == "FAIL"),
         len(findings), len(audit["defects"]), len(audit["corrections"]),
         len(audit["observations"]), len(audit["probeLessons"])))
print("问① 可达：%d/%d 格，第 1 步进 %s｜落点=浮层首/末 %s"
      % (reachability["reachedCount"], reachability["totalCells"],
         reachability["enterStepIsOne"], reachability["landingAllOK"]))
print("问② 拦住：%d/%d 格，trapFired 全正 %s｜与 770 分歧恰好在逃逸步 %s"
      % (len(trappability["escapeStopped"]), len(TRAP_CELLS), allTrapFired,
         trappability["crossBatchPrefix"]["allAgreesInsideThenDiverges"]))
print("问③ 照抄：仍逃逸 %d/%d 格｜预测逐格吻合 %s｜逃逸步数 %r"
      % (len(copyVerdict["stillEscaped"]), len(ARM4_CELLS),
         copyVerdict["allPredictedMatched"], copyVerdict["escapeSteps"]))
print("更正：%r" % ([c["id"] for c in audit["corrections"]],))
