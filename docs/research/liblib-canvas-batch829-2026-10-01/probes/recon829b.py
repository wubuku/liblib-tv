#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 829 源站侦察②：点「打开导演台」能不能把源站导演台叫出来。

★ batch 581 记的是「点击无响应」（路由没变、窗口没开）——但那次它同时又发现
  导演台浮层**常驻 DOM** ⟹ 两件事其实不矛盾：可能真正打开它的是**别的入口**。
★ 本次按顺序试三条路，每条都只点**非生成、非付费**的控件：
  ① 直接点画布上的「打开导演台」
  ② 先点节点卡（选中）再点「打开导演台」
  ③ 找画布上「导演台」类节点本身的入口
★ 每一步都记录「3D导演台」是否出现在 DOM、浮层根的矩形、FOV 读数。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk829b.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

DESK_PROBE = """()=>{
  const out={};
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
  const all=Array.from(document.querySelectorAll('*'));
  const header=all.find(e=>e.children.length===0 && txt(e)==='3D导演台');
  out['header存在']=!!header;
  if(header){
    out['header可见']=realVis(header);
    let p=header, root=null;
    for(let i=0;i<12&&p;i++){
      const r=p.getBoundingClientRect();
      if(r.width>900&&r.height>500){root=p;break;}
      p=p.parentElement;
    }
    if(root){
      out['浮层根盒']=box(root);
      out['浮层根可见']=realVis(root);
      out['浮层内canvas数']=root.querySelectorAll('canvas').length;
      out['range']=Array.from(root.querySelectorAll('input[type=range]'))
        .map(e=>({...box(e),min:e.min,max:e.max,step:e.step,value:e.value,
                  visible:realVis(e)}));
      out['文本行']=Array.from(root.querySelectorAll('div,span,label,p'))
        .filter(e=>realVis(e)&&e.children.length===0&&txt(e).length>0&&txt(e).length<24)
        .map(e=>({t:txt(e),box:box(e)})).slice(0,40);
      out['关开控件']=Array.from(root.querySelectorAll('button'))
        .filter(e=>realVis(e))
        .map(e=>({text:txt(e).slice(0,14),
                  aria:e.getAttribute('aria-label')||'',
                  title:e.getAttribute('title')||'',box:box(e)}))
        .slice(0,50);
    }
  }
  return out;
}"""

CANVAS_NODES = """()=>{
  const out=[];
  for(const e of document.querySelectorAll('*')){
    const t=(e.textContent||'').trim();
    if(t && t.length<40 && /导演台/.test(t)){
      const r=e.getBoundingClientRect();
      out.push({t:t.slice(0,30),tag:e.tagName,
                cls:(e.getAttribute('class')||'').slice(0,60),
                box:{x:Math.round(r.x),y:Math.round(r.y),
                     w:Math.round(r.width),h:Math.round(r.height)}});
    }
  }
  return out.slice(0,30);
}"""


def click_open(page, log):
    btn = page.locator("button").filter(has_text="打开导演台").first
    n = btn.count()
    log.append({"step": "找到打开导演台按钮", "count": n})
    if n:
        btn.click()
        page.wait_for_timeout(4_000)


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

        out["初始"] = page.evaluate(DESK_PROBE)
        out["画布上的导演台相关元素"] = page.evaluate(CANVAS_NODES)

        log = []
        click_open(page, log)
        out["点按钮后"] = page.evaluate(DESK_PROBE)
        page.screenshot(path="/tmp/liblib_source_desk829b.png")

        # ② 再试：点节点卡选中后点按钮
        if not out["点按钮后"].get("header存在"):
            log.append({"step": "再试：点画布空白后重试"})
            page.mouse.move(1200, 600)
            page.mouse.click(1200, 600)
            page.wait_for_timeout(1_500)
            click_open(page, log)
            out["第二次点按钮后"] = page.evaluate(DESK_PROBE)
            page.screenshot(path="/tmp/liblib_source_desk829b2.png")

        out["过程"] = log
        ctx.close()
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1)[:5000])


if __name__ == "__main__":
    main()
