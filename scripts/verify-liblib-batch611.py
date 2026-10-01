#!/usr/bin/env python3
"""Verify Batch 611: the sticky camera preview thumbnail in the 属性 panel.

## What the source shows (measured 2026-10-01, 1920x1150, probe66 + crop)

Right under the tab strip the source's inspector opens with a **sticky preview
thumbnail**:

```
section [1640,105,280,168]
  sticky top-0 z-20 border-b border-white/8 bg-[rgba(33,33,33,0.98)] px-4 py-4
  shadow-[0_8px_18px_rgba(0,0,0,0.18)] backdrop-blur-md
  div [1656,121,240,135]  relative overflow-hidden rounded-xl border
                          bg rgba(8,8,16,0.95)
    canvas [1657,122,240,135]
    div  [1669,134,51.3,13] pointer-events-none absolute left-3 top-3
                            text-[13px] leading-none text-white/55  -> "FOV 50°"
    button [1859,219,24,24] hover:bg-white/16 absolute bottom-3 right-3
                            flex size-6 items-center justify-center
                            rounded-lg bg-white/10 text-white/85
                            14x14 svg (two outward diagonal arrows)
```

The crop is decisive about *what* the canvas holds: it is a **real 3D render
from that camera's viewpoint** — the grid floor, the horizon and the character
at the table are all there.  It is not a schematic, a poster frame or a
placeholder.

## What the clone was missing

Nothing — the clone had no preview block at all, and the `FOV n°` text that the
source shows here (batch 581 mistook that badge for a control) had nowhere to
live.

## What this batch does — and deliberately does not fake

A 2D mock of the framing would be exactly the kind of control that looks
usable and silently lies, so this batch renders for real: a component **inside
the viewport's existing WebGL context** renders the same `scene` through a
temporary `PerspectiveCamera` placed by the selected camera's transform / FOV
into a `WebGLRenderTarget`, reads the pixels back, and blits them into the
panel's 2D canvas.  No second WebGL context is created, so the main canvas and
the `captureStream(30)` export path are untouched.

`readRenderTargetPixels` is a synchronous read-back and stalls the pipeline, so
the pass only runs when a **signature** changes: the camera's placement, the
look-at mode, the follow target, the playhead time, and the transform /
visibility of every object in the scene.  A still panel costs nothing.

The 24x24 button's *click behaviour was never measured on the source* (clicking
a source control writes to the real project, which needs authorisation).  Its
geometry and icon are measured; here it reuses the already-verified
`selectShot` + `setViewMode` pair to frame the selected camera, which is an
inference from the icon and the accessible name.

## Not claimed

- the source's expand-button click behaviour;
- that the clone's preview is pixel-identical to the source's — it is the same
  scene and the same camera math through a 240x135 buffer, not a byte match;
- the 相机截图 grid under it, whose item shape was unmeasurable (the source's
  grid measured 0 tall — no captures in that project).
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
    ROOT / "docs/research/liblib-canvas-batch611-2026-10-01/runtime-audit.json"
)
SCREENSHOT = ROOT / "docs/design-references/liblib-camera-preview-611-1920.png"
CLOSEUP = ROOT / "docs/design-references/liblib-camera-preview-611-closeup.png"

VIEWPORT = {"width": 1920, "height": 1150}

SECTION_W = 280
SECTION_H = 168
BOX_W = 240
BOX_H = 135
BOX_X = 1656
BADGE_W = 16
EXPAND = 24
ICON = 14

IGNORE_CONSOLE = (
    "The attached 3D object must be a part of the scene graph",
    "webpack-hmr",
    "WebSocket",
    "Failed to load resource",
    # Another developer is editing src/components/jimeng/nodes/
    # JimengTextNode.tsx in this shared worktree; a half-written block comment
    # surfaces through HMR as a page/console error that has nothing to do with
    # this batch.  Matched by path so a real error in *our* files still fails.
    "src/components/jimeng/nodes/JimengTextNode.tsx",
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


READ = """() => {
  const at = (el) => { const r = el.getBoundingClientRect();
    return [Math.round(r.x*10)/10, Math.round(r.y*10)/10,
            Math.round(r.width*10)/10, Math.round(r.height*10)/10]; };
  const cs = (el) => getComputedStyle(el);
  const section = document.querySelector('[data-director-camera-preview]');
  const canvas = document.querySelector('[data-director-camera-preview-canvas]');
  const fov = document.querySelector('[data-director-camera-preview-fov]');
  const expand = document.querySelector('[data-director-camera-preview-expand]');
  const box = canvas?.parentElement ?? null;
  // A cheap fingerprint of the painted pixels: sampled luminance mean plus a
  // coarse 8x6 luma grid, so "did the render change" is answerable cheaply.
  let paint = null;
  if (canvas) {
    const ctx = canvas.getContext('2d');
    const img = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
    let min = 255, max = 0, sum = 0, n = 0, bright = 0;
    for (let i = 0; i < img.length; i += 4) {
      const lum = (img[i] + img[i+1] + img[i+2]) / 3;
      if (lum < min) min = lum;
      if (lum > max) max = lum;
      sum += lum; n += 1;
      if (lum > 40) bright += 1;
    }
    const grid = [];
    for (let gy = 0; gy < 6; gy += 1) {
      let row = '';
      for (let gx = 0; gx < 8; gx += 1) {
        const x0 = Math.floor((gx * canvas.width) / 8);
        const y0 = Math.floor((gy * canvas.height) / 6);
        const x1 = Math.floor(((gx + 1) * canvas.width) / 8);
        const y1 = Math.floor(((gy + 1) * canvas.height) / 6);
        let acc = 0, cnt = 0;
        for (let y = y0; y < y1; y += 4) {
          for (let x = x0; x < x1; x += 4) {
            const o = (y * canvas.width + x) * 4;
            acc += (img[o] + img[o+1] + img[o+2]) / 3; cnt += 1;
          }
        }
        row += String(Math.round(acc / Math.max(cnt, 1))).padStart(3, '0');
      }
      grid.push(row);
    }
    paint = {w: canvas.width, h: canvas.height,
             min: Math.round(min), max: Math.round(max),
             mean: Math.round(sum / n),
             brightFraction: +(bright / n).toFixed(4), grid};
  }
  // How many canvases in the page actually hold a WebGL context?
  let webglCanvases = 0;
  for (const c of document.querySelectorAll('canvas')) {
    if (c.getContext('webgl2') || c.getContext('webgl')) webglCanvases += 1;
  }
  const main = document.querySelector('[data-director-webgl-canvas] canvas');
  let mainPainted = null;
  if (main) {
    // The main canvas has preserveDrawingBuffer, so toDataURL works.
    mainPainted = main.width * main.height;
  }
  const state = window.__director_store.getState();
  const selected = state.objects.find((o) => o.id === state.selectedObjectIds[0]);
  return {
    section: section ? {box: at(section), position: cs(section).position,
      zIndex: cs(section).zIndex, bg: cs(section).backgroundColor,
      borderBottom: cs(section).borderBottomWidth + ' ' + cs(section).borderBottomColor,
      pad: cs(section).padding, shadow: cs(section).boxShadow,
      backdrop: cs(section).backdropFilter} : null,
    box: box ? {box: at(box), radius: cs(box).borderRadius,
      overflow: cs(box).overflow, border: cs(box).borderTopWidth,
      bg: cs(box).backgroundColor} : null,
    canvas: canvas ? {box: at(canvas), w: canvas.width, h: canvas.height} : null,
    fov: fov ? {box: at(fov), text: (fov.textContent||'').trim(),
      pos: cs(fov).position, font: cs(fov).fontSize + '/' + cs(fov).lineHeight,
      color: cs(fov).color, pointerEvents: cs(fov).pointerEvents} : null,
    expand: expand ? {box: at(expand), pos: cs(expand).position,
      radius: cs(expand).borderRadius, bg: cs(expand).backgroundColor,
      color: cs(expand).color, aria: expand.getAttribute('aria-label'),
      svg: (() => { const s = expand.querySelector('svg'); return s ? at(s) : null; })(),
      cursor: cs(expand).cursor} : null,
    paint,
    webglCanvases,
    mainCanvas: main ? {box: at(main), pixels: mainPainted} : null,
    viewMode: state.viewMode,
    activeCameraId: state.activeCameraId,
    fovValue: selected?.camera ? selected.camera.fov : null,
    selectedKind: selected?.kind ?? null,
    selectedId: selected?.id ?? null,
    position: selected ? selected.transform.position.slice() : null,
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
        self.page.mouse.move(5, 5)
        self.page.wait_for_timeout(150)
        return self.page.evaluate(READ)


def box_is(box: list[float] | None, x=None, y=None, w=None, h=None) -> bool:
    if box is None:
        return False
    return (
        (x is None or abs(box[0] - x) <= 0.6)
        and (y is None or abs(box[1] - y) <= 0.6)
        and (w is None or abs(box[2] - w) <= 0.6)
        and (h is None or abs(box[3] - h) <= 0.6)
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
          store.addNode("script-execution", { title: "Batch 611 probe" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible", timeout=30_000)
    page.wait_for_timeout(1_500)

    # No camera selected -> no preview at all.
    empty = v.read()
    v.check("absent:without-camera", empty["section"] is None, detail=empty["selectedKind"])
    # The clone already runs TWO WebGL contexts (the viewport scene and the
    # corner orientation-axis gizmo), so the meaningful assertion is that the
    # preview adds none — a before/after comparison, not an absolute count.
    baseline_contexts = empty["webglCanvases"]
    v.result["baseline_webgl_contexts"] = baseline_contexts
    v.check("webgl:baseline-recorded", baseline_contexts >= 1,
            detail=baseline_contexts)

    page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          s.selectObject(s.objects.find((o) => o.kind === 'camera').id);
        }"""
    )
    page.locator("[data-director-camera-preview]").wait_for(state="visible")
    page.wait_for_timeout(2_500)
    r = v.read()
    v.result["initial"] = r

    # --- section --------------------------------------------------------
    sec = r["section"]
    v.check("section:280x168", box_is(sec["box"], w=SECTION_W, h=SECTION_H), detail=sec["box"])
    v.check("section:sticky", sec["position"] == "sticky", detail=sec["position"])
    v.check("section:z-20", sec["zIndex"] == "20", detail=sec["zIndex"])
    v.check("section:fill-212121-98",
            sec["bg"] == "rgba(33, 33, 33, 0.98)", detail=sec["bg"])
    v.check("section:border-b-1px-white-8",
            sec["borderBottom"].startswith("1px")
            and abs(alpha_of(sec["borderBottom"].split(" ", 1)[1]) - 0.08) < 0.005,
            detail=sec["borderBottom"])
    v.check("section:pad-16", sec["pad"] in ("16px", "0px 16px"), detail=sec["pad"])
    v.check("section:backdrop-blur", "blur" in sec["backdrop"], detail=sec["backdrop"])
    v.check("section:has-shadow", "rgba(0, 0, 0, 0.18)" in sec["shadow"],
            detail=sec["shadow"][:70])

    # --- preview box ----------------------------------------------------
    bx = r["box"]
    v.check("box:240x135", box_is(bx["box"], w=BOX_W, h=BOX_H), detail=bx["box"])
    v.check("box:x-1656", box_is(bx["box"], x=BOX_X), detail=bx["box"])
    v.check("box:radius-12", bx["radius"] == "12px", detail=bx["radius"])
    v.check("box:overflow-hidden", bx["overflow"] == "hidden", detail=bx["overflow"])
    v.check("box:1px-border", bx["border"] == "1px", detail=bx["border"])
    v.check("box:fill-080810", bx["bg"] == "rgba(8, 8, 16, 0.95)", detail=bx["bg"])

    # --- canvas ---------------------------------------------------------
    cv = r["canvas"]
    v.check("canvas:240x135-backing-store", cv["w"] == 240 and cv["h"] == 135, detail=cv)
    v.check("canvas:sits-inside-the-border",
            box_is(cv["box"], x=BOX_X + 1, y=bx["box"][1] + 1, w=BOX_W, h=BOX_H),
            detail=cv["box"])

    # --- it is a real render, not a fill --------------------------------
    paint = r["paint"]
    v.check("paint:has-contrast", paint["max"] - paint["min"] > 40,
            detail={"min": paint["min"], "max": paint["max"]})
    v.check("paint:not-near-black", paint["mean"] > 12, detail=paint["mean"])
    v.check("paint:not-near-white", paint["mean"] < 200, detail=paint["mean"])
    v.check("paint:mixed-content", 0.02 < paint["brightFraction"] < 0.95,
            detail=paint["brightFraction"])
    rows = set(paint["grid"])
    v.check("paint:many-distinct-regions", len(rows) >= 3, detail=len(rows))

    # --- FOV badge ------------------------------------------------------
    fov = r["fov"]
    v.check("fov-badge:absolute", fov["pos"] == "absolute", detail=fov["pos"])
    # left-3/top-3 are 12px, measured from the *padding* box (border box + 1px
    # border): source badge [1669,134] against box [1656,121] = 1657+12 / 122+12.
    pad_x = bx["box"][0] + 1
    pad_y = bx["box"][1] + 1
    pad_right = pad_x + BOX_W - 2
    pad_bottom = pad_y + BOX_H - 2
    v.check("fov-badge:left-3-top-3",
            abs(fov["box"][0] - (pad_x + 12)) <= 0.6
            and abs(fov["box"][1] - (pad_y + 12)) <= 0.6,
            detail={"badge": fov["box"], "expected": [pad_x + 12, pad_y + 12]})
    v.check("fov-badge:13px/13px", fov["font"] == "13px/13px", detail=fov["font"])
    v.check("fov-badge:white-55", abs(alpha_of(fov["color"]) - 0.55) < 0.01,
            detail=fov["color"])
    v.check("fov-badge:untargetable", fov["pointerEvents"] == "none",
            detail=fov["pointerEvents"])
    v.check("fov-badge:text-follows-store", fov["text"] == f"FOV {r['fovValue']}°",
            detail=f"{fov['text']} vs {r['fovValue']}")
    page.screenshot(path=str(SCREENSHOT))
    page.locator("[data-director-camera-preview]").screenshot(path=str(CLOSEUP))

    # --- expand button --------------------------------------------------
    ex = r["expand"]
    v.check("expand:24x24", box_is(ex["box"], w=EXPAND, h=EXPAND), detail=ex["box"])
    v.check("expand:absolute", ex["pos"] == "absolute", detail=ex["pos"])
    v.check("expand:right-3-bottom-3",
            abs(ex["box"][0] - (pad_right - 12 - EXPAND)) <= 0.6
            and abs(ex["box"][1] - (pad_bottom - 12 - EXPAND)) <= 0.6,
            detail={"btn": ex["box"],
                    "expected": [pad_right - 12 - EXPAND, pad_bottom - 12 - EXPAND]})
    v.check("expand:radius-8", ex["radius"] == "8px", detail=ex["radius"])
    v.check("expand:fill-white-10", abs(alpha_of(ex["bg"]) - 0.10) < 0.005, detail=ex["bg"])
    v.check("expand:icon-white-85", abs(alpha_of(ex["color"]) - 0.85) < 0.01,
            detail=ex["color"])
    v.check("expand:icon-14", box_is(ex["svg"], w=ICON, h=ICON), detail=ex["svg"])
    v.check("expand:accessible-name", ex["aria"] == "切换到机位视角", detail=ex["aria"])

    # --- it lives in ONE WebGL context ---------------------------------
    v.check("webgl:preview-adds-no-context",
            r["webglCanvases"] == baseline_contexts,
            detail={"baseline": baseline_contexts, "now": r["webglCanvases"]})
    v.check("main-canvas:alive", r["mainCanvas"] is not None
            and r["mainCanvas"]["pixels"] > 0, detail=r["mainCanvas"])

    # --- the render is live: move the camera, the pixels change ---------
    before = v.read()["paint"]["grid"]
    page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          const c = s.objects.find((o) => o.id === s.selectedObjectIds[0]);
          s.updateObjectTransform(c.id, 'position', 0, 9.5);
        }"""
    )
    page.wait_for_timeout(1_200)
    after = v.read()["paint"]["grid"]
    v.check("live:repaints-when-camera-moves", before != after,
            detail={"before": before[:2], "after": after[:2]})

    # ... and follows the camera's FOV too.
    fov_before = v.read()["fov"]["text"]
    page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          s.updateCamera(s.selectedObjectIds[0], { fov: 70 });
        }"""
    )
    page.wait_for_timeout(800)
    fov_after = v.read()
    v.check("live:fov-badge-follows", fov_after["fov"]["text"] == "FOV 70°",
            detail=f"{fov_before} -> {fov_after['fov']['text']}")
    page.evaluate(
        """() => window.__director_store.getState().updateCamera(
             window.__director_store.getState().selectedObjectIds[0], { fov: 43 })"""
    )
    page.wait_for_timeout(600)

    # --- the expand button frames the camera -----------------------------
    v.check("expand:starts-in-director-view", v.read()["viewMode"] == "director")
    page.locator("[data-director-camera-preview-expand]").click()
    page.wait_for_timeout(600)
    framed = v.read()
    v.check("expand:switches-to-camera-view", framed["viewMode"] == "camera",
            detail=framed["viewMode"])
    v.check("expand:activates-this-camera",
            framed["activeCameraId"] == framed["selectedId"],
            detail=f"{framed['activeCameraId']} vs {framed['selectedId']}")
    page.locator('[data-director-view-mode="director"]').click()
    page.wait_for_timeout(500)
    v.check("expand:reversible",
            v.read()["viewMode"] == "director")

    # --- deselecting a camera removes the block -------------------------
    page.evaluate("() => window.__director_store.getState().selectObject(null)")
    page.wait_for_timeout(600)
    v.check("absent:deselected", v.read()["section"] is None)
    v.check("webgl:contexts-back-to-baseline",
            v.read()["webglCanvases"] == baseline_contexts,
            detail=v.read()["webglCanvases"])

    page.wait_for_timeout(300)

    def attributable(text: str) -> bool:
        return any(k in text for k in IGNORE_CONSOLE)

    noise = [c for c in console if attributable(c)]
    real_console = [c for c in console if not attributable(c)]
    error_noise = [e for e in errors if attributable(e)]
    real_errors = [e for e in errors if not attributable(e)]
    v.check("diagnostics:no-page-errors", not real_errors, detail=real_errors[:5])
    v.check("diagnostics:no-console-errors", not real_console, detail=real_console[:5])
    v.result["diagnostics"] = {
        "consoleErrors": len(console),
        "filtered": len(noise),
        "pageErrors": len(errors),
        "pageErrorsFiltered": len(error_noise),
    }
    v.result["_summary"] = {"checks": v.count, "failures": v.failures}
    return v.result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 611,
        "title": "Sticky camera preview thumbnail in the 属性 panel (real offscreen render)",
        "date": "2026-10-01",
        "sourceEvidence": [
            "probe66 subtree dump of the source inspector",
            "crop of the source 2x screenshot proving the 240x135 canvas holds a "
            "real 3D render (grid floor, horizon, character at a table)",
        ],
        "claims": {
            "sourceFact": [
                "section 280x168 sticky top-0 z-20 border-b border-white/8 "
                "bg-[rgba(33,33,33,0.98)] px-4 py-4 "
                "shadow-[0_8px_18px_rgba(0,0,0,0.18)] backdrop-blur-md",
                "preview box 240x135 at x=1656, rounded-xl, overflow-hidden, "
                "1px border, bg rgba(8,8,16,0.95)",
                "canvas 240x135 starting 1px inside the box (the border sits on "
                "top of it and is clipped)",
                "FOV badge: absolute left-3 top-3, 13px/13px, text-white/55, "
                "text 'FOV n°', pointer-events-none",
                "expand button: 24x24 absolute bottom-3 right-3, rounded-lg, "
                "bg-white/10, text-white/85, 14x14 two-arrow icon, accessible "
                "name 切换到机位视角",
                "the canvas holds a real 3D render of the scene from that camera",
            ],
            "cloneDecision": [
                "rendered through a WebGLRenderTarget inside the viewport's "
                "existing context — a 2D mock would have been a control that "
                "looks usable and lies",
                "the clone already runs two WebGL contexts (scene + gizmo); the "
        "preview adds none",
        "read-back is gated on a signature (camera placement, look-at "
                "mode, follow target, playhead time, every object's transform "
                "and visibility) because readRenderTargetPixels stalls the "
                "pipeline",
            ],
            "inference": [
                "the expand button frames the selected camera (selectShot + "
                "setViewMode); the source's click behaviour was never measured",
            ],
            "notClaimed": [
                "pixel-identity with the source's preview",
                "the 相机截图 grid below it — the source's grid measured 0 tall "
                "(no captures in that project), so the item shape is unmeasurable",
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
