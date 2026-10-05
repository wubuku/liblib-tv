#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 777 验收器 —— **独立实现**，不 import 汇编器。

## 本批要防的错误方向

这一批的结论要用来**改写一条挂着的拍板项**（763 的 D1 后半句）。
如果判据有偏，**偏的方向**决定了错误的代价：

- 若把「输入框落点不可撤销」漏掉 ⟹ 会给用户一份「撤销一直可用」的建议 ⟹
  用户在输入框里删了东西就永久丢了。
- 若把「非输入框落点可撤销」漏掉 ⟹ 会把「零撤销入口」误报成「不可逆」⟹
  用户去申请一个**根本不需要**的「重置项目」功能。

所以验收器对这两条**各写一条阴性对照**，确保它们不是恒真。

## 沿用 775/776 的纪律

- 静态层**独立实现**（注释抹白而不删；只抹注释不抹字符串 R107；
  搜索带作用域 R117）
- 阴性对照的 `mutatedAnything` **实测**（比对派生指纹，R108）
- 阴性对照的 `kw` **取自判据标签字面量**（R118）
- `derive()` 对缺格健壮（缺格变红，不崩）
"""
import copy
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch777-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAWDIR = OUTDIR / "raw"
PROBEDIR = OUTDIR / "probes"
README = OUTDIR / "README.md"
LEDGER = ROOT / "docs/research/VERIFICATION_LEDGER.md"

RAW_FILES = ["vb777a.json"]
PROBE_FILES = ["dbg777a.py", "mk777audit.py"]
FFFD = "�"
META = {"tries", "retried"}
LANDINGS = ["fovInput", "deskButton", "body", "tree"]
TREE_ARM_EXPECTED_FAIL = "落点不可聚焦"
NON_INPUT = ["deskButton", "body"]

DD = "src/components/director/DirectorDesk.tsx"
FB_LIB = "src/lib/directorCommandFeedback.ts"
TREE_SRC = "src/components/director/DirectorObjectTree.tsx"


# ───────────────── 静态层（独立实现） ─────────────────
def blank_comments(s):
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


def first_in(lines, pat, after=0):
    rx = re.compile(pat)
    return next((n for n, ln in enumerate(lines, 1)
                 if n > after and rx.search(ln)), None)


def static_side():
    st = {}

    def load(rel):
        p = ROOT / rel
        if not p.exists():
            st["err"] = "缺源码 %s" % rel
            return []
        return blank_comments(p.read_text(encoding="utf-8")).split("\n")

    dl = load(DD)
    tl = load(TREE_SRC)
    st["guardLine"] = first_in(dl, r"if \(isEditable\) return;")
    st["undoLine"] = first_in(dl, r'key\.toLowerCase\(\) === "z"')
    st["undoAfterGuard"] = bool(st["guardLine"] and st["undoLine"]
                                and st["guardLine"] < st["undoLine"])
    st["historyAttrLines"] = [n for n, ln in enumerate(dl, 1)
                              if "data-director-history-past" in ln
                              or "data-director-history-future" in ln]
    st["feedbackPanelLine"] = first_in(dl, r"无命令反馈")
    fb = ROOT / FB_LIB
    st["committedReturnsNull"] = bool(
        fb.exists() and 'disposition === "COMMITTED") return null'
        in fb.read_text(encoding="utf-8"))
    # ★ 按行删除按钮带 `stopPropagation()` —— 这是「输入框在删除后留在屏上」的前提
    i = next((n for n, ln in enumerate(tl, 1)
              if "data-director-delete-object" in ln), None)
    st["rowDeleteLine"] = i
    st["rowDeleteStopPropagation"] = bool(
        i and "event.stopPropagation();" in "\n".join(tl[i - 1:i + 14]))
    return st


# ───────────────── 原始读数（重算） ─────────────────
def load_raw():
    for f in RAW_FILES:
        if not (RAWDIR / f).exists():
            raise SystemExit("缺原始读数 %s —— 判失败，不许通过" % f)
    for f in PROBE_FILES:
        if not (PROBEDIR / f).exists():
            raise SystemExit("缺探针脚本 %s —— 判失败，不许通过" % f)
    raw = json.loads((RAWDIR / "vb777a.json").read_text(encoding="utf-8"))
    if len(raw.get("rounds") or []) != 2:
        raise SystemExit("轮数不是 2")
    return raw


def strip(x):
    if isinstance(x, dict):
        return {k: v for k, v in x.items() if k not in META}
    return [{k: v for k, v in r.items() if k not in META} for r in (x or [])]


def derive(raw):
    D = {"unexpectedFailed": [], "expectedFailed": []}
    cells = {}
    for rd in raw["rounds"]:
        for r in strip(rd.get("rows")):
            cells.setdefault(r.get("landing"), []).append(r)
    D["cells"] = {k: v[0] for k, v in cells.items()}
    D["landings"] = sorted(cells)
    for k, c in D["cells"].items():
        f = c.get("FAILED")
        if not f:
            continue
        (D["expectedFailed"] if (k == "tree"
                                 and TREE_ARM_EXPECTED_FAIL in f)
         else D["unexpectedFailed"]).append("%s: %s" % (k, f))
    D["census"] = [strip(rd.get("census")) for rd in raw["rounds"]]
    D["feedback"] = [rd.get("feedback") or {} for rd in raw["rounds"]]
    D["persist"] = [rd.get("persist") or {} for rd in raw["rounds"]]
    D["roundsConsistent"] = (strip(raw["rounds"][0].get("rows"))
                             == strip(raw["rounds"][1].get("rows")))
    return D


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

    K = D["cells"]
    c0 = D["census"][0] if D["census"] else {}
    fb = (D["feedback"][0] or {}).get("after") or {}
    p0 = D["persist"][0] if D["persist"] else {}

    # ── 静态 ──
    add("静态：守卫找得到", _ok(st.get("guardLine")))
    add("静态：Cmd+Z 分支找得到", _ok(st.get("undoLine")))
    add("静态：★ 守卫排在 Cmd+Z 分支**之前** ⟹ 焦点在输入框时 undo 到不了",
        _ok(st.get("undoAfterGuard")))
    add("静态：桌根仍暴露 history-past/future（本批读数方法的前提）",
        _ok(st.get("historyAttrLines")))
    add("静态：反馈面板在位（无命令反馈那行还在）",
        _ok(st.get("feedbackPanelLine")))
    add("静态：★ `getDirectorCommandFeedback` 对 COMMITTED 返回 null"
        "（这才是「成功删除后显示『无命令反馈』」的机制）",
        _ok(st.get("committedReturnsNull")))
    add("静态：按行删除按钮带 stopPropagation"
        "（「输入框在删除后留在屏上」的前提）",
        _ok(st.get("rowDeleteStopPropagation")))

    # ── 覆盖 ──
    add("覆盖：落点集合恰为 %r" % (LANDINGS,), D["landings"], sorted(LANDINGS))
    add("覆盖：没有非预期 FAILED", D["unexpectedFailed"], [])
    add("覆盖：★ `tree` 臂**预期**失败且理由是「落点不可聚焦」"
        "（探针的自证：它与 body 臂是同一格，不许照报成两格）",
        len(D["expectedFailed"]), 1)
    add("一致性：两轮逐字段一致（已排除 tries/retried）",
        D["roundsConsistent"], True)

    # ── 四臂逐格自证 ──
    for k in ("fovInput",) + tuple(NON_INPUT):
        c = K.get(k) or {}
        add("%s 臂：起始历史干净（past=0）" % k,
            (c.get("before") or {}).get("past"), "0")
        add("%s 臂：删除后道具真的没了" % k, c.get("mugGone"), True)
        add("%s 臂：按行删除**没有改选中**（否则「输入框留在屏上」的前提没了）"
            % k, c.get("selectionKept"), True)
        add("%s 臂：删除进历史（past 0→1）" % k,
            (c.get("afterDelete") or {}).get("past"), "1")
    add("★ fovInput 臂：落点确实是**输入框**（否则那一格测的不是「输入框焦点」）",
        ((K.get("fovInput") or {}).get("atLanding") or {}).get("focusInInput"),
        True)
    for k in ("tree", "deskButton"):
        # ★ 预期失败的臂（`tree`：落点不可聚焦）根本没有 `atLanding` ——
        #   对它跑「不重复」的自证，等于**要求一个已被判无效的格自证成功**。
        if k in [f.split(":")[0] for f in D["expectedFailed"]]:
            continue
        add("%s 臂：落点与 body 臂**不重复**（焦点不是 BODY）" % k,
            ((K.get(k) or {}).get("atLanding") or {}).get("focusTag")
            not in (None, "BODY"), True)

    # ── 读数 1：删除进历史 ──
    add("R-past：删除进历史（非输入框三臂 past 0→1）",
        sum(1 for k in ("fovInput",) + tuple(NON_INPUT)
            if ((K.get(k) or {}).get("afterDelete") or {}).get("past") == "1"),
        3)

    # ── 读数 2：撤销的可用性（★ 两条各有一条阴性对照） ──
    add("R-undo：★ 非输入框落点**全部**能撤销（道具回到对象树）",
        sum(1 for k in NON_INPUT if (K.get(k) or {}).get("mugBack") is True),
        len(NON_INPUT))
    for k in NON_INPUT:
        u = (K.get(k) or {}).get("afterUndo") or {}
        add("R-undo：%s 臂撤销后历史结构正确（past→0、future→1）" % k,
            (u.get("past"), u.get("future")), ("0", "1"))
    f = K.get("fovInput") or {}
    add("★ R-undo：**输入框落点撤销无效**（道具没有回来）"
        "—— 这条若漏，会给用户一份「撤销一直可用」的错误建议",
        f.get("mugBack"), False)
    fu = f.get("afterUndo") or {}
    add("★ R-undo：输入框落点撤销后历史**没动**（past 仍=1、future 仍=0）"
        "⟹ 是**命令被吞**，不是「撤销了但没生效」",
        (fu.get("past"), fu.get("future")), ("1", "0"))

    # ── 读数 3：跨 reload 持久化 ──
    add("R-persist：那一格跑成了", _ok(p0.get("afterReload")))
    # ★ 字段名有歧义：`beforeReload.mug` 记的是「**删除之后、reload 之前**」
    #   道具在不在 ⟹ 它**应该**是 False（删掉了）。第一版按字面读成
    #   「删除前道具在」⟹ 判据写反 ⟹ 报出一条不存在的 FAIL。
    add("R-persist：删除后（reload 前）道具**已不在**",
        (p0.get("beforeReload") or {}).get("mug"), False)
    add("★ R-persist：reload 并重开桌后道具**仍然不在**（删除持久化成立）",
        (p0.get("afterReload") or {}).get("mug"), False)
    add("R-persist：reload 前后对象数不变（没有别的东西在动）",
        (p0.get("afterReload") or {}).get("n"),
        (p0.get("beforeReload") or {}).get("n"))
    add("★ R-persist：reload 后撤销历史**归零** ⟹ reload 之后删除真的没退路",
        ((p0.get("afterReload") or {}).get("state") or {}).get("past"), "0")

    # ── 读数 4：入口与提示 ──
    add("R-affordance：普查自证桌在（否则「没找到提示」不算数）",
        c0.get("deskOk"), True)
    add("R-affordance：按行删除入口 ≥ 1（普查前提成立）",
        _ok((c0.get("rowDelete") or 0) >= 1), True)
    add("★ R-affordance：桌内**撤销类控件 0 个**（普查与删除后各测一次）",
        (len(c0.get("undoish") or []), fb.get("undoishCount")), (0, 0))
    add("★ R-affordance：删除后 live 区里出现**「无命令反馈」**"
        "（成功提交后界面告诉用户「无反馈」）",
        _ok(any("无命令反馈" in (t or "")
                for t in (fb.get("liveTexts") or []))), True)

    # ── 产物纪律 ──
    add("产物：runtime-audit.json 在位", AUDIT.exists())
    add("产物：更正恰为 C777-1",
        [c.get("id") for c in (a.get("corrections") or [])], ["C777-1"])
    add("产物：教训为 R119–R122",
        [x.get("id") for x in (a.get("probeLessons") or [])],
        ["R119", "R120", "R121", "R122"])
    add("产物：两个缺陷（D1d 撤销不可用 / D1e 零入口）",
        sorted(d.get("id") for d in (a.get("defects") or [])),
        ["D1d", "D1e"])
    add("产物：汇编器与我**独立算出的**守卫行号一致",
        (a.get("static") or {}).get("guardLine"), st.get("guardLine"))
    add("产物：汇编器与我独立算出的 Cmd+Z 行号一致",
        (a.get("static") or {}).get("undoLine"), st.get("undoLine"))
    add("产物：★ 结论把「不可逆」判为**不成立**（而不是跟着 763 的原话）",
        (a.get("verdict") or {}).get("不可逆"),
        "**不成立**（非输入框落点 2/2 能撤销）")
    return C


# ───────────────── 阴性对照 ─────────────────
def _fp(o):
    if isinstance(o, dict):
        return {str(k): _fp(v) for k, v in o.items()
                if not (isinstance(k, str) and k.startswith("_"))}
    if isinstance(o, (list, tuple)):
        return [_fp(x) for x in o]
    return o


def _fingerprint(D):
    return json.dumps(_fp(D), ensure_ascii=False, sort_keys=True, default=str)


def neg_case(name, why, mutate, kw, D, st, a):
    raw2 = mutate(copy.deepcopy(D.get("_raw")))
    if raw2 is None:
        return {"name": name, "why": why, "caught": False,
                "mutatedAnything": False, "kwMatchedCount": 0,
                "expectFailOn": kw}
    D2 = derive(raw2)
    C2 = run_checks(a, copy.deepcopy(st), D2)
    bp = {c["label"]: c["pass"] for c in
          run_checks(a, copy.deepcopy(st), derive(copy.deepcopy(D.get("_raw"))))}
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

    def flip_input_undo(raw):
        n = 0
        for rd in raw["rounds"]:
            for r in rd.get("rows") or []:
                if r.get("landing") == "fovInput" and not r.get("FAILED"):
                    r["mugBack"] = True
                    r["afterUndo"] = dict(r.get("afterUndo") or {},
                                         past="0", future="1")
                    n += 1
        return raw if n else None

    def flip_noninput_undo(raw):
        n = 0
        for rd in raw["rounds"]:
            for r in rd.get("rows") or []:
                if r.get("landing") in NON_INPUT and not r.get("FAILED"):
                    r["mugBack"] = False
                    n += 1
        return raw if n else None

    def add_undoish(raw):
        n = 0
        for rd in raw["rounds"]:
            c = rd.get("census")
            if isinstance(c, dict):
                c["undoish"] = ["撤销"]
                n += 1
            f = rd.get("feedback")
            if isinstance(f, dict) and isinstance(f.get("after"), dict):
                f["after"]["undoishCount"] = 1
        return raw if n else None

    def kill_no_feedback(raw):
        n = 0
        for rd in raw["rounds"]:
            f = rd.get("feedback")
            if isinstance(f, dict) and isinstance(f.get("after"), dict):
                f["after"]["liveTexts"] = ["已删除 1 个对象"]
                n += 1
        return raw if n else None

    def unpersist(raw):
        n = 0
        for rd in raw["rounds"]:
            p = rd.get("persist")
            if isinstance(p, dict) and p.get("afterReload"):
                p["afterReload"]["mug"] = True
                n += 1
        return raw if n else None

    def set_past(raw):
        n = 0
        for rd in raw["rounds"]:
            for r in rd.get("rows") or []:
                if not r.get("FAILED") and isinstance(r.get("afterDelete"), dict):
                    r["afterDelete"]["past"] = "0"
                    n += 1
        return raw if n else None

    def nonexistent(raw):
        n = 0
        for rd in raw["rounds"]:
            for r in rd.get("rows") or []:
                r["__不存在的字段__"] = 1
                n += 1
        return raw if n else None

    out.append(neg_case(
        "把输入框落点的撤销改成「成功了」 ⟹ 「撤销无效」必须红",
        "★ 这条判据若恒真，会给用户一份「撤销一直可用」的错误建议",
        flip_input_undo, "输入框落点撤销无效", D, st, a))
    out.append(neg_case(
        "把非输入框落点的撤销改成「失败」 ⟹ 「全部能撤销」必须红",
        "★ 这条若恒真，会把「零撤销入口」误报成「不可逆」⟹ 用户去申请"
        "一个根本不需要的「重置项目」功能",
        flip_noninput_undo, "非输入框落点**全部**能撤销", D, st, a))
    out.append(neg_case(
        "给桌里加一个撤销按钮 ⟹ 「撤销类控件 0 个」必须红",
        "证明「零入口」这条读数不是恒真", add_undoish,
        "撤销类控件 0 个", D, st, a))
    out.append(neg_case(
        "把 live 区文案改成「已删除 1 个对象」 ⟹ 「出现『无命令反馈』」必须红",
        "证明那条判据测的是**具体文案**而不是「live 区非空」",
        kill_no_feedback, "无命令反馈", D, st, a))
    out.append(neg_case(
        "把跨 reload 改成「道具回来了」 ⟹ 「持久化成立」必须红",
        "证明持久化这条不是恒真", unpersist, "仍然不在", D, st, a))
    out.append(neg_case(
        "把删除后的 past 改成 0 ⟹ 「删除进历史」必须红",
        "证明「进历史」这条不是恒真（也是 D1d 的前提：历史里有才谈得上被吞）。"
        "★ 改 `past` 会**连带**打红「逐臂 past=1」那几条 ⟹ 这是合理的，"
        "所以 kw 要精确到**聚合那条**判据，否则会命中 4 条（775 的 R118："
        "kw 必须取自标签字面量，且要选**唯一**的那一条）",
        set_past, "R-past：删除进历史", D, st, a))
    out.append(neg_case(
        "★ 对照自己没改成：改一个 raw 里不存在的字段名 ⟹ 不许有判据翻红",
        "mutatedAnything 为 false 时这条对照的结论是空的（R108）",
        nonexistent, "__永不匹配__", D, st, a))
    return out


# ───────────────── 台账 / README ─────────────────
def artifact_checks():
    C = []
    if not LEDGER.exists():
        return [{"label": "台账在位", "pass": False, "got": "缺"}]
    txt = LEDGER.read_text(encoding="utf-8")
    lines = [ln for ln in txt.split("\n") if ln.strip()]
    mine = [ln for ln in lines if re.match(r"^\|\s*Batch\s+777\s*\|", ln)]
    C.append({"label": "台账：Batch 777 恰有一行", "pass": len(mine) == 1,
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
        print("缺少 runtime-audit.json（先跑 mk777audit.py）")
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
        {"batch": 777, "checks": checks, "pass": npass, "total": total,
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
            print("  ✗ 漏放：%s  翻红=%r" % (n["name"],
                                            (n.get("flipped") or [])[:4]))
    print("batch 777 %s" % ("通过" if ok else "不通过"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
