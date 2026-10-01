#!/usr/bin/env python3
"""Batch 796 取证：画布外框几何（左侧工具栏 / 顶栏右簇 / 底栏左簇 / Agent 抽屉默认态）。

为什么单独写这个提取器：jimeng_deep_snapshot.py 按"无障碍名"抓控件，适合做语义 diff，
但外框对齐要的是**容器 + 每个按钮的矩形和 computed 样式**，而且必须两侧同口径
（同一段 evaluate 跑在源站和复刻上），否则坐标差里会混进两侧实现差异的噪声。

只读：全程不点击、不输入、不触发任何计费动作。

用法:
    SNAP_MODE=source SNAP_URL=<源站画布> ~/.venvs/liblib-harness/bin/python \
        scripts/jimeng_headless.py run scripts/jimeng_frame_probe.py
    SNAP_MODE=clone  ~/.venvs/liblib-harness/bin/python \
        scripts/jimeng_deep_snapshot.py http://localhost:4317/jimeng/canvas/demo /dev/null \
        # 复刻侧改用直连模式（见 __main__ 的 MODE=clone 分支）
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

VIEWPORT = {"width": 1680, "height": 826}
SETTLE_MS = 11000

EXTRACT = """() => {
  const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
  const r = (el) => {
    if (!el) return null;
    const b = el.getBoundingClientRect();
    return { x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height) };
  };
  const cs = (el, ...props) => {
    if (!el) return null;
    const s = getComputedStyle(el);
    const o = {};
    for (const p of props) o[p] = s[p];
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

  // --- 左侧工具栏：找贴着左边缘、竖排的一列按钮 --------------------------
  const BTN = 'button,[role="button"],[aria-label]';
  const all = Array.from(document.querySelectorAll(BTN)).filter(visible);
  const leftish = all.filter((b) => {
    const bb = b.getBoundingClientRect();
    return bb.x < 120 && bb.width <= 80 && bb.height <= 80 && bb.height >= 24;
  });
  // 按 aria-label 认角色（源站与复刻的 class 完全不同，class 不可跨站比较）
  const railLabels = ['文本','图片','视频','音频','时间线','主体','导演台','资产库','上传'];
  const rail = railLabels.map((lb) => {
    const el = leftish.find((b) => norm(b.getAttribute('aria-label')) === lb);
    return el ? { label: lb, rect: r(el), style: cs(el, 'borderRadius','backgroundColor','color','fontSize','boxShadow') } : { label: lb, rect: null };
  }).filter((x) => x.rect);

  // 工具栏容器 = 上述按钮的最近共同祖先（用来读内边距/间隙）
  let railBox = null, railPad = null;
  if (rail.length) {
    const top = Math.min(...rail.map((x) => x.rect.y));
    const bot = Math.max(...rail.map((x) => x.rect.y + x.rect.h));
    const lf  = Math.min(...rail.map((x) => x.rect.x));
    const rt  = Math.max(...rail.map((x) => x.rect.x + x.rect.w));
    railBox = { x: lf, y: top, w: rt - lf, h: bot - top };
    const cand = Array.from(document.querySelectorAll('div,nav,aside,section'))
      .filter(visible)
      .map((el) => ({ el, b: el.getBoundingClientRect() }))
      .filter(({ b }) => b.x <= lf + 2 && b.width <= 140 && b.height >= bot - top - 8)
      .sort((a, c) => a.b.width - c.b.width)[0];
    if (cand) railPad = { rect: r(cand.el), style: cs(cand.el, 'padding','gap','display','flexDirection') };
  }

  // 相邻按钮的纵向步距（源站 42 / 复刻 36 是本 batch 的核心差异）
  const ys = rail.map((x) => x.rect.y).sort((a, b) => a - b);
  const pitch = ys.slice(1).map((y, i) => y - ys[i]);

  // --- 顶栏右簇 -----------------------------------------------------------
  const topRightLabels = ['搜索','生成历史','分享','更多','用户菜单'];
  const top = all.filter((b) => b.getBoundingClientRect().y < 60);
  const topRight = topRightLabels.map((lb) => {
    const el = top.find((b) => norm(b.getAttribute('aria-label')) === lb);
    return el ? { label: lb, rect: r(el) } : { label: lb, rect: null };
  }).filter((x) => x.rect);
  const credits = all.find((b) => /^Credits:/.test(norm(b.getAttribute('aria-label')) || b.innerText));
  if (credits) topRight.push({ label: 'credits', rect: r(credits), aria: norm(credits.getAttribute('aria-label')) });

  // --- 底栏左簇 -----------------------------------------------------------
  const bottom = all.filter((b) => b.getBoundingClientRect().y > 740);
  const bottomLeft = bottom.map((b) => ({
    label: norm(b.getAttribute('aria-label')) || norm(b.innerText).slice(0, 20),
    rect: r(b),
  })).sort((a, b) => a.rect.x - b.rect.x);

  // --- Agent 抽屉默认态 ---------------------------------------------------
  const agent = document.querySelector('aside[aria-label="Agent"], [aria-label="Agent"], [class*="agent" i], [class*="drawer" i]');
  const chatTrigger = all.find((b) => norm(b.getAttribute('aria-label')) === '与 AI 对话' || norm(b.innerText) === '与 AI 对话');
  const drawerOpenCues = all.filter((b) => ['收起','新建会话','发送消息','使用技能','引用参考'].includes(norm(b.getAttribute('aria-label')) || norm(b.innerText)));
  // 是否存在可输入的对话输入框（有 = 抽屉展开）
  const chatInput = document.querySelector('textarea, input[placeholder*="想法"], input[placeholder*="对话"]');

  // --- 画布背景 -----------------------------------------------------------
  const canvasRoot = document.querySelector('.react-flow, [class*="canvas-bg" i], [data-testid*="canvas" i]');

  return {
    url: location.href,
    rail, railPitch: pitch, railBox, railPad,
    topRight, bottomLeft,
    agent: {
      drawerEl: r(agent),
      chatTrigger: r(chatTrigger),
      openCueCount: drawerOpenCues.length,
      openCues: drawerOpenCues.map((b) => norm(b.getAttribute('aria-label')) || norm(b.innerText)),
      hasInput: !!chatInput,
      defaultOpen: drawerOpenCues.length > 0 && !!chatInput,
    },
    canvasRoot: r(canvasRoot),
    bodyBg: getComputedStyle(document.body).backgroundColor,
  };
}"""


def run(page, url: str, settle: int = SETTLE_MS) -> dict:
    page.set_viewport_size(VIEWPORT)
    if url and page.url != url:
        page.goto(url, wait_until="domcontentloaded", timeout=90_000)
    page.wait_for_timeout(settle)
    return page.evaluate(EXTRACT)


def report(tag: str, d: dict) -> None:
    print(f"\n===== {tag} =====")
    print(f"url={d['url']}")
    print("rail:")
    for x in d["rail"]:
        print(f"  {x['label']:<6} {x['rect']}")
    print(f"  pitch={d['railPitch']}")
    print(f"  box={d['railBox']}")
    if d.get("railPad"):
        print(f"  pad={d['railPad']['rect']} style={d['railPad']['style']}")
    print("topRight:")
    for x in d["topRight"]:
        print(f"  {x['label']:<10} {x['rect']} {x.get('aria','')}")
    print("bottomLeft:")
    for x in d["bottomLeft"]:
        print(f"  {x['label']:<20} {x['rect']}")
    print("agent:", json.dumps(d["agent"], ensure_ascii=False))
    print("canvasRoot:", d["canvasRoot"], "bodyBg:", d["bodyBg"])


def main() -> int:
    out = Path(os.environ.get("SNAP_OUT") or "/tmp/frame-probe.json")
    url = os.environ.get("SNAP_URL") or (sys.argv[1] if len(sys.argv) > 1 else "")
    settle = int(os.environ.get("SNAP_SETTLE", SETTLE_MS))

    injected = globals().get("page")
    if injected is not None:
        d = run(injected, url, settle)
    else:
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            pg = b.new_page(viewport=VIEWPORT, locale="zh-CN")
            try:
                d = run(pg, url, settle)
            finally:
                b.close()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    report(os.environ.get("SNAP_MODE", "result"), d)
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
