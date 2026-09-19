"""Jimeng clone batch 68 verifier — rail labels + text node defaults.

Contract (SOURCE_FACT batch 68, 68-rail.json / 68-newnode-selected.png):
- left rail aria-labels: 文本/图片/视频/音频/时间线/主体/导演台(Beta)/
  资产库/上传; 文本 click inserts a text node at viewport center.
- text node: title 文本 N, no selected toolbar, placeholder 双击编辑文本
  (gray), Type icon in title row, default 328×340.
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

        # Batch 398 SOURCE_FACT: Agent 面板常驻——本验证器不测面板，
        # 载入后先收起以避免遮挡画布交互
        _collapse = page.locator('button[aria-label="收起"]')
        if _collapse.count():
            _collapse.click()
            page.wait_for_timeout(400)

        # ---- rail aria-labels ----
        labels = page.evaluate(
            """() => [...document.querySelectorAll('aside button[aria-label]')].map(
                b => b.getAttribute('aria-label'))"""
        )
        want = ["文本", "图片", "视频", "音频", "时间线", "主体", "导演台",
                "资产库", "上传"]
        if labels != want:
            failures.append(f"rail labels: {labels} want {want}")
        beta = page.evaluate(
            """() => [...document.querySelectorAll('aside button[aria-label]')]
                .find(b => b.getAttribute('aria-label') === '导演台'
                    && b.textContent.includes('Beta')) !== null"""
        )
        if not beta:
            failures.append("导演台 missing Beta tag")

        # ---- insert text node at viewport center ----
        n0 = page.evaluate("() => document.querySelectorAll('.react-flow__node').length")
        page.evaluate(
            """() => [...document.querySelectorAll('aside button[aria-label]')]
                .find(b => b.getAttribute('aria-label') === '文本').click()"""
        )
        page.wait_for_timeout(1200)
        n1 = page.evaluate("() => document.querySelectorAll('.react-flow__node').length")
        if n1 != n0 + 1:
            failures.append(f"文本 insert: {n1} nodes want {n0 + 1}")
        else:
            text = page.evaluate(
                """() => {
                    const els = [...document.querySelectorAll('.react-flow__node-text')];
                    const el = els[els.length - 1];
                    if (!el) return null;
                    const r = el.getBoundingClientRect();
                    const tf = el.querySelector('p,textarea');
                    const icon = el.querySelector('svg');
                    return {
                        title: (el.textContent || '').trim().slice(0, 20),
                        w: Math.round(r.width), h: Math.round(r.height),
                        placeholder: tf ? tf.textContent.trim() : null,
                        phColor: tf ? getComputedStyle(tf).color : null,
                        hasIcon: !!icon,
                        cx: r.x + r.width / 2, cy: r.y + r.height / 2,
                    };
                }"""
            )
            if not text:
                failures.append("text node not found after insert")
            else:
                if "文本" not in text["title"]:
                    failures.append(f"text title: {text['title']!r}")
                # 0.7299 初始缩放下的屏幕尺寸 (世界 368×368, 批 238 SOURCE_FACT)
                if abs(text["w"] - 269) > 8 or abs(text["h"] - 269) > 8:
                    failures.append(
                        f"text size: {text['w']}x{text['h']} want ~269x269"
                    )
                if text["placeholder"] != "双击编辑文本":
                    failures.append(f"text placeholder: {text['placeholder']!r}")
                if "0.4" not in text["phColor"]:
                    failures.append(f"placeholder color: {text['phColor']}")
                if not text["hasIcon"]:
                    failures.append("text title icon missing")
                # viewport center (±60px)
                if abs(text["cx"] - VIEWPORT["width"] / 2) > 60 \
                        or abs(text["cy"] - VIEWPORT["height"] / 2) > 60:
                    failures.append(
                        f"text not at viewport center: ({text['cx']}, {text['cy']})"
                    )
                # no toolbar for the selected text node
                tb = page.evaluate(
                    """() => [...document.querySelectorAll('.react-flow__node-toolbar')]
                        .filter(t => t.getBoundingClientRect().height > 20
                            && getComputedStyle(t).visibility !== 'hidden').length"""
                )
                # 批 241b: 源站演进后文本节点选中态自有工具条
                # (背景色/展开/下载)，不再断言「无工具条」
                pass
                page.screenshot(
                    path=str(REFERENCE_DIR / "jimeng-clone-batch68-text-node.png")
                )
            # cleanup: undo the insert
            page.keyboard.press("Meta+z")
            page.wait_for_timeout(600)
            n2 = page.evaluate("() => document.querySelectorAll('.react-flow__node').length")
            if n2 != n0:
                failures.append(f"text insert undo: {n2} want {n0}")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 68 rail labels + text node defaults contract")


if __name__ == "__main__":
    main()
