#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 827 源站取证①：角色造型面板的**完整**结构（含筛选下拉的展开态）。

★ 上一版（recon826d）漏掉的东西：
  - 筛选下拉里那些选项（男/女/中性…）在 DOM 里「可见」，但截图上**根本不在**
    ⟹ 它们的**祖先**是 opacity:0 的下拉层 ⟹ 我上一版的 `vis()` 只看元素自身
    ⟹ **假可见**。本版改成：★ 先**真实鼠标点开**下拉，再读**可见**选项。
  - 面板的**头部/筛选行/右侧按钮/卡片区/底部 CTA** 的逐个矩形。
★ 硬约束：不点任何生成/付费按钮。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_studio827.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 祖先链可见性：把祖先的 opacity/visibility 一起算 ⟹ 不再被 opacity:0 骗
READ = """()=>{
  const out={};
  const realVis=(e)=>{
    for(let n=e;n&&n.nodeType===1;n=n.parentElement){
      const cs=getComputedStyle(n);
      if(cs.display==='none')return false;
      if(cs.visibility==='hidden')return false;
      if(Number(cs.opacity||'1')<=0.001)return false;   // ★ 祖先 opacity:0 也算不可见
    }
    const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0;
  };
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\\s+/g,' ');
  // ★ 面板根：从「我的角色库」那个按钮往上走到 1198×758 那个祖先
  let anchor=null;
  for(const e of document.querySelectorAll('button')){
    if(txt(e)==='我的角色库'&&realVis(e)){anchor=e;break;}
  }
  if(!anchor){out['err']='no anchor';return out;}
  let p=anchor, root=null;
  for(let i=0;i<15&&p;i++){
    const r=p.getBoundingClientRect();
    if(r.width>800&&r.height>400){root=p;break;}
    p=p.parentElement;
  }
  if(!root){out['err']='no root';return out;}
  out['面板根']=box(root);
  out['面板根class']=(root.getAttribute('class')||'').slice(0,160);
  // ★ 头部：两个页签 + 关闭
  const head=[];
  for(const e of root.querySelectorAll('button,[role=tab]')){
    if(!realVis(e))continue;
    const r=e.getBoundingClientRect();
    if(r.y>260)continue;                       // 只取头部那一行
    head.push({text:txt(e).slice(0,20),aria:e.getAttribute('aria-label')||'',
      role:e.getAttribute('role')||'',box:box(e),
      font:getComputedStyle(e).fontSize+'/'+getComputedStyle(e).fontWeight,
      color:getComputedStyle(e).color,
      bg:getComputedStyle(e).backgroundColor});
  }
  out['头部']=head;
  // ★ 筛选行（y 在头部之后、卡片之前）
  const filt=[];
  for(const e of root.querySelectorAll('button,[role=combobox],[role=button],input')){
    if(!realVis(e))continue;
    const r=e.getBoundingClientRect();
    if(r.y<240||r.y>300)continue;
    filt.push({tag:e.tagName,text:txt(e).slice(0,24),
      aria:e.getAttribute('aria-label')||'',
      role:e.getAttribute('role')||'',
      box:box(e),
      cls:(e.getAttribute('class')||'').slice(0,90)});
  }
  out['筛选行']=filt;
  // ★ 可见叶子文本（选项/卡片名/CTA）
  const leaves=[];
  for(const e of root.querySelectorAll('span,div,p,h1,h2,h3,button')){
    if(e.children.length>0)continue;
    if(!realVis(e))continue;
    const t=txt(e);
    if(!t||t.length>30)continue;
    leaves.push({tag:e.tagName,text:t,box:box(e)});
  }
  leaves.sort((a,b)=>(a.box.y-b.box.y)||(a.box.x-b.box.x));
  out['可见叶子文本']=leaves.slice(0,60);
  // ★ 卡片：图 + 名 + 「查看角色资产」
  const cards=[];
  for(const e of root.querySelectorAll('img')){
    if(!realVis(e))continue;
    const r=e.getBoundingClientRect();
    cards.push({alt:e.getAttribute('alt')||'',src:(e.getAttribute('src')||'').slice(-60),
      box:box(e)});
  }
  out['卡片图']=cards.slice(0,12);
  // ★ 底部 CTA 行（y > 800）
  const cta=[];
  for(const e of root.querySelectorAll('button')){
    if(!realVis(e))continue;
    const r=e.getBoundingClientRect();
    if(r.y<760)continue;
    cta.push({text:txt(e).slice(0,24),aria:e.getAttribute('aria-label')||'',
      box:box(e),
      bg:getComputedStyle(e).backgroundColor,
      color:getComputedStyle(e).color});
  }
  out['底部CTA']=cta;
  // ★ 底部那条横向滚动条（INPUT[type=range] / aria=角色列表）
  const sliders=[];
  for(const e of root.querySelectorAll('input')){
    sliders.push({type:e.getAttribute('type')||'',aria:e.getAttribute('aria-label')||'',
      box:box(e),visible:realVis(e)});
  }
  out['input']=sliders;
  return out;}"""

# ★ 点开某个筛选下拉后读它的**可见**选项
READ_OPEN = """()=>{
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
  const opts=[];
  for(const e of document.querySelectorAll('label,span,div,button')){
    if(e.children.length>0)continue;
    if(!realVis(e))continue;
    const t=(e.textContent||'').trim();
    if(!t||t.length>8)continue;
    const r=e.getBoundingClientRect();
    opts.push({text:t,box:box(e),
      cls:(e.getAttribute('class')||'').slice(0,70)});
  }
  opts.sort((a,b)=>(a.box.y-b.box.y)||(a.box.x-b.box.x));
  out['可见选项']=opts.slice(0,40);
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
    log["A 我的角色库"] = pg.evaluate(READ)
    pg.screenshot(path="/tmp/liblib_source_studio827_mine.png")

    # ★ 逐个点开三个筛选下拉（真实鼠标），读**可见**选项
    for i, name in enumerate(("性别", "年龄段", "文化区域")):
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(400)
        target = None
        for e in pg.query_selector_all("button,[role=combobox]"):
            if (e.text_content() or "").strip() == name:
                target = e
                break
        if target is None:
            log["下拉 %s" % name] = {"没找到入口": True}
            continue
        click_real(pg, target)
        pg.wait_for_timeout(900)
        log["下拉 %s" % name] = pg.evaluate(READ_OPEN)
        pg.screenshot(path="/tmp/liblib_source_studio827_%s.png" % name)

    # ★ 官方角色库页签
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(400)
    el = pg.query_selector("button:text-is('官方角色库')")
    if el:
        click_real(pg, el)
        pg.wait_for_timeout(3500)
    log["B 官方角色库"] = pg.evaluate(READ)
    pg.screenshot(path="/tmp/liblib_source_studio827_official.png")
    br.close()

OUT.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
print("saved", OUT)
