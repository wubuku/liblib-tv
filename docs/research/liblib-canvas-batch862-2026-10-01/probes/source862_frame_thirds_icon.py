#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 862 源站探针（补）：取景框上「构图参考线」按钮的 **SVG 逐字**。

★ 源站逐字（chunk）：`children:(0,i.jsx)(d.f,{className:"h-4 w-4 shrink-0","aria-hidden":!0})`
⟹ ⟹ 图标是 chunk 里的 `d.f`（某个 lucide 图标）⟹ ⟹ 必须把它的 path 取回来，
   不能拿 clone 现有的 `Grid3X3` 近似。

## 输出
  raw/source-862-frame-thirds-icon.json
"""
from __future__ import annotations

import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch862-2026-10-01"
RAW = BATCH / "raw"
COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

READ_SVG = r"""()=>{
  const btn=[...document.querySelectorAll('button')].find(b=>b.title==='构图参考线');
  if(!btn) return {找到:false};
  const svg=btn.querySelector('svg');
  return {找到:true,
          svgOuter: svg? svg.outerHTML : null,
          path: svg? [...svg.querySelectorAll('path,rect,circle,line')].map(n=>n.outerHTML) : [],
          attr: svg? [...svg.attributes].map(a=>a.name+'='+a.value) : [],
          btnHTML: btn.outerHTML.slice(0,600)};
}"""


def load_cookies(page) -> None:
    data = json.loads(COOKIE.read_text(encoding="utf-8"))
    cookies = data if isinstance(data, list) else data.get("cookies", [])
    page.context.add_cookies([
        {"name": c["name"], "value": c["value"], "domain": c["domain"],
         "path": c.get("path", "/")}
        for c in cookies if c.get("name")
    ])


def main() -> int:
    audit: dict = {"batch": 862, "probe": "source862_frame_thirds_icon"}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            load_cookies(page)
            page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(6_000)
            page.locator(".react-flow__node-director-console-3d").first.hover()
            page.wait_for_timeout(600)
            page.locator(".react-flow__node-director-console-3d "
                         "button:has-text('打开导演台')").first.click()
            page.wait_for_timeout(8_000)
            page.locator("[aria-label='选择画幅比例'], button:has-text('选择画幅比例')"
                         ).first.click(timeout=15_000)
            page.wait_for_timeout(1_500)
            page.locator("button:has-text('16:9')").first.click(timeout=15_000)
            page.wait_for_timeout(2_000)
            audit["关态"] = page.evaluate(READ_SVG)
        except Exception:
            audit["异常"] = traceback.format_exc()[-1500:]
        finally:
            browser.close()
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "source-862-frame-thirds-icon.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=1)[:3_500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
