#!/usr/bin/env python3
"""Batch 368 探针: 把 359/360 的**运行时**扫描器打到 367 刚走通的那些面上。

## 为什么源码普查不够, 非得再扫一遍运行时

batch 367 的普查读源码 `<button>` 标签, 抓到 7 处死控件并修好。但源码判据有
三个它看不见的洞:

1. **handler 可能在运行时被摘掉** —— 比如 `disabled` / 条件渲染 / 事件被
   `stopPropagation` 吞掉, 源码里 `onClick` 明明在。
2. **静默丢弃输入** —— `<textarea>` / `contenteditable` 有 `value`、能聚焦、
   能打字, 但没有 `onChange`/`onInput`, 打进去的字直接消失。**源码扫不出来**,
   因为 `value` 往往来自受控 state, 标签上有 handler 也可能只绑了一半。
3. **交互谎言** —— 声明了 `data-inert` 却还留着 `hover:` 变色。
   **这一条正是拿来反查 batch 367 自己的**: 我刚给 7 个控件加了 `data-inert`,
   漏掉一个 `hover:` 就是「声明了惰性但还在骗人」。

## 复用而不重写

- `SCAN_JS` / `classify` / `close_all` 直接 import `probe_liblib_batch359_node_surfaces`,
  判据不维护第二份实现(366 那条「过滤器必须双向验证」同理)。
- 导航直接复用 `probe_liblib_batch367_reachability.PROBES` —— 那些路径是踩了
  **8 处不同的坑**才走通的(派生自 `activeTool`、hover 菜单、视口外的节点、
  variant 分支……), 重新推导一遍只会再踩一遍。

## 门禁无法承载的部分

探针只报候选: 打不开的面报「跳过」而不是「0 问题」(360 立的规矩)。
另外 `data-storyboard-*` 编辑器面在 367 里已经能走到, 这里一并扫。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from playwright.sync_api import Page, sync_playwright  # noqa: E402

import probe_liblib_batch367_reachability as REACH  # noqa: E402
from probe_liblib_batch359_node_surfaces import (  # noqa: E402
    SCAN_JS,
    classify,
    close_all,
)

URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
OUT = ROOT / "docs" / "research" / "liblib-batch368-2026-10-02" / "runtime-panel-census.json"
VIEWPORT = REACH.VIEWPORT

SKIPPED = REACH.SKIPPED
ERROR = REACH.ERROR

# 复用 367 的导航。键是探针名, 值是要额外说明这个面「为什么值得扫」。
PANELS: dict[str, str] = {
    "image-edit/expand-panorama": "PanoramaEditPanel —— 367 修过「展开全景编辑器」",
    "segment-reshoot/translate-prompt": "SegmentReshootPanel —— 367 修过「翻译片段重拍提示词」",
    "subtitle-erase/help (误报嫌疑)": "SubtitleErasePanel —— 有 textarea? 有 hover 浮层",
    "storyboard-assets/add": "StoryboardScriptEditor 资产步 —— 367 修过「新增资产」",
    "video-gen/favorite": "VideoGenerationPanel 特效库 —— 367 修过 4 个「收藏」",
    "video-gen/banner-close": "VideoGenerationPanel 标记选择横幅 —— 367 修过「关闭」",
    "video-toolbar/undo-redo": "VideoProcessingToolbar —— 367 修过撤销/重做",
    "shot-breakdown/play-bgm": "ShotBreakdownResultNode 音乐卡 —— 367 修过「播放 BGM」",
}

# 上下文菜单是 365 修过的面, 源码普查没覆盖到(它不是面板, 是 portal)
EXTRA_PANELS: dict[str, str] = {
    "context-menu": "CanvasContextMenu —— 365 修过右键菜单, 从没被运行时扫过",
}


def open_context_menu(page: Page) -> dict[str, object]:
    """右键画布空白 -> 365 的菜单。"""
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(2000)
    pane = page.locator(".react-flow__pane")
    if pane.count() == 0:
        return {SKIPPED: "找不到画布空白区, 未测"}
    box = pane.first.bounding_box()
    if box is None:
        return {SKIPPED: "画布空白区无几何, 未测"}
    # 找一个真正空着的落点: 反复右击, 直到菜单真的出现
    for fx, fy in ((0.5, 0.35), (0.3, 0.6), (0.7, 0.7)):
        page.mouse.click(box["x"] + box["width"] * fx, box["y"] + box["height"] * fy, button="right")
        page.wait_for_timeout(500)
        if page.locator("[data-canvas-context-menu], [role='menu']").count() > 0:
            return {}
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
    return {SKIPPED: "右键后没找到上下文菜单, 未测"}


def main() -> int:
    report: dict[str, object] = {"url": URL, "viewport": VIEWPORT, "panels": {}}
    totals = {"deadControls": 0, "silentDiscard": 0, "lyingAffordance": 0}
    skipped: list[str] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport=VIEWPORT)
        page.on("pageerror", lambda e: report.setdefault("pageerrors", []).append(str(e)))

        for name, why in PANELS.items():
            try:
                REACH.PROBES[name](page)
                snap = page.evaluate(SCAN_JS)
                entry = classify(snap)
                entry["why"] = why
                entry["probe"] = name
            except Exception as exc:  # noqa: BLE001
                entry = {ERROR: f"{type(exc).__name__}: {exc}"}
            report["panels"][name] = entry
            for key in totals:
                n = len(entry.get(key, []) or [])
                totals[key] += n
            if ERROR in entry or SKIPPED in entry:
                skipped.append(name)
            print(f"── {name}: {entry.get('controls')} 控件 / {entry.get('inputs')} 输入")
            for key in ("deadControls", "silentDiscard", "lyingAffordance"):
                items = entry.get(key) or []
                if items:
                    print(f"   {key}: {json.dumps(items, ensure_ascii=False)[:400]}")

        for name, why in EXTRA_PANELS.items():
            close_all(page)
            gate = open_context_menu(page)
            if SKIPPED in gate or ERROR in gate:
                report["panels"][name] = gate
                skipped.append(name)
                print(f"── {name}: {gate}")
                continue
            entry = classify(page.evaluate(SCAN_JS))
            entry["why"] = why
            entry["probe"] = name
            report["panels"][name] = entry
            for key in totals:
                totals[key] += len(entry.get(key, []) or [])
            print(f"── {name}: {entry.get('controls')} 控件 / {entry.get('inputs')} 输入")
            for key in ("deadControls", "silentDiscard", "lyingAffordance"):
                items = entry.get(key) or []
                if items:
                    print(f"   {key}: {json.dumps(items, ensure_ascii=False)[:400]}")

        browser.close()

    report["summary"] = {
        "panelsScanned": len(PANELS) + len(EXTRA_PANELS),
        "skipped": skipped,
        "totals": totals,
        "note": "打不开的面报跳过, 不报「0 问题」; 候选是否真的骗人仍需人工定性",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n合计 死控件 {totals['deadControls']} | 静默丢弃 {totals['silentDiscard']} "
          f"| 交互谎言 {totals['lyingAffordance']} | 跳过 {len(skipped)}")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
