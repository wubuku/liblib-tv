"""batch 794 取证：源站顶栏 10 个控件的视觉构成（几何 + 样式 + 内部结构）。

只读。不点击、不输入、不触发任何计费动作。
"""

import json

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
  const TARGETS = [
    'canvas-project-logo',
    'canvas-project-title-trigger',
    'canvas-project-trigger',
    'canvas-node-summary-trigger',
    'canvas-share-trigger',
    'canvas-commerce-entry',
    'canvas-user-menu-trigger',
  ];

  const describe = (el) => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    // 直接子元素里的 svg 尺寸 + 路径数，用来判断图标规格
    const svgs = [...el.querySelectorAll('svg')].slice(0, 4).map((v) => {
      const vr = v.getBoundingClientRect();
      return {
        w: +vr.width.toFixed(1), h: +vr.height.toFixed(1),
        paths: v.querySelectorAll('path,circle,rect,line,polyline').length,
        stroke: getComputedStyle(v).stroke,
      };
    });
    return {
      aria: el.getAttribute('aria-label'),
      testid: el.getAttribute('data-testid'),
      tag: el.tagName.toLowerCase(),
      cls: (el.className || '').toString().replace(/\\s+/g, ' ').slice(0, 260),
      text: norm(el.innerText),
      title: el.getAttribute('title'),
      rect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
      style: {
        bg: s.backgroundColor,
        radius: s.borderRadius,
        border: s.borderTopWidth + ' ' + s.borderTopStyle + ' ' + s.borderTopColor,
        color: s.color,
        font: s.fontSize + '/' + s.lineHeight + ' w' + s.fontWeight,
        padding: s.padding,
        gap: s.gap,
        display: s.display,
        align: s.alignItems,
        justify: s.justifyContent,
        shadow: s.boxShadow,
        backdrop: s.backdropFilter,
      },
      svgs,
    };
  };

  const out = { found: {}, topbarContainers: [] };

  for (const t of TARGETS) {
    const el = document.querySelector(`[data-testid="${t}"]`);
    if (el) out.found[t] = describe(el);
  }
  // 无 testid 的两个：分享右侧的「更多」和 panel-launcher 组
  for (const el of document.querySelectorAll('header button, [class*="chrome" i] button')) {
    const a = el.getAttribute('aria-label') || '';
    if (a === '更多' && !out.found.more) out.found.more = describe(el);
  }
  const launchers = document.querySelectorAll('[data-testid="canvas-panel-launcher"]');
  launchers.forEach((el, i) => { out.found['panel-launcher-' + i] = describe(el); });

  // 顶栏容器：找出包住这些控件的共同祖先，量它的药丸背景
  const first = document.querySelector('[data-testid="canvas-project-logo"]');
  if (first) {
    let p = first.parentElement, hops = 0;
    while (p && hops < 6) {
      const r = p.getBoundingClientRect();
      const s = getComputedStyle(p);
      out.topbarContainers.push({
        depth: hops,
        cls: (p.className || '').toString().replace(/\\s+/g, ' ').slice(0, 200),
        rect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
        bg: s.backgroundColor, radius: s.borderRadius, display: s.display,
        gap: s.gap, padding: s.padding, backdrop: s.backdropFilter,
        border: s.borderTopWidth + ' ' + s.borderTopColor,
      });
      p = p.parentElement; hops++;
    }
  }
  return out;
}"""
)

print(json.dumps(data, ensure_ascii=False, indent=2))
