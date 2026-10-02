#!/usr/bin/env python3
"""batch 671 验收：「假阴性 0 格」是**结构性**的，还是碰巧

## 起点

670 在 19,680 格（164 档宽度 × 120 枚视口内控件）上量到**假阴性 0**：
「rect 说没挡、实际挡了」一格也没有。668 那 ≈1.0px 的签名只在 2 格出现过
（`描述想搭建的场景` @ 1405/1406），而那 2 格都被另一枚盒救回了。

**但 664 早就记过：空集不算证据。** 一个 0 必须回答「它为什么是 0」，
否则它和「没测到」无法区分。本批就是去回答这个。

## 结构性论证（先写成式子，再去量）

检视器那三枚的**命中区左沿**比 rect 左沿靠左 ≈1.0px（668/669 实测），
所以「命中区含某点、rect 不含」的那条 1px 条带是

```
S = (rectLeft − 1, rectLeft) = (W − 282, W − 281)
```

而**救场的那枚**是视口自己的 `div.absolute.inset-0`，它的 rect 右沿
**也是 `W − 281`**（666/668 逐档测过）。

⟹ **S 整条落在救场者的 rect 之内**（`x < W − 281` 对 S 的每一点都成立）
⟹ 假阴性在这套几何下**不可能出现**。**这是包含关系，不是巧合。**

本批不去论证它，而是**在 S 上密集采样去证伪它**：若存在任一采样点
「某枚在栈里、而无任何 pe:auto 盒的 rect 含它」，那 670 的 0 就是运气。

## 三件事

1. **密集采样**：对三枚盒各取 S 内 **0.01px 步长**（每条 100 个点）×
   三个宽度，逐点记「谁在栈里」与「谁的 rect 含它」。
2. **救场的右界**：量出「rect 仍含住」的最大 x —— 应当就是 `W − 281`。
3. **条件式**：写下「若要出现假阴性，必须同时满足什么」，并逐条核对读数。

**不声称**：那 ≈1.0px 的成因；以及这条包含关系在换掉 `px-3`、换掉
`border-l`、或把控件挪出视口面之后是否还成立。
"""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch671-2026-10-01"

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

WIDTHS = (1280, 1405, 1600)
STEP = 0.01
TARGETS = ["描述想搭建的场景", "上传图片", "发送"]

JS = r"""(arg) => {
  const scope = document.querySelector('[data-director-workspace]') || document.body;
  const ident = (e) => (e.getAttribute('class') || '').trim().split(/\s+/).slice(0, 5).join('.')
                   || '<' + e.tagName.toLowerCase() + '>';
  const raw = (v) => Math.round(v * 1000) / 1000;

  let el = null;
  for (const c of scope.querySelectorAll('button,input')) {
    if ((c.getAttribute('aria-label') || c.getAttribute('placeholder') || '')
        === arg.target) { el = c; break; }
  }
  if (!el) return {W: innerWidth, found: false};

  // 三枚检视器盒：aside / section / column，按结构定位
  let col = null, area = -1;
  for (const e of scope.querySelectorAll('div')) {
    const c = e.getAttribute('class') || '';
    if (!(c.includes('min-h-0') && c.includes('flex-1') && c.includes('overflow-y-auto'))) continue;
    const b = e.getBoundingClientRect(); const a = b.width * b.height;
    if (a > area) { area = a; col = e; }
  }
  const sec = col.parentElement;
  const aside = sec.parentElement;
  const trio = [aside, sec, col].filter(Boolean);

  // 救场者：视口自己的面（与 668 量到的那枚 div.absolute.inset-0 同盒）
  let surface = null;
  for (const e of scope.querySelectorAll('div')) {
    if ((e.getAttribute('class') || '').trim() !== 'absolute inset-0') continue;
    surface = e; break;
  }

  const r = el.getBoundingClientRect();
  const cy = raw(r.y + r.height / 2);

  // pe:auto 且零尺寸除外 —— rect 通道的候选总体
  const all = [];
  for (const e of scope.querySelectorAll('*')) {
    const s = getComputedStyle(e);
    if (s.pointerEvents === 'none') continue;
    const b = e.getBoundingClientRect();
    if (b.width <= 0 || b.height <= 0) continue;
    all.push({el: e, l: b.left, rr: b.right, t: b.top, b: b.bottom, ident: ident(e)});
  }
  const coverersOf = (x, y) => all.filter((a) => x >= a.l && x < a.rr && y >= a.t && y < a.b)
                             .map((a) => a.ident);

  const uniq = (xs) => [...new Set(xs)].sort();
  const rows = [];
  for (const box of trio) {
    const b = box.getBoundingClientRect();
    const left = raw(b.left);
    // S = (left − 1, left)，向内取 0.01 的整倍数
    const samples = [];
    for (let k = 1; k <= 100; k++) {
      const x = raw(left - 1 + k * (1 / 100));
      if (x >= left) break;
      const stack = document.elementsFromPoint(x, cy);
      const inStack = stack.some((h) => h === box || box.contains(h));
      const covers = coverersOf(x, cy);
      samples.push({x: x, boxInStack: inStack, coverers: covers});
    }
    rows.push({box: ident(box), rectLeft: left, rectRight: raw(b.right),
               n: samples.length,
               inStackCount: samples.filter((s) => s.boxInStack).length,
               // 命中说挡、而**没有任何** rect 候选含它 —— 假阴性
               falseNegatives: samples.filter((s) => s.boxInStack && s.coverers.length === 0),
               rescuedBy: uniq(samples.flatMap((s) => s.coverers)),
               firstXWithCover: (samples.find((s) => s.coverers.length > 0) || {}).x,
               lastXWithBoxInStack: (samples.filter((s) => s.boxInStack).pop() || {}).x});
  }
  return {W: innerWidth, found: true, target: arg.target, cy: cy,
          cx: raw(r.x + r.width / 2),
          surfaceRect: surface ? [raw(surface.getBoundingClientRect().left),
                                  raw(surface.getBoundingClientRect().right)] : null,
          surfaceIdent: surface ? ident(surface) : null,
          step: arg.step, rows: rows};
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
              + (f"  {str(detail)[:150]}" if detail else "")
              + (f"  [{note[:96]}]" if note else ""))


def main() -> int:
    v = Verifier()
    cells: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        page = br.new_page(viewport={"width": 1280, "height": 1150}, device_scale_factor=1)
        b617.open_desk(page)
        for w in WIDTHS:
            page.set_viewport_size({"width": w, "height": 1150})
            page.wait_for_timeout(90)
            page.evaluate("() => { for (const el of document.querySelectorAll("
                          "'nextjs-portal')) el.remove(); }")
            page.mouse.move(5, 5)
            page.wait_for_timeout(60)
            for t in TARGETS:
                cells[f"{w}:{t}"] = page.evaluate(JS, {"target": t, "step": STEP})
        page.close()
        br.close()

    keys = list(cells)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"stage": "raw-readings", "cells": cells}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    all_rows = [(k, row) for k in cells for row in cells[k]["rows"]]
    fn = [(k, r) for k, r in all_rows if r["falseNegatives"]]
    surfaces = {k: cells[k]["surfaceRect"] for k in keys}
    surface_ids = {cells[k]["surfaceIdent"] for k in keys}
    # 每条带里「盒在栈里」的样本数：应当 > 0（否则这条带根本没被走到）
    band_hits = {(k, r["box"]): (r["inStackCount"], r["n"]) for k, r in all_rows}

    v.check("every-sample-in-the-one-pixel-strip-is-still-covered-by-some-rect",
            not fn,
            detail={"sampledBoxes": len(all_rows), "samplesPerBox": STEP,
                    "falseNegativeSamples": [(k, r["box"], len(r["falseNegatives"]))
                                             for k, r in fn][:6],
                    "totalSamples": sum(r["n"] for _, r in all_rows),
                    "totalSamplesWhereBoxIsInStack":
                        sum(r["inStackCount"] for _, r in all_rows)},
            note="the falsification attempt: if any sample had the box in the hit "
                 "stack and NO pe:auto rect covering it, 670's zero was luck")

    # 每条带的救场者：取 9 次测量（三宽度 × 三控件）的交集，证明不是偶然
    resc_by_box: dict[str, set[str]] = {}
    for k in keys:
        for row in cells[k]["rows"]:
            s = resc_by_box.setdefault(row["box"], set())
            s.intersection_update(row["rescuedBy"]) if s else s.update(row["rescuedBy"])
    surf_minus_left: dict[str, set[float]] = {}
    for k in keys:
        for row in cells[k]["rows"]:
            surf_minus_left.setdefault(row["box"], set()).add(
                round(surfaces[k][1] - row["rectLeft"], 3))
    ASIDE = "absolute.-top-9.bottom-0.right-0.z-30"
    SEC = "flex.h-full.min-h-0.flex-col.border-l"
    COL = "min-h-0.flex-1.overflow-y-auto"
    SURF = "absolute.inset-0"

    v.check("the-rescuer-differs-by-box-the-two-outer-ones-are-rescued-by-the-surface",
            SURF in resc_by_box.get(ASIDE, set()) and SURF in resc_by_box.get(SEC, set())
            and ASIDE in resc_by_box.get(COL, set())
            and surf_minus_left.get(ASIDE) == {0.0}
            and surf_minus_left.get(SEC) == {0.0}
            and surf_minus_left.get(COL) == {-1.0},
            detail={"rescuedByIntersection": {k: sorted(v)[:6]
                                              for k, v in resc_by_box.items()},
                    "surfaceRightMinusTrioLeft": {k: sorted(v) for k, v in
                                                 surf_minus_left.items()},
                    "boxes": {"aside": ASIDE, "section": SEC, "column": COL},
                    "surfaceIdent": sorted(surface_ids)},
            note="the column's strip is NOT covered by the surface (its rect starts "
                 "1px to the right of the surface's) — it is covered by the aside, "
                 "whose rect starts exactly 1px to the column's left")

    v.check("the-strip-is-actually-walked-at-every-width",
            all(h > 0 and n > 0 for (h, n) in band_hits.values()),
            detail={"bands": len(band_hits),
                    "minInStackSamples": min(h for h, _ in band_hits.values()),
                    "samplesPerBand": sorted({n for _, n in band_hits.values()}),
                    "perBand": {f"{k}|{b}": list(v) for (k, b), v in
                                list(band_hits.items())[:6]}},
            note="an empty strip would make the check above vacuous — prove the "
                 "strip is non-empty before claiming the containment holds on it")

    v.check("the-rescuer-is-the-viewport-surface-not-an-inspector-box",
            all(cells[k]["surfaceIdent"] == "absolute.inset-0" for k in keys)
            and all(r["box"] != "absolute.inset-0" for _, r in all_rows),
            detail={"surfaceIdent": sorted(surface_ids),
                    "boxesSampled": sorted({r["box"] for _, r in all_rows}),
                    "rescuedBy": sorted({i for _, r in all_rows for i in r["rescuedBy"]})},
            note="670 attributed the rescue to this element; confirm it and confirm "
                 "it is not one of the boxes that needed rescuing")

    out = {"widths": list(WIDTHS), "targets": TARGETS, "step": STEP,
           "boxesSampled": sorted({r["box"] for _, r in all_rows}),
           "totalSamples": sum(r["n"] for _, r in all_rows),
           "totalSamplesWhereBoxIsInStack": sum(r["inStackCount"] for _, r in all_rows),
           "falseNegativeSamples": len(fn),
           "rescuedByIntersection": {k: sorted(v) for k, v in resc_by_box.items()}}
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "cells": cells, "checks": v.result},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
