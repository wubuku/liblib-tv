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
    / "liblib-canvas-batch62-2026-08-27"
    / "runtime-audit.json"
)


def errors_for(page: Page):
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
    page.wait_for_timeout(350)
    page.evaluate(
        """() => {
          const canvasStore = window.__libtv_store;
          const uiStore = window.__libtv_ui_store;
          const state = canvasStore.getState();
          const canvas = state.getActiveCanvas();
          const nodeIds = (canvas?.nodes || []).map((node) => node.id);
          const edgeIds = (canvas?.edges || []).map((edge) => edge.id);
          canvasStore.setState({
            selectedNodeIds: nodeIds.length > 0 ? [nodeIds[0]] : [],
            selectedNodeId: nodeIds.length > 0 ? nodeIds[0] : null,
            selectedEdgeIds: edgeIds.length > 0 ? [edgeIds[0]] : [],
          });
          uiStore.getState().closeAllPanels();
          window.__libtv_batch62_fixture = {
            canvasId: state.activeCanvasId,
            nodeIds,
            edgeIds,
          };
        }"""
    )
    page.wait_for_timeout(120)


def fixture(page: Page):
    return page.evaluate("() => window.__libtv_batch62_fixture")


def selection(page: Page):
    return page.evaluate("() => window.__libtv_capture_selection()")


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
            canvasId: state.activeCanvasId,
            nodeIds: (canvas?.nodes || []).map((node) => node.id),
            edgeIds: (canvas?.edges || []).map((edge) => edge.id),
            selectedNodeIds: state.selectedNodeIds,
            selectedNodeId: state.selectedNodeId,
            selectedEdgeIds: state.selectedEdgeIds,
            pastLength: history.past.length,
            futureLength: history.future.length,
          };
        }"""
    )


def ui(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__libtv_ui_store.getState();
          return {
            isAddNodePanelOpen: state.isAddNodePanelOpen,
            isCanvasDropdownOpen: state.isCanvasDropdownOpen,
            isAssetPanelOpen: state.isAssetPanelOpen,
            isToolboxPanelOpen: state.isToolboxPanelOpen,
            isMaterialPanelOpen: state.isMaterialPanelOpen,
            isCharacterPanelOpen: state.isCharacterPanelOpen,
            isHistoryPanelOpen: state.isHistoryPanelOpen,
            isShortcutsPanelOpen: state.isShortcutsPanelOpen,
            isTutorialPanelOpen: state.isTutorialPanelOpen,
            isNotificationOpen: state.isNotificationOpen,
            isUserMenuOpen: state.isUserMenuOpen,
            isSharePanelOpen: state.isSharePanelOpen,
            isAgentOpen: state.isAgentOpen,
            isZoomMenuOpen: state.isZoomMenuOpen,
            activePrimaryPanel: state.activePrimaryPanel,
          };
        }"""
    )


def set_selection(page: Page, node_ids, edge_ids):
    page.evaluate(
        """({nodeIds, edgeIds}) => {
          const state = window.__libtv_store.getState();
          state.selectElements({ nodeIds, edgeIds });
        }""",
        {"nodeIds": node_ids, "edgeIds": edge_ids},
    )
    page.wait_for_timeout(80)


def set_foreground(page: Page, key: str):
    page.evaluate(
        """(key) => {
          const ui = window.__libtv_ui_store;
          ui.setState({
            isAddNodePanelOpen: false,
            isCanvasDropdownOpen: false,
            isAssetPanelOpen: false,
            isToolboxPanelOpen: false,
            isMaterialPanelOpen: false,
            isCharacterPanelOpen: false,
            isHistoryPanelOpen: false,
            isShortcutsPanelOpen: false,
            isTutorialPanelOpen: false,
            isNotificationOpen: false,
            isUserMenuOpen: false,
            isSharePanelOpen: false,
            isAgentOpen: false,
            isZoomMenuOpen: false,
            activePrimaryPanel: null,
            isZoomMenuOpen: key === "zoom",
            isShortcutsPanelOpen: key === "shortcuts",
            isCanvasDropdownOpen: key === "canvas-dropdown",
            isAddNodePanelOpen: key === "add-node",
            isSharePanelOpen: key === "share",
            isNotificationOpen: key === "notification",
            isUserMenuOpen: key === "user-menu",
            activePrimaryPanel: key === "primary-panel" ? "toolbox" : null,
          });
        }""",
        key,
    )
    page.wait_for_timeout(80)


def run_selection_snapshot(page: Page):
    item = fixture(page)
    assert item["nodeIds"], "fixture requires at least one node"
    node_id = item["nodeIds"][0]
    edge_id = item["edgeIds"][0] if item["edgeIds"] else None
    result = page.evaluate(
        """({nodeId, edgeId}) => {
          const store = window.__libtv_store;
          store.setState({
            selectedNodeIds: ["stale", nodeId, nodeId],
            selectedNodeId: "stale",
            selectedEdgeIds: edgeId ? [edgeId, edgeId, "stale-edge"] : [],
          });
          return window.__libtv_capture_selection();
        }""",
        {"nodeId": node_id, "edgeId": edge_id},
    )
    assert result["nodeIds"] == [node_id], result
    assert result["edgeIds"] == ([edge_id] if edge_id else []), result
    assert result["kind"] == ("mixed" if edge_id else "node"), result
    assert result["primary"] == {"kind": "node", "id": node_id}, result
    return result


def run_captured_command(page: Page):
    item = fixture(page)
    assert len(item["nodeIds"]) >= 2, "fixture requires at least two nodes"
    first, second = item["nodeIds"][:2]
    page.evaluate(
        """({first, second}) => {
          const state = window.__libtv_store.getState();
          state.selectElements({ nodeIds: [first], edgeIds: [] });
          const snapshot = state.getSelectionSnapshot();
          state.selectElements({ nodeIds: [second], edgeIds: [] });
          state.removeSelectedNodes(snapshot.nodeIds);
        }""",
        {"first": first, "second": second},
    )
    page.wait_for_timeout(100)
    result = graph(page)
    assert first not in result["nodeIds"], result
    assert second in result["nodeIds"], result
    assert result["pastLength"] == 1, result
    return {"capturedNodeIds": [first], "remainingNodeId": second, "graph": result}


def run_foreground_escape(page: Page):
    item = fixture(page)
    node_id = item["nodeIds"][0]
    edge_id = item["edgeIds"][0] if item["edgeIds"] else None
    set_selection(page, [node_id], [edge_id] if edge_id else [])
    before = graph(page)
    cases = {}

    for surface in [
        "shortcuts",
        "canvas-dropdown",
        "add-node",
        "zoom",
        "share",
        "notification",
        "user-menu",
        "primary-panel",
    ]:
        set_selection(page, [node_id], [edge_id] if edge_id else [])
        set_foreground(page, surface)
        page.keyboard.press("Delete")
        blocked = graph(page)
        assert blocked["nodeIds"] == before["nodeIds"], (surface, blocked)
        assert blocked["edgeIds"] == before["edgeIds"], (surface, blocked)
        assert blocked["pastLength"] == before["pastLength"], (surface, blocked)
        assert selection(page)["nodeIds"] == [node_id], (surface, selection(page))

        page.keyboard.press("Escape")
        after_first_escape = graph(page)
        assert resolve_surface_closed(page), (surface, ui(page))
        assert after_first_escape["nodeIds"] == before["nodeIds"], (surface, after_first_escape)
        assert after_first_escape["selectedNodeIds"] == [node_id], (surface, after_first_escape)
        assert after_first_escape["selectedEdgeIds"] == ([edge_id] if edge_id else []), (
            surface,
            after_first_escape,
        )

        page.keyboard.press("Escape")
        after_second_escape = graph(page)
        assert after_second_escape["selectedNodeIds"] == [], (surface, after_second_escape)
        assert after_second_escape["selectedNodeId"] is None, (surface, after_second_escape)
        assert after_second_escape["selectedEdgeIds"] == [], (surface, after_second_escape)
        assert page.locator("[data-libtv-canvas-focus-root]").evaluate(
            "() => document.activeElement === document.querySelector('[data-libtv-canvas-focus-root]')"
        ), surface
        cases[surface] = {
            "blockedDelete": True,
            "firstEscapePreservedSelection": True,
            "secondEscapeClearedSelection": True,
            "focusRoot": True,
        }

    return cases


def resolve_surface_closed(page: Page):
    state = ui(page)
    return not any(
        [
            state["isAddNodePanelOpen"],
            state["isCanvasDropdownOpen"],
            state["isShortcutsPanelOpen"],
            state["isZoomMenuOpen"],
            state["isSharePanelOpen"],
            state["isNotificationOpen"],
            state["isUserMenuOpen"],
            state["activePrimaryPanel"],
        ]
    )


def run_editable_boundaries(page: Page):
    item = fixture(page)
    node_id = item["nodeIds"][0]
    set_foreground(page, "none")
    set_selection(page, [node_id], [])
    before = graph(page)
    result = {}

    for name, markup in [
        ("input", '<input id="batch62-input" value="text">'),
        ("textarea", '<textarea id="batch62-textarea">text</textarea>'),
        ("select", '<select id="batch62-select"><option>one</option></select>'),
        ("contenteditable", '<div id="batch62-contenteditable" contenteditable="true">text</div>'),
        ("role-textbox", '<div id="batch62-role-textbox" role="textbox" tabindex="0">text</div>'),
        ("role-searchbox", '<div id="batch62-role-searchbox" role="searchbox" tabindex="0">text</div>'),
        ("role-combobox", '<div id="batch62-role-combobox" role="combobox" tabindex="0">text</div>'),
    ]:
        page.evaluate(
            """(markup) => {
              document.querySelector("#batch62-editable-fixture")?.remove();
              const wrapper = document.createElement("div");
              wrapper.id = "batch62-editable-fixture";
              wrapper.innerHTML = markup;
              document.body.append(wrapper);
            }""",
            markup,
        )
        page.locator(f"#batch62-{name}").focus()
        page.keyboard.press("Delete")
        page.keyboard.press("Escape")
        after = graph(page)
        assert after == before, (name, before, after)
        result[name] = {"deleteAndEscapePassedThrough": True}

    page.evaluate(
        """() => {
          const wrapper = document.querySelector("#batch62-editable-fixture");
          wrapper?.remove();
          const target = document.createElement("button");
          target.id = "batch62-composing-target";
          document.body.append(target);
          target.focus();
          const event = new KeyboardEvent("keydown", {
            key: "Escape",
            bubbles: true,
            cancelable: true,
            isComposing: true,
          });
          target.dispatchEvent(event);
          target.remove();
        }"""
    )
    assert graph(page) == before
    result["ime-composition"] = {"escapePassedThrough": True}
    return result


def run_pane_cleanup(page: Page):
    item = fixture(page)
    node_id = item["nodeIds"][0]
    edge_id = item["edgeIds"][0] if item["edgeIds"] else None
    set_foreground(page, "none")
    set_selection(page, [node_id], [edge_id] if edge_id else [])
    pane = page.locator(".react-flow__pane")
    assert pane.count() == 1
    pane.click(position={"x": 820, "y": 640}, force=True)
    page.wait_for_timeout(100)
    after = graph(page)
    assert after["selectedNodeIds"] == [], after
    assert after["selectedEdgeIds"] == [], after
    assert page.locator("[data-libtv-canvas-focus-root]").evaluate(
        "() => document.activeElement === document.querySelector('[data-libtv-canvas-focus-root]')"
    )
    return {"selectionCleared": True, "focusRoot": True}


def run_desktop(page: Page):
    errors = errors_for(page)
    prepare(page)
    snapshot = run_selection_snapshot(page)
    # Reload gives the captured-command scenario a fresh graph without relying
    # on undo as fixture teardown.
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(350)
    prepare(page)
    captured_command = run_captured_command(page)
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(350)
    prepare(page)
    foreground = run_foreground_escape(page)
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(350)
    prepare(page)
    editable = run_editable_boundaries(page)
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(350)
    prepare(page)
    pane = run_pane_cleanup(page)
    assert_no_overflow(page)
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)
    return {
        "selectionSnapshot": snapshot,
        "capturedCommand": captured_command,
        "foreground": foreground,
        "editable": editable,
        "pane": pane,
        "noOverflow": True,
    }


def run_mobile(page: Page):
    errors = errors_for(page)
    prepare(page)
    item = fixture(page)
    node_id = item["nodeIds"][0]
    set_foreground(page, "shortcuts")
    set_selection(page, [node_id], [])
    page.keyboard.press("Escape")
    assert resolve_surface_closed(page)
    page.keyboard.press("Escape")
    assert selection(page)["kind"] == "none"
    assert_no_overflow(page)
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)
    return {
        "surfaceCloseAndSelectionClear": True,
        "noOverflow": True,
    }


def main():
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop_page = browser.new_page(
            viewport={"width": 929, "height": 874},
            device_scale_factor=1,
        )
        desktop = run_desktop(desktop_page)
        desktop_page.close()

        mobile_page = browser.new_page(
            viewport={"width": 390, "height": 844},
            device_scale_factor=1,
        )
        mobile = run_mobile(mobile_page)
        mobile_page.close()
        browser.close()

    audit = {
        "batch": 62,
        "status": "SCRIPT_RECORDED_PASS",
        "contract": {
            "scope": "clone-owned selection command snapshot, editable/IME boundary, "
            "blocking foreground surface suspension, one-Escape and canvas focus root",
            "source_exact_modal_focus": False,
            "universal_mixed_primary": False,
            "graph_mutation_from_selection_context": False,
        },
        "desktop": desktop,
        "mobile": mobile,
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 62 Playwright verification passed: selection snapshots, captured "
        "command IDs, foreground shortcut suspension, one-Escape cleanup, "
        "editable/IME pass-through, pane cleanup, focus root, mobile bounds and diagnostics."
    )


if __name__ == "__main__":
    main()
