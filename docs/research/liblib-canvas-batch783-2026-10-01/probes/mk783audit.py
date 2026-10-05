#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 783 汇编器 —— 11 个 `Escape` 主人「**能不能同时活着**」

## 本批验的是 782 留下的那个缺口

782 数出了挂载域里 **11 个** `Escape` 主人，但只数了**形态**
（相位 / 有没有 `sIP`），没数**它们能不能同时活着** ——
而这才决定 Escape 的真实行为：同时活着时，一次按压会关掉几个？

## ★★ 本批的预测**被否掉了**，而否掉它的过程就是本批的结论

**预测**（从源码逐行推出）：`DirectorTimeline:570` 与 `:594` 是**同文件、
相邻两个 `useEffect`、两个独立状态变量、零交叉守卫** ⟹ 静态上没有任何东西
保证它们不同时活着；而唯一的互斥机制是 `:569` 的 `pointerdown` 外点关闭
⟹ **键盘激活不产生 `pointerdown`** ⟹ 键盘下应该能同时开着。

**实测**：`bothByMouse` 与 `bothByKeyboard` 的读数**完全一样** ——
第二个面板打开后，**第一个（路径菜单）被关掉了**。
⟹ 「键盘能绕过外点关闭」**被否掉**；「唯一的互斥机制是 `pointerdown`」**被否掉**。

**真机制**（找到的，不是猜的）：互斥是**两个「打开者」里各一行的显式交叉写入** ——
`togglePathMenu`（`:601`）第 3 行 `setPresetPanelLeft(null);`、
`togglePresetPanel`（`:695`）第 10 行 `setPathMenuLeft(null);`
⟹ **双向、可证、设计好的不变量。**

## ★★ 而这才是本批真正的结论：「主人的门互相独立」≠「主人可以同时活着」

782 的普查里，这两个主人看起来是**两个门状态互不相关**的主人 ——
**任何只看 Escape 主人的普查都看不见那个不变量，因为它写在打开者里。**
⟹ 这条**限制了 782 的普查能承载多少结论**：普查给的是「形态」与「门」，
**不是「可达的共活集合」**。

## 顺带更正一条 779 的计数

桌的阶梯除了 779 数过的四档，**自己还有两道门**：
`:551` `if (document.querySelector("[data-director-capture-viewer]")) return;`
（**DOM 存在性**，不是状态）与 `:552` `if (workspaceBusy) return;`
⟹ 779 的「阶梯有四档」不完整。
"""
import hashlib
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent.parent
BATCH = REPO / "docs/research/liblib-canvas-batch783-2026-10-01"
OUT = BATCH / "runtime-audit.json"
CENSUS = BATCH / "raw/census783.json"
RAW = BATCH / "raw/vb783a.json"
META = {"tries", "retried"}

TL = "src/components/director/DirectorTimeline.tsx"
DD = "src/components/director/DirectorDesk.tsx"
SURFACE_PRED = "resolveLibTVBlockingForegroundSurface"
ARMS = ["bothByMouse", "bothByKeyboard", "reverseByMouse", "pathOnly"]
PRESSES = 1
ROUNDS = 2


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
owners = cen["escapeOwners"]
tl = (REPO / TL).read_text(encoding="utf-8")
dd = (REPO / DD).read_text(encoding="utf-8")
print("（阶段一）Escape 主人 %d 个" % len(owners))

# ── 预测 A：从普查看，这两个 Timeline 主人的门**互不相关** ──
#   （这正是 782 会给出的印象，也是本批要检验的对象）
tlOwners = [o for o in owners if o["file"] == TL]
assert len(tlOwners) == 2, "★ `DirectorTimeline` 的 Escape 主人变成 %d 个" % len(tlOwners)
a, b = tlOwners
assert a["ids"] == ["pathMenuLeft"] and b["ids"] == ["presetPanelLeft"], (
    "★ 两个 Timeline 主人的门状态变成 %r / %r ⟹ 「门互不相关」这条要重算"
    % (a["ids"], b["ids"]))
censusLooksIndependent = True
print("（阶段二）普查看：%s 的门=%r、%s 的门=%r ⟹ ★ **两者互不相关**"
      "（这正是 782 会给的印象）" % (a["short"], a["ids"], b["short"], b["ids"]))

# ── 预测 B：★ 真正让它们互斥的是**打开者里的双向交叉写入** ──
assert "const togglePathMenu" in tl and "const togglePresetPanel" in tl, (
    "★ 找不到那两个打开者 ⟹ 「交叉写入」这条要重算")
iPath = tl.index("const togglePathMenu")
iPreset = tl.index("const togglePresetPanel")
# ★ 空白归一：源码里 `setPresetPanelLeft(` 与它的实参**分两行**，
#   不归一的话下面那个 needle 根本匹配不上（又是一次「断言写错」而非
#   「机制变了」——782 的 R148）
sq = lambda s: " ".join(s.split())  # noqa: E731
pathBody = sq(tl[iPath:tl.index("\n  };", iPath)])
presetBody = sq(tl[iPreset:tl.index("\n  };", iPreset)])
assert "setPresetPanelLeft(null);" in pathBody, (
    "★ `togglePathMenu` 里**没有** `setPresetPanelLeft(null)` ⟹ "
    "「互斥写在打开者里」这条要重算")
assert "setPathMenuLeft(null);" in presetBody, (
    "★ `togglePresetPanel` 里**没有** `setPathMenuLeft(null)` ⟹ "
    "「互斥是双向的」这条要重算")
# ★ 顺序要钉死：交叉写入必须**排在「打开自己」之前**。
#   ⚠ 「打开自己」不能用 `setX(` 找 —— 函数体里**第一处** `setX(` 是
#   toggle-off 分支的 `setX(null);`，拿它当基准会把顺序判反。
#   「打开」那一处实参是算出来的 ⟹ needle 取 `setX(Math.max`。
#   ⚠ needle 用**正则**而不是 `str.index`：源码里实参**另起一行**，
#   空白归一后是 `setX( Math.max` —— 字面量 needle 会 `ValueError`，
#   而那**不是**「机制变了」。★ 这是同一个教训的第三次形态（R148）。
_mPathOpen = re.search(r"setPathMenuLeft\(\s*Math\.max", pathBody)
_mPreOpen = re.search(r"setPresetPanelLeft\(\s*Math\.max", presetBody)
assert _mPathOpen and _mPreOpen, "★ 两个「打开自己」的调用没找到 ⟹ 顺序判据要重算"
assert pathBody.index("setPresetPanelLeft(null);") < _mPathOpen.start(), (
    "★ `togglePathMenu` 里关闭对方的那行**排在**打开自己之后 ⟹ "
    "「先关后开」这个读法要重算")
assert presetBody.index("setPathMenuLeft(null);") < _mPreOpen.start(), (
    "★ `togglePresetPanel` 里关闭对方的那行**排在**打开自己之后 ⟹ "
    "「先关后开」这个读法要重算")
# ★ 普查器自己也必须独立找到这两处（两个实现互相抓）——
#   判据用**结构**而不是计数：要「`togglePathMenu` 写 `pathMenuLeft` 时
#   顺手写了 `presetPanelLeft`」**且**「`togglePresetPanel` 写
#   `presetPanelLeft` 时顺手写了 `pathMenuLeft`」，两条都要在。
xw = [w for r in owners if r["file"] == TL for w in r["crossWrites"]
      if w["alsoWrites"]]
def _has(fn, st, other):
    return any(w["fn"] == fn and w["state"] == st and other in w["alsoWrites"]
               for w in xw)
assert _has("togglePathMenu", "pathMenuLeft", "presetPanelLeft"), (
    "★ 普查器**没有**找到「`togglePathMenu` 写 `pathMenuLeft` 时顺手写 "
    "`presetPanelLeft`」⟹ 与字面量核对不一致：%r" % xw)
assert _has("togglePresetPanel", "presetPanelLeft", "pathMenuLeft"), (
    "★ 普查器**没有**找到「`togglePresetPanel` 写 `presetPanelLeft` 时顺手写 "
    "`pathMenuLeft`」⟹ 「互斥是**双向**的」这条要重算：%r" % xw)
# ★ 普查器的 `alsoWrites` 是**函数级**的：同一函数里**每个** setter 调用点
#   都会带上「这个函数顺手写了谁」⟹ 一个交叉写入会被记成好几条。
#   ⟹ 正确的去重单位是**函数**（源码里那两行各自属于一个打开者）。
_xw2, _seenFn = [], set()
for w in xw:
    if w["fn"] in _seenFn:
        continue
    _seenFn.add(w["fn"])
    _xw2.append(w)
assert len(_xw2) == 2 and {w["fn"] for w in _xw2} == {"togglePathMenu",
                                                      "togglePresetPanel"}, (
    "★ 去重后是 %d 个函数 %r，预测是 2 个（`togglePathMenu` / "
    "`togglePresetPanel`）" % (len(_xw2), [w["fn"] for w in _xw2]))
print("（阶段三）★ 交叉写入（去重后 %d 处，函数=%s）⟹ `togglePathMenu:601` 写 `pathMenuLeft` 时"
      "**顺手写** `presetPanelLeft`；`togglePresetPanel:695` 反之 ⟹ "
      "**双向、可证、设计好的不变量**"
      % (len(_xw2), [w["fn"] for w in _xw2]))

# ── 预测 C：★ 桌的阶梯**自己还有两道门**，779 只数了四档 ──
iLadder = dd.index('if (event.key !== "Escape") return;')
ladder = dd[iLadder:dd.index("window.addEventListener", iLadder)]
assert 'if (document.querySelector("[data-director-capture-viewer]")) return;' \
    in ladder, (
    "★ 阶梯里**没有**那道 DOM 存在性守卫 ⟹ 「779 漏了两道门」这条要重算")
assert "if (workspaceBusy) return;" in ladder, (
    "★ 阶梯里**没有** `workspaceBusy` 那道门 ⟹ 「779 漏了两道门」这条要重算")
ladderGuards = len(re.findall(r"\bif\s*\(", ladder)) - 1  # 减去键守卫本身
print("（阶段四）★ 桌的阶梯在四档之外还有 **2 道**门"
      "（`:551` DOM 存在性、`:552` `workspaceBusy`）⟹ 779 的「阶梯有四档」不完整")

# ── 预测 D：`page.tsx` 的两个主人**共用一个 effect** ⟹ 门归属在那里是歧义的 ──
assert "app/page.tsx:1400" in cen.get("sharedEffectOwners", []), (
    "★ 普查器**没有**标记 `page.tsx:1400/1401` 共用 effect ⟹ "
    "「那一处门归属是歧义的」这条要重算")
print("（阶段五）★ `page.tsx:1400/1401` **共用同一个 `useEffect`** ⟹ "
      "逐主人的门归属在那一处是**歧义**的（普查器只能看到整个 effect 的全部"
      "守卫）；782 已用字面量分别钉死两道门 ⟹ 结论不受影响，但**必须写明**")

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
    # ★ 自检要**比两轮**；原来写成「拿元素跟它自己比」⟹ 恒真且轮数判错
    assert len(rs) == ROUNDS, "%s 只有 %d 轮" % (k, len(rs))
    assert all(reading(x) == reading(rs[0]) for x in rs), \
        "%s 两轮逐字段不一致" % k
CELLS = sum(len(v) for v in arms.values())
print("（阶段六）%d 轮 × %d 臂 × %d 次按压 = **%d 格**，零 FAILED，两轮逐字段一致"
      % (ROUNDS, len(arms), PRESSES, CELLS))


def arm(k):
    return arms[k][0]


def seq(k):
    """`afterFirst` → `afterSecond` → 按压后。"""
    r = arm(k)
    out = {"first": r.get("afterFirst") or {}, "press": []}
    if r.get("afterSecond"):
        out["second"] = r["afterSecond"]
    for p in r.get("presses") or []:
        out["press"].append(p)
    return out


# ── 预测 F：★★ 键盘激活**也**会关掉第一个面板 ⟹「唯一的互斥机制是
#   `pointerdown`」**被否掉** ──
kb, ms = seq("bothByKeyboard"), seq("bothByMouse")
for k, s in (("bothByKeyboard", kb), ("bothByMouse", ms)):
    assert s["first"].get("pathOpen") is True, (
        "★ %s 第 1 个面板（路径菜单）没开 ⟹ 不是有效读数" % k)
    assert s["second"].get("presetOpen") is True, (
        "★ %s 第 2 个面板（预设）没开 ⟹ 不是有效读数" % k)
    assert s["second"].get("pathOpen") is False, (
        "★ %s 第 2 个面板打开后**路径菜单仍开着** ⟹ 「两者可同时活着」"
        "**成立** ⟹ 我 783 的预测对，J783-1/2 要重写" % k)
# ★ 键盘臂与鼠标臂读数**一致** ⟹ 激活方式不影响互斥 ⟹ pointerdown 假设死
assert kb["second"] == ms["second"], (
    "★ 键盘臂与鼠标臂的第 2 步读数不同（%r vs %r）⟹ "
    "「互斥与激活方式无关」这条要重算"
    % (kb["second"], ms["second"]))
sameByActivation = kb["second"] == ms["second"]
print("（阶段六）★ 两个臂的第 2 步读数**完全一样**（路径菜单关、预设面板开）"
      "⟹ ★ **「键盘能绕过外点关闭」被否掉**；激活方式与互斥无关")

# ── 预测 G：★ 反向顺序（预设 → 路径）**也**互斥 ⟹ 交叉写入是双向的 ──
rv = seq("reverseByMouse")
assert rv["first"].get("presetOpen") is True, (
    "★ reverse 臂第 1 个面板（预设）没开 ⟹ 不是有效读数")
assert rv.get("second", {}).get("pathOpen") is True, (
    "★ reverse 臂第 2 个面板（路径）没开 ⟹ 不是有效读数")
assert rv["second"].get("presetOpen") is False, (
    "★ reverse 臂第 2 个面板打开后**预设面板仍开着** ⟹ 互斥是"
    "**单向**的 ⟹ 「双向」这条要重算（而字面量说双向）")
print("（阶段六）★ 反向顺序（预设 → 路径）：预设关、路径开 ⟹ "
      "**双向互斥**得到运行时确认")

# ── 预测 H：一次 Escape 关掉**两个**东西（面板 + 阶梯那档）⟹ 并发，非阻断 ──
for k in ("bothByMouse", "bothByKeyboard", "reverseByMouse", "pathOnly"):
    s = seq(k)
    for p in s["press"]:
        assert (p["read"].get("cap") or 0) >= 1, (
            "★ %s 第%s次 cap=%r ⟹ 按键没送达浏览器" % (k, p["n"],
                                                     p["read"].get("cap")))
        assert (p["read"].get("win") or 0) >= 1, (
            "★ %s 第%s次 win=%r ⟹ 事件没到 window ⟹ 有主人做了阻断，"
            "而本批三个臂**都不该有** sIP 主人活着" % (k, p["n"],
                                                      p["read"].get("win")))
        st = p["state"]
        assert st.get("exportOpen") is False, (
            "★ %s 第%s次后导出面板**仍开着** ⟹ 阶梯没跑"
            % (k, p["n"]))
        assert st.get("deskOpen") is True, (
            "★ %s 第%s次后桌**关掉了** ⟹ 阶梯跑过了头" % (k, p["n"]))
    wasOpen = [x for x in ("pathOpen", "presetOpen")
               if s["press"][0]["state"].get(x) is False
               and (s.get("second") or s["first"]).get(x) is not False]
    closed = [x for x in ("pathOpen", "presetOpen")
              if s["press"][0]["state"].get(x) is False and x in wasOpen]
    print("（阶段六）%s：一次 Escape 关掉 %s ｜导出面板**也**关（%r）⟹ "
          "★ **一次按压两个主人**（面板 + 阶梯）"
          % (k, closed or "（无面板可关）",
             s["press"][0]["state"].get("exportOpen")))

# ── 判别力对照臂：只开路径菜单 ──
po = seq("pathOnly")
assert po["first"].get("pathOpen") is True, "★ 对照臂起点路径菜单没开"
assert po["press"][0]["state"].get("pathOpen") is False, (
    "★ 对照臂按压后路径菜单**仍开着** ⟹ 判别力为零")
print("（阶段六）`pathOnly` 对照臂：路径菜单开→关 ⟹ 判别力成立")

# ═══════════════ 3. 可比性 ═══════════════
r0 = [reading(x) for x in strip(rounds[0].get("rows"))]
r1 = [reading(x) for x in strip(rounds[1].get("rows"))]
tries = [r.get("tries", 1) for rd in rounds for r in (rd.get("rows") or [])]
comparability = {
    "rounds": ROUNDS, "armsPerRound": len(arms), "cells": CELLS,
    "allConsistent": r0 == r1,
    "censusMethod": cen.get("method"),
    "censusNotCovered": cen.get("notCovered"),
    "retryPolicy": "每格最多试 3 次（含第一次）；`tries`/`retried` 记进 raw "
                   "但**排除在两轮一致性比较之外**。",
    "retryStats": {"cells": len(tries),
                   "retriedCells": sum(1 for t in tries if t > 1),
                   "maxTries": max(tries) if tries else None},
    "boundary": "★ **本批未改 `src/`，也没有任何注入。** 只开/关两个时间轴"
                "面板与按 `Escape`，**不做任何破坏性操作**（不点删除/提交/"
                "连接/新增机位/导入导出，不做付费或真实生图生视频）；"
                "每格开头 `fresh()` 清 localStorage ⟹ 不留残留。",
}
assert comparability["allConsistent"] is True, "★ 两轮不一致"

# ═══════════════ 4. 结论 ═══════════════
judgments = [
    {"id": "J783-1",
     "text": "★ **我的预测被否掉了。** 预测是「两个 Timeline Escape 主人的门"
             "状态互相独立 ⟹ 可以同时活着，而唯一的互斥机制是 `:569` 的 "
             "`pointerdown` 外点关闭 ⟹ **键盘激活不产生 `pointerdown`** "
             "⟹ 键盘下应该能共活」。实测：`bothByMouse` 与 `bothByKeyboard` "
             "第 2 步读数**完全一样**（路径菜单关、预设面板开）⟹ "
             "**「键盘能绕过外点关闭」不成立**，「唯一的互斥机制是 "
             "`pointerdown`」**不成立**。",
     "evidence": "阶段六 预测 F"},
    {"id": "J783-2",
     "text": "★ **真机制是打开者里的双向显式交叉写入**：`togglePathMenu:601` "
             "第 3 行 `setPresetPanelLeft(null);`、`togglePresetPanel:695` "
             "第 10 行 `setPathMenuLeft(null);`，两处都**排在打开自己之前** "
             "⟹ **双向、可证、设计好的不变量**。运行时两个方向都测到了。",
     "evidence": "阶段三 + 阶段六 预测 G"},
    {"id": "J783-3",
     "text": "★★ **「主人的门互相独立」≠「主人可以同时活着」。** 这两个主人在"
             "普查里是**两个门状态互不相关**的主人 —— 而**任何只看 Escape "
             "主人的普查都看不见那个不变量，因为它写在打开者里**。⟹ 这条"
             "**限制了 782 那份普查能承载多少结论**：普查给的是「形态」与"
             "「门」，**不是「可达的共活集合」**；后者只能靠运行时或"
             "专门扫打开者。",
     "evidence": "阶段二 vs 阶段三"},
    {"id": "J783-4",
     "text": "★ **更正 779 的一处计数**：桌的阶梯除了四档，**自己还有两道门** —— "
             "`:551` `if (document.querySelector(\"[data-director-capture-"
             "viewer]\")) return;`（**DOM 存在性**，不是状态）与 `:552` "
             "`if (workspaceBusy) return;` ⟹ 「阶梯有四档」不完整。"
             "★ 这不改 779 的结论（它测的时候这两道都是假），但授权文本里"
             "描述阶梯的形状时要写全。",
     "evidence": "阶段四"},
    {"id": "J783-5",
     "text": "★ **一次 Escape 仍然会关掉两个东西**（面板 + 阶梯那档）："
             "四个臂全部 `cap>=1` 且 `win>=1`（**没有任何 sIP 主人活着**）"
             "⟹ 互斥**不靠传播阻断实现**，两个 bubble 主人照旧并发 ⟹ "
             "782 的 J4（一次按压多主并发）在本批**再次成立**。",
     "evidence": "阶段六 预测 H"},
]
corrections = [
    {"id": "C783-1",
     "targets": ["**783 规划里写的预测**：「两个 Timeline Escape 主人可以同时"
                 "活着（键盘绕过外点关闭）⟹ 若 D8 把它们改成 `sIP`，"
                 "其中一个会永远关不掉」"],
     "was": "读作「两者的互斥只靠 `:569` 的 `pointerdown` 外点关闭；"
            "键盘激活不产生 `pointerdown` ⟹ 键盘下可共活 ⟹ D8 会把"
            "「一次关两个」变成「一个关不掉」。」",
     "now": "★ **整条撤回。** 实测两个激活方式读数**完全一样**，两者"
            "**任何时候都不同时活着** —— 互斥是 `togglePathMenu:601` 与 "
            "`togglePresetPanel:695` 里**各一行的显式交叉写入**"
            "（双向、可证）。⟹ **D8 不会**把「一次关两个」变成「一个关不掉」。\n"
            "★ **但 D8a 的另外两半不受影响**：779 的「层级优先级是产品决定」"
            "与 782 的「菜单会变成第 4/5 个 `sIP` 主人」讲的是"
            "**菜单与桌阶梯**之间的关系，不是两个菜单之间的关系 —— "
            "782 已实测那个阻断**真的**发生（captureOwner 臂导出面板仍开）。",
     "evidence": "J783-1 + J783-2 + 阶段六 预测 F/G"},
    {"id": "C783-2",
     "targets": ["**779 对桌阶梯形状的描述**：「阶梯有四档」"],
     "was": "读作「`DirectorDesk.tsx:549-568` 是四档：activeGesture / 导出面板 "
            "/ followTarget / closeWorkspace」。",
     "now": "★ **不完整**：四档之前还有**两道门** —— `:551` 的 "
            "`document.querySelector(\"[data-director-capture-viewer]\")`"
            "（**DOM 存在性**，不是状态）与 `:552` 的 `workspaceBusy` "
            "⟹ 阶梯其实是「两道门 + 四档」。\n"
            "★ 不改 779 的结论（它测的时候这两道都是假），但**授权文本里"
            "描述阶梯的形状要写全** —— 否则下一个人会以为"
            "「有活动手势时 Escape 怎么走」只取决于四档。",
     "evidence": "J783-4 + 阶段四"},
]
assert [c["id"] for c in corrections] == ["C783-1", "C783-2"]

probeLessons = [
    {"id": "R146", "text": "★ **普查器不该做语义判断 —— 本批连踩两次。**"
                            "① 第一次想给每个主人标「激活门」，规则是"
                            "「提到 `event.key` 的是键守卫、其余是激活门」"
                            "⟹ **正则吃不下条件里的 `)`**"
                            "（`f(uiState)` 里 `uiState)` 先把 `[^)]*` 截断）"
                            "⟹ `page.tsx:1400` 的门整条丢失，**而输出里仍有"
                            "另一条门的标识符，看起来仍像个正常结果**；"
                            "而且那个分类学本身也站不住 —— 它把桌的 `:487` "
                            "`if (isEditable) return;` 也算成激活门，"
                            "而那是**分发守卫**。② 第二次改成一两两判「A 的条件"
                            "有没有提到 B 的状态」，被 `Escape`/`key`/`target` "
                            "淹没 —— 45 对「互相牵制」全是噪声。\n"
                            "⟹ **两次都是同一族**：把「看起来能自动判的东西」"
                            "交给正则。⟹ 改法是**把分类整个扔掉**，普查只"
                            "采集（条件用括号配对取、记行号），"
                            "**结论由汇编器用行锚定的字面量断言下**"
                            "（782 验收器已验证这条路）。"},
    {"id": "R147", "text": "★ **普查的「不相关」不等于「可共活」—— 而这条"
                            "只能靠把扫描范围挪一挪才看得见。** 两个 Timeline "
                            "Escape 主人的门状态互不相关（普查如实报告了），"
                            "可它们**永远不同时活着**，因为互斥写在"
                            "**打开者**里（`togglePathMenu:601` / "
                            "`togglePresetPanel:695` 各一行交叉写入）—— "
                            "**任何只看「主人」的普查都不会去看打开者**。\n"
                            "⟹ 普查器因此**加了一层** `crossWrites` 扫描"
                            "（找每个门状态的写入点落在哪个函数、那个函数"
                            "**有没有顺手写另一个门状态**），真机制立刻就出来了。\n"
                            "★ 推论：**「我扫的东西里没有 X」不能推出「X 不存在」**，"
                            "只能推出「X 不在我扫的范围里」—— 而这句话对"
                            "上一批那份普查的**每一列**都成立。"},
    {"id": "R148", "text": "★ **预测被否掉时，先去找真机制，别急着改断言。** "
                            "本批的预测（「键盘能绕过 `pointerdown` 外点关闭」）"
                            "被实测否掉，两臂读数完全一致。第一反应若是"
                            "「探针没测准」就会去改探针；而两臂一致这件事"
                            "**恰恰是**「互斥与激活方式无关」的强证据。\n"
                            "⟹ 顺着否掉的预测往下找，30 分钟就定位到"
                            "两行 `setX(null)` ⟹ 而那两行**就在源码里**，"
                            "只是不在主人身上。\n"
                            "★ 配套的一条：**只测一个顺序是不够的** —— 我第一版"
                            "只测了「路径→预设」，静态读到反向也有交叉写入后"
                            "**补了 `reverseByMouse` 臂**把结论从"
                            "「静态推断」变成「两个方向都是读数」。"},
]
assert [x["id"] for x in probeLessons] == ["R146", "R147", "R148"]

audit = {
    "batch": 783,
    "topic": "11 个 `Escape` 主人「能不能同时活着」：**预测被否**，真机制是"
             "打开者里的双向交叉写入 ⟹「门互相独立」≠「可共活」",
    "generatedBy": "probes/mk783audit.py",
    "sources": {
        "census783.json": {"sha16": sha(CENSUS), "owners": len(owners)},
        "vb783a.json": {"sha16": sha(RAW), "rounds": ROUNDS,
                        "armsPerRound": len(arms)},
    },
    "owners": owners,
    "coLive": {
        "censusLooksIndependent": censusLooksIndependent,
        "pair": [a["short"], b["short"]],
        "gateStates": [a["ids"], b["ids"]],
        "crossWrites": [{"fn": w["fn"], "fnLine": w["fnLine"],
                         "state": w["state"], "alsoWrites": w["alsoWrites"]}
                        for w in _xw2],
        "runtimeBothOrdersExclusive": True,
        "activationMethodIrrelevant": sameByActivation,
        "predictionRefuted": True,
    },
    "runtime": {k: seq(k) for k in ARMS},
    "verdict": {
        "我的预测": "★ **被否掉** —— 键盘激活**也**会关掉第一个面板，"
                    "「唯一的互斥机制是 `pointerdown`」不成立",
        "真机制": "★ **打开者里的双向显式交叉写入**"
                  "（`togglePathMenu:601`、`togglePresetPanel:695`）",
        "782 普查的效力": "★ **受限** —— 普查给的是「形态」与「门」，"
                          "**不是「可达的共活集合」**；互斥不变量写在"
                          "**打开者**里，任何只看主人的普查都看不见",
        "D8 的那条伤害": "★ **撤回**（C783-1）—— 两者永不共活，"
                         "D8 不会造成「一个关不掉」；D8a 的另外两半不受影响",
        "779 的阶梯形状": "★ **不完整**（C783-2）—— 是「**两道门 + 四档**」，"
                          "不是「四档」",
        "一次 Escape 关几个": "★ **两个**（面板 + 阶梯那档），四个臂全部 "
                             "`cap>=1` 且 `win>=1` ⟹ 不靠传播阻断",
    },
    "comparability": comparability,
    "results": {
        "escapeOwners": len(owners),
        "cells": CELLS, "arms": len(arms), "failedCells": 0,
        "crossWrites": len(_xw2),
        "ladderExtraGuards": 2,
        "predictionRefuted": True,
        "bothOrdersExclusive": True,
    },
    "judgments": judgments,
    "corrections": corrections,
    "findings": {
        "F1": "★ **预测被否**：键盘激活与鼠标激活读数完全一致 ⟹ "
              "「`pointerdown` 外点关闭是唯一互斥机制」不成立。",
        "F2": "★ **真机制 = 打开者里的双向交叉写入**，两方向都拿到运行时读数。",
        "F3": "★★ **「门互相独立」≠「可共活」** ⟹ 782 普查的效力被限定："
              "它给形态与门，**不给可达的共活集合**。",
        "F4": "★ **更正 779**：阶梯是「**两道门 + 四档**」，不是「四档」。",
        "F5": "★ **一次 Escape 仍关两个东西**，四个臂 `cap/win` 都 ≥1 "
              "⟹ 并发不靠传播阻断（782 的 J4 再次成立）。",
    },
    "probeLessons": probeLessons,
    "defects": [],
    "srcDiff": "**本批未改 `src/`**（工作区 `src/` 干净）；**没有任何注入**。",
    "rawSha": {"census783.json": sha(CENSUS), "vb783a.json": sha(RAW)},
    "retryStats": comparability["retryStats"],
    "boundary": comparability["boundary"],
}
OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote %s" % OUT)
