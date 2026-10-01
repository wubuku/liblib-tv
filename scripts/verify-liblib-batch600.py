#!/usr/bin/env python3
"""Verify Batch 600: 车道区容器栈、2px 列间隙、tiny-scrollbar、右缘圆角。

Source facts (live CDP sampling of the source director desk at 1920x1150,
2026-10-01, /tmp/src593/probe43 + probe44 + probe45).

Walking up from the lane canvas, the source stacks three boxes to the right of
the track list:

    div.flex.min-h-full.min-w-0.gap-[2px]      1920x130 @(0,1021)   gap: 2px
    |- left column  z-10 shrink-0 bg-[#1f1f1f] 320x130 @(0,1021)
    |                                              border-right: 0px
    |- pane       relative min-w-0 flex-1 bg-[#1f1f1f]   1598x129 @(322,1021)
       |- scroller tiny-scrollbar h-full min-w-0
       |           overflow-x-auto overflow-y-hidden      1598x129, scrollWidth 2124
          |- wrap relative shrink-0 overflow-hidden rounded-r-md bg-black/15
             2124x115 @(322,1021), border-radius 6px 0 0 0
             |- canvas block h-full cursor-ew-resize   2124x115

So the 2px between the columns is a flex GAP, not a border: `elementFromPoint`
at x=320 and x=321 lands on the flex parent itself, and the left column's
computed border-right-width is 0px.

The content box is sized to its content (2124x115) inside a taller pane
(1598x129), so `rounded-r-md` puts the corner at the far end of the scroll
range, not at the viewport edge, and 14px of the pane's #1f1f1f shows below.

The scroller carries the source's own utility class. Its rules were lifted
verbatim out of the shipped stylesheet
liblibtv_online/static/_next/static/chunks/2i0zx3s0wp9uo.css:

    .tiny-scrollbar{scrollbar-gutter:stable;scrollbar-width:thin;
      scrollbar-color:var(--border-emphasis) transparent}
    .tiny-scrollbar::-webkit-scrollbar{width:3px;height:3px}
    .tiny-scrollbar::-webkit-scrollbar-track{background:0 0}
    .tiny-scrollbar::-webkit-scrollbar-thumb{
      background-color:var(--border-emphasis);border-radius:3px}

with `--border-emphasis` resolving to #86909c on the source's :root (and on the
scroller itself). The clone had no such class and used the browser default.

The clone had a single scroller, a 1px `border-r border-white/[0.07]` on the
left column (pushing the right column 1px left of the source's 322), and
`min-h-full` on the content, so the right corner was square and the pane colour
never showed.

What this does NOT claim:
- `bg-black/15` on the source's content wrapper is not observable: the wrapper
  and the canvas are both 2124x115 and the canvas paints opaquely, so the
  wrapper's own colour is never seen. The clone keeps the observable #212121.
- the clone's seed data has two objects (4 lane rows) against the source
  project's one object (2 rows), so the clone's lane content is taller than its
  pane and the last row is clipped. The source does not clip at that row count.
  That is a seed-data difference, not a container difference, and no height
  contract was changed for it.
- `scrollbar-gutter: stable` reserves 3px of the scroller's client width on
  platforms with classic scrollbars; on this macOS box the scrollbars are
  overlays, so the reservation is not observable either way.

Contract asserted here:
1. the two columns are separated by a 2px flex gap and the left column has no
   right border;
2. the left column is 320px and the pane starts at 322;
3. the pane is `bg-[#1f1f1f]` and fills the remaining width;
4. the scroller between them is the 3px `tiny-scrollbar` (thin / stable /
   #86909c) and scrolls horizontally;
5. the content box is content-sized, keeps `rounded-r-md` on the right only
   (6px right, 0 left) and clips its own overflow;
6. the content still paints the #212121 lane base;
7. no diagnostics.
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
    / "liblib-canvas-batch600-2026-10-01"
    / "runtime-audit.json"
)

GLOBALS = ROOT / "src/app/globals.css"
PANE_BG = "rgb(31, 31, 31)"
CANVAS_BG = "rgb(33, 33, 33)"
SCROLLBAR_COLOR = "rgb(134, 144, 156)"


def attach_errors(page: Page) -> list[str]:
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(f"console:{message.type}:{message.text}")
        if message.type == "error"
        and "TransformControls" not in message.text
        else None,
    )
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    return errors


READ = """() => {
  const cs = (el) => getComputedStyle(el);
  const at = (el) => { const r = el.getBoundingClientRect();
    return {x: Math.round(r.x), y: Math.round(r.y),
            w: Math.round(r.width), h: Math.round(r.height)}; };
  const list = document.querySelector('[data-director-timeline-track-list]');
  const canvas = document.querySelector('[data-director-timeline-canvas]');
  const scroller = canvas.parentElement;
  const pane = scroller.parentElement;
  const flex = list.parentElement;
  const info = (el) => ({box: at(el), background: cs(el).backgroundColor,
    borderRightWidth: cs(el).borderRightWidth,
    radiusRight: cs(el).borderTopRightRadius,
    radiusLeft: cs(el).borderTopLeftRadius,
    overflowX: cs(el).overflowX, overflowY: cs(el).overflowY,
    scrollbarWidth: cs(el).scrollbarWidth,
    scrollbarGutter: cs(el).scrollbarGutter,
    scrollbarColor: cs(el).scrollbarColor,
    scrollWidth: el.scrollWidth, clientWidth: el.clientWidth,
    cls: (el.className || '').toString()});
  return {
    flex: {...info(flex), gap: cs(flex).gap},
    list: info(list), pane: info(pane),
    scroller: info(scroller), canvas: info(canvas),
    tinyScrollbarRules: document.querySelectorAll('.tiny-scrollbar').length,
  };
}"""


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1920x1150", "checks": []}

    def check(name: str, ok: bool, detail: Any = None) -> None:
        result["checks"].append({"name": name, "ok": bool(ok), "detail": detail})

    # 0) the utility itself is declared with the source's own values
    css = GLOBALS.read_text()
    check(
        "static:tiny-scrollbar-declared",
        ".tiny-scrollbar {" in css
        and "scrollbar-gutter: stable;" in css
        and "scrollbar-width: thin;" in css
        and "#86909c" in css
        and "width: 3px;" in css
        and "height: 3px;" in css,
        detail="globals.css carries the lifted .tiny-scrollbar rules",
    )

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 600" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(700)
    page.mouse.move(1500, 400)
    page.wait_for_timeout(250)
    snap = page.evaluate(READ)
    result["stack"] = snap

    # 1) a 2px gap, not a border
    check(
        "columns:2px-gap-not-border",
        snap["flex"]["gap"] == "2px"
        and snap["list"]["borderRightWidth"] == "0px"
        and snap["pane"]["box"]["x"] - snap["list"]["box"]["x"]
        - snap["list"]["box"]["w"] == 2,
        detail={"gap": snap["flex"]["gap"],
                "listBorderRight": snap["list"]["borderRightWidth"],
                "delta": snap["pane"]["box"]["x"] - snap["list"]["box"]["x"]
                - snap["list"]["box"]["w"]},
    )

    # 2) the source's column geometry
    check(
        "columns:320-then-322",
        snap["list"]["box"]["w"] == 320 and snap["list"]["box"]["x"] == 0
        and snap["pane"]["box"]["x"] == 322,
        detail={"list": snap["list"]["box"], "pane": snap["pane"]["box"]},
    )

    # 3) the pane
    check(
        "pane:1f1f1f-fills-remainder",
        snap["pane"]["background"] == PANE_BG
        and snap["pane"]["box"]["x"] + snap["pane"]["box"]["w"]
        == snap["flex"]["box"]["w"],
        detail={"background": snap["pane"]["background"],
                "box": snap["pane"]["box"], "flex": snap["flex"]["box"]},
    )

    # 4) the scroller carries the source's 3px scrollbar and scrolls
    check(
        "scroller:tiny-scrollbar-3px",
        snap["scroller"]["scrollbarWidth"] == "thin"
        and snap["scroller"]["scrollbarGutter"] == "stable"
        and snap["scroller"]["scrollbarColor"].startswith(SCROLLBAR_COLOR)
        and snap["scroller"]["overflowX"] == "auto"
        and snap["scroller"]["overflowY"] == "hidden"
        and snap["scroller"]["scrollWidth"] > snap["scroller"]["clientWidth"],
        detail={"width": snap["scroller"]["scrollbarWidth"],
                "gutter": snap["scroller"]["scrollbarGutter"],
                "color": snap["scroller"]["scrollbarColor"],
                "scroll": [snap["scroller"]["scrollWidth"],
                           snap["scroller"]["clientWidth"]]},
    )

    # 5) the content box: content-sized, right-only radius, clips itself
    check(
        "content:content-sized-rounded-right-only",
        snap["canvas"]["radiusRight"] == "6px"
        and snap["canvas"]["radiusLeft"] == "0px"
        and snap["canvas"]["overflowX"] == "hidden"
        and snap["canvas"]["overflowY"] == "hidden"
        and snap["canvas"]["box"]["w"] > snap["pane"]["box"]["w"],
        detail={"radius": [snap["canvas"]["radiusRight"], snap["canvas"]["radiusLeft"]],
                "overflow": [snap["canvas"]["overflowX"], snap["canvas"]["overflowY"]],
                "w": snap["canvas"]["box"]["w"], "paneW": snap["pane"]["box"]["w"]},
    )

    # 6) the lane base is still painted
    check(
        "content:lane-base-212121",
        snap["canvas"]["background"] == CANVAS_BG,
        detail=snap["canvas"]["background"],
    )

    # 7) scrolling the lane area moves the content, not the track list
    scrolled = page.evaluate(
        """() => {
          const list = document.querySelector('[data-director-timeline-track-list]');
          const scroller = document.querySelector('[data-director-timeline-canvas]').parentElement;
          const before = list.getBoundingClientRect().x;
          scroller.scrollLeft = 120;
          const canvas = document.querySelector('[data-director-timeline-canvas]');
          return {listX: Math.round(list.getBoundingClientRect().x), before: Math.round(before),
                  scrollLeft: scroller.scrollLeft,
                  maxScroll: scroller.scrollWidth - scroller.clientWidth,
                  canvasX: Math.round(canvas.getBoundingClientRect().x)};
        }"""
    )
    result["scrolled"] = scrolled
    check(
        "scroller:scrolls-content-not-columns",
        scrolled["scrollLeft"] == 120
        and scrolled["listX"] == scrolled["before"] == 0
        and scrolled["canvasX"] == 322 - 120,
        detail=scrolled,
    )

    check("no-console-errors", not errors, detail=errors[:5])
    return result


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1150})
        try:
            result = run_desktop(page)
        finally:
            browser.close()
    failed = [c for c in result["checks"] if not c["ok"]]
    print(
        f"Batch 600 verification: {len(result['checks']) - len(failed)}"
        f"/{len(result['checks'])} checks passed"
    )
    if failed:
        print("FAILED:", json.dumps(failed, ensure_ascii=False, indent=1))
        raise SystemExit(1)
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {AUDIT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
