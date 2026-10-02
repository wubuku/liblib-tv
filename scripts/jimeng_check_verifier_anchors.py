#!/usr/bin/env python3
"""verifier 锚点自查：把 `check(...)` 里所有指向 `_ausrc` 的锚点**逐个**验一遍。

## 为什么要有这个脚本

锚点写在 `verify-jimeng-batch841-unclickable.py`，被验的字在
`jimeng_unclickable_audit.py`。改基线后如果某个锚点对不上，那条判据会在**跑
完整门禁之后**才红 —— 而门禁要几分钟。更糟的是**反过来的假绿**：

`_ausrc` 是**原始文件文本**，而判据里的锚点常写成**相邻字面量拼接**
（`"foo "` + `"bar"`）。用正则去源码里找 `"foo "` 会**找到**，于是自查说
「没问题」，可运行时拼出来的是 `"foo bar"`，**在原文里根本不存在** ⇒
判据其实已经红了。**这个坑踩过两次**，所以固化成脚本。

⇒ 所以这里用 `ast`：Python 在**解析期**就把相邻字面量合并成**一个**
`Constant`，拿它去原文里找才是准的。

## 查什么

对每条 `check(...)`：

- `"X" in _ausrc` ⇒ `X` 必须**原样**出现在 audit 源码里，否则 `MISSING`
- `"X" not in _ausrc` ⇒ `X` 必须**不在** audit 源码里，否则 `WOULD-FAIL`
  （反向断言专门用来钉「旧措辞不许留在基线里」，最容易悄悄失效）

另外统计 `_pXXX` 那些探针文件锚点（同样查，只是不参与 `_ausrc` 判定）。

跑法：
  /opt/miniconda3/bin/python3 scripts/jimeng_check_verifier_anchors.py
退出码 0 = 全通；1 = 有问题。
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "scripts/jimeng_unclickable_audit.py"
VERIFIER = ROOT / "scripts/verify-jimeng-batch841-unclickable.py"

# 探针文件变量名 → 路径（这些锚点查的是探针源码，不是基线）
PROBE_VARS = {
    "_p868": "scripts/jimeng_probe868_textbar.py",
    "_p894": "scripts/jimeng_probe894_node_tabindex_matrix_src.py",
    "_p895": "scripts/jimeng_probe895_node_tabindex_matrix_ck.py",
    "_p896": "scripts/jimeng_probe896_roving_tabindex_policy_src.py",
    "_p897": "scripts/jimeng_probe897_ck_type_coverage.py",
    "_p898": "scripts/jimeng_probe898_ck_focus_lands_on_wrapper.py",
    # ⚠️ 900–905 这几条**曾经漏登记** ⇒ 它们的锚点自查**一直没收过**
    #（是 905 的 SS.4 FAIL 顺带发现的：判据引的句子在探针里根本没有，
    #  与 CC.8 同一个坑）。**探针一多就必须补登记**，否则自查是假绿。
    "_p900": "scripts/jimeng_probe900_unarmed_nodes_src.py",
    "_p901": "scripts/jimeng_probe901_roving_impl_ck.py",
    "_p902": "scripts/jimeng_probe902_unmeasured_cells_src.py",
    "_p903": "scripts/jimeng_probe903_carried_state_src.py",
    "_p904": "scripts/jimeng_probe904_endpoint_condition_src.py",
    "_p905": "scripts/jimeng_probe905_reentry_focus_src.py",
    "_p906": "scripts/jimeng_probe906_direction_asymmetry_src.py",
    "_p907": "scripts/jimeng_probe907_endpoint_to_start_map_src.py",
    "_p908": "scripts/jimeng_probe908_wrap_around_src.py",
}


def _const_str(node: ast.AST) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(
        node.value, str) else None


def collect(tree: ast.AST) -> list[tuple[str, str, bool]]:
    """抽出 (目标变量, 锚点, 是否取反)。"""
    out: list[tuple[str, str, bool]] = []
    for call in ast.walk(tree):
        if not isinstance(call, ast.Call):
            continue
        fn = call.func
        if not (isinstance(fn, ast.Name) and fn.id == "check"):
            continue
        for node in ast.walk(call):
            if not isinstance(node, ast.Compare):
                continue
            for op, comp in zip(node.ops, node.comparators):
                # ⚠️ `X in Y` 是 `In`、`X not in Y` 是 **`NotIn`**（**不是** `Not`
                #    —— `Not` 只出现在一元 `not` 上，漏了它会把反向断言当成正向）
                if not isinstance(op, (ast.In, ast.NotIn)):
                    continue
                neg = isinstance(op, ast.NotIn)
                # ⚠️ `"X" in _ausrc` 解析成 Compare(left=Constant("X"),
                #    ops=[In], comparators=[Name("_ausrc")]) ——
                #    **锚点在 left、目标变量在 comparators**（别搞反）
                name = comp.id if isinstance(comp, ast.Name) else None
                s = _const_str(node.left)
                if s is None or name is None:
                    continue
                if name != "_ausrc" and name not in PROBE_VARS:
                    continue
                out.append((name, s, neg))
    return out


def main() -> int:
    if not AUDIT.exists() or not VERIFIER.exists():
        print("找不到 audit / verifier 源码", file=sys.stderr)
        return 1
    ausrc = AUDIT.read_text(encoding="utf-8")
    probes = {k: (ROOT / v).read_text(encoding="utf-8")
              if (ROOT / v).exists() else ""
              for k, v in PROBE_VARS.items()}

    items = collect(ast.parse(VERIFIER.read_text(encoding="utf-8")))
    problems = 0
    n_ausrc = 0
    for name, anchor, neg in items:
        hay = ausrc if name == "_ausrc" else probes.get(name, "")
        present = anchor in hay
        if name == "_ausrc":
            n_ausrc += 1
        if neg and present:
            print(f"WOULD-FAIL  [{name}] {anchor!r}")
            problems += 1
        elif not neg and not present:
            print(f"MISSING     [{name}] {anchor!r}")
            problems += 1

    print(f"\n锚点 {len(items)} 条（其中指向 _ausrc 的 {n_ausrc} 条），"
          f"问题 {problems} 个")
    if problems:
        print("⇒ 有判据已经失效/或被改成永远为真，**别等门禁跑完才发现**。")
        return 1
    print("⇒ 全通 ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
