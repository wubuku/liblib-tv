#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 791 汇编器 —— 「双击空白画布开添加节点面板」这条入口

## 本批修了**同一个监听器上的两个缺陷**

758 记了前一个（入口从未触发）。后一个是本批**做回归臂时撞出来的**。

| 编号 | 缺陷 | pre 实测 |
| --- | --- | --- |
| D791-1 | 监听器注册在**冒泡**阶段，而 React Flow 在 pane 处 `stopPropagation` ⟹ **收不到** | 双击空白画布 面板条目 0 → **0** |
| D791-2 | 闸用 `closest('.react-flow__pane')`，但 v12 的 DOM 里 pane 是 viewport 的**最外层**、节点在它**里面** ⟹ **挡不住节点** | 双击**节点** 面板条目 0 → **9**（误开） |

★ D791-2 的依据不是发明：源码注释写的是「源站**空**画布双击 = 打开添加节点面板」，
「空」字就是契约。实测空白处 `elementFromPoint` 命中的正是 pane **自己**
（`isPaneItself=true`）⟹ 正确判据是 `classList.contains`。

## ★ 758 列的第三个修法**不可用**

758 给的三个方向里「改用 React Flow 的 `onPaneDoubleClick` prop」在
`@xyflow/react` v12 **不存在**（`grep -rl onPaneDoubleClick
node_modules/@xyflow/react/dist/` 无命中）⟹ 只剩「挂到 pane 上」与
「改捕获阶段」，而运行时读数（容器**捕获** = 1）直接支持后者。

## 读数（同一份探针，pre / post 各 2 轮，4 臂）

| 臂 | pre | post |
| --- | --- | --- |
| 双击空白画布 | 0 → **0** ✗ | 0 → **9** ✓ |
| 双击节点 | 0 → **9** ✗ | 0 → **0** ✓ |
| `Tab` 键 | 0 → 9 ✓ | 0 → 9 ✓ |
| 右键菜单 | 0 → 9 ✓ | 0 → 9 ✓ |

★ 两条阳性对照（`Tab`、右键菜单）**pre 就通** ⟹ 「双击那条坏了」与
「面板本身打不开」无法区分被排除。

## ★ 一处**未解释**的读数（不声称）

`容器冒泡` 计数 pre = 0、post = **1**。我的改动既不调 `stopPropagation`
也不改传播路径 ⟹ **解释不了**。功能读数（面板开没开）不受影响，
本批**不对**这个计数给机制说法。
"""
import json
import pathlib

REPO = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
B = "docs/research/liblib-canvas-batch791-2026-10-01"
PRE = REPO / (B + "/raw/vb791a-pre.json")
POST = REPO / (B + "/raw/vb791a-post.json")
OUT = REPO / (B + "/runtime-audit.json")
PAGE = "src/app/page.tsx"

ARMS = ["dblclickPane", "dblclickNode", "tabKey", "contextMenu"]


def line_of(rel, n):
    return (REPO / rel).read_text(encoding="utf-8").split("\n")[n - 1]


def index(raw):
    out = {}
    for rd in raw["rounds"]:
        for r in (rd.get("rows") or []):
            out.setdefault(r.get("arm"), []).append((rd.get("round"), r))
    return out


def got(cell):
    """★ 从 raw 重算：面板条目从几条变成几条、开了没有。"""
    return {"before": cell.get("before"), "after": cell.get("after"),
            "opened": bool(cell.get("panelOpened")),
            "failed": cell.get("FAILED")}


def main():
    pre_raw = json.loads(PRE.read_text(encoding="utf-8"))
    post_raw = json.loads(POST.read_text(encoding="utf-8"))
    pre, post = index(pre_raw), index(post_raw)
    checks = []

    def add(cid, desc, cond, detail):
        checks.append({"id": cid, "desc": desc, "ok": bool(cond),
                       "detail": detail})

    # ── A：源码行锚定（改完之后重新逐行读出来的行号）──
    det, ok = [], True
    whole = (REPO / PAGE).read_text(encoding="utf-8")
    for label, n, needle in [
        ("注册用捕获阶段", None, 'addEventListener("dblclick", handleDoubleClick, true)'),
        ("清理也用捕获阶段", None,
         'removeEventListener("dblclick", handleDoubleClick, true)'),
        ("闸改成「就是 pane」", None, 'classList.contains("react-flow__pane")'),
    ]:
        hits = [i + 1 for i, l in enumerate(whole.split("\n")) if needle in l]
        good = len(hits) == 1
        ok = ok and good
        det.append({"label": label, "needle": needle, "ok": good,
                    "lines": hits,
                    "code": line_of(PAGE, hits[0]).strip()[:100] if hits else None})
    c = {"id": "A:三处源码锚点各唯一", "ok": ok, "n": 3, "anchors": det,
         "claim": "★ add 与 remove **两侧**都带 `{ capture: true }`（漏改 cleanup "
                  "会留下一个再也摘不掉的监听器），且闸是 `classList.contains`"}
    assert ok, "★ 源码锚定失败：\n%r" % det
    checks.append(c)

    # ── B：格数与无失败 ──
    shape_bad = []
    for name, idx in (("pre", pre), ("post", post)):
        if set(idx) != set(ARMS):
            shape_bad.append({"phase": name, "arms": sorted(idx)})
        for k, v in idx.items():
            if len(v) != 2:
                shape_bad.append({"phase": name, "arm": k, "rounds": len(v)})
            for _rd, c2 in v:
                if got(c2)["failed"]:
                    shape_bad.append({"phase": name, "arm": k,
                                      "FAILED": got(c2)["failed"]})
    add("B:两阶段各 4 臂 × 2 轮且无 FAILED",
        "★ 4 臂（双击空白/双击节点/Tab/右键菜单）× 2 轮，pre 与 post 都是",
        not shape_bad, {"bad": shape_bad,
                        "pre": {k: len(v) for k, v in sorted(pre.items())},
                        "post": {k: len(v) for k, v in sorted(post.items())}})

    # ── C：★★ D791-1（死入口）：pre 空白双击 0→0，post 0→9 ──
    p_pane = [got(c) for _rd, c in pre["dblclickPane"]]
    q_pane = [got(c) for _rd, c in post["dblclickPane"]]
    add("C:★★ D791-1 死入口修好了",
        "★ 双击**空白画布**：pre 面板条目恒为 0（入口从未触发）、post 变成 9",
        all(not x["opened"] and x["after"] == 0 for x in p_pane)
        and all(x["opened"] and x["after"] == 9 for x in q_pane),
        {"pre": p_pane, "post": q_pane})

    # ── D：★★ D791-2（误开）：pre 节点双击 0→9，post 0→0 ──
    p_node = [got(c) for _rd, c in pre["dblclickNode"]]
    q_node = [got(c) for _rd, c in post["dblclickNode"]]
    add("D:★★ D791-2 节点双击不再误开面板",
        "★ 双击**节点**：pre 会误开（0 → 9）、post 不开（0 → 0）；"
        "★ 这是本批做回归臂时**撞出来的**既有缺陷，不是修复引入的",
        all(x["opened"] and x["after"] == 9 for x in p_node)
        and all(not x["opened"] and x["after"] == 0 for x in q_node),
        {"pre": p_node, "post": q_node})

    # ── E：★ 两条阳性对照前后都通（没被弄坏）──
    ctrl_bad = []
    for arm in ("tabKey", "contextMenu"):
        for name, idx in (("pre", pre), ("post", post)):
            for _rd, c2 in idx[arm]:
                g = got(c2)
                if not (g["opened"] and g["after"] == 9 and g["before"] == 0):
                    ctrl_bad.append({"phase": name, "arm": arm, "got": g})
    add("E:★ 两条别的入口前后都通",
        "★ `Tab` 键（`page.tsx:1360`）与右键菜单「添加节点」"
        "（`CanvasContextMenu.tsx:122`）pre 就通、post 仍通 ⟹ "
        "「双击那条坏了」与「面板本身打不开」可被区分",
        not ctrl_bad, {"bad": ctrl_bad})

    # ── F：★ 两轮逐臂完全一致 ──
    same = []
    for name, idx in (("pre", pre), ("post", post)):
        for arm, lst in idx.items():
            a = got(lst[0][1])
            b = got(lst[1][1])
            same.append(a == b)
    add("F:两轮逐臂完全一致", "★ 8 个格子每格两轮读数相同 ⟹ 不是抖动",
        all(same), {"perCell": len(same), "allSame": all(same)})

    # ── G：机制读数（pre 的相位计数）＋ ★ 未解释项如实记账 ──
    caps = [ (c or {}).get("counters") for _rd, c in pre["dblclickPane"] ]
    cap_ok = all(k and k.get("cap") == 1 and k.get("bub") == 0
                 and k.get("paneBub") == 1 for k in caps)
    post_caps = [ (c or {}).get("counters") for _rd, c in post["dblclickPane"] ]
    post_bub = [k.get("bub") for k in post_caps if k]
    add("G:★ 机制读数被复现，且未解释项如实记账",
        "★ pre 的相位计数：容器**捕获** 1 / 容器冒泡 **0** / pane 冒泡 1 "
        "⟹ 事件在 pane 之后被掐断，这正是改捕获阶段的依据。"
        "★ post 的容器冒泡变成 %s —— 本批**解释不了**（改动不涉及传播），"
        "故不据此下任何机制结论" % post_bub,
        cap_ok, {"preCounters": caps, "postContainerBubble": post_bub,
                 "未解释": True})

    out = {
        "batch": 791,
        "kind": "★ 第二批改 src/ 的批次（修同一个监听器上的两个缺陷）",
        "claims": {
            "D791-1": "★ 监听器注册在冒泡阶段 ⟹ 空白画布双击这条入口**从未触发**"
                      "（pre 实测面板条目恒 0）；改捕获阶段后 0 → 9",
            "D791-2": "★ 闸用 `closest()`，而 v12 的 pane 是 viewport 最外层、"
                      "节点在它里面 ⟹ 闸**从来没挡住节点** ⟹ 双击任意节点"
                      "都误开面板（pre 与 post 修前都是 0 → 9）",
            "C791-3": "★ 758 列的第三方向 `onPaneDoubleClick` 在 "
                      "`@xyflow/react` v12 **不存在**",
            "依据": "★ D791-2 不是发明：源码注释写的是「源站**空**画布双击」，"
                    "「空」字就是契约；且实测空白处命中的正是 pane 自己",
        },
        "checks": checks,
        "totals": {"checks": len(checks),
                   "assertedAnchors": sum(x.get("n", 0) for x in checks),
                   "failed": sum(0 if x["ok"] else 1 for x in checks)},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("★ D791-1 修好：空白画布双击 pre 0→0 死入口、post 0→9")
    print("★ D791-2 修好：节点双击 pre 0→9 误开、post 0→0")
    print("★ C791-3：`onPaneDoubleClick` 在 v12 不存在")
    print("★ 两条别的入口（Tab / 右键菜单）前后都通，没被弄坏")
    print("★ 断言 %d 条 / 锚点 %d 个 / 失败 %d"
          % (out["totals"]["checks"], out["totals"]["assertedAnchors"],
             out["totals"]["failed"]))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
