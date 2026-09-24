#!/usr/bin/env python3

"""Verify Batch 223: FrameOS 本地上传 real wiring.

Source sampling 2026-09-25 (probe wav upload): the rail's 本地上传 routes by
MIME to content-bearing nodes and titles them by filename (extension
stripped). The stale clone created EMPTY image/video nodes and ignored audio.

Checks (real test media from ~/Downloads, user-authorized):
1. upload PNG via filechooser → new image node titled 生成蓝色手机图片-2 with
   a blob: cover and the floating title showing the filename;
2. upload WAV → new audio node with the player row (Batch 222 form);
3. multi-file upload (PNG + WAV in one chooser) → two new nodes with
   distinct ids;
4. errors clean.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
PNG_PATH = os.path.expanduser("~/Downloads/生成蓝色手机图片-2.png")
WAV_PATH = os.path.expanduser("~/Downloads/voice_converted_1779790519790.wav")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-frameos-batch223-2026-09-25"
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


def upload(page: Page, paths: list[str]) -> None:
    with page.expect_file_chooser() as fc_info:
        page.locator("button[aria-label='本地上传']").click()
    fc_info.value.set_files(paths)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch223 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)
    nodes_before = page.evaluate(
        "window.__frameos_store.getState().nodes.length"
    )

    # 1) PNG → 内容图片节点, 标题 = 文件名去扩展名
    upload(page, [PNG_PATH])
    page.wait_for_timeout(900)
    state = page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          const last = s.nodes[s.nodes.length - 1];
          return { count: s.nodes.length, type: last.type, title: last.data.title,
                   imageUrl: (last.data.imageUrl || '').slice(0, 5), selected: s.selectedNodeId === last.id };
        })()"""
    )
    check("png:node-created", state["count"] == nodes_before + 1)
    check("png:type-image", state["type"] == "image")
    check("png:title-from-filename", state["title"] == "生成蓝色手机图片-2")
    check("png:blob-cover", state["imageUrl"] == "blob:")
    check("png:selected", state["selected"] is True)
    title_el = page.locator(
        ".react-flow__node-image .node-floating-title__name"
    ).last
    check(
        "png:floating-title",
        "生成蓝色手机图片-2" in (title_el.inner_text() or ""),
    )

    # 2) WAV → 内容音频节点 (Batch 222 播放器形态)
    count_after_png = state["count"]
    upload(page, [WAV_PATH])
    page.wait_for_timeout(900)
    state2 = page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          const last = s.nodes[s.nodes.length - 1];
          return { count: s.nodes.length, type: last.type, title: last.data.title,
                   audioUrl: (last.data.audioUrl || '').slice(0, 5) };
        })()"""
    )
    check("wav:node-created", state2["count"] == count_after_png + 1)
    check("wav:type-audio", state2["type"] == "audio")
    check(
        "wav:title-from-filename",
        state2["title"] == "voice_converted_1779790519790",
    )
    check("wav:blob-audio", state2["audioUrl"] == "blob:")
    audio_node = page.locator(".react-flow__node-audio").last
    check("wav:player-rendered", audio_node.locator("[data-frameos-audio-player]").count() == 1)

    # 3) 一次多文件 → 各建节点, id 唯一
    count_after_wav = state2["count"]
    upload(page, [PNG_PATH, WAV_PATH])
    page.wait_for_timeout(1200)
    state3 = page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          const ids = s.nodes.map((n) => n.id);
          return { count: s.nodes.length, unique: new Set(ids).size === ids.length };
        })()"""
    )
    check("multi:two-created", state3["count"] == count_after_wav + 2)
    check("multi:ids-unique", state3["unique"] is True)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 223, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch223: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
