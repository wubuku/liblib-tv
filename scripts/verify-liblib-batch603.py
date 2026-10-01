#!/usr/bin/env python3
"""Verify Batch 603: 属性面板页签条的几何与胶囊样式对齐源站。

Source facts (live CDP sampling of the source director desk at 1920x1150,
2026-10-01, /tmp/src593/probe49, sampled with 主机位 selected).

The source wraps its tab strip in a `<section>` and the strip itself in a
scroll container that hides its scrollbar:

    section.border-white/8.relative.w-full.min-w-0.max-w-full.overflow-hidden
           .border-b.px-4.pb-3                          280x57 @(1640,48)
      div.scrollbar-hide.flex.w-full.min-w-0.max-w-full.gap-2
          .overflow-x-auto.overflow-y-hidden.pt-4        248x44 @(1656,48)

16 (pt-4) + 28 (tab) + 12 (pb-3) + 1 (border-b) = 57.

Tabs, all `relative flex h-7 min-w-12 shrink-0 items-center justify-center
rounded-lg px-3 text-[13px] font-normal transition-colors`, content-sized on a
48px floor — 50 / 76 / 50 with 8px gaps, not equal columns:

    属性      @(1656,64) 50x28  active   bg-white/10    text-neutral-50
    运动轨迹   @(1714,64) 76x28  inactive text-white/45  hover:bg-white/6
    截图      @(1798,64) 50x28  inactive text-white/45  hover:text-white/75

The 运动轨迹 tab carries a NEW badge, verbatim:

    span[aria-hidden].pointer-events-none.absolute.right-0.top-0.z-10.flex.h-5
         .-translate-y-[70%].items-center.justify-center.rounded-t-lg
         .rounded-bl-sm.rounded-br-lg.bg-[#5DDCFF].px-1.5.text-[11px]
         .font-medium.leading-3.text-black

The clone ran `grid h-9 shrink-0 grid-cols-3 border-b border-white/[0.07]
bg-[#171717] p-1` — equal-width columns in a fixed 36px bar, `rounded` (4px)
tabs at 11px, active `bg-[#292929] text-[#d9d9d9]`, and a `rounded-full` 8px
`bg-[#09caf5]` badge.

The tab SET is unchanged by this batch. The source's camera inspector already
matches the clone's three tabs (属性 / 运动轨迹 / 截图, from batch 581); the
character inspector's set was never sampled on the source, so the clone's
属性 / 姿势 stays and only the shared chrome is aligned — an inference, not a
source fact.

Contract asserted here:
1. the section is 57px tall with a 1px bottom border and 16/12px side/bottom
   padding;
2. the strip is 44px with 8px gaps, 16px top padding and a hidden scrollbar;
3. the three tabs are 50 / 76 / 50 wide, 28 tall, 8px radius, 12px side padding,
   13px type, with 8px gaps;
4. the active tab is white/10 over #F7F7F7, the inactive ones white/45;
5. the NEW badge is #5DDCFF, 20px tall, 11px medium black, aria-hidden and
   pointer-events-none, anchored to the 运动轨迹 tab's top-right;
6. the character tabs share the same chrome;
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
    / "liblib-canvas-batch603-2026-10-01"
    / "runtime-audit.json"
)

GLOBALS = ROOT / "src/app/globals.css"
WHITE_10_ALPHA = 0.1
WHITE_45_ALPHA = 0.45
ACTIVE_TEXT = "rgb(247, 247, 247)"
BADGE_BG = "rgb(93, 220, 255)"
BADGE_TEXT = "rgb(0, 0, 0)"
SECTION_H = 57
STRIP_H = 44
TAB_H = 28
TAB_W = [50, 76, 50]
TAB_GAP = 8


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


READ = """(sel) => {
  const at = (el) => { const r = el.getBoundingClientRect();
    return {x: Math.round(r.x), y: Math.round(r.y),
            w: Math.round(r.width), h: Math.round(r.height)}; };
  const cs = (el) => getComputedStyle(el);
  const nav = document.querySelector(sel);
  if (!nav) return {missing: true};
  const strip = nav.firstElementChild;
  const tabs = [...nav.querySelectorAll('[data-director-camera-tab], [data-director-character-tab]')]
    .map((el) => {
      const c = cs(el);
      return {text: (el.textContent || '').trim(), box: at(el),
        background: c.backgroundColor, color: c.color, fontSize: c.fontSize,
        radius: c.borderTopLeftRadius, padding: c.padding,
        pressed: el.getAttribute('aria-pressed')};
    });
  for (let i = 1; i < tabs.length; i++) {
    tabs[i].gap = tabs[i].box.x - (tabs[i - 1].box.x + tabs[i - 1].box.w);
  }
  const badge = nav.querySelector('[data-director-camera-motion-new]');
  const bc = badge ? cs(badge) : null;
  const nc = cs(nav);
  const sc = cs(strip);
  return {
    nav: {box: at(nav), padding: nc.padding,
          borderBottomWidth: nc.borderBottomWidth, borderBottomColor: nc.borderBottomColor},
    strip: {box: at(strip), gap: sc.gap, paddingTop: sc.paddingTop,
            scrollbarWidth: sc.scrollbarWidth,
            overflowX: sc.overflowX, overflowY: sc.overflowY},
    tabs,
    badge: badge ? {box: at(badge), background: bc.backgroundColor, color: bc.color,
      fontSize: bc.fontSize, borderTopLeftRadius: bc.borderTopLeftRadius,
      ariaHidden: badge.getAttribute('aria-hidden'),
      pointerEvents: bc.pointerEvents} : null,
  };
}"""


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1920x1150", "checks": []}

    def check(name: str, ok: bool, detail: Any = None) -> None:
        result["checks"].append({"name": name, "ok": bool(ok), "detail": detail})

    css = GLOBALS.read_text()
    check(
        "static:scrollbar-hide-declared",
        ".scrollbar-hide {" in css
        and "scrollbar-width: none;" in css
        and "display: none;" in css,
        detail="globals.css carries the lifted .scrollbar-hide rules",
    )

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 603" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(700)
    page.evaluate(
        """() => {
          const d = window.__director_store.getState();
          d.selectObject(d.objects.find((o) => o.kind === 'camera').id);
        }"""
    )
    page.locator("[data-director-camera-tabs]").wait_for(state="visible")
    page.wait_for_timeout(500)
    page.mouse.move(900, 600)
    page.wait_for_timeout(250)
    cam = page.evaluate(READ, "[data-director-camera-tabs]")
    result["camera"] = cam

    # 1) the section
    check(
        "section:57px-border-b-16-12",
        cam["nav"]["box"]["h"] == SECTION_H
        and cam["nav"]["borderBottomWidth"] == "1px"
        and abs(alpha_of(cam["nav"]["borderBottomColor"]) - 0.08) < 0.001
        and cam["nav"]["padding"] == "0px 16px 12px",
        detail=cam["nav"],
    )

    # 2) the strip
    check(
        "strip:44px-gap-8-pt-16-hidden-scrollbar",
        cam["strip"]["box"]["h"] == STRIP_H
        and cam["strip"]["gap"] == f"{TAB_GAP}px"
        and cam["strip"]["paddingTop"] == "16px"
        and cam["strip"]["scrollbarWidth"] == "none"
        and cam["strip"]["overflowX"] == "auto"
        and cam["strip"]["overflowY"] == "hidden",
        detail=cam["strip"],
    )

    # 3) tab boxes
    widths = [tab["box"]["w"] for tab in cam["tabs"]]
    check(
        "tabs:50-76-50-28h-8px-radius",
        [tab["box"]["h"] for tab in cam["tabs"]] == [TAB_H] * 3
        and widths == TAB_W,
        detail=widths,
    )
    check(
        "tabs:content-sized-not-equal-columns",
        len(set(widths)) > 1
        and [tab["gap"] for tab in cam["tabs"][1:]] == [TAB_GAP] * 2,
        detail={"widths": widths,
                "gaps": [tab.get("gap") for tab in cam["tabs"][1:]]},
    )
    check(
        "tabs:13px-12px-padding",
        all(
            tab["fontSize"] == "13px" and tab["padding"] == "0px 12px"
            and tab["radius"] == "8px"
            for tab in cam["tabs"]
        ),
        detail=[(tab["fontSize"], tab["padding"], tab["radius"]) for tab in cam["tabs"]],
    )

    # 4) active vs inactive
    active = [tab for tab in cam["tabs"] if tab["pressed"] == "true"]
    idle = [tab for tab in cam["tabs"] if tab["pressed"] == "false"]
    check(
        "tabs:active-white-10-neutral-50",
        len(active) == 1
        and abs(alpha_of(active[0]["background"]) - WHITE_10_ALPHA) < 0.001
        and active[0]["color"] == ACTIVE_TEXT,
        detail=active,
    )
    check(
        "tabs:inactive-white-45",
        len(idle) == 2
        and all(
            abs(alpha_of(tab["color"]) - WHITE_45_ALPHA) < 0.001
            and alpha_of(tab["background"]) < 0.001
            for tab in idle
        ),
        detail=[(tab["text"], tab["color"], tab["background"]) for tab in idle],
    )

    # 5) the NEW badge
    badge = cam["badge"]
    motion = next(
        (tab for tab in cam["tabs"] if tab["text"].startswith("运动轨迹")), None
    )
    check(
        "badge:5ddcff-20h-11px-black-hidden",
        badge is not None
        and badge["background"] == BADGE_BG
        and badge["color"] == BADGE_TEXT
        and badge["fontSize"] == "11px"
        and badge["box"]["h"] == 20
        and badge["ariaHidden"] == "true"
        and badge["pointerEvents"] == "none",
        detail=badge,
    )
    check(
        "badge:anchored-to-the-motion-tab-top-right",
        badge is not None
        and motion is not None
        and badge["box"]["x"] + badge["box"]["w"] == motion["box"]["x"] + motion["box"]["w"]
        and badge["box"]["y"] < motion["box"]["y"],
        detail={"badge": badge["box"] if badge else None,
                "motion": motion["box"] if motion else None},
    )

    # 6) the character tabs share the same chrome
    page.evaluate(
        """() => {
          const d = window.__director_store.getState();
          d.selectObject(d.objects.find((o) => o.kind === 'character').id);
        }"""
    )
    page.locator("[data-director-character-tabs]").wait_for(state="visible")
    page.wait_for_timeout(400)
    page.mouse.move(900, 600)
    page.wait_for_timeout(200)
    ch = page.evaluate(READ, "[data-director-character-tabs]")
    result["character"] = ch
    check(
        "character-tabs:share-the-chrome",
        ch["nav"]["box"]["h"] == SECTION_H
        and ch["strip"]["box"]["h"] == STRIP_H
        and ch["strip"]["gap"] == f"{TAB_GAP}px"
        and all(
            tab["box"]["h"] == TAB_H
            and tab["radius"] == "8px"
            and tab["fontSize"] == "13px"
            for tab in ch["tabs"]
        ),
        detail={"nav": ch["nav"]["box"], "strip": ch["strip"]["box"], "tabs": ch["tabs"]},
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
        f"Batch 603 verification: {len(result['checks']) - len(failed)}"
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
