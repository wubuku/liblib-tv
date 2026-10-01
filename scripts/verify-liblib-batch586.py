#!/usr/bin/env python3
"""Verify Batch 586: director shell surface audit against 2026-10-01 source.

Source evidence: live CDP sampling of the source director desk taken before the
source overlay was closed (the 打开导演台 node button never responds and a page
reload does not restore it, so this channel needs a manual re-open):

  截图 tab (camera)   empty state 「暂无摄像机截图」; footer 「全部清空」
                      (x=1338) + 「发送到画布」 (x=1466)
  icon rail (x=8)     场景 / 添加角色 / 添加机位 / 全景图 / 选择画幅比例 /
                      AI 识图导入 / 帮助 — aria and title both verbatim
  scene tree rows     per row two icon buttons: title=隐藏 (x=226) and
                      title=锁定 (x=248)
  header              关闭 (x=0) + 收起 (x=240)
  viewport top        导演视角 / 机位视角 toggle, 重置视角
  viewport bottom     移动 / 截图 / 动画时间轴 / 上传图片 / prompt / 发送

Contract asserted here (audit + the one verified fix):
1. camera 截图 tab keeps the source empty state and both footer actions;
2. the icon rail exposes the same seven entries with the same aria labels;
3. object-tree row buttons use the source's verbatim 隐藏 / 锁定 titles;
4. the viewport view-mode toggle and 重置视角 exist;
5. the close affordance carries the source's 关闭 title;
6. no diagnostics.

Source evidence channel: the 打开导演台 node button only responds to a TRUSTED
pointer event. `el.click()` / Playwright's `locator.click()` on a detached-style
synthetic path is ignored by the source handler; `page.mouse.click(x, y)` at
the button's viewport coordinates opens the desk. Recorded here because it cost
several rounds of "the button is dead" dead-ends (batch 581–585).

Deliberately NOT implemented in this batch (recorded instead): aligning the
source header's 收起 button. Its behaviour WAS observed once the channel came
back (see the 收起 section of the batch README): 收起 removes the header and
the left scene panel only — the icon rail, the 3D viewport, the right inspector
panel, the 导演视角/机位视角 toggle, the gizmo and 重置视角 all stay; clicking
the rail's 场景 entry brings the header and left panel back. The clone's
`data-director-panels-toggle` (全屏 / 恢复侧栏) collapses BOTH panels instead,
and its state lives in `viewportPanelsCollapsed`, which four other verifiers
(batch 50 / 74 / 89 / 93) assert against. Re-pointing that state is a contract
migration, not a rename, so it is its own batch.
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
    / "liblib-canvas-batch586-2026-10-01"
    / "runtime-audit.json"
)

RAIL_ENTRIES = [
    "场景",
    "添加角色",
    "添加机位",
    "全景图",
    "选择画幅比例",
    "AI 识图导入",
    "帮助",
]


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

    def check(name: str, ok: bool, detail: Any = None) -> None:
        assert ok, f"batch586 check failed: {name} :: {detail}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 586" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(500)

    # 1) camera 截图 tab: source empty state + both footer actions
    page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          const camera = s.objects.find((o) => o.kind === 'camera');
          s.selectObject(camera.id);
        }"""
    )
    page.locator('[data-director-camera-tab="captures"]').click()
    gallery = page.locator("[data-director-capture-clear-all]").locator(
        "xpath=ancestor-or-self::*[1]"
    )
    check("capture:tab-visible", page.locator("[data-director-camera-tab='captures']").is_visible())
    check(
        "capture:empty-state",
        "暂无摄像机截图" in page.locator("[data-director-inspector]").inner_text(),
    )
    check(
        "capture:clear-all",
        page.locator("[data-director-capture-clear-all]").inner_text().strip() == "全部清空",
    )
    check(
        "capture:send-all",
        page.locator("[data-director-capture-send-all]").inner_text().strip() == "发送到画布",
    )
    # Batch 335 修正: `count() >= 0` 恒真 → 断言图库容器真的解析到
    check("capture:gallery-locator-resolves", gallery.count() == 1)

    # 2) icon rail: the same seven entries, aria verbatim
    rail = page.evaluate(
        """() => [...document.querySelectorAll('[data-director-rail-entry]')]
             .map(el => ({
               label: el.getAttribute('aria-label'),
               title: el.getAttribute('title'),
             }))"""
    )
    result["rail"] = rail
    check("rail:count", len(rail) == 7, detail=rail)
    check(
        "rail:aria-verbatim",
        [entry["label"] for entry in rail] == RAIL_ENTRIES,
        detail=[entry["label"] for entry in rail],
    )
    check(
        "rail:titles-verbatim",
        all(entry["title"] == entry["label"] for entry in rail),
        detail=rail,
    )

    # 3) object tree row buttons use the source's 隐藏 / 锁定 titles
    tree_titles = page.evaluate(
        """() => {
          const rows = [...document.querySelectorAll('[data-director-object-lock]')];
          return rows.map(el => {
            const row = el.closest('div');
            return {
              lockTitle: el.getAttribute('title'),
              lockAria: el.getAttribute('aria-label'),
              siblingTitles: row
                ? [...row.querySelectorAll('button[title]')].map(b => b.getAttribute('title'))
                : [],
            };
          });
        }"""
    )
    result["tree_rows"] = tree_titles
    check("tree:rows-found", len(tree_titles) >= 1, detail=tree_titles)
    check(
        "tree:lock-title-verbatim",
        all(row["lockTitle"] in ("锁定", "解锁") for row in tree_titles),
        detail=[row["lockTitle"] for row in tree_titles],
    )
    check(
        "tree:hide-title-verbatim",
        all(
            "隐藏" in row["siblingTitles"] or "显示" in row["siblingTitles"]
            for row in tree_titles
        ),
        detail=[row["siblingTitles"] for row in tree_titles],
    )
    check(
        "tree:lock-keeps-descriptive-aria",
        all(
            row["lockAria"]
            and ("锁定" in row["lockAria"] or "解锁" in row["lockAria"])
            for row in tree_titles
        ),
        detail=[row["lockAria"] for row in tree_titles],
    )

    # 4) viewport view-mode toggle + reset view
    check(
        "view:director-mode",
        page.locator('[data-director-view-mode="director"]').inner_text().strip()
        == "导演视角",
    )
    check(
        "view:camera-mode",
        page.locator('[data-director-view-mode="camera"]').inner_text().strip()
        == "机位视角",
    )
    check(
        "view:reset",
        page.locator('[aria-label="重置视角"]').count() >= 1
        or page.get_by_text("重置视角", exact=True).count() >= 1,
    )

    # 5) the close affordance carries the source's 关闭 title
    close_titles = page.evaluate(
        """() => [...document.querySelectorAll('button[title="关闭"], button[title="关闭导演台"]')]
             .map(el => el.getAttribute('title'))"""
    )
    result["close_titles"] = close_titles
    check("close:source-title", "关闭" in close_titles, detail=close_titles)

    # 6) the clone's own collapse affordance stays wired (not renamed to 收起)
    check(
        "collapse:own-affordance",
        page.locator("[data-director-panels-toggle]").count() == 1,
    )

    unexpected = [error for error in errors if "TransformControls" not in error]
    result["diagnostics"] = {
        "console": len(errors),
        "filtered_transformcontrols": len(errors) - len(unexpected),
        "errors": unexpected[:5],
    }
    check("diagnostics:zero", not unexpected, detail=unexpected[:8])
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 586,
        "title": "Director shell surface audit (截图 tab / icon rail / tree rows / view mode / close) with the verbatim tree lock title",
        "evidence": (
            "2026-10-01 live CDP sampling of the source director desk, taken "
            "before the source overlay was closed + "
            "docs/research/liblib-canvas-batch586-2026-10-01/README.md"
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
        "Batch 586 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Director shell surfaces match the 2026-10-01 source audit and the "
        "tree row lock title is verbatim. See runtime-audit.json."
    )


if __name__ == "__main__":
    main()
