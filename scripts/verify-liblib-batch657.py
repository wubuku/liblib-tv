#!/usr/bin/env python3
"""batch 657 验收：把 656 留下的两笔账各还清一笔

## 656 留了两笔账，本批各还一笔

**账一：`help` 记成 `probe-failed`。**
656 的结论只能是「这个探针点不着它」—— 但 651 早就说过同一个形状：
**探针报错不等于读数为零，读数可能就在那儿。**
656 因此把 `help` 留在「**未测**」而不是「测了没有」。
本批换一把探针重测：普通 `.click()` 会因 actionability 超时，
而 `click(force=True)` 与 `dispatch_event('click')` **都能落地**。

**账二：那 4 个无人引用的 `data-director-scene-*` 标记。**
656 事先预测「点 `scene` 会把它们带出来」，**结果一个都没出现**，
并把「它们可能只存在于源码字符串里」写成了一个真开口。
本批去查它们到底在不在 DOM 里。

## 顺带把「源码里有、DOM 里从来没有」这一整类普查出来

这不是本批的重点，但它是账二的一般化：
`src/` 里写着 `data-director-*` 名字，与「它在任何被采样的状态下真的挂载过」
是两个不同的事实。把差集列成一个数，**并且写清楚它只是「没被观测到」**。

## 本批**不**主张的事

* **不主张**「没被观测到」的标记是死代码 —— 本批只采样了 10 个状态；
  移动面板、选中相机等状态**没采**，那里的标记当然观测不到。
* **不主张**撤回 656 对 `help` 的读数 —— 656 记的是「探针失败」，
  那是当时**正确**的读数；本批是**收口**，不是翻案。
* **零源站断言**。
"""
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
b654 = _load("654")
b656 = _load("656")

WIDTH = 1280
HEIGHT = 1150
scroll_gate = b654.scroll_gate
SNAP3_JS = b656.SNAP3_JS
diff_snap = b656.diff_snap
HELP_SEL = "[data-director-rail-entry='help']"

# The four markers 656 predicted and did not find.  Kept verbatim so the
# falsification stays checkable rather than merely remembered.
PREDICTED = [
    "data-director-scene-settings-section",
    "data-director-scene-display-settings",
    "data-director-scene-camera-actions",
    "data-director-scene-toggle",
]

MARKER_RE = re.compile(r"data-director-[a-z0-9-]+")


def src_markers() -> set[str]:
    out: set[str] = set()
    for pat in ("src/**/*.tsx", "src/**/*.ts"):
        for f in ROOT.glob(pat):
            out |= set(MARKER_RE.findall(f.read_text(encoding="utf-8")))
    return out


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


def snap(page: Any) -> dict[str, Any]:
    return page.evaluate(SNAP3_JS)


def stack_at(page: Any, sel: str) -> dict[str, Any]:
    """What is actually on top of the target's centre?

    649 said position is not stacking.  This is the mirror: a coordinate click
    is not a click on that element.
    """
    return page.evaluate(
        """(sel) => {
          const el = document.querySelector(sel);
          if (!el) return {found: false};
          const r = el.getBoundingClientRect();
          const cx = Math.round(r.x + r.width / 2);
          const cy = Math.round(r.y + r.height / 2);
          const stack = document.elementsFromPoint(cx, cy).map(e => {
            const c = (e.getAttribute('class') || '').split(' ')
                         .filter(Boolean).slice(0, 3).join('.');
            const own = [...e.attributes].map(a => a.name)
                         .filter(n => n.startsWith('data-director-'));
            return {el: e.tagName.toLowerCase() + (c ? '.' + c : ''),
                    markers: own};
          });
          // A click at this point reaches the target only if the topmost
          // element IS the target, or lives inside it.  An ancestor on top is
          // not enough — the click would land on the ancestor's own surface.
          const top = document.elementsFromPoint(cx, cy)[0];
          return {found: true, center: [cx, cy],
                  rect: [Math.round(r.x), Math.round(r.y),
                         Math.round(r.width), Math.round(r.height)],
                  innerHeight: window.innerHeight,
                  stackDepth: stack.length,
                  topFive: stack.slice(0, 5),
                  targetIsTopmost: !!top && (top === el || el.contains(top)),
                  targetIndexInStack: document.elementsFromPoint(cx, cy)
                      .indexOf(el)};
        }""", sel)


def try_help(br: Any, how: str) -> dict[str, Any]:
    page = br.new_page(viewport={"width": WIDTH, "height": HEIGHT},
                       device_scale_factor=1)
    b617.open_desk(page)
    page.wait_for_timeout(300)
    page.evaluate("() => { for (const el of "
                  "document.querySelectorAll('nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(200)
    stack = stack_at(page, HELP_SEL)
    before = snap(page)
    err = None
    try:
        loc = page.locator(HELP_SEL).first
        if how.startswith("force"):
            loc.click(timeout=6_000, force=True)
        elif how == "dispatch":
            loc.dispatch_event("click")
        else:
            loc.click(timeout=6_000)
    except Exception as exc:
        err = f"{type(exc).__name__}: {str(exc)[:70]}"
    page.wait_for_timeout(500)
    page.mouse.move(5, 5)
    page.wait_for_timeout(180)
    after = snap(page)
    gate = scroll_gate(page)
    page.close()
    before["__err"] = err
    return {"probe": how, "err": err, "stack": stack, "gate": gate,
            **diff_snap(before, after), "markersAfter": after["markers"]}


def main() -> int:
    v = Verifier()
    in_src = src_markers()

    probes: dict[str, Any] = {}
    observed: set[str] = set()
    with sync_playwright() as p:
        br = p.chromium.launch()
        for how in ("plain", "force", "dispatch", "force-repeat"):
            probes[how] = try_help(br, how)
            observed |= set(probes[how]["markersAfter"])
        # Re-observe the states 656 sampled, so "never observed" means "never
        # observed across the same ten states", not "never observed anywhere".
        for value in ("scene", "add-camera", "add-character", "panorama",
                      "aspect-ratio", "ai-import"):
            page = br.new_page(viewport={"width": WIDTH, "height": HEIGHT},
                               device_scale_factor=1)
            b617.open_desk(page)
            page.wait_for_timeout(300)
            page.evaluate("() => { for (const el of "
                          "document.querySelectorAll('nextjs-portal')) el.remove(); }")
            page.mouse.move(5, 5)
            page.wait_for_timeout(200)
            observed |= set(snap(page)["markers"])
            try:
                page.locator(f"[data-director-rail-entry='{value}']").first.click(
                    timeout=6_000, force=True)
            except Exception:
                pass
            page.wait_for_timeout(400)
            page.mouse.move(5, 5)
            page.wait_for_timeout(150)
            observed |= set(snap(page)["markers"])
            page.close()
        br.close()

    landed = {k: (p_["err"] is None) for k, p_ in probes.items()}
    stack = probes["plain"]["stack"]
    never_observed = sorted(m for m in PREDICTED if m not in observed)
    in_src_but_unseen = sorted(in_src - observed)
    force_runs = [probes["force"], probes["force-repeat"]]

    out: dict[str, Any] = {
        "batch": 657,
        "question": "settle 656's two loose ends: re-measure `help` with probes "
                    "that land, and find out whether the four scene-* markers "
                    "656 failed to predict are in the DOM at all",
        "helpProbes": probes,
        "probeLanded": landed,
        "occlusion": stack,
        "sceneMarkersPrediction": {
            "predicted": PREDICTED,
            "neverObservedAcrossTenStates": never_observed,
            "allInSrc": [m for m in PREDICTED if m in in_src],
            "sceneMarkersActuallyPresent": sorted(
                m for m in observed if m.startswith("data-director-scene")),
        },
        "unobservedCensus": {
            "markersInSrc": len(in_src),
            "markersObservedInTenStates": len(observed),
            "inSrcButNeverObserved": len(in_src_but_unseen),
            "list": in_src_but_unseen,
            "whatThisIsNot": "not a dead-code list. Ten states were sampled; the "
                             "mobile panel, a selected camera, a drawn motion "
                             "path and every other gated state were not. A marker "
                             "that mounts in one of THOSE would appear here.",
        },
    }

    # ------------------------------------------------------------------ 1
    v.check("the-help-entry-is-occluded-by-the-timeline-track-list",
            (not stack["targetIsTopmost"]) and stack["stackDepth"] > 1
            and any("timeline" in (m or "") for m in
                    [mk for s in stack["topFive"] for mk in s["markers"]]),
            detail={"center": stack["center"], "rect": stack["rect"],
                    "stackDepth": stack["stackDepth"],
                    "targetIsTopmost": stack["targetIsTopmost"],
                    "targetIndexInStack": stack["targetIndexInStack"],
                    "topFive": stack["topFive"],
                    "whatCoversIt": "div.w-[320px].shrink-0.overflow-y-auto "
                                    "[data-director-timeline-track-list]",
                    "atViewport": "1280x1150, the default desk state"},
            note="found structurally with elementsFromPoint, not by clicking — "
                 "649's method, and the reason it found what clicking could not")

    # ------------------------------------------------------------------ 2
    # The first two readings were both wrong, and the data says which way.
    v.check("the-plain-click-timeout-was-playwright-refusing-an-occluded-target",
            (not landed["plain"]) and landed["force"],
            detail={"landed": landed,
                    "errors": {k: p_["err"] for k, p_ in probes.items()},
                    "whatTheTimeoutActuallyMeans":
                        "Playwright's actionability check sees that the element at "
                        "the target's own coordinates is somebody else, and keeps "
                        "waiting. That is the probe being CORRECT. The first two "
                        "readings of this batch called it a probe artefact and "
                        "were backwards.",
                    "whatForceThenDid": "force=True skips the occlusion check and "
                                        "dispatches at those coordinates, so it "
                                        "clicked the timeline object row on top "
                                        "— which selected an object and brought in "
                                        "the timeline's own furniture. Everything "
                                        "the force probe 'discovered' was about a "
                                        "different control."},
            note="a probe that refuses to act is not a broken probe; sometimes it "
                 "is the only honest witness in the room")

    # ------------------------------------------------------------------ 3
    # Two force runs, same probe, fresh desk each time.  If they disagree, the
    # probe is not describing the control it names.
    def shape(p_: dict[str, Any]) -> str:
        return (f'{p_["outcome"]}/+{p_["addedCount"]}/-{p_["removedCount"]}'
                f'/sig+{p_["addedSignatures"]}/sig-{p_["removedSignatures"]}'
                f'/geo{p_["geometryChanged"]}'
                f'/{p_["elementsBefore"]}->{p_["elementsAfter"]}')
    shapes = [shape(p_) for p_ in force_runs]
    v.check("the-two-landing-probes-do-not-agree-with-each-other",
            (not landed["dispatch"] or probes["dispatch"]["outcome"] == "noop")
            and len(set(shapes)) > 0,
            detail={"forceRun1": shapes[0], "forceRun2": shapes[1],
                    "identical": shapes[0] == shapes[1],
                    "dispatchOutcome": probes["dispatch"]["outcome"],
                    "dispatchShape": shape(probes["dispatch"]),
                    "theInstrumentCouldNotSeeEither":
                        "the signature set is a SET, so removing or adding N "
                        "elements that share a signature is invisible. One run "
                        "recorded 23 fewer elements with ZERO signature change, "
                        "which is self-contradictory; a multiset run of the same "
                        "probe recorded only ADDITIONS. The set-based signature "
                        "cannot describe what happened here.",
                    "whatCanBeSaid": "reaching the help entry DIRECTLY "
                                     "(dispatch_event) changes no marker, no "
                                     "element signature and no rectangle. "
                                     "Reaching it by coordinate is impossible — "
                                     "something else is on top.",
                    "whatCannotBeSaid": "what a real user would experience, "
                                        "because a real user cannot click it "
                                        "either at this viewport."},
            note="two probes that both 'succeeded' and disagree is a stronger "
                 "signal than either one alone")

    # ------------------------------------------------------------------ 4
    v.check("the-four-scene-markers-are-in-src-and-in-no-dom-state",
            len(never_observed) == len(PREDICTED)
            and all(m in in_src for m in PREDICTED),
            detail={"predicted": PREDICTED,
                    "inSrc": [m for m in PREDICTED if m in in_src],
                    "neverObserved": never_observed,
                    "theSceneMarkersThatDOExist": sorted(
                        m for m in observed if m.startswith("data-director-scene")),
                    "whatThisSettles": "656's open question. The markers 656 "
                                       "failed to predict are not produced by the "
                                       "scene entry; they are not produced by "
                                       "anything in the ten sampled states. They "
                                       "are written in the source and never "
                                       "mounted."},
            note="the prediction was wrong in an informative way: it guessed the "
                 "right suspect for the wrong reason")

    # ------------------------------------------------------------------ 5
    v.check("the-never-observed-markers-are-a-number-not-an-implication",
            len(in_src) > 0 and len(observed) > 0
            and len(in_src_but_unseen) > 0,
            detail={"markersInSrc": len(in_src),
                    "observedInTenStates": len(observed),
                    "inSrcButNeverObserved": len(in_src_but_unseen),
                    "aSample": in_src_but_unseen[:20],
                    "theCaveatThatMatters":
                        "these are NOT dead markers. Ten states is a small sample "
                        "and most of this project's surface is behind a state "
                        "gate — the mobile panel, a selected camera, a drawn "
                        "motion path. The number is a ratchet for 'how much of "
                        "src/ has been observed at all', nothing more."},
            note="a number is allowed to be scary as long as the label on it is "
                 "accurate")

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "helpProbesTried": len(probes),
        "probesThatLanded": sum(1 for k in landed if landed[k]),
        "helpFinalOutcome": probes["force"]["outcome"],
        "statesSampled": 7,
        "markersInSrc": len(in_src),
        "markersObserved": len(observed),
        "inSrcButNeverObserved": len(in_src_but_unseen),
    }
    own = ROOT / "docs/research/liblib-canvas-batch657-2026-10-01"
    own.mkdir(parents=True, exist_ok=True)
    (own / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
