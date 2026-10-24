#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 860 clone 探针：量 clone 的「机位取景框」在七档比例下**各自的矩形**。

## ★ 靶子（batch 859 登记的 D11，本批实测后**结论反转**）

★ 源站实测（`raw/source-860-viewport.json`）**钉死**的事实：

| | 基线（自适应） | 点「21:9」后 | 复原后 |
|---|---|---|---|
| 画布容器 `h-full w-full` | 1920×1080 (1.7778) | **1920×1080 (1.7778)** | 1920×1080 |
| `react-flow__viewport` | 732×411 (1.7778) | **732×411 (1.7778)** | 732×411 |
| 机位取景框 | **不在场** | **@(329,270) 1262×541（ratio 2.3334 ≈ 21:9）** | 不在场 |

⟹ ⟹ ★ **源站选比例【不改画布】** ⟹ ⟹ 它改的是**机位取景框**。
⟹ ⟹ ★ 所以 batch 859 登记的 D11（「clone 不改画布宽高比」）**说法是错的**：
   源站本来就不改画布 ⟹ ⟹ 真正的差异是：
   ★ **clone 的取景框只支持三档**（`16:9`／`9:16`／`1:1`），
   源站支持**七档数值比例**（21:9／16:9／4:3／1:1／3:4／9:16／自适应）。

## ★ clone 现状（要拿实测去对）

`src/components/director/directorViewportMath.ts`：
- `getDirectorAspectValue(ratio)` ⟹ ⟹ 只认 `"9:16"`／`"1:1"`，其余一律 **16/9**；
- `getDirectorFrameRect(w, h, ratio)` ⟹ ⟹ 按比例算框、居中、受 padding 约束；
- `DirectorViewport.tsx` 的 `AspectFrame` ⟹ ⟹ 读 `state.aspectRatio` 画框
  （`data-director-aspect-frame` ＋ `data-director-aspect-ratio`）。

## ★ 本探针要读到的

① 七档比例**逐档**的取景框矩形（`[data-director-aspect-frame]`）；
② 取景框上标的 `data-director-aspect-ratio`；
③ ★ **画布容器**在三态下**恒定**（源站同款 ⟹ ⟹ clone 也必须恒定）；
④ ★ 「自适应」在 clone 里对应哪一档（源站＝**无框**）；
⑤ 页面无诊断错误。

## 输出
  raw/clone-860-aspect.json
"""
from __future__ import annotations

import json
import pathlib

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch860-2026-10-01"
RAW = BATCH / "raw"
BASE = "http://localhost:4317"

# ★ 源站实测的期望值（出处见上表）
SOURCE_FRAME_21_9 = {"x": 329, "y": 270, "w": 1262, "h": 541, "ratio": 2.3334}
SOURCE_CANVAS = {"w": 1920, "h": 1080, "ratio": 1.7778}
SOURCE_VIEWPORT = {"w": 732, "h": 411, "ratio": 1.7778}
SOURCE_RATIOS = [
    ("自适应", None),
    ("21:9", 21 / 9),
    ("16:9", 16 / 9),
    ("4:3", 4 / 3),
    ("1:1", 1),
    ("3:4", 3 / 4),
    ("9:16", 9 / 16),
]

READ = r"""()=>{
  const rect=(e)=>{ if(!e) return null; const r=e.getBoundingClientRect();
    return {x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width),
            h:Math.round(r.height),
            ratio: r.height>0 ? +(r.width/r.height).toFixed(4) : null}; };
  const q=(s)=>document.querySelector(s);
  const frame=q('[data-director-aspect-frame]');
  const canvasBox=[...document.querySelectorAll('div')].find(e=>{
    const c=(e.className||'').toString().trim();
    return c==='h-full w-full' && e.querySelector('canvas');
  });
  const flowVp=q('.react-flow__viewport');
  return {
    取景框: frame?rect(frame):null,
    取景框比例标记: frame?frame.getAttribute('data-director-aspect-ratio'):null,
    取景框类名: frame?(frame.className||'').toString().slice(0,160):null,
    画布容器: canvasBox?rect(canvasBox):null,
    reactflow视口: flowVp?rect(flowVp):null,
    当前模式: (q('[data-director-left-panel-view]')||{getAttribute:()=>null})
      .getAttribute('data-director-left-panel-view'),
    画幅格: [...document.querySelectorAll('[data-director-aspect-option]')].map(e=>({
      text:(e.textContent||'').replace(/\s+/g,' ').trim(),
      pressed:e.getAttribute('aria-pressed')})),
  };
}"""


def open_desk(page) -> None:
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    page.evaluate(
        "() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
    page.wait_for_function("() => Boolean(window.__director_store)", timeout=90_000)
    page.wait_for_timeout(1500)
    node = page.locator(".react-flow__node-script-execution").first
    try:
        node.scroll_into_view_if_needed(timeout=8000)
    except Exception:  # noqa: BLE001
        pass
    page.wait_for_timeout(400)
    try:
        node.hover(timeout=8000)
        page.wait_for_timeout(600)
    except Exception:  # noqa: BLE001
        pass
    page.locator("[data-open-director]").first.click(timeout=15000)
    page.wait_for_timeout(6500)
    page.evaluate(
        "() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")


def main() -> int:
    out: dict = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080},
                                    device_scale_factor=1)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text)
                    if m.type == "error" else None)
            open_desk(page)
            page.locator("[data-director-rail-entry='aspect-ratio']").first.click(
                timeout=15000)
            page.wait_for_timeout(800)

            out["画幅格"] = page.evaluate(READ)["画幅格"]
            # ★ 逐档点一遍，逐档读取景框
            per_ratio: dict[str, object] = {}
            for label, expect in SOURCE_RATIOS:
                page.locator(f"[data-director-aspect-option='{label}']").first.click(
                    timeout=15000)
                page.wait_for_timeout(700)
                r = page.evaluate(READ)
                per_ratio[label] = {
                    "期望比例": expect,
                    "取景框": r["取景框"],
                    "取景框比例标记": r["取景框比例标记"],
                    "画布容器": r["画布容器"],
                    "reactflow视口": r["reactflow视口"],
                }
            out["逐档"] = per_ratio
            out["错误"] = [e for e in errors if "TransformControls" not in e][:8]
        finally:
            browser.close()
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "clone-860-aspect.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1)[:6000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
