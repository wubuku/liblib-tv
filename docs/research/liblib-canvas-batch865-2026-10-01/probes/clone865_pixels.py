#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 865 像素对照探针：**结构变了，像素有没有变？**

## ★ 为什么需要它（★ 这是本批最容易被糊弄过去的地方）

★ D25 是**结构**对齐（遮罩层／空框／三分线层／开关 四者平级）。
★ ★ 第一版我**推**过「clone 的线在框里、没有 `overflow-hidden` ⟹ 四角会溢出圆角」
⟹ ⟹ **推错了**：那四条线在 `33.333%`／`66.667%` 处 ⟹ ⟹ **永远碰不到四角**
⟹ ⟹ ⟹ **裁剪对线没有可见影响**。
★ ⇒ 所以「结构改了」**不等于**「视觉变了」⟹ ⟹ 必须**测**，不能推。

## ★ 怎么测才确定（★ A/B 在**同一页面同一时刻**）

★ ① 选 `16:9`、开参考线；
★ ② **隐藏 3D canvas** ＋ 给视口容器一个**纯色底**
   ⟹ ⟹ 3D 场景一直在动 ⟹ ⟹ 不这么做，截图就**不可比**；
★ ③ 截**新结构**（WORK）的取景框区域 ⟹ ⟹ 记作 A；
★ ④ ★ **DOM 手术**：把三分线层与开关**搬回框里**、并把它们的坐标改成
   「相对框」的旧写法（`left = 框宽 − 40`／`top = 8`、三层 `inset-0`）
   ⟹ ⟹ 这就是**旧结构**（HEAD 态）⟹ ⟹ 截同一区域 ⟹ ⟹ 记作 B；
★ ⑤ **逐像素**比 A 与 B。

★ ★ A 与 B 在**同一页面、同一时刻**⟹ ⟹ 差异**只可能**来自结构本身。
★ ⇒ 期望：**0 个像素不同** ⟹ ⟹ D25 是**纯结构对齐**，**视觉无差别**。

## 输出
  raw/clone-865-pixels-{new,old}.png
  raw/clone-865-pixels.json
"""
from __future__ import annotations

import json
import pathlib

from PIL import Image
from playwright.sync_api import sync_playwright

BATCH = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv/"
                     "docs/research/liblib-canvas-batch865-2026-10-01")
RAW = BATCH / "raw"
BASE = "http://localhost:4317"

# ★ 确定性化：隐藏 3D canvas ＋ 纯色底
FREEZE = r"""()=>{
  const st=document.createElement('style');
  st.id='b865-freeze';
  st.textContent='canvas{visibility:hidden !important}'
    +'.react-flow__viewport{background:#101418 !important}';
  document.head.appendChild(st);
  return true;
}"""

# ★ ★ DOM 手术：把三分线层与开关搬回框里（= 旧结构）
SURGERY = r"""()=>{
  const cont=document.querySelector('[data-director-aspect-mask-container]');
  const frame=document.querySelector('[data-director-aspect-frame]');
  const thirds=document.querySelector('[data-director-thirds]');
  const btn=document.querySelector('[data-director-frame-thirds-toggle]');
  if(!cont||!frame||!thirds||!btn) return {ok:false};
  const r=frame.getBoundingClientRect();
  // 三分线层：塞进框里 ⟹ 旧写法是 `absolute inset-0`
  thirds.style.left='0px'; thirds.style.top='0px';
  thirds.style.width='100%'; thirds.style.height='100%';
  thirds.style.overflow='visible';            // ★ 旧结构：框没有 overflow-hidden
  thirds.removeAttribute('aria-hidden');      // ★ 旧结构：没有 aria-hidden
  frame.appendChild(thirds);
  // 开关：塞进框里 ⟹ 旧写法是「相对框」的 (框宽 − 40, 8)
  btn.style.left=(r.width-40)+'px'; btn.style.top='8px';
  frame.appendChild(btn);
  return {ok:true, 框宽:Math.round(r.width)};
}"""

# ★ 读出取景框的矩形（截图区域）
RECT = r"""()=>{
  const f=document.querySelector('[data-director-aspect-frame]');
  if(!f) return null;
  const r=f.getBoundingClientRect();
  return {x:Math.floor(r.x),y:Math.floor(r.y),
          w:Math.ceil(r.width),h:Math.ceil(r.height)};
}"""


def open_desk(page) -> None:
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.wait_for_timeout(3_000)
    page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
    page.wait_for_function("() => Boolean(window.__director_store)", timeout=90_000)
    page.wait_for_timeout(1_500)
    node = page.locator(".react-flow__node-script-execution").first
    try:
        node.scroll_into_view_if_needed(timeout=8_000)
        page.wait_for_timeout(400)
        node.hover(timeout=8_000)
        page.wait_for_timeout(600)
    except Exception:  # noqa: BLE001
        pass
    page.locator("[data-open-director]").first.click(timeout=15_000)
    page.wait_for_timeout(6_500)
    page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
    page.wait_for_timeout(500)


def main() -> int:
    audit: dict = {"batch": 865, "probe": "clone865_pixels"}
    RAW.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080},
                                    device_scale_factor=1)
            open_desk(page)
            page.evaluate(
                "() => { const s = window.__director_store.getState();"
                " s.setFrameAspectRatio('16:9'); s.toggleThirds(); }")
            page.wait_for_timeout(1_200)
            page.evaluate(FREEZE)
            page.wait_for_timeout(600)
            rect = page.evaluate(RECT)
            audit["取景框矩形"] = rect
            if not rect:
                audit["异常"] = "★ 取景框不在场"
                return 1
            clip = {"x": rect["x"], "y": rect["y"],
                    "width": rect["w"], "height": rect["h"]}
            # ★ A：新结构
            page.screenshot(path=str(RAW / "clone-865-pixels-new.png"), clip=clip)
            # ★ ★ B：DOM 手术 ⟹ ⟹ 旧结构
            audit["手术"] = page.evaluate(SURGERY)
            page.wait_for_timeout(600)
            page.screenshot(path=str(RAW / "clone-865-pixels-old.png"), clip=clip)
        finally:
            browser.close()

    # ★ 逐像素比
    a = Image.open(RAW / "clone-865-pixels-new.png").convert("RGB")
    b = Image.open(RAW / "clone-865-pixels-old.png").convert("RGB")
    audit["尺寸"] = {"新": a.size, "旧": b.size}
    if a.size != b.size:
        audit["差异"] = "★ 尺寸不同 ⟹ ⟹ 不可比"
    else:
        pa, pb = a.load(), b.load()
        w, h = a.size
        diff = 0
        maxd = 0
        first = None
        for y in range(h):
            for x in range(w):
                ra, ga, ba = pa[x, y]
                rb, gb, bb = pb[x, y]
                d = max(abs(ra - rb), abs(ga - gb), abs(ba - bb))
                if d:
                    diff += 1
                    maxd = max(maxd, d)
                    if first is None:
                        first = {"x": x, "y": y,
                                 "新": [ra, ga, ba], "旧": [rb, gb, bb]}
        audit["逐像素"] = {"总像素": w * h, "不同像素": diff,
                          "最大通道差": maxd, "首个差异": first}
    (RAW / "clone-865-pixels.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=1)[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
