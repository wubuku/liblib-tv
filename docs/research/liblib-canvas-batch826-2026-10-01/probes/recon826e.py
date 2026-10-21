#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 826 源站取证⑤：把源站「素材库」popover 的**三枚**入口逐枚读出来。

★ 上一版（recon826c）只做了**子串搜索**，拿不到「就是这三枚」的完整清单
⟹ 本版：从锚点（逐字等于「风格库」的元素）**往上**定位到那个
  **240×220 的 fixed z-20 容器**，再枚举它里面的每一枚按钮。

★ 硬约束：不点生成/付费按钮。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_asset826e.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

READ = """()=>{
  const out={};
  const vis=(e)=>{const cs=getComputedStyle(e);
    return cs.visibility!=='hidden'&&cs.display!=='none'
      && Number(cs.opacity||'1')>0 && e.getBoundingClientRect().width>0;};
  // ★ 锚点：逐字等于「风格库」的可见元素
  let anchor=null;
  for(const e of document.querySelectorAll('span,div,button,p')){
    if((e.textContent||'').trim()!=='风格库')continue;
    if(!vis(e))continue;
    anchor=e;break;
  }
  out['锚点']=!!anchor;
  if(!anchor) return out;
  // ★ 往上：第一个「含锚点 + 宽在 200..400 + 高在 150..320」的祖先
  let p=anchor, root=null, chain=[];
  for(let i=0;i<12&&p;i++){
    const r=p.getBoundingClientRect();
    chain.push({tag:p.tagName,w:Math.round(r.width),h:Math.round(r.height),
      pos:getComputedStyle(p).position,z:getComputedStyle(p).zIndex});
    if(r.width>=200&&r.width<=400&&r.height>=150&&r.height<=320){root=p;break;}
    p=p.parentElement;
  }
  out['祖先链']=chain;
  if(!root){out['popover']=null;return out;}
  const r=root.getBoundingClientRect();
  out['popover']={tag:root.tagName,
    rect:{x:Math.round(r.x),y:Math.round(r.y),
          w:Math.round(r.width),h:Math.round(r.height)},
    cls:(root.getAttribute('class')||'').slice(0,200),
    bg:getComputedStyle(root).backgroundColor,
    radius:getComputedStyle(root).borderRadius};
  // ★ popover 里的每一枚按钮
  const items=[];
  for(const e of root.querySelectorAll('button')){
    const br=e.getBoundingClientRect();
    const t=(e.textContent||'').trim().replace(/\\s+/g,' ');
    const svg=e.querySelector('svg');
    const sr=svg?svg.getBoundingClientRect():null;
    // 叶子文本（标题/副标分开读）
    const leaves=[...e.querySelectorAll('span,div')]
      .filter(x=>x.children.length===0&&vis(x))
      .map(x=>(x.textContent||'').trim()).filter(Boolean);
    items.push({text:t, leaves:leaves.slice(0,6),
      hasNEW: t.indexOf('NEW')>=0,
      svg: sr? [Math.round(sr.width*10)/10, Math.round(sr.height*10)/10]:null,
      rect:{x:Math.round(br.x),y:Math.round(br.y),
            w:Math.round(br.width),h:Math.round(br.height)},
      可见:vis(e)});
  }
  out['入口']=items;
  // ★ popover 顶部标题
  const h=root.querySelector('h1,h2,h3,h4,[class*="font-medium"]');
  out['标题']=h?(h.textContent||'').trim():null;
  return out;}"""

cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
log = {}

with sync_playwright() as pw:
    br = pw.chromium.launch(headless=True)
    ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                          user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X "
                                      "10_15_7) AppleWebKit/537.36 (KHTML, like "
                                      "Chrome/134.0.0.0 Safari/537.36"),
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

    el = pg.query_selector('[data-sidebar-btn="open-asset"]')
    if el:
        bb = el.bounding_box()
        if bb:
            pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
    pg.wait_for_timeout(3500)
    log["素材库popover"] = pg.evaluate(READ)
    br.close()

OUT.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(log, ensure_ascii=False, indent=1)[:5000])
