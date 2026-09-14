"""Jimeng clone batch 66 verifier — save-state gated download.

Contract (SOURCE_FACT batch 66, pixel/census evidence):
- canvas content mutation → top bar 保存中…, download buttons disabled
  (title 导出前请保存画布) in single toolbar / multi toolbar / context menu;
- after mock autosave (~1.2s) → top bar 已保存, downloads enabled;
- clicking an enabled 下载 fires the mock toast.
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

        def topbar_status():
            return page.evaluate(
                """() => document.body.innerText.includes('保存中')
                    ? 'saving' : (document.body.innerText.includes('已保存') ? 'saved' : 'none')"""
            )

        def center(node_id):
            return page.evaluate(
                """(id) => { const n = document.querySelector(`[data-id="${id}"]`);
                    const r = n.getBoundingClientRect();
                    return {x: r.x + 60, y: r.y + 20}; }""",
                node_id,
            )

        def nudge_node(node_id):
            """30px 往返拖拽 → position change → canvas dirty (净位移 0)。"""
            c = center(node_id)
            page.mouse.move(c["x"] + 150, c["y"] + 150)
            page.mouse.down()
            page.mouse.move(c["x"] + 180, c["y"] + 150, steps=5)
            page.mouse.up()
            page.wait_for_timeout(100)
            c = center(node_id)
            page.mouse.move(c["x"] + 180, c["y"] + 150)
            page.mouse.down()
            page.mouse.move(c["x"] + 150, c["y"] + 150, steps=5)
            page.mouse.up()
            page.wait_for_timeout(200)

        # ---- baseline: saved, single toolbar download enabled ----
        c1 = center("video-local-1")
        page.mouse.click(c1["x"], c1["y"])
        page.wait_for_timeout(2500)  # let any initial dirtiness settle
        if topbar_status() != "saved":
            failures.append(f"baseline topbar: {topbar_status()}")
        dl_state = page.evaluate(
            """() => {
                const btn = [...document.querySelectorAll('button')]
                    .find(b => b.getAttribute('aria-label') === '下载');
                if (!btn) return null;
                return {disabled: btn.disabled, title: btn.title || null};
            }"""
        )
        if not dl_state:
            failures.append("single toolbar download not found")
        elif dl_state["disabled"]:
            failures.append(f"baseline download disabled: {dl_state}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch66-saved-state.png")
        )

        # ---- dirty: drag → 保存中… + gated download ----
        nudge_node("video-local-1")
        if topbar_status() != "saving":
            failures.append(f"after drag topbar: {topbar_status()} want saving")
        dl_state = page.evaluate(
            """() => {
                const btn = [...document.querySelectorAll('button')]
                    .find(b => b.getAttribute('aria-label') === '下载');
                return btn ? {disabled: btn.disabled, title: btn.title || null} : null;
            }"""
        )
        if not dl_state or not dl_state["disabled"] \
                or dl_state["title"] != "导出前请保存画布":
            failures.append(f"dirty download state: {dl_state}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch66-saving-state.png")
        )

        # ---- autosave restores ----
        page.wait_for_timeout(2600)
        if topbar_status() != "saved":
            failures.append(f"post-autosave topbar: {topbar_status()}")
        dl_state = page.evaluate(
            """() => {
                const btn = [...document.querySelectorAll('button')]
                    .find(b => b.getAttribute('aria-label') === '下载');
                return btn ? {disabled: btn.disabled, title: btn.title || null} : null;
            }"""
        )
        if not dl_state or dl_state["disabled"]:
            failures.append(f"post-autosave download: {dl_state}")

        # ---- context menu gating ----
        nudge_node("video-local-1")  # dirty again
        c1 = center("video-local-1")
        page.mouse.click(c1["x"] + 140, c1["y"] + 130, button="right")
        page.wait_for_timeout(600)
        menu_dl = page.evaluate(
            """() => [...document.querySelectorAll('button[role="menuitem"]')]
                .find(b => b.textContent.trim().startsWith('下载'))
                ? {disabled: [...document.querySelectorAll('button[role="menuitem"]')]
                    .find(b => b.textContent.trim().startsWith('下载')).disabled,
                   title: [...document.querySelectorAll('button[role="menuitem"]')]
                    .find(b => b.textContent.trim().startsWith('下载')).title || null}
                : null"""
        )
        if not menu_dl or not menu_dl["disabled"]:
            failures.append(f"context menu download while saving: {menu_dl}")
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
        page.wait_for_timeout(2600)  # autosave
        page.mouse.click(c1["x"] + 140, c1["y"] + 130, button="right")
        page.wait_for_timeout(600)
        menu_dl = page.evaluate(
            """() => {
                const b = [...document.querySelectorAll('button[role="menuitem"]')]
                    .find(x => x.textContent.trim().startsWith('下载'));
                return b ? {disabled: b.disabled, title: b.title || null} : null;
            }"""
        )
        if not menu_dl or menu_dl["disabled"]:
            failures.append(f"context menu download after save: {menu_dl}")
        else:
            page.evaluate(
                """() => [...document.querySelectorAll('button[role="menuitem"]')]
                    .find(b => b.textContent.trim().startsWith('下载'))?.click()"""
            )
            page.wait_for_timeout(400)
            toast = page.evaluate(
                "() => document.body.innerText.includes('视频下载已开始')"
            )
            if not toast:
                failures.append("enabled 下载 click did not fire mock toast")

        # ---- multi toolbar gating ----
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
        # dirty via nudge, then assert multi download gated
        nudge_node("video-local-1")
        page.wait_for_timeout(300)
        m_dl = page.evaluate(
            """() => {
                const btn = document.querySelector('[data-testid="multi-download"]');
                return btn ? {disabled: btn.disabled, title: btn.title || null} : null;
            }"""
        )
        if not m_dl or not m_dl["disabled"]:
            failures.append(f"multi download while saving: {m_dl}")
        page.wait_for_timeout(2600)
        m_dl = page.evaluate(
            """() => {
                const btn = document.querySelector('[data-testid="multi-download"]');
                return btn ? {disabled: btn.disabled, title: btn.title || null} : null;
            }"""
        )
        if not m_dl or m_dl["disabled"]:
            failures.append(f"multi download after save: {m_dl}")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 66 save-state gated download contract")


if __name__ == "__main__":
    main()
