"""Jimeng clone batch 45 verifier — node title hover (native tooltip attr).

SOURCE_FACT (batch 45): the source title span carries the full filename in a
native `title` attribute (browser hover tooltip); the visible text stays
truncated.
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

        title = page.evaluate(
            """() => {
                const span = [...document.querySelectorAll('.react-flow__node-video span')]
                    .find(s => s.getAttribute('title')?.includes('sb_518102884867410fb'));
                return span ? {
                    title: span.getAttribute('title'),
                    visible: span.textContent.trim(),
                    truncated: span.clientWidth < span.scrollWidth,
                } : null;
            }"""
        )
        if not title:
            failures.append("title span with native title attr not found")
        else:
            if "sb_518102884867410fb...20260622155459-tf5q2" not in title["title"]:
                failures.append(f"title attr: {title['title']!r}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch45-title-hover-1680.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 45 title hover contract")


if __name__ == "__main__":
    main()
