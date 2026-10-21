#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 827 源站取证③：点开三个筛选下拉（真实鼠标点 `<summary>`），读**展开态**。

★ 上一版没找到入口的原因：pill 是原生 `<details>/<summary>` ⟹ summary
  既不是 button 也不是 role=combobox ⟹ 用按钮选择器当然找不到。
★ 展开态的选项用**命中测试**读（收起时它们 display 仍是 block ⟹ 只有命中测试准）。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_studio827c.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

READ_PILLS = """()=>{
  const out=[];
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  for(const d of document.querySelectorAll('details')){
    const s=d.querySelector('summary');
    if(!s)continue;
    const t=(s.textContent||'').trim().replace(/\\s+/g,' ');
    if(!/性别|年龄段|文化区域/.test(t))continue;
    const panel=d.querySelector('div');
    out.push({label:t, open:d.hasAttribute('open'),
      summary:box(s), details:box(d),
      panel:panel?box(panel):null,
      summaryCls:(s.getAttribute('class')||'').slice(0,120),
      panelCls:panel?(panel.getAttribute('class')||'').slice(0,140):null});
  }
  return out;}"""

READ_OPTIONS = """()=>{
  const out=[];
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\\s+/g,' ');
  const hit=(e)=>{
    const r=e.getBoundingClientRect();
    if(r.width<=0||r.height<=0)return false;
    const h=document.elementFromPoint(r.x+r.width/2, r.y+r.height/2);
    return !!(h&&(h===e||e.contains(h)));};
  for(const lab of document.querySelectorAll('label')){
    const t=txt(lab);
    if(!t||t.length>12)continue;
    if(!/^(男|女|中性|儿童|少年|青年|中年|老年|东亚|欧美|中东|非洲|其他|奇幻)/.test(t))continue;
    const cb=lab.querySelector('input[type=checkbox]');
    out.push({text:t, box:box(lab), 命中:hit(lab),
      有checkbox:!!cb,
      cls:(lab.getAttribute('class')||'').slice(0,90)});
  }
  return out;}"""


def click_real(page, x, y):
    page.mouse.click(x, y)


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
            click_real(pg, bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
    pg.wait_for_timeout(5000)

    log["A 收起态的三个下拉"] = pg.evaluate(READ_PILLS)
    for name, key in (("性别", "g"), ("年龄段", "a"), ("文化区域", "c")):
        # 先全部收起
        pg.evaluate("""()=>{document.querySelectorAll('details[open]')
          .forEach(d=>d.removeAttribute('open'));}""")
        pg.wait_for_timeout(300)
        pick = pg.evaluate("""(n)=>{
          const d=[...document.querySelectorAll('details')]
            .find(x=>{const s=x.querySelector('summary');
              return s && (s.textContent||'').trim().startsWith(n);});
          if(!d)return null;
          const r=d.querySelector('summary').getBoundingClientRect();
          return {x:r.x+r.width/2,y:r.y+r.height/2};}""", name)
        if not pick:
            log["展开 %s" % name] = {"没找到": True}
            continue
        click_real(pg, pick["x"], pick["y"])
        pg.wait_for_timeout(900)
        log["展开 %s" % name] = pg.evaluate(READ_OPTIONS)
        log["展开 %s 后的 details" % name] = pg.evaluate(READ_PILLS)
        pg.screenshot(path="/tmp/liblib_source_studio827c_%s.png" % key)
    br.close()

OUT.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
print("saved", OUT)
