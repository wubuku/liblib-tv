#!/usr/bin/env python3
"""Verify Batch 614: the director desk's inspector column, measured against
the source's own column tree.

## How this batch was chosen

`probe613` walked every interactive element on both pages.  Among the source's
items that the clone had no counterpart for was the column itself: the source's
inspector wrapper is `absolute right-0 top-0 …` at `[1639, 0, 281, 1020]`,
while the clone's was `absolute inset-y-0` inside the middle flex child at
`[1640, 88, 280, 880]`.  Same root cause batch 613 fixed on the left.

## What the source actually is

    div.absolute.right-0.top-0.z-20.flex.w-[281px].flex-col.overflow-hidden
                                              [1639, 0, 281, 1020]
      div.flex.min-h-0.flex-1.flex-col.overflow-hidden.border.w-[281px]
         .border-y-0.border-l.border-r-0        bg rgb(33,33,33) = #212121
         border-left 1px rgba(255,255,255,0.08), other three edges 0
        div.flex.shrink-0.items-center.justify-between.h-12.px-3
                                              [1640, 0, 280, 48]
          span.text-[15px].font-medium.text-neutral-50   "摄像机"
                                              [1652, 11.9, 45, 23.3]
              font 15px/23.25px/500, color rgb(247,247,247)
                                              ← exactly ONE child
        div.min-h-0.flex-1.overflow-y-auto      [1640, 48, 280, 972]

The title band's `justify-between` with a single child puts it flush left, and
x=1652 is 1640 + the 12px `px-3`.  Both check out.

## Two historical readings this batch overturns

1. **batch 610's "源站该列没有左边框" was half wrong.**  The source has no
   border around the *column*; the column's own *panel* does carry a 1px
   `border-l` at 1639..1640.  So the column is 281 wide including that pixel
   and the content stays 280 at x=1640 — the geometry batch 610 matched, for
   a reason it had half wrong.

2. **batch 606's "右头 280px 定宽列 = 选中对象名" is superseded.**  The band it
   measured — `div.flex.shrink-0.items-center.justify-between.h-12.px-3` at
   `[1640,0,280,48]` holding one `text-[15px] font-medium text-neutral-50`
   span at `[1652,11.9,45,23.3]` — is the *inspector column's own title bar*,
   and its text is the object **kind** (「摄像机」), not the object's name
   (the name is the 名称 field further down the panel).  batch 606 read the
   element correctly and then built a separate full-width header carrying a
   second copy of it.  This batch fixes the title bar itself; the header's
   right group is left alone (it has its own 28-check contract) and the
   collision it creates is recorded below.

## Two deliberate deviations, recorded not hidden

- **`top-[52px]` instead of `top-0`.**  The source's top is 0 because its
  header is only the 280px left head, inside the left column's aside; nothing
  sits above its right column.  The clone's header is a *full-width* grid
  (batch 606) whose right group occupies `[1640,0,280,51]`, so a top-0
  inspector column would have its title bar covered end to end — a brand new
  invisible control.  52 yields the exact width, x, border, background,
  title-bar form and 1640 content origin.
- **Column runs to the viewport bottom instead of 1020.**  The source's 1020
  is content-driven (measured scrollHeight == clientHeight == 972, so it never
  scrolls; the computed `bottom: 130px` is a derived value, not a
  declaration).  The clone's camera panel content measures 1185 against the
  source's 907 — 278px more, from rows the source does not show there (可见 /
  未锁定, 当前镜头, 镜头名称).  Copying the content-driven rule verbatim would
  run the column 140px past the viewport, so it is bottom-anchored instead and
  the timeline (z-40) covers the rest — the same stacking relationship the
  source has.  The content-height difference is a separate target.

`z-30` is kept rather than the source's `z-20` because below 900px the column
is a drawer and must sit above the `z-20` mobile scrim.  The two never overlap
on desktop.

## Not claimed

- The source's inspector column has no click behaviour to record (it is a
  container); what is claimed is geometry, colour, border, typography, and
  that the clone's own tab row, fields, collapse and mobile drawer still work.
- The title band's text is a source fact **only for a selected camera**.  The
  source was not re-driven through other object kinds, so the clone's existing
  wording for those (角色 / 群众 / 角色组 / 场景物体 / Scene) is kept as-is and
  marked inference rather than invented afresh.
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
    ROOT / "docs/research/liblib-canvas-batch614-2026-10-01/runtime-audit.json"
)
SCREENSHOT = ROOT / "docs/design-references/liblib-inspector-column-614-1920.png"
VIEWPORT = {"width": 1920, "height": 1150}
MOBILE = {"width": 390, "height": 844}

# Source readings — probe614 / 614b / 614c / 614d, 2026-10-01, 1920x1150.
SOURCE_COL_X = 1639
SOURCE_COL_W = 281
SOURCE_PANEL_BG = "rgb(33, 33, 33)"
SOURCE_TITLE_W = 280
SOURCE_TITLE_H = 48
SOURCE_TITLE_TEXT_X = 1652
SOURCE_TITLE_FONT = "15px/23.25px/500"
SOURCE_TITLE_COLOR = "rgb(247, 247, 247)"
SOURCE_CONTENT_X = 1640
CLONE_COL_TOP = 52  # see "top-[52px] instead of top-0" above
HEADER_H = 52

IGNORE_CONSOLE = (
    "The attached 3D object must be a part of the scene graph",
    "webpack-hmr",
    "WebSocket",
    "Failed to load resource",
    "nextjs-dev-overlay",
    # Concurrent edits in this shared worktree, attributed by path.
    "src/components/jimeng/nodes/JimengTextNode.tsx",
    "src/components/jimeng/JimengHelpMenu.tsx",
)

DEEP_REACHABLE_JS = """() => {
  // the deepest control in the panel for the current selection.  The camera
  // panel's FOV field is its last row (source y=842 per batch 610's reading),
  // so it is the element that ends up under the timeline if the column runs
  // past it.  The panorama clear button is the one batch 95's regression
  // actually tripped on; it only exists once a panorama source is wired up,
  // so it is used when present and skipped otherwise.
  const el = document.querySelector('[data-director-panorama-clear]')
    || document.querySelector('[data-director-camera-fov-field]');
  if (!el) return {reachable: null, why: 'absent'};
  el.scrollIntoView({block: 'center'});
  const r = el.getBoundingClientRect();
  const hit = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
  return {
    reachable: !!(hit && (hit === el || el.contains(hit) || hit.contains(el))),
    box: [r.x, r.y, r.width, r.height],
    selector: el.hasAttribute('data-director-panorama-clear')
      ? 'panorama-clear' : 'camera-fov-field',
    hit: hit ? hit.tagName.toLowerCase() + ':' +
              (hit.getAttribute('aria-label') ||
               hit.getAttribute('data-director-export-trigger') || '') : null,
  };
}"""

READ = """() => {
  const at = (el) => { const r = el.getBoundingClientRect();
    return [Math.round(r.x*10)/10, Math.round(r.y*10)/10,
            Math.round(r.width*10)/10, Math.round(r.height*10)/10]; };
  const cs = (el) => getComputedStyle(el);
  const col = document.querySelector('[aria-label="属性"]');
  const panel = document.querySelector('[data-director-inspector]');
  const header = panel ? panel.querySelector('header') : null;
  const pc = panel ? cs(panel) : null;
  const hk = header ? Array.from(header.children).map((k) => {
    const s = cs(k);
    return {tag: k.tagName.toLowerCase(), box: at(k),
            text: (k.textContent || '').trim(),
            font: s.fontSize + '/' + s.lineHeight + '/' + s.fontWeight,
            color: s.color};
  }) : [];
  const scroller = (() => {
    for (const el of panel.querySelectorAll('*')) {
      if (/(auto|scroll)/.test(cs(el).overflowY)) return el;
    }
    return null;
  })();
  const firstField = panel.querySelector(
    '[data-director-object-name], input[type="text"], select');
  // `canvas` alone matches the 240x135 camera-preview canvas first; the
  // scene canvas is the one carrying data-engine.
  const canvas = document.querySelector('canvas[data-engine]')
    || Array.from(document.querySelectorAll('canvas')).find(
         (c) => c.getBoundingClientRect().width > 600);
  const main = document.querySelector('[data-director-workspace] main');
  return {
    col: col ? {box: at(col), z: cs(col).zIndex, overflow: cs(col).overflow,
                 hidden: col.getAttribute('aria-hidden')} : null,
    panel: panel ? {box: at(panel), bg: pc.backgroundColor,
      bl: pc.borderLeftWidth, blc: pc.borderLeftColor,
      br: pc.borderRightWidth, bt: pc.borderTopWidth, bb: pc.borderBottomWidth,
      kind: panel.getAttribute('data-director-inspector-kind')} : null,
    header: header ? {box: at(header), bb: cs(header).borderBottomWidth,
                      justify: cs(header).justifyContent, kids: hk} : null,
    scroller: scroller ? {box: at(scroller), clientH: scroller.clientHeight,
                          scrollH: scroller.scrollHeight} : null,
    firstField: firstField ? at(firstField) : null,
    main: main ? at(main) : null,
    canvas: canvas ? at(canvas) : null,
  };
}"""


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


def near(got: float, want: float, tol: float = 0.6) -> bool:
    return abs(got - want) <= tol


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
        self.page.mouse.move(900, 600)
        self.page.wait_for_timeout(150)
        return self.page.evaluate(READ)


def open_desk(page: Page, select_camera: bool = True) -> None:
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__libtv_ui_store "
        "&& window.__director_store)",
        timeout=60_000,
    )
    page.evaluate(
        """() => {
          const s = window.__libtv_store.getState();
          s.addNode("script-execution", { title: "Batch 614" });
          const node = s.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState()
            .openDirectorDesk(node.id, s.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible", timeout=30_000)
    if select_camera:
        # must run AFTER the desk mounts — openDirectorDesk resets selection
        page.evaluate(
            """() => {
              const d = window.__director_store.getState();
              const cam = d.objects.find((o) => o.kind === 'camera');
              if (cam) d.selectObject(cam.id);
            }"""
        )
    page.wait_for_timeout(1_500)


def run_desktop(page: Page) -> dict[str, Any]:
    v = Verifier(page)
    console: list[str] = []
    errors: list[str] = []
    page.on("console", lambda m: console.append(f"{m.type}: {m.text}"[:200])
            if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)[:200]))
    open_desk(page)

    r = v.read()
    v.result["desk"] = r

    # --- 1) the column ---------------------------------------------------
    col = r["col"]
    v.check("col:present", col is not None)
    if col:
        b = col["box"]
        v.check("col:x-1639", near(b[0], SOURCE_COL_X), detail=b[0])
        v.check("col:w-281", near(b[2], SOURCE_COL_W), detail=b[2])
        v.check("col:right-edge-flush", near(b[0] + b[2], VIEWPORT["width"]),
                detail=b[0] + b[2])
        v.check("col:top-52-not-0 (documented deviation)",
                near(b[1], CLONE_COL_TOP), detail=b[1])
        # the column's bottom is the timeline's top — the same relationship
        # the source's 1020/1021 has.  Running it to the viewport bottom was
        # tried and reverted: the clone's timeline is 52px taller than the
        # source's (182 vs 130), so a full-height column let the timeline
        # cover the panel's lower content and `data-director-panorama-clear`
        # became unclickable (caught by the batch 95 regression).
        tl = page.locator("[data-director-timeline]")
        tl_top = tl.bounding_box()["y"] if tl.count() else None
        v.check("col:bottom-stops-at-the-timeline",
                tl_top is not None and near(b[1] + b[3], tl_top),
                detail=f"{b[1] + b[3]} vs timeline {tl_top}")
        v.check("col:overflow-hidden", col["overflow"] == "hidden", detail=col["overflow"])
        v.check("col:z-30-above-the-mobile-scrim", col["z"] == "30", detail=col["z"])

    # --- 2) the panel: background + the single left border ---------------
    panel = r["panel"]
    v.check("panel:present", panel is not None)
    if panel:
        v.check("panel:bg-212121", panel["bg"] == SOURCE_PANEL_BG, detail=panel["bg"])
        v.check("panel:border-left-1px-white-8",
                panel["bl"] == "1px"
                and abs(alpha_of(panel["blc"]) - 0.08) < 0.001,
                detail=f"{panel['bl']} {panel['blc']}")
        v.check("panel:other-three-edges-0",
                panel["br"] == "0px" and panel["bt"] == "0px"
                and panel["bb"] == "0px",
                detail=f"{panel['bt']}/{panel['br']}/{panel['bb']}")
        # the panel is a border-box: it spans 1639..1920 including its 1px
        # left border, exactly like the source's [1639,0,281,1020]
        v.check("panel:border-box-starts-at-1639",
                near(panel["box"][0], SOURCE_COL_X), detail=panel["box"][0])
        v.check("panel:width-281-border-box", near(panel["box"][2], SOURCE_COL_W),
                detail=panel["box"][2])

    # --- 3) the title bar ------------------------------------------------
    h = r["header"]
    v.check("title:present", h is not None)
    if h:
        b = h["box"]
        v.check("title:280x48", near(b[2], SOURCE_TITLE_W) and near(b[3], SOURCE_TITLE_H),
                detail=b)
        v.check("title:no-border-b", h["bb"] == "0px", detail=h["bb"])
        v.check("title:justify-between", h["justify"] == "space-between",
                detail=h["justify"])
        v.check("title:exactly-one-child", len(h["kids"]) == 1,
                detail=[k["tag"] for k in h["kids"]])
        if h["kids"]:
            k = h["kids"][0]
            v.check("title:text-x-1652", near(k["box"][0], SOURCE_TITLE_TEXT_X),
                    detail=k["box"][0])
            v.check("title:font-15-23.25-500", k["font"] == SOURCE_TITLE_FONT,
                    detail=k["font"])
            v.check("title:color-neutral-50", k["color"] == SOURCE_TITLE_COLOR,
                    detail=k["color"])
            v.check("title:shows-the-object-kind", k["text"] == "摄像机", detail=k["text"])
            v.check("title:not-the-old-generic-label", k["text"] != "对象属性")

    # --- 4) content origin: batch 610's 248-wide fields still land right --
    if r["firstField"]:
        v.check("content:first-field-at-1656", near(r["firstField"][0], 1656),
                detail=r["firstField"])
    v.check("content:scroller-inside-the-column",
            r["scroller"] is not None
            and r["scroller"]["box"][0] == SOURCE_CONTENT_X
            and r["scroller"]["box"][1] >= CLONE_COL_TOP,
            detail=r["scroller"])

    # --- 5) the viewport frame lines up with the two columns -------------
    main = r["main"]
    v.check("viewport:frame-left-281", main is not None and near(main[0], 281),
            detail=main)
    v.check("viewport:frame-right-281",
            main is not None and near(main[0] + main[2], SOURCE_COL_X),
            detail=main)
    cv = r["canvas"]
    v.check("viewport:canvas-left-281", cv is not None and near(cv[0], 281), detail=cv)
    v.check("viewport:canvas-right-edge-1639",
            cv is not None and near(cv[0] + cv[2], SOURCE_COL_X), detail=cv)
    v.check("viewport:one-webgl-canvas", cv is not None, detail=cv)

    # The regression this column's bottom bound exists to prevent: a control
    # deep in the panel must remain clickable, i.e. not buried under the
    # timeline once scrolled into view.
    deep = page.evaluate(DEEP_REACHABLE_JS)
    v.check("panel:deep-content-stays-reachable", deep["reachable"] is True,
            detail=deep)
    page.screenshot(path=str(SCREENSHOT))

    # --- 6) collapse keeps the right column, frees only the left ---------
    page.locator("[data-director-panels-toggle]").click()
    page.wait_for_timeout(600)
    col_r = v.read()
    v.result["collapsed"] = col_r
    v.check("collapse:inspector-stays", col_r["col"] is not None
            and near(col_r["col"]["box"][0], SOURCE_COL_X),
            detail=col_r["col"])
    v.check("collapse:viewport-frees-only-the-tree-width",
            col_r["main"] is not None and near(col_r["main"][0], 48),
            detail=col_r["main"])
    page.locator('[data-director-icon-rail] [aria-label="场景"]').click()
    page.wait_for_timeout(600)
    back = v.read()
    v.check("restore:viewport-left-281-again",
            back["main"] is not None and near(back["main"][0], 281), detail=back["main"])
    v.check("restore:column-geometry-unchanged",
            back["col"] is not None and near(back["col"]["box"][2], SOURCE_COL_W),
            detail=back["col"])

    # --- 7) the column's own tab row and fields still work ----------------
    for tab in ("motion", "captures", "properties"):
        page.locator(f'[data-director-camera-tab="{tab}"]').click()
        page.wait_for_timeout(400)
        v.check(f"tab:{tab}-activates",
                page.locator(f'[data-director-camera-tab="{tab}"]')
                .get_attribute("aria-pressed") == "true")
    v.check("tab:properties-renders-the-fields",
            page.locator("[data-director-object-name]").count() == 1
            and page.locator("[data-director-transform-field]").count() >= 3,
            detail={
                "name": page.locator("[data-director-object-name]").count(),
                "fields": page.locator("[data-director-transform-field]").count(),
            })
    after_tabs = v.read()
    v.check("tab:title-back-to-摄像机",
            (after_tabs["header"] or {}).get("kids", [{}])[0].get("text") == "摄像机",
            detail=(after_tabs["header"] or {}).get("kids"))

    noise = [c for c in console if any(k in c for k in IGNORE_CONSOLE)]
    real_console = [c for c in console if not any(k in c for k in IGNORE_CONSOLE)]
    real_errors = [e for e in errors if not any(k in e for k in IGNORE_CONSOLE)]
    v.check("diagnostics:no-page-errors", not real_errors, detail=real_errors[:5])
    v.check("diagnostics:no-console-errors", not real_console, detail=real_console[:5])
    v.result["diagnostics"] = {"consoleErrors": len(console),
                                "filtered": len(noise),
                                "pageErrors": len(errors)}
    v.result["_summary"] = {"checks": v.count, "failures": v.failures}
    return v.result


def run_mobile(page: Page) -> dict[str, Any]:
    v = Verifier(page)
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)[:200]))
    open_desk(page, select_camera=False)
    col = page.locator('[aria-label="属性"]')
    v.check("mobile:inspector-starts-off-screen",
            col.bounding_box() is not None
            and col.bounding_box()["x"] >= MOBILE["width"] - 1,
            detail=col.bounding_box())
    # the mobile drawer triggers live in their own
    # `div.absolute.left-3.top-3.z-10.hidden.gap-1.max-[899px]:flex`, not in
    # the bottom pill (`data-director-viewport-toolbar` is that pill)
    page.locator('[aria-label="打开属性面板"]').first.click()
    page.wait_for_timeout(500)
    # the drawer is `right-0` and 281 wide, so on a 390px viewport it opens
    # flush to the right edge at x=109 — fully on screen, not "near 0"
    bb = col.bounding_box()
    v.check("mobile:drawer-opens-flush-right",
            bb is not None
            and near(bb["x"] + bb["width"], MOBILE["width"])
            and near(bb["width"], SOURCE_COL_W),
            detail=bb)
    v.check("mobile:drawer-starts-below-the-header",
            bb is not None and near(bb["y"], CLONE_COL_TOP), detail=bb)
    v.check("mobile:drawer-above-the-scrim",
            col.evaluate("el => parseInt(getComputedStyle(el).zIndex, 10) >= 20"))
    v.check("mobile:no-page-errors", not errors, detail=errors[:3])
    v.result["_summary"] = {"checks": v.count, "failures": v.failures}
    return v.result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 614,
        "title": "Director desk inspector column: frame, panel chrome and title bar",
        "date": "2026-10-01",
        "sourceEvidence": [
            "probe614: the column wrapper and everything under it, on both sides",
            "probe614b: scrollHeight vs clientHeight — the source's 1020 is "
            "content-driven, not viewport-anchored (the computed "
            "bottom:130px is a derived value)",
            "probe614c: direct children of the scrolling content, which "
            "attributes the 278px content-height gap",
            "probe614d: the panel's resolved border-left colour and the "
            "title bar's child count and computed font",
            "probe614e: the 3D canvas box on both sides",
        ],
        "claims": {
            "sourceFact": [
                "column: div.absolute.right-0.top-0.z-20.flex.w-[281px]"
                ".flex-col.overflow-hidden at [1639,0,281,1020]",
                "panel: bg rgb(33,33,33) = #212121, border-left "
                "1px rgba(255,255,255,0.08), the other three edges 0",
                "title bar: div.flex.shrink-0.items-center.justify-between"
                ".h-12.px-3 at [1640,0,280,48], no border-b, exactly one "
                "child — span.text-[15px].font-medium.text-neutral-50 "
                "reading 摄像机 at [1652,11.9,45,23.3], computed "
                "15px/23.25px/500 rgb(247,247,247)",
                "the title band is the inspector's own title bar, so "
                "batch 606's '右头 = 选中对象名' reading is superseded: the "
                "text is the object kind, and the name lives in the 名称 field",
                "the source's 3D canvas is full-bleed [0,0,1920,1150]",
            ],
            "overturnedReadings": [
                "batch 610's '源站该列没有左边框' was half wrong — the column "
                "has none, but the panel inside it has a 1px border-l at "
                "1639..1640, so the column is 281 wide including that pixel",
            ],
            "cloneDecision": [
                "the column is anchored at top-52 rather than the source's "
                "top-0, because the clone's header is full-width (batch 606) "
                "and its right group occupies [1640,0,280,51]; a top-0 "
                "column would have its title bar covered end to end",
                "the column runs to the viewport bottom instead of the "
                "source's content-driven 1020, because the clone's camera "
                "panel content measures 1185 against the source's 907",
                "z-30 is kept over the source's z-20 so the mobile drawer "
                "clears the z-20 scrim; the two never overlap on desktop",
            ],
            "notClaimed": [
                "the title band's text for object kinds other than a camera — "
                "the source was not re-driven, so the clone's existing wording "
                "is kept rather than invented",
                "the 278px content-height difference (extra rows the source "
                "does not show: 可见/未锁定, 当前镜头, 镜头名称) — separate target",
                "the source's full-bleed 3D canvas vs the clone's inset "
                "viewport frame — measured and recorded, separate target",
            ],
        },
    }
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport=VIEWPORT)
        page = ctx.new_page()
        desktop = run_desktop(page)
        mctx = browser.new_context(viewport=MOBILE)
        mobile = run_mobile(mctx.new_page())
        browser.close()
    total = (desktop["_summary"]["checks"] + mobile["_summary"]["checks"])
    fails = desktop["_summary"]["failures"] + mobile["_summary"]["failures"]
    audit["checks"] = {"desktop": desktop, "mobile": mobile}
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
