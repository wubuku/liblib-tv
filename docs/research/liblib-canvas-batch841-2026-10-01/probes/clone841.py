#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 841 clone 侧探针：读**右栏各页签**的实测控件，并与源站 raw 对拍。

★ 源站基准（2026-10-22 只读探针，raw 入库在
  `docs/research/liblib-canvas-batch841-2026-10-01/raw/source-841-tabs.json`）：
    页签行 288×40 @rel(912,70)，★ **当前选中那枚**是 56 宽（图标＋文字），
    其余五枚 24 宽（只有图标）
    鼻子页   6 条滑杆：山根／鼻梁／鼻尖／鼻子长短／鼻子大小／鼻翼
    嘴唇页  10 条滑杆：嘴巴上下／丰下唇／嘴巴宽度／丰唇／嘴角调整／嘴巴倾斜／
                    嘴巴大小／丰上唇／祛唇纹(带 i)／唇妆增强
    脸部页  15 条滑杆：额头／V 脸／脸部轮廓流畅(带 i)／小脸／脸部宽度／下巴高度／
                    下颌(左/右)／颧骨(左/右)／太阳穴(左/右)／中庭／下庭／人中
    几何规律：标签 rel y = 130 + 74.8·i（高 22，左端 rel 936）
              轨道 = 标签 +36（240×12）｜ 数值 = 标签 +3（7×16，右端 1176）
              「i」= 标签右端 +6、标签顶 +4（14×14）

★ 本探针只读 clone（4317）＋ 做**本地**交互（切页签、拖滑杆、按 Esc）。
★ 不碰任何会产生真实副作用的东西（clone 侧一切都是本地 mock）。

★ 输出：`/tmp/b841-clone-tabs.json`
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path("/tmp/b841-clone-tabs.json")

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
  const svgBox=(el)=>{if(!el)return null;const s=el.querySelector('svg');
    return s?rel(s):null;};
  // ★ 页签行：每枚的**盒 ＋ 图标 ＋ 文字**（文字只在当前选中那枚上可见）
  out['页签']=[...root.querySelectorAll('[data-character-editor-tab]')].map(e=>({
    id:e.getAttribute('data-character-editor-tab'),
    aria:e.getAttribute('aria-label'),
    selected:e.getAttribute('aria-selected')==='true',
    ...rel(e),
    图标盒:svgBox(e),
    文案盒:(()=>{const i=e.querySelector('.ce-tab-text');
      return i?{...rel(i),text:txt(i)}:null;})()}));
  // ★ 滑杆三件套：标签（文字 ＋ 可选的 i）／轨道／数值
  out['滑杆']=[...root.querySelectorAll('[data-character-editor-slider]')].map(e=>{
    const id=e.getAttribute('data-character-editor-slider');
    const lab=root.querySelector('[data-character-editor-slider-label="'+id+'"]');
    const val=root.querySelector('[data-character-editor-slider-value="'+id+'"]');
    const info=lab?lab.querySelector('.ce-info'):null;
    return {id,value:e.value,
      ...rel(e),
      标签:lab?{...rel(lab),text:txt(lab.querySelector('.ce-slider-label-text')),
        文案盒:rel(lab.querySelector('.ce-slider-label-text')),
        i盒:info?rel(info):null}:null,
      数值:val?{...rel(val),text:txt(val)}:null};});
  out['空态']=(()=>{const e=q('[data-character-editor-empty]');
    return e?txt(e):null;})();
  out['开关']=(()=>{const e=q('[data-character-editor-switch]');
    return e?{...rel(e),checked:e.getAttribute('aria-checked'),
      label:e.getAttribute('aria-label')}:null;})();
  out['提示']=(()=>{const e=q('[data-character-editor-notice]');
    return e?txt(e):null;})();
  return out;}"""


def open_editor(pg):
    """走一遍「角色造型室 → 官方角色库 → 第一个角色 → 编辑角色」。"""
    pg.goto(BASE + "/?batch841=1", wait_until="domcontentloaded")
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
            out["A_默认态_皮肤"] = pg.evaluate(READ)

            # ★ 依次切到三枚**已实现**的页签
            for tab_id in ["nose", "lips", "face"]:
                out["★点到_%s" % tab_id] = click_tab(pg, tab_id)
                out["B_%s" % tab_id] = pg.evaluate(READ)

            # ★ 「眉眼」仍应是**空态说明**（不编造控件）
            out["★点到_brow-eye"] = click_tab(pg, "brow-eye")
            out["C_brow-eye"] = pg.evaluate(READ)

            # ★★ **batch 843 起**：点左列第二段（脸部 & 身体特征）⟹
            #   **页签行应当消失**（源站实测：页签行只在「脸部精修」段存在）⟹ ⟹
            #   那是**当下仍未实现**的那一块 ⟹ ⟹ 显示**如实说明**而不编造控件
            #   ★ 探针必须**真的点一下** ⟹ ⟹ 否则「这个入口没有 X」这类断言根本不成立
            seg2 = pg.evaluate("""()=>{
              const e=document.querySelector('[data-character-editor-segment="traits"]');
              if(!e)return null; const r=e.getBoundingClientRect();
              return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),
                      h:Math.round(r.height)};}""")
            out["★点到_第二段"] = seg2
            if seg2:
                pg.mouse.click(seg2["x"] + seg2["w"] / 2, seg2["y"] + seg2["h"] / 2)
                pg.wait_for_timeout(450)
            out["C2_第二段"] = pg.evaluate(READ)
            # ★ 切回「脸部精修」段 ⟹ 页签行应当回来
            segback = pg.evaluate("""()=>{
              const e=document.querySelector('[data-character-editor-segment="face"]');
              if(!e)return null; const r=e.getBoundingClientRect();
              return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),
                      h:Math.round(r.height)};}""")
            if segback:
                pg.mouse.click(segback["x"] + segback["w"] / 2,
                               segback["y"] + segback["h"] / 2)
                pg.wait_for_timeout(450)
            out["C3_切回脸部精修"] = pg.evaluate(READ)

            # ★ 在「鼻子」页拖第一条滑杆 ⟹ 判据是「渲染数字 == 控件 value」
            click_tab(pg, "nose")
            sl = pg.evaluate("""()=>{
              const e=document.querySelector('[data-character-editor-slider]');
              if(!e)return null; const r=e.getBoundingClientRect();
              return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),
                      h:Math.round(r.height)};}""")
            out["★滑杆盒"] = sl
            if sl:
                pg.mouse.click(sl["x"] + sl["w"] * 0.6, sl["y"] + sl["h"] / 2)
                pg.wait_for_timeout(400)
            out["D_拖滑杆后"] = pg.evaluate(READ)

            # ★ Esc ⟹ 关掉编辑器、面板还在
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(600)
            out["E_Esc后"] = {
                "★编辑器还在吗": pg.evaluate(
                    "() => Boolean(document.querySelector('[data-character-editor]'))"),
                "★面板还在吗": pg.evaluate(
                    "() => Boolean(document.querySelector('[data-character-studio]'))"),
            }
            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        if out.get("异常"):
            print("异常：", out["异常"])
        for stage in ("A_默认态_皮肤", "B_nose", "B_lips", "B_face", "C_brow-eye",
                      "C2_第二段", "C3_切回脸部精修", "D_拖滑杆后"):
            r = out.get(stage) or {}
            if not r:
                continue
            tabs = [(t["id"], t["w"], t["selected"]) for t in r.get("页签", [])]
            print("── %s" % stage)
            print("   页签(宽/选中): %s" % tabs)
            print("   滑杆 %d 条：%s" % (
                len(r.get("滑杆", [])),
                [(s["标签"]["text"] if s.get("标签") else None) for s in r.get("滑杆", [])]))
            if r.get("空态"):
                print("   空态：%s" % r["空态"][:60])


if __name__ == "__main__":
    sys.exit(main())
