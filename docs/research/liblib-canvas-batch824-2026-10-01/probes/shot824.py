#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 824：源站 vs clone 的**底部工具条截图比对**（同视口、同裁剪区）。

★ 为什么用截图：DOM 读数只能告诉你「有一个 48×48、aria-label=TV Director
  的按钮」⟹ 但**它长什么样、是不是独立于药丸、旁边有没有字**，DOM 读数
  一开始骗了我（textContent 里有「TV Director」⟹ 我以为那是可见文字）。
  ⟹ ★★ **裁图放大**才发现源站旁边是空的 ⟹ 这一步是纯 DOM 读数给不了的。

★ 公平比较的前提：★ **同一视口 1600×950**（源站那张截图就是这个视口量的）
  ⟹ clone 也必须用 1600×950 量，否则药丸宽度不同，比出来的差是视口的差。
"""
import pathlib

from playwright.sync_api import sync_playwright

OUT_DIR = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/research/"
    "liblib-canvas-batch824-2026-10-01/shots")
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE = "http://localhost:4317"
VP = {"width": 1600, "height": 950}
# ★ 与源站那张 /tmp/liblib_source_bottom.png **完全相同**的裁剪区
CLIP = {"x": 640, "y": 870, "width": 390, "height": 75}

with sync_playwright() as pw:
    br = pw.chromium.launch(headless=True)
    ctx = br.new_context(viewport=VP, device_scale_factor=1, locale="zh-CN")
    pg = ctx.new_page()
    pg.goto(BASE, wait_until="domcontentloaded", timeout=90_000)
    pg.wait_for_timeout(3200)
    # ★ 把鼠标挪开，避免 hover 态影响
    pg.mouse.move(5, 5)
    pg.wait_for_timeout(400)
    pg.screenshot(path=str(OUT_DIR / "clone-824-bottom.png"))
    pg.screenshot(path=str(OUT_DIR / "clone-824-bottom-crop.png"), clip=CLIP)
    print("整页截图:", OUT_DIR / "clone-824-bottom.png")
    print("裁剪截图:", OUT_DIR / "clone-824-bottom-crop.png")
    # ★ 顺带记一下 clone 这一屏的读数（供 README 对照）
    import json
    read = pg.evaluate("""()=>{
      const vis=(e)=>{const r=e.getBoundingClientRect();
        if(r.width===0&&r.height===0)return false;
        const cs=getComputedStyle(e);
        return cs.visibility!=='hidden'&&cs.display!=='none'
          && Number(cs.opacity||'1')>0;};
      const out=[];
      for(const e of document.querySelectorAll('button[aria-label],button[title]')){
        if(!vis(e))continue;
        const r=e.getBoundingClientRect();
        if(r.y < window.innerHeight-140) continue;
        if(r.width>200) continue;
        out.push({aria:e.getAttribute('aria-label')||'',
          w:Math.round(r.width),h:Math.round(r.height),
          x:Math.round(r.x),y:Math.round(r.y)});}
      return {viewport:[window.innerWidth,window.innerHeight], buttons:out};}""")
    (OUT_DIR / "clone-824-bottom-reading.json").write_text(
        json.dumps(read, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(read, ensure_ascii=False))
    br.close()
