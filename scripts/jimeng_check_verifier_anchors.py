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
    # ⚠️⚠️⚠️ 批 946：这张表**停在 `_p941` 就是个真口子** ——
    #    943 / 944a / 944b / 945 / 946 这五个探针**一个都没登记**，
    #    于是它们身上的锚文**从来没被自查过**。
    #    代价当场就付了：HHHH.6 有一条锚文 `**这道门恒绿，等于没有门**`
    #    在探针里其实是 `—— 这道门恒绿，等于没有门`（**没有加粗标记**），
    #    而锚点自查报的是「1645 条 / **0 个问题**」⇒
    #    **一道没登记的锚文，等于一道不存在的锚文**。
    #    ⇒ 下面每加一个探针，**必须同时在这里登记**，否则自查形同虚设。
    "_p943": "scripts/jimeng_probe943_arm_relation_src.py",
    "_p944a": "scripts/jimeng_probe944a_node_inner_scan_src.py",
    "_p944b": "scripts/jimeng_probe944b_mouse_axes_src.py",
    "_p945": "scripts/jimeng_probe945_comp_scale_split_src.py",
    "_p946": "scripts/jimeng_probe946_prestate_src.py",
    "_p947": "scripts/jimeng_probe947_stablewait_src.py",
    "_p948": "scripts/jimeng_probe948_settle_landing_src.py",
    "_p949": "scripts/jimeng_probe949_replay944_src.py",
    "_p950": "scripts/jimeng_probe950_coldwindow_src.py",
    "_p951": "scripts/jimeng_probe951_focus_gate_src.py",
    "_p952": "scripts/jimeng_probe952_freeze_who_src.py",
    "_p953": "scripts/jimeng_probe953_roving_ring_ck.py",
    "_p954": "scripts/jimeng_probe954_source_ring_src.py",
    "_p955": "scripts/jimeng_probe955_onekey_inner_src.py",
    "_p956": "scripts/jimeng_probe956_replica_ring_ck.py",
    # ⚠️⚠️⚠️ 961 补登记：`_p957`–`_p960` **一直漏登记**，而收集器对**未登记**
    #   的变量是 `continue`（**静默跳过**）⇒ 那四批的**探针锚点一次都没被
    #   自查过**（只有指向 `_ausrc` 的那些被查了）⇒ 补上。
    "_p957": "scripts/jimeng_probe957_rail_roving_src.py",
    "_p958": "scripts/jimeng_probe958_rail_roving_ck.py",
    "_p959": "scripts/jimeng_probe959_domorder_src.py",
    "_p960": "scripts/jimeng_probe960_taborder_src.py",
    "_p961": "scripts/jimeng_probe961_ticensus_src.py",
    # ⚠️⚠️ 962：**我第一遍忘了登记 `_p962`** ⇒ 整组 `XXXX.*` 的锚文**全被静默跳过**（「0 问题」又一次是假绿）⇒ 同一个坑，**隔一层**又踩一次
    "_p962": "scripts/jimeng_probe962_focusmove_src.py",
    "_p963": "scripts/jimeng_probe963_nodecensus_src.py",
    "_p964": "scripts/jimeng_probe964_skipwhy_src.py",
    "_p965": "scripts/jimeng_probe965_focusable_src.py",
    "_p966": "scripts/jimeng_probe966_clicksel_src.py",
    # ⚠️ 967：**与写 `DDDD.*` 判据同一步登记** —— 962/963/964/965 各栽过一次，
    #   症状都是「新增变量没登记 ⇒ 锚点自查把整组**静默跳过** ⇒ 报 0 问题」
    "_p967": "scripts/jimeng_probe967_armptr_src.py",
    # ⚠️ 968/968b：**同样与写 `AAAAA.*` 判据同一步登记**（同一个坑，第三次预防）
    "_p968": "scripts/jimeng_probe968_replica_armptr_ck.py",
    "_p968b": "scripts/jimeng_probe968b_nextjsportal_ck.py",
    # ⚠️ 969：**同一步**登记（第四次预防同一个坑）
    "_p969": "scripts/jimeng_probe969_projectpanel_src.py",
    # ⚠️ 970：**同一步**登记（第五次预防同一个坑）
    "_p970": "scripts/jimeng_probe970_owntid_ck.py",
    # ⚠️⚠️ 971：**同一步**登记（第六次预防同一个坑）——
    #   ⭐⭐⭐ `EEEEE.3` 有一条判据要**反证 `_p971` 真被读过**
    #   ⇒ 而这条登记若漏掉，那个反证就是**恒真**（锚点自查会 `continue` 静默跳过）
    "_p971": "scripts/jimeng_probe971_savestate_src.py",
    # ⚠️⚠️ 972：**同一步**登记（第六次预防同一个坑）——
    #   ⭐⭐⭐ `FFFFF.2` 要钉「两套口径的差额恰好是被吃掉的那一枚」，
    #   而这条判据的锚文全在 972 探针里 ⇒ 漏登记 = 整条判据恒假绿
    "_p972": "scripts/jimeng_probe972_seam_src.py",
    # ⚠️⚠️ 973：**同一步**登记（第七次预防同一个坑）——
    #   ⭐⭐⭐ `GGGGG.1` 要钉「环序 = DOM 序」的那件新仪器 `DOMRANK_JS`
    #   ⇒ 漏登记 = 那组锚文一条都没被查过、而自查仍报「0 问题」
    "_p973": "scripts/jimeng_probe973_ringorder_ck.py",
    # ⚠️⚠️ 974：**同一步**登记（第八次预防同一个坑）——
    #   ⭐⭐ `HHHHH.1` 要钉「两侧真的是**同一件仪器**」（`_grab` + `assert`）
    "_p974": "scripts/jimeng_probe974_source_domrank_src.py",
    # ⚠️⚠️ 975：**同一步**登记（第九次预防同一个坑）——
    #   ⭐⭐ `IIIII.1` 要钉「H₁ 被判否」这个**否定结果**
    #   ⇒ 否定结果**尤其**要钉：它最容易在下一批被悄悄忘掉
    "_p975": "scripts/jimeng_probe975_scope_src.py",
    "_p975": "scripts/jimeng_probe975_scope_src.py",
    # ⚠️⚠️ 976：**同一步**登记（第十次预防同一个坑）——
    #   ⭐⭐ `JJJJJ.1` 要钉的是**否定结果**（H₂ 被证伪）
    #   ⇒ 否定结果**尤其**要钉：它最容易在下一批被悄悄忘掉
    "_p976": "scripts/jimeng_probe976_counterfactual_src.py",
    "_p976": "scripts/jimeng_probe976_counterfactual_src.py",
    # ⚠️⚠️ 977：**同一步**登记（第十次预防同一个坑）——
    #   ⭐⭐ `KKKKK.1` 要钉的是「**臂 B 打中了靶子**」这个**前提**
    #   ⇒ 前提最容易在下一次改实验时被忘掉
    "_p977": "scripts/jimeng_probe977_h3anchor_src.py",
    "_p977": "scripts/jimeng_probe977_h3anchor_src.py",
    # ⚠️⚠️ 978：**同一步**登记（第十一次预防同一个坑）——
    #   ⭐⭐ `LLLLL.1` 要钉的是那个**否定结果**（scroll 假设被否）
    #   ⇒ 否定结果**尤其**要钉：它最容易在下一批被悄悄忘掉
    "_p978": "scripts/jimeng_probe978_lab_body_stop.py",
    "_p978": "scripts/jimeng_probe978_lab_body_stop.py",
    # ⚠️⚠️ 979：**同一步**登记（第十二次预防同一个坑）——
    #   ⭐⭐ `MMMMM.1` 要钉的是那个**否定结果**（978 的 (a) 被否）
    #   ⇒ 否定结果**尤其**要钉：它最容易在下一批被悄悄忘掉
    "_p979": "scripts/jimeng_probe979_dwell_src.py",
    "_p979": "scripts/jimeng_probe979_dwell_src.py",
    # ⚠️⚠️ 980：**同一步**登记（第十三次预防同一个坑）——
    #   ⭐⭐ `NNNNN.1` 要钉的是**关键前提**（门②）
    #   ⇒ 前提最容易在下一次改实验时被忘掉
    "_p980": "scripts/jimeng_probe980_rate_src.py",
    # ⚠️⚠️ 981：**同一步**登记（第十四次预防同一个坑）——
    #   ⭐⭐ `OOOOO.1` 要钉的是**那个诚实的否定结果**（**没量到**）
    #   ⇒ 否定结果**尤其**要钉：它最容易在下一批被悄悄忘掉
    "_p981": "scripts/jimeng_probe981_srcrate_src.py",
    "_p981": "scripts/jimeng_probe981_srcrate_src.py",
    # ⚠️⚠️ 982：**同一步**登记（第十五次预防同一个坑）——
    #   ⭐⭐ `PPPPP.1` 要钉的是**那个新定义**（圈长 = 最小重复周期）
    "_p982": "scripts/jimeng_probe982_ringlen_src.py",
    # ⚠️⚠️⚠️⚠️⚠️ **`_p816` 漏登记 ⇒ 它的锚点被**静默跳过** ⇒ 锚点自查报「0 问题」**
    #   而 verifier 那条判据**真的红了**（`CCCCC.2`）⇒ **同一个坑的第五次**。
    # ⇒ 结论：**锚点自查报 0 ≠ 全部被查过** —— **它只查「已登记」的那些**。
    "_p816": "scripts/verify-jimeng-batch816-anchors.py",
    # ⚠️ 961 顺带补上 `asrc`（= audit 源码，M 组判据在用；
    #   它的路径是 `ROOT / "scripts" / "…"` 两段写法，自动提取抓不到）
    "asrc": "scripts/jimeng_unclickable_audit.py",
    # ⚠️⚠️⚠️ **961 补登记的 59 个**：收集器对**未登记**的变量是 `continue`
    #   （**静默跳过**）⇒ 这些变量上的锚点**从来没被自查过**。
    #   961 补登记后：新增受检 235 条，**实测 0 问题**。
    "_agp_raw": "src/components/jimeng/JimengAudioGenPanel.tsx",
    "_anchs": "scripts/jimeng_check_verifier_anchors.py",
    "_c942s": "scripts/jimeng_check_comment_anchors.py",
    "_jws_raw": "src/components/jimeng/JimengWorkspace.tsx",
    "_p871": "scripts/jimeng_probe871_voicefilter_kb.py",
    "_p872": "scripts/jimeng_probe872_voicefilters_kb.py",
    "_p873": "scripts/jimeng_probe873_voiceselect.py",
    "_p874": "scripts/jimeng_probe874_escvalue.py",
    "_p875": "scripts/jimeng_probe875_clearfilter.py",
    "_p875c": "scripts/jimeng_probe875_clearfilter_ck.py",
    "_p876": "scripts/jimeng_probe876_clearfilter_kb.py",
    "_p876b": "scripts/jimeng_probe876b_clearfilter_mech.py",
    "_p876c": "scripts/jimeng_probe876c_clearfilter_kb2.py",
    "_p876k": "scripts/jimeng_probe876c_clearfilter_kb2_ck.py",
    "_p877": "scripts/jimeng_probe877_clearfilter_kb_all.py",
    "_p878": "scripts/jimeng_probe878_nodefocus_ck.py",
    "_p881": "scripts/jimeng_probe881_domreplace_ck.py",
    "_p882": "scripts/jimeng_probe882_whostealsfocus_ck.py",
    "_p883": "scripts/jimeng_probe883_escselect_src.py",
    "_p884": "scripts/jimeng_probe884_selectnode_src.py",
    "_p885": "scripts/jimeng_probe885_escselect2_src.py",
    "_p886": "scripts/jimeng_probe886_esconchip_src.py",
    "_p887": "scripts/jimeng_probe887_esconchip_val_src.py",
    "_p888": "scripts/jimeng_probe888_reopen_src.py",
    "_p889": "scripts/jimeng_probe889_esclanding_src.py",
    "_p889b": "scripts/jimeng_probe889b_esclanding2_src.py",
    "_p889bck": "scripts/jimeng_probe889b_esclanding_ck.py",
    "_p889c": "scripts/jimeng_probe889c_blankvar_src.py",
    "_p889ck": "scripts/jimeng_probe889_esclanding_ck.py",
    "_p889d": "scripts/jimeng_probe889d_canvasfocus_src.py",
    "_p890": "scripts/jimeng_probe890_nodefocus_why_src.py",
    "_p890b": "scripts/jimeng_probe890b_nodefocus_why2_src.py",
    "_p890c": "scripts/jimeng_probe890c_nodefocus_why_ck.py",
    "_p891": "scripts/jimeng_probe891_mousedown_rule_ck.py",
    "_p893": "scripts/jimeng_probe893_clickmoment_src.py",
    "_p899": "scripts/jimeng_probe899_roving_next_rule_src.py",
    "_syn_src": "scripts/jimeng_probe_js_syntax_check.py",
    "_v942s": "scripts/jimeng_check_strip_comments.py",
    "_vsrc": "scripts/verify-jimeng-batch841-unclickable.py",
    "a2": "src/components/jimeng/JimengAudioGenPanel.tsx",
    "amsrc": "src/components/jimeng/JimengAssetsModal.tsx",
    "asrc2": "src/components/jimeng/JimengAudioGenPanel.tsx",
    "c958": "src/components/jimeng/JimengToolRail.tsx",
    "csrc": "src/components/jimeng/jimengMenuChrome.tsx",
    "csrc2": "src/components/jimeng/jimengMenuChrome.tsx",
    "g2": "src/components/jimeng/JimengGenPanel.tsx",
    "gsrc": "src/components/jimeng/JimengGenPanel.tsx",
    "hsrc": "src/components/jimeng/JimengHistoryMenu.tsx",
    "lsrc": "scripts/jimeng_kb_probe_lib.py",
    "p868s": "scripts/jimeng_probe868_textbar.py",
    "p869s": "scripts/jimeng_probe869_drawerpanels.py",
    "p870s": "scripts/jimeng_probe870_voicefilter.py",
    "pisrc": "src/components/jimeng/JimengProjectInfoModal.tsx",
    "psrc": "scripts/jimeng_probe850_genpanel_kb.py",
    "q852": "scripts/jimeng_probe852_arrowdiag.py",
    "q853b": "scripts/jimeng_probe853b_audiostruct_kb.py",
    "q855a": "scripts/jimeng_probe855_topbar_recon.py",
    "qsrc": "scripts/jimeng_probe864_modaltrap.py",
    "ssrc": "src/components/jimeng/JimengSearchOverlay.tsx",
    # 961 用它把「C 的出处」钉在**两个探针源码**上（892 首测 / 896 复核）
    "_p892": "scripts/jimeng_probe892_preventdefault_src.py",
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


# ⚠️ 961：被**静默跳过**的变量名（未登记 ⇒ 不查），收集时记下来、最后**打印出来** ⇒ 「假绿」不再无声
SKIPPED: list[str] = []


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
                    # ⚠️⚠️⚠️ **961 改**：原来这里是**裸 `continue`（静默跳过）**
                    #   ⇒ 判据里引了一个**没登记**的变量时，锚点**一条都不查**、
                    #   而且**连提示都没有** ⇒ 961 之前 `_p957`–`_p960` 与另外
                    #   59 个变量上的锚点**从来没被自查过**（"0 问题"是假绿）。
                    # ⇒ 现在**照样不查**（它们多半是字典/切片/循环变量，
                    #   不是文件源，硬当门会误报），但**必须被列出来**。
                    SKIPPED.append(name)
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

    if SKIPPED:
        # ⚠️ **不算问题**（多半是字典/切片/循环变量），但**必须可见**（961）
        import collections as _c
        for _n, _k in _c.Counter(SKIPPED).most_common():
            print(f"SKIPPED-未登记 [{_n}] {_k} 条锚点（**不查**）")
    print(f"\n锚点 {len(items)} 条（其中指向 _ausrc 的 {n_ausrc} 条），"
          f"问题 {problems} 个；另 {len(SKIPPED)} 条锚点因**变量未登记**被跳过"
          f"（{len(set(SKIPPED))} 个变量）")
    if problems:
        print("⇒ 有判据已经失效/或被改成永远为真，**别等门禁跑完才发现**。")
        return 1
    print("⇒ 全通 ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
