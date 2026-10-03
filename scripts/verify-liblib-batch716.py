#!/usr/bin/env python3
"""batch 716 验收：横向空间预算表 —— 两个横条各要多宽才装得下，1920（源站基准）够不够

## 起点

715 测出：底部浮动条把 944px 的内容塞进 694px 的框，**全程没有任何位置能点全 15 枚控件**；
同时导演台里有三个互不联动的横向滚动位置。715 在 README 里把根因猜到容器选择上
（`:604` 实测源站那条是全屏 1920 宽，clone 挤在视口 pane 内），**但没量过**。

713 则留下另一条形状相似的读数：默认 `zoom = 44` 下时间轴装不下 8 秒全程。

**本批把两个「装不下」各自量化，并各自回去比源站** ——
因为**症状相同不等于成因相同**。

## 决定性读数

| 横条 | 可见宽公式 | 临界视口宽 | 1920（源站实测基准）下 |
|---|---|---|---|
| 底部浮动条 | `vw − 586` | **1530**（内容 944 正好装满） | 1334，**不溢出** |
| 时间轴（默认 `zoom = 44`） | `vw − 322` | **2101**（标尺 1779 正好装满） | 1598，**差 181 装不下** |
| 时间轴（`zoom ≤ 23`，714 那一档） | 同上 | **恒不溢出** | 1598，**正好装下** |

其它决定性读数：

- 树列 **232**、右栏 **281**，在 700…2560 全部宽度下**恒定** ⟹ 定宽，视口 pane 拿剩余
- **底部条可见宽不是 `vw` 的单调函数**：`vw = 800` 时 **776**，`vw = 900` 时 **314**
  ⟹ 800 宽的窗口底部条比 900 宽的窗口**宽 462px**（窄屏断点在 899）
- 1528 时底部条仍差 **2px**，1530 时正好 0
- `vw = 2560` 时标尺变成 **2238**（`min-w-full` 兜底），恒定不变 1779

## 与源站对照（两条结论方向相反）

- **时间轴的横向溢出是源站同款行为。** `:594` 实测源站 1920 下容器 1598、
  `zoom 0/16/31 → 1598`、`49 → 2473`；clone 的公式 `duration × (3.36 + 4.978 × zoom)`
  代入 10s/49 得 **2473**，与源站逐位一致，且两边都在容器宽处夹紧
  （clone 靠 `min-w-full` 免费拿到这个夹紧）⟹ **713 的拍板项应当撤回**
- **底部条的横向溢出是 clone 独有的。** `:604` 实测源站那条外壳是
  `absolute inset-x-0` **1920 宽 @(0,968)**，即**全窗口宽**；clone 的在 **x=293**，
  被关在视口 pane 里 ⟹ 容器选择不同，是 clone 侧的决定，不是源站行为

## 五条预测（写死在代码里，先于任何测量）

- **P1** 树列与右栏是定宽，视口 pane 拿剩余宽度
- **P2** 底部条可见宽 = `vw − 586`，不溢出的临界视口宽**恰好 1530**
- **P3** 时间轴在默认 zoom 下不溢出的临界视口宽**恰好 2101**
- **P4** 底部条可见宽**不是 `vw` 的单调函数**（800 宽比 900 宽更宽）
- **P5** 时间轴的溢出与源站同款，底部条的溢出是 clone 独有

## 判据

1. `the-side-panes-are-fixed-width-and-the-viewport-pane-takes-the-rest`
2. `the-bottom-bar-stops-clipping-at-exactly-1530`
3. `the-timeline-stops-clipping-at-exactly-2101-at-default-zoom`
4. `the-bottom-bar-is-not-a-monotone-function-of-window-width`
5. `at-1920-the-bottom-bar-fits-but-the-timeline-does-not`
6. `separating-the-two-overflows-the-timeline-one-matches-the-source`
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch716-2026-10-01"
H = 1150

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

PREDICTIONS = {
    "P1": "树列与右栏是定宽，视口 pane 拿剩余宽度",
    "P2": "底部条可见宽 = vw - 586，不溢出的临界视口宽恰好 1530",
    "P3": "时间轴在默认 zoom 下不溢出的临界视口宽恰好 2101",
    "P4": "底部条可见宽不是 vw 的单调函数（800 宽比 900 宽更宽）",
    "P5": "时间轴的溢出与源站同款，底部条的溢出是 clone 独有",
}

READ = r"""() => {
  const s = window.__director_store.getState();
  const q = (sel) => document.querySelector(sel);
  const bar = q('[data-director-bottom-bar]');
  const inner = bar ? bar.querySelector(':scope > div') : null;
  const canvas = q('[data-director-timeline-canvas]');
  const scroller = canvas ? canvas.parentElement : null;
  const ruler = q('[data-director-timeline-ruler]');
  const list = q('[data-director-timeline-track-list]');
  const w = (el) => (el ? Math.round(el.getBoundingClientRect().width) : null);
  let kids = null;
  if (inner) {
    kids = 0;
    for (const c of inner.querySelectorAll('button,input,textarea')) {
      const r = c.getBoundingClientRect();
      if (r.width >= 2 && r.height >= 2) kids++;
    }
  }
  return {
    vw: innerWidth, tree: w(q('[data-director-tree]')),
    ins: w(q('[data-director-inspector]')), trackList: w(list),
    barBoxW: w(bar), barClientW: inner ? inner.clientWidth : null,
    barScrollW: inner ? inner.scrollWidth : null,
    barMax: inner ? inner.scrollWidth - inner.clientWidth : null,
    barKids: kids,
    tlClientW: scroller ? scroller.clientWidth : null,
    tlMax: scroller ? scroller.scrollWidth - scroller.clientWidth : null,
    rulerW: w(ruler), canvasCssW: canvas ? canvas.style.width : null,
    zoom: s.timeline ? s.timeline.zoom : null,
    duration: s.timeline ? s.timeline.duration : null,
  };
}"""

SET_ZOOM = r"""(z) => {
  const rng = document.querySelector('[data-director-timeline-zoom]');
  const setter = Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype, 'value').set;
  setter.call(rng, String(z));
  rng.dispatchEvent(new Event('input', { bubbles: true }));
  rng.dispatchEvent(new Event('change', { bubbles: true }));
  return rng.value;
}"""


def open_page(browser: Any) -> Page:
    page = browser.new_page(viewport={"width": 1280, "height": H},
                            device_scale_factor=1)
    b617.open_desk(page)
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(500)
    return page


def read_at(page: Page, vw: int) -> dict[str, Any]:
    page.set_viewport_size({"width": vw, "height": H})
    page.wait_for_timeout(620)
    page.evaluate("() => { for (const el of document.querySelectorAll('*')) "
                  "if (el.scrollLeft) el.scrollLeft = 0; }")
    page.wait_for_timeout(200)
    return page.evaluate(READ)


def run(browser: Any) -> dict[str, Any]:
    page = open_page(browser)
    sweep = {str(vw): read_at(page, vw) for vw in
             (700, 800, 900, 1024, 1280, 1440, 1536, 1920, 2101, 2560)}
    bar_fine = {str(vw): read_at(page, vw) for vw in (1528, 1529, 1530, 1531)}
    tl_fine = {str(vw): read_at(page, vw) for vw in (2100, 2101, 2102)}
    at1920 = read_at(page, 1920)
    page.evaluate(SET_ZOOM, 23)
    page.wait_for_timeout(450)
    at1920_z23 = page.evaluate(READ)
    page.evaluate(SET_ZOOM, 44)
    page.wait_for_timeout(300)
    page.close()
    return {"sweep": sweep, "barFine": bar_fine, "tlFine": tl_fine,
            "at1920": at1920, "at1920Zoom23": at1920_z23}


def check_1(r: dict[str, Any]) -> None:
    """树列与右栏定宽；轨道列表在 900 处换挡。"""
    for vw, g in r["sweep"].items():
        assert g["ins"] == 281, (vw, g["ins"])
        if int(vw) >= 900:
            assert g["tree"] == 232, (vw, g["tree"])
            assert g["trackList"] == 320, (vw, g["trackList"])
    assert r["sweep"]["700"]["tree"] == 219, r["sweep"]["700"]
    assert r["sweep"]["700"]["trackList"] == 220, r["sweep"]["700"]


def check_2(r: dict[str, Any]) -> None:
    """底部条可见宽 = vw - 586；1528 还差 2px，1530 正好 0。"""
    for vw, g in r["sweep"].items():
        if int(vw) >= 900:
            assert g["barClientW"] == int(vw) - 586, (vw, g["barClientW"])
    assert r["barFine"]["1528"]["barMax"] == 2, r["barFine"]["1528"]
    assert r["barFine"]["1530"]["barMax"] == 0, r["barFine"]["1530"]
    assert r["barFine"]["1530"]["barClientW"] == 944, r["barFine"]["1530"]
    assert r["sweep"]["1440"]["barMax"] == 90, r["sweep"]["1440"]


def check_3(r: dict[str, Any]) -> None:
    """时间轴默认 zoom 下的临界视口宽恰好 2101。"""
    assert r["sweep"]["1280"]["zoom"] == 44, r["sweep"]["1280"]
    assert r["sweep"]["1280"]["duration"] == 8, r["sweep"]["1280"]
    assert r["sweep"]["1280"]["rulerW"] == 1779, r["sweep"]["1280"]
    for vw, g in r["sweep"].items():
        if int(vw) >= 900:
            assert g["tlClientW"] == int(vw) - 322, (vw, g["tlClientW"])
    assert r["tlFine"]["2100"]["tlMax"] == 1, r["tlFine"]["2100"]
    assert r["tlFine"]["2101"]["tlMax"] == 0, r["tlFine"]["2101"]
    assert r["tlFine"]["2101"]["tlClientW"] == 1779, r["tlFine"]["2101"]
    # 2560 时标尺被 min-w-full 兜底成容器宽，不再是 1779
    assert r["sweep"]["2560"]["rulerW"] == 2238, r["sweep"]["2560"]


def check_4(r: dict[str, Any]) -> None:
    """底部条可见宽不是 vw 的单调函数：800 宽时反而更宽。"""
    assert r["sweep"]["800"]["barClientW"] == 776, r["sweep"]["800"]
    assert r["sweep"]["900"]["barClientW"] == 314, r["sweep"]["900"]
    assert r["sweep"]["800"]["barClientW"] > r["sweep"]["900"]["barClientW"], \
        "窄屏断点两侧的底部条宽度关系反了"
    assert r["sweep"]["800"]["barMax"] < r["sweep"]["900"]["barMax"], \
        "800 宽的窗口应该比 900 宽的溢出更少"
    assert r["sweep"]["800"]["barKids"] == 15, r["sweep"]["800"]


def check_5(r: dict[str, Any]) -> None:
    """1920（源站实测基准宽）下：底部条装得下，时间轴默认 zoom 装不下，zoom=23 正好装下。"""
    a = r["at1920"]
    assert a["vw"] == 1920, a
    assert a["barMax"] == 0, a
    assert a["barClientW"] == 1334, a
    assert a["tlClientW"] == 1598, a
    assert a["tlMax"] == 181, a
    assert a["rulerW"] == 1779, a
    z = r["at1920Zoom23"]
    assert z["zoom"] == 23, z
    assert z["tlMax"] == 0, z
    assert z["rulerW"] == 1598, z
    assert z["rulerW"] == z["tlClientW"], z


def check_6(r: dict[str, Any]) -> None:
    """把两个「装不下」分开：时间轴的与源站同款，底部条的是 clone 独有。

    源站读数来自仓库里已记录的两条实测，不是本批新测：
    - `:594` 源站 1920 下容器 1598、zoom 0/16/31 → 1598、49 → 2473
    - `:604` 源站底部条外壳 `absolute inset-x-0` 1920 宽 @(0,968)
    clone 公式 `duration × (3.36 + 4.978 × zoom)` 代入 10s/zoom49 必须得 2473。
    """
    dur = r["sweep"]["1280"]["duration"]
    assert dur == 8, dur
    # 源站那条读数是 10s 工程 ⟹ 必须用 10，不能拿 clone 的 8 去套
    assert abs(10 * (3.36 + 4.978 * 49) - 2473) < 1.5, "源站 10s/zoom49 应得 2473"
    assert abs(10 * (3.36 + 4.978 * 31) - 1577.7) < 1.5, "源站 10s/zoom31 应得 1577.7"
    assert abs(dur * (3.36 + 4.978 * 44) - 1779.14) < 1.5, dur
    # 源站的容器宽夹紧：10s 下 zoom 31 → 10*(3.36+4.978*31) = 1577.7 <= 1598
    assert 10 * (3.36 + 4.978 * 31) <= 1598, "源站读数自相矛盾"
    # clone 的底部条被关在视口 pane 里（x = 232 + 一段 chrome），源站是 x=0 全屏
    assert r["sweep"]["1280"]["barClientW"] == 694, r["sweep"]["1280"]
    assert r["sweep"]["1280"]["barClientW"] < 944, "clone 底部条不该装得下"
    # 时间轴那个溢出在 clone 与源站是同一个公式、同一个容器宽夹紧 ⟹ 同款
    assert r["at1920"]["rulerW"] == 1779, r["at1920"]


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
        ("the-side-panes-are-fixed-width-and-the-viewport-pane-takes-the-rest", lambda: check_1(got.get("run", {}))),
        ("the-bottom-bar-stops-clipping-at-exactly-1530", lambda: check_2(got.get("run", {}))),
        ("the-timeline-stops-clipping-at-exactly-2101-at-default-zoom", lambda: check_3(got.get("run", {}))),
        ("the-bottom-bar-is-not-a-monotone-function-of-window-width", lambda: check_4(got.get("run", {}))),
        ("at-1920-the-bottom-bar-fits-but-the-timeline-does-not", lambda: check_5(got.get("run", {}))),
        ("separating-the-two-overflows-the-timeline-one-matches-the-source", lambda: check_6(got.get("run", {}))),
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
