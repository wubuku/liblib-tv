#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 809 探针 —— 802 遗留的 7 个高风险动作：**把宿主组挪两次，新节点必须跟着挪同样的量**

## 起点

802 用 AST 普查出 41 个写点／37 个动作，`createImageHdPreset` 是**唯一一个**
用 `source.position`（相对坐标）建顶层节点的，于是源节点只要在组里就错位。
修完之后，802 记了一条遗留：**剩下 7 个高风险动作只有静态证据**。

读源码，这 7 个**全都**用了 `getAbsoluteNodePosition`（绝对坐标）⟹ 静态看着都对。
按 794 立下的硬规矩（只有静态证据时报告不许说「验过了」），本批去取**行为证据**。

## ★ 判据（沿用 802 的等式，**不涉及任何常量**）

同一个动作，宿主组放在**两个不同**的位置各跑一次：

    新节点B.pos − 新节点A.pos  ==  源B.abs − 源A.abs        （逐位相等）

新节点的位置由**源的绝对位置**决定 ⟹ 宿主组挪 Δ，新节点就必须挪 Δ。
若实现用的是源的**相对**位置，新节点会纹丝不动 ⟹ 缺陷一眼可见。

★ 与 802 的区别：802 那条判的是「新组 == 源abs + (320,−60)」，要**先知道偏移常量**
才有判据；本条只比**两个位置之间**的差 ⟹ 偏移是 80 还是 120 还是别的都无所谓。
★ 这也是「**不预设常量**」那条纪律的落地：探针里一个偏移数字都没有。

## ★ 夹具（fixture，**不是被测行为**）

- 种子视频节点 `v-UGQZzZOpbv` 的 `status` 是 `"failed"`，而视频工具栏
  （`VideoNode.tsx:412`）要求 `"ready"` ⟹ 5 个走工具栏的动作需要补状态。
  ★ 这只是**把入口打开**，被判的是「动作把新节点放哪」。
- 动作 ⑦（`completeShotBreakdown`）的源是动作 ③ 造出来的 `shot-breakdown` 节点，
  它天生是**顶层**节点 ⟹ 要测「组内」这一档，得给它注入一个宿主组（802 同款做法）。

## ★ 记两个状态

沿用 806 的纪律：**条件渲染的入口会漏算** ⟹ 每个动作都记
「动作前有哪些入口／动作后新建了什么」，而不只是记动作后的节点。
"""
import json
import pathlib
import sys
import time
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch774-2026-10-01" / "probes"))
import dbg774a as A  # noqa: E402

import os
OUT = pathlib.Path(os.environ.get("VB809_OUT") or
                      (pathlib.Path(__file__).resolve().parent.parent
                       / "raw" / "vb809a.json"))
#: ★ 全链阴性对照用：把两臂的宿主组位置改成**同一个** ⟹ 探针真的没挪成组，
#: 宿主组的两个位置。**只需要它们不同**，偏移常量不参与判据。
#:   整条链（探针 → raw → 验收器）必须自己翻红，而不是靠 raw 里的变异。
POS = ({"A": [300, 200], "B": [300, 200]} if os.environ.get("VB809_NOMOVE")
       else {"A": [300, 200], "B": [600, 500]})
VID = "v-UGQZzZOpbv"
GRP = "g-EFbbHpwq5w"


MOVE_GROUP = """(cfg)=>{const S=window.__libtv_store.getState();
  const cv=S.canvases.find(c=>c.id===S.activeCanvasId);
  if(!cv) return {FAILED:'no canvas'};
  // ★★ 探针返工 ①：`setNodes` 是**整表替换**（`canvasStore.ts:3645`
  //   `nodes: storedNodes`），**不是按 id 合并** ⟹ 只传一个组进去，
  //   整张画布就只剩那一个组，视频节点被我**自己抹掉**了。
  //   读数表现是「源节点不在画布上」——★ 第一版 28 条臂**全部**栽在这。
  //   教训同 807/808：**读数不对先怀疑自己的动作**。
  if(!cv.nodes.some(n=>n.id===cfg.id)) return {FAILED:'host group 不在画布上'};
  S.setNodes(cv.nodes.map(n=>n.id===cfg.id
    ? {...n,position:{x:cfg.x,y:cfg.y}} : n));
  return {ok:true,total:cv.nodes.length};}"""

PREP_READY = """(vid)=>{const S=window.__libtv_store.getState();
  window.__libtv_store.setState({canvases:S.canvases.map(c=>({...c,
    nodes:c.nodes.map(m=>m.id===vid?{...m,data:{...m.data,status:'ready'}}:m)}))});
  return {ok:true};}"""

#: ★ 探针返工 ⑤（**并且是一条方法论发现**）：第一版给 `shot-breakdown` 节点
#:   **注入**宿主组（`setNodes` 直接写 `parentId` + 相对 position）。
#:   store 侧完全正确（源与新节点都跟着组挪 Δ），
#:   **但 DOM 里的源节点纹丝不动** ⟹ DOM 相对位移差了一整个 300px。
#:   真因：React Flow 自己维护 `internals.positionAbsolute`，
#:   **改 `parentId` 不经过 `onNodesChange` 就不会同步到 DOM**。
#:   ⟹ 「注入 parentId」这个夹具**只对 store 判据有效、对 DOM 判据无效**。
#:   修法：改走 807 验证过的 **UI 造组**（选中两个散节点按 `G`）——
#:   组由 React Flow 自己建立 ⟹ DOM 与 store 一致。
MAKE_GROUP_VIA_UI = """(cfg)=>{const S=window.__libtv_store.getState();
  const cv=S.canvases.find(c=>c.id===S.activeCanvasId); if(!cv) return {FAILED:'no canvas'};
  const sb=cv.nodes.find(n=>n.id===cfg.sb);
  if(!sb) return {FAILED:'no shot-breakdown node'};
  // 找一个**不是组、也不是自己**的节点当搭子
  const mate=cv.nodes.find(n=>n.id!==cfg.sb&&n.type!=='storyboard-group');
  if(!mate) return {FAILED:'找不到搭子节点'};
  S.selectElements({nodeIds:[cfg.sb,mate.id],edgeIds:[]});
  return {ok:true,mate:mate.id};}"""

PARENT_OF = """(id)=>{const S=window.__libtv_store.getState();
  const cv=S.canvases.find(c=>c.id===S.activeCanvasId);
  const n=cv.nodes.find(x=>x.id===id);
  return {parentId:(n&&n.parentId)||null};}"""

SELECT = """(ids)=>{window.__libtv_store.getState()
  .selectElements({nodeIds:ids,edgeIds:[]}); return {ok:true};}"""

#: ★ 探针返工 ④（也是本批第一条**发现**）：种子里**已经有**一条
#:   image→video 的边（`e-OwhsBRzrTz`：`i-1FQ9tErTcC` → `v-UGQZzZOpbv`），
#:   于是 `createFirstFrameReference`／`createFirstLastFrameReference` 的
#:   `hasImageRef` 守卫**为真** ⟹ 只写 `attempt` 标签、**一个节点都不建**。
#:   第一版读到 `fresh=0` 时差点当成「功能坏了」。
#:   ⟹ 必须**记两个状态**（与 806「条件渲染要记两个状态」同款，只是这里是
#:   **条件分支**）：`keepRef` 记「有边时发生什么」，`dropRef` 才量到几何。
DROP_IMG_REF = """(vid)=>{const S=window.__libtv_store.getState();
  const cv=S.canvases.find(c=>c.id===S.activeCanvasId); if(!cv) return {FAILED:'no canvas'};
  const imgIds=new Set(cv.nodes.filter(n=>n.type==='image').map(n=>n.id));
  const dropped=cv.edges.filter(e=>e.target===vid&&imgIds.has(e.source));
  if(!dropped.length) return {FAILED:'没有 image→video 的边可删'};
  S.setEdges(cv.edges.filter(e=>!dropped.includes(e)));
  return {ok:true,dropped:dropped.map(e=>e.id)};}"""

NODES = """()=>{const S=window.__libtv_store.getState();
  const cv=S.canvases.find(c=>c.id===S.activeCanvasId)||S.canvases[0];
  const byId=new Map(cv.nodes.map(n=>[n.id,n]));
  const abs=(n)=>{let x=n.position.x,y=n.position.y,p=n.parentId;
    const seen=new Set([n.id]);let d=0;
    while(p&&!seen.has(p)&&d<32){seen.add(p);d+=1;const q=byId.get(p);if(!q)break;
      x+=q.position.x;y+=q.position.y;p=q.parentId;}
    return {x:x,y:y,depth:d};};
  return cv.nodes.map(n=>({id:n.id,type:n.type,parentId:n.parentId||null,
      pos:{x:n.position.x,y:n.position.y},abs:abs(n),w:n.width,h:n.height,
      gen:(n.data||{}).generatorType||null,
      cont:(n.data||{}).continuation?1:0,
      sb:(n.data||{}).sourceBreakdownId||null,
      attempt:(n.data||{}).attempt||null}));}"""

ENTRY = """()=>({
  attempt:Array.from(document.querySelectorAll('[data-video-attempt]'))
    .map(e=>(e.textContent||'').trim()),
  triggers:Array.from(document.querySelectorAll(
    '[data-video-subtitle-menu-trigger],[data-video-audio-menu-trigger],'
    +'[data-video-picture-edit-menu-trigger],[data-video-depth-motion-trigger],'
    +'[data-video-frame-menu-trigger]')).length,
  breakdownBtn:Array.from(document.querySelectorAll('button'))
    .filter(b=>(b.textContent||'').trim()==='逐帧拉片').length,
  contBtn:Array.from(document.querySelectorAll('button'))
    .filter(b=>(b.textContent||'').trim()==='智能续写').length,
  contSelector:document.querySelectorAll('[data-video-continuation-selector]').length,
  subtitlePanel:document.querySelectorAll('[data-subtitle-erase-panel]').length,
  shotStart:document.querySelectorAll('[data-shot-breakdown-start]').length,
})"""

DOMRECT = """(ids)=>{const out={};
  for(const id of ids){const e=document.querySelector(
    '[data-id="'+id+'"]')||document.querySelector('.react-flow__node[data-id="'+id+'"]');
    if(!e){out[id]=null;continue;}
    const r=e.getBoundingClientRect();
    out[id]={w:Math.round(r.width*100)/100,h:Math.round(r.height*100)/100,
             x:Math.round(r.left*100)/100,y:Math.round(r.top*100)/100};}
  return out;}"""


def boot(pg):
    pg.goto(A.BASE, wait_until="domcontentloaded", timeout=90000)
    pg.evaluate(A.CLEAR_LS, A.LS_KEY)
    pg.set_viewport_size({"width": 1440, "height": 1000})
    pg.goto(A.BASE, wait_until="networkidle", timeout=90000)
    pg.wait_for_selector(".react-flow__node", timeout=60000)
    pg.wait_for_timeout(1500)


def click_text(pg, text):
    for t in pg.query_selector_all("button"):
        if (t.text_content() or "").strip() == text:
            t.click()
            return True
    return False


#: ★ 探针返工 ③：把宿主组挪到 (300,200) 之后，画布的**平移/缩放还停在种子那套**
#:   （节点散布在 x≈100…3000）⟹ 源节点被挪到**视口外**，Playwright 直接报
#:   「element is outside of the viewport」点不动。
#:   修法：挪完组就 fit view（`Meta+0`），并且**逐次确认它真的进了视口** ——
#:   不确认就点，等于把「我点不到」和「功能坏了」混成同一个现象（805/807/808 同款）。
VIEWPORT = """()=>({w:window.innerWidth,h:window.innerHeight})"""

IN_VIEW = """(id)=>{const e=document.querySelector('.react-flow__node[data-id="'+id+'"]');
  if(!e) return {present:false};
  const r=e.getBoundingClientRect();
  return {present:true,x:r.left,y:r.top,w:r.width,h:r.height};}"""


def ensure_visible(pg, node_id, tries=4):
    """把 `node_id` 弄进视口。返回最后一次的读数。"""
    last = {}
    for _ in range(tries):
        last = pg.evaluate(IN_VIEW, node_id)
        if not last.get("present"):
            pg.wait_for_timeout(400)
            continue
        vp = pg.evaluate(VIEWPORT)
        inside = (last["x"] >= -2 and last["y"] >= -2
                  and last["x"] + last["w"] <= vp["w"] + 2
                  and last["y"] + last["h"] <= vp["h"] + 2)
        if inside:
            return {**last, "★ 在视口内": True, "尝试次数": 1}
        pg.keyboard.press("Meta+0")
        pg.wait_for_timeout(900)
    return {**last, "★ 在视口内": False, "视口": pg.evaluate(VIEWPORT)}


# ---------------------------------------------------------------- 七个动作
def t_first_frame(pg):
    pg.click('[data-video-attempt="首帧生成视频"]')
    pg.wait_for_timeout(900)


def t_first_last(pg):
    pg.click('[data-video-attempt="首尾帧生成视频"]')
    pg.wait_for_timeout(900)


def t_breakdown(pg):
    if not click_text(pg, "逐帧拉片"):
        raise RuntimeError("找不到「逐帧拉片」按钮")
    pg.wait_for_timeout(1100)


def t_continuation(pg):
    if not click_text(pg, "智能续写"):
        raise RuntimeError("找不到「智能续写」按钮")
    pg.wait_for_selector("[data-video-continuation-confirm]", timeout=20000)
    pg.click("[data-video-continuation-confirm]")
    pg.wait_for_timeout(900)


def t_subtitle(pg):
    pg.click("[data-video-subtitle-menu-trigger]")
    pg.wait_for_selector("[data-video-subtitle-mode]", timeout=20000)
    pg.click('[data-video-subtitle-mode="smart"]')
    pg.wait_for_selector("[data-subtitle-erase-submit]", timeout=20000)
    pg.click("[data-subtitle-erase-submit]")
    pg.wait_for_timeout(900)


def t_audio(pg):
    pg.click("[data-video-audio-menu-trigger]")
    pg.wait_for_selector("[data-video-audio-mode]", timeout=20000)
    pg.click('[data-video-audio-mode="av"]')
    # ★ createAudioSplit 走 acceptLibTVOperation，**有 600ms 延迟**
    #   （`VideoNode.tsx:248`），不等够就会读到「什么都没发生」。
    pg.wait_for_timeout(2600)


def t_shot_complete(pg):
    pg.click("[data-shot-breakdown-start]")
    pg.wait_for_timeout(1200)


#: (键, 动作名, 触发器, 是否需要 ready 夹具, 是否需要先造 shot-breakdown 节点,
#:  是否先删掉已有的 image→video 入边)
#:
#: ★ `firstFrame` / `firstLast` 各有**两条**臂：`keepRef` 记「种子已经有入边时
#:   发生什么」（读数是 fresh=0），`dropRef` 才量得到几何。
ACTIONS = [
    ("firstFrameKeepRef", "createFirstFrameReference(有 image 入边)",
     t_first_frame, False, False, False),
    ("firstFrame", "createFirstFrameReference", t_first_frame, False, False, True),
    ("firstLastKeepRef", "createFirstLastFrameReference(有 image 入边)",
     t_first_last, False, False, False),
    ("firstLast", "createFirstLastFrameReference", t_first_last, False, False, True),
    ("breakdown", "addDerivedNode(shot-breakdown)", t_breakdown, True, False, False),
    ("continuation", "createVideoContinuation", t_continuation, True, False, False),
    ("subtitle", "createSubtitleErase", t_subtitle, True, False, False),
    ("audio", "createAudioSplit", t_audio, True, False, False),
    ("shotComplete", "completeShotBreakdown", t_shot_complete, False, True, False),
]


def run_one(b, key, name, trig, need_ready, need_sb, pos_key,
             drop_ref=False):
    """在一个**全新页面**里跑：挪组 → 选中源 → 触发 → 读。"""
    pg = b.new_page()
    pg.set_default_timeout(30000)
    try:
        boot(pg)
        ox, oy = POS[pos_key]
        before_entry = None
        if need_sb:
            # ③ 先用 UI 造出 shot-breakdown 节点，再注入宿主组（fixture）
            pg.evaluate(SELECT, [VID])
            pg.wait_for_timeout(700)
            v0 = ensure_visible(pg, VID)
            if not v0.get("★ 在视口内"):
                return {"key": key, "pos": pos_key,
                        "FAILED": "造 shot-breakdown 前源节点不在视口：%r" % (v0,)}
            # ★ 探针返工 ②：种子视频是 `status:"failed"`，而「逐帧拉片」在
            #   工具栏里、工具栏要求 `status==="ready"` ⟹ 第一版报
            #   「找不到逐帧拉片按钮」。**又是入口没打开，不是功能坏。**
            pg.evaluate(PREP_READY, VID)
            pg.wait_for_timeout(800)
            t_breakdown(pg)
            sb = [n for n in pg.evaluate(NODES) if n["type"] == "shot-breakdown"]
            if not sb:
                return {"key": key, "pos": pos_key,
                        "FAILED": "逐帧拉片没造出 shot-breakdown 节点"}
            sb_id = sb[0]["id"]
            r = pg.evaluate(MAKE_GROUP_VIA_UI, {"sb": sb_id})
            if r.get("FAILED"):
                return {"key": key, "pos": pos_key, "FAILED": r["FAILED"]}
            pg.wait_for_timeout(800)
            # ★ 通过 UI 组合（807 验证过的路径：选中两个散节点按 `G`）
            pg.keyboard.press("g")
            pg.wait_for_timeout(1300)
            par = pg.evaluate(PARENT_OF, sb_id)
            if not par.get("parentId"):
                return {"key": key, "pos": pos_key,
                        "FAILED": "按 G 之后 shot-breakdown 仍没有父组（%r）" % (par,)}
            grp_id = par["parentId"]
            pg.evaluate(MOVE_GROUP, {"id": grp_id, "x": ox, "y": oy})
            pg.wait_for_timeout(800)
            src_id = sb_id
            v1 = ensure_visible(pg, src_id)
            if not v1.get("★ 在视口内"):
                return {"key": key, "pos": pos_key,
                        "FAILED": "注入宿主组后 shot-breakdown 节点不在视口：%r" % (v1,)}
        else:
            src_id = VID
            mg = pg.evaluate(MOVE_GROUP, {"id": GRP, "x": ox, "y": oy})
            pg.wait_for_timeout(700)
            # ★ 挪完组**立刻**确认源还在，别等跑完动作才发现画布被我抹了
            alive = pg.evaluate(NODES)
            if mg.get("FAILED") or not any(n["id"] == VID for n in alive):
                return {"key": key, "pos": pos_key,
                        "FAILED": "挪组后源节点不见了：%r / 画布剩 %d 个节点"
                                  % (mg.get("FAILED"), len(alive))}

        pg.evaluate(SELECT, [src_id])
        pg.wait_for_timeout(800)
        vis = ensure_visible(pg, src_id)
        if not vis.get("★ 在视口内"):
            return {"key": key, "pos": pos_key,
                    "FAILED": "源节点弄不进视口：%r" % (vis,)}
        if need_ready:
            pg.evaluate(PREP_READY, src_id)
            pg.wait_for_timeout(800)
        if drop_ref:
            dr_r = pg.evaluate(DROP_IMG_REF, src_id)
            if dr_r.get("FAILED"):
                return {"key": key, "pos": pos_key, "FAILED": dr_r["FAILED"]}
            pg.wait_for_timeout(600)
        before_entry = pg.evaluate(ENTRY)
        before = pg.evaluate(NODES)
        src = [n for n in before if n["id"] == src_id]
        if not src:
            return {"key": key, "pos": pos_key, "FAILED": "源节点不在画布上"}
        src = src[0]

        trig(pg)

        after_entry = pg.evaluate(ENTRY)
        after = pg.evaluate(NODES)
        before_ids = {n["id"] for n in before}
        fresh = [n for n in after if n["id"] not in before_ids]
        # ★ 807 的判据形状：光看「节点数没变」不够，得看**用户看得见的反馈**
        #   （芯片的 aria-pressed 与节点的 attempt 标签）才能判「静不静默」。
        src_after = [n for n in after if n["id"] == src_id]
        src_after = src_after[0] if src_after else None
        pressed = pg.evaluate("""()=>Array.from(document.querySelectorAll(
            '[data-video-attempt]')).map(e=>({label:(e.textContent||'').trim(),
            pressed:e.getAttribute('aria-pressed')}))""")
        # ★ 记**宿主组自己的框**（挪完组之后、动作之前那一刻读的）——
        #   有了它才能判「新节点有没有压在组上」这条用户看得见的读数。
        host_id = GRP if src_id == VID else grp_id
        host = [n for n in before if n["id"] == host_id]
        host = ({"pos": host[0]["pos"], "abs": host[0]["abs"],
                 "w": host[0]["w"], "h": host[0]["h"]} if host else None)
        # 排序必须**确定**：动作产物的相对次序在两次跑里是一样的
        fresh.sort(key=lambda n: (round(n["pos"]["y"], 3), round(n["pos"]["x"], 3)))
        dom = pg.evaluate(DOMRECT, [src_id] + [n["id"] for n in fresh])
        return {"key": key, "name": name, "pos": pos_key,
                "hostPos": [ox, oy], "srcId": src_id,
                "src": {"pos": src["pos"], "abs": src["abs"], "w": src["w"],
                        "attempt": src.get("attempt")},
                "srcAfter": ({"pos": src_after["pos"], "abs": src_after["abs"],
                              "attempt": src_after.get("attempt")}
                             if src_after else None),
                "chipsAfter": pressed, "host": host, "hostId": host_id,
                "beforeEntry": before_entry, "afterEntry": after_entry,
                "beforeCount": len(before), "afterCount": len(after),
                "fresh": [{"type": n["type"], "pos": n["pos"], "abs": n["abs"],
                           "w": n["w"], "h": n["h"], "gen": n["gen"],
                           "cont": n["cont"], "parentId": n["parentId"]}
                          for n in fresh],
                "dom": dom}
    except Exception as e:  # noqa: BLE001
        return {"key": key, "pos": pos_key,
                "FAILED": "%s: %s" % (type(e).__name__, e)}
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
            for key, name, trig, nr, ns, dr in ACTIONS:
                for pk in ("A", "B"):
                    t0 = time.time()
                    c = run_one(b, key, name, trig, nr, ns, pk, dr)
                    c["secs"] = round(time.time() - t0, 1)
                    cells.append(c)
                    print("rd%d %-13s %s  %s" % (rd, key, pk, c.get("FAILED")
                                                 or ("fresh=%d" % len(c.get("fresh", [])))),
                          flush=True)
            rounds.append({"round": rd, "cells": cells})
        b.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"base": A.BASE, "pos": POS, "rounds": rounds},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("written", OUT)


if __name__ == "__main__":
    main()
