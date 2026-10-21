#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 830 源站侦察①：导演台的「快捷键」面板与「时间轴缩放」控件。

★ 要回答的两件事：
  ① 源站导演台**有没有撤销栈** ⟹ i18n 有 `directorShortcutUndo = 撤销` ⟹ 有 ⟹
     但**按键是哪个**、**撤销能不能真的回退**，要看活体。
  ② batch 599/604 说的那个「zoom」＝ i18n 的 `directorTimelineZoom = 时间轴缩放`
     ⟹ 与 829 测的「场景缩放」（3D 视口）**不是同一个控件** ⟹ 要定位它。
★ 纪律：不点任何生成/付费控件。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk830_recon.json")
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
  const out={};
  out['可见按钮']=Array.from(document.querySelectorAll('button'))
    .filter(e=>realVis(e))
    .map(e=>({text:txt(e).slice(0,14),aria:e.getAttribute('aria-label')||'',
              title:e.getAttribute('title')||'',box:box(e)}))
    .filter(b=>b['text']||b['aria']||b['title']).slice(0,80);
  out['带aria的range']=Array.from(document.querySelectorAll('input[type=range]'))
    .filter(e=>realVis(e)||e.getAttribute('aria-label')||e.getAttribute('title'))
    .map(e=>({aria:e.getAttribute('aria-label')||'',
              title:e.getAttribute('title')||'',
              min:e.min,max:e.max,step:e.step,value:e.value,box:box(e),
              visible:realVis(e)}));
  // 找「时间轴缩放」这个 aria
  out['时间轴缩放命中']=Array.from(document.querySelectorAll(
      '[aria-label="时间轴缩放"],[title="时间轴缩放"]'))
    .map(e=>({tag:e.tagName,aria:e.getAttribute('aria-label')||'',
              title:e.getAttribute('title')||'',box:box(e),visible:realVis(e)}));
  // 面板类文字（找「快捷键」清单）
  out['含快捷键的文字']=Array.from(document.querySelectorAll('div,span,li,p,kbd'))
    .filter(e=>realVis(e)&&/快捷键|撤销|重做/.test(txt(e))&&txt(e).length<60)
    .map(e=>({t:txt(e).slice(0,40),tag:e.tagName,box:box(e)})).slice(0,40);
  return out;
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
        out["开台后"] = page.evaluate(DUMP)

        # ① 点「帮助」⟹ 找「快捷键」面板
        help_btn = page.locator("[aria-label='帮助']:visible").first
        help_btn.click()
        page.wait_for_timeout(2_500)
        out["点帮助后"] = page.evaluate(DUMP)
        page.screenshot(path="/tmp/liblib_source_desk830_help.png")

        # ② 关掉帮助浮层（Esc），再点「动画时间轴」
        page.keyboard.press("Escape")
        page.wait_for_timeout(1_500)
        tl = page.locator("[aria-label='动画时间轴']:visible").first
        tl.click()
        page.wait_for_timeout(4_000)
        out["点动画时间轴后"] = page.evaluate(DUMP)
        page.screenshot(path="/tmp/liblib_source_desk830_timeline.png")
        ctx.close()
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1)[:5000])


if __name__ == "__main__":
    main()
