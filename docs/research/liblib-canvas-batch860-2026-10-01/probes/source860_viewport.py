#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 860 源站探针 · 第二版（**只读**）：把「画布宽高比」这件事测准。

## ★ 为什么要有第二版

第一版（`source860_aspect.py`）读到一个**可疑模式**：
点「21:9」**之前**视口读数是 `null`，点**之后**才读到 1262×541（ratio **2.3334**
≈ 21:9 = 2.333）。

★ 但这**不能**直接当成「选比例后画布才出现」的结论 ⟹ ⟹ 因为第一版的读法是
「取面积最大的那个 div/canvas」⟹ ⟹ **它选中的元素可能每次都不是同一个**
⟹ ⟹ `null` 只说明「那一刻没有元素满足 `w>400 && h>200 && x>280`」，
**不说明**「画布不存在」。

⇒ ⇒ 第二版改成**枚举 + 分类**：把页面上所有够大的容器**全部**读出来，
带类名与矩形 ⟹ ⟹ 这样：
- 若「画布容器」在选比例前后**都**在（只是我之前没选对）⟹ ⟹ 结论是
  **「画布宽高比没变」**（那 2.3334 是别的东西）；
- 若它**选比例后才出现** ⟹ ⟹ 结论是「画布随比例而变」；
- 两种情况都能被**逐条读数**区分 ⟹ ⟹ 不再靠「null vs 有值」猜。

## ★ 副作用声明

同第一版：点「21:9」只改机位参数（不付费）；探针结束**点回「自适应」复原**；
★ **绝不点**「AI生成」。

## 输出
  raw/source-860-viewport.json
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

# ★ 枚举页面上所有「够大」的容器（带类名 ＋ 矩形 ＋ 纵横比）
#   ⟹ ⟹ 用来**逐条比对**而不是「取面积最大那个」。
READ_BIG = r"""()=>{
  const out=[];
  document.querySelectorAll('div,canvas,section,main,aside').forEach(e=>{
    const r=e.getBoundingClientRect();
    if(r.width<300||r.height<150) return;
    const cs=getComputedStyle(e);
    out.push({tag:e.tagName,
      cls:(e.className||'').toString().slice(0,110),
      x:Math.round(r.x), y:Math.round(r.y),
      w:Math.round(r.width), h:Math.round(r.height),
      ratio:+(r.width/r.height).toFixed(4),
      pos:cs.position, z:cs.zIndex,
      childCount:e.children.length,
      hasCanvas:!!e.querySelector(':scope > canvas'),
      text:(e.textContent||'').replace(/\s+/g,' ').trim().slice(0,26)});
  });
  // ★ 排序：面积降序 ⟹ ⟹ 读数稳定可逐条比
  out.sort((a,b)=>(b.w*b.h)-(a.w*a.h));
  return out.slice(0,26);
}"""

# ★ 源站逐字：`aspect_ratio` 事件是发给**机位**的 ⟹ ⟹ 那机位在 UI 上有什么表现？
#   ⟹ ⟹ 读所有**含比例文字**的元素（机位名/参数面板/预设列表…）
READ_CAMERA_HINTS = r"""()=>{
  const out=[];
  document.querySelectorAll('*').forEach(e=>{
    if(e.children.length>3) return;
    const t=(e.textContent||'').replace(/\s+/g,' ').trim();
    if(!t) return;
    if(!/21:9|16:9|9:16|4:3|3:4|1:1|画幅|比例|aspect/i.test(t)) return;
    const r=e.getBoundingClientRect();
    if(r.width<=0||r.height<=0) return;
    out.push({tag:e.tagName,
      cls:(e.className||'').toString().slice(0,110),
      text:t.slice(0,40),
      x:Math.round(r.x), y:Math.round(r.y),
      w:Math.round(r.width), h:Math.round(r.height)});
  });
  return out.slice(0,24);
}"""


def open_desk(page) -> None:
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(600)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')"
    ).first.click()
    page.wait_for_timeout(8_000)


def read_all(pg) -> dict:
    return {
        "大容器": pg.evaluate(READ_BIG),
        "比例相关": pg.evaluate(READ_CAMERA_HINTS),
    }


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

            # ── 切到画幅比例 ──
            btn = pg.locator("button[aria-label='选择画幅比例']").first
            btn.click(timeout=15_000)
            pg.wait_for_timeout(1_500)

            out["①基线（自适应）"] = read_all(pg)
            pg.screenshot(path=str(BATCH / "images/860src_vp_auto.png"))

            # ── 点 21:9 ──
            pg.locator("button", has_text="21:9").first.click(timeout=15_000)
            pg.wait_for_timeout(3_000)
            out["②点21比9后"] = read_all(pg)
            pg.screenshot(path=str(BATCH / "images/860src_vp_21x9.png"))

            # ── ★ 复原 ──
            pg.locator("button", has_text="自适应").first.click(timeout=15_000)
            pg.wait_for_timeout(3_000)
            out["③复原后"] = read_all(pg)

            pg.close()
            br.close()
    except Exception:  # noqa: BLE001
        out["★异常"] = traceback.format_exc()[-2500:]
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "source-860-viewport.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2)[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
