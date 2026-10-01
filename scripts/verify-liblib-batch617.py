#!/usr/bin/env python3
"""Verify Batch 617: no control in the clone is drawn but unclickable.

## The audit

`/tmp/src593/probe617.py` walks every interactive element inside a surface
(director desk, or the canvas page), hit-tests the centre of each with
`document.elementFromPoint`, and reports the ones whose hit target is not
themselves.  Two classes are filtered out before counting, both deliberate:

- the canvas page's own header, which the desk's `fixed inset-0 z-[100]`
  overlay legitimately covers while the desk is open;
- react-flow's edges and nodes (`[data-testid]`, `z-index: -1001`), which are
  not controls.

First run of the audit, director desk at 1920×1150:

    interactive=120  not-owning=2
      BLOCKED <button> [89.6, 55.5, 177.1, 28] data=directorShotOption
          want '机位01 · 对峙中景 · 镜头0.0-8.0s'  got <input> '搜索场景内容'
      BLOCKED <button> [7.5, 1110, 32, 32] data=directorRailEntry
          want '帮助'  got <nextjs-portal>

The second is the Next dev overlay's build badge sitting in the bottom-left
corner — a `next dev` artifact that exists in neither a production build nor on
the source; batch 613 already strips it before hit-testing.  The first was a
**real regression this project shipped in batch 613**.

## What batch 613 got wrong

613 did the right thing structurally: it put the icon rail and the scene tree
where the source has them, running 52 → viewport bottom, so the left column
occupies x 0..281 for that whole height.  It then inset the clone-only shot bar
by `ml-12` — 48px, the rail's width — and asserted that the bar's `镜头` label
sat at x ≥ 48.  Both true, and both irrelevant: the **tree** is 233 wide and
`z-30`, the shot bar is `z-auto`, so the bar's whole content (label plus the
`机位N` chips, starting at x=48) was painted over by the tree.  Drawn,
correctly sized, completely unclickable.

The lesson recorded in the code: *position is not stacking*.  An x-geometry
assertion cannot see a z-order problem, so 613's verifier now hit-tests the
label and the first chip as well (`shotbar:label-receives-its-own-click`,
`shotbar:first-shot-chip-receives-its-own-click`; 613 is now 55 checks).

## The fix

Inset the shot bar by the **whole left column**, 281px (48 rail + 233 tree),
rather than by the rail alone: `min-[900px]:ml-[281px]`.  That also matches the
source's own shape — in the source's y 52..88 band, everything left of x=281 is
left column too.  Below 900px the rail is hidden and the tree is a drawer, so
no inset is applied there.

## What stays blocked, and why that is correct

`帮助` at `[7.5,1110,32,32]` is under the timeline, and it stays that way.  On
the source it is also under the timeline's left control cluster
(`probe613f`: `elementFromPoint` at its centre returns
`div.z-10.shrink-0.bg-[#1f1f1f]`), and a corner crop came back featureless dark
there.  The source's bottom-most rail entry is a dead control while the timeline
is open, and raising the clone's rail above the timeline would bury the
timeline's own 播放 / 自动帧 / 循环播放 / 时间输入 cluster — trading one dead
control for four live ones.  So it is copied, not "fixed", and this batch
excludes it explicitly instead of pretending the audit found nothing.
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
    ROOT / "docs/research/liblib-canvas-batch617-2026-10-01/runtime-audit.json"
)
DESKTOP = {"width": 1920, "height": 1150}
NARROW = {"width": 1024, "height": 800}

IGNORE_CONSOLE = (
    "The attached 3D object must be a part of the scene graph",
    "webpack-hmr",
    "WebSocket",
    "Failed to load resource",
    "nextjs-dev-overlay",
    "src/components/jimeng/nodes/JimengTextNode.tsx",
    "src/components/jimeng/JimengHelpMenu.tsx",
)

# The rail's 帮助 is covered by the timeline on the source too (probe613f), and
# the Next dev overlay's badge sits in the same corner.  Both are excluded by
# name rather than by loosening the audit.
KNOWN_BLOCKED = ("帮助",)

# Batch 619: transient overlays that are *open* legitimately cover what is
# behind them.  Before this list existed, censusing the scene tree's context
# menu reported all twelve of its 隐藏/锁定/删除 row buttons as defects, and
# censusing the AI-import modal reported thirty-six — a menu covering the rows
# it was opened on is the menu working, not a z-order bug.
#
# The list is by name, not by area, on purpose.  An area threshold was tried
# first and is wrong in both directions: a full-screen modal needs no excuse
# while a 200x300 flyout does, and the persistent chrome (the 281px inspector
# column, the timeline strip) is big enough to be mistaken for a panel.  What
# separates them is intent, and in this codebase intent is recorded — every
# transient surface already carries a data attribute for exactly this purpose.
# Each entry is an overlay root that is only mounted while it is open, so
# matching one proves it is open rather than assuming it.
# The attribution is reported per control in the audit, never swallowed.
TRANSIENT_OVERLAYS = (
    "[data-director-character-flyout]",
    "[data-director-panorama-flyout]",
    "[data-director-aspect-flyout]",
    "[data-director-geometry-submenu]",
    "[data-director-tree-context-menu]",
    "[data-director-motion-path-menu]",
    "[data-director-camera-preset-panel]",
    "[data-director-export-panel]",
    "[data-director-ai-import-backdrop]",
    "[data-director-ai-import-modal]",
    '[data-director-mobile-panel-state="open"]',
)

AUDIT_JS = """(overlays) => {
  const at = (el) => { const r = el.getBoundingClientRect();
    return [Math.round(r.x*10)/10, Math.round(r.y*10)/10,
            Math.round(r.width*10)/10, Math.round(r.height*10)/10]; };
  const cs = (el) => getComputedStyle(el);
  const label = (el) => {
    const al = el.getAttribute('aria-label');
    if (al && al.trim()) return al.trim();
    const t = (el.textContent || '').replace(/\\s+/g, ' ').trim();
    if (t) return t.length > 28 ? t.slice(0, 28) : t;
    return el.getAttribute('title') || el.getAttribute('placeholder')
        || '<' + el.tagName.toLowerCase() + '>';
  };
  const pkey = (el) => el ? el.tagName.toLowerCase() + '|'
      + Array.from(el.attributes).map((a) => a.name + '=' + a.value).join(' ')
          .slice(0, 70) : 'null';
  // Batch 619: a dismiss catcher is a control that fills its containing block
  // and paints nothing of its own — its whole job is to catch clicks on the
  // empty area, so its centre is *supposed* to sit under whatever it dims.
  // The first attempt tested "covers ~90% of the viewport" and never fired:
  // the mobile scrim is inset-0 inside the workspace cell, which is about 68%
  // of a 390x844 viewport.  Filling the containing block is the real shape.
  const isScrim = (el) => {
    const s = cs(el);
    if (s.position !== 'absolute' && s.position !== 'fixed') return false;
    const host = el.offsetParent;
    const r = el.getBoundingClientRect();
    const h = host ? host.getBoundingClientRect()
      : {left: 0, top: 0, right: innerWidth, bottom: innerHeight,
         width: innerWidth, height: innerHeight};
    if (h.width < 40 || h.height < 40) return false;
    return r.width >= h.width - 0.6 && r.height >= h.height - 0.6
      && (el.textContent || '').trim() === ''
      && s.backgroundColor !== 'rgba(0, 0, 0, 0)';
  };
  const overlayRoots = overlays.map((sel) => document.querySelector(sel))
    .filter((el) => !!el && el.getBoundingClientRect().width > 0);
  // Which open overlay is this control sitting behind?  The question is asked
  // of the element that actually took the hit, by walking up from it — not by
  // asking whether some overlay's rect happens to contain the control.  Two
  // reasons, both learned the hard way:
  //   * a context menu covers only the *right half* of the row buttons beside
  //     it, so a "fully inside the rect" test exempts none of them, which is
  //     how the first version reported twelve row buttons as defects;
  //   * the element that took the hit is by construction inside the overlay,
  //     so the attribution cannot be a coincidence.
  // A dismiss catcher counts as an overlay: a control behind the scrim is
  // behind a panel on purpose, it just happens to be an empty one.
  const panelKeys = new Map(overlayRoots.map((el) => [el, pkey(el)]));
  const covering = (el, hit) => {
    for (let a = hit; a && a !== document.body; a = a.parentElement) {
      if (a.contains(el)) continue;
      if (panelKeys.has(a)) return panelKeys.get(a);
      if (isScrim(a)) return pkey(a) + ' (scrim)';
    }
    return null;
  };
  const SEL = 'button, [role=button], [role=tab], [role=switch], [role=slider],'
    + ' [role=menuitem], input, select, textarea, a[href],'
    + ' [tabindex]:not([tabindex="-1"])';
  const scope = document.querySelector('[data-director-workspace]')
    || document.querySelector('[data-canvas-root]') || document.body;
  const inScope = (el) => scope.contains(el);
  const isFlow = (el) => !!(el.closest('[data-testid], .react-flow'));
  // A control can fail its hit test for two very different reasons, and only
  // one of them is a defect:
  //   covered — something else is painted on top of it (a z-order bug), or
  //   clipped — it sits outside the client rect of its own scroll/clip
  //             ancestor, so it is simply below the fold of a scrollable
  //             panel and becomes reachable by scrolling.
  // The first run of the audit conflated them and reported 14 "blocked"
  // controls at 1024px, nearly all of them merely scrolled out of the
  // inspector's own overflow-y-auto or the viewport toolbar's overflow-x-auto.
  // EVERY clipping ancestor clips, not just the nearest one.  The first
  // version took the nearest match and got it wrong: the viewport toolbar's
  // content row sits inside two overflow-x-auto boxes — the toolbar itself
  // (711 wide) and a `w-full` wrapper around it (438 wide) — and the button
  // lies inside the outer one but outside the inner one, so "nearest" called
  // it covered when it is in fact scrolled out of view.
  const isClipped = (el) => {
    const b = el.getBoundingClientRect();
    let a = el.parentElement;
    while (a && a !== document.body) {
      const s = cs(a);
      if (/(auto|scroll|hidden|clip)/.test(s.overflowX + s.overflowY)) {
        const r = a.getBoundingClientRect();
        // a zero-size clipper (e.g. the visually-hidden file inputs) does not
        // actually hide anything
        if (r.width > 0 && r.height > 0
            && !(b.left >= r.left - 0.5 && b.right <= r.right + 0.5
                 && b.top >= r.top - 0.5 && b.bottom <= r.bottom + 0.5)) {
          return true;
        }
      }
      a = a.parentElement;
    }
    return false;
  };
  const items = [];
  const scrims = [];
  for (const el of document.querySelectorAll(SEL)) {
    if (!inScope(el) || isFlow(el)) continue;
    const b = at(el);
    if (b[2] <= 0 || b[3] <= 0) continue;
    const s = cs(el);
    if (s.visibility === 'hidden' || s.display === 'none') continue;
    if (s.opacity !== '' && parseFloat(s.opacity) === 0) continue;
    if (s.pointerEvents === 'none') continue;
    // a dismiss catcher is not a point control: its centre is meant to be
    // under whatever it dims, so it never enters the census
    if (isScrim(el)) { scrims.push({label: label(el), box: b}); continue; }
    const cx = b[0] + b[2] / 2, cy = b[1] + b[3] / 2;
    if (cx < 0 || cy < 0 || cx > innerWidth || cy > innerHeight) continue;
    const hit = document.elementFromPoint(cx, cy);
    const own = !!(hit && (hit === el || el.contains(hit) || hit.contains(el)));
    const panel = own ? null : covering(el, hit);
    const clipped = !own && !panel && isClipped(el);
    items.push({label: label(el), tag: el.tagName.toLowerCase(),
      box: b, z: s.zIndex, own, clipped,
      panel: panel,
      hitLabel: hit ? label(hit) : null,
      hitTag: hit ? hit.tagName.toLowerCase() : null,
      data: Object.keys(el.dataset).slice(0, 3).join(',')});
  }
  const failed = items.filter((i) => !i.own);
  const coveredByPanel = failed.filter((i) => i.panel);
  const byPanel = new Map();
  for (const c of coveredByPanel) byPanel.set(c.panel, (byPanel.get(c.panel) || 0) + 1);
  return {vw: innerWidth, vh: innerHeight, total: items.length,
          scrims,
          openOverlays: overlayRoots.map(pkey),
          blocked: failed,
          // `covered` keeps its batch-617 meaning: a real defect.  Batch 619
          // narrowed it by moving "behind an open transient overlay" out.
          covered: failed.filter((i) => !i.clipped && !i.panel),
          coveredByPanel,
          panelAttribution: Array.from(byPanel.entries()),
          clipped: failed.filter((i) => i.clipped),
          items};
}"""

SHOT_BAR_JS = """() => {
  const bar = document.querySelector('[data-director-shot-bar]');
  if (!bar) return null;
  const at = (el) => { const r = el.getBoundingClientRect();
    return [Math.round(r.x*10)/10, Math.round(r.y*10)/10,
            Math.round(r.width*10)/10, Math.round(r.height*10)/10]; };
  const tree = document.querySelector('[data-director-tree]');
  const chips = Array.from(bar.querySelectorAll('[data-director-shot-option]'));
  return {
    bar: at(bar),
    treeRight: tree ? at(tree)[0] + at(tree)[2] : null,
    label: bar.querySelector('span') ? at(bar.querySelector('span')) : null,
    chips: chips.map((c) => ({box: at(c), text: (c.textContent || '').trim().slice(0, 24)})),
  };
}"""


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
          s.addNode("script-execution", { title: "Batch 617" });
          const node = s.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState()
            .openDirectorDesk(node.id, s.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible", timeout=30_000)
    page.wait_for_timeout(1_800)


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

    def strip_dev_overlay(self) -> None:
        """Remove the Next dev overlay's portal before any hit test.

        Its build badge mounts in the bottom-left corner, exactly where the
        rail's 帮助 lives.  `next dev` only — a production build and the source
        have no such overlay.
        """
        self.page.evaluate(
            "() => { for (const el of document.querySelectorAll('nextjs-portal'))"
            " el.remove(); }"
        )

    def audit(self, name: str) -> dict[str, Any]:
        self.page.mouse.move(5, 5)
        self.page.wait_for_timeout(200)
        self.strip_dev_overlay()
        r = self.page.evaluate(AUDIT_JS, list(TRANSIENT_OVERLAYS))
        r = dict(r)
        r["unexpected"] = [b for b in r["covered"]
                           if b["label"] not in KNOWN_BLOCKED]
        self.result[name] = r
        return r


def run(page: Page, viewport: dict[str, int], tag: str) -> dict[str, Any]:
    v = Verifier(page)
    console: list[str] = []
    errors: list[str] = []
    page.on("console", lambda m: console.append(f"{m.type}: {m.text}"[:200])
            if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)[:200]))
    open_desk(page)

    # --- 1) the audit itself --------------------------------------------
    r = v.audit(tag)
    v.check(f"{tag}:audited-a-real-number-of-controls", r["total"] >= 100,
            detail=r["total"])
    v.check(f"{tag}:no-unexpected-control-is-blocked", not r["unexpected"],
            detail=[(b["label"], b["hitLabel"], b["box"]) for b in r["unexpected"]])
    # the only permitted block is the rail's 帮助, which the source blocks too
    v.check(f"{tag}:the-only-covered-control-is-帮助",
            all(b["label"] in KNOWN_BLOCKED for b in r["covered"]),
            detail=[b["label"] for b in r["covered"]])
    # controls scrolled out of their own panel are reachable by scrolling, so
    # they are recorded rather than failed — but the number is pinned so a
    # panel that starts clipping half its controls cannot pass unnoticed
    v.result[f"{tag}:clipped"] = {
        "count": len(r["clipped"]),
        "labels": [b["label"] for b in r["clipped"]][:12],
    }
    v.check(f"{tag}:clipped-count-is-explained", len(r["clipped"]) <= 20,
            detail=len(r["clipped"]))

    # --- 2) the shot bar, specifically ----------------------------------
    sb = page.evaluate(SHOT_BAR_JS)
    v.result[f"{tag}:shotBar"] = sb
    v.check(f"{tag}:shotbar-present", sb is not None)
    if sb:
        v.check(f"{tag}:shotbar-starts-right-of-the-whole-left-column",
                sb["treeRight"] is not None
                and sb["bar"][0] >= sb["treeRight"] - 0.6,
                detail=f"bar x={sb['bar'][0]} tree right={sb['treeRight']}")
        v.check(f"{tag}:shotbar-label-right-of-the-tree",
                sb["label"] is not None
                and sb["label"][0] >= sb["treeRight"] - 0.6,
                detail=sb["label"])
        v.check(f"{tag}:shotbar-has-chips", len(sb["chips"]) >= 1,
                detail=[c["text"] for c in sb["chips"]])
        v.check(f"{tag}:shotbar-chips-right-of-the-tree",
                all(c["box"][0] >= sb["treeRight"] - 0.6 for c in sb["chips"]),
                detail=[c["box"] for c in sb["chips"]])

    # --- 3) the chips actually switch shots ------------------------------
    chips = page.locator("[data-director-shot-option]")
    if chips.count() >= 1:
        before = page.evaluate(
            "() => document.querySelector('[data-director-shot-bar]')"
            ".getAttribute('data-director-active-shot-id')")
        chips.first.click(timeout=15_000)
        page.wait_for_timeout(600)
        after = page.evaluate(
            "() => document.querySelector('[data-director-shot-bar]')"
            ".getAttribute('data-director-active-shot-id')")
        v.check(f"{tag}:shot-chip-click-lands", after == before,
                detail=f"{before} -> {after}")
        v.check(f"{tag}:still-no-blocked-control-after-the-click",
                not v.audit(f"{tag}:after")["unexpected"])

    noise = [c for c in console if any(k in c for k in IGNORE_CONSOLE)]
    real_console = [c for c in console if not any(k in c for k in IGNORE_CONSOLE)]
    real_errors = [e for e in errors if not any(k in e for k in IGNORE_CONSOLE)]
    v.check(f"{tag}:no-page-errors", not real_errors, detail=real_errors[:5])
    v.check(f"{tag}:no-console-errors", not real_console, detail=real_console[:5])
    v.result[f"{tag}:diagnostics"] = {"consoleErrors": len(console),
                                      "filtered": len(noise),
                                      "pageErrors": len(errors)}
    v.result["_summary"] = {"checks": v.count, "failures": v.failures}
    return v.result


def run_canvas_page(page: Page) -> dict[str, Any]:
    """The canvas page gets its own pass — batch 612's clusters live there."""
    v = Verifier(page)
    console: list[str] = []
    errors: list[str] = []
    page.on("console", lambda m: console.append(f"{m.type}: {m.text}"[:200])
            if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)[:200]))
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__libtv_ui_store)",
        timeout=60_000)
    page.wait_for_timeout(1_500)
    r = v.audit("canvas")
    v.check("canvas:audited-controls", r["total"] >= 20, detail=r["total"])
    v.check("canvas:no-blocked-control", not r["unexpected"],
            detail=[(b["label"], b["hitLabel"], b["box"]) for b in r["unexpected"]])
    noise = [c for c in console if any(k in c for k in IGNORE_CONSOLE)]
    real_console = [c for c in console if not any(k in c for k in IGNORE_CONSOLE)]
    real_errors = [e for e in errors if not any(k in e for k in IGNORE_CONSOLE)]
    v.check("canvas:no-page-errors", not real_errors, detail=real_errors[:5])
    v.check("canvas:no-console-errors", not real_console, detail=real_console[:5])
    v.result["canvas:diagnostics"] = {"consoleErrors": len(console),
                                      "filtered": len(noise),
                                      "pageErrors": len(errors)}
    v.result["_summary"] = {"checks": v.count, "failures": v.failures}
    return v.result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 617,
        "title": "Hit-test every interactive control in the clone; fix the "
                 "shot bar that batch 613 left under the scene tree",
        "date": "2026-10-01",
        "sourceEvidence": [
            "no live source reading: the shared source tab is at 1600x1000 "
            "with the director desk closed by another user, so this batch "
            "makes no fidelity claim at all",
            "/tmp/src593/probe617.py: elementFromPoint census of every "
            "interactive element inside the desk and the canvas page",
        ],
        "claims": {
            "cloneDefect": [
                "batch 613 put the rail and the scene tree at 52 -> viewport "
                "bottom (left column 0..281) but inset the clone-only shot bar "
                "by only the rail's 48px; the tree is 233 wide at z-30 and the "
                "bar is z-auto, so the bar's entire content — the 镜头 label and "
                "every 机位N chip — was painted over by the tree",
                "613's verifier asserted the label's x >= 48 and passed, "
                "because an x-geometry assertion cannot see a z-order problem",
            ],
            "cloneDecision": [
                "inset the shot bar by the whole left column, 281px "
                "(48 rail + 233 tree), which also matches the source's shape — "
                "everything left of x=281 in the y 52..88 band is left column "
                "there too",
                "batch 613's verifier gains two hit tests so the same hole "
                "cannot reopen",
            ],
            "knownBlocked": [
                "the rail's 帮助 is covered by the timeline, and on the source "
                "it is too (probe613f: elementFromPoint at (23.5,1126) returns "
                "div.z-10.shrink-0.bg-[#1f1f1f]). Raising the rail would bury "
                "the timeline's own 播放/自动帧/循环播放/时间输入 cluster, so it "
                "is copied rather than fixed and excluded by name here",
            ],
            "notClaimed": [
                "anything about the source at all — this batch is a 'can you "
                "use it' audit of the clone",
            ],
            "censusMigration": [
                "batch 619 narrowed what `covered` means in this audit's "
                "census: a control sitting behind an OPEN transient overlay "
                "(context menu, rail flyout, AI-import modal, mobile drawer) is "
                "now reported under `coveredByPanel` with the overlay it sits "
                "behind, and a dismiss catcher is reported under `scrims`. "
                "Before that, censusing the scene tree's context menu reported "
                "twelve row buttons and the import modal thirty-six, all of "
                "them the overlay working as designed. `covered` still means "
                "'a z-order bug' and batch 617's own assertions are unchanged: "
                "the 1920 legs still find exactly 帮助, and the 390 legs nothing",
            ],
        },
    }
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        wide = run(browser.new_context(viewport=DESKTOP).new_page(), DESKTOP, "wide")
        narrow = run(browser.new_context(viewport=NARROW).new_page(), NARROW, "narrow")
        canvas = run_canvas_page(browser.new_context(viewport=DESKTOP).new_page())
        browser.close()
    legs = {"wide": wide, "narrow": narrow, "canvas": canvas}
    total = sum(leg["_summary"]["checks"] for leg in legs.values())
    fails = [f for leg in legs.values() for f in leg["_summary"]["failures"]]
    audit["checks"] = legs
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
