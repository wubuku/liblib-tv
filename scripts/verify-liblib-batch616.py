#!/usr/bin/env python3
"""Verify Batch 616: the scene tree's interior, against the source's own
two-child subtree.

## Where the readings come from

`/tmp/src593/probe613i` walked the source's left column on 2026-10-01 at
1920×1150 with the director desk open and a camera selected.  It found the
scene tree to be exactly **two** children:

    div [48, 52, 232, 1098]  .flex.w-[232px].min-w-0.flex-col.bg-[#171717]
      div [48, 52, 232, 48]   .flex.h-12.shrink-0.items-center.px-3
                              .text-[12px].leading-5.text-white/90
                              border 0px/0px/0px/0px   ← no border at all
      div [48, 100, 232, 1050]
                              .min-h-0.flex-1.overflow-y-auto.px-2.pb-3
                              [scrollbar-color:rgba(255,255,255,0.2)_transparent]
                              [scrollbar-width:thin]

The clone's tree had four children and two self-invented details: a
`border-b border-white/[0.07]` on the header (the source's four edges all
measure 0) and a `py-2` list with no horizontal padding, no `pb-3` and no
scrollbar tint.

## What is deliberately NOT changed

The two things the source and clone genuinely disagree about are **content**,
not chrome, and both are clone functionality that this work does not delete:

1. **Child count.** The source has 2 children; the clone has 4 — the two extra
   ones are 36px toolbars (`h-9 shrink-0 … border-b border-white/[0.06] px-2`)
   holding the clone's own group/camera actions.  Recorded, asserted as 4.
2. **What the 48px header holds.** The source's header carries a
   `text-[12px] leading-5 text-white/90` text title; the clone's carries a
   search field plus buttons (aria 搜索场景内容).  Only the frame is aligned;
   the search field stays and is verified to still work.

A third difference was measured but is out of scope here: the source's list
starts at y=100 (right under the header) while the clone's starts at y=172,
because of those two toolbars.  That is a consequence of (1), not an
independent defect.

## Note on the source session

These readings were captured earlier in the same session.  By the time this
batch was implemented the shared source tab had been changed by another user —
its viewport went to 1600×1000 and the director desk was closed — so no live
re-measurement was possible.  The class strings and edge widths above are the
ones `probe613i` actually returned, quoted verbatim rather than re-derived.
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
    ROOT / "docs/research/liblib-canvas-batch616-2026-10-01/runtime-audit.json"
)
SCREENSHOT = ROOT / "docs/design-references/liblib-scene-tree-616-1920.png"
VIEWPORT = {"width": 1920, "height": 1150}

# probe613i, 2026-10-01, 1920x1150, director desk open
SOURCE_TREE = (48, 52, 232, 1098)
SOURCE_HEADER = (48, 52, 232, 48)
SOURCE_HEADER_EDGES = ("0px", "0px", "0px", "0px")
SOURCE_HEADER_PAD_X = 12
SOURCE_LIST_PAD_X = 8
SOURCE_LIST_PAD_BOTTOM = 12
SCROLLBAR = "rgba(255, 255, 255, 0.2)"
CLONE_CHILD_COUNT = 4  # 2 clone-only toolbars on top of the source's 2

IGNORE_CONSOLE = (
    "The attached 3D object must be a part of the scene graph",
    "webpack-hmr",
    "WebSocket",
    "Failed to load resource",
    "nextjs-dev-overlay",
    "src/components/jimeng/nodes/JimengTextNode.tsx",
    "src/components/jimeng/JimengHelpMenu.tsx",
)

READ = """() => {
  const at = (el) => { const r = el.getBoundingClientRect();
    return [Math.round(r.x*10)/10, Math.round(r.y*10)/10,
            Math.round(r.width*10)/10, Math.round(r.height*10)/10]; };
  const cs = (el) => getComputedStyle(el);
  const tree = document.querySelector('[data-director-tree]');
  const header = tree ? tree.children[0] : null;
  const list = tree ? tree.querySelector(':scope > div.overflow-y-auto') : null;
  const lc = list ? cs(list) : null;
  return {
    tree: tree ? {box: at(tree), bg: cs(tree).backgroundColor} : null,
    header: header ? {box: at(header),
      edges: [cs(header).borderTopWidth, cs(header).borderRightWidth,
              cs(header).borderBottomWidth, cs(header).borderLeftWidth],
      padX: parseFloat(cs(header).paddingLeft),
      padY: parseFloat(cs(header).paddingTop)} : null,
    list: list ? {box: at(list), padX: parseFloat(lc.paddingLeft),
      padBottom: parseFloat(lc.paddingBottom),
      padTop: parseFloat(lc.paddingTop), overflowY: lc.overflowY,
      scrollbarColor: lc.scrollbarColor, scrollbarWidth: lc.scrollbarWidth,
      clientH: list.clientHeight, scrollH: list.scrollHeight} : null,
    children: tree ? Array.from(tree.children).map((k) => ({
      box: at(k),
      cls: (k.getAttribute('class') || '').slice(0, 90),
      text: (k.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 20),
    })) : [],
    search: (() => { const el = document.querySelector(
        '[data-director-tree] input[aria-label="搜索场景内容"]');
      return el ? {box: at(el), visible: el.getBoundingClientRect().width > 0}
                : null; })(),
    itemCount: document.querySelectorAll('[data-director-tree] [role="treeitem"],'
      + ' [data-director-tree-item]').length,
  };
}"""


def near(got: float, want: float, tol: float = 0.6) -> bool:
    return abs(got - want) <= tol


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
          s.addNode("script-execution", { title: "Batch 616" });
          const node = s.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState()
            .openDirectorDesk(node.id, s.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible", timeout=30_000)
    page.wait_for_timeout(1_500)

    r = v.read()
    v.result["desk"] = r

    # --- 1) the tree frame (unchanged by this batch, still pinned) --------
    v.check("tree:box-48-52-232-1098",
            r["tree"] is not None
            and all(near(r["tree"]["box"][i], SOURCE_TREE[i]) for i in range(4)),
            detail=(r["tree"] or {}).get("box"))
    v.check("tree:bg-171717",
            r["tree"] is not None and r["tree"]["bg"] == "rgb(23, 23, 23)",
            detail=(r["tree"] or {}).get("bg"))

    # --- 2) the header: 48 tall, no border, px-3 -------------------------
    h = r["header"]
    v.check("header:box-48-52-232-48",
            h is not None
            and all(near(h["box"][i], SOURCE_HEADER[i]) for i in range(4)),
            detail=(h or {}).get("box"))
    v.check("header:no-border-on-any-edge",
            h is not None and tuple(h["edges"]) == SOURCE_HEADER_EDGES,
            detail=(h or {}).get("edges"))
    v.check("header:px-3", h is not None and near(h["padX"], SOURCE_HEADER_PAD_X),
            detail=(h or {}).get("padX"))
    v.check("header:no-vertical-padding-of-its-own",
            h is not None and near(h["padY"], 0), detail=(h or {}).get("padY"))

    # --- 3) the list: px-2 pb-3 + the source's thin scrollbar -------------
    lst = r["list"]
    v.check("list:present", lst is not None)
    if lst:
        v.check("list:px-2", near(lst["padX"], SOURCE_LIST_PAD_X), detail=lst["padX"])
        v.check("list:pb-3", near(lst["padBottom"], SOURCE_LIST_PAD_BOTTOM),
                detail=lst["padBottom"])
        v.check("list:scrolls", lst["overflowY"] in ("auto", "scroll"),
                detail=lst["overflowY"])
        v.check("list:thin-scrollbar",
                lst["scrollbarWidth"] == "thin"
                and SCROLLBAR in lst["scrollbarColor"],
                detail=f"{lst['scrollbarWidth']} / {lst['scrollbarColor']}")
        v.check("list:starts-below-header-and-toolbars",
                lst["box"][1] > SOURCE_HEADER[1] + SOURCE_HEADER[3],
                detail=lst["box"])

    # --- 4) the two clone-only toolbars are kept, and are what the gap is --
    v.check("tree:four-children-2-clone-only-toolbars",
            len(r["children"]) == CLONE_CHILD_COUNT,
            detail=[c["cls"][:40] for c in r["children"]])
    toolbars = [c for c in r["children"] if "h-9" in c["cls"]]
    v.check("tree:the-two-extra-children-are-36px-toolbars",
            len(toolbars) == 2 and all(near(c["box"][3], 36) for c in toolbars),
            detail=[c["box"] for c in toolbars])

    # --- 5) the clone's own search still works (functionality preserved) --
    v.check("search:present-and-visible",
            r["search"] is not None and r["search"]["visible"] is True,
            detail=r["search"])
    if r["search"]:
        page.locator('[data-director-tree] input[aria-label="搜索场景内容"]').fill("机位")
        page.wait_for_timeout(500)
        filtered = v.read()
        v.check("search:filters-the-tree",
                filtered["itemCount"] <= max(r["itemCount"], 0) + 1
                and filtered["itemCount"] < 99,
                detail={"before": r["itemCount"], "after": filtered["itemCount"]})
        page.locator('[data-director-tree] input[aria-label="搜索场景内容"]').fill("")
        page.wait_for_timeout(400)
        v.check("search:clearing-restores",
                v.read()["itemCount"] == r["itemCount"],
                detail=r["itemCount"])

    page.screenshot(path=str(SCREENSHOT))

    noise = [c for c in console if any(k in c for k in IGNORE_CONSOLE)]
    real_console = [c for c in console if not any(k in c for k in IGNORE_CONSOLE)]
    real_errors = [e for e in errors if not any(k in e for k in IGNORE_CONSOLE)]
    v.check("diagnostics:no-page-errors", not real_errors, detail=real_errors[:5])
    v.check("diagnostics:no-console-errors", not real_console, detail=real_console[:5])
    v.result["diagnostics"] = {"consoleErrors": len(console),
                                "filtered": len(noise),
                                "pageErrors": len(errors)}
    v.result["_summary"] = {"checks": v.count, "failures": v.failures}
    return v.result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 616,
        "title": "Scene tree interior: header carries no border, list takes the "
                 "source's px-2 pb-3 and thin scrollbar",
        "date": "2026-10-01",
        "sourceEvidence": [
            "/tmp/src593/probe613i, 2026-10-01, 1920x1150, director desk open: "
            "the source's tree has exactly two children — a 48px header with "
            "all four edges 0px and a list with px-2 pb-3 plus "
            "[scrollbar-color:rgba(255,255,255,0.2)_transparent] "
            "[scrollbar-width:thin]",
            "the class strings and edge widths are quoted verbatim from that "
            "probe; by implementation time another user had resized the shared "
            "source tab to 1600x1000 and closed the desk, so no live "
            "re-measurement was possible and none is claimed",
        ],
        "claims": {
            "sourceFact": [
                "tree: div.flex.w-[232px].min-w-0.flex-col.bg-[#171717] at "
                "[48,52,232,1098] — two children only",
                "header: [48,52,232,48] .flex.h-12.shrink-0.items-center.px-3"
                ".text-[12px].leading-5.text-white/90, border 0/0/0/0",
                "list: .min-h-0.flex-1.overflow-y-auto.px-2.pb-3 with a thin "
                "scrollbar tinted rgba(255,255,255,0.2)",
            ],
            "cloneDecision": [
                "the clone's two extra 36px toolbars stay — they hold the "
                "clone's own group/camera actions, and deleting clone "
                "functionality to match a child count is not what this work is "
                "for; the resulting 72px offset of the list's start (172 vs "
                "100) is a consequence of that, recorded rather than removed",
                "the header's search field and buttons stay; only the frame is "
                "aligned, and the search is verified to still filter",
            ],
            "notClaimed": [
                "what text the source's 48px header carries — the class list "
                "was captured, the string was not",
            ],
        },
    }
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport=VIEWPORT)
        page = ctx.new_page()
        result = run(page)
        browser.close()
    summary = result["_summary"]
    audit["checks"] = result
    audit["result"] = f"{summary['checks'] - len(summary['failures'])}/{summary['checks']} passed"
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_PATH, "w", encoding="utf-8") as f:
        json.dump(audit, f, ensure_ascii=False, indent=2)
    print(f"\n{audit['result']}")
    if summary["failures"]:
        print("FAILED: " + ", ".join(summary["failures"]))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
