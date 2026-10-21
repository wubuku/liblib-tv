#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 831 微探针：源站快捷键对话框里**标题那 4px** 到底怎么回事。

★ clone 的 h2 盒在 85..107，源站在 81..103 ⟹ 差 4px，但两边的**两列完全一致**
  （123）⟹ 说明不是「整块偏移」，而是**标题这一件**偏了。
★ 要问的：对话框的 padding、标题行（h2 的父盒）、h2 自身的盒与计算样式。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk831_title.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

DUMP = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const d=Array.from(document.querySelectorAll('[role="dialog"]'))
    .filter(e=>e.getBoundingClientRect().width>0).pop();
  if(!d) return {found:false};
  const h2=d.querySelector('h2');
  const row=h2?h2.parentElement:null;
  const cs=(e)=>{const c=getComputedStyle(e);
    return {padding:c.padding,margin:c.margin,lineHeight:c.lineHeight,
            fontSize:c.fontSize,fontFamily:c.fontFamily,display:c.display,
            alignItems:c.alignItems,height:c.height,transform:c.transform,
            position:c.position,top:c.top};};
  return {found:true,
          dialog:{box:box(d),style:cs(d)},
          row:row?{tag:row.tagName,box:box(row),style:cs(row),
                    cls:String(row.className||'').slice(0,90),
                    kids:Array.from(row.children).map(k=>({
                      tag:k.tagName,t:(k.textContent||'').trim().slice(0,10),
                      box:box(k)}))}:null,
          h2:h2?{box:box(h2),style:cs(h2),
                 cls:String(h2.className||'').slice(0,90)}:null};
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
        page.locator("[aria-label='帮助']").first.click()
        page.wait_for_timeout(1_000)
        page.get_by_text("快捷键", exact=True).first.click()
        page.wait_for_timeout(1_500)
        out["标题"] = page.evaluate(DUMP)
        ctx.close()
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
