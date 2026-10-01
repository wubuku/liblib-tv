"""Jimeng clone batch 816-anchors verifier — chrome 的**可访问名**与**自动化锚点**收口到源站词汇。

选题来自 `scripts/jimeng_a11y_census.py`（跨站无障碍语义普查 diff）。
本 verifier 是那份普查的**回归形态**：普查负责找出缺口，本文件负责钉住不再退化。

Contract (SOURCE_FACT 2026-10-04 登录态 @1512×950，源站先 ⌘1 归 100%)：

  1. 左轨壳  role="toolbar" aria-label="Canvas toolbar" testid="canvas-fixed-toolbar"
             @[12,304] 48×398 radius 12px bg rgb(32,32,32) 9 枚钮
             —— 复刻几何配色本就逐项相同，此前**只差** role / aria / testid。

  2. 顶栏「搜索」「生成历史」三态逐项实测（**二次独立取样**，非单次读数）：

       态      radius   background            color
       默认      12px    transparent           rgb(255,255,255)   ← 纯白
       hover      6px    rgba(255,255,255,.08) rgb(255,255,255)
       激活       6px    rgba(255,255,255,.08) rgb(255,255,255)

     复刻此前是 `rounded-full`（28px 上 = **14px**，比源站默认大 2px、比
     源站激活态大 8px）+ `text-white/85`（**两态都不是源站的纯白**）+
     `bg-white/10`。三处都错，其中字色最显眼。

  3. 锚点实名：dock 三枚 + 顶栏搜索此前是复刻**自造**的 `dock-minimap` /
     `dock-edges` / `dock-zoom` / `topbar-search`，源站叫
     `canvas-display-toggle-minimap` / `canvas-display-toggle-connections` /
     `canvas-zoom-percent` / `canvas-panel-launcher`。

两处**刻意的偏离**（都写进了台账 §26，不是忘了改）：

  - 「生成历史」源站与「搜索」**共用** `canvas-panel-launcher`。照抄会同时命中
    2 个元素，直接打破 `verify-jimeng-batch801.py` 的「右簇 6 控件各命中 1 次」。
    源站这种复用是它自己的取舍，不是可取的契约 → 复刻用独立的
    `canvas-history-launcher`，并把「canvas-panel-launcher 恰好 1 命中」
    写成下面第 4 组断言钉死。
  - 「更多」源站**没有** testid，复刻保留自造的 `canvas-more-trigger` ——
    删掉它等于主动削弱自己的验收锚点，且源站侧无对照物可对齐。

⚠️ 颜色断言一律经 canvas 像素归一（`oklab()` 与 `rgba()` 记法不同，直接字符串
相等必假失败——这是本项目的老坑，见 batch 810-dock 文件头）。
"""

import os
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "research" / "jimeng-canvas-batch816-2026-10-03"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1512, "height": 950}

# 源站自造锚点黑名单：src/ 下不得再出现（防止下次又漂回去）
RETIRED = ["dock-minimap", "dock-edges", "dock-zoom", "topbar-search"]
# 复刻自造、源站无对照物的 testid，census 差集里显式豁免
KNOWN_CLONE_ONLY = {"canvas-more-trigger", "canvas-history-launcher"}

PROBE = r"""() => {
  // 任何颜色记法都经 canvas 像素归一：填一个点读回 RGBA
  const cv = document.createElement('canvas');
  cv.width = cv.height = 1;
  const ctx = cv.getContext('2d', { willReadFrequently: true });
  const toRGBA = (css) => {
    ctx.clearRect(0, 0, 1, 1);
    ctx.fillStyle = '#000';
    ctx.fillStyle = css;          // 非法值时 fillStyle 保持上一值
    ctx.fillRect(0, 0, 1, 1);
    const d = ctx.getImageData(0, 0, 1, 1).data;
    return [d[0], d[1], d[2], d[3]];
  };
  const read = (el) => {
    if (!el) return null;
    const r = el.getBoundingClientRect(), s = getComputedStyle(el);
    const rgba = toRGBA(s.color);
    return {
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      radius: parseFloat(s.borderTopLeftRadius) || 0,
      bgAlpha: toRGBA(s.backgroundColor)[3] / 255,
      rawBg: s.backgroundColor,
      colorRGB: rgba.slice(0, 3),
      colorAlpha: rgba[3] / 255,
    };
  };
  const byLabel = (lb) =>
    [...document.querySelectorAll('button,[role="button"]')]
      .find(b => (b.getAttribute('aria-label') || '') === lb) || null;

  const rail = document.querySelector('[data-testid="canvas-fixed-toolbar"]');
  const rr = rail ? rail.getBoundingClientRect() : null;
  const out = {
    search: read(byLabel('搜索')),
    history: read(byLabel('生成历史')),
    rail: rail ? {
      role: rail.getAttribute('role') || '',
      aria: rail.getAttribute('aria-label') || '',
      testid: rail.getAttribute('data-testid') || '',
      rect: rr ? [Math.round(rr.x), Math.round(rr.y), Math.round(rr.width), Math.round(rr.height)] : null,
      radius: parseFloat(getComputedStyle(rail).borderTopLeftRadius) || 0,
      bgRGB: toRGBA(getComputedStyle(rail).backgroundColor).slice(0, 3),
      nBtns: rail.querySelectorAll('button').length,
    } : null,
    testidCounts: {},
  };
  for (const t of ['canvas-fixed-toolbar', 'canvas-pointer-tool-toggle',
                   'canvas-display-toggle-minimap', 'canvas-display-toggle-connections',
                   'canvas-zoom-percent', 'canvas-panel-launcher',
                   'canvas-history-launcher', 'canvas-sidecar-launcher',
                   'canvas-more-trigger']) {
    out.testidCounts[t] = document.querySelectorAll(`[data-testid="${t}"]`).length;
  }
  return out;
}"""


def near(a, b, tol=1.0) -> bool:
    return a is not None and abs(a - b) <= tol


def main() -> int:
    failures: list[str] = []
    notes: list[str] = []

    # ── 组 0：源码级反向断言（不跑浏览器就能挡住漂移）──────────────────
    for token in RETIRED:
        hits = []
        for p in (ROOT / "src").rglob("*"):
            if p.suffix not in (".ts", ".tsx", ".js", ".mjs", ".css") or not p.is_file():
                continue
            if re.search(rf'(?<![\w-]){re.escape(token)}(?![\w-])', p.read_text(encoding="utf-8")):
                hits.append(str(p.relative_to(ROOT)))
        if hits:
            failures.append(f"自造锚点 {token!r} 仍存在于: {hits}")
    rail_src = (ROOT / "src/components/jimeng/JimengToolRail.tsx").read_text(encoding="utf-8")
    if 'data-testid="tool-rail"' in rail_src:
        failures.append('JimengToolRail 仍用 data-testid="tool-rail"，应为 "canvas-fixed-toolbar"')

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page(viewport=VIEWPORT, locale="zh-CN")
        try:
            pg.goto(CANVAS_URL, wait_until="domcontentloaded")
            pg.wait_for_selector('[data-testid="canvas-fixed-toolbar"]', timeout=60000)
            pg.wait_for_timeout(1200)
            idle = pg.evaluate(PROBE)

            # ── 组 1：顶栏「搜索」「生成历史」默认态 ───────────────────
            for lb in ("search", "history"):
                d = idle[lb]
                if not d:
                    failures.append(f"{lb} 按钮未找到")
                    continue
                if d["radius"] != 12:
                    failures.append(
                        f"{lb} 默认态 radius {d['radius']}px，want 12px（源站实测；"
                        f"此前 rounded-full = 14px）")
                if d["bgAlpha"] > 0.01:
                    failures.append(f"{lb} 默认态应透明，实测 alpha {d['bgAlpha']:.3f} ({d['rawBg']})")
                if d["colorAlpha"] < 0.99 or min(d["colorRGB"]) < 250:
                    failures.append(
                        f"{lb} 默认态字色 {d['colorRGB']} a={d['colorAlpha']:.2f}，"
                        f"want 纯白（源站 rgb(255,255,255)；复刻此前 white/85）")

            # ── 组 2：hover 态（radius 6 + white/8）────────────────────
            for lb, name in (("搜索", "search"), ("生成历史", "history")):
                pg.get_by_label(lb, exact=True).first.hover()
                pg.wait_for_timeout(450)
                h = pg.evaluate(PROBE)[name]
                pg.mouse.move(700, 700)
                pg.wait_for_timeout(350)
                if not h:
                    failures.append(f"{lb} hover 态未读到")
                    continue
                if h["radius"] != 6:
                    failures.append(f"{lb} hover 态 radius {h['radius']}px，want 6px")
                if abs(h["bgAlpha"] - 0.08) > 0.006:
                    failures.append(
                        f"{lb} hover 底色 alpha {h['bgAlpha']:.3f} ({h['rawBg']})，want 0.08")

            # ── 组 3：激活态 ────────────────────────────────────────────
            for lb, name in (("搜索", "search"), ("生成历史", "history")):
                pg.get_by_label(lb, exact=True).first.click()
                pg.wait_for_timeout(600)
                a = pg.evaluate(PROBE)[name]
                pg.keyboard.press("Escape")
                pg.wait_for_timeout(450)
                if not a:
                    failures.append(f"{lb} 激活态未读到")
                    continue
                if a["radius"] != 6:
                    failures.append(f"{lb} 激活态 radius {a['radius']}px，want 6px")
                if abs(a["bgAlpha"] - 0.08) > 0.006:
                    failures.append(
                        f"{lb} 激活底色 alpha {a['bgAlpha']:.3f} ({a['rawBg']})，want 0.08")
                if a["colorAlpha"] < 0.99 or min(a["colorRGB"]) < 250:
                    failures.append(f"{lb} 激活态字色应为纯白，实测 {a['colorRGB']}")

            # ── 组 4：左轨语义 + 几何 ──────────────────────────────────
            rail = idle["rail"]
            if not rail:
                failures.append("左轨 [data-testid=canvas-fixed-toolbar] 未找到")
            else:
                if rail["role"] != "toolbar":
                    failures.append(f"左轨 role={rail['role']!r}，want 'toolbar'")
                if rail["aria"] != "Canvas toolbar":
                    failures.append(f"左轨 aria-label={rail['aria']!r}，want 'Canvas toolbar'")
                if rail["rect"] != [12, 304, 48, 398]:
                    failures.append(f"左轨 {rail['rect']}，want [12,304,48,398]（源站实读）")
                if rail["radius"] != 12:
                    failures.append(f"左轨 radius {rail['radius']}px，want 12px")
                if rail["nBtns"] != 9:
                    failures.append(f"左轨 {rail['nBtns']} 枚钮，want 9（源站 9）")

            # ── 组 5：锚点实名 + 唯一性 ─────────────────────────────────
            for tid, want in (("canvas-fixed-toolbar", 1), ("canvas-pointer-tool-toggle", 1),
                              ("canvas-display-toggle-minimap", 1),
                              ("canvas-display-toggle-connections", 1),
                              ("canvas-zoom-percent", 1),
                              ("canvas-sidecar-launcher", 1),
                              ("canvas-history-launcher", 1),
                              ("canvas-panel-launcher", 1)):
                got = idle["testidCounts"].get(tid, 0)
                if got != want:
                    failures.append(f"testid {tid!r} 命中 {got} 次，want {want}")
            if idle["testidCounts"].get("canvas-more-trigger", 0) != 1:
                failures.append("testid 'canvas-more-trigger' 应保留 1 处（有意偏离，见文件头）")

            pg.screenshot(path=str(EVIDENCE / "clone-topright-816.png"),
                          clip={"x": 1120, "y": 8, "width": 380, "height": 56})
            pg.screenshot(path=str(EVIDENCE / "clone-rail-816.png"),
                          clip={"x": 0, "y": 296, "width": 72, "height": 414})
        finally:
            b.close()

    # ── 组 6：census 差集豁免与代码保持一致（防止白名单悄悄过期）────────
    src_allow = re.search(r"KNOWN_CLONE_ONLY\s*=\s*\{([^}]*)\}", Path(__file__).read_text("utf-8"))
    declared = set(re.findall(r'"([^"]+)"', src_allow.group(1))) if src_allow else set()
    if declared != KNOWN_CLONE_ONLY:
        failures.append(f"census 豁免表与 KNOWN_CLONE_ONLY 不一致: {declared} vs {KNOWN_CLONE_ONLY}")
    else:
        notes.append(f"census 豁免（源站无对照物）: {sorted(KNOWN_CLONE_ONLY)}")

    for n in notes:
        print(f"  注: {n}")
    if failures:
        print(f"FAIL batch816-anchors — {len(failures)} 项")
        for f in failures:
            print("  -", f)
        return 1
    print("PASS batch816-anchors — 左轨 toolbar 语义 + 顶栏右簇三态 12/6/6px 与纯白 + 锚点实名收口")
    return 0


if __name__ == "__main__":
    sys.exit(main())
