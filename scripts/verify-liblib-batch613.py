#!/usr/bin/env python3
"""Verify Batch 613: the director desk's left column, measured against the
source's own container tree rather than against its entries.

## How this batch was chosen

`probe613` walked every interactive element on both canvas pages instead of
just comparing accessible names.  That surfaced a `帮助` button at
`[7.5,1110,32,32]` in the source, 182px below where the clone's sat — and
following it up (`probe613d`/`613e`, walking up from the entry to the
containing block) explained why.

## What the source actually is

The source's left column is ONE element:

    aside.absolute.inset-y-0.left-0.z-30.overflow-hidden
         .border-r.border-white/10.bg-[#171717]        [0,0,281,1150]
      header.flex.h-[52px].items-center.border-b      [0,0,280,52]
      div.flex.h-[calc(100%-52px)]                    [0,52,280,1098]
        nav.border-white/8.flex.w-12.flex-col.gap-2.p-2   [0,52,48,1098]
        div.flex.w-[232px].flex-col.bg-[#171717]          [48,52,232,1098]

So the rail and the scene tree both start at y=52 (the header's bottom edge)
and run **to the viewport bottom**, and the timeline is a separate overlay on
the middle column that paints over the rail's lower part.

The clone had both of them `absolute inset-y-0` inside the middle flex child,
which (a) starts 36px lower because of the clone-only 36px shot bar, and
(b) stops at the timeline's top edge.  Net: every rail entry 36px low, 帮助
182px low, and the tree at 46/220 instead of 48/232.

Batch 602 had already recorded the source rail as `48x1098 @(0,52)` in its
docstring — but its assertion only checked width/padding/gap/background/
border and the *relative* gaps between entries, so the y was never pinned
down.  This batch fixes the container and closes that hole.

## The one thing that cannot be made to work

`probe613f` hit-tested the source's 帮助 at (23.5, 1126): it is **covered** by
the timeline's left control cluster (`z-10 shrink-0 bg-[#1f1f1f]`).  The
source's own bottom-most rail entry is a dead control while the timeline is
open, and it only becomes reachable once the timeline is minimised.  The
clone reproduces that: the timeline is `z-40` and the rail `z-30`, so 帮助 is
under it, and it is hit-testable again when `timelinePanelOpen` is false.
Raising the rail above the timeline instead would bury the timeline's own
left cluster (播放 / 自动帧 / 循环播放 / 时间输入) — trading one dead control
for four live ones.  So the source behaviour is copied and recorded, not
"fixed".

## Not claimed

- The source's rail/tree/shot-bar click behaviour (clicking writes to the
  real project).  What is claimed is geometry, colour, stacking, and that the
  clone's own controls still open and the collapse contract still holds.
- The source has **no** shot/camera tab row at all: a whole-DOM search for
  nav/tablist/role=tab plus the texts 镜头/机位N returns only three navs (the
  canvas navbar, the rail, and the viewport's floating pill).  The clone's
  `导演台镜头` bar is therefore clone-only functionality and is kept; it is
  merely inset by the rail's 48px so the rail no longer eats its label.
- The scene tree's *interior* (the clone has two extra 36px toolbar rows the
  source does not) is not part of this batch.
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
    ROOT / "docs/research/liblib-canvas-batch613-2026-10-01/runtime-audit.json"
)
SCREENSHOT = ROOT / "docs/design-references/liblib-left-column-613-1920.png"
VIEWPORT = {"width": 1920, "height": 1150}

# Source readings.  probe613c/probe613d/probe613i, 2026-10-01, 1920x1150.
SOURCE_RAIL = (0, 52, 48, 1098)
SOURCE_TREE = (48, 52, 232, 1098)
SOURCE_TREE_ASIDE_W = 233  # 232 content + the aside's 1px border-r
SOURCE_DIVIDER = (7.5, 100, 32, 8)
SOURCE_ENTRIES = {
    "场景": 60,
    "添加角色": 116,
    "添加机位": 156,
    "全景图": 196,
    "选择画幅比例": 236,
    "AI 识图导入": 276,
    "帮助": 1110,
}
RAIL_BG = "rgb(23, 23, 23)"
RAIL_Z = 30
TIMELINE_Z = 40

IGNORE_CONSOLE = (
    "The attached 3D object must be a part of the scene graph",
    "webpack-hmr",
    "WebSocket",
    "Failed to load resource",
    "nextjs-dev-overlay",
    # Concurrent edits in this shared worktree, attributed by path.  These are
    # other people's files mid-edit; the rule is to filter them out and not
    # touch them, while any error in a file this batch owns still fails.
    "src/components/jimeng/nodes/JimengTextNode.tsx",
    "src/components/jimeng/JimengHelpMenu.tsx",
)

READ = """() => {
  const at = (el) => { const r = el.getBoundingClientRect();
    return [Math.round(r.x*10)/10, Math.round(r.y*10)/10,
            Math.round(r.width*10)/10, Math.round(r.height*10)/10]; };
  const cs = (el) => getComputedStyle(el);
  const rail = document.querySelector('[data-director-icon-rail]');
  const rc = cs(rail);
  const entries = {};
  for (const el of rail.querySelectorAll('[data-director-rail-entry]')) {
    entries[el.getAttribute('aria-label')] = at(el);
  }
  const divider = rail.querySelector('[data-director-rail-divider]');
  const dc = divider ? cs(divider) : null;
  const treeAside = document.querySelector('[aria-label="场景对象"]');
  const tc = cs(treeAside);
  const tree = document.querySelector('[data-director-tree]');
  const shotBar = document.querySelector('[data-director-shot-bar]');
  const shotLabel = shotBar?.querySelector('span');
  const timeline = document.querySelector('[data-director-timeline]');
  const tl = timeline ? cs(timeline) : null;
  const help = rail.querySelector('[aria-label="帮助"]');
  return {
    rail: {box: at(rail), z: rc.zIndex, padding: rc.padding, gap: rc.gap,
           bg: rc.backgroundColor, borderRightWidth: rc.borderRightWidth,
           borderRightColor: rc.borderRightColor},
    entries, divider: divider ? {box: at(divider),
      borderBottomWidth: dc.borderBottomWidth,
      borderBottomColor: dc.borderBottomColor} : null,
    treeAside: {box: at(treeAside), z: tc.zIndex,
                borderRightWidth: tc.borderRightWidth,
                borderRightColor: tc.borderRightColor},
    tree: {box: at(tree), bg: cs(tree).backgroundColor},
    shotBar: shotBar ? {box: at(shotBar)} : null,
    shotLabel: shotLabel ? {box: at(shotLabel),
                            text: (shotLabel.textContent || '').trim()} : null,
    timeline: timeline ? {box: at(timeline), z: tl.zIndex} : null,
    help: {box: at(help),
           coveredByTimeline: (() => {
             if (!timeline) return false;
             const a = help.getBoundingClientRect(), b = timeline.getBoundingClientRect();
             return a.left < b.right && a.right > b.left
                 && a.top < b.bottom && a.bottom > b.top
                 && parseInt(tl.zIndex || '0', 10) > 30;
           })()},
    playback: (() => {
      const el = document.querySelector('[data-director-playback]');
      if (!el) return null;
      const r = el.getBoundingClientRect();
      const hit = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
      return {box: at(el), reachable: !!(hit && (hit === el || el.contains(hit)))};
    })(),
  };
}"""


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


def box_ok(got: list[float], want: tuple[float, ...], tol: float = 0.6) -> bool:
    return len(got) == 4 and all(abs(got[i] - want[i]) <= tol for i in range(4))


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

    def strip_dev_overlay(self) -> None:
        """Remove the Next dev overlay's portal before any hit test.

        帮助 sits at (23.5, 1126) — the bottom-left corner — and the dev
        server's `nextjs-portal` mounts a build-activity badge exactly there,
        so both elementFromPoint and locator.click() are intercepted by the
        tooling rather than by the app.  The overlay is injected by
        `next dev` and does not exist in a production build or on the source,
        so it is removed here to make the assertion measure the app.  The
        equivalent source reading was taken on production and was unaffected.
        """
        self.page.evaluate(
            """() => {
              for (const el of document.querySelectorAll('nextjs-portal')) {
                el.remove();
              }
            }"""
        )

    def read(self) -> dict[str, Any]:
        self.page.mouse.move(900, 600)
        self.page.wait_for_timeout(150)
        return self.page.evaluate(READ)


def run(page: Page) -> dict[str, Any]:
    v = Verifier(page)
    console: list[str] = []
    errors: list[str] = []
    page.on("console", lambda m: console.append(f"{m.type}: {m.text}"[:200])
            if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)[:200]))

    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__libtv_ui_store "
        "&& window.__director_store)",
        timeout=60_000,
    )
    page.evaluate(
        """() => {
          const s = window.__libtv_store.getState();
          s.addNode("script-execution", { title: "Batch 613" });
          const node = s.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState()
            .openDirectorDesk(node.id, s.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible", timeout=30_000)
    page.wait_for_timeout(1_500)

    r = v.read()
    v.result["desk"] = r

    # --- 1) the rail container ------------------------------------------
    rail = r["rail"]
    v.check("rail:container-[0,52,48,1098]", box_ok(rail["box"], SOURCE_RAIL),
            detail=rail["box"])
    v.check("rail:pad-8-gap-8-bg-171717",
            rail["padding"] == "8px" and rail["gap"] == "8px"
            and rail["bg"] == RAIL_BG,
            detail=f"{rail['padding']}/{rail['gap']}/{rail['bg']}")
    v.check("rail:border-r-1px-white-8",
            rail["borderRightWidth"] == "1px"
            and abs(alpha_of(rail["borderRightColor"]) - 0.08) < 0.001,
            detail=f"{rail['borderRightWidth']}/{rail['borderRightColor']}")
    v.check("rail:z-30", rail["z"] == "30", detail=rail["z"])

    # --- 2) every entry, y included -------------------------------------
    for name, y in SOURCE_ENTRIES.items():
        got = r["entries"].get(name)
        v.check(f"entry:{name}:present", got is not None)
        if got is None:
            continue
        want = (7.5, y, 32, 32)
        v.check(f"entry:{name}:box", box_ok(got, want), detail=f"{got} vs {list(want)}")
    v.check("entry:count-7", len(r["entries"]) == 7, detail=sorted(r["entries"]))

    # --- 3) the 32x8 divider between 场景 and 添加角色 -------------------
    d = r["divider"]
    v.check("divider:present", d is not None)
    if d:
        v.check("divider:box-[7.5,100,32,8]", box_ok(d["box"], SOURCE_DIVIDER),
                detail=d["box"])
        v.check("divider:border-b-1px-white-8",
                d["borderBottomWidth"] == "1px"
                and abs(alpha_of(d["borderBottomColor"]) - 0.08) < 0.001,
                detail=f"{d['borderBottomWidth']}/{d['borderBottomColor']}")
        v.check("divider:straddles-the-24px-step",
                abs((r["entries"]["添加角色"][1] - r["entries"]["场景"][1]) - 56) <= 0.6,
                detail=r["entries"]["添加角色"][1] - r["entries"]["场景"][1])

    # --- 4) the scene tree ----------------------------------------------
    v.check("tree:[48,52,232,1098]", box_ok(r["tree"]["box"], SOURCE_TREE),
            detail=r["tree"]["box"])
    v.check("tree:bg-171717", r["tree"]["bg"] == RAIL_BG, detail=r["tree"]["bg"])
    ta = r["treeAside"]
    v.check("tree:aside-233-with-1px-right-border",
            abs(ta["box"][2] - SOURCE_TREE_ASIDE_W) <= 0.6
            and ta["borderRightWidth"] == "1px"
            and abs(alpha_of(ta["borderRightColor"]) - 0.10) < 0.001,
            detail=ta)
    v.check("tree:z-30", ta["z"] == "30", detail=ta["z"])

    # --- 5) the clone-only shot bar no longer sits under the rail -------
    sb, sl = r["shotBar"], r["shotLabel"]
    v.check("shotbar:present", sb is not None)
    if sb and sl:
        v.check("shotbar:starts-right-of-the-rail",
                sl["box"][0] >= SOURCE_RAIL[2], detail=sl["box"])
        v.check("shotbar:label-visible", sl["text"] == "镜头", detail=sl["text"])

    # --- 6) stacking: the timeline covers 帮助, as it does on the source -
    tl = r["timeline"]
    v.check("timeline:present", tl is not None)
    if tl:
        v.check("timeline:z-40-above-rail", tl["z"] == str(TIMELINE_Z), detail=tl["z"])
        v.check("timeline:full-width", abs(tl["box"][2] - VIEWPORT["width"]) <= 1,
                detail=tl["box"])
    v.check("help:under-the-timeline-while-it-is-open",
            r["help"]["coveredByTimeline"] is True, detail=r["help"])
    v.strip_dev_overlay()
    v.check("playback:still-reachable", r["playback"] is not None
            and r["playback"]["reachable"] is True, detail=r["playback"])

    page.screenshot(path=str(SCREENSHOT))

    # --- 7) minimising the timeline frees 帮助, exactly like the source --
    page.evaluate("() => window.__director_store.getState().setTimelinePanelOpen(false)")
    page.wait_for_timeout(600)
    v.strip_dev_overlay()
    v.check("timeline:unmounts-when-minimised",
            page.locator("[data-director-timeline]").count() == 0)
    free = v.read()
    v.result["minimised"] = free
    v.check("help:still-pinned-at-1110",
            box_ok(free["help"]["box"], (7.5, 1110, 32, 32)), detail=free["help"]["box"])
    help_btn = page.locator('[data-director-icon-rail] [aria-label="帮助"]')
    v.check("help:hit-testable-when-the-timeline-is-minimised",
            help_btn.evaluate(
                """(el) => {
                     const b = el.getBoundingClientRect();
                     const hit = document.elementFromPoint(
                       b.x + b.width / 2, b.y + b.height / 2);
                     return !!(hit && (hit === el || el.contains(hit)));
                   }"""
            ))
    help_btn.click()
    page.wait_for_timeout(300)
    v.check("help:click-does-not-throw",
            page.locator("[data-director-workspace]").count() == 1)
    page.evaluate("() => window.__director_store.getState().setTimelinePanelOpen(true)")
    page.wait_for_timeout(500)

    # --- 8) the collapse contract (batch 587) survives the move ----------
    before = v.read()
    page.locator("[data-director-panels-toggle]").click()
    page.wait_for_timeout(600)
    after = v.read()
    v.result["collapsed"] = after
    v.check("collapse:rail-survives", len(after["entries"]) == 7,
            detail=sorted(after["entries"]))
    v.check("collapse:tree-is-hidden",
            page.locator("[data-director-tree]").is_visible() is False)
    v.check("collapse:rail-did-not-move",
            box_ok(after["entries"]["场景"], (7.5, 60, 32, 32)),
            detail=after["entries"]["场景"])
    page.locator('[data-director-icon-rail] [aria-label="场景"]').click()
    page.wait_for_timeout(600)
    restored = v.read()
    v.check("restore:tree-comes-back",
            page.locator("[data-director-tree]").is_visible() is True)
    v.check("restore:tree-back-to-[48,52,232,1098]",
            box_ok(restored["tree"]["box"], SOURCE_TREE), detail=restored["tree"]["box"])
    v.check("restore:rail-unchanged",
            box_ok(restored["rail"]["box"], SOURCE_RAIL), detail=restored["rail"]["box"])
    del before

    # --- 9) the rail's own flyouts still open from the new position -----
    # Switching flyouts is done by clicking the other rail entry (the rail's
    # `select` closes the previous one), NOT with Escape: Escape is not in
    # the flyout branch of the desk's key handler and falls through to
    # closeWorkspace().  That gap is pre-existing and out of this batch.
    char_entry = r["entries"]["添加角色"]
    page.locator('[data-director-icon-rail] [aria-label="添加角色"]').click()
    page.wait_for_timeout(500)
    v.check("flyout:opens", page.locator("[data-director-character-flyout]").count() == 1)
    if page.locator("[data-director-character-flyout]").count() == 1:
        fb = page.locator("[data-director-character-flyout]").bounding_box()
        # `absolute left-[calc(100%+8px)]` off the entry wrapper
        want_x = char_entry[0] + char_entry[2] + 8
        v.check("flyout:8px-right-of-its-entry",
                fb is not None and abs(fb["x"] - want_x) <= 0.6,
                detail=f"{fb} vs x={want_x}")
    page.locator('[data-director-icon-rail] button[aria-label="全景图"]').click()
    page.wait_for_timeout(500)
    v.check("flyout:panorama-opens",
            page.locator("[data-director-panorama-flyout]").count() == 1)
    v.check("flyout:switching-closes-the-previous-one",
            page.locator("[data-director-character-flyout]").count() == 0)
    pan = r["entries"]["全景图"]
    if page.locator("[data-director-panorama-flyout]").count() == 1:
        pb = page.locator("[data-director-panorama-flyout]").bounding_box()
        want_x = pan[0] + pan[2] + 8
        v.check("flyout:panorama-8px-right-of-its-entry",
                pb is not None and abs(pb["x"] - want_x) <= 0.6,
                detail=f"{pb} vs x={want_x}")
    # `select()` clears the open flyout before handling any entry, so
    # clicking another rail entry is what dismisses one.  (A second click on
    # the same entry re-opens rather than toggles — that is the clone's
    # existing behaviour and the source's flyout click semantics are not
    # authorised for measurement, so neither is asserted here.)
    page.locator('[data-director-icon-rail] button[aria-label="场景"]').click()
    page.wait_for_timeout(400)
    v.check("flyout:another-entry-dismisses-it",
            page.locator("[data-director-panorama-flyout]").count() == 0)

    noise = [c for c in console if any(k in c for k in IGNORE_CONSOLE)]
    real_console = [c for c in console if not any(k in c for k in IGNORE_CONSOLE)]
    real_errors = [e for e in errors if not any(k in e for k in IGNORE_CONSOLE)]
    v.check("diagnostics:no-page-errors", not real_errors, detail=real_errors[:5])
    v.check("diagnostics:no-console-errors", not real_console, detail=real_console[:5])
    v.result["diagnostics"] = {
        "consoleErrors": len(console),
        "filtered": len(noise),
        "pageErrors": len(errors),
    }
    v.result["_summary"] = {"checks": v.count, "failures": v.failures}
    return v.result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 613,
        "title": "Director desk left column: rail + scene tree against the source's own container tree",
        "date": "2026-10-01",
        "sourceEvidence": [
            "probe613: full interactive inventory of both canvas pages "
            "(not just accessible names) — turned up 帮助 at [7.5,1110,32,32]",
            "probe613c / probe613d: every ancestor of the rail's first entry, "
            "which is where the 36px/182px deltas turned out to come from",
            "probe613e: the vertical layout skeleton of both desks",
            "probe613g: a band sweep of y 52..88 — the source has no "
            "full-width row there, only rail / tree / inspector / viewport",
            "probe613h: whole-DOM nav/tab/role=tab search — the source desk "
            "has no shot row at all",
            "probe613i: exact boxes, borders and backgrounds for the source's "
            "aside / header / row / rail / divider / tree",
            "probe613f: elementFromPoint at the source's 帮助 centre",
        ],
        "claims": {
            "sourceFact": [
                "the source's left column is a single aside "
                "[0,0,281,1150] = header [0,0,280,52] + div.flex.h-[calc(100%-52px)] "
                "[0,52,280,1098] holding nav [0,52,48,1098] and the tree "
                "[48,52,232,1098]",
                "rail: 48 wide, p-2, gap-2, bg #171717, border-r white/8",
                "rail entries at y = 60 / 116 / 156 / 196 / 236 / 276, plus a "
                "32x8 border-b divider at y=100, plus 帮助 pinned at y=1110",
                "scene tree: div.flex.w-[232px].flex-col.bg-[#171717], no border "
                "of its own; the column's 1px border-r white/10 sits at "
                "x 280..281 on the aside",
                "the source's 帮助 is covered by the timeline's left control "
                "cluster (z-10 shrink-0 bg-[#1f1f1f]) — a dead control while "
                "the timeline is open",
                "the source desk has no shot/camera tab row",
            ],
            "cloneDecision": [
                "the rail and the tree are hoisted out of the middle flex "
                "child to be positioned against the workspace (which is "
                "fixed, hence a containing block), so they span 52 -> "
                "viewport bottom like the source's aside",
                "the clone-only 导演台镜头 bar is kept (the source has no such "
                "row) and merely inset by the rail's 48px at >=900px so the "
                "rail no longer covers its label",
                "the tree's aside is 233px wide so its 1px border-r lands at "
                "x 280..281, matching the source's column edge",
                "帮助 stays under the timeline, copying the source; raising "
                "the rail instead would bury the timeline's own 播放 / 自动帧 "
                "/ 循环播放 / 时间输入 cluster",
            ],
            "sourceSideObservations": [
                "the source's bottom-most rail entry is unreachable while the "
                "timeline is open and only becomes reachable once the "
                "timeline is minimised — the clone now behaves the same way",
            ],
            "notClaimed": [
                "the source's rail / tree button click behaviour",
                "the scene tree's interior — the clone carries two extra 36px "
                "toolbar rows the source does not have",
            ],
        },
    }
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport=VIEWPORT)
        page = ctx.new_page()
        audit["checks"] = run(page)
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    summary = audit["checks"]["_summary"]
    audit["result"] = (
        f"{summary['checks'] - len(summary['failures'])}/{summary['checks']} passed"
    )
    with open(AUDIT_PATH, "w", encoding="utf-8") as f:
        json.dump(audit, f, ensure_ascii=False, indent=2)
    print(f"\n{audit['result']}")
    if summary["failures"]:
        print("FAILED: " + ", ".join(summary["failures"]))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
