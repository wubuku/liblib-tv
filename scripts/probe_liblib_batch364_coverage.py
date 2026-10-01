#!/usr/bin/env python3
"""普查: 哪些画布本体组件的 data-* 标记从未被任何 liblib 门禁引用。

Batch 364 立项依据。**先验证判据本身**:

第一版判据是「组件名在门禁里出现过没有」, 扫出 30 个「未覆盖」组件 ——
但 `ImageEditPanel` 明明被 batch359 的节点面普查完整扫过, 只是它引用的是
`data-image-edit-panel` 这类标记, 不提组件名。
> **判据错了, 结论就全错。** 「组件名」不是覆盖的证据, `data-*` 才是 ——
> 因为门禁靠标记定位元素, 不靠组件名。

所以本普查改为: 取每个组件源码里的 `data-*` 标记, 看有没有门禁引用过。
**`data-*` 是本线的可测性契约**(每个可交互面都带标记), 因此它同时也是
「这个面有没有被验证过」的直接证据。

判定:
  UNCOVERED  —— 组件有 data-* 标记, 但**没有任何门禁引用过其中任何一个**
               = 从未被验证过的面, 交互谎言最可能藏在这里
  PARTIAL    —— 只被引用了一部分标记 = 有验证, 但覆盖不全
  COVERED    —— 标记被充分引用

注意: 零 `data-*` 标记的组件**不报** —— 那是「不可测」而非「未覆盖」,
另由 verify-assertions 那类门禁兜着, 混进来会污染结论。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ROOT / "src" / "components"
GATES = sorted((ROOT / "scripts").glob("verify-liblib-*.py"))
OUT = ROOT / "docs" / "research" / "liblib-batch364-2026-10-01" / "coverage-census.json"

# 跨线: 有并行 session 未提交 WIP, 不普查(只记录, 不动)
CROSS_LINE = ("director", "jimeng")

DATA_ATTR = re.compile(r'\bdata-([a-z0-9-]+)')

# 门禁里引用标记的写法五花八门(data-x= / "data-x" / [data-x]) —— 统一按子串找
gate_text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in GATES)


def main() -> int:
    census: dict[str, object] = {"components": {}, "summary": {}}
    uncovered: list[str] = []
    partial: list[str] = []
    covered = 0
    untestable: list[str] = []

    for path in sorted(COMPONENTS.glob("*.tsx")):
        name = path.stem
        if any(x in str(path) for x in CROSS_LINE):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        # 只取 JSX 里的 data-* (源码里注释中的不算, 避免把「文档里提到」
        # 误判成「可测标记」)
        marks = sorted({m for m in DATA_ATTR.findall(text)})
        if not marks:
            untestable.append(name)
            census["components"][name] = {"dataMarks": [], "state": "UNTESTABLE"}
            continue
        hit = [m for m in marks if m in gate_text]
        miss = [m for m in marks if m not in gate_text]
        state = "COVERED" if not miss else ("PARTIAL" if hit else "UNCOVERED")
        census["components"][name] = {
            "dataMarks": marks,
            "hit": hit,
            "miss": miss,
            "state": state,
        }
        if state == "UNCOVERED":
            uncovered.append(name)
        elif state == "PARTIAL":
            partial.append(name)
        else:
            covered += 1

    census["summary"] = {
        "componentsScanned": len(census["components"]),
        "covered": covered,
        "partial": len(partial),
        "uncovered": len(uncovered),
        "untestable": len(untestable),
        "uncoveredNames": uncovered,
        "partialNames": partial,
        "untestableNames": untestable,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(census, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"scanned {census['summary']['componentsScanned']} canvas components")
    print(f"  COVERED    {covered}")
    print(f"  PARTIAL    {len(partial)}: {' '.join(partial)}")
    print(f"  UNCOVERED  {len(uncovered)}: {' '.join(uncovered)}")
    print(f"  UNTESTABLE {len(untestable)} (no data-* marks; not reported as uncovered)")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
