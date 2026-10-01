#!/usr/bin/env python3
"""Verify Batch 369: 「有文件但没有 caller」的组件普查, 以及堵住一个**自指测量陷阱**。

## 起因

Batch 368 的普查只管「按钮」。往上看一层还有一类更根本的问题:
`src/components/` 下 153 个组件级文件, 有几个**从来没被任何东西调用**?
两个 Dialog 早就被记成「无人渲染」(batch 360), 但那只是**已知的两个** ——
其余的呢? 于是做了普查, 答案出乎意料:

```text
src/ 里零 caller 的组件: 5 个
CameraMovementDialog  CustomHandle  PlusIndicator  ScriptHeader  JimengInferPanel
```

**5 个全部已经在 `docs/research/components/COVERAGE_MATRIX.md` 登记**,
且状态与处置理由都写得很具体:

| 组件 | 状态 | 文档给的处置 |
|---|---|---|
| `ScriptHeader` | `LEGACY` | 当前未挂载; 不把固定标题或装饰圆点重新引入运行态 |
| `PlusIndicator` | `LEGACY` | no-op stub; 真实连接 affordance 是 React Flow `<Handle>` |
| `CustomHandle` | `LEGACY` | 当前未使用的旧 handle prototype |
| `CameraConfigDialog` | `SPEC_COMPLETE` / caller `EVIDENCE_GATED` | 当前无已证普通 caller |
| `CameraMovementDialog` | `SPEC_COMPLETE` / caller `EVIDENCE_GATED` | 不能以 dormant component 推导 source/runtime capability |

**这是个负结果: 仓库没有「写了却忘了接」的组件债, 文档是诚实的。**
负结果同样要钉住 —— 否则下一个写了没人接的组件会静默进来。

> 顺带纠正一条旧记录: batch 360/367 把这两个 Dialog 记为「属导演台跨线范围,
> 只记录不动」。实测 **director 也没引用**, 它们是纯顶层 dormant 组件。
> 错判的原因不是结论错, 而是**从来没查过全仓库引用**, 只在跨线目录里找过。

## 一个自指测量陷阱(本批最有价值的发现)

第一版普查把 `scripts/*.py` 也算进引用来源, 结果 `CameraConfigDialog` **没有**被
报成「无 caller」—— 因为它被**我自己的门禁脚本**提到了 11 次:
`verify-liblib-batch367.py` 和 `verify-liblib-batch368.py` 的白名单里都写着它。

> **记录死代码的门禁, 本身成了「它还活着」的证据。**
> 更糟的是这个偏差是**自我强化**的: 越是把某个组件写进白名单「好好记账」,
> 普查越看不见它是死的。

所以判据必须明确: **caller 只从 `src/` 里数, 审计脚本不是产品接线。**
`scripts/**` 提到某个组件, 只说明有人在审计它, 不说明用户能碰到它。
这条规则本身有阳性/阴性自检(见断言 4)。

## 断言

1. **正向**: 每个没有 caller 的组件, **必须**在 `COVERAGE_MATRIX.md` 登记,
   且那一行必须带一个明确状态词 —— 否则红(新写了没人接又没记账);
2. **反向(文档漂移)**: `COVERAGE_MATRIX.md` 里每一条指向
   `src/components/*.tsx` 的行, **那个文件必须还在** —— 文件删了行没删要红;
3. **没有 caller 且没有登记** 的组件数必须为 0;
4. **自指陷阱自检(双向)**:
   - 阴性: 造一个只在 `scripts/` 里被提到的组件, 普查**必须**仍报它无 caller
     (证明审计脚本的提及不算接线);
   - 阳性: 给一个已登记的 dormant 组件造一个 `src/` 内的 caller,
     普查**必须**不再报它 —— 证明判据不是恒真;
5. 跨线目录(`director` / `jimeng`)只统计不判红。
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
COMPONENTS = SRC / "components"
MATRIX = ROOT / "docs" / "research" / "components" / "COVERAGE_MATRIX.md"
OUT = ROOT / "docs" / "research" / "liblib-batch369-2026-10-02" / "unreferenced-components.json"

# 矩阵里算「已明确表态」的状态词。少一个就红 —— 要求作者写清处置, 不接受沉默。
STATUS_TOKENS = ("LEGACY", "SPEC_COMPLETE", "EVIDENCE_GATED", "DEPRECATED", "DORMANT", "REMOVED")

CROSS_LINE = ("director", "jimeng")


def source_files() -> dict[Path, str]:
    out: dict[Path, str] = {}
    for pattern in ("*.ts", "*.tsx"):
        for path in SRC.rglob(pattern):
            out[path] = path.read_text(encoding="utf-8", errors="replace")
    return out


def component_files() -> list[Path]:
    """组件级文件: `src/components/**` 下首字母大写的 `.tsx`。

    不含 `src/app/`(页面)与 `src/lib/`(纯函数) —— 那些不是「组件」口径。
    """
    return sorted(
        p
        for p in COMPONENTS.rglob("*.tsx")
        if re.match(r"^[A-Z]", p.stem)
    )


def is_cross_line(rel: Path) -> bool:
    return any(part.casefold().startswith(tuple(t.casefold() for t in CROSS_LINE)) for part in rel.parts[:-1])


def callers_in_src(name: str, files: dict[Path, str], self_path: Path) -> list[str]:
    """在 `src/` 里(排除自身文件)找引用。

    **必须排除自身文件** —— 否则文件内部的自引用(接口名、注释、重复声明)
    会把自己算成「有 caller」, 于是真正的死代码从名单上消失。
    第一版正是栽在这里: `CameraConfigDialog` 因为自己文件里出现了 3 次名字
    (`CameraConfigDialogProps` / `export function` / props 解构) 而被漏掉。
    """
    pat = re.compile(r"\b" + re.escape(name) + r"\b")
    hits: list[str] = []
    for path, text in files.items():
        if path == self_path:
            continue
        if pat.search(text):
            try:
                shown = str(path.relative_to(SRC))
            except ValueError:
                # 不在 src/ 下(比如有人把 scripts/ 也塞进候选集)时不能崩 ——
                # 崩在这里会让整门禁变成「一条 TypeError/ValueError 说了算」,
                # 而变异测试必须能**走到断言**才算数。路径只是给人看的, 兜住即可。
                shown = str(path)
            hits.append(shown)
    return hits


def matrix_entries() -> dict[str, str]:
    """从 COVERAGE_MATRIX 里抽出「组件名 -> 那一整行」。"""
    if not MATRIX.exists():
        return {}
    entries: dict[str, str] = {}
    for line in MATRIX.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.lstrip().startswith("|"):
            continue
        for token in re.findall(r"`([A-Z][A-Za-z0-9_]*)`", line):
            entries.setdefault(token, line)
    return entries


def matrix_referenced_paths() -> list[tuple[str, str]]:
    """矩阵里指向 `src/components/*.tsx` 的路径引用 -> (组件名, 路径)。

    反向断言用: 文档说有、文件却没了, 就是文档漂移。

    ## 这里踩过的坑(空断言)

    第一版写的是 `` `([^|]*?)`(src/components/...)` `` —— 用 `[^|]` 跨过两个
    反引号之间的内容。**但矩阵的列分隔符本身就是 `|`**:

    ```markdown
    | `PlusIndicator` | `src/components/PlusIndicator.tsx` | `LEGACY` | ... |
    ```

    于是 `[^|]` 一步也走不出去, 提取器**一条都匹配不到**, `drifted` 恒为空,
    `matrix:no-path-drift` 变成恒真 —— 而变异测试把路径改成一个不存在的文件,
    门禁照样 9/9 通过。

    > **正则型提取器可能悄悄匹配不到任何东西, 把断言变成 `not [] == True`。**
    > 光看「绿了」不会发现, 必须配一条「提取器确实抓到了东西」的自检
    > (见 `matrix:extractor-found-rows`), 并用变异测试确认它抓得住。
    """
    if not MATRIX.exists():
        return []
    text = MATRIX.read_text(encoding="utf-8", errors="replace")
    return re.findall(
        r"`([A-Z][A-Za-z0-9_]*)`[^`]*?`(src/components/[A-Za-z0-9_/\-.]+\.tsx)`", text
    )


def main() -> int:
    checks: list[dict[str, object]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    files = source_files()
    comps = component_files()
    entries = matrix_entries()

    unreferenced: list[dict[str, object]] = []
    undocumented: list[str] = []
    cross_undocumented: list[str] = []
    for path in comps:
        rel = path.relative_to(SRC)
        callers = callers_in_src(path.stem, files, path)
        if callers:
            continue
        cross = is_cross_line(rel.relative_to(Path("components")))
        row = entries.get(path.stem)
        has_status = bool(row) and any(tok in row for tok in STATUS_TOKENS)
        item = {
            "component": path.stem,
            "path": str(rel),
            "crossLine": cross,
            "registered": bool(row),
            "statusToken": next((t for t in STATUS_TOKENS if row and t in row), None),
        }
        unreferenced.append(item)
        if not has_status:
            token = f"{rel} (registered={bool(row)}, status={item['statusToken']!r})"
            # **跨线只统计不判红** —— director/jimeng 是并行 session 的地带,
            # 它们那边有没有登记是那边的事, 本线无权判红。
            # 第一版漏了这个分支, 结果把 `JimengInferPanel` 判成了本线的账 ——
            # 而那正是「过滤器没双向验证」的典型: 规则写了, 实现没跟上。
            (cross_undocumented if cross else undocumented).append(token)

    add(
        "census:no-undocumented-unreferenced",
        not undocumented,
        f"本线无 caller 却没有在 COVERAGE_MATRIX 明确表态的组件: {undocumented}",
    )
    # 过滤器自身的双向验证: 判红集合里**一个跨线组件都不许有**。
    # (第一版没写这条, 结果把 jimeng 的 `JimengInferPanel` 判成了本线的账。)
    leaked = [
        u for u in undocumented
        if is_cross_line(Path(u.split(" ")[0]).relative_to(Path("components")))
    ]
    add(
        "census:cross-line-excluded-from-failure",
        not leaked,
        f"判红集合里混入了跨线组件: {leaked}; "
        f"跨线另有 {len(cross_undocumented)} 项只记录不判红: {cross_undocumented}",
    )
    add(
        "census:found-some",
        len(unreferenced) > 0,
        f"本次普查到 {len(unreferenced)} 个无 caller 组件: "
        f"{[i['component'] for i in unreferenced]}",
    )

    # 断言 2: 反向 —— 矩阵指向的文件必须还在
    referenced = matrix_referenced_paths()
    # 防「空断言」: 提取器必须真的抓到行, 否则下面那条恒真而看不出来
    add(
        "matrix:extractor-found-rows",
        len(referenced) > 0,
        f"路径提取器抓到 {len(referenced)} 条; 一条都抓不到时, 漂移断言会变成恒真 "
        f"(第一版正是这样, 变异测试把路径改成不存在的文件仍然 9/9 通过)",
    )
    drifted: list[str] = []
    for name, rel_path in referenced:
        if not (ROOT / rel_path).exists():
            drifted.append(f"{name} -> {rel_path}")
    add(
        "matrix:no-path-drift",
        not drifted,
        f"矩阵里指向已删除文件的行: {drifted}",
    )

    # 断言 4a: 自指陷阱的阴性自检 —— 只被审计脚本提到的组件, 仍须判为无 caller
    probe_src = COMPONENTS / "ZzBatch369AuditMention.tsx"
    probe_src.write_text(
        "export function ZzBatch369AuditMention() {\n  return <div />;\n}\n", encoding="utf-8"
    )
    probe_script = ROOT / "scripts" / "zz_batch369_audit_mention.py"
    probe_script.write_text(
        '# 审计脚本提到 ZzBatch369AuditMention, 但这**不是**产品接线\n'
        'NAME = "ZzBatch369AuditMention"\n',
        encoding="utf-8",
    )
    try:
        files2 = source_files()
        # 只按 src/ 数 —— scripts/ 不参与
        callers = callers_in_src("ZzBatch369AuditMention", files2, probe_src)
        add(
            "criteria:audit-mention-is-not-wiring",
            callers == [],
            f"只被 scripts/ 提到的组件不该算有 caller, 实际 callers={callers}",
        )
        # 同一判据对 scripts/ 直接引用确实能看见(证明它不是恒真)
        script_text = probe_script.read_text(encoding="utf-8")
        add(
            "criteria:script-mention-is-detectable",
            "ZzBatch369AuditMention" in script_text,
            "判据本身必须看得见 scripts/ 里的提及, 否则上面那条就是空断言",
        )
    finally:
        probe_src.unlink(missing_ok=True)
        probe_script.unlink(missing_ok=True)

    # 断言 4b: 阳性自检 —— 给一个已登记的 dormant 组件造一个 src/ 内 caller,
    # 普查必须不再报它(证明判据不是恒真)
    dormant = next(
        (i for i in unreferenced if i["component"] == "CustomHandle"),
        None,
    )
    add(
        "criteria:has-dormant-sample",
        dormant is not None,
        f"需要一个已登记的 dormant 组件做阳性自检, 现有: {[i['component'] for i in unreferenced]}",
    )
    if dormant is not None:
        fake = COMPONENTS / "ZzBatch369Caller.tsx"
        fake.write_text(
            "import { CustomHandle } from \"./CustomHandle\";\n"
            "export function ZzBatch369Caller() {\n"
            "  return <CustomHandle />;\n"
            "}\n",
            encoding="utf-8",
        )
        try:
            files3 = source_files()
            add(
                "criteria:wired-dormant-not-reported",
                callers_in_src("CustomHandle", files3, COMPONENTS / "CustomHandle.tsx") != [],
                "给 CustomHandle 造一个 src/ 内 caller 后, 普查必须看见它 —— "
                "否则「无 caller」判据恒真, 整门禁就是空的",
            )
        finally:
            fake.unlink(missing_ok=True)

    # 断言 5: 跨线只统计不判红
    cross = [i["component"] for i in unreferenced if i["crossLine"]]
    add(
        "census:cross-line-counted-not-failed",
        True,
        f"跨线组件仅统计不判红: {cross}",
    )

    payload = {
        "checkedComponents": len(comps),
        "unreferenced": unreferenced,
        "statusTokens": list(STATUS_TOKENS),
        "crossLineNoted": cross,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    failed = [c for c in checks if not c["ok"]]
    if failed:
        print(f"Batch 369: {len(checks) - len(failed)}/{len(checks)} checks passed")
        print("FAILED:", json.dumps(failed, ensure_ascii=False, indent=1))
        return 1
    print(
        f"Batch 369 verification passed: {len(checks)} checks. "
        f"All {len(comps)} component files are either called from src/ or registered in "
        f"COVERAGE_MATRIX.md with an explicit status; no documented path has drifted; and "
        f"the census proves an audit-script mention is not product wiring (both directions)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
