#!/usr/bin/env python3
"""Verify Batch 535: director desk scene prompt bar.

Contract: source-site live sampling 2026-09-25 round 2
(docs/research/liblib-source-exploration-2026-09-25/NOTES.md §8 + screenshot
18-director-console-opened.png) — the 3D director desk viewport has a
bottom-center pill bar: a mode segment with three toggles (光标/相机/手),
a「+ 描述想要搭建的场景」input and a circular ↑ submit. Real scene building
is a cloud AI action: the clone keeps the input draft and mode selection
locally and the submit only flashes a local-draft confirmation (no
generation, no network).
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
    / "liblib-canvas-batch535-2026-09-27"
    / "runtime-audit.json"
)


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

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch535 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store)"""
    )

    # 建导演台节点并打开导演台（batch 70 路径）
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 535" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(400)

    bar = page.locator("[data-director-scene-prompt-bar]")
    check("bar:visible", bar.is_visible())
    check(
        "bar:placeholder",
        bar.locator("[data-director-scene-prompt-input]").get_attribute("placeholder")
        == "描述想要搭建的场景",
    )

    # 模式三态切换
    for mode_id in ["cursor", "camera", "hand"]:
        bar.locator(f"[data-director-scene-mode='{mode_id}']").click()
        page.wait_for_timeout(100)
        check(
            f"mode:active:{mode_id}",
            bar.locator(f"[data-director-scene-mode='{mode_id}']").get_attribute("aria-pressed") == "true",
        )

    # 输入草稿 + 提交 → 本地确认回显（无网络动作）
    prompt_input = bar.locator("[data-director-scene-prompt-input]")
    prompt_input.fill("一间咖啡馆，窗边两张桌子")
    bar.locator("[data-director-scene-prompt-submit]").click()
    page.wait_for_timeout(200)
    status = bar.locator("[data-director-scene-prompt-status]")
    check("submit:local-ack", "本地草稿" in status.inner_text())
    check("submit:draft-kept", prompt_input.input_value() == "一间咖啡馆，窗边两张桌子")

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 535,
        "title": "Director desk scene prompt bar",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§8 + screenshot 18-director-console-opened.png"
        ),
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
        "Batch 535 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "scene prompt bar with 光标/相机/手 mode toggles, draft input and "
        "local-only submit confirmation recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
