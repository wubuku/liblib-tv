#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 863 源站探针：取景框**框外遮罩**的逐字与运行时读数。

## ★ 靶子

★ 源站逐字（chunk 的 `mP` 组件）：

```js
(0,i.jsx)("div",{className:"absolute inset-0 bg-black/20 backdrop-blur-md",
  style:{WebkitMaskImage:"linear-gradient(#000 0 0), linear-gradient(#000 0 0)",
         WebkitMaskPosition:`0 0, ${u.left}px ${u.top}px`,
         WebkitMaskRepeat:"no-repeat, no-repeat",
         WebkitMaskSize:`100% 100%, ${u.width}px ${u.height}px`,
         WebkitMaskComposite:"xor", maskComposite:"exclude"}})
```

⟹ ⟹ 源站的框外是**一个铺满的遮罩层**：黑 20% ＋ **backdrop-blur**，
  用 **CSS mask** 把**框那块**挖空（`mask-composite: exclude`）。

★ clone（本批之前）：`shadow-[0_0_0_9999px_rgba(0,0,0,0.24)]`
  ⟹ ⟹ 框外变暗 **24%**、**没有模糊** ⟹ ⟹ 与源站不同（登记 D20）。

## ★ 本探针要读到的
① 遮罩层的**计算样式**：背景色、backdrop-filter、mask 图像／位置／尺寸／合成；
② 遮罩层与框的**几何**关系（遮罩铺满哪个容器）；
③ ★ **像素对照**：框外一点 vs 框内一点的亮度差（证明框外确实被压暗）
   ＋ 框内一点 vs 框外一点的**清晰度**差（blur 的直接证据：同一块 3D 内容的
   边缘对比度在框外更低）。

## ★ 副作用声明

★ 只点「画幅比例」⟹ ⟹ 本地视图态；**绝不点**「AI生成」「本地上传」「截图」。

## 输出
  raw/source-863-frame-mask.json
"""
from __future__ import annotations

import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch863-2026-10-01"
RAW = BATCH / "raw"
COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 读遮罩层：源站逐字 `absolute inset-0 bg-black/20 backdrop-blur-md`
READ_MASK = r"""()=>{
  const layers=[...document.querySelectorAll('div')].filter(e=>{
    const c=e.getAttribute('class')||'';
    return c.includes('backdrop-blur') && c.includes('absolute');
  });
  const out=[];
  for(const e of layers){
    const cs=getComputedStyle(e);
    const r=e.getBoundingClientRect();
    out.push({
      cls:(e.getAttribute('class')||''),
      rect:{x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)},
      backgroundColor:cs.backgroundColor,
      backdropFilter:cs.backdropFilter,
      webkitBackdropFilter:cs.webkitBackdropFilter,
      maskImage:cs.maskImage, webkitMaskImage:cs.webkitMaskImage,
      maskComposite:cs.maskComposite, webkitMaskComposite:cs.webkitMaskComposite,
      maskPosition:cs.maskPosition, webkitMaskPosition:cs.webkitMaskPosition,
      maskSize:cs.maskSize, webkitMaskSize:cs.webkitMaskSize,
      maskRepeat:cs.maskRepeat, webkitMaskRepeat:cs.webkitMaskRepeat,
      inlineStyle:e.getAttribute('style')||'',
    });
  }
  return out;
}"""

# ★ 读框（描边那层）
READ_FRAME = r"""()=>{
  const f=[...document.querySelectorAll('div')].find(e=>{
    const c=e.getAttribute('class')||'';
    return c.includes('outline-white/18') && c.includes('rounded-xl');
  });
  if(!f) return {框在场:false};
  const r=f.getBoundingClientRect();
  return {框在场:true, rect:{x:Math.round(r.x),y:Math.round(r.y),
                             w:Math.round(r.width),h:Math.round(r.height)}};
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
    audit: dict = {"batch": 863, "probe": "source863_frame_mask"}
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
            page.wait_for_timeout(2_500)

            audit["框"] = page.evaluate(READ_FRAME)
            audit["遮罩层"] = page.evaluate(READ_MASK)

            # ★ 像素对照：框上边缘两侧各取一小块，比亮度与清晰度
            frame = (audit.get("框") or {}).get("rect") or {}
            if frame:
                fx, fy = frame["x"], frame["y"]
                # 框内一点（往下 40px）与框外一点（往上 40px）
                inside = {"x": fx + 120, "y": fy + 60}
                outside = {"x": fx + 120, "y": max(2, fy - 30)}
                audit["像素对照"] = {
                    "inside": inside, "outside": outside,
                    "说明": "★ 框外应被黑 20% 压暗；框内被 mask 挖空 ⟹ 不受影响",
                }
                buf_in = page.screenshot(clip={"x": inside["x"], "y": inside["y"],
                                               "width": 64, "height": 64})
                buf_out = page.screenshot(clip={"x": outside["x"], "y": outside["y"],
                                                "width": 64, "height": 64})
                audit["像素对照"]["insidePng"] = len(buf_in)
                audit["像素对照"]["outsidePng"] = len(buf_out)
                (RAW).mkdir(parents=True, exist_ok=True)
                (RAW / "source-863-inside.png").write_bytes(buf_in)
                (RAW / "source-863-outside.png").write_bytes(buf_out)
        except Exception:
            audit["异常"] = traceback.format_exc()[-2000:]
        finally:
            browser.close()

    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "source-863-frame-mask.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=1)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
