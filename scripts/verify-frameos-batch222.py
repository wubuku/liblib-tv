#!/usr/bin/env python3

"""Verify Batch 222: FrameOS content-audio node rendering (plyr-form player).

Source sampling 2026-09-25 (uploaded a probe wav to frameos.cn canvas):
a content audio node renders an upper centered music icon + bottom player
row [play | current time | seek | duration] (source uses plyr), a top-right
替换内容 button, ONLY a right handle; selecting it shows a [下载, 收藏]
toolbar and NO prompt panel (empty audio nodes keep the Batch 213 panel).

Checks:
1. rail 音频 creates an empty audio node → prompt panel opens (regression);
2. store-injected audioUrl → player row appears with play button/time/seek;
3. 替换内容 button present; left handle gone, right handle kept;
4. selection → toolbar exactly [下载, 收藏]; prompt panel hidden;
5. errors clean.
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
    / "liblib-frameos-batch222-2026-09-25"
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


def open_add_menu(page: Page) -> None:
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    page.locator("button[aria-label='添加节点']").click()
    page.wait_for_timeout(300)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch222 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1200)

    # 1) 空音频节点: 创建 → 面板打开 (Batch 213 回归)
    open_add_menu(page)
    page.get_by_text("音频", exact=True).click()
    page.wait_for_timeout(500)
    empty_audio = page.locator(".react-flow__node-audio").last
    check("boot:audio-created", empty_audio.count() == 1)
    check(
        "empty:prompt-panel-opens",
        page.locator(".frameos-prompt-editor").is_visible(),
    )

    # 2) 注入 audioUrl (页内生成 0.6s wav data URI) → 内容态渲染
    inject_ok = page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          const audioNodes = s.nodes.filter((n) => n.type === 'audio');
          const target = audioNodes[audioNodes.length - 1];
          if (!target) return false;
          const sr = 8000, n = Math.floor(sr * 0.6);
          const buf = new ArrayBuffer(44 + n * 2);
          const dv = new DataView(buf);
          const w = (o, st) => { for (let i = 0; i < st.length; i++) dv.setUint8(o + i, st.charCodeAt(i)); };
          w(0, 'RIFF'); dv.setUint32(4, 36 + n * 2, true); w(8, 'WAVE');
          w(12, 'fmt '); dv.setUint32(16, 16, true); dv.setUint16(20, 1, true);
          dv.setUint16(22, 1, true); dv.setUint32(24, sr, true);
          dv.setUint32(28, sr * 2, true); dv.setUint16(32, 2, true); dv.setUint16(34, 16, true);
          w(36, 'data'); dv.setUint32(40, n * 2, true);
          for (let i = 0; i < n; i++) dv.setInt16(44 + i * 2, Math.sin(i / 20) * 8000, true);
          const bytes = new Uint8Array(buf);
          let bin = '';
          for (let i = 0; i < bytes.length; i += 4096) {
            bin += String.fromCharCode(...bytes.subarray(i, i + 4096));
          }
          s.updateNodeData(target.id, { audioUrl: 'data:audio/wav;base64,' + btoa(bin) });
          return true;
        })()"""
    )
    check("inject:audio-url-set", inject_ok is True)
    page.wait_for_timeout(600)

    node = page.locator(".react-flow__node-audio").last
    check("content:audio-wrap", node.locator(".audio-wrap").count() == 1)
    check("content:visual-icon", node.locator("[data-frameos-audio-visual]").count() == 1)
    player = node.locator("[data-frameos-audio-player]")
    check("content:player-row", player.count() == 1)
    check("content:play-button", node.locator("button[aria-label='播放']").count() == 1)
    check("content:current-time", node.locator("[data-frameos-audio-current]").count() == 1)
    check("content:duration-label", node.locator("[data-frameos-audio-duration]").count() == 1)
    check("content:seek-slider", player.locator("input[aria-label='进度']").count() == 1)
    check(
        "content:replace-button",
        node.locator("button[aria-label='替换内容']").count() == 1,
    )

    # 3) handle: 内容音频仅右 handle (源站实测)
    check("content:left-handle-gone", node.locator(".react-flow__handle-left").count() == 0)
    check("content:right-handle-kept", node.locator(".react-flow__handle-right").count() == 1)

    # 4) 选中 → 工具条恰好 [下载, 收藏]; 无面板
    node.click(position={"x": 40, "y": 50})
    page.wait_for_timeout(400)
    toolbar = page.locator(".frameos-floating-toolbar-new")
    check("selected:toolbar-opens", toolbar.is_visible())
    btns = toolbar.locator("button")
    check("selected:toolbar-two-buttons", btns.count() == 2)
    check("selected:download", btns.nth(0).get_attribute("aria-label") == "下载")
    check("selected:favorite", btns.nth(1).get_attribute("aria-label") == "收藏")
    check(
        "selected:no-prompt-panel",
        page.locator(".frameos-prompt-editor").count() == 0
        or not page.locator(".frameos-prompt-editor").first.is_visible(),
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 222, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch222: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
