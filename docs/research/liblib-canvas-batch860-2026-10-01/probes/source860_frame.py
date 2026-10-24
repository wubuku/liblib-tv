#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 860 源站探针 · 第三版：查清「机位取景框」**在哪种模式下可见**。

## ★ 为什么要第三版

第二版测出：源站点「21:9」后冒出一个
`outline-white/18 absolute rounded-xl outline -outline-offset-1` 的
1262×541 框（ratio **2.3334** ≈ 21:9），而**画布容器三态恒定**。

★ 但**还有两个没查清的点** ⟹ ⟹ 查不清就不能定判据：
① 这个框**在哪种视图模式下**可见？（导演视角／机位视角）
② 源站逐字：`o$` 里是 `let t = e1 || rL.cameras[0]?.id` ⟹ ⟹ 事件发给**机位**
   ⟹ ⟹ 那框大概是**当前机位**的取景框 ⟹ ⟹ 有没有机位时它什么样？

## ★ 本探针要读到的

① 三个视图模式（导演视角／机位视角／…）下，框在不在场；
② 每个模式下**框的矩形** ＋ 描边 alpha；
③ ★ 「自适应」在源站到底是不是**无框**（第二版看到不在场 ⟹ ⟹ 要复核）；
④ ★ 「16:9」「1:1」「9:16」三档的框**各是多少**（要数值，不要推断）。

## ★ 副作用声明

点比例只改机位参数（不付费）；结束前**点回「自适应」复原**；★ **绝不点**「AI生成」。

## 输出
  raw/source-860-frame.json
"""
from __future__ import annotations

import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch860-2026-10-01"
RAW = BATCH / "raw"

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 找取景框：按**结构特征**（outline ＋ rounded-xl ＋ absolute）⟹ ⟹ 不靠猜
READ_FRAME = r"""()=>{
  const rect=(e)=>{ if(!e) return null; const r=e.getBoundingClientRect();
    return {x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width),
            h:Math.round(r.height),
            ratio: r.height>0 ? +(r.width/r.height).toFixed(4) : null,
            border:getComputedStyle(e).borderColor,
            outline:getComputedStyle(e).outlineColor,
            outlineWidth:getComputedStyle(e).outlineWidth}; };
  const all=[...document.querySelectorAll('div')];
  const frames=all.filter(e=>{
    const c=(e.className||'').toString();
    return c.indexOf('outline-white')>=0 && c.indexOf('rounded-xl')>=0
           && c.indexOf('absolute')>=0;
  }).filter(e=>{ const r=e.getBoundingClientRect();
                  return r.width>200 && r.height>100; });
  // ★ 视图模式按钮（源站顶栏）
  const modeBtns=[...document.querySelectorAll('button')].filter(b=>{
    const t=(b.getAttribute('aria-label')||'')+' '+(b.textContent||'');
    return /导演视角|机位视角|自由视角/.test(t);
  }).map(b=>({label:(b.getAttribute('aria-label')||b.textContent||'').trim(),
              pressed:b.getAttribute('aria-pressed'),
              x:Math.round(b.getBoundingClientRect().x),
              y:Math.round(b.getBoundingClientRect().y)}));
  const canvasBox=all.find(e=>{
    const c=(e.className||'').toString().trim();
    return c==='h-full w-full' && e.querySelector('canvas');
  });
  return {
    取景框: frames.map(f=>({rect:rect(f),
      cls:(f.className||'').toString().slice(0,120)})),
    视图模式按钮: modeBtns,
    画布容器: canvasBox?rect(canvasBox):null,
  };
}"""


def open_desk(page) -> None:
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(600)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')"
    ).first.click()
    page.wait_for_timeout(8_000)


def click_ratio(pg, label: str) -> None:
    pg.locator("button", has_text=label).first.click(timeout=15_000)
    pg.wait_for_timeout(2_200)


def main() -> int:
    out: dict = {}
    try:
        cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            ctx.add_cookies([{"name": c["name"], "value": c["value"],
                              "domain": c["domain"], "path": c.get("path", "/")}
                             for c in cookies])
            pg = ctx.new_page()
            pg.set_default_timeout(20_000)
            pg.goto(URL, wait_until="domcontentloaded", timeout=90_000)
            pg.wait_for_timeout(12_000)
            el = pg.query_selector("text=下次再说")
            if el:
                el.click()
                pg.wait_for_timeout(900)
            open_desk(pg)
            if pg.query_selector("[data-director-practice-escape]"):
                pg.keyboard.press("Escape")
                pg.wait_for_timeout(900)

            # 切到画幅比例面板
            pg.locator("button[aria-label='选择画幅比例']").first.click(timeout=15_000)
            pg.wait_for_timeout(1_500)

            # ① 基线（自适应）
            out["①自适应"] = pg.evaluate(READ_FRAME)

            # ② 逐档：21:9 / 16:9 / 4:3 / 1:1 / 3:4 / 9:16
            for label in ["21:9", "16:9", "4:3", "1:1", "3:4", "9:16"]:
                click_ratio(pg, label)
                out[f"②{label}"] = pg.evaluate(READ_FRAME)

            # ③ 切到「机位视角」⟹ ⟹ 看框在不在
            mode_btns = out["①自适应"]["视图模式按钮"]
            out["③视图模式按钮"] = mode_btns
            cam_mode = None
            for b in mode_btns:
                if "机位" in b["label"]:
                    cam_mode = b
                    break
            if cam_mode:
                pg.mouse.click(cam_mode["x"] + 16, cam_mode["y"] + 16)
                pg.wait_for_timeout(2_500)
                out["④机位视角下"] = pg.evaluate(READ_FRAME)
                # ★ 机位视角下再点 21:9
                click_ratio(pg, "21:9")
                out["⑤机位视角+21比9"] = pg.evaluate(READ_FRAME)

            # ★ 复原：回自适应 ＋ 回导演视角
            click_ratio(pg, "自适应")
            out["⑥复原后"] = pg.evaluate(READ_FRAME)

            pg.close()
            br.close()
    except Exception:  # noqa: BLE001
        out["★异常"] = traceback.format_exc()[-2500:]
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "source-860-frame.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2)[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
