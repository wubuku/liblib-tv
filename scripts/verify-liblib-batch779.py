#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 779 验收器 —— **独立实现**，不 import 汇编器。

## 本批要防的错误方向

这一批的结论要用来**撤回一条挂着的拍板项的授权**（776 的「(a) 可以单独做」）。
判据有偏时，**偏的方向**决定错误的代价：

- 若把「第二道吞嘴（桌 `:487`）」漏掉 ⟹ 照 776 的 C776-1 单独做 (a) ⟹
  **对用户可见行为净为零**，而这条改动会被当成「已修 D1c」结案。
- 若把「第一道吞嘴（hook）」漏掉 ⟹ 会去改错的那一处 ⟹ 又一次「按设计写成新缺陷」。
- 若把「阶梯 `:553` 自己有一档 `activeGesture`」漏掉 ⟹ 会给出
  「改两处就能按一次关掉面板」这条**做不到**的承诺。
- 若把「判别器有鉴别力」漏掉 ⟹ 「`win=0`」可能是判别器整个坏了
  ⟹ 上面三条全部是空的。

所以这四条**各配一条阴性对照**；静态层再配**改源码**的对照（本批静态层
在 778 里连踩五次「找到错的」，第四次就出在这一层）。

## 沿用 775–778 的纪律

- 静态层**独立实现**（注释抹白不删 R107；搜索带作用域 R110/R117/R128）
- 阴性对照的 `mutatedAnything` **实测**（比对派生指纹，R108）
- 阴性对照的 `kw` **取自判据标签字面量且唯一**（R118）
- `derive()` 对缺格健壮（缺格变红，不崩）
- 承重读数必须**与监听器相对次序无关**（R132）
"""
import copy
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch779-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAWDIR = OUTDIR / "raw"
PROBEDIR = OUTDIR / "probes"
README = OUTDIR / "README.md"
LEDGER = ROOT / "docs/research/VERIFICATION_LEDGER.md"

RAW_FILES = ["vb779a.json"]
PROBE_FILES = ["dbg779a.py", "mk779audit.py", "add_ledger_row.py"]
FFFD = "�"
META = {"tries", "retried"}
ESC_ARMS = ["gestureNumber", "gestureRange"]
CONTROL_ARM = "controlNonInput"
MOD_ARM = "modifierNonEscape"
ARMS = ESC_ARMS + [CONTROL_ARM, MOD_ARM]
PRESSES = 3

DD = "src/components/director/DirectorDesk.tsx"
GB_SRC = "src/components/director/useDirectorGestureBoundary.ts"


# ───────────────── 静态层（独立实现） ─────────────────
def blank_comments(s):
    """注释抹白而不删（行号不漂移）。★ 只抹注释，不抹字符串（R107）。"""
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


def lines_of(src):
    return blank_comments(src).split("\n")


def all_in(lines, pat):
    rx = re.compile(pat)
    return [n for n, ln in enumerate(lines, 1) if rx.search(ln)]


def first_in(lines, pat, after=0):
    """★ 收的必须是**行列表**（不是整串，否则逐字符匹配恒假 —— R128①）。"""
    return next((n for n in all_in(lines, pat) if n > after), None)


def last_in(lines, pat):
    """★ 取**末次**出现：同名形状常在别处也有一份（R128②）。"""
    return max(all_in(lines, pat), default=None)


def static_side(sources=None):
    sources = sources or {}

    def load(rel):
        if rel in sources:
            return lines_of(sources[rel])
        p = ROOT / rel
        return lines_of(p.read_text(encoding="utf-8")) if p.exists() else None

    dl, gb = load(DD), load(GB_SRC)
    if dl is None or gb is None:
        return {"err": "缺源码"}
    st = {}
    # ── hook 的 onKeyDown ──
    kds = last_in(gb, r"onKeyDown: \(event\) => \{")
    if kds:
        depth = 0
        kend = kds
        for n in range(kds, len(gb) + 1):
            depth += gb[n - 1].count("{") - gb[n - 1].count("}")
            if depth <= 0 and n > kds:
                kend = n
                break
    else:
        kend = None
    kd = "\n".join(gb[(kds or 1) - 1:(kend or 1) - 1]) if kds else ""
    st["hookOnKeyDownLine"] = kds
    st["hookStopTotal"] = kd.count("stopPropagation")
    st["hookPreventTotal"] = kd.count("preventDefault")
    lines = kd.split("\n")
    ei = first_in(lines, r'event\.key === "Escape"')
    # Escape 分支 = 从 `event.key === "Escape"` 到它下面的第一个 `return;`
    er = first_in(lines, r"^\s*return;\s*$", after=ei or 0) if ei else None
    esc = "\n".join(lines[(ei or 1) - 1:(er or 1) - 1]) if ei and er else ""
    rest = "\n".join(lines[(er or 1):]) if er else ""
    st["hookEscapeStop"] = "stopPropagation" in esc
    st["hookEscapePrevent"] = "preventDefault" in esc
    st["hookNonEscapeStop"] = rest.count("stopPropagation")
    # ── 桌的监听挂载 ──
    st["deskWinRegs"] = all_in(dl, r'window\.addEventListener\("keydown"')
    st["deskCaptureRegs"] = all_in(
        dl, r'addEventListener\("keydown"[^)]*capture:\s*true')
    # ── 守卫 / 阶梯 ──
    guard = first_in(dl, r"if \(isEditable\) return;")
    gate = first_in(dl, r'if \(event\.key !== "Escape"\) return;')
    st["guardLine"], st["ladderGate"] = guard, gate
    st["guardBeforeLadder"] = bool(guard and gate and guard < gate)
    st["ladderPrevent"] = first_in(dl, r"^      event\.preventDefault\(\);",
                                   after=gate or 0)
    rung = {
        "gesture": first_in(dl, r"history\.activeGesture\) \{", after=gate or 0),
        "export": first_in(dl, r"if \(exportPanelOpen\) \{", after=gate or 0),
        "follow": first_in(dl, r"if \(followTargetId\) \{", after=gate or 0),
        "close": first_in(dl, r"^      closeWorkspace\(\);", after=gate or 0),
    }
    st["ladderRungs"] = rung
    order = [rung["gesture"], rung["export"], rung["follow"], rung["close"]]
    st["ladderOrder"] = order
    st["ladderOrdered"] = bool(all(order) and order == sorted(order))
    md = first_in(dl, r'event\.key === "Escape" && activeMobilePanel')
    st["mobileDrawerLine"] = md
    st["mobileDrawerBeforeGuard"] = bool(md and guard and md < guard)
    return st


# ───────────────── 原始读数（重算） ─────────────────
def load_raw():
    for f in RAW_FILES:
        if not (RAWDIR / f).exists():
            raise SystemExit("缺原始读数 %s —— 判失败，不许通过" % f)
    for f in PROBE_FILES:
        if not (PROBEDIR / f).exists():
            raise SystemExit("缺探针脚本 %s —— 判失败，不许通过" % f)
    raw = json.loads((RAWDIR / "vb779a.json").read_text(encoding="utf-8"))
    if len(raw.get("rounds") or []) != 2:
        raise SystemExit("轮数不是 2")
    return raw


GESTURE_RX = re.compile(r"director-gesture-\d+-(\d+)")


def norm(x):
    if isinstance(x, dict):
        return {k: norm(v) for k, v in x.items()}
    if isinstance(x, list):
        return [norm(v) for v in x]
    if isinstance(x, str):
        return GESTURE_RX.sub(r"director-gesture-<TS>-\1", x)
    return x


def strip(x):
    if isinstance(x, dict):
        return {k: v for k, v in x.items() if k not in META}
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
            arms.setdefault(r.get("arm"), []).append(norm(r))
    D["arms"] = {k: v[0] for k, v in arms.items()}
    D["all"] = arms
    for k, v in arms.items():
        if v[0].get("FAILED"):
            D["unexpectedFailed"].append("%s: %s" % (k, v[0]["FAILED"]))
    D["keys"] = sorted(arms)
    D["roundsConsistent"] = (
        [reading(x) for x in norm(strip(raw["rounds"][0].get("rows")))]
        == [reading(x) for x in norm(strip(raw["rounds"][1].get("rows")))])
    D["pressTotal"] = sum(len((v[0].get("presses") or []))
                          for v in arms.values())
    return D


def _a(D, arm):
    return D["arms"].get(arm) or {}


def _presses(D, arm):
    return [p for p in (_a(D, arm).get("presses") or []) if p]


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

    # ── 静态 ──
    add("静态：缺源码", st.get("err") is None, True)
    add("静态：hook 的 `onKeyDown` 找得到", _ok(st.get("hookOnKeyDownLine")))
    add("静态：★ hook 的 Escape 分支 `preventDefault`（第一道吞嘴之一）",
        _ok(st.get("hookEscapePrevent")))
    add("静态：★ hook 的 Escape 分支 `stopPropagation`（第一道吞嘴之二）",
        _ok(st.get("hookEscapeStop")))
    add("静态：★ 整个 `onKeyDown` 里 `stopPropagation` **恰好 1 次**",
        st.get("hookStopTotal"), 1)
    add("静态：★ `stopPropagation` **不在**非 Escape 分支里 ⟹ 非 Escape 键"
        "**一定**能穿过 hook 到达 window", st.get("hookNonEscapeStop"), 0)
    add("静态：桌的 keydown 监听挂在 window", _ok(st.get("deskWinRegs")))
    add("静态：★ 桌的监听**不在 capture 相位** ⟹ 判别器成立"
        "（capture 版任何 `stopPropagation` 都拦不住）",
        len(st.get("deskCaptureRegs") or []) == 0, True)
    add("静态：`isEditable` 守卫找得到", _ok(st.get("guardLine")))
    add("静态：Escape 阶梯闸门找得到", _ok(st.get("ladderGate")))
    add("静态：★ 守卫排在阶梯闸门**之前** ⟹ 第二道吞嘴在第一道**下游**",
        _ok(st.get("guardBeforeLadder")))
    add("静态：阶梯闸门之后有 `preventDefault`", _ok(st.get("ladderPrevent")))
    add("静态：★ 阶梯**自己有一档 `activeGesture`** ⟹ 前两处都改完，"
        "第 1 次按压仍只取消手势", _ok((st.get("ladderRungs") or {}).get("gesture")))
    add("静态：阶梯四档齐全", all((st.get("ladderRungs") or {}).values()))
    add("静态：★ 阶梯档位有序（手势→导出面板→退出跟随→关桌）",
        _ok(st.get("ladderOrdered")))
    add("静态：★ 移动抽屉的 Escape 分支排在守卫**之前**（C775-2 同仓先例）",
        _ok(st.get("mobileDrawerBeforeGuard")))

    # ── 原始读数：自证「按键真的送达了」──
    add("原始：零 FAILED", D["unexpectedFailed"] == [], True)
    add("原始：臂集合齐（%d 臂）" % len(ARMS), D["keys"], sorted(ARMS))
    add("原始：两轮逐字段一致", _ok(D.get("roundsConsistent")))
    add("原始：按压格数 = %d 臂 × %d 次" % (len(ARMS), PRESSES),
        D.get("pressTotal"), len(ARMS) * PRESSES)
    for arm in ARMS:
        c = _a(D, arm)
        add("原始：%s 聚焦落上了" % arm, (c.get("focus") or {}).get("ok") is True)
        add("原始：★ %s 每一次按压 `cap>=1` ⟹ 按键**真的送达了浏览器**，"
            "所以「没到达 window」这个读数有鉴别力" % arm,
            all((p.get("read") or {}).get("cap", 0) >= 1
                for p in _presses(D, arm)) and bool(_presses(D, arm)))
        add("原始：%s 导出面板在起点是开的 ⟹ 阶梯的 :557 那档有目标" % arm,
            (c.get("stateOnFocus") or {}).get("exportPanel") is True)

    # ── 预测 A：第一道吞嘴 ──
    nFirst = 0
    for arm in ESC_ARMS:
        for p in _presses(D, arm):
            rd = p.get("read") or {}
            if (rd.get("win") or 0) == 0:
                nFirst += 1
            add("逐次：%s 第%s次 `win=0` ⟹ 事件**从没到达 window**"
                % (arm, p.get("n")), (rd.get("win") or 0) == 0)
    add("★ 第一道吞嘴覆盖 %d/%d 次按压 ⟹ **776 的机制归属正确**"
        "（第 2/3 次确实被 hook 的 stopPropagation 吞）" % (
            nFirst, len(ESC_ARMS) * PRESSES),
        nFirst == len(ESC_ARMS) * PRESSES)

    # ── 预测 B：对照臂（鉴别力）──
    cp = _presses(D, CONTROL_ARM)
    for p in cp:
        add("对照：第%s次 `win>=1` ⟹ 事件到达了 window（判别器有鉴别力）"
            % p.get("n"), ((p.get("read") or {}).get("win") or 0) >= 1)
    add("对照：★ 第 1 次按压后导出面板**关掉了**（阶梯 :557 跑到）",
        (cp[0].get("state") or {}).get("exportPanel") is False if cp else False)
    add("对照：★ 第 2 次按压后桌**关掉了**（阶梯 :568 跑到）",
        (cp[1].get("state") or {}).get("deskOpen") is False if len(cp) > 1
        else False)
    add("★ 判别器有鉴别力：对照臂 %d/%d 次到达 window 且阶梯跑完 ⟹ "
        "gesture 臂的 `win=0` 不是判别器坏了" % (
            sum(1 for p in cp if ((p.get("read") or {}).get("win") or 0) >= 1),
            len(cp)),
        sum(1 for p in cp if ((p.get("read") or {}).get("win") or 0) >= 1)
        == len(cp))

    # ── 预测 C：第二道吞嘴（★ 本批载荷）──
    mp = _presses(D, MOD_ARM)
    for p in mp:
        rd, s = p.get("read") or {}, p.get("state") or {}
        add("逐次：Meta+z 第%s次 `win>=1` ⟹ 事件**穿过了 hook** 到达 window" % p.get("n"),
            (rd.get("win") or 0) >= 1)
        add("逐次：Meta+z 第%s次 `lastCommand` **不是** `UNDO`" % p.get("n"),
            s.get("lastCommand") != "UNDO")
    add("★ 第二道吞嘴：Meta+z %d/%d 次**到达了 window** 而 `lastCommand` 始终"
        "非 `UNDO` ⟹ **桌的 `:487` 守卫把它吞了**" % (
            sum(1 for p in mp if ((p.get("read") or {}).get("win") or 0) >= 1),
            len(mp)),
        bool(mp) and all(((p.get("read") or {}).get("win") or 0) >= 1
                         and (p.get("state") or {}).get("lastCommand") != "UNDO"
                         for p in mp))
    add("★ 承重的推论：修法 (a) 只动第一道 ⟹ 第 2 次按压从「被 hook 吞」变成"
        "「被 `:487` 吞」⟹ **对用户可见行为净为零** ⟹ **(a) 不能单独做**", True)

    # ── 产物自洽 ──
    add("产物：audit.batch=779", a.get("batch"), 779)
    add("产物：audit 的第一道吞嘴计数 = 重算值",
        (a.get("results") or {}).get("firstSwallowPresses"), nFirst)
    add("产物：audit 的阶梯档位 = 静态重算",
        (a.get("results") or {}).get("ladderRungs"),
        st.get("ladderRungs"))
    add("产物：audit 的守卫行号 = 静态重算",
        (a.get("static") or {}).get("guardLine"), st.get("guardLine"))
    add("产物：audit 的阶梯闸门行号 = 静态重算",
        (a.get("static") or {}).get("ladderGate"), st.get("ladderGate"))
    add("产物：audit 记的零 FAILED", (a.get("results") or {}).get("failedCells"), 0)
    return C


# ───────────────── 阴性对照 ─────────────────
def _fp(D):
    out = {}
    for arm, c in (D.get("arms") or {}).items():
        out[arm] = {
            "focus": (c.get("focus") or {}).get("ok"),
            "exportOnFocus": (c.get("stateOnFocus") or {}).get("exportPanel"),
            "gestureOnFocus": (c.get("stateOnFocus") or {}).get("gesture"),
            "presses": [{
                "cap": (p.get("read") or {}).get("cap"),
                "win": (p.get("read") or {}).get("win"),
                "winEntryCount": (p.get("read") or {}).get("winEntryCount"),
                "gesture": (p.get("state") or {}).get("gesture"),
                "lastCommand": (p.get("state") or {}).get("lastCommand"),
                "exportPanel": (p.get("state") or {}).get("exportPanel"),
                "deskOpen": (p.get("state") or {}).get("deskOpen"),
            } for p in (c.get("presses") or [])],
        }
    return out


def _fingerprint(D):
    return json.dumps(_fp(D), ensure_ascii=False, sort_keys=True, default=str)


def _flips(D, st, a, D2, st2, kw):
    C2 = run_checks(a, st2, D2)
    bp = {c["label"]: c["pass"] for c in run_checks(a, st, D)}
    flipped = [c["label"] for c in C2 if bp.get(c["label"], True)
               and not c["pass"]]
    hits = [f for f in flipped if kw in f]
    return flipped, hits, len(hits) == 1


def neg_case(name, why, mutate, kw, D, st, a):
    raw2 = mutate(copy.deepcopy(D.get("_raw")))
    if raw2 is None:
        return {"name": name, "why": why, "caught": False,
                "mutatedAnything": False, "kwMatchedCount": 0,
                "expectFailOn": kw}
    D2 = derive(raw2)
    flipped, hits, ok = _flips(D, st, a, D2, copy.deepcopy(st), kw)
    base = derive(copy.deepcopy(D.get("_raw")))
    return {"name": name, "why": why,
            "mutatedAnything": _fingerprint(D2) != _fingerprint(base),
            "kwMatchedCount": len(hits), "flipped": flipped, "caught": ok,
            "expectFailOn": kw}


def neg_case_static(name, why, mutate_src, kw, D, st, a):
    try:
        src2 = mutate_src()
    except Exception as e:  # noqa: BLE001
        return {"name": name, "why": why, "caught": False,
                "mutatedAnything": False, "kwMatchedCount": 0,
                "error": "%s: %s" % (type(e).__name__, e)}
    if src2 is None:
        return {"name": name, "why": why, "caught": False,
                "mutatedAnything": False, "kwMatchedCount": 0,
                "expectFailOn": kw}
    st2 = static_side(src2)
    flipped, hits, ok = _flips(D, st, a, derive(copy.deepcopy(D.get("_raw"))),
                               st2, kw)
    return {"name": name, "why": why,
            "mutatedAnything": json.dumps(st2, sort_keys=True, default=str)
            != json.dumps(st, sort_keys=True, default=str),
            "kwMatchedCount": len(hits), "flipped": flipped, "caught": ok,
            "expectFailOn": kw}


def _read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def negative_controls(D, st, a):
    out = []

    def make(arm, **patch):
        def f(raw):
            n = 0
            for rd in raw["rounds"]:
                for r in rd.get("rows") or []:
                    if r.get("arm") == arm and not r.get("FAILED"):
                        for p in r.get("presses") or []:
                            for k, v in patch.items():
                                if k == "read":
                                    p["read"] = dict(p.get("read") or {}, **v)
                                else:
                                    p["state"] = dict(p.get("state") or {}, **v)
                            n += 1
            return raw if n else None
        return f

    def let_escape_through(arm):
        return make(arm, read={"win": 1, "cap": 1})

    def undo_runs(arm):
        return make(arm, state={"lastCommand": "UNDO"})

    def kill_control(arm):
        return make(arm, read={"win": 0, "cap": 1})

    def control_stuck(arm):
        return make(arm, state={"exportPanel": True, "deskOpen": True})

    def nonexistent(raw):
        for rd in raw["rounds"]:
            for r in rd.get("rows") or []:
                if r.get("__永不匹配__") is None:
                    r["__永不匹配__"] = 1
                    return raw
        return raw

    def move_guard_after_gate():
        src = _read(DD)
        guard = "      if (isEditable) return;\n"
        gate = '      if (event.key !== "Escape") return;'
        if guard not in src or gate not in src:
            return None
        src = src.replace(guard, "")
        i = src.find(gate)
        j = src.find("\n", src.find("event.preventDefault();", i)) + 1
        return {DD: src[:j] + guard + src[j:]}

    def kill_hook_stop():
        src = _read(GB_SRC)
        line = "        event.stopPropagation();\n"
        if line not in src:
            return None
        return {GB_SRC: src.replace(line, "", 1)}

    def stop_non_escape_too():
        src = _read(GB_SRC)
        anchor = "        begin();\n"
        if anchor not in src:
            return None
        return {GB_SRC: src.replace(
            anchor, "        event.stopPropagation();\n" + anchor, 1)}

    # ★ 缩进必须与源码逐字一致（这里是 **6 空格**，不是 4）—— 对照块没对上时
    #   `mutatedAnything` 会是 false，结论直接为空（R108）。
    RUNG_BLOCK = ("      if (useDirectorStore.getState().history"
                  ".activeGesture) {\n"
                  "        cancelDirectorGesture();\n"
                  "        return;\n"
                  "      }\n")
    CLOSE_LINE = "      closeWorkspace();\n"

    def kill_ladder_gesture_rung():
        src = _read(DD)
        if RUNG_BLOCK not in src:
            return None
        return {DD: src.replace(RUNG_BLOCK, "", 1)}

    def put_gesture_rung_last():
        src = _read(DD)
        if RUNG_BLOCK not in src or CLOSE_LINE not in src:
            return None
        src = src.replace(RUNG_BLOCK, "", 1)
        return {DD: src.replace(CLOSE_LINE, RUNG_BLOCK + CLOSE_LINE, 1)}

    out.append(neg_case(
        "让 gesture 臂的 Escape 到达 window ⟹ 「第一道吞嘴是 hook」必须红",
        "★ 漏判方向 = 会去改错的那一处（桌守卫），而真正该改的 hook 没人动",
        let_escape_through("gestureNumber"),
        "第一道吞嘴覆盖", D, st, a))
    out.append(neg_case(
        "★ 对称：让 gestureRange 臂的 Escape 到达 window ⟹ 同一条必须红",
        "★ 没有这条，range 族的读数可以单独坏掉而不被发现",
        let_escape_through("gestureRange"),
        "第一道吞嘴覆盖", D, st, a))
    out.append(neg_case(
        "让 Meta+z 臂的 undo 真的执行 ⟹ 「第二道吞嘴」必须红",
        "★ 漏判方向 = 照 776 的 C776-1 单独做 (a) ⟹ 净效果为零，"
        "而这条改动会被当成「已修 D1c」结案",
        undo_runs("modifierNonEscape"),
        "第二道吞嘴：Meta+z", D, st, a))
    out.append(neg_case(
        "让对照臂的 Escape 也到不了 window ⟹ 「判别器有鉴别力」必须红",
        "★ 漏判方向 = 「win=0」是判别器坏了，本批三条结论全部是空的",
        kill_control("controlNonInput"),
        "判别器有鉴别力：对照臂", D, st, a))
    out.append(neg_case(
        "让对照臂的阶梯不跑（面板与桌都不关）⟹ 「阶梯跑完」那两条必须红",
        "证明阶梯那两个读数测的是**具体档位**而不是「win>=1」",
        control_stuck("controlNonInput"),
        "阶梯 :557 跑到", D, st, a))
    out.append(neg_case(
        "★ 对照自己没改成：写一个 raw 里不存在的字段 ⟹ 不许有判据翻红",
        "mutatedAnything 为 false 时这条对照的结论是空的（R108）",
        nonexistent, "__永不匹配__", D, st, a))

    out.append(neg_case_static(
        "★ 静态：把守卫挪到阶梯闸门**之后** ⟹ 「第二道在第一道下游」必须红",
        "证明那条排序判据真的在测顺序",
        move_guard_after_gate, "守卫排在阶梯闸门**之前**", D, st, a))
    out.append(neg_case_static(
        "★ 静态：删掉 hook Escape 分支的 `stopPropagation` ⟹ 「第一道吞嘴」必须红",
        "证明第一道不是「凭空断言的」",
        kill_hook_stop, "`stopPropagation`（第一道吞嘴之二）", D, st, a))
    out.append(neg_case_static(
        "★ 静态：给非 Escape 分支也加 `stopPropagation` ⟹ "
        "「非 Escape 键能到达 window」必须红",
        "★ 这条是第二道吞嘴测量的**前提** —— 若 hook 拦了非 Escape 键，"
        "「事件到达 window 而 undo 不发生」就不能归因于 `:487`",
        stop_non_escape_too, "**不在**非 Escape 分支里", D, st, a))
    out.append(neg_case_static(
        "★ 静态：删掉阶梯自己的 `activeGesture` 档 ⟹ 「阶梯自己有一档」必须红",
        "★ 漏判方向 = 会给出「改两处就能按一次关掉面板」这条**做不到**的承诺",
        kill_ladder_gesture_rung, "阶梯**自己有一档 `activeGesture`**", D, st, a))
    out.append(neg_case_static(
        "★ 静态：把 `activeGesture` 档挪到最后 ⟹ 「阶梯档位有序」必须红",
        "证明顺序判据真的在测顺序（775 的 C775-2 依赖这个顺序）",
        put_gesture_rung_last, "阶梯档位有序", D, st, a))
    return out


# ───────────────── 台账 / README ─────────────────
def artifact_checks():
    C = []
    if not LEDGER.exists():
        return [{"label": "台账在位", "pass": False, "got": "缺"}]
    txt = LEDGER.read_text(encoding="utf-8")
    mine = [ln for ln in txt.split("\n")
            if re.match(r"^\|\s*Batch\s+779\s*\|", ln)]
    C.append({"label": "台账：Batch 779 恰有一行", "pass": len(mine) == 1,
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
    else:
        C.append({"label": "README 在位", "pass": False, "got": "缺"})
    return C


def main():
    if not AUDIT.exists():
        print("缺少 runtime-audit.json（先跑 mk779audit.py）")
        return 1
    a = json.loads(AUDIT.read_text(encoding="utf-8"))
    st = static_side()
    try:
        raw = load_raw()
        rawErr = None
    except Exception as e:  # noqa: BLE001
        raw, rawErr = None, str(e)
    if rawErr:
        checks = [{"label": "原始读数可用（raw + 三个 probes/）", "pass": False,
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
        {"batch": 779, "checks": checks, "pass": npass, "total": total,
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
            print("  ✗ %s 命中 %s 条（期望恰好 1）  翻红=%r"
                  % (n["name"], n.get("kwMatchedCount"),
                     (n.get("flipped") or [])[:6]))
        elif not n["caught"]:
            print("  ✗ 漏放：%s" % n["name"])
    print("batch 779 %s" % ("通过" if ok else "不通过"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
