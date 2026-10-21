#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 826 源站取证①：画布底部工具条逐枚枚举 + 点开「角色造型室」看它开什么。

★ 目的：
  ① 源站底部工具条**逐枚**读数（文案／aria／data-sidebar-btn／矩形／图标）
     ⟹ 用来判断 clone 的「角色库」「打开工具箱」是否逐字对得上。
  ② 真实鼠标点开源站的**角色造型室** ⟹ 面板标题／页签／按钮全量读数
     ⟹ 用来判断 clone 的 CharacterLibraryPanel（标题「角色库」、页签
     「公共角色库 / Seedance合规素材库」）**对应的是源站哪一个东西**。

★ 硬约束：**不点任何生成/付费按钮**；只开面板、读结构、然后 Esc 关掉。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_rail826.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

READ_RAIL = """()=>{
  const vis=(e)=>{const cs=getComputedStyle(e);
    return cs.visibility!=='hidden'&&cs.display!=='none'
      && Number(cs.opacity||'1')>0;};
  const out={};
  out['url']=location.href;
  // ★ 工具条容器（源站叫 sidebar container）
  const ctr=document.querySelector('[data-sidebar-container]');
  out['容器']=ctr?{存在:true,
    rect:(()=>{const r=ctr.getBoundingClientRect();
      return {x:Math.round(r.x),y:Math.round(r.y),
              w:Math.round(r.width),h:Math.round(r.height)};})(),
    cls:(ctr.getAttribute('class')||'').slice(0,160),
    可见:vis(ctr)}:{存在:false};
  // ★ 逐枚：所有带 data-sidebar-btn* 的元素
  const btns=[];
  for(const e of document.querySelectorAll('[data-sidebar-btn],[data-guide-target]')){
    const r=e.getBoundingClientRect();
    btns.push({tag:e.tagName,
      key:e.getAttribute('data-sidebar-btn')||'',
      guide:e.getAttribute('data-guide-target')||'',
      aria:e.getAttribute('aria-label')||'',
      title:e.getAttribute('title')||'',
      text:(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,30),
      own:Array.from(e.childNodes).filter(n=>n.nodeType===3)
             .map(n=>n.textContent.trim()).join('|').slice(0,30),
      rect:{x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)},
      可见:vis(e)});
  }
  out['带sidebar-btn/guide-target的元素']=btns;
  // ★ 底部区域里所有可见按钮（含文字），按 x 排序
  const rail=[];
  for(const e of document.querySelectorAll('button,[role=button]')){
    const r=e.getBoundingClientRect();
    if(r.width===0||r.height===0)continue;
    if(r.y<window.innerHeight-140)continue;      // 只看最底下一条
    const t=((e.getAttribute('aria-label')||'')+'|'+((e.textContent||'')))
      .trim().replace(/\\s+/g,' ').slice(0,40);
    rail.push({tag:e.tagName,
      aria:e.getAttribute('aria-label')||'',
      title:e.getAttribute('title')||'',
      text:(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,24),
      dataBtn:e.getAttribute('data-sidebar-btn')||'',
      dataGuide:e.getAttribute('data-guide-target')||'',
      testid:e.getAttribute('data-testid')||'',
      rect:{x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)},
      可见:vis(e)});
  }
  rail.sort((a,b)=>a.rect.x-b.rect.x);
  out['底部一行按钮（按x排序）']=rail;
  return out;}"""

READ_PANEL = """()=>{
  const out={};
  // ★ 找含「角色」二字的面板容器
  const cands=[];
  for(const e of document.querySelectorAll('div,section,aside')){
    const t=(e.textContent||'').trim();
    if(!/角色造型室|公共角色库|我的角色库|官方角色库/.test(t))continue;
    const r=e.getBoundingClientRect();
    if(r.width<200||r.height<120)continue;
    cands.push(e);
  }
  // 取最小的那个（含关键词且面积够大）当作面板根
  let root=null;
  for(const e of cands){
    const r=e.getBoundingClientRect();
    if(!root){root=e;continue;}
    const rr=root.getBoundingClientRect();
    if(r.width* r.height < rr.width*rr.height) root=e;
  }
  out['找到候选面板数']=cands.length;
  if(!root){out['面板']=null;return out;}
  const r=root.getBoundingClientRect();
  out['面板根']={tag:root.tagName,
    rect:{x:Math.round(r.x),y:Math.round(r.y),
          w:Math.round(r.width),h:Math.round(r.height)},
    cls:(root.getAttribute('class')||'').slice(0,200),
    文本:(root.textContent||'').trim().replace(/\\s+/g,' ').slice(0,400)};
  // ★ 面板内的标题 / 页签 / 按钮
  const heads=[],tabs=[],btns=[];
  for(const e of root.querySelectorAll('h1,h2,h3,h4,[role=heading]')){
    heads.push({tag:e.tagName,text:(e.textContent||'').trim().slice(0,40)});
  }
  for(const e of root.querySelectorAll('[role=tab],[role=tablist] > *,button')){
    const t=(e.textContent||'').trim().replace(/\\s+/g,' ');
    if(!t)continue;
    const tag=e.getAttribute('role')||e.tagName.toLowerCase();
    const rec={tag:e.tagName,role:e.getAttribute('role')||'',
      text:t.slice(0,30),
      aria:e.getAttribute('aria-label')||'',
      testid:e.getAttribute('data-testid')||'',
      selected:e.getAttribute('aria-selected')};
    if(tag==='button')btns.push(rec); else tabs.push(rec);
  }
  out['标题']=heads.slice(0,10);
  out['页签']=tabs.slice(0,20);
  out['按钮']=btns.slice(0,40);
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

    log["A 工具条"] = pg.evaluate(READ_RAIL)

    # ── 真实鼠标点「角色造型室」那枚（data-sidebar-btn=character-library）
    hit = None
    for sel in ('[data-sidebar-btn="character-library"]',
                '[data-guide-target="character-studio-entry"]'):
        el = pg.query_selector(sel)
        if el:
            bb = el.bounding_box()
            if bb:
                pg.mouse.click(bb["x"] + bb["width"] / 2,
                               bb["y"] + bb["height"] / 2)
                hit = sel
                break
    log["B 点的是"] = hit
    pg.wait_for_timeout(5000)
    log["C 面板读数"] = pg.evaluate(READ_PANEL)
    pg.screenshot(path="/tmp/liblib_source_studio826.png", full_page=False)

    # ★ 再找「公共角色库」在源站哪里（有没有独立的入口）
    log["D 公共角色库出现处"] = pg.evaluate("""()=>{
      const out=[];
      for(const e of document.querySelectorAll('button,[role=tab],a,div')){
        const t=(e.textContent||'').trim();
        if(t!=='公共角色库')continue;
        const r=e.getBoundingClientRect();
        out.push({tag:e.tagName,role:e.getAttribute('role')||'',
          text:t, rect:{x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)},
          w:r.width,h:r.height,
          父:(e.parentElement?(e.parentElement.textContent||'')
              .trim().replace(/\\s+/g,' ').slice(0,60):'')});
      }
      return out.slice(0,10);}""")
    br.close()

OUT.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(log, ensure_ascii=False, indent=1)[:9000])
