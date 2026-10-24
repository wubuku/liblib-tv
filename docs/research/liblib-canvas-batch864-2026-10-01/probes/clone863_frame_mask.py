#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 863 clone 探针：取景框**框外遮罩**的读数（改前/改后同一口径）。

## ★★ Batch 864：**从 863 原样拷贝**而来，只改了**一处**——输出目录

- 拷贝自 `docs/research/liblib-canvas-batch863-2026-10-01/probes/clone863_frame_mask.py`
  （探针逻辑**一字未改** ⟹ ⟹ 读数与 863 **同口径**、可比）；
- 唯一的改动：`BATCH` 从 `…-batch863-…` 改指 `…-batch864-…`
  ⟹ ⟹ 产物落进**本批**的 `raw/`，**不再动 863 已提交的产物**；
- ★ 本批用它做**受控对照的同口径读数**（HEAD 态 vs WORK 态）：
  探针第 ④ 项会读那枚「构图参考线」开关
  ⟹ ⟹ HEAD 态（坐标控件 `z-20`）开关**被盖住**、WORK 态（`z-10`）**可点**。

## ★ 判据（源站逐字，chunk `mP` 组件）

```js
(0,i.jsx)("div",{className:"absolute inset-0 bg-black/20 backdrop-blur-md",
  style:{WebkitMaskImage:"linear-gradient(#000 0 0), linear-gradient(#000 0 0)",
         WebkitMaskPosition:`0 0, ${u.left}px ${u.top}px`,
         WebkitMaskRepeat:"no-repeat, no-repeat",
         WebkitMaskSize:`100% 100%, ${u.width}px ${u.height}px`,
         WebkitMaskComposite:"xor", maskComposite:"exclude"}})
```

★ 源站逐字的外层容器：`pointer-events-none absolute bottom-0 left-0 right-0 top-0 z-10`

## ★ 本探针要读到的（★ 前后同一口径）

① 遮罩层：背景色（黑 **20%**）、`backdrop-filter`（**含 blur**）、
   mask 图像／位置／尺寸／合成（**exclude**）；
② 遮罩层**铺满**视口容器（不是只跟框一样大）；
③ ★ **像素对照**：框内一点 vs 框外一点的亮度差
   ⟹ ⟹ 框外应被压暗 **20%**、框内**不受影响**（mask 挖空）；
④ 框的描边／圆角／分线／开关（回归，确认没被改坏）。

## 输出
  raw/clone-863-frame-mask.json
"""
from __future__ import annotations

import json
import pathlib

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch864-2026-10-01"
RAW = BATCH / "raw"
BASE = "http://localhost:4317"

READ = r"""()=>{
  const f=document.querySelector('[data-director-aspect-frame]');
  const btn=document.querySelector('[data-director-frame-thirds-toggle]');
  const out={框在场:!!f, 开关在场:!!btn};
  // ★ 遮罩层：源站逐字 `absolute inset-0 bg-black/20 backdrop-blur-md`
  const layers=[...document.querySelectorAll('div')].filter(e=>{
    const c=e.getAttribute('class')||'';
    return c.includes('backdrop-blur') && c.includes('absolute');
  });
  out.遮罩层=layers.map(e=>{
    const cs=getComputedStyle(e); const r=e.getBoundingClientRect();
    return {cls:(e.getAttribute('class')||''),
            rect:{x:Math.round(r.x),y:Math.round(r.y),
                  w:Math.round(r.width),h:Math.round(r.height)},
            backgroundColor:cs.backgroundColor,
            backdropFilter:cs.backdropFilter,
            webkitBackdropFilter:cs.webkitBackdropFilter,
            maskImage:cs.maskImage, webkitMaskImage:cs.webkitMaskImage,
            maskComposite:cs.maskComposite,
            webkitMaskComposite:cs.webkitMaskComposite,
            maskPosition:cs.maskPosition, maskSize:cs.maskSize,
            maskRepeat:cs.maskRepeat,
            pointerEvents:cs.pointerEvents, zIndex:cs.zIndex};
  });
  // ★ ★ 旧实现是「box-shadow 撑出 9999px 遮罩」⟹ ⟹ 一并读出来做前后对照
  if(f){
    const r=f.getBoundingClientRect(); const cs=getComputedStyle(f);
    out.框={x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};
    out.框样式={boxShadow:cs.boxShadow, border:cs.borderTopWidth,
                outline:cs.outlineWidth+' '+cs.outlineColor+' '+cs.outlineOffset,
                radius:cs.borderRadius, pointerEvents:cs.pointerEvents};
  }
  out.分线条数=document.querySelectorAll('[data-director-thirds] span').length;
  // ★ ★ **可见性检查**：★ 遮罩层/框带 `z-10` ⟹ ⟹ 万一被 3D canvas 盖住，
  //   几何读数仍然「正常」⟹ ⟹ 几何读数**证明不了可见**。
  //   ⟹ ⟹ 用 `elementFromPoint` 看**最顶层**是谁：
  //   · 框的左上角（框内 1px）⟹ 期望是框自己（或它的子元素）
  //   · 框外一点 ⟹ 期望是遮罩层（或它的子元素）
  const hit=(x,y)=>{const e=document.elementFromPoint(x,y);
    if(!e) return null;
    return {tag:e.tagName,
            cls:(e.getAttribute('class')||'').slice(0,70),
            isFrame:!!e.closest('[data-director-aspect-frame]'),
            isMask:!!e.closest('[data-director-aspect-mask]'),
            isCanvas:!!e.closest('canvas')};};
  const fr=out.框;
  out.命中测试 = fr ? {
    框角: hit(fr.x+1, fr.y+1),
    框内: hit(fr.x+Math.round(fr.w/2), fr.y+Math.round(fr.h/2)),
    框外上: hit(fr.x+Math.round(fr.w/2), Math.max(2, fr.y-30)),
  } : null;
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


def _pixels(png: bytes):
    from PIL import Image
    import io
    im = Image.open(io.BytesIO(png)).convert("RGB")
    return list(im.getdata())


def mean_luma(png: bytes) -> float:
    px = _pixels(png)
    return sum(0.2126 * r + 0.7152 * g + 0.0722 * b for r, g, b in px) / max(1, len(px))


def mean_rgb(png: bytes) -> dict:
    """★ 红色探针只要 **R 通道** 的均值（其余通道只作参考）。

    ⟹ ⟹ 判据用「框外 R − 框内 R」这个**差** ⟹ ⟹ 3D 场景在动也不影响
    ⟹ ⟹ 因为红色是探针**自己**染上去的、红通道的抬升是**确定性的**。
    """
    px = _pixels(png)
    n = max(1, len(px))
    return {
        "R": round(sum(r for r, _g, _b in px) / n, 2),
        "G": round(sum(g for _r, g, _b in px) / n, 2),
        "B": round(sum(b for _r, _g, b in px) / n, 2),
        "样本数": len(px),
    }


def main() -> int:
    out: dict = {"batch": 863, "probe": "clone863_frame_mask"}
    RAW.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080},
                                    device_scale_factor=1)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            open_desk(page)
            page.locator("[data-director-rail-entry='aspect-ratio']").first.click(
                timeout=15000)
            page.wait_for_timeout(900)
            page.locator("[data-director-aspect-option='16:9']").first.click(timeout=8000)
            page.wait_for_timeout(1200)

            out["读数"] = page.evaluate(READ)
            frame = (out["读数"].get("框") or {})
            if frame:
                # ★ ★★ **红色探针**：★ 直接证明 **mask 真的把框那块挖空了**。
                #   ★ 为什么不用「框内/框外亮度比」：★ 3D 场景**一直在动** ⟹ ⟹
                #   两次截图的内容不同 ⟹ ⟹ 亮度比**不稳定**（实测 0.87/0.90 漂移）⟹ ⟹
                #   只能当参考、不能当判据。
                #   ★ 红色探针是**确定性**的：★ 把遮罩层临时染成红 ⟹ ⟹
                #   框外**必须是红的**、框内**必须不是红的**（被 mask 挖空）。
                page.evaluate(
                    "() => { const m=document.querySelector"
                    "('[data-director-aspect-mask]');"
                    "if(m) m.style.backgroundColor='rgba(255,0,0,0.85)'; }"
                )
                page.wait_for_timeout(600)
                fx, fy = frame["x"], frame["y"]
                inside = {"x": fx + 150, "y": fy + 70}
                outside = {"x": fx + 150, "y": max(2, fy - 30)}
                buf_in = page.screenshot(clip={"x": inside["x"], "y": inside["y"],
                                               "width": 48, "height": 48})
                buf_out = page.screenshot(clip={"x": outside["x"], "y": outside["y"],
                                                "width": 48, "height": 48})
                (RAW / "clone-863-redprobe-inside.png").write_bytes(buf_in)
                (RAW / "clone-863-redprobe-outside.png").write_bytes(buf_out)
                out["红色探针"] = {
                    "框内": mean_rgb(buf_in),
                    "框外": mean_rgb(buf_out),
                    "说明": "★ 框外 R 明显高（被染红）⟹ ⟹ 框内 R 低 ⟹ ⟹ mask 挖空生效",
                }
                # ⟹ 还原（别把红色留在页面上）
                page.evaluate(
                    "() => { const m=document.querySelector"
                    "('[data-director-aspect-mask]');"
                    "if(m) m.style.backgroundColor=''; }"
                )
                page.wait_for_timeout(400)

                # ★ 框内一点 vs 框外一点的亮度（**只作参考**，3D 在动）
                buf_in2 = page.screenshot(clip={"x": inside["x"], "y": inside["y"],
                                                "width": 48, "height": 48})
                buf_out2 = page.screenshot(clip={"x": outside["x"], "y": outside["y"],
                                                 "width": 48, "height": 48})
                # ★ 把这两张「亮度参考取样」也落盘 ⟹ ⟹ 目录里的截图与产物**一一对应**
                (RAW / "clone-863-inside.png").write_bytes(buf_in2)
                (RAW / "clone-863-outside.png").write_bytes(buf_out2)
                li, lo = mean_luma(buf_in2), mean_luma(buf_out2)
                out["像素对照"] = {"inside": inside, "outside": outside,
                                  "框内平均亮度": round(li, 2),
                                  "框外平均亮度": round(lo, 2),
                                  "比值_框外除以框内": round(lo / li, 4) if li else None,
                                  "★说明": "★ 只作参考（3D 场景在动 ⟹ ⟹ 数值会漂移）"}
            out["错误"] = [e for e in errors if "TransformControls" not in e][:8]
        except Exception as e:
            out["异常"] = str(e)[:800]
        finally:
            browser.close()
    (RAW / "clone-863-frame-mask.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1)[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
