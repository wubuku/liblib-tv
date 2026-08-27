import json
import os
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:3000")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch65-2026-08-27"
    / "runtime-audit.json"
)
DESKTOP_VIEWPORT = {"x": -583.8, "y": 260.8, "zoom": 0.526}
COMPACT_VIEWPORT = {"x": 17, "y": 128, "zoom": 0.28}


def attach_errors(page: Page):
    errors = []
    page.on(
        "console",
        lambda message: errors.append(f"console:{message.type}:{message.text}")
        if message.type == "error"
        else None,
    )
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.on(
        "requestfailed",
        lambda request: errors.append(
            f"requestfailed:{request.method}:{request.url}:{request.failure}"
        ),
    )
    return errors


def assert_no_overflow(page: Page):
    assert page.evaluate(
        "() => document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )
    assert page.evaluate(
        "() => document.body.scrollWidth <= document.body.clientWidth"
    )


def assert_viewport(actual, expected, tolerance=0.001):
    assert actual is not None, actual
    assert abs(actual["x"] - expected["x"]) <= tolerance, (actual, expected)
    assert abs(actual["y"] - expected["y"]) <= tolerance, (actual, expected)
    assert abs(actual["zoom"] - expected["zoom"]) <= tolerance, (actual, expected)


def wait_for_viewport(page: Page, canvas_id: str, expected):
    page.wait_for_function(
        """({canvasId, expected}) => {
          const canvas = window.__libtv_store
            .getState()
            .canvases.find((item) => item.id === canvasId);
          if (!canvas) return false;
          return (
            Math.abs(canvas.viewport.x - expected.x) <= 0.001 &&
            Math.abs(canvas.viewport.y - expected.y) <= 0.001 &&
            Math.abs(canvas.viewport.zoom - expected.zoom) <= 0.000001
          );
        }""",
        arg={"canvasId": canvas_id, "expected": expected},
    )


def wait_for_owner(page: Page, canvas_id: str, owner: str):
    page.wait_for_function(
        """({canvasId, owner}) =>
          window.__libtv_get_viewport_ownership?.()[canvasId] === owner""",
        arg={"canvasId": canvas_id, "owner": owner},
    )


def open_page(browser, width: int, height: int):
    page = browser.new_page(
        viewport={"width": width, "height": height},
        device_scale_factor=1,
    )
    errors = attach_errors(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_function(
        """() =>
          Boolean(window.__libtv_store) &&
          Boolean(window.__libtv_apply_viewport_event) &&
          Boolean(window.__libtv_get_viewport_ownership) &&
          Boolean(document.querySelector("[data-libtv-react-flow-host]"))"""
    )
    page.wait_for_timeout(220)
    return page, errors


def runtime_snapshot(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          const activeCanvas = state.getActiveCanvas();
          return {
            activeCanvasId: state.activeCanvasId,
            viewports: Object.fromEntries(
              state.canvases.map((canvas) => [canvas.id, canvas.viewport]),
            ),
            ownership: window.__libtv_get_viewport_ownership?.() || {},
            transform:
              document.querySelector(".react-flow__viewport")?.style.transform || null,
            zoomLabel:
              document.querySelector('[data-viewport-menu-trigger="zoom"]')
                ?.textContent?.trim() || null,
            log: [...window.__libtv_viewport_owner_log],
            graph: {
              canvases: state.canvases.map((canvas) => ({
                id: canvas.id,
                nodes: canvas.nodes.map((node) => ({
                  id: node.id,
                  type: node.type,
                  position: node.position,
                  parentId: node.parentId || null,
                })),
                edges: canvas.edges.map((edge) => ({
                  id: edge.id,
                  source: edge.source,
                  target: edge.target,
                })),
              })),
              selectedNodeIds: state.selectedNodeIds,
              selectedNodeId: state.selectedNodeId,
              selectedEdgeIds: state.selectedEdgeIds,
              historyLengths: Object.fromEntries(
                Object.entries(state.historyByCanvas).map(([canvasId, history]) => [
                  canvasId,
                  { past: history.past.length, future: history.future.length },
                ]),
              ),
            },
            activeViewport: activeCanvas?.viewport || null,
          };
        }"""
    )


def run_pure_helper(page: Page):
    result = page.evaluate(
        """() => ({
          bootstrap: window.__libtv_plan_responsive_viewport_projection(
            { x: 12, y: 24, zoom: 1.25 },
            { x: 17, y: 128, zoom: 0.28 },
            "bootstrap",
          ),
          stable: window.__libtv_plan_responsive_viewport_projection(
            { x: 12, y: 24, zoom: 1.25 },
            { x: 17, y: 128, zoom: 0.28 },
            "stable",
          ),
          stableIgnoresInvalidBootstrap:
            window.__libtv_plan_responsive_viewport_projection(
              { x: 12, y: 24, zoom: 1.25 },
              { x: Number.NaN, y: 128, zoom: 0.28 },
              "stable",
            ),
          invalidStored: window.__libtv_plan_responsive_viewport_projection(
            { x: Number.NaN, y: 24, zoom: 1.25 },
            { x: 17, y: 128, zoom: 0.28 },
            "stable",
          ),
          invalidBootstrap: window.__libtv_plan_responsive_viewport_projection(
            { x: 12, y: 24, zoom: 1.25 },
            { x: 17, y: 128, zoom: 9 },
            "bootstrap",
          ),
          invalidZoomLow: window.__libtv_plan_responsive_viewport_projection(
            { x: 12, y: 24, zoom: 0.09 },
            { x: 17, y: 128, zoom: 0.28 },
            "stable",
          ),
        })"""
    )
    assert result["bootstrap"] == {
        "viewport": COMPACT_VIEWPORT,
        "ownership": "bootstrap",
        "shouldWriteStore": True,
    }, result
    expected_stable = {
        "viewport": {"x": 12, "y": 24, "zoom": 1.25},
        "ownership": "stable",
        "shouldWriteStore": False,
    }
    assert result["stable"] == expected_stable, result
    assert result["stableIgnoresInvalidBootstrap"] == expected_stable, result
    assert result["invalidStored"] is None, result
    assert result["invalidBootstrap"] is None, result
    assert result["invalidZoomLow"] is None, result
    return result


def run_fresh_bootstrap(browser, width: int, height: int, expected):
    page, errors = open_page(browser, width, height)
    snapshot = runtime_snapshot(page)
    assert snapshot["activeCanvasId"] == "canvas-2", snapshot
    assert_viewport(snapshot["activeViewport"], expected)
    assert snapshot["ownership"] == {"canvas-2": "bootstrap"}, snapshot
    assert snapshot["log"][-1]["reason"] == "bootstrap-applied", snapshot
    assert snapshot["log"][-1]["ownership"] == "bootstrap", snapshot
    assert snapshot["zoomLabel"] == f"{round(expected['zoom'] * 100)}%", snapshot
    assert_no_overflow(page)
    assert not errors, errors
    page.close()
    return snapshot


def run_untouched_breakpoint(browser):
    page, errors = open_page(browser, 929, 874)
    before = runtime_snapshot(page)
    assert_viewport(before["activeViewport"], DESKTOP_VIEWPORT)

    page.set_viewport_size({"width": 390, "height": 844})
    wait_for_viewport(page, "canvas-2", COMPACT_VIEWPORT)
    compact = runtime_snapshot(page)
    assert compact["ownership"]["canvas-2"] == "bootstrap", compact
    assert compact["graph"] == before["graph"], (before, compact)

    page.set_viewport_size({"width": 929, "height": 874})
    wait_for_viewport(page, "canvas-2", DESKTOP_VIEWPORT)
    restored = runtime_snapshot(page)
    assert restored["ownership"]["canvas-2"] == "bootstrap", restored
    assert restored["graph"] == before["graph"], (before, restored)
    reasons = [entry["reason"] for entry in restored["log"]]
    assert reasons.count("bootstrap-applied") >= 3, reasons
    assert "viewport-accepted" not in reasons, reasons
    assert_no_overflow(page)
    assert not errors, errors
    page.close()
    return {
        "before": before,
        "compact": compact,
        "restored": restored,
    }


def run_projection_echo(browser):
    page, errors = open_page(browser, 929, 874)
    before = runtime_snapshot(page)
    result = page.evaluate(
        """(viewport) =>
          window.__libtv_apply_viewport_event("canvas-2", viewport)""",
        DESKTOP_VIEWPORT,
    )
    after = runtime_snapshot(page)
    assert result == {"status": "committed", "reason": "projection-echo"}, result
    assert after["viewports"] == before["viewports"], (before, after)
    assert after["ownership"]["canvas-2"] == "bootstrap", after
    assert after["graph"] == before["graph"], (before, after)

    page.set_viewport_size({"width": 390, "height": 844})
    wait_for_viewport(page, "canvas-2", COMPACT_VIEWPORT)
    resized = runtime_snapshot(page)
    assert resized["ownership"]["canvas-2"] == "bootstrap", resized
    assert_no_overflow(page)
    assert not errors, errors
    page.close()
    return {"result": result, "after": after, "resized": resized}


def run_user_owned_breakpoint(browser):
    page, errors = open_page(browser, 929, 874)
    before = runtime_snapshot(page)
    page.locator('[data-viewport-menu-trigger="zoom"]').click()
    page.locator('[data-zoom-action="in"]').click()
    wait_for_owner(page, "canvas-2", "stable")
    page.wait_for_timeout(320)
    stable = runtime_snapshot(page)
    assert stable["activeViewport"]["zoom"] > DESKTOP_VIEWPORT["zoom"], stable
    assert stable["graph"] == before["graph"], (before, stable)

    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(260)
    compact_host = runtime_snapshot(page)
    assert_viewport(compact_host["activeViewport"], stable["activeViewport"])
    assert compact_host["ownership"]["canvas-2"] == "stable", compact_host
    assert compact_host["graph"] == before["graph"], (before, compact_host)
    assert compact_host["log"][-1]["reason"] == "stable-restored", compact_host
    assert_no_overflow(page)
    assert not errors, errors
    page.close()
    return {"stable": stable, "compactHost": compact_host}


def open_canvas_menu(page: Page):
    page.locator("[data-canvas-trigger]").click()
    menu = page.locator('[data-liblib-overlay="canvas-dropdown"]')
    menu.wait_for(state="visible")
    return menu


def switch_canvas(page: Page, canvas_id: str):
    menu = open_canvas_menu(page)
    menu.locator(f'[data-canvas-row="{canvas_id}"] button').first.click()
    page.wait_for_function(
        "(canvasId) => window.__libtv_store.getState().activeCanvasId === canvasId",
        arg=canvas_id,
    )


def run_canvas_restore(browser):
    page, errors = open_page(browser, 929, 874)
    before = runtime_snapshot(page)
    canvas_two_viewport = {"x": -321.5, "y": 144.25, "zoom": 0.75}
    canvas_one_viewport = {"x": 111, "y": 222, "zoom": 1.25}

    accepted = page.evaluate(
        """(viewport) =>
          window.__libtv_apply_viewport_event("canvas-2", viewport)""",
        canvas_two_viewport,
    )
    assert accepted == {"status": "committed", "reason": "viewport-accepted"}
    wait_for_viewport(page, "canvas-2", canvas_two_viewport)
    page.evaluate(
        """(viewport) => {
          window.__libtv_store.setState((state) => ({
            canvases: state.canvases.map((canvas) =>
              canvas.id === "canvas-1" ? { ...canvas, viewport } : canvas,
            ),
          }));
        }""",
        canvas_one_viewport,
    )

    switch_canvas(page, "canvas-1")
    wait_for_viewport(page, "canvas-1", canvas_one_viewport)
    canvas_one = runtime_snapshot(page)
    assert_viewport(canvas_one["activeViewport"], canvas_one_viewport)
    assert canvas_one["ownership"]["canvas-1"] == "stable", canvas_one

    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(240)
    canvas_one_compact_host = runtime_snapshot(page)
    assert_viewport(canvas_one_compact_host["activeViewport"], canvas_one_viewport)

    switch_canvas(page, "canvas-2")
    wait_for_viewport(page, "canvas-2", canvas_two_viewport)
    canvas_two = runtime_snapshot(page)
    assert_viewport(canvas_two["activeViewport"], canvas_two_viewport)
    assert canvas_two["ownership"]["canvas-2"] == "stable", canvas_two
    assert canvas_two["graph"] == before["graph"], (before, canvas_two)
    assert_no_overflow(page)
    assert not errors, errors
    page.close()
    return {
        "accepted": accepted,
        "canvasOne": canvas_one,
        "canvasOneCompactHost": canvas_one_compact_host,
        "canvasTwoRestored": canvas_two,
    }


def run_callback_guards(browser):
    page, errors = open_page(browser, 929, 874)
    before = runtime_snapshot(page)
    stale = page.evaluate(
        """() =>
          window.__libtv_apply_viewport_event(
            "canvas-1",
            { x: 999, y: 888, zoom: 2 },
          )"""
    )
    invalid = page.evaluate(
        """() =>
          window.__libtv_apply_viewport_event(
            "canvas-2",
            { x: 999, y: 888, zoom: 9 },
          )"""
    )
    after = runtime_snapshot(page)
    assert stale == {"status": "skipped", "reason": "canvas-changed"}, stale
    assert invalid == {"status": "skipped", "reason": "invalid-viewport"}, invalid
    assert after["viewports"] == before["viewports"], (before, after)
    assert after["ownership"] == before["ownership"], (before, after)
    assert after["transform"] == before["transform"], (before, after)
    assert after["zoomLabel"] == before["zoomLabel"], (before, after)
    assert after["graph"] == before["graph"], (before, after)
    assert after["log"][-2]["viewport"] == {"x": 999, "y": 888, "zoom": 2}
    assert after["log"][-1]["viewport"] is None
    assert_no_overflow(page)
    assert not errors, errors
    page.close()
    return {"stale": stale, "invalid": invalid, "before": before, "after": after}


def main():
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        pure_page, pure_errors = open_page(browser, 929, 874)
        pure_helper = run_pure_helper(pure_page)
        assert_no_overflow(pure_page)
        assert not pure_errors, pure_errors
        pure_page.close()

        desktop_bootstrap = run_fresh_bootstrap(
            browser,
            929,
            874,
            DESKTOP_VIEWPORT,
        )
        mobile_bootstrap = run_fresh_bootstrap(
            browser,
            390,
            844,
            COMPACT_VIEWPORT,
        )
        untouched_breakpoint = run_untouched_breakpoint(browser)
        projection_echo = run_projection_echo(browser)
        user_owned_breakpoint = run_user_owned_breakpoint(browser)
        canvas_restore = run_canvas_restore(browser)
        callback_guards = run_callback_guards(browser)
        browser.close()

    audit = {
        "batch": 65,
        "date": "2026-08-27",
        "url": URL,
        "scope": "clone-owned responsive viewport bootstrap ownership",
        "sourceParityClaim": False,
        "screenshotsReused": True,
        "pureHelper": pure_helper,
        "desktopBootstrap": desktop_bootstrap,
        "mobileBootstrap": mobile_bootstrap,
        "untouchedBreakpoint": untouched_breakpoint,
        "projectionEcho": projection_echo,
        "userOwnedBreakpoint": user_owned_breakpoint,
        "canvasRestore": canvas_restore,
        "callbackGuards": callback_guards,
        "acceptance": {
            "desktopAndMobileBootstrapExact": True,
            "untouchedBreakpointCanReproject": True,
            "userViewportSurvivesBreakpoint": True,
            "targetCanvasStoredViewportRestored": True,
            "nonDemoCanvasNeverUsesDemoPreset": True,
            "projectionEchoKeepsBootstrapOwnership": True,
            "staleAndInvalidCallbacksZeroMutation": True,
            "graphHistorySelectionZeroMutation": True,
            "noOverflow": True,
            "browserDiagnosticsClean": True,
        },
    }
    AUDIT_PATH.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "Batch 65 Playwright verification passed: pure responsive planning, "
        "desktop/mobile bootstrap, untouched and user-owned breakpoint behavior, "
        "projection echo, per-canvas restore, stale/invalid callback guards, "
        "graph/history/selection isolation, overflow and diagnostics."
    )


if __name__ == "__main__":
    main()
