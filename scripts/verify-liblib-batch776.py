#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 776 验收器 —— **独立实现**，不 import 汇编器。

## 为什么要独立

本批验的是**一句挂在拍板项里的话**。如果我把汇编器的静态层抄进验收器，
那么「汇编器读错」和「我读错」会一起错 —— 而这批的结论要用来**缩小授权范围**，
错的方向恰恰是最坏的方向（「机制不存在」⟹ 「不用改」）。

## 本批特有的三个坑（775 刚教的，这里直接用上）

1. **搜索必须带作用域**（R117）。`block()` 找结束标记时若从文件头开始，
   会匹配到起点**之前**的同形行 ⟹ 空串 ⟹ **假零**，而且方向是
   「我们的机制不存在」。775 的 R107（抹白过头得假零）、R110（相对/绝对行号
   混用恒假）是同族。
2. **只抹注释、不抹字符串**（R107）。
3. **阴性对照的 `mutatedAnything` 必须实测**（R108）：比对变异前后的
   **派生指纹**，而不是自称。

## 阴性对照的鉴别力从哪来

「对照臂第 1 次 Escape 关掉了导出面板」是本批**唯一**证明
「实验臂的『什么都没发生』不是『面板本来就关不掉』」的读数。
所以我专门写一条阴性对照：**把对照臂的读数改成『没关』**，
必须让「测量有鉴别力」那条判据翻红 —— 否则那条判据是恒真的。
"""
import copy
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch776-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAWDIR = OUTDIR / "raw"
PROBEDIR = OUTDIR / "probes"
README = OUTDIR / "README.md"
LEDGER = ROOT / "docs/research/VERIFICATION_LEDGER.md"

RAW_FILES = ["vb776a.json"]
PROBE_FILES = ["dbg776a.py", "mk776audit.py"]
FFFD = "�"

IDS = ["xf", "panchor", "ptransform", "pose", "fov"]
PRESSES = 3
META = {"tries", "retried"}
GESTURE_ID_RE = re.compile(r"director-gesture-\d+-\d+")

#: 源码锚点（全部现读，**不引用别批的行号**）
GB = "src/components/director/useDirectorGestureBoundary.ts"
INSP = "src/components/director/DirectorInspector.tsx"
DESK = "src/components/director/DirectorDesk.tsx"
STORE = "src/store/directorStore.ts"


# ───────────────── 静态层（独立实现） ─────────────────
def blank_comments(s):
    """注释**抹白而不删** —— 行号不漂移。★ 只抹注释，不抹字符串（R107）。"""
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


def first(lines, pat, after=0):
    """首个匹配行的绝对行号。★ `after` 必须给，否则会跨作用域误匹配（R117）。"""
    rx = re.compile(pat)
    return next((n for n, ln in enumerate(lines, 1)
                 if n > after and rx.search(ln)), None)


def block(lines, start_pat, end_pat):
    s = first(lines, start_pat)
    if not s:
        return "", None
    e = first(lines, end_pat, after=s)          # ★ 作用域在起点之后
    if not e:
        return "", s
    return "\n".join(lines[s - 1:e]), s


def static_side():
    st = {}
    def load(rel):
        p = ROOT / rel
        if not p.exists():
            st["err"] = "缺源码 %s" % rel
            return []
        return blank_comments(p.read_text(encoding="utf-8")).split("\n")

    gl = load(GB)
    insp = load(INSP)
    desk = load(DESK)
    store = load(STORE)
    st["fileLines"] = len(gl)

    esc, escLine = block(gl, r'if \(event\.key === "Escape"\)',
                         r"^\s*\}\s*$")
    st["escapeBranchLine"] = escLine
    st["escapeBranchText"] = " ".join(esc.split())
    st["escapeHasActiveRefGuard"] = ("activeRef" in esc) if esc else None
    st["escapeHasPreventDefault"] = ("preventDefault" in esc) if esc else None
    st["escapeHasStopPropagation"] = ("stopPropagation" in esc) if esc else None
    st["escapeCallsCancel"] = ("cancel()" in esc) if esc else None
    st["onFocusIsBegin"] = bool(first(gl, r"onFocus: begin,"))
    st["onFocusLine"] = first(gl, r"onFocus: begin,")
    st["pointerUpEarlyReturnForNumber"] = bool(
        first(gl, r'event\.currentTarget\.type === "number"'))
    st["gestureSpreadSites"] = [
        n for n, ln in enumerate(insp, 1)
        if "{...(disabled ? {} : gesture)}" in ln
        or "{...(isAxisDisabled(index) ? {} : gesture)}" in ln]
    st["deskExposesActiveGestureAttr"] = bool(
        first(desk, r"data-director-active-gesture="))
    st["beginReturnsCommitted"] = bool(
        first(store, r'commandKind: "GESTURE_BEGIN"'))
    # ★ 反向自证：Escape 分支**之后**必须紧跟本文件自己的下一个分支
    #   （`event.key !== "Tab"` ⟹ `begin()`），否则「提取到的那段」
    #   可能是别处的同形代码 —— 假零的另一种来法。
    #   ⚠️ 这条检查**第一版是从 DirectorDesk.tsx 抄来的**（那边 Escape 分支后面
    #   跟的是 modifier C 分支）⟹ 在本文件恒假。同一个检查抄到新上下文，
    #   必须**重新读一遍那个上下文长什么样**。
    after_esc = gl[(escLine or 0):(escLine or 0) + 10] if escLine else []
    st["escFollowedByTabBranch"] = any(
        'event.key !== "Tab"' in ln for ln in after_esc)
    return st


# ───────────────── 原始读数（重算） ─────────────────
def load_raw():
    for f in RAW_FILES:
        if not (RAWDIR / f).exists():
            raise SystemExit("缺原始读数 %s —— 判失败，不许通过" % f)
    for f in PROBE_FILES:
        if not (PROBEDIR / f).exists():
            raise SystemExit("缺探针脚本 %s —— 判失败，不许通过" % f)
    raw = json.loads((RAWDIR / "vb776a.json").read_text(encoding="utf-8"))
    if len(raw.get("rounds") or []) != 2:
        raise SystemExit("轮数不是 2")
    return raw


def norm(o):
    if isinstance(o, dict):
        return {k: norm(v) for k, v in o.items() if k not in META}
    if isinstance(o, list):
        return [norm(x) for x in o]
    if isinstance(o, str):
        return GESTURE_ID_RE.sub("director-gesture-<id>", o)
    return o


def derive(raw):
    """★ 现算；**对缺格健壮**（缺格要变成一条判据红，而不是让验收器崩）。"""
    D = {"censusFailed": [], "missing": []}
    rows, census = {}, {}
    for rd in raw["rounds"]:
        for r in norm(rd.get("rows")):
            rows.setdefault((r.get("ctx"), r.get("family"), r.get("nth"),
                             bool(r.get("isControl"))), []).append(r)
        for c in norm(rd.get("census")):
            census.setdefault((c.get("ctx"), c.get("id"),
                               c.get("precondition")), []).append(c)
    D["rows"] = {k: v[0] for k, v in rows.items()}
    D["rowsN"] = len(D["rows"])
    for (ctx, fam, nth, ctl), rs in rows.items():
        if rs[0].get("FAILED"):
            D["missing"].append("%s/%s#%s: %s" % (ctx, fam, nth,
                                                  rs[0]["FAILED"]))
    D["census"] = {k: v[0] for k, v in census.items()}
    D["censusN"] = len(D["census"])
    for k, c in D["census"].items():
        if c.get("FAILED"):
            D["censusFailed"].append("%s/%s" % (k[0], k[1]))
    D["gesture"] = {k: c for k, c in D["rows"].items() if not k[3]}
    D["control"] = {k: c for k, c in D["rows"].items() if k[3]}
    D["roundsConsistent"] = (norm(raw["rounds"][0].get("rows"))
                             == norm(raw["rounds"][1].get("rows")))
    D["censusConsistent"] = (norm(raw["rounds"][0].get("census"))
                             == norm(raw["rounds"][1].get("census")))
    D["famMax"] = {f: max([c["live"] for c in D["census"].values()
                           if c.get("id") == f and c.get("live") is not None]
                          or [0]) for f in IDS}
    return D


# ───────────────── 判据 ─────────────────
def run_checks(a, st, D):
    C = []

    def add(label, got, want=None):
        if isinstance(got, bool) and want is None:
            C.append({"label": label, "pass": bool(got), "got": got})
        else:
            C.append({"label": label, "pass": (got == want), "got": got,
                      "want": want})

    G = D["gesture"]
    gk = sorted(G)
    Ctl = D["control"]
    ck = sorted(Ctl)

    # ── 静态 ──
    add("静态：Escape 分支找得到", _ok(st.get("escapeBranchLine")))
    add("静态：★ 提取到的 Escape 分支**之后**紧跟本文件的 `begin()` 分支"
        "（反证：那段不是别处的同形代码）",
        _ok(st.get("escFollowedByTabBranch")))
    add("静态：★ Escape 分支里**没有** activeRef 守卫 ⟹ 修法 (a) 尚未实现"
        "（一旦实现本条立刻变红）",
        st.get("escapeHasActiveRefGuard"), False)
    add("静态：Escape 分支仍 preventDefault（吞键的前提）",
        st.get("escapeHasPreventDefault"), True)
    add("静态：Escape 分支仍 stopPropagation（桌的阶梯看不到它的原因）",
        st.get("escapeHasStopPropagation"), True)
    add("静态：Escape 分支仍调 cancel()（手势被清空的机制）",
        st.get("escapeCallsCancel"), True)
    add("静态：★ `onFocus: begin` 仍在 ⟹ 修法 (b) 尚未实现"
        "（一旦实现本条立刻变红）", _ok(st.get("onFocusIsBegin")))
    add("静态：onPointerUp 对 input[type=number] 的提前 return 仍在",
        _ok(st.get("pointerUpEarlyReturnForNumber")))
    add("静态：`{...gesture}` 恰 5 处展开",
        len(st.get("gestureSpreadSites") or []), 5)
    add("静态：桌根仍暴露 data-director-active-gesture（本批读数方法的前提）",
        _ok(st.get("deskExposesActiveGestureAttr")))
    add("静态：store 的 GESTURE_BEGIN 段在位", _ok(st.get("beginReturnsCommitted")))

    # ── 覆盖与一致性 ──
    add("覆盖：没有 FAILED 格（缺格会变成红，而不是崩掉）",
        _ok(not D["missing"]), True)
    add("覆盖：普查无 FAILED", _ok(not D["censusFailed"]), True)
    add("一致性：两轮测量一致（**已归一化**手势 id 与 tries/retried）",
        D.get("roundsConsistent"), True)
    add("一致性：两轮普查一致（同上归一化）",
        D.get("censusConsistent"), True)

    # ── 普查：五族全覆盖，每族都有非空的一次 ──
    for f in IDS:
        add("普查：族 %r 至少在一个上下文里**真的非空**"
            "（「全 0」长得像「不存在」，所以每族都要有一次非空）" % f,
            _ok(D["famMax"].get(f, 0) > 0), True)
    add("普查：★ 每一行都自证（0 个，或有面积且 input type 与源码标注一致）",
        _ok(all(c.get("selfJustified") is True
                for c in D["census"].values() if not c.get("FAILED"))), True)
    add("普查：★ 非空行的 input type 与源码标注逐族一致（number/range 不混）",
        _ok(all(c.get("type") == c.get("wantType")
                for c in D["census"].values() if c.get("live"))), True)
    add("★ 普查在**前置到位**后共找到的可用控件数 ≥ 50"
        "（5 族各至少一次非空；这是 R112「别把少测记成不存在」的量化下限）",
        _ok(sum(D["famMax"].values()) >= 50), True)

    # ── 实验臂：核心三条 ──
    add("实验臂：每一格都真的**聚焦起了手势**"
        "（onFocus: begin ⟹ beginDirectorGesture 返回 COMMITTED）",
        sum(1 for k in gk if G[k].get("isGestureElement") is True), len(gk))
    add("实验臂：★ 第 1 次 Escape —— 手势被清空，"
        "而导出面板与桌**一个都没关**（吞键的直接后果）",
        sum(1 for k in gk
            if G[k]["presses"][0]["gesture"] == ""
            and G[k]["presses"][0]["exportPresent"] is True
            and G[k]["presses"][0]["deskOpen"] is True), len(gk))
    later = [(k, p) for k in gk for p in G[k]["presses"][1:]]
    add("★ 实验臂：第 2/3 次 Escape **全部毫无作用** —— "
        "而那正是「(b) 单独改」之后的世界 ⟹ (b) 单独改是空操作（直接观测）",
        sum(1 for _, p in later
            if p["gesture"] == "" and p["exportPresent"] is True
            and p["deskOpen"] is True), len(later))
    add("实验臂：焦点在每次按压后都**仍在**控件上（Escape 不移焦，"
        "所以「无手势但焦点在控件上」这个状态确实可达）",
        sum(1 for k in gk for p in G[k]["presses"] if p["focusStill"] is True),
        len(gk) * PRESSES)
    add("实验臂：每格都自证落点（焦点 ok、起始手势空、导出面板先开着）",
        _ok(all((G[k].get("focus") or {}).get("ok") is True
                and G[k].get("gestureBeforeFocus") == ""
                and G[k].get("exportOpenBefore") is True for k in gk)), True)
    add("实验臂：每格都按了 %d 次" % PRESSES,
        _ok(all(len(G[k].get("presses") or []) == PRESSES for k in gk)), True)

    # ── 对照臂：证明测量有鉴别力 ──
    add("对照臂：恰 1 格", len(ck), 1)
    if ck:
        c = Ctl[ck[0]]
        add("对照臂：★ 聚焦后**没有**手势 ⟹ 它真的是非 gesture 控件"
            "（否则对照不成立）", c.get("isGestureElement"), False)
        add("对照臂：★ 第 1 次 Escape **关掉了导出面板** ⟹ "
            "「实验臂什么都没发生」不是「面板本来就关不掉」",
            c["presses"][0]["exportPresent"], False)
        add("对照臂：第 2 次 Escape **关掉了桌** ⟹ 桌的 Escape 阶梯本身在工作",
            c["presses"][1]["deskOpen"], False)

    # ── 产物纪律 ──
    add("产物：runtime-audit.json 在位", AUDIT.exists())
    add("产物：更正恰为 C776-1",
        [c.get("id") for c in (a.get("corrections") or [])], ["C776-1"])
    add("产物：教训为 R111–R118",
        [x.get("id") for x in (a.get("probeLessons") or [])],
        ["R111", "R112", "R113", "R114", "R115", "R116", "R117", "R118"])
    add("产物：汇编器与我**独立算出的** Escape 分支行号一致",
        (a.get("static") or {}).get("escapeBranchLine"),
        st.get("escapeBranchLine"))
    add("产物：汇编器与我独立算出的 onFocus 行号一致",
        (a.get("static") or {}).get("onFocusLine"), st.get("onFocusLine"))
    add("产物：★ 两轮**逐字节**并不相同（手势 id 内嵌时间戳）"
        "，而归一化后一致 —— 这件事必须被记下来而不是被藏起来",
        (a.get("comparability") or {}).get("rawRoundsByteIdentical"), False)
    add("产物：归一化说明存在", _ok((a.get("comparability") or {})
                                    .get("normalized")))
    return C


def _ok(x):
    return bool(x)


# ───────────────── 阴性对照 ─────────────────
def _fingerprint(D):
    """派生结果的规范指纹 —— 实测「变异到底改变了任何判据输入没有」（R108）。"""
    return json.dumps(_norm_for_fp(D), ensure_ascii=False, sort_keys=True,
                      default=str)


def _norm_for_fp(o):
    if isinstance(o, dict):
        return {str(k): _norm_for_fp(v) for k, v in o.items()
                if not (isinstance(k, str) and k.startswith("_"))}
    if isinstance(o, (list, tuple)):
        return [_norm_for_fp(x) for x in o]
    return o


def neg_case(name, why, mutate, kw, D, st, a):
    raw2 = mutate(copy.deepcopy(D.get("_raw")))
    if raw2 is None:
        return {"name": name, "why": why, "caught": False,
                "mutatedAnything": False, "kwMatchedCount": 0,
                "expectFailOn": kw}
    D2 = derive(raw2)
    C2 = run_checks(a, copy.deepcopy(st), D2)
    base = run_checks(a, copy.deepcopy(st), derive(copy.deepcopy(D.get("_raw"))))
    bp = {c["label"]: c["pass"] for c in base}
    flipped = [c["label"] for c in C2
               if bp.get(c["label"], True) and not c["pass"]]
    hits = [f for f in flipped if kw in f]
    return {"name": name, "why": why,
            "mutatedAnything": _fingerprint(D2) != _fingerprint(
                derive(copy.deepcopy(D.get("_raw")))),
            "kwMatchedCount": len(hits), "flipped": flipped,
            "caught": len(hits) == 1, "expectFailOn": kw}


def negative_controls(D, st, a):
    out = []

    def m_ctrl_closed(raw):
        n = 0
        for rd in raw["rounds"]:
            for r in rd.get("rows") or []:
                if r.get("isControl") and not r.get("FAILED"):
                    r["presses"][0]["exportPresent"] = True
                    r["presses"][1]["deskOpen"] = True
                    n += 1
        return raw if n else None

    def m_later_alive(raw):
        n = 0
        for rd in raw["rounds"]:
            for r in rd.get("rows") or []:
                if not r.get("isControl") and not r.get("FAILED"):
                    for p in r["presses"][1:]:
                        p["exportPresent"] = False
                        p["gesture"] = "director-gesture-<id>"
                        n += 1
        return raw if n else None

    def m_no_gesture_on_focus(raw):
        n = 0
        for rd in raw["rounds"]:
            for r in rd.get("rows") or []:
                if not r.get("FAILED"):
                    r["gestureAfterFocus"] = ""
                    r["isGestureElement"] = False
                    n += 1
        return raw if n else None

    def m_focus_moved(raw):
        n = 0
        for rd in raw["rounds"]:
            for r in rd.get("rows") or []:
                if not r.get("FAILED"):
                    for p in r.get("presses") or []:
                        p["focusStill"] = False
                    n += 1
        return raw if n else None

    def m_drop_family(raw):
        n = 0
        for rd in raw["rounds"]:
            rd["census"] = [c for c in (rd.get("census") or [])
                            if c.get("id") != "pose"]
            n += 1
        return raw if n else None

    def m_nonexistent(raw):
        n = 0
        for rd in raw["rounds"]:
            for r in rd.get("rows") or []:
                r["__不存在的字段__"] = 1
                n += 1
        return raw if n else None

    out.append(neg_case(
        "把对照臂改成「1 次 Escape 没关面板也没关桌」 ⟹ "
        "「测量有鉴别力」必须红",
        "证明那条判据不是恒真 —— 没有它，实验臂的『什么都没发生』"
        "无法区分「缺陷」与「面板本来就关不掉」",
        # ★ kw **必须取自判据标签里的字面量**，不能取自判据的「意图」。
        #   本文件第一版写的是 kw="测量有鉴别力" —— 那句话只出现在 `why` 里，
        #   标签里根本没有 ⟹ 翻红列表里一条都匹配不上 ⟹ 被读成「判据不灵」。
        #   （775 也踩过一次同一个坑：**这是复发性陷阱，不是手滑。**）
        m_ctrl_closed, "第 1 次 Escape **关掉了导出面板**", D, st, a))
    out.append(neg_case(
        "把第 2/3 次按压改成「起了作用」 ⟹ 「(b) 单独改是空操作」必须红",
        "证明本批最核心那条推论的判据真有鉴别力",
        m_later_alive, "单独改", D, st, a))
    out.append(neg_case(
        "把「聚焦起了手势」全改成没起 ⟹ 相关判据必须红",
        "证明「onFocus 不起手势」这个读数不会被放过（它曾差点被我当成机制）",
        m_no_gesture_on_focus, "聚焦起了手势", D, st, a))
    out.append(neg_case(
        "把「焦点仍在控件上」全改成 False ⟹ 该判据必须红",
        "证明「无手势但焦点在控件上」这个**可达状态**的判据不是恒真",
        m_focus_moved, "焦点在每次按压后", D, st, a))
    out.append(neg_case(
        "整族删掉 pose 的普查行 ⟹ 「每族至少一次非空」必须红，且不许崩",
        "证明 derive() 对缺格健壮",
        m_drop_family, "至少在一个上下文里", D, st, a))
    out.append(neg_case(
        "★ 对照自己没改成：改一个 raw 里不存在的字段名 ⟹ 不许有判据翻红",
        "mutatedAnything 为 false 时这条对照的结论是空的，必须自证出来（R108）",
        m_nonexistent, "__永不匹配__", D, st, a))
    return out


# ───────────────── 台账 / README ─────────────────
def artifact_checks():
    C = []
    if not LEDGER.exists():
        return [{"label": "台账在位", "pass": False, "got": "缺"}]
    txt = LEDGER.read_text(encoding="utf-8")
    lines = [ln for ln in txt.split("\n") if ln.strip()]
    mine = [ln for ln in lines if re.match(r"^\|\s*Batch\s+776\s*\|", ln)]
    C.append({"label": "台账：Batch 776 恰有一行", "pass": len(mine) == 1,
              "got": len(mine)})
    if mine:
        C.append({"label": "台账：该行无 U+FFFD", "pass": FFFD not in mine[0],
                  "got": mine[0].count(FFFD)})
        C.append({"label": "台账：该行恰 4 个竖线（3 列）",
                  "pass": mine[0].count("|") == 4, "got": mine[0].count("|")})
    if README.exists():
        rt = README.read_text(encoding="utf-8")
        bad = [ln for ln in rt.split("\n")
               if re.match(r"^\+\|\s*\d+[a-z]?\s*\|", ln)]
        C.append({"label": "★ README 里没有裸数字开头的 markdown 表行"
                    "（会骗过 pre-commit 的 added_batch_numbers）",
                  "pass": not bad, "got": bad[:2]})
        C.append({"label": "README 无 U+FFFD", "pass": FFFD not in rt,
                  "got": rt.count(FFFD)})
    return C


def main():
    if not AUDIT.exists():
        print("缺少 runtime-audit.json（先跑 mk776audit.py）")
        return 1
    a = json.loads(AUDIT.read_text(encoding="utf-8"))
    st = static_side()
    try:
        raw = load_raw()
        rawErr = None
    except Exception as e:  # noqa: BLE001
        raw, rawErr = None, str(e)
    if rawErr:
        checks = [{"label": "原始读数可用（raw + 两个 probes/）", "pass": False,
                   "got": rawErr}]
        neg = []
    else:
        D = derive(raw)
        D["_raw"] = raw
        checks = run_checks(a, st, D) + artifact_checks()
        neg = negative_controls(D, st, a)
    kw_bad = [n["name"] for n in neg if n.get("kwMatchedCount") != 1]
    inert = [n["name"] for n in neg if n.get("mutatedAnything") is False]
    npass = sum(1 for c in checks if c["pass"])
    total = len(checks)
    neg_ok = sum(1 for n in neg
                 if n.get("mutatedAnything") is False
                 or (n["caught"] and n.get("kwMatchedCount") == 1))
    ok = npass == total and neg_ok == len(neg)
    REPORT.write_text(json.dumps(
        {"batch": 776, "checks": checks, "pass": npass, "total": total,
         "negativeControls": neg, "negativeCaught": neg_ok,
         "negativeTotal": len(neg), "negativeKwBroken": kw_bad,
         "negativeInert": inert, "rawError": rawErr, "ok": ok},
        ensure_ascii=False, indent=1), encoding="utf-8")
    for c in checks:
        if not c["pass"]:
            print("FAIL  %s  got=%s" % (c["label"], json.dumps(
                c.get("got"), ensure_ascii=False)[:300]))
    print("\n验收 %d/%d 通过" % (npass, total))
    print("阴性对照 %d/%d 符合预期" % (neg_ok, len(neg)))
    for n in neg:
        if n.get("mutatedAnything") is False:
            print("  · %s（对照自己没改成，其结论为空，预期如此）" % n["name"])
        elif n.get("kwMatchedCount") != 1:
            print("  ✗ %s 命中 %s 条（期望恰好 1）"
                  % (n["name"], n.get("kwMatchedCount")))
        elif not n["caught"]:
            print("  ✗ 漏放：%s  翻红=%r" % (n["name"], (n.get("flipped") or [])[:4]))
    print("batch 776 %s" % ("通过" if ok else "不通过"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
