import json
import os
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
REFERENCE_DIR = ROOT / "docs" / "design-references"
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch56-2026-08-26"
    / "runtime-audit.json"
)
IMAGE_ID = "i-vxeeCnxySa"


def node(page: Page, node_id: str):
    return page.locator(f'.react-flow__node[data-id="{node_id}"]')


def box(locator):
    value = locator.bounding_box()
    assert value is not None
    return value


def collect_errors(page: Page):
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


def graph_signature(page: Page):
    return page.evaluate(
        """() => ({
          nodes: [...document.querySelectorAll('.react-flow__node')].map((node) => ({
            id: node.getAttribute('data-id'),
            text: node.textContent,
            rotateSource: node.getAttribute('data-rotate-mirror-source-id'),
          })),
          edges: [...document.querySelectorAll('.react-flow__edge')].map((edge) => ({
            id: edge.getAttribute('data-id'),
            source: edge.querySelector('.react-flow__edge-path')?.getAttribute('d'),
          })),
          selected: [...document.querySelectorAll('.react-flow__node.selected')].map((node) =>
            node.getAttribute('data-id')
          ),
          viewport: document.querySelector('.react-flow__viewport')?.getAttribute('style'),
        })"""
    )


def organize(page: Page):
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    page.keyboard.press("Alt+Shift+f")
    page.wait_for_timeout(300)


def click_toolbar_button(page: Page, selector: str):
    trigger = page.locator(selector)
    trigger_box = box(trigger)
    viewport_width = page.viewport_size["width"]
    viewport_height = page.viewport_size["height"]
    hit_test_blocked = page.evaluate(
        """({selector, rect}) => {
          const pointX = Math.max(0, Math.min(window.innerWidth - 1, rect.x + rect.width / 2));
          const pointY = Math.max(0, Math.min(window.innerHeight - 1, rect.y + rect.height / 2));
          const hit = document.elementFromPoint(pointX, pointY);
          const target = document.querySelector(selector);
          return !hit || !target || (hit !== target && !target.contains(hit));
        }""",
        {"selector": selector, "rect": trigger_box},
    )
    if (
        trigger_box["x"] < 0
        or trigger_box["x"] + trigger_box["width"] > viewport_width
        or trigger_box["y"] < 0
        or trigger_box["y"] + trigger_box["height"] > viewport_height
        or hit_test_blocked
    ):
        trigger.evaluate("(element) => element.click()")
    else:
        trigger.click()


def assert_no_overflow(page: Page):
    assert page.evaluate(
        "() => document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )
    assert page.evaluate(
        "() => document.body.scrollWidth <= document.body.clientWidth"
    )


def run_rotate(page: Page, viewport_label: str):
    errors = collect_errors(page)
    organize(page)
    source = node(page, IMAGE_ID)
    source.click(force=True)
    page.wait_for_timeout(180)
    toolbar = page.locator("[data-image-toolbar]")
    rotate = page.locator('[data-testid="image-toolbar-rotate"]')
    assert toolbar.count() == 1
    assert rotate.is_enabled()
    assert rotate.get_attribute("aria-label") == "旋转"
    nodes_before = page.locator(".react-flow__node").count()
    edges_before = page.locator(".react-flow__edge").count()
    graph_before = graph_signature(page)
    click_toolbar_button(page, '[data-testid="image-toolbar-rotate"]')
    page.wait_for_function(
        """({nodesBefore, edgesBefore}) =>
          document.querySelectorAll('.react-flow__node').length === nodesBefore + 1 &&
          document.querySelectorAll('.react-flow__edge').length === edgesBefore + 1 &&
          document.querySelector('[data-rotate-mirror="true"]') !== null
        """,
        arg={"nodesBefore": nodes_before, "edgesBefore": edges_before},
    )
    page.wait_for_timeout(180)

    derived_inner = page.locator('[data-rotate-mirror="true"]')
    derived = page.locator(".react-flow__node").filter(has=derived_inner)
    derived_id = derived.get_attribute("data-id")
    assert derived_id
    derived_box = box(derived)
    assert "旋转与镜像" in derived.inner_text()
    assert derived_inner.get_attribute("data-rotate-mirror-source-id") == IMAGE_ID
    assert derived_inner.get_attribute("data-rotate-mirror-source-filename") == "图片4"
    assert derived_inner.get_attribute("data-rotate-mirror-operation") == "rotate-mirror"
    assert derived_inner.get_attribute("data-rotate-mirror-prototype") == "true"
    assert derived.locator('[data-image-node-media] img[alt="旋转与镜像"]').count() == 1
    assert page.locator("[data-image-edit-panel]").count() == 1
    assert page.locator("[data-image-toolbar]").count() == 1
    assert page.locator('[data-testid="image-toolbar-rotate"]').is_enabled()
    assert page.locator(".react-flow__node.selected").count() == 1
    assert page.locator(f'.react-flow__node.selected[data-id="{derived_id}"]').count() == 1
    assert page.locator(f'.react-flow__node[data-id="{IMAGE_ID}"].selected').count() == 0

    source_edge = page.locator(
        f'.react-flow__edge[data-id="e-{IMAGE_ID}-{derived_id}"]'
    )
    assert source_edge.count() == 1
    assert derived_box["width"] > 0
    graph_after = graph_signature(page)
    assert len(graph_after["nodes"]) == len(graph_before["nodes"]) + 1
    assert len(graph_after["edges"]) == len(graph_before["edges"]) + 1

    page.screenshot(
        path=str(
            REFERENCE_DIR
            / f"liblib-clone-batch56-image-rotate-derived-{viewport_label}-2026-08-26.png"
        )
    )

    page.keyboard.press("Meta+z")
    page.wait_for_timeout(180)
    assert page.locator(f'.react-flow__node[data-id="{derived_id}"]').count() == 0
    assert page.locator(".react-flow__node").count() == nodes_before
    assert page.locator(".react-flow__edge").count() == edges_before
    assert page.locator(".react-flow__node.selected").count() == 0

    page.keyboard.press("Meta+Shift+z")
    page.wait_for_timeout(180)
    assert page.locator(f'.react-flow__node[data-id="{derived_id}"]').count() == 1
    assert page.locator(".react-flow__node.selected").count() == 0
    # Existing canvas undo/redo restores graph data but intentionally clears selection.
    assert page.locator('[data-rotate-mirror="true"]').count() == 1
    assert_no_overflow(page)
    assert not errors, errors
    return {
        "viewport": page.viewport_size,
        "derived_id": derived_id,
        "derived": derived_box,
        "nodes_before": nodes_before,
        "nodes_after": page.locator(".react-flow__node").count(),
        "edges_before": edges_before,
        "edges_after": page.locator(".react-flow__edge").count(),
        "selection_after_redo": [],
    }


def run_no_media(page: Page):
    errors = collect_errors(page)
    organize(page)
    source = node(page, IMAGE_ID)
    source.click(force=True)
    page.wait_for_timeout(150)
    click_toolbar_button(page, '[data-testid="image-toolbar-panorama-slash"]')
    page.wait_for_function(
        "() => document.querySelector('[data-image-placeholder=\"panorama\"]') !== null"
    )
    empty_inner = page.locator('[data-image-placeholder="panorama"]')
    empty = page.locator(".react-flow__node").filter(has=empty_inner)
    empty_node_id = empty.get_attribute("data-id")
    assert empty_node_id
    empty.click(force=True)
    page.wait_for_timeout(180)
    rotate = page.locator('[data-testid="image-toolbar-rotate"]')
    assert rotate.count() == 1
    assert rotate.is_disabled()
    nodes_before = page.locator(".react-flow__node").count()
    edges_before = page.locator(".react-flow__edge").count()
    graph_before = graph_signature(page)
    rotate.evaluate("(element) => element.click()")
    page.wait_for_timeout(180)
    assert page.locator(".react-flow__node").count() == nodes_before
    assert page.locator(".react-flow__edge").count() == edges_before
    assert graph_signature(page) == graph_before
    assert not errors, errors
    return {
        "empty_node_id": empty_node_id,
        "rotate_disabled": True,
        "nodes": nodes_before,
        "edges": edges_before,
    }


def main():
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop_page = browser.new_page(
            viewport={"width": 929, "height": 874}, device_scale_factor=1
        )
        desktop = run_rotate(desktop_page, "desktop-929")
        desktop_page.close()

        mobile_page = browser.new_page(
            viewport={"width": 390, "height": 844}, device_scale_factor=1
        )
        mobile = run_rotate(mobile_page, "mobile-390")
        mobile_page.close()

        no_media_page = browser.new_page(
            viewport={"width": 929, "height": 874}, device_scale_factor=1
        )
        no_media = run_no_media(no_media_page)
        no_media_page.close()
        browser.close()

    AUDIT_PATH.write_text(
        json.dumps(
            {
                "url": URL,
                "source_node_id": IMAGE_ID,
                "contract": {
                    "action": "旋转",
                    "derived_filename": "旋转与镜像",
                    "operation": "rotate-mirror",
                    "prototype": True,
                    "graph_delta": "one_image_node_plus_one_source_edge",
                    "undo_redo": "atomic_graph_transaction",
                    "no_media": "disabled_noop",
                    "selection_after_create": "derived_node",
                    "selection_after_undo_redo": "cleared_by_existing_history_contract",
                },
                "desktop": desktop,
                "mobile": mobile,
                "no_media": no_media,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print(
        "Batch 56 Playwright verification passed: media-gated rotate entry, "
        "rotate-mirror derived node metadata, source edge, atomic undo/redo, "
        "no-media disabled/no-op boundary and desktop/mobile overflow."
    )


if __name__ == "__main__":
    main()
