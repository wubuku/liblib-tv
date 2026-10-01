"""batch 835 取证补刀：面板顶部「仅支持新建一个空会话」这句话挂在谁身上。

2026-10-04 首轮普查在面板 innerText 里读到「新会话 仅支持新建一个空会话」，
但没说清它是**按钮 title/tooltip**、**空态文案**还是别的。这条对 834 很关键：
复刻做的是**真·多会话**，而源站的文案像是在说「只支持一条空会话」。
先把它定位清楚，再决定台账怎么写。

用法：
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
        scripts/jimeng_835_panel_probe.py
"""

from __future__ import annotations

import json
from pathlib import Path

OUT_DIR = Path("docs/research/jimeng-canvas-batch835-2026-10-04")
URL = (
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create"
)

# 找出含目标文案的元素，并报告它自己是哪一层（tag / 属性 / 尺寸）
LOCATE_JS = """(needle) => {
  const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const out = [];
  let n;
  while ((n = walk.nextNode())) {
    if (!(n.nodeValue || '').includes(needle)) continue;
    let el = n.parentElement;
    const chain = [];
    for (let i = 0; el && i < 4; i++, el = el.parentElement) {
      const b = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      chain.push({
        tag: el.tagName, tid: el.getAttribute('data-testid') || '',
        al: el.getAttribute('aria-label') || '', title: el.getAttribute('title') || '',
        cls: (el.className && String(el.className).slice(0, 60)) || '',
        rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
        display: cs.display, visibility: cs.visibility, text: (el.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 70),
      });
    }
    out.push({ needle, chain });
  }
  return out;
}"""

# 面板完整可访问文本 + 所有 testid（面板内）
PANEL_JS = """() => {
  const cands = [...document.querySelectorAll('div')].filter((el) => {
    const b = el.getBoundingClientRect();
    return Math.abs(b.width - 398) < 10 && b.x > innerWidth - 460 && b.height > 800;
  });
  if (!cands.length) return null;
  const el = cands[0];
  return {
    text: (el.innerText || '').replace(/\\n{2,}/g, '\\n').trim(),
    tids: [...el.querySelectorAll('[data-testid]')].map((n) => {
      const b = n.getBoundingClientRect();
      return { tid: n.getAttribute('data-testid'), al: n.getAttribute('aria-label') || '',
               expanded: n.getAttribute('aria-expanded'), disabled: n.getAttribute('aria-disabled'),
               rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)] };
    }),
  };
}"""


def main() -> int:
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    for _ in range(24):
        if not page.evaluate("() => document.body.innerText.includes('Loading canvas')"):
            break
        page.wait_for_timeout(2000)
    page.wait_for_timeout(2000)
    # 打开面板（不消耗积分）
    page.click('[data-testid="canvas-sidecar-launcher"]')
    page.wait_for_timeout(1500)

    report = {
        "viewport": page.viewport_size,
        "session_phrase": page.evaluate(LOCATE_JS, "仅支持新建一个空会话"),
        "session_label": page.evaluate(LOCATE_JS, "新会话"),
        "panel": page.evaluate(PANEL_JS),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "source-panel-probe.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    page.screenshot(path=str(OUT_DIR / "source-panel-open.png"))
    print("新会话 命中数:", len(report["session_label"]))
    print("仅支持新建一个空会话 命中数:", len(report["session_phrase"]))
    for hit in report["session_phrase"]:
        for step in hit["chain"][:3]:
            print(f"   <{step['tag']}> tid={step['tid']!r} al={step['al']!r} title={step['title']!r} "
                  f"rect={step['rect']} display={step['display']} text={step['text']!r}")
    if report["panel"]:
        print("\n面板 testid:", len(report["panel"]["tids"]))
        for t in report["panel"]["tids"]:
            print("   ", t)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
