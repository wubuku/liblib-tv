#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 846：子页签行的**像素对照**（源站 ↔ clone，同一个 clip）。

## 为什么单独截这一片

846 的实测发现子页签行存在**两处**疑似差异：
  ① 源站**每一枚**页签都渲染 label span（未选中时 `grid-template-columns:0px`
     ＋ `overflow:hidden` ⟹ ⟹ 文字被裁掉）；clone 只在选中那枚渲染 ⟹ ⟹ **结构差**
  ② clone 的子页签行宽 288（`.ce-tabs` 的 padding 24×2 ＋ 内容 240）⟹ ⟹
     源站 nav 盒是 240 ⟹ ⟹ 需要确认这是**同一口径**（源站 nav 在 `px-6` 的
     父 DIV 里 ⟹ ⟹ 240 是**内容区**宽度 ⟹ ⟹ clone 的 288 是**外层**盒）

⟹ ⟹ **文字层**（0 宽 vs 无 span）在**像素上**应当**完全看不出来**
⟹ ⟹ 所以必须**截同一片区域相减**才能判定 ⟹ ⟹ 光看 DOM 差异不���下结论。

★ 源站与 clone 的角色编辑器模态**同在视口 (361,161)** ⟹ ⟹ 同一个 clip
  在两端截到的是**同一片 UI** ⟹ ⟹ 可以直接相减。
★ clip 取 `x=1290 y=225 150×53`（⟹ ⟹ 覆盖三枚子页签 1297..1425）
  ⟹ ⟹ 与 `source846_tabsnap.py` 的**像素证据**同一片 ⟹ ⟹ 可交叉验证。

★ 输出：
  - `/tmp/b846-clone-tabs.png`（clone 截屏）
  - `raw/clone-846-tabs.png`（入库）
  - `raw/pixel-diff-846-tabs.json`（逐像素对照结果）
"""
import json
import pathlib
import sys
import traceback

from PIL import Image, ImageChops

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch846-2026-10-01"
SRC_PNG = pathlib.Path("/tmp/liblib_source_846_tabsnap.png")
CLONE_PNG = BATCH / "raw/clone-846-tabs.png"
OUT_JSON = BATCH / "raw/pixel-diff-846-tabs.json"

BASE = "http://localhost:4317"
TMP_PNG = pathlib.Path("/tmp/b846-clone-tabs.png")

# ★ 与源站截屏**同一个** clip（源站那趟：x 1290、y 225、150×53）
CLIP = {"x": 1290, "y": 225, "width": 150, "height": 53}


def open_editor(pg):
    pg.goto(BASE + "/?batch846tabpix=1", wait_until="domcontentloaded")
    pg.wait_for_timeout(3000)
    pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
    pg.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
    pg.evaluate("""() => {
      const cands=[...document.querySelectorAll('button,[role="button"]')];
      const b=cands.find(e=>e.getAttribute('aria-label')==='角色造型室')
        || cands.find(e=>e.getAttribute('data-sidebar-btn')==='character-library')
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
            pg.evaluate("""() => {
              const c=document.querySelector('[data-character-studio-cta="edit"]');
              if(c)c.click();}""")
            pg.wait_for_timeout(1200)
            # ★ 点「服装造型」分段 ⟹ ⟹ 子页签行才出现
            ok = pg.evaluate("""()=>{
              const bs=[...document.querySelectorAll('button')].filter(e=>{
                const r=e.getBoundingClientRect();
                return r.x<700&&r.width>100;});
              const b=bs.find(e=>(e.textContent||'').trim().startsWith('服装造型'));
              if(!b)return false; b.click(); return true;}""")
            out["★点到_第四段"] = ok
            pg.wait_for_timeout(1200)
            pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
            pg.screenshot(path=str(TMP_PNG), clip=CLIP)
            CLONE_PNG.write_bytes(TMP_PNG.read_bytes())
            br.close()

        # ★ 逐像素相减
        a = Image.open(SRC_PNG).convert("RGB")
        b = Image.open(CLONE_PNG).convert("RGB")
        out["★源站图幅"] = list(a.size)
        out["★clone图幅"] = list(b.size)
        if a.size != b.size:
            out["★说明"] = "图幅不同 ⟹ 无法相减"
        else:
            diff = ImageChops.difference(a, b)
            px = list(diff.getdata())
            w, h = a.size
            buckets = {"差0": 0, "差1到2": 0, "差3到4": 0, "差5到8": 0,
                       "差9到16": 0, "差17到24": 0, "差超过24": 0}
            worst = 0
            rows = {}
            cols = {}
            for i, p in enumerate(px):
                d = max(p)
                worst = max(worst, d)
                if d == 0:
                    buckets["差0"] += 1
                elif d <= 2:
                    buckets["差1到2"] += 1
                elif d <= 4:
                    buckets["差3到4"] += 1
                elif d <= 8:
                    buckets["差5到8"] += 1
                elif d <= 16:
                    buckets["差9到16"] += 1
                elif d <= 24:
                    buckets["差17到24"] += 1
                else:
                    buckets["差超过24"] += 1
                if d > 8:
                    y, x = divmod(i, w)
                    rows[y] = rows.get(y, 0) + 1
                    cols[x] = cols.get(x, 0) + 1
            total = w * h
            out["像素对照"] = {
                "★总像素": total,
                "★完全相同的像素": buckets["差0"],
                "★差1到2": buckets["差1到2"],
                "★差3到4": buckets["差3到4"],
                "★差5到8": buckets["差5到8"],
                "★差9到16": buckets["差9到16"],
                "★差17到24": buckets["差17到24"],
                "★差超过8": buckets["差9到16"] + buckets["差17到24"] + buckets["差超过24"],
                "★差超过24": buckets["差超过24"],
                "★最大通道差": worst,
                "★差异占比_超过8": round(
                    (buckets["差9到16"] + buckets["差17到24"] + buckets["差超过24"]) / total, 6),
                "★差异最大的行": sorted(rows.items(), key=lambda kv: -kv[1])[:10],
                "★差异最大的列": sorted(cols.items(), key=lambda kv: -kv[1])[:10],
            }
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT_JSON)
        if out.get("异常"):
            print("异常：", out["异常"])
        print(json.dumps(out.get("像素对照"), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    sys.exit(main())
