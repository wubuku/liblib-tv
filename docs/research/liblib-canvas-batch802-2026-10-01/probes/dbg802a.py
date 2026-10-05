#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 802 探针 —— `createImageHdPreset`：从**组内**的源节点建组，组会错位

## 起点：写点普查（`scan802.mjs`）的收获

802 先用 TypeScript AST 把「把 nodes 写进 canvas 对象」的**全部**写点普查出来：
**41 个写点、37 个动作，只有 4 个 fit 调用**。筛出「改了 `parentId` 或碰了坐标系
换算，却不经 fit」的高风险动作，逐个读源码 ⟹ 找到这一处。

## 缺陷（`canvasStore.ts:1642`）

    position: { x: source.position.x + 320, y: source.position.y - 60 }

`source.position` 的语义是「相对**直接父节点**」⟹ 源节点只要**在任何一个组里**
（不需要嵌套），新组又是**顶层**（无 `parentId`）⟹ 祖先的偏移被整段丢掉。

★ 与 799 / 800 是**同一类**错误（把相对坐标当绝对坐标），但触发条件**更宽**：
799 要「嵌套 + 外层有偏移」，800 要「取消嵌套组」，而这条**只要源在普通组里**。

★ **用户可达**：`ImageNode.tsx:294` 的「图片高清」按钮直接调它。

## ★ 判据

新组的**绝对**位置必须 = 源的**绝对**位置 + (320, −60)。只说绝对位置，
不预设实现用哪个函数换算。

★ 偏移 (320, −60) 也**不写死**：先测出「实际偏移」，再要求它与「源绝对 − 源相对」
  之差**逐位相等** ⟹ 那正是被丢掉的祖先偏移。
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
    "liblib-canvas-batch802-2026-10-01/raw/vb802a-%s.json" % PHASE)

#: 注入：一个宿主组 @(200,150)，里面放源节点 rel(50,50) ⟹ 源绝对 (250,200)。
#:   ★ 源节点的 `position` 是**相对**的，所以祖先偏移 (200,150) 正是
#:   「读源码以为拿到绝对、实际只拿到相对」时会丢掉的那一段。
MAKE_HOST = """(cfg)=>{
  const host=cfg.host, ox=cfg.ox, oy=cfg.oy;
  const st=window.__libtv_store;
  const mk=(id,type,pos,extra)=>Object.assign({
    id:id,type:type,position:{x:pos[0],y:pos[1]},width:0,height:0,
    data:{},style:{},measured:{},selected:false,dragging:false},extra||{});
  st.getState().setNodes([
    mk(host,'storyboard-group',[ox,oy],{width:400,height:400,
       style:{width:400,height:400,zIndex:-1001},zIndex:-1001,
       data:{title:'宿主组',variant:'image',tag:host}}),
    mk('n-src','image',[50,50],{parentId:host,width:200,height:100,
       data:{tag:'n-src'}}),
    mk('n-loose','image',[800,600],{width:200,height:100,
       data:{tag:'n-loose'}}),
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


def arm(pg, source_id, label, ox=200, oy=150):
    """★ 注入宿主组(ox,oy) → 以 `source_id` 调 `createImageHdPreset` → 读新建的组。"""
    r = pg.evaluate(MAKE_HOST, {"host": "g-host", "ox": ox, "oy": oy})
    if r.get("FAILED"):
        return {"arm": label, "FAILED": r["FAILED"]}
    pg.wait_for_timeout(800)
    before = pg.evaluate(MEASURE)
    src = [n for n in before["nodes"] if n["id"] == source_id][0]
    pg.evaluate("(id)=>window.__libtv_store.getState().createImageHdPreset(id);",
                source_id)
    pg.wait_for_timeout(900)
    after = pg.evaluate(MEASURE)
    before_ids = set(n["id"] for n in before["nodes"])
    fresh = [n for n in after["nodes"] if n["id"] not in before_ids]
    groups = [n for n in fresh if n["type"] == "storyboard-group"]
    if len(groups) != 1:
        return {"arm": label,
                "FAILED": "新建的组应恰有 1 个，实得 %d" % len(groups)}
    g = groups[0]
    kids = [n for n in fresh if n.get("parentId") == g["id"]]
    return {"arm": label, "sourceId": source_id, "newGroupId": g["id"],
            "hostOrigin": [ox, oy],
            "srcPos": src["pos"], "srcAbs": src["abs"],
            "newGroupPos": g["pos"], "newGroupAbs": g["abs"],
            "freshIds": [n["id"] for n in fresh],
            "kidsParented": [n["parentId"] == g["id"] for n in kids],
            "kidsCount": len(kids),
            "before": before, "after": after}


# ★ 三条臂：同一个「源在组内」的动作，宿主组放在**两个不同**的位置。
#   判据 = **宿主组移动 Δ，新组也必须移动 Δ**（新组由源的**绝对**位置决定）。
#   若实现用的是源的**相对**位置，新组会纹丝不动 ⟹ 缺陷一眼可见，
#   而且**完全不涉及任何常量**（不需要知道偏移是 320 还是别的）。
ARMS = [("presetFromLoose", "n-loose", 200, 150),      # 源是顶层 ⟹ 阴性对照
        ("presetFromGroupedA", "n-src", 200, 150),     # 源在组内，宿主 @(200,150)
        ("presetFromGroupedB", "n-src", 500, 450)]     # 源在组内，宿主 @(500,450)


def fmt(cell):
    if cell.get("FAILED"):
        return "FAILED:%s" % cell["FAILED"]
    lost = (cell["srcAbs"]["x"] - cell["srcPos"]["x"],
            cell["srcAbs"]["y"] - cell["srcPos"]["y"])
    d = (cell["newGroupPos"]["x"] - cell["srcAbs"]["x"],
         cell["newGroupPos"]["y"] - cell["srcAbs"]["y"])
    return ("宿主%s 源 %s rel(%s,%s) abs(%s,%s) ｜ 新组 pos(%s,%s) ｜ 相对源的绝对偏移%s"
            " ｜ 丢掉祖先%s ｜ 子节点 %d 挂对=%s"
            % (list(cell.get("hostOrigin") or []), cell["sourceId"],
               cell["srcPos"]["x"], cell["srcPos"]["y"],
               cell["srcAbs"]["x"], cell["srcAbs"]["y"],
               cell["newGroupPos"]["x"], cell["newGroupPos"]["y"],
               list(d), list(lost), cell["kidsCount"],
               all(cell["kidsParented"])))


def main():
    rounds = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        for rd in range(2):
            rows = []
            for name, src, ox, oy in ARMS:
                cell, tries = None, 0
                for t in range(3):
                    pg = b.new_page()
                    pg.set_default_timeout(60000)
                    tries = t + 1
                    try:
                        boot(pg)
                        cell = arm(pg, src, name, ox, oy)
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
                print("  r%d %-20s %s" % (rd + 1, name, fmt(cell)), flush=True)
            rounds.append({"round": rd + 1, "rows": rows})
        b.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"batch": 802, "phase": PHASE, "rounds": rounds},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
