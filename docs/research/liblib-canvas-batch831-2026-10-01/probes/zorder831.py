#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 831 诊断：源站时间轴**展开**时，rail 的「帮助」按钮还点得到吗？

★ 这个问题决定 clone 的做法：
  - 源站的时间轴默认**没开** ⟹ 「帮助」平时可达；
  - 若时间轴展开后源站的「帮助」被盖住 ⟹ clone（时间轴默认展开）就必然盖住
    ⟹ 那「帮助」在 clone 里就永远点不到 ⟹ 必须另找出路。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk831_help_zorder.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

DUMP = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const btn=document.querySelector('[aria-label="帮助"]');
  const b=box(btn);
  const cx=Math.round(b.x+b.w/2), cy=Math.round(b.y+b.h/2);
  const stack=document.elementsFromPoint(cx,cy).slice(0,8).map(e=>({
    tag:e.tagName,cls:String(e.className||'').slice(0,64),
    aria:e.getAttribute('aria-label')||'',
    z:getComputedStyle(e).zIndex,pos:getComputedStyle(e).position,
    box:box(e)}));
  // 找到盖住它的大块（时间轴）
  const cover=Array.from(document.querySelectorAll('section,div')).filter(e=>{
    const r=e.getBoundingClientRect();
    return r.width>800&&r.height>80&&r.top<=cy&&r.bottom>=cy
      &&r.left<=cx&&r.right>=cx;}).slice(0,6).map(e=>({
    tag:e.tagName,cls:String(e.className||'').slice(0,140),
    z:getComputedStyle(e).zIndex,pos:getComputedStyle(e).position,
    box:box(e)}));
  return {helpBox:b,point:[cx,cy],stack:stack,cover:cover};
}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(600)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(6_000)


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
        open_desk(page)
        out["①时间轴未开"] = page.evaluate(DUMP)
        # 打开时间轴
        if not page.evaluate(
                "()=>!!document.querySelector('[aria-label=\"时间轴缩放\"]')"):
            page.locator("[aria-label='动画时间轴']:visible").first.click()
            page.wait_for_timeout(3_500)
        out["②时间轴已开"] = page.evaluate(DUMP)
        page.screenshot(path="/tmp/liblib_source_desk831_zorder.png")
        ctx.close()
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已落盘：", OUT)


if __name__ == "__main__":
    main()
