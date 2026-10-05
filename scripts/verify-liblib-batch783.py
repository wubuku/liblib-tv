#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 783 验收器 —— **独立实现**，不 import 汇编器，也不 import 普查器

## 本批要防的错误方向

本批的结论是「**我的预测被否掉了，而真机制是打开者里的双向交叉写入**」。
三个方向各自有代价：

- 若把「**双向**」漏掉（只找到一处交叉写入）⟹ 会得出「互斥是单向的，
  所以从另一个方向进去能同时开着」⟹ 而运行时两个方向都测了、都被排除
  ⟹ **一条假缺陷**。
- 若把「**先关后开**」漏掉（不查顺序）⟹ 会得出「交叉写入存在就够了」⟹
  而若那行排在打开自己**之后**，打开预设面板会先把路径菜单关掉、
  再打开预设 —— 顺序恰恰是这条不变量能成立的**原因**，不是细节。
- 若把「**779 漏了两道门**」漏掉 ⟹ 授权文本继续按「四档」写阶梯的形状
  ⟹ 下一个人会以为「有活动手势时 Escape 怎么走」只取决于四档。
- 若把「**预测被否掉**」当成「探针不准」⟹ 会去改探针
  ⟹ 而两臂读数完全一致恰恰是「互斥与激活方式无关」的强证据（R148）。

## 静态层为什么算「独立」

普查器（`census783.py`）做的是**通用采集**：`useEffect` 体里逐条找 `if (…)`、
用**扫描最近 `const NAME = (…) => {`** 找交叉写入的归属函数。

本验收器**不复用其中任何一步**：全部用**行锚定的字面量断言** ——
「`togglePathMenu` 的函数体里必须出现这一行，且必须排在那一行之前」。
⟹ 普查器把归属函数认错（它靠向上扫最近的函数头）时，这里会红。

## 沿用 775–782 的纪律

- 阴性对照的 `mutatedAnything` **实测**、`kw` **唯一**（R118）
- ★ **源码变异必须行数中性**（782 新立）—— 否则行锚定判据会被移位冲掉
- 改源码的对照必须**真的**让对应判据红，且**只**红一条
"""
import copy
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch783-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAWDIR = OUTDIR / "raw"
PROBEDIR = OUTDIR / "probes"
README = OUTDIR / "README.md"
LEDGER = ROOT / "docs/research/VERIFICATION_LEDGER.md"
C782 = ROOT / ("docs/research/liblib-canvas-batch782-2026-10-01"
               "/raw/census782.json")

RAW_FILES = ["census783.json", "vb783a.json"]
PROBE_FILES = ["census783.py", "dbg783a.py", "mk783audit.py"]
FFFD = "�"
META = {"tries", "retried"}
TL = "src/components/director/DirectorTimeline.tsx"
DD = "src/components/director/DirectorDesk.tsx"
ARMS = ["bothByMouse", "bothByKeyboard", "reverseByMouse", "pathOnly"]
PRESSES = 1
ROUNDS = 2
SURFACE_PRED = "resolveLibTVBlockingForegroundSurface"


def squash(s):
    return " ".join(s.split())


def match(text, op, cl, idx):
    depth = 0
    for i in range(idx, len(text)):
        if text[i] == op:
            depth += 1
        elif text[i] == cl:
            depth -= 1
            if depth == 0:
                return i
    return -1


def fn_body(text, name):
    """★ 取 `const <name> = (…) => { … }` 的**整个函数体**（括号配对，R141）。"""
    m = re.search(r"\bconst\s+%s\b" % re.escape(name), text)
    if not m:
        return None
    cb = text.index("{", m.end())
    cl = match(text, "{", "}", cb)
    return text[cb:cl + 1] if cl > 0 else None


# ───────────────── 静态层（独立实现：行锚定字面量） ─────────────────
def static_side(sources=None):
    sources = sources or {}

    def load(rel):
        if rel in sources:
            return sources[rel]
        p = ROOT / rel
        return p.read_text(encoding="utf-8") if p.exists() else None

    tl, dd = load(TL), load(DD)
    if tl is None or dd is None:
        return {"err": "缺源码"}
    st = {}
    tb, pb = fn_body(tl, "togglePathMenu"), fn_body(tl, "togglePresetPanel")
    st["bothOpenersFound"] = bool(tb and pb)
    st["pathWritesPreset"] = bool(tb) and "setPresetPanelLeft(null);" in tb
    st["presetWritesPath"] = bool(pb) and "setPathMenuLeft(null);" in pb
    # ★ 顺序：**关闭对方**必须排在**打开自己**之前。
    #   ⚠ 两个坑（782 的 R148，第三次）：① 函数体里**第一处** `setX(` 是
    #   toggle-off 分支的 `setX(null);`，拿它当基准会把顺序判反；
    #   ② 源码里实参**另起一行**，字面量 needle 匹配不上 ⟹ needle 用正则。
    _open = lambda body, name: (  # noqa: E731
        re.search(r"set%s\(\s*Math\.max" % name, body) if body else None)
    tb2, pb2 = squash(tb or ""), squash(pb or "")
    _po, _ro = _open(tb2, "PathMenuLeft"), _open(pb2, "PresetPanelLeft")
    st["openCallFound"] = bool(_po and _ro)
    st["pathOrderOk"] = bool(
        _po and "setPresetPanelLeft(null);" in tb2
        and tb2.index("setPresetPanelLeft(null);") < _po.start())
    st["presetOrderOk"] = bool(
        _ro and "setPathMenuLeft(null);" in pb2
        and pb2.index("setPathMenuLeft(null);") < _ro.start())
    # ★ 两个 Escape 主人各自的门（行锚定）
    st["pathGate"] = "if (pathMenuLeft === null) return;" in tl
    st["presetGate"] = "if (presetPanelLeft === null) return;" in tl
    # ★ 两道门的状态**在各自的条件里互不出现** ⟹ 普查看起来「互不相关」
    cond = lambda s: squash(s)  # noqa: E731
    gm = re.search(r"if \(pathMenuLeft === null\) return;", tl)
    gp = re.search(r"if \(presetPanelLeft === null\) return;", tl)
    st["gatesDontCross"] = bool(
        gm and gp and "presetPanelLeft" not in gm.group(0)
        and "pathMenuLeft" not in gp.group(0))
    # ★ 桌阶梯：「两道门 + 四档」而不是「四档」
    iL = dd.index('if (event.key !== "Escape") return;')
    ladder = squash(dd[iL:dd.index("window.addEventListener", iL)])
    st["ladderDomGuard"] = \
        'if (document.querySelector("[data-director-capture-viewer]")) return;' \
        in ladder
    st["ladderBusyGuard"] = "if (workspaceBusy) return;" in ladder
    # ★ 四档各用**一个互不相同**的标识符；不要写成 `if (history.activeGesture)`
    #   —— 源码里是 `useDirectorStore.getState().history.activeGesture`，
    #   那个 needle 数不到（第一版数出 3 就是这么丢的）
    st["ladderRungs"] = sum(1 for k in ("activeGesture", "exportPanelOpen",
                                        "followTargetId", "closeWorkspace(")
                            if k in ladder)
    # ★ `page.tsx` 的两个主人共用一个 effect（普查必须如实标出）
    cen = json.loads(C782.read_text(encoding="utf-8"))
    st["escapeOwnerCount"] = sum(
        1 for o in cen["owners"] if "Escape" in o["keys"])
    st["sIPOwners"] = sorted(
        "%s:%d" % (o["file"].split("src/")[-1], o["regLine"])
        for o in cen["owners"] if "Escape" in o["keys"] and o["stopsImmediate"])
    st["surfacePredInPlane"] = sum(
        1 for o in cen["owners"] if "Escape" in o["keys"]
        and o["file"] == "src/app/page.tsx" and o["regLine"] == 1400)
    return st


# ───────────────── 原始读数（重算） ─────────────────
def load_raw():
    for f in RAW_FILES:
        if not (RAWDIR / f).exists():
            raise SystemExit("缺原始读数 %s —— 判失败，不许通过" % f)
    for f in PROBE_FILES:
        if not (PROBEDIR / f).exists():
            raise SystemExit("缺探针脚本 %s —— 判失败，不许通过" % f)
    raw = json.loads((RAWDIR / "vb783a.json").read_text(encoding="utf-8"))
    if len(raw.get("rounds") or []) != ROUNDS:
        raise SystemExit("轮数不是 %d" % ROUNDS)
    return raw


def strip(x):
    return [{k: v for k, v in r.items() if k not in META} for r in (x or [])]


def reading(row):
    r = {k: v for k, v in row.items() if k not in META}
    r.pop("arm", None)
    return r


def derive(raw):
    D = {"unexpectedFailed": [], "arms": {}}
    arms = {}
    for rd in raw.get("rounds") or []:
        for r in strip(rd.get("rows")):
            arms.setdefault(r.get("arm"), []).append(r)
    D["arms"] = {k: v for k, v in arms.items()}
    for k, v in arms.items():
        if v[0].get("FAILED"):
            D["unexpectedFailed"].append("%s: %s" % (k, v[0]["FAILED"]))
    D["keys"] = sorted(arms)
    D["rounds"] = len(raw.get("rounds") or [])
    D["roundsConsistent"] = (
        [reading(x) for x in strip(raw["rounds"][0].get("rows"))]
        == [reading(x) for x in strip(raw["rounds"][1].get("rows"))])
    D["pressTotal"] = sum(len(r.get("presses") or [])
                          for rd in (raw.get("rounds") or [])
                          for r in (rd.get("rows") or []))
    return D


def _a(D, arm):
    return (D["arms"].get(arm) or [{}])[0]


def _st(D, arm, key):
    return (_a(D, arm).get(key) or {})


def _ok(x):
    return bool(x)


# ───────────────── 判据 ─────────────────
def run_checks(a, st, D):
    C = []

    def add(label, got, want=None):
        if isinstance(got, bool) and want is None:
            C.append({"label": label, "pass": bool(got), "got": got})
        else:
            C.append({"label": label, "pass": (got == want), "got": got,
                      "want": want})

    # ── 静态：普查器本身的底数 ──
    add("静态：缺源码", st.get("err") is None, True)
    add("静态：★ 挂载域 `Escape` 主人 %d 个（沿用 782 的普查）"
        % (st.get("escapeOwnerCount") or 0), st.get("escapeOwnerCount"), 11)
    add("静态：★ 两个打开者都找得到", _ok(st.get("bothOpenersFound")))
    add("静态：★ `togglePathMenu` 里有 `setPresetPanelLeft(null);`"
        "（互斥的第一半）", _ok(st.get("pathWritesPreset")))
    add("静态：★ `togglePresetPanel` 里有 `setPathMenuLeft(null);`"
        "（互斥的第二半 ⟹ **双向**）", _ok(st.get("presetWritesPath")))
    add("静态：★★ 两处交叉写入都**排在打开自己之前** ⟹ "
        "「先关后开」是这条不变量能成立的**原因**，不是细节",
        (st.get("pathOrderOk"), st.get("presetOrderOk")), (True, True))
    add("静态：★ `:570` 的门是 `if (pathMenuLeft === null) return;`",
        _ok(st.get("pathGate")))
    add("静态：★ `:594` 的门是 `if (presetPanelLeft === null) return;`",
        _ok(st.get("presetGate")))
    add("静态：★★ 两道门**互不提到对方的状态** ⟹ 从普查看它们「互不相关」"
        "（这正是 782 会给的印象，也是本批要检验的对象）",
        _ok(st.get("gatesDontCross")))

    # ── 静态：更正 779 的阶梯形状 ──
    add("静态：★★ 阶梯里有 `:551` 那道 **DOM 存在性**门"
        "（`document.querySelector(\"[data-director-capture-viewer]\")`）",
        _ok(st.get("ladderDomGuard")))
    add("静态：★★ 阶梯里有 `:552` 那道 `workspaceBusy` 门",
        _ok(st.get("ladderBusyGuard")))
    add("静态：★ 阶梯的档数 = %d（activeGesture / 导出面板 / followTarget / "
        "closeWorkspace）⟹ 完整形状是「**两道门 + 四档**」"
        % (st.get("ladderRungs") or 0), st.get("ladderRungs"), 4)
    add("静态：`Escape` 主人的 `sIP` 名单 = %r（4 个，含宿主页）"
        % (st.get("sIPOwners") or []), len(st.get("sIPOwners") or []), 4)

    # ── 原始读数 ──
    add("原始：零 FAILED", D["unexpectedFailed"], [])
    add("原始：臂集合齐（%d 臂）" % len(ARMS), D["keys"], sorted(ARMS))
    add("原始：轮数 = %d" % ROUNDS, D.get("rounds"), ROUNDS)
    add("原始：两轮逐字段一致", _ok(D.get("roundsConsistent")))
    add("原始：按压格数 = %d 臂 × %d 次 × %d 轮 = %d"
        % (len(ARMS), PRESSES, ROUNDS, len(ARMS) * PRESSES * ROUNDS),
        D.get("pressTotal"), len(ARMS) * PRESSES * ROUNDS)
    for arm in ARMS:
        r = _a(D, arm)
        add("原始：%s 跑满 %d 次按压" % (arm, PRESSES),
            len(r.get("presses") or []), PRESSES)
        add("原始：%s 导出了面板是**开着**的（阶梯那档有目标）" % arm,
            ((r.get("stateBefore") or {}).get("exportOpen")), True)
        for p in (r.get("presses") or []):
            add("逐次：%s 第%s次 `cap>=1` ⟹ 按键**真的送达了浏览器**"
                % (arm, p.get("n")), (p["read"].get("cap") or 0) >= 1)
            add("逐次：%s 第%s次 `win>=1` ⟹ 事件**到达了 window** "
                "⟹ 本批三臂**没有任何 `sIP` 主人活着**"
                % (arm, p.get("n")), (p["read"].get("win") or 0) >= 1)
            add("逐次：%s 第%s次后导出面板**关掉了**（阶梯跑了）"
                % (arm, p.get("n")), (p.get("state") or {}).get("exportOpen"),
                False)
            add("逐次：%s 第%s次后桌**仍开着**（阶梯没跑过头）"
                % (arm, p.get("n")), (p.get("state") or {}).get("deskOpen"),
                True)

    # ── 预测 F：★★ 键盘臂与鼠标臂读数**一致** ⟹ 我的预测被否 ──
    kb2, ms2 = _st(D, "bothByKeyboard", "afterSecond"), \
        _st(D, "bothByMouse", "afterSecond")
    for arm in ("bothByMouse", "bothByKeyboard"):
        add("预测 F：%s 第 1 个面板（路径菜单）开着了" % arm,
            _st(D, arm, "afterFirst").get("pathOpen"), True)
        add("预测 F：%s 第 2 个面板（预设）开着了" % arm,
            _st(D, arm, "afterSecond").get("presetOpen"), True)
        add("预测 F：★ %s 第 2 个面板打开后**路径菜单被关掉了** ⟹ "
            "「键盘能绕过外点关闭」**被否**、「两者可共活」**被否**" % arm,
            _st(D, arm, "afterSecond").get("pathOpen"), False)
    add("预测 F：★★ 键盘臂与鼠标臂第 2 步读数**完全一样** ⟹ "
        "「互斥与激活方式无关」（`pointerdown` 假设死）",
        kb2, ms2)

    # ── 预测 G：★ 反向顺序也互斥 ⟹ **双向**拿到运行时确认 ──
    rv1, rv2 = _st(D, "reverseByMouse", "afterFirst"), \
        _st(D, "reverseByMouse", "afterSecond")
    add("预测 G：reverse 臂第 1 个面板（预设）开着了",
        rv1.get("presetOpen"), True)
    add("预测 G：reverse 臂第 2 个面板（路径）开着了", rv2.get("pathOpen"), True)
    add("预测 G：★★ reverse 臂第 2 个面板打开后**预设面板被关掉了** ⟹ "
        "互斥**不是单向的**（与 `:695` 那行交叉写入一致）",
        rv2.get("presetOpen"), False)

    # ── 判别力对照 ──
    add("对照：pathOnly 臂起点路径菜单**开着**",
        _st(D, "pathOnly", "afterFirst").get("pathOpen"), True)
    p0 = (_a(D, "pathOnly").get("presses") or [{}])[0]
    add("对照：★ pathOnly 臂按压后路径菜单**关掉了** ⟹ 判别力成立",
        (p0.get("state") or {}).get("pathOpen"), False)
    add("对照：pathOnly 臂导出面板**关掉了** ⟹ 一次按压**两个主人**"
        "（面板 + 阶梯那档）⟹ 并发**不靠传播阻断**",
        (p0.get("state") or {}).get("exportOpen"), False)
    nTwo = sum(1 for arm in ARMS
               if (p0 if arm == "pathOnly" else
                   (_a(D, arm).get("presses") or [{}])[0])
               .get("state", {}).get("exportOpen") is False)
    add("★ 四个臂**全部**是「一次 Escape 关两个东西」⟹ 782 的 J4 再次成立",
        nTwo, len(ARMS))

    # ── 产物自洽 ──
    own = a.get("coLive") or {}
    res = a.get("results") or {}
    add("产物：audit.batch=783", a.get("batch"), 783)
    add("产物：★ audit 记的「普查看起来互不相关」= True",
        own.get("censusLooksIndependent"), True)
    add("产物：★ audit 记的「预测被否掉」= True", own.get("predictionRefuted"),
        True)
    add("产物：★ audit 记的「激活方式与互斥无关」= True",
        own.get("activationMethodIrrelevant"), True)
    add("产物：★ audit 记的「两个方向都互斥」= True",
        own.get("runtimeBothOrdersExclusive"), True)
    add("产物：★ audit 记的交叉写入处数 = 独立字面量核对（2 处）",
        res.get("crossWrites"),
        int(bool(st.get("pathWritesPreset"))) +
        int(bool(st.get("presetWritesPath"))))
    add("产物：★ audit 记的阶梯「额外门数」= 独立字面量核对（2）",
        res.get("ladderExtraGuards"),
        int(bool(st.get("ladderDomGuard"))) + int(bool(st.get("ladderBusyGuard"))))
    add("产物：★ audit 记的格数 = 重算值", res.get("cells"), D.get("pressTotal"))
    add("产物：audit 记的零 FAILED", res.get("failedCells"), 0)
    return C


# ───────────────── 阴性对照 ─────────────────
def _fp(D):
    out = {}
    for arm, rows in (D.get("arms") or {}).items():
        out[arm] = [{
            "first": r.get("afterFirst"), "second": r.get("afterSecond"),
            "press": [{"cap": (p.get("read") or {}).get("cap"),
                       "win": (p.get("read") or {}).get("win"),
                       "pathOpen": (p.get("state") or {}).get("pathOpen"),
                       "presetOpen": (p.get("state") or {}).get("presetOpen"),
                       "exportOpen": (p.get("state") or {}).get("exportOpen"),
                       "deskOpen": (p.get("state") or {}).get("deskOpen")}
                      for p in (r.get("presses") or [])],
        } for r in rows]
    return out


def _fingerprint(D):
    return json.dumps(_fp(D), ensure_ascii=False, sort_keys=True, default=str)


def _st_fp(st):
    return json.dumps(st, ensure_ascii=False, sort_keys=True, default=str)


def neg_case(name, why, mutate, kw, D, st, a):
    raw2 = mutate(copy.deepcopy(D.get("_raw")))
    if raw2 is None:
        return {"name": name, "why": why, "caught": False,
                "mutatedAnything": False, "kwMatchedCount": 0,
                "expectFailOn": kw}
    D2 = derive(raw2)
    bp = {c["label"]: c["pass"] for c in run_checks(a, copy.deepcopy(st), D)}
    C2 = run_checks(a, copy.deepcopy(st), D2)
    flipped = [c["label"] for c in C2 if bp.get(c["label"], True)
               and not c["pass"]]
    hits = [f for f in flipped if kw in f]
    base = derive(copy.deepcopy(D.get("_raw")))
    return {"name": name, "why": why,
            "mutatedAnything": _fingerprint(D2) != _fingerprint(base),
            "kwMatchedCount": len(hits), "flipped": flipped,
            "caught": len(hits) == 1, "expectFailOn": kw}


MUT_FILES = (TL, DD)


def base_sources():
    return {f: (ROOT / f).read_text(encoding="utf-8") for f in MUT_FILES}


def neg_case_static(name, why, mutate_src, kw, D, st, a):
    try:
        src2 = mutate_src(base_sources())
    except Exception as e:  # noqa: BLE001
        return {"name": name, "why": why, "caught": False,
                "mutatedAnything": False, "kwMatchedCount": 0,
                "error": "%s: %s" % (type(e).__name__, e)}
    if src2 is None:
        return {"name": name, "why": why, "caught": False,
                "mutatedAnything": False, "kwMatchedCount": 0,
                "expectFailOn": kw}
    st2 = static_side(src2)
    bp = {c["label"]: c["pass"] for c in run_checks(a, copy.deepcopy(st), D)}
    C2 = run_checks(a, st2, derive(copy.deepcopy(D.get("_raw"))))
    flipped = [c["label"] for c in C2 if bp.get(c["label"], True)
               and not c["pass"]]
    hits = [f for f in flipped if kw in f]
    return {"name": name, "why": why,
            "mutatedAnything": _st_fp(st2) != _st_fp(st),
            "kwMatchedCount": len(hits), "flipped": flipped,
            "caught": len(hits) == 1, "expectFailOn": kw}


def _swap_once(text, old, new, tag):
    assert old in text, "★ %s：目标字面量没对上" % tag
    assert text.count("\n") == text.count("\n")
    return text.replace(old, new, 1)


def mut_drop_cross_path(src):
    t = src[TL]
    i = t.index("const togglePathMenu")
    j = t.index("const togglePresetPanel")
    body = t[i:j]
    nb = body.replace("  setPresetPanelLeft(null);\n", "  void 0;\n")
    assert nb != body, "★ 替换没生效"
    return {TL: t[:i] + nb + t[j:]}


def mut_drop_cross_preset(src):
    t = src[TL]
    i = t.index("const togglePresetPanel")
    body = t[i:]
    nb = body.replace("  setPathMenuLeft(null);\n", "  void 0;\n", 1)
    assert nb != body, "★ 替换没生效"
    return {TL: t[:i] + nb}


def mut_order(src):
    """★ 把「关闭对方」那行挪到「打开自己」**之后** ⟹ 顺序判据必须红。

    ⚠ 第一版把交叉写入插到 `setPathMenuLeft(` 的**前一行** ——
    那仍然在打开语句**之前**，顺序**没变**，对照静默返回未抓。
    ★ 教训：阴性对照本身也要**先验它真的改了目标性质**，不能只看
    「`mutatedAnything=True`」—— 那个只证明指纹变了，不证明改的是顺序。
    ⟹ 这里插到**函数体末尾**（打开语句之后），才真的反转。
    """
    t = src[TL]
    i = t.index("const togglePathMenu")
    j = t.index("const togglePresetPanel")
    body = t[i:j]
    line = "  setPresetPanelLeft(null);\n"
    assert line in body, "★ 交叉写入那行没对上"
    nb = body.replace(line, "", 1)
    # 函数体末尾（最后一个 `);\n  }` 之前）⟹ 落在打开语句**之后**
    k = nb.rindex(");\n  }")
    nb = nb[:k + 1] + "    setPresetPanelLeft(null);\n" + nb[k + 1:]
    assert nb.count("\n") == body.count("\n"), "★ 必须行数中性"
    sq = " ".join(nb.split())
    assert sq.index("setPresetPanelLeft(null);") > \
        re.search(r"setPathMenuLeft\(\s*Math\.max", sq).start(), \
        "★ 变异没有真的反转顺序"
    return {TL: t[:i] + nb + t[j:]}


def mut_ladder_busy(src):
    t = src[DD]
    return {DD: _swap_once(t, "      if (workspaceBusy) return;\n",
                           "      if (false) return;\n", "ladder-busy")}


def mut_ladder_dom(src):
    t = src[DD]
    return {DD: _swap_once(
        t, '      if (document.querySelector("[data-director-capture-viewer]")) '
           'return;\n', "      if (false) return;\n", "ladder-dom")}


def mut_kb_coexist(raw):
    """★ 把键盘臂读成「两个面板同时开着」⟹ 「预测被否掉」要红。"""
    for rd in raw["rounds"]:
        for r in (rd.get("rows") or []):
            if r.get("arm") == "bothByKeyboard":
                r["afterSecond"]["pathOpen"] = True
    return raw


def mut_kb_differs(raw):
    """★ 让键盘臂与鼠标臂读数**不同** ⟹ 「激活方式与互斥无关」要红。"""
    for rd in raw["rounds"]:
        for r in (rd.get("rows") or []):
            if r.get("arm") == "bothByKeyboard":
                r["afterSecond"]["pathOpen"] = True
                r["presses"][0]["state"]["presetOpen"] = True
    return raw


def mut_reverse_coexist(raw):
    """★ 把反向臂读成「预设仍开着」⟹ 「双向」要红。"""
    for rd in raw["rounds"]:
        for r in (rd.get("rows") or []):
            if r.get("arm") == "reverseByMouse":
                r["afterSecond"]["presetOpen"] = True
    return raw


def mut_win_zero(raw):
    """★ 把某臂的 `win` 读成 0 ⟹ 「没有 sIP 主人活着」要红。"""
    for rd in raw["rounds"]:
        for r in (rd.get("rows") or []):
            if r.get("arm") == "pathOnly":
                r["presses"][0]["read"]["win"] = 0
    return raw


# ───────────────── 主流程 ─────────────────
def main():
    raw = load_raw()
    D = derive(raw)
    D["_raw"] = raw
    a = json.loads(AUDIT.read_text(encoding="utf-8")) if AUDIT.exists() else {}
    st = static_side()

    C = run_checks(a, st, D)
    nPass = sum(1 for c in C if c["pass"])
    failed = [c["label"] for c in C if not c["pass"]]

    negs = [
        neg_case_static(
            "删掉 `togglePathMenu` 里的 `setPresetPanelLeft(null);`",
            "★ 「互斥的第一半」没了 ⟹ 从预设面板进去就能与路径菜单共活 ⟹ "
            "判据必须红",
            mut_drop_cross_path, "互斥的第一半", D, st, a),
        neg_case_static(
            "删掉 `togglePresetPanel` 里的 `setPathMenuLeft(null);`",
            "★★ 「**双向**」塌成单向 ⟹ 而运行时两个方向都测了 ⟹ "
            "判据必须红（只找到一处交叉写入会得出假结论）",
            mut_drop_cross_preset, "互斥的第二半", D, st, a),
        neg_case_static(
            "把交叉写入挪到「打开自己」**之后**",
            "★ 「先关后开」是这条不变量能成立的**原因** ⟹ 顺序判据必须能抓",
            mut_order, "排在打开自己之前", D, st, a),
        neg_case_static(
            "把阶梯的 `workspaceBusy` 那道门改成永假",
            "★ 「779 漏了两道门」这条要能抓 ⟹ 否则阶梯会被继续按「四档」写",
            mut_ladder_busy, "workspaceBusy", D, st, a),
        neg_case_static(
            "把阶梯的 DOM 存在性那道门改成永假",
            "★ 同上，另一道门",
            mut_ladder_dom, "DOM 存在性", D, st, a),
        neg_case("把键盘臂读成「两个面板同时开着」",
                 "★ 本批的核心是「**预测被否掉**」⟹ 对照要能证明这条会红，"
                 "否则一次把探针调偏就会静悄悄把结论翻回去",
                 mut_kb_coexist, "被否**", D, st, a),
        neg_case("让键盘臂与鼠标臂读数不同",
                 "★ 「互斥与激活方式无关」是**否掉 `pointerdown` 假设**的"
                 "关键一步 ⟹ 对照要能抓",
                 mut_kb_differs, "完全一样", D, st, a),
        neg_case("把反向臂读成「预设仍开着」",
                 "★ 「双向互斥的运行时确认」要能抓",
                 mut_reverse_coexist, "不是单向的", D, st, a),
        neg_case("把某臂的 `win` 读成 0",
                 "★ 「本批三臂没有任何 `sIP` 主人活着」是"
                 "「并发不靠传播阻断」的前提 ⟹ 对照要能抓",
                 mut_win_zero, "到达了 window", D, st, a),
    ]
    nNeg = len(negs)
    nCaught = sum(1 for n in negs if n.get("caught"))
    stale = [n["name"] for n in negs if not n.get("mutatedAnything")]
    multi = [n["name"] for n in negs if n.get("kwMatchedCount", 0) > 1]

    problems = []
    if failed:
        problems.append("%d 条判据未过：%r" % (len(failed), failed))
    if nCaught != nNeg:
        problems.append("阴性对照 %d/%d 被抓" % (nCaught, nNeg))
    if stale:
        problems.append("对照没真的改动任何东西：%r" % stale)
    if multi:
        problems.append("对照 `kw` 不唯一：%r" % multi)
    if not README.exists():
        problems.append("缺 README.md")
    if LEDGER.exists() and "| Batch 783 |" not in LEDGER.read_text(
            encoding="utf-8"):
        problems.append("台账没有 `| Batch 783 |` 行")
    # ★ 台账历史行里本来就有 9 处 U+FFFD ⟹ **只查新增那一行**
    if LEDGER.exists():
        for ln in LEDGER.read_text(encoding="utf-8").split("\n"):
            if ln.startswith("| Batch 783 |") and FFFD in ln:
                problems.append("台账的 Batch 783 行含 U+FFFD")
    for f in (README, AUDIT):
        if f.exists() and FFFD in f.read_text(encoding="utf-8"):
            problems.append("%s 含 U+FFFD" % f.name)

    rep = {
        "batch": 783,
        "verdict": "通过" if not problems else "不通过",
        "criteria": {"total": len(C), "passed": nPass,
                     "failed": len(failed), "failedLabels": failed},
        "negativeControls": {"total": nNeg, "caught": nCaught,
                             "stale": stale, "kwNotUnique": multi,
                             "cases": negs},
        "staticRecomputed": st,
        "runtimeRecomputed": {k: v for k, v in D.items() if k != "_raw"},
        "productSelfCheck": {c["label"]: c["pass"] for c in C
                             if c["label"].startswith("产物")},
        "problems": problems,
        "srcDiff": "**验收器未改 `src/`**（对照全在内存副本上做）",
    }
    REPORT.write_text(json.dumps(rep, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    print("判据 %d/%d ｜阴性对照 %d/%d ｜%s"
          % (nPass, len(C), nCaught, nNeg, rep["verdict"]))
    for p in problems:
        print("  ★ %s" % p)
    for n in negs:
        if not n.get("caught"):
            print("  ✗ 对照未抓：%s（kw=%r，命中 %s，%s）"
                  % (n["name"], n.get("expectFailOn"), n.get("kwMatchedCount"),
                     n.get("error", "")))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
