#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 808 探针 a：空组边界 —— 「删掉组里最后一个成员」之后会剩下什么

## 起点

793 留了一条待拍板 ②（空组要不要收缩/弱化、0 成员组的连线 handle 要不要一起去掉），
至今没有空组探针臂。807 顺带量到一条读数：组被**搬空**（成员被组合进另一个组）之后
**框保持原样**（`1000×1487`，正好等于原成员包围盒 ⊕ 2×padding）。

★ 但 807 覆盖的是「成员被搬进另一个组」那**一条**变空路径。另一条更常见、
也更危险的路径**没测**：**直接删掉组里的成员**。源码侧对应
`fitStoryboardGroupsToChildren` 的「★ 边界 1：`if (kids.length === 0) continue;`
空组不动」。

## 三条臂

| 臂 | 做什么 | 为什么值得问 |
| --- | --- | --- |
| `deleteGroupWithMembers` | 选中一个**带 2 个成员**的组，按 `Delete` | ★ `removeNode` 用的是 `withDescendantIds` ⟹ **成员会被连坐删除**；而键盘删除路径（`page.tsx:1376`）**没有任何确认**（对比：删画布**有**确认框）。这条问的是「连坐有没有告知、能不能撤回来」 |
| `deleteLastMember` | 先删掉一个成员，再删掉**最后一个** | 空组还在吗？框变了吗？★ **还渲染连线 handle 吗**？还有边吗？还能选中吗？ |
| `cleanupEmptyGroup` | 对空组按 `Shift+G`，再走右键「删除」 | `ungroupSelectedNodes` 有 `children.length === 0 → return state` ⟹ 空组**取消分组不掉**。那用户到底能不能清掉它？ |

## 判据纪律

- 只记**读数**，不预设「应该怎样」。空组该收缩还是该留着，是**待拍板**的事，
  本批只报事实。
- ★ 每条臂都要**阳性对照**：上一臂的动作**确实生效了**才算数
  （「删完什么都没变」和「删了但没生效」在读数上很像）。
- ★ 删除走**真实键盘**（`Delete`），不走 store —— 因为「有没有确认框」这件事
  本身就只能在真实路径上看。
"""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"


def ev(pg, js, arg=None):
    try:
        return pg.evaluate(js) if arg is None else pg.evaluate(js, arg)
    except Exception as exc:
        return {"FAILED": type(exc).__name__ + ": " + str(exc)[:220]}


SELECT = r"""(ids)=>{
  const s=window.__libtv_store; if(!s) return {ok:false};
  s.getState().selectElements({nodeIds: ids, edgeIds: []});
  const snap=s.getState().getSelectionSnapshot();
  return {ok:true, selected: s.getState().selectedNodeIds,
          snapNodeIds: (snap && snap.nodeIds)||[]};
}"""

GRAPH = r"""()=>{
  const s=window.__libtv_store; if(!s) return null;
  const st=s.getState();
  const cur=st.canvases.find(c=>c.id===st.activeCanvasId)||st.canvases[0];
  const idx={}; cur.nodes.forEach(n=>{idx[n.id]=n;});
  const dim=n=>({w:(n.width ?? Number(n.style&&n.style.width))||350,
                 h:(n.height ?? Number(n.style&&n.style.height))||180});
  const nodes=cur.nodes.map(n=>{
    const d=dim(n);
    return {id:n.id, type:n.type, parentId:n.parentId||null,
            pos:{x:n.position.x,y:n.position.y}, w:d.w, h:d.h,
            kids: cur.nodes.filter(k=>k.parentId===n.id).map(k=>k.id)};
  });
  return {nodeCount:cur.nodes.length, edgeCount:cur.edges.length,
          edges: cur.edges.map(e=>({id:e.id, source:e.source, target:e.target})),
          selected: st.selectedNodeIds||[], nodes};
}"""

# ★ 空组的 DOM 侧读数：还在不在、框多大、**还渲染几个连线 handle**
GROUP_DOM = r"""(gid)=>{
  const el=document.querySelector('[data-id="'+gid+'"]');
  if(!el) return {present:false};
  const r=el.getBoundingClientRect();
  const handles=el.querySelectorAll('.react-flow__handle');
  const kinds=[];
  handles.forEach(h=>kinds.push({cls:h.className.slice(0,60),
                                 type:h.getAttribute('data-handleid')||null}));
  return {present:true,
          rect:{w:Math.round(r.width), h:Math.round(r.height)},
          handleCount:handles.length, handles:kinds,
          selected: el.className.indexOf('selected')>=0};
}"""

OPEN_MENU = """(x,y)=>{
  const pane=document.querySelector('.react-flow__pane');
  if(!pane) return {ok:false, why:'no pane'};
  const opts={bubbles:true, cancelable:true, clientX:x, clientY:y, button:0};
  pane.dispatchEvent(new MouseEvent('mousedown',opts));
  pane.dispatchEvent(new MouseEvent('mouseup',opts));
  pane.dispatchEvent(new MouseEvent('contextmenu',opts));
  return {ok:true};
}"""

MENU_ITEMS = """()=>Array.from(document.querySelectorAll('[data-canvas-context-item]'))
      .map(b=>({item:b.getAttribute('data-canvas-context-item'),
                text:(b.textContent||'').trim().slice(0,12)}))"""

CLICK_MENU = r"""(label)=>{
  const b=document.querySelector('[data-canvas-context-item="'+label+'"]');
  if(!b) return {ok:false, why:'no such item'};
  b.click(); return {ok:true, text:(b.textContent||'').trim()};
}"""

UNDO_ISH = """()=>{const s=window.__libtv_store; if(!s) return null;
  const st=s.getState(); return {nodeCount:(st.canvases[0]||{}).nodes
      ? st.canvases.find(c=>c.id===st.activeCanvasId).nodes.length : null};}"""


def press_delete(pg):
    pg.keyboard.press("Delete")
    pg.wait_for_timeout(800)


def make_group_of_two(ctx):
    """UI 造一个带 2 个成员的组（选 2 个散节点按 G）。"""
    pg = ctx.new_page()
    pg.goto(BASE, wait_until="networkidle")
    pg.wait_for_selector(".react-flow__node", timeout=25000)
    pg.wait_for_timeout(1500)
    g0 = pg.evaluate(GRAPH)
    loose = [n["id"] for n in g0["nodes"] if n["type"] != "storyboard-group"][:2]
    pg.evaluate(SELECT, loose)
    pg.wait_for_timeout(300)
    pg.keyboard.press("g")
    pg.wait_for_timeout(900)
    g1 = pg.evaluate(GRAPH)
    host = None
    for n in g1["nodes"]:
        if n["type"] == "storyboard-group" and len(n["kids"]) == 2:
            host = n
            break
    return pg, g1, host, loose


def run_round(ctx, R):
    rec = {"round": R}
    pg = None
    try:
        # ── 臂 1：删掉一个带成员的组
        pg, g0, host, loose = make_group_of_two(ctx)
        rec["makeHost"] = {"host": host["id"] if host else None,
                           "kids": host["kids"] if host else None}
        if not host:
            rec["makeHost"]["FAILED"] = "没造出两成员的组，后续臂作废"
            return rec

        pg.evaluate(SELECT, [host["id"]])
        pg.wait_for_timeout(300)
        press_delete(pg)
        g1 = pg.evaluate(GRAPH)
        alive = {n["id"] for n in g1["nodes"]}
        rec["deleteGroupWithMembers"] = {
            "删掉的组": host["id"], "它原来的成员": host["kids"],
            "成员还在吗": {k: (k in alive) for k in host["kids"]},
            "节点数 Δ": g1["nodeCount"] - g0["nodeCount"],
            "组还在吗": host["id"] in alive,
            "★ 预期 Δ = -(1+成员数)": g1["nodeCount"] - g0["nodeCount"]
                                       == -(1 + len(host["kids"])),
            "★ 成员被连坐": all(k not in alive for k in host["kids"])}
        # 阳性对照：撤销能不能把它们全撤回来
        pg.keyboard.press("Meta+z")
        pg.wait_for_timeout(900)
        g2 = pg.evaluate(GRAPH)
        alive2 = {n["id"] for n in g2["nodes"]}
        rec["deleteGroupWithMembers"]["undo"] = {
            "节点数": g2["nodeCount"],
            "组回来了": host["id"] in alive2,
            "★ 成员全回来了": all(k in alive2 for k in host["kids"]),
            "★ 能完全撤销": host["id"] in alive2
                            and all(k in alive2 for k in host["kids"])}

        # ── 臂 2：删掉最后一个成员 ⟹ 空组
        pg.close()
        pg, g0, host, _ = make_group_of_two(ctx)
        kid = host["kids"][0]
        pg.evaluate(SELECT, [kid])
        pg.wait_for_timeout(300)
        press_delete(pg)
        mid = pg.evaluate(GRAPH)
        host_mid = next((n for n in mid["nodes"] if n["id"] == host["id"]), None)
        rec["deleteLastMember_step1"] = {
            "删掉的成员": kid, "组还剩几个": len(host_mid["kids"]) if host_mid else None,
            "组框": [host_mid["w"], host_mid["h"]] if host_mid else None,
            "原来的框": [host["w"], host["h"]],
            "★ 框变了（贴合剩下的）":
                bool(host_mid) and [host_mid["w"], host_mid["h"]] != [host["w"], host["h"]],
            "★ 删一个成员真的生效了": kid not in {n["id"] for n in mid["nodes"]}}

        kid2 = host_mid["kids"][0] if host_mid and host_mid["kids"] else None
        if kid2:
            pg.evaluate(SELECT, [kid2])
            pg.wait_for_timeout(300)
            press_delete(pg)
            g3 = pg.evaluate(GRAPH)
            host_end = next((n for n in g3["nodes"] if n["id"] == host["id"]), None)
            rec["deleteLastMember"] = {
                "删掉的成员": kid2,
                "空组还在吗": host_end is not None,
                "空组框": [host_end["w"], host_end["h"]] if host_end else None,
                "一步之前的框": [host_mid["w"], host_mid["h"]] if host_mid else None,
                "★ 框没变（沿用还剩一个时的）":
                    bool(host_end) and bool(host_mid)
                    and [host_end["w"], host_end["h"]]
                        == [host_mid["w"], host_mid["h"]],
                "边数": g3["edgeCount"],
                "DOM": ev(pg, GROUP_DOM, host["id"]),
                "★ 节点数 Δ（相对一步之前）":
                    g3["nodeCount"] - mid["nodeCount"]}

            # ── 臂 3：空组能不能被清掉
            pg.evaluate(SELECT, [host["id"]])
            pg.wait_for_timeout(300)
            press_delete(pg)
            g4 = pg.evaluate(GRAPH)
            rec["cleanupEmptyGroup"] = {
                "按 Delete 后节点数": g4["nodeCount"],
                "空组还在吗": host["id"] in {n["id"] for n in g4["nodes"]},
                "★ 删得掉": host["id"] not in {n["id"] for n in g4["nodes"]}}
            pg.keyboard.press("Meta+z")
            pg.wait_for_timeout(800)

            # 空组 + Shift+G（取消分组）⟹ 静默？
            pg.evaluate(SELECT, [host["id"]])
            pg.wait_for_timeout(400)
            before_sg = pg.evaluate(GRAPH)
            pg.keyboard.press("Shift+G")
            pg.wait_for_timeout(900)
            after_sg = pg.evaluate(GRAPH)
            rec["emptyGroupUngroup"] = {
                "节点数 Δ": after_sg["nodeCount"] - before_sg["nodeCount"],
                "空组还在吗": host["id"] in {n["id"] for n in after_sg["nodes"]},
                "★ 取消分组没作用": after_sg["nodeCount"] == before_sg["nodeCount"]
                                 and host["id"] in {n["id"] for n in after_sg["nodes"]}}

            # 右键菜单里有没有删除项、能不能删
            dom = ev(pg, GROUP_DOM, host["id"])
            box = ev(pg, """(gid)=>{const el=document.querySelector('[data-id="'+gid+'"]');
                if(!el) return null; const r=el.getBoundingClientRect();
                return {x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2)};}""",
                      host["id"])
            menu = None
            if box and box.get("x"):
                ev(pg, OPEN_MENU, [box["x"], box["y"]])
                pg.wait_for_timeout(600)
                menu = ev(pg, MENU_ITEMS)
                rec["contextMenuOnEmptyGroup"] = {"menuItems": menu,
                                                   "groupDom": dom}
    finally:
        if pg:
            pg.close()
    return rec


def main():
    out_path = pathlib.Path(sys.argv[1])
    rounds = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        try:
            for R in range(2):
                ctx = br.new_context(viewport={"width": 1440, "height": 1000})
                try:
                    rounds.append(run_round(ctx, R))
                finally:
                    ctx.close()
        finally:
            br.close()
    out = {"batch": 808, "base": BASE, "rounds": rounds}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    for r in rounds:
        a = r.get("deleteGroupWithMembers") or {}
        b = r.get("deleteLastMember") or {}
        c = r.get("cleanupEmptyGroup") or {}
        print("round %s ｜ 删带成员的组 Δ=%s 连坐=%s 能撤销=%s ｜ 空组框=%s handle=%s ｜ 删得掉=%s"
              % (r["round"], a.get("节点数 Δ"), a.get("★ 成员被连坐"),
                 (a.get("undo") or {}).get("★ 能完全撤销"),
                 b.get("空组框"), (b.get("DOM") or {}).get("handleCount"),
                 c.get("★ 删得掉")))
    print("wrote %s" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())