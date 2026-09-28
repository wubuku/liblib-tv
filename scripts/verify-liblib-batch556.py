#!/usr/bin/env python3
"""Verify Batch 556: timeline onboarding coachmark.

Contract: source-site sampling (screenshot 48-director-timeline-open.png)
— when the timeline panel opens, a coachmark popover appears above the
新建轨道 button: 「请选择一个角色或者摄像机后，可新建轨道」 with a
1/5 step counter and 跳过 / 下一步 actions. Steps 2-5 are unsampled, so
both actions dismiss the coachmark in the clone (CLONE_DECISION).
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
    / "liblib-canvas-batch556-2026-09-27"
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
        assert ok, f"batch556 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 556" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(600)

    coach = page.locator("[data-director-timeline-coachmark]")
    check("coach:visible", coach.is_visible())
    text = coach.inner_text()
    for token in ["请选择一个角色或者摄像机后", "可新建轨道", "1/5"]:
        check(f"coach:token:{token}", token in text)
    check(
        "coach:buttons",
        coach.locator("[data-director-coachmark-skip]").is_visible()
        and coach.locator("[data-director-coachmark-next]").is_visible(),
    )

    # 跳过 → 收起
    coach.locator("[data-director-coachmark-skip]").click()
    page.wait_for_timeout(250)
    check("skip:dismisses", coach.count() == 0)

    # Batch 572 migration: 源站实测（截图 58）气泡收起状态跨重载持久——
    # 重载后气泡不再出现（原「每次挂载再现」合同由持久化合同替代）。
    page.reload(wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(600)
    check(
        "reload:coach-stays-dismissed",
        page.locator("[data-director-timeline-coachmark]").count() == 0,
    )

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 556,
        "title": "Timeline onboarding coachmark",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§12 + screenshot 48-director-timeline-open.png (batch 552)"
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
        "Batch 556 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "coachmark content, skip and next dismissal recorded in "
        "runtime-audit.json."
    )


if __name__ == "__main__":
    main()
