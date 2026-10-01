#!/usr/bin/env python3
"""Verify Batch 598: 车道区（标尺右侧）改成跟随左列的两级行，并按源站
逐像素实测重画车道底色 / 播放头 / 关键帧菱形。

Source facts (live CDP sampling of the source director desk at 1920x1150,
2026-10-01, /tmp/src593/probe34–probe42).

The right-hand lane area is NOT DOM. It is a second canvas, 2124x115 CSS
(4248x230 at DPR 2) at page (322, 1021), inside
`relative shrink-0 overflow-hidden rounded-r-md bg-black/15`. It paints the
ruler, the lane bands, the playhead and the keyframe diamonds all at once. A
full div/span/button/svg/path/line/rect/polygon sweep of the band found no
overlay element at all (probe32), so everything below is read from the canvas
bitmap via getImageData.

  lane pitch     32px = a 31px band + a 1px #212121 bottom edge
                 band [37,67) then gap [67,68) then band [68,99)
  object lane    #28464c = #212121 + rgba(60,181,204,0.25)
                 a 1px #355359 line on its top edge
                 4px corner radius (the top edge ramps #323232 -> #355359
                 over the first 3.5px at both ends)
  track lane     #243032 = #212121 + rgba(60,181,204,0.1)
  canvas base    #212121 everywhere else
  playhead       2 CSS px wide, #05a3c5, and it covers ONLY the object lane:
                 at the 0s major tick the column is #212121 through the whole
                 ruler, #05a3c5 across [37,67), then #212121 across the gap and
                 plain #243032 through lane 2. No triangle head, no glow.
  keyframe       hollow diamond, 11x11 outer, 1px #13879f stroke, #2f2f2f
                 fill, vertically centred on its lane (centre css y 84 in a
                 lane spanning 68..99)
  ruler window   36px, ticks bottom-aligned 5px above its floor

Lane/row correspondence: lane 1 covers page y 1057..1088 and the left column
object row sits at (0,1057) 320x32; lane 2 covers 1089..1120 and the track row
sits at (0,1089) 320x32. Collapsing the object row (a pure aria-expanded toggle,
restored afterwards) leaves exactly one band [37,67) — the lane area follows
the left column's collapse state.

The clone mapped `timeline.tracks` straight into lanes, so it rendered one lane
per track (2) against 4 left-column rows, ignored the collapse toggle, and sat
8px out of alignment (its ruler was 28px where the source window is 36px).

NOT verified (recorded, not fabricated):
- unselected lane fills. The source project has a single track which is always
  selected, so no unselected lane was ever on screen. The clone mirrors the
  left column's already-measured alpha ladder (batch 597): object lane
  white/10, track lane transparent.
- which object lane carries the playhead when there is more than one object.
  The source has one object. The clone draws it on the object that owns the
  selected track (clone-only decision).
- the selected keyframe diamond. The source diamond is inside a canvas and a
  second click may delete the keyframe, so only the unselected state was read.
  The clone fills the selected one with the measured playhead #05a3c5.
- lane corner radius is read from the 3.5px top-edge ramp, not from a DOM box.

Contract asserted here:
1. the lane area renders one object lane per group plus that group's track
   lanes, in the same order as the left column;
2. lane rows line up 1:1 with left-column rows (same y, same 32px height);
3. collapsing an object removes exactly its track lanes, not the object lane;
4. object lane: selected rgba(60,181,204,0.25) / unselected white 10%, 1px
   #355359 top edge, 1px #212121 bottom edge, 4px radius;
5. track lane: selected rgba(60,181,204,0.1) / unselected transparent, 1px
   #212121 bottom edge;
6. the canvas base is #212121, so those alphas land on #28464c / #243032;
7. the playhead is 2px of #05a3c5 with no glow and no children, and it lives
   inside the object lane — never in a track lane or the ruler;
8. the playhead follows the selected track's object;
9. keyframe diamonds are 11x11 outer with a 1px #13879f stroke and a #2f2f2f
   fill;
10. the ruler window is 36px with ticks bottom-aligned 5px above its floor;
11. the object lane count does not change the data-director-track-id count;
12. no diagnostics.
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
    / "liblib-canvas-batch598-2026-10-01"
    / "runtime-audit.json"
)

TEAL_25 = "rgba(60, 181, 204, 0.25)"
TEAL_10 = "rgba(60, 181, 204, 0.1)"
TRANSPARENT = "rgba(0, 0, 0, 0)"
BASE_212121 = "rgb(33, 33, 33)"
EDGE_355359 = "rgb(53, 83, 89)"
PLAYHEAD_05A3C5 = "rgb(5, 163, 197)"
KEYFRAME_13879F = "rgb(19, 135, 159)"
KEYFRAME_2F2F2F = "rgb(47, 47, 47)"
# Tailwind compiles `bg-white/10` to `oklab(... / 0.1)`; the repo convention is
# to compare the ALPHA channel, never the serialisation.
WHITE_10_ALPHA = 0.1
RULER_HEIGHT = 36
TICK_BOTTOM_GAP = 5.0
MAJOR_TOP = 22.5
MINOR_TOP = 27.5
LANE_HEIGHT = 32
DIAMOND_BOX = 11.0


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


READ = """() => {
  const cs = (el) => getComputedStyle(el);
  const at = (el) => { const r = el.getBoundingClientRect();
    return {x: Math.round(r.x), y: Math.round(r.y),
            w: Math.round(r.width), h: Math.round(r.height)}; };
  const leftRows = [
    ...document.querySelectorAll('[data-director-timeline-object-row]'),
    ...document.querySelectorAll('[data-director-track-row]'),
  ].map((el) => ({kind: el.hasAttribute('data-director-timeline-object-row')
                        ? 'object' : 'track',
                  y: Math.round(el.getBoundingClientRect().y),
                  h: Math.round(el.getBoundingClientRect().height),
                  selected: el.getAttribute('data-director-timeline-object-selected')
                          ?? el.getAttribute('data-director-track-row-selected')}))
    .sort((a, b) => a.y - b.y);
  const objectLanes = [...document.querySelectorAll('[data-director-timeline-object-lane]')]
    .map((el) => ({y: Math.round(el.getBoundingClientRect().y),
                   h: Math.round(el.getBoundingClientRect().height),
                   selected: el.getAttribute('data-director-timeline-object-lane-selected'),
                   background: cs(el).backgroundColor,
                   borderTop: cs(el).borderTopColor,
                   borderTopWidth: cs(el).borderTopWidth,
                   borderBottom: cs(el).borderBottomColor,
                   borderBottomWidth: cs(el).borderBottomWidth,
                   radius: cs(el).borderTopLeftRadius,
                   playheads: el.querySelectorAll('[data-director-playhead]').length}));
  const trackLanes = [...document.querySelectorAll('[data-director-track-id]')]
    .map((el) => ({id: el.getAttribute('data-director-track-id'),
                   y: Math.round(el.getBoundingClientRect().y),
                   h: Math.round(el.getBoundingClientRect().height),
                   selected: el.getAttribute('data-director-track-selected'),
                   background: cs(el).backgroundColor,
                   borderBottom: cs(el).borderBottomColor,
                   playheads: el.querySelectorAll('[data-director-playhead]').length}));
  const canvas = document.querySelector('[data-director-timeline-canvas]');
  const ruler = document.querySelector('[data-director-timeline-ruler]');
  const rr = ruler.getBoundingClientRect();
  const tick = (kind) => {
    const el = document.querySelector('[data-director-ruler-tick="' + kind + '"]');
    const b = el.getBoundingClientRect();
    return {top: +(b.top - rr.top).toFixed(2), bottom: +(rr.bottom - b.bottom).toFixed(2),
            w: +b.width.toFixed(2), background: cs(el).backgroundColor};
  };
  const ph = document.querySelector('[data-director-playhead]');
  const diamonds = [...document.querySelectorAll('[data-director-keyframe-id]')].map((el) => {
    const b = el.getBoundingClientRect();
    return {id: el.getAttribute('data-director-keyframe-id'),
            box: +b.width.toFixed(2),
            borderWidth: cs(el).borderTopWidth,
            borderColor: cs(el).borderTopColor,
            background: cs(el).backgroundColor};
  });
  return {
    canvasBackground: cs(canvas).backgroundColor,
    ruler: {y: Math.round(rr.y), h: Math.round(rr.height), background: cs(ruler).backgroundColor},
    major: tick('major'), minor: tick('minor'),
    leftRows, objectLanes, trackLanes, diamonds,
    playhead: ph ? {box: at(ph), width: cs(ph).width, background: cs(ph).backgroundColor,
                    shadow: cs(ph).boxShadow, children: ph.children.length,
                    owner: ph.closest('[data-director-timeline-object-lane]') !== null,
                    inRuler: ph.closest('[data-director-timeline-ruler]') !== null} : null,
  };
}"""


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1920x1150", "checks": []}

    def check(name: str, ok: bool, detail: Any = None) -> None:
        result["checks"].append({"name": name, "ok": bool(ok), "detail": detail})

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 598" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(600)
    page.locator("[data-director-track-row]").first.wait_for(state="visible")

    tracks = page.evaluate(
        "() => window.__director_store.getState().timeline.tracks.map((t) => t.id)"
    )
    page.evaluate("(id) => window.__director_store.getState().selectTimelineTrack(id)", tracks[0])
    page.wait_for_timeout(250)
    page.mouse.move(1500, 400)
    page.wait_for_timeout(250)
    snap = page.evaluate(READ)
    result["expanded"] = snap

    # 1) one object lane per group, plus that group's track lanes
    check(
        "lanes:object-lane-per-group",
        len(snap["objectLanes"]) == 2 and len(snap["trackLanes"]) == len(tracks),
        detail={"object": len(snap["objectLanes"]), "track": len(snap["trackLanes"])},
    )

    # 2) lane rows line up 1:1 with the left column
    lane_rows = sorted(
        [(lane["y"], lane["h"], "object") for lane in snap["objectLanes"]]
        + [(lane["y"], lane["h"], "track") for lane in snap["trackLanes"]]
    )
    left = [(row["y"], row["h"], row["kind"]) for row in snap["leftRows"]]
    check(
        "lanes:align-with-left-column",
        lane_rows == left
        and all(h == LANE_HEIGHT for _, h, _ in lane_rows),
        detail={"lanes": lane_rows, "left": left},
    )

    # 3) collapse drops exactly that group's track lanes
    page.locator("[data-director-timeline-object-row]").first.locator(
        "button[aria-expanded]"
    ).click()
    page.wait_for_timeout(350)
    collapsed = page.evaluate(READ)
    result["collapsed"] = collapsed
    check(
        "lanes:collapse-drops-track-lanes",
        len(collapsed["objectLanes"]) == 2
        and len(collapsed["trackLanes"]) == len(tracks) - 1
        and collapsed["objectLanes"][0]["y"] == snap["objectLanes"][0]["y"],
        detail={
            "object": len(collapsed["objectLanes"]),
            "track": len(collapsed["trackLanes"]),
        },
    )
    collapsed_rows = sorted(
        [(lane["y"], lane["h"], "object") for lane in collapsed["objectLanes"]]
        + [(lane["y"], lane["h"], "track") for lane in collapsed["trackLanes"]]
    )
    collapsed_left = [
        (row["y"], row["h"], row["kind"]) for row in collapsed["leftRows"]
    ]
    check(
        "lanes:still-aligned-when-collapsed",
        collapsed_rows == collapsed_left,
        detail={"lanes": collapsed_rows, "left": collapsed_left},
    )
    page.locator("[data-director-timeline-object-row]").first.locator(
        "button[aria-expanded]"
    ).click()
    page.wait_for_timeout(300)

    # 4) object lane colours + edges
    object_selected = [lane for lane in snap["objectLanes"] if lane["selected"] == "true"]
    object_plain = [lane for lane in snap["objectLanes"] if lane["selected"] != "true"]
    check(
        "object-lane:selected-teal-25",
        len(object_selected) == 1
        and object_selected[0]["background"] == TEAL_25
        and object_selected[0]["borderTop"] == EDGE_355359
        and object_selected[0]["borderTopWidth"] == "1px",
        detail=object_selected,
    )
    check(
        "object-lane:unselected-white-10",
        len(object_plain) == 1
        and abs(alpha_of(object_plain[0]["background"]) - WHITE_10_ALPHA) < 0.001
        and object_plain[0]["borderTop"] == EDGE_355359
        and object_plain[0]["radius"] == "4px",
        detail=object_plain,
    )
    check(
        "object-lane:bottom-edge-212121",
        all(
            lane["borderBottom"] == BASE_212121
            and lane["borderBottomWidth"] == "1px"
            and lane["h"] == LANE_HEIGHT
            for lane in snap["objectLanes"]
        ),
        detail=[lane["borderBottom"] for lane in snap["objectLanes"]],
    )

    # 5) track lane colours
    track_selected = [lane for lane in snap["trackLanes"] if lane["selected"] == "true"]
    track_plain = [lane for lane in snap["trackLanes"] if lane["selected"] != "true"]
    check(
        "track-lane:selected-teal-10",
        len(track_selected) == 1 and track_selected[0]["background"] == TEAL_10,
        detail=track_selected,
    )
    check(
        "track-lane:unselected-transparent",
        len(track_plain) == 1
        and track_plain[0]["background"] == TRANSPARENT
        and all(
            lane["borderBottom"] == BASE_212121 for lane in snap["trackLanes"]
        ),
        detail=track_plain,
    )

    # 6) the canvas base the alphas land on
    check(
        "canvas:base-212121",
        snap["canvasBackground"] == BASE_212121,
        detail=snap["canvasBackground"],
    )

    # 7) playhead geometry, owner and absence of decoration
    ph = snap["playhead"]
    check(
        "playhead:2px-05a3c5-in-object-lane",
        ph is not None
        and ph["width"] == "2px"
        and ph["background"] == PLAYHEAD_05A3C5
        and ph["shadow"] == "none"
        and ph["children"] == 0
        and ph["owner"]
        and not ph["inRuler"],
        detail=ph,
    )
    check(
        "playhead:never-in-a-track-lane",
        all(lane["playheads"] == 0 for lane in snap["trackLanes"])
        and sum(lane["playheads"] for lane in snap["objectLanes"]) == 1,
        detail={
            "object": [lane["playheads"] for lane in snap["objectLanes"]],
            "track": [lane["playheads"] for lane in snap["trackLanes"]],
        },
    )
    check(
        "playhead:covers-the-object-lane-band",
        ph is not None
        and ph["box"]["h"] == LANE_HEIGHT - 2
        and ph["box"]["y"] == snap["objectLanes"][0]["y"] + 1,
        detail={"playhead": ph["box"] if ph else None,
                "lane": snap["objectLanes"][0]["y"]},
    )

    # 8) the playhead follows the selected track's object
    page.evaluate("(id) => window.__director_store.getState().selectTimelineTrack(id)", tracks[1])
    page.wait_for_timeout(250)
    moved = page.evaluate(READ)
    result["otherSelected"] = moved
    moved_playheads = [
        index
        for index, lane in enumerate(moved["objectLanes"])
        if lane["playheads"] == 1
    ]
    check(
        "playhead:follows-selected-object",
        moved_playheads == [1],
        detail={"objectLaneWithPlayhead": moved_playheads},
    )
    page.evaluate("(id) => window.__director_store.getState().selectTimelineTrack(id)", tracks[0])
    page.wait_for_timeout(250)

    # 9) keyframe diamonds
    plain_diamonds = [
        diamond
        for diamond in snap["diamonds"]
        if diamond["borderColor"] == KEYFRAME_13879F
    ]
    check(
        "keyframe:11px-hollow-13879f-2f2f2f",
        len(plain_diamonds) >= 1
        and all(
            abs(diamond["box"] - DIAMOND_BOX) <= 0.2
            and diamond["borderWidth"] == "1px"
            and diamond["background"] == KEYFRAME_2F2F2F
            for diamond in plain_diamonds
        )
        and len(snap["diamonds"]) == 6,
        detail=snap["diamonds"][:2],
    )

    # 10) ruler window and tick alignment
    check(
        "ruler:36px-window",
        snap["ruler"]["h"] == RULER_HEIGHT
        and snap["ruler"]["background"] == BASE_212121,
        detail=snap["ruler"],
    )
    check(
        "ruler:ticks-bottom-aligned-5px",
        abs(snap["major"]["top"] - MAJOR_TOP) < 0.6
        and abs(snap["minor"]["top"] - MINOR_TOP) < 0.6
        and abs(snap["major"]["bottom"] - TICK_BOTTOM_GAP) < 0.6
        and abs(snap["minor"]["bottom"] - TICK_BOTTOM_GAP) < 0.6
        and snap["major"]["w"] <= 1.2,
        detail={"major": snap["major"], "minor": snap["minor"]},
    )

    # 11) the object lanes do not inflate the data-director-track-id count
    check(
        "lanes:object-lanes-not-track-ids",
        page.locator("[data-director-track-id]").count() == len(tracks),
        detail={"tracks": tracks},
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
    print(f"Batch 598 verification: {len(result['checks']) - len(failed)}"
          f"/{len(result['checks'])} checks passed")
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
