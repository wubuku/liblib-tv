#!/usr/bin/env python3
"""batch 684 验收：`36×18` 那枚是**轨道标题按钮** —— 683 的事实没错，**我给它安的类比错了**

## 起点

683 报了一条读数：两条轨道的 `data-director-track-label` 键
**在每个高度下都有两种尺寸** `{(24,24), (36,18)}`，
并被我类比成「673 那条『异类合并』的尺寸版」。

**本批去查那枚 `36×18` 到底是什么。**

## 一条读数，以及一处纠正

### `36×18` 是轨道行的**标题按钮**

一条相机轨道行（`[data-director-track-row=…]`，320×32）里有 **4 枚**控件：

| 可及名 | 盒 | class 角色 |
|---|---|---|
| **`机位`**（轨道标题） | **`36×18`** | `relative z-[1] min-w-0 cursor-pointer truncate text-left font-medium` |
| `上一关键帧` | 24×24 | `group relative flex h-6 w-6 shrink-0 items-center justify-center rounded-md` |
| `当前帧有关键帧` | 24×24 | 同上 |
| `下一关键帧` | 24×24 | 同上 |

**四枚的 `selfData` 全是空数组** —— 它们都靠祖先的 `data-director-track-label` 认身份。
尺寸分布在 H = 400 / 720 / 1150 **逐格相同**：`{(24,24): 3, (36,18): 1}`。

### 纠正 683 的**类比**（事实不变）

- **683 断言的是真的**：两个 data 键在每个高度下确实各带两种尺寸。**这条不撤销。**
- **错的是我给它的解释**：我把它叫作「异类合并的尺寸版」，暗示那是一种异常。
  **它不是异常，是一条轨道行的解剖结构** —— 一个标题按钮 + 三个图标按钮，
  共用同一个 `data-director-track-label` 祖先。

**按纪律：历史批次不重写，纠正记在本批。**

### 真正的发现：「最近 data 属性」这条口径表达的是**包含关系**，不是身份

`dataOf`（找最近的 `data-*` 祖先）把**一个容器里的所有控件**都算成容器的键。
所以 `data-director-track-label=<track>` 这个键**覆盖 4 枚控件、2 种尺寸**。

**这同时是 674 那个「不可约的 4」的成因**：
那 3 枚导航钮**自身一个 data 属性都没有**（本批量到 `selfData == []`），
最近 data 规则只能把轨道的键借给它们 —— 于是 3 枚同轨道的按钮必然同键。

**所以 674 说的「不声称 4 是下界」，现在有了成因**：
不是「信息论上不可约」，而是**这 3 枚自己没有逐节点属性**。
要拆开只能改 `src/`（给它们加 `data-*`）—— **产品决定**。

### 一条可复用的推论

要判断「同一个键下的多个成员」是**同类的多个实例**还是**一个容器加它的子项**，
判据是**它们的盒尺寸与 class 角色不同** —— 也就是 683 已经在测的那个量。

**所以 683 那条判据测的是对的量，错的是我给它起的名字。**

## 自记

第一版我打算用**可及名**（`机位` / `上一关键帧`…）来认成员，临时改成**class 角色**
（`truncate` vs `h-6 w-6`）—— 因为 673 已经证明**按名字会折叠**，
而这里要认的恰恰是「同键下的不同成员」，用名字认会把要区分的东西先合并掉。

## 不声称

- **不声称** 683 的读数错了（**事实不变，只纠正解释**）；
- **不声称**给 3 枚导航钮加 `data-*` 是正确的修法（**产品决定**）；
- **不声称**源站的轨道行有同样的解剖（**未取证**）；
- **不声称**所有容器型 data 属性都会造成这个效应（本批只量了这一种）。
"""

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch684-2026-10-01"

HEIGHTS = [400, 720, 1150]
TRACKS = ["director-track-camera-main", "director-track-character-lead-transform"]

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

# **用 class 角色认成员，不用可及名** —— 673 已证按名字会折叠，
# 而这里要认的恰恰是「同键下的不同成员」。
LABEL_CLS = "truncate"          # 轨道标题按钮
NAV_CLS = "h-6 w-6"             # 三枚关键帧导航钮

JS = r"""(rows) => {
  const out = {};
  for (const id of rows) {
    const row = document.querySelector('[data-director-track-row="' + id + '"]');
    if (!row) { out[id] = null; continue; }
    const SEL = 'button, [role=button], [role=tab], [role=switch], [role=slider],'
      + ' [role=menuitem], input, select, textarea, a[href],'
      + ' [tabindex]:not([tabindex="-1"])';
    const members = [];
    for (const e of row.querySelectorAll(SEL)) {
      const s = getComputedStyle(e);
      if (s.display === 'none' || s.visibility === 'hidden') continue;
      const r = e.getBoundingClientRect();
      const self = Array.from(e.attributes)
          .filter((a) => a.name.startsWith('data-')).map((a) => a.name);
      members.push({
        name: e.getAttribute('aria-label') || (e.textContent || '').trim().slice(0, 24),
        box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        selfDataAttrNames: self,
        cls: (e.getAttribute('class') || '').trim().split(/\s+/).join(' '),
      });
    }
    const rr = row.getBoundingClientRect();
    out[id] = {rowBox: [Math.round(rr.x), Math.round(rr.y),
                        Math.round(rr.width), Math.round(rr.height)],
               members};
  }
  return out;
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
    cells: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        for h in HEIGHTS:
            page = br.new_page(viewport={"width": 1280, "height": h}, device_scale_factor=1)
            b617.open_desk(page)
            _clean(page)
            cells[f"1280x{h}"] = page.evaluate(JS, TRACKS)
            page.close()
        br.close()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"stage": "raw-readings", "cells": cells}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    keys = list(cells)

    def role_of(m: dict[str, Any]) -> str:
        cls = m["cls"].split()
        if LABEL_CLS in cls:
            return "track-label"
        if all(t in cls for t in NAV_CLS.split()):
            return "keyframe-nav"
        return "other"

    per_cell: dict[str, Any] = {}
    for k in keys:
        rec = {}
        for t in TRACKS:
            row = cells[k][t]
            if row is None:
                rec[t] = None
                continue
            members = [{**m, "role": role_of(m),
                        "size": [m["box"][2], m["box"][3]]} for m in row["members"]]
            rec[t] = {"rowBox": row["rowBox"], "members": members,
                      "sizeHistogram": {f"{s[0]}x{s[1]}": n for s, n in
                                        Counter(tuple(m["size"]) for m in members).items()},
                      "roles": {r: sum(1 for m in members if m["role"] == r)
                                for r in {m["role"] for m in members}}}
        per_cell[k] = rec

    label_members = [m for k in keys for t in TRACKS
                     for m in per_cell[k][t]["members"] if m["role"] == "track-label"]
    nav_members = [m for k in keys for t in TRACKS
                   for m in per_cell[k][t]["members"] if m["role"] == "keyframe-nav"]
    no_self = all(not m["selfDataAttrNames"] for m in label_members + nav_members)
    label_sizes = {tuple(m["size"]) for m in label_members}
    nav_sizes = {tuple(m["size"]) for m in nav_members}
    split_1_3 = all(per_cell[k][t]["roles"].get("track-label") == 1
                    and per_cell[k][t]["roles"].get("keyframe-nav") == 3
                    and per_cell[k][t]["roles"].get("other", 0) == 0
                    for k in keys for t in TRACKS)
    hist = {f"{k}|{t}": per_cell[k][t]["sizeHistogram"] for k in keys for t in TRACKS}

    v.check("each-track-row-is-one-label-plus-three-nav-buttons",
            len(TRACKS) == 2 and split_1_3
            and all(len(per_cell[k][t]["members"]) == 4 for k in keys for t in TRACKS),
            detail={"rolesPerCell": {f"{k}|{t}": per_cell[k][t]["roles"]
                                     for k in keys for t in TRACKS},
                    "rowBoxes": {f"{k}|{t}": per_cell[k][t]["rowBox"]
                                 for k in keys for t in TRACKS}},
            note="identified by CLASS ROLE (truncate vs h-6 w-6), not by accessible "
                 "name — 673 already showed name-keying folds")

    v.check("the-36x18-member-is-the-track-label-and-the-24x24-ones-are-the-nav-buttons",
            label_sizes == {(36, 18)} and nav_sizes == {(24, 24)}
            and len(label_members) == len(TRACKS) * len(HEIGHTS),
            detail={"labelSizes": sorted(label_sizes), "navSizes": sorted(nav_sizes),
                    "labelMembers": [{"cell": k, "track": t, "name": m["name"],
                                      "box": m["box"], "cls": m["cls"][:120]}
                                     for k in keys for t in TRACKS
                                     for m in per_cell[k][t]["members"]
                                     if m["role"] == "track-label"],
                    "sizeHistogramPerCell": hist},
            note="the two-size group is 1 label + 3 buttons, constant across heights")

    v.check("none-of-the-four-members-carries-a-data-attribute-of-its-own",
            no_self
            and len(label_members) + len(nav_members) == 4 * len(TRACKS) * len(HEIGHTS),
            detail={"membersChecked": len(label_members) + len(nav_members),
                    "expected": 4 * len(TRACKS) * len(HEIGHTS),
                    "withSelfData": [m["name"] for m in label_members + nav_members
                                     if m["selfDataAttrNames"]],
                    "howTheyAreIdentified":
                        "all four inherit `data-director-track-label=<track>` from the "
                        "row ancestor. The nearest-data rule therefore attributes FOUR "
                        "controls of TWO sizes to ONE key."},
            note="this is why 683 saw a two-size key — and it is containment, not identity")

    v.check("this-is-the-anatomy-of-a-track-row-not-a-heterogeneity-anomaly",
            split_1_3 and label_sizes == {(36, 18)} and nav_sizes == {(24, 24)},
            detail={"correctionTo683":
                    "683's READING stands: two data keys each carry two sizes at every "
                    "height. What was wrong is the interpretation — I called it '673's "
                    "异类合并, size-side', implying an anomaly. It is the normal anatomy of "
                    "a track row: one label button plus three icon buttons.",
                    "historyRule": "historic batches are not rewritten; the correction is "
                                   "recorded here, and 683 stays as it was committed",
                    "whatIsStillTrue": "the two-size-per-key fact, and the reusable "
                                       "inference below"},
            note="a fact can be right and its name wrong — the reading survives, the "
                 "label does not")

    v.check("the-reusable-inference-a-container-key-versus-same-class-instances",
            no_self and split_1_3,
            detail={"inference":
                        "To tell whether several members under one key are INSTANCES OF "
                        "ONE CLASS or A CONTAINER AND ITS CHILDREN, compare their box sizes "
                        "and class roles — which is exactly the quantity 683 already "
                        "measured. 683 measured the right thing; I named it wrong.",
                    "alsoExplains674":
                        "674's 'irreducible 4' has the same cause: the three nav buttons "
                        "have no per-node data attribute at all, so the nearest-data rule "
                        "lends them the track's key and they are necessarily equal. 674 "
                        "said 'not claimed to be a lower bound' — this is WHY it is not.",
                    "toBreakItApart": "give the three nav buttons their own data-*; that is "
                                      "a change to src/ — PRODUCT DECISION"},
            note="this is the actionable output of the batch")

    out = {"heights": HEIGHTS, "tracks": TRACKS,
           "perCell": per_cell, "labelSizes": sorted(label_sizes),
           "navSizes": sorted(nav_sizes), "sizeHistogramPerCell": hist,
           "noSelfData": no_self, "judged": len(TRACKS) * len(HEIGHTS) * 4}
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "cells": cells, "checks": v.result},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
