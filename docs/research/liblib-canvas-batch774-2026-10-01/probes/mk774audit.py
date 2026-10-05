#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 774 汇编器：从 raw/vb774{a,b}.json 现算 runtime-audit.json

## 这一批问的两件事

**问①**（探针 a，51 格）：D14「修法方向①」够不够？
方向① = 把 `isEditable` 那道早退的判据从**按标签名**换成**按浮层**。
用**注入**（只写 `contentEditable` 属性，不改 `src/`）让那道守卫在
浮层后代上**真的触发**，于是「守卫一旦触发，D14 的可见后果就没了」
这条**充分性**可以在运行时验，而识别性（谓词该怎么写）必须改 `src/`，攒为拍板项。

**问②**（探针 b，12 格）：方向① 会不会把 **Escape 阶梯**也一起挡掉？
`DirectorDesk.tsx` 的 `if (isEditable) return;` 排在**所有分支之前**，
Escape 阶梯也在它后面 ⟹ 问① 的前提**同时**意味着 Escape 一起被挡。问① 没量这件事。

## 断言编码的是**预测**，不是观测

每条 `assert` 编码的都是**从源码逐行推出的**结论。跑出来就该是这个数。
**断言炸了是机制读错了，是要去查的发现，不是要改的断言。**

关键几条（都能在源码里指出来）：
- 守卫输入 `target.isContentEditable === true` ⟹ `DirectorDesk.tsx:486` 直接 return
  ⟹ **任何分支都到不了** ⟹ `defaultPrevented` 必为 `false`。
- 守卫输入为假（按钮）⟹ 六个浮层上 Delete 分支都跑 ⟹ `dp === true`（这是 773 的结论，
  本批**当场重测一遍**当基线，而不是引用历史读数——R99 的同族：用一个可能已坏的读数
  方法去验上一批的结论，等于没验）。
- 捕获阶段且带 `stopImmediatePropagation()` 的 Escape 主人（phonevcam / modellib）
  排在桌内那个**之前** ⟹ 桌内**收不到事件** ⟹ `dp === false`，且**与注入无关**。
- 冒泡阶段、无 `preventDefault` 的两个主人（preset / pathmenu）排在桌内**之后**
  ⟹ 桌内**先**跑完整个 Escape 阶梯（`closeWorkspace()`）⟹ D8。
- export / crowd **没有**自己的 Escape 主人 ⟹ 桌内落 `exportPanelOpen`（关面板，桌在）
  或一路 fall through（`closeWorkspace()`，桌没了）。

## 规矩（沿用 756–773）

1. **数字不许手抄** —— 每个数从 raw 现算；静态事实当场读源码数出来。
2. **缺原始读数判失败**；**缺格判失败**，不许当「没发生」。
3. **`findings[k] == judgments[i].evidence`**，写盘前断言，验收器再查一遍。
4. **先证明可比再谈一致**（R55）：逐轮归一化 diff。
5. **`all([])` 是 True**：每处聚合显式判非空；分类必须**铺满**格子。
6. **读数方法本身要有对照**（R86）：中性键 `F2` 的那格**不只看 `dp=false`**——
   还要看**间谍确实收到了 F2**。只看 `dp` 的话，「注入把键投递本身弄坏」也会得 `false`，
   对照就废了。这一条是本批对 R86 的一次加强。
7. **注入必须先验生效**（R99）：每格记 `injectionSilent`，有就不算结果。
8. **静态断言的方向要写对**（R92）。
9. **结构性缺失要显式 SKIP 且分类铺满**，不许静默少一格。
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
KEYS = ["Delete", "Backspace", "Meta+z", "Meta+c", "Meta+v"]
NEUTRAL_KEY = "F2"
HAS_EDITABLE = ["export", "crowd", "modellib"]

# 问① 的格子：臂 A 基线 6、臂 B（α）30、臂 C（β）6、臂 D 中性 6、臂 E（β×可编辑）3
A_CELLS = ([(i, "base", "noneditable", "Delete") for i in IDS]
           + [(i, "alpha", "noneditable", k) for i in IDS for k in KEYS]
           + [(i, "beta", "noneditable", "Delete") for i in IDS]
           + [(i, "neutral", "noneditable", NEUTRAL_KEY) for i in IDS]
           + [(i, "beta", "editable", "Delete") for i in HAS_EDITABLE])
# 问② 的格子：6 层 × 2 臂（none / alpha）
B_CELLS = [(i, arm) for i in IDS for arm in ("none", "alpha")]
INJECT_ARMS = ("alpha", "beta", "neutral")


def load(name):
    p = RAW / name
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
A, A_p = load("vb774a.json")
B, B_p = load("vb774b.json")
for nm, raw in (("774a", A), ("774b", B)):
    rs = raw.get("rounds") or []
    assert len(rs) == 2, "%s 轮数 %d" % (nm, len(rs))
aR, bR = A["rounds"], B["rounds"]


def grid_a(raw):
    g, skip = {}, set()
    for rd in raw["rounds"]:
        for r in rd.get("rows") or []:
            if r.get("SKIPPED"):
                skip.add((r.get("id"), r.get("arm"), r.get("want")))
                continue
            g.setdefault((r.get("id"), r.get("arm"), r.get("want"),
                          r.get("key")), []).append(r)
    return g, skip


def grid_b(raw):
    g = {}
    for rd in raw["rounds"]:
        for r in rd.get("rows") or []:
            g.setdefault((r.get("id"), r.get("arm")), []).append(r)
    return g


ga, sa = grid_a(A)
gb = grid_b(B)
# ★ R96 的机械化：探针 a 的五个臂是**逐个 add() 显式调**的，
#   而 773 的教训正是「for 循环的补丁没落进文件 ⟹ 那一臂一次都没跑，
#   而探针不报错、汇编器也不报」。所以这里**逐臂断言非空**。
for arm in ("base", "alpha", "beta", "neutral"):
    got = [k for k in ga if k[1] == arm]
    assert got, "★ 探针 a 的「%s」臂一次都没跑 —— 探针不报错不等于跑过了（R96）" % arm
assert not [k for k in ga if k[1] not in ("base", "alpha", "beta", "neutral")], \
    "探针 a 里有没登记的臂 —— 合并规则要重算"
assert not sa, \
    "探针 a 里出现了结构性 SKIP 行 %r —— 臂 E 本来就只跑有可编辑控件的 3 层" \
    % (sorted(sa),)
assert sorted(ga) == sorted(A_CELLS), \
    "问① 格集合与登记的不符：多 %r / 少 %r" % (
        sorted(set(ga) - set(A_CELLS))[:4], sorted(set(A_CELLS) - set(ga))[:4])
assert sorted(gb) == sorted(B_CELLS), \
    "问② 格集合与登记的不符：多 %r / 少 %r" % (
        sorted(set(gb) - set(B_CELLS))[:4], sorted(set(B_CELLS) - set(gb))[:4])

missingA = [k for k in A_CELLS if k not in ga]
missingB = [k for k in B_CELLS if k not in gb]
assert not (missingA or missingB), \
    "缺格 A=%r B=%r —— 判失败，不许当「没发生」" % (missingA[:4], missingB[:4])
failed = sorted({"A:%s/%s/%s/%s" % k for k, v in ga.items()
                 for r in v if r.get("FAILED")}
                | {"B:%s/%s" % k for k, v in gb.items()
                   for r in v if r.get("FAILED")})
assert not failed, "有失败格 %r —— 判失败" % (failed,)
for k, v in list(ga.items()) + list(gb.items()):
    assert len(v) == 2, "%s 轮数 %d" % (k, len(v))
provA = len(ga)
provB = len(gb)
_nA = len(aR[0]["rows"])
_nB = len(bR[0]["rows"])

comparability = {
    "allConsistent774a": round_diff(A, "rows")[0] is True,
    "allConsistent774b": round_diff(B, "rows")[0] is True,
    "firstDiff774a": {} if round_diff(A, "rows")[0] is True
                     else {"rows": round_diff(A, "rows")[1]},
    "firstDiff774b": {} if round_diff(B, "rows")[0] is True
                     else {"rows": round_diff(B, "rows")[1]},
    "rounds": len(aR),
    "cellsPerRound774a": _nA,
    "cellsPerRound774b": _nB,
    "cellsQ1": len(ga),
    "cellsQ2": len(gb),
    "structuralSkips774a": len(sa),
    "protocol": "★ 每格都从**重新加载的页面**开始并清空 localStorage；"
                "每格都**点选**一个目标并回读 `selectedIds`；落点用 "
                "`.focus({preventScroll:true})` 并回读 `activeElement` 类别。",
    "injectionHonesty": A.get("injectionHonesty"),
    "whatThisProves": A.get("whatThisProves"),
    "whyQ2": B.get("whyItMatters"),
    "escapeOwners": B.get("escapeOwners"),
    "reading": B.get("reading"),
    "boundary": "只点对象树的行、6 个 disclosure 触发器、**选中**相机；"
                "**不点提交/连接/添加，更不做付费或真实生图生视频**。"
                "间谍是**纯读**（只加监听器）；注入只写 `contentEditable` 属性，"
                "**不改任何监听器、不改任何业务逻辑**。",
}
assert comparability["allConsistent774a"], comparability["firstDiff774a"]
assert comparability["allConsistent774b"], comparability["firstDiff774b"]


def cellA(r):
    f = r.get("focus") or {}
    inj = r.get("inject") or {}
    return {
        "key": r.get("key"),
        "focusTag": f.get("tag"),
        "focusEditable": f.get("editable") is True,
        "target": r.get("target"),
        "targetUndeletable": r.get("targetUndeletable") is True,
        "selectedIds": r.get("selectedIds"),
        "injectVariant": inj.get("variant"),
        "injectTook": inj.get("took"),
        "injectRootCE": inj.get("rootCE"),
        "injectActiveCE": inj.get("activeCE"),
        "injectionSilent": r.get("injectionSilent") is True,
        "focusMovedByInject": r.get("focusMovedByInject") is True,
        "spyInstalled": (r.get("spy") or {}).get("installed") is True,
        "eventsSeen": r.get("eventsSeen"),
        "keysSeen": r.get("keysSeen"),
        "targetCE": r.get("targetCE"),
        "defaultPrevented": r.get("defaultPrevented"),
        "objectsDelta": r.get("objectsDelta"),
        "selectedDelta": r.get("selectedDelta"),
        "deskStillOpen": r.get("deskStillOpen"),
        "panelStillOpen": r.get("panelStillOpen"),
    }


def cellB(r):
    f = r.get("focus") or {}
    inj = r.get("inject") or {}
    return {
        "key": r.get("key"),
        "focusTag": f.get("tag"),
        "focusEditable": f.get("editable") is True,
        "target": r.get("target"),
        "injectTook": inj.get("took"),
        "injectionSilent": r.get("injectionSilent") is True,
        "spyInstalled": (r.get("spy") or {}).get("installed") is True,
        "eventsSeen": r.get("eventsSeen"),
        "keysSeen": r.get("keysSeen"),
        "targetCE": r.get("targetCE"),
        "defaultPrevented": r.get("defaultPrevented"),
        "deskOpen": r.get("deskOpen"),
        "panelPresent": r.get("panelPresent"),
        "outcome": r.get("outcome"),
        # ★ 间谍收不到事件 ⟹ dp/targetCE 结构上不可读，而**读不到本身是证据**
        "spySawNothing": r.get("spySawNothing") is True,
        "dpUnreadable": r.get("dpUnreadable"),
    }


tA = {k: [cellA(r) for r in v] for k, v in ga.items()}
tB = {k: [cellB(r) for r in v] for k, v in gb.items()}

# ── 每格的自证
for k, v in tA.items():
    for c in v:
        assert c["spyInstalled"] is True, "%s 间谍没装上" % (k,)
        assert c["eventsSeen"], "%s 间谍一个 keydown 都没收到" % (k,)
        assert c["defaultPrevented"] in (True, False), \
            "%s 读不到 defaultPrevented（探针 bug）" % (k,)
        assert c["targetCE"] in (True, False), \
            "%s 读不到 target.isContentEditable（探针 bug）" % (k,)
        assert c["selectedIds"], "%s 目标没选中 —— 这不是读数" % (k,)
        if k[1] in INJECT_ARMS:
            # ★ R99：注入必须真的生效，否则这一格**不算结果**
            assert c["injectionSilent"] is False, (
                "%s 注入静默没生效（targetCE 没翻成 true）—— 探针没报错不等于"
                "注入成功了" % (k,))
            assert c["injectTook"] is True, "%s 注入没 took" % (k,)
        if k[2] == "editable":
            assert c["focusEditable"] is True, "%s 落点类别与 want 不符" % (k,)
        else:
            # ★ 中性臂的落点**也是**非编辑框（它只换键，不换落点）⟹ 同样要自证
            assert c["focusEditable"] is False, "%s 落点类别与 want 不符" % (k,)
        if k[1] == "neutral":
            assert k[3] == NEUTRAL_KEY
for k, v in tB.items():
    for c in v:
        assert c["spyInstalled"] is True, "%s 间谍没装上" % (k,)
        assert c["outcome"] in ("deskGone", "layerClosedOnly", "nothing"), \
            "%s 三态读数不合法：%r" % (k, c["outcome"])
        if c["spySawNothing"]:
            # ★ 捕获阶段被掐断 ⟹ dp/targetCE **结构上不可读**，
            #   而「读不到」本身是证据，所以这两格不是失败格。
            assert c["eventsSeen"] == 0, \
                "%s 标了 spySawNothing 却还有 %d 个事件" % (k, c["eventsSeen"])
            assert c["defaultPrevented"] is None and c["targetCE"] is None, \
                "%s 间谍没收到事件却有 dp/targetCE" % (k,)
            assert c["dpUnreadable"], "%s 缺 dpUnreadable 的书面理由" % (k,)
        else:
            assert c["eventsSeen"], "%s 间谍一个 keydown 都没收到" % (k,)
            assert c["defaultPrevented"] in (True, False), \
                "%s 读不到 defaultPrevented（探针 bug）" % (k,)
            assert c["targetCE"] in (True, False), \
                "%s 读不到 target.isContentEditable（探针 bug）" % (k,)
        if k[1] == "alpha":
            assert c["injectionSilent"] is False, "%s 注入静默没生效" % (k,)
            assert c["injectTook"] is True, "%s 注入没 took" % (k,)

print("（阶段一）问① %d 格 × %d 轮、问② %d 格 × %d 轮，无失败；"
      "结构性 SKIP %d 格" % (len(ga), len(aR), len(gb), len(bR), len(sa)))


# ═══════════════ 2. 静态层 ═══════════════
def src_text(rel):
    p = REPO / rel
    if not p.exists():
        raise SystemExit("FATAL 缺源码 %s" % p)
    return p.read_text(encoding="utf-8")


def strip_comments(s):
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    return re.sub(r"//[^\n]*", "", s)

def blank_comments(s):
    """把注释字符替换成空格 —— **行数与偏移都不变**。

    ★ 为什么不能直接删：`DirectorTimeline.tsx` 里两行
      `window.addEventListener("keydown", closeOnEscape);` **文本完全相同**，
      任何「按行文本找位置」的做法（`txt.index(line)`）都会落到第一处，
      于是 preset 的主人会被认成 pathmenu 的（第一版就踩了这个）。
      按**行号**算偏移是唯一稳的，而行号只有在不删字符时才靠得住。
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


def line_offsets(s):
    off, acc = [0], 0
    for ln in s.split("\n"):
        acc += len(ln) + 1
        off.append(acc)
    return off




DD = src_text("src/components/director/DirectorDesk.tsx")
DDc = blank_comments(DD)   # ★ 抹白而不是删除：删注释会让行号漂移
ddLines = DDc.split("\n")
i0 = DDc.index("const handleKeyDown = (event: KeyboardEvent) => {")
i1 = DDc.index('window.addEventListener("keydown", handleKeyDown);')
kd = DDc[i0:i1]
kdLines = kd.split("\n")
guardRel = next((n for n, ln in enumerate(kdLines, 1)
                 if "if (isEditable) return;" in ln), None)
escStairRel = next((n for n, ln in enumerate(kdLines, 1)
                    if 'event.key !== "Escape"' in ln), None)
guardAbs = next((n for n, ln in enumerate(ddLines, 1)
                 if "if (isEditable) return;" in ln), None)
metaRel = next((n for n, ln in enumerate(kdLines, 1)
                if 'toLowerCase() === "c"' in ln), None)
delRel = next((n for n, ln in enumerate(kdLines, 1)
               if 'event.key === "Delete"' in ln), None)
pdRel = [n for n, ln in enumerate(kdLines, 1) if "event.preventDefault()" in ln]

# ── Escape「主人」普查：机械扫全树每一个 keydown 监听器
DIR = REPO / "src" / "components" / "director"
listeners = []
for p in sorted(DIR.glob("*.ts*")):
    txt = blank_comments(p.read_text(encoding="utf-8"))
    lines = txt.split("\n")
    off = line_offsets(txt)
    for n, ln in enumerate(lines, 1):
        if not re.search(r'addEventListener\(\s*"keydown"', ln):
            continue
        hm = re.search(r'addEventListener\(\s*"keydown"\s*,\s*([A-Za-z_$][\w$]*)',
                       ln)
        hname = hm.group(1) if hm else None
        tm = re.search(r'addEventListener\(\s*"keydown"\s*,\s*'
                       r'[A-Za-z_$][\w$]*\s*,\s*(\w+)', ln)
        addPos = off[n - 1]
        body = ""
        if hname:
            # ★ handler 名**在同一文件里可能重名** ⟹ 取「文本上在这次
            #   addEventListener **之前**、且离它最近的那次定义」
            best = None
            for dm in re.finditer(
                    r'(?:const|function)\s+%s\s*=?\s*'
                    r'(?:\([^)]*\)|function)?\s*(?:=>\s*)?'
                    r'(?::\s*[^{]+)?\s*\{' % re.escape(hname), txt):
                if dm.start() < addPos and (best is None
                                            or dm.start() > best.start()):
                    best = dm
            if best:
                depth, i = 0, best.end() - 1
                while i < len(txt):
                    if txt[i] == "{":
                        depth += 1
                    elif txt[i] == "}":
                        depth -= 1
                        if depth == 0:
                            break
                    i += 1
                body = txt[best.end() - 1:i + 1]
        listeners.append({
            "file": p.name, "line": n, "handler": hname,
            "phase": (tm.group(1) if tm else "bubble"),
            "hasEscape": "Escape" in body,
            "hasTabOnly": '!== "Tab"' in body,
            "hasPreventDefault": "preventDefault" in body,
            "hasStopImmediate": "stopImmediatePropagation" in body,
            "setters": sorted(set(re.findall(r"\b(set[A-Z]\w*)\s*\(", body))),
            "callsOnClose": "onClose(" in body,
        })

# ★ 没映射到层的 Escape 监听器，**每一个都要有书面理由**，
#   且这个集合本身要断言 —— 新增第 5 个「没人管的 Escape 监听器」时
#   汇编器必须变红，而不是静默通过（R100：静默丢掉一类就是丢一个结论）。
UNMAPPED_REASON = {
    ("DirectorDesk.tsx", "handleKeyDown"):
        "桌内那个阶梯本身（它就是被测对象，不是任何浮层的主人）",
    ("DirectorInspector.tsx", "handleKeyDown"):
        "关的是 setViewerCaptureId —— 取景器，不是六个浮层之一",
    ("DirectorObjectTree.tsx", "esc"):
        "关的是对象树的右键菜单，不是六个浮层之一",
    ("DirectorViewport.tsx", "handleKeyDown"):
        "★ 它是 **motionPathDraft 绘制态**的 Escape/Enter 处理器"
        "（只有 `timeline.motionPathDraft` 非空时才注册），"
        "**不是路径菜单的主人** —— 路径菜单的主人是 DirectorTimeline.tsx "
        "那个冒泡阶段的 closeOnEscape",
}

# 层 → state setter 的映射（**从源码数出来**，不手抄）
OWNER_BY_SETTER = {
    "setPathMenuLeft": "pathmenu",
    "setPresetPanelLeft": "preset",
    "setModelLibraryOpen": "modellib",
}
escOwners = {}
unmapped = []
for L in listeners:
    if not L["hasEscape"]:
        continue
    who = None
    for s in L["setters"]:
        if s in OWNER_BY_SETTER:
            who = OWNER_BY_SETTER[s]
            break
    if who is None and L["callsOnClose"] \
            and L["file"] == "DirectorPhoneVcamPanel.tsx":
        who = "phonevcam"
    if who is None:
        unmapped.append(L)
        continue
    assert who not in escOwners, "同一个层数出两个 Escape 主人 —— 机制要重查"
    escOwners[who] = {
        "file": L["file"], "line": L["line"],
        "phase": L["phase"], "capture": L["phase"] == "true",
        "preventDefault": L["hasPreventDefault"],
        "stopImmediatePropagation": L["hasStopImmediate"],
    }
assert sorted((L["file"], L["handler"]) for L in unmapped) == \
    sorted(UNMAPPED_REASON), (
        "★ 没映射到浮层的 Escape 监听器集合变了：多 %r / 少 %r —— "
        "**每一个都要有书面理由**，新增的要么归到某个层、要么补理由"
        % (sorted(set((L["file"], L["handler"]) for L in unmapped)
                  - set(UNMAPPED_REASON)),
           sorted(set(UNMAPPED_REASON)
                  - set((L["file"], L["handler"]) for L in unmapped))))
assert len(listeners) == 9, (
    "扫到 %d 个 keydown 监听器而不是 9 个 —— 导演台树里加了/减了键盘"
    "监听器，整批的静态前提要重查" % len(listeners))
layersWithOwner = sorted(escOwners)
layersWithoutOwner = sorted(set(IDS) - set(layersWithOwner))

static = {
    "guardLine": guardAbs,
    "guardIsEditableReturn": "if (isEditable) return;" in kd,
    "guardPredicateHasContentEditable": "target.isContentEditable" in kd,
    "guardPredicateHasTagNames": all(
        ('tagName === "%s"' % t) in kd for t in ("INPUT", "TEXTAREA", "SELECT")),
    "guardBeforeMetaC": (guardRel is not None and metaRel is not None
                         and guardRel < metaRel),
    "guardBeforeDelete": (guardRel is not None and delRel is not None
                          and guardRel < delRel),
    # ★ 问② 的全部要害：Escape 阶梯排在守卫**之后**
    "escapeStaircaseAfterGuard": (guardRel is not None and escStairRel is not None
                                  and escStairRel > guardRel),
    "escapeStaircaseLine": escStairRel,
    "preventDefaultLinesInHandler": pdRel,
    "deskListenerOnWindow": 'window.addEventListener("keydown", handleKeyDown);'
    in DDc,
    "deskListenerIsCapture": 'window.addEventListener("keydown", handleKeyDown, true)'
    in DDc,
    "allKeydownListenersInDirectorTree": listeners,
    "escapeOwners": escOwners,
    "escapeListenersNotOwnedByAnyLayer": [
        {"file": L["file"], "line": L["line"], "handler": L["handler"],
         "phase": L["phase"],
         "whyNotALayerOwner": UNMAPPED_REASON[(L["file"], L["handler"])]}
        for L in unmapped],
    "layersWithEscapeOwner": layersWithOwner,
    "layersWithoutEscapeOwner": layersWithoutOwner,
    "closeWorkspaceReachableFromLadder": "closeWorkspace();" in kd,
    "exportPanelLadderStep": 'if (exportPanelOpen) {' in kd,
}
assert static["guardIsEditableReturn"] is True, "守卫不在了 —— 整批要重查"
assert static["guardPredicateHasContentEditable"] is True, \
    "守卫判据里没有 isContentEditable —— α/β 两条注入路径都作废"
assert static["guardPredicateHasTagNames"] is True, \
    "守卫的标签名判据变了 —— 772/773 的结论要重查"
assert static["guardBeforeMetaC"] is True and static["guardBeforeDelete"] is True
assert static["escapeStaircaseAfterGuard"] is True, (
    "★ Escape 阶梯不在守卫之后了 —— 问② 的前提作废，整批要重查")
assert static["deskListenerOnWindow"] is True
assert static["deskListenerIsCapture"] is False, \
    "桌内那个改成捕获阶段了 —— 问② 的整张顺序表要重算"
assert static["closeWorkspaceReachableFromLadder"] is True
assert static["exportPanelLadderStep"] is True, \
    "Escape 阶梯里没有 exportPanelOpen 那一档 —— 问② 的 export 预测要重算"
# ★ 预测：恰好 4 个层自己有 Escape 主人，且分属**两种注册阶段**
assert layersWithOwner == ["modellib", "pathmenu", "phonevcam", "preset"], \
    "有主人的层不是这 4 个：%r —— 问② 的分组预测要重算" % (layersWithOwner,)
assert layersWithoutOwner == ["crowd", "export"], \
    "没主人的层不是这 2 个：%r —— 问② 的预测要重算" % (layersWithoutOwner,)
for w in ("modellib", "phonevcam"):
    assert escOwners[w]["capture"] is True, \
        "%s 的 Escape 主人不在捕获阶段 —— 它与桌内谁先跑要说清" % w
    assert escOwners[w]["stopImmediatePropagation"] is True, \
        "%s 的 Escape 主人没有 stopImmediatePropagation —— 桌内仍会跑到" % w
for w in ("pathmenu", "preset"):
    assert escOwners[w]["capture"] is False, "%s 的主人不是冒泡阶段" % w
    assert escOwners[w]["preventDefault"] is False, \
        "%s 的主人会 preventDefault —— dp 的读法要改" % w
print("（阶段二）静态层：守卫在第 %d 行、Escape 阶梯第 %d 行（守卫之后）；"
      "Escape 主人 %d 层（捕获+stop %d 层 / 冒泡无 preventDefault %d 层）、"
      "无主人 %d 层 %r"
      % (static["guardLine"], static["escapeStaircaseLine"], len(layersWithOwner),
         sum(1 for w in escOwners.values() if w["capture"]),
         sum(1 for w in escOwners.values() if not w["capture"]),
         len(layersWithoutOwner), layersWithoutOwner))


# ═══════════════ 3. 聚合 · 问① ═══════════════
def uniq(k, t=tA, field="defaultPrevented"):
    vs = {c[field] for c in t[k]}
    assert len(vs) == 1, "%s 两轮 %s 不一致：%r" % (k, field, vs)
    return vs.pop()


base = {(i,): None for i in IDS}
baseDp, baseCE, baseDelta = {}, {}, {}
for i in IDS:
    k = (i, "base", "noneditable", "Delete")
    baseDp[i] = uniq(k)
    baseCE[i] = uniq(k, field="targetCE")
    baseDelta[i] = sorted({c["objectsDelta"] for c in tA[k]})
# ★ 预测 A：无注入、落非编辑框 ⟹ Delete 分支跑到 ⟹ dp=true、targetCE=false
for i in IDS:
    assert baseDp[i] is True, (
        "%s 无注入却读到 dp=false —— 臂 A 是**同会话基线**，"
        "它不动就说明读数方法本身坏了（R99 的同族），后面所有对比都作废" % i)
    assert baseCE[i] is False, "%s 无注入却读到 targetCE=true" % i

alphaDp, alphaDelta, alphaSel, alphaCE = {}, {}, {}, {}
for i in IDS:
    for kk in KEYS:
        k = (i, "alpha", "noneditable", kk)
        alphaDp[(i, kk)] = uniq(k)
        alphaCE[(i, kk)] = uniq(k, field="targetCE")
        alphaDelta[(i, kk)] = sorted({c["objectsDelta"] for c in tA[k]})
        alphaSel[(i, kk)] = sorted({c["selectedDelta"] for c in tA[k]})
# ★ 预测 B：α 注入 ⟹ targetCE=true ⟹ 守卫在 :486 直接 return ⟹ 任何分支都到不了
for (i, kk) in alphaDp:
    assert alphaCE[(i, kk)] is True, (
        "%s/%s α 注入后 targetCE 仍是 false —— 注入没起作用，这一格不算结果" % (i, kk))
    assert alphaDp[(i, kk)] is False, (
        "★ %s/%s：守卫输入已是 isContentEditable=true，DirectorDesk.tsx:%d "
        "就该直接 return、任何分支都到不了，却读到 defaultPrevented=true —— "
        "机制读错了，要重查" % (i, kk, static["guardLine"]))
# ★ 预测 C：守卫一旦触发 ⟹ 可见后果全部消失
for (i, kk) in alphaDp:
    assert alphaDelta[(i, kk)] == [0], (
        "%s/%s：守卫触发后对象数仍变了 %r —— 「守卫一旦触发后果就没了」"
        "这条充分性被推翻" % (i, kk, alphaDelta[(i, kk)]))
    assert alphaSel[(i, kk)] == [0], (
        "%s/%s：守卫触发后选中集仍变了 %r" % (i, kk, alphaSel[(i, kk)]))

betaDp, betaCE, betaRoot, betaAct, betaDelta = {}, {}, {}, {}, {}
for i in IDS:
    k = (i, "beta", "noneditable", "Delete")
    betaDp[i] = uniq(k)
    betaCE[i] = uniq(k, field="targetCE")
    betaDelta[i] = sorted({c["objectsDelta"] for c in tA[k]})
    betaRoot[i] = {c["injectRootCE"] for c in tA[k]}
    betaAct[i] = {c["injectActiveCE"] for c in tA[k]}
# ★ 预测 D：β 的 isContentEditable **沿 DOM 继承**（本批唯一的浏览器行为假设）
for i in IDS:
    assert betaRoot[i] == {True}, "%s：浮层根 contentEditable 没生效 %r" % (i, betaRoot[i])
    assert betaAct[i] == {True}, (
        "★ %s：浮层根打了 contentEditable，**落点却没有继承到** isContentEditable"
        " —— 本批唯一的行为假设被推翻，β 这条注入路径作废" % i)
    assert betaCE[i] is True, "%s：β 落点 targetCE 仍非 true" % i
    assert betaDp[i] is False, "%s：β 下 Delete 分支仍跑到" % i
    assert betaDelta[i] == [0], "%s：β 下对象数仍变了" % i

neuDp, neuCE, neuKeys, neuEvents = {}, {}, {}, {}
for i in IDS:
    k = (i, "neutral", "noneditable", NEUTRAL_KEY)
    neuDp[i] = uniq(k)
    neuCE[i] = uniq(k, field="targetCE")
    neuKeys[i] = {tuple(c["keysSeen"] or ()) for c in tA[k]}
    neuEvents[i] = sorted({c["eventsSeen"] for c in tA[k]})
# ★ 预测 E（对 R86 的一次加强）：中性键那一格**不只看 dp=false**，
#   还要看**间谍确实收到了 F2**。只看 dp 的话，「注入把键投递本身弄坏」
#   也会得 false ⟹ 对照就废了。
for i in IDS:
    assert neuCE[i] is True, "%s：中性臂 targetCE 非 true" % i
    assert neuEvents[i] and all(e >= 1 for e in neuEvents[i]), \
        "%s：中性臂间谍没收到 keydown —— dp=false 可能只是「键没送到」" % i
    for ks in neuKeys[i]:
        assert NEUTRAL_KEY in ks, \
            "%s：中性臂键流里没有 %s：%r" % (i, NEUTRAL_KEY, ks)
    assert neuDp[i] is False, (
        "★ 中性键 %s 竟读到 dp=true —— 说明有人在桌内那个处理器**之前**"
        "就调了 preventDefault()，那么「dp=true 就等于分支跑了」"
        "这条推理**不成立**，整批要重查" % NEUTRAL_KEY)

betaEdDp, betaEdCE = {}, {}
for i in HAS_EDITABLE:
    k = (i, "beta", "editable", "Delete")
    betaEdDp[i] = uniq(k)
    betaEdCE[i] = uniq(k, field="targetCE")
# ★ 预测 F：β 不过宽 —— 落在**本来就该触发**守卫的可编辑控件上，β 不改变结果
for i in HAS_EDITABLE:
    assert betaEdCE[i] is True, "%s：β×可编辑落点 targetCE 非 true" % i
    assert betaEdDp[i] is False, \
        "%s：β 让桌内守卫在**可编辑控件**上反而没触发 —— β 改变了它不该改的" % i

alphaBlocksAll = sorted("%s/%s" % k for k in alphaDp)
alphaDpAllFalse = sorted("%s/%s" % k for k, v in alphaDp.items()
                          if v is False)   # ★ 两边都必须是字符串 ——
                          #   元组列表与字符串列表比永远不等（774 第一版）
assert len(alphaBlocksAll) == 30, "臂 B 格数应为 30，实为 %d" % len(alphaBlocksAll)
assert alphaBlocksAll == alphaDpAllFalse, "臂 B 里有哪一格没被挡住"

q1 = {
    "perCell": {"%s/%s/%s/%s" % k: {
        "targetCE": alphaCE[(k[0], k[3])],
        "defaultPrevented": alphaDp[(k[0], k[3])],
        "objectsDelta": alphaDelta[(k[0], k[3])],
        "selectedDelta": alphaSel[(k[0], k[3])]} for k in tA if k[1] == "alpha"},
    "sameSessionBaseline": {
        "arm": "base（无注入，落非编辑框，按 Delete）",
        "cells": len(baseDp),
        "defaultPreventedTrue": sum(1 for v in baseDp.values() if v is True),
        "targetCEAllFalse": all(v is False for v in baseCE.values()),
        "perDisclosure": {i: {"dp": baseDp[i], "targetCE": baseCE[i],
                              "objectsDelta": baseDelta[i]} for i in IDS},
        "why": "★ 不是引用 773 的历史读数，而是**当场重测**：用一个可能已经"
               "坏掉的读数方法去验上一批的结论，等于没验（R99 的同族）。"},
    "armA_baseline": {"cells": len(baseDp), "allDpTrue": all(
        v is True for v in baseDp.values())},
    "armB_alphaBlocks": {
        "cells": len(alphaDp), "allDpFalse": all(
            v is False for v in alphaDp.values()),
        "allTargetCETrue": all(v is True for v in alphaCE.values()),
        "allObjectsDeltaZero": all(v == [0] for v in alphaDelta.values()),
        "allSelectedDeltaZero": all(v == [0] for v in alphaSel.values()),
        "claim": "★ 守卫一旦在浮层后代上触发，%d/%d 格 defaultPrevented 全为 "
                 "false、对象数与选中集**零变化** ⟹ 方向① 对 D14 是**充分的**"
                 % (len(alphaDpAllFalse), len(alphaDp))},
    "armC_betaInheritance": {
        "cells": len(betaDp), "rootCETrue": len(betaRoot),
        "landingInherits": len(betaAct),
        "allDpFalse": all(v is False for v in betaDp.values()),
        "claim": "★ `isContentEditable` 沿 DOM **继承**：浮层根打上 "
                 "`contenteditable` 后，%d/%d 个浮层的落点都继承到 true ⟹ "
                 "「整层一个谓词」这个形状**可实现**，而这正是方向① 的形状"
                 % (len(betaAct), len(betaDp))},
    "armD_neutralControl": {
        "cells": len(neuDp), "allDpFalse": all(v is False for v in neuDp.values()),
        "allTargetCETrue": all(v is True for v in neuCE.values()),
        "spySawNeutralKey": all(all(
            NEUTRAL_KEY in ks for ks in neuKeys[i]) for i in IDS),
        "claim": "★ 中性键 %s 在 α 注入下**间谍确实收到了它**、且 dp=false ⟹ "
                 "注入没有把键投递本身弄坏（R86 的加强版：不只看 dp，还要看"
                 "间谍收没收到）" % NEUTRAL_KEY},
    "armE_betaNotOverbroad": {
        "cells": len(betaEdDp), "allDpFalse": all(
            v is False for v in betaEdDp.values()),
        "claim": "β 落在**本来就该触发**守卫的可编辑控件上，%d/%d 格结果不变 "
                 "⟹ β 不过宽" % (len(betaEdDp), len(betaEdDp))},
    "sufficiency": {
        "proved": "「守卫一旦在浮层后代上触发，D14 的全部可见后果就消失」"
                  "（臂 B %d/%d + 臂 C %d/%d）"
                  % (len(alphaDpAllFalse), len(alphaDp), len(betaDp), len(betaDp)),
        "notProved": "「方向① 的谓词能正确识别『焦点在浮层内』」—— "
                     "**那必须改 src/**，注入验不到（注入只能让既有谓词为真，"
                     "不能造出一个新的谓词）。攒为拍板项。",
    },
}
print("（阶段三·问①）臂 A 基线 %d/%d 格 dp=true｜臂 B α 注入 %d/%d 格 dp=false "
      "且对象数/选中集零变化｜臂 C β 继承 %d/%d｜臂 D 中性 %d/%d｜臂 E %d/%d"
      % (sum(1 for v in baseDp.values() if v is True), len(baseDp),
         len(alphaDpAllFalse), len(alphaDp), len(betaAct), len(betaDp),
         len(neuDp), len(neuDp), len(betaEdDp), len(betaEdDp)))


# ═══════════════ 4. 聚合 · 问② ═══════════════
esc = {}
for i in IDS:
    for arm in ("none", "alpha"):
        k = (i, arm)
        esc[(i, arm)] = {
            "targetCE": uniq(k, t=tB, field="targetCE"),
            "dp": uniq(k, t=tB),
            "outcome": uniq(k, t=tB, field="outcome"),
            "deskOpen": uniq(k, t=tB, field="deskOpen"),
            "panelPresent": uniq(k, t=tB, field="panelPresent"),
            "spySawNothing": uniq(k, t=tB, field="spySawNothing"),
        }
# ★ 预测 G：守卫输入随注入翻 ⟹ **间谍收到事件的那些格**逐格匹配。
#   「间谍没收到」的格 `targetCE` 结构上不可读，不参与这条预测 ——
#   但它们参与下面那条更强的**交叉预测**。
SAW_NONE = sorted({i for i in IDS
                   if esc[(i, "alpha")]["spySawNothing"] is True})
for (i, arm), v in esc.items():
    if v["spySawNothing"] is True:
        continue
    want = (arm == "alpha")
    assert v["targetCE"] is want, \
        "%s/%s：targetCE=%r 而预测是 %r" % (i, arm, v["targetCE"], want)
# ★ 预测 H（**交叉**）：「间谍收不到事件」的层集合，**恰好等于**
#   「静态普查里主人在捕获阶段」的层集合 —— 两条独立路径（源码扫描 vs
#   运行时观测）得出同一个集合，才算真的对上了。
CAPTURE_OWNED = sorted(w for w in layersWithOwner
                       if escOwners[w]["capture"])
assert SAW_NONE == CAPTURE_OWNED, (
    "★ 「间谍收不到事件」的层是 %r，而静态普查里主人在捕获阶段的是 %r —— "
    "两条独立路径对不上，其中一条的读法错了" % (SAW_NONE, CAPTURE_OWNED))
for w in CAPTURE_OWNED:
    for arm in ("none", "alpha"):
        v = esc[(w, arm)]
        assert v["spySawNothing"] is True, (
            "%s 的主人在捕获阶段且带 stopImmediatePropagation ⟹ 间谍"
            "（window 冒泡）应当收不到事件，却收到了" % w)
        assert v["dp"] is None, "%s/%s：间谍没收到却有 dp=%r" % (w, arm, v["dp"])
        assert v["deskOpen"] is True, "%s/%s：导演台没了" % (w, arm)
        assert v["panelPresent"] is False, "%s/%s：层没关" % (w, arm)
# ★ 预测 I：冒泡阶段主人（preset/pathmenu）⟹ 桌内**先**跑完阶梯 ⟹ D8
for w in ("pathmenu", "preset"):
    v0 = esc[(w, "none")]
    assert v0["dp"] is True, "%s：无注入时桌内 Delete/Escape 阶梯应跑到" % w
    assert v0["outcome"] == "deskGone", (
        "★ %s：无注入时桌内那个处理器在**冒泡阶段**先跑完整个 Escape 阶梯"
        "（那两个主人的 useEffect 在浮层打开后才注册 ⟹ 排在挂载时注册的"
        "桌内监听器**之后**），于是 %r 之外的工作区也该没 —— 实测 %r"
        % (w, "层", v0["outcome"]))
# ★ 预测 J：export 靠桌内 :559 那一档（无自己的主人）
vE = esc[("export", "none")]
assert vE["dp"] is True and vE["outcome"] == "layerClosedOnly", \
    "export 无注入时应只关面板、导演台还在，实测 dp=%r outcome=%r" % (
        vE["dp"], vE["outcome"])
# ★ 预测 K：crowd 没有主人 ⟹ 桌内一路 fall through ⟹ D8
vC = esc[("crowd", "none")]
assert vC["dp"] is True and vC["outcome"] == "deskGone", \
    "crowd 无注入时应丢整个工作区（D8），实测 dp=%r outcome=%r" % (
        vC["dp"], vC["outcome"])

# ── ★ 本批最值钱的发现：方向① 对 Escape 不是干净的
#   四桶而不是三桶 —— 「修好 D8」与「引入死键」**不是同一件事**
#   （crowd 两件都占了），压进一个桶就会把 crowd 说成纯收益。
q2Effects = {}
for i in IDS:
    a, b = esc[(i, "none")], esc[(i, "alpha")]
    sig = lambda z: (z["dp"], z["outcome"], z["deskOpen"],  # noqa: E731
                     z["panelPresent"])
    if sig(a) == sig(b):
        effect = "noChange"
    elif a["outcome"] == "deskGone" and b["outcome"] == "layerClosedOnly":
        effect = "fixesD8Cleanly"      # 纯收益：工作区不丢、层照关
    elif a["outcome"] == "deskGone" and b["outcome"] == "nothing":
        effect = "fixesD8ButDeadKey"   # **两件都占**：工作区不丢了，但成死键
    else:
        effect = "regression"          # 纯损失：本来能关的面板关不掉了
    q2Effects[i] = {
        "escapeOwner": escOwners.get(i),
        "noInjection": a, "withAlpha": b, "effect": effect}
byEffect = {}
for i, v in q2Effects.items():
    byEffect.setdefault(v["effect"], []).append(i)
assert sorted(byEffect.get("noChange", [])) == ["modellib", "phonevcam"], \
    "「对方向① 无变化」的不是捕获阶段那两个：%r" % (byEffect.get("noChange"),)
assert sorted(byEffect.get("fixesD8Cleanly", [])) == ["pathmenu", "preset"], \
    "「纯粹修好 D8」的不是冒泡阶段那两个：%r" % (
        byEffect.get("fixesD8Cleanly"),)
assert sorted(byEffect.get("fixesD8ButDeadKey", [])) == ["crowd"], \
    "「修好 D8 但成死键」的不是 crowd：%r" % (
        byEffect.get("fixesD8ButDeadKey"),)
assert sorted(byEffect.get("regression", [])) == ["export"], \
    "「纯回归」的不是 export：%r" % (byEffect.get("regression"),)
# ★ 分类必须**铺满**：四个桶的并集恰好是 6 个浮层，且每桶非空
assert sorted(i for v in byEffect.values() for i in v) == sorted(IDS), \
    "四桶的并集没有铺满 6 个浮层：%r" % sorted(byEffect)
# 预测 M：export 尤其要紧 —— 它的「关面板」能力**只能**来自桌内那一档
assert q2Effects["export"]["withAlpha"]["outcome"] == "nothing" and \
    q2Effects["export"]["withAlpha"]["dp"] is False and \
    q2Effects["export"]["withAlpha"]["panelPresent"] is True, \
    "★ export 在方向① 之后不该变成死键，实测 %r" % (
        q2Effects["export"]["withAlpha"],)
assert q2Effects["crowd"]["withAlpha"]["outcome"] == "nothing" and \
    q2Effects["crowd"]["withAlpha"]["deskOpen"] is True, \
    "crowd 在方向① 之后不该从「丢工作区」变成「按了没反应」，实测 %r" % (
        q2Effects["crowd"]["withAlpha"],)

q2 = {
    "perCell": {"%s/%s" % k: v for k, v in esc.items()},
    "byDisclosure": q2Effects,
    "groups": {k: sorted(v) for k, v in sorted(byEffect.items())},
    "escapeOwnersStatic": escOwners,
    "layersWithoutEscapeOwner": layersWithoutOwner,
    "crossCheck": {
        "spySawNothingLayers": SAW_NONE,
        "capturePhaseOwnerLayers": CAPTURE_OWNED,
        "match": SAW_NONE == CAPTURE_OWNED,
        "claim": "★ 「间谍（window 冒泡）收不到 Escape」的层集合，**恰好等于**"
                 "「静态普查里 Escape 主人在捕获阶段」的层集合 —— 两条独立"
                 "路径（源码扫描 / 运行时观测）得出同一个集合。",
        "note": "这 %d 格的 `defaultPrevented` 与 `targetCE` **结构上不可读**："
                "事件在到达 window 冒泡之前就被 `stopImmediatePropagation()` "
                "掐断了。三态读数不依赖间谍，那 %d 格才是它们真正的测量。"
                "第一版把这类格判成 FAILED（「读数不算数」），是分类错误 —— "
                "**把一条发现写成了失败**（R97）。"
                % (len(SAW_NONE) * 2, len(SAW_NONE) * 2)},
    "headline": "★ 方向① **不是**一道干净的守卫：对 C/V/Z/Y/Delete 五支是纯"
                "收益，对 Escape 那支则分**四**种后果 —— "
                "2 层无变化、2 层纯粹修好 D8、1 层修好 D8 但成死键、"
                "1 层纯回归（**export 丢掉「关导出面板」这个能力**）。",
    "whyFourBuckets": "★ 第一版只分了**三**桶（把「deskGone → nothing」和"
                      "「deskGone → layerClosedOnly」都算成「修好 D8」），"
                      "于是 crowd 被说成纯收益。**「工作区不丢了」与「成了死键」"
                      "是两件事**，压进一个桶就会丢掉一半后果。分类的桶数本身"
                      "就是结论的一部分。",
    "consequence": "⟹ 修法必须**分段**：C/V/Z/Y/Delete 各自加「焦点在浮层内"
                   "就早退」；**Escape 阶梯不能共用那道守卫**——它需要的"
                   "是另一条规则（焦点在浮层内时**不 fall through 到 "
                   "closeWorkspace()**），而那条规则与 D8 的修法**是同一处**。",
    "newDefect": "★ 独立于 D8 的新发现：**2/6 个浮层（export、crowd）"
                 "根本没有自己的 Escape 主人**。capture 阶段有主人的只有 "
                 "2 个（modellib、phonevcam），冒泡阶段有主人的 2 个"
                 "（preset、pathmenu）**自己管不了工作区**（桌内先跑）"
                 "——「层内 Escape 能不能只关层」这件事，全族只有 2/6 做对了。",
}
print("（阶段四·问②）无注入：deskGone %d 层、layerClosedOnly %d 层、"
      "nothing %d 层｜注入 α 后：deskGone %d、layerClosedOnly %d、nothing %d"
      % (sum(1 for a in (esc[(i, "none")] for i in IDS)
             if a["outcome"] == "deskGone"),
         sum(1 for a in (esc[(i, "none")] for i in IDS)
             if a["outcome"] == "layerClosedOnly"),
         sum(1 for a in (esc[(i, "none")] for i in IDS)
             if a["outcome"] == "nothing"),
         sum(1 for a in (esc[(i, "alpha")] for i in IDS)
             if a["outcome"] == "deskGone"),
         sum(1 for a in (esc[(i, "alpha")] for i in IDS)
             if a["outcome"] == "layerClosedOnly"),
         sum(1 for a in (esc[(i, "alpha")] for i in IDS)
             if a["outcome"] == "nothing")))


# ═══════════════ 5. 判据 + 发现 ═══════════════
judgments = [
    {"id": "J1", "q": "问①", "claim": "方向① 对 D14 是**充分的**：守卫一旦在"
     "浮层后代上触发，D14 的全部可见后果消失（臂 B %d/%d 格 dp=false 且"
     "对象数/选中集零变化）" % (len(alphaDpAllFalse), len(alphaDp)),
     "evidence": {"armB": q1["armB_alphaBlocks"], "armC": q1["armC_betaInheritance"]},
     "boundary": "**只证充分性，不证识别性** —— 谓词该怎么写要改 src/"},
    {"id": "J2", "q": "问①", "claim": "`isContentEditable` 沿 DOM **继承**，"
     "所以「整层一个谓词」（方向① 的形状）**可实现**：浮层根打 "
     "`contenteditable` 后 %d/%d 个浮层的落点继承到 true"
     % (len(betaAct), len(betaDp)),
     "evidence": {"inheritance": q1["armC_betaInheritance"]},
     "boundary": "继承成立只说明**形状可实现**，不说明形状**正确**"},
    {"id": "J3", "q": "问①", "claim": "臂 A 同会话基线 %d/%d 格 dp=true ⟹ "
     "读数方法本身还活着（不是引用 773 的历史读数）"
     % (sum(1 for v in baseDp.values() if v is True), len(baseDp)),
     "evidence": {"baseline": q1["sameSessionBaseline"]},
     "boundary": "无"},
    {"id": "J4", "q": "问①", "claim": "注入没把键投递本身弄坏：中性键 %s 在 α "
     "注入下**间谍确实收到了它**且 dp=false（%d/%d）"
     % (NEUTRAL_KEY, len(neuDp), len(neuDp)),
     "evidence": {"control": q1["armD_neutralControl"]},
     "boundary": "R86 的加强版：只看 dp 的话「键没送到」也会得 false"},
    {"id": "J5", "q": "问②", "claim": "无注入时，落点非可编辑的浮层内按 "
     "Escape：%d 层丢整个工作区（D8）、%d 层只关层、%d 层死键"
     % (sum(1 for a in (esc[(i, "none")] for i in IDS)
            if a["outcome"] == "deskGone"),
        sum(1 for a in (esc[(i, "none")] for i in IDS)
            if a["outcome"] == "layerClosedOnly"),
        sum(1 for a in (esc[(i, "none")] for i in IDS)
            if a["outcome"] == "nothing")),
     "evidence": {"perDisclosure": {i: esc[(i, "none")] for i in IDS}},
     "boundary": "三态读数，缺一不可（R97 的同族）"},
    {"id": "J6", "q": "问②", "claim": "★ **2/6 个浮层（export、crowd）没有"
     "自己的 Escape 主人** ⟹ 「层内 Escape 只关层」全族只有 2/6 做对了",
     "evidence": {"owners": escOwners, "without": layersWithoutOwner,
                  "perDisclosure": {i: esc[(i, "none")] for i in IDS}},
     "boundary": "静态结论由机械普查得出（扫全树每一个 keydown 监听器）"},
    {"id": "J7", "q": "问②", "claim": "★ **方向① 不是一道干净的守卫**：捕获"
     "阶段有主人的 2 层无变化、冒泡阶段有主人的 2 层**纯粹修好 D8**、"
     "crowd 修好 D8 但**成了死键**、**export 纯回归**（丢掉「关导出面板」"
     "这个能力）—— 四种后果，**分四桶**",
     "evidence": {"groups": q2["groups"], "perDisclosure": q2Effects},
     "boundary": "结论只覆盖「焦点落在层内第一个非可编辑控件」这一个落点"},
    {"id": "J8", "q": "问②", "claim": "⟹ 修法必须**分段**：Escape 阶梯**不能**"
     "共用「焦点在浮层内就早退」那道守卫，它需要另一条规则"
     "（焦点在浮层内时不 fall through 到 `closeWorkspace()`），"
     "而那条规则与 D8 的修法**是同一处**",
     "evidence": {"consequence": q2["consequence"]},
     "boundary": "属拍板项，**未改 src/**"},
]
# ★ 每条判据带 `verdict` 与 `evidenceKey`（指回自己的 id）——
#   验收器会**独立从 raw 重算**一遍再与 `evidence` 对账，
#   所以这个索引是必要的（不能只靠「产物自己说的」）。
for j in judgments:
    j["verdict"] = "PASS"
    j["evidenceKey"] = j["id"]
assert sorted(j["id"] for j in judgments) == \
    ["J%d" % i for i in range(1, len(judgments) + 1)], "判据 id 不连续"
for j in judgments:
    assert j["evidence"], "%s 没有 evidence" % j["id"]
EVIDENCE_INDEX = {j["id"]: j["evidence"] for j in judgments}

findings = {
    "F1": "★ 更正 D14 修法方向① 的性质：它**充分但不干净**。对 C/V/Z/Y/Delete "
          "五支是纯收益（%d/%d 格 dp 从 true 变 false、零副作用）；"
          "对 Escape 那支会**拆掉 export 的面板关闭**。"
          % (len(alphaDpAllFalse), len(alphaDp)),
    "F2": "★ 独立于 D8 的新发现：**export 与 crowd 根本没有自己的 Escape "
          "主人**。捕获阶段有主人的只有 2/6（modellib、phonevcam），"
          "冒泡阶段有主人的 2/6（preset、pathmenu）**自己管不了工作区**"
          "——桌内那个挂载时就注册、排在它们前面。",
    "F3": "「层内 Escape 只关层」这件事，**全族只有 2/6 做对了**"
          "（modellib、phonevcam）。其余 4 个要么丢工作区，要么死键。",
    "F4": "`isContentEditable` 沿 DOM 继承**实测成立**（%d/%d）⟹ 方向① 的"
          "「整层一个谓词」形状可实现，不需要逐个控件打标。"
          % (len(betaAct), len(betaDp)),
    "F5": "「守卫一旦触发后果就没了」是**充分性**，不是识别性。识别性"
          "（「谓词该不该这么写」）必须改 src/，注入验不到——"
          "因为注入只能让**既有**谓词为真，造不出一个新的谓词。",
    "F6": "R86 的加强：阴性对照**不能只看 dp**。「注入把键投递弄坏」与"
          "「桌内不处理该键」都会得 dp=false ⟹ 必须同时断言"
          "**间谍确实收到了那个键**。",
    "F7": "R96 的机械化：探针的每个臂要**逐臂断言非空**。773 的教训是"
          "「for 循环的补丁没落进文件 ⟹ 那一臂一次都没跑，"
          "而探针不报错、汇编器也不报」。",
    "F8": "复用探针基础设施要**逐字节复制**。本批第一版从 read 输出重打"
          "`settle()`，漏掉 `querySelector(` 的右括号，3 格冒烟就撞上；"
          "内联 JS 应该在跑之前先过一遍 `node --check`。",
}
for i, j in enumerate(judgments):
    assert j["evidence"], "J%d 没有 evidence" % (i + 1)
assert set(findings) == {"F%d" % (i + 1) for i in range(len(findings))}

# ── 探针教训：机制失效要沉淀成教训，不只是修好
probeLessons = [
    {"id": "R100",
     "lesson": "阴性对照**不能只看 `defaultPrevented`**。「注入把键投递本身弄坏」"
               "与「桌内那个处理器不处理这个键」**都会得 dp=false** ⟹ 必须同时"
               "断言**间谍确实收到了那个键**（`keysSeen` 里真的有它）。",
     "why": "本批的 α/β 注入只写 `contentEditable` 属性，理论上不该动键投递——"
            "但「理论上」不是读数。臂 D 那 6 格就是为此存在的。",
     "fixInProbe": "臂 D 同时断言 `eventsSeen>=1` 与 `NEUTRAL_KEY in keysSeen`"},
    {"id": "R101",
     "lesson": "探针的**每个臂都要逐臂断言非空**（R96 的机械化）。",
     "why": "773 的 `for want in (...)` 补丁没落进文件 ⟹ 中性臂一次都没跑，"
            "而**探针不报错、汇编器也不报**。",
     "fixInProbe": "汇编器对 base/alpha/beta/neutral 四个臂逐个 `assert got`"},
    {"id": "R102",
     "lesson": "★ 静态扫描里**按 handler 名找函数体在同名时必错**，且"
               "**不能按行文本定位**——同名的 `addEventListener(...)` 行文本"
               "完全相同，`str.index` 会落到第一处。",
     "why": "`DirectorTimeline.tsx` 有两个 `closeOnEscape`；第一版把 preset 的"
            "主人认成了 pathmenu（两处都踩了：正则取文件里第一个定义 + "
            "`txt.index` 找行位置）。",
     "fixInProbe": "注释**抹白而不删**（行数与偏移不变）→ 按**行号**算偏移 → "
                   "取「文本上在这次 addEventListener **之前**且离它最近」的"
                   "那次定义；并断言未映射的每个监听器都有书面理由"},
]
# ── 更正：不是改历史批次的数字，而是**改一条挂着的拍板项的措辞**
corrections = [
    {"id": "C774-1",
     "targets": ["772 的拍板项「D14 修法」第 1 条",
                 "763 挂起的方向（把 isEditable 早退的判据实际换掉）"],
     "was": "「Delete/Backspace/Cmd+C/V/Z/Y **整段**移进『焦点在某个浮层内就"
            "早退』的守卫」——**整段**这个词把 Escape 也算进去了。",
     "now": "★ 那道守卫**不能**整段前移。`DirectorDesk.tsx` 的 `if (isEditable) "
            "return;` 排在**所有分支之前**，Escape 阶梯也在它后面；实测（%d/%d "
            "格）一旦守卫在浮层后代上触发，**export 的面板就再也关不掉**（变死键），"
            "crowd 则从「丢工作区」变成「按了没反应」。修法必须**分段**："
            "C/V/Z/Y/Delete 各自加守卫，Escape 阶梯另给一条规则。"
            % (sum(1 for v in q2Effects.values()
                   if v["withAlpha"]["outcome"] == "nothing"), len(IDS)),
     "evidence": "J7 + J8"},
]
observations = [
    {"o": 1, "text": "★ 问① 的答案干净得反常：α 注入 30/30 格、β 注入 6/6 格，"
                     "`targetCE` 一翻成 true，`defaultPrevented` 就**无一例外**变 "
                     "false，对象数与选中集**零变化**。守卫是充分且唯一的闸门。"},
    {"o": 2, "text": "`isContentEditable` 沿 DOM 继承**实测成立**（6/6）——"
                     "方向① 的「整层一个谓词」形状可实现，不必逐个控件打标。"},
    {"o": 3, "text": "★ 六个浮层的 Escape 主人是**三种不同的注册阶段**，而后果"
                     "完全由注册阶段决定：捕获+stop 的 2 个层桌内收不到事件；"
                     "冒泡无 stop 的 2 个层**自己管不了工作区**（桌内挂载时就注册、"
                     "排在它们前面）；**没有主人的 2 个层**则一路 fall through。"},
    {"o": 4, "text": "★ 方向① 的净后果分三组：2 层无变化、2 层修好 D8、2 层**回归**。"
                     "**「一道守卫统一修六处」这个直觉在 Escape 那支上是错的。**"},
    {"o": 5, "text": "问① 证明了**充分性**，问② 证明了**不干净**——两问合起来才"
                     "够支撑一条修法。缺问② 就会把 export 的回归带上线。"},
]
assert len(observations) >= 3
assert [c["id"] for c in corrections] == ["C774-1"]
assert [x["id"] for x in probeLessons] == ["R100", "R101", "R102"]

audit = {
    "batch": 774,
    "topic": "D14 修法方向① 的注入对照：充分性够不够，Escape 会不会被误伤",
    "generatedBy": "probes/mk774audit.py",
    "sources": {"vb774a.json": {"sha16": sha(A_p), "rounds": len(aR),
                                "rowsPerRound": _nA},
                "vb774b.json": {"sha16": sha(B_p), "rounds": len(bR),
                                "rowsPerRound": _nB}},
    "questions": {
        "Q1": "方向①（「把 isEditable 早退的判据从按标签名换成按浮层」）"
              "够不够？—— 注入 contentEditable 让那道守卫在浮层后代上真的触发，"
              "**一行 src/ 都不改**",
        "Q2": "方向① 会不会把 Escape 阶梯一起挡掉？—— `:486` 的守卫排在"
              "**所有分支之前**，Escape 阶梯也在它后面",
    },
    "comparability": comparability,
    "static": static,
    "q1": q1,
    "q2": q2,
    "evidenceIndex": EVIDENCE_INDEX,
    "judgments": judgments,
    "findings": findings,
    "probeLessons": probeLessons,
    "corrections": corrections,
    "observations": observations,
    "defects": [],
    "defectNote": "本批**不新增用户可见缺陷**。① 问① 验的是「修法够不够」，"
                  "不是「现在有没有坏」。② 无注入时 preset/pathmenu/crowd 三层"
                  "按 Escape 丢整个工作区 —— 那是 D8（768 记的 3/6），本批把它"
                  "**定位到具体是哪三层**，不另立新号。③ 「2/6 个浮层没有自己的"
                  "Escape 主人」是**结构事实**；它在用户侧的后果分两种 —— export "
                  "靠桌内那一档恰好能用（脆弱但能用），crowd 的后果就是 D8。",
    "rawSha": {"vb774a.json": sha(A_p), "vb774b.json": sha(B_p)},
    "srcDiff": "**本批未改 `src/`**（提交前 `git diff --stat HEAD -- src/` 为 0 行）",
    "boundary": comparability["boundary"],
}
OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote %s" % OUT)
