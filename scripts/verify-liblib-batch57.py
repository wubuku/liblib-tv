import json
import os
from pathlib import Path

from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch57-2026-08-27"
    / "runtime-audit.json"
)
URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")


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


def box(locator: Locator):
    result = locator.bounding_box()
    assert result is not None
    return result


def center(rect):
    return {
        "x": rect["x"] + rect["width"] / 2,
        "y": rect["y"] + rect["height"] / 2,
    }


def assert_no_overflow(page: Page):
    assert page.evaluate(
        "() => document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )
    assert page.evaluate(
        "() => document.body.scrollWidth <= document.body.clientWidth"
    )


def switch_to_empty_canvas(page: Page):
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(350)
    page.locator("[data-canvas-trigger]").click()
    page.locator('[data-canvas-row="canvas-1"] button').first.click()
    page.wait_for_timeout(180)
    assert page.locator(".react-flow__node").count() == 0
    assert page.locator(".react-flow__edge").count() == 0


def add_text_node(page: Page) -> str:
    page.get_by_role("button", name="添加节点").click()
    page.locator('[data-add-node-entry="text"]').click()
    node = page.locator(".react-flow__node-text").last
    node.wait_for(state="visible")
    node_id = node.get_attribute("data-id")
    assert node_id
    return node_id


def move_node(page: Page, node_id: str, target_x: float, target_y: float):
    node = page.locator(f'.react-flow__node[data-id="{node_id}"]')
    start = center(box(node))
    page.mouse.move(start["x"], start["y"])
    page.mouse.down()
    page.mouse.move(target_x, target_y, steps=8)
    page.mouse.up()
    page.wait_for_timeout(120)


def handle(page: Page, node_id: str, handle_id: str) -> Locator:
    result = page.locator(
        f'.react-flow__node[data-id="{node_id}"] '
        f'.react-flow__handle[data-handleid="{handle_id}"]'
    )
    assert result.count() == 1, (node_id, handle_id, result.count())
    return result


def drag_handle(page: Page, source_node_id: str, source_handle_id: str, target_node_id: str, target_handle_id: str):
    source = center(box(handle(page, source_node_id, source_handle_id)))
    target = center(box(handle(page, target_node_id, target_handle_id)))
    page.mouse.move(source["x"], source["y"])
    page.mouse.down()
    page.mouse.move(target["x"], target["y"], steps=16)
    page.mouse.up()
    page.wait_for_timeout(220)


def graph_state(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          const canvas = state.getActiveCanvas();
          const history = state.historyByCanvas[state.activeCanvasId] || { past: [], future: [] };
          return {
            nodes: (canvas?.nodes || []).map((node) => ({
              id: node.id,
              type: node.type,
              position: node.position,
            })),
            edges: (canvas?.edges || []).map((edge) => ({
              id: edge.id,
              source: edge.source,
              sourceHandle: edge.sourceHandle,
              target: edge.target,
              targetHandle: edge.targetHandle,
            })),
            selectedNodeIds: state.selectedNodeIds,
            selectedNodeId: state.selectedNodeId,
            pastLength: history.past.length,
            futureLength: history.future.length,
          };
        }"""
    )


def edge_between(state, source_id: str, target_id: str):
    return next(
        (
            edge
            for edge in state["edges"]
            if edge["source"] == source_id and edge["target"] == target_id
        ),
        None,
    )


def validation(page: Page, proposal):
    return page.evaluate(
        "(proposal) => window.__libtv_validate_connection(proposal)",
        proposal,
    )


def run_source_start(page: Page, viewport_label: str):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    first_id = add_text_node(page)
    if page.viewport_size["width"] <= 390:
        move_node(page, first_id, 195, 250)
    else:
        move_node(page, first_id, 465, 180)
    second_id = add_text_node(page)
    if page.viewport_size["width"] <= 390:
        move_node(page, second_id, 195, 650)
    else:
        move_node(page, second_id, 465, 420)

    before = graph_state(page)
    drag_handle(page, first_id, "source", second_id, "target")
    after = graph_state(page)
    edge = edge_between(after, first_id, second_id)

    assert len(after["edges"]) == len(before["edges"]) + 1
    assert edge is not None
    assert edge["sourceHandle"] == "source"
    assert edge["targetHandle"] == "target"
    assert after["selectedNodeIds"] == before["selectedNodeIds"]
    assert after["pastLength"] == before["pastLength"] + 1

    page.screenshot(
        path=str(
            REFERENCE_DIR
            / f"liblib-clone-batch57-connection-accepted-{viewport_label}-2026-08-27.png"
        )
    )

    page.keyboard.press("Meta+z")
    page.wait_for_timeout(180)
    undone = graph_state(page)
    assert edge_between(undone, first_id, second_id) is None
    assert len(undone["edges"]) == len(before["edges"])
    assert undone["pastLength"] == before["pastLength"]
    assert undone["futureLength"] == 1

    page.keyboard.press("Meta+Shift+z")
    page.wait_for_timeout(180)
    redone = graph_state(page)
    assert edge_between(redone, first_id, second_id) is not None
    assert redone["selectedNodeIds"] == []
    assert_no_overflow(page)
    assert not errors, errors

    return {
        "viewport": page.viewport_size,
        "source_node_id": first_id,
        "target_node_id": second_id,
        "edge": edge,
        "history_before": before["pastLength"],
        "history_after": after["pastLength"],
        "selection_before": before["selectedNodeIds"],
        "selection_after": after["selectedNodeIds"],
        "selection_after_redo": redone["selectedNodeIds"],
    }


def run_target_start(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    source_id = add_text_node(page)
    move_node(page, source_id, 220, 330)
    target_id = add_text_node(page)
    move_node(page, target_id, 650, 330)

    before = graph_state(page)
    drag_handle(page, target_id, "target", source_id, "source")
    after = graph_state(page)
    edge = edge_between(after, source_id, target_id)

    assert len(after["edges"]) == len(before["edges"]) + 1
    assert edge is not None
    assert edge["source"] == source_id
    assert edge["sourceHandle"] == "source"
    assert edge["target"] == target_id
    assert edge["targetHandle"] == "target"
    assert not edge_between(after, target_id, source_id)
    assert after["pastLength"] == before["pastLength"] + 1

    raw_target_start = validation(
        page,
        {
            "origin": "programmatic",
            "sourceNodeId": target_id,
            "sourceHandleId": "target",
            "targetNodeId": source_id,
            "targetHandleId": "source",
            "startedFromHandleType": "target",
        },
    )
    assert raw_target_start["status"] == "reject"
    assert raw_target_start["reason"] == "DUPLICATE_NODE_PAIR"

    normalized = page.evaluate(
        """({sourceId, targetId}) => window.__libtv_validate_connection({
          origin: "programmatic",
          sourceNodeId: targetId,
          sourceHandleId: "target",
          targetNodeId: sourceId,
          targetHandleId: "source",
          startedFromHandleType: "target",
        })""",
        {"sourceId": source_id, "targetId": target_id},
    )
    assert normalized["status"] == "reject"
    assert normalized["reason"] == "DUPLICATE_NODE_PAIR"
    assert_no_overflow(page)
    assert not errors, errors
    return {
        "source_node_id": source_id,
        "target_node_id": target_id,
        "edge": edge,
        "target_start_result_after_existing_edge": raw_target_start,
    }


def run_rejections(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    first_id = add_text_node(page)
    move_node(page, first_id, 465, 150)
    second_id = add_text_node(page)
    move_node(page, second_id, 465, 390)
    third_id = add_text_node(page)
    move_node(page, third_id, 465, 630)

    drag_handle(page, first_id, "source", second_id, "target")
    drag_handle(page, second_id, "source", third_id, "target")
    baseline = graph_state(page)
    assert edge_between(baseline, first_id, second_id)
    assert edge_between(baseline, second_id, third_id)

    cases = {
        "missing_endpoint": {
            "origin": "programmatic",
            "sourceNodeId": first_id,
            "sourceHandleId": "source",
            "targetNodeId": None,
            "targetHandleId": "target",
        },
        "dangling_endpoint": {
            "origin": "programmatic",
            "sourceNodeId": first_id,
            "sourceHandleId": "source",
            "targetNodeId": "missing-node",
            "targetHandleId": "target",
        },
        "invalid_handle_direction": {
            "origin": "programmatic",
            "sourceNodeId": first_id,
            "sourceHandleId": "target",
            "targetNodeId": third_id,
            "targetHandleId": "source",
        },
        "duplicate_forward": {
            "origin": "programmatic",
            "sourceNodeId": first_id,
            "sourceHandleId": "source",
            "targetNodeId": second_id,
            "targetHandleId": "target",
        },
        "duplicate_reverse": {
            "origin": "programmatic",
            "sourceNodeId": second_id,
            "sourceHandleId": "source",
            "targetNodeId": first_id,
            "targetHandleId": "target",
        },
        "self_loop": {
            "origin": "programmatic",
            "sourceNodeId": first_id,
            "sourceHandleId": "source",
            "targetNodeId": first_id,
            "targetHandleId": "target",
        },
        "directed_cycle": {
            "origin": "programmatic",
            "sourceNodeId": third_id,
            "sourceHandleId": "source",
            "targetNodeId": first_id,
            "targetHandleId": "target",
        },
    }
    reasons = {}
    for name, proposal in cases.items():
        result = validation(page, proposal)
        assert result["status"] == "reject", (name, result)
        reasons[name] = result["reason"]

    assert reasons == {
        "missing_endpoint": "MISSING_ENDPOINT",
        "dangling_endpoint": "DANGLING_ENDPOINT",
        "invalid_handle_direction": "INVALID_HANDLE_DIRECTION",
        "duplicate_forward": "DUPLICATE_NODE_PAIR",
        "duplicate_reverse": "DUPLICATE_NODE_PAIR",
        "self_loop": "SELF_LOOP",
        "directed_cycle": "DIRECTED_CYCLE",
    }

    direct_result = page.evaluate(
        """({sourceId, targetId}) => window.__libtv_store.getState().addEdge({
          id: "e-batch57-rejected-direct",
          source: sourceId,
          sourceHandle: "source",
          target: targetId,
          targetHandle: "target",
          type: "default",
        })""",
        {"sourceId": third_id, "targetId": first_id},
    )
    assert direct_result["status"] == "reject"
    assert direct_result["reason"] == "DIRECTED_CYCLE"
    after = graph_state(page)
    assert after == baseline
    assert_no_overflow(page)
    assert not errors, errors

    return {
        "node_ids": [first_id, second_id, third_id],
        "baseline": baseline,
        "reasons": reasons,
        "direct_store_result": direct_result,
        "after_rejected_store_submit": after,
    }


def main():
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop_page = browser.new_page(
            viewport={"width": 929, "height": 874}, device_scale_factor=1
        )
        desktop = run_source_start(desktop_page, "desktop-929")
        desktop_page.close()

        mobile_page = browser.new_page(
            viewport={"width": 390, "height": 844}, device_scale_factor=1
        )
        mobile = run_source_start(mobile_page, "mobile-390")
        mobile_page.close()

        target_start_page = browser.new_page(
            viewport={"width": 929, "height": 874}, device_scale_factor=1
        )
        target_start = run_target_start(target_start_page)
        target_start_page.close()

        rejection_page = browser.new_page(
            viewport={"width": 929, "height": 874}, device_scale_factor=1
        )
        rejections = run_rejections(rejection_page)
        rejection_page.close()
        browser.close()

    AUDIT_PATH.write_text(
        json.dumps(
            {
                "url": URL,
                "contract": {
                    "normalization": "source_to_target",
                    "handles": {"source": "source", "target": "target"},
                    "accepted_transaction": "one_edge_one_history",
                    "rejected_transaction": "zero_graph_selection_history_mutation",
                    "domain_status": "not-evaluated",
                },
                "desktop": desktop,
                "mobile": mobile,
                "target_start": target_start,
                "rejections": rejections,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print(
        "Batch 57 Playwright verification passed: real source/target Handle drag, "
        "target-start normalization, accepted one-step history, undo/redo, "
        "structural rejection reasons, zero-mutation rejected store submit, "
        "desktop/mobile overflow and console diagnostics."
    )


if __name__ == "__main__":
    main()
