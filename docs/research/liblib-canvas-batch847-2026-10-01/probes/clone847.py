#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 847 clone 侧探针：读左列第五段「音色音调」（标题行页签 ＋ 工具行 ＋ 20 条音色）。

★ 源站基准（**只读**实测，raw 入库在
  `docs/research/liblib-canvas-batch847-2026-10-01/raw/source-847-voice.json`）：
  - 右栏内层 288 宽 @1273 是 `flex min-h-0 flex-1 flex-col px-6` ⟹ ⟹ **三块**：
    ① 标题行 240×40 @rel(24,0) ＝ 三枚页签（音色库 70／我的音色 24／AI 生成 24）
    ② 工具行 240×32 @rel(24,48) ＝ 两枚 32×32（搜索／筛选音色），间隙 2
    ③ 滚动区 240×514 @rel(24,88) ＝ 20 张音色卡，滚动高 1192
  - 音色卡 240×48，步进 56；主按钮 198×40 ＋ 播放按钮 32×32
  - **这一段没有底部生成行**（batch 841 raw：右栏底部无任何按钮）

★ 输出：`/tmp/b847-clone-voice.json`
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path("/tmp/b847-clone-voice.json")

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
      overflow:cs.overflow,overflowY:cs.overflowY,
      gridTemplateColumns:cs.gridTemplateColumns,fontFamily:cs.fontFamily,
      appearance:cs.appearance,objectFit:cs.objectFit,
      boxShadow:cs.boxShadow,outlineWidth:cs.outlineWidth,outlineColor:cs.outlineColor,
      outlineStyle:cs.outlineStyle,filter:cs.filter,opacity:cs.opacity};};

  const col=root.querySelector('.ce-col-right');
  out['右栏盒']=col?rel(col):null;

  // ★ 标题行：三枚页签（★ 源站：音色库 70 宽带文字，另两枚 24 宽只有图标）
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
      // ★ 取**最内层**带文字的 span（★ 源站是「外层 span ＋ 内层文字 span」⟹ ⟹ 同口径）
      文字盒:(()=>{const ss=[...b.querySelectorAll('span')].filter(x=>txt(x));
        const s=ss.length?ss[ss.length-1]:null;return s?rel(s):null;})(),
      文字样式:(()=>{const ss=[...b.querySelectorAll('span')].filter(x=>txt(x));
        const s=ss.length?ss[ss.length-1]:null;return s?sty(s):null;})(),
      图标盒:(()=>{const s=b.querySelector('svg');return s?rel(s):null;})()}))}:null;

  // ★ 工具行：两枚 32×32
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

  // ★ 底部生成行（★ 这一段**整行都不该有**）
  out['确认生成数']=root.querySelectorAll('[data-character-editor-generate]').length;
  out['智能调整数']=root.querySelectorAll('[data-character-editor-smart]').length;
  out['生成行盒']=(()=>{const g=root.querySelector('[data-character-editor-generate]');
    return g?rel(g):null;})();

  // ★ 空态说明（★ 切到「我的音色」/「AI 生成」才该出现）
  out['空态']=(()=>{const e=root.querySelector('[data-character-editor-empty]');
    return e?txt(e):null;})();
  // ★★ **batch 848 起**：★ 「我的音色」页**已实测并实现** ⟹ ⟹ 读它的**实测空态**
  out['我的音色空态']=(()=>{const e=root.querySelector("[data-character-editor-voice-empty='mine']");
    return e?{...rel(e),text:txt(e)}:null;})();
  out['脸部页签数']=root.querySelectorAll('[data-character-editor-tab]').length;
  return out;}"""


def open_editor(pg):
    pg.goto(BASE + "/?batch847=1", wait_until="domcontentloaded")
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
    """★ 等布局**稳定**再读。

    ★★ **为什么必须有这一步**：编辑器刚打开的那一帧，字体/图片还没落位
    ⟹ ⟹ 右栏的 y 会比稳定值**小 2px**（实测 68 ⟹ ⟹ 稳定后是 70）
    ⟹ ⟹ 而源站的右栏是 **70** ⟹ ⟹ 若在未稳定的帧上读数 ⟹ ⟹ **差 2px**
    ⟹ ⟹ 而门禁的位置容差是 ±1 ⟹ ⟹ 那会变成**时好时坏的假红**。
    ⟹ ⟹ ★ 这里轮询到「连续三次读数相同」才返回 ⟹ ⟹ 读数才可复现。
    """
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
    """★ 点一个元素（真实鼠标点击）⟹ ⟹ **先 scrollIntoView**。

    ★★ 这一段**没有**底部生成遮罩 ⟹ ⟹ 卡片在可视区外时不会被遮罩挡住
    ⟹ ⟹ 但仍显式滚动 ⟹ ⟹ 免得点到空气（★ 「点了空气」在读数上只表现为
    ⟹ ⟹ 「选中态没变」⟹ ⟹ 极易误判成「clone 的交互坏了」）。

    ★★★ **必须把模态的滚动复位**（★★ 本轮踩到的**真坑**）：
      模态是 `overflow: hidden`，而它的内容**比它高 2px**
      （底栏 672＋88 ＝ 760 > 758）⟹ ⟹ **`overflow:hidden` 的元素仍可被程序滚动**
      ⟹ ⟹ `scrollIntoView` 找不到更近的可滚动祖先时就会**把模态本身滚 2px**
      ⟹ ⟹ 于是**整棵树**（三列 ＋ 底栏）**整体上移 2px**
      ⟹ ⟹ 读数会整片差 2px ⟹ ⟹ 而门禁的位置容差只有 ±1 ⟹ ⟹ 变成假红。
      ★★ 这**不是** clone 的缺陷：★ **源站同样如此**（源站的底栏也是 672＋88）
      ⟹ ⟹ 所以正解是**探针别去滚它** ⟹ ⟹ 这里显式复位。
    """
    scrolled = pg.evaluate("""(sel)=>{
      const e=document.querySelector(sel);
      if(!e)return false;
      e.scrollIntoView({block:'center'});
      // ★★ 复位：把 scrollIntoView 可能造成的滚动**全部撤掉**
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
            out["A_第五段"] = pg.evaluate(READ)

            # ★ 点第三张音色卡（青年大学生音色）⟹ 选中态应当转移
            out["★点到_第三张卡"] = click_box(pg,
                                          '[data-character-editor-voice-main="青年大学生音色"]')
            wait_stable(pg)
            out["B_点卡后"] = pg.evaluate(READ)

            # ★ 点「我的音色」页签 ⟹ 内容**未实测** ⟹ 应显示如实说明
            out["★点到_我的音色"] = click_box(pg,
                                          '[data-character-editor-voice-tab="mine"]')
            wait_stable(pg)
            out["C_切到我的音色"] = pg.evaluate(READ)

            # ★ 切回「音色库」⟹ 20 张卡应当回来
            out["★点到_音色库"] = click_box(pg,
                                          '[data-character-editor-voice-tab="library"]')
            wait_stable(pg)
            out["D_切回音色库"] = pg.evaluate(READ)

            # ★★ 顺带读**第二段**（traits）的底部生成行
            #   （★ batch 841 raw：那一段是**整宽 240×36** 的「确认生成」，没有「智能调整」）
            out["★点到_第二段"] = click_box(pg,
                                          '[data-character-editor-segment="traits"]')
            wait_stable(pg)
            out["E_第二段"] = pg.evaluate(READ)

            # ★★ 再读**第三段**（body）
            out["★点到_第三段"] = click_box(pg,
                                          '[data-character-editor-segment="body"]')
            wait_stable(pg)
            out["F_第三段"] = pg.evaluate(READ)

            # ★★ 读「脸部精修」段（★ **只有**那一段才有 196＋36 的「智能调整」）
            out["★点到_第一段"] = click_box(pg,
                                          '[data-character-editor-segment="face"]')
            wait_stable(pg)
            out["G_第一段"] = pg.evaluate(READ)

            # ★★ 读「服装造型」段（★ 846 已实现 ⟹ ⟹ 它的生成行是整宽 240×36）
            out["★点到_第四段"] = click_box(pg,
                                          '[data-character-editor-segment="outfit"]')
            wait_stable(pg)
            out["H_第四段"] = pg.evaluate(READ)

            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        if out.get("异常"):
            print("异常：", out["异常"])
        for stage in ("A_第五段", "B_点卡后", "C_切到我的音色", "D_切回音色库",
                      "E_第二段", "F_第三段", "G_第一段", "H_第四段"):
            r = out.get(stage) or {}
            if not r:
                continue
            t = (r.get("标题行") or {}).get("页签") or []
            print("── %-14s 页签=%d 工具=%d 卡=%d 滚动高=%s 空态=%r 生成=%s 智能=%s"
                  % (stage, len(t), len((r.get("工具行") or {}).get("按钮") or []),
                     len(r.get("音色卡") or []), (r.get("滚动区") or {}).get("滚动高"),
                     (r.get("空态") or "")[:12], r.get("确认生成数"), r.get("智能调整数")))


if __name__ == "__main__":
    sys.exit(main())
