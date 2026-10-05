#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 797 汇编器 —— 网格吸附**开着**时，拖组会把成员**拖下网格**

## 起点：796 顺带发现的那条

796 记下：拖后框的 `width` 是 `1173.3422818791946`，它会进 `node.style.width`
⟹ 用户可见的 DOM 尺寸带浮点尾数。796 判它**非缺陷**（无害），但同时指出：
「若将来要做尺寸吸附/对齐，这里需要先归一化」。

★ 本批去查「将来」是不是**已经**发生了 —— **已经**：

- 画布**已有**网格吸附：`page.tsx` 传 `snapToGrid` + `snapGrid={[20, 20]}`，
  状态在 `uiStore`（初值 `false`），UI 入口是底栏那个「网格吸附」按钮
- ★ 但组框是 **store 派生**的（793 的 `fitStoryboardGroupsToChildren` 直接写
  `position`/`width`），**不经过 react-flow 的拖拽管线**

## ★★ 核心机理：唯一来源是 `GROUP_PADDING = 32`（不是 20 的倍数）

派生量的定义：

- 组的位置 = `min(成员绝对) - PADDING`
- 成员的相对偏移 = `成员绝对 - 组位置`

⟹ 成员绝对**在网格**时，组位置与相对偏移**是否**在网格，只取决于 PADDING 是否是 20 的倍数。

实测（吸附开、两个成员都已落在网格上，pre）：

| 量 | 值 | 在网格 |
| --- | --- | --- |
| 成员绝对 | `(300,280)` `(260,-120)` | ✓ |
| 组位置 | `(228,-152)` | ✗ |
| 相对偏移 | `(72,432)` `(32,32)` | ✗ |
| **拖组后** 成员绝对 | `(632,272)` `(592,-128)` | ✗ |

★ 拖组时相对偏移**一个字节都没变**（`32,32` 拖前拖后一致），只有组位置从
`-152` 变成 `-160`（react-flow 只吸附**组**）⟹ 成员整体平移 `-8` ⟹ 掉出网格。

## 修法：`GROUP_PADDING` 32 → 40（= 2×20）

改一个常量。post 实测：组位置 `(220,-160)`、相对偏移全在网格、
拖组后成员 `(640,280)` —— **全程在网格**。

★ 改动前先**推演验证**过：padding=40 时组 pos / rel / 拖后成员绝对
**三组量全部在网格**，且仍满足 793 的贴合不变量。不是试出来的。

## ★★ 一条必须钉死的区分（否则结论会被误读）

`dragGroupSnapOn` 那条臂里，成员**拖之前就不在网格**（`(132,273)`）⟹
拖组只是把它们整体平移，post 里它们仍然不在网格 ⟹ **这不是缺陷**，
是前提不满足。★ 所以**只有** `groupDragAfterMembersSnapped`
（前提：先把成员摆到网格上）是有效判据。探针里给这条臂加了**前提守卫**：
摆平后若成员仍不在网格上，直接报 FAILED 而不是硬跑。
"""
import json
import pathlib
import re

REPO = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
B = "docs/research/liblib-canvas-batch797-2026-10-01"
PRE = REPO / (B + "/raw/vb797a-pre.json")
POST = REPO / (B + "/raw/vb797a-post.json")
OUT = REPO / (B + "/runtime-audit.json")
CS = "src/store/canvasStore.ts"
PAGE = "src/app/page.tsx"

ARMS = ["dragSnapOn", "dragSnapOff", "snapToggleOnly", "dragGroupSnapOn",
        "groupDragAfterMembersSnapped"]
GRID = 20


def index(raw):
    out = {}
    for rd in raw["rounds"]:
        for r in (rd.get("rows") or []):
            out.setdefault(r.get("arm"), []).append((rd.get("round"), r))
    return out


def on_grid(v):
    return not (v % GRID)


def all_on_grid(members):
    ms = [m for m in (members or []) if isinstance(m, dict)]
    return bool(ms) and all(on_grid(m["abs"]["x"]) and on_grid(m["abs"]["y"])
                            for m in ms)


def off_grid(members):
    return [m["id"][:8] for m in (members or [])
            if not (on_grid(m["abs"]["x"]) and on_grid(m["abs"]["y"]))]


def box(m):
    g = (m or {}).get("groupStore")
    if not g:
        return None
    return (g["pos"]["x"], g["pos"]["y"], g["w"], g["h"])


def read(cell, key="after"):
    b, a = cell.get("before"), cell.get(key)
    if not isinstance(b, dict) or not isinstance(a, dict):
        return None
    return {"box": (box(b), box(a)),
            "members": (b.get("members"), a.get("members")),
            "snap": a.get("snapToGrid")}


def main():
    pre_raw = json.loads(PRE.read_text(encoding="utf-8"))
    post_raw = json.loads(POST.read_text(encoding="utf-8"))
    pre, post = index(pre_raw), index(post_raw)
    checks = []

    def add(cid, desc, cond, detail):
        checks.append({"id": cid, "desc": desc, "ok": bool(cond),
                       "detail": detail})

    cs = (REPO / CS).read_text(encoding="utf-8")
    page = (REPO / PAGE).read_text(encoding="utf-8")

    # ── A：★★ 前提复核：吸附功能**真的存在**（不是「将来」的事）──
    snap_prop = re.findall(r"snapToGrid=\{snapToGrid\}", page)
    snap_grid = re.findall(r"snapGrid=\{\[20, 20\]\}", page)
    # ★ 「网格吸附」这个 UI 入口在 `BottomToolbar.tsx`，不在 `page.tsx`
    toolbar = (REPO / "src/components/BottomToolbar.tsx").read_text(
        encoding="utf-8")
    snap_ui = re.findall(r'label="网格吸附"', toolbar)
    add("A:★★ 网格吸附**已经存在**（`snapToGrid` + `snapGrid=[20,20]` + UI 入口）",
        "★ 796 说「若将来要做吸附对齐」—— 本批先证明**它已经在了**，"
        "否则整个批次的立论就塌了",
        len(snap_prop) == 1 and len(snap_grid) == 1 and len(snap_ui) >= 1,
        {"snapToGrid 传参": len(snap_prop), "snapGrid": len(snap_grid),
         "UI 入口": len(snap_ui)})

    # ── B：★★ 核心臂：成员先在网格上 → 拖组后**仍在**网格上 ──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for _rd, c in idx["groupDragAfterMembersSnapped"]:
            r = read(c)
            if not r:
                bad.append({"phase": name, "why": "空读数"})
                continue
            b_ok, a_ok = all_on_grid(r["members"][0]), all_on_grid(r["members"][1])
            rel_same = [tuple(m["pos"].values()) for m in r["members"][1]] == \
                [tuple(m["pos"].values()) for m in r["members"][0]]
            ev.append({"phase": name,
                       "拖前成员在网格": b_ok, "拖后在网格": a_ok,
                       "相对偏移未变": rel_same,
                       "拖前离网格": off_grid(r["members"][0]),
                       "拖后离网格": off_grid(r["members"][1]),
                       "组": (r["box"][0][:2], r["box"][1][:2])})
            # ★ 前置条件：拖之前成员**必须**已经在网格上，否则这条臂无效
            if not b_ok:
                bad.append(dict(ev[-1], why="前提不成立：拖前成员就不在网格上"))
            elif (name == "pre") == a_ok:
                # pre 应当**掉出**网格，post 应当**留在**网格上
                bad.append(dict(ev[-1], why="pre/post 的网格状态与预期相反"))
    add("B:★★ 核心臂：成员先在网格上，拖组后 pre **掉出**、post **仍在**",
        "★ 判据是「拖前就在网格上」这个**前提** + 拖后的网格状态。"
        "★ 相对偏移在两个阶段都必须**未变** ⟹ 证明位移全部来自组的位置变化",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev})

    # ── C：★★ 机理自证：相对偏移 pre/post 相同，且 pre 的**不在**网格上 ──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for _rd, c in idx["groupDragAfterMembersSnapped"]:
            r = read(c)
            if not r:
                continue
            rel0 = sorted(tuple(sorted(m["pos"].items()))
                          for m in r["members"][0])
            rel1 = sorted(tuple(sorted(m["pos"].items()))
                          for m in r["members"][1])
            # ★ 相对偏移在两个阶段都必须**未变** ⟹ 证明位移全部来自组的位置变化
            on0 = all(on_grid(m["pos"]["x"]) and on_grid(m["pos"]["y"])
                      for m in r["members"][0])
            on1 = all(on_grid(m["pos"]["x"]) and on_grid(m["pos"]["y"])
                      for m in r["members"][1])
            ev.append({"phase": name, "rel前": rel0, "rel后": rel1,
                       "未变": rel0 == rel1, "rel在网格": (on0, on1)})
            if rel0 != rel1:
                bad.append(dict(ev[-1], why="相对偏移变了，机理不成立"))
            if (name == "pre") != (not on0):
                bad.append(dict(ev[-1],
                                why="pre 的相对偏移应**不**在网格上"))
            if (name == "post") != on1:
                bad.append(dict(ev[-1],
                                why="post 的相对偏移应**在**网格上"))
    add("C:★★ 机理自证：相对偏移未变，且 pre 不在网格 / post 在网格",
        "★ 「相对偏移 = 成员绝对 − 组位置」⟹ 相对偏移在网格上、组位置也在网格上 "
        "⟹ 成员绝对必然在网格上。★ 这条把「唯一来源是 PADDING」钉死",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev})

    # ── D：★ 组的**位置**：拖**前**是派生值（分阶段），拖**后**由 react-flow 吸附 ──
    #   ★ 第一版我错在「pre 拖后不该在网格上」——实际 dragSnapOn 那类臂里
    #   组的拖后位置**由 react-flow 吸附**，两个阶段都该在网格上。
    #   分阶段的只有**拖前**那个派生值。
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for _rd, c in idx["groupDragAfterMembersSnapped"]:
            r = read(c)
            if not r:
                continue
            b = all(on_grid(v) for v in r["box"][0][:2])
            a = all(on_grid(v) for v in r["box"][1][:2])
            ev.append({"phase": name, "组拖前在网格": b, "组拖后在网格": a,
                       "pos": (r["box"][0][:2], r["box"][1][:2])})
            # ★ 拖后：两个阶段都必须在网格（react-flow 吸附的就是组）
            if not a:
                bad.append(dict(ev[-1], why="拖组后组位置不在网格上"))
            # ★ 拖前（派生值 = min − PADDING）：pre 不在、post 在
            if (name == "pre") != (not b):
                bad.append(dict(ev[-1], why="拖前组位置的网格状态与预期相反"))
    add("D:★ 组的**位置**：拖前 pre 不在网格/post 在；拖后两阶段都在",
        "★ 拖**前**是派生值 `min(成员) − PADDING` ⟹ 在不在网格**只取决于 "
        "PADDING**。★ 拖**后**是 react-flow 吸附的结果 ⟹ 两阶段都该在网格上",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev})

    # ── E：★★ 阳性对照：吸附**关**时成员不吸附（证明吸附真的在工作）──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for _rd, c in idx["dragSnapOff"]:
            r = read(c)
            if not r:
                bad.append({"phase": name, "why": "空读数"})
                continue
            # ★ 吸附关 ⟹ snapToGrid 读数必须是 false
            if r["snap"] is not False:
                bad.append({"phase": name, "why": "吸附读数不是 False",
                            "snap": r["snap"]})
                continue
            # ★ 而且成员**不该**在网格上（若是，就无法区分「吸附关了」与「本来就在」）
            on = all_on_grid(r["members"][1])
            ev.append({"phase": name, "snap": r["snap"], "成员在网格": on,
                       "离网格": off_grid(r["members"][1])})
            if on:
                bad.append(dict(ev[-1], why="吸附关却仍在网格，对照失效"))
    add("E:★★ 阳性对照：吸附**关**时 `snapToGrid=False` 且成员**不**在网格",
        "★ 没有它，「成员在网格上」可能只是「本来就在」，"
        "⟹ B 的 post 结论就没有意义",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev})

    # ── F：★ 前置对照：只切开关**不改几何**；且吸附读数随开关变化 ──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for _rd, c in idx["snapToggleOnly"]:
            r = read(c)
            if not r:
                bad.append({"phase": name, "why": "空读数"})
                continue
            same = r["box"][0] == r["box"][1] and \
                [m["abs"] for m in r["members"][0]] == \
                [m["abs"] for m in r["members"][1]]
            ev.append({"phase": name, "snap": r["snap"], "几何未变": same})
            if not same or r["snap"] is not True:
                bad.append(dict(ev[-1], why="切开关本身改了几何"))
    add("F:★ 前置对照：只切吸附开关**不改变任何几何**",
        "★ 若切开关就动几何，那 B 臂的「变化」可能来自开关而不是拖动",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev})

    # ── G：★ 区分无效臂：`dragGroupSnapOn` 的成员**拖前就不在网格** ──
    #   这条不是缺陷，是**前提不满足** ⟹ 必须显式记下来，否则会被误读成「没修好」
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for _rd, c in idx["dragGroupSnapOn"]:
            r = read(c)
            if not r:
                continue
            b_on = all_on_grid(r["members"][0])
            ev.append({"phase": name, "拖前成员在网格": b_on,
                       "拖后在网格": all_on_grid(r["members"][1]),
                       "判定": "★ 前提不满足 ⟹ 本臂**不构成**缺陷证据"})
            if b_on:
                bad.append(dict(ev[-1],
                                why="成员拖前已在网格 ⟹ 本臂应当也能判缺陷"))
    add("G:★★ 显式作废 `dragGroupSnapOn` 那条臂（前提不满足）",
        "★ 它拖之前成员就不在网格（`(132,273)`）⟹ 拖组只是整体平移，"
        "「结果不在网格」**不能**算缺陷。★ 必须显式作废，否则会被误读成「没修好」",
        not bad and len(ev) == 4 and all(not x["拖前成员在网格"]
                                         for x in ev),
        {"bad": bad, "evidence": ev})

    # ── H：★ 源码侧前提（从源码重读，不凭记忆）──
    pad = re.findall(r"const GROUP_PADDING = (\d+);", cs)
    pad_v = int(pad[0]) if pad else None
    add("H:★★ `GROUP_PADDING` 是网格（20）的整数倍",
        "★ 这是本批**唯一**的改动点 ⟹ 判据是「20 的倍数」，不是「40」"
        "（写死 40 的话，将来有人改成 60 也会被放过）",
        pad_v is not None and pad_v % GRID == 0,
        {"GROUP_PADDING": pad_v, "网格": GRID, "是倍数":
         pad_v is not None and pad_v % GRID == 0})

    # ── I：格数与无 FAILED ──
    bad = []
    for name, idx in (("pre", pre), ("post", post)):
        if set(idx) != set(ARMS):
            bad.append({"phase": name, "arms": sorted(idx)})
        for arm, lst in idx.items():
            if len(lst) != 2:
                bad.append({"phase": name, "arm": arm, "rounds": len(lst)})
            for _rd, c in lst:
                if c.get("FAILED"):
                    bad.append({"phase": name, "arm": arm,
                                "FAILED": c.get("FAILED")})
    add("I:两阶段各 5 臂 × 2 轮且无 FAILED",
        "★ 探针 FAILED 就是**空读数**", not bad, {"bad": bad})

    out = {
        "batch": 797,
        "kind": "★ 第七批改 src/ 的批次（常量改动：GROUP_PADDING 32→40）",
        "claims": {
            "D797-1": "★★ 画布**早已有**网格吸附（`snapToGrid` + `snapGrid=[20,20]` "
                      "+ 底栏「网格吸附」按钮）⟹ 796 说的「将来」**已经是现在**",
            "★★ 缺陷": "★★ 吸附开着时**拖组**，会把**原本整齐**的成员"
                        "**拖下网格**：pre 实测 `(300,280)` → `(632,272)`，"
                        "272 不是 20 的倍数",
            "★★ 机理": "★★ 唯一来源是 `GROUP_PADDING = 32`（**不是 20 的倍数**）"
                        "⟹ 组位置 `min−32` 与相对偏移 `绝对−组位置` 全部派生为"
                        "非网格数。★ 拖组时相对偏移**一个字节都没变**，"
                        "只有组被 react-flow 吸附 ⟹ 成员整体平移吸附余数",
            "C797-2": "★ 修法 = `GROUP_PADDING` **32 → 40**（= 2×20），"
                      "只改一个常量。★ 改动前**先推演验证**过："
                      "padding=40 时组 pos / rel / 拖后成员绝对三组量全在网格",
            "★ 限定": "★★ `dragGroupSnapOn` 那条臂**显式作废**："
                      "它拖之前成员就不在网格（`(132,273)`）⟹ "
                      "「结果不在网格」不构成缺陷证据。★ 只有"
                      "`groupDragAfterMembersSnapped`（先摆平成员）是有效判据",
            "★ 代价": "★ 吸附**关**时 padding 只是视觉留白，从 32 变 40 会让框"
                      "**宽 8 像素**。40 仍是整齐偶数、更贴近 8pt 栅格 ⟹ "
                      "这是**取舍**不是零成本",
        },
        "checks": checks,
        "totals": {"checks": len(checks), "assertedAnchors": len(checks),
                   "failed": sum(0 if x["ok"] else 1 for x in checks)},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("★ D797-1：画布早已有网格吸附（snapToGrid + snapGrid=[20,20] + 底栏按钮）")
    print("★★ 缺陷：pre 拖组后成员 (300,280)→(632,272)，272 掉出网格")
    print("★★ 机理：唯一来源是 GROUP_PADDING=32 不是 20 的倍数")
    print("★ C797-2：32→40（2×20），只改一个常量；改动前已推演验证")
    print("★ 限定：dragGroupSnapOn 前提不满足，已显式作废")
    print("★ 代价：吸附关时框宽 8 像素（取舍，非零成本）")
    print("★ 断言 %d 条 / 锚点 %d 个 / 失败 %d"
          % (out["totals"]["checks"], out["totals"]["assertedAnchors"],
             out["totals"]["failed"]))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
