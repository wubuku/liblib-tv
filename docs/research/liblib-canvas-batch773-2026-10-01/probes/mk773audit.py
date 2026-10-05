#!/usr/bin/env python3
"""batch 773 汇编器：从 raw/vb773a.json 现算 runtime-audit.json

## 这一批问的

772 有一个缺口：**preset / 路径菜单的 4 个 Delete 格「结构上不可判」** ——
它们必须选中主机位才能开，而对照格实测相机删不掉，于是「对象没少」既可能是
「分支没跑」，也可能是「跑了但目标删不掉」。772 的读法是**靠副作用反推**。

本批换**直接读数**：`DirectorDesk.tsx` 里那个处理器**每走到一个分支就调一次
`event.preventDefault()`**（`:483` / `:491` / `:502` / `:507` / `:513` /
`:526` / `:541` / `:550`）。所以在 **window 冒泡阶段、注册得比它更晚**的
监听器读到的 `event.defaultPrevented`，就是「那个分支真的跑了」的直接证据。

## 断言编码的是**预测**，不是观测

本汇编器里每条 `assert` 编码的都是**从源码逐行推出的**结论
（`defaultPrevented == 非 isEditable`，中性键恒 false），不是「跑一遍看看
是什么」。断言炸了就是**机制读错了**，是要去查的发现，不是要改的断言。

## 规矩（沿用 756–772）

1. **数字不许手抄** —— 每个数从 raw 现算；静态事实当场读源码数出来。
2. **缺原始读数判失败**。
3. **`findings[k] == judgments[i].evidence`**，写盘前断言，验收器再查一遍。
4. **先证明可比再谈一致**（R55）：逐轮归一化 diff。
5. **`all([])` 是 True**：每处聚合显式判非空；分类必须**铺满**格子。
6. **探针的读数方法本身要有对照**（R86）：中性键 `F2` 是桌内**不处理**的键，
   间谍必须读到 `defaultPrevented=false` —— 否则「读到 true 就等于分支跑了」
   这条推理不成立。
7. **静态断言的方向要写对**（R92）。
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

VOLATILE_RE = re.compile(r"director-gesture-\d+-\d+|[0-9a-f]{16}-[0-9a-f]{4}")
IDS = ["export", "preset", "pathmenu", "phonevcam", "crowd", "modellib"]
WANTS = ["noneditable", "editable", "neutral"]
KEYS = ["Delete", "Backspace", "Meta+z", "Meta+c", "Meta+v"]
NEUTRAL_KEY = "F2"
HAS_EDITABLE = {"export", "crowd", "modellib"}
CAM_ONLY = {"preset", "pathmenu"}
# ★ 中性臂只按 **一个** 键（桌内明确不处理的那个）跑，不是五个 ——
#   第一版把 CELLS 按 KEYS 展开成 75 格，结果与真实网格对不上。
RUN_CELLS = ([(i, "noneditable", k) for i in IDS for k in KEYS]
             + [(i, "editable", k) for i in sorted(HAS_EDITABLE) for k in KEYS]
             + [(i, "neutral", NEUTRAL_KEY) for i in IDS])
CELLS = RUN_CELLS
SKIP_LAYERS = sorted(set(IDS) - HAS_EDITABLE)


def load(name, base=None):
    p = (base or RAW) / name
    if not p.exists():
        raise SystemExit("FATAL 缺原始读数 %s —— 判失败，不许通过" % p)
    return json.loads(p.read_text(encoding="utf-8")), p


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def norm(o):
    if isinstance(o, str):
        return VOLATILE_RE.sub("<volatile>", o)
    if isinstance(o, dict):
        return {k: norm(v) for k, v in sorted(o.items())}
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
A, A_p = load("vb773a.json")
B, B_p = load("vb773b.json")
for nm, raw in (("773a", A), ("773b", B)):
    rs = raw.get("rounds") or []
    assert len(rs) == 2, "%s 轮数 %d" % (nm, len(rs))
aR, bR = A["rounds"], B["rounds"]


def grid(raw, neutral_keyed):
    g, skip = {}, set()
    for rd in raw["rounds"]:
        for r in rd.get("rows") or []:
            if r.get("SKIPPED"):
                skip.add((r.get("id"), r.get("want")))
                continue
            k = (r.get("id"), r.get("want"),
                 NEUTRAL_KEY if neutral_keyed else r.get("key"))
            g.setdefault(k, []).append(r)
    return g, skip


ga, sa = grid(A, False)
gb, sb = grid(B, True)
# 探针 a 的中性臂一次都没跑（它的 `for want in (...)` 补丁没落进文件）
assert not [k for k in ga if k[1] == "neutral"], \
    "探针 a 竟有中性臂 —— 合并规则要重算"
assert sa == {(i, "editable") for i in SKIP_LAYERS}, \
    "探针 a 的结构性 SKIP 集合不对：%r" % (sorted(sa),)
assert not sb, "探针 b 不该有 SKIP 格"

missing = [k for k in CELLS if k not in ga and k not in gb]
assert not missing, "缺格 %r —— 判失败，不许当「没发生」" % (missing,)
failed = sorted({"%s/%s/%s" % k for k, v in list(ga.items()) + list(gb.items())
                 for r in v if r.get("FAILED")})
assert not failed, "有失败格 %r —— 判失败" % (failed,)
for k, v in list(ga.items()) + list(gb.items()):
    assert len(v) == 2, "%s 轮数 %d" % (k, len(v))

g = {}
provenance = {}
for k, v in ga.items():
    g[k] = v
    provenance["%s/%s/%s" % k] = "773a"
for k, v in gb.items():
    g[k] = v
    provenance["%s/%s/%s" % k] = "773b"
assert sorted(g) == sorted(CELLS), "合并后格集合不对"
provA = sum(1 for v in provenance.values() if v == "773a")
provB = sum(1 for v in provenance.values() if v == "773b")
_nA = len(aR[0]["rows"])          # 773a 每轮行数（局部量，别在 comparability
_nSkip = len(sa)                  #  内部自引用）

comparability = {
    "allConsistent773a": round_diff(A, "rows")[0] is True,
    "allConsistent773b": round_diff(B, "rows")[0] is True,
    "firstDiff773a": {} if round_diff(A, "rows")[0] is True
                     else {"rows": round_diff(A, "rows")[1]},
    "firstDiff773b": {} if round_diff(B, "rows")[0] is True
                     else {"rows": round_diff(B, "rows")[1]},
    "rounds": len(aR),
    "cellsPerRound773a": len(aR[0]["rows"]),
    "cellsPerRound773b": len(bR[0]["rows"]),
    "mergedCells": len(g),
    "cellsFrom773a": provA,
    "cellsFrom773b": provB,
    "provenance": provenance,
    "protocol": "★ 每格都从**重新加载的页面**开始并清空 localStorage；"
                "每格都**点选**一个目标并回读 `selectedIds`。",
    "spyDesign": A.get("spyDesign"),
    "spyOrdering": "★ 同一节点（window）上的监听器按**注册顺序**触发。"
                   "桌内那个处理器在**挂载时**注册（DirectorDesk.tsx:570），"
                   "间谍是**开完浮层之后**才装 ⟹ 排在它**之后**，"
                   "读到的 defaultPrevented 已包含桌内那次的 preventDefault()。",
    "superseded": {
        "what": "**中性键对照臂**（%d 格）由 773b 单独补取。" % provB,
        "why": "773a 的 for-want 循环的补丁没落进文件 ⟹ 中性臂一次都没跑"
               "（%d 行/轮 = %d 实验 + %d SKIP）。"
               % (_nA, _nA - _nSkip, _nSkip),
        "howFixed": "补一个只跑这 %d 格的探针，在汇编器里**合并**，"
                    "不整套重跑（R96）。" % provB,
        "keptFrom773a": "773a 的 %d 格**全部保留**，不作废。" % provA,
    },
    "boundary": "只点对象树的行、6 个 disclosure 触发器、选中相机；"
                "**不点提交/连接/添加，更不做付费或真实生图生视频**。"
                "间谍是**纯读**（只加一个监听器，不改行为）。",
    "structuralSkips": len(sa),
    "deskGoneAfter": [rd.get("deskGoneAfter") for rd in aR + bR],
}
assert comparability["allConsistent773a"], comparability["firstDiff773a"]
assert comparability["allConsistent773b"], comparability["firstDiff773b"]

skipped = sorted({"%s/%s" % k for k in sa})

def cell(r):
    f = r.get("focus") or {}
    return {
        "key": r.get("key"),
        "focusTag": f.get("tag"),
        "focusType": f.get("type"),
        "focusEditable": f.get("editable") is True,
        "target": r.get("target"),
        "targetUndeletable": r.get("targetUndeletable") is True,
        "selectedIds": r.get("selectedIds"),
        "spyInstalled": (r.get("spy") or {}).get("installed") is True,
        "eventsSeen": r.get("eventsSeen"),
        "keysSeen": r.get("keysSeen"),
        "dpAll": r.get("dpAll"),
        "defaultPrevented": r.get("defaultPrevented"),
        "objectsDelta": r.get("objectsDelta"),
        "deskStillOpen": r.get("deskStillOpen"),
    }


t = {k: [cell(r) for r in v] for k, v in g.items()}

# ── 每格的自证
for k, v in t.items():
    for c in v:
        assert c["spyInstalled"] is True, "%s 间谍没装上" % (k,)
        assert c["eventsSeen"], "%s 间谍一个 keydown 都没收到" % (k,)
        assert c["defaultPrevented"] in (True, False), \
            "%s 读不到 defaultPrevented（探针 bug）" % (k,)
        assert c["selectedIds"], "%s 目标没选中 —— 这不是读数" % (k,)
        if k[1] == "neutral":
            assert c["key"] == NEUTRAL_KEY
        else:
            assert (c["focusEditable"] is (k[1] == "editable")), \
                "%s 落点类别与 want 不符" % (k,)

print("（阶段一）合并 %d 格 × %d 轮，无失败；来源 773a %d 格 / 773b %d 格（中性对照）；结构性 SKIP %d 层"
      % (len(CELLS), len(aR), provA, provB, len(skipped)))


# ═══════════════ 2. 静态层 ═══════════════
def src_text(rel):
    p = REPO / rel
    if not p.exists():
        raise SystemExit("FATAL 缺源码 %s" % p)
    return p.read_text(encoding="utf-8")


def strip_comments(s):
    return re.sub(r"//[^\n]*", "", s)


DD = src_text("src/components/director/DirectorDesk.tsx")
FC = src_text("src/components/director/useDirectorFocusContainment.ts")
DDc = strip_comments(DD)
i0 = DDc.index("const handleKeyDown = (event: KeyboardEvent) => {")
i1 = DDc.index('window.addEventListener("keydown", handleKeyDown);')
kd_lines = DDc[:i1].split("\n")
kd = "\n".join(kd_lines)
# 每个分支的 preventDefault 所在行号（**现读**，不手抄）
pdLines = [n for n, ln in enumerate(kd_lines, 1)
           if "event.preventDefault()" in ln]
branches = {}
for label, pat in (("Meta+C", 'toLowerCase() === "c"'),
                   ("Meta+V", 'toLowerCase() === "v"'),
                   ("Meta+Z", 'toLowerCase() === "z"'),
                   ("Meta+Y", 'toLowerCase() === "y"'),
                   ("Delete|Backspace", 'event.key === "Delete"'),
                   ("Escape", 'event.key !== "Escape"')):
    hit = [n for n, ln in enumerate(kd_lines, 1) if pat in ln]
    # 分支内**必须**有一处 preventDefault，且行号在守卫之后
    inner = [n for n in pdLines if hit and n > hit[0]]
    branches[label] = {"guardLine": hit[0] if hit else None,
                       "preventDefaultLines": inner,
                       "hasPreventDefault": bool(inner)}
# 冒泡监听里有没有 Tab 之外也会 preventDefault 的（会污染本批读数）
fcHook = strip_comments(FC)
fcHook = fcHook[fcHook.index("const handleKeyDown = (event: KeyboardEvent)"
                             " => {"):
               fcHook.index('root.addEventListener("keydown", handleKeyDown);')]

static = {
    "deskListenerOnWindow":
        'window.addEventListener("keydown", handleKeyDown)' in DDc,
    "deskListenerIsCapture":
        'window.addEventListener("keydown", handleKeyDown, true)' in DDc,
    "deskKeydownListenerCount": DDc.count('addEventListener("keydown"'),
    "guardIsEditableReturn": "if (isEditable) return;" in kd,
    "guardBeforeDelete": kd.index("if (isEditable) return;") < kd.index(
        'event.key === "Delete"'),
    "guardBeforeMetaC": kd.index("if (isEditable) return;") < kd.index(
        'toLowerCase() === "c"'),
    "preventDefaultLines": pdLines,
    "branches": branches,
    "allFiveBranchesPrevent": all(
        v["hasPreventDefault"] for v in branches.values()),
    # 污染检查：Tab 处理器只对 Tab preventDefault；页面那条桌开时已死
    "focusContainmentGuardsOnTabOnly": bool(
        re.search(r'if \(event\.key !== "Tab"\) return;', fcHook)),
    "focusContainmentPreventDefaults": fcHook.count("event.preventDefault()"),
    "deleteGuardedBySelection": "selectedObjectIds.length" in kd,
    "deleteGroupSubBranch": "DELETE_GROUP" in kd,
    "deleteObjectsSubBranch": "DELETE_OBJECTS" in kd,
}
assert static["deskListenerOnWindow"] is True
assert static["deskKeydownListenerCount"] == 1, \
    "DirectorDesk 里的 keydown 监听不止一个 —— 机制结论要重查"
assert static["deskListenerIsCapture"] is False
assert static["guardIsEditableReturn"] is True
assert static["guardBeforeDelete"] is True, "isEditable 早退不在 Delete 之前"
assert static["guardBeforeMetaC"] is True, "isEditable 早退不在 Meta+C 之前"
assert static["allFiveBranchesPrevent"] is True, (
    "有分支不调 preventDefault —— 「defaultPrevented=true 就等于分支跑了」"
    "这条推理作废，要重查")
assert static["focusContainmentGuardsOnTabOnly"] is True, \
    "对话框那个 Tab 处理器不再只认 Tab —— 它会污染本批读数"
assert static["deleteGuardedBySelection"] is True
assert static["deleteGroupSubBranch"] and static["deleteObjectsSubBranch"], \
    "Delete 分支的组/对象两条子路径变了 —— 772 的机制要重查"
print("（阶段二）静态层：桌内 %d 个 window 冒泡监听；5 个分支全部 "
      "preventDefault（行号 %r）；Tab 处理器只认 Tab"
      % (static["deskKeydownListenerCount"], static["preventDefaultLines"]))


# ═══════════════ 3. 聚合 ═══════════════
DESTRUCTIVE_KEYS = ("Delete", "Backspace")
NE = [(i, "noneditable", k) for i in IDS for k in KEYS]
ED = [(i, "editable", k) for i in sorted(HAS_EDITABLE) for k in KEYS]
NEU = [(i, "neutral", NEUTRAL_KEY) for i in IDS]

reach = {}
for k in NE + ED:
    dps = {c["defaultPrevented"] for c in t[k]}
    assert len(dps) == 1, "%s 两轮 dp 不一致：%r" % (k, dps)
    reach["%s/%s/%s" % k] = {
        "defaultPrevented": dps.pop(),
        "focusEditable": t[k][0]["focusEditable"],
        "objectsDelta": sorted({c["objectsDelta"] for c in t[k]}),
        "target": t[k][0]["target"],
        "targetUndeletable": t[k][0]["targetUndeletable"],
    }

# ── ★ 预测 1：非编辑框 ⟹ 分支跑了（dp=true）
for k in NE:
    assert reach["%s/%s/%s" % k]["defaultPrevented"] is True, (
        "%s/%s/%s 落非编辑框却读到 defaultPrevented=false —— "
        "机制读错了（或间谍顺序不成立），要重查" % k)
# ── ★ 预测 2：可编辑框 ⟹ isEditable 早退（dp=false）
for k in ED:
    assert reach["%s/%s/%s" % k]["defaultPrevented"] is False, (
        "%s/%s/%s 落可编辑框却读到 defaultPrevented=true —— "
        "isEditable 早退对 %s 没用，772 的守卫结论要推翻"
        % (k + (k[2],)))
# ── ★ 预测 3：中性键 ⟹ 桌内不处理 ⟹ dp=false
neutral = {}
for k in NEU:
    dps = {c["defaultPrevented"] for c in t[k]}
    assert len(dps) == 1, "%s 两轮 dp 不一致：%r" % (k, dps)
    assert dps == {False}, (
        "★ 中性键 %s 竟然读到 defaultPrevented=true —— 说明在桌内那个"
        "处理器**之前**就有人调了 preventDefault()，"
        "那么「dp=true 就等于分支跑了」这条推理**不成立**，整批要重查"
        % NEUTRAL_KEY)
    neutral[k[0]] = dps.pop()

def _sk(keys):
    return sorted("%s/%s/%s" % k for k in keys)


branchReached = _sk(k for k in NE
                    if reach["%s/%s/%s" % k]["defaultPrevented"] is True)
guardHolds = _sk(k for k in ED
                 if reach["%s/%s/%s" % k]["defaultPrevented"] is False)
sideEffect = _sk(k for k in NE
                 if k[2] in DESTRUCTIVE_KEYS
                 and reach["%s/%s/%s" % k]["defaultPrevented"] is True
                 and reach["%s/%s/%s" % k]["objectsDelta"]
                 and reach["%s/%s/%s" % k]["objectsDelta"][0] < 0)
# ★ 只统计**破坏性**键：Meta+C/V/Z 本来就不会改对象数（剪贴板/撤销栈），
#   把它们算进「dp=true 但没副作用」是概念错误（第一版就犯了这个）。
dpNoEffect = _sk(k for k in NE
                 if k[2] in DESTRUCTIVE_KEYS
                 and reach["%s/%s/%s" % k]["defaultPrevented"] is True
                 and reach["%s/%s/%s" % k]["objectsDelta"]
                 and reach["%s/%s/%s" % k]["objectsDelta"][0] == 0)
assert not (set(dpNoEffect) - set(_sk((i, "noneditable", kk)
                                          for i in CAM_ONLY
                                          for kk in DESTRUCTIVE_KEYS))), \
    "有非 cameraTrack 的格子「分支跑了但没删掉」—— 与 772 的读数不符"

# 更正 772：4/6 → 6/6
assert len({k.split("/")[0] for k in branchReached}) == 6, \
    "分支跑到的浮层数不是 6 —— 与预测不符"
assert all(x.split("/")[0] in {y.split("/")[0] for y in branchReached}
           for x in dpNoEffect), "dpNoEffect 里有非 cameraTrack 的浮层"

branchMap = {
    "perCell": reach,
    "neutralControl": neutral,
    "branchReachedCells": branchReached,
    "branchReachedDisclosures": sorted({k.split("/")[0]
                                        for k in branchReached}),
    "guardHoldsCells": guardHolds,
    "sideEffectCells": sideEffect,
    "dpTrueButNoEffectCells": dpNoEffect,
    "claim": "★ 桌内那个 keydown 处理器的分支，在**6/6 个浮层**里"
             "焦点落在非编辑框控件上时**全部都跑到了**"
             "（%d/%d 格 defaultPrevented=true）" % (len(branchReached),
                                                    len(NE)),
    "note": "Delete/Backspace 的**副作用**只在 %d 格看得见 —— "
            "另外 %d 格也是 dp=true，只是目标不可删 ⟹ 772 那句"
            "「preset/pathmenu 结构上不可判」指的是**副作用**不可判，"
            "**分支**是可判的。" % (len(sideEffect), len(dpNoEffect)),
    "perDisclosure": {
        i: {"deleteBranchReached":
            all(reach["%s/noneditable/%s" % (i, kk)]["defaultPrevented"]
                is True for kk in DESTRUCTIVE_KEYS),
            "metaKeysBranchReached":
            all(reach["%s/noneditable/%s" % (i, kk)]["defaultPrevented"]
                is True for kk in ("Meta+z", "Meta+c", "Meta+v")),
            "guardHolds": ("%s/editable/Delete" % i) in guardHolds,
            "neutralFalse": neutral[i] is False,
            "sideEffectVisible":
            ("%s/noneditable/Delete" % i) in sideEffect}
        for i in IDS},
}
assert len(branchReached) == len(NE)
assert len(guardHolds) == len(ED)
assert len(sideEffect) == 8, "副作用可见的格数应为 8，实为 %d" % len(sideEffect)
print("（阶段三）分支跑到 %d/%d 格（%d 个浮层）｜守卫挡住 %d/%d 格｜"
      "中性键全 false｜副作用可见 %d 格、dp=true 但无副作用 %d 格"
      % (len(branchReached), len(NE),
         len(branchMap["branchReachedDisclosures"]),
         len(guardHolds), len(ED), len(sideEffect), len(dpNoEffect)))


# ═══════════════ 4. findings ═══════════════
findings = {
    "F0_comparable": {
        "allConsistent773a": comparability["allConsistent773a"],
        "allConsistent773b": comparability["allConsistent773b"],
        "rounds": comparability["rounds"],
        "mergedCells": comparability["mergedCells"],
        "cellsFrom773a": comparability["cellsFrom773a"],
        "cellsFrom773b": comparability["cellsFrom773b"],
        "structuralSkips": comparability["structuralSkips"],
        "superseded": comparability["superseded"],
        "note": "%d 格 × %d 轮，两个探针各自逐格归一化后 diff 均为空（R55）。"
                "其中 %d 层是结构性 SKIP（没有可编辑控件）。"
                % (len(CELLS), len(aR), comparability["structuralSkips"]),
    },
    "F1_spyValid": {
        "claim": "★ 间谍本身可信：装上了、收到了事件、读得到 defaultPrevented",
        "cellsChecked": len(CELLS) * 2,
        "allInstalled": all(c["spyInstalled"] for v in t.values() for c in v),
        "allSawEvent": all(c["eventsSeen"] for v in t.values() for c in v),
        "allReadBoolean": all(c["defaultPrevented"] in (True, False)
                              for v in t.values() for c in v),
    },
    "F2_neutralControl": {
        "claim": "★ 中性键对照：桌内**不处理**的 %s 读到 defaultPrevented=false"
                 % NEUTRAL_KEY,
        "perDisclosure": neutral,
        "allFalse": all(v is False for v in neutral.values()),
        "why": "这是「dp=true 就等于分支跑了」这条推理的**前提**："
               "若连桌内不处理的键都读到 true，说明在桌内那个处理器**之前**"
               "就有人调了 `preventDefault()`，那么整批读数都不能用了。",
    },
    "F3_branchReached": {
        "claim": "★ 核心：桌内那个 keydown 处理器的分支，在**6/6 个浮层**里"
                 "焦点落在非编辑框控件上时**全部跑到了**",
        "cells": branchReached,
        "count": len(branchReached),
        "total": len(NE),
        "disclosures": branchMap["branchReachedDisclosures"],
        "perKey": {kk: sorted(k for k in branchReached
                              if k.endswith("/" + kk)) for kk in KEYS},
        "note": "这条把 772 的「4/6 个浮层实测穿透」**扩到 6/6** —— "
                "772 少的那 2 个不是安全的，只是**副作用**测不出来。",
    },
    "F4_guardHolds": {
        "claim": "★ 对照：焦点落在**可编辑**控件上时，那道 `isEditable` "
                 "早退把**全部五个键**都挡住了",
        "cells": guardHolds,
        "count": len(guardHolds),
        "total": len(ED),
        "keysGuarded": sorted({k.split("/")[2] for k in guardHolds}),
        "note": "772 只量过 Delete 被挡（3/3）。本批把作用域量全了："
                "**`Meta+C` / `Meta+V` / `Meta+Z` / `Delete` / `Backspace` "
                "一个都没漏**。所以那道早退不是「只挡住一半」，"
                "而是「**按控件类别挡，与浮层无关**」。",
    },
    "F5_dpEqualsNotEditable": {
        "claim": "★ %d/%d 格上 `defaultPrevented` 恰好等于「落点非可编辑」"
                 % (len(NE) + len(ED), len(NE) + len(ED)),
        "cellsChecked": len(NE) + len(ED),
        # ★ 现算，**不写死**（R99：第一版就是在这里写死了 True）
        "mismatches": [k for k in NE + ED
                       if reach["%s/%s/%s" % k]["defaultPrevented"]
                       is not (k[1] == "noneditable")],
        "perfect": not [k for k in NE + ED
                        if reach["%s/%s/%s" % k]["defaultPrevented"]
                        is not (k[1] == "noneditable")],
        "how": "这是从源码逐行推出的**预测**（`:487` 的早退在所有分支之前），"
               "45 格全部吻合 ⟹ 桌内那个处理器**对浮层一无所知**，"
               "它唯一的输入是 `event.target` 的标签名。",
    },
    "F6_sideEffectVsBranch": {
        "claim": "★ 「分支跑到了」与「东西真被删了」是**两件事**",
        "sideEffectCells": sideEffect,
        "dpTrueButNoEffectCells": dpNoEffect,
        "sideEffectCount": len(sideEffect),
        "dpNoEffectCount": len(dpNoEffect),
        "note": "同样是 dp=true，%d 格看得见副作用（目标可删），"
                "%d 格看不见（目标=主机位，删不掉）。"
                "**772 只报了前者，于是「后者」被写成了「不可判」—— "
                "它其实是可以判的，只要换一个与副作用无关的读数。**"
                % (len(sideEffect), len(dpNoEffect)),
    },
    "F7_staticLines": {
        "claim": "机制：桌内那个处理器的 5 个分支**每走到一个就调一次 "
                 "`preventDefault()`（行号现读）",
        "preventDefaultLines": static["preventDefaultLines"],
        "branches": static["branches"],
        "allFivePrevent": static["allFiveBranchesPrevent"],
        "guardBeforeDelete": static["guardBeforeDelete"],
        "guardBeforeMetaC": static["guardBeforeMetaC"],
        "deleteSubBranches": {"group": static["deleteGroupSubBranch"],
                              "objects": static["deleteObjectsSubBranch"]},
    },
    "F8_noPollution": {
        "claim": "读数没被别的处理器污染",
        "focusContainmentGuardsOnTabOnly":
            static["focusContainmentGuardsOnTabOnly"],
        "neutralAllFalse": all(v is False for v in neutral.values()),
        "pageHandlerDeadWhenDeskOpen": True,
        "why": "对话框那个 Tab 处理器（`useDirectorFocusContainment`）"
               "`if (event.key !== \"Tab\") return;` ⟹ 对本批这五个键"
               "**一次都不 preventDefault**；主画布页那条 Delete 在桌开时"
               "整条早退（772 的 F9）。加上中性键对照全 false，"
               "三个独立理由指向同一件事：**dp=true 就是桌内那个分支跑了**。",
    },
}

# ═══════════════ 5. 判据 ═══════════════
judgments = [
    {"id": "J1", "statement": "两个探针的读数各自两轮逐格一致（可比性）",
     "verdict": "PASS" if (comparability["allConsistent773a"]
                           and comparability["allConsistent773b"])
                else "FAIL",
     "evidenceKey": "F0_comparable", "evidence": findings["F0_comparable"]},
    {"id": "J2",
     "statement": "★ 中性键对照：桌内**不处理**的 %s 读到 "
                  "defaultPrevented=**false**（6/6）—— 这是「dp=true 就是"
                  "分支跑了」的**前提**" % NEUTRAL_KEY,
     "verdict": "PASS" if all(v is False for v in neutral.values()) else "FAIL",
     "evidenceKey": "F2_neutralControl",
     "evidence": findings["F2_neutralControl"]},
    {"id": "J3",
     "statement": "间谍本身可信：每格都装上了、都收到了事件、都读得到布尔值",
     "verdict": "PASS" if (findings["F1_spyValid"]["allInstalled"]
                           and findings["F1_spyValid"]["allSawEvent"]
                           and findings["F1_spyValid"]["allReadBoolean"])
                else "FAIL",
     "evidenceKey": "F1_spyValid", "evidence": findings["F1_spyValid"]},
    {"id": "J4",
     "statement": "★ 核心：分支在**6/6 个浮层**的**非编辑框**落点上"
                  "全部跑到了（%d/%d 格 dp=true）" % (len(NE), len(NE)),
     "verdict": "PASS" if len(branchReached) == len(NE) else "FAIL",
     "evidenceKey": "F3_branchReached", "evidence": findings["F3_branchReached"]},
    {"id": "J5",
     "statement": "★ 更正 772：D14 的范围是 **6/6 个浮层**，不是 4/6 —— "
                  "preset / 路径菜单不是安全的，只是**副作用**测不出来",
     "verdict": "PASS" if (len(branchMap["branchReachedDisclosures"]) == 6
                           and not findings["F5_dpEqualsNotEditable"]
                           ["mismatches"]) else "FAIL",
     "evidenceKey": "F3_branchReached", "evidence": findings["F3_branchReached"]},
    {"id": "J6",
     "statement": "★ 对照：可编辑落点上那道早退把**全部五个键**都挡住了"
                  "（%d/%d 格 dp=false）" % (len(ED), len(ED)),
     "verdict": "PASS" if len(guardHolds) == len(ED) else "FAIL",
     "evidenceKey": "F4_guardHolds", "evidence": findings["F4_guardHolds"]},
    {"id": "J7",
     "statement": "★ dp 恰好等于「落点非可编辑」，45/45 格 —— "
                  "桌内那个处理器**对浮层一无所知**",
     "verdict": "PASS" if findings["F5_dpEqualsNotEditable"]["perfect"]
                else "FAIL",
     "evidenceKey": "F5_dpEqualsNotEditable",
     "evidence": findings["F5_dpEqualsNotEditable"]},
    {"id": "J8",
     "statement": "★ 「分支跑到了」与「东西真被删了」分开报：%d 格有副作用、"
                  "%d 格 dp=true 但无副作用（全部落在 cameraTrack 两层）"
                  % (len(sideEffect), len(dpNoEffect)),
     "verdict": "PASS" if (len(sideEffect) == 8 and len(dpNoEffect) == 4
                           and all(k.split("/")[0] in CAM_ONLY
                                   for k in dpNoEffect)) else "FAIL",
     "evidenceKey": "F6_sideEffectVsBranch",
     "evidence": findings["F6_sideEffectVsBranch"]},
    {"id": "J9",
     "statement": "机制：5 个分支**每走到一个就调一次** `preventDefault()`"
                  "（行号现读），且都在 `:487` 那道早退**之后**",
     "verdict": "PASS" if (static["allFiveBranchesPrevent"]
                           and static["guardBeforeDelete"]
                           and static["guardBeforeMetaC"]) else "FAIL",
     "evidenceKey": "F7_staticLines", "evidence": findings["F7_staticLines"]},
    {"id": "J10",
     "statement": "读数没被别的处理器污染（Tab 处理器只认 Tab + 页面那条"
                  "桌开时已死 + 中性键全 false，三条独立理由）",
     "verdict": "PASS" if (static["focusContainmentGuardsOnTabOnly"]
                           and all(v is False
                                   for v in neutral.values())) else "FAIL",
     "evidenceKey": "F8_noPollution", "evidence": findings["F8_noPollution"]},
]

# ═══════════════ 6. audit ═══════════════
audit = {
    "batch": 773, "date": "2026-10-01",
    "scope": "桌内那个 keydown 处理器的分支**到底到没到** —— 用 "
             "`event.defaultPrevented` 做直接读数，替 772 的「靠副作用反推」",
    "env": {"base": "http://localhost:4317", "canvas": "canvas-2",
            "viewport": "1440x1000（桌面）",
            "player": "chromium (playwright sync_api)", "srcModified": False},
    "probes": [
        {"id": "773a", "file": "probes/dbg773a.py",
         "raw": "raw/vb773a.json", "rounds": len(aR),
         "cells": comparability["cellsPerRound773a"], "injected": True,
         "note": "★ 注入 = 一个**纯读**间谍：window 冒泡阶段、"
                 "**开完浮层之后**才注册（故排在桌内处理器之后）。"
                 "主网格：6 浮层 × 2 落点 × 5 键。"},
        {"id": "773b", "file": "probes/dbg773b.py",
         "raw": "raw/vb773b.json", "rounds": len(bR),
         "cells": comparability["cellsPerRound773b"], "injected": True,
         "note": "只补**中性键对照**（773a 的 for-want 补丁没落进文件，"
                 "中性臂一次都没跑）—— 不整套重跑（R96）。"}],
    "rawSha": {A_p.name: sha(A_p), B_p.name: sha(B_p)},
    "comparability": comparability, "static": static, "branchMap": branchMap,
    "findings": findings, "judgments": judgments,
    "defects": [],
    "defectsNote": "★ 本批**没有新缺陷**。它是 772 的 D14 的**范围更正**"
                   "与**读数方法**升级：4/6 → **6/6**，"
                   "并把 `isEditable` 早退的作用域从「只验过 Delete」"
                   "补到「五个键全部」。",
    "corrections": [
        {"id": "C773-1",
         "targets": ["batch 772 findings(F6_confounded)",
                     "batch 772 defects[D14].measured",
                     "batch 772 judgments[J7]"],
         "wasSaid": "「preset / pathmenu 的 4 个 Delete 格**结构上不可判**"
                    "（不是『没穿透』）」；D14 的 `measured` 写的是"
                    "「6 个浮层里 **4 个**实测会真删」",
         "actual": "★ 不可判的是**副作用**，不是**分支**。这两件事必须分开："
                   "同是 `defaultPrevented=true`，8 格目标可删所以看得见"
                   "副作用，4 格目标=主机位所以看不见。"
                   "换一个与副作用无关的读数之后，那 4 格**也是可判的**，"
                   "而且**分支确实跑到了**。",
         "measuredBy": "臂 1（落非编辑框）在 **6/6 个浮层**读到 "
                       "`defaultPrevented=true`（%d/%d 格）；"
                       "Delete/Backspace 的副作用在 %d 格可见、"
                       "%d 格 dp=true 但无副作用（全部落在 cameraTrack 两层）。"
                       % (len(branchReached), len(NE), len(sideEffect),
                          len(dpNoEffect)),
         "correctedScope": "D14 影响 **6/6 个浮层**，不是 4/6。",
         "whyItMatters": "写成「4/6」会让人以为 preset / 路径菜单**是安全的**，"
                         "从而在排期时跳过它们 —— 而它们同样会删掉"
                         "工作区里选中的对象（只是种子项目里恰好没有可删目标）。"},
    ],
    "observations": [
        {"id": "O773-1",
         "text": "★ 桌内那个处理器**对浮层一无所知**：它唯一的输入是 "
                 "`event.target` 的标签名。45/45 格上 "
                 "`defaultPrevented` 恰好等于「落点非可编辑」，"
                 "**与是哪个浮层完全无关**。",
         "whyItMatters": "「按浮层逐个测」的思路在这里是浪费 —— "
                         "**机制上不存在按浮层的分支**，一个守卫就能全族覆盖。"},
        {"id": "O773-2",
         "text": "★ 那道 `isEditable` 早退的作用域此前只量过一个键。"
                 "本批补全：它对 `Delete`/`Backspace`/`Meta+C`/`Meta+V`/"
                 "`Meta+Z` **五个键一视同仁**（可编辑落点 15/15 全挡住，"
                 "非编辑落点 30/30 全放行）。",
         "whyItMatters": "这说明它不是「只挡住一半」而是"
                         "「**按控件类别整齐地挡**」—— 修 D14 时可以直接"
                         "把这条守卫的判据从「标签名」换成「焦点在不在浮层内」，"
                         "**行为边界不变**。"},
        {"id": "O773-3",
         "text": "★ **「分支跑到了」与「东西真被删了」是两个信号**，"
                 "必须分别报。8 格两个信号同时为真，4 格只有前者 —— "
                 "**只报后者就会把「测不出来」写成「没问题」。**",
         "whyItMatters": "这是 R94 在**同一批**里的第二次成立："
                         "772 已经因为「靠副作用反推」少报了 2 个浮层。"},
    ],
    "probeLessons": [
        {"id": "R96",
         "text": "★ **一批读数失效时，不要整套重跑。** 773a 的中性臂"
                 "一次都没跑（`for want in (...)` 那个补丁没落进文件 —— "
                 "静默的、汇总照常打印的那种失效）。做法是**补一个只跑"
                 "缺失那几格的探针**，在汇编器里**合并**，并如实记下"
                 "「哪些格来自哪个探针、为什么被取代」。",
         "whyItMatters": "整套重跑会丢掉已经有效的读数，"
                         "更会把「为什么失效」这段推理从产物里抹掉。"},
        {"id": "R97",
         "text": "★ **「一个读不出来」和「一个没发生」是两回事。** "
                 "772 的 4 格是靠**副作用**（对象数变化）判的，"
                 "而副作用只在目标可删时才可见。修法：找一个**与副作用无关的"
                 "直接读数** —— 本批用 `event.defaultPrevented`，"
                 "因为桌内那个处理器**每走到一个分支就调一次** `preventDefault()`。"
                 "**判别式：读数方法里有没有一个「目标本身可不可观测」的自由变量。**",
         "whyItMatters": "副作用型读数天然带着「目标状态」这个隐藏变量；"
                         "不把它分离出来，就会在目标恰好不可观测时"
                         "把「没变化」误报成「没发生」。"},
        {"id": "R98",
         "text": "★ **读数方法本身要有中性对照。** 本批在断言之前先跑一格："
                 "按一个桌内**明确不处理**的键（`F2`），"
                 "间谍必须读到 `defaultPrevented=false`。"
                 "若读到 true，说明在桌内那个处理器**之前**就有人调了 "
                 "`preventDefault()`，那么「true 就等于分支跑了」整条推理作废。"
                 "**顺序型读数（监听器顺序、事件顺序）必须配一个「什么都没发生」"
                 "的阴性格。**",
         "whyItMatters": "监听器顺序是**注册顺序**决定的，"
                         "而注册顺序是**时序**事实 —— 它随时可能被"
                         "一次重挂载改掉，不测就会静默失效。"},
        {"id": "R99",
         "text": "★ **要读的字段必须在监听器里真的 push 它。** 第一版间谍写成 "
                 "`{key, meta, shift, atEntry:false, tag, type}` —— "
                 "`atEntry` 是**硬编码的字面量 false**，"
                 "而 `e.defaultPrevented` **根本没记**。结果 45 格全部读成 "
                 "`None`，而且**探针不报错、汇总照常打印**。"
                 "★ **识别信号：某一个字段在所有格上取同一个值"
                 "（尤其是 `None`/`False` 这类「看起来合理」的值），"
                 "先怀疑它没被记，而不是先怀疑产品。**",
         "whyItMatters": "R75 的加强版：判读朝「通过」方向的误报，"
                         "在这里伪装成了一次「读数全为否」的**干净结论**。"},
    ],
}

for j in audit["judgments"]:
    k = j["evidenceKey"]
    assert k in findings, "判据 %s 引用了不存在的 findings 键" % j["id"]
    assert findings[k] == j["evidence"], (
        "判据 %s 的 evidence 与 findings[%s] 不相等" % (j["id"], k))

OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1),
               encoding="utf-8")
print("wrote %s" % OUT)
print("判据 %d 条（PASS %d / FAIL %d）| findings %d 键 | 新缺陷 %d | "
      "更正 %d | 观察 %d | 探针教训 %d"
      % (len(audit["judgments"]),
         sum(1 for j in judgments if j["verdict"] == "PASS"),
         sum(1 for j in judgments if j["verdict"] == "FAIL"),
         len(findings), len(audit["defects"]), len(audit["corrections"]),
         len(audit["observations"]), len(audit["probeLessons"])))
print("分支跑到：%d/%d 格（%d 个浮层）｜守卫：%d/%d ｜"
      "副作用可见 %d 格、dp=true 无副作用 %d 格"
      % (len(branchReached), len(NE),
         len(branchMap["branchReachedDisclosures"]),
         len(guardHolds), len(ED), len(sideEffect), len(dpNoEffect)))
print("更正：%r" % ([c["id"] for c in audit["corrections"]],))
