#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 780 验收器 —— **独立实现**，不 import 汇编器。

## 本批要防的错误方向

这一批的结论要用来**下调一条缺陷的严重度**（777 的 D1d，中-高 → 中）并
**合并**另一条（778 的 D1f）。下调比上调更危险，因为：

- 若把「焦点在控件上时 Delete **真的删得掉**」漏掉 ⟹ 「顺手」成立 ⟹
  D1d 保持中-高 ⟹ 会给用户一份「这个场景很常见」的错误印象，
  而真正的门槛是四步刻意操作。
- 若把「对照臂真的删掉了」漏掉 ⟹ 「删不掉」可能只是**探针删不动** ⟹
  严重度被下调到一个**没有证据**的更低位。
- 若把「守卫排在 Delete 分支之前」漏掉 ⟹ 归因错了 ⟹ 会去改错的分支。
- 若把「`Meta+c`/`Meta+v` 没测」当成「测过且正常」⟹ 矩阵里会出现一行
  没有证据的判据（774 只在**浮层落点**上测过它们）。

所以这四条**各配一条阴性对照**；静态层配**改源码**的对照。

## 沿用 775–779 的纪律

- 静态层**独立实现**（R107 / R110 / R128）
- 阴性对照的 `mutatedAnything` **实测**（R108）
- 阴性对照的 `kw` **取自判据标签字面量且唯一**（R118）
- 跨批数字**对账**：从 776 的 raw 重算族规模，再与 778 的产物对账
- `derive()` 对缺格健壮
"""
import copy
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch780-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAWDIR = OUTDIR / "raw"
PROBEDIR = OUTDIR / "probes"
README = OUTDIR / "README.md"
LEDGER = ROOT / "docs/research/VERIFICATION_LEDGER.md"
RAW776 = ROOT / "docs/research/liblib-canvas-batch776-2026-10-01/raw/vb776a.json"
AUDIT778 = ROOT / "docs/research/liblib-canvas-batch778-2026-10-01/runtime-audit.json"
AUDIT779 = ROOT / "docs/research/liblib-canvas-batch779-2026-10-01/runtime-audit.json"

RAW_FILES = ["vb780a.json"]
PROBE_FILES = ["dbg780a.py", "mk780audit.py", "add_ledger_row.py"]
FFFD = "�"
META = {"tries", "retried"}
GESTURE_ARMS = ["numberDelete", "numberBackspace", "rangeDelete",
                "rangeBackspace"]
CONTROL_ARM = "controlDelete"
ARMS = GESTURE_ARMS + [CONTROL_ARM]
PRESSES = 2
DELETE_CMD = "DELETE_OBJECTS"
DD = "src/components/director/DirectorDesk.tsx"


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


def static_side(sources=None):
    sources = sources or {}

    def load(rel):
        if rel in sources:
            return lines_of(sources[rel])
        p = ROOT / rel
        return lines_of(p.read_text(encoding="utf-8")) if p.exists() else None

    dl = load(DD)
    if dl is None:
        return {"err": "缺源码"}
    st = {}
    guard = first_in(dl, r"if \(isEditable\) return;")
    dele = first_in(dl, r'event\.key === "Delete" \|\| event\.key === "Backspace"')
    call = first_in(dl, r"deleteDirectorEntity\(", after=dele or 0)
    st["guardLine"], st["deleteBranchLine"] = guard, dele
    st["deleteCallLine"] = call
    st["deleteAfterGuard"] = bool(guard and dele and guard < dele)
    st["deleteCallAfterBranch"] = bool(dele and call and dele < call)
    st["deleteBranchCovered"] = bool(dele and
                                     re.search(r'Delete.*\|\|.*Backspace',
                                               "\n".join(dl[dele - 1:dele])))
    return st


# ───────────────── 原始读数（重算） ─────────────────
def load_raw():
    for f in RAW_FILES:
        if not (RAWDIR / f).exists():
            raise SystemExit("缺原始读数 %s —— 判失败，不许通过" % f)
    for f in PROBE_FILES:
        if not (PROBEDIR / f).exists():
            raise SystemExit("缺探针脚本 %s —— 判失败，不许通过" % f)
    raw = json.loads((RAWDIR / "vb780a.json").read_text(encoding="utf-8"))
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
    add("静态：Delete/Backspace 分支找得到", _ok(st.get("deleteBranchLine")))
    add("静态：★ 守卫排在 Delete 分支**之前** ⟹ 焦点在 `<input>` 上时 "
        "`:517` 够不着（这是「顺手不成立」的机制）",
        _ok(st.get("deleteAfterGuard")))
    add("静态：`deleteDirectorEntity` 调用点在该分支**之内**",
        _ok(st.get("deleteCallAfterBranch")))
    add("静态：★ 该分支**同时**覆盖 Delete 与 Backspace 两个键",
        _ok(st.get("deleteBranchCovered")))

    # ── 原始读数：自证起点与送达 ──
    add("原始：零 FAILED", D["unexpectedFailed"] == [], True)
    add("原始：臂集合齐（%d 臂）" % len(ARMS), D["keys"], sorted(ARMS))
    add("原始：两轮逐字段一致", _ok(D.get("roundsConsistent")))
    add("原始：按压格数 = %d 臂 × %d 次" % (len(ARMS), PRESSES),
        D.get("pressTotal"), len(ARMS) * PRESSES)
    for arm in ARMS:
        c = _a(D, arm)
        add("原始：%s 聚焦落上了" % arm, (c.get("focus") or {}).get("ok") is True)
        add("原始：%s 起始历史干净（past=0）" % arm,
            (c.get("stateBefore") or {}).get("past"), "0")
        add("原始：%s 起点有对象" % arm, (c.get("objectsBefore") or 0) > 0)
        add("原始：★ %s 每一次按压 `cap>=1` ⟹ 按键**真的送达了浏览器**，"
            "所以「没删掉」这个读数有鉴别力" % arm,
            bool(_presses(D, arm))
            and all((p["read"].get("cap") or 0) >= 1
                    for p in _presses(D, arm)))

    # ── 预测 A：对照臂（鉴别力）──
    cp = _presses(D, CONTROL_ARM)
    for p in cp:
        add("对照：第%s次**真的删掉 1 个对象** ⟹ `:517` 跑到了"
            % p.get("n"), p.get("objectsDropped"), 1)
        add("对照：第%s次目标对象不在了" % p.get("n"),
            p.get("oidStillThere") is False)
        add("对照：第%s次 `lastCommand=%s`" % (p.get("n"), DELETE_CMD),
            (p.get("state") or {}).get("lastCommand"), DELETE_CMD)
        add("对照：第%s次 `past=1`（删除进了历史）" % p.get("n"),
            (p.get("state") or {}).get("past"), "1")
    nCtrl = sum(1 for p in cp
                if p.get("objectsDropped") == 1
                and (p.get("state") or {}).get("lastCommand") == DELETE_CMD)
    add("★ 判别力成立：对照臂 %d/%d 次**真删掉**（对象数与 `lastCommand` 都对）"
        "⟹ 「gesture 臂删不掉」不是探针删不动" % (nCtrl, len(cp)),
        bool(cp) and nCtrl == len(cp))

    # ── 预测 B（★ 本批载荷）：gesture 臂删不掉 ──
    for arm in GESTURE_ARMS:
        for p in _presses(D, arm):
            s = p.get("state") or {}
            add("逐次：%s 第%s次 `win>=1` ⟹ 事件**到达了 window**"
                % (arm, p.get("n")), (p["read"].get("win") or 0) >= 1)
            add("逐次：★ %s 第%s次**一个对象都没少**" % (arm, p.get("n")),
                p.get("objectsDropped"), 0)
            add("逐次：%s 第%s次目标对象还在" % (arm, p.get("n")),
                p.get("oidStillThere") is True)
            add("逐次：%s 第%s次 `past=0`（没进历史）" % (arm, p.get("n")),
                s.get("past"), "0")
            add("逐次：★ %s 第%s次 `lastCommand` 停在 `GESTURE_BEGIN` "
                "（桌的键处理根本没走到 Delete 分支）" % (arm, p.get("n")),
                s.get("lastCommand"), "GESTURE_BEGIN")
    # ★ 聚合必须数**条件成立的按压**，不是按压总数 ——
    #   数总数的话这条断言恒真，三条阴性对照会全部「命中 0 条」（R108/R113 同族）。
    nNoPress = sum(len(_presses(D, arm)) for arm in GESTURE_ARMS)
    nNo = sum(1 for arm in GESTURE_ARMS for p in _presses(D, arm)
              if p.get("objectsDropped") == 0)
    add("★ 777 的「顺手」**不成立**：%d/%d 次按压删不掉任何对象 ⟹ "
        "真实序列是「键入 → 鼠标点删除按钮 → 点回控件 → Cmd+Z」"
        % (nNo, nNoPress), nNo == nNoPress)
    nCmd = sum(1 for arm in GESTURE_ARMS for p in _presses(D, arm)
               if (p.get("state") or {}).get("lastCommand") == "GESTURE_BEGIN")
    add("★ 桌的键处理在 %d/%d 次按压里**根本没走到** Delete 分支"
        % (nCmd, nNoPress), nCmd == nNoPress)

    # ── 跨批对账：族规模从 776 的 raw 重算，并与 778 产物对账 ──
    if RAW776.exists() and AUDIT778.exists() and AUDIT779.exists():
        c776 = json.loads(RAW776.read_text(encoding="utf-8"))["rounds"][0]["census"]
        best = {}
        for x in c776:
            if not x.get("selfJustified"):
                continue
            if x.get("id") not in best or (x.get("live") or 0) > (
                    best[x["id"]].get("live") or 0):
                best[x["id"]] = x
        add("族规模：776 普查每族都非空（逐族自证，防「少测」冒充「不存在」）",
            all((x.get("live") or 0) > 0 for x in best.values()))
        fam = {}
        for x in best.values():
            fam[x.get("wantType")] = fam.get(x.get("wantType"), 0) + (
                x.get("live") or 0)
        a778 = json.loads(AUDIT778.read_text(encoding="utf-8"))
        a779 = json.loads(AUDIT779.read_text(encoding="utf-8"))
        add("族规模：从 776 raw 重算 = 与 778 产物**一致**（跨批去重规则没变）",
            [fam.get("number"), fam.get("range")],
            [a778["familySizes"]["number"]["count"],
             a778["familySizes"]["range"]["count"]])
        add("族规模：两族合计 53（与 776 README 自述相符）",
            fam.get("number", 0) + fam.get("range", 0), 53)
        # ── 矩阵：每一行都要有出处，且未测的那行不许被当成已测 ──
        rows = {r["key"]: r for r in (a.get("matrix") or {}).get("rows") or []}
        add("矩阵：三行**已测**的键都在（Escape / Meta+z / Delete / Backspace）",
            all(k in rows for k in ("Escape", "Meta+z", "Delete / Backspace")),
            True)
        cv = rows.get("Meta+c / Meta+v")
        add("矩阵：★ `Meta+c`/`Meta+v` 那一行**显式标为本批未测**"
            "（774 只在浮层落点上测过，没在 gesture 控件上测过）",
            bool(cv) and "未测" in (cv.get("number") or "")
            and "未测" in (cv.get("range") or ""))
        add("矩阵：`notMeasured` 列出 `Meta+c` 与 `Meta+v`",
            sorted((a.get("matrix") or {}).get("notMeasured") or []),
            ["Meta+c", "Meta+v"])
        add("矩阵：★ `Escape` 行的数字取自 779 产物（现算，不手抄）",
            str(a779["results"]["firstSwallowPresses"]) in rows["Escape"]["number"],
            True)
        add("矩阵：`Delete / Backspace` 行的 range 侧用的是重算出的族规模",
            str(fam.get("range")) in rows["Delete / Backspace"]["range"], True)
    else:
        add("跨批产物在位（776 raw / 778 audit / 779 audit）", False)

    # ── 产物自洽 ──
    add("产物：audit.batch=780", a.get("batch"), 780)
    add("产物：audit 的「删不掉」计数 = 重算值",
        (a.get("results") or {}).get("noDeletePresses"), nNo)
    add("产物：audit 的守卫行号 = 静态重算",
        (a.get("static") or {}).get("guardLine"), st.get("guardLine"))
    add("产物：audit 的 Delete 分支行号 = 静态重算",
        (a.get("static") or {}).get("deleteBranchLine"),
        st.get("deleteBranchLine"))
    add("产物：audit 记的零 FAILED", (a.get("results") or {}).get("failedCells"), 0)
    return C


# ───────────────── 阴性对照 ─────────────────
def _fp(D):
    out = {}
    for arm, c in (D.get("arms") or {}).items():
        out[arm] = {
            "focus": (c.get("focus") or {}).get("ok"),
            "pastBefore": (c.get("stateBefore") or {}).get("past"),
            "objectsBefore": c.get("objectsBefore"),
            "presses": [{
                "cap": (p.get("read") or {}).get("cap"),
                "win": (p.get("read") or {}).get("win"),
                "objectsDropped": p.get("objectsDropped"),
                "oidStillThere": p.get("oidStillThere"),
                "past": (p.get("state") or {}).get("past"),
                "lastCommand": (p.get("state") or {}).get("lastCommand"),
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

    TOP_KEYS = ("objectsDropped", "oidStillThere", "objectsAfter")

    def make(arm, **patch):
        """统一的按压字段改写：`read` / `state` 之外的都当顶层格字段。
        ★ 顶层格字段与 `state` 里的字段**同名但不是一回事** ——
        `objectsDropped` 是探针算出来的，`state.past` 是从 DOM 读的。"""
        def f(raw):
            n = 0
            for rd in raw["rounds"]:
                for r in rd.get("rows") or []:
                    if r.get("arm") == arm and not r.get("FAILED"):
                        for p in r.get("presses") or []:
                            for k, v in patch.items():
                                if k == "read":
                                    p["read"] = dict(p.get("read") or {}, **v)
                                elif k == "state":
                                    p["state"] = dict(p.get("state") or {}, **v)
                                elif k in TOP_KEYS:
                                    p[k] = v
                                    if k == "objectsDropped":
                                        p["objectsAfter"] = (
                                            (p.get("objectsBefore") or 0) - v)
                                else:
                                    p["state"] = dict(p.get("state") or {},
                                                      **{k: v})
                            n += 1
            return raw if n else None
        return f

    def make_gesture(arm, **patch):
        """`objectsDropped` 与 `oidStillThere` 必须**一起**改 ——
        只改一个会让那一格自相矛盾（对象数少了但目标还在）。"""
        return make(arm, **patch)

    def nonexistent(raw):
        for rd in raw["rounds"]:
            for r in rd.get("rows") or []:
                if r.get("__永不匹配__") is None:
                    r["__永不匹配__"] = 1
                    return raw
        return raw

    def move_guard_after_delete():
        src = _read(DD)
        guard = "      if (isEditable) return;\n"
        br = '      if (event.key === "Delete" || event.key === "Backspace") {'
        if guard not in src or br not in src:
            return None
        src = src.replace(guard, "")
        i = src.find(br)
        j = src.find("\n      const directorState = ", i)
        if j < 0:
            return None
        return {DD: src[:j] + guard + src[j:]}

    def narrow_branch_to_delete_only():
        src = _read(DD)
        old = '      if (event.key === "Delete" || event.key === "Backspace") {'
        if old not in src:
            return None
        return {DD: src.replace(old, '      if (event.key === "Delete") {')}

    out.append(neg_case(
        "让 gesture 臂**真的删掉**对象 ⟹ 「顺手不成立」必须红",
        "★ 漏判方向 = 「顺手」成立 ⟹ D1d 保持中-高 ⟹ "
        "会给出「这个场景很常见」的错误印象",
        make_gesture("numberDelete", objectsDropped=1, oidStillThere=False),
        "顺手」**不成立**", D, st, a))
    out.append(neg_case(
        "★ 对称：让 rangeDelete 臂**真的删掉** ⟹ 同一条必须红",
        "★ 没有这条，number 与 range 两族的读数可以单独坏掉",
        make_gesture("rangeDelete", objectsDropped=1, oidStillThere=False),
        "顺手」**不成立**", D, st, a))
    out.append(neg_case(
        "让 gesture 臂的 `lastCommand` 变成 DELETE_OBJECTS ⟹ "
        "「桌的键处理没走到 Delete 分支」必须红",
        "证明那一条测的是 `lastCommand` 这个具体字段，而不是「对象数没变」",
        make("numberBackspace", state={"lastCommand": DELETE_CMD}),
        "桌的键处理在", D, st, a))
    out.append(neg_case(
        "让对照臂删不掉 ⟹ 「判别力成立」与「真删掉 1 个对象」必须红",
        "★ 漏判方向 = 「删不掉」只是探针删不动 ⟹ "
        "严重度被下调到一个**没有证据**的更低位",
        make(CONTROL_ARM, objectsDropped=0, state={"lastCommand":
                                                    "GESTURE_BEGIN",
                                                    "past": "0"}),
        "判别力成立：对照臂", D, st, a))
    out.append(neg_case(
        "★ 对照自己没改成：写一个 raw 里不存在的字段 ⟹ 不许有判据翻红",
        "mutatedAnything 为 false 时这条对照的结论是空的（R108）",
        nonexistent, "__永不匹配__", D, st, a))
    out.append(neg_case_static(
        "★ 静态：把守卫挪到 Delete 分支**之后** ⟹ 「守卫排在之前」必须红",
        "证明归因真的落在顺序上，而不是落在「Delete 分支存在」上",
        move_guard_after_delete, "守卫排在 Delete 分支**之前**", D, st, a))
    out.append(neg_case_static(
        "★ 静态：把该分支窄化成只管 `Delete` ⟹ 「同时覆盖两个键」必须红",
        "证明 Backspace 那两格不是「顺手多测的」—— 分支只管一个键时"
        "本批的 Backspace 读数就失去了机制依据",
        narrow_branch_to_delete_only, "**同时**覆盖 Delete 与 Backspace",
        D, st, a))
    return out


# ───────────────── 台账 / README ─────────────────
def artifact_checks():
    C = []
    if not LEDGER.exists():
        return [{"label": "台账在位", "pass": False, "got": "缺"}]
    txt = LEDGER.read_text(encoding="utf-8")
    mine = [ln for ln in txt.split("\n")
            if re.match(r"^\|\s*Batch\s+780\s*\|", ln)]
    C.append({"label": "台账：Batch 780 恰有一行", "pass": len(mine) == 1,
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
        print("缺少 runtime-audit.json（先跑 mk780audit.py）")
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
        {"batch": 780, "checks": checks, "pass": npass, "total": total,
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
    print("batch 780 %s" % ("通过" if ok else "不通过"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
