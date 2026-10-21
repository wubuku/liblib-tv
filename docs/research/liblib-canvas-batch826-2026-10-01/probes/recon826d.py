#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 826 源站取证④：点开角色造型面板 → 读两个页签各自的内容 + 结构。

★ 要回答：clone 的「公共角色库 / Seedance合规素材库」两页签
  在源站当前构建里**对应什么**（还是根本没有）。
★ 硬约束：不点生成/付费按钮。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_studio826d.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

READ = """()=>{
  const out={};
  const vis=(e)=>{const cs=getComputedStyle(e);
    return cs.visibility!=='hidden'&&cs.display!=='none'
      && Number(cs.opacity||'1')>0 && e.getBoundingClientRect().width>0;};
  // ★ 面板根：找含「我的角色库」的**可见**按钮，往上走到合适祖先
  let anchor=null;
  for(const e of document.querySelectorAll('button')){
    if((e.textContent||'').trim()==='我的角色库' && vis(e)){anchor=e;break;}
  }
  out['锚点']=!!anchor;
  if(!anchor){return out;}
  // 往上：取第一个「宽>800 且 高>400」的祖先
  let p=anchor, root=null;
  for(let i=0;i<15&&p;i++){
    const r=p.getBoundingClientRect();
    if(r.width>800&&r.height>400){root=p;break;}
    p=p.parentElement;
  }
  if(!root){out['面板根']=null;return out;}
  const rr=root.getBoundingClientRect();
  out['面板根']={tag:root.tagName,
    rect:{x:Math.round(rr.x),y:Math.round(rr.y),
          w:Math.round(rr.width),h:Math.round(rr.height)},
    cls:(root.getAttribute('class')||'').slice(0,240),
    bg:getComputedStyle(root).backgroundColor,
    radius:getComputedStyle(root).borderRadius};
  // ★ 全量可点元素（带位置），按 y 再 x 排
  const items=[];
  for(const e of root.querySelectorAll('button,a,[role=tab],[role=button],[role=switch],input,select')){
    if(!vis(e))continue;
    const r=e.getBoundingClientRect();
    const t=((e.getAttribute('aria-label')||'')+'|'
      +(e.getAttribute('placeholder')||'')+'|'
      +((e.textContent||'').trim().replace(/\\s+/g,' '))).replace(/\\|+/g,'|');
    items.push({tag:e.tagName,role:e.getAttribute('role')||'',
      aria:e.getAttribute('aria-label')||'',
      placeholder:e.getAttribute('placeholder')||'',
      type:e.getAttribute('type')||'',
      text:(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,30),
      testid:e.getAttribute('data-testid')||'',
      rect:{x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)},
      cls:(e.getAttribute('class')||'').slice(0,90)});
  }
  items.sort((a,b)=>(a.rect.y-b.rect.y)||(a.rect.x-b.rect.x));
  out['可点元素']=items.slice(0,80);
  // ★ 面板里所有**文本节点**（可见），用来读空态/文案
  const texts=[];
  for(const e of root.querySelectorAll('h1,h2,h3,h4,p,span,div')){
    if(!vis(e))continue;
    const t=(e.textContent||'').trim().replace(/\\s+/g,' ');
    if(!t||t.length>40)continue;
    if(e.children.length>0)continue;      // 只要叶子
    const r=e.getBoundingClientRect();
    texts.push({tag:e.tagName,text:t,
      rect:{x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)}});
  }
  texts.sort((a,b)=>(a.rect.y-b.rect.y)||(a.rect.x-b.rect.x));
  out['叶子文本']=texts.slice(0,80);
  return out;}"""

cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
log = {}

with sync_playwright() as pw:
    br = pw.chromium.launch(headless=True)
    ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                          user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X "
                                      "10_15_7) AppleWebKit/537.36 (KHTML, like "
                                      "Gecko) Chrome/134.0.0.0 Safari/537.36"),
                          locale="zh-CN")
    ctx.add_cookies([{"name": c["name"], "value": c["value"],
                      "domain": c["domain"], "path": c.get("path", "/")}
                     for c in cookies])
    pg = ctx.new_page()
    pg.set_default_timeout(20000)
    pg.goto(URL, wait_until="domcontentloaded", timeout=90_000)
    pg.wait_for_timeout(12_000)
    for label in ("下次再说",):
        el = pg.query_selector("text=%s" % label)
        if el:
            el.click()
            pg.wait_for_timeout(900)
            break

    el = pg.query_selector('[data-sidebar-btn="character-library"]')
    if el:
        bb = el.bounding_box()
        if bb:
            pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
    pg.wait_for_timeout(5000)
    log["A 我的角色库页签"] = pg.evaluate(READ)
    pg.screenshot(path="/tmp/liblib_source_studio_mine826.png")

    # ★ 点「官方角色库」页签
    el = pg.query_selector("button:text-is('官方角色库')")
    if el:
        bb = el.bounding_box()
        if bb:
            pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
            log["B 点了官方角色库"] = True
        else:
            log["B 官方角色库无矩形"] = True
    else:
        log["B 没找到官方角色库按钮"] = True
    pg.wait_for_timeout(4000)
    log["C 官方角色库页签"] = pg.evaluate(READ)
    pg.screenshot(path="/tmp/liblib_source_studio_official826.png")
    br.close()

OUT.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
print("saved", OUT)
