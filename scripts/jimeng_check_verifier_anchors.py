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
    "_p909": "scripts/jimeng_probe909_canvas_root_ck.py",
    "_p910": "scripts/jimeng_probe910_endpoint_to_start_rescan_src.py",
    "_p911": "scripts/jimeng_probe911_threshold_bisect_src.py",
    "_p912": "scripts/jimeng_probe912_threshold_bisect2_src.py",
    "_p913": "scripts/jimeng_probe913_same_endpoint_two_routes_src.py",
    "_p914": "scripts/jimeng_probe914_two_routes_real_backwalk_src.py",
    "_p915": "scripts/jimeng_probe915_prehistory_irrelevance_src.py",
    "_p916": "scripts/jimeng_probe916_bite_then_walkback_src.py",
    "_p917": "scripts/jimeng_probe917_multi_bite_focus_trace_src.py",
    "_p918": "scripts/jimeng_probe918_movedonly_and_taborder_src.py",
    "_p919": "scripts/jimeng_probe919_inner_control_anatomy_src.py",
    "_p920": "scripts/jimeng_probe920_per_press_wrapper_census_src.py",
    "_p921": "scripts/jimeng_probe921_full_table_and_delta_src.py",
    "_p922": "scripts/jimeng_probe922_reverse_arm_window_src.py",
    "_p923": "scripts/jimeng_probe923_continuous_arm_stream_src.py",
    "_p924": "scripts/jimeng_probe924_both_boundaries_src.py",
    "_p925": "scripts/jimeng_probe925_past_zero_boundary_src.py",
    "_p926": "scripts/jimeng_probe926_window_survives_freeze_src.py",
    "_p927": "scripts/jimeng_probe927_early_writeback_repro_src.py",
    "_p928": "scripts/jimeng_probe928_replica_same_ruler.py",
    "_p929": "scripts/jimeng_probe929_long_tail_wrap_or_not_src.py",
    "_p930": "scripts/jimeng_probe930_second_wrap_src.py",
    "_p931": "scripts/jimeng_probe931_reverse_lap_cycle_src.py",
    "_p932": "scripts/jimeng_probe932_same_27_cycle_src.py",
    "_p933": "scripts/jimeng_probe933_body_stop_rate_src.py",
    "_p934": "scripts/jimeng_probe934_body_own_attrs_src.py",
    "_p935": "scripts/jimeng_probe935_body_stop_sweep_src.py",
    "_p936": "scripts/jimeng_probe936_inlayer_occlusion_src.py",
    "_p937": "scripts/jimeng_probe937_layer_exclusivity_src.py",
    "_p938": "scripts/jimeng_probe938_replica_layer_exclusivity.py",
    # ⚠️ 批 939：**两个**探针都得登记 —— 939 第一版（已作废、留痕不删）
    #    与 939b（判决版）。⚠️ 登记了还不够，判据得**真的用**这些名字
    #    （937 教训：登记表加了名字 ≠ 名字进了被遍历的那张表）。
    "_p939": "scripts/jimeng_probe939_tab_distance_src.py",
    "_p939b": "scripts/jimeng_probe939b_tab_constitution_src.py",
    # 批 940：判据开始**钉探针里的「阴性结构保证」**
    #    （`n_marked_is_node == 0` 是 `B939_SEL` 不选 `div` 推出来的，不是碰巧）
    "_p940": "scripts/jimeng_probe940_tabindex_rewrite_src.py",
    # 批 941：判据开始**钉 940 那个有缺陷的判据仍在源码里**
    #    （供下一个人对照，别删）——「造对一件事、顺手弄坏五件」的反面
    "_p941": "scripts/jimeng_probe941_layer_identity_probe_src.py",
    # 批 938：判据开始**钉 TS 源码**（槽位是 store 里的单一来源）
    "_wm_s": "src/store/jimengStore.ts",
    # ⚠️⚠️ **929 加的**：**门禁脚本自己**也必须登记 ——
    #    PPP.3 要钉「第二道 Python 语法门真的加进它了」，
    #    那道门就**长在这个文件里** ⇒ 不登记它，锚点就查不到。
    "_syn": "scripts/jimeng_probe_js_syntax_check.py",
    # ⚠️ 909 第一次把判据钉在**组件源码的实现字面量**上（判据写在
    # `armRovingTabindex` 里）⇒ 组件源码**必须登记进 PROBE_VARS**。
    # ⚠️⚠️ 第一次我把它误写进了一个**没人读**的 `SRC_VARS` ⇒
    # 锚点条数只涨了 22 而不是 30、**自查假绿**、两条坏锚点直到门禁才炸。
    # ⇒ **教训与 900–905 漏登记同一个**：登记表加了名字还不够，
    # **得确认那个名字真的进了被遍历的那张表**。
    "_wsrc": "src/components/jimeng/JimengWorkspace.tsx",
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
