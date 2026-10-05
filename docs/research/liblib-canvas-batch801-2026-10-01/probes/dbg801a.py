#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 801 探针 —— `duplicateGraphSelection`：复制出来的副本应该只是**平移**

## 起点

800 读了 `duplicateGraphSelection`（`canvasStore.ts:841`）的源码，逻辑**看起来是对的**：
父也被复制时保持 `position` 不变、只把 `parentId` 指向新 id（`:888`）；
父没被复制时提升为顶层、用**绝对位置 + 40**（`:891`）。

★ 但那只是**读源码**的结论。794 的教训（`removeNode` 那处只有静态证据、
不能写成「两处都验过了」）⟹ **没有行为证据就不算验过**。本批去测。

## ★ 判据：副本 = 原节点**整体平移 (40,40)**

用户视角的承诺是「复制一份、挪开一点」，所以判据只说这一句：

- **不变量 C1（平移）**：每个副本节点的**绝对**位置 = 其原节点的绝对位置 + (40,40)。
- **不变量 C2（结构）**：复制**组**时，副本与原的**父子关系逐条保持**；
  复制**组内一个成员**时，副本应当**脱离**该组、提升为顶层（这是**故意的**结构变化，
  按臂分开判，不与 C2 混成一条）。
- **不变量 C3（阳性）**：副本的 id 必须与原 id **全都不同**，且副本数 = 预期数。
  没有它，「什么都没复制」也会让 C1/C2 成立。

★ 判据只用**绝对位置**与**父子关系**，不预设实现怎么算偏移。

## ★ 三条臂

| 臂 | 复制什么 | 怎么触发 | 结构预期 |
| --- | --- | --- | --- |
| ★ 单层组 | 2 成员 + 它们的组 | UI：`G` 造组 → `Cmd+D` | 父子关系**保持** |
| ★ 嵌套整组 | 整个嵌套结构 | 注入 + store | 父子关系**保持**（逐层） |
| ★ 组内一个成员 | 只有成员 | 注入 + store | 副本**脱管**、提升为顶层 |

★ 第一条是**纯 UI 用户路径**（`page.tsx:1381` 的 `Cmd+D`），不需要注入。
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
    "liblib-canvas-batch801-2026-10-01/raw/vb801a-%s.json" % PHASE)

OFFSET = 40
OUTER, INNER = "g-outer", "g-inner"

MAKE_NESTED = """(ids)=>{
  const st=window.__libtv_store;
  const mk=(id,type,pos,extra)=>Object.assign({
    id:id,type:type,position:{x:pos[0],y:pos[1]},width:0,height:0,
    data:{},style:{},measured:{},selected:false,dragging:false},extra||{});
  // ★★ `data.tag` = 原节点 id：`duplicateGraphSelection` 复制时是
  //   `data: {...node.data, title: ...}` ⟹ 副本**继承**这个标记。
  //   这是**唯一可靠**的「副本 ↔ 源」配对方式：纯几何配对有歧义 ——
  //   副本 outer 落在 (240,190)，而原 inner 恰好也在 (240,190)
  //   （因为 `inner.position` 与复制偏移都是 (40,40)）⟹ 最近邻分不出来。
  const g=(id,pos,parentId,title)=>mk(id,'storyboard-group',pos,{
    parentId:parentId||undefined,width:10,height:10,
    style:{width:10,height:10,zIndex:-1001},zIndex:-1001,
    data:{title:title,variant:'image',tag:id}});
  const t=(id,pos,parentId)=>mk(id,'text',pos,{
    parentId:parentId||undefined,width:200,height:100,
    data:{tag:id}});
  st.getState().setNodes([
    g(ids.outer,[200,150],null,'外层'),
    g(ids.inner,[40,40],ids.outer,'内层'),
    t('n-m1',[40,40],ids.inner),
    t('n-m2',[440,40],ids.inner),
    t('n-loose',[40,440],ids.outer),
  ]);
  return {ok:true};}"""

MEASURE = """()=>{
  const S=window.__libtv_store.getState();
  const cv=S.canvases.find(c=>c.id===S.activeCanvasId)||S.canvases[0];
  const byId=new Map(cv.nodes.map(n=>[n.id,n]));
  const abs=(n)=>{let x=n.position.x,y=n.position.y,p=n.parentId;
    const seen=new Set([n.id]); let d=0;
    while(p&&!seen.has(p)&&d<32){seen.add(p);d+=1;
      const q=byId.get(p); if(!q)break; x+=q.position.x;y+=q.position.y;p=q.parentId;}
    return {x:x,y:y,depth:d};};
  return {nodes:cv.nodes.map(n=>{const a=abs(n);
      return {id:n.id, type:n.type, parentId:n.parentId||null,
        pos:{x:n.position.x,y:n.position.y},
        abs:{x:a.x,y:a.y,depth:a.depth}, w:n.width, h:n.height,
        tag:(n.data||{}).tag||null};})
    .sort((x,y)=>String(x.id)<String(y.id)?-1:1),
    total:cv.nodes.length};}"""


def boot(pg):
    pg.goto(A.BASE, wait_until="domcontentloaded", timeout=90000)
    pg.evaluate(A.CLEAR_LS, A.LS_KEY)
    pg.set_viewport_size({"width": 1440, "height": 1000})
    pg.goto(A.BASE, wait_until="networkidle", timeout=90000)
    pg.wait_for_selector(".react-flow__node", timeout=60000)
    pg.wait_for_timeout(1300)
    pg.keyboard.press("Meta+0")
    pg.wait_for_timeout(700)


def make_nested(pg):
    r = pg.evaluate(MAKE_NESTED, {"outer": OUTER, "inner": INNER})
    if r.get("FAILED"):
        return r.get("FAILED")
    pg.wait_for_timeout(900)
    return None


def copies(pg, want_count, label):
    """★ 注入 / 造组之后调复制，再读一次。返回 (before, after) 或 None。"""
    before = pg.evaluate(MEASURE)
    pg.evaluate("()=>window.__libtv_store.getState().duplicateSelectedNodes();")
    pg.wait_for_timeout(900)
    after = pg.evaluate(MEASURE)
    new_ids = [n["id"] for n in after["nodes"]
               if n["id"] not in {b["id"] for b in before["nodes"]}]
    if len(new_ids) != want_count:
        return None, ("%s：预期 %d 个副本，实得 %d 个"
                      % (label, want_count, len(new_ids)))
    return {"before": before, "after": after, "copyIds": new_ids}, None


def arm_copy_flat_group(pg):
    """★ 纯 UI：选 2 个散节点 `G` 造组，再 `Cmd+D` 复制。"""
    ids = pg.evaluate("""()=>{
      const S=window.__libtv_store.getState();
      const cv=S.canvases.find(c=>c.id===S.activeCanvasId)||S.canvases[0];
      return cv.nodes.filter(n=>n.type!=='storyboard-group'&&!n.parentId)
        .slice(0,2).map(n=>n.id);}""")
    if not ids or len(ids) < 2:
        return {"arm": "copyFlatGroup", "FAILED": "没有 2 个顶层散节点"}
    pre_groups = {n["id"] for n in pg.evaluate(MEASURE)["nodes"]
                  if n["type"] == "storyboard-group"}
    pg.evaluate("(ids)=>window.__libtv_store.getState().selectNodes(ids);", ids)
    pg.keyboard.press("g")
    pg.wait_for_timeout(900)
    grouped = pg.evaluate(MEASURE)
    made = [n["id"] for n in grouped["nodes"]
            if n["type"] == "storyboard-group" and n["id"] not in pre_groups]
    if len(made) != 1:
        return {"arm": "copyFlatGroup",
                "FAILED": "按 G 之后没有恰好多出一个组（实得 %d）" % len(made)}
    pg.evaluate("(id)=>window.__libtv_store.getState().selectNodes([id]);", made[0])
    before_sel = pg.evaluate(
        "()=>[...window.__libtv_store.getState().selectedNodeIds]")
    pg.keyboard.press("Meta+d")
    pg.wait_for_timeout(900)
    before = pg.evaluate(MEASURE)
    pg.evaluate("()=>window.__libtv_store.getState().duplicateSelectedNodes();")
    pg.wait_for_timeout(900)
    after = pg.evaluate(MEASURE)
    new_ids = [n["id"] for n in after["nodes"]
               if n["id"] not in {b["id"] for b in before["nodes"]}]
    if len(new_ids) != 3:
        return {"arm": "copyFlatGroup",
                "FAILED": "预期 3 个副本（组+2成员），实得 %d" % len(new_ids)}
    return {"arm": "copyFlatGroup", "groupId": made[0], "copyIds": new_ids,
            "afterGrouping": grouped, "selectedBeforeKey": before_sel,
            "before": before, "after": after, "viaUiKey": "Cmd+D"}


def arm_copy_nested(pg):
    """★ 注入嵌套 → 选**外层**组 → 复制（应连整个子树一起复制）。"""
    err = make_nested(pg)
    if err:
        return {"arm": "copyNested", "FAILED": err}
    pg.evaluate("(id)=>window.__libtv_store.getState().selectNodes([id]);", OUTER)
    cell, err = copies(pg, 5, "复制外层组")
    if err:
        return {"arm": "copyNested", "FAILED": err}
    cell["arm"] = "copyNested"
    return cell


def arm_copy_member(pg):
    """★ 注入嵌套 → 只选内层组的一个**成员** → 复制（应脱管、成为顶层）。"""
    err = make_nested(pg)
    if err:
        return {"arm": "copyMember", "FAILED": err}
    pg.evaluate("(id)=>window.__libtv_store.getState().selectNodes([id]);", "n-m1")
    cell, err = copies(pg, 1, "复制组内一个成员")
    if err:
        return {"arm": "copyMember", "FAILED": err}
    cell["arm"] = "copyMember"
    return cell


ARMS = [("copyFlatGroup", arm_copy_flat_group),
        ("copyNested", arm_copy_nested),
        ("copyMember", arm_copy_member)]


def fmt(cell):
    if cell.get("FAILED"):
        return "FAILED:%s" % cell["FAILED"]
    b = {n["id"]: n for n in cell["before"]["nodes"]}
    a = {n["id"]: n for n in cell["after"]["nodes"]}
    parts = []
    for cid in cell["copyIds"]:
        c = a[cid]
        mate = [n for n in cell["before"]["nodes"]
                if n["abs"]["x"] == c["abs"]["x"] - OFFSET
                and n["abs"]["y"] == c["abs"]["y"] - OFFSET]
        m = mate[0] if mate else None
        parts.append("%s abs(%s,%s) d=%s 父=%s ← %s"
                     % (cid[:6], c["abs"]["x"], c["abs"]["y"], c["abs"]["depth"],
                        c["parentId"] or "∅",
                        ("%s abs(%s,%s) d=%s" % (m["id"][:6], m["abs"]["x"],
                                                 m["abs"]["y"], m["abs"]["depth"]))
                        if m else "★找不到原节点"))
    return "副本%d ｜ %s" % (len(cell["copyIds"]), " ｜ ".join(parts))


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
                    pg.set_default_timeout(60000)
                    tries = t + 1
                    try:
                        boot(pg)
                        cell = fn(pg)
                        cell["arm"] = name
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
                print("  r%d %-16s %s" % (rd + 1, name, fmt(cell)), flush=True)
            rounds.append({"round": rd + 1, "rows": rows})
        b.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"batch": 801, "phase": PHASE, "rounds": rounds},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
