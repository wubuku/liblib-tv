#!/usr/bin/env python3
"""Batch 796 取证（二）：画布 chrome **容器**几何 —— 同一段 evaluate 跑两侧。

为什么要单独量容器：上一轮只比了"内层控件"的矩形，得出"右边距 12→16"这种
**错误结论** —— 源站顶栏 pill 右边距本来就是 12，是内层 4px padding 让最后一个
控件显得靠左。控件矩形 ≠ 容器矩形，比错了会照着假结论去改。
所以这里只认"带非透明背景的祖先容器"，控件位置作为附加信息。

用法（源站，需登录态）:
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
        scripts/jimeng_chrome_probe.py <source|clone> <url>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

VIEWPORT = {"width": 1680, "height": 826}

EXTRACT = """(anchor) => {
  const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
  const vis = (el) => {
    const b = el.getBoundingClientRect();
    if (b.width < 1 || b.height < 1) return false;
    for (let p = el; p; p = p.parentElement) {
      const s = getComputedStyle(p);
      if (s.visibility === 'hidden' || s.display === 'none') return false;
    }
    return true;
  };
  const r = (el) => {
    const b = el.getBoundingClientRect();
    return { x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height) };
  };
  const props = (el, ps) => {
    if (!el) return null;
    const s = getComputedStyle(el); const o = {};
    ps.forEach((p) => { o[p] = s[p]; });
    return o;
  };
  const all = [...document.querySelectorAll('button,[role=button],[aria-label]')].filter(vis);
  const byLb = (lb) => all.find((b) => norm(b.getAttribute('aria-label')) === lb);

  // 从锚点控件向上找"带背景的 chrome 容器"（第一个非透明 backgroundColor）
  const chrome = (el) => {
    let n = el;
    for (let i = 0; i < 8 && n; i++) {
      const bg = getComputedStyle(n).backgroundColor;
      // 必须同时认 rgba() 和 color(srgb …) 两种记法：源站 Tailwind v4 大量使用
      // 后者（如 rail 外壳 color(srgb 0.12549 0.12549 0.12549)）。早期只匹配
      // rgba() 会一路 walk 到页面底色，误判成「源站 rail 没有底色」。
      const m = /^rgba?\\(([^)]+)\\)$/.exec(bg) || /^color\\(srgb\\s+([^)]+)\\)$/.exec(bg);
      const alpha = m ? (m[1].trim().split(/[\\s,/]+/)[3] || '1').trim() : '1';
      if (m && parseFloat(alpha) > 0.02) {
        return {
          rect: r(n),
          style: props(n, ['backgroundColor', 'borderRadius', 'padding', 'gap', 'backdropFilter', 'boxShadow']),
          depth: i,
        };
      }
      n = n.parentElement;
    }
    return null;
  };

  const txt = byLb(anchor.rail);
  const um = byLb(anchor.topRight);
  const zoom = byLb(anchor.zoom) || byLb('缩放');
  const chat = byLb(anchor.chat);

  // 工具栏按钮内部图标
  const iconOf = (b) => {
    if (!b) return null;
    const s = b.querySelector('svg');
    return s ? { rect: r(s), style: props(s, ['width', 'height', 'strokeWidth']) } : null;
  };

  // 导演台→资产库 之间的兄弟（分隔用的额外间距从哪来）
  const dir = byLb('导演台'), ast = byLb('资产库');
  const between = [];
  if (dir && ast) {
    let cur = dir.nextElementSibling;
    while (cur && cur !== ast) {
      between.push({ tag: cur.tagName.toLowerCase(), rect: r(cur), style: props(cur, ['height', 'backgroundColor', 'marginTop', 'flexShrink']) });
      cur = cur.nextElementSibling;
    }
  }

  return {
    url: location.href,
    viewport: { w: innerWidth, h: innerHeight },
    rail: { btn: txt ? { rect: r(txt), style: props(txt, ['borderRadius', 'backgroundColor', 'color']) } : null,
            icon: iconOf(txt), chrome: chrome(txt) },
    topRight: { btn: um ? r(um) : null, chrome: chrome(um) },
    dock: { zoom: zoom ? r(zoom) : null, chrome: chrome(zoom) },
    chat: chat ? { rect: r(chat), style: props(chat, ['borderRadius', 'backgroundColor', 'color', 'fontSize']) } : null,
    between,
  };
}"""

ANCHORS = {
    "source": {"rail": "文本", "topRight": "用户菜单", "zoom": "Zoom options, 100%", "chat": "与 AI 对话"},
    "clone": {"rail": "文本", "topRight": "用户菜单", "zoom": "缩放", "chat": "与 AI 对话"},
}


def run(page, mode: str, url: str) -> dict:
    page.set_viewport_size(VIEWPORT)
    if url and page.url != url:
        page.goto(url, wait_until="domcontentloaded", timeout=90_000)
    page.wait_for_timeout(11_000 if mode == "source" else 9_000)
    return page.evaluate(EXTRACT, ANCHORS[mode])


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "source"
    url = sys.argv[2] if len(sys.argv) > 2 else ""
    injected = globals().get("page")
    if injected is not None:
        d = run(injected, mode, url)
    else:
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            pg = b.new_page(viewport=VIEWPORT, locale="zh-CN")
            try:
                d = run(pg, mode, url)
            finally:
                b.close()
    out = Path(f"docs/research/jimeng-canvas-batch796-2026-10-01/chrome-{mode}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    for k in ("rail", "topRight", "dock", "chat"):
        print(f"\n[{k}]")
        print(json.dumps(d[k], ensure_ascii=False, indent=1))
    print("\n[between]", json.dumps(d["between"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
