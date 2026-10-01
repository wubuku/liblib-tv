#!/usr/bin/env python3
"""batch 630 验收：把尺子扫到**时间轴高度**这条从未有人扫过的第三轴，并修掉
一个真实的钳制缺失。

## 这条轴为什么值得扫

627 扫宽度、628 扫高度、629 扫两者的交叉角 —— 三批加起来覆盖了窗口
`innerWidth × innerHeight` 这个平面。**但窗口不是唯一能改变纵向布局的输入**：
时间轴面板可由用户拖拽调高，量程 `DIRECTOR_TIMELINE_HEIGHT_MIN=88` ..
`MAX=420`（`directorStore.ts:99-100`），实测自 `data-director-timeline-resize-handle`
（`cursor-ns-resize`，8px 透明条）。这条轴**一个格子都没被扫过**。

## 本批挖到的真缺陷：高度没有对可用空间钳制

`setTimelineHeight` 只把值钳在 88..420 这个**魔数区间**里
（`directorStore.ts:5506-5512`），**没有任何东西拿它和可用纵向空间比**。实测
（`/tmp/dbg630b.py`、`/tmp/dbg630c.py`）：

| 窗口 | 请求时间轴 | 时间轴底边 | 超出窗口 | 视口高 |
| --- | --- | --- | --- | --- |
| 1440x900 | 420 | y=900 | 0 | 392 |
| 1440x660 | 420 | y=660 | 0 | 152 |
| 1440x480 | 420 | y=508 | **28** | **0** |
| 1440x400 | 420 | y=508 | **108** | **0** |
| 1440x360 | 420 | y=508 | **148** | **0** |

面板是 `flexShrink=0` + `overflow-y-visible`，工作区是 `fixed inset-0`（不滚动），
所以超出的 148px 直接在屏幕外。时间轴顶边随之被顶到 y=88，**3D 视口塌成 0 高**。

**为什么普查没报**（这一点比缺陷本身更值得记）：几何边界轴在所有这些设置下
`offViewportUnreachable` 都是 **0** —— 因为落在屏幕外那块的所有控件**恰好都在
时间轴自己的 `overflow-y-auto` 滚动容器里**，于是被 `offViewportScrollable`
判为「滚得到、不失败」。这正是 627 立的那条规则
（*落在任意一个裁剪祖先之外就算被裁，滚一下就到，记录不失败*）的**代价**：
它在这里把一个真实的布局问题**掩盖**成了健康。**「够不着 = 0」不能当作
「布局没问题」的证据。**

**为什么这仍然是真缺陷而不是可接受行为**：把手全程 `own=True`（5 个横向采样点
全部命中把手本身），所以用户能拖回来，**不是死局**；但一个面板能被拖到
35% 在屏幕外、且主视口高度为 0，本身就不是任何合理实现该有的状态。

**修法与全应用惯例同源**：626 立的规矩是「每个浮层按 `window.innerHeight − 8`
钳制，越界多少上移多少，不越界一个像素不动」。这里**安全边取 0 而不是 8** ——
8px 那条是给**浮层**留抓取余量的，而贴底面板本来就该贴住窗口下沿，套上 8 会把
613 在源站实测并钉住的 **182** 悄悄压成 174。**不发明任何 UX 数字**：
只保证「不超出窗口」，至于视口能不能被压到 0 高是拖拽者自己的选择，本批
明确**不**替产品决定这件事。

## 本批同时更正两条既往结论

1. **629 的「这类碰撞只出现在从未采样过的矮/窄视口」被推翻**。1440x660 配
   时间轴 420 就是一个**普通窗口**下可达的状态：视口 152px，`重置视角` 被
   底部带盖住 —— 而这正是 629 闭式公式预测的那一格。**豁免本身不变**
   （`victimInViewport` 不关心成因），变的是**说法**：它不是「窗口太矮导致的
   退化视口」，而是「视口比 gizmo 簇自身所需还矮 whatever 成因」。
2. **628 第一族的掩埋数是时间轴高度的函数**。660 高的窗口上把时间轴从 88 拖到
   420，掩埋数 1 → 4 → 4 → **10** → **15**；而 900/1150 高的窗口上恒为 1。
   所以 628 台账里的「299 枚」**只在默认 182 上成立**，本批把限定词补上。

## 不声称

- **源站任何事**。源站的拖拽量程**未取证**（`DirectorTimeline.tsx:273-274`
  原话：*量程 88..420 是 clone 自定的*）。所以本批**不主张源站会钳制**，
  只主张 clone 自己这个魔数区间在短窗口下留出了一个坏状态，而全应用对
  「不许超出窗口」已有 626 立的一致惯例。
- **视口 0 高该怎么处置**。本批只保证面板不超出窗口；最小视口高是产品决定。
- **628 第一族该修**。它仍是源站事实，处置仍卡在源站矮视口读数上。
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

_s = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(b617)

_s2 = importlib.util.spec_from_file_location(
    "b629", ROOT / "scripts/verify-liblib-batch629.py")
b629 = importlib.util.module_from_spec(_s2)
_s2.loader.exec_module(b629)

# The clone's own drag range (directorStore.ts:99-100), swept end to end plus
# intermediates.  182 is the source-measured default (batch 613).
TIMELINE_HEIGHTS = [88, 120, 150, 182, 210, 240, 270, 300, 330, 360, 390, 420]
DEFAULT_HEIGHT = 182
# <=898 declares its own expanded height.  Batch 629 measured 176 here and
# labelled it a clone-only narrow value; this batch keeps it as a pinned
# reading so a shrink is never mistaken for a clamp.
NARROW_MAX = 898
NARROW_EXPANDED = 176

# Windows chosen to straddle the boundary where the requested height stops
# fitting: 900/1150 never overflow at 420, 660 gives the 629 squeeze cell, and
# 560..360 are the ones that overflow.
WINDOWS = [(1440, 900), (1920, 1150), (1280, 720), (1440, 660), (1440, 560),
           (1440, 480), (1440, 400), (1440, 360), (900, 500), (640, 480)]
CROSSCHECK = [(1440, 400, 420), (1440, 360, 420), (1440, 660, 420),
              (1440, 900, 420)]

# The panel is bottom-docked, so the safety margin is 0 — see the docstring.
SAFETY = 0

GEOM_JS = """() => {
  const rd = (sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {top: r.top, left: r.left, width: r.width,
            height: r.height, bottom: r.bottom, right: r.right};
  };
  const handle = document.querySelector('[data-director-timeline-resize-handle]');
  const out = {
    win: {w: innerWidth, h: innerHeight},
    timeline: rd('[data-director-timeline]'),
    viewport: rd('[data-director-viewport]'),
    bottomBar: rd('[data-director-bottom-bar]'),
  };
  // "Can the user drag it back?" — the handle spans the panel's top edge, so
  // sample it at five points: a panel hanging off the screen must still be
  // recoverable by its own handle.
  out.handle = [];
  if (handle) {
    const r = handle.getBoundingClientRect();
    for (const frac of [0.02, 0.25, 0.5, 0.75, 0.98]) {
      const x = r.left + r.width * frac, y = r.top + r.height / 2;
      if (x < 0 || y < 0 || x > innerWidth || y > innerHeight) {
        out.handle.push({frac, own: false, offWindow: true});
        continue;
      }
      out.handle.push({frac, own: document.elementFromPoint(x, y) === handle,
                       offWindow: false});
    }
  }
  return out;
}"""


def prep(page) -> None:
    page.mouse.move(5, 5)
    page.wait_for_timeout(150)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal'))"
                  " el.remove(); }")


def ask_timeline(page, want: int) -> None:
    page.evaluate("(n) => window.__director_store.getState().setTimelineHeight(n)", want)
    page.wait_for_timeout(200)


def measure(page, want: int) -> dict[str, Any]:
    r = page.evaluate(b617.AUDIT_JS, list(b617.TRANSIENT_OVERLAYS))
    g = page.evaluate(GEOM_JS)
    tl, vp = g["timeline"], g["viewport"]
    band = g["bottomBar"]["height"] if g["bottomBar"] else None
    got = round(tl["height"], 3) if tl else None
    spill = (round(tl["bottom"] - g["win"]["h"], 3) if tl else None)
    # Two different reasons a panel can end up shorter than what was asked for,
    # and conflating them is a bug this batch made: the narrow family (<=898)
    # declares its own expanded height (176, a clone value batch 629 recorded),
    # while a clamp is a response to spilling past the window.  Only the second
    # one is `clamped`.
    #
    # `clamped` is detected GEOMETRICALLY, not by comparing against the
    # pre-fix state: a clamped panel is flush with the window bottom and
    # shorter than requested.  Defining it as "spilled past the window" would
    # be self-defeating — that is exactly what the fix removes, so the verifier
    # would report the clamp as never firing and pass for the wrong reason.
    short = got is not None and got < want - 0.5
    flush = (got is not None and vp is not None
             and abs(vp["top"] + got - g["win"]["h"]) <= 0.5)
    return {
        "requested": want,
        "actualHeight": got,
        "shrunkByCss": short and not (flush and short),
        "clamped": short and flush,
        "timelineBottom": round(tl["bottom"], 3) if tl else None,
        "spillBelowWindow": spill,
        "viewportH": round(vp["height"], 3) if vp else None,
        "viewportTop": round(vp["top"], 3) if vp else None,
        "band": band,
        "handleOwn": [h["own"] for h in g["handle"]],
        "total": r["total"],
        "offViewport": len(r["offViewportItems"]),
        "unreachable": [(b["label"], b["box"], b["data"])
                        for b in r["offViewportUnreachable"]],
        "scrollable": len(r["offViewportScrollable"]),
        "covered": [(b["label"], b["hitLabel"], b["box"]) for b in r["covered"]],
        "byTimeline": len(r["coveredByTimelineOverlay"]),
        "squeezeRows": [(b["label"], b["box"], b["hitLabel"])
                        for b in r["coveredByViewportSqueeze"]],
        "squeezeCoverers": [(b["label"], bool(b.get("hitInBottomBand")),
                             bool(b.get("hitInTimeline")),
                             bool(b.get("hitInShotBar")))
                            for b in r["coveredByViewportSqueeze"]],
        "blocked": [(b["label"], b["box"], b["panel"], b["timelineOverlay"],
                     b["clipped"], b["victimInViewport"])
                    for b in r["blocked"]],
    }


class Verifier:
    def __init__(self) -> None:
        self.result: dict[str, Any] = {}
        self.failures: list[str] = []
        self.count = 0

    def check(self, name: str, ok: bool, detail: Any = "") -> None:
        self.count += 1
        self.result[name] = {"ok": bool(ok), "detail": detail}
        if not ok:
            self.failures.append(name)
        print(("  PASS " if ok else "  FAIL ") + name + (f"  {detail}" if detail else ""))


def main() -> int:
    v = Verifier()
    cells: dict[str, Any] = {}
    cross: dict[str, Any] = {}
    stable: dict[str, Any] = {}
    unstable: list[Any] = []
    with sync_playwright() as p:
        br = p.chromium.launch()
        for w, h in WINDOWS:
            page = br.new_page(viewport={"width": w, "height": h},
                               device_scale_factor=1)
            b617.open_desk(page)
            for th in TIMELINE_HEIGHTS:
                page.set_viewport_size({"width": w, "height": h})
                page.wait_for_timeout(150)
                ask_timeline(page, th)
                prep(page)
                key = f"{w}x{h}/tl={th}"
                cells[key] = measure(page, th)
                # Ask the same height a second time.  A clamp that lands on the
                # boundary is a fixed point; one that oscillates or keeps
                # shrinking is not, and no single reading can tell them apart.
                ask_timeline(page, th)
                page.wait_for_timeout(160)
                stable[key] = {"firstHeight": cells[key]["actualHeight"],
                               "secondHeight": page.evaluate(
                                   "() => { const el ="
                                   " document.querySelector('[data-director-timeline]');"
                                   " return el ? Math.round(el.getBoundingClientRect()"
                                   ".height * 1000) / 1000 : null; }")}
            page.close()

        for w, h, th in CROSSCHECK:
            fresh = br.new_page(viewport={"width": w, "height": h},
                                device_scale_factor=1)
            b617.open_desk(fresh)
            ask_timeline(fresh, th)
            prep(fresh)
            cross[f"{w}x{h}/tl={th}"] = measure(fresh, th)
            fresh.close()
        br.close()

    out = {
        "batch": 630,
        "title": "the third axis nobody swept — the timeline's own draggable "
                 "height — plus a real defect: the magic 88..420 range is never "
                 "checked against the space actually available",
        "date": "2026-10-01",
        "timelineHeights": TIMELINE_HEIGHTS,
        "windows": WINDOWS,
        "cells": cells,
        "freshLoadCrosscheck": cross,
    }

    v.check(f"the-grid-covers-{len(WINDOWS)}w-x-{len(TIMELINE_HEIGHTS)}timeline",
            len(cells) == len(WINDOWS) * len(TIMELINE_HEIGHTS),
            detail=len(cells))

    # --- the defect ------------------------------------------------------
    spill = {k: r["spillBelowWindow"] for k, r in cells.items()
             if (r["spillBelowWindow"] or 0) > SAFETY + 0.5}
    v.check("the-timeline-never-extends-past-the-window-bottom", not spill,
            detail=dict(list(spill.items())[:6]))

    # Non-vacuity.  The trap here is that the obvious definition — "the panel
    # spilled past the window" — is exactly what the fix eliminates, so a
    # verifier written that way reports the clamp as never firing and passes
    # for the wrong reason.  The evidence that survives the fix is the height
    # coming BACK shorter than the value that was asked for.
    shortened = [k for k, r in cells.items() if r["shrunkByCss"] or r["clamped"]]
    v.check("the-clamp-is-actually-exercised", bool(shortened),
            detail={"count": len(shortened), "sample": shortened[:6],
                    "byOverflow": sum(1 for r in cells.values() if r["clamped"]),
                    "byCss": sum(1 for r in cells.values() if r["shrunkByCss"])})

    # ...and it lands exactly on the boundary rather than short of or past it:
    # asking twice for the same height must not shrink the panel any further.
    for k, r in stable.items():
        if r["secondHeight"] != r["firstHeight"]:
            unstable.append((k, r["firstHeight"], r["secondHeight"]))
    v.check("re-requesting-a-clamped-height-is-a-fixed-point", not unstable,
            detail={"checked": len(stable), "unstable": unstable[:6]})

    # 626's contract, verbatim: a panel that is not out of bounds must not move
    # a single pixel.  Pinned on the source-measured default, because applying
    # the 8px floating-menu margin here would silently turn 182 into 174 and
    # break what batch 613 measured.  Restricted to the wide family: <=898
    # declares its own expanded height (176, clone-only, recorded by 629), so
    # "the requested value came back" is not the same statement there.
    touched = {k: {"requested": r["requested"], "actual": r["actualHeight"]}
               for k, r in cells.items()
               if r["requested"] == DEFAULT_HEIGHT
               and int(k.split("x")[0]) > NARROW_MAX
               and r["clamped"]}
    v.check("the-source-measured-default-182-is-never-clamped", not touched,
            detail=dict(list(touched.items())[:6]))

    # ...and the narrow family's own default, so the 176 is recorded as a
    # value rather than showing up as an unexplained shrink.
    narrow_default = {k: r["actualHeight"] for k, r in cells.items()
                      if r["requested"] == DEFAULT_HEIGHT
                      and int(k.split("x")[0]) <= NARROW_MAX}
    v.check("the-narrow-family-keeps-its-own-declared-expanded-height",
            set(narrow_default.values()) == {NARROW_EXPANDED},
            detail=narrow_default)

    # --- the census stays clean on this axis too ------------------------
    bad = {k: r["unreachable"] for k, r in cells.items() if r["unreachable"]}
    v.check("no-cell-has-an-off-viewport-unreachable-control", not bad,
            detail={k: r[:3] for k, r in list(bad.items())[:6]})

    vac = [k for k, r in cells.items() if r["offViewport"] == 0]
    v.check("every-cell-actually-exercised-the-off-viewport-branch", not vac,
            detail=vac[:8])

    uncov = {k: r["covered"] for k, r in cells.items() if r["covered"]}
    v.check("no-cell-has-an-unexplained-covered-control", not uncov,
            detail={k: r[:3] for k, r in list(uncov.items())[:6]})

    # --- 629's law, re-checked on the third axis ------------------------
    viol = []
    for k, r in cells.items():
        for label, box, _hit in r["squeezeRows"]:
            if r["viewportTop"] is None or r["band"] is None:
                viol.append((k, label, "chrome-missing"))
                continue
            if (box[1] + box[3] - r["viewportTop"]) + r["band"] < r["viewportH"]:
                viol.append((k, label, box, r["viewportH"]))
    v.check("every-squeeze-row-still-satisfies-629s-closed-form", not viol,
            detail=viol[:6])

    diff = {}
    for k, r in cells.items():
        got = {row[0] for row in r["squeezeRows"]}
        want = b629.predict(r)
        if got != want:
            diff[k] = {"observed": sorted(got), "predicted": sorted(want)}
    v.check("629s-closed-form-still-predicts-every-cell-on-this-axis", not diff,
            detail=dict(list(diff.items())[:4]))

    # Batch 629's law assumed the viewport has POSITIVE height, and on this axis
    # that assumption breaks twice over.  Once the panel has taken the viewport's
    # whole vertical space, the viewport's own bottom-anchored chrome is pushed
    # ABOVE its own box, and whatever sits up there becomes the coverer: the
    # panel itself (its time scale, transport, track rows), or — the case this
    # batch had to go measure — the shot bar, whose `data-director-shot-option`
    # buttons are absolutely positioned ~225px above their own nav's box and
    # come down on the gizmo-mode buttons at y 48..80.  So the coverer must be
    # the bottom band, or — only once the viewport has no height left at all —
    # the panel or the shot bar that took its place.  A fourth coverer fails.
    loose_cover = []
    seen_families: set[tuple[str, bool]] = set()
    for k, r in cells.items():
        zero = (r["viewportH"] or 0) <= 0.5
        for label, in_band, in_timeline, in_shot in r["squeezeCoverers"]:
            if in_band:
                seen_families.add(("bottomBand", zero))
                continue
            if zero and (in_timeline or in_shot):
                seen_families.add(("timeline" if in_timeline else "shotBar", True))
                continue
            loose_cover.append((k, label, in_band, in_timeline, in_shot,
                                r["viewportH"]))
    v.check("every-squeeze-coverer-is-the-band-or-a-zero-height-replacement",
            not loose_cover, detail=loose_cover[:6])
    v.check("all-coverer-families-were-actually-exercised",
            {("bottomBand", False), ("timeline", True),
             ("shotBar", True)} <= seen_families,
            detail=sorted(f"{a}@zeroHeight={b}" for a, b in seen_families)
                   + ["note: bottomBand@zeroHeight=True never occurs — once the "
                      "viewport has no height the panel always wins the hit "
                      "test, so the band never gets to be the coverer"])

    # The batch's headline correction to 629: this collision is reachable at an
    # ORDINARY window height, so "it only happens on never-sampled short
    # viewports" is false.  Asserted so the correction cannot be undone.
    ordinary = {k: sorted({row[0] for row in r["squeezeRows"]})
                for k, r in cells.items()
                if r["squeezeRows"] and int(k.split("x")[1].split("/")[0]) >= 600}
    v.check("the-squeeze-is-reachable-at-an-ordinary-window-height", bool(ordinary),
            detail={"cells": list(ordinary)[:6], "count": len(ordinary)})

    # --- "you can always drag it back" ----------------------------------
    trapped = {k: r["handleOwn"] for k, r in cells.items()
               if not all(r["handleOwn"])}
    v.check("the-resize-handle-stays-reachable-at-every-setting", not trapped,
            detail=dict(list(trapped.items())[:4]))

    mism = [k for k, r in cross.items()
            if (r["total"], r["offViewport"], len(r["covered"]),
                tuple(sorted(x[0] for x in r["squeezeRows"])))
            != (cells[k]["total"], cells[k]["offViewport"],
                len(cells[k]["covered"]),
                tuple(sorted(x[0] for x in cells[k]["squeezeRows"])))]
    v.check(f"the-{len(CROSSCHECK)}-fresh-loads-agree-with-the-resized-page",
            not mism, detail=mism)

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "shortenedCells": len(shortened),
        "clampedByOverflow": sum(1 for r in cells.values() if r["clamped"]),
        "shrunkByFamilyCss": sum(1 for r in cells.values() if r["shrunkByCss"]),
        "maxSpillBelowWindow": max((r["spillBelowWindow"] or 0)
                                   for r in cells.values()),
        "squeezeCells": sum(1 for r in cells.values() if r["squeezeRows"]),
        "byTimelineAtDefault": {k: r["byTimeline"] for k, r in cells.items()
                                if r["requested"] == DEFAULT_HEIGHT},
        "byTimelineAtMax": {k: r["byTimeline"] for k, r in cells.items()
                            if r["requested"] == max(TIMELINE_HEIGHTS)},
        "minViewportH": min((r["viewportH"] or 0) for r in cells.values()),
    }
    audit = ROOT / "docs/research/liblib-canvas-batch630-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
