#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 845 clone 侧探针：读左列第三段「身材塑形」（**18 条**滑杆）。

★ 源站基准（**只读**实测，raw 入库在
  `docs/research/liblib-canvas-batch845-2026-10-01/raw/`）：
  - `source-845-body.json`   ⟹ 结构：18 条滑杆的名字／量程／「i」标记／盒
  - `source-845-pixels.json` ⟹ **像素**：2px 轨道、纯白填充段、14×14 纯白圆钮、
                              圆心 2×2 深点（#464646）、圆钮中心 = 轨道左端 + 7 + ratio·226
  - `source-845-visual.json` ＋ `source-845-sliders.png` ⟹ 截屏原件

★ 输出：`/tmp/b845-clone-body.json`
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path("/tmp/b845-clone-body.json")

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
      paddingLeft:cs.paddingLeft,paddingTop:cs.paddingTop,gap:cs.gap,
      display:cs.display,alignItems:cs.alignItems,justifyContent:cs.justifyContent,
      fontFamily:cs.fontFamily};};

  // ★ 页签行（★ 源站：这一段**没有**页签行 ⟹ ⟹ 这里读它有没有）
  out['页签数']=root.querySelectorAll('[data-character-editor-tab]').length;
  // ★ 空态说明（★ 这一段已实现 ⟹ ⟹ **不该**有）
  out['空态']=(()=>{const e=root.querySelector('[data-character-editor-empty]');
    return e?txt(e):null;})();

  // ★ 18 条滑杆
  out['滑杆']=[...root.querySelectorAll('[data-character-editor-slider]')].map(inp=>{
    const id=inp.getAttribute('data-character-editor-slider');
    const lab=root.querySelector('[data-character-editor-slider-label="'+id+'"]');
    const nameEl=lab?lab.querySelector('.ce-slider-label-text'):null;
    const info=lab?lab.querySelector('.ce-info'):null;
    const val=root.querySelector('[data-character-editor-slider-value="'+id+'"]');
    const dot=root.querySelector('[data-character-editor-slider-dot="'+id+'"]');
    return {id:id,
      名字文字:nameEl?txt(nameEl):null,
      名字盒:nameEl?rel(nameEl):null,
      名字样式:nameEl?sty(nameEl):null,
      标签盒:lab?rel(lab):null,
      标签样式:lab?sty(lab):null,
      有i:!!info,
      i盒:info?rel(info):null,
      i样式:info?sty(info):null,
      min:inp.getAttribute('min'), max:inp.getAttribute('max'),
      step:inp.getAttribute('step'), value:inp.value,
      输入盒:rel(inp),
      输入样式:sty(inp),
      数值文字:val?txt(val):null,
      数值盒:val?rel(val):null,
      数值样式:val?sty(val):null,
      圆心点盒:dot?rel(dot):null,
      圆心点样式:dot?sty(dot):null};});

  // ★ 面板（★ 滚动区长度）
  const panel=root.querySelector('.ce-panel--seg');
  out['面板']=panel?{box:rel(panel),
    滚动高:panel.scrollHeight, 客户端高:panel.clientHeight}:null;
  const col=root.querySelector('.ce-col-right');
  out['右栏盒']=col?rel(col):null;
  return out;}"""


def open_editor(pg):
    pg.goto(BASE + "/?batch845=1", wait_until="domcontentloaded")
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
    b = pg.evaluate("""(sel)=>{
      const e=document.querySelector(sel);
      if(!e)return null; const r=e.getBoundingClientRect();
      return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),
              h:Math.round(r.height)};}""", selector)
    if not b:
        return None
    pg.mouse.click(b["x"] + b["w"] * dx, b["y"] + b["h"] * dy)
    pg.wait_for_timeout(400)
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

            # ★ 点左列第三段（身材塑形）
            out["★点到_第三段"] = click_box(pg,
                                           '[data-character-editor-segment="body"]')
            out["A_第三段"] = pg.evaluate(READ)

            # ★★ **真实鼠标**点「丰胸」轨道的**最左端** ⟹ ⟹ 量程是 −100..100
            #   ⟹ ⟹ 值应变负数、圆心点应跑到**最左**（ratio 0 ⟹ 圆钮中心 = 轨道左端 + 7）
            trk = pg.evaluate("""()=>{
              const e=document.querySelector('[data-character-editor-slider="body-breast"]');
              if(!e)return null; const r=e.getBoundingClientRect();
              return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),
                      h:Math.round(r.height)};}""")
            out["★丰胸轨道盒"] = trk
            if trk:
                pg.mouse.click(trk["x"] + 1, trk["y"] + trk["h"] / 2)
                pg.wait_for_timeout(500)
            out["B_点最左后"] = pg.evaluate(READ)

            # ★ 再点最右端 ⟹ 应该是 +100
            if trk:
                pg.mouse.click(trk["x"] + trk["w"] - 1, trk["y"] + trk["h"] / 2)
                pg.wait_for_timeout(500)
            out["C_点最右后"] = pg.evaluate(READ)

            # ★ 点回第一段 ⟹ 页签行应当回来
            out["★点到_脸部精修"] = click_box(pg,
                                              '[data-character-editor-segment="face"]')
            out["D_切回脸部精修"] = pg.evaluate(READ)

            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        if out.get("异常"):
            print("异常：", out["异常"])
        for stage in ("A_第三段", "B_点最左后", "C_点最右后", "D_切回脸部精修"):
            r = out.get(stage) or {}
            if not r:
                continue
            print("── %s  页签数=%s 空态=%r 滑杆数=%d 滚动高=%s"
                  % (stage, r.get("页签数"), (r.get("空态") or "")[:16],
                     len(r.get("滑杆") or []),
                     (r.get("面板") or {}).get("滚动高")))
            for s in (r.get("滑杆") or [])[:3]:
                print("    - %-10s 值=%-5s min=%-5s max=%-4s 点=%s"
                      % (s.get("名字文字"), s.get("value"), s.get("min"),
                         s.get("max"), json.dumps(s.get("圆心点盒"), ensure_ascii=False)))


if __name__ == "__main__":
    sys.exit(main())
