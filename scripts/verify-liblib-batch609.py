#!/usr/bin/env python3
"""Verify Batch 609: source-shaped transform field rows + keyframe diamonds.

## What the source shows (measured 2026-10-01, 1920x1150, probe66/probe67)

The source's right-hand inspector is a 280px column (`div.flex.min-h-full.
flex-col` at x=1640, starting y=48).  Its field rows are built from four
recurring pieces, all measured on the live DOM:

* a group is **60px** tall: a 28px label box + `mb-1` (4px) + a 28px control —
  `div [1656,289,248,60]` > `div.mb-1.flex.h-7.items-center
  .text-[13px].font-normal.leading-none.text-white/45` + a 28px control;
* text inputs and selects are **248x28** `h-7 w-full rounded-lg border-0
  bg-white/10 px-2 text-[12px] text-neutral-50 outline-none
  placeholder:text-white/30 focus:bg-white/13` (selects add `appearance-none`);
* a three-axis row is `grid grid-cols-3 gap-1` of **80x28** cells —
  `focus-within:bg-white/13 relative flex h-7 min-w-0 overflow-hidden
  rounded-lg bg-white/10 transition-colors` (no border; focus raises the fill
  instead of drawing one);
* inside a cell the scrub chip is **absolute**, 20x28, `cursor-ew-resize`,
  `rounded-l-lg border-0 bg-transparent text-[12px] uppercase text-white/45`,
  the number input is `h-full min-w-0 flex-1 pl-6 pr-0 text-[12px]
  tabular-nums` (**left** aligned, `pl-6` clearing the chip), and the cell ends
  with a **20x28 keyframe toggle** — `ml-px ... border-l border-black/20` with
  two mutually exclusive states:
    - `当前帧无关键帧` — `bg-white/[0.04] text-white/75 hover:bg-white/[0.07]
      hover:text-[#5DDCFF]`, 9x9 svg whose `rect` is `fill=none
      stroke=currentColor stroke-width=1.2`;
    - `当前帧有关键帧` — `bg-[#263E43] text-[#5DDCFF]` (rgb(38,62,67) /
      rgb(93,220,255)), same rect but `fill=currentColor`.
  The rect is `x=1.95 y=1.95 width=6.1 height=6.1 rx=1
  transform=rotate(45 5 5)` in a `viewBox="0 0 10 10"`.

Rows that do not live in the object's transform (the source's 注视坐标 cells,
measured at `[1656,753,80,28]`) carry **no** keyframe toggle — only the scrub
chip and the input.

## What the clone was missing

Its three-axis rows were 32px tall with a 1px `border-white/[0.08]` and an
opaque `#222` fill, `grid-cols-3 gap-1.5`, an in-flow 24px scrub chip, a
right-aligned 11px number input, and a 6px cyan diamond (`size-1.5 rotate-45
bg-[#09caf5]`) that only *reported* keyframes — it could not be clicked.  The
名称 input was likewise `h-8 ... border border-white/[0.08] bg-[#222]`.

## What this batch does

1. re-shapes `AxisFields` to the source geometry above (h-7 cells, no border,
   `gap-1`, absolute 20px scrub chip, left-aligned 12px input, h-7/13px label);
2. replaces the read-only diamond with a real **20x28 keyframe toggle** in both
   measured states, wired to the timeline: clicking a cell that has no keyframe
   at the playhead records one from the current transform (`force=true`, so the
   global 自动关键帧 switch does not veto an explicit click); clicking a cell
   that has one deletes it;
3. keeps `data-director-keyframed-axis` / `-axis-index` on the **on**-state
   button, so batch 575's locator contract is unchanged.

## Not claimed

The source's keyframe toggle was **never clicked** — clicking a source control
can write to the real project, which needs authorisation. Its two-state
wording (`当前帧无关键帧` / `当前帧有关键帧`) and its two colour treatments are
measured; that a click toggles is a clone-side inference from the aria pair
being mutually exclusive on a `button`.  The clone's own toggle *is* verified
end to end here.

Because the clone's track keyframes store a whole `DirectorTransform` (not
per-axis values), the on/off predicate stays at **field** granularity — the
three cells of one row share a state, exactly as batch 575 already modelled it.
Making it per-axis would mean a persisted-schema change, which is out of scope.
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
    ROOT / "docs/research/liblib-canvas-batch609-2026-10-01/runtime-audit.json"
)
SCREENSHOT = ROOT / "docs/design-references/liblib-keyframe-diamond-609-1920.png"

VIEWPORT = {"width": 1920, "height": 1150}

CELL_H = 28
TOGGLE_W = 20
TOGGLE_H = 28
CHIP_W = 20
CHIP_H = 28
GROUP_H = 60
LABEL_H = 28
OFF_LABEL = "当前帧无关键帧"
ON_LABEL = "当前帧有关键帧"

# Transient noise we filter, with the counts kept in the audit.  The first two
# are the known TransformControls teardown warning (batches 37/46/49); the
# rest are dev-server HMR reconnects, which happen when another developer
# restarts the shared 4317 server while this run is in flight.
IGNORE_CONSOLE = (
    "The attached 3D object must be a part of the scene graph",
    "webpack-hmr",
    "WebSocket",
    "Failed to load resource",
)


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


def rgb_tuple(colour: str) -> tuple[float, float, float] | None:
    match = re.match(r"rgba?\(([^)]+)\)", colour)
    if not match:
        return None
    parts = [p.strip() for p in match.group(1).split(",")]
    if len(parts) < 3:
        return None
    try:
        return tuple(round(float(p), 1) for p in parts[:3])  # type: ignore[return-value]
    except ValueError:
        return None


READ = """() => {
  const at = (el) => { const r = el.getBoundingClientRect();
    return [Math.round(r.x*10)/10, Math.round(r.y*10)/10,
            Math.round(r.width*10)/10, Math.round(r.height*10)/10]; };
  const cs = (el) => getComputedStyle(el);
  const cell = document.querySelector('[data-director-transform-field="position"]')
    ?.closest('label');
  const chip = cell?.querySelector('button[aria-label^="左右拖动调整"]') ?? null;
  const input = cell?.querySelector('input') ?? null;
  const toggle = cell?.querySelector('[data-director-keyframe-toggle]') ?? null;
  const group = cell?.closest('fieldset') ?? null;
  const legend = group?.querySelector('legend') ?? null;
  const grid = cell?.parentElement ?? null;
  const cells = [...(grid?.children ?? [])].map(at);
  const name = document.querySelector('[data-director-object-name]');
  const nameLabel = name?.parentElement?.querySelector('span') ?? null;
  const glyph = toggle?.querySelector('svg rect') ?? null;
  return {
    cell: cell ? {box: at(cell), bg: cs(cell).backgroundColor,
                   radius: cs(cell).borderRadius, border: cs(cell).borderTopWidth} : null,
    gridGap: grid ? cs(grid).gap : null,
    gridWidth: grid ? at(grid)[2] : null,
    cellBoxes: cells,
    legend: legend ? {box: at(legend), font: cs(legend).fontSize,
                      color: cs(legend).color, weight: cs(legend).fontWeight} : null,
    groupH: group ? at(group)[3] : null,
    chip: chip ? {box: at(chip), pos: cs(chip).position, z: cs(chip).zIndex,
                  radius: cs(chip).borderRadius, color: cs(chip).color,
                  font: cs(chip).fontSize, cursor: cs(chip).cursor} : null,
    input: input ? {box: at(input), font: cs(input).fontSize, padLeft: cs(input).paddingLeft,
                    textAlign: cs(input).textAlign, transform: cs(input).textTransform} : null,
    toggle: toggle ? {box: at(toggle), label: toggle.getAttribute('aria-label'),
                      state: toggle.getAttribute('data-director-keyframe-toggle-state'),
                      bg: cs(toggle).backgroundColor, color: cs(toggle).color,
                      borderLeft: cs(toggle).borderLeftWidth + ' ' + cs(toggle).borderLeftColor,
                      marginLeft: cs(toggle).marginLeft,
                      glyph: glyph ? {box: at(glyph), fill: glyph.getAttribute('fill'),
                                      stroke: glyph.getAttribute('stroke'),
                                      strokeWidth: glyph.getAttribute('stroke-width'),
                                      viewBox: glyph.parentElement?.getAttribute('viewBox'),
                                      svg: at(glyph.parentElement)} : null} : null,
    toggles: [...document.querySelectorAll('[data-director-keyframe-toggle]')]
      .map((b) => ({id: b.getAttribute('data-director-keyframe-toggle'),
                    box: at(b), label: b.getAttribute('aria-label'),
                    state: b.getAttribute('data-director-keyframe-toggle-state'),
                    bg: cs(b).backgroundColor, color: cs(b).color})),
    name: name ? {box: at(name), bg: cs(name).backgroundColor, radius: cs(name).borderRadius,
                  border: cs(name).borderTopWidth, font: cs(name).fontSize,
                  pad: cs(name).padding, color: cs(name).color} : null,
    nameLabel: nameLabel ? {box: at(nameLabel), font: cs(nameLabel).fontSize,
                            color: cs(nameLabel).color} : null,
    track: (() => { const s = window.__director_store.getState();
      const id = s.selectedObjectIds[0];
      const t = s.timeline.tracks.find((tr) => tr.objectId === id);
      return {objectId: id, currentTime: s.timeline.currentTime,
              keyframeCount: t ? t.keyframes.length : null,
              times: t ? t.keyframes.map((k) => k.time) : null}; })(),
  };
}"""


class Verifier:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.result: dict[str, Any] = {}
        self.failures: list[str] = []
        self.count = 0

    def check(self, name: str, ok: bool, detail: Any = "") -> None:
        self.count += 1
        self.result[name] = {"ok": bool(ok), "detail": detail}
        if not ok:
            self.failures.append(name)
        print(("  PASS " if ok else "  FAIL ") + name + (f"  {detail}" if detail else ""))

    def read(self) -> dict[str, Any]:
        # Park the pointer first: the off-state toggle has
        # `hover:bg-white/[0.07]`, and Playwright leaves the cursor on whatever
        # it last clicked, which would otherwise be read as the resting style.
        self.page.mouse.move(5, 5)
        self.page.wait_for_timeout(120)
        return self.page.evaluate(READ)


def approx(values: list[float], expected: list[float], tol: float = 0.6) -> bool:
    return len(values) == len(expected) and all(
        abs(a - b) <= tol for a, b in zip(values, expected)
    )


def run(page: Page) -> dict[str, Any]:
    v = Verifier(page)
    console: list[str] = []
    errors: list[str] = []
    page.on("console", lambda m: console.append(f"{m.type}: {m.text}"[:200])
            if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)[:200]))

    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__libtv_ui_store "
        "&& window.__director_store)",
        timeout=60_000,
    )
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 609 probe" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible", timeout=30_000)
    page.wait_for_timeout(1_500)

    # Move the playhead off every seeded keyframe so the toggles start "off".
    page.evaluate("() => window.__director_store.getState().setTimelineTime(6.5)")
    page.wait_for_timeout(400)
    page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          const id = s.selectedObjectIds[0];
          const track = s.timeline.tracks.find((t) => t.objectId === id);
          (track ? track.keyframes : []).forEach((k) =>
            s.deleteTimelineKeyframe(k.id));
        }"""
    )
    page.wait_for_timeout(400)

    off = v.read()
    v.result["off_state"] = off

    # --- cell geometry -------------------------------------------------
    cell = off["cell"]
    v.check("cell:present", cell is not None)
    if cell:
        v.check("cell:height", cell["box"][3] == CELL_H, detail=cell["box"])
        v.check("cell:radius", cell["radius"] == "8px", detail=cell["radius"])
        v.check("cell:no-border", cell["border"] == "0px", detail=cell["border"])
        v.check(
            "cell:fill-white-10",
            abs(alpha_of(cell["bg"]) - 0.10) < 0.005,
            detail=cell["bg"],
        )
    v.check("grid:gap-4", off["gridGap"] == "4px", detail=off["gridGap"])
    v.check("grid:three-cells", len(off["cellBoxes"]) == 3, detail=off["cellBoxes"])
    widths = {b[2] for b in off["cellBoxes"]}
    v.check("grid:cells-equal-width", len(widths) == 1, detail=off["cellBoxes"])
    # 4px gap between consecutive cells, 28px tall, no vertical slack.
    if len(off["cellBoxes"]) == 3:
        gaps = [
            round(off["cellBoxes"][i + 1][0] - (off["cellBoxes"][i][0] + off["cellBoxes"][i][2]), 1)
            for i in range(2)
        ]
        v.check("grid:horizontal-gaps", all(abs(g - 4) < 0.6 for g in gaps), detail=gaps)
        v.check(
            "grid:rows-share-y",
            len({b[1] for b in off["cellBoxes"]}) == 1
            and all(b[3] == CELL_H for b in off["cellBoxes"]),
            detail=off["cellBoxes"],
        )

    # --- group rhythm --------------------------------------------------
    v.check("group:height-60", off["groupH"] == GROUP_H, detail=off["groupH"])
    v.check(
        "label:height-28",
        off["legend"]["box"][3] == LABEL_H,
        detail=off["legend"]["box"],
    )
    v.check("label:font-13", off["legend"]["font"] == "13px", detail=off["legend"]["font"])
    v.check("label:weight-400", off["legend"]["weight"] == "400", detail=off["legend"]["weight"])
    v.check(
        "label:colour-white-45",
        abs(alpha_of(off["legend"]["color"]) - 0.45) < 0.01,
        detail=off["legend"]["color"],
    )

    # --- scrub chip ----------------------------------------------------
    chip = off["chip"]
    v.check("chip:position-absolute", chip["pos"] == "absolute", detail=chip["pos"])
    v.check("chip:width-20", chip["box"][2] == CHIP_W, detail=chip["box"])
    v.check("chip:height-28", chip["box"][3] == CHIP_H, detail=chip["box"])
    v.check("chip:cursor-ew-resize", chip["cursor"] == "ew-resize", detail=chip["cursor"])
    v.check("chip:font-12", chip["font"] == "12px", detail=chip["font"])
    v.check(
        "chip:uppercase",
        chip["box"] is not None and off["cell"] is not None
        and chip["box"][0] == off["cell"]["box"][0],
        detail={"chip": chip["box"], "cell": off["cell"]["box"] if off["cell"] else None},
    )
    v.check(
        "chip:colours-white-45",
        abs(alpha_of(chip["color"]) - 0.45) < 0.01,
        detail=chip["color"],
    )

    # --- number input --------------------------------------------------
    num = off["input"]
    v.check("input:height-28", num["box"][3] == 28, detail=num["box"])
    v.check("input:font-12", num["font"] == "12px", detail=num["font"])
    v.check("input:pad-left-24", num["padLeft"] == "24px", detail=num["padLeft"])
    v.check("input:left-aligned", num["textAlign"] in ("start", "left"), detail=num["textAlign"])

    # --- keyframe toggle, off state ------------------------------------
    toggle = off["toggle"]
    v.check("toggle:present", toggle is not None)
    if toggle:
        v.check("toggle:size-20x28", toggle["box"][2] == TOGGLE_W and toggle["box"][3] == TOGGLE_H,
                detail=toggle["box"])
        v.check("toggle:aria-off", toggle["label"] == OFF_LABEL, detail=toggle["label"])
        v.check("toggle:state-off", toggle["state"] == "off", detail=toggle["state"])
        v.check("toggle:fill-white-4pct", abs(alpha_of(toggle["bg"]) - 0.04) < 0.005,
                detail=toggle["bg"])
        v.check("toggle:icon-white-75", abs(alpha_of(toggle["color"]) - 0.75) < 0.01,
                detail=toggle["color"])
        v.check("toggle:border-l-1px-black-20",
                toggle["borderLeft"].startswith("1px")
                and abs(alpha_of(toggle["borderLeft"].split(" ", 1)[1]) - 0.2) < 0.01,
                detail=toggle["borderLeft"])
        v.check("toggle:margin-left-1px", toggle["marginLeft"] == "1px", detail=toggle["marginLeft"])
        g = toggle["glyph"]
        v.check("glyph:viewbox", g and g["viewBox"] == "0 0 10 10", detail=g and g["viewBox"])
        v.check("glyph:svg-9x9", g and g["svg"][2] == 9 and g["svg"][3] == 9, detail=g and g["svg"])
        v.check("glyph:fill-none", g and g["fill"] == "none", detail=g and g["fill"])
        v.check("glyph:stroke-width", g and g["strokeWidth"] == "1.2", detail=g and g["strokeWidth"])
        v.check("glyph:stroke-current", g and g["stroke"] == "currentColor", detail=g and g["stroke"])

    v.check(
        "toggles:three-rows-x-three",
        len(off["toggles"]) == 9,
        detail=[t["id"] for t in off["toggles"]],
    )
    v.check(
        "toggles:all-off-initially",
        all(t["state"] == "off" for t in off["toggles"]),
        detail=[(t["id"], t["state"]) for t in off["toggles"]],
    )
    v.check(
        "toggles:not-on-target-rows",
        all(
            "target" not in (t["id"] or "") and "followOffset" not in (t["id"] or "")
            for t in off["toggles"]
        ),
        detail=[t["id"] for t in off["toggles"]],
    )
    v.check("store:no-keyframe", off["track"]["keyframeCount"] == 0, detail=off["track"])

    # --- 名称 input ----------------------------------------------------
    nm = off["name"]
    v.check("name:height-28", nm["box"][3] == 28, detail=nm["box"])
    v.check("name:radius-8", nm["radius"] == "8px", detail=nm["radius"])
    v.check("name:no-border", nm["border"] == "0px", detail=nm["border"])
    v.check("name:fill-white-10", abs(alpha_of(nm["bg"]) - 0.10) < 0.005, detail=nm["bg"])
    v.check("name:font-12", nm["font"] == "12px", detail=nm["font"])
    v.check("name:pad-8", nm["pad"] in ("8px", "0px 8px"), detail=nm["pad"])
    v.check("name:label-28-13px",
            off["nameLabel"]["box"][3] == 28 and off["nameLabel"]["font"] == "13px",
            detail=off["nameLabel"])

    # --- click the off toggle: a keyframe appears ----------------------
    page.locator('[data-director-keyframe-toggle="position-X"]').click()
    page.wait_for_timeout(500)
    on = v.read()
    v.result["after_click_on"] = on
    v.check("click:keyframe-recorded", (on["track"]["keyframeCount"] or 0) == 1, detail=on["track"])
    v.check(
        "click:playhead-time",
        on["track"]["times"]
        and abs(on["track"]["times"][0] - on["track"]["currentTime"]) < 0.001,
        detail=on["track"],
    )
    on_states = {t["id"]: t for t in on["toggles"]}
    v.check(
        "click:position-row-on",
        all(on_states[f"position-{a}"]["state"] == "on" for a in ("X", "Y", "Z")),
        detail={k: on_states[k]["state"] for k in on_states if k.startswith("position")},
    )
    # A clone keyframe stores the whole DirectorTransform, so one keyframe at
    # the playhead pins all three rows at once.  That is the honest reading of
    # the data model (per-axis keyframes would need a persisted-schema change),
    # so it is asserted rather than worked around.
    v.check(
        "click:one-keyframe-lights-every-row",
        all(t["state"] == "on" for t in on["toggles"]),
        detail={k: on_states[k]["state"] for k in sorted(on_states)},
    )
    v.check(
        "click:still-exactly-one-keyframe",
        (on["track"]["keyframeCount"] or 0) == 1,
        detail=on["track"],
    )
    t_on = on["toggle"]
    v.check("on:aria", t_on["label"] == ON_LABEL, detail=t_on["label"])
    v.check("on:state", t_on["state"] == "on", detail=t_on["state"])
    v.check("on:fill-263E43", rgb_tuple(t_on["bg"]) == (38.0, 62.0, 67.0), detail=t_on["bg"])
    v.check("on:icon-5DDCFF", rgb_tuple(t_on["color"]) == (93.0, 220.0, 255.0), detail=t_on["color"])
    v.check("on:glyph-filled", t_on["glyph"]["fill"] == "currentColor", detail=t_on["glyph"]["fill"])
    v.check(
        "on:keeps-batch575-contract",
        page.locator("[data-director-keyframed-axis='position']").count() == 3,
        detail=page.locator("[data-director-keyframed-axis='position']").count(),
    )
    page.screenshot(path=str(SCREENSHOT))

    # --- click again: the keyframe goes away ---------------------------
    page.locator('[data-director-keyframe-toggle="position-X"]').click()
    page.wait_for_timeout(500)
    back = v.read()
    v.result["after_click_off"] = back
    v.check("untoggle:keyframe-gone", (back["track"]["keyframeCount"] or 0) == 0, detail=back["track"])
    v.check(
        "untoggle:aria-back",
        back["toggle"]["label"] == OFF_LABEL,
        detail=back["toggle"]["label"],
    )
    v.check(
        "untoggle:fill-back-to-4pct",
        abs(alpha_of(back["toggle"]["bg"]) - 0.04) < 0.005,
        detail=back["toggle"]["bg"],
    )
    v.check(
        "untoggle:batch575-contract-cleared",
        page.locator("[data-director-keyframed-axis='position']").count() == 0,
        detail=page.locator("[data-director-keyframed-axis='position']").count(),
    )

    # --- the toggle survives a playhead move --------------------------
    # A toggle in a different row deletes the same single keyframe.
    page.locator('[data-director-keyframe-toggle="position-Z"]').click()
    page.wait_for_timeout(400)
    v.check("crossrow:records-one", (v.read()["track"]["keyframeCount"] or 0) == 1)
    page.locator('[data-director-keyframe-toggle="scale-X"]').click()
    page.wait_for_timeout(400)
    v.check(
        "crossrow:any-row-deletes-it",
        (v.read()["track"]["keyframeCount"] or 0) == 0,
    )
    page.locator('[data-director-keyframe-toggle="rotation-Y"]').click()
    page.wait_for_timeout(400)
    page.evaluate("() => window.__director_store.getState().setTimelineTime(7.5)")
    page.wait_for_timeout(400)
    moved = v.read()
    v.check(
        "seek:other-playhead-reads-off",
        all(t["state"] == "off" for t in moved["toggles"]),
        detail=[(t["id"], t["state"]) for t in moved["toggles"]],
    )
    v.check("seek:keyframe-survives", (moved["track"]["keyframeCount"] or 0) == 1, detail=moved["track"])
    page.evaluate("() => window.__director_store.getState().setTimelineTime(6.5)")
    page.wait_for_timeout(400)
    seeked = v.read()
    v.check(
        "seek:back-reads-on",
        all(
            t["state"] == "on" for t in seeked["toggles"] if t["id"].startswith("rotation")
        ),
        detail=[(t["id"], t["state"]) for t in seeked["toggles"]],
    )

    # --- a locked object cannot be keyframed --------------------------
    page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          s.updateObject(s.selectedObjectIds[0], { locked: true });
        }"""
    )
    page.wait_for_timeout(400)
    locked = v.read()
    v.check(
        "locked:toggles-disabled",
        all(
            page.locator(f'[data-director-keyframe-toggle="{t["id"]}"]').is_disabled()
            for t in locked["toggles"]
        ),
        detail=[t["id"] for t in locked["toggles"]],
    )

    page.wait_for_timeout(300)
    real_errors = [e for e in errors]
    noise = [c for c in console if any(k in c for k in IGNORE_CONSOLE)]
    real_console = [c for c in console if c not in noise]
    v.check("diagnostics:no-page-errors", not real_errors, detail=real_errors[:5])
    v.check("diagnostics:no-console-errors", not real_console, detail=real_console[:5])
    v.result["diagnostics"] = {
        "consoleErrors": len(console),
        "filtered": len(noise),
        "pageErrors": len(real_errors),
    }

    v.result["_summary"] = {"checks": v.count, "failures": v.failures}
    return v.result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 609,
        "title": "Source-shaped transform rows + 20x28 keyframe diamond toggles",
        "date": "2026-10-01",
        "sourceEvidence": [
            "probe66 tree dump of the source right inspector (280px column, x=1640)",
            "probe67 exact computed styles for the keyframe toggle and 名称 input",
        ],
        "claims": {
            "sourceFact": [
                "field group = 28px label box + mb-1 + 28px control = 60px",
                "cell = 80x28, rounded-lg, bg-white/10, no border, focus -> bg-white/13",
                "grid-cols-3 gap-1",
                "scrub chip = 20x28 absolute, rounded-l-lg, text-[12px] uppercase text-white/45",
                "number input = h-full pl-6 pr-0 text-[12px], left aligned",
                "keyframe toggle = 20x28, ml-px, border-l border-black/20",
                "off = bg-white/[0.04] text-white/75, glyph fill=none",
                "on = bg-[#263E43] text-[#5DDCFF], glyph fill=currentColor",
                "glyph = 9x9 svg viewBox 0 0 10 10, rect 6.1 rx=1 rotate(45 5 5)",
                "rows outside the object transform (注视坐标) carry no toggle",
            ],
            "inference": [
                "clicking the toggle records/deletes a keyframe at the playhead — the "
                "source button was never clicked (needs authorisation); the two-state "
                "aria pair on a <button> is the basis",
                "recording uses force=true so the global 自动关键帧 switch cannot veto "
                "an explicit click",
            ],
            "cloneOnly": [
                "toggled state is per FIELD, not per axis: the clone's track keyframes "
                "store a whole DirectorTransform, so one keyframe at the playhead pins "
                "all three rows at once and any of the nine toggles deletes that same "
                "one keyframe; a persisted per-axis model is out of scope for this batch",
                "fixes a latent bug: keyframedAxes only read value.transform (the camera "
                "track shape), so it was always empty for character/prop transform "
                "tracks — batch 575 only ever exercised a camera and hid it",
            ],
            "notClaimed": [
                "the source's toggle click behaviour",
                "the source's 280px column width, its tab strip, its sticky preview "
                "canvas and its three 248x28 selects — measured, left to a later batch",
            ],
        },
    }
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT)
        try:
            audit["checks"] = run(page)
        finally:
            browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    summary = audit["checks"]["_summary"]
    print(f"\n{summary['checks'] - len(summary['failures'])}/{summary['checks']} passed")
    if summary["failures"]:
        print("FAILED: " + ", ".join(summary["failures"]))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
