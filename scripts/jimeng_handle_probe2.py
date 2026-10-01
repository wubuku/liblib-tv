#!/usr/bin/env python3
"""Batch 805 取证（二）：**视频节点**的连接手柄 + hover 可见态。

batch 804 探针一的遗留问题：画布上 4 个音频节点几乎完全叠在视频节点上
（视频 454..1023×285..605，音频 578..978×305..665），点节点中心永远落在
音频节点上，5 次点击只选中过「音频 4」。而 batch 210/380 关于「本地上传
视频节点左侧无 +」的旧记载**恰恰是视频节点的规则**，拿音频节点的样本去
推视频节点是不成立的——必须精确选中视频节点再量。

第二个遗留问题：探针一量到的 + 钮 bg=透明 / pointer-events:none，说明量到
的是**未激活态**。真实可见外观（底色、边框、图标、阴影）要 hover 上去才
拿得到，本脚本把 hover 前后的 computed style 都 dump 出来。

只读护栏：全部动作限于 hover / 键盘，不点击任何计费入口。

用法:
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
        scripts/jimeng_handle_probe2.py <source|clone> <url>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

VIEWPORT = {"width": 1680, "height": 826}

DUMP = """() => {
  const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
  const r = (el) => {
    const b = el.getBoundingClientRect();
    return { x: Math.round(b.x), y: Math.round(b.y),
             w: Math.round(b.width), h: Math.round(b.height) };
  };
  const K = ['backgroundColor', 'backgroundImage', 'border', 'borderRadius',
             'opacity', 'visibility', 'pointerEvents', 'zIndex', 'position',
             'color', 'boxShadow', 'transform', 'overflow'];
  const cs = (el) => { const s = getComputedStyle(el); const o = {};
    K.forEach((k) => { o[k] = s[k]; }); return o; };
  const nodes = [...document.querySelectorAll('.react-flow__node')].map((n) => ({
    aria: n.getAttribute('aria-label'),
    cls: norm(n.className.toString()).slice(0, 120),
    selected: n.classList.contains('selected'),
    rect: r(n),
  }));
  const btns = [...document.querySelectorAll('[aria-label*="onnected" i], [aria-label*="添加节点"]')]
    .map((b) => ({
      aria: b.getAttribute('aria-label'),
      tag: b.tagName.toLowerCase(),
      rect: r(b),
      style: cs(b),
      parent: {
        tag: b.parentElement ? b.parentElement.tagName.toLowerCase() : null,
        cls: b.parentElement ? norm(b.parentElement.className.toString()).slice(0, 120) : null,
        rect: b.parentElement ? r(b.parentElement) : null,
      },
      inner: [...b.querySelectorAll('*')].map((k) => ({
        tag: k.tagName.toLowerCase(),
        cls: norm(k.className && k.className.toString()).slice(0, 60),
        rect: r(k),
      })),
    }));
  // 60x120 隐形热区：源站不是 .react-flow__handle（探针一没抓到），
  // 按几何捞——贴着节点左右缘、宽 60 高 120 的 div
  const hot = [...document.querySelectorAll('div')].filter((d) => {
    const b = d.getBoundingClientRect();
    return Math.round(b.width) === 60 && Math.round(b.height) === 120;
  }).map((d) => ({
    cls: norm(d.className.toString()).slice(0, 120),
    rect: r(d),
    style: cs(d),
    // 到最近 .react-flow__node 的距离，判它属于哪个节点
    node: (() => {
      let p = d;
      for (let i = 0; i < 6 && p; i++) {
        if (p.classList && p.classList.contains('react-flow__node'))
          return p.getAttribute('aria-label');
        p = p.parentElement;
      }
      return null;
    })(),
  }));
  return { nodes, btns, hot };
}"""


def run(pg, mode: str, url: str) -> dict:
    pg.goto(url, wait_until="domcontentloaded")
    pg.wait_for_timeout(6000)
    for _ in range(14):
        pg.keyboard.press("Meta+0")
        pg.wait_for_timeout(120)
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(600)

    d: dict = {"mode": mode, "url": url, "attempts": [], "before": None, "after": None}

    base = pg.evaluate(DUMP)
    d["before"] = base

    # 挑一个只属于目标节点的落点：对每个节点算「中心点落在别的节点里的」
    # 次数，选最干净的那个节点，取其 rect 内第一个干净像素点。
    def pick(nodes):
        """给每个节点找一个「只落在它自己身上」的像素点。

        注意不能对 frac 循环一见 inside-self 就 break —— 那等价于永远选
        中心点，而中心点恰恰是重叠节点堆叠的地方（源站 5 个音频节点把
        视频节点盖得只剩左上角一小块）。必须对每个 frac 各自算一次
        blocked 数再取最小。
        """
        scored = []
        for n in nodes:
            rct = n["rect"]
            if rct["w"] < 120 or rct["h"] < 60:
                continue
            others = [o for o in nodes if o is not n]
            best = None
            for fx, fy in (
                (0.5, 0.5), (0.08, 0.06), (0.5, 0.06), (0.06, 0.5),
                (0.92, 0.06), (0.5, 0.94), (0.94, 0.5), (0.06, 0.06),
            ):
                px = rct["x"] + rct["w"] * fx
                py = rct["y"] + rct["h"] * fy
                blocked = sum(
                    1 for o in others
                    if o["rect"]["x"] <= px <= o["rect"]["x"] + o["rect"]["w"]
                    and o["rect"]["y"] <= py <= o["rect"]["y"] + o["rect"]["h"]
                )
                if best is None or blocked < best[0]:
                    best = (blocked, px, py)
                if blocked == 0:
                    break
            scored.append((best[0], n, best[1], best[2]))
        scored.sort(key=lambda t: t[0])
        return scored

    ranked = pick(base["nodes"])
    for blocked, n, px, py in ranked[:3]:
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(500)
        pg.mouse.click(px, py)
        pg.wait_for_timeout(1500)
        snap = pg.evaluate(DUMP)
        sel = [x for x in snap["nodes"] if x["selected"]]
        d["attempts"].append({
            "target": n["aria"], "pt": [round(px), round(py)], "blockedBy": blocked,
            "selected": [x["aria"] for x in sel],
        })
        if sel and sel[0]["aria"] == n["aria"]:
            d["after"] = snap
            break
    else:
        d["after"] = snap

    # hover-only 取样：不点击，只把鼠标放到节点干净点上，看 + 钮是否出现。
    # 台账批 380 记载「DOM 常驻 hover 显示」，这里对每类节点各验一次，
    # 顺带解决「量到的钮 bg 透明 + pe:none 是否只是未激活态」的疑问。
    scan = []
    for blocked, n, px, py in ranked[:5]:
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(350)
        pg.mouse.move(px - 30, py - 30)
        pg.wait_for_timeout(150)
        pg.mouse.move(px, py)
        pg.wait_for_timeout(800)
        s3 = pg.evaluate(DUMP)
        scan.append({
            "node": n["aria"], "pt": [round(px), round(py)],
            "buttons": [
                {"aria": b["aria"], "rect": b["rect"],
                 "bg": b["style"]["backgroundColor"], "border": b["style"]["border"],
                 "pe": b["style"]["pointerEvents"], "op": b["style"]["opacity"],
                 "r": b["style"]["borderRadius"], "color": b["style"]["color"]}
                for b in s3["btns"]
            ],
        })
    d["hoverScan"] = scan

    # hover 可见态：对每个 + 钮 hover 一下再量
    hovers = []
    for b in (d["after"] or {}).get("btns", []):
        rct = b["rect"]
        cx, cy = rct["x"] + rct["w"] / 2, rct["y"] + rct["h"] / 2
        pg.mouse.move(cx - 40, cy - 40)
        pg.wait_for_timeout(200)
        pg.mouse.move(cx, cy)
        pg.wait_for_timeout(700)
        s2 = pg.evaluate(DUMP)
        same = [x for x in s2["btns"] if x["aria"] == b["aria"]]
        hovers.append({"aria": b["aria"], "idle": b, "hover": same[0] if same else None})
    d["hovers"] = hovers
    return d


def _run_standalone(fn) -> dict:
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
    injected = globals().get("page")
    d = run(injected, mode, url) if injected is not None else _run_standalone(lambda pg: run(pg, mode, url))
    out = Path(f"docs/research/jimeng-canvas-batch806-2026-10-03/handle2-{mode}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out}\nattempts: {json.dumps(d['attempts'], ensure_ascii=False)}")
    print("\n-- 节点 --")
    for n in (d["after"] or {}).get("nodes", []):
        print(f"  {n['aria']!r} sel={n['selected']} @{n['rect']}")
    print("\n-- 60x120 隐形热区 --")
    for h in (d["after"] or {}).get("hot", []):
        print(f"  node={h['node']!r} @{h['rect']} bg={h['style']['backgroundColor']} pe={h['style']['pointerEvents']} cls={h['cls'][:80]}")
    print("\n-- hover-only 扫描（不点击，只移鼠标）--")
    for s in d.get("hoverScan", []):
        print(f"  {s['node']!r} @{s['pt']}")
        for b in s["buttons"]:
            print(f"      {b['aria']!r} @{b['rect']} bg={b['bg']} b={b['border']} pe={b['pe']} op={b['op']} r={b['r']}")
    print("\n-- + 钮（idle → hover）--")
    for hv in d.get("hovers", []):
        i, ho = hv["idle"], hv["hover"]
        print(f"  {hv['aria']!r}")
        print(f"    idle  @{i['rect']} bg={i['style']['backgroundColor']} b={i['style']['border']} op={i['style']['opacity']} pe={i['style']['pointerEvents']} r={i['style']['borderRadius']}")
        if ho:
            print(f"    hover @{ho['rect']} bg={ho['style']['backgroundColor']} b={ho['style']['border']} op={ho['style']['opacity']} pe={ho['style']['pointerEvents']} r={ho['style']['borderRadius']} color={ho['style']['color']} shadow={ho['style']['boxShadow'][:60]}")
            print(f"      inner={json.dumps(ho['inner'], ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
