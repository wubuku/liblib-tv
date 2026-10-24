#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 861 源站探针 · 第一版：查清「选择画幅比例」七格的 **disabled** 条件。

## ★ 为什么查这个

源站逐字（chunk `aU` 组件）：
- props 解构：`hasCameras:a, aspectRatio:l, onAspectRatioChange:d, …`
- 父组件传参：`hasCameras: rL.cameras.length > 0`
- aspect 段七格：`disabled:!a` ＋ 类名含 `disabled:cursor-not-allowed disabled:opacity-35`

⟹ ⟹ **源码推断**：源站**没有机位时，七档比例全部禁用**。

★ 但**源码只能证明这个分支存在**，不能证明运行时行为 ⟹ ⟹ 必须实测：
① **有机位**时七格的 `disabled` 读数；
② ★ **删掉机位**后七格的 `disabled` 读数（**决定性**）；
③ 复原（把机位加回去）。

## ★ 副作用声明

★ **只删机位、不上传、不生成**：删机位是可撤销的本地状态改动 ⟹ ⟹ 结束前**加回机位**复原。
★ **绝不点**「AI生成」（真实生图，付费）。
★ **绝不点**「本地上传」（会打开文件选择器并可能上传 ⟹ ⟹ 只读它的存在性）。

## 输出
  raw/source-861-aspect-disabled.json
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

# ★ 读七格比例按钮：文本就是档名（21:9 / 16:9 / …），★ 「自适应」用 aria 兜底
READ_OPTIONS = r"""()=>{
  const all=[...document.querySelectorAll('button')];
  const opt=all.filter(b=>{
    const t=(b.textContent||'').trim();
    return /^(21:9|16:9|4:3|1:1|3:4|9:16|自适应)$/.test(t);
  });
  return opt.map(b=>{
    const cs=getComputedStyle(b);
    const r=b.getBoundingClientRect();
    return {
      text:(b.textContent||'').trim(),
      disabled:b.disabled===true,
      ariaDisabled:b.getAttribute('aria-disabled'),
      opacity:cs.opacity,
      cursor:cs.cursor,
      borderColor:cs.borderColor,
      rect:{x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)},
    };
  });
}"""

# ★ 读「场景树」里有哪些行、每行有哪些按钮（找机位与删除入口）
READ_TREE = r"""()=>{
  const rows=[...document.querySelectorAll('[class*="tree"] , [data-testid]')]
    .filter(e=>/tree/i.test((e.getAttribute('class')||'')));
  const out=[];
  const seen=new Set();
  for(const e of rows){
    if(seen.has(e)) continue; seen.add(e);
    const t=(e.textContent||'').trim();
    if(!t || t.length>400) continue;
    out.push({
      cls:(e.getAttribute('class')||'').slice(0,90),
      text:t.slice(0,160),
      buttons:[...e.querySelectorAll('button')].map(b=>({
        label:(b.getAttribute('aria-label')||b.title||b.textContent||'').trim().slice(0,40),
        disabled:b.disabled===true})),
    });
    if(out.length>40) break;
  }
  return out;
}"""

# ★ 读页面上所有「看起来像删除/垃圾桶」的按钮
READ_DELETE_ENTRIES = r"""()=>{
  const btns=[...document.querySelectorAll('button')];
  const hits=btns.filter(b=>{
    const l=((b.getAttribute('aria-label')||'')+' '+(b.title||'')+' '+(b.textContent||'')).trim();
    return /删除|移除|delete|remove|trash|垃圾桶/i.test(l);
  });
  return hits.map(b=>{
    const r=b.getBoundingClientRect();
    return {label:((b.getAttribute('aria-label')||'')+' '+(b.title||'')+' '+(b.textContent||'')).trim().slice(0,60),
            disabled:b.disabled===true,
            x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};
  });
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
    """进「选择画幅比例」模式。"""
    page.locator(
        "[aria-label='选择画幅比例'], button:has-text('选择画幅比例')"
    ).first.click(timeout=15_000)
    page.wait_for_timeout(1_500)


def main() -> int:
    audit: dict = {"batch": 861, "probe": "source861_aspect_disabled"}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            load_cookies(page)
            page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(6_000)
            open_desk(page)
            audit["导演台已开"] = True

            # ① 先在「场景树」模式下找机位与删除入口
            audit["场景树行"] = page.evaluate(READ_TREE)
            audit["删除类按钮"] = page.evaluate(READ_DELETE_ENTRIES)

            # ② 有机位时的七格读数
            open_aspect(page)
            audit["有机位_七格"] = page.evaluate(READ_OPTIONS)
        except Exception:
            audit["异常"] = traceback.format_exc()[-1500:]
        finally:
            browser.close()

    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "source-861-aspect-disabled.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=1)[:4_000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
