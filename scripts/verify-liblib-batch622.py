#!/usr/bin/env python3
"""Batch 622 — kill a candidate with a measurement, and fix a one-pixel
breakpoint disagreement that left 22 controls visible but dead.

Two findings, in the order they were reached.

**1. The 900–1043px band is not a defect (candidate withdrawn).**

621 left a candidate: "raise the two-row breakpoint from 898 to ~1043 to
remove the 20–145px hidden in that band".  That candidate smuggled in an
assumption — that content hidden behind the right strip is *buried*.  It is
not.  Above the breakpoint the single-row arrangement (floating strip + a
horizontally scrolling cluster) is exactly the source-measured layout from
batches 593/596, and its overflow is reachable by scrolling.  Measured at
899/900/960/1024/1043/1100/1280 (`/tmp/dbg622a.py`), every one of the
cluster's 14 controls scrolls to the centre of the window and then takes its
own hit test: `reachable_but_blocked=0`, `never_in_window=0` at every width.
Moving the breakpoint would not fix anything — it would replace a
source-measured desktop layout with a clone-side re-arrangement that no
source reading supports.  This batch records the measurement and withdraws
the candidate.

**2. At exactly 899px the scene tree and the inspector are dead.**

The same sweep found the one viewport where the control census went from
zero covered controls to 22.  The cause is a one-pixel disagreement about
where the mobile breakpoint is:

    JS   matchMedia('(max-width: 899px)')  → mobile at width <= 899
    CSS  Tailwind max-[899px]
         → @media (width < 899px)          → mobile at width <= 898

So at vw=899 the JavaScript decided it was on a phone while the stylesheet
decided it was on a desktop.  The scene tree and the inspector column were
rendered in their **desktop, on-screen** positions — tree at [0,88,220,812],
inspector at [618,52,281,666] — and then, because `treeMobileInactive` /
`inspectorMobileInactive` are derived from the JS flag, both columns were
marked `inert` wholesale.  Every control in them was on screen and dead.
`/tmp/dbg622b.py` reads all five widths:

    vw=897  js<=899  css<899  agree  tree box [-220, 88, ...] inert   (off-screen, correct)
    vw=898  js<=899  css<899  agree  tree box [-220, 88, ...] inert   (off-screen, correct)
    vw=899  js<=899  css<899  DIFFER tree box [   0, 88, ...] inert   ← visible and dead
    vw=900  js<=899  css<899  agree  tree not inert                    (desktop, correct)

The fix aligns the JS to the CSS (`max-width: 898px`) rather than the other
way round: the 898/899 landing point is the codebase-wide convention that
621 already recorded as recorded-not-fixed, and moving the CSS would shift
every `max-[899px]` rule at once.

Usage: python3 verify-liblib-batch622.py
"""
from __future__ import annotations

import importlib.util
import re
import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = ROOT / "docs/research/liblib-canvas-batch622-2026-10-01/runtime-audit.json"

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

# The query the app actually uses, read out of the source rather than
# hard-coded here — if someone edits DirectorDesk's breakpoint, this test
# follows the edit instead of silently measuring a literal that no longer
# exists (which is exactly how the first version of this test lied: it kept
# evaluating '(max-width: 899px)' after the fix had changed it to 898 and
# reported a disagreement that the running app no longer had).
def _app_media_query() -> str:
    src = (ROOT / "src/components/director/DirectorDesk.tsx").read_text()
    # Strip comments first.  The first version of this test regexed the raw
    # file and matched the *comment* that quotes the old value — so it went on
    # measuring `(max-width: 899px)` long after the code had moved to 898, and
    # reported a disagreement the running app no longer had.
    code = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    code = re.sub(r"//[^\n]*", "", code)
    m = re.search(r'matchMedia\(\s*"([^"]+)"\s*\)', code)
    assert m, "could not find matchMedia() in DirectorDesk.tsx"
    return m.group(1)


APP_QUERY = _app_media_query()

# The two media queries whose disagreement this batch is about.  The second
# one is literally what Tailwind v4 emits for `max-[899px]`.
ALIGN_JS = """(appQuery) => {
  // Landmarks that do NOT depend on the inert attribute — an earlier version
  // located the columns via closest('[inert]'), which only resolves on narrow
  // screens and therefore reported "no box" on the desktop widths it was
  // supposed to be checking.
  const tree = document.querySelector('aside[aria-label="场景对象"]');
  const insp = document.querySelector('[data-director-inspector]')
            || document.querySelector("[aria-label='属性']");
  const box = (el) => { if (!el) return null; const r = el.getBoundingClientRect();
    return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; };
  return {
    appQuery,
    appMobile: matchMedia(appQuery).matches,           // the query in DirectorDesk
    cssMobile: matchMedia('(width < 899px)').matches,   // what Tailwind emits
    treeFound: !!tree, inspectorFound: !!insp,
    treeInert: tree ? tree.hasAttribute('inert') : null,
    treeAriaHidden: tree ? tree.getAttribute('aria-hidden') : null,
    treeBox: box(tree),
    inspectorInert: insp ? insp.hasAttribute('inert') : null,
    inspectorBox: box(insp),
    vw: innerWidth,
  };
}"""

# Every control in the cluster, scrolled to the middle of the window and then
# hit-tested.  A control that is merely clipped is reachable and must take its
# own hit; a control that is buried cannot.
REACH_JS = """() => {
  const host = document.querySelector('[data-director-timeline-controls-scroll]');
  if (!host) return {error: 'no scroll host'};
  const nodes = [...host.querySelectorAll('button, [role="switch"], [role="button"], input')];
  const saved = host.scrollLeft;
  const out = [];
  for (const el of nodes) {
    const hb = host.getBoundingClientRect();
    const r0 = el.getBoundingClientRect();
    const want = r0.x + r0.width / 2 - (hb.x + hb.width / 2);
    host.scrollLeft = Math.max(0, Math.min(want, host.scrollWidth - host.clientWidth));
    const r = el.getBoundingClientRect();
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    const inside = cx >= hb.x && cx <= hb.x + hb.width
                && cy >= hb.y && cy <= hb.y + hb.height;
    let hitSelf = null;
    if (inside) {
      const h = document.elementFromPoint(cx, cy);
      hitSelf = !!(h && (h === el || el.contains(h)));
    }
    out.push({label: el.getAttribute('aria-label') || el.getAttribute('title')
                   || (el.textContent || '').trim().slice(0, 12) || el.tagName.toLowerCase(),
              inside, hitSelf});
  }
  host.scrollLeft = saved;
  return {clientW: host.clientWidth, scrollW: host.scrollWidth,
          hidden: Math.max(0, host.scrollWidth - host.clientWidth), nodes: out};
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


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 622,
        "title": "withdraw the 900-1043px candidate with a measurement, and "
                 "fix the 899px JS/CSS breakpoint disagreement that left the "
                 "scene tree and inspector visible but inert",
        "date": "2026-10-01",
        "sourceEvidence": [
            "no live source reading: the shared source tab is at 1600x1000 "
            "with another user in it (probe616), so this batch makes no "
            "fidelity claim",
            "/tmp/dbg622a.py: the control census across 899/900/960/1024/"
            "1043/1100/1280 plus a scroll-then-hit-test of all 14 cluster "
            "controls. reachable_but_blocked=0 and never_in_window=0 at every "
            "width, so the band's 20-145px of hidden cluster is scrollable, "
            "not buried",
            "/tmp/dbg622b.py: at 897/898/899/900/901 the two media queries and "
            "the tree/inspector inert flags side by side. Only 899 disagrees",
        ],
        "claims": {
            "cloneDecision": [
                "DirectorDesk's matchMedia is now '(max-width: 898px)' so the "
                "JS mobile flag lands on the same width as Tailwind's "
                "compiled '(width < 899px)'. At 899 the scene tree and "
                "inspector now render in desktop positions and are not inert, "
                "so their controls take clicks; <=898 keeps the drawers "
                "correctly inert and off-screen, and >=900 is unchanged",
            ],
            "notClaimed": [
                "anything about the source at all — no source reading backs "
                "any part of this batch",
                "that the 898/899 landing point is correct. It is the "
                "codebase-wide convention, recorded and left alone by 621; "
                "this batch only removes the JS/CSS disagreement about it, it "
                "does not move the breakpoint itself",
                "that the 900-1043px band is improved. It is not touched, and "
                "the measurement says there is nothing there to improve: the "
                "cluster's overflow above the breakpoint is scrollable by "
                "design. 621's candidate to move the two-row breakpoint up to "
                "~1043 is withdrawn, not deferred",
            ],
        },
    }
    v = Verifier()
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # --- part 1: the breakpoint agreement, across the boundary -----------
        for w, expect_mobile in ((897, True), (898, True), (899, False),
                                 (900, False), (901, False)):
            page = browser.new_page(viewport={"width": w, "height": 900},
                                    device_scale_factor=1)
            console: list[str] = []
            errors: list[str] = []
            page.on("console", lambda m: console.append(f"{m.type}: {m.text}"[:200])
                    if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            b617.open_desk(page)
            page.evaluate("() => document.querySelectorAll('nextjs-portal')"
                          ".forEach(el => el.remove())")
            page.mouse.move(5, 5)
            page.wait_for_timeout(250)
            a = page.evaluate(ALIGN_JS, APP_QUERY)
            v.result[f"vw{w}:alignment"] = a
            v.check(f"vw{w}:the-js-and-css-breakpoints-agree",
                    a["appMobile"] == a["cssMobile"],
                    detail={"appQuery": a["appQuery"], "app": a["appMobile"],
                            "css": a["cssMobile"]})
            v.check(f"vw{w}:is-the-viewport-classified-as-expected",
                    a["appMobile"] == expect_mobile,
                    detail={"got": a["appMobile"], "want": expect_mobile})
            # The behavioural invariant, stated without reference to any width:
            # **a column that is on screen must be interactive.**  That one
            # direction is the defect — at 899 both columns were painted in
            # their desktop positions and marked inert, so every control was
            # visible and dead.
            #
            # The converse is deliberately NOT asserted.  Below the breakpoint
            # the tree drawer is parked off screen *and* inert, but the
            # inspector column is parked off screen and *not* inert — a
            # pre-existing asymmetry that this batch did not introduce and does
            # not fix.  An off-screen column cannot be clicked, and the census
            # is clean there, so it is not a control defect; keyboard focus is
            # the only surface it could affect.  It is recorded instead of
            # turned into a passing-or-failing rule the code never promised.
            if a["treeFound"]:
                tree_on = a["treeBox"][0] + a["treeBox"][2] > 0
                v.check(f"vw{w}:the-tree-is-not-inert-while-on-screen",
                        (not tree_on) or not a["treeInert"],
                        detail={"onScreen": tree_on, "inert": a["treeInert"],
                                "ariaHidden": a["treeAriaHidden"],
                                "box": a["treeBox"]})
            if a["inspectorFound"]:
                insp_on = a["inspectorBox"][0] < a["vw"]
                v.check(f"vw{w}:the-inspector-is-not-inert-while-on-screen",
                        (not insp_on) or not a["inspectorInert"],
                        detail={"onScreen": insp_on, "inert": a["inspectorInert"],
                                "box": a["inspectorBox"]})
            v.result[f"vw{w}:offscreen-not-inert"] = {
                "tree": (not (a["treeBox"][0] + a["treeBox"][2] > 0))
                        and a["treeFound"] and not a["treeInert"],
                "inspector": (not (a["inspectorBox"][0] < a["vw"]))
                              and a["inspectorFound"] and not a["inspectorInert"],
            }
            # The census is the user-visible consequence: a column that is inert
            # while on screen shows up as covered controls.  Assert it directly
            # so the invariant is not only about two attributes.
            cen = page.evaluate(b617.AUDIT_JS, list(b617.TRANSIENT_OVERLAYS))
            cov = [b for b in cen["covered"] if b["label"] not in b617.KNOWN_BLOCKED]
            v.result[f"vw{w}:census"] = {"total": cen["total"], "covered": len(cov)}
            v.check(f"vw{w}:the-census-reports-no-covered-control",
                    not cov,
                    detail=[(b["label"], b["box"]) for b in cov][:5])
            noise = [x for x in console if any(k in x for k in IGNORE_CONSOLE)]
            real_c = [x for x in console if not any(k in x for k in IGNORE_CONSOLE)]
            real_e = [e for e in errors if not any(k in e for k in IGNORE_CONSOLE)]
            v.check(f"vw{w}:no-page-errors", not real_e, detail=real_e[:3])
            v.check(f"vw{w}:no-console-errors", not real_c,
                    detail={"errs": real_c[:3], "filtered": len(noise)})
            page.close()

        # --- part 2: the withdrawn candidate, now a contract ------------------
        for w in (900, 960, 1024, 1043, 1100, 1280):
            page = browser.new_page(viewport={"width": w, "height": 900},
                                    device_scale_factor=1)
            b617.open_desk(page)
            page.evaluate("() => document.querySelectorAll('nextjs-portal')"
                          ".forEach(el => el.remove())")
            page.mouse.move(5, 5)
            page.wait_for_timeout(250)
            r = page.evaluate(REACH_JS)
            v.result[f"vw{w}:cluster-reach"] = r
            blocked = [n for n in r["nodes"] if n["inside"] and not n["hitSelf"]]
            never = [n for n in r["nodes"] if not n["inside"]]
            v.check(f"vw{w}:every-cluster-control-is-reachable-by-scrolling",
                    not blocked and not never,
                    detail={"controls": len(r["nodes"]), "blocked": blocked[:4],
                            "neverInWindow": never[:4]})
            cen = page.evaluate(b617.AUDIT_JS, list(b617.TRANSIENT_OVERLAYS))
            covered = [b for b in cen["covered"] if b["label"] not in b617.KNOWN_BLOCKED]
            v.result[f"vw{w}:census"] = {"total": cen["total"],
                                        "covered": len(covered),
                                        "clipped": len(cen["clipped"])}
            v.check(f"vw{w}:the-hidden-part-is-clipped-not-buried",
                    not covered,
                    detail={"hidden": r["hidden"], "covered": [(b["label"], b["box"])
                            for b in covered][:4]})
            page.close()

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
