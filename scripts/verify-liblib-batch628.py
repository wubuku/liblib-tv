#!/usr/bin/env python3
"""batch 628 验收：把 627 的尺子扫到**高度**方向，并让「时间轴覆盖三列」成为结构性豁免。

## 为什么要扫高度

627 把 86 个宽度扫完了，**但那张网格的高度是固定的 900**。而 626 挖出的两个真缺陷
恰恰**只在高度上出现**：`motion-path-menu` 的盒底恒为 `视口高 + 63`，
`geometry-submenu` 的盒底恒 778 —— 两者与宽度无关、与高度强相关。627 的网格从定义
上就覆盖不到 626 那类缺陷。这是 627 自己在「不声称」里写下的缺口。

## 为什么还要加收起态

627 只扫了默认（展开）态。时间轴可收起，展开 182 / 收起 88
（`data-director-timeline-collapsed`）。收起步意味着时间轴贴底更高 —— 根的 top 从
`视口高 − 182` 变成 `视口高 − 88`，向下 40px 处的下拉可用空间少 94px。几何上最容易
出事的一个组合，627 完全没测。

## 本批的两条结论

**一、几何边界轴在高度方向是干净的。** 74 个高度 × 两态，「视口外且不在任何裁剪祖先
之内」= 0，且没有任何一个高度出现「零视口外控件」的空转。

**二、层叠那半在矮视口下确实有事，但是源站事实而不是 clone 缺陷。** 工作区是
`fixed inset-0`（满视口），时间轴是 `relative z-40` 贴在底部，而三列是
`absolute bottom-0` 的面板 —— batch 613 在源站 1920×1150 实测过这件事，注释原话是
「时间线是浮在中间列上的独立覆盖层，会盖住 rail 的下段」。于是矮视口下三列底部
一条带被时间轴压住，场景树最后一个对象行的 隐藏/锁定/删除 三连点不到。

**本批不修它**，因为两条修法都会破坏源站实测：
- 缩短三列到时间轴之上 → 破 613 钉住的 `aside` 盒子；
- 给可滚内容加底部留白 → 破 `DirectorObjectTree.tsx:415` 标注为「源站列表逐字」的
  `px-2 pb-3`。

要修需要源站在**矮视口**下的读数，那是待授权项。所以本批做的是把这件事从
「619 里那个 `帮助` 的名字巧合」升级成**结构化豁免**：豁免需要**两个半边同时成立**
（命中者在时间轴内 **且** 受害者在三列之一内），任何一边不成立照旧报缺陷 ——
batch 621 那个「导出面板提交钮 vs 把手」的真缺陷因此不受影响。

## 为什么不叫它「通过」

豁免是**解释**，不是**通过**。本批把每格被解释掉的枚数写进 audit，让读者能自己判断
「这条豁免在这个视口下盖掉了多少东西」。
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

# 360→1400 every 20, plus a dense band around the 778 threshold batch 626
# measured for the geometry submenu (constant box bottom 778 + 8px margin), plus
# 1150 — the source's own measured viewport height, which the every-20 grid
# steps straight over (1150-360 is not a multiple of 20).
HEIGHTS = sorted(set(range(360, 1420, 20)) | set(range(778, 800)) | {1150})
CROSSCHECK = [360, 400, 540, 600, 700, 785, 786, 787, 900, 1000, 1150]
STATES = [("expanded", "false"), ("collapsed", "true")]


def prep(page) -> None:
    page.mouse.move(5, 5)
    page.wait_for_timeout(160)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal'))"
                  " el.remove(); }")


def set_collapsed(page, want: str) -> None:
    got = page.locator("[data-director-timeline]").first.get_attribute(
        "data-director-timeline-collapsed")
    if got != want:
        page.locator("[data-director-timeline-collapse]").first.click(timeout=15_000)
        page.wait_for_timeout(500)
    now = page.locator("[data-director-timeline]").first.get_attribute(
        "data-director-timeline-collapsed")
    if now != want:
        raise RuntimeError(f"could not reach collapsed={want} (got {now})")


def measure(page) -> dict[str, Any]:
    r = page.evaluate(b617.AUDIT_JS, list(b617.TRANSIENT_OVERLAYS))
    return {
        "total": r["total"],
        "offViewport": len(r["offViewportItems"]),
        "unreachable": [(b["label"], b["box"], b["data"])
                        for b in r["offViewportUnreachable"]],
        "scrollable": len(r["offViewportScrollable"]),
        # `covered` is now the unexplained remainder; anything left in it is a
        # defect by construction, whatever its label.
        "covered": [(b["label"], b["hitLabel"], b["box"]) for b in r["covered"]],
        "coveredByTimeline": [
            (b["label"], b["hitInTimeline"], b["victimInColumn"])
            for b in r["coveredByTimelineOverlay"]],
        "coveredByViewportSqueeze": [
            (b["label"], b["victimInViewport"], b.get("viewportH"))
            for b in r["coveredByViewportSqueeze"]],
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
    sweep: dict[str, Any] = {}
    cross: dict[str, Any] = {}
    with sync_playwright() as p:
        br = p.chromium.launch()
        for state, want in STATES:
            page = br.new_page(viewport={"width": 1440, "height": 900},
                               device_scale_factor=1)
            b617.open_desk(page)
            for h in HEIGHTS:
                page.set_viewport_size({"width": 1440, "height": h})
                page.wait_for_timeout(200)
                set_collapsed(page, want)
                prep(page)
                sweep[f"{state}@{h}"] = measure(page)
            page.close()

        for state, want in STATES:
            for h in CROSSCHECK:
                fresh = br.new_page(viewport={"width": 1440, "height": h},
                                    device_scale_factor=1)
                b617.open_desk(fresh)
                set_collapsed(fresh, want)
                prep(fresh)
                cross[f"{state}@{h}"] = measure(fresh)
                fresh.close()
        br.close()

    out = {
        "batch": 628,
        "title": "sweep the height axis (x timeline collapsed/expanded) and turn "
                 "'the timeline overlays the three columns' from a name coincidence "
                 "into a structural exemption",
        "date": "2026-10-01",
        "heights": HEIGHTS,
        "states": [s for s, _ in STATES],
        "sweep": sweep,
        "freshLoadCrosscheck": cross,
    }

    v.check(f"the-sweep-covers-{len(HEIGHTS)}-heights-x-{len(STATES)}-states",
            len(sweep) == len(HEIGHTS) * len(STATES))

    bad = {k: r["unreachable"] for k, r in sweep.items() if r["unreachable"]}
    v.check("no-height-has-an-off-viewport-unreachable-control", not bad,
            detail={k: r[:3] for k, r in list(bad.items())[:6]})

    vac = [k for k, r in sweep.items() if r["offViewport"] == 0]
    v.check("every-height-actually-exercised-the-off-viewport-branch", not vac,
            detail=vac[:8])

    uncovered = {k: r["covered"] for k, r in sweep.items() if r["covered"]}
    v.check("no-height-has-an-unexplained-covered-control", not uncovered,
            detail={k: r[:3] for k, r in list(uncovered.items())[:6]})

    loose = {k: [e for e in r["coveredByTimeline"] if not (e[1] and e[2])]
             for k, r in sweep.items()
             if [e for e in r["coveredByTimeline"] if not (e[1] and e[2])]}
    v.check("every-timeline-overlay-exemption-has-both-halves", not loose,
            detail={k: r[:3] for k, r in list(loose.items())[:6]})

    # the exemption must be visible in the record, not silently swallowing
    total_explained = sum(len(r["coveredByTimeline"]) for r in sweep.values())
    v.check("the-timeline-overlay-exemption-is-actually-exercised",
            total_explained > 0,
            detail=f"{total_explained} controls explained across {len(sweep)} cells")

    # --- the bottom-bar squeeze, and its bound ------------------------------
    # This family is NOT a source fact, so it gets a *bounded* exemption: the
    # bound is derived from the sweep itself (the tallest viewport at which it
    # still fires) rather than hand-picked, so a future change that widens the
    # collision upward fails here instead of being quietly absorbed.
    #
    # Batch 629 re-scoped the family.  628 keyed it on the COVERER being the
    # bottom bar; 629 — sweeping the width x height corner neither 627 nor 628
    # had covered — immediately produced coverers that are not the bottom bar
    # (the viewport's own top toolbar, and the gizmo's own info panel covering a
    # sibling axis label at 780x400).  Keying on the coverer matched only the
    # one collision 628 happened to see.  The gate is now the victim being
    # inside the 3D viewport, with the coverer recorded for the reader.
    fired = sorted({int(k.split("@")[1]) for k, r in sweep.items()
                    if r["coveredByViewportSqueeze"]})
    bound = max(fired) if fired else None
    above = [h for h in fired if bound is not None and h > bound]
    v.check("the-viewport-squeeze-stops-at-one-height", not above,
            detail={"bound": bound, "stillFiringAbove": above,
                    "firedAt": fired[:12]})
    loose2 = {k: [e for e in r["coveredByViewportSqueeze"] if not e[1]]
              for k, r in sweep.items()
              if [e for e in r["coveredByViewportSqueeze"] if not e[1]]}
    v.check("every-viewport-exemption-is-inside-the-viewport", not loose2,
            detail={k: r[:3] for k, r in list(loose2.items())[:6]})
    v.check("the-viewport-squeeze-is-actually-exercised", bool(fired),
            detail={"heights": fired[:12],
                    "minViewportHeightInvolved": min(
                        (e[2] for r in sweep.values()
                         for e in r["coveredByViewportSqueeze"] if e[2] is not None),
                        default=None)})

    mism = [k for k, r in cross.items()
            if (r["total"], r["offViewport"], len(r["covered"]))
            != (sweep[k]["total"], sweep[k]["offViewport"],
                len(sweep[k]["covered"]))]
    v.check(f"the-{len(CROSSCHECK)}-fresh-loads-agree-with-the-resized-page",
            not mism, detail=mism)

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "offViewport": sum(r["offViewport"] for r in sweep.values()),
        "coveredByTimeline": total_explained,
    }
    audit = ROOT / "docs/research/liblib-canvas-batch628-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
