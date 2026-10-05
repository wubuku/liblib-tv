#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 778 汇编器 —— **`Cmd+Z` 在检查器控件上的早退，是「按设计」还是「缺陷」？
按控件类型拆开之后，我自己的规划假设被否掉了。**

## 本批要回答的

777 把「焦点在检查器输入框上时删除不可撤销」记成缺陷 **D1d（中-高）**。
我 778 规划时的假设是：

> D1d **过宽**。正确范围 = 「只有**没有原生撤销**的控件才是真空」⟹
> 实测即 range 族；number 族有原生撤销可用 ⟹ 早退是**取舍、按设计**⟹
> **D14 修法的授权范围缩小，number 族的早退语义不必动。**

**这个假设的前半被否掉了，后半被反转了。**

## 拆成两个独立问题（混在一起就会得出 777 那句过度概括）

| 问题 | 问的是什么 | 实测 |
| --- | --- | --- |
| **Q-doc** | 桌的 `Cmd+Z` 分支**够不够得着**？ | **两族都够不着**（`past` 1→1、`future` 0→0、道具没回来） |
| **Q-native** | 控件**自己**的文本撤销有没有顶上来？ | **number 有、range 没有** ⟹ 26 个 range 控件上是死键 |

777 只回答了 Q-doc，而且只在 **1 个 range 滑杆**上测过
（777 的 `fovInput` 臂 = `[data-director-camera-fov]` = `DirectorInspector.tsx:1646`
那个 `type="range"`）。⟹ 我规划时把「777 只测了 range」误当成
「只有 range 是真空」，于是推出「number 族没问题」。

**实测否掉它**：`delWhileFocused` 的 number 臂 `mugBack=false`、`past` 1→1
⟹ **D1d 在 number 族同样成立**。理由很直白：**input 的文本撤销栈里
没有「删了一个对象」这件事** —— 原生撤销顶不上删除。

## 被反转的是「守卫能不能整体去掉」

我原以为 number 族的早退是「按设计的取舍」，所以去掉它无所谓。
**实测它是承重墙**：

- `docAfterBlur` 两族都是 `past` 1→0、**`future` 0→1**
  ⟹ 一次 blur 提交就把**唯一**的撤销槽占掉了。
- 守卫的作用是让 number 用户按 `Cmd+Z` 撤**自己刚打的字**。
- 去掉守卫 ⟹ number 用户输入后按 `Cmd+Z` 会撤掉**上一个文档动作**
  ⟹ 不是体验差，是**数据错**。

⟹ **任何修法必须按控件类型分流，不能整体去掉守卫。** 而分流判据
**同仓已有先例**：`useDirectorGestureBoundary.ts:82-90` 的 `onPointerUp`
**已经**在按 `type === "number"` 分派了 ⟹ 照抄那个形状即可，
不必发明新写法。

## 本批自己的设计错：8 格里有 2 格是同一格

`native` 与 `whileFocused` 动作完全相同（聚焦 → 改动 → `Cmd+Z` 不 blur）
—— 我在探针 docstring 里**自己写了**「与 `native` 同动作」，却仍然跑了两格。
归一化（剥掉 gesture id 里内嵌的时间戳）后两臂逐字段一致 ⟹ **7 格**。
"""
import hashlib
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
#: HERE = <repo>/docs/research/<batch>/probes ⟹ 退 **4** 级到仓库根
REPO = HERE.parent.parent.parent.parent
BATCH = REPO / "docs/research/liblib-canvas-batch778-2026-10-01"
OUT = BATCH / "runtime-audit.json"
RAW = BATCH / "raw/vb778a.json"
RAW776 = REPO / "docs/research/liblib-canvas-batch776-2026-10-01/raw/vb776a.json"

FAMS = ("number", "range")
#: 探针跑了 4 个臂，但 `native` 与 `whileFocused` **动作相同** ⟹ 实为 3 个臂。
ARMS_RUN = ["native", "docAfterBlur", "whileFocused", "delWhileFocused"]
ARMS_DISTINCT = ["native", "docAfterBlur", "delWhileFocused"]
#: 两臂同格时，汇编器必须**断言它们一致**（而不是报成两格）。
DUP_PAIR = ("native", "whileFocused")
MUG = "director-prop-mug"
META = {"tries", "retried"}
#: gesture id 形如 `director-gesture-1791187547721-1` ⟹ 内嵌 epoch ms + 序号。
#: ★ 不归一化的话「两轮一致」与「两臂同格」两件事都测不了（R116/R125）。
GESTURE_RX = re.compile(r"director-gesture-\d+-(\d+)")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def src_text(rel):
    p = REPO / rel
    if not p.exists():
        raise SystemExit("FATAL 缺源码 %s" % rel)
    return p.read_text(encoding="utf-8")


def blank_comments(s):
    """注释抹白而不删（行号不漂移）。★ 只抹注释，不抹字符串（775 的 R107）。"""
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


def norm(x):
    """递归归一化：gesture id 里的 epoch ms 换成占位符。"""
    if isinstance(x, dict):
        return {k: norm(v) for k, v in x.items()}
    if isinstance(x, list):
        return [norm(v) for v in x]
    if isinstance(x, str):
        return GESTURE_RX.sub(r"director-gesture-<TS>-\1", x)
    return x


def strip(rows):
    """去掉 `tries`/`retried`（777 的教训：入参既可能是 dict 也可能是 list）。"""
    if isinstance(rows, dict):
        return {k: v for k, v in rows.items() if k not in META}
    return [{k: v for k, v in r.items() if k not in META} for r in (rows or [])]


# ═══════════════ 1. 原始读数 ═══════════════
raw = json.loads(RAW.read_text(encoding="utf-8"))
rounds = raw["rounds"]
assert len(rounds) == 2, "轮数不是 2"

cells = {}
for rd in rounds:
    for r in strip(rd.get("rows")):
        cells.setdefault((r.get("family"), r.get("arm")), []).append(norm(r))
lifecycle = [strip(rd.get("lifecycle")) for rd in rounds]

seen = set(cells)
want = {(f, a) for f in FAMS for a in ARMS_RUN}
assert seen == want, "臂集合不符：缺 %r 多 %r" % (
    sorted(want - seen), sorted(seen - want))
bad = [(k, v[0].get("FAILED")) for k, v in cells.items() if v[0].get("FAILED")]
assert not bad, "★ 有 FAILED：%r" % bad
for k, rs in cells.items():
    assert len(rs) == 2, "%s 只跑了 %d 轮" % (k, len(rs))
print("（阶段一）%d 轮 × %d 臂 × %d 族 = %d 格，零 FAILED"
      % (len(rounds), len(ARMS_RUN), len(FAMS), len(cells)))

# ── 自证：`native` 与 `whileFocused` 是同一格 ──
# ★ 我在探针 docstring 里写了「与 native 同动作」，却没让探针自证 ⟹
#   汇编器必须断言两臂**逐字段一致**，否则 8 格里会有 1 格是重复计数。
# ★ 比较前必须剔掉 `arm` —— 它是**臂的标签**，不是读数；留着它断言必然失败
#   （第一版就是这么把自己绊住的）。
def as_reading(row, drop_arm=True):
    r = {k: v for k, v in row.items() if k not in META}
    if drop_arm:
        r.pop("arm", None)
    return r


for fam in FAMS:
    a, b = cells[(fam, DUP_PAIR[0])], cells[(fam, DUP_PAIR[1])]
    ra, rb = as_reading(a[0]), as_reading(b[0])
    assert ra == rb, (
        "★ %s 的 %s 与 %s **读数不一致** ⟹ 它们不是同一格，"
        "本批的「格数」要重算；差异字段 %r\n  %s\n  %s"
        % (fam, DUP_PAIR[0], DUP_PAIR[1],
           sorted(k for k in set(ra) | set(rb) if ra.get(k) != rb.get(k)),
           json.dumps(ra, ensure_ascii=False)[:300],
           json.dumps(rb, ensure_ascii=False)[:300]))
    assert as_reading(a[1]) == ra, "%s/%s 两轮不一致" % (fam, DUP_PAIR[0])
dupVerdict = {fam: as_reading(cells[(fam, DUP_PAIR[0])][0])
              == as_reading(cells[(fam, DUP_PAIR[1])][0]) for fam in FAMS}
assert all(dupVerdict.values()), "同格自证没过"
print("（阶段一）同格自证：%s/%s 两臂（剔掉臂标签后）逐字段一致 ⟹ "
      "**%d 格而非 %d 格**"
      % (DUP_PAIR[0], DUP_PAIR[1], len(FAMS) * len(ARMS_DISTINCT),
         len(FAMS) * len(ARMS_RUN)))

# ── 每格自证：起点干净、改动真的发生、动作真的做了 ──
for fam in FAMS:
    for arm in ARMS_DISTINCT:
        c = cells[(fam, arm)][0]
        assert (c.get("stateOnFocus") or {}).get("past") == "0", \
            "%s/%s 起始历史不干净（past=%r）" % (
                fam, arm, (c.get("stateOnFocus") or {}).get("past"))
        assert (c.get("focus") or {}).get("ok") is True, \
            "%s/%s 聚焦没落在控件上" % (fam, arm)
        if arm == "delWhileFocused":
            assert c.get("mugGoneAfterDel") is True, \
                "%s 删除后道具还在 ⟹ 不是有效读数" % fam
            assert c.get("pastAfterDel") == "1", \
                "%s 删除后 past=%r，而预测是 1（删除进历史）" % (
                    fam, c.get("pastAfterDel"))
            assert (c.get("focusAfterDel") or {}).get("ok") is True, \
                "★ %s 删除后焦点没回到控件 ⟹ 那一格不是有效读数" % fam
        else:
            assert c.get("valueAfterMutate") is not None, \
                "%s/%s 没记到改动后的值 ⟹ 不是有效读数" % (fam, arm)
            if arm == "docAfterBlur":
                assert c.get("blurFocusOk") is True, \
                    "★ %s 的 blur 落点没聚焦上 ⟹ 那一格不是有效读数" % fam
                assert (c.get("stateAfterBlur") or {}).get("focusTag") == "BUTTON", \
                    "%s blur 后焦点不是 BUTTON（=%r）" % (
                        fam, (c.get("stateAfterBlur") or {}).get("focusTag"))

# ═══════════════ 2. 预测（从源码逐行推出） ═══════════════
# ── 预测 A：焦点在可编辑元素上时，桌的 Cmd+Z 分支**够不着** ──
#   ⟸ `isEditable` 守卫（DirectorDesk.tsx:487）排在 Cmd+Z 分支（:506）**之前**
#   ⟹ `lastCommand` **不出现** `UNDO`，`past`/`future` 不动
#   ★ 这一条对**两族**都成立 —— 判据只看 tagName，不看 `type`。
for fam in FAMS:
    for arm in ARMS_DISTINCT:
        c = cells[(fam, arm)][0]
        if arm != "delWhileFocused":
            continue
        u = c.get("stateAfterUndo") or {}
        assert u.get("lastCommand") != "UNDO", (
            "★ %s/%s 的 lastCommand 变成了 UNDO ⟹ 「守卫早退」这条推理不成立"
            % (fam, arm))
        assert u.get("past") == "1" and u.get("future") == "0", (
            "★ %s/%s 撤销后 past=%r future=%r，而预测是 1/0（命令被吞）"
            % (fam, arm, u.get("past"), u.get("future")))
        assert c.get("mugBack") is False, (
            "★ %s/%s **居然能撤销** ⟹ 「删除不可撤销」在 %s 族上不成立"
            % (fam, arm, fam))
# ⟹ D1d 的范围**没有被收窄**：两族都成立。
nDelBlocked = sum(1 for f in FAMS
                  if cells[(f, "delWhileFocused")][0].get("mugBack") is False)
assert nDelBlocked == len(FAMS), "D1d 只在 %d/%d 族成立" % (nDelBlocked, len(FAMS))

# ── 预测 B：blur 时手势**提交** ⟹ 改动进历史（`:80 onBlur: commit`）──
for fam in FAMS:
    for rd in lifecycle:
        c = next((x for x in rd if x.get("family") == fam), None)
        assert c is not None, "生命周期普查里没有 %s 族" % fam
        if c.get("FAILED"):
            raise SystemExit("★ %s 族生命周期普查 FAILED：%s" % (fam, c["FAILED"]))
        assert (c.get("onFocus") or {}).get("past") == "0", \
            "%s 聚焦后 past=%r，而预测是 0（还没提交）" % (
                fam, (c.get("onFocus") or {}).get("past"))
        assert (c.get("afterMutate") or {}).get("past") == "0", (
            "★ %s 改动后 past=%r，而预测是 0（改动期间不提交）"
            % (fam, (c.get("afterMutate") or {}).get("past")))
        assert (c.get("afterBlur") or {}).get("past") == "1", (
            "★ %s blur 后 past=%r，而预测是 1（blur 提交）"
            % (fam, (c.get("afterBlur") or {}).get("past")))
        assert (c.get("afterBlur") or {}).get("gesture") == "", \
            "%s blur 后手势没清空" % fam
        assert (c.get("afterBlur") or {}).get("lastCommand") == "GESTURE_COMMIT", \
            "%s blur 后 lastCommand=%r，而预测是 GESTURE_COMMIT" % (
                fam, (c.get("afterBlur") or {}).get("lastCommand"))

# ── 预测 C：blur 之后撤销**可用**，且**占掉唯一的撤销槽** ──
for fam in FAMS:
    c = cells[(fam, "docAfterBlur")][0]
    u = c.get("stateAfterUndo") or {}
    assert u.get("lastCommand") == "UNDO", (
        "★ %s blur 后 lastCommand=%r，而预测是 UNDO（守卫不触发）"
        % (fam, u.get("lastCommand")))
    assert u.get("past") == "0" and u.get("future") == "1", (
        "★ %s blur 后撤销后 past=%r future=%r，而预测是 0/1"
        % (fam, u.get("past"), u.get("future")))
    assert c.get("valueAfterUndo") != c.get("valueAtUndo"), (
        "★ %s blur 后撤销没把值改回去 ⟹ 「改动进历史且可撤」不成立" % fam)
# ⟹ `future` 0→1 是「**唯一**的撤销槽被这次编辑占掉」的直接证据
nSlotConsumed = sum(1 for f in FAMS
                    if (cells[(f, "docAfterBlur")][0].get("stateAfterUndo") or {})
                    .get("future") == "1")
assert nSlotConsumed == len(FAMS), "撤销槽被占掉只在 %d/%d 族成立" % (
    nSlotConsumed, len(FAMS))

# ── 预测 D（★ 本批的核心，且**成对**）：焦点在控件内时 `Cmd+Z` 的三个读数 ──
#   number 族：值回到改动前（**原生撤销顶上了**）
#   range  族：三个读数**全不动** ⟹ **死键**
# ★ 必须**成对**断言：只断言「range 没变」的话，一个「根本不会撤销任何东西」
#   的坏探针也能过；只断言「number 变了」的话，一个只会撤销的探针也能过。
nativeUndo = {}
for fam in FAMS:
    c = cells[(fam, "native")][0]
    base = (c.get("valueAfterMutate") or {}).get("value")
    after = (c.get("valueAfterUndo") or {}).get("value")
    u = c.get("stateAfterUndo") or {}
    assert base is not None, "%s/native 没记到基准值 ⟹ 不是有效读数" % fam
    nativeUndo[fam] = {
        "mutatedTo": base, "afterUndo": after,
        "valueReverted": after != base,
        "past": u.get("past"), "future": u.get("future"),
        "lastCommand": u.get("lastCommand"),
        # ★ 桌的键处理**根本没被触到**的证据（R126：不能只看「没变」）
        "deskSawKey": u.get("lastCommand") == "UNDO",
    }
assert nativeUndo["number"]["valueReverted"] is True, (
    "★ number 族的原生撤销**没生效**（%r → %r）⟹ 「range 是死键」这个读法要重算："
    "它可能只是「探针什么也撤不掉」"
    % (nativeUndo["number"]["mutatedTo"], nativeUndo["number"]["afterUndo"]))
assert nativeUndo["range"]["valueReverted"] is False, (
    "★ range 族的值**居然回退了** ⟹ 「26 个滑杆是死键」这条不成立")
for fam in FAMS:
    assert nativeUndo[fam]["deskSawKey"] is False, (
        "%s/native 的 lastCommand 出现了 UNDO ⟹ 守卫没拦住" % fam)
# ⟹ range 族的「真空」是**三读数同时不动**，而不是其中之一
vacuum = (not nativeUndo["range"]["valueReverted"]
          and nativeUndo["range"]["lastCommand"] != "UNDO")
assert vacuum is True
print("（阶段二）D1d 两族都成立（%d/%d）｜blur 后两族都可撤（%d/%d）｜"
      "焦点内：number **有**原生撤销、range **无**（真空=%s）"
      % (nDelBlocked, len(FAMS), nSlotConsumed, len(FAMS), vacuum))

# ═══════════════ 3. 静态层 ═══════════════
DD = blank_comments(src_text("src/components/director/DirectorDesk.tsx"))
dl = DD.split("\n")
GB = blank_comments(src_text(
    "src/components/director/useDirectorGestureBoundary.ts"))
INSP = blank_comments(src_text(
    "src/components/director/DirectorInspector.tsx"))
# ★ 每份源码都必须 `.split("\n")` —— `first_in` 收的是**行列表**，
#   直接传整串会变成逐字符匹配，断言恒假（R110 的又一变体）。
gb = GB.split("\n")
insp = INSP.split("\n")


def all_in(lines, pat):
    rx = re.compile(pat)
    return [n for n, ln in enumerate(lines, 1) if rx.search(ln)]


def first_in(lines, pat, after=0):
    """★ 搜索必须带作用域（`after`）—— 否则「找不到」被读成「不存在」
    （775 的 R110 / 776 的 R117）。"""
    return next((n for n in all_in(lines, pat) if n > after), None)


def last_in_before(lines, pat, before):
    """★ 取 `before` 之前**最后一个**匹配，而不是第一个 —— 文件里
    `type="range"` 出现在 1353/1647/2532… 多处，取首次会匹配到别的控件，
    读数就挂在了错的元素上（R110 同族）。"""
    return next((n for n in reversed(all_in(lines, pat)) if n < before), None)


def last_in(lines, pat):
    """★ 取**末次**出现。`useDirectorGestureBoundary.ts:17-24` 有一份
    `DirectorGestureBoundaryHandlers` **类型声明**列着 `onFocus`/`onBlur`/
    `onPointerUp`，实现体在 `:78-90` ⟹ 取首次会把读数挂在类型声明上。"""
    return next(reversed(all_in(lines, pat)), None)


# S1：守卫早于 Cmd+Z 分支 ⟹ 预测 A 的机制
guardLine = first_in(dl, r"if \(isEditable\) return;")
undoLine = first_in(dl, r'key\.toLowerCase\(\) === "z"')
# S2：判据只看 tagName，**不看 `type`** ⟹ 两族走同一条分支
predLine = first_in(dl, r"const isEditable =")
typeInPredicate = first_in(dl, r'\.type\b|\btype\s*===', after=predLine or 0)
predicateEnd = first_in(dl, r"if \(event\.isComposing\)", after=predLine or 0)
predicate = "\n".join(dl[(predLine or 1) - 1:(predicateEnd or 1) - 1])
typeConsulted = bool(re.search(r"\.type\b|getAttribute\(.type.\)", predicate))
# S3：onFocus=begin / onBlur=commit ⟹ 预测 B 的机制
# ★ 取**末次**出现：`:17-24` 的类型声明也列着这两个名字，取首次会挂错行。
onFocusLine = last_in(gb, r"onFocus:")
onBlurLine = last_in(gb, r"onBlur:")
# S4：`onPointerUp` **已经**按 type 分派 ⟹ 分流修法的同仓先例
puStart = last_in(gb, r"onPointerUp:")
puEnd = last_in(gb, r"onPointerCancel:")
puBody = "\n".join(gb[(puStart or 1) - 1:(puEnd or 1) - 1]) if (
    puStart and puEnd and puStart < puEnd) else ""
puNumberDispatch = ('HTMLInputElement' in puBody and '=== "number"' in puBody)
# S5：探针用的两个元素在源码里**确实是**它们声称的 `type`
# ★ 属性名必须**精确**匹配：`\b` 在 `-` 前也算词边界 ⟹ `fov\b` 会命中
#   `fov-field`/`fov-slider`/`fov-fill`… 而探针的 CSS 选择器
#   `[data-director-camera-fov]` 是**精确属性名**匹配。两者必须对齐。
fovAttrLine = first_in(insp, r"data-director-camera-fov(?![-\w])")
fovRangeLine = last_in_before(insp, r'type="range"', fovAttrLine or 10 ** 9)
xfAttrLine = first_in(insp, r"data-director-transform-field(?![-\w])")
xfNumLine = last_in_before(insp, r'type="number"', xfAttrLine or 10 ** 9)
fovGap = (fovAttrLine - fovRangeLine) if (fovAttrLine and fovRangeLine) else None
xfGap = (xfAttrLine - xfNumLine) if (xfAttrLine and xfNumLine) else None

static = {
    "guardLine": guardLine, "undoLine": undoLine,
    "guardBeforeUndo": bool(guardLine and undoLine and guardLine < undoLine),
    "isEditableLine": predLine,
    "isEditableConsultsType": typeConsulted,
    "onFocusLine": onFocusLine, "onBlurLine": onBlurLine,
    "onBlurCommits": bool(
        re.search(r"onFocus:\s*begin\b", GB) and re.search(r"onBlur:\s*commit\b", GB)),
    "onPointerUpDispatchesNumber": puNumberDispatch,
    "fovTypeLine": fovRangeLine, "fovAttrLine": fovAttrLine, "fovGap": fovGap,
    "xfTypeLine": xfNumLine, "xfAttrLine": xfAttrLine, "xfGap": xfGap,
    "fovIsRange": bool(fovGap is not None and 0 < fovGap <= 6),
    "xfIsNumber": bool(xfGap is not None and 0 < xfGap <= 6),
}
assert guardLine is not None, "守卫不见了"
assert undoLine is not None, "Cmd+Z 分支不见了"
assert static["guardBeforeUndo"] is True, (
    "★ Cmd+Z 分支排到了守卫**之前** ⟹ 「守卫早退」这条推理不成立")
assert predLine is not None, "isEditable 判据不见了"
assert typeConsulted is False, (
    "★ `isEditable` 判据**开始看 input.type 了** ⟹ 阶段二里"
    "「两族同分支」的读数要重算")
assert onFocusLine is not None and onBlurLine is not None, \
    "focus/blur 绑定不见了"
assert static["onBlurCommits"] is True, \
    "★ `onBlur` 不再是 `commit` ⟹ 「blur 时提交」这条预测要重算"
assert puNumberDispatch is True, (
    "★ `onPointerUp` 不再按 `type === \"number\"` 分派 ⟹ "
    "「同仓已有分流先例」这条授权依据要撤")
assert static["fovIsRange"] is True, (
    "★ FOV 那个元素不再是 `type=\"range\"`（type 行 :%s，data 行 :%s，相距 %s 行）"
    "⟹ 「777 的 fovInput 臂是 range 滑杆」这条追溯断了"
    % (fovRangeLine, fovAttrLine, fovGap))
assert static["xfIsNumber"] is True, (
    "★ 变换字段不再是 `type=\"number\"`（type 行 :%s，data 行 :%s，相距 %s 行）"
    "⟹ 「number 族代表元素」这条读数要重算"
    % (xfNumLine, xfAttrLine, xfGap))
print("（阶段三）静态：守卫 :%s 早于 Cmd+Z :%s｜isEditable **不看 type**=%s｜"
      "onBlur=commit :%s｜onPointerUp 已分流 number=%s｜fov :%s(range) / xf :%s(number)"
      % (guardLine, undoLine, not typeConsulted, onBlurLine,
         puNumberDispatch, fovRangeLine, xfNumLine))

# ═══════════════ 4. 族规模（从 776 的 raw 现算，不手抄） ═══════════════
raw776 = json.loads(RAW776.read_text(encoding="utf-8"))
census776 = raw776["rounds"][0]["census"]
# ★ 跨上下文**取 max**，不是求和 —— 同一族控件在 camera / camera-path /
#   prop / character 等上下文里是**同一批 DOM 元素**，求和会重复计数（R125 同族）。
best = {}
for c in census776:
    k = c.get("id")
    if not c.get("selfJustified"):
        continue
    if k not in best or (c.get("live") or 0) > (best[k].get("live") or 0):
        best[k] = c
# ★ 逐族自证非空：全 0 与「不存在」在产物里长得一样（R104/R112）
for k, c in best.items():
    assert (c.get("live") or 0) > 0, (
        "★ 776 普查里 %s 族 live=0 ⟹ 规模读数无效" % k)
famCount = {}
for k, c in best.items():
    famCount.setdefault(c.get("wantType"), {})[k] = c.get("live")
famSize = {t: sum(v.values()) for t, v in famCount.items()}
famIds = {t: sorted(v) for t, v in famCount.items()}
assert famSize.get("range") and famSize.get("number"), "族规模读不出来"
# ★ 独立交叉校验：27 + 26 = 53，而 776 的 README 自己写的是「共 53 个可用控件」
assert famSize["number"] + famSize["range"] == 53, (
    "★ 两族合计 %d，而 776 README 自己写的是 53 ⟹ 去重规则（取 max）选错了"
    % (famSize["number"] + famSize["range"]))
nVacuumControls = famSize["range"]
nSafeControls = famSize["number"]
print("（阶段四）族规模（776 raw 现算，跨上下文取 max）：number %d %r｜"
      "range %d %r｜合计 %d ✓ 与 776 README 自述的 53 相符"
      % (nSafeControls, famIds["number"], nVacuumControls, famIds["range"],
         nSafeControls + nVacuumControls))

# ═══════════════ 5. 可比性 ═══════════════
r0 = norm(strip(rounds[0].get("rows")))
r1 = norm(strip(rounds[1].get("rows")))
l0 = norm(strip(rounds[0].get("lifecycle")))
l1 = norm(strip(rounds[1].get("lifecycle")))
tries = [r.get("tries", 1) for rd in rounds for r in (rd.get("rows") or [])]
comparability = {
    "rounds": len(rounds), "rowsPerRound": len(rounds[0].get("rows") or []),
    "allConsistent": r0 == r1 and l0 == l1,
    "duplicateCell": {
        "arms": list(DUP_PAIR),
        "why": "★ 我在探针 docstring 里**自己写了**「与 `native` 同动作」，"
               "却仍然把它跑成了两格。动作相同 ⟹ 实为同一格，"
               "报成 8 格会**多算一格**。",
        "selfJustified": dupVerdict,
        "rule": "归一化 gesture id 里内嵌的 epoch ms（R125）后逐字段比较；"
                "不一致就说明它们不是同一格，「格数」要重算。",
        "distinctCells": len(FAMS) * len(ARMS_DISTINCT),
        "distinctArms": list(ARMS_DISTINCT),
    },
    "normalization": "★ gesture id 形如 `director-gesture-1791187547721-1`，"
                     "内嵌 epoch ms ⟹ **不归一化的话「两轮一致」永远不可能**。"
                     "归一化规则 `<TS>` 已写进本产物（不是排除字段）。",
    "retryPolicy": "每格最多试 3 次（含第一次），900×n 退避；`tries`/`retried` "
                   "记进 raw 但**排除在两轮一致性比较之外**。",
    "retryStats": {"cells": len(tries),
                   "retriedCells": sum(1 for t in tries if t > 1),
                   "maxTries": max(tries) if tries else None},
    "boundary": "★ **本批未改 `src/`，也没有任何注入。** 删除**是破坏性操作"
                "且本批真的执行了**（用户目标明确允许有副作用的 CRUD），但："
                "① 每格开头 `fresh()` 清 localStorage ⟹ 不留残留；"
                "② **不点**提交/连接/新增机位/导入导出，不做付费或真实生图生视频。",
}
assert comparability["allConsistent"] is True, "★ 两轮不一致"

# ═══════════════ 6. 结论 ═══════════════
judgments = [
    {"id": "J1",
     "text": "★ **D1d 的范围没有被收窄 —— 它在两族上都成立。** "
             "我 778 规划时假设「有原生撤销的控件不是真空」⟹ 实测否掉："
             "`delWhileFocused` 的 number 臂道具**没回来**、`past` 1→1、"
             "`future` 0→0、`lastCommand` 连 `UNDO` 都没出现。"
             "理由很直白 —— **input 的文本撤销栈里没有「删了一个对象」这件事**。",
     "evidence": "阶段二 预测 A"},
    {"id": "J2",
     "text": "★ **被收窄的是「守卫能不能整体去掉」，而答案是否。** "
             "我原以为 number 族的早退是「按设计的取舍」；实测它是**承重墙**："
             "`docAfterBlur` 两族都是 `future` 0→1 ⟹ 一次 blur 提交就把"
             "**唯一**的撤销槽占掉。去掉守卫 ⟹ number 用户输入后按 `Cmd+Z` "
             "会撤掉**上一个文档动作** ⟹ 不是体验差，是**数据错**。",
     "evidence": "阶段二 预测 C"},
    {"id": "J3",
     "text": "★ **「死键」只对 range 族成立（%d 个控件）。** 焦点在滑杆上时 "
             "`Cmd+Z` 的**三个读数同时不动**：值不动、`past/future` 不动、"
             "`lastCommand` 停在原处（不是 `UNDO`）⟹ 桌的键处理**根本没被触到**。"
             "而 number 族（%d 个）的原生撤销顶上了 ⟹ 值回到 %s。",
     "evidence": "阶段二 预测 D + 阶段四"},
    {"id": "J4",
     "text": "★ **出路存在，但要靠「先移开焦点」这个用户不会想到的动作。** "
             "`docAfterBlur` 两族都 2/2 可撤（`lastCommand`=`UNDO`、"
             "`past` 1→0、`future` 0→1、值回退）⟹ 手势是在 **blur 时**提交的"
             "（`useDirectorGestureBoundary.ts:80 onBlur: commit`），"
             "所以「手还在滑杆上」时历史里**根本没有那一格**。",
     "evidence": "阶段二 预测 B + C"},
    {"id": "J5",
     "text": "★ **同仓已有分流先例可以照抄**：`useDirectorGestureBoundary.ts:82-90` "
             "的 `onPointerUp` **已经**在按 `type === \"number\"` 提前 return "
             "⟹ 「按控件类型分派手势行为」在这个仓里是既有写法。"
             "而 `DirectorDesk.tsx:475-480` 的 `isEditable` 判据**只看 tagName、"
             "不看 `type`** ⟹ 缺的正是这一层分派。",
     "evidence": "阶段三 S2 + S4"},
    {"id": "J6",
     "text": "★ **777 的 `fovInput` 臂是 range 滑杆，不是数字输入框。** "
             "它用 `[data-director-camera-fov]` = `DirectorInspector.tsx:1646` "
             "那个 `type=\"range\"`。同一个 FOV 区块里还有一个 "
             "`type=\"number\"` 的读数框（`:1661`，**不挂 gesture**、"
             "另有 draft 与 `onBlur` 复位）⟹ 777 的 D1d 其实是 **n=1 的 "
             "range 样本**，778 的 number 臂才是把它推广开的那个读数。",
     "evidence": "阶段三 S5"},
]
corrections = [
    {"id": "C778-1",
     "targets": ["**778 规划时的假设**：「D1d 过宽 ⟹ 正确范围 = 只有没有原生撤销的"
                 "控件才是真空 ⟹ number 族 27 个早退是取舍、按设计 ⟹ "
                 "D14 修法授权范围缩小，number 族的早退语义不必动」",
                 "**777 的措辞**：「焦点在**检查器输入框**上时删除不可撤销」"],
     "was": "读作「删除不可撤销只发生在没有原生撤销的控件上（range 族 %d 个），"
            "number 族 %d 个是按设计的取舍、不在范围内」。" % (
                nVacuumControls, nSafeControls),
     "now": "★ 据实拆成两个独立问题："
            "**Q-doc（桌的分支够不够得着）两族都够不着** ⟹ D1d 覆盖**全部 %d 个**"
            "可用控件，两族 %d/%d 成立，**范围没有被收窄**；"
            "**Q-native（控件自己的文本撤销顶不顶得上）只有 number 顶得上** ⟹ "
            "「死键」只落在 range 族 %d 个上。"
            "★ 并且 777 的样本是 **n=1 的 range 滑杆**（见 J6）⟹ "
            "「输入框」这个措辞当时是过度概括，本批把它推广到两族。"
            "★ **被收窄的是修法而不是缺陷范围**：`:487` 那道守卫在 number 族上"
            "是**承重墙**（去掉它会把「撤自己的字」变成「撤上一个动作」= 数据错）"
            "⟹ 修法**必须按控件类型分流**，不能整体去守卫。",
     "evidence": "J1 + J2 + J3"},
]
assert [c["id"] for c in corrections] == ["C778-1"]

probeLessons = [
    {"id": "R123", "text": "★ **探针里两臂动作写得一样，它们就是同一格。** "
                            "我在 `native` 与 `whileFocused` 的 docstring 里"
                            "**自己写了**「与 `native` 同动作」，却仍跑成两格 "
                            "⟹ 8 格里有一格是重复计数。归一化后逐字段断言一致，"
                            "不一致就得重算格数。"},
    {"id": "R124", "text": "★ **「变化=是」有可能是「基准值没取到」的假象。** "
                            "本批 `summarize()` 只认 `valueBeforeUndo`/"
                            "`valueAtUndo`，而 `native`/`whileFocused` 臂两者"
                            "都没有（它们不 blur）⟹ `vb` 取到 `{}` ⟹ "
                            "`str(None) != str(\"4.8\")` **恒真**。"
                            "实测 range 那一格**其实没变**却被打印成「变化=是」。"
                            "⟹ 基准值必须从 `valueAfterMutate` 取，"
                            "且「变没变」不能用「两个都可能缺失的字段不相等」来判。"
                            "这是 R121（把「读不到」当成「没变」）的同族错误。"},
    {"id": "R125", "text": "★ **内嵌时间戳的 id 让两件事都测不了**："
                            "「两轮逐字段一致」（R116）和「两臂是不是同一格」"
                            "（R123）都因为 `director-gesture-<epoch_ms>-<seq>` "
                            "而恒假。归一化规则**写进产物**，不是排除字段。"},
    {"id": "R126", "text": "★ **「三个读数都没动」里的每一个「没动」都有三个"
                            "不同原因**（值没被改 / 被改了但撤得回 / 撤不回）。"
                            "本批靠 `lastCommand` 兜底：`native` 两族停在 "
                            "`GESTURE_BEGIN`/`UPDATE_CAMERA` 而**不出现** "
                            "`UNDO` ⟹ 这才证明**桌的键处理根本没被触到**，"
                            "而不是「触到了但没生效」。只看「值没变」会把这两种"
                            "混成一种。"},
    {"id": "R127", "text": "★ **臂的名字会替读数说话。** 777 的臂叫 `fovInput`、"
                            "结论写「焦点在**输入框**上」⟹ 读起来像数字输入，"
                            "而该元素是 `type=\"range\"` 的滑杆。**`type` "
                            "才是族的判据，不是标签、不是臂名。** 一个 n=1 的 "
                            "range 样本被措辞放大成「所有检查器输入框」。"},
    {"id": "R128", "text": "★ **静态搜索的四种「找到错的」都在本批各犯了一次**："
                            "① 忘 `.split(\"\\n\")` ⟹ 整串当行列表，逐字符匹配恒假；"
                            "② 忘了 `useDirectorGestureBoundary.ts:17-24` 有一份"
                            "**类型声明**列着同名 handler ⟹ `first_in` 挂到声明上；"
                            "③ `type=\"range\"` 有十几处 ⟹ 该取 data 属性**之前最后**"
                            "一个而不是第一个；④ **`\\b` 在 `-` 前也算词边界** ⟹ "
                            "`fov\\b` 命中 `fov-field`，而探针的 CSS "
                            "`[data-director-camera-fov]` 是**精确属性名**匹配 —— "
                            "**搜索式必须和探针的选择器对齐**。"
                            "四次都是同一族：断言恒假时先怀疑搜索，而不是先改断言。"},
]
assert [x["id"] for x in probeLessons] == [
    "R123", "R124", "R125", "R126", "R127", "R128"]

defects = [
    {"id": "D1d", "severity": "中-高（范围已由 778 更正）",
     "text": "★ **焦点在检查器控件上时，删除不可撤销。** 删除进了历史"
             "（`past`=1）但 `Cmd+Z` 被 `isEditable` 守卫"
             "（`DirectorDesk.tsx:487`，排在 `:506` 的 undo 分支之前）吞掉 ⟹ "
             "道具没回来、`past` 仍=1、`future` 仍=0、`lastCommand` 连 `UNDO` "
             "都没出现。**与 D14 同一道守卫。** "
             "**778 更正**：范围不是「所有检查器输入框」这么含糊的措辞，"
             "而是**全部 %d 个可用控件、两族 %d/%d 成立** —— "
             "**原生撤销顶不上删除**（文本撤销栈里没有「删了一个对象」）。"
             % (nSafeControls + nVacuumControls, nDelBlocked, len(FAMS)),
     "evidence": "J1"},
    {"id": "D1f", "severity": "中（本批记录）",
     "text": "★ **%d 个 range 族滑杆上，焦点还在控件内时 `Cmd+Z` 是死键，"
             "且零反馈。** 三个读数同时不动：值不动（48→48）、`past/future` 不动、"
             "`lastCommand` 停在 `UPDATE_CAMERA` 而不是 `UNDO` ⟹ "
             "桌的键处理**根本没被触到**。而 `onBlur: commit` 意味着改动"
             "**要等移开焦点才进历史** ⟹ 用户「刚拖完滑杆就按 `Cmd+Z`」"
             "**什么也不会发生**，而界面不告知（`COMMITTED` 已被 "
             "`getDirectorCommandFeedback` 过滤成 `null`，777 已测撤销类控件 0）。"
             "**同一族里 number 有原生撤销、range 没有 ⟹ 同一个键在不同滑杆上"
             "行为不一致，用户无从预期。**" % nVacuumControls,
     "evidence": "J3 + J4"},
]
audit = {
    "batch": 778,
    "topic": "`Cmd+Z` 在检查器控件上的早退是「按设计」还是「缺陷」？"
             "按控件类型拆开之后，我自己的规划假设被否掉了",
    "generatedBy": "probes/mk778audit.py",
    "sources": {
        "vb778a.json": {"sha16": sha(RAW), "rounds": len(rounds),
                        "rowsPerRound": len(rounds[0].get("rows") or [])},
        "vb776a.json": {"sha16": sha(RAW776), "usedFor": "族规模（现算，不手抄）"},
    },
    "theSplit": {
        "why": "★ 777 只回答了 Q-doc 且样本是 n=1 的 range 滑杆 ⟹ "
               "我 778 规划时把「只测了 range」误当成「只有 range 是真空」。",
        "Q-doc": "桌的 Cmd+Z 分支够不够得着 → **两族都够不着**"
                 "（守卫只看 tagName，不看 `type`）",
        "Q-native": "控件自己的文本撤销顶不顶得上 → **number 顶得上、range 顶不上**",
        "refutedPlan": "★ 「number 族早退是取舍、按设计 ⟹ D14 授权范围缩小」"
                       "**被否掉**，且方向反转：守卫在 number 族上是**承重墙**。",
    },
    "verdict": {
        "D1d范围": "**没有被收窄** —— 全部 %d 个可用控件、两族 %d/%d 成立"
                   % (nSafeControls + nVacuumControls, nDelBlocked, len(FAMS)),
        "死键范围": "**只有 range 族 %d 个**（number 族 %d 个有原生撤销）"
                    % (nVacuumControls, nSafeControls),
        "守卫能否整体去掉": "**不能** —— 去掉会让 number 用户的 `Cmd+Z` "
                            "撤掉上一个文档动作（数据错）",
        "出路": "**存在** —— blur 之后两族都 2/2 可撤",
    },
    "comparability": comparability,
    "static": static,
    "familySizes": {
        "number": {"count": nSafeControls, "ids": famIds["number"],
                   "nativeUndo": True},
        "range": {"count": nVacuumControls, "ids": famIds["range"],
                  "nativeUndo": False},
        "dedupRule": "★ 跨上下文**取 max**，不是求和 —— 同一族控件在不同上下文里"
                     "是**同一批 DOM 元素**（`xf` 在 camera 与 camera-path 都是 12）"
                     "⟹ 求和会重复计数。",
        "crossCheck": "number %d + range %d = %d，与 776 README 自述的"
                      "「共 53 个可用控件」相符 ⟹ 去重规则被独立校验过。"
                      % (nSafeControls, nVacuumControls,
                         nSafeControls + nVacuumControls),
    },
    "lifecycle": lifecycle[0],
    "nativeUndo": nativeUndo,
    "results": {
        "delBlockedFamilies": nDelBlocked,
        "delBlockedMugBack": False,
        "undoSlotConsumedFamilies": nSlotConsumed,
        "nativeUndoWorks": {"number": True, "range": False},
        "vacuumCells": 1 if vacuum else 0,
        "vacuumControls": nVacuumControls,
        "distinctCells": comparability["duplicateCell"]["distinctCells"],
        "failedCells": 0,
    },
    "judgments": judgments,
    "corrections": corrections,
    "findings": {
        "F1": "★ **D1d 范围没有被收窄** —— 原生撤销顶不上删除，两族都成立。",
        "F2": "★ **守卫不能整体去掉** —— 它在 number 族上是承重墙，"
              "去掉会把「撤自己的字」变成「撤上一个动作」。",
        "F3": "★ **%d 个 range 滑杆上是死键且零反馈**，出路要靠先移开焦点。"
              % nVacuumControls,
        "F4": "★ **同仓已有分流先例**（`onPointerUp` 按 `type === \"number\"`），"
              "缺的只是 `isEditable` 判据里的那一层。",
        "F5": "★ **777 的 `fovInput` 臂是 range 滑杆** ⟹ 它的 D1d 是 n=1 的 "
              "range 样本，「输入框」的措辞当时是过度概括。",
    },
    "probeLessons": probeLessons,
    "defects": defects,
    "srcDiff": "**本批未改 `src/`**（工作区 `src/` 干净）；**没有任何注入**。"
               "★ 本批**真的执行了破坏性删除**（用户目标允许有副作用的 CRUD），"
               "但每格开头 `fresh()` 清 localStorage ⟹ 不留残留。",
    "rawSha": {"vb778a.json": sha(RAW), "vb776a.json": sha(RAW776)},
    "retryStats": comparability["retryStats"],
    "boundary": comparability["boundary"],
}
OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote %s" % OUT)
