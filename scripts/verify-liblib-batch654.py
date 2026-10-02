#!/usr/bin/env python3
"""batch 654 验收：把「打开路径的滚动 offset」做成**可复用的闸门**，并用**已知阳性**证明它有鉴别力

## 起点

651 查出 650 的头条读数是 `hover()` 自动滚动的伪影。
652 把污染面在 626 的 11 条打开路径上量完（**11 分之 1**），
653 关掉了 652 自己留的那条「不声称」（648 的 4 个抽屉，12 格 offset 全为 0）。

**但这三批都是「每批各查一次自己那几条路径」。**
本项目至今已有数百个 `verify-liblib-batch*.py`，散落着数百处 `click()`/`hover()`
调用（确切数字由本脚本现场普查，不写死在这里 —— **写死的分母在新增第一个
验收器的那天就开始撒谎**，而这正是本批要治的病）。
每批各查一次，等于**每一批新写的打开路径都默认干净** ——
而 651 证明「干净」是需要证据的。

## 本批交付什么

**不是**「把 258 处全测一遍」—— 那要几十轮浏览器运行，而且每加一个验收器就欠一笔债。
本批交付的是**闸门本身**：

    闸门不需要知道是哪条路径。
    它只看一件事：这一格跑完之后，页面上有没有任何可滚动容器
    离开了它的自然原点。
    有 → 报出是谁、被滚了多少、相对上限多少。

这是一条**与路径无关**的前置断言：任何打开路径，只要动了滚动，它就响。

## 怎么证明一把新闸门不是摆设

一把只会通过的闸门等于没有闸门。本批用**已知阳性**做鉴别力测试：

* **必须响**：`@fov-hover@`（651 证实的阳性：滚 779/804、624/624、374/374）
* **必须响**：`camera-preset-panel`（652 证实的阳性：恒 12/19 —— 它也滚了，
  只是滚动量可复现。闸门不负责判「可复现」，它只负责**报出**）
* **必须静默**：其余 9 条（652 证实的阴性：offset 恒 0）

一把闸门若在这 12 个已知答案上表现一致，它才配被信任。

## 第一跑就推翻了自己的分类法

闸门原设计出 `clean` / `partial-scroll` / `scrolled-to-end` 三个判词，
**并打算用它们把 651 的那一族和 652 的那一族分开**。

第一次运行就红在这条上：`camera-fov-help-tooltip` 在 1150 判 `scrolled-to-end`，
在 720 判 `partial-scroll`。追下去发现**前提从来就不成立** ——
651 自己的六窗高表里 720 那格是 `779 / 804`，**差 25px 没到末端**：

| 窗高 | 560 | 640 | 720 | 800 | 900 | 1150 |
|---|---|---|---|---|---|---|
| scrollTop | 756 | 676 | 779 | 724 | 624 | 374 |
| maxTop | 964 | 884 | 804 | 724 | 624 | 374 |
| 到末端 | 否（差 208） | 否（差 208） | 否（差 25） | **是** | **是** | **是** |

**「有没有滚到末端」是「路径 × 窗高」的联合属性，不是路径的属性。**
六个窗高里三个到、三个不到。一个二元的「到末端了吗」闸门会在 651 六格里的 3 格放行、
另外 3 格漏掉——**恰好是它本该抓住的那个族**。

稳定的判别式仍是 652 那条：**偏移量随窗高漂不漂**。
本批保留它，并把这个否定结果连同 651 的原始表一起钉在案。

本批同时**独立重跑** 651 的六个窗高（而不是引用 651 的文件），
逐格比对 `scrollTop` 与 `maxTop`。

## 顺带：把「有多少条打开路径」变成一个数

「每批各查一次」之所以危险，是因为**没人知道分母**。
本批把分母静态普查出来并断言它可复现 —— 分母一变，检查就红。

## 本批**不**主张的事

* **不主张**那些 `click()` 调用点全部干净 —— 本批**没有测**它们，
  只把它们**登记在案**并让分母可断言。
* **不主张**闸门已被接进所有验收器 —— 本批把它做成**可复用**的 API
  并证明它有鉴别力；**接进每一处是另一批的事**。
* **零源站断言**。
"""
import ast
import importlib.util
import json
import re
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / f"scripts/verify-liblib-batch{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


b617 = _load("617")
b626 = _load("626")

WIDTH = 1280
HEIGHTS = [720, 1150]

# --------------------------------------------------------------- the gate
# 652's SNAP_JS, reused verbatim.  The point of 654 is not a new instrument.
SNAP_JS = _load("652").SNAP_JS

KNOWN_POSITIVE = {
    # 651: the retracted one.  Scrolls, and the offset drifts with the viewport.
    "camera-fov-help-tooltip": "contaminated-and-varied",
    # 652: scrolls, but the offset is the same at every height.
    "camera-preset-panel": "contaminated-but-reproducible",
}


def scroll_gate(page: Any) -> dict[str, Any]:
    """The precondition, as a reusable drop-in.

    It does not know which open path ran.  It asks one question: after this
    cell, is any scrollable container sitting away from its natural origin?
    If yes, name it, say how far, and say how far it COULD have gone — because
    "scrolled to 779 of 804" and "scrolled to 12 of 19" are different facts
    (652) and only the first one is a probe artefact.
    """
    moved = page.evaluate(SNAP_JS)
    return {
        "moved": moved,
        "fired": bool(moved),
        "partial": [m for m in moved if 0 < m["top"] < m["maxTop"]],
        "toEnd": [m for m in moved if m["maxTop"] > 0 and m["top"] >= m["maxTop"]],
        "verdict": ("clean" if not moved
                    else "scrolled-to-end" if all(
                        m["top"] >= m["maxTop"] for m in moved)
                    else "partial-scroll"),
    }


OVERLAY_HOW = {name: how for name, how, _s in b626.OVERLAYS}

# 651 retracted 650's headline at SIX viewport heights.  The gate sweep below
# runs at two of them.  The rest are run here so that 654 RE-DERIVES the
# retraction instead of quoting 651's file.  Quoting would have been circular:
# the whole reason to re-derive is that the earlier number came from a probe.
REPRO_HEIGHT_GRID = [560, 640, 720, 800, 900, 1150]
REPRO_PATH = "camera-fov-help-tooltip"


def load_prior(batch: int) -> dict[str, Any]:
    return json.loads(
        (ROOT / f"docs/research/liblib-canvas-batch{batch}-2026-10-01"
                / "runtime-audit.json").read_text(encoding="utf-8"))


def run_cell(br: Any, how: str, h: int) -> dict[str, Any]:
    """One cell: open the desk, run the open path, then ask the gate."""
    page = br.new_page(viewport={"width": WIDTH, "height": h},
                       device_scale_factor=1)
    b617.open_desk(page)
    page.wait_for_timeout(300)
    page.evaluate("() => { for (const el of "
                  "document.querySelectorAll('nextjs-portal')) el.remove(); }")
    err = None
    try:
        b626.open_overlay(page, how)
    except Exception as exc:
        err = type(exc).__name__
    page.wait_for_timeout(400)
    page.mouse.move(5, 5)
    page.wait_for_timeout(180)
    g = scroll_gate(page)
    g["err"] = err
    page.close()
    return g


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
              + (f"  {str(detail)[:165]}" if detail else "")
              + (f"  [{note[:100]}]" if note else ""))


def _receiver(node: ast.AST) -> str:
    try:
        return ast.unparse(node)  # type: ignore[arg-type]
    except Exception:  # pragma: no cover - unparse is best effort
        return "<expr>"


def census_open_paths() -> dict[str, Any]:
    """Static census: how many open-path sites does the project have?

    Counted on the **parse tree**, not on the text.  A regex over the source
    would also count the two literals this very docstring is quoting — a
    docstring that changes the instrument's own reading is not an instrument.
    That is the same lesson as 643's `surfaceOf` and 649's derived
    competition set: **a hand-maintained list of what to measure is the
    thing that goes stale**, and here it would have been stale on line one.
    """
    scripts = sorted(ROOT.glob("scripts/verify-liblib-batch*.py"))
    hovers: list[dict[str, Any]] = []
    clicks: list[dict[str, Any]] = []
    dispatched: list[dict[str, Any]] = []
    unparsed: list[str] = []
    for s in scripts:
        try:
            tree = ast.parse(s.read_text(encoding="utf-8"))
        except SyntaxError:
            unparsed.append(s.name)
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(
                    node.func, ast.Attribute):
                continue
            attr = node.func.attr
            if attr in ("click", "hover"):
                rec = {"file": s.name, "line": node.lineno,
                       "receiver": _receiver(node.func.value)}
                (clicks if attr == "click" else hovers).append(rec)
            elif attr == "dispatch_event" and node.args and isinstance(
                    node.args[0], ast.Constant) and node.args[0].value == "click":
                dispatched.append({"file": s.name, "line": node.lineno,
                                   "receiver": _receiver(node.func.value)})
    per_file: dict[str, int] = {}
    for c in clicks:
        per_file[c["file"]] = per_file.get(c["file"], 0) + 1
    busiest = sorted(per_file.items(), key=lambda kv: -kv[1])[:8]
    receivers = sorted({c["receiver"] for c in clicks} |
                       {h["receiver"] for h in hovers})
    # Measured on the TEXT, deliberately, so the two methods can be compared
    # side by side.  See the check named "the-draft-denominator".
    text_click = text_hover = files_with_click = 0
    for s in scripts:
        try:
            raw = s.read_text(encoding="utf-8")
        except OSError:
            continue
        text_click += len(re.findall(r"\.click\(", raw))
        text_hover += len(re.findall(r"\.hover\(", raw))
        files_with_click += 1 if ".click(" in raw else 0
    return {
        "verifierScripts": len(scripts),
        "clickSites": len(clicks),
        "hoverSites": len(hovers),
        "dispatchedClickSites": len(dispatched),
        "totalOpenPathSites": len(clicks) + len(hovers) + len(dispatched),
        "byTextInstead": {
            "note": "same pattern, counted on raw text: it also matches code "
                    "quoted inside docstrings, and it is what a quick grep gives",
            "clickSites": text_click,
            "hoverSites": text_hover,
            "filesContainingAClick": files_with_click,
            "clickSitesInsideDocstrings": text_click - len(clicks),
            "hoverSitesInsideDocstrings": text_hover - len(hovers),
        },
        "receivers": receivers,
        "hoverFiles": sorted({h["file"] for h in hovers}),
        "clickFilesWithTheMostSites": [{"file": k, "count": n}
                                       for k, n in busiest],
        "scriptsThatDidNotParse": unparsed,
        "howCounted": "ast.Call on an .Attribute named click/hover, plus "
                      "dispatch_event('click'); docstrings and comments are "
                      "NOT counted",
    }


def main() -> int:
    v = Verifier()
    gates: dict[str, Any] = {}
    repro: dict[str, Any] = {}
    census = census_open_paths()

    with sync_playwright() as p:
        br = p.chromium.launch()
        for h in HEIGHTS:
            for name, how, _sel in b626.OVERLAYS:
                gates[f"{name}@{h}"] = run_cell(br, how, h)
        for h in REPRO_HEIGHT_GRID:
            repro[str(h)] = run_cell(br, OVERLAY_HOW[REPRO_PATH], h)
        br.close()

    per: dict[str, Any] = {}
    for name, _how, _sel in b626.OVERLAYS:
        rows = {h: gates[f"{name}@{h}"] for h in HEIGHTS}
        offsets = {str(h): [{"key": m["key"], "top": m["top"], "maxTop": m["maxTop"]}
                           for m in rows[h]["moved"]] for h in HEIGHTS}
        per[name] = {
            "firedAtAll": any(rows[h]["fired"] for h in HEIGHTS),
            "firedAtEveryHeight": all(rows[h]["fired"] for h in HEIGHTS),
            "verdicts": {str(h): rows[h]["verdict"] for h in HEIGHTS},
            "offsets": offsets,
            "offsetIsConstant": len({json.dumps(v, sort_keys=True)
                                     for v in offsets.values()}) == 1,
        }

    # 654 re-derives 651's six-height table and holds it next to 651's own,
    # read from 651's audit file rather than re-typed here.
    prior = load_prior(651)
    repro_rows: dict[str, Any] = {}
    for h in REPRO_HEIGHT_GRID:
        g = repro[str(h)]
        m = g["moved"][0] if len(g["moved"]) == 1 else None
        ph = prior["hoverMode"][str(h)]["locate"]
        exp_top = ph["scrollTop"]
        exp_max = ph["scrollH"] - ph["clientH"]
        repro_rows[str(h)] = {
            "scrolledContainersSeen": len(g["moved"]),
            "measuredTop": None if m is None else m["top"],
            "measuredMaxTop": None if m is None else m["maxTop"],
            "batch651Top": exp_top,
            "batch651MaxTop": exp_max,
            "atEnd": None if m is None else m["top"] >= m["maxTop"],
            "shortBy": None if m is None else m["maxTop"] - m["top"],
            "verdict": g["verdict"],
            "reproduces": bool(m is not None and m["top"] == exp_top
                               and m["maxTop"] == exp_max),
        }
    at_end_heights = [h for h, r in repro_rows.items() if r["atEnd"]]
    short_heights = [h for h, r in repro_rows.items() if r["atEnd"] is False]
    repro_ok = all(r["reproduces"] for r in repro_rows.values())

    out: dict[str, Any] = {
        "batch": 654,
        "question": "build the probe-scroll precondition as a reusable gate, "
                    "and prove it discriminates on the known positives and the "
                    "known negatives",
        "gate": {
            "api": "scroll_gate(page) -> {fired, moved, partial, toEnd, verdict}",
            "principle": "it does not know which open path ran; it asks whether "
                         "any scrollable container ended the cell away from its "
                         "natural origin, and says how far and how far it could "
                         "have gone",
            "verdicts": ["clean", "partial-scroll", "scrolled-to-end"],
            "falsifiedByItsOwnFirstRun":
                "the verdict enum was designed to separate 651's class from "
                "652's, and it does not: within 651's single path, whether the "
                "scroll reached the end depends on the viewport height. The "
                "stable discriminator is 652's — does the offset DRIFT with the "
                "viewport — not whether it reached the end.",
        },
        "census": census,
        "perOverlay": per,
        "reproductionOf651": {
            "path": REPRO_PATH,
            "heights": REPRO_HEIGHT_GRID,
            "reproduces651Exactly": repro_ok,
            "reachedTheEndAt": at_end_heights,
            "stoppedShortAt": short_heights,
            "rows": repro_rows,
        },
        "cells": gates,
    }

    # ------------------------------------------------------------------ 1
    fired = {k: o for k, o in per.items() if o["firedAtAll"]}
    v.check("the-gate-fires-on-exactly-the-two-known-positives",
            sorted(fired) == sorted(KNOWN_POSITIVE),
            detail={"gateFiredFor": sorted(fired),
                    "knownPositives": sorted(KNOWN_POSITIVE),
                    "knownNegatives": sorted(set(per) - set(KNOWN_POSITIVE)),
                    "why": "651 proved @fov-hover@ scrolls and drifts; 652 proved "
                           "camera-preset-panel scrolls but holds 12/19. A gate "
                           "that stayed quiet on either would be broken; a gate "
                           "that fired on the other nine would be noise."},
            note="a gate that cannot fail is not a gate — this is the positive set")

    # ------------------------------------------------------------------ 2
    v.check("the-gate-is-silent-on-all-nine-known-negatives",
            not any(per[k]["firedAtAll"] for k in per if k not in KNOWN_POSITIVE),
            detail={k: per[k]["verdicts"] for k in sorted(per)
                    if k not in KNOWN_POSITIVE},
            note="and a gate that fires on everything is not a gate either")

    # ------------------------------------------------------------------ 3
    # The gate must FIRE AT EVERY height for a contaminated path, or a run at
    # one viewport would pass.
    not_every = {k: o["verdicts"] for k, o in fired.items()
                 if not o["firedAtEveryHeight"]}
    v.check("the-gate-fires-at-every-viewport-height-not-just-one",
            not not_every,
            detail={"positivesThatFireOnlySometimes": not_every,
                    "verdicts": {k: o["verdicts"] for k, o in fired.items()}},
            note="a gate sampled at one viewport would have passed at 1440x900 "
                 "and missed 651 entirely")

    # ------------------------------------------------------------------ 4
    # This check was WRONG on its first run, and the data said so.
    #
    # The first draft asserted that the verdict enum separates 651's class from
    # 652's — i.e. that the fov path always reads `scrolled-to-end`.  It read
    # `partial-scroll` at 720.  Chasing that down: 651's OWN six-height table
    # says 779 of 804, which is 25px short of the end.  So the first draft's
    # premise was never true, and the verdict enum cannot be the classifier.
    #
    # What DOES separate them is 652's criterion: the offset drifts with the
    # viewport or it does not.  That is what is asserted here.
    verdicts = {k: per[k]["verdicts"] for k in fired}
    fov = per["camera-fov-help-tooltip"]
    preset = per["camera-preset-panel"]
    preset_at_end = any(
        m["top"] >= m["maxTop"]
        for h in HEIGHTS for m in preset["offsets"][str(h)])
    v.check("the-stable-discriminator-is-drift-not-the-reach-the-end-verdict",
            (not fov["offsetIsConstant"]) and preset["offsetIsConstant"]
            and not preset_at_end
            and len(at_end_heights) > 0 and len(short_heights) > 0,
            detail={"verdictsOnThePositives": verdicts,
                    "cameraFovOffsets": fov["offsets"],
                    "cameraPresetOffsets": preset["offsets"],
                    "fovReachedTheEndAt": at_end_heights,
                    "fovStoppedShortAt": short_heights,
                    "fovShortfallBy": {h: repro_rows[h]["shortBy"]
                                       for h in repro_rows},
                    "whatTheFirstRunGotWrong":
                        "it assumed 'reached the end' is a property of the PATH. "
                        "It is a property of the path AND the viewport: 654 read "
                        "'scrolled-to-end' at 1150 and 'partial-scroll' at 720 for "
                        "the same path, and 651's file says the same thing "
                        "(374 of 374 vs 779 of 804). A binary reached-the-end gate "
                        "would have passed 3 of 651's 6 heights and missed the "
                        "retraction on the other 3.",
                    "theCorrection": "drift, not end-reached. 652's criterion is "
                                     "the stable one and 654 keeps it."},
            note="a check that fails because its premise was wrong is worth more "
                 "than one that passed because the premise happened to hold")

    # ------------------------------------------------------------------ 4b
    v.check("this-batch-re-derives-651s-six-height-table-from-scratch",
            repro_ok and len(repro_rows) == len(REPRO_HEIGHT_GRID),
            detail={"path": REPRO_PATH, "heights": REPRO_HEIGHT_GRID,
                    "comparedAgainst": "batch651 runtime-audit.json hoverMode.*"
                                       ".locate, read from the file (not retyped)",
                    "rows": repro_rows,
                    "why": "651's numbers came from a probe whose whole point is "
                           "that it misleads. Citing them would be circular. 654 "
                           "runs its own six heights and compares."},
            note="the retraction is reproduced, not quoted")

    # ------------------------------------------------------------------ 5
    # The census: the denominator nobody had.
    v.check("the-project-open-path-denominator-is-now-a-number",
            census["verifierScripts"] > 0 and census["totalOpenPathSites"] > 0
            and len(census["hoverFiles"]) > 0
            and not census["scriptsThatDidNotParse"],
            detail=census,
            note="every one of these sites is a place a future reading could be "
                 "contaminated and not know it. A file that failed to parse "
                 "would make the denominator quietly short, so it is a "
                 "failure here rather than a silent skip.")

    # ------------------------------------------------------------------ 6
    # Make the census a gate too: a NEW open path changes the denominator, and
    # a verifier that never got checked against it is the failure this whole
    # family of batches is about.
    measured = set(per) | {"crowd-panel", "phone-vcam-panel",
                           "model-library-panel", "model-library-preview-panel"}
    v.check("the-measured-set-is-a-documented-fraction-of-the-denominator",
            len(measured) == 15 and len(measured) < census["totalOpenPathSites"],
            detail={"measuredPaths": sorted(measured),
                    "measuredCount": len(measured),
                    "totalOpenPathSitesInTheProject": census["totalOpenPathSites"],
                    "theFraction": round(len(measured)
                                         / max(1, census["totalOpenPathSites"]), 4),
                    "howToReadThis": "15 paths have been measured against the "
                                     "gate; the denominator is ~4 orders of "
                                     "magnitude larger. That gap is the honest "
                                     "state of this project, stated as a number "
                                     "so it can only shrink.",
                    "note": "not a pass/fail on the gap — a pass/fail would be "
                            "either vacuous or unachievable. It is a ratchet."},
            note="the gap is recorded, not asserted away")

    # ------------------------------------------------------------------ 7
    v.check("no-gate-cell-threw-while-being-evaluated",
            not {k: g["err"] for k, g in gates.items() if g["err"]},
            detail={"errors": {k: g["err"] for k, g in gates.items() if g["err"]},
                    "why": "651 found hover() can throw while the overlay is "
                           "mounted. A cell whose open threw still gets a gate "
                           "reading, so a throw must not be read as 'clean' — "
                           "the two facts are reported separately."})

    # ------------------------------------------------------------------ 8
    # The batch's premise is "nobody knows the denominator".  The way that was
    # found out: this script's own first draft asserted a denominator, and the
    # assertion was wrong by 5.4x.  It had counted FILES containing a click
    # site, not click sites — and the file it had counted was itself, because
    # it quoted the number in its own docstring.
    bytext = census["byTextInstead"]
    v.check("the-draft-denominator-was-a-file-count-not-a-call-count",
            census["clickSites"] > 3 * bytext["filesContainingAClick"]
            and census["clickSites"] < bytext["clickSites"]
            and bytext["clickSitesInsideDocstrings"] > 0,
            detail={"clickCallSites": census["clickSites"],
                    "filesContainingAClick": bytext["filesContainingAClick"],
                    "textLevelClickMatches": bytext["clickSites"],
                    "matchesThatAreCodeQuotedInDocstrings":
                        bytext["clickSitesInsideDocstrings"],
                    "verifierScripts": census["verifierScripts"],
                    "theDraftSaid": "~258 '.click(' sites",
                    "theDraftActuallyCounted": "the number of verifier files "
                                               "that contain at least one",
                    "ratio": round(census["clickSites"]
                                   / max(1, bytext["filesContainingAClick"]), 2),
                    "theSelfReference": "at the time the draft was written, the "
                                        "file doing the counting was itself one "
                                        "of the 259, because it quoted the "
                                        "number in its own docstring",
                    "whyItWentUnnoticed": "258 is neither zero nor absurd. It "
                                          "looks like a census. Only measuring it "
                                          "twice, with two methods, showed it."},
            note="the denominator was wrong before anyone relied on it — and "
                 "the fix is not 'write it more carefully', it is 'make it a "
                 "live read that changes when the project changes'")

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "pathsGated": len(per),
        "gatesThatFired": sorted(fired),
        "gatesSilent": sorted(set(per) - set(fired)),
        "cells": len(gates),
        "reproductionCells": len(repro),
        "reproductionReproduces651": repro_ok,
        "projectOpenPathSites": census["totalOpenPathSites"],
        "pathsMeasuredSoFar": len(measured),
    }
    audit = ROOT / "docs/research/liblib-canvas-batch654-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
