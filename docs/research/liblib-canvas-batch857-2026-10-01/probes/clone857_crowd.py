#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 857 clone 探针：导演台「群众阵列（crowd）」对话框的**行为与几何**。

## ★ 对齐的源站逐字（见 raw/source-857-contract.json）

| 源站逐字 | clone 应当 |
| --- | --- |
| `[K,Q]=useState(1.2)` ＋ 行/列 `useState(3)` | 对话框初值 3／3／1.2 |
| 行/列 `min:1,max:10,step:1`；间距 `min:.1,max:10,step:.1` | 同 |
| 间距 onChange `Math.min(10,Math.max(.1,Math.round(10*t)/10))` | 填 1.55 ⟹ 读回 **1.6** |
| `W({left:t.right+8,top:t.top})`（t ＝ 按钮矩形） | 对话框 **left ＝ 按钮 right+8**、**top ＝ 按钮 top** |
| `if("crowd"===L)return void O(null)` | 再点一次「群众 (3x3)」⟹ **对话框关闭** |
| `en.current?.contains(t)||ea.current?.contains(t)||O(null)` | 点**外面** ⟹ **对话框关闭** |
| `"aria-expanded":"crowd"===L` | 按钮 `aria-expanded` 随开关变 |
| 全页同 aria-label 的入口**只有 1 个** | 桌面**可见**入口**只有 1 枚** |

## ★ 两个断点要分别取证（★ 不能混着说「一个入口」）

- 桌面（1440×900）：可见的 crowd 入口**只有 rail 的「群众 (3x3)」** ⟹ 与源站一致。
- 移动端（390×844）：rail 是 `hidden` ⟹ ⟹ **移动端那枚视口按钮**是唯一入口
  ⟹ ⟹ 这是 **clone 自己的扩展**（源站没有移动端布局，见
  `raw/source-857-mobile.json`）⟹ ⟹ 如实登记、单独取证。

## 输出
  raw/clone-857-crowd.json
  images/857clone_crowd-*.png
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch857-2026-10-01"
RAW = BATCH / "raw"
SHOTS = BATCH / "images"
BASE = "http://localhost:4317"

# ★ 一次读齐：入口矩形、对话框矩形、两个入口是否可见、输入框的量程
READ_STATE = r"""()=>{
  const vis = (e)=>{ if(!e) return false; const r=e.getBoundingClientRect();
    const cs=getComputedStyle(e);
    return r.width>0 && r.height>0 && cs.display!=='none' && cs.visibility!=='hidden'; };
  const rect = e=>{ if(!e) return null; const r=e.getBoundingClientRect();
    return {x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height),
            right:Math.round(r.right), bottom:Math.round(r.bottom)}; };
  const btn = document.querySelector("[data-director-character-option='crowd-3x3']");
  const mobile = document.querySelector('[data-director-crowd-mobile-trigger]');
  const dlg = document.querySelector('[data-director-crowd-dialog]');
  const input = (k)=>{ const e=document.querySelector("[data-director-crowd-input='"+k+"']");
    if(!e) return null;
    return {value:e.value, min:e.getAttribute('min'), max:e.getAttribute('max'),
            step:e.getAttribute('step'), aria:e.getAttribute('aria-label')}; };
  return {
    rail入口: rect(btn),
    rail入口可见: vis(btn),
    rail入口ariaExpanded: btn ? btn.getAttribute('aria-expanded') : null,
    rail入口背景: btn ? getComputedStyle(btn).backgroundColor : null,
    移动端入口: rect(mobile),
    移动端入口可见: vis(mobile),
    对话框: rect(dlg),
    对话框可见: vis(dlg),
    对话框aria: dlg ? dlg.getAttribute('aria-label') : null,
    计数文案: (document.querySelector('[data-director-crowd-count]')||{}).textContent||'',
    行数: input('rows'), 列数: input('columns'), 间距: input('spacing'),
    可见入口数: [btn, mobile].filter(vis).length,
  };
}"""


def open_desk(pg):
    pg.goto(BASE + "/", wait_until="domcontentloaded")
    pg.wait_for_timeout(3000)
    pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
    pg.wait_for_function("() => Boolean(window.__director_store)", timeout=90_000)
    pg.wait_for_timeout(1500)
    node = pg.locator(".react-flow__node-script-execution").first
    try:
        node.scroll_into_view_if_needed(timeout=8000)
    except Exception:
        pass
    pg.wait_for_timeout(400)
    try:
        node.hover(timeout=8000)
        pg.wait_for_timeout(600)
    except Exception:
        pass
    pg.locator("[data-open-director]").first.click(timeout=15000)
    pg.wait_for_timeout(6500)
    pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")


def open_crowd(pg):
    pg.locator("[data-director-rail-entry='add-character']").click(timeout=15000)
    pg.wait_for_timeout(400)
    pg.locator("[data-director-character-option='crowd-3x3']").click(timeout=15000)
    pg.wait_for_timeout(400)


def main() -> int:
    out = {"批次": "batch 857", "探针": "clone857_crowd"}
    RAW.mkdir(parents=True, exist_ok=True)
    SHOTS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            # ══════════ 桌面 1440×900 ══════════
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            open_desk(page)
            out["①打开导演台"] = "OK"

            page.locator("[data-director-rail-entry='add-character']").click(timeout=15000)
            page.wait_for_timeout(400)
            out["②浮层开着时的入口数"] = page.evaluate(READ_STATE)
            page.locator("[data-director-character-option='crowd-3x3']").click(timeout=15000)
            page.wait_for_timeout(500)
            state = page.evaluate(READ_STATE)
            out["③对话框打开后"] = state
            page.screenshot(path=str(SHOTS / "857clone_crowd-dialog.png"))

            btn = state.get("rail入口") or {}
            dlg = state.get("对话框") or {}
            out["③落点是否符合源站公式"] = {
                "期望_left": btn.get("right", 0) + 8,
                "实测_left": dlg.get("x"),
                "left相等": btn.get("right", 0) + 8 == dlg.get("x"),
                "期望_top": btn.get("y"),
                "实测_top": dlg.get("y"),
                "top相等": btn.get("y") == dlg.get("y"),
            }

            # ★ 间距的**行为**证据（源站填 1.55 ⟹ 读回 1.6）
            page.locator("[data-director-crowd-input='spacing']").fill("1.55")
            page.wait_for_timeout(300)
            out["④间距填1.55后"] = page.evaluate(READ_STATE)

            # ★ 再点一次「群众 (3x3)」⟹ 对话框关闭（源站 `if("crowd"===L)O(null)`）
            page.locator("[data-director-character-option='crowd-3x3']").click(timeout=15000)
            page.wait_for_timeout(400)
            out["⑤再点一次后"] = page.evaluate(READ_STATE)

            # ★ 点**外面** ⟹ 对话框关闭（源站 outside-mousedown）
            open_crowd(page)
            page.wait_for_timeout(300)
            out["⑥重开后"] = page.evaluate(READ_STATE)
            page.locator("[data-director-tree] input").first.click(timeout=15000)
            page.wait_for_timeout(400)
            out["⑦点外面之后"] = page.evaluate(READ_STATE)

            # ★ 桌面**可见**的 crowd 入口只有一个
            page.locator("[data-director-rail-entry='add-character']").click(timeout=15000)
            page.wait_for_timeout(400)
            out["⑧桌面可见入口数"] = page.evaluate(READ_STATE)["可见入口数"]
            page.close()

            # ══════════ 移动端 390×844 ══════════
            mpage = browser.new_page(viewport={"width": 390, "height": 844})
            open_desk(mpage)
            out["⑨移动端导演台"] = "OK"
            mpage.locator("[data-director-crowd-mobile-trigger]").click(timeout=15000)
            mpage.wait_for_timeout(600)
            out["⑩移动端点开对话框"] = mpage.evaluate(READ_STATE)
            mpage.screenshot(path=str(SHOTS / "857clone_crowd-mobile.png"))
            # ★ 移动端那枚也是**开关**（源站「群众 (3x3)」是开关 ⟹ ⟹ 扩展要同语义）
            mpage.locator("[data-director-crowd-mobile-trigger]").click(timeout=15000)
            mpage.wait_for_timeout(500)
            out["⑪移动端再点一次"] = mpage.evaluate(READ_STATE)
            mpage.close()
        except Exception:
            out["★异常"] = traceback.format_exc()[-2500:]
        finally:
            browser.close()
    p = RAW / "clone-857-crowd.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if "★异常" not in out else 1


if __name__ == "__main__":
    sys.exit(main())
