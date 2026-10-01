#!/usr/bin/env python3
"""Verify Batch 592: 时间线最小化/展开时间线 + 场景 prompt 文案逐字。

Source facts (live CDP sampling of the source director desk at 1920x1150):

时间线最小化 — measured before/after on the same page:

    expanded   timeline root 1920 x 182 @ (0, 968)
               toolbar row at y=1027, track rows at y=1055+
    collapsed  timeline root 1920 x  88 @ (0, 1062)
               toolbar row STILL PRESENT at y=1121
               播放 / 自动帧 / 循环播放 / 播放头位置 / 总时长 / ms /
               新建轨道 / 时间轴缩放 / 导出视频到画布 all survive
               only the track area goes away (轨道行 pushed past the fold)
               the button becomes `展开时间线` @ (1764, 1121), 24x24

So "minimize" collapses the track area and keeps the whole toolbar — and the
button's accessible name flips with the state.

The clone's timeline was a fixed 196px with no collapse affordance at all.

场景描述 prompt — the source's input zone is a contenteditable
(`role="textbox"`, `aria-multiline="true"`, 14px, 142x24) whose accessible
name is 描述想搭建的场景. The visible placeholder is the slightly different
描述您想搭建的场景. The submit button is 32x32, `border-radius: 9999px`, no
text, with `aria="发送"` and `title="发送"`; its empty-input background
`rgba(255,255,255,0.08)` matches the clone's existing disabled style.

The clone wrote 描述想要搭建的场景 (an extra 要) and labelled the submit button
提交场景描述 at 28px.

NOT verified (recorded, not fabricated): whether the source's Enter key
submits or inserts a newline in its contenteditable, and the source's
placeholder-vs-aria split mechanics. This batch keeps the clone's <input>
implementation and aligns the strings and geometry only.

Contract asserted here:
1. the timeline root is 182px expanded and 88px collapsed;
2. the collapse button's accessible name flips 时间线最小化 / 展开时间线;
3. collapsing hides the track area but keeps the whole toolbar (播放,
   播放头位置, 总时长, 时间轴缩放 all still visible);
4. expanding restores the track area;
5. the prompt input's placeholder and accessible name are 描述想搭建的场景;
6. the submit button is 发送 (aria + title) at 32px with a fully round shape;
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
    / "liblib-canvas-batch592-2026-10-01"
    / "runtime-audit.json"
)

TIMELINE_EXPANDED_PX = 182
TIMELINE_COLLAPSED_PX = 88
SURVIVES_COLLAPSE = [
    '[data-director-playback]',
    '[data-director-time-field="time"]',
    '[data-director-time-field="duration"]',
    '[data-director-time-unit]',
    '[data-director-add-track][aria-label]',
    '[data-director-timeline-zoom]',
]


def attach_errors(page: Page) -> list[str]:
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(f"console:{message.type}:{message.text}")
        if message.type == "error"
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
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool, detail: Any = None) -> None:
        assert ok, f"batch592 check failed: {name} :: {detail}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 592" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(600)

    timeline = page.locator("[data-director-timeline]")
    timeline.wait_for(state="visible")
    collapse = page.locator("[data-director-timeline-collapse]")

    # 1+2) expanded state
    expanded_box = timeline.bounding_box()
    result["expanded_box"] = expanded_box
    check(
        "timeline:expanded-182",
        abs(round(expanded_box["height"]) - TIMELINE_EXPANDED_PX) <= 1,
        detail=expanded_box,
    )
    check(
        "timeline:collapse-label",
        collapse.get_attribute("aria-label") == "时间线最小化",
        detail=collapse.get_attribute("aria-label"),
    )
    check(
        "timeline:collapse-pressed-false",
        collapse.get_attribute("aria-pressed") == "false",
    )
    check(
        "timeline:collapse-24x24",
        abs(round(collapse.bounding_box()["width"]) - 24) <= 1
        and abs(round(collapse.bounding_box()["height"]) - 24) <= 1,
        detail=collapse.bounding_box(),
    )
    check(
        "timeline:tracks-visible-when-expanded",
        page.locator("[data-director-timeline-canvas]").count() == 1,
    )

    # 3) collapse
    collapse.click()
    page.wait_for_timeout(250)
    collapsed_box = timeline.bounding_box()
    result["collapsed_box"] = collapsed_box
    check(
        "timeline:collapsed-88",
        abs(round(collapsed_box["height"]) - TIMELINE_COLLAPSED_PX) <= 1,
        detail=collapsed_box,
    )
    check(
        "timeline:tracks-hidden",
        page.locator("[data-director-timeline-canvas]").count() == 0,
    )
    check(
        "timeline:expand-label",
        collapse.get_attribute("aria-label") == "展开时间线",
        detail=collapse.get_attribute("aria-label"),
    )
    check(
        "timeline:expand-pressed-true",
        collapse.get_attribute("aria-pressed") == "true",
    )
    for selector in SURVIVES_COLLAPSE:
        check(
            f"collapsed:toolbar-keeps:{selector}",
            page.locator(selector).first.is_visible(),
        )

    # 4) expand again
    collapse.click()
    page.wait_for_timeout(250)
    check(
        "timeline:re-expanded-182",
        abs(round(timeline.bounding_box()["height"]) - TIMELINE_EXPANDED_PX) <= 1,
        detail=timeline.bounding_box(),
    )
    check(
        "timeline:tracks-back",
        page.locator("[data-director-timeline-canvas]").count() == 1,
    )
    check(
        "timeline:collapse-label-back",
        collapse.get_attribute("aria-label") == "时间线最小化",
    )

    # 5) prompt strings
    prompt = page.locator("[data-director-scene-prompt-input]")
    check("prompt:placeholder", prompt.get_attribute("placeholder") == "描述想搭建的场景",
          detail=prompt.get_attribute("placeholder"))
    check("prompt:aria", prompt.get_attribute("aria-label") == "描述想搭建的场景",
          detail=prompt.get_attribute("aria-label"))
    check("prompt:no-stale-yao", "描述想要搭建" not in (prompt.inner_text() or "")
          and prompt.get_attribute("placeholder") != "描述想要搭建的场景")

    # 6) submit button
    submit = page.locator("[data-director-scene-prompt-submit]")
    submit_box = submit.bounding_box()
    submit_style = submit.evaluate(
        """el => {
          const c = getComputedStyle(el);
          // rounded-full computes to a clamped 9999px on a 32px box, which
          // serialises in exponential form; parse it and compare numerically
          return {radius: parseFloat(c.borderTopLeftRadius)};
        }"""
    )
    result["submit"] = {"box": submit_box, **submit_style}
    check("submit:aria", submit.get_attribute("aria-label") == "发送",
          detail=submit.get_attribute("aria-label"))
    check("submit:title", submit.get_attribute("title") == "发送",
          detail=submit.get_attribute("title"))
    check(
        "submit:32px",
        abs(round(submit_box["width"]) - 32) <= 1 and abs(round(submit_box["height"]) - 32) <= 1,
        detail=submit_box,
    )
    check(
        "submit:fully-round",
        submit_style["radius"] >= 16,
        detail=submit_style["radius"],
    )
    # empty input keeps the source's rgba(255,255,255,0.08) look (clone's
    # existing disabled style)
    check("submit:disabled-when-empty", submit.is_disabled())

    unexpected = [error for error in errors if "TransformControls" not in error]
    result["diagnostics"] = {
        "console": len(errors),
        "filtered_transformcontrols": len(errors) - len(unexpected),
        "errors": unexpected[:5],
    }
    check("diagnostics:zero", not unexpected, detail=unexpected[:8])
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 592,
        "title": "时间线最小化/展开时间线（182→88px）+ 场景描述 prompt 文案与提交钮逐字对齐",
        "evidence": (
            "2026-10-01 live CDP before/after sampling of the source director "
            "desk at 1920x1150 + "
            "docs/research/liblib-canvas-batch592-2026-10-01/README.md"
        ),
        "migrated_assertions": [
            "verify-liblib-batch535.py: placeholder/aria 描述想要搭建的场景 -> "
            "描述想搭建的场景 (batch 592 DOM re-check showed the extra 要 was a "
            "screenshot-transcription slip)"
        ],
        "not_verified": [
            "the source prompt is a contenteditable; whether Enter submits or "
            "inserts a newline there was not observed, so the clone keeps its "
            "<input> and only the strings and geometry were aligned",
            "the source shows 描述您想搭建的场景 as the visible placeholder while "
            "its accessible name is 描述想搭建的场景; the clone aligns to the "
            "accessible name",
        ],
        "results": [],
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(
            viewport={"width": 1440, "height": 900}, device_scale_factor=1
        )
        audit["results"].append(run_desktop(desktop))
        desktop.close()
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    checks = audit["results"][0]["checks"]
    print(
        "Batch 592 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "时间线最小化 collapses the timeline 182px -> 88px while keeping the "
        "whole toolbar and flipping its own name to 展开时间线; the scene "
        "prompt strings and submit button now match the source verbatim. "
        "See runtime-audit.json."
    )


if __name__ == "__main__":
    main()
