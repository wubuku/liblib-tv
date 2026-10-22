#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 840 clone 侧探针：读**角色大编辑器**的几何，并与源站实测对拍。

★ 源站实测基准（1920×1080，`raw/source-840-editor.json`）：
    模态            1198×758 @361,161
    内容行          1198×602 @rel(0,70)   ⟹ 左列 288 / 预览 624 / 右栏 288
    底栏            1198×88  @rel(0,672)
    标题输入        216×32  @rel(24,80)    （aria-label=角色名称）
    标签行          240×22  @rel(24,122)   （「· 青年 · 东亚 · 现代」）
    五段            240×44  @rel(12,168/220/272/324/376)
    左下三枚工具    32×32   @rel(17/49/90,624)
    预览角色图      467×550 @rel(367,70)
    半身/全身       32×32   @rel(564/605,624)   ⟹ 间隙 9px（容器实宽 73）
    返回按钮        26×26   @rel(16,24)
    右栏页签        288×40  @rel(912,70)；皮肤 56×39 @rel(936,70)；其余 24×39
    六条滑杆        轨道 240×12；标签 22 高；数值在轨道右端
    祛斑祛痘开关    32×18
    确认生成        196×36 @rel(936,622)；智能调整 36×36 @rel(1140,622)
    底栏            保存 80×40 @rel(483,697)；保存并添加到画布 144×40 @rel(571,697)

★ 本探针只读 clone（4317）＋ 做**本地**交互（拖滑杆、切开关、切页签/分段、输入名字、按 Esc）。
★ 不碰任何会产生真实副作用的东西（clone 侧一切都是本地 mock）。

★ 输出：`/tmp/b840-clone-editor.json`
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path("/tmp/b840-clone-editor.json")

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
  // ★ 相对模态左上角的偏移（源站读数是绝对坐标 ⟹ 对拍要用相对值）
  const rel=(e)=>{if(!e)return null;const b=box(e);
    return {x:b.x-rb.x,y:b.y-rb.y,w:b.w,h:b.h};};
  const q=(sel)=>root.querySelector(sel);
  // ★ 元素里**第一个 svg** 的盒（源站图标全是 18×18，除「返回」那枚 16×16）
  const svgBox=(el)=>{if(!el)return null;const s=el.querySelector('svg');
    return s?rel(s):null;};
  out['内容行盒']=rel(q('.ce-body'));
  out['左列盒']=rel(q('.ce-col-left'));
  out['预览盒']=rel(q('.ce-preview'));
  out['右列盒']=rel(q('.ce-col-right'));
  out['返回按钮']=(()=>{const e=q('.ce-back');
    return e?{...rel(e),aria:e.getAttribute('aria-label'),图标盒:svgBox(e)}:null;})();
  out['标题输入']=(()=>{const e=q('[data-character-editor-name]');
    return e?{...rel(e),value:e.value,aria:e.getAttribute('aria-label')}:null;})();
  const tags=q('[data-character-editor-tags]');
  out['标签行']=tags?{...rel(tags),text:txt(tags)}:null;
  const tagText=q('[data-character-editor-tag-text]');
  out['标签文本']=tagText?{...rel(tagText),text:txt(tagText)}:null;
  out['性别图标']=(()=>{const e=q('.ce-tag-gender');return e?rel(e):null;})();
  out['积分符号']=(()=>{const e=q('[data-character-editor-credit-bolt]');
    return e?rel(e):null;})();
  out['积分数值']=(()=>{const e=q('[data-character-editor-credit-num]');
    return e?{...rel(e),text:txt(e)}:null;})();
  out['生成资产标签']=(()=>{const e=q('[data-character-editor-gen-assets-label]');
    return e?{...rel(e),text:txt(e)}:null;})();
  out['复选框可见件']=(()=>{const e=q('.ce-checkbox');
    return e?rel(e):null;})();
  out['五段']=[...root.querySelectorAll('[data-character-editor-segment]')].map(e=>({
    id:e.getAttribute('data-character-editor-segment'),text:txt(e),
    ...rel(e),bg:getComputedStyle(e).backgroundColor,
    selected:e.classList.contains('is-on'),
    图标盒:(()=>{const i=e.querySelector('.ce-seg-icon');return i?rel(i):null;})(),
    文案盒:(()=>{const i=e.querySelector('.ce-seg-text');return i?{...rel(i),text:txt(i)}:null;})(),
    徽标盒:(()=>{const i=e.querySelector('.ce-badge');
      return i?{...rel(i),text:txt(i)}:null;})()}));
  out['左下工具']=[...root.querySelectorAll('.ce-col-left .ce-tool')].map(e=>({
    aria:e.getAttribute('aria-label'),...rel(e),图标盒:svgBox(e)}));
  out['角色图']=(()=>{const e=q('.ce-figure');return e?rel(e):null;})();
  out['半身全身容器']=(()=>{const e=q('.ce-preview-tools');return e?rel(e):null;})();
  out['半身全身']=[...root.querySelectorAll('.ce-preview-tools .ce-tool')].map(e=>({
    aria:e.getAttribute('aria-label'),...rel(e),图标盒:svgBox(e)}));
  out['页签']=[...root.querySelectorAll('[data-character-editor-tab]')].map(e=>({
    id:e.getAttribute('data-character-editor-tab'),text:txt(e),aria:e.getAttribute('aria-label'),
    ...rel(e),selected:e.getAttribute('aria-selected')==='true',
    图标盒:(()=>{const i=e.querySelector('.ce-tab-icon');return i?rel(i):null;})(),
    文案盒:(()=>{const i=e.querySelector('.ce-tab-text');
      return i?{...rel(i),text:txt(i)}:null;})()}));
  out['滑杆标签']=[...root.querySelectorAll('[data-character-editor-slider-label]')].map(e=>({
    id:e.getAttribute('data-character-editor-slider-label'),text:txt(e),...rel(e),
    文案盒:(()=>{const i=e.querySelector('.ce-slider-label-text');
      return i?{...rel(i),text:txt(i)}:null;})(),
    图标盒:(()=>{const i=e.querySelector('.ce-info');return i?rel(i):null;})()}));
  out['滑杆轨道']=[...root.querySelectorAll('[data-character-editor-slider]')].map(e=>({
    id:e.getAttribute('data-character-editor-slider'),value:e.value,...rel(e)}));
  out['滑杆数值']=[...root.querySelectorAll('[data-character-editor-slider-value]')].map(e=>({
    id:e.getAttribute('data-character-editor-slider-value'),text:txt(e),...rel(e)}));
  const sw=q('[data-character-editor-switch]');
  out['开关']=sw?{...rel(sw),checked:sw.getAttribute('aria-checked'),
    label:sw.getAttribute('aria-label')}:null;
  out['祛斑祛痘行']=(()=>{const e=q('[data-character-editor-switch-row]');
    if(!e)return null;
    const t=e.querySelector('.ce-switch-label-text');
    const i=e.querySelector('.ce-info');
    return {...rel(e),text:txt(e),
      文案盒:t?{...rel(t),text:txt(t)}:null,图标盒:i?rel(i):null};})();
  out['确认生成']=(()=>{const e=q('[data-character-editor-generate]');
    if(!e)return null;
    const t=e.querySelector('.ce-generate-text');
    return {...rel(e),text:txt(e),图标盒:svgBox(e),
      文案盒:t?{...rel(t),text:txt(t)}:null};})();
  out['智能调整']=(()=>{const e=q('[data-character-editor-smart]');
    return e?{...rel(e),aria:e.getAttribute('aria-label'),图标盒:svgBox(e)}:null;})();
  out['底栏盒']=rel(q('.ce-footer'));
  out['保存时生成角色资产']=(()=>{const e=q('[data-character-editor-gen-assets]');
    return e?{...rel(e),text:txt(e)}:null;})();
  const sv=q('[data-character-editor-save]');
  out['保存']=sv?{...rel(sv),text:txt(sv)}:null;
  const sa=q('[data-character-editor-save-add]');
  out['保存并添加到画布']=sa?{...rel(sa),text:txt(sa)}:null;
  const notice=q('[data-character-editor-notice]');
  out['提示']=notice?txt(notice):null;
  out['空态']=(()=>{const e=q('[data-character-editor-empty]');
    return e?txt(e):null;})();
  const ae=document.activeElement;
  out['活动焦点']=ae?{tag:ae.tagName,
    在编辑器内:(root.contains(ae))}:null;
  return out;}"""


def main():
    out = {}
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            pg = ctx.new_page()
            pg.goto(BASE + "/?batch840=1", wait_until="domcontentloaded")
            pg.wait_for_timeout(3000)
            pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
            pg.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
            opened = pg.evaluate("""() => {
              const cands=[...document.querySelectorAll('button,[role="button"]')];
              const b=cands.find(e=>e.getAttribute('aria-label')==='角色造型室')
                || cands.find(e=>(e.getAttribute('data-sidebar-btn')==='character-library'))
                || cands.find(e=>(e.textContent||'').trim()==='人物');
              if(b){b.click();return true;} return false;}""")
            out["★是否点开角色库入口"] = opened
            pg.wait_for_timeout(1500)
            pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
            out["★面板是否打开"] = pg.evaluate(
                "() => Boolean(document.querySelector('[data-character-studio]'))")
            # ★ 切到「官方角色库」 ＋ 选中第一个角色
            pg.evaluate("""() => {
              const t=[...document.querySelectorAll('[data-character-studio-tab]')]
                .find(e=>e.getAttribute('data-character-studio-tab')==='official');
              if(t)t.click();}""")
            pg.wait_for_timeout(800)
            pg.evaluate("""() => {
              const c=document.querySelector('[data-character-strip-card]');
              if(c)c.click();}""")
            pg.wait_for_timeout(700)
            out["A_点编辑前"] = pg.evaluate(READ)

            # ★ 点「编辑角色」（**真实鼠标**）
            bb = pg.evaluate("""() => {
              const e=document.querySelector('[data-character-studio-cta="edit"]');
              if(!e)return null; const r=e.getBoundingClientRect();
              return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),
                      h:Math.round(r.height)};}""")
            out["★编辑角色CTA盒"] = bb
            if bb:
                pg.mouse.click(bb["x"] + bb["w"] / 2, bb["y"] + bb["h"] / 2)
                pg.wait_for_timeout(900)
            out["B_点开后"] = pg.evaluate(READ)
            pg.screenshot(path="/tmp/b840-clone-editor.png")

            # ★ Esc 的**两条路径**都要测：
            #   ① 焦点**不在**可编辑元素里（刚打开）⟹ 走画布那套全局键盘契约（store 分支）
            #   ② 焦点**在标题输入框**里 ⟹ 全局那套对可编辑目标是**早退**的 ⟹ 走编辑器自己那层
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(500)
            out["B2_Esc后_焦点不在输入框"] = {
                "★编辑器还在吗": pg.evaluate(
                    "() => Boolean(document.querySelector('[data-character-editor]'))"),
                "★面板还在吗": pg.evaluate(
                    "() => Boolean(document.querySelector('[data-character-studio]'))"),
            }
            # ★ 再点开一次（继续后面的交互）
            if bb:
                pg.mouse.click(bb["x"] + bb["w"] / 2, bb["y"] + bb["h"] / 2)
                pg.wait_for_timeout(700)
            out["B3_再打开"] = pg.evaluate(READ)

            # ★ 拖第一条滑杆（真实鼠标点到轨道 60% 处）
            sl = pg.evaluate("""() => {
              const e=document.querySelector('[data-character-editor-slider]');
              if(!e)return null; const r=e.getBoundingClientRect();
              return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),
                      h:Math.round(r.height)};}""")
            out["★滑杆盒"] = sl
            if sl:
                pg.mouse.click(sl["x"] + sl["w"] * 0.6, sl["y"] + sl["h"] / 2)
                pg.wait_for_timeout(400)
            out["C_拖滑杆后"] = pg.evaluate(READ)

            # ★ 点「祛斑祛痘」开关
            sw = pg.evaluate("""() => {
              const e=document.querySelector('[data-character-editor-switch]');
              if(!e)return null; const r=e.getBoundingClientRect();
              return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),
                      h:Math.round(r.height)};}""")
            if sw:
                pg.mouse.click(sw["x"] + sw["w"] / 2, sw["y"] + sw["h"] / 2)
                pg.wait_for_timeout(400)
            out["D_点开关后"] = pg.evaluate(READ)

            # ★ 点「确认生成」⟹ clone **不消耗**积分（源站会消耗 ⚡44 真实积分）
            #   ⟹ 读数：积分数值仍应是 44，且给出「不消耗」的如实提示
            gb = pg.evaluate("""() => {
              const e=document.querySelector('[data-character-editor-generate]');
              if(!e)return null; const r=e.getBoundingClientRect();
              return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),
                      h:Math.round(r.height)};}""")
            if gb:
                pg.mouse.click(gb["x"] + gb["w"] / 2, gb["y"] + gb["h"] / 2)
                pg.wait_for_timeout(350)
            out["D2_点确认生成后"] = pg.evaluate(READ)
            pg.wait_for_timeout(2600)

            # ★ 点右栏第二个页签（眉眼）⟹ 应显示**空态说明**
            #   ★★ **batch 843 起改点「妆造」**：眉眼页在 batch 842 已实现
            #   ⟹ ⟹ 「仍未实现的那一页」变成了妆造 ⟹ ⟹ 探针必须跟着改
            #   ⟹ ⟹ （★ 门禁改了而探针没改 ⟹ ⟹ 那条断言就会**永远红** ⟹ ⟹ 那是**假绿/假红**）
            tb = pg.evaluate("""() => {
              const e=document.querySelector('[data-character-editor-tab="makeup"]');
              if(!e)return null; const r=e.getBoundingClientRect();
              return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),
                      h:Math.round(r.height)};}""")
            if tb:
                pg.mouse.click(tb["x"] + tb["w"] / 2, tb["y"] + tb["h"] / 2)
                pg.wait_for_timeout(400)
            out["E_切页签后"] = pg.evaluate(READ)

            # ★ 切回「皮肤」页签（**留在「脸部精修」段** ⟹ ⟹ 右栏仍是页签行 ＋ 6 条滑杆）
            pg.evaluate("""() => {
              const t=document.querySelector('[data-character-editor-tab="skin"]');
              if(t)t.click();}""")
            pg.wait_for_timeout(400)
            out["F_切回皮肤"] = pg.evaluate(READ)

            # ★★ **batch 844 起**：点左列**第三段**（身材塑形）⟹ **页签行应当消失**
            #   （★ 844 起第二段「脸部 & 身体特征」已实现 ⟹ ⟹ 未实现的又挪了一位）
            #   ⟹ ⟹ 那是**当下仍未实现**的那一块（源站实测有内容 ⟹ ⟹ clone 显示空态说明）
            #   ★ ★ 探针必须**真的点一下** ⟹ ⟹ 否则「这个入口没有 X」这类断言根本不成立
            #   ★ ★ 且必须是**从 face 段点过去**的 ⟹ ⟹ 才是**真实的转移**（不是原地 no-op）
            pg.evaluate("""() => {
              const s=document.querySelector('[data-character-editor-segment="body"]');
              if(s)s.click();}""")
            pg.wait_for_timeout(400)
            out["F2_第三段"] = pg.evaluate(READ)

            # ★ 切回「脸部精修」段 ⟹ 页签行应当回来
            pg.evaluate("""() => {
              const s=document.querySelector('[data-character-editor-segment="face"]');
              if(s)s.click();}""")
            pg.wait_for_timeout(400)
            out["F3_切回脸部精修"] = pg.evaluate(READ)

            # ★ 在标题输入框里输入（真实键盘）
            nb = pg.evaluate("""() => {
              const e=document.querySelector('[data-character-editor-name]');
              if(!e)return null; const r=e.getBoundingClientRect();
              return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),
                      h:Math.round(r.height)};}""")
            if nb:
                pg.mouse.click(nb["x"] + 30, nb["y"] + nb["h"] / 2)
                pg.wait_for_timeout(200)
                pg.keyboard.press("End")
                for _ in range(4):
                    pg.keyboard.press("Backspace")
                pg.keyboard.type("克隆体")
                pg.wait_for_timeout(300)
            out["G_改名后"] = pg.evaluate(READ)

            # ★ 点「保存」⟹ **真的**改名并落回角色 ⟹ 编辑器关闭
            sv = pg.evaluate("""() => {
              const e=document.querySelector('[data-character-editor-save]');
              if(!e)return null; const r=e.getBoundingClientRect();
              return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),
                      h:Math.round(r.height)};}""")
            if sv:
                pg.mouse.click(sv["x"] + sv["w"] / 2, sv["y"] + sv["h"] / 2)
                pg.wait_for_timeout(700)
            out["G2_点保存后"] = {
                "★编辑器还在吗": pg.evaluate(
                    "() => Boolean(document.querySelector('[data-character-editor]'))"),
                "★面板名字": pg.evaluate(
                    """() => { const e=document.querySelector('[data-character-studio-name]');
                        return e?(e.textContent||'').trim():null; }"""),
            }
            # ★ 再打开一次 ⟹ 标题里应是**改过的名字**
            if bb:
                pg.mouse.click(bb["x"] + bb["w"] / 2, bb["y"] + bb["h"] / 2)
                pg.wait_for_timeout(700)
            out["G3_重开后标题"] = (pg.evaluate(READ) or {}).get("标题输入")

            # ★ 按 Esc ⟹ 关掉编辑器、**面板还在**
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(600)
            out["H_Esc后"] = {
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
        for k in ("★是否点开角色库入口", "★面板是否打开", "★是否有编辑器"):
            print("%-18s %r" % (k, out.get(k)))
        for stage in ("A_点编辑前", "B_点开后", "C_拖滑杆后", "D_点开关后",
                      "E_切页签后", "F_切回皮肤", "G_改名后"):
            r = out.get(stage) or {}
            if not r:
                continue
            print("── %s" % stage)
            for key in ("模态盒", "内容行盒", "左列盒", "预览盒", "右列盒", "标题输入",
                        "标签行", "五段", "页签", "滑杆轨道", "滑杆数值", "开关",
                        "确认生成", "智能调整", "底栏盒", "保存", "保存并添加到画布",
                        "保存时生成角色资产", "提示", "空态"):
                if key in r:
                    print("   %-16s %s" % (key, json.dumps(r[key], ensure_ascii=False)))
        print("H_Esc后:", json.dumps(out.get("H_Esc后"), ensure_ascii=False))
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    sys.exit(main())
