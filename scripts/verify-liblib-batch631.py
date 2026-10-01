#!/usr/bin/env python3
"""batch 631 验收：把「收起侧栏」这个**状态**当轴扫（623 留下的候选：
宽度 × 状态矩阵才是完整面），并把 628 第一族**量化归因**到场景树行按钮。

## 为什么扫这个状态

630 刚把镜头条确认为三族盖住者之一，而 `viewportPanelsCollapsed`
（用户可见的「收起」按钮，`data-director-panels-toggle`）在 ≥899 会隐藏
场景对象列、并给场景树加 `inert`——**它会抽掉第一族的埋藏对象**。所以这个
开关既是 623 留下的那条候选，又直接关系到 628 那族「暂不修」的解释。

## 本批三条结论

1. **「收起侧栏」态在几何上干净**：2 态 × 11 窗口 × 2 时间轴 = 44 格，
   够不着 0 / 零尺寸 0 / 无法解释 0（零尺寸检查是 623 立的，因为普查**结构上
   看不见**塌成 0 尺寸的控件——623 在 899 上抓到整列 `[0,0,0,0]`、7 枚活控件
   凭空消失）。
2. **628 第一族被量化归因**：≥899 收起侧栏后掩埋数 14 → 2、10 → 1、4 → 1，
   剩下的那枚是图标栏的 `帮助`（613 在源站实测过它被时间线盖住，属另一条
   源站事实）。**所以那一族的埋藏对象就是场景树的行按钮三连**；侧栏不在，
   它就基本消失。≤898 侧栏本就是屏外抽屉，掩埋恒 0。
3. **≤898 时「收起」是一个只让自己消失的空按钮**：场景树本来已是屏外
   `inert` 抽屉（`-220,88`），点击前后场景树盒与视口盒**逐像素相同**，
   唯一可见效果是该按钮自身消失（源码 `{!viewportPanelsCollapsed ? … : null}`）。

**本批不修第三条**，理由与 628 对第一族的处置同源：**源站窄屏顶栏未取证**
（待授权清单第 10 项）。而本批把那个笼统的问题**具体化**成了一个可回答的单点
问题——「源站窄屏顶栏上有没有「收起侧栏」这个按钮」。

## 本批被自己推翻的两个预测（都记下来）

- 猜「这个开关会抽掉镜头条」→ **错**：镜头条在 `collapsed=True` 下仍在
  `281,52 1639x36`，所以 630 的第三族盖住者不受它影响。
- 猜「≤898 收起后就再也回不来」→ **错**：窄屏有「打开场景对象」/「打开属性
  面板」两个可点入口，抽屉能开，`DirectorDesk.tsx:412` 的 effect 会把
  `collapsed` 复位。**不是死局。**

## 不声称

- 源站任何事。窄屏顶栏上是否存在这个按钮**未取证**，故不主张删也不主张留。
- 「收起」按钮在 ≤898 应当被删。这是产品决定，且需要源站读数。
"""
import importlib.util
import json
import sys
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
b623 = _load("623")
b629 = _load("629")

# 623's breakpoint convention: >=899 is the three-column desktop layout, <=898
# turns the tree into an off-screen drawer.
NARROW_MAX = 898

WINDOWS = [(1920, 1150), (1440, 900), (1440, 660), (1280, 720), (1024, 800),
           (900, 500), (899, 700), (898, 700), (780, 600), (480, 700), (360, 640)]
TIMELINES = [182, 420]
CROSSCHECK = [(1440, 900, 420), (899, 700, 420), (780, 600, 420), (1920, 1150, 420)]

GEOM_JS = """() => {
  const rd = (sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {t: Math.round(r.top * 100) / 100, l: Math.round(r.left * 100) / 100,
            w: Math.round(r.width * 100) / 100, h: Math.round(r.height * 100) / 100,
            b: Math.round(r.bottom * 100) / 100,
            r: Math.round(r.right * 100) / 100,
            display: getComputedStyle(el).display,
            inert: el.hasAttribute('inert')};
  };
  return {
    collapsed: window.__director_store.getState().viewportPanelsCollapsed,
    viewport: rd('[data-director-viewport]'),
    bottomBar: rd('[data-director-bottom-bar]'),
    tree: rd('aside[aria-label="场景对象"]'),
    inspector: rd('aside[aria-label="属性"]'),
    rail: rd('[data-director-icon-rail]'),
    shotBar: rd('[data-director-shot-bar]'),
    timeline: rd('[data-director-timeline]'),
  };
}"""


def column_of(box: list[float], g: dict[str, Any]) -> str:
    """Which column a victim box belongs to, by geometry.

    The census records no column on `coveredByTimelineOverlay` rows, and adding
    a field to the shared AUDIT_JS for one batch's question is the wrong trade.
    The three columns do not overlap in x (rail 0..48, tree 48..281, inspector
    to the right of the viewport), so the centre point classifies them exactly.
    """
    cx = box[0] + box[2] / 2
    for name, sel in (("rail", "rail"), ("tree", "tree"), ("inspector", "inspector")):
        rect = g.get(sel)
        if rect and rect["display"] != "none" and rect["w"] > 0 \
                and rect["l"] - 0.5 <= cx <= rect["r"] + 0.5:
            return name
    return "other"


def prep(page) -> None:
    page.mouse.move(5, 5)
    page.wait_for_timeout(140)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal'))"
                  " el.remove(); }")


def ask_panels(page, want: bool) -> None:
    page.evaluate("(v) => window.__director_store.getState()"
                  ".setViewportPanelsCollapsed(v)", want)
    page.wait_for_timeout(260)


def ask_timeline(page, want: int) -> None:
    page.evaluate("(n) => window.__director_store.getState().setTimelineHeight(n)", want)
    page.wait_for_timeout(200)


def measure(page) -> dict[str, Any]:
    r = page.evaluate(b617.AUDIT_JS, list(b617.TRANSIENT_OVERLAYS))
    g = page.evaluate(GEOM_JS)
    z = page.evaluate(b623.BLIND_JS)
    vp = g["viewport"]
    return {
        "total": r["total"],
        "offViewport": len(r["offViewportItems"]),
        "unreachable": [(b["label"], b["box"], b["data"])
                        for b in r["offViewportUnreachable"]],
        "zeroSize": z,
        "unexplained": [(b["label"], b["hitLabel"], b["box"]) for b in r["covered"]],
        "timelineOverlay": [(b["label"], b["box"], b["hitLabel"],
                             column_of(b["box"], g))
                            for b in r["coveredByTimelineOverlay"]],
        "squeezeRows": [(b["label"], b["box"], b["hitLabel"])
                        for b in r["coveredByViewportSqueeze"]],
        "squeezeCoverers": [(b["label"], bool(b.get("hitInBottomBand")),
                             bool(b.get("hitInTimeline")),
                             bool(b.get("hitInShotBar")))
                            for b in r["coveredByViewportSqueeze"]],
        "blocked": [(b["label"], b["box"], b["panel"], b["timelineOverlay"],
                     b["clipped"], b["victimInViewport"])
                    for b in r["blocked"]],
        "geom": g,
        "viewportH": round(vp["h"], 3) if vp else None,
        "viewportTop": round(vp["t"], 3) if vp else None,
        "band": g["bottomBar"]["h"] if g["bottomBar"] else None,
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
    click_probe: dict[str, Any] = {}
    cross: dict[str, Any] = {}
    with sync_playwright() as p:
        br = p.chromium.launch()
        for collapsed in (False, True):
            page = br.new_page(viewport={"width": 1440, "height": 900},
                               device_scale_factor=1)
            b617.open_desk(page)
            ask_panels(page, collapsed)
            for w, h in WINDOWS:
                page.set_viewport_size({"width": w, "height": h})
                page.wait_for_timeout(190)
                for th in TIMELINES:
                    ask_timeline(page, th)
                    prep(page)
                    cells[f"collapsed={collapsed}/{w}x{h}/tl={th}"] = measure(page)
            page.close()

        # The button a user actually presses, and whether it changes anything.
        for w, h in ((1440, 900), (899, 700), (780, 600), (360, 640)):
            page = br.new_page(viewport={"width": w, "height": h},
                               device_scale_factor=1)
            b617.open_desk(page)
            page.wait_for_timeout(260)
            before = page.evaluate(GEOM_JS)
            tg = page.locator("[data-director-panels-toggle]").first
            visible = bool(tg.count()) and tg.is_visible()
            after = None
            if visible:
                tg.click(timeout=15_000)
                page.wait_for_timeout(500)
                after = page.evaluate(GEOM_JS)
            entries = page.evaluate("""() => {
              const out = [];
              for (const el of document.querySelectorAll(
                  'button,[role="button"],[role="switch"],a[href]')) {
                const r = el.getBoundingClientRect();
                const cs = getComputedStyle(el);
                if (r.width === 0 || r.height === 0) continue;
                if (r.right <= 0 || r.left >= innerWidth) continue;
                if (r.bottom <= 0 || r.top >= innerHeight) continue;
                if (cs.display === 'none' || cs.pointerEvents === 'none') continue;
                const label = el.getAttribute('aria-label') || el.getAttribute('title')
                              || (el.textContent || '').trim().slice(0, 12);
                if (label) out.push(label);
              }
              return out;
            }""")
            click_probe[f"{w}x{h}"] = {
                "width": w, "toggleVisible": visible, "before": before,
                "after": after, "onScreenLabelsAfter": entries,
            }
            page.close()

        for w, h, th in CROSSCHECK:
            fresh = br.new_page(viewport={"width": w, "height": h},
                                device_scale_factor=1)
            b617.open_desk(fresh)
            ask_panels(fresh, True)
            ask_timeline(fresh, th)
            prep(fresh)
            cross[f"{w}x{h}/tl={th}"] = measure(fresh)
            fresh.close()
        br.close()

    out = {
        "batch": 631,
        "title": "the sidebar-collapse state as an axis, and the first family "
                 "quantified onto the scene tree's row buttons",
        "date": "2026-10-01",
        "windows": WINDOWS,
        "timelineHeights": TIMELINES,
        "cells": cells,
        "clickProbe": click_probe,
        "freshLoadCrosscheck": cross,
    }

    v.check(f"the-grid-covers-2state-x-{len(WINDOWS)}w-x-{len(TIMELINES)}tl",
            len(cells) == 2 * len(WINDOWS) * len(TIMELINES), detail=len(cells))

    # --- 1) the state is geometrically clean ----------------------------
    bad = {k: r["unreachable"] for k, r in cells.items() if r["unreachable"]}
    v.check("no-cell-has-an-off-viewport-unreachable-control", not bad,
            detail={k: r[:3] for k, r in list(bad.items())[:6]})

    zbad = {k: r["zeroSize"] for k, r in cells.items() if r["zeroSize"]}
    v.check("no-cell-has-a-control-collapsed-to-nothing", not zbad,
            detail={k: r[:4] for k, r in list(zbad.items())[:6]})

    uncov = {k: r["unexplained"] for k, r in cells.items() if r["unexplained"]}
    v.check("no-cell-has-an-unexplained-covered-control", not uncov,
            detail={k: r[:3] for k, r in list(uncov.items())[:6]})

    vac = [k for k, r in cells.items() if r["offViewport"] == 0]
    v.check("every-cell-actually-exercised-the-off-viewport-branch", not vac,
            detail=vac[:8])

    # --- 3) non-vacuity: the state really changes the layout ------------
    changed, wide_pairs = [], []
    for w, h in WINDOWS:
        a = cells[f"collapsed=False/{w}x{h}/tl={TIMELINES[-1]}"]
        b = cells[f"collapsed=True/{w}x{h}/tl={TIMELINES[-1]}"]
        ga, gb = a["geom"], b["geom"]
        if ga["tree"] != gb["tree"] or ga["viewport"] != gb["viewport"]:
            changed.append(f"{w}x{h}")
        if w > NARROW_MAX:
            wide_pairs.append({"cell": f"{w}x{h}",
                               "total": (a["total"], b["total"]),
                               "treeDisplay": (ga["tree"]["display"],
                                               gb["tree"]["display"]),
                               "viewportLeft": (ga["viewport"]["l"],
                                                gb["viewport"]["l"])})
    v.check("the-collapse-state-actually-changes-the-layout", bool(changed),
            detail={"changedCells": changed, "widePairs": wide_pairs[:6]})
    # Collapsing must both remove the column and hand its width to the
    # viewport — the first half alone would pass for a panel that hid itself
    # without reflowing anything.
    v.check("at-899-and-above-collapsing-removes-the-column-and-widens-the-viewport",
            all(p["treeDisplay"] == ("block", "none")
                and p["viewportLeft"][1] < p["viewportLeft"][0]
                and p["total"][1] < p["total"][0]
                for p in wide_pairs),
            detail=wide_pairs[:6])

    # --- 2) the first family, attributed by column ----------------------
    # With the sidebar gone at >=899, every remaining victim must sit in the
    # ICON RAIL (the 48px strip that stays) and NOT one may be a tree row.
    # Getting this wrong the first time is the point: my expectation was
    # "only 帮助 is left", and the readings said 帮助 / AI 识图导入 /
    # 选择画幅比例 / 全景图 / 添加机位 / 添加角色 — all rail entries, because a
    # 420px-tall timeline buries more of the rail than the 182px default did.
    survivors = {}
    wrong_column = {}
    for k, r in cells.items():
        if not k.startswith("collapsed=True/"):
            continue
        w = int(k.split("/")[1].split("x")[0])
        if w <= NARROW_MAX:
            continue
        cols = {row[3] for row in r["timelineOverlay"]}
        if cols - {"rail"}:
            wrong_column[k] = sorted(cols)
    v.check("with-the-sidebar-gone-no-tree-row-stays-buried", not wrong_column,
            detail=dict(list(wrong_column.items())[:6]))

    # ...and the same victims in the same cells WITH the sidebar present must
    # include tree rows, which is what makes it an attribution rather than a
    # coincidence of counts.
    tree_rows_present = {}
    for k, r in cells.items():
        if not k.startswith("collapsed=False/"):
            continue
        w = int(k.split("/")[1].split("x")[0])
        if w <= NARROW_MAX:
            continue
        cols = {row[3] for row in r["timelineOverlay"]}
        if "tree" in cols:
            tree_rows_present[k] = sorted(cols)
    v.check("with-the-sidebar-present-tree-rows-are-buried", bool(tree_rows_present),
            detail=dict(list(tree_rows_present.items())[:6]))

    # ...and the comparison that makes it an attribution rather than a
    # coincidence: the same cell with the sidebar present buries strictly more.
    deltas = []
    for w, h in WINDOWS:
        a = cells[f"collapsed=False/{w}x{h}/tl={TIMELINES[-1]}"]["timelineOverlay"]
        b = cells[f"collapsed=True/{w}x{h}/tl={TIMELINES[-1]}"]["timelineOverlay"]
        if len(a) != len(b):
            deltas.append({"cell": f"{w}x{h}", "withSidebar": len(a),
                           "withoutSidebar": len(b)})
    v.check("the-burial-count-drops-when-the-sidebar-is-collapsed", bool(deltas),
            detail=deltas[:8])

    # --- 4) the narrow-screen no-op, as a falsifiable claim -------------
    # At <=898 the tree is already an off-screen inert drawer, so pressing the
    # button must not move a pixel of the tree or the viewport.  This is the
    # finding, stated so it can be overturned by evidence.
    noop_ok, moved = [], []
    for key, cp in click_probe.items():
        if cp["width"] > NARROW_MAX or not cp["toggleVisible"] or not cp["after"]:
            continue
        ga, gb = cp["before"], cp["after"]
        same = (ga["tree"] == gb["tree"] and ga["viewport"] == gb["viewport"]
                and ga["shotBar"] == gb["shotBar"])
        (noop_ok if same else moved).append(key)
    v.check("at-898-and-below-the-collapse-button-moves-nothing", bool(noop_ok)
            and not moved, detail={"noOp": noop_ok, "didMove": moved})

    # ...and it is still a real state, not a write that failed: the store
    # flips, and the button is the thing that disappears.
    flips = {k: (v2["after"]["collapsed"] if v2["after"] else None)
             for k, v2 in click_probe.items()
             if v2["width"] <= NARROW_MAX and v2["toggleVisible"]}
    v.check("the-store-state-really-flips-at-narrow-widths",
            all(x is True for x in flips.values()), detail=flips)

    # ...and the state is recoverable, which is what my own first hypothesis
    # got wrong: the narrow layout has its own drawer entry points.
    recover = {k: [l for l in v2["onScreenLabelsAfter"]
                   if any(s in l for s in ("打开场景对象", "打开属性面板"))]
               for k, v2 in click_probe.items() if v2["width"] <= NARROW_MAX}
    v.check("narrow-widths-keep-a-drawer-entry-point-after-collapsing",
            all(len(x) >= 1 for x in recover.values()), detail=recover)

    # --- 630's law, still holding in this state -------------------------
    diff = {}
    for k, r in cells.items():
        got = {row[0] for row in r["squeezeRows"]}
        want = b629.predict(r)
        if got != want:
            diff[k] = {"observed": sorted(got), "predicted": sorted(want)}
    v.check("629s-closed-form-still-predicts-every-cell-in-both-states", not diff,
            detail=dict(list(diff.items())[:4]))

    not_band = [(k, lab) for k, r in cells.items()
                for lab, band, tl, shot in r["squeezeCoverers"]
                if not band and not ((r["viewportH"] or 0) <= 0.5 and (tl or shot))]
    v.check("every-squeeze-coverer-is-still-an-enumerated-family", not not_band,
            detail=not_band[:6])

    mism = [k for k, r in cross.items()
            if (r["total"], r["offViewport"], len(r["unexplained"]),
                tuple(sorted(x[0] for x in r["squeezeRows"])))
            != (cells[f"collapsed=True/{k}"]["total"],
                cells[f"collapsed=True/{k}"]["offViewport"],
                len(cells[f"collapsed=True/{k}"]["unexplained"]),
                tuple(sorted(x[0] for x in cells[f"collapsed=True/{k}"]["squeezeRows"])))]
    v.check(f"the-{len(CROSSCHECK)}-fresh-loads-agree-with-the-resized-page",
            not mism, detail=mism)

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "unreachable": sum(len(r["unreachable"]) for r in cells.values()),
        "zeroSize": sum(len(r["zeroSize"]) for r in cells.values()),
        "unexplained": sum(len(r["unexplained"]) for r in cells.values()),
        "offViewport": sum(r["offViewport"] for r in cells.values()),
        "buriedWithSidebar": {f"{w}x{h}": len(
            cells[f"collapsed=False/{w}x{h}/tl={TIMELINES[-1]}"]["timelineOverlay"])
            for w, h in WINDOWS},
        "buriedWithoutSidebar": {f"{w}x{h}": len(
            cells[f"collapsed=True/{w}x{h}/tl={TIMELINES[-1]}"]["timelineOverlay"])
            for w, h in WINDOWS},
    }
    audit = ROOT / "docs/research/liblib-canvas-batch631-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
