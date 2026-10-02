#!/usr/bin/env python3
"""batch 678 验收：**中心口径每格漏掉约 26 枚控件** —— 换成 5×5 网格,遮挡人口从 1–6 涨到 27–33

## 起点

676/677 连续两批指出同一条口径的覆盖边界：**探测点只取控件中心**。
677 给的修法是「多读一个 `getComputedStyle(el).pointerEvents`」。

本批先量那条修法：**130 枚控件里 `pointer-events:none` 的有 0 枚** ——
664 记的那 22 个 `pe:none` 元素**与控件总体零重叠**。
所以 677 的建议是**保险，不是现存缺口**（这条先记下来，免得把它当成已修的问题）。

然后做真正有后果的那件事：**把探测点从「一个中心」换成「5×5 网格」**。

## 三条读数

### 1. 人口：三条口径差一个数量级

| 视口格 | 667 口径 | 中心口径 | **网格口径（5×5 = 25 样本）** | 中心漏掉 |
|---|---|---|---|---|
| 1280×720 | 2 | 6 | **33** | **27** |
| 1280×1150 | 2 | 4 | **30** | 26 |
| 1366×1150 | 2 | 3 | **29** | 26 |
| 1440×1150 | 1 | 2 | **29** | 27 |
| 1600×1150 | 1 | 1 | **27** | 26 |
| 1920×1150 | 1 | 1 | **27** | 26 |

恒有 **667 ⊆ 中心 ⊆ 网格**，而 |中心| ≤ 6、|网格| ≥ 27。
**中心口径在每一格都固定漏掉 26 枚 / 130 枚（20%）**，另有 2 枚只在 1/6 格里被漏到。

### 2. 漏掉的那些是可归因的，不是噪声

按 data 键认同（**不按名字** —— 673/674 的纪律），漏掉的 26 枚对应 **22 个 data 键**，
归到 **6 个盖住者族**；每一枚的遮挡比例**全是 1/25 的整数倍**
（0.12 = 3/25、0.20 = 5/25、0.40 = 10/25）——
**盖住的是整列网格样本，说明盖住者是轴对齐矩形，不是抖动**。

| 控件（data 键） | 枚 | 盒 | 占比 | 盖住者 | 出现格 |
|---|---|---|---|---|---|
| `data-director-transform-field=position/rotation/scale` | **9** | 59×28 | **0.40** | `button.shrink-0.cursor-ew-resize`（**它自己的轴片**） | 6/6 |
| `data-director-viewport-gizmo-button=x/z-negative` | 2 | 15×15 | 0.12 | `button.absolute.h-[15px]` | 6/6 |
| 播放条/时间轴 15 个键（`playback` / `loop` / `timeline-time` / `add-keyframe` / …） | 15 | 24–109×24/28 | 0.20 | `div.absolute.inset-x-0`（轨道行高亮层） | 6/6 |
| `data-director-uniform-scale=true` | 1 | 96×16 | 0.40 | `section.z-40.pointer-events-auto`（浮层） | 1/6 |
| `data-director-scene-prompt-input=true` | 1 | 143×16 | 0.40 | `div.absolute.inset-0`（视口面） | 1/6 |

**第一族最值得记**：检视器那个数值框被**它自己的轴片按钮**盖掉 40%，
而源码 `DirectorInspector.tsx:172-175` 写着「`pl-6` 让开轴片」——
**让开的是左内边距，轴片仍然落在这个 `<input>` 的盒内**。
中心探针看不见它，因为轴片在左边，而中心是空的。

## 自记：一条判据把「没测」读成了「测了不一样」

第 3 条判据本批第一版写成「网格的 `(0.5,0.5)` 样本必须等于中心探针」，
运行失败。原因是**中心落在视口外的控件，网格根本不采样**（`gridCentre` 留 `null`），
而中心探针对同一批控件返回 `false` —— 我把 `null` 和 `false` 比成了「不一致」。

**一个缺失的字段读起来就是一个值**（670 已经吃过一次：`filter(r => r.disagree)`
恒为 0 那次）。这次是它的反面：`null` 被读成了「否」。
改成**只在网格真的采到那个点时才比**，并把「没采到」的枚数单列成第三态。

另：第一版断言按探针里的 4 格写了具体数字，验收器跑 6 格时对不上 ——
改成断言**结构**（`|中心| < |网格|`、占比是 1/25 的整数倍、盖住者族数 ≤ 6），
具体名单记进载荷。**会因视口格数而变的数字不钉死。**

## 不声称

- **不声称**那 26 枚「是缺陷」—— 其中多数是**源站实测过的布局**（`pl-6` 让开轴片、
  轨道行高亮层），是**设计上就压在盒内**的；本批只主张**中心口径看不见它们**；
- **不声称**网格口径是「正确的口径」—— 5×5 仍是采样，边界情形仍可能漏；
- **不声称**占比 0.40/0.20/0.12 在别的格点数下不变（它们是 1/25 的倍数这件事依赖格数）；
- **不声称** 664 的 22 个 `pe:none` 元素有问题 —— 本批只记下**它们与 130 枚控件零重叠**。
"""

import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch678-2026-10-01"

CELLS = [(1280, 720), (1280, 1150), (1366, 1150), (1440, 1150),
         (1600, 1150), (1920, 1150)]
# 5×5，**含 0.5** —— 这样中心探针与网格的 (0.5,0.5) 必须是同一个点，
# 两条代码路径可以互验（check 2 就是在验这件事）。
FRACS = [0.1, 0.3, 0.5, 0.7, 0.9]

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

spec2 = importlib.util.spec_from_file_location(
    "b667", ROOT / "scripts/verify-liblib-batch667.py")
b667 = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(b667)

JS = r"""(fracs) => {
  const scope = document.querySelector('[data-director-workspace]') || document.body;
  const SEL = 'button, [role=button], [role=tab], [role=switch], [role=slider],'
    + ' [role=menuitem], input, select, textarea, a[href],'
    + ' [tabindex]:not([tabindex="-1"])';
  const cs = (e) => getComputedStyle(e);
  const lab = (e) => e.getAttribute('aria-label') || e.getAttribute('placeholder')
    || (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 24)
    || e.getAttribute('title') || '<' + e.tagName.toLowerCase() + '>';
  const dataOf = (e) => { for (let n = e; n && n !== document.body; n = n.parentElement)
      for (const a of n.attributes) if (a.name.startsWith('data-')) return a.name + '=' + a.value;
    return '-'; };
  const ident = (e) => e.tagName.toLowerCase() + '|'
    + (e.getAttribute('class') || '').trim().split(/\s+/).slice(0, 2).join('.');
  const vis = (e) => { const s = cs(e);
    if (s.display === 'none' || s.visibility === 'hidden') return false;
    const b = e.getBoundingClientRect();
    return b.width > 0 && b.height > 0 && parseFloat(s.opacity) !== 0; };
  const own = (a, b) => !!(a && b && (a === b || a.contains(b) || b.contains(a)));

  const rows = [];
  for (const el of scope.querySelectorAll(SEL)) {
    if (!vis(el)) continue;
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    let samples = 0, foreign = 0, gridCentre = null;
    const coverers = {};
    for (const fx of fracs) for (const fy of fracs) {
      const px = r.x + r.width * fx, py = r.y + r.height * fy;
      if (px < 0 || py < 0 || px > innerWidth || py > innerHeight) continue;
      samples += 1;
      const hit = document.elementFromPoint(px, py);
      const isForeign = !!(hit && !own(hit, el));
      if (fx === 0.5 && fy === 0.5) gridCentre = isForeign;
      if (!isForeign) continue;
      foreign += 1;
      const k = ident(hit);
      coverers[k] = (coverers[k] || 0) + 1;
    }
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    const chit = (cx >= 0 && cy >= 0 && cx <= innerWidth && cy <= innerHeight)
      ? document.elementFromPoint(cx, cy) : null;
    rows.push({name: lab(el), data: dataOf(el),
               box: [Math.round(r.width), Math.round(r.height)],
               pe: cs(el).pointerEvents,
               samples, foreign, gridCentre,
               centre: !!(chit && !own(chit, el)),
               coverers});
  }
  return {vw: innerWidth, vh: innerHeight, rows};
}"""


def _clean(page) -> None:
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(80)


class Verifier:
    def __init__(self) -> None:
        self.result: dict[str, Any] = {}
        self.failures: list[str] = []
        self.count = 0

    def check(self, name: str, ok: bool, detail: Any = "", note: str = "") -> None:
        self.count += 1
        self.result[name] = {"ok": bool(ok), "detail": detail, "note": note or None}
        if not ok:
            self.failures.append(name)
        print(("  PASS " if ok else "  FAIL ") + name
              + (f"  {str(detail)[:130]}" if detail else "")
              + (f"  [{note[:96]}]" if note else ""))


def main() -> int:
    v = Verifier()
    cells: dict[str, Any] = {}
    c667: dict[str, list] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        for (w, h) in CELLS:
            page = br.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
            b617.open_desk(page)
            _clean(page)
            cells[f"{w}x{h}"] = page.evaluate(JS, FRACS)
            c667[f"{w}x{h}"] = sorted({x["control"] for x in page.evaluate(b667.JS)["ch3b"]})
            page.close()
        br.close()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"stage": "raw-readings", "cells": cells, "c667": c667},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    keys = list(cells)
    TOTAL = cells[keys[0]] and len(cells[keys[0]]["rows"])
    SAMPLE = len(FRACS) ** 2

    pop = {k: {"controls": len(cells[k]["rows"]),
               "centre": sum(1 for r in cells[k]["rows"] if r["centre"]),
               "grid": sum(1 for r in cells[k]["rows"] if r["foreign"] > 0),
               "c667": len(c667[k])} for k in keys}
    missed = {k: sum(1 for r in cells[k]["rows"]
                     if r["foreign"] > 0 and not r["centre"]) for k in keys}
    pe_none = {k: sum(1 for r in cells[k]["rows"] if r["pe"] == "none") for k in keys}

    # 跨格聚合 grid-only 人口：按 (data 键, 盒) 认同一枚控件 —— **不按名字**（673/674 的纪律）
    agg: dict[tuple, dict[str, Any]] = defaultdict(
        lambda: {"cells": 0, "fracs": [], "coverers": Counter(), "names": set()})
    for k in keys:
        for r in cells[k]["rows"]:
            if r["foreign"] > 0 and not r["centre"]:
                a = agg[(r["data"], tuple(r["box"]))]
                a["cells"] += 1
                a["fracs"].append(round(r["foreign"] / r["samples"], 3))
                a["names"].add(r["name"])
                for c, n in r["coverers"].items():
                    a["coverers"][c] += n
    families = sorted({c for a in agg.values() for c in a["coverers"]})
    fracs_seen = sorted({f for a in agg.values() for f in a["fracs"]})
    exact = all(abs(round(f * SAMPLE) - f * SAMPLE) < 1e-9 for f in fracs_seen)

    # 检视器数值框那一族：按 data 键认（9 枚 transform-field × axis）
    tf = [r for r in cells[keys[0]]["rows"] if "data-director-transform-field" in r["data"]]
    tf_grid = [r for r in cells[keys[0]]["rows"]
               if "data-director-transform-field" in r["data"] and r["foreign"] > 0]
    tf_coverers = sorted({c for r in tf_grid for c in r["coverers"]})

    # 两条代码路径互验：网格的 (0.5,0.5) 必须等于中心探针。
    # **只在网格真的采到那个点时才比** —— 中心落在视口外时网格不采样、留 null，
    # 而中心探针给出 false。把 null 当成「不一致」就是把「没测」读成「测了不一样」。
    compared = [(k, r) for k in keys for r in cells[k]["rows"] if r["gridCentre"] is not None]
    unsampled = [(k, r) for k in keys for r in cells[k]["rows"] if r["gridCentre"] is None]
    disagree = [(k, r["name"]) for (k, r) in compared if r["gridCentre"] != r["centre"]]
    agree = not disagree

    v.check("no-control-in-the-population-has-pointer-events-none",
            all(pe_none[k] == 0 for k in keys) and 0.5 in FRACS,
            detail={"controls": pop[keys[0]]["controls"],
                    "pointerEventsNonePerCell": pe_none,
                    "what677Recommended": "read getComputedStyle(el).pointerEvents",
                    "reading": "that extra read lands on an EMPTY quadrant in this clone — "
                               "664's 22 pe:none elements are all non-controls, so the "
                               "recommendation is insurance, not a fixed defect"},
            note="record this BEFORE building on 677's recommendation")

    v.check("the-5x5-grid-probe-sees-four-to-thirty-times-the-centre-probe",
            all(0 < pop[k]["centre"] < pop[k]["grid"] for k in keys)
            and min(pop[k]["grid"] for k in keys) >= 20
            and all(missed[k] >= 20 for k in keys),
            detail={"population": pop, "missedByCentre": missed,
                    "samplesPerControl": SAMPLE, "controls": TOTAL},
            note="centre sees 1-6, the grid sees 27-33, at every cell")

    v.check("the-two-probe-paths-agree-on-every-sample-both-of-them-actually-took",
            agree and 0.5 in FRACS and len(unsampled) > 0,
            detail={"fracs": FRACS,
                    "comparedControlCells": len(compared),
                    "unsampledBecauseCentreIsOffViewport": len(unsampled),
                    "disagreements": disagree,
                    "thirdState":
                        "gridCentre is null when the control's centre lies outside the "
                        "viewport, so the grid never samples it. That is `missing`, not "
                        "`measured false` — and the centre probe does return false there."},
            note="an instrument cross-check: the two are different expressions in the "
                 "page. The first version of this check compared null against false and "
                 "reported a disagreement that was really an unmeasured point")

    v.check("every-missed-control-has-a-named-coverer-and-a-fraction-of-the-grid",
            len(agg) > 0 and len(families) <= 6 and exact,
            detail={"distinctMissedControls": len(agg),
                    "covererFamilies": families,
                    "fractionsSeen": fracs_seen,
                    "allFractionsAreExactMultiplesOf1Over25": exact},
            note="0.12/0.20/0.40 are 3/25, 5/25, 10/25 — the coverers are axis-aligned "
                 "rects covering whole grid columns, not jitter")

    v.check("the-nine-inspector-number-boxes-are-40-percent-covered-by-their-own-axis-chips",
            len(tf) == 9 and len(tf_grid) == 9
            and all(r["foreign"] / r["samples"] == 0.4 for r in tf_grid)
            and tf_coverers == ["button|shrink-0.cursor-ew-resize"],
            detail={"transformInputs": len(tf), "gridOccluded": len(tf_grid),
                    "fraction": sorted({round(r["foreign"] / r["samples"], 3) for r in tf_grid}),
                    "coverers": tf_coverers,
                    "sourceFact":
                        "src/components/director/DirectorInspector.tsx:172-175 records the "
                        "source's number box as `h-full min-w-0 flex-1 pl-6 pr-0` with the "
                        "comment 'pl-6 让开轴片'. The padding makes room; the chips still sit "
                        "INSIDE the <input>'s box, so 40% of it is covered."},
            note="the centre probe cannot see it — the chips are on the left, the centre "
                 "is clear")

    v.check("667s-population-is-the-smallest-of-the-three-at-every-cell",
            all(pop[k]["c667"] <= pop[k]["centre"] < pop[k]["grid"] for k in keys)
            and all(set(c667[k]) <= {r["name"] for r in cells[k]["rows"] if r["centre"]}
                    for k in keys),
            detail={"c667": {k: c667[k] for k in keys},
                    "perCell": pop,
                    "why": "667's census additionally requires an enclosing "
                           "pointer-events:none layer, so it is a subset of the centre "
                           "probe's population, which is itself a subset of the grid's"},
            note="three probe rules, three populations, one order")

    out = {"cells": keys, "fracs": FRACS, "samplesPerControl": SAMPLE,
           "controls": TOTAL, "population": pop, "missedByCentre": missed,
           "pointerEventsNonePerCell": pe_none, "c667": c667,
           "missedDistinct": [{"data": k2[0], "box": list(k2[1]), "cells": a["cells"],
                               "fracs": a["fracs"], "names": sorted(a["names"]),
                               "coverers": a["coverers"].most_common()}
                              for k2, a in sorted(agg.items(), key=lambda kv: -kv[1]["cells"])],
           "covererFamilies": families, "fractionsSeen": fracs_seen,
           "transformInputs": {"count": len(tf), "gridOccluded": len(tf_grid),
                               "coverers": tf_coverers},
           "judged": sum(pop[k]["controls"] for k in keys) * SAMPLE}
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "cells": cells, "c667": c667, "checks": v.result},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
