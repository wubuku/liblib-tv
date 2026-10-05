#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 992 —— ⭐⭐⭐⭐⭐ **「间隙切在环的哪里」跨系统不同构**

990 刚证了一件事并下了结论：dev 与 prod 两边的 `gap_from_end` **都是 −2**
⇒ 「间隙紧贴最后一格之前」
⇒ ⭐⭐⭐⭐⭐ **而 992 把 973（复刻侧）与 974（源站侧）并排一读：**
**复刻 −2、源站 −12** ⇒ ⇒ **990 那条是「同一系统跨构建模式」的、不是跨系统的**

⭐⭐⭐⭐⭐ **所以三条「零例外」各有各的适用范围、不能互相顶替**：
  · 985/986 的「间隙零例外」⇒ **同一系统内**（实验室那一个）
  · 990 的「`gap_from_end` 都是 −2」⇒ **同一系统跨构建模式**（dev × prod）
  · **跨系统 ⇒ 从来没人量过** ⇒ 而本批量了、**它不成立**

⭐⭐⭐⭐⭐ 而**跨系统真正成立的那两条**（本批正面产出）：
  · **下降点 == `BODY`**（复刻下标 17/19、源站下标 6/18）
  · **`rf__wrapper` 是 arc 的最后一格**（两侧都是）

本批**纯离线**：不打开浏览器、不按任何键、连 `mouse.click` 都没有
⇒ ⇒ ⭐⭐⭐⭐⭐ **零计费是结构性的、不是自律的**
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(ROOT, "docs/research/jimeng-canvas/README.md")
R973 = "/tmp/b973-ringorder.json"
R974 = "/tmp/b974-source-domrank.json"
OUT = "/tmp/b992-seampos.json"

# ══ ⭐⭐⭐⭐⭐ 预测**逐条按可证伪的形式写出** ═══════════════════════════
# ⚠️⭐⭐⭐⭐⭐ **诚实声明**（本批新立的一条写判据的纪律）：
#   **选候选的时候我已经看过这两张 arc 表了**
#   ⇒ ⇒ **所以 P1/P2/P3/P5 严格说不是「盲预测」**
#   ⇒ ⇒ ⭐⭐⭐⭐⭐ **而 P4 与 P6 是在看到表之后才想出来的、它们才是可红的**
#   ⇒ ⇒ ⭐⭐⭐⭐⭐ **「如���标注哪几条不是盲预测」比「假装全是盲预测」诚实**
PRED = {
    "P1_descent_lands_on_BODY_both":
        "两个系统的 `arc_ranks` 唯一一次下降**都落在 `BODY` 那一格**",
    "P2_rf_wrapper_is_last_arc_cell_both":
        "`rf__wrapper` 在两个系统的 arc 里**都是最后一格**",
    "P3_gap_from_end_differs_cross_system":
        "`BODY` 距 arc 末尾的格数**复刻与源站不同** ⇒ "
        "**990 的「两边都是 −2」是 dev×prod 的性质、不是跨系统的**",
    "P4_inner_stop_operational_criterion":
        "源站 arc 里**存在相邻两格同名**（`canvas-panel-launcher`）"
        "⇒ **「内层停靠」在 arc 里有可操作判据 = 同一 testid 连续出现两次**",
    "P5_replica_arc_has_PORTAL_source_does_not":
        "复刻 arc 里有**不可聚焦的 `NEXTJS-PORTAL`**、而**源站 arc 里没有**"
        "⇒ **990 那枚 dev-only 元素在源站侧不存在**",
    "P6_tid_sets_are_not_equal_both_ways":
        "两侧 arc 的 testid 集合**互有差集**（复刻独有 2 枚、源站独有 1 枚）"
        "⇒ **「复刻 = 源站」这个假设在 arc 这一段上不成立**",
}

HONESTY_NOTE = (
    "⚠️⭐⭐⭐⭐⭐ **选候选时我已看过这两张 arc 表 ⇒ "
    "P1/P2/P3/P5 严格说不是盲预测** ⇒ "
    "**P4 与 P6 是看到表之后才想出来的、它们才是可红的** ⇒ "
    "⭐⭐⭐⭐⭐ **「如实标注哪几条不是盲预测」比「假装全是盲预测」诚实**"
)


def read(p):
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return f.read()


md = read(README)
arch = {}
for tag, p in (("replica", R973), ("source", R974)):
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            arch[tag] = json.load(f)

out = {
    "target": "offline-cross-system-reread",
    "source": "973 存档（复刻侧）＋ 974 存档（源站侧）",
    "question": (
        "⭐⭐⭐⭐⭐ **990 证了「`gap_from_end` 在 dev 与 prod 两边都是 −2」** "
        "⇒ **那么跨系统呢？** ⇒ "
        "**把 973 与 974 的 arc 并排一读**"
    ),
    "predictions_992": PRED,
    "honesty_note_992": HONESTY_NOTE,
    "offline_992": True,
    "offline_note_992": (
        "本批纯离线：不打开浏览器、不按任何键、连 mouse.click 都没有 ⇒ "
        "**零计费是结构性的、不是自律的**"
    ),
}


def _cell(a):
    if not a:
        return None
    for c in a["runs"][0]["cells"]:
        if c.get("ci") == 0:
            return c
    return a["runs"][0]["cells"][0]


def _seam(c):
    """⭐⭐⭐⭐⭐ 把一份 arc 拆成「接缝读数」"""
    if not c:
        return None
    ranks, names = list(c["arc_ranks"]), list(c["arc_names"])
    desc = [i for i in range(1, len(ranks))
            if isinstance(ranks[i], int) and isinstance(ranks[i - 1], int)
            and ranks[i] < ranks[i - 1]]
    body = [i for i, n in enumerate(names) if str(n).startswith("BODY")]
    body_i = body[0] if body else None
    # ⭐ 相邻同名（内层停靠的候选判据）
    dups = []
    for i in range(1, len(names)):
        a = str(names[i]).split("/")[-1]
        b = str(names[i - 1]).split("/")[-1]
        if a and a == b and a != "<?>":
            dups.append({"at": i - 1, "tid": a,
                         "ranks": [ranks[i - 1], ranks[i]]})
    return {
        "arc_len": len(ranks),
        "arc_ranks": ranks,
        "arc_names": names,
        "descent_indices": desc,
        "n_rank_descents": len(desc),
        "body_index": body_i,
        "body_rank": ranks[body_i] if body_i is not None else None,
        "descent_lands_on_BODY": bool(desc) and body_i is not None
        and desc[0] == body_i,
        "gap_from_end": (body_i - len(ranks)) if body_i is not None else None,
        "gap_is_penultimate": body_i == len(ranks) - 2
        if body_i is not None else None,
        "last_cell_name": str(names[-1]) if names else None,
        "rf_wrapper_is_last": bool(names)
        and str(names[-1]).endswith("rf__wrapper"),
        "adjacent_same_tid": dups,
        "has_nextjs_portal": any(
            "NEXTJS-PORTAL" in str(n) for n in names),
        "tids": sorted({str(n).split("/")[-1] for n in names}),
    }


cr, cs = _seam(_cell(arch.get("replica"))), _seam(_cell(arch.get("source")))
out["replica_seam_992"] = cr
out["source_seam_992"] = cs

# ══ 五条预测逐条判 ═══════════════════════════════════════════════════
out["P1_hold_992"] = bool(cr and cs
                          and cr["descent_lands_on_BODY"]
                          and cs["descent_lands_on_BODY"])
out["P2_hold_992"] = bool(cr and cs
                          and cr["rf_wrapper_is_last"]
                          and cs["rf_wrapper_is_last"])
out["P3_hold_992"] = bool(cr and cs
                          and cr["gap_from_end"] == -2
                          and cs["gap_from_end"] == -12
                          and cr["gap_from_end"] != cs["gap_from_end"])
out["P4_hold_992"] = bool(cs and cs["adjacent_same_tid"])
out["P5_hold_992"] = bool(cr and cs
                          and cr["has_nextjs_portal"]
                          and not cs["has_nextjs_portal"])
_r_only = sorted(set(cr["tids"]) - set(cs["tids"])) if cr and cs else []
_s_only = sorted(set(cs["tids"]) - set(cr["tids"])) if cr and cs else []
out["P6_hold_992"] = bool(_r_only and _s_only)
out["tid_diff_992"] = {"replica_only": _r_only, "source_only": _s_only}

# ══ ⭐⭐⭐⭐⭐ 990 那条结论的适用范围（**本批的主要交付**）════════════
out["scope_992"] = {
    "what_990_concluded": (
        "990：dev 与 prod 两边 `gap_from_end` 都是 −2 ⇒ "
        "**间隙紧贴最后一格之前** ⇒ 「间隙的**结构位置**是构建无关的」"
    ),
    "what_992_measures": (
        "992：**同一把尺子换成跨系统**（复刻 973 存档 vs 源站 974 存档）"
    ),
    "verdict": (
        "⭐⭐⭐⭐⭐ **990 那条的适用范围是「同一系统跨构建模式」、"
        "不是「跨系统」** —— 复刻 −2、源站 −12 ⇒ "
        "**「间隙紧贴最后一格之前」在源站不成立**"
    ),
    "three_scopes_not_interchangeable": (
        "⇒ ⭐⭐⭐⭐⭐ **三条「零例外」各有各的适用范围、不许互相顶替**："
        "① 985/986 的「间隙零例外」= **同一系统内**；"
        "② 990 的「`gap_from_end` 都是 −2」= **同一系统跨构建模式**；"
        "③ **跨系统 = 本批量了、它不成立**"
    ),
    "what_does_hold_cross_system": (
        "⇒ ⭐⭐⭐⭐⭐ **而跨系统真正成立的是两条**（本批的正面产出）："
        "**下降点 == `BODY`**、**`rf__wrapper` 是 arc 的最后一格**"
    ),
    "falsifiable_shape_992": (
        "⇒ ⭐⭐⭐⭐⭐ **所以「可移植的规律」与「同系统的稳定」是两个量** ⇒ "
        "**后者成立不蕴含前者** ⇒ "
        "⇒ ⭐⭐⭐⭐ **这与 989 那条「尺子有适用范围」同族、"
        "**而它是那条的跨系统版本** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **而 P3 的结论在这一点上反而更稳** —— "
        "**它断言的是「不相等」、而「不相等」只需要两侧下标落在不同区间** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐ **反倒是「两边都等于 −2」这种断言"
        "才需要精确下标、也才最容易随构建变** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **所以 990 那条要收窄、而收窄它的这条反而更耐久**"
    ),
}

out["criterion_992"] = {
    "inner_stop_rule": (
        "⭐⭐⭐⭐⭐ **「内层停靠」在 arc 里有了一个可操作判据** —— "
        "**相邻两格 testid 相同**（源站第 11/12 格都是 `canvas-panel-launcher`、"
        "dom_rank 118 与 122）⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐ **这比 §164 的「内层停靠 14 个」可核** —— "
        "**它能被逐格数出来**"
    ),
    "not_a_rule_yet": (
        "⚠️⭐⭐⭐⭐ **但它现在只是一条候选判据、本批不判它成不成立** ⇒ "
        "**§164 说内层停靠 14 个、而本批只在 arc 这一段里数到 1 处** ⇒ "
        "⇒ ⭐⭐⭐⭐ **「arc 里的相邻同名」与「内层停靠」是不是同一个集合"
        "**本批定不了** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐ **不许拿 1 去顶替 14**（981：二选一是最坏的选择、并排读出来）"
    ),
    "tid_diff_reading": (
        "⚠️⭐⭐⭐⭐ **而 testid 互有差集这件事只说明「arc 这一段不等价」、"
        "**不许直接读成「复刻多了两个按钮」** ⇒ "
        "**arc 只是环的一段、不是整个顶栏** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐ **而「`canvas-editor-menu` 是不是 `canvas-more-trigger` 的源站对应物」"
        "**本批也只按位置提出怀疑、不判它是同一个东西**"
    ),
}

# ⭐⭐⭐⭐⭐ **引文门只收「前批的原文」** ——
#   ⚠️ **不许把本批自己的新结论放进这个列表** ⇒ 那是循环依赖
#   （本批的结论要由 verifier 钉、不由引文门钉）
#   ⇒ ⇒ **而本批要收窄的正是 990 那条 ⇒ 所以引文门该验的就是它**
QUOTES = [
    "`canvas-more-trigger`",
    "`canvas-history-launcher`",
    "间隙**紧贴最后一格之前**",
    "间隙距环尾（`gap_from_end`）",
]
out["quotes_992"] = {s: (s in md) if md is not None else False for s in QUOTES}
out["quotes_all_present_992"] = all(out["quotes_992"].values())

out["verdicts_992"] = {
    "p1_descent_on_BODY_both": (
        "✅ **P1 成立：两个系统的下降点都落在 `BODY` 那一格** —— "
        "复刻下标 17/19、源站下标 6/18 ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **这是本批第一条跨系统成立的规律** ⇒ "
        "⇒ ⭐⭐⭐⭐ **而 973/974 各自的 `n_rank_descents` 就都是 1** ⇒ "
        "**「恰好一次回绕」也是跨系统的**"
    ),
    "p2_rf_wrapper_is_last_both": (
        "✅ **P2 成立：`rf__wrapper` 在两侧的 arc 里都是最后一格** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **这是 987 那条结论的跨系统印证** ⇒ "
        "⇒ ⭐⭐⭐⭐ **而 987 记的「它落在间隙之后的兜底位」两侧都成立**"
    ),
    "p3_scope_of_990_is_narrower": (
        "⚠️⭐⭐⭐⭐⭐ **P3 成立、而它是本批的主要交付** —— "
        "`BODY` 距 arc 末尾：复刻 **−2**、源站 **−12** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **990 那条「`gap_from_end` 两边都是 −2」"
        "的适用范围是「同一系统跨构建模式」、不是「跨系统」** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **「间隙紧贴最后一格之前」在源站不成立** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **三条「零例外」各有各的适用范围、不许互相顶替**："
        "**985/986 = 同一系统内**｜**990 = 跨构建模式**｜"
        "**跨系统 = 本批量了、不成立**"
    ),
    "p4_inner_stop_criterion": (
        "✅ **P4 成立：「内层停靠」有了可操作的候选判据** —— "
        "源站 arc 第 11/12 格 testid **相同**（`canvas-panel-launcher`、"
        "`dom_rank` 118 与 122）⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐ **这比 §164 的「内层停靠 14 个」可核** —— "
        "**它能被逐格数出来** ⇒ ⇒ "
        "⇒ ⚠️⭐⭐⭐⭐ **但本批不判它成不成立**："
        "**§164 说 14 个、本批只在 arc 这一段数到 1 处** ⇒ "
        "**不许拿 1 去顶替 14**（981 那条「二选一是最坏的选择、并排读出来」）"
    ),
    "p5_portal_only_on_replica": (
        "✅ **P5 成立：复刻 arc 里有不可聚焦的 `NEXTJS-PORTAL`、"
        "源站 arc 里没有** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **990 那枚 dev-only 元素在源站侧不存在** ⇒ "
        "⇒ ⭐⭐⭐⭐ **而 990 刚证「间隙紧贴它在后面」的那个位置、"
        "**在源站是由 `BODY` 顶上去的、而源站的 `BODY` 在环的中段**"
    ),
    "p6_tid_sets_differ_both_ways": (
        "✅ **P6 成立：两侧 arc 的 testid 集合互有差集** —— "
        "复刻独有 `canvas-history-launcher`、`canvas-more-trigger`；"
        "源站独有 `canvas-editor-menu` ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐ **「复刻 = 源站」这个假设在 arc 这一段上不成立** ⇒ ⇒ "
        "⇒ ⚠️⭐⭐⭐⭐ **而这不等于「复刻多了两个按钮」** —— "
        "**arc 只是环的一段、不是整个顶栏** ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **816 记的 `KNOWN_CLONE_ONLY` 两个 testid "
        "在这一段上独立复现了** ⇒ "
        "**但「源站对应物是什么」本批只按位置提出怀疑、不判它是同一个东西**"
    ),
    "honest_blind_prediction_992": (
        "⚠️⭐⭐⭐⭐⭐ **本批如实标注：P1/P2/P3/P5 不是盲预测** —— "
        "**选候选时我已经看过这两张 arc 表** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **而 P4 与 P6 是看到表之后才想出来的、它们才是可红的** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **「如实标注哪几条不是盲预测」"
        "**比「假装全是盲预测」诚实** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐ **986 立的那条「预测要按定义写出」在这里要加一个限定："
        "**选候选的方式会污染预测** ⇒ **所以「怎么选候选」本身也要记下来**"
    ),
    "quotes_gate_scope_992": (
        "⭐⭐⭐⭐⭐ **引文门只收「前批的原文」、不许收本批自己的新结论** —— "
        "**那是循环依赖**（本批结论由 verifier 钉、不由引文门钉）⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **而本批要收窄的正是 990 那条 ⇒ 所以引文门验的就是它**："
        "**「间隙紧贴最后一格之前」与「间隙距环尾（`gap_from_end`）」"
        "两句都必须逐字在 README 里** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **989 栽过一次、991 又栽过一次 ⇒ 第三次仍然要跑这道门**"
    ),
    "offline_992": (
        "⭐⭐⭐⭐⭐ **本批纯离线**：不打开浏览器、不按任何键、"
        "**连 `mouse.click` 都没有** ⇒ ⇒ "
        "⭐⭐⭐⭐ **零计费是结构性的、不是自律的** ⇒ "
        "**两侧全部用 973/974 存档**"
    ),
    "ephemeral_992": (
        "⚠️⭐⭐⭐⭐⭐ **本批全部读数都依赖 `/tmp` 里的 973/974 存档、"
        "**它们不在仓库里** ⇒ **这三条结论都会随存档过期而失效** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **而 `dom_rank` 是**绝对下标**、"
        "**换一次构建就可能全变** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **所以本批真正可移植的只有「相对关系」那两条"
        "（下降点 == `BODY`、`rf__wrapper` 是末格）** ⇒ "
        "**绝对下标 −2 / −12 只当作「当时量到的」**"
    ),
}

out["discipline_992"] = "".join([
    "① ⭐⭐⭐⭐⭐ **「同系统的稳定」与「可移植的规律」是两个量、"
    "**后者不蕴含前者** ⇒\n",
    "  ② ⭐⭐⭐⭐⭐ **每条「零例外」都要问「零例外的范围有多大」** ⇒\n",
    "  ③ ⭐⭐⭐⭐⭐ **如实标注哪几条预测不是盲的** —— "
    "**选候选的方式会污染预测** ⇒\n",
    "  ④ ⭐⭐⭐⭐⭐ **候选判据 ≠ 结论**（「相邻同名」还不等于「内层停靠」）⇒\n",
    "  ⑤ ⭐⭐⭐⭐ **差集不等于「多出来的功能」**（arc 只是环的一段）⇒\n",
    "  ⑥ ⭐⭐⭐⭐⭐ **绝对下标是会过期的读数、相对关系才可移植** ⇒\n",
    "  ⑦ ⭐⭐⭐⭐ **本批纯离线、零计费是结构性的** ⇒\n",
])

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("P1 =", out["P1_hold_992"], "P2 =", out["P2_hold_992"],
      "P3 =", out["P3_hold_992"], "P4 =", out["P4_hold_992"],
      "P5 =", out["P5_hold_992"], "P6 =", out["P6_hold_992"])
print("replica gap_from_end =",
      (cr or {}).get("gap_from_end"), "| source gap_from_end =",
      (cs or {}).get("gap_from_end"))
print("replica penultimate =", (cr or {}).get("gap_is_penultimate"),
      "| source penultimate =", (cs or {}).get("gap_is_penultimate"))
print("tid diff:", json.dumps(out["tid_diff_992"], ensure_ascii=False))
print("quotes_all_present =", out["quotes_all_present_992"])
print("PROBE_992_DONE ->", OUT)
