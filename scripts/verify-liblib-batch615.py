#!/usr/bin/env python3
"""Verify Batch 615: the header's 收起 button is clickable at narrow widths.

## The defect

Batch 94's mobile leg had been red for the whole session:

    Locator.click: Timeout 30000ms exceeded — waiting for
      locator("[data-director-panels-toggle]")
      … 56 × waiting for element to be visible, enabled and stable
        - <div class="flex h-9 w-[170px] …"> from
          <div role="group" aria-label="导演台视角"
               class="pointer-events-auto absolute left-1/2 top-2 z-10
                      -translate-x-1/2"> subtree intercepts pointer events

A control that is drawn but cannot be clicked is the same class of defect as
batch 604's swallowed prompt capsule and batch 611's export panel buried under
the inspector's field rows.  A baseline comparison (`cp` to /tmp +
`git checkout --`, never stash) confirmed the failure predates batches
613/614, so it is a pre-existing hole rather than collateral from this run.

## The geometry

The view-mode switcher is `absolute left-1/2 top-2 z-10 -translate-x-1/2` with
a **fixed 170px** inner row.  Being absolutely positioned, it ignores the
header's `grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)]` entirely and simply
sits over the middle.  At 390px:

    header          [0,   0, 390, 52]
    left column     [0,   0, 147.5, 51]     ← minmax(0,1fr) of (390-95)/2
      关闭           [8,   5.5, 40, 40]
      收起           [99.5, 5.5, 40, 40]     ← right half under the switcher
    switcher        [110, 8, 170, 36]       ← 195 ± 85
    right column    [242.5, 0, 147.5, 51]

The switcher's left edge (110) lands 10.5px inside 收起, so the button's centre
(119.5) is covered.

## The fix

Cap the left column at the switcher's left edge on narrow screens:
`max-w-[calc(50vw-85px)]`, where 85 is half of the switcher's fixed 170px.  At
390 the column becomes 110 wide and 收起 lands at 62..102, clear of the
switcher.  At ≥900px `50vw − 85 ≥ 395 > 280`, so the cap never engages and the
source's fixed 280px left head is untouched — batch 606's 28 checks, which
pin the desktop header down to `关闭 @(0,5.5)` / `收起 @(240,5.5)`, stay green.

## What is NOT claimed

The source's header at this width is unmeasured.  `probe615b` opened a
throwaway tab at 390×844 with a device-metrics override applied to that tab
only (the shared session's existing tab was never touched, and no clicks were
issued); it lands on the **canvas** page, because the director desk needs a
click to open.  So nothing is claimed about what the source does on a phone —
this batch removes a control that cannot be clicked, and leaves every source
reading at the desktop widths where readings exist.
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
    ROOT / "docs/research/liblib-canvas-batch615-2026-10-01/runtime-audit.json"
)
SCREENSHOT = ROOT / "docs/design-references/liblib-header-mobile-615-390.png"
DESKTOP_SCREENSHOT = (
    ROOT / "docs/design-references/liblib-header-mobile-615-1920.png"
)

MOBILE = {"width": 390, "height": 844}
DESKTOP = {"width": 1920, "height": 1150}
SWITCHER_W = 170

# Source readings at 1920 (batch 606) that must not move.
SRC_LEFT_COL_W = 280
SRC_CLOSE = (0, 5.5, 40, 40)
SRC_TOGGLE = (240, 5.5, 40, 40)

IGNORE_CONSOLE = (
    "The attached 3D object must be a part of the scene graph",
    "webpack-hmr",
    "WebSocket",
    "Failed to load resource",
    "nextjs-dev-overlay",
    "src/components/jimeng/nodes/JimengTextNode.tsx",
    "src/components/jimeng/JimengHelpMenu.tsx",
)

READ = """() => {
  const at = (el) => { const r = el.getBoundingClientRect();
    return [Math.round(r.x*10)/10, Math.round(r.y*10)/10,
            Math.round(r.width*10)/10, Math.round(r.height*10)/10]; };
  const cs = (el) => getComputedStyle(el);
  const overlap = (a, b) => a[0] < b[0] + b[2] && a[0] + a[2] > b[0]
    && a[1] < b[1] + b[3] && a[1] + a[3] > b[1];
  const hitOf = (el) => {
    const r = el.getBoundingClientRect();
    const h = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
    if (!h) return {tag: null, own: false};
    return {tag: h.tagName.toLowerCase(),
            aria: (h.getAttribute && h.getAttribute('aria-label')) || '',
            own: h === el || el.contains(h) || h.contains(el)};
  };
  const grab = (el) => el ? {box: at(el), hit: hitOf(el),
    maxW: cs(el).maxWidth, w: cs(el).width} : null;
  const header = document.querySelector('[data-director-header]');
  const group = document.querySelector('[aria-label="导演台视角"]');
  const toggle = document.querySelector('[data-director-panels-toggle]');
  const close = document.querySelector('header button[aria-label="关闭"]');
  const exportBtn = document.querySelector('[data-director-project-export]');
  const importBtn = document.querySelector('[data-director-project-import]');
  const g = grab(group), t = grab(toggle);
  return {
    vw: innerWidth, vh: innerHeight,
    header: grab(header),
    leftCol: header ? grab(header.children[0]) : null,
    rightCol: header ? grab(header.children[header.children.length - 1]) : null,
    group: g, toggle: t, close: grab(close),
    exportBtn: grab(exportBtn), importBtn: grab(importBtn),
    overlap: (g && t) ? overlap(g["box"], t["box"]) : null,
    switcherLeft: g ? g["box"][0] : None,
  };
}"""


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
        w, h = self.page.viewport_size["width"], self.page.viewport_size["height"]
        self.page.mouse.move(w // 2, h // 2)
        self.page.wait_for_timeout(150)
        return self.page.evaluate(READ)


def open_desk(page: Page) -> None:
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__libtv_ui_store "
        "&& window.__director_store)",
        timeout=60_000,
    )
    page.evaluate(
        """() => {
          const s = window.__libtv_store.getState();
          s.addNode("script-execution", { title: "Batch 615" });
          const node = s.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState()
            .openDirectorDesk(node.id, s.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible", timeout=30_000)
    page.wait_for_timeout(1_500)


def run(page: Page, viewport: dict[str, int], tag: str,
        round_trip: bool = False) -> dict[str, Any]:
    v = Verifier(page)
    console: list[str] = []
    errors: list[str] = []
    page.on("console", lambda m: console.append(f"{m.type}: {m.text}"[:200])
            if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)[:200]))
    open_desk(page)

    r = v.read()
    v.result[f"{tag}:desk"] = r
    vw = viewport["width"]

    # --- 1) the switcher itself is unchanged ----------------------------
    g = r["group"]
    v.check(f"{tag}:switcher-present", g is not None)
    if g:
        v.check(f"{tag}:switcher-still-170-wide", near(g["box"][2], SWITCHER_W),
                detail=g["box"])
        v.check(f"{tag}:switcher-still-centred",
                near(g["box"][0], vw / 2 - SWITCHER_W / 2), detail=g["box"][0])

    # --- 2) the left column clears the switcher -------------------------
    lc = r["leftCol"]
    v.check(f"{tag}:left-col-present", lc is not None)
    if lc and g:
        v.check(f"{tag}:left-col-capped-at-the-switcher",
                lc["box"][2] <= g["box"][0] + 0.6,
                detail=f"left {lc['box'][2]} vs switcher left {g['box'][0]}")
    v.check(f"{tag}:no-overlap-with-the-switcher", r["overlap"] is False,
            detail=r["overlap"])

    # --- 3) every header control is hit-testable -------------------------
    for key, label in (("toggle", "收起"), ("close", "关闭"),
                       ("exportBtn", "导出"), ("importBtn", "导入")):
        n = r.get(key)
        v.check(f"{tag}:{label}-hit-testable",
                n is not None and n["hit"]["own"] is True,
                detail=(n or {}).get("hit"))

    # --- 4) the click actually lands -------------------------------------
    # The restore path is the rail's 场景 entry, and the rail is `hidden` below
    # 900px by design (batch 573), so the round trip only runs on desktop; the
    # narrow leg asserts the click itself lands.
    if r["toggle"] is not None:
        page.locator("[data-director-panels-toggle]").click(timeout=15_000)
        page.wait_for_timeout(600)
        collapsed = page.evaluate(
            "() => document.querySelector('[data-director-workspace]')"
            ".getAttribute('data-director-panels-collapsed')")
        v.check(f"{tag}:收起-click-lands", collapsed == "true", detail=collapsed)
        if round_trip:
            page.locator('[data-director-icon-rail] [aria-label="场景"]').click()
            page.wait_for_timeout(600)
            v.check(f"{tag}:场景-restores-it",
                    page.locator("[data-director-tree]").is_visible() is True)
            after = v.read()
            v.result[f"{tag}:after"] = after
            v.check(f"{tag}:no-overlap-after-the-round-trip", after["overlap"] is False,
                    detail=after["overlap"])
            v.check(f"{tag}:left-col-back-to-110", after["leftCol"] is not None
                    and near(after["leftCol"]["box"][2], 110),
                    detail=(after["leftCol"] or {}).get("box"))

    page.screenshot(path=str(SCREENSHOT if tag == "mobile" else DESKTOP_SCREENSHOT))

    noise = [c for c in console if any(k in c for k in IGNORE_CONSOLE)]
    real_console = [c for c in console if not any(k in c for k in IGNORE_CONSOLE)]
    real_errors = [e for e in errors if any(k in e for k in IGNORE_CONSOLE)]
    v.check(f"{tag}:no-page-errors", not real_errors, detail=real_errors[:5])
    v.check(f"{tag}:no-console-errors", not real_console, detail=real_console[:5])
    v.result[f"{tag}:diagnostics"] = {"consoleErrors": len(console),
                                      "filtered": len(noise),
                                      "pageErrors": len(errors)}
    v.result["_summary"] = {"checks": v.count, "failures": v.failures}
    return v.result


def run_desktop_extra(page: Page) -> dict[str, Any]:
    """The source's 1920px left head must be byte-identical after the fix."""
    v = Verifier(page)
    open_desk(page)
    r = v.read()
    v.result["desk"] = r
    lc = r["leftCol"]
    v.check("desktop:left-col-still-280", lc is not None
            and near(lc["box"][2], SRC_LEFT_COL_W), detail=lc["box"][2] if lc else None)
    v.check("desktop:max-width-cap-does-not-engage",
            lc is not None and (lc["maxW"] in ("none", "")
                                or float(lc["maxW"].replace("px", "")) > SRC_LEFT_COL_W),
            detail=lc["maxW"] if lc else None)
    v.check("desktop:关闭-still-at-0-5.5",
            r["close"] is not None
            and all(near(r["close"]["box"][i], SRC_CLOSE[i]) for i in range(4)),
            detail=(r["close"] or {}).get("box"))
    v.check("desktop:收起-still-at-240-5.5",
            r["toggle"] is not None
            and all(near(r["toggle"]["box"][i], SRC_TOGGLE[i]) for i in range(4)),
            detail=(r["toggle"] or {}).get("box"))
    v.check("desktop:switcher-still-@-",
            r["group"] is not None and near(r["group"]["box"][0], 875),
            detail=(r["group"] or {}).get("box"))
    v.check("desktop:no-overlap", r["overlap"] is False, detail=r["overlap"])
    page.locator("[data-director-panels-toggle]").click(timeout=15_000)
    page.wait_for_timeout(600)
    v.check("desktop:收起-click-lands",
            page.evaluate("() => document.querySelector("
                          "'[data-director-workspace]')"
                          ".getAttribute('data-director-panels-collapsed')")
            == "true")
    page.locator('[data-director-icon-rail] [aria-label="场景"]').click()
    page.wait_for_timeout(600)
    v.check("desktop:场景-restores-it",
            page.locator("[data-director-tree]").is_visible() is True)
    back = v.read()
    v.result["after"] = back
    v.check("desktop:geometry-restored", back["toggle"] is not None
            and all(near(back["toggle"]["box"][i], SRC_TOGGLE[i]) for i in range(4)),
            detail=(back["toggle"] or {}).get("box"))
    page.screenshot(path=str(DESKTOP_SCREENSHOT))
    v.result["_summary"] = {"checks": v.count, "failures": v.failures}
    return v.result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 615,
        "title": "Narrow-viewport header: the 收起 button is no longer covered "
                 "by the centred view-mode switcher",
        "date": "2026-10-01",
        "sourceEvidence": [
            "batch 94's mobile leg: 56 retries of 'subtree intercepts pointer "
            "events' from the 170px switcher over [data-director-panels-toggle]",
            "baseline comparison (cp to /tmp + git checkout --, never stash) "
            "reproduced the same failure with batches 613/614 reverted, so it "
            "is pre-existing rather than collateral",
            "probe615: the header's grid, the four children and the exact "
            "boxes/hit results at 390x844 and 1920x1150",
            "probe615b: a throwaway tab at 390x844 with a device-metrics "
            "override on that tab only — it lands on the canvas page, so the "
            "source's narrow header is NOT measured and not claimed",
        ],
        "claims": {
            "cloneDefect": [
                "the view-mode switcher is absolute + fixed 170px, so it "
                "ignores the header's grid and covers the left column's tail",
                "at 390px the left column is 147.5 wide and 收起 sits at "
                "[99.5,5.5,40,40], so its right half (110..139.5) is under the "
                "switcher and its centre is not clickable",
            ],
            "cloneDecision": [
                "cap the left column at max-w-[calc(50vw-85px)] below 900px, "
                "85 being half the switcher's fixed 170px",
                "at >=900px 50vw-85 >= 395 > 280, so the cap never engages and "
                "the source's fixed 280px left head is untouched",
            ],
            "notClaimed": [
                "what the source's header does at phone widths — unmeasured",
                "the 170px switcher width itself, which comes from batch 605's "
                "desktop reading and is kept",
            ],
        },
    }
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        mobile_ctx = browser.new_context(viewport=MOBILE)
        mobile = run(mobile_ctx.new_page(), MOBILE, "mobile")
        desk_ctx = browser.new_context(viewport=DESKTOP)
        desktop = run_desktop_extra(desk_ctx.new_page())
        browser.close()
    total = mobile["_summary"]["checks"] + desktop["_summary"]["checks"]
    fails = mobile["_summary"]["failures"] + desktop["_summary"]["failures"]
    audit["checks"] = {"mobile": mobile, "desktop": desktop}
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
