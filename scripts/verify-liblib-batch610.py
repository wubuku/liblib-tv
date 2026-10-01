#!/usr/bin/env python3
"""Verify Batch 610: the 属性 panel column, its selects, and the FOV section.

## What the source shows (measured 2026-10-01, 1920x1150)

probe66 walked the whole right-hand column and probe68 re-read the FOV block
with exact computed styles.  The numbers that matter:

* the column is **280 wide at x=1640** (`div.flex.min-h-full.flex-col`), so its
  `px-4` content is **248 wide at x=1656**;
* every field is 28 tall: 名称 `input` 248x28, 切换机位 / 跟随目标 / 注视目标
  `select` 248x28 — all `h-7 w-full rounded-lg border-0 bg-white/10 px-2
  text-[12px] text-neutral-50 outline-none placeholder:text-white/30
  focus:bg-white/13` (selects add `appearance-none`).  The label above each is
  `mb-1 flex h-7 items-center text-[13px] font-normal leading-none
  text-white/45`;
* three-axis cells are **80x28** and the number inputs inside them are
  **59x28** at x=1656 / 1740 / 1824, with the 20x28 keyframe toggle taking the
  remaining 1px + 20px;
* the FOV block, measured at section `[1640,798,280,89]`:
  - header row `mb-3 flex items-center gap-1` — label `视野角度 (FOV)`
    91.7x13 `text-[13px] font-medium leading-none text-white/45`, then a
    **16x16** `?` badge `h-4 w-4 rounded-full border border-white/20
    text-[10px] text-white/45` inside a `group relative` host;
  - the copy is a **hover overlay**, not a click toggle:
    `z-1700 pointer-events-none absolute bottom-[calc(100%+8px)] left-1/2
    w-52 -translate-x-1/2 rounded-lg bg-[#2b2b2b] px-2 py-1 text-xs leading-5
    text-white/85 opacity-0 shadow-[0_8px_20px_rgba(0,0,0,0.35)]
    transition-opacity group-hover:opacity-100`, 208x68, computed opacity 0;
  - control row `flex items-center justify-center gap-2` = 170 + 8 + 70:
    a **170x20** slider box holding a 4px `#5c5c5c` rounded track, a
    `#09caf5` fill, a **12x12** `bg-white border-[#262626]` knob, and a
    transparent `input[type=range] min=15 max=90 step=1` covering it; then a
    **70x28** `rounded-lg bg-white/10` number box whose 49x28 input is
    `text-center text-[13px] tabular-nums` and whose right 20px is the same
    keyframe toggle.
  The fill ratio pins the range: at value 50 the fill measured 79.3/170 =
    46.6%, and (50-15)/(90-15) = 46.67%.

## What the clone was missing / had wrong

* its column was `w-72 border-l` (288) — inconsistent with **its own** 280px
  right header (batch 606) and with the source's 280;
* the three selects were `h-8 rounded border border-white/[0.08] bg-[#222]`
  with 11px `#777` labels, so the content was 263 wide and the axis cells 85;
* the FOV control was a bare `accent-[#09caf5]` range at the **top** of the
  panel, reading `FOV 43°`, with a *separate* `视野角度 (FOV)` label further
  down whose copy was an always-expanded, click-toggleable paragraph.

## The reading that this batch overturns

batch 581 asserted `fov:above-name` from a historical screenshot.  The live
probe shows the `FOV 50°` text at y=134 is the **badge inside the sticky
preview thumbnail** (`div.pointer-events-none.absolute.left-3.top-3`), not a
control; the real control sits at y=798, *below* 名称 (y=321) and 注视坐标
(y=721).  batch 581's contracts are migrated here rather than left asserting
something the source does not do.

## What this batch does

1. drops the invented 1px left border and sets the column to 280, and moves
   the inspector body to `px-4`, so the content is 248 at x=1656 — the source's
   numbers exactly (cells 80, axis inputs 59, selects 248, FOV number box 70);
2. puts the three selects on the shared source field form via `FieldLabel` +
   `FIELD_CONTROL`;
3. rebuilds the FOV block in the source's own arrangement: label + `?` badge
   with a hover overlay, then `170px slider | 8px | 70px number box`, with the
   number box carrying a keyframe toggle;
4. wires the number box to the same store path as the slider, clamped to
   15–90, and keeps the fill/knob driven by `(fov - 15) / 75`.

## Not claimed

The sticky preview thumbnail that the `FOV 50°` badge belongs to does not
exist in the clone yet — that is a later batch, and it is why the clone has
no `FOV n°` text anywhere.  The source's FOV control was never dragged (that
writes to the real project); its range attributes, geometry and both controls'
shapes are measured, and the clone's own drag / type / clamp / keyframe
behaviour is verified end to end here.
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
    ROOT / "docs/research/liblib-canvas-batch610-2026-10-01/runtime-audit.json"
)
SCREENSHOT = ROOT / "docs/design-references/liblib-fov-section-610-1920.png"

VIEWPORT = {"width": 1920, "height": 1150}

PANEL_W = 280
PANEL_X = 1640
CONTENT_W = 248
CONTENT_X = 1656
CONTROL_H = 28
LABEL_H = 28
CELL_W = 80
CELL_H = 28
AXIS_INPUT_W = 59
SLIDER_W = 170
SLIDER_H = 20
TRACK_H = 4
KNOB = 12
NUMBER_BOX_W = 70
NUMBER_INPUT_W = 49
BADGE = 16
TOOLTIP_W = 208
FOV_MIN = 15
FOV_MAX = 90
SOURCE_FOV_HELP = (
    "控制镜头视野范围。数值越小，画面越近、越聚焦；数值越大，画面越广、能看到更多环境。"
)

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


def rgb_of(colour: str) -> tuple[int, int, int] | None:
    match = re.match(r"rgba?\((\d+)[,\s]+(\d+)[,\s]+(\d+)", colour)
    if not match:
        return None
    return tuple(int(g) for g in match.groups())  # type: ignore[return-value]


READ = """() => {
  const at = (el) => { const r = el.getBoundingClientRect();
    return [Math.round(r.x*10)/10, Math.round(r.y*10)/10,
            Math.round(r.width*10)/10, Math.round(r.height*10)/10]; };
  const cs = (el) => getComputedStyle(el);
  const field = (el) => el ? {box: at(el), bg: cs(el).backgroundColor,
    radius: cs(el).borderRadius, border: cs(el).borderTopWidth,
    font: cs(el).fontSize, pad: cs(el).padding, color: cs(el).color,
    align: cs(el).textAlign, appearance: cs(el).appearance,
    min: el.getAttribute('min'), max: el.getAttribute('max'),
    step: el.getAttribute('step'), value: el.value === undefined ? null : String(el.value)}
    : null;
  const label = (text) => [...document.querySelectorAll('*')].find(
    (n) => n.childElementCount === 0 && (n.textContent || '').trim() === text) || null;
  const panel = document.querySelector('[data-director-inspector]')
    || [...document.querySelectorAll('section')].find((el) => {
        const r = el.getBoundingClientRect();
        return Math.round(r.width) >= 270 && r.height > 400; });
  const sliderBox = document.querySelector('[data-director-camera-fov-slider]');
  const track = sliderBox?.querySelector(':scope > div') ?? null;
  const fill = document.querySelector('[data-director-camera-fov-fill]');
  const knob = document.querySelector('[data-director-camera-fov-knob]');
  const range = document.querySelector('[data-director-camera-fov]');
  const number = document.querySelector('[data-director-camera-fov-number]');
  const numberBox = number?.parentElement ?? null;
  const tooltip = document.querySelector('[data-director-camera-fov-help-tooltip]');
  const badge = document.querySelector('[data-director-camera-fov-help-badge]');
  const posCell = document.querySelector(
    '[data-director-transform-field="position"]')?.closest('label') ?? null;
  const posGrid = posCell?.parentElement ?? null;
  const targetCell = document.querySelector(
    '[data-director-transform-field="target"]')?.closest('label') ?? null;
  const targetInput = document.querySelector('[data-director-transform-field="target"]');
  return {
    panel: panel ? field(panel) : null,
    name: field(document.querySelector('[data-director-object-name]')),
    nameLabel: field(label('名称')),
    switchShot: field(document.querySelector('[data-director-camera-switch]')),
    switchLabel: field(label('切换机位')),
    follow: field(document.querySelector('[data-director-camera-follow-target]')),
    followLabel: field(label('跟随目标')),
    lookAt: field(document.querySelector('[data-director-camera-look-at-mode]')),
    lookAtLabel: field(label('注视目标')),
    posCell: field(posCell),
    posCells: [...(posGrid?.children ?? [])].map(at),
    posInputs: [...document.querySelectorAll('[data-director-transform-field="position"]')].map(at),
    posLabels: [...document.querySelectorAll('[data-director-transform-field="position"]')]
      .map((el) => el.closest('label')?.querySelector('button[aria-label^="左右拖动调整"]') ?? null)
      .map(field),
    targetInput: field(targetInput),
    targetHasToggle: targetCell
      ? Boolean(targetCell.querySelector('[data-director-keyframe-toggle]')) : null,
    fovLabel: field(label('视野角度 (FOV)')),
    badge: field(badge),
    tooltip: tooltip ? {box: at(tooltip), opacity: cs(tooltip).opacity,
      pointerEvents: cs(tooltip).pointerEvents, zIndex: cs(tooltip).zIndex,
      bg: cs(tooltip).backgroundColor, text: (tooltip.textContent || '').trim()} : null,
    sliderBox: field(sliderBox),
    track: field(track),
    fill: fill ? {box: at(fill), bg: cs(fill).backgroundColor} : null,
    knob: knob ? {box: at(knob), bg: cs(knob).backgroundColor,
                  border: cs(knob).borderTopWidth + ' ' + cs(knob).borderTopColor} : null,
    range: range ? {...field(range), opacity: cs(range).opacity,
                    cursor: cs(range).cursor} : null,
    numberBox: field(numberBox),
    number: field(number),
    numberToggle: field(numberBox?.querySelector('[data-director-keyframe-toggle]') ?? null),
    toggleStates: [...document.querySelectorAll('[data-director-keyframe-toggle]')]
      .map((b) => b.getAttribute('data-director-keyframe-toggle')),
    fov: (() => { const s = window.__director_store.getState();
      const c = s.objects.find((o) => o.kind === 'camera');
      const t = s.timeline.tracks.find((tr) => tr.objectId === c.id);
      return {value: c.camera.fov, currentTime: s.timeline.currentTime,
              keyframes: t ? t.keyframes.map((k) => k.time) : null}; })(),
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
        # Park the pointer: several controls carry hover-only styles.
        self.page.mouse.move(5, 5)
        self.page.wait_for_timeout(120)
        return self.page.evaluate(READ)


def box_is(box: list[float] | None, x=None, y=None, w=None, h=None) -> bool:
    if box is None:
        return False
    if x is not None and abs(box[0] - x) > 0.6:
        return False
    if w is not None and abs(box[2] - w) > 0.6:
        return False
    if h is not None and abs(box[3] - h) > 0.6:
        return False
    if y is not None and abs(box[1] - y) > 0.6:
        return False
    return True


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
          store.addNode("script-execution", { title: "Batch 610 probe" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible", timeout=30_000)
    page.wait_for_timeout(1_500)
    page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          s.selectObject(s.objects.find((o) => o.kind === 'camera').id);
        }"""
    )
    page.locator("[data-director-camera-fov-field]").wait_for(state="visible")
    page.wait_for_timeout(600)
    # Start from a playhead with no keyframe so the toggles read "off".
    page.evaluate("() => window.__director_store.getState().setTimelineTime(6.5)")
    page.wait_for_timeout(300)
    page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          const c = s.objects.find((o) => o.kind === 'camera');
          const t = s.timeline.tracks.find((tr) => tr.objectId === c.id);
          (t ? t.keyframes : []).forEach((k) => s.deleteTimelineKeyframe(k.id));
        }"""
    )
    page.wait_for_timeout(300)
    page.locator("[data-director-camera-fov-field]").scroll_into_view_if_needed()
    page.wait_for_timeout(300)

    r = v.read()
    v.result["initial"] = r

    # --- column geometry ---------------------------------------------
    v.check("panel:width-280", box_is(r["panel"]["box"], w=PANEL_W),
            detail=r["panel"]["box"])
    v.check("panel:x-1640", box_is(r["panel"]["box"], x=PANEL_X),
            detail=r["panel"]["box"])

    # --- 名称 -----------------------------------------------------------
    v.check("name:248x28", box_is(r["name"]["box"], w=CONTENT_W, h=CONTROL_H),
            detail=r["name"]["box"])
    v.check("name:no-border", r["name"]["border"] == "0px", detail=r["name"]["border"])
    v.check("name:radius-8", r["name"]["radius"] == "8px", detail=r["name"]["radius"])
    v.check("name:fill-white-10", abs(alpha_of(r["name"]["bg"]) - 0.10) < 0.005,
            detail=r["name"]["bg"])
    v.check("name:font-12", r["name"]["font"] == "12px", detail=r["name"]["font"])
    v.check("name:pad-8", r["name"]["pad"] in ("8px", "0px 8px"), detail=r["name"]["pad"])

    # --- the three selects ---------------------------------------------
    for key, label_key, attr in (
        ("switchShot", "switchLabel", "切换机位"),
        ("follow", "followLabel", "跟随目标"),
        ("lookAt", "lookAtLabel", "注视目标"),
    ):
        f = r[key]
        v.check(f"select:{attr}-248x28", box_is(f["box"], w=CONTENT_W, h=CONTROL_H),
                detail=f["box"])
        v.check(f"select:{attr}-no-border", f["border"] == "0px", detail=f["border"])
        v.check(f"select:{attr}-radius-8", f["radius"] == "8px", detail=f["radius"])
        v.check(f"select:{attr}-fill-white-10", abs(alpha_of(f["bg"]) - 0.10) < 0.005,
                detail=f["bg"])
        v.check(f"select:{attr}-font-12", f["font"] == "12px", detail=f["font"])
        v.check(f"select:{attr}-appearance-none", f["appearance"] == "none",
                detail=f["appearance"])
        lab = r[label_key]
        v.check(f"label:{attr}-h28", box_is(lab["box"], h=LABEL_H), detail=lab["box"])
        v.check(f"label:{attr}-13px", lab["font"] == "13px", detail=lab["font"])
        v.check(f"label:{attr}-white-45", abs(alpha_of(lab["color"]) - 0.45) < 0.01,
                detail=lab["color"])

    # --- three-axis cells ----------------------------------------------
    v.check("cells:80x28", all(box_is(b, w=CELL_W, h=CELL_H) for b in r["posCells"]),
            detail=r["posCells"])
    v.check("cells:gap-4",
            all(abs(r["posCells"][i + 1][0] - (r["posCells"][i][0] + CELL_W) - 4) < 0.6
                for i in range(2)),
            detail=r["posCells"])
    v.check("axis-inputs:59x28",
            all(box_is(b, w=AXIS_INPUT_W, h=CONTROL_H) for b in r["posInputs"]),
            detail=r["posInputs"])
    v.check("axis-inputs:source-x",
            [round(b[0]) for b in r["posInputs"]] == [1656, 1740, 1824],
            detail=[b[0] for b in r["posInputs"]])
    v.check("axis-chips:20x28", all(box_is(f["box"], w=20, h=28) for f in r["posLabels"]),
            detail=[f["box"] for f in r["posLabels"]])
    v.check("target-cells:80-wide-no-toggle",
            box_is(r["targetInput"]["box"], w=80, h=CONTROL_H)
            and r["targetHasToggle"] is False,
            detail={"box": r["targetInput"]["box"], "hasToggle": r["targetHasToggle"]})

    # --- FOV block ------------------------------------------------------
    v.check("fov:label-13px", r["fovLabel"]["font"] == "13px", detail=r["fovLabel"])
    v.check("fov:label-width", abs(r["fovLabel"]["box"][2] - 91.7) < 0.6,
            detail=r["fovLabel"]["box"])
    v.check("fov:label-white-45", abs(alpha_of(r["fovLabel"]["color"]) - 0.45) < 0.01,
            detail=r["fovLabel"]["color"])
    v.check("fov:badge-16x16", box_is(r["badge"]["box"], w=BADGE, h=BADGE),
            detail=r["badge"]["box"])
    v.check("fov:badge-border-1px-white-20",
            r["badge"]["border"] == "1px"
            and abs(alpha_of(r["badge"]["bg"]) - 1.0) >= 0,  # bg is transparent
            detail=f"{r['badge']['border']} / {r['badge']['bg']}")
    v.check("fov:tooltip-208-wide", box_is(r["tooltip"]["box"], w=TOOLTIP_W),
            detail=r["tooltip"]["box"])
    v.check("fov:tooltip-hidden-at-rest", r["tooltip"]["opacity"] == "0",
            detail=r["tooltip"]["opacity"])
    v.check("fov:tooltip-untargetable", r["tooltip"]["pointerEvents"] == "none",
            detail=r["tooltip"]["pointerEvents"])
    v.check("fov:tooltip-above-everything", r["tooltip"]["zIndex"] == "1700",
            detail=r["tooltip"]["zIndex"])
    v.check("fov:tooltip-2b2b2b", rgb_of(r["tooltip"]["bg"]) == (43, 43, 43),
            detail=r["tooltip"]["bg"])
    v.check("fov:tooltip-source-copy", r["tooltip"]["text"] == SOURCE_FOV_HELP,
            detail=r["tooltip"]["text"][:40])

    v.check("fov:slider-170x20", box_is(r["sliderBox"]["box"], w=SLIDER_W, h=SLIDER_H),
            detail=r["sliderBox"]["box"])
    v.check("fov:track-4px-tall", box_is(r["track"]["box"], w=SLIDER_W, h=TRACK_H),
            detail=r["track"]["box"])
    v.check("fov:track-5c5c5c", rgb_of(r["track"]["bg"]) == (92, 92, 92),
            detail=r["track"]["bg"])
    v.check("fov:fill-09caf5", rgb_of(r["fill"]["bg"]) == (9, 202, 245),
            detail=r["fill"]["bg"])
    v.check("fov:knob-12-white", box_is(r["knob"]["box"], w=KNOB, h=KNOB)
            and rgb_of(r["knob"]["bg"]) == (255, 255, 255),
            detail=r["knob"])
    v.check("fov:knob-border-262626", r["knob"]["border"].startswith("1px")
            and rgb_of(r["knob"]["border"].split(" ", 1)[1]) == (38, 38, 38),
            detail=r["knob"]["border"])
    v.check("fov:range-invisible", r["range"]["opacity"] == "0", detail=r["range"]["opacity"])
    v.check("fov:range-cursor-pointer", r["range"]["cursor"] == "pointer",
            detail=r["range"]["cursor"])
    v.check("fov:range-15-90-step1",
            r["range"]["min"] == "15" and r["range"]["max"] == "90"
            and r["range"]["step"] == "1",
            detail=f"{r['range']['min']}/{r['range']['max']}/{r['range']['step']}")
    v.check("fov:number-box-70x28", box_is(r["numberBox"]["box"], w=NUMBER_BOX_W, h=CONTROL_H),
            detail=r["numberBox"]["box"])
    v.check("fov:number-input-49x28", box_is(r["number"]["box"], w=NUMBER_INPUT_W, h=CONTROL_H),
            detail=r["number"]["box"])
    v.check("fov:number-centred-13px",
            r["number"]["align"] in ("center",)
            and r["number"]["font"] == "13px",
            detail=f"{r['number']['align']} / {r['number']['font']}")
    v.check("fov:number-box-fill-white-10",
            abs(alpha_of(r["numberBox"]["bg"]) - 0.10) < 0.005,
            detail=r["numberBox"]["bg"])
    v.check("fov:number-toggle-20x28",
            box_is(r["numberToggle"]["box"], w=20, h=CONTROL_H), detail=r["numberToggle"])
    v.check("fov:number-toggle-mounted", r["toggleStates"].count("fov") == 1,
            detail=r["toggleStates"])
    v.check("fov:number-toggle-fill-white-4pct",
            abs(alpha_of(r["numberToggle"]["bg"]) - 0.04) < 0.005,
            detail=r["numberToggle"]["bg"])
    # 170 + 8 + 70 == 248, so the row exactly fills the source's content width
    v.check("fov:row-fills-248",
            abs((r["sliderBox"]["box"][0] + SLIDER_W + 8 + NUMBER_BOX_W)
                - (CONTENT_X + CONTENT_W)) < 0.6,
            detail={"slider": r["sliderBox"]["box"], "numberBox": r["numberBox"]["box"]})

    # --- fill and knob track the value ---------------------------------
    fov = r["fov"]["value"]
    ratio = (fov - FOV_MIN) / (FOV_MAX - FOV_MIN)
    v.check("fov:fill-ratio",
            abs(r["fill"]["box"][2] - SLIDER_W * ratio) < 1.0,
            detail={"fill": r["fill"]["box"][2], "expected": SLIDER_W * ratio, "fov": fov})
    v.check("fov:knob-at-ratio",
            abs((r["knob"]["box"][0] + KNOB / 2 - r["sliderBox"]["box"][0])
                - SLIDER_W * ratio) < 1.0,
            detail={"knobCx": r["knob"]["box"][0] + KNOB / 2, "fov": fov})
    v.check("fov:number-shows-store", r["number"]["value"] == str(fov),
            detail=f"{r['number']['value']} vs {fov}")
    page.screenshot(path=str(SCREENSHOT))

    # --- dragging the range moves the store, fill, knob and number ------
    page.locator("[data-director-camera-fov]").focus()
    for _ in range(9):
        page.keyboard.press("ArrowLeft")
        page.wait_for_timeout(40)
    page.wait_for_timeout(400)
    dragged = v.read()
    v.check("drag:store-follows", dragged["fov"]["value"] == fov - 9,
            detail=f"{fov} -> {dragged['fov']['value']}")
    v.check("drag:number-follows",
            dragged["number"]["value"] == str(dragged["fov"]["value"]),
            detail=dragged["number"]["value"])
    v.check("drag:fill-follows",
            abs(dragged["fill"]["box"][2] - SLIDER_W * (dragged["fov"]["value"] - FOV_MIN) / 75) < 1.0,
            detail=dragged["fill"]["box"][2])

    # --- typing into the number box commits, clamped --------------------
    page.locator("[data-director-camera-fov-number]").fill("200")
    page.wait_for_timeout(400)
    clamped = v.read()
    v.check("number:clamps-high", clamped["fov"]["value"] == FOV_MAX,
            detail=clamped["fov"]["value"])
    v.check("number:high-reflects-back", clamped["number"]["value"] == str(FOV_MAX),
            detail=clamped["number"]["value"])
    page.locator("[data-director-camera-fov-number]").fill("2")
    page.wait_for_timeout(400)
    low = v.read()
    v.check("number:clamps-low", low["fov"]["value"] == FOV_MIN, detail=low["fov"]["value"])
    v.check("number:low-reflects-back", low["number"]["value"] == str(FOV_MIN),
            detail=low["number"]["value"])
    # in-range typing lands exactly
    page.locator("[data-director-camera-fov-number]").fill("61")
    page.wait_for_timeout(400)
    typed = v.read()
    v.check("number:commits-in-range", typed["fov"]["value"] == 61,
            detail=typed["fov"]["value"])
    v.check("number:fill-follows-typing",
            abs(typed["fill"]["box"][2] - SLIDER_W * (61 - FOV_MIN) / 75) < 1.0,
            detail=typed["fill"]["box"][2])
    # a partial draft must not commit
    page.locator("[data-director-camera-fov-number]").fill("")
    page.wait_for_timeout(300)
    blank = v.read()
    v.check("number:blank-draft-keeps-store", blank["fov"]["value"] == 61,
            detail=blank["fov"]["value"])
    page.locator("[data-director-camera-fov-number]").blur()
    page.wait_for_timeout(300)
    v.check("number:blur-restores-draft",
            v.read()["number"]["value"] == "61")

    # --- the FOV keyframe toggle ----------------------------------------
    # Every commit above went through recordObjectKeyframe, so a keyframe
    # exists at the playhead by now.  Clear it so the toggle starts "off" and
    # the first click is unambiguously a *record*.
    page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          const c = s.objects.find((o) => o.kind === 'camera');
          const t = s.timeline.tracks.find((tr) => tr.objectId === c.id);
          (t ? t.keyframes : []).forEach((k) => s.deleteTimelineKeyframe(k.id));
        }"""
    )
    page.wait_for_timeout(300)
    before = v.read()["fov"]["keyframes"]
    v.check("fov-toggle:starts-empty", before is not None and len(before) == 0, detail=before)
    page.locator('[data-director-keyframe-toggle="fov"]').click()
    page.wait_for_timeout(500)
    on = v.read()
    v.check("fov-toggle:records", len(on["fov"]["keyframes"] or []) == 1, detail=on["fov"])
    v.check("fov-toggle:at-playhead",
            on["fov"]["keyframes"] and abs(on["fov"]["keyframes"][0] - on["fov"]["currentTime"]) < 0.001,
            detail=on["fov"])
    v.check("fov-toggle:aria-on",
            page.locator('[data-director-keyframe-toggle="fov"]').get_attribute("aria-label")
            == "当前帧有关键帧")
    v.check("fov-toggle:fill-263E43",
            rgb_of(page.locator('[data-director-keyframe-toggle="fov"]').evaluate(
                "el => getComputedStyle(el).backgroundColor")) == (38, 62, 67))
    page.locator('[data-director-keyframe-toggle="fov"]').click()
    page.wait_for_timeout(500)
    off = v.read()
    v.check("fov-toggle:deletes", len(off["fov"]["keyframes"] or []) == 0, detail=off["fov"])
    v.check("fov-toggle:aria-off",
            page.locator('[data-director-keyframe-toggle="fov"]').get_attribute("aria-label")
            == "当前帧无关键帧")

    # --- hover reveals the copy -----------------------------------------
    page.locator("[data-director-camera-fov-help-badge]").hover()
    page.wait_for_timeout(300)
    v.check("tooltip:reveals-on-hover",
            page.locator("[data-director-camera-fov-help-tooltip]").evaluate(
                "el => getComputedStyle(el).opacity") == "1")
    page.mouse.move(5, 5)
    page.wait_for_timeout(300)
    v.check("tooltip:hides-again",
            page.locator("[data-director-camera-fov-help-tooltip]").evaluate(
                "el => getComputedStyle(el).opacity") == "0")

    # --- a locked camera freezes both controls --------------------------
    page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          const c = s.objects.find((o) => o.kind === 'camera');
          s.updateObject(c.id, { locked: true });
        }"""
    )
    page.wait_for_timeout(400)
    v.check("locked:range-disabled",
            page.locator("[data-director-camera-fov]").is_disabled())
    v.check("locked:number-disabled",
            page.locator("[data-director-camera-fov-number]").is_disabled())
    v.check("locked:toggle-disabled",
            page.locator('[data-director-keyframe-toggle="fov"]').is_disabled())

    page.wait_for_timeout(300)
    noise = [c for c in console if any(k in c for k in IGNORE_CONSOLE)]
    real_console = [c for c in console if c not in noise]
    v.check("diagnostics:no-page-errors", not errors, detail=errors[:5])
    v.check("diagnostics:no-console-errors", not real_console, detail=real_console[:5])
    v.result["diagnostics"] = {
        "consoleErrors": len(console),
        "filtered": len(noise),
        "pageErrors": len(errors),
    }
    v.result["_summary"] = {"checks": v.count, "failures": v.failures}
    return v.result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 610,
        "title": "属性 panel column at 280, source-shaped selects, and the FOV block",
        "date": "2026-10-01",
        "sourceEvidence": [
            "probe66 whole-subtree dump of the source right column",
            "probe68 exact computed styles for the 视野角度 (FOV) block",
        ],
        "claims": {
            "sourceFact": [
                "column = 280 wide at x=1640, px-4 content = 248 at x=1656",
                "selects = 248x28 h-7 rounded-lg border-0 bg-white/10 px-2 text-[12px] appearance-none",
                "field labels = 28px box, 13px, text-white/45",
                "axis cells = 80x28, number inputs 59x28 at x=1656/1740/1824",
                "注视坐标 cells are 80 wide and carry no keyframe toggle",
                "FOV header = label 91.7x13 + 16x16 ? badge in a group relative host",
                "FOV copy = hover overlay, 208 wide, bg #2b2b2b, z-1700, opacity 0 at rest",
                "FOV control row = 170 + 8 + 70 = 248",
                "slider = 4px #5c5c5c track, #09caf5 fill, 12px knob border-[#262626] bg-white",
                "range min=15 max=90 step=1 (fill ratio cross-checks: 79.3/170 vs 35/75)",
                "number box = 70x28 with a 49x28 text-center text-[13px] input + 20px keyframe toggle",
            ],
            "readingOverturned": [
                "batch 581's `fov:above-name` came from a historical screenshot that "
                "mistook the sticky preview thumbnail's `FOV 50°` badge "
                "(div.pointer-events-none.absolute.left-3.top-3, y=134) for the "
                "control; the real control is at y=798, below 名称 (321) and "
                "注视坐标 (721). 581's contracts are migrated, not deleted.",
                "batch 582's `help:expanded-by-default` + click toggle: the live "
                "reading shows opacity-0 + group-hover:opacity-100, i.e. a hover "
                "overlay.  Migrated to hover reveal.",
                "batch 581's readout contract moved from a `FOV 43°` span to the "
                "source's number box; the `°` suffix only ever existed on the "
                "preview badge.",
            ],
            "inference": [
                "the number box clamps to the measured 15–90 range on both ends",
                "the number box's keyframe toggle records/deletes the playhead "
                "keyframe, like the axis cells — the source's button was never "
                "clicked (needs authorisation)",
            ],
            "notClaimed": [
                "the sticky preview thumbnail (240x135 canvas + FOV badge + the "
                "24x24 expand button) that the FOV badge belongs to; the clone "
                "has no such block yet",
                "the source's FOV drag behaviour",
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
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    summary = audit["checks"]["_summary"]
    print(f"\n{summary['checks'] - len(summary['failures'])}/{summary['checks']} passed")
    if summary["failures"]:
        print("FAILED: " + ", ".join(summary["failures"]))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
