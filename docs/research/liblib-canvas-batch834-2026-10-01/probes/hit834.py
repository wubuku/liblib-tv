#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 834 诊断：clone 的引导按钮**为什么点不动**（命中测试）。"""
import json
import pathlib

from playwright.sync_api import sync_playwright

OUT = pathlib.Path("/tmp/liblib_clone_guide834_hit.json")
BASE = "http://localhost:4317"

DUMP_HIT = """()=>{
  const b=document.querySelector('[data-director-timeline-guide-next]');
  if(!b) return {found:false};
  const r=b.getBoundingClientRect();
  const cx=Math.round(r.left+r.width/2), cy=Math.round(r.top+r.height/2);
  const at=document.elementFromPoint(cx,cy);
  const stack=document.elementsFromPoint(cx,cy).slice(0,6).map(e=>({
    tag:e.tagName, cls:String(e.className||'').slice(0,70),
    pe:getComputedStyle(e).pointerEvents, z:getComputedStyle(e).zIndex,
    pos:getComputedStyle(e).position,
  }));
  const bubble=document.querySelector('[data-director-timeline-guide-bubble]');
  const ov=document.querySelector('[data-director-timeline-guide-overlay]');
  return {found:true, cx, cy, inViewport: cy>=0 && cy<=innerHeight,
          hit: at? {tag:at.tagName, cls:String(at.className||'').slice(0,90),
                    pe:getComputedStyle(at).pointerEvents}: null,
          stack,
          buttonPE:getComputedStyle(b).pointerEvents,
          bubblePE:bubble?getComputedStyle(bubble).pointerEvents:null,
          bubbleZ:bubble?getComputedStyle(bubble).zIndex:null,
          overlayPE:ov?getComputedStyle(ov).pointerEvents:null,
          overlayZ:ov?getComputedStyle(ov).zIndex:null,
          bubbleBox: bubble? (()=>{const q=bubble.getBoundingClientRect();
            return {x:Math.round(q.x),y:Math.round(q.y),w:Math.round(q.width),h:Math.round(q.height)};})():null};
}"""


def main():
    out = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        page = br.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(f"{BASE}/?batch834h=1", wait_until="networkidle", timeout=90_000)
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
        page.wait_for_timeout(2_500)
        page.evaluate(
            "() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
        out["步0命中"] = page.evaluate(DUMP_HIT)
        # ★ 走到第 2 步（气泡更靠下）
        page.evaluate("() => { const b=document.querySelector"
                      "('[data-director-timeline-guide-next]'); if(b) b.click(); }")
        page.wait_for_timeout(1_200)
        out["步1命中"] = page.evaluate(DUMP_HIT)
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1)[:2500])


if __name__ == "__main__":
    main()
