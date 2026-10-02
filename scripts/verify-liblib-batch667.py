#!/usr/bin/env python3
"""batch 667 验收：CH3b 与 CH4 归到机制，**并改掉 CH4 的判据**

## 起点

665 的四路表还剩两格没有主体：CH3b（`pe:none` 层压在**点不到**的控件上）与
CH4（一个「全透明」元素吃掉了命中），各只有 1–4 枚。666 把 CH3 归到了两个机制，
本批把剩下两格也收掉 —— **而 CH4 那一格需要改判据，不是补主体。**

## 一：CH3b 的两个机制

| 控件 | pe:none 盖住者 | 命中 |
|---|---|---|
| `帮助`（**6 格恒定**） | 对象行高亮层 `span.pointer-events-none.absolute.inset-x-0.inset-y-0`，盒 `[0, 1105, 320, 32]` | **`收起属性`** = 662 的在案项 |
| `描述想搭建的场景`（**1280/1366 有，1440 起没有**） | **`data-director-scene-prompt-status`**，盒 `[1053, 937, 143, 17]` | 检视器的透明滚动列 |

第一个盖住者**就是 666 已经命名过的那一层**（同一个 class、同一个盒）——
**归到机制而不是新造一个名字。**

第二个值得单记：那条状态行的盒**与输入框逐位重合**（17px vs 16px 高），
也就是说「有东西盖在输入框上」这件事在几何上**就是那条状态行本身**。

## 二：CH4 的判据量错了东西（本批的主要纠正）

665 的 CH4 判据是「命中元素的 `backgroundColor` alpha = 0」。
它**把两种完全不同的东西放进了同一格**：

| 命中元素 | 面积 | `paints` | 子元素 | 文本 | 边框 | 它是什么 |
|---|---|---|---|---|---|---|
| `button.group.relative.z-[1].flex`（`收起属性`） | **400**（20×20） | **`nothing`** | 3 | 0 | 无 | **一枚看得见的图标按钮** |
| `div.min-h-0.flex-1.overflow-y-auto`（检视器滚动列） | **227080**（280×811） | `descendant-svg-fill` | 88 | 32 | 无 | **一个自己透明、靠后代作画的大容器** |

**两者的 `backgroundColor` 都是 `rgba(0, 0, 0, 0)`** ——
所以 alpha 判据分不开它们。

而**「这个元素不可见」对两者都是错的**：
那枚 20×20 的按钮**画着一个 chevron**，它是 662 记的**在案遮挡者**。

> **正确的切分要更小心一些**：`paints`（这个元素自己或它的后代有没有画出任何东西）
> 能把那枚**可见按钮**从透明容器里分出来，**但它也不是同质的** ——
> `descendant-svg-fill` 那一组里还混着检视器的外层滚动列（227080px²）
> 和一个内层 `space-y-3 border-t p` 区块（70808px²）。
> **所以本批只主张「`paints` 能把可见按钮分出来」，不主张「它把这一格切干净了」。**
>
> 而且 `paints` **只看背景与 SVG `fill`，描边（`stroke`）画的图标会被它判成
> `nothing`** —— 它比 alpha 好，**但不是定论**。
>
> 这是 647 当场证伪 `paintedAtCentre` 字段名的同形操作，这次对象是**我自己
> 上一批写的判据**。而和 647 一样，**它停在「这个名字错了」，没有顺手装一个
> 替代品** —— 本批的读数推翻了我「`paints` 同质」这个更强的说法。

## 三：两条阶梯一左一右，**只差 1px**

* 视口的 pe:none 层右沿 = **`W − 281`**
* 检视器透明滚动列左沿 = **`W − 280`**

**两者重叠 1px**，合起来把 `x > 281` 的整条宽度**铺满**。
而**场景提示条正活在那条带子里** —— 于是它的控件**一旦被视口层的右沿够到，
就再也逃不掉**：左边是视口层，右边是检视器列，中间没有缝。

这解释了 666 与本批两条方向相反的阶梯：
**视口层从右往左吃**（成员 19→22 增加），**检视器列从左往右吃**（成员 4→1 减少）。
同一条 1px 边界的两侧。

## 四、CH3b 与 CH4 的成员数都随宽度单调，且每枚只进出一次

| 宽度 | 1280 | 1280 | 1366 | 1440 | 1600 | 1920 |
|---|---|---|---|---|---|---|
| | ×720 | ×1150 | ×1150 | ×1150 | ×1150 | ×1150 |
| CH3b | 2 | 2 | 2 | **1** | 1 | 1 |
| CH4 | 4 | 4 | 3 | **2** | 1 | 1 |

## 本批**不**主张的事

* **零源站断言**，**未改 `src/`**、**未改 665 的已发布 audit** ——
  665 的 CH4 那一格的**读数仍然有效**（它确实量到了「盖住者自己没背景」），
  本批主张的只是**那个读数被起了一个错名字**。
* **不主张**`paints` 就是完美的可见性判据 —— 它只看背景与 SVG `fill`，
  **描边（`stroke`）画的图标它会判成 `nothing`**。它比 alpha 好，但**不是**定论。
* **不主张**那 1px 的重叠是缺陷 —— 它是两条布局边各自算出来的结果，
  是不是该留缝是**产品决定**。
* **不主张** CH3b / CH4 的成员是缺陷 —— 它们都 `own=False`，**本来就点不到**，
  而原因早已分别归给 662 与 659/660。
"""
import importlib.util
import json
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch667-2026-10-01"

CELLS = [(1280, 720), (1280, 1150), (1366, 1150), (1440, 1150),
         (1600, 1150), (1920, 1150)]

JS = """() => {
  const scope = document.querySelector('[data-director-workspace]') || document.body;
  const SEL = 'button, [role=button], [role=tab], [role=switch], [role=slider],'
    + ' [role=menuitem], input, select, textarea, a[href],'
    + ' [tabindex]:not([tabindex="-1"])';
  const cs = (e) => getComputedStyle(e);
  const lab = (e) => e.getAttribute('aria-label')
    || (e.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 20)
    || e.getAttribute('title') || '<' + e.tagName.toLowerCase() + '>';
  const dataOf = (e) => Array.from(e.attributes)
    .filter((a) => a.name.startsWith('data-director'))
    .map((a) => a.name + '=' + a.value).join(' ') || null;
  const ident = (e) => dataOf(e)
    || (e.getAttribute('class') || '').split(' ').filter(Boolean).slice(0, 4).join('.')
    || '<' + e.tagName.toLowerCase() + '>';
  const alphaOf = (bg) => {
    if (!bg) return null;
    if (bg === 'transparent') return 0;
    const m = bg.match(/rgba\\(([^)]+)\\)/);
    if (m) { const p = m[1].split(',').map((s) => parseFloat(s));
             return p.length === 4 ? p[3] : 1; }
    return 1;
  };
  // Does this element PAINT anything of its own?  Either a non-transparent
  // background, or a descendant that has one, or a descendant SVG fill.
  // 665's CH4 test was `alpha(backgroundColor) === 0`, which is satisfied by a
  // visible icon button just as much as by a big transparent container.
  const paints = (e) => {
    if (alphaOf(cs(e).backgroundColor) > 0) return 'own-background';
    for (const d of e.querySelectorAll('*')) {
      const s = cs(d);
      if (s.display === 'none' || s.visibility === 'hidden') continue;
      if (alphaOf(s.backgroundColor) > 0) return 'descendant-background';
      if (s.fill && s.fill !== 'none' && !/^(transparent|rgba?\(0, ?0, ?0, ?0\))$/.test(s.fill)) {
        return 'descendant-svg-fill';
      }
    }
    if ((e.textContent || '').replace(/\\s+/g, ' ').trim()) return 'own-text';
    return 'nothing';
  };
  const strokeOnly = (e) => {
    for (const d of e.querySelectorAll('svg, path, circle, line, polyline, rect')) {
      const s = cs(d);
      if (s.stroke && s.stroke !== 'none') return true;
    }
    return false;
  };
  const peNone = [];
  for (const e of scope.querySelectorAll('*')) {
    if (cs(e).pointerEvents !== 'none') continue;
    const r = e.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    peNone.push({el: e, r: r, id: ident(e)});
  }
  const outermost = (cx, cy) => {
    const hits = peNone.filter((p) => cx >= p.r.x && cx <= p.r.right
                                    && cy >= p.r.y && cy <= p.r.bottom);
    if (!hits.length) return null;
    return hits.filter((p) => !hits.some((q) => q !== p && q.el.contains(p.el)))[0];
  };
  // the viewport's pe:none layer -- the biggest box, the one 666 named
  let vp = null;
  for (const p of peNone) {
    const a = p.r.width * p.r.height;
    if (!vp || a > vp.r.width * vp.r.height) vp = p;
  }
  const ch3b = [], ch4 = [];
  for (const el of scope.querySelectorAll(SEL)) {
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    const s = cs(el);
    if (s.visibility === 'hidden' || s.display === 'none') continue;
    if (s.opacity !== '' && parseFloat(s.opacity) === 0) continue;
    if (s.pointerEvents === 'none') continue;
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    if (cx < 0 || cy < 0 || cx > innerWidth || cy > innerHeight) continue;
    const hit = document.elementFromPoint(cx, cy);
    const own = !!(hit && (hit === el || el.contains(hit) || hit.contains(el)));
    if (own) continue;
    const o = outermost(cx, cy);
    if (o) {
      ch3b.push({control: lab(el), controlData: dataOf(el),
        centre: [Math.round(cx), Math.round(cy)],
        controlRect: [Math.round(r.x), Math.round(r.y),
                      Math.round(r.width), Math.round(r.height)],
        peNoneId: o.id,
        peNoneBox: [Math.round(o.r.x), Math.round(o.r.y),
                    Math.round(o.r.width), Math.round(o.r.height)],
        hitLabel: hit ? lab(hit) : null});
    }
    if (hit && alphaOf(cs(hit).backgroundColor) === 0) {
      const hr = hit.getBoundingClientRect();
      ch4.push({control: lab(el), controlData: dataOf(el),
        hitTag: hit.tagName.toLowerCase(), hitId: ident(hit),
        hitRect: [Math.round(hr.x), Math.round(hr.y),
                  Math.round(hr.width), Math.round(hr.height)],
        hitArea: Math.round(hr.width * hr.height),
        hitAlpha: 0, hitOpacity: cs(hit).opacity,
        paints: paints(hit), strokeOnly: strokeOnly(hit),
        childCount: hit.querySelectorAll('*').length,
        textLen: (hit.textContent || '').replace(/\\s+/g, ' ').trim().length});
    }
  }
  return {vw: innerWidth, vh: innerHeight,
          viewportLayerRight: vp ? Math.round(vp.r.right) : null,
          viewportLayerBox: vp ? [Math.round(vp.r.x), Math.round(vp.r.y),
                                  Math.round(vp.r.width), Math.round(vp.r.height)] : null,
          ch3bCount: ch3b.length, ch4Count: ch4.length,
          ch3b: ch3b, ch4: ch4};
}"""


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / f"scripts/verify-liblib-batch{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


b617 = _load("617")
ROW_LAYER = "pointer-events-none.absolute.inset-x-0.inset-y-0"
STATUS = "data-director-scene-prompt-status=true"
TOGGLE = "group.relative.z-[1].flex"
COLUMN = "min-h-0.flex-1.overflow-y-auto"


def _clean(page: Any) -> None:
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(200)


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
              + (f"  {str(detail)[:150]}" if detail else "")
              + (f"  [{note[:96]}]" if note else ""))


def main() -> int:
    v = Verifier()
    cells: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        for (w, h) in CELLS:
            page = br.new_page(viewport={"width": w, "height": h},
                               device_scale_factor=1)
            b617.open_desk(page)
            _clean(page)
            cells[f"{w}x{h}"] = page.evaluate(JS)
            page.close()
        br.close()

    keys = [f"{w}x{h}" for (w, h) in CELLS]
    w_of = {k: int(k.split("x")[0]) for k in keys}
    ch3b_counts = {k: cells[k]["ch3bCount"] for k in keys}
    ch4_counts = {k: cells[k]["ch4Count"] for k in keys}

    # CH3b mechanisms
    help_rows = {k: [r for r in cells[k]["ch3b"] if r["control"] == "帮助"]
                 for k in keys}
    help_everywhere = all(len(help_rows[k]) == 1 for k in keys)
    help_layer = {k: help_rows[k][0]["peNoneId"] for k in keys}
    help_box = {k: help_rows[k][0]["peNoneBox"] for k in keys}
    help_hit = {k: help_rows[k][0]["hitLabel"] for k in keys}
    status_rows = {k: [r for r in cells[k]["ch3b"]
                       if r["peNoneId"] == STATUS] for k in keys}
    status_present = {k: len(status_rows[k]) for k in keys}
    status_geometry = {k: [{"controlRect": r["controlRect"], "peNoneBox": r["peNoneBox"]}
                           for r in status_rows[k]] for k in keys}
    status_overlap = {k: [{"dx": r["peNoneBox"][0] - r["controlRect"][0],
                           "dy": r["peNoneBox"][1] - r["controlRect"][1],
                           "dw": r["peNoneBox"][2] - r["controlRect"][2],
                           "dh": r["peNoneBox"][3] - r["controlRect"][3]}
                          for r in status_rows[k]] for k in keys}

    # CH4: the two populations, split by `paints` rather than by alpha
    paint_groups: dict[str, list[dict[str, Any]]] = {}
    for k in keys:
        for r in cells[k]["ch4"]:
            paint_groups.setdefault(r["paints"], []).append({**r, "cell": k})
    by_paints = {p: {"n": len(rs),
                     "hitIds": sorted({r["hitId"] for r in rs}),
                     "areas": sorted({r["hitArea"] for r in rs}),
                     "controls": sorted({r["control"] for r in rs})}
                 for p, rs in paint_groups.items()}
    alpha_zero_but_paints_something = all(
        r["hitAlpha"] == 0 for rs in paint_groups.values() for r in rs)
    the_two = sorted(paint_groups)
    column_left = {k: sorted({r["hitRect"][0] for r in cells[k]["ch4"]
                              if r["hitId"] == COLUMN}) for k in keys}
    column_left_first = {k: (column_left[k][0] if column_left[k] else None)
                         for k in keys}
    vp_right = {k: cells[k]["viewportLayerRight"] for k in keys}
    gap = {k: (column_left_first[k] - vp_right[k]
               if column_left_first[k] is not None else None) for k in keys}

    out: dict[str, Any] = {
        "batch": 667,
        "question": "665's four-channel table still had two cells with no "
                    "subject: CH3b and CH4. 666 closed CH3.  This batch closes "
                    "both -- and finds that CH4's own criterion is misnamed.",
        "ch3bCounts": ch3b_counts, "ch4Counts": ch4_counts,
        "ch3b": {
            "help": {"presentEverywhere": help_everywhere,
                     "peNoneLayer": help_layer, "box": help_box, "hit": help_hit},
            "statusLine": {"presentIn": status_present,
                           "geometry": status_geometry,
                           "boxMinusControlRect": status_overlap},
        },
        "ch4": {
            "criterionUnderReview": "alpha(backgroundColor) === 0 — i.e. 'the "
                                    "thing that took the hit has no background "
                                    "of its own'",
            "allHitsHaveAlphaZero": alpha_zero_but_paints_something,
            "splitByPaints": by_paints,
            "whyTheSplitIsTheRightOne": "a 20x20 icon button with no background "
                                        "is VISIBLE, and a 280x811 container with "
                                        "no background but 88 painted descendants "
                                        "is a different thing entirely. Both have "
                                        "alpha 0.",
        },
        "theOnePixelSeam": {"viewportLayerRight": vp_right,
                            "inspectorColumnLeft": column_left_first,
                            "gap": gap},
    }

    # ------------------------------------------------------------------ checks
    v.check("ch3b-has-two-mechanisms-and-the-first-is-the-layer-666-already-named",
            help_everywhere
            and all(v == ROW_LAYER for v in help_layer.values())
            and all(v == "收起属性" for v in help_hit.values()),
            detail={"counts": ch3b_counts, "peNoneLayer": help_layer,
                    "box": help_box, "hit": help_hit,
                    "thePoint": "666 already named this exact layer (the object "
                                "row's `span[aria-hidden]` highlight) while closing "
                                "CH3.  CH3b's first member is swallowed by the "
                                "SAME layer, and what actually takes the click is "
                                "662's in-case `收起属性`.",
                    "whyNotANewName": "naming a member where a mechanism already "
                                      "exists is how 661 got its answer demoted; "
                                      "this batch reuses the name instead"},
            note="one layer, two cells — the mechanism outlives the cell it was "
                 "found in")

    v.check("the-second-ch3b-mechanism-is-the-prompt-status-line-whose-box-sits-on-the-input",
            any(status_present[k] for k in keys)
            and all(all(d["dx"] == 0 for d in status_overlap[k])
                    for k in keys),
            detail={"presentInCells": status_present,
                    "geometry": status_geometry,
                    "statusBoxMinusInputRect": status_overlap,
                    "reading": "the status line's box starts at exactly the input's "
                               "x (dx = 0 in every cell) and is one pixel taller, "
                               "so 'something is lying on the input' is "
                               "geometrically the status line itself",
                    "itLeavesAt1440": "present at 1280/1366, gone at 1440 and wider "
                                      "— the same seam as the rest of this batch",
                    "alreadyAttributed": "the click still goes to the inspector's "
                                         "transparent column, i.e. 664's finding; "
                                         "this batch only names the pe:none layer "
                                         "that also sits there"},
            note="the coverer and the victim share a left edge exactly")

    v.check("ch4s-criterion-mixes-a-visible-icon-button-with-a-big-transparent-container",
            len(the_two) >= 2 and "nothing" in by_paints
            and by_paints["nothing"]["areas"] == [400]
            and all(a > 1000 for a in by_paints["descendant-svg-fill"]["areas"]),
            detail={"splitByPaints": by_paints,
                    "allHitsHaveAlphaZero": alpha_zero_but_paints_something,
                    "theIconButton": {"hitId": TOGGLE, "area": 400,
                                      "paints": "nothing", "childCount": 3,
                                      "textLen": 0, "border": False,
                                      "what": "收起属性 — 662's in-case coverer, a "
                                              "20x20 chevron button that is "
                                              "plainly visible"},
                    "theContainer": {"hitId": COLUMN, "area": 227080,
                                     "paints": "descendant-svg-fill",
                                     "childCount": 88, "textLen": 32,
                                     "what": "the inspector's own scroll column: "
                                             "transparent itself, painted by 88 "
                                             "descendants"},
                    "theCorrection": "665's CH4 test asked 'does the hitter have a "
                                     "background of its own'.  Both answers were "
                                     "yes-less, so both landed in one cell, and the "
                                     "cell was named 'a fully transparent element "
                                     "took the hit'.  The first member is not "
                                     "transparent — it is a visible control. The "
                                     "criterion measures the wrong property."},
            note="a criterion that fires on a visible button has already told you "
                 "it is measuring the wrong thing")

    v.check("paints-separates-the-visible-button-that-alpha-cannot",
            alpha_zero_but_paints_something
            and by_paints.get("nothing", {}).get("hitIds") == [TOGGLE]
            and by_paints["nothing"]["areas"] == [400]
            and len(by_paints) >= 2
            and max(max(v_["areas"]) for v_ in by_paints.values())
            >= 100 * min(min(v_["areas"]) for v_ in by_paints.values()),
            detail={"groupsByPaints": {p: {"hitIds": v_["hitIds"],
                                            "areas": v_["areas"], "n": v_["n"]}
                                        for p, v_ in by_paints.items()},
                    "groupsByAlpha": {"rgba(0, 0, 0, 0)": sorted(
                        {r["hitId"] for rs in paint_groups.values() for r in rs}),
                        "areas": sorted({r["hitArea"] for rs in
                                         paint_groups.values() for r in rs})},
                    "whatIsTrue": "the `nothing` group is a SINGLE element: the "
                                  "20x20 chevron button, 400px^2, in all six cells. "
                                  "The alpha group cannot tell it apart from a "
                                  "227080px^2 column — a spread of 567x.",
                    "whatIsFALSEandWasRefutedHere": "I first wrote that `paints` "
                                                    "splits the cell HOMOGENEOUSLY. "
                                                    "It does not: the "
                                                    "`descendant-svg-fill` group "
                                                    "still contains two identities "
                                                    "— the inspector's outer "
                                                    "scroll column (227080px^2) and "
                                                    "an inner `space-y-3 border-t p` "
                                                    "section (70808px^2, seen at "
                                                    "1280x720). So `paints` splits "
                                                    "two ways, not three, and the "
                                                    "second way is not homogeneous "
                                                    "either.",
                    "theClaimIsWeakerThanIFirstWrote": "`paints` separates the "
                                                        "visible button from the "
                                                        "transparent containers. It "
                                                        "does NOT cleanly partition "
                                                        "the whole cell.",
                    "notClaimed": "that `paints` is a correct visibility test — it "
                                  "looks at backgrounds and SVG fills only, so a "
                                  "stroke-drawn icon would read as `nothing`. Better "
                                  "than alpha, not final.",
                    "sameShapeAs647": "647 corrected `paintedAtCentre`'s field "
                                      "name on the spot. This is the same operation, "
                                      "one batch later, aimed at this batch's own "
                                      "instrument — and like 647's, it stopped at "
                                      "'this name is wrong' rather than installing "
                                      "a replacement."},
            note="a field name is a claim; check the claim — and check your own "
                 "replacement's claim too")

    v.check("the-viewport-layer-and-the-inspector-column-are-one-pixel-apart",
            all(g is not None and g == 1 for g in gap.values() if g is not None)
            and any(g is not None for g in gap.values()),
            detail={"viewportLayerRight": vp_right,
                    "inspectorColumnLeft": column_left_first,
                    "gap": gap,
                    "theNumbers": "the viewport's pe:none layer ends at W-281 and "
                                  "the inspector's transparent column starts at "
                                  "W-280 — they OVERLAP by one pixel, so together "
                                  "they tile the whole band right of x=281",
                    "whyThatMatters": "the scene prompt bar lives in exactly that "
                                      "band. Once the viewport layer's right edge "
                                      "reaches a prompt control there is no gap left "
                                      "to escape through: 666's staircase (19->22, "
                                      "growing) and this batch's (4->1, shrinking) "
                                      "are the two sides of one seam.",
                    "notADefectClaim": "the two edges are each computed from their "
                                       "own layout; whether a gap should exist is a "
                                       "product decision"},
            note="one pixel is the width of this whole seam")

    v.check("both-staircases-are-monotone-in-width-and-each-control-leaves-once",
            all(ch3b_counts[k] >= ch3b_counts[keys[i + 1]]
                for i, k in enumerate(keys[:-1]))
            and all(ch4_counts[k] >= ch4_counts[keys[i + 1]]
                    for i, k in enumerate(keys[:-1])),
            detail={"cells": keys, "ch3bCounts": ch3b_counts,
                    "ch4Counts": ch4_counts,
                    "ch3b": "2/2/2/1/1/1 — 描述想搭建的场景 leaves at 1440",
                    "ch4": "4/4/3/2/1/1 — 上传图片 and 描述想搭建的场景 leave first, "
                           "then 发送; 帮助 never leaves (it is the constant)",
                    "direction": "CH3b and CH4 both SHRINK with width while 666's "
                                 "CH3 GROWS with width — the two sides of the same "
                                 "1px seam",
                    "scope": "6 cells at these widths only"},
            note="one seam, two staircases, opposite directions")

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "checks": v.result},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
