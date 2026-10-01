#!/usr/bin/env python3
"""Verify Batch 594: 时间轴右列缩放簇（自绘轨道 + 0-100 量程 + 标尺宽度公式）。

Source facts (live CDP sampling of the source director desk at 1920x1150,
2026-10-01, evidence under /tmp/src593/probe14-19):

The timeline's right cell is a 120px cluster, not a labelled slider:

    cluster  div.flex.h-9.w-[120px].items-center.gap-2
                  .border-l.border-white/[0.08].bg-[#212121].px-2
    slider   input[type=range][aria-label="时间轴缩放"]  min=0 max=100
             **no step attribute** (browser default step 1), 71x24,
             absolutely positioned, appearance-none, opacity 0
    track    span 71x4  rounded-full  bg white/40   (self drawn)
    thumb    span 12x12 rounded-full  border+bg #F7F7F7  (self drawn)
    minimize button 24x24, aria-label 时间线最小化 -> 展开时间线

There is NO magnifier icon and no <label> wrapper — the clone had
`<ZoomIn size={13}/>` plus a native `accent-[#09caf5]` range at
min 0.75 / max 2.5 / step 0.25.

Ruler width vs zoom, sampled on the source (总时长 = 10000 ms) by reading the
canvas element's width after clicking the slider:

    zoom    0    16    31    49    64    82    100
    width 1598  1598  1598  2473  3220  4116  5012

49 / 64 / 82 / 100 are strictly collinear: slope 49.78 px per zoom step and
intercept ~=33.6px, i.e. 3.36 + 4.978*zoom px per second. Below zoom 31 the
content is clamped to the container width (1598).

The clone used `max(640, duration * 80 * zoom)` with zoom in 0.75..2.5.

NOT verified (recorded, not fabricated):
* the source's DEFAULT zoom. The sampled project sits at 43.7751, but that is
  a value the user dragged; the default cannot be recovered without resetting
  their project. The clone seeds 44 so the opening density matches what the
  source currently looks like — an inference, flagged as such in the store.
* how the px/s slope scales with 总时长. Only the 10s point was sampled;
  changing the source's duration writes the user's project, so the
  duration-proportional extrapolation is an inference.
* the source clamps content width to the CONTAINER width, which is dynamic.
  The clone keeps its own 640px floor and says so.

Contract asserted here:
1. the zoom input is min=0 / max=100 with no step attribute and 71x24;
2. the self-drawn track is 71x4 rounded-full and the thumb 12x12;
3. the thumb position and the filled track follow the value;
4. the cluster is 120x36 with the border-left and #212121 background, and it
   contains both the slider and the 时间线最小化 button (24x24);
5. there is no magnifier icon inside the cluster;
6. the clone's ruler width follows 3.36 + 4.978*zoom px/s (above the floor);
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
    / "liblib-canvas-batch594-2026-10-01"
    / "runtime-audit.json"
)

# Tailwind 的 rounded-full 在 Chromium 里解析成一个巨大的 px 值（实测
# 3.35544e+07px），不是字面量 9999px；只断言「圆到不能再圆」。
FULL_ROUND_MIN_PX = 1000

CLUSTER_W = 120
CLUSTER_H = 36
SLIDER_W = 71
SLIDER_H = 24
TRACK_H = 4
THUMB = 12
# 源站实测斜率（总时长 10000ms）：49/64/82/100 四点共线
PX_PER_SEC_BASE = 3.36
PX_PER_SEC_PER_ZOOM = 4.978


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
    page.on(
        "requestfailed",
        lambda request: errors.append(
            f"requestfailed:{request.method}:{request.url}:{request.failure}"
        ),
    )
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1920x1150", "checks": []}

    def check(name: str, ok: bool, detail: Any = None) -> None:
        result["checks"].append(
            {"name": name, "ok": bool(ok), "detail": detail}
        )

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 594" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(600)
    page.locator("[data-director-timeline-controls]").wait_for(state="visible")

    # 1-5) the cluster's own geometry
    cluster = page.evaluate(
        """() => {
          const cluster = document.querySelector('[data-director-timeline-zoom-cluster]');
          const r = cluster.getBoundingClientRect();
          const cs = getComputedStyle(cluster);
          const zoom = cluster.querySelector('[data-director-timeline-zoom]');
          const zr = zoom.getBoundingClientRect();
          const track = cluster.querySelector('div > div[aria-hidden="true"]');
          const thumb = cluster.querySelectorAll('div[aria-hidden="true"]')[1];
          const tr = track.getBoundingClientRect();
          const thr = thumb.getBoundingClientRect();
          const minimize = cluster.querySelector('[data-director-timeline-collapse]');
          const mr = minimize.getBoundingClientRect();
          return {
            cluster: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
            borderLeft: cs.borderLeftWidth + ' ' + cs.borderLeftColor,
            background: cs.backgroundColor,
            zoom: {min: zoom.min, max: zoom.max, step: zoom.getAttribute('step'),
                   value: Number(zoom.value), type: zoom.type,
                   title: zoom.getAttribute('title'),
                   box: [Math.round(zr.x), Math.round(zr.y), Math.round(zr.width), Math.round(zr.height)],
                   opacity: getComputedStyle(zoom).opacity,
                   appearance: getComputedStyle(zoom).appearance},
            track: {box: [Math.round(tr.x), Math.round(tr.y), Math.round(tr.width), Math.round(tr.height)],
                    radius: getComputedStyle(track).borderRadius,
                    background: getComputedStyle(track).backgroundColor},
            thumb: {box: [Math.round(thr.x), Math.round(thr.y), Math.round(thr.width), Math.round(thr.height)],
                    radius: getComputedStyle(thumb).borderRadius,
                    background: getComputedStyle(thumb).backgroundColor,
                    left: thumb.style.left, transform: thumb.style.transform},
            minimize: {aria: minimize.getAttribute('aria-label'),
                       box: [Math.round(mr.x), Math.round(mr.y), Math.round(mr.width), Math.round(mr.height)]},
            svgCount: cluster.querySelectorAll('svg').length,
            labelCount: cluster.querySelectorAll('label').length,
            fillWidth: track.firstElementChild.style.width,
          };
        }"""
    )
    result["cluster"] = cluster
    check(
        "cluster:120x36",
        cluster["cluster"][2] == CLUSTER_W and cluster["cluster"][3] == CLUSTER_H,
        detail=cluster["cluster"],
    )
    check(
        "cluster:border-left-and-bg",
        cluster["borderLeft"].startswith("1px ")
        and cluster["background"] == "rgb(33, 33, 33)",
        detail={"borderLeft": cluster["borderLeft"], "background": cluster["background"]},
    )
    check(
        "zoom:range-0-100-no-step",
        cluster["zoom"]["min"] == "0"
        and cluster["zoom"]["max"] == "100"
        and cluster["zoom"]["step"] is None
        and cluster["zoom"]["type"] == "range"
        and cluster["zoom"]["title"] == "时间轴缩放",
        detail=cluster["zoom"],
    )
    check(
        "zoom:71x24-transparent",
        cluster["zoom"]["box"][2] == SLIDER_W
        and cluster["zoom"]["box"][3] == SLIDER_H
        and cluster["zoom"]["opacity"] == "0",
        detail=cluster["zoom"],
    )
    check(
        "track:71x4-round",
        cluster["track"]["box"][2] == SLIDER_W
        and cluster["track"]["box"][3] == TRACK_H
        and float(cluster["track"]["radius"].removesuffix("px"))
        >= FULL_ROUND_MIN_PX,
        detail=cluster["track"],
    )
    check(
        "thumb:12x12-round",
        cluster["thumb"]["box"][2] == THUMB
        and cluster["thumb"]["box"][3] == THUMB
        and float(cluster["thumb"]["radius"].removesuffix("px"))
        >= FULL_ROUND_MIN_PX,
        detail=cluster["thumb"],
    )
    check(
        "minimize:24x24-inside-cluster",
        cluster["minimize"]["aria"] == "时间线最小化"
        and cluster["minimize"]["box"][2] == 24
        and cluster["minimize"]["box"][3] == 24,
        detail=cluster["minimize"],
    )
    check(
        "cluster:no-icon-no-label",
        cluster["svgCount"] == 1 and cluster["labelCount"] == 0,
        detail={"svg": cluster["svgCount"], "label": cluster["labelCount"]},
    )

    # 3) the fill and the thumb follow the value
    page.evaluate(
        "() => window.__director_store.getState().setTimelineZoom(25)"
    )
    page.wait_for_timeout(200)
    at_25 = page.evaluate(
        """() => {
          const cluster = document.querySelector('[data-director-timeline-zoom-cluster]');
          const track = cluster.querySelector('div > div[aria-hidden="true"]');
          const thumb = cluster.querySelectorAll('div[aria-hidden="true"]')[1];
          return {fill: track.firstElementChild.style.width, left: thumb.style.left,
                  value: Number(cluster.querySelector('input').value)};
        }"""
    )
    result["at_25"] = at_25
    check(
        "zoom:fill-and-thumb-follow",
        at_25["value"] == 25 and at_25["fill"] == "25%" and at_25["left"] == "25%",
        detail=at_25,
    )

    # 6) the ruler width follows the measured px/s law
    width = page.evaluate(
        """(z) => {
          window.__director_store.getState().setTimelineZoom(z);
          return null;
        }""",
        0,
    )
    del width
    samples = {}
    for zoom in (0, 25, 50, 100):
        page.evaluate(
            "(z) => window.__director_store.getState().setTimelineZoom(z)", zoom
        )
        page.wait_for_timeout(200)
        samples[zoom] = page.evaluate(
            """() => Math.round(document.querySelector('[data-director-timeline-canvas]')
                 .getBoundingClientRect().width)"""
        )
    result["ruler_width"] = samples
    duration = page.evaluate(
        "() => window.__director_store.getState().timeline.duration"
    )
    # 源站把内容宽度夹在**容器宽**上（实测 zoom 0/16/31 都是 1598 = 容器宽）；
    # clone 的轨道容器是 `min-w-full` 的 flex-1，所以同一个下限在这里体现为
    # 容器宽而不是算出来的 640。
    container = page.evaluate(
        """() => {
          const canvas = document.querySelector('[data-director-timeline-canvas]');
          return Math.round(canvas.parentElement.getBoundingClientRect().width);
        }"""
    )
    expected = {
        zoom: max(
            container,
            640,
            round(duration * (PX_PER_SEC_BASE + PX_PER_SEC_PER_ZOOM * zoom)),
        )
        for zoom in samples
    }
    result["ruler_width_expected"] = expected
    result["ruler_container_width"] = container
    check(
        "ruler:width-follows-source-law",
        samples == expected,
        detail={
            "actual": samples,
            "expected": expected,
            "duration": duration,
            "container": container,
        },
    )
    check(
        "ruler:clamps-to-container-then-grows",
        samples[0] == samples[25] == container
        and samples[50] > container
        and samples[100] > samples[50],
        detail={"samples": samples, "container": container},
    )

    page.evaluate(
        "() => window.__director_store.getState().setTimelineZoom(44)"
    )
    page.wait_for_timeout(150)
    page.screenshot(
        path=str(
            ROOT / "docs" / "design-references" / "liblib-timeline-zoom-cluster-1920.png"
        )
    )

    result["diagnostics"] = errors
    check("no-diagnostics", not errors, detail=errors)
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 594,
        "title": "时间轴右列缩放簇：自绘轨道 + 12px 圆钮 + 0-100 量程 + 标尺宽度公式",
        "evidence": (
            "2026-10-01 live CDP sampling of the source director desk at "
            "1920x1150 + docs/research/liblib-canvas-batch594-2026-10-01/README.md"
        ),
        "source_facts": {
            "cluster": "120x36 flex h-9 w-[120px] gap-2 border-l border-white/[0.08] bg-[#212121] px-2",
            "slider": "input[type=range] min=0 max=100, no step attribute, 71x24, opacity 0, appearance-none",
            "track": "71x4 rounded-full white/40",
            "thumb": "12x12 rounded-full border+bg #F7F7F7",
            "minimize": "24x24 inside the cluster, 时间线最小化 / 展开时间线",
            "ruler_width_by_zoom_at_10s": {
                "0": 1598,
                "16": 1598,
                "31": 1598,
                "49": 2473,
                "64": 3220,
                "82": 4116,
                "100": 5012,
            },
            "ruler_width_law": "3.36 + 4.978*zoom px per second, clamped to the container width",
            "no_magnifier_icon": True,
        },
        "clone_only": [
            "the ruler keeps a 640px floor — the source clamps to its (dynamic) container width",
        ],
        "not_verified": [
            "the source's DEFAULT zoom: the sampled project sits at 43.7751 but that is a "
            "user-dragged value, so the clone seeds 44 to match the current look and says so",
            "how the px/s slope scales with 总时长: only the 10s point was sampled, the "
            "duration-proportional extrapolation is an inference",
        ],
        "migrated_contracts": [
            "batch 36: the zoom endpoint moved from 2.5 to 100 with the new 0-100 range",
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
        f"Batch 594 verification: {len(checks) - len(failed)}/{len(checks)} checks passed"
    )
    if failed:
        raise SystemExit(
            "FAILED: " + json.dumps(failed, ensure_ascii=False, indent=2)
        )


if __name__ == "__main__":
    main()
