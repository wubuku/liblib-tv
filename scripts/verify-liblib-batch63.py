import json
import os
from pathlib import Path

from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch63-2026-08-27"
    / "runtime-audit.json"
)


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


def prepare(page: Page):
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(300)
    page.evaluate(
        """() => {
          window.__libtv_store.getState().setActiveCanvas("canvas-1");
          window.__libtv_ui_store.getState().closeAllPanels();
        }"""
    )
    page.wait_for_timeout(220)
    reset_fixture(page)


def reset_fixture(page: Page):
    page.evaluate(
        """() => {
          const store = window.__libtv_store;
          store.setState((state) => ({
            activeCanvasId: "canvas-1",
            selectedNodeIds: [],
            selectedNodeId: null,
            selectedEdgeIds: [],
            historyByCanvas: {
              ...state.historyByCanvas,
              "canvas-1": { past: [], future: [] },
            },
            canvases: state.canvases.map((canvas) =>
              canvas.id === "canvas-1"
                ? {
                    ...canvas,
                    nodes: [],
                    edges: [],
                    viewport: { x: 0, y: 0, zoom: 1 },
                  }
                : canvas,
            ),
          }));
          window.__libtv_ui_store.getState().closeAllPanels();
        }"""
    )
    page.wait_for_timeout(140)
    assert page.locator(".react-flow__node").count() == 0


def graph(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          const canvas = state.getActiveCanvas();
          const history = state.historyByCanvas[state.activeCanvasId] || {
            past: [],
            future: [],
          };
          return {
            nodes: (canvas?.nodes || []).map((node) => ({
              id: node.id,
              type: node.type,
              position: node.position,
              width: node.width,
              height: node.height,
              data: node.data,
            })),
            selectedNodeIds: state.selectedNodeIds,
            selectedNodeId: state.selectedNodeId,
            selectedEdgeIds: state.selectedEdgeIds,
            pastLength: history.past.length,
            futureLength: history.future.length,
          };
        }"""
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


def assert_centered(page: Page, node_id: str, tolerance=1.5):
    host_box = rect(page.locator("[data-libtv-react-flow-host]"))
    node_box = rect(page.locator(f'.react-flow__node[data-id="{node_id}"]'))
    host_center = center(host_box)
    node_center = center(node_box)
    error = {
        "x": node_center["x"] - host_center["x"],
        "y": node_center["y"] - host_center["y"],
    }
    assert abs(error["x"]) <= tolerance, (host_box, node_box, error)
    assert abs(error["y"]) <= tolerance, (host_box, node_box, error)
    return {
        "hostRect": host_box,
        "nodeRect": node_box,
        "hostCenter": host_center,
        "nodeCenter": node_center,
        "centerError": error,
    }


def open_add_node(page: Page):
    page.get_by_role("button", name="添加节点").click()
    panel = page.locator('[data-liblib-overlay="add-node"]')
    assert panel.is_visible()
    return panel


def assert_graph_transaction(page: Page, expected_type: str):
    snapshot = graph(page)
    assert len(snapshot["nodes"]) == 1, snapshot
    node = snapshot["nodes"][0]
    assert node["type"] == expected_type, snapshot
    assert snapshot["selectedNodeIds"] == [node["id"]], snapshot
    assert snapshot["selectedNodeId"] == node["id"], snapshot
    assert snapshot["selectedEdgeIds"] == [], snapshot
    assert snapshot["pastLength"] == 1, snapshot
    assert snapshot["futureLength"] == 0, snapshot
    placement = assert_centered(page, node["id"])
    return {"graph": snapshot, "placement": placement}


def add_from_panel(page: Page, node_type: str):
    panel = open_add_node(page)
    panel.locator(f'[data-add-node-entry="{node_type}"]').click()
    page.wait_for_timeout(140)
    assert not panel.is_visible()
    return assert_graph_transaction(page, node_type)


def open_asset_manager(page: Page):
    page.get_by_role("button", name="资产管理").click()
    panel = page.locator('[data-liblib-overlay="asset"]')
    assert panel.is_visible()
    page.wait_for_timeout(100)
    return panel


def run_pure_helper(page: Page):
    result = page.evaluate(
        """() => ({
          identity: window.__libtv_plan_host_center_placement(
            { left: 20, top: 30, width: 200, height: 80 },
            { x: 12, y: -4 },
            { width: 10, height: 6 },
          ),
          translated: window.__libtv_plan_host_center_placement(
            { left: 240, top: 0, width: 689, height: 874 },
            { x: 900, y: 450 },
            { width: 512, height: 288 },
          ),
          invalidHost: window.__libtv_plan_host_center_placement(
            { left: 0, top: 0, width: 0, height: 80 },
            { x: 0, y: 0 },
            { width: 10, height: 10 },
          ),
          invalidFlow: window.__libtv_plan_host_center_placement(
            { left: 0, top: 0, width: 100, height: 80 },
            { x: Number.NaN, y: 0 },
            { width: 10, height: 10 },
          ),
          invalidDimensions: window.__libtv_plan_host_center_placement(
            { left: 0, top: 0, width: 100, height: 80 },
            { x: 0, y: 0 },
            { width: -1, height: 10 },
          ),
        })"""
    )
    assert result["identity"] == {
        "clientCenter": {"x": 120, "y": 70},
        "flowCenter": {"x": 12, "y": -4},
        "nodePosition": {"x": 7, "y": -7},
    }, result
    assert result["translated"] == {
        "clientCenter": {"x": 584.5, "y": 437},
        "flowCenter": {"x": 900, "y": 450},
        "nodePosition": {"x": 644, "y": 306},
    }, result
    assert result["invalidHost"] is None, result
    assert result["invalidFlow"] is None, result
    assert result["invalidDimensions"] is None, result
    return result


def run_zero_mutation_guard(page: Page):
    reset_fixture(page)
    before = graph(page)
    page.evaluate(
        """() => {
          window.__libtv_store
            .getState()
            .addNodeAtFlowCenter("text", { x: Number.NaN, y: 0 });
        }"""
    )
    after = graph(page)
    assert after == before, (before, after)
    return after


def run_compatibility_add(page: Page):
    reset_fixture(page)
    page.evaluate("() => window.__libtv_store.getState().addNode('audio')")
    page.wait_for_timeout(120)
    snapshot = graph(page)
    assert len(snapshot["nodes"]) == 1, snapshot
    assert snapshot["nodes"][0]["type"] == "audio", snapshot
    assert snapshot["pastLength"] == 1, snapshot
    return snapshot


def run_character(page: Page, asset_open=False):
    reset_fixture(page)
    asset_panel = open_asset_manager(page) if asset_open else None
    page.get_by_role("button", name="角色库").click()
    panel = page.locator('[data-liblib-overlay="primary:character"]')
    assert panel.is_visible()
    if asset_panel:
        assert asset_panel.is_visible()
    panel.get_by_role("button", name="应用至画布").click()
    page.wait_for_timeout(160)
    assert not panel.is_visible()
    if asset_panel:
        assert asset_panel.is_visible()
    result = assert_graph_transaction(page, "image")
    node = result["graph"]["nodes"][0]
    assert node["width"] == 512 and node["height"] == 288, node
    assert node["data"]["width"] == 568 and node["data"]["height"] == 761, node
    assert node["data"]["filename"] == "甜妹/清新少女", node
    return result


def run_desktop(page: Page):
    errors = attach_errors(page)
    prepare(page)
    results = {
        "pureHelper": run_pure_helper(page),
        "closed": {},
    }

    for node_type in ["text", "image", "video"]:
        reset_fixture(page)
        results["closed"][node_type] = add_from_panel(page, node_type)

    reset_fixture(page)
    asset_panel = open_asset_manager(page)
    asset_host_box = rect(page.locator("[data-libtv-react-flow-host]"))
    assert asset_host_box["x"] >= 239, asset_host_box
    assert asset_host_box["width"] < 700, asset_host_box
    results["assetOpen"] = add_from_panel(page, "text")
    assert asset_panel.is_visible()

    results["characterClosed"] = run_character(page)
    results["characterAssetOpen"] = run_character(page, asset_open=True)
    results["zeroMutation"] = run_zero_mutation_guard(page)
    results["compatibilityAdd"] = run_compatibility_add(page)
    assert_no_overflow(page)
    assert not errors, errors
    return results


def run_mobile(page: Page):
    errors = attach_errors(page)
    prepare(page)

    closed = add_from_panel(page, "text")
    reset_fixture(page)
    asset_panel = open_asset_manager(page)
    asset_host_box = rect(page.locator("[data-libtv-react-flow-host]"))
    assert asset_host_box["x"] >= 239, asset_host_box
    assert asset_host_box["width"] <= 151, asset_host_box
    asset_open = add_from_panel(page, "image")
    assert asset_panel.is_visible()

    assert_no_overflow(page)
    assert not errors, errors
    return {
        "closed": closed,
        "assetOpen": asset_open,
    }


def main():
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(
            viewport={"width": 929, "height": 874},
            device_scale_factor=1,
        )
        desktop_results = run_desktop(desktop)
        desktop.close()

        mobile = browser.new_page(
            viewport={"width": 390, "height": 844},
            device_scale_factor=1,
        )
        mobile_results = run_mobile(mobile)
        mobile.close()
        browser.close()

    audit = {
        "batch": 63,
        "date": "2026-08-27",
        "url": URL,
        "scope": "clone-owned actual React Flow host-center default placement",
        "sourceParityClaim": False,
        "screenshotsReused": True,
        "desktop": desktop_results,
        "mobile": mobile_results,
        "acceptance": {
            "maxCenterErrorPx": 1.5,
            "graphHistoryStepsPerAdd": 1,
            "selectionProjectsCreatedNode": True,
            "invalidFlowCenterZeroMutation": True,
            "legacyAddNodeCallable": True,
            "noOverflow": True,
            "browserDiagnosticsClean": True,
        },
    }
    AUDIT_PATH.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "Batch 63 Playwright verification passed: pure host-center planning, "
        "desktop/mobile Add Node placement, asset-open host geometry, Character "
        "Library graph dimensions, one-step history, exact selection, invalid "
        "input zero mutation, legacy add compatibility, overflow and diagnostics."
    )


if __name__ == "__main__":
    main()
