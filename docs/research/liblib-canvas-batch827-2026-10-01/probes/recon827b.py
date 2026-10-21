#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 827 源站取证②：把角色造型面板的**筛选下拉**读准。

★ 上一版两个错：
  ① 找下拉入口用 `textContent === '性别'` ⟹ 实际 pill 的文本带箭头 ⟹ 没找到
     ⟹ 改成**前缀匹配**。
  ② 判「可见」只看元素自身 + 祖先的 opacity ⟹ 仍然把**收起**的下拉选项
     判成「可见」⟹ ★★ 截图明明是收起的 ⟹ ⟹ 隐藏机制**不是** opacity
     ⟹ 本版改用**命中测试**（elementFromPoint 落在谁身上）当可见性判据，
     并把祖先链的 display/visibility/opacity/transform/overflow/height/
     clip-path 全打出来 ⟹ 定位真正的机制。
★ 硬约束：不点任何生成/付费按钮。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_studio827b.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

READ = """()=>{
  const out={};
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\\s+/g,' ');
  // ★ 命中测试：点它的中心，命中谁？只有命中它自己（或它的后代）才算「看得见」
  const hitSelf=(e)=>{
    const r=e.getBoundingClientRect();
    if(r.width<=0||r.height<=0)return {hit:false,why:'零尺寸'};
    const cx=r.x+r.width/2, cy=r.y+r.height/2;
    const h=document.elementFromPoint(cx,cy);
    if(!h)return {hit:false,why:'命中 null'};
    return {hit:(h===e||e.contains(h)),
            命中标签:h.tagName,
            命中文字:(h.textContent||'').trim().slice(0,12)};
  };
  // ★ 找到三个筛选 pill（文本**前缀**匹配）
  const pills=[];
  for(const e of document.querySelectorAll('button,[role=combobox],[role=button]')){
    const t=txt(e);
    if(!/^(性别|年龄段|文化区域)/.test(t))continue;
    const r=e.getBoundingClientRect();
    if(r.width===0||r.height===0)continue;
    pills.push({text:t,box:box(e),
      cls:(e.getAttribute('class')||'').slice(0,120),
      html:(e.innerHTML||'').slice(0,220)});
  }
  out['筛选pill']=pills;
  // ★ 祖先链：找一个选项（男）并把它每一层祖先的样式打出来
  let opt=null;
  for(const e of document.querySelectorAll('span,div,label')){
    if(txt(e)==='男'){opt=e;break;}
  }
  out['有「男」这个节点']=!!opt;
  if(opt){
    const chain=[]; let n=opt;
    for(let i=0;i<8&&n&&n.nodeType===1;i++){
      const cs=getComputedStyle(n);
      chain.push({tag:n.tagName,
        cls:(n.getAttribute('class')||'').slice(0,90),
        display:cs.display, visibility:cs.visibility, opacity:cs.opacity,
        transform:cs.transform, overflow:cs.overflow, overflowY:cs.overflowY,
        height:cs.height, maxHeight:cs.maxHeight, clipPath:cs.clipPath,
        contentVisibility:cs.contentVisibility, contain:cs.contain,
        position:cs.position, zIndex:cs.zIndex,
        box:box(n)});
      n=n.parentElement;
    }
    out['「男」的祖先链']=chain;
    out['「男」命中测试']=hitSelf(opt);
    out['「男」的兄弟']=Array.from(opt.parentElement?opt.parentElement.children:[])
      .slice(0,6).map(x=>({tag:x.tagName,txt:txt(x).slice(0,10),
        cls:(x.getAttribute('class')||'').slice(0,60),box:box(x)}));
  }
  return out;}"""

READ_OPTIONS = """()=>{
  const out={};
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\\s+/g,' ');
  const hitSelf=(e)=>{
    const r=e.getBoundingClientRect();
    if(r.width<=0||r.height<=0)return false;
    const h=document.elementFromPoint(r.x+r.width/2, r.y+r.height/2);
    return !!(h && (h===e||e.contains(h)));
  };
  const opts=[];
  for(const e of document.querySelectorAll('span,div,label,button')){
    if(e.children.length>0)continue;
    const t=txt(e);
    if(!t||t.length>8)continue;
    if(!/^(男|女|中性|儿童|少年|青年|中年|老年|东亚|欧美|中东|非洲|其他|奇幻)$/.test(t))continue;
    opts.push({text:t,box:box(e),命中:hitSelf(e),
      cls:(e.getAttribute('class')||'').slice(0,70)});
  }
  out['选项（按命中测试分）']={
    '命中自己（看得见）':opts.filter(o=>o['命中']),
    '没命中自己（被盖/被裁）':opts.filter(o=>!o['命中'])};
  return out;}"""


def click_real(page, locator):
    bb = locator.bounding_box()
    if not bb:
        return False
    page.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
    return True


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
        click_real(pg, el)
    pg.wait_for_timeout(5000)
    log["A 收起态"] = pg.evaluate(READ)

    # ★ 真实鼠标点开「性别」pill（前缀匹配）
    pg.evaluate("""()=>{
      const b=[...document.querySelectorAll('button,[role=combobox],[role=button]')]
        .find(e=>/^性别/.test((e.textContent||'').trim()));
      if(b){const r=b.getBoundingClientRect();
        window.__pick={x:r.x+r.width/2,y:r.y+r.height/2};}}""")
    pick = pg.evaluate("()=>window.__pick")
    if pick:
        pg.mouse.click(pick["x"], pick["y"])
        pg.wait_for_timeout(1200)
        log["B 点开性别后"] = pg.evaluate(READ_OPTIONS)
        pg.screenshot(path="/tmp/liblib_source_studio827b_gender.png")
        log["C 点开后的祖先链"] = pg.evaluate(READ)
    br.close()

OUT.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
print("saved", OUT)
