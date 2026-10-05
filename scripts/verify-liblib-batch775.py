#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 775 验收器 —— **独立实现**，不 import 汇编器（`mk775audit.py`）。

## 为什么静态层要「另写一遍」

汇编器和我读的是同一份源码、同一个心智模型。如果我把汇编器的
`static` 直接抄进验收器，那么「汇编器算错了」和「我算错了」会一起错，
验收就变成**自证**。所以这里对守卫那一段**另写一份独立的静态实现**
（连行号都是自己算的），只有两者一致才算真的对上了。

★ 行号纪律（R102）：**注释抹白而不删**。删注释会让行号漂移
（486 → 487），而「守卫在第 487 行」是本批静态层的一条断言。

## 阴性对照的纪律（R100 及其加强版）

每条阴性对照必须同时自证两件事，否则结论是空的：

1. `mutatedAnything` —— 自己**真的改到东西了**吗？
   改了 raw 里**不存在的字段名**时，判据读到的还是原值 ⟹
   「判据不灵」与「对照自己没改成」长得一模一样。
2. `kwMatchedCount == 1` —— 关键词只命中**一条**判据吗？
   命中 0 条 = 测了个不存在的东西；命中 ≥2 条 = 没测出是哪条在把关。

## 跨批引用的数字一律现算

「774 的基线 dp」「774 的 α 臂零副作用」这两个数是**从 774 的 raw 现算**的，
不在这里手抄。774 一旦漂移，本批的跨批对照当场变红。
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch775-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAWDIR = OUTDIR / "raw"
PROBEDIR = OUTDIR / "probes"
README = OUTDIR / "README.md"
LEDGER = ROOT / "docs/research/VERIFICATION_LEDGER.md"
B774 = ROOT / "docs/research/liblib-canvas-batch774-2026-10-01"

RAW_FILES = ["vb775a.json"]
PROBE_FILES = ["dbg775a.py", "mk775audit.py"]
FFFD = "�"

IDS = ["export", "preset", "pathmenu", "phonevcam", "crowd", "modellib"]
LANDINGS = ["trigger", "outsidePanel", "treeContainer", "body", "layerRoot"]
NEUTRAL_KEY = "F2"
#: 目标**不可删**的两层（774 实测 `deleteDirectorEntity` 不吃相机）
CAM_LAYERS = ["preset", "pathmenu"]
CAM = "director-camera-main"

#: 每轮 6（base）+ 30（landing）+ 30（neutral）= 66 格，两轮 132 格
CELLS = ([(i, "base", "base", "Delete") for i in IDS]
         + [(i, arm, lg, ("F2" if arm == "neutral" else "Delete"))
            for arm in ("landing", "neutral") for lg in LANDINGS for i in IDS])

#: 元数据（重试次数）**必须排除**在两轮一致性比较之外：
#: 一次跑干净、一次重试过，机制读数应当相同 —— 把 tries 算进去
#: 会把「基础设施抖过一下」读成「机制不一致」。
META_KEYS = {"tries", "retried"}


# ───────────────── 静态层（独立实现） ─────────────────
def blank_comments(s):
    """把注释**抹白**（保留换行与字符数）而不删 —— 行号不漂移（R102）。

    ★ **只抹注释，不抹字符串字面量**。第一版把 `"INPUT"` 也抹成空白，
      于是 `tagName === "INPUT"` 读不到任何标签、`event.key === "Escape"`
      直接搜不到 ⟹ 静态层静默退化成「什么都没找到」，看起来像通过。
      **把源码抹过头，得到的不是零结果而是假零。**
    """
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


def static_side():
    """对 `DirectorDesk.tsx` 桌内 keydown 处理器的静态读数。"""
    st = {}
    p = ROOT / "src/components/director/DirectorDesk.tsx"
    if not p.exists():
        st["err"] = "找不到 DirectorDesk.tsx"
        return st
    raw = p.read_text(encoding="utf-8")
    src = blank_comments(raw)
    lines = src.split("\n")
    st["fileLines"] = len(lines)

    # ① 守卫本体：`if (isEditable) return;`
    guard = [i + 1 for i, ln in enumerate(lines)
             if re.search(r"if\s*\(\s*isEditable\s*\)\s*return\s*;", ln)]
    st["guardLines"] = guard
    st["guardLine"] = guard[0] if len(guard) == 1 else None
    st["guardCount"] = len(guard)

    # ② 判据：从 `const isEditable =` 起，取到 `;` 结束的那几行
    pred = None
    for i, ln in enumerate(lines):
        if re.search(r"const\s+isEditable\s*=", ln):
            buf = []
            j = i
            while j < len(lines) and j < i + 12:
                buf.append(lines[j].strip())
                if lines[j].rstrip().endswith(";"):
                    break
                j += 1
            pred = " ".join(buf)
            st["predStartLine"] = i + 1
            break
    st["predicate"] = pred
    st["predicateFound"] = pred is not None

    # ③ 判据**恰为**四类，且**不含第五类**
    if pred:
        flat = re.sub(r"\s+", " ", pred)
        st["hasContentEditable"] = "isContentEditable" in flat
        st["tags"] = sorted(set(re.findall(r'tagName === "([A-Z]+)"', flat)))
        st["tagsExpect"] = ["INPUT", "SELECT", "TEXTAREA"]
        st["tagsExact"] = st["tags"] == st["tagsExpect"]
        # ④ ★ 判据里**没有任何**「元素是否在某个浮层内」的判断
        #    —— 这是「方向① 还没被实现」的证据，也是本批静态层的核心断言。
        #    一旦方向① 落地，这条立刻变红（不必等人发现结论已过期）。
        layerwords = ["closest(", "contains(", "panelPresent", "overlay",
                      "popover", "layer", "dialog", "floating", "trigger"]
        st["layerishInPredicate"] = sorted(
            {w for w in layerwords if w.lower() in flat.lower()})

    # ⑤ 守卫和各类分支的**真实**先后关系。
    #    ★ 都从**文件头**找首个出现 —— 若改成「从守卫之后找」，
    #      `gl < v` 就恒真，这条判据变成空转（R107）。
    #    ★ 匹配**调用点** `deleteDirectorEntity(`，不能匹配第 242 行的
    #      `const deleteDirectorEntity = useDirectorStore(` —— 那是 store
    #      订阅，落在守卫之前，会把这条判据读成假（第一版就踩了）。
    def first_line(pat):
        for i, ln in enumerate(lines):
            if re.search(pat, ln):
                return i + 1
        return None

    gl = st.get("guardLine") or 0
    st["composeLine"] = first_line(r"event\.isComposing")
    st["mobileEscapeLine"] = first_line(r'event\.key === "Escape"')
    st["metaCopyLine"] = first_line(r'key\.toLowerCase\(\) === "c"')
    st["deleteLine"] = first_line(r"deleteDirectorEntity\s*\(")
    st["deleteStoreSubLine"] = first_line(
        r"const\s+deleteDirectorEntity\s*=\s*useDirectorStore")
    st["escapeLadderLine"] = first_line(r'event\.key !== "Escape"')
    # ★ 精确的先后关系（现读，不照抄 774 的措辞）：
    #   守卫**之前**：isComposing 早退、移动端抽屉的 Escape 分支
    #   守卫**之后**：C/V/Z/Y 分支、Delete/Backspace、Escape 阶梯
    st["guardBeforeMetaCopy"] = gl < (st["metaCopyLine"] or 0)
    st["guardBeforeDelete"] = gl < (st["deleteLine"] or 0)
    st["guardBeforeEscapeLadder"] = gl < (st["escapeLadderLine"] or 0)
    st["guardBeforeD14All"] = (st["guardBeforeMetaCopy"]
                               and st["guardBeforeDelete"])
    # ★ 已有的**例外**：移动端抽屉的 Escape 分支排在守卫之前。
    #   它是桌内**唯一**一处「Escape 不经过 isEditable 守卫」的处理 ——
    #   ⟹ 正是 C774-1「Escape 阶梯必须分段」所需的**同仓结构先例**。
    st["mobileEscapeBeforeGuard"] = bool(
        st["mobileEscapeLine"] and gl
        and st["mobileEscapeLine"] < gl)
    st["isComposingBeforeGuard"] = bool(
        st["composeLine"] and gl and st["composeLine"] < gl)

    # ⑥ 六个浮层的 panel 选择器在源码里都得找得到。
    #    ★ 语料是**整个 director 组件目录**，不是手挑的几个文件 ——
    #      export 的 panel 在 `DirectorExportPanel.tsx` 里，
    #      第一版只扫了 4 个文件 ⟹ 读成「选择器不存在」（R107）。
    ddir = ROOT / "src/components/director"
    corpus = "\n".join(
        f.read_text(encoding="utf-8") for f in sorted(ddir.glob("*.tsx")))
    sels = {
        "export": "data-director-export-panel",
        "preset": "data-director-camera-preset-panel",
        "pathmenu": "data-director-motion-path-menu",
        "phonevcam": "data-director-phone-vcam-panel",
        "crowd": "data-director-crowd-panel",
        "modellib": "data-director-model-library-panel",
    }
    st["corpusFiles"] = len(list(ddir.glob("*.tsx")))
    st["selectorsFound"] = {k: (v in corpus) for k, v in sels.items()}

    # ⑦ 跨批：774 的 raw 现算
    st["b774"] = cross_batch_774()
    return st


def cross_batch_774():
    """★ 从 774 的 raw **现算**跨批数字，不手抄（单一真相源）。

    ★ 臂名是**现读**的，不是我以为的 `A`/`B`：第一版按 `arm == "A"` /
      `variant == "alpha"` 去数，数出 0 行 —— 而「0 == 0」在断言里
      长得像通过。**跨批读取必须先验非空，再比大小。**
    """
    cb = {"ok": False}
    a = B774 / "raw/vb774a.json"
    b = B774 / "raw/vb774b.json"
    if not (a.exists() and b.exists()):
        cb["err"] = "缺 774 的 raw"
        return cb
    A = json.loads(a.read_text(encoding="utf-8"))
    B = json.loads(b.read_text(encoding="utf-8"))
    rowsA = [r for rd in A["rounds"] for r in (rd.get("rows") or [])
             if not r.get("SKIPPED") and not r.get("FAILED")]
    cb["armsA"] = sorted({r.get("arm") for r in rowsA})
    cb["armsB"] = sorted({r.get("arm") for r in
                          (r for rd in B["rounds"]
                           for r in (rd.get("rows") or []))})
    base = [r for r in rowsA if r.get("arm") == "base"]
    alpha = [r for r in rowsA if r.get("arm") == "alpha"]
    cb["baseN"] = len(base)
    cb["baseDpTrue"] = sum(1 for r in base if r.get("defaultPrevented") is True)
    cb["alphaN"] = len(alpha)
    cb["alphaDpFalse"] = sum(1 for r in alpha
                             if r.get("defaultPrevented") is False)
    cb["alphaZeroObjDelta"] = sum(1 for r in alpha
                                  if (r.get("objectsDelta") or 0) == 0)
    cb["alphaZeroSelDelta"] = sum(1 for r in alpha
                                  if (r.get("selectedDelta") or 0) == 0)
    rowsB = [r for rd in B["rounds"] for r in (rd.get("rows") or [])
             if not r.get("FAILED")]
    cb["bN"] = len(rowsB)
    # ★ 774 的四桶结论**从 raw 现算**：`outcome == "nothing"` 即
    #   「按了 Escape 什么也没发生」= 死键。跨批对照不引用正文措辞。
    cb["bDeadKeyIds"] = sorted({r.get("id") for r in rowsB
                                if r.get("arm") == "alpha"
                                and r.get("outcome") == "nothing"})
    cb["bDeadKeyN"] = sum(1 for r in rowsB
                          if r.get("arm") == "alpha"
                          and r.get("outcome") == "nothing")
    cb["ok"] = True
    return cb


# ───────────────── 原始读数（重算） ─────────────────
def load_raw():
    for f in RAW_FILES:
        if not (RAWDIR / f).exists():
            raise SystemExit("缺原始读数 %s —— 判失败，不许通过" % f)
    for f in PROBE_FILES:
        if not (PROBEDIR / f).exists():
            raise SystemExit("缺探针脚本 %s —— 判失败，不许通过" % f)
    raw = json.loads((RAWDIR / "vb775a.json").read_text(encoding="utf-8"))
    if len(raw.get("rounds") or []) != 2:
        raise SystemExit("轮数不是 2")
    return raw


def strip_meta(rows):
    """去掉 `tries`/`retried` —— 基础设施元数据不是机制读数。"""
    out = []
    for r in rows or []:
        c = {k: v for k, v in r.items() if k not in META_KEYS}
        out.append(c)
    return out


def derive(raw):
    """★ 全部现算，不采信产物里的任何派生字段。

    ★ **对缺格必须健壮**：缺格要变成一条判据红，而不是让验收器崩掉
      —— 崩掉的话，「删掉整臂」这个阴性对照就测不到目标判据，
      反而变成「验收器自己坏了」。
    """
    D = {"badCoverage": [], "censusFailed": [], "census": {},
         "missing": [], "roundsConsistent": None}
    g = {}
    census = {}
    for rd in raw["rounds"]:
        for r in strip_meta(rd.get("rows")):
            g.setdefault((r.get("id"), r.get("arm"), r.get("landing"),
                          r.get("key")), []).append(r)
        for c in strip_meta(rd.get("census")):
            census.setdefault(c.get("id"), []).append(c)
    D["grid"] = sorted(g)
    D["gridN"] = len(g)
    D["missing"] = sorted(set(CELLS) - set(g))
    D["extra"] = sorted(set(g) - set(CELLS))
    if D["missing"] or D["extra"]:
        D["badCoverage"].append(
            "格集合不符：多 %d / 少 %d" % (len(D["extra"]), len(D["missing"])))

    # 两轮一致性（已排除元数据）
    r0 = strip_meta(raw["rounds"][0].get("rows"))
    r1 = strip_meta(raw["rounds"][1].get("rows"))
    D["roundsConsistent"] = (r0 == r1)

    # 普查
    for cid, rows in census.items():
        if not rows or rows[0].get("FAILED"):
            D["censusFailed"].append(cid)
            continue
        h = rows[0].get("hit") or {}
        D["census"][cid] = {
            "noBlank": bool(h.get("noBlank")),
            "controls": h.get("controls"),
            "rect": h.get("panelRect"),
            "rounds": len(rows)}
    D["censusIds"] = sorted(D["census"])

    def one(cell):
        rs = g.get(cell) or []
        return rs[0] if rs else None

    D["base"] = {i: one((i, "base", "base", "Delete")) for i in IDS}
    D["landing"] = {(i, lg): one((i, "landing", lg, "Delete"))
                    for i in IDS for lg in LANDINGS}
    D["neutral"] = {(i, lg): one((i, "neutral", lg, NEUTRAL_KEY))
                    for i in IDS for lg in LANDINGS}
    # 跨批：774 的 layerRoot 格对应「层内控件」那一格
    D["b774"] = None
    return D


# ───────────────── 判据 ─────────────────
def _ok(x):
    return bool(x)


def run_checks(a, st, rw, D):
    C = []

    def add(label, got, want=None):
        """want=None ⟹ 断言 got 为真；否则断言 got == want。"""
        if isinstance(got, bool) and want is None:
            C.append({"label": label, "pass": got, "got": got})
        else:
            C.append({"label": label, "pass": (got == want), "got": got,
                      "want": want})

    # ── 静态层 ──
    add("静态：DirectorDesk.tsx 恰有一处 `if (isEditable) return;`",
        st.get("guardCount"), 1)
    add("静态：守卫在第 487 行（R102：抹白不删，注释不漂行号）",
        st.get("guardLine"), 487)
    add("静态：判据找得到且含 isContentEditable",
        _ok(st.get("predicateFound") and st.get("hasContentEditable")))
    add("静态：判据的标签集合恰为 INPUT/SELECT/TEXTAREA（无第五类）",
        st.get("tags"), ["INPUT", "SELECT", "TEXTAREA"])
    add("静态：★ 判据里**没有任何**「是否在浮层内」的判断"
        "（方向① 未被实现；一旦实现本条立刻变红）",
        st.get("layerishInPredicate"), [])
    add("静态：守卫排在 C/V/Z/Y 分支（490）与 Delete/Backspace（527）**之后**"
        "—— 即 D14 的每一个键都在守卫之下",
        _ok(st.get("guardBeforeD14All")))
    add("静态：守卫排在 Escape 阶梯（549）之前", st.get("guardBeforeEscapeLadder"),
        True)
    add("静态：★ 已记录的**例外**——移动端抽屉的 Escape 分支（482）排在守卫"
        "（487）之前 ⟹ 桌内唯一一处「Escape 不经 isEditable 守卫」的处理，"
        "即 C774-1「Escape 必须分段」的**同仓结构先例**",
        st.get("mobileEscapeBeforeGuard"), True)
    add("静态：isComposing 早退也在守卫之前",
        _ok(st.get("isComposingBeforeGuard")))
    add("静态：6 个浮层 panel 选择器都在源码里",
        _ok(all((st.get("selectorsFound") or {}).values())))

    # ── 覆盖 ──
    add("覆盖：每轮 66 格、两轮全在（缺格/多格皆为红）",
        _ok(not D["badCoverage"]), True)
    add("覆盖：两轮一致（已排除 tries/retried 元数据）",
        D.get("roundsConsistent"), True)

    # ── 普查：★ 本批最要紧的一条 ──
    add("普查：6 个浮层都测到了（无一 FAILED）",
        _ok(not D["censusFailed"]), True)
    add("普查：6 个浮层**都没有非控件区** ⟹ 「层内落非控件处」产品里不存在",
        _ok(len(D["census"]) == len(IDS)
            and all(v["noBlank"] for v in D["census"].values())), True)
    add("普查：★ 每行都自证非空（控件数 > 0 且面板矩形有面积）"
        "—— 防「浮层不在 DOM / 控件数为 0 / 矩形为空」的静默通过",
        _ok(all((v["controls"] or 0) > 0
                and v["rect"] and v["rect"][2] > 0 and v["rect"][3] > 0
                for v in D["census"].values())), True)
    add("普查：★ 浮层根本来就没有 tabindex（6/6 实测 hadTabindexBefore=false）"
        "⟹ layerRoot 那个状态是**探针合成**的",
        _ok(all(((D["landing"].get((i, "layerRoot")) or {})
                 .get("landed") or {}).get("hadTabindexBefore") is False
                for i in IDS)), True)

    # ── 读数方法还活着吗 ──
    add("臂 base：6/6 defaultPrevented=true（读数方法还活着，R99 的同族）",
        sum(1 for i in IDS
            if (D["base"].get(i) or {}).get("defaultPrevented") is True),
        len(IDS))
    add("臂 base：6/6 无 FAILED",
        sum(1 for i in IDS if not (D["base"].get(i) or {}).get("FAILED")),
        len(IDS))

    # ── 主测量：五类落点 × 6 层 = 30 格 ──
    lc = [(i, lg) for i in IDS for lg in LANDINGS]
    add("臂 landing：30/30 defaultPrevented=true"
        "（守卫在这五类落点上**不**触发）",
        sum(1 for k in lc
            if (D["landing"].get(k) or {}).get("defaultPrevented") is True),
        len(lc))
    add("臂 landing：30/30 无 FAILED",
        sum(1 for k in lc if not (D["landing"].get(k) or {}).get("FAILED")),
        len(lc))

    # ── 阴性对照：不能只看 dp，必须同时断言间谍**确实收到了那个键** ──
    add("臂 neutral：30/30 defaultPrevented=false", _ok(all(
        ((D["neutral"].get(k) or {}).get("defaultPrevented")) is False
        for k in lc)), True)
    add("臂 neutral：★ 30/30 键流里**确实含 F2**"
        "（否则 false 只说明键没送到，不说明判据灵）",
        sum(1 for k in lc if NEUTRAL_KEY in
            ((D["neutral"].get(k) or {}).get("keysSeen") or [])),
        len(lc))

    # ── 伤害分布 ──
    dmg = sum(1 for k in lc
              if (D["landing"].get(k) or {}).get("objectsDelta") == -1)
    nod = sum(1 for k in lc
              if (D["landing"].get(k) or {}).get("objectsDelta") == 0)
    add("臂 landing：伤害格 Δ=−1 的有 20 格", dmg, 20)
    add("臂 landing：无伤格 Δ=0 的有 10 格", nod, 10)
    add("臂 landing：★ Δ=0 的 10 格**恰好**是「目标不可删」的两层"
        "（preset/pathmenu × 5 落点）⟹ 「没伤害」≠「分支没跑」（R97）",
        _ok(all((D["landing"].get((i, lg)) or {}).get("objectsDelta") == 0
                for i in CAM_LAYERS for lg in LANDINGS)
            and all((D["landing"].get((i, lg)) or {}).get("objectsDelta") == -1
                    for i in IDS if i not in CAM_LAYERS
                    for lg in LANDINGS)), True)

    # ── 三个读数的组合 ──
    onlyLayerRoot = _ok(all(
        (((D["landing"].get((i, "layerRoot")) or {}).get("targetInLayer") or {})
         .get("activeInLayer")) is True
        for i in IDS)
        and all((((D["landing"].get((i, lg)) or {}).get("targetInLayer") or {})
                 .get("activeInLayer")) is not True
                for i in IDS for lg in LANDINGS if lg != "layerRoot"))
    add("★ activeInLayer **只在 layerRoot 上成立**（其余 24 格为假）"
        "⟹ 「用户可达 ∧ 方向① 覆盖」这一格在这五类落点里是空的", onlyLayerRoot,
        True)

    # ── 两个前置逐格自证 ──
    add("前置①：30 格浮层**仍然开着**（落点动作没顺手关掉它）",
        sum(1 for k in lc
            if (D["landing"].get(k) or {}).get("layerStillOpen") is True),
        len(lc))
    add("前置②：30 格**选中未变**（落点动作没改选中）",
        sum(1 for k in lc
            if (D["landing"].get(k) or {}).get("selectionUnchanged") is True),
        len(lc))

    # ── 单一真相源 ──
    leaked = [k for k in lc
              if "userReachable" in (D["landing"].get(k) or {})]
    add("★ raw 里**没有** userReachable 字段（可达性由落点名推导，单一真相源）",
        _ok(not leaked), True)

    # ── 跨批：现算 ──
    cb = st.get("b774") or {}
    add("跨批：774 的 raw 在位", _ok(cb.get("ok")), True)
    add("跨批：774 臂 A 基线 6/6 dp=true（现算，不手抄）",
        cb.get("baseDpTrue"), cb.get("baseN"))
    add("跨批：774 α 臂 dp 全为 false（现算）",
        cb.get("alphaDpFalse"), cb.get("alphaN"))
    add("跨批：774 α 臂对象数零变化（现算）",
        cb.get("alphaZeroObjDelta"), cb.get("alphaN"))
    add("跨批：774 α 臂选中集零变化（现算）",
        cb.get("alphaZeroSelDelta"), cb.get("alphaN"))
    add("跨批：★ 774 的死键集合现算恰为 {crowd, export}（α 臂 outcome=nothing）"
        "—— 独立复现 774 的四桶结论，不引用其正文",
        cb.get("bDeadKeyIds"), ["crowd", "export"])

    # ── 产物纪律 ──
    add("产物：runtime-audit.json 在位", AUDIT.exists())
    add("产物：README.md 在位", README.exists())
    add("产物：汇编器声明 0 个新缺陷（推翻的是我自己的暗示，记 C775-1）",
        a.get("defects"), [])
    add("产物：更正恰为 C775-1（订正 774 的落点暗示）与 C775-2"
        "（收窄 774 关于守卫位置的措辞）",
        [c.get("id") for c in (a.get("corrections") or [])],
        ["C775-1", "C775-2"])
    add("产物：教训为 R103/R104", [x.get("id") for x in
                                (a.get("probeLessons") or [])],
        ["R103", "R104"])
    add("产物：汇编器与我的静态读数**一致**（独立实现对上了）",
        (a.get("static") or {}).get("guardLine"), st.get("guardLine"))
    return C


# ───────────────── 阴性对照 ─────────────────
def _fingerprint(D):
    """派生结果的规范指纹 —— 用来判断「变异到底有没有改变任何判据输入」。

    ★ 归一化成 JSON 串：tuple 会变成 list，但**值**必须保持可比较。
    """
    def norm(o):
        if isinstance(o, dict):
            # ★ 键可能是 `(layerId, landing)` 这样的**元组**，所以键必须先转字符串
            return {str(k): norm(v) for k, v in o.items()
                    if not (isinstance(k, str) and k.startswith("_"))}
        if isinstance(o, (list, tuple)):
            return [norm(x) for x in o]
        return o
    return json.dumps(norm(D), ensure_ascii=False, sort_keys=True,
                      default=str)


def neg_case(name, why, mutate, kw, D):
    """跑一次「改坏 raw」的对照。

    ★ `mutatedAnything` **实测**，不是自称：比对变异前后的派生指纹。
      改一个判据读不到的字段名 ⟹ 指纹不变 ⟹ `mutatedAnything=False` ⟹
      这条对照的结论是空的，必须自己报出来（R100 的加强版）。
    ★ `kw` 匹配的是**判据标签**，不是 `got` —— 匹配 `got` 会在翻红列表里
      一条都找不到，然后被误读成「判据不灵」（第一版就踩了）。
    """
    import copy
    raw2 = mutate(copy.deepcopy(D.get("_raw")))
    if raw2 is None:
        return {"name": name, "caught": False, "mutatedAnything": False,
                "kwMatchedCount": 0, "why": "变异函数没返回 raw",
                "expectFailOn": kw}
    D2 = derive(raw2)
    st2 = copy.deepcopy(D.get("_st"))
    a2 = copy.deepcopy(D.get("_a"))
    C2 = run_checks(a2, st2, raw2, D2)
    base_pass = {c["label"]: c["pass"] for c in
                 run_checks(a2, st2, D.get("_raw"), derive(D.get("_raw")))}
    flipped = [c["label"] for c in C2
               if base_pass.get(c["label"], True) and not c["pass"]]
    kw_hits = [f for f in flipped if kw in f]
    return {"name": name, "why": why,
            "mutatedAnything": _fingerprint(D2) != _fingerprint(
                derive(D.get("_raw"))),
            "kwMatchedCount": len(kw_hits), "flipped": flipped,
            "caught": len(kw_hits) == 1,
            "expectFailOn": kw}


def negative_controls(D):
    a, st, raw = D.get("_a"), D.get("_st"), D.get("_raw")
    out = []

    def m_objects(raw):
        n = 0
        for rd in raw["rounds"]:
            for r in rd.get("rows") or []:
                if r.get("arm") == "landing" and not r.get("FAILED"):
                    r["objectsDelta"] = 0
                    n += 1
        return raw if n else None

    def m_dp(raw):
        n = 0
        for rd in raw["rounds"]:
            for r in rd.get("rows") or []:
                if r.get("arm") == "landing" and not r.get("FAILED"):
                    r["defaultPrevented"] = False
                    n += 1
        return raw if n else None

    def m_active(raw):
        n = 0
        for rd in raw["rounds"]:
            for r in rd.get("rows") or []:
                if r.get("arm") == "landing" and not r.get("FAILED"):
                    r.setdefault("targetInLayer", {})["activeInLayer"] = True
                    n += 1
        return raw if n else None

    def m_drop_arm(raw):
        n = 0
        for rd in raw["rounds"]:
            rd["rows"] = [r for r in (rd.get("rows") or [])
                          if r.get("arm") != "neutral"]
            n += 1
        return raw if n else None

    def m_census(raw):
        n = 0
        for rd in raw["rounds"]:
            for c in rd.get("census") or []:
                if not c.get("FAILED") and (c.get("hit") or {}).get("noBlank"):
                    c["hit"]["noBlank"] = False
                    n += 1
        return raw if n else None

    def m_nonexistent_field(raw):
        """★ 对照自己没改成：改一个 raw 里**不存在**的字段名。"""
        n = 0
        for rd in raw["rounds"]:
            for r in rd.get("rows") or []:
                r["__不存在的字段__"] = 12345
                n += 1
        return raw if n else None

    out.append(neg_case(
        "把 landing 臂的对象变化全改成 0 ⟹ 伤害分布判据必须红",
        "证明「Δ=−1 的恰好 20 格 / Δ=0 的恰好 10 格」这条判据真有鉴别力",
        m_objects, "伤害格 Δ=−1", D))
    out.append(neg_case(
        "把 landing 臂的 defaultPrevented 全改成 false ⟹ 守卫未触发判据必须红",
        "证明「30/30 dp=true」不是恒真", m_dp, "守卫在这五类落点上", D))
    out.append(neg_case(
        "把 landing 臂的 activeInLayer 全改成 true ⟹ 「只在 layerRoot 成立」必须红",
        "证明「只在 layerRoot 成立」不是恒真", m_active, "activeInLayer", D))
    out.append(neg_case(
        "整臂删掉 neutral ⟹ 覆盖判据必须红，且**验收器不许崩**",
        "证明 derive() 对缺格健壮（崩掉就等于没测到目标判据）；"
        "删一臂会连带让两条 neutral 判据一起红，这是预期的",
        m_drop_arm, "覆盖：每轮", D))
    out.append(neg_case(
        "把普查的 noBlank 全翻成 false ⟹ 「6/6 没有非控件区」必须红",
        "证明普查结论不是恒真", m_census, "没有非控件区", D))
    out.append(neg_case(
        "★ 对照自己没改成：改一个 raw 里不存在的字段名 ⟹ **不许**有判据翻红",
        "区分「判据不灵」与「对照自己没改成」；mutatedAnything 为 false 时"
        "这条对照的结论是空的", m_nonexistent_field, "__永不匹配__", D))
    return out


# ───────────────── 产物纪律（台账/README） ─────────────────
def artifact_checks():
    C = []
    if not LEDGER.exists():
        return [{"label": "台账在位", "pass": False, "got": "缺"}]
    txt = LEDGER.read_text(encoding="utf-8")
    lines = [ln for ln in txt.split("\n") if ln.strip()]
    # ★ 台账的真实行首是 `| Batch 775 |`（带 "Batch" 字样）。
    #   注意它**不会**被 pre-commit 的 `added_batch_numbers()` 认成批次号
    #   —— 那个正则要求 `+| <数字> |`，中间没有 "Batch"。
    #   所以本树的台账行不参与钩子的批次登记，774 能过钩子也是这个原因。
    #   （而 README/探针里**必须**避开裸数字行首，见下面那条。）
    mine = [ln for ln in lines if re.match(r"^\|\s*Batch\s+775\s*\|", ln)]
    C.append({"label": "台账：Batch 775 恰有一行", "pass": len(mine) == 1,
              "got": len(mine)})
    if mine:
        ln = mine[0]
        C.append({"label": "台账：该行无 U+FFFD", "pass": FFFD not in ln,
                  "got": ln.count(FFFD)})
        C.append({"label": "台账：该行恰 4 个竖线（3 列）",
                  "pass": ln.count("|") == 4, "got": ln.count("|")})
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
        print("缺少 runtime-audit.json（先跑 mk775audit.py）")
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
        D["_raw"], D["_st"], D["_a"] = raw, st, a
        checks = run_checks(a, st, raw, D) + artifact_checks()
        neg = negative_controls(D)

    kw_bad = [n["name"] for n in neg if n.get("kwMatchedCount") != 1]
    inert = [n["name"] for n in neg if n.get("mutatedAnything") is False]
    npass = sum(1 for c in checks if c["pass"])
    total = len(checks)
    neg_ok = sum(1 for n in neg
                 if n.get("mutatedAnything") is False
                 or (n["caught"] and n.get("kwMatchedCount") == 1))
    ok = npass == total and neg_ok == len(neg)
    REPORT.write_text(json.dumps(
        {"batch": 775, "checks": checks, "pass": npass, "total": total,
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
            print("  ✗ %s 命中 %s 条判据（期望恰好 1）"
                  % (n["name"], n.get("kwMatchedCount")))
        elif not n["caught"]:
            print("  ✗ 漏放：%s  翻红=%r" % (n["name"], n.get("flipped")[:4]))
    print("batch 775 %s" % ("通过" if ok else "不通过"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
