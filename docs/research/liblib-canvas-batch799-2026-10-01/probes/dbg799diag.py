#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 799 诊断：注入后到底**哪一拍**把组框从 10x10 变成贴合值的？

`setNodes`（`canvasStore.ts:3605`）逐行读过，里面**没有** fit；
全仓 `fitStoryboardGroupsToChildren` 只有 4 个调用点（3345/3381/3437/3820），
都不在 `setNodes` 上。但 `nestedOrigin` 臂「注入」那一步读数已经是贴合态
（`inner 680x180`）⟹ **有什么东西在注入之后动了框**。

本诊断**只采集，不下结论**：
  · t=0     —— 同一个 evaluate tick 内立刻读（能看见 `setNodes` 的同步效果）
  · t=30 / 250 / 700 / 1500
另外记 `width` / `style.width` / `measured`，用来分辨框的新尺寸是
「fit 算出来的」还是「DOM 量出来后被写回 store 的」。

★ 读数逻辑 `_READ_JS` 只有**一份**，注入臂与后续读数由它拼出来
  ⟹ 不存在两套口径。
"""
import json
import pathlib
import sys
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch774-2026-10-01" / "probes"))
import dbg774a as A  # noqa: E402

OUT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/research/"
                   "liblib-canvas-batch799-2026-10-01/raw/vb799diag-%s.json"
                   % (sys.argv[1] if len(sys.argv) > 1 else "post"))

#: ★ 全文件唯一的读数实现
_READ_JS = """
  const S=window.__libtv_store.getState();
  const cv=S.canvases.find(c=>c.id===S.activeCanvasId)||S.canvases[0];
  const byId=new Map(cv.nodes.map(n=>[n.id,n]));
  const abs=(n)=>{let x=n.position.x,y=n.position.y,p=n.parentId;
    const seen=new Set([n.id]); let d=0;
    while(p&&!seen.has(p)&&d<32){seen.add(p);d+=1;
      const q=byId.get(p); if(!q)break; x+=q.position.x;y+=q.position.y;p=q.parentId;}
    return {x:x,y:y};};
  return cv.nodes.map(n=>({id:n.id, type:n.type, parentId:n.parentId||null,
    rel:{x:n.position.x,y:n.position.y}, abs:abs(n),
    w:n.width, h:n.height,
    styleW:(n.style||{}).width, styleH:(n.style||{}).height,
    measuredW:(n.measured||{}).width, measuredH:(n.measured||{}).height,
  })).sort((a,b)=>String(a.id)<String(b.id)?-1:1);
"""

_INJECT_JS = """
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
  const nodes=[g('g-outer',[spec.ox,spec.oy],null,'外层'),
               g('g-inner',[40,40],'g-outer','内层'),
               t('n-m1',[40,40],'g-inner'),
               t('n-m2',[440,40],'g-inner'),
               t('n-loose',[40,440],'g-outer')];
  st.getState().setNodes(nodes);
"""

#: ★ 注入 + 同一 tick 内立刻读
_READ_FN = "()=>{" + _READ_JS + "\n}"

INJECT_AND_READ0 = ("(spec)=>{\n  const read_=" + _READ_FN + ";\n"
                    + _INJECT_JS + "\n  return read_();\n}")

READ = _READ_FN


def main():
    res = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        for ox, oy, tag in ((0, 0, "origin"), (200, 150, "offset")):
            pg = b.new_page()
            pg.set_default_timeout(60000)
            pg.goto(A.BASE, wait_until="domcontentloaded", timeout=90000)
            pg.evaluate(A.CLEAR_LS, A.LS_KEY)
            pg.set_viewport_size({"width": 1440, "height": 1000})
            pg.goto(A.BASE, wait_until="networkidle", timeout=90000)
            pg.wait_for_selector(".react-flow__node", timeout=25000)
            pg.wait_for_timeout(1300)
            pg.keyboard.press("Meta+0")
            pg.wait_for_timeout(700)

            t0 = pg.evaluate(INJECT_AND_READ0, {"ox": ox, "oy": oy})
            seq = [{"t": 0, "nodes": t0}]
            for ms in (30, 250, 700, 1500):
                pg.wait_for_timeout(ms - seq[-1]["t"])
                seq.append({"t": ms, "nodes": pg.evaluate(READ)})
            res.append({"tag": tag, "ox": ox, "oy": oy, "seq": seq})
            for s in seq:
                gs = " ｜ ".join(
                    "%s rel(%s,%s) abs(%s,%s) w=%s h=%s styleW=%s mW=%s mH=%s" % (
                        n["id"], n["rel"]["x"], n["rel"]["y"],
                        n["abs"]["x"], n["abs"]["y"], n["w"], n["h"],
                        n["styleW"], n["measuredW"], n["measuredH"])
                    for n in s["nodes"] if n["type"] == "storyboard-group")
                print("  [%s] t=%-5s %s" % (tag, s["t"], gs), flush=True)
            pg.close()
        b.close()
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
