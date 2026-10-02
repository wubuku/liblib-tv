#!/usr/bin/env python3
"""batch 676 验收：673 咬到的「`收起属性` 按名字当键」不是活缺陷 —— 但它露出一个更尖的洞

## 起点

673 用 `ast` 普查出：`收起属性` **活体有 2 枚**，却被 **4 个历史验收器**
（593 / 661 / 664 / 667）当键用过，其中 661/664/667 的推理**正是按名字做的**。
673 把 `收起属性` 列为「最严重的被咬名字」。

本批去问：**这个撞车有没有真的发生过？**

## 三条读数

### 1. 撞车没有发生 —— 但不是因为判据分得清，而是因为其中一枚从未进入视野

在 667 自己的 6 个视口格（1280×720 / 1280×1150 / 1366 / 1440 / 1600 / 1920 × 1150）里，
凡是「按 667 的口径」（每个控件中心、`elementFromPoint` 命中外人）读到的
`收起属性` 命中者，**6 格全部是 `data-director-timeline-object-row=director-camera-main`
那一枚**；另一枚（`director-character-lead`）**一次都没出现过**。

两枚同名、同列（`x=8`）、同尺寸（20×20），**只有 y 随窗高走**（底锚定）：
`camera-main` 恒在 `H−39..H−19`（**正是 662 的在案读数**），
`character-lead` 恒在 `H−103..H−83`。而 `帮助` 的探测中心恒落在下面那枚上。

**所以 664/667 的 `hitSays == "收起属性"` 从来不需要区分两者 —— 它一直只见到一枚。**

### 2. 没出现 ≠ 那枚坏了：两枚在自身 3×3 上都是 9/9

`director-character-lead` 那一枚从未被外人命中，但**它自己是完全可点的**
（自身盒内 3×3 九个采样点，6 格全部 9/9 命中自己）。
**本批不把它读成「潜伏缺陷」** —— 它没坏；它是**没被看过**。

### 3. 真正的洞：这套判据对它是单向的

用**运行时注入**（不改 `src/`）给某一枚按钮加 `pointer-events:none`，
再重跑 667 的那条名字判据：

- 注入 **`director-character-lead`（没被看过的那个）** ⟹ 667 的判据**逐字不变**；
- 注入 **`director-camera-main`（被看过的那个）** ⟹ 判据**立刻改变**。

两条一起才是证据：只跑第一条，它可能只是「注入没生效」。

**结论**：673 说的「按名字当键会被同名控件咬到」在这几批里是**潜在**风险，不是活缺陷；
但**同一条判据只覆盖了两枚中的一枚** —— 另一枚坏掉不会有任何断言变红。
**这与折叠无关，是「探测点只取控件中心」这一条口径的覆盖边界。**

## 不声称

不声称 `director-character-lead` 那枚按钮在源站有任何对应行为（未取证）；
不声称 664/667 的结论因此是错的（它们在**自己那枚**按钮上是对的）；
不声称注入等价于真实的遮挡（`pointer-events:none` 是一种构造，不是源站行为）；
不改任何历史批次 —— 本批只补上「这套判据的覆盖边界只有一枚」这个事实。
"""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch676-2026-10-01"

# **667 自己的 6 格** —— 不换格子，才能谈「667 的判据看不看得见」
CELLS = [(1280, 720), (1280, 1150), (1366, 1150), (1440, 1150),
         (1600, 1150), (1920, 1150)]
# 注入实验只跑两格：一格是 667 名单里最挤的，一格是最宽的
INJECT_CELLS = [(1280, 1150), (1920, 1150)]

TOGGLE_NAME = "收起属性"
HELP_NAME = "帮助"

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

JS = r"""() => {
  const scope = document.querySelector('[data-director-workspace]') || document.body;
  const SEL = 'button, [role=button], [role=tab], [role=switch], [role=slider],'
    + ' [role=menuitem], input, select, textarea, a[href],'
    + ' [tabindex]:not([tabindex="-1"])';
  const cs = (e) => getComputedStyle(e);
  const lab = (e) => e.getAttribute('aria-label') || e.getAttribute('placeholder')
    || (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 24)
    || e.getAttribute('title') || '<' + e.tagName.toLowerCase() + '>';
  const rowOf = (e) => { for (let n = e; n && n !== document.body; n = n.parentElement) {
      const r = n.getAttribute && n.getAttribute('data-director-timeline-object-row');
      if (r) return r; } return '-'; };
  const vis = (e) => { const s = cs(e);
    if (s.display === 'none' || s.visibility === 'hidden') return false;
    const b = e.getBoundingClientRect();
    return b.width > 0 && b.height > 0 && parseFloat(s.opacity) !== 0; };

  const toggles = [];
  for (const e of scope.querySelectorAll(SEL)) {
    if (!vis(e)) continue;
    if ((e.getAttribute('aria-label') || '') !== '收起属性') continue;
    const r = e.getBoundingClientRect();
    toggles.push({el: e, box: [Math.round(r.x), Math.round(r.y),
                                Math.round(r.width), Math.round(r.height)],
                  row: rowOf(e)});
  }

  // 自身 3x3：证明「这枚按钮自己可点」，也用来验注入确实生效
  const selfHits = toggles.map((t) => {
    const [x, y, w, h] = t.box;
    let n = 0;
    for (const fx of [0.25, 0.5, 0.75]) for (const fy of [0.25, 0.5, 0.75]) {
      const hit = document.elementFromPoint(Math.round(x + w * fx) + 0.5,
                                            Math.round(y + h * fy) + 0.5);
      if (hit && (hit === t.el || t.el.contains(hit))) n += 1;
    }
    return n;
  });

  // 667 的口径：每个控件中心，命中者是外人时记下命中者的名字 + 是哪一枚
  const foreign = [];
  for (const el of scope.querySelectorAll(SEL)) {
    if (!vis(el)) continue;
    const r = el.getBoundingClientRect();
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    if (cx < 0 || cy < 0 || cx > innerWidth || cy > innerHeight) continue;
    const hit = document.elementFromPoint(cx, cy);
    if (!hit) continue;
    if (hit === el || el.contains(hit) || hit.contains(el)) continue;
    foreign.push({control: lab(el), hitLabel: lab(hit),
                  hitTag: hit.tagName.toLowerCase(), hitRow: rowOf(hit),
                  toggleIndex: toggles.findIndex((t) => t.el === hit)});
  }

  // 667 那条断言本身：`帮助` 中心被谁吃掉
  let helpVerdict = null, helpCentre = null;
  for (const el of scope.querySelectorAll(SEL)) {
    if (!vis(el) || lab(el) !== '帮助') continue;
    const r = el.getBoundingClientRect();
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    helpCentre = [Math.round(cx), Math.round(cy)];
    const hit = document.elementFromPoint(cx, cy);
    helpVerdict = hit ? lab(hit) : null;
    break;
  }
  return {vw: innerWidth, vh: innerHeight,
          toggles: toggles.map((t) => ({box: t.box, row: t.row})),
          selfHits, foreign, helpVerdict, helpCentre};
}"""

INJECT_JS = r"""(row) => {
  for (const e of document.querySelectorAll('[data-director-workspace] button, '
      + '[data-director-workspace] [role=button]')) {
    if (e.getAttribute('aria-label') !== '收起属性') continue;
    let hit = null;
    for (let n = e; n && n !== document.body; n = n.parentElement) {
      const r = n.getAttribute && n.getAttribute('data-director-timeline-object-row');
      if (r) { hit = r; break; }
    }
    if (hit === row) { e.style.pointerEvents = 'none'; return true; }
  }
  return false;
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
    base: dict[str, Any] = {}
    inject: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        for (w, h) in CELLS:
            page = br.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
            b617.open_desk(page)
            _clean(page)
            base[f"{w}x{h}"] = page.evaluate(JS)
            page.close()
        for (w, h) in INJECT_CELLS:
            for row in ("director-character-lead", "director-camera-main"):
                page = br.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
                b617.open_desk(page)
                _clean(page)
                applied = page.evaluate(INJECT_JS, row)
                page.wait_for_timeout(60)
                inject[f"{w}x{h}|{row}"] = {"injectedRow": row, "applied": applied,
                                            **page.evaluate(JS)}
                page.close()
        br.close()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"stage": "raw-readings", "baseline": base, "injection": inject},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    keys = list(base)
    rows = {k: [t["row"] for t in base[k]["toggles"]] for k in keys}
    boxes = {k: [t["box"] for t in base[k]["toggles"]] for k in keys}
    seen: set[int] = set()
    per_cell: dict[str, Any] = {}
    for k in keys:
        hits = [f for f in base[k]["foreign"] if f["toggleIndex"] >= 0]
        per_cell[k] = {"toggleForeignHits": [{"control": f["control"],
                                              "label": f["hitLabel"],
                                              "row": f["hitRow"],
                                              "index": f["toggleIndex"]} for f in hits],
                       "helpVerdict": base[k]["helpVerdict"]}
        seen |= {f["toggleIndex"] for f in hits}

    # 注入实验：基线 / 看不见的那枚 / 看得见的那枚
    inj: dict[str, Any] = {}
    for (w, h) in INJECT_CELLS:
        k = f"{w}x{h}"
        bl = base[k]
        row_unseen, row_seen = rows[k][0], rows[k][1]
        rec = {"baseline": {"helpVerdict": bl["helpVerdict"], "selfHits": bl["selfHits"]}}
        for tag, row in (("unseen", row_unseen), ("seen", row_seen)):
            r = inject[f"{k}|{row}"]
            rec[tag] = {"row": row, "applied": r["applied"],
                        "helpVerdict": r["helpVerdict"], "selfHits": r["selfHits"]}
        inj[k] = rec

    v.check("two-toggles-share-the-name-same-column-same-size-and-are-bottom-anchored",
            all(len(base[k]["toggles"]) == 2 for k in keys)
            and len({tuple(rows[k]) for k in keys}) == 1
            and rows[keys[0]][0] != rows[keys[0]][1]
            and len({(t[0], t[2], t[3]) for k in keys for t in boxes[k]}) == 1
            and all(boxes[k][1][1] == base[k]["vh"] - 39
                    and boxes[k][1][1] + boxes[k][1][3] == base[k]["vh"] - 19
                    for k in keys),
            detail={"rows": rows, "boxes": boxes,
                    "distinctXWidthHeight": sorted({(t[0], t[2], t[3])
                                                    for k in keys for t in boxes[k]}),
                    "closes662":
                        "662 recorded 收起属性 as sitting at H−39..H−19. The "
                        "director-camera-main button is exactly that one, in all six "
                        "cells; the character-lead one is at H−103..H−83."},
            note="only y moves with viewport height — same x=8, same 20x20, "
                 "bottom-anchored, which is why the 帮助 probe always lands on one of them")

    v.check("only-one-of-the-two-ever-appears-as-a-foreign-hitter-in-667s-own-six-cells",
            seen == {1} and all(c["helpVerdict"] == TOGGLE_NAME
                                for c in per_cell.values()),
            detail={"toggleIndicesEverSeen": sorted(seen),
                    "perCell": per_cell,
                    "reading":
                        "in all six cells the 收起属性 hitter is the "
                        "data-director-timeline-object-row=director-camera-main button; "
                        "the character-lead button never appears"},
            note="673's collision is a LATENT risk in these six cells, not a live one")

    v.check("the-never-seen-toggle-is-not-broken-it-is-fully-clickable",
            all(all(n == 9 for n in base[k]["selfHits"]) for k in keys),
            detail={"selfHitsPerCell": {k: base[k]["selfHits"] for k in keys},
                    "probes": "3x3 inside each 20x20 button's own box"},
            note="do not read 'never occludes anyone' as 'is broken' — it is 9/9")

    v.check("breaking-the-never-seen-toggle-leaves-667s-name-based-verdict-unchanged",
            all(inj[k]["unseen"]["applied"] for k in inj)
            and all(inj[k]["unseen"]["helpVerdict"] == inj[k]["baseline"]["helpVerdict"]
                    for k in inj),
            detail={k: {"baseline": inj[k]["baseline"]["helpVerdict"],
                        "injected": inj[k]["unseen"]["helpVerdict"],
                        "injectedRow": inj[k]["unseen"]["row"],
                        "selfHitsBefore": inj[k]["baseline"]["selfHits"],
                        "selfHitsAfter": inj[k]["unseen"]["selfHits"]}
                    for k in inj},
            note="the character-lead button can be made unclickable and 667's assertion "
                 "still holds — it never looks at that element")

    v.check("breaking-the-seen-toggle-does-change-it-so-the-previous-check-is-not-vacuous",
            all(inj[k]["seen"]["applied"] for k in inj)
            and all(inj[k]["seen"]["helpVerdict"] != inj[k]["baseline"]["helpVerdict"]
                    for k in inj),
            detail={k: {"baseline": inj[k]["baseline"]["helpVerdict"],
                        "injected": inj[k]["seen"]["helpVerdict"],
                        "injectedRow": inj[k]["seen"]["row"]} for k in inj},
            note="positive control: without it, check 4 could just mean 'the injection "
                 "did not work'")

    v.check("both-injections-are-not-no-ops-on-the-injected-button-itself",
            all(inj[k][tag]["selfHits"][idx] == 0
                for k in inj
                for tag, idx in (("unseen", 0), ("seen", 1))),
            detail={k: {tag: {"row": inj[k][tag]["row"],
                              "selfHits": inj[k][tag]["selfHits"]}
                        for tag in ("unseen", "seen")} for k in inj},
            note="the injected button loses all 9 of its own hits in both cases — so the "
                 "injection always bit; it was 667's probe that never looked")

    out = {"cells": keys, "injectCells": [f"{w}x{h}" for (w, h) in INJECT_CELLS],
           "toggleRows": rows, "toggleBoxes": boxes,
           "toggleIndicesEverSeenAsForeignHitter": sorted(seen),
           "perCell": per_cell, "injection": inj,
           "judged": sum(len(base[k]["foreign"]) for k in keys)
                     + sum(len(r["foreign"]) for r in inject.values())}
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "baseline": base, "injection": inject,
                    "checks": v.result}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
