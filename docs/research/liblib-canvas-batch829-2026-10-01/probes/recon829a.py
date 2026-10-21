#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 829 源站侦察①：源站导演台现在**是否可见**、长什么样、有没有「关闭」控件。

★ 背景：batch 599/604 留下同一条未观测项 ——「源站关闭再打开导演台时 zoom 是否保留，
  没有观测过」。batch 828 把 clone 侧测清楚了（同节点关台重开**保留**），本批去测源站。
★ 先做侦察：桌面在不在、可见吗、FOV 读面在哪、关/开控件是什么形态。
★ 硬约束：不点任何生成/付费按钮。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk829.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

READ = """()=>{
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

  // ① 找「3D导演台」这个 HEADER
  const all=Array.from(document.querySelectorAll('*'));
  const header=all.find(e=>e.children.length===0 && txt(e)==='3D导演台');
  out['header存在']=!!header;
  if(header){
    out['header可见']=realVis(header);
    out['header盒']=box(header);
    // 往上找浮层根（1920×880 那个）
    let p=header, root=null;
    for(let i=0;i<12&&p;i++){
      const r=p.getBoundingClientRect();
      if(r.width>900&&r.height>500){root=p;break;}
      p=p.parentElement;
    }
    if(root){
      out['浮层根盒']=box(root);
      out['浮层根class']=(root.getAttribute('class')||'').slice(0,140);
      out['浮层根可见']=realVis(root);
      out['浮层内canvas数']=root.querySelectorAll('canvas').length;
      // ② range / number 输入
      const ranges=Array.from(root.querySelectorAll('input[type=range]'))
        .map(e=>({...box(e),min:e.min,max:e.max,step:e.step,value:e.value,
                  visible:realVis(e),
                  cls:(e.getAttribute('class')||'').slice(0,80)}));
      out['range']=ranges;
      const nums=Array.from(root.querySelectorAll('input[type=number]'))
        .map(e=>({...box(e),value:e.value,visible:realVis(e),
                  ph:e.getAttribute('placeholder')||''}));
      out['number']=nums.slice(0,12);
      const texts=Array.from(root.querySelectorAll('input'))
        .map(e=>({type:e.type,value:e.value,visible:realVis(e),box:box(e)}));
      out['全部input']=texts.slice(0,20);
      // ③ 页签
      out['页签']=Array.from(root.querySelectorAll('[role=tab],button'))
        .filter(e=>realVis(e)&&/属性|截图|运动轨迹/.test(txt(e)))
        .map(e=>({text:txt(e).slice(0,12),box:box(e)}));
      // ④ 关/开控件
      out['按钮']=Array.from(root.querySelectorAll('button'))
        .filter(e=>realVis(e))
        .map(e=>({text:txt(e).slice(0,16),
                  aria:e.getAttribute('aria-label')||'',
                  title:e.getAttribute('title')||'',
                  box:box(e)}))
        .filter(b=>b['text']||b['aria']||b['title'])
        .slice(0,60);
    }
  }
  // ⑤ 画布上有没有「打开导演台」按钮
  out['打开导演台按钮']=Array.from(document.querySelectorAll('button'))
    .filter(e=>/打开导演台|导演台/.test(txt(e)))
    .map(e=>({text:txt(e).slice(0,20),box:box(e),visible:realVis(e)}));
  out['url']=location.href;
  out['localStorage键']=Object.keys(localStorage).slice(0,30);
  return out;
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
        try:
            page.wait_for_function(
                "() => Array.from(document.querySelectorAll('*'))"
                ".some(e => e.children.length === 0 && "
                "(e.textContent||'').trim() === '3D导演台')", timeout=40_000)
        except Exception as exc:  # noqa: BLE001
            print("等 3D导演台 超时：", str(exc)[:200])
        page.wait_for_timeout(3_000)
        data = page.evaluate(READ)
        page.screenshot(path="/tmp/liblib_source_desk829.png", full_page=False)
        ctx.close()
        br.close()
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(data, ensure_ascii=False, indent=1)[:4000])


if __name__ == "__main__":
    main()
