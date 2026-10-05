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
import re  # ⚠️ 997：`classify_skipped` 要按**赋值语句的形状**分类s
import sys  # ⭐⭐⭐⭐⭐ 1002：让 `argv[1]` 能覆盖判据文件路径
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
    # ⚠️⚠️ 976：**同一步**登记（第十次预防同一个坑）——
    #   ⭐⭐ `JJJJJ.1` 要钉的是**否定结果**（H₂ 被证伪）
    #   ⇒ 否定结果**尤其**要钉：它最容易在下一批被悄悄忘掉
    "_p976": "scripts/jimeng_probe976_counterfactual_src.py",
    # ⚠️⚠️ 977：**同一步**登记（第十次预防同一个坑）——
    #   ⭐⭐ `KKKKK.1` 要钉的是「**臂 B 打中了靶子**」这个**前提**
    #   ⇒ 前提最容易在下一次改实验时被忘掉
    "_p977": "scripts/jimeng_probe977_h3anchor_src.py",
    # ⚠️⚠️ 978：**同一步**登记（第十一次预防同一个坑）——
    #   ⭐⭐ `LLLLL.1` 要钉的是那个**否定结果**（scroll 假设被否）
    #   ⇒ 否定结果**尤其**要钉：它最容易在下一批被悄悄忘掉
    "_p978": "scripts/jimeng_probe978_lab_body_stop.py",
    # ⚠️⚠️ 979：**同一步**登记（第十二次预防同一个坑）——
    #   ⭐⭐ `MMMMM.1` 要钉的是那个**否定结果**（978 的 (a) 被否）
    #   ⇒ 否定结果**尤其**要钉：它最容易在下一批被悄悄忘掉
    "_p979": "scripts/jimeng_probe979_dwell_src.py",
    # ⚠️⚠️ 980：**同一步**登记（第十三次预防同一个坑）——
    #   ⭐⭐ `NNNNN.1` 要钉的是**关键前提**（门②）
    #   ⇒ 前提最容易在下一次改实验时被忘掉
    "_p980": "scripts/jimeng_probe980_rate_src.py",
    # ⚠️⚠️ 981：**同一步**登记（第十四次预防同一个坑）——
    #   ⭐⭐ `OOOOO.1` 要钉的是**那个诚实的否定结果**（**没量到**）
    #   ⇒ 否定结果**尤其**要钉：它最容易在下一批被悄悄忘掉
    "_p981": "scripts/jimeng_probe981_srcrate_src.py",
    # ⚠️⚠️ 982：**同一步**登记（第十五次预防同一个坑）——
    #   ⭐⭐ `PPPPP.1` 要钉的是**那个新定义**（圈长 = 最小重复周期）
    "_p982": "scripts/jimeng_probe982_ringlen_src.py",
    # ⚠️⚠️ 983：**同一步**登记（第十六次预防同一个坑）——
    #   ⭐⭐ `QQQQQ.1` 要钉的是**那三条预测都命中**（2/2 逐格相同）
    "_p983": "scripts/jimeng_probe983_wrapcmp_ck.py",
    # ⚠️⚠️ 984：**同一步**登记（第十七次预防同一个坑）——
    #   ⭐⭐ `RRRRR.3` 要钉的是**「仍未找到出处」这条边界**（否定结果最容易丢）
    "_p984": "scripts/jimeng_probe984_bodytabindex_lab.py",
    # ⚠️⚠️ 985：**同一步**登记（第十八次预防同一个坑）——
    #   ⭐⭐ `SSSSS.1` 要钉的是**那三条否定读数**（`body` 从未被聚焦）⇒ **否定结果最容易丢**
    "_p985": "scripts/jimeng_probe985_bodynotacell_lab.py",
    # ⚠️⚠️ 986：**同一步**登记（第十九次预防同一个坑）——
    #   ⭐⭐⭐⭐⭐ `TTTTT.1` 要钉的是**那三条按定义预写的预测**
    #   （`P1` 缺失率归零 / `P2` 间隙在回绕点 / `P3` 间隙仍是间隙）
    #   ⇒ 预测最容易在下一批被悄悄改成「跑出来是什么就写什么」
    "_p986": "scripts/jimeng_probe986_gaprate_lab.py",
    # ⚠️⚠️ 987：**同一步**登记（第二十次预防同一个坑）——
    #   ⭐⭐⭐⭐⭐ `UUUUU.2` 要钉的是**那条被数据否掉的预测**（P1）
    #   ⇒ ⭐⭐ **否定结果尤其要钉**：它最容易在下一批被悄悄忘掉、
    #   或者被改写成「跑出来是什么就写什么」
    "_p987": "scripts/jimeng_probe987_wrapcause_ck.py",
    # ⚠️⚠️ 988：**同一步**登记（第二十一次预防同一个坑）——
    #   ⭐⭐⭐⭐ `VVVVV.2` 要钉的是**「分子也要减」那条**（第一版只盯着分母）
    "_p988": "scripts/jimeng_probe988_arcdenom_reread.py",
    # ⚠️⚠️ 989：**同一步**登记（第二十二次预防同一个坑）——
    #   ⭐⭐⭐⭐ `WWWWW.2` 要钉的是**「两批不适用」这个结论** ——
    #   ⇒ ⭐⭐ **否定结果尤其要钉**：它最容易在下一批被悄悄忘掉
    "_p989": "scripts/jimeng_probe989_ruler_reread.py",
    # ⚠️⚠️ 990：**同一步**登记（第二十三次预防同一个坑）——
    #   ⭐⭐⭐⭐⭐ `XXXXX.3` 要钉的是**「间隙在生产构建里仍在」**（P1 成立）
    #   ⇒ 而 `XXXXX.4` 要钉的是**被数据否掉的 P2/P3**
    #   ⇒ ⭐⭐ **否定结果与肯定结果同样要钉**
    "_p990": "scripts/jimeng_probe990_prodbuild_ck.py",
    # ⚠️⚠️ 991：**同一步**登记（第二十四次预防同一个坑）——
    #   ⭐⭐⭐⭐⭐ `Y991A.2` 要钉的是**「88 + 14 = 102 = 回卷点下标」这条纯算术**
    #   ⇒ 而 `Y991A.4` 要钉的是**「理由错、结果撞对」**
    #   ⇒ ⭐⭐ **否定结果与肯定结果同样要钉**
    "_p991": "scripts/jimeng_probe991_wrapvsindex_reread.py",
    # ⚠️⚠️ 992：**同一步**登记（第二十五次预防同一个坑）——
    #   ⭐⭐⭐⭐⭐ `Z991A.3` 要钉的是**「990 那条只管跨构建模式、跨系统不成立」**
    #   ⇒ 而 `Z991A.7` 要钉的是**「哪几条预测不是盲的」这条自省**
    "_p992": "scripts/jimeng_probe992_seampos_crosssys_reread.py",
    # ⚠️⚠️ 993：**同一步**登记（第二十六次预防同一个坑）——
    #   ⭐⭐⭐⭐⭐ `X992A.4` 要钉的是**「P4 被否、而门错的是我」**
    #   ⇒ 而 `X992A.5` 要钉的是**「跨系统验过的两条一绿一红」**
    "_p993": "scripts/jimeng_probe993_zeroexception_scope_reread.py",
    # ⚠️⚠️ 994：**同一步**登记（第二十七次预防同一个坑）——
    #   ⭐⭐⭐⭐⭐ `Y992B.2` 要钉的是**「一次扫描会改变它所扫描的对象」**
    #   ⇒ 而 `Y992B.4` 要钉的是**「判据逐字复用、不重写」**
    "_p994": "scripts/jimeng_probe994_scope_presupposition_reread.py",
    # ⚠️⚠️ 995：**同一步**登记（第二十八次预防同一个坑）——
    #   ⭐⭐⭐⭐⭐ `Z992C.1` 要钉的是**「两套措辞交集是 0」**
    #   ⇒ 而 `Z992C.2` 要钉的是**「`恒为 X` 是读数、`零例外` 是断言」**
    "_p995": "scripts/jimeng_probe995_wording_reread.py",
    # ⚠️⚠️ 996：**同一步**登记（第二十九次预防同一个坑）——
    #   ⭐⭐⭐⭐⭐ `A993D.2` 要钉的是**「0 缺失是这道门最危险的状态」**
    #   ⇒ 而 `A993D.3` 要钉的是**「反向用例连否两次」**
    "_p996": "scripts/jimeng_probe996_regguard_reread.py",
    # ⚠️⚠️⚠️ 997 补登记：`_p870s` 是一行**普通** `.read_text()` 读取
    #   （`p870s_ = ROOT / "scripts/jimeng_probe870_voicefilter_src.py"`），
    #   形状与 `_pNNN` 完全一样 ⇒ **却一直没登记** ⇒
    #   **⇒ 961 补了 59 个、962 补了 1 个、两次都只按 `_pNNN` 族去补**
    #   ⇒ **⇒ 而这一条是「按族的形状去补、漏掉的那一族一直没人看」的第三例**
    "_p870s": "scripts/jimeng_probe870_voicefilter_src.py",
    # ⚠️ 997：**读取行与这条登记是同一步加的** ⇒
    #   **996 那条「钉探针 ≠ 钉 audit」在两处各栽过一次、这次必须一步做完**
    "_p997": "scripts/jimeng_probe997_skipcensus_reread.py",
    # ⚠️ 998：**读取行与这条登记同一步加** ⇒ **不许只加一处**
    "_p998": "scripts/jimeng_probe998_derivesrc_reread.py",
    # ⚠️ 999：**读取行与这条登记同一步加** —— 995/996 各栽过一次
    "_p999": "scripts/jimeng_probe999_whowouldfail_reread.py",
    # ⚠️ 1000：**读取行与这条登记同一步加**
    "_p1000": "scripts/jimeng_probe1000_negative_census_reread.py",
    # ⚠️ 1001：**读取行与这条登记同一步加**
    "_p1001": "scripts/jimeng_probe1001_repeat_shape_reread.py",
    "_p1002": "scripts/jimeng_probe1002_mutation_coverage.py",
    "_p1003": "scripts/jimeng_probe1003_anchor_teeth.py",
    "_p1004": "scripts/jimeng_probe1004_anchor_coupling.py",
    "_p1005": "scripts/jimeng_probe1005_zero_coupling_census.py",
    # ⭐⭐⭐⭐⭐ 1006：门加了 `argv[3]` 探针源覆盖之后、`_p1006` 才有意义
    #   ⇒ 而它必须在**加读取行的同一步**被登记 —— 漏登记 = 假绿（900–905 同一个坑）
    "_p1006": "scripts/jimeng_probe1006_duplicate_anchors.py",
    # ⭐⭐⭐⭐⭐ 1007：门第一次能读到**否掉自己上一批结论**的那个探针
    #   ⇒ 而它必须在**加读取行的同一步**被登记 —— 漏登记 = 假绿（900–905 同一个坑）
    "_p1007": "scripts/jimeng_probe1007_disparate_copies.py",
    # ⭐⭐⭐⭐⭐ 1008：**拿 1005 那份清单当实验对象** —— 第一个「过期的仓内产物」被当成被测系统
    #   ⇒ 而它必须在**加读取行的同一步**被登记 —— 漏登记 = 假绿（900–905 同一个坑）
    "_p1008": "scripts/jimeng_probe1008_golden_freshness.py",
    # ⭐⭐⭐⭐⭐ 1009：**第一次把「目标侧的编辑」逐行真跑门、做成一张表**
    #   ⇒ 而它必须在**加读取行的同一步**被登记 —— 漏登记 = 假绿（900–905 同一个坑）
    "_p1009": "scripts/jimeng_probe1009_edit_visibility.py",
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

# ⚠️⚠️⚠️ 997：**别名** —— 995 那条根因（`in` 判断「有没有登记」不可靠）的第四种形态
#   `_aus936 = _ausrc` ⇒ 判据里写 `_aus936 in ...`、而表里登记的是**本名** `_ausrc`
#   ⇒ ⇒ **这与 995 同形、只是方向相反：995 是「本名的守卫把别处写的名字当成已登记」**
#   ⇒ ⇒ **这一条是「引用的是别名、表里只有本名」⇒ 于是落进「未登记」**
#   ⇒ ⇒ **⇒ 处置不必是「再读一遍文件」、可以是「给它一个别名」** —— 而那样**零 IO**
ALIASES: dict[str, str] = {
    "_aus936": "_ausrc",
}


def resolve_alias(name: str) -> str:
    """把别名折到本名；不是别名就原样返回"""
    seen = set()
    while name in ALIASES and name not in seen:
        seen.add(name)
        name = ALIASES[name]
    return name


# ⚠️⚠️⚠️ 997：⭐⭐⭐⭐⭐ **「31 个未登记变量」不是一个同质的集合**
#   995 那条是「共 N 条不给检索词」；这一条更狠 ——
#   **同一张表里塞着四种不同的东西、而门把它们统称成「未登记」**
#   ⇒ ⇒ **⇒ 归类之前不该把那个数当成一个口子的大小**
RX_DERIVED_997 = re.compile(
    r"strip_comments|strip_py_comments|json\.loads|\.group\(|\.split\(|"
    r"\[.*:|\+")
RX_ALIAS_997 = re.compile(r"^\s*\w+\s*$")


def classify_skipped(tree: ast.AST, names: set[str]) -> dict[str, list[str]]:
    """⭐⭐ 把「未登记」的变量按**赋值语句的形状**分成四类

    ⚠️ **这里刻意不判定「哪个名字该登记」** —— **只报形状** ⇒
    **⇒ 「该不该补」是人的决定、而「它是什么」是读数** ⇒
    **这两件事混在一起、就会出现 997 第一版那种
    「分类器自己造了个假阳性、把 P1 从成立翻成被否」的事**
    """
    rhs: dict[str, list[str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        tgts = node.targets if isinstance(node, ast.Assign) \
            else [node.target]
        for t in tgts:
            if not isinstance(t, ast.Name):
                continue
            rhs.setdefault(t.id, []).append(
                (ast.unparse(node.value) if node.value is not None else ""))
    out = {"A-可补登记(有一行普通 read_text)": [],
           "B-派生物(strip/group/切片)": [],
           "C-不是文本(字面量/子进程/解析结果)": [],
           "D-连赋值都没有(循环变量)": []}
    for n in sorted(names):
        kinds = rhs.get(n, [])
        if not kinds:
            out["D-连赋值都没有(循环变量)"].append(n)
            continue
        j = " ".join(kinds)
        if all(".read_text(" in k and not RX_DERIVED_997.search(k)
               for k in kinds):
            out["A-可补登记(有一行普通 read_text)"].append(n)
        elif RX_DERIVED_997.search(j):
            out["B-派生物(strip/group/切片)"].append(n)
        else:
            out["C-不是文本(字面量/子进程/解析结果)"].append(n)
    return out


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
                # ⚠️ 997：**先折别名** ⇒ 别名不再落进「未登记」
                name = resolve_alias(name)
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


def census_ok_shape(tree: ast.AST) -> list[tuple[int, str, str]]:
    """⭐⭐⭐⭐⭐ 1002：`check(name, ok, detail)` 的 **`ok` 位置**必须是表达式。

    ⚠️⭐⭐⭐⭐⭐ **为什么单列一道门**（`collect()` 只走 `Compare` 节点）：
    ⇒ ⇒ **`ok` 写成裸字符串 ⇒ 那一条判据**恒真** ⇒ 而它**一个 `Compare` 都没有**
    ⇒ ⇒ **⇒ 所以 `collect()` 结构上看不见它、`锚点 N 条` 也数不到它**
    ⇒ ⇒ **⇒ 而 1001 批我在做坏锚点探针时、正好连着三次把整条判断写成了字符串**
    ⇒ ⇒ **⇒ 门三次都报「全通」—— 而「门没报」与「门坏了」在输出上完全一样**

    ⚠️⚠️⚠️ **口径警告（我第一版就数错了）**：
    `check` 是**固定三参** `(name, ok, detail="")` ⇒ ⇒
    **`args[1]` 才是条件、`args[2]` 是给人看的 detail** ⇒ ⇒
    ⇒ **而我第一版把 `args[1:]` 整个当条件、于是分母成了 911（真实是 791）** ⇒ ⇒
    ⭐⭐⭐⭐ **⇒ 109 条 `detail` 里混着 106 个 f-string —— 它们非空、恒真、**
    **而它们是**消息**、根本不是条件** ⇒ ⇒ **⇒ 一旦口径错了、就会报出 106 个假的「恒真」**
    ⇒ ⇒ **⇒ 这与 1001「同一个东西要比同一个口径」是同一条**
    """
    out: list[tuple[int, str, str]] = []
    for call in ast.walk(tree):
        if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                and call.func.id == "check"):
            continue
        title = (call.args[0].value
                 if call.args and isinstance(call.args[0], ast.Constant)
                 else "?")
        if len(call.args) < 2:
            out.append((call.lineno, str(title)[:40], "**没有 `ok` 参数**"))
            continue
        ok = call.args[1]
        if isinstance(ok, ast.Constant) and isinstance(ok.value, str):
            out.append((call.lineno, str(title)[:40],
                        "`ok` 是**裸字符串字面量** ⇒ 恒真 ⇒ "
                        f"{ok.value[:40]!r}"))
        elif isinstance(ok, ast.Constant):
            out.append((call.lineno, str(title)[:40],
                        f"`ok` 是裸字面量 {ok.value!r} ⇒ "
                        f"{'恒真' if ok.value else '恒假'}"))
    return out


def main() -> int:
    # ⭐⭐⭐⭐⭐ 1002：**判据文件路径可以覆盖** ⇒ ⇒
    #   **「门只能读固定路径」⇒ 任何检出率实验都必须改真文件 ⇒ ⇒**
    #   **⇒ 而那意味着实验本身有副作用（改到一半被中断就留下一个坏文件）** ⇒ ⇒
    #   **⇒ 处置：接受 `argv[1]` 作为判据文件路径、默认值不变 ⇒ ⇒**
    #   **⇒ 于是 1002 的变异实验全部在 `/tmp` 的副本上做、真文件一个字节都不动**
    # ⭐⭐⭐⭐⭐ 1003：**目标文件（audit）也必须可覆盖** ⇒ ⇒
    #   **⇒ 因为「判据的牙」这件事的实验是「改目标、不改判据」—— 与 1002 正好相反** ⇒ ⇒
    #   **⇒ 而如果目标不可覆盖、那就又变成改真文件了 ⇒ ⇒
    #   **⇒ 两批的实验方向相反、可覆盖的能力却是同一个**
    # ⭐⭐⭐⭐⭐ 1006：**探针源也必须可覆盖**（`argv[3]` = 一个 JSON：`{变量名: 路径}`）⇒ ⇒
    #   **⇒ 因为 467 条锚点指向探针文件、而它们此前**一个都测不到** ⇒ ⇒
    #   **⇒ 1003 当时的选择是「放弃这一类」、并把被排除的条数报了出来** ⇒ ⇒
    #   **⇒ 那个取舍是对的、而本批把它补上 ⇒ ⇒
    #   **⇒ 三批下来 `argv[1]` 判据侧 / `argv[2]` audit 侧 / `argv[3]` 探针侧 —— **
    #   **⇒ 而它们是**同一个通用约束**的三个面：「仪器只能读固定路径 ⇒ 实验必然有副作用」**
    import json as _json
    _pover = {}
    if len(sys.argv) > 3:
        _pover = _json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
    _vpath = Path(sys.argv[1]) if len(sys.argv) > 1 else VERIFIER
    _apath = Path(sys.argv[2]) if len(sys.argv) > 2 else AUDIT
    if not _apath.exists() or not _vpath.exists():
        print("找不到 audit / verifier 源码", file=sys.stderr)
        return 1
    ausrc = _apath.read_text(encoding="utf-8")
    probes = {k: (Path(_pover[k]) if k in _pover
                  else ROOT / v).read_text(encoding="utf-8")
              if (Path(_pover[k]) if k in _pover else ROOT / v).exists() else ""
              for k, v in PROBE_VARS.items()}

    _vtree = ast.parse(_vpath.read_text(encoding="utf-8"))
    items = collect(_vtree)
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

    # ── ⭐⭐⭐⭐⭐ 1002：`ok` 位置的条件形状普查（`collect()` 看不见它）────
    bad_ok = census_ok_shape(_vtree)
    for _ln, _t, _why in bad_ok:
        print(f"SHAPE-OK    [line {_ln}] {_t} —— {_why}")
    problems += len(bad_ok)
    n_checks = sum(1 for c in ast.walk(_vtree)
                   if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)
                   and c.func.id == "check")
    print(f"SHAPE-口径：check({n_checks}) 条、其中 `ok` 是**裸字面量**的 "
          f"{len(bad_ok)} 条（**`detail` 位置不算** —— 它是人看的消息）")

    if SKIPPED:
        # ⚠️ **不算问题**（多半是字典/切片/循环变量），但**必须可见**（961）
        import collections as _c
        for _n, _k in _c.Counter(SKIPPED).most_common():
            print(f"SKIPPED-未登记 [{_n}] {_k} 条锚点（**不查**）")
        # ⚠️⚠️⚠️ 997：**「未登记」不是一个同质的集合** ⇒ 门自己分类
        _cls = classify_skipped(ast.parse(
            _vpath.read_text(encoding="utf-8")), set(SKIPPED))
        for _tag, _names in _cls.items():
            if _names:
                print(f"SKIPPED-分类 [{_tag}] {len(_names)} 个："
                      f"{' '.join(sorted(_names))}")
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
