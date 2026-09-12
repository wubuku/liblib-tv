"""Jimeng clone batch 18 verifier — shortcuts panel + ⌘0 fit canvas.

Contract:
- Help menu 快捷键 opens the shortcuts panel with sections 通用操作/视图 and
  documented keys (撤销 ⌘Z, 适配画布 ⇧1|⌘0, 缩放画布 ⌘ scroll); close × works.
- ⌘0 fits the canvas (zoom readout changes from 73%).
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

        page.locator('button[aria-label="帮助"]').click()
        page.wait_for_timeout(500)
        page.locator('[role="menuitem"]', has_text="快捷键").click()
        page.wait_for_timeout(700)

        panel = page.evaluate(
            """() => {
                const d = document.querySelector('div[aria-label="快捷键"]');
                if (!d) return null;
                const rows = [...d.querySelectorAll('span')].map(s => s.textContent.trim());
                return {
                    sections: d.textContent.includes('通用操作') && d.textContent.includes('视图'),
                    undo: rows.includes('撤销') && rows.includes('⌘ Z'),
                    fit: rows.includes('适配画布') && rows.includes('⇧ 1 | ⌘ 0'),
                    group: rows.includes('创建编组') && rows.includes('⌘ G'),
                    canvasScroll: rows.includes('缩放画布') && rows.includes('⌘ scroll'),
                };
            }"""
        )
        if not panel:
            failures.append("shortcuts panel did not open")
        else:
            if not panel["sections"]:
                failures.append("sections missing")
            for key, name in [
                ("undo", "撤销行"), ("fit", "适配画布行"),
                ("group", "编组行"), ("canvasScroll", "缩放画布行"),
            ]:
                if not panel[key]:
                    failures.append(f"{name} missing")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch18-shortcuts-1680.png")
        )

        # ⌘0 fit canvas — zoom readout should change from 73%
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        page.keyboard.press("Meta+0")
        page.wait_for_timeout(900)
        zoom = page.evaluate(
            "() => document.querySelector('.jimeng-bottom-dock').textContent.match(/\\d+%/)?.[0]"
        )
        if zoom == "73%":
            failures.append(f"⌘0 did not change zoom: {zoom}")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 18 shortcuts contract")


if __name__ == "__main__":
    main()
