#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 861 源站探针 · 第四版：**点「全景图」三行**，各自打开什么。

## ★ 源码层已钉死的（第三版追出来的）

源站逐字（chunk，`aU` 的 panorama 段）：
```js
(0,i.jsxs)("button",{type:"button",className:eu,onClick:()=>{I?.(),et.current?.click()},…})   // 本地上传
(0,i.jsxs)("button",{type:"button",className:eu,onClick:T,…})                                   // 历史记录
(0,i.jsxs)("button",{type:"button",disabled:E,className:eu,onClick:P,…})                        // AI生成
```
回调实现（逐字）：
- `oY`（本地上传的 `I`）＝ **纯埋点**：`libtv.canvas.director.panorama.local_upload.click`
  ⟹ ⟹ 真正的动作是 **`et.current?.click()`**（触发隐藏的 file input）；
- `oX`（AI生成的 `P`）＝ `td(!0)` ⟹ ⟹ 打开一个对话框（`tc` 状态）；
- `oB`（历史记录的 `T`）＝ `eu?.((e,t)=>{…})` ⟹ ⟹ 依赖上游提供的选择器 `eu`。

★ ★ **关键的安全判断**：这三个点击**只打开界面**（文件选择器／对话框），
**不触发生图、不上传** ⟹ ⟹ 可以安全点击取证。
★ 点「本地上传」时**不选文件**（headless 下 filechooser 会触发，我们不响应）⟹ ⟹ 无上传。

## ★ 本探针要读到的

① 点「本地上传」⟹ ⟹ **是否弹出文件选择器**（Playwright `filechooser` 事件）；
② 点「历史记录」⟹ ⟹ 出现什么（面板／对话框／无反应）；
③ 点「AI生成」⟹ ⟹ 出现什么对话框（**绝不点对话框里的生成按钮**）；
④ 三行各自的 `disabled` 状态 ＋ 「AI生成」的文本（`panoramaAiGenerating` 分支）。

## ★ 副作用声明

★ 只**打开**界面，不提交任何生成；点完刷新/退出即可复原（无持久改动）。
★ **绝不点**对话框里的「生成」「确定」等提交按钮。

## 输出
  raw/source-861-panorama-rows.json
"""
from __future__ import annotations

import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch861-2026-10-01"
RAW = BATCH / "raw"

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 读「刚出现的浮层」：所有 z-index 高的 fixed/absolute 容器 ＋ 它们的文本
READ_OVERLAY = r"""()=>{
  const out=[];
  const all=[...document.querySelectorAll('div,section,aside,dialog')];
  for(const e of all){
    const cs=getComputedStyle(e);
    const z=parseInt(cs.zIndex||'0',10);
    if(!Number.isFinite(z)||z<30) continue;
    const r=e.getBoundingClientRect();
    if(r.width<120||r.height<60) continue;
    if(r.width>1900&&r.height>1000) continue;
    const t=(e.textContent||'').replace(/\s+/g,' ').trim();
    if(!t||t.length>400) continue;
    // ★ 只取最内层（没有更小的同 z 兄弟覆盖）
    out.push({z, cls:(e.getAttribute('class')||'').slice(0,90),
              rect:{x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)},
              text:t.slice(0,300)});
  }
  // ★ 去重（按 z+rect）
  const seen=new Set(); const uniq=[];
  for(const o of out.sort((a,b)=>b.z-a.z)){
    const k=o.z+'|'+JSON.stringify(o.rect);
    if(seen.has(k)) continue; seen.add(k); uniq.push(o);
  }
  return uniq.slice(0,12);
}"""

# ★ 读三行本身的状态
READ_ROWS = r"""()=>{
  const want=['本地上传','历史记录','AI生成','生成中'];
  const out=[];
  for(const b of document.querySelectorAll('aside button')){
    const t=(b.textContent||'').trim();
    if(!want.includes(t)) continue;
    const cs=getComputedStyle(b);
    out.push({text:t, disabled:b.disabled===true, opacity:cs.opacity, cursor:cs.cursor,
              hasIcon:!!b.querySelector('svg')});
  }
  return out;
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


def open_panorama(page) -> None:
    page.locator("[aria-label='全景图'], button:has-text('全景图')").first.click(
        timeout=15_000)
    page.wait_for_timeout(1_500)


def main() -> int:
    audit: dict = {"batch": 861, "probe": "source861_panorama_rows"}
    choosers: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            # ★ 监听文件选择器（点「本地上传」应当触发）
            page.on("filechooser", lambda fc: choosers.append(
                str(getattr(fc, "element", None) and
                    fc.element.get_attribute("type"))))
            load_cookies(page)
            page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(6_000)
            open_desk(page)
            open_panorama(page)

            audit["三行_前"] = page.evaluate(READ_ROWS)

            # ① 本地上传 ⟹ 应当弹出文件选择器
            page.locator("aside button", has_text="本地上传").first.click(
                timeout=10_000)
            page.wait_for_timeout(1_800)
            audit["本地上传_弹了文件选择器"] = bool(choosers)
            audit["本地上传_浮层"] = page.evaluate(READ_OVERLAY)

            # ② 历史记录
            page.locator("aside button", has_text="历史记录").first.click(
                timeout=10_000)
            page.wait_for_timeout(2_000)
            audit["历史记录_浮层"] = page.evaluate(READ_OVERLAY)

            # ③ AI生成（只打开对话框 ⟹ 不点提交）
            page.locator("aside button", has_text="AI生成").first.click(
                timeout=10_000)
            page.wait_for_timeout(2_500)
            audit["AI生成_浮层"] = page.evaluate(READ_OVERLAY)
            audit["三行_后"] = page.evaluate(READ_ROWS)
            audit["页面按钮总数"] = page.evaluate("document.querySelectorAll('button').length")
        except Exception:
            audit["异常"] = traceback.format_exc()[-1800:]
        finally:
            browser.close()

    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "source-861-panorama-rows.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    for k in ("三行_前", "本地上传_弹了文件选择器", "三行_后", "异常"):
        print(f"{k}: {audit.get(k)}")
    for k in ("本地上传_浮层", "历史记录_浮层", "AI生成_浮层"):
        print(f"--- {k}:")
        for o in (audit.get(k) or [])[:4]:
            print("   z=%s %s %s" % (o["z"], o["rect"], o["text"][:150]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
