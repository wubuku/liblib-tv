#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 809 **侦察**探针 —— 802 遗留的 7 个高风险动作，入口到底可不可达

只做一件事：把 7 个动作的 UI 入口逐个探一遍，记下「能不能点到、点了之后
有没有新建节点、新建的是哪个」。**不做判据**（判据在 dbg809a）。

★ 沿用 806 的纪律：**条件渲染的入口会漏算** ⟹ 每个动作要记
  「动作前 / 动作后」两个状态的入口普查，而不是只记动作后。
"""
import json
import pathlib
import sys
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch774-2026-10-01" / "probes"))
import dbg774a as A  # noqa: E402

BASE = A.BASE
OUT = pathlib.Path(__file__).resolve().parent.parent / "raw" / "vb809recon.json"

VID = "v-UGQZzZOpbv"
GRP = "g-EFbbHpwq5w"

#: 把种子视频节点的状态补齐到能开工具栏的状态。
#:   ★ 这是**夹具（fixture）**，不是被测行为：被判的是「动作把新节点放哪」。
#:   工具栏 `VideoNode.tsx:412` 要求 `status === "ready"`，而种子是 `"failed"`。
PREP = """(vid)=>{
  const S=window.__libtv_store.getState();
  const cv=S.canvases.find(c=>c.id===S.activeCanvasId)||S.canvases[0];
  const n=cv.nodes.find(x=>x.id===vid); if(!n) return {FAILED:'no node'};
  window.__libtv_store.setState({canvases:S.canvases.map(c=>c.id===cv.id?{...c,
    nodes:c.nodes.map(m=>m.id===vid?{...m,data:{...m.data,status:'ready'}}:m)}:c)});
  return {ok:true, status:n.data.status};}"""

SELECT = """(ids)=>{const S=window.__libtv_store.getState();
  S.selectElements({nodeIds:ids,edgeIds:[]});
  return {sel:S.selectedNodeIds};}"""

SURVEY = """()=>{
  const sel=document.querySelectorAll('.react-flow__node.selected');
  const q=(s)=>Array.from(document.querySelectorAll(s)).map(e=>({
      tag:e.tagName.toLowerCase(),
      txt:(e.textContent||'').trim().slice(0,24),
      rect:(r=>({w:Math.round(r.width),h:Math.round(r.height)}))(e.getBoundingClientRect())}));
  return {
    selectedCount:sel.length,
    attempt:q('[data-video-attempt]'),
    toolbar:q('[data-video-subtitle-menu-trigger],[data-video-audio-menu-trigger],'
             +'[data-video-picture-edit-menu-trigger],[data-video-depth-motion-trigger],'
             +'[data-video-frame-menu-trigger]'),
    anyData:q('[data-video-toolbar-menu]'),
    breakdownByText:q('button').filter(b=>(b.textContent||'').trim()==='逐帧拉片'),
    contByText:q('button').filter(b=>(b.textContent||'').trim()==='智能续写'),
  };}"""

NODES = """()=>{const S=window.__libtv_store.getState();
  const cv=S.canvases.find(c=>c.id===S.activeCanvasId)||S.canvases[0];
  const byId=new Map(cv.nodes.map(n=>[n.id,n]));
  const abs=(n)=>{let x=n.position.x,y=n.position.y,p=n.parentId;const seen=new Set([n.id]);let d=0;
    while(p&&!seen.has(p)&&d<32){seen.add(p);d+=1;const q=byId.get(p);if(!q)break;
      x+=q.position.x;y+=q.position.y;p=q.parentId;}return{x:x,y:y,depth:d};};
  return cv.nodes.map(n=>({id:n.id,type:n.type,parentId:n.parentId||null,
      pos:{x:n.position.x,y:n.position.y},abs:abs(n),w:n.width,h:n.height,
      gen:(n.data||{}).generatorType||null,
      cont:(n.data||{}).continuation?1:0,
      sb:(n.data||{}).sourceBreakdownId||null}));}"""


def boot(pg):
    pg.goto(BASE, wait_until="domcontentloaded", timeout=90000)
    pg.evaluate(A.CLEAR_LS, A.LS_KEY)
    pg.set_viewport_size({"width": 1440, "height": 1000})
    pg.goto(BASE, wait_until="networkidle", timeout=90000)
    pg.wait_for_selector(".react-flow__node", timeout=60000)
    pg.wait_for_timeout(1500)
    pg.keyboard.press("Meta+0")
    pg.wait_for_timeout(700)


def main():
    out = {"base": BASE, "vid": VID, "grp": GRP, "steps": []}
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        pg = b.new_page()
        pg.set_default_timeout(30000)
        try:
            boot(pg)
            out["steps"].append({"s": "boot", "nodes": pg.evaluate(NODES)})
            # 选中视频节点
            out["steps"].append({"s": "select", "r": pg.evaluate(SELECT, [VID])})
            pg.wait_for_timeout(900)
            out["steps"].append({"s": "survey-selected(failed)", "r": pg.evaluate(SURVEY)})
            # 夹具：状态补到 ready
            out["steps"].append({"s": "prep", "r": pg.evaluate(PREP, VID)})
            pg.wait_for_timeout(900)
            out["steps"].append({"s": "survey-ready", "r": pg.evaluate(SURVEY)})
            # 逐帧拉片
            for t in pg.query_selector_all("button"):
                if (t.text_content() or "").strip() == "逐帧拉片":
                    t.click()
                    break
            pg.wait_for_timeout(1200)
            out["steps"].append({"s": "after-breakdown", "r": pg.evaluate(SURVEY),
                                 "nodes": pg.evaluate(NODES)})
        except Exception as e:  # noqa: BLE001
            out["FAILED"] = "%s: %s" % (type(e).__name__, e)
        finally:
            try:
                pg.close()
            except Exception:  # noqa: BLE001
                pass
            b.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1)[:6000])


if __name__ == "__main__":
    main()
