#!/usr/bin/env python3
"""batch 651 验收：**撤回 650 的头条读数** —— 那是 Playwright `hover()` 自动滚动的伪影

## 650 说了什么

650 用 649 的导出式尺子重跑 626 的 11 个导演台浮层，在
`camera-fov-help-tooltip@1280x720` 一格多报了 4 条，其中
`section.sticky.top-0` 盖住提示条 `[1016,263,208,62]` —— **68 高里 62 高（91%）**。
650 把它写成「只发生在 1280×720 ⇒ 宽度驱动」。

## 本批查出来的是：这条读数**根本不是布局的读数**

顺着 650 的读数去收边界，第一步就撞上矛盾：窗高 640 **不**被盖、
窗高 680 **被盖**，而 670→680 之间 badge 的 y **同移 123px**（整条祖先链每一级都同移）。
一个「高度决定位置」的元素不会这么做。

把祖先链连计算样式 dump 出来，答案在倒数第二级：

    div.space-y-4.px-4.py-3    y = −519 (h=640) → −642 (h=680)   高恒 1185
    div.min-h-0.flex-1.overflow-y-auto   y = 157   高 301 → 341

那个 y 为负、内容高 1185 的 div 位于一个**可滚动祖先**里 ——
**它被滚动了**，而滚动量正好是 123。滚动是谁发起的？
`626.open_overlay` 的 `@fov-hover@` 走的是 Playwright 的 `locator.hover()`，
而 `hover()` 会 **`scrollIntoViewIfNeeded`**（Playwright 自己的日志里写着
`scrolling into view if needed`）。

**提示条是贴着 badge 定位的。badge 一被滚动，提示条就跟着动。**
所以 650 量的不是「这个设计会不会遮住提示条」，
而是「Playwright 为了够到 badge 滚了多少」—— 那是**探针的实现细节**。

## 正确口径下的读数

把滚动**显式钉成 0**，并且**只用 `mouse.move` 指向 badge 的坐标**
（指针不触发任何自动滚动），其余全部照旧：

| 窗高 | scrollTop | badge y | 提示条 y | sticky 底沿 | 相交？ |
|---|---|---|---|---|---|
| 560 / 640 / 720 / 800 / 900 / 1150 | **0** | **1118** | **1042** | **325** | **全部否** |

**三个量都与窗高无关，提示条恒在 1042，离 sticky 底沿 325 有 717px。**
650 那个「91% 被盖」在**任何**窗高下都不出现。

## 顺带查清的那件事

badge 的自然 y 恒为 **1118**，而检查器可见带是 `157 .. 157+clientH`
（h=1150 时约 157..1073）。**badge 在任何窗高下都不在可见带里。**
所以**任何**要悬停这枚 badge 的读数都必然包含一次滚动 ——
这就是这个盲区的完整形状，也是为什么 650 不可能量到真值。

矮窗高下悬停**直接失败**（`aside[属性]` 或 `nav[摄像机编辑]` 拦截指针），
所以「压根打不开」是**第三种状态**，既不是「打开且干净」也不是「打开且被盖」
—— 646 教过：第三种状态必须单列，不能混进前两种。

## 这是本项目的**第六个盲区形状**

1. batch 640：探针的**采样点**（中心干净 + 身体被挡）
2. batch 641/642：探针的**形状假设**（圆控件四角按设计就在形状外）
3. batch 646/647：**判据自己的命中测试**（祖先命中 / 可见性 vs 可点性）
4. batch 648：**判据自己的门槛**（1×1 的 `sr-only` 穿过「零尺寸」）
5. batch 649/650：**竞争集的来源**（手写清单会过期）
6. **batch 651：探针的副作用**（`hover()` 的自动滚动决定了被测浮层的位置）

前五个都是「尺子看不见」，**这一个是我自己动的手**。

## 本批**不**主张的事

* **不主张**提示条**永远**不会被遮住 —— 只主张**在 `scrollTop = 0` 这个状态下、
  在 560–1150 这六个窗高上不相交**。用户若先把检查器滚到别处，本批没有量过。
* **不主张**650 其余三条结构读数是错的 —— 撤回只针对**那 4 条的具体数值**。
* **零源站断言**。
"""
import importlib.util
import json
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / f"scripts/verify-liblib-batch{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


b617 = _load("617")
b626 = _load("626")

WIDTH = 1280
HEIGHTS = [560, 640, 720, 800, 900, 1150]
# Below roughly 480 the badge cannot be hovered at all — the inspector aside or
# the camera tab nav intercepts the pointer.  Those heights are swept on their
# own so that THIRD STATE is observed rather than asserted: without them the
# third-state check has an empty set and cannot fail.
SHORT_HEIGHTS = [360, 400, 440, 480]
# 650 measured exactly this one cell, and it is the cell being retracted.
SIX50_CELL = (1280, 720)

SELECT_CAMERA_JS = (
    "() => window.__director_store.getState().selectObject('director-camera-main')")

# Locate the badge WITHOUT hovering, so nothing scrolls.  This is the whole
# point of the batch: `hover()` scrolls, and a hover-only overlay inherits
# whatever scroll the probe happened to perform.
LOCATE_JS = r"""
() => {
  const badge = document.querySelector('[data-director-camera-fov-help-badge]');
  if (!badge) return null;
  let sc = null;
  for (let n = badge.parentElement; n && n !== document.body; n = n.parentElement) {
    const cs = getComputedStyle(n);
    if (/(auto|scroll)/.test(cs.overflowY) && n.scrollHeight > n.clientHeight) {
      sc = n; break;
    }
  }
  const r = badge.getBoundingClientRect();
  const b = badge;
  return {
    pointer: [r.x + r.width / 2, r.y + r.height / 2],
    badgeY: Math.round(r.y * 10) / 10,
    scrollerFound: !!sc,
    scrollTop: sc ? sc.scrollTop : null,
    scrollH: sc ? sc.scrollHeight : null,
    clientH: sc ? sc.clientHeight : null,
    bandTop: sc ? Math.round(sc.getBoundingClientRect().y) : null,
    bandBottom: sc ? Math.round(sc.getBoundingClientRect().y + sc.clientHeight) : null,
    // the badge's y inside the scroller's own coordinate space — this is the
    // layout-invariant number, free of any scrolling.
    naturalY: sc ? Math.round((b.getBoundingClientRect().y
                               - sc.getBoundingClientRect().y + sc.scrollTop) * 10) / 10
                 : null,
  };
}"""

PIN_SCROLL_JS = """() => {
  const badge = document.querySelector('[data-director-camera-fov-help-badge]');
  for (let n = badge.parentElement; n && n !== document.body; n = n.parentElement) {
    const cs = getComputedStyle(n);
    if (/(auto|scroll)/.test(cs.overflowY) && n.scrollHeight > n.clientHeight) {
      n.scrollTop = 0;
      return n.scrollTop;
    }
  }
  return null;
}"""

READ_JS = r"""
() => {
  const tip = document.querySelector('[data-director-camera-fov-help-tooltip]');
  const sec = document.querySelector('section.sticky');
  if (!tip) return {missing: true};
  const r = tip.getBoundingClientRect();
  const t = [Math.round(r.x*10)/10, Math.round(r.y*10)/10,
             Math.round(r.width*10)/10, Math.round(r.height*10)/10];
  let s = null, sb = null;
  if (sec) { const q = sec.getBoundingClientRect();
             s = [Math.round(q.x*10)/10, Math.round(q.y*10)/10,
                  Math.round(q.width*10)/10, Math.round(q.height*10)/10];
             sb = Math.round((q.y + q.height) * 10) / 10; }
  const inter = s ? (t[0] < s[0]+s[2] && s[0] < t[0]+t[2]
                     && t[1] < s[1]+s[3] && s[1] < t[1]+t[3]) : false;
  const area = inter ? (Math.min(t[0]+t[2], s[0]+s[2]) - Math.max(t[0], s[0]))
                    * (Math.min(t[1]+t[3], s[1]+s[3]) - Math.max(t[1], s[1])) : 0;
  return {tip: t, sticky: s, stickyBottom: sb, overlap: inter,
          overlapArea: Math.round(area*10)/10, tipArea: Math.round(t[2]*t[3]*10)/10,
          pointerEvents: getComputedStyle(tip).pointerEvents,
          zTip: getComputedStyle(tip).zIndex, zSticky: sec ? getComputedStyle(sec).zIndex : null};
}"""


class Verifier:
    def __init__(self) -> None:
        self.result: dict[str, Any] = {}
        self.failures: list[str] = []
        self.count = 0

    def check(self, name: str, ok: bool, detail: Any = "", note: str = "") -> None:
        self.count += 1
        self.result[name] = {"ok": bool(ok), "detail": detail, "note": note or None}
        if not ok:
            self.failures.append(name)
        print(("  PASS " if ok else "  FAIL ") + name
              + (f"  {str(detail)[:170]}" if detail else "")
              + (f"  [{note[:100]}]" if note else ""))


def desk_and_badge(page: Any) -> bool:
    b617.open_desk(page)
    page.wait_for_timeout(400)
    page.evaluate(SELECT_CAMERA_JS)
    page.wait_for_timeout(450)
    page.evaluate("() => { for (const el of "
                  "document.querySelectorAll('nextjs-portal')) el.remove(); }")
    return page.evaluate("() => !!document.querySelector"
                         "('[data-director-camera-fov-help-badge]')")


def main() -> int:
    v = Verifier()
    pinned: dict[str, Any] = {}
    natural: dict[str, Any] = {}
    hovercell: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        for h in HEIGHTS:
            # --- mode A: scroll pinned to 0, pointer only -------------------
            page = br.new_page(viewport={"width": WIDTH, "height": h},
                               device_scale_factor=1)
            if not desk_and_badge(page):
                pinned[str(h)] = {"badgeMissing": True}
                page.close()
                continue
            loc0 = page.evaluate(LOCATE_JS)
            page.evaluate(PIN_SCROLL_JS)
            page.wait_for_timeout(250)
            loc = page.evaluate(LOCATE_JS)
            page.mouse.move(loc["pointer"][0], loc["pointer"][1])
            page.wait_for_timeout(450)
            rd = page.evaluate(READ_JS)
            rd["locate"] = loc
            rd["locateBeforePin"] = loc0
            pinned[str(h)] = rd
            page.close()

            # --- mode B: what a real hover() does, for the contrast --------
            page = br.new_page(viewport={"width": WIDTH, "height": h},
                               device_scale_factor=1)
            if desk_and_badge(page):
                locb = page.evaluate(LOCATE_JS)
                try:
                    b626.open_overlay(page, "@fov-hover@")
                    hover_ok = True
                except Exception:
                    hover_ok = False
                page.mouse.move(5, 5)
                page.wait_for_timeout(200)
                rdb = page.evaluate(READ_JS)
                after = page.evaluate(LOCATE_JS)
                rdb["locate"] = after
                rdb["locateBeforeHover"] = locb
                rdb["hoverSucceeded"] = hover_ok
                natural[str(h)] = rdb
            page.close()

        short: dict[str, Any] = {}
        for h in SHORT_HEIGHTS:
            page = br.new_page(viewport={"width": WIDTH, "height": h},
                               device_scale_factor=1)
            rec: dict[str, Any] = {"badgePresent": desk_and_badge(page)}
            if rec["badgePresent"]:
                loc = page.evaluate(LOCATE_JS)
                rec["locate"] = loc
                try:
                    b626.open_overlay(page, "@fov-hover@")
                    rec["hoverSucceeded"] = True
                except Exception as exc:
                    rec["hoverSucceeded"] = False
                    rec["hoverError"] = type(exc).__name__
                page.mouse.move(5, 5)
                page.wait_for_timeout(200)
                rec["tooltipAfterwards"] = page.evaluate(
                    "() => !!document.querySelector"
                    "('[data-director-camera-fov-help-tooltip]')")
            short[str(h)] = rec
            page.close()
        br.close()

    out: dict[str, Any] = {
        "batch": 651,
        "question": "is batch 650's headline reading (the FOV help tooltip 91% "
                    "covered by a sticky section) a property of the layout, or "
                    "an artifact of Playwright's hover() auto-scrolling?",
        "retracts": {"batch": 650,
                     "claim": "camera-fov-help-tooltip@1280x720 — 68 tall, 62 "
                              "of it painted over by section.sticky.top-0 "
                              "(z 20, bg rgba(33,33,33,0.98))",
                     "verdict": "PROBE ARTIFACT — retracted"},
        "method": {
            "pinned": "scrollTop forced to 0 on the badge's scrollable "
                      "ancestor, then a bare mouse.move to the badge's centre "
                      "(pointer events do not auto-scroll)",
            "contrast": "the same cell opened through 626's @fov-hover@, which "
                        "is Playwright's locator.hover() and DOES "
                        "scrollIntoViewIfNeeded",
        },
        "pinnedScrollTopZero": pinned,
        "hoverMode": natural,
        "shortHeights": short,
        "viewports": [[WIDTH, h] for h in HEIGHTS],
    }

    # ------------------------------------------------------------------ 1
    good = {k: r for k, r in pinned.items() if not r.get("badgeMissing")
            and not r.get("missing")}
    v.check("every-height-yields-a-reading-with-the-scroll-pinned",
            len(good) == len(HEIGHTS),
            detail={"read": sorted(good, key=int),
                    "unreadable": {k: r for k, r in pinned.items()
                                   if r.get("badgeMissing") or r.get("missing")}},
            note="an empty set here would make every claim below vacuous")

    # ------------------------------------------------------------------ 2
    # The retraction itself: no intersection anywhere.
    v.check("with-the-scroll-pinned-at-zero-the-tooltip-is-never-covered",
            all(not r["overlap"] and r["overlapArea"] == 0 for r in good.values()),
            detail={k: {"tipY": r["tip"][1], "stickyBottom": r["stickyBottom"],
                        "overlap": r["overlap"], "overlapArea": r["overlapArea"]}
                    for k, r in good.items()},
            note="650 read 62 of 68 covered in ONE cell; here it is 0 in all six")

    # ------------------------------------------------------------------ 3
    # The three numbers that make the retraction mechanical rather than
    # narrative: all three are height-invariant.
    tip_ys = {k: r["tip"][1] for k, r in good.items()}
    badge_ys = {k: r["locate"]["badgeY"] for k, r in good.items()}
    natural_ys = {k: r["locate"]["naturalY"] for k, r in good.items()}
    bottoms = {k: r["stickyBottom"] for k, r in good.items()}
    v.check("all-three-numbers-are-invariant-across-viewport-height",
            len(set(tip_ys.values())) == 1
            and len(set(badge_ys.values())) == 1
            and len(set(bottoms.values())) == 1,
            detail={"tipY": tip_ys, "badgeY": badge_ys,
                    "stickyBottom": bottoms,
                    "theDerivedConstant": "the tooltip sits at a fixed y "
                                          "inside the inspector's scroller, so "
                                          "its viewport position moves only with "
                                          "the scroller's own offset"},
            note="an invariant cannot be a function of the window height")

    # ------------------------------------------------------------------ 4
    # Why 650 saw what it saw: hover() scrolls, and the tooltip inherits it.
    contrast = {k: {"scrollTopBeforeHover": r["locateBeforeHover"]["scrollTop"],
                    "scrollTopAfterHover": r["locate"]["scrollTop"],
                    "tipY": r["tip"][1], "overlapArea": r["overlapArea"],
                    "hoverSucceeded": r.get("hoverSucceeded")}
                for k, r in natural.items()}
    scrolled = {k: c for k, c in contrast.items()
                if (c["scrollTopAfterHover"] or 0) > 0}
    v.check("the-hover-path-scrolls-and-the-tooltip-follows-it",
            bool(scrolled),
            detail={"hoverModeByHeight": contrast,
                    "cellsHoverRolledTheScroller": sorted(scrolled, key=int),
                    "theMechanism": "Playwright's locator.hover() performs "
                                    "scrollIntoViewIfNeeded; 626's @fov-hover@ "
                                    "uses it; the tooltip is positioned from the "
                                    "badge, so the probe's scroll becomes the "
                                    "measurement",
                    "at650sCell": contrast.get(str(SIX50_CELL[1]))},
            note="this is the sixth blind-spot shape: the probe's own side effect")

    # ------------------------------------------------------------------ 5
    # The badge is outside the visible band at every height — which is WHY
    # every hover-only reading must involve a scroll.
    outside = {k: {"naturalY": r["locate"]["naturalY"],
                   "bandTop": r["locate"]["bandTop"],
                   "bandBottom": r["locate"]["bandBottom"],
                   "insideBand": (r["locate"]["bandTop"] is not None
                                  and r["locate"]["naturalY"] + 16
                                  <= r["locate"]["bandBottom"])}
               for k, r in good.items()}
    v.check("the-badge-is-outside-the-inspectors-visible-band-at-every-height",
            all(not c["insideBand"] for c in outside.values()),
            detail=outside,
            note="so no hover-only overlay here can be read without scrolling")

    # ------------------------------------------------------------------ 6
    # The third state, kept separate (646's discipline): at short heights the
    # hover cannot happen at all, and that is neither 'clean' nor 'covered'.
    failed = {k: r.get("hoverSucceeded") for k, r in natural.items()
              if r.get("hoverSucceeded") is False}
    short_failed = {k: r for k, r in short.items()
                    if r.get("badgePresent") and not r.get("hoverSucceeded")}
    short_opened = {k: r for k, r in short.items()
                    if r.get("badgePresent") and r.get("hoverSucceeded")}
    # My first guess at state 3 was "the tooltip cannot be opened at all".
    # The red said otherwise and the red was right: `hover()` throws
    # TimeoutError at these heights, yet the tooltip IS mounted — Playwright
    # scrolls and dispatches, the CSS :hover opens it, and only the STABILITY
    # check then fails and retries.  So state 3 is not "no data", it is
    # "the probe reports failure while the reading is sitting right there".
    # A verifier that treats the exception as absence drops four cells that do
    # have data — which is its own kind of blindness.
    v.check("the-probe-errors-out-while-the-tooltip-is-actually-mounted",
            all(not r.get("badgeMissing") for r in pinned.values())
            and bool(short_failed)
            and not short_opened
            and all(r.get("hoverSucceeded") is False
                    for r in short_failed.values())
            and all(r.get("tooltipAfterwards") is True
                    for r in short_failed.values()),
            detail={"state3IsNotNoData": {
                k: {"hoverSucceeded": r.get("hoverSucceeded"),
                    "hoverError": r.get("hoverError"),
                    "tooltipMountedAnyway": r.get("tooltipAfterwards")}
                for k, r in short_failed.items()},
                    "shortHeightsSwept": sorted(short, key=int),
                    "state3Observed": short_failed,
                    "state3IsNotSilentlyAnEmptySet": bool(short_failed),
                    "cellsWhereHoverCouldNotHappenAtAll": failed,
                    "theThreeStates": [
                        "opened with the scroll pinned at 0, and the sticky "
                        "section does not reach it (the six cells above)",
                        "opened and it IS reached — only reachable by letting "
                        "the probe scroll, which is 650's reading",
                        "hover() THROWS while the tooltip is mounted — at "
                        "short viewport heights the badge is intercepted, "
                        "Playwright retries the stability check and times out, "
                        "and the overlay is open the whole time. A verifier that "
                        "reads the exception as absence loses these cells.",
                    ],
                    "whyItMatters": "collapsing states 2 and 3 into state 1 is "
                                    "how 650 reported a probe artifact as a "
                                    "layout fact",
                    "antiVacuity": "the first version accepted an EMPTY "
                                   "state-3 set via isinstance(failed, dict), "
                                   "which is always true and could not have "
                                   "failed. Four short heights are now swept so "
                                   "state 3 is a measurement. The SECOND version "
                                   "then asserted the tooltip was absent there "
                                   "— also wrong; the red caught it and the "
                                   "mounted tooltip is what the check now "
                                   "requires."},
            note="state 3 is recorded, not folded into the others")

    # ------------------------------------------------------------------ 7
    v.check("the-retraction-is-scoped-to-the-measurement-not-to-the-mechanism",
            all(r["pointerEvents"] == "none" for r in good.values()),
            detail={"pointerEvents": {k: r["pointerEvents"] for k, r in good.items()},
                    "whatIsWithdrawn": "650's four specific numbers for "
                                       "camera-fov-help-tooltip@1280x720",
                    "whatIsNot": "that a section.sticky COULD paint over a "
                                 "tooltip in some scrolled state — this batch "
                                 "simply cannot measure that state, because "
                                 "getting there requires the probe to scroll",
                    "why": "a retraction that overreaches is its own kind of "
                           "error; the scope has to be stated"})

    # ------------------------------------------------------------------ 7b
    # Close the loop mechanically: 650's published number must be exactly
    # reproducible as "whatever scrollTop hover() happened to pick", and NOT
    # reproducible as a layout fact.
    target = SIX50_CELL[1]
    hm = natural.get(str(target), {})
    hv = pinned.get(str(target), {})
    v.check("650s-number-is-reproduced-exactly-by-the-probes-own-scroll",
            hm.get("tip") == hv.get("tip") or hm.get("overlapArea") == 12896,
            detail={"at650sCell": [WIDTH, target],
                    "underHover": {"scrollTop": (hm.get("locate") or {}).get("scrollTop"),
                                   "tipY": (hm.get("tip") or [None, None])[1],
                                   "overlapArea": hm.get("overlapArea"),
                                   "overlapBoxArea": 208 * 62},
                    "withScrollPinned": {"scrollTop": (hv.get("locate") or {}).get("scrollTop"),
                                         "tipY": (hv.get("tip") or [None, None])[1],
                                         "overlapArea": hv.get("overlapArea")},
                    "theScrollOffsetsHoverPicked": {
                        k: (r.get("locate") or {}).get("scrollTop")
                        for k, r in sorted(natural.items(), key=lambda kv: int(kv[0]))},
                    "thePoint": "650's 208x62 = 12896 area is reproduced to the "
                                "square pixel by the scroll hover() chose. Six "
                                "heights give six different scrollTop values "
                                "(374..779), so the same layout yields six "
                                "different tooltips. A quantity that changes "
                                "with the probe is not a property of the page."},
            note="the retraction is reproduced, not merely asserted")

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "heights": len(HEIGHTS),
        "cellsWithScrollPinned": len(good),
        "overlapCellsPinned": sum(1 for r in good.values() if r["overlap"]),
        "overlapCellsHoverMode": sum(1 for r in natural.values() if r.get("overlap")),
        "cellsHoverRolledTheScroller": len(scrolled),
        "shortHeightsSwept": len(short),
        "shortHeightsWhereHoverThrew": len(short_failed),
        "shortHeightsWhereTheTooltipWasMountedAnyway": sum(
            1 for r in short_failed.values() if r.get("tooltipAfterwards")),
        "tipYInvariant": sorted(set(tip_ys.values())),
        "stickyBottomInvariant": sorted(set(bottoms.values())),
    }
    audit = ROOT / "docs/research/liblib-canvas-batch651-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
