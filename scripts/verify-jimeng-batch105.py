"""Jimeng clone batch 105 verifier — audio gen panel dual-mode rendering (Batch 301/302).

Contract (SOURCE_FACT 301-evolution-scan.json):
- 音频生成 mode: placeholder「请输入你想生成的说话内容」, form height 196,
  selectors = Seed TTS (two-line dropdown) + 音色 grid button;
- 创作类型 dropdown → 音乐生成: placeholder「请输入你想生成的音乐」,
  form height 144, selectors = SeedMusic 1.0 Preview + 120s;
- switching back reverts everything.
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

        page.locator('aside button[aria-label="音频"]').click()
        page.wait_for_timeout(900)

        def panel_state() -> dict | None:
            return page.evaluate(
                """() => {
                    const f = [...document.querySelectorAll('form')].find(f =>
                        f.querySelector('textarea[aria-label="音频生成提示词"]'));
                    if (!f) return null;
                    const r = f.getBoundingClientRect();
                    const ta = f.querySelector('textarea');
                    const overlay = f.querySelector('div.pointer-events-none');
                    return {
                        h: Math.round(r.height),
                        placeholder: overlay ? overlay.textContent.trim() : null,
                        hasSeedTts: !!f.querySelector('button[aria-label="选择模型: Seed TTS"]'),
                        hasSeedMusic: !!f.querySelector('button[aria-label="选择模型: SeedMusic 1.0 Preview"]'),
                        hasVoice: !!f.querySelector('button[aria-label^="音色: "]'),
                        has120s: !!f.querySelector('button[aria-label="选择时长: 120s"]'),
                    };
                }"""
            )

        st = panel_state()
        if not st:
            failures.append("audio gen panel missing")
        else:
            if st["placeholder"] != "请输入你想生成的说话内容":
                failures.append(f"audio-mode placeholder: {st['placeholder']!r}")
            if abs(st["h"] - 196) > 4:
                failures.append(f"audio-mode height {st['h']} != 196")
            if not st["hasSeedTts"] or not st["hasVoice"]:
                failures.append("audio-mode selectors missing (Seed TTS / 音色)")
            if st["hasSeedMusic"] or st["has120s"]:
                failures.append("music-only selectors visible in audio mode")

        # switch to 音乐生成
        page.locator('button[aria-label="创作类型: 音频生成"]').click()
        page.wait_for_timeout(300)
        page.locator('button[role="option"]', has_text="音乐生成").click()
        page.wait_for_timeout(500)

        st2 = panel_state()
        if not st2:
            failures.append("panel missing after switching to 音乐生成")
        else:
            if st2["placeholder"] != "请输入你想生成的音乐":
                failures.append(f"music-mode placeholder: {st2['placeholder']!r}")
            if abs(st2["h"] - 144) > 4:
                failures.append(f"music-mode height {st2['h']} != 144")
            if not st2["hasSeedMusic"] or not st2["has120s"]:
                failures.append("music-mode selectors missing (SeedMusic / 120s)")
            if st2["hasSeedTts"] or st2["hasVoice"]:
                failures.append("audio-mode selectors visible in music mode")

        # Batch 367: duration control is a continuous slider popover
        # (SOURCE_FACT 367e/367f: title 选择音乐生成时长, free 0-360s track,
        # 7 tick labels 0..360, numeric input; price stays 6.6 regardless)
        page.locator('button[aria-label="选择时长: 120s"]').click()
        page.wait_for_timeout(300)
        slider = page.evaluate(
            """() => {
                const pop = [...document.querySelectorAll('div[role="listbox"][aria-label="音乐时长"]')][0];
                if (!pop) return null;
                const th = pop.querySelector('[role="slider"]');
                const labels = [...pop.querySelectorAll('div.flex span')].filter(
                    s => s.parentElement.className.includes('justify-between'));
                const input = pop.querySelector('input');
                return {
                    title: (pop.querySelector('p') || {}).textContent || null,
                    valnow: th ? th.getAttribute('aria-valuenow') : null,
                    ticks: labels.map(s => s.textContent.trim()),
                    inputValue: input ? input.value : null,
                };
            }"""
        )
        if not slider:
            failures.append("duration slider popover missing")
        else:
            if slider["title"] != "选择音乐生成时长":
                failures.append(f"slider title: {slider['title']!r}")
            if slider["valnow"] != "120":
                failures.append(f"slider aria-valuenow: {slider['valnow']!r} != 120")
            if slider["ticks"] != ["0", "60", "120", "180", "240", "300", "360"]:
                failures.append(f"slider ticks: {slider['ticks']}")
            if slider["inputValue"] != "120":
                failures.append(f"slider input value: {slider['inputValue']!r}")

        # click mid-track -> free value ~180 (±40), trigger label follows, price fixed 6.6
        box = page.locator('div[role="listbox"][aria-label="音乐时长"] .relative.h-4').bounding_box()
        if box:
            page.mouse.click(box["x"] + box["width"] * 0.5, box["y"] + box["height"] / 2)
            page.wait_for_timeout(300)
            after = page.evaluate(
                """() => {
                    const th = document.querySelector('div[role="listbox"][aria-label="音乐时长"] [role="slider"]');
                    const trigger = document.querySelector('button[aria-label^="选择时长:"]');
                    const f = [...document.querySelectorAll('form')].find(f =>
                        f.querySelector('textarea[aria-label="音频生成提示词"]'));
                    const m = f ? (f.textContent || '').match(/Current price\\s*([\\d.]+)/) : null;
                    return {valnow: th ? th.getAttribute('aria-valuenow') : null,
                            trigger: trigger ? trigger.getAttribute('aria-label') : null,
                            price: m ? m[1] : null};
                }"""
            )
            v = int(after["valnow"])
            if abs(v - 180) > 40:
                failures.append(f"mid-track click valuenow {v} not ~180")
            if after["trigger"] != f"选择时长: {v}s":
                failures.append(f"trigger label not following: {after['trigger']!r}")
            if after["price"] != "6.6":
                failures.append(f"price changed with duration: {after['price']!r}")
        else:
            failures.append("slider track box not found")

        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch105-music-mode.png")
        )

        # switch back to 音频生成
        page.locator('button[aria-label="创作类型: 音乐生成"]').click()
        page.wait_for_timeout(300)
        page.locator('button[role="option"]', has_text="音频生成").click()
        page.wait_for_timeout(500)
        st3 = panel_state()
        if not st3 or st3["placeholder"] != "请输入你想生成的说话内容":
            failures.append(f"revert placeholder wrong: {st3 and st3['placeholder']!r}")

        ctx.close()

    if failures:
        print("FAIL batch 105:")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print("PASS batch 105: gen panel dual-mode rendering (placeholder/height/selectors)")


if __name__ == "__main__":
    main()
