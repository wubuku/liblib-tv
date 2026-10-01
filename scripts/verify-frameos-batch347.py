#!/usr/bin/env python3

"""Verify Batch 347: 交互盲区清零 + 把它变成**门禁**（不再靠临场想起补钩子）。

缺陷（元缺陷，Batch 345/346 **连踩两次**）:
- Batch 345: `FrameosToast` 的 toast 元素只有内联样式、没有任何标识 → 「UI 是否
  谎报成功」根本测不了。
- Batch 346: 帮助面板的行**同样**没有可寻址属性。

同一个坑在两个批次里踩两次，说明「补可测性」靠临场想起是不可靠的。

本批把欠账**测出来**并清零，然后把「清零」变成**门禁**:
运行时枚举所有可点元素，任何一个缺少稳定钩子（无 data-frameos-* / 无
aria-label / 无 id / 无 title）都让验证器失败。以后新增 UI 元素忘加钩子，
门禁会当场指出来。

修复前的运行时普查（probe-frameos-batch347-interactive-blindspots.py）:
    [default] 可点元素 38  有稳定钩子 34  盲区 4  (11%)
    盲区样本: '下载桌面端' / '测试作品' / '测试项目' / '画布 1'
—— 三个**核心导航**控件 + 一个头部按钮, 恰恰是测试唯一没法精确定位的东西。

断言:
1. 默认态**零**交互盲区（门禁主体）;
2. 帮助面板打开时**零**盲区;
3. 选中节点（浮动工具条出现）时**零**盲区;
4. 三个面包屑按钮各自可被 `data-frameos-crumb` 精确寻址;
5. 面包屑按钮的钩子值与显示文本一致;
6. 钩子真的能用来**操作**面包屑（点它能打开对应下拉）—— 钩子不是摆设;
7. 「下载桌面端」按钮可寻址;
8. 枚举总数不为 0（防止「因为选择器写错所以没扫到任何元素」这种假绿）;
9. 诊断零错误。
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
    ROOT
    / "docs"
    / "research"
    / "liblib-frameos-batch347-2026-10-01"
    / "runtime-audit.json"
)
sys.path.insert(0, str(ROOT / "scripts"))
from frameos_verify_common import attach_errors, goto_clean_canvas  # noqa: E402

# 与探针同一份枚举逻辑 —— 门禁和测量必须用同一把尺子
ENUMERATE_JS = """
() => {
  const sel = 'button, [role="button"], a[href], input, textarea, select, [tabindex]';
  const nodes = Array.from(document.querySelectorAll(sel));
  const describe = (el) => {
    const text = (el.textContent || '').trim().slice(0, 24);
    const aria = el.getAttribute('aria-label') || '';
    const title = el.getAttribute('title') || '';
    const dataKeys = Array.from(el.attributes)
      .filter((a) => a.name.startsWith('data-'))
      .map((a) => a.name);
    const id = el.id || '';
    const hooks = [];
    if (dataKeys.length) hooks.push(...dataKeys);
    if (aria) hooks.push('aria-label=' + aria);
    if (title) hooks.push('title=' + title);
    if (id) hooks.push('#' + id);
    return { tag: el.tagName.toLowerCase(), text, aria, title, id,
             dataKeys, hasHook: hooks.length > 0, hooks };
  };
  const all = nodes.map(describe);
  const blind = all.filter((d) => !d.hasHook);
  return {
    total: all.length,
    withHook: all.length - blind.length,
    blind: blind.length,
    blindItems: blind.map((d) => ({
      tag: d.tag, text: d.text || d.aria || d.title || '(无任何文字)',
    })),
  };
}
"""


def scan(page: Page) -> dict[str, Any]:
    return page.evaluate(ENUMERATE_JS)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool, detail: str = "") -> None:
        assert ok, f"batch347 check failed: {name} {detail}".strip()
        result["checks"].append(name)

    errors = attach_errors(page)
    goto_clean_canvas(page, BASE_URL)

    # ── 1~3 三种 UI 态下都必须零盲区 ──
    default = scan(page)
    result["default"] = default
    check("scan:not-empty", default["total"] >= 20,
          f"只扫到 {default['total']} 个元素 —— 选择器可能写错了(假绿)")
    check("blind:default-zero", default["blind"] == 0,
          f"盲区 {default['blind']}/{default['total']}: {default['blindItems']}")

    page.keyboard.press("?")
    page.wait_for_timeout(500)
    with_help = scan(page)
    result["with_help"] = with_help
    check("blind:with-help-zero", with_help["blind"] == 0,
          f"盲区 {with_help['blind']}/{with_help['total']}: {with_help['blindItems']}")
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    page.evaluate(
        """() => {
          const st = window.__frameos_store;
          st.getState().selectNode(st.getState().nodes[0].id);
          return true;
        }"""
    )
    page.wait_for_timeout(700)
    with_node = scan(page)
    result["with_node_selected"] = with_node
    check("blind:with-node-selected-zero", with_node["blind"] == 0,
          f"盲区 {with_node['blind']}/{with_node['total']}: {with_node['blindItems']}")

    # ── 4~6 面包屑: 钩子存在 + 值正确 + 真的能用来操作 ──
    crumbs = page.evaluate(
        """() => Array.from(document.querySelectorAll('[data-frameos-crumb]')).map((el) => ({
             hook: el.getAttribute('data-frameos-crumb'),
             text: (el.textContent || '').trim(),
           }))"""
    )
    result["crumbs"] = crumbs
    check("crumb:three-buttons", len(crumbs) == 3, f"crumbs={crumbs}")
    for c in crumbs:
        check(f"crumb:hook-matches-text:{c['hook']}", c["hook"] == c["text"],
              f"hook={c['hook']!r} text={c['text']!r}")
    # 钩子不是摆设: 用它点开画布下拉
    page.locator('[data-frameos-crumb="画布 1"]').first.click()
    page.wait_for_timeout(400)
    check("crumb:hook-usable", page.locator("[data-frameos-canvas-dropdown]").count() == 1,
          "用钩子点面包屑没有打开下拉 —— 钩子存在但不可用于操作")
    page.keyboard.press("Escape")
    page.mouse.click(1000, 700)
    page.wait_for_timeout(300)

    # ── 7 下载桌面端可寻址 ──
    check("header:download-addressable",
          page.locator("[data-frameos-download-client]").count() == 1,
          "「下载桌面端」按钮仍无钩子")

    # ── 8~12 Batch 353: 门禁覆盖面从 3 态扩到 8 态 ──
    # 每进一个态就扫一次, 退干净再进下一个(态之间会互相污染, 例如裁剪态会
    # 顶掉普通工具条)。这 5 个态在原门禁里**完全没被检查过**。
    for name, enter in [
        ("crop", enter_crop_state),
        ("group", enter_group_state),
        ("node-search", enter_node_search_state),
        ("template-panel", enter_template_state),
        ("generation", enter_generation_state),
    ]:
        leave_all(page)
        enter(page)
        snap = scan(page)
        result[f"state_{name}"] = snap
        check(f"scan:not-empty:{name}", snap["total"] >= 20,
              f"只扫到 {snap['total']} 个元素 —— 态可能没进去(假绿)")
        check(f"blind:{name}-zero", snap["blind"] == 0,
              f"盲区 {snap['blind']}/{snap['total']}: {snap['blindItems']}")
    leave_all(page)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


# ── Batch 353: 把门禁的 UI 态覆盖面从 3 种扩到 8 种 ──────────────────────
# 原门禁只普查「默认 / 帮助开 / 选中节点」三态，于是**碰不到**的东西一律
# 逃过检查: 裁剪态、分组态、节点搜索面板、模板面板, 以及
# `FrameosGenerationOverlay`(整个组件零 data-frameos-*)。
# 探针(probe-frameos-batch353-addressability.py)在这 5 个新态里量出 **5 个盲区**:
#   group     3  (整组执行 / 存为模板 / 解组)
#   generation 2  (取消按钮 + 常态面板的 prompt textarea)
# 补钩子后 5 态全部归零, 并把 5 个新态并入门禁 —— 覆盖面本身就是约束,
# 否则「门禁只扫 3 态」这件事会慢慢被忘掉, 新的盲区继续从缝里长出来。
EXTRA_STATES: list[tuple[str, Any]] = []


def enter_crop_state(page: Page) -> None:
    page.locator('.react-flow__node[data-id="image-1"]').click()
    page.wait_for_timeout(600)
    page.get_by_label("裁剪", exact=True).first.click()
    page.wait_for_selector("[data-frameos-crop-rect]", timeout=8000)
    page.wait_for_timeout(400)


def enter_group_state(page: Page) -> None:
    page.evaluate(
        """() => {
            const st = window.__frameos_store;
            const ids = st.getState().nodes.slice(0, 2).map((n) => n.id);
            st.getState().createGroup(ids);
            return true;
        }"""
    )
    page.wait_for_timeout(700)


def enter_node_search_state(page: Page) -> None:
    page.keyboard.press("Meta+f")
    page.wait_for_timeout(600)


def enter_template_state(page: Page) -> None:
    page.get_by_label("模板", exact=True).first.click()
    page.wait_for_timeout(600)


def enter_generation_state(page: Page) -> None:
    """进入生成浮窗。mock 时钟压到 20s —— 机制与时长无关, 探针用 2s 同理。"""
    pane = page.locator(".react-flow__pane")
    box = pane.bounding_box()
    pane.dblclick(position={"x": box["width"] * 0.2, "y": box["height"] * 0.75})
    page.wait_for_selector("[data-frameos-pane-addnode-type]", timeout=8000)
    page.locator('[data-frameos-pane-addnode-type="image"]').click()
    page.wait_for_timeout(500)
    page.locator(".react-flow__node").last.click()
    page.wait_for_timeout(500)
    page.get_by_label("生成", exact=True).first.click()
    page.wait_for_timeout(300)
    page.evaluate(
        """() => {
            const s = window.__frameos_store.getState();
            window.__frameos_store.setState({
              currentGeneration: { ...s.currentGeneration, durationMs: 20000 },
            });
        }"""
    )
    page.wait_for_timeout(600)


def leave_all(page: Page) -> None:
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    page.evaluate("() => window.__frameos_store.getState().setCroppingNode(null)")
    page.wait_for_timeout(200)


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 347,
        "title": "FrameOS interactive blind spots cleared to zero and locked by a gate",
        "defect": (
            "A meta-defect hit twice: Batch 345 found FrameosToast elements had no "
            "identifying attribute (so 'is the UI lying about success?' was untestable), "
            "and Batch 346 found the help panel rows had the same problem. Twice is a "
            "pattern: 'remember to add test hooks' is not a reliable process. A runtime "
            "census measured the remaining debt: 38 clickable elements, 4 blind spots "
            "(11%) -- '下载桌面端' plus the three core breadcrumb navigation buttons "
            "(项目/场景/画布), i.e. exactly the controls a test most needs to address."
        ),
        "fix": (
            "Added data-frameos-crumb (covers all three breadcrumb switchers via their "
            "shared Crumb renderer) and data-frameos-download-client. The important part "
            "is not the two attributes but the GATE: the verifier enumerates every "
            "clickable element in three UI states and fails if any lacks a stable hook, "
            "naming it. Future UI added without a hook now fails the suite instead of "
            "quietly becoming untestable."
        ),
        "note": (
            "'下载桌面端' remains a deliberate mock (window.alert). The source's target is "
            "an external download URL that was never sampled, so the clone does not invent "
            "one -- but addressability is required regardless, precisely so that if it "
            "breaks later we can catch it."
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
        "Batch 347 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Every clickable element in the default canvas, the open help panel and the "
        "node-selected state now has a stable test hook, the three breadcrumb "
        "navigation buttons are individually addressable and actually operable via "
        "their hook, and the census is enforced as a gate so a future UI element "
        "cannot silently become untestable."
    )


if __name__ == "__main__":
    main()
