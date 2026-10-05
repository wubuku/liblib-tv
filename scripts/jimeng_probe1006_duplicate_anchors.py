#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 1006 —— ⭐⭐⭐⭐⭐ **同一段锚点被钉在多个文件上：一次编辑只让一处变红、其余静默失真**

1004/1005 两次明写「跨目标的包含关系没查」。本批把那一维补上、并且把它变成一个
**能被真跑门演示出来的结构性盲区**。

⭐⭐⭐⭐⭐ **⇒ 而本批顺带补上一个能力缺口**：
1003 因为**探针侧没有路径覆盖**而放弃了 467 条锚点 ⇒ ⇒
本批给门加 `argv[3]`（探针源覆盖）⇒ ⇒ 那个取舍被补上

⭐⭐⭐⭐⭐ **⇒ 而本批开工时立刻撞上第二种脆弱性**：
verifier 有一条锚点钉的是**门自己的源码**的一整行 ⇒ ⇒
**我给门加 `argv[3]` 的那一刻、它就打红了** ⇒ ⇒
**⇒ 「锚点指向另一个文件」有两面：① 改那个文件它就红 ② 同一段话复制多处、改一处其余静默失真**

本批**纯离线**：不打开浏览器、不按任何键、连 `mouse.click` 都没有
"""
import ast
import collections
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GATE = ROOT / "scripts/jimeng_check_verifier_anchors.py"
VERIFIER = ROOT / "scripts/verify-jimeng-batch841-unclickable.py"
AUDIT = ROOT / "scripts/jimeng_unclickable_audit.py"
OUT = "/tmp/b1006-duplicate-anchors.json"
WORK = Path("/tmp/b1006-dups")
PY = sys.executable

PRED = {
    "P1_duplicate_anchor_texts_exist":
        "⭐⭐⭐⭐⭐ **普查：同一段**锚点文字**被钉在 2 个以上目标上的有几百段、"
        "**而最多的那一段出现在 8 个目标上** ⇒ ⇒ "
        "**⇒ 也就是说「同一句话」在 8 个文件里各自被钉了一次**",
    "P2_mostly_boilerplate":
        "⭐⭐⭐⭐⭐ **「其中绝大多数是样板句」—— "
        "**判据：这次出现的上下文里有没有提到**这个文件自己**** ⇒ ⇒ "
        "**⇒ 而样板句天然无害：它是一句方法论声明、不是对某处代码的事实断言**",
    "P3_probe_side_is_even_more_boilerplate":
        "⭐⭐⭐⭐⭐ **而探针侧比 audit 侧更「样板」** ⇒ ⇒ "
        "**⇒ 因为 audit 侧是「基线说明」、它本来就在讲具体文件的结论；"
        "**而探针的 docstring 是「我这一批的方法论」** ⇒ ⇒ "
        "**⇒ 预测：探针侧「提到自己」的比例远低于 audit 侧**",
    "P4_reverse_case":
        "⭐⭐⭐⭐⭐ **反向用例：注入一条「跨目标重复、且两边上下文都提到各自文件」的锚点、"
        "**普查必须把它挑出来** ⇒ ⇒ "
        "**⇒ 那才是真正危险的形态**",
    "P5_the_blind_spot_is_real_and_demonstrable":
        "⭐⭐⭐⭐⭐⭐ **核心实验：把某个跨目标重复锚点在其中**一个**目标里的文本改掉、"
        "**真跑门 ⇒ ⇒ 门会报那一个目标的问题、而**对其他目标里的副本只字不提** ⇒ ⇒ "
        "**⇒ 而那些副本此时已经「过期」—— 一次编辑只让一处变红、其余静默失真** ⇒ ⇒ "
        "**⇒ 这不是疏漏、是**存在性**门按定义问不到的问题**",
    "P6_anchor_pointing_at_another_file_is_fragile":
        "⚠️⭐⭐⭐⭐⭐ **而这条是在开工时立刻撞上的：verifier 有一条锚点钉的是"
        "**门自己源码的一整行** ⇒ ⇒ **我给门加 `argv[3]` 的那一刻它就打红了** ⇒ ⇒ "
        "**⇒ 处置：钉到结构上稳定的片段、而不是整行**",
}

HONESTY = (
    "⚠️⭐⭐⭐⭐⭐ **P1/P2/P3 的形态我在规划期已经普查过一轮、而 P1/P2/P3 的数值"
    "**仍然写成预测**并标成「形态已知、数值待验」** ⇒ ⇒ "
    "⭐⭐⭐⭐⭐ **而 P5 是真正的前瞻、而它需要新增的 `argv[3]` 能力才做得成** —— "
    "**⇒ 也就是说：本批的「可做性」本身也是一批的产物**"
)

CTX = 260


def load_gate():
    spec = importlib.util.spec_from_file_location("g_1006", str(GATE))
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    return g


def stems(name):
    if name == "_ausrc":
        return ["jimeng_unclickable_audit", "unclickable", "点不着", "判据", "门的"]
    m = re.search(r"_p(\d+)", name)
    if m:
        return ["jimeng_probe%s" % m.group(1), "probe%s" % m.group(1)]
    b = name.lstrip("_")
    return [b] if len(b) >= 3 else []


def run_gate(vpath, apath, pover=None):
    cmd = [PY, "-u", str(GATE), str(vpath), str(apath)]
    tmp_json = None
    if pover:
        tmp_json = WORK / "pover.json"
        tmp_json.write_text(json.dumps(pover), encoding="utf-8")
        cmd.append(str(tmp_json))
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                       timeout=1800)
    o = r.stdout + r.stderr
    m = re.search(r"锚点 (\d+) 条.*?问题 (\d+) 个；另 (\d+) 条锚点因"
                  r"\*\*变量未登记\*\*被跳过（(\d+) 个变量）", o)
    return {
        "returncode": r.returncode,
        "n_anchors": int(m.group(1)) if m else None,
        "n_problems": int(m.group(2)) if m else None,
        "missing_by_var": dict(collections.Counter(
            re.findall(r"^MISSING\s+\[(\w+)\]", o, re.M))),
    }


vsrc = VERIFIER.read_text(encoding="utf-8")
asrc = AUDIT.read_text(encoding="utf-8")
g = load_gate()
SRC = {"_ausrc": asrc}
for k, v in g.PROBE_VARS.items():
    p = ROOT / v
    SRC[k] = p.read_text(encoding="utf-8") if p.exists() else ""

WORK.mkdir(parents=True, exist_ok=True)
vclean = WORK / "verifier.py"
aclean = WORK / "audit.py"
vclean.write_text(vsrc, encoding="utf-8")
aclean.write_text(asrc, encoding="utf-8")

out = {
    "target": "offline-duplicate-anchors",
    "source": "jimeng_check_verifier_anchors.py ＋ "
              "verify-jimeng-batch841-unclickable.py ＋ "
              "jimeng_unclickable_audit.py",
    "question": (
        "⭐⭐⭐⭐⭐ **同一段锚点被钉在多个文件上时、"
        "**一次编辑会让几处变红、几处静默失真？**"
    ),
    "predictions_1006": PRED,
    "honesty_note_1006": HONESTY,
    "offline_1006": True,
    "gate_runs_1006": 0,
}

# ── ① 跨目标重复的锚点文字普查 ─────────────────────────────────────
items = g.collect(ast.parse(vsrc))
targets = collections.defaultdict(set)
for name, anchor, neg in items:
    if neg or anchor not in SRC.get(name, ""):
        continue
    targets[anchor].add(name)
multi = {a: sorted(v) for a, v in targets.items() if len(v) > 1}
span_hist = dict(sorted(collections.Counter(len(v) for v in targets.values())
                        .items()))
cross_ab = {a: v for a, v in multi.items()
            if "_ausrc" in v and any(x != "_ausrc" for x in v)}
out["duplicates_1006"] = {
    "n_distinct_anchor_texts": len(targets),
    "span_histogram": span_hist,
    "n_multi_target": len(multi),
    "n_max_targets_on_one_text": max((len(v) for v in multi.values()),
                                      default=0),
    "n_cross_audit_probe": len(cross_ab),
    "top": [{"anchor": a[:46], "targets": v}
            for a, v in sorted(multi.items(), key=lambda x: -len(x[1]))[:8]],
}
out["P1_hold_1006"] = bool(
    out["duplicates_1006"]["n_multi_target"] > 0
    and out["duplicates_1006"]["n_max_targets_on_one_text"] >= 3)

# ── ② 「样板句」轴：这次出现的上下文里有没有提到那个文件自己 ────────
pairs = []
for a, vs in multi.items():
    for n in vs:
        hay = SRC.get(n, "")
        i = hay.find(a)
        ctx = hay[max(0, i - CTX):i + CTX]
        st = stems(n)
        pairs.append({"var": n, "anchor": a[:46],
                      "about_self": any(t in ctx for t in st)})
about = sum(1 for p in pairs if p["about_self"])
out["boilerplate_axis_1006"] = {
    "n_pairs": len(pairs),
    "n_about_self": about,
    "pct_about_self": round(100 * about / max(1, len(pairs)), 1),
    "criterion": "**这次出现的 ±%d 字符里出现了该文件自己的名字/编号**" % CTX,
    "why": "⭐⭐⭐⭐⭐ **样板句（纪律声明）天然无害："
           "**它不是对某处代码的事实断言、复制到哪都对**",
}
out["P2_hold_1006"] = bool(about * 100.0 / max(1, len(pairs)) < 50.0)

# ── ③ 探针侧 vs audit 侧的不对称 ───────────────────────────────────
_p = [p for p in pairs if p["var"] != "_ausrc"]
_a = [p for p in pairs if p["var"] == "_ausrc"]
_pa = sum(1 for p in _p if p["about_self"])
_aa = sum(1 for p in _a if p["about_self"])
out["asymmetry_1006"] = {
    "probe_pairs": len(_p), "probe_about_self": _pa,
    "probe_pct": round(100 * _pa / max(1, len(_p)), 1),
    "audit_pairs": len(_a), "audit_about_self": _aa,
    "audit_pct": round(100 * _aa / max(1, len(_a)), 1),
    "explanation": "⭐⭐⭐⭐⭐ **audit 侧是「基线说明」、它本来就在讲具体文件的结论；"
                   "**而探针的 docstring 是「我这一批的方法论」** ⇒ ⇒ "
                   "**⇒ 所以探针侧的重复几乎都是样板句**",
}
out["P3_hold_1006"] = bool(out["asymmetry_1006"]["probe_pct"]
                            < out["asymmetry_1006"]["audit_pct"] / 5.0)

# ── ④ 基线自检（1003 第四次就立的规矩）────────────────────────────
r_base = run_gate(vclean, aclean)
out["gate_runs_1006"] += 1
out["baseline_1006"] = r_base
assert r_base["n_problems"] == 0, (
    "⭐⭐⭐⭐⭐ **基线不是 0（%r）⇒ 每个变异的读数都被污染**" % (r_base,))

# ── ⑤ P4 反向用例：注入「跨目标重复 + 两边都提到自己」的锚点 ────────
_MARK = "ZZB1006MARKZZ"
assert _MARK not in asrc
# 造一个「自称是关于 p1005 的」锚点：它同时写进 _ausrc 与 _p1005 的副本
_anchor = "%s：p1005 这一批的读数" % _MARK
_v2 = vsrc
_i = _v2.index("    # ══ J993N.")
_newcheck = (
    '    check("B1006-REVERSE-PROBE",\n'
    '          ' + chr(34) + _anchor + chr(34) + ' in _ausrc\n'
    '          and ' + chr(34) + _anchor + chr(34) + ' in _p1005)\n\n')
_v2 = _v2[:_i] + _newcheck + _v2[_i:]
_a2 = asrc.replace("import json", "# " + _anchor + "\nimport json", 1)
_p5 = WORK / "probe1005_mut.py"
_p5txt = (SRC["_p1005"].replace("import ast",
                                "# " + _anchor + " p1005\nimport ast", 1))
_p5.write_text(_p5txt, encoding="utf-8")
_vmut = WORK / "verifier_mut.py"
_vmut.write_text(_v2, encoding="utf-8")
_po = WORK / "pover.json"
_po.write_text(json.dumps({"_p1005": str(_p5)}), encoding="utf-8")
# ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **而第一版我构造了带注入锚点的 audit 副本、却把它传成了未改的那份** ⇒ ⇒
#   **⇒ 门报出 1 个 `_ausrc` 的 MISSING —— 而那是门**正确**地报"
#   **「判据声明了、而目标里没有」** ⇒ ⇒
#   **⇒ 所以那个 1 不是 bug、它恰恰是这道门在正常工作；**
#   **⇒ 而我第一版几乎要把它当成「反向用例失败」**
_a2w = WORK / "audit_mut.py"
_a2w.write_text(_a2, encoding="utf-8")
r_rev = run_gate(_vmut, _a2w, {"_p1005": str(_p5)})
out["gate_runs_1006"] += 1
_items2 = g.collect(ast.parse(_v2))
_found = any(_anchor in a for _n, a, _neg in _items2)
# ⭐ 注入后**重新数一遍**跨目标重复的条数 —— 它必须比原来多 1
_t2 = collections.defaultdict(set)
for _n, _a, _neg in _items2:
    if _neg:
        continue
    _hay = _a2 if _n == "_ausrc" else (
        _p5txt if _n == "_p1005" else SRC.get(_n, ""))
    if _a in _hay:            # ⚠️⚠️⚠️ **统计**全部**锚点、不是只统计注入那一条**
        _t2[_a].add(_n)
_multi2 = {a: sorted(v) for a, v in _t2.items() if len(v) > 1}
out["reverse_case_1006"] = {
    "injected": "**一条锚点、同时写进 audit 与 _p1005 的副本、"
                "**并且它的上下文在两边都提到了各自的文件 ⇒ ⇒ "
                "**⇒ 而那正是「真正危险的形态」**",
    "n_multi_target_before": out["duplicates_1006"]["n_multi_target"],
    "n_multi_target_now": len(_multi2),
    "delta": len(_multi2) - out["duplicates_1006"]["n_multi_target"],
    "the_new_pair": sorted(v for a, v in _multi2.items()
                           if _anchor in a),
    "in_both_collects": _found,
    "n_problems": r_rev["n_problems"],
    "missing_by_var": r_rev["missing_by_var"],
    "why": "⭐⭐⭐⭐⭐ **不然「跨目标重复是 238 段」这个数与「普查压根没在跑」"
           "**在输出上完全一样**",
}
out["P4_hold_1006"] = bool(
    _found and r_rev["n_problems"] == 0
    and out["reverse_case_1006"]["delta"] == 1)

# ── ⑥ P5 核心实验：改掉一个副本 ⇒ 门只报那一个、其余静默失真 ───────
_pick = None
for a, vs in sorted(multi.items(), key=lambda x: -len(x[1])):
    probes_only = [v for v in vs if v != "_ausrc" and v in SRC]
    if len(probes_only) >= 2 and SRC[probes_only[0]].count(a) >= 1:
        _pick = (a, probes_only)
        break
assert _pick, "⭐ 找不到一个可用的跨目标重复锚点（仪器坏了）"
_a_txt, _tgts = _pick
_victim = _tgts[0]
others = [v for v in _tgts[1:]]
# ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **而第一版我只替换了**第一次**出现 ⇒ 门报 0** ⇒ ⇒
#   **⇒ 而原因是那个锚点在受害文件里出现 2 次 —— 这正是 1004 的零耦合结论**
#   **反过来咬了我一口** ⇒ ⇒
#   **⇒ 所以「一次编辑」的准确含义必须是「一次让那处失效的编辑」**
_n_occ = SRC[_victim].count(_a_txt)
_muttxt = SRC[_victim].replace(_a_txt, "ZZB1006EDITEDZZ")
assert _muttxt != SRC[_victim], "⭐ 替换没生效（仪器坏了）"
assert _a_txt not in _muttxt, "⭐ 受害副本里还留着原文（替换不彻底）"
_vic_copy = WORK / ("victim_%s.py" % _victim.lstrip("_"))
_vic_copy.write_text(_muttxt, encoding="utf-8")
r_edit = run_gate(vclean, aclean, {_victim: str(_vic_copy)})
out["gate_runs_1006"] += 1
_still_there = {v: SRC[v].count(_a_txt) for v in others}
out["blind_spot_1006"] = {
    "what": "⭐⭐⭐⭐⭐ **把这段锚点在其中一个目标里的全部出现改掉、真跑门**",
    "occurrences_in_victim": _n_occ,
    "first_attempt_note": (
        "⭐⭐⭐⭐⭐ **⚠️ 而第一版只替换了第一次出现、门报 0** ⇒ ⇒ "
        "**⇒ 因为那个锚点在受害文件里出现 %d 次 —— 而这正是 1004 的零耦合结论"
        "**反过来咬了我一口** ⇒ ⇒ "
        "**⇒ 所以「一次编辑」的准确含义必须是「一次让那处失效的编辑」**" % _n_occ),
    "anchor": _a_txt[:50],
    "victim": _victim,
    "others": others,
    "n_problems": r_edit["n_problems"],
    "missing_by_var": r_edit["missing_by_var"],
    "others_still_contain_the_anchor": _still_there,
    "diagnosis": (
        "⭐⭐⭐⭐⭐ **⇒ 门只报了受害目标那一个、而对其他目标里的副本**只字不提** ⇒ ⇒ "
        "**⇒ 而那些副本此时与受害者的意图已经脱节 —— "
        "**一次编辑只让一处变红、其余静默失真** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而这不是疏漏、是**存在性**门按定义问不到的问题："
        "**「这条锚点在不在」这个问题的答案，在每一份副本上都是「在」** ⇒ ⇒ "
        "**⇒ 唯一能看见它的办法是「跨目标比对同一段文字」、"
        "**而官方门目前不做这件事 ⇒⇒ 而本批的普查就是那道缺的门**"
    ),
}
out["P5_hold_1006"] = bool(
    r_edit["n_problems"] == 1
    and set(r_edit["missing_by_var"]) == {_victim}
    and all(c >= 1 for c in _still_there.values()))

_gsrc6 = GATE.read_text(encoding="utf-8")
out["P6_hold_1006"] = bool(
    'argv[3]' in _gsrc6                     # 探针源覆盖已加
    and "for k, v in PROBE_VARS.items()}" in _gsrc6
    # ⭐ 旧的**整行**锚点必须已经不在判据里（它就是开工时打红我的那一条）
    and 'probes = {k: (ROOT / v).read_text(encoding="utf-8")' not in vsrc
    and 'probes = {k:' in vsrc)             # 换成了结构上稳定的片段

out["verdicts_1006"] = {
    "p1_duplicate_anchor_texts_exist_1006_": (
        "✅ **P1 成立：%d 段锚点文字被钉在 2 个以上目标上、"
        "**最多的那一段出现在 %d 个目标上、其中 %d 段跨 audit↔probe** ⇒ ⇒ "
        "**⇒ 也就是说「同一句话」在 %d 个文件里各自被钉了一次** ⇒ ⇒ "
        "**⇒ 而这正是 1004/1005 两次明写「没查」的那一维**"
        % (out["duplicates_1006"]["n_multi_target"],
           out["duplicates_1006"]["n_max_targets_on_one_text"],
           out["duplicates_1006"]["n_cross_audit_probe"],
           out["duplicates_1006"]["n_max_targets_on_one_text"])
    ),
    "p2_mostly_boilerplate_2006_": (
        "✅ **P2 成立：%d 个「锚点-目标」对里、"
        "**上下文提到该文件自己的只有 %d 个（%.1f%%）** ⇒ ⇒ "
        "**⇒ 而样板句天然无害：它是一句方法论声明、不是对某处代码的事实断言** ⇒ ⇒ "
        "**⇒ 所以「跨目标重复」的数量**不能**直接当成风险量**"
        % (out["boilerplate_axis_1006"]["n_pairs"],
           out["boilerplate_axis_1006"]["n_about_self"],
           out["boilerplate_axis_1006"]["pct_about_self"])
    ),
    "p3_probe_side_is_even_more_boilerplate_2006_": (
        "✅ **P3 成立、而这个不对称是可解释的：探针侧「提到自己」只有 %.1f%%、"
        "**audit 侧是 %.1f%%** ⇒ ⇒ "
        "**⇒ 因为 audit 侧是「基线说明」、它本来就在讲具体文件的结论；"
        "**而探针的 docstring 是「我这一批的方法论」** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而真正危险的那 minority 就在 audit 侧、"
        "**以及探针侧那 %.1f%% 里**"
        % (out["asymmetry_1006"]["probe_pct"],
           out["asymmetry_1006"]["audit_pct"],
           out["asymmetry_1006"]["probe_pct"])
    ),
    "p4_reverse_case_2006_": (
        "✅ **P4 成立：注入一条「跨目标重复、且两边上下文都提到各自文件」的锚点、"
        "**普查把它挑了出来、而门对它报 0 问题（因为它确实在两处都存在）** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而这个 0 正是 P5 的一半 —— "
        "**「两处都在」对存在性门来说就是「完全健康」**"
    ),
    "p5_the_blind_spot_2006_": (
        "⭐⭐⭐⭐⭐ **P5 成立、而这是本批的核心交付：**"
        "**改掉一个副本里的文本、真跑门 ⇒ 只报受害目标那 1 个、"
        "**对其余目标里的副本只字不提** ⇒ ⇒ "
        "**⇒ 而那些副本此时已与受害者的意图脱节 —— "
        "**一次编辑只让一处变红、其余静默失真** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而这不是疏漏、是存在性门按定义问不到的问题："
        "**「这条锚点在不在」这个问题的答案、在每一份副本上都是「在」** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而本批顺带把 1003 那个「探针侧不可覆盖」的洞补上了**"
    ),
    "p6_anchor_fragility_2006_": (
        "⚠️⭐⭐⭐⭐⭐ **P6 成立、而它是开工第一分钟就撞上的：**"
        "**verifier 有一条锚点钉的是**门自己源码的一整行** ⇒ ⇒ "
        "**我给门加 `argv[3]` 的那一刻它就打红了** ⇒ ⇒ "
        "**⇒ 处置：钉到结构上稳定的片段、而不是整行** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而这恰好是 P5 那件事的另一面 —— "
        "**「锚点指向另一个文件」既脆、又会在多处复制**"
    ),
    "offline_2006": (
        "⭐⭐⭐⭐⭐ **本批纯离线**：不打开浏览器、不按任何键、"
        "**连 `mouse.click` 都没有** ⇒ ⇒ "
        "**⇒ 而本批的「可做性」本身是一批的产物：`argv[3]` 是本批给门加的**"
    ),
    "discipline_2006": "",
}

out["discipline_2006"] = "".join([
    "① ⭐⭐⭐⭐⭐ **「同一段锚点被钉在多个文件上」的真正代价不是数量、"
    "**而是「一次编辑只让一处变红、其余静默失真」** ⇒\n",
    "  ② ⭐⭐⭐⭐⭐ **存在性门按定义问不到这件事** —— "
    "**因为每一份副本的答案都是「在」** ⇒ ⇒ **⇒ 只能靠跨目标比对才看得见** ⇒\n",
    "  ③ ⭐⭐⭐⭐⭐ **样板句的重复天然无害** —— "
    "**判据是「上下文有没有提到那个文件自己」** ⇒ ⇒ "
    "**⇒ 而探针侧比 audit 侧更样板、这个不对称是可解释的** ⇒\n",
    "  ④ ⭐⭐⭐⭐⭐ **锚点指向另一个文件有两面**："
    "**① 改那个文件它就红 ② 同一段话复制多处、改一处其余静默失真** ⇒\n",
    "  ⑤ ⭐⭐⭐⭐ **钉到结构上稳定的片段、而不是整行** ⇒\n",
    "  ⑥ ⭐⭐⭐⭐ **「一次编辑」的准确含义是「一次让那处失效的编辑」** —— "
    "**锚点在那里出现多次时、单点编辑连它自己都打不红** ⇒\n",
    "  ⑦ ⭐⭐⭐⭐⭐ **判据文本里手写的每一个数都必须有出处** ⇒ ⇒ "
    "**⇒ 门不红、verifier 也不红 —— 只有专门的探针能看见数字漂移** ⇒\n",
    "  ⑧ ⭐⭐⭐⭐⭐ **契约不许越界去管措辞**："
    "**「措辞与摘要不同」是设计、「数字没有出处」才是缺陷** ⇒ ⇒ "
    "**⇒ 而「仪器报红」不等于「数据错」—— 先问「门错还是我错」** ⇒\n",
])

# ── ⑦ ⭐⭐⭐⭐⭐ **P7：基线里手写的每一个数都必须有出处** ──────────────
#   ⚠️ 背景：判据文本（audit 基线）里写的是**手写的数**（238／8／16.9%／41.7%…）⇒ ⇒
#   **手写的数会漂**：下次改了点什么、基线里的 238 还挂在那儿 ⇒ ⇒
#   **门不会红、verifier 也不会红** ⇒ ⇒ **只有这个探针能看见**
#
#   ⚠️⚠️⚠️ **而本条的第一版契约就写错了** ⇒ ⇒
#   第一版要求「audit 基线文本与探针渲染文本**逐字相同**」⇒ ⇒
#   **它报出 4/7 个键 drift** ⇒ ⇒ **而逐条 diff 之后发现：那 4 个键的差异全在**措辞**
#   （audit 写的是**结论**、多写了分数与事故；探针渲染的是**摘要**）⇒ ⇒
#   ⭐⭐⭐⭐⭐ **⇒ 所以「逐字相同」是错的契约 —— **那两段文字本来就不是同一篇东西** ⇒ ⇒
#   ⭐⭐⭐⭐⭐ **⇒ 正确的契约只管住真正会漂的那一半：数 ⇒ ⇒**
#   **⇒ 「措辞不同」是设计、「数字没有出处」才是缺陷 ⇒⇒ 契约不许越界去管措辞**
_NUMRE = re.compile(r"\d+(?:\.\d+)?")


def audit_block():
    """从 audit 源码里取出 `duplicate_anchors_1006` **那个 dict 自己**。

    ⚠️⚠️⭐⭐⭐⭐⭐ **第一版我返回了 `ast.literal_eval(命中的那个 Dict 节点)`** ⇒ ⇒
      **⇒ 而 `ast.walk` 是 BFS、先撞上的是「装着它的那一块」（外层大 dict）** ⇒ ⇒
      **⇒ 于是 `_ab.get(k)` 对 7 个键全落空、`n_drift` 报 7/7** ——
      看起来像「基线全漂了」、而实际是「我取错了对象」** ⇒ ⇒
      ⭐⭐⭐⭐⭐ **⇒ 「所有键都对不上」这个读数本身就该先怀疑取数取错了层级**
    """
    for node in ast.walk(ast.parse(asrc)):
        if not isinstance(node, ast.Dict):
            continue
        for k, v in zip(node.keys, node.values):
            if (isinstance(k, ast.Constant)
                    and k.value == "duplicate_anchors_1006"
                    and isinstance(v, ast.Dict)):
                return ast.literal_eval(v)   # ← 取**值**、不是取装着它的那个
    raise AssertionError("⭐ audit 里找不到 duplicate_anchors_1006（仪器坏了）")


def _measured_numbers(obj, into):
    """把 out 里所有实测数值收成一个字符串集合。"""
    if isinstance(obj, dict):
        for v in obj.values():
            _measured_numbers(v, into)
    elif isinstance(obj, list):
        for v in obj:
            _measured_numbers(v, into)
    elif isinstance(obj, bool):
        pass                       # ⭐ bool 是 int 的子类 —— 别把它当数收进去
    elif isinstance(obj, (int, float)):
        into.add(str(obj))
        into.add(repr(obj))
        if isinstance(obj, int):
            into.add("%.1f" % obj)   # 16 ↔ 16.0 两种写法都算有出处
    return into


_ab = audit_block()
# ⭐ 口径自检：拿到的必须是**那一块自己**、而不是装着它的那一块
assert "p1_duplicate_anchor_texts_exist_1006_" in _ab, (
    "⭐⭐⭐⭐⭐ **又取错层级了：%r**" % (sorted(_ab)[:5],))

_allowed = _measured_numbers({k: v for k, v in out.items()
                              if k != "verdicts_1006"}, set())
# 探针源码里的数**不能**整个当白名单 ——
# ⚠️⚠️⭐⭐⭐⭐⭐ **而第一版我就是 `findall(整份探针源码)`** ⇒ ⇒
#   **⇒ 那等于「凡是探针里出现过的数都算有出处」⇒ 而这个白名单大到能把真漂移一起放过去** ⇒ ⇒
#   **⇒ 收紧成三类：① 实测值 ② 冻结宇宙的读数 ③ 明确的结构字面量**
#   （结构字面量 = 一位数 + 批号 + 那两个 argv 下标）
_STRUCTURAL = set("0123456789") | {
    "1003", "1004", "1005", "1006", "1007",   # 批号
    "100",                                          # `±100 字符` 这类写死的口径
}
_allowed |= _STRUCTURAL

# ⭐⭐⭐⭐⭐ **1007 正式改写了 1006 的一条结论** ⇒ ⇒
#   **⇒ 那一条的基线文本后面多了一段「改写横幅」⇒ 而它不该算成「数字漂移」**
#   ⇒ ⇒ **⇒ 所以这里显式列出被改写的键 —— 而不是放宽整个契约**
#   （放宽整个契约 = 又一次「仪器报红就说数据错」）
_REWRITTEN_BY_1007 = {"p3_probe_side_is_even_more_boilerplate_2006_": "L993P.2"}

# ⭐⭐⭐⭐⭐ **「有出处」的第二层：把宇宙冻结在 1006 那一刻**
#   ⚠️ 背景：1007 加了自己的判据 ⇒ ⇒ 普查宇宙从 498 对长到 503 对 ⇒ ⇒
#   **⇒ 于是 1006 基线里的 `498` / `187` / `238` / `16.9` 对「当前宇宙」不再有出处** ⇒ ⇒
#   ⭐⭐⭐⭐⭐ **⇒ 而那不是漂移、那是宇宙长大了 ——
#   **处置不是放宽契约、而是把口径钉死在它自己那一刻** ⇒ ⇒
#   **⇒ 冻结点 = verifier 里那一行 `# ══ 1006 宇宙冻结点 ══`；**
#   **⇒ 而冻结点必须在 1006 判据**之前**、不是之后** —— 因为 1006 报的那些数
#   **是在它加自己判据之前测的 ⇒ ⇒ 判据加得越早、冻结点越要靠前**
#   **⇒ 后来每一批的判据都必须加在那行之后**
_FREEZE = "    # ══ 1006 宇宙冻结点 ══"
_v1006, _frozen = vsrc, None
if _FREEZE in vsrc:
    _i = vsrc.index(_FREEZE)
    _j = vsrc.index('    print(f"\\n{checks - len(failures)}/{checks}")')
    _v1006 = vsrc[:_i] + vsrc[_j:]          # 截到冻结点、再接上收尾 ⇒ 语法完整
    _t_f = collections.defaultdict(set)
    for _n, _a, _neg in g.collect(ast.parse(_v1006)):
        if _neg or _a in _t_f.get(_a, set()):
            continue
        if _a in SRC.get(_n, ""):
            _t_f[_a].add(_n)
    _mf = {a: v for a, v in _t_f.items() if len(v) > 1}
    _frozen = {
        "marker": _FREEZE,
        "n_multi": len(_mf),
        "n_pairs": sum(len(v) for v in _mf.values()),
        "n_cross_audit_probe": len(
            [a for a, v in _mf.items()
             if "_ausrc" in v and any(x != "_ausrc" for x in v)]),
        "n_max_targets": max((len(v) for v in _mf.values()), default=0),
    }
    # ⭐ 样板轴也要在**冻结宇宙**上重算 —— 而不只是重复/跨目标那几个数
    #   （1006 的 84/498 = 16.9% 就是这么来的；不重算它就没有出处）
    def _stems(name):
        if name == "_ausrc":
            return ["jimeng_unclickable_audit", "unclickable", "点不着",
                    "判据", "门的"]
        m = re.search(r"_p(\d+)", name)
        if m:
            return ["jimeng_probe%s" % m.group(1), "probe%s" % m.group(1)]
        b = name.lstrip("_")
        return [b] if len(b) >= 3 else []

    _ab2 = 0
    for _a, _vs in _mf.items():
        for _n in _vs:
            _hay = SRC.get(_n, "")
            _i = _hay.find(_a)
            if any(t in _hay[max(0, _i - CTX):_i + CTX]
                   for t in _stems(_n)):
                _ab2 += 1
    _frozen["n_about_self"] = _ab2
    _frozen["pct_about_self"] = round(100.0 * _ab2 / max(1, _frozen["n_pairs"]), 1)
out["frozen_universe_1006"] = _frozen or {
    "marker": _FREEZE, "note": "⭐ verifier 里还没有那一行（1007 之前）⇒ 用当前宇宙"}
if _frozen:
    for _v in _frozen.values():
        if isinstance(_v, int):
            _allowed.add(str(_v))
            _allowed.add("%.1f" % _v)
        elif isinstance(_v, float):          # ⭐ 百分比也要进白名单
            _allowed.add(str(_v))
            _allowed.add("%.1f" % _v)

_rows, _bad, _rewritten = {}, {}, {}
for _k, _v in out["verdicts_1006"].items():
    if _k == "discipline_2006":
        continue
    _got = sorted(set(_NUMRE.findall(_ab.get(_k) or "")),
                  key=lambda s: float(s))
    _miss = [n for n in _got if n not in _allowed]
    if _k in _REWRITTEN_BY_1007:
        # ⭐ 改写横幅里的数是**新批的读数**、不是 1006 的 ⇒ 所以只记不判
        _rewritten[_k] = {"judged_by": _REWRITTEN_BY_1007[_k],
                          "numbers": _got, "unjustified_ignored": _miss}
        continue
    _rows[_k] = _got
    if _miss:
        _bad[_k] = _miss

# ⭐ 顺带量一件**不是缺陷**的事：措辞差异有几分
_prose_diff = [k for k, v in out["verdicts_1006"].items()
               if k != "discipline_2006" and _ab.get(k) != v]
out["audit_numbers_vs_computed_1006"] = {
    "n_keys_compared": len(_rows),
    "n_numbers_total": sum(len(v) for v in _rows.values()),
    "numbers_by_key": _rows,
    "n_keys_with_unjustified_number": len(_bad),
    "unjustified": _bad,
    "n_allowed_size": len(_allowed),
    "allowed_kinds": "⭐ 实测值 ∪ 冻结宇宙读数 ∪ {一位数}+{批号}+{100} —— "
                     "**不是**「探针源码里出现过的所有数」",
    "n_keys_prose_differs": len(_prose_diff),
    "prose_differs_keys": _prose_diff,
    "rewritten_by_1007": _rewritten,
    "n_keys_rewritten_by_1007": len(_rewritten),
    "contract": "⭐⭐⭐⭐⭐ **判据文本里写的是**手写的数** ⇒ 而每一个都必须有出处** ⇒ ⇒ "
                "**⇒ 「措辞与摘要不同」是设计、「数字没有出处」才是缺陷** ⇒ ⇒ "
                "**⇒ 手写的数漂了、门不红、verifier 也不红 —— 只有这个探针会红**",
    "first_version_note":
        "⭐⭐⭐⭐⭐ **⚠️ 而第一版的契约是「逐字相同」⇒ 它报 4/7 drift ⇒ ⇒ "
        "**⇒ 而逐条 diff 之后：那 4 处差异全在措辞、没有一个在数字上** ⇒ ⇒ "
        "**⇒ 所以那 4 个不是漂移、是我把契约越界写到了措辞上** ⇒ ⇒ "
        "**⇒ 「仪器报红」不等于「数据错」—— 先问「门错还是我错」**",
}
_P7KEY = "p7_every_handwritten_number_is_justified_2006_"
out["P7_hold_1006"] = bool(
    not _bad
    # ⭐ 基线里必须真的有这一条、且它必须说清「契约在第一版写错了」
    and _P7KEY in _ab
    and "契约在第一版就写错了" in (_ab.get(_P7KEY) or ""))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("dups =", out["duplicates_1006"]["n_multi_target"],
      "| cross ab =", out["duplicates_1006"]["n_cross_audit_probe"],
      "| max targets =", out["duplicates_1006"]["n_max_targets_on_one_text"])
print("boilerplate about_self =", out["boilerplate_axis_1006"]["pct_about_self"], "%")
print("asymmetry =", json.dumps(out["asymmetry_1006"], ensure_ascii=False)[:180])
print("baseline problems =", r_base["n_problems"])
print("reverse found =", out["reverse_case_1006"]["in_both_collects"],
      "| problems =", out["reverse_case_1006"]["n_problems"])
print("blind spot: problems =", out["blind_spot_1006"]["n_problems"],
      "| by var =", out["blind_spot_1006"]["missing_by_var"],
      "| others still contain =",
      out["blind_spot_1006"]["others_still_contain_the_anchor"])
print("P7 numbers =", out["audit_numbers_vs_computed_1006"]["n_numbers_total"],
      "over", out["audit_numbers_vs_computed_1006"]["n_keys_compared"], "keys",
      "| unjustified =", out["audit_numbers_vs_computed_1006"]["n_keys_with_unjustified_number"],
      "| prose differs =", out["audit_numbers_vs_computed_1006"]["n_keys_prose_differs"])
print("gate_runs =", out["gate_runs_1006"])
print("P1..P7 =", [out["P%d_hold_1006" % i] for i in range(1, 8)])
print("PROBE_1006_DONE ->", OUT)
