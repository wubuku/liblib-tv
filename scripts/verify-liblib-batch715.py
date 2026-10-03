#!/usr/bin/env python3
"""batch 714 的延伸：导演台里的横向滚动容器普查 + 底部条的可达性

## 起点

713 测出时间轴默认缩放装不下 8 秒全程（标尺 1779px / 可见 958px），只能横向滚动。
714 测出 zoom 划块低端 24 档是空行程、且划块能点能用键盘。
两批都只谈**时间轴那一个**滚动容器。本批问一个更基础的问题：
**整个导演台到底有几个横向滚动容器？它们联动吗？各自装得下自己的内容吗？**

## 决定性读数（视口 1280×1150）

| 读数 | 值 |
|---|---|
| 横向滚动容器（`overflow-x: auto/scroll`） | 1280 下 **2 个**真能滚，1024 下 **3 个** |
| 时间轴轨道容器 | 958 / 1779（`max 821`） |
| **底部浮动条** | 可见 **694** / 内容 **944**（`max 250`） |
| 工具条（`timeline-controls-scroll`） | 1280 下不溢出；1024 下溢出 **20px**（裁掉「删除关键帧」） |
| **三个容器之间的联动** | **零** —— 任何一个滚到底，别的 `scrollLeft` 一个都不动 |
| 真实滚轮 | 三个容器**全部**有效（底部条在 5 个采样点上都到 250） |
| 底部条控件总数 | **15 枚**（可见框只有 694px，内容 944px） |
| `scrollLeft = 0` 时死掉的控件 | **上传图片 / 描述想搭建的场景 / 发送**（出框 + 命中测试打不到） |
| `scrollLeft = 250` 时死掉的控件 | **移动 / 旋转 / 缩放**（被推到左边、出框 + 打不到） |
| 带 `tiny-scrollbar` 的容器 | **只有时间轴那一个** |

**⟹ 底部条不存在「全部可见」的滚动位置**：944 > 694，两个极端各死 3 枚。
**⟹ 没有可见的滚动条提示**：三个容器里只有时间轴那一个写了滚动条样式。

## 五条预测（写死在代码里，先于任何测量）

- **P1** 导演台里有 ≥2 个横向滚动容器（时间轴不是唯一的一个）
- **P2** 它们**互不联动**（各自独立，界面不共享滚动位置指示）
- **P3** 底部条的内容比它的可见框宽，默认就有控件在框外
- **P4** 框外的控件**默认打不到**，但滚过去之后能打到（不是永久不可达）
- **P5** 滚动只是**把死掉的控件从一头换到另一头**，不存在「全都活着」的位置

## 判据

1. `the-bottom-bar-never-shows-all-of-its-controls`
2. `the-wheel-scrolls-the-bottom-bar-everywhere`
3. `scrolling-the-bottom-bar-trades-one-set-of-dead-controls-for-another`
4. `the-desk-has-two-independent-horizontal-scrollers-at-1280`
5. `a-third-scroller-appears-at-1024-and-nothing-cross-links`
6. `only-the-timeline-scroller-has-a-styled-scrollbar`
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch715-2026-10-01"
W, DESK_H = 1280, 1150

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

PREDICTIONS = {
    "P1": "导演台里有 >=2 个横向滚动容器（时间轴不是唯一的一个）",
    "P2": "它们互不联动（各自独立，界面不共享滚动位置指示）",
    "P3": "底部条的内容比它的可见框宽，默认就有控件在框外",
    "P4": "框外的控件默认打不到，但滚过去之后能打到（不是永久不可达）",
    "P5": "滚动只是把死掉的控件从一头换到另一头，不存在「全都活着」的位置",
}

# 所有操作按**稳定名字**定位（取最近的 data-* 属性），绝不用索引：
# 跨状态索引不稳定会让「谁带动了谁」这种因果读数彻底作废。
SCROLLERS = r"""() => {
  const desk = document.querySelector('[data-director-workspace]');
  const out = [];
  let auto = 0;
  for (const el of desk.querySelectorAll('*')) {
    const cs = getComputedStyle(el);
    if (cs.overflowX !== 'auto' && cs.overflowX !== 'scroll') continue;
    const r = el.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) continue;
    let key = null;
    let n = el;
    for (let d = 0; d < 4 && n; d++) {
      const a = [...n.attributes].find((x) => x.name.startsWith('data-')
        && !x.name.startsWith('data-react'));
      if (a) { key = a.name + '=' + a.value; break; }
      n = n.parentElement;
    }
    if (!key) key = 'auto#' + (auto++);
    out.push({ key, clientW: el.clientWidth, scrollW: el.scrollWidth,
      left: el.scrollLeft, max: el.scrollWidth - el.clientWidth,
      x: Math.round(r.x), y: Math.round(r.y),
      w: Math.round(r.width), h: Math.round(r.height),
      hasTinyScrollbar: el.className.includes('tiny-scrollbar') });
  }
  return out;
}"""

ACT = r"""(arg) => {
  const desk = document.querySelector('[data-director-workspace]');
  let auto = 0;
  const find = () => {
    const all = [];
    for (const el of desk.querySelectorAll('*')) {
      const cs = getComputedStyle(el);
      if (cs.overflowX !== 'auto' && cs.overflowX !== 'scroll') continue;
      const r = el.getBoundingClientRect();
      if (r.width < 4 || r.height < 4) continue;
      let key = null; let n = el;
      for (let d = 0; d < 4 && n; d++) {
        const a = [...n.attributes].find((x) => x.name.startsWith('data-')
          && !x.name.startsWith('data-react'));
        if (a) { key = a.name + '=' + a.value; break; }
        n = n.parentElement;
      }
      if (!key) key = 'auto#' + (auto++);
      all.push({ key, el });
    }
    return all;
  };
  const all = find();
  if (arg.op === 'reset') {
    let n = 0;
    for (const { el } of all) if (el.scrollLeft !== 0) { el.scrollLeft = 0; n++; }
    return n;
  }
  const hit = all.find((x) => x.key === arg.key);
  if (!hit) return { error: 'not found: ' + arg.key };
  if (arg.op === 'drive') { hit.el.scrollLeft = hit.el.scrollWidth;
    return { after: hit.el.scrollLeft }; }
  if (arg.op === 'rect') { hit.el.scrollLeft = 0;
    const r = hit.el.getBoundingClientRect();
    return { x: Math.round(r.x), y: Math.round(r.y),
             w: Math.round(r.width), h: Math.round(r.height) }; }
  return null;
}"""

BAR_KIDS = r"""(scrollTo) => {
  const bar = document.querySelector('[data-director-bottom-bar]');
  const el = bar.querySelector(':scope > div');
  el.scrollLeft = scrollTo;
  const box = el.getBoundingClientRect();
  const out = [];
  for (const c of el.querySelectorAll('button,input,textarea')) {
    const r = c.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    const inVP = cx >= 0 && cx <= innerWidth && cy >= 0 && cy <= innerHeight;
    const h = inVP ? document.elementFromPoint(cx, cy) : null;
    out.push({ label: (c.getAttribute('aria-label') || c.getAttribute('placeholder')
        || c.getAttribute('title') || (c.textContent || '').trim().slice(0, 14)),
      x: Math.round(r.x), right: Math.round(r.right),
      inBox: r.x >= box.x - 0.5 && r.right <= box.right + 0.5,
      hitSelf: h === c || (h ? c.contains(h) : false) });
  }
  return { scrollLeft: el.scrollLeft, clientW: el.clientWidth,
    scrollW: el.scrollWidth, boxX: Math.round(box.x),
    boxRight: Math.round(box.right), kids: out };
}"""

TOOLBAR_KIDS = r"""() => {
  const el = document.querySelector('[data-director-timeline-controls-scroll]');
  const box = el.getBoundingClientRect();
  const out = [];
  for (const c of el.querySelectorAll('button,input,select')) {
    const r = c.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    if (r.x >= box.x - 0.5 && r.right <= box.right + 0.5) continue;
    out.push({ label: (c.getAttribute('aria-label') || c.getAttribute('title')
        || (c.textContent || '').trim().slice(0, 14)),
      x: Math.round(r.x), right: Math.round(r.right) });
  }
  return { clientW: el.clientWidth, scrollW: el.scrollWidth,
    boxRight: Math.round(box.right), clipped: out };
}"""

# 只读，不改 scrollLeft（早期版本误用 BAR_KIDS 读值，会把滚动位置先归零）
READ_BAR_LEFT = r"""() => {
  const bar = document.querySelector('[data-director-bottom-bar]');
  return bar.querySelector(':scope > div').scrollLeft;
}"""


def fresh(browser: Any, w: int = W) -> Page:
    page = browser.new_page(viewport={"width": w, "height": DESK_H},
                            device_scale_factor=1)
    b617.open_desk(page)
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(400)
    return page


def dead(kids: list[dict[str, Any]]) -> list[str]:
    return sorted(k["label"] for k in kids if not k["hitSelf"])


def probe_vw(browser: Any, vw: int) -> dict[str, Any]:
    page = fresh(browser, vw)
    page.evaluate(ACT, {"op": "reset"})
    page.wait_for_timeout(250)
    scrollers = page.evaluate(SCROLLERS)
    scrollable = [s for s in scrollers if s["max"] > 1]

    links = []
    for s in scrollable:
        page.evaluate(ACT, {"op": "reset"})
        page.wait_for_timeout(280)
        base = {x["key"]: x["left"] for x in page.evaluate(SCROLLERS)}
        drv = page.evaluate(ACT, {"op": "drive", "key": s["key"]})
        page.wait_for_timeout(340)
        after = page.evaluate(SCROLLERS)
        moved = [{"key": a["key"], "from": base[a["key"]], "to": a["left"]}
                 for a in after if a["key"] != s["key"] and a["left"] != base[a["key"]]]

        page.evaluate(ACT, {"op": "reset"})
        page.wait_for_timeout(240)
        r = page.evaluate(ACT, {"op": "rect", "key": s["key"]})
        page.mouse.move(r["x"] + r["w"] / 2, r["y"] + r["h"] / 2)
        page.wait_for_timeout(160)
        page.mouse.wheel(2000, 0)
        page.wait_for_timeout(520)
        post = {x["key"]: x["left"] for x in page.evaluate(SCROLLERS)}
        links.append({"key": s["key"], "max": s["max"], "drove": drv,
                      "moved": moved, "wheelTo": post[s["key"]]})

    # 底部条：滚轮逐点（5 个横向采样）
    bar0 = page.evaluate(BAR_KIDS, 0)
    rect = page.evaluate(ACT, {"op": "rect", "key": "data-director-bottom-bar=true"})
    wheel_points = []
    for f in (0.05, 0.25, 0.45, 0.65, 0.85):
        page.evaluate(ACT, {"op": "reset"})
        page.wait_for_timeout(220)
        x = rect["x"] + rect["w"] * f
        page.mouse.move(x, rect["y"] + rect["h"] / 2)
        page.wait_for_timeout(160)
        page.mouse.wheel(1200, 0)
        page.wait_for_timeout(500)
        wheel_points.append({"f": f, "x": int(x),
                             "to": page.evaluate(READ_BAR_LEFT)})

    page.evaluate(ACT, {"op": "reset"})
    page.wait_for_timeout(220)
    at0 = page.evaluate(BAR_KIDS, 0)
    atMax = page.evaluate(BAR_KIDS, at0["scrollW"])

    # 跨全程扫 5 个滚动位置：把「不存在全都可见的位置」从算术推断变成实测。
    # 注意：某枚控件「两端都死」≠「哪都死」（它可能只在中间活），
    # 所以必须扫全程，不能只看两个极端。
    span = at0["scrollW"] - at0["clientW"]
    sweep = []
    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        page.evaluate("(v) => { const b = document.querySelector"
                      "('[data-director-bottom-bar]');"
                      "b.querySelector(':scope > div').scrollLeft = v; }", span * frac)
        page.wait_for_timeout(300)
        s = page.evaluate(BAR_KIDS, span * frac)
        sweep.append({"frac": frac, "scrollLeft": s["scrollLeft"],
                      "dead": dead(s["kids"]), "deadCount": len(dead(s["kids"]))})

    toolbar = page.evaluate(TOOLBAR_KIDS)
    page.close()
    return {"scrollers": scrollers, "scrollable": [s["key"] for s in scrollable],
            "links": links, "bar0": at0, "barMax": atMax,
            "deadAt0": dead(at0["kids"]), "deadAtMax": dead(atMax["kids"]),
            "sweep": sweep,
            "toolbar": toolbar, "wheelPoints": wheel_points,
            "tinyScrollbarKeys": [s["key"] for s in scrollers
                                  if s.get("hasTinyScrollbar")]}


def run(browser: Any) -> dict[str, Any]:
    return {"v1280": probe_vw(browser, 1280), "v1024": probe_vw(browser, 1024)}


def check_1(r: dict[str, Any]) -> None:
    """底部条不存在「全部可见」的滚动位置（跨全程实测，不只看两端）。"""
    for vw in ("v1280", "v1024"):
        a = r[vw]["bar0"]
        assert a["scrollW"] > a["clientW"], (vw, a["scrollW"], a["clientW"])
        assert len(a["kids"]) == 15, (vw, len(a["kids"]))
        sweep = r[vw]["sweep"]
        assert len(sweep) == 5, (vw, sweep)
        assert all(s["deadCount"] > 0 for s in sweep), \
            (vw, [(s["frac"], s["dead"]) for s in sweep])
        # 1024 下两端各有 8/9 枚死控件（框只有 438px）
        assert len(r[vw]["deadAt0"]) >= 3, (vw, r[vw]["deadAt0"])
        assert len(r[vw]["deadAtMax"]) >= 3, (vw, r[vw]["deadAtMax"])
    # 1280 下两个极端的死亡集合完全不相交、各 3 枚
    assert len(r["v1280"]["deadAt0"]) == 3, r["v1280"]["deadAt0"]
    assert len(r["v1280"]["deadAtMax"]) == 3, r["v1280"]["deadAtMax"]
    # 全程最优位置：1280 最多同时点到 13/15 枚，1024 最多 10/15 枚
    assert min(s["deadCount"] for s in r["v1280"]["sweep"]) == 2, r["v1280"]["sweep"]
    assert min(s["deadCount"] for s in r["v1024"]["sweep"]) == 5, r["v1024"]["sweep"]


def check_2(r: dict[str, Any]) -> None:
    """滚轮在底部条任意横向位置都生效（一次「不生效」的读数是探针假象）。"""
    for p in r["v1280"]["wheelPoints"]:
        assert p["to"] == r["v1280"]["bar0"]["scrollW"] - r["v1280"]["bar0"]["clientW"], p
    assert len(r["v1280"]["wheelPoints"]) == 5, r["v1280"]["wheelPoints"]


def check_3(r: dict[str, Any]) -> None:
    """滚动只是把死控件从一头换到另一头：两个极端的死亡集合互不相交。"""
    a, b = r["v1280"]["deadAt0"], r["v1280"]["deadAtMax"]
    assert set(a).isdisjoint(b), (a, b)
    assert set(b) == {"移动", "旋转", "缩放"}, b
    assert "发送" in a and "描述想搭建的场景" in a, a
    # 滚到最右之后，右端那三枚确实活过来了（不是永久不可达）
    for k in r["v1280"]["barMax"]["kids"]:
        if k["label"] in ("发送", "描述想搭建的场景", "上传图片"):
            assert k["hitSelf"] and k["inBox"], k


def check_4(r: dict[str, Any]) -> None:
    """1280 下两个可滚容器，互不联动，但滚轮都有效。"""
    v = r["v1280"]
    assert len(v["scrollable"]) == 2, v["scrollable"]
    keys = set(v["scrollable"])
    assert "data-director-bottom-bar=true" in keys, v["scrollable"]
    assert "data-director-timeline=true" in keys, v["scrollable"]
    for l in v["links"]:
        assert l["drove"] and l["drove"]["after"] == l["max"], l
        assert l["moved"] == [], f"{l['key']} 滚到底带动了别的容器：{l['moved']}"
        assert l["wheelTo"] == l["max"], l


def check_5(r: dict[str, Any]) -> None:
    """1024 下冒出第三个容器（工具条，溢出 20px），依然零联动。"""
    v = r["v1024"]
    assert len(v["scrollable"]) == 3, v["scrollable"]
    assert "data-director-timeline-controls-scroll=true" in v["scrollable"], v["scrollable"]
    tb = v["toolbar"]
    assert tb["scrollW"] - tb["clientW"] == 20, tb
    assert any(c["label"] == "删除关键帧" for c in tb["clipped"]), tb["clipped"]
    for l in v["links"]:
        assert l["moved"] == [], f"{l['key']} 滚到底带动了别的容器：{l['moved']}"
        assert l["wheelTo"] == l["max"], l
    # 1280 下工具条不溢出，所以第三个容器是 1024 才出现的
    assert "data-director-timeline-controls-scroll=true" not in r["v1280"]["scrollable"]


def check_6(r: dict[str, Any]) -> None:
    """三个容器里只有时间轴那一个写了滚动条样式 —— 另两个没有任何可见提示。"""
    for vw in ("v1280", "v1024"):
        keys = r[vw]["tinyScrollbarKeys"]
        assert keys == ["data-director-timeline=true"], (vw, keys)


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
        ("the-bottom-bar-never-shows-all-of-its-controls", lambda: check_1(got.get("run", {}))),
        ("the-wheel-scrolls-the-bottom-bar-everywhere", lambda: check_2(got.get("run", {}))),
        ("scrolling-the-bottom-bar-trades-one-set-of-dead-controls-for-another", lambda: check_3(got.get("run", {}))),
        ("the-desk-has-two-independent-horizontal-scrollers-at-1280", lambda: check_4(got.get("run", {}))),
        ("a-third-scroller-appears-at-1024-and-nothing-cross-links", lambda: check_5(got.get("run", {}))),
        ("only-the-timeline-scroller-has-a-styled-scrollbar", lambda: check_6(got.get("run", {}))),
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
