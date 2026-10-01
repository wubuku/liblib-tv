#!/usr/bin/env python3

"""Verify Batch 279: crop mode (裁剪) mock UI.

Source-sampled 2026-09-28 (docs/research/liblib-frameos-batch278-2026-09-28/):
content-image toolbar 裁剪 enters a crop state — control bar below the node
(退出裁剪 / 宽高比自由 / 480 x 480 inputs / 确认裁剪) + 8 调整裁剪区域 handles
on the node + thirds guides.

Checks (desktop 1440x900):
1. select content image → toolbar → 裁剪 click enters crop mode;
2. crop bar visible with 退出裁剪/宽高比/480x480 inputs/确认裁剪;
3. 8 handles on the node;
4. normal toolbar hidden while cropping;
5. 确认裁剪 alerts mock and exits crop mode;
6. re-enter → 退出裁剪 closes without alert;
7. console/page errors clean.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

from frameos_verify_common import attach_errors


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-frameos-batch279-2026-09-28"
    / "runtime-audit.json"
)



def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch279 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1500)

    # select content image node
    page.mouse.click(500, 200)
    page.wait_for_timeout(300)
    center = page.evaluate(
        """(() => {
          const r = document.querySelector('.react-flow__node[data-id=\\'image-1\\']')?.getBoundingClientRect();
          return r ? { x: r.x + r.width / 2, y: r.y + r.height / 2 } : null;
        })()"""
    )
    page.mouse.click(center["x"], center["y"])
    page.wait_for_timeout(600)
    toolbar = page.locator(".frameos-floating-toolbar-new")
    check("setup:toolbar-opens", toolbar.is_visible())

    # enter crop mode
    toolbar.locator("button[aria-label='裁剪']").click()
    page.wait_for_timeout(500)
    bar = page.locator(".frameos-crop-bar")
    check("crop:bar-opens", bar.is_visible())
    check("crop:normal-toolbar-hidden", not toolbar.is_visible())
    check("crop:exit-btn", page.locator("button[aria-label='退出裁剪']").count() == 1)
    check("crop:aspect-btn", page.locator("button[aria-label='宽高比']").count() == 1)
    check("crop:confirm-btn", bar.get_by_text("确认裁剪").count() == 1)
    # Batch 352: 此断言原先是 `crop:size-inputs-480`, 钉死两个输入框的值 === '480'。
    # 查一手源站采样 `docs/research/liblib-frameos-batch278-2026-09-28/CROP_OBSERVATIONS.md:11`:
    #     "[480] x [480]（两个 42px 宽的数字输入框，**裁剪区当前尺寸**）"
    # —— 480 是**采样当时那个裁剪区的当前尺寸**, 不是源站写死的常数; 观测者自己
    # 标注的就是「裁剪区当前尺寸」。克隆此前把观测值当常数抄进了 `defaultValue={480}`,
    # 并用本断言把那个字面化钉死 —— 于是输入框永远显示 480, 与节点实际尺寸无关,
    # 用户改了也不会被应用(Batch 350 修的就是这个)。
    # 所以这里断言的是**源站性质**: 输入框显示裁剪区**当前尺寸**。
    check(
        "crop:size-inputs-are-current-size",
        page.evaluate(
            """(() => {
              const ins = [...document.querySelectorAll('.frameos-crop-bar input')];
              if (ins.length !== 2) return false;
              const el = document.querySelector('.react-flow__node[data-id="image-1"]');
              if (!el) return false;
              const r = el.getBoundingClientRect();
              const zoom = (window.__frameos_canvas_zoom ?? 1);
              return ins.every((i) => {
                const v = Number(i.value);
                return Number.isFinite(v) && v > 0;
              }) && (() => {
                // 宽高必须与节点的流坐标尺寸一致（经 zoom 换算到 CSS px）
                const st = window.__frameos_store.getState();
                const n = st.nodes.find((x) => x.id === 'image-1');
                return n && n.style
                  && Number(ins[0].value) === Number(n.style.width)
                  && Number(ins[1].value) === Number(n.style.height);
              })();
            })()"""
        ),
    )
    handles = page.evaluate("document.querySelectorAll(\"[aria-label='调整裁剪区域']\").length")
    check("crop:8-handles", handles == 8)
    guides = page.evaluate(
        """(() => {
          const g = document.querySelector('.frameos-crop-guides');
          return g ? getComputedStyle(g).backgroundImage.includes('linear-gradient') : false;
        })()"""
    )
    check("crop:thirds-guides", guides)

    # 确认裁剪 → mock alert + exit (dialog auto-dismissed by attach_errors)
    bar.get_by_text("确认裁剪").click()
    page.wait_for_timeout(500)
    check("crop:confirm-exits", not bar.is_visible())

    # re-enter, exit via 退出裁剪
    page.mouse.click(center["x"], center["y"])
    page.wait_for_timeout(400)
    toolbar.locator("button[aria-label='裁剪']").click()
    page.wait_for_timeout(400)
    check("crop:re-enter", page.locator(".frameos-crop-bar").is_visible())
    page.locator("button[aria-label='退出裁剪']").click()
    page.wait_for_timeout(400)
    check("crop:exit-closes", not page.locator(".frameos-crop-bar").is_visible())
    check("crop:normal-toolbar-back", toolbar.is_visible())

    if errors:
        raise AssertionError(f"batch279 console/page errors: {errors[:3]}")
    result["checks"].append("errors:empty")
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 279, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch279: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
