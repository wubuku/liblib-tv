#!/usr/bin/env python3
"""Batch 621 — two-row timeline toolbar on narrow screens.

Batch 618 made the toolbar's overflow honest (content clips at the content box
instead of painting under the right strip) but left the underlying squeeze in
place.  Measured across widths, the left cluster's window is

    window = viewport − 8 (px-2) − 260 (the reserve for the right strip)

against a constant ~776px of content, so:

    viewport   390   600   768   899  1024  1280+
    window     122   332   500   631   756  1012
    hidden     654   444   276   145    20     0

The toolbar only fits above ~1044px, and at 390 barely a sixth of it was on
screen.  Below the project's existing 899px breakpoint the right strip stops
floating over the right end and takes its own row, which makes the window
`viewport − 16` instead: 899 and up fits outright, 768 is 24px short, and 390
goes from 654px hidden to 402px — still not whole, but no longer a sliver.

The collapsed state needed its own number: two rows eat 72px, so 88 − 72 would
leave a 16px track strip.  Below the breakpoint the collapsed height becomes
124 = 36 + 36 + 52, which keeps the track strip exactly where it is today.

One pre-existing blemish comes with it: 新建轨道's label wrapped to two lines
and overflowed its 24px box at every width (1920/1440/390 measured identical).
It had simply never been on screen — it lives past the fold of the scrolling
cluster.  82px wide with a 13px four-character label and a 13px icon leaves
13px for padding, so the label only fits on one line with ~6px per side.

Usage: python3 verify-liblib-batch621.py
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = ROOT / "docs/research/liblib-canvas-batch621-2026-10-01/runtime-audit.json"

_spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(b617)

IGNORE_CONSOLE = (
    "The attached 3D object must be a part of the scene graph",
    "webpack-hmr",
    "WebSocket",
    "Failed to load resource",
    "nextjs-dev-overlay",
    "src/components/jimeng/nodes/JimengTextNode.tsx",
    "src/components/jimeng/JimengHelpMenu.tsx",
    "src/components/jimeng/nodes/JimengTimelineNode.tsx",
)

# Below the breakpoint the strip is its own row; the numbers are what batch 621
# measured, not aspirations: window, strip position, strip top offset from the
# toolbar's first row, and the track strip height.
NARROW = {"width": 390, "height": 844}
TABLET = {"width": 768, "height": 1024}
WIDE = {"width": 1920, "height": 1150}

TOOLBAR_JS = """() => {
  const at = (el) => { const r = el.getBoundingClientRect();
    return [Math.round(r.x*10)/10, Math.round(r.y*10)/10,
            Math.round(r.width*10)/10, Math.round(r.height*10)/10]; };
  const host = document.querySelector('[data-director-timeline-controls-scroll]');
  const header = document.querySelector('[data-director-timeline-controls]');
  const strip = document.querySelector('[data-director-timeline-strip-right]');
  const timeline = document.querySelector('[data-director-timeline]');
  const tracks = document.querySelector('[data-director-timeline-track-list]');
  const zoom = document.querySelector('[data-director-timeline-zoom-cluster]');
  const addTrack = document.querySelector('[data-director-add-track]');
  const range = addTrack ? document.createRange() : null;
  if (range) range.selectNodeContents(addTrack);
  return {
    vw: innerWidth,
    timeline: at(timeline), header: at(header), strip: at(strip),
    stripPosition: getComputedStyle(strip).position,
    headerPaddingRight: getComputedStyle(header).paddingRight,
    host: at(host), window: host.clientWidth, content: host.scrollWidth,
    hidden: Math.max(0, host.scrollWidth - host.clientWidth),
    zoom: zoom ? at(zoom) : null,
    exportBtn: (() => { const e = document.querySelector('[data-director-export-trigger]');
      return e ? at(e) : null; })(),
    trackArea: tracks ? Math.round(tracks.getBoundingClientRect().height) : null,
    tracks: tracks ? at(tracks) : null,
    addTrack: addTrack ? {
      box: at(addTrack), clientH: addTrack.clientHeight, scrollH: addTrack.scrollHeight,
      lines: range ? [...range.getClientRects()].map((r) => Math.round(r.height)) : null,
      paddingLeft: getComputedStyle(addTrack).paddingLeft,
      whiteSpace: getComputedStyle(addTrack).whiteSpace,
    } : null,
  };
}"""


class Verifier:
    def __init__(self) -> None:
        self.result: dict[str, Any] = {}
        self.failures: list[str] = []
        self.count = 0

    def check(self, name: str, ok: bool, detail: Any = "") -> None:
        self.count += 1
        self.result[name] = {"ok": bool(ok), "detail": detail}
        if not ok:
            self.failures.append(name)
        print(("  PASS " if ok else "  FAIL ") + name + (f"  {detail}" if detail else ""))


def open_desk(page: Page) -> None:
    b617.open_desk(page)


def leg(v: Verifier, browser: Any, tag: str, viewport: dict[str, int],
        two_rows: bool) -> dict[str, Any]:
    page = browser.new_page(viewport=viewport, device_scale_factor=1)
    console: list[str] = []
    errors: list[str] = []
    page.on("console", lambda m: console.append(f"{m.type}: {m.text}"[:200])
            if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)[:200]))
    try:
        open_desk(page)
        r = page.evaluate(TOOLBAR_JS)
        v.result[f"{tag}:expanded"] = r
        v.check(f"{tag}:the-toolbar-is-still-36px-tall", r["header"][3] == 36,
                detail=r["header"])
        v.check(f"{tag}:the-track-strip-is-below-the-toolbar",
                r["tracks"] is not None and r["tracks"][1] >= r["strip"][1],
                detail={"strip": r["strip"], "tracks": r["tracks"]})
        if two_rows:
            v.check(f"{tag}:the-strip-is-its-own-row",
                    r["stripPosition"] == "static"
                    and r["strip"][1] == r["header"][1] + r["header"][3],
                    detail={"pos": r["stripPosition"], "strip": r["strip"],
                            "header": r["header"]})
            v.check(f"{tag}:the-header-no-longer-reserves-260px",
                    r["headerPaddingRight"] == "8px", detail=r["headerPaddingRight"])
            v.check(f"{tag}:the-cluster-window-is-the-full-width",
                    r["window"] == r["header"][2] - 16,
                    detail={"window": r["window"], "headerWidth": r["header"][2]})
            v.check(f"{tag}:far-more-of-the-cluster-is-reachable",
                    r["hidden"] < 420, detail={"hidden": r["hidden"],
                                               "window": r["window"]})
            v.check(f"{tag}:the-zoom-cluster-and-export-are-both-fully-visible",
                    r["zoom"] is not None and r["exportBtn"] is not None
                    and r["zoom"][0] <= 8 and r["exportBtn"][0] + r["exportBtn"][2]
                    <= r["strip"][0] + r["strip"][2],
                    detail={"zoom": r["zoom"], "export": r["exportBtn"],
                            "strip": r["strip"]})
            v.check(f"{tag}:the-track-strip-is-103px",
                    r["trackArea"] == 103, detail=r["trackArea"])
        else:
            v.check(f"{tag}:the-strip-is-still-floating-right",
                    r["stripPosition"] == "absolute"
                    and abs(r["strip"][0] + r["strip"][2] - r["header"][0]
                            - r["header"][2]) < 0.6,
                    detail={"pos": r["stripPosition"], "strip": r["strip"],
                            "header": r["header"]})
            v.check(f"{tag}:the-260px-reserve-is-still-there",
                    r["headerPaddingRight"] == "260px", detail=r["headerPaddingRight"])
            v.check(f"{tag}:the-desktop-track-strip-is-145px",
                    r["trackArea"] == 145, detail=r["trackArea"])
        a = r["addTrack"]
        v.check(f"{tag}:新建轨道-stays-on-one-line",
                a is not None and a["clientH"] == a["scrollH"],
                detail={"clientH": a["clientH"], "scrollH": a["scrollH"],
                        "lines": a["lines"]} if a else None)
        v.check(f"{tag}:新建轨道-keeps-the-source-width",
                a is not None and a["box"][2] == 82, detail=a["box"] if a else None)

        # collapsed
        page.locator("[data-director-timeline-collapse]").click(timeout=15_000)
        page.wait_for_timeout(700)
        c = page.evaluate(TOOLBAR_JS)
        v.result[f"{tag}:collapsed"] = c
        if two_rows:
            v.check(f"{tag}:collapsed-keeps-a-124px-timeline",
                    c["timeline"][3] == 124, detail=c["timeline"])
            v.check(f"{tag}:collapsed-keeps-a-52px-track-strip",
                    c["trackArea"] == 51 or c["trackArea"] == 52,
                    detail=c["trackArea"])
        else:
            v.check(f"{tag}:collapsed-stays-88px-on-desktop",
                    c["timeline"][3] == 88, detail=c["timeline"])

        # The regression this batch's two-row layout introduced: the strip-right
        # became a static flex item, so its z-30 started creating a stacking
        # context and trapped the export panel's z-50 below the resize handle
        # (z-40).  The submit button then lost the hit test.  Pin the fix here so
        # it is guarded by this batch's own verifier, not only 619's.
        if two_rows:
            page.locator("[data-director-export-trigger]").first.click(timeout=15_000)
            page.locator("[data-director-export-panel]").first.wait_for(
                state="visible", timeout=15_000)
            page.wait_for_timeout(500)
            page.mouse.move(5, 5)
            page.wait_for_timeout(150)
            hit = page.evaluate(
                """() => {
                  const s = document.querySelector('[data-director-export-submit]');
                  const r = s.getBoundingClientRect();
                  const el = document.elementFromPoint(r.x + r.width/2, r.y + r.height/2);
                  return {hit: el ? (el.getAttribute('data-director-export-submit') !== null
                                    ? 'submit' : (el.getAttribute('aria-label') || el.tagName.toLowerCase())) : null,
                          box: [r.x, r.y, r.width, r.height]};
                }""")
            v.result[f"{tag}:export-submit-hit"] = hit
            v.check(f"{tag}:the-export-panel-submit-still-takes-the-hit",
                    hit["hit"] == "submit", detail=hit)

        noise = [x for x in console if any(k in x for k in IGNORE_CONSOLE)]
        real_console = [x for x in console if not any(k in x for k in IGNORE_CONSOLE)]
        real_errors = [e for e in errors if not any(k in e for k in IGNORE_CONSOLE)]
        v.check(f"{tag}:no-page-errors", not real_errors, detail=real_errors[:4])
        v.check(f"{tag}:no-console-errors", not real_console, detail=real_console[:4])
        v.result[f"{tag}:diagnostics"] = {"consoleErrors": len(console),
                                          "filtered": len(noise),
                                          "pageErrors": len(errors)}
    finally:
        page.close()
    return r


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 621,
        "title": "Two-row timeline toolbar below 900px, and stop 新建轨道's "
                 "label wrapping at every width",
        "date": "2026-10-01",
        "sourceEvidence": [
            "no live source reading: the shared source tab is at 1600x1000 "
            "with another user in it (probe616), so this batch makes no "
            "fidelity claim",
            "/tmp/dbg621.py: window vs content for ten viewport widths — the "
            "cluster's window is viewport - 8 - 260 against a constant ~776px "
            "of content, so it only fits above ~1044px (measured: 1280 and up "
            "have 0 hidden, 1024 has 20, 899 has 145, 768 has 276, 600 has "
            "444, 390 has 654)",
            "/tmp/dbg621b.py: the breakpoint actually lands between 898 and "
            "899, not between 899 and 900 — Tailwind v4 compiles max-[899px] "
            "to `@media (width < 899px)`, a strict inequality, while "
            "matchMedia('(max-width: 899px)') reports true at 899",
            "/tmp/dbg621c.py: the cluster's content is a constant ~776px; the "
            "larger scrollWidth readings at wide viewports are just "
            "scrollWidth collapsing to clientWidth when nothing overflows",
            "/tmp/dbg621d.py: the two-row geometry and the collapsed numbers "
            "at 390 and 768, plus screenshots",
            "/tmp/dbg621e.py: 新建轨道 measured identical at 1920/1440/390 — "
            "box 82x24, clientHeight 24, scrollHeight 26, three line boxes",
        ],
        "claims": {
            "cloneDecision": [
                "below the project's existing 899px breakpoint the right strip "
                "stops floating over the toolbar's right end and becomes a "
                "second row, and the header drops its pr-[260px] reserve. The "
                "cluster's window becomes viewport - 16, so 899 fits outright, "
                "768 is 24px short and 390 goes from 654px hidden to 402px. "
                "390 still cannot show 776px of content; that is physics, and "
                "this batch does not claim otherwise",
                "the collapsed height below the breakpoint becomes 124 = 36 + "
                "36 + 52 so the track strip keeps exactly the 52px it has "
                "today (88 - 72 would have left 16)",
                "新建轨道's label is locked to one line with px-1.5 and "
                "whitespace-nowrap. 82 - 52 (label) - 13 (icon) - 4 (gap) "
                "leaves 13px for padding, so ~6px per side is what makes the "
                "source's measured 82x24 box hold its measured 13px label on "
                "one line. The outer width, x, gap and radii that batch 601 "
                "pins are unchanged",
            ],
            "notClaimed": [
                "anything about the source at all — the source's director desk "
                "at phone widths has never been sampled",
                "the 899px breakpoint itself: this batch reuses the project's "
                "existing max-[899px] and did not touch the convention, but "
                "Tailwind's strict inequality means the switch happens at "
                "898/899 rather than 899/900. That off-by-one predates this "
                "batch and is recorded, not fixed — changing it would move "
                "every other max-[899px] rule in the codebase at once",
                "the 900-1043px band is left alone even though 144-20px of the "
                "cluster is hidden there: that band keeps the source-measured "
                "single-row arrangement (the 260px reserve and the 244px strip "
                "are batch 593/596 readings), and re-arranging desktop widths "
                "is a bigger decision than this batch's evidence supports",
            ],
        },
    }
    v = Verifier()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        leg(v, browser, "phone-390", NARROW, True)
        leg(v, browser, "tablet-768", TABLET, True)
        leg(v, browser, "desktop-1920", WIDE, False)
        browser.close()
    total = v.count
    fails = v.failures
    audit["checks"] = v.result
    audit["result"] = f"{total - len(fails)}/{total} passed"
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_PATH, "w", encoding="utf-8") as f:
        json.dump(audit, f, ensure_ascii=False, indent=2)
    print(f"\n{audit['result']}")
    if fails:
        print("FAILED: " + ", ".join(fails))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
