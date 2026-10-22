#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 846 源站探针（**只读**）：左列第四段「服装造型」的完整结构。

## 为什么必须再跑一趟

batch 841 的 raw 里，右栏子树**被探针的 `y<=833` 截断**了 ⟹ ⟹
这一段的**下半截**（发色／妆容／口红三块）**根本没进 raw** ⟹ ⟹
841 的 SEGMENT_NOTE 里那些条数（「发型 10 个／选发色 10 个 ＋ 自定义颜色／妆容 7 个／
选口红颜色 10 个」）**是当时读到的、不是完整清单** ⟹ ⟹ 不能直接照抄。

★ 本趟**不按 y 过滤** ⟹ ⟹ 直接从 DOM 里读**全部**元素 ⟹ ⟹ 清单与几何一次拿全。

## 这一段的结构（★ 与前三段**不同**）

    右栏第一层 ＝ **子页签行**（40 高）：「造型」（56 宽，带文字）＋「服装」＋「AI 生成」（各 24 宽）
      ⟹ ⟹ ★ **这一段有标题行**（前两段没有）⟹ ⟹ 内容起点比那两段**低 40px**
    右栏第二层 ＝ 滚动区（`px-6 pb-20 pt-4`）⟹ ⟹ 内容起点 ＝ 列顶 + 40 + 16
    内容 ＝ 若干「H3 ＋ chip 行 ＋ 卡片网格」的块：
      H3「发型」240×22（`text-sm font-normal leading-[22px]`）
        ├ chip 行（`flex flex-wrap gap-1.5`）：50×26 的圆角 chip
        └ 卡片网格（`grid grid-cols-3 gap-x-1.5 gap-y-2 pt-1`）：76×96 的卡

★ **只读**：只点左列的**分段** ⟹ ⟹ **不消耗** ⚡44 ⟹ ⟹ 点击前后都核对那一颗积分。

★ 输出：`/tmp/liblib_source_846_outfit.json`
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

URL = ("https://www.liblib.tv/canvas"
       "?spaceId=7709759&projectId=a860e1da8e9e4504bececda022386429")
COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_846_outfit.json")

SEGMENT = "服装造型"

MEASURE = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\\s+/g,' ');
  const cls=(e)=>String((e&&e.getAttribute)?(e.getAttribute('class')||''):'');
  const st=(e)=>{if(!e)return null;const cs=getComputedStyle(e);
    return {fontSize:cs.fontSize,fontWeight:cs.fontWeight,lineHeight:cs.lineHeight,
      color:cs.color,backgroundColor:cs.backgroundColor,borderRadius:cs.borderRadius,
      borderTopWidth:cs.borderTopWidth,borderTopColor:cs.borderTopColor,
      paddingLeft:cs.paddingLeft,paddingTop:cs.paddingTop,paddingRight:cs.paddingRight,
      paddingBottom:cs.paddingBottom,gap:cs.gap,rowGap:cs.rowGap,columnGap:cs.columnGap,
      display:cs.display,alignItems:cs.alignItems,justifyContent:cs.justifyContent,
      gridTemplateColumns:cs.gridTemplateColumns,fontFamily:cs.fontFamily,
      appearance:cs.appearance,objectFit:cs.objectFit,
      boxShadow:cs.boxShadow,outlineWidth:cs.outlineWidth,outlineColor:cs.outlineColor,
      outlineStyle:cs.outlineStyle,filter:cs.filter,opacity:cs.opacity};};

  const aside=[...document.querySelectorAll('aside')].find(a=>{
    const r=a.getBoundingClientRect();return r.x>=1273&&Math.round(r.width)===288;});
  if(!aside)return {err:'右栏没找到'};
  const out={};
  out['右栏盒']=box(aside);

  // ★ 右栏的**直接子节点**（★ 用来判「这一段有没有标题行」）
  out['右栏直接子节点']=[...aside.children].map(e=>({
    tag:e.tagName,cls:cls(e),box:box(e),
    子节点数:e.children.length,
    滚动高:e.scrollHeight, 客户端高:e.clientHeight}));

  // ★★ **内层列**的子节点（★ 右栏真正的结构在这一层 ⟹ ⟹ 标题行 ＋ 滚动区）
  const inner=aside.firstElementChild;
  out['右栏内层']=inner?{tag:inner.tagName,cls:cls(inner),box:box(inner),
    子节点:[...inner.children].map(e=>({tag:e.tagName,cls:cls(e),box:box(e),
      子节点数:e.children.length,滚动高:e.scrollHeight,客户端高:e.clientHeight,
      孙节点:[...e.children].map(x=>({tag:x.tagName,cls:cls(x),box:box(x),
        子节点数:x.children.length}))}))}:null;

  // ★ **子页签行**（这一段有 ⟹ ⟹ 与前两段不同）
  const nav=aside.querySelector('nav');
  if(nav){
    out['子页签行']={box:box(nav),cls:cls(nav),style:st(nav),
      按钮:[...nav.querySelectorAll('button')].map(b=>({
        aria:b.getAttribute('aria-label')||'',text:txt(b),cls:cls(b),
        box:box(b),style:st(b),
        选中:b.getAttribute('aria-selected'),
        选中态:b.getAttribute('aria-current'),
        文字盒:(()=>{const s=[...b.querySelectorAll('span')].find(x=>txt(x));
          return s?box(s):null;})(),
        文字样式:(()=>{const s=[...b.querySelectorAll('span')].find(x=>txt(x));
          return s?st(s):null;})(),
        图标盒:(()=>{const s=b.querySelector('svg');return s?box(s):null;})()}))};
  }

  // ★ 滚动区（★ 按 `overflow-y:auto` 找 ⟹ ⟹ 不靠猜层级）
  const scroll=[...aside.querySelectorAll('*')].find(e=>{
    const cs=getComputedStyle(e);
    return (cs.overflowY==='auto'||cs.overflowY==='scroll')&&e.scrollHeight>e.clientHeight+4;});
  out['滚动区']=scroll?{box:box(scroll),cls:cls(scroll),style:st(scroll),
    滚动高:scroll.scrollHeight, 客户端高:scroll.clientHeight,
    子节点:[...scroll.children].map(e=>({tag:e.tagName,cls:cls(e),box:box(e),
      子节点数:e.children.length,
      孙节点:[...e.children].map(x=>({tag:x.tagName,cls:cls(x),box:box(x),
        子节点数:x.children.length,cls2:cls(x)}))}))}:null;

  // ★ **全部** H3（★ 不按 y 过滤）
  out['H3']=[...aside.querySelectorAll('h3')].map(h=>({
    text:txt(h),cls:cls(h),box:box(h),style:st(h)}));

  // ★ chip：圆角按钮（`rounded-full border px-3 py-1 text-xs`）
  out['chip']=[...aside.querySelectorAll('button')].filter(b=>/rounded-full/.test(cls(b)))
    .map(b=>({text:txt(b),cls:cls(b),box:box(b),style:st(b),
      aria:b.getAttribute('aria-label')||'',
      选中:b.getAttribute('aria-pressed')||b.getAttribute('aria-selected'),
      标题:(b.getAttribute('title')||''),
      子节点:[...b.children].map(x=>({tag:x.tagName,cls:cls(x),box:box(x),
        文本:txt(x),样式:st(x)}))}));

  // ★ 卡片网格：`group flex min-w-0 flex-col items-center gap-1 text-[11px] leading-4`
  const cards=[...aside.querySelectorAll('button')].filter(b=>/group flex min-w-0 flex-col/.test(cls(b)));
  out['卡片']=cards.map(b=>{
    const media=b.querySelector('span');
    const img=b.querySelector('img');
    const nameEl=[...b.querySelectorAll('span')].filter(s=>txt(s)&&s.children.length===0)[0]||null;
    return {aria:b.getAttribute('aria-label')||'',
      text:txt(b),
      名字:nameEl?txt(nameEl):null,
      名字盒:nameEl?box(nameEl):null,
      名字样式:nameEl?st(nameEl):null,
      卡盒:box(b),卡样式:st(b),
      媒体盒:media?box(media):null,媒体样式:media?st(media):null,
      有图:!!img,
      图盒:img?box(img):null,
      图源:img?((img.currentSrc||img.src||'').slice(0,160)):null,
      选中:b.getAttribute('aria-pressed')};});

  // ★ 颜色输入（源站的发色／口红可能有 `<input type=color>` 之类的入口）
  out['颜色输入']=[...aside.querySelectorAll('input')].map(i=>({
    type:i.getAttribute('type'),aria:i.getAttribute('aria-label')||'',
    value:i.value||'',box:box(i),style:st(i)}));

  // ★ **底部生成遮罩**（★ 这一段**特有**的一层：整宽 240×36 的「确认生成」，
  //   ⟹ ⟹ 与「脸部精修」段那枚 196×36 ＋ 36×36 的**不一样** ⟹ ⟹ 别照抄那一段）
  const mask=[...aside.querySelectorAll('*')].find(e=>/editorPanelGenerateMask/.test(cls(e)));
  out['生成遮罩']=mask?{box:box(mask),cls:cls(mask),
    子节点:[...mask.children].map(e=>({tag:e.tagName,cls:cls(e),box:box(e),
      文本:txt(e),样式:st(e),
      孙节点:[...e.children].map(x=>({tag:x.tagName,cls:cls(x),box:box(x),
        文本:txt(x),样式:st(x)}))}))}:null;

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

            before = read_credit(pg)
            # ★★ **前缀匹配**（★ 源站的按钮可能带角标 ⟹ ⟹ 精确文本会**点空气**）
            ok_seg = pg.evaluate("""(label)=>{
              const bs=[...document.querySelectorAll('button')].filter(e=>{
                const r=e.getBoundingClientRect();
                return r.x<700&&r.width>100;});
              const b=bs.find(e=>(e.textContent||'').trim().startsWith(label));
              if(!b)return false; b.click(); return true;}""", SEGMENT)
            pg.wait_for_timeout(3500)
            after = read_credit(pg)
            log["★分段_是否点到"] = ok_seg
            log["★分段_积分是否变化"] = (before != after)
            if before != after:
                log["★★ 积分变了 ⟹ 立刻停"] = True
                raise SystemExit("积分变了")

            reading = pg.evaluate(MEASURE)
            # ★★ **自证**：读到的必须是**目标段**（子页签行里有「造型」）
            nav_btns = [b.get("aria") for b in
                        ((reading.get("子页签行") or {}).get("按钮") or [])]
            log["★读数_子页签"] = nav_btns
            log["★读数_是目标段"] = ("造型" in nav_btns)
            if "造型" not in nav_btns:
                log["★★ 读到的**不是**目标段 ⟹ 这份读数不可信 ⟹ 立刻停"] = True
                raise SystemExit("读到的不是目标段")
            log["★读数"] = reading
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
                print("  %-24s %s" % (k, json.dumps(v, ensure_ascii=False)[:120]))
        r = log.get("★读数") or {}
        if r:
            print("  H3：", [(h.get("text"), h.get("box")) for h in (r.get("H3") or [])])
            print("  chip 数：", len(r.get("chip") or []),
                  "｜ 卡片数：", len(r.get("卡片") or []),
                  "｜ 颜色输入：", len(r.get("颜色输入") or []))
            for c in (r.get("chip") or [])[:12]:
                print("   chip %-10s %s" % (c.get("text"), c.get("box")))
        if log.get("异常"):
            print("异常：", log["异常"])


if __name__ == "__main__":
    sys.exit(main())
