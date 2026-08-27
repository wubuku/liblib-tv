import json
import os
from pathlib import Path

from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:3000")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch64-2026-08-27"
    / "runtime-audit.json"
)
NODE_ID = "batch64-center-node"


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


def rect(locator: Locator):
    box = locator.bounding_box()
    assert box, f"missing bounding box for {locator}"
    return box


def center(box):
    return {
        "x": box["x"] + box["width"] / 2,
        "y": box["y"] + box["height"] / 2,
    }


def prepare(page: Page, with_node=True):
    viewport = page.viewport_size
    assert viewport
    node_position = {
        "x": viewport["width"] / 2 - 175,
        "y": viewport["height"] / 2 - 90,
    }
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(260)
    page.evaluate(
        """() => {
          window.__libtv_store.getState().setActiveCanvas("canvas-1");
          window.__libtv_ui_store.getState().closeAllPanels();
          window.__libtv_asset_layout_log = [];
        }"""
    )
    page.wait_for_timeout(180)
    page.evaluate(
        """({nodeId, nodePosition, withNode}) => {
          const store = window.__libtv_store;
          store.setState((state) => ({
            activeCanvasId: "canvas-1",
            selectedNodeIds: withNode ? [nodeId] : [],
            selectedNodeId: withNode ? nodeId : null,
            selectedEdgeIds: [],
            historyByCanvas: {
              ...state.historyByCanvas,
              "canvas-1": { past: [], future: [] },
            },
            canvases: state.canvases.map((canvas) =>
              canvas.id === "canvas-1"
                ? {
                    ...canvas,
                    viewport: { x: 0, y: 0, zoom: 1 },
                    nodes: withNode
                      ? [
                          {
                            id: nodeId,
                            type: "text",
                            position: nodePosition,
                            width: 350,
                            height: 180,
                            style: { width: 350, height: 180 },
                            data: { content: "Batch 64 center anchor" },
                          },
                        ]
                      : [],
                    edges: [],
                  }
                : canvas,
            ),
          }));
        }""",
        {
            "nodeId": NODE_ID,
            "nodePosition": node_position,
            "withNode": with_node,
        },
    )
    page.wait_for_timeout(140)
    expected_count = 1 if with_node else 0
    assert page.locator(".react-flow__node").count() == expected_count


def snapshot(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          const canvas = state.getActiveCanvas();
          const history = state.historyByCanvas[state.activeCanvasId] || {
            past: [],
            future: [],
          };
          return {
            activeCanvasId: state.activeCanvasId,
            viewport: canvas?.viewport || null,
            nodes: (canvas?.nodes || []).map((node) => ({
              id: node.id,
              type: node.type,
              position: node.position,
              width: node.width,
              height: node.height,
              data: node.data,
            })),
            edges: (canvas?.edges || []).map((edge) => ({
              id: edge.id,
              source: edge.source,
              target: edge.target,
            })),
            selectedNodeIds: state.selectedNodeIds,
            selectedNodeId: state.selectedNodeId,
            selectedEdgeIds: state.selectedEdgeIds,
            pastLength: history.past.length,
            futureLength: history.future.length,
          };
        }"""
    )


def semantic_snapshot(value):
    return {
        "activeCanvasId": value["activeCanvasId"],
        "nodes": value["nodes"],
        "edges": value["edges"],
        "selectedNodeIds": value["selectedNodeIds"],
        "selectedNodeId": value["selectedNodeId"],
        "selectedEdgeIds": value["selectedEdgeIds"],
        "pastLength": value["pastLength"],
        "futureLength": value["futureLength"],
    }


def geometry(page: Page):
    host_box = rect(page.locator("[data-libtv-react-flow-host]"))
    node_box = rect(page.locator(f'.react-flow__node[data-id="{NODE_ID}"]'))
    host_center = center(host_box)
    node_center = center(node_box)
    return {
        "hostRect": host_box,
        "nodeRect": node_box,
        "hostCenter": host_center,
        "nodeCenter": node_center,
        "centerError": {
            "x": node_center["x"] - host_center["x"],
            "y": node_center["y"] - host_center["y"],
        },
    }


def assert_centered(page: Page, tolerance=1.5):
    value = geometry(page)
    assert abs(value["centerError"]["x"]) <= tolerance, value
    assert abs(value["centerError"]["y"]) <= tolerance, value
    return value


def wait_for_log(page: Page, minimum_length: int):
    page.wait_for_function(
        "(length) => window.__libtv_asset_layout_log.length >= length",
        arg=minimum_length,
    )
    return page.evaluate("() => window.__libtv_asset_layout_log")


def asset_toggle(page: Page):
    page.get_by_role("button", name="资产管理", exact=True).click()


def open_asset(page: Page):
    asset_toggle(page)
    panel = page.locator('[data-liblib-overlay="asset"]')
    panel.wait_for(state="visible")
    wait_for_log(page, 1)
    return panel


def assert_viewport(value, x, y=0, zoom=1, tolerance=0.01):
    assert abs(value["x"] - x) <= tolerance, value
    assert abs(value["y"] - y) <= tolerance, value
    assert abs(value["zoom"] - zoom) <= tolerance, value


def run_pure_helper(page: Page):
    result = page.evaluate(
        """() => ({
          identity: window.__libtv_plan_host_resize_center_preservation(
            { left: 0, top: 0, width: 929, height: 874 },
            { x: 0, y: 0, zoom: 1 },
            { left: 0, top: 0, width: 929, height: 874 },
          ),
          open: window.__libtv_plan_host_resize_center_preservation(
            { left: 0, top: 0, width: 929, height: 874 },
            { x: 0, y: 0, zoom: 1 },
            { left: 240, top: 0, width: 689, height: 874 },
          ),
          translated: window.__libtv_plan_host_resize_center_preservation(
            { left: 20, top: 30, width: 200, height: 100 },
            { x: 30, y: -20, zoom: 2 },
            { left: 40, top: 10, width: 300, height: 140 },
          ),
          invalidZoom: window.__libtv_plan_host_resize_center_preservation(
            { left: 0, top: 0, width: 100, height: 80 },
            { x: 0, y: 0, zoom: 0 },
            { left: 0, top: 0, width: 80, height: 80 },
          ),
          invalidHost: window.__libtv_plan_host_resize_center_preservation(
            { left: 0, top: 0, width: 0, height: 80 },
            { x: 0, y: 0, zoom: 1 },
            { left: 0, top: 0, width: 80, height: 80 },
          ),
        })"""
    )
    assert result["identity"]["flowAnchor"] == {"x": 464.5, "y": 437}, result
    assert result["identity"]["targetViewport"] == {"x": 0, "y": 0, "zoom": 1}, result
    assert result["open"]["flowAnchor"] == {"x": 464.5, "y": 437}, result
    assert result["open"]["targetViewport"] == {"x": -120, "y": 0, "zoom": 1}, result
    assert result["translated"]["flowAnchor"] == {"x": 35, "y": 35}, result
    assert result["translated"]["targetViewport"] == {
        "x": 80,
        "y": 0,
        "zoom": 2,
    }, result
    assert result["invalidZoom"] is None, result
    assert result["invalidHost"] is None, result
    return result


def run_toolbar_toggle(page: Page):
    prepare(page)
    before = snapshot(page)
    before_geometry = assert_centered(page)

    open_asset(page)
    opened = snapshot(page)
    opened_geometry = assert_centered(page)
    assert_viewport(opened["viewport"], -120)
    assert semantic_snapshot(opened) == semantic_snapshot(before), (before, opened)

    asset_toggle(page)
    page.locator('[data-liblib-overlay="asset"]').wait_for(state="hidden")
    logs = wait_for_log(page, 2)
    closed = snapshot(page)
    closed_geometry = assert_centered(page)
    assert_viewport(closed["viewport"], 0)
    assert semantic_snapshot(closed) == semantic_snapshot(before), (before, closed)
    assert [entry["reason"] for entry in logs] == ["committed", "committed"], logs
    return {
        "before": before_geometry,
        "opened": opened_geometry,
        "closed": closed_geometry,
        "logs": logs,
        "viewportOpen": opened["viewport"],
        "viewportClosed": closed["viewport"],
    }


def run_explicit_close(page: Page):
    prepare(page)
    before = snapshot(page)
    panel = open_asset(page)
    panel.get_by_role("button", name="关闭资产管理").click()
    panel.wait_for(state="hidden")
    logs = wait_for_log(page, 2)
    after = snapshot(page)
    assert_viewport(after["viewport"], 0)
    assert_centered(page)
    assert semantic_snapshot(after) == semantic_snapshot(before), (before, after)
    return {"logs": logs, "viewport": after["viewport"]}


def run_canvas_context(page: Page):
    prepare(page)
    before = snapshot(page)
    panel = open_asset(page)
    panel.locator("[data-asset-manager-canvas]").click()
    panel.wait_for(state="hidden")
    dropdown = page.locator('[data-liblib-overlay="canvas-dropdown"]')
    dropdown.wait_for(state="visible")
    logs = wait_for_log(page, 2)
    after = snapshot(page)
    assert_viewport(after["viewport"], 0)
    assert_centered(page)
    assert semantic_snapshot(after) == semantic_snapshot(before), (before, after)
    page.keyboard.press("Escape")
    assert not dropdown.is_visible()
    return {"logs": logs, "viewport": after["viewport"]}


def run_stale_canvas_guard(page: Page):
    prepare(page)
    canvas_two_before = page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          const canvas = state.canvases.find((item) => item.id === "canvas-2");
          return canvas?.viewport || null;
        }"""
    )
    page.get_by_role("button", name="资产管理", exact=True).dispatch_event("click")
    page.evaluate("() => window.__libtv_store.getState().setActiveCanvas('canvas-2')")
    page.wait_for_timeout(220)
    logs = page.evaluate("() => window.__libtv_asset_layout_log")
    assert logs, logs
    assert logs[-1]["status"] == "skipped", logs
    assert logs[-1]["reason"] in ["canvas-changed", "instance-changed"], logs
    state = snapshot(page)
    assert state["activeCanvasId"] == "canvas-2", state
    assert state["pastLength"] == 0, state
    assert state["selectedNodeIds"] == [], state
    return {
        "log": logs[-1],
        "canvasTwoViewportBefore": canvas_two_before,
        "canvasTwoViewportAfter": state["viewport"],
    }


def run_default_add_composition(page: Page):
    prepare(page, with_node=False)
    open_asset(page)
    page.get_by_role("button", name="添加节点").click()
    page.locator('[data-add-node-entry="text"]').click()
    page.wait_for_timeout(140)
    state = snapshot(page)
    assert len(state["nodes"]) == 1, state
    node_id = state["nodes"][0]["id"]
    host_box = rect(page.locator("[data-libtv-react-flow-host]"))
    node_box = rect(page.locator(f'.react-flow__node[data-id="{node_id}"]'))
    error = {
        "x": center(node_box)["x"] - center(host_box)["x"],
        "y": center(node_box)["y"] - center(host_box)["y"],
    }
    assert abs(error["x"]) <= 1.5 and abs(error["y"]) <= 1.5, error
    assert state["selectedNodeIds"] == [node_id], state
    assert state["pastLength"] == 1, state
    return {
        "hostRect": host_box,
        "nodeRect": node_box,
        "centerError": error,
        "viewport": state["viewport"],
    }


def run_desktop(page: Page):
    errors = attach_errors(page)
    prepare(page)
    result = {
        "pureHelper": run_pure_helper(page),
        "toolbarToggle": run_toolbar_toggle(page),
        "explicitClose": run_explicit_close(page),
        "canvasContext": run_canvas_context(page),
        "staleCanvasGuard": run_stale_canvas_guard(page),
        "defaultAddComposition": run_default_add_composition(page),
    }
    assert_no_overflow(page)
    assert not errors, errors
    return result


def run_mobile(page: Page):
    errors = attach_errors(page)
    result = run_toolbar_toggle(page)
    assert abs(result["opened"]["hostRect"]["width"] - 150) <= 1, result
    assert_viewport(result["viewportOpen"], -120)
    assert_no_overflow(page)
    assert not errors, errors
    return result


def main():
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(
            viewport={"width": 929, "height": 874},
            device_scale_factor=1,
        )
        desktop_result = run_desktop(desktop)
        desktop.close()

        mobile = browser.new_page(
            viewport={"width": 390, "height": 844},
            device_scale_factor=1,
        )
        mobile_result = run_mobile(mobile)
        mobile.close()
        browser.close()

    audit = {
        "batch": 64,
        "date": "2026-08-27",
        "url": URL,
        "scope": "clone-owned Asset drawer host-center anchor preservation",
        "sourceParityClaim": False,
        "screenshotsReused": True,
        "desktop": desktop_result,
        "mobile": mobile_result,
        "acceptance": {
            "maxCenterErrorPx": 1.5,
            "expectedDrawerViewportDeltaX": -120,
            "graphHistorySelectionZeroMutation": True,
            "currentOwnerGuard": True,
            "defaultAddComposition": True,
            "noOverflow": True,
            "browserDiagnosticsClean": True,
        },
    }
    AUDIT_PATH.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "Batch 64 Playwright verification passed: pure resize planning, "
        "desktop/mobile Asset open/close center preservation, toolbar/X/Canvas "
        "context entry unification, graph/history/selection isolation, stale "
        "canvas guard, Batch 63 default-add composition, overflow and diagnostics."
    )


if __name__ == "__main__":
    main()
