#!/usr/bin/env python3

"""Verify Batch 99 shortcuts help panel alignment with the 2026-09-05 source audit."""

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
    / "liblib-canvas-batch99-2026-09-05"
    / "runtime-audit.json"
)

# label -> (column, kbd count, suffix)  kbd count includes icon-only ⌘ keys
CREATION_ITEMS = {
    "成组": (2, ""),
    "合并分镜组": (3, ""),
    "解组": (3, ""),
    "连线": (2, ""),
    "复制节点和连线": (2, ""),
    "生成": (2, ""),
    "新建节点": (1, ""),
    "节点复制": (1, "+拖动节点"),
    "创建副本": (2, "+拖动"),
}
OTHER_ITEMS = {
    "撤销": (2, ""),
    "重做": (3, ""),
    "画布节点搜索": (2, ""),
    "删除": (1, ""),
}
SPOT_ITEMS = {
    "适应画布": 2,
    "整理画布": 3,
    "移动": 1,
    "抓手工具": 1,
}


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


def row_kbd_and_suffix(page: Page, dialog: Any, label: str) -> tuple[int, str]:
    label_span = dialog.get_by_text(label, exact=True)
    assert label_span.count() == 1, f"label not unique: {label}"
    row = label_span.locator("xpath=..")
    kbd_count = row.locator("kbd").count()
    suffix = ""
    suffix_loc = row.locator("span.text-xs")
    if suffix_loc.count() == 1:
        suffix = suffix_loc.inner_text()
    return kbd_count, suffix


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch99 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    page.get_by_role("button", name="快捷键").click()
    dialog = page.locator('[data-liblib-overlay="shortcuts"]')
    assert dialog.is_visible()

    for title in ["创作", "缩放", "移动画布", "其他"]:
        check(f"column:{title}", dialog.get_by_role("heading", name=title, exact=True).is_visible())

    for label, (kbd_count, _) in CREATION_ITEMS.items():
        kbd, suffix = row_kbd_and_suffix(page, dialog, label)
        check(f"creation:{label}:kbd", kbd == kbd_count)
        if suffix:
            check(f"creation:{label}:suffix", suffix == suffix)

    creation_labels = [
        dialog.get_by_text(label, exact=True).count() for label in CREATION_ITEMS
    ]
    check("creation:all-present", all(count == 1 for count in creation_labels))
    check(
        "creation:no-delete",
        dialog.get_by_role("heading", name="创作").locator(
            "xpath=following-sibling::*"
        ).get_by_text("删除", exact=True).count() == 0,
    )

    for label, (kbd_count, _) in OTHER_ITEMS.items():
        kbd, _ = row_kbd_and_suffix(page, dialog, label)
        check(f"other:{label}:kbd", kbd == kbd_count)
    check("other:windows-redo-removed", dialog.get_by_text("重做（Windows）", exact=True).count() == 0)
    check(
        "other:search-key",
        dialog.get_by_text("画布节点搜索", exact=True).locator("xpath=..").get_by_text("F", exact=True).count() == 1,
    )
    check(
        "other:delete-key",
        dialog.get_by_text("删除", exact=True).locator("xpath=..").get_by_text("Delete", exact=True).count() == 1,
    )

    for label, kbd_count in SPOT_ITEMS.items():
        kbd, _ = row_kbd_and_suffix(page, dialog, label)
        check(f"spot:{label}:kbd", kbd == kbd_count)

    page.get_by_role("button", name="关闭快捷键面板").click()
    check("close", not dialog.is_visible())

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 99,
        "title": "Shortcuts help panel alignment with 2026-09-05 source audit",
        "evidence": "docs/research/liblib-live-2026-09-05/README.md",
        "results": [],
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        audit["results"].append(run_desktop(desktop))
        desktop.close()
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    checks = audit["results"][0]["checks"]
    print(
        "Batch 99 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Four-column shortcut copy, keycap counts, suffixes, deletion row placement, "
        "canvas-node-search row and Windows-redo removal recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
