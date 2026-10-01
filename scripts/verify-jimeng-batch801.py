"""Jimeng clone batch 801 verifier — 画布/顶栏根节点可访问名。

Contract (SOURCE_FACT 2026-10-01，登录态，1680×826)：
  画布根  .react-flow  aria-label="Canvas"  role="application"
                       data-testid="rf__wrapper"
  顶栏根  <header>      aria-label="Canvas top bar"
                       data-testid="canvas-top-bar"

来源：快照 diff 显示这两条是源站独有条目（复刻缺失）。xyflow v12 未开放
根节点的 aria-label / role prop，故复刻侧挂 ref 后补设。
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}


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
        page.wait_for_timeout(2500)

        print("— 画布根 —")
        flow = page.locator(".react-flow").first
        check(".react-flow 存在", flow.count() == 1, f"count={flow.count()}")
        if flow.count():
            check('画布根 aria-label="Canvas"',
                  flow.get_attribute("aria-label") == "Canvas",
                  repr(flow.get_attribute("aria-label")))
            check('画布根 role="application"',
                  flow.get_attribute("role") == "application",
                  repr(flow.get_attribute("role")))
            b = flow.bounding_box()
            check("画布根铺满视口 1680x826",
                  b is not None and abs(b["width"] - 1680) <= 2 and abs(b["height"] - 826) <= 2,
                  str(b))

        print("— 顶栏根 —")
        hdr = page.locator('header[data-testid="canvas-top-bar"]')
        check("header[data-testid=canvas-top-bar] 存在", hdr.count() == 1, f"count={hdr.count()}")
        check('header aria-label="Canvas top bar"',
              hdr.get_attribute("aria-label") == "Canvas top bar",
              repr(hdr.get_attribute("aria-label")))
        hb = hdr.bounding_box()
        check("顶栏仍 @[12,10] 1656x40",
              hb is not None and abs(hb["x"] - 12) <= 2 and abs(hb["y"] - 10) <= 2
              and abs(hb["width"] - 1656) <= 2 and abs(hb["height"] - 40) <= 2,
              str(hb))

        print("— 回归 —")
        check("顶栏右簇 6 控件齐全",
              all(page.locator(s).count() == 1 for s in [
                  '[data-testid="topbar-search"]',
                  'button[aria-label="生成历史"]',
                  '[data-testid="canvas-share-trigger"]',
                  '[data-testid="canvas-more-trigger"]',
                  '[data-testid="canvas-commerce-entry"]',
                  '[data-testid="canvas-user-menu-trigger"]',
              ]), "missing control")
        check("画布仍有 2 节点", page.locator(".react-flow__node").count() == 2,
              f"count={page.locator('.react-flow__node').count()}")
        check("无 console/page 错误", not errors, "; ".join(errors[:3]))
        page.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch801-canvas-aria-1680.png"))
        browser.close()

    print()
    if failures:
        print(f"FAIL: {len(failures)}/{checks} 项未通过")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print(f"PASS: jimeng batch 801 画布/顶栏根可访问名契约（{checks} 项断言全通过）")


if __name__ == "__main__":
    main()
