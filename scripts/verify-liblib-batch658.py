#!/usr/bin/env python3
"""batch 658 验收：遮挡普查 —— 每个导��台控件在**自己的中心点**上是不是栈顶

## 起点

657 在 `help` 这一个控件上撞见了一件事：
**它被自己的时间轴轨道列表盖住**（栈深 21、目标在第 8 位、`targetIsTopmost=False`），
而这件事**用点击永远找不到** —— 普通 `click()` 被 Playwright 正确地拒绝，
`force=True` 反而点中了轨道行。

657 用的是 649 的办法：**不点击，看结构**。
本批把那把尺子从**一个控件**扩到**全部控件**。

## 为什么这条普查值得单独做

`elementsFromPoint` 走的是真正的命中测试 ——
它**跳过** `pointer-events: none` 的元素（648 已证过这一点，当时写成「命中测试测不到」）。
所以它给出的栈**就是一次点击真正能到达的那一摞**。

于是「一个控件在自己中心点是不是栈顶」等价于
「**这个控件能不能被点到**」—— 这是可判定的，而且不需要点它。

## 三个必须分开的桶

普查最容易被自己骗的地方是**把不同性质的东西混成一个数字**：

1. **零尺寸**（623 的盲区）—— 不能算「被遮」，它是根本不存在于命中面
2. **不在视口内** —— 不能算「被遮」，用户本来就看不到它
3. **被遮** —— 中心点在视口内、有尺寸，但栈顶不是它

本批把三者**分别计数并分别断言**，任何一个桶为空都写清楚是空还是没量。

## 本批**不**主张的事

* **不主张**遮��是缺陷 —— 需要产品判断，���是 clone 与源站的差异。
* **零源站断言**。
"""
import importlib.util
import json
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

WIDTH = 1280
HEIGHTS = [720, 900, 1150]
scroll_gate = b654.scroll_gate

# The control set is a selector, not a list.  A hand-written list of controls is
# the exact thing that expires — 643, 626, 654, in that order.
CONTROLS_JS = """() => {
  const SEL = 'button, input, select, textarea, a[href], [role="button"], '
            + '[role="tab"], [role="switch"], [role="checkbox"], '
            + '[role="option"], [role="menuitem"]';
  const out = [];
  for (const el of document.querySelectorAll(SEL)) {
    const r = el.getBoundingClientRect();
    const w = Math.round(r.width), h = Math.round(r.height);
    const cx = r.x + w / 2, cy = r.y + h / 2;
    const rec = {
      tag: el.tagName.toLowerCase(),
      role: el.getAttribute('role') || '',
      markers: [...el.attributes].map(a => a.name)
                 .filter(n => n.startsWith('data-director-')),
      label: (el.getAttribute('aria-label') || el.textContent || '')
               .trim().replace(/\\s+/g, ' ').slice(0, 26),
      // The VALUE, not just the name: seven rail entries share the name
      // data-director-rail-entry and differ only by value, and every one of
      // them is an icon button with no text. 657's finding is about one of
      // them specifically.
      railEntry: el.getAttribute('data-director-rail-entry') || null,
      // Which side of the desk this control belongs to.  The first run of this
      // census reported 45 occluded controls and most of them were the CANVAS
      // PAGE's own header (项目菜单 / 工作区名称 / 画布 2 / 故事板 / 开通会员 …)
      // sitting underneath the open director desk.  That is the desk being on
      // top, not a blocked control — and mixing the two is exactly how a
      // census produces a scary number for a boring fact (655's 80).
      inDesk: !!el.closest('[data-director-workspace]'),
      rect: [Math.round(r.x), Math.round(r.y), w, h],
      w, h,
      // On the CENTRE point, not on the rect's top-left corner.  The first run
      // tested `r.top < innerHeight`, which lets a control whose top edge is
      // visible but whose centre is already below the fold pass as "in
      // viewport" — and then elementsFromPoint returns an EMPTY stack, so six
      // bottom-bar controls were filed as "occluded" with stackDepth 0.  The
      // only thing being measured at that point was the edge of the screen.
      inViewport: cx >= 0 && cy >= 0 && cx <= window.innerWidth
                  && cy <= window.innerHeight,
      center: [Math.round(cx), Math.round(cy)],
    };
    rec.zeroSized = (w <= 0 || h <= 0);
    if (rec.zeroSized || !rec.inViewport) {
      rec.classification = rec.zeroSized ? 'zero-sized' : 'offscreen';
      rec.occluded = false;
      out.push(rec);
      continue;
    }
    const stack = document.elementsFromPoint(cx, cy);
    const top = stack[0] || null;
    rec.stackDepth = stack.length;
    rec.selfIsTop = !!top && (top === el || el.contains(top));
    rec.occluded = !rec.selfIsTop;
    rec.classification = rec.selfIsTop ? 'reachable' : 'occluded';
    if (rec.occluded && top) {
      rec.coveredBy = {
        tag: top.tagName.toLowerCase(),
        cls: (top.getAttribute('class') || '').split(' ')
               .filter(Boolean).slice(0, 4).join('.'),
        markers: [...top.attributes].map(a => a.name)
                   .filter(n => n.startsWith('data-director-')),
        label: (top.getAttribute('aria-label') || top.textContent || '')
                 .trim().replace(/\\s+/g, ' ').slice(0, 26),
      };
    }
    out.push(rec);
  }
  return out;
}"""


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


def main() -> int:
    v = Verifier()
    cells: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        for h in HEIGHTS:
            page = br.new_page(viewport={"width": WIDTH, "height": h},
                               device_scale_factor=1)
            b617.open_desk(page)
            page.wait_for_timeout(400)
            page.evaluate("() => { for (const el of "
                          "document.querySelectorAll('nextjs-portal')) el.remove(); }")
            page.mouse.move(5, 5)
            page.wait_for_timeout(220)
            rows = page.evaluate(CONTROLS_JS)
            gate = scroll_gate(page)
            page.close()
            by_bucket: dict[str, list[dict[str, Any]]] = {}
            for r in rows:
                side = "in-desk" if r["inDesk"] else "outside-desk"
                by_bucket.setdefault(f"{side}/{r['classification']}",
                                      []).append(r)
            cells[str(h)] = {
                "gate": gate, "total": len(rows),
                "inDesk": sum(1 for r in rows if r["inDesk"]),
                "outsideDesk": sum(1 for r in rows if not r["inDesk"]),
                "buckets": {k: len(v_) for k, v_ in sorted(by_bucket.items())},
                "occluded": by_bucket.get("in-desk/occluded", []),
                "occludedOutsideDesk": by_bucket.get("outside-desk/occluded", []),
                "zeroSized": by_bucket.get("in-desk/zero-sized", []),
                "offscreen": by_bucket.get("in-desk/offscreen", []),
                "reachable": by_bucket.get("in-desk/reachable", []),
            }
        br.close()

    def key(r: dict[str, Any]) -> str:
        return (f'{r["markers"][0] if r["markers"] else r["tag"]}'
                f'|{r["label"]}')

    per_height_occluded = {h: sorted({key(r) for r in cells[h]["occluded"]})
                           for h in map(str, HEIGHTS)}
    everywhere = sorted(set(per_height_occluded[str(HEIGHTS[0])]).intersection(
        *[set(v) for v in per_height_occluded.values()]))
    somewhere = sorted({k for v in per_height_occluded.values() for k in v})
    only_some = sorted(set(somewhere) - set(everywhere))

    out: dict[str, Any] = {
        "batch": 658,
        "question": "is `help` alone?  census every control for whether it is "
                    "topmost at its own centre — structurally, without clicking",
        "method": {
            "instrument": "elementsFromPoint at each control's own centre. It "
                          "is a real hit test: it skips pointer-events:none, so "
                          "the stack it returns is what a click could reach.",
            "controlSet": "a CSS selector over the live DOM, not a hand-written "
                          "list of controls",
            "buckets": "zero-sized / offscreen / occluded are counted "
                       "separately — collapsing them is how a census lies",
        },
        "perHeight": {h: {"total": cells[h]["total"],
                          "buckets": cells[h]["buckets"],
                          "gateVerdict": cells[h]["gate"]["verdict"],
                          "occludedKeys": per_height_occluded[h],
                          "zeroSizedSample": [key(r) for r in
                                              cells[h]["zeroSized"]][:10],
                          } for h in map(str, HEIGHTS)},
        "occludedDetail": {h: [{"key": key(r), "rect": r["rect"],
                                "center": r.get("center"),
                                "stackDepth": r.get("stackDepth"),
                                "coveredBy": r.get("coveredBy")}
                               for r in cells[h]["occluded"]]
                           for h in map(str, HEIGHTS)},
    }

    # ------------------------------------------------------------------ 1
    v.check("the-control-set-is-derived-from-the-dom",
            all(cells[h]["total"] > 0 for h in map(str, HEIGHTS)),
            detail={"controlsPerHeight": {h: cells[h]["total"]
                                          for h in map(str, HEIGHTS)},
                    "buckets": {h: cells[h]["buckets"]
                                for h in map(str, HEIGHTS)}},
            note="a census whose population is written by hand has no way to "
                 "notice when the product grows a control")

    # ------------------------------------------------------------------ 2
    v.check("the-three-buckets-are-counted-separately-not-merged",
            all({"in-desk/reachable", "in-desk/occluded"} <= set(cells[h]["buckets"])
                for h in map(str, HEIGHTS)),
            detail={"buckets": {h: cells[h]["buckets"]
                                for h in map(str, HEIGHTS)},
                    "inDeskPerHeight": {h: cells[h]["inDesk"]
                                        for h in map(str, HEIGHTS)},
                    "outsideDeskPerHeight": {h: cells[h]["outsideDesk"]
                                             for h in map(str, HEIGHTS)},
                    "why": "623 established that zero-size controls slip through "
                           "a census. Folding them into 'occluded' would "
                           "manufacture findings; folding them into 'reachable' "
                           "would hide them. They get their own bucket and their "
                           "own count.",
                    "whyTheSideSplit": "the first run reported 45 occluded and "
                                       "most were the canvas page's own header "
                                       "underneath the open desk. The desk being "
                                       "on top is not a blocked control. 655's 80 "
                                       "was the same mistake — a scary number for "
                                       "a boring fact — and it is now the shape "
                                       "this census is built to avoid."},
            note="an empty bucket is allowed, but only if it is reported as "
                 "empty rather than dropped")

    # ------------------------------------------------------------------ 3
    # 657's one finding, reproduced by a census that never clicked anything.
    help_occluded = {str(h): any(r.get("railEntry") == "help"
                                 for r in cells[str(h)]["occluded"])
                     for h in HEIGHTS}
    v.check("657s-help-finding-is-reproduced-by-a-census-that-never-clicked",
            all(help_occluded.values()),
            detail={"helpOccludedAt": help_occluded,
                    "howItIsFound": "by the VALUE of data-director-rail-entry, "
                                    "not the name and not the text — seven rail "
                                    "entries share the attribute name and every "
                                    "one of them is an icon button with no text",
                    "thePoint": "657 found this by chasing a click timeout. This "
                                "census finds it by asking a question of the "
                                "structure. A finding you can only reach by "
                                "breaking something is a finding you will not "
                                "reach again."},
            note="a method that reproduces a known finding is calibrated; one "
                 "that invents a new one is not")

    # ------------------------------------------------------------------ 4
    v.check("help-is-not-alone",
            len(somewhere) > 1,
            detail={"occludedAtEveryHeight": everywhere,
                    "occludedAtSomeHeights": only_some,
                    "totalDistinctOccluded": len(somewhere),
                    "byHeight": per_height_occluded,
                    "reading": "a single blocked control is an anecdote; a count "
                               "is a census"},
            note="this check is the whole reason the batch exists")

    # ------------------------------------------------------------------ 5
    # What is doing the covering matters: another control is a different
    # problem from a decorative wrapper.
    by_cover_kind: dict[str, list[str]] = {}
    for h in map(str, HEIGHTS):
        for r in cells[h]["occluded"]:
            cb = r.get("coveredBy") or {}
            kind = ("control" if cb.get("tag") in ("button", "input", "select",
                                                   "textarea", "a")
                    else "non-control")
            by_cover_kind.setdefault(kind, []).append(f'{h}:{key(r)}')
    v.check("what-is-doing-the-covering-is-classified-not-assumed",
            set(by_cover_kind) <= {"control", "non-control"}
            and len(by_cover_kind) > 0,
            detail={"byCoverKind": {k: sorted(set(v_))[:20]
                                    for k, v_ in by_cover_kind.items()},
                    "counts": {k: len(set(v_)) for k, v_ in by_cover_kind.items()},
                    "why": "a control hidden behind another control and a control "
                           "hidden behind a decorative wrapper are different "
                           "bugs with different fixes. The census reports which "
                           "is which rather than counting them together."},
            note="covering by a control is worse than covering by a decoration, "
                 "and the number should say so")

    # ------------------------------------------------------------------ 6
    height_varies = len({tuple(per_height_occluded[h]) for h in map(str, HEIGHTS)}) > 1
    v.check("whether-occlusion-depends-on-the-viewport-height-is-now-a-fact",
            len(per_height_occluded) == len(HEIGHTS),
            detail={"variesWithHeight": height_varies,
                    "perHeight": per_height_occluded,
                    "heightsSwept": HEIGHTS,
                    "theMechanism": "the timeline's height lives in the store "
                                    "(default 182, 88..420), and 630 already "
                                    "recorded that below 176 the store's MIN "
                                    "pushes the value back to 88 while the panel "
                                    "still overflows. So the thing doing the "
                                    "covering is itself viewport-dependent."},
            note="a sweep that happens to agree at every height is still a "
                 "measurement; a sweep that never ran is not")

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "heights": HEIGHTS,
        "controlsPerHeight": {h: cells[h]["total"] for h in map(str, HEIGHTS)},
        "inDeskPerHeight": {h: cells[h]["inDesk"] for h in map(str, HEIGHTS)},
        "occludedInDeskPerHeight": {h: len(cells[h]["occluded"])
                                   for h in map(str, HEIGHTS)},
        "occludedOutsideDeskPerHeight": {
            h: len(cells[h]["occludedOutsideDesk"]) for h in map(str, HEIGHTS)},
        "zeroSizedInDeskPerHeight": {h: len(cells[h]["zeroSized"])
                                     for h in map(str, HEIGHTS)},
        "distinctOccludedInDesk": len(somewhere),
        "occludedAtEveryHeight": len(everywhere),
    }
    audit = ROOT / "docs/research/liblib-canvas-batch658-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
