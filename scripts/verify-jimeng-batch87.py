"""Jimeng clone batch 87 verifier — node title inline rename.

Contract (SOURCE_FACT batch 87, 87-rename-open.png):
- clicking the node title opens an inline input pre-filled with the
  current title (300px, white/70);
- Enter commits (renameNode, title attr + row text update, undoable via
  Cmd+Z); Escape cancels; double-click on the row still toggles the
  insert menu and exits renaming.
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
        page.wait_for_timeout(2500)

        # select video node, then click its title text
        c = page.evaluate(
            """() => { const n = document.querySelector('[data-id="video-local-1"]');
                const r = n.getBoundingClientRect();
                return {x: r.x + 60, y: r.y + 20}; }"""
        )
        page.mouse.click(c["x"], c["y"])
        page.wait_for_timeout(600)
        title = page.locator('[data-id="video-local-1"] [data-testid="node-title-text"]')
        if not title.count():
            failures.append("title text span not found")
            raise SystemExit(1)
        title.click()
        page.wait_for_timeout(500)
        inp = page.locator('[data-testid="node-rename-input"]')
        if not inp.count():
            failures.append("rename input did not open")
            raise SystemExit(1)
        val = inp.input_value()
        if "sb_518102884867410fb" not in val:
            failures.append(f"rename input prefilled wrong: {val!r}")

        # rename + Enter
        page.keyboard.press("Meta+a")
        page.keyboard.type("重命名测试.mp4")
        page.keyboard.press("Enter")
        page.wait_for_timeout(700)
        shown = page.locator(
            '[data-id="video-local-1"] [data-testid="node-title-text"]'
        ).inner_text()
        if shown != "重命名测试.mp4":
            failures.append(f"rename not applied: {shown!r}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch87-renamed.png")
        )

        # undo restores
        page.keyboard.press("Meta+z")
        page.wait_for_timeout(700)
        restored = page.locator(
            '[data-id="video-local-1"] [data-testid="node-title-text"]'
        ).inner_text()
        if "sb_518102884867410fb" not in restored:
            failures.append(f"rename undo failed: {restored!r}")

        # Escape cancels editing
        page.locator(
            '[data-id="video-local-1"] [data-testid="node-title-text"]'
        ).click()
        page.wait_for_timeout(400)
        page.keyboard.type("XYZ")
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        if page.locator('[data-testid="node-rename-input"]').count():
            failures.append("Escape did not cancel rename editing")
        kept = page.locator(
            '[data-id="video-local-1"] [data-testid="node-title-text"]'
        ).inner_text()
        if "sb_518102884867410fb" not in kept:
            failures.append(f"Escape rename kept wrong title: {kept!r}")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 87 node rename contract")


if __name__ == "__main__":
    main()
