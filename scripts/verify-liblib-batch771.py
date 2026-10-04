"""batch 771 验收器：6 个 disclosure 浮层的 Tab 围栏——可达性 / 可修性 /
「照抄 useLayerFocus 够不够」

三层结构（与 753–770 同）：
  1. **静态层** —— 从 `src/` 独立复核：导演台只有一层围栏且挂在 root（冒泡）、
     root 对**每次** Tab 都无条件 `preventDefault` + `focus(nextIndex)`；
     以及 `useLayerFocus.ts` 的 trap **没有** `stopImmediatePropagation()`
     （这条是本批对 768/770 修法措辞的更正）
  2. **产物层** —— 判据条数与 verdict、findings↔evidence 一致性、
     更正块、观察、教训、README 结构、台账行、表格首格不许裸数字
  3. **原始读数交叉核对** —— 从 `raw/vb771a.json` 与 batch 770 的
     `raw/vb770a.json` **重算**：可达性、注入是否真的拦到 Tab、
     注入臂是否走浮层自己的数组、与 770 的分歧点是否落在 770 的逃逸步、
     以及**臂 4 的逃逸步数**（验收器自己再写一份模拟器，不采信汇编器的
     派生字段）；缺失时**判失败而不是通过**

⚠ 本批盯住六件容易自欺的事：
  - **单变量必须真的单变量**：臂 3 与臂 4 只差 `stopsImmediate` 一个布尔。
    读数里那个字段必须逐格核对 —— 只在注释里说「只差一句」不算数。
  - **注入臂的读数只在「注入真的拦住了」时才算数**：先验 `trapFired > 0`
    与 `panelCount > 0`，否则「没逃逸」可能只是「浮层里一个可聚焦控件都没有」。
  - **「照抄」不能只靠读代码断言**：本批的核心就是把它变成单变量实测。
    验收器独立重读源码确认那句话确实不在，再核对 6/6 格仍逃逸。
  - **跨批可比的不是「序列相同」**：两臂处理变量不同，序列本来就不该相同。
    可比的是**分歧点**——必须落在 770 的逃逸步上。
  - **按 (tag,type) 比落点会踩坑**：preset/pathmenu 的首末控件都是无文字
    BUTTON，按标签分不开（汇编器先踩过）。验收器按**下标算术**比。
  - **`all([])` 是 True**：三组分类必须**铺满 24 格**；「臂 4 没有任何格逃逸」
    这种空集不许被当成「没测到」而通过。

判据 **15 条（15 PASS / 0 FAIL）**。
"""
import copy
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch771-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAWDIR = OUTDIR / "raw"
PROBEDIR = OUTDIR / "probes"
README = OUTDIR / "README.md"
LEDGER = ROOT / "docs/research/VERIFICATION_LEDGER.md"
PREV_RAW = (ROOT / "docs/research/liblib-canvas-batch770-2026-10-01/raw"
            / "vb770a.json")

RAW_FILES = ["vb771a.json"]
PROBE_FILES = ["dbg771a.py", "mk771audit.py"]
FFFD = "�"

IDS = ["export", "preset", "pathmenu", "phonevcam", "crowd", "modellib"]
REACH = ["reach-fwd", "reach-back"]
TRAP = "trap-fwd"
ARM4 = "trapnostop-fwd"
CELLS = ([(i, a) for i in IDS for a in REACH]
         + [(i, TRAP) for i in IDS] + [(i, ARM4) for i in IDS])
J_IDS = ["J%d" % i for i in range(1, 16)]
EXPECT_FAIL_IDS = []
EXPECT_PASS_IDS = J_IDS
EXPECT_LESSON_IDS = ["R90", "R91", "R92", "R93"]
EXPECT_CORRECTION_IDS = ["C771-1", "C771-2"]


def src(p):
    return (ROOT / p).read_text(encoding="utf-8")


def fc_strip(s):
    """去掉行注释，避免注释里的字样被当成代码命中。"""
    return re.sub(r"//[^\n]*", "", s)


def static_side():
    """静态层：独立复核围栏机制与本批那条更正。"""
    FC = src("src/components/director/useDirectorFocusContainment.ts")
    LF = src("src/hooks/useLayerFocus.ts")
    FCc, LFc = fc_strip(FC), fc_strip(LF)
    i = FCc.index("const handleKeyDown = (event: KeyboardEvent) => {")
    j = FCc.index('root.addEventListener("keydown", handleKeyDown);')
    hook = FCc[i:j]
    a = LFc.index("const onKey = (e: KeyboardEvent) => {")
    b = LFc.index('window.addEventListener("keydown", onKey, true);')
    lfTrap = LFc[a:b]
    consumers = []
    for p in sorted((ROOT / "src").rglob("*.ts*")):
        if p.name == "useLayerFocus.ts":
            continue
        try:
            t = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if re.search(r"import[^;]*\buseLayerFocus\b", t):
            consumers.append(str(p.relative_to(ROOT)))
    return {
        "trapOnRoot": 'root.addEventListener("keydown", handleKeyDown)' in FCc,
        "trapIsCapture":
            'root.addEventListener("keydown", handleKeyDown, true)' in FCc,
        "keydownListenerCount": FCc.count('addEventListener("keydown"'),
        "arrayIsRoot": "getDirectorFocusableElements(root)" in hook,
        "rootPreventDefault": "event.preventDefault()" in hook,
        "rootFocusesNextIndex":
            re.search(r"focusable\[nextIndex\]\?\.focus\(", hook) is not None,
        "rootNextIndexGuarded": re.search(r"if \(nextIndex", hook) is not None,
        "lfHasTrap": "trap" in LFc,
        "lfUsesCapture":
            'window.addEventListener("keydown", onKey, true)' in LFc,
        "lfStopsImmediate": "stopImmediatePropagation()" in LFc,
        "lfStopsPropagation": "stopPropagation()" in LFc,
        "lfTrapPreventDefaults": lfTrap.count("e.preventDefault()"),
        "lfConsumers": consumers,
        "lfDirectorConsumers": [f for f in consumers
                                if f.startswith("src/components/director/")],
    }


def sim_arm4(pS, n, D, s, steps):
    """验收器自己写的一份臂 4 模拟器（与汇编器那份**不共享代码**）。

    一步里两个处理器都会动手，且**都** preventDefault：
      ① 注入（浮层 ref、捕获）：面板内取下一个并环绕；
      ② 对话框 root（冒泡）：对话���数组 +1 并环绕
         （`useDirectorFocusContainment.ts` 对**每次** Tab 都接管 nextIndex）。
    浮层是数组里连续的一段 ⟹ 局部下标 +1 就是数组下标 +1。
    """
    out, i = [], s
    for _ in range(steps):
        j = i + 1 if i >= 0 else 0
        if j >= n:
            j = 0
        d = pS + j + 1
        if d >= D:
            d = 0
        i = d - pS
        out.append(i if 0 <= i < n else None)
    return out


def load_raw():
    """只负责**装载**。派生一律放到 derive()，且 run_checks 每次都重跑。"""
    for f in RAW_FILES:
        if not (RAWDIR / f).exists():
            raise SystemExit("缺原始读数 %s —— 判失败，不许通过" % f)
    for f in PROBE_FILES:
        if not (PROBEDIR / f).exists():
            raise SystemExit("缺探针脚本 %s —— 判失败，不许通过" % f)
    if not PREV_RAW.exists():
        raise SystemExit("缺 770 的 raw —— 跨批对照判失败")
    a = json.loads((RAWDIR / RAW_FILES[0]).read_text(encoding="utf-8"))
    prev = json.loads(PREV_RAW.read_text(encoding="utf-8"))
    rounds = a.get("rounds") or []
    if len(rounds) != 2:
        raise SystemExit("轮数 %d（要 2）" % len(rounds))
    g = {}
    for rd in rounds:
        for r in rd.get("rows") or []:
            g.setdefault((r.get("id"), r.get("mode")), []).append(r)
    miss = [k for k in CELLS if k not in g]
    if miss:
        raise SystemExit("缺格 %r" % (miss,))
    pg = {}
    for rd in prev["rounds"]:
        for r in rd.get("rows") or []:
            pg.setdefault((r.get("id"), r.get("mode")), []).append(r)
    return {"g": g, "prev": pg, "rounds": rounds}


def derive(g, pg):
    """★ 全部现算。**不采信产物里的任何派生字段**，也不复用上一次的结果 ——
    阴性对照正是靠改 ``g`` 之后重跑这一层来被看见的。"""
    D = {"failed": [], "walkN": None, "reachN": None,
         "reachEnter": {}, "reachLanding": {}, "reachAdjacent": {},
         "reachStartOutside": {}, "trapStopped": {}, "trapFired": {},
         "trapOwnArray": {}, "trapRange": {},
         "arm4Escaped": {}, "arm4Fired": {}, "arm4Predicted": {},
         "arm4StopsFlag": {}, "trapStopsFlag": {}, "cross": {}}
    for k, v in g.items():
        for r in v:
            if r.get("FAILED"):
                D["failed"].append("%s/%s: %s" % (k[0], k[1], r["FAILED"]))
        if len(v) != 2:
            D["failed"].append("%s 轮数 %d" % (k, len(v)))
    for i in IDS:
        for mode in (TRAP, ARM4):
            ns = {(r.get("walk") or {}).get("steps") for r in g[(i, mode)]}
            if len(ns) != 1:
                D["failed"].append("%s/%s 步数不一致 %r"
                                   % (i, mode, sorted(ns)))
                continue
            v = ns.pop()
            if D["walkN"] is None:
                D["walkN"] = v
            elif D["walkN"] != v:
                D["failed"].append("%s/%s 步数 %s 与别的浮层的 %s 不一致"
                                   % (i, mode, v, D["walkN"]))
    reachNs = {(r.get("walk") or {}).get("steps")
               for i in IDS for r in g[(i, REACH[0])]}
    if len(reachNs) != 1:
        raise SystemExit("可达性步数不一致：%r" % sorted(reachNs))
    D["reachN"] = reachNs.pop()
    if D["walkN"] is None:
        raise SystemExit("读不到注入臂的步数")

    for i in IDS:
        rg = None
        for mode in REACH:
            for r in g[(i, mode)]:
                st = r.get("start") or {}
                rgs = r.get("range") or {}
                if rg is None:
                    rg = rgs
                if rgs.get("contiguous") is not True:
                    D["failed"].append("%s/%s 浮层在数组里不连续" % (i, mode))
                if st.get("inPanel") is True:
                    D["reachStartOutside"][i] = False
                steps = r.get("steps") or []
                first = next((s for s in steps if s.get("inPanel") is True),
                             None)
                D["reachEnter"]["%s/%s" % (i, mode)] = (
                    first.get("step") if first else None)
                if first:
                    D["reachLanding"]["%s/%s" % (i, mode)] = first.get(
                        "idxInDialog")
        pS, pE = rg.get("panelStart"), rg.get("panelEnd")
        pC, Dg = rg.get("panelCount"), rg.get("dialogCount")
        D["trapRange"][i] = [pS, pE, pC, Dg]
        okF = all((r.get("start") or {}).get("idxInDialog") == pS - 1
                  or (pS == 0 and (r.get("start") or {}).get("idxInDialog")
                      == Dg - 1) for r in g[(i, REACH[0])])
        okB = all((r.get("start") or {}).get("idxInDialog") == pE + 1
                  or (pE + 1 >= Dg and (r.get("start") or {}).get("idxInDialog")
                      == 0) for r in g[(i, REACH[1])])
        D["reachAdjacent"][i] = okF and okB
        D["reachLanding"][i] = (
            D["reachLanding"].get("%s/%s" % (i, REACH[0])) == pS
            and D["reachLanding"].get("%s/%s" % (i, REACH[1])) == pE)

        esc, fired, own, flag, sIdx = None, [], True, True, None
        for r in g[(i, TRAP)]:
            steps = r.get("steps") or []
            if esc is None:
                esc = next((s["step"] for s in steps
                            if s.get("inPanel") is not True), None)
            fired.append(r.get("trapFired"))
            inj = r.get("injSetup") or {}
            if inj.get("stopsImmediate") is not True or not inj.get(
                    "panelCount"):
                flag = False
            if sIdx is None:
                sIdx = (r.get("start") or {}).get("idxInDialog")
        exp = [pS + ((sIdx - pS + k + 1) % pC) for k in range(D["walkN"])]
        for r in g[(i, TRAP)]:
            if [s.get("idxInDialog") for s in (r.get("steps") or [])] != exp:
                own = False
        D["trapStopped"][i] = esc is None
        D["trapFired"][i] = all(f is not None and f > 0 for f in fired)
        D["trapOwnArray"][i] = own
        D["trapStopsFlag"][i] = flag

        esc4, fired4, flag4, sLoc = None, [], True, None
        for r in g[(i, ARM4)]:
            steps = r.get("steps") or []
            if esc4 is None:
                esc4 = next((s["step"] for s in steps
                             if s.get("inPanel") is not True), None)
            fired4.append(r.get("trapFired"))
            inj = r.get("injSetup") or {}
            if inj.get("stopsImmediate") is not False or not inj.get(
                    "panelCount"):
                flag4 = False
            if sLoc is None:
                sLoc = (r.get("start") or {}).get("idxInPanel")
        sim = sim_arm4(pS, pC, Dg, sLoc, D["walkN"])
        pred = next((n + 1 for n, v in enumerate(sim) if v is None), None)
        D["arm4Escaped"][i] = esc4
        D["arm4Fired"][i] = all(f is not None and f > 0 for f in fired4)
        D["arm4Predicted"][i] = (esc4 == pred)
        D["arm4StopsFlag"][i] = flag4

    for i in IDS:
        old = pg.get((i, "fwd")) or []
        if not old:
            D["cross"][i] = {"ok": False, "why": "770 缺 %s/fwd" % i}
            continue
        os_ = old[0].get("steps") or []
        oldEsc = next((s.get("step") for s in os_
                       if s.get("inPanel") is not True), None)
        pS, pE = D["trapRange"][i][0], D["trapRange"][i][1]
        sIdx = (g[(i, TRAP)][0].get("start") or {}).get("idxInDialog")
        inside = pE - sIdx
        agree = all(
            os_[k].get("idxInDialog")
            == (g[(i, TRAP)][0].get("steps") or [])[k].get("idxInDialog")
            for k in range(min(inside, len(os_), D["walkN"])))
        D["cross"][i] = {
            "ok": bool(agree and ((oldEsc == inside + 1) if oldEsc is not None
                                  else inside >= D["walkN"])),
            "agree": agree, "oldEscapeStep": oldEsc, "inside": inside,
            "startSame": (old[0].get("start") or {}).get("idxInDialog") == sIdx,
        }
    return D


def run_checks(a, st, rw):
    # ★ 每次都从 g 重算一遍：阴性对照改的就是 g，不重算就看不见。
    _g, _pg = rw["g"], rw["prev"]
    rw = derive(_g, _pg)
    rw["g"], rw["prev"] = _g, _pg
    J = {j["id"]: j for j in a.get("judgments") or []}
    F = a.get("findings") or {}
    tp = a.get("trappability") or {}
    rch = a.get("reachability") or {}
    cv = a.get("copyVerdict") or {}
    C = []

    def chk(label, cond, got):
        C.append({"label": label, "pass": bool(cond), "got": got})

    # ── 产物层
    chk("产物：判据 15 条且 id 齐全", sorted(J) == sorted(J_IDS),
        {"got": sorted(J), "want": sorted(J_IDS)})
    chk("产物：verdict 与预期一致",
        all(J[j]["verdict"] == "PASS" for j in J_IDS if j in J)
        and not [j for j in EXPECT_FAIL_IDS],
        {"got": {j: J[j]["verdict"] for j in J_IDS if j in J}})
    bad = [j["id"] for j in J.values()
           if F.get(j["evidenceKey"]) != j["evidence"]]
    chk("产物：每条判据的 evidence 等于 findings[evidenceKey]",
        not bad, {"mismatch": bad})
    chk("产物：本批无新缺陷（三个问题都不是新缺陷）",
        a.get("defects") == [], {"got": a.get("defects")})
    corr = a.get("corrections") or []
    chk("产物：更正块 2 条（C771-1/C771-2）",
        sorted(c["id"] for c in corr) == sorted(EXPECT_CORRECTION_IDS),
        {"got": [c["id"] for c in corr]})
    chk("产物：C771-1 明确点名 768 与 770 两处措辞",
        any("768" in str(c.get("targets")) and "770" in str(c.get("targets"))
            for c in corr if c["id"] == "C771-1"),
        {"got": [c.get("targets") for c in corr]})
    lessons = a.get("probeLessons") or []
    chk("产物：教训 %s 齐全" % EXPECT_LESSON_IDS,
        sorted(x["id"] for x in lessons) == sorted(EXPECT_LESSON_IDS),
        {"got": [x["id"] for x in lessons]})
    chk("产物：观察 ≥3 条", len(a.get("observations") or []) >= 3,
        {"got": len(a.get("observations") or [])})
    chk("产物：raw/vb771a.json 的 sha 记进产物",
        "vb771a.json" in (a.get("rawSha") or {}),
        {"got": a.get("rawSha")})

    # ── 静态层
    chk("静态：导演台只有一层围栏且挂在 root（冒泡）",
        st["trapOnRoot"] and not st["trapIsCapture"]
        and st["keydownListenerCount"] == 1,
        {"onRoot": st["trapOnRoot"], "capture": st["trapIsCapture"],
         "listeners": st["keydownListenerCount"]})
    chk("静态：root 那一层对每次 Tab 都无条件 preventDefault + focus(next)",
        st["rootPreventDefault"] and st["rootFocusesNextIndex"]
        and not st["rootNextIndexGuarded"],
        {"pd": st["rootPreventDefault"], "focus": st["rootFocusesNextIndex"],
         "guarded": st["rootNextIndexGuarded"]})
    chk("静态：★ 更正 —— useLayerFocus 的 trap 没有 stopImmediatePropagation",
        st["lfStopsImmediate"] is False and st["lfStopsPropagation"] is False,
        {"stopImmediate": st["lfStopsImmediate"],
         "stopPropagation": st["lfStopsPropagation"]})
    chk("静态：useLayerFocus 仍挂在 window 捕获上（所以那句缺失是要紧的）",
        st["lfHasTrap"] and st["lfUsesCapture"],
        {"hasTrap": st["lfHasTrap"], "capture": st["lfUsesCapture"]})
    chk("静态：导演台一个组件都没用 useLayerFocus",
        st["lfDirectorConsumers"] == [],
        {"got": st["lfDirectorConsumers"]})
    chk("产物：静态层与验收器重读的源码一致",
        (a.get("static") or {}).get("useLayerFocusStopsImmediate") is False
        and (a.get("static") or {}).get("rootFocusesNextEveryTime") is True,
        {"got": {k: (a.get("static") or {}).get(k)
                 for k in ("useLayerFocusStopsImmediate",
                           "rootFocusesNextEveryTime")}})

    # ── 原始读数层
    chk("原始：24 格 × 2 轮、无缺格无失败格、步数一致",
        not rw["failed"] and len(rw["g"]) == len(CELLS)
        and all(len(v) == 2 for v in rw["g"].values()),
        {"failed": rw["failed"], "cells": len(rw["g"]),
         "walkSteps": rw["walkN"], "reachSteps": rw["reachN"]})
    chk("原始：★ 问① 12/12 格都进得去浮层",
        len(rw["reachEnter"]) == len(IDS) * 2
        and all(v == 1 for v in rw["reachEnter"].values()),
        {"enterAt": rw["reachEnter"]})
    chk("原始：问① 落点正好是浮层的首/末控件",
        all(rw["reachLanding"][i] is True for i in IDS),
        {"got": {i: rw["reachLanding"][i] for i in IDS}})
    chk("原始：问① 起点全部落在浮层外且紧邻浮层（「3 步够」的前提）",
        all(rw["reachStartOutside"].get(i) is not False for i in IDS)
        and all(rw["reachAdjacent"][i] for i in IDS),
        {"outside": rw["reachStartOutside"], "adjacent": rw["reachAdjacent"]})
    chk("原始：★ 问② 注入真的拦到了 Tab（否则「没逃逸」不算数）",
        all(rw["trapFired"][i] for i in IDS),
        {"got": rw["trapFired"]})
    chk("原始：★ 问② 6/6 个浮层 12 步都没走出浮层",
        all(rw["trapStopped"][i] for i in IDS),
        {"got": rw["trapStopped"]})
    chk("原始：注入臂走的是**浮层自己的数组**并环绕",
        all(rw["trapOwnArray"][i] for i in IDS),
        {"got": rw["trapOwnArray"]})
    chk("原始：单变量守住了 —— 臂 3 停传播、臂 4 不停",
        all(rw["trapStopsFlag"][i] for i in IDS)
        and all(rw["arm4StopsFlag"][i] for i in IDS),
        {"trap": rw["trapStopsFlag"], "arm4": rw["arm4StopsFlag"]})
    chk("原始：★ 问③ 臂 4 的注入也真的拦到了 Tab（读数不算退化）",
        all(rw["arm4Fired"][i] for i in IDS),
        {"got": rw["arm4Fired"]})
    chk("原始：★ 问③ 6/6 格在「照抄 useLayerFocus」的语义下**仍然逃逸**",
        all(rw["arm4Escaped"][i] is not None for i in IDS),
        {"got": rw["arm4Escaped"]})
    chk("原始：★ 问③ 逃逸步数与**验收器自己写的**模拟器逐格吻合",
        all(rw["arm4Predicted"][i] for i in IDS),
        {"got": rw["arm4Predicted"]})
    chk("原始：★ 与 770 的分歧点恰好落在 770 的逃逸步上",
        all(rw["cross"][i]["ok"] for i in IDS),
        {"got": {i: rw["cross"][i] for i in IDS}})
    chk("产物：三问的聚合与原始读数一致",
        rch.get("reachedCount") == 12 and rch.get("totalCells") == 12
        and len(tp.get("escapeStopped") or []) == 6
        and len(cv.get("stillEscaped") or []) == 6
        and cv.get("allPredictedMatched") is True,
        {"reached": rch.get("reachedCount"),
         "stopped": len(tp.get("escapeStopped") or []),
         "stillEscaped": len(cv.get("stillEscaped") or []),
         "predMatched": cv.get("allPredictedMatched")})
    chk("产物：分类铺满 —— 没有「没测到」的桶被当成通过",
        rch.get("neverReached") == [] and tp.get("stillEscaped") == []
        and cv.get("neverEscaped") == [],
        {"neverReached": rch.get("neverReached"),
         "trapStillEscaped": tp.get("stillEscaped"),
         "arm4NeverEscaped": cv.get("neverEscaped")})
    chk("产物：探针脚本与 raw 都随产物提交（R43）",
        all((PROBEDIR / f).exists() for f in PROBE_FILES)
        and all((RAWDIR / f).exists() for f in RAW_FILES),
        {"probes": PROBE_FILES, "raw": RAW_FILES})

    # ── README / 台账
    if not README.exists():
        chk("README 存在", False, "缺 README.md")
    else:
        rd = README.read_text(encoding="utf-8")
        chk("README：不含替换字符 U+FFFD", FFFD not in rd,
            {"count": rd.count(FFFD)})
        for need in ("可达性", "可修性", "照抄", "C771-1", "R90"):
            chk("README 提到「%s」" % need, need in rd, None)
        bare = [ln for ln in rd.split("\n")
                if re.match(r"^\|\s*\d+[a-z]?\s*\|", ln)]
        chk("README：表格首格没有裸数字（pre-commit 正则会拦）",
            not bare, {"bare": bare[:3]})
    if not LEDGER.exists():
        chk("台账存在", False, "缺台账")
    else:
        ll = LEDGER.read_text(encoding="utf-8")
        lines = [ln for ln in ll.split("\n") if ln.startswith("| Batch 771 ")]
        chk("台账：Batch 771 恰好一行", len(lines) == 1,
            {"count": len(lines)})
        if lines:
            chk("台账：该行不含 U+FFFD", FFFD not in lines[0],
                {"count": lines[0].count(FFFD)})
            chk("台账：首格是 `| Batch 771 |` 而不是裸数字",
                re.match(r"^\|\s*Batch 771\s*\|", lines[0]) is not None,
                {"head": lines[0][:60]})
            chk("台账：恰好 3 列", lines[0].count("|") == 4,
                {"pipes": lines[0].count("|")})
        chk("台账：历史 U+FFFD 仍在 9 处、且分布未变",
            ll.count(FFFD) == 9, {"count": ll.count(FFFD)})
    return C


def negative_controls(a, st, rw):
    """阴性对照：每条都改**所有轮**，且必须被拦下。"""
    out = []

    def run(name, mutate, expect_label_kw):
        aa = copy.deepcopy(a)
        rr = copy.deepcopy(rw)
        mutate(aa, rr)
        cs = run_checks(aa, st, rr)
        caught = not any(c["pass"] for c in cs
                         if expect_label_kw in c["label"])
        out.append({"name": name, "caught": caught,
                    "expectFailOn": expect_label_kw,
                    "stillPassing": [c["label"] for c in cs
                                     if c["pass"] and expect_label_kw
                                     in c["label"]]})

    def allRounds(g, key, fn):
        for r in g[key]:
            fn(r)

    def firstTrapRow(g, i):
        return g[(i, TRAP)][0]

    def firstArm4Row(g, i):
        return g[(i, ARM4)][0]

    def m_stopsFlagToFalse(aa, rr):
        allRounds(rr["g"], (IDS[0], TRAP),
                  lambda r: r["injSetup"].__setitem__("stopsImmediate", False))

    def m_arm4FlagToTrue(aa, rr):
        allRounds(rr["g"], (IDS[0], ARM4),
                  lambda r: r["injSetup"].__setitem__("stopsImmediate", True))

    def m_reachNotEntered(aa, rr):
        for k in [(i, a2) for i in IDS for a2 in REACH]:
            for r in rr["g"][k]:
                for s in r.get("steps") or []:
                    if s.get("inPanel") is True:
                        s["inPanel"] = False

    def m_arm4EscapeStepWrong(aa, rr):
        for r in rr["g"][(IDS[0], ARM4)]:
            for s in r.get("steps") or []:
                if s.get("inPanel") is False:
                    s["step"] = 99

    def m_trapLeavesPanel(aa, rr):
        for r in rr["g"][(IDS[0], TRAP)]:
            for s in r.get("steps") or []:
                s["inPanel"] = False

    def m_trapFiredZero(aa, rr):
        allRounds(rr["g"], (IDS[0], TRAP),
                  lambda r: r.__setitem__("trapFired", 0))

    def m_evidenceTamper(aa, rr):
        for j in aa.get("judgments") or []:
            if j["id"] == "J11":
                j["evidence"]["stillEscapedCount"] = 0

    def m_dropFindingsKey(aa, rr):
        aa.get("findings", {}).pop("F7_arm4StillEscapes", None)

    def m_defectInjected(aa, rr):
        aa["defects"] = [{"id": "DX", "severity": "低", "title": "假的"}]

    def m_correctionDropped(aa, rr):
        aa["corrections"] = [c for c in aa.get("corrections") or []
                             if c["id"] != "C771-1"]

    def m_lessonDropped(aa, rr):
        aa["probeLessons"] = [x for x in aa.get("probeLessons") or []
                              if x["id"] != "R91"]

    def m_ledgerLineRemoved(aa, rr):
        pass  # 由下面单独的文本对照处理

    run("把臂 3 的 stopsImmediate 改成 False（抹掉单变量）",
        m_stopsFlagToFalse, "单变量守住了")
    run("把臂 4 的 stopsImmediate 改成 True（抹掉单变量）",
        m_arm4FlagToTrue, "单变量守住了")
    run("把可达性 12 格全部改成「没进浮层」",
        m_reachNotEntered, "都进得去浮层")
    run("改掉臂 4 一格的逃逸步数（打乱模拟器预测）",
        m_arm4EscapeStepWrong, "模拟器逐格吻合")
    run("让臂 3 有一格走出浮层（把「6/6 拦住」做成假的）",
        m_trapLeavesPanel, "都没走出浮层")
    # ★ 关键词必须**唯一**：问②与问③的判据都含「真的拦到了 Tab」，
    #   写宽了会被另一条「仍然通过」顶掉 —— 那就是**对照自己漏放**（R86）。
    run("把臂 3 的 trapFired 置 0（「没逃逸」变成退化）",
        m_trapFiredZero, "问② 注入真的拦到了")
    run("篡改一条判据的 evidence（让它与 findings 不符）",
        m_evidenceTamper, "evidence 等于 findings")
    run("删掉判据引用的 findings 键",
        m_dropFindingsKey, "evidence 等于 findings")
    run("给本批塞一个假的新缺陷",
        m_defectInjected, "本批无新缺陷")
    run("删掉 C771-1 这条更正",
        m_correctionDropped, "更正块 2 条")
    run("删掉一条探针教训",
        m_lessonDropped, "教训")

    # 文本类对照：直接动文件，跑完复原
    def text_run(name, path, old, new, expect_fail):
        if not path.exists():
            out.append({"name": name, "caught": False,
                        "why": "文件不存在，无法做文本对照"})
            return
        orig = path.read_text(encoding="utf-8")
        if old not in orig:
            out.append({"name": name, "caught": False,
                        "why": "锚点没找到：%r" % old[:40]})
            return
        try:
            path.write_text(orig.replace(old, new, 1), encoding="utf-8")
            aa = json.loads(AUDIT.read_text(encoding="utf-8"))
            cs = run_checks(aa, st, rw)
            caught = not any(c["pass"] for c in cs if expect_fail in c["label"])
            out.append({"name": name, "caught": caught,
                        "expectFailOn": expect_fail,
                        "stillPassing": [c["label"] for c in cs
                                         if c["pass"] and expect_fail
                                         in c["label"]]})
        finally:
            path.write_text(orig, encoding="utf-8")

    text_run("把台账 Batch 771 行删掉", LEDGER,
             "| Batch 771 ", "| Batch 771X ", "台账：Batch 771 恰好一行")
    if README.exists():
        rd = README.read_text(encoding="utf-8")
        anchor = next((ln for ln in rd.split("\n")
                       if ln.startswith("|")), "")
        text_run("把 README 表格首格改成裸数字（pre-commit 正则会拦）",
                 README, anchor, "| 771 | x | y |", "首格没有裸数字")
    return out


def main():
    if not AUDIT.exists():
        print("缺少 runtime-audit.json")
        return 1
    a = json.loads(AUDIT.read_text(encoding="utf-8"))
    st = static_side()
    try:
        rw = load_raw()
        rawErr = None
    except Exception as e:
        rw, rawErr = {}, str(e)

    checks = run_checks(a, st, rw) if not rawErr else [
        {"label": "原始读数可用（raw/ + probes/ + 770 的 raw）", "pass": False,
         "got": rawErr}]
    neg = [] if rawErr else negative_controls(a, st, rw)

    npass = sum(1 for c in checks if c["pass"])
    total = len(checks)
    neg_ok = sum(1 for n in neg if n["caught"])
    ok = npass == total and neg_ok == len(neg)

    REPORT.write_text(json.dumps(
        {"batch": 771, "checks": checks, "pass": npass, "total": total,
         "negativeControls": neg, "negativeCaught": neg_ok,
         "negativeTotal": len(neg), "rawError": rawErr, "ok": ok},
        ensure_ascii=False, indent=1), encoding="utf-8")

    for c in checks:
        if not c["pass"]:
            print("FAIL  %s  got=%s" % (c["label"], json.dumps(
                c["got"], ensure_ascii=False)[:260]))
    print("\n验收 %d/%d 通过" % (npass, total))
    print("阴性对照 %d/%d 全部拦下" % (neg_ok, len(neg)))
    for n in neg:
        if not n["caught"]:
            print("  ✗ 漏放：%s  (%s)" % (n["name"], n.get("why")
                                        or n.get("expectFailOn")))
    print("batch 771 %s" % ("通过" if ok else "不通过"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
