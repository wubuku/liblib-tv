#!/usr/bin/env python3
"""Verify Batch 587: 导演台「收起」语义对齐源站（2026-10-01 实测）。

Source facts (live CDP sampling of the source director desk at 1920x1150,
controlled before/after/after-restore diff):

    收起 lives in the header, immediately right of the `3D导演台` title
    (x=240, y=6, 40x40, `aria="收起"`). It is the desk's only collapse
    affordance.

    Clicking it removes the header and the left scene panel from the DOM.
    Everything else keeps its exact coordinates:

        收起前 / 收起后 / 点图标栏「场景」恢复后
        header   280x52  -> REMOVED -> 280x52
        left     280x1098-> REMOVED -> 280x1098
        rail     7 entries, x=8, 32x32   -> KEPT   -> KEPT
        right    1639,0 281x1150          -> KEPT   -> KEPT
        canvas   0,0 1920x1150            -> KEPT   -> KEPT
        导演视角 / 机位视角 / gizmo / 重置视角 -> KEPT -> KEPT

    The restore affordance is the icon rail's 场景 entry — there is no
    second button inside the collapsed desk.

The clone previously shipped a clone-only `全屏 / 恢复侧栏` toggle in the
viewport bottom bar that hid BOTH panels. That is not the source behaviour,
so batch 587 removed it and moved `data-director-panels-toggle` onto the
header 收起 button, leaving `viewportPanelsCollapsed` meaning "left scene
panel collapsed" (the field name and its persistence exclusions are kept so
batch 74 / 89 / 93 contracts stay intact).

Contract asserted here:
1. header carries a verbatim 收起 button (aria + title);
2. collapsing hides the left scene panel ONLY — the right inspector panel,
   the icon rail, the view-mode toggle and 重置视角 all survive;
3. the viewport gives back exactly the scene-panel width (~220px) on the
   left, and nothing on the right;
4. the 收起 button unmounts with the collapse (no dead one-way control);
5. the rail's 场景 entry restores the header, the panel and the geometry;
6. the viewport bottom bar no longer offers 全屏 / 恢复侧栏;
7. no diagnostics.
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
    / "liblib-canvas-batch587-2026-10-01"
    / "runtime-audit.json"
)

RAIL_ENTRIES = [
    "场景",
    "添加角色",
    "添加机位",
    "全景图",
    "选择画幅比例",
    "AI 识图导入",
    "帮助",
]


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


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool, detail: Any = None) -> None:
        assert ok, f"batch587 check failed: {name} :: {detail}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 587" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(500)

    workspace = page.locator("[data-director-workspace]")
    viewport = page.locator("[data-director-viewport]")
    tree_rail = page.locator('aside[aria-label="场景对象"]')
    inspector_rail = page.locator('aside[aria-label="属性"]')
    toggle = page.locator("[data-director-panels-toggle]")

    def display(locator: Any) -> str:
        return locator.evaluate("el => getComputedStyle(el).display")

    def box(locator: Any) -> dict[str, float]:
        return locator.bounding_box() or {}

    # 1) header carries the verbatim 收起 button
    check("header:collapse-present", toggle.count() == 1)
    check("header:collapse-aria", toggle.get_attribute("aria-label") == "收起")
    check("header:collapse-title", toggle.get_attribute("title") == "收起")
    check(
        "header:collapse-in-header",
        toggle.evaluate("el => Boolean(el.closest('header'))"),
    )
    check(
        "header:collapse-before-title",
        toggle.evaluate(
            """el => {
              const h1 = el.closest('header').querySelector('h1');
              return h1 ? h1.textContent.trim() === '3D导演台' : false;
            }"""
        ),
    )
    check("initial:expanded-flag", workspace.get_attribute(
        "data-director-panels-collapsed"
    ) == "false")

    expanded_viewport = box(viewport)
    check("initial:tree-visible", display(tree_rail) != "none")
    check("initial:inspector-visible", display(inspector_rail) != "none")
    result["expanded_viewport"] = expanded_viewport

    # 6) the clone-only 全屏 toggle is gone from the viewport bottom bar
    bar_labels = page.evaluate(
        """() => [...document.querySelectorAll('[data-director-viewport] button')]
             .map(b => b.getAttribute('aria-label') || b.getAttribute('title') || '')"""
    )
    result["viewport_bar_labels"] = bar_labels
    check(
        "bottombar:no-clone-fullscreen",
        "全屏" not in bar_labels and "恢复侧栏" not in bar_labels,
        detail=bar_labels,
    )

    # 2) collapse hides the left scene panel only
    toggle.click()
    page.wait_for_function(
        "() => window.__director_store.getState().viewportPanelsCollapsed === true"
    )
    page.wait_for_timeout(250)
    collapsed_viewport = box(viewport)
    result["collapsed_viewport"] = collapsed_viewport

    check("collapsed:flag", workspace.get_attribute("data-director-panels-collapsed") == "true")
    check("collapsed:tree-hidden", display(tree_rail) == "none")
    check("collapsed:inspector-kept", display(inspector_rail) != "none")
    check(
        "collapsed:inspector-focusable",
        inspector_rail.get_attribute("aria-hidden") is None
        and not inspector_rail.get_attribute("inert"),
    )

    # 3) viewport gives back the scene-panel width on the left only
    gained = collapsed_viewport["width"] - expanded_viewport["width"]
    check("collapsed:viewport-grows", 180 <= gained <= 260, detail=gained)
    check(
        "collapsed:viewport-left-edge",
        collapsed_viewport["x"] <= expanded_viewport["x"] - 180,
        detail=(expanded_viewport["x"], collapsed_viewport["x"]),
    )
    check(
        "collapsed:viewport-right-edge-unchanged",
        abs(
            (
                collapsed_viewport["x"] + collapsed_viewport["width"]
            )
            - (expanded_viewport["x"] + expanded_viewport["width"])
        )
        <= 2,
    )

    # 4) the 收起 button unmounts — no dead one-way control
    check("collapsed:toggle-unmounted", toggle.count() == 0)

    # 2 (cont.) rail / view mode / reset survive the collapse
    rail = page.evaluate(
        """() => [...document.querySelectorAll('[data-director-rail-entry]')]
             .filter(el => el.getBoundingClientRect().width > 0)
             .map(el => el.getAttribute('aria-label'))"""
    )
    check("collapsed:rail-kept", rail == RAIL_ENTRIES, detail=rail)
    check(
        "collapsed:view-mode-kept",
        page.locator('[data-director-view-mode="director"]').is_visible()
        and page.locator('[data-director-view-mode="camera"]').is_visible(),
    )
    check(
        "collapsed:reset-view-kept",
        page.get_by_text("重置视角", exact=True).count() >= 1,
    )

    # 5) the rail's 场景 entry restores header + panel + geometry
    page.locator("[data-director-rail-entry='scene']").click()
    page.wait_for_function(
        "() => window.__director_store.getState().viewportPanelsCollapsed === false"
    )
    page.wait_for_timeout(250)
    restored_viewport = box(viewport)
    result["restored_viewport"] = restored_viewport

    check("restored:flag", workspace.get_attribute("data-director-panels-collapsed") == "false")
    check("restored:tree-visible", display(tree_rail) != "none")
    check("restored:inspector-visible", display(inspector_rail) != "none")
    check("restored:toggle-back", toggle.count() == 1)
    check("restored:toggle-aria", toggle.get_attribute("aria-label") == "收起")
    check(
        "restored:viewport-geometry",
        abs(restored_viewport["x"] - expanded_viewport["x"]) <= 1
        and abs(restored_viewport["width"] - expanded_viewport["width"]) <= 1,
        detail=(expanded_viewport, restored_viewport),
    )

    unexpected = [error for error in errors if "TransformControls" not in error]
    result["diagnostics"] = {
        "console": len(errors),
        "filtered_transformcontrols": len(errors) - len(unexpected),
        "errors": unexpected[:5],
    }
    check("diagnostics:zero", not unexpected, detail=unexpected[:8])
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 587,
        "title": "导演台「收起」语义对齐源站——只收左侧场景面板，恢复入口为图标栏「场景」",
        "evidence": (
            "2026-10-01 live CDP controlled before/after/restore diff of the "
            "source director desk at 1920x1150 + "
            "docs/research/liblib-canvas-batch587-2026-10-01/README.md"
        ),
        "migrated_assertions": [
            "verify-liblib-batch50.py: 收起 replaces 全屏; inspector stays visible; "
            "restore via rail 场景; data-director-panels-toggle now in DirectorDesk",
            "verify-liblib-batch93.py: restore clicks rail 场景 instead of a second "
            "toggle press (the header button unmounts on collapse)",
            "verify-liblib-batch74.py / batch89.py: unaffected — they only assert "
            "viewportPanelsCollapsed stays out of the persisted envelope and "
            "restores to false",
        ],
        "results": [],
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(
            viewport={"width": 1440, "height": 900}, device_scale_factor=1
        )
        audit["results"].append(run_desktop(desktop))
        desktop.close()
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    checks = audit["results"][0]["checks"]
    print(
        "Batch 587 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "收起 now collapses only the left scene panel and the rail 场景 entry "
        "restores it, matching the 2026-10-01 source diff. See runtime-audit.json."
    )


if __name__ == "__main__":
    main()
