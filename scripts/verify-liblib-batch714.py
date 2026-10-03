#!/usr/bin/env python3
"""batch 714 验收：zoom 划块的低端 23% 是空行程 —— 划块在动，时间轴不动

## 起点

713 测出：默认 `zoom=44` 时标尺 1779.125px、可见 pane 958px，**46% 的时间轴在视口外**，
必须横向滚动（滚到 `scrollLeft=821`）才看得到全程。712 顺手测了 zoom 划块，结论是
「**只能拖不能点**」，并留下一个拍板项：「想缩小看全程只能拖一枚不能点的划块，
要不要给它加点击落点」。

本批问一个更靠前的问题：**那枚划块到底把什么放大/缩小了？** 它有没有可能根本调不出全程？

## 决定性读数

| 读数 | 值 |
|---|---|
| `timelineWidth` 公式（`DirectorTimeline.tsx:495`） | `Math.max(640, duration × (3.36 + 4.978 × zoom))` |
| canvas 宽度随 zoom | 0..15 恒为 **640px**（下限生效） |
| 渲染出来的 canvas 宽度 | 0..23 恒为 **958px**（`min-w-full` 压住） |
| 第一个真正改变几何的 zoom | **24**（982.66px，`scrollWidth` 983 > 958） |
| zoom 0 与 zoom 23 的刻度/标签/关键帧像素位置 | **逐条完全相同** |
| 划块轨道宽 71px；点在 35% / 38% | zoom 跳到 **87** / **91** |
| 圆钮附近 ±6px 内点击 | zoom **不变** |
| 聚焦后 `ArrowLeft×5` / `Home` / `End` | 44→**39** / **0** / **100** |
| ctrl+滚轮 | zoom 与 `scrollLeft` **都不变** |
| 整段 sweep 后 `history.past` / `lastCommandResult` | **0 条** / **仍为 null** |

**⟹ 滑块低端 24 个整数档（0..23，占行程 23%）对时间轴零影响**：圆钮在走、填充条在长，
刻度、秒标签、关键帧菱形**一个像素都不动**。

## 五条预测（写死在代码里，先于任何测量）

- **P1** zoom 存在一段区间，渲染宽度恒等于 pane 宽（全程可见、横向不溢出）
- **P2** 区间两端（zoom 0 与 23）刻度与关键帧的像素位置**完全相同**
- **P3** zoom=0 不会让播放头失去可达性（640 下限 + `min-w-full` 双重保护）
- **P4** 划块**能点**、**能用方向键** ⟹ 推翻 712 的「只能拖不能点」
- **P5** zoom 是纯视图态：不写历史、不写命令账

## 判据

1. `the-lower-23-of-the-zoom-slider-is-a-dead-band`
2. `the-640px-floor-written-in-the-source-never-renders`
3. `the-playhead-still-reaches-the-whole-course-at-minimum-zoom`
4. `the-zoom-slider-jumps-on-click-and-steps-on-arrow-keys`
5. `zoom-is-pure-view-state`
6. `retraction-of-712-the-slider-was-never-drag-only`
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch714-2026-10-01"
W, DESK_H = 1280, 1150
RULER_Y_OFFSET = 18

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

PREDICTIONS = {
    "P1": "zoom 存在一段区间，渲染宽度恒等于 pane 宽（全程可见、横向不溢出）",
    "P2": "区间两端（zoom 0 与 23）刻度与关键帧的像素位置完全相同",
    "P3": "zoom=0 不会让播放头失去可达性（640 下限 + min-w-full 双重保护）",
    "P4": "划块能点、能用方向键 —— 推翻 712 的「只能拖不能点」",
    "P5": "zoom 是纯视图态：不写历史、不写命令账",
}

READ = r"""() => {
  const s = window.__director_store.getState();
  const t = s.timeline || {};
  const canvas = document.querySelector('[data-director-timeline-canvas]');
  const scroller = canvas ? canvas.parentElement : null;
  const ruler = document.querySelector('[data-director-timeline-ruler]');
  const rng = document.querySelector('[data-director-timeline-zoom]');
  const cb = canvas ? canvas.getBoundingClientRect() : null;
  const rb = ruler ? ruler.getBoundingClientRect() : null;
  const gb = rng ? rng.getBoundingClientRect() : null;
  const r2 = (v) => (v === null ? null : Math.round(v * 100) / 100);
  return {
    zoom: t.zoom, duration: t.duration,
    playhead: t.playheadTime !== undefined ? t.playheadTime : t.currentTime,
    pastLen: s.history && s.history.past ? s.history.past.length : null,
    lastCommandResult: s.lastCommandResult === undefined ? 'ABSENT'
      : (s.lastCommandResult === null ? null : 'SET'),
    canvasW: cb ? r2(cb.width) : null, canvasX: cb ? r2(cb.x) : null,
    canvasCssW: canvas ? canvas.style.width : null,
    scrollerClientW: scroller ? scroller.clientWidth : null,
    scrollerScrollW: scroller ? scroller.scrollWidth : null,
    scrollLeft: scroller ? scroller.scrollLeft : null,
    rulerW: rb ? r2(rb.width) : null,
    rulerX: rb ? r2(rb.x) : null, rulerY: rb ? r2(rb.y) : null,
    rngX: gb ? r2(gb.x) : null, rngY: gb ? r2(gb.y) : null,
    rngW: gb ? r2(gb.width) : null, rngH: gb ? r2(gb.height) : null,
    ticks: [...document.querySelectorAll('[data-director-ruler-tick]')]
      .map((el) => r2(el.getBoundingClientRect().x)),
    labels: [...document.querySelectorAll('[data-director-timeline-ruler] span')]
      .filter((el) => /s$/.test(el.textContent || '') && el.children.length === 0)
      .map((el) => [el.textContent, r2(el.getBoundingClientRect().x)]),
    keyframes: [...document.querySelectorAll('[data-director-keyframe-id]')]
      .map((el) => [el.getAttribute('data-director-keyframe-id'),
                    r2(el.getBoundingClientRect().x)]),
  };
}"""

# 仪器驱动：把值塞进**真实 range 元素**并派发原生 input 事件，
# 于是组件自己的 onChange -> setTimelineZoom 整条路都跑到（不是写 store）。
SET_ZOOM = r"""() => {
  const rng = document.querySelector('[data-director-timeline-zoom]');
  const setter = Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype, 'value').set;
  setter.call(rng, String(window.__z));
  rng.dispatchEvent(new Event('input', { bubbles: true }));
  rng.dispatchEvent(new Event('change', { bubbles: true }));
  return rng.value;
}"""


def read(page: Page) -> dict[str, Any]:
    return page.evaluate(READ)


def set_zoom(page: Page, z: float) -> dict[str, Any]:
    page.evaluate("() => { window.__z = %s; }" % json.dumps(str(z)))
    page.evaluate(SET_ZOOM)
    page.wait_for_timeout(220)
    return read(page)


def fresh(browser: Any) -> Page:
    page = browser.new_page(viewport={"width": W, "height": DESK_H},
                            device_scale_factor=1)
    b617.open_desk(page)
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(300)
    return page


def run(browser: Any) -> dict[str, Any]:
    page = fresh(browser)
    default = read(page)
    curve = {str(z): set_zoom(page, z) for z in (0, 5, 10, 15, 20, 23, 24, 44, 100)}
    page.evaluate(SET_ZOOM)  # 回到 44
    page.evaluate("() => { window.__z = 44; }")
    page.evaluate(SET_ZOOM)
    page.wait_for_timeout(220)

    # --- 真实点击：轨道 35% / 38%，以及圆钮附近 ±6px ---
    g = read(page)
    cy = g["rngY"] + g["rngH"] / 2
    thumb_x = g["rngX"] + 0.44 * g["rngW"]
    clicks: dict[str, Any] = {}
    for label, dx in (("track-35pct", 0.35 * g["rngW"]),
                      ("track-38pct", 0.38 * g["rngW"]),
                      ("thumb-minus-6", -6.0),
                      ("thumb", 0.0),
                      ("thumb-plus-6", 6.0)):
        page.mouse.click(thumb_x + dx, cy)
        page.wait_for_timeout(260)
        clicks[label] = read(page)["zoom"]
        page.evaluate("() => { window.__z = 44; }")
        page.evaluate(SET_ZOOM)
        page.wait_for_timeout(200)

    # --- 真实键盘：聚焦后按键（先断言焦点到位，到位不了就报错） ---
    page.evaluate("() => document.querySelector("
                  "'[data-director-timeline-zoom]').focus()")
    page.wait_for_timeout(150)
    kb: dict[str, Any] = {
        "focusLanded": page.evaluate(
            "() => document.activeElement === document.querySelector("
            "'[data-director-timeline-zoom]')")}
    assert kb["focusLanded"], "zoom 划块没拿到焦点，键盘读数作废"
    kb["start"] = read(page)["zoom"]
    for _ in range(5):
        page.keyboard.press("ArrowLeft")
        page.wait_for_timeout(150)
    kb["after5Left"] = read(page)["zoom"]
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(200)
    kb["afterRight"] = read(page)["zoom"]
    page.keyboard.press("Home")
    page.wait_for_timeout(220)
    kb["afterHome"] = read(page)["zoom"]
    page.keyboard.press("End")
    page.wait_for_timeout(220)
    kb["afterEnd"] = read(page)["zoom"]

    # --- ctrl+滚轮：不是缩放入口 ---
    g = read(page)
    page.evaluate("() => { window.__z = 44; }")
    page.evaluate(SET_ZOOM)
    page.wait_for_timeout(200)
    g = read(page)
    page.mouse.move(g["rulerX"] + 300, g["rulerY"] + RULER_Y_OFFSET)
    page.keyboard.down("Control")
    page.mouse.wheel(0, -240)
    page.wait_for_timeout(500)
    page.keyboard.up("Control")
    wheel = read(page)

    # --- zoom=0 时播放头的可达集（真实点击） ---
    z0 = set_zoom(page, 0)
    hits: dict[str, Any] = {}
    for f in (0.25, 0.50, 0.75, 0.99):
        page.mouse.click(z0["rulerX"] + z0["rulerW"] * f, z0["rulerY"] + RULER_Y_OFFSET)
        page.wait_for_timeout(380)
        hits[str(f)] = read(page)["playhead"]
    page.mouse.click(z0["rulerX"] + z0["rulerW"] - 2, z0["rulerY"] + RULER_Y_OFFSET)
    page.wait_for_timeout(380)
    hits["right-edge-2px"] = read(page)["playhead"]

    # --- 副作用 ---
    for z in (0, 10, 23, 50, 100, 44):
        set_zoom(page, z)
    after = read(page)
    page.close()
    return {"default": default, "curve": curve, "clicks": clicks, "keyboard": kb,
            "wheel": {"zoom": wheel["zoom"], "scrollLeft": wheel["scrollLeft"]},
            "zeroHits": hits, "atZero": {k: z0[k] for k in
                                        ("zoom", "canvasW", "scrollerClientW",
                                         "scrollerScrollW", "rulerW")},
            "afterSweep": {"pastLen": after["pastLen"],
                           "lastCommandResult": after["lastCommandResult"],
                           "zoom": after["zoom"]}}


def check_1(r: dict[str, Any]) -> None:
    """滑块低端 24 个整数档对时间轴零影响。"""
    c = r["curve"]
    for z in ("0", "5", "10", "15", "20", "23"):
        g = c[z]
        assert g["canvasW"] == g["scrollerClientW"], f"zoom {z} 宽度 {g['canvasW']}"
        assert g["scrollerScrollW"] == g["scrollerClientW"], \
            f"zoom {z} 仍在溢出：{g['scrollerScrollW']}"
    # 第一个真正改变几何的档
    assert c["24"]["scrollerScrollW"] > c["24"]["scrollerClientW"], c["24"]
    assert c["24"]["canvasW"] > c["23"]["canvasW"], "zoom 24 应该开始变宽"
    # 两端逐像素相同
    a, b = c["0"], c["23"]
    assert a["ticks"] and a["ticks"] == b["ticks"], "zoom 0 与 23 的刻度位置不同"
    assert a["labels"] == b["labels"], "秒标签位置不同"
    assert a["keyframes"] == b["keyframes"], "关键帧位置不同"
    assert a["canvasW"] == b["canvasW"], (a["canvasW"], b["canvasW"])


def check_2(r: dict[str, Any]) -> None:
    """源码里写着的 640px 下限，在这个布局里永远渲染不出来。"""
    for z in ("0", "5", "10", "15"):
        g = r["curve"][z]
        assert g["canvasCssW"] == "640px", f"zoom {z} 的内联宽是 {g['canvasCssW']}"
        assert g["canvasW"] == 958, f"zoom {z} 却渲染成 {g['canvasW']}"
    assert r["curve"]["20"]["canvasCssW"] == "823.36px", r["curve"]["20"]
    assert r["curve"]["20"]["canvasW"] == 958, "640 下限失效后本该变宽，但仍被压回 958"


def check_3(r: dict[str, Any]) -> None:
    """缩到最小不会让播放头失去可达性，而且此时没有任何横向溢出。"""
    z0 = r["atZero"]
    assert z0["zoom"] == 0, z0
    assert z0["scrollerScrollW"] == z0["scrollerClientW"] == 958, z0
    d = r["default"]["duration"]
    assert d == 8, d
    for f, want in (("0.25", 2.0), ("0.5", 4.0), ("0.75", 6.0)):
        assert abs(r["zeroHits"][f] - want) < 0.01, (f, r["zeroHits"][f])
    assert r["zeroHits"]["0.99"] > 7.9, r["zeroHits"]
    assert r["zeroHits"]["right-edge-2px"] > 7.9, r["zeroHits"]


def check_4(r: dict[str, Any]) -> None:
    """712 说它「只能拖」—— 点得动，方向键也走得动。"""
    c, k = r["clicks"], r["keyboard"]
    assert c["track-35pct"] > 80, c
    assert c["track-38pct"] > c["track-35pct"], c
    assert c["thumb-minus-6"] == 44, c
    assert c["thumb"] == 44, c
    assert c["thumb-plus-6"] == 44, c
    assert k["focusLanded"] is True, k
    assert k["start"] == 44, k
    assert k["after5Left"] == 39, k
    assert k["afterRight"] == 40, k
    assert k["afterHome"] == 0, k
    assert k["afterEnd"] == 100, k


def check_5(r: dict[str, Any]) -> None:
    """zoom 是纯视图态：整段 sweep 不写历史、不写命令账、也不是滚轮入口。"""
    a = r["afterSweep"]
    assert a["pastLen"] == 0, a
    assert a["lastCommandResult"] is None, a
    assert a["zoom"] == 44, a
    assert r["wheel"]["zoom"] == 44, r["wheel"]
    assert r["wheel"]["scrollLeft"] == 0, r["wheel"]


def check_6(r: dict[str, Any]) -> None:
    """撤回 712 的「只能拖不能点」：落点一直有，键盘也一直有。

    712 的读数存活（点在圆钮上确实不动），但那不是「不能点」，是浏览器对
    圆钮的标准行为；点到钮外 6px 就跳。⟹ 「给 zoom 加点击落点」这个拍板项作废。
    """
    c = r["clicks"]
    assert c["track-35pct"] != 44, c
    assert c["thumb-plus-6"] == 44, "圆钮 ±6px 内不动才是 712 读到的那一格"
    assert r["keyboard"]["afterEnd"] == 100, r["keyboard"]


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
        ("the-lower-23-of-the-zoom-slider-is-a-dead-band", lambda: check_1(got.get("run", {}))),
        ("the-640px-floor-written-in-the-source-never-renders", lambda: check_2(got.get("run", {}))),
        ("the-playhead-still-reaches-the-whole-course-at-minimum-zoom", lambda: check_3(got.get("run", {}))),
        ("the-zoom-slider-jumps-on-click-and-steps-on-arrow-keys", lambda: check_4(got.get("run", {}))),
        ("zoom-is-pure-view-state", lambda: check_5(got.get("run", {}))),
        ("retraction-of-712-the-slider-was-never-drag-only", lambda: check_6(got.get("run", {}))),
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
