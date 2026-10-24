#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 862 源站探针 · 第一版：「添加角色」的**预设角色**点开会打开什么。

## ★ 靶子

★ clone 的 `DirectorCharacterPanel.tsx` 里，8 枚预设角色点开会弹一句
`预设角色「X」为本地等效占位` ⟹ ⟹ **占位**（用户可见的假功能）。

★ 源站逐字（`aU` 的 character 段）：预设角色那几枚走 `onAddCharacter:h`
⟹ ⟹ 传的是**预设 id** ⟹ ⟹ 打开什么要**实测**。

## ★ 本探针要读到的

① 「添加角色」面板里那几枚预设的**逐字标签 ＋ 坐标 ＋ 尺寸**；
② ★ 点第 1 枚预设后，**DOM 差分**（按钮文本集合 ＋ 整页文本长度 ＋ dialog 元素）；
③ ★ 点开后的**截图**（人眼可判）；
④ ★ 关掉之后再点另一枚 ⟹ ⟹ 看是不是同一个界面。

## ★ 副作用声明

★ 点预设角色在源站**只打开界面**（不生图、不付费）⟹ ⟹ 安全。
★ ★ 绝不点任何对话框里的「生成」「确认购买」等提交按钮。

## 输出
  raw/source-862-character-preset.json ＋ images/862src_*.png
"""
from __future__ import annotations

import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch861-2026-10-01"
ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch862-2026-10-01"
RAW = BATCH / "raw"
IMG = BATCH / "images"

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

SNAP = r"""()=>{
  const btn=[...document.querySelectorAll('button')].map(b=>
    ((b.getAttribute('aria-label')||'')+'|'+(b.title||'')+'|'+(b.textContent||''))
    .replace(/\s+/g,' ').trim().slice(0,70)).filter(Boolean);
  const dialogs=[...document.querySelectorAll('[role="dialog"],[aria-modal="true"]')]
    .map(e=>{const r=e.getBoundingClientRect();
      return {text:(e.textContent||'').replace(/\s+/g,' ').trim().slice(0,260),
              rect:{x:Math.round(r.x),y:Math.round(r.y),
                    w:Math.round(r.width),h:Math.round(r.height)}};});
  const body=(document.body.innerText||'').replace(/\s+/g,' ').trim();
  return {buttons:btn, dialogs:dialogs, textLen:body.length, textTail:body.slice(-600)};
}"""

# ★ 左栏「添加角色」模式下的所有行（预设角色那几枚）
READ_ROWS = r"""()=>{
  const aside=document.querySelector('aside');
  if(!aside) return null;
  const btns=[...aside.querySelectorAll('button')].map(b=>{
    const r=b.getBoundingClientRect();
    if(r.width===0||r.height===0) return null;
    return {label:((b.getAttribute('aria-label')||'')+'|'+(b.title||'')+'|'
                  +(b.textContent||'')).replace(/\s+/g,' ').trim().slice(0,60),
            disabled:b.disabled===true,
            x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};
  }).filter(Boolean);
  return {text:(aside.textContent||'').replace(/\s+/g,' ').trim().slice(0,600),
          buttons:btns};
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


def diff(before: list[str], after: list[str]) -> dict:
    sb, sa = set(before), set(after)
    return {"新增按钮": sorted(sa - sb)[:30], "消失按钮": sorted(sb - sa)[:20]}


def main() -> int:
    audit: dict = {"batch": 862, "probe": "source862_character_preset"}
    IMG.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            load_cookies(page)
            page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(6_000)
            open_desk(page)

            # ★ 进「添加角色」模式
            page.locator("[aria-label='添加角色'], button:has-text('添加角色')").first.click(
                timeout=15_000)
            page.wait_for_timeout(1_500)
            rows = page.evaluate(READ_ROWS)
            audit["添加角色_左栏"] = rows
            page.screenshot(path=str(IMG / "862src_character_panel.png"))

            base = page.evaluate(SNAP)
            audit["基线"] = {"按钮数": len(base["buttons"]), "textLen": base["textLen"]}

            # ★ 点第 1 枚预设角色（不是「本地上传」／「群众」／「几何体」那几枚）
            # ★ ★ 第一版踩的坑：筛选只按关键词 ⟹ ⟹ 选中了「**关闭**」按钮
            #   （x=0,y=6）⟹ ⟹ 把导演台整个关掉了 ⟹ ⟹ 差分读数变成「界面消失」。
            #   ⇒ 改成**按位置筛**：只在**左栏面板区**（48 ≤ x < 280 且 y > 100）
            #   且**不在** rail 那一列（x < 48）里挑。
            preset_btn = None
            for b in (rows or {}).get("buttons", []):
                lbl = b["label"]
                if not lbl or b["x"] < 48 or b["x"] >= 280 or b["y"] < 100:
                    continue
                if any(k in lbl for k in ("本地上传", "群众", "几何", "添加角色", "关闭", "收起")):
                    continue
                preset_btn = b
                break
            audit["选中的预设"] = preset_btn
            if preset_btn:
                page.mouse.click(preset_btn["x"] + preset_btn["w"] / 2,
                                 preset_btn["y"] + preset_btn["h"] / 2)
                page.wait_for_timeout(3_000)
                after = page.evaluate(SNAP)
                audit["点预设后"] = diff(base["buttons"], after["buttons"])
                audit["点预设后"]["textLen前"] = base["textLen"]
                audit["点预设后"]["textLen后"] = after["textLen"]
                audit["点预设后"]["dialogs"] = after["dialogs"]
                audit["点预设后"]["textTail"] = after["textTail"]
                page.screenshot(path=str(IMG / "862src_after_preset.png"))
        except Exception:
            audit["异常"] = traceback.format_exc()[-1800:]
        finally:
            browser.close()

    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "source-862-character-preset.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=1)[:4500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
