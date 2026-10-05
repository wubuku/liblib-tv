#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 784 验收器 —— **独立实现**，不 import 汇编器，也不 import 普查器

## 本批要防的错误方向

本批的结论是「`sIP` 与 bubble **共活**时，一次 Escape 只关 `sIP` 那个」。
四个方向各自有代价：

- 若把「**键盘下可达**」漏掉（只报鼠标臂的结果）⟹ 会得出「外点关闭已经
  保证了互斥」⟹ **D1i 整个消失**，而它正是本批唯一的缺陷。
- 若把「**`sIP` 单独活着时也要按两次**」漏掉 ⟹ 会把 D1i 说成
  「只有共活才有问题」⟹ 而 782 那条读数会被当成孤例。
- 若把「**只有 3 个门状态有外点关闭**」漏掉 ⟹ 授权文本继续按
  「层内 Escape 只关层」写 ⟹ 而 774 那个 2/6 的现象没有机制层解释。
- 若信了 raw 里那个 `coLive` 字段 ⟹ `ctxThenLibMouse` 会被算成共活 ⟹
  「外点关闭只挡鼠标」这条**直接翻掉**（R149）。

## 静态层为什么算「独立」

普查器（`census784.py`）用「取最近的前置 `DECL_RX` 声明 + 括号配对」找处理器体。
本验收器**用另一种分解**：从 `addEventListener(` 的第二个实参出发，
**先取实参文本本身**（`([A-Za-z_$][\w$]*|)`），再按「是标识符还是内联箭头」
分别处理；并且**不复用**普查器的 `handler_body`。

★ 更重要的是：验收器**自己重算**外点关闭清单，而不是读 `census784.json`
—— 否则「改源码」的阴性对照会作用在一个 JSON 上，什么也测不到。

## 沿用 775–783 的纪律

- 阴性对照的 `mutatedAnything` **实测**、`kw` **唯一**
- ★ **源码变异必须行数中性**（782 立）
- ★ 改源码的对照要能真的让**重算结果**变（784 新增：因为静态层是重算的）
"""
import copy
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch784-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAWDIR = OUTDIR / "raw"
PROBEDIR = OUTDIR / "probes"
README = OUTDIR / "README.md"
LEDGER = ROOT / "docs/research/VERIFICATION_LEDGER.md"

RAW_FILES = ["census784.json", "vb784a.json"]
PROBE_FILES = ["census784.py", "dbg784a.py", "mk784audit.py"]
FFFD = "�"
META = {"tries", "retried"}
TREE = "src/components/director/DirectorObjectTree.tsx"
VP = "src/components/director/DirectorViewport.tsx"
ARMS = ["ctxThenLibMouse", "ctxThenLibKeyboard", "ctxOnly", "libOnly"]
PRESSES = 2
ROUNDS = 2

STATES = ["viewerCaptureId", "contextMenu", "open", "pathMenuLeft",
          "presetPanelLeft", "motionPathDraft", "modelLibraryOpen",
          "activeDirectorNodeId", "exportPanelOpen", "followTargetId"]
POINTER_EVENTS = ("mousedown", "pointerdown", "click", "touchstart")


def squash(s):
    return " ".join(s.split())


def brace_body(text, start):
    cb = text.find("{", start)
    if cb < 0:
        return None
    depth = 0
    for i in range(cb, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[cb:i + 1]
    return None


def setter(state):
    return "set" + state[0].upper() + state[1:]


def scan_outside_close(text, rel):
    """★ **独立**实现：逐条 pointer/mouse 监听 → 取**它自己的处理器体** →
    要求 `set<S>(null)` **直接**在里面。"""
    found = {s: [] for s in STATES}
    for m in re.finditer(
            r"(?:window|document|[\w.]+)\s*\.\s*addEventListener\(\s*"
            r"[\"']([a-z]+)[\"']\s*,\s*([A-Za-z_$][\w$]*|\()", text):
        ev, arg = m.group(1), m.group(2)
        if ev not in POINTER_EVENTS:
            continue
        if arg == "(":                       # 内联箭头：`(e) => {`
            body = brace_body(text, m.end() - 1)
        else:
            # ★ 取**在监听之前**的最后一个声明 —— 不是全文最后一个。
            #   原因：`DirectorTimeline` 里有**两个**都叫 `close` 的函数
            #   （两个 effect 各一个）⟹ 取「全文最后一个」会把 `:569` 那条
            #   监听算到**另一个** `close` 身上 ⟹ 漏掉 `pathMenuLeft`。
            #   ★ 这条是**两个独立实现互相抓到的**（782 立的老规矩）。
            decls = [d for d in re.finditer(
                r"(?:const|let|var|function)\s+%s\b" % re.escape(arg), text)
                if d.start() < m.start()]
            if not decls:
                continue
            d = decls[-1]
            body = brace_body(text, d.end())
        if not body:
            continue
        for s in STATES:
            if re.search(r"\b%s\s*\(\s*null" % setter(s), body):
                found[s].append({"event": ev, "handler": arg, "file": rel,
                                 "line": text[:m.start()].count("\n") + 1})
    return found


# ───────────────── 静态层 ─────────────────
def static_side(sources=None):
    sources = sources or {}
    st = {}

    def load(rel):
        if rel in sources:
            return sources[rel]
        p = ROOT / rel
        return p.read_text(encoding="utf-8") if p.exists() else None

    tree, vp = load(TREE), load(VP)
    if tree is None or vp is None:
        return {"err": "缺源码"}
    # ★ **重算**外点关闭清单（扫全仓，源码优先于 `sources`）
    found = {s: [] for s in STATES}
    for p in sorted(list((ROOT / "src").rglob("*.ts")) +
                    list((ROOT / "src").rglob("*.tsx"))):
        rel = str(p.relative_to(ROOT))
        txt = sources.get(rel, p.read_text(encoding="utf-8"))
        sub = scan_outside_close(txt, rel)
        for s in STATES:
            found[s] += sub[s]
    withOc = sorted(s for s in STATES if found[s])
    withoutOc = sorted(s for s in STATES if not found[s])
    st["statesWithOutsideClose"] = withOc
    st["statesWithoutOutsideClose"] = withoutOc
    st["events"] = {s: sorted({o["event"] for o in found[s]}) for s in withOc}
    st["contextMenuSites"] = found["contextMenu"]
    # ★ 树那个主人的外点关闭：`mousedown` + `close` 里**直接**写
    eff = brace_body(tree, tree.rindex("useEffect(")) or ""
    st["treeMousedown"] = 'addEventListener("mousedown", close)' in eff
    st["treeCloseDirect"] = bool(re.search(
        r"const close = \(event: MouseEvent\) => \{[^}]*setContextMenu\(null\);",
        eff, re.S))
    # ★ 模型库触发器：`<button type="button" onClick=…>` ⟹ 键盘 Enter 只 click
    iAttr = vp.index("data-director-model-library-trigger")
    trig = vp[vp.rindex("<button", 0, iAttr):vp.index(">", iAttr) + 1]
    st["libTriggerIsButton"] = trig.startswith("<button")
    st["libTriggerType"] = bool(re.search(r'type="button"', trig))
    # ★ 词边界：`data-onClick` 里**含有** `onClick` ⟹ 裸 `in` 会恒真
    st["libTriggerOnClick"] = bool(re.search(r"(?<![\w-])onClick", trig))
    return st


# ───────────────── 原始读数 ─────────────────
def load_raw():
    for f in RAW_FILES:
        if not (RAWDIR / f).exists():
            raise SystemExit("缺原始读数 %s —— 判失败，不许通过" % f)
    for f in PROBE_FILES:
        if not (PROBEDIR / f).exists():
            raise SystemExit("缺探针脚本 %s —— 判失败，不许通过" % f)
    raw = json.loads((RAWDIR / "vb784a.json").read_text(encoding="utf-8"))
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


def coLive(D, arm):
    a2 = _a(D, arm).get("after2") or {}
    return bool(a2.get("ctxOpen") is True and a2.get("libOpen") is True)


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

    add("静态：缺源码", st.get("err") is None, True)
    # ── 静态：★ 重算的外点关闭清单 ──
    add("静态：★★ 独立重算：有外点关闭的门状态 = %r"
        % (st.get("statesWithOutsideClose") or []),
        st.get("statesWithOutsideClose"),
        ["contextMenu", "pathMenuLeft", "presetPanelLeft"])
    add("静态：★ 没有外点关闭的门状态 %d 个（预测 7）"
        % len(st.get("statesWithoutOutsideClose") or []),
        len(st.get("statesWithoutOutsideClose") or []), 7)
    add("静态：★★ 那 3 个的外点事件**各不相同** ⟹ 逐个手写、无统一机制",
        st.get("events"),
        {"contextMenu": ["mousedown"], "pathMenuLeft": ["pointerdown"],
         "presetPanelLeft": ["pointerdown"]})
    add("静态：★ 树那个主人的外点关闭挂在 **`mousedown`** 上",
        _ok(st.get("treeMousedown")))
    add("静态：★ 那个 `close` 里**直接** `setContextMenu(null)`（不是一跳间接）",
        _ok(st.get("treeCloseDirect")))
    add("静态：★ 模型库触发器是 `<button …>`", _ok(st.get("libTriggerIsButton")))
    add("静态：★★ 模型库触发器是 `type=\"button\"` ⟹ 键盘 `Enter` 激活它"
        "**只产生 `click`、不产生 `mousedown`**",
        _ok(st.get("libTriggerType")))
    add("静态：★ 模型库触发器用 `onClick` 激活", _ok(st.get("libTriggerOnClick")))

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
        add("原始：%s 导出面板起点**开着**（阶梯那档有目标）" % arm,
            (r.get("after1") or {}).get("exportOpen"), True)

    # ── 预测 D：★ 鼠标激活**不**共活 ──
    add("预测 D：mouse 臂第 1 步右键菜单**开着**",
        (_a(D, "ctxThenLibMouse").get("after1") or {}).get("ctxOpen"), True)
    add("预测 D：mouse 臂第 2 步模型库**开着**",
        (_a(D, "ctxThenLibMouse").get("after2") or {}).get("libOpen"), True)
    add("预测 D：★★ mouse 臂第 2 步后**右键菜单被关掉了** ⟹ `mousedown` "
        "关掉了它 ⟹ 「鼠标下不共活」成立",
        (_a(D, "ctxThenLibMouse").get("after2") or {}).get("ctxOpen"), False)
    add("预测 D：mouse 臂**不共活**", coLive(D, "ctxThenLibMouse"), False)

    # ── 预测 E：★★ 键盘激活**共活** ──
    add("预测 E：keyboard 臂第 1 步右键菜单**开着**",
        (_a(D, "ctxThenLibKeyboard").get("after1") or {}).get("ctxOpen"), True)
    add("预测 E：keyboard 臂第 2 步模型库**开着**",
        (_a(D, "ctxThenLibKeyboard").get("after2") or {}).get("libOpen"), True)
    add("预测 E：★★★ keyboard 臂第 2 步后**右键菜单仍开着** ⟹ "
        "★ **共活在键盘下可达**（「外点关闭只挡鼠标」）",
        (_a(D, "ctxThenLibKeyboard").get("after2") or {}).get("ctxOpen"), True)
    add("预测 E：keyboard 臂**共活**", coLive(D, "ctxThenLibKeyboard"), True)

    # ── 预测 F：★★ 共活时一次只关 `sIP` 那个 ──
    kb = _a(D, "ctxThenLibKeyboard")
    p1, p2 = kb["presses"][0], kb["presses"][1]
    add("预测 F：第 1 次 `cap==0` **且** `win==0` ⟹ `sIP` 截断整条链",
        (p1["read"].get("cap"), p1["read"].get("win")), (0, 0))
    add("预测 F：★ 第 1 次后**模型库关掉了**（`sIP` 那个先关）",
        p1["state"].get("libOpen"), False)
    add("预测 F：★★★ 第 1 次后**右键菜单留在原地** ⟹ ★ **一次 Escape 只关 "
        "`sIP` 那个**，bubble 那个**无反馈地留着**",
        p1["state"].get("ctxOpen"), True)
    add("预测 F：★ 第 1 次后**导出面板也留在原地** ⟹ 桌的阶梯**也跑不到**",
        p1["state"].get("exportOpen"), True)
    add("预测 F：★ 第 2 次后**右键菜单关掉了** ⟹ **要按两次 Escape**",
        p2["state"].get("ctxOpen"), False)
    add("预测 F：第 2 次后导出面板也关掉了 ⟹ 第 2 次阶梯才跑",
        p2["state"].get("exportOpen"), False)

    # ── 预测 G：两个对照臂 ──
    co = _a(D, "ctxOnly")["presses"][0]
    lo = _a(D, "libOnly")["presses"][0]
    add("对照：ctxOnly 第 1 次 `cap>=1` ⟹ 没有 `sIP` 主人挡路",
        (co["read"].get("cap") or 0) >= 1)
    add("对照：ctxOnly 第 1 次右键菜单**关掉了**",
        co["state"].get("ctxOpen"), False)
    add("对照：★ ctxOnly 第 1 次**导出面板也关掉了** ⟹ 两个 bubble 主人并发"
        "（782 的 J4 再次成立）", co["state"].get("exportOpen"), False)
    add("对照：libOnly 第 1 次 `cap==0` ⟹ `sIP` 截断",
        lo["read"].get("cap"), 0)
    add("对照：libOnly 第 1 次模型库**关掉了**", lo["state"].get("libOpen"),
        False)
    add("对照：★★ libOnly 第 1 次**导出面板仍在** ⟹ ★ **`sIP` 单独活着时，"
        "Escape 也要按两次**（782 读数第二次复现）",
        lo["state"].get("exportOpen"), True)

    # ── 预测 H：★ raw 里的 `coLive` 派生字段与重算不符 ──
    mism = [k for k in ARMS if _a(D, k).get("coLive") is not None
            and bool(_a(D, k)["coLive"]) != coLive(D, k)]
    add("预测 H：★★ raw 的 `coLive` 字段与重算不符的臂 = %r ⟹ "
        "★ 那个字段**漏了「第一个是不是还开着」**这一检查（R149）"
        % mism, mism, ["ctxThenLibMouse"])

    # ── 产物自洽 ──
    own = a.get("outsideClose") or {}
    res = a.get("results") or {}
    add("产物：audit.batch=784", a.get("batch"), 784)
    add("产物：★ audit 的「有外点关闭」清单 = 独立重算",
        own.get("withOutsideClose"), st.get("statesWithOutsideClose"))
    add("产物：★ audit 的「没有外点关闭」数 = 独立重算",
        len(own.get("withoutOutsideClose") or []),
        len(st.get("statesWithoutOutsideClose") or []))
    add("产物：★ audit 的外点事件表 = 独立重算", own.get("events"),
        st.get("events"))
    add("产物：★ audit 记的「键盘下共活」= 重算值",
        res.get("keyboardCoLive"), coLive(D, "ctxThenLibKeyboard"))
    add("产物：★ audit 记的「鼠标下共活」= 重算值",
        res.get("mouseCoLive"), coLive(D, "ctxThenLibMouse"))
    add("产物：★ audit 记的 raw 字段不符臂数 = 重算值",
        sorted(res.get("rawFieldMismatchArms") or []), sorted(mism))
    add("产物：★ audit 记的**按压格数**（跨轮）= 重算值",
        res.get("pressCells"), D.get("pressTotal"))
    add("产物：★ audit 记的**行数** = %d 臂 × %d 轮"
        % (len(ARMS), ROUNDS), res.get("cells"),
        len(ARMS) * ROUNDS)
    add("产物：audit 记的零 FAILED", res.get("failedCells"), 0)
    return C


# ───────────────── 阴性对照 ─────────────────
def _fp(D):
    return json.dumps({k: [{kk: vv for kk, vv in r.items() if kk != "tries"}
                           for r in v] for k, v in (D.get("arms") or {}).items()},
                      ensure_ascii=False, sort_keys=True, default=str)


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
            "mutatedAnything": _fp(D2) != _fp(base),
            "kwMatchedCount": len(hits), "flipped": flipped,
            "caught": len(hits) == 1, "expectFailOn": kw}


MUT_FILES = (TREE, VP)


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


def mut_no_mousedown(src):
    t = src[TREE]
    old = 'window.addEventListener("mousedown", close);'
    assert old in t, "★ mousedown 那行没对上"
    t = t.replace(old, 'window.addEventListener("never", close);', 1)
    assert t.count("\n") == src[TREE].count("\n")
    return {TREE: t}


def mut_one_hop(src):
    """★ 把「直接写」改成**一跳间接** ⟹ 「直接出现」这条判据必须红。"""
    t = src[TREE]
    old = "      setContextMenu(null);\n    };\n    const esc"
    assert old in t, "★ 目标片段没对上"
    t = t.replace(
        old,
        "      queueMicrotask(() => setContextMenu(null));\n    };\n    const esc",
        1)
    assert t.count("\n") == src[TREE].count("\n")
    return {TREE: t}


def mut_trigger_type(src):
    t = src[VP]
    i = t.index("data-director-model-library-trigger")
    o = t.rindex("<button", 0, i)
    head = t[o:i]
    assert 'type="button"' in head, "★ type 那一行没对上"
    nt = head.replace('type="button"', 'type="submit"') + t[i:]
    out = t[:o] + nt
    assert out.count("\n") == t.count("\n")
    return {VP: out}


def mut_no_onclick(src):
    t = src[VP]
    i = t.index("data-director-model-library-trigger")
    o = t.rindex("<button", 0, i)
    close = t.index(">", i)
    head = t[o:close]
    assert re.search(r"(?<![\w-])onClick", head), "★ onClick 不在开标签里"
    out = t[:o] + re.sub(r"(?<![\w-])onClick", "data-onClick", head) + t[close:]
    assert out.count("\n") == t.count("\n")
    return {VP: out}


def mut_kb_not_colive(raw):
    for rd in raw["rounds"]:
        for r in (rd.get("rows") or []):
            if r.get("arm") == "ctxThenLibKeyboard":
                r["after2"]["ctxOpen"] = False
    return raw


def mut_press1_closes_ctx(raw):
    for rd in raw["rounds"]:
        for r in (rd.get("rows") or []):
            if r.get("arm") == "ctxThenLibKeyboard":
                r["presses"][0]["state"]["ctxOpen"] = False
    return raw


def mut_libonly_closes_export(raw):
    for rd in raw["rounds"]:
        for r in (rd.get("rows") or []):
            if r.get("arm") == "libOnly":
                r["presses"][0]["state"]["exportOpen"] = False
    return raw


def mut_fix_rawfield(raw):
    """★ 把 raw 里那个错的 `coLive` 字段**改成对的** ⟹ 「派生字段是错的」要红。"""
    for rd in raw["rounds"]:
        for r in (rd.get("rows") or []):
            if r.get("arm") == "ctxThenLibMouse":
                r["coLive"] = False
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
            "把树那个主人的 `mousedown` 外点关闭改成一个永不触发的事件",
            "★ 「独立重算的有外点关闭清单」必须少掉 `contextMenu` ⟹ "
            "「只有 3 个有」这条要能被抓",
            # ★ kw 必须**只**在那一条标签里出现：「独立重算」会命中 4 条
            #   （1 条静态 + 3 条产物自洽），而「有外点关闭的门状态」又被
            #   「没有外点关闭的门状态」**包含** ⟹ 用带 ★★ 的那条
                        mut_no_mousedown, "★★ 独立重算", D, st, a),
        neg_case_static(
            "把 `setContextMenu(null)` 改成**一跳间接**（`queueMicrotask`）",
            "★★ 「**直接**出现」这条判据是 R146b 的修复 ⟹ "
            "「那个 `close` 里**直接**写」必须红（间接调用不算外点关闭）",
            mut_one_hop, "直接", D, st, a),
        neg_case_static(
            "把模型库触发器的 `type=\"button\"` 改成 `type=\"submit\"`",
            "★ 「键盘 `Enter` 只产生 `click`、不产生 `mousedown`」"
            "这条的静态前提之一 ⟹ 对照要能抓",
            mut_trigger_type, "只产生", D, st, a),
        neg_case_static(
            "把模型库触发器的 `onClick` 去掉",
            "★ 同上：没有 `onClick` 就没有「点一下就开」这条路 ⟹ "
            "「键盘激活可达」的前提不成立",
            mut_no_onclick, "用 `onClick`", D, st, a),
        neg_case("把 keyboard 臂读成「右键菜单被关掉了」（不共活）",
                 "★★★ 本批唯一的缺陷 D1i **完全依赖**这一格 ⟹ "
                 "对照要能证明它红",
                 mut_kb_not_colive, "共活在键盘下可达", D, st, a),
        neg_case("把 keyboard 臂第 1 次读成「右键菜单被关掉了」",
                 "★★★ 「一次 Escape 只关 `sIP` 那个」这条要能抓",
                 mut_press1_closes_ctx, "留在原地", D, st, a),
        neg_case("把 libOnly 第 1 次读成「导出面板被关掉了」",
                 "★ 「`sIP` 单独活着时也要按两次」这条要能抓",
                 mut_libonly_closes_export, "单独活着", D, st, a),
        neg_case("把 raw 里那个错的 `coLive` 字段**改成对的**",
                 "★ R149：「raw 里的派生字段要与它自己的输入对账」⟹ "
                 "如果探针某天修好了，这条判据必须能红（否则就再也发现不了"
                 "它曾经错过）",
                 mut_fix_rawfield, "漏了", D, st, a),
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
    if LEDGER.exists() and "| Batch 784 |" not in LEDGER.read_text(
            encoding="utf-8"):
        problems.append("台账没有 `| Batch 784 |` 行")
    if LEDGER.exists():
        for ln in LEDGER.read_text(encoding="utf-8").split("\n"):
            if ln.startswith("| Batch 784 |") and FFFD in ln:
                problems.append("台账的 Batch 784 行含 U+FFFD")
    for f in (README, AUDIT):
        if f.exists() and FFFD in f.read_text(encoding="utf-8"):
            problems.append("%s 含 U+FFFD" % f.name)

    rep = {
        "batch": 784,
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
