#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 861 源站探针 · 第五版：**「AI生成」「历史记录」到底开没开界面**（截图 ＋ DOM 差分）。

## ★ 为什么还要第五版

第四版读出：
- 「本地上传」⟹ **弹出了文件选择器**（`filechooser` 触发 ＝ True）✔ 决定性
- 「历史记录」「AI生成」⟹ **没读到新浮层**

★ 但第四版的浮层探针**只按 z-index ≥ 30 过滤** ⟹ ⟹ 对话框若 z 较低就会**漏掉**
⟹ ⟹ 「没读到」**不等于**「没打开」⟹ ⟹ 结论未定。

★ 而这个结论会**决定 861 的靶子**：
- 若源站两行**真的开了界面** ⟹ ⟹ clone 是「占位」⟹ ⟹ 值得整改；
- 若源站两行**也点了没反应** ⟹ ⟹ clone 与源站**一致** ⟹ ⟹ **不是缺口** ⟹ ⟹ 别改。

## ★ 本版读什么

① 点击前后的**按钮文本集合差分**（不限 z）；
② 点击后的**截图**（人眼可判）；
③ 整页文本长度差分（对话框会带进新文本）；
④ `aria-modal`／`role="dialog"` 元素的有无。

## ★ 副作用声明

★ 只点击行本体，**绝不点对话框里的提交按钮** ⟹ ⟹ 不生图、不上传。

## 输出
  raw/source-861-panorama-diff.json ＋ images/861src_ai.png 等
"""
from __future__ import annotations

import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch861-2026-10-01"
RAW = BATCH / "raw"
IMG = BATCH / "images"

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

SNAP = r"""()=>{
  const btn=[...document.querySelectorAll('button')]
    .map(b=>((b.getAttribute('aria-label')||'')+'|'+(b.title||'')+'|'+(b.textContent||'')).replace(/\s+/g,' ').trim())
    .filter(Boolean);
  const dialogs=[...document.querySelectorAll('[role="dialog"],[aria-modal="true"]')]
    .map(e=>{const r=e.getBoundingClientRect();
      return {text:(e.textContent||'').replace(/\s+/g,' ').trim().slice(0,200),
              rect:{x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)}};});
  const body=(document.body.innerText||'').replace(/\s+/g,' ').trim();
  return {buttons:btn, dialogs:dialogs, textLen:body.length,
          textTail:body.slice(-400),
          inputs:[...document.querySelectorAll('input')].map(i=>({type:i.type,accept:i.accept})).slice(0,10)};
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


def diff(before: list[str], after: list[str]) -> dict:
    sb, sa = set(before), set(after)
    return {
        "新增按钮": sorted(sa - sb)[:30],
        "消失按钮": sorted(sb - sa)[:30],
        "按钮数前": len(before), "按钮数后": len(after),
    }


def main() -> int:
    audit: dict = {"batch": 861, "probe": "source861_panorama_diff"}
    IMG.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            load_cookies(page)
            page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(6_000)
            open_desk(page)
            open_panorama(page)

            base = page.evaluate(SNAP)
            audit["基线"] = {"按钮数": len(base["buttons"]),
                             "dialogs": base["dialogs"],
                             "textLen": base["textLen"],
                             "inputs": base["inputs"]}
            page.screenshot(path=str(IMG / "861src_panorama_before.png"))

            # ① 历史记录
            page.locator("aside button", has_text="历史记录").first.click(
                timeout=10_000)
            page.wait_for_timeout(2_500)
            hist = page.evaluate(SNAP)
            audit["历史记录"] = diff(base["buttons"], hist["buttons"])
            audit["历史记录"]["dialogs"] = hist["dialogs"]
            audit["历史记录"]["textLen前"] = base["textLen"]
            audit["历史记录"]["textLen后"] = hist["textLen"]
            audit["历史记录"]["textTail"] = hist["textTail"]
            page.screenshot(path=str(IMG / "861src_after_history.png"))

            # ② AI生成
            page.locator("aside button", has_text="AI生成").first.click(
                timeout=10_000)
            page.wait_for_timeout(3_000)
            ai = page.evaluate(SNAP)
            audit["AI生成"] = diff(base["buttons"], ai["buttons"])
            audit["AI生成"]["dialogs"] = ai["dialogs"]
            audit["AI生成"]["textLen前"] = base["textLen"]
            audit["AI生成"]["textLen后"] = ai["textLen"]
            audit["AI生成"]["textTail"] = ai["textTail"]
            audit["AI生成"]["inputs"] = ai["inputs"]
            page.screenshot(path=str(IMG / "861src_after_ai.png"))
        except Exception:
            audit["异常"] = traceback.format_exc()[-1800:]
        finally:
            browser.close()

    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "source-861-panorama-diff.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=1)[:3_500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
