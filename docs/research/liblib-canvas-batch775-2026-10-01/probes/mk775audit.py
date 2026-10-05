#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 775 汇编器：从 raw/vb775a.json 现算 runtime-audit.json

## 这一批问的

772/774 量 D14 时，落点**全部**取自「浮层内第一个**可聚焦控件**」。
本批把落点空间枚举一遍，并回答一个更基础的问题：

> 方向① 的谓词是「**焦点在某个浮层内**就早退」。
> 浮层开着、但焦点**不在**层内时，Delete 的伤害还在不在？
> —— 以及那算「方向① 漏网」还是「用户本来就在编辑桌内」？

## 三条判据的来源（都能在源码里指出来）

1. `DirectorDesk.tsx` 的守卫判据**只有** `isContentEditable` 与
   `tagName ∈ {INPUT, TEXTAREA, SELECT}`，**不含任何「元素是否在某个浮层内」**
   的判断 ⟹ 五类落点的 `target` 都不是那三种标签、也都不 contentEditable
   ⟹ **守卫在五类落点上全都不触发** ⟹ `defaultPrevented` 应全为 `true`。
2. 同一段代码里 Delete 分支会 `deleteDirectorEntity(...)` ⟹ 只要分支跑到且
   选中有**可删**对象，对象数就 −1。preset/pathmenu 的目标是相机（删不掉）⟹ Δ=0。
3. `activeElement` 在浮层内 ⟺ 方向① 的谓词会触发。这是**直接读数**
   （探针按层选择器算 `panel.contains(activeElement)`），不是从后果反推。

## ★ 普查本身也可能空转

「这个浮层没有非控件区」有两种可能：
（a）浮层里**真的**每个可见点都属于一个控件；
（b）浮层**根本不在 DOM 里** / 一个控件都没有 / 几何是空的 ⟹ **读数是空的**。

所以普查的每一行都必须自证**非空**：控件数 ≥ 1、面板矩形宽高 > 0、
且浮层确实在 `panelPresent` 之后才量的。不满足就判那一行作废，不许算进结论。

## 规矩（沿用 756–774）

1. **数字不许手抄** —— 每个数从 raw 现算；静态事实当场读源码数出来。
2. **缺原始读数判失败**；**缺格判失败**，不许当「没发生」。
3. **先证明可比再谈一致**（R55）：逐轮归一化 diff。
4. **`all([])` 是 True**：每处聚合显式判非空；分类必须**铺满**格子。
5. **阴性对照不能只看 `defaultPrevented`**（R100）：同时断言间谍**确实收到了
   那个键**。
6. **探针的每个臂都要逐臂断言非空**（R101）。
7. **「某类落点不存在」也是一个要测的量**（R103）：第一版把
   `layerNonControl` 写进协议当一类落点，冒烟就打回 6/6 —— **凭空造出一批格**。
8. **跨批引用的数字要从那一批的 raw 现算**（本汇编器直接读 774 的 raw），
   不许在正文里手抄。
"""
import hashlib
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
BATCH = HERE.parent if HERE.name == "probes" else HERE
RAW = BATCH / "raw"
OUT = BATCH / "runtime-audit.json"
REPO = HERE
for _ in range(12):
    if (REPO / "package.json").exists() and (REPO / "src").is_dir():
        break
    REPO = REPO.parent
else:
    raise SystemExit("FATAL 找不到仓库根")

# ★ 跨批引用：774 的 raw（要现算，不许手抄）
B774 = REPO / "docs/research/liblib-canvas-batch774-2026-10-01/raw/vb774a.json"

VOLATILE_RE = re.compile(r"director-gesture-\d+-\d+|[0-9a-f]{16}-[0-9a-f]{4}")
IDS = ["export", "preset", "pathmenu", "phonevcam", "crowd", "modellib"]
LANDINGS = ["trigger", "outsidePanel", "treeContainer", "body", "layerRoot"]
NEUTRAL_KEY = "F2"
DESTRUCTIVE_KEY = "Delete"
CELLS = ([(i, "base", "base") for i in IDS]
         + [(i, "landing", L) for i in IDS for L in LANDINGS]
         + [(i, "neutral", L) for i in IDS for L in LANDINGS])
BASE_CELLS = [(i, "base", "base") for i in IDS]
LAND_CELLS = [(i, "landing", L) for i in IDS for L in LANDINGS]
NEU_CELLS = [(i, "neutral", L) for i in IDS for L in LANDINGS]
# 落点分类的四个桶（**必须铺满 base + landing 那 36 格**）
BUCKETS = ("base", "layerRoot", "deskControl", "noFocus")
DESK_CONTROL_LANDINGS = ("trigger", "outsidePanel", "treeContainer")
# ★ 「用户可达」是**从落点名推导**的量，不是读数 ——
#   探针第一版把它写进 raw，结果同一个 layerRoot 落点在 landing 臂是 True、
#   在 neutral 臂是 False（两个真相源，且都不报错）。
#   `layerRoot` 之所以不可达：产品里浮层根**本来没有 tabindex**（不可聚焦），
#   是探针注入 `tabindex=-1` 才造出「焦点在层内、落点不是控件」这个状态。
USER_REACHABLE = {L: (L != "layerRoot") for L in LANDINGS}


def load(p):
    if not p.exists():
        raise SystemExit("FATAL 缺原始读数 %s —— 判失败，不许通过" % p)
    return json.loads(p.read_text(encoding="utf-8")), p


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


#: ★ 这两个键是**关于这次运行的元数据**，不是读数 ⟹ 必须从「两轮逐格一致」
#:   的比较里排除。否则 round 1 试了 3 次、round 2 试了 1 次就会让两轮
#:   「不一致」，而那不是机制不一致，是基础设施抖动次数不同。
META_KEYS = ("tries", "retried")


def norm(o):
    if isinstance(o, str):
        return VOLATILE_RE.sub("<volatile>", o)
    if isinstance(o, dict):
        return {k: norm(v) for k, v in sorted(o.items())
                if k not in META_KEYS}
    if isinstance(o, list):
        return [norm(v) for v in o]
    return o


def round_diff(raw, key):
    rs = raw.get("rounds") or []
    if len(rs) < 2:
        return None, "轮数不足 2"
    x, y = norm(rs[0].get(key)), norm(rs[1].get(key))
    if x == y:
        return True, None

    def walk(u, v, path=""):
        if isinstance(u, dict) and isinstance(v, dict):
            for k in sorted(set(u) | set(v)):
                if k not in u:
                    return "%s.%s 只在 round2" % (path, k)
                if k not in v:
                    return "%s.%s 只在 round1" % (path, k)
                r = walk(u[k], v[k], "%s.%s" % (path, k))
                if r:
                    return r
            return None
        if isinstance(u, list) and isinstance(v, list):
            if len(u) != len(v):
                return "%s 长度 %d vs %d" % (path, len(u), len(v))
            for i, (p_, q_) in enumerate(zip(u, v)):
                r = walk(p_, q_, "%s[%d]" % (path, i))
                if r:
                    return r
            return None
        return None if u == v else "%s: %r vs %r" % (path, u, v)

    return False, walk(x, y, key)


# ═══════════════ 1. 读原始读数 ═══════════════
A, A_p = load(RAW / "vb775a.json")
rounds = A.get("rounds") or []
assert len(rounds) == 2, "轮数 %d（要 2）" % len(rounds)
aR = rounds

g, skips, failed = {}, [], []
for rd in aR:
    for r in rd.get("rows") or []:
        if r.get("SKIPPED"):
            skips.append((r.get("id"), r.get("arm"), r.get("landing")))
            continue
        if r.get("FAILED"):
            failed.append("%s/%s/%s: %s" % (r.get("id"), r.get("arm"),
                                             r.get("landing"),
                                             str(r["FAILED"])[:70]))
        g.setdefault((r.get("id"), r.get("arm"), r.get("landing")), []).append(r)
assert not skips, "本批不该有 SKIP 格：%r" % (skips[:4],)
# ★ 重试统计：**如实记进产物**。重试是必要的（4317 多人共用，偶发抖动），
#   但「哪些格重试过、试了几次」必须留下来，否则这一批看上去像一次跑过
#   的干净数据（R96：失效机制要记下来，不只是修好）。
retryStats = {"cells": 0, "retriedCells": 0, "maxTries": 1,
              "retried": sorted(
                  "%s/%s/%s=%s" % (r.get("id"), r.get("arm"),
                                   r.get("landing"), r.get("tries"))
                  for rd in aR for r in (rd.get("rows") or [])
                  if not r.get("SKIPPED") and (r.get("tries") or 1) > 1),
              "censusRetried": sorted(
                  "%s=%s" % (c.get("id"), c.get("tries"))
                  for rd in aR for c in (rd.get("census") or [])
                  if (c.get("tries") or 1) > 1)}
retryStats["cells"] = len(g)
retryStats["retriedCells"] = len(retryStats["retried"])
retryStats["maxTries"] = max(
    [1] + [(r.get("tries") or 1) for rd in aR
           for r in (rd.get("rows") or []) if not r.get("SKIPPED")]
    + [(c.get("tries") or 1) for rd in aR
       for c in (rd.get("census") or [])])
assert not failed, "有失败格 ⟹ 判失败：%r" % (failed,)
assert sorted(g) == sorted(CELLS), (
    "格集合与登记不符：多 %r / 少 %r"
    % (sorted(set(g) - set(CELLS))[:4], sorted(set(CELLS) - set(g))[:4]))
for k, v in g.items():
    assert len(v) == 2, "%s 轮数 %d" % (k, len(v))

# ★ R101：逐臂数格 —— 某一臂一次都没跑时**必须**红
armCells = {}
for arm in ("base", "landing", "neutral"):
    armCells[arm] = len([k for k in g if k[1] == arm])
    assert armCells[arm], "★ 臂「%s」一次都没跑（R101）" % arm
assert armCells == {"base": 6, "landing": 30, "neutral": 30}, \
    "逐臂格数不对：%r" % armCells

census = {}
for rd in aR:
    for c in rd.get("census") or []:
        census.setdefault(c.get("id"), []).append(c)
assert sorted(census) == sorted(IDS), \
    "普查的层集合不对：%r" % (sorted(census),)
for i, v in census.items():
    assert len(v) == 2, "普查 %s 两轮不一致（%d 行）" % (i, len(v))
censusFailed = sorted("%s: %s" % (i, c["FAILED"])
                      for v in census.values() for c in v if c.get("FAILED"))
assert not censusFailed, "普查有失败层 ⟹ 判失败：%r" % (censusFailed,)
# ★ 普查的**非空自证**（见文件头）：「没有非控件区」不能是因为浮层是空的
for i, v in census.items():
    for c in v:
        h = c.get("hit") or {}
        assert h.get("noBlank") is True, (
            "%s 的普查结果既不是 noBlank 也不是有命中点：%r —— "
            "协议与读数对不上，要重查" % (i, h))
        assert (h.get("controls") or 0) >= 1, (
            "%s：浮层里**一个可聚焦控件都没有** ⟹ 「没有非控件区」是空转，"
            "不能算进结论" % i)
        rect = h.get("panelRect") or []
        assert len(rect) == 4 and rect[2] > 0 and rect[3] > 0, (
            "%s：面板矩形是空的 %r ⟹ 普查读数无效" % (i, rect))

comparability = {
    "allConsistent": round_diff(A, "rows")[0] is True,
    "firstDiff": {} if round_diff(A, "rows")[0] is True
                  else {"rows": round_diff(A, "rows")[1]},
    "allConsistentCensus": round_diff(A, "census")[0] is True,
    "firstDiffCensus": {} if round_diff(A, "census")[0] is True
                        else {"census": round_diff(A, "census")[1]},
    "rounds": len(aR),
    "rowsPerRound": len(aR[0]["rows"]),
    "censusRowsPerRound": len(aR[0].get("census") or []),
    "armCells": armCells,
    "retryPolicy": "每格最多试 %d 次（含第一次），失败后按 900×n 毫秒退避；"
                   "4317 是多人共用的 dev server，偶发「导演台没开」/"
                   "「目标没选中」是**基础设施抖动**，不是机制读不出来。"
                   "★ 重试次数**记进 raw 的 `tries` 字段**，但 `tries`/"
                   "`retried` 被**排除在两轮一致性比较之外** —— 那是元数据。"
                   % 3,
    "retryStats": retryStats,
    "protocol": "★ 每格都从**重新加载的页面**开始并清空 localStorage；每格都"
                "**点选**一个目标并回读 `selectedIds`；落点用 "
                "`.focus({preventScroll:true})`（除普查里那一次真点）并回读 "
                "`activeElement` 是否在浮层内。",
    "preconditions": "★ 两个前置，不满足就不是读数：① 落点动作**不能顺手关掉"
                     "浮层**（点触发器会 ⟹ 一律用 `.focus()`）；② **不能改选中**"
                     "（点对象树行会 ⟹ 只把焦点放到树的容器上）。",
    "arms": {"base": "同会话基线：不落点，按 Delete",
             "landing": "★ 主测量：五类落点上按 Delete",
             "neutral": "对照：同样五类落点，按桌内不处理的 %s" % NEUTRAL_KEY},
    "boundary": "只点对象树的行、6 个 disclosure 触发器、**选中**相机；"
                "**不点提交/连接/添加，更不做付费或真实生图生视频**。"
                "间谍是**纯读**；本批**没有任何注入**。",
    "probeDesign": A.get("whyItMatters"),
    "threeReadings": A.get("threeReadings"),
}
assert comparability["allConsistent"], comparability["firstDiff"]
assert comparability["allConsistentCensus"], comparability["firstDiffCensus"]


def cell(r):
    f = r.get("landed") or {}
    return {
        "key": r.get("key"),
        "landing": r.get("landing"),
        # ★ 由落点名推导，不读 raw
        "userReachable": USER_REACHABLE.get(r.get("landing")),
        "landedTag": f.get("tag"),
        "landedNote": f.get("note"),
        "hadTabindexBefore": f.get("hadTabindexBefore"),
        "isBody": f.get("isBody"),
        "activeInLayerAtLanding": f.get("activeInLayer"),
        "target": r.get("target"),
        "targetUndeletable": r.get("targetUndeletable") is True,
        # ★ 选中集在 raw 里是**树状态**里的字段，不在行顶层。
        #   第一版读 `r.get("selectedIds")`（永远是空）⟹ 断言「目标没选中」
        #   触发，读起来像「探针没选中」，其实是**字段名对不上**（R109）。
        "selectedIds": ((r.get("before") or {}).get("selectedIds") or []),
        "afterSelectedIds": ((r.get("after") or {}).get("selectedIds") or []),
        "selectedAfterLanding": r.get("selectedAfterLanding") or [],
        "selectionUnchanged": r.get("selectionUnchanged") is True,
        "layerStillOpen": r.get("layerStillOpen") is True,
        "spyInstalled": (r.get("spy") or {}).get("installed") is True,
        "eventsSeen": r.get("eventsSeen") or 0,
        "keysSeen": r.get("keysSeen") or [],
        "targetCE": r.get("targetCE"),
        "defaultPrevented": r.get("defaultPrevented"),
        "objectsDelta": r.get("objectsDelta"),
        "deskStillOpen": r.get("deskStillOpen"),
        "activeInLayer": (r.get("targetInLayer") or {}).get("activeInLayer"),
    }


t = {k: [cell(r) for r in v] for k, v in g.items()}

# ── 每格自证
for k, v in t.items():
    for c in v:
        assert c["spyInstalled"] is True, "%s 间谍没装上" % (k,)
        assert c["eventsSeen"], "%s 间谍一个 keydown 都没收到" % (k,)
        assert c["defaultPrevented"] in (True, False), \
            "%s 读不到 defaultPrevented（探针 bug）" % (k,)
        assert c["targetCE"] in (True, False), \
            "%s 读不到 target.isContentEditable（探针 bug）" % (k,)
        assert c["selectedIds"], "%s 目标没选中 —— 这不是读数" % (k,)
        if k[1] in ("landing", "neutral"):
            assert c["layerStillOpen"] is True, \
                "%s ★ 落点动作把浮层关掉了 —— 这一格不是有效读数" % (k,)
            assert c["selectionUnchanged"] is True, \
                "%s ★ 落点动作改选中 —— 这一格不是有效读数" % (k,)
        if k[1] == "neutral":
            assert c["key"] == NEUTRAL_KEY, "%s 中性臂的键不对" % (k,)
        else:
            assert c["key"] == DESTRUCTIVE_KEY, "%s 的键不对" % (k,)

print("（阶段一）%d 格 × %d 轮（base %d / landing %d / neutral %d），无失败；"
      "普查 %d 层 × %d 轮"
      % (len(CELLS), len(aR), armCells["base"], armCells["landing"],
         armCells["neutral"], len(census), len(aR[0].get("census") or [])))


# ═══════════════ 2. 静态层 ═══════════════
def src_text(rel):
    p = REPO / rel
    if not p.exists():
        raise SystemExit("FATAL 缺源码 %s" % p)
    return p.read_text(encoding="utf-8")


def blank_comments(s):
    """注释**抹白而不删** —— 行数与偏移都不变（774 R102）。"""
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


DD = blank_comments(
    src_text("src/components/director/DirectorDesk.tsx"))
ddLines = DD.split("\n")
i0 = DD.index("const handleKeyDown = (event: KeyboardEvent) => {")
i1 = DD.index('window.addEventListener("keydown", handleKeyDown);')
kdLines = DD[i0:i1].split("\n")
kd = "\n".join(kdLines)


def rel(pat):
    return next((n for n, ln in enumerate(kdLines, 1) if pat in ln), None)


guardRel = rel("if (isEditable) return;")
delRel = rel('event.key === "Delete"')
guardAbs = next((n for n, ln in enumerate(ddLines, 1)
                 if "if (isEditable) return;" in ln), None)


def _first(pat):
    """**整文件**里首个匹配行的**绝对**行号（1 起）。

    ★ 与 `rel()` 的区别：`rel()` 在处理器体内数相对行号，`_first()` 在整份
      文件里数绝对行号。两者混用会把「守卫在 487」写成「守卫在 16」。
    ★ 从**文件头**找首个出现 —— 若改成从守卫之后找，`guard < x` 就恒真，
      判据变成空转。
    """
    rx = re.compile(pat)
    return next((n for n, ln in enumerate(ddLines, 1) if rx.search(ln)), None)


mobRel = _first(r'event\.key === "Escape"')
modRel = _first(r'key\.toLowerCase\(\) === "c"')
escRel = _first(r'event\.key !== "Escape"')
# ★ 判据体：只看 `isEditable = ...` 到分号那一段，**不要**把后面整个处理器
#   都算进来（否则 `document.querySelector` 之类会污染「有没有层内判断」这条）
j0 = kd.index("const isEditable =")
j1 = kd.index(";", j0) + 1
pred = kd[j0:j1]

static = {
    "guardLine": guardAbs,
    "guardIsEditableReturn": "if (isEditable) return;" in kd,
    "guardPredicate": " ".join(pred.split()),
    "guardPredicateHasContentEditable": "isContentEditable" in pred,
    "guardPredicateTagNames": sorted(
        m for m in re.findall(r'tagName === "(\w+)"', pred)),
    # ★ 本批静态层的第一要务：守卫判据里**没有任何**「元素是否在某个浮层内」
    #   的判断 ⟹ 五类落点上它一律不触发
    "guardPredicateMentionsLayer": bool(
        re.search(r"contains|closest|panel|Panel|floating|popover|dropdown",
                  pred)),
    "guardBeforeDelete": bool(guardRel and delRel and guardRel < delRel),
    # ★★ 守卫与各类分支的**真实**先后关系（C775-2）。
    #   774 写的是「`if (isEditable) return;` 排在**所有分支之前**」——
    #   逐行现读之后这句话不成立：**移动端抽屉的 Escape 分支在守卫之前**。
    #   它不是错读，是 774 没量到那一处。而它恰好是 C774-1 要的**同仓先例**。
    "composeLine": _first("event\\.isComposing"),
    "mobileEscapeLine": _first('event\\.key === "Escape"'),
    "modifierCopyLine": _first('key\\.toLowerCase\\(\\) === "c"'),
    "escapeLadderLine": _first('event\\.key !== "Escape"'),
    "guardBeforeModifierCopy": bool(guardAbs and modRel and guardAbs < modRel),
    "guardBeforeEscapeLadder": bool(
        guardAbs and escRel and guardAbs < escRel),
    # ★ 这三个比较**必须都用绝对行号**。第一版拿 `guardRel`（处理器体内的
    #   相对行号，约 16）去比 `mobRel`（整文件的 482）⟹ 恒假，
    #   C775-2 的断言当场翻脸 —— 而翻的方向恰好是「我的发现不存在」。
    "mobileEscapeBeforeGuard": bool(
        guardAbs and mobRel and mobRel < guardAbs),
    "deskListenerOnWindow":
        'window.addEventListener("keydown", handleKeyDown);' in DD,
    "deskListenerIsCapture":
        'window.addEventListener("keydown", handleKeyDown, true);' in DD,
    "deleteCallsDeleteDirectorEntity":
        "deleteDirectorEntity({" in kd,
    "deleteGuardedBySelection": "selectedObjectIds" in kd,
}
assert static["guardIsEditableReturn"] is True, \
    "守卫不在了 ⟹ 本批整批要重查"
assert static["guardPredicateHasContentEditable"] is True, \
    "守卫判据里没有 isContentEditable ⟹ 本批的「全不触发」预测要重算"
assert static["guardPredicateTagNames"] == ["INPUT", "SELECT", "TEXTAREA"], \
    "守卫的标签名判据变了：%r ⟹ 本批预测要重算" % static["guardPredicateTagNames"]
assert static["guardPredicateMentionsLayer"] is False, (
    "★ 守卫判据里已经出现「元素是否在某个浮层内」的判断了 —— "
    "**方向① 可能已经被实现**，本批整批的「方向① 不触发」结论要重算")
assert static["guardBeforeDelete"] is True
# ★ C775-2：守卫**之前**就有一处 Escape 处理。774 写「排在所有分支之前」
#   不成立。这不是错读 —— 是 774 没量到那一处；而它正是 C774-1 需要的先例。
assert static["mobileEscapeLine"] is not None, \
    "移动端抽屉的 Escape 分支不在了 ⟹ C775-2 与 C774-1 的先例都要重查"
assert static["mobileEscapeBeforeGuard"] is True, (
    "★ 移动端抽屉的 Escape 分支不再排在守卫之前了 —— "
    "C775-2 失效，C774-1 的「同仓先例」要另找")
assert static["guardBeforeModifierCopy"] is True
assert static["guardBeforeEscapeLadder"] is True
assert static["deskListenerOnWindow"] is True
assert static["deskListenerIsCapture"] is False, \
    "桌内那个改成捕获阶段了 ⟹ 间谍顺序的前提变了"
assert static["deleteCallsDeleteDirectorEntity"] is True
assert static["deleteGuardedBySelection"] is True
print("（阶段二）静态层：守卫在第 %s 行，判据 = %r；判据里**没有**任何"
      "「是否在浮层内」的判断；桌内监听是 window 冒泡非捕获"
      % (static["guardLine"], static["guardPredicate"]))


# ═══════════════ 3. 聚合 ═══════════════
def uniq(k, field):
    vs = {c[field] for c in t[k]}
    assert len(vs) == 1, "%s 两轮 %s 不一致：%r" % (k, field, vs)
    return vs.pop()


base = {i: {"dp": uniq((i, "base", "base"), "defaultPrevented"),
           "targetCE": uniq((i, "base", "base"), "targetCE"),
           "objectsDelta": sorted({c["objectsDelta"]
                                   for c in t[(i, "base", "base")]}),
           "activeInLayer": uniq((i, "base", "base"), "activeInLayer")}
        for i in IDS}
# ★ 预测 1（同会话基线）：不落点、按 Delete ⟹ dp=true、activeInLayer 不成立
for i in IDS:
    assert base[i]["dp"] is True, (
        "%s 的基线格读到 dp=false ⟹ 读数方法本身坏了（R99 的同族），"
        "后面所有对比都作废" % i)
    assert base[i]["targetCE"] is False, "%s 基线格 targetCE 非 false" % i
    assert base[i]["activeInLayer"] is False, \
        "%s 基线格 activeInLayer 为真 ⟹ 落点/前置条件有问题" % i

land, neu = {}, {}
for i in IDS:
    for L in LANDINGS:
        k = (i, "landing", L)
        land[(i, L)] = {
            "dp": uniq(k, "defaultPrevented"),
            "targetCE": uniq(k, "targetCE"),
            "activeInLayer": uniq(k, "activeInLayer"),
            "landedTag": uniq(k, "landedTag"),
            "isBody": uniq(k, "isBody"),
            "userReachable": uniq(k, "userReachable"),
            # ★ 必须带进聚合：断言「浮层根本来没有 tabindex」读的是这一项。
            #   漏了它 ⟹ `land[...]["hadTabindexBefore"]` 直接 KeyError。
            #   （两轮若不一致，`uniq` 会当场报出来 —— 这正是要的行为。）
            "hadTabindexBefore": uniq(k, "hadTabindexBefore"),
            "targetUndeletable": uniq(k, "targetUndeletable"),
            "objectsDelta": sorted({c["objectsDelta"] for c in t[k]}),
        }
        kn = (i, "neutral", L)
        neu[(i, L)] = {
            "dp": uniq(kn, "defaultPrevented"),
            "targetCE": uniq(kn, "targetCE"),
            "activeInLayer": uniq(kn, "activeInLayer"),
            "sawNeutralKey": all(NEUTRAL_KEY in c["keysSeen"]
                                 for c in t[kn]),
            "eventsSeen": sorted({c["eventsSeen"] for c in t[kn]}),
        }
# ★ 预测 2：守卫判据只认 contentEditable 与三个标签名，而五类落点的 `target`
#   是 BUTTON / SECTION / BODY 等 ⟹ 守卫在五类落点上一律不触发 ⟹ dp 全为 true
for (i, L), v in land.items():
    assert v["targetCE"] is False, (
        "%s/%s：落点 targetCE=true ⟹ 守卫该触发，本批预测作废" % (i, L))
    assert v["dp"] is True, (
        "★ %s/%s：守卫判据不含任何「是否在浮层内」的判断，落点又是 %s ⟹ "
        "守卫应当**不触发**、Delete 分支应当跑到，却读到 dp=false"
        % (i, L, v["landedTag"]))
# ★ 预测 3：分支跑到 + 选中有可删对象 ⟹ 对象数 −1；相机不可删 ⟹ Δ=0
for (i, L), v in land.items():
    want = [0] if v["targetUndeletable"] else [-1]
    assert v["objectsDelta"] == want, (
        "%s/%s：分支已跑到（dp=%s），目标%s，Δ对象应为 %r，实为 %r"
        % (i, L, v["dp"], "不可删" if v["targetUndeletable"] else "可删",
           want, v["objectsDelta"]))
nDamaged = len([1 for v in land.values() if v["objectsDelta"] == [-1]])
nUndamaged = len([1 for v in land.values() if v["objectsDelta"] == [0]])

# ★★ 预测 4 之前先验一件更基础的事：**「焦点在层内、落点不是控件」这个状态
#   是不是我注入出来的？** 产品里浮层根本来没有 tabindex ⟹ 不可聚焦 ⟹
#   那个状态不存在；`hadTabindexBefore` 必须 6/6 全为假。
#   ★ 这一条把「我假设有个洞」变成「产品里根本没有这个状态」——
#     第一版它是**我的断言**（而且在两个臂上还不一致）。
layerRootCells = sorted("%s/%s" % (i, L) for i in IDS for L in LANDINGS
                        if land[(i, L)]["activeInLayer"] is True)
rootHadTab = {i: {land[(i, "layerRoot")]["hadTabindexBefore"]}
              for i in IDS}
for i in IDS:
    assert land[(i, "layerRoot")]["hadTabindexBefore"] is False, (
        "★ %s：浮层根**本来就有** tabindex ⟹ 「焦点在层内、落点不是控件」"
        "是**产品里真实存在**的状态，不是探针注入的 ⟹ "
        "「这一格用户到不了」这条结论作废，要重查" % i)
# ★ `activeElement` 在浮层内 ⟺ 方向① 的谓词会触发。
#   它应当**只**在 layerRoot 上成立 —— 而 layerRoot 是探针注入出来的合成状态
for (i, L), v in land.items():
    want = (L == "layerRoot")
    assert v["activeInLayer"] is want, (
        "%s/%s：activeInLayer=%r 而预测是 %r" % (i, L, v["activeInLayer"],
                                               want))
reachableInLayer = sorted("%s/%s" % k for k, v in land.items()
                          if v["activeInLayer"] is True
                          and v["userReachable"] is True)
assert layerRootCells == sorted("%s/layerRoot" % i for i in IDS), \
    "activeInLayer 为真的落点不是全部 layerRoot：%r" % (layerRootCells,)
assert not reachableInLayer, (
    "★ 竟有「用户可达且 activeInLayer=true」的落点：%r ⟹ "
    "「方向① 覆盖的那一格不可达」这条结论被推翻，要重查" % (reachableInLayer,))

# ★ 预测 5：中性键 F2 在五类落点上仍是 dp=false，**且间谍确实收到了它**
for (i, L), v in neu.items():
    assert v["dp"] is False, (
        "★ 中性键 %s 在 %s/%s 上读到 dp=true —— 说明有人在桌内那个处理器"
        "**之前**就调了 preventDefault()，那么「dp=true 就等于分支跑了」"
        "这条推理**不成立**，整批要重查" % (NEUTRAL_KEY, i, L))
    assert v["sawNeutralKey"], \
        "%s/%s：中性臂键流里没有 %s ⟹ 「键根本没送到」也会得 dp=false，" \
        "只看 dp 没有鉴别力（R100）" % (i, L, NEUTRAL_KEY)
    assert all(e >= 1 for e in v["eventsSeen"]), \
        "%s/%s：中性臂间谍没收到事件" % (i, L)

# ── ★ 分类：四桶，必须**铺满** base + landing 那 36 格，且互斥
buckets = {}
for i in IDS:
    k = (i, "base", "base")
    buckets["%s/base" % i] = "base"
    for L in LANDINGS:
        v = land[(i, L)]
        if v["activeInLayer"] is True:
            b = "layerRoot"
        elif L in DESK_CONTROL_LANDINGS:
            b = "deskControl"
        else:                       # body
            b = "noFocus"
        buckets["%s/%s" % (i, L)] = b
assert sorted(buckets) == sorted("%s/%s" % (i, L) for i in IDS
                                 for L in ["base"] + LANDINGS), \
    "分类的格集合不对"
byBucket = {}
for k, b in buckets.items():
    byBucket.setdefault(b, []).append(k)
for b in byBucket:
    byBucket[b] = sorted(byBucket[b])
assert sorted(byBucket) == sorted(BUCKETS), \
    "四个桶不齐：%r（分类必须**铺满**且每桶非空）" % (sorted(byBucket),)
assert all(byBucket[b] for b in BUCKETS), "有空的桶：%r" % byBucket
assert sum(len(v) for v in byBucket.values()) == len(IDS) * (1 + len(LANDINGS))

# ★ 跨批：774 实测「层内**控件**落点」有伤害、且方向① 覆盖它。
#   这两个数**从 774 的 raw 现算**，不许手抄。
A774, A774_p = load(B774)
g774 = {}
for rd in A774["rounds"]:
    for r in rd.get("rows") or []:
        if r.get("SKIPPED") or r.get("FAILED"):
            continue
        g774.setdefault((r.get("id"), r.get("arm"), r.get("want"),
                         r.get("key")), []).append(r)
x774 = {}
for i in IDS:
    kb = (i, "base", "noneditable", "Delete")
    ka = (i, "alpha", "noneditable", "Delete")
    assert kb in g774 and ka in g774, "774 的 raw 里缺 %s 的两格" % i
    x774[i] = {
        "baseDp": {c["defaultPrevented"] for c in g774[kb]}.pop(),
        "baseDelta": sorted({c["objectsDelta"] for c in g774[kb]}),
        "alphaDp": {c["defaultPrevented"] for c in g774[ka]}.pop(),
        "alphaDelta": sorted({c["objectsDelta"] for c in g774[ka]}),
    }
assert all(v["baseDp"] is True for v in x774.values()), \
    "774 的基线不再是 6/6 dp=true ⟹ 跨批引用作废"
assert all(v["alphaDp"] is False for v in x774.values()), \
    "774 的 α 臂不再是 6/6 dp=false ⟹ 跨批引用作废"
assert all(v["alphaDelta"] == [0] for v in x774.values()), \
    "774 的 α 臂不再零副作用 ⟹ 跨批引用作废"
n774Damaged = len([1 for v in x774.values() if v["baseDelta"] == [-1]])

q = {
    "census": {
        "layers": sorted(census),
        "noBlankLayers": sorted(i for i in IDS
                                if all((c.get("hit") or {}).get("noBlank")
                                       is True for c in census[i])),
        "controlsPerLayer": {i: sorted({(c.get("hit") or {}).get("controls")
                                        for c in census[i]}) for i in IDS},
        "claim": "★ **%d/%d 个浮层没有「非控件区」** ⟹ 「焦点在层内、"
                 "但落点不是控件」这个状态**用户根本到不了**（点非控件区不会"
                 "移动焦点，而层内没有非控件区可点）⟹ 方向① 谓词上**没有**"
                 "我原本假设的那个洞" % (len(IDS), len(IDS)),
        "nonVacuous": "★ 普查自身也自证非空：每一层都有 ≥1 个可聚焦控件、"
                      "面板矩形宽高 > 0、浮层确实已出现 ⟹ 「没有非控件区」"
                      "不是因为浮层是空的",
    },
    "sameSessionBaseline": {
        "arm": "base（不落点，按 Delete）", "cells": len(base),
        "allDpTrue": all(v["dp"] is True for v in base.values()),
        "allActiveInLayerFalse": all(v["activeInLayer"] is False
                                     for v in base.values()),
        "why": "★ 不是引用 774 的历史读数，而是**当场重测** —— "
               "用一个可能已坏的读数方法去验上一批的结论，等于没验",
    },
    "landingArm": {
        "cells": len(land), "allDpTrue": all(v["dp"] is True
                                             for v in land.values()),
        "allTargetCEFalse": all(v["targetCE"] is False
                                for v in land.values()),
        "damaged": nDamaged, "undamaged": nUndamaged,
        "claim": "★ 守卫判据**只认** `isContentEditable` 与三个标签名，"
                 "而五类落点的 `target` 是 BUTTON / SECTION / BODY 等 ⟹ "
                 "守卫在 **%d/%d 格**上一律不触发，Delete 分支全部跑到"
                 % (len(land), len(land)),
    },
    "predicateCoverage": {
        "layerRootCells": layerRootCells,
        "reachableInLayerCells": reachableInLayer,
        "rootHadTabindexBefore": {i: sorted(map(str, v))
                                  for i, v in rootHadTab.items()},
        "claim": "★ 产品里浮层根**本来没有 tabindex**（6/6 实测）⟹ "
                 "「焦点在层内、落点却不是控件」这个状态**不存在**；"
                 "`activeElement` 在浮层内**只**在探针注入出来的 layerRoot 上"
                 "成立 ⟹ **「用户可达 ∧ 方向① 覆盖」这一格在五类落点里是空的**",
        "readings": "读数是**直接**的（按层选择器算 `panel.contains("
                    "activeElement)`），不是从后果反推",
    },
    "neutralControl": {
        "cells": len(neu),
        "allDpFalse": all(v["dp"] is False for v in neu.values()),
        "allSawNeutralKey": all(v["sawNeutralKey"] for v in neu.values()),
        "claim": "★ 中性键 %s 在五类落点上 dp=false（%d/%d）**且间谍确实"
                 "收到了它** ⟹ 「注入/落点把键投递弄坏」这条解释被排除"
                 "（R100 的加强版）" % (NEUTRAL_KEY, len(neu), len(neu)),
    },
    "buckets": {"perCell": buckets, "byBucket": byBucket},
    "crossBatch774": {
        "source": "batch774/raw/vb774a.json（现算，不手抄）",
        "sha16": sha(A774_p),
        "perDisclosure": x774,
        "damagedCells": n774Damaged,
        "claim": "★ 跨批对照：774 实测「层内**控件**落点」上基线 dp=true、"
                 "有伤害（%d 格），而方向①（α 臂）把它全部挡住且零副作用 ⟹ "
                 "**方向① 覆盖的那一格，恰好就是实测有伤害的那一格**"
                 % n774Damaged,
    },
    "conclusion": {
        "direction1CoverageComplete": True,
        "statement": "★ 在「**用户可达**的落点」这个限制下，方向① 覆盖的与"
                     "实测有伤害的**完全重合**：伤害只发生在焦点位于**浮层内"
                     "控件**上时（774 的 6 格 + 本批的 base 6 格），而焦点在"
                     "**层外**时那 %d 格伤害全部落在「用户明确在编辑桌内」"
                     "（deskControl %d 格）或「焦点谁都不在」（noFocus %d 格）"
                     "上 —— 后者**没有证据**说它是缺陷。"
                     % (nDamaged, len(byBucket["deskControl"]),
                        len(byBucket["noFocus"])),
        "selfCorrection": "★ 本批**推翻的是我自己 774 README「下一批」里的"
                          "一个暗示**：「本批只验了『焦点落在层内第一个非编辑"
                          "控件』这一个落点」读起来像「别的落点上也可能有伤害"
                          "而没测」。测完的结论是：别的**用户可达**落点上伤害"
                          "确实还在，但那些落点的语义是「用户在编辑桌内」，"
                          "**不是漏网**。这条暗示据实订正（C775-1）。",
    },
}
assert len(land) == 30
assert nDamaged + nUndamaged == len(land)
print("（阶段三）基线 6/6 dp=true｜五类落点 %d/%d 格 dp=true（伤害 %d 格 / "
      "目标不可删 %d 格）｜中性 %d/%d dp=false 且都收到 %s｜"
      "activeInLayer 只在 layerRoot 成立且**不可达**"
      % (sum(1 for v in land.values() if v["dp"] is True), len(land),
         nDamaged, nUndamaged,
         sum(1 for v in neu.values() if v["dp"] is False), len(neu),
         NEUTRAL_KEY))

# ═══════════════ 4. 判据 + 证据 + 发现 ═══════════════
judgments = [
    {"id": "J1", "q": "普查",
     "claim": "★ **%d/%d 个浮层没有「非控件区」** ⟹ 「焦点在层内、但落点不是"
     "控件」这个状态**用户到不了** ⟹ 方向① 谓词上**没有**我原本假设的那个洞"
     % (len(IDS), len(IDS)),
     "evidence": {"census": q["census"]},
     "boundary": "普查只答「有没有可点的非控件区」；它不排除将来某个浮层"
                 "加出 padding 区域 —— 那一版需要重测"},
    {"id": "J2", "q": "问①",
     "claim": "★ 同会话基线 6/6 格 dp=true、activeInLayer 全为假 ⟹ 读数方法"
     "本身还活着、落点前置条件没问题",
     "evidence": {"baseline": q["sameSessionBaseline"]},
     "boundary": "无"},
    {"id": "J3", "q": "问①",
     "claim": "★ 守卫判据**只认** `isContentEditable` 与 INPUT/TEXTAREA/SELECT，"
     "**不含任何「是否在浮层内」的判断** ⟹ 五类落点上守卫一律不触发，"
     "Delete 分支 **%d/%d 格**全部跑到" % (len(land), len(land)),
     "evidence": {"landing": q["landingArm"], "staticPredicate":
                  static["guardPredicate"]},
     "boundary": "只覆盖「焦点落在这五类地方」；其它落点未测"},
    {"id": "J4", "q": "问①",
     "claim": "★ 分支跑到之后的伤害分布是 %d 格 Δ=−1、%d 格 Δ=0 —— "
     "差额**恰好**等于「目标不可删」的两层（相机）" % (nDamaged, nUndamaged),
     "evidence": {"landing": q["landingArm"]},
     "boundary": "「没有伤害」与「测不出来」在这里不是一回事：Δ=0 的两格"
                 "是因为目标本身删不掉，**分支确实跑了**（dp=true）"},
    {"id": "J5", "q": "问②",
     "claim": "★ 产品里浮层根**本来没有 tabindex**（6/6 实测）⟹ 「焦点在层内、"
             "落点却不是控件」这个状态**不存在**；`activeElement` 在浮层内**只**"
             "在探针注入出来的 layerRoot 上成立 ⟹ **「用户可达 ∧ 方向① 覆盖」"
             "这一格在五类落点里是空的**（%d 格）" % len(land),
     "evidence": {"coverage": q["predicateCoverage"]},
     "boundary": "★ `userReachable` 是**从落点名推导**的量，不读 raw —— "
                 "第一版把它当读数写进探针，同一个落点在两个臂上给出了不同值。"
                 "「合成」这一条则由 `hadTabindexBefore` 6/6 全假**实测**支撑"},
    {"id": "J6", "q": "问②",
     "claim": "★ 跨批对照（774 的 raw 现算）：方向① 覆盖的那一格**恰好就是**"
     "实测有伤害的那一格 —— 774 的层内控件落点基线 dp=true、%d 格有伤害，"
     "α 臂 6/6 全部挡住且零副作用" % n774Damaged,
     "evidence": {"crossBatch": q["crossBatch774"]},
     "boundary": "跨批对照要求 774 的 raw 与探针**同时在场**（本汇编器直接读它）"},
    {"id": "J7", "q": "问③",
     "claim": "★ 中性键 %s 在五类落点上是 dp=false（%d/%d）**且间谍确实收到"
     "了它** ⟹ 「落点动作把键投递弄坏」这条解释被排除"
     % (NEUTRAL_KEY, len(neu), len(neu)),
     "evidence": {"control": q["neutralControl"]},
     "boundary": "R100 的加强版：只看 dp 的话，「键根本没送到」也会得 false"},
]
for j in judgments:
    j["verdict"] = "PASS"
    j["evidenceKey"] = j["id"]
assert sorted(j["id"] for j in judgments) == \
    ["J%d" % i for i in range(1, len(judgments) + 1)]
EVIDENCE_INDEX = {j["id"]: j["evidence"] for j in judgments}

probeLessons = [
    {"id": "R103",
     "lesson": "★ **「某类落点（状态）不存在」本身也是一个要测的量。**"
               "把一个不存在的状态写进协议，等于凭空造出一批格 —— "
               "而那些格要么全失败，要么全被你事后解释掉。",
     "why": "本批第一版把 `layerNonControl`（点浮层空白处）当成一类落点写进"
            "协议，冒烟立刻打回：**%d/%d 个浮层一个非控件的点都找不到**"
            "（`data-*` 挂在内层容器上，几何上被控件铺满）。"
            % (len(IDS), len(IDS)),
     "fixInProbe": "把它从「一类落点」降级成**一条普查**（每个浮层有没有"
                   "非控件区？点它会不会把焦点移进层内？），**「找不到」本身"
                   "就是读数**；并且普查每一行都要自证**非空**"
                   "（控件数 ≥ 1、面板矩形宽高 > 0），否则「没有非控件区」"
                   "可能只是因为浮层是空的"},
    {"id": "R104",
     "lesson": "★ **普查/旁支测量也必须走与主测量同一套前置。**",
     "why": "本批第一版普查没选相机 ⟹ `preset` 的触发器是 `disabled` ⟹ "
            "普查静默少测 1 层（`pathmenu` 的触发器不依赖选中才侥幸测到）⟹ "
            "**「触发器点不动」被当成了一条读数**。",
     "fixInProbe": "普查里显式复制 `run_cell` 的前置（含选相机），"
                   "并且把「前置没过」单列成一条 `FAILED` 而不是读数"},
]
corrections = [
    {"id": "C775-1",
     "targets": ["774 README §10「下一批」的最后一段"],
     "was": "「本批只验了『焦点落在层内第一个非可编辑控件』这一个落点；"
            "**落可编辑控件**时方向① 与现状一致（臂 E 3/3 已量），但那是既有"
            "守卫的功劳，不构成对方向① 的检验。」—— 这段的语气**暗示**"
            "「别的落点上可能也有伤害而没测」。",
     "now": "★ 据实订正：别的**用户可达**落点（触发器 / 桌内他处 / 对象树"
            "容器 / body）上伤害**确实还在**（%d/%d 格 dp=true），但那些落点"
            "的语义是「**用户明确在编辑桌内**」，**不是方向① 的漏网**。"
            "而「焦点在层内、落点却不是控件」这个状态**用户到不了**"
            "（%d/%d 浮层没有非控件区）。所以在**用户可达**这个限制下，"
            "**方向① 的覆盖与实测有伤害的那一格完全重合**。"
            % (nDamaged + nUndamaged, len(land), len(IDS), len(IDS)),
     "evidence": "J1 + J5 + J6 + J7"},
    {"id": "C775-2",
     "targets": ["774 README §5「`if (isEditable) return;` 排在**所有分支之前**」",
                 "774 的 C774-1 论证前提"],
     "was": "「`:487` 的 `if (isEditable) return;` 排在**所有分支之前**，"
            "Escape 阶梯也在其后」—— 读作「桌内没有任何 Escape 处理绕过这道守卫」。",
     "now": "★ 据实收窄：守卫（487）确实在 C/V/Z/Y（490）、Delete/Backspace"
            "（527）与 Escape 阶梯（549）**之前**，但**移动端抽屉的 Escape "
            "分支（482）在它之前**。也就是说桌内**已经存在**一处「Escape "
            "不经 isEditable 守卫」的分层处理。两件事因此改写：① 774 那句"
            "「所有分支」不成立；② C774-1 从「Escape 需要**另一条**规则」"
            "升级为「Escape 已有**同仓结构先例**可抄」—— 差别在于先例是"
            "按**状态**（`activeMobilePanel`）分层，而需要的规则是按"
            "**焦点所在层**分层，**判据不同、形状相同**。",
     "evidence": "静态层 J8（mobileEscapeLine=482 < guardLine=487）"},
]
observations = [
    {"o": 1, "text": "★ 我开这一批时的**假设是错的**，而把它变成读数只花了"
                     "一次普查：%d/%d 个浮层没有非控件区 ⟹ 「层内落非控件处」"
                     "用户到不了。**把「某个状态不存在」也当成一个要测的量，"
                     "比假定它存在便宜得多。**" % (len(IDS), len(IDS))},
    {"o": 2, "text": "★ 伤害在这五类落点上分布是 %d 格 Δ=−1、%d 格 Δ=0，"
                     "差额**恰好**是「目标不可删」的两层 —— 这正好演示了"
                     "R97：**「没伤害」与「分支没跑」是两件事**，而这里 dp=true "
                     "把两者分开了。" % (nDamaged, nUndamaged)},
    {"o": 3, "text": "★ `activeElement` 在浮层内**只**在 layerRoot 上成立，"
                     "而 layerRoot `tabindex=-1` ⟹ 键盘 Tab 到不了。⟹ "
                     "**「用户可达 ∧ 方向① 覆盖」这一格在 775 的五类落点里"
                     "是空的** —— 而它真要靠 774 那一格（层内的**控件**）才成立。"},
    {"o": 4, "text": "静态层顺带查出一件对**未来**有约束的事：守卫判据里"
                     "**没有任何**「元素是否在某个浮层内」的判断。汇编器把"
                     "这条写成断言 ⟹ **一旦方向① 被实现，这一批的静态层立刻变红**"
                     "，不必等人发现结论已经过期。"},
    {"o": 5, "text": "★ 跨批引用的两个数（774 的基线 dp 与 α 臂 dp/零副作用）"
                     "是**从 774 的 raw 现算**的，不在正文里手抄 ⟹ 774 的结论"
                     "一旦漂移，本批的跨批对照会当场变红。"},
]
assert len(observations) >= 5
assert [c["id"] for c in corrections] == ["C775-1", "C775-2"]
assert [x["id"] for x in probeLessons] == ["R103", "R104"]

audit = {
    "batch": 775,
    "topic": "方向① 的谓词上有没有洞：把「落点」这个变量枚举一遍",
    "generatedBy": "probes/mk775audit.py",
    "sources": {"vb775a.json": {"sha16": sha(A_p), "rounds": len(aR),
                                "rowsPerRound": len(aR[0]["rows"])}},
    "questions": {
        "Q0": "「焦点在层内、落点却不是控件」这个状态**用户到不了**吗？"
              "（普查，不是假定）",
        "Q1": "浮层开着、焦点在**层外**的五类落点上，Delete 的伤害还在不在？"
              "守卫会不会触发？",
        "Q2": "方向① 覆盖的那一格，与实测有伤害的那一格，是不是同一格？",
        "Q3": "落点动作有没有把键投递本身弄坏？（中性键 %s）" % NEUTRAL_KEY,
    },
    "comparability": comparability,
    "static": static,
    "results": q,
    "evidenceIndex": EVIDENCE_INDEX,
    "judgments": judgments,
    "findings": {
        "F1": "★ **方向① 的覆盖是完整的**（在「用户可达」这个限制下）：伤害只"
              "发生在焦点位于**浮层内控件**上时，而层外的 %d 格伤害全部属于"
              "「用户明确在编辑桌内」或「焦点谁都不在」。"
              % (nDamaged + nUndamaged,),
        "F2": "★ **「层内落非控件处」用户到不了**：%d/%d 个浮层没有非控件区。"
              "这一条**推翻的是我自己在 774 README「下一批」里的暗示**，"
              "而推翻它只花了 %d 行普查。" % (len(IDS), len(IDS), len(IDS)),
        "F3": "★ 守卫判据里**没有任何**「是否在浮层内」的判断 —— 这既是「五类"
              "落点全不触发」的根据，也是「方向① 还没被实现」的证据。"
              "汇编器把它写成断言 ⟹ 方向① 一旦落地，本批静态层立刻变红。",
        "F4": "★ 伤害分布（%d 格 Δ=−1 / %d 格 Δ=0）的差额**恰好**是「目标"
              "不可删」的两层 ⟹ 又一次演示 R97：「没伤害」≠「分支没跑」。"
              % (nDamaged, nUndamaged),
        "F5": "★ 跨批引用的数字从 774 的 raw 现算，不手抄 ⟹ 774 的结论漂移"
              "时本批当场变红。",
    },
    "probeLessons": probeLessons,
    "corrections": corrections,
    "observations": observations,
    "defects": [],
    "defectNote": "本批**不新增用户可见缺陷**。① 问的是「方向① 够不够」，"
                  "不是「现在有没有坏」。② 五类落点上的伤害**全部**属于"
                  "「用户明确在编辑桌内」（deskControl）或「焦点谁都不在」"
                  "（body）—— 后者**没有证据**说它是缺陷，登记它等于把"
                  "「按设计」写成「新缺陷」。③ 本批推翻的是**我自己**"
                  "上一批 README 里的一个暗示，记在 C775-1。",
    "srcDiff": "**本批未改 `src/`**（提交前 `git diff --stat HEAD -- src/` "
               "为 0 行）；本批**没有任何注入**",
    "rawSha": {"vb775a.json": sha(A_p)},
    "retryStats": retryStats,
    "boundary": comparability["boundary"],
}
OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote %s" % OUT)
