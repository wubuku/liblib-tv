#!/usr/bin/env python3
"""FrameOS 源站状态探针 (Batch 327 起)。

只读探针：不点击任何生成/付费按钮，不创建/删除/移动节点。
用途：确认 (1) 登录态 (2) 画布健康 (节点数/缩放) (3) 顶层结构基线，
作为每轮增量采样前的守卫——源站故障时不要浪费采样窗口。

优先连接用户已开的有头 CDP 浏览器 (:9222，保留登录态)；
不可用时回退到 playwright 持久化上下文 (~/libtv-cdp-profile)。

Run: ~/.venvs/liblib-harness/bin/python scripts/probe-frameos-source.py
"""

import json
import sys

from playwright.sync_api import sync_playwright

CANVAS_URL = (
    "https://www.frameos.cn/#/canvas/01KT17B610DG417X8Q76QZSN8Z/"
    "01KWS3TK5BTEH7680N4W9JW4KW"
)

STATE_JS = """
() => {
  const nodes = [...document.querySelectorAll('.react-flow__node')];
  const pane = document.querySelector('.react-flow__viewport');
  const t = (sel) => document.querySelector(sel)?.innerText?.trim() ?? null;
  return {
    url: location.href,
    title: document.title,
    zoom: pane ? (pane.style.transform || '') : null,
    nodeCount: nodes.length,
    nodes: nodes.map((n) => {
      const r = n.getBoundingClientRect();
      return {
        id: n.getAttribute('data-id'),
        cls: (n.className || '').toString().replace(/\\s+/g, ' ').slice(0, 90),
        w: Math.round(r.width),
        h: Math.round(r.height),
        text: (n.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 40),
      };
    }),
    minimap: !!document.querySelector('[class*=minimap]'),
    groups: document.querySelectorAll('.canvas-group').length,
    bodyText: (document.body.innerText || '').replace(/\\s+/g, ' ').slice(0, 300),
  };
}
"""


def main() -> int:
    with sync_playwright() as p:
        page = None
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222", timeout=15000)
            ctx = browser.contexts[0]
            page = next((pg for pg in ctx.pages if "frameos.cn" in pg.url), None)
            if page is None:
                page = ctx.new_page()
                print("NOTE: no frameos.cn tab; opened a new one in the CDP browser")
        except Exception as exc:  # noqa: BLE001
            print(f"NOTE: CDP unavailable ({exc}); falling back to persistent context")
            ctx = p.chromium.launch_persistent_context(
                "/Users/yangjiefeng/libtv-cdp-profile",
                headless=True,
                args=["--no-first-run", "--no-default-browser-check"],
            )
            page = ctx.new_page()

        page.goto(CANVAS_URL, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(18000)
        page.set_viewport_size({"width": 1920, "height": 1150})
        page.wait_for_timeout(2000)

        state = page.evaluate(STATE_JS)
        print("=== FRAMEOS SOURCE STATE ===")
        print(json.dumps(state, ensure_ascii=False, indent=2)[:4000])

        logged_out = any(
            k in (state.get("bodyText") or "") for k in ("登录", "手机号登录", "扫码")
        )
        print(f"LOGIN_SUSPECT: {logged_out}")
        print(f"NODECOUNT: {state.get('nodeCount')}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
