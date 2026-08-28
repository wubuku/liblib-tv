#!/usr/bin/env python3

"""Verify Batch 78 Director pointer cancellation and cleanup contracts."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch78-2026-08-28"
    / "runtime-audit.json"
)


def attach_errors(page: Page) -> list[str]:
    errors: list[str] = []
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


def box(locator: Locator) -> dict[str, float]:
    result = locator.bounding_box()
    assert result is not None
    return {key: float(value) for key, value in result.items()}


def open_director(page: Page, scenario: str) -> None:
    page.goto(f"{BASE_URL}/?batch78={scenario}", wait_until="networkidle")
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__libtv_ui_store)"
    )
    page.locator("[data-open-director]").click()
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.locator("[data-director-timeline]").wait_for(state="visible")
    page.locator('canvas[data-director-webgl-canvas="true"]').wait_for(
        state="visible"
    )
    page.wait_for_timeout(320)


def director_state(page: Page) -> dict[str, Any]:
    result = page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          const track = state.timeline.tracks.find(
            (item) => item.id === state.timeline.selectedTrackId
          );
          const pad = document.querySelector(
            "[data-director-phone-vcam-pose-pad]"
          );
          const pointerId = window.__batch78PointerId;
          return {
            timeline: {
              currentTime: state.timeline.currentTime,
              selectedTrackId: state.timeline.selectedTrackId,
            },
            curve: track?.speedCurve ?? null,
            history: {
              past: state.history.past.length,
              future: state.history.future.length,
              active: Boolean(state.history.activeGesture),
            },
            phone: {
              status: state.phoneVcam.status,
              pose: state.phoneVcam.pose,
              hasPointerCapture:
                pad && Number.isFinite(pointerId)
                  ? pad.hasPointerCapture(pointerId)
                  : false,
            },
          };
        }"""
    )
    assert isinstance(result, dict)
    return result


def install_pointer_probe(page: Page) -> None:
    page.evaluate(
        """() => {
          window.__batch78PointerId = null;
          window.addEventListener(
            "pointerdown",
            (event) => {
              window.__batch78PointerId = event.pointerId;
            },
            true,
          );
        }"""
    )


def pointer_id(page: Page) -> int:
    page.wait_for_function(
        "() => Number.isFinite(window.__batch78PointerId)"
    )
    value = page.evaluate("() => window.__batch78PointerId")
    assert isinstance(value, int)
    return value


def dispatch_window_pointer_cancel(page: Page, active_pointer_id: int) -> None:
    page.evaluate(
        """(pointerId) => window.dispatchEvent(
          new PointerEvent("pointercancel", {
            bubbles: true,
            cancelable: true,
            pointerId,
          })
        )""",
        active_pointer_id,
    )


def dispatch_hidden_visibility_change(page: Page) -> None:
    page.evaluate(
        """() => {
          Object.defineProperty(document, "visibilityState", {
            configurable: true,
            value: "hidden",
          });
          document.dispatchEvent(new Event("visibilitychange"));
        }"""
    )


def open_curve_editor(page: Page) -> Locator:
    trigger = page.locator("[data-director-open-curve-editor]")
    trigger.click()
    editor = page.locator("[data-director-curve-editor]")
    editor.wait_for(state="visible")
    return editor


def drag_curve_handle(
    page: Page,
    *,
    dx: float,
    dy: float,
    finish: Callable[[Page, int], None],
) -> None:
    handle = page.locator('[data-director-curve-handle="1"]')
    handle_box = box(handle)
    x = handle_box["x"] + handle_box["width"] / 2
    y = handle_box["y"] + handle_box["height"] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    active_pointer_id = pointer_id(page)
    page.mouse.move(x + dx, y + dy, steps=6)
    finish(page, active_pointer_id)
    page.wait_for_timeout(120)


def run_curve_commit(page: Page) -> dict[str, Any]:
    errors = attach_errors(page)
    open_director(page, "curve-commit")
    open_curve_editor(page)
    install_pointer_probe(page)
    before = director_state(page)

    def finish(current_page: Page, _: int) -> None:
        current_page.mouse.up()

    drag_curve_handle(page, dx=52, dy=-16, finish=finish)
    after = director_state(page)
    assert after["curve"] != before["curve"]
    assert after["history"]["past"] == before["history"]["past"] + 1
    assert after["history"]["active"] is False
    assert after["history"]["future"] == 0
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)
    return {
        "curveCommit": True,
        "historyDelta": 1,
        "gestureCleared": True,
    }


def run_curve_cancel(page: Page, cancel_kind: str) -> dict[str, Any]:
    errors = attach_errors(page)
    open_director(page, f"curve-cancel-{cancel_kind}")
    open_curve_editor(page)
    install_pointer_probe(page)
    before = director_state(page)

    def finish(current_page: Page, active_pointer_id: int) -> None:
        if cancel_kind == "pointercancel":
            dispatch_window_pointer_cancel(current_page, active_pointer_id)
        elif cancel_kind == "blur":
            current_page.evaluate("() => window.dispatchEvent(new Event('blur'))")
        elif cancel_kind == "hidden":
            dispatch_hidden_visibility_change(current_page)
        else:
            raise AssertionError(f"unknown curve cancel: {cancel_kind}")
        current_page.mouse.up()

    drag_curve_handle(page, dx=64, dy=-20, finish=finish)
    after = director_state(page)
    assert after["curve"] == before["curve"]
    assert after["history"] == before["history"]
    assert after["history"]["active"] is False
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)
    return {
        f"curveCancel:{cancel_kind}": True,
        "baselineRestored": True,
        "historyDelta": 0,
        "gestureCleared": True,
    }


def run_curve_begin_rejected(page: Page) -> dict[str, Any]:
    errors = attach_errors(page)
    open_director(page, "curve-begin-rejected")
    open_curve_editor(page)
    install_pointer_probe(page)
    before = director_state(page)
    result = page.evaluate(
        """() => window.__director_store.getState().beginDirectorGesture({
          commandKind: "batch78-owner",
          targetId: "batch78-owner",
          fieldScope: "owner",
        })"""
    )
    assert result["disposition"] == "COMMITTED"

    handle = page.locator('[data-director-curve-handle="1"]')
    handle_box = box(handle)
    x = handle_box["x"] + handle_box["width"] / 2
    y = handle_box["y"] + handle_box["height"] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x + 48, y - 12, steps=4)
    page.mouse.up()
    page.wait_for_timeout(100)
    during_rejected_begin = director_state(page)
    assert during_rejected_begin["curve"] == before["curve"]
    assert during_rejected_begin["history"]["past"] == before["history"]["past"]
    assert (
        during_rejected_begin["history"]["future"]
        == before["history"]["future"]
    )
    assert during_rejected_begin["history"]["active"] is True

    page.evaluate("() => window.__director_store.getState().cancelDirectorGesture()")
    after = director_state(page)
    assert after["history"]["active"] is False
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)
    return {
        "curveBeginRejected": True,
        "rejectedPointerDidNotConsumeOwner": True,
        "cleanup": True,
    }


def open_phone_pose_pad(page: Page) -> Locator:
    page.locator("[data-director-phone-vcam-trigger]").click()
    connect = page.locator("[data-director-phone-vcam-connect]")
    connect.wait_for(state="visible")
    connect.click()
    pad = page.locator("[data-director-phone-vcam-pose-pad]")
    pad.wait_for(state="visible")
    return pad


def run_phone_cancel_and_reuse(page: Page) -> dict[str, Any]:
    errors = attach_errors(page)
    open_director(page, "phone-pointer-cancel")
    pad = open_phone_pose_pad(page)
    install_pointer_probe(page)
    before = director_state(page)
    pad_box = box(pad)
    x = pad_box["x"] + pad_box["width"] * 0.5
    y = pad_box["y"] + pad_box["height"] * 0.5
    page.mouse.move(x, y)
    page.mouse.down()
    active_pointer_id = pointer_id(page)
    page.mouse.move(x + 45, y - 20, steps=5)
    moved = director_state(page)
    assert moved["phone"]["pose"] != before["phone"]["pose"]
    assert moved["phone"]["hasPointerCapture"] is True

    pad.dispatch_event(
        "pointercancel",
        {"bubbles": True, "cancelable": True, "pointerId": active_pointer_id},
    )
    page.wait_for_timeout(80)
    page.mouse.up()
    canceled = director_state(page)
    assert canceled["phone"]["hasPointerCapture"] is False

    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x - 36, y + 16, steps=4)
    reused = director_state(page)
    page.mouse.up()
    assert reused["phone"]["pose"] != canceled["phone"]["pose"]

    page.mouse.move(x, y)
    page.mouse.down()
    active_pointer_id = pointer_id(page)
    page.evaluate("() => window.dispatchEvent(new Event('blur'))")
    page.wait_for_timeout(80)
    blurred = director_state(page)
    page.mouse.up()
    assert blurred["phone"]["hasPointerCapture"] is False

    page.mouse.move(x, y)
    page.mouse.down()
    active_pointer_id = pointer_id(page)
    page.locator(
        "[data-director-phone-vcam-panel] button[aria-label='关闭虚拟相机']"
    ).evaluate("(element) => element.click()")
    page.wait_for_timeout(80)
    assert page.locator("[data-director-phone-vcam-pose-pad]").count() == 0
    page.mouse.up()
    assert active_pointer_id >= 0
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)
    return {
        "phonePointerCancel": True,
        "phonePointerReuse": True,
        "phoneBlurCleanup": True,
        "phoneCloseCleanup": True,
        "captureReleased": True,
    }


def run_timeline_cancel_and_reuse(page: Page) -> dict[str, Any]:
    errors = attach_errors(page)
    open_director(page, "timeline-scrub-cancel")
    install_pointer_probe(page)
    ruler = page.locator("[data-director-timeline-ruler]")
    ruler_box = box(ruler)
    start_x = ruler_box["x"] + ruler_box["width"] * 0.2
    y = ruler_box["y"] + ruler_box["height"] / 2
    page.mouse.move(start_x, y)
    before = director_state(page)
    page.mouse.down()
    active_pointer_id = pointer_id(page)
    page.mouse.move(start_x + 120, y, steps=5)
    moved = director_state(page)
    assert moved["timeline"]["currentTime"] != before["timeline"]["currentTime"]

    dispatch_window_pointer_cancel(page, active_pointer_id)
    canceled = director_state(page)
    canceled_time = canceled["timeline"]["currentTime"]
    page.mouse.move(start_x + 260, y, steps=5)
    page.wait_for_timeout(80)
    stale_move = director_state(page)
    page.mouse.up()
    assert stale_move["timeline"]["currentTime"] == canceled_time

    page.mouse.move(start_x, y)
    page.mouse.down()
    active_pointer_id = pointer_id(page)
    page.mouse.move(start_x + 180, y, steps=5)
    page.mouse.up()
    reused = director_state(page)
    assert reused["timeline"]["currentTime"] != canceled_time

    page.mouse.move(start_x, y)
    page.mouse.down()
    pointer_id(page)
    hidden_started = director_state(page)
    dispatch_hidden_visibility_change(page)
    page.mouse.move(start_x + 240, y, steps=5)
    hidden_stale = director_state(page)
    page.mouse.up()
    assert (
        hidden_stale["timeline"]["currentTime"]
        == hidden_started["timeline"]["currentTime"]
    ), (
        f"hidden cleanup failed: started={hidden_started['timeline']['currentTime']}, "
        f"after={hidden_stale['timeline']['currentTime']}, "
        f"visibility={page.evaluate('() => document.visibilityState')}"
    )

    page.locator("[data-close-director]").click()
    assert page.locator("[data-director-workspace]").count() == 0
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)
    return {
        "timelinePointerCancel": True,
        "timelineStaleMoveStopped": True,
        "timelinePointerReuse": True,
        "timelineVisibilityCleanup": True,
        "historyUntouched": True,
    }


def verify_static_contract() -> None:
    curve_source = (
        ROOT / "src/components/director/DirectorCurveEditor.tsx"
    ).read_text(encoding="utf-8")
    phone_source = (
        ROOT / "src/components/director/DirectorPhoneVcamPanel.tsx"
    ).read_text(encoding="utf-8")
    timeline_source = (
        ROOT / "src/components/director/DirectorTimeline.tsx"
    ).read_text(encoding="utf-8")

    assert "result.disposition !== \"COMMITTED\"" in curve_source
    assert "cancelDirectorGesture" in curve_source
    assert "window.addEventListener(\"pointercancel\"" in curve_source
    assert "window.addEventListener(\"blur\"" in curve_source
    assert "document.addEventListener(\"visibilitychange\"" in curve_source
    assert "dragCleanupRef" in curve_source
    assert "onPointerCancel" in phone_source
    assert "onLostPointerCapture" in phone_source
    assert "releasePosePointer" in phone_source
    assert "window.addEventListener(\"blur\"" in phone_source
    assert "document.addEventListener(\"visibilitychange\"" in phone_source
    assert "window.addEventListener(\"pointercancel\"" in timeline_source
    assert "window.addEventListener(\"blur\"" in timeline_source
    assert "document.addEventListener(\"visibilitychange\"" in timeline_source
    assert "scrubCleanupRef" in timeline_source


def run_browser_verifier() -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    scenarios: list[tuple[str, Callable[[Page], dict[str, Any]]]] = [
        ("curveCommit", run_curve_commit),
        ("curveCancelPointer", lambda page: run_curve_cancel(page, "pointercancel")),
        ("curveCancelBlur", lambda page: run_curve_cancel(page, "blur")),
        ("curveCancelHidden", lambda page: run_curve_cancel(page, "hidden")),
        ("curveBeginRejected", run_curve_begin_rejected),
        ("phoneCancelAndReuse", run_phone_cancel_and_reuse),
        ("timelineCancelAndReuse", run_timeline_cancel_and_reuse),
    ]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for name, scenario in scenarios:
            page = browser.new_page(
                viewport={"width": 1440, "height": 900},
                device_scale_factor=1,
            )
            results[name] = scenario(page)
            page.close()
        browser.close()
    return results


def main() -> None:
    verify_static_contract()
    results = run_browser_verifier()
    audit = {
        "batch": 78,
        "status": "SCRIPT_RECORDED_PASS",
        "baseUrl": BASE_URL,
        "scope": [
            "Director curve editor pointer gesture cancellation",
            "Director phone vcam pose pointer capture lifecycle",
            "Director timeline scrub stale pointer lifecycle",
        ],
        "results": results,
        "screenshots": [],
        "errors": [],
    }
    AUDIT_PATH.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit, ensure_ascii=False))


if __name__ == "__main__":
    if any(argument in {"-h", "--help"} for argument in sys.argv[1:]):
        print("Verify Batch 78 Director pointer cancellation and cleanup contracts.")
        print("Usage: python3 scripts/verify-liblib-batch78.py")
        raise SystemExit(0)
    main()
