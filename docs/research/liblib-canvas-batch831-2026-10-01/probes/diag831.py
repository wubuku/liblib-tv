#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断：clone 4317 上「帮助」按钮被谁挡住了。"""
import json
import pathlib

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"

DUMP = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const btn=document.querySelector('[data-director-rail-entry="help"]');
  if(!btn) return {found:false};
  const b=box(btn);
  const cx=Math.round(b.x+b.w/2), cy=Math.round(b.y+b.h/2);
  const top=document.elementFromPoint(cx,cy);
  const chain=[];
  let e=top;
  for(let i=0;e&&i<6;i++,e=e.parentElement){
    chain.push({tag:e.tagName,cls:String(e.className||'').slice(0,70),
                aria:e.getAttribute('aria-label')||'',
                role:e.getAttribute('role')||'',
                box:box(e)});
  }
  // 该点上所有元素的命中测试
  const all=document.elementsFromPoint(cx,cy).slice(0,8).map(e=>({
    tag:e.tagName,cls:String(e.className||'').slice(0,60),
    aria:e.getAttribute('aria-label')||'',role:e.getAttribute('role')||'',
    z:getComputedStyle(e).zIndex,pos:getComputedStyle(e).position,
    pe:getComputedStyle(e).pointerEvents,box:box(e)}));
  return {found:true,btn:{box:b,vis:getComputedStyle(btn).visibility,
                          op:getComputedStyle(btn).opacity,
                          pe:getComputedStyle(btn).pointerEvents},
          point:[cx,cy], topChain:chain, hitStack:all};
}"""


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        page = br.new_page(viewport={"width": 1920, "height": 1080},
                           device_scale_factor=1)
        page.goto(f"{BASE}/?batch831d=1", wait_until="networkidle", timeout=90_000)
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
        page.wait_for_timeout(1_800)
        out = page.evaluate(DUMP)
        print(json.dumps(out, ensure_ascii=False, indent=1))
        page.screenshot(path="/tmp/liblib_clone_desk831_helpbtn.png")
        br.close()


if __name__ == "__main__":
    main()
