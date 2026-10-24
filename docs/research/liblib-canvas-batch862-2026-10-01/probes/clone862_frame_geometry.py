#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 862 clone 探针：取景框**几何** ＋ 三分线**颜色** ＋ 框上开关**是否存在**。

## ★ 为什么要读这些

★ 源站逐字（`mP` 的几何算法）：
```js
let a=n.clientWidth, i=n.clientHeight;
let o=a-t-r,                      // t=左面板宽(281) r=右面板宽(281)
    s=Math.max(1,i-224),
    l=Math.min(Math.max(1,o-96), s*e),
    c=l/e;
c>s&&(l=(c=s)*e);
p({left:t+(o-l)/2, top:(i-c)/2, width:l, height:c});
```
★ 源站实测（16:9，1920×1080）：框 @(329,185) 1262×710。

★ clone 的 `getDirectorFrameRect` 是**从读数反推**的 padding 公式
   （`horizontalPadding=40 / topPadding=32 / bottomPadding=88`）
   ⟹ ⟹ **与源站逐字不是同一套算法** ⟹ ⟹ 必须实测对照。

## ★ 本探针要读到的
① clone 在 1920×1080 下六档的框**绝对几何**；
② clone 的 3D 视口容器尺寸 ＋ 左右栏宽度（用于判断「减面板」等价性）；
③ 三分线颜色（源站 ＝ `bg-(--color-white-alpha-50)` ＝ white/50）；
④ 框上是否**存在**那枚 32×32 的「构图参考线」开关（源站有）。

## 输出
  raw/clone-862-frame-geometry.json
"""
from __future__ import annotations

import json
import pathlib

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch862-2026-10-01"
RAW = BATCH / "raw"
BASE = "http://localhost:4317"

RATIOS = ["21:9", "16:9", "4:3", "1:1", "3:4", "9:16"]

READ_FRAME = r"""()=>{
  const f=document.querySelector('[data-director-aspect-frame]');
  if(!f) return null;
  const r=f.getBoundingClientRect();
  const cs=getComputedStyle(f);
  const thirds=[...document.querySelectorAll('[data-director-thirds] span')].map(s=>{
    const c=getComputedStyle(s); const rc=s.getBoundingClientRect();
    return {bg:c.backgroundColor, w:Math.round(rc.width), h:Math.round(rc.height),
            x:Math.round(rc.x), y:Math.round(rc.y)};
  });
  // ★ 框上那枚 32×32 的开关？
  const btns=[...document.querySelectorAll('button')].map(b=>{
    const rc=b.getBoundingClientRect(); const c=getComputedStyle(b);
    return {title:b.title||'', ariaLabel:b.getAttribute('aria-label')||'',
            cls:(b.getAttribute('class')||''), x:Math.round(rc.x), y:Math.round(rc.y),
            w:Math.round(rc.width), h:Math.round(rc.height)};
  }).filter(b=>b.w===32&&b.h===32&&b.x>=r.left-4&&b.x<=r.right+4&&b.y>=r.top-4&&b.y<=r.bottom+4);
  return {rect:{x:Math.round(r.x),y:Math.round(r.y),
                w:Math.round(r.width),h:Math.round(r.height)},
          border:cs.borderTopWidth, borderColor:cs.borderTopColor,
          outline:cs.outlineWidth, outlineColor:cs.outlineColor,
          outlineOffset:cs.outlineOffset, radius:cs.borderRadius,
          boxShadow:cs.boxShadow.slice(0,80),
          thirds, 框上32按钮:btns};
}"""

READ_LAYOUT = r"""()=>{
  const vp=document.querySelector('[data-director-workspace]')||
           document.querySelector('[data-director-viewport]');
  const cand=[...document.querySelectorAll('div')].filter(e=>{
    const c=e.getAttribute('class')||'';
    return /relative/.test(c)&&/overflow-hidden|flex-1/.test(c);
  }).map(e=>{const r=e.getBoundingClientRect();
    return {cls:(e.getAttribute('class')||'').slice(0,70),
            x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};});
  return {视口候选:cand.slice(0,12),
          窗口:{w:window.innerWidth,h:window.innerHeight}};
}"""


def open_desk(page) -> None:
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
    page.wait_for_function("() => Boolean(window.__director_store)", timeout=90_000)
    page.wait_for_timeout(1500)
    node = page.locator(".react-flow__node-script-execution").first
    try:
        node.scroll_into_view_if_needed(timeout=8000)
        page.wait_for_timeout(400)
        node.hover(timeout=8000)
        page.wait_for_timeout(600)
    except Exception:  # noqa: BLE001
        pass
    page.locator("[data-open-director]").first.click(timeout=15000)
    page.wait_for_timeout(6500)
    page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")


def main() -> int:
    out: dict = {"batch": 862, "probe": "clone862_frame_geometry"}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080},
                                    device_scale_factor=1)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            open_desk(page)
            out["布局"] = page.evaluate(READ_LAYOUT)

            page.locator("[data-director-rail-entry='aspect-ratio']").first.click(
                timeout=15000)
            page.wait_for_timeout(900)
            for ratio in RATIOS:
                page.locator(f"[data-director-aspect-option='{ratio}']").first.click(
                    timeout=8000)
                page.wait_for_timeout(700)
                out[f"几何_{ratio}"] = page.evaluate(READ_FRAME)
            out["错误"] = [e for e in errors if "TransformControls" not in e][:8]
        finally:
            browser.close()
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "clone-862-frame-geometry.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for ratio in RATIOS:
        g = out.get(f"几何_{ratio}")
        if g:
            print(ratio, g["rect"], "| 三分线", len(g["thirds"]),
                  "| 框上32按钮", len(g["框上32按钮"]),
                  "| border", g["border"], g["borderColor"], "| radius", g["radius"])
        else:
            print(ratio, "框不在场")
    print("布局:", json.dumps(out.get("布局"), ensure_ascii=False)[:900])
    print("错误:", out.get("错误"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
