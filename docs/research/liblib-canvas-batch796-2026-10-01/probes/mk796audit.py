#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 796 汇编器 —— 组的几何变化是否被正确纳入**撤销**

## 起点：793 遗留里的**最后一条**

793 列了三条未验路径：拖拽跟随（= 793 本体）、删成员收拢（= 794）、
键盘移动（= 795）。剩下这条是「组的几何变化是否被 `onNodeDragStop` 正确纳入撤销」。

## ★ 读源码看着是对的，但有两处读不出来

`onNodeDragStart` 拍 `snapshot: { nodes: currentCanvas.nodes, … }`（拖动**开始前**），
`onNodeDragStop` 里 `moved` 为真时
`setStoreNodes(currentNodes, { recordHistory: true, historySnapshot: transaction.snapshot })`
（提交**跟随后**的节点、存**拖动前**的快照）⟹ 撤销理应回到拖动前的样子。

★ 但有两件只能实测：

1. `snapshot.nodes` 是**引用**不是深拷贝。若后续写入**原地改**这个数组，
   快照就被污染 ⟹ 撤销回到一个「已被改过」的世界。
2. `moved` 的判据只看**被拖的 id**（或选区里的 id）的 `position`，
   **不看框**。框是 793 收口改的 ⟹ 有没有可能出现「框变了但 `moved` 为假、
   历史里什么都没有」？

## ★ 结论：**没有缺陷，无需改 `src/`**

| 臂 | pre | post |
| --- | --- | --- |
| ★ 撤销臂 | 组 `(76,-157) 706×812` → 拖后 `(100,-157) 1173.34×812` → 撤销后**`(76,-157) 706×812`**、`past 1→2→1` | **与 pre 逐格一致** |
| ★ 快照污染臂 | 快照里的组是 `(76,-157) 706×812`（**拖动前**的值，**未被污染**） | 同左 |
| ★ 空拖臂 | 零位移拖拽 ⟹ `past 1→1`（**不记历史**） | 同左 |
| ★ 阳性对照 | 造组后立刻 `Cmd+Z` ⟹ 组消失、`past 1→0` | 同左 |

★ 因为**本批没改 `src/`**，pre 与 post **必须**逐格相同；它们相同，
恰好证明「读数可复现、不是探针状态依赖」。

## ★★ 一个必须解释的脏值：框宽 `1173.3422818791946`

★ 成员的绝对 x 是 `891.3422818791946`，右边界 = `891.34 + 350 = 1241.34`；
左边界是另一个成员的 `132`；`1241.34 - 132 + 64 = 1173.34` —— **算术完全自洽**。

⟹ 脏值来自**拖拽落点本身落在亚像素上**（Playwright 的 `mouse.move` + react-flow
原样记录），框只是**忠实跟随**。★ 这**不是缺陷**，是浏览器/拖拽的固有行为。

★ 793 的 `EPS = 0.01` 容差正是为这类浮点噪声设的，而本批证明**它稳**：
两阶段、两轮的脏值**逐位相同**（`1173.3422818791946`），⟹ 落点是**确定性**的，
不是随机噪声 ⟹ 「已贴合就 no-op」的判定不会因噪声而时灵时不灵。

★ **教训**：探针第一版用 `Math.round` 取整，恰好把这个脏值**掩盖**成 `891`，
于是它在读数里看不出来是怎么来的。去掉取整后一眼看出真相。★ 探针**取整会隐藏问题**。
"""
import json
import pathlib
import re

REPO = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
B = "docs/research/liblib-canvas-batch796-2026-10-01"
PRE = REPO / (B + "/raw/vb796a-pre.json")
POST = REPO / (B + "/raw/vb796a-post.json")
OUT = REPO / (B + "/runtime-audit.json")

ARMS = ["dragThenUndo", "snapshotPurity", "noopDrag", "positiveUndo"]
EPS = 0.01
PADDING = 32


def index(raw):
    out = {}
    for rd in raw["rounds"]:
        for r in (rd.get("rows") or []):
            out.setdefault(r.get("arm"), []).append((rd.get("round"), r))
    return out


def box(m):
    g = (m or {}).get("groupStore")
    if not g:
        return None
    return (g["pos"]["x"], g["pos"]["y"], g["w"], g["h"])


def near(a, b):
    return abs(a - b) <= EPS


def box_near(a, b):
    return a is not None and b is not None and all(
        near(x, y) for x, y in zip(a, b))


def read(cell, key="after"):
    b = cell.get("before")
    a = cell.get(key)
    if not isinstance(b, dict) or not isinstance(a, dict):
        return None
    return {"before": b, "after": a,
            "box": (box(b), box(a)),
            "past": (b.get("past"), a.get("past"))}


def members_box(m):
    """★ 从 raw 的成员读数**独立重算**外接框 + padding（不读源码公式）。"""
    ms = [x for x in (m or {}).get("members", []) if isinstance(x, dict)]
    if not ms:
        return None
    x0 = min(x["abs"]["x"] for x in ms)
    y0 = min(x["abs"]["y"] for x in ms)
    x1 = max(x["abs"]["x"] + (x.get("w") or 0) for x in ms)
    y1 = max(x["abs"]["y"] + (x.get("h") or 0) for x in ms)
    return (x0 - PADDING, y0 - PADDING, x1 - x0 + PADDING * 2,
            y1 - y0 + PADDING * 2)


def main():
    pre_raw = json.loads(PRE.read_text(encoding="utf-8"))
    post_raw = json.loads(POST.read_text(encoding="utf-8"))
    pre, post = index(pre_raw), index(post_raw)
    checks = []

    def add(cid, desc, cond, detail):
        checks.append({"id": cid, "desc": desc, "ok": bool(cond),
                       "detail": detail})

    # ── A：★ 本批没改 `src/` ⟹ pre 与 post 必须**逐格相同** ──
    # ★ 这不是形式：它同时证明「读数可复现」与「探针不依赖运行状态」。
    def sig_of(idx):
        out = {}
        for arm, lst in idx.items():
            out[arm] = []
            for _rd, c in lst:
                s = read(c, "afterDrag") if arm == "dragThenUndo" else read(c)
                if not s:
                    out[arm].append(None)
                    continue
                out[arm].append({
                    "box": s["box"][1], "past": s["past"],
                    "undoBox": (box(c.get("after")) or [None])[0]
                    if arm == "dragThenUndo" else None,
                })
        return out

    sp, sq = sig_of(pre), sig_of(post)
    diff = [arm for arm in ARMS if sp.get(arm) != sq.get(arm)]
    add("A:★★ 没改 `src/` ⟹ pre 与 post **逐格相同**",
        "★ 它同时证明「读数可复现」与「探针不依赖运行状态」；"
        "★ 含亚像素脏值也必须逐位相同",
        not diff, {"不同的臂": diff, "pre": sp, "post": sq})

    # ── B：★★ 撤销臂：成员与**框**都复原，且 past 退一格 ──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for _rd, c in idx["dragThenUndo"]:
            b = read(c, "before")
            mid = read(c, "afterDrag")
            a = read(c, "after")
            if not (b and mid and a):
                bad.append({"phase": name, "why": "空读数"})
                continue
            # ★ 撤销臂的判据：撤销后 == 拖动**前**（容差比，防浮点）
            ok = (box_near(a["box"][1], b["box"][0])
                  and mid["past"][1] == mid["past"][0] + 1
                  and a["past"][1] == mid["past"][1] - 1)
            ev.append({"phase": name, "before": b["box"][0],
                       "afterDrag": mid["box"][1], "afterUndo": a["box"][1],
                       "past": (b["past"][0], mid["past"][1], a["past"][1]),
                       "复原": box_near(a["box"][1], b["box"][0])})
            if not ok:
                bad.append(ev[-1])
    add("B:★★ 撤销臂：组**与框**都复原到拖动前，且 `past` 退一格",
        "★ 793 遗留问的是「组的几何变化是否被纳入撤销」⟹ 判据是**撤销后回到拖动前**"
        "，且历史深度真的退一格（不是「有东西被恢复」就算）",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev})

    # ── C：★★ 快照**未被污染**：`past` 末条里的组仍是拖动前的几何 ──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for _rd, c in idx["snapshotPurity"]:
            b, a = c.get("before"), c.get("after")
            if not isinstance(b, dict) or not isinstance(a, dict):
                bad.append({"phase": name, "why": "空读数"})
                continue
            snap = a.get("snapGroup")
            live = a.get("groupStore")
            if not snap or not live:
                bad.append({"phase": name, "why": "快照或现值缺失"})
                continue
            s = (snap["pos"]["x"], snap["pos"]["y"], snap["w"], snap["h"])
            l = (live["pos"]["x"], live["pos"]["y"], live["w"], live["h"])
            bg = b["groupStore"]
            dragged = (bg["pos"]["x"], bg["pos"]["y"], bg["w"], bg["h"])
            # ★ 关键：快照里的组必须是**拖动前**的值，且与**现值不同**
            #   （相同就说明快照被现值覆盖了，那才是污染）
            # ★ 不写死 `(706, 812)`：那是从读数看来的，判据必须从 raw 的
            #   `before.groupStore` 现取，否则种子一变就假绿。
            ok = box_near(s, dragged) and not box_near(s, l)
            ev.append({"phase": name, "快照里的组": s, "现值的组": l,
                       "拖动前的组": dragged,
                       "等于拖动前": box_near(s, dragged),
                       "与现值不同": not box_near(s, l)})
            if not ok:
                bad.append(ev[-1])
    add("C:★★ 快照**未被污染**：`past` 末条里的组仍是拖动前的几何",
        "★ `snapshot.nodes` 是**引用**不是深拷贝 ⟹ 若写入原地改它，"
        "撤销就会回到「已被改过」的世界。★ 判据是「快照 == 拖动前」"
        "**且**「快照 ≠ 现值」（相同反而说明被覆盖了）",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev})

    # ── D：★ 空拖臂：零位移**不记历史**（`moved` 判据真的看了位置）──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for _rd, c in idx["noopDrag"]:
            r = read(c)
            if not r:
                bad.append({"phase": name, "why": "空读数"})
                continue
            ok = (r["past"][0] == r["past"][1]
                  and box_near(r["box"][0], r["box"][1]))
            ev.append({"phase": name, "box": r["box"], "past": r["past"],
                       "ok": ok})
            if not ok:
                bad.append(ev[-1])
    add("D:★ 空拖臂：零位移拖拽**不记历史**、几何不变",
        "★ `moved` 的判据是「被拖 id 的 position 变了」⟹ 零位移必须不记历史。"
        "★ 若它无条件记历史，撤销栈会被无意义的空操作填满",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev})

    # ── E：★★ 阳性对照：`Cmd+Z` 真的接上了画布 ──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for _rd, c in idx["positiveUndo"]:
            b, a = c.get("before"), c.get("after")
            if not isinstance(b, dict) or not isinstance(a, dict):
                bad.append({"phase": name, "why": "空读数"})
                continue
            ok = (box(b) is not None and box(a) is None
                  and a.get("past") == b.get("past") - 1)
            ev.append({"phase": name, "before": box(b), "after": box(a),
                       "past": (b.get("past"), a.get("past")), "ok": ok})
            if not ok:
                bad.append(ev[-1])
    add("E:★★ 阳性对照：`Cmd+Z` 真的接上了画布（造组后撤销 ⟹ 组消失）",
        "★ 没有它，撤销臂的「复原」可以是「撤销键根本没反应、什么都没变」"
        "——那种情况 `box` 也恰好等于拖动前 ⟹ 假绿",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev})

    # ── F：★★ 拖后框 = 独立重算的贴合值（顺带证 793 的收口仍在生效）──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for _rd, c in idx["snapshotPurity"]:
            a = c.get("after")
            if not isinstance(a, dict):
                bad.append({"phase": name, "why": "空读数"})
                continue
            want = members_box(a)
            got = box(a)
            ok = box_near(got, want)
            ev.append({"phase": name, "拖后框": got, "独立重算": want,
                       "相等": ok})
            if not ok:
                bad.append(ev[-1])
    add("F:★★ 拖后框**精确等于**按 padding 独立重算的贴合值",
        "★ 用 raw 的成员读数重算，**不依赖**源码公式 ⟹ 公式写错也会被抓出来。"
        "★ 这是 793 收口仍生效的旁证（本批没改它）",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev})

    # ── G：★ 脏值可复现（两阶段逐位相同）──
    dirty = []
    for name, idx in (("pre", pre), ("post", post)):
        for _rd, c in idx["snapshotPurity"]:
            w = (c.get("after") or {}).get("groupStore", {}).get("w")
            if isinstance(w, float) and abs(w - round(w)) > 1e-6:
                dirty.append((name, w))
    uniq = sorted({w for _n, w in dirty})
    add("G:★ 亚像素脏值**两阶段逐位相同**（⟹ 落点确定、EPS 判定稳）",
        "★ 脏值来自拖拽落点的亚像素，不是缺陷（框只是忠实跟随）。"
        "★ 但它**逐位可复现** ⟹ 793 的 `EPS=0.01` no-op 判定不会时灵时不灵。"
        "★ 第一版探针用 `Math.round` 把它掩盖成整数，来源一度看不出来",
        len(uniq) == 1 and len(dirty) == 4,
        {"脏值": uniq, "出现次数": len(dirty),
         "判为缺陷": False, "理由": "算术自洽：891.34+350-132+64=1173.34"})

    # ── H：格数与无 FAILED ──
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
    add("H:两阶段各 4 臂 × 2 轮且无 FAILED",
        "★ 探针 FAILED 就是**空读数**", not bad, {"bad": bad})

    # ── I：★ 源码侧的**前提**复核（从源码读出，不是凭记忆）──
    cs = (REPO / "src/store/canvasStore.ts").read_text(encoding="utf-8")
    page = (REPO / "src/app/page.tsx").read_text(encoding="utf-8")
    snap_ref = re.findall(r"snapshot: \{ nodes: currentCanvas\.nodes,", page)
    hist_arg = re.findall(r"historySnapshot: transaction\.snapshot", page)
    moved = re.findall(r"before\.position\.x !== after\.position\.x", page)
    eps = re.findall(r"const EPS = 0\.01;", cs)
    add("I:★ 源码侧前提复核：快照取自**拖动前**、提交时带上它、`moved` 判位置、`EPS` 在",
        "★ 这些是本批结论的机制依据 ⟹ 必须**从源码重新读出**，"
        "不能凭上一批的记忆（改过 `src/` 后行号会位移）",
        len(snap_ref) == 1 and len(hist_arg) == 1
        and len(moved) == 1 and len(eps) == 1,
        {"快照取自拖动前": len(snap_ref), "提交时带上快照": len(hist_arg),
         "moved判位置": len(moved), "EPS": len(eps)})

    out = {
        "batch": 796,
        "kind": "★ 纯测量批次（**没改 `src/`**）：结论是「撤销本来就正确」",
        "claims": {
            "R796-1": "★★ 组的几何变化**本来就**被正确纳入撤销——"
                      "撤销后组与框都回到 `(76,-157) 706x812`、`past 2→1`。"
                      "★ 793 遗留的最后一条，答案是「不用改」",
            "★ 快照": "★★ `snapshot.nodes` 虽然是**引用**，但实测**未被污染**："
                      "`past` 末条里的组仍是拖动前的几何，**且 ≠ 现值**",
            "★ 空拖": "★ 零位移拖拽**不记历史**（`past 1→1`）⟹ "
                      "`moved` 判据真的看了位置，无意义的空操作不会填满撤销栈",
            "★ 阳性对照": "★★ 造组后立刻 `Cmd+Z` ⟹ 组消失、`past 1→0` ⟹ "
                          "证明撤销键接上了画布（否则撤销臂的「复原」可以假绿）",
            "★★ 脏值": "★ 框宽 `1173.3422818791946` **不是缺陷**："
                        "成员绝对 x = `891.3422818791946`，右边界 `1241.34`，"
                        "减 `132` 加 `64` ⟹ `1173.34`，**算术完全自洽**。"
                        "脏值来自**拖拽落点的亚像素**，框只是忠实跟随",
            "★ 可复现": "★★ 脏值在两阶段两轮**逐位相同** ⟹ 落点是**确定性**的 "
                        "⟹ 793 的 `EPS=0.01` no-op 判定稳定，不会时灵时不灵",
            "★ 教训": "★ 探针第一版用 `Math.round` 取整，恰好把这个脏值"
                      "**掩盖**成 `891` ⟹ 「探针取整会隐藏问题」",
        },
        "checks": checks,
        "totals": {"checks": len(checks), "assertedAnchors": len(checks),
                   "failed": sum(0 if x["ok"] else 1 for x in checks)},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("★ R796-1：撤销臂 pre/post 都把组与框复原到 (76,-157) 706x812、past 2→1")
    print("★ 快照未被污染：past 末条里的组仍是拖动前几何，且 ≠ 现值")
    print("★ 空拖不记历史：past 1→1")
    print("★ 阳性对照：造组后 Cmd+Z 组消失、past 1→0")
    print("★★ 脏值 %r 两阶段逐位相同 ⟹ 拖拽落点确定，非缺陷" % (uniq,))
    print("★ 结论：793 遗留最后一条 = 「本来就正确，无需改 src/」")
    print("★ 断言 %d 条 / 锚点 %d 个 / 失败 %d"
          % (out["totals"]["checks"], out["totals"]["assertedAnchors"],
             out["totals"]["failed"]))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
