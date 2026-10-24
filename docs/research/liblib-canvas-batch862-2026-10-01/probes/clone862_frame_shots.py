#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 862 取证截图：取景框 ＋ 框上那枚「构图参考线」开关（开／关两态）。

★ 输出
  images/862clone_frame_toggle_off.png   取景框 ＋ 开关（关闭态）
  images/862clone_frame_toggle_on.png    取景框 ＋ 三分线 ＋ 开关（开启态）
  images/862clone_frame_auto.png         「自适应」⟹ ⟹ 框与开关都不在场
  raw/clone-862-frame-shots.json         三张图的读数（几何 ＋ 颜色 ＋ 在场与否）
"""
from __future__ import annotations

import json
import pathlib

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch862-2026-10-01"
IMAGES = BATCH / "images"
RAW = BATCH / "raw"
BASE = "http://localhost:4317"

READ = r"""()=>{
  const f=document.querySelector('[data-director-aspect-frame]');
  const btn=document.querySelector('[data-director-frame-thirds-toggle]');
  const out={框在场:!!f, 开关在场:!!btn};
  if(f){
    const r=f.getBoundingClientRect();
    out.框={x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};
    const cs=getComputedStyle(f);
    out.描边={width:cs.outlineWidth,color:cs.outlineColor,offset:cs.outlineOffset};
    out.圆角=cs.borderRadius;
  }
  if(btn){
    const r=btn.getBoundingClientRect();
    const cs=getComputedStyle(btn);
    out.开关={x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),
              颜色:cs.color, 背景:cs.backgroundColor};
  }
  out.分线条数=document.querySelectorAll('[data-director-thirds] span').length;
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
    out: dict = {"batch": 862, "probe": "clone862_frame_shots"}
    IMAGES.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080},
                                    device_scale_factor=1)
            open_desk(page)
            page.locator("[data-director-rail-entry='aspect-ratio']").first.click(
                timeout=15000)
            page.wait_for_timeout(900)
            page.locator("[data-director-aspect-option='16:9']").first.click(timeout=8000)
            page.wait_for_timeout(900)

            out["关态"] = page.evaluate(READ)
            frame = page.locator("[data-director-aspect-frame]").first
            box = frame.bounding_box()
            clip = {"x": max(0, box["x"] - 40), "y": max(0, box["y"] - 40),
                    "width": min(1920 - max(0, box["x"] - 40), box["width"] + 80),
                    "height": min(1080 - max(0, box["y"] - 40), box["height"] + 80)}
            page.screenshot(path=str(IMAGES / "862clone_frame_toggle_off.png"),
                            clip=clip)

            page.locator("[data-director-frame-thirds-toggle]").first.click(timeout=8000)
            page.wait_for_timeout(800)
            out["开态"] = page.evaluate(READ)
            page.screenshot(path=str(IMAGES / "862clone_frame_toggle_on.png"),
                            clip=clip)

            page.locator("[data-director-aspect-option='自适应']").first.click(timeout=8000)
            page.wait_for_timeout(800)
            out["自适应"] = page.evaluate(READ)
            page.screenshot(path=str(IMAGES / "862clone_frame_auto.png"))
        finally:
            browser.close()
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "clone-862-frame-shots.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1)[:2500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
