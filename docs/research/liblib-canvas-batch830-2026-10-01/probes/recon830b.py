#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 830 源站侦察②：点开「帮助」⟹ 「快捷键」页签 ⟹ 读出**撤销的按键**。

★ i18n 有 `directorShortcutUndo = 撤销` ⟹ 源站导演台**有撤销** ⟹ 现在要拿到：
  ① 它绑的是哪个键（面板里会写出来）
  ② 「快捷键」页签与「使用教程」页签怎么切
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk830_shortcuts.json")
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
  // 浮层里所有可见文字（叶子节点）
  const leaves=Array.from(document.querySelectorAll('div,span,li,p,kbd,button'))
    .filter(e=>realVis(e)&&e.children.length===0&&txt(e).length>0)
    .map(e=>({t:txt(e).slice(0,28),tag:e.tagName,box:box(e)}));
  // 浮层里带 kbd 的行（快捷键常这样渲染）
  const kbdRows=Array.from(document.querySelectorAll('kbd'))
    .filter(e=>realVis(e))
    .map(e=>({t:txt(e),box:box(e),
              parentText:txt(e.parentElement||e).slice(0,40)}));
  return {leaves:leaves.slice(0,120), kbdRows:kbdRows.slice(0,40),
          kbd总数:document.querySelectorAll('kbd').length};
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
        page.locator("[aria-label='帮助']:visible").first.click()
        page.wait_for_timeout(2_500)
        out["打开帮助后"] = page.evaluate(DUMP)
        page.screenshot(path="/tmp/liblib_source_desk830_help2.png")
        # 点「快捷键」页签
        try:
            page.locator("text=快捷键").first.click()
            page.wait_for_timeout(2_000)
            out["点快捷键页签后"] = page.evaluate(DUMP)
            page.screenshot(path="/tmp/liblib_source_desk830_shortcuts.png")
        except Exception as exc:  # noqa: BLE001
            out["点快捷键页签失败"] = str(exc)[:300]
        ctx.close()
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in out.items():
        if k == "打开帮助后" or k == "点快捷键页签后":
            print("==", k, "kbd 总数:", v.get("kbd总数"))
            for r in v.get("kbdRows", []):
                print("   kbd:", r)
        else:
            print("==", k, str(v)[:200])


if __name__ == "__main__":
    main()
