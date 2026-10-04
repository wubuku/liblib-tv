#!/usr/bin/env python3
"""batch 763 探针 c：改变视口宽度后立刻 fitView，落点是否用旧容器宽度？

起因：763b 的 `click_real` 在 800px 下反复 FATAL，落在 x=596（0 命中、中心是 DIV）。
x=596 与同一次 fitView 正常的 x=276 **恰好差 320 = 1440/2 − 800/2**，
且按钮 rect 宽高完全一致（说明 zoom 相同 = 0.2396）⟹ 不是缩放算错，
是**居中偏移按 1440 算、却在 800 的 DOM 上生效**。

本探针正面量这个竞态：同一串动作（1440 加载 → Meta+0 → resize 800 → 等 delay →
Meta+0）跑一个 delay 矩阵，每个 delay 跑 2 轮。

判别量（每个 trial 一行）：
  btnX          按钮屏幕 x（fit-for-800 的期望值 276，旧宽度竞态的值 596）
  storeViewport store 里的 x/zoom（DOM 之外的第二份真相）
  zoomOK        zoom 是否等于 800 档期望的 0.2396
  centerHit     中心点是否真落在按钮上
  hitCount      按钮 rect 内扫网格的命中点数
  dialogOpen    此刻是否已有 dialog（排除「被导演台盖住」这个解释）

**只报实测，不解释。** 命中不了就是命中不了，如实记 0。
"""
import json
import pathlib
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch763-2026-10-01/raw/vb763c.json")

DELAYS = [0, 150, 400, 900]
ROUNDS = 2

PROBE = """()=>{
  const b=document.querySelector('[data-open-director]');
  if(!b) return {missing:true};
  const r=b.getBoundingClientRect();
  const st=window.__libtv_store.getState();
  const uis=window.__libtv_ui_store.getState();
  let hits=0;
  for(let f=0.08; f<=0.95; f+=0.07)
    for(let g=0.08; g<=0.95; g+=0.07){
      const x=Math.round(r.x+r.width*f), y=Math.round(r.y+r.height*g);
      if(x<2||y<2||x>innerWidth-2||y>innerHeight-2) continue;
      const e=document.elementFromPoint(x,y);
      if(e&&e.closest&&e.closest('[data-open-director]')) hits++;}
  const cx=Math.round(r.x+r.width/2), cy=Math.round(r.y+r.height/2);
  const top=(cx>1&&cy>1&&cx<innerWidth-1&&cy<innerHeight-1)
    ?document.elementFromPoint(cx,cy):null;
  return {vw:innerWidth,
    btnX:Math.round(r.x), btnY:Math.round(r.y),
    btnW:Math.round(r.width), btnH:Math.round(r.height),
    storeX:st.getActiveCanvas().viewport.x,
    storeY:st.getActiveCanvas().viewport.y,
    storeZoom:st.getActiveCanvas().viewport.zoom,
    uiZoom:uis.zoomLevel,
    zoomOK:Math.abs(st.getActiveCanvas().viewport.zoom-0.23962516733601072)<1e-6,
    centerHit:!!(top&&top.closest&&top.closest('[data-open-director]')),
    centerTag:top?top.tagName:null,
    hitCount:hits,
    dialogOpen:!!document.querySelector('[role="dialog"][aria-modal="true"]')};}"""


def trial(pg, delay):
    pg.goto(BASE, wait_until="networkidle")
    pg.wait_for_selector(".react-flow__node", timeout=25000)
    pg.wait_for_timeout(1200)
    pg.keyboard.press("Meta+0")
    pg.wait_for_timeout(900)
    pg.set_viewport_size({"width": 800, "height": 1000})
    pg.wait_for_timeout(delay)
    pg.keyboard.press("Meta+0")
    pg.wait_for_timeout(1000)
    r = pg.evaluate(PROBE)
    r["delay"] = delay
    r["btnXExpected"] = 276
    r["btnXStaleWidth"] = 596
    r["landed"] = ("staleWidth" if r.get("btnX") == 596
                   else "expected" if r.get("btnX") == 276 else "other")
    return r


def main():
    out = {"batch": 763, "probe": "c", "question":
           "改变视口宽度后立刻 fitView，落点是否用旧容器宽度？",
           "delaysMs": DELAYS, "rounds": ROUNDS, "trials": []}
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 1440, "height": 1000})
        for rd in range(1, ROUNDS + 1):
            for d in DELAYS:
                t = trial(pg, d)
                t["round"] = rd
                out["trials"].append(t)
                print("r%d delay=%-4s landed=%-11s btnX=%-4s zoomOK=%-5s "
                      "centerHit=%-5s hits=%-4s dialog=%s"
                      % (rd, d, t["landed"], t.get("btnX"), t.get("zoomOK"),
                         t.get("centerHit"), t.get("hitCount"),
                         t.get("dialogOpen")))
        br.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print("\nwrote %s" % OUT)


if __name__ == "__main__":
    main()
