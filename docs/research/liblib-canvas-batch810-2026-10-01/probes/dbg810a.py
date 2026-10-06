#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 810 探针 —— 「组框到底有没有收敛成不动点？」

## 起点：799 留下的一句话

`canvasStore.ts:722-726` 的注释写着：

    3. **单趟不足，靠反馈补齐**。`routeReactFlowChanges` 每次 react-flow 变化
       （含 DOM 测量产生的 `dimensions` change）都会再跑一次本函数……
       也就是说「先外后内 + 每轮重算」单跑一趟是**不够**的，正确性依赖那条反馈。

799 当时是在**嵌套**结构上看到第 2 趟才收敛的。而 792 已经决定
**UI 造不出嵌套组** ⟹ 那条「单趟不足」在**用户可达**的形态里到底还成不成立，
**没有人量过**。

## ★ 判据（独立重算，**不读源码公式**）

组框必须**恰好包住所有成员**：

    期望 x      = min(成员绝对 x) − padding
    期望 y      = min(成员绝对 y) − padding
    期望 width  = (max(成员绝对 x + 宽) − min(成员绝对 x)) + padding × 2
    期望 height = (max(成员绝对 y + 高) − min(成员绝对 y)) + padding × 2

`padding` 由 raw 里**反推**（用两个不同成员的包围盒解方程），不是抄源码里的 40。
容差 0.01 —— 源码自己的 no-op 分支也用这个量级（`canvasStore.ts:792` 的 `EPS`）。

## ★ 阳性对照（没有它，「全绿」什么都不能说明）

**臂 0**：把组框**手动改成一个明显错的尺寸**（10×10），
然后等反馈沉淀 ⟹ 如果 fit 真的在跑，它必须**自己修回**期望值。
修不回来 ⟹ 判据抓不到「fit 根本没执行」⟹ 整批作废。

## ★ 记两个时刻

每条臂都读**两次**（沉淀后 + 再等一轮）：两次相同 ⟹ 已经是不动点。
不一样 ⟹ 还在动，那本身就是一条读数。
"""
import json
import os
import pathlib
import sys
import time
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch774-2026-10-01" / "probes"))
import dbg774a as A  # noqa: E402

OUT = pathlib.Path(os.environ.get("VB810_OUT") or
                   (HERE.parent / "raw" / "vb810a.json"))
VID = "v-UGQZzZOpbv"          # 种子视频，**本来就在组里**
SEEDS = ["i-1FQ9tErTcC", "i-lBzmo67AHv", "i-dnwoZQ7jsG", "i-vxeeCnxySa"]

#: ★ `setNodes` 是**整表替换**（`canvasStore.ts:3645`），不是按 id 合并
#:   ⟹ 809 踩过：只传一个节点进去，整张画布会被抹成那一个。
PATCH = """(ops)=>{const S=window.__libtv_store.getState();
  const cv=S.canvases.find(c=>c.id===S.activeCanvasId); if(!cv) return {FAILED:'no canvas'};
  const byId=new Map(cv.nodes.map(n=>[n.id,n]));
  const next=cv.nodes.map(n=>{
    const op=ops.filter(o=>o.id===n.id)[0];
    if(!op) return n;
    const patch={};
    if(op.pos) patch.position={x:op.pos[0],y:op.pos[1]};
    if(op.wh){ patch.width=op.wh[0]; patch.height=op.wh[1];
      patch.style={...(n.style||{}),width:op.wh[0],height:op.wh[1]}; }
    return Object.assign({},n,patch);
  });
  if(ops.some(o=>o.wh) && ops[0].wh){
    // 组的 style 也要跟上，否则 React Flow 读的还是旧尺寸
    next.forEach(n=>{const op=ops.filter(o=>o.id===n.id)[0];
      if(op&&op.wh) n.style={...(n.style||{}),width:op.wh[0],height:op.wh[1]};});
  }
  S.setNodes(next);
  return {ok:true,total:next.length};}"""

#: ★★ 探针返工：原来「施加扰动」和「读瞬间」是**两次** `page.evaluate`，
#:   中间隔了一次进程往返 ⟹ `setNodes` 触发的 React 重排 + react-flow 的
#:   `dimensions` 变化已经把框修回去了，**读到的还是原值** ⟹ 阳性对照形同虚设
#:   （第一版 S2 差点据此宣布「fit 会自我修复」）。
#:   修法：**同一个** `page.evaluate` 里 `setNodes` 之后**同步** `getState()` ——
#:   `set` 是同步的，此刻读到的就是**还没被 React 洗过**的原始值。
PATCH_READ = """(ops)=>{const S=window.__libtv_store.getState();
  const cv=S.canvases.find(c=>c.id===S.activeCanvasId); if(!cv) return {FAILED:'no canvas'};
  const byId=new Map(cv.nodes.map(n=>[n.id,n]));
  const next=cv.nodes.map(n=>{
    const op=ops.filter(o=>o.id===n.id)[0]; if(!op) return n;
    const patch={};
    if(op.pos) patch.position={x:op.pos[0],y:op.pos[1]};
    if(op.wh){ patch.width=op.wh[0]; patch.height=op.wh[1];
      patch.style={...(n.style||{}),width:op.wh[0],height:op.wh[1]}; }
    return Object.assign({},n,patch);
  });
  S.setNodes(next);
  // ★ 同步读：set 之后的第一个瞬间，React 还没跑
  const after=window.__libtv_store.getState();
  const cv2=after.canvases.find(c=>c.id===after.activeCanvasId);
  const touched=ops.map(o=>{const m=cv2.nodes.find(x=>x.id===o.id);
    return m?{id:m.id,w:m.width,h:m.height,
              pos:{x:m.position.x,y:m.position.y}}:null;});
  return {ok:true,total:next.length,touched:touched};}"""

SELECT = """(ids)=>{window.__libtv_store.getState()
  .selectElements({nodeIds:ids,edgeIds:[]}); return {ok:true};}"""

PREP_READY = """(vid)=>{const S=window.__libtv_store.getState();
  window.__libtv_store.setState({canvases:S.canvases.map(c=>({...c,
    nodes:c.nodes.map(m=>m.id===vid?{...m,data:{...m.data,status:'ready'}}:m)}))});
  return {ok:true};}"""

NODES = """()=>{const S=window.__libtv_store.getState();
  const cv=S.canvases.find(c=>c.id===S.activeCanvasId)||S.canvases[0];
  const byId=new Map(cv.nodes.map(n=>[n.id,n]));
  const abs=(n)=>{let x=n.position.x,y=n.position.y,p=n.parentId;
    const seen=new Set([n.id]);let d=0;
    while(p&&!seen.has(p)&&d<32){seen.add(p);d+=1;const q=byId.get(p);if(!q)break;
      x+=q.position.x;y+=q.position.y;p=q.parentId;}
    return {x:x,y:y,depth:d};};
  return cv.nodes.map(n=>{const a=abs(n);
    return {id:n.id,type:n.type,parentId:n.parentId||null,
      pos:{x:n.position.x,y:n.position.y},abs:{x:a.x,y:a.y,depth:a.depth},
      w:n.width,h:n.height,
      sw:(n.style&&typeof n.style.width==='number')?n.style.width:null,
      sh:(n.style&&typeof n.style.height==='number')?n.style.height:null,
      domW:(n.measured&&n.measured.width)||null,
      domH:(n.measured&&n.measured.height)||null};});}"""

#: 组框的 **DOM** 读数（store 说贴合不够，用户看见的也得贴合）
GROUP_DOM = """(gid)=>{const e=document.querySelector('.react-flow__node[data-id="'+gid+'"]');
  if(!e) return null; const r=e.getBoundingClientRect();
  return {w:Math.round(r.width*100)/100,h:Math.round(r.height*100)/100,
          x:Math.round(r.left*100)/100,y:Math.round(r.top*100)/100};}"""

DOMRECT = """(ids)=>{const o={};
  for(const id of ids){const e=document.querySelector('.react-flow__node[data-id="'+id+'"]');
    if(!e){o[id]=null;continue;} const r=e.getBoundingClientRect();
    o[id]={w:Math.round(r.width*100)/100,h:Math.round(r.height*100)/100,
           x:Math.round(r.left*100)/100,y:Math.round(r.top*100)/100};}
  return o;}"""


def boot(pg):
    pg.goto(A.BASE, wait_until="domcontentloaded", timeout=90000)
    pg.evaluate(A.CLEAR_LS, A.LS_KEY)
    pg.set_viewport_size({"width": 1440, "height": 1000})
    pg.goto(A.BASE, wait_until="networkidle", timeout=90000)
    pg.wait_for_selector(".react-flow__node", timeout=60000)
    pg.wait_for_timeout(1500)


IN_VIEW = """(id)=>{const e=document.querySelector('.react-flow__node[data-id="'+id+'"]');
  if(!e) return {present:false}; const r=e.getBoundingClientRect();
  return {present:true,x:r.left,y:r.top,w:r.width,h:r.height};}"""
VIEWPORT = """()=>({w:window.innerWidth,h:window.innerHeight})"""


def ensure_visible(pg, node_id, tries=4):
    last = {}
    for _ in range(tries):
        last = pg.evaluate(IN_VIEW, node_id)
        if not last.get("present"):
            pg.wait_for_timeout(400)
            continue
        vp = pg.evaluate(VIEWPORT)
        if (last["x"] >= -2 and last["y"] >= -2
                and last["x"] + last["w"] <= vp["w"] + 2
                and last["y"] + last["h"] <= vp["h"] + 2):
            return {**last, "★ 在视口内": True}
        pg.keyboard.press("Meta+0")
        pg.wait_for_timeout(900)
    return {**last, "★ 在视口内": False}


def make_group(pg, ids, label):
    """★ 807 验证过的 UI 造组路径：选中两个散节点按 `G`。"""
    for i in ids:
        v = ensure_visible(pg, i)
        if not v.get("★ 在视口内"):
            return {"FAILED": "%s：%s 不在视口" % (label, i)}
    pg.evaluate(SELECT, list(ids))
    pg.wait_for_timeout(800)
    pg.keyboard.press("g")
    pg.wait_for_timeout(1400)
    nodes = pg.evaluate(NODES)
    grp = [n for n in nodes if n["type"] == "storyboard-group"
           and all(any(x["id"] == i and x["parentId"] == n["id"] for x in nodes)
                   for i in ids)]
    if not grp:
        return {"FAILED": "%s：按 G 之后没找到包住 %s 的组" % (label, ids)}
    return {"groupId": grp[0]["id"]}


def snapshot(pg, gid, kid_ids):
    """读两个时刻：判定「是不是已经是不动点」。"""
    n1 = pg.evaluate(NODES)
    d1 = pg.evaluate(DOMRECT, [gid] + list(kid_ids))
    pg.wait_for_timeout(2200)
    n2 = pg.evaluate(NODES)
    d2 = pg.evaluate(DOMRECT, [gid] + list(kid_ids))

    def pick(ns):
        g = [x for x in ns if x["id"] == gid]
        kids = [x for x in ns if x["parentId"] == gid]
        return {"组": g[0] if g else None,
                "成员": sorted(kids, key=lambda z: (z["id"]))}

    a, b = pick(n1), pick(n2)
    return {"第一次": a, "第二次": b,
            "dom1": d1, "dom2": d2,
            "★ 两次相同（已是不动点）":
                a["组"] is not None and b["组"] is not None
                and a["组"]["pos"] == b["组"]["pos"]
                and a["组"]["w"] == b["组"]["w"]
                and a["组"]["h"] == b["组"]["h"],
            "组DOM": pg.evaluate(GROUP_DOM, gid)}


#: ★ 真拖拽（走 `onNodesChange` ⟹ 会触发 `routeReactFlowChanges`）
#:   —— 809 的教训：**store 直写绕过了事件路径**，「组没跟上」可能只是
#:   「我绕过了 fit 的触发点」，不是应用缺缺陷。
DRAG = """(ids)=>{
  const e=document.querySelector('.react-flow__node[data-id="'+ids[0]+'"]');
  if(!e) return {FAILED:'no dom node'};
  const r=e.getBoundingClientRect();
  return {x:Math.round(r.left+r.width/2), y:Math.round(r.top+20),
          w:Math.round(r.width), h:Math.round(r.height)};}"""


def drag_member(pg, node_id, dx, dy):
    """用真 pointer 事件把成员拖走 ⟹ 走完整的 `onNodesChange` 路径。"""
    box = pg.evaluate(DRAG, [node_id])
    if box.get("FAILED"):
        return box
    pg.mouse.move(box["x"], box["y"])
    pg.wait_for_timeout(200)
    pg.mouse.down()
    for i in range(1, 9):                      # 分步移动，react-flow 要看到连续事件
        pg.mouse.move(box["x"] + dx * i / 8.0, box["y"] + dy * i / 8.0)
        pg.wait_for_timeout(60)
    pg.mouse.up()
    pg.wait_for_timeout(900)
    return {"ok": True, "from": [box["x"], box["y"]], "拖了": [dx, dy]}


ARMS = ["badBox", "seeds", "freshDerived", "dragMember", "shrinkGroup"]


def run_arm(b, arm):
    pg = b.new_page()
    pg.set_default_timeout(30000)
    try:
        boot(pg)
        cell = {"arm": arm}

        # ── 臂 0 / 3 / 4：先把组造出来（两个种子节点）
        if arm in ("badBox", "dragMember", "shrinkGroup"):
            g = make_group(pg, SEEDS[:2], arm)
            if g.get("FAILED"):
                return {**cell, **g}
            gid, kids = g["groupId"], SEEDS[:2]
        elif arm == "seeds":
            g = make_group(pg, SEEDS[2:4], arm)
            if g.get("FAILED"):
                return {**cell, **g}
            gid, kids = g["groupId"], SEEDS[2:4]
        elif arm == "freshDerived":
            # ★ 新鲜创建的派生节点：先逐帧拉片，再把它与一个种子节点组合
            pg.evaluate(SELECT, [VID])
            pg.wait_for_timeout(700)
            v = ensure_visible(pg, VID)
            if not v.get("★ 在视口内"):
                return {**cell, "FAILED": "视频节点不在视口"}
            pg.evaluate(PREP_READY, VID)
            pg.wait_for_timeout(800)
            for t in pg.query_selector_all("button"):
                if (t.text_content() or "").strip() == "逐帧拉片":
                    t.click()
                    break
            pg.wait_for_timeout(1200)
            nodes = pg.evaluate(NODES)
            sb = [n for n in nodes if n["type"] == "shot-breakdown"]
            if not sb:
                return {**cell, "FAILED": "逐帧拉片没造出节点"}
            sb_id = sb[0]["id"]
            g = make_group(pg, [sb_id, SEEDS[2]], arm)
            if g.get("FAILED"):
                return {**cell, **g}
            gid, kids = g["groupId"], [sb_id, SEEDS[2]]
        else:
            return {**cell, "FAILED": "未知臂 %r" % arm}

        cell["groupId"] = gid
        cell["kids"] = kids
        cell["扰动前"] = snapshot(pg, gid, kids)

        # ── 施加扰动
        if arm == "badBox":
            # ★ 阳性对照：把组框改成明显错的 10×10
            r = pg.evaluate(PATCH_READ, [{"id": gid, "wh": [10, 10]}])
        elif arm == "dragMember":
            # ★ 真拖拽：把成员拖出组框（757 的场景），走**完整事件路径**
            r = drag_member(pg, kids[0], 501, 233)
        elif arm == "shrinkGroup":
            r = pg.evaluate(PATCH_READ, [{"id": gid, "wh": [40, 40]}])
        else:
            r = {"ok": True, "note": "无扰动（基线臂）"}
        # ★ 扰动**瞬间**的读数：等 600ms 之后再看，可能已经有人把框修回去了，
        #   那样就分不清「扰动没生效」与「生效了又被 fit 修回」。
        # ★ 瞬间读数改成**同一个** evaluate 里的同步读（见 PATCH_READ 的注释）
        cell["扰动瞬间"] = {
            "组": [{"id": t["id"], "w": t["w"], "h": t["h"],
                    "pos": t["pos"],
                    "abs": {"x": t["pos"]["x"], "y": t["pos"]["y"], "depth": 0}}
                   for t in (r.get("touched") or []) if t and t["id"] == gid],
            "DOM": None,
            "★ 读法": "setNodes 之后同步 getState（React 还没跑）"}
        pg.wait_for_timeout(600)
        cell["扰动"] = r
        cell["观测"] = snapshot(pg, gid, kids)
        return cell
    except Exception as e:  # noqa: BLE001
        return {"arm": arm, "FAILED": "%s: %s" % (type(e).__name__, e)}
    finally:
        try:
            pg.close()
        except Exception:  # noqa: BLE001
            pass


def main():
    rounds = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        for rd in range(2):
            cells = []
            for arm in ARMS:
                t0 = time.time()
                c = run_arm(b, arm)
                c["secs"] = round(time.time() - t0, 1)
                cells.append(c)
                g = (c.get("观测") or {}).get("组") or {}
                print("rd%d %-14s %s  组框 %s×%s @%s (%.0fs)" % (
                    rd, arm, c.get("FAILED") or "ok",
                    g.get("w"), g.get("h"),
                    list((g.get("pos") or {}).values()), c["secs"]), flush=True)
            rounds.append({"round": rd, "cells": cells})
        b.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"base": A.BASE, "rounds": rounds},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("written", OUT)


if __name__ == "__main__":
    main()
