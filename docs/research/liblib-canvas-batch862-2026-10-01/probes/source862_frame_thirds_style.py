#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 862 源站探针（补）：取景框 + 构图参考线开关的**计算样式**（同口径）。

★ 为什么需要这一步
─────────────────
★ 源站把颜色写成 Tailwind 的 **CSS 变量类**（`bg-(--color-white-alpha-50)`、
  `bg-(--btn-secondary-bg)`、`text-btn-primary`）⟹ ⟹ `getComputedStyle` 读回来
  是 `lab(...)`／`oklab(...)` **函数值**（例：`lab(100 -0.0000298 0.0000119 / 0.18)`），
  而 clone 那边是 `rgba(255,255,255,0.18)` ⟹ ⟹ **两边字符串不可能逐字相等**。
★ ⇒ ⟹ 必须**归一化成同一口径**（RGBA 数值）才能比 ⟹ ⟹ 这里用 **canvas 画一遍
  再读像素**（浏览器会把任意颜色语法解析成像素）。

## ★ 读到的
① 框：outline 宽度／偏移／圆角／border 宽度 ＋ **归一化后的描边色**；
② 三分线（点开关后）：4 条的 **归一化背景色**；
③ 开关按钮：开启态的 **归一化前景色** ＋ **归一化背景色** ＋ 位置／z-index。

## 输出
  raw/source-862-frame-thirds-style.json
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

# ★ 把任意颜色语法归一化成 RGBA（canvas 画一遍再读像素）
NORM = r"""(c)=>{
  const cv=document.createElement('canvas'); cv.width=8; cv.height=8;
  const ctx=cv.getContext('2d');
  ctx.clearRect(0,0,8,8);
  ctx.fillStyle='#000';
  ctx.fillStyle=c;           // ★ 非法值时 fillStyle 保持上一次（'#000'）
  ctx.fillRect(0,0,8,8);
  const d=ctx.getImageData(4,4,1,1).data;
  return {raw:c, rgba:[d[0],d[1],d[2],d[3]]};
}"""

READ_FRAME_STYLE = r"""()=>{
  const f=[...document.querySelectorAll('div')].find(e=>{
    const c=e.getAttribute('class')||'';
    return c.includes('outline-white/18') && c.includes('rounded-xl');
  });
  if(!f) return {框在场:false};
  const cs=getComputedStyle(f);
  const r=f.getBoundingClientRect();
  return {框在场:true,
          rect:{x:Math.round(r.x),y:Math.round(r.y),
                w:Math.round(r.width),h:Math.round(r.height)},
          outlineWidth:cs.outlineWidth, outlineStyle:cs.outlineStyle,
          outlineOffset:cs.outlineOffset, outlineColor:cs.outlineColor,
          borderWidth:cs.borderTopWidth, borderColor:cs.borderTopColor,
          borderRadius:cs.borderRadius,
          遮罩兄弟:[...f.parentElement.children].map(e=>{
            const c=e.getAttribute('class')||'';
            return {cls:c.slice(0,90)};
          })};
}"""

READ_BTN_STYLE = r"""()=>{
  const b=[...document.querySelectorAll('button')].find(x=>x.title==='构图参考线');
  if(!b) return {按钮在场:false};
  const cs=getComputedStyle(b); const r=b.getBoundingClientRect();
  return {按钮在场:true,
          rect:{x:Math.round(r.x),y:Math.round(r.y),
                w:Math.round(r.width),h:Math.round(r.height)},
          color:cs.color, backgroundColor:cs.backgroundColor,
          position:cs.position, pointerEvents:cs.pointerEvents, zIndex:cs.zIndex,
          borderRadius:cs.borderRadius};
}"""

READ_LINES = r"""()=>{
  const lines=[...document.querySelectorAll('div')].filter(e=>{
    const c=e.getAttribute('class')||'';
    return c.includes('--color-white-alpha-50');
  });
  return {条数:lines.length,
          背景色:lines.map(e=>getComputedStyle(e).backgroundColor),
          类名:lines.map(e=>(e.getAttribute('class')||''))};
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
    audit: dict = {"batch": 862, "probe": "source862_frame_thirds_style"}
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

            audit["框样式"] = page.evaluate(READ_FRAME_STYLE)
            audit["按钮关态"] = page.evaluate(READ_BTN_STYLE)

            # ★ 点开关 ⟹ ⟹ 开启态样式 ＋ 三分线
            btn = page.locator("button[title='构图参考线']").first
            box = btn.bounding_box()
            page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            page.wait_for_timeout(1_500)
            audit["按钮开态"] = page.evaluate(READ_BTN_STYLE)
            audit["三分线"] = page.evaluate(READ_LINES)

            # ★ 归一化（canvas 像素）
            frame = audit.get("框样式") or {}
            colors = {}
            if frame.get("outlineColor"):
                colors["框描边"] = page.evaluate(NORM, frame["outlineColor"])
            btn_open = audit.get("按钮开态") or {}
            if btn_open.get("color"):
                colors["按钮前景_开态"] = page.evaluate(NORM, btn_open["color"])
            if btn_open.get("backgroundColor"):
                colors["按钮背景_开态"] = page.evaluate(
                    NORM, btn_open["backgroundColor"])
            btn_off = audit.get("按钮关态") or {}
            if btn_off.get("color"):
                colors["按钮前景_关态"] = page.evaluate(NORM, btn_off["color"])
            for i, c in enumerate((audit.get("三分线") or {}).get("背景色") or []):
                colors[f"三分线_{i}"] = page.evaluate(NORM, c)
            audit["归一化颜色"] = colors
        except Exception:
            audit["异常"] = traceback.format_exc()[-1500:]
        finally:
            browser.close()
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "source-862-frame-thirds-style.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=1)[:4_500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
