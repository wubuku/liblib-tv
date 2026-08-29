#!/usr/bin/env python3

"""Verify the Batch 94 Director focus containment and keyboard boundary."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch94-2026-08-29"
    / "runtime-audit.json"
)


def attach_errors(page: Page) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    phase = ["startup"]
    page.on(
        "console",
        lambda message: errors.append(
            f"{phase[0]}:console:{message.type}:{message.text}"
        )
        if message.type == "error"
        else None,
    )
    page.on(
        "pageerror",
        lambda error: errors.append(
            f"{phase[0]}:pageerror:{error}\n{error.stack or 'stack unavailable'}"
        ),
    )
    page.on(
        "requestfailed",
        lambda request: errors.append(
            f"{phase[0]}:requestfailed:{request.method}:{request.url}:"
            f"{request.failure}"
        ),
    )
    return errors, phase


def wait_for_app(page: Page) -> None:
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__director_store)"
    )
    page.wait_for_selector("[data-libtv-react-flow-host]")


def clear_director_persistence(page: Page) -> None:
    page.evaluate(
        """() => {
          for (const key of Object.keys(localStorage)) {
            if (key.startsWith("liblib-tv-director-project-v1:")) {
              localStorage.removeItem(key);
            }
          }
          localStorage.removeItem("liblib-tv-director-local-model-library-v1");
        }"""
    )


def open_director(page: Page, query: str) -> Locator:
    page.goto(f"{BASE_URL}/{query}", wait_until="networkidle")
    wait_for_app(page)
    clear_director_persistence(page)
    page.reload(wait_until="networkidle")
    wait_for_app(page)
    trigger = page.locator("[data-open-director]").first
    trigger.wait_for(state="visible")
    trigger.click()
    workspace = page.locator("[data-director-workspace]")
    workspace.wait_for(state="visible")
    page.locator('canvas[data-director-webgl-canvas="true"]').wait_for(
        state="visible"
    )
    page.wait_for_timeout(220)
    return trigger


def assert_no_horizontal_overflow(page: Page, label: str) -> None:
    dimensions = page.evaluate(
        """() => ({
          document: {
            scrollWidth: document.documentElement.scrollWidth,
            clientWidth: document.documentElement.clientWidth,
          },
          body: {
            scrollWidth: document.body.scrollWidth,
            clientWidth: document.body.clientWidth,
          },
        })"""
    )
    assert (
        dimensions["document"]["scrollWidth"]
        <= dimensions["document"]["clientWidth"] + 1
    ), f"{label} document overflow: {dimensions}"
    assert (
        dimensions["body"]["scrollWidth"] <= dimensions["body"]["clientWidth"] + 1
    ), f"{label} body overflow: {dimensions}"


def active_element(page: Page) -> dict[str, Any]:
    return page.evaluate(
        """() => {
          const element = document.activeElement;
          if (!(element instanceof HTMLElement)) return {tag: null};
          return {
            tag: element.tagName.toLowerCase(),
            id: element.id,
            ariaLabel: element.getAttribute("aria-label"),
            dataScope: element.closest("[data-director-focus-scope]")?.getAttribute(
              "data-director-focus-scope"
            ) ?? null,
            isWorkspace: Boolean(element.closest("[data-director-workspace]")),
            isCanvasRoot: element.matches("[data-libtv-canvas-focus-root]"),
          };
        }"""
    )


def focusable_snapshot(page: Page, selector: str) -> list[dict[str, Any]]:
    return page.evaluate(
        """(selector) => {
          const root = document.querySelector(selector);
          if (!(root instanceof HTMLElement)) return [];
          const selectorText = [
            "a[href]", "area[href]", "button", "input", "select", "textarea",
            "iframe", "object", "embed", "[contenteditable='true']", "[tabindex]"
          ].join(",");
          return [...root.querySelectorAll(selectorText)]
            .filter((element) => {
              if (!(element instanceof HTMLElement)) return false;
              if (element.tabIndex < 0) return false;
              if (element.matches("[hidden], [aria-hidden='true'], [inert]")) {
                return false;
              }
              if (element.closest("[hidden], [aria-hidden='true'], [inert]")) {
                return false;
              }
              if ("disabled" in element && element.disabled) return false;
              if (element.getAttribute("type") === "hidden") return false;
              const style = getComputedStyle(element);
              return style.display !== "none" &&
                style.visibility !== "hidden" &&
                element.getClientRects().length > 0;
            })
            .map((element) => ({
              tag: element.tagName.toLowerCase(),
              id: element.id,
              ariaLabel: element.getAttribute("aria-label"),
              testId: [...element.attributes]
                .find((attribute) => attribute.name.startsWith("data-"))
                ?.name ?? null,
            }));
        }""",
        selector,
    )


def assert_active_inside(page: Page, selector: str, label: str) -> None:
    inside = page.locator(selector).evaluate(
        """(root) => root.contains(document.activeElement)"""
    )
    assert inside, f"{label} activeElement escaped: {active_element(page)}"


def run_workspace_tab_cycle(page: Page) -> dict[str, Any]:
    workspace = page.locator("[data-director-workspace]")
    workspace.focus()
    focusables = focusable_snapshot(page, "[data-director-workspace]")
    assert focusables, "Director workspace needs at least one tabbable control"

    forward: list[dict[str, Any]] = []
    for _ in range(len(focusables) + 1):
        page.keyboard.press("Tab")
        assert_active_inside(page, "[data-director-workspace]", "workspace Tab")
        forward.append(active_element(page))

    workspace.focus()
    page.keyboard.press("Shift+Tab")
    assert_active_inside(page, "[data-director-workspace]", "workspace reverse Tab")
    reverse_first = active_element(page)

    return {
        "focusableCount": len(focusables),
        "forwardSamples": forward[:4],
        "forwardWrapped": forward[-1] == forward[0],
        "reverseFirst": reverse_first,
        "reverseStayedInside": True,
    }


def run_desktop(page: Page) -> dict[str, Any]:
    errors, phase = attach_errors(page)
    phase[0] = "desktop-bootstrap"
    trigger = open_director(page, "?batch94=desktop")
    workspace = page.locator("[data-director-workspace]")

    initial = active_element(page)
    assert initial["isWorkspace"], initial
    assert workspace.get_attribute("data-director-focus-scope") == "workspace"
    assert workspace.get_attribute("data-director-focus-state") == "workspace"
    assert_no_horizontal_overflow(page, "Batch 94 desktop bootstrap")

    phase[0] = "desktop-tab-cycle"
    tab_cycle = run_workspace_tab_cycle(page)

    phase[0] = "desktop-editable"
    name_input = page.locator("[data-director-inspector] input").first
    before = page.evaluate(
        "() => ({objects: window.__director_store.getState().objects.length, past: window.__director_store.getState().history.past.length})"
    )
    name_input.fill("Batch 94 focus input")
    name_input.press("Delete")
    after = page.evaluate(
        "() => ({objects: window.__director_store.getState().objects.length, past: window.__director_store.getState().history.past.length})"
    )
    assert before["objects"] == after["objects"], (before, after)
    assert name_input.input_value() == "Batch 94 focus input", name_input.input_value()
    page.keyboard.press("Escape")
    assert workspace.is_visible()

    phase[0] = "desktop-close-return"
    workspace.locator("[data-close-director]").first.click()
    workspace.wait_for(state="hidden")
    assert trigger.evaluate(
        "() => document.activeElement === document.querySelector('[data-open-director]')"
    )

    trigger.click()
    workspace.wait_for(state="visible")
    page.wait_for_timeout(160)
    page.keyboard.press("Escape")
    workspace.wait_for(state="hidden")
    assert trigger.evaluate(
        "() => document.activeElement === document.querySelector('[data-open-director]')"
    )

    return {
        "viewport": {"width": 1440, "height": 900},
        "initialFocusInsideWorkspace": True,
        "workspaceTabCycle": tab_cycle,
        "editableBoundary": True,
        "closeButtonFocusReturn": True,
        "escapeFocusReturn": True,
        "noHorizontalOverflow": True,
        "diagnostics": {
            "consoleErrors": len([item for item in errors if ":console:" in item]),
            "pageErrors": len([item for item in errors if ":pageerror:" in item]),
            "requestFailures": len(
                [item for item in errors if ":requestfailed:" in item]
            ),
            "details": errors,
        },
    }


def run_mobile_drawer(
    page: Page,
    trigger_selector: str,
    panel_selector: str,
    scope_name: str,
    close_with: str,
) -> dict[str, Any]:
    trigger = page.locator(trigger_selector)
    trigger.click()
    panel = page.locator(panel_selector)
    panel.wait_for(state="visible")
    page.wait_for_timeout(220)

    assert panel.get_attribute("data-director-mobile-panel-state") == "open"
    assert panel.get_attribute("data-director-focus-scope") == scope_name
    assert active_element(page)["dataScope"] == scope_name, active_element(page)
    assert panel.get_attribute("aria-hidden") is None
    assert panel.get_attribute("inert") is None

    focusables = focusable_snapshot(page, panel_selector)
    assert focusables, f"{scope_name} drawer needs a tabbable control"
    samples: list[dict[str, Any]] = []
    for _ in range(len(focusables) + 1):
        page.keyboard.press("Tab")
        assert_active_inside(page, panel_selector, f"{scope_name} drawer Tab")
        samples.append(active_element(page))

    other_panel_selector = (
        "[aria-label='属性']"
        if scope_name == "tree"
        else "[aria-label='场景对象']"
    )
    other_panel = page.locator(other_panel_selector)
    assert other_panel.get_attribute("aria-hidden") == "true"
    assert other_panel.get_attribute("inert") == ""

    if close_with == "backdrop":
        backdrop = page.locator("button[aria-label='关闭移动端面板']")
        if scope_name == "tree":
            backdrop.click(position={"x": 350, "y": 420})
        else:
            backdrop.click(position={"x": 40, "y": 420})
    else:
        page.keyboard.press("Escape")
    panel.wait_for(state="visible")
    assert panel.get_attribute("data-director-mobile-panel-state") == "closed"
    assert trigger.evaluate(
        """(element) => document.activeElement === element"""
    )

    return {
        "scope": scope_name,
        "focusableCount": len(focusables),
        "initialFocus": True,
        "tabCycleStayedInside": True,
        "tabSamples": samples[:4],
        "inactivePeerIsInert": True,
        "closeFocusReturn": True,
        "closeMethod": close_with,
    }


def run_mobile(page: Page) -> dict[str, Any]:
    errors, phase = attach_errors(page)
    phase[0] = "mobile-bootstrap"
    open_director(page, "?batch94=mobile")
    workspace = page.locator("[data-director-workspace]")
    assert_no_horizontal_overflow(page, "Batch 94 mobile bootstrap")

    phase[0] = "mobile-tree"
    tree = run_mobile_drawer(
        page,
        "button[aria-label='打开场景对象']",
        "[aria-label='场景对象']",
        "tree",
        "backdrop",
    )

    phase[0] = "mobile-inspector"
    inspector = run_mobile_drawer(
        page,
        "button[aria-label='打开属性面板']",
        "[aria-label='属性']",
        "inspector",
        "escape",
    )

    phase[0] = "mobile-collapsed"
    page.locator("[data-director-panels-toggle]").click()
    page.wait_for_timeout(160)
    for selector in ("[aria-label='场景对象']", "[aria-label='属性']"):
        panel = page.locator(selector)
        assert panel.get_attribute("aria-hidden") == "true"
        assert panel.get_attribute("inert") == ""
    assert workspace.get_attribute("data-director-focus-state") == "workspace"
    assert_no_horizontal_overflow(page, "Batch 94 mobile collapsed")

    return {
        "viewport": {"width": 390, "height": 844},
        "treeDrawer": tree,
        "inspectorDrawer": inspector,
        "collapsedRailsAreInert": True,
        "noHorizontalOverflow": True,
        "diagnostics": {
            "consoleErrors": len([item for item in errors if ":console:" in item]),
            "pageErrors": len([item for item in errors if ":pageerror:" in item]),
            "requestFailures": len(
                [item for item in errors if ":requestfailed:" in item]
            ),
            "details": errors,
        },
    }


def verify_static_contract() -> dict[str, bool]:
    desk_source = (
        ROOT / "src/components/director/DirectorDesk.tsx"
    ).read_text(encoding="utf-8")
    focus_source = (
        ROOT / "src/components/director/useDirectorFocusContainment.ts"
    ).read_text(encoding="utf-8")
    assertions = {
        "workspaceFocusScope": 'data-director-focus-scope="workspace"' in desk_source,
        "mobileTreeFocusScope": 'activeMobileFocusScope === "tree"' in desk_source
        and "treePanelRef" in desk_source,
        "mobileInspectorFocusScope": 'activeMobileFocusScope === "inspector"'
        in desk_source
        and "inspectorPanelRef" in desk_source,
        "inertRails": "inert={treeMobileInactive" in desk_source
        and "inert={inspectorMobileInactive" in desk_source,
        "tabContainment": 'event.key !== "Tab"' in focus_source
        and "preventDefault" in focus_source,
        "focusReturn": "returnTargetRef" in focus_source
        and "canvasRootSelector" in focus_source,
    }
    assert all(assertions.values()), assertions
    return assertions


def main() -> None:
    static_contract = verify_static_contract()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        desktop_context = browser.new_context(
            viewport={"width": 1440, "height": 900}
        )
        desktop_result = run_desktop(desktop_context.new_page())
        desktop_context.close()

        mobile_context = browser.new_context(
            viewport={"width": 390, "height": 844}
        )
        mobile_result = run_mobile(mobile_context.new_page())
        mobile_context.close()
        browser.close()

    for result in (desktop_result, mobile_result):
        assert result["diagnostics"]["consoleErrors"] == 0, result["diagnostics"]
        assert result["diagnostics"]["pageErrors"] == 0, result["diagnostics"]
        assert result["diagnostics"]["requestFailures"] == 0, result["diagnostics"]

    audit = {
        "batch": 94,
        "status": "SCRIPT_RECORDED_PASS",
        "baseUrl": BASE_URL,
        "sourceExact": False,
        "contract": {
            "scope": "clone-owned Director focus containment and keyboard boundary",
            "screenshotsWritten": False,
            "screenshotRecognition": False,
            "remoteSync": False,
        },
        "staticContract": static_contract,
        "desktop": desktop_result,
        "mobile": mobile_result,
    }
    AUDIT_PATH.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
