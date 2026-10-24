#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 859 clone 探针：量「全景图」「选择画幅比例」**面板模式**的逐段读数。

## ★ 本批的靶子（batch 858 登记的 D8）

源站逐字：左侧那个 232px 面板是**五模式互斥容器**
（`"scene"===z?n:null,"character"===z?(…),"camera"===z?(…),
"panorama"===z?(…),"aspect"===z?(…)`）
⟹ ⟹ **「全景图」「选择画幅比例」也是面板模式**，不是 rail 浮层。
⟹ ⟹ clone 此前把它们做成 **portal 浮层** ⟹ ⟹ 本批改成面板。

## ★ 期望值的出处（**不是 clone 自己算的**）

| 期望 | 出处 |
| --- | --- |
| 全景图：面板 @(48,52) 232 宽、标题条 232×48/12px、容器 `px-2` @(48,100) 232×96 | 源站实测 `raw/source-859-panels.json` 的 `④全景图面板` |
| 全景图：三行 @(56,100)/(56,132)/(56,164) 各 **216×32**、字号 **13px**、行高 **20px**、图标 **14×14** | 同上 |
| 全景图：三行文本逐字「本地上传」「历史记录」「AI生成」 | 同上 |
| 画幅比例：面板 @(48,52) 232 宽、标题条 232×48/12px | 源站实测 `⑤画幅比例面板` |
| 画幅比例：网格 @(48,100) 232×324、`104px 104px`、gap **8px**、padding `0px 8px 12px` | 同上 |
| 画幅比例：七格各 **104×72**、字号 **12px**、圆角 **12px**、边框 **1px**（选中 0.85／未选 0.1） | 同上 |

## ★ 还要证明的（结构事实，不是像素）

① 两个模式下**场景树不在场**（模式互斥）；
② **不再有**那两个 portal 浮层（`[data-director-panorama-flyout]` /
   `[data-director-aspect-flyout]` 必须为 0）；
③ rail 的 `aria-pressed` **跟着模式走**（源站逐字 `aria-pressed={z===r.id}`）；
④ 切走再切回，选中项**还在**（面板常驻挂载）。

## 输出
  raw/clone-859-panels.json
  images/859clone_panorama.png ／ 859clone_aspect.png
"""
from __future__ import annotations

import json
import pathlib

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch859-2026-10-01"
RAW = BATCH / "raw"
SHOTS = BATCH / "images"
BASE = "http://localhost:4317"

# ★ 源站实测的期望值（出处见上表）
SOURCE = {
    "panorama": {
        "panel": {"x": 48, "y": 52, "w": 232},
        "title": {"x": 48, "y": 52, "w": 232, "h": 48, "font": 12},
        "list": {"x": 48, "y": 100, "w": 232, "h": 96},
        "rows": [
            {"text": "本地上传", "x": 56, "y": 100, "w": 216, "h": 32},
            {"text": "历史记录", "x": 56, "y": 132, "w": 216, "h": 32},
            {"text": "AI生成", "x": 56, "y": 164, "w": 216, "h": 32},
        ],
        "row_font": 13,
        "row_line_height": 20,
        "icon": {"w": 14, "h": 14},
    },
    "aspect": {
        "panel": {"x": 48, "y": 52, "w": 232},
        "title": {"x": 48, "y": 52, "w": 232, "h": 48, "font": 12},
        "grid": {"x": 48, "y": 100, "w": 232, "h": 324},
        "columns": "104px 104px",
        "gap": 8,
        "cells": [
            {"text": "自适应", "x": 56, "y": 100, "w": 104, "h": 72},
            {"text": "21:9", "x": 168, "y": 100, "w": 104, "h": 72},
            {"text": "16:9", "x": 56, "y": 180, "w": 104, "h": 72},
            {"text": "4:3", "x": 168, "y": 180, "w": 104, "h": 72},
            {"text": "1:1", "x": 56, "y": 260, "w": 104, "h": 72},
            {"text": "3:4", "x": 168, "y": 260, "w": 104, "h": 72},
            {"text": "9:16", "x": 56, "y": 340, "w": 104, "h": 72},
        ],
        "cell_font": 12,
        "cell_radius": 12,
    },
}

# ★ 与源站探针**同口径**的读数（同样的 rect / font / lineHeight / border）
READ = r"""()=>{
  const rect=(e)=>{ if(!e) return null; const r=e.getBoundingClientRect();
    return {x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width),
            h:Math.round(r.height), right:Math.round(r.right),
            bottom:Math.round(r.bottom)}; };
  const vis=(e)=>{ if(!e) return false; const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0; };
  const panel=document.querySelector('[data-director-panorama-panel]');
  const aspect=document.querySelector('[data-director-aspect-panel]');
  const tree=document.querySelector('[data-director-tree]');
  const railBtns=[...document.querySelectorAll('[data-director-rail-entry]')].map(b=>({
    id:b.getAttribute('data-director-rail-entry'),
    pressed:b.getAttribute('aria-pressed'),
    label:b.getAttribute('aria-label')}));
  const out={
    rail:railBtns,
    treePresent: Boolean(tree && vis(tree)),
    oldPortalPanorama: document.querySelectorAll('[data-director-panorama-flyout]').length,
    oldPortalAspect: document.querySelectorAll('[data-director-aspect-flyout]').length,
    panorama:null, aspect:null,
  };
  if(panel && vis(panel)){
    const title=panel.querySelector('[data-director-panel-title="panorama"]');
    const list=panel.querySelector('[data-director-panorama-list]');
    const ts=title?getComputedStyle(title):null;
    out.panorama={
      panel:rect(panel),
      title:rect(title), titleText:title?(title.innerText||'').trim():null,
      titleFont:ts?ts.fontSize:null,
      listCls:list?(list.className||'').toString():null,
      list:rect(list),
      listPadding:list?getComputedStyle(list).padding:null,
      rows:[...panel.querySelectorAll('[data-director-panorama-option]')].map(e=>{
        const r=e.getBoundingClientRect();
        const cs=getComputedStyle(e);
        const sp=e.querySelector('span');
        const spc=sp?getComputedStyle(sp):null;
        const svg=e.querySelector('svg');
        const svr=svg?svg.getBoundingClientRect():null;
        return {text:(e.textContent||'').replace(/\s+/g,' ').trim(),
                x:Math.round(r.x), y:Math.round(r.y),
                w:Math.round(r.width), h:Math.round(r.height),
                fontSize:cs.fontSize, lineHeight:cs.lineHeight,
                spanFont:spc?spc.fontSize:null,
                spanLineHeight:spc?spc.lineHeight:null,
                spanText:sp?(sp.textContent||'').trim():null,
                icon: svr?{x:Math.round(svr.x),y:Math.round(svr.y),
                           w:Math.round(svr.width),h:Math.round(svr.height)}:null};
      }),
    };
  }
  if(aspect && vis(aspect)){
    const title=aspect.querySelector('[data-director-panel-title="aspect"]');
    const grid=aspect.querySelector('[data-director-aspect-grid]');
    const ts=title?getComputedStyle(title):null;
    const gs=grid?getComputedStyle(grid):null;
    out.aspect={
      panel:rect(aspect),
      title:rect(title), titleText:title?(title.innerText||'').trim():null,
      titleFont:ts?ts.fontSize:null,
      gridCls:grid?(grid.className||'').toString():null,
      grid:rect(grid),
      gridTemplateColumns:gs?gs.gridTemplateColumns:null,
      columnGap:gs?gs.columnGap:null, rowGap:gs?gs.rowGap:null,
      padding:gs?gs.padding:null,
      cells:[...aspect.querySelectorAll('[data-director-aspect-option]')].map(e=>{
        const r=e.getBoundingClientRect();
        const cs=getComputedStyle(e);
        const g=e.querySelector('[data-director-aspect-glyph]');
        const gr=g?g.getBoundingClientRect():null;
        return {text:(e.textContent||'').replace(/\s+/g,' ').trim(),
                x:Math.round(r.x), y:Math.round(r.y),
                w:Math.round(r.width), h:Math.round(r.height),
                fontSize:cs.fontSize,
                borderColor:cs.borderColor, borderWidth:cs.borderWidth,
                borderRadius:cs.borderRadius,
                pressed:e.getAttribute('aria-pressed'),
                glyph: gr?{w:Math.round(gr.width),h:Math.round(gr.height)}:null};
      }),
    };
  }
  return out;
}"""


def open_desk(pg) -> None:
    pg.goto(BASE + "/", wait_until="domcontentloaded")
    pg.wait_for_timeout(3000)
    pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
    pg.wait_for_function("() => Boolean(window.__director_store)", timeout=90_000)
    pg.wait_for_timeout(1500)
    node = pg.locator(".react-flow__node-script-execution").first
    try:
        node.scroll_into_view_if_needed(timeout=8000)
    except Exception:  # noqa: BLE001
        pass
    pg.wait_for_timeout(400)
    try:
        node.hover(timeout=8000)
        pg.wait_for_timeout(600)
    except Exception:  # noqa: BLE001
        pass
    pg.locator("[data-open-director]").first.click(timeout=15000)
    pg.wait_for_timeout(6500)
    pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")


def main() -> int:
    out: dict = {"批次": 859, "探针": "clone859_panels", "源站期望": SOURCE}
    RAW.mkdir(parents=True, exist_ok=True)
    SHOTS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            open_desk(page)
            out["①打开导演台"] = "OK"

            # ── 全景图 ──
            page.locator("[data-director-rail-entry='panorama']").first.click(timeout=15000)
            page.wait_for_timeout(700)
            out["②全景图面板"] = page.evaluate(READ)
            page.screenshot(path=str(SHOTS / "859clone_panorama.png"))

            # ── 画幅比例 ──
            page.locator("[data-director-rail-entry='aspect-ratio']").first.click(timeout=15000)
            page.wait_for_timeout(700)
            out["③画幅比例面板"] = page.evaluate(READ)
            page.screenshot(path=str(SHOTS / "859clone_aspect.png"))

            # ── 选一格再切走再切回 ⟹ 选中项还在（面板常驻挂载）──
            page.locator("[data-director-aspect-option='16:9']").first.click(timeout=15000)
            page.wait_for_timeout(400)
            page.locator("[data-director-rail-entry='scene']").first.click(timeout=15000)
            page.wait_for_timeout(500)
            page.locator("[data-director-rail-entry='aspect-ratio']").first.click(timeout=15000)
            page.wait_for_timeout(700)
            out["④切走再切回"] = page.evaluate(READ)
        finally:
            browser.close()
    (RAW / "clone-859-panels.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for key in ("②全景图面板", "③画幅比例面板"):
        r = out.get(key, {})
        print(f"== {key}")
        print(f"   场景树在场={r.get('treePresent')} ｜ 旧浮层 panorama={r.get('oldPortalPanorama')} aspect={r.get('oldPortalAspect')}")
        print(f"   rail pressed={[(b['id'], b['pressed']) for b in r.get('rail', [])]}")
        p = r.get("panorama")
        if p:
            print(f"   全景图 面板={p.get('panel')} 标题={p.get('title')} {p.get('titleText')!r} {p.get('titleFont')}")
            print(f"   全景图 容器={p.get('list')} cls={p.get('listCls')!r} pad={p.get('listPadding')}")
            for row in p.get("rows", []):
                print(f"      行 {row['text']!r} @({row['x']},{row['y']}) {row['w']}x{row['h']} "
                      f"font={row['fontSize']}/{row['lineHeight']} icon={row['icon']}")
        a = r.get("aspect")
        if a:
            print(f"   画幅 面板={a.get('panel')} 标题={a.get('title')} {a.get('titleText')!r} {a.get('titleFont')}")
            print(f"   画幅 网格={a.get('grid')} cols={a.get('gridTemplateColumns')} "
                  f"gap={a.get('columnGap')}/{a.get('rowGap')} pad={a.get('padding')}")
            for c in a.get("cells", []):
                print(f"      格 {c['text']!r} @({c['x']},{c['y']}) {c['w']}x{c['h']} "
                      f"font={c['fontSize']} 边={c['borderColor']}/{c['borderWidth']} "
                      f"圆角={c['borderRadius']} pressed={c['pressed']} glyph={c['glyph']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
