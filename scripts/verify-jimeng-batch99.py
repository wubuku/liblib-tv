"""Jimeng clone batch 99 verifier — custom frame picker geometry (Batch 202).

Contract (SOURCE_FACT, 202-custom-picker.json):
- 截取帧 → 自定义 opens the frame picker panel node-wide (564 @ node 569);
- filmstrip 54px tall; bottom row h-9: ▶ 00:00/00:06 ｜ 截取帧 ｜
  「请至少截取 1 帧」hint (12px) + 确认;
- 确认 disabled until a frame is captured: bg white/16 + text white/20, r8;
- clicking the strip moves the playhead; 截取帧 enables 确认 and clears
  the hint; 确认 closes the picker and writes the frame time.
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

        # select video-local-1 (off-center: play button swallows center clicks)
        center = page.evaluate(
            """() => {
                const el = document.querySelector('[data-id="video-local-1"]');
                const r = el.getBoundingClientRect();
                return {x: r.x + r.width / 2 - 120, y: r.y + 40, w: r.width};
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

                picker = page.evaluate(
                    """() => {
                        const bar = [...document.querySelectorAll('.react-flow__node-toolbar')]
                            .find(t => (t.textContent || '').includes('确认'));
                        if (!bar) return null;
                        const panel = bar.firstElementChild;
                        const pr = (panel || bar).getBoundingClientRect();
                        const strip = bar.querySelector('.relative');
                        const hint = document.querySelector('[data-testid="frame-hint"]');
                        const confirm = [...bar.querySelectorAll('button')]
                            .find(b => b.textContent.trim() === '确认');
                        const cs = confirm ? getComputedStyle(confirm) : null;
                        return {
                            panelW: Math.round(pr.width),
                            stripH: strip ? Math.round(strip.getBoundingClientRect().height) : null,
                            hintText: hint ? hint.textContent.trim() : null,
                            confirmDisabled: confirm ? confirm.disabled : null,
                            confirmBg: cs ? cs.backgroundColor : null,
                            confirmColor: cs ? cs.color : null,
                        };
                    }"""
                )
                if not picker:
                    failures.append("frame picker did not open")
                else:
                    # NodeToolbar portal renders unscaled: CSS contract is
                    # panel width == node data width (569), source 564@569
                    if abs(picker["panelW"] - 569) > 4:
                        failures.append(f"panel width {picker['panelW']} != 569")
                    if picker["stripH"] is None or abs(picker["stripH"] - 56) > 4:
                        failures.append(f"filmstrip height {picker['stripH']} != 54-56")
                    if picker["hintText"] != "请至少截取 1 帧":
                        failures.append(f"hint wrong: {picker['hintText']!r}")
                    if picker["confirmDisabled"] is not True:
                        failures.append("确认 should start disabled in custom mode")
                    # Tailwind 4 may emit oklab() — compare alpha channel only
                    def alpha_of(color: str) -> str:
                        if color.startswith("oklab"):
                            return color.rsplit("/", 1)[-1].strip(" )")
                        if color.startswith("rgba"):
                            return color.rsplit(",", 1)[-1].strip(" )")
                        return color
                    if alpha_of(picker["confirmBg"] or "") != "0.16":
                        failures.append(f"disabled bg {picker['confirmBg']} != white/16")
                    if alpha_of(picker["confirmColor"] or "") != "0.2":
                        failures.append(f"disabled text {picker['confirmColor']} != white/20")

                    page.screenshot(
                        path=str(REFERENCE_DIR / "jimeng-clone-batch99-picker.png")
                    )

                    # strip click moves the playhead; 截取帧 captures → hint
                    # clears and 确认 enables (batch 34 contract)
                    strip_box = page.evaluate(
                        """() => {
                            const bar = [...document.querySelectorAll('.react-flow__node-toolbar')]
                                .find(t => (t.textContent || '').includes('确认'));
                            const strip = bar.querySelector('.relative');
                            const r = strip.getBoundingClientRect();
                            return {x: r.x + r.width * 0.5, y: r.y + r.height / 2};
                        }"""
                    )
                    page.mouse.click(strip_box["x"], strip_box["y"])
                    page.wait_for_timeout(300)
                    moved = page.evaluate(
                        """() => {
                            const bar = [...document.querySelectorAll('.react-flow__node-toolbar')]
                                .find(t => (t.textContent || '').includes('确认'));
                            const el = bar.querySelector('[data-testid="frame-readout"]');
                            return el ? el.textContent.trim() : null;
                        }"""
                    )
                    if not moved or moved.startswith("00:00 /"):
                        failures.append(f"strip click did not move playhead: {moved!r}")

                    cap_btn = page.evaluate(
                        """() => {
                            const bar = [...document.querySelectorAll('.react-flow__node-toolbar')]
                                .find(t => (t.textContent || '').includes('确认'));
                            const confirm = [...bar.querySelectorAll('button')]
                                .find(b => b.textContent.trim() === '截取帧');
                            if (!confirm) return null;
                            const r = confirm.getBoundingClientRect();
                            return {x: r.x + r.width / 2, y: r.y + r.height / 2};
                        }"""
                    )
                    if not cap_btn:
                        failures.append("截取帧 picker button missing")
                    else:
                        page.mouse.click(cap_btn["x"], cap_btn["y"])
                        page.wait_for_timeout(400)
                    after = page.evaluate(
                        """() => {
                            const hint = document.querySelector('[data-testid="frame-hint"]');
                            const bar = [...document.querySelectorAll('.react-flow__node-toolbar')]
                                .find(t => (t.textContent || '').includes('确认'));
                            const confirm = bar && [...bar.querySelectorAll('button')]
                                .find(b => b.textContent.trim() === '确认');
                            return {hintGone: !hint,
                                    enabled: confirm ? !confirm.disabled : null};
                        }"""
                    )
                    if not after["hintGone"]:
                        failures.append("hint still visible after capture")
                    if after["enabled"] is not True:
                        failures.append("确认 not enabled after capture")

                    # confirm closes the picker
                    cb = page.evaluate(
                        """() => {
                            const bar = [...document.querySelectorAll('.react-flow__node-toolbar')]
                                .find(t => (t.textContent || '').includes('确认'));
                            const confirm = [...bar.querySelectorAll('button')]
                                .find(b => b.textContent.trim() === '确认');
                            const r = confirm.getBoundingClientRect();
                            return {x: r.x + r.width / 2, y: r.y + r.height / 2};
                        }"""
                    )
                    page.mouse.click(cb["x"], cb["y"])
                    page.wait_for_timeout(500)
                    gone = page.evaluate(
                        """() => ![...document.querySelectorAll('.react-flow__node-toolbar')]
                            .some(t => (t.textContent || '').includes('确认'))"""
                    )
                    if not gone:
                        failures.append("picker did not close after 确认")

        ctx.close()

    if failures:
        print("FAIL batch 99:")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print("PASS batch 99: custom frame picker geometry + capture gate")


if __name__ == "__main__":
    main()
