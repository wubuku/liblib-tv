#!/usr/bin/env python3
"""Verify Batch 605: header view-mode pair + the 「正在跟随」 follow banner.

Source-site live sampling 2026-10-01, 1920x1150, director desk open. Every
value below is a measured source fact.

## 1. The 导演视角 / 机位视角 pair is not a header grid cell

It floats over the viewport, centred:

    div.pointer-events-auto.absolute.left-1/2.top-2.-translate-x-1/2
      div.border-white/8.flex.h-9.items-center.justify-center.gap-0.5
          .overflow-hidden.rounded-xl.border.bg-[#212121].p-0.5.w-[170px]
                                                       170x36 @(875,8)
        ├ button h-8.rounded-[10px].text-[13px].leading-5.transition-colors
        │        .min-w-0.flex-1.px-2.bg-white/10.text-neutral-50
        │                                               81x32 @(878,10)
        └ button ...text-neutral-50.hover:bg-white/10   81x32 @(961,10)

The two buttons are 2px apart (container `gap-0.5`) and carry the **same**
text colour (`text-neutral-50`); only the background distinguishes the
selected one. Neither button has an `aria-label` — the accessible name is the
visible text.

## 2. The 「正在跟随」 banner

While the camera follows a target the source pins an orange banner to the top
centre of the viewport, above everything (z-305):

    div.pointer-events-none.fixed.left-1/2.top-0.z-[305].-translate-x-1/2
        .motion-safe:transition-opacity.motion-safe:duration-200
                                                       173.7x34 @(873.1,0)
      div.flex.items-center.gap-2.rounded-b-xl.border.px-3.py-1.5.text-white
          .shadow-md.pointer-events-none
          background rgb(228,101,37) = #E46525, border 1px #E46525,
          border-radius 0 0 12px 12px
        ├ span.inline-block.size-2.shrink-0.rounded-full.bg-white
        │                                        8x8 @(886.1,13)  static dot
        ├ span.text-sm 「正在跟随」                56x20 @(902.1,7)   14px
        └ span.relative.ml-1.inline-flex
            ├ button[aria-label=退出跟随]
            │   .peer.rounded-full.bg-white.px-2.py-0.5.text-xs.font-medium
            │   .leading-none.text-gray-900.hover:bg-white/90
            │                                       63.7x16 @(970.1,9) 「取消ESC」
            └ span.pointer-events-none.absolute.left-1/2.top-full.z-10.mt-2
                .-translate-x-1/2.whitespace-nowrap.rounded-md.bg-black/90
                .px-2.py-1.text-xs.font-normal.text-white.opacity-0
                .shadow-md.transition-opacity.peer-hover:opacity-100
                                        82.1x24 @(960.9,33) 「按 ESC 退出」

The hint is a `peer-hover` tooltip (opacity-0 at rest). The 8px dot is
**static** (`animation-name: none`) — copied as-is, no breathing animation.

The hint text is a real contract, not decoration: ESC while following exits
follow mode rather than closing the whole desk. The clone's Escape handler
ended in `closeWorkspace()`, so batch 605 inserts a follow-exit branch ahead
of it.

Follow state is keyed on the active camera's `camera.followTargetId`, the same
field the inspector's 跟随目标 select, the timeline's 跟随目标时不可使用预设运镜
guard and the phone-vcam 请先关闭机位跟随 guard already use (store:6308).

Not claimed: the source's 收起 button, 项目名称 inline edit, 画布 1 chip,
发布与分享 / 积分超市 / credit counter — all measured but left for a later
batch, because the clone's header layout around them differs structurally
(the source's left header is a fixed 280px column; the clone's is a 3-column
grid spanning the workspace). The source's two view buttons carry no
`aria-label`; the clone keeps one (identical accessible name).
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
    ROOT / "docs/research/liblib-canvas-batch605-2026-10-01/runtime-audit.json"
)
SCREENSHOT = ROOT / "docs/design-references/liblib-follow-banner-605-1920.png"

VIEWPORT = {"width": 1920, "height": 1150}
SOURCE_ORANGE = "228, 101, 37"
# Measured on the source site (probe60): the 取消 pill inherits
# pointer-events:none, and elementFromPoint at its centre returns the
# 机位视角 button underneath. See the module docstring.
SOURCE_CANCEL_POINTER_EVENTS = "none"


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


def rgb_tuple(colour: str) -> tuple[int, int, int] | None:
    match = re.match(r"rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)", colour)
    if match:
        return tuple(int(round(float(g))) for g in match.groups())  # type: ignore[return-value]
    return None


READ_PAIR = """() => {
  const cs = (el) => getComputedStyle(el);
  const at = (el) => { const r = el.getBoundingClientRect();
    return {x: r.x, y: r.y, w: r.width, h: r.height, right: r.right, bottom: r.bottom}; };
  const read = (el) => { const c = cs(el);
    return {box: at(el), backgroundColor: c.backgroundColor, color: c.color,
            borderRadius: c.borderRadius, padding: c.padding, gap: c.gap,
            display: c.display, position: c.position, zIndex: c.zIndex,
            width: c.width, fontSize: c.fontSize, lineHeight: c.lineHeight,
            borderTopWidth: c.borderTopWidth, borderTopColor: c.borderTopColor,
            borderBottomLeftRadius: c.borderBottomLeftRadius,
            borderBottomRightRadius: c.borderBottomRightRadius,
            opacity: c.opacity, animationName: c.animationName,
            className: (el.className || '').toString()}; };
  const group = document.querySelector('[aria-label="导演台视角"]');
  if (!group) return {error: 'no view group'};
  const shell = group.firstElementChild;
  const a = document.querySelector('[data-director-view-mode="director"]');
  const b = document.querySelector('[data-director-view-mode="camera"]');
  return {group: read(group), shell: shell ? read(shell) : null,
          a: a ? read(a) : null, b: b ? read(b) : null};
}"""

READ_BANNER = """() => {
  const cs = (el) => getComputedStyle(el);
  const at = (el) => { const r = el.getBoundingClientRect();
    return {x: r.x, y: r.y, w: r.width, h: r.height, right: r.right, bottom: r.bottom}; };
  const read = (el) => { const c = cs(el);
    return {box: at(el), backgroundColor: c.backgroundColor, color: c.color,
            borderRadius: c.borderRadius, padding: c.padding, gap: c.gap, margin: c.margin,
            position: c.position, zIndex: c.zIndex, opacity: c.opacity,
            pointerEvents: c.pointerEvents,
            fontSize: c.fontSize, fontWeight: c.fontWeight, lineHeight: c.lineHeight,
            borderTopWidth: c.borderTopWidth, borderTopColor: c.borderTopColor,
            borderBottomLeftRadius: c.borderBottomLeftRadius,
            borderBottomRightRadius: c.borderBottomRightRadius,
            animationName: c.animationName,
            className: (el.className || '').toString()}; };
  const banner = document.querySelector('[data-director-follow-banner]');
  if (!banner) return {present: false};
  const panel = banner.firstElementChild;
  const dot = panel ? panel.children[0] : null;
  const label = panel ? panel.children[1] : null;
  const holder = panel ? panel.children[2] : null;
  const cancel = holder ? holder.querySelector('button') : null;
  // the hint is a DIRECT child span of the holder; `querySelector('span')`
  // would match the smaller <span>ESC</span> inside the button instead
  const hint = holder
    ? [...holder.children].find((c) => c.tagName.toLowerCase() === 'span') ?? null
    : null;
  return {present: true, banner: read(banner),
          panel: panel ? read(panel) : null,
          dot: dot ? read(dot) : null, label: label ? read(label) : null,
          cancel: cancel ? read(cancel) : null, hint: hint ? read(hint) : null,
          labelText: label ? (label.innerText || '').trim() : null,
          cancelText: cancel ? (cancel.innerText || '').trim() : null,
          hintText: hint ? (hint.innerText || '').trim() : null,
          cancelAria: cancel ? cancel.getAttribute('aria-label') : null};
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
          store.addNode("script-execution", { title: "Batch 605" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(900)


def set_follow(page: Page, on: bool) -> None:
    """Drive the active camera's followTargetId through the real store action."""
    ok = page.evaluate(
        """(enable) => {
          const d = window.__director_store.getState();
          const camera = d.objects.find((o) => o.kind === 'camera');
          if (!camera) return 'no-camera';
          const target = d.objects.find((o) => o.kind !== 'camera');
          if (!target) return 'no-target';
          d.updateCamera(camera.id, { followTargetId: enable ? target.id : null });
          return 'ok';
        }""",
        on,
    )
    if ok != "ok":
        raise AssertionError(f"could not drive follow state: {ok}")
    page.wait_for_timeout(400)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {
        "viewport": f"{VIEWPORT['width']}x{VIEWPORT['height']}",
        "checks": [],
    }

    def check(name: str, ok: bool, detail: Any = None) -> None:
        result["checks"].append({"name": name, "ok": bool(ok), "detail": detail})

    errors = attach_errors(page)
    open_director(page)

    # --- 1. the view-mode pair -------------------------------------------------
    pair = page.evaluate(READ_PAIR)
    if pair.get("error"):
        check("pair:mounted", False, detail=pair["error"])
        result["diagnostics"] = {"console": errors[:5]}
        return result
    check("pair:mounted", True)

    group, shell, a, b = pair["group"], pair["shell"], pair["a"], pair["b"]

    check(
        "pair:floated-left-1/2-top-2",
        group["position"] == "absolute"
        and "left-1/2" in group["className"]
        and "top-2" in group["className"]
        and "-translate-x-1/2" in group["className"],
        detail=group["className"][:150],
    )
    check(
        "pair:shell-170x36",
        shell is not None
        and abs(shell["box"]["w"] - 170) < 0.6
        and abs(shell["box"]["h"] - 36) < 0.6,
        detail=[shell["box"]["w"], shell["box"]["h"]] if shell else None,
    )
    check(
        "pair:shell-rounded-xl-bg-212121",
        shell is not None
        and shell["borderRadius"] == "12px"
        and rgb_tuple(shell["backgroundColor"]) == (33, 33, 33),
        detail=f"{shell['borderRadius']} {shell['backgroundColor']}" if shell else None,
    )
    check(
        "pair:shell-border-1px-white-8",
        shell is not None
        and shell["borderTopWidth"] == "1px"
        and abs(alpha_of(shell["borderTopColor"]) - 0.08) < 0.01,
        detail=f"{shell['borderTopWidth']} {shell['borderTopColor']}" if shell else None,
    )
    check(
        "pair:shell-padding-2-gap-2",
        shell is not None
        and shell["padding"] == "2px"
        and shell["gap"] == "2px",
        detail=f"padding={shell['padding']} gap={shell['gap']}" if shell else None,
    )
    for key, btn in (("a", a), ("b", b)):
        check(
            f"pair:{key}-81x32",
            btn is not None
            and abs(btn["box"]["w"] - 81) < 0.6
            and abs(btn["box"]["h"] - 32) < 0.6,
            detail=[btn["box"]["w"], btn["box"]["h"]] if btn else None,
        )
        check(
            f"pair:{key}-rounded-10px",
            btn is not None and btn["borderRadius"] == "10px",
            detail=btn["borderRadius"] if btn else None,
        )
        check(
            f"pair:{key}-font-13px-20px",
            btn is not None
            and btn["fontSize"] == "13px"
            and btn["lineHeight"] == "20px",
            detail=f"{btn['fontSize']}/{btn['lineHeight']}" if btn else None,
        )
    check(
        "pair:gap-2px",
        a is not None and b is not None
        and abs((b["box"]["x"] - a["box"]["right"]) - 2) < 0.6,
        detail=round(b["box"]["x"] - a["box"]["right"], 2) if a and b else None,
    )
    # selected = bg-white/10, unselected = transparent; same text colour
    check(
        "pair:selected-bg-white-10",
        a is not None and abs(alpha_of(a["backgroundColor"]) - 0.1) < 0.01,
        detail=a["backgroundColor"] if a else None,
    )
    check(
        "pair:unselected-transparent",
        b is not None and alpha_of(b["backgroundColor"]) == 0.0,
        detail=b["backgroundColor"] if b else None,
    )
    check(
        "pair:same-text-colour",
        a is not None and b is not None and a["color"] == b["color"],
        detail=[a["color"], b["color"]] if a and b else None,
    )
    check(
        "pair:aria-pressed-mutually-exclusive",
        page.locator('[data-director-view-mode][aria-pressed="true"]').count() == 1,
    )

    # --- 2. the follow banner --------------------------------------------------
    before = page.evaluate(READ_BANNER)
    check("banner:hidden-without-follow", before.get("present") is False,
          detail="no followTargetId -> no banner")

    set_follow(page, True)
    on = page.evaluate(READ_BANNER)
    check("banner:shown-while-following", on.get("present") is True)
    if on.get("present"):
        banner, panel = on["banner"], on["panel"]
        check(
            "banner:fixed-top-0-z-305",
            banner["position"] == "fixed"
            and "top-0" in banner["className"]
            and banner["zIndex"] == "305",
            detail=f"{banner['position']} z={banner['zIndex']}",
        )
        check(
            "banner:pointer-events-none",
            "pointer-events-none" in banner["className"]
            and panel is not None
            and "pointer-events-none" in panel["className"],
        )
        check(
            "banner:panel-orange-#E46525",
            panel is not None
            and rgb_tuple(panel["backgroundColor"]) == (228, 101, 37)
            and rgb_tuple(panel["borderTopColor"]) == (228, 101, 37),
            detail=f"{panel['backgroundColor']} {panel['borderTopColor']}" if panel else None,
        )
        check(
            "banner:panel-rounded-b-12",
            panel is not None
            and panel["borderBottomLeftRadius"] == "12px"
            and panel["borderBottomRightRadius"] == "12px"
            and float(panel["borderRadius"].split()[0].rstrip("px")) == 0,
            detail=panel["borderRadius"] if panel else None,
        )
        check(
            "banner:panel-padding-6-12",
            panel is not None and panel["padding"] == "6px 12px",
            detail=panel["padding"] if panel else None,
        )
        check(
            "banner:dot-8px-static-white",
            on["dot"] is not None
            and abs(on["dot"]["box"]["w"] - 8) < 0.6
            and abs(on["dot"]["box"]["h"] - 8) < 0.6
            and rgb_tuple(on["dot"]["backgroundColor"]) == (255, 255, 255)
            and on["dot"]["animationName"] == "none",
            detail=f"{on['dot']['box']} {on['dot']['backgroundColor']} "
            f"anim={on['dot']['animationName']}" if on["dot"] else None,
        )
        check(
            "banner:label-text",
            on["labelText"] == "正在跟随"
            and on["label"] is not None
            and on["label"]["fontSize"] == "14px",
            detail=f"{on['labelText']!r} {on['label']['fontSize'] if on['label'] else None}",
        )
        check(
            "banner:cancel-white-pill",
            on["cancel"] is not None
            and float(on["cancel"]["borderRadius"].rstrip("px")) >= 8
            and rgb_tuple(on["cancel"]["backgroundColor"]) == (255, 255, 255)
            and on["cancel"]["padding"] == "2px 8px"
            and on["cancel"]["fontSize"] == "12px"
            and on["cancel"]["fontWeight"] == "500",
            detail=f"{on['cancel']['borderRadius']} {on['cancel']['backgroundColor']} "
            f"{on['cancel']['padding']} {on['cancel']['fontSize']}/"
            f"{on['cancel']['fontWeight']}" if on["cancel"] else None,
        )
        check(
            "banner:cancel-aria-退出跟随",
            on["cancelAria"] == "退出跟随",
            detail=on["cancelAria"],
        )
        check(
            "banner:cancel-text-取消ESC",
            (on["cancelText"] or "").replace(" ", "") == "取消ESC",
            detail=on["cancelText"],
        )
        check(
            "banner:hint-text-按ESC退出",
            (on["hintText"] or "").replace(" ", "") == "按ESC退出",
            detail=on["hintText"],
        )
        check(
            "banner:hint-hidden-until-peer-hover",
            on["hint"] is not None
            and abs(float(on["hint"]["opacity"]) - 0.0) < 0.01
            and "peer-hover:opacity-100" in on["hint"]["className"],
            detail=f"opacity={on['hint']['opacity']}" if on["hint"] else None,
        )
        check(
            "banner:cancel-pointer-events-auto",
            on["cancel"] is not None
            and on["cancel"]["pointerEvents"] == "auto",
            # SOURCE_POINTER_EVENTS_FACT was measured on the source site with
            # /tmp/src593/probe60.py, not read back from the clone.
            detail="deliberate deviation: the source's own 取消 pill inherits "
            f"pointer-events:{SOURCE_CANCEL_POINTER_EVENTS} from the banner "
            "panel (panel and banner both write pointer-events-none, the button "
            "does not re-enable it), and elementFromPoint at the pill centre "
            "lands on the 机位视角 button underneath — so the source's cancel is "
            "unclickable and its peer-hover hint can never appear. Geometry and "
            "styling are copied verbatim; only hit-testing is opened.",
        )
        check(
            "banner:hit-testable-cancel",
            page.evaluate(
                """(pt) => {
                  const el = document.elementFromPoint(pt.x, pt.y);
                  return Boolean(el && el.closest('[data-director-follow-cancel]'));
                }""",
                {"x": on["cancel"]["box"]["x"] + on["cancel"]["box"]["w"] / 2,
                 "y": on["cancel"]["box"]["y"] + on["cancel"]["box"]["h"] / 2},
            ),
        )
        page.screenshot(path=str(SCREENSHOT))

    # --- 3. the cancel button really exits follow ------------------------------
    page.locator("[data-director-follow-cancel]").click()
    page.wait_for_timeout(400)
    after = page.evaluate(READ_BANNER)
    check("banner:click-cancel-exits", after.get("present") is False)
    check(
        "follow:target-cleared",
        page.evaluate(
            """() => {
              const d = window.__director_store.getState();
              const camera = d.objects.find((o) => o.id === d.activeCameraId);
              return (camera?.camera?.followTargetId ?? null) === null;
            }"""
        ),
    )

    # --- 4. ESC exits follow instead of closing the whole desk -----------------
    set_follow(page, True)
    check(
        "follow:shown-again",
        page.evaluate(READ_BANNER).get("present") is True,
    )
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)
    check(
        "esc:exits-follow-not-desk",
        page.evaluate(READ_BANNER).get("present") is False
        and page.locator("[data-director-workspace]").count() == 1,
        detail="ESC clears followTargetId and leaves the desk open",
    )

    check("no-console-errors", not errors, detail=errors[:5])
    result["measured"] = {"pair": pair, "bannerOn": on}
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
        f"Batch 605 verification: {len(result['checks']) - len(failed)}"
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
