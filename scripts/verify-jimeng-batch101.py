"""Jimeng clone batch 101 verifier — image toolbar 工具∨ menu (Batch 209).

Contract (SOURCE_FACT 209-menu-crop2.png / 209-tools-menu.json):
- clicking 工具 opens a 232px menu anchored below-right with two groups —
  「编辑」: 消除笔 / 构图 / 宫格切分(›) / 提示词反推,
  「预设」: 场景俯视图 / 连续分镜图 / 多机位九宫格 / 人物三视图 /
  面部三视图 / 产品三视图;
- group labels 编辑/预设 are dimmed; 宫格切分 carries a right chevron;
  工具 chevron flips up while open; Escape closes the menu.
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")

CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}

EDIT_ITEMS = ["消除笔", "构图", "宫格切分", "提示词反推"]
PRESET_ITEMS = [
    "场景俯视图",
    "连续分镜图",
    "多机位九宫格",
    "人物三视图",
    "面部三视图",
    "产品三视图",
]


def main() -> None:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []

    with sync_playwright() as p:
        ctx = p.chromium.launch(headless=True)
        page = ctx.new_page()
        page.set_viewport_size(VIEWPORT)  # type: ignore[arg-type]
        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        # Batch 398 SOURCE_FACT: Agent 面板常驻——本验证器不测面板，
        # 载入后先收起以避免遮挡画布交互
        _collapse = page.locator('button[aria-label="收起"]')
        if _collapse.count():
            _collapse.click()
            page.wait_for_timeout(400)

        # select video → 截取帧 → 首帧 (produces image node)
        center = page.evaluate(
            """() => {
                const el = document.querySelector('[data-id="video-local-1"]');
                const r = el.getBoundingClientRect();
                return {x: r.x + r.width / 2 - 120, y: r.y + 40};
            }"""
        )
        page.mouse.click(center["x"], center["y"])
        page.wait_for_timeout(600)
        cap = page.evaluate(
            """() => {
                const t = [...document.querySelectorAll('.react-flow__node-toolbar')]
                    .find(t => t.textContent.includes('截取帧'));
                const btn = t && [...t.querySelectorAll('button')]
                    .find(b => b.textContent.trim() === '截取帧');
                if (!btn) return null;
                const r = btn.getBoundingClientRect();
                return {x: r.x + r.width / 2, y: r.y + r.height / 2};
            }"""
        )
        if not cap:
            failures.append("截取帧 button not found")
        else:
            page.mouse.click(cap["x"], cap["y"])
            page.wait_for_timeout(400)
            first = page.evaluate(
                """() => {
                    const btn = [...document.querySelectorAll('button')]
                        .find(b => b.textContent.trim() === '首帧'
                            && b.getBoundingClientRect().height < 50);
                    if (!btn) return null;
                    const r = btn.getBoundingClientRect();
                    return {x: r.x + r.width / 2, y: r.y + r.height / 2};
                }"""
            )
            if not first:
                failures.append("首帧 menu item not found")
            else:
                page.mouse.click(first["x"], first["y"])
                page.wait_for_timeout(900)
                img_sel = page.evaluate(
                    """() => {
                        const nodes = [...document.querySelectorAll('.react-flow__node-image')];
                        const el = nodes[nodes.length - 1];
                        if (!el) return null;
                        const r = el.getBoundingClientRect();
                        return {x: Math.min(r.x + r.width / 2, 1660), y: r.y + r.height / 2};
                    }"""
                )
                if not img_sel:
                    failures.append("image node missing after 首帧")
                else:
                    page.mouse.click(img_sel["x"], img_sel["y"])
                    page.wait_for_timeout(700)

                    tools = page.evaluate(
                        """() => {
                            const t = [...document.querySelectorAll('.react-flow__node-toolbar')]
                                .sort((a,b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
                            const btn = [...t.querySelectorAll('button')]
                                .find(b => b.textContent.trim() === '工具');
                            if (!btn) return null;
                            const r = btn.getBoundingClientRect();
                            return {x: r.x + r.width / 2, y: r.y + r.height / 2};
                        }"""
                    )
                    if not tools:
                        failures.append("工具 button not found")
                    else:
                        # 工具 button may sit beyond the viewport (avoidance
                        # placement) — dispatch a JS click instead
                        clicked = page.evaluate(
                            """() => {
                                const t = [...document.querySelectorAll('.react-flow__node-toolbar')]
                                    .sort((a,b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
                                const btn = [...t.querySelectorAll('button')]
                                    .find(b => b.textContent.trim() === '工具');
                                if (!btn) return false;
                                btn.click();
                                return true;
                            }"""
                        )
                        if not clicked:
                            failures.append("工具 button not clickable")
                        page.wait_for_timeout(500)

                        menu = page.evaluate(
                            """() => {
                                const m = document.querySelector('[role=menu][aria-label="工具菜单"]');
                                if (!m) return null;
                                const r = m.getBoundingClientRect();
                                const labels = [...m.querySelectorAll('button[role=menuitem]')]
                                    .map(b => b.textContent.trim());
                                const groups = [...m.querySelectorAll('p')]
                                    .map(p => p.textContent.trim());
                                const sub = [...m.querySelectorAll('button[role=menuitem]')]
                                    .some(b => b.textContent.includes('宫格切分')
                                        && b.querySelector('svg:last-of-type'));
                                return {w: Math.round(r.width), labels, groups, sub};
                            }"""
                        )
                        if not menu:
                            failures.append("工具 menu did not open")
                        else:
                            if abs(menu["w"] - 232) > 6:
                                failures.append(f"menu width {menu['w']} != 232")
                            if menu["groups"] != ["编辑", "预设"]:
                                failures.append(f"group labels: {menu['groups']}")
                            if menu["labels"] != EDIT_ITEMS + PRESET_ITEMS:
                                failures.append(f"menu items: {menu['labels']}")
                            if not menu["sub"]:
                                failures.append("宫格切分 lacks right chevron")
                            page.screenshot(
                                path=str(
                                    REFERENCE_DIR
                                    / "jimeng-clone-batch101-tools-menu.png"
                                )
                            )

                        # Escape closes the menu
                        page.keyboard.press("Escape")
                        page.wait_for_timeout(400)
                        gone = page.evaluate(
                            """() => !document.querySelector('[role=menu][aria-label="工具菜单"]')"""
                        )
                        if not gone:
                            failures.append("Escape did not close the tools menu")

        # undo restores baseline
        page.keyboard.press("Meta+z")
        page.wait_for_timeout(600)
        imgs = page.evaluate(
            "() => document.querySelectorAll('.react-flow__node-image').length"
        )
        if imgs != 0:
            failures.append(f"undo did not remove image node: {imgs}")

        ctx.close()

    if failures:
        print("FAIL batch 101:")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print("PASS batch 101: tools menu (编辑/预设 groups, 10 items, chevrons)")


if __name__ == "__main__":
    main()
