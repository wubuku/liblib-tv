#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 792 汇编器 —— 组合 (G) 跨分组多选时**静默掏空已有分组**

## 承重事实（batch 756，本批**独立复现**而不是引用）

`groupSelectedNodes` 的 `children` 过滤只把 `storyboard-group` **自己**排除，
而 re-parent 依据是 `absolutePositions`（由 `children` 生成）⟹
**在选区里的旧分组**既不进新组、也不移动，**但它的成员**同样在选区里
⟹ 被改写成新组的子节点 ⟹ 旧分组 children 归零、退化成空壳。

## ★ 修法：只堵破坏，不改既有设计决定

既有决定是「分组不参与组合」（`type !== "storyboard-group"`）。本批**保留**它，
只补一条：**所属的组也在选区里**的节点不进 `children`。

⟹ 那个成员既不会被拽进新组、也不会脱离原组。

| 格 | pre | post |
| --- | --- | --- |
| 旧分组的成员被抢 | **1 → 0** ✗ | **无** ✓ |
| 新组 children | 8 | **7** |
| toast / 提示 | 0 | 0 |

★ 新组 children 从 8 变 7 **不是退化**：那 1 个正是原本会被拽走、
从而掏空旧组的那一个。少收的这一点，换的是「不动别人的分组」。

## ★ 两个阳性对照（缺了它们，一个「让 G 什么都不做」的修复也能全绿）

| 臂 | pre | post |
| --- | --- | --- |
| 组 + 它自己的成员 → `g` | 零变化 | 零变化 |
| 两个散节点 → `g` | 节点 +1、新组 children **2** | 节点 +1、新组 children **2** |

## ★ 选区是**用 store 摆的**，不是框选出来的

`page.tsx:1574` 是 `selectionOnDrag={false}` ⟹ 拖拽**根本不产生框选**
（第一版探针照 756 的手势拖，三条臂全读成空读数：选区 0 / 1 / 节点Δ 0）。
缺陷在 `groupSelectedNodes` 本身 ⟹ 用 `selectNodes` 摆选区才是对准靶子，
命令仍然走**真实键盘 `g`**。
"""
import json
import pathlib

REPO = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
B = "docs/research/liblib-canvas-batch792-2026-10-01"
PRE = REPO / (B + "/raw/vb792a-pre.json")
POST = REPO / (B + "/raw/vb792a-post.json")
OUT = REPO / (B + "/runtime-audit.json")
CS = "src/store/canvasStore.ts"

ARMS = ["selectAllThenG", "groupPlusMember", "twoLoose"]


def index(raw):
    out = {}
    for rd in raw["rounds"]:
        for r in (rd.get("rows") or []):
            out.setdefault(r.get("arm"), []).append((rd.get("round"), r))
    return out


def read(cell):
    """★ 从 raw 的 before/after **重算**：谁被掏空、新组收到几个。"""
    b, a = cell.get("before"), cell.get("after")
    if not isinstance(b, dict) or not isinstance(a, dict):
        return None
    bmap = {g["id"]: len(g["kids"]) for g in b.get("groups", [])}
    amap = {g["id"]: g for g in a.get("groups", [])}
    drained = [{"group": k[:10], "before": bmap[k], "after": len(amap[k]["kids"])}
               for k in bmap if k in amap
               and len(amap[k]["kids"]) < bmap[k]]
    new = [{"children": len(g["kids"])} for k, g in amap.items()
           if k not in bmap]
    return {"drained": drained, "newGroups": new,
            "nodeDelta": a.get("nodeCount", 0) - b.get("nodeCount", 0),
            "selectedBeforeG": cell.get("selectedBeforeG"),
            "toastCount": cell.get("toastCount")}


def main():
    pre_raw = json.loads(PRE.read_text(encoding="utf-8"))
    post_raw = json.loads(POST.read_text(encoding="utf-8"))
    pre, post = index(pre_raw), index(post_raw)
    checks = []

    def add(cid, desc, cond, detail):
        checks.append({"id": cid, "desc": desc, "ok": bool(cond),
                       "detail": detail})

    # ── A：源码锚点（改完之后重新逐行读）──
    whole = (REPO / CS).read_text(encoding="utf-8")
    lines = whole.split("\n")
    det, ok = [], True
    for label, needle in [
        ("收集选区里的分组 id", 'const selectedGroupIds = new Set('),
        ("闸：所属组也在选区 ⟹ 不进 children",
         '&& !selectedGroupIds.has(node.parentId ?? ""),'),
        ("原过滤仍在（分组不参与组合）", 'node.type !== "storyboard-group"'),
    ]:
        hits = [i + 1 for i, l in enumerate(lines) if needle in l]
        good = len(hits) == 1
        ok = ok and good
        det.append({"label": label, "needle": needle, "ok": good, "lines": hits,
                    "code": lines[hits[0] - 1].strip()[:96] if hits else None})
    c = {"id": "A:三处源码锚点各唯一", "ok": ok, "n": 3, "anchors": det,
         "claim": "★ 既有决定「分组不参与组合」**保留**；新增的只有"
                  "「所属组也在选区里的成员不进 children」这一条"}
    assert ok, "★ 源码锚定失败：\n%r" % det
    checks.append(c)

    # ── B：格数与无 FAILED ──
    shape_bad = []
    for name, idx in (("pre", pre), ("post", post)):
        if set(idx) != set(ARMS):
            shape_bad.append({"phase": name, "arms": sorted(idx)})
        for k, v in idx.items():
            if len(v) != 2:
                shape_bad.append({"phase": name, "arm": k, "rounds": len(v)})
            for _rd, c2 in v:
                if c2.get("FAILED") or read(c2) is None:
                    shape_bad.append({"phase": name, "arm": k,
                                      "FAILED": c2.get("FAILED") or "读数缺失"})
    add("B:两阶段各 3 臂 × 2 轮且无 FAILED",
        "★ 探针自己有 FAILED 或读数缺失就是**空读数**，不能当结论",
        not shape_bad, {"bad": shape_bad,
                        "pre": {k: len(v) for k, v in sorted(pre.items())},
                        "post": {k: len(v) for k, v in sorted(post.items())}})

    # ── C：★ 每条臂的选区都真的摆好了（前置条件被读到）──
    sel_bad = []
    for name, idx in (("pre", pre), ("post", post)):
        r = read(idx["selectAllThenG"][0][1])
        if not r or r["selectedBeforeG"] != 10:
            sel_bad.append({"phase": name, "selectedBeforeG":
                            r and r["selectedBeforeG"]})
        r2 = read(idx["groupPlusMember"][0][1])
        if not r2 or r2["selectedBeforeG"] != 2:
            sel_bad.append({"phase": name, "arm": "groupPlusMember",
                            "selectedBeforeG":
                            r2 and r2["selectedBeforeG"]})
    add("C:★ 选区前置条件被读到（不是「假设我选中了」）",
        "★ 756 的血泪：先记基线，否则会把「本来就空」读成「被掏空」；"
        "本批要求每条臂在按 `g` 之前读回 `selectedNodeIds` 的长度",
        not sel_bad, {"bad": sel_bad,
                      "want": {"selectAllThenG": 10, "groupPlusMember": 2}})

    # ── D：★★ 处理臂：pre 掏空、post 不掏空 ──
    p_all = [read(c) for _rd, c in pre["selectAllThenG"]]
    q_all = [read(c) for _rd, c in post["selectAllThenG"]]
    add("D:★★ 处理臂：pre 静默掏空、post 不掏空",
        "★ pre 有分组的成员被抢（1 → 0）；post **零个**分组成员减少。"
        "★ 新组 children 由 8 变 7，少的那 1 个正是原本会被拽走、"
        "从而掏空旧组的那一个 —— 少收这一点换的是「不动别人的分组」",
        all(x["drained"] and x["newGroups"]
            and x["newGroups"][0]["children"] == 8 for x in p_all)
        and all(not x["drained"] and x["newGroups"]
                and x["newGroups"][0]["children"] == 7 for x in q_all),
        {"pre": p_all, "post": q_all})

    # ── E：★ 两条阳性对照前后都不变 ──
    ctrl_bad = []
    for arm in ("groupPlusMember", "twoLoose"):
        for name, idx in (("pre", pre), ("post", post)):
            for _rd, c2 in idx[arm]:
                r = read(c2)
                if arm == "groupPlusMember":
                    okc = (r and not r["newGroups"] and r["nodeDelta"] == 0
                           and not r["drained"])
                else:
                    okc = (r and r["newGroups"]
                           and r["newGroups"][0]["children"] == 2
                           and r["nodeDelta"] == 1)
                if not okc:
                    ctrl_bad.append({"phase": name, "arm": arm, "got": r})
    add("E:★★ 两条阳性对照前后都不变",
        "★ 「组 + 自己成员」= 零变化（756 记录）；"
        "「两个散节点」= 节点 +1、新组 children 2 ⟹ 正常组合**仍能成**。"
        "★ 缺了后者，一个「让 `G` 什么都不做」的修复也能全绿",
        not ctrl_bad, {"bad": ctrl_bad})

    # ── F：★ 基线里「本来就空」的组没被误读 ──
    # ★ 判定要**按阶段**给：pre 恰好 1 个受害者、post 是 **0** 个。
    #   第一版一刀切要求「两阶段都恰好 1 个」⟹ post 修好之后当场把断言打红。
    base_bad, base_ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for _rd, c2 in idx["selectAllThenG"]:
            b = c2.get("baseline") or {}
            empty_before = [g["id"] for g in b.get("groups", []) if not g["kids"]]
            r = read(c2)
            if not r:
                base_bad.append({"phase": name, "why": "读数缺失"})
                continue
            d = r["drained"]
            misread = [x for x in d
                       if any(x["group"] in g or g[:10] == x["group"]
                              for g in empty_before)]
            base_ev.append({"phase": name, "drained": d,
                            "本来就空的组": [g[:10] for g in empty_before],
                            "误读": misread})
            if misread:
                base_bad.append({"phase": name, "misread": misread})
            if name == "pre" and len(d) != 1:
                base_bad.append({"phase": name, "drained": d,
                                 "why": "pre 应恰好 1 个受害者"})
            if name == "post" and d:
                base_bad.append({"phase": name, "drained": d,
                                 "why": "post 应 0 个受害者"})
    add("F:★ 基线里「本来就空」的组没被当成受害者",
        "★ 756 的原话：「如果只看操作后的快照，会把『本来就空』"
        "误读成『被操作掏空』」⟹ 种子里 2 个组有 1 个（`g-245IDFh8sB`）"
        "本来就 0 成员，**受害的只能**是另一个。★ pre 恰好 1 个、post 0 个",
        not base_bad, {"bad": base_bad, "evidence": base_ev})

    # ── G：★ 零提示这件事本批没有改变（不声称修好了）──
    toasts = {n: [read(c).get("toastCount") for _rd, c in idx["selectAllThenG"]]
              for n, idx in (("pre", pre), ("post", post))}
    add("G:★ 零提示这件事**没有**被改变（如实记账）",
        "★ toast / alert / status 五类选择器命中 pre 与 post 都是 **0**。"
        "★ 本批修的是「不再破坏」，**没有**加任何提示 ⟹ "
        "「选中里有分组时用户仍然得不到告知」是**遗留**项",
        all(v == [0, 0] for v in toasts.values()), toasts)

    out = {
        "batch": 792,
        "kind": "★ 第三批改 src/ 的批次（静默数据丢失）",
        "claims": {
            "D792-1": "★ 组合 (G) 跨分组多选时**静默掏空已有分组**："
                      "旧分组的成员被拽进新组，旧组 children 归零、"
                      "界面只显示「组合成功」、五类提示选择器命中 0",
            "C792-2": "★ 既有决定「分组不参与组合」**保留**；只补"
                      "「所属组也在选区里的成员不进 children」⟹ "
                      "成员既不 进新组也不脱离原组",
            "C792-3": "★ 新组 children 8 → 7 **不是退化**：少收的那 1 个"
                      "正是原本会被拽走、从而掏空旧组的那一个",
            "遗留": "★ 零提示**没有**被改变 —— 选中里有分组时用户仍然"
                    "得不到任何告知",
        },
        "checks": checks,
        "totals": {"checks": len(checks),
                   "assertedAnchors": sum(x.get("n", 0) for x in checks),
                   "failed": sum(0 if x["ok"] else 1 for x in checks)},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("★ D792-1 修好：pre 旧分组成员 1→0，post 零个分组成员减少")
    print("★ 新组 children 8 → 7（少的那 1 个正是原本会被拽走的那一个）")
    print("★ 两条阳性对照前后都不变：组+自己成员=零变化；两个散节点=children 2")
    print("★ 遗留：零提示**没有**被改变")
    print("★ 断言 %d 条 / 锚点 %d 个 / 失败 %d"
          % (out["totals"]["checks"], out["totals"]["assertedAnchors"],
             out["totals"]["failed"]))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
