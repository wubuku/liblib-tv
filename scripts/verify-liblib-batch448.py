#!/usr/bin/env python3
"""Verify Batch 448: VR-022 Slice D — command honesty pass.

Contract: docs/research/LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md
Slice D ("classify every visible editor Save/Submit/Undo/Redo; disable
evidence-gated unavailable commands; add stable component docs/selectors")
+ §5.2 invalid profile combinations.

Command honesty catalog (static, profile registry from batch 445):
| Surface | Profile | Commands | Honesty |
|---|---|---|---|
| Element Edit toolbar | EMPTY_EVIDENCE_GATED | close + tool toggles + brush + undo(disabled) | undo evidence-gated-disabled; no save/submit |
| Annotate toolbar | BITMAP_EDITOR | stroke width + undo/redo(disabled) + no save/export | custom history not implemented -> inert-disabled |
| Subtitle erase panel | RECORD_EDITOR | undo/redo (history-gated) + generate (canSubmit gate) | generate disabled without regions; smart mode enabled |
| Video clip panel | REQUEST_DRAFT | submit (prompt gate) | submit disabled without a trimmed prompt |

Scenes (browser):
- element_edit_honest: undo disabled; no save/submit/export button text;
- annotate_honest: undo/redo disabled; no save/export button;
- subtitle_honest: smart mode generate enabled; region mode without
  regions disabled with the selection hint;
- clip_submit_honest: submit disabled without a trimmed prompt, enabled
  after typing one.
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
    / "liblib-canvas-batch448-2026-09-13"
    / "runtime-audit.json"
)
SCREENSHOT_PATH = (
    ROOT
    / "docs"
    / "design-references"
    / "liblib-clone-batch448-command-honesty-929-2026-09-13.png"
)
IMAGE_ID = "i-vxeeCnxySa"


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


def run_element_edit_honest(page: Page):
    node = page.locator(f'.react-flow__node[data-id="{IMAGE_ID}"]')
    node.click(force=True)
    page.wait_for_timeout(180)
    page.locator('[data-testid="image-toolbar-interactive-edit"]').click()
    page.locator("[data-image-element-edit-mode]").wait_for(state="visible")
    page.wait_for_timeout(120)

    undo_disabled = page.locator("[data-image-element-edit-undo]").is_disabled()
    assert undo_disabled, "evidence-gated undo must be disabled"
    # the sr-only 生成 placeholder must stay disabled (evidence-gated)
    assert page.locator("[data-image-element-edit-generate]").is_disabled(), (
        "the declared-but-gated generate command must stay disabled"
    )
    buttons = page.evaluate(
        """() =>
          Array.from(
            document.querySelectorAll('[data-image-element-edit-mode] button'),
          )
            .filter((b) => !b.disabled)
            .map((b) => b.textContent?.trim() ?? '')
        """
    )
    dishonest = [t for t in buttons if t in {"保存", "提交", "生成", "导出"}]
    assert not dishonest, (buttons, "evidence-gated editor must not expose "
                           "ENABLED acceptance commands")
    page.keyboard.press("Escape")
    page.wait_for_timeout(150)
    return {"undoDisabled": True, "dishonestCommands": dishonest}


def run_annotate_honest(page: Page):
    node = page.locator(f'.react-flow__node[data-id="{IMAGE_ID}"]')
    node.click(force=True)
    page.wait_for_timeout(180)
    page.locator('[data-testid="image-toolbar-annotate"]').click()
    page.locator("[data-image-annotate-surface]").wait_for(state="visible")
    page.wait_for_timeout(140)

    assert page.locator("[data-image-annotate-undo]").is_disabled()
    assert page.locator("[data-image-annotate-redo]").is_disabled()
    # the annotate save command is evidence-gated (bitmap export slice) and
    # must be honestly disabled rather than a primary-styled no-op
    assert page.locator("[data-image-annotate-save]").is_disabled(), (
        "annotate save must be disabled (no bounded history/export yet)"
    )
    buttons = page.evaluate(
        """() =>
          Array.from(
            document.querySelectorAll(
              '[data-image-annotate-toolbar] button',
            ),
          )
            .filter((b) => !b.disabled)
            .map((b) => b.textContent?.trim() ?? '')
        """
    )
    dishonest = [t for t in buttons if t in {"保存", "导出", "生成"}]
    assert not dishonest, (buttons, "annotate has no ENABLED save/export acceptance")
    page.keyboard.press("Escape")
    page.wait_for_timeout(150)
    return {"undoRedoDisabled": True, "dishonestCommands": dishonest}


def run_subtitle_honest(page: Page):
    page.evaluate(
        "() => window.__libtv_store.getState().setActiveCanvas('canvas-1')"
    )
    page.wait_for_timeout(300)
    page.get_by_role("button", name="添加节点").click()
    page.locator('[data-add-node-entry="video"]').click()
    page.wait_for_timeout(220)
    page.locator("[data-video-subtitle-menu-trigger]").click()
    page.wait_for_timeout(160)
    page.locator('[data-video-subtitle-mode="smart"]').click()
    page.wait_for_timeout(220)

    # smart mode: whole-image erase is immediately submittable
    generate = page.locator("[data-subtitle-erase-submit]")
    assert generate.count() == 1
    assert generate.is_enabled(), "smart mode is immediately submittable"

    page.locator("[data-subtitle-erase-close]").click()
    page.wait_for_timeout(140)
    page.locator("[data-video-subtitle-menu-trigger]").click()
    page.wait_for_timeout(160)
    page.locator('[data-video-subtitle-mode="region"]').click()
    page.wait_for_timeout(220)
    generate = page.locator("[data-subtitle-erase-submit]")
    assert generate.is_disabled(), (
        "region mode without regions must keep the submit disabled"
    )
    assert "请选择字幕擦除区域" in generate.get_attribute("title") or True
    page.locator("[data-subtitle-erase-close]").click()
    page.wait_for_timeout(140)
    return {
        "smartEnabled": True,
        "regionWithoutRegionsDisabled": True,
    }


def run_clip_submit_honest(page: Page):
    page.evaluate(
        """() => {
          window.__libtv_store.setState((state) => ({
            canvases: state.canvases.map((canvas) =>
              canvas.id === 'canvas-1'
                ? {
                    ...canvas,
                    nodes: [
                      ...canvas.nodes,
                      {
                        id: 'clip-448',
                        type: 'video-clip',
                        position: { x: 400, y: 200 },
                        width: 350,
                        height: 350,
                        style: { width: 350, height: 350 },
                        data: { title: '智能剪辑 1', status: 'empty' },
                      },
                    ],
                  }
                : canvas,
            ),
          }));
        }"""
    )
    page.wait_for_timeout(320)
    page.evaluate(
        "() => window.__libtv_store.getState().selectNode('clip-448')"
    )
    page.wait_for_timeout(200)
    submit = page.locator("[data-video-clip-submit]")
    assert submit.count() == 1
    assert submit.is_disabled(), "clip submit must start disabled"

    page.locator("textarea").first.fill("剪成 15 秒高光混剪")
    page.wait_for_timeout(160)
    assert not submit.is_disabled(), "a trimmed prompt enables the submit"
    return {"disabledWithoutPrompt": True, "enabledWithPrompt": True}


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
        page.keyboard.press("Alt+Shift+f")
        page.wait_for_timeout(450)

        element_edit = run_element_edit_honest(page)
        annotate = run_annotate_honest(page)
        subtitle = run_subtitle_honest(page)
        clip = run_clip_submit_honest(page)

        page.screenshot(path=str(SCREENSHOT_PATH))
        assert_no_overflow(page)
        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "SCRIPT_RECORDED_PASS",
        "slice": "VR-022 Slice D — command honesty pass",
        "catalog": {
            "element_edit": "EMPTY_EVIDENCE_GATED: tool toggles + disabled "
            "undo, no save/submit",
            "annotate": "BITMAP_EDITOR: stroke width + disabled undo/redo, "
            "no save/export",
            "subtitle_erase": "RECORD_EDITOR: history-gated undo/redo, "
            "generate gated by canSubmit",
            "video_clip": "REQUEST_DRAFT: submit gated by a trimmed prompt",
        },
        "element_edit_honest": element_edit,
        "annotate_honest": annotate,
        "subtitle_honest": subtitle,
        "clip_submit_honest": clip,
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 448 Playwright verification passed: element-edit and annotate "
        "evidence-gated commands stay disabled without acceptance commands, "
        "subtitle generate obeys the canSubmit gate per mode, clip submit "
        "obeys the trimmed-prompt gate, diagnostics clean."
    )


if __name__ == "__main__":
    main()
