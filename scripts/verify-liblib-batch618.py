#!/usr/bin/env python3
"""Batch 618 — mobile hit-test sweep + the toolbar reserve contract.

Batch 617 censused the desk at 1920x1150 and 1024x800 and found exactly one
blocked control.  It never looked at 390x844, and doing so turned up four
more: 总时长 / 时间单位 / 新建轨道 / 预设运镜 were painted *underneath* the
opaque right strip.

The cause is a CSS detail, not a z-index mistake.  The toolbar kept
`overflow-x-auto` on the header itself and reserved room for the absolutely
positioned 244px right strip with `pr-[260px]`.  Per CSS, padding-right belongs
to the scrollable overflow region, so once the left cluster overflows its
content box it keeps painting all the way out to the padding edge — i.e. into
the reserve that belongs to the strip.  At 1920 the cluster (1044px) fits in its
1392px window and never overflows, so this was invisible; at 390 the window is
390-8-260 = 122px and 922px of toolbar painted under the black block.

This verifier therefore pins three things:

  1. the clip edge sits at the content box, not at the padding box — no control
     in the left cluster may be hit anywhere under the right strip;
  2. the controls that used to be buried are reachable by scrolling the cluster
     (clipped, not covered) and a real mouse click on one of them lands;
  3. desktop is byte-for-byte unchanged — the cluster does not scroll at 1920,
     the toolbar is still 36px, the strip is still 244x36 at the right.

plus the census on three more mobile states (export panel open, timeline
collapsed, and the plain desk).

Read-only apart from clicks inside the clone.  Usage: python3
verify-liblib-batch618.py
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = ROOT / "docs/research/liblib-canvas-batch618-2026-10-01/runtime-audit.json"

MOBILE = {"width": 390, "height": 844}
DESKTOP = {"width": 1920, "height": 1150}

# The rail is hidden below 900px, so 帮助 does not exist in the mobile legs and
# there is no known-blocked exception to allow here.  Any covered control fails.
KNOWN_BLOCKED = ("帮助",)

# Reuse batch 617's census verbatim so the two batches measure the same thing.
_spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(b617)
AUDIT_JS = b617.AUDIT_JS
TRANSIENT_OVERLAYS = b617.TRANSIENT_OVERLAYS

IGNORE_CONSOLE = (
    "The attached 3D object must be a part of the scene graph",
    "webpack-hmr",
    "WebSocket",
    "Failed to load resource",
    "nextjs-dev-overlay",
    "src/components/jimeng/nodes/JimengTextNode.tsx",
    "src/components/jimeng/JimengHelpMenu.tsx",
    # batch 620: another developer's in-flight edit; filtered by path like the
    # two entries above.  Not ours to fix and not ours to revert.
    "src/components/jimeng/nodes/JimengTimelineNode.tsx",
)

# The four controls the first mobile sweep found under the strip.
BURIED = ("总时长", "切换时间单位为", "选中角色、道具或分组后建立轨道", "预设运镜")

TOOLBAR_JS = """() => {
  const at = (el) => { const r = el.getBoundingClientRect();
    return [Math.round(r.x*10)/10, Math.round(r.y*10)/10,
            Math.round(r.width*10)/10, Math.round(r.height*10)/10]; };
  const host = document.querySelector('[data-director-timeline-controls-scroll]');
  const header = document.querySelector('[data-director-timeline-controls]');
  const strip = document.querySelector('[data-director-timeline-strip-right]');
  const cs = (el) => getComputedStyle(el);
  if (!host || !header || !strip) {
    return {host: host ? at(host) : null, header: header ? at(header) : null,
            strip: strip ? at(strip) : null};
  }
  // Sample the strip's own footprint: nothing from the left cluster may be the
  // hit target anywhere in there.  This is the direct statement of the defect —
  // getBoundingClientRect ignores clipping, so box positions alone cannot see
  // it, only the hit test can.
  const y = at(strip)[1] + at(strip)[3] / 2;
  const samples = [];
  for (let x = at(strip)[0] + 2; x < at(strip)[0] + at(strip)[2] - 1; x += 8) {
    const el = document.elementFromPoint(x, y);
    samples.push({x: Math.round(x), inHost: !!(el && host.contains(el)),
                  tag: el ? el.tagName.toLowerCase() : null});
  }
  return {
    host: at(host), header: at(header), strip: at(strip),
    hostOverflowX: cs(host).overflowX, hostOverflowY: cs(host).overflowY,
    headerOverflowX: cs(header).overflowX,
    headerPaddingRight: cs(header).paddingRight,
    hostScrollW: host.scrollWidth, hostClientW: host.clientWidth,
    hostScrollLeft: Math.round(host.scrollLeft),
    needsScroll: host.scrollWidth > host.clientWidth,
    sampleY: Math.round(y), samplesUnderStrip: samples.filter((s) => s.inHost),
    sampleCount: samples.length,
  };
}"""

DESKTOP_TOOLBAR_JS = """() => {
  const at = (el) => { const r = el.getBoundingClientRect();
    return [Math.round(r.x*10)/10, Math.round(r.y*10)/10,
            Math.round(r.width*10)/10, Math.round(r.height*10)/10]; };
  const host = document.querySelector('[data-director-timeline-controls-scroll]');
  const header = document.querySelector('[data-director-timeline-controls]');
  const strip = document.querySelector('[data-director-timeline-strip-right]');
  const first = ['data-director-playback', 'data-director-auto-keyframe',
                 'data-director-loop', 'data-director-add-track']
    .map((d) => document.querySelector('[' + d + ']'))
    .filter(Boolean)
    .map((el) => ({data: el.dataset[Object.keys(el.dataset)[0]],
                   box: at(el), text: (el.textContent || '').trim().slice(0, 10)}));
  return {
    host: at(host), header: at(header), strip: at(strip),
    hostOverflowX: getComputedStyle(host).overflowX,
    hostScrollW: host.scrollWidth, hostClientW: host.clientWidth,
    needsScroll: host.scrollWidth > host.clientWidth,
    headerPaddingRight: getComputedStyle(header).paddingRight,
    // the desktop column must keep batch 614's top edge; the mobile drawer fix
    // is a max-[899px] override and must not leak into this width
    inspector: at(document.querySelector("[aria-label='属性']")),
    first,
  };
}"""


DRAWER_JS = """() => {
  const at = (el) => { const r = el.getBoundingClientRect();
    return [Math.round(r.x*10)/10, Math.round(r.y*10)/10,
            Math.round(r.width*10)/10, Math.round(r.height*10)/10]; };
  const hit = (sel) => { const el = document.querySelector(sel);
    if (!el) return null; const r = el.getBoundingClientRect();
    const h = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
    return h ? (h === el || el.contains(h) ? 'own'
                : h.tagName.toLowerCase() + ':'
                  + (h.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 10))
              : null; };
  return {
    drawer: at(document.querySelector("[aria-label='属性']")),
    tree: at(document.querySelector("[aria-label='场景对象']")),
    scrim: at(document.querySelector("[aria-label='关闭移动端面板']")),
    shotChip: hit('[data-director-shot-option]'),
    shotLabel: hit('[data-director-shot-bar] span'),
    activeShot: document.querySelector('[data-director-shot-bar]')
      ?.getAttribute('data-director-active-shot-id'),
    pressed: document.querySelector('[data-director-shot-option]')
      ?.getAttribute('aria-pressed'),
  };
}"""


def open_desk(page: Page) -> None:
    b617.open_desk(page)


class Verifier:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.result: dict[str, Any] = {}
        self.failures: list[str] = []
        self.count = 0

    def check(self, name: str, ok: bool, detail: Any = "") -> None:
        self.count += 1
        self.result[name] = {"ok": bool(ok), "detail": detail}
        if not ok:
            self.failures.append(name)
        print(("  PASS " if ok else "  FAIL ") + name + (f"  {detail}" if detail else ""))

    def census(self, name: str) -> dict[str, Any]:
        self.page.mouse.move(5, 5)
        self.page.wait_for_timeout(220)
        self.page.evaluate(
            "() => { for (const el of document.querySelectorAll('nextjs-portal'))"
            " el.remove(); }")
        r = dict(self.page.evaluate(AUDIT_JS, list(TRANSIENT_OVERLAYS)))
        r["unexpected"] = [b for b in r["covered"] if b["label"] not in KNOWN_BLOCKED]
        self.result[name] = r
        return r


def scroll_control_into_view(page: Page, selector: str) -> dict[str, Any]:
    """Scroll the cluster just far enough to bring one control into its window.

    Scrolling to the *end* is not good enough: the cluster is 776px of content
    in a 122px window, so the end of the scroll is the tail of the toolbar and
    the control this test wants sits at the far left, off-window.  Centre the
    target instead, then return its post-scroll box for a raw mouse click.
    """
    return page.evaluate(
        """(sel) => {
          const host = document.querySelector('[data-director-timeline-controls-scroll]');
          const el = document.querySelector(sel);
          const hb = host.getBoundingClientRect();
          const r = el.getBoundingClientRect();
          const want = r.x + r.width / 2 - (hb.x + hb.width / 2);
          host.scrollLeft = Math.max(0, Math.min(want, host.scrollWidth - host.clientWidth));
          const r2 = el.getBoundingClientRect();
          return {x: r2.x + r2.width / 2, y: r2.y + r2.height / 2,
                  scrollLeft: Math.round(host.scrollLeft),
                  label: el.getAttribute('aria-label')};
        }""",
        selector,
    )


def run_mobile(browser: Any) -> dict[str, Any]:
    """390x844: the census, the reserve contract, and a real click on a control
    that used to be buried."""
    v = Verifier(browser.new_page(viewport=MOBILE, device_scale_factor=1))
    console: list[str] = []
    errors: list[str] = []
    v.page.on("console", lambda m: console.append(f"{m.type}: {m.text}"[:200])
              if m.type == "error" else None)
    v.page.on("pageerror", lambda e: errors.append(str(e)[:200]))
    open_desk(v.page)

    r = v.census("mobile:census")
    v.check("mobile:audited-a-real-number-of-controls", r["total"] >= 30, detail=r["total"])
    v.check("mobile:no-control-is-covered", not r["unexpected"],
            detail=[(b["label"], b["hitLabel"], b["box"]) for b in r["unexpected"]])

    # the four the first sweep found under the strip must now be merely clipped
    clipped_labels = [b["label"] for b in r["clipped"]]
    still_buried = [b["label"] for b in r["covered"]]
    # Batch 621 迁移（不是放宽）：621 把窄屏工具条改成两行，右格不再浮在
    # 右端、独占第二行，于是这四枚**不再只是「被裁剪」而是完整可见** ——
    # 既不在 covered 里，也不在 clipped 里。合同随之升级：从「至少能滚动
    # 到」变成「开箱即见」。原来那条允许 clipped 的口径是 618 当时的实情，
    # 现在留着就等于允许回到更差的状态。
    v.check("mobile:the-formerly-buried-four-are-now-fully-visible",
            not any(k in lab for lab in clipped_labels for k in BURIED)
            and not any(k in lab for lab in still_buried for k in BURIED),
            detail={"clipped": clipped_labels, "covered": still_buried})
    v.result["mobile:clipped"] = {"count": len(r["clipped"]),
                                  "labels": clipped_labels[:12]}
    # Batch 627 迁移（不是放宽阈值）。`clipped` 从此装了两类东西：
    #   ① 窗口**内**、被自己面板的 overflow 滚下去的 —— 这正是 618 当初在数的，
    #      少是好，所以阈值 20 继续按这一类算；
    #   ② 中心**整个在窗口外**、只能靠横向滚窄屏工具条那 776px 才见得到的 ——
    #      390 下有 84 枚。627 之前它们被普查的 `continue` 静默丢弃，所以从来
    #      不进这个计数。
    # 把 20 抬到 100 能让这一条变绿，但那等于放弃 618 真正想守的东西
    # （「窄屏没有把一大堆控件藏到滚动区后面」），所以按原义取数、新类别单记。
    in_window_clipped = [b for b in r["clipped"] if not b.get("offViewport")]
    v.check("mobile:clipped-count-is-explained",
            len(in_window_clipped) <= 20,
            detail={"inWindowClipped": len(in_window_clipped),
                    "offViewportScrollable": len(r["offViewportScrollable"]),
                    "totalClipped": len(r["clipped"])})

    # the reserve contract
    tb = v.page.evaluate(TOOLBAR_JS)
    v.result["mobile:toolbar"] = tb
    v.check("mobile:the-scroll-host-is-an-inner-cluster",
            tb.get("hostOverflowX") in {"auto", "scroll"}, detail=tb.get("hostOverflowX"))
    v.check("mobile:the-toolbar-itself-no-longer-scrolls",
            tb.get("headerOverflowX") == "visible", detail=tb.get("headerOverflowX"))
    # Batch 621 迁移：621 的两行布局在窄屏取消了给浮在右端的右格留的 260px
    # 预留（右格已独占第二行，不再与左格同行抢位），换成 `pr-2` = 8px。
    # ≥900 的 260px 并没有丢：本文件的 desktop 腿 `desktop:the-reserve-is-
    # still-260px` 与 621 的 `desktop-1920:the-260px-reserve-is-still-there`
    # 各自继续守着那条源站实测值。所以这里断的是「窄屏不该再留 260」。
    v.check("mobile:the-narrow-reserve-is-8px",
            tb.get("headerPaddingRight") == "8px", detail=tb.get("headerPaddingRight"))
    v.check("mobile:the-cluster-does-overflow-at-390", tb.get("needsScroll") is True,
            detail={"clientW": tb.get("hostClientW"), "scrollW": tb.get("hostScrollW")})
    v.check("mobile:nothing-from-the-cluster-is-painted-under-the-strip",
            not tb.get("samplesUnderStrip"),
            detail={"samples": tb.get("sampleCount"),
                    "underStrip": tb.get("samplesUnderStrip")[:6]})

    # a real click on a control that used to be unreachable.  The click is a raw
    # mouse click at the measured centre — no auto-scroll, so if anything were
    # still painted on top the click would land on that instead.
    box = scroll_control_into_view(v.page, "[data-director-time-unit]")
    v.page.wait_for_timeout(200)
    v.result["mobile:unitButton"] = box
    v.page.mouse.click(box["x"], box["y"])
    v.page.wait_for_timeout(500)
    flipped = v.page.evaluate(
        "() => document.querySelector('[data-director-time-unit]')"
        ".getAttribute('aria-label')")
    v.check("mobile:the-buried-unit-toggle-takes-a-real-click",
            flipped != box["label"] and flipped.startswith("切换时间单位为"),
            detail=f"{box['label']} -> {flipped} (scrollLeft={box['scrollLeft']})")
    v.page.mouse.click(box["x"], box["y"])
    v.page.wait_for_timeout(400)

    r2 = v.census("mobile:census-after-scroll")
    v.check("mobile:still-nothing-covered-after-the-click", not r2["unexpected"],
            detail=[(b["label"], b["hitLabel"]) for b in r2["unexpected"]])

    noise = [c for c in console if any(k in c for k in IGNORE_CONSOLE)]
    real_console = [c for c in console if not any(k in c for k in IGNORE_CONSOLE)]
    real_errors = [e for e in errors if not any(k in e for k in IGNORE_CONSOLE)]
    v.check("mobile:no-page-errors", not real_errors, detail=real_errors[:5])
    v.check("mobile:no-console-errors", not real_console, detail=real_console[:5])
    v.result["mobile:diagnostics"] = {"consoleErrors": len(console),
                                      "filtered": len(noise),
                                      "pageErrors": len(errors)}
    v.result["_summary"] = {"checks": v.count, "failures": v.failures}
    v.page.close()
    return v.result


def run_mobile_state(browser: Any, tag: str, setup: str | None,
                     expect: str | None = None) -> dict[str, Any]:
    """Census the desk at 390 in one more state (export panel open, collapsed).

    `expect` is the overlay the setup is supposed to open.  Without it a leg can
    pass while the overlay never appeared — which is exactly what happened to
    this file's export leg until batch 619 pointed it at the right button.
    """
    page = browser.new_page(viewport=MOBILE, device_scale_factor=1)
    v = Verifier(page)
    console: list[str] = []
    errors: list[str] = []
    page.on("console", lambda m: console.append(f"{m.type}: {m.text}"[:200])
            if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)[:200]))
    open_desk(page)
    if setup:
        page.locator(setup).click(timeout=15_000)
        page.wait_for_timeout(700)
    if expect:
        v.check(f"{tag}:the-overlay-actually-opened",
                page.locator(expect).first.is_visible(), detail=expect)
    r = v.census(f"{tag}:census")
    v.check(f"{tag}:audited-a-real-number-of-controls", r["total"] >= 30,
            detail=r["total"])
    v.check(f"{tag}:no-control-is-covered", not r["unexpected"],
            detail=[(b["label"], b["hitLabel"], b["box"]) for b in r["unexpected"]])
    noise = [c for c in console if any(k in c for k in IGNORE_CONSOLE)]
    real_console = [c for c in console if not any(k in c for k in IGNORE_CONSOLE)]
    real_errors = [e for e in errors if not any(k in e for k in IGNORE_CONSOLE)]
    v.check(f"{tag}:no-page-errors", not real_errors, detail=real_errors[:5])
    v.check(f"{tag}:no-console-errors", not real_console, detail=real_console[:5])
    v.result[f"{tag}:diagnostics"] = {"consoleErrors": len(console),
                                      "filtered": len(noise),
                                      "pageErrors": len(errors)}
    v.result["_summary"] = {"checks": v.count, "failures": v.failures}
    page.close()
    return v.result


def run_desktop(browser: Any) -> dict[str, Any]:
    """1920x1150: nothing about the desktop arrangement may have moved."""
    page = browser.new_page(viewport=DESKTOP, device_scale_factor=1)
    v = Verifier(page)
    console: list[str] = []
    errors: list[str] = []
    page.on("console", lambda m: console.append(f"{m.type}: {m.text}"[:200])
            if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)[:200]))
    open_desk(page)
    tb = page.evaluate(DESKTOP_TOOLBAR_JS)
    v.result["desktop:toolbar"] = tb
    v.check("desktop:the-toolbar-is-still-36px", tb["header"][3] == 36,
            detail=tb["header"])
    v.check("desktop:the-toolbar-still-spans-the-full-width", tb["header"][2] == 1920,
            detail=tb["header"])
    v.check("desktop:the-strip-is-still-244x36-at-the-right",
            tb["strip"][2] == 244 and tb["strip"][3] == 36
            and abs(tb["strip"][0] + tb["strip"][2] - 1920) < 0.6,
            detail=tb["strip"])
    v.check("desktop:the-reserve-is-still-260px", tb["headerPaddingRight"] == "260px",
            detail=tb["headerPaddingRight"])
    v.check("desktop:the-cluster-ends-where-the-reserve-begins",
            abs(tb["host"][0] + tb["host"][2] - (1920 - 260)) < 0.6,
            detail={"host": tb["host"], "expectedRight": 1920 - 260})
    v.check("desktop:the-cluster-does-not-scroll-at-1920", tb["needsScroll"] is False,
            detail={"clientW": tb["hostClientW"], "scrollW": tb["hostScrollW"]})
    v.check("desktop:the-source-ordered-controls-are-untouched",
            len(tb["first"]) == 4
            and tb["first"][0]["box"][2] == 26 and tb["first"][1]["box"][2] == 24
            and tb["first"][2]["box"][2] == 26 and tb["first"][3]["box"][2] == 82,
            detail=[(f["data"], f["box"]) for f in tb["first"]])
    v.check("desktop:the-cluster-starts-at-the-toolbar's-content-box",
            abs(tb["host"][0] - 8) < 0.6, detail=tb["host"][0])
    v.check("desktop:the-inspector-column-keeps-its-52px-top",
            tb["inspector"][1] == 52, detail=tb["inspector"])

    r = v.census("desktop:census")
    v.check("desktop:only-the-rails-帮助-is-covered",
            [b["label"] for b in r["covered"]] == list(KNOWN_BLOCKED),
            detail=[b["label"] for b in r["covered"]])
    noise = [c for c in console if any(k in c for k in IGNORE_CONSOLE)]
    real_console = [c for c in console if not any(k in c for k in IGNORE_CONSOLE)]
    real_errors = [e for e in errors if not any(k in e for k in IGNORE_CONSOLE)]
    v.check("desktop:no-page-errors", not real_errors, detail=real_errors[:5])
    v.check("desktop:no-console-errors", not real_console, detail=real_console[:5])
    v.result["_summary"] = {"checks": v.count, "failures": v.failures}
    page.close()
    return v.result


def run_drawer(browser: Any) -> dict[str, Any]:
    """390x844 with the inspector drawer open: the shot bar must stay operable.

    Found by a regression, not by a sweep.  Batch 96 opens this drawer and then
    clicks a shot chip, and that click had been landing only inside a ~50ms
    window: the drawer slides in over 200ms, and once it settles it covers the
    chip.  Sampling the chip's hit target over time showed the drawer at x=131
    (chip clear) at t=0 and x=109 (chip covered) by t=80ms — so the old leg
    passed by winning a race, and this batch's toolbar change was enough to lose
    it.  The scrim (`absolute inset-0`, 88..668) and the tree drawer
    (`top-[88px]`) both already excluded the shot-bar row; only the inspector
    drawer reached up over it via the desktop `-top-9`.
    """
    page = browser.new_page(viewport=MOBILE, device_scale_factor=1)
    v = Verifier(page)
    console: list[str] = []
    errors: list[str] = []
    page.on("console", lambda m: console.append(f"{m.type}: {m.text}"[:200])
            if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)[:200]))
    open_desk(page)
    page.locator("button[aria-label='打开属性面板']").click()
    page.locator("[aria-label='属性'][data-director-mobile-panel-state='open']").wait_for(
        state="visible", timeout=20_000)
    # well past the 200ms slide-in, so this measures the settled layout
    page.wait_for_timeout(1_200)
    page.mouse.move(5, 5)
    page.wait_for_timeout(200)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
    d = page.evaluate(DRAWER_JS)
    v.result["drawer:geometry"] = d
    v.check("drawer:it-starts-below-the-shot-bar-row", d["drawer"][1] == 88,
            detail=d["drawer"])
    v.check("drawer:it-ends-where-the-scrim-ends",
            abs(d["drawer"][1] + d["drawer"][3] - (d["scrim"][1] + d["scrim"][3])) < 0.6,
            detail={"drawer": d["drawer"], "scrim": d["scrim"]})
    v.check("drawer:the-scrim-still-starts-at-88", d["scrim"][1] == 88, detail=d["scrim"])
    v.check("drawer:the-shot-chip-takes-its-own-hit", d["shotChip"] == "own",
            detail=d["shotChip"])
    v.check("drawer:the-shot-label-takes-its-own-hit", d["shotLabel"] == "own",
            detail=d["shotLabel"])
    before = d["activeShot"]
    page.locator("[data-director-shot-option]").first.click(timeout=15_000)
    page.wait_for_timeout(500)
    after = page.evaluate(
        "() => document.querySelector('[data-director-shot-bar]')"
        ".getAttribute('data-director-active-shot-id')")
    pressed = page.evaluate(
        "() => document.querySelector('[data-director-shot-option]')"
        ".getAttribute('aria-pressed')")
    v.check("drawer:the-shot-chip-click-lands-with-the-drawer-open",
            after == before and pressed == "true", detail=f"{before} -> {after} pressed={pressed}")
    noise = [c for c in console if any(k in c for k in IGNORE_CONSOLE)]
    real_console = [c for c in console if not any(k in c for k in IGNORE_CONSOLE)]
    real_errors = [e for e in errors if not any(k in e for k in IGNORE_CONSOLE)]
    v.check("drawer:no-page-errors", not real_errors, detail=real_errors[:5])
    v.check("drawer:no-console-errors", not real_console, detail=real_console[:5])
    v.result["drawer:diagnostics"] = {"consoleErrors": len(console),
                                       "filtered": len(noise),
                                       "pageErrors": len(errors)}
    v.result["_summary"] = {"checks": v.count, "failures": v.failures}
    page.close()
    return v.result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 618,
        "title": "Mobile hit-test sweep at 390x844; move the toolbar's scroll "
                 "host inward so nothing paints under the opaque right strip",
        "date": "2026-10-01",
        "sourceEvidence": [
            "no live source reading: the shared source tab is at 1600x1000 "
            "with the director desk closed by another user (probe616 re-run), "
            "so this batch makes no fidelity claim",
            "/tmp/dbg618.py: batch 617's census re-used at 390x844 — "
            "interactive=41, covered=4 (总时长, 切换时间单位为 s, "
            "选中角色、道具或分组后建立轨道, 预设运镜)",
            "/tmp/dbg618b.py: the hitters are the transparent zoom range "
            "(absolute inset-x-0 opacity-0) and the opaque "
            "div[data-director-timeline-strip-right] (absolute right-0 z-30 "
            "244x36 bg-[#212121])",
            "/tmp/dbg618c.py: scrolling the toolbar to its end clears all four — "
            "reachable, not dead — clientWidth 390 vs scrollWidth 1044",
            "/tmp/dbg618d.py: the export-panel-open and timeline-collapsed "
            "states at 390 are clean; the drawer-open state reports 11 covered, "
            "all of them behind the drawer panel or the drawer scrim itself",
            "/tmp/dbg618f.py (run twice, baseline vs fixed): sampling the shot "
            "chip's hit target while the inspector drawer settles showed the "
            "drawer at x=131 with the chip clear at t=0 and x=109 with the chip "
            "covered by t=80ms — batch 96's mobile shot click only ever landed "
            "inside that ~50ms window",
        ],
        "claims": {
            "cloneDefect": [
                "the toolbar reserved pr-[260px] for the absolutely positioned "
                "244px right strip while keeping overflow-x-auto on the header "
                "itself; padding-right belongs to the scrollable overflow "
                "region, so once the left cluster overflowed its content box it "
                "kept painting out to the padding edge — into the reserve",
                "at 1920 the cluster (1044px) fits its window and never "
                "overflows, so this was invisible; at 390 the window is 122px "
                "and 922px of toolbar painted under an opaque black block, so "
                "four controls were drawn yet unreachable, with no scrollbar "
                "to hint that anything was there",
            ],
            "cloneDecision": [
                "the scroll host moves one level in, to "
                "[data-director-timeline-controls-scroll], so the clip edge is "
                "the content box (x=130 at 390) and overflow content can no "
                "longer reach the reserve",
                "the four controls are now classified clipped — reachable by "
                "scrolling the cluster, exactly as at 1024 — rather than being "
                "redrawn or hidden",
                "the inspector drawer gets max-[899px]:top-0, cancelling the "
                "desktop -top-9 at mobile widths so it starts at 88 like the "
                "scrim (absolute inset-0 -> 88..668) and like the tree drawer "
                "(top-[88px] min-[900px]:top-[52px]). The scrim's own extent "
                "already declared the shot-bar row usable while a drawer is "
                "open; the inspector drawer was the only one of the three that "
                "reached up over it. Desktop keeps -top-9, so batch 614's column "
                "(top 52 / width 281 / bottom at the timeline) is untouched",
            ],
            "contractMigration": [
                "batch 596 asserted the header itself was the horizontal scroll "
                "container (strip:left-cell-scrolls). The contract's meaning "
                "('the left cell scrolls') is unchanged, so the check now reads "
                "the inner cluster's overflowX instead of the header's; the "
                "reason batch 596 gave for keeping the strip outside the header "
                "is unaffected because the strip is still outside it",
            ],
            "notClaimed": [
                "anything about the source at all",
                "the mobile drawer's height is now 580 instead of 616 (it starts "
                "36px lower and still ends at the timeline) — that follows from "
                "matching the scrim, and no reading says a mobile drawer should "
                "be any particular height",
                "the source's own mobile toolbar and drawer arrangement is "
                "unknown; the source's director desk at 390 has never been "
                "sampled",
            ],
        },
    }
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        mobile = run_mobile(browser)
        export_open = run_mobile_state(browser, "export-open",
                                       # the strip's 导出视频到画布 trigger, not the
                                       # header's project-JSON export: the latter
                                       # downloads a file and opens no panel, so
                                       # batch 618's first run of this leg was
                                       # censusing the plain desk under a label
                                       # that claimed otherwise (found by 619)
                                       "[data-director-export-trigger]",
                                       "[data-director-export-panel]")
        collapsed = run_mobile_state(browser, "collapsed",
                                     "[data-director-timeline-collapse]")
        drawer = run_drawer(browser)
        desktop = run_desktop(browser)
        browser.close()
    legs = {"mobile": mobile, "export-open": export_open,
            "collapsed": collapsed, "drawer": drawer, "desktop": desktop}
    total = sum(leg["_summary"]["checks"] for leg in legs.values())
    fails = [f for leg in legs.values() for f in leg["_summary"]["failures"]]
    audit["checks"] = legs
    audit["result"] = f"{total - len(fails)}/{total} passed"
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_PATH, "w", encoding="utf-8") as f:
        json.dump(audit, f, ensure_ascii=False, indent=2)
    print(f"\n{audit['result']}")
    if fails:
        print("FAILED: " + ", ".join(fails))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
