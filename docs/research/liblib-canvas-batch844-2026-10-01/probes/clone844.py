#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 844 clone 侧探针：读左列第二段「脸部 & 身体特征」（纹身 & 疤痕 ＋ 6 张贴纸卡）。

★ 源站基准（**只读**实测，raw 入库在
  `docs/research/liblib-canvas-batch844-2026-10-01/raw/source-844-traits.json`）：
  - H3「纹身 & 疤痕」240×22（14px／400／纯白）
  - 6 张卡 76×54，3 列 × 2 行（列距 82、行距 62）
  - 缩略图 76×32 的**圆形**（rounded-full，白 5% 底 ＋ 白 8% 边）；图 74×30
  - 名字 11px／16px（左右各 4px 内边距）
  - 第 6 张「自定义」**没有图** ⟹ 一枚 16×16 图标 ⟹ 且**没有** `aria-pressed`
  - 前 5 张 `aria-pressed="false"`（初始一个都没选中）

★ 输出：`/tmp/b844-clone-traits.json`
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path("/tmp/b844-clone-traits.json")

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
      display:cs.display,alignItems:cs.alignItems,justifyContent:cs.justifyContent};};

  // ★ 页签行（★ 源站：**这一段没有页签行** ⟹ ⟹ 这里读它有没有）
  out['页签数']=root.querySelectorAll('[data-character-editor-tab]').length;
  // ★ 空态说明（★ 这一段已实现 ⟹ ⟹ **不该**有）
  out['空态']=(()=>{const e=root.querySelector('[data-character-editor-empty]');
    return e?txt(e):null;})();

  // ★ H3
  out['H3']=(()=>{const e=root.querySelector('[data-character-editor-h3="纹身 & 疤痕"]');
    if(!e)return null;
    return {text:txt(e),box:rel(e),style:sty(e)};})();

  // ★ 6 张贴纸卡
  out['卡片']=[...root.querySelectorAll('[data-character-editor-trait]')].map(b=>{
    const thumb=b.querySelector('.ce-trait-thumb');
    const img=b.querySelector('img');
    const name=b.querySelector('.ce-trait-name');
    const icon=[...b.querySelectorAll('svg')].map(s=>rel(s))[0]||null;
    return {key:b.getAttribute('data-character-editor-trait'),
      pressed:b.getAttribute('aria-pressed'),
      box:rel(b),
      缩略盒:thumb?rel(thumb):null,
      缩略样式:thumb?sty(thumb):null,
      图:img?{src:(img.currentSrc||img.src||'').slice(0,140),box:rel(img)}:null,
      媒体里有图:!!img,
      图标盒:icon,
      名字:name?{text:txt(name),box:rel(name),style:sty(name)}:null};});

  // ★ 面板（内容起点）
  const panel=root.querySelector('.ce-panel--seg');
  out['面板']=panel?{box:rel(panel)}:null;
  // ★ 右栏盒（★ 用来算「内容起点相对列顶多少」⟹ ⟹ 与源站同口径）
  const col=root.querySelector('.ce-col-right');
  out['右栏盒']=col?rel(col):null;
  return out;}"""


def open_editor(pg):
    pg.goto(BASE + "/?batch844=1", wait_until="domcontentloaded")
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

            # ★ 点左列第二段
            out["★点到_第二段"] = click_box(pg,
                                           '[data-character-editor-segment="traits"]')
            out["A_第二段"] = pg.evaluate(READ)

            # ★ 点一张卡（「痣」）⟹ 选中态应当转移
            out["★点到_痣"] = click_box(pg, '[data-character-editor-trait="痣"]')
            out["B_点卡后"] = pg.evaluate(READ)

            # ★ 点回第一段 ⟹ 页签行应当回来
            out["★点到_脸部精修"] = click_box(pg,
                                              '[data-character-editor-segment="face"]')
            out["C_切回脸部精修"] = pg.evaluate(READ)

            # ★ 再回第二段 ⟹ 选中态是否保持（★ clone 的本地行为 ⟹ 不声称与源站一致）
            out["★再点_第二段"] = click_box(pg,
                                            '[data-character-editor-segment="traits"]')
            out["D_再回第二段"] = pg.evaluate(READ)

            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        if out.get("异常"):
            print("异常：", out["异常"])
        for stage in ("A_第二段", "B_点卡后", "C_切回脸部精修", "D_再回第二段"):
            r = out.get(stage) or {}
            if not r:
                continue
            print("── %s" % stage)
            print("   页签数=%s 空态=%r H3=%s" % (
                r.get("页签数"), (r.get("空态") or "")[:18],
                json.dumps((r.get("H3") or {}).get("box"), ensure_ascii=False)))
            for c in (r.get("卡片") or []):
                print("    - %-6s %s pressed=%s 图=%s" % (
                    (c.get("名字") or {}).get("text"),
                    json.dumps(c.get("box"), ensure_ascii=False),
                    c.get("pressed"), c.get("媒体里有图")))


if __name__ == "__main__":
    sys.exit(main())
