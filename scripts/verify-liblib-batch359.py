#!/usr/bin/env python3

"""Verify Batch 359: liblib 节点编辑面与输入控件的「交互谎言」双类门禁。

Batch 358 普查的是**画布外框**的 16 个态。节点一被选中, 浮出来的是另一整片界面 ——
图片节点浮动工具条(十来个动作)、图片编辑面板、标注模式工具条、视频片段编辑面板 ——
**这片面一次都没普查过**, 而 frameos batch 350 那个「裁剪宽高静默丢弃输入」正是在
节点级编辑态里。

结果: **16 个画布态 + 15 个节点面, 两类缺陷都是 0。**
这不是「没查」, 是查过了:

- 静默丢弃输入: 全线干净, 且**功能抽检**过 —— 风格库搜索 16 张卡 → 敲不存在的词
  → 0 张; 特效库 24 → 0; 工作区改名生效。有 `onChange` 只是必要条件
  (frameos batch 350 的裁剪框就是「有 handler、值进了 store、但没有任何代码读它」),
  所以必须真敲字看结果。
- 点了没反应: 判据与 batch358 完全一致(含「例外须自证惰性」), 零命中。

## 这批真正的产出是**两个门禁**, 以及一次假零的拦截

普查工具最危险的失败模式不是报错, 是**安静地什么都没测**然后报「无问题」。
本批实际拦下两次:

1. **画布没 hydration 完** —— 一轮 `wait_for_timeout(1500)` 没等到,
   `node_ids` 拿到空数组, 探针「跑完」并报 0 问题 / 0 死控件。**假零。**
   现在显式 `wait_for_selector('.react-flow__node')`, 且节点为空时直接抛错。
2. **标注模式没打开** —— 工具条带 scale transform, 页面内 `el.click()` 点不动它。
   第一版一律用派发点击, 标注态的 testid 集合是空的、控件数反而从 ~50 掉到 39,
   却照样显示「无问题」。三连跑里还**间歇性**失败(第 2 轮有一个 False)。
   现在: 先 `click(force=True)`、失败退回派发, 并**有界重试**直到标注工具条真的出现;
   仍打不开就红 —— 那一态等于没测, 不能算「干净」。

## 断言

1. 画布节点非空 (否则普查没测到东西, 不能报零违规);
2. 16 个画布态: 输入控件无静默丢弃;
3. 每个节点面: 无静默丢弃、无死控件;
4. 标注态**真的打开** (防假绿, 有界重试后仍失败即红);
5. 覆盖下界: 节点面数、控件总数、输入控件总数不为 0 —— 界面长大后门禁会要求重新枚举;
6. 诊断零错误。
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
    ROOT / "docs" / "research" / "liblib-batch359-2026-10-01" / "runtime-audit.json"
)
sys.path.insert(0, str(ROOT / "scripts"))
from probe_liblib_batch359_node_surfaces import (  # noqa: E402
    PRIMARY_PANELS,
    SCAN_JS,
    TOGGLES,
    classify,
    close_all,
)

MIN_NODE_SURFACES = 8
ANNOTATE_RETRIES = 3


def click_node(page: Page, node_id: str) -> bool:
    loc = page.locator(f'.react-flow__node[data-id="{node_id}"]')
    if loc.count() == 0:
        return False
    # 节点可能在视口外(react-flow viewport transform), 真实点击会抛
    # "Element is outside of the viewport"; 页面内派发可以稳定选中。
    loc.first.evaluate("(el) => el.click()")
    page.wait_for_timeout(700)
    return True


def open_annotate(page: Page) -> bool:
    """有界重试直到标注工具条真的出现。返回是否打开。"""
    for _ in range(ANNOTATE_RETRIES):
        ann = page.locator('[data-testid="image-toolbar-annotate"]')
        if ann.count() == 0:
            return False
        try:
            ann.first.click(force=True, timeout=4000)
        except Exception:  # noqa: BLE001
            ann.first.evaluate("(el) => el.click()")
        page.wait_for_timeout(900)
        if page.locator("[data-image-annotate-toolbar]").count() > 0:
            return True
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        page.locator(f'.react-flow__node[data-id="{page.evaluate("window.__lastNode")}"]') \
            .first.evaluate("(el) => el.click()")
        page.wait_for_timeout(700)
    return False


def run(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool, detail: str = "") -> None:
        assert ok, f"batch359 check failed: {name} {detail}".strip()
        result["checks"].append(name)

    errors: list[str] = []
    page.on(
        "console",
        lambda m: errors.append(f"console:{m.type}:{m.text}") if m.type == "error" else None,
    )
    page.on("pageerror", lambda e: errors.append(f"pageerror:{e}"))

    page.goto(BASE_URL, wait_until="networkidle")
    # 防假零: 必须真的等到画布节点
    page.wait_for_selector(".react-flow__node", timeout=30000)
    page.wait_for_timeout(600)

    # ── 画布外框 16 态: 只查输入控件 ──
    chrome: dict[str, Any] = {}
    page.evaluate("() => { const ui = window.__libtv_ui_store.getState(); "
                  "if (ui.closeAllPanels) ui.closeAllPanels(); }")
    page.wait_for_timeout(300)
    chrome["__default__"] = classify(page.evaluate(SCAN_JS))
    for name in PRIMARY_PANELS:
        close_all(page)
        page.evaluate("(n) => window.__libtv_ui_store.getState().setPrimaryPanel(n)", name)
        page.wait_for_timeout(800)
        chrome[name] = classify(page.evaluate(SCAN_JS))
    for name, fn in TOGGLES:
        close_all(page)
        page.evaluate("(f) => window.__libtv_ui_store.getState()[f]()", fn)
        page.wait_for_timeout(800)
        chrome[name] = classify(page.evaluate(SCAN_JS))

    for name, st in chrome.items():
        check(f"chrome:no-silent-discard:{name}", not st["silentDiscard"],
              f"静默丢弃输入的控件: {st['silentDiscard']}")
    result["chrome"] = {
        n: {"inputs": s["inputs"], "controls": s["controls"]} for n, s in chrome.items()
    }

    # ── 节点面: 两类都查 ──
    node_ids = page.evaluate(
        """() => Array.from(document.querySelectorAll('.react-flow__node'))
             .map(n => n.getAttribute('data-id')).filter(Boolean)"""
    )
    check("canvas:has-nodes", len(node_ids) >= MIN_NODE_SURFACES,
          f"只找到 {len(node_ids)} 个节点 —— 画布可能没加载, 不能据此报零违规")

    surfaces: dict[str, Any] = {}
    annotate_ok = 0
    for nid in node_ids:
        close_all(page)
        if not click_node(page, nid):
            continue
        page.evaluate("(id) => { window.__lastNode = id; }", nid)
        label = f"node:{nid[:14]}"
        st = classify(page.evaluate(SCAN_JS))
        surfaces[label] = st
        check(f"{label}:no-silent-discard", not st["silentDiscard"],
              f"静默丢弃输入的控件: {st['silentDiscard']}")
        check(f"{label}:no-dead-control", not st["deadControls"],
              f"点了没反应的控件: {st['deadControls']}")

        if page.locator('[data-testid="image-toolbar-annotate"]').count() > 0:
            opened = open_annotate(page)
            alabel = label + ":annotate"
            if opened:
                st2 = classify(page.evaluate(SCAN_JS))
                surfaces[alabel] = st2
                annotate_ok += 1
                check(f"{alabel}:no-silent-discard", not st2["silentDiscard"],
                      f"静默丢弃输入的控件: {st2['silentDiscard']}")
                check(f"{alabel}:no-dead-control", not st2["deadControls"],
                      f"点了没反应的控件: {st2['deadControls']}")
            else:
                check(f"{alabel}:opened", False,
                      f"标注模式在 {ANNOTATE_RETRIES} 次重试后仍未打开 —— "
                      "这一态等于没测, 不能算「干净」")
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)

    check("annotate:covered", annotate_ok >= 3,
          f"只有 {annotate_ok} 个节点进到了标注模式 —— 覆盖不足")

    total_controls = sum(s["controls"] for s in surfaces.values())
    total_inputs = sum(s["inputs"] for s in surfaces.values())
    result["nodeSurfaces"] = {
        "count": len(surfaces),
        "annotateOpened": annotate_ok,
        "totalControls": total_controls,
        "totalInputs": total_inputs,
    }
    check("coverage:surfaces", len(surfaces) >= MIN_NODE_SURFACES,
          f"只测到 {len(surfaces)} 个节点面")
    check("coverage:controls", total_controls >= 300,
          f"节点面总共只扫到 {total_controls} 个控件 —— 覆盖不足")
    check("coverage:inputs", total_inputs >= 10,
          f"节点面总共只扫到 {total_inputs} 个输入控件 —— 覆盖不足")

    check("diagnostics:zero", not errors, f"errors={errors[:3]}")
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 359,
        "defect": "无新缺陷。普查从画布外框扩到节点编辑面(15 个节点面)并新增"
                  "「静默丢弃输入」一类, 16 个画布态 + 15 个节点面两类均为 0。",
        "fix": "不适用(无缺陷可修)。本批产出是两个门禁, 以及两次**假零**的拦截: "
               "画布未 hydration 导致普查测到 0 个节点却报「无问题」; 标注模式间歇性"
               "打不开却照样计入「干净」。",
        "role": "把节点编辑面与输入控件纳入交互谎言门禁, 并给普查加防假零下界",
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
    ns = audit["desktop"]["nodeSurfaces"]
    print(
        f"Batch 359 verification passed: {len(audit['desktop']['checks'])} checks, "
        f"{audit['desktop']['diagnostics']['console']} diagnostics. "
        f"Covered {len(audit['desktop']['chrome'])} canvas chrome states and "
        f"{ns['count']} node surfaces ({ns['annotateOpened']} in annotate mode, "
        f"{ns['totalControls']} controls, {ns['totalInputs']} inputs). "
        "No input silently discards what the user types and no enabled control is "
        "left click-dead in any of them, and the census refuses to report a clean "
        "result unless it actually reached those surfaces."
    )


if __name__ == "__main__":
    main()
