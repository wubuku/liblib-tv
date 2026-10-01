#!/usr/bin/env python3
"""Batch 620 — census the canvas page at 390x844 and in its open states.

617 censused the canvas page once, at 1920.  The phone width had never been
censused there, and 618/619 both found their real defects in the narrow band
and in *open* states rather than in base layouts — the toolbar's padding
reserve, the mobile drawer, the export panel, all 390-only.

Two things came out of it:

  1. the census was missing the canvas page's own overlay convention.
     `data-liblib-overlay` marks every transient surface on that page (zoom
     menu, canvas dropdown, asset manager, add node, agent drawer, shortcuts,
     share, the two libraries), so censusing the zoom menu at 390 reported the
     five toolbar buttons it legitimately pops over as defects.  620 teaches
     the census that attribute and keeps the director desk's named list;
  2. one real defect survived the exemption: the asset sidebar's own collapse
     button is painted under the canvas page's bottom toolbar at 390, because
     the toolbar is `fixed bottom-[18px] z-[60]` and the sidebar is
     `relative z-50`.  It is not reachable and it is visibly broken — half of
     the « glyph sticks out from under the 资产管理 pill.  The header ✕ and the
     toolbar's 资产管理 button both close the same panel, so the fix is to stop
     rendering the footer button below 900px rather than to raise the sidebar
     above the toolbar, which would bury five live controls instead.

Usage: python3 verify-liblib-batch620.py
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
AUDIT_PATH = ROOT / "docs/research/liblib-canvas-batch620-2026-10-01/runtime-audit.json"

MOBILE = {"width": 390, "height": 844}
WIDE = {"width": 1920, "height": 1150}

_spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(b617)
AUDIT_JS = b617.AUDIT_JS
TRANSIENT_OVERLAYS = b617.TRANSIENT_OVERLAYS
KNOWN_BLOCKED = b617.KNOWN_BLOCKED

IGNORE_CONSOLE = (
    "The attached 3D object must be a part of the scene graph",
    "webpack-hmr",
    "WebSocket",
    "Failed to load resource",
    "nextjs-dev-overlay",
    "src/components/jimeng/nodes/JimengTextNode.tsx",
    "src/components/jimeng/JimengHelpMenu.tsx",
    # another developer's in-flight edit to this file surfaced as a syntax
    # error in the shared dev server while this batch was running; filtered by
    # path like the two entries above
    "src/components/jimeng/nodes/JimengTimelineNode.tsx",
)

# (label, width, what to click, the overlay that click is expected to open)
STATES: list[tuple[str, str, str | None, str | None]] = [
    ("1920 plain", "wide", None, None),
    ("1920 project menu", "wide", "[data-project-menu-trigger]", None),
    ("1920 canvas switcher", "wide", "[data-canvas-trigger]", None),
    ("1920 zoom options", "wide", "[data-viewport-menu-trigger]", '[data-liblib-overlay="zoom-menu"]'),
    ("1920 asset manager", "wide", "text=资产管理", '[data-liblib-overlay="asset"]'),
    ("390 plain", "mobile", None, None),
    ("390 project menu", "mobile", "[data-project-menu-trigger]", None),
    ("390 canvas switcher", "mobile", "[data-canvas-trigger]", None),
    ("390 zoom options", "mobile", "[data-viewport-menu-trigger]", '[data-liblib-overlay="zoom-menu"]'),
    ("390 asset manager", "mobile", "text=资产管理", '[data-liblib-overlay="asset"]'),
]

ASSET_PANEL_JS = """() => {
  const at = (el) => { const r = el.getBoundingClientRect();
    return [Math.round(r.x*10)/10, Math.round(r.y*10)/10,
            Math.round(r.width*10)/10, Math.round(r.height*10)/10]; };
  const own = (sel) => { const el = document.querySelector(sel); if (!el) return null;
    // display first: a display:none element has a zero rect, and reporting
    // "zero-size" for it hides the difference between "not rendered" and
    // "rendered but collapsed"
    const s = getComputedStyle(el);
    if (s.display === 'none' || s.visibility === 'hidden') return 'hidden';
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) return 'zero-size';
    const h = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
    return (h === el || el.contains(h)) ? 'own' : 'covered by <' + (h ? h.tagName.toLowerCase() : 'null') + '>';
  };
  return {
    footerCollapse: own('[data-asset-manager-collapse]'),
    headerClose: own('[aria-label="关闭资产管理"]'),
    panel: (() => { const el = document.querySelector('[data-liblib-overlay="asset"]');
      return el ? {box: at(el), z: getComputedStyle(el).zIndex} : null; })(),
    toolbars: [...document.querySelectorAll('button')]
      .filter((b) => (b.getAttribute('aria-label') || '') === '资产管理')
      .map((b) => at(b)),
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


def census(page: Page) -> dict[str, Any]:
    page.mouse.move(5, 5)
    page.wait_for_timeout(250)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal'))"
                  " el.remove(); }")
    r = dict(page.evaluate(AUDIT_JS, list(TRANSIENT_OVERLAYS)))
    r["unexpected"] = [b for b in r["covered"] if b["label"] not in KNOWN_BLOCKED]
    return r


def open_canvas(page: Page) -> None:
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__libtv_ui_store)", timeout=60_000)
    page.wait_for_timeout(1_500)


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 620,
        "title": "Census the canvas page at 390 and in its open states; stop "
                 "rendering the asset sidebar's buried collapse button on phones",
        "date": "2026-10-01",
        "sourceEvidence": [
            "no live source reading: the shared source tab is at 1600x1000 "
            "with another user in it (probe616), so this batch makes no "
            "fidelity claim",
            "/tmp/dbg620.py: the canvas page at 390 censused for the first "
            "time — 18 controls, nothing covered; 1920 has 24 and is also clean",
            "/tmp/dbg620c.py: the page's five overlay states at both widths. "
            "At 390 the zoom menu reported five toolbar buttons as covered, "
            "which is the menu working; at 390 the asset manager reported the "
            "sidebar's own collapse button, which is not",
            "/tmp/dbg620d.py: the hit chain for that button — "
            "div.fixed.bottom-[18px].z-[60] (the canvas bottom toolbar) over "
            "aside.relative.z-50 (the sidebar), plus a screenshot showing half "
            "the « glyph sticking out from under the 资产管理 pill",
        ],
        "claims": {
            "cloneDefect": [
                "at 390 the asset sidebar is a 320px full-height left panel at "
                "z-50 while the canvas page's bottom toolbar is "
                "fixed bottom-[18px] z-[60]; the sidebar's own "
                "data-asset-manager-collapse button at (16, 813.5, 22, 22) is "
                "painted under the toolbar's second cluster, so it cannot be "
                "clicked and it is visibly broken",
            ],
            "cloneDecision": [
                "the footer collapse button is not rendered below 900px. The "
                "panel keeps its header ✕ (aria-label 关闭资产管理) and the "
                "toolbar's own 资产管理 button calls the same close, so nothing "
                "is lost. Raising the sidebar above the toolbar was rejected: "
                "it would bury the toolbar's five live controls instead of one "
                "dead one",
                "the census learns [data-liblib-overlay], the attribute every "
                "transient surface on the canvas page already carries, so the "
                "exemption list does not grow one entry per surface",
            ],
            "notClaimed": [
                "anything about the source at all",
                "the canvas page's 390 header shows four of the six controls "
                "it shows at 1920 (工作流 / 故事板 / 发布与分享 / Agent and the "
                "two inert chips are hidden) — that is a pre-existing "
                "responsive decision, recorded here because the census is the "
                "first thing to count it",
                "no reading says how wide the source's asset sidebar is at "
                "phone widths; the 320px figure is the clone's own",
            ],
        },
    }
    v = Verifier()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for label, which, setup, overlay in STATES:
            viewport = WIDE if which == "wide" else MOBILE
            page = browser.new_page(viewport=viewport, device_scale_factor=1)
            console: list[str] = []
            errors: list[str] = []
            page.on("console", lambda m: console.append(f"{m.type}: {m.text}"[:200])
                    if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            tag = label.replace(" ", "-")
            try:
                open_canvas(page)
                if setup:
                    page.locator(setup).first.click(timeout=15_000)
                    page.wait_for_timeout(800)
                if overlay:
                    v.check(f"{tag}:the-overlay-opened",
                            page.locator(overlay).first.is_visible(), detail=overlay)
                r = census(page)
                v.result[f"{tag}:census"] = r
                v.check(f"{tag}:audited-a-real-number-of-controls", r["total"] >= 15,
                        detail=r["total"])
                v.check(f"{tag}:no-control-is-covered", not r["unexpected"],
                        detail=[(b["label"], b["hitLabel"], b["box"])
                                for b in r["unexpected"]])
                v.check(f"{tag}:the-only-possible-block-is-帮助",
                        all(b["label"] in KNOWN_BLOCKED for b in r["covered"]),
                        detail=[b["label"] for b in r["covered"]])
                if "asset" in label:
                    a = page.evaluate(ASSET_PANEL_JS)
                    v.result[f"{tag}:assetPanel"] = a
                    if which == "mobile":
                        v.check(f"{tag}:the-buried-collapse-button-is-gone",
                                a["footerCollapse"] == "hidden", detail=a["footerCollapse"])
                        v.check(f"{tag}:the-panel-still-has-a-working-close",
                                a["headerClose"] == "own", detail=a["headerClose"])
                    else:
                        v.check(f"{tag}:the-footer-collapse-still-works-on-desktop",
                                a["footerCollapse"] == "own", detail=a["footerCollapse"])
                noise = [c for c in console if any(k in c for k in IGNORE_CONSOLE)]
                real_console = [c for c in console
                                if not any(k in c for k in IGNORE_CONSOLE)]
                real_errors = [e for e in errors if not any(k in e for k in IGNORE_CONSOLE)]
                v.check(f"{tag}:no-page-errors", not real_errors, detail=real_errors[:4])
                v.check(f"{tag}:no-console-errors", not real_console, detail=real_console[:4])
                v.result[f"{tag}:diagnostics"] = {"consoleErrors": len(console),
                                                  "filtered": len(noise),
                                                  "pageErrors": len(errors)}
            except Exception as exc:  # noqa: BLE001 — a state may not exist
                v.check(f"{tag}:state-ran", False, detail=f"{type(exc).__name__}: {exc}")
            finally:
                page.close()
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
