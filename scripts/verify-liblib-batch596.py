#!/usr/bin/env python3
"""Verify Batch 596: 「导出视频到画布」归位到时间轴右格 + 两格工具条结构。

Source facts (live CDP sampling of the source director desk at 1920x1150,
2026-10-01, /tmp/src593/probe14+20):

The strip's right cell is 244x36 @(1676,1021):

    absolute right-0 top-0 z-20 flex h-9 items-center gap-2 bg-[#212121] pr-2
      |- flex h-9 w-[120px] items-center gap-2 border-l border-white/[0.08]
      |  bg-[#212121] px-2                     <- the zoom cluster (batch 594)
      |- button 108x28 @(1804,1025)
           bg #f7f7f7, radius 8px, colour #141414, 12px font-medium,
           class "relative flex h-7 shrink-0 items-center gap-2 rounded-lg
                  bg-[#f7f7f7] px-3 text-[12px] font-medium leading-none
                  text-[#141414] ..."
           contains ONE <span>导出视频到画布</span> and a 1px transparent guide
           span — i.e. it is TEXT ONLY, no icon.

Exactly one such button exists in the whole source document, and it is inside
the timeline strip — the director's top header has no export button.

The clone had it in the top header as a dark ghost button (`h-8 px-2
text-[11px] text-[#b5b5b5]`) with a FileVideo2 icon.

Structural consequence: the strip is TWO cells. The left cell scrolls
horizontally (the clone's toolbar is much longer than the source's); the right
cell floats above it. The right cell must live OUTSIDE the scrolling header —
`overflow-x-auto` computes `overflow-y` to `auto` per CSS, which clipped the
upward-opening export panel (measured: the panel's centre hit-tested onto the
WebGL canvas).

NOT verified (recorded, not fabricated): the source's export PANEL geometry.
Clicking the source's button could start a real video export inside the user's
project, which is an externally visible / paid-class action, so it was not
exercised. The clone's panel now opens upward (`bottom-full`) because the strip
is flush with the viewport bottom — an inference, flagged as such.

Contract asserted here:
1. the strip renders a right cell (absolute right-0 top-0, 244-ish wide) that
   holds the zoom cluster and the export trigger;
2. the export trigger is inside that right cell, is a 108x28 light primary
   button (bg #f7f7f7, colour #141414, radius 8px, 12px) and is TEXT ONLY;
3. the trigger is NOT in the director top header any more;
4. the left cell still carries the source's seven controls as a prefix and
   still scrolls horizontally;
5. opening the panel puts it fully on screen — no ancestor clips it, and its
   centre hit-tests onto the panel rather than the viewport canvas;
6. no diagnostics.
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
    / "liblib-canvas-batch596-2026-10-01"
    / "runtime-audit.json"
)

TRIGGER_W = 108
TRIGGER_H = 28
TRIGGER_BG = "rgb(247, 247, 247)"
TRIGGER_COLOR = "rgb(20, 20, 20)"
TRIGGER_RADIUS = "8px"
STRIP_H = 36
SOURCE_PREFIX = [
    "播放",
    "自动帧",
    "循环播放",
    "播放头位置",
    "总时长",
    "切换时间单位为 ms",
    "选中角色、道具或分组后建立轨道",
]


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


def open_desk(page: Page) -> None:
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 596" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(600)
    page.locator("[data-director-timeline-controls]").wait_for(state="visible")


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1920x1150", "checks": []}

    def check(name: str, ok: bool, detail: Any = None) -> None:
        result["checks"].append(
            {"name": name, "ok": bool(ok), "detail": detail}
        )

    errors = attach_errors(page)
    open_desk(page)

    # 1-3) the right cell and the trigger's geometry / style / ancestry
    strip = page.evaluate(
        """() => {
          const cell = document.querySelector('[data-director-timeline-strip-right]');
          const r = cell.getBoundingClientRect();
          const cs = getComputedStyle(cell);
          const trigger = cell.querySelector('[data-director-export-trigger]');
          const tr = trigger.getBoundingClientRect();
          const tcs = getComputedStyle(trigger);
          const header = document.querySelector('[data-director-workspace] header');
          return {
            cell: {box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
                   position: cs.position, background: cs.backgroundColor,
                   paddingRight: cs.paddingRight, zIndex: cs.zIndex,
                   hasCluster: Boolean(cell.querySelector('[data-director-timeline-zoom-cluster]'))},
            trigger: {box: [Math.round(tr.x), Math.round(tr.y), Math.round(tr.width), Math.round(tr.height)],
                      background: tcs.backgroundColor, color: tcs.color,
                      radius: tcs.borderRadius, fontSize: tcs.fontSize,
                      fontWeight: tcs.fontWeight,
                      text: (trigger.innerText || '').trim(),
                      svgCount: trigger.querySelectorAll('svg').length,
                      spanCount: trigger.querySelectorAll('span').length,
                      inHeader: Boolean(trigger.closest('[data-director-timeline-controls]'))},
            headerHasExport: Boolean(header.querySelector('[data-director-export-trigger]')),
            headerOverflowX: getComputedStyle(
              document.querySelector('[data-director-timeline-controls]')).overflowX,
            headerOverflowY: getComputedStyle(
              document.querySelector('[data-director-timeline-controls]')).overflowY,
            order: [...document.querySelector('[data-director-timeline-controls]')
              .querySelectorAll('button, input')].map((el) => (
                el.getAttribute('aria-label') || (el.innerText || '').trim()
                || el.getAttribute('data-director-time-field') || el.getAttribute('type')
              )).filter(Boolean),
          };
        }"""
    )
    result["strip"] = strip
    check(
        "strip-right:cell",
        strip["cell"]["box"][3] == STRIP_H
        and strip["cell"]["position"] == "absolute"
        and strip["cell"]["hasCluster"],
        detail=strip["cell"],
    )
    check(
        "export:geometry",
        strip["trigger"]["box"][2] == TRIGGER_W
        and strip["trigger"]["box"][3] == TRIGGER_H,
        detail=strip["trigger"]["box"],
    )
    check(
        "export:light-primary-style",
        strip["trigger"]["background"] == TRIGGER_BG
        and strip["trigger"]["color"] == TRIGGER_COLOR
        and strip["trigger"]["radius"] == TRIGGER_RADIUS
        and strip["trigger"]["fontSize"] == "12px"
        and strip["trigger"]["fontWeight"] in {"500", "600"},
        detail={
            key: strip["trigger"][key]
            for key in ("background", "color", "radius", "fontSize", "fontWeight")
        },
    )
    check(
        "export:text-only",
        strip["trigger"]["text"] == "导出视频到画布" and strip["trigger"]["svgCount"] == 0,
        detail={
            "text": strip["trigger"]["text"],
            "svg": strip["trigger"]["svgCount"],
            "spans": strip["trigger"]["spanCount"],
        },
    )
    check(
        "export:left-the-header",
        strip["headerHasExport"] is False and strip["trigger"]["inHeader"] is False,
        detail={
            "headerHasExport": strip["headerHasExport"],
            "inHeader": strip["trigger"]["inHeader"],
        },
    )
    check(
        "strip:left-cell-scrolls",
        strip["headerOverflowX"] in {"auto", "scroll"}
        and strip["order"][: len(SOURCE_PREFIX)] == SOURCE_PREFIX,
        detail={"overflow": [strip["headerOverflowX"], strip["headerOverflowY"]],
                "order": strip["order"][: len(SOURCE_PREFIX) + 1]},
    )

    # 5) the panel is not clipped and hit-tests onto itself
    page.locator("[data-director-export-trigger]").click()
    panel = page.locator("[data-director-export-panel]")
    panel.wait_for(state="visible")
    page.wait_for_timeout(250)
    panel_state = page.evaluate(
        """() => {
          const panel = document.querySelector('[data-director-export-panel]');
          const r = panel.getBoundingClientRect();
          const cx = r.x + r.width / 2;
          const cy = r.y + r.height / 2;
          const hit = document.elementFromPoint(cx, cy);
          // Walk ancestors looking for a clipper that would actually CUT the
          // panel. The workspace root and the app shell are overflow:hidden at
          // full viewport size, so they contain the panel and are harmless.
          const clippers = [];
          let e = panel.parentElement;
          while (e) {
            const cs = getComputedStyle(e);
            const b = e.getBoundingClientRect();
            const cuts =
              r.left < b.left - 0.5 || r.top < b.top - 0.5
              || r.right > b.right + 0.5 || r.bottom > b.bottom + 0.5;
            if (cs.overflow !== 'visible' && cuts) {
              clippers.push({tag: e.tagName.toLowerCase(), overflow: cs.overflow,
                             box: [Math.round(b.x), Math.round(b.y),
                                   Math.round(b.width), Math.round(b.height)]});
            }
            e = e.parentElement;
          }
          return {box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
                  viewport: [window.innerWidth, window.innerHeight],
                  hitInside: Boolean(hit && panel.contains(hit)),
                  hit: hit ? hit.tagName.toLowerCase() : null,
                  clippers};
        }"""
    )
    result["panel"] = panel_state
    check(
        "panel:hit-testable",
        panel_state["hitInside"] is True,
        detail={"hit": panel_state["hit"], "box": panel_state["box"]},
    )
    check(
        "panel:on-screen",
        panel_state["box"][0] >= 0
        and panel_state["box"][1] >= 0
        and panel_state["box"][0] + panel_state["box"][2]
        <= panel_state["viewport"][0]
        and panel_state["box"][1] + panel_state["box"][3]
        <= panel_state["viewport"][1],
        detail=panel_state,
    )
    check(
        "panel:no-clipping-ancestor",
        not panel_state["clippers"],
        detail=panel_state["clippers"],
    )

    page.screenshot(
        path=str(
            ROOT / "docs" / "design-references" / "liblib-timeline-export-1920.png"
        )
    )
    result["diagnostics"] = errors
    check("no-diagnostics", not errors, detail=errors)
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 596,
        "title": "导出视频到画布归位到时间轴右格（浅色主按钮 108x28，纯文字）+ 工具条两格结构",
        "evidence": (
            "2026-10-01 live CDP sampling of the source director desk at "
            "1920x1150 + docs/research/liblib-canvas-batch596-2026-10-01/README.md"
        ),
        "source_facts": {
            "right_cell": "244x36 @(1676,1021), absolute right-0 top-0 z-20 flex h-9 items-center gap-2 bg-[#212121] pr-2",
            "export_button": "108x28 @(1804,1025), bg #f7f7f7, radius 8px, colour #141414, 12px medium, text only (no icon)",
            "export_button_count_in_document": 1,
            "export_button_location": "inside the timeline strip; the director top header has none",
        },
        "clone_only": [
            "the panel opens upward (bottom-full) — the source's panel geometry was "
            "not measured because clicking the source button could start a real "
            "export in the user's project",
            "the left cell keeps pr-[260px] so the scrolling toolbar does not run "
            "under the floating right cell",
        ],
        "not_verified": [
            "the source's export panel size, position and contents — not exercised, "
            "clicking the source trigger is an externally visible / paid-class action",
        ],
        "migrated_contracts": [
            "batch 40: the mobile panel right margin 12px -> 8px, because the right "
            "cell itself carries the source's pr-2",
        ],
        "results": [],
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(
            viewport={"width": 1920, "height": 1150}, device_scale_factor=1
        )
        audit["results"].append(run_desktop(desktop))
        desktop.close()
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    checks = audit["results"][0]["checks"]
    failed = [item for item in checks if not item["ok"]]
    print(
        f"Batch 596 verification: {len(checks) - len(failed)}/{len(checks)} checks passed"
    )
    if failed:
        raise SystemExit(
            "FAILED: " + json.dumps(failed, ensure_ascii=False, indent=2)
        )


if __name__ == "__main__":
    main()
