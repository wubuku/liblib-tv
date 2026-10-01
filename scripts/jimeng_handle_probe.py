#!/usr/bin/env python3
"""Batch 805 取证：节点「连接手柄」（+ 圆钮）的实名与几何 —— 同一段 evaluate 跑两侧。

背景：batch 210 只量到源站 + 圆钮 36×36，batch 380 留档了实名
「Create connected node after …」。但从来没有回答两个问题：

  1. 实名到底怎么拼？`after 视频 1` 里的「视频 1」是节点标题还是序号？
     不同节点类型（文本/图片/视频/音频）前缀是不是各不同？
  2. 36×36 那个圆钮**外面**有没有更大的隐形热区？
     clone 现在是 60×120 的隐形 react-flow Handle，圆钮只是它的子节点。
     如果源站也是「隐形热区 + 内嵌 36 圆钮」两层结构，那 60×120 可能
     是对的；如果源站只有 36×36 一层，那 clone 的热区是凭空放大的。

本探针把每层都 dump 出来：命中元素 + 逐级祖先链（含每个祖先的 rect /
背景 / 透明度），这样「隐形热区」和「圆钮」能被区分开，而不是只看
最外层那个矩形就下结论（batch 796 的教训：只比内层控件会得出假结论）。

用法（源站，需登录态）:
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
        scripts/jimeng_handle_probe.py <source|clone> <url>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

VIEWPORT = {"width": 1680, "height": 826}

# 一次 evaluate 拿到全部：手柄元素 + 祖先链。
# 用 ReactFlow 的节点容器（.react-flow__node）定位，而不是靠坐标点，
# 这样缩放/平移变化都不会让取样点踩空。
EXTRACT = """() => {
  const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
  const r = (el) => {
    const b = el.getBoundingClientRect();
    return {
      x: Math.round(b.x), y: Math.round(b.y),
      w: Math.round(b.width), h: Math.round(b.height),
    };
  };
  const cs = (el, keys) => {
    const s = getComputedStyle(el); const o = {};
    keys.forEach((k) => { o[k] = s[k]; });
    return o;
  };
  const visible = (el) => {
    const b = el.getBoundingClientRect();
    if (b.width < 1 || b.height < 1) return false;
    for (let p = el; p; p = p.parentElement) {
      const s = getComputedStyle(p);
      if (s.visibility === 'hidden' || s.display === 'none') return false;
    }
    return true;
  };
  const DESC = [
    'backgroundColor', 'backgroundImage', 'border', 'borderRadius',
    'opacity', 'zIndex', 'position',
  ];

  // 节点卡片：clone 是 .react-flow__node，源站类名未知 → 退化为
  // 「有 aria-label 且标题匹配 /(视频|图片|文本|音频) \\d+/ 的祖先」。
  const nodeOf = (el) => {
    let n = el;
    for (let i = 0; i < 10 && n; i++) {
      if (n.classList && n.classList.contains('react-flow__node')) return n;
      const t = norm(n.textContent || '').slice(0, 40);
      if (/^(视频|图片|文本|音频)\\s*\\d*/.test(t) && n.getBoundingClientRect().width > 200) return n;
      n = n.parentElement;
    }
    return null;
  };

  const nodeLabel = (n) => {
    if (!n) return null;
    const t = norm(n.textContent || '');
    const m = /(视频|图片|文本|音频)\\s*\\d+/.exec(t);
    return m ? m[0] : norm(t).slice(0, 12);
  };

  const chain = (el, depth) => {
    const out = []; let n = el;
    for (let i = 0; i < depth && n; i++) {
      out.push({
        depth: i,
        tag: n.tagName.toLowerCase(),
        cls: norm(n.className && n.className.toString ? n.className.toString() : '').slice(0, 110),
        aria: n.getAttribute ? (n.getAttribute('aria-label') || null) : null,
        title: n.getAttribute ? (n.getAttribute('title') || null) : null,
        testid: n.getAttribute ? (n.getAttribute('data-testid') || null) : null,
        rect: r(n),
        style: cs(n, DESC),
        hasBg: (() => {
          const b = getComputedStyle(n).backgroundColor;
          const m = /^rgba?\\(([^)]+)\\)$/.exec(b) || /^color\\(srgb\\s+([^)]+)\\)$/.exec(b);
          const a = m ? (m[1].trim().split(/[\\s,/]+/)[3] || '1').trim() : '1';
          return !!(m && parseFloat(a) > 0.02);
        })(),
      });
      n = n.parentElement;
    }
    return out;
  };

  // 只关心「连接手柄」：aria 命中 connected，或 (无 aria 但) 位于节点左右
  // 缘外、且带 react-flow__handle 类。
  const cands = [...document.querySelectorAll(
    '[aria-label*="onnected" i], .react-flow__handle, [class*="handle"]'
  )].filter(visible);

  const seen = new Set();
  const handles = [];
  for (const el of cands) {
    const key = el.tagName + '|' + (el.getAttribute('aria-label') || '') + '|' +
      JSON.stringify(r(el));
    if (seen.has(key)) continue; seen.add(key);
    const node = nodeOf(el);
    handles.push({
      tag: el.tagName.toLowerCase(),
      cls: norm(el.className && el.className.toString ? el.className.toString() : '').slice(0, 130),
      aria: el.getAttribute('aria-label') || null,
      title: el.getAttribute('title') || null,
      testid: el.getAttribute('data-testid') || null,
      rect: r(el),
      style: cs(el, DESC),
      pointerEvents: getComputedStyle(el).pointerEvents,
      // 该元素内部还有没有更小的「可见圆钮」子节点
      kids: [...el.querySelectorAll('*')].filter(visible).map((k) => ({
        tag: k.tagName.toLowerCase(),
        aria: k.getAttribute('aria-label') || null,
        rect: r(k),
        hasBg: (() => {
          const b = getComputedStyle(k).backgroundColor;
          const m = /^rgba?\\(([^)]+)\\)$/.exec(b) || /^color\\(srgb\\s+([^)]+)\\)$/.exec(b);
          const a = m ? (m[1].trim().split(/[\\s,/]+/)[3] || '1').trim() : '1';
          return !!(m && parseFloat(a) > 0.02);
        })(),
      })).slice(0, 8),
      node: nodeLabel(node),
      nodeRect: node ? r(node) : null,
      chain: chain(el, 4),
    });
  }

  // 顺手把节点卡片本体也记下来（判手柄相对左右缘的偏移要用）
  const nodes = [...document.querySelectorAll('.react-flow__node')].filter(visible).map((n) => ({
    label: nodeLabel(n),
    selected: n.classList.contains('selected'),
    rect: r(n),
  }));

  return { handles, nodes, url: location.href };
}"""


def run(pg, mode: str, url: str) -> dict:
    pg.goto(url, wait_until="domcontentloaded")
    pg.wait_for_timeout(6000)
    # 归零到 100%：手柄偏移是相对量，缩放会污染所有坐标
    for _ in range(14):
        pg.keyboard.press("Meta+0")
        pg.wait_for_timeout(120)
    pg.wait_for_timeout(1200)

    d: dict = {"mode": mode, "url": url, "viewports": []}

    if mode == "source":
        # 源站：逐个点节点卡片中心，等选中态的 + 圆钮出现。
        # 点击坐标取自第一次 evaluate 里的节点卡片矩形。
        first = pg.evaluate(EXTRACT)
        d["initial"] = {"nodes": first["nodes"]}
        for n in first["nodes"][:6]:
            if n["rect"]["w"] < 120:
                continue
            cx = n["rect"]["x"] + n["rect"]["w"] / 2
            cy = n["rect"]["y"] + n["rect"]["h"] / 2
            try:
                pg.mouse.click(cx, cy)
            except Exception as exc:  # noqa: BLE001
                d.setdefault("clickErrors", []).append(str(exc))
            pg.wait_for_timeout(1400)
            snap = pg.evaluate(EXTRACT)
            hs = [h for h in snap["handles"] if h["aria"]]
            if hs:
                d["viewports"].append(
                    {"node": n["label"], "handles": hs, "nodes": snap["nodes"]}
                )
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(700)
    else:
        snap = pg.evaluate(EXTRACT)
        d["viewports"].append(
            {"node": "(clone 单次)", "handles": snap["handles"], "nodes": snap["nodes"]}
        )

    d["nViewports"] = len(d["viewports"])
    return d


def _run_standalone(fn) -> dict:
    """独立运行（不经 jimeng_headless）时自己开浏览器。"""
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page(viewport=VIEWPORT, locale="zh-CN")
        try:
            return fn(pg)
        finally:
            b.close()


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "clone"
    url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:4317/jimeng/canvas/demo"
    # 经 jimeng_headless.py run 调用时 page 已注入（含登录态），直接复用；
    # 自己单跑才另开浏览器。
    injected = globals().get("page")
    if injected is not None:
        d = run(injected, mode, url)
    else:
        d = _run_standalone(lambda pg: run(pg, mode, url))
    out = Path(f"docs/research/jimeng-canvas-batch806-2026-10-03/handle-{mode}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out}")

    for vp in d.get("viewports", []):
        print(f"\n=== node: {vp['node']} ===")
        for h in vp["handles"]:
            rr = h["rect"]
            print(
                f"  [{h['tag']}] aria={h['aria']!r} title={h['title']!r} "
                f"@{[rr['x'], rr['y']]} {rr['w']}x{rr['h']} "
                f"bg={h['style']['backgroundColor']} r={h['style']['borderRadius']} "
                f"pe={h['pointerEvents']} cls={h['cls'][:70]}"
            )
            for k in h["kids"]:
                print(f"      kid <{k['tag']}> aria={k['aria']!r} bg={k['hasBg']} @{k['rect']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
