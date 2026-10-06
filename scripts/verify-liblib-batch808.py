#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 808 验收器 —— 独立实现，不 import 探针

## 本批的读数

793 留的待拍板 ②（空组要不要收缩/弱化、0 成员组的连线 handle 要不要一起去掉）
第一次拿到**实测读数**。807 只覆盖了「成员被搬进另一个组」那一条变空路径；
本批覆盖另一条更常见的：**直接删成员**。

## ★ 本批最要紧的一条纪律：**作废的臂必须显式作废**

右键菜单那条臂探针**没打开菜单**（`menuItems` 为空）⟹ 它**没有测到任何东西**。
按 802 起的规矩「前提不满足的臂**显式作废**」，本批把它做成断言 **S7**：
一旦有人拿一个空 `menuItems` 去论证「菜单里没有删除项」，S7 就会红。

★ 而它**本来就很诱人**：源码里确实有 `data-canvas-context-item="删除"`
（`CanvasContextMenu.tsx:191`），空读数很容易被写成「右键菜单里没有删除」。

## 另一条：一个差点被我误读的读数

空组在 store 里是 `698×430`，而 DOM 的 `getBoundingClientRect()` 是
`367×226` ⟹ 比值 `0.526` / `0.526` **完全一致**。★ 那是 **zoom 缩放**，不是框塌了。
S4 因此额外要求「两个方向的比值是同一个数」—— 若框真的塌了，两个比值会分叉。
"""
import copy
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
D = ROOT / "docs/research/liblib-canvas-batch808-2026-10-01"
RAW = D / "raw/vb808a.json"
REPORT = D / "verify-report.json"
CS = "src/store/canvasStore.ts"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_checks(raw, src):
    checks = []

    def add(cid, why, ok, ev):
        checks.append({"id": cid, "why": why, "ok": bool(ok), "evidence": ev})

    rs = raw.get("rounds", [])

    # ── S1 ★★ 删带成员的组：成员被连坐，但**能完全撤销**
    ev = []
    for r in rs:
        a = r.get("deleteGroupWithMembers") or {}
        if a.get("FAILED") or "节点数 Δ" not in a:
            continue
        kids = a.get("它原来的成员") or []
        u = a.get("undo") or {}
        ev.append({"round": r["round"], "组": a.get("删掉的组"),
                   "成员": kids, "节点数 Δ": a.get("节点数 Δ"),
                   "成员还在吗": a.get("成员还在吗"),
                   "undo": u,
                   "★ 连坐": bool(kids) and all(v is False
                                                for v in (a.get("成员还在吗") or {}).values()),
                   "★ Δ 正好是 -(1+成员数)":
                       a.get("节点数 Δ") == -(1 + len(kids)),
                   "★ 撤销后全回来了": bool(u.get("★ 成员全回来了"))
                                       and bool(u.get("组回来了")),
                   "★ 三件同时": bool(kids)
                       and all(v is False for v in (a.get("成员还在吗") or {}).values())
                       and a.get("节点数 Δ") == -(1 + len(kids))
                       and bool(u.get("★ 成员全回来了")) and bool(u.get("组回来了"))})
    add("S1:★★ 删掉一个**带成员的组**：成员**被连坐删除**，但 `Cmd+Z` **能完全撤销**",
        "★★ 这是「级联删除」这个高风险行为的完整刻画：连坐**确实发生**、"
        "Δ **正好是 -(1+成员数)**（不多不少）、而且**能撤销回来**；"
        "★ 键盘删除路径（`page.tsx:1376`）**没有任何确认框**——对比「删画布」**有**确认框，"
        "所以「组会带走它的成员」这件事**用户事前得不到任何告知**",
        ev and all(x["★ 三件同时"] for x in ev), ev)

    # ── S2 ★★ 阳性对照：删掉一个成员时，组**收缩贴合**剩下的
    ev = [{"round": r["round"], "删掉的成员": s.get("删掉的成员"),
           "组还剩几个": s.get("组还剩几个"),
           "框（删之前）": s.get("原来的框"), "框（删之后）": s.get("组框"),
           "★ 真的删掉了": s.get("★ 删一个成员真的生效了"),
           "★ 框收缩贴合了": s.get("★ 框变了（贴合剩下的）")}
          for r in rs for s in [r.get("deleteLastMember_step1") or {}]
          if s.get("★ 删一个成员真的生效了") is not None]
    add("S2:★★ 阳性对照：组还剩成员时，删掉一个成员会让框**收缩贴合剩下的**",
        "★★ 没有这条，「空组框不变」可能只是「框从来就不变」⟹ ★ 而它同时证明"
        "**fit 对非空组是活的**（源码 `kids.length === 0 → continue` 只跳过空组）",
        ev and all(x["★ 真的删掉了"] and x["★ 框收缩贴合了"] for x in ev), ev)

    # ── S3 ★★★ 空组还在，且**框沿用上一个状态**（不收缩到 0）
    ev = []
    for r in rs:
        b = r.get("deleteLastMember") or {}
        if "空组还在吗" not in b:
            continue
        ev.append({"round": r["round"], "空组还在吗": b.get("空组还在吗"),
                   "框（还有 1 个成员时）": b.get("一步之前的框"),
                   "框（空组）": b.get("空组框"),
                   "★ 还活着": b.get("空组还在吗") is True,
                   "★ 框一个像素都没变": b.get("★ 框没变（沿用还剩一个时的）"),
                   "★ 且框非零": bool(b.get("空组框")) and all(v > 0 for v in b["空组框"]),
                   "★ 三件同时": b.get("空组还在吗") is True
                       and b.get("★ 框没变（沿用还剩一个时的）")
                       and bool(b.get("空组框")) and all(v > 0 for v in b["空组框"])})
    add("S3:★★★ 空组**还在**，框**一个像素都没变**、也没塌成 0",
        "★★★ 源码侧对应 `fitStoryboardGroupsToChildren` 的"
        "「★ 边界 1：`if (kids.length === 0) continue;` 空组不动」；"
        "★ 这是 793 待拍板 ②（空组要不要收缩/弱化）的实测读数 —— "
        "现状是**完全不动**，本批只报事实、不判对错",
        ev and all(x["★ 三件同时"] for x in ev), ev)

    # ── S4 ★★★ 空组**仍渲染连线 handle**（并证明 DOM 不是在骗人）
    ev = []
    for r in rs:
        b = r.get("deleteLastMember") or {}
        dom = b.get("DOM") or {}
        if dom.get("FAILED") or "handleCount" not in dom:
            continue
        store_box = b.get("空组框") or []
        rect = dom.get("rect") or {}
        ratios = []
        # ★ 这里原来直接算 `rect["w"] / store_box[0]` ⟹ 阴性对照 N3 把框改成
        #   `[0, 0]` 时**除零崩掉整个验收器**。教训：判据里每一个除法都要先看
        #   分母。改成「分母为 0 ⟹ 比值不可用、这条判据直接判否」而不是崩 ——
        #   崩掉会让阴性对照**测不出东西**（读数不动 ≠ 没崩）。
        ratio_note = "两个方向都算出来了"
        if (len(store_box) >= 2 and store_box[0] and store_box[1]
                and rect.get("w") and rect.get("h")):
            ratios = [rect["w"] / store_box[0], rect["h"] / store_box[1]]
        else:
            ratios = []
            ratio_note = "★ 比值不可用（store 框或 DOM rect 有 0）"
        ev.append({"round": r["round"], "handleCount": dom.get("handleCount"),
                   "handles": dom.get("handles"),
                   "DOM rect": rect, "store 框": store_box,
                   "两个方向的比值": ratios, "比值说明": ratio_note,
                   "★ 同一个 zoom 解释两者":
                       len(ratios) == 2 and abs(ratios[0] - ratios[1]) < 0.02,
                   "★ handle 数 > 0": (dom.get("handleCount") or 0) > 0,
                   "★ 且每个都能说出类型": all(
                       h.get("type") for h in (dom.get("handles") or [])),
                   "★ 三件同时": (dom.get("handleCount") or 0) > 0
                       and all(h.get("type") for h in (dom.get("handles") or []))
                       and len(ratios) == 2
                       and abs(ratios[0] - ratios[1]) < 0.02})
    add("S4:★★★ 空组**仍然渲染连线 handle**（并证明 DOM 的框没在骗人）",
        "★★★ 这是 793 待拍板 ② 的另一半（「0 成员组的连线 handle 要不要一起去掉」）"
        "的实测读数；★★ store 的框与 DOM 的 rect **差一个 zoom**（两个方向比值"
        "必须一致，否则说明框真的塌了）⟹ 这一条顺带排除「空组其实没渲染」的误读",
        ev and all(x["★ 三件同时"] for x in ev), ev)

    # ── S5 ★★ 空组**删得掉**（不是死路）
    ev = []
    for r in rs:
        c = r.get("cleanupEmptyGroup") or {}
        if "空组还在吗" not in c:
            continue
        ev.append({"round": r["round"], "按 Delete 后节点数": c.get("按 Delete 后节点数"),
                   "空组还在吗": c.get("空组还在吗"),
                   "★ 删得掉": c.get("★ 删得掉") is True})
    add("S5:★★ 空组**删得掉**（按 `Delete` 能删掉，不是死路）",
        "★ 这条是为了排除「空组是个用户清不掉的陷阱」这个猜测；"
        "★ 它同时让 S6 的「取消分组静默」有对照 —— 删得掉、但取消分组不作用",
        ev and all(x["★ 删得掉"] for x in ev), ev)

    # ── S6 ★★ 空组按 `Shift+G`（取消分组）是**静默**的
    ev = []
    for r in rs:
        u = r.get("emptyGroupUngroup") or {}
        if "节点数 Δ" not in u:
            continue
        ev.append({"round": r["round"], "节点数 Δ": u.get("节点数 Δ"),
                   "空组还在吗": u.get("空组还在吗"),
                   "★ 静默": u.get("★ 取消分组没作用") is True})
    add("S6:★★ 空组按 `Shift+G`（取消分组）—— 节点数不变、组也还在 ⟹ **静默**",
        "★★ 源码侧对应 `ungroupSelectedNodes` 的 `if (!group || children.length === 0) "
        "return state;`；★ 这是**第三个**同族静默（807 记的第二个：选区含组时按 `G`）；"
        "★ 注意它和 S5 是一对：有 S5 才知道「用户其实能删掉它」，"
        "所以这条是「缺一条提示」而不是「清不掉」",
        ev and all(x["★ 静默"] for x in ev), ev)

    # ── S7 ★★★ 作废闸：右键菜单那条臂**没有测到任何东西**，必须显式作废
    ev = []
    for r in rs:
        c = r.get("contextMenuOnEmptyGroup")
        ev.append({"round": r["round"],
                   "menuItems": (c or {}).get("menuItems"),
                   "★ 该臂作废（菜单没打开、没测到东西）":
                       (c is None) or not ((c or {}).get("menuItems"))})
    add("S7:★★★ 作废闸：右键菜单那条臂**探针没打开菜单** ⟹ 显式作废、不得据此下结论",
        "★★★ 源码里**确实有** `data-canvas-context-item=\"删除\"`"
        "（`CanvasContextMenu.tsx:191`）⟹ 空读数极易被写成「菜单里没有删除项」，"
        "那是**错的结论**；★ 按 802 起的「前提不满足的臂显式作废」，把它做成断言",
        ev and all(x["★ 该臂作废（菜单没打开、没测到东西）"] for x in ev), ev)

    # ── S8 静态锚点：两条「空就跳过」的边界
    i0 = src.find("if (kids.length === 0) continue;")
    # ★★ **第五次踩「同名锚点命中接口声明」**（799 updateNodeData、800 ungroup
    #   SelectedNodes、801 duplicateGraphSelection、802 createImageHdPreset、
    #   807 groupSelectedNodes —— 这次是**我自己的验收器**）。`src.find` 抓到的是
    #   `CanvasState` 的声明，`children.length === 0` 那行在**实现**里、离声明
    #   十万八千里 ⟹ 段长取不到。改成 `rfind`（取最后一次出现 = 实现）。
    hits = [i for i in range(len(src))
            if src.startswith("ungroupSelectedNodes: (", i)]
    j0 = hits[-1] if hits else -1
    seg_fit = src[max(0, i0 - 200):i0 + 60] if i0 >= 0 else ""
    seg_un = src[j0:j0 + 1200] if j0 >= 0 else ""
    add("S8:★★ 静态锚点：两条「空就跳过」的边界都在源码里",
        "★ fit 的 `kids.length === 0 → continue`（空组不动）与 "
        "`ungroupSelectedNodes` 的 `children.length === 0 → return state` "
        "（取消分组无作用）⟹ S3 与 S6 各有对应的静态侧证据",
        i0 >= 0 and "if (!group || children.length === 0) return state;" in seg_un,
        {"fit 的空组跳过": i0 >= 0, "fit 段长": len(seg_fit),
         "同名锚点出现次数": len(hits), "★ 取的是最后一次（实现）": len(hits) > 1,
         "ungroup 的空组返回": "if (!group || children.length === 0) return state;"
                            in seg_un})

    return checks


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    src = (ROOT / CS).read_text(encoding="utf-8")

    checks = run_checks(raw, src)
    nPass = sum(1 for c in checks if c["ok"])
    assert nPass == len(checks), (
        "★ 基线有 %d 项红（%r）" % (len(checks) - nPass,
                                   [c["id"] for c in checks if not c["ok"]]))

    def neg(name, why, mutate, expect):
        d = copy.deepcopy(raw)
        hit = mutate(d)
        assert hit, "★ raw 变异没命中"
        c = run_checks(d, src)
        flipped = [x["id"] for x in c if x["ok"] is False]
        if expect == "__NO_FLIP__":
            return {"name": name, "why": why, "evidence": {"hit": hit},
                    "expectFlipped": "（反向对照：期望不翻）",
                    "flipped": flipped, "ok": not flipped}
        return {"name": name, "why": why, "evidence": {"hit": hit},
                "expectFlipped": expect, "flipped": flipped,
                "ok": expect in flipped}

    def undo_broken(d):
        n = 0
        for r in d["rounds"]:
            a = r.get("deleteGroupWithMembers") or {}
            u = a.get("undo") or {}
            if u:
                u["★ 成员全回来了"] = False
                n += 1
        return n

    def no_shrink(d):
        n = 0
        for r in d["rounds"]:
            s = r.get("deleteLastMember_step1") or {}
            if "★ 框变了（贴合剩下的）" in s:
                s["★ 框变了（贴合剩下的）"] = False
                n += 1
        return n

    def empty_box_changed(d):
        n = 0
        for r in d["rounds"]:
            b = r.get("deleteLastMember") or {}
            if b.get("空组框"):
                b["空组框"] = [0, 0]
                b["★ 框没变（沿用还剩一个时的）"] = False
                n += 1
        return n

    def handles_gone(d):
        n = 0
        for r in d["rounds"]:
            b = r.get("deleteLastMember") or {}
            dom = b.get("DOM") or {}
            if dom.get("handleCount") is not None:
                dom["handleCount"] = 0
                dom["handles"] = []
                n += 1
        return n

    def undeletable(d):
        n = 0
        for r in d["rounds"]:
            c = r.get("cleanupEmptyGroup") or {}
            if "★ 删得掉" in c:
                c["★ 删得掉"] = False
                c["空组还在吗"] = True
                n += 1
        return n

    def menu_claim(d):
        """★ 伪造一个「菜单里没有删除项」的读数 ⟹ S7 必须翻。"""
        n = 0
        for r in d["rounds"]:
            c = r.get("contextMenuOnEmptyGroup")
            if c is not None:
                c["menuItems"] = [{"item": "撤销", "text": "撤销"}]
                n += 1
        return n

    def touch_unrelated(d):
        for r in d["rounds"]:
            r["note"] = "touched"
        return True

    negs = [
        neg("N1 ★★ raw：声称撤销后成员没全回来",
            "★ 验证 S1 守的不只是「连坐」，还有「**能撤销**」这半句",
            undo_broken,
            "S1:★★ 删掉一个**带成员的组**：成员**被连坐删除**，但 `Cmd+Z` **能完全撤销**"),
        neg("N2 ★★ raw：声称非空组删成员后框没变",
            "★★ 验证 S2 的阳性对照不是空转",
            no_shrink,
            "S2:★★ 阳性对照：组还剩成员时，删掉一个成员会让框**收缩贴合剩下的**"),
        neg("N3 ★★★ raw：把空组框改成 [0,0] 且声称没变",
            "★★★ 验证 S3 抓的是「框一个像素都没变、也没塌」",
            empty_box_changed,
            "S3:★★★ 空组**还在**，框**一个像素都没变**、也没塌成 0"),
        neg("N4 ★★★ raw：声称空组没有 handle 了",
            "★★★ 验证 S4 抓的是「空组仍渲染 handle」这条读数",
            handles_gone,
            "S4:★★★ 空组**仍然渲染连线 handle**（并证明 DOM 的框没在骗人）"),
        neg("N5 ★★ raw：声称空组删不掉",
            "★ 验证 S5 守的是「不是死路」这半句",
            undeletable,
            "S5:★★ 空组**删得掉**（按 `Delete` 能删掉，不是死路）"),
        neg("N6 ★★★ raw：伪造「菜单里有其它项」（即那臂其实测到了东西）",
            "★★★ 验证 S7 的作废闸：一旦那臂不再为空，就必须因为「没测到删除项」"
            "而翻红 ⟹ 防止有人拿空读数编出「菜单里没有删除项」",
            menu_claim,
            "S7:★★★ 作废闸：右键菜单那条臂**探针没打开菜单** ⟹ 显式作废、不得据此下结论"),
        neg("N7 ★★ 反向对照：只动与判据无关的字段（note）",
            "★ 证明判据锚的是读数、不是某段文本",
            touch_unrelated, "__NO_FLIP__"),
    ]

    report = {"batch": 808, "totals": {"passed": nPass, "total": len(checks)},
              "checks": checks, "negatives": negs,
              "negativesOk": sum(1 for n in negs if n["ok"]),
              "negativesTotal": len(negs), "rawSha": sha(RAW)}
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    for c in checks:
        print("  %s %s" % ("PASS" if c["ok"] else "FAIL", c["id"]))
    print("★ 主检查 %d/%d" % (nPass, len(checks)))
    for n in negs:
        print("  %s %s ｜ 翻红：%s" % ("PASS" if n["ok"] else "FAIL", n["name"],
                                      n["flipped"] or "无"))
    print("★ 阴性对照 %d/%d" % (sum(1 for n in negs if n["ok"]), len(negs)))
    return 0 if (nPass == len(checks) and all(n["ok"] for n in negs)) else 1


if __name__ == "__main__":
    sys.exit(main())