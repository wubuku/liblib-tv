#!/usr/bin/env python3

"""Verify Batch 186: footer icon buttons aligned to source order and glyphs.

Source evidence (2026-09-08 CDP, source-footer-icons.json): the video panel
footer holds four 32px icon buttons after the params trigger — doc-sparkle
(libtv, viewBox 0 0 20 20), 文A translate (libtv, 0 0 19.71 18), lucide
settings2 (0 0 24 24), and the generate up-arrow (libtv, 0 0 18 18,
inverted) — with the credits block sitting between settings2 and generate.
None of the source buttons carry aria/title and their click semantics are
unsampled. The clone now matches the order and embeds the harvested libtv
paths (settings2 stays lucide — the source uses lucide there too).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch186-2026-09-08"
    / "runtime-audit.json"
)


def attach_errors(page: Page) -> list[str]:
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(f"console:{message.type}:{message.text}")
        if message.type == "error"
        else None,
    )
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch186 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(500)

    page.locator('.react-flow__node[data-id="v-UGQZzZOpbv"]').click(force=True)
    page.wait_for_timeout(400)

    footer = page.locator("[data-video-generation-panel] footer").first
    icons = footer.locator("button[data-footer-icon], button[aria-label='翻译视频提示词']")
    check("footer:three-icon-buttons", icons.count() == 3)
    check(
        "footer:order",
        icons.nth(0).get_attribute("data-footer-icon") == "doc-sparkle"
        and icons.nth(1).get_attribute("aria-label") == "翻译视频提示词"
        and icons.nth(2).get_attribute("data-footer-icon") == "settings2",
    )

    # harvested glyph paths
    sparkle = footer.locator("button[data-footer-icon='doc-sparkle'] svg")
    check("footer:sparkle-viewbox", sparkle.get_attribute("viewBox") == "0 0 20 20")
    translate = footer.locator("button[aria-label='翻译视频提示词'] svg")
    check("footer:translate-viewbox", translate.get_attribute("viewBox") == "0 0 19.71 18")

    # generate button uses the harvested up-arrow
    gen = page.locator("[data-video-generate-submit]")
    gen_svg = gen.locator("svg").first
    check("footer:generate-arrow-viewbox", gen_svg.get_attribute("viewBox") == "0 0 18 18")

    # credits block sits between settings2 and the generate button
    order_ok = page.evaluate(
        """() => {
        const panel = document.querySelector('[data-video-generation-panel] footer');
        const settings2 = panel.querySelector("button[data-footer-icon='settings2']");
        const credits = panel.querySelector('[data-video-credits]');
        const gen = panel.querySelector('[data-video-generate-submit]');
        return settings2.compareDocumentPosition(credits) & Node.DOCUMENT_POSITION_FOLLOWING
          && credits.compareDocumentPosition(gen) & Node.DOCUMENT_POSITION_FOLLOWING;
        }"""
    )
    check("footer:credits-between", bool(order_ok))

    # generate still functional: click adds pending state via title change? keep
    # to the desktop contract of batch125/33 instead — assert title exists
    check("footer:generate-title", (gen.get_attribute("title") or "") == "生成视频")

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 186, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch186: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
