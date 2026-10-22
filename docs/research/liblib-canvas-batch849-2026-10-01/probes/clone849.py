#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 849 clone 侧探针：读第四段「服装造型」的**另外两页**（服装／AI 生成）。

★ 源站基准（**只读**实测，raw 入库在
  `docs/research/liblib-canvas-batch848-2026-10-01/raw/source-848-p1.json`
  ＋ `raw/source-848-p2.json`）：
  - **P1「服装」**：小标题「服装」240×22 ＋ **7 枚**分类 chip（50×26）
    ＋ **24 张**服装卡（76×155）＋ ★ **有**底部生成遮罩
  - **P2「AI 生成」**：卡片 240×168（输入框 240×140 ＋ 圆按钮 28×28 ＋ 胶囊 119×28）
    ＋「确认生成」240×36（★ 在**内容流**里 ⟹ ⟹ **没有**底部生成遮罩）
  - ★ **页签宽度随选中态变**：造型 56／服装 56／AI 生成 73（选中时）；未选中一律 24

★ 输出：`/tmp/b849-clone-outfit.json`
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path("/tmp/b849-clone-outfit.json")

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
      borderLeftWidth:cs.borderLeftWidth,borderLeftColor:cs.borderLeftColor,
      borderRightWidth:cs.borderRightWidth,borderRightColor:cs.borderRightColor,
      paddingLeft:cs.paddingLeft,paddingTop:cs.paddingTop,paddingRight:cs.paddingRight,
      paddingBottom:cs.paddingBottom,marginTop:cs.marginTop,marginBottom:cs.marginBottom,
      gap:cs.gap,rowGap:cs.rowGap,columnGap:cs.columnGap,
      display:cs.display,alignItems:cs.alignItems,justifyContent:cs.justifyContent,
      overflow:cs.overflow,overflowY:cs.overflowY,
      gridTemplateColumns:cs.gridTemplateColumns,fontFamily:cs.fontFamily,
      appearance:cs.appearance,objectFit:cs.objectFit,
      boxShadow:cs.boxShadow,outlineWidth:cs.outlineWidth,outlineColor:cs.outlineColor,
      outlineStyle:cs.outlineStyle,filter:cs.filter,opacity:cs.opacity};};

  const col=root.querySelector('.ce-col-right');
  out['右栏盒']=col?rel(col):null;

  // ★ 子页签行：三枚（★ **宽度随选中态变** ⟹ ⟹ 三页要各读一次）
  const tabs=root.querySelectorAll('[data-character-editor-outfit-tab]');
  const tabRow=tabs.length?tabs[0].parentElement:null;
  out['子页签行']=tabRow?{box:rel(tabRow),style:sty(tabRow),
    页签:[...tabs].map(b=>({
      id:b.getAttribute('data-character-editor-outfit-tab'),
      aria:b.getAttribute('aria-label')||'',text:txt(b),
      selected:b.getAttribute('aria-selected'),
      box:rel(b),style:sty(b),
      文字盒:(()=>{const ss=[...b.querySelectorAll('span')].filter(x=>txt(x));
        const s=ss.length?ss[ss.length-1]:null;return s?rel(s):null;})(),
      文字样式:(()=>{const ss=[...b.querySelectorAll('span')].filter(x=>txt(x));
        const s=ss.length?ss[ss.length-1]:null;return sty(s);})(),
      图标盒:(()=>{const s=b.querySelector('svg');return s?rel(s):null;})()}))}:null;

  // ★★ P1「服装」页
  const title=root.querySelector('[data-character-editor-outfit-clothes-title]');
  const chips=root.querySelectorAll('[data-character-editor-outfit-clothes-chip]');
  const cards=root.querySelectorAll('[data-character-editor-outfit-clothes-card]');
  out['服装页']={
    小标题盒:title?rel(title):null,小标题文字:title?txt(title):null,
    小标题样式:title?sty(title):null,
    分类chip数:chips.length,
    分类chip:[...chips].map(c=>({文字:txt(c),box:rel(c),style:sty(c),
      选中:c.getAttribute('aria-pressed')})),
    卡片数:cards.length,
    卡片:[...cards].map(c=>{
      const media=c.querySelector('.ce-card-media');
      const img=media?media.querySelector('img'):null;
      const name=c.querySelector('.ce-card-name');
      return {名字:name?txt(name):null,名字盒:name?rel(name):null,
        名字样式:name?sty(name):null,
        卡盒:rel(c),卡样式:sty(c),
        媒体盒:media?rel(media):null,媒体样式:media?sty(media):null,
        图盒:img?rel(img):null,图样式:img?sty(img):null,
        图源:img?img.getAttribute('src'):null,
        选中:c.getAttribute('aria-pressed')};})};

  // ★★ P2「AI 生成」页
  const card=root.querySelector('[data-character-editor-outfit-ai-card]');
  const ta=root.querySelector('[data-character-editor-outfit-ai-textarea]');
  const round=root.querySelector('[data-character-editor-outfit-ai-round]');
  const pill=root.querySelector('[data-character-editor-outfit-ai-pill]');
  const upload=root.querySelector('[data-character-editor-outfit-ai-upload]');
  const gen=root.querySelector('[data-character-editor-outfit-ai-generate]');
  out['AI页']={
    卡片盒:card?rel(card):null,卡片样式:card?sty(card):null,
    输入框盒:ta?rel(ta):null,输入框样式:ta?sty(ta):null,
    输入框占位:ta?ta.getAttribute('placeholder'):null,
    输入框aria:ta?ta.getAttribute('aria-label'):null,
    圆按钮盒:round?rel(round):null,圆按钮样式:round?sty(round):null,
    圆按钮aria:round?round.getAttribute('aria-label'):null,
    圆按钮文字:round?txt(round):null,
    胶囊盒:pill?rel(pill):null,胶囊样式:pill?sty(pill):null,
    胶囊aria:pill?pill.getAttribute('aria-label'):null,
    胶囊文字:pill?txt(pill):null,
    上传aria:upload?upload.getAttribute('aria-label'):null,
    确认生成盒:gen?rel(gen):null,确认生成样式:gen?sty(gen):null,
    确认生成文字:gen?txt(gen):null};

  // ★ 底部生成行（★ P2 **不该有** ⟹ ⟹ 计数应为 0）
  out['底部生成数']=root.querySelectorAll('[data-character-editor-generate]').length;
  out['生成行盒']=(()=>{const g=root.querySelector('[data-character-editor-generate]');
    return g?rel(g):null;})();
  out['智能调整数']=root.querySelectorAll('[data-character-editor-smart]').length;

  // ★ 空态说明（★ 第四段现在**没有**「未实测」说明了 ⟹ ⟹ 应当为 null）
  out['空态']=(()=>{const e=root.querySelector('[data-character-editor-empty]');
    return e?txt(e):null;})();
  return out;}"""


def open_editor(pg):
    pg.goto(BASE + "/?batch849=1", wait_until="domcontentloaded")
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


def wait_stable(pg, tries=60):
    """★ 等布局**稳定**再读（★ 字体/图片落位前右栏会差 2px ⟹ ⟹ 门禁容差只有 ±1）。"""
    last = None
    stable = 0
    for _ in range(tries):
        b = pg.evaluate("""()=>{const c=document.querySelector('.ce-col-right');
          if(!c)return null;const r=c.getBoundingClientRect();
          return {x:Math.round(r.x),y:Math.round(r.y),
                  w:Math.round(r.width),h:Math.round(r.height)};}""")
        if b and b == last:
            stable += 1
            if stable >= 3:
                return b
        else:
            stable = 0
        last = b
        pg.wait_for_timeout(250)
    return last


def click_box(pg, selector, dx=0.5, dy=0.5):
    """★ 点一个元素 ⟹ ⟹ **先 scrollIntoView，再把模态的滚动复位**。

    ★★ 模态是 `overflow:hidden` 且内容比它高 2px ⟹ ⟹ `scrollIntoView` 会把模态滚 2px
    ⟹ ⟹ 整棵树（读数）整体上移 2px ⟹ ⟹ 门禁 ±1 容差会**假红** ⟹ ⟹ 必须复位。
    """
    scrolled = pg.evaluate("""(sel)=>{
      const e=document.querySelector(sel);
      if(!e)return false;
      e.scrollIntoView({block:'center'});
      for(const m of document.querySelectorAll('[data-character-editor]')){
        m.scrollTop=0; m.scrollLeft=0;}
      return true;}""", selector)
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


def main() -> int:
    result = {}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": 1920, "height": 1080},
                                      locale="zh-CN")
            pg = ctx.new_page()
            open_editor(pg)
            # ★★ 「编辑角色」CTA 才是**打开编辑器**的那一步
            #   ⟹ ⟹ 只点角色库里的卡片**不会**打开编辑器（它只设 currentId）
            result["★编辑角色CTA盒"] = click_box(pg, '[data-character-studio-cta="edit"]')
            pg.wait_for_timeout(600)

            # ★ 点左列第四段（服装造型）
            result["★点到_第四段"] = click_box(
                pg, '[data-character-editor-segment="outfit"]')
            result["★布局稳定后_右栏盒"] = wait_stable(pg)

            # ── 三页各读一次（★ 页签宽度随选中态变 ⟹ ⟹ 必须三页都读）──
            for tab_id, key in (("style", "造型"), ("clothes", "服装"), ("ai", "AI 生成")):
                result["★点到_%s" % key] = click_box(
                    pg, '[data-character-editor-outfit-tab="%s"]' % tab_id)
                wait_stable(pg)
                result[key] = pg.evaluate(READ)
            # ★ 再读一次「服装」页 ⟹ ⟹ 验证「切回后内容真的回来」
            result["★点到_服装_再读"] = click_box(
                pg, '[data-character-editor-outfit-tab="clothes"]')
            wait_stable(pg)
            result["服装页_再读"] = pg.evaluate(READ)
            browser.close()
    except Exception:
        result["★异常"] = traceback.format_exc()
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", OUT)
    for k in ("造型", "服装", "AI 生成", "服装页_再读"):
        if k in result and isinstance(result[k], dict):
            r = result[k]
            print("  %-10s 页签宽 %s ｜ chip %s ｜ 卡 %s ｜ 底部生成 %s"
                  % (k,
                     [t["box"]["w"] for t in (r.get("子页签行") or {}).get("页签", [])],
                     (r.get("服装页") or {}).get("分类chip数"),
                     (r.get("服装页") or {}).get("卡片数"),
                     r.get("底部生成数")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
