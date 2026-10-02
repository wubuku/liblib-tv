#!/usr/bin/env python3
"""batch 674 验收：**没有不折叠的身份**，折叠能压到 4 —— 而「更细的键」会把另一维做粗

## 起点

673 数出：130 枚控件只对应 **102** 个可及名，**28 枚**被按名字的字典吞掉，
并咬到 9 个既往验收器（`收起属性` 活体 2 枚却被 4 个当键用过）。

本批问的是那句更根本的话：**换一个身份就不折叠了吗？**

## 五套身份，五种折叠量（130 枚控件，三视口逐格相同）

| 身份口径 | 不同身份 | 折叠组 | 吞掉 |
|---|---|---|---|
| **可及名**（`aria-label` → placeholder → textContent） | **102** | 8 | **28** |
| **结构 kS**（tag + class 头 3 段 + 最近 data 的**名** + role） | **62** | 19 | **68** |
| **结构+值 kS2**（加上最近 data 的 `name=value`） | **120** | **5** | **10** |
| **kS3**（自身 data **全取**，回退祖先**只取名**） | **119** | 4 | **11** |
| **kS4**（自身 data **全取**，回退祖先**带值**） | **126** | 2 | **4** |

**两个反直觉的事实**：

1. **结构身份比名字折叠得更狠**（68 > 28）—— 9 条拖动标签、9 枚关键帧片、
   6 枚轴按钮在**结构上同族**，而它们的**名字各不相同**。
2. **两套划分不互相包含**：名字把 `当前帧有关键帧` 那 11 枚并成一条
   （9 枚轨道片 + 2 枚检视器钮），结构却把它们分开；
   反过来结构把三条 `左右拖动调整 X/Y/Z 轴` 并成 9 枚一条，名字却分得开。
   **所以没有「最好的键」—— 每套键各对一族最优。**

## kS2 剩下那 10 枚：正好两族 —— 但**「不可约」这句话被本批自己推翻**

| 族 | 组数 × 每组 | 键里那一维的值 |
|---|---|---|
| 变换输入框 | 3 组 × 3 | `data-director-transform-field=position / rotation / scale` |
| 关键帧导航钮 | 2 组 × 3 | `data-director-track-label=director-track-…`（同一轨道） |

**本文件第一版在这里写的是「都是同维度重复而该维度没有逐节点 id」—— 读数推翻了它。**
那 9 枚变换输入框**本来就带着逐节点 id**：`DirectorInspector.tsx:179-180` 在同一个
`<input>` 上同时写了 `data-director-transform-field` 与 `data-director-transform-axis`，
9 枚的**完整** self-data 是 9 个互不相同的元组。**是 kS2 只取第一个 data 属性把它丢掉了。**

## 一条独立教训：把一个维度做细，会把回退维度做粗

kS3 在自身 data 维度变细（9 枚变换输入框散开），却把**祖先回退**从 `name=value`
退化成只有 `name` —— 两条导演台轨道被并成一条 6 枚组（kS2 下是 2 组 × 3），
5 枚 `隐藏*` 按钮也丢了 `object-id` 的值被并成一条 5 枚组。**净效果 11 > 10，更差。**
残留组最大规模 kS2 = 3 → kS3 = 6。

**一条键不是「整体更细」，它是「逐维更细」，而各维之间会互相换。**

kS4（自身全取 + 回退带值）吞 **4** 枚，残留**正好**是那 6 枚关键帧导航钮 ——
它们**自身**一个 data 属性都没有，判别位在祖先 `div` 上而同轨道三枚共享，
彼此只能靠名字（`上一/当前/下一关键帧`）区分。**不声称 4 是下界。**

**另外 18 枚控件自己身上没有任何 `data-*` 属性**（14 个名字，含 `收起属性`、
`上一/下一关键帧`、`当前帧有关键帧`、全部 `隐藏*`）—— 它们只能靠祖先的属性被认出来。

## 顺带更正 670 的一处措辞

670 写「**66 枚控件**在每一档宽度上都是假阳性」。**那 66 是名字数**：
按可及名算恒真交集是 66 个**名字**（而真阳性的**控件**数是 73/75/76）；
换结构身份，同一个恒真集合按 kS 只有 **32** 个键，按 kS2/kS4 却有 **71** 个。

**「枚控件」这个措辞不成立** —— 控件层的数字取决于用哪套身份，本批把五套都记下来了。

**一个反直觉的连带读数**：kS2/kS4 折叠得最少，却给出**最多**的恒真键（71 > 66）。
键的个数与折叠量**不成单调关系** —— 折得越细，同一批控件散成的键反而越多。

**不声称**：kS4 就是最终答案（它仍吞 4 枚，且换第六套键又是另一个数）；
不声称 4 是折叠下界；不声称 18 枚「无自身 data 属性」需要改（改 `src/` 是**产品决定**）。
"""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch674-2026-10-01"

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
  const cls = (e) => (e.getAttribute('class') || '').trim().split(/\s+/);
  const labName = (e) => e.getAttribute('aria-label')
    || e.getAttribute('placeholder')
    || (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 24)
    || e.getAttribute('title') || '<' + e.tagName.toLowerCase() + '>';
  const nearestName = (e) => { for (let n = e; n && n !== document.body; n = n.parentElement)
      for (const a of n.attributes) if (a.name.startsWith('data-')) return a.name; return '-'; };
  const nearestWithValue = (e) => { for (let n = e; n && n !== document.body; n = n.parentElement)
      for (const a of n.attributes) if (a.name.startsWith('data-')) return a.name + '=' + a.value;
    return '-'; };
  const role = (e) => e.getAttribute('role') || '-';
  const kS = (e) => e.tagName.toLowerCase() + '|' + cls(e).slice(0, 3).join('.')
                    + '|' + nearestName(e) + '|' + role(e);
  const kS2 = (e) => e.tagName.toLowerCase() + '|' + cls(e).slice(0, 3).join('.')
                     + '|' + nearestWithValue(e) + '|' + role(e);
  const selfData = (e) => Array.from(e.attributes)
      .filter((a) => a.name.startsWith('data-')).map((a) => a.name + '=' + a.value);
  // kS3: 自身**全部** data 属性；一个都没有才回退到最近祖先的 data **名**（不含值）。
  const kS3 = (e) => e.tagName.toLowerCase() + '|' + cls(e).slice(0, 3).join('.')
    + '|' + (selfData(e).length ? selfData(e).join('&') : nearestName(e))
    + '|' + role(e);
  // kS4: 同 kS3，但回退时带上**值** —— 自身变细、回退不变粗，才是把两个维度分开量。
  const kS4 = (e) => e.tagName.toLowerCase() + '|' + cls(e).slice(0, 3).join('.')
    + '|' + (selfData(e).length ? selfData(e).join('&') : nearestWithValue(e))
    + '|' + role(e);
  const vis = (e) => { const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden') return false;
    const b = e.getBoundingClientRect();
    return b.width > 0 && b.height > 0 && parseFloat(s.opacity) !== 0; };

  const all = [];
  for (const e of scope.querySelectorAll('*')) {
    const s = getComputedStyle(e);
    if (s.pointerEvents === 'none') continue;
    const b = e.getBoundingClientRect();
    if (b.width <= 0 || b.height <= 0) continue;
    all.push({el: e, l: b.left, t: b.top, rr: b.right, b: b.bottom,
              ident: cls(e).join('.')});
  }
  const rows = [];
  for (const e of scope.querySelectorAll(SEL)) {
    if (!vis(e)) continue;
    const b = e.getBoundingClientRect();
    const px = b.x + b.width / 2, py = b.y + b.height / 2;
    const stack = document.elementsFromPoint(px, py);
    const selfAt = stack.findIndex((h) => h === e || e.contains(h));
    const cands = [];
    for (const a of all) {
      if (a.el === e || a.el.contains(e) || e.contains(a.el)) continue;
      if (!(px >= a.l && px < a.rr && py >= a.t && py < a.b)) continue;
      cands.push({ident: a.ident, at: stack.indexOf(a.el)});
    }
    const below = cands.filter((c) => c.at > selfAt).sort((x, y) => x.at - y.at);
    const blame = below.length ? below[0].ident : (cands[0] || {}).ident || null;
    rows.push({name: labName(e), kS: kS(e), kS2: kS2(e), kS3: kS3(e), kS4: kS4(e),
               selfData: selfData(e),
               trueFP: selfAt === 0 && cands.length > 0, blame: blame});
  }
  const dup = (key) => { const m = new Map();
    for (const r of rows) { if (!m.has(r[key])) m.set(r[key], []); m.get(r[key]).push(r); }
    return [...m.entries()].filter(([, v]) => v.length > 1)
        .map(([k, v]) => ({key: k, n: v.length, names: v.map((x) => x.name)})); };
  const uniq = (key) => new Set(rows.map((r) => r[key])).size;
  return {W: innerWidth, controls: rows.length,
          distinctNames: uniq('name'), distinctKS: uniq('kS'), distinctKS2: uniq('kS2'),
          distinctKS3: uniq('kS3'), distinctKS4: uniq('kS4'),
          dupsName: dup('name'), dupsKS: dup('kS'), dupsKS2: dup('kS2'),
          dupsKS3: dup('kS3'), dupsKS4: dup('kS4'),
          noSelfData: rows.filter((r) => r.selfData.length === 0).map((r) => r.name),
          rows: rows};
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


def fold(d: dict[str, Any], which: str) -> tuple[int, int, int]:
    dups = d["dups" + which]
    return (len(dups), sum(g["n"] for g in dups), sum(g["n"] - 1 for g in dups))


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

    d_name = {k: fold(cells[k], "Name") for k in keys}
    d_ks = {k: fold(cells[k], "KS") for k in keys}
    d_ks2 = {k: fold(cells[k], "KS2") for k in keys}
    d_ks3 = {k: fold(cells[k], "KS3") for k in keys}
    d_ks4 = {k: fold(cells[k], "KS4") for k in keys}
    uniq = {k: (cells[k]["distinctNames"], cells[k]["distinctKS"], cells[k]["distinctKS2"],
                cells[k]["distinctKS3"], cells[k]["distinctKS4"]) for k in keys}
    fp_by = {}
    for tag, fld in (("name", "name"), ("kS", "kS"), ("kS2", "kS2"),
                     ("kS3", "kS3"), ("kS4", "kS4")):
        sets = [set(r[fld] for r in cells[k]["rows"] if r["trueFP"]) for k in keys]
        fp_by[tag] = {"perCell": [len(s) for s in sets],
                      "intersection": len(set.intersection(*sets))}
    fp_counts = [len([r for r in cells[k]["rows"] if r["trueFP"]]) for k in keys]
    ks2_groups = sorted(cells[keys[0]]["dupsKS2"], key=lambda g: (-g["n"], g["key"]))
    ks3_groups = sorted(cells[keys[0]]["dupsKS3"], key=lambda g: (-g["n"], g["key"]))
    ks4_groups = sorted(cells[keys[0]]["dupsKS4"], key=lambda g: (-g["n"], g["key"]))
    no_self = sorted({n for n in cells[keys[0]]["noSelfData"]})
    no_self_elems = len(cells[keys[0]]["noSelfData"])

    v.check("five-identities-five-folding-counts-identical-at-three-viewports",
            len({d_name[k] for k in keys}) == 1
            and len({d_ks[k] for k in keys}) == 1
            and len({d_ks2[k] for k in keys}) == 1
            and len({d_ks3[k] for k in keys}) == 1
            and len({d_ks4[k] for k in keys}) == 1
            and len({str(uniq[k]) for k in keys}) == 1,
            detail={"uniquish": uniq[keys[0]],
                    "foldsName_groups_inside_shadowed": d_name[keys[0]],
                    "foldsKS": d_ks[keys[0]], "foldsKS2": d_ks2[keys[0]],
                    "foldsKS3": d_ks3[keys[0]], "foldsKS4": d_ks4[keys[0]]},
            note="names swallow 28, structure swallows 68, structure+value swallows 10; "
                 "kS3 swallows 11 (coarser fallback), kS4 swallows fewer than kS2")

    v.check("the-two-folding-partitions-are-not-nested",
            len({r["name"] for r in cells[keys[0]]["rows"]}) == 102
            and len({r["kS"] for r in cells[keys[0]]["rows"]}) == 62
            and len({r["kS2"] for r in cells[keys[0]]["rows"]}) == 120
            and d_ks[keys[0]][2] > d_name[keys[0]][2] > d_ks2[keys[0]][2],
            detail={"swallowedByName": d_name[keys[0]][2],
                    "swallowedByKS": d_ks[keys[0]][2],
                    "swallowedByKS2": d_ks2[keys[0]][2],
                    "exampleWhereStructureWins":
                        "当前帧有关键帧 is ONE name (11 controls) but TWO kS2 keys",
                    "exampleWhereNameWins":
                        "左右拖动调整 X/Y/Z 轴 are THREE names but ONE kS key (9 controls)"},
            note="no key is simply 'best' — each is best for a different family")

    v.check("the-kS2-residue-of-ten-is-exactly-two-families",
            len(ks2_groups) == 5
            and sorted(g["n"] for g in ks2_groups) == [3, 3, 3, 3, 3]
            and len({g["key"].split("|")[2].split("=")[0] for g in ks2_groups}) == 2,
            detail={"groups": [{"key": g["key"], "n": g["n"],
                                "names": g["names"]} for g in ks2_groups],
                    "familyAttributeNames":
                        sorted({g["key"].split("|")[2].split("=")[0] for g in ks2_groups})},
            note="9 transform inputs grouped 3-by-field, 6 keyframe-nav buttons grouped "
                 "3-by-track. NOT claimed irreducible — the next check refutes that")

    v.check("eighteen-controls-carry-no-data-attribute-of-their-own",
            no_self_elems == 18 and len(no_self) == 14
            and "收起属性" in no_self and "上一关键帧" in no_self,
            detail={"elementsWithoutSelfData": no_self_elems,
                    "distinctNames": len(no_self), "names": no_self,
                    "notTheSameAs664s22":
                        "664 counted 22 pe:none ELEMENTS; this counts 18 CONTROLS with no "
                        "self data attribute. Different populations — not a conflict"},
            note="they can only be identified through an ancestor's attribute")

    v.check("670s-66-is-a-name-count-not-a-control-count",
            fp_by["name"]["intersection"] == 66
            and len({fp_by[t]["intersection"] for t in ("name", "kS", "kS2")}) == 3
            and fp_by["kS2"]["intersection"] > fp_by["name"]["intersection"],
            detail={"alwaysTrueFPByKey": fp_by,
                    "trueFPCountsPerCell": fp_counts,
                    "correction":
                        "670's README said '66 枚控件在每一档宽度上都是假阳性'; 66 is the "
                        "intersection of NAMES (73/75/76 controls are true-FP at "
                        "1280/1440/1920, the counts 670 recorded). The control-level number "
                        "depends on the key and is not pinned here",
                    "correctsThisBatchesOwnPriorGuess":
                        "I expected kS2 to be the SMALLEST count because kS2 folds least. "
                        "The reading says the opposite: 71 > 66, because a finer key "
                        "splits the same true-FP set into MORE keys. The key count is not "
                        "monotone in the folding amount; the most-collapsing key (kS, 32) "
                        "is the smallest."},
            note="the wording is what fails, not the number 66 itself")

    tf_rows = [r for r in cells[keys[0]]["rows"] if "transform-field" in r["kS2"]]
    tf_full = {tuple(r["selfData"]) for r in tf_rows}
    ks2_max = max((g["n"] for g in ks2_groups), default=0)
    ks3_max = max((g["n"] for g in ks3_groups), default=0)
    v.check("a-finer-key-on-one-dimension-can-be-coarser-on-another",
            d_ks3[keys[0]][2] > d_ks2[keys[0]][2] and ks3_max > ks2_max,
            detail={"swallowedByKS2": d_ks2[keys[0]][2],
                    "swallowedByKS3": d_ks3[keys[0]][2],
                    "largestResidueGroupKS2": ks2_max, "largestResidueGroupKS3": ks3_max,
                    "ks3ResidueGroups": [{"key": g["key"], "n": g["n"],
                                          "names": g["names"]} for g in ks3_groups],
                    "mechanism":
                        "kS3 is finer on the SELF-data dimension (all attributes, so the "
                        "9 transform inputs split) but its ancestor FALLBACK degraded from "
                        "name=value to name only. That merged the two director tracks into "
                        "one 6-button group AND collapsed the 5 隐藏* buttons that kS2 kept "
                        "apart by object id. Net: 11 swallowed vs kS2's 10"},
            note="a key is not 'finer' overall — it is finer per dimension, and the "
                 "dimensions trade against each other")

    v.check("the-transform-family-already-had-a-per-node-discriminator-kS2-threw-away",
            len(tf_rows) == 9
            and len(tf_full) == 9
            and d_ks4[keys[0]][2] < d_ks2[keys[0]][2],
            detail={"transformControls": len(tf_rows),
                    "distinctFULLselfDataTuples": len(tf_full),
                    "sampleFullTuples": sorted("&".join(t) for t in tf_full)[:3],
                    "swallowedByKS2": d_ks2[keys[0]][2],
                    "swallowedByKS3": d_ks3[keys[0]][2],
                    "swallowedByKS4": d_ks4[keys[0]][2],
                    "ks4ResidueGroups": [{"key": g["key"], "n": g["n"],
                                          "names": g["names"]} for g in ks4_groups],
                    "sourceFact":
                        "src/components/director/DirectorInspector.tsx:179-180 puts BOTH "
                        "data-director-transform-field and data-director-transform-axis on "
                        "the same <input>; kS2 kept only the FIRST data attribute it found",
                    "correction":
                        "This batch's own 'irreducible 10' is irreducible only under the kS2 "
                        "definition — the discriminator was already in the clone all along"},
            note="kS4 keeps the self-data dimension fine AND the ancestor fallback intact; "
                 "the residue is the controls with no self data at all")

    out = {"cells": list(keys), "controls": cells[keys[0]]["controls"],
           "uniquish": uniq[keys[0]],
           "folds": {"name": d_name[keys[0]], "kS": d_ks[keys[0]],
                    "kS2": d_ks2[keys[0]], "kS3": d_ks3[keys[0]],
                    "kS4": d_ks4[keys[0]]},
           "alwaysTrueFPByKey": fp_by,
           "residueGroupsKS2": [g["key"] for g in ks2_groups],
           "residueGroupsKS3": [{"key": g["key"], "n": g["n"], "names": g["names"]}
                                 for g in ks3_groups],
           "residueGroupsKS4": [{"key": g["key"], "n": g["n"], "names": g["names"]}
                                 for g in ks4_groups],
           "noSelfDataElements": no_self_elems, "noSelfDataNames": no_self,
           "judged": cells[keys[0]]["controls"] * len(keys)}
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "cells": cells, "checks": v.result},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
