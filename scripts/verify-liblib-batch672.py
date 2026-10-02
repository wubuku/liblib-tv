#!/usr/bin/env python3
"""batch 672 验收：把 66 枚「恒假阳性」按**头顶那枚 rect 候选**归到机制

## 起点

670 在 164 档宽度上量到：每档 77 格带 rect 候选，其中 73–76 格是假阳性
（rect 说挡了、实际没挡，栈顶是自己）。**66 枚控件在每一档上都是假阳性。**

670 只给了一个候选做法（挑 gizmo 轴按钮一族试试），**没有归到机制**。
本批把**整族**归掉：不手写名单，而是对每一格算出「一个只看 rect 的判据
**会先怪谁**」—— 即候选里**在栈中最靠上、且位于自己之下**的那一枚 ——
再按它分组。

**为什么是「最靠上的那一枚」而不是「随便一枚」**：rect 判据不知道层叠，
会随便挑一个 blames；本批用一个**确定且可复算**的规则（栈序最靠上）
把责任落到唯一一枚上，避免「归因」变成挑一个好看的。

## 顺带更正 670 的一处措辞

670 的 README 写「含全部 **9** 个 gizmo 轴按钮 `X/Y/Z 正向·反向`」。
实测：`X/Y/Z 正向·反向` 是 **6** 枚 15×15 的轴按钮；
另有 **3** 枚是 `左右拖动调整 X/Y/Z 轴` 的说明标签。
**轴相关的控件共 9 枚，但轴按钮只有 6 枚。** 历史批次不重写，纠正记在这里。

**不声称**：这些机制在源站有对应物；也不声称「栈序最靠上」是唯一合理的
归因规则 —— 换一条规则会得到另一张表，本批把这一点写进载荷。
"""

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch672-2026-10-01"

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

CELLS = [(1280, 1150), (1440, 1150), (1920, 1150)]
AXIS_BUTTON = r"^[XYZ] (正向|反向)$"
AXIS_LABEL = "左右拖动调整 "

JS = r"""(arg) => {
  const scope = document.querySelector('[data-director-workspace]') || document.body;
  const SEL = 'button, [role=button], [role=tab], [role=switch], [role=slider],'
    + ' [role=menuitem], input, select, textarea, a[href],'
    + ' [tabindex]:not([tabindex="-1"])';
  const ident = (e) => (e.getAttribute('class') || '').trim().split(/\s+/).slice(0, 4).join('.')
                   || '<' + e.tagName.toLowerCase() + '>';
  const lab = (e) => e.getAttribute('aria-label')
    || e.getAttribute('placeholder')
    || (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 24)
    || e.getAttribute('title') || '<' + e.tagName.toLowerCase() + '>';

  const all = [];
  for (const e of scope.querySelectorAll('*')) {
    const s = getComputedStyle(e);
    if (s.pointerEvents === 'none') continue;
    const b = e.getBoundingClientRect();
    if (b.width <= 0 || b.height <= 0) continue;
    all.push({el: e, l: b.left, t: b.top, rr: b.right, b: b.bottom, ident: ident(e)});
  }

  const rows = [];
  for (const e of scope.querySelectorAll(SEL)) {
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden') continue;
    if (parseFloat(s.opacity) === 0) continue;
    const b = e.getBoundingClientRect();
    if (b.width <= 0 || b.height <= 0) continue;
    const cx = b.x + b.width / 2, cy = b.y + b.height / 2;
    if (cx < 0 || cy < 0 || cx > innerWidth || cy > innerHeight) continue;
    const stack = document.elementsFromPoint(cx, cy);
    const selfAt = stack.findIndex((h) => h === e || e.contains(h));
    const cands = [];
    for (const a of all) {
      if (a.el === e || a.el.contains(e) || e.contains(a.el)) continue;
      if (!(cx >= a.l && cx < a.rr && cy >= a.t && cy < a.b)) continue;
      const at = stack.indexOf(a.el);
      cands.push({ident: a.ident, at: at});
    }
    // 归因规则：候选里「在栈中最靠上、且位于自己之下」的那一枚。
    // selfAt === -1（自己不在栈里）时取栈中最靠上的候选。
    const below = cands.filter((c) => c.at > selfAt).sort((x, y) => x.at - y.at);
    const blame = (below.length ? below[0]
                  : cands.slice().sort((x, y) => (x.at < 0 ? 1 : 0) - (y.at < 0 ? 1 : 0)
                                              || x.at - y.at)[0]) || null;
    rows.push({name: lab(e), ident: ident(e),
               w: Math.round(b.width * 100) / 100, h: Math.round(b.height * 100) / 100,
               cx: Math.round(cx * 100) / 100, cy: Math.round(cy * 100) / 100,
               selfAt: selfAt, hitBlocked: selfAt !== 0,
               nCand: cands.length,
               trueFP: selfAt === 0 && cands.length > 0,
               blame: blame ? blame.ident : null,
               blameAt: blame ? blame.at : null,
               cands: cands.map((c) => c.ident)});
  }
  return {W: innerWidth, cells: rows.length, rows: rows};
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
              + (f"  {str(detail)[:150]}" if detail else "")
              + (f"  [{note[:96]}]" if note else ""))


def main() -> int:
    v = Verifier()
    cells: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        for (w, h) in CELLS:
            page = br.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
            b617.open_desk(page)
            _clean(page)
            cells[f"{w}x{h}"] = page.evaluate(JS)
            page.close()
        br.close()

    keys = [f"{w}x{h}" for (w, h) in CELLS]
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"stage": "raw-readings", "cells": cells}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    n_cells = {k: cells[k]["cells"] for k in keys}
    fp_count = {k: sum(1 for r in cells[k]["rows"] if r["trueFP"]) for k in keys}
    # 归因族：按 blame 分组，取三视口的交集（证明不是某一档的偶然）
    per_key_fam: dict[str, dict[str, list[str]]] = {}
    for k in keys:
        fam: dict[str, list[str]] = {}
        for r in cells[k]["rows"]:
            if not r["trueFP"]:
                continue
            fam.setdefault(r["blame"] or "<null>", []).append(r["name"])
        per_key_fam[k] = fam
    always: set[str] = set.intersection(*[set(n for rows in per_key_fam[k].values()
                                              for n in rows) for k in keys])
    families = {}
    for k in keys:
        for blame, names in per_key_fam[k].items():
            families.setdefault(blame, {})[k] = len(names)
    fam_stable = {b: sorted(v.keys()) == keys for b, v in families.items()}
    fam_counts = {b: sorted(v.values()) for b, v in families.items()}

    axis_btn = {k: sorted(r["name"] for r in cells[k]["rows"]
                          if re.match(AXIS_BUTTON, r["name"])) for k in keys}
    axis_lbl = {k: sorted({r["name"] for r in cells[k]["rows"]
                           if r["name"].startswith(AXIS_LABEL)}) for k in keys}
    # 同名元素的个数：textContent 版 lab() 会把 3 层嵌套的同名元素算成同一个名字
    axis_lbl_elems = {k: sum(1 for r in cells[k]["rows"]
                             if r["name"].startswith(AXIS_LABEL)) for k in keys}
    gizmo_rows = {(k, r["name"]): r for k in keys for r in cells[k]["rows"]
                  if any(p in r["name"] for p in ("正向", "反向"))}

    v.check("the-66-always-false-positives-partition-into-a-handful-of-families",
            len(always) == 66 and len(families) <= 8 and all(fam_stable.values()),
            detail={"alwaysFalsePositives": len(always),
                    "families": len(families),
                    "familySizesPerCell": fam_counts,
                    "familyPresentAtAllCells": {k: v for k, v in fam_stable.items() if not v},
                    "fpCountPerCell": fp_count, "cellsPerViewport": n_cells},
            note="no hand-written list: the partition is computed by the blame rule")

    v.check("the-gizmo-family-is-six-axis-buttons-with-exactly-one-candidate",
            all(len(axis_btn[k]) == 6 for k in keys)
            and all(sorted(axis_btn[k]) == ["X 反向", "X 正向", "Y 反向", "Y 正向",
                                            "Z 反向", "Z 正向"] for k in keys)
            and all(gizmo_rows[(k, n)]["nCand"] == 1
                    and gizmo_rows[(k, n)]["blame"] == "absolute.inset-0"
                    for k in keys for n in axis_btn[k]),
            detail={"axisButtons": axis_btn[keys[0]],
                    "axisButtonBoxes@first": {n: [gizmo_rows[(keys[0], n)]["w"],
                                                  gizmo_rows[(keys[0], n)]["h"]]
                                              for n in axis_btn[keys[0]]},
                    "candidatesPerButton": {n: gizmo_rows[(keys[0], n)]["nCand"]
                                            for n in axis_btn[keys[0]]},
                    "blamePerButton": sorted({gizmo_rows[(keys[0], n)]["blame"]
                                              for n in axis_btn[keys[0]]}),
                    "blameStackIndex": sorted({gizmo_rows[(keys[0], n)]["blameAt"]
                                              for n in axis_btn[keys[0]]})},
            note="the whole family reduces to ONE element: the viewport's own "
                 "div.absolute.inset-0, three levels below each button")

    v.check("there-are-nine-axis-related-controls-but-only-six-axis-buttons",
            all(len(axis_btn[k]) + len(axis_lbl[k]) == 9 for k in keys)
            and all(axis_lbl[k] == ["左右拖动调整 X 轴", "左右拖动调整 Y 轴",
                                    "左右拖动调整 Z 轴"] for k in keys)
            and all(axis_lbl_elems[k] == 9 for k in keys),
            detail={"axisButtons": len(axis_btn[keys[0]]),
                    "axisLabelNames": axis_lbl[keys[0]],
                    "axisLabelElements": axis_lbl_elems[keys[0]],
                    "axisRelatedTotal": len(axis_btn[keys[0]]) + len(axis_lbl[keys[0]]),
                    "correctionTo670":
                        "670's README said 'all 9 gizmo axis buttons X/Y/Z 正向·反向'; "
                        "those names are 6 controls, and 3 more names are the drag labels",
                    "instrumentCaveat":
                        "the 3 label names come from 9 ELEMENTS — lab() reads textContent, "
                        "so three nested levels per label collapse into one name; every "
                        "name-keyed census in this repo silently deduplicates them"},
            note="historical batches are not rewritten; the correction lives here")

    v.check("the-blame-is-never-an-ancestor-of-the-control",
            all(all(r["blame"] is None or r["blame"] != r["ident"]
                    for r in cells[k]["rows"] if r["trueFP"]) for k in keys)
            and all(all(gizmo_rows[(k, n)]["blameAt"] > gizmo_rows[(k, n)]["selfAt"]
                        for n in axis_btn[k]) for k in keys),
            detail={"fpCells": sum(fp_count.values()),
                    "selfAtForAxisButtons": sorted({gizmo_rows[(keys[0], n)]["selfAt"]
                                                    for n in axis_btn[keys[0]]}),
                    "blameAtForAxisButtons": sorted({gizmo_rows[(keys[0], n)]["blameAt"]
                                                     for n in axis_btn[keys[0]]})},
            note="the blamed element is strictly BELOW the control in the hit stack — "
                 "that is what makes it a false positive rather than a real occlusion")

    out = {"cells": list(keys), "cellsPerViewport": n_cells,
           "fpCountPerViewport": fp_count, "alwaysFalsePositives": len(always),
           "families": len(families), "familySizesPerCell": fam_counts,
           "blameRule": "topmost candidate strictly below the control in the hit stack; "
                        "if the control is not in the stack, the topmost candidate",
           "axisButtons": len(axis_btn[keys[0]]), "axisLabels": len(axis_lbl[keys[0]])}
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "cells": cells, "checks": v.result},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
