#!/usr/bin/env python3
"""Batch 623 — sweep the breakpoint neighbourhoods instead of three widths,
and close the one-pixel gap between `max-[899px]` and `min-[900px]`.

**Why a sweep.**  622 found 22 controls that were visible and dead at exactly
one viewport width — 899.  The census had always sampled 390 / 768 / 1920, so
a defect confined to a single pixel was invisible to it by construction.  This
batch turns the census into a width sweep: every breakpoint in the codebase
gets a dense ±3 neighbourhood, plus a coarse pass over the range, and the
result is that the plain state is clean at all 86 widths.

**The gap.**  Those 86 widths also turned up something the discrete samples
could not: at 899 the resource rail collapsed to `[0,0,0,0]`, taking seven
live controls with it.  The cause is a misreading of the compiler:

    max-[899px]  ->  @media (width < 899px)   ->  <= 898   (narrow)
    min-[900px]  ->  @media (width >= 900px)  ->  >= 900   (desktop)

The two look complementary but are a pixel apart, so 899 fell into a band
where **no responsive rule applied at all**.  Measured before the fix:

    vw    tree                 rail            inspector       shotbar         controls
    898   [-220, 88, 220, 812] [0,0,0,0]      [898,88,281,..]  (off)              52
    899   [   0, 88, 220, 812] [0,0,0,0]      [618,52,281,..]  [0,52,899,36]     108
    900   [  48, 52, 233, 848] [0,52,48,848]  [619,52,281,..]  [281,52,619,36]   115

899 rendered a self-contradictory state: the tree and inspector as desktop
columns, the rail as if hidden, and the shot bar running from x=0.  Changing
`min-[900px]` to `min-[899px]` (16 occurrences, 2 files) closes it exactly:
narrow is <= 898 and desktop is >= 899, no gap and no overlap, and it agrees
with the `matchMedia('(max-width: 898px)')` that 622 aligned.  Only the
`min-` side needed moving — `max-[899px]` already meant <= 898.

**The census has a blind spot, and this batch plugs it.**  A control that
renders at zero size is not "covered" by anything, so the census reported
`covered=0` at 899 while seven controls had silently vanished (115 - 108).
So every width here is additionally checked for zero-size or `display:none`
controls, which is what actually surfaced the rail.

**A correction to 622.**  622's README recorded an asymmetry: "below 898 the
tree drawer is inert but the inspector column is parked off screen and *not*
inert".  That was wrong — a measurement artifact.  622 read the `inert`
attribute off `section[data-director-inspector]`, but `inert` is carried by
the enclosing `aside[aria-label="属性"]`.  The truth is fully symmetric: below
the breakpoint both columns are inert and off screen, at and above it neither
is.  623 measures the ancestors to prove it, and this verifier asserts the
symmetric version of the invariant.

Usage: python3 verify-liblib-batch623.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = ROOT / "docs/research/liblib-canvas-batch623-2026-10-01/runtime-audit.json"

_spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(b617)

IGNORE_CONSOLE = (
    "The attached 3D object must be a part of the scene graph",
    "webpack-hmr",
    "WebSocket",
    "Failed to load resource",
    "nextjs-dev-overlay",
    "src/components/jimeng/nodes/JimengTextNode.tsx",
    "src/components/jimeng/nodes/JimengHelpMenu.tsx",
    "src/components/jimeng/nodes/JimengTimelineNode.tsx",
)

# Where CSS behaviour switches.  Read out of the source rather than hard-coded,
# so the sweep follows the codebase if a breakpoint moves.
def _breakpoints() -> list[int]:
    found: set[int] = set()
    for path in (ROOT / "src").rglob("*.tsx"):
        text = re.sub(r"/\*.*?\*/", "", path.read_text(), flags=re.S)
        text = re.sub(r"//[^\n]*", "", text)
        for m in re.finditer(r"(?:max|min)-\[(\d+)px\]", text):
            found.add(int(m.group(1)))
    return sorted(found)


SWITCHES = _breakpoints()
DENSE = sorted({w for b in SWITCHES for w in range(b - 3, b + 4)})
COARSE = sorted(set(range(360, 1921, 40)))
WIDTHS = sorted(set(DENSE) | set(COARSE))

# Fresh-load cross-checks.  The bulk sweep resizes one page, which is much
# faster but could in principle measure a stale state; these widths are
# recomputed from a brand-new page load and must agree.
CROSSCHECK = [429, 430, 479, 480, 519, 520, 619, 620, 679, 680, 849, 850,
              897, 898, 899, 900, 901]

# Zero-size / display:none controls.  The census cannot see these: a control
# that renders at nothing is not covered by anything.
BLIND_JS = """() => {
  const sel = 'button, [role="button"], [role="switch"], [role="separator"], a[href], input';
  const out = [];
  for (const el of document.querySelectorAll(sel)) {
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    // a control that draws nothing and takes no clicks
    const zero = (r.width === 0 && r.height === 0);
    const hidden = cs.display === 'none' || cs.visibility === 'hidden';
    const label = el.getAttribute('aria-label') || el.getAttribute('title')
                  || (el.textContent || '').trim().slice(0, 14) || el.tagName.toLowerCase();
    if (zero || hidden) {
      // an ancestor that is genuinely collapsed is expected (a closed drawer);
      // only report when nothing in the chain is off-screen or hidden
      let n = el, explained = false;
      while (n && n !== document.body) {
        const nr = n.getBoundingClientRect();
        const ncs = getComputedStyle(n);
        if (nr.right <= 0 || nr.left >= innerWidth
            || ncs.display === 'none' || ncs.visibility === 'hidden') { explained = true; break; }
        n = n.parentElement;
      }
      if (!explained) {
        out.push({label, zero, hidden,
                  box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
                  data: Object.keys(el.dataset).slice(0, 3)});
      }
    }
  }
  return out;
}"""

GEOM_JS = """() => {
  const at = (sel) => { const e = document.querySelector(sel); if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; };
  // inert lives on the aside wrapper, not on the section inside it — 622 read
  // the inner element and wrongly concluded the columns were asymmetric.
  const t = document.querySelector('aside[aria-label="场景对象"]');
  const i = document.querySelector('aside[aria-label="属性"]');
  return {
    vw: innerWidth,
    tree: at('aside[aria-label="场景对象"]'),
    treeInert: t ? t.hasAttribute('inert') : null,
    inspector: at('aside[aria-label="属性"]'),
    inspectorInert: i ? i.hasAttribute('inert') : null,
    rail: at('[data-director-icon-rail]'),
    shotBar: at('[data-director-shot-bar]'),
  };
}"""


class Verifier:
    def __init__(self) -> None:
        self.result: dict[str, Any] = {}
        self.failures: list[str] = []
        self.count = 0

    def check(self, name: str, ok: bool, detail: Any = "") -> None:
        self.count += 1
        self.result[name] = {"ok": bool(ok), "detail": detail}
        if not ok:
            self.failures.append(name)
        print(("  PASS " if ok else "  FAIL ") + name + (f"  {detail}" if detail else ""))


def prep(page: Any) -> None:
    page.evaluate("() => document.querySelectorAll('nextjs-portal')"
                  ".forEach(el => el.remove())")
    page.mouse.move(5, 5)
    page.wait_for_timeout(120)


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 623,
        "title": "sweep the breakpoint neighbourhoods instead of three widths, "
                 "and close the one-pixel gap between max-[899px] and "
                 "min-[900px] that collapsed the resource rail at 899",
        "date": "2026-10-01",
        "sourceEvidence": [
            "no live source reading: the shared source tab is at 1600x1000 "
            "with another user in it (probe616), so this batch makes no "
            "fidelity claim",
            "/tmp/dbg623a.py: 86 widths (dense +-3 around every breakpoint in "
            "src/ plus a coarse 40px pass), census at each, and a fresh-load "
            "cross-check at 17 widths",
            "/tmp/dbg623b.py: the ancestor chain of both columns at "
            "390/897/898/899/900, showing inert is carried by the aside wrapper "
            "— 622 read the inner section and got a false asymmetry",
            "/tmp/dbg623c.py: panel geometry at 895..905 before and after the "
            "fix. Before: rail [0,0,0,0] and 108 controls at 899 vs [0,52,48,848] "
            "and 115 at 900. After: identical",
        ],
        "claims": {
            "cloneDecision": [
                "min-[900px] became min-[899px] in 16 places across "
                "DirectorDesk.tsx and DirectorIconRail.tsx, so narrow is <= 898 "
                "and desktop is >= 899 with no uncovered width. Only the min- "
                "side moved: max-[899px] already meant <= 898",
                "the sweep is now part of acceptance: 86 widths, each with a "
                "census, a zero-size/display:none control check, and the "
                "on-screen/inert invariant for both columns",
            ],
            "notClaimed": [
                "anything about the source at all — no source reading backs "
                "this batch, including the choice to put 899 on the desktop "
                "side. That choice follows 622, which aligned the JS to <= 898 "
                "mobile, and the arithmetic of the two media queries; it is not "
                "a source reading",
                "the other breakpoints. 430/480/520/620/680/850 are "
                "independent per-component thresholds whose base bands are "
                "ordinary mobile-first defaults, not the complement of "
                "max-[899px]/min-[900px]; they were swept but not changed",
                "that the sweep is exhaustive. 86 widths across 360..1920 is "
                "dense at the boundaries and coarse between them; a defect "
                "confined to an unsampled pixel between the coarse steps would "
                "still be missed",
            ],
        },
        "breakpointsFound": SWITCHES,
    }
    v = Verifier()
    sweep: dict[str, Any] = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # --- bulk: one page, resized -------------------------------------
        page = browser.new_page(viewport={"width": 1440, "height": 900},
                                device_scale_factor=1)
        b617.open_desk(page)
        page.wait_for_timeout(600)
        for w in WIDTHS:
            page.set_viewport_size({"width": w, "height": 900})
            page.wait_for_timeout(160)
            prep(page)
            cen = page.evaluate(b617.AUDIT_JS, list(b617.TRANSIENT_OVERLAYS))
            cov = [b for b in cen["covered"] if b["label"] not in b617.KNOWN_BLOCKED]
            sweep[w] = {"total": cen["total"], "covered": len(cov),
                        "coveredLabels": [b["label"] for b in cov][:6],
                        "clipped": len(cen["clipped"]),
                        "zeroSize": page.evaluate(BLIND_JS)}
        page.close()

        bad_covered = {w: r for w, r in sweep.items() if r["covered"]}
        bad_zero = {w: r for w, r in sweep.items() if r["zeroSize"]}
        v.result["sweep"] = {str(w): {k: r[k] for k in ("total", "covered", "clipped")}
                             for w, r in sweep.items()}
        v.check(f"the-sweep-covers-{len(WIDTHS)}-widths", len(sweep) == len(WIDTHS),
                detail={"dense": len(DENSE), "coarse": len(COARSE)})
        v.check("no-width-has-a-covered-control", not bad_covered,
                detail={str(w): r["coveredLabels"] for w, r in list(bad_covered.items())[:6]})
        v.check("no-width-has-a-control-collapsed-to-nothing", not bad_zero,
                detail={str(w): [z["label"] for z in r["zeroSize"][:4]]
                        for w, r in list(bad_zero.items())[:6]})

        # --- fresh-load cross-check --------------------------------------
        mismatches = []
        for w in CROSSCHECK:
            pg = browser.new_page(viewport={"width": w, "height": 900},
                                  device_scale_factor=1)
            b617.open_desk(pg)
            pg.wait_for_timeout(400)
            prep(pg)
            cen = pg.evaluate(b617.AUDIT_JS, list(b617.TRANSIENT_OVERLAYS))
            cov = [b for b in cen["covered"] if b["label"] not in b617.KNOWN_BLOCKED]
            fresh = {"total": cen["total"], "covered": len(cov),
                     "zeroSize": pg.evaluate(BLIND_JS)}
            if sweep.get(w) and (fresh["total"] != sweep[w]["total"]
                                 or fresh["covered"] != sweep[w]["covered"]):
                mismatches.append((w, sweep[w], fresh))
            v.result[f"fresh-vw{w}"] = fresh
            pg.close()
        v.check("resizing-one-page-agrees-with-a-fresh-load", not mismatches,
                detail=[(w, a, b) for w, a, b in mismatches[:4]])

        # --- the gap, closed: 899 must look like 900 ---------------------
        for w in (897, 898, 899, 900):
            pg = browser.new_page(viewport={"width": w, "height": 900},
                                  device_scale_factor=1)
            console: list[str] = []
            errors: list[str] = []
            pg.on("console", lambda m: console.append(f"{m.type}: {m.text}"[:200])
                  if m.type == "error" else None)
            pg.on("pageerror", lambda e: errors.append(str(e)[:200]))
            b617.open_desk(pg)
            pg.wait_for_timeout(400)
            prep(pg)
            g = pg.evaluate(GEOM_JS)
            v.result[f"vw{w}:geometry"] = g
            tree_on = g["tree"][0] + g["tree"][2] > 0
            insp_on = g["inspector"][0] < g["vw"]
            # "inert exactly when off screen" — i.e. inert == not onScreen.
            # The first version of this check compared onScreen to inert
            # directly, which inverts the claim and failed on correct data at
            # every width: the same shape of mistake as 622's false asymmetry.
            v.check(f"vw{w}:the-tree-is-inert-exactly-when-it-is-off-screen",
                    bool(g["treeInert"]) == (not tree_on),
                    detail={"onScreen": tree_on, "inert": g["treeInert"],
                            "box": g["tree"]})
            v.check(f"vw{w}:the-inspector-is-inert-exactly-when-it-is-off-screen",
                    bool(g["inspectorInert"]) == (not insp_on),
                    detail={"onScreen": insp_on, "inert": g["inspectorInert"],
                            "box": g["inspector"]})
            if w >= 899:
                # the rail must exist on the desktop side of the boundary
                v.check(f"vw{w}:the-resource-rail-has-its-source-width",
                        g["rail"] is not None and g["rail"][2] == 48
                        and g["rail"][3] > 0,
                        detail=g["rail"])
                v.check(f"vw{w}:the-tree-sits-at-the-source-column",
                        g["tree"][0] == 48 and g["tree"][2] == 233,
                        detail=g["tree"])
            noise = [x for x in console if any(k in x for k in IGNORE_CONSOLE)]
            real_c = [x for x in console if not any(k in x for k in IGNORE_CONSOLE)]
            real_e = [e for e in errors if not any(k in e for k in IGNORE_CONSOLE)]
            v.check(f"vw{w}:no-page-errors", not real_e, detail=real_e[:3])
            v.check(f"vw{w}:no-console-errors", not real_c,
                    detail={"errs": real_c[:3], "filtered": len(noise)})
            pg.close()

        browser.close()

    audit["checks"] = v.result
    audit["result"] = f"{v.count - len(v.failures)}/{v.count} passed"
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2))
    print(f"\n{audit['result']}")
    if v.failures:
        print("FAILED: " + ", ".join(v.failures))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
