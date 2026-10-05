#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 793 探针 —— 分组框**跟随**成员吗

## 承重事实（batch 757，本批要**重新确认**而不是引用）

把子节点拖出分组框之后：

- 分组框 DOM 位置 / 尺寸**都不变**
- 子节点**仍然挂着** `parentId`
- ⟹ **store 说它属于这个组，屏幕说它不在框里**

批 757 记的读数：拖 501px 后子节点左边缘距框右边缘 **277** 屏幕像素
（完全在框外），框一动不动、也不提示。

## 三条臂

| 臂 | 拖什么 | 作用 |
| --- | --- | --- |
| ★ 处理臂 | 有成员的组的**子节点** | 就是不跟随的那条 |
| ★ 阳性对照一 | 一个**非成员**节点（散节点） | 拖它**不得**动任何组 |
| ★ 阳性对照二 | **组本身** | 拖它尺寸**不得**变，且成员要跟着走 |

★ 两条对照缺一不可：只测「子节点拖出去框跟着走」的话，
一个「凡是拖动就把所有组都重算一遍」的粗糙实现也能全绿
——它会让非成员的拖动也动组。

## 每个读数怎么来

| 读什么 | 怎么读 |
| --- | --- |
| 框**画在哪** | `.react-flow__node-storyboard-group[data-id=…]` 的 DOM rect |
| 框**存的是** | store 里该组的 `position` / `width` / `height` |
| 子节点**绝对**位置 | store 里沿 `parentId` 链求和（与 `getAbsoluteNodePosition` 同算法） |
| 子节点**在不在框里** | 两个 **DOM** rect 的包含关系（同一页内前后对比，zoom 自动约掉） |
| 挂载还在不在 | 子节点的 `parentId` |

★ 757 吃过亏：zoom 在同一批里变了三次（0.375 / 1.501 / 0.751）。
本探针**不换算 zoom** —— 前后对比都在同一页、同一 zoom 下用 DOM rect，
zoom 自己约掉；另把当轮 zoom 记进 raw 以防后人误用。

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
    "liblib-canvas-batch793-2026-10-01/raw/vb793a-%s.json" % PHASE)

GROUPSEL = ".react-flow__node-storyboard-group"

#: ★ 读框的 DOM rect + 组的 store 值 + 每个子节点的绝对位置与「在不在框里」
MEASURE = """(gid)=>{
  const s=window.__libtv_store.getState();
  const cv=s.canvases.find(c=>c.id===s.activeCanvasId)||s.canvases[0];
  const byId=new Map(cv.nodes.map(n=>[n.id,n]));
  const abs=(n)=>{let x=n.position.x,y=n.position.y,p=n.parentId;
    const seen=new Set([n.id]);
    while(p&&!seen.has(p)){seen.add(p);const q=byId.get(p);
      if(!q)break;x+=q.position.x;y+=q.position.y;p=q.parentId;}
    return {x,y};};
  const R=(r)=>({t:Math.round(r.top),l:Math.round(r.left),
    w:Math.round(r.width),h:Math.round(r.height),
    b:Math.round(r.bottom),r:Math.round(r.right)});
  const el=document.querySelector('.react-flow__node-storyboard-group[data-id="'+gid+'"]');
  const g=byId.get(gid);
  const kids=cv.nodes.filter(n=>n.parentId===gid);
  const childInfo=kids.map(k=>{
    const a=abs(k);
    const ke=document.querySelector('.react-flow__node[data-id="'+k.id+'"]');
    const kr=ke?R(ke.getBoundingClientRect()):null;
    const gr=el?R(el.getBoundingClientRect()):null;
    const inside= !!(kr&&gr && kr.l>=gr.l && kr.t>=gr.t
      && kr.r<=gr.r && kr.b<=gr.b);
    return {id:k.id, abs:{x:Math.round(a.x),y:Math.round(a.y)},
      w:k.width||null, h:k.height||null, dom:kr, inside};
  });
  return {canvasId:cv.id,
    zoom:(document.querySelector('.react-flow__viewport')||{}).style
      ? document.querySelector('.react-flow__viewport').style.transform : null,
    groupId:gid, groupStore:g?{pos:{x:g.position.x,y:g.position.y},
      w:g.width||null,h:g.height||null}:null,
    groupDom:el?R(el.getBoundingClientRect()):null,
    kids:childInfo};}"""

FIND_POINT = """(sel)=>{const el=document.querySelector(sel);
  if(!el) return {missing:true};
  const r=el.getBoundingClientRect();
  if(r.width<8||r.height<8) return {zero:true, r:[r.width,r.height]};
  // ★ 取**内圈**的点，避开描边与被别的元素盖住的边
  const pts=[[0.5,0.5],[0.5,0.3],[0.3,0.5],[0.5,0.7],[0.7,0.5]];
  for(const [fx,fy] of pts){
    const x=Math.round(r.left+r.width*fx), y=Math.round(r.top+r.height*fy);
    if(x<2||y<2||x>innerWidth-2||y>innerHeight-2) continue;
    const e=document.elementFromPoint(x,y);
    if(e&&e.closest&&e.closest(sel)===el) return {pt:[x,y]};
  }
  return {noHit:true};}"""


def boot(pg):
    pg.goto(A.BASE, wait_until="domcontentloaded")
    pg.evaluate(A.CLEAR_LS, A.LS_KEY)
    pg.set_viewport_size({"width": 1440, "height": 1000})
    pg.goto(A.BASE, wait_until="networkidle")
    pg.wait_for_selector(".react-flow__node", timeout=25000)
    pg.wait_for_timeout(1300)
    pg.keyboard.press("Meta+0")
    pg.wait_for_timeout(700)


def pick_group(pg):
    """★ 挑一个**有成员**的组（没有成员就没得测跟随）。"""
    return pg.evaluate("""()=>{const s=window.__libtv_store.getState();
      const cv=s.canvases.find(c=>c.id===s.activeCanvasId)||s.canvases[0];
      const g=cv.nodes.find(n=>n.type==='storyboard-group'
        && cv.nodes.some(m=>m.parentId===n.id));
      if(!g) return null;
      const kid=cv.nodes.find(m=>m.parentId===g.id);
      const loose=cv.nodes.find(n=>n.type!=='storyboard-group'&&!n.parentId);
      return {gid:g.id, kidId:kid?kid.id:null, looseId:loose?loose.id:null};}""")


FIND_GROUP_POINT = """(sel)=>{
  // ★ 组框是 `zIndex:-1001`，它的**中心被子节点盖住**，标题又带
  //   `pointer-events-none` 抓不到 ⟹ 通用内圈扫描必然失败（第一版
  //   就是这样两条轮次全 FAILED「点不到组框」）。
  // ⟹ 这里专门找「命中组、且**不属于任何其他节点**」的点。
  // ★ 还要贴着**边**扫：修好之后框会变贴合，padding 只剩
  //   32 store px ≈ 12 屏幕 px，从 8% 起扫会正好越过 padding 落到子节点上
  //   （第二版就是这样：pre 通、post FAILED）。⟹ 先沿四边细扫，再退回全网格。
  const el=document.querySelector(sel);
  if(!el) return {missing:true};
  const r=el.getBoundingClientRect();
  if(r.width<8||r.height<8) return {zero:true};
  const ok=(x,y)=>{ if(x<2||y<2||x>innerWidth-2||y>innerHeight-2) return null;
    const e=document.elementFromPoint(x,y);
    if(!e||!e.closest) return null;
    return e.closest('.react-flow__node')===el ? [x,y] : null; };
  // ① 沿边细扫（0.01 ~ 0.12，步长 0.01）
  for(let t=0.01; t<=0.121; t+=0.01){
    for(const [fx,fy] of [[t,0.01],[t,0.99],[0.01,t],[0.99,t],
                          [t,0.06],[t,0.94],[0.06,t],[0.94,t]]){
      const p=ok(Math.round(r.left+r.width*fx), Math.round(r.top+r.height*fy));
      if(p) return {pt:p, edge:true};
    }
  }
  // ② 退回全网格
  for(let fy=0.08; fy<=0.92; fy+=0.06)
    for(let fx=0.08; fx<=0.92; fx+=0.06){
      const p=ok(Math.round(r.left+r.width*fx), Math.round(r.top+r.height*fy));
      if(p) return {pt:p, edge:false};
    }
  return {noHit:true, rect:[Math.round(r.width),Math.round(r.height)]};}"""


def drag_group(pg, gid, dx, dy):
    p = pg.evaluate(FIND_GROUP_POINT,
                    '.react-flow__node-storyboard-group[data-id="%s"]' % gid)
    if not p.get("pt"):
        return {"FAILED": p, "moved": False}
    x, y = p["pt"]
    pg.mouse.move(x, y)
    pg.mouse.down()
    pg.mouse.move(x + dx, y + dy, steps=22)
    pg.mouse.up()
    pg.wait_for_timeout(500)
    return {"moved": True, "from": p["pt"], "to": [x + dx, y + dy]}


def drag(pg, sel, dx, dy):
    """★ 抓住元素中心拖 (dx, dy)。

    ★ R26：给组**新写**一个 `drag_group` 时，上一版编辑把 `def drag(...)`
      那一行当成锚点替换掉了，于是 `drag` 的函数体变成了 `drag_group`
      里 `return` **之后**的死代码 —— 语法照样通过、探针照样能跑，
      只有另外两条臂一调 `drag` 就 `NameError`。
      ⟹ 改完必须 `grep` 确认**所有**被调用的函数都还有 `def`。
    """
    p = pg.evaluate(FIND_POINT, sel)
    if not p.get("pt"):
        return {"FAILED": p, "moved": False}
    x, y = p["pt"]
    pg.mouse.move(x, y)
    pg.mouse.down()
    pg.mouse.move(x + dx, y + dy, steps=22)
    pg.mouse.up()
    pg.wait_for_timeout(500)
    return {"moved": True, "from": p["pt"], "to": [x + dx, y + dy]}


def arm_drag_child_out(pg):
    """★ 处理臂：把有成员的组的**子节点**往右拖，拖到框外。"""
    ids = pick_group(pg)
    if not ids or not ids.get("kidId"):
        return {"arm": "dragChildOut", "FAILED": "找不到有成员的组"}
    before = pg.evaluate(MEASURE, ids["gid"])
    d = drag(pg, '.react-flow__node[data-id="%s"]' % ids["kidId"], 380, 0)
    if d.get("FAILED"):
        return {"arm": "dragChildOut", "FAILED": "点不到子节点", "detail": d}
    after = pg.evaluate(MEASURE, ids["gid"])
    return {"arm": "dragChildOut", "groupId": ids["gid"],
            "kidId": ids["kidId"], "drag": d,
            "before": before, "after": after}


def arm_drag_non_member(pg):
    """★ 阳性对照一：拖一个**非成员**（散节点）⟹ 任何组都不得动。"""
    ids = pick_group(pg)
    if not ids or not ids.get("looseId"):
        return {"arm": "dragNonMember", "FAILED": "找不到散节点"}
    before = pg.evaluate(MEASURE, ids["gid"])
    d = drag(pg, '.react-flow__node[data-id="%s"]' % ids["looseId"], 260, 180)
    if d.get("FAILED"):
        return {"arm": "dragNonMember", "FAILED": "点不到散节点", "detail": d}
    after = pg.evaluate(MEASURE, ids["gid"])
    return {"arm": "dragNonMember", "groupId": ids["gid"],
            "looseId": ids["looseId"], "drag": d,
            "before": before, "after": after}


def arm_drag_group_itself(pg):
    """★ 阳性对照二：拖**组本身**⟹ 尺寸不得变，成员要跟着走。"""
    ids = pick_group(pg)
    if not ids:
        return {"arm": "dragGroupItself", "FAILED": "找不到有成员的组"}
    before = pg.evaluate(MEASURE, ids["gid"])
    # ★ 组的**中间**被子节点占满、标题又 `pointer-events-none`，
    #   ⟹ 必须用专门找「只属于组」的点的那套，不能用通用内圈扫描
    d = drag_group(pg, ids["gid"], 0, 150)
    if d.get("FAILED"):
        return {"arm": "dragGroupItself", "FAILED": "点不到组框", "detail": d}
    after = pg.evaluate(MEASURE, ids["gid"])
    return {"arm": "dragGroupItself", "groupId": ids["gid"],
            "drag": d, "before": before, "after": after}


ARMS = [("dragChildOut", arm_drag_child_out),
        ("dragNonMember", arm_drag_non_member),
        ("dragGroupItself", arm_drag_group_itself)]


def fmt(cell):
    if cell.get("FAILED"):
        return "FAILED:%s" % cell["FAILED"]
    b, a = cell["before"], cell["after"]
    gb, ga = b["groupStore"], a["groupStore"]
    db, da = b["groupDom"], a["groupDom"]
    kb = b["kids"][0] if b["kids"] else {}
    ka = a["kids"][0] if a["kids"] else {}
    return ("组 pos (%s,%s)→(%s,%s) 尺寸 %sx%s→%sx%s | DOM 尺寸 %s→%s | "
            "子节点 绝对 (%s,%s)→(%s,%s) 在框内 %s→%s"
            % (gb["pos"]["x"], gb["pos"]["y"], ga["pos"]["x"], ga["pos"]["y"],
               gb["w"], gb["h"], ga["w"], ga["h"],
               (db["w"], db["h"]) if db else None,
               (da["w"], da["h"]) if da else None,
               kb.get("abs", {}).get("x"), kb.get("abs", {}).get("y"),
               ka.get("abs", {}).get("x"), ka.get("abs", {}).get("y"),
               kb.get("inside"), ka.get("inside")))


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
    OUT.write_text(json.dumps({"batch": 793, "phase": PHASE, "rounds": rounds},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
