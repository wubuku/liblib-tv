#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 778 验收器 —— **独立实现**，不 import 汇编器。

## 本批要防的错误方向

这一批的结论要用来**改写一条挂着的拍板项**（777 的 D1d 及其修法授权范围）。
判据有偏时，**偏的方向**决定错误的代价：

- 若把「number 族的原生撤销没顶上来」漏掉（探针其实什么也撤不掉）⟹
  会把 **27 个**控件误报成死键 ⟹ 修法会去动一块**本来正常**的语义。
- 若把「range 族是死键」漏掉 ⟹ **26 个**滑杆的缺陷被放过 ⟹
  用户「刚拖完滑杆就按 `Cmd+Z`」永远没反应，且没人知道。
- 若把「D1d 只在 range 族成立」漏掉 ⟹ 给出「改 number 族的早退语义」这条
  **会引入数据错**的建议（见 C778-1 / J2）。
- 若把「守卫能整体去掉」漏掉 ⟹ 一次改动把 number 用户的 `Cmd+Z`
  从「撤自己的字」变成「撤上一个动作」。

所以这四条**各配一条阴性对照**，并且头两条是**对称**的 ——
漏判的方向不同，错误的代价也不同。

## 为什么静态层也要阴性对照

本批汇编器的静态层在写出来时连踩**四次**「找到错的」（见 R128）：
忘 `.split("\\n")`、命中类型声明、取首次而非末次、`\\b` 命中 `fov-field`。
四次都是「断言恒假」，也就是**判据可能根本不测东西**。
所以静态层用**改源码**的阴性对照来证明它不是恒真：
把守卫挪到 Cmd+Z 分支之后、把 `onPointerUp` 的分派删掉，两处都必须翻红。

## 沿用 775/776/777 的纪律

- 静态层**独立实现**（注释抹白而不删 R107；搜索带作用域 R110/R117/R128）
- 阴性对照的 `mutatedAnything` **实测**（比对派生指纹，R108）
- 阴性对照的 `kw` **取自判据标签字面量且唯一**（R118）
- `derive()` 对缺格健壮（缺格变红，不崩）
"""
import copy
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch778-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAWDIR = OUTDIR / "raw"
PROBEDIR = OUTDIR / "probes"
README = OUTDIR / "README.md"
LEDGER = ROOT / "docs/research/VERIFICATION_LEDGER.md"

RAW_FILES = ["vb778a.json"]
PROBE_FILES = ["dbg778a.py", "mk778audit.py"]
FFFD = "�"
META = {"tries", "retried"}
FAMS = ["number", "range"]
ARMS_DISTINCT = ["native", "docAfterBlur", "delWhileFocused"]
DUP_PAIR = ["native", "whileFocused"]
MUG = "director-prop-mug"

DD = "src/components/director/DirectorDesk.tsx"
GB_SRC = "src/components/director/useDirectorGestureBoundary.ts"
INSP = "src/components/director/DirectorInspector.tsx"
RAW776 = (ROOT / "docs/research/liblib-canvas-batch776-2026-10-01"
          "/raw/vb776a.json")


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


def first_in(lines, pat, after=0):
    """★ 搜索必须带作用域，且**收的是行列表**（不是整串，否则逐字符匹配恒假
    —— R128①）。"""
    rx = re.compile(pat)
    return next((n for n, ln in enumerate(lines, 1) if n > after
                 and rx.search(ln)), None)


def last_in(lines, pat):
    """★ 取**末次**出现：handler 名字常在类型声明里也有一份（R128②）。"""
    rx = re.compile(pat)
    return max((n for n, ln in enumerate(lines, 1) if rx.search(ln)),
               default=None)


def last_before(lines, pat, before):
    """★ 取 `before` 之前**最后**一个匹配（`type="range"` 在本文件出现十几次）。
    ★ 第一版这里写成了 `next(...)` ⟹ 实际返回**首个** ⟹ 名字与实现不符，
    报出 1353 而不是 1647。**两个独立实现互相抓到它**（汇编器给 1647），
    这正是「静态层独立实现」这条纪律的用处。"""
    rx = re.compile(pat)
    return max((n for n, ln in enumerate(lines, 1)
                if n < before and rx.search(ln)), default=None)


def static_side(sources=None):
    """`sources` 可传**改过的**源码文本 ⟹ 静态层的阴性对照用它。"""
    sources = sources or {}

    def load(rel):
        if rel in sources:
            return lines_of(sources[rel])
        p = ROOT / rel
        if not p.exists():
            return None
        return lines_of(p.read_text(encoding="utf-8"))

    st = {}
    dl = load(DD)
    gb = load(GB_SRC)
    insp = load(INSP)
    if dl is None or gb is None or insp is None:
        return {"err": "缺源码"}

    st["guardLine"] = first_in(dl, r"if \(isEditable\) return;")
    st["undoLine"] = first_in(dl, r'key\.toLowerCase\(\) === "z"')
    st["guardBeforeUndo"] = bool(st["guardLine"] and st["undoLine"]
                                 and st["guardLine"] < st["undoLine"])
    # ★ `isEditable` 判据**不看 `type`** ⟹ number 与 range 走同一条分支。
    #   这正是「D1d 两族同形」的机制，也是「守卫不能整体去掉」的根。
    p0 = first_in(dl, r"const isEditable =")
    p1 = first_in(dl, r"if \(event\.isComposing\)", after=p0 or 0)
    pred = "\n".join(dl[(p0 or 1) - 1:(p1 or 1) - 1]) if (p0 and p1) else ""
    st["isEditableLine"] = p0
    st["isEditableConsultsType"] = bool(
        re.search(r"\.type\b|getAttribute\(.type.\)", pred))
    st["isEditableMentionsTagName"] = bool(
        re.search(r'INPUT|TEXTAREA|SELECT', pred))
    # ★ 实现体里的 onFocus/onBlur（不是 `:17-24` 的类型声明，R128②）
    gbs = "\n".join(gb)
    st["onFocusBegins"] = bool(re.search(r"onFocus:\s*begin\b", gbs))
    st["onBlurCommits"] = bool(re.search(r"onBlur:\s*commit\b", gbs))
    st["onFocusLine"] = last_in(gb, r"onFocus:")
    st["onBlurLine"] = last_in(gb, r"onBlur:")
    # ★ 同仓已有的按 type 分派先例（R128③：取 data 属性**之前最后一个**）
    pu = last_in(gb, r"onPointerUp:")
    pc = last_in(gb, r"onPointerCancel:")
    body = ("\n".join(gb[(pu or 1) - 1:(pc or 1) - 1])
            if pu and pc and pu < pc else "")
    st["onPointerUpLine"] = pu
    st["onPointerUpDispatchesNumber"] = bool(
        "HTMLInputElement" in body and '=== "number"' in body)
    # ★ 属性名**精确**匹配：`\b` 在 `-` 前也算词边界 ⟹ `fov\b` 会命中
    #   `fov-field`，而探针的 CSS `[data-director-camera-fov]` 是精确匹配（R128④）
    fa = first_in(insp, r"data-director-camera-fov(?![-\w])")
    fr = last_before(insp, r'type="range"', fa) if fa else None
    xa = first_in(insp, r"data-director-transform-field(?![-\w])")
    xr = last_before(insp, r'type="number"', xa) if xa else None
    st["fovAttrLine"], st["fovTypeLine"] = fa, fr
    st["xfAttrLine"], st["xfTypeLine"] = xa, xr
    st["fovIsRange"] = bool(fr and fa and 0 < fa - fr <= 6)
    st["xfIsNumber"] = bool(xr and xa and 0 < xa - xr <= 6)
    return st


# ───────────────── 原始读数（重算） ─────────────────
def load_raw():
    for f in RAW_FILES:
        if not (RAWDIR / f).exists():
            raise SystemExit("缺原始读数 %s —— 判失败，不许通过" % f)
    for f in PROBE_FILES:
        if not (PROBEDIR / f).exists():
            raise SystemExit("缺探针脚本 %s —— 判失败，不许通过" % f)
    raw = json.loads((RAWDIR / "vb778a.json").read_text(encoding="utf-8"))
    if len(raw.get("rounds") or []) != 2:
        raise SystemExit("轮数不是 2")
    return raw


GESTURE_RX = re.compile(r"director-gesture-\d+-(\d+)")


def norm(x):
    """★ gesture id 内嵌 epoch ms ⟹ 不归一化的话「两轮一致」与「两臂同格」
    两件事都测不了（R116 / R125）。"""
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
    """★ 剔掉 `arm`（臂的**标签**，不是读数）——留着它同格比较必然失败。"""
    r = {k: v for k, v in row.items() if k not in META}
    r.pop("arm", None)
    return r


def derive(raw):
    D = {"unexpectedFailed": [], "cells": {}}
    cells = {}
    for rd in raw.get("rounds") or []:
        for r in strip(rd.get("rows")):
            cells.setdefault((r.get("family"), r.get("arm")), []).append(norm(r))
    D["cells"] = {k: v[0] for k, v in cells.items()}
    D["rounds"] = {k: v for k, v in cells.items()}
    D["keys"] = sorted("%s/%s" % k for k in cells)
    for k, v in cells.items():
        if v[0].get("FAILED"):
            D["unexpectedFailed"].append("%s/%s: %s"
                                         % (k[0], k[1], v[0]["FAILED"]))
    D["lifecycle"] = [strip(rd.get("lifecycle")) for rd in raw.get("rounds") or []]
    D["roundsConsistent"] = (norm(strip(raw["rounds"][0].get("rows")))
                             == norm(strip(raw["rounds"][1].get("rows"))))
    D["lifecycleConsistent"] = (norm(D["lifecycle"][0] if D["lifecycle"] else None)
                                == norm(D["lifecycle"][1] if len(D["lifecycle"]) > 1
                                        else None))
    # ★ 同格自证（剔掉臂标签后逐字段比较）
    D["dup"] = {}
    for fam in FAMS:
        a = cells.get((fam, DUP_PAIR[0]))
        b = cells.get((fam, DUP_PAIR[1]))
        D["dup"][fam] = bool(a and b
                             and reading(a[0]) == reading(b[0]))
    D["distinctCells"] = len(FAMS) * len(ARMS_DISTINCT)
    D["ranCells"] = len(cells)
    return D


def _c(D, fam, arm):
    return D["cells"].get((fam, arm)) or {}


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
    add("静态：`if (isEditable) return;` 找得到", _ok(st.get("guardLine")))
    add("静态：Cmd+Z 分支找得到", _ok(st.get("undoLine")))
    add("静态：★ 守卫排在 Cmd+Z 分支**之前** ⟹ 焦点在可编辑元素时 undo 到不了",
        _ok(st.get("guardBeforeUndo")))
    add("静态：`isEditable` 判据找得到", _ok(st.get("isEditableLine")))
    add("静态：判据按 tagName 认可编辑元素", _ok(st.get("isEditableMentionsTagName")))
    add("静态：★ `isEditable` 判据**不看 `type`** ⟹ 两族走同一条分支"
        "（这既是 D1d 两族同形的机制，也是「守卫不能整体去掉」的根）",
        st.get("isEditableConsultsType") is False)
    add("静态：实现体里 `onFocus: begin`（不是只声明了名字）",
        _ok(st.get("onFocusBegins")))
    add("静态：★ 实现体里 `onBlur: commit` ⟹ 改动**要等移开焦点才进历史**",
        _ok(st.get("onBlurCommits")))
    add("静态：★ `onPointerUp` 已按 `type === \"number\"` 分派 "
        "⟹ 同仓已有分流先例可抄", _ok(st.get("onPointerUpDispatchesNumber")))
    add("静态：★ 777 的 `fovInput` 臂那个元素仍是 `type=\"range\"` ⟹ "
        "777 的 D1d 是 n=1 的 range 样本", _ok(st.get("fovIsRange")))
    add("静态：变换字段那个元素仍是 `type=\"number\"` ⟹ number 族代表元素在位",
        _ok(st.get("xfIsNumber")))

    # ── 原始读数 ──
    add("原始：零 FAILED", D["unexpectedFailed"] == [], True)
    add("原始：臂集合齐（2 族 × 4 臂）",
        D["ranCells"] == len(FAMS) * 4, True)
    add("原始：两轮逐字段一致（gesture id 已归一化）",
        _ok(D.get("roundsConsistent")))
    add("原始：生命周期两轮一致", _ok(D.get("lifecycleConsistent")))
    add("原始：★ 同格自证 —— %s/%s 两臂（剔掉臂标签）逐字段一致"
        % (DUP_PAIR[0], DUP_PAIR[1]),
        all((D.get("dup") or {}).values()))
    add("原始：★ 格数按同格折算后是 %d（跑了 %d 格，其中 1 格重复）"
        % (D.get("distinctCells", 0), D.get("ranCells", 0)),
        D.get("distinctCells") == len(FAMS) * len(ARMS_DISTINCT))

    # ── 预测 A：`delWhileFocused` ⟹ D1d ──
    for fam in FAMS:
        c = _c(D, fam, "delWhileFocused")
        u = c.get("stateAfterUndo") or {}
        add("逐族：%s 删除后道具不在（这一格的前提成立）" % fam,
            c.get("mugGoneAfterDel") is True)
        add("逐族：%s 删除后 past=1（删除确实进了历史）" % fam,
            c.get("pastAfterDel"), "1")
        add("逐族：★ %s 撤销后 lastCommand **不是** UNDO "
            "⟹ 桌的键处理根本没被触到" % fam, u.get("lastCommand") != "UNDO")
        add("逐族：%s 撤销后 past=1 future=0（命令被吞、历史没动）" % fam,
            [u.get("past"), u.get("future")], ["1", "0"])
        add("逐族：★ %s 撤销后道具**没回来**" % fam, c.get("mugBack") is False)
    nBlocked = sum(1 for f in FAMS
                   if _c(D, f, "delWhileFocused").get("mugBack") is False)
    add("★ D1d 在两族上都成立（%d/%d）⟹ **范围没有被收窄**，"
        "原生撤销顶不上删除" % (nBlocked, len(FAMS)),
        nBlocked == len(FAMS))

    # ── 预测 B：手势生命周期 ⟹ blur 时才提交 ──
    # ★ 只跑**第 1 轮**：两轮一致性另有判据，逐格跑第 2 轮会让每个标签出现两次
    #   ⟹ 阴性对照的 `kw` 必然命中多条（R118 的新变体）。
    for rd in (D.get("lifecycle") or [])[:1]:
        for fam in FAMS:
            c = next((x for x in rd if x.get("family") == fam), None)
            add("生命周期：%s 有读数" % fam, c is not None)
            if not c:
                continue
            add("生命周期：%s 聚焦后 past=0" % fam,
                (c.get("onFocus") or {}).get("past"), "0")
            add("生命周期：★ %s 改动后 past=0（改动期间**不**提交）" % fam,
                (c.get("afterMutate") or {}).get("past"), "0")
            add("生命周期：★ %s blur 后 past=1（blur 才提交）" % fam,
                (c.get("afterBlur") or {}).get("past"), "1")
            add("生命周期：%s blur 后手势清空" % fam,
                (c.get("afterBlur") or {}).get("gesture"), "")
            add("生命周期：%s blur 后 lastCommand=GESTURE_COMMIT" % fam,
                (c.get("afterBlur") or {}).get("lastCommand"), "GESTURE_COMMIT")
    nLife = 0
    for fam in FAMS:
        c = next((x for x in (D.get("lifecycle") or [[]])[0]
                  if x.get("family") == fam), None)
        if not c or c.get("FAILED"):
            continue
        if ((c.get("onFocus") or {}).get("past") == "0"
                and (c.get("afterMutate") or {}).get("past") == "0"
                and (c.get("afterBlur") or {}).get("past") == "1"):
            nLife += 1
    add("★ 手势生命周期两族一致：聚焦后 past=0 → 改动后 past=0 → blur 后 past=1"
        "（%d/%d）⟹ 改动**要等移开焦点才进历史**" % (nLife, len(FAMS)),
        nLife == len(FAMS))

    # ── 预测 C：blur 后可撤，且占掉唯一撤销槽 ──
    for fam in FAMS:
        c = _c(D, fam, "docAfterBlur")
        u = c.get("stateAfterUndo") or {}
        add("blur 后：%s 焦点确实落在 BUTTON 上" % fam,
            (c.get("stateAfterBlur") or {}).get("focusTag"), "BUTTON")
        add("blur 后：%s lastCommand=UNDO（守卫不触发了）" % fam,
            u.get("lastCommand"), "UNDO")
        add("blur 后：%s past=0 future=1" % fam,
            [u.get("past"), u.get("future")], ["0", "1"])
        add("blur 后：%s 值被撤回去了" % fam,
            c.get("valueAfterUndo") != c.get("valueAtUndo"))
    nSlot = sum(1 for f in FAMS
                if (_c(D, f, "docAfterBlur").get("stateAfterUndo") or {})
                .get("future") == "1")
    add("★ blur 后两族都把**唯一**的撤销槽占掉了（%d/%d）⟹ "
        "守卫在 number 族上是承重墙" % (nSlot, len(FAMS)), nSlot == len(FAMS))

    # ── 预测 D：焦点在内时的原生撤销（★ 成对） ──
    rev = {}
    for fam in FAMS:
        c = _c(D, fam, DUP_PAIR[0])
        base = (c.get("valueAfterMutate") or {}).get("value")
        after = (c.get("valueAfterUndo") or {}).get("value")
        rev[fam] = (base is not None and after != base)
        add("焦点内：%s 记到了改动后的基准值" % fam, base is not None)
        add("焦点内：%s lastCommand 不是 UNDO（守卫拦住了）" % fam,
            (c.get("stateAfterUndo") or {}).get("lastCommand") != "UNDO")
    add("★ 焦点内：number 族的**原生撤销顶上了**（值回到改动前）",
        _ok(rev.get("number")))
    add("★ 焦点内：range 族的值**没回退** ⟹ 与 number 构成对照",
        rev.get("range") is False)
    add("★ 真空格 = range 族三读数同时不动（值 + past/future + lastCommand）",
        rev.get("range") is False
        and (_c(D, "range", DUP_PAIR[0]).get("stateAfterUndo") or {})
        .get("lastCommand") != "UNDO")

    # ── 族规模（从 776 的 raw 现算） ──
    if RAW776.exists():
        c776 = json.loads(RAW776.read_text(encoding="utf-8"))["rounds"][0]["census"]
        best = {}
        for x in c776:
            if not x.get("selfJustified"):
                continue
            if x.get("id") not in best or (x.get("live") or 0) > \
                    (best[x["id"]].get("live") or 0):
                best[x["id"]] = x
        size = {}
        for x in best.values():
            size[x.get("wantType")] = size.get(x.get("wantType"), 0) + \
                (x.get("live") or 0)
        add("族规模：776 普查每族都非空（逐族自证，防「少测」冒充「不存在」）",
            all((x.get("live") or 0) > 0 for x in best.values()))
        add("族规模：number=27 / range=26（跨上下文取 max，**不是**求和）",
            [size.get("number"), size.get("range")], [27, 26])
        add("族规模：两族合计 53 与 776 README 自述相符", sum(size.values()), 53)
    else:
        add("族规模：776 的 raw 在位（现算，不手抄）", False)

    # ── 产物自洽：runtime-audit 的断言必须与重算值一致 ──
    add("产物：audit.batch=778", a.get("batch"), 778)
    add("产物：audit 记的真空控件数 = range 族规模",
        (a.get("results") or {}).get("vacuumControls"),
        (a.get("familySizes") or {}).get("range", {}).get("count"))
    add("产物：audit 记的独立格数 = %d" % D.get("distinctCells"),
        (a.get("results") or {}).get("distinctCells"), D.get("distinctCells"))
    add("产物：audit 的 D1d 两族成立数 = %d" % nBlocked,
        (a.get("results") or {}).get("delBlockedFamilies"), nBlocked)
    add("产物：audit 的守卫行号 = 静态重算",
        (a.get("static") or {}).get("guardLine"), st.get("guardLine"))
    add("产物：audit 的 Cmd+Z 行号 = 静态重算",
        (a.get("static") or {}).get("undoLine"), st.get("undoLine"))
    return C


# ───────────────── 阴性对照 ─────────────────
def _fp(D):
    """派生指纹：只取**会被判据读到的**字段（R108：比对派生指纹，不是自称）。"""
    out = {}
    for (fam, arm), c in (D.get("cells") or {}).items():
        out["%s/%s" % (fam, arm)] = {
            "mugBack": c.get("mugBack"),
            "mugGoneAfterDel": c.get("mugGoneAfterDel"),
            "pastAfterDel": c.get("pastAfterDel"),
            "valueAfterMutate": (c.get("valueAfterMutate") or {}).get("value"),
            "valueAtUndo": (c.get("valueAtUndo") or {}).get("value"),
            "valueAfterUndo": (c.get("valueAfterUndo") or {}).get("value"),
            "past": (c.get("stateAfterUndo") or {}).get("past"),
            "future": (c.get("stateAfterUndo") or {}).get("future"),
            "last": (c.get("stateAfterUndo") or {}).get("lastCommand"),
        }
    out["_life"] = [
        [{"f": x.get("family"),
          "on": (x.get("onFocus") or {}).get("past"),
          "mu": (x.get("afterMutate") or {}).get("past"),
          "bl": (x.get("afterBlur") or {}).get("past"),
          "g": (x.get("afterBlur") or {}).get("gesture"),
          "c": (x.get("afterBlur") or {}).get("lastCommand")}
         for x in rd] for rd in (D.get("lifecycle") or [])]
    return out


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


def neg_case_static(name, why, mutate_src, kw, D, st, a):
    """静态层的阴性对照：**改源码** ⟹ 证明静态判据不是恒真。
    ★ 本批静态层连踩四次「找到错的」（R128），四次都表现为断言恒假。"""
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
    bp = {c["label"]: c["pass"] for c in
          run_checks(a, copy.deepcopy(st), derive(copy.deepcopy(D.get("_raw"))))}
    flipped = [c["label"] for c in C2
               if bp.get(c["label"], True) and not c["pass"]]
    hits = [f for f in flipped if kw in f]
    return {"name": name, "why": why,
            "mutatedAnything": _st_fp(st2) != _st_fp(st),
            "kwMatchedCount": len(hits), "flipped": flipped,
            "caught": len(hits) == 1, "expectFailOn": kw}


def _st_fp(st):
    return json.dumps(st, ensure_ascii=False, sort_keys=True, default=str)


def _read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def negative_controls(D, st, a):
    out = []

    def _mk(fam, arm, **patch):
        def f(raw):
            n = 0
            for rd in raw["rounds"]:
                for r in rd.get("rows") or []:
                    if r.get("family") == fam and r.get("arm") == arm \
                            and not r.get("FAILED"):
                        for k, v in patch.items():
                            if k in ("valueAfterUndo", "valueAtUndo",
                                     "valueAfterMutate"):
                                r[k] = dict(r.get(k) or {}, value=v)
                            elif k == "stateAfterUndo":
                                r[k] = dict(r.get(k) or {}, **v)
                            else:
                                r[k] = v
                        n += 1
            return raw if n else None
        return f

    def undoable(fam):
        return _mk(fam, "delWhileFocused", mugBack=True,
                   stateAfterUndo={"past": "0", "future": "1",
                                   "lastCommand": "UNDO"})

    def range_native_reverts(raw):
        """★ range/native 的值也回退 ⟹ 「range 的值没回退」必须红。
        ★ 基准取 **`valueOnFocus`**（改动前的值），不能取 `valueAfterMutate`
        —— range/native 的 afterUndo **本来就等于** afterMutate（48→48），
        拿它当「撤回了的值」等于什么都没改（R108 的反面：改了个寂寞）。"""
        n = 0
        for rd in raw["rounds"]:
            for r in rd.get("rows") or []:
                if r.get("family") == "range" and r.get("arm") == "native" \
                        and not r.get("FAILED"):
                    r["valueAfterUndo"] = dict(
                        r.get("valueAfterUndo") or {},
                        value=(r.get("valueOnFocus") or {}).get("value"))
                    n += 1
        return raw if n else None

    def number_native_stuck(raw):
        """★ number/native 也撤不回来 ⟹ 「原生撤销顶上了」必须红。
        ★ 这条是**对称**的另一半：没有它，一个「根本不会撤销任何东西」的
        坏探针能同时骗过 range 与 number 两条判据。"""
        n = 0
        for rd in raw["rounds"]:
            for r in rd.get("rows") or []:
                if r.get("family") == "number" and r.get("arm") == "native" \
                        and not r.get("FAILED"):
                    r["valueAfterUndo"] = dict(
                        r.get("valueAfterUndo") or {},
                        value=(r.get("valueAfterMutate") or {}).get("value"))
                    n += 1
        return raw if n else None

    def break_duplicate(raw):
        """让 native 与 whileFocused 读数不同 ⟹ 「同格自证」必须红。"""
        n = 0
        for rd in raw["rounds"]:
            for r in rd.get("rows") or []:
                if r.get("arm") == "whileFocused" and not r.get("FAILED"):
                    r["mugBack"] = not r.get("mugBack")
                    n += 1
        return raw if n else None

    def blur_past_stays(raw):
        """blur 后 past 不涨 ⟹ 「blur 才提交」必须红。"""
        n = 0
        for rd in raw["rounds"]:
            for x in rd.get("lifecycle") or []:
                if not x.get("FAILED"):
                    x["afterBlur"] = dict(x.get("afterBlur") or {}, past="0")
                    n += 1
        return raw if n else None

    def doc_after_blur_undo_stuck(raw):
        """blur 后撤销不生效 ⟹ 「占掉唯一撤销槽」必须红。"""
        n = 0
        for rd in raw["rounds"]:
            for r in rd.get("rows") or []:
                if r.get("arm") == "docAfterBlur" and not r.get("FAILED"):
                    r["stateAfterUndo"] = dict(
                        r.get("stateAfterUndo") or {},
                        past="1", future="0", lastCommand="GESTURE_COMMIT")
                    n += 1
        return raw if n else None

    def nonexistent(raw):
        for rd in raw["rounds"]:
            for r in rd.get("rows") or []:
                if r.get("__永不匹配__") is None:
                    r["__永不匹配__"] = 1
                    return raw
        return raw

    out.append(neg_case(
        "把 number 族的删除撤销改成「成功了」 ⟹ 「D1d 两族都成立」必须红",
        "★ **对称对照之一**：漏判方向 = 把 27 个 number 控件误当成安全 ⟹ "
        "修法会去动一块本来正常的语义",
        undoable("number"), "D1d 在两族上都成立", D, st, a))
    out.append(neg_case(
        "把 range 族的删除撤销改成「成功了」 ⟹ 「D1d 两族都成立」必须红",
        "★ **对称对照之二**：漏判方向 = 777 那条过度概括被当成正确，"
        "⟹ 授权范围被错误地缩到 26 个",
        undoable("range"), "D1d 在两族上都成立", D, st, a))
    out.append(neg_case(
        "让 range 族在焦点内也撤得回来 ⟹ 「range 的值没回退」必须红",
        "★ 漏判方向 = 26 个滑杆的死键被放过",
        range_native_reverts, "range 族的值**没回退**", D, st, a))
    out.append(neg_case(
        "★ 对称：让 number 族在焦点内也撤不回来 ⟹ 「原生撤销顶上了」必须红",
        "★ 没有这条，一个「根本不会撤销任何东西」的坏探针能同时骗过 "
        "range 与 number 两条判据 ⟹ 真空格就成了恒真",
        number_native_stuck, "原生撤销顶上了", D, st, a))
    out.append(neg_case(
        "让 native 与 whileFocused 读数不同 ⟹ 「同格自证」必须红",
        "证明「8 格里有 1 格重复」这条不是自称；否则格数会多算一格",
        break_duplicate, "同格自证", D, st, a))
    out.append(neg_case(
        "让 blur 后 past 不涨 ⟹ 「blur 才提交」必须红",
        "证明「出路要靠先移开焦点」这条不是恒真",
        blur_past_stays, "改动**要等移开焦点才进历史**", D, st, a))
    out.append(neg_case(
        "让 blur 后撤销不生效 ⟹ 「占掉唯一撤销槽」必须红",
        "★ 漏判方向 = 「守卫是承重墙」这条授权依据被推翻 ⟹ "
        "会给出「整体去掉守卫」这条会引入数据错的建议",
        doc_after_blur_undo_stuck, "占掉了", D, st, a))
    out.append(neg_case(
        "★ 对照自己没改成：写一个 raw 里不存在的字段 ⟹ 不许有判据翻红",
        "mutatedAnything 为 false 时这条对照的结论是空的（R108）",
        nonexistent, "__永不匹配__", D, st, a))

    # ── 静态层的阴性对照（改源码） ──
    def move_guard_after_undo():
        src = _read(DD)
        guard = "      if (isEditable) return;\n"
        if guard not in src:
            return None
        src = src.replace(guard, "")
        anchor = '      if (modifier && event.key.toLowerCase() === "z") {'
        i = src.find(anchor)
        if i < 0:
            return None
        j = src.find("\n", src.find("return;", i)) + 1
        return {DD: src[:j] + guard + src[j:]}

    def kill_pointer_dispatch():
        src = _read(GB_SRC)
        block = ('      if (\n'
                 '        event.currentTarget instanceof HTMLInputElement &&\n'
                 '        event.currentTarget.type === "number"\n'
                 '      ) {\n'
                 '        return;\n'
                 '      }\n')
        if block not in src:
            return None
        return {GB_SRC: src.replace(block, "")}

    def make_is_editable_consult_type():
        src = _read(DD)
        old = '          target.tagName === "INPUT" ||'
        if old not in src:
            return None
        return {DD: src.replace(
            old, '          (target.tagName === "INPUT" &&\n'
                 '            (target as HTMLInputElement).type !== "range") ||')}

    def flip_fov_to_number():
        src = _read(INSP)
        i = src.find('data-director-camera-fov\n')
        if i < 0:
            return None
        head = src.rfind('type="range"', 0, i)
        if head < 0:
            return None
        return {INSP: src[:head] + 'type="number"' + src[head + 12:]}

    out.append(neg_case_static(
        "★ 静态：把守卫挪到 Cmd+Z 分支**之后** ⟹ 「守卫排在之前」必须红",
        "★ 本批静态层连踩四次作用域坑（R128），四次都表现为断言恒假 ⟹ "
        "必须有对照证明静态判据真的在测顺序",
        move_guard_after_undo, "守卫排在 Cmd+Z 分支**之前**", D, st, a))
    out.append(neg_case_static(
        "★ 静态：删掉 `onPointerUp` 的 type 分派 ⟹ 「同仓已有分流先例」必须红",
        "证明「照抄 :82-90 的形状即可」这条授权依据不是恒真",
        kill_pointer_dispatch, "同仓已有分流先例可抄", D, st, a))
    out.append(neg_case_static(
        "★ 静态：让 `isEditable` 去看 `type` ⟹ 「判据不看 type」必须红",
        "★ 漏判方向 = 「两族同分支」这个前提被推翻 ⟹ D1d 的机制解释要重算",
        make_is_editable_consult_type, "判据**不看 `type`**", D, st, a))
    out.append(neg_case_static(
        "★ 静态：把 FOV 那个元素改成 `type=\"number\"` ⟹ "
        "「777 是 n=1 的 range 样本」必须红",
        "证明「777 措辞过度概括」这条追溯不是恒真",
        flip_fov_to_number, "n=1 的 range 样本", D, st, a))
    return out


# ───────────────── 台账 / README ─────────────────
def artifact_checks():
    C = []
    if not LEDGER.exists():
        return [{"label": "台账在位", "pass": False, "got": "缺"}]
    txt = LEDGER.read_text(encoding="utf-8")
    lines = [ln for ln in txt.split("\n") if ln.strip()]
    mine = [ln for ln in lines if re.match(r"^\|\s*Batch\s+778\s*\|", ln)]
    C.append({"label": "台账：Batch 778 恰有一行", "pass": len(mine) == 1,
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
        print("缺少 runtime-audit.json（先跑 mk778audit.py）")
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
        {"batch": 778, "checks": checks, "pass": npass, "total": total,
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
    print("batch 778 %s" % ("通过" if ok else "不通过"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
