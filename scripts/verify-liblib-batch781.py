#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 781 验收器 —— **独立实现**，不 import 汇编器。

## 本批要防的错误方向

这一批要**补掉一个判据里唯一的空洞**，并**下一条「放行安不安全」的安全结论**。
两边的偏都有代价：

- 若把「`Meta+c`/`Meta+v` 在 gesture 臂上**不发**」漏掉 ⟹ 矩阵最后一行
  仍是**凭判据推出来的、没有读数** ⟹ 而 780 已经按它推过一轮。
- 若把「director 面**从不**碰 `navigator.clipboard`」漏掉 ⟹ 会得出
  「放行 `Cmd+C` 会污染系统剪贴板」的**完全相反**结论 ⟹ **一个正确的修法
  被否掉**。这个搜索**必须带作用域**：`app/frameos/` 与 `components/jimeng/`
  里都有 `navigator.clipboard`（R110/R128）。
- 若把「占位文案『无命令反馈』」漏掉 ⟹ 会把「死键 + 面板在骗人」误报成
  「静默的死键」⟹ 而 777 的 D1e 正是**占位文案**那条。

所以这三条各配一条阴性对照；静态层配**改源码**的对照。

## 沿用 775–780 的纪律

- 静态层**独立实现**（R107 / R110 / R128）
- 阴性对照的 `mutatedAnything` **实测**（R108）、`kw` **唯一**（R118）
- **聚合判据数「条件成立的次数」，不是「总数」**（780 自己的教训）
- `derive()` 对缺格健壮
"""
import copy
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch781-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAWDIR = OUTDIR / "raw"
PROBEDIR = OUTDIR / "probes"
README = OUTDIR / "README.md"
LEDGER = ROOT / "docs/research/VERIFICATION_LEDGER.md"
RAW776 = ROOT / "docs/research/liblib-canvas-batch776-2026-10-01/raw/vb776a.json"
AUDIT780 = ROOT / "docs/research/liblib-canvas-batch780-2026-10-01/runtime-audit.json"

RAW_FILES = ["vb781a.json"]
PROBE_FILES = ["dbg781a.py", "mk781audit.py", "add_ledger_row.py"]
FFFD = "�"
META = {"tries", "retried"}
COPY_CMD = "COPY_SELECTION"
PASTE_CMD = "PASTE_CLIPBOARD"
PLACEHOLDER = "无命令反馈"
STALE_CMD = "GESTURE_BEGIN"
STALE_DISP = "COMMITTED"
GESTURE_ARMS = ["numberCopy", "numberPaste", "rangeCopy", "rangePaste"]
CONTROL_ARMS = ["controlCopy", "controlPaste"]
ARMS = GESTURE_ARMS + CONTROL_ARMS
PRESSES = 2
DD = "src/components/director/DirectorDesk.tsx"
STORE = "src/store/directorStore.ts"
FB_LIB = "src/lib/directorCommandFeedback.ts"
#: ★ 「director 面」的**确切范围** —— 搜索必须限定在这里（R110/R128）
DIRECTOR_GLOBS = ["src/store/directorStore.ts", "src/components/director"]


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
    """★ 收的必须是**行列表**（R128①）。"""
    return next((n for n in all_in(lines, pat) if n > after), None)


def static_side(sources=None, extra_files=None):
    """`sources` 传改过的源码文本；`extra_files` 追加**假文件**（给
    「director 面出现 navigator.clipboard」那条对照用）。"""
    sources = sources or {}
    st = {}
    if extra_files:
        hits = []
        for rel, txt in extra_files.items():
            for n, ln in enumerate(lines_of(txt), 1):
                if re.search(r"navigator\.clipboard|clipboard\.writeText|"
                             r"clipboard\.readText", ln):
                    hits.append("%s:%d" % (rel, n))
        st["systemClipboardHits"] = hits
        st["directorFilesScanned"] = -1   # 标记：本次只扫了注入的文件
        return st

    def load(rel):
        if rel in sources:
            return lines_of(sources[rel])
        p = ROOT / rel
        return lines_of(p.read_text(encoding="utf-8")) if p.exists() else None

    dl = load(DD)
    store = load(STORE)
    if dl is None or store is None:
        return {"err": "缺源码"}
    # ★ `in` 在**行列表**上比对的是「某个元素恰好等于该串」⟹ 恒假
    #   （R128 的又一变体：拿对了容器、拿错了类型）。
    storeText = "\n".join(store)
    guard = first_in(dl, r"if \(isEditable\) return;")
    cpy = first_in(dl, r'key\.toLowerCase\(\) === "c"')
    pst = first_in(dl, r'key\.toLowerCase\(\) === "v"')
    cpyCall = first_in(dl, r"copyDirectorSelection\(\);", after=cpy or 0)
    pstCall = first_in(dl, r"pasteDirectorClipboard\(\);", after=pst or 0)
    st["guardLine"], st["copyLine"], st["pasteLine"] = guard, cpy, pst
    st["copyCallLine"], st["pasteCallLine"] = cpyCall, pstCall
    st["copyAfterGuard"] = bool(guard and cpy and guard < cpy)
    st["pasteAfterGuard"] = bool(guard and pst and guard < pst)
    st["internalClipboardWrite"] = "clipboard: built.packet" in storeText
    st["internalClipboardType"] = "DirectorClipboardPacketV1" in storeText
    pstGuard = first_in(store, r"if \(!state\.clipboard\) \{",
                        after=first_in(store,
                                       r"pasteDirectorClipboard: \(\) =>"))
    st["pasteEmptyGuard"] = bool(pstGuard)
    # ★ FB_LIB 也要走 `load()` —— 否则「改源码」的阴性对照传进来的
    #   `sources[FB_LIB]` 会被**忽略**，对照自己就变成惰性的（R108）。
    fb = load(FB_LIB)
    st["committedReturnsNull"] = bool(
        fb is not None
        and 'disposition === "COMMITTED") return null' in "\n".join(fb))
    # ★ 带作用域地扫 director 面（R110/R128）
    files = []
    for g in DIRECTOR_GLOBS:
        p = ROOT / g
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            files.extend(sorted(p.rglob("*.ts")) + sorted(p.rglob("*.tsx")))
    hits = []
    for p in files:
        for n, ln in enumerate(lines_of(p.read_text(encoding="utf-8")), 1):
            if re.search(r"navigator\.clipboard|clipboard\.writeText|"
                         r"clipboard\.readText", ln):
                hits.append("%s:%d" % (p.relative_to(ROOT), n))
    st["directorFilesScanned"] = len(files)
    st["systemClipboardHits"] = hits
    return st


# ───────────────── 原始读数（重算） ─────────────────
def load_raw():
    for f in RAW_FILES:
        if not (RAWDIR / f).exists():
            raise SystemExit("缺原始读数 %s —— 判失败，不许通过" % f)
    for f in PROBE_FILES:
        if not (PROBEDIR / f).exists():
            raise SystemExit("缺探针脚本 %s —— 判失败，不许通过" % f)
    raw = json.loads((RAWDIR / "vb781a.json").read_text(encoding="utf-8"))
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
    for k, v in arms.items():
        if v[0].get("FAILED"):
            D["unexpectedFailed"].append("%s: %s" % (k, v[0]["FAILED"]))
    D["keys"] = sorted(arms)
    D["roundsConsistent"] = (
        [reading(x) for x in norm(strip(raw["rounds"][0].get("rows")))]
        == [reading(x) for x in norm(strip(raw["rounds"][1].get("rows")))])
    D["pressTotal"] = sum(len((v[0].get("presses") or [])) for v in arms.values())
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
    add("静态：`isEditable` 守卫找得到", _ok(st.get("guardLine")))
    add("静态：★ `Cmd+C` 分支排在守卫**之后**", _ok(st.get("copyAfterGuard")))
    add("静态：★ `Cmd+V` 分支排在守卫**之后**",
        _ok(st.get("pasteAfterGuard")))
    add("静态：★ 扫了 director 面 %d 个文件" % (st.get("directorFilesScanned")
                                       or 0),
        (st.get("directorFilesScanned") or 0) > 0)
    add("静态：★ director 面**零** `navigator.clipboard` / `writeText` / "
        "`readText` 命中 ⟹ **放行不会碰系统剪贴板**（这一条是矩阵能不能"
        "覆盖 C/V 的前提）", st.get("systemClipboardHits"), [])
    add("静态：`copyDirectorSelection` 写的是**内部** clipboard 包",
        _ok(st.get("internalClipboardWrite")))
    add("静态：内部包类型是 `DirectorClipboardPacketV1`",
        _ok(st.get("internalClipboardType")))
    add("静态：★ store 里有 `if (!state.clipboard)` 那道拒绝"
        "（这是「Paste 给真实消息」的机制）", _ok(st.get("pasteEmptyGuard")))
    add("静态：★ `getDirectorCommandFeedback` 对 `COMMITTED` 返回 null"
        "⟹ Copy 成功时面板只能显示占位文案",
        _ok(st.get("committedReturnsNull")))

    # ── 原始读数：自证起点与送达 ──
    add("原始：零 FAILED", D["unexpectedFailed"] == [], True)
    add("原始：臂集合齐（%d 臂）" % len(ARMS), D["keys"], sorted(ARMS))
    add("原始：两轮逐字段一致", _ok(D.get("roundsConsistent")))
    add("原始：按压格数 = %d 臂 × %d 次" % (len(ARMS), PRESSES),
        D.get("pressTotal"), len(ARMS) * PRESSES)
    for arm in ARMS:
        c = _a(D, arm)
        add("原始：%s 聚焦落上了" % arm, (c.get("focus") or {}).get("ok") is True)
        add("原始：%s 桌在" % arm,
            (c.get("stateBefore") or {}).get("deskOpen") is True)
        add("原始：★ %s 每一次按压 `cap>=1` ⟹ 按键**真的送达了浏览器**"
            % arm, bool(_presses(D, arm))
            and all((p["read"].get("cap") or 0) >= 1
                    for p in _presses(D, arm)))

    # ── 预测 A：gesture 臂不发 ──
    for arm in GESTURE_ARMS:
        for p in _presses(D, arm):
            s = p.get("state") or {}
            live = s.get("liveTexts") or []
            add("逐次：%s 第%s次 `win>=1` ⟹ 事件**到达了 window**"
                % (arm, p.get("n")), (p["read"].get("win") or 0) >= 1)
            add("逐次：%s 第%s次 `lastCommand` **既不是** `%s` **也不是** `%s`"
                % (arm, p.get("n"), COPY_CMD, PASTE_CMD),
                s.get("lastCommand") not in (COPY_CMD, PASTE_CMD))
            add("逐次：%s 第%s次 `lastCommand` 是**陈旧值** `%s`"
                "（没被这两下按键更新）" % (arm, p.get("n"), STALE_CMD),
                s.get("lastCommand"), STALE_CMD)
            add("逐次：%s 第%s次 `lastDisp` 也是**陈旧值** `%s`"
                % (arm, p.get("n"), STALE_DISP), s.get("lastDisp"), STALE_DISP)
            add("逐次：★ %s 第%s次 live 区**含占位文案**「%s」⟹ "
                "不是「静默」而是**面板在骗人**" % (arm, p.get("n"), PLACEHOLDER),
                PLACEHOLDER in live)
    nNo = sum(len(_presses(D, arm)) for arm in GESTURE_ARMS)
    nNoFire = sum(1 for arm in GESTURE_ARMS for p in _presses(D, arm)
                  if (p.get("state") or {}).get("lastCommand")
                  not in (COPY_CMD, PASTE_CMD))
    nPh = sum(1 for arm in GESTURE_ARMS for p in _presses(D, arm)
              if PLACEHOLDER in ((p.get("state") or {}).get("liveTexts") or []))
    add("★ 780 矩阵最后一行被测出来了：gesture 臂 %d/%d 次 `Meta+c`/`Meta+v` "
        "**不发** ⟹ 那一行不再是「凭判据推出来的」" % (nNoFire, nNo),
        nNoFire == nNo)
    add("★ 死键 **%d/%d** 次伴随**占位文案**「%s」⟹ 准确说法是"
        "「死键 + 面板在骗人」，不是「静默」" % (nPh, nNo, PLACEHOLDER),
        nPh == nNo)

    # ── 预测 B：对照臂真的发生 + 桌的反馈通道是通的 ──
    nCtrl = 0
    nCtrlOk = 0
    for arm in CONTROL_ARMS:
        want = COPY_CMD if arm == "controlCopy" else PASTE_CMD
        for p in _presses(D, arm):
            s = p.get("state") or {}
            nCtrl += 1
            if s.get("lastCommand") == want:
                nCtrlOk += 1
            add("对照：%s 第%s次 `lastCommand=%s` ⟹ 那个分支**真的跑了**"
                % (arm, p.get("n"), want), s.get("lastCommand"), want)
    add("★ 判别力成立：对照臂 %d/%d 次 C/V **真的发生** ⟹ "
        "「gesture 臂不发」不是「那个分支本来就不跑」" % (nCtrlOk, nCtrl),
        nCtrlOk == nCtrl and nCtrl > 0)
    # ★ Paste 必须是**非 COMMITTED** 且 live 区给**真实消息**（不含占位）
    pasteLive = sorted({t for p in _presses(D, "controlPaste")
                        for t in ((p.get("state") or {}).get("liveTexts") or [])})
    pasteDisp = {(p.get("state") or {}).get("lastDisp")
                 for p in _presses(D, "controlPaste")}
    add("★ 对照臂 `Meta+v` 的 disposition **非 `COMMITTED`**（实际 %r）"
        % sorted(x for x in pasteDisp if x), all(
            x and x != "COMMITTED" for x in pasteDisp) and bool(pasteDisp))
    add("★ 对照臂 `Meta+v` 的 live 区给**真实消息**（%r）而**不含**占位文案"
        " ⟹ 桌**有**「无操作/拒绝」的反馈通道" % pasteLive,
        bool(pasteLive) and all(t != PLACEHOLDER for t in pasteLive))
    add("★ 差异不在「有没有反馈通道」，在「**命令有没有产生**」",
        bool(pasteLive) and nNoFire == nNo)

    # ── 跨批对账 ──
    if RAW776.exists() and AUDIT780.exists():
        c776 = json.loads(RAW776.read_text(
            encoding="utf-8"))["rounds"][0]["census"]
        best = {}
        for x in c776:
            if not x.get("selfJustified"):
                continue
            if x.get("id") not in best or (x.get("live") or 0) > (
                    best[x["id"]].get("live") or 0):
                best[x["id"]] = x
        add("族规模：776 普查每族都非空（逐族自证）",
            all((x.get("live") or 0) > 0 for x in best.values()))
        fam = {}
        for x in best.values():
            fam[x.get("wantType")] = fam.get(x.get("wantType"), 0) + (
                x.get("live") or 0)
        a780 = json.loads(AUDIT780.read_text(encoding="utf-8"))
        c780 = (a780.get("matrix") or {}).get("counts") or {}
        add("族规模：从 776 raw 重算 = 与 780 产物**一致**",
            [fam.get("number"), fam.get("range")],
            [c780.get("number"), c780.get("range")])
        add("族规模：两族合计 53", fam.get("number", 0) + fam.get("range", 0), 53)
        # ★ 780 那一行**必须**还标着「未测」⟹ 本批的前提成立
        rows780 = {r["key"]: r for r in
                   (a780.get("matrix") or {}).get("rows") or []}
        cv = rows780.get("Meta+c / Meta+v")
        add("★ 780 产物里 `Meta+c`/`Meta+v` 那一行**标着「未测」**"
            "⟹ 本批「补最后一行」的前提成立", bool(cv) and "未测" in (
                cv.get("number") or ""))
        # ★ 本批的矩阵**不能**再留 notMeasured
        add("★ 本批产物 `notMeasured` 为空（五个键全部有读数）",
            (a.get("matrix") or {}).get("notMeasured"), [])
        rows = {r["key"]: r for r in (a.get("matrix") or {}).get("rows") or []}
        add("矩阵：五行都在（Escape / Meta+z / Delete·Backspace / Meta+c·Meta+v）"
            " —— 第五行是新增的「反馈与内部剪贴板」",
            all(k in rows for k in ("Escape", "Meta+z", "Delete / Backspace",
                                    "Meta+c / Meta+v")), True)
    else:
        add("跨批产物在位（776 raw / 780 audit）", False)

    # ── 产物自洽 ──
    add("产物：audit.batch=781", a.get("batch"), 781)
    add("产物：audit 的「不发」计数 = 重算值",
        (a.get("results") or {}).get("noFirePresses"), nNoFire)
    add("产物：audit 的「占位文案」计数 = 重算值",
        (a.get("results") or {}).get("placeholderPresses"), nPh)
    add("产物：audit 记的系统剪贴板命中数 = 静态重算",
        (a.get("results") or {}).get("systemClipboardHits"),
        len(st.get("systemClipboardHits") or []))
    add("产物：audit 的守卫行号 = 静态重算",
        (a.get("static") or {}).get("guardLine"), st.get("guardLine"))
    add("产物：audit 记的零 FAILED", (a.get("results") or {}).get("failedCells"), 0)
    return C


# ───────────────── 阴性对照 ─────────────────
def _fp(D):
    out = {}
    for arm, c in (D.get("arms") or {}).items():
        out[arm] = {
            "focus": (c.get("focus") or {}).get("ok"),
            "deskOpen": (c.get("stateBefore") or {}).get("deskOpen"),
            "presses": [{
                "cap": (p.get("read") or {}).get("cap"),
                "win": (p.get("read") or {}).get("win"),
                "lastCommand": (p.get("state") or {}).get("lastCommand"),
                "lastDisp": (p.get("state") or {}).get("lastDisp"),
                "live": (p.get("state") or {}).get("liveTexts"),
            } for p in (c.get("presses") or [])],
        }
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
    C2 = run_checks(a, copy.deepcopy(st), D2)
    bp = {c["label"]: c["pass"] for c in run_checks(a, copy.deepcopy(st), D)}
    flipped = [c["label"] for c in C2 if bp.get(c["label"], True)
               and not c["pass"]]
    hits = [f for f in flipped if kw in f]
    base = derive(copy.deepcopy(D.get("_raw")))
    return {"name": name, "why": why,
            "mutatedAnything": _fingerprint(D2) != _fingerprint(base),
            "kwMatchedCount": len(hits), "flipped": flipped,
            "caught": len(hits) == 1, "expectFailOn": kw}


def neg_case_extra_file(name, why, files, kw, D, st, a):
    """注入一个**假文件**进 director 面 ⟹ 「零命中」那条必须红。
    ★ 这是唯一能验「带作用域的搜索」真的在看的办法：只改真源码里的
    某个字符串，命中位置会变但**命中数仍是 0**。"""
    st2 = static_side(extra_files=files)
    C2 = run_checks(a, st2, derive(copy.deepcopy(D.get("_raw"))))
    bp = {c["label"]: c["pass"] for c in run_checks(a, copy.deepcopy(st), D)}
    flipped = [c["label"] for c in C2 if bp.get(c["label"], True)
               and not c["pass"]]
    hits = [f for f in flipped if kw in f]
    return {"name": name, "why": why,
            "mutatedAnything": _st_fp(st2) != _st_fp(st),
            "kwMatchedCount": len(hits), "flipped": flipped,
            "caught": len(hits) == 1, "expectFailOn": kw}


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
    C2 = run_checks(a, st2, derive(copy.deepcopy(D.get("_raw"))))
    bp = {c["label"]: c["pass"] for c in run_checks(a, copy.deepcopy(st), D)}
    flipped = [c["label"] for c in C2 if bp.get(c["label"], True)
               and not c["pass"]]
    hits = [f for f in flipped if kw in f]
    return {"name": name, "why": why,
            "mutatedAnything": _st_fp(st2) != _st_fp(st),
            "kwMatchedCount": len(hits), "flipped": flipped,
            "caught": len(hits) == 1, "expectFailOn": kw}


def _read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def negative_controls(D, st, a):
    out = []

    def make(arm, cmd=None, disp=None, live=None, win=None):
        def f(raw):
            n = 0
            for rd in raw["rounds"]:
                for r in rd.get("rows") or []:
                    if r.get("arm") == arm and not r.get("FAILED"):
                        for p in r.get("presses") or []:
                            if cmd is not None:
                                p["state"] = dict(p.get("state") or {},
                                                  lastCommand=cmd)
                            if disp is not None:
                                p["state"] = dict(p.get("state") or {},
                                                  lastDisp=disp)
                            if live is not None:
                                p["state"] = dict(p.get("state") or {},
                                                  liveTexts=live)
                            if win is not None:
                                p["read"] = dict(p.get("read") or {}, win=win)
                            n += 1
            return raw if n else None
        return f

    def nonexistent(raw):
        for rd in raw["rounds"]:
            for r in rd.get("rows") or []:
                if r.get("__永不匹配__") is None:
                    r["__永不匹配__"] = 1
                    return raw
        return raw

    def move_guard_after_cv():
        src = _read(DD)
        guard = "      if (isEditable) return;\n"
        if guard not in src:
            return None
        src = src.replace(guard, "")
        anchor = '      if (modifier && event.key.toLowerCase() === "v") {'
        i = src.find(anchor)
        if i < 0:
            return None
        j = src.find("\n", src.find("return;", src.find("pasteDirectorClipboard();", i))) + 1
        return {DD: src[:j] + guard + src[j:]}

    def drop_internal_clipboard_type():
        src = _read(STORE)
        if "DirectorClipboardPacketV1" not in src:
            return None
        return {STORE: src.replace("DirectorClipboardPacketV1",
                                   "DirectorClipboardPacketV9")}

    def committed_feedback_no_longer_null():
        fb = _read(FB_LIB)
        old = 'if (!result || result.disposition === "COMMITTED") return null;'
        if old not in fb:
            return None
        return {FB_LIB: fb.replace(
            old, 'if (!result) return null;')}

    out.append(neg_case(
        "让 gesture 臂的 `Meta+c` **真的执行** ⟹ 「最后一行被测出来了」必须红",
        "★ 漏判方向 = 矩阵最后一行**仍然是凭判据推出来的、没有读数**",
        make("numberCopy", cmd=COPY_CMD, disp="COMMITTED",
             live=["已复制 1 个对象"]),
        "最后一行被测出来了", D, st, a))
    out.append(neg_case(
        "★ 对称：让 rangePaste 臂**真的执行** ⟹ 同一条必须红",
        "★ 没有这条，number 与 range 两族的读数可以单独坏掉",
        make("rangePaste", cmd=PASTE_CMD, disp="NOOP",
             live=["当前没有可复制或粘贴的对象"]),
        "最后一行被测出来了", D, st, a))
    out.append(neg_case(
        "把 gesture 臂的 live 区改成**空** ⟹ 「面板在骗人」必须红",
        "★ 漏判方向 = 把「死键 + 占位文案」误报成「静默的死键」⟹ "
        "777 的 D1e（占位文案那条）会被漏掉",
        make("rangeCopy", live=[]), "死键 **", D, st, a))
    out.append(neg_case(
        "把对照臂 `Meta+v` 的 live 区改成**占位文案** ⟹ "
        "「桌有拒绝反馈通道」必须红",
        "★ 漏判方向 = 会得出「桌**没有**反馈通道」⟹ "
        "修法会指向「加反馈」而不是「让命令产生」",
        make("controlPaste", live=[PLACEHOLDER]),
        "桌**有**「无操作/拒绝」的反馈通道", D, st, a))
    out.append(neg_case(
        "把对照臂 `Meta+v` 的 disposition 改成 `COMMITTED` ⟹ "
        "「非 COMMITTED 的拒绝」必须红",
        "证明那条测的是 disposition 而不是「live 区非空」",
        make("controlPaste", disp="COMMITTED"),
        "disposition **非 `COMMITTED`**", D, st, a))
    out.append(neg_case(
        "★ 对照自己没改成：写一个 raw 里不存在的字段 ⟹ 不许有判据翻红",
        "mutatedAnything 为 false 时这条对照的结论是空的（R108）",
        nonexistent, "__永不匹配__", D, st, a))
    out.append(neg_case_extra_file(
        "★ 静态：给 director 面**注入**一个调 `navigator.clipboard` 的文件 ⟹ "
        "「零命中」必须红",
        "★ **这一条是「带作用域的搜索」唯一真正的对照**：只改真源码里的某个"
        "字符串，命中位置会变但**命中数仍是 0** ⟹ 必须注入新文件才能验",
        {"src/components/director/__neg781.ts":
         "export const leak = () => navigator.clipboard.writeText('x');\n"},
        "零** `navigator.clipboard`", D, st, a))
    out.append(neg_case_static(
        "★ 静态：把守卫挪到 C/V 分支**之后** ⟹ 「C/V 排在守卫之前」必须红",
        "证明归因落在顺序上",
        move_guard_after_cv, "`Cmd+C` 分支排在守卫**之后**", D, st, a))
    out.append(neg_case_static(
        "★ 静态：把内部包类型改名 ⟹ 「内部 clipboard 包」必须红",
        "证明「复制/粘贴完全内部」测的是**类型**而不是「有个 clipboard 字段」",
        drop_internal_clipboard_type, "内部包类型是", D, st, a))
    out.append(neg_case_static(
        "★ 静态：让 `getDirectorCommandFeedback` 对 COMMITTED 也返回 null "
        "的**反面** —— 改成不返回 null ⟹ 「COMMITTED→null」必须红",
        "证明「Copy 成功时面板只能显示占位文案」有机制依据",
        committed_feedback_no_longer_null, "`COMMITTED` 返回 null", D, st, a))
    return out


# ───────────────── 台账 / README ─────────────────
def artifact_checks():
    C = []
    if not LEDGER.exists():
        return [{"label": "台账在位", "pass": False, "got": "缺"}]
    txt = LEDGER.read_text(encoding="utf-8")
    mine = [ln for ln in txt.split("\n")
            if re.match(r"^\|\s*Batch\s+781\s*\|", ln)]
    C.append({"label": "台账：Batch 781 恰有一行", "pass": len(mine) == 1,
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
        print("缺少 runtime-audit.json（先跑 mk781audit.py）")
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
        {"batch": 781, "checks": checks, "pass": npass, "total": total,
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
    print("batch 781 %s" % ("通过" if ok else "不通过"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
