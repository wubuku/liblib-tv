#!/usr/bin/env python3
"""Verify Batch 606: the director header's two fixed 280px side columns.

Source-site live sampling 2026-10-01, 1920x1150, director desk open with a
camera selected. Every value below is a measured source fact.

## Measured source structure

The director top region is three things, not one bar:

  * a 52px band, `pointer-events-none absolute inset-x-0 top-0 z-30 h-[52px]`
    1920x52 @(0,0), which carries nothing but the floating view-mode pair
    (batch 605);
  * a **fixed 280px left column**
        header.border-white/8.flex.h-[52px].items-center.border-b
                                                   280x52 @(0,0)
    with exactly three direct children and **zero gaps** (40 + 200 + 40):
        button 关闭   40x40 @(0,5.5)
                     .text-white/72.flex.size-10.shrink-0
                      .items-center.justify-center.hover:text-white
                     icon 16x16 @(12,17.5)
        div          200x22.5 @(40,14.5)
                     .min-w-0.flex-1.truncate.text-[14px]
                      .leading-[22px].text-white/90
        button 收起   40x40 @(240,5.5)  same classes as 关闭
                     icon 16x16 @(252,17.5)
  * a **fixed 280px right column**
        div.flex.shrink-0.items-center.justify-between.h-12.px-3
                                                   280x48 @(1640,0)
    holding a single line — the selected object's name,
    `text-[15px] font-medium text-neutral-50`, measured 45x23.3 @(1652,11.9)
    (x=1652 = 1640 + the column's 12px `px-3`).

The clone previously ran one header-wide 3-column grid at `h-12` with a
`px-2` gutter, a 32x32 `rounded text-[#a3a3a3]` 收起, a redundant
返回画布 button that called the same `closeWorkspace` as 关闭导演台, and no
object name on the right at all.

Changes:
  * header height 48 -> 52, bottom border `white/[0.07]` -> `white/[0.08]`;
  * both side columns become fixed 280px at >=900px (the same breakpoint the
    clone already uses for its panel collapse), fluid below that;
  * 关闭 moves to the far left as the source's single close affordance; the
    redundant 返回画布 is removed (same handler) and `data-close-director`
    moves onto 关闭 so the eight verifiers that click it keep working;
  * 收起 32x32 -> 40x40 with the source's `text-white/72 hover:text-white`
    and a 16px icon;
  * the command feedback moves to the middle grid track (a 280px left column
    cannot hold a `max-w-[220px] ml-3 pl-3` status strip); it is still inside
    the header, so batch 83's containment assertion is unaffected;
  * the right column gains the selected object name.

Not claimed: the source's title slot was also observed carrying a
`border-b border-dashed` inline-edit input (项目名称) plus a 画布 1 chip in a
different snapshot, but those readings were mutually inconsistent with the
three-children/zero-gap structure above (they placed 4+ controls inside a
200px slot, and put 工作流/故事板 *inside* the 收起 button's own box), so they
are treated as an unreliable reading. The clone keeps its batch-587-pinned
`h1`「3D导演台」and the scene name as a second, clone-only line.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT / "docs/research/liblib-canvas-batch606-2026-10-01/runtime-audit.json"
)
SCREENSHOT = ROOT / "docs/design-references/liblib-header-606-1920.png"

VIEWPORT = {"width": 1920, "height": 1150}
COL_W = 280
BTN = 40
ICON = 16


def alpha_of(colour: str) -> float:
    for pattern in (
        r"rgba?\([^)]*?,\s*([0-9.]+)\s*\)$",
        r"oklab\([^)]*?/\s*([0-9.]+)\s*\)",
        r"lab\([^)]*?/\s*([0-9.]+)\s*\)",
    ):
        match = re.search(pattern, colour)
        if match:
            return float(match.group(1))
    return 1.0


READ = """() => {
  const cs = (el) => getComputedStyle(el);
  const at = (el) => { const r = el.getBoundingClientRect();
    return {x: r.x, y: r.y, w: r.width, h: r.height, right: r.right, bottom: r.bottom}; };
  const d = (el) => { const c = cs(el);
    return {tag: el.tagName.toLowerCase(), box: at(el), backgroundColor: c.backgroundColor,
            color: c.color, borderRadius: c.borderRadius, padding: c.padding,
            display: c.display, gap: c.gap, width: c.width,
            borderTopWidth: c.borderTopWidth, borderBottomWidth: c.borderBottomWidth,
            borderBottomColor: c.borderBottomColor,
            fontSize: c.fontSize, lineHeight: c.lineHeight, fontWeight: c.fontWeight,
            height: c.height,
            text: (el.innerText || '').trim().slice(0, 24),
            aria: el.getAttribute('aria-label'), title: el.getAttribute('title'),
            svg: (() => { const s = el.querySelector('svg'); return s ? at(s) : null; })(),
            className: (el.className || '').toString()}; };
  const header = document.querySelector('[data-director-header]');
  if (!header) return {error: 'no header'};
  const inFlow = [...header.children].filter((el) => cs(el).position !== 'absolute');
  const left = inFlow[0] || null;
  const right = inFlow[inFlow.length - 1] || null;
  const name = document.querySelector('[data-director-header-object-name]');
  return {header: d(header), left: left ? d(left) : null,
          leftKids: left ? [...left.children].map(d) : [],
          right: right ? d(right) : null,
          name: name ? d(name) : null,
          closeCount: header.querySelectorAll('[data-close-director]').length};
}"""


def attach_errors(page: Page) -> list[str]:
    errors: list[str] = []
    page.on(
        "console",
        lambda msg: errors.append(f"console.{msg.type}: {msg.text}")
        if msg.type == "error"
        and "TransformControls" not in msg.text
        # dev-server HMR socket noise (the 4317 dev server is shared with
        # other developers and gets restarted underneath us); not an
        # application error
        and "webpack-hmr" not in msg.text
        and "WebSocket" not in msg.text
        else None,
    )
    page.on("pageerror", lambda err: errors.append(f"pageerror: {err}"))
    return errors


def open_director(page: Page) -> None:
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"
    )
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 606" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(900)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {
        "viewport": f"{VIEWPORT['width']}x{VIEWPORT['height']}",
        "checks": [],
    }

    def check(name: str, ok: bool, detail: Any = None) -> None:
        result["checks"].append({"name": name, "ok": bool(ok), "detail": detail})

    errors = attach_errors(page)
    open_director(page)
    page.evaluate(
        """() => {
          const d = window.__director_store.getState();
          const cam = d.objects.find((o) => o.kind === 'camera');
          if (cam) d.selectObject(cam.id);
        }"""
    )
    page.wait_for_timeout(600)

    data = page.evaluate(READ)
    if data.get("error"):
        check("header:mounted", False, detail=data["error"])
        result["diagnostics"] = {"console": errors[:5]}
        return result
    check("header:mounted", True)

    header, left, right = data["header"], data["left"], data["right"]

    # --- the 52px header --------------------------------------------------------
    check(
        "header:52px",
        abs(header["box"]["h"] - 52) < 0.6,
        detail=header["box"]["h"],
    )
    check(
        "header:border-b-1px-white-8",
        header["borderBottomWidth"] == "1px"
        and abs(alpha_of(header["borderBottomColor"]) - 0.08) < 0.01,
        detail=f"{header['borderBottomWidth']} {header['borderBottomColor']}",
    )

    # --- the 280px left column --------------------------------------------------
    check(
        "left:280px-at-origin",
        left is not None
        and abs(left["box"]["w"] - COL_W) < 0.6
        and abs(left["box"]["x"]) < 0.6,
        detail=[left["box"]["w"], left["box"]["x"]] if left else None,
    )
    kids = data["leftKids"]
    check(
        "left:three-children",
        len(kids) == 3,
        detail=[k["tag"] for k in kids],
    )
    if len(kids) == 3:
        close_btn, title, collapse = kids
        for key, btn, expect_x in (("close", close_btn, 0), ("collapse", collapse, 240)):
            check(
                f"left:{key}-40x40",
                abs(btn["box"]["w"] - BTN) < 0.6 and abs(btn["box"]["h"] - BTN) < 0.6,
                detail=[btn["box"]["w"], btn["box"]["h"]],
            )
            check(
                f"left:{key}-at-x-{expect_x}",
                abs(btn["box"]["x"] - expect_x) < 0.6,
                detail=btn["box"]["x"],
            )
            check(
                f"left:{key}-icon-16px",
                btn["svg"] is not None
                and abs(btn["svg"]["w"] - ICON) < 0.6
                and abs(btn["svg"]["h"] - ICON) < 0.6,
                detail=btn["svg"],
            )
            check(
                f"left:{key}-text-white-72",
                abs(alpha_of(btn["color"]) - 0.72) < 0.01,
                detail=btn["color"],
            )
            check(
                f"left:{key}-no-radius",
                btn["borderRadius"] == "0px",
                detail=btn["borderRadius"],
            )
        check(
            "left:title-200px",
            abs(title["box"]["w"] - 200) < 0.6 and abs(title["box"]["x"] - 40) < 0.6,
            detail=[title["box"]["w"], title["box"]["x"]],
        )
        check(
            "left:title-14px-22px",
            title["fontSize"] == "14px" and title["lineHeight"] == "22px",
            detail=f"{title['fontSize']}/{title['lineHeight']}",
        )
        check(
            "left:title-keeps-h1-3D导演台",
            page.evaluate(
                """() => {
                  const h1 = document.querySelector('[data-director-header] h1');
                  return Boolean(h1 && h1.textContent.trim() === '3D导演台');
                }"""
            ),
            detail="batch 587 pins this h1",
        )
        gaps = [
            round(kids[i + 1]["box"]["x"] - (kids[i]["box"]["x"] + kids[i]["box"]["w"]), 2)
            for i in range(len(kids) - 1)
        ]
        check(
            "left:zero-gaps",
            all(abs(g) < 0.6 for g in gaps),
            detail=gaps,
        )

    # --- single close affordance ------------------------------------------------
    check(
        "close:single-affordance",
        data["closeCount"] == 1
        and page.locator('button[aria-label="返回画布"]').count() == 0,
        detail={
            "data-close-director": data["closeCount"],
            "返回画布": page.locator('button[aria-label="返回画布"]').count(),
        },
    )
    check(
        "close:title-关闭",
        page.evaluate(
            """() => [...document.querySelectorAll('[data-director-header] button')]
                 .some((b) => b.getAttribute('title') === '关闭')"""
        ),
        detail="batch 586 requires the source's 关闭 title",
    )

    # --- the 280px right column -------------------------------------------------
    check(
        "right:280px-flush-to-edge",
        right is not None
        and abs(right["box"]["w"] - COL_W) < 0.6
        and abs(right["box"]["x"] - (VIEWPORT["width"] - COL_W)) < 0.6,
        detail=[right["box"]["w"], right["box"]["x"]] if right else None,
    )
    check(
        "right:padding-12",
        right is not None and right["padding"] == "0px 12px",
        detail=right["padding"] if right else None,
    )

    # --- the object name --------------------------------------------------------
    name = data["name"]
    check(
        "name:present-and-15px",
        name is not None and name["fontSize"] == "15px",
        detail=f"{name['box']} {name['fontSize']}" if name else None,
    )
    check(
        "name:at-source-x-1652",
        name is not None and abs(name["box"]["x"] - 1652) < 1.0,
        detail=name["box"]["x"] if name else None,
    )
    check(
        "name:truncated-medium",
        name is not None
        and "truncate" in name["className"]
        and name["fontWeight"] in ("500", "600")
        and "text-neutral-50" in name["className"],
        detail=name["className"][:110] if name else None,
    )
    check(
        "name:reflects-selection",
        bool(name and name["text"])
        and name["text"] == page.evaluate(
            """() => {
              const d = window.__director_store.getState();
              const id = d.selectedObjectIds[0] ?? d.selectedObjectId;
              return d.objects.find((o) => o.id === id)?.name ?? null;
            }"""
        ),
        detail=name["text"] if name else None,
    )

    page.screenshot(path=str(SCREENSHOT), clip={"x": 0, "y": 0, "width": 1920, "height": 58})
    check("no-console-errors", not errors, detail=errors[:5])
    result["measured"] = data
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT)
        try:
            result = run_desktop(page)
        finally:
            browser.close()
    failed = [c for c in result["checks"] if not c["ok"]]
    print(
        f"Batch 606 verification: {len(result['checks']) - len(failed)}"
        f"/{len(result['checks'])} checks passed"
    )
    if failed:
        print("FAILED:", json.dumps(failed, ensure_ascii=False, indent=1))
        raise SystemExit(1)
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {AUDIT_PATH.relative_to(ROOT)}")
    print(f"wrote {SCREENSHOT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
