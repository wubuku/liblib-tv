"""Jimeng clone batch 22 verifier — avatar account menu.

Contract (SOURCE_FACT batch 22): clicking the top-bar avatar opens the
account menu (租户名 header + 帮助中心/使用手册/快捷键/AI生成水印设置/即梦CLI,
same items as the help menu); 快捷键 opens the shortcuts panel from it.
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

    with sync_playwright() as p:
        ctx = p.chromium.launch(headless=True)
        page = ctx.new_page()
        page.set_viewport_size(VIEWPORT)  # type: ignore[arg-type]
        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2200)

        page.locator('button[aria-label="账号菜单"]').click()
        page.wait_for_timeout(600)
        # two menus share structure; after avatar click the LAST one is the
        # account menu anchored under the avatar
        menu = page.evaluate(
            """() => {
                const menus = [...document.querySelectorAll('div')]
                    .filter(d => d.querySelector('button[role="menuitem"]')
                              && d.textContent.includes('帮助中心')
                              && d.textContent.includes('即梦CLI'));
                const d = menus[menus.length - 1];
                if (!d) return null;
                return {
                    items: [...d.querySelectorAll('[role="menuitem"]')]
                        .map(b => b.textContent.trim()),
                };
            }"""
        )
        if not menu:
            failures.append("avatar account menu did not open")
        else:
            want = ["帮助中心", "使用手册", "快捷键", "AI生成水印设置", "即梦CLI"]
            if menu["items"] != want:
                failures.append(f"avatar menu items: {menu['items']}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch22-avatar-menu-1680.png")
        )

        # 快捷键 from avatar menu opens shortcuts panel
        page.locator('[role="menuitem"]', has_text="快捷键").last.click()
        page.wait_for_timeout(700)
        panel = page.evaluate(
            "() => !!document.querySelector('div[aria-label=\"快捷键\"]')"
        )
        if not panel:
            failures.append("shortcuts panel did not open from avatar menu")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 22 avatar menu contract")


if __name__ == "__main__":
    main()
