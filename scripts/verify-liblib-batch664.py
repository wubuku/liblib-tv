#!/usr/bin/env python3
"""batch 664 验收：第三态（`not-measurable`）的塌缩普查 —— 语料结构 + 代价量

## 起点

663 找到一个**第 9 个盲区形状**：建在 `elementsFromPoint` 上的仪器，
在 `pointer-events:none` 元素上**不会失败，它会自信地作答** ——
把「测不了」报成「知道」。639/641/646 都记过这个盲区，**没有人写下后果**。

663 给自己的仪器加了 `not-measurable` 闸门。本批问两件事：
**语料里有多少台仪器站在那个盲区上**，以及**那个盲区现在值多少钱**。

## 一：普查必须分两层 —— 第一版一个都没找到

第一版照 654 的做法只扫 Python AST，**命中测试调用点是 0**。
因为它们**住在 JS 字符串常量里** —— 654 的 AST 普查数的是 `.click()`
这种 Python 侧调用，而 `document.elementFromPoint` 是**载荷内部**的调用。

**判据的仪器在字符串里，调用点普查就必须分两层**：
Python 侧数「求值了几次」，JS 侧数「仪器里有几次命中测试」。

两层普查（**360** 个验收器，0 个解析失败）：

| 项 | 值 |
|---|---|
| 载荷里含命中测试的文件 | **21** |
| 命中测试调用点 | **26** |
| 其中所在载荷**提到过** `pointer-events` 的 | **10** |
| **能表达拒绝态**（返回一个可表示「测不了」的字段）的 | **1**（只有 663） |
| `page.evaluate(*_JS)` 求值点 | **101** |

「提到过 `pointer-events`」是**弱指标**：659 的 `FORCE_PE_JS` 是**去设置**
它（页内实验），不是**去读它**。所以本批只主张「这个文件知道有这回事」，
**不主张**「这个调用被守住了」—— 那个需要逐处读，本批没做，**不声称**。

## 二：代价 —— 一个**量到的零**，而且它有作用域

导演台开着的时候，工作区里有 **22** 个 `pointer-events:none` 且**有面积**的元素
（三个视口恒定），其中 1 个 `opacity:0`，**13 个不带任何 `data-director` 属性**
（连按名字指认都做不到）。

其中压住活控件**中心点**的有 **27（1280 宽两个视口）/ 30（1920）** 枚，
占 132 枚活控件的 **20%–23%**。

**但代价是零，理由是硬的**：这 30 枚里，命中测试要么正确返回控件本身
（或是它自己的图标 / 632 记过的祖先容器），要么该控件的遮挡**早已在案**。

「在案」是**跨批复核**出来的，不是本批写下的白名单：
命中的元素既不是控件本身、也不是它的后代或祖先时，判据去问
**658 的 `occludedKeys` 里有没有这个控件自己的 `data-director-*` 属性**：

* `帮助` ← `收起属性`：**662 的在案项**；
* `描述想搭建的场景` ← `data-director-scene-prompt-input`：
  **658 在 720 与 1150 都记着它被遮**，659/660 给这一族收了 `W ≥ 1510` 的闭式。
  而这里的盖住者是检视器一根 **280px 宽、`backgroundColor: rgba(0,0,0,0)`
  的透明列** —— **可命中、不可见**，所以任何**绘制类**读数从来点不出它的名。

**所以本批的结论是：第三态现在没有造成我能点名的任何假阴性。**
这句话有作用域：**它只覆盖「这里有什么」这个问题**。
若要回答「这里**画**着什么」（646/647 那一类），那 22 个元素**全部不可见**，
而它们里有 **播放头、画幅参考框、底栏宿主、gizmo 的 webgl 画布**。

**空集不算证据 —— 但「量到的零」和「没记录」不是一回事。**
本批把作用域写死，就是为了让它能被将来的批次推翻。

## 三：那 22 个是谁

三个视口恒定的 10 个具名成员（`byData`）：
`data-director-webgl-canvas` / `data-director-gizmo-webgl-canvas` /
`data-director-gizmo-webgl-canvas-wrapper` / `data-director-aspect-frame` /
`data-director-bottom-bar` / `data-director-scene-prompt-status` /
`data-director-timeline-coachmark` / `data-director-playhead` /
`data-director-character-label=…` + **13 个无属性**。

**`data-director-playhead` 在名单里**这件事有分量：播放头是时间轴上**唯一**
表示「当前时刻」的图元，而它是 `pointer-events:none` ——
**任何基于命中测试的判据都看不见它**。

## 四：闸门已经存在，且它是唯一的

360 个验收器里，**只有 663 的 `COMPETITORS_JS` 能表达拒绝态**，
而它在 3/3 格上正确地触发了（读 663 的 audit，**不重跑**）。
**机制有了，人口也量出来了，缺的只是没有第二台仪器用它。**

## 本批**不**主张的事

* **不主张** 21 个文件里有 20 个「判据有 bug」—— 「提到 pointer-events」
  与「守住了调用」**是两件事**，本批只主张前者。
* **不主张**该给 20 个文件加闸门 —— 那是**共享判据**改动，
  按规矩要「只增不改 + 机械零回归证明」，本批**没做**、**不声称**。
* **不主张**那些 `pointer-events:none` 层该改 —— 它们**点击穿透是对的**，
  绝大多数是装饰层（`span[aria-hidden].absolute.inset-0` 之类）。
* **不主张**「量到的零」覆盖别的问题 —— 作用域见第二节。
* **零源站断言**，**未改 `src/`**、**未改任何共享判据**。
"""
import ast
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch664-2026-10-01"
SELF = "verify-liblib-batch664.py"

HIT = re.compile(r"\belements?FromPoint\s*\(")
PE = re.compile(r"pointerEvents|pointer-events")

# The payload's own refusal: a returned field whose value can express
# "this instrument cannot see the target".  663 invented it; the census asks
# whether anyone else has one.
REFUSAL = re.compile(r"not-measurable|not_measurable|cannotMeasure|unmeasurable")

COST_JS = """() => {
  const scope = document.querySelector('[data-director-workspace]');
  const LIVE = 'button, [role=button], [role=tab], [role=switch], [role=slider],'
    + ' [role=menuitem], input, select, textarea, a[href],'
    + ' [tabindex]:not([tabindex="-1"])';
  const label = (el) => {
    const al = el.getAttribute('aria-label');
    if (al && al.trim()) return al.trim();
    const t = (el.textContent || '').replace(/\\s+/g, ' ').trim();
    if (t) return t.length > 22 ? t.slice(0, 22) : t;
    return el.getAttribute('data-director') || '<' + el.tagName.toLowerCase() + '>';
  };
  const invisible = [];
  for (const el of scope.querySelectorAll('*')) {
    const cs = getComputedStyle(el);
    if (cs.pointerEvents !== 'none') continue;
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    invisible.push({r: r, label: label(el), opacity: cs.opacity,
                    data: Array.from(el.attributes)
                      .filter((a) => a.name.startsWith('data-director'))
                      .map((a) => a.name + '=' + a.value).join(' ') || null});
  }
  const hits = [];
  let liveTotal = 0;
  for (const c of scope.querySelectorAll(LIVE)) {
    const cr = c.getBoundingClientRect();
    if (cr.width < 1 || cr.height < 1) continue;
    liveTotal += 1;
    const cx = cr.x + cr.width / 2, cy = cr.y + cr.height / 2;
    if (cx < 0 || cy < 0 || cx > innerWidth || cy > innerHeight) continue;
    for (const inv of invisible) {
      if (cx < inv.r.x || cx > inv.r.right) continue;
      if (cy < inv.r.y || cy > inv.r.bottom) continue;
      const st = document.elementsFromPoint(cx, cy);
      const top = st[0] || null;
      hits.push({
        control: label(c), centre: [Math.round(cx), Math.round(cy)],
        controlData: Array.from(c.attributes)
          .filter((a) => a.name.startsWith('data-director'))
          .map((a) => a.name + '=' + a.value).join(' ') || null,
        coverer: inv.label, covererData: inv.data, covererOpacity: inv.opacity,
        covererRect: [Math.round(inv.r.x), Math.round(inv.r.y),
                      Math.round(inv.r.width), Math.round(inv.r.height)],
        hitSays: top ? (top.getAttribute('aria-label')
            || (top.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 22)
            || '<' + top.tagName.toLowerCase() + '>') : 'none',
        hitIsSelfOrDescendant: !!(top && (top === c || c.contains(top))),
        // 632's "the coverer is often a container, not a leaf": structural,
        // not a string match.  An ANCESTOR of the control taking the hit is
        // the container case; anything else is a real coverer.
        hitContainsControl: !!(top && top.contains(c)),
        hitTag: top ? top.tagName.toLowerCase() : null,
      });
      break;
    }
  }
  const byData = invisible.reduce((m, i) => {
    const k = i.data || '(no data-director attr)';
    m[k] = (m[k] || 0) + 1; return m;
  }, {});
  return {liveControls: liveTotal,
          pointerEventsNoneElements: invisible.length,
          ofWhichOpacityZero: invisible.filter((i) => i.opacity === '0').length,
          controlsWhoseCentreIsUnderOne: hits.length,
          byData: byData, hits: hits};
}"""


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / f"scripts/verify-liblib-batch{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


b617 = _load("617")


def js_payloads(src: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for node in ast.parse(src).body:
        targets: list[str] = []
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            targets = [node.target.id]
        if not targets or not any(t.endswith("JS") for t in targets):
            continue
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            for t in targets:
                out[t] = node.value.value
    return out


def census_corpus(self_name: str) -> dict[str, Any]:
    """Two layers, because the instrument lives inside a string constant."""
    scripts = sorted((ROOT / "scripts").glob("verify-liblib-batch*.py"))
    totals: Counter = Counter()
    rows: list[dict[str, Any]] = []
    unparsable: list[str] = []
    python_ast_hit_calls = 0     # layer 1: what the first version counted
    js_layer_hit_calls = 0       # layer 2: where the calls actually are
    refusal_files: list[str] = []

    for path in scripts:
        if path.name == self_name:
            continue
        src = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(src)
        except SyntaxError as exc:
            unparsable.append(f"{path.name}: {exc}")
            continue
        rel = path.name
        evaluates = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                    and node.func.attr == "evaluate":
                if any(isinstance(a, ast.Name) and a.id.endswith("JS")
                       for a in node.args):
                    evaluates += 1
        # layer 1: a hit-test call in PYTHON code.  Expected to be zero, and the
        # check below asserts that it is -- the point is that the first version
        # of this census found nothing and that is a fact about the corpus.
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                nm = ast.unparse(node.func).rsplit(".", 1)[-1]
                if nm in ("elementFromPoint", "elementsFromPoint"):
                    python_ast_hit_calls += 1
        payloads = js_payloads(src)
        hits = sum(len(HIT.findall(b)) for b in payloads.values())
        js_layer_hit_calls += hits
        pe = [n for n, b in payloads.items() if PE.search(b)]
        refusals = [n for n, b in payloads.items() if REFUSAL.search(b)]
        if refusals:
            refusal_files.append(rel)
        if hits or evaluates:
            rows.append({"file": rel, "evaluates": evaluates,
                         "hitCallsInJs": hits, "peAwarePayloads": pe,
                         "refusalPayloads": refusals})
            totals["filesWithHit"] += 1
            totals["hitCallsInJs"] += hits
            totals["hitCallsInPeAwarePayload"] += hits if pe else 0
            totals["evaluates"] += evaluates
    return {"scripts": len(scripts) - 1, "unparsable": unparsable,
            "pythonAstHitCalls": python_ast_hit_calls,
            "jsLayerHitCalls": js_layer_hit_calls,
            "totals": dict(totals), "rows": rows,
            "filesThatCanRefuse": refusal_files}


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
    corpus = census_corpus(SELF)
    grid: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        for (w, h) in [(1280, 1150), (1280, 720), (1920, 1150)]:
            page = br.new_page(viewport={"width": w, "height": h},
                               device_scale_factor=1)
            b617.open_desk(page)
            _clean(page)
            grid[f"{w}x{h}"] = page.evaluate(COST_JS)
            page.close()
        br.close()

    b663 = json.loads((ROOT / "docs/research/liblib-canvas-batch663-2026-10-01"
                             / "runtime-audit.json").read_text(encoding="utf-8"))
    refused_in_663 = sorted(b663["verifier"]["counts"]["states"].items())
    n_refused_663 = sum(1 for _, s in refused_in_663 if s == "not-measurable")

    # the measured zero: a covered control's centre must still be reachable, or
    # its occlusion must ALREADY BE ON RECORD.  Admissibility is structural
    # and cross-batch, never a hand-written whitelist:
    #   * the hitter is the control or a descendant      -> still clickable
    #   * the hitter is an ANCESTOR of the control       -> 632's container case
    #   * the control's own data attribute appears in 658's occludedKeys
    #                                                      -> 658/659's families
    #   * the hitter is 收起属性                          -> 662's in-case defect
    # anything else is a NEW occlusion and must fail here.
    b658 = json.loads((ROOT / "docs/research/liblib-canvas-batch658-2026-10-01"
                            / "runtime-audit.json").read_text(encoding="utf-8"))
    b658_keys: set[str] = set()
    for h in b658["perHeight"]:
        b658_keys.update(b658["perHeight"][h]["occludedKeys"])

    covered = {k: c["hits"] for k, c in grid.items()}
    wrong: dict[str, Any] = {}
    attributed: dict[str, Any] = {}
    for k, hits in covered.items():
        for h in hits:
            if h["hitIsSelfOrDescendant"]:
                continue
            if h["hitContainsControl"]:
                continue                       # 632's container case
            if h["hitSays"] == "收起属性":
                attributed.setdefault(k, []).append(
                    {"control": h["control"], "why": "662's in-case defect"})
                continue
            attr = (h.get("controlData") or "").split(" ")[0].split("=")[0]
            on_record = [key for key in sorted(b658_keys) if attr and attr in key]
            if on_record:
                attributed.setdefault(k, []).append(
                    {"control": h["control"], "controlAttr": attr,
                     "matchedPriorKey": on_record,
                     "why": "658 already recorded this control as occluded, and "
                            "659/660 closed-formed the scene-prompt family"})
                continue
            wrong.setdefault(k, []).append(h)
    named_wrong = {k: sorted({(h["hitSays"], h.get("control")) for h in hs})
                   for k, hs in wrong.items()}
    unknown_named = {k: v for k, v in named_wrong.items() if v}
    container_cases = sum(1 for hits in covered.values() for h in hits
                          if h["hitContainsControl"]
                          and not h["hitIsSelfOrDescendant"])

    byData = grid["1920x1150"]["byData"]
    unnamed = byData.get("(no data-director attr)", 0)
    pe_none_counts = {k: c["pointerEventsNoneElements"] for k, c in grid.items()}
    covered_counts = {k: c["controlsWhoseCentreIsUnderOne"] for k, c in grid.items()}
    live_counts = {k: c["liveControls"] for k, c in grid.items()}

    out: dict[str, Any] = {
        "batch": 664,
        "question": "663 found an instrument that answers, confidently, a "
                    "question it cannot see.  How many instruments stand on that "
                    "blind spot, and what does it cost today?",
        "census": {
            "mustBeTwoLayered": {
                "pythonAstHitCalls": corpus["pythonAstHitCalls"],
                "jsLayerHitCalls": corpus["jsLayerHitCalls"],
                "why": "the first version scanned only the Python AST and found "
                       "zero. 654's AST census counted `.click()` on the Python "
                       "side; `document.elementFromPoint` lives INSIDE a JS "
                       "string constant, so the instrument is in the string.",
            },
            "scripts": corpus["scripts"], "unparsable": corpus["unparsable"],
            "totals": corpus["totals"],
            "weakMetric": "「payload mentions pointer-events」 is NOT 「the call "
                          "is guarded」: 659's FORCE_PE_JS sets it rather than "
                          "reads it. This batch claims only the former.",
            "filesThatCanRefuse": corpus["filesThatCanRefuse"],
        },
        "theCost": {
            "perViewport": {k: {"liveControls": live_counts[k],
                                "pointerEventsNoneElements": pe_none_counts[k],
                                "ofWhichOpacityZero": grid[k]["ofWhichOpacityZero"],
                                "controlsWhoseCentreIsUnderOne": covered_counts[k]}
                            for k in grid},
            "theZero": "in every covered cell the hit test still returns the "
                       "control or its own icon, OR the control's occlusion is "
                       "already on record in 658's occludedKeys",
            "exceptionsNamed": {"收起属性": "662's in-case defect",
                                "ancestor container": "632's 'the coverer is often a "
                                                     "container, not a leaf', "
                                                     "detected as hitContainsControl",
                                "on-record families": "658's occludedKeys — the "
                                                      "scene-prompt family that 659 "
                                                      "and 660 closed-formed"},
            "alreadyAttributed": attributed,
            "admissibilityIsCrossBatch": "a non-self hitter is admissible iff the "
                                         "control's own data attribute appears in "
                                         "658's occludedKeys. That is the "
                                         "accumulated record, not a whitelist this "
                                         "batch wrote.",
            "unknownNamedExceptions": unknown_named,
            "scope": "the zero covers 'what is AT this point'. It does NOT cover "
                     "'what is PAINTED here': all 22 elements are invisible to any "
                     "hit-test-based criterion, and they include the playhead, the "
                     "aspect frame and the bottom-bar host.",
        },
        "whoTheyAre": {"byDataAt1920": byData, "unnamed": unnamed},
        "theGateExists": {"batch663States": refused_in_663,
                          "notMeasurableIn663": n_refused_663,
                          "readFrom": "663's audit, not re-run"},
    }

    # ------------------------------------------------------------------ checks
    v.check("the-census-has-to-be-two-layered-and-that-is-now-a-checked-fact",
            corpus["pythonAstHitCalls"] == 0 and corpus["jsLayerHitCalls"] > 0
            and not corpus["unparsable"],
            detail={"pythonAstHitCalls": corpus["pythonAstHitCalls"],
                    "jsLayerHitCalls": corpus["jsLayerHitCalls"],
                    "scripts": corpus["scripts"], "unparsable": corpus["unparsable"],
                    "theFirstRunFoundNothing": "and that is not a null result -- it "
                                               "is a fact about where the "
                                               "instrument lives",
                    "rule": "a call-site census over a criterion corpus has to "
                            "count the Python side (how often a payload is "
                            "evaluated) and the JS side (how many hit tests are in "
                            "it) separately"},
            note="654's AST census was right for `.click()` and wrong for this")

    v.check("of-the-hit-test-call-sites-only-one-payload-can-refuse",
            len(corpus["filesThatCanRefuse"]) == 1
            and corpus["filesThatCanRefuse"] == ["verify-liblib-batch663.py"],
            detail={"scripts": corpus["scripts"],
                    "filesWithHitCalls": corpus["totals"].get("filesWithHit"),
                    "hitCallsInJs": corpus["jsLayerHitCalls"],
                    "hitCallsInPeAwarePayload": corpus["totals"].get(
                        "hitCallsInPeAwarePayload"),
                    "evaluateCallSites": corpus["totals"].get("evaluates"),
                    "filesThatCanRefuse": corpus["filesThatCanRefuse"],
                    "whatARefusalLooksLike": "a returned field whose value can say "
                                             "'this instrument cannot see the "
                                             "target' -- 663's `state`",
                    "whatThisDoesNotClaim": "that the other 20 files have a bug. "
                                            "'Mentions pointer-events' and 'guards "
                                            "the call' are different claims and only "
                                            "the first is measured here.",
                    "theConsequence": "the mechanism exists and is unique; the "
                                      "population it would fire on is measured in "
                                      "the next checks; nobody else uses it."},
            note="a gate that only one instrument walks through is not yet a "
                 "criterion")

    v.check("the-blind-population-is-22-elements-and-13-cannot-even-be-named",
            len(set(pe_none_counts.values())) == 1
            and list(pe_none_counts.values())[0] == 22
            and unnamed == 13,
            detail={"perViewport": out["theCost"]["perViewport"],
                    "constantAcrossViewports": len(set(pe_none_counts.values())) == 1,
                    "unnamedElements": unnamed,
                    "whyItMatters": "13 of 22 carry no data-director attribute, so "
                                    "even a criterion that wanted to refer to them "
                                    "by name could not -- the naming gap is part "
                                    "of the blind spot, not beside it",
                    "ofWhichOpacityZero": {k: grid[k]["ofWhichOpacityZero"]
                                           for k in grid}},
            note="an instrument that cannot see it and a name that cannot address "
                 "it are the same gap twice")

    v.check("the-blind-population-includes-the-playhead-and-the-aspect-frame",
            "data-director-playhead=true data-director-playhead-time=0.000" in byData
            and any("aspect-frame" in k for k in byData)
            and any("bottom-bar" in k for k in byData)
            and any("webgl-canvas" in k for k in byData),
            detail={"byDataAt1920": byData,
                    "playhead": "the only mark on the timeline that says where "
                                "'now' is, and it is pointer-events:none -- no "
                                "hit-test-based criterion can see it",
                    "aspectFrame": "the 16:9 framing guide",
                    "bottomBar": "the host div carries the attribute but not the "
                                 "clicks; only its children are hit-testable",
                    "webglCanvases": "the viewport and gizmo canvases",
                    "scoped": "these are named as MEMBERS OF THE BLIND SET, not as "
                              "defects. They are click-through layers, which is "
                              "what they are for."},
            note="invisible to a click test does not mean invisible on screen")

    v.check("no-new-occlusion-hides-behind-the-pointer-events-none-population",
            not unknown_named,
            detail={"controlsWhoseCentreIsUnderOne": covered_counts,
                    "liveControls": live_counts,
                    "shareCovered": {k: f"{covered_counts[k]}/{live_counts[k]}"
                                     for k in grid},
                    "everyOtherCellSelfOrDescendant": "in all covered cells the hit "
                                                       "test returns the control or "
                                                       "a descendant, i.e. the "
                                                       "control is still clickable",
                    "admissibilityTest": "structural and CROSS-BATCH, not a string "
                                         "whitelist: ancestor hitter = 632; control "
                                         "attr present in 658's occludedKeys = "
                                         "658/659/660; hitter is 收起属性 = 662. "
                                         "Anything else is a NEW occlusion and "
                                         "fails here.",
                    "alreadyAttributed": attributed,
                    "containerCasesObserved": container_cases,
                    "exceptions": {"收起属性": "662's in-case defect, already "
                                              "attributed and closed-form'd",
                                   "ancestor container": "632's 'the coverer is "
                                                         "often a container, not a "
                                                         "leaf' — measured as "
                                                         "`hitContainsControl`, not "
                                                         "matched by text",
                                   "scene-prompt family": "658 recorded "
                                     "`data-director-scene-prompt-input|描述想搭建的场景` "
                                     "as occluded at both 720 and 1150, and 659/660 "
                                     "gave it the W >= 1510 rule. The hitter here is "
                                     "a TRANSPARENT 280px inspector column "
                                     "(backgroundColor rgba(0,0,0,0)) — "
                                     "hit-testable though invisible, which is why "
                                     "no painting-based criterion ever named it."},
                    "newOcclusions": named_wrong,
                    "theCaseThatAlmostSlippedThrough": "the scene-prompt input's "
                                                        "coverer is transparent, so "
                                                        "it is invisible to any "
                                                        "PAINT-based reading and "
                                                        "only shows up under a hit "
                                                        "test",
                    "whyThisIsWorthRecording": "an empty set is not evidence -- but "
                                               "a measured zero with its scope "
                                               "written down is different from an "
                                               "unrecorded one, and this one is "
                                               "falsifiable by the next batch"},
            note="空集不算证据；但量到的零和没记录不是一回事")

    v.check("the-gate-already-exists-and-it-fired",
            n_refused_663 == 3 and len(corpus["filesThatCanRefuse"]) == 1,
            detail={"batch663States": refused_in_663,
                    "notMeasurableCells": n_refused_663,
                    "readFrom": "663's audit — not re-run here",
                    "population": f"{pe_none_counts['1920x1150']} elements in the "
                                  "open desk, of which the 3 the gate fired on are "
                                  "the ones sitting at a probed overlay's centre",
                    "theGap": "mechanism done, population measured, and no second "
                              "instrument uses it. Turning that into a shared "
                              "criterion is a `只增不改` change with a mechanical "
                              "zero-regression proof, which this batch did NOT do "
                              "and does NOT claim."},
            note="基础设施齐了，缺的是有人接线")

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
