#!/usr/bin/env python3
"""Verify Batch 601: 时间轴工具条左格逐项对齐（间隙 / 尺寸 / 圆角 / 配色 / 默认单位）。

Source facts (live CDP sampling of the source director desk at 1920x1150,
2026-10-01, /tmp/src593/probe47 + a 4x screenshot of the strip).

The left cell of the source's timeline strip holds exactly seven controls.
Measured x / width / gap-from-previous, all 24px tall at y=1027:

    播放      x=8   w=26  gap –    rounded-md(6)  transparent  text-white/80
    自动帧    x=34  w=24  gap 0    rounded-lg(8)  transparent  text-white/80
                                                   svg.h-3.5.w-3.5 (a stopwatch)
    循环播放  x=58  w=26  gap 0    rounded-md(6)  bg-white/10   text-neutral-50
    播放头位置 x=88  w=46  gap 4    radius 8px 0 0 8px  bg-white/10 12px #F7F7F7
    总时长    x=135 w=46  gap 1    radius 0            bg-white/10 12px #F7F7F7
    单位      x=182 w=33  gap 1    radius 0 8px 8px 0 bg-white/10 12px #F7F7F7
    新建轨道  x=230 w=82  gap 15   rounded-lg(8)  transparent  13px

So the gaps are NOT a uniform 4px: the first three sit flush, a 4px step
reaches the readout group, that group is joined at 1px, and 15px separates it
from 新建轨道. The clone ran a single `gap-1` on the header, which pushed every
control after 播放 progressively to the right (up to 14px off at 总时长).

The readout group's styling is `bg-white/10 px-0 text-[12px] text-[#F7F7F7]`
with `hover:bg-white/[0.16]` and `focus:bg-white/[0.18] focus:ring-1
focus:ring-[#5DDCFF]/70`; the clone used `bg-[#222] px-1 text-xs text-[#c8c8c8]`.

The unit default was wrong. The source opens in **ms**: unit button text `ms`,
aria 切换时间单位为 s, 播放头位置 `0`, 总时长 `10000` for its 10s project. The
clone defaulted to `s` — a choice batch 591 made with no source behind it, and
`总时长` read 8.00 where the source reads 10000. Batch 591's initial-state
assertions are migrated accordingly; the toggle, the join and the commit
semantics are untouched.

The 自动帧 button holds a 14px stopwatch icon, not a dot. The clone drew an
8px dot.

NOT verified (recorded, not fabricated):
- 自动帧's ON appearance. The source's toggle reads aria-pressed="false", so
  only the OFF state (transparent + text-white/80) was measured; the clone's
  ON tint is its own. Its `autoKeyframe` default also stays `true` — the
  source's value is the user's own project state, not a recoverable default,
  and batch 36 pins it.
- 循环播放's OFF appearance, for the same reason (the source has no
  aria-pressed on it and is currently in its lit state).
- 新建轨道's enabled condition. The source's button reads **disabled** while a
  *camera* (主机位) is selected, even though its own accessible name promises
  「选中角色、道具或分组」 and the source's onboarding bubble says
  「请选择一个角色或者摄像机后，可新建轨道」. Those contradict, so the clone's
  condition is left alone and the observation is filed instead of guessed at.

Contract asserted here:
1. the seven controls sit at the source's x positions, with the source's gaps;
2. their widths are 26/24/26/46/46/33/82;
3. the radii are 6/8/6/8-0-0/0/0-8-8/8 as measured;
4. the readout group is white/10 at 12px #F7F7F7, joined at 1px, and the
   新建轨道 button is 15px after it;
5. the toolbar opens in ms: unit text `ms`, aria 切换时间单位为 s, integer-ms
   readouts;
6. 自动帧 holds a 14px icon, not an 8px dot;
7. 新建轨道 shows the text 新建轨道 at 13px alongside its accessible name;
8. no diagnostics.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch601-2026-10-01"
    / "runtime-audit.json"
)

WHITE_10_ALPHA = 0.1
WHITE_80_ALPHA = 0.8
TEXT_F7F7F7 = "rgb(247, 247, 247)"

SOURCE_LAYOUT = [
    # (selector, x, width, gap-from-previous, left radius px, right radius px)
    ("[data-director-playback]", 8, 26, None, 6, 6),
    ("[data-director-auto-keyframe]", 34, 24, 0, 8, 8),
    ("[data-director-loop]", 58, 26, 0, 6, 6),
    ("[data-director-time-field='time']", 88, 46, 4, 8, 0),
    ("[data-director-time-field='duration']", 135, 46, 1, 0, 0),
    ("[data-director-time-unit]", 182, 33, 1, 0, 8),
    ("[data-director-add-track]", 230, 82, 15, 8, 8),
]


def alpha_of(color: str) -> float:
    """Last component of rgb()/rgba(), or the `/ a` tail of oklab()."""
    if "/" in color and "rgba" not in color and "rgb(" not in color:
        return float(color.rsplit("/", 1)[1].strip().rstrip(")"))
    inner = color[color.index("(") + 1 : color.rindex(")")]
    parts = [p.strip() for p in inner.split(",")]
    return float(parts[3]) if len(parts) == 4 else 1.0


def attach_errors(page: Page) -> list[str]:
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(f"console:{message.type}:{message.text}")
        if message.type == "error"
        and "TransformControls" not in message.text
        else None,
    )
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    return errors


READ = """(sels) => {
  const bar = document.querySelector('[data-director-timeline-controls]');
  const all = [...bar.querySelectorAll('button, input')];
  const out = sels.map((sel) => {
    const el = document.querySelector(sel);
    if (!el) return {sel, missing: true};
    const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    // document order, not sibling order: the readout group is a wrapper, so the
    // gap that matters is against the last control *before* it
    const idx = all.indexOf(el);
    const prev = idx > 0 ? all[idx - 1] : null;
    const pr = prev ? prev.getBoundingClientRect() : null;
    const svg = el.querySelector('svg');
    const svgBox = svg ? svg.getBoundingClientRect() : null;
    return {sel, x: Math.round(r.x), w: Math.round(r.width), h: Math.round(r.height),
      gap: pr ? Math.round(r.x - (pr.x + pr.width)) : null,
      radiusLeft: cs.borderTopLeftRadius, radiusRight: cs.borderTopRightRadius,
      background: cs.backgroundColor, color: cs.color, fontSize: cs.fontSize,
      text: (el.textContent || '').trim(), value: 'value' in el ? el.value : null,
      aria: el.getAttribute('aria-label'), disabled: el.disabled === true,
      svgBox: svgBox ? [Math.round(svgBox.width), Math.round(svgBox.height)] : null};
  });
  return out;
}"""


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1920x1150", "checks": []}

    def check(name: str, ok: bool, detail: Any = None) -> None:
        result["checks"].append({"name": name, "ok": bool(ok), "detail": detail})

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 601" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(700)
    page.mouse.move(1500, 300)
    page.wait_for_timeout(250)
    sels = [row[0] for row in SOURCE_LAYOUT]
    items = page.evaluate(READ, sels)
    result["items"] = items

    # 1-3) x / gap / width / radius, position by position
    for index, (sel, x, width, gap, radius_l, radius_r) in enumerate(SOURCE_LAYOUT):
        item = items[index]
        label = sel.strip("[]'= ") or sel
        check(
            f"layout:{index + 1}-{label}:x-width-gap",
            item.get("x") == x
            and item.get("w") == width
            and item.get("h") == 24
            and item.get("gap") == gap,
            detail={k: item.get(k) for k in ("x", "w", "h", "gap")},
        )
        check(
            f"layout:{index + 1}-{label}:radius",
            item.get("radiusLeft") == f"{radius_l}px"
            and item.get("radiusRight") == f"{radius_r}px",
            detail=[item.get("radiusLeft"), item.get("radiusRight")],
        )

    # 4) the readout group styling and the 15px step to 新建轨道
    readout = items[3:6]
    check(
        "readouts:white-10-12px-f7f7f7",
        all(
            abs(alpha_of(item["background"]) - WHITE_10_ALPHA) < 0.001
            and item["fontSize"] == "12px"
            and item["color"] == TEXT_F7F7F7
            for item in readout
        ),
        detail=[
            [item["background"], item["fontSize"], item["color"]] for item in readout
        ],
    )
    check(
        "readouts:joined-at-1px",
        readout[1]["gap"] == 1 and readout[2]["gap"] == 1,
        detail=[item["gap"] for item in readout],
    )
    check(
        "add-track:15px-after-the-group",
        items[6]["gap"] == 15 and items[3]["gap"] == 4,
        detail={"before-group": items[3]["gap"], "before-add-track": items[6]["gap"]},
    )

    # 5) the toolbar opens in the source's ms mode
    unit = items[5]
    head = items[3]
    duration = items[4]
    check(
        "unit:opens-in-ms",
        unit["text"] == "ms"
        and unit["aria"] == "切换时间单位为 s"
        and head["value"] == "0"
        and duration["value"].isdigit()
        and int(duration["value"]) == 8000,
        detail={"text": unit["text"], "aria": unit["aria"],
                "head": head["value"], "duration": duration["value"]},
    )

    # 6) 自动帧 holds a 14px icon, not an 8px dot
    auto = items[1]
    check(
        "auto-keyframe:14px-icon",
        auto["svgBox"] is not None and auto["svgBox"] == [14, 14],
        detail=auto["svgBox"],
    )
    # The source's toggle reads aria-pressed="false", so only the OFF look was
    # measurable. The clone's own default stays `true` (batch 36 pins it, and
    # the source's value is the user's project state), so toggle it off here
    # and compare the OFF appearance against the source.
    page.locator("[data-director-auto-keyframe]").click()
    page.wait_for_timeout(200)
    # park the pointer away first: the button's hover rules (bg-white/10 /
    # text-white) are exactly what we are trying to measure past
    page.mouse.move(1500, 300)
    page.wait_for_timeout(250)
    auto_off = page.evaluate(
        """() => {
          const el = document.querySelector('[data-director-auto-keyframe]');
          const cs = getComputedStyle(el);
          return {background: cs.backgroundColor, color: cs.color,
                  pressed: el.getAttribute('aria-pressed')};
        }"""
    )
    result["autoKeyframeOff"] = auto_off
    check(
        "auto-keyframe:transparent-when-off",
        alpha_of(auto_off["background"]) < 0.001
        and abs(alpha_of(auto_off["color"]) - WHITE_80_ALPHA) < 0.001
        and auto_off["pressed"] == "false",
        detail=auto_off,
    )
    page.locator("[data-director-auto-keyframe]").click()
    page.wait_for_timeout(200)
    page.mouse.move(1500, 300)
    page.wait_for_timeout(150)

    # 7) 新建轨道: the visible text and the accessible name coexist
    add = items[6]
    check(
        "add-track:text-and-aria",
        add["text"] == "新建轨道"
        and add["aria"] == "选中角色、道具或分组后建立轨道"
        and add["fontSize"] == "13px",
        detail={"text": add["text"], "aria": add["aria"], "fontSize": add["fontSize"]},
    )

    # the play and loop buttons read as the source's
    check(
        "play:transparent-white-80",
        alpha_of(items[0]["background"]) < 0.001
        and abs(alpha_of(items[0]["color"]) - WHITE_80_ALPHA) < 0.001,
        detail=[items[0]["background"], items[0]["color"]],
    )
    check(
        "loop:lit-white-10-when-on",
        abs(alpha_of(items[2]["background"]) - WHITE_10_ALPHA) < 0.001
        and items[2]["color"] == TEXT_F7F7F7,
        detail=[items[2]["background"], items[2]["color"]],
    )

    check("no-console-errors", not errors, detail=errors[:5])
    return result


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1150})
        try:
            result = run_desktop(page)
        finally:
            browser.close()
    failed = [c for c in result["checks"] if not c["ok"]]
    print(
        f"Batch 601 verification: {len(result['checks']) - len(failed)}"
        f"/{len(result['checks'])} checks passed"
    )
    if failed:
        print("FAILED:", json.dumps(failed, ensure_ascii=False, indent=1))
        raise SystemExit(1)
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {AUDIT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
