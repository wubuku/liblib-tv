#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 843 源站探针（**只读**）：「妆造」页的 **11 个分类 chip** ＋ 每个分类的**卡片清单**。

## 为什么必须再跑一趟

batch 841／842 的 raw 只采到了**默认那个分类**（眉毛）的 13 张卡片
⟹ ⟹ 另外 **10 个分类**的卡片清单**完全没测过**。

⟹ 而 chip 是 `role=tab` ⟹ ⟹ **点它会换掉下面整个卡片网格**
⟹ ⟹ 不测就实现 = 编造 ⟹ ⟹ 本趟把 11 个分类**逐个点一遍**。

★ **只读**：只点右栏页签（妆造）＋ 只点**分类 chip** ⟹ ⟹
  **不点**「确认生成／保存／智能调整」⟹ ⟹ **不消耗** ⚡44
  ⟹ ⟹ 每次点击前后都核对那一颗积分（x 540..575、y 855..885）。

★ 输出：`/tmp/liblib_source_843_makeup.json`
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

URL = ("https://www.liblib.tv/canvas"
       "?spaceId=7709759&projectId=a860e1da8e9e4504bececda022386429")
COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_843_makeup.json")

CHIP_TEXTS = ["眉毛", "美瞳", "卧蚕", "眼影", "睫毛",
              "修容", "腮红", "唇彩", "妆饰", "眼线", "高光"]

MEASURE = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\\s+/g,' ');
  const st=(e)=>{const cs=getComputedStyle(e);
    return {fontSize:cs.fontSize,fontWeight:cs.fontWeight,lineHeight:cs.lineHeight,
      color:cs.color,backgroundColor:cs.backgroundColor,borderRadius:cs.borderRadius,
      borderTopWidth:cs.borderTopWidth,borderTopColor:cs.borderTopColor,
      paddingLeft:cs.paddingLeft,paddingTop:cs.paddingTop,gap:cs.gap};};

  const aside=[...document.querySelectorAll('aside')].find(a=>{
    const r=a.getBoundingClientRect();return r.x>=1273&&Math.round(r.width)===288;});
  if(!aside)return {err:'右栏没找到'};
  const out={};
  out['右栏盒']=box(aside);

  // ★ H4 标题（含那枚「i」）
  const h4=aside.querySelector('h4');
  out['H4']=h4?{text:txt(h4).replace(/i$/,''),box:box(h4),style:st(h4),
    cls:(h4.className||'').slice(0,110),
    i盒:(()=>{const i=h4.querySelector('[role="img"]');return i?box(i):null;})(),
    html:(h4.outerHTML||'').slice(0,400)}:null;

  // ★ 分类 chip（role=tab 且 50×26）
  const chips=[...aside.querySelectorAll('[role="tab"]')].filter(e=>{
    const r=e.getBoundingClientRect();return Math.round(r.width)===50&&Math.round(r.height)===26;});
  out['chip']=chips.map(e=>({text:txt(e),box:box(e),style:st(e),
    selected:e.getAttribute('aria-selected')==='true',
    cls:(e.className||'').slice(0,110)}));

  // ★ 分类容器 ＋ 卡片面板
  const tl=aside.querySelector('[role="tablist"]');
  out['chip容器']=tl?{box:box(tl),style:st(tl),cls:(tl.className||'').slice(0,110)}:null;
  const panel=aside.querySelector('[role="tabpanel"]');
  out['tabpanel']=panel?{box:box(panel),style:st(panel),
    cls:(panel.className||'').slice(0,110),aria:panel.getAttribute('aria-label')||''}:null;

  // ★ 卡片：76×96 的按钮 ＋ 媒体区 ＋ 名字 ＋ 有没有图
  const cards=[...panel?panel.querySelectorAll('button'):[]].filter(e=>{
    const r=e.getBoundingClientRect();return Math.round(r.width)===76&&Math.round(r.height)===96;});
  out['卡片']=cards.map(b=>{
    const img=b.querySelector('img');
    const name=[...b.querySelectorAll('span')].find(s=>
      s.children.length===0&&txt(s)&&Math.round(s.getBoundingClientRect().height)===16);
    const media=b.firstElementChild;
    return {aria:b.getAttribute('aria-label')||'',pressed:b.getAttribute('aria-pressed'),
      box:box(b),
      媒体盒:media?box(media):null,
      媒体样式:media?st(media):null,
      名字:name?{text:txt(name),box:box(name),style:st(name)}:null,
      图:img?{src:(img.currentSrc||img.src||'').slice(0,120),box:box(img),
        natural:[img.naturalWidth,img.naturalHeight]}:null,
      媒体里有图:!!img};});

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
                if bb:
                    pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
                pg.wait_for_timeout(4000)
            log["★是否点到编辑角色"] = click_text(pg, "编辑角色")
            pg.wait_for_timeout(5000)

            # ★ 先切到「妆造」页签
            before = read_credit(pg)
            ok = pg.evaluate("""()=>{
              const b=[...document.querySelectorAll('button')]
                .find(e=>(e.getAttribute('aria-label')||'')==='妆造');
              if(!b)return false; b.click(); return true;}""")
            pg.wait_for_timeout(3000)
            after = read_credit(pg)
            log["★妆造页签_是否点到"] = ok
            log["★妆造页签_积分是否变化"] = (before != after)
            if before != after:
                log["★★ 积分变了 ⟹ 立刻停"] = True
                raise SystemExit("积分变了")

            # ★ 逐个点 11 个分类 chip ⟹ 采每个分类的卡片清单
            cats = {}
            for name in CHIP_TEXTS:
                before = read_credit(pg)
                clicked = pg.evaluate("""(name)=>{
                  const b=[...document.querySelectorAll('[role="tab"]')]
                    .find(e=>(e.textContent||'').trim()===name);
                  if(!b)return false; b.click(); return true;}""", name)
                pg.wait_for_timeout(1800)
                after = read_credit(pg)
                cats[name] = pg.evaluate(MEASURE)
                log["★分类_%s_积分是否变化" % name] = (before != after)
                log["★分类_%s_是否点到" % name] = clicked
                if before != after:
                    log["★★ 积分变了 ⟹ 立刻停"] = True
                    break
            log["★各分类读数"] = cats
    except SystemExit:
        pass
    except Exception:
        log["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        for k, v in log.items():
            if k.startswith("★") and k != "★各分类读数":
                print("  %-28s %s" % (k, json.dumps(v, ensure_ascii=False)[:90]))
        if log.get("异常"):
            print("异常：", log["异常"])


if __name__ == "__main__":
    sys.exit(main())
