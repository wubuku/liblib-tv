"""Jimeng clone batch 800 verifier — 点阵网格：实测参数 + 世界锚定。

（编号说明：797 与 799 均已被并行会话占用。本批取 800 以免撞号。）

Contract (SOURCE_FACT 2026-10-01 登录态，源站**截图逐像素**实测 @1680×826)：

  源站点阵网格画在 WebGL <canvas> 上（画布内有 2 个 canvas，getContext('2d')
  取不到像素，故改用 Playwright 截图 + PIL 逐像素分析）。

  100% 缩放：点距 **18px**、点簇宽 **2px**、峰值 **rgb(45,45,45)**，
            背景 rgb(13,13,13) ⇒ 白色 alpha ≈ 0.13（13+(255−13)×0.13≈44.5）
  48%  缩放：点距 **8.6px**（≈18×0.48）
  ⇒ 网格是**世界锚定**的：点距随 zoom 缩放，不是固定屏幕间距。

  - 本批**推翻**旧台账的估值「28px / rgba(255,255,255,.075) /
    73% 下约 20px 屏幕」—— 那是在无法从 canvas 读像素时的猜测，实测 18px / 0.13。
  - 复刻的实现陷阱：`.react-flow__pane` **不在** `.react-flow__viewport` 内
    （实测 paneInsideViewport=false），是屏幕层，其 CSS background 不会被
    viewport 的 transform 缩放。直接写死 18px 会让网格固定在 18px 屏幕间距。
    故由 `JimengWorkspace.applyGridVars` 按真实变换写 CSS 变量：
    tile = 18 × zoom，偏移 = pan mod tile。

  命中  默认缩放下 computed background-size == 18 × zoom；
        实测屏幕点距 == 该 tile（±1px），且区域确为纯背景（≥90%）；
        点簇宽 2–3px、峰值亮度 44±4；
        切到 100% 后点距回到 18（±1px），即点距随 zoom 变化而非固定。
"""

import io
import os
from collections import Counter
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}

GRID_WORLD_PX = 18
BG_RGB = (13, 13, 13)
# 取一块纯画布区（避开 rail x<60 / dock y>774 / 节点区）
REGION = {"x": 120, "y": 620, "width": 300, "height": 130}


def analyze_grid(png_bytes: bytes) -> dict:
    """在截图里量点阵：背景色、点距、点簇宽、峰值亮度。"""
    im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    w, h = im.size
    px = im.load()

    def lum(c: tuple[int, int, int]) -> int:
        return sum(c)

    cnt = Counter(px[x, y] for x in range(w) for y in range(h))
    bg = cnt.most_common(1)[0][0]
    base = lum(bg)
    # 找非背景像素最多的那一行 = 穿过一排点的水平线
    rows = [(sum(1 for x in range(w) if lum(px[x, y]) != base), y) for y in range(h)]
    rows.sort(reverse=True)
    n_on, y = rows[0]
    on = [x for x in range(w) if lum(px[x, y]) != base]
    runs: list[tuple[int, int]] = []
    if on:
        s = q = on[0]
        for x in on[1:]:
            if x != q + 1:
                runs.append((s, q - s + 1))
                s = x
            q = x
        runs.append((s, q - s + 1))
    starts = [r[0] for r in runs]
    periods = [starts[i + 1] - starts[i] for i in range(len(starts) - 1)]
    bright = max(
        ((lum(px[x, yy]), px[x, yy]) for yy in range(h) for x in range(w) if lum(px[x, yy]) != base),
        default=(base, bg),
    )
    return {
        "bg": bg,
        "bg_ratio": cnt[bg] / (w * h),
        "period_avg": (sum(periods) / len(periods)) if periods else None,
        "widths": sorted({r[1] for r in runs}),
        "peak": bright[1],
        "dot_count": n_on,
    }


def main() -> None:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    checks = 0

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(f"{name}: {detail}")
        print(f"  [{'ok ' if ok else 'FAIL'}] {name}{'' if ok else ' — ' + detail}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport=VIEWPORT, locale="zh-CN")
        errors: list[str] = []
        page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))

        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        def read_grid() -> dict:
            st = page.evaluate(
                """() => {
                  const el = document.querySelector('.jimeng-canvas');
                  const pane = document.querySelector('.jimeng-canvas .react-flow__pane');
                  if (!pane) return null;
                  const cs = getComputedStyle(pane);
                  const vp = document.querySelector('.jimeng-canvas .react-flow__viewport');
                  return {
                    zoom: (document.body.innerText.match(/(\\d{1,3})%/) || [])[0] || null,
                    bgSize: cs.backgroundSize, bgPos: cs.backgroundPosition,
                    bgImage: cs.backgroundImage.slice(0, 90),
                    varTile: el ? el.style.getPropertyValue('--jm-grid-tile') : '',
                    insideViewport: !!(pane && vp && vp.contains(pane)),
                  };
                }"""
            )
            shot = page.screenshot(clip=REGION)
            return {"style": st, "grid": analyze_grid(shot)}

        # ── 默认缩放 ──
        print("— 默认缩放 —")
        d = read_grid()
        st, g = d["style"], d["grid"]
        check("pane 存在", st is not None, "None")
        zoom = 0.0
        if st:
            zoom = float((st["zoom"] or "0").rstrip("%")) / 100
            want_tile = GRID_WORLD_PX * zoom
            got_tile = float(st["bgSize"].split()[0].replace("px", ""))
            check(f"background-size == 18×zoom（{want_tile:.2f}px）",
                  abs(got_tile - want_tile) < 0.5, f"实际 {got_tile:.4f}px @zoom {st['zoom']}")
            check("网格由 --jm-grid-tile 驱动（非写死）",
                  bool(st["varTile"]) and st["varTile"].endswith("px"), repr(st["varTile"]))
            check("background-position 由 pan 推导", st["bgPos"] not in ("0% 0%", "0px 0px"), st["bgPos"])
            check("点色 alpha ≈0.13", "0.13" in st["bgImage"], st["bgImage"])
            check("pane 确实不在 viewport 内（故需 JS 换算）",
                  st["insideViewport"] is False, f"insideViewport={st['insideViewport']}")

        check(f"区域背景为 {BG_RGB}", tuple(g["bg"]) == BG_RGB, str(g["bg"]))
        check("采样区基本是空白画布（≥90% 背景）", g["bg_ratio"] >= 0.90, f"{g['bg_ratio']:.1%}")
        check("该行确实穿到点（非背景像素 ≥20）", g["dot_count"] >= 20, f"dot_count={g['dot_count']}")
        check(f"实测屏幕点距 ≈ {GRID_WORLD_PX}×zoom",
              g["period_avg"] is not None and abs(g["period_avg"] - GRID_WORLD_PX * zoom) <= 1.0,
              f"实测 {g['period_avg'] and round(g['period_avg'], 2)}px")
        check("点簇宽 2–3px", g["widths"] and all(2 <= x <= 3 for x in g["widths"]), str(g["widths"]))
        check("峰值亮度 ≈45（±4）", 41 <= g["peak"][0] <= 49, f"实际 {g['peak']}")

        # ── 切到 100%：点距应回到 18 ──
        print("— 切到 100%（验证点距随 zoom 变化）—")
        page.locator('[data-testid="dock-zoom"]').click()
        page.wait_for_timeout(500)
        page.locator('[role="menuitem"]', has_text="缩放至100%").click()
        page.wait_for_timeout(1200)
        d2 = read_grid()
        st2, g2 = d2["style"], d2["grid"]
        check("缩放已到 100%", st2["zoom"] == "100%", str(st2["zoom"]))
        check("100% 时 background-size ≈18px",
              abs(float(st2["bgSize"].split()[0].replace("px", "")) - GRID_WORLD_PX) < 0.5,
              st2["bgSize"])
        check("100% 时实测点距 ≈18px（±1）",
              g2["period_avg"] is not None and abs(g2["period_avg"] - GRID_WORLD_PX) <= 1.0,
              f"实测 {g2['period_avg'] and round(g2['period_avg'], 2)}px")
        check("点距确实随 zoom 变化（非固定屏幕间距）",
              bool(g["period_avg"] and g2["period_avg"] and abs(g2["period_avg"] - g["period_avg"]) > 2),
              f"{round(g['period_avg'] or 0, 1)} → {round(g2['period_avg'] or 0, 1)}")

        page.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch800-grid-100-1680.png"))
        check("无 console/page 错误", not errors, "; ".join(errors[:4]))
        browser.close()

    print()
    if failures:
        print(f"FAIL: {len(failures)}/{checks} 项不通过")
        for f in failures:
            print("  - " + f)
        raise SystemExit(1)
    print(f"PASS: jimeng batch 800 点阵网格实测参数 + 世界锚定（{checks} 项断言全通过）")


if __name__ == "__main__":
    main()
