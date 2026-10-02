#!/usr/bin/env python3
"""batch 681 验收：`帮助` 被时间轴底栏压死的**完整机制**是 `z-30` 对 `z-40` —— 几何上无法避免

## 起点

680 扫窗高时读到一条刺眼的读数：`data-director-rail-entry="help"`（左栏底部的「帮助」）
在**全部 18 个有样本的 (宽, 高) 组合**下 `frac = 1.00` —— 一次都没能被点到。
盖住者是时间轴对象行里的 `收起属性` 箭头。

本批只做**取证**，把机制拆到可复算的最小：**几何 + 层叠各一条**。
**本批不改 `src/`** —— 修法是**产品决定**，见 §5。

## 三条读数

### 1. 几何：重叠不是巧合，是**必然**

| 元素 | 盒（1280×1150） |
|---|---|
| 左栏容器 `absolute bottom-0 left-0 top-[52px] z-30 w-12` | `[0, 52, 48, 1098]` |
| `帮助`（`mt-auto`，被推到栏底） | `[8, 1110, 32, 32]` = **y ∈ [H−40, H−8]** |
| 时间轴底栏 `<section class="z-40 …">` | `[0, 968, 1280, 182]` = **y ∈ [H−182, H]** |
| `收起属性` 箭头（camera-main 行） | `[8, 1111, 20, 20]` |

**底栏高 182，而 `帮助` 距视口底只有 40 —— 182 > 40 ⟹ 两者必然相交，与视口宽高无关。**
这解释了 680 那条「与宽高都无关」：它不是巧合，是**尺寸关系决定的**。

### 2. 层叠：左栏 `z-30`，底栏 `z-40`

- 左栏容器：`position: absolute`，**`z-index: 30`**
- 时间轴底栏 section：`position: relative`，**`z-index: 40`**
- DOM 顺序：左栏（索引 257）**在**轨道列表（索引 587）**之前**

**`帮助` 中心的 `elementsFromPoint` 命中链（三格逐格相同）：**

```
1. button.group.relative.z-[1]        [8, 1111, 20, 20]   ← 收起属性箭头（相机行）
2. div[data-director-timeline-object-row=director-camera-main]  [0, 1105, 320, 32]
3. div                                   [0, 1105, 320, 64]
4. div.w-[320px]                         [0, 1005, 320, 145]  ← 轨道列表
5. div.flex                              [0, 1005, 1280, 145]
6. section.z-40                          [0, 968, 1280, 182]   ← 底栏
```

**`帮助` 自己连前 6 名都进不去。** 决定它的是**两个 z 值的比较**，不是谁在 DOM 里靠后
（DOM 顺序上左栏其实在前，是 z 值把它压下去了）。

### 3. 一条**待取证**的线索：源站的左列是 `z-10`

`src/components/director/DirectorTimeline.tsx:1591-1595` 里记着**源站实测**：

> Batch 600（源站实测）：… 源站左列 `z-10 shrink-0 bg-[#1f1f1f]` 的 borderRight 实测 0px。

而 clone 把这条左列放进了一个 **`z-40`** 的底栏 section 里，左栏自己是 `z-30`。

**若源站的左列真是 `z-10`，且源站左栏的 z 高于它，则源站里 `帮助` 是可点的。**

**这是由一条已记录的源站事实推出的假设，不是读数。**
本批**没有源站授权，不取证，因此不声称任何源站行为。**
（见 §5 的待授权项。）

## 4. 自记两条

1. 探针第一版找「左栏容器」用的判据是「高度 ≥ 80% 视口」，
   在 1280×720 抓到 `[0, 52, 48, 668]`（668/720 = 93%）——
   **判据碰巧成立，但它是比例阈值，换个视口就可能抓到错的祖先**。
   正式验收器改成沿 `position` 向上走到第一个非 static 的祖先（**可复算的规则**），
   并把两条判据的读数都记进载荷。
2. **我写了一条恒真判据**（`no-source-claim-is-made-…`，`v.check(..., True, …)`），
   理由是「把拒绝外推这件事钉住」。**这正是我自己反复记的那条反模式** ——
   一条不可能失败的判据不是护栏，是装饰。**已删除**：
   拒绝外推写在 README §3/§6 与 audit 载荷的 `hypothesisNotClaim` 里，
   **不伪装成判据**。

## 5. 两种修法（**产品决定，本批不动 `src/`**）

| 方案 | 改什么 | 代价 |
|---|---|---|
| A. 抬左栏 | 左栏容器 `z-30` → 高于底栏 | 整条左栏会压到时间轴底栏**上方**，时间轴左列 320px 区域将被 rail 盖住 —— 那是 15+ 个控件的宿主 |
| B. 挪 `帮助` | 把 `mt-auto` 改成不贴底（例如 `mb-14`） | 偏离源站节奏；**源站是否也贴底，本批未取证** |

**两条都改变源站已实测过的布局，本批不擅自选。**

## 6. 不声称

- **不声称**源站的 `帮助` 可点或不可点（**未取证**，需要授权）；
- **不声称**方案 A/B 哪个对（§5 是取舍，不是结论）；
- **不声称** 182 与 40 这两个数在所有视口下恒定（本次三格逐格相同，
  但它们来自 145 + 37 的布局常量，未在更多格上验证）；
- **不改 `src/`。**
"""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch681-2026-10-01"

CELLS = [(1280, 720), (1280, 1150), (1920, 1150)]

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

JS = r"""() => {
  const box = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
    return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; };
  const info = (e) => { if (!e) return null; const s = getComputedStyle(e);
    return {box: box(e), z: s.zIndex, pos: s.position, pe: s.pointerEvents,
            cls: (e.getAttribute('class') || '').trim().split(/\s+/).slice(0, 10).join(' ')}; };
  // 容器沿 position 向上走到**第一个非 static 的祖先** —— 可复算的规则，
  // 不是「高度 ≥ 80% 视口」那种碰巧成立的比例阈值。
  const positionedAncestor = (e) => { let n = e;
    while (n && n.parentElement && getComputedStyle(n).position === 'static')
      n = n.parentElement;
    return n; };

  const help = document.querySelector('[data-director-rail-entry="help"]');
  const list = document.querySelector('[data-director-timeline-track-list]');
  const railBox = positionedAncestor(help);
  const barSection = positionedAncestor(list);

  const r = help.getBoundingClientRect();
  const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
  const chain = document.elementsFromPoint(cx, cy).slice(0, 6).map((e) => ({
    tag: e.tagName.toLowerCase(),
    data: e.getAttribute('data-director-rail-entry')
      || e.getAttribute('data-director-timeline-object-row')
      || e.getAttribute('data-director-timeline-track-list') || '-',
    cls: (e.getAttribute('class') || '').trim().split(/\s+/).slice(0, 3).join(' '),
    z: getComputedStyle(e).zIndex, pos: getComputedStyle(e).position,
    box: box(e), isHelp: e === help,
  }));

  const all = Array.from(document.querySelectorAll('[data-director-workspace] *'));
  const chevrons = Array.from(document.querySelectorAll('[aria-label="收起属性"]')).map((e) => {
    const row = e.closest('[data-director-timeline-object-row]');
    return {box: box(e),
            row: row ? row.getAttribute('data-director-timeline-object-row') : '-'};
  });
  return {vw: innerWidth, vh: innerHeight,
          help: info(help), railContainer: info(railBox), barSection: info(barSection),
          trackList: info(list), chevrons, chain,
          domOrder: {iHelp: all.indexOf(help), iList: all.indexOf(list),
                     helpBeforeList: all.indexOf(help) < all.indexOf(list)}};
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

    with sync_playwright() as p:
        br = p.chromium.launch()
        for (w, h) in CELLS:
            page = br.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
            b617.open_desk(page)
            _clean(page)
            cells[f"{w}x{h}"] = page.evaluate(JS)
            page.close()
        br.close()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"stage": "raw-readings", "cells": cells}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    keys = list(cells)
    zs = {k: {"railZ": cells[k]["railContainer"]["z"],
              "barZ": cells[k]["barSection"]["z"],
              "railPos": cells[k]["railContainer"]["pos"],
              "barPos": cells[k]["barSection"]["pos"]} for k in keys}
    geom = {}
    for k in keys:
        hb = cells[k]["help"]["box"]
        bb = cells[k]["barSection"]["box"]
        geom[k] = {"helpBox": hb, "barBox": bb,
                   "helpTopFromBottom": cells[k]["vh"] - hb[1],
                   "barTopFromBottom": cells[k]["vh"] - bb[1],
                   "overlapHeight": max(0, (hb[1] + hb[3]) - bb[1]),
                   "helpFullyInsideBar":
                       bb[1] <= hb[1] and hb[1] + hb[3] <= bb[1] + bb[3]
                       and bb[0] <= hb[0] and hb[0] + hb[2] <= bb[0] + bb[2]}

    v.check("the-rail-is-z-30-and-the-timeline-bottom-bar-is-z-40-in-every-cell",
            all(int(zs[k]["railZ"]) == 30 and int(zs[k]["barZ"]) == 40 for k in keys)
            and zs[keys[0]]["railPos"] == "absolute"
            and zs[keys[0]]["barPos"] == "relative",
            detail={"zAndPosition": zs,
                    "railClass": cells[keys[0]]["railContainer"]["cls"],
                    "barClass": cells[keys[0]]["barSection"]["cls"],
                    "domOrder": {k: cells[k]["domOrder"] for k in keys}},
            note="DOM order puts the rail FIRST — it is the z comparison, not document "
                 "order, that puts the timeline on top")

    v.check("the-geometry-makes-the-overlap-unavoidable-not-a-coincidence",
            all(geom[k]["barTopFromBottom"] == 182
                and geom[k]["helpTopFromBottom"] == 40
                and geom[k]["overlapHeight"] > 0
                and geom[k]["helpFullyInsideBar"] for k in keys),
            detail=geom,
            note="bar height 182 > distance from 帮助's top to the bottom 40, so the two "
                 "always intersect — that is why 680's reading is width- and height-"
                 "independent")

    v.check("the-help-button-does-not-even-reach-the-top-six-of-its-own-hit-chain",
            all(cells[k]["chain"][0]["isHelp"] is False
                and any(c["isHelp"] for c in cells[k]["chain"]) is False
                and cells[k]["chain"][0]["cls"].startswith("group relative")
                for k in keys),
            detail={k: {"chain": [{"tag": c["tag"], "data": c["data"], "z": c["z"],
                                   "box": c["box"], "cls": c["cls"]}
                                  for c in cells[k]["chain"]],
                        "chevrons": cells[k]["chevrons"]} for k in keys},
            note="top of the stack is the timeline's 收起属性 chevron, every cell")

    v.check("the-chevron-that-wins-is-the-camera-main-row-one-and-it-matches-662s-reading",
            all(any(c["box"] == cells[k]["chevrons"][-1]["box"]
                    for c in cells[k]["chain"][:1])
                and cells[k]["chevrons"][-1]["row"] == "director-camera-main"
                for k in keys),
            detail={k: {"chevrons": cells[k]["chevrons"],
                        "topOfChain": cells[k]["chain"][0]} for k in keys},
            note="closes 662/667's in-case onto a named row: "
                 "data-director-timeline-object-row=director-camera-main")

    out = {"cells": keys, "zAndPosition": zs, "geometry": geom,
           "chains": {k: cells[k]["chain"] for k in keys},
           "chevrons": {k: cells[k]["chevrons"] for k in keys},
           "domOrder": {k: cells[k]["domOrder"] for k in keys},
           "sourceFactOnRecord":
               "src/components/director/DirectorTimeline.tsx:1591-1595 records a source "
               "measurement: the source's left column is `z-10 shrink-0 bg-[#1f1f1f]`. "
               "The clone puts that same column inside a `z-40` bottom-bar section while "
               "the rail is `z-30`.",
           "hypothesisNotClaim":
               "IF the source's left column really is z-10 and the source's rail is "
               "higher, then 帮助 is clickable in the source. THIS BATCH TOOK NO SOURCE "
               "EVIDENCE AND CLAIMS NOTHING ABOUT SOURCE BEHAVIOUR. The only source fact "
               "used is the z-10 note already committed to the repo — not a new reading.",
           "productDecision": {
               "A": "raise the rail above the bar (z-30 -> higher): the rail would then "
                     "cover the timeline's 320px left column, which hosts 15+ controls",
               "B": "move 帮助 off the bottom (mt-auto -> e.g. mb-14): departs from the "
                    "source rhythm, and whether the source also pins it to the bottom is "
                    "NOT established by this batch",
               "chosen": None, "note": "product decision — this batch changed no src/"},
           "judged": len(keys)}
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "cells": cells, "checks": v.result},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
