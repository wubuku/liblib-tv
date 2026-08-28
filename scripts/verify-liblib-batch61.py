import json
import os
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch61-2026-08-27"
    / "runtime-audit.json"
)
PAGE_PATH = ROOT / "src" / "app" / "page.tsx"
STORE_PATH = ROOT / "src" / "store" / "canvasStore.ts"
ROUTING_PATH = ROOT / "src" / "lib" / "libtvReactFlowChangeRouting.ts"

CANVAS_ID = "canvas-1"
NODE_A = "batch61-node-a"
NODE_B = "batch61-node-b"
NODE_C = "batch61-node-c"
EDGE_AB = "batch61-edge-ab"
EDGE_BC = "batch61-edge-bc"


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
    reset_fixture(page)


def reset_fixture(page: Page):
    page.evaluate(
        """({canvasId, nodeA, nodeB, nodeC, edgeAB}) => {
          const store = window.__libtv_store;
          store.setState((state) => ({
            activeCanvasId: canvasId,
            selectedNodeIds: [],
            selectedNodeId: null,
            selectedEdgeIds: [],
            historyByCanvas: {
              ...state.historyByCanvas,
              [canvasId]: { past: [], future: [] },
            },
            canvases: state.canvases.map((canvas) =>
              canvas.id === canvasId
                ? {
                    ...canvas,
                    viewport: { x: 0, y: 0, zoom: 1 },
                    nodes: [
                      {
                        id: nodeA,
                        type: "text",
                        position: { x: 120, y: 150 },
                        width: 220,
                        height: 140,
                        style: { width: 220, height: 140 },
                        data: { content: "Batch 61 A" },
                      },
                      {
                        id: nodeB,
                        type: "text",
                        position: { x: 560, y: 150 },
                        width: 220,
                        height: 140,
                        style: { width: 220, height: 140 },
                        data: { content: "Batch 61 B" },
                      },
                      {
                        id: nodeC,
                        type: "text",
                        position: { x: 560, y: 410 },
                        width: 220,
                        height: 140,
                        style: { width: 220, height: 140 },
                        data: { content: "Batch 61 C" },
                      },
                    ],
                    edges: [
                      {
                        id: edgeAB,
                        source: nodeA,
                        sourceHandle: "source",
                        target: nodeB,
                        targetHandle: "target",
                        type: "default",
                      },
                    ],
                  }
                : canvas,
            ),
          }));
          window.__libtv_react_flow_change_log = [];
        }""",
        {
            "canvasId": CANVAS_ID,
            "nodeA": NODE_A,
            "nodeB": NODE_B,
            "nodeC": NODE_C,
            "edgeAB": EDGE_AB,
        },
    )
    page.wait_for_timeout(180)
    page.evaluate("() => { window.__libtv_react_flow_change_log = []; }")
    assert page.locator(".react-flow__node").count() == 3
    assert page.locator(".react-flow__edge").count() == 1


def state_snapshot(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          const canvas = state.getActiveCanvas();
          const history = state.historyByCanvas[state.activeCanvasId] || {
            past: [],
            future: [],
          };
          const runtimeKeys = ["selected", "measured", "dragging", "resizing"];
          return {
            activeCanvasId: state.activeCanvasId,
            nodes: (canvas?.nodes || []).map((node) => ({
              id: node.id,
              position: node.position,
              width: node.width,
              height: node.height,
              measured: node.measured || null,
              dragging:
                typeof node.dragging === "boolean" ? node.dragging : null,
              resizing:
                typeof node.resizing === "boolean" ? node.resizing : null,
              selectedPresent: Object.prototype.hasOwnProperty.call(
                node,
                "selected",
              ),
              data: node.data,
            })),
            edges: (canvas?.edges || []).map((edge) => ({
              id: edge.id,
              source: edge.source,
              sourceHandle: edge.sourceHandle || null,
              target: edge.target,
              targetHandle: edge.targetHandle || null,
              selectedPresent: Object.prototype.hasOwnProperty.call(
                edge,
                "selected",
              ),
            })),
            selectedNodeIds: state.selectedNodeIds,
            selectedNodeId: state.selectedNodeId,
            selectedEdgeIds: state.selectedEdgeIds,
            pastLength: history.past.length,
            futureLength: history.future.length,
            pastRuntimeFields: history.past.map((entry) => ({
              nodes: entry.nodes.map((node) =>
                runtimeKeys.filter((key) =>
                  Object.prototype.hasOwnProperty.call(node, key),
                ),
              ),
              edges: entry.edges.map((edge) =>
                runtimeKeys.filter((key) =>
                  Object.prototype.hasOwnProperty.call(edge, key),
                ),
              ),
            })),
          };
        }"""
    )


def semantic_graph(snapshot):
    return {
        "nodes": [
            {
                "id": node["id"],
                "position": node["position"],
                "width": node["width"],
                "height": node["height"],
                "data": node["data"],
                "selectedPresent": node["selectedPresent"],
            }
            for node in snapshot["nodes"]
        ],
        "edges": snapshot["edges"],
        "pastLength": snapshot["pastLength"],
        "futureLength": snapshot["futureLength"],
    }


def route(page: Page, request):
    return page.evaluate(
        "(request) => window.__libtv_route_react_flow_changes(request)",
        request,
    )


def assert_rejected_unchanged(page: Page, request, expected_code):
    before = state_snapshot(page)
    result = route(page, request)
    after = state_snapshot(page)
    assert result["status"] == "rejected", result
    assert result["code"] == expected_code, result
    assert after == before, (request, before, after)
    return result


def run_synthetic_corpus(page: Page):
    errors = attach_errors(page)
    prepare(page)
    corpus = {}

    before = state_snapshot(page)
    result = route(
        page,
        {
            "expectedActiveCanvasId": CANVAS_ID,
            "nodeChanges": [
                {"id": NODE_A, "type": "select", "selected": True}
            ],
        },
    )
    after = state_snapshot(page)
    assert result["code"] == "APPLIED_SELECTION"
    assert after["selectedNodeIds"] == [NODE_A]
    assert semantic_graph(after) == semantic_graph(before)
    corpus["node_selection"] = result

    reset_fixture(page)
    before = state_snapshot(page)
    result = route(
        page,
        {
            "expectedActiveCanvasId": CANVAS_ID,
            "edgeChanges": [
                {"id": EDGE_AB, "type": "select", "selected": True}
            ],
        },
    )
    after = state_snapshot(page)
    assert result["code"] == "APPLIED_SELECTION"
    assert after["selectedEdgeIds"] == [EDGE_AB]
    assert after["edges"][0]["selectedPresent"] is False
    assert semantic_graph(after) == semantic_graph(before)
    corpus["edge_selection"] = result

    reset_fixture(page)
    before = state_snapshot(page)
    result = route(
        page,
        {
            "expectedActiveCanvasId": CANVAS_ID,
            "nodeChanges": [
                {
                    "id": NODE_A,
                    "type": "position",
                    "position": {"x": 245, "y": 315},
                    "positionAbsolute": {"x": 245, "y": 315},
                    "dragging": True,
                }
            ],
        },
    )
    after = state_snapshot(page)
    assert result["code"] == "APPLIED_TRANSPORT"
    assert after["nodes"][0]["position"] == {"x": 245, "y": 315}
    assert after["nodes"][0]["dragging"] is True
    assert after["pastLength"] == before["pastLength"]
    corpus["finite_position"] = result

    reset_fixture(page)
    before = state_snapshot(page)
    result = route(
        page,
        {
            "expectedActiveCanvasId": CANVAS_ID,
            "nodeChanges": [
                {
                    "id": NODE_A,
                    "type": "dimensions",
                    "dimensions": {"width": 333, "height": 222},
                    "resizing": False,
                }
            ],
        },
    )
    after = state_snapshot(page)
    assert result["code"] == "APPLIED_TRANSPORT"
    assert after["nodes"][0]["measured"] == {"width": 333, "height": 222}
    assert after["nodes"][0]["width"] == before["nodes"][0]["width"]
    assert after["nodes"][0]["height"] == before["nodes"][0]["height"]
    assert after["pastLength"] == before["pastLength"]
    corpus["passive_dimensions"] = result

    reset_fixture(page)
    result = route(
        page,
        {
            "expectedActiveCanvasId": CANVAS_ID,
            "nodeChanges": [
                {"id": NODE_B, "type": "select", "selected": True},
                {
                    "id": NODE_A,
                    "type": "position",
                    "position": {"x": 180, "y": 190},
                    "dragging": False,
                },
            ],
        },
    )
    after = state_snapshot(page)
    assert result["code"] == "APPLIED_MIXED_RUNTIME"
    assert after["selectedNodeIds"] == [NODE_B]
    assert after["nodes"][0]["position"] == {"x": 180, "y": 190}
    assert after["pastLength"] == 0
    corpus["mixed_runtime"] = result

    rejection_cases = {
        "selection_then_remove": (
            {
                "expectedActiveCanvasId": CANVAS_ID,
                "nodeChanges": [
                    {"id": NODE_A, "type": "select", "selected": True},
                    {"id": NODE_A, "type": "remove"},
                ],
            },
            "SEMANTIC_CHANGE_REQUIRES_COMMAND",
        ),
        "node_add": (
            {
                "expectedActiveCanvasId": CANVAS_ID,
                "nodeChanges": [
                    {
                        "type": "add",
                        "item": {
                            "id": "forbidden-node",
                            "position": {"x": 0, "y": 0},
                            "data": {},
                        },
                    }
                ],
            },
            "SEMANTIC_CHANGE_REQUIRES_COMMAND",
        ),
        "node_replace": (
            {
                "expectedActiveCanvasId": CANVAS_ID,
                "nodeChanges": [
                    {
                        "id": NODE_A,
                        "type": "replace",
                        "item": {
                            "id": NODE_A,
                            "position": {"x": 0, "y": 0},
                            "data": {},
                        },
                    }
                ],
            },
            "SEMANTIC_CHANGE_REQUIRES_COMMAND",
        ),
        "attribute_resize": (
            {
                "expectedActiveCanvasId": CANVAS_ID,
                "nodeChanges": [
                    {
                        "id": NODE_A,
                        "type": "dimensions",
                        "dimensions": {"width": 300, "height": 200},
                        "setAttributes": True,
                    }
                ],
            },
            "ATTRIBUTE_RESIZE_REQUIRES_COMMAND",
        ),
        "edge_add": (
            {
                "expectedActiveCanvasId": CANVAS_ID,
                "edgeChanges": [
                    {
                        "type": "add",
                        "item": {
                            "id": "forbidden-edge",
                            "source": NODE_B,
                            "target": NODE_C,
                        },
                    }
                ],
            },
            "SEMANTIC_CHANGE_REQUIRES_COMMAND",
        ),
        "edge_remove": (
            {
                "expectedActiveCanvasId": CANVAS_ID,
                "edgeChanges": [{"id": EDGE_AB, "type": "remove"}],
            },
            "SEMANTIC_CHANGE_REQUIRES_COMMAND",
        ),
        "edge_replace": (
            {
                "expectedActiveCanvasId": CANVAS_ID,
                "edgeChanges": [
                    {
                        "id": EDGE_AB,
                        "type": "replace",
                        "item": {
                            "id": EDGE_AB,
                            "source": NODE_A,
                            "target": NODE_C,
                        },
                    }
                ],
            },
            "SEMANTIC_CHANGE_REQUIRES_COMMAND",
        ),
        "unknown_variant": (
            {
                "expectedActiveCanvasId": CANVAS_ID,
                "nodeChanges": [{"id": NODE_A, "type": "teleport"}],
            },
            "UNSUPPORTED_CHANGE_VARIANT",
        ),
        "unexpected_field": (
            {
                "expectedActiveCanvasId": CANVAS_ID,
                "nodeChanges": [
                    {
                        "id": NODE_A,
                        "type": "select",
                        "selected": True,
                        "data": {"forbidden": True},
                    }
                ],
            },
            "UNSUPPORTED_CHANGE_VARIANT",
        ),
        "stale_node": (
            {
                "expectedActiveCanvasId": CANVAS_ID,
                "nodeChanges": [
                    {
                        "id": "deleted-node",
                        "type": "position",
                        "position": {"x": 10, "y": 10},
                    }
                ],
            },
            "STALE_ELEMENT_ID",
        ),
        "stale_edge": (
            {
                "expectedActiveCanvasId": CANVAS_ID,
                "edgeChanges": [
                    {"id": "deleted-edge", "type": "select", "selected": True}
                ],
            },
            "STALE_ELEMENT_ID",
        ),
        "old_canvas": (
            {
                "expectedActiveCanvasId": "canvas-2",
                "nodeChanges": [
                    {"id": NODE_A, "type": "select", "selected": True}
                ],
            },
            "ACTIVE_CANVAS_CHANGED",
        ),
        "same_id_semantic_precedence": (
            {
                "expectedActiveCanvasId": CANVAS_ID,
                "nodeChanges": [
                    {"id": NODE_A, "type": "remove"},
                    {
                        "type": "add",
                        "item": {
                            "id": NODE_A,
                            "position": {"x": 0, "y": 0},
                            "data": {},
                        },
                    },
                    {
                        "id": NODE_A,
                        "type": "position",
                        "position": {"x": 99, "y": 99},
                    },
                ],
            },
            "SEMANTIC_CHANGE_REQUIRES_COMMAND",
        ),
    }
    for name, (request, expected_code) in rejection_cases.items():
        reset_fixture(page)
        corpus[name] = assert_rejected_unchanged(
            page,
            request,
            expected_code,
        )

    reset_fixture(page)
    before = state_snapshot(page)
    result = page.evaluate(
        """({canvasId, nodeA}) =>
          window.__libtv_route_react_flow_changes({
            expectedActiveCanvasId: canvasId,
            nodeChanges: [{
              id: nodeA,
              type: "position",
              position: { x: Number.NaN, y: 10 },
            }],
          })""",
        {"canvasId": CANVAS_ID, "nodeA": NODE_A},
    )
    assert result["code"] == "INVALID_NUMERIC_PAYLOAD"
    assert state_snapshot(page) == before
    corpus["nan_position"] = result

    reset_fixture(page)
    before = state_snapshot(page)
    result = page.evaluate(
        """({canvasId, nodeA}) =>
          window.__libtv_route_react_flow_changes({
            expectedActiveCanvasId: canvasId,
            nodeChanges: [{
              id: nodeA,
              type: "dimensions",
              dimensions: { width: Number.POSITIVE_INFINITY, height: 10 },
            }],
          })""",
        {"canvasId": CANVAS_ID, "nodeA": NODE_A},
    )
    assert result["code"] == "INVALID_NUMERIC_PAYLOAD"
    assert state_snapshot(page) == before
    corpus["infinite_dimensions"] = result

    reset_fixture(page)
    direct_connection = page.evaluate(
        """({edgeId, nodeB, nodeC}) =>
          window.__libtv_store.getState().addEdge({
            id: edgeId,
            source: nodeB,
            sourceHandle: "source",
            target: nodeC,
            targetHandle: "target",
            type: "default",
          })""",
        {"edgeId": EDGE_BC, "nodeB": NODE_B, "nodeC": NODE_C},
    )
    assert direct_connection["status"] == "allow"
    before = state_snapshot(page)
    result = route(
        page,
        {
            "expectedActiveCanvasId": CANVAS_ID,
            "edgeChanges": [
                {"id": EDGE_BC, "type": "select", "selected": True}
            ],
        },
    )
    after = state_snapshot(page)
    assert result["code"] == "APPLIED_SELECTION"
    assert [edge["id"] for edge in after["edges"]] == [EDGE_AB, EDGE_BC]
    assert after["selectedEdgeIds"] == [EDGE_BC]
    assert after["pastLength"] == before["pastLength"]
    corpus["current_snapshot_preserves_new_edge"] = result

    reset_fixture(page)
    route(
        page,
        {
            "expectedActiveCanvasId": CANVAS_ID,
            "nodeChanges": [
                {
                    "id": NODE_A,
                    "type": "dimensions",
                    "dimensions": {"width": 333, "height": 222},
                    "resizing": False,
                }
            ],
            "edgeChanges": [
                {"id": EDGE_AB, "type": "select", "selected": True}
            ],
        },
    )
    immediate_copy = page.evaluate(
        """({nodeA, nodeB, nodeC, edgeAB}) => {
          const state = window.__libtv_store.getState();
          state.selectElements({ nodeIds: [nodeA], edgeIds: [edgeAB] });
          state.duplicateSelectedNodes();
          const nextState = window.__libtv_store.getState();
          const nextCanvas = nextState.getActiveCanvas();
          const copiedNode = nextCanvas.nodes.find(
            (node) => ![nodeA, nodeB, nodeC].includes(node.id),
          );
          return {
            copiedNodeId: copiedNode?.id || null,
            runtimeFields: ["selected", "measured", "dragging", "resizing"].filter(
              (key) => Object.prototype.hasOwnProperty.call(copiedNode, key),
            ),
            selectedEdgeIds: nextState.selectedEdgeIds,
          };
        }""",
        {
            "nodeA": NODE_A,
            "nodeB": NODE_B,
            "nodeC": NODE_C,
            "edgeAB": EDGE_AB,
        },
    )
    sanitized = state_snapshot(page)
    copied_nodes = [
        node for node in sanitized["nodes"] if node["id"] not in {NODE_A, NODE_B, NODE_C}
    ]
    assert len(copied_nodes) == 1
    assert immediate_copy["copiedNodeId"] == copied_nodes[0]["id"]
    assert immediate_copy["runtimeFields"] == []
    assert immediate_copy["selectedEdgeIds"] == []
    assert sanitized["selectedEdgeIds"] == []
    assert sanitized["pastRuntimeFields"][-1]["nodes"] == [[], [], []]
    assert sanitized["pastRuntimeFields"][-1]["edges"] == [[]]
    corpus["history_copy_runtime_sanitation"] = {
        "copiedNodeId": copied_nodes[0]["id"],
        "copyCommitRuntimeFields": immediate_copy["runtimeFields"],
        "postMountMeasured": copied_nodes[0]["measured"],
        "historyRuntimeFields": sanitized["pastRuntimeFields"][-1],
    }

    assert_no_overflow(page)
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)
    return corpus


def center(rect):
    return {
        "x": rect["x"] + rect["width"] / 2,
        "y": rect["y"] + rect["height"] / 2,
    }


def run_real_callbacks(page: Page):
    errors = attach_errors(page)
    prepare(page)
    node = page.locator(f'.react-flow__node[data-id="{NODE_A}"]')
    node.click(force=True)
    page.wait_for_timeout(100)
    selected = state_snapshot(page)
    assert selected["selectedNodeIds"] == [NODE_A]
    assert all(not item["selectedPresent"] for item in selected["nodes"])

    drag_start = center(node.bounding_box())
    before_drag = state_snapshot(page)
    page.mouse.move(drag_start["x"], drag_start["y"])
    page.mouse.down()
    page.mouse.move(drag_start["x"] + 25, drag_start["y"] + 18, steps=3)
    first_frame = state_snapshot(page)
    page.mouse.move(drag_start["x"] + 70, drag_start["y"] + 46, steps=5)
    second_frame = state_snapshot(page)
    assert first_frame["pastLength"] == before_drag["pastLength"]
    assert second_frame["pastLength"] == before_drag["pastLength"]
    page.mouse.up()
    page.wait_for_timeout(160)
    after_drag = state_snapshot(page)
    assert after_drag["pastLength"] == before_drag["pastLength"] + 1
    assert after_drag["nodes"][0]["position"] != before_drag["nodes"][0]["position"]

    history_before_noop = after_drag["pastLength"]
    current_box = node.bounding_box()
    current_center = center(current_box)
    page.mouse.move(current_center["x"], current_center["y"])
    page.mouse.down()
    page.mouse.up()
    page.wait_for_timeout(100)
    after_noop = state_snapshot(page)
    assert after_noop["pastLength"] == history_before_noop

    edge = page.locator(f'.react-flow__edge[data-id="{EDGE_AB}"]')
    page.locator(".react-flow__pane").click(position={"x": 780, "y": 730})
    page.wait_for_timeout(80)
    assert state_snapshot(page)["selectedNodeIds"] == []
    edge.locator('path[stroke="transparent"]').click(force=True)
    page.wait_for_timeout(280)
    edge_selected = state_snapshot(page)
    assert edge_selected["selectedEdgeIds"] == [EDGE_AB]
    assert edge_selected["selectedNodeIds"] == []
    assert edge_selected["edges"][0]["selectedPresent"] is False
    assert "selected" in (edge.get_attribute("class") or "").split()
    delete_button = page.locator(f'[data-edge-delete="{EDGE_AB}"]')
    assert delete_button.count() == 1
    assert delete_button.evaluate("(element) => getComputedStyle(element).opacity") == "1"

    before_delete = state_snapshot(page)
    delete_button.click()
    page.wait_for_timeout(120)
    after_delete = state_snapshot(page)
    assert after_delete["edges"] == []
    assert after_delete["selectedEdgeIds"] == []
    assert after_delete["pastLength"] == before_delete["pastLength"] + 1

    page.keyboard.press("Meta+z")
    page.wait_for_timeout(120)
    after_undo = state_snapshot(page)
    assert [item["id"] for item in after_undo["edges"]] == [EDGE_AB]
    assert after_undo["selectedEdgeIds"] == []

    page.keyboard.press("Meta+Shift+z")
    page.wait_for_timeout(120)
    after_redo = state_snapshot(page)
    assert after_redo["edges"] == []
    assert after_redo["selectedEdgeIds"] == []

    callback_log = page.evaluate("() => window.__libtv_react_flow_change_log")
    assert callback_log
    assert all(
        entry["result"]["status"] == "applied" for entry in callback_log
    ), callback_log
    observed_node_types = sorted(
        {
            change["type"]
            for entry in callback_log
            for change in entry["request"].get("nodeChanges", [])
        }
    )
    observed_edge_types = sorted(
        {
            change["type"]
            for entry in callback_log
            for change in entry["request"].get("edgeChanges", [])
        }
    )
    assert "select" in observed_node_types
    assert "position" in observed_node_types
    assert observed_edge_types == ["select"]
    assert_no_overflow(page)
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)
    return {
        "observedNodeChangeTypes": observed_node_types,
        "observedEdgeChangeTypes": observed_edge_types,
        "callbackLog": callback_log,
        "drag": {
            "historyBefore": before_drag["pastLength"],
            "historyDuringFirstFrame": first_frame["pastLength"],
            "historyDuringSecondFrame": second_frame["pastLength"],
            "historyAfterStop": after_drag["pastLength"],
            "historyAfterNoop": after_noop["pastLength"],
        },
        "edgeSelectionSemanticFieldAbsent": True,
        "namedDeleteUndoRedo": True,
    }


def run_mobile(page: Page):
    errors = attach_errors(page)
    prepare(page)
    edge = page.locator(f'.react-flow__edge[data-id="{EDGE_AB}"]')
    edge.locator('path[stroke="transparent"]').click(force=True)
    page.wait_for_timeout(100)
    state = state_snapshot(page)
    assert state["selectedEdgeIds"] == [EDGE_AB]
    assert state["edges"][0]["selectedPresent"] is False
    assert_no_overflow(page)
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)
    return {
        "viewport": page.viewport_size,
        "selectedEdgeIds": state["selectedEdgeIds"],
        "semanticSelectedFieldAbsent": True,
        "noOverflow": True,
    }


def run_static_checks():
    page_source = PAGE_PATH.read_text()
    store_source = STORE_PATH.read_text()
    routing_source = ROUTING_PATH.read_text()
    assert "applyNodeChanges" not in page_source
    assert "applyEdgeChanges" not in page_source
    assert "routeReactFlowChanges" in page_source
    assert "selectedEdgeIds" in store_source
    assert "planLibTVReactFlowChanges" in store_source
    for variant in [
        'case "select"',
        'case "position"',
        'case "dimensions"',
        'case "add"',
        'case "remove"',
        'case "replace"',
    ]:
        assert variant in routing_source
    return {
        "routeHasNoGenericReducers": True,
        "edgeSelectionOwnerPresent": True,
        "exactNodeVariantsPresent": [
            "select",
            "position",
            "dimensions",
            "add",
            "remove",
            "replace",
        ],
        "exactEdgeVariantsPresent": ["select", "add", "remove", "replace"],
    }


def main():
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    static_checks = run_static_checks()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        corpus_page = browser.new_page(
            viewport={"width": 929, "height": 874},
            device_scale_factor=1,
        )
        synthetic_corpus = run_synthetic_corpus(corpus_page)
        corpus_page.close()

        callback_page = browser.new_page(
            viewport={"width": 929, "height": 874},
            device_scale_factor=1,
        )
        real_callbacks = run_real_callbacks(callback_page)
        callback_page.close()

        mobile_page = browser.new_page(
            viewport={"width": 390, "height": 844},
            device_scale_factor=1,
        )
        mobile = run_mobile(mobile_page)
        mobile_page.close()

        browser.close()

    audit = {
        "batch": 61,
        "date": "2026-08-27",
        "status": "SCRIPT_RECORDED_PASS",
        "url": URL,
        "fixture": "LIBTV-FIX-LOCAL-REACT-FLOW-CHANGES-01",
        "verifier": "LIBTV-VR-016",
        "staticChecks": static_checks,
        "syntheticCorpus": synthetic_corpus,
        "realCallbacks": real_callbacks,
        "mobile": mobile,
        "screenshots": {
            "newScreenshotRequired": False,
            "reason": "No visual geometry or styling changed; Batch 57 and Batch 60 remain the visual regression authorities.",
        },
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        "Batch 61 verification passed: whole-batch classification, current "
        "snapshot routing, node/edge selection projection, drag history, "
        "runtime-field sanitation, semantic rejection, named edge delete "
        "undo/redo, mobile overflow and browser diagnostics."
    )


if __name__ == "__main__":
    main()
