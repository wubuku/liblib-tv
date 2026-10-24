#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 862 探针：**源站 vs clone** 的「添加角色」面板**逐枚**读数对照。

## ★ 靶子

★ 源站逐字（chunk `aU` 的 character 段）：
```js
ei.map(e=>(0,i.jsxs)("button",{type:"button",className:eu,
  onClick:()=>h({...e.bodyType?{bodyType:e.bodyType}:{},
                  ...e.scaleOverride?{scale:e.scaleOverride}:{}}),
  children:[(0,i.jsx)(aT,{}),(0,i.jsx)("span",{className:"truncate",children:e.label})]},e.id))
```
⟹ ⟹ 预设来自一个**数组**，每项有 `id`／`label`／可选 `bodyType`／`scaleOverride`。

★ ★★ 源站左栏的**实测文本**是：
「添加角色 本地上传 标准男性 标准女性 健硕 纤细 少年 儿童 **宽厚二头身** 群众 (3x3) 几何模型」
⟹ ⟹ **7 枚**预设角色，「宽厚」「二头身」在源站是**一枚**。

★ 而 clone 的 `DirectorCharacterPanel.tsx` 是 **8 枚**：
标准男性／标准女性／健硕／纤细／少年／儿童／**宽厚**／**二头身**
⟹ ⟹ ★★ **clone 把源站的一枚拆成了两枚** ⟹ ⟹ 逐字差异。

## ★ 本探针要读到的（**两边同一口径**）

① 角色面板里**每一枚**的逐字文本 ＋ 顺序 ＋ 矩形 ＋ 图标；
② 面板容器与标题条的**类名**（逐字对照源站 chunk 里的类串）；
③ 两边放在**同一张表**里 ⟹ ⟹ 直接得到差异。

## ★ 副作用

★ 只读 ⟹ ⟹ 无副作用。

## 输出
  raw/character-panel-compare.json
"""
from __future__ import annotations

import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch862-2026-10-01"
RAW = BATCH / "raw"
SOURCE_COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
SOURCE_URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
              "&projectId=a860e1da8e9e4504bececda022386429")
CLONE_BASE = "http://localhost:4317"

# ★ 读「添加角色」面板的每一枚行（**排除** rail 那一列 x<48）
READ_PANEL = r"""()=>{
  const aside=document.querySelector('aside');
  if(!aside) return null;
  const rows=[];
  for(const b of aside.querySelectorAll('button')){
    const r=b.getBoundingClientRect();
    if(r.width===0||r.height===0) continue;
    if(r.x<48||r.x>=300) continue;
    const label=((b.getAttribute('aria-label')||'')+'|'+(b.title||'')+'|'
                 +(b.textContent||'')).replace(/\s+/g,' ').trim();
    const svg=b.querySelector('svg');
    rows.push({
      label:label.slice(0,50),
      text:(b.textContent||'').replace(/\s+/g,' ').trim(),
      x:Math.round(r.x),y:Math.round(r.y),
      w:Math.round(r.width),h:Math.round(r.height),
      hasIcon:!!svg,
      iconPath:(svg&&svg.querySelector('path'))?svg.querySelector('path').getAttribute('d').slice(0,40):null,
      cls:(b.getAttribute('class')||'').slice(0,120),
    });
  }
  // ★ 容器与标题条
  const title=aside.querySelector('[class*="h-12"]');
  const panels=[...aside.querySelectorAll('div')].filter(e=>{
    const c=(e.getAttribute('class')||'');
    return c.indexOf('overflow-y-auto')>=0 && c.indexOf('px-2')>=0;
  });
  return {
    行:rows,
    标题文本:title?(title.textContent||'').trim():null,
    标题类名:title?(title.getAttribute('class')||''):null,
    容器类名:panels.length?panels[0].getAttribute('class'):null,
  };
}"""


def load_cookies(page) -> None:
    data = json.loads(SOURCE_COOKIE.read_text(encoding="utf-8"))
    cookies = data if isinstance(data, list) else data.get("cookies", [])
    page.context.add_cookies([
        {"name": c["name"], "value": c["value"], "domain": c["domain"],
         "path": c.get("path", "/")}
        for c in cookies if c.get("name")
    ])


def open_source_desk(page) -> None:
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(600)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')"
    ).first.click()
    page.wait_for_timeout(8_000)


def open_clone_desk(page) -> None:
    page.goto(CLONE_BASE + "/", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
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
    page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")


def main() -> int:
    audit: dict = {"batch": 862, "probe": "character-panel-compare"}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            load_cookies(page)
            page.goto(SOURCE_URL, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(6_000)
            open_source_desk(page)
            page.locator("[aria-label='添加角色'], button:has-text('添加角色')").first.click(
                timeout=15_000)
            page.wait_for_timeout(1500)
            audit["源站"] = page.evaluate(READ_PANEL)
            page.screenshot(path=str(BATCH / "images/862src_character_panel.png")
                            if (BATCH / "images").exists() else
                            str(BATCH / "raw/862src_character_panel.png"))
            page.close()

            page2 = browser.new_page(viewport={"width": 1920, "height": 1080})
            open_clone_desk(page2)
            page2.locator("[data-director-rail-entry='add-character']").first.click(
                timeout=15000)
            page2.wait_for_timeout(1200)
            audit["clone"] = page2.evaluate(READ_PANEL)
            page2.screenshot(path=str(BATCH / "raw/862clone_character_panel.png"))
            page2.close()
        except Exception:
            audit["异常"] = traceback.format_exc()[-1500:]
        finally:
            browser.close()

    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "character-panel-compare.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    for side in ("源站", "clone"):
        d = audit.get(side) or {}
        print(f"=== {side} ===")
        for r in (d.get("行") or []):
            print(f"   {r['text']!r:28s} @({r['x']},{r['y']}) {r['w']}x{r['h']} icon={r['hasIcon']}")
        print("   标题类名:", (d.get("标题类名") or "")[:90])
        print("   容器类名:", (d.get("容器类名") or "")[:120])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
