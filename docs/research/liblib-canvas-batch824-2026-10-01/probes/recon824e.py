#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 824 源站补测②：底部工具条的**药丸容器**矩形。

★ 为什么要量这个：★ 我第一版的判据拿 clone 的「**药丸边缘** → 球」
  去比源站的「**最后一枚按钮边缘** → 球」⟹ ★★ **两把不是一样的尺子**，
  而数字碰巧都等于 14 ⟹ ★★ 判据绿灯、实际差 9px。
  ⟹ 做法：**两边都量「按钮→球」和「药丸→球」两个量**，都从源站 raw 取期望值。

★ 药丸容器怎么找：底部那 8 枚里，前 7 枚（添加节点…教程）的**最近公共祖先**
  ⟹ 它就是药丸；第 8 枚（TV Director）**不在**里面 ⟹ 正好证明「球在药丸之外」。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_dockpill.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

JS = """()=>{
  const vis=(e)=>{const r=e.getBoundingClientRect();
    if(r.width===0&&r.height===0)return false;
    const cs=getComputedStyle(e);
    return cs.visibility!=='hidden'&&cs.display!=='none'
      && Number(cs.opacity||'1')>0;};
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:+r.x.toFixed(2),y:+r.y.toFixed(2),
            w:+r.width.toFixed(2),h:+r.height.toFixed(2),
            cx:+(r.x+r.width/2).toFixed(2),cy:+(r.y+r.height/2).toFixed(2)};};
  const dock=Array.from(document.querySelectorAll('button[aria-label]')).filter(
    e=>vis(e)&&e.getBoundingClientRect().y>=window.innerHeight-140
       &&e.getBoundingClientRect().width<=200);
  const names=dock.map(e=>e.getAttribute('aria-label'));
  const orb=dock.find(e=>e.getAttribute('aria-label')==='TV Director');
  const help=dock.find(e=>e.getAttribute('aria-label')==='教程');
  // ★ 前 7 枚的最近公共祖先 = 药丸
  let anc=help;
  const inners=dock.filter(e=>e!==orb);
  for(const e of inners){
    while(anc&&!anc.contains(e)) anc=anc.parentElement;}
  // ★ 父链：找药丸背景到底长在谁身上
  const chain=[];
  let n=help;
  for(let i=0;i<8&&n;i++){
    const s2=getComputedStyle(n), rr=n.getBoundingClientRect();
    chain.push({tag:n.tagName, cls:(n.getAttribute('class')||'').slice(0,80),
      box:box(n), bg:s2.backgroundColor, radius:s2.borderRadius,
      padding:s2.padding, overflow:s2.overflow, position:s2.position});
    n=n.parentElement;
  }
  // ★ 药丸 = 父链里第一个「**有底色** + 宽度小于视口」的元素
  //   （最近公共祖先会一路走到 body ⟹ 那不是药丸）
  let pillEl=null, pillInfo=null;
  for(const c of chain){
    if(c.bg!=='rgba(0, 0, 0, 0)' && c.bg!=='transparent'
       && c.box.w < window.innerWidth){pillInfo=c;break;}}
  for(let e=help;e;e=e.parentElement){
    const s4=getComputedStyle(e), rr=e.getBoundingClientRect();
    const solid=s4.backgroundColor!=='rgba(0, 0, 0, 0)'
      && s4.backgroundColor!=='transparent';
    if(solid && rr.width < window.innerWidth){pillEl=e;break;}}
  const o=orb?box(orb):null, h=help?box(help):null;
  const p=pillInfo?pillInfo.box:null;
  return {视口:[window.innerWidth,window.innerHeight],
    底部按钮名:names,
    球:o, 教程:h, 药丸:p,
    药丸样式:pillInfo?{bg:pillInfo.bg,radius:pillInfo.radius,
                     padding:pillInfo.padding,overflow:pillInfo.overflow,
                     position:pillInfo.position,cls:pillInfo.cls}:null,
    按钮到球间隙:(o&&h)? +(o.x-(h.x+h.w)).toFixed(2):null,
    药丸到球间隙:(o&&p)? +(o.x-(p.x+p.w)).toFixed(2):null,
    同轴偏差:(o&&h)? +(o.cy-h.cy).toFixed(2):null,
    球在药丸之外:(o&&p)? (o.x>=p.x+p.w):null,
    球是药丸的后代: pillEl? !pillEl.contains(orb):null,
    父链: chain,
  };}"""

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
    out = pg.evaluate(JS)
    br.close()

OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=1))
