#!/usr/bin/env python3
"""batch 665 验收：四路判据交叉表 + 617 普查的 6 道静默 `continue` 逐条归因

## 起点

639 挂了两年的下一批候选第 1 条是「绘制类读数与命中类读数的一致率表」。
664 刚把 22 个 `pointer-events:none` 元素交出来，说它们是两种读法分歧的
**下界样本**。本批做那张表，并且在做的过程中发现了一件更靠底的事。

## 一：盲区的位置不在「测量」里，在「纳入」里

664 普查的是**测量调用**（`elementFromPoint` / `elementsFromPoint`），
结论是 26 个调用点、只有 1 台能拒绝。
**它没有普查纳入过滤** —— 而第三态塌缩在共享判据里正是**那一行**：

    src 侧无关，判据侧 `scripts/verify-liblib-batch617.py:282`
    if (s.pointerEvents === 'none') continue;

**普查连 `pe:none` 的控件都不枚举。** 那不是「仪器答错」，
是「这个控件在我们的账本上不存在」。

664 与本批合起来才把这条路径找全：**664 找到仪器端，本批找到纳入端。**

## 二：6 道门逐条归因 —— 而 L282 一次都没触发

抄 617 的 `inScope` / `isFlow` / `isScrim` 与 6 道 `continue`（逐行号），
对**每一个**控件记录它被哪一道拦下（而不是让它静默消失）：

| 门 | 判据 | 拦下 |
|---|---|---|
| L276 | `!inScope(el) \|\| isFlow(el)` | **60**（画布页顶栏：项目菜单 / 工作区名称 / 画布 2 …） |
| L278 | `b[2] <= 0 \|\| b[3] <= 0` | **4**（623 在案的零尺寸族） |
| L280 | `visibility:hidden / display:none` | **0** |
| L281 | `opacity === 0` | **2** |
| **L282** | **`pointerEvents === 'none'`** | **0** |
| L285 | `isScrim(el)` | **0** |

196 个原始控件 → 保留 **130**，与 617 自己报的 `total=130` **逐位相同**（两个窗高）。
**抄写的忠实性是被证明的，不是被声称的。**

**L282 = 0 是一个量到的零，而且它有作用域**：导演台**自己的控件**里没有
`pe:none` 的。所以第三态塌缩在这个页面的**纳入端**不发生。

## 三：但盲区在门外 —— 而 L282 对它**结构上无法发言**

那道门只测**控件自己**的 `pointer-events`。而 664 那 22 个元素造成的损害是
**别的 `pe:none` 元素压在控件上方**：

    25 枚控件：own = True（点得到），中心上方却盖着 pe:none 层

这 25 枚里有 gizmo 的六枚轴按钮、`重置视角`、以及底栏那一整排。
**L282 对此一句话都说不出来 —— 它问的不是这个问题。**

## 四：四路交叉表，三个窗高**逐格相同**

196 个原始控件 → 6 道门留下 **130**（= 617 自己报的 `total`）。
130 枚按四路读数分类：

| 格 | 含义 | 数量 |
|---|---|---|
| 92 | 四路一致（干净） | |
| **24** | **CH3 可命中性**：`own` 为真但上方压着 `pe:none` 层 | |
| 10 | 视口外 | |
| 2 | CH3b：`pe:none` 层压在**点不到**的控件上 | |
| 2 | CH4 透明性：一个**全透明**元素吃掉了命中 | |
| **0** | **CH1 裁剪**：`own` 为真但不在命中栈里 | |
| **0** | **CH2 合成**：祖先 `opacity < 1` | |

720 / 900 / 1150 **逐格相同**（`own`/`painted` 两路在本页从不打架）。

**CH1 = 0 是有原因的**：646 找到的那一族（被自己的滚动容器裁掉）
在**画布页**的 1020px 工具条上，**不在导演台**。

**CH2 = 0 更有意思**：不带门跑的时候它是 **1**，而那一格**就是
`data-director-timelineZoom` 本身** —— 一枚 `opacity:0` 的控件。
**合成通道在本页唯一的成员，被它自己描述的那条通道（`opacity`）丢掉了。**
一个通道会举报自己的唯一证人。

（不带门跑时 CH3 是 25 而非 24，多的那一枚同样是 `时间轴缩放`。）

## 五：L281 静默丢掉的 2 枚里，有一枚 658 算进了缺陷

`opacity:0` 被 L281 丢掉的两枚是：

* `data-directorScenePromptFile` —— **1×1** 的 `sr-only` 文件输入；
* `data-directorTimelineZoom` —— 时间轴缩放。

**而 658 的 `occludedKeys` 里正有 `data-director-scene-prompt-file|`** ——
658 把它算成「4 枚不可达的提示条控件」之一，**617 的普查根本枚举不到它**。

所以：**两个普查对「它存不存在」意见不一致，而两边的账本都没说这件事。**
659/660 给提示条收的闭式（中心落在裁剪盒内）是对**可见**控件说的；
那枚文件输入是 1×1 且 `opacity:0`，**用户看不见也点不到**，
但文件选择**仍可由脚本触发**。**它是不是缺陷取决于产品意图，本批不主张。**

## 本批**不**主张的事

* **零源站断言**，**未改 `src/`**、**未改任何共享判据**。
* **不主张** L282 该删或该改 —— 它在这个页面一次都没触发，
  而它是**共享判据**，改动要「只增不改 + 机械零回归证明」，**本批没做**。
* **不主张**那 25 枚是缺陷 —— 它们 `own=True`，**点得到**；
  本批只主张「`own` 这一路的读数看不见压在上面的 `pe:none` 层」。
* **不主张** CH4 那 2 枚是新发现 —— 它们是 662/664 的在案项
  （`帮助`←`收起属性`；提示条那几枚 ← 检视器的透明列）。
* **不主张**「四路逐格相同」是全局定理 —— 只在 **W=1280 × 3 窗高**下成立。
* **不主张** sr-only 文件输入该不该算控件 —— **产品决定**。
"""
import importlib.util
import json
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch665-2026-10-01"

# cell names, named once so a detail block cannot mistype one
CH1 = "CH1 clipping: own but absent from the hit stack"
CH2 = "CH2 compositing: not own, an ancestor is faded"
CH3 = "CH3 hit-testability: own, yet a pe:none layer sits over it"
CH3B = "CH3b: a pe:none layer over a control that is NOT own"
CH4 = "CH4 transparency: a fully transparent element took the hit"
CLEAN = "all four readings agree"
OFF = "off-viewport"

HEIGHTS = [720, 900, 1150]
WIDTH = 1280

# 617's scope, inScope, isFlow and isScrim copied verbatim (617:158-169, 196-199),
# and all six `continue` gates recorded instead of acted on.  Nothing here decides
# anything: it only says WHICH gate would have removed each control.
GATES_JS = """() => {
  const SEL = 'button, [role=button], [role=tab], [role=switch], [role=slider],'
    + ' [role=menuitem], input, select, textarea, a[href],'
    + ' [tabindex]:not([tabindex="-1"])';
  const scope = document.querySelector('[data-director-workspace]') || document.body;
  const inScope = (el) => scope.contains(el);
  const isFlow = (el) => !!(el.closest('[data-testid], .react-flow'));
  const cs = (el) => getComputedStyle(el);
  const box = (el) => { const r = el.getBoundingClientRect();
    return [r.x, r.y, r.width, r.height]; };
  const isScrim = (el) => {
    const s = cs(el);
    if (s.position !== 'absolute' && s.position !== 'fixed') return false;
    const host = el.offsetParent;
    const r = el.getBoundingClientRect();
    const h = host ? host.getBoundingClientRect()
      : {left: 0, top: 0, right: innerWidth, bottom: innerHeight,
         width: innerWidth, height: innerHeight};
    if (h.width < 40 || h.height < 40) return false;
    return r.width >= h.width - 0.6 && r.height >= h.height - 0.6
      && (el.textContent || '').trim() === ''
      && s.backgroundColor !== 'rgba(0, 0, 0, 0)';
  };
  const label = (el) => el.getAttribute('aria-label')
    || (el.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 20)
    || el.getAttribute('title') || '<' + el.tagName.toLowerCase() + '>';
  // 664's population: elements the hit test can never see
  const peNone = [];
  for (const e of scope.querySelectorAll('*')) {
    const s = cs(e);
    if (s.pointerEvents !== 'none') continue;
    const r = e.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    peNone.push(e);
  }
  const rows = [];
  for (const el of document.querySelectorAll(SEL)) {
    const b = box(el), s = cs(el);
    const gates = {
      L276_outOfScopeOrFlow: !inScope(el) || isFlow(el),
      L278_zeroSize: b[2] <= 0 || b[3] <= 0,
      L280_visibilityOrDisplay: s.visibility === 'hidden' || s.display === 'none',
      L281_opacityZero: s.opacity !== '' && parseFloat(s.opacity) === 0,
      L282_pointerEventsNone: s.pointerEvents === 'none',
      L285_isScrim: isScrim(el),
    };
    const firstDrop = Object.keys(gates).find((k) => gates[k]) || null;
    if (firstDrop) {
      rows.push({kept: false, droppedBy: firstDrop, label: label(el),
                 data: Object.keys(el.dataset).slice(0, 3).join(','),
                 tag: el.tagName.toLowerCase(),
                 box: b.map((n) => Math.round(n * 10) / 10),
                 pointerEvents: s.pointerEvents, opacity: s.opacity,
                 visibility: s.visibility, display: s.display});
      continue;
    }
    // ---- 617's two readings, verbatim (617:298-319) ----
    const cx = b[0] + b[2] / 2, cy = b[1] + b[3] / 2;
    const offViewport = cx < 0 || cy < 0 || cx > innerWidth || cy > innerHeight;
    const hit = offViewport ? null : document.elementFromPoint(cx, cy);
    const own = !!(hit && (hit === el || el.contains(hit) || hit.contains(el)));
    const paintStack = offViewport ? [] : (document.elementsFromPoint(cx, cy) || []);
    const paintedAtCentre = !offViewport && paintStack.indexOf(el) !== -1;
    // ---- 617's compositing channel (647) ----
    let minAncOpacity = 1;
    for (let n = el; n; n = n.parentElement) {
      const o = parseFloat(cs(n).opacity);
      if (!isNaN(o) && o < minAncOpacity) minAncOpacity = o;
    }
    // ---- channel 4 (664): someone ELSE's pe:none layer over the centre ----
    let peNoneOver = 0;
    for (const e of peNone) {
      const q = e.getBoundingClientRect();
      if (cx >= q.x && cx <= q.right && cy >= q.y && cy <= q.bottom) peNoneOver += 1;
    }
    let transparentTop = false;
    if (hit) {
      const bg = cs(hit).backgroundColor || '';
      const m = bg.match(/rgba\\(([^)]+)\\)/);
      if (m) {
        const parts = m[1].split(',').map((t) => parseFloat(t));
        if (parts.length === 4 && parts[3] === 0) transparentTop = true;
      } else if (bg === 'transparent') { transparentTop = true; }
    }
    rows.push({kept: true, droppedBy: null, label: label(el),
               data: Object.keys(el.dataset).slice(0, 3).join(','),
               tag: el.tagName.toLowerCase(),
               box: b.map((n) => Math.round(n * 10) / 10),
               own: own, paintedAtCentre: paintedAtCentre,
               ownButNotPainted: own && !paintedAtCentre,
               faded: minAncOpacity < 0.999,
               minAncestorOpacity: Math.round(minAncOpacity * 1000) / 1000,
               peNoneOver: peNoneOver, offViewport: offViewport,
               transparentTop: transparentTop && !own,
               hitLabel: hit ? (hit.getAttribute('aria-label')
                   || (hit.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 20)
                   || hit.tagName.toLowerCase()) : null});
  }
  return {vw: innerWidth, vh: innerHeight, total: rows.length,
          peNonePopulation: peNone.length, rows: rows};
}"""


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / f"scripts/verify-liblib-batch{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


b617 = _load("617")

GATE_LABELS = {
    "L276_outOfScopeOrFlow": "not in the desk scope, or inside react-flow",
    "L278_zeroSize": "width or height is 0",
    "L280_visibilityOrDisplay": "visibility:hidden or display:none",
    "L281_opacityZero": "opacity:0",
    "L282_pointerEventsNone": "pointer-events:none — THE THIRD-STATE COLLAPSE",
    "L285_isScrim": "a dismiss catcher, recorded as a scrim instead",
}
GATE_LINES = {"L276_outOfScopeOrFlow": 276, "L278_zeroSize": 278,
              "L280_visibilityOrDisplay": 280, "L281_opacityZero": 281,
              "L282_pointerEventsNone": 282, "L285_isScrim": 285}


def _clean(page: Any) -> None:
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(220)


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
    theirs: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        for h in HEIGHTS:
            page = br.new_page(viewport={"width": WIDTH, "height": h},
                               device_scale_factor=1)
            b617.open_desk(page)
            _clean(page)
            cells[str(h)] = page.evaluate(GATES_JS)
            theirs[str(h)] = page.evaluate(b617.AUDIT_JS,
                                            list(b617.TRANSIENT_OVERLAYS))
            page.close()
        br.close()

    table: dict[str, dict[str, int]] = {}
    by_gate: dict[str, dict[str, int]] = {}
    kept_counts: dict[str, int] = {}
    kept_counts: dict[str, int] = {}
    their_totals: dict[str, int] = {}
    faithful: dict[str, Any] = {}
    ch3_labels: list[str] = []
    opacity_zero: list[dict[str, Any]] = []
    unattributed: dict[str, list[str]] = {}

    for h in HEIGHTS:
        c = cells[str(h)]
        kept = [r for r in c["rows"] if r["kept"]]
        kept_counts[str(h)] = len(kept)
        their_totals[str(h)] = theirs[str(h)]["total"]
        gate_h: dict[str, int] = {}
        for r in c["rows"]:
            if not r["kept"]:
                gate_h[r["droppedBy"]] = gate_h.get(r["droppedBy"], 0) + 1
                if r["droppedBy"] == "L281_opacityZero":
                    opacity_zero.append({"h": h, "label": r["label"],
                                         "data": r["data"], "box": r["box"],
                                         "opacity": r["opacity"]})
        by_gate[str(h)] = gate_h
        buckets: dict[str, int] = {}
        for r in kept:
            if r["offViewport"]:
                k = OFF
            elif r["ownButNotPainted"]:
                k = CH1
            elif not r["own"] and r["faded"]:
                k = CH2
            elif r["peNoneOver"] and r["own"]:
                k = CH3
            elif r["peNoneOver"]:
                k = CH3B
            elif r["transparentTop"]:
                k = CH4
            else:
                k = CLEAN
            buckets[k] = buckets.get(k, 0) + 1
            if k == CH3 and len(ch3_labels) < 10:
                ch3_labels.append(r["label"])
        table[str(h)] = buckets
        mine = sum(1 for r in kept if not r["own"])
        their_blocked = len(theirs[str(h)]["blocked"])
        faithful[str(h)] = {"myKept": len(kept), "theirTotal": theirs[str(h)]["total"],
                            "myBlocked": mine, "theirBlocked": their_blocked,
                            "sameTotal": len(kept) == theirs[str(h)]["total"],
                            "sameBlockedCount": mine == their_blocked,
                            "theirScrims": len(theirs[str(h)]["scrims"])}
        dropped = {r["data"] or r["label"] for r in c["rows"] if not r["kept"]}
        # 617's AUDIT_JS returns `total` (a count) and `blocked` (keys), but NOT
        # the kept items, so a key-level diff is not available.  The proof that
        # the copy is faithful is at the COUNT level and is stated as such; an
        # earlier draft of this check also computed a set difference that was
        # meaningless (kept - dropped - blocked lists every clean control).
        unattributed[str(h)] = {
            "droppedKeys": len(dropped),
            "keptCount": len(kept),
            "rawCount": c["total"],
            "theirTotal": theirs[str(h)]["total"],
            "keyLevelDiffAvailable": False,
        }

    keys = sorted(table, key=int)
    identical = all(table[keys[0]] == table[k] for k in keys)
    ch1 = {h: table[h].get(CH1, 0) for h in keys}
    # gates are counted PER HEIGHT: one census per page load, and the raw
    # population is the whole document, not just the desk
    l282 = {h: by_gate[h].get("L282_pointerEventsNone", 0) for h in keys}
    l282_all_zero = all(n == 0 for n in l282.values())
    gate_totals = {h: {"raw": cells[h]["total"],
                       "dropped": sum(by_gate[h].values()),
                       "kept": kept_counts[h]} for h in keys}
    every_drop_attributed = all(
        gate_totals[h]["dropped"] + gate_totals[h]["kept"] == gate_totals[h]["raw"]
        for h in keys)

    b658 = json.loads((ROOT / "docs/research/liblib-canvas-batch658-2026-10-01"
                            / "runtime-audit.json").read_text(encoding="utf-8"))
    prompt_file_in_658 = any("scene-prompt-file" in k
                             for hh in b658["perHeight"]
                             for k in b658["perHeight"][hh]["occludedKeys"])

    out: dict[str, Any] = {
        "batch": 665,
        "question": "639 left 'a consistency table for the painting-class and "
                    "hit-class readings' open for two years. Build it — and "
                    "while building it, find where the third state collapses in "
                    "the shared criterion.",
        "theCollapseSite": {
            "file": "scripts/verify-liblib-batch617.py",
            "line": GATE_LINES["L282_pointerEventsNone"],
            "code": "if (s.pointerEvents === 'none') continue;",
            "whatItDoes": "a pe:none control is not enumerated at all, so it is "
                          "absent from the ledger rather than reported as "
                          "unmeasurable",
            "why664MissedIt": "664 censused MEASUREMENT calls; this is an "
                              "INCLUSION filter. 664 found the instrument end, "
                              "this batch found the inclusion end.",
        },
        "gates": {g: {"line": GATE_LINES[g], "what": GATE_LABELS[g],
                      "droppedPerHeight": {h: by_gate[h].get(g, 0) for h in keys}}
                  for g in GATE_LABELS},
        "gatesTotal": gate_totals,
        "faithfulnessTo617": faithful,
        "table": table,
        "tableIsIdenticalAtEveryHeight": identical,
        "CH1Clipping": ch1,
        "CH3Labels": ch3_labels,
        "peNonePopulation": {h: cells[h]["peNonePopulation"] for h in keys},
        "opacityZeroDropped": opacity_zero,
        "crossBatch658": {"promptFileKeyPresentIn658": prompt_file_in_658,
                          "theirKeys": b658["perHeight"]["1150"]["occludedKeys"]},
        "accounting": unattributed,
    }

    # ------------------------------------------------------------------ checks
    v.check("the-copied-filters-reproduce-617s-own-census-exactly",
            all(f["sameTotal"] and f["sameBlockedCount"] for f in faithful.values()),
            detail={"perHeight": faithful,
                    "whatWasCopied": "617's scope selector, inScope, isFlow, "
                                     "isScrim, and both readings (own, "
                                     "paintedAtCentre) verbatim from 617:298-319",
                    "whyItMatters": "the point of copying was to reuse the "
                                     "shared criterion's own numbers instead of "
                                     "inventing near-misses.  That only counts if "
                                     "the copy is provably faithful, and this is "
                                     "the proof: same kept count, same blocked "
                                     "count, at every height.",
                    "aWiderProbeFirstFound132": "an earlier bare probe with NO "
                                                "filters enumerated 132; the two "
                                                "extra were exactly the two "
                                                "opacity:0 controls L281 drops. "
                                                "There is no divergence between the "
                                                "two censuses — my first read of it "
                                                "as a superset was wrong."},
            note="a reused criterion is only reuse if the copy is provably equal")

    v.check("every-dropped-control-is-attributed-to-one-of-the-six-gates",
            every_drop_attributed,
            detail={"gates": out["gates"], "gatesTotal": gate_totals,
                    "accounting": unattributed,
                    "countedPerHeight": "one census per page load; the raw "
                                        "population is the whole document, so "
                                        "L276 carries the canvas page's own top bar",
                    "L276sample": "项目菜单 / 工作区名称 / 画布 2 / 工作流 / 故事板",
                    "L278sample": "623's in-case zero-size family, unchanged",
                    "L281sample": opacity_zero,
                    "rule": "record the FIRST gate that would have removed each "
                            "control instead of letting a bare `continue` make it "
                            "disappear"},
            note="a silent continue is a control that cannot be asked about")

    v.check("the-third-state-gate-fires-zero-times-in-the-desk",
            l282_all_zero,
            detail={"L282DroppedPerHeight": l282,
                    "peNonePopulation": out["peNonePopulation"],
                    "reading": "none of the desk's own CONTROLS is pointer-events:"
                               "none, so the inclusion end of the third-state "
                               "collapse does not fire on this page",
                    "scope": "this is a measured zero, and its scope is the "
                             "INCLUSION end only.  It does not mean the desk has "
                             "no blind spot — the next check is that.",
                    "notClaimed": "that the gate should be removed or changed. It "
                                  "is a shared criterion; a change needs "
                                  "只增不改 plus a mechanical zero-regression "
                                  "proof, which this batch did not do.",
                    "alsoZero": {"L280_visibilityOrDisplay": {
                                     h: by_gate[h].get("L280_visibilityOrDisplay", 0)
                                     for h in keys},
                                 "L285_isScrim": {
                                     h: by_gate[h].get("L285_isScrim", 0)
                                     for h in keys}}},
            note="a measured zero, scoped to the inclusion end — and scoped "
                 "honestly, because the next cell is not zero")

    v.check("the-blind-spot-is-outside-the-gate-not-inside-it",
            all(table[h].get(CH3, 0) > 0 for h in keys),
            detail={"CH3count": {h: table[h].get(CH3, 0) for h in keys},
                    "samples": ch3_labels,
                    "mechanism": "L282 tests the CONTROL's own pointer-events. "
                                 "The damage 664 measured is a DIFFERENT pe:none "
                                 "element lying over the control's centre.  A gate "
                                 "that asks the first question is structurally "
                                 "unable to speak about the second.",
                    "notADefectClaim": "own=True means those controls are still "
                                       "clickable.  The claim is only that `own` "
                                       "cannot see what is lying on top of them.",
                    "shareOfKept": {h: "{}/{}".format(
                        table[h].get(CH3, 0), kept_counts[h]) for h in keys}},
            note="the gate is in the right place and the wrong question")

    v.check("the-four-channel-table-is-identical-at-all-three-heights",
            identical and all(n == 0 for n in ch1.values()),
            detail={"table": table, "identicalAtEveryHeight": identical,
                    "CH1Clipping": ch1,
                    "whyCH1isZero": "646's family — a control scrolled out of "
                                    "its OWN scroller — was found on the CANVAS "
                                    "PAGE's 1020px toolbar, not in the director "
                                    "desk. `own` and `paintedAtCentre` therefore "
                                    "never disagree here.",
                    "regularity": "the same shape 633 found for the burial "
                                  "surface: at W=1280 the cell counts do not move "
                                  "with the viewport height",
                    "scope": "W=1280 x 3 heights only. NOT a theorem; a width or "
                             "a shorter viewport can move these cells and this "
                             "check will go red.",
                    "CH4isPriorWork": "the two CH4 cells are 662's 帮助←收起属性 "
                                      "and 664's transparent inspector column — "
                                      "prior findings, counted here for the table",
                    "CH2": "one control per height: not own, with a faded ancestor"},
            note="regularity is a fact about the surface, not about the world")

    v.check("one-of-the-two-silently-dropped-controls-is-a-defect-658-counted",
            prompt_file_in_658 and len(opacity_zero) > 0,
            detail={"opacityZeroDropped": opacity_zero,
                    "in658sOccludedKeys": prompt_file_in_658,
                    "theirKeys": b658["perHeight"]["1150"]["occludedKeys"],
                    "theDisagreement": "658 counted `data-director-scene-prompt-"
                                       "file` among the prompt bar's unreachable "
                                       "controls; 617's census CANNOT ENUMERATE "
                                       "it, because L281 drops it for opacity:0. "
                                       "Neither ledger says so.",
                    "whatItIs": "a 1x1 sr-only file input at opacity 0 — the user "
                                "cannot see it or click it, yet a script can still "
                                "drive it",
                    "scoped": "659 and 660's closed form (centre strictly inside "
                              "the host's clip box) is a statement about VISIBLE "
                              "controls; this one is not visible, so the form does "
                              "not cover it and is not claimed to",
                    "notClaimed": "whether an sr-only file input should count as a "
                                  "control at all — that is a product decision"},
            note="two censuses disagree about whether something exists, and "
                 "neither wrote it down")

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
