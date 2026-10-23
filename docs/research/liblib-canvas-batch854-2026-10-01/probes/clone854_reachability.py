#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 854 探针（**可达性**）：克隆成果**从克隆站根目录**能不能「用户可达」。

## ★ 为什么要有这个探针

★ 目标里新加了一条硬要求：**所有完成的克隆成果（页面）都必须通过克隆网站根目录
★ 「用户可达」，并且文档中说明如何「可达」、用户可以如何进行交互测试。**
★ ⟹ ⟹ 光写文档不算数 ⟹ ⟹ 得**真的从根地址点进去**。

## ★ 测法（**只用真实用户动作**）

1. 打开 **`http://localhost:4317/`**（★ **不带任何查询参数** ⟹ ⟹ 不能靠
   `?batch852=1` 之类的参数「开的后门」）
2. 等画布渲染完
3. 记录根页上**所有**能通向克隆成果的入口（按可见文本／data 属性找）
4. 逐个真的点进去 ⟹ ⟹ 记录落地页是什么
5. 记录每个落地页上**能交互**的元素（按钮／开关／树行…）⟹ ⟹ 供文档写「怎么测」

## 输出
  raw/clone-854-reachability.json
  images/854reach_*.png
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch854-2026-10-01"
RAW = BATCH / "raw"
SHOTS = BATCH / "images"
BASE = "http://localhost:4317"

# ★ 根页上「能通向导演台」的入口：脚本执行节点里的「打开导演台」按钮
READ_ENTRIES = r"""()=>{
  const out = [];
  document.querySelectorAll('button, [role="button"], a').forEach(e=>{
    const r = e.getBoundingClientRect();
    if(r.width<=0||r.height<=0) return;
    const t = (e.textContent||'').trim();
    const da = e.getAttribute('data-open-director');
    if(!t && !da) return;
    out.push({text:t.slice(0,40), dataOpenDirector:da,
              x:Math.round(r.x), y:Math.round(r.y),
              w:Math.round(r.width), h:Math.round(r.height)});
  });
  out.sort((a,b)=>(a.y-b.y)||(a.x-b.x));
  return out;
}"""

# ★ 落地页上的「可交互元素」清单（供文档写「用户可以怎么测」）
READ_INTERACTIVE = r"""()=>{
  const pick = (sel) => Array.from(document.querySelectorAll(sel)).map(e=>{
    const r = e.getBoundingClientRect();
    if(r.width<=0||r.height<=0) return null;
    return {sel:sel, text:(e.textContent||'').trim().slice(0,32),
            aria:e.getAttribute('aria-label')||'', x:Math.round(r.x), y:Math.round(r.y)};
  }).filter(Boolean);
  const out = [];
  ['[data-open-director]','[data-director-tree]','[data-director-object-id]',
   '[data-director-group-action]','[data-director-rail-entry]',
   '[data-director-transform-mode]','[data-director-scene-snap-to-grid]',
   '[data-director-selection-count]','[data-director-inspector-kind]',
   '[role="switch"]','[role="tab"]'].forEach(sel=>{ out.push(...pick(sel)); });
  return out;
}"""


def main() -> int:
    out = {}
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            pg = ctx.new_page()
            pg.set_default_timeout(30_000)

            # ★ ① 根地址（**不带任何参数**）
            pg.goto(BASE + "/", wait_until="domcontentloaded")
            pg.wait_for_timeout(4000)
            pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
            pg.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
            pg.wait_for_timeout(1500)
            out["①根地址"] = BASE + "/"
            out["①根页URL"] = pg.url
            out["①根页标题"] = pg.title()
            out["①根页节点数"] = pg.evaluate(
                "() => document.querySelectorAll('.react-flow__node').length")
            out["①根页入口"] = pg.evaluate(READ_ENTRIES)
            shot(pg, "01-root")

            # ★ ② 真实用户动作：hover 脚本执行节点 ⟹ 点「打开导演台」
            node = pg.locator(".react-flow__node-script-execution").first
            ok_node = node.count() > 0
            out["②有脚本执行节点"] = ok_node
            if ok_node:
                try:
                    node.scroll_into_view_if_needed(timeout=8000)
                except Exception:
                    pass
                pg.wait_for_timeout(400)
                try:
                    node.hover(timeout=8000)
                    pg.wait_for_timeout(700)
                except Exception:
                    pass
                out["②hover后入口"] = pg.evaluate(READ_ENTRIES)
                btn = pg.locator("[data-open-director]").first
                out["②有打开导演台按钮"] = btn.count() > 0
                if out["②有打开导演台按钮"]:
                    btn.click(timeout=15000)
                    pg.wait_for_timeout(6000)
                    pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
                    out["③导演台URL"] = pg.url
                    out["③导演台有树"] = pg.evaluate(
                        "() => Boolean(document.querySelector('[data-director-tree]'))")
                    out["③导演台有对象树行"] = pg.evaluate(
                        "() => document.querySelectorAll('[data-director-object-id]').length")
                    out["③导演台有rail"] = pg.evaluate(
                        "() => document.querySelectorAll('[data-director-rail-entry]').length")
                    out["③导演台可交互元素"] = pg.evaluate(READ_INTERACTIVE)
                    shot(pg, "02-director")
            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        RAW.mkdir(parents=True, exist_ok=True)
        (RAW / "clone-854-reachability.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", RAW / "clone-854-reachability.json")
        if out.get("异常"):
            print("异常：", out["异常"][-800:])
        print("根页 URL     :", out.get("①根页URL"))
        print("根页节点数   :", out.get("①根页节点数"))
        print("根页入口     :", json.dumps(out.get("①根页入口"), ensure_ascii=False)[:600])
        print("有脚本节点   :", out.get("②有脚本执行节点"))
        print("有打开导演台 :", out.get("②有打开导演台按钮"))
        print("导演台有树   :", out.get("③导演台有树"))
        print("导演台对象行 :", out.get("③导演台有对象树行"))
        print("导演台 rail  :", out.get("③导演台有rail"))
        ie = out.get("③导演台可交互元素") or []
        print("可交互元素数 :", len(ie))
        for e in ie[:18]:
            print("   ", json.dumps(e, ensure_ascii=False))
    return 0


def shot(pg, name):
    SHOTS.mkdir(parents=True, exist_ok=True)
    p = SHOTS / ("854reach_%s.png" % name)
    pg.screenshot(path=str(p))
    return p


if __name__ == "__main__":
    sys.exit(main())
