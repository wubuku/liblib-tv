#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 824 源站补测：TV Director 那枚按钮的**计算样式**与内部结构。

★ 为什么要补这一轮：
  第一次量源站只拿到「矩形 48×48 + aria-label + 3 个 svg」，
  但裁图放大（/tmp/liblib_source_tvzoom.png）看��——
  ★★ 它是一颗**青蓝渐变小球**，**外面套一个独立的深色圆形容器**，
  ★★ 而且**旁边没有任何可见文字**（DOM 读数里的 textContent "TV Director"
     是 **sr-only** 的，视觉上不渲染）。

  ⟹ 所以 clone 那枚不能做成「球 + 可见文字」，
  ⟹ 必须是「**独立圆钮 + 只图标 + text 转 sr-only**」。

★ 本探针要拿到的：
  ① 按钮的 computed：bg / border / radius / shadow / size
  ② 「TV Director」文字节点的承载元素是不是 sr-only（怎么藏的）
  ③ 内部 3 个 svg 分别是什么（尺寸/位置）
  ④ 与源站「教程」按钮的对比（源站按钮统一的 ghost 样式）
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_tvstyle.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

STYLE = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect();
    if(r.width===0&&r.height===0)return false;
    const cs=getComputedStyle(e);
    return cs.visibility!=='hidden'&&cs.display!=='none'
      && Number(cs.opacity||'1')>0;};
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const detail=(e)=>{if(!e)return null;const cs=getComputedStyle(e);
    return {tag:e.tagName, box:box(e),
      cls:(e.getAttribute('class')||'').slice(0,90),
      bg:cs.backgroundColor, bgImage:cs.backgroundImage.slice(0,140),
      border:cs.border, borderRadius:cs.borderRadius,
      boxShadow:cs.boxShadow.slice(0,120),
      position:cs.position, overflow:cs.overflow,
      w:cs.width, h:cs.height, padding:cs.padding,
      font:cs.fontSize+'/'+cs.lineHeight+'/'+cs.fontWeight,
      color:cs.color, opacity:cs.opacity, zIndex:cs.zIndex,
      pointerEvents:cs.pointerEvents,
      clipPath:cs.clipPath, clip:cs.clip,
      text:(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,30)};};

  const cap=document.querySelector('button[aria-label="TV Director"]');
  const help=document.querySelector('button[aria-label="教程"]');
  const out={};
  out['胶囊']=detail(cap);
  out['教程按钮']=detail(help);

  // ★ 内部结构：3 个 svg + 可能承载文字的元素
  if(cap){
    out['子元素']=Array.from(cap.children).map(detail);
    out['svg']=Array.from(cap.querySelectorAll('svg')).map((s,i)=>({
      i, box:box(s), cls:(s.getAttribute('class')||'').slice(0,60),
      fill:(s.getAttribute('fill')||''), viewBox:s.getAttribute('viewBox'),
      innerHTML:s.innerHTML.slice(0,120)}));
    // ★ 文字节点在哪个元素里？那个元素怎么隐藏的？
    const walker=document.createTreeWalker(cap,NodeFilter.SHOW_TEXT);
    let n, hits=[];
    while((n=walker.nextNode())){
      if((n.nodeValue||'').trim()) hits.push(n.nodeValue.trim());
    }
    out['文字节点']=hits;
    // 找第一个含 "TV Director" 文字的元素
    const holder=Array.from(cap.querySelectorAll('*')).find(
      e=>(e.textContent||'').trim()==='TV Director' && !Array.from(e.children)
        .some(c=>(c.textContent||'').trim()==='TV Director'));
    out['文字承载元素']=detail(holder);
    out['文字承载元素HTML']=holder?holder.outerHTML.slice(0,300):null;
    // ★ 球体的像素色：取按钮中心附近
    out['胶囊整段HTML']=cap.outerHTML.slice(0,900);
  }
  return out;}"""

cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
out = {}
with sync_playwright() as pw:
    br = pw.chromium.launch(headless=True)
    ctx = br.new_context(viewport={"width": 1600, "height": 950},
                          user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X "
                                      "10_15_7) AppleWebKit/537.36 (KHTML, like "
                                      "Gecko) Chrome/134.0.0.0 Safari/537.36"),
                          locale="zh-CN")
    ctx.add_cookies([{"name": c["name"], "value": c["value"],
                      "domain": c["domain"], "path": c.get("path", "/")}
                     for c in cookies])
    pg = ctx.new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=90_000)
    pg.wait_for_timeout(9000)
    for label in ("下次再说",):
        el = pg.query_selector("text=%s" % label)
        if el:
            el.click()
            pg.wait_for_timeout(900)
            break
    out = pg.evaluate(STYLE)
    br.close()

OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=1)[:4000])
