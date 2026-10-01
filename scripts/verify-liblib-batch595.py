#!/usr/bin/env python3
"""Verify Batch 595: 时间轴标尺刻度（0.1s 次 / 1s 主 + 居中 {n}s 标签 + 取色）。

Source facts (measured by reading the source ruler canvas' pixels, 2026-10-01,
2x DPR, evidence under /tmp/src593/probe22-26):

The source ruler is a single `<canvas>`; its tick structure was recovered by
scanning bright columns per row band, not by reading text.

Subdivision is FIXED at 0.1s and does NOT adapt to zoom — at zoom 42 and at
zoom 100 there are exactly 100 ticks for a 10s timeline; only the spacing
scales (major tick spacing measured 211px @ zoom 42, 500px @ zoom 100).
Every 10th tick is a major (1s) tick carrying a `{n}s` label.

Geometry (CSS px, y measured from the canvas top):

    labels   y 5.0 - 13.5   colour #9d9d9d   (8.5px band -> ~12px font)
    major    y 22.5 - 31.0  colour #878787   8.5px tall
    minor    y 27.5 - 31.0  colour #686868   3.5px tall
    ruler background #212121
    lane background  #2a2a2a, NO vertical grid lines, NO row separators

Label positions are centred on their major tick (measured: `1s` glyphs span
212.0-222.5 with the tick at 217.0).

The clone had one full-height `border-l` per **second**, labels left-aligned
4px from the tick at 9px `#5e5e5e`, a `#191919` ruler, and a per-second
`border-l` grid inside every keyframe lane.

Contract asserted here:
1. the ruler is 0.1s-graded and the tick count is duration/0.1 + 1;
2. every 10th tick is major, the rest minor;
3. major ticks are 8.5px #878787, minor 3.5px #686868, both bottom-aligned;
4. major labels read `{n}s`, are #9d9d9d, 12px, and are centred on their tick
   (their box straddles the tick, not offset by a fixed left padding);
5. the ruler background is #212121;
6. keyframe lanes are #2a2a2a with no vertical grid lines;
7. tick spacing scales with zoom while the count stays fixed;
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
    / "liblib-canvas-batch595-2026-10-01"
    / "runtime-audit.json"
)

TICK_SECONDS = 0.1
MAJOR_EVERY = 10
MAJOR_PX = 8.5
MINOR_PX = 3.5
MAJOR_COLOR = "rgb(135, 135, 135)"
MINOR_COLOR = "rgb(104, 104, 104)"
LABEL_COLOR = "rgb(157, 157, 157)"
RULER_BG = "rgb(33, 33, 33)"
# Batch 595 originally read the lane fill as #2a2a2a. Batch 598 re-measured the
# source lane canvas pixel by pixel (/tmp/src593/probe35–probe42) and that value
# was the **gap** between lanes, not a lane fill: the canvas base is #212121,
# an unselected track lane is transparent over it, a selected one is
# #212121 + rgba(60,181,204,0.1) = #243032, and the object lane above it is
# #212121 + rgba(60,181,204,0.25) = #28464c with a 1px #355359 top edge.
# The point of the check is unchanged: lanes are flat, with no vertical grid.
LANE_BG = "rgb(33, 33, 33)"


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


def read_ruler(page: Page) -> dict[str, Any]:
    return page.evaluate(
        """() => {
          const ruler = document.querySelector('[data-director-timeline-ruler]');
          const r = ruler.getBoundingClientRect();
          const cs = getComputedStyle(ruler);
          const spans = [...ruler.querySelectorAll('[data-director-ruler-tick]')];
          const majors = spans.filter((s) => s.dataset.directorRulerTick === 'major');
          const minors = spans.filter((s) => s.dataset.directorRulerTick === 'minor');
          const box = (el) => { const b = el.getBoundingClientRect();
            return {x: +b.x.toFixed(2), w: +b.width.toFixed(2), h: +b.height.toFixed(2),
                    bottom: +(b.bottom).toFixed(2)}; };
          const labels = [...ruler.children].map((c) => c.children[1]).filter(Boolean);
          return {
            background: cs.backgroundColor,
            height: Math.round(r.height),
            tickCount: spans.length,
            majorCount: majors.length,
            minorCount: minors.length,
            major: {box: box(majors[0]), color: getComputedStyle(majors[0]).backgroundColor},
            minor: {box: box(minors[0]), color: getComputedStyle(minors[0]).backgroundColor},
            majorBottoms: [...new Set(majors.map((m) => +m.getBoundingClientRect().bottom.toFixed(2)))],
            minorBottoms: [...new Set(minors.map((m) => +m.getBoundingClientRect().bottom.toFixed(2)))],
            majorGap: majors.length > 1
              ? +(majors[1].getBoundingClientRect().x - majors[0].getBoundingClientRect().x).toFixed(2)
              : null,
            firstLabels: labels.slice(0, 3).map((el) => {
              const b = el.getBoundingClientRect();
              const c = getComputedStyle(el);
              return {text: el.textContent, color: c.color, fontSize: c.fontSize,
                      center: +(b.x + b.width / 2).toFixed(2), x: +b.x.toFixed(2),
                      w: +b.width.toFixed(2), top: +(b.top - r.top).toFixed(2),
                      transform: c.transform};
            }),
            firstTickX: +spans[0].getBoundingClientRect().x.toFixed(2),
          };
        }"""
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
          store.addNode("script-execution", { title: "Batch 595" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(600)
    page.locator("[data-director-timeline-ruler]").wait_for(state="visible")

    duration = page.evaluate(
        "() => window.__director_store.getState().timeline.duration"
    )
    ruler = read_ruler(page)
    result["duration"] = duration
    result["ruler"] = ruler

    # 1-2) tick count and the 1-in-10 major ratio
    expected_ticks = round(duration / TICK_SECONDS) + 1
    check(
        "ruler:0.1s-tick-count",
        ruler["tickCount"] == expected_ticks
        and ruler["tickCount"] == ruler["majorCount"] + ruler["minorCount"],
        detail={
            "duration": duration,
            "expected": expected_ticks,
            "actual": ruler["tickCount"],
        },
    )
    check(
        "ruler:major-every-10",
        ruler["majorCount"] == round(ruler["tickCount"] / MAJOR_EVERY) + 1
        or ruler["majorCount"] == (ruler["tickCount"] - 1) // MAJOR_EVERY + 1,
        detail={"major": ruler["majorCount"], "minor": ruler["minorCount"]},
    )

    # 3) tick sizes and colours, both bottom-aligned
    check(
        "ruler:major-tick",
        abs(ruler["major"]["box"]["h"] - MAJOR_PX) < 0.6
        and ruler["major"]["color"] == MAJOR_COLOR
        and len(ruler["majorBottoms"]) == 1
        and len(ruler["minorBottoms"]) == 1
        and abs(ruler["majorBottoms"][0] - ruler["minorBottoms"][0]) < 0.6,
        detail={"major": ruler["major"], "bottoms": [ruler["majorBottoms"], ruler["minorBottoms"]]},
    )
    check(
        "ruler:minor-tick",
        abs(ruler["minor"]["box"]["h"] - MINOR_PX) < 0.6
        and ruler["minor"]["color"] == MINOR_COLOR,
        detail=ruler["minor"],
    )

    # 4) labels: `{n}s`, #9d9d9d, 12px, centred on the tick
    labels = ruler["firstLabels"]
    check(
        "ruler:label-text-and-style",
        bool(labels)
        and labels[0]["text"] == "0s"
        and labels[1]["text"] == "1s"
        and all(item["color"] == LABEL_COLOR and item["fontSize"] == "12px" for item in labels),
        detail=labels,
    )
    ticks_x = page.evaluate(
        """() => [...document.querySelectorAll('[data-director-ruler-tick="major"]')]
             .slice(0, 3).map((el) => +el.getBoundingClientRect().x.toFixed(2))"""
    )
    check(
        "ruler:label-centred-on-tick",
        all(
            abs(item["center"] - tick) < 1.0
            for item, tick in zip(labels, ticks_x)
        ),
        detail={"labels": [(i["text"], i["center"]) for i in labels], "ticks": ticks_x},
    )

    # 5) ruler background
    check("ruler:background-212121", ruler["background"] == RULER_BG, detail=ruler["background"])

    # 6) keyframe lanes: flat over the #212121 canvas base, no vertical grid
    #    lines. Batch 598: an unselected track lane paints nothing of its own,
    #    so the check moves to the canvas base it composites onto.
    lanes = page.evaluate(
        """() => {
          const all = [...document.querySelectorAll('[data-director-track-id]')];
          const plain = all.filter(
            (el) => el.getAttribute('data-director-track-selected') !== 'true');
          const verticals = (el) =>
            [...el.querySelectorAll('span')].filter((s) => {
              const b = s.getBoundingClientRect();
              return b.width <= 1.6 && b.height > 8;
            }).length;
          const canvas = document.querySelector('[data-director-timeline-canvas]');
          return {
            count: all.length,
            plainCount: plain.length,
            backgrounds: [...new Set(plain.map((el) => getComputedStyle(el).backgroundColor))],
            canvasBackground: getComputedStyle(canvas).backgroundColor,
            verticals: all.reduce((sum, el) => sum + verticals(el), 0),
          };
        }"""
    )
    result["lane"] = lanes
    check(
        "lane:212121-base-no-grid",
        lanes["plainCount"] >= 1
        and lanes["backgrounds"] == ["rgba(0, 0, 0, 0)"]
        and lanes["canvasBackground"] == LANE_BG
        and lanes["verticals"] == 0,
        detail=lanes,
    )

    # 7) the count is zoom-invariant while the spacing scales
    gaps = {}
    counts = {}
    for zoom in (25, 100):
        page.evaluate(
            "(z) => window.__director_store.getState().setTimelineZoom(z)", zoom
        )
        page.wait_for_timeout(200)
        snap = read_ruler(page)
        gaps[zoom] = snap["majorGap"]
        counts[zoom] = snap["tickCount"]
    result["zoom"] = {"gaps": gaps, "counts": counts}
    check(
        "ruler:count-fixed-spacing-scales",
        counts[25] == counts[100] == expected_ticks
        and gaps[25] is not None
        and gaps[100] is not None
        and gaps[100] > gaps[25] * 2,
        detail=result["zoom"],
    )

    page.evaluate(
        "() => window.__director_store.getState().setTimelineZoom(44)"
    )
    page.wait_for_timeout(200)
    page.screenshot(
        path=str(
            ROOT / "docs" / "design-references" / "liblib-timeline-ruler-ticks-1920.png"
        )
    )

    result["diagnostics"] = errors
    check("no-diagnostics", not errors, detail=errors)
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 595,
        "title": "时间轴标尺刻度：0.1s 次 / 1s 主 + 居中 {n}s 标签 + 取色，轨道道去网格",
        "evidence": (
            "2026-10-01 pixel scan of the source ruler canvas (2x DPR) at "
            "1920x1150 + docs/research/liblib-canvas-batch595-2026-10-01/README.md"
        ),
        "source_facts": {
            "subdivision": "0.1s, fixed — 100 ticks for a 10s timeline at both zoom 42 and zoom 100",
            "major_every": 10,
            "labels": "{n}s, #9d9d9d, ~12px, band y 5.0-13.5, centred on the major tick",
            "major_tick": "y 22.5-31.0, 8.5px, #878787",
            "minor_tick": "y 27.5-31.0, 3.5px, #686868",
            "ruler_background": "#212121",
            "lane_background": "#2a2a2a, no vertical grid lines, no row separators",
            "major_spacing": {"zoom_42": 211, "zoom_100": 500},
        },
        "clone_only": [
            "the ruler keeps h-7 (28px); the source's tick band bottoms out at canvas "
            "y=31, a 3px difference that would shift the whole lane stack for no "
            "strong evidence",
            "the selected-track tint on a lane stays (the source has no equivalent "
            "left-column/lane selection highlight on the lane itself)",
        ],
        "not_verified": [
            "the source's exact font family/size for the labels — the glyph band is "
            "8.5px tall, which implies ~12px for a typical UI face, but the canvas "
            "draws text directly and exposes no font info",
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
        f"Batch 595 verification: {len(checks) - len(failed)}/{len(checks)} checks passed"
    )
    if failed:
        raise SystemExit(
            "FAILED: " + json.dumps(failed, ensure_ascii=False, indent=2)
        )


if __name__ == "__main__":
    main()
