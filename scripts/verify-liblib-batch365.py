#!/usr/bin/env python3
"""Verify Batch 365: 画布右键菜单的 backdrop 关闭路径从未被验证过。

## 怎么找到的

Batch 364 建立了「覆盖普查」(`probe_liblib_batch364_coverage.py`): 取每个画布
组件源码里的 `data-*` 标记, 看有没有 liblib 门禁引用过。结果 UNCOVERED = 0,
PARTIAL = 10。逐个核实 PARTIAL 的漏网标记时, 落到 `CanvasContextMenu` 的
`canvas-context-backdrop` —— 它是该组件**唯一**没被任何门禁引用的标记。

`CanvasContextMenu` 的其余标记全部有门禁覆盖(5 个门禁引用了它):

| 标记 | 覆盖它的门禁 |
|---|---|
| `canvas-context-menu` | 172 / 173 / 179 / 185 / 187 |
| `canvas-context-item` | 172 / 173 / 179 / 185 / 187 |
| `canvas-context-variant` | 172 / 173 |
| **`canvas-context-backdrop`** | **无** |

**唯独漏掉的, 恰恰是最基础的那条交互** —— 「点了菜单外面, 菜单会关掉」。
菜单的打开/尺寸/项序/快捷键都验了, 关闭路径没验。

## 为什么这条值得单独立门禁

它是画布右键菜单**唯一**的「逃逸方式」: 菜单一开, backdrop 盖住整个视口
(`fixed inset-0 z-[62]`, 菜单在 z-[63])。用户想取消只有两条路 ——

1. 点菜单外(backdrop 的 `onMouseDown`)
2. 在菜单外右键(backdrop 的 `onContextMenu` → preventDefault + onClose)

这两条路任一坏掉, 菜单就**卡死在屏幕上**, 除非刷新页面。而它们既无门禁,
也从未被任何普查扫到(普查只查「有没有 handler」, 而这两个 handler 是在的 ——
问题不在于缺失 handler, 而在于**没人验证过它们真的有效**)。

这与 batch 357-364 那一类缺陷相反: 那批是「声明了却没接线」, 这批是
「接了线却没人确认它通」。

## 判据

防假零优先: 菜单**必须真的打开**才测关闭, 打不开直接红 —— 不许报「0 问题」。
另外双向覆盖两条关闭路径, 并确认 backdrop 盖住的是**整个视口**(而不是
只盖菜单周围一小块 —— 那种实现下点「菜单外」会点到画布而不是 backdrop)。
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT = ROOT / "docs" / "research" / "liblib-batch365-2026-10-01" / "runtime-audit.json"

MENU = "[data-canvas-context-menu]"
BACKDROP = "[data-canvas-context-backdrop]"


def blank_point(page: Page) -> tuple[int, int]:
    """画布空白处(避开节点)的坐标。"""
    vw, vh = page.viewport_size["width"], page.viewport_size["height"]
    return int(vw * 0.78), int(vh * 0.82)


def open_menu(page: Page) -> bool:
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(1500)
    page.keyboard.press("Alt+Shift+F")
    page.wait_for_timeout(600)
    bx, by = blank_point(page)
    page.mouse.click(bx, by, button="right")
    page.wait_for_timeout(450)
    return page.locator(MENU).count() == 1


def main() -> int:
    audit: dict[str, object] = {"checks": [], "errors": {"console": [], "page": [], "request": []}}
    checks: list[dict[str, object]] = audit["checks"]  # type: ignore[assignment]
    errs: dict[str, list] = audit["errors"]  # type: ignore[assignment]

    def check(name: str, ok: bool, detail: object = None) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("console", lambda m: m.type == "error" and errs["console"].append(m.text))
        page.on("pageerror", lambda e: errs["page"].append(str(e)))
        page.on("requestfailed", lambda r: errs["request"].append(r.url))

        # ---- 1. 防假零: 菜单必须真的打开 ----
        if not open_menu(page):
            check("menu:really-opens", False, "右键空白处未打开菜单(不是 0 问题)")
            browser.close()
            return report(audit)
        check("menu:really-opens", True)

        # ---- 2. backdrop 必须盖住整个视口 ----
        bd = page.locator(BACKDROP)
        check("backdrop:exists", bd.count() == 1, f"count={bd.count()}")
        if bd.count() == 1:
            b = bd.bounding_box()
            vw, vh = page.viewport_size["width"], page.viewport_size["height"]
            covers = b is not None and abs(b["x"]) <= 1 and abs(b["y"]) <= 1 \
                and abs(b["width"] - vw) <= 1 and abs(b["height"] - vh) <= 1
            check("backdrop:covers-full-viewport", covers,
                  {"box": b, "viewport": [vw, vh]})
            # 菜单必须在 backdrop 之上, 否则点不到菜单项
            layers = page.evaluate(
                """(menuSel) => {
                  const m = document.querySelector(menuSel);
                  const b = document.querySelector('[data-canvas-context-backdrop]');
                  return {menuZ: m ? getComputedStyle(m).zIndex : null,
                          backdropZ: b ? getComputedStyle(b).zIndex : null};
                }""",
                MENU,
            )
            audit["layers"] = layers
            check("menu:above-backdrop",
                  layers["menuZ"] is not None and layers["backdropZ"] is not None
                  and int(layers["menuZ"]) > int(layers["backdropZ"]), layers)

        # ---- 3. 关闭路径 A: 点菜单外(backdrop 的 onMouseDown) ----
        page.mouse.click(blank_point(page)[0], blank_point(page)[1])
        page.wait_for_timeout(400)
        check("close:click-outside-backdrop", page.locator(MENU).count() == 0,
              "点菜单外后菜单未关闭")
        audit["closeByOutsideClick"] = page.locator(MENU).count() == 0

        # ---- 4. 关闭路径 B: 在菜单外右键(onContextMenu → preventDefault + close) ----
        if not open_menu(page):
            check("close:right-click-outside", False, "第二次打开失败, 未测(不是 0 问题)")
        else:
            bx, by = blank_point(page)
            page.mouse.click(bx, by, button="right")
            page.wait_for_timeout(400)
            closed = page.locator(MENU).count() == 0
            check("close:right-click-outside", closed, "菜单外右键后菜单未关闭")
            audit["closeByOutsideRightClick"] = closed
            # 关键: onContextMenu 里 preventDefault 了, 浏览器原生菜单不该弹出。
            # 这里无法直接断言原生菜单, 但断言**没有**顺带打开一个新的菜单态
            # (preventDefault 失效的话, page 的 contextmenu 会走 window handler)
            check("close:no-reopen-loop", page.locator(MENU).count() == 0,
                  "菜单外右键后又打开了菜单, onContextMenu 的 preventDefault 可能失效")

        page.screenshot(path=str(AUDIT.parent / "canvas-context.png"))
        browser.close()

    return report(audit)


def report(audit: dict) -> int:
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    failed = [c for c in audit["checks"] if not c["ok"]]  # type: ignore[union-attr]
    errs = audit["errors"]
    noisy = [e for e in list(errs["console"]) + list(errs["page"])  # type: ignore[index]
             if "ERR_ABORTED" not in e and "WebSocket" not in e]
    if failed:
        print(f"Batch 365: {len(audit['checks']) - len(failed)}/{len(audit['checks'])} checks passed")  # type: ignore[arg-type]
        print("FAILED:", json.dumps(failed, ensure_ascii=False, indent=1))
    if noisy:
        print("DIAGNOSTICS:", json.dumps(noisy[:5], ensure_ascii=False, indent=1))
    if failed or noisy:
        return 1
    print(f"Batch 365 verification passed: {len(audit['checks'])} checks. "  # type: ignore[arg-type]
          "Canvas context menu backdrop covers the viewport, sits below the menu, "
          "and both escape paths (outside click, outside right-click) close it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
