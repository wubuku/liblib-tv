#!/usr/bin/env python3
"""Verify Batch 607: timeline panel shell + the drag-to-resize top handle.

Source-site live sampling 2026-10-01, 1920x1150, director desk open.

## Measured source structure

    div.pointer-events-auto.relative.flex.w-full.min-w-0.flex-col
        .overflow-hidden.rounded-tl-none.rounded-tr-none
        .border-t.border-white/10.bg-[#1f1f1f].text-white
        .shadow-[0_-18px_48px_rgba(0,0,0,0.24)].backdrop-blur-xl
                                                    1920x130 @(0,1020)
      ├ div.absolute.inset-x-0.top-0.z-40.h-2.cursor-ns-resize
      │                              1920x8 @(0,1021)   touch-action: auto
      │                                                   user-select: none
      ├ div.absolute.inset-x-0.top-0.z-30.flex.min-w-0.gap-[2px]
      │                              1920x36 @(0,1021)
      │   ├ div.shrink-0.bg-[#1f1f1f]            320x36 @(0,1021)
      │   └ div.relative.min-w-0.flex-1.overflow-hidden.bg-[#212121]
      │                                            1598x36 @(322,1021)
      ├ div.pointer-events-none.absolute.bottom-0.top-0.z-50.overflow-hidden
      │                                            1598x129 @(322,1021)
      └ div.min-h-0.flex-1                        1920x129 @(0,1021)

The handle sits at z-40, i.e. **above** the 36px header row (z-30), so it caps
the top 8px of that row. `elementFromPoint` at the handle's centre returns the
handle itself, so the affordance is genuinely grabbable in the source.

The clone had no panel-level handle at all (its `cursor-ew-resize` uses are the
lane splitter and the playhead, not the panel edge), and its shell read
`bg-[#161616] border-white/[0.08]` with no shadow and no backdrop blur.

What this batch changes:
  * the panel adopts the source's shell: `#1f1f1f`, `border-white/10`,
    `rounded-tl-none rounded-tr-none`, `shadow-[0_-18px_48px_rgba(0,0,0,0.24)]`,
    `backdrop-blur-xl`, `min-w-0`;
  * a real drag-to-resize handle at the top edge, 8px, `z-40`, `cursor-ns-resize`,
    resizing the panel height (up is taller);
  * height is **view state** — per batch 599's conclusion (the document schema
    deliberately omits view-state fields, exactly as `timeline.zoom` does) it
    lives in component state next to `timelineCollapsed` and never reaches the
    persisted schema.

Deliberate deviations:
  * the clone keeps `overflow-visible` where the source has `overflow-hidden`:
    several absolutely positioned drop-downs inside the timeline (track menus,
    the curve editor) rely on not being clipped. Switching to hidden would
    require portalling them out, which is out of scope. Recorded, not faked.
  * the drag range (88..420) is clone-chosen; the source's is unmeasured
    because dragging its handle would change the panel height inside the real
    project, which needs authorisation.
  * the source's header row measured two children here (320 + 1598, gap 2px);
    an earlier snapshot also showed a 244px right cluster at (1676,1021) that
    was absent this time. That reading is treated as state-dependent and is not
    claimed.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT / "docs/research/liblib-canvas-batch607-2026-10-01/runtime-audit.json"
)
SCREENSHOT = ROOT / "docs/design-references/liblib-timeline-resize-607-1920.png"

VIEWPORT = {"width": 1920, "height": 1150}
DEFAULT_H = 182
HANDLE_H = 8
MIN_H = 88
MAX_H = 420


def alpha_of(colour: str) -> float:
    for pattern in (
        r"rgba?\([^)]*?,\s*([0-9.]+)\s*\)$",
        r"oklab\([^)]*?/\s*([0-9.]+)\s*\)",
        r"lab\([^)]*?/\s*([0-9.]+)\s*\)",
    ):
        match = re.search(pattern, colour)
        if match:
            return float(match.group(1))
    return 1.0


READ = """() => {
  const t = document.querySelector('[data-director-timeline]');
  const h = document.querySelector('[data-director-timeline-resize-handle]');
  if (!t) return {error: 'no timeline'};
  const cs = (el) => getComputedStyle(el);
  const at = (el) => { const r = el.getBoundingClientRect();
    return {x: r.x, y: r.y, w: r.width, h: r.height, right: r.right}; };
  const c = cs(t);
  const hc = h ? cs(h) : null;
  const hr = h ? h.getBoundingClientRect() : null;
  const hit = hr ? document.elementFromPoint(hr.x + hr.width / 2, hr.y + hr.height / 2) : null;
  return {panel: {box: at(t), backgroundColor: c.backgroundColor,
                  borderTopWidth: c.borderTopWidth, borderTopColor: c.borderTopColor,
                  boxShadow: c.boxShadow, backdropFilter: c.backdropFilter,
                  minWidth: c.minWidth, height: c.height, overflowY: c.overflowY,
                  attr: t.getAttribute('data-director-timeline-height'),
                  className: (t.className || '').toString()},
          handle: h ? {box: at(h), cursor: hc.cursor, zIndex: hc.zIndex,
                        position: hc.position, backgroundColor: hc.backgroundColor,
                        touchAction: hc.touchAction, userSelect: hc.userSelect,
                        role: h.getAttribute('role'),
                        orientation: h.getAttribute('aria-orientation'),
                        label: h.getAttribute('aria-label'),
                        className: (h.className || '').toString()} : null,
          hitIsHandle: Boolean(h && hit && (h === hit || h.contains(hit))),
          hitTag: hit ? hit.tagName.toLowerCase() : null};
}"""


def attach_errors(page: Page) -> list[str]:
    errors: list[str] = []
    page.on(
        "console",
        lambda msg: errors.append(f"console.{msg.type}: {msg.text}")
        if msg.type == "error"
        and "TransformControls" not in msg.text
        and "webpack-hmr" not in msg.text
        and "WebSocket" not in msg.text
        else None,
    )
    page.on("pageerror", lambda err: errors.append(f"pageerror: {err}"))
    return errors


def open_director(page: Page) -> None:
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"
    )
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 607" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(1000)


def drag_handle(page: Page, dy: int) -> None:
    box = page.locator("[data-director-timeline-resize-handle]").bounding_box()
    assert box, "resize handle has no box"
    cx = box["x"] + box["width"] / 2
    cy = box["y"] + box["height"] / 2
    page.mouse.move(cx, cy)
    page.mouse.down()
    page.mouse.move(cx, cy + dy, steps=8)
    page.mouse.up()
    page.wait_for_timeout(350)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {
        "viewport": f"{VIEWPORT['width']}x{VIEWPORT['height']}",
        "checks": [],
    }

    def check(name: str, ok: bool, detail: Any = None) -> None:
        result["checks"].append({"name": name, "ok": bool(ok), "detail": detail})

    errors = attach_errors(page)
    open_director(page)
    data = page.evaluate(READ)
    if data.get("error"):
        check("panel:mounted", False, detail=data["error"])
        result["diagnostics"] = {"console": errors[:5]}
        return result
    check("panel:mounted", True)

    panel, handle = data["panel"], data["handle"]

    # --- panel shell -----------------------------------------------------------
    check(
        "panel:bg-1f1f1f",
        panel["backgroundColor"] == "rgb(31, 31, 31)",
        detail=panel["backgroundColor"],
    )
    check(
        "panel:border-top-1px-white-10",
        panel["borderTopWidth"] == "1px"
        and abs(alpha_of(panel["borderTopColor"]) - 0.1) < 0.01,
        detail=f"{panel['borderTopWidth']} {panel['borderTopColor']}",
    )
    check(
        "panel:shadow-0-18px-48px",
        "18px 48px" in panel["boxShadow"] and "0.24" in panel["boxShadow"],
        detail=panel["boxShadow"][:110],
    )
    check(
        "panel:backdrop-blur",
        panel["backdropFilter"] not in ("none", ""),
        detail=panel["backdropFilter"],
    )
    check(
        "panel:rounded-top-none",
        "rounded-tl-none" in panel["className"]
        and "rounded-tr-none" in panel["className"],
        detail=panel["className"][:180],
    )
    check(
        "panel:default-height-182",
        abs(float(panel["height"].rstrip("px")) - DEFAULT_H) < 0.6
        and panel["attr"] == str(DEFAULT_H),
        detail=f"{panel['height']} attr={panel['attr']}",
    )

    # --- the handle ------------------------------------------------------------
    check("handle:mounted", handle is not None)
    if handle:
        check(
            "handle:1920x8",
            abs(handle["box"]["w"] - VIEWPORT["width"]) < 0.6
            and abs(handle["box"]["h"] - HANDLE_H) < 0.6,
            detail=[handle["box"]["w"], handle["box"]["h"]],
        )
        check(
            "handle:flushed-to-panel-top",
            abs(handle["box"]["x"] - panel["box"]["x"]) < 0.6
            and abs(handle["box"]["y"] - (panel["box"]["y"] + 1)) < 0.6,
            detail=[handle["box"]["x"], handle["box"]["y"], panel["box"]["y"]],
        )
        check(
            "handle:cursor-ns-resize",
            handle["cursor"] == "ns-resize",
            detail=handle["cursor"],
        )
        check(
            "handle:absolute-z-40",
            handle["position"] == "absolute" and handle["zIndex"] == "40",
            detail=f"{handle['position']} z={handle['zIndex']}",
        )
        check(
            "handle:transparent",
            alpha_of(handle["backgroundColor"]) == 0.0,
            detail=handle["backgroundColor"],
        )
        check(
            "handle:separator-semantics",
            handle["role"] == "separator"
            and handle["orientation"] == "horizontal"
            and bool(handle["label"]),
            detail=[handle["role"], handle["orientation"], handle["label"]],
        )
    check(
        "handle:hit-testable",
        data["hitIsHandle"],
        detail=f"elementFromPoint -> {data['hitTag']}",
    )

    # --- dragging --------------------------------------------------------------
    drag_handle(page, -80)  # up = taller
    after = page.evaluate(READ)
    grew = float(after["panel"]["height"].rstrip("px"))
    check(
        "drag:up-grows-panel",
        abs(grew - (DEFAULT_H + 80)) < 1.0 and after["panel"]["attr"] == str(DEFAULT_H + 80),
        detail=grew,
    )
    page.screenshot(path=str(SCREENSHOT))

    drag_handle(page, 40)  # back down
    back = page.evaluate(READ)
    check(
        "drag:down-shrinks-panel",
        abs(float(back["panel"]["height"].rstrip("px")) - (DEFAULT_H + 40)) < 1.0,
        detail=back["panel"]["height"],
    )

    # --- clamping --------------------------------------------------------------
    drag_handle(page, -900)
    top = page.evaluate(READ)
    check(
        "clamp:max-420",
        abs(float(top["panel"]["height"].rstrip("px")) - MAX_H) < 1.0,
        detail=top["panel"]["height"],
    )
    drag_handle(page, 1800)
    low = page.evaluate(READ)
    check(
        "clamp:min-88",
        abs(float(low["panel"]["height"].rstrip("px")) - MIN_H) < 1.0,
        detail=low["panel"]["height"],
    )

    # --- the collapse control still owns its own semantics ---------------------
    page.locator('button[aria-label="时间线最小化"]').click()
    page.wait_for_timeout(350)
    collapsed = page.evaluate(READ)
    check(
        "collapse:independent-of-resize",
        abs(float(collapsed["panel"]["height"].rstrip("px")) - MIN_H) < 0.6
        and collapsed["panel"]["attr"] == str(MIN_H),
        detail=f"{collapsed['panel']['height']} attr={collapsed['panel']['attr']}",
    )

    check("no-console-errors", not errors, detail=errors[:5])
    result["measured"] = {"before": data, "afterDrag": after, "collapsed": collapsed}
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT)
        try:
            result = run_desktop(page)
        finally:
            browser.close()
    failed = [c for c in result["checks"] if not c["ok"]]
    print(
        f"Batch 607 verification: {len(result['checks']) - len(failed)}"
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
    print(f"wrote {SCREENSHOT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
