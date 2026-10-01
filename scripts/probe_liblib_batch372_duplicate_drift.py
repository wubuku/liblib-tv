#!/usr/bin/env python3
"""Batch 372 普查: 跨脚本重复的辅助函数, 副本之间**漂移了多少**。

## 起因

Batch 371 抓到一个模式: 同一个缺陷隔着一份代码复制到另一条线, **只修了一份**。
`run-liblib-verifiers.sh` 的「汇总与清单同源」早已修好, 而
`run-frameos-verifiers.sh` 里同一份逻辑一直带着 bug。

那只是两个 runner。普查一翻, 发现这仓库里**到处都是这种副本**:

```text
616 份  main
343 份  attach_errors
310 份  run_desktop
 69 份  assert_no_overflow
 61 份  run_mobile
 45 份  open_director
 26 份  director_state
 …
```

**一份修复要抵达 343 份副本, 靠人是不可能完成的。** 所以先量一件事:
**这些副本到底还一样吗?** 如果它们已经漂移, 那么「改一处」和「改全部」之间的
差距就是实际存在的风险敞口。

## 方法与它的边界

- 按 `^def NAME(` 切出函数体(到下一个顶层 `def`/`class`/文件尾);
- 归一化: 去空行、去纯注释行、去行首缩进差异、折叠行尾空白;
- 然后按 body 的哈希分组: **同一个哈希 = 逐字相同的副本**, 不同哈希 = 已漂移。

> 边界要说清楚: 这是**文本**层面的比较, 不是行为层面的。它**看不见**
> 「两段代码字面不同但行为等价」(比如变量改名)。所以「漂移数」是**上界估计** ——
> 真实的行为差异只会更少, 不会更多。反过来说, **文本相同一定行为相同**,
> 所以「完全一致的副本数」这个下界是可靠的。

## 输出

- 每个函数: 副本数、逐字一致的组数、漂移的组数、最大组的占比
- 漂移最严重的函数明细(便于人工挑出「哪些副本才是真正在用的」)
"""

from __future__ import annotations

import collections
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
OUT = ROOT / "docs" / "research" / "liblib-batch372-2026-10-02" / "duplicate-helper-drift.json"

DEF_RE = re.compile(r"^def (\w+)\(", re.M)
TOP_LEVEL_RE = re.compile(r"^(def |class |@)", re.M)


def split_functions(text: str) -> dict[str, str]:
    """把源码切成 {函数名: 函数体}。只处理顶层 def。"""
    out: dict[str, str] = {}
    starts = [(m.start(), m.group(1)) for m in DEF_RE.finditer(text)]
    for i, (pos, name) in enumerate(starts):
        end = len(text)
        rest = text[pos + 1:]
        nxt = TOP_LEVEL_RE.search(rest)
        if nxt:
            end = pos + 1 + nxt.start()
        out[name] = text[pos:end]
    return out


def normalize(body: str) -> str:
    """去空行、去整行注释、去行首缩进、折叠行尾空白。"""
    lines = []
    for raw in body.splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        lines.append(s)
    return "\n".join(lines)


def main() -> int:
    per_name: dict[str, dict[str, str]] = collections.defaultdict(dict)
    scanned = 0
    for path in sorted(SCRIPTS.glob("*.py")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            continue
        scanned += 1
        for name, body in split_functions(text).items():
            norm = normalize(body)
            if not norm:
                continue
            digest = hashlib.sha1(norm.encode("utf-8")).hexdigest()[:12]
            per_name[name].setdefault(digest, []).append(path.name)

    report: list[dict[str, object]] = []
    for name, groups in per_name.items():
        total = sum(len(v) for v in groups.values())
        if total < 2:
            continue
        variants = sorted(groups.items(), key=lambda kv: -len(kv[1]))
        report.append({
            "name": name,
            "copies": total,
            "distinctVariants": len(groups),
            "identicalCopies": len(variants[0][1]),
            "largestGroupShare": round(len(variants[0][1]) / total, 3),
            "variants": [
                {"digest": d, "count": len(files), "files": sorted(files)[:6]}
                for d, files in variants
            ],
        })

    report.sort(key=lambda r: (-int(r["copies"]), str(r["name"])))
    drifted = [r for r in report if int(r["distinctVariants"]) > 1]
    total_copies = sum(int(r["copies"]) for r in report)
    drifted_copies = sum(int(r["copies"]) for r in drifted)

    payload = {
        "scriptsScanned": scanned,
        "functionsWithCopies": len(report),
        "functionsDrifted": len(drifted),
        "totalCopies": total_copies,
        "copiesInDriftedFunctions": drifted_copies,
        "method": {
            "unit": "顶层 def 的函数体",
            "normalize": "去空行 / 去整行注释 / 去行首缩进 / 折叠行尾空白",
            "comparison": "sha1 前 12 位",
            "caveat": "文本层面比较: 同一哈希**一定**行为等价(可靠下界); "
                      "不同哈希**未必**行为不同(字面不同但行为等价的情况算进漂移, "
                      "所以漂移数是**上界**)",
        },
        "top": [
            {
                "name": r["name"], "copies": r["copies"],
                "distinctVariants": r["distinctVariants"],
                "identicalCopies": r["identicalCopies"],
            }
            for r in report[:25]
        ],
        "full": report,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"扫描 {scanned} 个脚本")
    print(f"有 2+ 份副本的函数: {len(report)} 个, 合计 {total_copies} 份副本")
    print(f"其中已漂移的函数: {len(drifted)} 个, 涉及 {drifted_copies} 份副本\n")
    print(f"{'函数':<24}{'副本':>6}{'变体':>6}{'最大组':>8}{'占比':>8}")
    for r in report[:20]:
        print(f"  {r['name']:<22}{r['copies']:>6}{r['distinctVariants']:>6}"
              f"{r['identicalCopies']:>8}{str(r['largestGroupShare']):>8}")
    print(f"\nwrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
