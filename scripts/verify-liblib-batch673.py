#!/usr/bin/env python3
"""batch 673 验收：**按名字计数的普查，28 枚控件被静默折叠**

## 起点

672 归因时撞见一件小事：gizmo 那 3 个拖动说明标签，其实来自 **9 个元素**
（每个标签 3 层嵌套同名），而本仓库所有普查的 `lab()` 都读 `textContent`
—— 于是 3 个名字。**672 把它记成「第 11 个盲区形状：身份按文本折叠」。**

**一个形状不等于一个人口。** 本批去数这个折叠到底有多大，并且回答
「它咬到过历史吗」。

## 一：活体普查（130 控件 → 102 个名字）

| 量 | 值 | 三视口 |
|---|---|---|
| 控件 | **130** | 逐格相同 |
| **不同名字** | **102** | 逐格相同 |
| **被名字吞掉的控件** | **28**（21.5%） | 逐格相同 |
| 碰撞名字 | **8** 个，涉及 36 枚控件 | 逐格相同 |

碰撞名单与倍数：`当前帧有关键帧` **11**、`<input>`（无 aria/placeholder 的
兜底名）**10**、`左右拖动调整 X/Y/Z 轴` **各 3**、
`上一关键帧` / `下一关键帧` / `收起属性` **各 2**。

**倍数不是偶然的**：每一组的成员盒都落在**一个格点阵**上
（`当前帧有关键帧` 的 x 步长 84、y 步长 72；`左右拖动调整 X 轴` 三枚同 x、y 步长 72）
—— 它们是**每个时间轴行 / 每个轨道格重复一次**的结构。

## 二：静态普查（既往验收器拿这些名字当键用了多少次）

用 `ast` 精确数：`scripts/verify-liblib-batch*.py` 里，**这些名字的字面量**
出现在**代码**（排除注释与 docstring）且处在**比较 / 下标 / 字典键 / 集合成员**
位置上的次数。**不 grep** —— grep 分不出注释、docstring 与代码。

## 三：咬合

把「历史上被当作键用的名字」与「活体里 n>1 的名字」求交 ——
**那个交集就是被折叠影响过的历史读数**。

**不声称**：这些历史结论因此是错的 —— 多数是「在某一格量到某一枚」，
不受折叠影响；本批只主张**按名字聚合的那些读数有歧义**。
"""

import ast
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch673-2026-10-01"
SCRIPTS = ROOT / "scripts"

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

CELLS = [(1280, 1150), (1440, 1150), (1920, 1150)]

JS = r"""() => {
  const scope = document.querySelector('[data-director-workspace]') || document.body;
  const SEL = 'button, [role=button], [role=tab], [role=switch], [role=slider],'
    + ' [role=menuitem], input, select, textarea, a[href],'
    + ' [tabindex]:not([tabindex="-1"])';
  const labA = (e) => e.getAttribute('aria-label')
    || e.getAttribute('placeholder')
    || (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 24)
    || e.getAttribute('title') || '<' + e.tagName.toLowerCase() + '>';
  const ident = (e) => (e.getAttribute('class') || '').trim().split(/\s+/).slice(0, 3).join('.')
                   || '<' + e.tagName.toLowerCase() + '>';
  const vis = (e) => { const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden') return false;
    const b = e.getBoundingClientRect();
    return b.width > 0 && b.height > 0 && parseFloat(s.opacity) !== 0; };
  const ctrls = [];
  for (const e of scope.querySelectorAll(SEL)) {
    if (!vis(e)) continue;
    const b = e.getBoundingClientRect();
    ctrls.push({name: labA(e), ident: ident(e), tag: e.tagName.toLowerCase(),
                box: [b.x, b.y, b.width, b.height].map((v) => Math.round(v * 100) / 100)});
  }
  const byName = new Map();
  for (const c of ctrls) {
    if (!byName.has(c.name)) byName.set(c.name, []);
    byName.get(c.name).push(c);
  }
  const collisions = [];
  for (const [name, list] of byName) {
    if (list.length < 2) continue;
    collisions.push({name: name, n: list.length,
                     members: list.map((c) => ({ident: c.ident, tag: c.tag, box: c.box}))});
  }
  collisions.sort((a, b) => b.n - a.n || (a.name < b.name ? -1 : 1));
  return {W: innerWidth, controls: ctrls.length, distinctNames: byName.size,
          collisions: collisions};
}"""

KEY_PARENTS = (ast.Compare, ast.Subscript, ast.Dict, ast.Set, ast.List, ast.Tuple)


def _clean(page) -> None:
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(80)


def static_census(names: set[str]) -> dict[str, Any]:
    """ast 精确普查：这些名字的字面量在**代码**里被当键用的次数"""
    files = sorted(f for f in SCRIPTS.glob("verify-liblib-batch*.py")
                   if f.name != Path(__file__).name)
    # 普查必须排除自己：673 的源码里就有 bite_files["收起属性"] 这样的下标键，
    # 不排除就会把自己算成第 10 个「被折叠影响过的历史验收器」——**仪器量到了自己**。
    docstring_nodes: set[int] = set()
    per_file: dict[str, dict[str, int]] = {}
    total = 0
    for f in files:
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        parents: dict[int, ast.AST] = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                parents[id(child)] = node
        # docstring：Module / ClassDef / FunctionDef 的 body[0]
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)):
                body = getattr(node, "body", None)
                if body and isinstance(body[0], ast.Expr) and \
                        isinstance(body[0].value, ast.Constant) and \
                        isinstance(body[0].value.value, str):
                    docstring_nodes.add(id(body[0].value))
        hits: dict[str, int] = {}
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            if node.value not in names or id(node) in docstring_nodes:
                continue
            p = parents.get(id(node))
            if isinstance(p, KEY_PARENTS):
                hits[node.value] = hits.get(node.value, 0) + 1
        if hits:
            per_file[f.name] = hits
            total += sum(hits.values())
    return {"filesScanned": len(files), "filesWithHits": len(per_file),
            "keyUses": total, "perFile": per_file}


def on_lattice(boxes: list[list[float]]) -> dict[str, Any]:
    """成员盒是否落在格点阵上：x 等距 或 y 等距"""
    xs = sorted({b[0] for b in boxes})
    ys = sorted({b[1] for b in boxes})
    dx = [round(xs[i + 1] - xs[i], 2) for i in range(len(xs) - 1)]
    dy = [round(ys[i + 1] - ys[i], 2) for i in range(len(ys) - 1)]
    return {"xs": xs, "ys": ys, "dx": dx, "dy": dy,
            "xEquidistant": len(set(dx)) <= 1, "yEquidistant": len(set(dy)) <= 1}


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

    ctrl = {k: cells[k]["controls"] for k in keys}
    distinct = {k: cells[k]["distinctNames"] for k in keys}
    shadowed = {k: ctrl[k] - distinct[k] for k in keys}
    col_count = {k: len(cells[k]["collisions"]) for k in keys}
    fp = {k: json.dumps([(c["name"], c["n"]) for c in cells[k]["collisions"]],
                        ensure_ascii=False) for k in keys}
    coll0 = cells[keys[0]]["collisions"]
    names = {c["name"] for c in coll0}
    lat = {c["name"]: on_lattice([m["box"] for m in c["members"]]) for c in coll0}
    stat = static_census(names)
    bite = sorted(n for n in names if stat["perFile"] and
                  any(n in hits for hits in stat["perFile"].values()))
    bite_files = {n: sorted(f for f, hits in stat["perFile"].items() if n in hits)
                  for n in bite}
    judged = sum(ctrl[k] for k in keys)

    v.check("130-controls-collapse-to-102-names-at-every-viewport",
            len(set(ctrl.values())) == 1 and len(set(distinct.values())) == 1
            and len(set(shadowed.values())) == 1
            and ctrl[keys[0]] == 130 and distinct[keys[0]] == 102
            and shadowed[keys[0]] == 28,
            detail={"controls": ctrl, "distinctNames": distinct, "shadowed": shadowed,
                    "shadowedShare": round(shadowed[keys[0]] / ctrl[keys[0]], 3)},
            note="28 of 130 — a name-keyed dict loses more than a fifth of the table")

    v.check("eight-colliding-names-and-their-multiplicities-are-identical-at-three-viewports",
            len(set(col_count.values())) == 1 and len(set(fp.values())) == 1
            and sorted(c["n"] for c in coll0) == [2, 2, 2, 3, 3, 3, 10, 11],
            detail={"collidingNames": col_count,
                    "names": [{"name": c["name"], "n": c["n"]} for c in coll0],
                    "controlsInCollision": sum(c["n"] for c in coll0)},
            note="one name with 11, one with 10, three with 3, three with 2")

    same_kind, mixed_kind = [], []
    for c in coll0:
        shapes = {(round(m["box"][2], 2), round(m["box"][3], 2), m["ident"])
                  for m in c["members"]}
        sizes = {(round(m["box"][2], 2), round(m["box"][3], 2)) for m in c["members"]}
        rec = {"name": c["name"], "n": c["n"], "distinctShapes": len(shapes),
               "boxSizes": sorted(sizes),
               "shapeCounts": [{"ident": s[2][:40], "box": [s[0], s[1]],
                                "n": sum(1 for m in c["members"]
                                         if (round(m["box"][2], 2), round(m["box"][3], 2),
                                             m["ident"]) == s)}
                               for s in sorted(shapes)]}
        (mixed_kind if len(shapes) > 1 else same_kind).append(rec)

    v.check("two-names-merge-different-controls-not-just-repeated-copies",
            len(same_kind) == 6 and len(mixed_kind) == 2
            and any(r["name"] == "<input>" for r in mixed_kind)
            and all(r["distinctShapes"] > 1 for r in mixed_kind),
            detail={"sameControlRepeated": same_kind, "differentControlsMerged": mixed_kind},
            note="当前帧有关键帧 is 9 timeline chips (20x28) PLUS 2 inspector buttons "
                 "(24x24); <input> is not a name at all — it is lab()'s fallback when "
                 "aria-label, placeholder and textContent all come up empty")

    v.check("the-colliding-names-were-used-as-keys-in-nine-historic-verifiers",
            stat["filesWithHits"] == 9 and stat["keyUses"] >= 20
            and len(bite) >= 6 and len(bite_files["收起属性"]) == 4,
            detail={"staticCensus": dict(stat, selfExcluded=Path(__file__).name),
                    "bittenNames": bite,
                    "filesPerName": bite_files,
                    "collidingNamesNoVerifierKeys": sorted(set(names) - set(bite)),
                    "selfReference":
                        "this census counts the corpus it lives in, INCLUDING earlier "
                        "liblib verifiers that quote the colliding names. Across three "
                        "runs of the SAME census the bitten-name count moved 7 -> 6 -> 7 "
                        "purely because this file was being edited between runs. That is "
                        "why the count is recorded, not pinned; the census already "
                        "excludes its own source (selfExcluded above)",
                    "whyKeyUsesIsNotPinned":
                        "the scan covers every verify-liblib-batch*.py INCLUDING this "
                        "one, so the total moves as this file is edited (26 -> 27 while "
                        "writing this very check). The structure is asserted; the exact "
                        "total is recorded, not pinned",
                    "worstOffender": {"name": "收起属性", "liveMultiplicity": 2,
                                      "files": bite_files["收起属性"]}},
            note="收起属性 has TWO live elements and was keyed by name in 4 verifiers — "
                 "including 661/664/667, whose reasoning is by name")

    v.check("the-blind-spot-is-bigger-than-the-gizmo-labels-alone",
            shadowed[keys[0]] > 9 and len(names) > 3,
            detail={"shadowed": shadowed[keys[0]], "collidingNames": len(names),
                    "gizmoLabelsAlone": 6,
                    "largestCollision": max(c["n"] for c in coll0),
                    "worstName": max(coll0, key=lambda c: c["n"])["name"]},
            note="672 saw 6 folded labels; the real folded population is 28 controls")

    out = {"cells": list(keys), "controls": ctrl, "distinctNames": distinct,
           "shadowed": shadowed, "collidingNames": col_count,
           "multiplicities": {c["name"]: c["n"] for c in coll0},
           "lattice": lat, "staticCensus": stat, "bite": bite, "biteFiles": bite_files,
           "sameControlRepeated": [r["name"] for r in same_kind],
           "differentControlsMerged": [r["name"] for r in mixed_kind],
           "controlsJudged": judged}
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "cells": cells, "checks": v.result},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
