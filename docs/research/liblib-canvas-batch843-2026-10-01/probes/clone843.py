#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 843 clone 侧探针：读「妆造」页（11 枚分类 chip ＋ 随 chip 切换的卡片网格）。

★ 源站基准（**只读**实测，raw 入库在
  `docs/research/liblib-canvas-batch843-2026-10-01/raw/source-843-makeup.json`）：
  - H4「妆容素材」240×22（14px/500/白，带一枚「i」）
  - 分类 chip 11 枚 50×26：4 列 × 3 行（步进 56／32），选中那枚**白底黑字**
  - 卡片 76×96：3 列（步进 82／104），每个分类的**第一张恒为「无」**（无缩略图）
  - 每个分类的卡片数：眉毛 14／美瞳 14／卧蚕 9／眼影 14／睫毛 15／修容 12／
    腮红 13／唇彩 18／妆饰 7／眼线 12／高光 10（**含**各自的「无」）

★ 本探针还验一条**结构事实**（源站实测，batch 841 raw）：
  **页签行只在「脸部精修」段存在** ⟹ ⟹ 点左列别的段 ⟹ 右栏**不显示页签行**。

★ 输出：`/tmp/b843-clone-makeup.json`
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path("/tmp/b843-clone-makeup.json")

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

  // ★ 页签行（★ 源站：**只在「脸部精修」段存在** ⟹ ⟹ 这里读它有没有）
  out['页签数']=root.querySelectorAll('[data-character-editor-tab]').length;

  // ★ H4
  out['H4']=(()=>{const e=q('.ce-h4');
    if(!e)return null;
    return {text:txt(e),box:rel(e),
      i盒:(()=>{const i=e.querySelector('.ce-info');return i?rel(i):null;})()};})();

  // ★ 分类 chip
  out['chip']=[...root.querySelectorAll('[data-character-editor-chip]')].map(e=>({
    id:e.getAttribute('data-character-editor-chip'),text:txt(e),
    selected:e.getAttribute('aria-selected')==='true',box:rel(e)}));

  // ★ 卡片
  out['卡片']=[...root.querySelectorAll('[data-character-editor-makeup-card]')].map(b=>({
    key:b.getAttribute('data-character-editor-makeup-card'),
    name:b.getAttribute('data-character-editor-makeup-name'),
    aria:b.getAttribute('aria-label'),pressed:b.getAttribute('aria-pressed'),
    box:rel(b),媒体盒:rel(b.querySelector('.ce-card-media')),
    名字盒:rel(b.querySelector('[data-character-editor-card-name]')),
    名字:txt(b.querySelector('[data-character-editor-card-name]')),
    占位盒:rel(b.querySelector('[data-character-editor-card-thumb]')),
    无图标盒:rel(b.querySelector('.ce-card-none'))}));

  out['空态']=(()=>{const e=q('[data-character-editor-empty]');
    return e?txt(e):null;})();

  // ★★ **计算样式**（盒对上了 ⟹ 样子也得对上）
  const sty=(e)=>{if(!e)return null;const cs=getComputedStyle(e);
    return {fontSize:cs.fontSize,fontWeight:cs.fontWeight,lineHeight:cs.lineHeight,
      color:cs.color,backgroundColor:cs.backgroundColor,borderRadius:cs.borderRadius,
      borderTopWidth:cs.borderTopWidth,borderTopColor:cs.borderTopColor,
      paddingLeft:cs.paddingLeft,paddingTop:cs.paddingTop};};
  const chips=[...root.querySelectorAll('[data-character-editor-chip]')];
  const media=root.querySelector('.ce-card-media');
  // ★ **未选中**的那枚要按 aria-selected 找（★ 不能用 chips[1] —— 那个位置**可能**正好是选中的）
  const off=chips.find(c=>c.getAttribute('aria-selected')!=='true');
  out['样式']={未选中chip:sty(off),选中chip:sty(root.querySelector('.ce-chip.is-on')),
    卡片媒体区:sty(media),H4:sty(root.querySelector('.ce-h4'))};
  return out;}"""


def open_editor(pg):
    pg.goto(BASE + "/?batch843=1", wait_until="domcontentloaded")
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
            cta = click_box(pg, '[data-character-studio-cta="edit"]')
            out["★编辑角色CTA盒"] = cta
            pg.wait_for_timeout(500)

            # ★ 「妆造」页
            out["★点到_妆造"] = click_box(pg, '[data-character-editor-tab="makeup"]')
            out["A_妆造_默认分类"] = pg.evaluate(READ)

            # ★ 依次点**每一个**分类 chip ⟹ 每个分类的卡片清单都要对上（138 张）
            for cat_id in ["brow", "contact", "wochan", "yanying", "jielan",
                           "xiurong", "saihong", "runcai", "zhuangshi",
                           "yanxian", "gaoguang"]:
                out["★点到_%s" % cat_id] = click_box(
                    pg, '[data-character-editor-chip="%s"]' % cat_id)
                out["分类_%s" % cat_id] = pg.evaluate(READ)

            # ★ 点第二张卡（美瞳的「琥珀」）⟹ 选中态应当转移
            #   ★★ **必须先切回「美瞳」**：跑完 11 个分类后当前是「高光」，
            #   而「琥珀」那枚卡**不在当前分类里** ⟹ ⟹ 点它等于**点空气**
            #   ⟹ ⟹ 「点了没反应」会被误读成「交互没生效」
            #   ★ 选卡用**带序号**的属性（★ 源站「眼影」有两个同名「自然」⟹
            #   只用「分类/名字」当属性值 ⟹ DOM 里两个同值 ⟹ 选择器会挑错卡）
            out["★切回_美瞳"] = click_box(pg, '[data-character-editor-chip="contact"]')
            out["★点到_琥珀"] = click_box(
                pg, '[data-character-editor-makeup-name="琥珀"]')
            out["C_点卡后"] = pg.evaluate(READ)

            # ★ 点左列**第五段**（音色音调）⟹ **页签行应当消失** ＋ 出现空态说明
            #   （★ 846 起第四段已实现 ⟹ ⟹ 「仍未实现的那一段」又挪了一位）
            out["★点到_第五段"] = click_box(pg,
                                           '[data-character-editor-segment="voice"]')
            out["D_第五段"] = pg.evaluate(READ)

            # ★ 点回「脸部精修」⟹ 页签行应当回来
            out["★点到_脸部精修"] = click_box(pg,
                                              '[data-character-editor-segment="face"]')
            out["E_切回脸部精修"] = pg.evaluate(READ)

            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        if out.get("异常"):
            print("异常：", out["异常"])
        for stage in ("A_妆造_默认分类", "分类_contact", "分类_runcai",
                      "C_点卡后", "D_第五段", "E_切回脸部精修"):
            r = out.get(stage) or {}
            if not r:
                continue
            print("── %s" % stage)
            print("   页签数=%s  chip=%s  卡片=%d 张  空态=%s" % (
                r.get("页签数"),
                [(c["text"], c["selected"]) for c in (r.get("chip") or [])][:4],
                len(r.get("卡片") or []),
                (r.get("空态") or "")[:40]))


if __name__ == "__main__":
    sys.exit(main())
