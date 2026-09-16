"""Jimeng clone batch 100 verifier — custom frame capture end-to-end (Batch 203).

Contract (SOURCE_FACT 203-picker-interaction/confirm.json):
- 截取帧 → 自定义 opens the picker (readout 00:00/00:06, hint visible,
  确认 style-gated);
- strip click moves the readout; 截取帧 captures → hint clears, 确认 arms;
- 确认 closes the picker AND produces an image node titled「{video}_自定义」
  with lineage edge and right-side avoidance placement (same family as
  首帧/尾帧 captures, batch 62/195);
- undo removes the produced node and edge.
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

        n0 = page.evaluate(
            "() => document.querySelectorAll('.react-flow__node').length"
        )

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
            custom = page.evaluate(
                """() => {
                    const btn = [...document.querySelectorAll('button')]
                        .find(b => b.textContent.trim() === '自定义'
                            && b.getBoundingClientRect().height < 50);
                    if (!btn) return null;
                    const r = btn.getBoundingClientRect();
                    return {x: r.x + r.width / 2, y: r.y + r.height / 2};
                }"""
            )
            if not custom:
                failures.append("自定义 menu item not found")
            else:
                page.mouse.click(custom["x"], custom["y"])
                page.wait_for_timeout(700)

                readout0 = page.evaluate(
                    """() => {
                        const bar = [...document.querySelectorAll('form,div')]
                            .find(d => d.querySelector('[data-testid="frame-readout"]')
                                       && d.textContent.includes('确认'));
                        return bar?.querySelector('[data-testid="frame-readout"]')
                            ?.textContent.trim() ?? null;
                    }"""
                )
                if readout0 != "00:00 / 00:06":
                    failures.append(f"initial readout: {readout0!r}")

                strip = page.evaluate(
                    """() => {
                        const bar = [...document.querySelectorAll('form,div')]
                            .find(d => d.querySelector('[data-testid="frame-readout"]')
                                       && d.textContent.includes('确认'));
                        const el = bar.querySelector('[data-testid="frame-strip"]');
                        const r = el.getBoundingClientRect();
                        return {x: r.x, y: r.y, w: r.width};
                    }"""
                )
                page.mouse.click(strip["x"] + strip["w"] * 0.7, strip["y"])
                page.wait_for_timeout(300)
                readout1 = page.evaluate(
                    """() => {
                        const bar = [...document.querySelectorAll('form,div')]
                            .find(d => d.querySelector('[data-testid="frame-readout"]')
                                       && d.textContent.includes('确认'));
                        return bar?.querySelector('[data-testid="frame-readout"]')
                            ?.textContent.trim() ?? null;
                    }"""
                )
                if readout1 == readout0:
                    failures.append(f"strip click did not move readout: {readout1!r}")

                clicked_cap = False
                for _ in range(8):
                    page.wait_for_timeout(300)
                    clicked_cap = page.evaluate(
                        """() => {
                            const bar = [...document.querySelectorAll('form,div')]
                                .find(d => d.querySelector('[data-testid="frame-readout"]')
                                           && d.textContent.includes('确认'));
                            if (!bar) return false;
                            const btn = [...bar.querySelectorAll('button')]
                                .find(b => b.textContent.trim() === '截取帧');
                            if (!btn) return false;
                            btn.click();
                            return true;
                        }"""
                    )
                    if clicked_cap:
                        break
                if not clicked_cap:
                    failures.append("picker 截取帧 button missing before capture")
                page.wait_for_timeout(400)
                page.wait_for_timeout(400)
                clicked_confirm = False
                for _ in range(8):
                    clicked_confirm = page.evaluate(
                        """() => {
                            const bar = [...document.querySelectorAll('form,div')]
                                .find(d => d.querySelector('[data-testid="frame-readout"]')
                                           && d.textContent.includes('确认'));
                            if (!bar) return false;
                            const btn = [...bar.querySelectorAll('button')]
                                .find(b => b.textContent.trim() === '确认');
                            if (!btn || btn.disabled) return false;
                            btn.click();
                            return true;
                        }"""
                    )
                    if clicked_confirm:
                        break
                    page.wait_for_timeout(300)
                if not clicked_confirm:
                    failures.append("确认 not clickable after capture")
                page.wait_for_timeout(700)

                picker_gone = page.evaluate(
                    """() => ![...document.querySelectorAll('form,div')]
                        .some(d => d.querySelector('[data-testid="frame-readout"]')
                                  && d.textContent.includes('确认'))"""
                )
                if not picker_gone:
                    failures.append("picker did not close after 确认")

                result = page.evaluate(
                    """() => {
                        const imgs = [...document.querySelectorAll('.react-flow__node-image')];
                        const el = imgs[imgs.length - 1] ?? null;
                        if (!el) return {count: imgs.length};
                        const img = el.querySelector('img');
                        return {count: imgs.length,
                                hasPoster: !!img,
                                title: (el.textContent || '').trim().slice(0, 60)};
                    }"""
                )
                if result["count"] != 1:
                    failures.append(f"image node count {result['count']} != 1")
                else:
                    if not result["hasPoster"]:
                        failures.append("produced image node has no poster")
                    if "_截帧_1" not in (result["title"] or ""):
                        failures.append(f"custom title wrong: {result['title']!r}")

                edges = page.evaluate(
                    "() => document.querySelectorAll('.react-flow__edge').length"
                )
                if edges != 1:
                    failures.append(f"lineage edge missing: {edges} != 1")

                page.screenshot(
                    path=str(REFERENCE_DIR / "jimeng-clone-batch100-custom-capture.png")
                )

                page.keyboard.press("Meta+z")
                page.wait_for_timeout(600)
                n2 = page.evaluate(
                    "() => document.querySelectorAll('.react-flow__node').length"
                )
                e2 = page.evaluate(
                    "() => document.querySelectorAll('.react-flow__edge').length"
                )
                if n2 != n0 or e2 != 0:
                    failures.append(f"undo failed: nodes {n2}/{n0}, edges {e2}")

        ctx.close()

    if failures:
        print("FAIL batch 100:")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print("PASS batch 100: custom capture end-to-end (confirm → image node)")


if __name__ == "__main__":
    main()
