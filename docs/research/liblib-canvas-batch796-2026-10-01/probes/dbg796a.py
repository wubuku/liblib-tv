#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 796 探针 —— 组的几何变化是否被正确纳入**撤销**

## 起点：793 遗留里的**最后一条**

793 的三条未验路径，到 795 已经做完两条（拖拽跟随 = 793 本体、
删成员收拢 = 794、键盘移动 = 795）。剩下这条是：

> 「组的几何变化是否被 `onNodeDragStop` 正确纳入**撤销**」

## ★ 为什么这条不能靠读源码下结论（源码里看着是对的）

`onNodeDragStop`（`page.tsx` 里那一段）的逻辑是：

- `onNodeDragStart` 拍 `dragHistorySnapshot.current = { snapshot: { nodes: currentCanvas.nodes, … } }`
  —— 拖动**开始前**的状态
- `onNodeDragStop` 里 `moved` 为真时
  `setStoreNodes(currentNodes, { recordHistory: true, historySnapshot: transaction.snapshot })`
  —— 提交**跟随后**的 `currentNodes`，历史里存**拖动前**的快照

⟹ 读起来自洽：撤销恢复拖动前的坐标，框自然回到原位。

★ **但有两处读源码看不出来的东西**：

1. `snapshot: { nodes: currentCanvas.nodes }` 是**引用**，不是深拷贝。若后续任何写入
   **原地改**了这个数组（而不是返回新数组），快照就被污染 ⟹ 撤销会回到一个
   「已经被改过」的世界。★ 这只能实测。
2. `moved` 的判据是「**被拖的那个 id**（或选区里的 id）位置变了」。
   ★ 框被 793 收口改动时，`moved` 根本不看框 ⟹ 若只拖了「位置没变的节点」，
   框却因为收口被重算了，历史里**可能什么都没有**。

## ★ 四条臂

| 臂 | 动作 | 判什么 |
| --- | --- | --- |
| ★ 撤销臂 | 拖子节点出框 → `Cmd+Z` | 成员**与框**是否都回到原位、`past` 是否退一格 |
| ★ 快照污染臂 | 拖子节点出框 → 读 `past` 里那条快照的**框坐标** | 快照里的框是**拖动前**的值吗（= 没被污染） |
| ★ 空拖臂 | 在组**原地**按下一个成员（零位移）松手 | `moved` 为假 ⟹ 撤销后必须**完全不变** |
| ★ 阳性对照 | `Cmd+Z` 本身有没有接线 | 与方向键/Delete 同一条 keydown 链路 |

★ 每条臂都用**真实拖拽**（沿四边细扫找「只属于组」的点）与**真实 Cmd+Z**，
不走 store 捷径——`onNodeDragStop` 只在真实拖拽时触发。

## 读数

组的 store 几何、成员的绝对位置、`past` 深度，以及 **`past` 最后一条快照里**
组的 pos/尺寸（用来判快照污染）。
"""
import json
import pathlib
import sys
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch774-2026-10-01" / "probes"))
import dbg774a as A  # noqa: E402

PHASE = sys.argv[1] if len(sys.argv) > 1 else "pre"
assert PHASE in ("pre", "post"), "★ 阶段只能是 pre / post，收到 %r" % PHASE

OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/research/"
    "liblib-canvas-batch796-2026-10-01/raw/vb796a-%s.json" % PHASE)

#: ★ 造一个**两成员**的组（与 793/794/795 同一套）
MAKE_PAIR_GROUP = """()=>{
  const st=window.__libtv_store.getState();
  const cv=st.canvases.find(c=>c.id===st.activeCanvasId)||st.canvases[0];
  const loose=cv.nodes.filter(n=>n.type!=='storyboard-group'&&!n.parentId)
    .slice(0,2).map(n=>n.id);
  if(loose.length<2) return {FAILED:'散节点不足两个'};
  window.__libtv_store.getState().selectNodes(loose);
  window.__libtv_store.getState().groupSelectedNodes(loose);
  const s2=window.__libtv_store.getState();
  const cv2=s2.canvases.find(c=>c.id===s2.activeCanvasId)||s2.canvases[0];
  const g=cv2.nodes.find(n=>n.type==='storyboard-group'
    && cv2.nodes.filter(m=>m.parentId===n.id).length>=2);
  if(!g) return {FAILED:'没造出两成员的组'};
  return {gid:g.id, memberIds:cv2.nodes.filter(m=>m.parentId===g.id)
    .map(m=>m.id)};}"""

#: ★ 读组几何 + 成员绝对位置 + past 深度 + **past 末条快照里的组几何**
#: ★★ 绝对位置**不取整**（第一版 `Math.round` 把亚像素掩盖了 ⟹
#:   框宽 `1173.3422818791946` 这个脏值在读数里看不出来是怎么来的）。
MEASURE = """(gid)=>{
  const s=window.__libtv_store.getState();
  const cv=s.canvases.find(c=>c.id===s.activeCanvasId)||s.canvases[0];
  const byId=new Map(cv.nodes.map(n=>[n.id,n]));
  const abs=(n)=>{let x=n.position.x,y=n.position.y,p=n.parentId;
    const seen=new Set([n.id]);
    while(p&&!seen.has(p)){seen.add(p);const q=byId.get(p);
      if(!q)break;x+=q.position.x;y+=q.position.y;p=q.parentId;}
    // ★ 不取整：脏值必须原样读出来
    return {x:x,y:y,roundX:Math.round(x),roundY:Math.round(y)};};
  const hist=(s.historyByCanvas&&s.historyByCanvas[s.activeCanvasId])||null;
  const past=(hist&&hist.past)||[];
  const g=byId.get(gid);
  const last=past.length?past[past.length-1]:null;
  const snapG=last&&last.nodes?last.nodes.find(n=>n.id===gid):null;
  return {past:past.length,
    groupStore:g?{pos:{x:g.position.x,y:g.position.y},
      w:g.width,h:g.height}:null,
    members:cv.nodes.filter(n=>n.parentId===gid)
      .map(m=>({id:m.id, abs:abs(m), w:m.width, h:m.height})),
    snapGroup: snapG?{pos:{x:snapG.position.x,y:snapG.position.y},
      w:snapG.width,h:snapG.height}:null};}"""

#: ★ 找一个**只属于组、不属于任何成员**的屏幕点（组 zIndex -1001，中心被盖住）
SCAN_GROUP = """(gid)=>{
  const el=document.querySelector(
    '.react-flow__node-storyboard-group[data-id=\"'+gid+'\"]');
  if(!el) return {FAILED:'组 DOM 不在'};
  const r=el.getBoundingClientRect();
  const cx=r.left+r.width/2, cy=r.top+r.height/2;
  for(const inset of [3,6,10,16,24,34]){
    for(const [x,y] of [[r.left+inset,cy],[r.right-inset,cy],
      [cx,r.top+inset],[cx,r.bottom-inset]]){
      const hit=document.elementFromPoint(Math.round(x),Math.round(y));
      if(hit&&hit.closest('.react-flow__node')
        &&hit.closest('.react-flow__node').getAttribute('data-id')===gid)
        return {x:Math.round(x), y:Math.round(y)};}
  }
  return {FAILED:'找不到只属于组的点'};}"""

#: ★ 找一个成员节点的**中心**（成员在组上面，直接可用）
SCAN_MEMBER = """(mid)=>{
  const el=document.querySelector('.react-flow__node[data-id=\"'+mid+'\"]');
  if(!el) return {FAILED:'成员 DOM 不在'};
  const r=el.getBoundingClientRect();
  return {x:Math.round(r.left+r.width/2), y:Math.round(r.top+r.height/2)};}"""


def boot(pg):
    pg.goto(A.BASE, wait_until="domcontentloaded")
    pg.evaluate(A.CLEAR_LS, A.LS_KEY)
    pg.set_viewport_size({"width": 1440, "height": 1000})
    pg.goto(A.BASE, wait_until="networkidle")
    pg.wait_for_selector(".react-flow__node", timeout=25000)
    pg.wait_for_timeout(1300)
    pg.keyboard.press("Meta+0")
    pg.wait_for_timeout(700)


def make_pair(pg):
    r = pg.evaluate(MAKE_PAIR_GROUP)
    if r.get("FAILED"):
        return None, r.get("FAILED")
    pg.wait_for_timeout(500)
    return r, None


def drag(pg, start, dx, dy, steps=12):
    """★ 真实拖拽：按下 → 分步移动 → 松手（`onNodeDragStop` 只在真实拖拽时触发）。"""
    pg.mouse.move(start["x"], start["y"])
    pg.mouse.down()
    for i in range(1, steps + 1):
        pg.mouse.move(start["x"] + dx * i // steps,
                      start["y"] + dy * i // steps)
        pg.wait_for_timeout(18)
    pg.wait_for_timeout(160)
    pg.mouse.up()
    pg.wait_for_timeout(550)


def arm_drag_then_undo(pg):
    """★ 撤销臂：拖子节点出框 → `Cmd+Z` ⟹ 成员与框都要回来。"""
    r, err = make_pair(pg)
    if err:
        return {"arm": "dragThenUndo", "FAILED": err}
    gid, kid = r["gid"], r["memberIds"][0]
    p = pg.evaluate(SCAN_MEMBER, kid)
    if p.get("FAILED"):
        return {"arm": "dragThenUndo", "FAILED": p["FAILED"]}
    before = pg.evaluate(MEASURE, gid)
    drag(pg, p, 320, 0)
    afterDrag = pg.evaluate(MEASURE, gid)
    pg.keyboard.press("Meta+z")
    pg.wait_for_timeout(650)
    after = pg.evaluate(MEASURE, gid)
    return {"arm": "dragThenUndo", "gid": gid, "kid": kid,
            "before": before, "afterDrag": afterDrag, "after": after}


def arm_snapshot_purity(pg):
    """★ 快照污染臂：`past` 末条快照里组的 pos/尺寸是否**仍是拖动前**的值。"""
    r, err = make_pair(pg)
    if err:
        return {"arm": "snapshotPurity", "FAILED": err}
    gid, kid = r["gid"], r["memberIds"][0]
    p = pg.evaluate(SCAN_MEMBER, kid)
    if p.get("FAILED"):
        return {"arm": "snapshotPurity", "FAILED": p["FAILED"]}
    before = pg.evaluate(MEASURE, gid)
    drag(pg, p, 320, 0)
    after = pg.evaluate(MEASURE, gid)
    return {"arm": "snapshotPurity", "gid": gid, "kid": kid,
            "before": before, "after": after}


def arm_noop_drag(pg):
    """★ 空拖臂：原地按下一个成员（**零位移**）松手 ⟹ `moved` 为假，不得记历史。"""
    r, err = make_pair(pg)
    if err:
        return {"arm": "noopDrag", "FAILED": err}
    gid, kid = r["gid"], r["memberIds"][0]
    p = pg.evaluate(SCAN_MEMBER, kid)
    if p.get("FAILED"):
        return {"arm": "noopDrag", "FAILED": p["FAILED"]}
    before = pg.evaluate(MEASURE, gid)
    drag(pg, p, 0, 0, steps=4)
    after = pg.evaluate(MEASURE, gid)
    return {"arm": "noopDrag", "gid": gid, "kid": kid,
            "before": before, "after": after}


def arm_positive_undo(pg):
    """★ 阳性对照：先造组（记一条历史）→ 立刻 `Cmd+Z` ⟹ 组必须消失。

    ★ 它证明「`Cmd+Z` 这条 keydown 链路真的接上了画布」⟹ 撤销臂的读数
    才不是因为「撤销键没反应」而误判。
    """
    r, err = make_pair(pg)
    if err:
        return {"arm": "positiveUndo", "FAILED": err}
    gid = r["gid"]
    before = pg.evaluate(MEASURE, gid)
    pg.keyboard.press("Meta+z")
    pg.wait_for_timeout(650)
    after = pg.evaluate(MEASURE, gid)
    return {"arm": "positiveUndo", "gid": gid,
            "before": before, "after": after}


ARMS = [("dragThenUndo", arm_drag_then_undo),
        ("snapshotPurity", arm_snapshot_purity),
        ("noopDrag", arm_noop_drag),
        ("positiveUndo", arm_positive_undo)]


def fmt(cell):
    if cell.get("FAILED"):
        return "FAILED:%s" % cell["FAILED"]
    b, a = cell.get("before"), cell.get("after")
    g = lambda m: ("(%s,%s)%sx%s" % (m["groupStore"]["pos"]["x"],
                                      m["groupStore"]["pos"]["y"],
                                      m["groupStore"]["w"], m["groupStore"]["h"])
                   if m and m.get("groupStore") else "无组")
    if cell["arm"] == "dragThenUndo":
        mid = cell.get("afterDrag")
        return ("组 %s → 拖后 %s → 撤销后 %s ｜ past %d→%d→%d"
                % (g(b), g(mid), g(a), b["past"], mid["past"], a["past"]))
    if cell["arm"] == "positiveUndo":
        return ("组 %s → 撤销后 %s ｜ past %d→%d" % (g(b), g(a),
                                                    b["past"], a["past"]))
    if cell["arm"] == "noopDrag":
        return ("组 %s → %s ｜ past %d→%d" % (g(b), g(a),
                                             b["past"], a["past"]))
    return ("组 %s → %s ｜ past %d→%d ｜ 快照里的组 %s"
            % (g(b), g(a), b["past"], a["past"],
               a.get("snapGroup") and "(%s,%s)%sx%s" % (
                   a["snapGroup"]["pos"]["x"], a["snapGroup"]["pos"]["y"],
                   a["snapGroup"]["w"], a["snapGroup"]["h"]) or "无"))


def main():
    rounds = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        for rd in range(2):
            rows = []
            for name, fn in ARMS:
                cell, tries = None, 0
                for t in range(3):
                    pg = b.new_page()
                    pg.set_default_timeout(15000)
                    tries = t + 1
                    try:
                        boot(pg)
                        cell = fn(pg)
                    except Exception as e:      # noqa: BLE001
                        cell = {"arm": name,
                                "FAILED": "%s: %s" % (type(e).__name__, e)}
                    finally:
                        try:
                            pg.close()
                        except Exception:       # noqa: BLE001
                            pass
                    if not cell.get("FAILED"):
                        break
                cell["tries"] = tries
                rows.append(cell)
                print("  r%d %-18s %s" % (rd + 1, name, fmt(cell)), flush=True)
            rounds.append({"round": rd + 1, "rows": rows})
        b.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"batch": 796, "phase": PHASE, "rounds": rounds},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
