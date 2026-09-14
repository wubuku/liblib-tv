"""Jimeng clone batch 64 verifier — multi-select context menu.

Contract (SOURCE_FACT batch 64, 64-multiselect-contextmenu.png):
- right-click with ≥2 nodes selected → menu variant: 复制/复制副本/粘贴 ｜
  编组 ｜ 下载(disabled, title 导出前请保存画布) ｜ 重做/撤销/删除;
  no 保存到主体库 item.
- 编组 click links data-group-id on both nodes; ⌘⇧G clears.
- multi 复制副本 duplicates the whole selection (+2 nodes, one undo step).
- single-select right-click keeps the original menu (保存到主体库, no 编组).
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")

CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}


def main() -> None:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []

    with sync_playwright() as p:
        ctx = p.chromium.launch(headless=True)
        page = ctx.new_page()
        page.set_viewport_size(VIEWPORT)  # type: ignore[arg-type]
        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        def center(node_id):
            return page.evaluate(
                """(id) => { const n = document.querySelector(`[data-id="${id}"]`);
                    const r = n.getBoundingClientRect();
                    return {x: r.x + 60, y: r.y + 20}; }""",
                node_id,
            )

        # ---- multi-select (retry: known timing flake) ----
        selected = 0
        for _attempt in range(3):
            page.mouse.click(300, 750)
            page.wait_for_timeout(300)
            c1 = center("video-local-1")
            c2 = center("video-empty-1")
            page.mouse.click(c1["x"], c1["y"])
            page.wait_for_timeout(300)
            page.keyboard.down("Shift")
            page.mouse.click(c2["x"], c2["y"])
            page.keyboard.up("Shift")
            page.wait_for_timeout(800)
            selected = page.evaluate(
                "() => document.querySelectorAll('.react-flow__node.selected').length"
            )
            if selected == 2:
                break
        if selected != 2:
            failures.append(f"multi-select failed: selected={selected}")

        # ---- right-click on first selected node ----
        c1 = center("video-local-1")
        page.mouse.click(c1["x"] + 140, c1["y"] + 130, button="right")
        page.wait_for_timeout(700)
        menu = page.evaluate(
            """() => {
                const menu = document.querySelector('[role="menu"]');
                if (!menu) return null;
                const items = [...menu.querySelectorAll('button[role="menuitem"]')]
                    .map(b => ({label: (b.textContent.trim().match(/^[\u4e00-\u9fff]+/) || [''])[0],
                                disabled: b.disabled, title: b.title || null}));
                return items;
            }"""
        )
        if not menu:
            failures.append("context menu not rendered on multi right-click")
        else:
            labels = [m["label"] for m in menu]
            page.screenshot(
                path=str(REFERENCE_DIR / "jimeng-clone-batch64-context-menu.png")
            )
            for want in ["复制", "复制副本", "粘贴", "编组", "下载", "重做", "撤销", "删除"]:
                if want not in labels:
                    failures.append(f"multi menu missing {want}: {labels}")
            if "保存到主体库" in labels:
                failures.append("multi menu should not contain 保存到主体库")
            dl = next((m for m in menu if m["label"].startswith("下载")), None)
            if not dl or not dl["disabled"] or dl["title"] != "导出前请保存画布":
                failures.append(f"multi 下载 disabled state wrong: {dl}")

            # ---- 编组 via menu ----
            grp = next((m for m in menu if m["label"].startswith("编组")), None)
            page.evaluate(
                """() => [...document.querySelectorAll('button[role="menuitem"]')]
                    .find(b => b.textContent.trim().startsWith('编组'))?.click()"""
            )
            page.wait_for_timeout(700)
            linked = page.evaluate(
                """() => {
                    const a = document.querySelector('[data-id="video-local-1"] [data-group-id]');
                    const b = document.querySelector('[data-id="video-empty-1"] [data-group-id]');
                    return !!a && !!b
                        && a.getAttribute('data-group-id') === b.getAttribute('data-group-id');
                }"""
            )
            if not linked:
                failures.append("menu 编组 did not link group ids")

            # ---- 解除编组 via shortcut, restore selection ----
            page.keyboard.press("Meta+Shift+g")
            page.wait_for_timeout(600)
            page.mouse.click(300, 750)
            page.wait_for_timeout(300)
            c1 = center("video-local-1")
            c2 = center("video-empty-1")
            page.mouse.click(c1["x"], c1["y"])
            page.wait_for_timeout(300)
            page.keyboard.down("Shift")
            page.mouse.click(c2["x"], c2["y"])
            page.keyboard.up("Shift")
            page.wait_for_timeout(700)

        # ---- multi 复制副本 duplicates the whole selection ----
        n0 = page.evaluate("() => document.querySelectorAll('.react-flow__node').length")
        page.mouse.click(c1["x"] + 140, c1["y"] + 130, button="right")
        page.wait_for_timeout(700)
        page.evaluate(
            """() => [...document.querySelectorAll('button[role="menuitem"]')]
                .find(b => b.textContent.trim().startsWith('复制副本'))?.click()"""
        )
        page.wait_for_timeout(800)
        n1 = page.evaluate("() => document.querySelectorAll('.react-flow__node').length")
        if n1 != n0 + 2:
            failures.append(f"multi 复制副本 node count: {n1} want {n0 + 2}")
        page.keyboard.press("Meta+z")
        page.wait_for_timeout(600)
        n2 = page.evaluate("() => document.querySelectorAll('.react-flow__node').length")
        if n2 != n0:
            failures.append(f"multi 复制副本 undo: {n2} want {n0}")

        # ---- single-select right-click keeps original menu ----
        page.mouse.click(300, 750)
        page.wait_for_timeout(300)
        c1 = center("video-local-1")
        page.mouse.click(c1["x"], c1["y"])
        page.wait_for_timeout(400)
        page.mouse.click(c1["x"] + 140, c1["y"] + 130, button="right")
        page.wait_for_timeout(700)
        single = page.evaluate(
            """() => {
                const menu = document.querySelector('[role="menu"]');
                if (!menu) return null;
                return [...menu.querySelectorAll('button[role="menuitem"]')]
                    .map(b => (b.textContent.trim().match(/^[\u4e00-\u9fff]+/) || [''])[0]);
            }"""
        )
        if not single:
            failures.append("single context menu not rendered")
        else:
            labels = single
            if "保存到主体库" not in labels:
                failures.append(f"single menu lost 保存到主体库: {labels}")
            if "编组" in labels:
                failures.append("single menu should not contain 编组")
            dl_idx = labels.index("下载") if "下载" in labels else -1
            if dl_idx >= 0:
                dis = page.evaluate(
                    """() => [...document.querySelectorAll('button[role="menuitem"]')]
                        .find(b => b.textContent.trim().startsWith('下载'))?.disabled"""
                )
                if dis:
                    failures.append("single 下载 should be enabled")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 64 multi-select context menu contract")


if __name__ == "__main__":
    main()
