"""batch 794 取证：源站节点标题行的「资源处理三态状态行」精确结构。

只读。不点击、不输入、不触发计费动作。

跑法（注入已登录 page）:
    SNAP_URL=<画布地址> ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py \
        run scripts/jimeng_probe794_titlerow.py
"""

import json
import os

URL = os.environ.get(
    "SNAP_URL",
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
)

page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
page.wait_for_timeout(10_000)

data = page.evaluate(
    """() => {
  const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
  const node = document.querySelector('.react-flow__node');
  if (!node) return { error: 'no node' };

  // 逐层剥出标题行：节点内 aria-label 最短、位于节点顶部的那块
  const walk = (el, depth, out) => {
    if (depth > 7) return;
    for (const c of el.children) {
      const r = c.getBoundingClientRect();
      if (r.width < 1 || r.height < 1) continue;
      const s = getComputedStyle(c);
      out.push({
        depth,
        tag: c.tagName.toLowerCase(),
        cls: (c.className || '').toString().replace(/\\s+/g, ' ').slice(0, 110),
        aria: c.getAttribute('aria-label'),
        title: c.getAttribute('title'),
        text: norm(c.innerText).slice(0, 120),
        rect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
        font: s.font || (s.fontSize + '/' + s.lineHeight),
        color: s.color,
        bg: s.backgroundColor,
        pos: s.position,
        trunc: s.textOverflow,
        ws: s.whiteSpace,
        maxW: s.maxWidth,
      });
      walk(c, depth + 1, out);
    }
  };
  const tree = [];
  walk(node, 0, tree);

  // 只保留节点顶部 60px 内的条目 —— 标题行就在那儿
  const nr = node.getBoundingClientRect();
  const topBand = tree.filter((t) => t.rect.y < nr.y + 60);

  return {
    nodeText: norm(node.innerText),
    nodeAria: node.getAttribute('aria-label'),
    nodeAriaDescribedBy: !!node.getAttribute('aria-describedby'),
    topBand,
    // 状态行候选：文本里含 ready/processing/failed 的最内层元素
    statusCandidates: tree
      .filter((t) => /ready|processing|failed|resource/i.test(t.text || '') || /ready|processing|failed|resource/i.test(t.aria || ''))
      .map((t) => ({ depth: t.depth, cls: t.cls, text: t.text, aria: t.aria, color: t.color, font: t.font, rect: t.rect })),
  };
}"""
)

print(json.dumps(data, ensure_ascii=False, indent=2))
