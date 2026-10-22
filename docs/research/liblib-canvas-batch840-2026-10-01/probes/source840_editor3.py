#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 840 源站探针③：问「**哪些是选中的**」——用**计算样式**，不用类名。

★ 为什么：类名被截断（120 字）⟹ 看不出选中态；⟹ ⟹ 选中态在源站是由**样式**表达的
  （页签是 `border-b` 的颜色、段是背景色）⟹ ⟹ 读**计算样式**才作数。

★★ 只读：不点任何东西。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_840_editor3.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

STYLES = r"""()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\s+/g,' ');
  const pick=(sel)=>[...document.querySelectorAll(sel)];
  const styleOf=(e)=>{const cs=getComputedStyle(e);
    return {bg:cs.backgroundColor,color:cs.color,borderBottom:cs.borderBottomColor,
      borderBottomWidth:cs.borderBottomWidth,borderBottomStyle:cs.borderBottomStyle,
      opacity:cs.opacity,fontWeight:cs.fontWeight,borderRadius:cs.borderRadius};};
  const segs=pick('button').filter(b=>{
    const r=b.getBoundingClientRect();
    return r.x>=370&&r.x<=376&&r.width===240&&r.height===44;})
    .map(b=>({text:txt(b).slice(0,20),box:box(b),style:styleOf(b),
              ariaPressed:b.getAttribute('aria-pressed'),
              dataActive:b.getAttribute('data-active'),
              cls:(b.getAttribute('class')||'').slice(-140)}));
  const tabs=pick('button').filter(b=>{
    const r=b.getBoundingClientRect();
    return r.y>=231&&r.y<=233&&r.height===39&&r.x>=1290&&r.x<=1545;})
    .map(b=>({text:txt(b).slice(0,8),aria:b.getAttribute('aria-label')||'',box:box(b),
              style:styleOf(b),
              ariaSelected:b.getAttribute('aria-selected'),
              dataActive:b.getAttribute('data-active'),
              cls:(b.getAttribute('class')||'').slice(-140)}));
  // Mantine Switch 的轨道与滑块
  const sw=document.querySelector('.mantine-Switch-track');
  const th=document.querySelector('.mantine-Switch-thumb');
  const swInfo=sw?{box:box(sw),style:styleOf(sw),cls:(sw.getAttribute('class')||'').slice(-120)}:null;
  const thInfo=th?{box:box(th),style:styleOf(th),
                   transform:getComputedStyle(th).transform}:null;
  // 底栏复选框（sr-only input 旁边的可见件）
  const cbs=[...document.querySelectorAll('input[type=checkbox]')].map(i=>({
    checked:i.checked,box:box(i),cls:(i.getAttribute('class')||'').slice(0,90)}));
  // 五段里的「限免」徽标
  const badges=[...document.querySelectorAll('span,div')].filter(e=>{
    const t=txt(e); if(t!=='限免')return false;
    return e.children.length===0;}).map(e=>({box:box(e),style:styleOf(e),
      cls:(e.getAttribute('class')||'').slice(-120)}));
  return {segs,tabs,swInfo,thInfo,cbs,badges};
}"""

FIND_ASSETS_BTN = """()=>{
  const out=[];
  for(const e of document.querySelectorAll('button')){
    if((e.textContent||'').trim()!=='查看角色资产')continue;
    const r=e.getBoundingClientRect();
    out.push({x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),
      h:Math.round(r.height)});
  }
  return out;}"""


def click_text(page, label):
    for e in page.query_selector_all("span,div,button,a,p"):
        if (e.text_content() or "").strip() != label:
            continue
        bb = e.bounding_box()
        if not bb:
            continue
        page.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
        return True
    return False


def main():
    log = {}
    try:
        cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            ctx.add_cookies([{"name": c["name"], "value": c["value"],
                              "domain": c["domain"], "path": c.get("path", "/")}
                             for c in cookies])
            pg = ctx.new_page()
            pg.set_default_timeout(25_000)
            pg.goto(URL, wait_until="domcontentloaded", timeout=90_000)
            pg.wait_for_timeout(12_000)
            el = pg.query_selector("text=下次再说")
            if el:
                el.click()
                pg.wait_for_timeout(900)
            el = pg.query_selector('[data-sidebar-btn="character-library"]')
            if el:
                bb = el.bounding_box()
                if bb:
                    pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
            pg.wait_for_timeout(5000)
            tab = pg.query_selector("button:text-is('官方角色库')")
            if tab:
                bb = tab.bounding_box()
                pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
                pg.wait_for_timeout(4000)
            bs = pg.evaluate(FIND_ASSETS_BTN)
            if bs:
                b = bs[0]
                pg.mouse.move(b["x"] + b["w"] / 2, b["y"] + b["h"] / 2)
                pg.wait_for_timeout(1500)
                bs2 = pg.evaluate(FIND_ASSETS_BTN)
                b2 = bs2[0] if bs2 else b
                pg.mouse.click(b2["x"] + b2["w"] / 2, b2["y"] + b2["h"] / 2)
                pg.wait_for_timeout(3500)
            log["★是否点到编辑角色"] = click_text(pg, "编辑角色")
            pg.wait_for_timeout(5000)
            log["★样式读数"] = pg.evaluate(STYLES)
            br.close()
    except Exception:
        log["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        s = log.get("★样式读数") or {}
        for seg in s.get("segs") or []:
            print(f"  段 {seg['text']!r:22s} {seg['box']} bg={seg['style']['bg']} "
                  f"color={seg['style']['color']} radius={seg['style']['borderRadius']}")
        for t in s.get("tabs") or []:
            print(f"  页签 {t['text'] or t['aria']!r:12s} {t['box']} "
                  f"bb={t['style']['borderBottom']} w={t['style']['borderBottomWidth']}")
        print("  switch:", json.dumps(s.get("swInfo"), ensure_ascii=False))
        print("  thumb :", json.dumps(s.get("thInfo"), ensure_ascii=False))
        print("  复选框:", json.dumps(s.get("cbs"), ensure_ascii=False))
        for b in s.get("badges") or []:
            print(f"  限免徽标 {b['box']} bg={b['style']['bg']} color={b['style']['color']}")
        if log.get("异常"):
            print("异常：", log["异常"])


if __name__ == "__main__":
    main()
