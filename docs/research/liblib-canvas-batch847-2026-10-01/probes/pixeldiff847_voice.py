#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 847：第五段右栏顶部的**像素对照**（源站 ↔ clone，同一个 clip）。

## 为什么截这一片

★ 门禁已经比了 **152 项几何** ＋ **786 项计算样式** ⟹ ⟹ DOM 层面已经对齐
⟹ ⟹ 但那只说明「盒子与样式一致」⟹ ⟹ **画出来**长什么样还没验
⟹ ⟹ 而这一段有三处**只能靠像素看**的东西：
  ① 标题行那三枚页签的**图标字形**（源站 iconify ⟹ ⟹ clone 是 lucide 占位）
  ② 音色卡那枚**图标区**（白 6% 底 ＋ 圆角 8 ＋ 16×16 图标）
  ③ 播放按钮那枚 14×14 图标
⟹ ⟹ ★ 这三处**预期就有差**（字形不可得项）⟹ ⟹ 差多少要**量出来**才能如实标注。

★ 源站与 clone 的角色编辑器模态**同在视口 (361,161)** ⟹ ⟹ 同一个 clip
  在两端截到的是**同一片 UI** ⟹ ⟹ 可以直接相减。
★ clip 取 `x=1290 y=225 255×200` ⟹ ⟹ 覆盖标题行（231..271）＋ 工具行（279..311）
  ＋ 前两张音色卡（319..423）。

★ 输出：
  - `raw/source-847-voice.png`（源站截屏，★ **入库** ⟹ ⟹ 对照可从已入库文件复现）
  - `raw/clone-847-voice.png`（clone 截屏，入库）
  - `raw/pixel-diff-847-voice.json`（逐像素对照结果，入库）

★ **归因**另由 `probes/pixelattrib847.py` 做（读两张**已入库**的 PNG ＋ raw 里的盒
  ⟹ ⟹ 回答「差异到底落在**文字**还是**图标**上」）。
"""
import json
import pathlib
import sys
import traceback

from PIL import Image, ImageChops

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch847-2026-10-01"
SRC_PNG = BATCH / "raw/source-847-voice.png"
CLONE_PNG = BATCH / "raw/clone-847-voice.png"
OUT_JSON = BATCH / "raw/pixel-diff-847-voice.json"

URL = ("https://www.liblib.tv/canvas"
       "?spaceId=7709759&projectId=a860e1da8e9e4504bececda022386429")
COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
BASE = "http://localhost:4317"

# ★ 与源站截屏**同一个** clip（★ 覆盖标题行 ＋ 工具行 ＋ 前两张卡）
CLIP = {"x": 1290, "y": 225, "width": 255, "height": 200}


def source_shot() -> dict:
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                             locale="zh-CN")
        ctx.add_cookies([{"name": c["name"], "value": c["value"],
                          "domain": c["domain"], "path": c.get("path", "/")}
                         for c in cookies])
        pg = ctx.new_page()
        pg.set_default_timeout(25_000)
        pg.goto(URL, wait_until="domcontentloaded", timeout=90_000)
        pg.wait_for_timeout(12_000)
        el = pg.query_selector("text=下次再说")
        if el:
            el.click()
            pg.wait_for_timeout(900)
        el = pg.query_selector('[data-sidebar-btn="character-library"]')
        if el:
            bb = el.bounding_box()
            if bb:
                pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
        pg.wait_for_timeout(5000)
        tab = pg.query_selector("button:text-is('官方角色库')")
        if tab:
            bb = tab.bounding_box()
            if bb:
                pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
            pg.wait_for_timeout(4000)
        for e in pg.query_selector_all("span,div,button,a,p"):
            if (e.text_content() or "").strip() != "编辑角色":
                continue
            bb = e.bounding_box()
            if bb:
                pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
            break
        pg.wait_for_timeout(5000)
        # ★ 点左列第五段（音色音调）
        ok = pg.evaluate("""()=>{
          const bs=[...document.querySelectorAll('button')].filter(e=>{
            const r=e.getBoundingClientRect();return r.x<700&&r.width>100;});
          const b=bs.find(e=>(e.textContent||'').trim().startsWith('音色音调'));
          if(!b)return false; b.click(); return true;}""")
        pg.wait_for_timeout(3500)
        # ★ 自证：标题行里要有「音色库」
        head = pg.evaluate("""()=>{
          const a=[...document.querySelectorAll('aside')].find(x=>{
            const r=x.getBoundingClientRect();return r.x>=1273&&Math.round(r.width)===288;});
          if(!a)return '';
          const t=a.textContent||''; return t.slice(0,60);}""")
        pg.screenshot(path=str(SRC_PNG), clip=CLIP)
        br.close()
        return {"★点到第五段": ok, "★标题行附近文本": head}


def clone_shot() -> dict:
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                             locale="zh-CN")
        pg = ctx.new_page()
        pg.goto(BASE + "/?batch847pix=1", wait_until="domcontentloaded")
        pg.wait_for_timeout(3000)
        pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
        pg.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
        pg.evaluate("""() => {
          const c=[...document.querySelectorAll('button,[role="button"]')];
          const b=c.find(e=>e.getAttribute('aria-label')==='角色造型室')
            ||c.find(e=>(e.getAttribute('data-sidebar-btn')==='character-library'))
            ||c.find(e=>(e.textContent||'').trim()==='人物'); if(b)b.click();}""")
        pg.wait_for_timeout(1500)
        pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
        pg.evaluate("""() => {
          const t=[...document.querySelectorAll('[data-character-studio-tab]')]
            .find(e=>e.getAttribute('data-character-studio-tab')==='official'); if(t)t.click();}""")
        pg.wait_for_timeout(800)
        pg.evaluate("() => { const c=document.querySelector('[data-character-strip-card]'); if(c)c.click();}")
        pg.wait_for_timeout(700)
        b = pg.evaluate("""()=>{const e=document.querySelector('[data-character-studio-cta="edit"]');
          if(!e)return null;const r=e.getBoundingClientRect();
          return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)};}""")
        pg.mouse.click(b["x"], b["y"])
        pg.wait_for_timeout(1200)
        # ★ 等布局稳定（★ 字体/图片落位后才稳 ⟹ ⟹ 否则右栏会差 2px）
        for _ in range(40):
            cur = pg.evaluate("""()=>{const c=document.querySelector('.ce-col-right');
              if(!c)return null;const r=c.getBoundingClientRect();
              return {x:Math.round(r.x),y:Math.round(r.y)};}""")
            if cur == getattr(clone_shot, "_last", None):
                break
            clone_shot._last = cur
            pg.wait_for_timeout(250)
        seg = pg.evaluate("""()=>{const e=document.querySelector('[data-character-editor-segment="voice"]');
          if(!e)return null;const r=e.getBoundingClientRect();
          return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)};}""")
        pg.mouse.click(seg["x"], seg["y"])
        pg.wait_for_timeout(1200)
        head = pg.evaluate("""()=>{
          const e=document.querySelector('[data-character-editor-voice-tab]');
          return e?e.getAttribute('aria-label'):null;}""")
        pg.screenshot(path=str(CLONE_PNG), clip=CLIP)
        br.close()
        return {"★点到的页签": head}


def diff() -> dict:
    a = Image.open(SRC_PNG).convert("RGB")
    b = Image.open(CLONE_PNG).convert("RGB")
    if a.size != b.size:
        return {"★异常": "两张图尺寸不同：%s vs %s" % (a.size, b.size)}
    d = ImageChops.difference(a, b)
    gray = d.convert("L")
    w, h = gray.size
    px = gray.load()
    total = w * h
    over8 = 0
    over24 = 0
    cols = {}
    rows = {}
    for yy in range(h):
        for xx in range(w):
            v = px[xx, yy]
            if v > 8:
                over8 += 1
                cols[xx] = cols.get(xx, 0) + 1
                rows[yy] = rows.get(yy, 0) + 1
            if v > 24:
                over24 += 1
    hot_cols = sorted([c for c, n in cols.items() if n >= 6])
    hot_rows = sorted([r for r, n in rows.items() if n >= 6])
    # ★ 把「成片」的差列并成区间（⟹ ⟹ 便于判断差是不是集中在几枚图标上）
    spans = []
    for c in hot_cols:
        if spans and c == spans[-1][1] + 1:
            spans[-1][1] = c
        else:
            spans.append([c, c])
    return {
        "★clip": CLIP,
        "★总像素": total,
        "★差超过8": over8,
        "★差超过24": over24,
        "★差异占比_超过8": round(over8 / total * 100, 2),
        "★差异占比_超过24": round(over24 / total * 100, 2),
        "★热列区间": spans,
        "★热行区间": [[spans[0][0], spans[0][1]]] if False else hot_rows[:12],
        "★说明": "★ 预期差异**集中在三处图标字形**（标题行两枚页签图标 ＋ 工具行两枚图标 "
                  "＋ 卡里的图标区／播放按钮图标）⟹ ⟹ 那是 **iconify vs lucide** 的字形差 "
                  "⟹ ⟹ **不可得项** ⟹ ⟹ 如实标注",
    }


def main() -> int:
    out = {}
    try:
        out["源站"] = source_shot()
        out["clone"] = clone_shot()
        out["对照"] = diff()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                            encoding="utf-8")
        print("已落盘：", OUT_JSON)
        if out.get("异常"):
            print("异常：", out["异常"])
        print(json.dumps(out.get("对照", {}), ensure_ascii=False, indent=1)[:1500])
    return 0


if __name__ == "__main__":
    sys.exit(main())
