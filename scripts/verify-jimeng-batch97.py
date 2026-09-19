"""Jimeng clone batch 97 verifier — image node toolbar (Batch 195 replication).

Contract (SOURCE_FACT 195/208; tail buttons corrected by 208 screenshot):
- 截取帧 首帧 creates image node titled 「{video title}_首帧」 (underscore,
  aria 「图片 node: sb_..._」 form) with poster and lineage edge.
- Selecting the image node shows its own toolbar — same dark pill, node-wide —
  with EXACTLY: 智能改图(VIP✦) / 扩图 / 智能超清 / 抠图 / 多角度 / 工具∨
  ｜ divider ｜ 全屏预览 + 下载 tail icon buttons (208 screenshot — the
  195 "no tail buttons" conclusion missed text-less icon buttons);
  智能超清 carries NO vip diamond here (differs from video toolbar).
- 智能改图 has 2 svgs (icon + vip diamond), 工具 has 2 svgs (icon + chevron),
  plain items 1 svg.
- Undo removes the created node and edge.
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")

CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}

EXPECTED_ITEMS = ["智能改图", "扩图", "智能超清", "抠图", "多角度", "工具"]


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

        n0 = page.evaluate(
            "() => document.querySelectorAll('.react-flow__node').length"
        )

        # ---- select video-local-1, open 截取帧, click 首帧 ----
        # off-center click: the play button at node center swallows clicks (batch 38)
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
                if (!t) return null;
                const btn = [...t.querySelectorAll('button')]
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
                page.wait_for_timeout(700)

                n1 = page.evaluate(
                    "() => document.querySelectorAll('.react-flow__node').length"
                )
                if n1 != n0 + 1:
                    failures.append(f"首帧 did not add image node: {n1} vs {n0}")

                img = page.evaluate(
                    """() => {
                        const nodes = [...document.querySelectorAll('.react-flow__node-image')];
                        const el = nodes[nodes.length - 1];
                        if (!el) return null;
                        return {hasPoster: !!el.querySelector('img'),
                                title: (el.textContent || '').trim().slice(0, 80)};
                    }"""
                )
                if not img:
                    failures.append("image node missing after 首帧")
                else:
                    if not img["hasPoster"]:
                        failures.append("image node has no poster")
                    # Batch 195 SOURCE_FACT: underscore title 「…_首帧」
                    if "_首帧" not in img["title"]:
                        failures.append(
                            f"image title lacks underscore frame suffix: {img['title']!r}"
                        )

                edges = page.evaluate(
                    "() => document.querySelectorAll('.react-flow__edge').length"
                )
                if edges != 1:
                    failures.append(f"lineage edge missing: {edges} != 1")

        # ---- select the image node → its own toolbar ----
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
            failures.append("cannot locate image node for selection")
        else:
            page.mouse.click(img_sel["x"], img_sel["y"])
            page.wait_for_timeout(700)

            tb = page.evaluate(
                """() => {
                    const panels = [...document.querySelectorAll('.react-flow__node-toolbar')]
                        .map(t => ({t, r: t.getBoundingClientRect()}))
                        .filter(x => x.r.width > 50);
                    if (!panels.length) return null;
                    panels.sort((a, b) => b.r.width - a.r.width);
                    const t = panels[0].t;
                    const btns = [...t.querySelectorAll('button')].map(b => ({
                        label: b.textContent.trim(),
                        svgs: b.querySelectorAll('svg').length,
                    }));
                    return {btns,
                            hasDivider: !!t.querySelector('.jimeng-node-toolbar-divider'),
                            text: t.textContent};
                }"""
            )
            if not tb:
                failures.append("image node toolbar not visible after selection")
            else:
                labels = [b["label"] for b in tb["btns"] if b["label"]]
                if labels != EXPECTED_ITEMS:
                    failures.append(f"image toolbar items wrong: {labels}")
                if not tb["hasDivider"]:
                    failures.append("image toolbar must have the tail divider")
                tail = page.evaluate(
                    """() => {
                        const t = [...document.querySelectorAll('.react-flow__node-toolbar')]
                            .sort((a,b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
                        return {
                            fs: !!t.querySelector('button[aria-label="全屏预览"]'),
                            dl: !!t.querySelector('button[aria-label="下载"]'),
                        };
                    }"""
                )
                if not (tail["fs"] and tail["dl"]):
                    failures.append(
                        f"image toolbar tail buttons missing: {tail}"
                    )
                svg_by_label = {b["label"]: b["svgs"] for b in tb["btns"]}
                if svg_by_label.get("智能改图") != 2:
                    failures.append(
                        f"智能改图 svg count {svg_by_label.get('智能改图')} != 2 (icon+vip)"
                    )
                if svg_by_label.get("工具") != 2:
                    failures.append(
                        f"工具 svg count {svg_by_label.get('工具')} != 2 (icon+chevron)"
                    )
                if svg_by_label.get("扩图") != 1:
                    failures.append(
                        f"扩图 svg count {svg_by_label.get('扩图')} != 1"
                    )
                if svg_by_label.get("智能超清") != 1:
                    failures.append(
                        "智能超清 must carry NO vip diamond on image toolbar"
                    )

                page.screenshot(
                    path=str(REFERENCE_DIR / "jimeng-clone-batch97-image-toolbar.png")
                )

        # ---- undo removes node + edge ----
        page.keyboard.press("Meta+z")
        page.wait_for_timeout(600)
        n2 = page.evaluate(
            "() => document.querySelectorAll('.react-flow__node').length"
        )
        e2 = page.evaluate(
            "() => document.querySelectorAll('.react-flow__edge').length"
        )
        if n2 != n0 or e2 != 0:
            failures.append(f"undo failed: nodes {n2} vs {n0}, edges {e2}")

        ctx.close()

    if failures:
        print("FAIL batch 97:")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print("PASS batch 97: image node toolbar (6 items + divider/fullscreen/download tail)")


if __name__ == "__main__":
    main()
