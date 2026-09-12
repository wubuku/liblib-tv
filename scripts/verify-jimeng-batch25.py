"""Jimeng clone batch 25 verifier — pane context menu (source-extracted).

SOURCE_FACT (batch 25): right-click on empty canvas opens the pane menu:
新建节点 > (submenu 文本/图片/视频/音频), 粘贴 ⌘V (disabled without
clipboard), 重做 ⌘⇧Z (disabled at tip), 撤销 ⌘Z.
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")

CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}


def node_count(page) -> int:
    return page.evaluate(
        "() => document.querySelectorAll('.react-flow__node').length"
    )


def main() -> None:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []

    with sync_playwright() as p:
        ctx = p.chromium.launch(headless=True)
        page = ctx.new_page()
        page.set_viewport_size(VIEWPORT)  # type: ignore[arg-type]
        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        before = node_count(page)

        # pane right-click
        page.mouse.click(400, 700, button="right")
        page.wait_for_timeout(700)
        menu = page.evaluate(
            """() => {
                const m = [...document.querySelectorAll('[role="menu"]')]
                    .find(m => m.textContent.includes('新建节点'));
                if (!m) return null;
                return {
                    items: [...m.querySelectorAll(':scope > button, :scope > div > button')]
                        .map(b => ({
                            label: b.textContent.trim().split(/\\s+/)[0],
                            disabled: b.disabled,
                        })),
                };
            }"""
        )
        if not menu:
            failures.append("pane menu did not open")
        else:
            labels = [i["label"] for i in menu["items"]]
            want = ["新建节点", "粘贴", "重做", "撤销"]
            if len(labels) != len(want) or not all(
                l.startswith(w) for l, w in zip(labels, want)
            ):
                failures.append(f"pane menu items: {labels}")
            redo = next(
                (i for i in menu["items"] if i["label"].startswith("重做")), None
            )
            if not redo or not redo["disabled"]:
                failures.append("重做 should be disabled at history tip")

        # hover 新建节点 → submenu
        page.locator('[role="menuitem"]', has_text="新建节点").hover()
        page.wait_for_timeout(500)
        sub = page.evaluate(
            """() => {
                const subs = [...document.querySelectorAll('[role="menu"]')]
                    .filter(m => m.textContent.includes('文本')
                              && m.textContent.includes('音频')
                              && !m.textContent.includes('粘贴'));
                return subs.length > 0
                    ? [...subs[subs.length-1].querySelectorAll('[role="menuitem"]')]
                        .map(b => b.textContent.trim())
                    : null;
            }"""
        )
        if sub != ["文本", "图片", "视频", "音频"]:
            failures.append(f"insert submenu: {sub}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch25-pane-menu-1680.png")
        )

        # click 视频 in submenu → node created at the right-click position
        page.locator('[role="menuitem"]', has_text="视频").last.click()
        page.wait_for_timeout(800)
        after = node_count(page)
        if after != before + 1:
            failures.append(f"nodes after pane insert: {after} (want {before + 1})")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 25 pane menu contract")


if __name__ == "__main__":
    main()
