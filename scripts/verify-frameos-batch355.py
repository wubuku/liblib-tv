#!/usr/bin/env python3

"""Verify Batch 355: 不允许存在「启用着、收下输入、什么都不做」的表单控件。

缺陷（克隆侧，用户可见）:
`FrameosProjectAssetsPanel` 的搜索框是一个**启用着、无 `value` 绑定、无 `onChange`**
的裸 `<input>`。用户在里面打字，控件收下输入，然后**什么都不发生**。

实测 (probe-frameos-batch355-input-census.py / probe_assets 探针, 修复前):
    搜索框 disabled = False
    输入 '角色' 后面板文本变化 = False     ← 一字不变
    输入框当前值 = '角色'                  ← 收下了, 留着, 没被用
    console errors: []                     ← 不是报错, 是纯惰性

与 Batch 350 的裁剪宽高同族: **看起来能用的表单, 静默丢弃用户的输入**。
区别在于裁剪那条会弹确认(更恶劣), 这条安静地什么都不做。

修复: 面板内容是硬编码空态「暂无已生成的资产图」—— 克隆侧没有资产数据, 而
「把节点设为资产图」的源站点击效果未采样(Batch 226), 因此**不发明**资产分类学。
没有东西可搜时, 唯一诚实的做法是**别假装它能用**: 禁用 + 说明原因 + 视觉区分。

本验证器把普查变成**门禁**（Batch 347 的同款思路: 元缺陷不能靠临场想起）:
枚举各 UI 态下所有启用的 input/textarea, 任何一个既无 `onChange` 又非 disabled
就让验证器失败并指名。

断言:
1. 防假绿: 普查本身能跑通, 且各态的元素总数不为 0（否则「零违规」可能只是没扫到）;
2~5. 资产面板 / 裁剪态 / 主生成面板 / 默认态 —— 启用控件的**静默丢弃数为 0**;
6. 资产搜索框确实是 disabled 且带说明（钉住本次修复）;
7. 资产面板空态仍在（不因为禁用搜索框就把空态删了）;
8. 诊断零错误。
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
    ROOT / "docs" / "research" / "liblib-frameos-batch355-2026-10-01" / "runtime-audit.json"
)
sys.path.insert(0, str(ROOT / "scripts"))
from frameos_verify_common import attach_errors, goto_clean_canvas  # noqa: E402

# React 会把 props 挂在 DOM 节点上(__reactProps$*), 从那里读 onChange/value
# —— 判据是「这个控件有没有被 React 接上事件处理」, 而不是看源码里有没有写。
CLASSIFY_JS = """
() => {
  const out = Array.from(document.querySelectorAll('input, textarea')).map((el) => {
    const rk = Object.keys(el).filter((k) => k.startsWith('__reactProps$'));
    let hasOnChange = false;
    for (const k of rk) {
      const props = el[k];
      if (props && typeof props.onChange === 'function') hasOnChange = true;
    }
    return {
      tag: el.tagName.toLowerCase(),
      disabled: el.disabled === true,
      readOnly: el.readOnly === true,
      placeholder: (el.placeholder || '').slice(0, 30),
      data: Array.from(el.attributes).filter((a) => a.name.startsWith('data-')).map((a) => a.name),
      hasOnChange,
    };
  });
  return out;
}
"""


def leave_all(page: Page) -> None:
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    page.evaluate(
        """() => {
            const st = window.__frameos_store.getState();
            st.setCroppingNode(null);
            if (st.isProjectAssetsPanelOpen) st.toggleProjectAssetsPanel();
            st.selectNode(null);
        }"""
    )
    page.wait_for_timeout(300)


def enter_assets(page: Page) -> None:
    page.locator("[data-frameos-assets-button]").first.click()
    page.wait_for_selector("[data-frameos-project-assets-panel]", timeout=8000)


def enter_crop(page: Page) -> None:
    page.locator('.react-flow__node[data-id="image-1"]').click()
    page.wait_for_timeout(600)
    page.get_by_label("裁剪", exact=True).first.click()
    page.wait_for_selector("[data-frameos-crop-rect]", timeout=8000)


def enter_generative(page: Page) -> None:
    pane = page.locator(".react-flow__pane")
    box = pane.bounding_box()
    pane.dblclick(position={"x": box["width"] * 0.2, "y": box["height"] * 0.75})
    page.wait_for_selector("[data-frameos-pane-addnode-type]", timeout=8000)
    page.locator('[data-frameos-pane-addnode-type="image"]').click()
    page.wait_for_timeout(500)
    page.locator(".react-flow__node").last.click()
    page.wait_for_timeout(600)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool, detail: str = "") -> None:
        assert ok, f"batch355 check failed: {name} {detail}".strip()
        result["checks"].append(name)

    errors = attach_errors(page)
    goto_clean_canvas(page, BASE_URL)

    states = [
        ("default", lambda pg: None),
        ("assets_panel", enter_assets),
        ("crop", enter_crop),
        ("generative_panel", enter_generative),
    ]
    census: dict[str, Any] = {}
    for name, enter in states:
        leave_all(page)
        enter(page)
        page.wait_for_timeout(400)
        items = page.evaluate(CLASSIFY_JS)
        silent = [
            it for it in items
            if not it["disabled"] and not it["readOnly"] and not it["hasOnChange"]
        ]
        census[name] = {"all": items, "silently_discarding": silent}
        # 资产面板/裁剪态/主面板必须真的扫到控件, 否则「零违规」是空断言
        if name != "default":
            check(f"scan:not-empty:{name}", len(items) >= 1,
                  f"只扫到 {len(items)} 个控件 —— 态可能没进去(假绿)")
        check(f"no-silent-discard:{name}", not silent,
              f"静默丢弃输入的控件: "
              f"{[{'tag': i['tag'], 'ph': i['placeholder'], 'data': i['data']} for i in silent]}")

    result["census"] = census
    check("scan:not-empty:default-or-others",
          sum(len(v["all"]) for v in census.values()) >= 4,
          "全部态加起来控件数过少 —— 普查可能整体失效(假绿)")

    # ── 钉住本次修复 ──
    leave_all(page)
    enter_assets(page)
    page.wait_for_timeout(300)
    search = page.locator("[data-frameos-assets-search]")
    check("assets-search:exists", search.count() == 1, f"count={search.count()}")
    check("assets-search:disabled", search.evaluate("el => el.disabled === true"),
          "资产搜索框又变回启用状态 —— 会重新变成静默丢弃输入的假控件")
    check("assets-search:explains-why",
          "暂无资产" in (search.get_attribute("title") or ""),
          f"title={search.get_attribute('title')!r}（应说明为什么不能搜）")
    panel_text = page.locator("[data-frameos-project-assets-panel]").inner_text()
    check("assets-panel:empty-state-kept", "暂无已生成的资产图" in panel_text,
          f"空态被误删: {panel_text[:60]!r}")

    check("diagnostics:zero", not errors, f"errors={errors[:3]}")
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 355,
        "defect": "项目资产面板的搜索框是启用着、无 value 绑定、无 onChange 的裸 input —— "
                  "收下输入后什么都不做(实测输入后面板文本一字不变、零 console 错误)",
        "fix": "没有资产可搜时禁用并说明原因(不发明资产分类学: 源站点击效果未采样)",
        "role": "把「静默丢弃输入」普查变成门禁",
    }
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            audit["desktop"] = run_desktop(page)
        finally:
            browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2))
    print(
        f"Batch 355 verification passed: {len(audit['desktop']['checks'])} checks, "
        f"{audit['desktop']['diagnostics']['console']} diagnostics. "
        "No enabled input or textarea in any frameos UI state silently discards what "
        "the user types any more — the assets search box is disabled with a reason "
        "instead of pretending to work, and the census is enforced as a gate."
    )


if __name__ == "__main__":
    main()
