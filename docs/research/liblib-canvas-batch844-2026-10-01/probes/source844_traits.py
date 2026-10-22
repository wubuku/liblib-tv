#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 844 源站探针（**只读**）：左列第二段「脸部 & 身体特征」的右栏结构。

## 为什么还要跑一趟

batch 841 的 raw 只记了「右栏子树的 tag/box/cls」，**没有计算样式**，也**没有 aria**
⟹ ⟹ 而 clone 要对齐的不只是盒，还有**外观**（字体/颜色/圆角/边框）与**语义**（选中态）。

★ **本段的结构（841 raw 已机器提取）**：
  H3「纹身 & 疤痕」240×22 ＋ 一张 **3 列 × 2 行**的卡片网格（6 张 76×54）
  ⟹ 缩略图 **76×32 的圆形**（`rounded-full`，与妆造页的 76×76 方形**不一样**）
  ⟹ 第 6 张「自定义」**没有图** ⟹ 是一枚 16×16 的图标

★ **只读**：只点左列的**分段**（不点页签、不点卡片、不点「确认生成」）
  ⟹ ⟹ **不消耗** ⚡44 ⟹ ⟹ 每次点击前后都核对那一颗积分（x 540..575、y 855..885）。

★ 输出：`/tmp/liblib_source_844_traits.json`
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

URL = ("https://www.liblib.tv/canvas"
       "?spaceId=7709759&projectId=a860e1da8e9e4504bececda022386429")
COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_844_traits.json")

SEGMENT = "脸部 & 身体特征"

MEASURE = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\\s+/g,' ');
  const cls=(e)=>String((e&&e.getAttribute)?(e.getAttribute('class')||''):'').slice(0,150);
  const st=(e)=>{if(!e)return null;const cs=getComputedStyle(e);
    return {fontSize:cs.fontSize,fontWeight:cs.fontWeight,lineHeight:cs.lineHeight,
      color:cs.color,backgroundColor:cs.backgroundColor,borderRadius:cs.borderRadius,
      borderTopWidth:cs.borderTopWidth,borderTopColor:cs.borderTopColor,
      paddingLeft:cs.paddingLeft,paddingTop:cs.paddingTop,gap:cs.gap,
      fontFamily:cs.fontFamily,display:cs.display,alignItems:cs.alignItems,
      justifyContent:cs.justifyContent,width:cs.width,height:cs.height,
      objectFit:cs.objectFit,position:cs.position};};

  const aside=[...document.querySelectorAll('aside')].find(a=>{
    const r=a.getBoundingClientRect();return r.x>=1273&&Math.round(r.width)===288;});
  if(!aside)return {err:'右栏没找到'};
  const out={};
  out['右栏盒']=box(aside);

  // ★ 右栏的**第一层子节点**（★ 用来判「这一段有没有标题行」）
  const kid=aside.firstElementChild;
  out['右栏第一层']=kid?{tag:kid.tagName,cls:cls(kid),
    box:box(kid),style:st(kid),
    子节点数:kid.children.length,
    头行:(kid.firstElementChild&&kid.firstElementChild.tagName==='DIV'
      &&Math.round(kid.firstElementChild.getBoundingClientRect().height)===40)
      ?{box:box(kid.firstElementChild),
         cls:cls(kid.firstElementChild),
         按钮:[...kid.firstElementChild.querySelectorAll('button')].map(b=>({
           text:txt(b),box:box(b),aria:b.getAttribute('aria-label')||'',
           cls:cls(b)}))}
      :null,
    内容起点:(()=>{ // ★ 内容容器（滚动区）的盒
      const sc=[...kid.children].find(c=>c.tagName==='DIV'&&c!==kid.firstElementChild);
      return sc?{box:box(sc),cls:cls(sc),style:st(sc)}:null;})()
  }:null;

  // ★ H3 标题
  const h3=aside.querySelector('h3');
  out['H3']=h3?{text:txt(h3),box:box(h3),style:st(h3),
    cls:cls(h3),
    html:(h3.outerHTML||'').slice(0,300)}:null;

  // ★ 网格容器
  const grid=[...aside.querySelectorAll('div')].find(d=>{
    const c=String(d.getAttribute('class')||'');
    return /grid-cols-3/.test(c)&&d.querySelectorAll('button').length>0;});
  out['网格']=grid?{box:box(grid),cls:cls(grid),
    style:st(grid),按钮数:grid.querySelectorAll('button').length}:null;

  // ★ 6 张卡（76×54 的按钮）
  const cards=[...aside.querySelectorAll('button')].filter(e=>{
    const r=e.getBoundingClientRect();
    return Math.round(r.width)===76&&Math.round(r.height)===54;});
  out['卡片']=cards.map(b=>{
    const thumb=b.firstElementChild;
    const img=b.querySelector('img');
    const name=[...b.querySelectorAll('span')].find(s=>
      s.children.length===0&&txt(s)&&Math.round(s.getBoundingClientRect().height)===16);
    const icon=[...b.querySelectorAll('span')].find(s=>
      s.children.length===0&&Math.round(s.getBoundingClientRect().width)===16
      &&Math.round(s.getBoundingClientRect().height)===16&&!txt(s));
    return {aria:b.getAttribute('aria-label')||'',
      pressed:b.getAttribute('aria-pressed'),
      selected:b.getAttribute('aria-selected'),
      data:[...b.attributes].filter(a=>a.name.startsWith('data-'))
            .map(a=>a.name+'='+a.value),
      box:box(b),
      缩略盒:thumb?box(thumb):null,
      缩略样式:thumb?st(thumb):null,
      缩略cls:thumb?cls(thumb):'',
      图:img?{src:(img.currentSrc||img.src||'').slice(0,120),box:box(img),
        natural:[img.naturalWidth,img.naturalHeight],样式:st(img)}:null,
      媒体里有图:!!img,
      图标盒:icon?box(icon):null,
      名字:name?{text:txt(name),box:box(name),style:st(name),
        cls:cls(name)}:null,
      html:(b.outerHTML||'').slice(0,420)};});

  // ★ 整个右栏的**可见子树**（兜底：结构上还有什么没被上面读到）
  out['右栏可见子树']=[...aside.querySelectorAll('*')].filter(e=>{
    const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&r.height<200;}).slice(0,60).map(e=>({
    tag:e.tagName,role:e.getAttribute('role')||'',text:txt(e).slice(0,26),
    aria:e.getAttribute('aria-label')||'',box:box(e),
    cls:cls(e)}));

  // ★ 积分（底栏那颗）
  const hits=[];
  for(const e of document.querySelectorAll('span,div,b')){
    const t=txt(e); if(!/^\\d+$/.test(t)||e.children.length!==0)continue;
    const r=e.getBoundingClientRect(); if(r.width<=0||r.height<=0)continue;
    const x=Math.round(r.x), y=Math.round(r.y);
    if(x>=540&&x<=575&&y>=855&&y<=885)hits.push({t,x,y});}
  out['积分']=hits;
  return out;}"""


def read_credit(page):
    """★ 只读**那一颗**积分（x 540..575、y 855..885）。"""
    return page.evaluate("""()=>{
      const hits=[];
      for(const e of document.querySelectorAll('span,div,b')){
        const t=(e.textContent||'').trim();
        if(!/^\\d+$/.test(t)||e.children.length!==0)continue;
        const r=e.getBoundingClientRect();
        if(r.width<=0||r.height<=0)continue;
        const x=Math.round(r.x), y=Math.round(r.y);
        if(x>=540&&x<=575&&y>=855&&y<=885)hits.push({t,x,y});}
      return hits;}""")


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
                if bb:
                    pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
                pg.wait_for_timeout(4000)

            # ★ 进「编辑角色」大编辑器
            ok_edit = False
            for e in pg.query_selector_all("span,div,button,a,p"):
                if (e.text_content() or "").strip() != "编辑角色":
                    continue
                bb = e.bounding_box()
                if not bb:
                    continue
                pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
                ok_edit = True
                break
            log["★是否点到编辑角色"] = ok_edit
            pg.wait_for_timeout(5000)

            # ★ 点左列第二段（**真实转移**，不是原地 no-op）
            before = read_credit(pg)
            ok_seg = pg.evaluate("""(label)=>{
              const b=[...document.querySelectorAll('button')]
                .find(e=>(e.textContent||'').trim()===label);
              if(!b)return false; b.click(); return true;}""", SEGMENT)
            pg.wait_for_timeout(3000)
            after = read_credit(pg)
            log["★分段_是否点到"] = ok_seg
            log["★分段_积分是否变化"] = (before != after)
            if before != after:
                log["★★ 积分变了 ⟹ 立刻停"] = True
                raise SystemExit("积分变了")

            log["★读数"] = pg.evaluate(MEASURE)

            # ★ 再核一次积分（读完不点 ⟹ 必须一致）
            log["★读完_积分是否变化"] = (read_credit(pg) != after)
    except SystemExit:
        pass
    except Exception:
        log["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        for k, v in log.items():
            if k.startswith("★") and k != "★读数":
                print("  %-24s %s" % (k, json.dumps(v, ensure_ascii=False)[:90]))
        r = log.get("★读数") or {}
        if r:
            print("  H3:", json.dumps((r.get("H3") or {}).get("text"), ensure_ascii=False))
            print("  卡片数:", len(r.get("卡片") or []))
            for c in (r.get("卡片") or []):
                print("   -", json.dumps((c.get("名字") or {}).get("text"), ensure_ascii=False),
                      c.get("box"), "图:", c.get("媒体里有图"),
                      "pressed:", c.get("pressed"), "aria:", json.dumps(c.get("aria"), ensure_ascii=False))
        if log.get("异常"):
            print("异常：", log["异常"])


if __name__ == "__main__":
    sys.exit(main())
