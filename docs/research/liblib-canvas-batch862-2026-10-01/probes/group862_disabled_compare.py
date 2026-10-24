#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 862 探针：**源站 vs clone** 的「打组／解组／复制当前选择」在
**无选中**与**有选中**两态下的 `disabled` 读数对照。

## ★ 靶子

★ clone 的场景树顶部有三枚入口：「打组」「解组」「复制当前选择」。
★ clone 普查（`probes/clone862_dead_buttons.py`）发现：在**无选中**时点它们
**什么也没发生**（既不报错、也不提示、也不变）。
★ ★ 源站大概率是**直接 disable**（点不动）⟹ ⟹ 那 clone 就该 disable
⟹ ⟹ 而不是「可点但没反应」。

## ★ 本探针要读到的（**两边同一口径**）

① 「无选中」态：三枚按钮的 `disabled` ＋ 类名 ＋ 可见性；
② 「有选中」态（点场景树里的一行）：同上；
③ 两边的读数**放在同一张表**里 ⟹ ⟹ 直接得到差异。

## ★ 副作用

★ 只点场景树的一行（选中）⟹ ⟹ 无破坏性操作 ⟹ ⟹ 不点任何删除/生成。

## 输出
  raw/source-862-group-disabled.json ＋ raw/clone-862-group-disabled.json
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

# ★ 三枚入口的关键词（源站与 clone 的文案一致）
KEYS = ["打组", "解组", "复制"]

# ★ 读左栏顶部的工具按钮（**排除** rail 那一列 x<48 ⟹ ⟹ 只看面板区）
READ_TOOLBAR = r"""(keys)=>{
  const out=[];
  for(const b of document.querySelectorAll('aside button')){
    const r=b.getBoundingClientRect();
    if(r.width===0||r.height===0) continue;
    if(r.x<48||r.x>=300) continue;
    if(r.y>140) continue;               // ★ 只要**顶部**那排
    const label=((b.getAttribute('aria-label')||'')+'|'+(b.title||'')+'|'
                 +(b.textContent||'')).replace(/\s+/g,' ').trim();
    if(!keys.some(k=>label.includes(k))) continue;
    const cs=getComputedStyle(b);
    out.push({label:label.slice(0,40), disabled:b.disabled===true,
              ariaDisabled:b.getAttribute('aria-disabled'),
              opacity:cs.opacity, cursor:cs.cursor, pointerEvents:cs.pointerEvents,
              x:Math.round(r.x),y:Math.round(r.y),
              w:Math.round(r.width),h:Math.round(r.height)});
  }
  return out;
}"""

# ★ 场景树里的对象行（用来选中一个对象）
READ_OBJECT_ROWS = r"""()=>{
  const out=[];
  for(const el of document.querySelectorAll('aside [class*="row"], aside [data-director-object-row]')){
    const r=el.getBoundingClientRect();
    if(r.width===0||r.height===0) continue;
    const t=(el.textContent||'').replace(/\s+/g,' ').trim();
    if(!t||t.length>40) continue;
    out.push({text:t.slice(0,30), x:Math.round(r.x),y:Math.round(r.y),
              w:Math.round(r.width),h:Math.round(r.height)});
    if(out.length>12) break;
  }
  return out;
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


def probe(page, label: str, opener) -> dict:
    out: dict = {"端": label}
    try:
        opener(page)
        page.wait_for_timeout(1200)
        # ① 无选中态
        out["无选中_按钮"] = page.evaluate(READ_TOOLBAR, KEYS)
        rows = page.evaluate(READ_OBJECT_ROWS)
        out["对象行"] = rows[:6]
        # ② 选中第一个对象行 ⟹ ⟹ 再读
        if rows:
            r0 = rows[0]
            page.mouse.click(r0["x"] + 12, r0["y"] + r0["h"] / 2)
            page.wait_for_timeout(1200)
            out["有选中_按钮"] = page.evaluate(READ_TOOLBAR, KEYS)
        else:
            out["有选中_按钮"] = "（没找到对象行）"
    except Exception:
        out["异常"] = traceback.format_exc()[-1200:]
    return out


def main() -> int:
    audit: dict = {"batch": 862, "probe": "group-disabled-compare"}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            # ── 源站 ──
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            load_cookies(page)
            page.goto(SOURCE_URL, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(6_000)
            audit["源站"] = probe(page, "源站", open_source_desk)
            page.close()

            # ── clone ──
            page2 = browser.new_page(viewport={"width": 1920, "height": 1080})
            audit["clone"] = probe(page2, "clone", open_clone_desk)
            page2.close()
        except Exception:
            audit["异常"] = traceback.format_exc()[-1500:]
        finally:
            browser.close()

    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "group-disabled-compare.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    for side in ("源站", "clone"):
        d = audit.get(side) or {}
        print(f"=== {side} ===")
        print("  无选中:", json.dumps(d.get("无选中_按钮"), ensure_ascii=False)[:400])
        print("  有选中:", json.dumps(d.get("有选中_按钮"), ensure_ascii=False)[:400])
        print("  对象行:", json.dumps(d.get("对象行"), ensure_ascii=False)[:200])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
