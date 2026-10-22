#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 850 clone 侧探针：读**预览区（中列）**的两态。

★ 源站基准（**只读**实测，raw 入库在
  `docs/research/liblib-canvas-batch850-2026-10-01/raw/source-850-{default,half,full}.json`）：
  - 中列 MAIN 624×602
  - 图区**四层**：467×550 → inset-0 → **变换层** → 图盒 425×542 → img
  - ★ 变换层：半身 = `matrix(3.84422,0,0,3.84422,-665.652,-173.149)`，全身 = `matrix(1,0,0,1,0,0)`
    ⟹ ⟹ ★ **源站默认就是「半身」**
  - 遮罩**三层**：外层 196 高 ＋ blur 228 高（`blur(16px)`）＋ 渐变 196 高（**17 段** linear-gradient）
    ⟹ ⟹ ★ 全身态整块**淡出**（opacity 0）
  - 取景工具行 73×32：两枚 32×32 按钮 ＋ **一枚 1×12 分隔线** ⟹ ⟹ 容器**透明**

★ ★ **同口径**：源站那趟**没有点任何左列分段**（default 态就是刚打开编辑器）
  ⟹ ⟹ 本探针也**不点分段** ⟹ ⟹ 两边读的是同一状态。

★ ★ **几何口径**：源站 raw 记的是 `getBoundingClientRect`（**变换后**的视觉盒）
  ⟹ ⟹ 半身态的图盒被放大了 1795×2114 ⟹ ⟹ **不可比**
  ⟹ ⟹ ⟹ 所以：
     · **full 态**（identity transform）比**全部几何**（此时视觉盒 ＝ 布局盒）；
     · **half 态**只比 **transform 矩阵** ＋ 与图无关的属性（opacity／backdrop-filter／transition）。
  ⟹ ⟹ clone 侧额外记 `布局盒`（offset*，**不受 transform 影响**）⟹ ⟹ 可逐项对。

★ 输出：`/tmp/b850-clone-preview.json`
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path("/tmp/b850-clone-preview.json")

READ = r"""()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\s+/g,' ');
  const root=document.querySelector('[data-character-editor]');
  const out={};
  out['★是否有编辑器']=Boolean(root);
  if(!root)return out;
  const rb=box(root);
  out['模态盒']=rb;
  const rel=(e)=>{if(!e)return null;const b=box(e);
    return {x:b.x-rb.x,y:b.y-rb.y,w:b.w,h:b.h};};
  // ★ 布局盒（★ 不受 transform 影响 ⟹ ⟹ 半身态也能比）
  const lay=(e)=>{if(!e)return null;
    return {x:e.offsetLeft,y:e.offsetTop,w:e.offsetWidth,h:e.offsetHeight};};
  const sty=(e)=>{if(!e)return null;const cs=getComputedStyle(e);
    return {color:cs.color,backgroundColor:cs.backgroundColor,
      backgroundImage:cs.backgroundImage.slice(0,900),
      backdropFilter:cs.backdropFilter,webkitBackdropFilter:cs.webkitBackdropFilter,
      borderRadius:cs.borderRadius,opacity:cs.opacity,visibility:cs.visibility,
      position:cs.position,zIndex:cs.zIndex,left:cs.left,top:cs.top,bottom:cs.bottom,
      right:cs.right,width:cs.width,height:cs.height,
      transform:cs.transform,transformOrigin:cs.transformOrigin,
      transitionProperty:cs.transitionProperty,
      transitionDuration:cs.transitionDuration,
      transitionTimingFunction:cs.transitionTimingFunction,
      transitionDelay:cs.transitionDelay,
      transition:cs.transition,
      gap:cs.gap,display:cs.display,alignItems:cs.alignItems,
      justifyContent:cs.justifyContent,overflow:cs.overflow,
      objectFit:cs.objectFit,pointerEvents:cs.pointerEvents,
      paddingLeft:cs.paddingLeft,paddingRight:cs.paddingRight,
      paddingTop:cs.paddingTop,paddingBottom:cs.paddingBottom};};
  const q=(sel)=>root.querySelector(sel);

  const main=q('[data-character-editor-preview]');
  const fig=q('[data-character-editor-figure]');
  const inner=fig?fig.querySelector('.ce-figure-inner'):null;
  const zoom=q('[data-character-editor-figure-zoom]');
  const figbox=q('[data-character-editor-figure-img]');
  const img=figbox?figbox.querySelector('img'):null;
  const mask=q('[data-character-editor-preview-mask]');
  const blur=q('[data-character-editor-preview-mask-blur]');
  const fade=q('[data-character-editor-preview-mask-fade]');
  const tools=q('[data-character-editor-preview-tools]');
  const sep=q('[data-character-editor-preview-sep]');
  const btns=[...root.querySelectorAll('[data-character-editor-framing]')];

  out['预览区']={
    中列盒:main?rel(main):null,中列样式:sty(main),
    图容器盒:fig?rel(fig):null,图容器布局盒:fig?lay(fig):null,图容器样式:sty(fig),
    内层盒:inner?rel(inner):null,内层布局盒:inner?lay(inner):null,
    变换层盒:zoom?rel(zoom):null,变换层布局盒:zoom?lay(zoom):null,变换层样式:sty(zoom),
    图盒盒:figbox?rel(figbox):null,图盒布局盒:figbox?lay(figbox):null,图盒样式:sty(figbox),
    图元素盒:img?rel(img):null,图元素布局盒:img?lay(img):null,图元素样式:sty(img),
    图源:img?img.getAttribute('src'):null,
    遮罩盒:mask?rel(mask):null,遮罩布局盒:mask?lay(mask):null,遮罩样式:sty(mask),
    blur层盒:blur?rel(blur):null,blur层布局盒:blur?lay(blur):null,blur层样式:sty(blur),
    渐变层盒:fade?rel(fade):null,渐变层布局盒:fade?lay(fade):null,渐变层样式:sty(fade),
    工具行盒:tools?rel(tools):null,工具行布局盒:tools?lay(tools):null,工具行样式:sty(tools),
    分隔线盒:sep?rel(sep):null,分隔线布局盒:sep?lay(sep):null,分隔线样式:sty(sep),
    按钮数:btns.length,
    按钮:btns.map(b=>({aria:b.getAttribute('aria-label')||'',
      className:b.className,box:rel(b),布局盒:lay(b),style:sty(b),
      图标盒:(()=>{const s=b.querySelector('svg');return s?rel(s):null;})()})),
    // ★ 底部生成行（★ 本批**不该**动它 ⟹ ⟹ 读一下确认没被牵连）
    };
  // ★★ 左下三工具（★ 它们**共用** `.ce-tool` 类 ⟹ ⟹ ★ 本批动了那个类
  //    ⟹ ⟹ 必须证明**没连带改坏**它们 ⟹ ⟹ 与 batch 840 的 clone 基线逐项比）
  out['底部生成数']=root.querySelectorAll('[data-character-editor-generate]').length;
  out['左下工具']=[...root.querySelectorAll('.ce-col-left .ce-tool')].map(e=>({
    aria:e.getAttribute('aria-label')||'',box:rel(e),
    图标盒:(()=>{const s=e.querySelector('svg');return s?rel(s):null;})()}));
  // ★ 预览区里**不得**有「未实测」之类的说明（★ 本批全部实测并实现）
  out['预览区文字']=txt(main);
  out['空态数']=root.querySelectorAll('[data-character-editor-empty]').length;
  return out;}"""


def open_editor(pg):
    pg.goto(BASE + "/?batch850=1", wait_until="domcontentloaded")
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
    """★ 点一个元素 ⟹ ⟹ **先 scrollIntoView，再把模态的滚动复位**（模态 overflow:hidden ⟹ ⟹ 会滚 2px）。"""
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
    pg.wait_for_timeout(700)
    b["★滚进可视区"] = scrolled
    return b


def wait_stable(pg, tries=60):
    last = None
    stable = 0
    for _ in range(tries):
        b = pg.evaluate("""()=>{const c=document.querySelector('.ce-preview');
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
            result["★编辑角色CTA盒"] = click_box(pg, '[data-character-studio-cta="edit"]')
            pg.wait_for_timeout(800)
            result["★布局稳定后_预览盒"] = wait_stable(pg)

            # ★ 态一：**默认**（★ 源站默认就是「半身」⟹ ⟹ clone 也不点任何取景按钮）
            result["★默认态"] = pg.evaluate(READ)

            # ★ 态二：点「全身」
            result["★点到_全身"] = click_box(pg, '[data-character-editor-framing="full"]')
            pg.wait_for_timeout(900)
            result["★全身态"] = pg.evaluate(READ)

            # ★ 态三：点回「半身」⟹ ⟹ 验证「切回来真的变回去」
            result["★点到_半身"] = click_box(pg, '[data-character-editor-framing="half"]')
            pg.wait_for_timeout(900)
            result["★半身态_回切"] = pg.evaluate(READ)
            browser.close()
    except Exception:
        result["★异常"] = traceback.format_exc()
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", OUT)
    for key in ("★默认态", "★全身态", "★半身态_回切"):
        r = result.get(key)
        if isinstance(r, dict) and r.get("预览区"):
            p = r["预览区"]
            print("  %-12s 变换层 transform=%s ｜ 遮罩 opacity=%s ｜ blur=%s"
                  % (key,
                     (p.get("变换层样式") or {}).get("transform"),
                     (p.get("遮罩样式") or {}).get("opacity"),
                     (p.get("blur层样式") or {}).get("backdropFilter")))
        else:
            print("  %-12s （无读数）" % key)
    if result.get("★异常"):
        print("异常：", result["★异常"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
