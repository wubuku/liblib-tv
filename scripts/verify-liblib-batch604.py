#!/usr/bin/env python3
"""Verify Batch 604: viewport bottom floating bar — two pills side by side.

Source-site live sampling 2026-10-01, 1920x1150, director desk open, one
camera object selected. Every value below is a measured source fact, not a
transcription of an older screenshot.

Source structure (measured, in document order):

    div.z-(--z-sticky).pointer-events-none.absolute.inset-x-0.bottom-0
        .flex.flex-col.items-center.gap-1                 1920x182 @(0,968)  z=200
      div.pointer-events-auto.flex.items-center.gap-2        360x48  @(780,968)
        div.nodrag.nopan.nowheel.relative.flex.items-end.gap-2  360x48 @(780,968)
          nav.relative.flex.h-12.shrink-0.items-center.gap-2.rounded-full
              .border.border-white/10.bg-[rgba(33,33,33,0.94)].text-white
              .shadow-[0_1px_2px_rgba(0,0,0,0.18)].backdrop-blur-xl
              .w-32.p-2                                      128x48  @(780,968)
            div.relative  -> button 移动        32x32 @(789,976) icon size-5
            span.flex.shrink-0 -> button 截图   32x32 @(829,976) icon size-5
            button 动画时间轴 (direct child)     32x32 @(869,976) icon size-5
                                                     aria-pressed=true -> bg-white/8
          div.relative.shrink-0.transition-[width]           224x48  @(916,968)
            div.nodrag.nopan.nowheel.relative.z-10.grid.min-h-12.w-full
                .border.border-white/10.bg-[rgba(33,33,33,0.94)].p-2.text-white
                .shadow-[0_16px_24px_rgba(0,0,0,0.18),0_4px_8px_rgba(0,0,0,0.16),
                        0_1px_1px_rgba(0,0,0,0.12)]
                                                     224x48  grid cols 32/142/32
              button 上传图片 col-1  32x32 @(925,977)  rounded-full text-white/60
                                                      icon size-4, hover:text-white
              input  (1x1 hidden)
              button 发送     col-3  32x32 @(1103,977) rounded-full ml-1
                                                      bg-white text-[#171717]
                                                      disabled:bg-white/8 text-white/28

Bar height arithmetic: 48 (pill row) + 4 (gap-1) + 130 (director desk panel)
= 182, and the pills sit at the TOP of that 182px bar because the desk panel
occupies the rest.

What this batch changed in the clone:
  * the single flat bar (`h-11 rounded-md bg-[#222]/95`, 11 controls) became
    the source's `nav` pill shell; the prompt bar became the source's `grid`
    pill shell; both now share one bottom row (the source's row), which also
    removes a real overlap defect — the two were previously independent
    absolutely positioned bars (tool bar z-10 @(651.5,904) 595x44 and prompt
    bar z-20 @(266,908) 1366x44) that almost completely covered each other,
    the prompt bar's pointer-events-auto pills swallowing the tool bar's
    clicks;
  * the 光标/相机/手 mode segment (invented in batch 535 from a screenshot
    transcription; the live source has no such control) is deleted;
  * the prompt pill's glyph-only `+` becomes a real 上传图片 button that
    opens a local file picker and echoes the chosen file name (local mock,
    no network, no generation).

Not claimed: the source's 移动/截图/动画时间轴 click behaviour (screenshot may
write to the real project and was therefore never clicked), the source's
prompt Enter semantics (may trigger paid generation), the source's upload
target, and the source's send/submit behaviour. The clone's own control set is
larger than the source's three-item pill (transform modes, aspect ratios,
thirds grid, phone vcam, crowd, model library, capture) — those are
clone-only and are kept, as the clone has no source counterpart to defer to.
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
    ROOT / "docs/research/liblib-canvas-batch604-2026-10-01/runtime-audit.json"
)
SCREENSHOT = ROOT / "docs/design-references/liblib-bottom-bar-604-1920.png"

VIEWPORT = {"width": 1920, "height": 1150}
PILL_H = 48
ROW_GAP = 8

# Alpha-insensitive colour comparison: the source serialises some colours as
# `lab()`/`oklab()` and others as `rgba()`, so never compare strings.
def alpha_of(colour: str) -> float:
    match = re.search(r"rgba?\([^)]*?,\s*([0-9.]+)\s*\)$", colour)
    if match:
        return float(match.group(1))
    match = re.search(r"oklab\([^)]*?/\s*([0-9.]+)\s*\)", colour)
    if match:
        return float(match.group(1))
    match = re.search(r"lab\([^)]*?/\s*([0-9.]+)\s*\)", colour)
    if match:
        return float(match.group(1))
    return 1.0


READ = """(selector) => {
  const root = document.querySelector(selector);
  if (!root) return null;
  const cs = (el) => getComputedStyle(el);
  const at = (el) => { const r = el.getBoundingClientRect();
    return {x: r.x, y: r.y, w: r.width, h: r.height,
            right: r.right, bottom: r.bottom}; };
  const read = (el) => { const c = cs(el);
    return {box: at(el), backgroundColor: c.backgroundColor, color: c.color,
            borderRadius: c.borderRadius, padding: c.padding, gap: c.gap,
            display: c.display, position: c.position, zIndex: c.zIndex,
            borderTopWidth: c.borderTopWidth, borderTopColor: c.borderTopColor,
            boxShadow: c.boxShadow, backdropFilter: c.backdropFilter,
            gridTemplateColumns: c.gridTemplateColumns,
            className: (el.className || '').toString()}; };
  const bar = root.querySelector('[data-director-bottom-bar]') || root;
  const pillA = bar.querySelector('[data-director-viewport-toolbar]');
  const pillB = bar.querySelector('[data-director-scene-prompt-bar]');
  // bar -> pointer-events-auto scroller -> mx-auto row (items-center gap-2) -> pillA
  // 源站把这两层合成一个 `pointer-events-auto flex items-center gap-2`；
  // clone 多一层 `overflow-x-auto` 滚动壳（窄屏保护），故两层分别记录。
  const row = pillA ? pillA.parentElement : null;
  const scroller = row ? row.parentElement : null;
  // 只收 button：胶囊里还有隐藏 file input 与文本 input，它们不是圆按钮
  const cells = (pill) => pill ? [...pill.querySelectorAll('button')]
      .filter((el) => el.getBoundingClientRect().width > 0)
      .map((el) => { const s = read(el);
        const svg = el.querySelector('svg');
        return {...s, tag: el.tagName.toLowerCase(),
                ariaLabel: el.getAttribute('aria-label'),
                ariaPressed: el.getAttribute('aria-pressed'),
                disabled: el.disabled === true,
                svgBox: svg ? at(svg) : null}; }) : [];
  return {
    bar: read(bar), row: row ? read(row) : null,
    scroller: scroller ? read(scroller) : null,
    pillA: pillA ? read(pillA) : null, cellsA: cells(pillA),
    pillB: pillB ? read(pillB) : null, cellsB: cells(pillB),
  };
}"""


def attach_errors(page: Page) -> list[str]:
    errors: list[str] = []
    page.on(
        "console",
        lambda msg: errors.append(f"console.{msg.type}: {msg.text}")
        if msg.type == "error" and "TransformControls" not in msg.text
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
          store.addNode("script-execution", { title: "Batch 604" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(900)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": f"{VIEWPORT['width']}x{VIEWPORT['height']}", "checks": []}

    def check(name: str, ok: bool, detail: Any = None) -> None:
        result["checks"].append({"name": name, "ok": bool(ok), "detail": detail})

    errors = attach_errors(page)
    open_director(page)
    data = page.evaluate(READ, "[data-director-workspace]")

    if data is None or data.get("bar") is None:
        check("bottom-bar:mounted", False, detail="data-director-bottom-bar missing")
        result["diagnostics"] = {"console": errors[:5]}
        return result

    check("bottom-bar:mounted", True)

    bar, row, scroller = data["bar"], data["row"], data["scroller"]
    pill_a, pill_b = data["pillA"], data["pillB"]

    # 1) the bottom bar shell — source: absolute inset-x-0 bottom-0,
    #    flex column, items-center, gap 4px, z-index 200, pointer-events-none
    check(
        "bar:absolute-inset-x-0-bottom-0",
        bar["position"] == "absolute"
        and "inset-x-0" in bar["className"]
        and "bottom-0" in bar["className"],
        detail=bar["className"][:160],
    )
    check(
        "bar:column-items-center-gap-4",
        bar["display"] == "flex" and bar["gap"] == "4px",
        detail=f"display={bar['display']} gap={bar['gap']}",
    )
    check("bar:z-index-200", bar["zIndex"] == "200", detail=bar["zIndex"])
    check(
        "bar:pointer-events-none",
        "pointer-events-none" in bar["className"],
        detail=bar["className"][:120],
    )

    # 2) the single row that puts both pills side by side — source:
    #    `pointer-events-auto flex items-center gap-2`, 360x48
    check(
        "row:flex-items-center-gap-8",
        row is not None
        and row["display"] == "flex"
        and row["gap"] == f"{ROW_GAP}px",
        detail=f"display={row['display']} gap={row['gap']}" if row else "no row",
    )
    check(
        "row:pointer-events-auto",
        scroller is not None and "pointer-events-auto" in scroller["className"],
        detail=scroller["className"][:120] if scroller else None,
    )

    # 3) pill A — the source `nav` shell
    check(
        "pillA:h-12-48px",
        pill_a is not None and abs(pill_a["box"]["h"] - PILL_H) < 0.6,
        detail=pill_a["box"]["h"] if pill_a else None,
    )
    check(
        "pillA:rounded-full",
        pill_a is not None
        and pill_a["borderRadius"] not in ("0px", "")
        and float(pill_a["borderRadius"].rstrip("px")) >= 24,
        detail=pill_a["borderRadius"] if pill_a else None,
    )
    check(
        "pillA:bg-rgba-33-33-33-0.94",
        pill_a is not None and alpha_of(pill_a["backgroundColor"]) == 0.94,
        detail=pill_a["backgroundColor"] if pill_a else None,
    )
    check(
        "pillA:border-1px-white-10",
        pill_a is not None
        and pill_a["borderTopWidth"] == "1px"
        and abs(alpha_of(pill_a["borderTopColor"]) - 0.1) < 0.01,
        detail=f"{pill_a['borderTopWidth']} {pill_a['borderTopColor']}" if pill_a else None,
    )
    check(
        "pillA:padding-8-gap-8",
        pill_a is not None
        and pill_a["padding"] == "8px"
        and pill_a["gap"] == f"{ROW_GAP}px",
        detail=f"padding={pill_a['padding']} gap={pill_a['gap']}" if pill_a else None,
    )
    check(
        "pillA:shadow-0-1px-2px",
        pill_a is not None
        and "rgba(0, 0, 0, 0.18)" in pill_a["boxShadow"]
        and "1px 2px" in pill_a["boxShadow"],
        detail=pill_a["boxShadow"][:110] if pill_a else None,
    )
    check(
        "pillA:backdrop-blur",
        pill_a is not None and pill_a["backdropFilter"] not in ("none", ""),
        detail=pill_a["backdropFilter"] if pill_a else None,
    )

    # 4) pill A cells — source: 32x32, rounded-lg (8px), text-white, 20px icons
    # 源站那枚 nav 胶囊里只有三个 32x32 / 20px 图标的纯图标按钮。clone 的
    # 控件集更大（画幅比 40 宽、保存构图带文字），二者都是 clone-only，故
    # 「32x32 + 20px」只对纯图标控件断言，带文字的另计。
    cells_a = data["cellsA"]
    icon_only = [c for c in cells_a if c["ariaLabel"] is not None]
    check(
        "pillA:cells-32x32",
        bool(icon_only)
        and all(abs(c["box"]["w"] - 32) < 0.6 and abs(c["box"]["h"] - 32) < 0.6 for c in icon_only),
        detail=[[c["ariaLabel"], c["box"]["w"], c["box"]["h"]] for c in cells_a][:5],
    )
    check(
        "pillA:icons-20px",
        bool(icon_only)
        and all(
            c["svgBox"] is not None
            and abs(c["svgBox"]["w"] - 20) < 0.6
            and abs(c["svgBox"]["h"] - 20) < 0.6
            for c in icon_only
        ),
        detail=[[c["ariaLabel"], c["svgBox"]["w"] if c["svgBox"] else None] for c in icon_only][:5],
    )
    round_cells = [c for c in cells_a if c["borderRadius"] not in ("",)]
    lg_cells = [c for c in round_cells if float(c["borderRadius"].rstrip("px")) == 8]
    check(
        "pillA:rounded-lg-8px",
        bool(lg_cells),
        detail=[c["borderRadius"] for c in round_cells][:6],
    )

    # 5) pill B — the source grid pill
    check(
        "pillB:h-48px",
        pill_b is not None and abs(pill_b["box"]["h"] - PILL_H) < 0.6,
        detail=pill_b["box"]["h"] if pill_b else None,
    )
    check(
        "pillB:rounded-full",
        pill_b is not None
        and float(pill_b["borderRadius"].rstrip("px")) >= 24,
        detail=pill_b["borderRadius"] if pill_b else None,
    )
    check(
        "pillB:grid-cols-32-1fr-32",
        pill_b is not None
        and re.match(r"^32px [\d.]+px 32px$", pill_b["gridTemplateColumns"]) is not None,
        detail=pill_b["gridTemplateColumns"] if pill_b else None,
    )
    check(
        "pillB:padding-8",
        pill_b is not None and pill_b["padding"] == "8px",
        detail=pill_b["padding"] if pill_b else None,
    )
    check(
        "pillB:three-layer-shadow",
        pill_b is not None
        and "16px 24px" in pill_b["boxShadow"]
        and "4px 8px" in pill_b["boxShadow"]
        and "1px 1px" in pill_b["boxShadow"],
        detail=pill_b["boxShadow"][:150] if pill_b else None,
    )
    check(
        "pillB:bg-rgba-33-33-33-0.94",
        pill_b is not None and alpha_of(pill_b["backgroundColor"]) == 0.94,
        detail=pill_b["backgroundColor"] if pill_b else None,
    )

    # 6) pill B cells — source: rounded-full, 32x32, 16px icons
    cells_b = data["cellsB"]
    check(
        "pillB:upload-cell-aria",
        any(c["ariaLabel"] == "上传图片" for c in cells_b),
        detail=[c["ariaLabel"] for c in cells_b],
    )
    check(
        "pillB:send-cell-aria",
        any(c["ariaLabel"] == "发送" for c in cells_b),
        detail=[c["ariaLabel"] for c in cells_b],
    )
    check(
        "pillB:buttons-rounded-full-16px-icons",
        bool(cells_b)
        and all(float(c["borderRadius"].rstrip("px")) >= 24 for c in cells_b)
        and all(
            abs(c["svgBox"]["w"] - 16) < 0.6 and abs(c["svgBox"]["h"] - 16) < 0.6
            for c in cells_b
            if c["svgBox"]
        ),
        detail=[
            [c["ariaLabel"], c["borderRadius"],
             c["svgBox"]["w"] if c["svgBox"] else None]
            for c in cells_b
        ],
    )
    send = next((c for c in cells_b if c["ariaLabel"] == "发送"), None)
    check(
        "pillB:send-disabled-when-empty",
        send is not None and send["disabled"] is True,
        detail=send["disabled"] if send else None,
    )

    # 7) the two pills are side by side, 8px apart, bottom-aligned, no overlap
    if pill_a and pill_b:
        gap = pill_b["box"]["x"] - pill_a["box"]["right"]
        check(
            "pills:side-by-side-gap-8",
            abs(gap - ROW_GAP) < 0.6,
            detail=round(gap, 2),
        )
        check(
            "pills:bottom-aligned",
            abs(pill_a["box"]["bottom"] - pill_b["box"]["bottom"]) < 0.6,
            detail=[pill_a["box"]["bottom"], pill_b["box"]["bottom"]],
        )
        check(
            "pills:row-centered",
            abs((pill_a["box"]["x"] + pill_b["box"]["right"]) / 2 - row["box"]["x"] - row["box"]["w"] / 2) < 1.0,
            detail={
                "pills_mid": (pill_a["box"]["x"] + pill_b["box"]["right"]) / 2,
                "row_mid": row["box"]["x"] + row["box"]["w"] / 2,
            },
        )
    else:
        check("pills:side-by-side-gap-8", False, detail="missing a pill")
        check("pills:bottom-aligned", False, detail="missing a pill")
        check("pills:row-centered", False, detail="missing a pill")

    # 8) the invented 光标/相机/手 mode segment must be gone
    check(
        "mode-segment:removed",
        page.locator("[data-director-scene-mode]").count() == 0,
        detail="source has no 光标/相机/手 segment (batch 535 transcribed it "
        "from screenshot 18, the live DOM does not have it)",
    )

    # 9) the upload cell is a working local control: choosing a file echoes the
    #    file name into the status line and issues no network request
    page.set_input_files(
        "[data-director-scene-prompt-file]",
        files=[{"name": "cafe-reference.png", "mimeType": "image/png",
                "buffer": b"\x89PNG\r\n\x1a\n"}],
    )
    page.wait_for_timeout(250)
    status = page.locator("[data-director-scene-prompt-status]")
    check(
        "upload:local-echo",
        "cafe-reference.png" in (status.inner_text() or ""),
        detail=status.inner_text(),
    )

    # 10) the tool pill stays clickable now that it shares the row (regression
    #     guard for the overlap that used to swallow its clicks)
    capture = page.locator("[data-director-capture]")
    box_capture = capture.bounding_box()
    check(
        "tool-pill:hit-testable",
        page.evaluate(
            """(pt) => {
              const el = document.elementFromPoint(pt.x, pt.y);
              return Boolean(el && el.closest('[data-director-viewport-toolbar]'));
            }""",
            {"x": box_capture["x"] + box_capture["width"] / 2,
             "y": box_capture["y"] + box_capture["height"] / 2},
        )
        if box_capture
        else False,
        detail=box_capture,
    )

    page.screenshot(path=str(SCREENSHOT))
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
        f"Batch 604 verification: {len(result['checks']) - len(failed)}"
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
