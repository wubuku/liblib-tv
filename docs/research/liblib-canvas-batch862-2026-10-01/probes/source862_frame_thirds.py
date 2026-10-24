#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 862 源站探针：**取景框上的构图网格（三分线）开关按钮**。

## ★ 为什么查这个

★ 源站逐字（chunk `mP` 组件 ＋ 它的调用点）：

```js
function mP({aspectRatio:e, leftPanelWidth:t=281, rightPanelWidth:r=281,
             showCompositionGrid:n=!1, onToggleCompositionGrid:a}){
  ...
  if(!e) return void p(null);          // ★ 没有比例 ⟹ 不画框
  ...
  a?(0,i.jsx)("button",{
      type:"button",
      title:s("canvas:directorAspectFrameOverlay"),
      className:`nodrag nopan nowheel pointer-events-auto absolute z-20 flex h-8 w-8
        items-center justify-center rounded-lg transition-colors
        ${n?"bg-(--btn-secondary-bg) text-btn-primary"
           :"text-white/50 hover:bg-white/10 hover:text-white/80"}`,
      style:{left:u.left+u.width-40, top:u.top+8},
      onClick:a,
      children:(0,i.jsx)(d.f,{className:"h-4 w-4 shrink-0","aria-hidden":!0})
  }):null
}
```

调用点（逐字）：

```js
(0,i.jsx)(mP,{aspectRatio:tr, leftPanelWidth:tO, rightPanelWidth:tU,
  showCompositionGrid:ti,
  onToggleCompositionGrid:null!==tr?()=>{
      let e=!ti, t=e1||rL.cameras[0]?.id;
      t&&n4(t,"reference_line",(0,nZ.p)(e),"right_panel");
      to(e)
  }:void 0})
```

⟹ ⟹ 三条**可验证**断言：
① 取景框**在场**时（选了具体比例），框的**右上角**有一枚 **32×32** 的切换按钮
   （位置 ＝ 框左上 + (框宽 − 40, 8)）；
② 「自适应」（`tr===null`）⟹ 框不在场 ⟹ **按钮也不在场**；
③ 点击 ⟹ 框内出现**三分线**（4 条线）＋ 按钮自身样式切换。

## ★ 副作用声明

★ 只点「画幅比例」与「取景框上的开关」⟹ ⟹ 都是本地视图态，不上传、不生成。
★ **绝不点**「AI生成」「本地上传」「截图」（真实生成/上传）。

## 输出
  raw/source-862-frame-thirds.json
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

# ★ 读取景框：源站逐字 `outline-white/18 absolute rounded-xl outline -outline-offset-1`
READ_FRAME = r"""()=>{
  const frames=[...document.querySelectorAll('div')].filter(e=>{
    const c=e.getAttribute('class')||'';
    return c.includes('outline-white/18') && c.includes('rounded-xl');
  });
  return frames.map(e=>{
    const r=e.getBoundingClientRect();
    const cs=getComputedStyle(e);
    return {cls:(e.getAttribute('class')||''),
            rect:{x:Math.round(r.x),y:Math.round(r.y),
                  w:Math.round(r.width),h:Math.round(r.height)},
            outlineWidth:cs.outlineWidth, outlineColor:cs.outlineColor,
            outlineOffset:cs.outlineOffset, borderRadius:cs.borderRadius,
            lines:e.querySelectorAll('div').length,
            inner:[...e.querySelectorAll('div')].slice(0,8).map(d=>{
              const rc=d.getBoundingClientRect();
              return {cls:(d.getAttribute('class')||'').slice(0,80),
                      x:Math.round(rc.x),y:Math.round(rc.y),
                      w:Math.round(rc.width),h:Math.round(rc.height)};
            })};
  });
}"""

# ★ 读框上那枚按钮：absolute ＋ 32×32 ＋ pointer-events-auto
READ_FRAME_BTN = r"""()=>{
  const frames=[...document.querySelectorAll('div')].filter(e=>{
    const c=e.getAttribute('class')||'';
    return c.includes('outline-white/18') && c.includes('rounded-xl');
  });
  if(!frames.length) return {在场:false, 按钮:[]};
  const fr=frames[0].getBoundingClientRect();
  const all=[...document.querySelectorAll('button')].map(b=>{
    const r=b.getBoundingClientRect();
    const cs=getComputedStyle(b);
    return {title:b.title||'', ariaLabel:b.getAttribute('aria-label')||'',
            cls:(b.getAttribute('class')||''),
            pos:cs.position, pe:cs.pointerEvents, z:cs.zIndex,
            color:cs.color, bg:cs.backgroundColor,
            x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height),
            svg:b.querySelectorAll('svg').length,
            svgCls:b.querySelector('svg')?(b.querySelector('svg').getAttribute('class')||''):''};
  });
  // ★ 只留「落在框内 或 贴着框右上角」的按钮
  const near=all.filter(b=>b.w>0&&b.h>0&&(
    (b.x>=fr.left-2 && b.x<=fr.right+2 && b.y>=fr.top-2 && b.y<=fr.bottom+2) ||
    (b.x>=fr.left+fr.width-120 && b.x<=fr.left+fr.width+60 &&
     b.y>=fr.top-20 && b.y<=fr.top+60)));
  return {在场:true,
          框:{x:Math.round(fr.x),y:Math.round(fr.y),
              w:Math.round(fr.width),h:Math.round(fr.height)},
          按钮:near, 全部按钮数:all.length};
}"""

# ★ 读三分线：源站逐字 `bg-(--color-white-alpha-50) absolute … w-px / h-px`
READ_THIRDS = r"""()=>{
  const lines=[...document.querySelectorAll('div')].filter(e=>{
    const c=e.getAttribute('class')||'';
    return c.includes('--color-white-alpha-50');
  }).map(e=>{
    const r=e.getBoundingClientRect();
    return {cls:(e.getAttribute('class')||''),
            x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};
  });
  return {条数:lines.length, 线:lines};
}"""


def load_cookies(page) -> None:
    data = json.loads(COOKIE.read_text(encoding="utf-8"))
    cookies = data if isinstance(data, list) else data.get("cookies", [])
    page.context.add_cookies([
        {"name": c["name"], "value": c["value"], "domain": c["domain"],
         "path": c.get("path", "/")}
        for c in cookies if c.get("name")
    ])


def open_desk(page) -> None:
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(600)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')"
    ).first.click()
    page.wait_for_timeout(8_000)


def open_aspect(page) -> None:
    page.locator(
        "[aria-label='选择画幅比例'], button:has-text('选择画幅比例')"
    ).first.click(timeout=15_000)
    page.wait_for_timeout(1_500)


def main() -> int:
    audit: dict = {"batch": 862, "probe": "source862_frame_thirds"}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            load_cookies(page)
            page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(6_000)
            open_desk(page)
            audit["导演台已开"] = True

            # ① 默认（「自适应」）⟹ ⟹ 框不在场 ⟹ ⟹ 按钮也不在场
            audit["自适应_框"] = page.evaluate(READ_FRAME)
            audit["自适应_框上按钮"] = page.evaluate(READ_FRAME_BTN)
            audit["自适应_三分线"] = page.evaluate(READ_THIRDS)

            # ② 选 16:9 ⟹ ⟹ 框在场
            open_aspect(page)
            page.locator("button:has-text('16:9')").first.click(timeout=15_000)
            page.wait_for_timeout(2_000)
            audit["选16比9_框"] = page.evaluate(READ_FRAME)
            audit["选16比9_框上按钮"] = page.evaluate(READ_FRAME_BTN)
            audit["选16比9_三分线"] = page.evaluate(READ_THIRDS)

            # ③ 点框上那枚开关 ⟹ ⟹ 三分线出现
            btn = page.locator("[data-862-frame-btn]").first
            hit = None
            for b in audit.get("选16比9_框上按钮", {}).get("按钮", []):
                if b["w"] == 32 and b["h"] == 32 and b["pe"] == "auto":
                    hit = b
                    break
            audit["选中按钮"] = hit
            if hit:
                page.mouse.click(hit["x"] + hit["w"] / 2, hit["y"] + hit["h"] / 2)
                page.wait_for_timeout(1_500)
                audit["点开关后_三分线"] = page.evaluate(READ_THIRDS)
                audit["点开关后_框上按钮"] = page.evaluate(READ_FRAME_BTN)
        except Exception:
            audit["异常"] = traceback.format_exc()[-2000:]
        finally:
            browser.close()

    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "source-862-frame-thirds.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=1)[:5_000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
