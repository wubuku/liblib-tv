#!/usr/bin/env python3
"""Verify Batch 602: 左侧 rail 的节奏、分隔线与配色对齐源站。

Source facts (live CDP sampling of the source director desk at 1920x1150,
2026-10-01, /tmp/src593/probe50 + a nav child listing).

The source's icon rail is a `<nav>`:

    nav.border-white/8.flex.w-12.shrink-0.flex-col.items-center.gap-2
        .border-r.p-2            48x1098 @(0,52)   padding 8, gap 8, border-r white/8

inside

    aside.absolute.inset-y-0.left-0.z-30.overflow-hidden
         .border-r.border-white/10.bg-[#171717]      281x1150, bg rgb(23,23,23)

and under a 52px header (`关闭` 40x40 @(0,6) on the left, `收起` 40x40 @(240,6)
on the right).

Entries, 32x32, `rounded-lg`, 20px icon (`svg.size-5`), all at x=8:

    场景          y=60   aria-pressed=false  text-white/72  transparent
    divider       y=100  32x8  `border-white/8 h-2 w-8 border-b`
    添加角色      y=116  aria-pressed=true   bg-white/10    text-white
    添加机位      y=156  aria-pressed=false  text-white/72  transparent
    全景图        y=196  aria-pressed=false  text-white/72  transparent
    选择画幅比例   y=236  aria-pressed=false  text-white/72  transparent
    AI 识图导入    y=276  (no aria-pressed)  text-white/72  transparent
    帮助          y=1110 32x32  rounded-lg, pinned to the nav's bottom

So the rhythm is 40px (32 + gap-2) with a 24px step after 场景 where the 8px
divider sits between the two 8px gaps, and the idle/hover/active colours are
`text-white/72` / `hover:bg-white/8 hover:text-white` / `bg-white/10 text-white`.

The clone ran 46px wide with `gap-1` (a 36px pitch and no divider), a 16px icon,
`text-[#a5a5a5]` idle, `bg-white/[0.12]` active, `bg-[#1a1a1a]` rail and a
`rounded-full` help button.

NOT verified (recorded, not fabricated):
- the clone's first entry sits at y=92 and the source's at y=60. That is not a
  rail defect: the source's rail starts under a 52px header, the clone's under an
  84px top bar. Aligning it would mean reworking the top bar, which is a
  different surface, so the absolute offset stays and the *rhythm* is what this
  batch pins.
- which rail entry is active differs by project (the source has 添加角色
  selected, the clone opens on 场景), so the active styling is asserted by
  driving the clone's own selection rather than by assuming a default.
- `收起` and `关闭` in the source's 52px header stay as they are; the clone's
  top bar is a different structure.

Contract asserted here:
1. the rail is 48px wide with 8px padding, an 8px gap and a white/8 right border
   over #171717;
2. entries are 32x32 at x=8 with an 8px radius and a 20px icon;
3. the vertical rhythm is 40px, with a 24px step across the divider;
4. the 8x32 divider sits between 场景 and 添加角色 with a white/8 bottom border;
5. idle entries are white/72, the active one is white/10 bg + white text;
6. 帮助 is pinned to the bottom with the same 32x32 rounded-lg 20px treatment;
7. no diagnostics.
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
    / "liblib-canvas-batch602-2026-10-01"
    / "runtime-audit.json"
)

RAIL_BG = "rgb(23, 23, 23)"
WHITE_72_ALPHA = 0.72
WHITE_10_ALPHA = 0.1
WHITE_8_ALPHA = 0.08
PITCH = 40
DIVIDER_GAP = 24
ICON_PX = 20
RAIL_W = 48
RAIL_PAD = 8
RAIL_GAP = 8


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


READ = """() => {
  const cs = (el) => getComputedStyle(el);
  const at = (el) => { const r = el.getBoundingClientRect();
    return {x: Math.round(r.x), y: Math.round(r.y),
            w: Math.round(r.width), h: Math.round(r.height)}; };
  const rail = document.querySelector('[data-director-icon-rail]');
  const rc = cs(rail);
  const items = [...rail.querySelectorAll('[data-director-rail-entry]')].map((el) => {
    const c = cs(el);
    const svg = el.querySelector('svg');
    return {name: el.getAttribute('aria-label'), box: at(el),
      color: c.color, background: c.backgroundColor, radius: c.borderTopLeftRadius,
      pressed: el.getAttribute('aria-pressed'),
      icon: svg ? Math.round(svg.getBoundingClientRect().width) : null};
  });
  // gap = the space between two entries; the source's are [24, 8, 8, 8, 8],
  // the first one straddling the 8px divider (8 + 8 + 8)
  for (let i = 1; i < items.length; i++) {
    items[i].gap = items[i].box.y - (items[i - 1].box.y + items[i - 1].box.h);
    items[i].pitch = items[i].box.y - items[i - 1].box.y;
  }
  const divider = rail.querySelector('[data-director-rail-divider]');
  return {
    rail: {box: at(rail), padding: rc.padding, gap: rc.gap,
           background: rc.backgroundColor,
           borderRightWidth: rc.borderRightWidth,
           borderRightColor: rc.borderRightColor},
    divider: divider ? {...at(divider),
      borderBottomWidth: cs(divider).borderBottomWidth,
      borderBottomColor: cs(divider).borderBottomColor} : null,
    items,
  };
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
          store.addNode("script-execution", { title: "Batch 602" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(700)
    page.mouse.move(1500, 300)
    page.wait_for_timeout(250)
    snap = page.evaluate(READ)
    result["rail"] = snap

    rail = snap["rail"]
    items = snap["items"]
    main = [item for item in items if item["name"] != "帮助"]
    help_item = next(item for item in items if item["name"] == "帮助")

    # 1) the rail box itself
    check(
        "rail:48px-pad-8-gap-8-171717",
        rail["box"]["w"] == RAIL_W
        and rail["padding"] == f"{RAIL_PAD}px"
        and rail["gap"] == f"{RAIL_GAP}px"
        and rail["background"] == RAIL_BG
        and rail["borderRightWidth"] == "1px"
        and abs(alpha_of(rail["borderRightColor"]) - WHITE_8_ALPHA) < 0.001,
        detail=rail,
    )

    # 2) entry boxes, radius and icon size
    check(
        "entries:32x32-at-x8-rounded-lg-20px-icon",
        all(
            item["box"]["w"] == 32
            and item["box"]["h"] == 32
            and item["box"]["x"] == RAIL_PAD
            and item["radius"] == "8px"
            and item["icon"] == ICON_PX
            for item in items
        ),
        detail=[(item["name"], item["box"], item["icon"]) for item in items],
    )

    # 3) the rhythm: 40px, with a 24px step across the divider
    gaps = [item.get("gap") for item in main[1:]]
    pitches = [item.get("pitch") for item in main[1:]]
    check(
        "entries:40px-pitch-8px-gaps-24px-across-divider",
        gaps[0] == DIVIDER_GAP
        and all(gap == RAIL_GAP for gap in gaps[1:])
        and pitches[0] == 32 + DIVIDER_GAP
        and all(pitch == PITCH for pitch in pitches[1:]),
        detail={"gaps": gaps, "pitches": pitches},
    )

    # 4) the divider
    divider = snap["divider"]
    check(
        "divider:32x8-white-8-between-scene-and-character",
        divider is not None
        and divider["w"] == 32
        and divider["h"] == 8
        and divider["x"] == RAIL_PAD
        and divider["borderBottomWidth"] == "1px"
        and abs(alpha_of(divider["borderBottomColor"]) - WHITE_8_ALPHA) < 0.001
        and divider["y"] == main[0]["box"]["y"] + 32 + RAIL_GAP
        and divider["y"] + 8 + RAIL_GAP == main[1]["box"]["y"],
        detail=divider,
    )

    # 5) idle vs active colours — drive the clone's own selection
    idle = [item for item in main if item["pressed"] == "false"]
    active = [item for item in main if item["pressed"] == "true"]
    check(
        "entries:idle-white-72",
        len(idle) >= 3
        and all(
            abs(alpha_of(item["color"]) - WHITE_72_ALPHA) < 0.001
            and alpha_of(item["background"]) < 0.001
            for item in idle
        ),
        detail=[(item["name"], item["color"], item["background"]) for item in idle],
    )
    check(
        "entries:active-white-10-on-white",
        len(active) == 1
        and abs(alpha_of(active[0]["background"]) - WHITE_10_ALPHA) < 0.001
        and abs(alpha_of(active[0]["color"]) - 1.0) < 0.001,
        detail=active,
    )

    # 6) 帮助: pinned to the bottom, same treatment as the other entries
    last = main[-1]
    check(
        "help:pinned-to-the-bottom",
        help_item["box"]["y"]
        >= rail["box"]["y"] + rail["box"]["h"] - 2 * RAIL_PAD - 32
        and help_item["box"]["y"] > last["box"]["y"] + 100,
        detail={"help": help_item["box"], "rail": rail["box"], "last": last["box"]},
    )
    check(
        "help:rounded-lg-20px-icon-idle-white-72",
        help_item["radius"] == "8px"
        and help_item["icon"] == ICON_PX
        and abs(alpha_of(help_item["color"]) - WHITE_72_ALPHA) < 0.001,
        detail=help_item,
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
        f"Batch 602 verification: {len(result['checks']) - len(failed)}"
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
