#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 839 clone 侧探针：读「角色资产视图」的**几何**，与源站实测对拍。

★ 源站实测基准（1920×1080，官方角色库页签，`raw/source-839-assets.json`）：
    模态           1198×758 @361,160
    内容区上沿     y=279
    图 1  164×220  @500,393   （立绘）
    图 2  165×220  @676,393   （近景）
    图 3  165×220  @853,393   （表情）
    图 4  391×220  @1030,393  （三视图）
    「选择角色音色」128×36 @896,646
    名字            88×22 @916,783

★ 本探针只读 clone（4317），不点任何会产生副作用的东西（角色库是 mock 数据）。

★ 输出：`/tmp/b839-clone-assets.json`
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path("/tmp/b839-clone-assets.json")

READ = """()=>{
  const realVis=(e)=>{
    for(let n=e;n&&n.nodeType===1;n=n.parentElement){
      const cs=getComputedStyle(n);
      if(cs.display==='none')return false;
      if(cs.visibility==='hidden')return false;
      if(Number(cs.opacity||'1')<=0.001)return false;
    }
    const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0;
  };
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\\s+/g,' ');
  const modal=document.querySelector('[data-character-studio]');
  const out={};
  if(!modal)return {err:'no modal'};
  out['模态盒']=box(modal);
  const content=document.querySelector('.cs-content');
  out['内容区盒']=content?box(content):null;
  const imgs=[...document.querySelectorAll('[data-character-studio-asset-image]')];
  out['资产图']=imgs.map(e=>({i:e.getAttribute('data-character-studio-asset-image'),
    box:box(e),可见:realVis(e),
    src:(e.querySelector('img')&&e.querySelector('img').getAttribute('src')||'').slice(-34)}));
  const voices=[...document.querySelectorAll('[data-character-studio-voice]')];
  out['音色按钮数量']=voices.length;
  const voice=voices[0];
  out['音色按钮']=voice?{box:box(voice),text:txt(voice),可见:realVis(voice),
    父cls:(voice.parentElement&&voice.parentElement.getAttribute('class')||'').slice(0,40),
    祖父cls:(voice.parentElement&&voice.parentElement.parentElement&&
            voice.parentElement.parentElement.getAttribute('class')||'').slice(0,40),
    定位:getComputedStyle(voice).position,
    定位父:(voice.offsetParent&&(voice.offsetParent.getAttribute('class')||voice.offsetParent.tagName)||'null').slice(0,40),
    全部:voices.map(v=>box(v))}:null;
  const name=document.querySelector('[data-character-studio-name]');
  out['名字']=name?{box:box(name),text:txt(name)}:null;
  const assets=document.querySelector('[data-character-studio-view-assets]');
  out['浮层']=assets?{box:box(assets),opacity:getComputedStyle(assets).opacity,
    pointerEvents:getComputedStyle(assets).pointerEvents}:null;
  const stage=document.querySelector('[data-character-studio-asset-view]');
  out['资产视图容器']=stage?{box:box(stage),
    角色:stage.getAttribute('data-character-studio-asset-view')}:null;
  const viewport=document.querySelector('.cs-viewport');
  out['carousel盒']=viewport?box(viewport):null;
  out['carousel是否压暗']=viewport?viewport.classList.contains('is-dimmed'):null;
  const vpTrack=document.querySelector('.cs-track');
  out['轨道opacity']=vpTrack?getComputedStyle(vpTrack).opacity:null;
  const vrow=document.querySelector('.cs-voice-row');
  out['音色行']=vrow?{box:box(vrow),
    定位父:(vrow.offsetParent&&(vrow.offsetParent.getAttribute('class')||vrow.offsetParent.tagName)||'null').slice(0,40),
    父盒:(vrow.offsetParent&&vrow.offsetParent.getBoundingClientRect)?{
      x:Math.round(vrow.offsetParent.getBoundingClientRect().x),
      y:Math.round(vrow.offsetParent.getBoundingClientRect().y)}:null,
    定位:vrow.getBoundingClientRect?getComputedStyle(vrow).position:''}:null;
  const stage2=document.querySelector('.cs-assets-stage');
  out['资产舞台盒']=stage2?{box:box(stage2),
    定位父:(stage2.offsetParent&&(stage2.offsetParent.getAttribute('class')||stage2.offsetParent.tagName)||'null').slice(0,40),
    定位:getComputedStyle(stage2).position}:null;
  const ae=document.activeElement;
  out['活动焦点']=ae?{tag:ae.tagName,
    cls:(ae.getAttribute&&ae.getAttribute('class')||'').slice(0,50),
    是资产视图:(ae.getAttribute&&ae.getAttribute('data-character-studio-asset-view'))||''}:null;
  return out;}"""


def main():
    out = {}
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            pg = ctx.new_page()
            pg.goto(BASE + "/?batch839=1", wait_until="domcontentloaded")
            pg.wait_for_timeout(3000)
            pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
            pg.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
            # ★ 打开角色库面板
            opened = pg.evaluate("""() => {
              const cands=[...document.querySelectorAll('button,[role="button"]')];
              const b=cands.find(e=>e.getAttribute('aria-label')==='角色造型室')
                || cands.find(e=>(e.getAttribute('data-sidebar-btn')==='character-library'))
                || cands.find(e=>(e.textContent||'').trim()==='人物');
              if(b){b.click();return true;} return false;}""")
            out["★是否点开角色库入口"] = opened
            pg.wait_for_timeout(1500)
            pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
            has_modal = pg.evaluate(
                "() => Boolean(document.querySelector('[data-character-studio]'))")
            out["★面板是否打开"] = has_modal
            if not has_modal:
                print("★ 面板没打开")
                br.close()
                return 2
            # ★ 切到「官方角色库」
            pg.evaluate("""() => {
              const t=[...document.querySelectorAll('[data-character-studio-tab]')]
                .find(e=>e.getAttribute('data-character-studio-tab')==='official');
              if(t)t.click();}""")
            pg.wait_for_timeout(800)
            # ★ 选中第一张角色卡
            pg.evaluate("""() => {
              const c=document.querySelector('[data-character-strip-card]');
              if(c)c.click();}""")
            pg.wait_for_timeout(700)
            out["A_点开前"] = pg.evaluate(READ)
            # ★ 悬停 ⟹ 等 ⟹ 点「查看角色资产」（浮层未显形时 pointer-events:none）
            bb = pg.evaluate("""() => {
              const e=document.querySelector('[data-character-studio-view-assets]');
              if(!e)return null; const r=e.getBoundingClientRect();
              return {x:Math.round(r.x),y:Math.round(r.y),
                      w:Math.round(r.width),h:Math.round(r.height)};}""")
            out["★浮层盒（悬停前）"] = bb
            if bb:
                pg.mouse.move(bb["x"] + bb["w"] / 2, bb["y"] + bb["h"] / 2)
                pg.wait_for_timeout(800)
            out["B_悬停后"] = pg.evaluate(READ)
            if bb:
                pg.mouse.click(bb["x"] + bb["w"] / 2, bb["y"] + bb["h"] / 2)
                pg.wait_for_timeout(900)
            out["C_点开后"] = pg.evaluate(READ)
            pg.screenshot(path="/tmp/b839-clone-assets.png")
            # ★ 点音色按钮
            vb = pg.evaluate("""() => {
              const e=document.querySelector('[data-character-studio-voice]');
              if(!e)return null; const r=e.getBoundingClientRect();
              return {x:Math.round(r.x),y:Math.round(r.y)};}""")
            if vb:
                pg.mouse.click(vb["x"] + 30, vb["y"] + 18)
                pg.wait_for_timeout(600)
            out["D_点音色后"] = pg.evaluate(READ)
            pg.screenshot(path="/tmp/b839-clone-assets-voice.png")
            # ★ Esc 关掉
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(600)
            out["E_Esc后"] = pg.evaluate(READ)
            # ★ F：浮层是 **toggle**（再点一次关掉）
            bb2 = pg.evaluate("""() => {
              const e=document.querySelector('[data-character-studio-view-assets]');
              if(!e)return null; const r=e.getBoundingClientRect();
              return {x:Math.round(r.x),y:Math.round(r.y),
                      w:Math.round(r.width),h:Math.round(r.height)};}""")
            if bb2:
                # ★ 第一次点 = **打开**（此刻资产视图是关的）
                pg.mouse.move(bb2["x"] + bb2["w"] / 2, bb2["y"] + bb2["h"] / 2)
                pg.wait_for_timeout(700)
                pg.mouse.click(bb2["x"] + bb2["w"] / 2, bb2["y"] + bb2["h"] / 2)
                pg.wait_for_timeout(700)
                out["F1_第一次点后"] = pg.evaluate(READ)
            # ★ 关掉之后**还能再打开**（不是一次性）
            out["F_再点浮层后"] = pg.evaluate(READ)
            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        for k in ("★是否点开角色库入口", "★面板是否打开"):
            print("%-20s %r" % (k, out.get(k)))
        for stage in ("A_点开前", "B_悬停后", "C_点开后", "D_点音色后", "E_Esc后", "F1_第一次点后", "F_再点浮层后"):
            r = out.get(stage) or {}
            if not r:
                print("%-12s （空）" % stage)
                continue
            print("── %s" % stage)
            print("   模态盒      ", r.get("模态盒"))
            print("   内容区盒    ", r.get("内容区盒"))
            print("   资产图      ", json.dumps(r.get("资产图"), ensure_ascii=False))
            print("   音色按钮    ", json.dumps(r.get("音色按钮"), ensure_ascii=False))
            print("   名字        ", json.dumps(r.get("名字"), ensure_ascii=False))
            print("   浮层        ", json.dumps(r.get("浮层"), ensure_ascii=False))
            print("   资产视图容器", json.dumps(r.get("资产视图容器"), ensure_ascii=False))
            print("   压暗/轨道op ", r.get("carousel是否压暗"), r.get("轨道opacity"))
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    sys.exit(main())
