"""batch 795 取证（补）：源站「用户菜单」到底在不在 chrome 药丸内？

batch 794 里我曾据按钮自身 `border: 0px none` 判定「用户菜单不在药丸内」，
并据此改了 batch 96。但实测几何对不上：源站顶栏容器右缘 1668，而用户菜单
右缘 1664（正好内缩 4px）—— 这更像 p-1 药丸的 4px 内边距。故复查其祖先链
的背景/圆角/内边距。

只读。
"""

URL = (
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create"
)

page.set_viewport_size({"width": 1680, "height": 826})
page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
page.wait_for_timeout(10_000)

data = page.evaluate(
    """() => {
  const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
  const out = {};
  const chain = (sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const rows = [];
    for (let p = el, i = 0; p && i < 5; p = p.parentElement, i++) {
      const r = p.getBoundingClientRect();
      const s = getComputedStyle(p);
      rows.push({
        depth: i,
        cls: (p.className || '').toString().replace(/\\s+/g, ' ').slice(0, 110),
        aria: p.getAttribute('aria-label'),
        rect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
        bg: s.backgroundColor,
        radius: s.borderRadius,
        padding: s.padding,
        backdrop: s.backdropFilter,
        shadow: s.boxShadow.slice(0, 80),
      });
    }
    return rows;
  };
  out.userMenu = chain('[data-testid="canvas-user-menu-trigger"]');
  out.search = chain('[data-testid="canvas-panel-launcher"]');
  out.credits = chain('[data-testid="canvas-commerce-entry"]');
  out.share = chain('[data-testid="canvas-share-trigger"]');
  return out;
}"""
)

import json  # noqa: E402
print(json.dumps(data, ensure_ascii=False, indent=2))
