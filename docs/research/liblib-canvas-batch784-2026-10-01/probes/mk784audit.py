#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 784 汇编器 —— 「`sIP` 主人 + `bubble` 主人**共活**」时会怎样

## 782/783 测过的都是「`sIP` 单独活着」或「两个 bubble」

⟹ **「一个 `sIP` 主人和一个 bubble 主人同时活着」这个格子，从来没被测过。**
而它才是「层内 Escape 只关层」失效的**一般形态**。

## ★ 预测（从源码逐行推出）与实测：预测成立

| 主人 | 相位 | 阻断 | 外点关闭 |
| --- | --- | --- | --- |
| `DirectorObjectTree.tsx:213` | bubble | 不阻断 | ★ `mousedown`（`:212`，处理器 `close` 里**直接** `setContextMenu(null)`） |
| `DirectorViewport.tsx:2748` | **capture** | **`sIP`** | 无（模型库那套在**面板内部**判 `contains`） |

★ 关键：右键菜单的互斥挂在 **`mousedown`** 上，而模型库触发器是
`<button type="button" onClick>`（`DirectorViewport.tsx:3568-3574`）——
**键盘 `Enter` 激活按钮只产生 `click`，不产生 `mousedown`**。

⟹ 预测 ①：鼠标激活 ⟹ `mousedown` ⟹ **不会**共活
⟹ 预测 ②：★ **键盘**激活 ⟹ 没有任何 pointer 事件 ⟹ **两个都开着**

**实测两条都对**，而且后果可测：共活时第 1 次按 Escape `cap=0, win=0`
⟹ `sIP` 把整条链截断 ⟹ **模型库关了、右键菜单留在原地、桌的阶梯也跑不到**
（导出面板同样留在原地）⟹ **要按第二次**。

## ★★ 普查器这一批又踩了两次（第三版才对）

1. 用「取门状态 `ids` 的第一个」⟹ 给 `DirectorDesk:570` 算出 `state=capture`
   ⟹ **783 明令禁止的语义判断，换个形式又犯了一次**。
2. 判据写成「这条 pointer 监听**所在的 `useEffect` 体**里有没有 `set<S>(null)`」
   ⟹ 抓到**假阳性** `DirectorTimeline.tsx:771`（`pointerup`/`handleUp`）——
   那是一段**拖拽结束**的清理，而且 `handleUp` 是**一跳间接**调 `cleanup()`。

⟹ 第三版判据：**处理器自己的函数体里直接出现 `set<S>(null)`**，
同时排掉「不在 effect 里的代码」与「一跳间接调用」。

## ★ 探针自己有一个错的派生字段

`dbg784a.py` 记的 `coLive` 只看了「第一个开了 ctx」+「第二个开了 lib」，
**没检查第一个是不是还开着** ⟹ `ctxThenLibMouse` 被标成 `coLive=True`，
而它自己的 `after2.ctxOpen=False`。
⟹ **汇编器不信它**，一律从 `after2` 重算，并把「raw 里的派生字段与它自己的
输入不一致」记成一条发现（R149）。
"""
import hashlib
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent.parent
BATCH = REPO / "docs/research/liblib-canvas-batch784-2026-10-01"
OUT = BATCH / "runtime-audit.json"
CENSUS = BATCH / "raw/census784.json"
RAW = BATCH / "raw/vb784a.json"
META = {"tries", "retried"}

TREE = "src/components/director/DirectorObjectTree.tsx"
VP = "src/components/director/DirectorViewport.tsx"
TL = "src/components/director/DirectorTimeline.tsx"
ARMS = ["ctxThenLibMouse", "ctxThenLibKeyboard", "ctxOnly", "libOnly"]
PRESSES = 2
ROUNDS = 2
#: ★ 判据的 `kw` 取自**这些标签的字面量**，逐条唯一
CTX_OWNER = "DirectorObjectTree.tsx:213"
LIB_OWNER = "DirectorViewport.tsx:2748"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def strip(rows):
    return [{k: v for k, v in r.items() if k not in META} for r in (rows or [])]


def reading(row):
    r = {k: v for k, v in row.items() if k not in META}
    r.pop("arm", None)
    return r


# ═══════════════ 1. 静态 ═══════════════
cen = json.loads(CENSUS.read_text(encoding="utf-8"))
oc = cen["outsideClose"]
withOc = cen["statesWithOutsideClose"]
withoutOc = cen["statesWithoutOutsideClose"]
print("（阶段一）门状态 %d 个：**有**外点关闭 %d 个 / **没有** %d 个"
      % (len(cen["states"]), len(withOc), len(withoutOc)))

# ── 预测 A：★★ 11 个主人对应的门状态里，**只有 3 个**有任何外点关闭 ──
#   ⟹ 「层内 Escape 只关层」**没有全局保障**
assert withOc == ["contextMenu", "pathMenuLeft", "presetPanelLeft"], (
    "★ 有外点关闭的门状态变成 %r（预测是 contextMenu / pathMenuLeft / "
    "presetPanelLeft 三个）⟹ 「只有 3 个有」的结论要重算" % withOc)
assert len(withoutOc) == 7, (
    "★ 没有外点关闭的门状态变成 %d 个（预测 7）⟹ 要重算" % len(withoutOc))
print("（阶段二）★ 有外点关闭的只有 **3** 个：%r；**没有**的 **%d** 个：%r"
      % (withOc, len(withoutOc), withoutOc))

# ── 预测 B：★ 那个「只有 3 个」的清单里，事件**各不相同** ⟹
#   「外点关闭」是**逐个手写**的，没有统一机制 ──
evs = {s: sorted({o["event"] for o in oc[s]}) for s in withOc}
assert evs == {"contextMenu": ["mousedown"], "pathMenuLeft": ["pointerdown"],
               "presetPanelLeft": ["pointerdown"]}, (
    "★ 外点关闭的事件清单变成 %r ⟹ 「逐个手写、没有统一机制」要重算" % evs)
print("（阶段三）★ 三个人的外点事件**各不相同**（%r）⟹ 是**逐个手写**的，"
      "仓里**没有**统一机制" % evs)

# ── 预测 C：★ 树那个主人的外点关闭挂在 **`mousedown`** 上（不是 pointerdown）──
#   ⟹ 这决定了「键盘能不能绕过它」
tree = (REPO / TREE).read_text(encoding="utf-8")


def _body(text, start_idx):
    cb = text.find("{", start_idx)
    depth = 0
    for i in range(cb, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[cb:i + 1]
    return ""


# ★ 要取**整个 effect 体**：`mousedown` 监听在 `:212`，而 `esc` 处理器在
#   `:209` —— 按「从 useEffect 到 esc 那一行」切片会把监听**切掉**
#   （第一版就是这么写的，然后断言炸了）
eff = _body(tree, tree.rindex("useEffect("))
assert 'window.addEventListener("mousedown", close);' in eff, (
    "★ 树那个主人**没有** `mousedown` 外点关闭 ⟹ 「键盘能绕过」这条要重算")
assert re.search(r"const close = \(event: MouseEvent\) => \{[^}]*"
                 r"setContextMenu\(null\);", eff, re.S), (
    "★ 那个 `close` 里**没有直接** `setContextMenu(null)` ⟹ "
    "「键盘能绕过」这条要重算")
# ★ 模型库触发器是 `<button onClick>` ⟹ 键盘 `Enter` 只产生 `click`
vp = (REPO / VP).read_text(encoding="utf-8")
# ★ 那个开标签**跨多行**，正则要求「`>` 后面紧跟 `<button`/`</div`」匹配不到
#   ⟹ 改成「从属性往前找最近的 `<button`，往后取到**第一个** `>`」
_iAttr = vp.index("data-director-model-library-trigger")
_iOpen = vp.rindex("<button", 0, _iAttr)
trig = vp[_iOpen:vp.index(">", _iAttr) + 1]
assert "onClick" in trig and 'type="button"' in trig, (
    "★ 模型库触发器**不是** `<button type=button onClick>` ⟹ "
    "「键盘激活不产生 mousedown」这条要重算")
print("（阶段四）★ 树那个主人的外点关闭在 **`mousedown`** 且 `close` 里"
      "**直接** `setContextMenu(null)`；模型库触发器是 "
      "`<button type=\"button\" onClick>` ⟹ ★ **键盘 `Enter` 激活它不产生 "
      "`mousedown`** ⟹ 那道互斥**只挡鼠标**")

# ═══════════════ 2. 运行时 ═══════════════
raw = json.loads(RAW.read_text(encoding="utf-8"))
rounds = raw["rounds"]
assert len(rounds) == ROUNDS, "轮数不是 %d" % ROUNDS
arms = {}
for rd in rounds:
    for r in strip(rd.get("rows")):
        arms.setdefault(r.get("arm"), []).append(r)
assert set(arms) == set(ARMS), "臂集合不符：%r" % sorted(arms)
bad = [(k, v[0].get("FAILED")) for k, v in arms.items() if v[0].get("FAILED")]
assert not bad, "★ 有 FAILED：%r" % bad
for k, rs in arms.items():
    assert len(rs) == ROUNDS, "★ %s 只有 %d 轮" % (k, len(rs))
    assert all(reading(x) == reading(rs[0]) for x in rs), "★ %s 两轮不一致" % k
# ★ 「行数」与「按压格数」是两个量：第一版把行数（%d）当成了格数，
#   而 %d 臂 × %d 次 × %d 轮 = %d。★ 与 775 的 8→6、782 的 12 格标签同族。
ROWS = sum(len(v) for v in arms.values())
CELLS = ROWS * PRESSES
print("（阶段五）%d 轮 × %d 臂 = **%d 行**；%d 行 × %d 次按压 = **%d 个"
      "按压格**，零 FAILED，两轮逐字段一致"
      % (ROUNDS, len(arms), ROWS, ROWS, PRESSES, CELLS))


def arm(k):
    return arms[k][0]


def coLive(k):
    """★ **从 `after2` 重算**共活 —— 不信探针自己那个 `coLive` 字段。"""
    a2 = arm(k).get("after2") or {}
    return bool(a2.get("ctxOpen") is True and a2.get("libOpen") is True)


# ── 预测 D：★ 鼠标激活**不**共活（`mousedown` 关掉了右键菜单）──
ms, kb = arm("ctxThenLibMouse"), arm("ctxThenLibKeyboard")
assert (ms.get("after1") or {}).get("ctxOpen") is True, (
    "★ mouse 臂第 1 步右键菜单没开 ⟹ 不是有效读数")
assert (ms.get("after2") or {}).get("libOpen") is True, (
    "★ mouse 臂第 2 步模型库没开 ⟹ 不是有效读数")
assert (ms.get("after2") or {}).get("ctxOpen") is False, (
    "★ mouse 臂第 2 步后**右键菜单仍开着** ⟹ 「鼠标下互斥」**被否**，"
    "而静态说 `mousedown` 会关掉它 ⟹ 机制读错了")
print("（阶段六）★ mouse 臂：第 2 步后 `ctx=False, lib=True` ⟹ "
      "**不共活**（`mousedown` 关掉了右键菜单）⟹ 预测 ① 成立")

# ── 预测 E：★★ 键盘激活**共活** ──
assert (kb.get("after1") or {}).get("ctxOpen") is True, (
    "★ keyboard 臂第 1 步右键菜单没开 ⟹ 不是有效读数")
assert (kb.get("after2") or {}).get("libOpen") is True, (
    "★ keyboard 臂第 2 步模型库没开 ⟹ 不是有效读数")
assert coLive("ctxThenLibKeyboard"), (
    "★ keyboard 臂第 2 步后**两个都开着**这件事不成立 ⟹ "
    "「键盘能绕过 `mousedown`」**被否** ⟹ 机制读错了")
print("（阶段六）★★ keyboard 臂：第 2 步后 `ctx=True, lib=True` ⟹ "
      "**共活** ⟹ 预测 ② 成立（「键盘 `Enter` 不产生 `mousedown`」）")

# ── 预测 F：★★ 共活时一次 Escape **只关 `sIP` 那个**，bubble 那个留在原地 ──
p1, p2 = kb["presses"][0], kb["presses"][1]
assert p1["read"].get("cap") == 0 and p1["read"].get("win") == 0, (
    "★ keyboard 臂第 1 次 cap=%r win=%r，而预测是**双双为 0**"
    "（`sIP` 截断整条链）⟹ 「共活时只关一个」这条要重算"
    % (p1["read"].get("cap"), p1["read"].get("win")))
assert p1["state"].get("libOpen") is False, (
    "★ keyboard 臂第 1 次后**模型库仍开着** ⟹ 「`sIP` 那个先关」要重算")
assert p1["state"].get("ctxOpen") is True, (
    "★ keyboard 臂第 1 次后**右键菜单被关掉了** ⟹ "
    "★ **预测被否** —— bubble 主人居然跑了，"
    "而 `cap=0` 说明整条链被截断 ⟹ 机制与我读的不一样，J784-3 要重写")
assert p1["state"].get("exportOpen") is True, (
    "★ keyboard 臂第 1 次后**导出面板被关掉了** ⟹ "
    "「桌的阶梯也跑不到」这条要重算")
print("（阶段六）★★ keyboard 臂第 1 次：cap=0 win=0（`sIP` 截断整条链）｜"
      "**模型库关了、右键菜单留在原地、导出面板也留在原地** ⟹ "
      "★ **一次 Escape 只关掉 `sIP` 那个**，bubble 那个**留在原地**")
assert p2["state"].get("ctxOpen") is False, (
    "★ keyboard 臂第 2 次后**右键菜单仍开着** ⟹ 「要按第二次」这条要重算")
assert p2["state"].get("exportOpen") is False, (
    "★ keyboard 臂第 2 次后**导出面板仍开着** ⟹ 「第 2 次阶梯才跑」要重算")
print("（阶段六）★ keyboard 臂第 2 次：右键菜单关了、导出面板也关了 ⟹ "
      "**要按两次 Escape**")

# ── 预测 G：两个对照臂（判别力）──
co = arm("ctxOnly")["presses"][0]
lo = arm("libOnly")["presses"][0]
assert co["read"].get("cap") >= 1 and co["state"].get("ctxOpen") is False, (
    "★ `ctxOnly` 对照臂：右键菜单**单独**开着时第 1 次就关了、且 `cap>=1` "
    "⟹ 判别力为零")
assert co["state"].get("exportOpen") is False, (
    "★ `ctxOnly` 对照臂第 1 次后导出面板**仍开着** ⟹ "
    "「两个 bubble 主人并发」这条要重算")
print("（阶段六）`ctxOnly` 对照：第 1 次 cap>=1、右键菜单关、**导出面板也关** "
      "⟹ 两个 bubble 主人并发（782 的 J4 再次成立）")
assert lo["read"].get("cap") == 0 and lo["state"].get("libOpen") is False, (
    "★ `libOnly` 对照臂：模型库**单独**开着时第 1 次 `cap` 应为 0 且它关掉 "
    "⟹ 判别力为零")
assert lo["state"].get("exportOpen") is True, (
    "★ `libOnly` 对照臂第 1 次后导出面板**被关掉了** ⟹ "
    "「`sIP` 单独活着时阶梯也跑不到」这条要重算（782 的读数）")
print("（阶段六）`libOnly` 对照：第 1 次 cap=0、模型库关、**导出面板仍在** ⟹ "
      "★ **`sIP` 单独活着时，Escape 也要按两次才能走到桌的阶梯**"
      "（782 的读数第二次复现）")

# ── 预测 H：★ 探针自己那个 `coLive` 字段**是错的** ──
wrong = [k for k in ARMS if arm(k).get("coLive") is not None
         and bool(arm(k)["coLive"]) != coLive(k)]
assert wrong == ["ctxThenLibMouse"], (
    "★ 探针的 `coLive` 字段与重算一致的臂变成 %r ⟹ 「探针派生字段是错的」"
    "这条要重算" % wrong)
print("（阶段六）★★ 探针记的 `coLive` 字段在 %r 臂上**与重算不符** ⟹ "
      "★ 那个字段只看了「第一个开了 ctx」+「第二个开了 lib」，"
      "**没检查第一个是不是还开着** ⟹ 汇编器一律重算" % wrong)

# ═══════════════ 3. 可比性 ═══════════════
r0 = [reading(x) for x in strip(rounds[0].get("rows"))]
r1 = [reading(x) for x in strip(rounds[1].get("rows"))]
tries = [r.get("tries", 1) for rd in rounds for r in (rd.get("rows") or [])]
comparability = {
    "rounds": ROUNDS, "armsPerRound": len(arms),
    "cells": ROWS, "pressCells": CELLS,
    "allConsistent": r0 == r1,
    "censusMethod": cen.get("method"),
    "censusNotCovered": cen.get("notCovered"),
    "retryPolicy": "每格最多试 3 次（含第一次）；`tries`/`retried` 记进 raw "
                   "但**排除在两轮一致性比较之外**。",
    "retryStats": {"cells": len(tries),
                   "retriedCells": sum(1 for t in tries if t > 1),
                   "maxTries": max(tries) if tries else None},
    "boundary": "★ **本批未改 `src/`，也没有任何注入。** 只右键一个树行、"
                "开/关模型库与按 `Escape`，**不做任何破坏性操作**"
                "（**从不点右键菜单里的任何一项** —— 那一项里有「删除」；"
                "不点删除/提交/连接/新增机位/导入导出，不做付费或真实"
                "生图生视频）；每格开头 `fresh()` 清 localStorage ⟹ 不留残留。",
}
assert comparability["allConsistent"] is True, "★ 两轮不一致"

# ═══════════════ 4. 结论 ═══════════════
judgments = [
    {"id": "J784-1",
     "text": "★ **11 个 `Escape` 主人对应的门状态里，只有 3 个有任何外点关闭**"
             "（`contextMenu`←`mousedown`、`pathMenuLeft`/`presetPanelLeft`"
             "←`pointerdown`），**其余 7 个一个都没有** ⟹ "
             "「层内 Escape 只关层」这件事**没有全局保障**，"
             "774 那个「全族只有 2/6 做对」现在有了机制层的解释。",
     "evidence": "阶段一 + 阶段二"},
    {"id": "J784-2",
     "text": "★ **那 3 个的外点事件各不相同**（`mousedown` / `pointerdown` / "
             "`pointerdown`）⟹ 是**逐个手写**的，仓里**没有**统一机制。",
     "evidence": "阶段三"},
    {"id": "J784-3",
     "text": "★★ **外点关闭只挡鼠标。** 树那个主人的互斥挂在 **`mousedown`** 上，"
             "而模型库触发器是 `<button type=\"button\" onClick>` ⟹ "
             "**键盘 `Enter` 激活它只产生 `click`、不产生 `mousedown`**。"
             "实测：鼠标臂**不**共活（`ctx=False, lib=True`），"
             "**键盘臂共活**（`ctx=True, lib=True`）⟹ 预测两条都成立。",
     "evidence": "阶段四 + 阶段六 预测 D/E"},
    {"id": "J784-4",
     "text": "★★★ **`sIP` 主人与 bubble 主人共活时，一次 Escape 只关掉 "
             "`sIP` 那个**，bubble 那个**留在原地**：键盘臂第 1 次 "
             "`cap=0, win=0`（`sIP` 截断整条链）、模型库关、"
             "**右键菜单仍在**、**导出面板仍在**（桌的阶梯也跑不到）⟹ "
             "**要按第二次**。⟹ 「层内 Escape 只关层」在共活时**不成立**，"
             "而且**第一次按压对那一层完全没有反馈**。",
     "evidence": "阶段六 预测 F"},
    {"id": "J784-5",
     "text": "★ **`sIP` 单独活着时也一样要按两次**：`libOnly` 对照臂第 1 次 "
             "`cap=0`、模型库关、**导出面板仍在** ⟹ 782 那条读数第二次复现。",
     "evidence": "阶段六 预测 G"},
    {"id": "J784-6",
     "text": "★ **两个 bubble 主人仍然并发**：`ctxOnly` 对照臂第 1 次 "
             "`cap>=1`、右键菜单关、**导出面板也关** ⟹ 782 的 J4 再次成立。",
     "evidence": "阶段六 预测 G"},
]
corrections = [
    {"id": "C784-1",
     "targets": ["**D8a 的范围**（「`DirectorTimeline:570/594` 改 `sIP` 会让"
                 "菜单开着时阶梯跑不到」）"],
     "was": "读作「这是那两个时间轴菜单**特有**的代价」。",
     "now": "★ **要改写成一般形态**：784 测到的是「**任何** `sIP` 主人与"
            "**任何** bubble 主人共活时，bubble 那个就关不掉」—— "
            "**与它们是不是时间轴菜单无关**。\n"
            "★ 而这对 D8 反而是**支持性证据**：`DirectorTimeline` 那两个"
            "因为有**双向交叉写入**（783 已证）⟹ **永不共活** ⟹ "
            "把它们升级成 `sIP` **不会**制造「一个关不掉」。\n"
            "⟹ **真正的风险面是那 7 个既没有外点关闭、也没有交叉写入的"
            "门状态**（见 D1i），D8 只是先把两个**安全**的升了。",
     "evidence": "J784-4 + 783 的 J783-2"},
    {"id": "C784-2",
     "targets": ["**`dbg784a.py` 记的 `coLive` 字段**"],
     "was": "读作「该臂的两个面板是否同时开着」。",
     "now": "★ **它算错了**：只看了「第一个开了 `ctx`」+「第二个开了 `lib`」，"
            "**没检查第一个是不是还开着** ⟹ `ctxThenLibMouse` 被标成 "
            "`coLive=True`，而它自己的 `after2.ctxOpen=False`。\n"
            "⟹ **汇编器一律从 `after2` 重算**，并把"
            "「raw 里的派生字段与它自己的输入不一致」记成一条发现（R149）。",
     "evidence": "阶段六 预测 H"},
]
assert [c["id"] for c in corrections] == ["C784-1", "C784-2"]

probeLessons = [
    {"id": "R146b", "text": "★ **783 立的规矩我这一批又犯了两次，"
                            "而且都是「换个形式的同一件事」。** "
                            "① 用「取门状态 `ids` 的第一个」去猜每个主人的"
                            "门 ⟹ 给 `DirectorDesk:570` 算出 `state=capture`"
                            "（它真正的门是「桌开着」）。"
                            "② 判据写成「这条 pointer 监听**所在的 "
                            "`useEffect` 体**里有没有 `set<S>(null)`」⟹ "
                            "抓到**假阳性** `DirectorTimeline.tsx:771`"
                            "（`pointerup`/`handleUp`）—— 那是一段**拖拽结束**"
                            "的清理，`handleUp` 还是**一跳间接**调 `cleanup()`。\n"
                            "⟹ 第三版判据：**处理器自己的函数体里直接出现**"
                            "`set<S>(null)` ⟹ 同时排掉「不在 effect 里的代码」"
                            "与「一跳间接调用」。\n"
                            "★ 教训升级版：**「普查器不做语义判断」这条规矩，"
                            "光写下来不够 —— 它得同时写成**判据的形状**，"
                            "否则下一个人还会发明一个「看起来不是语义判断」"
                            "的启发式。"},
    {"id": "R149", "text": "★ **raw 里的派生字段要与它自己的输入对账。** "
                            "`dbg784a.py` 记的 `coLive` 在 "
                            "`ctxThenLibMouse` 臂上标了 `True`，"
                            "而同一行 raw 里的 `after2.ctxOpen` 是 `False`。\n"
                            "⟹ 如果汇编器直接读那个字段，**整批结论会翻**"
                            "（会说「鼠标下也共活」⟹ 于是「外点关闭只挡鼠标」"
                            "这条就没了）。⟹ **凡是 raw 里的派生字段，"
                            "汇编器都要从原始读数重算一遍并断言两者一致**；"
                            "不一致时**以重算为准**并把它记成一条发现。"},
]
assert [x["id"] for x in probeLessons] == ["R146b", "R149"]

defects = [
    {"id": "D1i", "severity": "中·共活时失效",
     "text": "★ **「层内 Escape 只关层」在 `sIP` 与 bubble 共活时不成立。** "
             "实测（`ctxThenLibKeyboard` 臂，两轮一致）：右键树行打开右键菜单后，"
             "用**键盘 `Enter`** 激活模型库触发器 ⟹ **两个面板同时开着**"
             "（键盘激活 `<button onClick>` **不产生 `mousedown`**，"
             "而右键菜单的外点关闭正挂在 `mousedown` 上）⟹ "
             "按第 1 次 Escape：`cap=0, win=0`（模型库那个 "
             "`DirectorViewport:2748` 的 `sIP` 截断整条链）⟹ "
             "**模型库关了、右键菜单留在原地、桌的阶梯也跑不到**"
             "（导出面板同样留在原地）⟹ **要按第 2 次**。\n"
             "★ **第一次按压对那一层完全没有反馈**，而它**看起来**像"
             "「Escape 没生效」。\n"
             "★ 范围：这不是那两个时间轴菜单特有的 —— "
             "**11 个主人里 7 个既没有外点关闭、也没有交叉写入**，"
             "其中任何一对 `sIP` × bubble 都有这个形态。"
             "⚠ **本批未测「第一次按压的反馈面板显示什么」**（探针没记 "
             "`lastCommand`）⟹ 「零反馈」这一条**只对右键菜单成立**，"
             "桌侧那一层本批**未测**。",
     "evidence": "J784-4 + 阶段六 预测 F + 阶段一/二"},
]
audit = {
    "batch": 784,
    "topic": "`sIP` 主人与 bubble 主人**共活**时的 Escape 行为："
             "预测成立 ⟹ 一次只关一个、另一个留在原地（新缺陷 D1i）；"
             "且 11 个主人里只有 3 个有任何外点关闭",
    "generatedBy": "probes/mk784audit.py",
    "sources": {
        "census784.json": {"sha16": sha(CENSUS),
                           "states": len(cen["states"])},
        "vb784a.json": {"sha16": sha(RAW), "rounds": ROUNDS,
                        "armsPerRound": len(arms)},
    },
    "outsideClose": {
        "withOutsideClose": withOc, "withoutOutsideClose": withoutOc,
        "events": evs,
        "note": "★ 判据 = 处理器**自己的**函数体里**直接**出现 "
                "`set<S>(null)` ⟹ 排掉「不在 effect 里的代码」与"
                "「一跳间接调用」",
    },
    "runtime": {k: {"after1": arm(k).get("after1"),
                    "after2": arm(k).get("after2"),
                    "coLiveRecomputed": coLive(k),
                    "coLiveInRaw": arm(k).get("coLive"),
                    "presses": arm(k).get("presses")} for k in ARMS},
    "verdict": {
        "共活可达吗": "★ **键盘下可达**：右键菜单 + 模型库**键盘**激活 ⟹ "
                      "两个都开着；★ **鼠标下不可达**（`mousedown` 会关掉"
                      "右键菜单）",
        "共活时一次 Escape 关几个": "★ **只关 `sIP` 那个**；bubble 那个"
                                    "**留在原地**且**无反馈**；桌的阶梯"
                                    "**也跑不到** ⟹ **要按两次**",
        "外点关闭的覆盖面": "★ 11 个主人的门状态里**只有 3 个**有，"
                            "**7 个一个都没有**；那 3 个的事件还**各不相同** "
                            "⟹ 逐个手写，仓里没有统一机制",
        "D8a 的范围": "★ 要改写成**一般形态**（与是不是时间轴菜单无关）；"
                      "但对 D8 本身是**支持性证据**（那两个永不共活）",
        "782 的读数": "★ `sIP` 单独活着时也要按两次 ⟹ 第二次复现",
    },
    "comparability": comparability,
    "results": {
        "gateStates": len(cen["states"]),
        "statesWithOutsideClose": len(withOc),
        "statesWithoutOutsideClose": len(withoutOc),
        "cells": ROWS, "pressCells": CELLS,
        "arms": len(arms), "presses": PRESSES,
        "failedCells": 0,
        "keyboardCoLive": coLive("ctxThenLibKeyboard"),
        "mouseCoLive": coLive("ctxThenLibMouse"),
        "rawFieldMismatchArms": wrong,
    },
    "judgments": judgments,
    "corrections": corrections,
    "findings": {
        "F1": "★ 11 个 `Escape` 主人的门状态里**只有 3 个**有外点关闭，"
              "7 个没有 ⟹ 「层内 Escape 只关层」**没有全局保障**。",
        "F2": "★ 那 3 个的外点事件**各不相同** ⟹ 逐个手写，仓里无统一机制。",
        "F3": "★★ **外点关闭只挡鼠标** ⟹ 键盘 `Enter` 激活 `<button onClick>` "
              "不产生 `mousedown` ⟹ 共活在键盘下**可达**（实测）。",
        "F4": "★★★ **共活时一次 Escape 只关 `sIP` 那个**，bubble 那个留在原地、"
              "无反馈，阶梯也跑不到 ⟹ 新缺陷 D1i。",
        "F5": "★ `sIP` 单独活着时也要按两次（782 读数第二次复现）。",
        "F6": "★ 探针的 `coLive` 派生字段**算错了** ⟹ 汇编器一律重算（R149）。",
    },
    "probeLessons": probeLessons,
    "defects": defects,
    "notMeasured": [
        "第一次按压时**桌侧反馈面板显示什么**（探针没记 `lastCommand`）⟹ "
        "「零反馈」只对右键菜单成立",
    ],
    "srcDiff": "**本批未改 `src/`**（工作区 `src/` 干净）；**没有任何注入**。",
    "rawSha": {"census784.json": sha(CENSUS), "vb784a.json": sha(RAW)},
    "retryStats": comparability["retryStats"],
    "boundary": comparability["boundary"],
}
OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote %s" % OUT)
