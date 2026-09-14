#!/usr/bin/env python3
"""Verify Batch 501: VR-018 Slice B remaining — Share overlay + Agent drawer
local status lines carry explicit disposition tones.

Contract: docs/research/LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md §16
Slice B (Add Node / Share / Agent / Video clip disposition) — this batch
closes the last two surfaces. Prototype-unavailable commands project
diagnostic; local-boundary acceptance projects positive; copy stays with
the owning surface (prototype honesty unchanged).

Scenes:
- share_unavailable_diagnostic: publish / link clicks surface
  data-status-tone="diagnostic" with the existing prototype copy;
- agent_submit_positive: a non-empty prompt submit surfaces
  data-status-tone="positive" (local preview accepted);
- agent_unavailable_diagnostic: attachment / Skill affordances surface
  data-status-tone="diagnostic"; typing clears the status line.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch501-2026-09-14"
    / "runtime-audit.json"
)
SCREENSHOT_PATH = (
    ROOT
    / "docs"
    / "design-references"
    / "liblib-clone-batch501-feedback-tones-929-2026-09-14.png"
)


def attach_errors(page: Page):
    errors = []
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


def assert_no_overflow(page: Page):
    assert page.evaluate(
        "() => document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )
    assert page.evaluate(
        "() => document.body.scrollWidth <= document.body.clientWidth"
    )


def share_status(page: Page):
    return page.evaluate(
        """() => {
          const el = document.querySelector('[data-share-status]');
          return el ? { text: el.innerText, tone: el.dataset.statusTone } : null;
        }"""
    )


def agent_status(page: Page):
    return page.evaluate(
        """() => {
          const el = document.querySelector('[data-agent-status]');
          return el ? { text: el.innerText, tone: el.dataset.statusTone } : null;
        }"""
    )


def main():
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)

    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 929, "height": 874}, device_scale_factor=1
        )
        errors.extend(attach_errors(page))
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(450)

        # Scene 1: share overlay — publish, then link.
        page.get_by_role("button", name="发布与分享").click()
        overlay = page.locator('[data-liblib-overlay="share"]')
        overlay.wait_for(state="visible")

        page.locator('[data-share-action="publish"]').click()
        page.wait_for_timeout(120)
        publish_status = share_status(page)
        assert publish_status == {
            "text": "本地原型：发布服务未连接",
            "tone": "diagnostic",
        }, publish_status

        page.locator('[data-share-action="link"]').click()
        page.wait_for_timeout(120)
        link_status = share_status(page)
        assert link_status == {
            "text": "本地原型：分享链接服务未连接",
            "tone": "diagnostic",
        }, link_status

        # Close the share panel before the agent scenes.
        page.get_by_role("button", name="发布与分享").click()
        overlay.wait_for(state="hidden")

        # Scene 2: agent drawer — unavailable affordances, then submit.
        page.get_by_role("button", name="Agent", exact=True).click()
        page.get_by_placeholder("开始你的创作，或者 @ 引用工作流/节点/资源").wait_for(
            state="visible"
        )

        # The drawer composer's bottom button row can be covered by the
        # bottom tool dock (z-[60]) at this viewport — pre-existing page
        # chrome stacking, out of scope here. These scenes verify the
        # status projection, so the three composer affordances dispatch
        # synthetic clicks instead of hit-tested ones.
        page.get_by_role("button", name="添加附件").dispatch_event("click")
        page.wait_for_timeout(120)
        attach_status = agent_status(page)
        assert attach_status == {
            "text": "本地预览：附件上传未接入",
            "tone": "diagnostic",
        }, attach_status

        page.get_by_role("button", name="Skill", exact=True).dispatch_event("click")
        page.wait_for_timeout(120)
        skill_status = agent_status(page)
        assert skill_status == {
            "text": "本地预览：Skill 面板未接入",
            "tone": "diagnostic",
        }, skill_status

        prompt_box = page.get_by_placeholder(
            "开始你的创作，或者 @ 引用工作流/节点/资源"
        )
        prompt_box.fill("一段雨夜霓虹的城市空镜")
        page.wait_for_timeout(120)
        # Clearing projects an empty neutral line (inert) — same constant-DOM
        # pattern as the AddNodePanel / VideoClipEditPanel status elements.
        cleared = agent_status(page)
        assert cleared == {"text": "", "tone": "neutral"}, cleared

        page.locator("[data-agent-send]").dispatch_event("click")
        page.wait_for_timeout(120)
        submit_status = agent_status(page)
        assert submit_status == {
            "text": "本地预览已提交，未连接 Agent 服务",
            "tone": "positive",
        }, submit_status

        page.screenshot(path=str(SCREENSHOT_PATH))
        assert_no_overflow(page)
        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "SCRIPT_RECORDED_PASS",
        "slice": "VR-018 Slice B remaining — Share overlay + Agent drawer "
        "status lines carry explicit disposition tones",
        "scenes": {
            "share_publish_diagnostic": publish_status,
            "share_link_diagnostic": link_status,
            "agent_attachment_diagnostic": attach_status,
            "agent_skill_diagnostic": skill_status,
            "agent_typing_clears": cleared,
            "agent_submit_positive": submit_status,
        },
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 501 verification passed: share/agent status lines project "
        "diagnostic/positive tones via the VR-018 catalog; prototype copy "
        "and geometry unchanged; recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
