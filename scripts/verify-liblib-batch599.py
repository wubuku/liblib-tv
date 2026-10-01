#!/usr/bin/env python3
"""Verify Batch 599: 打开导演台不再把时间轴缩放打回 1。

The bug.

`createDefaultTimeline()` in `src/store/directorStore.ts` declares
`zoom: 44`, chosen in batch 594 so a freshly opened desk matches the ruler
density currently visible in the source (10s ≈ 2212px; the source project read
43.7751, itself a value the user had dragged to, so 44 is an inference and not
a source fact).

That default never reached the UI. `DirectorDesk` opens the desk from a
`useEffect` that calls `openSession`, which rebuilds the runtime timeline
through `restoreDirectorProjectRuntimeSnapshotV1` in
`src/lib/directorProjectRuntimeAdapter.ts`. The project document schema
deliberately omits the view-only fields — the same function reinstates
`currentTime: 0` and `isPlaying: false` — but it reinstated `zoom` as a
**literal 1**. So every desk open overwrote 44 with 1 and the ruler sat at its
densest setting, 8s ≈ 640px.

Measured before the fix (fresh profile, 1920x1150):

    after page load          zoom = 44
    after openDirectorDesk   zoom = 1
    zoom slider value        1

and the trapping subscription pointed at
`openSession -> restoreDirectorProjectState -> restoreDirectorProjectRuntimeSnapshotV1`.

The fix introduces `DIRECTOR_TIMELINE_DEFAULT_ZOOM = 44` in the adapter (the
module `directorStore` already imports from, so declaring it in the store and
importing it back would close a cycle) and uses it in both places.

What this does NOT claim: whether the source preserves zoom across closing and
reopening its desk was never observed, so the clone still resets to the
default on open. Only the two constants were unified; no persistence of the
live value was added.

Contract asserted here:
1. the adapter reinstates the shared constant, never a literal;
2. the store's default timeline uses the same constant;
3. no `zoom: 1` literal survives in the adapter;
4. zoom is 44 after page load;
5. zoom is STILL 44 after openDirectorDesk (the regression);
6. the zoom slider reads 44;
7. closing and reopening the desk keeps 44;
8. a document round-trip (export -> import) keeps 44;
9. the batch-594 clamp still holds at both ends (0 and 100);
10. no diagnostics.
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
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch599-2026-10-01"
    / "runtime-audit.json"
)

ADAPTER = ROOT / "src/lib/directorProjectRuntimeAdapter.ts"
STORE = ROOT / "src/store/directorStore.ts"
DEFAULT_ZOOM = 44


def attach_errors(page: Page) -> list[str]:
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(f"console:{message.type}:{message.text}")
        if message.type == "error"
        and "TransformControls" not in message.text
        else None,
    )
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1920x1150", "checks": []}

    def check(name: str, ok: bool, detail: Any = None) -> None:
        result["checks"].append({"name": name, "ok": bool(ok), "detail": detail})

    # 1-3) static: one declared constant, used in both places
    adapter_source = ADAPTER.read_text()
    store_source = STORE.read_text()
    check(
        "static:adapter-uses-the-shared-constant",
        "export const DIRECTOR_TIMELINE_DEFAULT_ZOOM = 44" in adapter_source
        and "zoom: DIRECTOR_TIMELINE_DEFAULT_ZOOM," in adapter_source,
        detail="DIRECTOR_TIMELINE_DEFAULT_ZOOM declared and used in the adapter",
    )
    check(
        "static:no-zoom-1-literal-in-adapter",
        "zoom: 1," not in adapter_source,
        detail=None,
    )
    check(
        "static:store-default-uses-the-shared-constant",
        "zoom: DIRECTOR_TIMELINE_DEFAULT_ZOOM," in store_source
        and "zoom: 44," not in store_source,
        detail=None,
    )

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    # 4) the declared default survives a fresh load
    loaded = page.evaluate(
        "() => window.__director_store.getState().timeline.zoom"
    )
    result["afterLoad"] = loaded
    check("runtime:default-after-load", loaded == DEFAULT_ZOOM, detail=loaded)

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 599" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(500)

    # 5) the regression: opening the desk used to reset this to 1
    opened = page.evaluate(
        "() => window.__director_store.getState().timeline.zoom"
    )
    result["afterOpen"] = opened
    check("runtime:desk-open-keeps-default", opened == DEFAULT_ZOOM, detail=opened)

    # 6) and the control the user actually sees agrees
    slider = page.evaluate(
        """() => {
          const cluster = document.querySelector('[data-director-timeline-zoom-cluster]');
          const input = cluster && cluster.querySelector('input[type=range]');
          return input ? {value: input.value, min: input.min, max: input.max} : null;
        }"""
    )
    result["slider"] = slider
    check(
        "runtime:slider-reads-default",
        slider is not None
        and int(slider["value"]) == DEFAULT_ZOOM
        and slider["min"] == "0"
        and slider["max"] == "100",
        detail=slider,
    )

    # 7) close and reopen the same node
    node_id = page.evaluate(
        "() => window.__libtv_ui_store.getState().activeDirectorNodeId"
    )
    canvas_id = page.evaluate(
        "() => window.__libtv_ui_store.getState().activeDirectorCanvasId"
    )
    page.evaluate(
        "() => window.__libtv_ui_store.getState().closeDirectorDesk()"
    )
    page.wait_for_timeout(300)
    page.evaluate(
        "(args) => window.__libtv_ui_store.getState().openDirectorDesk(args[0], args[1])",
        [node_id, canvas_id],
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(500)
    reopened = page.evaluate(
        "() => window.__director_store.getState().timeline.zoom"
    )
    result["afterReopen"] = reopened
    check("runtime:reopen-keeps-default", reopened == DEFAULT_ZOOM, detail=reopened)

    # 8) a full document round-trip rebuilds the runtime timeline from the
    #    adapter, which is the code path that used to lose the default
    roundtrip = page.evaluate(
        """() => {
          const store = window.__director_store;
          const raw = store.getState().exportDirectorProject();
          if (!raw) return {error: 'export returned null'};
          const before = store.getState().timeline.zoom;
          store.getState().importDirectorProject(raw);
          return {before, after: store.getState().timeline.zoom};
        }"""
    )
    result["roundtrip"] = roundtrip
    check(
        "runtime:document-roundtrip-keeps-default",
        roundtrip.get("after") == DEFAULT_ZOOM
        and roundtrip.get("before") == DEFAULT_ZOOM,
        detail=roundtrip,
    )

    # 9) batch 594's clamp must still hold at both ends
    clamped = page.evaluate(
        """() => {
          const store = window.__director_store;
          store.getState().setTimelineZoom(-5);
          const low = store.getState().timeline.zoom;
          store.getState().setTimelineZoom(150);
          const high = store.getState().timeline.zoom;
          store.getState().setTimelineZoom(44);
          return {low, high, restored: store.getState().timeline.zoom};
        }"""
    )
    result["clamp"] = clamped
    check(
        "runtime:clamp-still-0-to-100",
        clamped["low"] == 0 and clamped["high"] == 100,
        detail=clamped,
    )

    check("no-console-errors", not errors, detail=errors[:5])
    return result


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1150})
        try:
            result = run_desktop(page)
        finally:
            browser.close()
    failed = [c for c in result["checks"] if not c["ok"]]
    print(
        f"Batch 599 verification: {len(result['checks']) - len(failed)}"
        f"/{len(result['checks'])} checks passed"
    )
    if failed:
        print("FAILED:", json.dumps(failed, ensure_ascii=False, indent=1))
        raise SystemExit(1)
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {AUDIT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
