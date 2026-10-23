#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 858 定点归因：`626.py` 的 `side-panel-unhittable-row-is-the-timeline/
1280x540/add-character-panel` 这条红 ⟹ ⟹ 到底是被时间线盖住、还是别的。

## ★ 为什么要定点查

`626.py` 的 `side-panel-*` 那几条判据是**本批迁移时新增的**（原来量的是
「浮层」，现在量的是「左侧面板」）⟹ ⟹ 这条红**不是**老判据回归，
而是**新判据第一次亮红**⟹ ⟹ 必须查清「是 clone 的真缺陷」还是「判据本身写错了」。

★ 判据原文（`scripts/verify-liblib-batch626.py`）：

    v.check(f"side-panel-unhittable-row-is-the-timeline/{tag}",
            bool(row.get("coveredByTimeline")),
            f"timelineTop={row.get('timelineTop')}")

⟹ ⟹ 它断言的是：「几何模型」那一行点不到时，**必须**是**被时间线盖住**。
⟹ ⟹ 红的含义是：点不到，**但** `coveredByTimeline` ＝ False。

## ★ 本探针读什么（不猜，只读）

① 面板矩形、列表矩形、`scrollTop`／`scrollHeight`／`clientHeight`
② 「几何模型」那一行在**滚动前**与**滚动后**的矩形
③ 那一行中心点上**真正**是哪个元素（`document.elementFromPoint`）
④ 时间线矩形、视口尺寸
⑤ 点击失败时 Playwright 的**原文**异常

⟹ ⟹ 对照组：**1440×900**（绿）与 **1280×720**（绿）各读一遍 ⟹ ⟹
「只有 540 短视口才出问题」这个事实才立得住。

## 输出
  raw/attrib-626-1280x540.json
"""
from __future__ import annotations

import json
import pathlib

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch858-2026-10-01"
RAW = BATCH / "raw"
BASE = "http://localhost:4317"

READ = r"""()=>{
  const q=(s)=>document.querySelector(s);
  const rect=(e)=>{ if(!e) return null; const r=e.getBoundingClientRect();
    return {x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height),
            right:Math.round(r.right), bottom:Math.round(r.bottom)}; };
  const panel=q('[data-director-character-panel]');
  const row=q("[data-director-character-option='geometry']");
  const tl=q('[data-director-timeline]');
  const tlRect=tl?tl.getBoundingClientRect():null;
  let list=null;
  if(panel){
    list=[...panel.querySelectorAll('div')].find(d=>{
      const cs=getComputedStyle(d);
      return (cs.overflowY==='auto'||cs.overflowY==='scroll') &&
             d.contains(panel.querySelector("[data-director-character-option='geometry']"));
    });
  }
  const rr=row?row.getBoundingClientRect():null;
  let hit=null;
  if(rr){
    const cx=Math.round(rr.x+rr.width/2), cy=Math.round(rr.y+rr.height/2);
    const el=document.elementFromPoint(cx,cy);
    hit={cx,cy,
         tag:el?el.tagName:null,
         cls:el?(el.getAttribute('class')||'').slice(0,120):null,
         dataAttrs:el?[...el.attributes].filter(a=>a.name.startsWith('data-'))
                                .map(a=>a.name+'='+a.value).join(' '):null,
         isRowOrChild: el?(el===row||row.contains(el)):false,
         inViewport: cx>=0&&cx<=innerWidth&&cy>=0&&cy<=innerHeight};
  }
  const rows=[...document.querySelectorAll('[data-director-character-option]')].map(el=>{
    const r=el.getBoundingClientRect();
    return {id:el.getAttribute('data-director-character-option'),
            y:Math.round(r.y), bottom:Math.round(r.bottom)};
  });
  return {
    viewport:{w:innerWidth,h:innerHeight},
    panel:rect(panel),
    list:list?{rect:rect(list),scrollTop:Math.round(list.scrollTop),
               scrollHeight:list.scrollHeight,clientHeight:list.clientHeight,
               overflowY:getComputedStyle(list).overflowY}:null,
    geometryRow:rect(row),
    timeline:tlRect?{rect:rect(tl),z:getComputedStyle(tl).zIndex}:null,
    coveredByTimeline: !!(tlRect && rr && rr.bottom>tlRect.top && rr.top<tlRect.bottom),
    timelineTop:tlRect?Math.round(tlRect.top):null,
    elementAtGeometryCenter:hit,
    rows,
  };
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


def probe(pg, vw: int, vh: int) -> dict:
    out: dict = {"viewport": f"{vw}x{vh}"}
    pg.set_viewport_size({"width": vw, "height": vh})
    pg.wait_for_timeout(800)
    pg.locator("[data-director-rail-entry='add-character']").first.click(timeout=15000)
    pg.wait_for_timeout(700)
    out["①打开面板后"] = pg.evaluate(READ)

    row = pg.locator("[data-director-character-option='geometry']").first
    try:
        row.scroll_into_view_if_needed(timeout=8000)
        out["②滚动成功"] = True
    except Exception as exc:  # noqa: BLE001
        out["②滚动成功"] = False
        out["②滚动异常"] = f"{type(exc).__name__}: {str(exc)[:200]}"
    pg.wait_for_timeout(400)
    out["③滚动后"] = pg.evaluate(READ)

    try:
        row.click(timeout=10_000)
        pg.wait_for_timeout(600)
        out["④点击"] = "成功"
    except Exception as exc:  # noqa: BLE001
        out["④点击"] = "失败"
        out["④点击异常"] = f"{type(exc).__name__}: {str(exc)[:400]}"
    out["⑤点击后"] = pg.evaluate(READ)
    return out


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    result: dict = {"批次": 858, "探针": "attrib626", "说明":
                    "626 的 side-panel-unhittable-row-is-the-timeline/"
                    "1280x540/add-character-panel 这条红的定点归因"}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1280, "height": 540})
            open_desk(page)
            for vw, vh in [(1440, 900), (1280, 720), (1280, 540)]:
                result[f"视口 {vw}x{vh}"] = probe(page, vw, vh)
        finally:
            browser.close()
    (RAW / "attrib-626-1280x540.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    for key in ("视口 1440x900", "视口 1280x720", "视口 1280x540"):
        r = result.get(key, {})
        g = r.get("③滚动后", {})
        print(f"== {key}")
        print(f"   视口={g.get('viewport')}")
        print(f"   面板={g.get('panel')}")
        print(f"   列表={g.get('list')}")
        print(f"   几何行={g.get('geometryRow')}")
        print(f"   时间线={g.get('timeline')}")
        print(f"   coveredByTimeline={g.get('coveredByTimeline')}")
        print(f"   行中心命中={g.get('elementAtGeometryCenter')}")
        print(f"   点击={r.get('④点击')} {str(r.get('④点击异常'))[:200]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
