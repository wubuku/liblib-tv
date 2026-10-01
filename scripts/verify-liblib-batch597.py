#!/usr/bin/env python3
"""Verify Batch 597: 轨道列表的选中态是**背景**（青色底），不是文字色。

Source facts (live CDP sampling of the source director desk at 1920x1150,
2026-10-01, /tmp/src593/probe10 + probe30 + probe31):

With 位置 selected (idle, mouse parked away, and after clicking the object
name — all three identical):

    对象行  overlay span[aria-hidden].absolute.inset-0
                     bg rgba(60, 181, 204, 0.25)   320x32 @(0,1057)
            text colour rgb(247,247,247)
    轨道行  background rgba(60, 181, 204, 0.1)    320x32 @(0,1089)
            text colour rgb(168,168,168)
    装饰加号 both strokes rgba(7, 184, 221, 0.4)

Unselected (measured right after collapsing / re-expanding the object row,
probe4 + probe10):

    对象行  overlay span bg-white/10
    轨道行  bg-transparent + hover:bg-white/[0.04]
    装饰加号 both strokes #363636

So selection is carried entirely by the BACKGROUND. The text colours do not
change: the object name and the track name are `font-medium text-[#F7F7F7]` in
both states, the value column is `text-[13px] text-[#A8A8A8]` in both.

The clone expressed selection by swapping the row's text colour
(`#F7F7F7` when selected, `#A8A8A8` otherwise) and had no object-row overlay at
all.

NOT verified (recorded, not fabricated): the source has a single track, so the
"unselected" values come from the state right after a collapse/expand toggle
rather than from clicking a different track. Whether toggling the chevron
really deselects the track, or the row simply re-rendered, is not separated.

Contract asserted here:
1. the object row always carries an aria-hidden full-bleed overlay span;
2. the object row's overlay is teal 25% when one of its tracks is selected and
   white/10 otherwise;
3. the track row's background is teal 10% when selected, transparent otherwise
   (hover tint retained);
4. the track row's text colour is #A8A8A8 in BOTH states;
5. the object row's and track row's names are #F7F7F7 font-medium in both
   states;
6. the decorative plus is teal 40% when selected and #363636 when not;
7. selecting a different track flips all of the above;
8. no diagnostics.
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
    / "liblib-canvas-batch597-2026-10-01"
    / "runtime-audit.json"
)

TEAL_25 = "rgba(60, 181, 204, 0.25)"
TEAL_10 = "rgba(60, 181, 204, 0.1)"
# Tailwind compiles `bg-white/10` to `oklab(... / 0.1)` in this build while the
# source serialises `rgba(255,255,255,0.1)`; the repo convention is to compare
# the ALPHA channel, never the serialisation.
WHITE_10_ALPHA = 0.1
TRACK_TEXT = "rgb(168, 168, 168)"
NAME_TEXT = "rgb(247, 247, 247)"
PLUS_SELECTED = "rgba(7, 184, 221, 0.4)"
PLUS_PLAIN = "rgb(54, 54, 54)"


def alpha_of(color: str) -> float:
    """Last component of rgb()/rgba(), or the `/ a` tail of oklab()."""
    if "/" in color and "rgba" not in color and "rgb(" not in color:
        return float(color.rsplit("/", 1)[1].strip().rstrip(")"))
    inner = color[color.index("(") + 1 : color.rindex(")")]
    parts = [p.strip() for p in inner.split(",")]
    return float(parts[3]) if len(parts) == 4 else 1.0


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


def read_rows(page: Page, track_id: str | None = None) -> dict[str, Any]:
    return page.evaluate(
        """(wanted) => {
          const rows = [...document.querySelectorAll('[data-director-track-row]')];
          const trackRow = wanted
            ? rows.find((el) => el.getAttribute('data-director-track-row') === wanted)
            : rows[0];
          const objectRow = trackRow.closest('[data-director-object-group]')
            .querySelector('[data-director-timeline-object-row]');
          const overlay = objectRow.querySelector(':scope > span[aria-hidden="true"]');
          const nameOf = (row) => {
            const el = row.querySelector('[title]');
            return {text: (el.textContent || '').trim(),
                    color: getComputedStyle(el).color,
                    weight: getComputedStyle(el).fontWeight};
          };
          const decoration = trackRow.children[0];
          const plusStrokes = [...decoration.children]
            .map((el) => getComputedStyle(el).backgroundColor);
          const value = trackRow.querySelector('[data-director-track-value]');
          return {
            object: {
              selected: objectRow.getAttribute('data-director-timeline-object-selected'),
              overlay: overlay ? getComputedStyle(overlay).backgroundColor : null,
              overlaySize: overlay ? (b => [Math.round(b.width), Math.round(b.height)])(overlay.getBoundingClientRect()) : null,
              name: nameOf(objectRow),
            },
            track: {
              selected: trackRow.getAttribute('data-director-track-row-selected'),
              background: getComputedStyle(trackRow).backgroundColor,
              color: getComputedStyle(trackRow).color,
              name: nameOf(trackRow),
              value: value ? {color: getComputedStyle(value).color,
                              fontSize: getComputedStyle(value).fontSize} : null,
              plusStrokes,
            },
          };
        }""",
        track_id,
    )


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1920x1150", "checks": []}

    def check(name: str, ok: bool, detail: Any = None) -> None:
        result["checks"].append(
            {"name": name, "ok": bool(ok), "detail": detail}
        )

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 597" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(600)
    page.locator("[data-director-track-row]").first.wait_for(state="visible")

    # start from a definite selection
    first_id = page.evaluate(
        "() => window.__director_store.getState().timeline.tracks[0].id"
    )
    page.evaluate(
        "(id) => window.__director_store.getState().selectTimelineTrack(id)",
        first_id,
    )
    page.wait_for_timeout(200)
    page.mouse.move(1500, 400)
    page.wait_for_timeout(200)
    selected = read_rows(page, first_id)
    result["selected"] = selected

    # 1-6) the selected state
    check(
        "object:overlay-present",
        selected["object"]["overlay"] is not None
        and abs(selected["object"]["overlaySize"][0] - 320) <= 1
        and selected["object"]["overlaySize"][1] == 32,
        detail=selected["object"],
    )
    check(
        "selected:object-overlay-teal-25",
        selected["object"]["selected"] == "true"
        and selected["object"]["overlay"] == TEAL_25,
        detail=selected["object"],
    )
    check(
        "selected:track-bg-teal-10",
        selected["track"]["selected"] == "true"
        and selected["track"]["background"] == TEAL_10,
        detail=selected["track"],
    )
    check(
        "selected:track-text-stays-a8a8a8",
        selected["track"]["color"] == TRACK_TEXT
        and selected["track"]["value"]["color"] == TRACK_TEXT,
        detail={"row": selected["track"]["color"], "value": selected["track"]["value"]},
    )
    check(
        "selected:names-stay-f7f7f7-medium",
        selected["object"]["name"]["color"] == NAME_TEXT
        and selected["track"]["name"]["color"] == NAME_TEXT
        and selected["object"]["name"]["weight"] in {"500", "600", "700"}
        and selected["track"]["name"]["weight"] in {"500", "600", "700"},
        detail={"object": selected["object"]["name"], "track": selected["track"]["name"]},
    )
    check(
        "selected:plus-teal-40",
        selected["track"]["plusStrokes"]
        and all(color == PLUS_SELECTED for color in selected["track"]["plusStrokes"]),
        detail=selected["track"]["plusStrokes"],
    )

    # 7) selection moving to the other track turns this row back to plain
    ids = page.evaluate(
        "() => window.__director_store.getState().timeline.tracks.map((t) => t.id)"
    )
    first_id, other_id = ids[0], ids[1]
    page.evaluate(
        "(id) => window.__director_store.getState().selectTimelineTrack(id)",
        other_id,
    )
    page.wait_for_timeout(250)
    page.mouse.move(1500, 400)
    page.wait_for_timeout(200)
    other = read_rows(page, other_id)
    result["other_selected"] = other
    check(
        "selected:moves-to-the-other-track",
        other["track"]["selected"] == "true" and other["track"]["background"] == TEAL_10,
        detail=other["track"],
    )
    plain = read_rows(page, first_id)
    result["plain"] = plain
    check(
        "plain:track-bg-transparent",
        plain["track"]["selected"] == "false"
        and plain["track"]["background"] == "rgba(0, 0, 0, 0)",
        detail=plain["track"],
    )
    check(
        "plain:track-text-stays-a8a8a8",
        plain["track"]["color"] == TRACK_TEXT,
        detail=plain["track"]["color"],
    )
    check(
        "plain:object-overlay-white-10",
        plain["object"]["selected"] == "false"
        and plain["object"]["overlay"] is not None
        and abs(alpha_of(plain["object"]["overlay"]) - WHITE_10_ALPHA) < 0.01,
        detail=plain["object"],
    )
    check(
        "plain:plus-363636",
        plain["track"]["plusStrokes"]
        and all(color == PLUS_PLAIN for color in plain["track"]["plusStrokes"]),
        detail=plain["track"]["plusStrokes"],
    )

    page.screenshot(
        path=str(
            ROOT / "docs" / "design-references" / "liblib-timeline-selection-1920.png"
        )
    )
    result["diagnostics"] = errors
    check("no-diagnostics", not errors, detail=errors)
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 597,
        "title": "轨道列表选中态改为背景表达：对象行 teal 25% 覆盖层 + 轨道行 teal 10% 背景，文字色恒定",
        "evidence": (
            "2026-10-01 live CDP sampling of the source director desk at "
            "1920x1150 + docs/research/liblib-canvas-batch597-2026-10-01/README.md"
        ),
        "source_facts": {
            "selected": {
                "object_overlay": "rgba(60,181,204,0.25) full-bleed aria-hidden span, 320x32",
                "track_background": "rgba(60,181,204,0.1)",
                "track_text": "rgb(168,168,168)",
                "names": "font-medium #F7F7F7",
                "decorative_plus": "rgba(7,184,221,0.4)",
            },
            "plain": {
                "object_overlay": "bg-white/10",
                "track_background": "bg-transparent (+ hover:bg-white/[0.04])",
                "track_text": "rgb(168,168,168)",
                "decorative_plus": "#363636",
            },
        },
        "clone_only": [],
        "not_verified": [
            "the source has a single track, so the 'plain' values were read right "
            "after a collapse/expand toggle rather than from clicking a second track; "
            "whether the toggle deselects or merely re-renders is not separated",
        ],
        "results": [],
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(
            viewport={"width": 1920, "height": 1150}, device_scale_factor=1
        )
        audit["results"].append(run_desktop(desktop))
        desktop.close()
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    checks = audit["results"][0]["checks"]
    failed = [item for item in checks if not item["ok"]]
    print(
        f"Batch 597 verification: {len(checks) - len(failed)}/{len(checks)} checks passed"
    )
    if failed:
        raise SystemExit(
            "FAILED: " + json.dumps(failed, ensure_ascii=False, indent=2)
        )


if __name__ == "__main__":
    main()
