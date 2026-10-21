#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 831：clone 的引导泡为什么跑到视口外（y=1749，视口只有 1080）。"""
import json
import pathlib

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"

DUMP = """()=>{
  const c=document.querySelector('[data-director-timeline-coachmark]');
  if(!c) return {found:false};
  const cs=getComputedStyle(c);
  const r=c.getBoundingClientRect();
  const chain=[];
  let e=c.parentElement;
  for(let i=0;e&&i<8;i++,e=e.parentElement){
    const s=getComputedStyle(e);
    const rr=e.getBoundingClientRect();
    chain.push({tag:e.tagName,cls:String(e.className||'').slice(0,70),
                position:s.position,transform:s.transform,
                filter:s.filter,perspective:s.perspective,
                contain:s.contain,willChange:s.willChange,
                height:s.height,box:{x:Math.round(rr.x),y:Math.round(rr.y),
                                    w:Math.round(rr.width),h:Math.round(rr.height)}});
  }
  return {found:true,
          box:{x:Math.round(r.x),y:Math.round(r.y),
               w:Math.round(r.width),h:Math.round(r.height)},
          computed:{position:cs.position,top:cs.top,left:cs.left,
                    inlineTop:c.style.top,inlineLeft:c.style.left,
                    width:cs.width},
          innerHeight:window.innerHeight,
          innerWidth:window.innerWidth,
          docH:document.documentElement.scrollHeight,
          bodyH:document.body.scrollHeight,
          chain:chain};
}"""


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        page = br.new_page(viewport={"width": 1920, "height": 1080},
                           device_scale_factor=1)
        page.goto(f"{BASE}/?batch831e=1", wait_until="networkidle", timeout=90_000)
        page.wait_for_function(
            "() => Boolean(window.__libtv_store && window.__libtv_ui_store "
            "&& window.__director_store)", timeout=60_000)
        page.wait_for_timeout(800)
        nid = page.evaluate("""() => {
          const nodes = window.__libtv_store.getState().getActiveCanvas().nodes
            .filter((n) => n.type === 'script-execution');
          return nodes.length === 1 ? nodes[0].id : null;
        }""")
        page.locator('.react-flow__node[data-id="%s"] [data-open-director]' % nid).first.click()
        page.locator("[data-director-workspace]").wait_for(state="visible", timeout=30_000)
        page.wait_for_timeout(2_000)
        print(json.dumps(page.evaluate(DUMP), ensure_ascii=False, indent=1))
        br.close()


if __name__ == "__main__":
    main()
