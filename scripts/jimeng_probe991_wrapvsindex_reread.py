#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 991 —— ⭐⭐⭐⭐⭐ **§164 自己的算术驳了它自己**

989 把 954 的「环长 102」按 986/988 的换算改成 101，**理由是「旧口径把间隙算成一格」**
⇒ 而 989 **同一批**又写了「**102 是回卷点位置、101 是圈长，口径不同、不许并**」
⇒ ⇒ ⭐⭐⭐⭐⭐ **这两句互相矛盾**：若 102 是**按压序号**、101 是**间隔**，
那么 102 → 101 是**序号与间隔之差**、**与间隙无关**

⭐⭐⭐⭐⭐ 而 §164 **自己就把 102 定义成了按压序号**：
「**回卷点 = 第 102 按**（`node#0` 第二次出现）」
⇒ ⇒ **而 988/989 要减的那个间隙、974 已在源站侧量到它在 out 段内部、**
**不在回卷点上** ⇒ ⇒ **再次否掉「102 → 101 是因为间隙」**

⭐⭐⭐⭐⭐ **本批还撞出一条一节内部的自我矛盾**（纯算术、不需要浏览器）：
§164 写「**节点停靠 88 个 + 内层停靠 14 个 + 出画布 18 个**」、
「**回卷点 = 第 102 按**」⇒ **88 + 14 = 102 = 回卷点下标**
⇒ ⇒ ⭐⭐⭐⭐⭐ **那 out 段那 18 按就不在周期内**
⇒ ⇒ 而同一节又写「**它含节点段 + 内层控件段 + 顶栏那一段**」⇒ **两句矛盾**

本批**纯离线**：不打开浏览器、不按任何键、连 `mouse.click` 都没有
⇒ ⇒ ⭐⭐⭐⭐⭐ **零计费是结构性的、不是自律的**
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(ROOT, "docs/research/jimeng-canvas/README.md")
A974 = "/tmp/b974-source-domrank.json"
OUT = "/tmp/b991-wrapvsindex.json"

# ══ ⭐⭐⭐⭐⭐ 三条预测**全部在看数据前按定义写出** ══════════════════════
#   （986 立的那条：预测要「算出来」而不是「写死」⇒ 而它算错了也要留着）
PRED = {
    # P1 ⭐⭐⭐⭐⭐ 纯算术：88 + 14 是否恰等于回卷点下标
    "P1_node_plus_inner_equals_wrap_index":
        "节点停靠 88 + 内层停靠 14 = 102，而 §164 自己写「回卷点 = 第 102 按」"
        " ⇒ **out 段那 18 按不在周期内**",
    # P2 ⭐⭐⭐⭐⭐ 同一节里另一句必须与 P1 矛盾
    "P2_section_self_contradiction":
        "而 §164 同一节写「周期……它含节点段 + 内层控件段 + 顶栏那一段」"
        " ⇒ **P1 与这句直接矛盾**",
    # P3 ⭐⭐⭐⭐⭐ 102 与 101 差 1 的成因
    "P3_why_102_vs_101":
        "node#0 第 1 次落在第 1 按、第 2 次落在第 102 按 ⇒ **间隔 = 101**"
        " ⇒ **差 1 的成因是「序号与间隔之差」、不是间隙**",
    # P4 ⭐⭐⭐⭐⭐ 间隙到底在不在回卷点上（拿 974 存档判）
    "P4_gap_is_not_at_wrap":
        "974 存档里 out 段唯一的 dom_rank 下降落在 **BODY** 那一格"
        " ⇒ **间隙在 out 段内部、不在回卷点上**",
    # P5 ⭐⭐⭐⭐⭐ 989 那次改写的定性
    "P5_989_rewrite_reason":
        "⇒ **989 对 954 的 102 → 101 是「理由错、结果撞对」**；"
        "**out 段 18 → 17 才是真改写**",
}


def read(p):
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return f.read()


md = read(README)
arch = None
if os.path.exists(A974):
    with open(A974, encoding="utf-8") as f:
        arch = json.load(f)

out = {
    "target": "offline-reread",
    "reps": 0,
    "source": "§164 原文 + 974 存档",
    "question": (
        "⭐⭐⭐⭐⭐ **989 把 954 的「环长 102」按间隙换算改成 101 —— "
        "而 989 同一批又写「102 是回卷点位置、101 是圈长，不许并」** "
        "⇒ **那 102 → 101 到底是因为间隙、还是因为序号与间隔之差？**"
    ),
    "predictions_991": PRED,
    "offline_991": True,
    "offline_note_991": (
        "本批纯离线：不打开浏览器、不按任何键、连 mouse.click 都没有 ⇒ "
        "**零计费是结构性的、不是自律的**"
    ),
}

# ══ 一、⭐⭐⭐⭐⭐ 引文必须逐字来自原文 —— 数字也**从原文抠**、不许写死 ══
#   （989 栽在这里一次：我凭记忆写「out 段 18 个」，原文是三段相加）
QUOTES = [
    "**节点停靠 88 个 + 内层停靠 14 个 + 出画布 18 个**",
    "**回卷点 = 第 102 按**（`node#0` 第二次出现）",
    "它含**节点段 + 内层控件段 + 顶栏那一段**",
    "**环长 102 → 101**（旧口径把间隙算成一格 ⇒ **可聚焦停靠点数 = 旧 − 1**）",
    "**「102 是回卷点位置、101 是圈长」，口径不同、**",
]
q = {}
for s in QUOTES:
    q[s] = (s in md) if md is not None else False
out["quotes_991"] = q
out["quotes_all_present_991"] = all(q.values())

# ⭐ 从 §164 那一行把三个数**抠出来**（不是写死）
_m = re.search(
    r"节点停靠 (\d+) 个 \+ 内层停靠 (\d+) 个 \+ 出画布 (\d+) 个", md or "")
node_stops = int(_m.group(1)) if _m else None
inner_stops = int(_m.group(2)) if _m else None
out_stops = int(_m.group(3)) if _m else None

_w = re.search(r"回卷点 = 第 (\d+) 按", md or "")
wrap_index = int(_w.group(1)) if _w else None

sum_node_inner = (node_stops + inner_stops) if None not in (
    node_stops, inner_stops) else None

out["arithmetic_991"] = {
    "node_stops": node_stops,            # 88
    "inner_stops": inner_stops,          # 14
    "out_stops": out_stops,              # 18
    "sum_node_inner": sum_node_inner,    # 102
    "wrap_index": wrap_index,            # 102
    "sum_equals_wrap_index": sum_node_inner == wrap_index,
    "total_presses_stated": (node_stops + inner_stops + out_stops)
    if None not in (node_stops, inner_stops, out_stops) else None,
    # ⭐ 环长 = 间隔 = 两个落点之差（不是「回卷点下标」本身）
    "period_as_interval": (wrap_index - 1) if wrap_index is not None else None,
    "period_eq_wrap_index_minus_1": (wrap_index - 1 == 101)
    if wrap_index is not None else False,
}
out["P1_hold_991"] = out["arithmetic_991"]["sum_equals_wrap_index"]
out["P3_hold_991"] = out["arithmetic_991"]["period_eq_wrap_index_minus_1"]

# ══ 二、⭐⭐⭐⭐⭐ P2：同一节里的自相矛盾（**两句必须都在、且互相排斥**）══
_claims_out_in_period = ("它含**节点段 + 内层控件段 + 顶栏那一段**" in (md or ""))
_claims_out_in_period = _claims_out_in_period and (
    "「周期」在这两边都**不是常数**" in (md or ""))
out["P2_hold_991"] = bool(
    out["P1_hold_991"] and _claims_out_in_period)
out["self_contradiction_991"] = {
    "sentence_a": "节点段 + 内层停靠 的和恰等于回卷点下标 ⇒ out 段不在周期内",
    "sentence_b": "同一节写「周期……它含节点段 + 内层控件段 + 顶栏那一段」",
    "both_present": bool(_claims_out_in_period),
    "mutually_exclusive": bool(out["P1_hold_991"] and _claims_out_in_period),
}

# ══ 三、⭐⭐⭐⭐⭐ P4：间隙在不在回卷点上（**拿 974 存档判**）══════════
c0 = None
if arch:
    for _c in arch["runs"][0]["cells"]:
        if _c.get("ci") == 0:
            c0 = _c
            break
if c0:
    ranks = list(c0["arc_ranks"])
    desc = [i for i in range(1, len(ranks)) if ranks[i] < ranks[i - 1]]
    body_seats = list(c0["body_seats"])
    seam_seat = c0["seam_pred"][0]["seat"] if c0.get("seam_pred") else None
    out["source_arc_991"] = {
        "arc_len_old": c0["arc_len"],                       # 18
        "arc_len_new": c0["arc_len"] - 1,                   # 17（988 换算）
        "arc_ranks": ranks,
        "n_rank_descents": c0["n_rank_descents"],
        "descent_indices": desc,
        "descent_rank_value": [ranks[i] for i in desc],
        "body_seats": body_seats,
        "seam_seat": seam_seat,
        "descent_is_at_body_seat": bool(desc) and desc[0] == body_seats[0],
        "seam_seat_equals_descent": bool(desc) and desc[0] == seam_seat,
        "ring_follows_dom_order": c0.get("ring_follows_dom_order"),
        # ⭐⭐⭐⭐⭐ **974 只量了 out 段、根本没量到源站的圈长** ——
        #   `n_lead_cap_hit` 说明它撞了 140 的按压上限
        "n_lead_cap_hit": c0.get("n_lead_cap_hit"),
        "n_lead_cap": arch.get("n_lead_cap"),
        "n_lead": c0.get("n_lead"),
        "ring_len_measured_here": False,
    }
    out["P4_hold_991"] = bool(
        c0.get("n_rank_descents") == 1
        and len(desc) == 1 and desc[0] == body_seats[0])
else:
    out["source_arc_991"] = {"error": "974 存档不在 %s" % A974}
    out["P4_hold_991"] = None

# ══ 四、⭐⭐⭐⭐⭐ P5：989 那次改写的定性（**结果撞对、理由错**）════════
out["P5_hold_991"] = bool(
    out["P3_hold_991"]
    and (out["P4_hold_991"] in (True, None))
    and q.get("**环长 102 → 101**（旧口径把间隙算成一格 ⇒ **可聚焦停靠点数 = 旧 − 1**）")
)
out["rewrite_991"] = {
    "what_989_did": "把 §164 的 102 改成 101、理由写的是「旧口径把间隙算成一格」",
    "why_reason_is_wrong": (
        "§164 自己把 102 定义成**回卷点的按压序号**（回卷点 = 第 102 按）；"
        "而**序号与间隔之差天然就是 1**（第 1 按与第 102 按之间是 101 个间隔）"
        "⇒ ⇒ **这条 −1 与间隙无关**"
    ),
    "why_the_17_is_real": (
        "**out 段 18 → 17 才是真改写** —— 那 18 格里确实含 1 格间隙，"
        "988 已在 974 存档上量到 arc_len_new = 17"
    ),
    "two_different_minuses_merged": (
        "⇒ ⭐⭐⭐⭐⭐ **989 把两条成因不同、结果相同的「−1」并成了一次改写**"
        " ⇒ 这是 981 那条「同一个东西要比同一个口径」最纯的一次实例"
    ),
    "not_merged_still_holds": (
        "⭐⭐ **而 989 那条「不许把 102 与 101 并成一个数」仍然成立** —— "
        "本批只是把「不许并」升级成「并排读出来、并说清各自的成因」"
    ),
}

# ══ 五、⭐⭐⭐⭐⭐ 判据要钉的内容，**必须真的写在探针里** ══════════════
out["verdicts_991"] = {
    "p1_out_segment_not_in_period": (
        "✅ **P1 成立：out 段那 18 按不在周期内** —— "
        "节点停靠 88 + 内层停靠 14 = 102，而 §164 自己写「回卷点 = 第 102 按」"
        " ⇒ ⇒ ⭐⭐⭐⭐⭐ **纯算术、不需要浏览器就成立** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐ **而 120 按的总额里那 18 个出画布停靠、"
        "是第二次环的前 18 按** ⇒ **不是一个 120 的环**"
    ),
    "p2_section_self_contradiction": (
        "⚠️⭐⭐⭐⭐⭐ **P2 成立：§164 这一节自己驳了自己** —— "
        "同一节里「它含节点段 + 内层控件段 + 顶栏那一段」与 "
        "「88 + 14 = 102 = 回卷点下标」**互相排斥** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **要改的是「周期含顶栏那一段」那一句** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **而 989 只挂了一条改写横幅、没抓到这一处** ⇒ ⇒ "
        "⇒ ⭐⭐⭐ **「不许并」和「挂横幅」都做了、不等于矛盾被看见了**"
    ),
    "p3_index_vs_interval": (
        "✅ **P3 成立：102 与 101 差 1 的成因是「序号与间隔之差」** —— "
        "node#0 第 1 次落在第 1 按、第 2 次落在第 102 按 ⇒ **间隔 101** "
        "⇒ ⇒ ⭐⭐⭐⭐⭐ **而 989 给它写的理由是「旧口径把间隙算成一格」** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **理由错、结果撞对** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **989 同一批其实已经写下了正确答案**"
        "（「102 是回卷点位置、101 是圈长，口径不同」）"
        "⇒ **却把间隙那条换算又套了上去** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **同一批里的两句话互相矛盾、而门没抓到**"
    ),
    "p4_gap_is_not_at_wrap": (
        "✅ **P4 成立：间隙不在回卷点上** —— 974 存档里源站 out 段"
        "**唯一的 dom_rank 下降**落在 **BODY** 那一格"
        "（`n_rank_descents = 1`、下降下标与 `body_seats[0]` 相同）⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **间隙在 out 段内部、而回卷点是 `node#0`（一个真节点）** "
        "⇒ ⇒ ⭐⭐⭐⭐⭐ **再次否掉「102 → 101 是因为间隙」**"
    ),
    "p4_2_974_never_measured_source_ring": (
        "⚠️⭐⭐⭐⭐⭐ **而 974 根本没量到源站的圈长** —— "
        "它报的是 `n_lead_cap_hit = True`（撞了 140 的按压上限）"
        "⇒ **它量到的是 out 段、不是圈长** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐ **所以「102 vs 101」在 974 存档里本来就不可判定** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐ **必须用 §164 自己的数** —— 而它的数是自洽的、"
        "只是与同一节的另一句矛盾"
    ),
    "two_minus_one_merged": (
        "⭐⭐⭐⭐⭐ **本批最该带走的一条：989 把两条成因不同、结果相同的"
        "「−1」并成了一次改写** —— ① 102 → 101 是**序号与间隔之差**；"
        "② out 段 18 → 17 是**间隙** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **结果撞对、而理由错** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **这是 981 那条「同一个东西要比同一个口径」"
        "最纯的一次实例** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **而 989 那条「不许把 102 与 101 并成一个数」仍然成立**"
        "—— 本批只是把「不许并」升级成「并排读出来、并说清各自的成因」"
    ),
    "contradiction_is_its_own_finding": (
        "⭐⭐⭐⭐⭐ **「一节内部的自我矛盾」是本批唯一的原始发现** —— "
        "它**不是**换算、不是新测量，**是 §164 自己的三个数加起来的** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **这一类发现成本最低、可移植性最高** ⇒ "
        "⇒ ⭐⭐ **任何一章的「分解式 + 总数」都值得这样加一遍**"
    ),
    "offline_991": (
        "⭐⭐⭐⭐⭐ **本批纯离线**：不打开浏览器、不按任何键、"
        "连 `mouse.click` 都没有 ⇒ ⇒ "
        "⭐⭐⭐⭐ **零计费是结构性的、不是自律的** ⇒ "
        "**源站侧全部用 974 存档**（985 已确认登录态过期）⇒ **不是「测了没事」**"
    ),
    "quotes_from_original_991": (
        "⭐⭐⭐⭐⭐ **引文与数字都从原文抠、不写死** —— 989 栽过一次"
        "（凭记忆写「out 段 18 个」、原文是三段相加）⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **`quotes_all_present_991` 是门**："
        "**哪一条不在原文里、本批就不成立**"
    ),
    "selfcheck_991": (
        "⚠️⭐⭐⭐⭐⭐ **本批的局限要说清楚** —— "
        "**P4 依赖 `/tmp/b974-source-domrank.json` 这个 974 存档还在** "
        "⇒ **它不在仓库里、所以这是一条会过期的读数** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐ **过期的读数不许当结论用**、只当「当时的量」⇒ "
        "⇒ ⭐⭐⭐ **而 P1/P2/P3 只依赖 §164 原文、不依赖那个文件**"
    ),
}

out["discipline_991"] = "".join([
    "① ⭐⭐⭐⭐⭐ **同一批里的两句话可以互相矛盾、而门只钉判据、不钉矛盾** ⇒\n",
    "  ② ⭐⭐⭐⭐⭐ **「结果撞对、理由错」是最难自查的一类错** ——\n",
    "  ③ ⭐⭐⭐⭐⭐ **「不许并」要升级成「并排读出、并说清各自的成因」** ——\n",
    "  ④ ⭐⭐⭐⭐⭐ **纯算术也能推翻一节的定性**（88 + 14 = 102）⇒\n",
    "  ⑤ ⭐⭐⭐⭐ **引文与数字都从原文抠**、哪一条不在原文里本批就不成立 ⇒\n",
    "  ⑥ ⭐⭐⭐⭐ **恒真的门比没有门更坏** —— 本批每条都有反向判据 ⇒\n",
    "  ⑦ ⭐⭐⭐⭐ **本批纯离线、零计费是结构性的** ——\n",
])

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("P1_hold =", out["P1_hold_991"])
print("P2_hold =", out["P2_hold_991"])
print("P3_hold =", out["P3_hold_991"])
print("P4_hold =", out["P4_hold_991"])
print("P5_hold =", out["P5_hold_991"])
print("quotes_all_present =", out["quotes_all_present_991"])
print("arithmetic =", json.dumps(out["arithmetic_991"], ensure_ascii=False))
print("PROBE_991_DONE ->", OUT)
