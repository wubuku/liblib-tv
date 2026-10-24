#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 861 源站探针 · 第三版：**决定性读数** —— 无机位时七格是不是 `disabled:true`。

## ★ 已有证据（前两版）

① 源站逐字：`hasCameras: rL.cameras.length > 0` ＋ aspect 段 `disabled:!a`
   ＋ 类名含 `disabled:cursor-not-allowed disabled:opacity-35`；
② 运行时（第一版）：**有机位**时七格 `disabled:false`／`opacity:1`／`cursor:pointer`；
③ 运行时（第二版）：左栏 scene 模式里有「**机位1**」「**机位2**」两行，
   每行只有「隐藏」「锁定」两个按钮 ⟹ ⟹ **可见 UI 里没有删除按钮**。

★ 所以第三版要试的**两种结果都有价值**：
- **A** 删除可行 ⟹ ⟹ 删光机位 ⟹ ⟹ 读七格 `disabled`（**决定性**）⟹ ⟹ 再加回机位复原；
- **B** 删除不可行 ⟹ ⟹ 源站的「无机位」状态**不可达** ⟹ ⟹ `disabled:!hasCameras`
  这个分支在源站**永不触发** ⟹ ⟹ 差异只登记、**不改 clone**。

★ 无论 A/B，都必须**复原**（加回机位）并记录复原读数。

## ★ 副作用声明

★ 会**尝试删除源站机位**（测试账号 ⟹ 允许有副作用的 CRUD）⟹ ⟹ 结束前复原。
★ **绝不点**「AI生成」「本地上传」「添加角色」（真实生图/上传）。

## 输出
  raw/source-861-no-camera.json
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

READ_OPTIONS = r"""()=>{
  const all=[...document.querySelectorAll('button')];
  return all.filter(b=>/^(21:9|16:9|4:3|1:1|3:4|9:16|自适应)$/.test((b.textContent||'').trim()))
    .map(b=>{ const cs=getComputedStyle(b);
      return {text:(b.textContent||'').trim(), disabled:b.disabled===true,
              opacity:cs.opacity, cursor:cs.cursor}; });
}"""

# ★ 左栏 scene 模式的文本（看机位还在不在）
READ_ASIDE_TEXT = r"""()=>{
  const aside=document.querySelector('aside');
  if(!aside) return null;
  return (aside.textContent||'').replace(/\s+/g,' ').trim().slice(0,600);
}"""

# ★ 机位行附近的所有按钮（选中后可能冒出删除按钮）
READ_ROW_BUTTONS = r"""()=>{
  const out=[];
  for(const b of document.querySelectorAll('aside button')){
    const r=b.getBoundingClientRect();
    if(r.width===0||r.height===0) continue;
    if(r.x>290) continue;
    if(r.y<120||r.y>260) continue;
    out.push({label:((b.getAttribute('aria-label')||'')+' | '+(b.title||'')+' | '+(b.textContent||'')).replace(/\s+/g,' ').trim().slice(0,60),
              x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});
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


def open_aspect(page) -> None:
    page.locator(
        "[aria-label='选择画幅比例'], button:has-text('选择画幅比例')"
    ).first.click(timeout=15_000)
    page.wait_for_timeout(1_500)


def back_to_scene(page) -> None:
    page.locator("[aria-label='场景'], button:has-text('场景')").first.click(
        timeout=15_000)
    page.wait_for_timeout(1_200)


def main() -> int:
    audit: dict = {"batch": 861, "probe": "source861_no_camera"}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            load_cookies(page)
            page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(6_000)
            open_desk(page)

            audit["基线_左栏"] = page.evaluate(READ_ASIDE_TEXT)
            open_aspect(page)
            audit["基线_七格"] = page.evaluate(READ_OPTIONS)

            # ── 尝试删机位 1 ────────────────────────────────
            back_to_scene(page)
            audit["选中前_行按钮"] = page.evaluate(READ_ROW_BUTTONS)
            cam1 = page.locator("aside").get_by_text("机位1", exact=True).first
            cam1.click(timeout=10_000)
            page.wait_for_timeout(1_200)
            audit["选中后_行按钮"] = page.evaluate(READ_ROW_BUTTONS)
            audit["选中后_左栏"] = page.evaluate(READ_ASIDE_TEXT)

            # ★ 试 Delete 键
            page.keyboard.press("Delete")
            page.wait_for_timeout(1_500)
            audit["按Delete后_左栏"] = page.evaluate(READ_ASIDE_TEXT)
            audit["按Delete后_行按钮"] = page.evaluate(READ_ROW_BUTTONS)

            # ★ 再试 Backspace
            page.keyboard.press("Backspace")
            page.wait_for_timeout(1_500)
            audit["按Backspace后_左栏"] = page.evaluate(READ_ASIDE_TEXT)

            # ★ 有机位被删掉的话 ⟹ 进 aspect 模式读七格
            open_aspect(page)
            audit["删后_七格"] = page.evaluate(READ_OPTIONS)
            audit["删后_左栏"] = page.evaluate(READ_ASIDE_TEXT)
        except Exception:
            audit["异常"] = traceback.format_exc()[-1800:]
        finally:
            browser.close()

    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "source-861-no-camera.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    for k in ("基线_左栏", "选中后_左栏", "按Delete后_左栏", "按Backspace后_左栏", "删后_左栏"):
        print(f"{k}: {audit.get(k)}")
    print("基线_七格:", json.dumps(audit.get("基线_七格"), ensure_ascii=False)[:200])
    print("删后_七格:", json.dumps(audit.get("删后_七格"), ensure_ascii=False)[:300])
    print("异常:", audit.get("异常"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
