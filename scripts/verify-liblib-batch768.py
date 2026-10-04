"""batch 768 验收器：关闭 disclosure 浮层时焦点会不会回到触发器

三层结构（与 753–767 同）：
  1. **静态层** —— 从 `src/` **独立**复核实现事实：keydown 监听的阶段与
     「是否停止传播」（本批的核心机制证据），`useLayerFocus` 的归还焦点
     样板与它的消费者
  2. **产物层** —— 判据条数与 verdict、缺陷/扩宽、观察、教训、README 结构、
     台账行、表格首格不许裸数字
  3. **原始读数交叉核对** —— 从 `raw/vb768a.json`（基线）与
     `raw/vb768b.json`（注入）**按正确键名重算** 12 格的分类、逐浮层的
     焦点归还结论、注入改动了哪几格；缺失时**判失败而不是通过**

⚠ 本批盯住五件容易自欺的事：
  - **「焦点在触发器上」可能是 no-op**。本批的判别式是：注入一条
    「真的会挪焦点」的对照，看那一格读数变不变。产物必须保留这条撤回
    （J5/O1），不许把那 3 格算成「做对了」。
  - **分母是 6 个 disclosure，但只有 2 个真的测到了**。产物必须把
    「被 D3 遮住」与「触发器已卸载、物理上不可能」两类单列，
    不许把它们算成通过。
  - **`all([])` 是 True**：每个分类列表都显式判非空，并断言
    12 格的四个分类**恰好铺满**、四个焦点结论桶**恰好铺满 6 个浮层**。
  - **D8 有两种机制**（没有 Esc 处理 / 有但不停止传播），修法不同。
    产物只写一种机制就要判失败。
  - **更正 767 的三处**（O3 的写法数、范围表述的 aria-expanded 份数、
    J9 补干净）必须都在 README 与判据里，不许悄悄改写历史批次。

判据 **14 条（8 PASS / 6 FAIL）**。
"""
import copy
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch768-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAWDIR = OUTDIR / "raw"
PROBEDIR = OUTDIR / "probes"
README = OUTDIR / "README.md"
LEDGER = ROOT / "docs/research/VERIFICATION_LEDGER.md"
PREV_RAW = (ROOT / "docs/research/liblib-canvas-batch767-2026-10-01"
            / "raw" / "vb767a.json")

RAW_FILES = ["vb768a.json", "vb768b.json"]
PROBE_FILES = ["dbg768a.py", "dbg768b.py", "mk768audit.py"]
BARE_NUM_CELL = re.compile(r"^\|\s*\d+[a-z]?\s*\|")
FFFD = "�"

IDS = ["export", "preset", "pathmenu", "phonevcam", "crowd", "modellib"]
MODES = ["inside", "trigger"]
CELLS = [(i, m) for i in IDS for m in MODES]
EXPECT_FAIL_IDS = ["J3", "J6", "J7", "J9", "J10", "J12"]
EXPECT_PASS_IDS = ["J1", "J2", "J4", "J5", "J8", "J11", "J13", "J14"]
EXPECT_LESSON_IDS = ["R75", "R76", "R77", "R78", "R79", "R80"]
OTHER_STATES = ["crowdPanelOpen", "modelLibraryOpen", "phoneVcamOpen",
                "presetPanelLeft", "pathMenuLeft"]
CLASSES = ["desk-lost", "panel-stuck", "closed-focus-on-trigger",
           "closed-focus-on-body", "closed-focus-in-dialog",
           "closed-focus-outside-dialog"]


def src(p):
    return (ROOT / p).read_text(encoding="utf-8")


def line_of(t, n, s=0):
    i = t.find(n, s)
    return -1 if i < 0 else t.count("\n", 0, i)


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
def fn_body(text, fn, span=3000):
    """取 `const <fn> = (…) => { … }` 的函数体（按花括号配对）。

    ★ 不许用「注册点往后看 N 个字符」：捕获阶段那几处的函数体**定义在
      注册点之前**（`DirectorViewport.tsx:2742` 定义、`:2748` 注册），
      往前看会漏判 `stopImmediatePropagation` —— 汇编器第一版就这么错的。
    """
    m = re.search(r"const\s+" + re.escape(fn) + r"\s*=\s*\([^)]*\)\s*=>\s*\{",
                  text)
    if not m:
        return None
    i = m.end() - 1
    depth = 0
    for j in range(i, min(len(text), i + span)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i:j + 1]
    return None


def static_side():
    desk = src("src/components/director/DirectorDesk.tsx")
    tl = src("src/components/director/DirectorTimeline.tsx")
    vcam = src("src/components/director/DirectorPhoneVcamPanel.tsx")
    vp = src("src/components/director/DirectorViewport.tsx")
    lf = src("src/hooks/useLayerFocus.ts")

    win_kd = re.compile(r'(window|document)\.addEventListener\(\s*"keydown"'
                        r'\s*,\s*(\w+)\s*(?:,\s*(true|false))?\s*\)')
    listeners = []
    for fname, text in (("DirectorDesk.tsx", desk), ("DirectorTimeline.tsx", tl),
                        ("DirectorPhoneVcamPanel.tsx", vcam),
                        ("DirectorViewport.tsx", vp)):
        for m in win_kd.finditer(text):
            fn, cap = m.group(2), (m.group(3) or "false") == "true"
            body = fn_body(text, fn)
            listeners.append({
                "file": fname,
                "line": text.count("\n", 0, m.start()) + 1,
                "fn": fn, "capture": cap,
                "bodyFound": body is not None,
                "stops": bool(body) and (
                    "stopImmediatePropagation()" in body
                    or "stopPropagation()" in body),
                "prevents": bool(body) and "preventDefault()" in body,
            })
    cap = [l for l in listeners if l["capture"]]
    bub = [l for l in listeners if not l["capture"]]

    # 导演台阶梯：另外五个浮层状态 0 处引用；导出面板恰好一档且在 close 之前
    other_hits = {k: len(re.findall(re.escape(k), desk)) for k in OTHER_STATES}
    export_tier = line_of(desk, "if (exportPanelOpen) {")
    close_ws = line_of(desk, "closeWorkspace();")
    editable_gate = line_of(desk, "if (isEditable) return;")

    # useLayerFocus：归还焦点的样板 + 它的消费者
    consumers = sorted(
        p.name for p in (ROOT / "src").rglob("*.tsx")
        if re.search(r"useLayerFocus\((ref|panelRef)", p.read_text(
            encoding="utf-8")))
    director_uses = [p.name for p in
                     (ROOT / "src/components/director").rglob("*.tsx")
                     if "useLayerFocus" in p.read_text(encoding="utf-8")]

    return {
        "listeners": listeners,
        "total": len(listeners),
        "captureCount": len(cap),
        "bubbleCount": len(bub),
        "allBodiesFound": all(l["bodyFound"] for l in listeners),
        "captureStops": ["%s:%d" % (l["file"], l["line"]) for l in cap
                         if l["stops"]],
        "bubbleStops": ["%s:%d" % (l["file"], l["line"]) for l in bub
                        if l["stops"]],
        "bubblePrevents": ["%s:%d" % (l["file"], l["line"]) for l in bub
                           if l["prevents"]],
        "combos": sorted({"%s/%s" % ("capture" if l["capture"] else "bubble",
                                     "stops" if l["stops"] else "leaks")
                          for l in listeners}),
        "otherStateHits": other_hits,
        "otherStateTotal": sum(other_hits.values()),
        "exportTierCount": len(re.findall(r"if \(exportPanelOpen\)", desk)),
        "exportTierLine": export_tier,
        "closeWorkspaceLine": close_ws,
        "tierBeforeClose": 0 <= export_tier < close_ws,
        "isEditableGateLine": editable_gate,
        # isEditable 早退排在 Escape 分支之前（765 的 D3 机制，本批 D3 扩宽的根）
        "escapeGateLine": line_of(desk, 'if (event.key !== "Escape") return;'),
        "useLayerFocusOpenerFocus": "opener.focus()" in lf,
        "useLayerFocusIsConnected": "root.isConnected" in lf,
        "useLayerFocusRaft": "requestAnimationFrame" in lf,
        "useLayerFocusNamesBodyDrop": "焦点掉到 body" in lf,
        "useLayerFocusConsumers": consumers,
        "directorUsesUseLayerFocus": director_uses,
    }


# ═════════════════════ 2. 原始读数交叉核对 ═════════════════════
def raw_files():
    out = {}
    for f in RAW_FILES:
        p = RAWDIR / f
        if not p.exists():
            raise SystemExit("FATAL 缺原始读数 %s" % p)
        out[f] = json.loads(p.read_text(encoding="utf-8"))
    return out


def classify(st, desk):
    """从「导演台还在吗 / 面板还在吗 / 焦点在哪」现算分类（不复用汇编器）。"""
    if (st or {}).get("open") is False or (desk or {}).get("open") is False:
        return "desk-lost"
    st = st or {}
    if st.get("panelPresent") is True:
        return "panel-stuck"
    if st.get("panelPresent") is not False:
        return "unknown"
    a = st.get("active") or {}
    if a.get("isTrigger") is True:
        return "closed-focus-on-trigger"
    if a.get("isBody") is True:
        return "closed-focus-on-body"
    if a.get("inDialog") is True:
        return "closed-focus-in-dialog"
    return "closed-focus-outside-dialog"


def raw_side_from(files):
    a, b = files["vb768a.json"], files["vb768b.json"]

    def grid(raw, key):
        g = {}
        for rd in raw["rounds"]:
            for r in rd.get(key) or []:
                g.setdefault((r.get("id"), r.get("mode")), []).append(r)
        return g

    gA, gB = grid(a, "rows"), grid(b, "rows")
    out = {"roundsA": len(a["rounds"]), "roundsB": len(b["rounds"]),
           "missing": [], "failedA": [], "failedB": [], "cells": {}}
    for k in CELLS:
        if k not in gA or k not in gB:
            out["missing"].append("%s/%s" % k)
            continue
        for tag, g, key in (("A", gA, "failedA"), ("B", gB, "failedB")):
            for r in g[k]:
                if r.get("FAILED"):
                    out[key].append("%s/%s" % k)
        cells = []
        for i in range(2):
            ra, rb = gA[k][i], gB[k][i]
            base = classify(ra.get("after"), ra.get("desk"))
            inj = classify(rb.get("after2"), rb.get("desk"))
            log = rb.get("inj") or []
            cells.append({
                "base": base, "inj": inj, "changed": base != inj,
                "opened": (ra.get("before") or {}).get("panelPresent")
                          is True,
                "focusPlaced": (ra.get("focus") or {}).get("focused") is True,
                "focusWasInPanel": ((ra.get("before") or {}).get("active")
                                    or {}).get("inPanel") is True,
                "focusWasOnTrigger": ((ra.get("before") or {}).get("active")
                                      or {}).get("isTrigger") is True,
                "focusableTag": (ra.get("focus") or {}).get("tag"),
                "focusableType": (ra.get("focus") or {}).get("type"),
                "focusables": (ra.get("focus") or {}).get("total"),
                "ariaExpanded": (ra.get("before") or {}).get(
                    "triggerAriaExpanded"),
                "injLog": log,
                # 注入到底调没调 focus()：**看记录里有没有 focused 键**
                "injFocusCalled": any("focused" in r for r in log),
                "injFocusSucceeded": any(r.get("focused") is True
                                         for r in log),
                "baseFocus": (ra.get("after") or {}).get("active") or {},
                "injFocus": (rb.get("after2") or {}).get("active") or {},
            })
        out["cells"]["%s/%s" % k] = cells

    def all_cells(pred):
        """两轮都满足的格。

        ★ 不要按「变体名」过滤成两半再拼：767 在字符串排序上踩过
          （`sorted(["D8","D9","D10"])` 不是期望顺序），这里一律用集合比。
        """
        return [k for k in CELLS
                if all(pred(c) for c in out["cells"]["%s/%s" % k])]

    out["deskLost"] = ["%s/%s" % k for k in
                       all_cells(lambda c: c["base"] == "desk-lost")]
    out["stuck"] = ["%s/%s" % k for k in
                    all_cells(lambda c: c["base"] == "panel-stuck")]
    out["onTrigger"] = ["%s/%s" % k for k in
                        all_cells(
                            lambda c: c["base"] == "closed-focus-on-trigger")]
    out["onBody"] = ["%s/%s" % k for k in
                     all_cells(lambda c: c["base"] == "closed-focus-on-body")]
    out["changedByInjection"] = [k for k in CELLS
                                 if any(c["changed"] for c in
                                        out["cells"]["%s/%s" % k])]
    out["changedByInjection"] = ["%s/%s" % k for k in out["changedByInjection"]]
    out["insensitive"] = [k for k in CELLS
                          if not any(c["changed"] for c in
                                     out["cells"]["%s/%s" % k])]
    out["insensitive"] = ["%s/%s" % k for k in out["insensitive"]]

    # 逐浮层的焦点归还结论（分母 6）
    per = {}
    for i in IDS:
        cs = out["cells"]["%s/inside" % i]
        if any(c["base"] == "unknown" for c in cs):
            per[i] = "unknown"
        elif all(c["base"] == "panel-stuck" for c in cs):
            per[i] = "unmeasured-d3-masks-it"
        elif all(c["base"] == "desk-lost" for c in cs):
            per[i] = "impossible-trigger-unmounted"
        elif all(c["base"] == "closed-focus-on-body" for c in cs):
            per[i] = "measured-fails"
        elif all(c["base"] == "closed-focus-on-trigger" for c in cs):
            per[i] = "measured-passes"
        else:
            per[i] = "mixed"
    out["perDisclosure"] = per
    out["implemented"] = [i for i in IDS if per[i] == "measured-passes"]
    out["measuredFails"] = [i for i in IDS if per[i] == "measured-fails"]
    out["unmeasured"] = [i for i in IDS
                         if per[i] == "unmeasured-d3-masks-it"]
    out["impossible"] = [i for i in IDS
                         if per[i] == "impossible-trigger-unmounted"]

    # no-op 判别：触发器变体「焦点在触发器」的读数，注入后必须**仍**是触发器
    vac = []
    for i in IDS:
        cs = out["cells"]["%s/trigger" % i]
        if all(c["base"] == "closed-focus-on-trigger" for c in cs) and \
                all(c["inj"] == "closed-focus-on-trigger" for c in cs) and \
                all(c["injFocusCalled"] for c in cs) and \
                all(c["focusWasOnTrigger"] for c in cs):
            vac.append(i)
    out["vacuous"] = vac

    # 注入纪律：面板没关 ⟹ 不许调 focus；导演台没了 ⟹ 不许调 focus
    out["injectionRespectedNoop"] = all(
        not c["injFocusCalled"] and c["injFocus"] == c["baseFocus"]
        for k in out["stuck"] for c in out["cells"][k])
    out["injectionRespectedUnmounted"] = all(
        not c["injFocusCalled"] and c["injLog"]
        and c["injLog"][0].get("trigThere") is False
        for k in out["deskLost"] for c in out["cells"][k])
    out["injectionFiredWhereItShould"] = all(
        c["injFocusCalled"] and c["injFocusSucceeded"]
        for k in out["onBody"] + out["onTrigger"] for c in out["cells"][k])

    # 跨批：可聚焦控件数
    if PREV_RAW.exists():
        prev = json.loads(PREV_RAW.read_text(encoding="utf-8"))
        pf = {}
        for rd in prev["rounds"]:
            for r in rd.get("results") or []:
                pf.setdefault(r["id"], set()).add(
                    (r.get("afterOpen") or {}).get("panelFocusables"))
        out["prevFocusables"] = {i: sorted(x for x in pf.get(i, [])
                                           if x is not None) for i in IDS}
        out["thisFocusables"] = {
            i: sorted({c["focusables"] for c in
                       out["cells"]["%s/inside" % i]}) for i in IDS}
        out["focusablesAgree"] = all(
            out["prevFocusables"][i] == out["thisFocusables"][i]
            for i in IDS)
        pexp = {r["id"]: (r.get("afterOpen") or {}).get("triggerAriaExpanded")
                for r in prev["rounds"][0]["results"]}
        out["prevAriaExpanded"] = pexp
        out["thisAriaExpanded"] = {
            i: out["cells"]["%s/trigger" % i][0]["ariaExpanded"] for i in IDS}
    return out


def raw_side():
    files = raw_files()
    out = raw_side_from(files)
    out["__raw__"] = files
    return out


# ═════════════════════ 3. 产物层 + 交叉核对 ═════════════════════
def run_checks(a, st, rw):
    ck = []

    def C(label, cond, got=None):
        ck.append({"label": label, "pass": bool(cond), "got": got})

    f = a["findings"]
    J = a["judgments"]
    fr = f["focusRestore"]
    inj = f["injectionContrast"]
    tax = f["escTaxonomy"]
    cb = f["crossBatch"]

    def df(did):
        for x in (a.get("defects") or []) + (a.get("widened") or []):
            if x.get("id") == did:
                return x
        return {}

    def jd(jid):
        for j in J:
            if j["id"] == jid:
                return j
        return {}

    # ── 静态层：keydown 监听的阶段 × 是否停止传播（本批机制证据）
    C("★★ 静态：全仓导演台 keydown 监听 6 处（捕获 3 / 冒泡 3）",
      st["total"] == 6 and st["captureCount"] == 3 and st["bubbleCount"] == 3,
      {"total": st["total"], "cap": st["captureCount"],
       "bub": st["bubbleCount"]})
    C("★★ 静态：每一处监听的函数体都找得到（正则在工作）",
      st["allBodiesFound"], st["listeners"])
    C("★★ 静态：只有两种组合 capture/stops 与 bubble/leaks（D8 机制的地基）",
      st["combos"] == ["bubble/leaks", "capture/stops"], st["combos"])
    C("★★ 静态：捕获阶段 %d 处**全部**停止传播"
      % st["captureCount"],
      len(st["captureStops"]) == st["captureCount"], st["captureStops"])
    C("★★ 静态：冒泡阶段**一处**停止传播的都没有（D8 机制②成立）",
      st["bubbleStops"] == [], st["bubbleStops"])
    C("★ 静态：产物里的监听表与现算的逐项一致（阶段/停止传播）",
      [(l["file"], l["line"], l["capture"], l["stopsPropagation"])
       for l in tax["keydownListeners"]] ==
      [(l["file"], l["line"], l["capture"], l["stops"]) for l in st["listeners"]],
      tax.get("keydownListeners"))
    C("★ 静态：产物的组合集合与现算一致",
      tax.get("combinations") == st["combos"], tax.get("combinations"))
    C("★ 静态：产物说冒泡阶段停止传播数 = 0，与现算一致",
      tax.get("bubbleStopsAny") == [] and st["bubbleStops"] == [],
      tax.get("bubbleStopsAny"))

    # ── 静态层：导演台阶梯
    C("★★ 静态：DirectorDesk 的 Esc 阶梯对另外五个浮层状态 0 处引用",
      st["otherStateTotal"] == 0, st["otherStateHits"])
    C("★★ 静态：阶梯里导出面板那档恰好一处，且排在 closeWorkspace 之前",
      st["exportTierCount"] == 1 and st["tierBeforeClose"],
      {"tier": st["exportTierCount"], "before": st["tierBeforeClose"]})
    C("★ 静态：导演台自己的 keydown 监听在**冒泡**阶段（与 D8 机制②有关）",
      not any(l["file"] == "DirectorDesk.tsx" and l["capture"]
              for l in st["listeners"]), st["listeners"])
    C("★ 静态：isEditable 早退排在 Escape 分支之前（D3 的机制，765 已立）",
      0 <= st["isEditableGateLine"] < st["escapeGateLine"],
      {"isEditable": st["isEditableGateLine"],
       "escGate": st["escapeGateLine"]})
    C("★ 静态：产物说阶梯引用别的浮层状态 0 处，与现算一致",
      tax.get("deskLadderReferencesOtherPanels") == st["otherStateTotal"])

    # ── 静态层：useLayerFocus 样板（D11 的修法依据）
    C("★★ 静态：useLayerFocus 有 opener.focus() / isConnected 守卫 / rAF",
      st["useLayerFocusOpenerFocus"] and st["useLayerFocusIsConnected"]
      and st["useLayerFocusRaft"],
      {"opener": st["useLayerFocusOpenerFocus"],
       "connected": st["useLayerFocusIsConnected"],
       "raf": st["useLayerFocusRaft"]})
    C("★★ 静态：useLayerFocus 的注释里**逐字**写着本批的症状"
      "（焦点掉到 body）", st["useLayerFocusNamesBodyDrop"])
    C("★★ 静态：useLayerFocus 的消费者只有即梦那两个组件，导演台一个没用",
      st["useLayerFocusConsumers"] ==
      ["JimengAiDrawer.tsx", "JimengNodeSummaryPopover.tsx"]
      and st["directorUsesUseLayerFocus"] == [],
      {"consumers": st["useLayerFocusConsumers"],
       "director": st["directorUsesUseLayerFocus"]})

    # ── 产物层：判据
    C("★ 判据 14 条（8 PASS / 6 FAIL）",
      len(J) == 14
      and sum(1 for j in J if j["verdict"] == "PASS") == 8
      and sum(1 for j in J if j["verdict"] == "FAIL") == 6,
      {"n": len(J),
       "pass": sum(1 for j in J if j["verdict"] == "PASS"),
       "fail": sum(1 for j in J if j["verdict"] == "FAIL")})
    got_fail = {j["id"] for j in J if j["verdict"] == "FAIL"}
    got_pass = {j["id"] for j in J if j["verdict"] == "PASS"}
    C("★ FAIL 的判据恰好是 %s" % "/".join(EXPECT_FAIL_IDS),
      got_fail == set(EXPECT_FAIL_IDS), sorted(got_fail))
    C("★ PASS 的判据恰好是 %s" % "/".join(EXPECT_PASS_IDS),
      got_pass == set(EXPECT_PASS_IDS), sorted(got_pass))
    C("★★ 每条判据的 evidence 与 findings 同一份（JSON 往返后再查一遍）",
      all(j.get("evidenceKey") in f and f[j["evidenceKey"]] == j.get("evidence")
          for j in J),
      [j["id"] for j in J
       if not (j.get("evidenceKey") in f
               and f[j["evidenceKey"]] == j.get("evidence"))])
    C("★ 每条判据都有 evidenceKey 与非空 evidence",
      all(j.get("evidenceKey") and j.get("evidence") for j in J))

    # ── D11
    d = df("D11")
    C("★★ D11 在 defects 里，严重度低、标了扩宽 765 的 D4、要改 src",
      bool(d) and d.get("severity") == "低" and d.get("newInThisBatch")
      and d.get("widensD4From765") and d.get("needsSrcChange") is True, d)
    C("★★ D11 有 inRepoExemplar 且指向 useLayerFocus（修法有先例）",
      "useLayerFocus" in (d.get("inRepoExemplar") or ""), d)
    C("★ D11 的 where 每一项行号都有效",
      d and all(ptr_valid(w) for w in d.get("where") or []),
      d.get("where") if d else None)
    C("★★ D11 的 measured 里含「没测到」的 4 个浮层（不许算成通过）",
      d and "没测到" in (d.get("measured") or "")
      and all(x in (d.get("measured") or "")
              for x in ("虚拟相机", "模型库")), d.get("measured") if d else None)

    # ── 焦点归还的四桶（用 raw 现算的）
    C("★★ 焦点归还：**实现 = 0 个**（分母 6）",
      fr.get("implementedRestore") == [] and rw.get("implemented") == [],
      {"artifact": fr.get("implementedRestore"),
       "raw": rw.get("implemented")})
    C("★★ 焦点归还：测到且失败的恰好是虚拟相机 + 模型库",
      sorted(fr.get("measuredAndFails") or []) == sorted(rw["measuredFails"])
      == ["modellib", "phonevcam"],
      {"artifact": fr.get("measuredAndFails"),
       "raw": rw.get("measuredFails")})
    C("★★ 焦点归还：被 D3 遮住的是导出 + 群众",
      sorted(fr.get("unmeasuredBecauseD3") or []) == sorted(rw["unmeasured"])
      == ["crowd", "export"],
      {"artifact": fr.get("unmeasuredBecauseD3"), "raw": rw.get("unmeasured")})
    C("★★ 焦点归还：触发器已卸载的是预设 + 路径菜单",
      sorted(fr.get("impossibleBecauseTriggerUnmounted") or [])
      == sorted(rw["impossible"]) == ["pathmenu", "preset"],
      {"artifact": fr.get("impossibleBecauseTriggerUnmounted"),
       "raw": rw.get("impossible")})
    C("★★ 四个焦点结论桶**恰好铺满 6 个浮层**（all([]) 陷阱）",
      sorted((fr.get("measuredAndFails") or [])
             + (fr.get("unmeasuredBecauseD3") or [])
             + (fr.get("impossibleBecauseTriggerUnmounted") or [])
             + (fr.get("implementedRestore") or [])) == sorted(IDS))
    C("★ 分母说明写明「4 个没被真正测到」",
      "4" in (fr.get("denominatorNote") or "")
      and "没被真正测到" in (fr.get("denominatorNote") or ""))

    # ── 注入对照
    C("★★ 注入改动的格**恰好**是那 2 格（掉 body → 触发器）",
      sorted(inj.get("cellsChangedByInjection") or [])
      == sorted(rw["changedByInjection"])
      == ["modellib/inside", "phonevcam/inside"],
      {"artifact": inj.get("cellsChangedByInjection"),
       "raw": rw["changedByInjection"]})
    C("★★ 注入不改变读数的格恰好 10 格（12 − 2）",
      len(inj.get("cellsInsensitiveToInjection") or [])
      == len(rw["insensitive"]) == 10,
      {"artifact": len(inj.get("cellsInsensitiveToInjection") or []),
       "raw": len(rw["insensitive"])})
    C("★★ 注入在「面板没关」的 2 格上**没调** focus，且焦点读数未变",
      rw["injectionRespectedNoop"] is True)
    C("★★ 注入在「导演台没了」的 5 格上**没能**调 focus（trigThere=false）",
      rw["injectionRespectedUnmounted"] is True)
    C("★★ 注入在「面板关了、触发器还在」的 5 格上都调了且成功",
      rw["injectionFiredWhereItShould"] is True)
    C("★★ 注入说明里写明「挂在 window 捕获阶段」及原因",
      "捕获" in (inj.get("whyCapture") or "")
      and "stopImmediatePropagation" in (inj.get("whyCapture") or ""))

    # ── no-op 撤回（本批最关键的一条）
    C("★★ no-op 判别：触发器变体那 3 格的读数**对注入完全不敏感**",
      sorted(fr["perDisclosure"][i]["triggerVariantIsVacuous"]
             for i in IDS if i in rw["vacuous"]) == [True, True, True]
      and sorted(rw["vacuous"]) == ["export", "modellib", "phonevcam"],
      {"raw": rw["vacuous"],
       "artifact": {i: fr["perDisclosure"][i]["triggerVariantIsVacuous"]
                    for i in rw["vacuous"]}})
    C("★★ J5 明确**撤回**了探针自己打印的「焦点回触发器 ✓」",
      jd("J5").get("verdict") == "PASS"
      and "no-op" in jd("J5").get("statement", "")
      and "撤回" in jd("J5").get("statement", ""))
    C("★ O1 把「平凡读数」记成了方法论",
      any(o.get("id") == "O1" and "平凡" in (o.get("text") or "")
          for o in a.get("observations") or []))

    # ── D8 的两种机制
    w8 = df("D8")
    C("★★ D8 从 1/6 扩到 3/6，新增成员是 preset + pathmenu",
      bool(w8) and w8.get("from") == "1/6" and w8.get("to") == "3/6"
      and sorted(w8.get("newMembers") or []) == ["pathmenu", "preset"], w8)
    C("★★ D8 记了**两种机制**且分开命名（修法不同）",
      bool(w8) and set((w8.get("mechanismSplit") or {}).keys())
      == {"crowd", "preset/pathmenu"}
      and "不停止传播" in (w8["mechanismSplit"].get("preset/pathmenu") or ""),
      (w8 or {}).get("mechanismSplit"))
    C("★ D8 明确更正 767 的 O3", "correctsBatch767" in (w8 or {}))
    C("★ D8 的修法说清「两类都要用捕获+停止传播」",
      "两类" in ((w8 or {}).get("fixDirection") or ""))
    C("★★ D8 的 measured 逐格列出 raw 现算的 %d 格"
      % len(rw["deskLost"]),
      len(rw["deskLost"]) == 5
      and all(k in (w8.get("measured") or "") for k in rw["deskLost"]),
      {"raw": rw["deskLost"], "measured": (w8 or {}).get("measured")})

    # ── D3 / D4 扩宽
    w3, w4 = df("D3"), df("D4")
    C("★★ D3 从 1/6 扩到 2/6（新增 crowd）",
      bool(w3) and w3.get("from") == "1/6" and w3.get("to") == "2/6"
      and w3.get("newMembers") == ["crowd"], w3)
    C("★★ D3 记了「两个缺陷会叠在一起、修 D3 必须先修 D8」",
      "叠" in (w3.get("compositionNote") or "")
      and "先修 D8" in (w3.get("compositionNote") or ""))
    C("★★ D4 从 1/6 扩到 3/6（新增 phonevcam + modellib）",
      bool(w4) and w4.get("from") == "1/6" and w4.get("to") == "3/6"
      and sorted(w4.get("newMembers") or [])
      == ["modellib", "phonevcam"], w4)

    # ── 更正 767
    C("★★ J12 明确更正 767 的「6 个带 aria-expanded」（实为 5 个）",
      jd("J12").get("verdict") == "FAIL"
      and "5 个" in jd("J12").get("statement", "")
      and "aria-expanded" in jd("J12").get("statement", ""))
    C("★★ crossBatch：pathmenu 的 aria-expanded 读数是 null（与 767 的 J10 同）",
      cb["ariaExpandedIn768"].get("pathmenu") is None
      and cb["ariaExpandedIn767"].get("pathmenu") is None
      and rw.get("thisAriaExpanded", {}).get("pathmenu") is None
      and rw.get("prevAriaExpanded", {}).get("pathmenu") is None,
      {"b768": cb.get("ariaExpandedIn768"),
       "b767": cb.get("ariaExpandedIn767"),
       "raw768": rw.get("thisAriaExpanded"),
       "raw767": rw.get("prevAriaExpanded")})
    C("★★ crossBatch：带 aria-expanded 的触发器恰好 5 个，pathmenu 只有 "
      "aria-pressed",
      cb.get("withAriaExpanded") == 5
      and cb.get("withAriaPressedOnly") == ["pathmenu"],
      {"n": cb.get("withAriaExpanded"),
       "only": cb.get("withAriaPressedOnly")})
    C("★ J7 明确说 D8 的机制不是一个是两个（更正 767 的 O3）",
      jd("J7").get("verdict") == "FAIL"
      and "两个" in jd("J7").get("statement", ""))

    # ── 跨批交叉核对
    C("★★ 跨批：6 个浮层的可聚焦控件数与 767 逐个相同",
      rw.get("focusablesAgree") is True and cb.get("perId")
      and all(v["agree"] for v in cb["perId"].values()),
      {"raw": rw.get("thisFocusables"), "prev": rw.get("prevFocusables")})
    C("★ 跨批的计数在产物里与 raw 现算一致",
      {i: cb["perId"][i]["batch768"] for i in IDS} == rw["thisFocusables"],
      {"artifact": {i: cb["perId"][i]["batch768"] for i in IDS},
       "raw": rw["thisFocusables"]})
    C("★ J11 判据在（跨批交叉核对是 PASS）",
      jd("J11").get("verdict") == "PASS")

    # ── 可比性 / 纪律
    comp = f["comparability"]
    C("★★ 两轮逐字段一致（a 与 b 各自）",
      comp["a"]["allConsistent"] is True and comp["b"]["allConsistent"] is True,
      {"a": comp["a"]["allConsistent"], "b": comp["b"]["allConsistent"]})
    proto = comp.get("protocol") or ""
    C("★★ 可比性里记了协议：每格从重载页面开始、全程不点外点",
      ("重载" in proto or "重新加载" in proto) and "不点外点" in proto, proto)
    C("★★ 12 格的起点都干净（浮层确实打开、焦点确实放到位）",
      all(c["opened"] and c["focusPlaced"] for k in CELLS
          for c in rw["cells"]["%s/%s" % k])
      and all(c["focusWasInPanel"] for k in CELLS if k[1] == "inside"
              for c in rw["cells"]["%s/%s" % k])
      and all(c["focusWasOnTrigger"] for k in CELLS if k[1] == "trigger"
              for c in rw["cells"]["%s/%s" % k]),
      [("%s/%s" % k, c["opened"], c["focusPlaced"])
       for k in CELLS for c in rw["cells"]["%s/%s" % k]
       if not (c["opened"] and c["focusPlaced"])])
    C("★★ 12 格 0 格 FAILED、无缺格",
      rw["failedA"] == [] and rw["failedB"] == [] and rw["missing"] == [],
      {"a": rw["failedA"], "b": rw["failedB"], "missing": rw["missing"]})
    C("★★ 12 格的四个分类**恰好铺满**（all([]) 陷阱）",
      len(rw["deskLost"]) + len(rw["stuck"]) + len(rw["onTrigger"])
      + len(rw["onBody"]) == 12 and rw["deskLost"] and rw["stuck"]
      and rw["onTrigger"] and rw["onBody"],
      {"deskLost": len(rw["deskLost"]), "stuck": len(rw["stuck"]),
       "onTrigger": len(rw["onTrigger"]), "onBody": len(rw["onBody"])})
    C("★ 产物与 raw 现算的分类逐项一致（deskGoneAfter 逐格）",
      all(sorted(comp["a"]["deskGoneAfter"][r]) == sorted(rw["deskLost"])
          for r in range(len(comp["a"]["deskGoneAfter"]))),
      {"deskGoneAfter": comp["a"]["deskGoneAfter"], "raw": rw["deskLost"]})
    C("★ 产物 12 格的分类与 raw 现算逐格一致",
      all(all(fr["cells"]["%s/%s" % k][r]["class"]
              == rw["cells"]["%s/%s" % k][r]["base"] for r in range(2))
          for k in CELLS),
      [("%s/%s" % k, fr["cells"]["%s/%s" % k][0]["class"],
        rw["cells"]["%s/%s" % k][0]["base"]) for k in CELLS
       if fr["cells"]["%s/%s" % k][0]["class"]
       != rw["cells"]["%s/%s" % k][0]["base"]])
    C("★ 没有点任何有副作用的控件（J13 在）",
      jd("J13").get("verdict") == "PASS"
      and "提交" in jd("J13").get("statement", ""))
    C("★ 观测 O5 记了 localStorage 清理的实证（第 1 轮清 0 份、第 2 轮清 1 份）",
      any(o.get("id") == "O5" and "localStorage" in (o.get("text") or "")
          for o in a.get("observations") or []))

    # ── 产物结构
    C("★★ R80：注入臂的 after 已是注入后状态，汇编器改了字段名",
      any(r["id"] == "R80" and "classInInjectedArm" in r.get("text", "")
          and "无效的阴性对照" in r.get("whyItMatters", "")
          for r in a.get("probeLessons") or []))
    C("★ 观察 %d 条、探针教训 %d 条（%s）"
      % (len(a.get("observations") or []),
         len(a.get("probeLessons") or []), "/".join(EXPECT_LESSON_IDS)),
      len(a.get("observations") or []) == 5
      and sorted(r["id"] for r in a.get("probeLessons") or [])
      == EXPECT_LESSON_IDS,
      [r["id"] for r in a.get("probeLessons") or []])
    C("★ 每条探针教训都有 whyItMatters",
      all(r.get("whyItMatters") for r in a.get("probeLessons") or []),
      [r["id"] for r in a.get("probeLessons") or []
       if not r.get("whyItMatters")])
    C("★★ R75 是本批的核心教训（读数说焦点在哪 ≠ 有人把它放到那儿）",
      any(r["id"] == "R75" and "对照" in r.get("text", "")
          and "不敏感" in r.get("text", "")
          for r in a.get("probeLessons") or []))
    C("★★ 不声称里保留了「导出/群众的焦点契约没测到」与"
      "「预设/路径菜单无法测」",
      sum(1 for t in a.get("notClaimed") or []
          if "没有测到" in t or "无法" in t) >= 2,
      [t[:40] for t in a.get("notClaimed") or []])
    C("★ 不声称里说了没改 src/", any("没有改 `src/`" in t
                              for t in a.get("notClaimed") or []))
    C("★ env.srcModified 为 False", a["env"].get("srcModified") is False)
    C("★ 原始读数与探针脚本都随产物提交（R43）",
      all((RAWDIR / f).exists() for f in RAW_FILES)
      and all((PROBEDIR / f).exists() for f in PROBE_FILES),
      {"raw": [f for f in RAW_FILES if not (RAWDIR / f).exists()],
       "probes": [f for f in PROBE_FILES if not (PROBEDIR / f).exists()]})
    C("★ rawSha 覆盖两份原始读数",
      set(a.get("rawSha") or {}) == set(RAW_FILES), a.get("rawSha"))
    C("★ 每个探针都标了 injected 与轮数",
      {p["id"]: p.get("injected") for p in a.get("probes") or []}
      == {"768a": False, "768b": True},
      [(p["id"], p.get("injected")) for p in a.get("probes") or []])

    # ── README
    if README.exists():
        rt = README.read_text(encoding="utf-8")
        rows = [ln for ln in rt.splitlines() if ln.startswith("| J")]
        C("★ README 判据表 14 行", len(rows) == 14, len(rows))
        C("★★ README 判据表首格不许是裸数字（pre-commit 正则会拦）",
          not any(BARE_NUM_CELL.match(ln) for ln in rows),
          [ln[:20] for ln in rows if BARE_NUM_CELL.match(ln)])
        verdict_by_id = {j["id"]: j["verdict"] for j in J}
        row_mismatch = []
        for ln in rows:
            jid = ln.split("|")[1].strip()
            if jid not in verdict_by_id:
                row_mismatch.append((jid, "不在产物里"))
            elif ("PASS" in ln) != (verdict_by_id[jid] == "PASS"):
                row_mismatch.append((jid, verdict_by_id[jid]))
        C("★ README 判据表的结论与产物 verdict 一致（逐行比）",
          not row_mismatch, row_mismatch)
        for sec in ("## 选题", "## 判据", "## 缺陷", "## 扩宽的三个缺陷",
                    "## 方法论", "## 更正 767", "## 不声称", "## 探针教训",
                    "## 复现"):
            C("★ README 有「%s」章节" % sec.strip("# "), sec in rt)
        C("★★ README 有独立的 D11 章节", "### D11" in rt)
        C("★ README 的 D11 章节写明了「没测到」的 4 个浮层",
          "没有测到" in rt and "触发器" in rt)
        C("★★ README 有撤回 no-op 那一节",
          "撤回" in rt and "no-op" in rt and "平凡" in rt)
        C("★ README 记了 D8 的两种机制的对照表",
          "冒泡" in rt and "捕获" in rt and "注册顺序无关" in rt)
        C("★ README 的更正段覆盖 767 的三处",
          all(x in rt for x in ("O3", "aria-expanded", "J9")))
    else:
        C("★ README 存在", False)

    # ── 台账
    lt = LEDGER.read_text(encoding="utf-8")
    hits = [ln for ln in lt.split("\n") if ln.startswith("| Batch 768 |")]
    C("★★ 台账恰好一行 Batch 768", len(hits) == 1, len(hits))
    if hits:
        ln = hits[0]
        C("★ 台账首格是 Batch 768（不是裸数字）",
          ln.split("|")[1].strip() == "Batch 768", ln[:24])
        C("★★ 台账新行 0 个 U+FFFD", ln.count(FFFD) == 0, ln.count(FFFD))
        C("★ 台账新行是 3 列", ln.count("|") == 4, ln.count("|"))
        C("★ 台账新行提到了 D11 与 D8 扩宽",
          "D11" in ln and "1/6 → 3/6" in ln)
    C("★ 台账历史 U+FFFD 仍是 9 个、仍在 522/583/587",
      lt.count(FFFD) == 9
      and [i + 1 for i, x in enumerate(lt.split("\n")) if FFFD in x]
      == [522, 583, 587],
      {"n": lt.count(FFFD),
       "lines": [i + 1 for i, x in enumerate(lt.split("\n")) if FFFD in x]})
    C("★ 台账只有 631 行", len(lt.split("\n")) == 631, len(lt.split("\n")))
    return ck


# ═════════════════════ 4. 阴性对照 ═════════════════════
def negative_controls(a, st, rw):
    cases = []

    def inj(name, mutate):
        x = copy.deepcopy(a)
        try:
            mutate(x)
        except Exception as e:
            cases.append({"name": name, "caught": False,
                          "firstFail": "注入自身抛错：%s" % e})
            return
        failed = [c["label"] for c in run_checks(x, st, rw) if not c["pass"]]
        cases.append({"name": name, "caught": len(failed) > 0,
                      "firstFail": failed[0] if failed else None})

    def inj_static(name, mutate):
        s = copy.deepcopy(st)
        try:
            mutate(s)
        except Exception as e:
            cases.append({"name": name, "caught": False,
                          "firstFail": "注入自身抛错：%s" % e})
            return
        failed = [c["label"] for c in run_checks(a, s, rw) if not c["pass"]]
        cases.append({"name": name, "caught": len(failed) > 0,
                      "firstFail": failed[0] if failed else None})

    def inj_raw(name, mutate):
        files = copy.deepcopy(rw["__raw__"])
        try:
            mutate(files)
        except Exception as e:
            cases.append({"name": name, "caught": False,
                          "firstFail": "注入自身抛错：%s" % e})
            return
        try:
            badr = raw_side_from(files)
        except Exception as e:
            cases.append({"name": name, "caught": True,
                          "firstFail": "重算抛错：%s" % e})
            return
        failed = [c["label"] for c in run_checks(a, st, badr) if not c["pass"]]
        cases.append({"name": name, "caught": len(failed) > 0,
                      "firstFail": failed[0] if failed else None})

    def inj_file(name, path, old, new, all_hits=False):
        orig = path.read_text(encoding="utf-8")
        if old not in orig:
            cases.append({"name": name, "caught": False,
                          "firstFail": "待替换文本不存在（对照本身失效）"})
            return
        try:
            body = orig.replace(old, new) if all_hits \
                else orig.replace(old, new, 1)
            path.write_text(body, encoding="utf-8")
            failed = [c["label"] for c in run_checks(a, st, rw) if not c["pass"]]
        finally:
            path.write_text(orig, encoding="utf-8")
        cases.append({"name": name, "caught": len(failed) > 0,
                      "firstFail": failed[0] if failed else None})

    def rows(files, fn, key="rows"):
        out = []
        for rd in files[fn]["rounds"]:
            for x in rd.get(key) or []:
                if x.get("mode") == key and False:
                    pass
            for x in rd.get(key) or []:
                out.append(x)
        return out

    def res_all(files, fn, ident, mode, key="rows"):
        """同一个 (浮层, 变体) 在**所有轮**里的记录。

        ★ 本批的结论要求**两轮都满足**，所以只改一轮的对照永远不会触发
          （763–767 各踩过一次不同形状的这条）。
        """
        out = []
        for rd in files[fn]["rounds"]:
            hit = [x for x in (rd.get(key) or [])
                   if x.get("id") == ident and x.get("mode") == mode]
            if not hit:
                raise KeyError((ident, mode))
            out.append(hit[0])
        return out

    # ── 伪造「缺陷不存在 / 性质变了」
    inj("★ 删掉 D11", lambda x: x.__setitem__(
        "defects", [d for d in x["defects"] if d["id"] != "D11"]))
    inj("★ 把 D11 降级成观察", lambda x: x.__setitem__(
        "observations", x["observations"] + [{"id": "O9", "text": "D11"}]))
    inj("★ 把 D11 的严重度从低改成中", lambda x:
        [d for d in x["defects"] if d["id"] == "D11"][0].__setitem__(
            "severity", "中"))
    inj("★ 把 D11 的 widensD4From765 去掉（退回个案）", lambda x:
        [d for d in x["defects"] if d["id"] == "D11"][0].pop(
            "widensD4From765"))
    inj("★ 把 D11 的 inRepoExemplar 抹掉（修法就没先例了）", lambda x:
        [d for d in x["defects"] if d["id"] == "D11"][0].pop("inRepoExemplar"))
    inj("★ D11 的 where 指向不存在的行号", lambda x:
        [d for d in x["defects"] if d["id"] == "D11"][0]["where"].append(
            "src/components/director/DirectorDesk.tsx:99999"))
    inj("★ D11 的 measured 里抹掉「没测到」", lambda x:
        [d for d in x["defects"] if d["id"] == "D11"][0].__setitem__(
            "measured", "2 个浮层焦点掉到 body"))

    # ── 把 4 个没测到的浮层算成通过（本批最想防的自欺）
    inj("★★ 把「被 D3 遮住」的两格算成通过", lambda x:
        x["findings"]["focusRestore"].__setitem__(
            "unmeasuredBecauseD3", [])
        or x["findings"]["focusRestore"].__setitem__(
            "implementedRestore", ["export", "crowd"]))
    inj("★★ 把「触发器已卸载」的两格算成通过", lambda x:
        x["findings"]["focusRestore"].__setitem__(
            "impossibleBecauseTriggerUnmounted", [])
        or x["findings"]["focusRestore"].__setitem__(
            "implementedRestore", ["preset", "pathmenu"]))
    inj("★★ 只留两个「测到且错」就把分母说成 2", lambda x:
        x["findings"]["focusRestore"].__setitem__("denominatorNote",
                                                  "分母是 2 个浮层"))

    # ── 把 no-op 撤回抹掉
    inj("★★ 把三个 no-op 格标成「不是平凡读数」", lambda x:
        x["findings"]["focusRestore"]["perDisclosure"]["export"].__setitem__(
            "triggerVariantIsVacuous", False))
    inj("★★ 把 J5 的 no-op 撤回删掉", lambda x: x.__setitem__(
        "judgments", [j for j in x["judgments"] if j["id"] != "J5"]))
    inj("★★ 把 J5 改成 FAIL（撤回就不成立了）", lambda x:
        [j for j in x["judgments"] if j["id"] == "J5"][0].__setitem__(
            "verdict", "FAIL"))
    inj("★ 删掉 O1（平凡读数这条方法论）", lambda x: x.__setitem__(
        "observations", [o for o in x["observations"] if o["id"] != "O1"]))
    inj("★ 删掉 R75（本批核心教训）", lambda x: x.__setitem__(
        "probeLessons", [r for r in x["probeLessons"] if r["id"] != "R75"]))
    inj("★ R75 抹掉 whyItMatters", lambda x:
        [r for r in x["probeLessons"] if r["id"] == "R75"][0].pop(
            "whyItMatters"))

    # ── 把注入对照抹掉
    inj("★★ 删掉 cellsChangedByInjection（注入对照就没了）", lambda x:
        x["findings"]["injectionContrast"].__setitem__(
            "cellsChangedByInjection", []))
    inj("★★ 把注入说成改动了 4 格", lambda x:
        x["findings"]["injectionContrast"].__setitem__(
            "cellsChangedByInjection",
            ["phonevcam/inside", "modellib/inside", "export/inside",
             "crowd/inside"]))
    inj("★ 抹掉注入挂在捕获阶段的原因", lambda x:
        x["findings"]["injectionContrast"].__setitem__("whyCapture", ""))

    # ── D8 的两种机制
    inj("★ 把 D8 的第二种机制抹掉（只剩 crowd 那种）", lambda x:
        [w for w in x["widened"] if w["id"] == "D8"][0]["mechanismSplit"].pop(
            "preset/pathmenu"))
    inj("★ 把 D8 的新增成员改成只有 preset", lambda x:
        [w for w in x["widened"] if w["id"] == "D8"][0].__setitem__(
            "newMembers", ["preset"]))
    inj("★ 把 D8 的 from/to 抹掉", lambda x:
        [w for w in x["widened"] if w["id"] == "D8"][0].__setitem__("from", "")
        or [w for w in x["widened"] if w["id"] == "D8"][0].__setitem__("to",
                                                                      ""))
    inj("★ D8 抹掉「注册顺序无关」这个要点", lambda x:
        [w for w in x["widened"] if w["id"] == "D8"][0].__setitem__(
            "mechanismSplit",
            {"crowd": "没有自己的 Esc 处理",
             "preset/pathmenu": "有 Esc 处理"}))
    inj("★ 删掉 J7（D8 两种机制的判据）", lambda x: x.__setitem__(
        "judgments", [j for j in x["judgments"] if j["id"] != "J7"]))

    # ── 更正 767
    inj("★ 删掉 J12（更正 aria-expanded 份数）", lambda x: x.__setitem__(
        "judgments", [j for j in x["judgments"] if j["id"] != "J12"]))
    inj("★ 把带 aria-expanded 的份数从 5 改成 6", lambda x:
        x["findings"]["crossBatch"].__setitem__("withAriaExpanded", 6))
    inj("★ 把 pathmenu 从「只有 aria-pressed」里去掉", lambda x:
        x["findings"]["crossBatch"].__setitem__("withAriaPressedOnly", []))

    # ── D3 / D4 扩宽
    inj("★ 把 D3 的扩宽抹掉", lambda x: x.__setitem__(
        "widened", [w for w in x["widened"] if w["id"] != "D3"]))
    inj("★ D3 抹掉「两个缺陷会叠在一起」", lambda x:
        [w for w in x["widened"] if w["id"] == "D3"][0].pop(
            "compositionNote"))
    inj("★ 把 D4 的扩宽抹掉", lambda x: x.__setitem__(
        "widened", [w for w in x["widened"] if w["id"] != "D4"]))

    # ── 判据偷改
    for jid in EXPECT_FAIL_IDS:
        i = [k for k, j in enumerate(a["judgments"]) if j["id"] == jid][0]
        inj("★ 把 %s 从 FAIL 改成 PASS" % jid, lambda x, i=i:
            x["judgments"][i].__setitem__("verdict", "PASS"))
    inj("★ 判据全改成 PASS", lambda x: ([j.__setitem__("verdict", "PASS")
                                       for j in x["judgments"]]))
    inj("★ 把判据条数从 14 改成 11", lambda x: x.__setitem__(
        "judgments", x["judgments"][:11]))
    inj("★ 把 J3 的 evidence 换成可比性（D11 失去支撑）", lambda x:
        [j for j in x["judgments"] if j["id"] == "J3"][0].__setitem__(
            "evidence", x["findings"]["comparability"]))
    inj("★ 只改 findings 一份（判据的 evidence 不动）", lambda x:
        x["findings"]["focusRestore"].__setitem__("measuredAndFails",
                                                  ["export"]))

    # ── 静态层伪造
    inj_static("伪造：DirectorDesk 里其实有 crowdPanelOpen 的一档",
               lambda x: x.__setitem__("otherStateTotal", 1))
    inj_static("伪造：阶梯里 exportPanelOpen 有两档",
               lambda x: x.__setitem__("exportTierCount", 2))
    inj_static("伪造：那档排在 closeWorkspace 之后",
               lambda x: x.__setitem__("tierBeforeClose", False))
    inj_static("伪造：导演台自己的监听变成捕获阶段",
               lambda x: x["listeners"].__setitem__(
                   0, dict(x["listeners"][0], capture=True)))
    inj_static("伪造：冒泡阶段有一处停止传播", lambda x: x.__setitem__(
        "bubbleStops", ["DirectorTimeline.tsx:570"]))
    inj_static("伪造：捕获阶段有一处没停止传播", lambda x: x.__setitem__(
        "captureStops", ["DirectorViewport.tsx:2711"]))
    inj_static("伪造：出现第三种组合", lambda x: x.__setitem__(
        "combos", ["bubble/leaks", "capture/stops", "capture/leaks"]))
    inj_static("伪造：函数体找不到（正则失效）", lambda x: x.__setitem__(
        "allBodiesFound", False))
    inj_static("伪造：useLayerFocus 的 opener.focus() 不见了", lambda x:
               x.__setitem__("useLayerFocusOpenerFocus", False))
    inj_static("伪造：useLayerFocus 注释里没有本批症状", lambda x:
               x.__setitem__("useLayerFocusNamesBodyDrop", False))
    inj_static("伪造：导演台其实用了 useLayerFocus", lambda x: x.__setitem__(
        "directorUsesUseLayerFocus", ["DirectorDesk.tsx"]))
    inj_static("伪造：isEditable 早退排在 Escape 分支之后", lambda x:
               x.__setitem__("isEditableGateLine", 999))

    # ── 原始读数：改真正的被检查键
    inj_raw("★★ 原始：虚拟相机的焦点不再掉 body（D11 少一个）", lambda x:
            [v["after"].__setitem__(
                "active", dict(v["after"]["active"], isBody=False,
                               isTrigger=True, tag="BUTTON"))
             for v in res_all(x, "vb768a.json", "phonevcam", "inside")])
    inj_raw("★★ 原始：把模型库也说成焦点回触发器", lambda x:
            [v["after"].__setitem__(
                "active", dict(v["after"]["active"], isBody=False,
                               isTrigger=True, tag="BUTTON"))
             for v in res_all(x, "vb768a.json", "modellib", "inside")])
    inj_raw("★★ 原始：预设运镜不再关导演台（D8 缩回 1/6）", lambda x:
            [v.__setitem__("after", dict(v["after"], open=True,
                                         panelPresent=False))
             for v in res_all(x, "vb768a.json", "preset", "inside")]
            + [v.__setitem__("desk", {"open": True})
               for v in res_all(x, "vb768a.json", "preset", "inside")])
    inj_raw("★★ 原始：路径菜单也不再关导演台", lambda x:
            [v.__setitem__("after", dict(v["after"], open=True,
                                         panelPresent=False))
             for v in res_all(x, "vb768a.json", "pathmenu", "inside")]
            + [v.__setitem__("desk", {"open": True})
               for v in res_all(x, "vb768a.json", "pathmenu", "inside")])
    def strip_injection(x):
        """把 b 臂整条还原成 a 臂的读数 ⟹ 注入「一格都没改动」。

        ★ 不能只把 `after2` 覆盖成 b 自己的 `after` —— b 的 `after`
          是在注入 150ms 触发**之后**、750ms 时才读的，**它已经是注入后
          的状态**（见 R80）。基线只能取自 a 臂。
        """
        idx = {}
        for rd in x["vb768a.json"]["rounds"]:
            for r in rd["rows"]:
                idx.setdefault((r["id"], r["mode"]), []).append(r)
        for i, rd in enumerate(x["vb768b.json"]["rounds"]):
            for r in rd["rows"]:
                src = idx[(r["id"], r["mode"])][i]
                r["after2"] = copy.deepcopy(src["after"])
                r["desk"] = copy.deepcopy(src["desk"])
    inj_raw("★★ 原始：把 b 臂还原成 a 臂（注入一格都没改动）",
            strip_injection)
    inj_raw("★★ 原始：注入在「面板没关」的那格也调了 focus（R76 失效）",
            lambda x:
            [v.__setitem__("inj", [{"panelGone": True, "trigThere": True,
                                    "focused": True}])
             for v in res_all(x, "vb768b.json", "export", "inside")])
    inj_raw("★★ 原始：注入在导演台没了的格谎称触发器还在", lambda x:
            [v.__setitem__("inj", [{"panelGone": True, "trigThere": True,
                                    "focused": True}])
             for v in res_all(x, "vb768b.json", "preset", "inside")])
    inj_raw("★ 原始：把群众阵列的浮层说成关掉了（D3 扩宽失效）", lambda x:
            [v.__setitem__("after", dict(v["after"], panelPresent=False))
             for v in res_all(x, "vb768a.json", "crowd", "inside")])
    inj_raw("★ 原始：某格 FAILED", lambda x:
            [v.__setitem__("FAILED", "点不动")
             for v in res_all(x, "vb768a.json", "modellib", "trigger")])
    inj_raw("★ all([]) 陷阱：把 rows 清空（两轮都清）", lambda x:
            [rd.__setitem__("rows", []) for rd in x["vb768a.json"]["rounds"]])
    inj_raw("★ 原始：某格起点不干净（浮层没打开）", lambda x:
            [v["before"].__setitem__("panelPresent", False)
             for v in res_all(x, "vb768a.json", "export", "trigger")])
    inj_raw("★ 原始：把可聚焦控件数改成与 767 不同（跨批核对失效）", lambda x:
            [v["focus"].__setitem__("total", 99)
             for v in res_all(x, "vb768a.json", "modellib", "inside")])
    inj_raw("★ 原始：pathmenu 的 aria-expanded 填上 true（J12 失去依据）",
            lambda x:
            [v["before"].__setitem__("triggerAriaExpanded", "true")
             for v in res_all(x, "vb768a.json", "pathmenu", "trigger")])
    inj_raw("★ 原始：把两轮说成不一致时（可比性失效）", lambda x:
            x["vb768a.json"]["rounds"][1]["rows"][0].__setitem__(
                "focus", {"focused": False}))

    # ── 台账 / README
    led = LEDGER.read_text(encoding="utf-8")
    led_line = next((ln for ln in led.split("\n")
                     if ln.startswith("| Batch 768 |")), "")
    if led_line:
        sep = "" if led.endswith(led_line + "\n") else "\n"
        inj_file("★ 台账删掉 Batch 768 行", LEDGER, sep + led_line, "")
        inj_file("★ 台账行首格改成裸数字 768", LEDGER,
                 "| Batch 768 |", "| 768 |")
        inj_file("★ 台账行首格写成 Batch 0768", LEDGER,
                 "| Batch 768 |", "| Batch 0768 |")
        inj_file("★ 台账新行塞一个 U+FFFD", LEDGER,
                 led_line[:40], led_line[:40] + FFFD)
        inj_file("★ 台账被追加了 Batch 769（行数断言）", LEDGER,
                 "| Batch 768 |", "| Batch 768 |\n| Batch 769 | x")
        # ★ 768 那一行里 "D11" 出现 **2 次**，只替换第一处等于没改
        inj_file("★ 台账新行不含 D11", LEDGER, "D11", "D1x",
                 all_hits=True)
    if README.exists():
        rt = README.read_text(encoding="utf-8")
        bad_cell = next((ln for ln in rt.split("\n")
                         if ln.startswith("| J")), "| J1 | x |")
        inj_file("★ README 判据表首格改成裸数字", README, bad_cell, "| 1 | x |")
        inj_file("★ README 删掉「不声称」章节", README, "## 不声称", "## 备注")
        inj_file("★ README 删掉 D11 章节", README, "### D11", "### 附注")
        inj_file("★ README 删掉撤回 no-op 那一节", README, "撤回",
                 "另说", all_hits=True)
        inj_file("★ README 删掉「更正 767」章节", README, "## 更正 767",
                 "## 附注")
        inj_file("★ README 删掉「注册顺序无关」", README, "注册顺序无关",
                 "顺序无关", all_hits=True)
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
        {"label": "原始读数可用（raw/ 下 2 份）", "pass": False, "got": rawErr}]
    neg = [] if rawErr else negative_controls(a, st, rw)

    npass = sum(1 for c in checks if c["pass"])
    total = len(checks)
    neg_ok = sum(1 for n in neg if n["caught"])
    ok = npass == total and neg_ok == len(neg)

    REPORT.write_text(json.dumps(
        {"batch": 768, "checks": checks, "pass": npass, "total": total,
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
            print("  ✗ 漏放：%s" % n["name"])
    print("batch 768 %s" % ("通过" if ok else "不通过"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
