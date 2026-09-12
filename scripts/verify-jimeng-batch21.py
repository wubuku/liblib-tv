"""Jimeng clone batch 21 verifier — canvas navigation semantics (source-extracted).

SOURCE_FACT (batch 21 extraction): blank LEFT-drag does NOT pan; plain wheel
PANS vertically; ctrl+wheel zooms; middle-drag pans (CLONE_DECISION).
Also: keyboard ⌘1 sets zoom to 100%, ⇧1 fits canvas (readout changes).
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")

CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}


def viewport_transform(page) -> str:
    return page.evaluate(
        "() => getComputedStyle(document.querySelector('.react-flow__viewport')).transform"
    )


def zoom_text(page) -> str:
    return page.evaluate(
        "() => document.querySelector('.jimeng-bottom-dock').textContent.match(/\\d+%/)?.[0]"
    )


def main() -> None:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []

    with sync_playwright() as p:
        ctx = p.chromium.launch(headless=True)
        page = ctx.new_page()
        page.set_viewport_size(VIEWPORT)  # type: ignore[arg-type]
        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        # blank left-drag must NOT pan
        vp0 = viewport_transform(page)
        page.mouse.move(1500, 700)
        page.mouse.down()
        page.mouse.move(1350, 620, steps=8)
        page.mouse.up()
        page.wait_for_timeout(500)
        vp1 = viewport_transform(page)
        if vp0 != vp1:
            failures.append("blank left-drag panned the canvas (should not)")

        # plain wheel pans vertically (translate Y changes, scale unchanged)
        vp_a = viewport_transform(page)
        page.mouse.move(800, 600)
        page.mouse.wheel(0, 240)
        page.wait_for_timeout(700)
        vp_b = viewport_transform(page)
        if vp_a == vp_b:
            failures.append("plain wheel did not pan")
        scale_a = vp_a.split(",")[0].replace("matrix(", "")
        scale_b = vp_b.split(",")[0].replace("matrix(", "")
        if scale_a != scale_b:
            failures.append(f"plain wheel changed scale: {scale_a} → {scale_b}")

        # ctrl+wheel zooms
        page.keyboard.down("Control")
        page.mouse.wheel(0, -240)
        page.keyboard.up("Control")
        page.wait_for_timeout(700)
        vp_c = viewport_transform(page)
        if vp_b == vp_c:
            failures.append("ctrl+wheel did not zoom")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch21-nav-1680.png")
        )

        # ⌘1 → zoom 100%
        page.keyboard.press("Meta+1")
        page.wait_for_timeout(800)
        z = zoom_text(page)
        if z != "100%":
            failures.append(f"⌘1 zoom: {z} (want 100%)")

        # ⇧1 → fit (readout changes away from 100%)
        page.keyboard.press("Shift+1")
        page.wait_for_timeout(900)
        z2 = zoom_text(page)
        if z2 == "100%":
            failures.append("⇧1 did not fit canvas")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 21 navigation contract")


if __name__ == "__main__":
    main()
