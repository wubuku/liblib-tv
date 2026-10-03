#!/usr/bin/env python3
"""batch 724 验收：Handles 才是画布的控件；缩放快捷键没坏 —— 坏的是「菜单开着时按」

## 起点

723 普查画布，得出一句「十张卡只有一张带控件，其余九张零控件」。
本批顺着自己的 Handle 往下走，发现那句话**说过头了**：
723 的普查只数了 `button`，而 React Flow 的 Handle 是
`<div class="react-flow__handle">`，根本没进那个集合。

## 决定性读数（`/?batch70=1`，1280×1150，导演台关着）

### 纠正 723：「零控件」应为「零按钮」

**十张卡每张都有 2 个 Handle**（`target` + `source`），共 20 个，
每个实测 **11×11**（源码写的是 `style={{width:20,height:20}}`，
20 × 画布缩放 0.526 ≈ 11 ⟹ **Handle 跟着画布一起缩放**）。

`data-connectable` 属性为 `null`，可连接性只体现在 class 的 `connectable` 上。

默认视口下 20 个 Handle 里 **9 个在屏**（其余 11 个出屏）。

### 缩放菜单：六档全部生效

菜单 **188×279** @(88,817)，当前值 53%，六个动作各 36 高：
`放大 ⌘+` / `缩小 ⌘−` / `适合屏幕 ⌘0` / `缩放至50%` / `缩放至100%` / **`缩放至800%`**。

| 动作 | 读数 |
|---|---|
| 放大 ×2 | 38 → **48** → **58**（步长 ±10pp） |
| 缩小 | 58 → **48** |
| 50% | `matrix(0.5, …)` |
| 100% | `matrix(1, …)` |
| **800%** | **`matrix(8, …)`** —— 真到 8 倍 |
| 适合屏幕 | **38** |

### 缩放快捷键没坏 —— 但只在「没有面板开着」的时候

| 前提 | ⌘+ | ⌘0 | ⌘− |
|---|---|---|---|
| **干净状态** | **+10pp** ✓ | 落到 **38%（= fit 值）** ✓ | **−10pp** ✓ |
| **缩放菜单开着** | 不变 ✗ | 不变 ✗ | 不变 ✗ |

（干净状态的绝对读数随前置视口而变，从 53% 起是 53 → 63 → 38 → 28；
验收器改按相对变化断言，不写死起点。）

源码侧：`handleKeyDown` 开头有
`if (resolveLibTVBlockingForegroundSurface(uiState)) return;`，
而 `resolveLibTVBlockingForegroundSurface` 把 `isZoomMenuOpen` 列为阻塞面。

⟹ **菜单上印给自己的三个快捷键提示，在菜单打开期间全部不成立**；
Escape 关掉面板后同一个键就可用。
（第一版探针刚点过菜单项就按键，得出「⌘+/⌘0 坏了」的假结论 ——
**这是我自己的读数污染**，第二版做 A/B 才分清。）

### 手工连线：两对都试了，都没成

| 试的配对 | 结果 |
|---|---|
| 照抄现有连线 `i-1FQ9tErTcC → b-bTLLuU4w5q`（必然合法，且已存在） | 11 → **11** |
| 新配对 `i-1FQ9tErTcC → i-vxeeCnxySa`（按规则应当允许：无重复对、无有向环） | 11 → **11** |

过程中 `.react-flow__connection` **出现了**（手势被 React Flow 认出），
但 `.react-flow__handle-connecting` **全程为 null**、valid 手柄恒 **0 个**
⟹ `onConnect` 从未触发。

## 不声称

- **不声称「画布不能手工连线」是缺陷** —— 探针能做的范围内没成功，
  但**成因未取证**：可能是手势需要更多中间点 / 更慢，也可能是
  `isValidConnection` 在 react-flow 的参数下与源码规则不一致。
  **下一步该做的是把 `isValidConnection` 的返回值 instrument 出来。**
- **不声称 723 的读数错了** —— 723 的判据是「按钮数」，读数正确，
  **错的是它顺带说的「零控件」这个概括**。
- **不声称源站画布有/没有这些 Handle**（源站未测）。

## 方法论

1. **概括比判据宽一步时，要回去看判据到底测了什么** ——
  723 判的是「每张卡几个 `button`」，说的是「零控件」。
  **判据只覆盖了按钮，凭什么说控件？**
2. **「我刚做过什么」要进读数的解释里** ——
  「⌘+ 无效」这个结论只在我先点开过缩放菜单时成立；
  同一个键在干净状态下有效。**读数不可用时先查操作历史，别急着开单。**
3. **A/B 要只变一个变量** —— 第二版把「有没有面板开着」作为唯一变量，
  其余（焦点元素、视口、缩放档位）全部固定，才分得清。
4. **失败的手势要看中间态** —— 只看 `edges` 11→11 分不出「被规则拒绝」与
  「手势没被接住」；`.react-flow__connection` 出现了、valid 手柄 0 个，
  才把范围缩到「连接进入了一半」。
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch724-2026-10-01"
BASE = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
W, H = 1280, 1150

HANDLES_JS = r"""() => {
  const out = [];
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const hs = [...n.querySelectorAll('.react-flow__handle')].map((h) => {
      const hr = h.getBoundingClientRect();
      const cx = hr.x + hr.width / 2, cy = hr.y + hr.height / 2;
      return {
        tag: h.tagName.toLowerCase(),
        id: h.getAttribute('data-handleid'),
        cls: h.className,
        dataConnectable: h.getAttribute('data-connectable'),
        w: Math.round(hr.width), h: Math.round(hr.height),
        onScreen: cx >= 0 && cx <= window.innerWidth
          && cy >= 0 && cy <= window.innerHeight,
      };
    });
    out.push({id: n.getAttribute('data-id'), nHandles: hs.length,
              nBtns: n.querySelectorAll('button, [role="button"]').length,
              handles: hs});
  }
  return out;
}"""

ZOOM_JS = r"""() => {
  const b = document.querySelector('[data-viewport-menu-trigger="zoom"]');
  const rf = document.querySelector('.react-flow__viewport');
  return {text: (b ? b.textContent : '').trim(),
          matrix: rf ? getComputedStyle(rf).transform : null,
          menuOpen: !!document.querySelector('[data-liblib-overlay="zoom-menu"]')};
}"""

MENU_JS = r"""() => {
  const m = document.querySelector('[data-liblib-overlay="zoom-menu"]');
  if (!m) return null;
  const r = m.getBoundingClientRect();
  return {
    rect: {w: Math.round(r.width), h: Math.round(r.height),
           x: Math.round(r.x), y: Math.round(r.y)},
    current: (m.querySelector('[data-zoom-current]') || {}).textContent,
    actions: [...m.querySelectorAll('[data-zoom-action]')].map((x) => ({
      action: x.getAttribute('data-zoom-action'),
      label: (x.textContent || '').trim(),
      h: Math.round(x.getBoundingClientRect().height)})),
  };
}"""

EDGES_JS = r"""() => window.__libtv_store.getState().getActiveCanvas()
  .edges.map((e) => ({id: e.id, source: e.source, target: e.target}))"""


def zoom(page: Page) -> dict[str, Any]:
    return page.evaluate(ZOOM_JS)


def click_action(page: Page, action: str) -> None:
    if not page.evaluate("() => Boolean(document.querySelector"
                         "('[data-liblib-overlay=\"zoom-menu\"]'))"):
        page.evaluate("() => document.querySelector"
                      "('[data-viewport-menu-trigger=\"zoom\"]').click()")
        page.wait_for_timeout(400)
    page.evaluate("""(a) => { const b = document.querySelector(
        '[data-zoom-action="' + a + '"]'); if (b) b.click(); }""", action)
    page.wait_for_timeout(700)


def drag_pair(page: Page, src: str, dst: str) -> dict[str, Any]:
    plan = page.evaluate(r"""([s, d]) => {
      const pick = (id, side) => {
        const n = document.querySelector('.react-flow__node[data-id="' + id + '"]');
        if (!n) return null;
        const h = n.querySelector('.react-flow__handle-' + side);
        if (!h) return null;
        const r = h.getBoundingClientRect();
        return {x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2)};
      };
      return {src: pick(s, 'right'), dst: pick(d, 'left')};
    }""", [src, dst])
    res: dict[str, Any] = {"pair": [src, dst], "found": bool(plan["src"]
                                                             and plan["dst"])}
    if not res["found"]:
        return res
    page.mouse.move(plan["src"]["x"], plan["src"]["y"])
    page.mouse.down()
    page.wait_for_timeout(300)
    page.mouse.move((plan["src"]["x"] + plan["dst"]["x"]) // 2,
                    (plan["src"]["y"] + plan["dst"]["y"]) // 2, steps=10)
    page.wait_for_timeout(350)
    res["midDrag"] = page.evaluate("""() => ({
      connLine: !!document.querySelector('.react-flow__connection'),
      connecting: document.querySelectorAll(
        '.react-flow__handle-connecting').length,
      valid: document.querySelectorAll(
        '.react-flow__handle.valid, .react-flow__handle-connecting').length})""")
    page.mouse.move(plan["dst"]["x"], plan["dst"]["y"], steps=10)
    page.wait_for_timeout(500)
    res["atTarget"] = page.evaluate("""() => ({
      connecting: document.querySelectorAll(
        '.react-flow__handle-connecting').length,
      valid: document.querySelectorAll(
        '.react-flow__handle.valid, .react-flow__handle-connecting').length})""")
    page.mouse.up()
    page.wait_for_timeout(900)
    return res


def run(browser: Any) -> dict[str, Any]:
    page = browser.new_page(viewport={"width": W, "height": H},
                            device_scale_factor=1)
    r: dict[str, Any] = {}
    page.goto(f"{BASE}/?batch70=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__director_store)",
        timeout=60_000)
    page.evaluate("() => { for (const el of document.querySelectorAll"
                  "('nextjs-portal')) el.remove(); }")
    page.mouse.move(W - 4, 4)
    page.wait_for_timeout(1_200)

    r["handles"] = page.evaluate(HANDLES_JS)
    r["zoom0"] = zoom(page)

    page.evaluate("() => document.querySelector"
                  "('[data-viewport-menu-trigger=\"zoom\"]').click()")
    page.wait_for_timeout(500)
    r["menu"] = page.evaluate(MENU_JS)
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)

    # 六档逐档
    click_action(page, "fit")
    seq = []
    for a in ("in", "in", "out", "50", "100", "800", "fit"):
        click_action(page, a)
        seq.append({"action": a, "zoom": zoom(page)})
    r["menuSeq"] = seq

    # 快捷键：干净状态
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    page.mouse.move(W - 4, 4)
    page.wait_for_timeout(200)
    clean = [{"step": "start", **zoom(page)}]
    page.keyboard.press("Meta+Equal")
    page.wait_for_timeout(700)
    clean.append({"step": "cmdPlus", **zoom(page)})
    page.keyboard.press("Meta+Digit0")
    page.wait_for_timeout(700)
    clean.append({"step": "cmdZero", **zoom(page)})
    page.keyboard.press("Meta+Minus")
    page.wait_for_timeout(700)
    clean.append({"step": "cmdMinus", **zoom(page)})
    r["cleanShortcuts"] = clean

    # 快捷键：菜单开着
    page.evaluate("() => document.querySelector"
                  "('[data-viewport-menu-trigger=\"zoom\"]').click()")
    page.wait_for_timeout(500)
    blocked = [{"step": "menuOpen", **zoom(page)}]
    page.keyboard.press("Meta+Equal")
    page.wait_for_timeout(700)
    blocked.append({"step": "cmdPlus", **zoom(page)})
    page.keyboard.press("Meta+Digit0")
    page.wait_for_timeout(700)
    blocked.append({"step": "cmdZero", **zoom(page)})
    page.keyboard.press("Meta+Minus")
    page.wait_for_timeout(700)
    blocked.append({"step": "cmdMinus", **zoom(page)})
    r["menuOpenShortcuts"] = blocked
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)

    # 手工连线：照抄一条现有配对 + 一对没连过的
    click_action(page, "fit")
    r["edges0"] = page.evaluate(EDGES_JS)
    first = r["edges0"][0]
    r["dragExisting"] = drag_pair(page, first["source"], first["target"])
    r["edges1"] = page.evaluate(EDGES_JS)
    imgs = page.evaluate(r"""() => window.__libtv_store.getState()
        .getActiveCanvas().nodes.filter((n) => n.type === 'image')
        .map((n) => n.id)""")
    r["dragNew"] = drag_pair(page, imgs[0], imgs[-1])
    r["edges2"] = page.evaluate(EDGES_JS)
    page.close()
    return r


def check_1(r: dict[str, Any]) -> None:
    """纠正 723：十张卡每张两个 Handle，是 div 不是 button。"""
    hs = r["handles"]
    assert len(hs) == 10, len(hs)
    assert all(c["nHandles"] == 2 for c in hs), [c["id"] for c in hs]
    total = sum(c["nHandles"] for c in hs)
    assert total == 20, total
    for c in hs:
        for h in c["handles"]:
            assert h["tag"] == "div", h
            assert h["id"] in ("target", "source"), h
            assert "connectable" in h["cls"], h
            assert h["dataConnectable"] is None, h
    assert sum(c["nBtns"] for c in hs) == 1, sum(c["nBtns"] for c in hs)


def check_2(r: dict[str, Any]) -> None:
    """Handle 实测 11×11：源码写 20×20，被画布缩放 0.526 乘了一遍。"""
    ws = {h["w"] for c in r["handles"] for h in c["handles"]}
    hs = {h["h"] for c in r["handles"] for h in c["handles"]}
    assert ws == {11}, ws
    assert hs == {11}, hs
    assert round(20 * 0.526) == 11, 20 * 0.526
    assert r["zoom0"]["text"] == "53%", r["zoom0"]
    assert "0.526" in (r["zoom0"]["matrix"] or ""), r["zoom0"]


def check_3(r: dict[str, Any]) -> None:
    """默认视口下 20 个 Handle 里 9 个在屏。"""
    allh = [h for c in r["handles"] for h in c["handles"]]
    on = [h for h in allh if h["onScreen"]]
    assert len(allh) == 20, len(allh)
    assert len(on) == 9, [(h["id"], h["onScreen"]) for h in allh]


def check_4(r: dict[str, Any]) -> None:
    """缩放菜单六项各 36 高；菜单 188×279；六档逐档生效，含 800%。"""
    m = r["menu"]
    assert (m["rect"]["w"], m["rect"]["h"]) == (188, 279), m["rect"]
    acts = [a["action"] for a in m["actions"]]
    assert acts == ["in", "out", "fit", "50", "100", "800"], acts
    assert {a["h"] for a in m["actions"]} == {36}, m["actions"]
    seq = {s["action"]: s["zoom"] for s in r["menuSeq"]}
    assert [s["zoom"]["text"] for s in r["menuSeq"][:3]] == ["48%", "58%", "48%"]
    assert "matrix(0.5," in seq["50"]["matrix"], seq["50"]
    assert "matrix(1," in seq["100"]["matrix"], seq["100"]
    assert "matrix(8," in seq["800"]["matrix"], seq["800"]
    assert seq["800"]["text"] == "800%", seq["800"]
    assert seq["fit"]["text"] == "38%", seq["fit"]


def pct(text: str) -> int:
    return int(text.rstrip("%"))


def check_5(r: dict[str, Any]) -> None:
    """干净状态下 ⌘+ / ⌘0 / ⌘− 三个缩放快捷键全部生效（按相对变化断言）。

    起点不是固定值 —— 前面那一轮菜单遍历最后落在 fit，所以这里只断言
    「⌘+ 加 10pp、⌘0 落到 fit 的 38%、⌘− 再减 10pp」。
    """
    c = {s["step"]: s for s in r["cleanShortcuts"]}
    assert all(not s["menuOpen"] for s in r["cleanShortcuts"]), r["cleanShortcuts"]
    assert pct(c["cmdPlus"]["text"]) - pct(c["start"]["text"]) == 10, (
        c["start"]["text"], c["cmdPlus"]["text"])
    assert c["cmdZero"]["text"] == "38%", c["cmdZero"]
    assert "0.382865" in c["cmdZero"]["matrix"], c["cmdZero"]
    assert pct(c["cmdZero"]["text"]) - pct(c["cmdMinus"]["text"]) == 10, (
        c["cmdZero"]["text"], c["cmdMinus"]["text"])


def check_6(r: dict[str, Any]) -> None:
    """菜单开着时同样三个键全部失效 —— 菜单上印给自己的提示在此期间是假的。"""
    m = {s["step"]: s for s in r["menuOpenShortcuts"]}
    assert all(s["menuOpen"] for s in r["menuOpenShortcuts"]), r["menuOpenShortcuts"]
    assert m["menuOpen"]["text"] == "28%", m["menuOpen"]
    assert m["cmdPlus"]["text"] == "28%", m["cmdPlus"]
    assert m["cmdZero"]["text"] == "28%", m["cmdZero"]
    assert m["cmdMinus"]["text"] == "28%", m["cmdMinus"]
    labels = [a["label"] for a in r["menu"]["actions"][:3]]
    assert labels == ["放大⌘ +", "缩小⌘ -", "适合屏幕⌘ 0"], labels


def check_7(r: dict[str, Any]) -> None:
    """手工连线两对都不成立；中途连接线出现但 connecting/valid 恒 0。"""
    for key, before, after in (("dragExisting", "edges0", "edges1"),
                               ("dragNew", "edges1", "edges2")):
        d = r[key]
        assert d["found"] is True, d
        assert len(r[after]) == len(r[before]), (key, before, after)
        assert d["midDrag"]["connLine"] is True, (key, d)
        assert d["midDrag"]["connecting"] == 0, (key, d)
        assert d["midDrag"]["valid"] == 0, (key, d)
        assert d["atTarget"]["connecting"] == 0, (key, d)
        assert d["atTarget"]["valid"] == 0, (key, d)
    assert len(r["edges0"]) == 11, r["edges0"]


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
    results: dict[str, Any] = {}
    checks = [
        ("every-card-has-two-handles-which-are-divs-not-buttons",
         lambda: check_1(got.get("run", {}))),
        ("handles-are-11px-because-the-canvas-zooms-them-to-0.526",
         lambda: check_2(got.get("run", {}))),
        ("nine-of-twenty-handles-are-on-screen-in-the-default-viewport",
         lambda: check_3(got.get("run", {}))),
        ("all-six-zoom-menu-actions-work-including-800-percent",
         lambda: check_4(got.get("run", {}))),
        ("the-three-zoom-shortcuts-work-when-no-panel-is-open",
         lambda: check_5(got.get("run", {}))),
        ("the-same-three-shortcuts-are-dead-while-the-zoom-menu-is-open",
         lambda: check_6(got.get("run", {}))),
        ("hand-drawing-an-edge-never-completes-for-either-pair",
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
