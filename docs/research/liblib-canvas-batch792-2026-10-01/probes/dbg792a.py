#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 792 探针 —— 「组合」(G) 跨分组多选时**静默掏空已有分组**

## 承重事实（batch 756，本批要**重新确认**而不是直接引用）

`groupSelectedNodes` 的 `children` 过滤把 `storyboard-group` **排除**：

    src/store/canvasStore.ts:3266-3268
      node.type !== "storyboard-group"

但 `nextNodes` 的 re-parent 条件是 `absolutePositions.has(node.id)`，
而 `absolutePositions` 由 `children` 生成 ⟹ **只**排除分组自己、
**不**排除分组的成员。成员也在选区里 ⟹ 被无条件改写成**新组**的子节点
⟹ 旧分组归零、退化成空壳，界面上只是「组合成功」。

★ 756 的警告本批照办：**先记基线**（哪些组本来就空、哪些本来有成员），
否则会把「本来就空」读成「被掏空」。

## 三条臂

| 臂 | 动作 | 作用 |
| --- | --- | --- |
| ★ 处理臂 | 框选全部 → `G` | 就是坏掉的那条 |
| ★ 阳性对照一 | 选中「组 + 它自己的成员」→ `G` | 756 记录的是**零变化** |
| ★ 阳性对照二 | 选中**两个散节点** → `G` | 正常组合必须**仍然能成** |

★ 没有阳性对照二，一个「让 `G` 什么都不做」的修复也能全绿。

## 每一步都读前置条件

每条臂在按 `G` 之前都读一次 `selectedNodeIds.length` 与「选中的里有没有分组」，
按完再读组的 children ⟹ 「选区里到底有什么」是被**读**出来的，不靠假设。

## 格数

3 臂 × 2 轮 × {pre, post} = 每次运行 6 格
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
    "liblib-canvas-batch792-2026-10-01/raw/vb792a-%s.json" % PHASE)

#: ★ 读组结构：哪些组、成员是谁、成员现在挂在谁下面
GROUPS = """()=>{
  const s=window.__libtv_store.getState();
  const cv=s.canvases.find(c=>c.id===s.activeCanvasId)||s.canvases[0];
  const nodes=cv.nodes;
  const kids=(gid)=>nodes.filter(n=>n.parentId===gid).map(n=>n.id);
  return {canvasId:cv.id, nodeCount:nodes.length,
    groups:nodes.filter(n=>n.type==='storyboard-group').map(g=>
      ({id:g.id, title:(g.data&&g.data.title)||'', kids:kids(g.id),
       groupKind:(g.data&&g.data.groupKind)||''})),
    loose:nodes.filter(n=>n.type!=='storyboard-group'&&!n.parentId)
      .map(n=>({id:n.id, type:n.type})),
    memberOf:Object.fromEntries(nodes.filter(n=>n.parentId)
      .map(n=>[n.id,n.parentId])),
    selected:s.selectedNodeIds.slice()};}"""

PANE_START = """()=>{
  const pane=document.querySelector('.react-flow__pane');
  if(!pane) return {FAILED:'没有 pane'};
  const r=pane.getBoundingClientRect();
  // ★ 起点要落在 pane **自己**上、且不在任何节点里
  for(let f=0.02; f<=0.30; f+=0.02){
    const x=Math.round(r.left+r.width*f), y=Math.round(r.top+r.height*0.03);
    if(x<2||y<2) continue;
    const e=document.elementFromPoint(x,y);
    if(e && e.classList && e.classList.contains('react-flow__pane')
       && !e.closest('.react-flow__node'))
      return {pt:[x,y], end:[Math.round(innerWidth-8), Math.round(innerHeight-8)]};
  }
  return {FAILED:'pane 左上角找不到空白起点'};}"""

TOAST_PROBE = """()=>{
  const sels=['[role="alert"]','[role="status"]','[data-toast]',
    '[data-canvas-toast]','[class*="toast"]','[class*="Toast"]'];
  return sels.reduce((n,s)=>n+document.querySelectorAll(s).length,0);}"""

SEL_READ = "()=>window.__libtv_store.getState().selectedNodeIds.length"


def boot(pg):
    pg.goto(A.BASE, wait_until="domcontentloaded")
    pg.evaluate(A.CLEAR_LS, A.LS_KEY)
    pg.set_viewport_size({"width": 1440, "height": 1000})
    pg.goto(A.BASE, wait_until="networkidle")
    pg.wait_for_selector(".react-flow__node", timeout=25000)
    pg.wait_for_timeout(1300)
    pg.keyboard.press("Meta+0")
    pg.wait_for_timeout(600)


def click_node(pg, node_id, shift=False):
    """★ 真点某个节点（`shift` 为真就是**加选**），并验它真的被选中。"""
    r = pg.evaluate("""(id)=>{const n=document.querySelector(
        '.react-flow__node[data-id="'+id+'"]');
      if(!n) return {missing:true};
      const b=n.getBoundingClientRect();
      return {pt:[Math.round(b.left+b.width/2), Math.round(b.top+b.height/2)]};}""",
                    node_id)
    if not r.get("pt"):
        return False
    if shift:
        pg.keyboard.down("Shift")
    pg.mouse.click(r["pt"][0], r["pt"][1])
    if shift:
        pg.keyboard.up("Shift")
    pg.wait_for_timeout(300)
    return True


SELECT = """(ids)=>{window.__libtv_store.getState().selectNodes(ids);
  return window.__libtv_store.getState().selectedNodeIds.slice();}"""


def pick(pg, ids):
    """★ 用 store 摆好选区，并**读回**它真的成立了。"""
    return pg.evaluate(SELECT, ids)


def arm_select_all_then_g(pg):
    """★ 处理臂：选中**全部**节点 → 真实按 `g`。

    ★ 选区是**用 store 摆的**，不是框选出来的：`page.tsx:1574` 是
      `selectionOnDrag={false}` ⟹ 拖拽**根本不产生框选**
      （第一版探针照 756 的手势拖，读到选区 0，三条臂全是空读数）。
      缺陷在 `groupSelectedNodes` 本身 ⟹ 用 store 摆选区才是对准靶子；
      命令仍然走**真实键盘 `g`**。
    """
    base = pg.evaluate(GROUPS)
    allids = [n for g in base["groups"] for n in g["kids"]]
    allids += [g["id"] for g in base["groups"]]
    allids += [x["id"] for x in base["loose"]]
    sel = pick(pg, allids)
    before = pg.evaluate(GROUPS)
    toast = pg.evaluate(TOAST_PROBE)
    pg.keyboard.press("g")
    pg.wait_for_timeout(500)
    after = pg.evaluate(GROUPS)
    return {"arm": "selectAllThenG", "baseline": base,
            "picked": len(allids), "selectedBeforeG": len(sel),
            "selectedHasGroup": any(g["id"] in sel
                                    for g in before["groups"]),
            "toastCount": toast, "before": before, "after": after}


def arm_group_plus_member(pg):
    """★ 阳性对照一：选中「组 + 它自己的成员」→ `g`（756 记录是零变化）。"""
    base = pg.evaluate(GROUPS)
    g = next((x for x in base["groups"] if x["kids"]), None)
    if not g:
        return {"arm": "groupPlusMember", "FAILED": "没有带成员的组",
                "baseline": base}
    sel = pick(pg, [g["id"], g["kids"][0]])
    before = pg.evaluate(GROUPS)
    pg.keyboard.press("g")
    pg.wait_for_timeout(500)
    after = pg.evaluate(GROUPS)
    return {"arm": "groupPlusMember", "groupId": g["id"],
            "memberId": g["kids"][0],
            "selectedBeforeG": len(sel),
            "before": before, "after": after}


def arm_two_loose(pg):
    """★ 阳性对照二：选中**两个散节点** → `g`（正常组合必须仍然能成）。"""
    base = pg.evaluate(GROUPS)
    loose = list(base["loose"])
    if len(loose) < 2:
        return {"arm": "twoLoose", "FAILED": "散节点不足两个",
                "baseline": base}
    sel = pick(pg, [loose[0]["id"], loose[1]["id"]])
    before = pg.evaluate(GROUPS)
    pg.keyboard.press("g")
    pg.wait_for_timeout(500)
    after = pg.evaluate(GROUPS)
    new_groups = [x for x in after["groups"] if x["id"] not in
                  {g["id"] for g in before["groups"]}]
    return {"arm": "twoLoose", "picked": [loose[0]["id"], loose[1]["id"]],
            "selectedBeforeG": len(sel),
            "newGroups": new_groups,
            "nodeDelta": after["nodeCount"] - before["nodeCount"],
            "before": before, "after": after}


ARMS = [("selectAllThenG", arm_select_all_then_g),
        ("groupPlusMember", arm_group_plus_member),
        ("twoLoose", arm_two_loose)]


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
    OUT.write_text(json.dumps({"batch": 792, "phase": PHASE, "rounds": rounds},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote %s" % OUT)


def fmt(cell):
    if cell.get("FAILED"):
        return "FAILED:%s" % cell["FAILED"]
    if cell["arm"] == "twoLoose":
        ng = cell.get("newGroups") or []
        return "节点Δ=%d 新组=%d children=%s" % (
            cell.get("nodeDelta", -1), len(ng),
            [len(g["kids"]) for g in ng])
    b4, af = cell["before"], cell["after"]
    lost = []
    for g in b4["groups"]:
        kb = len(g["kids"])
        ga = next((x for x in af["groups"] if x["id"] == g["id"]), None)
        ka = len(ga["kids"]) if ga else None
        if ka is not None and ka < kb:
            lost.append("%s %d→%d" % (g["id"][:10], kb, ka))
    newg = [x for x in af["groups"]
            if x["id"] not in {g["id"] for g in b4["groups"]}]
    return ("选区=%d 成员被抢=%s 新组=%d children=%s toast=%s"
            % (cell.get("selectedBeforeG", -1), lost or "无", len(newg),
               [len(g["kids"]) for g in newg], cell.get("toastCount", "-")))


if __name__ == "__main__":
    main()
