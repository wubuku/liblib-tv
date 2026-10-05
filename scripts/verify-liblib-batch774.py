"""batch 774 验收器：D14 修法方向① 的注入对照 + Escape 会不会被误伤

三层结构（与 753–773 同）：
  1. **静态层** —— 从 `src/` 独立复核：桌内那个 keydown 监听是 window **冒泡**
     非捕获、`isEditable` 早退的判据含 `isContentEditable`、**Escape 阶梯排在
     那道守卫之后**（问② 的全部要害）、六个浮层的 Escape 主人的**注册阶段**由
     机械普查得出且**未映射的每个都有书面理由**
  2. **产物层** —— 判据条数与 verdict、evidence↔evidenceIndex 一致、教训、
     观察、更正块、README 结构、台账行、表格首格不许裸数字
  3. **原始读数交叉核对** —— 从 `raw/vb774{a,b}.json` **重算**格集合与覆盖
     完整性、每格自证、五个臂各自的预测、问② 的三态与三组分组

⚠ 本批盯住十件容易自欺的事：
  - **R100：阴性对照不能只看 `defaultPrevented`**（本批新增）。「注入把键投递
    本身弄坏」与「桌内不处理该键」**都会得 dp=false** ⟹ 必须同时断言
    **间谍确实收到了那个键**。这条判据要真能鉴别，就得有阴性对照专门把
    `keysSeen` 里的 `F2` 删掉而看它变红。
  - **R101：每个臂都要逐臂断言非空**。773 的 `for` 补丁没落进文件 ⟹ 那一臂
    一次都没跑，而探针与汇编器都不报错。验收器要自己数出每个臂的格数。
  - **R99：`defaultPrevented` 与 `targetCE` 都要读到了两个不同的值**。全同值
    意味着「压根没记」或「注入压根没生效」。
  - **注入必须真的生效**：任何一格 `injectionSilent` ⟹ 判失败。
  - **`isContentEditable` 的继承是行为假设**，必须逐格验 `injectActiveCE`。
  - **三态读数**（`deskGone` / `layerClosedOnly` / `nothing`）缺一不可：只报
    「面板还在不在」会把「导演台没了」读成「面板还在」。
  - **分组必须铺满且互斥**：`noChange` / `fixesD8` / `regression` 各 2 层，
    且三个集合的并集恰好是 6 个浮层。
  - **「问① 充分」与「问① 识别」是两件事**：验收器要确认产物里**明写**了
    「不证识别性」这条边界，不许把充分性吹成识别性。
  - **静态扫描按 handler 名找函数体在同名时必错**（R102）：验收器**独立**重跑
    一遍普查，与产物对账。
  - **探针 raw/ 与 probes/ 必须在场**（R43）。

判据 **8 条**（J1–J8）。
"""
import copy
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch774-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAWDIR = OUTDIR / "raw"
PROBEDIR = OUTDIR / "probes"
README = OUTDIR / "README.md"
LEDGER = ROOT / "docs/research/VERIFICATION_LEDGER.md"

RAW_FILES = ["vb774a.json", "vb774b.json"]
PROBE_FILES = ["dbg774a.py", "dbg774b.py", "mk774audit.py"]
FFFD = "�"

IDS = ["export", "preset", "pathmenu", "phonevcam", "crowd", "modellib"]
KEYS = ["Delete", "Backspace", "Meta+z", "Meta+c", "Meta+v"]
NEUTRAL_KEY = "F2"
HAS_EDITABLE = {"export", "crowd", "modellib"}
A_CELLS = ([(i, "base", "noneditable", "Delete") for i in IDS]
           + [(i, "alpha", "noneditable", k) for i in IDS for k in KEYS]
           + [(i, "beta", "noneditable", "Delete") for i in IDS]
           + [(i, "neutral", "noneditable", NEUTRAL_KEY) for i in IDS]
           + [(i, "beta", "editable", "Delete") for i in sorted(HAS_EDITABLE)])
B_CELLS = [(i, arm) for i in IDS for arm in ("none", "alpha")]
INJECT_ARMS = ("alpha", "beta", "neutral")
J_IDS = ["J%d" % i for i in range(1, 9)]
EXPECT_LESSON_IDS = ["R100", "R101", "R102"]
EXPECT_CORRECTION_IDS = ["C774-1"]

# 未映射到浮层的 Escape 监听器，**每个都要有书面理由**（R102）
UNMAPPED_REASON = {
    ("DirectorDesk.tsx", "handleKeyDown"):
        "桌内那个阶梯本身（它就是被测对象，不是任何浮层的主人）",
    ("DirectorInspector.tsx", "handleKeyDown"):
        "关的是 setViewerCaptureId —— 取景器，不是六个浮层之一",
    ("DirectorObjectTree.tsx", "esc"):
        "关的是对象树的右键菜单，不是六个浮层之一",
    ("DirectorViewport.tsx", "handleKeyDown"):
        "★ 它是 **motionPathDraft 绘制态**的 Escape/Enter 处理器"
        "（只有 `timeline.motionPathDraft` 非空时才注册），"
        "**不是路径菜单的主人**",
}
OWNER_BY_SETTER = {"setPathMenuLeft": "pathmenu",
                   "setPresetPanelLeft": "preset",
                   "setModelLibraryOpen": "modellib"}


# ───────────────── 静态层（独立实现，不 import 汇编器） ─────────────────
def blank_comments(s):
    """注释**抹白而不删** —— 行数与偏移都不变（R102）。"""
    out = list(s)
    i, n, state = 0, len(s), None
    while i < n:
        c = s[i]
        nxt = s[i + 1] if i + 1 < n else ""
        if state is None:
            if c == "/" and nxt == "/":
                state = "line"
                out[i] = out[i + 1] = " "
                i += 2
                continue
            if c == "/" and nxt == "*":
                state = "block"
                out[i] = out[i + 1] = " "
                i += 2
                continue
        elif state == "line":
            if c == "\n":
                state = None
            else:
                out[i] = " "
        else:
            if c == "*" and nxt == "/":
                out[i] = out[i + 1] = " "
                state = None
                i += 2
                continue
            if c != "\n":
                out[i] = " "
        i += 1
    return "".join(out)


def line_offsets(s):
    off, acc = [0], 0
    for ln in s.split("\n"):
        acc += len(ln) + 1
        off.append(acc)
    return off


def static_side():
    DD = blank_comments(
        (ROOT / "src/components/director/DirectorDesk.tsx")
        .read_text(encoding="utf-8"))
    ddLines = DD.split("\n")
    i0 = DD.index("const handleKeyDown = (event: KeyboardEvent) => {")
    i1 = DD.index('window.addEventListener("keydown", handleKeyDown);')
    kdLines = DD[i0:i1].split("\n")
    kd = "\n".join(kdLines)

    def rel(pat):
        return next((n for n, ln in enumerate(kdLines, 1) if pat in ln), None)

    guardRel, escRel = rel("if (isEditable) return;"), \
        rel('event.key !== "Escape"')
    metaRel, delRel = rel('toLowerCase() === "c"'), \
        rel('event.key === "Delete"')
    guardAbs = next((n for n, ln in enumerate(ddLines, 1)
                     if "if (isEditable) return;" in ln), None)

    listeners, owners, unmapped = [], {}, []
    for p in sorted((ROOT / "src/components/director").glob("*.ts*")):
        txt = blank_comments(p.read_text(encoding="utf-8"))
        lines, off = txt.split("\n"), line_offsets(txt)
        for n, ln in enumerate(lines, 1):
            if not re.search(r'addEventListener\(\s*"keydown"', ln):
                continue
            hm = re.search(
                r'addEventListener\(\s*"keydown"\s*,\s*([A-Za-z_$][\w$]*)', ln)
            hname = hm.group(1) if hm else None
            tm = re.search(r'addEventListener\(\s*"keydown"\s*,\s*'
                           r'[A-Za-z_$][\w$]*\s*,\s*(\w+)', ln)
            addPos = off[n - 1]
            body = ""
            if hname:
                # ★ 同名 handler 在同一文件里可能有好几个 ⟹ 取「最近的、
                #   在这次 addEventListener **之前**」的那次定义（R102）
                best = None
                for dm in re.finditer(
                        r'(?:const|function)\s+%s\s*=?\s*'
                        r'(?:\([^)]*\)|function)?\s*(?:=>\s*)?'
                        r'(?::\s*[^{]+)?\s*\{' % re.escape(hname), txt):
                    if dm.start() < addPos and (best is None
                                                or dm.start() > best.start()):
                        best = dm
                if best:
                    depth, i = 0, best.end() - 1
                    while i < len(txt):
                        if txt[i] == "{":
                            depth += 1
                        elif txt[i] == "}":
                            depth -= 1
                            if depth == 0:
                                break
                        i += 1
                    body = txt[best.end() - 1:i + 1]
            L = {"file": p.name, "line": n, "handler": hname,
                 "phase": (tm.group(1) if tm else "bubble"),
                 "hasEscape": "Escape" in body,
                 "hasPreventDefault": "preventDefault" in body,
                 "hasStopImmediate": "stopImmediatePropagation" in body,
                 "setters": sorted(set(re.findall(
                     r"\b(set[A-Z]\w*)\s*\(", body))),
                 "callsOnClose": "onClose(" in body}
            listeners.append(L)
            if not L["hasEscape"]:
                continue
            who = None
            for s in L["setters"]:
                if s in OWNER_BY_SETTER:
                    who = OWNER_BY_SETTER[s]
                    break
            if who is None and L["callsOnClose"] \
                    and L["file"] == "DirectorPhoneVcamPanel.tsx":
                who = "phonevcam"
            if who is None:
                unmapped.append(L)
            else:
                owners[who] = L
    return {
        "deskListenerOnWindow":
            'window.addEventListener("keydown", handleKeyDown);' in DD,
        "deskListenerIsCapture":
            'window.addEventListener("keydown", handleKeyDown, true);' in DD,
        "guardLine": guardAbs,
        "guardIsEditableReturn": "if (isEditable) return;" in kd,
        "guardPredicateHasContentEditable": "target.isContentEditable" in kd,
        "guardPredicateHasTagNames": all(
            ('tagName === "%s"' % t) in kd
            for t in ("INPUT", "TEXTAREA", "SELECT")),
        "guardBeforeMetaC": bool(guardRel and metaRel and guardRel < metaRel),
        "guardBeforeDelete": bool(guardRel and delRel and guardRel < delRel),
        "escapeStaircaseAfterGuard": bool(guardRel and escRel
                                         and escRel > guardRel),
        "escapeStaircaseRelLine": escRel,
        "exportPanelLadderStep": "if (exportPanelOpen) {" in kd,
        "closeWorkspaceInLadder": "closeWorkspace();" in kd,
        "listeners": listeners,
        "listenersCount": len(listeners),
        "owners": owners,
        "ownersCapture": sorted(w for w, L in owners.items()
                                if L["phase"] == "true"),
        "ownersBubble": sorted(w for w, L in owners.items()
                               if L["phase"] != "true"),
        "unmapped": [{"file": L["file"], "line": L["line"],
                      "handler": L["handler"], "phase": L["phase"],
                      "whyNotALayerOwner": UNMAPPED_REASON[
                          (L["file"], L["handler"])]}
                     for L in unmapped
                     if (L["file"], L["handler"]) in UNMAPPED_REASON],
        "unmappedSet": sorted((L["file"], L["handler"]) for L in unmapped),
    }


# ───────────────── 原始读数（重算） ─────────────────
def load_raw():
    for f in RAW_FILES:
        if not (RAWDIR / f).exists():
            raise SystemExit("缺原始读数 %s —— 判失败，不许通过" % f)
    for f in PROBE_FILES:
        if not (PROBEDIR / f).exists():
            raise SystemExit("缺探针脚本 %s —— 判失败，不许通过" % f)
    rw = {}
    for tag, f in (("A", "vb774a.json"), ("B", "vb774b.json")):
        rw[tag] = json.loads((RAWDIR / f).read_text(encoding="utf-8"))
        if len(rw[tag].get("rounds") or []) != 2:
            raise SystemExit("%s 轮数不是 2" % f)
    return rw


def derive(rw):
    """★ 全部现算，不采信产物里的任何派生字段。"""
    A, B = rw["A"], rw["B"]
    gA, gB, skipA = {}, {}, set()
    for rd in A["rounds"]:
        for r in rd.get("rows") or []:
            if r.get("SKIPPED"):
                skipA.add((r.get("id"), r.get("arm"), r.get("want")))
                continue
            gA.setdefault((r.get("id"), r.get("arm"), r.get("want"),
                           r.get("key")), []).append(r)
    for rd in B["rounds"]:
        for r in rd.get("rows") or []:
            if r.get("FAILED"):
                continue
            gB.setdefault((r.get("id"), r.get("arm")), []).append(r)
    D = {"badCoverage": [], "gridA": sorted(gA), "gridB": sorted(gB),
         "skipA": sorted(skipA), "roundsConsistent": True}

    def consistency(raw):
        r0 = json.loads(json.dumps(raw["rounds"][0].get("rows")))
        r1 = json.loads(json.dumps(raw["rounds"][1].get("rows")))
        return r0 == r1

    D["roundsConsistentA"] = consistency(A)
    D["roundsConsistentB"] = consistency(B)
    D["roundsConsistent"] = D["roundsConsistentA"] and D["roundsConsistentB"]

    if D["gridA"] != sorted(A_CELLS):
        D["badCoverage"].append(
            "问① 格集合不符：多 %r / 少 %r"
            % (sorted(set(D["gridA"]) - set(A_CELLS))[:3],
               sorted(set(A_CELLS) - set(D["gridA"]))[:3]))
    if D["gridB"] != sorted(B_CELLS):
        D["badCoverage"].append(
            "问② 格集合不符：多 %r / 少 %r"
            % (sorted(set(D["gridB"]) - set(B_CELLS))[:3],
               sorted(set(B_CELLS) - set(D["gridB"]))[:3]))
    if D["skipA"]:
        D["badCoverage"].append("问② 臂 E 本来就只跑 3 层，不该有 SKIP：%r"
                                % (D["skipA"],))
    for src, g in (("A", gA), ("B", gB)):
        for k, v in g.items():
            if len(v) != 2:
                D["badCoverage"].append("%s %s 轮数 %d" % (src, k, len(v)))
            for r in v:
                if r.get("FAILED"):
                    D["badCoverage"].append(
                        "%s %s FAILED: %s" % (src, k, str(r["FAILED"])[:60]))
    # ★ R101：逐臂数格 —— 某一臂一次都没跑时**必须**红
    for arm in ("base", "alpha", "beta", "neutral"):
        n = len([k for k in gA if k[1] == arm])
        D["armCells"] = D.get("armCells", {})
        D["armCells"][arm] = n
        if n == 0:
            D["badCoverage"].append("★ 臂「%s」一次都没跑（R101）" % arm)
    D["armCellsExpected"] = {"base": 6, "alpha": 30, "beta": 9, "neutral": 6}

    def cA(r):
        f = r.get("focus") or {}
        inj = r.get("inject") or {}
        return {"focusEditable": f.get("editable") is True,
                "selectedIds": r.get("selectedIds") or [],
                "spyInstalled": (r.get("spy") or {}).get("installed") is True,
                "eventsSeen": r.get("eventsSeen") or 0,
                "keysSeen": r.get("keysSeen") or [],
                "dp": r.get("defaultPrevented"),
                "targetCE": r.get("targetCE"),
                "objectsDelta": r.get("objectsDelta"),
                "selectedDelta": r.get("selectedDelta"),
                "injectTook": inj.get("took"),
                "injectRootCE": inj.get("rootCE"),
                "injectActiveCE": inj.get("activeCE"),
                "injectionSilent": r.get("injectionSilent") is True,
                # ★ 问① 的格**每一个**都该收到事件（没有哪一层掐断传播），
                #   所以这里恒为 False，并在下面被断言。
                "spySawNothing": r.get("spySawNothing") is True}

    def cB(r):
        inj = r.get("inject") or {}
        return {"spyInstalled": (r.get("spy") or {}).get("installed") is True,
                "eventsSeen": r.get("eventsSeen") or 0,
                "keysSeen": r.get("keysSeen") or [],
                "dp": r.get("defaultPrevented"),
                "targetCE": r.get("targetCE"),
                "outcome": r.get("outcome"),
                "deskOpen": r.get("deskOpen"),
                "panelPresent": r.get("panelPresent"),
                "spySawNothing": r.get("spySawNothing") is True,
                "dpUnreadable": r.get("dpUnreadable"),
                "injectTook": inj.get("took"),
                "injectionSilent": r.get("injectionSilent") is True}

    tA = {k: [cA(r) for r in v] for k, v in gA.items()}
    tB = {k: [cB(r) for r in v] for k, v in gB.items()}
    D["tA"], D["tB"] = tA, tB

    def uniq(t, k, f):
        # ★ 缺格必须变成**一条判据红**，而不是让 derive 崩掉 ——
        #   崩掉的话阴性对照「把某一臂整臂删掉」就测不到那条判据了。
        cells = t.get(k) or []
        if not cells:
            return "<missing>"
        vs = {c[f] for c in cells}
        return vs.pop() if len(vs) == 1 else sorted(map(str, vs))

    D["base"] = {i: {"dp": uniq(tA, (i, "base", "noneditable", "Delete"),
                               "dp"),
                     "targetCE": uniq(tA, (i, "base", "noneditable",
                                           "Delete"), "targetCE")}
                 for i in IDS}
    D["alpha"] = {}
    for i in IDS:
        for kk in KEYS:
            k = (i, "alpha", "noneditable", kk)
            v = tA.get(k) or []
            D["alpha"][(i, kk)] = {
                "dp": uniq(tA, k, "dp"), "targetCE": uniq(tA, k, "targetCE"),
                "objectsDelta": sorted({c["objectsDelta"] for c in v}
                                       or ["<missing>"]),
                "selectedDelta": sorted({c["selectedDelta"] for c in v}
                                        or ["<missing>"])}
    D["beta"] = {}
    for i in IDS:
        k = (i, "beta", "noneditable", "Delete")
        v = tA.get(k) or []
        D["beta"][i] = {
            "dp": uniq(tA, k, "dp"), "targetCE": uniq(tA, k, "targetCE"),
            "rootCE": sorted({str(c["injectRootCE"]) for c in v})
                      or ["<missing>"],
            "activeCE": sorted({str(c["injectActiveCE"]) for c in v})
                       or ["<missing>"],
            "objectsDelta": sorted({c["objectsDelta"] for c in v}
                                   or ["<missing>"])}
    D["neutral"] = {}
    for i in IDS:
        k = (i, "neutral", "noneditable", NEUTRAL_KEY)
        ks = [set(c["keysSeen"]) for c in (tA.get(k) or [])]
        D["neutral"][i] = {
            "dp": uniq(tA, k, "dp"), "targetCE": uniq(tA, k, "targetCE"),
            "sawNeutralKey": all(NEUTRAL_KEY in s for s in ks) if ks else False,
            "eventsSeen": sorted({c["eventsSeen"] for c in (tA.get(k) or [])}
                                 or ["<missing>"])}
    D["betaEd"] = {}
    for i in sorted(HAS_EDITABLE):
        k = (i, "beta", "editable", "Delete")
        D["betaEd"][i] = {"dp": uniq(tA, k, "dp"),
                          "targetCE": uniq(tA, k, "targetCE")}
    D["esc"] = {}
    for i in IDS:
        for arm in ("none", "alpha"):
            k = (i, arm)
            D["esc"][(i, arm)] = {
                "dp": uniq(tB, k, "dp"), "targetCE": uniq(tB, k, "targetCE"),
                "outcome": uniq(tB, k, "outcome"),
                "deskOpen": uniq(tB, k, "deskOpen"),
                "panelPresent": uniq(tB, k, "panelPresent"),
                "spySawNothing": uniq(tB, k, "spySawNothing")}
    # ★ 四桶而不是三桶：「修好 D8」与「引入死键」**不是同一件事**
    #   （crowd 两件都占），压进一个桶就会把 crowd 说成纯收益。
    eff = {}
    for i in IDS:
        a, b = D["esc"][(i, "none")], D["esc"][(i, "alpha")]
        sig = lambda z: (z["dp"], z["outcome"], z["deskOpen"],  # noqa: E731
                         z["panelPresent"])
        if sig(a) == sig(b):
            eff[i] = "noChange"
        elif a["outcome"] == "deskGone" and b["outcome"] == "layerClosedOnly":
            eff[i] = "fixesD8Cleanly"
        elif a["outcome"] == "deskGone" and b["outcome"] == "nothing":
            eff[i] = "fixesD8ButDeadKey"
        else:
            eff[i] = "regression"
    D["effects"] = eff
    grp = {}
    for i, e in eff.items():
        grp.setdefault(e, []).append(i)
    D["groups"] = {k: sorted(v) for k, v in sorted(grp.items())}
    D["groupsFlat"] = sorted(i for v in grp.values() for i in v)
    # ★ 「间谍收不到事件」的层集合（运行时）vs「主人在捕获阶段」的层集合（源码）
    D["sawNothingLayers"] = sorted({i for i in IDS
                                    if D["esc"][(i, "alpha")]
                                    ["spySawNothing"] is True})
    D["unreadableCells"] = sorted(
        "%s/%s" % k for k, v in D["esc"].items()
        if v["spySawNothing"] is True)
    D["unreadableHaveReason"] = all(
        c["dpUnreadable"] for v in tB.values() for c in v
        if c["spySawNothing"] is True)
    D["unreadableDpIsNone"] = all(
        v["dp"] is None and v["targetCE"] is None
        for v in D["esc"].values() if v["spySawNothing"] is True)

    allc = [c for v in tA.values() for c in v] + \
           [c for v in tB.values() for c in v]
    sawA = [c for v in tA.values() for c in v]
    sawB = [c for v in tB.values() for c in v if not c["spySawNothing"]]
    D["allInstalled"] = all(c["spyInstalled"] for c in allc)
    D["allSawEvent"] = all(c["eventsSeen"] for c in sawA) and \
        all(c["eventsSeen"] for c in sawB)
    D["allReadDp"] = all(c["dp"] in (True, False) for c in allc if not (
        c["spySawNothing"])) and D["unreadableDpIsNone"]
    D["allReadCE"] = all(c["targetCE"] in (True, False) for c in allc
                         if not c["spySawNothing"])
    D["allHadSelection"] = all(c["selectedIds"] for v in tA.values()
                               for c in v)
    D["dpValues"] = sorted({str(c["dp"]) for c in allc})
    D["ceValues"] = sorted({str(c["targetCE"]) for c in allc})
    D["dpValuesReadable"] = sorted({str(c["dp"]) for c in allc
                                    if not c["spySawNothing"]})
    D["q1SawNothing"] = sum(1 for v in tA.values() for c in v
                            if c["spySawNothing"])
    inj = [c for v in tA.values() for c in v
           if c["injectTook"] is not None]
    D["injectedCells"] = len(inj)
    D["silentCells"] = sum(1 for c in allc if c["injectionSilent"])
    D["injectAllTook"] = bool(inj) and all(c["injectTook"] for c in inj)
    return D


def run_checks(a, st, rw):
    D = derive(rw)
    J = {j["id"]: j for j in a.get("judgments") or []}
    C = []

    def chk(label, cond, got):
        C.append({"label": label, "pass": bool(cond), "got": got})

    # ── 产物层
    chk("产物：判据 8 条且 id 齐全", sorted(J) == sorted(J_IDS),
        {"got": sorted(J)})
    chk("产物：verdict 与预期一致（全 PASS，无 FAIL）",
        all(J[j].get("verdict") == "PASS" for j in J_IDS if j in J),
        {"got": {j: J[j].get("verdict") for j in J_IDS if j in J}})
    chk("产物：每条判据都有非空 evidence 且 evidenceKey 指回自己",
        all(J[j].get("evidence") and J[j].get("evidenceKey") == j
            for j in J_IDS if j in J),
        {"got": {j: J[j].get("evidenceKey") for j in J_IDS if j in J}})
    chk("产物：evidenceIndex 与 judgments 的 evidence 一致",
        (a.get("evidenceIndex") or {}) ==
        {j: J[j].get("evidence") for j in J if j in J},
        {"got": sorted((a.get("evidenceIndex") or {}))})
    chk("产物：探针教训 %s 齐全" % EXPECT_LESSON_IDS,
        sorted(x["id"] for x in (a.get("probeLessons") or []))
        == sorted(EXPECT_LESSON_IDS),
        {"got": [x["id"] for x in (a.get("probeLessons") or [])]})
    chk("产物：观察 ≥5 条", len(a.get("observations") or []) >= 5,
        {"got": len(a.get("observations") or [])})
    chk("产物：本批不新增用户可见缺陷（defects 为空且有说明）",
        a.get("defects") == [] and bool(a.get("defectNote")),
        {"defects": a.get("defects")})
    chk("产物：更正块 %s" % EXPECT_CORRECTION_IDS,
        sorted(c["id"] for c in (a.get("corrections") or []))
        == sorted(EXPECT_CORRECTION_IDS),
        {"got": [c["id"] for c in (a.get("corrections") or [])]})
    chk("产物：C774-1 点名了 772 的拍板项", any(
        "772" in str(c.get("targets")) for c in (a.get("corrections") or [])
        if c["id"] == "C774-1"),
        {"got": [c.get("targets") for c in (a.get("corrections") or [])]})
    chk("产物：★ 每条边界都写明「问① 只证充分性、不证识别性」",
        any("不证识别性" in str(j.get("boundary", ""))
            for j in J.values()),
        {"got": [j.get("boundary") for j in J.values()
                 if j.get("boundary") != "无"]})
    chk("产物：两份 raw 的 sha 都记进产物",
        set(RAW_FILES) <= set((a.get("rawSha") or {})),
        {"got": a.get("rawSha")})
    chk("产物：探针 raw/ 与 probes/ 都在场（R43）",
        all((RAWDIR / f).exists() for f in RAW_FILES)
        and all((PROBEDIR / f).exists() for f in PROBE_FILES),
        {"raw": RAW_FILES, "probes": PROBE_FILES})
    chk("产物：声明本批未改 src/", "未改" in str(a.get("srcDiff", "")),
        {"got": a.get("srcDiff")})

    # ── 静态层
    chk("静态：桌内那个 keydown 监听在 window 冒泡、**不是**捕获",
        st["deskListenerOnWindow"] and not st["deskListenerIsCapture"],
        {"capture": st["deskListenerIsCapture"]})
    chk("静态：守卫判据含 isContentEditable 与三个标签名",
        st["guardPredicateHasContentEditable"]
        and st["guardPredicateHasTagNames"],
        {"ce": st["guardPredicateHasContentEditable"],
         "tags": st["guardPredicateHasTagNames"]})
    chk("静态：守卫排在 Meta+C 与 Delete 之前",
        st["guardBeforeMetaC"] and st["guardBeforeDelete"],
        {"metaC": st["guardBeforeMetaC"], "del": st["guardBeforeDelete"]})
    chk("静态：★ Escape 阶梯排在守卫之后（问② 的全部要害）",
        st["escapeStaircaseAfterGuard"],
        {"guardLine": st["guardLine"],
         "escapeRel": st["escapeStaircaseRelLine"]})
    chk("静态：Escape 阶梯里有 exportPanelOpen 那一档且末尾是 closeWorkspace",
        st["exportPanelLadderStep"] and st["closeWorkspaceInLadder"],
        {"exportStep": st["exportPanelLadderStep"],
         "close": st["closeWorkspaceInLadder"]})
    chk("静态：★ 扫到 9 个 keydown 监听器", st["listenersCount"] == 9,
        {"got": st["listenersCount"]})
    chk("静态：★ 恰好 4 个浮层有自己的 Escape 主人",
        sorted(st["owners"]) == ["modellib", "pathmenu", "phonevcam",
                                 "preset"],
        {"got": sorted(st["owners"])})
    chk("静态：★ 主人分属**两种**注册阶段：捕获 2 个 / 冒泡 2 个",
        st["ownersCapture"] == ["modellib", "phonevcam"]
        and st["ownersBubble"] == ["pathmenu", "preset"],
        {"capture": st["ownersCapture"], "bubble": st["ownersBubble"]})
    chk("静态：捕获阶段的两个主人都带 stopImmediatePropagation",
        all(st["owners"][w]["hasStopImmediate"]
            for w in st["ownersCapture"]),
        {"got": {w: st["owners"][w]["hasStopImmediate"]
                 for w in st["ownersCapture"]}})
    chk("静态：冒泡阶段的两个主人都**不** preventDefault",
        not any(st["owners"][w]["hasPreventDefault"]
                for w in st["ownersBubble"]),
        {"got": {w: st["owners"][w]["hasPreventDefault"]
                 for w in st["ownersBubble"]}})
    chk("静态：★ 没有主人的恰好是 crowd 与 export",
        sorted(set(IDS) - set(st["owners"])) == ["crowd", "export"],
        {"got": sorted(set(IDS) - set(st["owners"]))})
    chk("静态：★ R102 —— 没映射到浮层的 Escape 监听器**每个都有书面理由**，"
        "且集合与登记一致",
        [x["file"] for x in st["unmapped"]] == sorted(
            {f for f, _h in UNMAPPED_REASON}),
        {"got": st["unmappedSet"],
         "withReason": [x["file"] for x in st["unmapped"]]})
    chk("产物：静态层与验收器重读的源码一致",
        sorted((a.get("static") or {}).get("escapeOwners") or {})
        == sorted(st["owners"])
        and (a.get("static") or {}).get("guardLine") == st["guardLine"]
        and (a.get("static") or {}).get(
            "escapeStaircaseAfterGuard") is True,
        {"owners": sorted((a.get("static") or {}).get("escapeOwners") or {}),
         "guardLine": (a.get("static") or {}).get("guardLine")})

    # ── 原始读数层
    chk("原始：两个探针各自两轮逐格一致", D["roundsConsistent"],
        {"A": D["roundsConsistentA"], "B": D["roundsConsistentB"]})
    chk("原始：★ R101 —— 四个臂逐臂数格，且没有哪个臂一次都没跑",
        D["armCells"] == D["armCellsExpected"],
        {"got": D.get("armCells"), "want": D["armCellsExpected"]})
    chk("原始：格集合与登记完全一致（问① %d 格 + 问② %d 格），无失败格"
        % (len(A_CELLS), len(B_CELLS)), not D["badCoverage"],
        {"bad": D["badCoverage"]})
    chk("原始：每格自证（间谍装上；除 4 格按设计收不到外都收到事件；"
        "两个布尔在该读的地方都读得到；目标有选中）",
        D["allInstalled"] and D["allSawEvent"] and D["allReadDp"]
        and D["allReadCE"] and D["allHadSelection"],
        {"installed": D["allInstalled"], "events": D["allSawEvent"],
         "dp": D["allReadDp"], "ce": D["allReadCE"],
         "selected": D["allHadSelection"]})
    chk("原始：★ R99 —— 可读的 dp 读到**两个**不同的值，而读不到的 4 格"
        "**恰好**是捕获阶段那两个层（不是全 None、也不是随机缺）",
        D["dpValuesReadable"] == ["False", "True"]
        and D["dpValues"] == ["False", "None", "True"]
        and D["ceValues"] == ["False", "None", "True"]
        and len(D["unreadableCells"]) == 4
        and D["unreadableDpIsNone"],
        {"readable": D["dpValuesReadable"], "all": D["dpValues"],
         "unreadable": D["unreadableCells"]})
    chk("原始：★ 注入格**无一格静默失效**，且每个都 took（%d 格）"
        % D["injectedCells"],
        D["silentCells"] == 0 and D["injectAllTook"],
        {"silent": D["silentCells"], "allTook": D["injectAllTook"]})
    chk("原始：★ 臂 A 同会话基线 6/6 格 dp=true、targetCE=false",
        len(D["base"]) == 6
        and all(v["dp"] is True for v in D["base"].values())
        and all(v["targetCE"] is False for v in D["base"].values()),
        {"got": {i: D["base"][i] for i in IDS}})
    chk("原始：★ 臂 B α 注入 30/30 格 targetCE=true 且 dp 从 true 变 false",
        len(D["alpha"]) == 30
        and all(v["targetCE"] is True and v["dp"] is False
                for v in D["alpha"].values()),
        {"n": len(D["alpha"]),
         "bad": [k for k, v in D["alpha"].items()
                 if v["targetCE"] is not True or v["dp"] is not False]})
    chk("原始：★ 臂 B 注入后对象数与选中集**零变化**（30/30）",
        all(v["objectsDelta"] == [0] and v["selectedDelta"] == [0]
            for v in D["alpha"].values()),
        {"bad": [k for k, v in D["alpha"].items()
                 if v["objectsDelta"] != [0]
                 or v["selectedDelta"] != [0]]})
    chk("原始：★ 臂 C β 的 isContentEditable **继承**成立（6/6，"
        "根 true → 落点 true → dp=false）",
        len(D["beta"]) == 6
        and all(v["rootCE"] == ["True"] and v["activeCE"] == ["True"]
                and v["targetCE"] is True and v["dp"] is False
                for v in D["beta"].values()),
        {"got": {i: D["beta"][i] for i in IDS}})
    chk("原始：★ 臂 D 中性键 F2 读到 dp=false（6/6）",
        len(D["neutral"]) == 6
        and all(v["dp"] is False for v in D["neutral"].values()),
        {"got": {i: D["neutral"][i]["dp"] for i in IDS}})
    chk("原始：★ 臂 D **间谍确实收到了 F2**（R100：不只看 dp，还要看收没收到）",
        all(v["sawNeutralKey"] and all(e >= 1 for e in v["eventsSeen"])
            for v in D["neutral"].values()),
        {"got": {i: {"saw": D["neutral"][i]["sawNeutralKey"],
                     "events": D["neutral"][i]["eventsSeen"]}
                 for i in IDS}})
    chk("原始：臂 E β 落在可编辑控件上 3/3 格 dp=false（β 不过宽）",
        len(D["betaEd"]) == 3
        and all(v["dp"] is False and v["targetCE"] is True
                for v in D["betaEd"].values()),
        {"got": D["betaEd"]})
    chk("原始：★ 问② 的 targetCE 逐格：间谍收到事件的那 8 格里 "
        "arm=none ⟹ false、arm=alpha ⟹ true",
        all(D["esc"][(i, "none")]["targetCE"] is False
            and D["esc"][(i, "alpha")]["targetCE"] is True
            for i in IDS
            if not D["esc"][(i, "alpha")]["spySawNothing"]),
        {"got": {"%s/%s" % k: v["targetCE"] for k, v in D["esc"].items()}})
    chk("原始：★ 交叉预测 —— 「间谍收不到事件」的层集合，**恰好等于**"
        "「静态普查里主人在捕获阶段」的层集合",
        D["sawNothingLayers"] == sorted(st["ownersCapture"])
        and D["unreadableHaveReason"],
        {"runtimeSawNothing": D["sawNothingLayers"],
         "staticCaptureOwners": sorted(st["ownersCapture"])})
    chk("原始：★ 读不到 dp 的 4 格**有书面理由**，且它们的三态读数仍然有效",
        D["unreadableHaveReason"]
        and all(D["esc"][(i, a)]["outcome"] in
                ("deskGone", "layerClosedOnly", "nothing")
                for i in D["sawNothingLayers"] for a in ("none", "alpha")),
        {"unreadable": D["unreadableCells"],
         "reason": D["unreadableHaveReason"]})
    chk("原始：问① 的 51 格**每一格**都收到了事件（掐断传播只发生在问② 的 4 格）",
        D["q1SawNothing"] == 0, {"q1SawNothing": D["q1SawNothing"]})
    chk("原始：问② 三态读数合法（deskGone / layerClosedOnly / nothing）",
        all(v["outcome"] in ("deskGone", "layerClosedOnly", "nothing")
            for v in D["esc"].values()),
        {"got": {"%s/%s" % k: v["outcome"]
                 for k, v in D["esc"].items()}})
    chk("原始：★ 四个后果桶各归其位、互斥、**并集铺满** 6 个浮层",
        D["groups"] == {"fixesD8ButDeadKey": ["crowd"],
                        "fixesD8Cleanly": ["pathmenu", "preset"],
                        "noChange": ["modellib", "phonevcam"],
                        "regression": ["export"]}
        and D["groupsFlat"] == sorted(IDS),
        {"got": D["groups"]})
    chk("原始：★ export 注入后变**死键**（无注入时是「只关层、桌还在」）",
        D["esc"][("export", "none")]["outcome"] == "layerClosedOnly"
        and D["esc"][("export", "alpha")]["outcome"] == "nothing"
        and D["esc"][("export", "alpha")]["dp"] is False
        and D["esc"][("export", "alpha")]["panelPresent"] is True,
        {"got": {"none": D["esc"][("export", "none")],
                 "alpha": D["esc"][("export", "alpha")]}})
    chk("原始：★ crowd 注入后不再丢工作区、但成了死键（无注入时是 D8）",
        D["esc"][("crowd", "none")]["outcome"] == "deskGone"
        and D["esc"][("crowd", "alpha")]["outcome"] == "nothing"
        and D["esc"][("crowd", "alpha")]["deskOpen"] is True,
        {"got": {"none": D["esc"][("crowd", "none")],
                 "alpha": D["esc"][("crowd", "alpha")]}})
    chk("产物：★ 与验收器独立重算一致（臂 B / 臂 C / 问② 分组）",
        (a.get("q1") or {}).get("armB_alphaBlocks", {}).get("allDpFalse")
        is True
        and (a.get("q1") or {}).get("armC_betaInheritance", {}
                                    ).get("landingInherits") == 6
        and (a.get("q2") or {}).get("groups") == D["groups"],
        {"q1B": (a.get("q1") or {}).get("armB_alphaBlocks"),
         "q1C": (a.get("q1") or {}).get("armC_betaInheritance"),
         "q2groups": (a.get("q2") or {}).get("groups")})
    chk("产物：★ 证据 J5/J6/J7 与验收器重算的三态逐格一致",
        (a.get("evidenceIndex") or {}).get("J5", {}).get("perDisclosure")
        == {i: D["esc"][(i, "none")] for i in IDS},
        {"got": sorted((a.get("evidenceIndex") or {}).get("J5", {})
                       .get("perDisclosure") or {})})

    # ── README / 台账
    if not README.exists():
        chk("README 存在", False, "缺 README.md")
    else:
        rd = README.read_text(encoding="utf-8")
        chk("README：不含替换字符 U+FFFD", FFFD not in rd,
            {"count": rd.count(FFFD)})
        for need in ("C774-1", "6/6", "defaultPrevented", "R100", "F2",
                     "死键", "不证识别性"):
            chk("README 提到「%s」" % need, need in rd, None)
        bare = [ln for ln in rd.split("\n")
                if re.match(r"^\|\s*\d+[a-z]?\s*\|", ln)]
        chk("README：表格首格没有裸数字（pre-commit 正则会拦）", not bare,
            {"bare": bare[:3]})
    if not LEDGER.exists():
        chk("台账存在", False, "缺台账")
    else:
        ll = LEDGER.read_text(encoding="utf-8")
        lines = [ln for ln in ll.split("\n")
                 if ln.startswith("| Batch 774 ")]
        chk("台账：Batch 774 恰好一行", len(lines) == 1,
            {"count": len(lines)})
        if lines:
            chk("台账：该行不含 U+FFFD", FFFD not in lines[0],
                {"count": lines[0].count(FFFD)})
            chk("台账：首格是 `| Batch 774 |`",
                re.match(r"^\|\s*Batch 774\s*\|", lines[0]) is not None,
                {"head": lines[0][:60]})
            chk("台账：恰好 3 列", lines[0].count("|") == 4,
                {"pipes": lines[0].count("|")})
        chk("台账：历史 U+FFFD 仍在 9 处", ll.count(FFFD) == 9,
            {"count": ll.count(FFFD)})
    return C


def negative_controls(a, st, rw):
    out = []

    def sig(obj):
        """derive() 的输出里有**元组键**，JSON 不收 ⟹ 键统一压成字符串。"""
        if isinstance(obj, dict):
            return {("/".join(str(x) for x in k) if isinstance(k, tuple)
                     else str(k)): sig(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [sig(x) for x in obj]
        if isinstance(obj, set):
            return sorted(str(x) for x in obj)
        return obj

    baseSig = json.dumps(sig(derive(rw)), sort_keys=True, default=str)

    def run(name, mutate, kw):
        rr = copy.deepcopy(rw)
        mutate(rr)
        # ★ 对照自证：这一次变更**到底有没有真的改动数据**。
        #   改错字段名（raw 里没有那个键）会让变更静默失效，
        #   然后被判成「判据漏放」——真凶是对照自己。必须能区分这两种。
        try:
            newSig = json.dumps(sig(derive(rr)), sort_keys=True,
                                default=str)
            changed = (newSig != baseSig)
        except Exception:  # noqa: BLE001
            changed = True
        try:
            cs = run_checks(a, st, rr)
        except SystemExit as e:
            out.append({"name": name, "caught": True, "kwMatchedCount": 1,
                        "mutatedAnything": changed, "why": str(e)[:80]})
            return
        hit = [c for c in cs if kw in c["label"]]
        out.append({"name": name, "kwMatchedCount": len(hit),
                    "kwMatchedAnyLabel": bool(hit), "mutatedAnything": changed,
                    "caught": bool(hit) and not any(c["pass"] for c in hit),
                    "expectFailOn": kw,
                    "stillPassing": [c["label"] for c in hit if c["pass"]]})

    def everyA(rr, fn, only=None):
        for rd in rr["A"]["rounds"]:
            for r in rd["rows"]:
                if r.get("SKIPPED") or (only and not only(r)):
                    continue
                fn(r)

    def everyB(rr, fn, only=None):
        for rd in rr["B"]["rounds"]:
            for r in rd["rows"]:
                if r.get("SKIPPED") or (only and not only(r)):
                    continue
                fn(r)

    def m_alphaDpTrue(rr):
        """谎称 α 注入后守卫没挡住 ⟹ 臂 B 的 dp 判据必须红"""
        everyA(rr, lambda r: r.__setitem__("defaultPrevented", True),
               only=lambda r: r.get("arm") == "alpha")

    def m_alphaSideEffect(rr):
        """谎称 α 注入后对象还是被删了 ⟹ 「零变化」判据必须红"""
        everyA(rr, lambda r: r.__setitem__("objectsDelta", -1),
               only=lambda r: r.get("arm") == "alpha"
               and r.get("key") == "Delete")

    def m_betaInheritFalse(rr):
        """谎称 isContentEditable 没有继承 ⟹ 臂 C 必须红"""
        def f(r):
            if r.get("arm") == "beta":
                (r.setdefault("inject") or {})["activeCE"] = False
        everyA(rr, f)

    def m_neutralNoKey(rr):
        """★ R100 的关键阴性对照：把中性臂的 F2 从**键流**里删掉。
        「键根本没送到」与「桌内不处理」都会得 dp=false ⟹ 只看 dp 的判据
        一定是漏放的，而加强后的判据必须红。"""
        def f(r):
            if r.get("arm") == "neutral":
                r["keysSeen"] = [x for x in (r.get("keysSeen") or [])
                                 if x != NEUTRAL_KEY]
        everyA(rr, f)

    def m_neutralDpTrue(rr):
        def f(r):
            if r.get("arm") == "neutral":
                r["defaultPrevented"] = True
        everyA(rr, f)

    def m_baseFalse(rr):
        def f(r):
            if r.get("arm") == "base":
                r["defaultPrevented"] = False
        everyA(rr, f)

    def m_exportNotDead(rr):
        """谎称 export 注入后还能关面板 ⟹ 「变死键」判据必须红"""
        def f(r):
            if r.get("id") == "export" and r.get("arm") == "alpha":
                r["outcome"] = "layerClosedOnly"
                r["panelPresent"] = False
        everyB(rr, f)

    def m_exportNoChange(rr):
        """谎称 export 对方向① **无变化** ⟹ 四个后果桶必须红。

        ★ 四个字段都要对齐：只改其中一部分，签名就不相等，分类落到
        `regression`（原样），**这一格就等于没改**。第一版就踩了这个 ——
        阴性对照「没让任何判据变红」的原因不是判据不灵，是它自己没改成。
        """
        def f(r):
            if r.get("id") == "export" and r.get("arm") == "none":
                # ★ 字段名必须是 raw 里**真有的**那个：第一版写成 r["dp"]，
                #   而 `cB()` 读的是 `r["defaultPrevented"]` ⟹ 这一格
                #   等于没改，然后被判成「判据漏放」——真凶是对照自己。
                r["defaultPrevented"] = False
                r["outcome"] = "nothing"
                r["deskOpen"] = True
                r["panelPresent"] = True
        everyB(rr, f)

    def m_roundsDiffer(rr):
        rr["A"]["rounds"][1]["rows"][0]["defaultPrevented"] = \
            not rr["A"]["rounds"][0]["rows"][0]["defaultPrevented"]

    def m_allNone(rr):
        everyA(rr, lambda r: r.__setitem__("defaultPrevented", None))
        everyB(rr, lambda r: r.__setitem__("defaultPrevented", None))

    def m_injectionSilent(rr):
        """谎称有一格注入静默没生效 ⟹ 「无一格静默失效」必须红"""
        everyA(rr, lambda r: r.__setitem__("injectionSilent", True),
               only=lambda r: r.get("arm") == "alpha"
               and r.get("id") == "crowd" and r.get("key") == "Meta+c")

    def m_dropArm(rr):
        """★ R101：把中性臂整臂删掉 ⟹ 「逐臂数格」必须红"""
        for rd in rr["A"]["rounds"]:
            rd["rows"] = [r for r in rd["rows"]
                          if r.get("arm") != "neutral"]

    def m_noSelection(rr):
        everyA(rr, lambda r: r.__setitem__("selectedIds", []),
               only=lambda r: r.get("arm") == "beta"
               and r.get("id") == "modellib")

    def m_sawNothingLied(rr):
        """谎称「捕获阶段那个层其实收到了事件」⟹ 交叉预测必须红。"""
        everyB(rr, lambda r: r.__setitem__("spySawNothing", False),
               only=lambda r: r.get("id") == "phonevcam"
               and r.get("arm") == "alpha")

    def m_dropUnreadableReason(rr):
        """把「dp 读不到」的书面理由抹掉 ⟹ 那条判据必须红。"""
        everyB(rr, lambda r: r.__setitem__("dpUnreadable", None),
               only=lambda r: r.get("id") == "modellib")

    run("谎称 α 注入后守卫没挡住（dp 改回 true）", m_alphaDpTrue,
        "臂 B α 注入 30/30 格")
    run("谎称 α 注入后对象还是被删了", m_alphaSideEffect, "零变化")
    run("谎称 isContentEditable 没有沿 DOM 继承", m_betaInheritFalse,
        "臂 C β 的 isContentEditable")
    run("★ R100：把中性臂的 F2 从键流里删掉（键没送到 vs 桌内不处理）",
        m_neutralNoKey, "间谍确实收到了 F2")
    run("中性臂 dp 改成 true（读数方法的前提被破坏）", m_neutralDpTrue,
        "臂 D 中性键 F2 读到 dp=false")
    run("谎称臂 A 基线没跑到分支", m_baseFalse, "臂 A 同会话基线")
    run("谎称 export 注入后还能关面板", m_exportNotDead, "export 注入后变**死键**")
    run("把 export 混进 noChange 组", m_exportNoChange, "四个后果桶")
    run("第二轮的读数被改掉", m_roundsDiffer, "两轮逐格一致")
    run("★ R99：把 defaultPrevented 全改成 None", m_allNone,
        "R99 ——")
    run("谎称有一格注入静默没生效", m_injectionSilent, "静默失效")
    run("★ R101：把中性臂整臂删掉", m_dropArm, "逐臂数格")
    run("把一格的目标选中抹掉", m_noSelection, "目标有选中")
    run("★ 谎称捕获阶段那个层其实收到了事件（源码与运行时两条独立路径"
        "必须对上）", m_sawNothingLied, "交叉预测")
    run("把「dp 读不到」的书面理由抹掉", m_dropUnreadableReason,
        "读不到 dp 的 4 格")

    def aproduct(name, mutate, kw):
        aa = copy.deepcopy(a)
        mutate(aa)
        cs = run_checks(aa, st, rw)
        hit = [c for c in cs if kw in c["label"]]
        out.append({"name": name, "kwMatchedCount": len(hit),
                    "kwMatchedAnyLabel": bool(hit),
                    "caught": bool(hit) and not any(c["pass"] for c in hit),
                    "expectFailOn": kw,
                    "stillPassing": [c["label"] for c in hit if c["pass"]]})

    aproduct("篡改一条判据的 evidence",
             lambda x: [j.update(evidence={"x": 1}) for j in x["judgments"]
                        if j["id"] == "J7"], "evidenceIndex 与 judgments")
    aproduct("删掉一个判据",
             lambda x: x.__setitem__("judgments",
                                     [j for j in x["judgments"]
                                      if j["id"] != "J6"]), "判据 8 条")
    aproduct("删掉更正 C774-1",
             lambda x: x.__setitem__("corrections", []), "更正块")
    aproduct("删掉一条探针教训",
             lambda x: x.__setitem__(
                 "probeLessons",
                 [y for y in x["probeLessons"] if y["id"] != "R100"]),
             "探针教训")
    # 关键词必须**唯一命中一条**判据（R86）：「不证识别性」同时出现在
    # 「每条边界都写明…」与「README 提到…」两条里 ⟹ 改用前者的独有片段。
    aproduct("删掉「不证识别性」这条边界（把充分性吹成识别性）",
             lambda x: [j.__setitem__("boundary", "无")
                        for j in x["judgments"] if j["id"] == "J1"],
             "每条边界都写明")
    aproduct("给本批塞一个假的新缺陷",
             lambda x: x.__setitem__("defects", [{"id": "DX"}]),
             "本批不新增用户可见缺陷")
    aproduct("篡改静态层的守卫行号",
             lambda x: x["static"].__setitem__("guardLine", 1),
             "静态层与验收器重读的源码一致")

    def text_run(name, path, old, new, kw):
        if not path.exists():
            out.append({"name": name, "caught": False, "kwMatchedCount": 0,
                        "why": "文件不存在"})
            return
        orig = path.read_text(encoding="utf-8")
        if old not in orig:
            out.append({"name": name, "caught": False, "kwMatchedCount": 0,
                        "why": "锚点没找到：%r" % old[:40]})
            return
        try:
            path.write_text(orig.replace(old, new, 1), encoding="utf-8")
            cs = run_checks(a, st, rw)
            hit = [c for c in cs if kw in c["label"]]
            out.append({"name": name, "kwMatchedCount": len(hit),
                        "kwMatchedAnyLabel": bool(hit),
                        "caught": bool(hit) and not any(c["pass"] for c in hit),
                        "expectFailOn": kw,
                        "stillPassing": [c["label"] for c in hit
                                         if c["pass"]]})
        finally:
            path.write_text(orig, encoding="utf-8")

    text_run("把台账 Batch 774 行改名", LEDGER, "| Batch 774 ",
             "| Batch 774X ", "台账：Batch 774 恰好一行")
    if README.exists():
        rd = README.read_text(encoding="utf-8")
        anchor = next((ln for ln in rd.split("\n") if ln.startswith("|")), "")
        text_run("把 README 表格首格改成裸数字", README, anchor,
                 "| 774 | x | y |", "首格没有裸数字")
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
    except Exception as e:  # noqa: BLE001
        rw, rawErr = {}, str(e)
    checks = run_checks(a, st, rw) if not rawErr else [
        {"label": "原始读数可用（两份 raw + 三个 probes/）", "pass": False,
         "got": rawErr}]
    neg = [] if rawErr else negative_controls(a, st, rw)
    kw_bad = [n["name"] for n in neg if n.get("kwMatchedCount") != 1]
    inert_bad = [n["name"] for n in neg if n.get("mutatedAnything") is False]
    npass = sum(1 for c in checks if c["pass"])
    total = len(checks)
    neg_ok = sum(1 for n in neg
                 if n["caught"] and n.get("kwMatchedCount") == 1
                 and n.get("mutatedAnything") is not False)
    ok = npass == total and neg_ok == len(neg)
    REPORT.write_text(json.dumps(
        {"batch": 774, "checks": checks, "pass": npass, "total": total,
         "negativeControls": neg, "negativeCaught": neg_ok,
         "negativeTotal": len(neg), "negativeKwBroken": kw_bad,
         "negativeInert": inert_bad,
         "rawError": rawErr, "ok": ok}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    for c in checks:
        if not c["pass"]:
            print("FAIL  %s  got=%s" % (c["label"], json.dumps(
                c["got"], ensure_ascii=False)[:300]))
    print("\n验收 %d/%d 通过" % (npass, total))
    print("阴性对照 %d/%d 全部拦下" % (neg_ok, len(neg)))
    for n in neg:
        if n.get("mutatedAnything") is False:
            print("  ✗ 对照自己没改成（改的字段名 raw 里不存在）：%s" % n["name"])
        elif n.get("kwMatchedCount") != 1:
            print("  ✗ 阴性对照自身写坏（关键词命中 %s 条判据）：%s"
                  % (n.get("kwMatchedCount"), n["name"]))
        elif not n["caught"]:
            print("  ✗ 漏放：%s  (%s)" % (n["name"],
                                         n.get("why")
                                         or n.get("expectFailOn")))
    print("batch 774 %s" % ("通过" if ok else "不通过"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
