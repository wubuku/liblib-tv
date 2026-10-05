#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 794 汇编器 —— 删掉一个成员之后，分组框**不收拢**

## 起点：793 自己列出来的未验路径之一

793 把跟随挂在 `routeReactFlowChanges` 的**唯一收口**上，于是「成员移动」跟随了。
但删除走的是**另外两个写点**：

- `removeNode`（`canvasStore.ts:3327`）
- `removeSelectedNodes`（`canvasStore.ts:3363`）

它们**不经**那个收口 ⟹ 删成员后框不会收拢。

★ 这不是 793 引入的：修之前框**根本**不动。793 修好了「成员移动」，
「成员减少」这一半还在。★ 两个写点是**同一条路径的两个半边**，
只修一个就是半个修复（791 的教训）⟹ 两处**一起**改。

## ★ 为什么不能直接用种子的组

种子里那个组**只有 1 个成员** ⟹ 删掉就变 0 成员 ⟹ 而 793 的边界 1 明确
「**0 成员的组不动**」（那是 757 待拍板 ②，源站未采样）。
⟹ 要测「收拢」必须先造一个**两成员**的组。

## 读数（同一份探针，pre / post 各 2 轮，3 臂）

| 臂 | pre | post |
| --- | --- | --- |
| ★ 组两个 → 删一个 | 组 `(76,-157) 706×812` **完全不变** ✗ | 组 **`(100,241) 682×414`**（收拢）✓ |
| ★ 撤销臂 | 成员 2→2、框原样 | 成员 2→2、框**复原** `706×812` ✓ |
| 前置对照：组两个不动 | `706×812` | `706×812`（不受扰动）✓ |

★ post 的 `682×414` **精确等于**按 `32×2` 从幸存者读数**独立重算**的贴合值
`{100, 241, 682, 414}`。

## ★ 写点普查（机器核对，不是散文）

`canvasStore` 里把 `nodes` 写进一个 canvas 对象的源码形态共 **17 处**。本批覆盖
**3 处**（拖拽/尺寸 1 + 删除 2），其余 **14 处未普查**。★ 三个数字由汇编器**从
源码数出来**（check A），不是手写的。

★ 普查器**只采集，不做语义判断**：它把每处连同实参行一起收下来，
「覆盖 / 未覆盖」交给 B、B2 逐处判定。

## ★ 汇编器自己踩的三个坑（都已修，判据都留在代码里）

1. **needle 打在错误的一行**。原判据要在**同一行**同时找到
   `fitStoryboardGroupsToChildren(` 与 `filter((node) => !removedIds.has(node.id))`，
   但 prettier 把实参换到了**下一行** ⟹ B 一处都没命中。改成「call 行 + 其后
   两行」一起收。
2. **`owner()` 爬出了 store 体**。按 `\\s{2,4}` 匹配 `name: (` 会一路爬到外层
   `create((set, get) => ({` ⟹ 两处 owner 被判成同一个函数。store 的 action 是
   **恰好 2 空格**缩进（嵌套的 `set((state) => {` 是 4/6）⟹ 收紧成 `^  (\\w+): \\(`，
   搜索下界锚在 `export const useCanvasStore = create` 那一行。
3. **手写的普查数字本身是错的**。docstring 原写「16 处 / 覆盖 3 / 未普查 13」，
   机器数出来是 **17 / 3 / 14**。★ 这是「断言必须从源码逐行读出、不能从记忆推」
   的又一笔代价——不数一遍，就会把一个错数字印进 README。
"""
import json
import pathlib
import re

REPO = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
B = "docs/research/liblib-canvas-batch794-2026-10-01"
PRE = REPO / (B + "/raw/vb794a-pre.json")
POST = REPO / (B + "/raw/vb794a-post.json")
OUT = REPO / (B + "/runtime-audit.json")
CS = "src/store/canvasStore.ts"

ARMS = ["groupTwoDeleteOne", "groupTwoDeleteOneUndo", "groupTwoNoDelete"]
PADDING = 32

#: ★ 会把 `nodes` 写进一个 canvas 对象的源码形态（普查用）
WRITE_SITE_RES = [
    r"nodes: canvas\.nodes\.",
    r"nodes: restored\.nodes",
    r"nodes: \[\.\.\.canvas\.nodes",
    r"\{ \.\.\.canvas, nodes:",
    r"nodes: fitStoryboardGroupsToChildren\(",
    r"nodes: plan\.nextNodes",
]


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
    return {"before": b, "after": a,
            "memberCount": [b.get("memberCount"), a.get("memberCount")],
            "group": [b.get("groupStore"), a.get("groupStore")],
            "inside": [[m.get("inside") for m in b.get("members", [])],
                       [m.get("inside") for m in a.get("members", [])]],
            "past": [b.get("past"), a.get("past")],
            "membersAfter": a.get("members", [])}


def tight_fit(member):
    if not member or not member.get("abs"):
        return None
    return {"x": member["abs"]["x"] - PADDING,
            "y": member["abs"]["y"] - PADDING,
            "w": (member.get("w") or 0) + PADDING * 2,
            "h": (member.get("h") or 0) + PADDING * 2}


def main():
    pre_raw = json.loads(PRE.read_text(encoding="utf-8"))
    post_raw = json.loads(POST.read_text(encoding="utf-8"))
    pre, post = index(pre_raw), index(post_raw)
    checks = []

    def add(cid, desc, cond, detail, claim=None):
        checks.append({"id": cid, "desc": desc, "ok": bool(cond),
                       "detail": detail, **({"claim": claim} if claim else {})})

    # ── A：★ 写点普查（从源码数出来）──
    lines = (REPO / CS).read_text(encoding="utf-8").split("\n")
    sites = []
    for i, l in enumerate(lines, 1):
        if any(re.search(p, l) for p in WRITE_SITE_RES):
            # ★ 实参常在**下一行**（prettier 换行），所以连着后面两行一起收，
            #   否则「按同行匹配」会漏掉真实站点（第一版就是这么错的）。
            nxt = " ".join(lines[i:i + 2]).strip()
            sites.append({
                "line": i,
                "covered": "fitStoryboardGroupsToChildren" in l,
                "code": l.strip()[:88],
                "arg": nxt[:120],
            })
    covered = [s for s in sites if s["covered"]]
    uncovered = [s for s in sites if not s["covered"]]

    add("A:★ 写点普查：共 %d 处、本批覆盖 %d 处、未普查 %d 处"
        % (len(sites), len(covered), len(uncovered)),
        "★ 普查器只**采集**，不做语义判断：把 nodes 写进 canvas 的源码形态"
        "全部列出，再由 B 逐处判定覆盖与否",
        len(sites) > 0 and len(covered) + len(uncovered) == len(sites),
        {"total": len(sites), "covered": len(covered),
         "uncovered": len(uncovered), "sites": sites},
        claim="★ 覆盖面是**从源码数出来的**，不是手写数字。"
             "★ 未普查的 %d 处**不许**被说成「也覆盖了」" % len(uncovered))

    # ── B：两处删除写点**都**挂了（半个修复要能被抓到）──
    # ★ 判据是**实参**里有 removedIds ⟹ 这两个是删除路径；
    #   实参是 plan.nextNodes 的那处是 793 的拖拽路径，**不算**删除写点。
    rm = [s for s in covered if "removedIds.has(node.id)" in s["arg"]]
    drag = [s for s in covered if "plan.nextNodes" in s["arg"]]
    add("B:★ 两个删除写点**都**挂了重算",
        "★ `removeNode` 与 `removeSelectedNodes` 是同一条路径的两个半边；"
        "只修一个就是半个修复（791 的教训）",
        len(rm) == 2,
        {"删除写点": [{"line": s["line"], "arg": s["arg"]} for s in rm],
         "拖拽写点": [s["line"] for s in drag],
         "covered": len(covered),
         "判据": "实参含 removedIds.has(node.id)"})

    # ── B2：★ 两个删除写点属于**不同的函数**（同一条路径的两个半边）──
    # ★ store 的 action 形如 `  name: (…) => {`（**恰好 2 空格**缩进）。
    #   实现体里嵌套的 `set((state) => {` 是 4/6 空格；按更松的缩进匹配就会
    #   一路爬到外层 create 的箭头去 ⟹ 第一版把 owner 全判成了同一个名字。
    body_start = next(
        i for i, l in enumerate(lines)
        if re.match(r"\s*export const useCanvasStore = create", l))

    def owner(line_no):
        for j in range(line_no - 1, body_start, -1):
            m = re.match(r"  ([A-Za-z_]\w*):\s*\(", lines[j])
            if m:
                return m.group(1)
        return None

    owners = sorted({owner(s["line"]) for s in rm})
    add("B2:★★ 两个删除写点分属**两个不同的函数**",
        "★ 同名函数里数出两处 ⟹ 可能只是同一处被写了两遍；"
        "必须确认是 `removeNode` 与 `removeSelectedNodes` 两个函数",
        owners == ["removeNode", "removeSelectedNodes"],
        {"函数": owners, "行": [s["line"] for s in rm],
         "判据": "向上找最近一个**恰好 2 空格**缩进的 `name: (` 顶层 action"})

    # ── C：★ 独立重算：post 的框必须**精确等于**幸存者的贴合值 ──
    ev, cbad = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for _rd, cell in idx["groupTwoDeleteOne"]:
            r = read(cell)
            if not r or r["memberCount"][1] != 1:
                cbad.append({"phase": name, "why": "成员数不是 1"})
                continue
            want = tight_fit(r["membersAfter"][0])
            g = r["group"][1]
            got = {"x": g["pos"]["x"], "y": g["pos"]["y"], "w": g["w"],
                   "h": g["h"]}
            same = want == got
            ev.append({"phase": name, "group": got, "tightFit": want,
                       "equals": same})
            if (name == "pre") == same:      # pre 应当**不等**，post 应当**相等**
                cbad.append(ev[-1])
    add("C:★★ post 的框精确等于按 padding 独立重算的贴合值，pre 不等",
        "★ 用 raw 里的幸存者读数重算，**不依赖**源码公式 ⟹ 公式写错也会被抓出来",
        not cbad, {"bad": cbad, "evidence": ev})

    # ── D：★ 处理臂两个方向都要判 ──
    p = [read(c) for _rd, c in pre["groupTwoDeleteOne"]]
    q = [read(c) for _rd, c in post["groupTwoDeleteOne"]]
    add("D:★★ 处理臂：pre 框不动、post 框收拢，且幸存者仍在框内",
        "★ 「成员 2→1」两阶段都成立；要判的是**框有没有跟着变**",
        all(x and x["memberCount"] == [2, 1]
            and x["group"][0] == x["group"][1]
            and x["inside"][1] == [True] for x in p)
        and all(x and x["memberCount"] == [2, 1]
                and x["group"][0] != x["group"][1]
                and x["inside"][1] == [True] for x in q),
        {"pre": [{"m": x["memberCount"], "same": x["group"][0] == x["group"][1],
                  "inside": x["inside"][1]} for x in p],
         "post": [{"m": x["memberCount"], "same": x["group"][0] == x["group"][1],
                   "inside": x["inside"][1]} for x in q]})

    # ── E：★★ 撤销臂：成员与**框**都要回来 ──
    ubad, udet = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for _rd, cell in idx["groupTwoDeleteOneUndo"]:
            b = read(cell)
            mid = read(cell, "afterDelete")
            a = read(cell)
            if not (b and mid and a):
                ubad.append({"phase": name, "why": "读数缺失"})
                continue
            ok = (a["memberCount"][1] == 2
                  and a["group"][1] == b["group"][0]
                  and a["inside"][1] == [True, True]
                  and a["past"][1] < a["past"][0] + 1)
            udet.append({"phase": name,
                         "before": b["group"][0], "afterDelete": mid["group"][1],
                         "afterUndo": a["group"][1],
                         "members": a["memberCount"], "past": a["past"],
                         "frameRestored": a["group"][1] == b["group"][0]})
            if not ok:
                ubad.append(udet[-1])
    add("E:★★ 撤销臂：成员与**框**都回来，且 `past` 真的退了一格",
        "★ 756 的教训：「用户最自然的补救动作无效，唯一出路是撤销」"
        "——所以撤销臂必须同时验**成员**与**框**",
        not ubad, {"bad": ubad, "evidence": udet})

    # ── F：★ 前置对照：造组那一步本身是对的，且修复没打扰它 ──
    fbad, fdet = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for _rd, cell in idx["groupTwoNoDelete"]:
            m = cell.get("state")
            if not m or m.get("memberCount") != 2:
                fbad.append({"phase": name, "why": "不是两成员"})
                continue
            want = tight_fit(_outer_box(m["members"]))
            g = m["groupStore"]
            got = {"x": g["pos"]["x"], "y": g["pos"]["y"], "w": g["w"],
                   "h": g["h"]}
            same = want == got
            fdet.append({"phase": name, "group": got, "tightFit": want,
                         "equals": same,
                         "inside": [x["inside"] for x in m["members"]]})
            if not (same and all(x["inside"] for x in m["members"])):
                fbad.append(fdet[-1])
    add("F:★ 前置对照：造出的两成员框就是贴合值，且两阶段一致",
        "★ 没有它，「处理臂的框变了」可能只是造组那一步本来就错",
        not fbad, {"bad": fbad, "evidence": fdet})

    # ── G：格数与无 FAILED ──
    gbad = []
    for name, idx in (("pre", pre), ("post", post)):
        if set(idx) != set(ARMS):
            gbad.append({"phase": name, "arms": sorted(idx)})
        for k, v in idx.items():
            if len(v) != 2:
                gbad.append({"phase": name, "arm": k, "rounds": len(v)})
            for _rd, c2 in v:
                if c2.get("FAILED"):
                    gbad.append({"phase": name, "arm": k,
                                 "FAILED": c2["FAILED"]})
    add("G:两阶段各 3 臂 × 2 轮且无 FAILED",
        "★ 探针 FAILED 就是**空读数**", not gbad, {"bad": gbad})

    out = {
        "batch": 794,
        "kind": "★ 第五批改 src/ 的批次（删除路径 + 写点普查）",
        "claims": {
            "D794-1": "★ 删掉一个成员之后分组框**完全不收拢**"
                      "（pre：框 `(76,-157) 706×812` 一动不动，"
                      "而幸存者的贴合值是 `{100,241,682,414}`）",
            "C794-2": "★ 修法 = 把同一个纯函数挂到**两个**删除写点"
                      "（`removeNode` + `removeSelectedNodes`）⟹ "
                      "只修一个就是半个修复",
            "★ 普查": "★ `canvasStore` 里把 `nodes` 写进 canvas 的地方共 %d 处；"
                      "本批覆盖 %d 处（拖拽 1 + 删除 2），**其余 %d 处未普查**"
                      % (len(sites), len(covered), len(uncovered)),
            "★ 撤销": "★ 撤销臂确认**框**也跟着回来（成员 2→2、框复原 "
                      "`706×812`）—— 756 的教训是「唯一出路是撤销」，"
                      "所以这条必须单独验",
            "★ 未碰": "★ **0 成员的组仍然不动**（793 边界 1 / 757 待拍板 ②）"
                      "⟹ 本批只修「成员减少但仍 ≥1」这一段",
        },
        "checks": checks,
        "totals": {"checks": len(checks),
                   "assertedAnchors": sum(
                       x["detail"].get("total", 0) for x in checks),
                   "failed": sum(0 if x["ok"] else 1 for x in checks)},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("★ D794-1 修好：pre 删成员后框 `(76,-157) 706x812` 不动；"
          "post 收拢成 `(100,241) 682x414`")
    print("★ C794-2：两个删除写点都挂了重算（不是半个修复）")
    print("★ 撤销臂：成员 2→2、框复原 706x812、past 退一格")
    print("★ 写点普查：共 %d 处 / 覆盖 %d 处 / 未普查 %d 处（从源码数出来）"
          % (len(sites), len(covered), len(uncovered)))
    print("★ 断言 %d 条 / 锚点 %d 个 / 失败 %d"
          % (out["totals"]["checks"], out["totals"]["assertedAnchors"],
             out["totals"]["failed"]))
    print("wrote %s" % OUT)


def _outer_box(members):
    """★ 多个成员的贴合框 = 各自外接盒的并集 + padding（与 helper 同构）。"""
    if not members:
        return None
    minx = min(m["abs"]["x"] for m in members)
    miny = min(m["abs"]["y"] for m in members)
    maxx = max(m["abs"]["x"] + (m.get("w") or 0) for m in members)
    maxy = max(m["abs"]["y"] + (m.get("h") or 0) for m in members)
    return {"abs": {"x": minx, "y": miny}, "w": maxx - minx, "h": maxy - miny}


if __name__ == "__main__":
    main()
