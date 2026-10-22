#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 842 clone 侧探针：读「眉眼」页的**分块布局**（H3 ＋ 滑杆组 ＋ H4 ＋ 预设卡）。

★ 源站基准（**只读**实测，raw 入库）：
  - `docs/research/liblib-canvas-batch841-2026-10-01/raw/source-841-tabs.json`
    （几何：30 条滑杆的四件套、2 个 H3、「眼神光」、11 张卡的盒与文案）
  - `docs/research/liblib-canvas-batch842-2026-10-01/raw/source-842-brow.json`
    （计算样式：H3/H4 的字号与颜色、卡片的圆角与底色、「i」标记是描边圆）

★ 源站结构（源站实测）：
    H3「眼睛」 → 19 条滑杆 → H4「眼神光」（带 i）→ 11 张 76×96 眼型卡
    → H3「眉毛」 → 11 条滑杆
  ⟹ 合计 **30 条**滑杆（★ 不是 32 ⟹ 841 的 README 写错了，见 842 的 README）

★ 本探针只读 clone（4317）＋ 做**本地**交互（切页签、拖滑杆、点卡）。

★ 输出：`/tmp/b842-clone-brow.json`
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path("/tmp/b842-clone-brow.json")

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
  const q=(sel)=>root.querySelector(sel);

  // ★ 标题（H3 分段 ＋ H4 预设分组）
  out['标题']=[...root.querySelectorAll('.ce-h3,.ce-h4')].map(e=>({
    tag:e.tagName,text:txt(e),box:rel(e),
    i盒:(()=>{const i=e.querySelector('.ce-info');return i?rel(i):null;})()}));

  // ★ 滑杆四件套（标签／i／轨道／数值）
  out['滑杆']=[...root.querySelectorAll('[data-character-editor-slider]')].map(e=>{
    const id=e.getAttribute('data-character-editor-slider');
    const lab=root.querySelector('[data-character-editor-slider-label="'+id+'"]');
    const val=root.querySelector('[data-character-editor-slider-value="'+id+'"]');
    const info=lab?lab.querySelector('.ce-info'):null;
    return {id,value:e.value,box:rel(e),
      标签:lab?{...rel(lab),text:txt(lab.querySelector('.ce-slider-label-text')),
        文案盒:rel(lab.querySelector('.ce-slider-label-text')),
        i盒:info?rel(info):null}:null,
      数值:val?{...rel(val),text:txt(val)}:null};});

  // ★ 预设卡（76×96）：按钮盒 ＋ 媒体区 ＋ 名字 ＋ 选中态
  out['卡片']=[...root.querySelectorAll('[data-character-editor-card]')].map(b=>({
    aria:b.getAttribute('aria-label'),pressed:b.getAttribute('aria-pressed'),
    box:rel(b),
    媒体盒:rel(b.querySelector('.ce-card-media')),
    名字盒:rel(b.querySelector('[data-character-editor-card-name]')),
    名字:txt(b.querySelector('[data-character-editor-card-name]')),
    占位盒:rel(b.querySelector('[data-character-editor-card-thumb]')),
    无图标盒:rel(b.querySelector('.ce-card-none')),
  }));

  out['空态']=(()=>{const e=q('[data-character-editor-empty]');
    return e?txt(e):null;})();

  // ★★ **计算样式**（盒对上了 ⟹ 样子也得对上：字号／颜色／圆角／描边）
  const sty=(e)=>{if(!e)return null;const cs=getComputedStyle(e);
    return {fontSize:cs.fontSize,fontWeight:cs.fontWeight,lineHeight:cs.lineHeight,
      color:cs.color,backgroundColor:cs.backgroundColor,borderRadius:cs.borderRadius,
      borderTopWidth:cs.borderTopWidth,borderTopColor:cs.borderTopColor,
      paddingLeft:cs.paddingLeft,gap:cs.gap};};
  const h3=root.querySelector('.ce-h3');
  const h4=root.querySelector('.ce-h4');
  const info=root.querySelector('.ce-info');
  const media=root.querySelector('.ce-card-media');
  const name=root.querySelector('.ce-card-name');
  const onName=root.querySelector('.ce-card.is-on .ce-card-name');
  out['样式']={H3:sty(h3),H4:sty(h4),i标记:sty(info),
    卡片媒体区:sty(media),卡片名字:sty(name),选中卡片名字:sty(onName)};
  return out;}"""


def open_editor(pg):
    """走一遍「角色造型室 → 官方角色库 → 第一个角色 → 编辑角色」。"""
    pg.goto(BASE + "/?batch842=1", wait_until="domcontentloaded")
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


def click_tab(pg, tab_id):
    box = pg.evaluate("""(id)=>{
      const e=document.querySelector('[data-character-editor-tab="'+id+'"]');
      if(!e)return null; const r=e.getBoundingClientRect();
      return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),
              h:Math.round(r.height)};}""", tab_id)
    if not box:
        return False
    pg.mouse.click(box["x"] + box["w"] / 2, box["y"] + box["h"] / 2)
    pg.wait_for_timeout(450)
    return True


def main():
    out = {}
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            pg = ctx.new_page()
            open_editor(pg)
            cta = pg.evaluate("""()=>{
              const e=document.querySelector('[data-character-studio-cta="edit"]');
              if(!e)return null; const r=e.getBoundingClientRect();
              return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),
                      h:Math.round(r.height)};}""")
            out["★编辑角色CTA盒"] = cta
            if cta:
                pg.mouse.click(cta["x"] + cta["w"] / 2, cta["y"] + cta["h"] / 2)
                pg.wait_for_timeout(900)

            # ★ 「眉眼」页（batch 842 新实现的那一页）
            out["★点到_brow-eye"] = click_tab(pg, "brow-eye")
            out["A_眉眼"] = pg.evaluate(READ)

            # ★ 拖第一条滑杆 ⟹ 判据是「渲染数字 == 控件 value」
            sl = pg.evaluate("""()=>{
              const e=document.querySelector('[data-character-editor-slider]');
              if(!e)return null; const r=e.getBoundingClientRect();
              return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),
                      h:Math.round(r.height)};}""")
            out["★滑杆盒"] = sl
            if sl:
                pg.mouse.click(sl["x"] + sl["w"] * 0.6, sl["y"] + sl["h"] / 2)
                pg.wait_for_timeout(400)
            out["B_拖滑杆后"] = pg.evaluate(READ)

            # ★ 点第三张眼型卡 ⟹ 选中态应当转移
            #   ★★ 卡片在**滚动区下面**（源站 abs y 1782 ⟹ 视口 1080 之外）⟹ ⟹
            #   **必须先把右栏滚下去**，否则 `mouse.click` 点的是空气 ⟹ ⟹
            #   「点了没反应」会被误读成「交互没生效」（★ 读数对不上时先怀疑自己的动作）
            out["★滚动前scrollTop"] = pg.evaluate(
                "() => { const p=document.querySelector('.ce-panel');"
                " return p ? p.scrollTop : null; }")
            pg.evaluate("() => { const p=document.querySelector('.ce-panel');"
                        " if(p) p.scrollTop = 1200; }")
            pg.wait_for_timeout(500)
            out["★滚动后scrollTop"] = pg.evaluate(
                "() => { const p=document.querySelector('.ce-panel');"
                " return p ? p.scrollTop : null; }")
            card = pg.evaluate("""()=>{
              const e=document.querySelector('[data-character-editor-card="清澈"]');
              if(!e)return null; const r=e.getBoundingClientRect();
              return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),
                      h:Math.round(r.height)};}""")
            out["★卡片盒"] = card
            if card:
                pg.mouse.click(card["x"] + card["w"] / 2, card["y"] + 30)
                pg.wait_for_timeout(400)
            out["C_点卡后"] = pg.evaluate(READ)

            # ★ 「妆造」页仍是**空态说明**（本批不实现）
            out["★点到_makeup"] = click_tab(pg, "makeup")
            out["D_妆造"] = pg.evaluate(READ)

            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        if out.get("异常"):
            print("异常：", out["异常"])
        for stage in ("A_眉眼", "B_拖滑杆后", "C_点卡后", "D_妆造"):
            r = out.get(stage) or {}
            if not r:
                continue
            print("── %s" % stage)
            print("   标题: %s" % [(t["tag"], t["text"], t["box"]["y"]) for t in r.get("标题", [])])
            print("   滑杆 %d 条: %s" % (
                len(r.get("滑杆", [])),
                [(s["标签"]["text"] if s.get("标签") else None) for s in r.get("滑杆", [])][:6]))
            print("   卡片 %d 张: %s" % (
                len(r.get("卡片", [])),
                [(c["aria"], c["pressed"], c["box"]["x"], c["box"]["y"]) for c in r.get("卡片", [])][:4]))
            if r.get("空态"):
                print("   空态：%s" % r["空态"][:70])


if __name__ == "__main__":
    sys.exit(main())
