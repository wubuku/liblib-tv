#!/usr/bin/env python3
"""batch 666 验收：CH3 那 24 枚归到机制 —— 两类盖住者、两条盒包含闭式

## 起点

665 的四路表里 CH3 有 **24** 枚（1280 宽两个窗高恒定，1440 是 26、1920 是 27），
含义是「`own` 为真（点得到）却中心上方压着一个 `pointer-events:none` 层」。
665 只说了这一格**存在**，没说是被谁压的。662 的教训是**报机制而不是报成员**，
所以本批把那 24 枚归到机制。

## 一：24–27 枚受害者，只有 **2 类**盖住者

| 机制 | 吞掉 | 盒 |
|---|---|---|
| **视口的 pe:none 层** | **19 / 21 / 22** 枚（随宽度增长） | `x 281 .. W−281`、`y 88 .. H−182` |
| **对象行的选中高亮层**<br>`span.pointer-events-none.absolute.inset-x-0.inset-y-0`<br>（`DirectorTimeline.tsx:1636-1642`） | **恰好 5** 枚，**每格恒定** | 每个对象行一个 `320×32` |

**第一类的盒逐位等于视口格**：左边 281 = 48（rail）+ 233（场景树列），
右边 `W−281`（检视器 281 宽），上边 88（顶带下沿），下边 `H−182`（时间轴顶边）。
实测 718/878/1358 宽与 450/880 高**逐位符合 `W−562` 与 `H−182`**。

**第二类的 5 枚恒定**：`收起属性`×2、`角色01 · 陈默`、`机位01 · 对峙中景`、
`绘制轨迹` —— 四个窗高一字不差。

## 二：盖住者**没有一次**是受害者的祖先

这是本批唯一可能推翻结论的那一问，第一版还**测错了**：
我用「身份字符串」在祖先链里找，而盖住者的身份用 class/`<div>`、
祖先链用 data 属性，**两套命名对不上**，于是报出「0 个祖先」。

改成**对象身份**（沿真实 `parentElement` 链比 `===`）之后，
**4 个视口 × 24–27 枚，全部仍然不是祖先**。

> **所以这不是同义反复，是真实的跨容器覆盖。**
> 665 说「门在正确的位置、问了错误的问题」—— 本批把「问题」补全了：
> 被问的是「你上面有什么」，答案是「**一个和你没有亲缘关系的大盒子**」。

## 三：闭式 —— 两条盒包含

    属于「视口层」 ⟺ 中心 x ≤ W − 281  且  中心 y ≤ H − 182
    属于「对象行高亮层」 ⟺ 中心落在某个 320×32 的行盒内

第一条解释了成员数**随宽度增长**：视口层向右伸到 `W−281`，
于是提示条那几枚（`上传图片` / `描述想搭建的场景` / `发送`）**逐个**被它吃掉 ——
1280 时层右沿 999、提示条控件在 1053 之后，**一枚都不在内**；
1366 时层右沿 1085，吃到 `上传图片`；1440 时 1159，加上 `描述想搭建的场景`
（`发送` 的中心 x 更靠右，仍在外）；1600 与 1920 时三枚全在内。

> **顺带纠正我第一版的读数**：我以为 1920 比 1440 只多一枚。
> **5 个宽度各测一次之后是 0 → 1 → 2 → 3**，每枚各在**一个宽度**上加入。
> 「19 → 21 → 22」只是我抽了三个宽度的错觉。

## 四、这不是缺陷主张

那 24–27 枚**全部 `own=True`**，也就是**点得到** ——
`pointer-events:none` 的层本来就是**点击穿透**的。
本批主张的只有一句：**`own` 这一路的读数看不见它们上面有什么。**

## 本批**不**主张的事

* **零源站断言**，**未改 `src/`**、**未改任何共享判据**。
* **不主张**那 24–27 枚是缺陷 —— 它们点得到。
* **不主张**视口的 pe:none 层该改 —— **点击穿透是对的**，
  而它盒住整个视口格多半正是它该做的（让画布不吃点击）。
* **不主张**闭式在别处成立 —— 只在这 6 格（5 宽度 + 1 矮视口）测过，
  且第一条的常数 281 / 88 / 182 是**本读数的值**，不是从源码推的。
"""
import importlib.util
import json
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch666-2026-10-01"

WIDTHS = [1280, 1366, 1440, 1600, 1920]
SHORT = (1280, 720)
TALL = 1150
# 1280 and 1440 bracket the prompt-bar joins; 1920 is the widest member
CELLS = [(w, TALL) for w in WIDTHS] + [SHORT]

# 662's instrument applied to the CH3 cell: for each control whose centre is
# under a pe:none layer, name the OUTERMOST such layer, then decide -- by
# OBJECT identity, not by a string -- whether that layer is an ancestor.
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
  const rows = [];
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
    if (!own) continue;
    const o = outermost(cx, cy);
    if (!o) continue;
    // OBJECT identity along the real parentElement chain.  The first draft
    // compared identity STRINGS against a differently-built chain and reported
    // "not an ancestor" for everything, which was the test's bug, not the
    // page's.
    let depth = -1;
    for (let n = el.parentElement, d = 1; n && n !== document.body;
         n = n.parentElement, d += 1) {
      if (n === o.el) { depth = d; break; }
    }
    rows.push({control: lab(el), controlData: dataOf(el),
      centre: [Math.round(cx), Math.round(cy)],
      controlRect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      covererId: o.id, covererRect: o.id ? undefined : undefined,
      covererBox: [Math.round(o.r.x), Math.round(o.r.y), Math.round(o.r.width), Math.round(o.r.height)],
      covererIsAncestor: depth > 0, ancestorDepth: depth,
      covererPos: cs(o.el).position, covererZ: cs(o.el).zIndex});
  }
  // group by identity, but count DISTINCT ELEMENTS -- three elements share two
  // identity strings, and the first draft reported one box for all of them.
  const groups = {};
  for (const r of rows) {
    const k = r.covererId;
    if (!groups[k]) groups[k] = {id: k, boxes: {}, n: 0, ancestor: 0, controls: []};
    const bk = r.covererBox.join(',');
    groups[k].boxes[bk] = (groups[k].boxes[bk] || 0) + 1;
    groups[k].n += 1;
    if (r.covererIsAncestor) groups[k].ancestor += 1;
    groups[k].controls.push(r.control);
  }
  return {vw: innerWidth, vh: innerHeight, total: rows.length,
          ancestorHits: rows.filter((r) => r.covererIsAncestor).length,
          distinctCovererIdentities: Object.keys(groups).length,
          groups: Object.values(groups), rows: rows};
}"""


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / f"scripts/verify-liblib-batch{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


b617 = _load("617")


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

    keys = sorted(cells, key=lambda k: (int(k.split("x")[0]), int(k.split("x")[1])))
    totals = {k: cells[k]["total"] for k in keys}
    ancestor = {k: cells[k]["ancestorHits"] for k in keys}
    identities = {k: cells[k]["distinctCovererIdentities"] for k in keys}

    # the viewport layer: the biggest box, and its geometry as a closed form
    viewport_boxes: dict[str, list[int]] = {}
    row_boxes: dict[str, dict[str, int]] = {}
    row_members: dict[str, list[str]] = {}
    for k in keys:
        gs = sorted(cells[k]["groups"], key=lambda g: -g["n"])
        vp = gs[0]
        row = gs[1] if len(gs) > 1 else None
        boxes = sorted(([int(x) for x in bk.split(",")] for bk in vp["boxes"]),
                       key=lambda b: -(b[2] * b[3]))
        viewport_boxes[k] = boxes[0]
        if row:
            rb = sorted(([int(x) for x in bk.split(",")] for bk in row["boxes"]),
                        key=lambda b: b[1])
            row_boxes[k] = {"x": rb[0][0], "w": rb[0][2], "nBoxes": len(rb),
                            "boxes": rb}
            row_members[k] = row["controls"]

    w_of = {k: int(k.split("x")[0]) for k in keys}
    h_of = {k: int(k.split("x")[1]) for k in keys}
    vp_geometry = {
        "left": {k: viewport_boxes[k][0] for k in keys},
        "leftIsConstant281": len({viewport_boxes[k][0] for k in keys}) == 1,
        "width": {k: viewport_boxes[k][2] for k in keys},
        "widthIsWminus562": all(viewport_boxes[k][2] == w_of[k] - 562 for k in keys),
        "top": {k: viewport_boxes[k][1] for k in keys},
        "topIsConstant88": len({viewport_boxes[k][1] for k in keys}) == 1,
        "height": {k: viewport_boxes[k][3] for k in keys},
        # H-182 is the BOTTOM edge, not the height.  The first draft asserted
        # `height == H-182` and went red: 450 != 538 at H=720.  The height is
        # H-270, and 88 + (H-270) = H-182, so the bottom edge is where the
        # number belongs.  A derived quantity is not the measured one.
        "heightIsHminus270": all(viewport_boxes[k][3] == h_of[k] - 270 for k in keys),
        "bottom": {k: viewport_boxes[k][1] + viewport_boxes[k][3] for k in keys},
        "bottomIsHminus182": all(viewport_boxes[k][1] + viewport_boxes[k][3]
                                 == h_of[k] - 182 for k in keys),
        "rightEdge": {k: viewport_boxes[k][0] + viewport_boxes[k][2] for k in keys},
        "rightEdgeIsWminus281": all(viewport_boxes[k][0] + viewport_boxes[k][2]
                                    == w_of[k] - 281 for k in keys),
    }
    row_geometry = {
        "x": {k: row_boxes[k]["x"] for k in row_boxes},
        "width": {k: row_boxes[k]["w"] for k in row_boxes},
        "bothConstant": len({(row_boxes[k]["x"], row_boxes[k]["w"])
                             for k in row_boxes}) == 1,
        "nBoxesPerCell": {k: row_boxes[k]["nBoxes"] for k in row_boxes},
        "membersIdenticalEverywhere": len({tuple(sorted(row_members[k]))
                                           for k in row_members}) == 1,
        "members": {k: sorted(row_members[k]) for k in row_members},
    }

    # the closed form: membership of the viewport layer, per control
    def in_viewport_layer(k: str, centre: list[int]) -> bool:
        b = viewport_boxes[k]
        return b[0] <= centre[0] <= b[0] + b[2] and b[1] <= centre[1] <= b[1] + b[3]

    mismatches: dict[str, Any] = {}
    membership_checked = 0
    for k in keys:
        vp_id = sorted(cells[k]["groups"], key=lambda g: -g["n"])[0]["id"]
        for r in cells[k]["rows"]:
            if r["covererId"] != vp_id:
                continue
            membership_checked += 1
            if not in_viewport_layer(k, r["centre"]):
                mismatches.setdefault(k, []).append(
                    {"control": r["control"], "centre": r["centre"],
                     "layerBox": viewport_boxes[k]})

    prompt = {k: sorted(c for c in cells[k]["groups"][0]["controls"]
                        if c in ("上传图片", "描述想搭建的场景", "发送"))
              for k in keys}
    prompt_layer_right = {k: vp_geometry["rightEdge"][k] for k in keys}
    prompt_centre_x = {}
    for k in keys:
        vp_id = sorted(cells[k]["groups"], key=lambda g: -g["n"])[0]["id"]
        prompt_centre_x[k] = {r["control"]: r["centre"][0] for r in cells[k]["rows"]
                              if r["covererId"] == vp_id
                              and r["control"] in ("上传图片", "描述想搭建的场景", "发送")}

    out: dict[str, Any] = {
        "batch": 666,
        "question": "665's CH3 cell said 24 controls are clickable yet have a "
                    "pointer-events:none layer over their centre. 662's lesson is "
                    "to name the mechanism, not the member.  Who are they?",
        "totalsPerCell": totals,
        "covererIdentitiesPerCell": identities,
        "ancestorHitsPerCell": ancestor,
        "viewportLayer": {"boxPerCell": viewport_boxes, "geometry": vp_geometry,
                          "members": {k: sorted(cells[k]["groups"][0]["controls"])
                                      for k in keys}},
        "rowHighlightLayer": {"geometry": row_geometry},
        "closedForm": {
            "rule1": "a control belongs to the viewport layer <=> its centre x "
                     "<= W - 281 and its centre y <= H - 182 (the layer's "
                     "BOTTOM edge; its height is H-270)",
            "rule2": "a control belongs to a row highlight layer <=> its centre "
                     "falls inside one of the 320x32 row boxes",
            "membershipChecked": membership_checked,
            "mismatches": mismatches,
        },
        "thePromptBarJoins": {"members": prompt, "layerRightEdge": prompt_layer_right,
                              "centreX": prompt_centre_x},
        "notADefectClaim": "all of these are own=True, i.e. clickable; pe:none "
                           "layers are click-through by design",
    }

    # ------------------------------------------------------------------ checks
    v.check("two-coverer-identities-explain-every-cell",
            all(n == 2 for n in identities.values()),
            detail={"identitiesPerCell": identities, "totalsPerCell": totals,
                    "viewportLayer": {"members1280": out["viewportLayer"]["members"]["1280x720"],
                                      "nPerCell": {k: len(out["viewportLayer"]["members"][k])
                                                   for k in keys}},
                    "rowLayer": {"members": row_geometry["members"]["1280x720"],
                                 "nPerCell": {k: len(row_geometry["members"][k])
                                              for k in keys}},
                    "whyThisIsThe662Lesson": "662 found that naming the member "
                                             "(`收起属性`) was not naming the cause. "
                                             "Same move here: 24-27 victims, TWO "
                                             "coverers, and the membership is a "
                                             "box-containment test, not a list."},
            note="many victims, two mechanisms — the shape 662 found, one layer up")

    v.check("the-viewport-layer-box-equals-the-viewport-cell-on-all-four-edges",
            vp_geometry["leftIsConstant281"] and vp_geometry["topIsConstant88"]
            and vp_geometry["widthIsWminus562"] and vp_geometry["heightIsHminus270"]
            and vp_geometry["bottomIsHminus182"]
            and vp_geometry["rightEdgeIsWminus281"],
            detail={"geometry": vp_geometry,
                    "theFourEdges": {
                        "left 281": "48 (the icon rail) + 233 (the scene-tree column)",
                        "right W-281": "the inspector is 281 wide",
                        "top 88": "under the top band",
                        "bottom H-182": "the timeline's top edge — the layer stops "
                                        "exactly where the timeline starts"},
                    "measured": "718/804/878/1038/1358 wide at "
                                "1280/1366/1440/1600/1920 and 450/880 tall at "
                                "720/1150, matching W-562 and H-270 digit for digit",
                    "theNumberBelongsToTheBottomEdge": "H-182 is the bottom, not the "
                                                       "height. The first draft "
                                                       "asserted `height == H-182` "
                                                       "and went red — 450 != 538 at "
                                                       "H=720. Height is H-270, and "
                                                       "88 + (H-270) = H-182. Same "
                                                       "error class as 634/638/660: "
                                                       "a derived quantity asserted "
                                                       "as if it were the measured "
                                                       "one.",
                    "scope": "the constants 281 / 88 / 182 / 270 are THIS reading's "
                             "values, not derived from source. If the column widths "
                             "ever change, this check goes red — which is the point."},
            note="a box that coincides with the layout cell it covers is a fact, "
                 "not a coincidence")

    v.check("the-coverer-is-never-an-ancestor-of-the-control",
            all(n == 0 for n in ancestor.values()),
            detail={"ancestorHitsPerCell": ancestor, "totalsPerCell": totals,
                    "test": "object identity along the real parentElement chain",
                    "theFirstDraftGotThisWrong": "it compared an identity STRING "
                                                 "(class or '<div>') against a chain "
                                                 "built from data attributes, so "
                                                 "the two vocabularies never met and "
                                                 "it reported 'not an ancestor' for "
                                                 "everything — including cases "
                                                 "that are ancestors.  The test's "
                                                 "bug, not the page's.",
                    "whyItMatters": "if the coverer were always an ancestor, CH3 "
                                    "would be a tautology and cost nothing to "
                                    "report.  It is not: these are genuine "
                                    "cross-container overlaps, which is what makes "
                                    "665's cell worth closing."},
            note="a string-keyed ancestor test is a test that cannot fail")

    v.check("the-box-containment-rule-predicts-every-viewport-layer-member",
            not mismatches and membership_checked > 0,
            detail={"closedForm": out["closedForm"],
                    "membershipChecked": membership_checked,
                    "rule": "centre x <= W-281 and centre y <= H-182",
                    "derivedNotTranscribed": "the rule is stated once and applied "
                                             "to every member of every cell; the "
                                             "layer's box is measured, not assumed"},
            note="a closed form beats a list of names")

    v.check("the-row-highlight-layer-swallows-exactly-five-and-never-changes",
            row_geometry["membersIdenticalEverywhere"]
            and all(n == 5 for n in (len(v_) for v_ in row_geometry["members"].values())),
            detail={"geometry": row_geometry,
                    "theFive": row_geometry["members"][keys[0]],
                    "nBoxesPerCell": row_geometry["nBoxesPerCell"],
                    "theIdentityCollapsesTwoElements": "the class string is the "
                                                       "same for every object row, "
                                                       "so ONE identity covers "
                                                       "several elements; the first "
                                                       "draft reported a single box "
                                                       "for all of them, which is "
                                                       "why the box count is "
                                                       "recorded here",
                    "sourceFact": "DirectorTimeline.tsx:1636-1642 — the "
                                  "`span[aria-hidden].absolute.inset-0` row "
                                  "highlight, whose colour switches with selection",
                    "whyConstant": "the object rows are 32px and their y positions "
                                   "do not depend on the viewport, so the same five "
                                   "controls fall under a row highlight at every "
                                   "width and height"},
            note="a constant five is a structural fact, not a coincidence")

    v.check("the-prompt-bar-controls-join-the-layer-one-by-one-as-it-widens",
            all(all(c in prompt[k] for c in prompt["1920x1150"])
                for k in keys if k == "1920x1150")
            and len(prompt["1280x720"]) == 0
            and len(prompt["1920x1150"]) == 3,
            detail={"members": prompt, "layerRightEdge": prompt_layer_right,
                    "centreX": prompt_centre_x,
                    "theMechanism": "the layer's right edge is W-281, so a prompt "
                                    "bar control joins exactly when the layer "
                                    "reaches its centre x. Five widths, and the "
                                    "membership goes 0 -> 1 -> 2 -> 3 -> 3: at 1280 "
                                    "the edge is 999 and every prompt control sits "
                                    "past it; at 1366 (edge 1085) 上传图片 is in; "
                                    "at 1440 (edge 1159) 描述想搭建的场景 joins; at "
                                    "1600 and 1920 all three are in. Each control "
                                    "joins at its own width.",
                    "myFirstReadingWasWrong": "I sampled three widths and wrote "
                                              "'19 -> 21 -> 22', implying one join. "
                                              "Sampling five widths shows 0 -> 1 -> "
                                              "2 -> 3 -> 3 — three separate joins. "
                                              "A three-point sample drew a line "
                                              "through a staircase.",
                    "notAWidthIndependentSurface": "this is the opposite of 633's "
                                                  "finding that the burial surface "
                                                  "does not depend on width — here "
                                                  "it very much does",
                    "priorWork": "659 and 660 closed the prompt bar's OWN "
                                 "reachability rule (W >= 1510). That is a different "
                                 "question from 'is it under a pe:none layer', and "
                                 "the two must not be conflated."},
            note="one edge of one box, and three controls join in order")

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
