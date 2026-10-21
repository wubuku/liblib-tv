#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最小诊断：机位属性面板里到底有哪些 input（两个选择器各跑一次）。"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
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
  const all=Array.from(document.querySelectorAll('input')).map(e=>{
    const r=e.getBoundingClientRect();
    return {type:e.type, value:e.value, x:Math.round(r.x), y:Math.round(r.y),
            w:Math.round(r.width), h:Math.round(r.height),
            vis:realVis(e),
            attrs:[...e.attributes].map(a=>a.name+'='+a.value).slice(0,3)};
  });
  return {all: all, textInputsX: all.filter(e=>e.type==='text').map(e=>[e.x,e.y,e.vis])};
}"""


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
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
        print("== 开台后（未选机位）==")
        d = page.evaluate(DUMP)
        print("  text inputs:", d["textInputsX"])
        page.locator("text=机位1").first.click()
        page.wait_for_timeout(2_500)
        print("== 选中机位1 后 ==")
        d = page.evaluate(DUMP)
        print("  text inputs:", d["textInputsX"])
        for e in d["all"]:
            if e["x"] > 1600:
                print("   ", e)
        ctx.close()
        br.close()


if __name__ == "__main__":
    main()
