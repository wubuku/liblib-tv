#!/usr/bin/env python3
"""Batch 619 — teach the census about open overlays, then sweep every state.

Batch 618 had to exclude the mobile drawer from the census by hand, because the
audit reported two things that are not defects: the dismiss catcher's own
centre (it sits under the panel it dims) and every control behind an open
drawer.  Both are structural, so both can be decided structurally, and once
they can, whole states become auditable that were previously unusable as
targets.

This verifier does two jobs:

  1. pin the classification itself — every state must come back with no
     uncovered control except the rail's 帮助, which the source blocks too;
  2. pin that the exemptions actually FIRE.  A census that passes because its
     rules never triggered is worse than no census, so each overlay state also
     asserts that the overlay was found, that it attributed at least one
     control, and that the scrim rule fired in the drawer states.

Two dead ends are recorded here because the obvious implementations are wrong
in ways that look right:

  * "the scrim covers ~90% of the viewport" — it does not.  The mobile scrim is
    inset-0 inside the workspace cell, about 68% of a 390x844 viewport, so the
    rule never fired and the scrim was audited as a control.
  * "exempt anything behind a panel larger than N% of the screen" — wrong in
    both directions.  A full-screen modal needs no excuse while a 200x300
    flyout does, and the persistent chrome (the 281px inspector column, the
    timeline strip) is big enough to be mistaken for a panel.  Intent is what
    separates them, and this codebase already records intent in a data
    attribute on every transient surface, so the list is by name.

Usage: python3 verify-liblib-batch619.py
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = ROOT / "docs/research/liblib-canvas-batch619-2026-10-01/runtime-audit.json"

MOBILE = {"width": 390, "height": 844}
WIDE = {"width": 1920, "height": 1150}

KNOWN_BLOCKED = ("帮助",)

IGNORE_CONSOLE = (
    "The attached 3D object must be a part of the scene graph",
    "webpack-hmr",
    "WebSocket",
    "Failed to load resource",
    "nextjs-dev-overlay",
    "src/components/jimeng/nodes/JimengTextNode.tsx",
    "src/components/jimeng/JimengHelpMenu.tsx",
    # batch 620: another developer's in-flight edit; filtered by path like the
    # two entries above.  Not ours to fix and not ours to revert.
    "src/components/jimeng/nodes/JimengTimelineNode.tsx",
)

_spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(b617)
AUDIT_JS = b617.AUDIT_JS
TRANSIENT_OVERLAYS = b617.TRANSIENT_OVERLAYS

# (label, viewport, setup, overlay the setup opens, whether that overlay is
# expected to cover at least one control).  The flag is per state on purpose:
# the export panel pops up over the track area and covers nothing, and asserting
# "attributed >= 1" there would assert something untrue.  Asserting "attributed
# == 0" for it is the stronger claim — the panel is open and covers no control.
STATES: list[tuple[str, str, str | None, str | None, bool]] = [
    ("1920 plain", "wide", None, None, False),
    ("1920 export panel", "wide", "[data-director-export-trigger]",
     "[data-director-export-panel]", False),
    ("1920 tree context menu", "wide", "@tree-rctx@",
     "[data-director-tree-context-menu]", True),
    ("1920 rail panorama flyout", "wide", "[data-director-rail-entry='panorama']",
     "[data-director-panorama-flyout]", True),
    ("1920 rail aspect flyout", "wide", "[data-director-rail-entry='aspect-ratio']",
     "[data-director-aspect-flyout]", True),
    ("1920 rail add-character flyout", "wide", "[data-director-rail-entry='add-character']",
     "[data-director-character-flyout]", True),
    ("1920 ai-import modal", "wide", "[data-director-rail-entry='ai-import']",
     "[data-director-ai-import-modal]", True),
    ("1920 track row context menu", "wide", "@track-rctx@", None, False),
    ("390 plain", "mobile", None, None, False),
    ("390 export panel", "mobile", "[data-director-export-trigger]",
     "[data-director-export-panel]", True),
    ("390 inspector drawer", "mobile", "button[aria-label='打开属性面板']",
     '[data-director-mobile-panel-state="open"]', True),
    ("390 tree drawer", "mobile", "button[aria-label='打开场景对象']",
     '[data-director-mobile-panel-state="open"]', True),
]


def open_desk(page: Page) -> None:
    b617.open_desk(page)


def census(page: Page) -> dict[str, Any]:
    page.mouse.move(5, 5)
    page.wait_for_timeout(250)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal'))"
                  " el.remove(); }")
    r = dict(page.evaluate(AUDIT_JS, list(TRANSIENT_OVERLAYS)))
    r["unexpected"] = [b for b in r["covered"] if b["label"] not in KNOWN_BLOCKED]
    return r


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


def open_state(page: Page, setup: str | None) -> None:
    if not setup:
        return
    if setup == "@tree-rctx@":
        page.locator("[data-director-tree] [data-director-object-id]").first.click(
            button="right", timeout=15_000)
    elif setup == "@track-rctx@":
        page.locator("[data-director-timeline-object-row]").first.click(
            button="right", timeout=15_000)
    else:
        page.locator(setup).first.click(timeout=15_000)


def run_state(browser: Any, v: Verifier, label: str, which: str,
              setup: str | None, overlay: str | None, covers: bool) -> None:
    viewport = WIDE if which == "wide" else MOBILE
    page = browser.new_page(viewport=viewport, device_scale_factor=1)
    console: list[str] = []
    errors: list[str] = []
    page.on("console", lambda m: console.append(f"{m.type}: {m.text}"[:200])
            if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)[:200]))
    tag = label.replace(" ", "-").replace(":", "")
    try:
        open_desk(page)
        open_state(page, setup)
        if overlay:
            page.locator(overlay).first.wait_for(state="visible", timeout=15_000)
        # past the 200ms slide of the drawers and flyouts
        page.wait_for_timeout(900)
        r = census(page)
        v.result[f"{tag}:census"] = r
        v.check(f"{tag}:audited-a-real-number-of-controls", r["total"] >= 30,
                detail=r["total"])
        v.check(f"{tag}:no-control-is-covered", not r["unexpected"],
                detail=[(b["label"], b["hitLabel"], b["box"]) for b in r["unexpected"]])
        # Batch 628 migration: the old guard here was "the only control allowed
        # to be covered is 帮助" — a single hard-coded label, i.e. a name
        # coincidence rather than a reason.  The same source-measured
        # relationship (batch 613: the timeline is an overlay floating over the
        # three columns) buries whole 隐藏/锁定/删除 triads on the last object
        # rows once the viewport gets short, and those labels depend on the
        # scene, so no name list can ever cover the family.  The audit now
        # explains it structurally, and this guard re-checks the exemption's two
        # halves so it cannot be quietly widened later.
        v.check(f"{tag}:every-timeline-overlay-exemption-has-both-halves",
                all(b.get("hitInTimeline") and b.get("victimInColumn")
                    for b in r["coveredByTimelineOverlay"]),
                detail=[(b["label"], b["hitInTimeline"], b["victimInColumn"])
                        for b in r["coveredByTimelineOverlay"]][:6])
        v.check(f"{tag}:no-control-is-off-viewport-and-unreachable",
                not r["offViewportUnreachable"],
                detail=[(b["label"], b["box"], b["data"])
                        for b in r["offViewportUnreachable"]])
        # non-vacuity: the branch above has to have actually run.  A desk with
        # no off-viewport control at all would make the check pass for the wrong
        # reason, and that is exactly how a silent `continue` looks.
        v.check(f"{tag}:the-off-viewport-branch-actually-ran",
                len(r["offViewportItems"]) > 0,
                detail=f"{len(r['offViewportItems'])} off-viewport, "
                       f"{len(r['offViewportScrollable'])} scrollable")
        v.check(f"{tag}:the-only-possible-block-is-帮助",
                all(b["label"] in KNOWN_BLOCKED for b in r["covered"]),
                detail=[b["label"] for b in r["covered"]])
        # Batch 628: 帮助 used to be excused here by name.  It is now excused by
        # structure, so assert the structural form too — otherwise this check
        # would go quietly vacuous once 帮助 left `covered` for the right reason.
        # All three reasons are admissible: the two source/structural overlays
        # and an open transient panel.  The first version of this assertion
        # demanded the timeline overlay specifically and went red in the
        # ai-import-modal state, where 帮助 is attributed to the open modal
        # instead — which is a perfectly good explanation, just a different one.
        helpRows = [b for b in r["blocked"] if b["label"] in KNOWN_BLOCKED]
        v.check(f"{tag}:帮助-is-still-explained-by-a-known-reason",
                all(b.get("panel") or b.get("timelineOverlay")
                    or b.get("viewportSqueeze") for b in helpRows),
                detail=[(b["label"], bool(b.get("panel")),
                         b.get("timelineOverlay"), b.get("viewportSqueeze"))
                        for b in helpRows])
        if overlay:
            # the exemption must actually have run, or this state proves nothing
            v.check(f"{tag}:the-overlay-was-found-open", len(r["openOverlays"]) >= 1,
                    detail=r["openOverlays"][:3])
            if covers:
                v.check(f"{tag}:the-overlay-attributed-at-least-one-control",
                        len(r["coveredByPanel"]) >= 1,
                        detail=[(b["label"], (b["panel"] or "")[:40])
                                for b in r["coveredByPanel"]][:4])
            else:
                v.check(f"{tag}:the-open-overlay-covers-no-control",
                        not r["coveredByPanel"],
                        detail=[(b["label"], (b["panel"] or "")[:40])
                                for b in r["coveredByPanel"]][:4])
            # accounting completeness: every control that failed the hit test
            # for a non-scroll reason is either a defect or attributed to an
            # overlay.  Nothing may fall between the two buckets.
            # Batch 628 added two more buckets, so the identity grew with them
            # rather than being relaxed — this check exists precisely to catch
            # an exemption added on one side and forgotten on the other, and it
            # did.
            nonClipped = len(r["blocked"]) - len(r["clipped"])
            v.check(f"{tag}:every-failure-is-either-a-defect-or-attributed",
                    nonClipped == (len(r["covered"]) + len(r["coveredByPanel"])
                                   + len(r["coveredByTimelineOverlay"])
                                   + len(r["coveredByViewportSqueeze"])),
                    detail={"nonClipped": nonClipped,
                            "covered": len(r["covered"]),
                            "attributed": len(r["coveredByPanel"]),
                            "timelineOverlay": len(r["coveredByTimelineOverlay"]),
                            "viewportSqueeze": len(r["coveredByViewportSqueeze"])})
        if "drawer" in label:
            v.check(f"{tag}:the-dismiss-catcher-was-not-audited-as-a-control",
                    any(s["label"] == "关闭移动端面板" for s in r["scrims"]),
                    detail=r["scrims"])
        noise = [c for c in console if any(k in c for k in IGNORE_CONSOLE)]
        real_console = [c for c in console if not any(k in c for k in IGNORE_CONSOLE)]
        real_errors = [e for e in errors if not any(k in e for k in IGNORE_CONSOLE)]
        v.check(f"{tag}:no-page-errors", not real_errors, detail=real_errors[:4])
        v.check(f"{tag}:no-console-errors", not real_console, detail=real_console[:4])
        v.result[f"{tag}:diagnostics"] = {"consoleErrors": len(console),
                                          "filtered": len(noise),
                                          "pageErrors": len(errors)}
    finally:
        page.close()


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 619,
        "title": "Classify 'behind an open overlay' and 'the dismiss catcher' "
                 "as non-defects, then sweep ten director-desk states",
        "date": "2026-10-01",
        "sourceEvidence": [
            "no live source reading: the shared source tab is at 1600x1000 "
            "with the director desk closed by another user (probe616 re-run), "
            "so this batch makes no fidelity claim",
            "/tmp/dbg619.py: first attempt at the exemptions — the area-based "
            "scrim test never fired (the mobile scrim is inset-0 inside the "
            "workspace cell, ~68% of a 390x844 viewport, not 90%), and the "
            "hitter-keyed overlay test never fired either, because a control "
            "behind a drawer hit-tests to the drawer's innermost element",
            "/tmp/dbg619b.py: corrected rules, then a sweep of ten states — "
            "before the overlay list existed, the tree context menu reported 12 "
            "covered row buttons, the aspect flyout 12, the add-character flyout "
            "20 and the AI-import modal 36, all of them the overlay working",
        ],
        "claims": {
            "cloneDecision": [
                "the dismiss-catcher test is structural: a control whose rect "
                "fills its containing block, paints a background and has no text "
                "of its own is excluded from the census and reported under "
                "`scrims`",
                "controls sitting behind an open transient overlay are reported "
                "under `coveredByPanel` together with the overlay that covers "
                "them; the overlay list is by data attribute because that is "
                "how this codebase records which surfaces are transient, and "
                "an area threshold is wrong in both directions",
                "`covered` keeps its batch-617 meaning — a z-order bug — so "
                "batch 617's own assertions are unchanged",
            ],
            "notClaimed": [
                "anything about the source at all",
                "the exemption list is a list of names, not a proof of intent: "
                "a future overlay that forgets its data attribute would be "
                "audited as covering controls, which fails loudly rather than "
                "silently passing",
                "the states swept are the ones reachable from the desk's own "
                "controls; the camera-preset panel needs a selected camera "
                "track and the motion-path menu needs a selected track, so "
                "neither is in this sweep",
            ],
        },
    }
    v = Verifier()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for label, which, setup, overlay, covers in STATES:
            run_state(browser, v, label, which, setup, overlay, covers)
        browser.close()
    total = v.count
    fails = v.failures
    audit["checks"] = v.result
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
