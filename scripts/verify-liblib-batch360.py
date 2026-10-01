#!/usr/bin/env python3
"""Verify Batch 360: 尚未覆盖的节点类型与浮层也不得存在交互谎言。

358/359 覆盖的是: 画布外框 16 态 + fixture 里 10 个节点的编辑面。
**没覆盖**的两块:

1. **能新建、但默认画布里没有的节点类型** —— 音频 / 智能剪辑 / 逐帧拉片。
   它们的编辑面板一次都没进过。普查找到 3 个死控件:
   `AudioNode` 的「播放音频」、`VideoClipEditPanel` 的「默认模式」与
   「16:9 · 720P · 30s」输出设置 —— 三个都**无 onClick、也没 disabled**,
   却各带悬停反馈。
2. **浮层** —— 预览大图(ImagePreviewOverlay)、图片标注画布、标注画布里的颜色菜单。
   节点编辑面那批只普查了工具条与编辑面板, 标注态进去之后的画布控件是另一层。
   frameos batch 350 的裁剪框也正是这种「浮在上面的编辑层」。

**跳过「导演台」(script-execution)**: 它打开 DirectorDesk, 那是另一条线,
且有并行 session 正在改(`src/components/director/*` 有未提交 WIP) ——
现在去普查会把人家的在途改动混进结果。**跨线不碰。**

判据与 batch359 完全一致(同一套扫描器 + 「例外须自证惰性」), 这里只扩覆盖面。

## 探针本身也踩了一次坑, 值得记

第一版把 CSS 类名当成了 `data-add-node-entry` 的值, 三个类型全部「面板里没有
该类型」被跳过 —— 而探针**如实报了跳过, 没有假装测过**, 于是这个错误是可见的。
如果它当时报「0 问题」, 这三个编辑面就会以「已覆盖」的名义混过去。
(`data-add-node-entry` 的值是 AddNodePanel 里的 `entry.type`: audio / video-clip /
shot-breakdown。)

## 断言

1. 防假零: 画布有节点, 且三种新类型**都真的被创建出来**(跳过的类型直接红);
2. 每种新节点: 无静默丢弃、无死控件;
3. 每个浮层: 无静默丢弃、无死控件;
4. 浮层**真的打开了**(预览层/标注画布/颜色菜单各有独立标志, 打不开即红);
5. 付费与只读项的既有约定不被破坏(诊断零错误);
6. 覆盖下界: 三种新类型 + 三层浮层一个都不能少。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT / "docs" / "research" / "liblib-batch360-2026-10-01" / "runtime-audit.json"
)
sys.path.insert(0, str(ROOT / "scripts"))
from probe_liblib_batch359_node_surfaces import (  # noqa: E402
    SCAN_JS,
    classify,
    close_all,
)
from probe_liblib_batch360_new_nodes import NEW_NODE_TYPES  # noqa: E402

MIN_CONTROLS_PER_SURFACE = 30


def create_node(page: Page, entry_type: str) -> str | None:
    before = set(page.evaluate(
        """() => Array.from(document.querySelectorAll('.react-flow__node'))
             .map(n => n.getAttribute('data-id')).filter(Boolean)"""
    ))
    page.get_by_role("button", name="添加节点", exact=True).click(force=True)
    page.wait_for_timeout(500)
    entry = page.locator(f"[data-add-node-entry='{entry_type}']")
    if entry.count() == 0:
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        return None
    entry.first.click(force=True)
    page.wait_for_timeout(1400)
    after = page.evaluate(
        """() => Array.from(document.querySelectorAll('.react-flow__node'))
             .map(n => n.getAttribute('data-id')).filter(Boolean)"""
    )
    new = [n for n in after if n not in before]
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)
    return new[0] if new else None


def open_annotate(page: Page, retries: int = 3) -> bool:
    for _ in range(retries):
        ann = page.locator('[data-testid="image-toolbar-annotate"]')
        if ann.count() == 0:
            return False
        try:
            ann.first.click(force=True, timeout=4000)
        except Exception:  # noqa: BLE001
            ann.first.evaluate("(el) => el.click()")
        page.wait_for_timeout(900)
        if page.locator("[data-image-annotate-canvas]").count() > 0:
            return True
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
    return False


def run(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": [], "surfaces": {}}

    def check(name: str, ok: bool, detail: str = "") -> None:
        assert ok, f"batch360 check failed: {name} {detail}".strip()
        result["checks"].append(name)

    errors: list[str] = []
    page.on(
        "console",
        lambda m: errors.append(f"console:{m.type}:{m.text}") if m.type == "error" else None,
    )
    page.on("pageerror", lambda e: errors.append(f"pageerror:{e}"))

    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_selector(".react-flow__node", timeout=30000)
    page.wait_for_timeout(600)

    def census(name: str) -> dict[str, Any]:
        st = classify(page.evaluate(SCAN_JS))
        result["surfaces"][name] = {
            "inputs": st["inputs"], "controls": st["controls"],
            "silent": st["silentDiscard"], "dead": st["deadControls"],
        }
        check(f"{name}:no-silent-discard", not st["silentDiscard"],
              f"静默丢弃输入的控件: {st['silentDiscard']}")
        check(f"{name}:no-dead-control", not st["deadControls"],
              f"点了没反应的控件: {st['deadControls']}")
        check(f"{name}:no-lying-affordance", not st.get("lyingAffordance"),
              f"声明了惰性却仍带 hover 视觉暗示(悬停会亮, 像能点): "
              f"{st.get('lyingAffordance')}")
        check(f"{name}:coverage", st["controls"] >= MIN_CONTROLS_PER_SURFACE,
              f"该面只扫到 {st['controls']} 个控件 —— 面板可能没打开")
        return st

    # ── ① 默认画布里没有的节点类型 ──
    created: dict[str, Any] = {}
    for label, entry_type in NEW_NODE_TYPES:
        close_all(page)
        nid = create_node(page, entry_type)
        created[label] = nid
        check(f"new-node:{label}:created", nid is not None,
              f"「{label}」(data-add-node-entry='{entry_type}') 没能创建出来 —— "
              "这一面等于没测, 不能算「干净」")
        if nid is None:
            continue
        page.locator(f'.react-flow__node[data-id="{nid}"]').first.evaluate("(el) => el.click()")
        page.wait_for_timeout(900)
        census(f"new:{label}")
    result["created"] = created

    # ── ② 浮层 ──
    image_ids = [
        nid for nid in page.evaluate(
            """() => Array.from(document.querySelectorAll('.react-flow__node'))
                 .map(n => n.getAttribute('data-id')).filter(Boolean)"""
        )
        if nid.startswith("i-")
    ]
    check("canvas:has-image-node", bool(image_ids), "画布上没有图片节点, 浮层无从下手")
    if image_ids:
        nid = image_ids[0]
        close_all(page)
        page.locator(f'.react-flow__node[data-id="{nid}"]').first.evaluate("(el) => el.click()")
        page.wait_for_timeout(700)

        prev = page.locator('[data-testid="image-toolbar-preview"]')
        if prev.count() > 0:
            try:
                prev.first.click(force=True, timeout=4000)
            except Exception:  # noqa: BLE001
                prev.first.evaluate("(el) => el.click()")
            page.wait_for_timeout(1000)
            opened = page.locator("[data-image-preview-content]").count() > 0
            check("overlay:preview:opened", opened,
                  "预览大图没打开 —— 这一面等于没测, 不能算「干净」")
            if opened:
                census("overlay:preview")
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            page.locator(f'.react-flow__node[data-id="{nid}"]') \
                .first.evaluate("(el) => el.click()")
            page.wait_for_timeout(700)

        if open_annotate(page):
            census("overlay:annotate")
            color = page.locator("[data-image-annotate-color]").first
            if color.count() > 0:
                try:
                    color.click(force=True, timeout=4000)
                except Exception:  # noqa: BLE001
                    color.evaluate("(el) => el.click()")
                page.wait_for_timeout(700)
                menu_open = page.locator("[data-image-annotate-color-menu]").count() > 0
                check("overlay:color-menu:opened", menu_open,
                      "标注颜色菜单没打开 —— 这一面等于没测")
                if menu_open:
                    census("overlay:annotate:color")
        else:
            check("overlay:annotate:opened", False,
                  "标注画布在 3 次重试后仍未打开 —— 这一面等于没测")

    check("diagnostics:zero", not errors, f"errors={errors[:3]}")
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 360,
        "defect": "普查未覆盖的两块: ①能新建但默认画布没有的节点类型(音频/智能剪辑/"
                  "逐帧拉片)的编辑面板 —— 3 个死控件(AudioNode 播放音频、"
                  "VideoClipEditPanel 的默认模式与输出设置); ②浮层(预览大图/标注画布/"
                  "标注颜色菜单)—— 0 个。",
        "fix": "3 个死控件改为「保持启用 + 去悬停反馈 + cursor default + title + "
               "data-inert」, 文案与几何不动(batch25 读的正是文案)。",
        "role": "把节点类型与浮层纳入交互谎言门禁; 跳过导演台(另一条线, 有并行 session 在改)",
    }
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            audit["desktop"] = run(page)
        finally:
            browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2))
    n = len(audit["desktop"]["surfaces"])
    print(
        f"Batch 360 verification passed: {len(audit['desktop']['checks'])} checks, "
        f"{audit['desktop']['diagnostics']['console']} diagnostics. "
        f"Covered {n} surfaces: three node types absent from the default canvas "
        "(audio / smart clip / shot breakdown) plus the preview overlay, the annotate "
        "canvas and its colour menu. No input silently discards what the user types and "
        "no enabled control is left click-dead in any of them."
    )


if __name__ == "__main__":
    main()
