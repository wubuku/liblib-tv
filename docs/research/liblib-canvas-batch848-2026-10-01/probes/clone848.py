#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 848 clone 侧探针：读第五段「音色音调」的**另外两页**（我的音色／AI 生成）。

★ 源站基准（**只读**实测，raw 入库在
  `docs/research/liblib-canvas-batch848-2026-10-01/raw/source-848-p3.json`
  ＋ `raw/source-848-p4.json`）：
  - **P3「我的音色」**：标题行 ＋ **工具行（两枚 32×32）** ＋ 滚动区 240×514
    ＋ 空态「暂无音色数据」240×96
  - **P4「AI 生成」**：标题行 ＋ **没有工具行** ＋ 内容区 240×562
    ＋ 输入框 240×120 ＋「生成音色」240×36（角标 36×16，数字「21」）
    ＋「生成历史」240×16 ＋ 空态「暂无历史记录」240×64
  - ★ **页签宽度随选中态变**：音色库 70／我的音色 84／AI 生成 73（选中时）；
    未选中一律 24（★ 三份 raw 交叉校验，见 `probes/gen848_data.py`）

★ 输出：`/tmp/b848-clone-voice.json`
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path("/tmp/b848-clone-voice.json")

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

  // ★ 标题行：三枚页签（★ **宽度随选中态变** ⟹ ⟹ 三页要各读一次）
  const tabs=root.querySelectorAll('[data-character-editor-voice-tab]');
  const tabRow=tabs.length?tabs[0].parentElement:null;
  out['标题行']=tabRow?{box:rel(tabRow),style:sty(tabRow),
    边框:(()=>{const cs=getComputedStyle(tabRow);
      return {borderBottomWidth:cs.borderBottomWidth,borderBottomColor:cs.borderBottomColor};})(),
    页签:[...tabs].map(b=>({
      id:b.getAttribute('data-character-editor-voice-tab'),
      aria:b.getAttribute('aria-label')||'',text:txt(b),
      selected:b.getAttribute('aria-selected'),
      box:rel(b),style:sty(b),
      文字盒:(()=>{const ss=[...b.querySelectorAll('span')].filter(x=>txt(x));
        const s=ss.length?ss[ss.length-1]:null;return s?rel(s):null;})(),
      文字样式:(()=>{const ss=[...b.querySelectorAll('span')].filter(x=>txt(x));
        const s=ss.length?ss[ss.length-1]:null;return sty(s);})(),
      图标盒:(()=>{const s=b.querySelector('svg');return s?rel(s):null;})()}))}:null;

  // ★ 工具行：两枚 32×32（★ P3「我的音色」页**也有** ⟹ ⟹ 要看这一页的工具数）
  const tools=root.querySelectorAll('[data-character-editor-voice-tool]');
  const toolRow=tools.length?tools[0].parentElement:null;
  out['工具行']=toolRow?{box:rel(toolRow),style:sty(toolRow),
    按钮:[...tools].map(b=>({
      kind:b.getAttribute('data-character-editor-voice-tool'),
      aria:b.getAttribute('aria-label')||'',box:rel(b),style:sty(b),
      图标盒:(()=>{const s=b.querySelector('svg');return s?rel(s):null;})()}))}:null;

  // ★ 滚动区 ＋ 20 张音色卡
  const list=root.querySelector('[data-character-editor-voice-list]');
  out['滚动区']=list?{box:rel(list),style:sty(list),滚动高:list.scrollHeight,
    客户端高:list.clientHeight}:null;
  out['音色卡']=[...root.querySelectorAll('[data-character-editor-voice-card]')].map(c=>{
    const main=c.querySelector('[data-character-editor-voice-main]');
    const icon=c.querySelector('.ce-voice-icon');
    const text=c.querySelector('.ce-voice-text');
    const name=c.querySelector('.ce-voice-name');
    const sub=c.querySelector('.ce-voice-sub');
    const play=c.querySelector('[data-character-editor-voice-play]');
    return {
      key:c.getAttribute('data-character-editor-voice-card'),
      名字:name?txt(name):null,名字盒:name?rel(name):null,名字样式:name?sty(name):null,
      副标:sub?txt(sub):null,副标盒:sub?rel(sub):null,副标样式:sub?sty(sub):null,
      卡盒:rel(c),卡样式:sty(c),
      主按钮盒:main?rel(main):null,
      图标区盒:icon?rel(icon):null,图标区样式:icon?sty(icon):null,
      图标盒:(()=>{const s=icon?icon.querySelector('svg'):null;return s?rel(s):null;})(),
      文字区盒:text?rel(text):null,
      播放按钮盒:play?rel(play):null,播放按钮样式:play?sty(play):null,
      播放图标盒:(()=>{const s=play?play.querySelector('svg'):null;return s?rel(s):null;})(),
      选中:main?main.getAttribute('aria-pressed'):null};});

  // ★★ P3「我的音色」页的空态
  const mineEmpty=root.querySelector('[data-character-editor-voice-empty="mine"]');
  out['我的音色空态']=mineEmpty?{text:txt(mineEmpty),box:rel(mineEmpty),
    style:sty(mineEmpty)}:null;

  // ★★ P4「AI 生成」页
  const ai=root.querySelector('[data-character-editor-voice-ai]');
  const ta=root.querySelector('[data-character-editor-voice-textarea]');
  const gen=root.querySelector('[data-character-editor-voice-generate]');
  const badge=root.querySelector('[data-character-editor-voice-badge]');
  const hist=root.querySelector('[data-character-editor-voice-history]');
  const histEmpty=root.querySelector('[data-character-editor-voice-history-empty]');
  out['AI页']=ai?{
    内容区盒:rel(ai),内容区样式:sty(ai),
    输入框盒:ta?rel(ta):null,输入框样式:ta?sty(ta):null,
    输入框占位:ta?ta.getAttribute('placeholder'):null,
    输入框aria:ta?ta.getAttribute('aria-label'):null,
    按钮盒:gen?rel(gen):null,按钮样式:gen?sty(gen):null,
    按钮aria:gen?gen.getAttribute('aria-label'):null,
    按钮文字:gen?txt(gen):null,
    角标盒:badge?rel(badge):null,角标样式:badge?sty(badge):null,
    角标文字:badge?txt(badge):null,
    历史区盒:hist?rel(hist):null,
    历史标题盒:(()=>{const h=hist?hist.querySelector('h3'):null;return h?rel(h):null;})(),
    历史标题文字:(()=>{const h=hist?hist.querySelector('h3'):null;return h?txt(h):null;})(),
    历史标题样式:(()=>{const h=hist?hist.querySelector('h3'):null;return h?sty(h):null;})(),
    历史空态盒:histEmpty?rel(histEmpty):null,
    历史空态文字:histEmpty?txt(histEmpty):null,
    历史空态样式:histEmpty?sty(histEmpty):null}:null;

  // ★ 底部生成行（★ 这一段**整行都不该有**）
  out['确认生成数']=root.querySelectorAll('[data-character-editor-generate]').length;
  out['智能调整数']=root.querySelectorAll('[data-character-editor-smart]').length;
  out['生成行盒']=(()=>{const g=root.querySelector('[data-character-editor-generate]');
    return g?rel(g):null;})();

  // ★ 空态说明（★ 第五段现在**没有**「未实测」说明了 ⟹ ⟹ 应当为 null）
  out['空态']=(()=>{const e=root.querySelector('[data-character-editor-empty]');
    return e?txt(e):null;})();
  out['脸部页签数']=root.querySelectorAll('[data-character-editor-tab]').length;
  return out;}"""


def open_editor(pg):
    pg.goto(BASE + "/?batch848=1", wait_until="domcontentloaded")
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

            # ★ 点左列第五段（音色音调）
            out["★点到_第五段"] = click_box(pg,
                                          '[data-character-editor-segment="voice"]')
            out["★布局稳定后_右栏盒"] = wait_stable(pg)
            out["A_音色库"] = pg.evaluate(READ)

            # ★ P3「我的音色」
            out["★点到_我的音色"] = click_box(pg,
                                          '[data-character-editor-voice-tab="mine"]')
            wait_stable(pg)
            out["B_我的音色"] = pg.evaluate(READ)

            # ★ P4「AI 生成」
            out["★点到_AI生成"] = click_box(pg,
                                          '[data-character-editor-voice-tab="ai"]')
            wait_stable(pg)
            out["C_AI生成"] = pg.evaluate(READ)

            # ★ 切回「音色库」⟹ 20 张卡应当回来
            out["★点到_音色库"] = click_box(pg,
                                          '[data-character-editor-voice-tab="library"]')
            wait_stable(pg)
            out["D_切回音色库"] = pg.evaluate(READ)

            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        if out.get("异常"):
            print("异常：", out["异常"])
        for stage in ("A_音色库", "B_我的音色", "C_AI生成", "D_切回音色库"):
            r = out.get(stage) or {}
            if not r:
                continue
            t = (r.get("标题行") or {}).get("页签") or []
            ai = r.get("AI页") or {}
            print("── %-12s 页签宽=%s 工具=%d 卡=%d 空态=%r 我的空态=%r AI区=%s"
                  % (stage,
                     [x.get("box", {}).get("w") for x in t],
                     len((r.get("工具行") or {}).get("按钮") or []),
                     len(r.get("音色卡") or []),
                     (r.get("空态") or "")[:8],
                     (r.get("我的音色空态") or {}).get("text"),
                     ai.get("内容区盒")))


if __name__ == "__main__":
    sys.exit(main())
