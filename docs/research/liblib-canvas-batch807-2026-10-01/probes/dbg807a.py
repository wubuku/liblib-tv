#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 807 探针 a：`groupSelectedNodes` —— 几何证据 + 那个「静默无操作」

## 为什么读源码不算数

802 的普查把 `groupSelectedNodes` 列为风险最高的一档（会建组、碰 `parentId`），
读源码看 `:3546-3548` 的
`position: absolutePositions.get(node.id) - groupNode.position.x`
**是正确的**。但 794 留过一条硬规矩：只有静态证据时，报告**不许**说「验过了」。

## 三条不变量（全部只认**绝对几何**，不预设 `position` 存绝对还是相对）

- **N1 不该跳的东西没跳**：被组合的每个成员，组合**前后绝对位置逐位相同**。
  （用户眼里「组合」只是换个框，不该让里面的东西挪窝。）
- **N2 成员在框内**：新组的**绝对**框包含所有被组合成员的绝对矩形。
  （793 立的不变量，嵌套下是 799 的判据。）
- ★★ **N3 操作要么生效、要么有反馈**：按 `G` 之后，要么节点集合**真的**变了，
  要么页面上**出现**了可见反馈（状态行 / toast / 任何 `[data-*]` 的变化）。
  ⟹ 这条是 **792 的遗留**（「选中里有分组时用户得不到任何告知」）的判据。

## 三条臂

| 臂 | 选什么 | 为什么值得问 |
| --- | --- | --- |
| `withHostMember` | 宿主组的**一个成员** + 一个散节点 | 成员被拽进新组，宿主组失一个成员要收缩 ⟹ 会不会跳？宿主组变不变空？ |
| `twoHostMembers` | 宿主组的**两个成员** | 同上，但宿主组会**变空** ⟹ 793 的空组问题被顺带碰到 |
| `groupPlusOne` | **一个组** + 一个散节点 | ★ `children` 过滤掉组之后只剩 1 个 ⟹ `children.length < 2` 静默 return ⟹ N3 该红 |

★ 前两条必须**先在 UI 上造出宿主组**（选 2 个散节点按 `G`），不能注入 ——
792 那条修法的前提就是「UI 造得出组」，注入会绕过这条前提。
"""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"

# ★★ `selectElements` 收的是**对象** `{nodeIds, edgeIds}`（`canvasStore.ts:392`），
#   不是裸数组。第一版传了裸数组 ⟹ `nodeIds` 是 undefined ⟹ 选区一直是空 ⟹
#   按 `G` 当然什么也不发生。★ 而「按 G 没反应」看起来**太像**一个真实的
#   「静默无操作」缺陷（792 的遗留），差点被我当成结论记下来。
SELECT = r"""(ids)=>{
  const s=window.__libtv_store; if(!s) return {ok:false};
  s.getState().selectElements({nodeIds: ids, edgeIds: []});
  const snap = s.getState().getSelectionSnapshot();
  return {ok:true, ids, selectedNodeIds: s.getState().selectedNodeIds,
          snapshotNodeIds: (snap && snap.nodeIds) || []};
}"""

# ★ 绝对位置独立重算（起点是 position，沿 parentId 链求和）
GRAPH = r"""()=>{
  const s=window.__libtv_store; if(!s) return null;
  const st=s.getState();
  const cur=st.canvases.find(c=>c.id===st.activeCanvasId)||st.canvases[0];
  const idx={}; cur.nodes.forEach(n=>{idx[n.id]=n;});
  const abs=(nid)=>{
    let n=idx[nid]; if(!n) return null;
    let x=n.position.x, y=n.position.y, pid=n.parentId, hops=0;
    const seen={}; seen[nid]=1;
    while(pid && idx[pid] && !seen[pid] && hops<32){
      seen[pid]=1; hops++;
      x+=idx[pid].position.x; y+=idx[pid].position.y;
      pid=idx[pid].parentId;
    }
    return {x,y,depth:hops};
  };
  const dim=(n)=>({w:(n.width ?? Number(n.style&&n.style.width))||350,
                   h:(n.height ?? Number(n.style&&n.style.height))||180});
  const nodes=cur.nodes.map(n=>{
    const a=abs(n.id)||{x:0,y:0,depth:0}; const d=dim(n);
    return {id:n.id, type:n.type, parentId:n.parentId||null,
            pos:{x:n.position.x,y:n.position.y},
            abs:a, w:d.w, h:d.h,
            kids: cur.nodes.filter(k=>k.parentId===n.id).map(k=>k.id)};
  });
  return {canvasId:cur.id, nodeCount:cur.nodes.length,
          selectedNodeIds: st.selectedNodeIds||[],
          nodes};
}"""

# 页面上**所有** [data-*] 的快照，用来判断「有没有出现可见反馈」
FEEDBACK = r"""()=>{
  const snap={};
  document.querySelectorAll('*').forEach(el=>{
    for(const a of el.attributes){
      if(!a.name.startsWith('data-')) continue;
      const k=a.name+'='+a.value;
      snap[k]=(snap[k]||0)+1;
    }
  });
  const status=document.body.innerText.replace(/\s+/g,' ').trim().slice(0,600);
  return {keys:Object.keys(snap).sort(), snap, status};
}"""

GROUPS = r"""()=>{
  const s=window.__libtv_store; if(!s) return null;
  const st=s.getState();
  const cur=st.canvases.find(c=>c.id===st.activeCanvasId)||st.canvases[0];
  return cur.nodes.filter(n=>n.type==='storyboard-group').map(n=>({
     id:n.id, parentId:n.parentId||null,
     kids: cur.nodes.filter(k=>k.parentId===n.id).map(k=>k.id)}));
}"""


def press_g(pg):
    pg.keyboard.press("g")
    pg.wait_for_timeout(900)


def loose_ids(g, n=8):
    return [x["id"] for x in g["nodes"] if x["type"] != "storyboard-group"][:n]


def run_round(ctx, R):
    rec = {"round": R}
    pg = ctx.new_page()
    try:
        pg.goto(BASE, wait_until="networkidle")
        pg.wait_for_selector(".react-flow__node", timeout=25000)
        pg.wait_for_timeout(1500)

        # ── 先在 UI 上造一个宿主组：选 2 个散节点按 G
        g0 = pg.evaluate(GRAPH)
        pool = loose_ids(g0)
        pg.evaluate(SELECT, pool[:2])
        pg.wait_for_timeout(400)
        press_g(pg)
        after_make = pg.evaluate(GRAPH)
        groups = pg.evaluate(GROUPS)
        host = None
        for grp in groups:
            if len(grp["kids"]) == 2:
                host = grp
                break
        rec["makeHost"] = {"picked": pool[:2],
                           "groupsBefore": len([x for x in g0["nodes"]
                                                if x["type"] == "storyboard-group"]),
                           "groupsAfter": len(groups),
                           "host": host}
        if not host:
            rec["makeHost"]["FAILED"] = "★ 没造出两成员的宿主组，后续臂全部作废"
            return rec

        idx = {n["id"]: n for n in after_make["nodes"]}

        # ── 臂 1：宿主组的一个成员 + 一个散节点
        member = host["kids"][0]
        other = next((i for i in pool[2:] if i in idx and not idx[i]["parentId"]),
                     None)
        if other:
            before = pg.evaluate(GRAPH)
            fb_before = pg.evaluate(FEEDBACK)
            pg.evaluate(SELECT, [member, other])
            pg.wait_for_timeout(400)
            press_g(pg)
            after = pg.evaluate(GRAPH)
            fb_after = pg.evaluate(FEEDBACK)
            rec["withHostMember"] = {
                "selected": [member, other],
                "beforeAbs": {i: (idx[i]["abs"], idx[i]["w"], idx[i]["h"])
                              for i in (member, other)},
                "beforeHost": next((n for n in before["nodes"] if n["id"] == host["id"]),
                                   None),
                "afterNodes": after["nodes"],
                "afterHost": next((n for n in after["nodes"] if n["id"] == host["id"]),
                                  None),
                "nodeCountDelta": after["nodeCount"] - before["nodeCount"],
                "newFeedbackKeys": sorted(set(fb_after["keys"])
                                          - set(fb_before["keys"])),
                "statusChanged": fb_before["status"] != fb_after["status"],
                "statusAfter": fb_after["status"][:220]}

        # ── 臂 2：宿主组的两个成员（宿主组会变空）
        after1 = pg.evaluate(GRAPH)
        idx1 = {n["id"]: n for n in after1["nodes"]}
        host_now = next((n for n in after1["nodes"]
                         if len(n["kids"]) >= 1), None)
        if host_now and len(host_now["kids"]) >= 2:
            kids = host_now["kids"][:2]
            before = pg.evaluate(GRAPH)
            idxb = {n["id"]: n for n in before["nodes"]}
            pg.evaluate(SELECT, kids)
            pg.wait_for_timeout(400)
            press_g(pg)
            after = pg.evaluate(GRAPH)
            rec["twoHostMembers"] = {
                "host": host_now["id"], "selected": kids,
                "beforeAbs": {i: (idxb[i]["abs"], idxb[i]["w"], idxb[i]["h"])
                              for i in kids},
                "afterNodes": after["nodes"],
                "nodeCountDelta": after["nodeCount"] - before["nodeCount"],
                "hostAfter": next((n for n in after["nodes"]
                                   if n["id"] == host_now["id"]), None)}

        # ── 臂 3 ★：一个组 + 一个散节点 ⟹ children<2 ⟹ 静默 return？
        after2 = pg.evaluate(GRAPH)
        any_group = next((n for n in after2["nodes"]
                          if n["type"] == "storyboard-group"), None)
        # ★ 先算出「不是那个组的 id」，再筛 —— 写成生成器里的条件表达式
        #   会被 Python 的 `if ... else` 结合律坑到（第一版就 SyntaxError）
        gid = any_group["id"] if any_group else None
        loose = None
        for n in after2["nodes"]:
            if n["type"] == "storyboard-group" or n["id"] == gid:
                continue
            loose = n
            break
        if any_group and loose:
            before = pg.evaluate(GRAPH)
            fb_before = pg.evaluate(FEEDBACK)
            pg.evaluate(SELECT, [any_group["id"], loose["id"]])
            pg.wait_for_timeout(400)
            press_g(pg)
            after = pg.evaluate(GRAPH)
            fb_after = pg.evaluate(FEEDBACK)
            rec["groupPlusOne"] = {
                "selected": [any_group["id"], loose["id"]],
                "nodeCountDelta": after["nodeCount"] - before["nodeCount"],
                "selectedAfter": after["selectedNodeIds"],
                "newFeedbackKeys": sorted(set(fb_after["keys"])
                                          - set(fb_before["keys"])),
                "statusChanged": fb_before["status"] != fb_after["status"],
                "statusAfter": fb_after["status"][:220]}
    finally:
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
    out = {"batch": 807, "base": BASE, "rounds": rounds}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    for r in rounds:
        mh = r.get("makeHost") or {}
        print("round %s ｜ 宿主组=%s ｜ 臂1 Δ节点=%s ｜ 臂3 Δ节点=%s ｜ 臂3 状态变了=%s"
              % (r["round"], (mh.get("host") or {}).get("id"),
                 (r.get("withHostMember") or {}).get("nodeCountDelta"),
                 (r.get("groupPlusOne") or {}).get("nodeCountDelta"),
                 (r.get("groupPlusOne") or {}).get("statusChanged")))
    print("wrote %s" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())