#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 794 探针 —— 删掉一个成员之后，分组框**收不收拢**

## 起点：793 留下的三个未验路径之一

793 把分组框跟随挂在 `routeReactFlowChanges` 的**唯一收口**上，于是拖拽与
尺寸变更都会跟随。但 `removeSelectedNodes`（`canvasStore.ts:3361`）是
**另一个写点**、不走那个收口 ⟹ **删成员后框不会收拢**。

★ 这不是 793 引入的：修之前框**根本**不动，删成员当然也不动。
793 修好了「成员移动」，「成员减少」这一半还在。

## ★ 为什么不能直接用种子的组来测

种子里那个组**只有 1 个成员** ⟹ 删掉它就变成 0 成员 ⟹ 而 793 的
边界 1 明确「**0 成员的组不动**」（那是 757 待拍板 ②，源站未采样）。
⟹ 要测「收拢」必须先造一个**两成员**的组。

## 三条臂

| 臂 | 动作 | 作用 |
| --- | --- | --- |
| ★ 处理臂 | 组两个散节点 → 删掉其中一个 | 就是不收拢的那条 |
| ★ 撤销臂 | 同上 → `Cmd+Z` | 撤销能不能把**框**也带回来（756 的教训：唯一出路是撤销） |
| ★ 前置对照 | 组两个散节点，**什么都不做** | 保证「造组」这一步本身是对的，且修复没打扰它 |

## 读数

框的 store 几何 + DOM rect + 每个成员的绝对位置；「成员是否还在框里」用
**DOM rect** 判定（pre/post 同页同 zoom，zoom 自己约掉）。

★ 另记 `past`（撤销栈深度）——撤销臂要靠它确认「撤销栈里确实有东西」。
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
    "liblib-canvas-batch794-2026-10-01/raw/vb794a-%s.json" % PHASE)

#: ★ 造一个**两成员**的组：选两个散节点 → 真的调 `groupSelectedNodes`
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

#: ★ 读框几何 + 成员绝对位置 + 「在不在框里」（DOM rect 判定）
MEASURE = """(gid)=>{
  const s=window.__libtv_store.getState();
  const cv=s.canvases.find(c=>c.id===s.activeCanvasId)||s.canvases[0];
  const byId=new Map(cv.nodes.map(n=>[n.id,n]));
  const abs=(n)=>{let x=n.position.x,y=n.position.y,p=n.parentId;
    const seen=new Set([n.id]);
    while(p&&!seen.has(p)){seen.add(p);const q=byId.get(p);
      if(!q)break;x+=q.position.x;y+=q.position.y;p=q.parentId;}
    return {x:Math.round(x),y:Math.round(y)};};
  const R=(r)=>({t:Math.round(r.top),l:Math.round(r.left),
    w:Math.round(r.width),h:Math.round(r.height),
    b:Math.round(r.bottom),r:Math.round(r.right)});
  const el=document.querySelector('.react-flow__node-storyboard-group[data-id="'+gid+'"]');
  const g=byId.get(gid);
  const gr=el?R(el.getBoundingClientRect()):null;
  const kids=cv.nodes.filter(n=>n.parentId===gid);
  return {past:(s.historyByCanvas&&s.historyByCanvas[s.activeCanvasId]
      ? (s.historyByCanvas[s.activeCanvasId].past||[]).length : -1),
    groupExists:!!g,
    groupStore:g?{pos:{x:g.position.x,y:g.position.y},
      w:g.width,h:g.height}:null,
    groupDom:gr,
    memberCount:kids.length,
    members:kids.map(k=>({id:k.id, abs:abs(k), w:k.width, h:k.height,
      inside: !!(gr && (()=>{const ke=document.querySelector(
        '.react-flow__node[data-id="'+k.id+'"]');
        if(!ke) return false; const kr=R(ke.getBoundingClientRect());
        return kr.l>=gr.l&&kr.t>=gr.t&&kr.r<=gr.r&&kr.b<=gr.b;})())}))};}"""


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


def arm_group_two_delete_one(pg):
    """★ 处理臂：组两个 → 删一个 ⟹ 框该收拢。"""
    r, err = make_pair(pg)
    if err:
        return {"arm": "groupTwoDeleteOne", "FAILED": err}
    gid = r["gid"]
    before = pg.evaluate(MEASURE, gid)
    victim = r["memberIds"][0]
    # ★ 选区用 store 摆，命令走**真实 Delete 键**
    pg.evaluate("""(id)=>window.__libtv_store.getState().selectNodes([id]);""", victim)
    pg.keyboard.press("Delete")
    pg.wait_for_timeout(500)
    after = pg.evaluate(MEASURE, gid)
    return {"arm": "groupTwoDeleteOne", "gid": gid,
            "victim": victim, "survivor": r["memberIds"][1:],
            "before": before, "after": after}


def arm_group_two_delete_one_undo(pg):
    """★ 撤销臂：删一个 → `Cmd+Z` ⟹ 成员与**框**都要回来。"""
    r, err = make_pair(pg)
    if err:
        return {"arm": "groupTwoDeleteOneUndo", "FAILED": err}
    gid = r["gid"]
    before = pg.evaluate(MEASURE, gid)
    pg.evaluate("""(id)=>window.__libtv_store.getState().selectNodes([id]);""",
                r["memberIds"][0])
    pg.keyboard.press("Delete")
    pg.wait_for_timeout(450)
    mid = pg.evaluate(MEASURE, gid)
    pg.keyboard.press("Meta+z")
    pg.wait_for_timeout(500)
    after = pg.evaluate(MEASURE, gid)
    return {"arm": "groupTwoDeleteOneUndo", "gid": gid,
            "victim": r["memberIds"][0],
            "before": before, "afterDelete": mid, "after": after}


def arm_group_two_no_delete(pg):
    """★ 前置对照：组两个，**什么都不做** ⟹ 框必须就是两成员的贴合值。"""
    r, err = make_pair(pg)
    if err:
        return {"arm": "groupTwoNoDelete", "FAILED": err}
    pg.wait_for_timeout(400)
    m = pg.evaluate(MEASURE, r["gid"])
    return {"arm": "groupTwoNoDelete", "gid": r["gid"],
            "memberIds": r["memberIds"], "state": m}


ARMS = [("groupTwoDeleteOne", arm_group_two_delete_one),
        ("groupTwoDeleteOneUndo", arm_group_two_delete_one_undo),
        ("groupTwoNoDelete", arm_group_two_no_delete)]


def fmt(cell):
    if cell.get("FAILED"):
        return "FAILED:%s" % cell["FAILED"]
    if cell["arm"] == "groupTwoNoDelete":
        m = cell["state"]
        g = m["groupStore"]
        return ("成员=%d 组 (%s,%s) %sx%s 在框内=%s past=%d"
                % (m["memberCount"], round(g["pos"]["x"]), round(g["pos"]["y"]),
                   round(g["w"]), round(g["h"]),
                   [x["inside"] for x in m["members"]], m["past"]))
    b, a = cell["before"], cell["after"]
    gb, ga = b["groupStore"], a["groupStore"]
    return ("成员 %d→%d ｜ 组 (%s,%s)%sx%s → (%s,%s)%sx%s ｜ 在框内 %s→%s ｜ past %d→%d"
            % (b["memberCount"], a["memberCount"],
               round(gb["pos"]["x"]), round(gb["pos"]["y"]),
               round(gb["w"]), round(gb["h"]),
               round(ga["pos"]["x"]), round(ga["pos"]["y"]),
               round(ga["w"]), round(ga["h"]),
               [x["inside"] for x in b["members"]],
               [x["inside"] for x in a["members"]],
               b["past"], a["past"]))


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
                print("  r%d %-26s %s" % (rd + 1, name, fmt(cell)), flush=True)
            rounds.append({"round": rd + 1, "rows": rows})
        b.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"batch": 794, "phase": PHASE, "rounds": rounds},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
