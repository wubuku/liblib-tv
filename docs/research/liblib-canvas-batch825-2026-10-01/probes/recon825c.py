#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 825 源站取证③（决定性）：**打开源站的导演台**，让机位跟随一个目标，
看源站在机位跟随时**到底有没有**顶部横幅。

★ 这一步要回答的是：
  ① 机位跟随时源站有没有横幅？（bundle 说没有 ⟹ 要用运行时确认）
  ② 那条横幅在**激活**状态下，按钮点不点得动？
     （bundle 代码：面板 active 时 pointer-events-auto ⟹ 点得动；
       605 量的那块是**未激活**的 ⟹ 点不动）
  ③ 源站的机位跟随在**检查器**里长什么样（跟随目标 / 不跟随 / 跟随视角…）

★ 有副作用（会把源站测试画布里那台相机的 followTargetId 设上）⟹
  ★ 结束时**改回 null**（不改回去就等于在源站留了个跟随状态）。
★ 硬约束：**不点任何生成/付费按钮**。
"""
import json
import pathlib
import re
import time

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk_follow.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 导演台里「有没有跟随横幅」的读数（按**结构**找，不按 testid 猜）
READ = """()=>{
  const vis=(e)=>{const r=e.getBoundingClientRect();
    const cs=getComputedStyle(e);
    return cs.visibility!=='hidden'&&cs.display!=='none'
      && Number(cs.opacity||'1')>0;};
  const out={};
  out['url']=location.href;
  out['有工作台']=!!document.querySelector('[data-director-workspace]');
  // ★ 所有「固定定位 + 顶部 + 含跟随字样」的元素（含**未激活**的）
  const cands=[];
  for(const e of document.querySelectorAll('div,span,button')){
    const cs=getComputedStyle(e);
    if(cs.position!=='fixed')continue;
    const r=e.getBoundingClientRect();
    if(r.y>80||r.height>80)continue;
    const t=(e.textContent||'').trim().replace(/\\s+/g,' ');
    if(!/跟随|ESC/.test(t))continue;
    cands.push({tag:e.tagName,text:t.slice(0,40),
      testid:e.getAttribute('data-testid')||'',
      cls:(e.getAttribute('class')||'').slice(0,140),
      rect:{x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)},
      opacity:cs.opacity, bg:cs.backgroundColor, pe:cs.pointerEvents,
      z:cs.zIndex, ariaHidden:e.getAttribute('aria-hidden'),
      inert:e.hasAttribute('inert'),
      visible:vis(e)});
  }
  out['跟随横幅候选（含未激活）']=cands;
  // ★ 取消按钮的命中测试（elementFromPoint 落在谁身上）
  const btn=document.querySelector('[data-testid="collab-follow-banner-close"]')
    || Array.from(document.querySelectorAll('button'))
        .find(b=>(b.getAttribute('aria-label')||'')==='退出跟随');
  if(btn){
    const r=btn.getBoundingClientRect();
    const cx=r.x+r.width/2, cy=r.y+r.height/2;
    const hit=document.elementFromPoint(cx,cy);
    out['取消按钮']={
      存在:true, rect:{x:Math.round(r.x),y:Math.round(r.y),
                       w:Math.round(r.width),h:Math.round(r.height)},
      own:(btn.textContent||'').trim(),
      aria:btn.getAttribute('aria-label'),
      ariaKeyShortcuts:btn.getAttribute('aria-keyshortcuts'),
      cls:(btn.getAttribute('class')||'').slice(0,140),
      pe:getComputedStyle(btn).pointerEvents,
      命中标签:hit?hit.tagName:null,
      命中testid:hit?(hit.getAttribute('data-testid')||''):null,
      命中文字:hit?(hit.textContent||'').trim().slice(0,20):null,
      命中就是它: hit===btn || (hit?btn.contains(hit):false)};
  } else { out['取消按钮']={存在:false}; }
  // ★ 检查器里的机位跟随控件
  const ctrls=[];
  for(const e of document.querySelectorAll('button,select,input,label,[role=button],[role=combobox]')){
    const t=((e.getAttribute('aria-label')||'')+' '+((e.textContent||''))).trim()
      .replace(/\\s+/g,' ');
    if(!/跟随|机位|视角|偏移/.test(t))continue;
    const r=e.getBoundingClientRect();
    ctrls.push({tag:e.tagName,text:t.slice(0,40),
      testid:e.getAttribute('data-testid')||'',
      aria:e.getAttribute('aria-label')||'',
      value:(e.value!==undefined?String(e.value).slice(0,30):''),
      options:(e.tagName==='SELECT'?Array.from(e.options).map(o=>o.text).slice(0,8):null),
      rect:{x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)},
      visible:vis(e)});
  }
  out['跟随相关控件']=ctrls.slice(0,30);
  return out;}"""

cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
log = {}

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
    pg.set_default_timeout(20000)
    pg.goto(URL, wait_until="domcontentloaded", timeout=90_000)
    pg.wait_for_timeout(11_000)
    for label in ("下次再说",):
        el = pg.query_selector("text=%s" % label)
        if el:
            el.click()
            pg.wait_for_timeout(900)
            break

    log["A 画布页读数"] = pg.evaluate(READ)

    # ── 打开导演台：点「打开导演台」那个按钮
    opened = False
    for sel in ("text=打开导演台", "[data-open-director]",
                "button:has-text('打开导演台')"):
        el = pg.query_selector(sel)
        if el:
            try:
                el.scroll_into_view_if_needed(timeout=4000)
                bb = el.bounding_box()
                if bb:
                    pg.mouse.click(bb["x"] + bb["width"] / 2,
                                   bb["y"] + bb["height"] / 2)
                    opened = True
                    log["B 点击的入口"] = sel
                    break
            except Exception as exc:                            # noqa: BLE001
                log["B 点击异常"] = str(exc)[:150]
    pg.wait_for_timeout(9000)
    log["C 点完之后"] = pg.evaluate(READ)
    log["C 导演台开了吗"] = bool(pg.query_selector("[data-director-workspace]"))

    # ── 在导演台里找「跟随目标」下拉（真实鼠标点开对象树里的相机）
    sel_opts = pg.evaluate("""()=>Array.from(document.querySelectorAll('select'))
      .map(s=>({testid:s.getAttribute('data-testid')||'',
                aria:s.getAttribute('aria-label')||'',
                label:(s.closest('label')?(s.closest('label').textContent||''):'')
                    .trim().replace(/\\s+/g,' ').slice(0,20),
                options:Array.from(s.options).map(o=>({v:o.value,t:o.text}))}))""")
    log["D 导演台里的 select"] = sel_opts
    br.close()

OUT.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(log, ensure_ascii=False, indent=1)[:6000])
