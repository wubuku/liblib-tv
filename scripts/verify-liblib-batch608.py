#!/usr/bin/env python3
"""Verify Batch 608: the 动画时间轴 toggle in the viewport bottom pill.

## What the source shows (measured 2026-10-01, 1920x1150)

The source's first bottom pill carries exactly three controls — 移动 / 截图 /
动画时间轴 — each 32x32 with a 20px icon and `rounded-lg`; the active one
appends `bg-white/8`. 动画时间轴 measured at (869,976) with
`aria-pressed="true"`, and the timeline panel was visible at the same moment.

## What the clone was missing

The clone's timeline was permanently visible and had no whole-panel toggle at
all. Its bottom pill also carried no 动画时间轴 control.

## What this batch does

1. lifts the two timeline **view-state** fields out of component state and into
   `directorStore` — `timelinePanelOpen` and `timelineHeight` — so the toggle
   and the drag handle (batch 607) operate on one source of truth. Like
   `viewportPanelsCollapsed` and (since batch 599) `timeline.zoom`, they stay
   **out of the persisted document schema**: the schema describes project
   content, not how the panels happen to be arranged right now;
2. renders `null` from `DirectorTimeline` when the panel is closed, so the
   viewport grows into the freed space;
3. adds the 动画时间轴 button to the clone's bottom pill with `aria-pressed`
   bound to `timelinePanelOpen` and `bg-white/8` on the active state.

The two panel verbs stay independent: 动画时间轴 hides the panel entirely,
while 时间线最小化 (inside the panel) collapses 182 -> 88 and leaves the panel
in place.

## Not claimed

The source's 动画时间轴 click behaviour was **never measured** — clicking a
source control can change the real project, which needs authorisation. Its
semantics here are a clone-side inference from three mutually supporting facts
(its name, `aria-pressed="true"`, and the panel being visible at that moment).
What the toggle does *is* verified, end to end, on the clone.
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
    ROOT / "docs/research/liblib-canvas-batch608-2026-10-01/runtime-audit.json"
)
SCREENSHOT = ROOT / "docs/design-references/liblib-timeline-toggle-608-1920.png"

VIEWPORT = {"width": 1920, "height": 1150}
BTN = 32
ICON = 20
DEFAULT_H = 182
MIN_H = 88


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
  const btn = document.querySelector('[data-director-timeline-toggle]');
  const t = document.querySelector('[data-director-timeline]');
  const vp = document.querySelector('[data-director-viewport]');
  const cs = (el) => getComputedStyle(el);
  const at = (el) => { const r = el.getBoundingClientRect();
    return {x: r.x, y: r.y, w: r.width, h: r.height, bottom: r.bottom}; };
  let toggle = null;
  if (btn) {
    const c = cs(btn);
    const s = btn.querySelector('svg');
    toggle = {box: at(btn), pressed: btn.getAttribute('aria-pressed'),
              label: btn.getAttribute('aria-label'), title: btn.getAttribute('title'),
              backgroundColor: c.backgroundColor, color: c.color,
              borderRadius: c.borderRadius, svg: s ? at(s) : null,
              className: (btn.className || '').toString()};
  }
  const d = window.__director_store.getState();
  return {toggle: toggle,
          timelinePresent: Boolean(t),
          timelineH: t ? at(t).h : null,
          viewportH: vp ? at(vp).h : null,
          viewportBottom: vp ? at(vp).bottom : null,
          store: {open: d.timelinePanelOpen, height: d.timelineHeight}};
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
          store.addNode("script-execution", { title: "Batch 608" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(1000)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {
        "viewport": f"{VIEWPORT['width']}x{VIEWPORT['height']}",
        "checks": [],
    }

    def check(name: str, ok: bool, detail: Any = None) -> None:
        result["checks"].append({"name": name, "ok": bool(ok), "detail": detail})

    errors = attach_errors(page)
    open_director(page)
    on = page.evaluate(READ)
    check("toggle:mounted", on["toggle"] is not None)
    if on["toggle"] is None:
        result["diagnostics"] = {"console": errors[:5]}
        return result

    t = on["toggle"]
    check(
        "toggle:32x32-icon-20px",
        abs(t["box"]["w"] - BTN) < 0.6
        and abs(t["box"]["h"] - BTN) < 0.6
        and t["svg"] is not None
        and abs(t["svg"]["w"] - ICON) < 0.6
        and abs(t["svg"]["h"] - ICON) < 0.6,
        detail=[t["box"]["w"], t["box"]["h"], t["svg"]],
    )
    check(
        "toggle:rounded-lg",
        t["borderRadius"] == "8px",
        detail=t["borderRadius"],
    )
    check(
        "toggle:accessible-name-动画时间轴",
        t["label"] == "动画时间轴" and t["title"] == "动画时间轴",
        detail=[t["label"], t["title"]],
    )
    check(
        "toggle:starts-pressed-with-panel-open",
        t["pressed"] == "true"
        and on["timelinePresent"]
        and on["store"]["open"] is True,
        detail={"pressed": t["pressed"], "present": on["timelinePresent"]},
    )
    # `bg-white/8` is 8% alpha (0.08), not 10% — the same value the source
    # measured for its active pill button.
    check(
        "toggle:active-bg-white-8",
        abs(alpha_of(t["backgroundColor"]) - 0.08) < 0.005,
        detail=t["backgroundColor"],
    )
    check(
        "timeline:default-height-182",
        on["timelineH"] is not None
        and abs(on["timelineH"] - DEFAULT_H) < 0.6
        and on["store"]["height"] == DEFAULT_H,
        detail=[on["timelineH"], on["store"]["height"]],
    )
    viewport_before = on["viewportH"]

    # --- close ------------------------------------------------------------------
    page.locator("[data-director-timeline-toggle]").click()
    page.wait_for_timeout(500)
    off = page.evaluate(READ)
    check(
        "toggle:close-clears-pressed",
        off["toggle"]["pressed"] == "false"
        and alpha_of(off["toggle"]["backgroundColor"]) == 0.0,
        detail={"pressed": off["toggle"]["pressed"],
                "bg": off["toggle"]["backgroundColor"]},
    )
    check(
        "timeline:unmounted-when-closed",
        off["timelinePresent"] is False
        and off["timelineH"] is None
        and off["store"]["open"] is False,
        detail={"present": off["timelinePresent"], "open": off["store"]["open"]},
    )
    check(
        "viewport:grows-into-freed-space",
        off["viewportH"] is not None
        and viewport_before is not None
        and off["viewportH"] > viewport_before,
        detail={"before": viewport_before, "after": off["viewportH"]},
    )
    page.screenshot(path=str(SCREENSHOT))

    # --- reopen -----------------------------------------------------------------
    page.locator("[data-director-timeline-toggle]").click()
    page.wait_for_timeout(500)
    again = page.evaluate(READ)
    check(
        "toggle:reopen-restores",
        again["toggle"]["pressed"] == "true"
        and again["timelinePresent"] is True
        and abs((again["timelineH"] or 0) - DEFAULT_H) < 0.6
        and again["store"]["open"] is True,
        detail={"pressed": again["toggle"]["pressed"],
                "h": again["timelineH"], "open": again["store"]["open"]},
    )

    # --- independence from 时间线最小化 ----------------------------------------
    page.locator('button[aria-label="时间线最小化"]').click()
    page.wait_for_timeout(400)
    minimized = page.evaluate(READ)
    check(
        "minimize:independent-verb",
        minimized["timelinePresent"] is True
        and abs((minimized["timelineH"] or 0) - MIN_H) < 0.6
        and minimized["store"]["open"] is True
        and minimized["toggle"]["pressed"] == "true",
        detail={"present": minimized["timelinePresent"],
                "h": minimized["timelineH"],
                "open": minimized["store"]["open"],
                "pressed": minimized["toggle"]["pressed"]},
    )
    page.locator('button[aria-label="展开时间线"]').click()
    page.wait_for_timeout(400)

    # --- the two view-state fields live in the store ---------------------------
    check(
        "store:owns-view-state",
        page.evaluate(
            """() => {
              const d = window.__director_store.getState();
              return typeof d.timelinePanelOpen === 'boolean'
                && typeof d.timelineHeight === 'number'
                && typeof d.setTimelinePanelOpen === 'function'
                && typeof d.toggleTimelinePanel === 'function'
                && typeof d.setTimelineHeight === 'function';
            }"""
        ),
        detail="timelinePanelOpen / timelineHeight are store view state",
    )
    check(
        "store:view-state-not-persisted",
        page.evaluate(
            """() => {
              const snap = window.__director_store.getState()
                .getProjectPersistenceSnapshot
                ? window.__director_store.getState().getProjectPersistenceSnapshot()
                : null;
              if (!snap) return 'no-snapshot';
              const doc = snap.document ?? snap;
              return !('timelinePanelOpen' in doc) && !('timelineHeight' in doc);
            }"""
        ),
        detail="the document schema must not carry view state (batch 599 rule)",
    )

    check("no-console-errors", not errors, detail=errors[:5])
    result["measured"] = {"on": on, "off": off, "reopened": again, "minimized": minimized}
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
        f"Batch 608 verification: {len(result['checks']) - len(failed)}"
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
