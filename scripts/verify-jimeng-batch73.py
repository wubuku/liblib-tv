"""Jimeng clone batch 73 verifier — rail hover flyout + local upload flow.

Contract (SOURCE_FACT batch 73, 73-upload-panel.png):
- hovering the rail shows label flyouts right of the icons (文本…上传);
- 上传 opens a multi file chooser; chosen files become local-upload video
  nodes at viewport center with the file name as title (sb_... filename
  pattern of the existing source node) and media controls.
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

        # ---- hover rail → flyout labels visible ----
        page.hover('aside button[aria-label="文本"]')
        page.wait_for_timeout(400)
        labels = page.evaluate(
            """() => [...document.querySelectorAll('[data-rail-label]')]
                .map(s => ({label: s.getAttribute('data-rail-label'),
                            opacity: getComputedStyle(s).opacity}))"""
        )
        want = ["文本", "图片", "视频", "音频", "时间线", "主体", "导演台",
                "资产库", "上传"]
        got = [l["label"] for l in labels]
        if got != want:
            failures.append(f"flyout labels: {got} want {want}")
        hidden = [l for l in labels if l["opacity"] != "1"]
        if hidden:
            failures.append(f"flyout labels not visible on hover: {hidden}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch73-rail-flyout.png")
        )

        # ---- upload via file chooser ----
        n0 = page.evaluate("() => document.querySelectorAll('.react-flow__node').length")
        with page.expect_file_chooser() as fc_info:
            page.locator('aside button[aria-label="上传"]').click()
        fc = fc_info.value
        if not fc.is_multiple():
            failures.append("upload chooser should be multiple")
        upload = os.path.join(REFERENCE_DIR, "batch73-sample-upload.mp4")
        Path(upload).write_bytes(b"\x00" * 64)
        fc.set_files(upload)
        page.wait_for_timeout(900)
        n1 = page.evaluate("() => document.querySelectorAll('.react-flow__node').length")
        if n1 != n0 + 1:
            failures.append(f"upload node count: {n1} want {n0 + 1}")
        else:
            node = page.evaluate(
                """() => {
                    const els = [...document.querySelectorAll('.react-flow__node-video')];
                    const el = els[els.length - 1];
                    const title = (el.querySelector('.truncate') || el).textContent.trim();
                    const r = el.getBoundingClientRect();
                    const img = el.querySelector('img');
                    return {title, w: Math.round(r.width), h: Math.round(r.height),
                            hasPoster: !!img, cx: r.x + r.width/2, cy: r.y + r.height/2};
                }"""
            )
            if node["title"] != "batch73-sample-upload.mp4":
                # title should equal the file name (SOURCE_FACT sb_... pattern)
                failures.append(f"upload node title: {node['title']!r}")
            if not node["hasPoster"]:
                failures.append("upload node missing poster")
            # viewport center ±60
            if abs(node["cx"] - VIEWPORT["width"] / 2) > 60 \
                    or abs(node["cy"] - VIEWPORT["height"] / 2) > 60:
                failures.append(
                    f"upload node not centered: ({node['cx']}, {node['cy']})"
                )
            page.screenshot(
                path=str(REFERENCE_DIR / "jimeng-clone-batch73-upload-node.png")
            )
            # undo → back to baseline
            page.keyboard.press("Meta+z")
            page.wait_for_timeout(700)
            n2 = page.evaluate("() => document.querySelectorAll('.react-flow__node').length")
            if n2 != n0:
                failures.append(f"upload undo: {n2} want {n0}")
        os.remove(upload)

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 73 rail flyout + local upload contract")


if __name__ == "__main__":
    main()
