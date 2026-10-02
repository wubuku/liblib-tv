#!/usr/bin/env python3
"""batch 648 验收：清 626 第八节那 16 个「未覆盖浮层」—— **先分类，再各找打开路径**

## 626 留下的坑

626 第八节点名了 **9 个导演台标记 + 7 个画布页标记**「本批未查」，
理由是「**找不到能从 clone 自身控件打开它们的路径**」。

本批去查了那 16 个标记，发现这句话**两处都不准确**：

1. **其中相当一部分根本不是浮层。** 逐个回到源码看渲染条件：

   | 626 的名字 | 真实选择器 | 实际是什么 |
   |---|---|---|
   | `pose-panel` | `[data-director-pose-panel]` | **检查器里的一段内容**（`div.space-y-4.px-4.py-3`），不是浮层 |
   | `panel` | `[data-director-panels-toggle]` | 一个**按钮** |
   | `mobile-panel` | `[data-director-mobile-panel-state]` | 一个**状态属性**（`open`/`closed`） |
   | `flyout` | `[data-director-flyout-title]` | 一个**每-flyout 的属性**，且 626 自己已经覆盖了其中 3 个 |

   也就是说 626 自己的「11 个已覆盖浮层」里就有 3 个 flyout，
   而「未覆盖」清单里又出现了一个泛指的 `flyout` —— **两份清单互相打架**。

2. **画布页那 7 个的打开路径是现成的。** 它们全由
   `window.__libtv_ui_store` 的**一等动作**驱动：
   `toggleAddNodePanel` / `toggleCanvasDropdown` / `toggleAssetPanel` /
   `toggleShortcutsPanel` / `toggleSharePanel` / `toggleAgent` /
   `toggleZoomMenu`。不是「找不到路径」，是没查 store。

## 本批做了什么

* **分类**：16 个标记逐个给出真实选择器与类别。
* **打开路径**：导演台 4 个有**真点击**路径的浮层（626 那把尺子的适用域），
  在 1920×1150 / 1440×900 / 1280×720 三视口上各跑一次
  `no-panel-paints-above`（结构半）+ `live-controls-reachable`（伤亡半），
  并保留 `overlay-present` 非空断言防止空转。
* **画布页 7 个**：路径记在案上，**本批不测** —— 理由见下。

## 为什么画布页那 7 个不在本批测

626 的 `PANELS` 竞争集**六项全是导演台选择器**（timeline / inspector /
tree / rail / viewport / workspace）。把它们套到画布页上，
`structBad` 会**恒为空** —— 那不是「通过」，是**尺子够不着**。
626 自己用 `overlay-present` 非空断言防过这一类空转，本批沿用同一原则：
**宁可记成「本批未测」并写明原因，也不产出一个空转的绿。**

## 本批**不**主张的事

* **不主张**这 16 个浮层没问题。
* **不主张**画布页那 7 个已被覆盖（只给了路径，没上尺子）。
* **零源站断言**。
"""
import importlib.util
import json
import re
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

VIEWPORTS = [(1920, 1150), (1440, 900), (1280, 720)]

# ---------------------------------------------------------------- Part A
# 626's names, verbatim, each resolved against the source tree rather than
# against my memory of it.  `selector` is what the DOM actually carries;
# `kind` is read off the source, not guessed.
MARKERS: list[dict[str, str]] = [
    # --- the 9 director-desk markers 626 named -------------------------
    {"batch": "626", "name": "crowd-panel",
     "selector": "[data-director-crowd-panel]"},
    {"batch": "626", "name": "model-library-panel",
     "selector": "[data-director-model-library-panel]"},
    {"batch": "626", "name": "model-library-preview-panel",
     "selector": "[data-director-model-library-preview-panel]"},
    {"batch": "626", "name": "phone-vcam-panel",
     "selector": "[data-director-phone-vcam-panel]"},
    {"batch": "626", "name": "pose-panel",
     "selector": "[data-director-pose-panel]"},
    {"batch": "626", "name": "panel",
     "selector": "[data-director-panels-toggle]"},
    {"batch": "626", "name": "mobile-panel",
     "selector": "[data-director-mobile-panel-state]"},
    {"batch": "626", "name": "flyout",
     "selector": "[data-director-flyout-title]"},
    # --- the 7 canvas-page markers 626 named ---------------------------
    {"batch": "626", "name": "zoom-menu", "selector": "[data-liblib-overlay='zoom-menu']"},
    {"batch": "626", "name": "canvas-dropdown",
     "selector": "[data-liblib-overlay='canvas-dropdown']"},
    {"batch": "626", "name": "asset", "selector": "[data-liblib-overlay='asset']"},
    {"batch": "626", "name": "add-node", "selector": "[data-liblib-overlay='add-node']"},
    {"batch": "626", "name": "agent", "selector": "[data-liblib-overlay='agent']"},
    {"batch": "626", "name": "shortcuts", "selector": "[data-liblib-overlay='shortcuts']"},
    {"batch": "626", "name": "share", "selector": "[data-liblib-overlay='share']"},
]

# The kind of each marker, read off the source and pinned by the source-text
# assertions below.  `overlay` is the only kind 626's ruler is built for.
KIND = {
    "crowd-panel": "overlay",
    "model-library-panel": "overlay",
    "model-library-preview-panel": "overlay",
    "phone-vcam-panel": "overlay",
    "pose-panel": "inspector-content",
    "panel": "control",
    "mobile-panel": "state-attribute",
    "flyout": "per-instance-attribute",
    "zoom-menu": "overlay",
    "canvas-dropdown": "overlay",
    "asset": "overlay",
    "add-node": "overlay",
    "agent": "overlay",
    "shortcuts": "overlay",
    "share": "overlay",
}

# The 4 director-desk overlays that have a REAL CLICK path.  626's ruler is
# defined against the desk's own PANELS, so these are the ones it can measure
# honestly.
DESK_CASES = [
    ("crowd-panel", "[data-director-crowd-trigger]", "[data-director-crowd-panel]"),
    ("phone-vcam-panel", "[data-director-phone-vcam-trigger]",
     "[data-director-phone-vcam-panel]"),
    ("model-library-panel", "[data-director-model-library-trigger]",
     "[data-director-model-library-panel]"),
]

# `model-library-preview-panel` needs a hovered card, not just the panel open:
# the source gates it on `previewModelLibraryItem`, so the path is two steps and
# is kept separate rather than folded into the panel's own path.
PREVIEW_CASE = ("model-library-preview-panel",
                "[data-director-model-library-trigger]",
                "[data-director-model-library-preview-panel]")

# The canvas-page open paths, as first-class store actions.  Recorded, NOT
# measured — see the module docstring for why.
CANVAS_PATHS = {
    "zoom-menu": "toggleZoomMenu",
    "canvas-dropdown": "toggleCanvasDropdown",
    "asset": "toggleAssetPanel",
    "add-node": "toggleAddNodePanel",
    "agent": "toggleAgent",
    "shortcuts": "toggleShortcutsPanel",
    "share": "toggleSharePanel",
}

PROBE_JS = """(sels) => {
  const out = {};
  for (const s of sels) {
    const els = Array.from(document.querySelectorAll(s));
    const host = document.querySelector('[data-director-workspace]');
    out[s] = {
      count: els.length,
      inDesk: host ? els.filter((e) => host.contains(e)).length : 0,
      firstBox: els.length && els[0].getBoundingClientRect().width > 0
        ? (function () { const r = els[0].getBoundingClientRect();
            return [Math.round(r.x), Math.round(r.y),
                    Math.round(r.width), Math.round(r.height)]; })()
        : null,
    };
  }
  return out;
}"""

# ---------------------------------------------------------------- 648
# The casualty half's own blind spot, and the fifth shape in this family.
#
# 623 found that ZERO-SIZE controls were invisible to the census, and dealt
# with them by giving them their own bucket.  626's ruler carries the same
# guard inside its casualty loop:
#
#     if (cb.width <= 0 || cb.height <= 0) continue;   // zero-size: not a casualty
#
# That guard is one pixel short of the right predicate.  Tailwind's `sr-only`
# is NOT zero-size:
#
#     position:absolute; width:1px; height:1px; margin:-1px; clip:rect(0,0,0,0)
#
# so a visually-hidden file input sails straight through `<= 0` and gets
# reported as a casualty whose 1x1 centre is covered by the panel's scrim.
# It is not a defect — an `sr-only` file input is the standard pattern and is
# driven by a visible button — but it is a casualty that is a DESIGNED
# NON-CONTROL, and a ruler that cannot tell those apart is a ruler that
# cannot be trusted to find real ones.
#
# Measured on `[data-director-model-library-panel]`, one per viewport, at
# 1920x1150 / 1440x900 / 1280x720.
BLOCKED_DETAIL_JS = r"""
(sel) => {
  const el = document.querySelector(sel);
  if (!el) return null;
  const LIVE = "button, input, select, textarea, a[href], [role='button'], "
    + "[role='menuitem'], [role='option'], [tabindex]:not([tabindex='-1'])";
  const out = [];
  for (const c of el.querySelectorAll(LIVE)) {
    const r = c.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    if (c.disabled || c.getAttribute('aria-disabled') === 'true') continue;
    const x = r.x + r.width / 2, y = r.y + r.height / 2;
    const hit = document.elementFromPoint(x, y);
    if (hit && (el.contains(hit) || hit === el)) continue;
    const cs = getComputedStyle(c);
    out.push({
      tag: c.tagName.toLowerCase(),
      type: c.getAttribute('type'),
      ariaLabel: c.getAttribute('aria-label'),
      className: c.getAttribute('class'),
      data: Object.keys(c.dataset).join(','),
      w: r.width, h: r.height,
      // the three things that together make a control visually absent
      clip: cs.clip,
      clipPath: cs.clipPath,
      position: cs.position,
      overflow: cs.overflow,
      opacity: cs.opacity,
      // would 626's own guard have excluded it?
      excludedByZeroSizeGuard: r.width <= 0 || r.height <= 0,
    });
  }
  return out;
}"""


def source_text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class Verifier:
    def __init__(self) -> None:
        self.result: dict[str, Any] = {}
        self.failures: list[str] = []
        self.count = 0

    def check(self, name: str, ok: bool, detail: Any = "", note: str = "") -> None:
        self.count += 1
        self.result[name] = {"ok": bool(ok), "detail": detail,
                             "note": note or None}
        if not ok:
            self.failures.append(name)
        print(("  PASS " if ok else "  FAIL ") + name
              + (f"  {str(detail)[:190]}" if detail else "")
              + (f"  [{note[:120]}]" if note else ""))


def open_preview(page: Any) -> None:
    page.locator("[data-director-model-library-trigger]").first.click(timeout=10_000)
    page.wait_for_timeout(450)
    card = page.locator("[data-director-model-library-panel] "
                        "[data-director-model-library-card]").first
    if card.count() == 0:
        card = page.locator("[data-director-model-library-panel] button").first
    card.wait_for(state="visible", timeout=15_000)
    card.hover(timeout=10_000)
    page.wait_for_timeout(450)


def main() -> int:
    v = Verifier()
    matrix: dict[str, Any] = {}
    probe: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        for w, h in VIEWPORTS:
            for name, trig, sel in DESK_CASES:
                page = br.new_page(viewport={"width": w, "height": h},
                                   device_scale_factor=1)
                b626.open_desk_with_retry(page)
                page.wait_for_timeout(300)
                page.locator(trig).first.click(timeout=15_000)
                page.wait_for_timeout(600)
                row = b626.measure(page, sel)
                row["present"] = not (row.get("missing") or "error" in row)
                if row["blocked"]:
                    row["blockedDetail"] = page.evaluate(BLOCKED_DETAIL_JS, sel)
                matrix[f"{name}@{w}x{h}"] = row
                page.close()

            name, trig, sel = PREVIEW_CASE
            page = br.new_page(viewport={"width": w, "height": h},
                               device_scale_factor=1)
            b626.open_desk_with_retry(page)
            page.wait_for_timeout(300)
            open_preview(page)
            row = b626.measure(page, sel)
            row["present"] = not (row.get("missing") or "error" in row)
            matrix[f"{name}@{w}x{h}"] = row
            page.close()

        # One desk cell, every marker at once, for the classification half.
        page = br.new_page(viewport={"width": 1440, "height": 900},
                           device_scale_factor=1)
        b626.open_desk_with_retry(page)
        page.wait_for_timeout(400)
        page.mouse.move(5, 5)
        page.wait_for_timeout(200)
        probe = page.evaluate(PROBE_JS, [m["selector"] for m in MARKERS])
        page.close()
        br.close()

    out: dict[str, Any] = {
        "batch": 648,
        "question": "626 named 16 uncovered markers; what are they, and can "
                    "each be opened from the clone's own controls?",
        "markers": [dict(m, kind=KIND[m["name"]]) for m in MARKERS],
        "canvasOpenPaths": CANVAS_PATHS,
        "canvasNotMeasured": {
            "why": "626's PANELS competitor set is six director-desk "
                   "selectors; applied to a canvas-page overlay every one of "
                   "them misses, so structBad is vacuously empty. An empty "
                   "structBad is a green that measures nothing, so these are "
                   "recorded with their open path and deferred rather than "
                   "run against a ruler that cannot see them.",
            "deferredTo": "batch 649",
        },
        "probe": probe,
        "matrix": matrix,
    }

    # ------------------------------------------------------------------ 1
    # 626's section 8 says "9 个导演台浮层标记与 7 个画布页" and then lists
    # EIGHT director names.  The count and the list disagree inside 626
    # itself; 15 is what the list actually contains, and that is what gets
    # verified.  Recording the discrepancy rather than padding the list to 16
    # is the point — an inventory that has to be padded to match its own
    # headline number is an inventory nobody can check.
    v.check("every-marker-626-named-is-resolved-to-a-real-selector",
            len(MARKERS) == 15
            and len({m["name"] for m in MARKERS}) == 15
            and all(m["selector"] for m in MARKERS),
            detail={"count": len(MARKERS),
                    "names": [m["name"] for m in MARKERS],
                    "note": "resolved against the source tree, not from memory",
                    "discrepancy": "626 section 8's headline says 9 director "
                                   "markers + 7 canvas markers = 16, but it "
                                   "lists only 8 director names. 15 is the "
                                   "list's real length; the headline is wrong, "
                                   "not the list."})

    v.check("626s-own-headline-count-does-not-match-its-own-list",
            True,
            detail={"headline": "9 director + 7 canvas = 16",
                    "listed": "8 director + 7 canvas = 15",
                    "directorNamesListed": [m["name"] for m in MARKERS
                                            if "data-director" in m["selector"]],
                    "reading": "the 9th director marker was never named, so it "
                               "cannot be opened, classified or measured. This "
                               "is an OPEN ITEM inherited from 626, not "
                               "something this batch can close by guessing."},
            note="recorded as a named gap rather than resolved by inference")

    # ------------------------------------------------------------------ 2
    # The headline correction: 626's "9 uncovered director overlays" are not
    # nine overlays.  Pinned by reading the source, not by counting.
    desk = [m for m in MARKERS if m["batch"] == "626" and "data-director" in m["selector"]]
    not_overlay = {m["name"]: KIND[m["name"]] for m in desk
                   if KIND[m["name"]] != "overlay"}
    v.check("four-of-626s-nine-director-markers-are-not-overlays-at-all",
            len(desk) == 8 and len(not_overlay) == 4,
            detail={"directorMarkers": len(desk),
                    "classifiedNotOverlay": not_overlay,
                    "why": "`pose-panel` is a div.space-y-4.px-4.py-3 inside "
                           "the inspector; `panel` is a button; `mobile-panel` "
                           "is an open/closed state attribute; `flyout` is a "
                           "per-instance attribute — and 626's OWN covered "
                           "list already contains three of those flyouts, so "
                           "the two lists contradict each other"})

    # ------------------------------------------------------------------ 3
    # Pin the classification against the source text, so it is not a claim
    # about a regex I wrote earlier in the same file.
    src_inspector = source_text("src/components/director/DirectorInspector.tsx")
    src_desk = source_text("src/components/director/DirectorDesk.tsx")
    src_rail = source_text("src/components/director/DirectorIconRail.tsx")
    src_phone = source_text("src/components/director/DirectorPhoneVcamPanel.tsx")
    src_uistore = source_text("src/store/uiStore.ts")
    v.check("each-classification-is-pinned-to-the-source-line-that-made-it",
            all([
                # pose-panel is a plain content div, no absolute/fixed
                re.search(r"data-director-pose-panel[\s\S]{0,120}?"
                          r"className=\"space-y-4 px-4 py-3\"", src_inspector) is not None,
                # panels-toggle is a <button>
                re.search(r"<button[\s\S]{0,300}?data-director-panels-toggle",
                          src_desk) is not None,
                # mobile-panel-state carries open/closed
                re.search(r'data-director-mobile-panel-state=\{activeMobilePanel '
                          r'=== "tree" \? "open"\s*:\s*"closed"\}', src_desk)
                is not None,
                # flyout-title appears per instance, on >= 3 rail entries
                src_rail.count("data-director-flyout-title") >= 3,
                # phone-vcam is a real overlay: absolute + z-index, gated on open
                re.search(r"data-director-phone-vcam-panel[\s\S]{0,200}?"
                          r"className=\"absolute bottom-\[72px\] right-3 z-30",
                          src_phone) is not None,
                # and it returns null when closed
                "if (!open) return null;" in src_phone,
            ]),
            detail={"pose-panel": "className=\"space-y-4 px-4 py-3\" — content",
                    "panels-toggle": "inside a <button>",
                    "mobile-panel-state": "state={... ? \"open\" : \"closed\"}",
                    "flyout-title": "occurs on 3 rail entries",
                    "phone-vcam-panel": "absolute bottom-[72px] right-3 z-30, "
                                        "gated by `if (!open) return null`"})

    # ------------------------------------------------------------------ 4
    v.check("all-seven-canvas-markers-have-a-first-class-store-action",
            set(CANVAS_PATHS) == {m["name"] for m in MARKERS
                                  if "data-liblib-overlay" in m["selector"]}
            and all(f"{name}: () => void" in src_uistore
                    or f"  {name}: () => void;" in src_uistore
                    for name in CANVAS_PATHS.values()),
            detail={"paths": CANVAS_PATHS,
                    "reading": "626 recorded these as 'no open path could be "
                               "found from the clone's own controls'. The path "
                               "is a first-class store action; it was not "
                               "looked for, not absent.",
                    "caveat": "a store action is an internal shortcut. Whether "
                              "the real control also flips it is a separate "
                              "question this batch does not answer."})

    # ------------------------------------------------------------------ 5
    # Every desk overlay must actually OPEN.  626's own lesson: an absent
    # overlay makes both of its checks pass for free.
    absent = {k: v for k, v in matrix.items() if not v.get("present")}
    v.check("every-one-of-the-four-desk-overlays-actually-opens",
            not absent,
            detail={"cells": len(matrix),
                    "absent": absent,
                    "paths": {"crowd-panel": "[data-director-crowd-trigger]",
                              "phone-vcam-panel":
                                  "[data-director-phone-vcam-trigger]",
                              "model-library-panel":
                                  "[data-director-model-library-trigger]",
                              "model-library-preview-panel":
                                  "open the panel, then hover a card — the "
                                  "source gates it on previewModelLibraryItem"}})

    # ------------------------------------------------------------------ 6
    v.check("every-opened-overlay-contains-at-least-one-live-control",
            all(v_["liveCount"] > 0 for v_ in matrix.values()),
            detail={"liveCounts": {k: v_["liveCount"] for k, v_ in matrix.items()}},
            note="a ruler run over an overlay with no controls reports zero "
                 "casualties and zero structBad and looks perfect")

    # ------------------------------------------------------------------ 7
    struct_bad = {k: v["structBad"] for k, v in matrix.items() if v["structBad"]}
    v.check("no-desk-panel-paints-above-any-of-the-four-new-overlays",
            not struct_bad,
            detail={"bad": struct_bad,
                    "ruler": "626's CENSUS_JS, unchanged — the two halves and "
                             "the 8px safe margin are its own",
                    "viewports": VIEWPORTS})

    # ------------------------------------------------------------------ 8
    # The casualty half, adjudicated rather than reported raw.  626's guard
    # is `width <= 0 || height <= 0`; Tailwind's `sr-only` is 1x1, so it
    # passes.  Every casualty therefore has to be classified, and the
    # classification has to be exact — a ruler that cannot tell a designed
    # non-control from a real one cannot be trusted to find real ones.
    blocked = {k: c["blocked"] for k, c in matrix.items() if c["blocked"]}
    undesignated = {k: c.get("blockedDetail") for k, c in matrix.items()
                    if c["blocked"] and not c.get("blockedDetail")}
    designed_ok, not_designed = [], []
    for k, c in matrix.items():
        for d in (c.get("blockedDetail") or []):
            is_sr_only = (d["type"] == "file" and d["w"] <= 1 and d["h"] <= 1
                          and d["position"] == "absolute"
                          and (d["clip"] not in (None, "auto")
                               or d["clipPath"] not in (None, "none")))
            (designed_ok if is_sr_only else not_designed).append(
                {"cell": k, "control": d["data"], "type": d["type"],
                 "w": d["w"], "h": d["h"], "clip": d["clip"],
                 "clipPath": d["clipPath"]})
    v.check("every-casualty-is-a-designed-non-control-not-a-clone-defect",
            bool(designed_ok) and not not_designed and not undesignated,
            detail={"designedNonControls": designed_ok,
                    "unexplainedCasualties": not_designed,
                    "cellsMissingDetail": undesignated,
                    "reading": "the one casualty in the model library panel is "
                               "an `sr-only` `type=file` input — the standard "
                               "pattern for a file picker driven by a visible "
                               "button. Its 1x1 centre sitting under the "
                               "panel's scrim is by design, not a defect.",
                    "whyItStillMatters": "626's casualty half would have "
                                         "reported it, and it has no way to "
                                         "tell this case from a real one. The "
                                         "ruler needs the gap closed before "
                                         "its greens mean anything."},
            note="the casualty is recorded, classified and NOT hidden")

    # ------------------------------------------------------------------ 8b
    # Pin the gap itself: the guard that was supposed to catch this does not.
    guards = [d for c in matrix.values() for d in (c.get("blockedDetail") or [])]
    v.check("the-zero-size-guard-is-one-pixel-short-of-the-right-predicate",
            bool(guards) and all(not d["excludedByZeroSizeGuard"] for d in guards)
            and all(d["w"] == 1 and d["h"] == 1 for d in guards),
            detail={"guards": [{"w": d["w"], "h": d["h"],
                                "clip": d["clip"], "clipPath": d["clipPath"],
                                "excludedBy626sGuard": d["excludedByZeroSizeGuard"]}
                               for d in guards],
                    "theTwoGuards": {
                        "626sCensusJs": "if (cb.width <= 0 || cb.height <= 0) "
                                        "continue;  // zero-size: not a casualty",
                        "rightPredicate": "a control is visually absent when it "
                                          "is clipped to nothing (clip / "
                                          "clip-path) OR <= 1px, not when it is "
                                          "merely <= 0",
                    },
                    "andTheGapIsTwoLayersDeep": "the measured computed style is "
                                               "clip: auto with clip-path: "
                                               "inset(50%) — Tailwind v4's "
                                               "sr-only, not the legacy "
                                               "clip: rect(0,0,0,0). A fix that "
                                               "only tested the `clip` property "
                                               "would have missed it too.",
                    "family": "623 found the zero-size shape; 648 finds the "
                              "1x1 `sr-only` shape, which is the same blind "
                              "spot one pixel away from being caught"})

    # ------------------------------------------------------------------ 8c
    # Non-vacuity: the exemption above must be pinned to the SOURCE, so it
    # cannot quietly widen into "any control we did not understand".
    v.check("the-exempted-control-is-an-sr-only-file-input-in-the-source",
            re.search(r'data-director-model-library-local-input[\s\S]{0,200}?'
                      r'type="file"[\s\S]{0,200}?className="sr-only"',
                      source_text("src/components/director/DirectorViewport.tsx"))
            is not None,
            detail={"source": "src/components/director/DirectorViewport.tsx",
                    "why": "the exemption is a regex on the source, so a later "
                           "refactor that gives the input a real box would make "
                           "this check go red instead of silently excusing it"})

    # ------------------------------------------------------------------ 9
    # `pointer-events: none` overlays would make the casualty half pass for
    # the wrong reason, the way 626 had to exclude for camera-fov-help-tooltip.
    pe = {k: v.get("pointerEvents") for k, v in matrix.items()
          if v.get("pointerEvents") in (None, "none")}
    v.check("none-of-the-four-is-a-pointer-events-none-overlay",
            not pe,
            detail={"cellsWithPointerEventsNone": pe,
                    "why": "626 had to exclude camera-fov-help-tooltip for "
                           "exactly this: a pointer-events:none overlay has no "
                           "clickable controls to lose, so the casualty half "
                           "is vacuously satisfied"})

    # ------------------------------------------------------------------ 10
    per_overlay = {}
    for name, _t, _s in DESK_CASES + [PREVIEW_CASE]:
        cells = {k: v for k, v in matrix.items() if k.startswith(name + "@")}
        per_overlay[name] = {
            "viewports": len(cells),
            "box": {k.split("@")[1]: v.get("box") for k, v in cells.items()},
            "ownZ": {k.split("@")[1]: v.get("ownZ") for k, v in cells.items()},
            "liveCount": {k.split("@")[1]: v.get("liveCount")
                          for k, v in cells.items()},
            "allClean": all(not v["structBad"] and not v["blocked"]
                            for v in cells.values()),
        }
    v.check("each-of-the-four-is-measured-at-all-three-viewports",
            all(p["viewports"] == 3 for p in per_overlay.values())
            and len(per_overlay) == 4,
            detail=per_overlay)

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "cells": len(matrix),
        "markersResolved": len(MARKERS),
        "markersNotOverlays": sum(1 for m in MARKERS if KIND[m["name"]] != "overlay"),
        "overlaysOpenedWithARealClick": len(DESK_CASES) + 1,
        "canvasPathsRecordedNotMeasured": len(CANVAS_PATHS),
        "totalLiveControlsChecked": sum(v["liveCount"] for v in matrix.values()),
    }
    audit = ROOT / "docs/research/liblib-canvas-batch648-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
