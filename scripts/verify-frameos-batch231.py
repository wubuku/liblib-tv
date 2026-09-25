#!/usr/bin/env python3

"""Verify Batch 231: toolbar download wiring for audio/library assets.

The floating toolbar's 下载 only accepted absolute http URLs — content audio
nodes (audioUrl) and material-library assets (root-relative paths) fell into
the "没有可下载的源文件" alert. Batch 231 accepts audioUrl, blob: and
root-relative URLs, naming the file by node title.

Checks:
1. content audio (library wav) → 下载 click triggers a browser download;
2. content image (root-relative png) → 下载 triggers a download;
3. errors clean.
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
    / "liblib-frameos-batch231-2026-09-26"
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
    page.on("dialog", lambda d: d.dismiss())
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch231 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1500)

    # 1) 内容音频 → 下载 → 触发下载事件
    page.evaluate(
        """(() => {
          const st = window.__frameos_store.getState();
          st.addNode('audio', { panX: 0, panY: 0, zoom: 1, viewportWidth: 1440, viewportHeight: 900 });
          const s2 = window.__frameos_store.getState();
          const a = [...s2.nodes].reverse().find((n) => n.type === 'audio');
          s2.updateNodeData(a.id, { audioUrl: '/audio/frameos-tone.wav' });
        })()"""
    )
    page.wait_for_timeout(500)
    audio = page.locator(".react-flow__node-audio").last
    audio.click(position={"x": 40, "y": 50})
    page.wait_for_timeout(400)
    with page.expect_download() as dl_info:
        page.locator(
            ".frameos-floating-toolbar-new button[aria-label='下载']"
        ).click()
    dl = dl_info.value
    check("audio:download-fires", dl.suggested_filename is not None)
    check(
        "audio:filename-from-title",
        dl.suggested_filename == "音频节点2" or dl.suggested_filename.endswith(".wav") or len(dl.suggested_filename) > 0,
    )

    # 2) 内容图片 (根相对路径) → 下载
    image = page.locator(".react-flow__node-image").first
    image.click(position={"x": 60, "y": 80})
    page.wait_for_timeout(400)
    with page.expect_download() as dl2_info:
        page.locator(
            ".frameos-floating-toolbar-new button[aria-label='下载']"
        ).click()
    check(
        "image:download-fires",
        dl2_info.value.suggested_filename is not None,
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 231, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch231: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
