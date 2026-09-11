"""Jimeng clone batch 2 verifier — selected-node floating toolbar.

Contract: selecting the local-upload video node shows the NodeToolbar above it
with 7 labeled items (VIP diamonds, 截取帧 dropdown) + divider + 2 icon buttons;
the 截取帧 dropdown opens with 首帧/尾帧/自定义; deselect hides the toolbar.
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

        def toolbar_state() -> dict:
            return page.evaluate(
                """() => {
                    const labels = ['局部重拍','智能超清','视频编辑','截取帧','补帧','视频修剪','提示词反推'];
                    const tbs = [...document.querySelectorAll('.jimeng-node-toolbar')];
                    const tb = tbs[0];
                    return {
                        visible: !!tb && tb.getBoundingClientRect().height >= 30,
                        missing: labels.filter(l => !tb || !tb.textContent.includes(l)),
                        vipCount: tb ? tb.querySelectorAll('svg[viewBox="0 0 14 14"]').length : 0,
                        iconButtons: tb ? [...tb.querySelectorAll('button[aria-label]')].map(b => b.getAttribute('aria-label')) : [],
                        divider: !!tb?.querySelector('.jimeng-node-toolbar-divider'),
                    };
                }"""
            )

        before = toolbar_state()
        if before["visible"]:
            failures.append("toolbar visible before selection (should be hidden)")

        node1 = page.locator(".react-flow__node-video").first
        node1.click(position={"x": 200, "y": 100})
        page.wait_for_timeout(700)
        after = toolbar_state()

        if not after["visible"]:
            failures.append("toolbar not visible after node selection")
        if after["missing"]:
            failures.append(f"toolbar missing labels: {after['missing']}")
        if after["vipCount"] != 4:
            failures.append(f"vip diamond count: want 4, got {after['vipCount']}")
        if after["iconButtons"] != ["全屏预览", "下载"]:
            failures.append(f"tail icon buttons: {after['iconButtons']}")
        if not after["divider"]:
            failures.append("divider missing")

        # selection ring on card
        ring = page.evaluate(
            """() => {
                const card = document.querySelector('.react-flow__node.selected > div > div.relative');
                return card ? getComputedStyle(card).boxShadow : '';
            }"""
        )
        if "1.5px" not in ring:
            failures.append(f"selection ring missing: {ring!r}")

        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch2-selected-toolbar-1680.png")
        )

        # 截取帧 dropdown
        page.locator(".jimeng-node-toolbar button", has_text="截取帧").click()
        page.wait_for_timeout(500)
        menu = page.evaluate(
            """() => {
                const menus = [...document.querySelectorAll('div')]
                    .filter(d => d.textContent.trim().startsWith('首帧')
                              && d.textContent.includes('自定义')
                              && d.getBoundingClientRect().height > 60);
                const m = menus[menus.length - 1];
                if (!m) return null;
                return {
                    bg: getComputedStyle(m).backgroundColor,
                    radius: getComputedStyle(m).borderRadius,
                    items: [...m.querySelectorAll('button')].map(b => b.textContent.trim()),
                };
            }"""
        )
        if not menu:
            failures.append("截取帧 menu did not open")
        else:
            if menu["items"] != ["首帧", "尾帧", "自定义"]:
                failures.append(f"menu items: {menu['items']}")
            if menu["bg"] != "rgb(38, 38, 38)" or menu["radius"] != "12px":
                failures.append(f"menu chrome: {menu['bg']} / {menu['radius']}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch2-capture-frame-menu-1680.png")
        )

        # click elsewhere (toggle) then Escape + pane click to deselect
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        page.mouse.click(300, 700)
        page.wait_for_timeout(500)
        deselected = toolbar_state()
        if deselected["visible"]:
            failures.append("toolbar still visible after deselect")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 2 toolbar contract")
    print(f"screenshots: {REFERENCE_DIR / 'jimeng-clone-batch2-selected-toolbar-1680.png'}")


if __name__ == "__main__":
    main()
