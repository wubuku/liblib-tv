#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 862 clone 探针：取景框上的**构图参考线**开关（源站逐字对齐的验证）。

## ★ 判据（全部来自源站实测 `raw/source-862-frame-thirds.json` ＋ 源站逐字）

① 「自适应」⟹ ⟹ **取景框不在场** ⟹ ⟹ 框上那枚开关**也不在场**
   （源站逐字：`onToggleCompositionGrid:null!==tr?…:void 0`）；
② 选了具体比例 ⟹ ⟹ 框在场 ⟹ ⟹ 框上有**一枚 32×32** 的开关，
   `title="构图参考线"`；
③ ★ **相对偏移不变量**（跨六档都成立，不依赖视口尺寸）：
   开关左缘 − 框左缘 ＝ 框宽 − 40；开关上缘 − 框上缘 ＝ 8
   （源站逐字：`left: u.left + u.width − 40`、`top: u.top + 8`）；
④ 点开关 ⟹ ⟹ 框内出现 **4 条**三分线，颜色 `rgba(255,255,255,0.5)`
   （源站逐字 `bg-(--color-white-alpha-50)` ＝ 白 50%）；
⑤ 框的描边 ＝ **outline** 1px／白 18%／内缩 1px，圆角 **12px**
   （源站逐字 `outline-white/18 … outline -outline-offset-1 rounded-xl`）。

## 输出
  raw/clone-862-frame-thirds.json
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

READ = r"""()=>{
  const f=document.querySelector('[data-director-aspect-frame]');
  const btn=document.querySelector('[data-director-frame-thirds-toggle]');
  if(!f) return {框在场:false, 按钮在场:!!btn};
  const r=f.getBoundingClientRect();
  const cs=getComputedStyle(f);
  const out={框在场:true, 按钮在场:!!btn,
             框:{x:Math.round(r.x),y:Math.round(r.y),
                 w:Math.round(r.width),h:Math.round(r.height)},
             描边:{width:cs.outlineWidth,color:cs.outlineColor,
                   offset:cs.outlineOffset,style:cs.outlineStyle},
             borderWidth:cs.borderTopWidth, 圆角:cs.borderRadius};
  if(btn){
    const br=btn.getBoundingClientRect();
    const bcs=getComputedStyle(btn);
    out.按钮={x:Math.round(br.x),y:Math.round(br.y),
              w:Math.round(br.width),h:Math.round(br.height),
              title:btn.title, ariaLabel:btn.getAttribute('aria-label'),
              pressed:btn.getAttribute('aria-pressed'),
              相对左:Math.round(br.x-r.x), 相对上:Math.round(br.y-r.y),
              期望左:Math.round(r.width)-40, 期望上:8,
              颜色:bcs.color, 背景:bcs.backgroundColor,
              pointerEvents:bcs.pointerEvents, position:bcs.position,
              zIndex:bcs.zIndex};
    const svg=btn.querySelector('svg');
    out.按钮.svg=svg?svg.getAttribute('viewBox'):null;
    out.按钮.pathLen=btn.querySelectorAll('path').length;
  }
  const thirds=[...document.querySelectorAll('[data-director-thirds] span')].map(s=>{
    const c=getComputedStyle(s); const rc=s.getBoundingClientRect();
    return {bg:c.backgroundColor, w:Math.round(rc.width), h:Math.round(rc.height)};
  });
  out.三分线={条数:thirds.length, 线:thirds};
  return out;
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
    out: dict = {"batch": 862, "probe": "clone862_frame_thirds"}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080},
                                    device_scale_factor=1)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            open_desk(page)

            # ① 「自适应」⟹ ⟹ 框不在场 ⟹ ⟹ 按钮也不在场
            out["自适应"] = page.evaluate(READ)

            # ② 六档 ⟹ ⟹ 框在 ⟹ ⟹ 按钮在 ⟹ ⟹ 相对偏移恒为 (宽−40, 8)
            page.locator("[data-director-rail-entry='aspect-ratio']").first.click(
                timeout=15000)
            page.wait_for_timeout(900)
            for ratio in RATIOS:
                page.locator(f"[data-director-aspect-option='{ratio}']").first.click(
                    timeout=8000)
                page.wait_for_timeout(700)
                out[f"档_{ratio}"] = page.evaluate(READ)

            # ③ 点框上那枚开关 ⟹ ⟹ 三分线出现
            before = out.get("档_16:9", {})
            page.locator("[data-director-frame-thirds-toggle]").first.click(timeout=8000)
            page.wait_for_timeout(800)
            out["点开关后"] = page.evaluate(READ)
            out["点开关前_三分线条数"] = (before.get("三分线") or {}).get("条数")
            out["点开关后_三分线条数"] = (
                (out["点开关后"].get("三分线") or {}).get("条数"))

            # ④ 再点一次 ⟹ ⟹ 三分线消失
            page.locator("[data-director-frame-thirds-toggle]").first.click(timeout=8000)
            page.wait_for_timeout(800)
            out["再点后_三分线条数"] = (
                (page.evaluate(READ).get("三分线") or {}).get("条数"))

            # ⑤ 回到「自适应」⟹ ⟹ 框与按钮都不在场
            page.locator("[data-director-aspect-option='自适应']").first.click(
                timeout=8000)
            page.wait_for_timeout(700)
            out["回自适应"] = page.evaluate(READ)
            out["错误"] = [e for e in errors if "TransformControls" not in e][:8]
        finally:
            browser.close()
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "clone-862-frame-thirds.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("自适应:", json.dumps(out.get("自适应"), ensure_ascii=False))
    for ratio in RATIOS:
        g = out.get(f"档_{ratio}") or {}
        b = g.get("按钮") or {}
        print(ratio, g.get("框"), "| 按钮", b.get("x"), b.get("y"), b.get("w"),
              b.get("h"), "| 相对", b.get("相对左"), b.get("相对上"),
              "| 期望", b.get("期望左"), b.get("期望上"),
              "| 描边", (g.get("描边") or {}).get("width"),
              (g.get("描边") or {}).get("color"),
              (g.get("描边") or {}).get("offset"),
              "| 圆角", g.get("圆角"), "| border", g.get("borderWidth"))
    print("点开关前条数:", out.get("点开关前_三分线条数"),
          "→ 点后:", out.get("点开关后_三分线条数"),
          "→ 再点:", out.get("再点后_三分线条数"))
    print("点开关后 按钮样式:",
          json.dumps((out.get("点开关后") or {}).get("按钮"), ensure_ascii=False))
    print("回自适应:", json.dumps(out.get("回自适应"), ensure_ascii=False))
    print("错误:", out.get("错误"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
