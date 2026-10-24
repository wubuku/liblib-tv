#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 861 源站探针 · 第二版：**找到机位列表与它的删除入口**。

## ★ 第一版读到什么、缺什么

已读（决定性的一半）：
- 有机位时七格 `disabled:false`／`opacity:1`／`cursor:pointer` ✔
  （与源码 `disabled:!hasCameras` ＋ `hasCameras: rL.cameras.length>0` 一致）

★ **缺**：「无机位」时七格 `disabled:true` 的**决定性读数**
⟹ ⟹ 需要**找到并执行**删除机位的入口。

第一版的 `READ_TREE`（按 class 含 "tree" 找）**读空了**，
`删除类按钮`（按 aria-label/文本含 删除|移除|delete|remove|trash）**也读空了**
⟹ ⟹ 说明源站的删除入口**不是**这两个形状 ⟹ ⟹ 改成**全面枚举**：
① 左栏（aside）每个模式的全部文本与全部按钮的 aria-label；
② 整个页面上**全部**按钮的 aria-label／文本（去重、限量）；
③ 含「机位」「镜头」二字的元素。

## ★ 副作用声明

★ **只读**：本版**不点任何删除**（只找入口）⟹ ⟹ 无副作用。
★ **绝不点**「AI生成」「本地上传」。

## 输出
  raw/source-861-panorama-cam-entry.json
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

# ★ 全面枚举按钮（aria-label ／ title ／ 文本 ＋ 坐标）
READ_BUTTONS = r"""()=>{
  const out=[];
  const seen=new Set();
  for(const b of document.querySelectorAll('button')){
    const r=b.getBoundingClientRect();
    if(r.width===0||r.height===0) continue;
    const lbl=((b.getAttribute('aria-label')||'')+' | '+(b.title||'')+' | '+(b.textContent||''))
              .replace(/\s+/g,' ').trim().slice(0,90);
    const key=lbl+'@'+Math.round(r.x)+','+Math.round(r.y);
    if(seen.has(key)) continue; seen.add(key);
    out.push({label:lbl, disabled:b.disabled===true,
              x:Math.round(r.x),y:Math.round(r.y),
              w:Math.round(r.width),h:Math.round(r.height),
              cls:(b.getAttribute('class')||'').slice(0,70)});
  }
  return out;
}"""

# ★ 找出含「机位／镜头／相机」二字的元素
READ_CAM_WORDS = r"""()=>{
  const out=[];
  const seen=new Set();
  const all=[...document.querySelectorAll('div,span,button,li,p')];
  for(const e of all){
    const t=(e.textContent||'').trim();
    if(!t || t.length>120) continue;
    if(!/机位|镜头|相机|camera|Camera/.test(t)) continue;
    // ★ 只取**叶子**（没有子元素也含同样文本）⟹ ⟹ 避免把整棵树重复 dump
    if([...e.children].some(c=>(c.textContent||'').trim()===t)) continue;
    const key=t;
    if(seen.has(key)) continue; seen.add(key);
    const r=e.getBoundingClientRect();
    out.push({text:t, tag:e.tagName,
              x:Math.round(r.x),y:Math.round(r.y),
              w:Math.round(r.width),h:Math.round(r.height),
              cls:(e.getAttribute('class')||'').slice(0,70)});
  }
  return out.slice(0,80);
}"""

# ★ 左栏（aside）结构
READ_ASIDE = r"""()=>{
  const aside=document.querySelector('aside');
  if(!aside) return null;
  const r=aside.getBoundingClientRect();
  return {
    rect:{x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)},
    text:(aside.textContent||'').replace(/\s+/g,' ').trim().slice(0,1200),
    buttons:[...aside.querySelectorAll('button')].map(b=>{
      const br=b.getBoundingClientRect();
      return {label:((b.getAttribute('aria-label')||'')+' | '+(b.title||'')+' | '+(b.textContent||'')).replace(/\s+/g,' ').trim().slice(0,60),
              disabled:b.disabled===true,
              x:Math.round(br.x),y:Math.round(br.y),
              w:Math.round(br.width),h:Math.round(br.height)};
    }),
  };
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


def main() -> int:
    audit: dict = {"batch": 861, "probe": "source861_cam_entry"}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            load_cookies(page)
            page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(6_000)
            open_desk(page)

            audit["左栏_default"] = page.evaluate(READ_ASIDE)
            audit["按钮_default"] = page.evaluate(READ_BUTTONS)
            audit["机位字样_default"] = page.evaluate(READ_CAM_WORDS)

            # ★ 进「机位」模式（camera）看面板
            page.locator(
                "[aria-label='添加机位'], button:has-text('添加机位')"
            ).first.click(timeout=15_000)
            page.wait_for_timeout(1_500)
            audit["左栏_camera"] = page.evaluate(READ_ASIDE)
            audit["按钮_camera"] = page.evaluate(READ_BUTTONS)
        except Exception:
            audit["异常"] = traceback.format_exc()[-1500:]
        finally:
            browser.close()

    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "source-861-panorama-cam-entry.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print("★ 已写 raw/source-861-panorama-cam-entry.json")
    print("异常:", audit.get("异常"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
