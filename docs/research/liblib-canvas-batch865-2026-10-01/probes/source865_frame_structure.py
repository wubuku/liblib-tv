#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 865 源站探针：取景框的**运行时 DOM 结构** ＋ 框的 `pointer-events`。

## ★ 靶子

★ batch 864 登记了 **D25**：源站取景框那三层是
「遮罩层／**空框**／三分线层／开关」**四者平级**（都是遮罩容器的**直接子元素**），
而 clone 把**三分线与开关塞进了框里**。

★ chunk 的逐字（`mP` 组件）说它是四者平级 ⟹ ⟹ 但**逐字 ≠ 运行时**
⟹ ⟹ 本探针用**源站运行时 DOM** 独立证实一遍（★ 比逐字更强：
逐字可能被压缩／改写，运行时不会）。

★ 顺带取一条**继承**的证据：★ 源站的框**没有**写 `pointer-events`
⟹ ⟹ 但 `pointer-events` 是**可继承属性**
⟹ ⟹ 它**继承**了容器的 `pointer-events-none`
⟹ ⟹ 源站运行时那个框的 `pointerEvents` 应该是 `"none"`
⟹ ⟹ ★ 若读出来确实是 `"none"` ⟹ ⟹ clone 显式写 `pointer-events-none`
就是**与源站完全等价**（不是偏差）。

## ★ 副作用声明

★ 只点「选择画幅比例」与「16:9」⟹ ⟹ 本地视图态；
  **绝不点**「AI生成」「本地上传」「截图」「导出」⟹ ⟹ 不产生付费或生图动作。

## 输出
  raw/source-865-frame-structure.json
"""
from __future__ import annotations

import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")
BATCH = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv/"
                     "docs/research/liblib-canvas-batch865-2026-10-01")
RAW = BATCH / "raw"

# ★ ★ 运行时读数：★ **按类名**找源站那四个元素（源站编译后的类名逐字相同）
READ = r"""()=>{
  const byCls=sel=>[...document.querySelectorAll(sel)];
  const mask=byCls('.bg-black\\/20.backdrop-blur-md')[0];
  if(!mask) return {遮罩层在场:false};
  const cont=mask.parentElement;
  const cls=el=>el?(el.getAttribute('class')||''):null;
  const cs=el=>el?getComputedStyle(el):null;
  const children=[...cont.children].map(el=>({
    tag:el.tagName,
    cls:cls(el),
    是不是遮罩层:el===mask,
    pointerEvents:cs(el)?cs(el).pointerEvents:null,
    zIndex:cs(el)?cs(el).zIndex:null,
  }));
  // ★ 框：容器里那个「有 outline 的空 div」
  const frame=[...cont.children].find(el=>{
    const c=cls(el)||'';
    return c.includes('outline-white/18')&&c.includes('rounded-xl')&&!c.includes('backdrop-blur');
  })||null;
  const thirds=[...cont.children].find(el=>{
    const c=cls(el)||'';
    return c.includes('overflow-hidden')&&c.includes('rounded-xl')&&!c.includes('outline-white/18');
  })||null;
  const toggle=[...cont.children].find(el=>el.tagName==='BUTTON')||null;
  const out={
    遮罩层在场:true,
    容器类:cls(cont),
    容器pointerEvents:cs(cont)?cs(cont).pointerEvents:null,
    容器子元素数:cont.children.length,
    容器子元素:children,
    框:{cls:cls(frame), 子元素数:frame?frame.childElementCount:null,
        父是不是容器:frame?frame.parentElement===cont:null,
        pointerEvents:cs(frame)?cs(frame).pointerEvents:null,
        zIndex:cs(frame)?cs(frame).zIndex:null,
        rect:frame?(()=>{const r=frame.getBoundingClientRect();
              return {x:Math.round(r.x),y:Math.round(r.y),
                      w:Math.round(r.width),h:Math.round(r.height)};})():null},
    三分线层:{cls:cls(thirds), 在场:!!thirds,
        pointerEvents:cs(thirds)?cs(thirds).pointerEvents:null,
        ariaHidden:thirds?thirds.getAttribute('aria-hidden'):null,
        父是不是容器:thirds?thirds.parentElement===cont:null},
    开关:{cls:cls(toggle), 在场:!!toggle,
        pointerEvents:cs(toggle)?cs(toggle).pointerEvents:null,
        zIndex:cs(toggle)?cs(toggle).zIndex:null,
        父是不是容器:toggle?toggle.parentElement===cont:null,
        title:toggle?toggle.getAttribute('title'):null,
        rect:toggle?(()=>{const r=toggle.getBoundingClientRect();
              return {x:Math.round(r.x),y:Math.round(r.y),
                      w:Math.round(r.width),h:Math.round(r.height)};})():null},
  };
  // ★ ★ 四者平级的**判定**：★ 每个元素的父元素**都是容器**
  out.四者都直属容器 =
    out.框.父是不是容器 === true &&
    out.三分线层.父是不是容器 === true &&
    out.开关.父是不是容器 === true;
  return out;
}"""


def load_cookies(page) -> None:
    data = json.loads(COOKIE.read_text(encoding="utf-8"))
    cookies = data if isinstance(data, list) else data.get("cookies", [])
    page.context.add_cookies([
        {"name": c["name"], "value": c["value"], "domain": c.get("domain") or ".liblib.tv",
         "path": c.get("path") or "/"}
        for c in cookies if c.get("name")
    ])


def main() -> int:
    audit: dict = {"batch": 865, "probe": "source865_frame_structure"}
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
            # ★ 选 16:9 ⟹ ⟹ 取景框在场
            page.locator("[aria-label='选择画幅比例'], button:has-text('选择画幅比例')"
                         ).first.click(timeout=15_000)
            page.wait_for_timeout(1_500)
            page.locator("button:has-text('16:9')").first.click(timeout=15_000)
            page.wait_for_timeout(3_000)
            audit["16比9"] = page.evaluate(READ)
            # ★ ★ 再开参考线 ⟹ ⟹ 三分线层应当场（★ 它是**条件渲染**的）
            toggle = page.locator("button[title='构图参考线'], "
                                  "button[aria-label='构图参考线']").first
            if toggle.count() == 1:
                toggle.click(timeout=15_000)
                page.wait_for_timeout(2_500)
                audit["开参考线后"] = page.evaluate(READ)
            else:
                audit["开参考线说明"] = f"★ 框上那枚按钮没找到（count={toggle.count()}）"
        except Exception:
            audit["异常"] = traceback.format_exc()[-2000:]
        finally:
            browser.close()

    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "source-865-frame-structure.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=1)[:5000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
