#!/usr/bin/env python3
"""batch 713 验收：712 的「4.24 上限」是视口边缘，不是夹紧

## 起点

712 测出：标尺左侧精确按 `t = frac × duration` 映射，frac ≥ 0.54 之后 t 冻结在
**4.240000131736106**，而 `duration = 8`、关键帧在 0/4/8 —— 三者对不上。
712 把它记成「死区而不是夹紧」，并把 4.24 当成播放头的上限。

**本批证明那个上限不存在。** 读法换成：**时间轴是横向可滚动的，标尺比可见视口宽**，
点不到的那一段**在视口外面**。

## 决定性读数

| 读数 | 值 |
|---|---|
| 标尺宽度 / 滚动容器 `clientWidth` | 1779.125 / **958** |
| 可见边缘对应的 frac | **0.5385** |
| 712 里冻结开始的 frac | **0.53** |
| 横向滚到底（`scrollLeft = 821`）后点 frac 0.75 | **`t = 6`** |
| 横向滚到底后点 frac 0.99 | **`t = 7.92`** |

**同一个 frac，滚不滚动差 1.76 秒。** ⟹ 712 的读数全部存活，**解释要换**。

## 五条预测（写死在代码里，先于任何测量）

- **P1** 默认缩放下标尺比可见视口宽约 1.86 倍（46% 的时间轴在视口外）
- **P2** 冻结开始的 frac **就是**可见边缘的 frac
- **P3** 横向滚动之后同样的 frac 能点出更大的 t ⟹ **没有 4.24 上限**
- **P4** 滚轮是有效的横向滚动手势
- **P5** 播放头的真实上限是 `duration`（8s）

## 判据

1. `at-default-zoom-the-timeline-is-wider-than-its-visible-pane`
2. `the-frozen-fraction-is-exactly-the-visible-edge`
3. `scrolling-the-timeline-moves-the-playhead-past-four-point-two-four`
4. `the-wheel-scrolls-the-timeline-horizontally`
5. `the-real-playhead-ceiling-is-the-duration`
6. `retraction-of-712-the-4-24-ceiling-is-the-visible-edge-not-a-clamp`
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch713-2026-10-01"
W, DESK_H = 1280, 1150
RULER_Y_OFFSET = 18          # 标尺盒子的纵向中点（相对 ruler 顶部）

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

PREDICTIONS = {
    "P1": "默认缩放下标尺比可见视口宽约 1.86 倍（46% 的时间轴在视口外）",
    "P2": "冻结开始的 frac 就是可见边缘的 frac",
    "P3": "横向滚动之后同样的 frac 能点出更大的 t —— 没有 4.24 上限",
    "P4": "滚轮是有效的横向滚动手势",
    "P5": "播放头的真实上限是 duration（8s）",
}

READ = r"""() => {
  const s = window.__director_store.getState();
  const t = s.timeline || {};
  const ruler = document.querySelector('[data-director-timeline-ruler]');
  const canvas = document.querySelector('[data-director-timeline-canvas]');
  const scroller = canvas ? canvas.parentElement : null;
  const rb = ruler ? ruler.getBoundingClientRect() : null;
  return {
    t: t.playheadTime !== undefined ? t.playheadTime : t.currentTime,
    zoom: t.zoom, duration: t.duration,
    rulerW: rb ? rb.width : null, rulerX: rb ? rb.x : null, rulerY: rb ? rb.y : null,
    scrollerClientW: scroller ? scroller.clientWidth : null,
    scrollerScrollW: scroller ? scroller.scrollWidth : null,
    scrollLeft: scroller ? scroller.scrollLeft : null,
    overflowX: scroller ? getComputedStyle(scroller).overflowX : null,
  };
}"""

SEL_CAMERA = r"""() => {
  const s = window.__director_store.getState();
  const c = s.objects.find((o) => o.kind === 'camera');
  const row = document.querySelector('[data-director-tree] [role="treeitem"]'
    + '[data-director-object-id="' + c.id + '"]');
  if (row) row.click();
  return !!row;
}"""


def read(page: Page) -> dict[str, Any]:
    return page.evaluate(READ)


def fresh(browser: Any) -> Page:
    page = browser.new_page(viewport={"width": W, "height": DESK_H},
                            device_scale_factor=1)
    b617.open_desk(page)
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(300)
    page.evaluate(SEL_CAMERA)
    page.wait_for_timeout(600)
    return page


def click_frac(page: Page, frac: float) -> float:
    r = read(page)
    page.mouse.click(r["rulerX"] + r["rulerW"] * frac, r["rulerY"] + RULER_Y_OFFSET)
    page.wait_for_timeout(420)
    return read(page)["t"]


def run(browser: Any) -> dict[str, Any]:
    page = fresh(browser)
    geo = read(page)
    unscrolled = {str(f): click_frac(page, f) for f in (0.53, 0.75, 0.99)}

    # 真实手势：滚轮横向滚到底
    page.mouse.move(700, geo["rulerY"] + RULER_Y_OFFSET)
    page.mouse.wheel(3000, 0)
    page.wait_for_timeout(700)
    scrolled = read(page)
    scrolled_hits = {str(f): click_frac(page, f) for f in (0.05, 0.50, 0.75, 0.99)}

    # 反向滚回
    page.mouse.wheel(-3000, 0)
    page.wait_for_timeout(700)
    back = read(page)
    page.close()
    visible_edge_frac = geo["scrollerClientW"] / geo["rulerW"]
    return {
        "geo": geo, "unscrolled": unscrolled,
        "scrolledLeft": scrolled["scrollLeft"], "scrolledHits": scrolled_hits,
        "backLeft": back["scrollLeft"], "tAfterBack": back["t"],
        "visibleEdgeFrac": visible_edge_frac,
        "visibleEdgeT": visible_edge_frac * geo["duration"],
        "widthRatio": geo["rulerW"] / geo["scrollerClientW"],
    }


def check_1(r: dict[str, Any]) -> None:
    g = r["geo"]
    assert g["overflowX"] == "auto", g["overflowX"]
    assert g["rulerW"] > g["scrollerClientW"], g
    assert abs(g["scrollerScrollW"] - g["rulerW"]) < 1, g
    assert 1.8 < r["widthRatio"] < 1.9, f"宽度比 {r['widthRatio']} 不是 ~1.86"


def check_2(r: dict[str, Any]) -> None:
    # 712 记录冻结开始于 frac 0.53；可见边缘是 0.5385 —— 两者必须是同一个位置
    assert abs(r["visibleEdgeFrac"] - 0.5385) < 0.005, r["visibleEdgeFrac"]
    assert abs(r["unscrolled"]["0.53"] - r["unscrolled"]["0.99"]) < 0.001, \
        "未滚动时 0.53 与 0.99 应该落在同一个值"
    assert abs(r["unscrolled"]["0.99"] - r["visibleEdgeT"]) < 0.15, \
        (r["unscrolled"], r["visibleEdgeT"])


def check_3(r: dict[str, Any]) -> None:
    assert r["scrolledLeft"] > 700, r["scrolledLeft"]
    # 同一个 frac，滚动之后能点出更大的 t
    assert r["scrolledHits"]["0.75"] > r["unscrolled"]["0.99"] + 1.0, \
        (r["scrolledHits"], r["unscrolled"])
    assert abs(r["scrolledHits"]["0.75"] - 6.0) < 0.05, r["scrolledHits"]["0.75"]
    # 712 那个「上限」在滚动后不再成立
    assert r["scrolledHits"]["0.99"] > 4.5, r["scrolledHits"]


def check_4(r: dict[str, Any]) -> None:
    assert r["backLeft"] == 0, f"反向滚轮没回到 0：{r['backLeft']}"


def check_5(r: dict[str, Any]) -> None:
    d = r["geo"]["duration"]
    assert d == 8, d
    assert abs(r["scrolledHits"]["0.99"] - d) < 0.1, \
        f"滚到最右点 99% 只到 {r['scrolledHits']['0.99']}，duration 是 {d}"


def check_6(r: dict[str, Any]) -> None:
    """撤回 712 的两条解释：不是死区、不是 4.24 上限，而是视口边缘。
    712 的读数（右侧点不动）全部存活。"""
    assert r["unscrolled"]["0.75"] == r["unscrolled"]["0.99"], r["unscrolled"]
    assert r["scrolledHits"]["0.75"] > 5.9, r["scrolledHits"]


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {"predictions": PREDICTIONS}
    failures: list[str] = []
    got: dict[str, Any] = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            got["run"] = run(browser)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"run: {exc}")
            got["run"] = {}
        browser.close()
    results.update(got)
    checks = [
        ("at-default-zoom-the-timeline-is-wider-than-its-visible-pane", lambda: check_1(got.get("run", {}))),
        ("the-frozen-fraction-is-exactly-the-visible-edge", lambda: check_2(got.get("run", {}))),
        ("scrolling-the-timeline-moves-the-playhead-past-four-point-two-four", lambda: check_3(got.get("run", {}))),
        ("the-wheel-scrolls-the-timeline-horizontally", lambda: check_4(got.get("run", {}))),
        ("the-real-playhead-ceiling-is-the-duration", lambda: check_5(got.get("run", {}))),
        ("retraction-of-712-the-4-24-ceiling-is-the-visible-edge-not-a-clamp", lambda: check_6(got.get("run", {}))),
    ]
    summary: dict[str, bool] = {}
    for name, fn in checks:
        try:
            fn()
            summary[name] = True
        except Exception as exc:  # noqa: BLE001
            summary[name] = False
            failures.append(f"{name}: {exc}")
    results["summary"] = summary
    results["failures"] = failures
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1, default=str))
    for name, ok in summary.items():
        print(("PASS " if ok else "FAIL ") + name)
    for f in failures:
        print("  ->", f[:400])
    print(f"\n{sum(1 for v in summary.values() if v)}/{len(summary)} 通过")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
