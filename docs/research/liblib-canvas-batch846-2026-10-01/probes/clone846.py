#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 846 clone 侧探针：读左列第四段「服装造型」（子页签行 ＋ 四个小节）。

★ 源站基准（**只读**实测，raw 入库在
  `docs/research/liblib-canvas-batch846-2026-10-01/raw/source-846-outfit.json`）：
  - 右栏第一层 ＝ **子页签行**（40 高）：造型（56，带文字）／服装（24）／AI 生成（24）
  - 内容起点 ＝ 列顶 + 40 + 16(pt-4) ⟹ ⟹ 四个小节：发型／发色／妆容／口红
  - 发型 ＝ 7 枚 chip ＋ 12 张 76×96 的卡；发色 ＝ 11 枚 35×35 的色块
  - 妆容 ＝ 7 枚 chip（宽度随文案变）＋ 7 张卡；口红 ＝ 10 枚色块
  - 滚动区高 1312；底部**只有**整宽 240×36 的「确认生成」（没有「智能调整」）

★ 输出：`/tmp/b846-clone-outfit.json`
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path("/tmp/b846-clone-outfit.json")

READ = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\\s+/g,' ');
  const root=document.querySelector('[data-character-editor]');
  const out={};
  out['★是否有编辑器']=Boolean(root);
  if(!root)return out;
  const rb=box(root);
  out['模态盒']=rb;
  const rel=(e)=>{if(!e)return null;const b=box(e);
    return {x:b.x-rb.x,y:b.y-rb.y,w:b.w,h:b.h};};
  const sty=(e)=>{if(!e)return null;const cs=getComputedStyle(e);
    return {fontSize:cs.fontSize,fontWeight:cs.fontWeight,lineHeight:cs.lineHeight,
      color:cs.color,backgroundColor:cs.backgroundColor,borderRadius:cs.borderRadius,
      borderTopWidth:cs.borderTopWidth,borderTopColor:cs.borderTopColor,
      borderBottomWidth:cs.borderBottomWidth,borderBottomColor:cs.borderBottomColor,
      paddingLeft:cs.paddingLeft,paddingTop:cs.paddingTop,paddingRight:cs.paddingRight,
      paddingBottom:cs.paddingBottom,gap:cs.gap,rowGap:cs.rowGap,columnGap:cs.columnGap,
      display:cs.display,alignItems:cs.alignItems,justifyContent:cs.justifyContent,
      gridTemplateColumns:cs.gridTemplateColumns,fontFamily:cs.fontFamily,
      appearance:cs.appearance,objectFit:cs.objectFit,
      boxShadow:cs.boxShadow,outlineWidth:cs.outlineWidth,outlineColor:cs.outlineColor,
      outlineStyle:cs.outlineStyle,filter:cs.filter,opacity:cs.opacity};};

  const col=root.querySelector('.ce-col-right');
  out['右栏盒']=col?rel(col):null;
  // ★ 页签行（★ 这一段**有**⟹ ⟹ 这里读它有几枚、几何如何）
  const tabRow=root.querySelector('.ce-tabs');
  out['子页签行']=tabRow?{box:rel(tabRow),
    style:sty(tabRow),
    // ★★ 那条 **240px 宽的底边框线**（★ 源站 nav 的 `border-bottom`
    //   ⟹ ⟹ 像素对照实测：源站 y=270 整行有白 8% 的线 ⟹ ⟹ clone 之前**整条没画**）
    边框:(()=>{const cs=getComputedStyle(tabRow);
      return {borderBottomWidth:cs.borderBottomWidth,borderBottomColor:cs.borderBottomColor,
        borderBottomStyle:cs.borderBottomStyle};})(),
    按钮:[...tabRow.querySelectorAll('[data-character-editor-outfit-tab]')].map(b=>({
      id:b.getAttribute('data-character-editor-outfit-tab'),
      aria:b.getAttribute('aria-label')||'',text:txt(b),
      selected:b.getAttribute('aria-selected'),
      box:rel(b),style:sty(b),
      // ★★ 取**最内层**那个带文字的 span（★ 源站是「外层 grid span ＋ 内层文字 span」
      //   ⟹ ⟹ 只比外层会比到**结构差异**而不是几何差异 ⟹ ⟹ 取内层才是同口径）
      文字盒:(()=>{const ss=[...b.querySelectorAll('span')].filter(x=>txt(x));
        const s=ss.length?ss[ss.length-1]:null;return s?rel(s):null;})(),
      文字样式:(()=>{const ss=[...b.querySelectorAll('span')].filter(x=>txt(x));
        const s=ss.length?ss[ss.length-1]:null;return s?sty(s):null;})(),
      图标盒:(()=>{const s=b.querySelector('svg');return s?rel(s):null;})()}))}:null;
  // ★ 脸部段的六枚页签（★ 这一段**不该**有 ⟹ ⟹ 读它有没有）
  out['脸部页签数']=root.querySelectorAll('[data-character-editor-tab]').length;
  out['空态']=(()=>{const e=root.querySelector('[data-character-editor-empty]');
    return e?txt(e):null;})();

  // ★ 四个小节标题
  out['H3']=[...root.querySelectorAll('[data-character-editor-outfit-title]')].map(h=>({
    text:txt(h),box:rel(h),style:sty(h)}));

  // ★ chip（14 枚：发型 7 ＋ 妆容 7）
  out['chip']=[...root.querySelectorAll('[data-character-editor-outfit-chip]')].map(b=>({
    key:b.getAttribute('data-character-editor-outfit-chip'),
    text:txt(b),box:rel(b),style:sty(b),
    选中:b.getAttribute('aria-pressed')}));

  // ★ 色块（21 枚：发色 11 ＋ 口红 10）
  out['色块']=[...root.querySelectorAll('[data-character-editor-outfit-swatch]')].map(b=>({
    key:b.getAttribute('data-character-editor-outfit-swatch'),
    aria:b.getAttribute('aria-label')||'',text:txt(b),
    box:rel(b),style:sty(b),
    选中:b.getAttribute('aria-pressed'),
    有图:!!b.querySelector('svg'),
    图标盒:(()=>{const s=b.querySelector('svg');return s?rel(s):null;})()}));
  // ★ 卡片（19 张）
  out['卡片']=[...root.querySelectorAll('[data-character-editor-outfit-card]')].map(b=>{
    const media=b.querySelector('.ce-card-media');
    const img=b.querySelector('img');
    const name=b.querySelector('.ce-card-name');
    return {key:b.getAttribute('data-character-editor-outfit-card'),
      aria:b.getAttribute('aria-label')||'',
      名字:name?txt(name):null,
      名字盒:name?rel(name):null,
      名字样式:name?sty(name):null,
      卡盒:rel(b),卡样式:sty(b),
      媒体盒:media?rel(media):null,媒体样式:media?sty(media):null,
      有图:!!img,
      图盒:img?rel(img):null,
      图源:img?((img.currentSrc||img.src||'').slice(0,160)):null,
      选中:b.getAttribute('aria-pressed')};});

  // ★ 面板（滚动区长度）
  const panel=root.querySelector('.ce-panel--outfit')||root.querySelector('.ce-panel');
  out['面板']=panel?{box:rel(panel),滚动高:panel.scrollHeight,
    客户端高:panel.clientHeight}:null;

  // ★ 底部生成行（★ 这一段**只有**整宽的「确认生成」）
  const gen=root.querySelector('[data-character-editor-generate]');
  out['确认生成']=gen?{box:rel(gen),style:sty(gen),text:txt(gen)}:null;
  out['智能调整数']=root.querySelectorAll('[data-character-editor-smart]').length;
  return out;}"""


def open_editor(pg):
    pg.goto(BASE + "/?batch846=1", wait_until="domcontentloaded")
    pg.wait_for_timeout(3000)
    pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
    pg.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
    pg.evaluate("""() => {
      const cands=[...document.querySelectorAll('button,[role="button"]')];
      const b=cands.find(e=>e.getAttribute('aria-label')==='角色造型室')
        || cands.find(e=>(e.getAttribute('data-sidebar-btn')==='character-library'))
        || cands.find(e=>(e.textContent||'').trim()==='人物');
      if(b){b.click();return true;} return false;}""")
    pg.wait_for_timeout(1500)
    pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
    pg.evaluate("""() => {
      const t=[...document.querySelectorAll('[data-character-studio-tab]')]
        .find(e=>e.getAttribute('data-character-studio-tab')==='official');
      if(t)t.click();}""")
    pg.wait_for_timeout(800)
    pg.evaluate("""() => {
      const c=document.querySelector('[data-character-strip-card]');
      if(c)c.click();}""")
    pg.wait_for_timeout(700)


def click_box(pg, selector, dx=0.5, dy=0.5):
    """★ 点一个元素（真实鼠标点击）。

    ★★ **必须先把它滚进可视区** —— 这一段的滚动区高 1312 而可视高只有 562
    ⟹ ⟹ 「口红」那十枚色块在 rel y=1266 ⟹ ⟹ **在可视区之外**
    ⟹ ⟹ 不滚动就点 ⟹ ⟹ 鼠标落在生成遮罩上 ⟹ ⟹ **点了空气**
    ⟹ ⟹ 而「点了空气」在读数上只表现为「选中态没变」⟹ ⟹ 很容易误判成
    「clone 的交互坏了」⟹ ⟹ ★ 这里显式 scrollIntoView 再点。

    ★ 返回**点击时**的盒（⟹ ⟹ 滚动后的绝对坐标 ⟹ ⟹ 可自证点到了哪）。
    """
    scrolled = pg.evaluate("""(sel)=>{
      const e=document.querySelector(sel);
      if(!e)return false;
      e.scrollIntoView({block:'center'}); return true;}""", selector)
    pg.wait_for_timeout(350)
    b = pg.evaluate("""(sel)=>{
      const e=document.querySelector(sel);
      if(!e)return null; const r=e.getBoundingClientRect();
      return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),
              h:Math.round(r.height)};}""", selector)
    if not b:
        return None
    pg.mouse.click(b["x"] + b["w"] * dx, b["y"] + b["h"] * dy)
    pg.wait_for_timeout(400)
    b["★滚进可视区"] = scrolled
    return b


def main():
    out = {}
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            pg = ctx.new_page()
            open_editor(pg)
            out["★编辑角色CTA盒"] = click_box(pg, '[data-character-studio-cta="edit"]')
            pg.wait_for_timeout(600)

            out["★点到_第四段"] = click_box(pg,
                                           '[data-character-editor-segment="outfit"]')
            out["A_第四段"] = pg.evaluate(READ)

            # ★ 点一枚 chip（发型「古风」）⟹ 选中态应当转移
            out["★点到_古风"] = click_box(pg,
                                        '[data-character-editor-outfit-chip="发型-古风"]')
            out["B_点chip后"] = pg.evaluate(READ)

            # ★ 点一枚色块（口红的第三枚）⟹ 选中态应当转移
            out["★点到_口红色块"] = click_box(pg,
                                          '[data-character-editor-outfit-swatch="口红-2"]')
            out["C_点色块后"] = pg.evaluate(READ)

            # ★ 点一枚卡片（发型「长直发」）⟹ 选中态应当转移
            out["★点到_长直发"] = click_box(pg,
                                          '[data-character-editor-outfit-card="发型-长直发"]')
            out["D_点卡后"] = pg.evaluate(READ)

            # ★ 点第二枚子页签（服装）⟹ 内容**未实测** ⟹ 应显示如实说明
            out["★点到_服装子页签"] = click_box(pg,
                                            '[data-character-editor-outfit-tab="clothes"]')
            out["E_切到服装"] = pg.evaluate(READ)

            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        if out.get("异常"):
            print("异常：", out["异常"])
        for stage in ("A_第四段", "B_点chip后", "C_点色块后", "D_点卡后", "E_切到服装"):
            r = out.get(stage) or {}
            if not r:
                continue
            print("── %s  H3=%d chip=%d 色块=%d 卡片=%d 滚动高=%s 空态=%r 智能调整=%s"
                  % (stage, len(r.get("H3") or []), len(r.get("chip") or []),
                     len(r.get("色块") or []), len(r.get("卡片") or []),
                     (r.get("面板") or {}).get("滚动高"),
                     (r.get("空态") or "")[:14], r.get("智能调整数")))


if __name__ == "__main__":
    sys.exit(main())
