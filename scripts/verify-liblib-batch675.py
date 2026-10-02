#!/usr/bin/env python3
"""batch 675 验收：**归因对身份稳健，计数对身份敏感** —— 把「折叠」这个变量接进 672/673 的读数

## 起点

673 数出名字折叠 28 枚；674 数出换五套身份折叠量是 28 / 68 / 10 / 11 / 4。
两批都只给了「人口」，没回答那句真正要紧的话：

**672 那张 8 族表、673 那份碰撞名单，哪些是随身份变的、哪些是不变的？**

## 三条结论

### 1. 672 的族表逐格不变 —— 但原因是那条口径本身与身份无关

672 的族表（`relative.min-h-0.flex-1` 25 格、`absolute.inset-0` 19/21/22、… 、1 格）
逐档合计 73 / 75 / 76。本批发现它属于 **V3 口径 =「每档全部真阳性控件」**，
而 V3 **根本不用身份**（不按键分组，直接取该视口里 `trueFP` 的全部控件）。

**所以「族表在四套身份下不变」不是稳健性的证据，是口径的同义反复。**

### 2. 同一句「66 个名字」有三种读法，三张不同的表

| 口径 | 含义 | 1280 / 1440 / 1920 | 随身份变？ |
|---|---|---|---|
| **V1** | 键在三视口都是真阳性 ⟹ 把该键的**所有**控件都算进去 | **85 / 85 / 85**（按名字）<br>**78 / 78 / 78**（kS）<br>**73 / 73 / 73**（kS4） | **变** |
| **V2** | 且该枚控件自身在该档也是真阳性 | 73 / 73 / 73 | 不变 |
| **V3** | 每档全部真阳性控件（= 672 的族表） | 73 / 75 / 76 | 不变（口径不用身份） |

**670/672 并列写下的两句（「66 个名字每档都假阳性」与「每档 73–76 格」）出自两种不同读法。**

V1 还会**凭空造出一个族**：按名字的 V1 有 **9** 个族，多出来的那个是
`blame` 落在**无 class 元素**上的 12 枚 —— 它们在那档并不是真阳性，是被名字折叠拖进来的。

### 3. 673 的 8 个碰撞名，kS4 **全部**分开；而 kS4 自己的残留 ⊂ 名字折叠集

- 8 个碰撞名在 kS4 下**每个都跨了与控件数一样多的键**（11→11、10→10、3→3、2→2…）
  ⟹ **kS4 分开了名字折叠的全部 8 组**。
- 但 kS4 自己折叠 4 枚（6 枚元素）—— 那 6 枚是两条轨道各 3 枚导航钮，
  它们**全部落在名字的 36 枚折叠集之内**（`kS4 \ name = 0`）。
- 净账：kS4 分开了名字折叠的 36 枚里的 **30** 枚，剩下 6 枚两边都折叠。

## 不声称

不声称 672 的族表「错了」（它在自己的口径下逐格复现）；
不声称 V1/V2/V3 里哪一个「对」（本批证明它们互不相同，且都没被任何批次声明为唯一口径）；
不声称 kS4 是最终答案（674 已声明它仍吞 4 枚）。
"""

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch675-2026-10-01"
B674_AUDIT = ROOT / "docs/research/liblib-canvas-batch674-2026-10-01/runtime-audit.json"

IDENTITIES = ("name", "kS", "kS2", "kS3", "kS4")
CELLS = [(1280, 1150), (1440, 1150), (1920, 1150)]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


b617 = _load("b617", ROOT / "scripts/verify-liblib-batch617.py")
# **仪器复用**：675 不重写普查 JS，直接用 674 的那一份 ——
# 同一台量具、同一批读数，只换分析口径。跨批次一致性由 check 6 单独验。
b674 = _load("b674", ROOT / "scripts/verify-liblib-batch674.py")


def _clean(page) -> None:
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(80)


def _blame(row: dict[str, Any]) -> str:
    """672 的归因规则：blame 是候选里在命中栈中最靠上、且位于该控件之下者。
    674 的 JS 已按这条规则算好；这里只把「无 class」显式标出来（JSON 里是 null）。"""
    return row["blame"] or "<no-class>"


def _always_keys(cells: dict[str, Any], ident: str) -> set[str]:
    per = [{r[ident] for r in cells[k]["rows"] if r["trueFP"]} for k in cells]
    return set.intersection(*per)


def _selected(cells: dict[str, Any], ident: str, variant: str) -> dict[str, list]:
    """三种读法。V3 刻意**不**接 ident —— 它的口径就是「这一档的全部真阳性控件」。"""
    always = _always_keys(cells, ident)
    out: dict[str, list] = {}
    for k, cell in cells.items():
        rows = cell["rows"]
        if variant == "V1":       # 键恒真 ⟹ 该键的所有控件
            out[k] = [r for r in rows if r[ident] in always]
        elif variant == "V2":     # 且自身在该档真阳性
            out[k] = [r for r in rows if r["trueFP"] and r[ident] in always]
        elif variant == "V3":     # 每档全部真阳性控件（与身份无关）
            out[k] = [r for r in rows if r["trueFP"]]
        else:
            raise ValueError(variant)
    return out


def _families(sel: dict[str, list]) -> dict[str, list]:
    return {k: sorted(Counter(_blame(r) for r in rows).items(),
                     key=lambda kv: (-kv[1], kv[0]))
            for k, rows in sel.items()}


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
        for (w, h) in CELLS:
            page = br.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
            b617.open_desk(page)
            _clean(page)
            cells[f"{w}x{h}"] = page.evaluate(b674.JS)
            page.close()
        br.close()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"stage": "raw-readings", "cells": cells}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    keys = list(cells)
    ident_counts = {i: {k: len({r[i] for r in cells[k]["rows"]}) for k in keys}
                    for i in IDENTITIES}
    folds = {i: {k: sum(g["n"] - 1 for g in cells[k]["dups" + n])
                 for k in keys}
             for i, n in (("name", "Name"), ("kS", "KS"), ("kS2", "KS2"),
                          ("kS3", "KS3"), ("kS4", "KS4"))}
    always_n = {i: len(_always_keys(cells, i)) for i in IDENTITIES}

    tables: dict[str, Any] = {}
    for i in IDENTITIES:
        for var in ("V1", "V2", "V3"):
            fams = _families(_selected(cells, i, var))
            tables[f"{i}/{var}"] = {
                "controlsPerCell": [len(_selected(cells, i, var)[k]) for k in keys],
                "familiesPerCell": [len(fams[k]) for k in keys],
                "familyNamesPerCell": [[n for n, _ in fams[k]] for k in keys],
            }
    # V3 口径与身份无关：只算一次，存成 672 那张表的复现
    fams_v3 = _families(_selected(cells, "name", "V3"))
    table_672 = {k: dict(fams_v3[k]) for k in keys}

    def flat(var: str, i: str = "name") -> list[int]:
        return tables[f"{i}/{var}"]["controlsPerCell"]

    # ---- 673 那 8 个碰撞名在 kS4 下的分离情况（1280 视口） ----
    rows0 = cells[keys[0]]["rows"]
    collisions = []
    for name, cnt in sorted(Counter(r["name"] for r in rows0).items()):
        if cnt < 2:
            continue
        sub = [r for r in rows0 if r["name"] == name]
        collisions.append({"name": name, "controls": len(sub),
                           "kS2keys": len({r["kS2"] for r in sub}),
                           "kS4keys": len({r["kS4"] for r in sub}),
                           "kS4DataValues": sorted({r["kS4"].split("|")[2] for r in sub})})

    def folded(ident: str) -> set[int]:
        c = Counter(r[ident] for r in rows0)
        return {i for i, r in enumerate(rows0) if c[r[ident]] > 1}

    sn, s2, s4 = folded("name"), folded("kS2"), folded("kS4")

    v.check("672s-family-table-is-reproduced-under-the-V3-reading",
            all(len(table_672[k]) == 8 for k in keys)
            and [len(_selected(cells, "name", "V3")[k]) for k in keys] == [73, 75, 76]
            and table_672[keys[0]]["relative.min-h-0.flex-1"] == 25
            and table_672[keys[2]]["absolute.inset-0"] == 22,
            detail={"table672Reproduced": table_672,
                    "controlsPerCell": flat("V3"),
                    "V3UsesIdentity": False},
            note="the table is reproduced cell-for-cell — and that is the point of the "
                 "next check: it reproduces because V3 never uses the identity")

    v.check("the-family-table-is-stable-because-V3-cannot-see-identity-not-because-it-is-robust",
            all(tables[f"{i}/V3"]["familyNamesPerCell"] == tables["name/V3"]["familyNamesPerCell"]
                for i in IDENTITIES)
            and tables["name/V3"]["controlsPerCell"] == tables["kS4/V3"]["controlsPerCell"],
            detail={"V3familyNamesIdenticalUnderAllIdentities": True,
                    "V3controlsPerCell": tables["kS4/V3"]["controlsPerCell"],
                    "why":
                        "V3 selects by trueFP alone. Its stability across identities is a "
                        "tautology, NOT evidence that the attribution is identity-robust"},
            note="do not read 'stable under 4 identities' as 'robust'")

    v.check("one-sentence-three-readings-three-tables-and-only-V1-moves-with-identity",
            flat("V1") != flat("V2") and flat("V2") != flat("V3")
            and tables["name/V1"]["controlsPerCell"] != tables["kS/V1"]["controlsPerCell"]
            and tables["kS/V1"]["controlsPerCell"] != tables["kS4/V1"]["controlsPerCell"],
            detail={"V1_byIdentity": {i: flat("V1", i) for i in IDENTITIES},
                    "V2_byIdentity": {i: flat("V2", i) for i in IDENTITIES},
                    "V3_byIdentity": {i: flat("V3", i) for i in IDENTITIES},
                    "history":
                        "670/672 printed '66 个名字每档都假阳性' (V2) next to '每档 73-76 格' "
                        "(V3). They are two different readings of one number."},
            note="V1 is the only reading that moves when the identity changes: "
                 "name 85 / kS 78 / kS2 73 / kS3 77 / kS4 73")

    v.check("name-folding-invents-a-ninth-family",
            tables["name/V1"]["familiesPerCell"] == [9, 9, 9]
            and tables["name/V3"]["familiesPerCell"] == [8, 8, 8]
            and "<no-class>" in tables["name/V1"]["familyNamesPerCell"][0],
            detail={"nameV1": tables["name/V1"]["familyNamesPerCell"][0],
                    "nameV3": tables["name/V3"]["familyNamesPerCell"][0],
                    "kS4V1families": tables["kS4/V1"]["familiesPerCell"],
                    "kS4V3families": tables["kS4/V3"]["familiesPerCell"],
                    "mechanism":
                        "V1 under the name identity pulls in 12 controls that are NOT "
                        "true-FP in that cell; their blame is an element with no class, so "
                        "a family appears that has no counterpart under V3 or under kS4"},
            note="collapsing a set can invent a category, not only merge members")

    v.check("kS4-splits-all-eight-of-673s-collision-names",
            len(collisions) == 8
            and all(c["kS4keys"] == c["controls"] for c in collisions),
            detail={"collisions": collisions,
                    "alwaysTrueKeysByIdentity": always_n},
            note="inside each colliding name, every control gets its own kS4 key")

    v.check("kS4s-residue-is-a-strict-subset-of-the-name-folded-set",
            len(s4) == 6 and len(sn) == 36
            and len(s4 - sn) == 0 and len(sn - s4) == 30,
            detail={"foldedControls": {"name": len(sn), "kS2": len(s2), "kS4": len(s4)},
                    "name_and_kS4": len(sn & s4),
                    "nameOnly": len(sn - s4), "kS4Only": len(s4 - sn),
                    "kS4ResidueNames": sorted({rows0[i]["name"] for i in s4}),
                    "kS4ResidueDiscriminators":
                        sorted({rows0[i]["kS4"].split("|")[2] for i in s4})},
            note="kS4 separates 30 of the 36 name-folded controls; the 6 it still folds "
                 "are the two tracks' nav triads, which the name identity folds too")

    prior = json.loads(B674_AUDIT.read_text(encoding="utf-8"))["verifier"]
    mine = list(prior["uniquish"])          # 674 按 IDENTITIES 次序存的是位置数组
    here = [ident_counts[i][keys[0]] for i in IDENTITIES]
    prior_swallowed = [prior["folds"][i][2] for i in IDENTITIES]
    mine_swallowed = [folds[i][keys[0]] for i in IDENTITIES]
    v.check("cross-run-identity-counts-match-batch674s-recorded-audit",
            len(mine) == len(here) and mine == here
            and prior_swallowed == mine_swallowed,
            detail={"batch674Uniquish": mine, "batch675Uniquish": here,
                    "batch674Swallowed": prior_swallowed,
                    "batch675Swallowed": mine_swallowed},
            note="same instrument, two independent runs — the readings are not run-specific")

    out = {"cells": keys, "controls": cells[keys[0]]["controls"],
           "identities": list(IDENTITIES),
           "identityCounts": ident_counts, "swallowed": folds,
           "alwaysTrueFPKeys": always_n,
           "table672Reproduced": table_672,
           "readings": tables, "collisions": collisions,
           "foldedControls": {"name": len(sn), "kS2": len(s2), "kS4": len(s4),
                              "name&kS4": len(sn & s4), "nameOnly": len(sn - s4),
                              "kS4Only": len(s4 - sn)},
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
