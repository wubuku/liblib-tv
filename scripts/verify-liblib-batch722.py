#!/usr/bin/env python3
"""batch 722 验收：底部浮动条的两种修法各自要付多少 —— 把 715/716 的定性变成账

## 起点

715 测出底部浮动条可见 694（1280）/ 438（1024），内容恒为 944，控件 15 枚，
**跨全程扫 5 个滚动位置后任何位置都点不全**（1280 最好 13/15）。
716 补上根因的两半：`:604` 实测源站那条外壳是 `absolute inset-x-0` **1920 全屏宽**，
而 clone 的在视口 pane 内；源码注释（`DirectorViewport.tsx:3407`）自陈
「clone 的控件集更大，故去掉定宽让内容撑开」。

**两半根因各自要修多少，720/721 都没算过。** 本批只做这一件事：
把「提容器到窗级」与「收控件集」各自的账算平，让拍板项从三选一变成带价的菜单。

## 决定性读数（1280×1150）

### 壳与内容

| 读数 | 值 |
|---|---|
| 底部条外壳 | **718** @(281,920)，`px-3` ⟹ 左右内边距合计 **24** |
| 横向滚动框 | **694**（`clientWidth` 694 / `scrollWidth` **944**） |
| 内容行 | **944** = 工具胶囊 **711** + gap **8** + prompt 胶囊 **225** |
| 溢出 | **250** |

### 两枚胶囊里只有一枚不一样

| 胶囊 | clone 实测 | `:604` 记录的源站 | 差 |
|---|---|---|---|
| 工具胶囊 `[data-director-viewport-toolbar]` | **711×48** | **360×48** @(780,968) | **+351** |
| prompt 胶囊 `[data-director-scene-prompt-bar]` | **225×48** | **225×48** | **0（逐像素相同）** |

⟹ **overflow 的账不该记在 prompt 头上** —— 它与源站一致。
604 列的 clone-only 清单（变换上下文条 / 变换三档 / 画幅比三枚 / 九宫格 /
虚拟相机 / 群众阵列 / 模型库 / 保存构图）全部落在那 351 里。

### 工具胶囊逐组定价（12 个直接子元素）

| # | 元素 | 宽 | 源站有吗 |
|---|---|---|---|
| 0 | 变换上下文条 `transform-context` | 98 | 无 |
| 1 | 移动 / 旋转 / 缩放 | 112 | 源站只有「移动」 |
| 2 | 动画时间轴 `timeline-toggle` | 32 | **有** |
| 3 | 分隔符 | 1 | — |
| 4 | 画幅比例 16:9 / 9:16 / 1:1 | 136 | 无（源站在左侧 rail） |
| 5 | 开启九宫格辅助线 | 32 | 无 |
| 6 | 分隔符 | 1 | — |
| 7 | 虚拟相机 `phone-vcam-trigger` | 32 | 无 |
| 8 | 添加群众阵列 `crowd-trigger` | 32 | 无 |
| 9 | 模型库 `model-library-trigger` | 32 | 无 |
| 10 | 分隔符 | 1 | — |
| 11 | 保存构图 `capture` | 84 | 无 |

**clone-only 控件内容合计 558 = 工具胶囊 711 的 78%**；
源站有的只有「动画时间轴」那 32 与三个 1px 分隔符。

### 修法 A：提容器到窗级

| 视口宽 | 可用（`vw − 24`） | 内容 944 | 结果 |
|---|---|---|---|
| **1280** | **1256** | 944 | **装得下，余 312** |
| **1024** | **1000** | 944 | **装得下，余 56** |
| **临界** | — | — | **vw ≥ 968** |
| 900 | 876 | 944 | 差 68 |
| 800 | 776 | 944 | 差 168 |

⟹ **一处容器改动、不牺牲任何控件，`vw ≥ 968` 全程装得下。**
但 **900 / 800 仍在窄屏侧装不下** —— 716 实测 `vw < 899` 时底部条**本来就落在窗级**，
所以修法 A 在窄屏侧等于没修。

### 修法 B：收控件集（容器保持在 pane 级 694）

需从 944 砍掉 **≥ 250**（**26.5%**）。按实测宽度给 clone-only 那 8 组定价：

| 组 | 实测宽 |
|---|---|
| 变换三档（移动/旋转/缩放） | 112 |
| 画幅比例 16:9 / 9:16 / 1:1 | 136 |
| 变换上下文条 | 98 |
| 保存构图 | 84 |
| 九宫格 / 虚拟相机 / 群众阵列 / 模型库 | 各 32 |

- **单组最大 136 ≪ 250** ⟹ 一组永远不够；
- **最大的两组 112 + 136 = 248，差 2px** ⟹ **两组也不够**；
- **三组可行**：画幅比 136 + 保存构图 84 + 任意一枚 32 = **252**（余 2）。

⟹ **「收控件集」至少要动 3 组 clone-only 控件**（7 枚按钮），每一刀都在削功能；
修法 A 一样都不削。

### 窄屏侧的切换点（实测，不是推断）

| vw | 底部条 `x` | 层级 |
|---|---|---|
| 900 / 899 | **281** | pane 级（**与 1280 同侧**） |
| 800 / 700 | **0** | 窗级 |

⟹ 716 记的「`vw = 800` 时底部条 776 宽」确实是窗级，但**切换点不在 899**；
899 与 900 同侧。窄屏侧本来就在窗级，所以**修法 A 在那里等于没修**
（800 仍差 **168**）。

## 不声称

- **不声称源站那条在窄屏下也不溢出** —— `:604` 的读数是 1920 基准宽下的。
- **不声称「clone-only」就是「该删的」** —— 604 明写它们是**刻意保留**的，
  `data-director-capture` 还有 12 个 verifier 依赖。本批只定价，不建议删。
- **不声称修法 A 一定可行** —— 提容器到窗级会不会盖住别的 pane，未取证。

## 方法论

1. **定性的根因要拆成两笔账分别算** —— 716 说根因是「clone 侧两个决定叠加」，
   但没算各自值多少。**分开算之后结论完全不对称**：一处改动 312 余量 vs 三组削功能。
2. **「控件集更大」要落到具体宽度** —— 源码注释里那句自陈没有数字，
   558/711 才是能拿去拍板的数字。
3. **对账要平，残差要归因** —— 逐组相加差 14（margin 12 + border 2），
   第一版只算了 margin、差 2 没交代；**残差不为 0 就一定要指出是哪一项**。
4. **「至少要动几个」要用最大组合验证，不能顺手加一个同类项** ——
   第一版把「模型库」当成比「虚拟相机」宽，算出 264 就说四枚够用，
   实际两者都是 32，正确答案是 **248 差 2px、至少三组**。
5. **断点位置要实测** —— 716 记的「899 断点」在底部条这一层并不成立，
   899 与 900 同侧；**上一批的断点结论不能直接套到另一个元素上**。
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch722-2026-10-01"

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

# :604 记录的源站读数（源站导演台当前关着，这两条是仓库里既有的实测）
SOURCE_604 = {"toolbarW": 360, "promptW": 225, "barW": 1920,
              "toolbarX": 780, "barY": 968}

BAR_JS = r"""() => {
  const bar = document.querySelector('[data-director-bottom-bar]');
  if (!bar) return null;
  const r = bar.getBoundingClientRect();
  const cs = getComputedStyle(bar);
  const scroller = [...bar.querySelectorAll('*')].find((el) => {
    const s = getComputedStyle(el);
    return /auto|scroll/.test(s.overflowX);
  });
  if (!scroller) return null;
  const sr = scroller.getBoundingClientRect();
  const row = scroller.firstElementChild;
  const rr = row.getBoundingClientRect();
  return {
    vw: window.innerWidth,
    bar: {x: Math.round(r.x), y: Math.round(r.y),
          w: Math.round(r.width), h: Math.round(r.height)},
    padTotal: parseFloat(cs.paddingLeft) + parseFloat(cs.paddingRight),
    scroller: {x: Math.round(sr.x), w: Math.round(sr.width)},
    clientWidth: scroller.clientWidth,
    scrollWidth: scroller.scrollWidth,
    row: {x: Math.round(rr.x), w: Math.round(rr.width), h: Math.round(rr.height)},
    hasTinyScrollbar: /tiny-scrollbar/.test(scroller.className),
  };
}"""

TB_JS = r"""() => {
  const tb = document.querySelector('[data-director-viewport-toolbar]');
  const p = document.querySelector('[data-director-scene-prompt-bar]');
  if (!tb || !p) return null;
  const cs = getComputedStyle(tb);
  const gap = parseFloat(cs.columnGap) || 0;
  const border = parseFloat(cs.borderLeftWidth) + parseFloat(cs.borderRightWidth);
  const tbr = tb.getBoundingClientRect();
  const pr = p.getBoundingClientRect();
  const kids = [...tb.children].map((el, i) => {
    const kr = el.getBoundingClientRect();
    const ks = getComputedStyle(el);
    const ds = {};
    for (const a of el.attributes) {
      if (a.name.startsWith('data-')) {
        ds[a.name.replace('data-director-', '')] = a.value.slice(0, 40);
      }
    }
    const btns = [...el.querySelectorAll('button')].map((b) => ({
      label: b.getAttribute('aria-label')
        || (b.textContent || '').trim().slice(0, 16),
      w: Math.round(b.getBoundingClientRect().width),
      h: Math.round(b.getBoundingClientRect().height)}));
    return {"i": i, "ariaLabel": el.getAttribute('aria-label'), "data": ds,
            "w": Math.round(kr.width),
            "ml": parseFloat(ks.marginLeft), "mr": parseFloat(ks.marginRight),
            "btns": btns}
  });
  return {
    toolbar: {w: Math.round(tbr.width), h: Math.round(tbr.height)},
    prompt: {w: Math.round(pr.width), h: Math.round(pr.height)},
    gap: gap, padL: parseFloat(cs.paddingLeft), padR: parseFloat(cs.paddingRight),
    border: border, kids: kids,
  };
}"""


def bar_reading(page: Page) -> dict[str, Any]:
    g = page.evaluate(BAR_JS)
    assert g, "找不到 [data-director-bottom-bar]"
    return g


def strip(page: Page) -> None:
    page.evaluate("() => { for (const el of document.querySelectorAll"
                  "('nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(400)


def run(browser: Any) -> dict[str, Any]:
    page = browser.new_page(viewport={"width": 1280, "height": 1150},
                            device_scale_factor=1)
    r: dict[str, Any] = {"source604": SOURCE_604}
    b617.open_desk(page)
    strip(page)

    b = bar_reading(page)
    t = page.evaluate(TB_JS)
    assert t, "找不到工具胶囊或 prompt 胶囊"
    r["bar1280"] = b
    r["toolbar"] = t

    # 对账：子元素 + gap + padding + border + margin 是否等于容器宽
    kids = t["kids"]
    sum_w = sum(k["w"] for k in kids)
    sum_m = sum(k["ml"] + k["mr"] for k in kids)
    gaps = t["gap"] * max(0, len(kids) - 1)
    r["reconcile"] = {
        "n": len(kids), "sumKids": sum_w, "gaps": gaps,
        "padL": t["padL"], "padR": t["padR"], "border": t["border"],
        "margins": sum_m,
        "accounted": sum_w + gaps + t["padL"] + t["padR"] + t["border"] + sum_m,
        "toolbarW": t["toolbar"]["w"],
        "residual": t["toolbar"]["w"]
        - (sum_w + gaps + t["padL"] + t["padR"] + t["border"] + sum_m),
    }

    # 视口扫描：宽侧、临界、899 断点两侧、窄屏侧
    scan: list[dict[str, Any]] = []
    for vw in (1280, 1024, 968, 900, 899, 880, 860, 840, 820, 800, 700):
        page.set_viewport_size({"width": vw, "height": 1150})
        page.wait_for_timeout(900)
        strip(page)
        g = bar_reading(page)
        would_be = g["vw"] - g["padTotal"]
        scan.append({
            "vw": g["vw"], "barW": g["bar"]["w"], "barX": g["bar"]["x"],
            "padTotal": g["padTotal"], "clientWidth": g["clientWidth"],
            "scrollWidth": g["scrollWidth"], "contentW": g["row"]["w"],
            "windowLevelW": would_be,
            "fitsNow": g["clientWidth"] >= g["row"]["w"],
            "fitsIfWindowLevel": would_be >= g["row"]["w"],
            "slackIfWindowLevel": would_be - g["row"]["w"],
        })
    r["scan"] = scan
    page.close()
    return r


def check_1(r: dict[str, Any]) -> None:
    """内容行 944 = 工具胶囊 711 + gap 8 + prompt 225；scroller 694 ⟹ 溢出 250。"""
    b, t = r["bar1280"], r["toolbar"]
    assert t["toolbar"]["w"] == 711, t["toolbar"]
    assert t["prompt"]["w"] == 225, t["prompt"]
    assert t["gap"] == 8, t["gap"]
    assert b["row"]["w"] == 944, b["row"]
    assert b["row"]["w"] == t["toolbar"]["w"] + t["gap"] + t["prompt"]["w"], b
    assert b["clientWidth"] == 694 and b["scrollWidth"] == 944, b
    assert b["scrollWidth"] - b["clientWidth"] == 250, b
    assert b["bar"]["w"] == 718 and b["padTotal"] == 24, b


def check_2(r: dict[str, Any]) -> None:
    """两枚胶囊里只有工具胶囊不一样：+351 对 0。"""
    s = r["source604"]
    assert r["toolbar"]["toolbar"]["w"] - s["toolbarW"] == 351, r["toolbar"]
    assert r["toolbar"]["prompt"]["w"] == s["promptW"], (r["toolbar"], s)
    assert r["bar1280"]["bar"]["w"] == 718 and s["barW"] == 1920, (
        r["bar1280"]["bar"], s)
    assert r["bar1280"]["bar"]["x"] == 281, r["bar1280"]["bar"]


def check_3(r: dict[str, Any]) -> None:
    """工具胶囊 12 个直接子元素逐组对账，残差必须为 0（border 与 margin 都算进去）。"""
    rc = r["reconcile"]
    assert rc["n"] == 12, rc["n"]
    assert rc["sumKids"] == 593, rc
    assert rc["gaps"] == 88, rc
    assert rc["padL"] == 8 and rc["padR"] == 8, rc
    assert rc["border"] == 2, rc
    assert rc["margins"] == 12, rc
    assert rc["accounted"] == 711, rc
    assert rc["residual"] == 0, rc
    widths = [k["w"] for k in r["toolbar"]["kids"]]
    assert widths == [98, 112, 32, 1, 136, 32, 1, 32, 32, 32, 1, 84], widths


def check_4(r: dict[str, Any]) -> None:
    """clone-only 控件内容合计 558 = 工具胶囊 711 的 78%；源站有的只有动画时间轴那 32。"""
    kids = r["toolbar"]["kids"]
    clone_only_idx = (0, 1, 4, 5, 7, 8, 9, 11)
    clone_only = sum(kids[i]["w"] for i in clone_only_idx)
    assert clone_only == 558, clone_only
    assert round(100.0 * clone_only / 711) == 78, (clone_only, 711)
    assert kids[2]["data"].get("timeline-toggle") == "true", kids[2]
    assert kids[2]["w"] == 32, kids[2]
    assert [kids[i]["w"] for i in (3, 6, 10)] == [1, 1, 1], kids


def check_5(r: dict[str, Any]) -> None:
    """修法 A：宽侧临界 vw = 968（content 944 + padding 24）；1280 余 312、1024 余 56。

    **内容宽不是常数** —— 窄屏侧变换上下文条截断、prompt 胶囊收窄，
    700 下只有 885。所以临界是逐 vw 量的，不是拿 944 一把套。
    """
    by = {s["vw"]: s for s in r["scan"]}
    assert by[1280]["contentW"] == 944, by[1280]
    assert by[1024]["contentW"] == 944, by[1024]
    assert by[968]["contentW"] == 944, by[968]
    assert by[1280]["fitsIfWindowLevel"] is True, by[1280]
    assert by[1280]["slackIfWindowLevel"] == 312, by[1280]
    assert by[1024]["fitsIfWindowLevel"] is True, by[1024]
    assert by[1024]["slackIfWindowLevel"] == 56, by[1024]
    assert by[968]["fitsIfWindowLevel"] is True, by[968]
    assert by[968]["slackIfWindowLevel"] == 0, by[968]
    assert 944 + 24 == 968
    assert by[700]["contentW"] == 885, by[700]
    for s in r["scan"]:
        assert s["windowLevelW"] == s["vw"] - s["padTotal"], s
        assert s["fitsIfWindowLevel"] == (
            s["windowLevelW"] >= s["contentW"]), s
    # 宽侧（内容恒为 944）的临界恰好 968
    for vw in (1280, 1024, 968, 900):
        assert by[vw]["fitsIfWindowLevel"] == (vw >= 968), by[vw]


def check_6(r: dict[str, Any]) -> None:
    """修法 B：容器留在 pane 级要砍 ≥250；最大的两组 clone-only 合计 248，差 2px。"""
    by = {s["vw"]: s for s in r["scan"]}
    need = 944 - by[1280]["clientWidth"]
    assert need == 250, need
    assert round(100.0 * need / 944) == 26, need  # 26.48%
    k = r["toolbar"]["kids"]
    ctx, tf, aspect, capture = k[0]["w"], k[1]["w"], k[4]["w"], k[11]["w"]
    grid, vcam, crowd, lib = k[5]["w"], k[7]["w"], k[8]["w"], k[9]["w"]
    assert (ctx, tf, aspect, capture) == (98, 112, 136, 84), (
        ctx, tf, aspect, capture)
    assert (grid, vcam, crowd, lib) == (32, 32, 32, 32), (grid, vcam, crowd, lib)
    # 单组最大 136，一组永远不够
    assert max(ctx, tf, aspect, capture, grid) == 136 < need, need
    # 最大的两组：变换三档 112 + 画幅比 136 = 248，差 2px —— 两组不够
    assert (112 + 136) == 248 < need, (248, need)
    # 三组可行：画幅比 136 + 保存构图 84 + 任意一枚 32 = 252
    assert (aspect + capture + grid) == 252 and 252 >= need, 252


def check_7(r: dict[str, Any]) -> None:
    """窄屏侧底部条才落到窗级，切换点实测在 899 与 800 之间；那里修法 A 也不够用。"""
    by = {s["vw"]: s for s in r["scan"]}
    # 899 与 900 同侧（还在 pane 级），900..800 之间才切到窗级
    assert by[900]["barX"] == by[899]["barX"] != 0, (by[900], by[899])
    assert by[800]["barX"] == 0, by[800]
    pane = [s["vw"] for s in r["scan"] if s["barX"] != 0]
    win = [s["vw"] for s in r["scan"] if s["barX"] == 0]
    assert min(pane) > max(win), (min(pane), max(win))
    r["narrowBoundary"] = {"paneLevel": sorted(pane), "windowLevel": sorted(win)}
    # 窄屏侧本来就在窗级，可修法 A 依然装不下
    for vw in win:
        assert by[vw]["fitsIfWindowLevel"] is False, by[vw]
    assert by[800]["slackIfWindowLevel"] == -168, by[800]
    assert by[900]["slackIfWindowLevel"] == -68, by[900]


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    got: dict[str, Any] = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            got["run"] = run(browser)
        except Exception as exc:  # noqa: BLE001
            failures.append("run: %s" % exc)
            got["run"] = {}
        browser.close()
    results: dict[str, Any] = {"source604": SOURCE_604}
    checks = [
        ("content-944-splits-into-toolbar-711-plus-prompt-225-over-a-694-box",
         lambda: check_1(got.get("run", {}))),
        ("only-the-tool-capsule-differs-from-source-351-wider-while-prompt-matches",
         lambda: check_2(got.get("run", {}))),
        ("the-tool-capsule-twelve-children-reconcile-to-its-own-width",
         lambda: check_3(got.get("run", {}))),
        ("clone-only-controls-account-for-558-of-711",
         lambda: check_4(got.get("run", {}))),
        ("lifting-the-container-to-window-level-fits-at-every-vw-from-968-up",
         lambda: check_5(got.get("run", {}))),
        ("keeping-the-container-needs-at-least-250-cut-achieved-by-four-controls",
         lambda: check_6(got.get("run", {}))),
        ("the-narrow-side-is-already-window-level-so-option-a-does-not-cover-it",
         lambda: check_7(got.get("run", {}))),
    ]
    summary: dict[str, bool] = {}
    for name, fn in checks:
        try:
            fn()
            summary[name] = True
        except Exception as exc:  # noqa: BLE001
            summary[name] = False
            failures.append("%s: %s" % (name, exc))
    results.update(got)
    results["summary"] = summary
    results["failures"] = failures
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1, default=str),
        encoding="utf-8")
    for name, ok in summary.items():
        print(("PASS " if ok else "FAIL ") + name)
    for f in failures:
        print("  ->", f[:400])
    print("\n%d/%d 通过" % (sum(1 for v in summary.values() if v), len(summary)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
