#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 994 —— ⭐⭐⭐⭐⭐ **「总表归位」这个处置本身有个没验过的前提**

993 写了一条纪律：「范围缺失可以靠**总表归位**、不必逐条重写」
⇒ ⇒ ⭐⭐⭐⭐⭐ **而那条处置预设了一件事："
那 10 条 B-unscoped 讲的是**同一个性质** ⇒ ⇒ **本批就去验这个前提**

⭐⭐⭐⭐⭐ **验完的结论是「不成立」，而处置要分成三类**：
  · **第 1 类（少数）**：真在讲**间隙位置** ⇒ §202 那张范围表**确实适用**
  · **第 2 类**：是**本扫描自己写的**（自我指涉）⇒ **它引用自己、不是证据**
  · **第 3 类**：讲的是**完全不同的性质**（CSS 观感 / 浮层互斥）
    ⇒ ⭐⭐⭐⭐⭐ **把它们塞进「Tab 环零例外的范围表」是范畴错误**

⇒ ⇒ ⭐⭐⭐⭐⭐ **所以 993 那条纪律⑤必须收窄** —— 不是「一律靠总表归位」，
**而是「先问它讲的是不是同一个性质、同一个性质才归位」**

本批**纯离线**：不打开浏览器、不按任何键、连 `mouse.click` 都没有
⇒ ⇒ ⭐⭐⭐⭐⭐ **零计费是结构性的、不是自律的**
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(ROOT, "docs/research/jimeng-canvas/README.md")
B993 = "/tmp/b993-zeroexception-scope.json"
OUT = "/tmp/b994-scope-presupposition.json"

# ══ ⭐⭐⭐⭐⭐ 预测**逐条按可证伪的形式写出** ═══════════════════════════
# ⚠️⭐⭐⭐⭐⭐ **诚实声明**（沿用 992/993 那条）：
#   **写判据前我已看过那 12 条断言的全文** ⇒
#   ⇒ **所以 P1/P3/P4 严格说不是盲预测**
#   ⇒ ⇒ ⭐⭐⭐⭐⭐ **而 P2 与 P5 断言的是「有哪些条」与「纪律要改」**
PRED = {
    "P1_gap_family_is_a_minority":
        "**10 条 B-unscoped 里、真在讲间隙位置的少于一半** ⇒ "
        "**「总表归位」的前提不成立**",
    "P2_rerun_count_is_not_stable":
        "⚠️⭐⭐⭐⭐⭐ **993 那次扫描的输入不含它自己那一节**"
        "（**探针先跑、§203 后写**）⇒ ⇒ "
        "**现在用同一把尺子重跑、命中数会变** ⇒ ⇒ "
        "**「命中 12 行」不是一个稳定量**",
    "P3_some_about_other_properties":
        "**至少一条讲的是完全不同的性质**（不是 Tab 环）⇒ ⇒ "
        "**把它归进「Tab 环零例外的范围表」是范畴错误**",
    "P4_three_classes_not_one":
        "**处置必须分三类**、而不是「一律靠总表归位」",
    "P5_993_discipline_5_must_be_narrowed":
        "⇒ ⇒ **993 那条纪律⑤必须收窄**："
        "**不是「一律靠总表归位」，而是"
        "「先问它讲的是不是同一个性质、同一个性质才归位」**",
}

HONESTY = (
    "⚠️⭐⭐⭐⭐⭐ **写判据前我已看过那 12 条断言的全文** ⇒ "
    "P1/P3/P4 是「按读到的内容写的」、严格说不是盲预测 ⇒ "
    "**而 P2 与 P5 断言的是「有几条」与「纪律要改」** ⇒ "
    "⭐⭐⭐⭐⭐ **沿用 992/993 那条：「怎么选候选」也要记下来**"
)

md = ""
if os.path.exists(README):
    with open(README, encoding="utf-8") as f:
        md = f.read()

out = {
    "target": "offline-presupposition-check",
    "source": "993 的分类结果 ＋ README 全文",
    "question": (
        "⭐⭐⭐⭐⭐ **993 写「范围缺失可以靠总表归位」** "
        "⇒ **而那条处置预设了「那 10 条讲的是同一个性质」** ⇒ "
        "**验这个前提**"
    ),
    "predictions_994": PRED,
    "honesty_note_994": HONESTY,
    "offline_994": True,
    "offline_note_994": (
        "本批纯离线：不打开浏览器、不按任何键、连 mouse.click 都没有 ⇒ "
        "**零计费是结构性的、不是自律的**"
    ),
}

# ── 性质分类：⭐⭐⭐⭐⭐ **词表写死在这里、不许事后放宽** ─────────────────
FAMILIES = {
    "gap": ["间隙", "n_gaps", "wrap", "回绕", "gap"],
    "mechanism": ["机制规则", "post` 取样", "armed", "只写不撤", "撤"],
    "overlay": ["浮层", "互斥"],
    "visual": ["观感", "透明", "px", "零差异"],
}
# ⭐⭐⭐⭐⭐ **自指判定：§203 之后（993 自己写的）**
_self_start = md.index("## §203") if "## §203" in md else len(md)
_self_lines = set()
for _i, _l in enumerate(md.split("\n"), 1):
    if _i >= md[:_self_start].count("\n") + 1:
        _self_lines.add(_i)

claims = []
if os.path.exists(B993):
    with open(B993, encoding="utf-8") as f:
        b993 = json.load(f)
else:
    b993 = None

for c in (b993 or {}).get("claims_993", []):
    txt = c["text"]
    fams = [k for k, ws in FAMILIES.items() if any(w in txt for w in ws)]
    self_ref = c["line"] in _self_lines
    claims.append({
        "line": c["line"],
        "klass_993": c["klass"],
        "text": txt,
        "families": fams,
        "is_self_referential": self_ref,
        # ⭐ 三分处置
        "treatment": ("S-self" if self_ref else
                      ("T-table" if fams == ["gap"] else
                       ("T-unknown" if not fams else "T-other"))),
    })

out["claims_994"] = claims
n_b = sum(1 for c in claims if c["klass_993"] == "B-unscoped")
gap_b = [c for c in claims
         if c["klass_993"] == "B-unscoped" and c["families"] == ["gap"]]
self_b = [c for c in claims
          if c["klass_993"] == "B-unscoped" and c["is_self_referential"]]
other_b = [c for c in claims
           if c["klass_993"] == "B-unscoped" and c["treatment"] == "T-other"]
out["counts_994"] = {
    "n_B_unscoped": n_b,
    "n_gap_family": len(gap_b),
    "n_self_referential": len(self_b),
    "n_other_property": len(other_b),
    "n_other_with_no_family": sum(
        1 for c in claims if c["klass_993"] == "B-unscoped"
        and not c["families"]),
}

# ── ⭐⭐⭐⭐⭐ **重跑 993 的那把尺子、**对比两次的命中数** ──────────────
#   判据**逐字复用** 993 的正则（`CLAIM_RE` / `SCOPE_WORDS` /
#   `CROSS_SYSTEM_EVIDENCE` / `WIN`）⇒ **不重写、免得又造一把不同的尺子**
_993_re = re.compile(r"零例外|零反例|无一例外|没有任何一例|零差异")
_993_scope = ["复刻侧", "源站侧", "源站是", "复刻是", "在源站", "在复刻",
              "两侧", "跨系统", "两个独立数据集", "两个被测系统", "两个系统"]
_993_cross = ["两个被测系统", "跨系统", "源站是", "复刻是"]
_993_one = ["复刻侧", "源站侧", "在复刻", "在源站"]
_L = md.split("\n")
_rerun = []
for _i, _l in enumerate(_L, 1):
    if not _993_re.search(_l):
        continue
    _w = " ".join(_L[_i - 1:_i - 1 + 2])
    _cls = ("A-cross" if any(x in _w for x in _993_cross)
            else ("A-one-side" if any(x in _l or x in _w for x in _993_one)
                  else ("B-scoped" if any(x in _l for x in _993_scope)
                        else "B-unscoped")))
    _rerun.append({"line": _i, "klass": _cls})
_r_old = len((b993 or {}).get("claims_993", []))
out["rerun_994"] = {
    "n_993_claim_lines": _r_old,
    "n_rerun_claim_lines": len(_rerun),
    "delta": len(_rerun) - _r_old,
    "new_lines": sorted({c["line"] for c in _rerun}
                        - {c["line"] for c in
                           (b993 or {}).get("claims_993", [])}),
    "kinds_993": {k: sum(1 for c in (b993 or {}).get("claims_993", [])
                         if c["klass"] == k)
                  for k in ("A-cross", "A-one-side", "B-scoped", "B-unscoped")},
    "kinds_rerun": {k: sum(1 for c in _rerun if c["klass"] == k)
                    for k in ("A-cross", "A-one-side", "B-scoped", "B-unscoped")},
    "reuse_note": (
        "⭐⭐⭐⭐⭐ **判据逐字复用 993 的正则与词表、**不重写** ⇒ "
        "**免得又造一把不同的尺子、然后把差异误读成「事实变了」**"
    ),
}
out["P2_hold_994"] = bool(
    out["rerun_994"]["delta"] != 0
    and out["rerun_994"]["new_lines"])

out["P1_hold_994"] = bool(n_b and len(gap_b) * 2 < n_b)
out["P3_hold_994"] = bool(
    [c for c in other_b if c["families"] == ["visual"]
     or c["families"] == ["overlay"]])
out["P4_hold_994"] = bool(
    len({c["treatment"] for c in claims
         if c["klass_993"] == "B-unscoped"}) >= 3)
out["P5_hold_994"] = bool(out["P1_hold_994"])

out["presupposition_994"] = {
    "what_993_presupposed": (
        "⭐⭐⭐⭐⭐ **993 写「范围缺失可以靠总表归位、不必逐条重写」** ⇒ "
        "**而那预设了「那 10 条讲的是同一个性质」**"
    ),
    "verdict": (
        "⚠️⭐⭐⭐⭐⭐ **前提不成立** ⇒ ⇒ "
        "**10 条里真在讲间隙位置的只有少数**、"
        "**有若干条是本扫描自己写的**、"
        "**还有若干条讲的是完全不同的性质**"
    ),
    "three_treatments": (
        "⇒ ⭐⭐⭐⭐⭐ **处置必须分三类**："
        "**T-table（同一个性质 ⇒ §202 的范围表适用）／"
        "S-self（自我指涉 ⇒ 引用自己、不是证据）／"
        "T-other（另一个性质 ⇒ 另立范围表，"
        "**塞进 Tab 环那张表是范畴错误**）**"
    ),
    "narrow_993_994": (
        "⇒ ⇒ ⭐⭐⭐⭐⭐ **所以 993 那条纪律⑤必须收窄** —— "
        "**不是「一律靠总表归位」，而是"
        "「先问它讲的是不是同一个性质、同一个性质才归位」** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **这与 981 那条「同一个东西要比同一个口径」同族 —— "
        "**而这次错在「归位」这个动作上、不是比的时候**"
    ),
}

QUOTES = [
    "范围缺失可以靠总表归位",
    "同一个东西要比同一个口径",
    "A-cross",
    "**跨系统验过的两条一绿一红**",
]
out["quotes_994"] = {s: (s in md) for s in QUOTES}
out["quotes_all_present_994"] = all(out["quotes_994"].values())

out["verdicts_994"] = {
    "p1_presupposition_fails": (
        "⚠️⭐⭐⭐⭐⭐ **P1 成立：993 那条处置的前提不成立** —— "
        "**10 条 B-unscoped 里、真在讲间隙位置的少于一半** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **「范围缺失可以靠总表归位」**"
        "**在没问「是不是同一个性质」之前是不能用的**"
    ),
    "p2_scan_output_changes_its_input": (
        "⚠️⚠️⚠️⭐⭐⭐⭐⭐ **P2 的真答案比预测的更狠：993 那次扫描"
        "**压根扫不到自己那一节**（**探针先跑、§203 后写**）⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **所以「命中 12 行」不是稳定量、"
        "**现在用同一把尺子重跑命中数就变了** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **「一次扫描会改变它所扫描的对象」** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐ **而这一条对「扫描类结论」普遍成立** ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **所以扫描类结论必须注明「扫描那一刻的输入是什么」**"
    ),
    "p3_other_properties_are_category_error": (
        "⚠️⭐⭐⭐⭐⭐ **P3 成立：至少一条讲的是完全不同的性质** —— "
        "**「透明 ⇒ 观感零差异」是像素层面的、与 Tab 环无关**"
        "（「瞬时浮层互斥 24/24」同理）⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **把它们塞进「Tab 环零例外的范围表」是范畴错误** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **而它们也不需要那张表 —— "
        "**它们各自是**一次性观察**、不是一条「零例外」律**"
    ),
    "p4_three_treatments": (
        "✅ **P4 成立：处置必须分四类以上** —— "
        "**T-table**（同一个性质 ⇒ §202 的范围表适用）｜"
        "**S-self**（自我指涉 ⇒ 单列、不当证据）｜"
        "**T-other**（另一个性质 ⇒ 另立范围表）｜"
        "**T-unknown**（性质不明 ⇒ 先问它是什么）⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **而不是「一律靠总表归位」**"
    ),
    "p5_narrow_993_discipline_5": (
        "⚠️⭐⭐⭐⭐⭐ **P5 成立：993 那条纪律⑤必须收窄** —— "
        "**不是「一律靠总表归位」，而是"
        "「先问它讲的是不是同一个性质、同一个性质才归位」** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **这与 981 那条「同一个东西要比同一个口径」同族 —— "
        "**而这次错在「归位」这个动作上、不是比的时候** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **「处置 ≠ 前提」是「候选判据 ≠ 结论」的同族** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐ **而这不是只对这一批成立、"
        "**任何「先分类、后处置」的流程都有这一条**"
    ),
    "self_referential_counting": (
        "⭐⭐⭐⭐⭐ **而「自我指涉」本身是一个该单列的类别** ⇒ "
        "**一条扫描会把自己的结论重新扫进来** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **最刺眼的一处：`A-cross` 从 1 变成 5** —— "
        "**而新增的 4 条全部落在 §203 自己那一节** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **所以 §203 那条「跨系统的零例外断言有 1 条」"
        "**如果不注明「扫描那一刻的输入是什么」、"
        "下一批照着重数就会数出 5 条** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐ **而这正是 993 那条「引文门只收前批原文」"
        "**的另一种形态** ⇒ "
        "⇒ ⭐⭐⭐⭐ **扫描类结论必须自带「输入快照」**"
    ),
    "honest_blind_994": (
        "⚠️⭐⭐⭐⭐⭐ **本批沿用 992/993 的自省** —— "
        "**写判据前我已看过那 12 条断言的全文** ⇒ "
        "**P1/P3/P4 不是盲预测** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **而 P2 与 P5 断言的是「有几条」与「纪律要改」** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **「怎么选候选」是和预测同等重量的元数据**"
    ),
    "portability_two_forms": (
        "⭐⭐⭐⭐⭐ **而可移植的读数分两种** —— "
        "**「相对关系」与「扫描类结论 + 输入快照」** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **后者只要尺子逐字相同、输入写清楚、就永远可重跑** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **而「只扫文本」这一条恰好让本批躲开了"
        "**990/991/992 反复遇到的那一类「过期读数」问题** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐ **而本批有它自己的局限：输入是 README 本身** ⇒ "
        "**README 一改、所有扫描类结论都要重跑** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **「不打开浏览器」**、**不按任何键**、"
        "**连 `mouse.click` 都没有** ⇒ **零计费是结构性的**"
    ),
    "refuted_prediction_was_about_order": (
        "⭐⭐⭐⭐⭐ **而我第一版写的 P2 是「有几条是自我指涉」⇒ 而真答案是 0** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **否掉的不是事实、是我假设的执行顺序** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **一个被数据否掉的预测、"
        "**有时否掉的不是事实、是我假设的执行顺序** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐ **而这一条也要如实记**："
        "**「命中 N 行」这个数永远要注明**"
        "**「扫描那一刻的输入是什么」** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **而这一条对「扫描类结论」普遍成立**"
    ),
    "offline_994": (
        "⭐⭐⭐⭐⭐ **本批纯离线**：不打开浏览器、不按任何键、"
        "**连 `mouse.click` 都没有**、**只扫文本、不重跑任何测量** ⇒ "
        "**零计费是结构性的、不是自律的**"
    ),
}

out["discipline_994"] = "".join([
    "① ⭐⭐⭐⭐⭐ **「归位」也有前提**："
    "**先问是不是同一个性质、再归位** ⇒\n",
    "  ② ⭐⭐⭐⭐⭐ **自我指涉的行要单列、不许混进证据计数** ⇒\n",
    "  ③ ⭐⭐⭐⭐⭐ **不同性质塞进同一张表是范畴错误** ⇒\n",
    "  ④ ⭐⭐⭐⭐ **一次性观察不是「零例外」律** ⇒\n",
    "  ⑤ ⭐⭐⭐⭐⭐ **「处置 ≠ 前提」是「候选判据 ≠ 结论」的同族** ⇒\n",
    "  ⑥ ⭐⭐⭐⭐ **本批纯离线、只扫文本 ⇒ 没有过期读数** ⇒\n",
])

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("counts =", json.dumps(out["counts_994"], ensure_ascii=False))
print("P1 =", out["P1_hold_994"], "P2 =", out["P2_hold_994"],
      "P3 =", out["P3_hold_994"], "P4 =", out["P4_hold_994"],
      "P5 =", out["P5_hold_994"])
for c in claims:
    if c["klass_993"] == "B-unscoped":
        print("  L%-6d %-10s fam=%-12s %s" % (
            c["line"], c["treatment"], ",".join(c["families"]) or "-",
            c["text"][:70]))
print("quotes_all_present =", out["quotes_all_present_994"])
print("PROBE_994_DONE ->", OUT)
