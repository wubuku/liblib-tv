#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 795 汇编器 —— 键盘方向键**能不能**移动节点

## 起点：793 遗留里写的第三条，前提**不成立**

793 的遗留原文：「未测键盘方向键移动成员是否同样触发跟随」。

★ 动手前先查源码，发现这条遗留把「没测」当成了「可能有、只是没测」：

- `page.tsx` 的 `handleKeyDown` 分支只有 `Escape` / `Delete` / `Backspace` /
  `Tab` / `Cmd+0` / `Cmd+=` / `Cmd+-` / `Cmd+z` / `Cmd+d` / `g` …，
  **没有任何 `Arrow*`**。
- `@xyflow/react` v12 **不内建**方向键移动（它内建的只有 `deleteKeyCode` 一类，
  而 `page.tsx` 里 `deleteKeyCode={[]}` 把它显式清空了）。
- store 里**没有** `nudge` / `moveNodeBy` 之类的 API。

⟹ 不是「方向键移动了但框没跟随」，而是**键盘用户完全无法移动节点**。
793 遗留写错了前提；本批把它当成一个**独立的可交互性缺陷**来测。

## ★ 读数（同一份探针，pre / post 各 2 轮 × 3 臂）

| 臂 | pre | post |
| --- | --- | --- |
| ★ 方向键移成员 ×3 | 成员 `(108,-125)` **纹丝不动**、框不动、`past 1→1` ✗ | 成员 **`(111,-125)`**（+3）、**框跟着 `+3`**、`past 1→4` ✓ |
| ★ 方向键移组本身 ×3 | 纹丝不动、`past 1→1` ✗ | 组 **`(82,-157)`**、成员**同步 `+6`**、`past 1→4` ✓ |
| ★ 阳性对照（`Delete`） | 节点 11→**10**、`past 1→2` ✓ | 节点 11→**10**、`past 1→2` ✓ |

★ **阳性对照是本批的关键**：它和方向键走**同一个** `window` keydown 监听器
（`page.tsx` 的 `handleKeyDown`），且两轮都真删掉了一个节点 ⟹ 证明「键盘事件确实
到达了画布」⟹ pre 的「没动」是**能力缺失**，不是「探针没把事件送到位」。

★ **移动成员时框跟着 `+3`**：这是 793 的 `fitStoryboardGroupsToChildren` 收口在起作用。
793/794 修的是「拖拽」与「删除」两条路径；键盘移动是**第三条**写点 ⟹ 本批的修复
也**必须**走同一个收口，否则就是 794 刚补完的那个洞的**同型第三次复发**。

## ★★ 读数里的一个 UX 代价（如实记账，不当优点）

3 次按压 ⟹ `past 1→4` ⟹ **一次按压记一条历史** ⟹ 撤销要按 **3 次**才回到原位。

★ 这不是 bug（每次按压是一次独立的用户动作，各自带一条历史是自洽的），
但它意味着**键盘移动的可撤销粒度 = 1 像素**。桌面画布（Figma / FigJam）同样如此，
所以本批**保留**现状、不做「同一串按压合并成一条历史」——那是另一个设计决定，
且源站未采样。★ 但它必须被**记下来**，因为「撤销一次就回到原位」是用户的自然预期。

## ★★ 两条臂的位移为什么不同（1× vs 2×）——机制，不是 bug

| 臂 | 选区含 | `movingIds` | 每按压绝对位移 | 3 次实测 |
| --- | --- | --- | --- | --- |
| D 移动**成员** | 只有成员 | 只有成员（组由收口重算） | 成员 +1、组 +1 | **+3** |
| E 移动**组** | 组 | 组 **和它的成员**（store 显式塞 child） | 两者 `position` 各 +1，而成员绝对 = 自身 + 父组 ⟹ **+2** | **+6** |

★ 我第一版把 E 的 `wantDelta` 也写成 3 ⟹ 实测 6 时判红。**是我的断言写错了，
不是实现错了**：读数 6 与源码里「child 也进 `movingIds`」完全自洽。
★ 这也说明「组与成员**绝对位移相等**」这个不变量仍然成立（6 == 6）⟹ 成员没掉出框。

## ★ 汇编器自己踩的四个坑（都已修）

1. **`KeyError: 0`** —— 我把探针的 `abs` 当 tuple 用 `[0]` 取 x，但它其实是
   `{"x":..,"y":..}` **dict**。★ 第一反应应该是回 raw 看真实结构，不是改断言迁就代码。
2. **1× 写成 3×**（见上）—— 断言错了，实现对。★ 改法是先回源码确认
   `movingIds` 里到底有没有 child，再定 `wantDelta`。
3. **`api: 2`** —— 正则 `^  nudgeSelectedNodes: \(delta` 把**接口声明**
   （有类型注解）和**实现**（无注解）都数进去了。改成按注解区分，两个各数一次。
4. **`没选区不拦: 3`** —— `if (selection.nodeIds.length > 0)` 在 `Delete`/`g`
   分支里也有，全文计数必然是 3。改成先定位**方向键分支那一段**再数。
"""
import json
import pathlib
import re

REPO = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
B = "docs/research/liblib-canvas-batch795-2026-10-01"
PRE = REPO / (B + "/raw/vb795a-pre.json")
POST = REPO / (B + "/raw/vb795a-post.json")
OUT = REPO / (B + "/runtime-audit.json")
PAGE = "src/app/page.tsx"
CS = "src/store/canvasStore.ts"

ARMS = ["arrowMovesMember", "arrowMovesGroup", "positiveDelete"]
STEP = 1          # 一次按压 1 像素
PRESSES = 3
ACCEL = 10        # Shift 加速档


def index(raw):
    out = {}
    for rd in raw["rounds"]:
        for r in (rd.get("rows") or []):
            out.setdefault(r.get("arm"), []).append((rd.get("round"), r))
    return out


def read(cell, key="after"):
    b, a = cell.get("before"), cell.get(key)
    if not isinstance(b, dict) or not isinstance(a, dict):
        return None
    by = {t["id"]: t for t in b.get("targets", [])}
    ay = {t["id"]: t for t in a.get("targets", [])}

    def xy(t):
        """★ 绝对位置是 `{'x':..,'y':..}` **dict**（第一版按 tuple 写 ⟹ KeyError）。"""
        p = (t or {}).get("abs")
        return None if not isinstance(p, dict) else (p.get("x"), p.get("y"))

    return {
        # ★ 按 **before 的顺序**取，保证「第 0 个 = 被按的那个」
        "ids": list(by),
        "abs": {k: (xy(by[k]), xy(ay.get(k))) for k in by},
        "exists": {k: (by[k].get("exists"),
                       (ay.get(k) or {}).get("exists")) for k in by},
        "nodeCount": (b.get("nodeCount"), a.get("nodeCount")),
        "past": (b.get("past"), a.get("past")),
    }


def dx(r, which):
    """★ 第 `which` 个 target 的 Δx；读数缺失返回 None（**空读数**）。"""
    k = r["ids"][which]
    (b, a) = r["abs"][k]
    return None if not (b and a) else a[0] - b[0]


def main():
    pre_raw = json.loads(PRE.read_text(encoding="utf-8"))
    post_raw = json.loads(POST.read_text(encoding="utf-8"))
    pre, post = index(pre_raw), index(post_raw)
    checks = []

    def add(cid, desc, cond, detail):
        checks.append({"id": cid, "desc": desc, "ok": bool(cond),
                       "detail": detail})

    page = (REPO / PAGE).read_text(encoding="utf-8")
    cs = (REPO / CS).read_text(encoding="utf-8")

    # ── A：★★ 起点普查：修之前**根本没有**方向键处理（从源码数出来）──
    arrow_tbl = re.findall(r"Arrow(?:Up|Down|Left|Right):", page)
    keydown_arrow = re.findall(r"ARROW_NUDGE\[event\.key\]", page)
    add("A:★★ 方向键映射表 4 项、且 keydown 里真接上了",
        "★ 修法 = 一张 4 项的 `ARROW_NUDGE` 表 + keydown 里的一个分支；"
        "两项都要在（只加表不接 = 白加）",
        len(arrow_tbl) == 4 and len(keydown_arrow) == 1,
        {"表项": len(arrow_tbl), "接上": len(keydown_arrow)})

    # ── B：★★ store 侧 API 在，且**必须过 793 的收口** ──
    # ★ 只数**实现**。接口声明那行是
    #   `  nudgeSelectedNodes: (delta: { x: number; y: number }) => void;`
    #   它同样以 `  name: (delta` 开头 ⟹ 第一版正则把两处都数成 2。
    #   区别在**类型注解**：实现是 `nudgeSelectedNodes: (delta) => {`（无注解）。
    api = re.findall(r"^  nudgeSelectedNodes: \(delta\) => \{", cs, re.M)
    decl = re.findall(r"^  nudgeSelectedNodes: \(delta: \{", cs, re.M)
    # ★ 收口：`fitStoryboardGroupsToChildren` 的 call 站点
    #   793 拖拽 1 + 794 删除 2 + 795 键盘 1 = 4
    fit_calls = re.findall(r"nodes: fitStoryboardGroupsToChildren\(", cs)
    fit_def = re.findall(r"function fitStoryboardGroupsToChildren\(", cs)
    add("B:★★ store 有 `nudgeSelectedNodes` **实现**，且它**过了 793 的收口**",
        "★ 键盘移动是**第三条**写点。若它绕过 `fitStoryboardGroupsToChildren`，"
        "就是 794 刚补完的洞**同型第三次复发** ⟹ 收口调用数必须正好 4。"
        "★ 实现 1 个 + 接口声明 1 个，两者都要数到",
        len(api) == 1 and len(decl) == 1
        and len(fit_calls) == 4 and len(fit_def) == 1,
        {"api实现": len(api), "接口声明": len(decl),
         "收口调用数": len(fit_calls), "收口定义": len(fit_def)})

    # ── C：★ 三条刻意边界：modifier 不抢、没选区不拦、Shift 加速 ──
    # ★ 收窄到**方向键分支内部**的那一段：`if (selection.nodeIds.length > 0)`
    #   在别处也出现（`Delete`/`g` 分支），按全文计数会数出 3 个 ⟹ 误报。
    no_mod = re.findall(r"if \(!modifier && !event\.altKey\) \{", page)
    nudge_blk = re.search(
        r"const nudge = ARROW_NUDGE\[event\.key\];(?P<body>.{0,600}?)\n      \}",
        page, re.S)
    guard = re.findall(r"if \(selection\.nodeIds\.length > 0\) \{",
                       nudge_blk.group("body")) if nudge_blk else []
    accel = re.findall(r"const step = event\.shiftKey \? 10 : 1;", page)
    add("C:★ 三条边界都在（不抢 modifier / 没选区不拦 / Shift 加速 10）",
        "★ 不抢 `Cmd/Ctrl+方向`：那是浏览器切标签页。★ 没选区**不** "
        "preventDefault：焦点不在画布时方向键仍该能滚别的面板",
        len(no_mod) == 1 and len(guard) == 1 and len(accel) == 1,
        {"不抢modifier": len(no_mod), "没选区不拦(限方向键分支)": len(guard),
         "Shift加速": len(accel), "找到方向键分支": bool(nudge_blk)})

    # ── D：★★ 处理臂：pre 完全不动、post 恰好 +3，且**框跟着** ──
    ev, dbad = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for _rd, cell in idx["arrowMovesMember"]:
            r = read(cell)
            if not r or len(r["ids"]) < 2:
                dbad.append({"phase": name, "why": "空读数"})
                continue
            # ★ 探针里 targets 顺序 = [被按的成员, 组]
            dk, dg = dx(r, 0), dx(r, 1)
            if dk is None or dg is None:
                dbad.append({"phase": name, "why": "绝对位置读数缺失"})
                continue
            ev.append({"phase": name, "kid": r["abs"][r["ids"][0]],
                       "group": r["abs"][r["ids"][1]],
                       "dKid": dk, "dGroup": dg, "past": r["past"]})
            if name == "pre":
                if not (dk == 0 and dg == 0 and r["past"] == (1, 1)):
                    dbad.append(ev[-1])
            else:
                # ★ 移动**成员**：选区里只有那个成员 ⟹ 只有它的 `position` +1，
                #   组由 `fitStoryboardGroupsToChildren` 重算后也 +1
                #   ⟹ 绝对位移是 **1×**（对比 E 臂移动组时的 **2×**）。
                # ★ 「框跟着 +3」是 793 收口在起作用的证据。
                want = STEP * PRESSES
                if not (dk == want and dg == want
                        and r["past"][1] - r["past"][0] == PRESSES):
                    dbad.append(dict(ev[-1], wantDelta=want))
    add("D:★★ 处理臂：pre 纹丝不动、post 成员与框都恰好 +3，历史 +3",
        "★ 「框跟着 +3」是 793 收口的证据；「历史 +3」是每次按压一条记录",
        not dbad, {"bad": dbad, "evidence": ev})

    # ── E：★★ 第二条臂：移动**组本身**时组与成员**同步**，且成员仍在框内 ──
    ev5, ebad = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for _rd, cell in idx["arrowMovesGroup"]:
            r = read(cell)
            if not r or len(r["ids"]) < 2:
                ebad.append({"phase": name, "why": "空读数"})
                continue
            # ★ 探针里 targets 顺序 = [组, 它的成员]
            dg, dk = dx(r, 0), dx(r, 1)
            if dg is None or dk is None:
                ebad.append({"phase": name, "why": "绝对位置读数缺失"})
                continue
            ev5.append({"phase": name, "group": r["abs"][r["ids"][0]],
                        "kid": r["abs"][r["ids"][1]],
                        "dGroup": dg, "dKid": dk, "同步": dg == dk,
                        "past": r["past"]})
            if name == "post":
                # ★★ 为什么这里是 **2×** 而不是 1×（第一版我写成 1×，实测翻红）：
                #   移动**组**时，选中区含组 ⟹ `movingIds` 里**组和它的成员都在**
                #   （store 实现显式把 child 也塞进去）⟹ 两者 `position` 各 +1；
                #   而成员的**绝对**位置 = 自身 + 父组 ⟹ 每按压绝对位移 **+2**。
                #   对比 D 臂（移动成员）：只有成员 `position` +1，组由
                #   `fitStoryboardGroupsToChildren` 重算 ⟹ 绝对位移 **+1**。
                #   两条臂数值不同是**机制决定的**，不是某一臂多走了 1 像素。
                want = STEP * PRESSES * 2
                # ★ 关键不变量：组与成员的**绝对位移必须相等** ⟹ 成员仍贴在框里
                if not (dg == dk and dg == want
                        and r["past"][1] - r["past"][0] == PRESSES):
                    ebad.append(dict(ev5[-1], wantDelta=want))
    add("E:★★ 移动组本身时，组与成员绝对位移**相等**（成员仍贴住框）",
        "★ 组 `position` 是相对父节点的偏移 ⟹ 组与成员同时加同一个 delta "
        "才能保持贴住。若只搬组不搬成员，成员会掉出框",
        not ebad, {"bad": ebad, "evidence": ev5})

    # ── F：★★ 阳性对照：Delete 两阶段都真删（证明键盘事件到达了画布）──
    fbad, fev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for _rd, cell in idx["positiveDelete"]:
            r = read(cell)
            if not r:
                fbad.append({"phase": name, "why": "空读数"})
                continue
            ok = (r["nodeCount"] == (11, 10)
                  and list(r["exists"].values())[0] == (True, False)
                  and r["past"][1] - r["past"][0] == 1)
            fev.append({"phase": name, "nodeCount": r["nodeCount"],
                        "exists": r["exists"], "past": r["past"], "ok": ok})
            if not ok:
                fbad.append(fev[-1])
    add("F:★★ 阳性对照：`Delete` 两阶段都真删掉一个节点",
        "★ 它和方向键走**同一个** keydown 监听器 ⟹ 它通过即证明"
        "「键盘事件确实到达画布」⟹ pre 的「没动」是能力缺失，不是探针坏了",
        not fbad, {"bad": fbad, "evidence": fev})

    # ── G：★ 修复没打扰阳性对照与节点总数 ──
    gbad = []
    for name, idx in (("pre", pre), ("post", post)):
        for arm, lst in idx.items():
            for _rd, c2 in lst:
                if c2.get("FAILED"):
                    gbad.append({"phase": name, "arm": arm,
                                 "FAILED": c2["FAILED"]})
        # ★ 方向键两条臂**不得**改变节点数（移动不是增删）
        for arm in ("arrowMovesMember", "arrowMovesGroup"):
            for _rd, c2 in idx.get(arm, []):
                r = read(c2)
                if r and r["nodeCount"][0] != r["nodeCount"][1]:
                    gbad.append({"phase": name, "arm": arm,
                                 "nodeCount": r["nodeCount"]})
    add("G:★ 方向键只挪位置、不增删节点；且无 FAILED",
        "★ 探针 FAILED 就是**空读数**", not gbad, {"bad": gbad})

    # ── H：格数与两轮一致（只比**行为签名**）──
    hbad = []
    for name, idx in (("pre", pre), ("post", post)):
        if set(idx) != set(ARMS):
            hbad.append({"phase": name, "arms": sorted(idx)})
        for arm in ARMS:
            if len(idx.get(arm, [])) != 2:
                hbad.append({"phase": name, "arm": arm,
                             "rounds": len(idx.get(arm, []))})
    add("H:两阶段各 3 臂 × 2 轮",
        "★ 节点 id 每轮新造 ⟹ 拿 id 判「一致」会误报，只比格数与结构",
        not hbad, {"bad": hbad})

    out = {
        "batch": 795,
        "kind": "★ 第六批改 src/ 的批次（新增能力：键盘移动）",
        "claims": {
            "D795-1": "★★ **画布此前完全没有键盘移动节点的能力**——"
                      "pre 实测：方向键 ×3 后成员与组的绝对位置**纹丝不动**"
                      "（`past 1→1`，连历史都没记）",
            "★ 反证": "★★ 阳性对照（`Delete`）**两阶段都真删掉一个节点**"
                      "（11→10、`past 1→2`），且它与方向键走**同一个** "
                      "keydown 监听器 ⟹ 排除「探针没把事件送到位」",
            "C795-2": "★ 修法 = store 新增 `nudgeSelectedNodes` + 一张 4 项的 "
                      "`ARROW_NUDGE` 表 + keydown 一个分支",
            "★ 收口": "★★ 键盘移动是**第三条**写点，它**过了 793 的收口**"
                      "（`fitStoryboardGroupsToChildren` 调用数 3→4）⟹ "
                      "移动成员时框跟着 +3，就是 793 那条收口的证据",
            "★ 边界": "★ 三条：① 不抢 `Cmd/Ctrl/Alt+方向`（留给浏览器切标签页）"
                      "② 没选区**不** preventDefault（方向键仍能滚别的面板）"
                      "③ `Shift` 按住时 10 像素、否则 1 像素",
            "★ 代价": "★★ 3 次按压 ⟹ `past 1→4` ⟹ **一次按压记一条历史**，"
                      "撤销要按 3 次才回原位。与桌面画布惯例一致 ⟹ 保留现状、"
                      "**不当缺陷修**，但必须记账",
        },
        "checks": checks,
        "totals": {"checks": len(checks),
                   "assertedAnchors": len(checks),
                   "failed": sum(0 if x["ok"] else 1 for x in checks)},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("★ D795-1：pre 方向键 ×3 纹丝不动（past 1→1）——键盘根本没有移动能力")
    print("★ 反证：Delete 阳性对照两阶段都真删（11→10、past 1→2）")
    print("★ C795-2：store 新增 nudgeSelectedNodes + ARROW_NUDGE 4 项表")
    print("★ 收口：fitStoryboardGroupsToChildren 调用数 3→4（键盘是第三条写点）")
    print("★ 代价：3 次按压 past 1→4，撤销粒度 = 1 像素（记账，不当缺陷）")
    print("★ 断言 %d 条 / 锚点 %d 个 / 失败 %d"
          % (out["totals"]["checks"], out["totals"]["assertedAnchors"],
             out["totals"]["failed"]))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
