#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 800 探针 —— **取消分组**（`ungroupSelectedNodes`）的坐标系

## 起点：799 的**姊妹**缺陷

799 查出 `fitStoryboardGroupsToChildren` 写回时把 kids 的**绝对**包围盒
原样写进组的 `position`，而 `position` 的语义是**相对直接父节点**。

★ 同一类错误在 `ungroupSelectedNodes` 里还有**第二处**（`canvasStore.ts` 约 3580 行）：

    withoutParent(node, {
      x: group.position.x + node.position.x,   // ★ 只加了一层
      y: group.position.y + node.position.y,
    })

它假设「组的 `position` 就是组的绝对位置」⟹ 这只在组**没有父节点**时成立。
嵌套时沿途所有祖先的偏移都被**丢掉** ⟹ **取消一次分组，里面的东西会跳位**。

## ★ 判据：取消分组**不该**让任何东西移动

不变量 U：对每个成员，取消分组**前后**的**绝对**位置必须**逐位相同**。
——「我只是取消了分组，东西不该跳」。这条与坐标系语义无关，只看用户看得见的位置。

## ★ 四条臂

| 臂 | 怎么造分组 | 角色 |
| --- | --- | --- |
| ★ 键盘往返 | 选 2 个散节点按 `G` 造组，再按 `Shift+G` 取消 | 阴性对照：**纯 UI 用户路径**，组无父 ⟹ 必须全对 |
| ★ 取消**外层** | 注入嵌套数据，直接调 store | 阴性对照：取消**顶层**组 ⟹ 沿途没有祖先 ⟹ 必须全对 |
| ★ 取消**内层** | 注入嵌套数据，直接调 store | 缺陷臂：内层组成员会跳 |

★ 前两条阴性对照是**同一个操作**（取消分组）在「沿途没有祖先」时的样子，
  第三条是「沿途有一个祖先」时的样子 ⟹ 两者的**差**就是缺陷本身，
  不需要另找对照。键盘臂额外证明：**真的用户路径**（`page.tsx:1412` 的 `Shift+G`
  分支）也是对的 ⟹ 缺陷只出现在注入出来的嵌套结构上。

★ 嵌套臂必须注入：792 已复核，UI 造不出嵌套（`groupSelectedNodes` 的 children 过滤）。

★ 阳性对照：解除后成员的 `parentId` 必须**确实被删掉**。
  没有它，「什么都没发生」也会让不变量 U 成立 ⟹ 假绿。
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
    "liblib-canvas-batch800-2026-10-01/raw/vb800a-%s.json" % PHASE)

OUTER, INNER = "g-outer", "g-inner"

#: ★ 嵌套注入：outer ⊃ {inner, loose}，inner ⊃ {m1, m2}
#:   层序自洽（每个 position 从 0 起，语义「相对直接父节点」），外层**有偏移**。
MAKE_NESTED = """(ids)=>{
  const st=window.__libtv_store;
  const mk=(id,type,pos,extra)=>Object.assign({
    id:id,type:type,position:{x:pos[0],y:pos[1]},width:0,height:0,
    data:{},style:{},measured:{},selected:false,dragging:false},extra||{});
  const g=(id,pos,parentId,title)=>mk(id,'storyboard-group',pos,{
    parentId:parentId||undefined,width:10,height:10,
    style:{width:10,height:10,zIndex:-1001},zIndex:-1001,
    data:{title:title,variant:'image'}});
  const t=(id,pos,parentId)=>mk(id,'text',pos,{
    parentId:parentId||undefined,width:200,height:100});
  st.getState().setNodes([
    g(ids.outer,[200,150],null,'外层'),
    g(ids.inner,[40,40],ids.outer,'内层'),
    t('n-m1',[40,40],ids.inner),
    t('n-m2',[440,40],ids.inner),
    t('n-loose',[40,440],ids.outer),
  ]);
  return {ok:true};}"""

#: ★ 读**每个**节点的绝对位置（沿 parentId 链求和）+ 是否还挂在组里
MEASURE = """()=>{
  const S=window.__libtv_store.getState();
  const cv=S.canvases.find(c=>c.id===S.activeCanvasId)||S.canvases[0];
  const byId=new Map(cv.nodes.map(n=>[n.id,n]));
  const abs=(n)=>{let x=n.position.x,y=n.position.y,p=n.parentId;
    const seen=new Set([n.id]); let d=0;
    while(p&&!seen.has(p)&&d<32){seen.add(p);d+=1;
      const q=byId.get(p); if(!q)break; x+=q.position.x;y+=q.position.y;p=q.parentId;}
    return {x:x,y:y,depth:d};};
  return {nodes:cv.nodes.map(n=>({id:n.id, type:n.type,
      parentId:n.parentId||null,
      pos:{x:n.position.x,y:n.position.y},
      abs:abs(n), w:n.width, h:n.height}))
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


def settle(pg, ms=900):
    """★ 注入后 `routeReactFlowChanges` 的尺寸反馈会连续跑 fit（799 实测）
    ⟹ 读数前必须等到几何稳定，否则读到的是中间态。"""
    pg.wait_for_timeout(ms)


def make_nested(pg):
    r = pg.evaluate(MAKE_NESTED, {"outer": OUTER, "inner": INNER})
    if r.get("FAILED"):
        return r.get("FAILED")
    settle(pg)
    return None


def arm_keyboard_roundtrip(pg):
    """★ 纯 UI 路径：选 2 个散节点 → `G` 造组 → `Shift+G` 取消。"""
    ids = pg.evaluate("""()=>{
      const S=window.__libtv_store.getState();
      const cv=S.canvases.find(c=>c.id===S.activeCanvasId)||S.canvases[0];
      return cv.nodes.filter(n=>n.type!=='storyboard-group'&&!n.parentId)
        .slice(0,2).map(n=>n.id);}""")
    if not ids or len(ids) < 2:
        return {"arm": "keyboardRoundtrip", "FAILED": "画布上没有 2 个顶层散节点"}
    # ★ 先记下按 G **之前**已有的组 —— 种子画布上本来就有一个组，
    #   第一版按「不在选区里」找新组，把它也算进去了（实得 3 个而不是 1 个）。
    pre_groups = {n["id"] for n in pg.evaluate(MEASURE)["nodes"]
                  if n["type"] == "storyboard-group"}
    pg.evaluate("(ids)=>window.__libtv_store.getState().selectNodes(ids);", ids)
    pg.keyboard.press("g")
    pg.wait_for_timeout(900)
    grouped = pg.evaluate(MEASURE)
    new_group = [n for n in grouped["nodes"]
                 if n["type"] == "storyboard-group" and n["id"] not in pre_groups]
    if len(new_group) != 1:
        return {"arm": "keyboardRoundtrip",
                "FAILED": "按 G 之后没有恰好多出一个组（实得 %d 个）"
                          % len(new_group)}
    before = pg.evaluate(MEASURE)
    pg.keyboard.press("Shift+g")
    pg.wait_for_timeout(900)
    after = pg.evaluate(MEASURE)
    return {"arm": "keyboardRoundtrip", "members": ids,
            "groupId": new_group[0]["id"],
            "groupCountBefore": sum(1 for n in grouped["nodes"]
                                    if n["type"] == "storyboard-group"),
            "groupCountAfter": sum(1 for n in after["nodes"]
                                   if n["type"] == "storyboard-group"),
            "before": before, "after": after}


def arm_ungroup(gid, watch):
    """★ 注入嵌套 → 取消 `gid` 的分组 ⟹ `watch` 里的 id 绝对位置不该变。"""
    err = make_nested(pg_holder[0])
    if err:
        return {"arm": "ungroup", "FAILED": err}
    pg = pg_holder[0]
    before = pg.evaluate(MEASURE)
    pg.evaluate("(id)=>window.__libtv_store.getState().ungroupSelectedNodes([id]);", gid)
    pg.wait_for_timeout(900)
    after = pg.evaluate(MEASURE)
    return {"arm": "ungroup", "groupId": gid, "watch": watch,
            "before": before, "after": after}


pg_holder = [None]


def arm_ungroup_inner(pg):
    return arm_ungroup(INNER, ["n-m1", "n-m2"])


def arm_ungroup_outer(pg):
    return arm_ungroup(OUTER, [INNER, "n-loose"])


ARMS = [("keyboardRoundtrip", arm_keyboard_roundtrip),
        ("ungroupInner", arm_ungroup_inner),
        ("ungroupOuter", arm_ungroup_outer)]


def fmt(cell):
    if cell.get("FAILED"):
        return "FAILED:%s" % cell["FAILED"]
    b = {n["id"]: n for n in cell["before"]["nodes"]}
    a = {n["id"]: n for n in cell["after"]["nodes"]}
    watch = cell.get("watch") or cell.get("members") or []
    parts = []
    for i in watch:
        if i not in b or i not in a:
            parts.append("%s 消失" % i)
            continue
        moved = (b[i]["abs"]["x"] != a[i]["abs"]["x"]
                 or b[i]["abs"]["y"] != a[i]["abs"]["y"])
        parts.append("%s %s→%s %s" % (i, (b[i]["abs"]["x"], b[i]["abs"]["y"]),
                                       (a[i]["abs"]["x"], a[i]["abs"]["y"]),
                                       "★跳位" if moved else "不动"))
    return "组%s ｜ %s" % (cell.get("groupId", "?"), " ｜ ".join(parts))


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
                    pg_holder[0] = pg
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
                print("  r%d %-18s %s" % (rd + 1, name, fmt(cell)), flush=True)
            rounds.append({"round": rd + 1, "rows": rows})
        b.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"batch": 800, "phase": PHASE, "rounds": rounds},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
