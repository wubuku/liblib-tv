#!/usr/bin/env python3
"""batch 663 验收：竞争面集合的两种口径，以及第三种读法 —— 仪器必须**拒绝作答**

## 起点

626 判「浮层有没有被谁压住」的方式，是拿一份**手写的 6 项面板名单**（`PANELS`）
去代理「谁画在这个浮层之上并与之相交」。手写名单会过期，而本项目已列它为
最后一处已知会过期的手写名单（候选 #6）。

662 刚给了机制上溯的仪器。本批用它派生竞争面集合，并与手写名单逐格比对。

## 一：两种口径在派生集为空的那 27 格上完全一致

11 个浮层 × 3 视口 = 33 格。**30 格**的浮层可命中（27 格派生集为**空**，
3 格非空 —— 见第二节）；另 **3 格**不可命中（见第三节）。
**在派生集为空的那 27 格上，626 的 `structBad` 也是空** ——
手写名单没有多报。**但这是最弱的一种一致**：
一份「短到永远不会触发」的名单和一个正确的名单在空集上长得一模一样，
所以第一节只主张「不多报」，真正的检验在第二节。

## 二：手写名单漏掉的那一个，且它不造成伤亡

`camera-preset-panel` 在 3 个视口上都有一个**真实**的竞争面：
`div.pointer-events-auto.flex.w-full.overflow-x-auto`（48px 高的横滚宿主，
W=1280 时宽 **694** —— 正是 659/660 那条场景提示条的宿主），
压住面板底部 48px。**626 的 6 项名单里没有它，所以 `structBad=0`。**

**但这不改变 626 的判定**：626 自己的 audit 记着该浮层
`liveCount=10 / blocked=[]` —— **重叠带里没有活控件**。
所以这是**归因不全**，不是**漏报缺陷**。本批据此把话说准。

## 三：第 9 个盲区形状 —— 仪器自信地回答它**看不见**的问题

`camera-fov-help-tooltip` 是 `pointer-events:none`（源码 `DirectorInspector.tsx:1621`，
`className` 里明写）。**`pointer-events:none` 的元素永远不会被 `elementsFromPoint`
返回**，无论它画在哪一层。

于是：
* 可命中性读数 `selfHits = 0/25`；
* 第一版派生仪器把「栈里在它前面的所有元素」当成「盖住它的东西」，
  **凭空造出 2–3 个竞争面** —— 而那其实是**「那个位置本来有什么」**。

**独立否证**：那两个「竞争面」是 `data-director-shot-inspector` 与
`data-director-camera-preview` —— 提示条的祖先链上**没有**它们
（祖先是 `section[data-director-inspector][data-director-inspector-kind=camera]`），
它们是同一列的**兄弟 section**，盒与提示条纵向重叠 **65/68px**。
而提示条 `z-index: 1700`、它们是 `auto` / `20` ——
**提示条画在它们之上**，命中栈只是因为跳过它才露出它们。

**所以正确读法是「本仪器测不了」，不是「有 2 个竞争面」。**
仪器因此长出第四种状态（承 656 的 `probe-failed`）：
`measured-empty` / `measured-nonempty` / **`not-measurable`** / `missing`。
**把「测不了」和「量到空集」混为一谈，就是 656 记的「抛错探针被读成否定」的同形错误，
只是方向相反：这次是仪器把「不知道」报成了「知道」。**

## 四、标定

* **阳性**：30 格派生集为空 ⟺ 626 的 `structBad` 为空（两套独立实现）。
* **阴性/拒绝**���3 格 `pointer-events:none` ⟹ 拒绝作答。
* **跨批复现**：本批读的浮层盒与 **626 自己 audit 里的 33 个 `box` 逐位相同**。
* 浮层盒、祖先链、z 值三者在 1920×1150 与 1280×720 上形态一致。

## 本批**不**主张的事

* **零源站断言** —— 源站有没有这个重叠**未取证**，**不改任何 `src/`**。
* **不主张 626 判错了** —— 它的**判定**在 33 格里全对；缺的只是**归因**。
* **不主张**该删掉 626 的 `PANELS` —— **迁移合同而非删除被测行为**：
  本批只**记录**派生集合与那一个洞，不动那份名单。
* **不主张**提示条与兄弟 section 的重叠是缺陷 —— 那是**产品决定**（源站未取证）。
* **不主张** `z-index` 比较能替代命中栈 —— 本批的结论恰恰是**命中栈在
  `pointer-events:none` 上失效**，z 比较只用来**否证**伪造出来的那个集合。
"""
import importlib.util
import json
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch663-2026-10-01"

# GROUND TRUTH, with an explicit refusal state.  elementsFromPoint returns
# topmost-first, so every element at an index below the overlay's own index is
# painted above it.  That reading is meaningless when the overlay cannot be hit
# at all, so the instrument refuses instead of answering.
COMPETITORS_JS = """({sel, hand}) => {
  const el = document.querySelector(sel);
  if (!el) return {state: 'missing'};
  const r = el.getBoundingClientRect();
  if (r.width <= 0 || r.height <= 0) return {state: 'zero-sized'};
  const HAND = new Set(hand);
  const cs = getComputedStyle(el);
  const own = () => {
    for (const at of el.attributes) {
      if (at.name.startsWith('data-director')) {
        return at.value ? at.name + '=' + at.value : at.name;
      }
    }
    return null;
  };
  const describe = (e) => {
    const b = e.getBoundingClientRect();
    const s = getComputedStyle(e);
    const data = Array.from(e.attributes)
      .filter((a) => a.name.startsWith('data-director'))
      .map((a) => a.name + '=' + a.value).join(' ') || null;
    return {tag: e.tagName.toLowerCase(), data: data,
            cls: (e.getAttribute('class') || '').split(' ').filter(Boolean).slice(0, 4).join('.'),
            z: s.zIndex, pos: s.position, pointerEvents: s.pointerEvents,
            rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
            overlapPxY: Math.round(
              Math.min(b.bottom, r.bottom) - Math.max(b.y, r.y)),
            overlapPxX: Math.round(
              Math.min(b.right, r.right) - Math.max(b.x, r.x)),
            inHandList: HAND.has(e)};
  };
  // GATE: can this instrument see the overlay at all?  A pointer-events:none
  // element is never returned by elementsFromPoint, so "what paints above it"
  // is unanswerable -- and answering anyway is worse than not answering.
  let selfHits = 0;
  const stacks = [];
  for (let i = 1; i <= 5; i += 1) for (let j = 1; j <= 5; j += 1) {
    const x = r.x + (r.width * i) / 6, y = r.y + (r.height * j) / 6;
    const st = document.elementsFromPoint(x, y);
    const at = st.indexOf(el);
    if (at >= 0 || st.some((e) => el.contains(e))) selfHits += 1;
    stacks.push({x: Math.round(x), y: Math.round(y), stack: st, at: at});
  }
  const base = {
    overlay: own(), pointerEvents: cs.pointerEvents, z: cs.zIndex, pos: cs.position,
    overlayRect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    selfHits: selfHits, samples: stacks.length,
    hitTestable: selfHits > 0,
  };
  if (selfHits === 0) {
    // REFUSE, and show what the unrefused version would have claimed.
    const above = new Set();
    for (const s of stacks) {
      for (const e of s.stack) {
        if (e === el || el.contains(e) || e.contains(el)) continue;
        above.add(e);
      }
    }
    const raw = Array.from(above);
    const minimal = raw.filter((e) => !raw.some((f) => f !== e && f.contains(e)));
    return Object.assign(base, {state: 'not-measurable',
                                whatTheUnrefusedVersionWouldSay: minimal.map(describe)});
  }
  const above = new Set();
  for (const s of stacks) {
    for (let k = 0; k < (s.at < 0 ? s.stack.length : s.at); k += 1) {
      const e = s.stack[k];
      if (e === el || el.contains(e) || e.contains(el)) continue;
      above.add(e);
    }
  }
  const raw = Array.from(above);
  const minimal = raw.filter((e) => !raw.some((f) => f !== e && f.contains(e)));
  return Object.assign(base, {state: raw.length ? 'measured-nonempty' : 'measured-empty',
                              competitors: minimal.map(describe),
                              rawCount: raw.length});
}"""

# The ancestry leg: for a refuted cell, show that the "competitors" are not
# ancestors, and compare z.
ANCESTRY_JS = """(sel) => {
  const el = document.querySelector(sel);
  if (!el) return {missing: true};
  const chain = [];
  for (let n = el; n && n !== document.body; n = n.parentElement) {
    const d = Array.from(n.attributes)
      .filter((a) => a.name.startsWith('data-director'))
      .map((a) => a.name + '=' + a.value).join(' ') || null;
    if (d) chain.push(d);
  }
  return {ancestorDataChain: chain,
          sections: Array.from(document.querySelectorAll('section[data-director-shot-inspector]'))
            .map((n) => { const b = n.getBoundingClientRect();
              return {data: 'data-director-shot-inspector=true',
                      z: getComputedStyle(n).zIndex,
                      pos: getComputedStyle(n).position,
                      rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width),
                             Math.round(b.height)],
                      containsOverlay: n.contains(el)}; })};
}"""


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / f"scripts/verify-liblib-batch{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


b617 = _load("617")
b626 = _load("626")
HAND = [q for _, q in b626.PANELS]
# one representative per overlay class: the one that has a competitor, the one
# that cannot be measured, and two that agree with the hand list
VIEWPORTS = [(1920, 1150), (1440, 900), (1280, 720)]


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
    ancestry: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        for (vw, vh) in VIEWPORTS:
            for (name, how, sel) in b626.OVERLAYS:
                key = f"{vw}x{vh}/{name}"
                # 626's own precedent: a retry may re-run page setup, never an
                # assertion.  4317 is shared and a cell can time out for
                # infra reasons; without this the run silently loses cells.
                o: dict[str, Any] = {}
                for attempt in (1, 2):
                    page = br.new_page(viewport={"width": vw, "height": vh},
                                       device_scale_factor=1)
                    try:
                        b617.open_desk(page)
                        b626.open_overlay(page, how)
                        _clean(page)
                        o = page.evaluate(COMPETITORS_JS,
                                          {"sel": sel, "hand": HAND})
                        o["handStructBad"] = page.evaluate(
                            b626.CENSUS_JS,
                            {"sel": sel, "panels": b626.PANELS, "live": b626.LIVE,
                             "margin": b626.SAFE_MARGIN}).get("structBad")
                        if o.get("state") == "not-measurable":
                            ancestry[key] = page.evaluate(ANCESTRY_JS, sel)
                    except Exception as exc:                      # noqa: BLE001
                        o = {"state": "error",
                             "error": f"{type(exc).__name__}: {exc}"[:180]}
                    finally:
                        page.close()
                    if o.get("state") != "error":
                        break
                o["attempts"] = attempt
                cells[key] = o
        br.close()

    measured_empty = {k: c for k, c in cells.items()
                      if c.get("state") == "measured-empty"}
    measured_non = {k: c for k, c in cells.items()
                    if c.get("state") == "measured-nonempty"}
    refused = {k: c for k, c in cells.items()
               if c.get("state") == "not-measurable"}
    errored = {k: c for k, c in cells.items() if c.get("state") == "error"}
    states = {k: c.get("state") for k, c in cells.items()}
    # agreement is only meaningful where the derived set is EMPTY: a non-empty
    # set is check 2's subject, not a disagreement of the hand list.
    disagree = {k: c["handStructBad"] for k, c in measured_empty.items()
                if c.get("handStructBad")}

    hand_missed = {k: c for k, c in measured_non.items()
                   if not c["handStructBad"]}

    b626audit = json.loads((ROOT / "docs/research/liblib-canvas-batch626-2026-10-01"
                                  / "runtime-audit.json").read_text(encoding="utf-8"))
    prior_boxes = {f"{r['vw']}x{r['vh']}/{r['overlay']}": r["box"]
                   for r in b626audit["measurements"]}
    box_cmp: dict[str, Any] = {}
    for k, c in cells.items():
        if "overlayRect" in c and k in prior_boxes:
            box_cmp[k] = {"prior626": prior_boxes[k], "here": c["overlayRect"],
                          "same": list(prior_boxes[k]) == list(c["overlayRect"])}
    box_mismatch = {k: b for k, b in box_cmp.items() if not b["same"]}

    # the refutation: the fabricated "competitors" are provably below the overlay
    refutations: dict[str, Any] = {}
    for k, c in refused.items():
        fab = c["whatTheUnrefusedVersionWouldSay"]
        anc = ancestry.get(k, {})
        chain = anc.get("ancestorDataChain", [])
        refutations[k] = {
            "pointerEvents": c["pointerEvents"],
            "selfHits": c["selfHits"], "samples": c["samples"],
            "overlayZ": c["z"], "overlayRect": c["overlayRect"],
            "fabricated": fab,
            "theirZ": [m["z"] for m in fab],
            "anyFabricatedIsAnAncestor": [
                any(m["data"] and m["data"] in chain for m in fab)],
            "ancestorChain": chain,
            "shotInspectors": anc.get("sections", []),
            "verdict": "the fabricated set is the inspector's sibling columns; "
                       "the overlay's z is above theirs and none of them is an "
                       "ancestor, so the set names things the overlay paints over, "
                       "not things that cover it",
        }

    out: dict[str, Any] = {
        "batch": 663,
        "question": "626 judges occlusion with a hand-written 6-item panel list. "
                    "Derive the competitor set from the ground truth instead, and "
                    "see whether the hand list has a hole.",
        "theTwoReadings": {
            "handWritten626": "a global 6-item guess at which panels an overlay "
                              "might compete with, never measured, never "
                              "per-overlay",
            "derived662": "for each overlay, the elements the hit stack puts "
                          "above it at a 5x5 lattice of its own box, reduced to "
                          "an antichain",
        },
        "theRefusalState": {
            "why": "elementsFromPoint never returns a pointer-events:none "
                   "element, so for one the derived set silently degrades into "
                   "'whatever else was at that point'",
            "states": ["missing", "zero-sized", "not-measurable",
                       "measured-empty", "measured-nonempty", "error"],
            "whyItMatters": "reporting a refusal as an empty set would be the "
                            "mirror image of 656's 'a throwing probe read as a "
                            "negative'",
        },
        "counts": {"cells": len(cells), "measuredEmpty": len(measured_empty),
                   "measuredNonEmpty": len(measured_non),
                   "notMeasurable": len(refused), "errored": len(errored),
                   "states": states},
        "agreementWithTheHandList": {
            "rule": "on every cell whose derived set is EMPTY, 626's structBad is "
                    "empty too; the non-empty cells are the hand list's hole and "
                    "are check 2's subject, not a disagreement here",
            "emptyCellsChecked": sorted(measured_empty),
            "disagreements": disagree,
            "erroredCells": errored,
        },
        "handListHole": {
            "cells": sorted(hand_missed),
            "theCompetitor": {k: c["competitors"] for k, c in hand_missed.items()},
            "noCasualty": "626's own audit records liveCount=10 / blocked=[] for "
                          "camera-preset-panel at all three viewports, so the 48px "
                          "overlap band contains no live control: this is an "
                          "attribution gap, not a missed defect",
        },
        "refutations": refutations,
        "crossBatch626Boxes": {"compared": len(box_cmp), "mismatches": box_mismatch},
    }

    # ------------------------------------------------------------------ checks
    v.check("the-hand-list-and-the-derived-set-agree-in-every-measurable-cell",
            not disagree and not errored and len(measured_empty) >= 20
            and len(cells) == 33,
            detail={"cells": len(cells), "measuredEmpty": len(measured_empty),
                    "measuredNonEmpty": len(measured_non),
                    "notMeasurable": len(refused), "errored": len(errored),
                    "erroredCells": errored,
                    "rule": "derived set empty  <=>  626 structBad empty",
                    "emptyCellsChecked": sorted(measured_empty),
                    "disagreements": disagree,
                    "whatThisEstablishes": "626's hand list does not over-report "
                                           "on any cell where the derived set is "
                                           "empty",
                    "honestReading": "agreement on empty answers is weak evidence "
                                     "-- a list that is simply too short to fire "
                                     "looks identical to a correct one.  The next "
                                     "check is the one that bites, and it is why "
                                     "this check does not claim more.",
                    "setupRetry": "626's precedent: a retry may re-run page setup, "
                                  "never an assertion.  4317 is shared and cells "
                                  "can time out for infra reasons."},
            note="agreement on empty sets is the weakest kind of agreement, and it "
                 "is reported as such")

    v.check("the-derived-set-finds-one-competitor-the-hand-list-cannot-name",
            len(hand_missed) == 3
            and all(len(c["competitors"]) == 1 for c in hand_missed.values())
            and all(not any(m["inHandList"] for m in c["competitors"])
                    for c in hand_missed.values()),
            detail={"cells": sorted(hand_missed),
                    "theCompetitor": {k: c["competitors"] for k, c in hand_missed.items()},
                    "handListWouldSay": {k: c["handStructBad"]
                                         for k, c in hand_missed.items()},
                    "theHost": "div.pointer-events-auto.flex.w-full.overflow-x-auto "
                               "-- the 48px horizontal scroll host; at W=1280 it is "
                               "694 wide, which is the same host 659 and 660 "
                               "closed-formed as the scene prompt bar's",
                    "noCasualty": {
                        "from626sAudit": "liveCount=10, blocked=[] at all three "
                                         "viewports",
                        "why": "the 48px overlap band is the panel's padding, so "
                               "the structural gap has no victim",
                        "scoped": "this batch claims an attribution gap, NOT a "
                                  "missed defect"},
                    "what626GotRight": "its verdict. 626 is not wrong in 33 of 33 "
                                       "cells; it is incomplete in its explanation."},
            note="a short list and a correct list look identical until one case "
                 "needs the missing item")

    v.check("a-pointer-events-none-overlay-is-not-measurable-and-the-instrument-says-so",
            len(refused) == 3
            and all(c["pointerEvents"] == "none" for c in refused.values())
            and all(c["selfHits"] == 0 for c in refused.values())
            and all(c["state"] == "not-measurable" for c in refused.values()),
            detail={"cells": sorted(refused),
                    "pointerEvents": {k: c["pointerEvents"] for k, c in refused.items()},
                    "selfHits": {k: f"{c['selfHits']}/{c['samples']}"
                                 for k, c in refused.items()},
                    "states": {k: c["state"] for k, c in refused.items()},
                    "sourceFact": "DirectorInspector.tsx:1621 -- the tooltip's "
                                  "className contains pointer-events-none, and the "
                                  "source comment records that the site treats it "
                                  "as a hover layer",
                    "mechanism": "elementsFromPoint skips pointer-events:none "
                                 "elements entirely, so the overlay is at index -1 "
                                 "in every stack and 'what is above it' degenerates "
                                 "to 'whatever else was at that point'",
                    "theFabricatedAnswer": {k: len(c["whatTheUnrefusedVersionWouldSay"])
                                            for k, c in refused.items()},
                    "priorWork": "639, 641 and 646 all record elementsFromPoint as "
                                 "blind on pointer-events:none.  None of them drew "
                                 "the consequence: an instrument built on it does "
                                 "not fail, it answers."},
            note="the ninth blind-spot shape: an instrument that answers, "
                 "confidently, a question it cannot see")

    v.check("the-fabricated-competitors-are-provably-below-the-overlay",
            all(not any(r["anyFabricatedIsAnAncestor"]) for r in refutations.values())
            and all(all(_znum(r["overlayZ"]) > _znum(z) for z in r["theirZ"])
                        for r in refutations.values()),
            detail=refutations,
            note="an independent route to the same conclusion: z-order, which the "
                 "hit stack could not give us, is what shows the fabricated set is "
                 "upside down")

    v.check("the-overlay-boxes-read-here-match-626s-own-audit-bit-for-bit",
            not box_mismatch and len(box_cmp) == len(cells),
            detail={"compared": len(box_cmp), "cells": len(cells),
                    "mismatches": box_mismatch,
                    "why": "this batch re-opens all 11 overlays at all three "
                           "viewports from scratch, so its boxes are an independent "
                           "re-measurement of 626's",
                    "sample": {k: box_cmp[k] for k in sorted(box_cmp)[:3]}},
            note="the two batches agree before either is compared to a theory")

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "checks": v.result},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


def _znum(z: Any) -> int:
    """z-index as a comparable number; 'auto' is 0, matching 626's own ctxZ."""
    try:
        return int(str(z))
    except (TypeError, ValueError):
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
