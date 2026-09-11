"""Jimeng clone batch 4 verifier — insert menu (+ handle) and node context menu.

Contract:
- "+" circle on node edge opens the 添加节点 menu (7 items); clicking 视频
  creates a new empty video node to the right with a connecting edge.
- Right-click on a node opens the context menu with shortcut rows and a
  disabled 重做; 删除 removes the node; Escape closes.
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
        page.wait_for_timeout(2200)

        # ── + handle insert menu ──
        node1 = page.locator(".react-flow__node-video").first
        node1.hover(position={"x": 400, "y": 160})
        page.wait_for_timeout(500)
        plus = page.evaluate(
            """() => {
                const n = [...document.querySelectorAll('.react-flow__node-video')][0];
                const nr = n.getBoundingClientRect();
                const btn = n.querySelector('button[aria-label="右侧添加节点"], span[role="button"][aria-label="右侧添加节点"]');
                if (!btn) {
                    const any = [...n.querySelectorAll('[aria-label="右侧添加节点"]')][0];
                    if (!any) return null;
                    const r = any.getBoundingClientRect();
                    return {x: r.x + r.width/2, y: r.y + r.height/2};
                }
                const r = btn.getBoundingClientRect();
                return {x: r.x + r.width/2, y: r.y + r.height/2};
            }"""
        )
        if not plus:
            failures.append("right + circle not visible on hover")
        else:
            page.mouse.click(plus["x"], plus["y"])
            page.wait_for_timeout(700)
            menu = page.evaluate(
                """() => {
                    const menus = [...document.querySelectorAll('[role="menu"]')]
                        .filter(m => m.textContent.includes('添加节点'));
                    const m = menus[menus.length - 1];
                    if (!m) return null;
                    const r = m.getBoundingClientRect();
                    return {
                        rect: [Math.round(r.width), Math.round(r.height)],
                        bg: getComputedStyle(m).backgroundColor,
                        items: [...m.querySelectorAll('[role="menuitem"]')].map(b => b.textContent.trim()),
                    };
                }"""
            )
            if not menu:
                failures.append("insert menu did not open after + click")
            else:
                if menu["bg"] != "rgb(38, 38, 38)":
                    failures.append(f"insert menu bg: {menu['bg']}")
                want = ["文本", "图片", "视频", "音频", "时间线", "主体", "导演台"]
                if menu["items"] != want:
                    failures.append(f"insert items: {menu['items']}")
            page.screenshot(
                path=str(REFERENCE_DIR / "jimeng-clone-batch4-insert-menu-1680.png")
            )
            # pick 视频 → new node + edge
            page.locator('[role="menuitem"]', has_text="视频").click()
            page.wait_for_timeout(900)
            counts = page.evaluate(
                """() => ({
                    nodes: document.querySelectorAll('.react-flow__node-video').length,
                    edges: document.querySelectorAll('.react-flow__edge').length,
                })"""
            )
            if counts["nodes"] != 3:
                failures.append(f"video nodes after add: {counts['nodes']} (want 3)")
            if counts["edges"] < 1:
                failures.append("no edge created after add")
            page.screenshot(
                path=str(REFERENCE_DIR / "jimeng-clone-batch4-node-added-1680.png")
            )
            # cleanup: delete the new node via context menu later; first close any menu
            page.keyboard.press("Escape")

        # ── node context menu ──
        node1 = page.locator(".react-flow__node-video").first
        node1.click(button="right", position={"x": 200, "y": 100})
        page.wait_for_timeout(700)
        cm = page.evaluate(
            """() => {
                const menus = [...document.querySelectorAll('[role="menu"]')]
                    .filter(m => m.textContent.includes('复制副本'));
                const m = menus[menus.length - 1];
                if (!m) return null;
                return {
                    items: [...m.querySelectorAll('[role="menuitem"]')].map(b => ({
                        label: b.textContent.trim().replace(/[⌘⇧Z⌫\s]+/g, ''),
                        disabled: b.disabled,
                    })),
                };
            }"""
        )
        if not cm:
            failures.append("context menu did not open on right click")
        else:
            labels = [i["label"] for i in cm["items"]]
            want = ["复制", "复制副本", "粘贴", "保存到主体库", "下载", "重做", "撤销", "删除"]
            if len(labels) != len(want) or not all(
                l.startswith(w) for l, w in zip(labels, want)
            ):
                failures.append(f"context items: {labels}")
            redo = next((i for i in cm["items"] if i["label"] == "重做"), None)
            if not redo or not redo["disabled"]:
                failures.append("重做 not disabled")
            page.screenshot(
                path=str(REFERENCE_DIR / "jimeng-clone-batch4-context-menu-1680.png")
            )
            # delete the node we added (cleanup + functional check)
            page.locator('[role="menuitem"]', has_text="删除").click()
            page.wait_for_timeout(700)
            after = page.evaluate(
                "() => document.querySelectorAll('.react-flow__node-video').length"
            )
            if after != 2:
                failures.append(f"nodes after delete: {after} (want 2)")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 4 menus contract")


if __name__ == "__main__":
    main()
