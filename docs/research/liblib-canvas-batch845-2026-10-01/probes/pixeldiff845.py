#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 845：clone 与源站的**像素**对照（同一片区域，同一个 clip）。

## 为什么还要这一步

门禁 S3 比的是**计算样式**，而**轨道与圆钮是伪元素**（`::-webkit-slider-runnable-track`
／`::-webkit-slider-thumb`）⟹ ⟹ 计算样式**量不到它们** ⟹ ⟹ 门禁看不到
「轨道是不是 2px」「填充段到没到圆钮中心」「圆钮是不是 14px 白圆」。

⟹ ⟹ 唯一能验证的，是**把同一片区域截下来逐像素比**。

★ 源站与 clone 的角色编辑器模态**都在视口正中**（源站 361／161 ⟹ clone 也一样）
  ⟹ ⟹ 同一个 clip 框在两端截到的是**同一片 UI** ⟹ ⟹ 可以直接相减。

★ 输出：
  - `/tmp/b845-clone-sliders.png`（clone 的截屏）
  - `raw/clone-845-sliders.png`（入库）
  - `raw/pixel-diff-845.json`（逐像素对照结果）
"""
import json
import pathlib
import sys
import traceback

from PIL import Image, ImageChops

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch845-2026-10-01"
SRC_PNG = BATCH / "raw/source-845-sliders.png"
CLONE_PNG = BATCH / "raw/clone-845-sliders.png"
OUT_JSON = BATCH / "raw/pixel-diff-845.json"

BASE = "http://localhost:4317"
TMP_PNG = pathlib.Path("/tmp/b845-clone-sliders.png")

# ★ 与源站截屏**同一个** clip（源站那趟：x 1285、y 235、260×175）
CLIP = {"x": 1285, "y": 235, "width": 260, "height": 175}


def open_editor(pg):
    pg.goto(BASE + "/?batch845vis=1", wait_until="domcontentloaded")
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


def main():
    out = {}
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            pg = ctx.new_page()
            open_editor(pg)
            # ★ 点「编辑角色」
            pg.evaluate("""() => {
              const c=document.querySelector('[data-character-studio-cta="edit"]');
              if(c)c.click();}""")
            pg.wait_for_timeout(1200)
            # ★ 点左列第三段（身材塑形）
            ok = pg.evaluate("""()=>{
              const s=document.querySelector('[data-character-editor-segment="body"]');
              if(!s)return false; s.click(); return true;}""")
            out["★点到_第三段"] = ok
            pg.wait_for_timeout(900)
            # ★ 自证：读到的第一条滑杆必须是「丰胸」
            first = pg.evaluate("""()=>{
              const e=document.querySelector('[data-character-editor-slider]');
              return e?e.getAttribute('aria-label'):null;}""")
            out["★读数_第一条滑杆"] = first
            out["★读数_是目标段"] = (first == "丰胸")
            # ★ 截屏（**同一个** clip）
            pg.screenshot(path=str(TMP_PNG), clip=CLIP)
            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()

    try:
        src = Image.open(SRC_PNG).convert("RGB")
        clone = Image.open(TMP_PNG).convert("RGB")
        diff = ImageChops.difference(src, clone)
        bbox = diff.getbbox()
        hist = diff.convert("L").histogram()
        total = sum(hist)
        over8 = sum(hist[9:])
        over24 = sum(hist[25:])
        maxd = max((i for i, v in enumerate(hist) if v), default=0)
        # ★ 逐行统计：哪些**行**差异最大（★ 便于定位差异是不是集中在轨道那一行）
        w, h = diff.size
        px = diff.load()
        rows = []
        for y in range(h):
            n = sum(1 for x in range(w) if px[x, y][0] > 24)
            if n:
                rows.append({"y": y, "差异像素数": n})
        rows.sort(key=lambda r: -r["差异像素数"])
        out["像素对照"] = {
            "★图幅": list(src.size),
            "★差异包围盒": list(bbox) if bbox else None,
            "★总像素": total,
            "★完全相同的像素": hist[0],
            "★差1到2": hist[1] + hist[2],
            "★差3到4": hist[3] + hist[4],
            "★差5到8": sum(hist[5:9]),
            "★差超过8": over8,
            "★差超过24": over24,
            "★最大通道差": maxd,
            "★差异占比_超过8": round(over8 / total, 4),
            "★差异占比_超过24": round(over24 / total, 4),
            "★差异最大的行": rows[:12],
            "★说明": "★ 逐像素相减 ⟹ 「差异最大的行」若集中在轨道那两行 ⟹ ⟹ "
                    "就说明轨道的粗细/填充段还没对齐；★ 文字行有差异 ⟹ ⟹ 字体渲染差异。"
                    "★ ★ 源站与 clone 的角色编辑器模态**同在视口 (361,161)** ⟹ ⟹ "
                    "同一个 clip 在两端截到的是**同一片 UI** ⟹ ⟹ 可以直接相减。",
        }
        clone.save(CLONE_PNG)
    except Exception:
        out["像素对照异常"] = traceback.format_exc()

    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已写入", OUT_JSON)
    print(json.dumps(out, ensure_ascii=False, indent=1)[:1800])
    return 0


if __name__ == "__main__":
    sys.exit(main())
