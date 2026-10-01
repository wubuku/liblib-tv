#!/usr/bin/env python3
"""即梦画布深度结构快照 —— 源站与复刻通用，产出可 diff 的规范化 JSON。

用法（源站，需登录态）:
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
        scripts/jimeng_deep_snapshot.py <url> <out.json>

用法（复刻，无需登录）:
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_deep_snapshot.py \
        http://localhost:4317/jimeng/canvas/demo <out.json>

设计要点：两侧 DOM 结构不同（源站是 React Flow + tailwind token，复刻是
@xyflow/react + 自有 class），所以这里**不按 class 抓**，只抓语义层：
可见交互元素的无障碍名 / 可见文本 / 屏幕矩形，加上画布节点的类型与几何。
这样同一份提取器能同时喂给两侧，diff 出来的差异就是真实复刻缺口。

只读：全程不点击、不输入、不触发任何计费动作。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

VIEWPORT = {"width": 1680, "height": 826}
SETTLE_MS = 9000


def extract(page) -> dict:
    """把整页压成一组规范化事实。纯 evaluate，无副作用。"""
    return page.evaluate(
        """() => {
      const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
      const rectOf = (el) => {
        const r = el.getBoundingClientRect();
        return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
      };
      const visible = (el) => {
        const r = el.getBoundingClientRect();
        if (r.width < 1 || r.height < 1) return false;
        const s = getComputedStyle(el);
        if (s.visibility === 'hidden' || s.display === 'none' || Number(s.opacity) === 0) return false;
        // 被祖先 visibility:hidden / display:none 关掉的一律不算可见
        for (let p = el; p; p = p.parentElement) {
          const ps = getComputedStyle(p);
          if (ps.visibility === 'hidden' || ps.display === 'none') return false;
        }
        return true;
      };
      // 交互元素：aria-label 优先，其次可见文本
      const INTERACTIVE = 'button, a[href], [role="button"], [role="menuitem"], [role="tab"], [role="switch"], input, textarea, [tabindex]:not([tabindex="-1"])';
      const items = [];
      for (const el of document.querySelectorAll(INTERACTIVE)) {
        if (!visible(el)) continue;
        const label = norm(el.getAttribute('aria-label'));
        const text = norm(el.innerText || el.value || el.getAttribute('placeholder'));
        const name = label || text;
        if (!name || name.length > 40) continue;
        items.push({
          name,
          tag: el.tagName.toLowerCase(),
          role: el.getAttribute('role') || '',
          testid: el.getAttribute('data-testid') || '',
          pressed: el.getAttribute('aria-pressed'),
          disabled: el.getAttribute('aria-disabled') === 'true' || el.disabled === true,
          rect: rectOf(el),
        });
      }
      // 同一 name 的重复项（图标钮常同名）合并，保留出现次数与首个矩形
      const byName = new Map();
      for (const it of items) {
        const key = `${it.name}|${it.testid}`;
        const prev = byName.get(key);
        if (prev) { prev.count += 1; } else { byName.set(key, { ...it, count: 1 }); }
      }
      const controls = [...byName.values()]
        .map(({ name, tag, role, testid, pressed, disabled, count, rect }) =>
          ({ name, tag, role, testid, pressed, disabled, count, rect }))
        .sort((a, b) => a.name.localeCompare(b.name, 'zh'));

      // 画布节点
      const nodeSel = '.react-flow__node, [data-id][class*="node"]';
      const nodes = [];
      for (const n of document.querySelectorAll(nodeSel)) {
        if (!visible(n)) continue;
        const cls = (n.className || '').toString();
        const type = (cls.match(/react-flow__node-([a-z]+)/) || [])[1] || '';
        nodes.push({
          id: (n.getAttribute('data-id') || '').slice(0, 40),
          type,
          cls: cls.replace(/\\s+/g, ' ').slice(0, 120),
          rect: rectOf(n),
          text: norm(n.innerText).slice(0, 200),
          hasToolbar: !!n.querySelector('.react-flow__node-toolbar'),
          toolbar: norm(n.querySelector('.react-flow__node-toolbar')?.innerText).slice(0, 160),
          mediaCount: n.querySelectorAll('img, video, canvas').length,
        });
      }

      // 画布级浮层（工具条 / 面板 / 弹层 / 菜单 / toast）
      const overlaySel = '.react-flow__node-toolbar, [role="dialog"], [role="menu"], [role="listbox"], [role="tooltip"], [class*="toast" i], [class*="panel" i], [class*="drawer" i], [class*="popover" i], [class*="dropdown" i], [class*="menu" i]';
      const overlays = [];
      for (const o of document.querySelectorAll(overlaySel)) {
        if (!visible(o)) continue;
        const t = norm(o.innerText);
        if (!t) continue;
        overlays.push({
          cls: (o.className || '').toString().replace(/\\s+/g, ' ').slice(0, 100),
          role: o.getAttribute('role') || '',
          rect: rectOf(o),
          text: t.slice(0, 220),
        });
      }

      // 关键 computed token（只取复刻文档里明确对齐过的那几个）
      const bodyStyle = getComputedStyle(document.body);
      const canvasBgEl = document.querySelector('[class*="canvas-bg" i]');
      const token = (el, prop) => (el ? getComputedStyle(el)[prop] : null);
      return {
        url: location.href,
        title: document.title,
        zoomText: (document.body.innerText.match(/(\\d{1,3})%/) || [])[0] || null,
        counts: {
          controls: controls.length,
          nodes: nodes.length,
          handles: document.querySelectorAll('.react-flow__handle').length,
          edges: document.querySelectorAll('.react-flow__edge').length,
          edgesSvg: document.querySelectorAll('svg.react-flow__edges, .react-flow__edgelabel-renderer').length,
          canvases: document.querySelectorAll('canvas').length,
          videos: document.querySelectorAll('video').length,
          images: document.querySelectorAll('img').length,
        },
        tokens: {
          bodyBg: bodyStyle.backgroundColor,
          bodyFont: bodyStyle.fontFamily,
          bodyColor: bodyStyle.color,
          canvasBg: token(canvasBgEl, 'backgroundColor'),
        },
        controls,
        nodes,
        overlays,
      };
    }"""
    )


def _run(page, url: str, out: Path, settle_ms: int = SETTLE_MS) -> int:
    # 注入模式下 page 来自 jimeng_auth.CONTEXT_OPTIONS（1512×950），与复刻的
    # 1680×826 不同，横向坐标无法直接对比。这里统一到复刻设计宽度，
    # 让两侧几何可比 —— 源站证据也一直是按 1680×826 记的。
    vw = int(os.environ.get("SNAP_VW", VIEWPORT["width"]))
    vh = int(os.environ.get("SNAP_VH", VIEWPORT["height"]))
    page.set_viewport_size({"width": vw, "height": vh})
    if url and page.url != url:
        page.goto(url, wait_until="domcontentloaded", timeout=90_000)
    page.wait_for_timeout(settle_ms)
    data = extract(page)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    c = data["counts"]
    print(f"snapshot -> {out}")
    print(f"  url={data['url']}")
    print(f"  controls={c['controls']} nodes={c['nodes']} handles={c['handles']} "
          f"edges={c['edges']} overlays={len(data['overlays'])}")
    return 0


def main() -> int:
    # 被 jimeng_headless.py run 注入时复用它的已登录 page；否则自起无头浏览器。
    injected = globals().get("page")
    out = Path(os.environ.get("SNAP_OUT") or (sys.argv[2] if len(sys.argv) > 2 else "snapshot.json"))
    url = os.environ.get("SNAP_URL") or (sys.argv[1] if len(sys.argv) > 1 else "")

    if injected is not None:
        return _run(injected, url, out, settle_ms=int(os.environ.get("SNAP_SETTLE", SETTLE_MS)))
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport=VIEWPORT, locale="zh-CN")
        try:
            return _run(page, url, out)
        finally:
            browser.close()


if __name__ == "__main__":
    sys.exit(main())
