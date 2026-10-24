#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 860 源站探针 · 第四版：查两件事。

① ★ 源站**视口底部**有没有 clone 那组三枚比例按钮（`16:9`／`9:16`／`1:1`）？
   ⟹ ⟹ clone 底部那组是**clone 自己的扩展**还是源站逐字？
② ★ 源站**视口底部**整体有哪些控件（`aria-label` ＋ 文本 ＋ 位置）？
   ⟹ ⟹ 用它来决定 clone 底部那组该怎么处理。

## ★ 为什么要查

clone 视口底部有一组 `data-director-aspect` 的三枚比例按钮（`16:9`／`9:16`／`1:1`），
它驱动的是**导出比例**（`state.aspectRatio`）。
而源站的画幅比例在**左侧面板七格**里（batch 859 已对齐），
且源站把比例**发给机位**当**取景比例**（batch 860 实测）。

⟹ ⟹ 所以要先确认：clone 底部那组按钮，源站有没有？
   - 若**有** ⟹ ⟹ 它也该驱动取景比例；
   - 若**没有** ⟹ ⟹ 它是 clone 自己的扩展 ⟹ ⟹ 要么保留（明确标注是扩展），
     要么并入七格。⟹ ⟹ **不能擅自删用户可见的功能** ⟹ ⟹ 本批只做「不冲突」。

## ★ 副作用声明

只读（不点任何按钮）⟹ ⟹ 无副作用。

## 输出
  raw/source-860-bottombar.json
"""
from __future__ import annotations

import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch860-2026-10-01"
RAW = BATCH / "raw"

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 视口底部一带的控件（y > 视口高的 88%）
READ_BOTTOM = r"""()=>{
  const H=window.innerHeight;
  const out=[];
  document.querySelectorAll('button,[role="button"],input,select').forEach(e=>{
    const r=e.getBoundingClientRect();
    if(r.width<=0||r.height<=0) return;
    if(r.y < H*0.86) return;          // ★ 只要底部 14%
    out.push({tag:e.tagName,
      aria:e.getAttribute('aria-label')||'',
      title:e.getAttribute('title')||'',
      pressed:e.getAttribute('aria-pressed'),
      text:(e.textContent||'').replace(/\s+/g,' ').trim().slice(0,24),
      x:Math.round(r.x), y:Math.round(r.y),
      w:Math.round(r.width), h:Math.round(r.height),
      cls:(e.className||'').toString().slice(0,90)});
  });
  out.sort((a,b)=>a.x-b.x);
  return {视口高:H, 控件:out};
}"""


def open_desk(page) -> None:
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(600)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')"
    ).first.click()
    page.wait_for_timeout(8_000)


def main() -> int:
    out: dict = {}
    try:
        cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            ctx.add_cookies([{"name": c["name"], "value": c["value"],
                              "domain": c["domain"], "path": c.get("path", "/")}
                             for c in cookies])
            pg = ctx.new_page()
            pg.set_default_timeout(20_000)
            pg.goto(URL, wait_until="domcontentloaded", timeout=90_000)
            pg.wait_for_timeout(12_000)
            el = pg.query_selector("text=下次再说")
            if el:
                el.click()
                pg.wait_for_timeout(900)
            open_desk(pg)
            if pg.query_selector("[data-director-practice-escape]"):
                pg.keyboard.press("Escape")
                pg.wait_for_timeout(900)
            out["①底部控件"] = pg.evaluate(READ_BOTTOM)
            pg.screenshot(path=str(BATCH / "images/860src_bottombar.png"))
            pg.close()
            br.close()
    except Exception:  # noqa: BLE001
        out["★异常"] = traceback.format_exc()[-2500:]
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "source-860-bottombar.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2)[:6000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
