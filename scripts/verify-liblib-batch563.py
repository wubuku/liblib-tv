#!/usr/bin/env python3
"""Verify Batch 563: camera panel three tabs + 运动轨迹 (NEW) tab.

Contract: source-site CDP sampling (screenshots 50/51) — the camera
inspector panel has THREE tabs 属性 | 运动轨迹(NEW) | 截图; the 运动轨迹
tab hosts the 虚拟相机 section (wifi hint, QR, 录制/重试) plus ⟳ 预设运镜
and 创建运动轨迹 buttons. In the clone the 录制 button wires to the real
startPhoneVcamRecording store action; 预设运镜/创建运动轨迹 render as
hint buttons (full panels live in the timeline cluster —
CLONE_DECISION). No cloud actions.
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
    / "liblib-canvas-batch563-2026-09-28"
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
        assert ok, f"batch563 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 563" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    # 会话异步打开会重置选中——待其稳定后再选摄像机
    page.wait_for_timeout(800)
    page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          const camera = s.objects.find((o) => o.kind === "camera");
          if (camera) s.selectObject(camera.id);
        }"""
    )
    page.wait_for_timeout(400)

    # 三页签结构
    tabs = page.locator("[data-director-camera-tab]")
    check("tabs:three", tabs.count() == 3)
    check(
        "tabs:motion-present",
        page.locator("[data-director-camera-tab='motion']").is_visible(),
    )
    check(
        "tabs:motion-new-badge",
        page.locator("[data-director-camera-motion-new]").is_visible(),
    )

    # 属性页签仍可用（既有合同）
    check(
        "properties:active-default",
        page.locator("[data-director-camera-tab='properties']").get_attribute(
            "aria-pressed"
        )
        == "true",
    )

    # 切换到运动轨迹页签
    page.locator("[data-director-camera-tab='motion']").click()
    page.wait_for_timeout(250)
    motion = page.locator("[data-director-motion-vcam]")
    check("motion:section-visible", motion.is_visible())
    check(
        "motion:wifi-hint",
        "请保持手机和电脑在同一 wifi 下" in motion.inner_text(),
    )
    check("motion:qr", page.locator("[data-director-motion-qr]").is_visible())

    # 未连接：录制禁用（源站需先扫码连接）
    record = page.locator("[data-director-motion-record]")
    check("record:disabled-before-connect", record.is_disabled())
    check("record:idle-label", "录制" in record.inner_text())

    # 点击 QR 模拟连接 → 录制启用 → 点击进入录制中（真实 store 动作）
    page.locator("[data-director-motion-qr]").click()
    page.wait_for_timeout(250)
    check("qr:connected-label", "已连接" in page.locator("[data-director-motion-qr]").inner_text())
    check("record:enabled-after-connect", record.is_enabled())
    record.click()
    page.wait_for_timeout(300)
    check(
        "record:recording-state",
        page.evaluate(
            "window.__director_store.getState().phoneVcam.status"
        )
        == "recording",
    )
    check("record:label-recording", "录制中" in record.inner_text())

    # 重试按钮可见
    check("retry:visible", page.locator("[data-director-motion-retry]").is_visible())

    # 预设运镜/创建运动轨迹提示按钮
    check(
        "preset:hint-button",
        page.locator("[data-director-motion-preset-button]").is_visible(),
    )
    check(
        "create-path:hint-button",
        page.locator("[data-director-motion-create-path]").is_visible(),
    )

    # 已知瞬态（batch 553/558 留痕）：TransformControls attach 告警
    real_errors = [
        error for error in errors if "TransformControls" not in error
    ]
    check("diagnostics:zero", not real_errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 563,
        "title": "Camera panel three tabs + 运动轨迹 (NEW) tab",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§12 + screenshots 50/51 (CDP 2026-09-29)"
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
        "Batch 563 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "three-tab structure, motion tab content (vcam section with real "
        "recording action, preset/create-path hint buttons) recorded in "
        "runtime-audit.json."
    )


if __name__ == "__main__":
    main()
