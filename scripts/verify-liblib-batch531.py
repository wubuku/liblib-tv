#!/usr/bin/env python3
"""Verify Batch 531: self-write storyboard script editor overlay.

Contract: source-site CDP sampling 2026-09-27
(docs/research/liblib-source-exploration-2026-09-25/NOTES.md §11 update +
screenshot 38-script-selfwrite-clicked.png) — clicking 自己编写分镜脚本 on
the script generator opens a full-screen storyboard editor: a 3-step
stepper (确认镜头/准备资产/合成提示词 with 1个镜头待核对/暂无资产/0/1 已合成),
top-right 0/3 完成后可批量生成视频 + close, a 10-column shot table
(镜号/时长/画面描述/景别/光影氛围/对白/旁白/音效/运镜/最终提示词/操作) whose
first row is 1|5s with + placeholders and 待生成提示词, footer 添加镜头 and
→ 下一步：准备资产.

This corrects the batch-528 round-8 reading ("未展开子流程"): the two
generate entries still drive the follow banner, but the self-write entry
opens this editor as a blocking foreground surface (ESC closes it).
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
    / "liblib-canvas-batch531-2026-09-27"
    / "runtime-audit.json"
)

SELF_WRITE = "自己编写分镜脚本"
GEN_ENTRY = "剧本生成分镜脚本"


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


def add_script_generator(page: Page) -> Any:
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(400)
    panel = page.locator('[data-liblib-overlay="add-node"]')
    panel.locator("[data-add-node-entry='script']").click()
    page.wait_for_timeout(300)
    panel.locator("[data-add-node-entry='script-new']").click()
    page.wait_for_timeout(700)
    return page.locator(".react-flow__node-script-generator").first


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch531 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    # —— 生成入口保持 batch 528 跟随合同 ——
    node = add_script_generator(page)
    entry = node.locator(f"[data-script-generator-attempt='{GEN_ENTRY}']")
    entry.click()
    page.wait_for_timeout(250)
    banner = page.locator("[data-follow-banner]")
    check("gen-entry:follow-banner", banner.get_attribute("aria-hidden") == "false")
    check("gen-entry:no-editor", page.locator("[data-storyboard-editor]").count() == 0)
    banner.locator("[data-follow-cancel]").click()
    page.wait_for_timeout(200)

    # —— 自写入口打开全屏编辑器 ——
    self_write = node.locator(f"[data-script-generator-attempt='{SELF_WRITE}']")
    self_write.click()
    page.wait_for_timeout(300)
    editor = page.locator("[data-storyboard-editor]")
    check("editor:opens", editor.is_visible())
    check("editor:no-follow", banner.get_attribute("aria-hidden") == "true")
    text = editor.inner_text()
    for token in ["确认镜头", "准备资产", "合成提示词", "1个镜头待核对", "暂无资产",
                  "0/1 已合成", "0/3 完成后可批量生成视频", "镜号", "时长", "画面描述",
                  "景别", "光影氛围", "对白/旁白", "音效", "运镜", "最终提示词", "操作",
                  "待生成提示词", "添加镜头", "下一步：准备资产"]:
        check(f"editor:token:{token}", token in text)
    check("editor:first-row", editor.locator("[data-storyboard-row='1']").count() == 1)

    # 单元格点击可编辑（本地草稿）
    cell = editor.locator("[data-storyboard-row='1']").locator("[data-storyboard-cell]").first
    cell.click()
    page.wait_for_timeout(150)
    editor.locator("[data-storyboard-cell-input]").fill("咖啡馆对峙，陈默推门而入")
    editor.locator("[data-storyboard-cell-input]").press("Enter")
    page.wait_for_timeout(150)
    check(
        "cell:edit-commits",
        "咖啡馆对峙" in editor.locator("[data-storyboard-row='1']").inner_text(),
    )

    # 添加镜头 → 镜号 2
    editor.locator("[data-storyboard-add-shot]").click()
    page.wait_for_timeout(200)
    check("add-shot:row2", editor.locator("[data-storyboard-row='2']").count() == 1)
    check("add-shot:counter", "0/2 已合成" in editor.inner_text())

    # ESC 经 storyboard-editor 阻塞面关闭（全屏遮罩下画布 pane 不可点）
    page.locator("[data-storyboard-editor]").click(position={"x": 700, "y": 300})
    page.keyboard.press("Escape")
    page.wait_for_timeout(250)
    check("escape:closes", page.locator("[data-storyboard-editor]").count() == 0)

    # ✕ 按钮亦可关闭（重开验证；batch 534 后节点已转进度卡，
    # 按源站流程以「打开脚本节点 →」重入）
    node.locator("[data-script-generator-open-storyboard]").click()
    page.wait_for_timeout(250)
    editor = page.locator("[data-storyboard-editor]")
    editor.locator("[data-storyboard-close]").click()
    page.wait_for_timeout(250)
    check("close-button:closes", page.locator("[data-storyboard-editor]").count() == 0)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 531,
        "title": "Self-write storyboard script editor overlay",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md §11 "
            "update + screenshot 38-script-selfwrite-clicked.png (CDP 2026-09-27)"
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
        "Batch 531 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "self-write entry opens the full-screen storyboard editor (stepper, "
        "10-column table, add-shot, ESC/close) while generate entries keep "
        "the batch-528 follow contract, recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
