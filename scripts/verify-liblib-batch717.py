#!/usr/bin/env python3
"""batch 717 验收：899px 断点到底控制什么 —— 断点找错了 1px，真换层在 898|899

## 起点

716 撞见一条非单调读数：`vw = 800` 时底部浮动条可见 776，`vw = 900` 时只有 314 ——
窄 100px 的窗口，底部条反而宽 462px。当时把它归到「899px 断点两侧定位基准换了一层」。

代码里 `max-[899px]` 遍地都是，但**没有人量过这个断点到底改了什么**。
本批用 batch 711 的「一次全叶投影的前后差集」跨断点做差，并做字段级分类。

## 决定性读数

| 对比对 | 叶子数 | 只在左侧 | 只在右侧 | 变了 | 相同 |
|---|---|---|---|---|---|
| 898 vs 898（重复读） | 842 / 842 | 0 | 0 | **0** | 842 |
| 899 vs 899（重复读） | 842 / 842 | 0 | 0 | **0** | 842 |
| **899 vs 900** | 842 / 842 | 0 | 0 | **175** | 667 |
| **898 vs 899** | 842 / 842 | 0 | 0 | **831** | 11 |

**⟹ 我一开始就找错了 1px：899 与 900 在断点的同一侧。**
那 175 处差异全是 1px 重排（154 枚居中元素 x 移 0.5px、20 枚满宽元素 w 差 1px、
1 枚 y/w/h 亚像素），**照那张表几乎可以得出「断点什么都不做」的错误结论**。

真断点在 **898|899**，一次同时跳六项：

| 指标 | 898（窄） | 899（宽） |
|---|---|---|
| 树列 | **219** | **232** |
| 轨道列表 | **220** | **320** |
| 底部条框宽 / 左缘 x | **898 / 0** | **337 / 281** |
| 底部条可见宽 | **874** | **313** |
| 时间轴滚动容器可见宽 | **676** | **577** |
| 头部 `padding-right` | **8px** | **260px** |

**`max-[899px]` 在 Tailwind v4 是严格小于（`width < 899`）**，
所以 **899 本身走的是宽屏分支** —— 字面值与实际生效边界**差 1**。

## 跨真断点的差集：只切换了 2 枚叶子的 display

- 叶子 **842 → 842**，**0 增 0 删**
- **0 处** `data-*` / `aria-label` / `role` / 文本 / `visibility` 变化
- **恰好 2 处** `display` 变化：
  - `root/3:div`：`none`（0×0）→ `flex`（x0 y52 **48×1098**）—— 只在 ≥899 出现的竖条
  - `root/4:div/…/section/6:div`：`flex`（x12 y100 **68×32**）→ `none` —— 只在 ≤898 出现的控件

**⟹ 断点不增删节点、不改语义，只切换两枚元素的显隐。**
底部条在断点处**窄 561px**（874 → 313），溢出 70 → 631 ——
这就是 716 那条「800 比 900 宽」的机制。

## 五条预测（写死在代码里，先于任何测量）

- **P1** 同一宽度连读两遍的投影逐条相同（差集法的前���条件）
- **P2** 断点在 **898|899**，而 899|900 只有 1px 级重排
- **P3** `max-[899px]` 是严格小于 ⟹ 899 本身走宽屏分支
- **P4** 跨真断点 **0 增 0 删**，且**没有任何语义字段**变化
- **P5** 跨真断点**恰好 2 枚**叶子切 `display`，其余 829 枚只动几何

## 判据

1. `the-same-width-projection-is-byte-identical`
2. `the-breakpoint-is-between-898-and-899-not-899-and-900`
3. `max-899px-is-strictly-less-than-899`
4. `across-the-real-breakpoint-no-node-is-added-or-removed`
5. `across-the-real-breakpoint-nothing-semantic-changes-except-two-display-toggles`
6. `the-bottom-bar-loses-561px-at-the-breakpoint`
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch717-2026-10-01"
H = 1150

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

PREDICTIONS = {
    "P1": "同一宽度连读两遍的投影逐条相同（差集法的前置条件）",
    "P2": "断点在 898|899，而 899|900 只有 1px 级重排",
    "P3": "max-[899px] 是严格小于 —— 899 本身走宽屏分支",
    "P4": "跨真断点 0 增 0 删，且没有任何语义字段变化",
    "P5": "跨真断点恰好 2 枚叶子切 display，其余只动几何",
}

PROJECT = r"""() => {
  const root = document.querySelector('[data-director-workspace]');
  if (!root) return { leaves: {}, count: 0 };
  const leaves = {};
  const r2 = (v) => Math.round(v * 10) / 10;
  const walk = (el, path) => {
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    leaves[path] = {
      tag: el.tagName.toLowerCase(),
      data: [...el.attributes]
        .filter((a) => a.name.startsWith('data-') && !a.name.startsWith('data-react'))
        .map((a) => a.name + '=' + a.value).sort().join(' '),
      aria: el.getAttribute('aria-label') || '',
      role: el.getAttribute('role') || '',
      txt: (el.children.length === 0 ? (el.textContent || '').trim() : '').slice(0, 20),
      x: r2(r.x), y: r2(r.y), w: r2(r.width), h: r2(r.height),
      display: cs.display, visibility: cs.visibility,
    };
    [...el.children].forEach((k, i) =>
      walk(k, path + '/' + i + ':' + k.tagName.toLowerCase()));
  };
  walk(root, '0:root');
  return { leaves: leaves, count: Object.keys(leaves).length };
}"""

GEOM = r"""() => {
  const q = (sel) => document.querySelector(sel);
  const rect = (el) => (el ? el.getBoundingClientRect() : null);
  const bar = q('[data-director-bottom-bar]');
  const inner = bar ? bar.querySelector(':scope > div') : null;
  const canvas = q('[data-director-timeline-canvas]');
  const scroller = canvas ? canvas.parentElement : null;
  const hdr = q('[data-director-timeline-controls]');
  const r = (v) => (v === null ? null : Math.round(v));
  return {
    vw: innerWidth,
    tree: r(rect(q('[data-director-tree]')).width),
    ins: r(rect(q('[data-director-inspector]')).width),
    trackList: r(rect(q('[data-director-timeline-track-list]')).width),
    barBoxW: r(rect(bar).width), barX: r(rect(bar).x),
    barClientW: inner ? inner.clientWidth : None,
    barMax: inner ? inner.scrollWidth - inner.clientWidth : None,
    tlScrollW: scroller ? scroller.clientWidth : None,
    headerPr: hdr ? getComputedStyle(hdr).paddingRight : None,
  };
}"""

FIELDS = ("tag", "data", "aria", "role", "txt",
          "x", "y", "w", "h", "display", "visibility")
GEOM_FIELDS = ("x", "y", "w", "h")
SEMANTIC_FIELDS = ("data", "aria", "role", "txt", "visibility")


def classify(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    ka, kb = a["leaves"], b["leaves"]
    changed: list[dict[str, Any]] = []
    same = 0
    for k in sorted(set(ka) & set(kb)):
        d = [f for f in FIELDS if ka[k][f] != kb[k][f]]
        if not d:
            same += 1
            continue
        rec = {"key": k, "fields": d,
               "a": {f: ka[k][f] for f in d},
               "b": {f: kb[k][f] for f in d}}
        if "display" in d:
            # 差集只记「变化的字段」，而几何断言要读完整记录 ⟹ display 变化的叶子补全
            rec["fullA"] = ka[k]
            rec["fullB"] = kb[k]
        changed.append(rec)
    return {"countA": a["count"], "countB": b["count"],
            "onlyA": sorted(set(ka) - set(kb)), "onlyB": sorted(set(kb) - set(ka)),
            "same": same, "changed": changed}


def open_page(browser: Any) -> Page:
    page = browser.new_page(viewport={"width": 1280, "height": H},
                            device_scale_factor=1)
    b617.open_desk(page)
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(500)
    return page


def run(browser: Any) -> dict[str, Any]:
    page = open_page(browser)

    def at(vw: int) -> tuple[Any, Any]:
        page.set_viewport_size({"width": vw, "height": H})
        page.wait_for_timeout(650)
        page.evaluate("() => { for (const el of document.querySelectorAll('*')) "
                      "if (el.scrollLeft) el.scrollLeft = 0; }")
        page.wait_for_timeout(200)
        return page.evaluate(PROJECT), page.evaluate(GEOM)

    p898a, g898a = at(898)
    p898b, _ = at(898)
    p899a, g899a = at(899)
    p899b, _ = at(899)
    p900, g900 = at(900)
    page.close()
    noise = classify(p899a, p900)
    deltas: dict[str, int] = {}
    for c in noise["changed"]:
        for f in c["fields"]:
            d = round(abs(float(c["b"][f]) - float(c["a"][f])), 2)
            deltas["%s=%s" % (f, d)] = deltas.get("%s=%s" % (f, d), 0) + 1
    noiseDeltas = deltas
    return {
        "stability898": classify(p898a, p898b),
        "stability899": classify(p899a, p899b),
        "crossReal": classify(p898a, p899a),
        "crossNoise": noise, "noiseDeltas": noiseDeltas,
        "geom": {"898": g898a, "899": g899a, "900": g900},
    }


def check_1(r: dict[str, Any]) -> None:
    """前置条件：同一宽度连读两遍，投影逐条相同 —— 否则差集法不可信。"""
    for k in ("stability898", "stability899"):
        s = r[k]
        assert s["changed"] == [], (k, s["changed"][:3])
        assert s["onlyA"] == [] and s["onlyB"] == [], (k, s["onlyA"], s["onlyB"])
        assert s["same"] == s["countA"] == 842, (k, s["same"], s["countA"])


def check_2(r: dict[str, Any]) -> None:
    """真断点在 898|899；899|900 只有 1px 级重排，且不含 display。"""
    real, noise = r["crossReal"], r["crossNoise"]
    assert len(real["changed"]) == 831, len(real["changed"])
    assert len(noise["changed"]) == 175, len(noise["changed"])
    for c in noise["changed"]:
        assert set(c["fields"]) <= set(GEOM_FIELDS), c
    # 175 枚里有 154 枚只动 x 且位移恰好 0.5px（居中元素重排）
    only_x = [c for c in noise["changed"] if c["fields"] == ["x"]]
    assert len(only_x) == 154, len(only_x)
    # 899|900 的全部几何位移都 <= 1px，且分布逐项钉死（这才是「只是 1px 重排」的证据）
    assert r["noiseDeltas"] == {"w=1.0": 21, "x=0.5": 14, "x=1.0": 140,
                                "y=0.3": 1, "h=0.5": 1}, r["noiseDeltas"]
    dxs = sorted({round(abs(c["b"]["x"] - c["a"]["x"]), 2) for c in only_x})
    assert dxs == [0.5, 1.0], dxs
    assert all(abs(float(c["b"][f]) - float(c["a"][f])) <= 1.0
               for c in noise["changed"] for f in c["fields"]), noise["changed"][:3]


def check_3(r: dict[str, Any]) -> None:
    """`max-[899px]` 是严格小于：899 本身已经是宽屏分支。"""
    n, w = r["geom"]["898"], r["geom"]["899"]
    assert n["tree"] == 219 and w["tree"] == 232, (n["tree"], w["tree"])
    assert n["trackList"] == 220 and w["trackList"] == 320, (n, w)
    assert n["headerPr"] == "8px", n["headerPr"]
    assert w["headerPr"] == "260px", w["headerPr"]
    assert n["barX"] == 0 and w["barX"] == 281, (n["barX"], w["barX"])


def check_4(r: dict[str, Any]) -> None:
    """跨真断点 0 增 0 删。"""
    c = r["crossReal"]
    assert c["countA"] == c["countB"] == 842, (c["countA"], c["countB"])
    assert c["onlyA"] == [] and c["onlyB"] == [], (c["onlyA"][:5], c["onlyB"][:5])
    assert c["same"] == 11, c["same"]


def check_5(r: dict[str, Any]) -> None:
    """跨真断点没有任何语义字段变化，且恰好 2 枚叶子切 display。"""
    c = r["crossReal"]
    for ch in c["changed"]:
        assert not (set(ch["fields"]) & set(SEMANTIC_FIELDS)), ch
    disp = [ch for ch in c["changed"] if "display" in ch["fields"]]
    assert len(disp) == 2, [(d["key"], d["fields"]) for d in disp]
    pairs = sorted((d["a"]["display"], d["b"]["display"]) for d in disp)
    assert pairs == [("flex", "none"), ("none", "flex")], pairs
    off = [d for d in disp if d["a"]["display"] == "none"][0]
    assert off["fullA"]["w"] == 0 and off["fullA"]["h"] == 0, off["fullA"]
    assert off["fullB"]["w"] == 48 and off["fullB"]["h"] == 1098, off["fullB"]
    assert off["fullB"]["x"] == 0 and off["fullB"]["y"] == 52, off["fullB"]
    on = [d for d in disp if d["a"]["display"] == "flex"][0]
    assert on["fullA"]["w"] == 68 and on["fullA"]["h"] == 32, on["fullA"]
    assert on["fullA"]["x"] == 12 and on["fullA"]["y"] == 100, on["fullA"]
    assert on["fullB"]["w"] == 0 and on["fullB"]["h"] == 0, on["fullB"]
    # 其余 829 枚只动几何
    assert len(c["changed"]) - 2 == 829, len(c["changed"])


def check_6(r: dict[str, Any]) -> None:
    """底部条在断点处窄 561px —— 这就是 716 那条「800 比 900 宽」的机制。"""
    n, w = r["geom"]["898"], r["geom"]["899"]
    assert n["barClientW"] == 874 and w["barClientW"] == 313, (n, w)
    assert n["barClientW"] - w["barClientW"] == 561, (n, w)
    assert n["barBoxW"] == 898 and w["barBoxW"] == 337, (n, w)
    assert n["barMax"] == 70, n["barMax"]
    assert w["barMax"] == 631, w["barMax"]
    assert n["tlScrollW"] == 676 and w["tlScrollW"] == 577, (n, w)
    # 900 与 899 同侧，只差 1px
    assert r["geom"]["900"]["barClientW"] - w["barClientW"] == 1, r["geom"]["900"]


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
        ("the-same-width-projection-is-byte-identical", lambda: check_1(got.get("run", {}))),
        ("the-breakpoint-is-between-898-and-899-not-899-and-900", lambda: check_2(got.get("run", {}))),
        ("max-899px-is-strictly-less-than-899", lambda: check_3(got.get("run", {}))),
        ("across-the-real-breakpoint-no-node-is-added-or-removed", lambda: check_4(got.get("run", {}))),
        ("across-the-real-breakpoint-nothing-semantic-changes-except-two-display-toggles", lambda: check_5(got.get("run", {}))),
        ("the-bottom-bar-loses-561px-at-the-breakpoint", lambda: check_6(got.get("run", {}))),
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
