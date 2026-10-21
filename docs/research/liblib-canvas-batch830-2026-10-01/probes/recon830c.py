#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 830 源站侦察③：右栏「名称」输入到底长什么样（type? contenteditable?）。"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk830_nameinput.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

DUMP = """()=>{
  const realVis=(e)=>{
    for(let n=e;n&&n.nodeType===1;n=n.parentElement){
      const cs=getComputedStyle(n);
      if(cs.display==='none')return false;
      if(cs.visibility==='hidden')return false;
      if(Number(cs.opacity||'1')<=0.001)return false;
    }
    const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0;
  };
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\\s+/g,' ');
  const right=Array.from(document.querySelectorAll('input,textarea,[contenteditable="true"]'))
    .filter(e=>realVis(e)&&e.getBoundingClientRect().x>1600)
    .map(e=>({tag:e.tagName,type:e.type||'',value:e.value??e.textContent,
              ph:e.getAttribute('placeholder')||'',aria:e.getAttribute('aria-label')||'',
              title:e.getAttribute('title')||'',box:box(e)}));
  // 「名称」那一行的文字
  const nameRows=Array.from(document.querySelectorAll('div,span,label'))
    .filter(e=>realVis(e)&&e.children.length===0&&txt(e)==='名称')
    .map(e=>({box:box(e), parentHTML:(e.parentElement||e).outerHTML.slice(0,400)}));
  return {rightInputs:right, nameRows:nameRows};
}"""


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                             locale="zh-CN")
        ctx.add_cookies([{"name": c["name"], "value": c["value"],
                          "domain": c["domain"], "path": c.get("path", "/"),
                          "expires": c.get("expires", -1),
                          "httpOnly": c.get("httpOnly", False),
                          "secure": c.get("secure", False),
                          "sameSite": c.get("sameSite", "Lax")} for c in cookies])
        page = ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(12_000)
        card = page.locator(".react-flow__node-director-console-3d").first
        card.hover()
        page.wait_for_timeout(600)
        page.locator(
            ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
        page.wait_for_timeout(6_000)
        page.locator("text=机位1").first.click()
        page.wait_for_timeout(2_500)
        out = page.evaluate(DUMP)
        ctx.close()
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("右栏输入:", json.dumps(out["rightInputs"], ensure_ascii=False)[:1500])
    print("\n名称行数:", len(out["nameRows"]))
    for r in out["nameRows"][:2]:
        print("  ", r["box"], r["parentHTML"][:300])


if __name__ == "__main__":
    main()
