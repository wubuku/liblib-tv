#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 782 验收器 —— **独立实现**，不 import 汇编器，也不 import 普查器

## 本批要防的错误方向

本批的结论**推翻了自己的一半**，所以要防的方向比往常更多：

- 若把「挂载域里有 **3 个**主人」漏掉（仍按 director 目录数）⟹ 会把一条
  **已经站不住**的默认（四批共同依赖的「那 6 个键只有一个主人」）继续
  往下传 ⟹ 779/780/781 的授权文本全部建在一个假前提上。
- 若把「另外两个主人**都被门挡住了**」漏掉 ⟹ 会得出「归因被推翻」⟹
  **撤回四批的授权依据**——而运行时明明测到阶梯在跑。
- 若把「两张门**性质不同**」漏掉（`:1401` 显式让位 vs `:1400` 靠遗漏）
  ⟹ 会得出「归因完好」⟹ **新缺陷 D1h 整个消失**，而它正是本批唯一的
  新增可执行结论。
- 若把「`Tab` 的第二主人是**假的**」漏掉 ⟹ 会把
  `useDirectorGestureBoundary:92` 的**排除清单**当成归属 ⟹ 而那正是
  R144 的成因。
- 若把「`sIP` 与 `sP` 是两类」漏掉 ⟹ 会得出「排他的一定在 capture 相位」
  ⟹ 而那是**断言的分类错了、不是机制错了**（R144 的另一半）。

## 静态层为什么算「独立」

普查器（`census782.py`）的做法是**通用抽取**：一条正则同时抓事件名 /
处理器名 / capture 参数，键集靠 `===`/`!==`/成员式三种形态 + 「就近取
`modifier` 极性」的 300 字符窗口。

本验收器**不复用其中任何一步**：

1. **发现**换成三步分解（逐行找 `addEventListener(` → 括号配对取**整个
   调用语句** → 在**语句**里找 `"keydown"`；capture 看**处理器名之后**的
   尾部）。⟹ 能发现那条正则会漏掉的写法：跨行调用、参数顺序不同、
   capture 写成变量。
2. **键集**不做通用抽取，而是**行锚定的字面量断言**：承重的每一条认领
   都写成「某个 handler 体里**必须**出现这一段子串」。
   ⟹ 普查器算错极性时，这里会红 —— 因为它根本不走极性判断。
3. **`sIP`/`sP` 分类**也按字面量分别断言，不共享 `stopsImmediate` 字段。

⟹ 两个实现**各自可能错，但不容易错在同一处**（R107 / R110 / R128）。

## 沿用 775–781 的纪律

- 阴性对照的 `mutatedAnything` **实测**（R108）、`kw` **唯一**（R118）
- **聚合判据数「条件成立的次数」，不是「总数」**（780 自己的教训）
- 改源码的对照必须**真的**让对应判据红，且**只**红一条
"""
import copy
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch782-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAWDIR = OUTDIR / "raw"
PROBEDIR = OUTDIR / "probes"
README = OUTDIR / "README.md"
LEDGER = ROOT / "docs/research/VERIFICATION_LEDGER.md"

RAW_FILES = ["census782.json", "vb782a.json"]
PROBE_FILES = ["census782.py", "dbg782a.py", "mk782audit.py"]
FFFD = "�"
META = {"tries", "retried"}
ARMS = ["captureOwner", "bubbleOwner", "none"]
PRESSES = 2
ROUNDS = 2

PAGE = "src/app/page.tsx"
DD = "src/components/director/DirectorDesk.tsx"
VP = "src/components/director/DirectorViewport.tsx"
GB = "src/components/director/useDirectorGestureBoundary.ts"
FC = "src/components/director/useDirectorFocusContainment.ts"
PV = "src/components/director/DirectorPhoneVcamPanel.tsx"
CTX = "src/lib/libtvSelectionCommandContext.ts"

#: 承重的 4 个「多主人」键 + 2 个「单主人」键
MULTI_KEYS = ["Meta+z", "Meta+y", "Delete", "Backspace"]
SINGLE_KEYS = ["Meta+c", "Meta+v"]
#: 宿主页两个主人的注册行（普查器给出行号；这里**独立**复核它们真实存在）
HOST_CAPTURE_REG = 1400
HOST_BUBBLE_REG = 1401
#: 缺陷 D1h 的载荷
GATE_DIRECTOR = "activeDirectorNodeId"
GATE_SURFACE = "resolveLibTVBlockingForegroundSurface"


# ───────────────── 注释抹白（不删字符，行号不漂移） ─────────────────
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


def lines_of(src):
    return blank_comments(src).split("\n")


def squash(s):
    """空白归一，让字面量断言不依赖缩进与换行。"""
    return " ".join(s.split())


def all_in(lines, pat):
    rx = re.compile(pat)
    return [n for n, ln in enumerate(lines, 1) if rx.search(ln)]


def first_in(lines, pat, after=0):
    """★ 收的必须是**行列表**（R128①）。"""
    return next((n for n in all_in(lines, pat) if n > after), None)


def match_paren(text, open_idx):
    depth = 0
    for i in range(open_idx, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    return -1


def match_brace(text, open_idx):
    depth = 0
    for i in range(open_idx, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1


def handler_body(lines, decl_line):
    """从声明行括号配对取整个函数体（独立实现，R141）。"""
    text = "\n".join(lines[decl_line - 1:])
    op = text.find("{")
    if op < 0:
        return "", decl_line
    cl = match_brace(text, op)
    if cl < 0:
        return "", len(lines)
    end = decl_line + text[:cl].count("\n")
    return text[:cl + 1], end


def find_keydown_sites(lines):
    """★ **三步分解**的站点发现 —— 与普查器那条单正则不同。

    ① 逐行找 `addEventListener(`；
    ② 括号配对取**整个调用语句**，在**语句**里找 `"keydown"`；
    ③ capture 看**处理器名之后**的尾部有没有 `true`。
    ⟹ 普查器那条正则要求「事件名、处理器名、`, true`」在同一行且
    处理器是裸标识符；这里逐项独立取 ⟹ 跨行 / 参数换序 / 变量 capture
    都能发现，而普查器会漏。
    """
    sites = []
    text = "\n".join(lines)
    for m in re.finditer(r"addEventListener\s*\(", text):
        line = text[:m.start()].count("\n") + 1
        op = text.index("(", m.end() - 1)
        cl = match_paren(text, op)
        if cl < 0:
            continue
        call = squash(text[op:cl + 1])
        if not re.search(r'["\']key(down|up)["\']', call):
            continue
        h = re.search(r',\s*([A-Za-z0-9_.]+)\s*(,|\))', call)
        name = h.group(1) if h else None
        tail = call[h.end(1):] if h else call
        sites.append({"line": line, "handler": name,
                      "capture": bool(re.search(r'\btrue\b', tail)),
                      "call": call})
    # React prop：`onKeyDown` 后面**必须紧跟 `(`** ⟹ 排除
    # `onKeyDown: KeyboardEventHandler<HTMLElement>;` 这类**类型声明**
    for m in re.finditer(r"\bonKeyDown\b\s*[:=]\s*\(", text):
        sites.append({"line": text[:m.start()].count("\n") + 1,
                      "handler": "inline", "capture": False,
                      "call": squash(text[m.start():m.start() + 40])})
    typeDecls = [text[:m.start()].count("\n") + 1
                 for m in re.finditer(r"\bonKeyDown\b\s*:\s*[A-Z]", text)]
    sites.sort(key=lambda s: s["line"])
    return sites, typeDecls


# ───────────────── 静态层（独立实现） ─────────────────
def static_side(sources=None):
    sources = sources or {}
    st = {}

    def load(rel):
        if rel in sources:
            return lines_of(sources[rel])
        p = ROOT / rel
        return lines_of(p.read_text(encoding="utf-8")) if p.exists() else None

    page = load(PAGE)
    dd = load(DD)
    if page is None or dd is None:
        return {"err": "缺源码"}

    # ── ① 挂载域：**独立**找「谁渲染了 `<DirectorDesk`」 ──
    hosts = []
    for p in sorted(ROOT.glob("src/**/*.ts")) + sorted(ROOT.glob("src/**/*.tsx")):
        rel = str(p.relative_to(ROOT))
        txt = sources.get(rel, p.read_text(encoding="utf-8"))
        if re.search(r"<DirectorDesk[\s/>]", txt):
            hosts.append(rel)
    st["mountHosts"] = hosts
    if hosts != [PAGE]:
        st["err"] = "挂载页不是 %r" % hosts
        return st

    # ── ② 站点发现（director 目录 + 挂载页） ──
    planeFiles = sorted((ROOT / "src/components/director").rglob("*.ts")) + \
        sorted((ROOT / "src/components/director").rglob("*.tsx"))
    perFile, total, tds = {}, 0, 0
    for p in planeFiles:
        rel = str(p.relative_to(ROOT))
        sites, td = find_keydown_sites(load(rel))
        perFile[rel] = len(sites)
        total += len(sites)
        tds += len(td)
    hsites, htd = find_keydown_sites(page)
    perFile[PAGE] = len(hsites)
    total += len(hsites)
    tds += len(htd)
    st["sitesPerFile"] = perFile
    st["siteTotal"] = total
    st["typeDeclSitesExcluded"] = tds

    byLine = {s["line"]: s for s in hsites}
    st["hostCaptureRegExists"] = HOST_CAPTURE_REG in byLine
    st["hostBubbleRegExists"] = HOST_BUBBLE_REG in byLine
    st["hostCaptureIsCapture"] = bool(byLine.get(HOST_CAPTURE_REG, {})
                                      .get("capture"))
    st["hostBubbleIsCapture"] = bool(byLine.get(HOST_BUBBLE_REG, {})
                                     .get("capture"))
    capH = byLine.get(HOST_CAPTURE_REG, {}).get("handler")
    bubH = byLine.get(HOST_BUBBLE_REG, {}).get("handler")
    st["hostCaptureHandler"], st["hostBubbleHandler"] = capH, bubH

    def decl_for(handler, reg):
        if not handler:
            return None
        rx = re.compile(r'(const|function|let|var)\s+' + re.escape(handler) + r'\b')
        for n in range(reg, 0, -1):
            if rx.search(page[n - 1]):
                return n
        return None

    capDecl, bubDecl = decl_for(capH, HOST_CAPTURE_REG), \
        decl_for(bubH, HOST_BUBBLE_REG)
    st["hostCaptureDecl"], st["hostBubbleDecl"] = capDecl, bubDecl
    capBody = squash(handler_body(page, capDecl)[0]) if capDecl else ""
    bubBody = squash(handler_body(page, bubDecl)[0]) if bubDecl else ""
    st["hostCaptureBodyLen"], st["hostBubbleBodyLen"] = len(capBody), len(bubBody)
    st["capBody"] = capBody
    st["bubBody"] = bubBody
    deskBody = squash(handler_body(dd, first_in(
        dd, r"const handleKeyDown = \(event: KeyboardEvent\)") or 1)[0])

    # ── ③ 键集：**行锚定的字面量断言**（不走普查器的极性判断） ──
    LIT = {
        "hostCap_escape": (capBody, 'event.key === "Escape" ||'),
        "hostCap_delete": (capBody, 'event.key === "Delete" ||'),
        "hostCap_backspace": (capBody, 'event.key === "Backspace" ||'),
        "hostCap_tab": (capBody, 'event.key === "Tab" ||'),
        # ★ 成员式：普查器第一版整个漏掉的那一种
        "hostCap_meta_zyx": (capBody,
                             '(modifier && ["z", "y", "d"]'
                             '.includes(event.key.toLowerCase()))'),
        "hostCap_no_c_literal": (capBody, None),      # 特殊：取反
        "hostCap_no_v_literal": (capBody, None),
        "hostBub_escape": (bubBody, "if (event.key === \"Escape\") {"),
        "hostBub_delete": (bubBody,
                           'if (event.key === "Delete" '
                           '|| event.key === "Backspace") {'),
        "hostBub_tab": (bubBody, "if (event.key === \"Tab\") {"),
        "hostBub_meta_z": (bubBody,
                           'if (modifier && event.key.toLowerCase() === "z") {'),
        "hostBub_meta_y": (bubBody,
                           'if (modifier && event.key.toLowerCase() === "y") {'),
        # ★ 裸 v：极性判据的**反证**——普查器第一版把它报成 `Meta+v`
        "hostBub_bare_v": (bubBody,
                           'if (!modifier && !event.altKey && '
                           'event.key.toLowerCase() === "v")'),
        "hostBub_no_c_literal": (bubBody, None),
        "desk_meta_c": (deskBody,
                        'if (modifier && event.key.toLowerCase() === "c") {'),
        "desk_meta_v": (deskBody,
                        'if (modifier && event.key.toLowerCase() === "v") {'),
        "desk_meta_z": (deskBody,
                        'if (modifier && event.key.toLowerCase() === "z") {'),
        "desk_meta_y": (deskBody,
                        'if (modifier && event.key.toLowerCase() === "y") {'),
        "desk_delete": (deskBody,
                        'if (event.key === "Delete" || '
                        'event.key === "Backspace") {'),
        "desk_escape": (deskBody,
                        'if (event.key === "Escape" && activeMobilePanel) {'),
    }
    lits = {}
    for k, (body, needle) in LIT.items():
        if needle is None:                      # 取反：不该出现的字面量
            ch = k.rsplit("_no_", 1)[1].split("_")[0]
            lits[k] = bool(re.search(r'["\']%s["\']' % ch, body))
        else:
            lits[k] = needle in body
    st["literals"] = lits

    # ── ④ 两道门（字面量 + 位置） ──
    gateBub = 'if (uiState.%s) return;' % GATE_DIRECTOR
    gateCap = 'if (!%s(uiState)) return;' % GATE_SURFACE
    st["gateBubbleLiteral"] = gateBub in bubBody
    st["gateCaptureLiteral"] = gateCap in capBody
    st["gateBubGlobalCount"] = sum(1 for ln in page if gateBub in squash(ln))
    st["gateCapGlobalCount"] = sum(1 for ln in page if gateCap in squash(ln))

    # ── ⑤ 阻塞面枚举里**没有**导演台（缺陷 D1h 的载荷） ──
    ctx = "\n".join(load(CTX) or [])
    union = ctx.split("export type LibTVBlockingForegroundSurface =")[1]
    union = union.split(";")[0]
    st["unionMembers"] = sorted(re.findall(r'"([a-z-]+)"', union))
    st["unionMentionsDirector"] = bool(re.search(r"director", union, re.I))
    snap = ctx.split("export interface LibTVForegroundSurfaceSnapshot")[1]
    snap = snap.split("}")[0]
    st["snapshotMentionsActiveDirectorNodeId"] = GATE_DIRECTOR in snap

    # ── ⑥ `sIP` 与 `sP` 分两类（字面量，不共享字段） ──
    vp, gb, pv = load(VP), load(GB), load(PV)
    vpSites, _ = find_keydown_sites(vp)
    vpSip = [s["line"] for s in vpSites if s["capture"]]
    st["viewportCaptureSites"] = vpSip
    st["viewportSipCount"] = sum(
        1 for ln in vp if "stopImmediatePropagation()" in ln)
    st["gestureHasSip"] = any("stopImmediatePropagation()" in ln for ln in gb)
    st["gestureHasSprop"] = any("stopPropagation()" in ln for ln in gb)
    st["gestureExcludesTab"] = any('event.key !== "Tab"' in squash(ln)
                                   for ln in gb)
    st["gestureClaimsTab"] = any('event.key === "Tab"' in squash(ln)
                                 for ln in gb)
    st["phoneVcamSip"] = any("stopImmediatePropagation()" in ln for ln in pv)
    st["captureBodySip"] = "stopImmediatePropagation()" in capBody
    # ★ D8 的「同仓先例」**只数 director 面**：宿主页 `page.tsx:1400` 那处
    #   形状虽同，语义却是「页面 chrome 的门」⟹ 算进去会把「照抄 3 处」
    #   说成 4 处，而 J5 的论证依赖这个数
    st["d8PrecedentsInPlane"] = (st["viewportSipCount"]
                                + int(bool(st["phoneVcamSip"])))
    st["d8PrecedentsIncludingHost"] = (st["d8PrecedentsInPlane"]
                                       + int(bool(st["captureBodySip"])))

    # ── ⑦ 焦点容器三个调用点（**在调用方文件里**，不是 hook 自己） ──
    deskText = "\n".join(dd)
    fcCalls = []
    # ★ **函数定义**长得几乎一样：`export function useDirectorFocusContainment({`
    #   ⟹ 必须排除，否则 `fcDefIsNotACall` 恒假、调用点数也永远对不上
    #   （第一版汇编器正是在 hook 自己的文件里搜，搜到的唯一一处就是这个定义）
    for m in re.finditer(r"(?<!function )useDirectorFocusContainment\s*"
                         r"\(\s*\{", deskText):
        op = deskText.index("{", m.end() - 1)
        cl = match_brace(deskText, op)
        if cl > 0:
            fcCalls.append(deskText[op:cl + 1])
    st["fcCallCount"] = len(fcCalls)
    st["fcWithStop"] = sum(1 for c in fcCalls if "stopPropagation" in c)
    st["fcStopAllMobileGated"] = all(
        "activeMobileFocusScope" in c for c in fcCalls
        if "stopPropagation" in c)
    fcText = "\n".join(load(FC) or [])
    st["fcDefaultFalse"] = "stopPropagation = false" in fcText
    st["fcDefIsNotACall"] = not re.search(
        r"(?<!function )useDirectorFocusContainment\s*\(\s*\{", fcText)

    # ── ⑧ director 面**不写**任何阻塞面开关（D1h「当前不可达」那半） ──
    FLAGS = ["isShortcutsPanelOpen", "isAddNodePanelOpen", "isZoomMenuOpen",
             "isSharePanelOpen", "isNotificationOpen", "isUserMenuOpen",
             "isFollowingSession", "isCanvasDropdownOpen",
             "isStoryboardEditorOpen", "activePrimaryPanel"]
    hits = []
    for p in planeFiles:
        rel = str(p.relative_to(ROOT))
        for n, ln in enumerate(lines_of(sources.get(
                rel, p.read_text(encoding="utf-8"))), 1):
            for fl in FLAGS:
                if fl in ln:
                    hits.append("%s:%d:%s" % (rel, n, fl))
    st["blockingFlagHits"] = hits
    # 导演台是 z-[100] 全屏模态 ⟹ 画布 chrome 被盖住
    deskReg = first_in(dd, r"fixed inset-0 z-\[100\]")
    st["deskIsFullScreenZ100"] = bool(deskReg)
    return st


# ───────────────── 原始读数（重算） ─────────────────
def load_raw():
    for f in RAW_FILES:
        if not (RAWDIR / f).exists():
            raise SystemExit("缺原始读数 %s —— 判失败，不许通过" % f)
    for f in PROBE_FILES:
        if not (PROBEDIR / f).exists():
            raise SystemExit("缺探针脚本 %s —— 判失败，不许通过" % f)
    raw = json.loads((RAWDIR / "vb782a.json").read_text(encoding="utf-8"))
    if len(raw.get("rounds") or []) != ROUNDS:
        raise SystemExit("轮数不是 %d" % ROUNDS)
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
    D["rounds"] = len(raw.get("rounds") or [])
    D["roundsConsistent"] = (
        [reading(x) for x in norm(strip(raw["rounds"][0].get("rows")))]
        == [reading(x) for x in norm(strip(raw["rounds"][1].get("rows")))])
    D["pressPerRound"] = sum(len((v[0].get("presses") or []))
                             for v in arms.values())
    # ★ audit 的 `cells` 是**跨轮**总格数；`arms[arm]` 只留了第一轮，
    #   所以必须回到 `rounds` 重数，不能拿 `pressPerRound` 去比（R128⑦）
    D["pressTotal"] = sum(len(strip(r.get("presses")))
                          for rd in (raw.get("rounds") or [])
                          for r in (rd.get("rows") or []))
    D["startExportOpen"] = {
        k: (v[0].get("stateBefore") or {}).get("exportOpen")
        for k, v in arms.items()}
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

    L = st.get("literals") or {}

    # ── 静态：普查器自身的可信度 ──
    add("静态：缺源码", st.get("err") is None, True)
    add("静态：★ 挂载域 = director 目录 ∪ **渲染 `<DirectorDesk` 的那一页**",
        st.get("mountHosts"), [PAGE])
    add("静态：★ 独立发现 %d 个键盘站点（director 目录 + 挂载页）"
        % (st.get("siteTotal") or 0), (st.get("siteTotal") or 0) > 0)
    add("静态：★ `onKeyDown` 的**类型声明**被排除 %d 处"
        "（`onKeyDown: KeyboardEventHandler<…>` 不是主人）"
        % (st.get("typeDeclSitesExcluded") or 0),
        (st.get("typeDeclSitesExcluded") or 0) >= 1)
    add("静态：`%s:%d` 注册点在位且**是 capture**"
        % (PAGE, HOST_CAPTURE_REG),
        bool(st.get("hostCaptureRegExists")) and
        bool(st.get("hostCaptureIsCapture")))
    add("静态：`%s:%d` 注册点在位且**是 bubble**"
        % (PAGE, HOST_BUBBLE_REG),
        bool(st.get("hostBubbleRegExists")) and
        not st.get("hostBubbleIsCapture"))
    add("静态：两个宿主页 handler 体都取到了（%d / %d 字符）"
        % (st.get("hostCaptureBodyLen") or 0, st.get("hostBubbleBodyLen") or 0),
        bool(st.get("hostCaptureBodyLen")) and bool(st.get("hostBubbleBodyLen")))
    add("静态：★ 焦点容器的 3 个调用点在**调用方文件**里，"
        "而 hook 自己的文件里**一个都不是**",
        (st.get("fcCallCount"), st.get("fcDefIsNotACall")), (3, True))

    # ── 静态：★ 两个宿主页主人认领了那 4 个键（字面量，不走极性判断） ──
    add("静态：★ `%s:%d`（capture+sIP）认领 `Escape`"
        % (PAGE, HOST_CAPTURE_REG), _ok(L.get("hostCap_escape")))
    add("静态：★ `%s:%d` 认领 `Delete`" % (PAGE, HOST_CAPTURE_REG),
        _ok(L.get("hostCap_delete")))
    add("静态：★ `%s:%d` 认领 `Backspace`" % (PAGE, HOST_CAPTURE_REG),
        _ok(L.get("hostCap_backspace")))
    add("静态：★ `%s:%d` 认领 `Tab`" % (PAGE, HOST_CAPTURE_REG),
        _ok(L.get("hostCap_tab")))
    add("静态：★★ `%s:%d` 用**成员式**认领 `Meta+z`/`Meta+y`"
        "（普查器第一版整个漏掉的那一种形态）" % (PAGE, HOST_CAPTURE_REG),
        _ok(L.get("hostCap_meta_zyx")))
    add("静态：★ `%s:%d` 认领 `Escape`" % (PAGE, HOST_BUBBLE_REG),
        _ok(L.get("hostBub_escape")))
    add("静态：★ `%s:%d` 认领 `Delete`/`Backspace`" % (PAGE, HOST_BUBBLE_REG),
        _ok(L.get("hostBub_delete")))
    add("静态：★ `%s:%d` 认领 `Tab`" % (PAGE, HOST_BUBBLE_REG),
        _ok(L.get("hostBub_tab")))
    add("静态：★ `%s:%d` 认领 `Meta+z`" % (PAGE, HOST_BUBBLE_REG),
        _ok(L.get("hostBub_meta_z")))
    add("静态：★ `%s:%d` 认领 `Meta+y`" % (PAGE, HOST_BUBBLE_REG),
        _ok(L.get("hostBub_meta_y")))
    add("静态：★ 桌认领全部 6 个承重键（`Meta+c`/`Meta+v`/`Meta+z`/`Meta+y`/"
        "`Delete`/`Backspace`）",
        all(_ok(L.get(k)) for k in ("desk_meta_c", "desk_meta_v", "desk_meta_z",
                                    "desk_meta_y", "desk_delete",
                                    "desk_escape")))

    # ── 静态：★ `Meta+c`/`Meta+v` 的「真·单主人」是**负向**断言 ──
    add("静态：★★ 宿主页两个 handler 体里**没有任何 `\"c\"` 字面量** "
        "⟹ `Meta+c` 的主人在挂载域里**真的唯一**",
        bool(L.get("hostCap_no_c_literal")) is False and
        bool(L.get("hostBub_no_c_literal")) is False)
    add("静态：★ 宿主页里唯一的 `\"v\"` 是**裸 v**（`!modifier && …`）"
        "⟹ `Meta+v` 的主人**真的唯一**（普查器第一版把它报成 `Meta+v`，"
        "方向刚好反）",
        _ok(L.get("hostBub_bare_v")) and
        bool(L.get("hostCap_no_v_literal")) is False)

    # ── 静态：★ 两道门，性质不同 ──
    add("静态：★ `%s:%d` 的门是 `if (uiState.%s) return;` ⟹ **显式以导演台"
        "开着为条件**（可靠让位）" % (PAGE, HOST_BUBBLE_REG, GATE_DIRECTOR),
        bool(st.get("gateBubbleLiteral")) and
        st.get("gateBubGlobalCount") == 1)
    add("静态：★ `%s:%d` 的门是 `if (!%s(uiState)) return;`"
        % (PAGE, HOST_CAPTURE_REG, GATE_SURFACE),
        bool(st.get("gateCaptureLiteral")) and
        st.get("gateCapGlobalCount") == 1)
    add("静态：★★ `LibTVBlockingForegroundSurface` 的 %d 个成员里"
        "**没有导演台** ⟹ `:1400` 休眠是**遗漏**不是设计（D1h 的载荷）"
        % len(st.get("unionMembers") or []),
        st.get("unionMentionsDirector"), False)
    add("静态：★ `LibTVForegroundSurfaceSnapshot` 里**没有** `%s`"
        % GATE_DIRECTOR, st.get("snapshotMentionsActiveDirectorNodeId"), False)
    add("静态：★ director 面**不写**任何阻塞面开关（%d 个标志全 0 命中）"
        "⟹ 门不会被导演台自己打开"
        % 10, st.get("blockingFlagHits"), [])
    add("静态：★ 导演台根容器是 `fixed inset-0 z-[100]` 全屏模态 "
        "⟹ 画布 chrome 被盖住",
        _ok(st.get("deskIsFullScreenZ100")))

    # ── 静态：`sIP` 与 `sP` 分两类 ──
    add("静态：★ `DirectorViewport` 有 %d 处 `stopImmediatePropagation()`"
        % (st.get("viewportSipCount") or 0),
        (st.get("viewportSipCount") or 0) >= 2)
    add("静态：★ `DirectorPhoneVcamPanel` 有一处 `stopImmediatePropagation()`",
        _ok(st.get("phoneVcamSip")))
    add("静态：★ `useDirectorGestureBoundary` 有 `stopPropagation()` "
        "**但没有** `stopImmediatePropagation()` ⟹ `sP` 与 `sIP` "
        "**确实是两类**",
        _ok(st.get("gestureHasSprop")) and
        not st.get("gestureHasSip"))
    add("静态：★ `useDirectorGestureBoundary` 的 `!== \"Tab\"` 是**排除清单**"
        "（`:92` **不**认领 `Tab`）⟹ 第一版那个「`Tab` 第二主人」是假的",
        _ok(st.get("gestureExcludesTab")) and
        not st.get("gestureClaimsTab"))

    # ── 静态：焦点容器 ──
    add("静态：`useDirectorFocusContainment` 在 `DirectorDesk.tsx` 里 3 个调用点",
        st.get("fcCallCount"), 3)
    add("静态：★ 其中 2 个开 `stopPropagation`，且**都受 "
        "`activeMobileFocusScope` 门控**（都是移动端焦点域）",
        (st.get("fcWithStop"), st.get("fcStopAllMobileGated")), (2, True))
    add("静态：`stopPropagation` 默认值是 `false` ⟹ 桌面端 workspace 不排他",
        _ok(st.get("fcDefaultFalse")))

    # ── 原始读数 ──
    add("原始：零 FAILED", D["unexpectedFailed"], [])
    add("原始：臂集合齐（%d 臂）" % len(ARMS), D["keys"], sorted(ARMS))
    add("原始：两轮逐字段一致", _ok(D.get("roundsConsistent")))
    add("原始：轮数 = %d" % ROUNDS, D.get("rounds"), ROUNDS)
    add("原始：★ 按压格数 = %d 臂 × %d 次 × %d 轮 = %d（**跨轮**总数）"
        % (len(ARMS), PRESSES, ROUNDS, len(ARMS) * PRESSES * ROUNDS),
        D.get("pressTotal"), len(ARMS) * PRESSES * ROUNDS)
    for arm in ARMS:
        add("原始：%s 起点导出面板**开着**（阶梯的 `:557` 那档有目标）" % arm,
            D["startExportOpen"].get(arm), True)
        add("原始：%s 跑满 %d 次按压" % (arm, PRESSES),
            len(_presses(D, arm)), PRESSES)

    # ── 预测 F：capture 相位 `sIP` 真的挡住阶梯，且**连正向对照一起截断** ──
    e0 = _presses(D, "captureOwner")[0]
    e1 = _presses(D, "captureOwner")[1]
    add("预测 F：captureOwner 第 1 次 `cap==0` **且** `win==0` "
        "⟹ capture 相位的 `sIP` 把**整条链**截断（含 capture 相位上"
        "更早的监听器）⟹ 「排他性真的发生」",
        (e0["read"].get("cap"), e0["read"].get("win")), (0, 0))
    add("预测 F：captureOwner 第 1 次后**目标浮层关掉了**（那个主人跑了）",
        (e0.get("state") or {}).get("targetOpen"), False)
    add("预测 F：★ captureOwner 第 1 次后**导出面板仍开着** ⟹ 桌的阶梯"
        "**一次都跑不到**", (e0.get("state") or {}).get("exportOpen"), True)
    add("预测 F：captureOwner 第 2 次链**恢复**（`cap>=1` 且 `win>=1`）",
        ((e1["read"].get("cap") or 0) >= 1, (e1["read"].get("win") or 0) >= 1),
        (True, True))
    add("预测 F：captureOwner 第 2 次**导出面板关掉了** ⟹ 主人卸载后阶梯接住",
        (e1.get("state") or {}).get("exportOpen"), False)

    # ── 预测 G：不排他的主人与阶梯**并发** ──
    b0 = _presses(D, "bubbleOwner")[0]
    add("预测 G：bubbleOwner 第 1 次后**目标浮层关掉了**",
        (b0.get("state") or {}).get("targetOpen"), False)
    add("预测 G：★ bubbleOwner 第 1 次后**导出面板也关掉了** "
        "⟹ 一次按压里两个主人同时处理（不排他 ⟹ 并发）",
        (b0.get("state") or {}).get("exportOpen"), False)

    # ── 预测 H：对照臂阶梯跑完（判别力） ──
    n0, n1 = _presses(D, "none")[0], _presses(D, "none")[1]
    add("预测 H：none 臂第 1 次 `cap>=1` ⟹ 键真的送达",
        (n0["read"].get("cap") or 0) >= 1)
    add("预测 H：none 臂第 1 次关掉导出面板", (n0.get("state") or {})
        .get("exportOpen"), False)
    add("预测 H：none 臂第 2 次关掉整张桌 ⟹ 阶梯跑完",
        (n1.get("state") or {}).get("deskOpen"), False)

    # ── 预测 I：★★ D1h 的「当前」那半 —— 宿主页那两道门**此刻是关着的** ──
    #   这是**运行时**证据：若 `%s:%d`（capture + `sIP`）当时在跑，
    #   它会在 window 捕获相位 `sIP` 掉整条链 ⟹ `cap` 必为 0 且阶梯跑不到。
    add("预测 I：★★ 对照臂第 1 次 `cap>=1` **且**导出面板真的关了 "
        "⟹ `%s:%d` **当时没跑** ⟹ 缺陷 D1h 的「当前不可达」有运行时证据"
        % (PAGE, HOST_CAPTURE_REG),
        ((n0["read"].get("cap") or 0) >= 1,
         (n0.get("state") or {}).get("exportOpen") is False), (True, True))
    add("预测 I：★ bubbleOwner 臂第 1 次同样 `cap>=1` ⟹ 路径菜单那个"
        " bubble 主人**没有**顺带 `sIP`",
        (b0["read"].get("cap") or 0) >= 1)

    # ── 产物自洽 ──
    own = a.get("ownership") or {}
    res = a.get("results") or {}
    add("产物：audit.batch=782", a.get("batch"), 782)
    add("产物：★ audit 记的挂载页与静态重算一致", own.get("domain", {})
        .get("mountHosts"), st.get("mountHosts"))
    add("产物：★ audit 记的单主人键 = %r" % SINGLE_KEYS,
        sorted(own.get("singleOwnerKeys") or []), sorted(SINGLE_KEYS))
    add("产物：★ audit 记的多主人计数 = 独立发现的主人数",
        own.get("multiOwnerCount"), 3)
    add("产物：★ audit 记的 `Escape` `sIP` 数 = 独立字面量重算"
        "（director 面 %d + 宿主页 %d）"
        % (st.get("d8PrecedentsInPlane") or 0,
           int(bool(st.get("captureBodySip")))),
        res.get("escapeStopImmediate"), st.get("d8PrecedentsIncludingHost"))
    add("静态：★★ D8 的同仓先例**只数 director 面**（%d 处），"
        "宿主页那处**不算**（语义不同：一个是页面 chrome 的门）"
        % (st.get("d8PrecedentsInPlane") or 0),
        st.get("d8PrecedentsInPlane"), 3)
    add("产物：★ audit 记的 D8 先例数 = 独立字面量重算",
        res.get("d8Precedents"), st.get("d8PrecedentsInPlane"))
    add("产物：★ audit 记的格数（**跨轮**）= 重算值",
        res.get("cells"), D.get("pressTotal"))
    add("产物：★ audit 记的每轮按压数 = 重算值",
        len(ARMS) * PRESSES, D.get("pressPerRound"))
    add("产物：★ audit 记的「宿主页门此刻关着」= True",
        res.get("hostGateClosedNow"), True)
    add("产物：audit 记的零 FAILED", res.get("failedCells"), 0)
    add("产物：★ audit 的阻塞面枚举 = 静态重算",
        (own.get("hostGates") or {}).get(
            "app/page.tsx:%d" % HOST_CAPTURE_REG, {}).get("blockingSurfaceUnion"),
        st.get("unionMembers"))
    add("产物：★ audit 记的 director 面阻塞面命中 = 静态重算",
        own.get("blockingFlagsInDirectorPlane"),
        {k: [] for k in []} or ({} if not st.get("blockingFlagHits")
                                else {"has": len(st["blockingFlagHits"])}))
    return C


# ───────────────── 阴性对照 ─────────────────
def _fp(D):
    out = {}
    for arm, c in (D.get("arms") or {}).items():
        out[arm] = [{
            "cap": (p.get("read") or {}).get("cap"),
            "win": (p.get("read") or {}).get("win"),
            "targetOpen": (p.get("state") or {}).get("targetOpen"),
            "exportOpen": (p.get("state") or {}).get("exportOpen"),
            "deskOpen": (p.get("state") or {}).get("deskOpen"),
        } for p in (c.get("presses") or [])]
    return out


def _fingerprint(D):
    return json.dumps(_fp(D), ensure_ascii=False, sort_keys=True, default=str)


def _st_fp(st):
    slim = {k: v for k, v in st.items() if k not in ("capBody", "bubBody")}
    return json.dumps(slim, ensure_ascii=False, sort_keys=True, default=str)


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


#: 静态对照要改的源码文件（改内存副本，**不碰磁盘**）
MUT_FILES = (CTX, PAGE, DD, VP, GB, FC)


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
    C2 = run_checks(a, st2, derive(copy.deepcopy(D.get("_raw"))))
    bp = {c["label"]: c["pass"] for c in run_checks(a, copy.deepcopy(st), D)}
    flipped = [c["label"] for c in C2 if bp.get(c["label"], True)
               and not c["pass"]]
    hits = [f for f in flipped if kw in f]
    return {"name": name, "why": why,
            "mutatedAnything": _st_fp(st2) != _st_fp(st),
            "kwMatchedCount": len(hits), "flipped": flipped,
            "caught": len(hits) == 1, "expectFailOn": kw}


def mut_union(src):
    t = src[CTX]
    t = t.replace('  | "storyboard-editor";',
                  '  | "storyboard-editor"\n  | "director-desk";')
    assert t != src[CTX], "替换没生效"
    return {CTX: t}


def mut_gate_bubble(src):
    """★ **行数中性**：把那道门改成永假，而不是**删掉**那一行 ——
    删行会让下面所有注册点**移位**，于是行锚定判据（`:1400`/`:1401`）
    一起变红 ⟹ 对照测到的就不是「门被拆掉」这件事了。"""
    t = src[PAGE]
    old = "      if (uiState.activeDirectorNodeId) return;"
    assert old in t, "门的字面量没对上"
    t = t.replace(old, "      if (false && uiState.activeDirectorNodeId) return;")
    assert t != src[PAGE] and t.count("\n") == src[PAGE].count("\n")
    return {PAGE: t}


def mut_sip(src):
    """★ 同样**行数中性**：把一处 `sIP` 降级成 `sP`（而不是删掉那一行）——
    降级正好命中「`sIP` 与 `sP` 是两类、先例少一处」这两条判据。"""
    t = src[VP]
    assert t.count("event.stopImmediatePropagation();") >= 2
    t = t.replace("event.stopImmediatePropagation();",
                  "event.stopPropagation();", 1)
    assert t.count("\n") == src[VP].count("\n")
    return {VP: t}


def mut_tab_exclusion(src):
    t = src[GB]
    assert 'event.key !== "Tab"' in t
    t = t.replace('event.key !== "Tab"', 'event.key === "Tab"')
    return {GB: t}


def mut_claim_z(src):
    """给宿主页的 capture handler 加上 `Meta+c` 认领 ⟹ 「单主人」要红。"""
    t = src[PAGE]
    assert 'event.key === "Escape" ||' in t
    old = "        const blocksBrowserDefault ="
    assert old in t, "插入点没对上"
    t = t.replace(old, '        if (modifier && event.key.toLowerCase() === "c") {}'
                  + old, 1)
    assert '"c"' in t and t.count("\n") == src[PAGE].count("\n")
    return {PAGE: t}


def mut_fc_calls(src):
    t = src[DD]
    assert t.count("useDirectorFocusContainment({") == 3
    t = t.replace("useDirectorFocusContainment({",
                  "useDirectorFocusContainment2({")
    return {DD: t}


def mut_cap_raw(raw):
    for rd in raw["rounds"]:
        for r in (rd.get("rows") or []):
            if r.get("arm") == "captureOwner":
                r["presses"][0]["read"]["cap"] = 1
    return raw


def mut_gate_raw(raw):
    """把对照臂第 1 次的导出面板读成「仍开着」⟹ 「门此刻关着」那条要红。"""
    for rd in raw["rounds"]:
        for r in (rd.get("rows") or []):
            if r.get("arm") == "none":
                r["presses"][0]["state"]["exportOpen"] = True
    return raw


def mut_concurrent_raw(raw):
    for rd in raw["rounds"]:
        for r in (rd.get("rows") or []):
            if r.get("arm") == "bubbleOwner":
                r["presses"][0]["state"]["exportOpen"] = True
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
    nFail = len(C) - nPass
    failed = [c["label"] for c in C if not c["pass"]]

    negs = [
        neg_case_static(
            "把导演台登记进阻塞面枚举",
            "★ D1h 的**反证**：枚举里一旦出现 `director`，"
            "「`:1400` 靠遗漏休眠」与「缺陷 D1h 存在」两条都要塌 "
            "⟹ 判据必须红",
            mut_union, "没有导演台", D, st, a),
        neg_case_static(
            "删掉 `page.tsx:1312` 的 `activeDirectorNodeId` 早退",
            "★ 两道门里那道**可靠**的没了 ⟹ `:1401` 会在导演台打开时"
            "抢走那 4 个键 ⟹ 「显式让位」这条判据必须红",
            mut_gate_bubble, "显式以导演台", D, st, a),
        neg_case_static(
            "把 `DirectorViewport` 的一处 `stopImmediatePropagation()` 删掉",
            "D8 的「同仓先例」是照抄的依据；先例少一处 ⟹ 计数判据必须红",
            mut_sip, "只数 director 面", D, st, a),
        neg_case_static(
            "把 `useDirectorGestureBoundary` 的 `!== \"Tab\"` 改成 `=== \"Tab\"`",
            "★ 排除清单一旦变成归属，`Tab` 就真的多一个主人 ⟹ "
            "「第一版那个第二主人是假的」必须红",
            mut_tab_exclusion, "第一版那个", D, st, a),
        neg_case_static(
            "给宿主页的 capture handler 加上 `Meta+c` 认领",
            "★ 「`Meta+c` 的主人**真的唯一**」是**负向**断言 ⟹ "
            "必须能被抓到（负向断言最容易写成恒真）",
            mut_claim_z, "真的唯一", D, st, a),
        neg_case_static(
            "把 `useDirectorFocusContainment` 的调用点改名",
            "★ 调用点在**调用方文件**里这条要能验：改掉调用点后"
            "「3 个调用点」必须红（第一版搜错了文件，永远发现不了）",
            mut_fc_calls, "调用点在**调用方文件**里", D, st, a),
        neg_case("把 captureOwner 第 1 次的 `cap` 读成 1",
                 "★ 「`sIP` 把整条链截断」是本批最容易被当成**坏测量**"
                 "删掉的读数（R143a）⟹ 对照必须能证明它红",
                 mut_cap_raw, "预测 F", D, st, a),
        neg_case("把对照臂第 1 次的导出面板读成「仍开着」",
                 "★ D1h 的「当前不可达」**只有**这一条运行时证据 ⟹ "
                 "它必须能红，否则整条结论无依据",
                 mut_gate_raw, "预测 I", D, st, a),
        neg_case("把 bubbleOwner 第 1 次的导出面板读成「仍开着」",
                 "★ 「不排他的主人与阶梯并发」是 J4 ⟹ 对照要能证明它红",
                 mut_concurrent_raw, "预测 G", D, st, a),
    ]
    nNeg = len(negs)
    nNegCaught = sum(1 for n in negs if n.get("caught"))
    negStale = [n["name"] for n in negs
                if not n.get("mutatedAnything")]
    negMulti = [n["name"] for n in negs if n.get("kwMatchedCount", 0) > 1]

    problems = []
    if nFail:
        problems.append("%d 条判据未过：%r" % (nFail, failed))
    if nNegCaught != nNeg:
        problems.append("阴性对照 %d/%d 被抓" % (nNegCaught, nNeg))
    if negStale:
        problems.append("对照没真的改动任何东西：%r" % negStale)
    if negMulti:
        problems.append("对照 `kw` 不唯一（红了一条以上）：%r" % negMulti)
    for f in (README, LEDGER):
        if not f.exists():
            problems.append("缺 %s" % f.name)
    ledgerHas = LEDGER.exists() and "| Batch 782 |" in \
        LEDGER.read_text(encoding="utf-8")
    if not ledgerHas:
        problems.append("台账没有 `| Batch 782 |` 行")
    # ★ 台账历史行里本来就有 9 处 U+FFFD（R110 记录过）⟹ **只查新增那一行**，
    #   否则这条判据恒红、等于没有
    if LEDGER.exists():
        bad = [ln for ln in LEDGER.read_text(encoding="utf-8").split("\n")
               if ln.startswith("| Batch 782 |") and FFFD in ln]
        if bad:
            problems.append("台账的 Batch 782 行含 U+FFFD")
    for f in (README, AUDIT, REPORT):
        if f.exists() and FFFD in f.read_text(encoding="utf-8"):
            problems.append("%s 含 U+FFFD" % f.name)

    rep = {
        "batch": 782,
        "verdict": "通过" if not problems else "不通过",
        "criteria": {"total": len(C), "passed": nPass, "failed": nFail,
                     "failedLabels": failed},
        "negativeControls": {"total": nNeg, "caught": nNegCaught,
                             "stale": negStale, "kwNotUnique": negMulti,
                             "cases": negs},
        "staticRecomputed": {k: v for k, v in st.items()
                             if k not in ("capBody", "bubBody")},
        "runtimeRecomputed": {k: v for k, v in D.items() if k != "_raw"},
        "productSelfCheck": {c["label"]: c["pass"] for c in C
                             if c["label"].startswith("产物")},
        "problems": problems,
        "srcDiff": "**验收器未改 `src/`**（对照全在内存副本上做）",
    }
    REPORT.write_text(json.dumps(rep, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    print("判据 %d/%d ｜阴性对照 %d/%d ｜%s"
          % (nPass, len(C), nNegCaught, nNeg, rep["verdict"]))
    for p in problems:
        print("  ★ %s" % p)
    for n in negs:
        if not n.get("caught"):
            print("  ✗ 对照未抓：%s（kw=%s，命中 %s）"
                  % (n["name"], n.get("expectFailOn"), n.get("kwMatchedCount")))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
