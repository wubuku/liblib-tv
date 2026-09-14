"""Jimeng clone batch 82 verifier — offline-edit conflict dialog.

Contract (SOURCE_FACT batch 82, 81-after-reload-state.png):
- setOfflineDialog(true) opens a centered modal rgb(25,25,25) w~545:
  title 发现离线编辑, body 你在离线状态下对当前画布做了修改…,
  buttons 丢弃修改 (dark) / 保留并同步 (white);
- backdrop black/55; Escape closes;
- both buttons close with a mock toast.
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

        page.evaluate(
            "() => window.__jimengStore.getState().setOfflineDialog(true)"
        )
        page.wait_for_timeout(600)
        dlg = page.evaluate(
            """() => {
                const el = document.querySelector('[data-testid="jimeng-offline-dialog"]');
                if (!el) return null;
                const r = el.getBoundingClientRect();
                const cs = getComputedStyle(el);
                return {w: Math.round(r.width),
                        bg: cs.backgroundColor, radius: cs.borderRadius,
                        title: (el.querySelector('h3') || {}).textContent || '',
                        body: (el.querySelector('p') || {}).textContent || '',
                        keep: !!el.querySelector('[data-testid="offline-keep"]'),
                        discard: !!el.querySelector('[data-testid="offline-discard"]')};
            }"""
        )
        if not dlg:
            failures.append("offline dialog not opened")
        else:
            if abs(dlg["w"] - 545) > 8:
                failures.append(f"dialog width: {dlg['w']} want ~545")
            if dlg["bg"] != "rgb(25, 25, 25)":
                failures.append(f"dialog bg: {dlg['bg']}")
            if "发现离线编辑" not in dlg["title"]:
                failures.append(f"title: {dlg['title']!r}")
            if "尚未同步到服务器" not in dlg["body"]:
                failures.append(f"body: {dlg['body']!r}")
            if not (dlg["keep"] and dlg["discard"]):
                failures.append(f"buttons missing: {dlg}")
            page.screenshot(
                path=str(REFERENCE_DIR / "jimeng-clone-batch82-offline-dialog.png")
            )

        # Escape closes
        page.keyboard.press("Escape")
        page.wait_for_timeout(600)
        if page.locator('[data-testid="jimeng-offline-dialog"]').count():
            failures.append("Escape did not close offline dialog")

        # 保留并同步 → toast + close
        page.evaluate(
            "() => window.__jimengStore.getState().setOfflineDialog(true)"
        )
        page.wait_for_timeout(400)
        page.locator('[data-testid="offline-keep"]').click()
        page.wait_for_timeout(500)
        if page.locator('[data-testid="jimeng-offline-dialog"]').count():
            failures.append("保留并同步 did not close dialog")
        if "离线修改已同步" not in page.evaluate("() => document.body.innerText"):
            failures.append("保留并同步 toast missing")

        # 丢弃修改 → toast + close
        page.evaluate(
            "() => window.__jimengStore.getState().setOfflineDialog(true)"
        )
        page.wait_for_timeout(400)
        page.locator('[data-testid="offline-discard"]').click()
        page.wait_for_timeout(500)
        if page.locator('[data-testid="jimeng-offline-dialog"]').count():
            failures.append("丢弃修改 did not close dialog")
        if "已丢弃离线修改" not in page.evaluate("() => document.body.innerText"):
            failures.append("丢弃修改 toast missing")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 82 offline-edit dialog contract")


if __name__ == "__main__":
    main()
