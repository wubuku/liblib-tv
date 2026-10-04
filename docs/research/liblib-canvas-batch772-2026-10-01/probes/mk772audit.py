#!/usr/bin/env python3
"""batch 772 汇编器：从 raw/vb772a.json 现算 runtime-audit.json

## 这一批问的

767–771 连续五批都在 disclosure 浮层的**焦点围栏**上。D8（按 Esc 丢整个
工作区）是「窗口级处理器抢在浮层前面动手」的一个**实例**。本批问它的
**同族**，而且是带**破坏性**的那一族：

  **浮层开着、焦点落在浮层里某个控件上时，导演台的全局快捷键会不会照样生效？**

## 机制（静态可查，本批逐字读过）

`DirectorDesk.tsx:473-571` 在 **window、冒泡**阶段注册**一个** keydown 处理器，
管的不止 Escape：`:490-516` 是 `Meta/Ctrl + C/V/Z/Y`，`:517-548` 是
**`Delete` / `Backspace` → `deleteDirectorEntity()`**（真删东西）。

唯一的挡板是 `:487` 的 `if (isEditable) return;`，而 `isEditable` 只认
`isContentEditable` 与 `INPUT/TEXTAREA/SELECT`（`:475-480`）。

**导演台开着时，主画布页自己那条 Delete 路径是死的** ——
`src/app/page.tsx:1306-1310` 的 `handleKeyDown` 第一句业务判断就是
`if (uiState.activeDirectorNodeId) return;`。所以活路径**只有一条**，
机制上没有第二条。

## 规矩（沿用 756–771）

1. **数字不许手抄** —— 每个数从 raw 现算；静态事实当场读源码数出来。
2. **缺原始读数判失败**。
3. **`findings[k] == judgments[i].evidence`**，写盘前断言，验收器再查一遍。
4. **先证明可比再谈一致**（R55）：逐轮归一化 diff。
5. **`all([])` 是 True**：每处聚合显式判非空；分类必须**铺满**格子。
6. **破坏性的读数要先有阳性对照**：Delete 分支只在**有选中**时才动手，
   「按了没反应」可能只是「本来就没选中」。每一格都要自证**选中真的成了**。
7. **「撤销没生效」也要有设置对照**（R86）：臂 4 每次都先在**树上**删掉一个
   对象并**确认对象数真的掉了**，没掉就判该格失败。
8. **静态断言的方向要写对**（R92）：期望与事实相反时，要写成**产物里的更正**，
   不是崩掉的断言。
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
MODES = [
    ("del-noneditable", "noneditable", "Delete"),
    ("bs-noneditable", "noneditable", "Backspace"),
    ("del-editable", "editable", "Delete"),
    ("undo-noneditable", "noneditable", "Meta+z"),
]
HAS_EDITABLE = {"export", "crowd", "modellib"}
# 全部格（含 3 个结构性 SKIP）
CELLS = [(i, m) for i in IDS for m, _, _ in MODES]
SKIP_CELLS = [(i, "del-editable") for i in IDS if i not in HAS_EDITABLE]
RUN_CELLS = [k for k in CELLS if k not in SKIP_CELLS]
# 破坏性的三条臂（del/bs × 落点）—— undo 单独算
DESTRUCTIVE = [(i, m) for i in IDS
               for m in ("del-noneditable", "bs-noneditable", "del-editable")
               if (i, m) in RUN_CELLS]


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


# ═══════════════ 1. 读原始读数（**两个探针合并**） ═══════════════
# ★ 772a 有一处**排序 bug**：它先选中相机、再去点第一个对象，把相机顶掉了，
#   于是 preset 的触发器重新变 disabled、3 格全 FAILED。那 3 格**不作废**，
#   由 772b 用正确顺序重取；772a 的其余读数**全部保留**。
#   772a 的另外两格（pathmenu 的 del/bs）**不作废也不采信为「没穿透」** ——
#   772a 自己无法区分「快捷键没进去」与「相机不可删」，归因交给 772b 的
#   cam-deletable-control 对照格。
A, A_p = load("vb772a.json")
B, B_p = load("vb772b.json")
for nm, raw in (("772a", A), ("772b", B)):
    rs = raw.get("rounds") or []
    assert len(rs) == 2, "%s 轮数 %d" % (nm, len(rs))
aR, bR = A["rounds"], B["rounds"]


def grid(raw, keyfn):
    g = {}
    for rd in raw["rounds"]:
        for r in rd.get("rows") or []:
            g.setdefault(keyfn(r), []).append(r)
    return g


ga = grid(A, lambda r: (r.get("id"), r.get("mode")))
gb = grid(B, lambda r: tuple((r.get("plan") or "").split("/"))
          if r.get("plan") != "cam-deletable-control"
          else ("cam", "deletable-control"))

aFailed = {k for k, v in ga.items() for r in v if r.get("FAILED")}
aSkip = {k for k, v in ga.items() for r in v if r.get("SKIPPED")}
assert aFailed == {("preset", m) for m in
                   ("del-noneditable", "bs-noneditable", "undo-noneditable")}, \
    "772a 的失败格与已知的排序 bug 不符：%r" % (sorted(aFailed),)
for k in aFailed:
    assert k in gb, "772a 的失败格 %r 没有被 772b 补上 —— 判失败" % (k,)
for k, v in gb.items():
    for r in v:
        assert not r.get("FAILED"), "772b 有失败格 %r: %s" % (k, r["FAILED"])
    assert len(v) == 2, "772b %s 轮数 %d" % (k, len(v))
for k, v in ga.items():
    assert len(v) == 2, "772a %s 轮数 %d" % (k, len(v))
    if k in aFailed:
        continue                      # 已知排序 bug，由 772b 取代
    for r in v:
        assert not r.get("FAILED"), \
            "772a 有失败格 %r 且没被 772b 覆盖 —— 判失败" % (k,)

# ── 合并：772b 的格覆盖 772a 的同名格
merged = {}
provenance = {}
for k, v in ga.items():
    if k in aSkip:
        continue
    if k in aFailed:
        continue
    merged[k] = v
    provenance["%s/%s" % k] = "772a"
for k, v in gb.items():
    if k == ("cam", "deletable-control"):
        merged[k] = v
        provenance["%s/%s" % k] = "772b"
        continue
    merged[k] = v
    provenance["%s/%s" % k] = "772b"
assert len(merged) == len(RUN_CELLS) + 1, (
    "合并后格数 %d，期望 %d（%d 个实验格 + 1 个对照格；`del-editable` "
    "在 3 个没有可编辑控件的浮层上是结构性 SKIP）"
    % (len(merged), len(RUN_CELLS) + 1, len(RUN_CELLS)))

_provA = sum(1 for v in provenance.values() if v == "772a")
_provB = sum(1 for v in provenance.values() if v == "772b")

comparability = {
    "allConsistent772a": round_diff(A, "rows")[0] is True,
    "allConsistent772b": round_diff(B, "rows")[0] is True,
    "firstDiff772a": {} if round_diff(A, "rows")[0] is True
                     else {"rows": round_diff(A, "rows")[1]},
    "firstDiff772b": {} if round_diff(B, "rows")[0] is True
                     else {"rows": round_diff(B, "rows")[1]},
    "rounds": len(aR),
    "cellsPerRound772a": len(aR[0]["rows"]),
    "cellsPerRound772b": len(bR[0]["rows"]),
    "mergedCells": len(merged),
    "provenance": provenance,
    "cellsFrom772a": _provA,
    "cellsFrom772b": _provB,
    "protocol": "★ 每格都从**重新加载的页面**开始（768 的 R73）并清空"
                "localStorage 的导演台项目键；每格开头都**点选**一个对象并回读"
                " `selectedIds` —— Delete/Undo 分支只在有选中时才动手，"
                "**选中没成立就不是读数**（规矩 6）。",
    "superseded": {
        "cells": sorted("%s/%s" % k for k in aFailed),
        "why": "772a 的排序 bug：`ensure_camera()` 之后又去点了第一个对象，"
               "把刚选中的相机顶掉 ⟹ preset 触发器重新 disabled。",
        "fixedBy": "772b：对 needs==cameraTrack 的浮层，**被删目标就用相机"
                   "本身**，点一次同时满足「触发器可用」与「有选中」。",
        "keptFrom772a": "772a 的其余 %d 格**全部保留**，不作废。"
                        "★ 注意 pathmenu 的 3 格也来自 **772b**（772b 覆盖了"
                        "772a 的同名格）—— provenance 是现算的，不是手算的。"
                        % _provA,
    },
    "boundary": "只点对象树的行、6 个 disclosure 触发器、选中相机；"
                "**不点提交/连接/添加，更不做付费或真实生图生视频**。"
                "Delete 是被测行为，破坏只存在于探针这一页内。",
    "deskGoneAfter772a": [rd.get("deskGoneAfter") for rd in aR],
    "deskGoneAfter772b": [rd.get("deskGoneAfter") for rd in bR],
}
assert comparability["allConsistent772a"], comparability["firstDiff772a"]
assert comparability["allConsistent772b"], comparability["firstDiff772b"]


def cell(r):
    b, a = r.get("before") or {}, r.get("after") or {}
    selB = r.get("selectedBeforeKey")
    if selB is None:
        selB = b.get("selectedIds")
    selA = r.get("selectedAfterKey")
    if selA is None:
        selA = a.get("selectedIds")
    dl = r.get("delta") or {}
    return {
        "key": r.get("key"),
        "layer": r.get("layer") or r.get("id"),
        "focus": r.get("focus"),
        "target": r.get("target"),
        "selectedAfterSelect": r.get("selectedAfterSelect")
                               or r.get("selectedBefore"),
        "selectedBeforeKey": selB,
        "selectedAfterKey": selA,
        "objectsBefore": b.get("objectCount"),
        "objectsAfter": a.get("objectCount"),
        "nodesBefore": b.get("nodeCount"),
        "nodesAfter": a.get("nodeCount"),
        "deltaObjects": dl.get("objects"),
        "deltaNodes": dl.get("nodes"),
        "objectsDropped": r.get("objectsDropped"),
        "selectionCleared": r.get("selectionCleared"),
        "restored": r.get("restored"),
        "setup": r.get("setup"),
        "layerStillOpen": r.get("layerStillOpen"),
        "deskStillOpen": r.get("deskStillOpen"),
        "focusAfter": r.get("focusAfter"),
    }


t = {k: [cell(r) for r in v] for k, v in merged.items()}

# ── 每格的自证：按��那一刻**真的有选中**
for k, v in t.items():
    for c in v:
        assert c["selectedBeforeKey"], \
            "%s/%s 按键时没有选中 —— 这不是读数（规矩 6）" % (k[0], k[1])
        assert c["focus"] and not c["focus"].get("err"), \
            "%s/%s 焦点没放进去" % (k[0], k[1])
for k in DESTRUCTIVE:
    for c in t[k]:
        assert c["selectedBeforeKey"] is not None, \
            "%s/%s 缺按键前选中的读数" % (k[0], k[1])

print("（阶段一）合并完成：%d 格 = %d 实验格 + 1 对照格；"
      "来源 772a %d 格 / 772b %d 格"
      % (len(merged), len(RUN_CELLS), _provA, _provB))


# ═══════════════ 2. 静态层 ═══════════════
def src_text(rel):
    p = REPO / rel
    if not p.exists():
        raise SystemExit("FATAL 缺源码 %s" % p)
    return p.read_text(encoding="utf-8")


def strip_comments(s):
    return re.sub(r"//[^\n]*", "", s)


DD = src_text("src/components/director/DirectorDesk.tsx")
PG = src_text("src/app/page.tsx")
SEL = src_text("src/lib/libtvSelectionCommandContext.ts")
DDc, PGc, SELc = strip_comments(DD), strip_comments(PG), strip_comments(SEL)
i0 = DDc.index("const handleKeyDown = (event: KeyboardEvent) => {")
i1 = DDc.index('window.addEventListener("keydown", handleKeyDown);')
kd = DDc[i0:i1]
p0 = PGc.index("const handleKeyDown = (event: KeyboardEvent) => {")
p1 = PGc.index('window.addEventListener("keydown", handleKeyDown);', p0)
pgkd = PGc[p0:p1]
s0 = SELc.index("export function isLibTVEditableCommandTarget(")
s1 = SELc.index("\n}", s0)
sgt = SELc[s0:s1]

static = {
    # ── 桌内那一个处理器
    "deskListenerOnWindow": 'window.addEventListener("keydown", handleKeyDown)'
                            in DDc,
    "deskListenerIsCapture":
        'window.addEventListener("keydown", handleKeyDown, true)' in DDc,
    "deskKeydownListenerCount": DDc.count('addEventListener("keydown"'),
    "deskListenerCountInHandler": kd.count('addEventListener("keydown"'),
    # ── 唯一的挡板
    "guardIsEditableReturn": bool(re.search(r"if \(isEditable\) return;", kd)),
    "guardBeforeDelete": kd.index("if (isEditable) return;") < kd.index(
        'event.key === "Delete"'),
    "isEditableCovers": sorted(set(re.findall(
        r"target\.tagName === \"(\w+)\"", kd))),
    "isEditableHasContentEditable": "target.isContentEditable" in kd,
    # ── 破坏性分支
    "deleteBranchPresent": 'event.key === "Delete" || event.key === "Backspace"'
                           in kd,
    "deleteCallsEntity": "deleteDirectorEntity(" in kd,
    "deleteHasWorkspaceBusyGuard": "workspaceBusy" in kd,
    "deleteHasViewerGuard":
        'document.querySelector("[data-director-capture-viewer]")' in kd,
    "deleteGuardedBySelection": "directorState.selectedObjectIds.length" in kd,
    # ── 其余全局键
    "modifierKeys": sorted(set(re.findall(
        r'event\.key\.toLowerCase\(\) === "(\w)"', kd))),
    # ── 主画布页那条 Delete 路径在导演台开着时是死的
    "pageHandlerReturnsWhenDeskOpen":
        bool(re.search(r"if \(uiState\.activeDirectorNodeId\) return;", pgkd)),
    "pageDeletePresent": 'event.key === "Delete" || event.key === "Backspace"'
                         in pgkd,
    "pageGuardBeforeDelete":
        pgkd.index("activeDirectorNodeId") < pgkd.index('event.key === "Delete"'),
    # ── 两道守卫不等价（观察项）
    "pageGuardSelector": "input:not([type='button'])" in sgt
                         or 'input:not([type=\'button\']' in sgt,
    "pageGuardExcludesFileInput": "type='file'" in sgt
                                   or "type=\\'file\\'" in sgt,
    "pageGuardCoversRoleTextbox": "role='textbox'" in sgt
                                   or "role=\\'textbox\\'" in sgt,
    "deskGuardIsTagNameOnly": "closest(" not in kd,
}
assert static["deskListenerOnWindow"] is True
assert static["deskKeydownListenerCount"] == 1, \
    "DirectorDesk 里的 keydown 监听不止一个 —— 机制结论要重查"
assert static["deskListenerIsCapture"] is False, \
    "桌内那一个变成捕获阶段了 —— 机制结论要重查"
assert static["guardIsEditableReturn"] is True
assert static["guardBeforeDelete"] is True, \
    "isEditable 早退不在 Delete 分支之前 —— 机制要重查"
assert static["deleteBranchPresent"] is True
assert static["deleteCallsEntity"] is True
assert static["deleteGuardedBySelection"] is True
assert static["pageHandlerReturnsWhenDeskOpen"] is True, \
    "主画布页那条 Delete 不再在导演台开着时早退 ⟹ 可能存在第二条活路径"
assert static["pageGuardBeforeDelete"] is True
assert static["pageDeletePresent"] is True
print("（阶段二）静态层：桌内 %d 个 keydown 监听（window 冒泡）、"
      "挡板 = isEditable 早退、主画布页 Delete 在桌开时已死 = %s"
      % (static["deskKeydownListenerCount"],
         static["pageHandlerReturnsWhenDeskOpen"]))


# ═══════════════ 3. 聚合 ═══════════════
def derived(c):
    """派生出两个信号（772a 没自报 `selectionCleared`，现算，不采信）。"""
    b, a = c["selectedBeforeKey"], c["selectedAfterKey"]
    return {"objectsDropped": (c["deltaObjects"] or 0) < 0,
            "selectionCleared": bool(b) and not a,
            "selectionUnchanged": b == a}


for k, v in t.items():
    for c in v:
        c["derived"] = derived(c)

DEL = [(i, "del-noneditable") for i in IDS]
BS = [(i, "bs-noneditable") for i in IDS]
ED = [(i, "del-editable") for i in sorted(HAS_EDITABLE)]
UNDO = [(i, "undo-noneditable") for i in IDS]
# 这两个浮层的触发器必须选中相机才能开 ⟹ 按键时的目标**只能是相机**
CAM_ONLY = {"preset", "pathmenu"}
MEASURABLE = [k for k in DEL + BS if k[0] not in CAM_ONLY]
CONFOUNDED = [k for k in DEL + BS if k[0] in CAM_ONLY]

leak = {}
for k in DEL + BS:
    ds = [c["derived"] for c in t[k]]
    leak["%s/%s" % k] = {
        "probe": comparability["provenance"]["%s/%s" % k],
        "deltaObjects": sorted({c["deltaObjects"] for c in t[k]}),
        "targetAtKeyTime": sorted({str(c["selectedBeforeKey"])
                                   for c in t[k]}),
        "objectsDropped": all(d["objectsDropped"] for d in ds),
        "selectionCleared": all(d["selectionCleared"] for d in ds),
        "classifiable": k[0] not in CAM_ONLY,
    }
for k, v in leak.items():
    if v["classifiable"]:
        assert v["objectsDropped"] is True, \
            "%s 可判但没删掉东西 —— 结论要重查" % (k,)
        assert v["selectionCleared"] is True, \
            "%s 可判但选中没被清空 —— 结论要重查" % (k,)

guard = {}
for k in ED:
    ds = [c["derived"] for c in t[k]]
    guard["%s/%s" % k] = {
        "probe": comparability["provenance"]["%s/%s" % k],
        "deltaObjects": sorted({c["deltaObjects"] for c in t[k]}),
        "focusEditable": all((c["focus"] or {}).get("editable") is True
                             for c in t[k]),
        "blocked": all(not d["objectsDropped"] and d["selectionUnchanged"]
                       for d in ds),
    }
for k, v in guard.items():
    assert v["focusEditable"] is True, "%s 落点不是可编辑控件" % (k,)
    assert v["blocked"] is True, "%s 落在输入框上却还是删了 —— 守卫失效" % (k,)

undo = {}
for k in UNDO:
    setups = [c["setup"] for c in t[k]]
    ok_setup = all(
        (s or {}).get("objectsAfter") is not None
        and (s["objectsAfter"] < s["objectsBefore"]) for s in setups)
    assert ok_setup, "%s/undo 的设置没自证（树上 Delete 没删掉）—— 判失败" % (k[0],)
    undo["%s/%s" % k] = {
        "probe": comparability["provenance"]["%s/%s" % k],
        "setup": setups,
        "deltaObjects": sorted({c["deltaObjects"] for c in t[k]}),
        "restored": all(c["restored"] is True for c in t[k]),
    }
    assert undo["%s/%s" % k]["restored"] is True, \
        "%s/undo 在浮层里没恢复 —— 与结论相反" % (k[0],)

ctrl = t[("cam", "deletable-control")]
control = {
    "focus": ctrl[0]["focus"],
    "targetAtKeyTime": ctrl[0]["selectedBeforeKey"],
    "deltaObjects": sorted({c["deltaObjects"] for c in ctrl}),
    "selectionUnchanged": all(c["derived"]["selectionUnchanged"]
                              for c in ctrl),
    "objectsDropped": any(c["derived"]["objectsDropped"] for c in ctrl),
    "note": "★ 这一格是 772a 留下的悬案的钥匙：pathmenu 两格「没删对象」"
            "到底是快捷键没进去，还是相机不可删？本格把焦点放在**任何浮层之外**"
            "的对话框控件（`aria-label=关闭`）上、只按 `Delete` —— "
            "相机**删不掉** ⟹ 那两格是**结构上不可判**，不是「这条路是好的」。",
}
assert control["objectsDropped"] is False, \
    "相机居然删得掉 ⟹ CONFOUNDED 的分类作废，要重查"

deskGone = [x for x in (comparability["deskGoneAfter772a"]
                       + comparability["deskGoneAfter772b"]) if x]
leakage = {
    "perCell": leak, "guard": guard, "undo": undo, "control": control,
    "leakedDisclosures": sorted({k.split("/")[0] for k, v in leak.items()
                                 if v["classifiable"] and v["objectsDropped"]}),
    "leakedCells": sorted(k for k, v in leak.items()
                          if v["classifiable"] and v["objectsDropped"]),
    "classifiableCells": sorted(k for k, v in leak.items()
                                if v["classifiable"]),
    "confoundedCells": sorted(k for k, v in leak.items()
                              if not v["classifiable"]),
    "undoLeakedCells": sorted(k for k, v in undo.items() if v["restored"]),
    "guardBlockedCells": sorted(k for k, v in guard.items() if v["blocked"]),
    "deskGoneAfter": deskGone,
    "theseKeysDoNotCloseDesk": not deskGone,
    "perDisclosure": {
        i: {"delDropped": leak["%s/del-noneditable" % i]["objectsDropped"],
            "bsDropped": leak["%s/bs-noneditable" % i]["objectsDropped"],
            "classifiable": leak["%s/del-noneditable" % i]["classifiable"],
            "undoRestored": undo["%s/undo-noneditable" % i]["restored"],
            "guardBlocked": ("%s/del-editable" % i) in guard}
        for i in IDS},
}
assert len(leakage["leakedCells"]) == 8, \
    "实测穿透的破坏性格数不对：%d" % len(leakage["leakedCells"])
assert len(leakage["undoLeakedCells"]) == 6
assert len(leakage["guardBlockedCells"]) == 3
print("（阶段三）穿透：Delete/Backspace %d/%d 可判格（%d 个浮层）｜"
      "结构上不可判 %d 格｜undo %d/6｜守卫挡住 %d/3"
      % (len(leakage["leakedCells"]),
         len(leakage["classifiableCells"]),
         len(leakage["leakedDisclosures"]),
         len(leakage["confoundedCells"]),
         len(leakage["undoLeakedCells"]),
         len(leakage["guardBlockedCells"])))


# ═══════════════ 4. findings ═══════════════
findings = {
    "F0_comparable": {
        "allConsistent772a": comparability["allConsistent772a"],
        "allConsistent772b": comparability["allConsistent772b"],
        "rounds": comparability["rounds"],
        "cellsPerRound772a": comparability["cellsPerRound772a"],
        "cellsPerRound772b": comparability["cellsPerRound772b"],
        "mergedCells": comparability["mergedCells"],
        "provenance": comparability["provenance"],
        "superseded": comparability["superseded"],
        "note": "两个探针各 2 轮，逐格归一化后 diff 均为空（R55）。",
    },
    "F1_selfProven": {
        "claim": "★ 每格按键那一刻**真的有选中**（Delete/Undo 分支的前提）",
        "cellsChecked": len(RUN_CELLS) * 2,
        "allHadSelection": all(c["selectedBeforeKey"]
                                for v in t.values() for c in v),
        "why": "没有选中时 Delete 分支在 `objectIds.length > 0` 处就返回，"
               "「按了没反应」会是**退化情况**而不是「没穿透」（规矩 6）。",
    },
    "F2_deleteLeaks": {
        "claim": "★ 浮层开着、焦点落在**非编辑框**控件上时，`Delete` 会"
                 "**真的删掉**导演台里选中的对象",
        "leakedCells": leakage["leakedCells"],
        "leakedDisclosures": leakage["leakedDisclosures"],
        "classifiableCells": leakage["classifiableCells"],
        "perCell": {k: leak[k] for k in leakage["classifiableCells"]},
        "deltaObjects": sorted({tuple(v["deltaObjects"])
                                for k, v in leak.items()
                                if v["classifiable"]}),
        "targetDeleted": sorted({t[tuple(k.split("/"))][0]
                                 ["selectedBeforeKey"][0]
                                 for k in leakage["leakedCells"]}),
    },
    "F3_backspaceLeaks": {
        "claim": "`Backspace` 走的是**同一条**分支（`:517` 的 `||`），结论相同",
        "cells": sorted(k for k in leakage["leakedCells"]
                        if k.endswith("/bs-noneditable")),
        "sameDeltaAsDelete": all(
            leak[k]["deltaObjects"]
            == leak[k.replace("bs-", "del-")]["deltaObjects"]
            for k in leak if k.endswith("/bs-noneditable")),
        "note": "★ 这不是「顺手也测了」——两条臂的 `deltaObjects` 逐格相同，"
                "**同一个症状、同一条代码路径**，符合 R60 的判别式。",
    },
    "F4_isEditableGuardHolds": {
        "claim": "★ 对照：焦点落在浮层内的**可编辑**控件上时，Delete **被挡住**",
        "cells": leakage["guardBlockedCells"],
        "perCell": guard,
        "focusWasEditable": all(v["focusEditable"] for v in guard.values()),
        "deltaObjects": sorted({tuple(v["deltaObjects"])
                                for v in guard.values()}),
        "note": "这一格是 769 量的那道 `isEditable` 早退（`DirectorDesk.tsx:487`）。"
                "**它只挡住输入框，挡不住按钮。**",
    },
    "F5_undoLeaks": {
        "claim": "★ 浮层开着时 `Meta+Z` 会**撤销掉工作区里已经发生过的删除**",
        "cells": leakage["undoLeakedCells"],
        "perCell": undo,
        "setupAlwaysVerified": True,
        "setupShape": sorted({str(v["setup"][0]) for v in undo.values()}),
        "note": "每格都先在**树上**删掉一个对象并**自证**对象数真的掉了"
                "（5→4），才去浮层里按 `Meta+Z`（R86）。"
                "6/6 全部恢复到 5。",
    },
    "F6_confounded": {
        "claim": "★ preset / pathmenu 的 4 个 Delete 格**结构上不可判**"
                 "（不是「没穿透」）",
        "confoundedCells": leakage["confoundedCells"],
        "why": "这两个浮层的触发器**必须选中主机位**才能开（否则 `disabled`），"
               "而打开它们还会把选中**换成主机位**（772a 读数："
               "`selectedIds` 从角色变成 `['director-camera-main']`）。"
               "⟹ 按键时的目标**只能是相机**，而相机**不可删**（见 F7）。",
        "whatWouldMakeItDecidable": "项目里有**第二台相机**、或开这两个浮层时"
                                    "仍能保持一个**可删对象**的选中。",
    },
    "F7_cameraUndeletable": {
        "claim": "★ 对照格：相机**根本删不掉**（这才是 F6 的原因）",
        "focus": control["focus"],
        "focusWasOutsideAnyLayer": True,
        "targetAtKeyTime": control["targetAtKeyTime"],
        "deltaObjects": control["deltaObjects"],
        "selectionUnchanged": control["selectionUnchanged"],
        "objectsDropped": control["objectsDropped"],
        "note": "焦点放在 `aria-label=关闭` 的按钮上（**任何浮层之外**），"
                "只按 `Delete` ⟹ 对象没少、选中没变。"
                "**没有这一格，F6 就会被误读成「这条路是好的」。**",
    },
    "F8_deskNotClosed": {
        "claim": "★ 这三个键**不会**关掉导演台 —— 与 D8 的 Esc 路径不是一回事",
        "deskGoneAfter": leakage["deskGoneAfter"],
        "noneClosedTheDesk": leakage["theseKeysDoNotCloseDesk"],
        "note": "D8 是「按 Esc 丢整个工作区」；本批量到的三个键都是"
                "**改内容但不关工作区**。两条路径的**后果类型不同**，"
                "修法也不同，别混为一谈。",
    },
    "F9_singleLivePath": {
        "claim": "★ 机制：导演台开着时，`Delete` 的活路径**只有一条**",
        "deskKeydownListeners": static["deskKeydownListenerCount"],
        "deskListenerOnWindow": static["deskListenerOnWindow"],
        "deskListenerIsCapture": static["deskListenerIsCapture"],
        "pageDeleteExists": static["pageDeletePresent"],
        "pageReturnsWhenDeskOpen":
            static["pageHandlerReturnsWhenDeskOpen"],
        "pageGuardBeforeDelete": static["pageGuardBeforeDelete"],
        "why": "`src/app/page.tsx` 的 `handleKeyDown` 第一句业务判断就是 "
               "`if (uiState.activeDirectorNodeId) return;` ⟹ 导演台开着"
               "时主画布页自己那条 Delete 是**死的**。所以没有「第二条路径」"
               "这种解释空间。",
    },
    "F10_guardPosition": {
        "claim": "机制：唯一的挡板是 `if (isEditable) return;`，且它在 "
                 "Delete 分支**之前**",
        "guardIsEditableReturn": static["guardIsEditableReturn"],
        "guardBeforeDelete": static["guardBeforeDelete"],
        "isEditableCovers": static["isEditableCovers"],
        "isEditableHasContentEditable": static["isEditableHasContentEditable"],
        "deleteGuardedBySelection": static["deleteGuardedBySelection"],
        "deleteCallsEntity": static["deleteCallsEntity"],
        "modifierKeys": static["modifierKeys"],
    },
    "F11_twoGuardsDiffer": {
        "claim": "★ 观察：桌内那道 `isEditable` 与主画布页那道**不等价**",
        "deskGuardIsTagNameOnly": static["deskGuardIsTagNameOnly"],
        "pageGuardExcludesFileInput": static["pageGuardExcludesFileInput"],
        "pageGuardCoversRoleTextbox": static["pageGuardCoversRoleTextbox"],
        "consequenceToday": "**没有可观测后果** —— 主画布页那条 Delete 在桌开"
                            "时是死的（F9）。本批的 `del-editable` 对照格落在"
                            "模型库那个 `sr-only` 的 `type=file` 上（769 的 "
                            "D12 同一个控件），桌内那道守卫认它 ⟹ 被挡住。",
        "latentRisk": "哪天主画布页那条 Delete 复活，"
                      "`input[type=file]` 就会从「被当编辑框」变成"
                      "「不是编辑框」⟹ 在模型库里按 Delete 会删对象。",
    },
}


# ═══════════════ 5. 判据 ═══════════════
judgments = [
    {"id": "J1",
     "statement": "两个探针的读数各自两轮逐格一致（可比性）",
     "verdict": "PASS" if (comparability["allConsistent772a"]
                           and comparability["allConsistent772b"]) else "FAIL",
     "evidenceKey": "F0_comparable", "evidence": findings["F0_comparable"]},
    {"id": "J2",
     "statement": "★ 合并后 22 格无缺格无失败格；772a 的 3 个失败格"
                  "**逐个**被 772b 取代，且 772a 的其余读数**全部保留**",
     "verdict": "PASS" if (len(comparability["provenance"]) == 22
                           and len(comparability["superseded"]["cells"]) == 3)
                else "FAIL",
     "evidenceKey": "F0_comparable", "evidence": findings["F0_comparable"]},
    {"id": "J3",
     "statement": "★ 每格按键那一刻**真的有选中**（否则「没反应」是退化情况）",
     "verdict": "PASS" if findings["F1_selfProven"]["allHadSelection"]
                else "FAIL",
     "evidenceKey": "F1_selfProven", "evidence": findings["F1_selfProven"]},
    {"id": "J4",
     "statement": "★ 问：`Delete` 穿透 —— 落非编辑框时 **4/4 个可判浮层"
                  "真的删掉了选中对象**（Δ对象 = −1，选中被清空）",
     "verdict": "PASS" if len(findings["F2_deleteLeaks"]["leakedCells"]) == 8
                else "FAIL",
     "evidenceKey": "F2_deleteLeaks", "evidence": findings["F2_deleteLeaks"]},
    {"id": "J5",
     "statement": "`Backspace` 与 `Delete` 逐格 Δ 相同 ⟹ 同一条代码路径"
                  "（R60 的判别式：不是「顺手测了」）",
     "verdict": "PASS" if findings["F3_backspaceLeaks"]["sameDeltaAsDelete"]
                else "FAIL",
     "evidenceKey": "F3_backspaceLeaks",
     "evidence": findings["F3_backspaceLeaks"]},
    {"id": "J6",
     "statement": "★ 对照组：落**可编辑**控件时 3/3 被 `isEditable` 早退挡住",
     "verdict": "PASS" if (len(leakage["guardBlockedCells"]) == 3
                           and findings["F4_isEditableGuardHolds"]
                           ["focusWasEditable"]) else "FAIL",
     "evidenceKey": "F4_isEditableGuardHolds",
     "evidence": findings["F4_isEditableGuardHolds"]},
    {"id": "J7",
     "statement": "★ preset / pathmenu 的 4 个 Delete 格判为"
                  "**结构上不可判**，不是「没穿透」",
     "verdict": "PASS" if len(leakage["confoundedCells"]) == 4 else "FAIL",
     "evidenceKey": "F6_confounded", "evidence": findings["F6_confounded"]},
    {"id": "J8",
     "statement": "★ 对照格：相机**删不掉**（焦点在浮层之外、只按 Delete）"
                  "⟹ J7 的归因成立",
     "verdict": "PASS" if (control["objectsDropped"] is False
                           and control["selectionUnchanged"] is True)
                else "FAIL",
     "evidenceKey": "F7_cameraUndeletable",
     "evidence": findings["F7_cameraUndeletable"]},
    {"id": "J9",
     "statement": "★ `Meta+Z` 穿透 —— **6/6 个浮层**都撤销掉了工作区里"
                  "已经发生的删除（每格 setup 自证 5→4）",
     "verdict": "PASS" if len(leakage["undoLeakedCells"]) == 6 else "FAIL",
     "evidenceKey": "F5_undoLeaks", "evidence": findings["F5_undoLeaks"]},
    {"id": "J10",
     "statement": "★ 这三个键**一个都没**关掉导演台 ⟹ 与 D8 的 Esc 路径"
                  "是两类后果",
     "verdict": "PASS" if leakage["theseKeysDoNotCloseDesk"] else "FAIL",
     "evidenceKey": "F8_deskNotClosed", "evidence": findings["F8_deskNotClosed"]},
    {"id": "J11",
     "statement": "★ 机制：导演台开着时 `Delete` 的活路径**只有一条**"
                  "（主画布页那条已被 `activeDirectorNodeId` 早退掉）",
     "verdict": "PASS" if (static["deskKeydownListenerCount"] == 1
                           and static["pageHandlerReturnsWhenDeskOpen"]
                           and static["pageGuardBeforeDelete"]) else "FAIL",
     "evidenceKey": "F9_singleLivePath",
     "evidence": findings["F9_singleLivePath"]},
    {"id": "J12",
     "statement": "机制：唯一的挡板是 `if (isEditable) return;`，"
                  "且它在 Delete 分支**之前**",
     "verdict": "PASS" if (static["guardIsEditableReturn"]
                           and static["guardBeforeDelete"]
                           and static["deleteCallsEntity"]) else "FAIL",
     "evidenceKey": "F10_guardPosition",
     "evidence": findings["F10_guardPosition"]},
    {"id": "J13",
     "statement": "★ 观察：桌内那道 `isEditable` 与主画布页那道**不等价**"
                  "（本批无后果，属潜在风险）",
     "verdict": "PASS" if (static["deskGuardIsTagNameOnly"]
                           and static["pageGuardExcludesFileInput"]
                           and static["pageGuardCoversRoleTextbox"])
                else "FAIL",
     "evidenceKey": "F11_twoGuardsDiffer",
     "evidence": findings["F11_twoGuardsDiffer"]},
]

# ═══════════════ 6. audit ═══════════════
audit = {
    "batch": 772,
    "date": "2026-10-01",
    "scope": "浮层开着、焦点落在浮层内某个控件上时，导演台的全局快捷键"
             "（Delete / Backspace / Meta+Z）会不会照样生效 —— D8 的**破坏性同族**",
    "env": {"base": "http://localhost:4317", "canvas": "canvas-2",
            "viewport": "1440x1000（桌面）",
            "player": "chromium (playwright sync_api)", "srcModified": False},
    "probes": [
        {"id": "772a", "file": "probes/dbg772a.py", "raw": "raw/vb772a.json",
         "rounds": len(aR), "cells": comparability["cellsPerRound772a"],
         "note": "主网格：6 浮层 × 4 臂（其中 del-editable 在 3 个浮层上是"
                 "结构性 SKIP）。**有 3 格因排序 bug FAILED，见 superseded。**"},
        {"id": "772b", "file": "probes/dbg772b.py", "raw": "raw/vb772b.json",
         "rounds": len(bR), "cells": comparability["cellsPerRound772b"],
         "note": "补 preset 的 3 格 + pathmenu 的归因 + **一个相机可删性对照格**"},
    ],
    "rawSha": {A_p.name: sha(A_p), B_p.name: sha(B_p)},
    "comparability": comparability,
    "static": static,
    "leakage": leakage,
    "findings": findings,
    "judgments": judgments,
    "defects": [
        {"id": "D14", "severity": "中", "newInThisBatch": True,
         "relatedToD8From767": True, "relatedToD3From765": True,
         "title": "浮层开着时 `Delete` / `Backspace` / `Meta+Z` 会穿透进导演台："
                  "焦点落在浮层里的**按钮**上时，Delete 真的删掉工作区里选中的对象",
         "where": ["src/components/director/DirectorDesk.tsx:473-571",
                   "src/components/director/DirectorDesk.tsx:487",
                   "src/components/director/DirectorDesk.tsx:517-548"],
         "mechanism": "`DirectorDesk.tsx:570` 在 **window、冒泡**阶段注册"
                      "**一个** keydown 处理器。唯一的挡板是 `:487` 的 "
                      "`if (isEditable) return;`，而 `isEditable` 只认 "
                      "`isContentEditable` 与 `INPUT/TEXTAREA/SELECT`"
                      "（`:475-480`）⟹ **按钮一律不在保护范围内**。"
                      "于是 `:517` 的 `Delete || Backspace` 分支会走到 "
                      "`deleteDirectorEntity()`。`workspaceBusy` 与"
                      "拍摄预览两个守卫都**不会**在正常编辑态成立，"
                      "所以这条路径在**正常使用中就是活的**。",
         "measured": "6 个浮层里 **4 个**（导出 / 本机预演 / 群众阵列 / 模型库）"
                     "实测在落非编辑框时按 `Delete` 与 `Backspace` "
                     "**对象数各 −1、选中被清空**（8/8 可判格）；"
                     "落**可编辑**控件时 3/3 被挡住；"
                     "`Meta+Z` **6/6 个浮层**都撤销掉了工作区里已发生的删除。",
         "confounded": "preset 与路径菜单的 4 个 Delete 格**结构上不可判**："
                       "它们必须选中主机位才能开，打开时还会把选中换成主机位，"
                       "而**相机删不掉**（对照格实测）。"
                       "⟹ 本批**不声称**这两个浮层安全。",
         "consequence": "破坏性且**无确认框**（与主画布页 Batch 177 对齐源站的"
                        "「Delete 立即删除」一致）。不过可被 `Meta+Z` 撤回 —— "
                        "而 `Meta+Z` 本身也从浮层里穿透了，用户在浮层里根本"
                        "按不到正确的撤销入口。",
         "notTheSameAsD8": "★ D8 是「按 Esc **丢整个工作区**」；"
                           "本批这三个键是「**改内容但不关工作区**」。"
                           "两者的后果类型不同，修法也不同。",
         "fixDirection": [
             "① 把 `Delete`/`Backspace`/`Cmd+C/V/Z/Y` 整段移进"
             "「焦点在某个浮层内就早退」的守卫（等价于 767/769 已实测的"
             "`isEditable` 早退思路，但要按**浮层**判而不是按标签判）；",
             "② 或给 6 个浮层统一接一层**捕获阶段**的 keydown 拦截 + "
             "`stopImmediatePropagation()`（同仓已有两处现成配方："
             "`DirectorViewport.tsx:2734-2753`、"
             "`DirectorPhoneVcamPanel.tsx:286-296`）。",
             "两条都必须做；只做 ① 的话，将来新增的浮层仍会漏。",
         ]},
    ],
    "observations": [
        {"id": "O772-1",
         "text": "★ **同一个 `isEditable` 早退，在 Esc 上是「救命的」，"
                 "在 Delete 上是「漏的」。** 769 已实测：群众阵列在输入框上按 "
                 "Esc 什么都没发生（早退生效 ⟹ 导演台没被关掉）；"
                 "本批实测：同一个早退在 Delete 上放行了按钮。"
                 "**同一行代码，在一个键上是修复、在另一个键上是漏洞。**",
         "whyItMatters": "「已经有一个守卫了」是最容易让人停手的理由；"
                         "本批说明**守卫的作用域必须按键分别量**（R82 的又一次成立）。"},
        {"id": "O772-2",
         "text": "★ 三个浮层（预设运镜 / 创建运动轨迹 / 本机预演）"
                 "**一个可编辑控件都没有** ⟹ `isEditable` 在这三个里"
                 "**永远不可能成立** ⟹ 那道守卫对它们等于不存在。",
         "whyItMatters": "守卫的强度取决于**浮层里有没有输入框**。"
                         "只挑「有输入框的浮层」验收，会得到"
                         "「守卫是好的」的错误安心。"},
        {"id": "O772-3",
         "text": "★ 这三个键**一个都没**关掉导演台（4 轮全空）。"
                 "所以本批的 D14 与 D8 是**两类后果**：D8 丢工作区、"
                 "D14 丢内容但工作区还在。",
         "whyItMatters": "把两条路径合并成一个「Esc/快捷键会搞坏导演台」"
                         "会让修法选错 —— D8 要改 Esc 阶梯，"
                         "D14 要改的是按键的作用域。"},
        {"id": "O772-4",
         "text": "★ 桌内那道 `isEditable`（认**任何** INPUT，含 "
                 "`type=file`）与主画布页那道 "
                 "`isLibTVEditableCommandTarget`（**排除** `input[type=file]`、"
                 "且额外认 `[role=textbox]/[role=searchbox]/[role=combobox]`/"
                 "`[data-libtv-editor-root]`）**不等价**。"
                 "今天没有可观测后果（主画布页那条 Delete 在桌开时是死的）。",
         "whyItMatters": "本批的 `del-editable` 对照格正好落在模型库那个 "
                         "`sr-only` 的 `type=file` 上（769 的 D12 同一个控件）——"
                         "**桌内那道认它，所以挡住了。** 哪天主画布页那条"
                         "复活，同一个控件就会从「被当编辑框」翻成「不是编辑框」。"},
    ],
    "probeLessons": [
        {"id": "R94",
         "text": "★ **「没变化」有两种读法，必须用对照格分开。** 772a 的 "
                 "pathmenu 两格「按 Delete 没删对象」——可能是①快捷键没进去，"
                 "也可能是②目标根本删不掉。**只写「未观察到穿透」就是把 ① 和 ② "
                 "混成一句。** 修法：加一个**只隔离一个变量**的对照格"
                 "（焦点放在浮层之外、只按同一个键）——"
                 "本批测出「相机删不掉」，于是那两格被正名为"
                 "**结构上不可判**。",
         "whyItMatters": "「没有证据表明有洞」与「这里测不了」长得一模一样，"
                         "而它们导向完全相反的下一步（收工 vs 换实验设计）。"},
        {"id": "R95",
         "text": "★ **探针的设置步骤会污染后面的设置。** 772a 先 "
                 "`ensure_camera()` 再去点第一个对象 —— 那一��**把刚选中的"
                 "相机顶掉了**，preset 的触发器重新变 `disabled`，3 格全 FAILED。"
                 "**凡是「先布置 A、再布置 B」的设置，B 可能悄悄清掉 A。**",
         "whyItMatters": "它不会报错，只会安静地让一批格子失效。"
                         "判别式：**每一个设置动作之后都回读它自己的前提**"
                         "（本批的 `selectedIds` 就是那个回读点）。"},
        {"id": "R96",
         "text": "★ **一批读数失效时，不要整套重跑。** 772a 的 preset 3 格"
                 "失效，但它的另外 18 格**完全有效**。做法是**补一个探针"
                 "只重取失效的那几格**，在汇编器里**合并**并如实记下"
                 "「哪几格来自哪个探针、为什么被取代」。",
         "whyItMatters": "整套重跑会丢掉已经有效的读数、并把「为什么失效」"
                         "这段推理从产物里抹掉；而**失效的原因本身往往比"
                         "读数更有价值**（R95 就是这么沉淀下来的）。"},
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
      "观察 %d | 探针教训 %d"
      % (len(audit["judgments"]),
         sum(1 for j in judgments if j["verdict"] == "PASS"),
         sum(1 for j in judgments if j["verdict"] == "FAIL"),
         len(findings), len(audit["defects"]), len(audit["observations"]),
         len(audit["probeLessons"])))
print("穿透：%s" % (leakage["leakedDisclosures"],))
print("守卫对照：%s｜结构上不可判：%s"
      % (leakage["guardBlockedCells"], leakage["confoundedCells"]))
print("更正/取代：%s" % (comparability["superseded"]["cells"],))
