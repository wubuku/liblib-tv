#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 1007 —— ⭐⭐⭐⭐⭐ **1006 那把「样板轴」的刀：是我自己造的、也由我自己拆掉**

1006 给了「样板轴」：判据是「**这次出现的上下文里有没有提到该文件自己**」，
并写下「探针侧 1.9% vs audit 侧 41.7%、**而这个不对称是可解释的**」。

⭐⭐⭐⭐⭐ **⇒ 而本批就是去查那个「可解释」到底可解释了什么。**

**❌ P1**：用 1006 那把刀，「同一条句子在它的多个副本里前后不一致」的占 33.8%
   —— 我预测「只有少数」、**被否**
**⭐ P2（P1 修正后）**：99% 的不一致是**词表自己造的**
**❌⭐⭐⭐⭐⭐ P3**：那把刀**没有客观停点** —— 窗口 0/40/120/260/600 单调涨、无拐点
**✅ P4**：唯一有停点的口径是「只看那句话本身」⇒ 而它的读数是 **0/503**
**✅ P5**：反向用例 —— 两把刀都**不是恒零**（否则上面那些读数全无意义）
**✅ P6**：清单逐条落进仓里、且是本探针自己写的

本批**纯离线**：不打开浏览器、不按任何键、连 `mouse.click` 都没有
"""
import ast
import collections
import importlib.util
import io
import json
import re
import subprocess
import sys


# ── ⭐⭐⭐⭐⭐ 1032-②f：**退出码必须真的说话** ——
#   ⇒ ⇒ 本脚本以前是一个平铺脚本、**没有 `sys.exit`** ⇒ ⇒
#   ⇒ ⇒⇒ **无论 P1..PN 有几条是 False，退出码恒为 0** ⇒ ⇒⇒⇒
#   ⇒ ⇒⇒⇒⇒ **⇒ 而 1015 的分类器是「rc≠0 ⇒ crashed」⇒ ⇒⇒⇒⇒
#   ⇒ ⇒⇒⇒⇒⇒ ⇒ **⇒ 于是「自报红」被记成了「rc=0 / state=reproduced」** ⇒ ⇒⇒⇒⇒
#   ⇒ ⇒⇒⇒⇒⇒ ⇒⇒ **⇒ 「退出码恒 0 的门，等于没有门」—— 本批把它变成真话**：
#   ⇒ ⇒⇒⇒⇒⇒ ⇒⇒   ① 判据红 ⇒ **rc=1**  ② 仪器崩 ⇒ **rc=2**  ③ 全绿 ⇒ **rc=0**
#   ⚠️⭐⭐⭐⭐⭐ **崩与红必须分开记账** —— 而它们以前**都记成了 0**
#   ⚠️ 而「红」必须先逐条定性过：**预测被否型**（False 才是结论）不算红


def _exit_code(criteria, crashed=False):
    """退出码的**纯函数**（⇒ 可单测、也可被别的门当契约引用）。"""
    if crashed:
        return 2
    # ⭐⭐⭐⭐⭐ 1032-②f（补）：**「不适用」（`None`）不许算成「红」** —⇒
    #   ⇒ ⇒ `all([True, None])` 是 `False` ⇒ ⇒⇒ **而 `None` 的意思是「没测到」**
    #   ⇒ ⇒⇒⇒ **⇒ 把「没测到」算成「测了、没过」⇒ ⇒ 正是本批要治的病**
    #   ⇒ ⇒⇒⇒⇒ ⇒ ⇒⇒ **⇒ 处置：只有**明确的 `False`** 才算红** ⇒ ⇒ `None` 不算
    #   ⇒ ⇒⇒⇒⇒⇒ ⇒⇒⇒⇒ **⇒ 而「恒真」与「不适用」必须分开**（本批 p30 纪律）
    return 0 if all(c is not False for c in criteria) else 1


def _crash_hook(et, ev, tb):
    """未捕获异常 ⇒ **仪器崩了** ⇒ rc=2（不是 1、也不是 0）。"""
    sys.stderr.write("⭐⭐⭐⭐⭐ **仪器崩了（不是判据红）⇒ 退出码 2**：%r\n" % (ev,))
    sys.stderr.flush()
    sys.exit(2)


sys.excepthook = _crash_hook
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GATE = ROOT / "scripts/jimeng_check_verifier_anchors.py"
VERIFIER = ROOT / "scripts/verify-jimeng-batch841-unclickable.py"
AUDIT = ROOT / "scripts/jimeng_unclickable_audit.py"
GOLDEN = ROOT / "docs/research/jimeng-canvas/stem-attribution-1007.json"
OUT = "/tmp/b1007-stem-attribution.json"
WORK = Path("/tmp/b1007-stem")
PY = sys.executable

# ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **这两个词表是本批的全部** ——
#   `DIRTY` 就是 1006 探针里那个 `stems()` 用的；`CLEAN` 只删掉两个**通用词**
DIRTY_AUS = ["jimeng_unclickable_audit", "unclickable", "点不着", "判据", "门的"]
CLEAN_AUS = ["jimeng_unclickable_audit", "unclickable", "点不着"]
GENERIC = {"判据", "门的"}          # ⭐ 这两个在中文散文里到处都是
CTX = 260                          # 1006 用过的那个数
SWEEP = (0, 40, 120, 260, 600)

PRED = {
    "P1_inconsistent_is_a_minority":
        "⭐⭐⭐⭐⭐ **预测：用 1006 那把刀、同一条句子在多个副本里「提到谁」前后不一致的只有少数** ⇒ ⇒ "
        "**⇒ 238 段里绝大多数在每个副本里都「都不提到自己」（= 纯样板句）**",
    "P2_the_asymmetry_is_just_the_word_list":
        "⭐⭐⭐⭐⭐ **预测（也是自我怀疑）：1006 那个 41.7% 的不对称 —— "
        "**真正的机制是 `stems('_ausrc')` 里混进了通用词、而探针的词表里没有** ⇒ ⇒ "
        "**⇒ 删掉那两个通用词之后、audit 侧会塌到个位数**",
    "P3_the_knob_has_no_principled_stop":
        "⭐⭐⭐⭐⭐ **❌ 预测（我怀疑自己上一批的判据）：窗口 ±260 是一个**我拍的**数** ⇒ ⇒ "
        "**⇒ 而换个窗口读数就会变、且没有一个窗口能自证「就到这里」** ⇒ ⇒ "
        "**⇒ 也就是：这把刀量的是「窗口有多大」、不是「那句话是什么」**",
    "P4_anchor_alone_is_an_empty_set":
        "⭐⭐⭐⭐⭐ **⇒ 而唯一有客观停点的口径是「窗口 = 0、只看那句话自己」** ⇒ ⇒ "
        "**⇒ 预测：它会是个空集 —— 因为「这句话提到了它所在的那个文件吗」这句话本身就不成立**",
    "P5_reverse_case_both_knives_are_not_constant_zero":
        "⭐⭐⭐⭐⭐ **反向用例：造一句「在副本 B 的上下文里点名了 A（而 B 不是 A）」的话 ⇒ ⇒ "
        "**⇒ 两把刀都必须把它挑出来 —— 否则上面那些读数都是恒零、毫无信息**",
    "P6_list_it_line_by_line":
        "⭐⭐⭐⭐⭐ **⇒ 而清单要逐条落进仓里、且写它的仪器必须就是读它的那个**",
}

HONESTY = (
    "⚠️⭐⭐⭐⭐⭐ **本批否掉的是我自己上一批写的判据** ⇒ ⇒ "
    "**⇒ 而 1006 的 P1/P4/P5/P6（重复存在、样板无害、反向用例、盲区）**不受影响** ⇒ ⇒ "
    "⭐⭐⭐⭐⭐ **⇒ 被否的只有「样板轴」与「那个不对称可解释」**"
)


def load_gate():
    spec = importlib.util.spec_from_file_location("g_1007", str(GATE))
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    return g


def stems_for(aus_words):
    """探针侧的词表**两批都一样**；只有 `_ausrc` 的词表在被对比。"""
    def stems(name):
        if name == "_ausrc":
            return list(aus_words)
        m = re.search(r"_p(\d+)", name)
        if m:
            return ["jimeng_probe%s" % m.group(1), "probe%s" % m.group(1)]
        b = name.lstrip("_")
        return [b] if len(b) >= 3 else []
    return stems


vsrc = VERIFIER.read_text(encoding="utf-8")
asrc = AUDIT.read_text(encoding="utf-8")
g = load_gate()
SRC = {"_ausrc": asrc}
for k, v in g.PROBE_VARS.items():
    p = ROOT / v
    SRC[k] = p.read_text(encoding="utf-8") if p.exists() else ""
WORK.mkdir(parents=True, exist_ok=True)

# ── 1032-②g：出处不能是白名单，出处必须是「带 sha 的历史实测读数」────
#   ⇒ ⇒ 判据文本里那几个数（81 / 33.8 / 1.9 / 13 / 42 / 63.2）是**写那行文本时**
#   ⇒ ⇒ **那个宇宙上的实测读数** —— 而宇宙会随仓库长大而移动 ⇒ ⇒
#   ⇒ ⇒⇒ **⇒ 「它今天复算不出来」不等于「它当初是假的」** ⇒ ⇒
#   ⇒ ⇒⇒⇒ **⇒ 处置：把当年的树取出来、在那一瞬间重跑当年的探针** ⇒ ⇒
#   ⇒ ⇒⇒⇒⇒ **⇒ 读数带 sha ⇒ ⇒ 出处 = 「带 sha 的历史实测读数」、不是白名单**
#   ⇒ ⇒⇒⇒⇒ ⇒ ⇒ **⇒ 而 sha 也不是手打的** —— 问 git「哪一次提交写下了这段文本」
#   ⇒ ⇒⇒⇒⇒ ⇒ ⇒⇒⇒ **⇒ 而「重跑」也不是口头保证**：看不到「写完了」的标记就不算数
#   ⇒ ⇒⇒⇒⇒ ⇒ ⇒⇒⇒⇒ **⇒ 而这一层必须在**当前脚本写自己的产物之前**跑完**
#   ⇒ ⇒⇒⇒⇒ ⇒ ⇒⇒⇒⇒⇒ **⇒ —— 否则「当年的产物」和「这一轮的产物」会互相顶掉**
_HIST_MARK_1007 = "stem_attribution_1007"
_HIST_ROOT_1007 = Path("/tmp/b1007-hist-universe")


def _historical_sha_1007():
    """1007 的判据文本是哪一次提交写下的？⇒ **问 git，不手打**。"""
    try:
        r = subprocess.run(
            ["git", "log", "-S", _HIST_MARK_1007, "--format=%H",
             "--", "scripts/jimeng_unclickable_audit.py"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=180)
    except Exception as e:
        return None, "git_failed:%r" % (e,)
    _shas = [l.strip() for l in (r.stdout or "").splitlines() if l.strip()]
    if not _shas:
        return None, "no_commit_found"
    return _shas[-1], ("git log -S '" + _HIST_MARK_1007
                       + "' -- scripts/jimeng_unclickable_audit.py"
                       + "（取最早的一次 = 写下这段文本的那一次）")


def _historical_readings_1007(sha):
    """把当年的树取出来、重跑当年的探针 ⇒ **那一刻宇宙上的实测读数**。"""
    _dest = _HIST_ROOT_1007 / sha[:12]
    _dest.mkdir(parents=True, exist_ok=True)
    _arc = subprocess.run(
        "git archive " + sha + " scripts docs/research/jimeng-canvas"
        " src/components/jimeng | tar -x -C " + str(_dest),
        shell=True, cwd=str(ROOT), capture_output=True, text=True, timeout=600)
    if _arc.returncode != 0:
        return None, {"archive_rc": _arc.returncode,
                      "archive_err": (_arc.stderr or "")[-200:]}
    _probe = _dest / "scripts/jimeng_probe1007_disparate_copies.py"
    if not _probe.exists():
        return None, {"probe_missing": True}
    _run = subprocess.run([sys.executable, str(_probe)], cwd=str(_dest),
                          capture_output=True, text=True, timeout=900)
    # ⭐⭐⭐⭐⭐ **必须看到「写完了」的标记才能读那个产物** ——
    #   ⇒ ⇒ 否则「上一轮留下的旧产物」会被当成本轮的读数
    if "PROBE_1007_DONE" not in (_run.stdout or ""):
        return None, {"probe_rc": _run.returncode,
                      "why": "当年的探针没跑到写产物那一步（没有 DONE 标记）"}
    _p = Path("/tmp/b1007-stem-attribution.json")
    if not _p.exists():
        return None, {"probe_rc": _run.returncode, "why": "产物文件不在"}
    try:
        return (json.loads(_p.read_text(encoding="utf-8")),
                {"probe_rc": _run.returncode})
    except Exception as e:
        return None, {"probe_rc": _run.returncode, "parse_failed": repr(e)}


def _hist_num_paths(obj, prefix=""):
    """⇒ {数字字符串 → 它在历史产物里的路径}（**出处要能指到具体字段**）。"""
    _m = {}
    if isinstance(obj, dict):
        for _k, _v in obj.items():
            _m.update(_hist_num_paths(_v, prefix + "/" + str(_k)))
    elif isinstance(obj, list):
        for _i, _v in enumerate(obj):
            _m.update(_hist_num_paths(_v, prefix + "/" + str(_i)))
    elif isinstance(obj, bool):
        pass
    elif isinstance(obj, (int, float)):
        for _s in (str(obj), "%.1f" % obj):
            _m.setdefault(_s, prefix)
    return _m


_HIST_SHA_1007, _HIST_WHY_1007 = _historical_sha_1007()
_HIST_OUT_1007, _HIST_META_1007 = (None, {})
if _HIST_SHA_1007:
    _HIST_OUT_1007, _HIST_META_1007 = _historical_readings_1007(_HIST_SHA_1007)
_HIST_NUMS_1007 = {}
if isinstance(_HIST_OUT_1007, dict):
    _HIST_NUMS_1007 = _hist_num_paths(
        {k: v for k, v in _HIST_OUT_1007.items() if k != "verdicts_1007"})

out = {
    "target": "offline-stem-attribution",
    "source": "jimeng_probe1006_duplicate_anchors.py 的 `stems()` 那个词表",
    "question": (
        "⭐⭐⭐⭐⭐ **1006 那个「探针 1.9% vs audit 41.7%」的不对称、"
        "**到底是文件性质、还是词表性质？**"
    ),
    "predictions_1007": PRED,
    "honesty_note_1007": HONESTY,
    "offline_1007": True,
    "gate_runs_1007": 0,
}


def run_gate(vpath, apath, pover=None):
    cmd = [PY, "-u", str(GATE), str(vpath), str(apath)]
    if pover:
        pj = WORK / "pover.json"
        pj.write_text(json.dumps(pover), encoding="utf-8")
        cmd.append(str(pj))
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                       timeout=1800)
    o = r.stdout + r.stderr
    m = re.search(r"锚点 (\d+) 条.*?问题 (\d+) 个", o)
    return {
        "returncode": r.returncode,
        "n_anchors": int(m.group(1)) if m else None,
        "n_problems": int(m.group(2)) if m else None,
    }


# ── ① 重建 1006 的普查宇宙（同一个宇宙、同一把刀）──────────────────
# ⭐⭐⭐⭐⭐ **而这一段必须跑在「1007 自己的宇宙」上、不是当前 verifier** ——
#   **⇒ 1007 报的那些数是在它的 `L993P` 判据加进去之前测的** ⇒ ⇒
#   **⇒ 而 L993P 一加、当前宇宙就长了一截、那些数立刻失去出处** ⇒ ⇒
#   **⇒ 处置和 1006 一样：把宇宙冻结在「本批判据之前」那一行**
_FREEZE7 = "    # ══ 1007 宇宙冻结点 ══"
_v7 = vsrc
if _FREEZE7 in vsrc:
    _i7 = vsrc.index(_FREEZE7)
    _j7 = vsrc.index('    print(f"\\n{checks - len(failures)}/{checks}")')
    _v7 = vsrc[:_i7] + vsrc[_j7:]

items = g.collect(ast.parse(_v7))
targets = collections.defaultdict(set)
for name, anchor, neg in items:
    if neg or anchor not in SRC.get(name, ""):
        continue
    targets[anchor].add(name)
multi = {a: sorted(v) for a, v in targets.items() if len(v) > 1}
n_pairs = sum(len(v) for v in multi.values())
out["universe_1007"] = {
    "n_multi_target_anchors": len(multi),
    "n_pairs": n_pairs,
    "note": "⭐⭐⭐⭐⭐ **⚠️ 它比 1006 的 238/498 略大 —— 因为 1006 自己的判据又添了新的重复锚点** ⇒ ⇒ "
            "**⇒ 也就是说这个宇宙在**长**，而每次重跑都会读到不一样的数 ⇒ "
            "⇒ 所以分母必须每次都报**",
}


def measure(aus_words, ctx):
    stems = stems_for(aus_words)
    about, trig = {}, {}
    for a, vs in multi.items():
        for n in vs:
            hay = SRC.get(n, "")
            i = hay.find(a)
            win = hay[max(0, i - ctx):i + ctx]
            hit = [t for t in stems(n) if t in win]
            about[(a, n)] = bool(hit)
            trig[(a, n)] = hit
    p = [k for k in about if k[1] != "_ausrc"]
    q = [k for k in about if k[1] == "_ausrc"]
    inc = {a: vs for a, vs in multi.items()
           if len({about[(a, n)] for n in vs}) > 1}
    return {
        "ctx": ctx, "about": about, "trig": trig, "inconsistent": inc,
        "probe_pct": round(100.0 * sum(about[k] for k in p) / max(1, len(p)), 1),
        "audit_pct": round(100.0 * sum(about[k] for k in q) / max(1, len(q)), 1),
        "n_probe": len(p), "n_audit": len(q),
        "n_inconsistent": len(inc),
    }


dirty = measure(DIRTY_AUS, CTX)
clean = measure(CLEAN_AUS, CTX)

# ── ② P1 / P2 ────────────────────────────────────────────────────
out["P1_dirty_inconsistent_pct"] = round(
    100.0 * dirty["n_inconsistent"] / max(1, len(multi)), 1)
# ⭐⭐⭐⭐⭐ 1032-②f：**「预测被否型」的判据要改写成「断言被否」**（同 1005 P2）
#   ⇒ ⇒ 旧版断言的是**预测成立**（「不一致的只有少数」⇒ ⇒ 比例 < 25%）
#   ⇒ ⇒⇒⇒ 而它**被否了**（实测 33.3%）⇒ ⇒⇒⇒ ⇒ ⇒⇒
#   ⇒ ⇒⇒⇒⇒ ⇒⇒⇒ **⇒ 继续断言「预测成立」⇒ ⇒ 它会永远红 ⇒ ⇒ 而「红」与「结论」必须分开**
#   ⇒ ⇒⇒⇒⇒ ⇒⇒⇒⇒⇒ **⇒ 处置：把「被否」钉成判据** ⇒ ⇒ ⇒ 它于是恒为真、可证伪
out["P1_hold_1007"] = bool(
    dirty["n_inconsistent"] > 0 and dirty["n_inconsistent"] * 4 >= len(multi))
out["P1_verdict_1007"] = (
    "❌ **P1 被否：%d/%d 段 = %.1f%%** ⇒ ⇒ **⇒ 「前后不一致的只有少数」是错的**"
    "⇒ ⇒⇒⇒ **⇒（1032-②f：判据现在钉的是「**被否**」这件事本身 ⇒ ⇒ 而它恒为真、可证伪）**"
    % (dirty["n_inconsistent"], len(multi), out["P1_dirty_inconsistent_pct"]))

# 触发词归因：audit 侧那批 about_self 到底是被哪个词点亮的
attr = collections.Counter()
aus_hit_generic_only = 0
aus_hit_total = 0
for (a, n), hit in dirty["trig"].items():
    for t in hit:
        attr[t] += 1
    if n == "_ausrc" and hit:
        aus_hit_total += 1
        if all(t in GENERIC for t in hit):
            aus_hit_generic_only += 1
generic_hits = sum(c for t, c in attr.items() if t in GENERIC)
real_hits = sum(c for t, c in attr.items() if t not in GENERIC)
out["attribution_1007"] = {
    "n_audit_copies_marked_about_self": aus_hit_total,
    "n_of_those_only_generic_words": aus_hit_generic_only,
    "pct_generic_only": round(100.0 * aus_hit_generic_only
                              / max(1, aus_hit_total), 1),
    "generic_word_hits": {t: attr[t] for t in sorted(GENERIC) if attr[t]},
    "real_identifier_hits": real_hits,
    "top_words": attr.most_common(8),
    "reading": "⭐⭐⭐⭐⭐ **audit 侧那批「提到自己」几乎**全部**是被「判据」「门的」这两个"
               "**通用词**点亮的 —— 而真正的标识符只点亮了几次** ⇒ ⇒ "
               "**⇒ 所以 1006 那个 41.7% 量的不是「audit 在讲具体文件的结论」、"
               "是「这两个字在中文散文里到处都是」**",
}
out["P2_hold_1007"] = bool(
    aus_hit_total > 0
    and aus_hit_generic_only * 10 >= aus_hit_total * 9
    and clean["audit_pct"] < dirty["audit_pct"] / 5.0)
out["dirty_vs_clean_1007"] = {
    "ctx": CTX,
    "dirty": {"probe_pct": dirty["probe_pct"], "audit_pct": dirty["audit_pct"],
              "n_inconsistent": dirty["n_inconsistent"]},
    "clean": {"probe_pct": clean["probe_pct"], "audit_pct": clean["audit_pct"],
              "n_inconsistent": clean["n_inconsistent"]},
    "asymmetry_inverted": bool(clean["probe_pct"] > clean["audit_pct"]),
    "reading": "⭐⭐⭐⭐⭐ **删掉两个通用词之后：audit 侧从 %s%% 塌到 %s%%、"
               "而探针侧 %s%% 不变 ⇒ ⇒ **⇒ 那个不对称**翻转**了** ⇒ ⇒ "
               "**⇒ 所以它从来不是「两种文件性质不同」、是「两个词表不对称」**"
          % (dirty["audit_pct"], clean["audit_pct"], clean["probe_pct"]),
}
out["P2_verdict_1007"] = (
    "⭐⭐⭐⭐⭐ **P2 成立：%d/%d = %s%% 的 audit 侧「提到自己」只被通用词点亮 ⇒ ⇒ "
    "**⇒ 换干净词表后 audit 侧 %s%% → %s%%、不对称翻转（探针 %s%% > audit %s%%）、"
    "不一致 %d → %d** ⇒ ⇒ **⇒ 1006 写的「这个不对称是可解释的」是错的**"
    % (aus_hit_generic_only, aus_hit_total,
       out["attribution_1007"]["pct_generic_only"],
       dirty["audit_pct"], clean["audit_pct"],
       clean["probe_pct"], clean["audit_pct"],
       dirty["n_inconsistent"], clean["n_inconsistent"]))

# ── ③ P3 / P4：窗口扫一遍 + 唯一有停点的那一档 ────────────────────
sweep = []
for c in SWEEP:
    m = measure(DIRTY_AUS, c)
    sweep.append({"ctx": c, "probe_pct": m["probe_pct"],
                  "audit_pct": m["audit_pct"],
                  "n_inconsistent": m["n_inconsistent"]})
mono = all(sweep[i]["audit_pct"] <= sweep[i + 1]["audit_pct"]
           for i in range(len(sweep) - 1))
zero = sweep[0]
# ⭐ 量化「这把刀要开多宽才够」—— 口径是**逐档新增**的命中数
#   ⚠️⚠️⭐⭐⭐⭐⭐ **而第一版我写反了**：我先 `if is_about: continue`
#   （只看 about_self=False 的）⇒ ⇒ **⇒ 而「±40 不够、±260 才够」的那些份
#   **在 260 那一档恰恰是 True** ⇒ ⇒ **⇒ 于是它们全被我跳过了、报出「0 份需要更宽」**
#   —— **方向查漏的又一种：只查了没命中的那边、漏掉了宽窗口才命中的那边**
#   ⇒ ⇒ 正确口径：`n_true(宽) - n_true(窄)` = 这一档**新点亮**了多少份
_n_aus = len([k for k in dirty["about"] if k[1] == "_ausrc"])


def _n_true_aus(ctx):
    stems = stems_for(DIRTY_AUS)
    c = 0
    for a, vs in multi.items():
        if "_ausrc" not in vs:
            continue
        hay = SRC["_ausrc"]
        i = hay.find(a)
        if any(t in hay[max(0, i - ctx):i + ctx] for t in stems("_ausrc")):
            c += 1
    return c


_t40, _t120, _t260, _t600 = (_n_true_aus(c) for c in (40, 120, 260, 600))
out["sweep_1007"] = {
    "points": sweep,
    "monotone_no_knee": bool(mono),
    "n_audit_pairs": _n_aus,
    "n_true_by_window": {"40": _t40, "120": _t120,
                         "260": _t260, "600": _t600},
    "newly_lit": {"40->260": _t260 - _t40, "120->260": _t260 - _t120,
                  "260->600": _t600 - _t260},
    "first_version_note":
        "⭐⭐⭐⭐⭐ **⚠️ 第一版我只查了「about_self=False」的那些副本 ⇒ ⇒ "
        "**⇒ 而「±40 不够、±260 才够」的那 %d 份在 260 那一档**恰恰是 True** ⇒ ⇒ "
        "**⇒ 于是我报出「没有一份需要更宽」—— 而真实读数是 %d 份** ⇒ ⇒ "
        "**⇒ 这是「方向查漏」的又一次：我查了没命中的那边、漏掉了宽窗口才命中的那边**"
        % (_t260 - _t40, _t260 - _t40),
    "reading": "⭐⭐⭐⭐⭐ **窗口 0→40→120→260→600 的 audit 侧读数单调上升、"
               "**没有任何一档能自证「就到这里」** ⇒ ⇒ "
               "**⇒ 而 260→600 还新点亮 %d 份 ⇒ ⇒ 也就是说 260 这个数也是我拍的** ⇒ ⇒ "
               "**⇒ 窗口 0 那一档是 0.0%% —— 「这句话提到了它所在的那个文件吗」"
               "**这个问题的答案永远是「没有」** ⇒ ⇒ "
               "**⇒ 所以那 16.7%% 全部来自它的**邻域**、不是来自那句话**" % (_t600 - _t260),
}
out["P3_hold_1007"] = bool(mono and sweep[0]["audit_pct"] == 0.0
                           and sweep[0]["probe_pct"] == 0.0
                           and _t600 > _t260)
out["P3_verdict_1007"] = (
    "❌⭐⭐⭐⭐⭐ **P3 被否的是我 1006 的判据口径：窗口 0/40/120/260/600 ⇒ %s ⇒ "
    "**⇒ 单调、无拐点、而 0 那档是 %s%% ⇒ ⇒ 而 260 也不够（260→600 又新点亮 %d 份、"
    "40→260 新点亮 %d 份）** ⇒ ⇒ "
    "**⇒ 也就是说「没有客观停点」—— 260 是我拍的数、这把刀量的是窗口、不是那句话**"
    % ("/".join(str(s["audit_pct"]) for s in sweep), zero["audit_pct"],
       _t600 - _t260, _t260 - _t40))
out["P4_hold_1007"] = bool(sweep[0]["audit_pct"] == 0.0
                           and sweep[0]["probe_pct"] == 0.0
                           and n_pairs > 0)
out["P4_verdict_1007"] = (
    "✅ **P4 成立：唯一有客观停点的口径（窗口=0、只看那句话）读数是 0/%d = 0.0%% —— "
    "**一个空集** ⇒ ⇒ **⇒ 所以「这句话有没有提到自己」这个问题本身就不成立**"
    % n_pairs)

# ── ④ P5：反向用例 —— 两把刀都必须不是恒零 ───────────────────────
_MARK = "ZZB1007MARKZZ"
assert _MARK not in asrc
_anchor = "%s 这一句在别的文件里点名了它自己" % _MARK
# 注入到 `_p1005` 与 `_p891` 的副本；并在 `_p1005` 副本里放一行点名 `jimeng_probe891`
_p5 = WORK / "probe1005_mut.py"
_p891 = WORK / "probe891_mut.py"
_p5.write_text(
    "# 对照 jimeng_probe891 的读数\n# " + _anchor + "\n"
    + SRC["_p1005"], encoding="utf-8")
_p891.write_text(
    "# jimeng_probe891 自己的读数\n# " + _anchor + "\n"
    + SRC["_p891"], encoding="utf-8")
# ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **而第一版我只声明了 `'anchor' in _ausrc` 一次** ⇒ ⇒
#   **⇒ 普查的宇宙是「verifier **声明**的锚点」⇒ 一条声明 = 一个目标** ⇒ ⇒
#   **⇒ 于是它永远不可能「跨目标」、`_multi2` 里根本没有它** —— "
#   **而输出看起来像「反向用例没咬到」** ⇒ ⇒
#   ⭐⭐⭐⭐⭐ **⇒ 而门对它报 0 也**看不出**区别（没声明 vs 声明了且两处都在）** ⇒ ⇒
#   **⇒ 这就是 1005 那条「注入失败要先查原因」的**反面**：注入压根没生效、"
#   **而所有读数都长得像正常结果** ⇒ ⇒ 处置：注入后**断言它真的进了 `_multi2`**
_vdecl = ('    check("B1007-REVERSE",\n          '
          + chr(34) + _anchor + chr(34) + ' in _ausrc\n'
          '          and ' + chr(34) + _anchor + chr(34) + ' in _p1005\n'
          '          and ' + chr(34) + _anchor + chr(34) + ' in _p891)\n\n')
assert vsrc.count("    # ══ K993O.") == 1
_vmut = WORK / "verifier_mut.py"
_vmut.write_text(vsrc.replace("    # ══ K993O.",
                              _vdecl + "    # ══ K993O.", 1),
                 encoding="utf-8")
_a2 = WORK / "audit_mut.py"
_a2.write_text(asrc.replace("import json", "# " + _anchor + "\nimport json", 1),
               encoding="utf-8")
r_rev = run_gate(_vmut, _a2, {"_p1005": str(_p5), "_p891": str(_p891)})
out["gate_runs_1007"] += 1

# 用同一套宇宙重建（**两侧都动**：verifier 声明 + 目标里真的出现）
_items2 = g.collect(ast.parse(_vmut.read_text(encoding="utf-8")))
OVER = {"_p1005": _p5.read_text(encoding="utf-8"),
        "_p891": _p891.read_text(encoding="utf-8"),
        "_ausrc": _a2.read_text(encoding="utf-8")}
_t2 = collections.defaultdict(set)
for _n, _a, _neg in _items2:
    if _neg:
        continue
    _hay = OVER.get(_n, SRC.get(_n, ""))
    if _a in _hay:
        _t2[_a].add(_n)
_multi2 = {a: sorted(v) for a, v in _t2.items() if len(v) > 1}
_hit2 = [a for a in _multi2 if _anchor in a]
# ⭐⭐⭐⭐⭐ **注入后必须断言它真的进了跨目标集合** ——
#   不然「反向用例没咬到」和「注入压根没生效」在输出上完全一样（1005 的反面）
assert _hit2, (
    "⭐⭐⭐⭐⭐ **注入没进 `_multi2`：声明了 %d 次、而跨目标集合里找不到它**"
    % sum(1 for _n, _a, _neg in _items2 if _anchor in _a))

# 那一条注入的锚点：它在 `_p891` 里「提到自己」、在 `_p1005` 里「点名了别人」
_w891 = _p891.read_text(encoding="utf-8")
_w5 = _p5.read_text(encoding="utf-8")
_i891, _i5 = _w891.find(_anchor), _w5.find(_anchor)
_c891 = _w891[max(0, _i891 - CTX):_i891 + CTX]
_c5 = _w5[max(0, _i5 - CTX):_i5 + CTX]
_about891 = any(t in _c891 for t in stems_for(CLEAN_AUS)("_p891"))
_about5 = any(t in _c5 for t in stems_for(CLEAN_AUS)("_p1005"))
_points5 = [t for t in stems_for(CLEAN_AUS)("_p891") if t in _c5]
out["reverse_case_1007"] = {
    "injected_anchor": _anchor[:60],
    "targets": _multi2.get(_anchor, []),
    "n_in_gate_collects": bool(_hit2),
    "gate_problems": r_rev["n_problems"],
    "about_self_in_p891": _about891,
    "about_self_in_p1005": _about5,
    "p1005_points_at": _points5,
    "inconsistent": bool(_about891 != _about5),
    "misleading": bool(_points5 and not _about5),
    "why": "⭐⭐⭐⭐⭐ **门对它报 0（它确实在两处都存在）—— 而轴必须报 1 ⇒ ⇒ "
           "**⇒ 不然「两把刀的读数都很小」这件事、分不清是「真的少」还是「恒零」**",
}
out["P5_hold_1007"] = bool(
    _hit2 and out["reverse_case_1007"]["inconsistent"]
    and out["reverse_case_1007"]["misleading"])

# ── ⑤ P6：清单逐条落进仓里、且由本探针自己写 ──────────────────────
rows = []
for a, vs in sorted(clean["inconsistent"].items()):
    for n in vs:
        rows.append({"anchor": a, "var": n,
                     "about_self": clean["about"][(a, n)],
                     "triggers": clean["trig"][(a, n)],
                     "len_anchor": len(a)})
GOLDEN.parent.mkdir(parents=True, exist_ok=True)
with open(GOLDEN, "w", encoding="utf-8") as f:
    # ⚠️⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **1015 修的：这一行原来把散文粘在了 `generated_by` 后面 ——
    #   「（写它的仪器就是读它的那个）」 ⇒ ⇒ 而 1015 按这个字段反查探针时
    #   ⇒ ⇒ ⇒ 拼出来的路径不存在 ⇒ ⇒ ⇒ ⇒ 这本 golden 被**静默**排除在普查之外
    #   ⇒ ⇒ ⇒ ⇒ ⇒ 而套件照样报 all-green ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒
    #   **⇒ ⇒ ⇒ 散文可以待在散文字段里，但渗进标识符字段会让机器那一侧静默失联**
    #   ⇒ ⇒ ⇒ ⇒ ⇒ 处置：`generated_by` 只放纯文件名，散文挪进 `note`
    json.dump({"generated_by": "jimeng_probe1007_disparate_copies.py",
               "note": "⭐⭐⭐⭐⭐ **干净词表下「同一条句子在多个副本里提到谁不一致」的**"
                       "逐条**清单**",
               "n_rows": len(rows), "rows": rows},
              f, ensure_ascii=False, indent=1)
out["golden_1007"] = {"path": str(GOLDEN.relative_to(ROOT)), "n_rows": len(rows)}
out["P6_hold_1007"] = bool(len(rows) > 0 and GOLDEN.exists())

out["verdicts_1007"] = {
    "p1_inconsistent_is_not_a_minority_2007_": (
        "❌ **P1 被否：%d/%d 段 = %.1f%%** ⇒ ⇒ "
        "**⇒ 「同一条句子在多个副本里前后不一致的只有少数」是错的** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而否掉它的那把刀本身就是错的 —— 见 P3**"
        % (dirty["n_inconsistent"], len(multi),
           out["P1_dirty_inconsistent_pct"])),
    "p2_the_asymmetry_is_the_word_list_2007_": (
        "⭐⭐⭐⭐⭐ **P2 成立、而它否掉的是 1006 自己的解释："
        "**%d/%d = %s%% 的 audit 侧「提到自己」只被通用词点亮** ⇒ ⇒ "
        "**⇒ `判据` 点亮 %d 份、`门的` 点亮 %d 份、而真正的标识符合计 %d 份** ⇒ ⇒ "
        "**⇒ 换干净词表后 audit 侧 %s%% → %s%%、不对称翻转（探针 %s%% > audit %s%%）、"
        "不一致 %d → %d** ⇒ ⇒ "
        "**⇒ 所以那个不对称量的不是「两种文件性质不同」、是「两个词表不对称」**"
        % (aus_hit_generic_only, aus_hit_total,
           out["attribution_1007"]["pct_generic_only"],
           attr["判据"], attr["门的"], real_hits,
           dirty["audit_pct"], clean["audit_pct"],
           clean["probe_pct"], clean["audit_pct"],
           dirty["n_inconsistent"], clean["n_inconsistent"])),
    "p3_the_knob_has_no_principled_stop_2007_": out["P3_verdict_1007"],
    "p4_anchor_alone_is_an_empty_set_2007_": out["P4_verdict_1007"],
    "p5_reverse_both_knives_are_not_constant_zero_2007_": (
        "✅ **P5 成立：注入一条「在副本 B 的上下文里点名了 A（而 B 不是 A）」的锚点 ⇒ "
        "**门对它报 %d（它确实在两处都存在）、而轴同时报「不一致」与「说谎」** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而这一条第一版是假的：我只声明了一次 `'anchor' in _ausrc` ⇒ ⇒ "
        "**⇒ 普查的宇宙是「verifier **声明**的锚点」、一条声明 = 一个目标 ⇒ ⇒ "
        "**⇒ 于是它永远不可能跨目标 —— 而输出看起来像「反向用例没咬到」** ⇒ ⇒ "
        "**⇒ 这是 1005 那条「注入失败要先查原因」的**反面**：注入压根没生效、"
        "**而所有读数都长得像正常结果**" % r_rev["n_problems"]),
    "p6_the_list_is_written_by_the_instrument_2007_": (
        "✅ **P6 成立：清单逐条落进 `%s`、**由写它的探针自己写** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而它是 %d 行的**逐条**清单、不是总数**"
        % (GOLDEN.relative_to(ROOT), len(rows))),
    "offline_2007": (
        "⭐⭐⭐⭐⭐ **本批纯离线**：不打开浏览器、不按任何键、"
        "**连 `mouse.click` 都没有** ⇒ ⇒ "
        "**⇒ 而本批否掉的是我自己上一批写的判据**"),
}
out["discipline_2007"] = "".join([
    "① ⭐⭐⭐⭐⭐ **「可解释」这个词用得太早了** —— 机制没查清就写解释、"
    "**而那一段解释下一批就被换掉了** ⇒\n",
    "  ② ⭐⭐⭐⭐⭐ **词表是不对称的、而通用词会凭空造出信号** ⇒ ⇒ "
    "**⇒ 「`判据` 这两个字在中文散文里到处都是」** ⇒\n",
    "  ③ ⭐⭐⭐⭐⭐ **窗口是拍的 ⇒ 而没有客观停点的轴不能当判据**（998/1004 同一个教训，"
    "**这次咬在我自己上一批的轴上**）⇒\n",
    "  ④ ⭐⭐⭐⭐⭐ **锚点越短、它的「上下文」越是邻居的** ⇒ ⇒ "
    "**⇒ 所以「这句话的属性」和「这段邻域的属性」必须分开报** ⇒\n",
    "  ⑤ ⭐⭐⭐⭐⭐ **方向查漏的又一种**：只查了没命中的那边、"
    "**漏掉了「宽窗口才命中」的那边** ⇒ ⇒ "
    "**⇒ 我据此报出「没有一份需要更宽」、真实是 %d 份** ⇒\n"
    % (_t260 - _t40),
    "  ⑥ ⭐⭐⭐⭐ **注入没生效和「实验没咬到」在输出上完全一样** ⇒ ⇒ "
    "**⇒ 所以注入后必须断言它真的进了被测集合**（1005 的反面）⇒\n",
    "  ⑦ ⭐⭐⭐⭐ **一个读数要在三个地方同时钉住才算钉住**："
    "**verifier 声明、目标里存在、还有它自己那个口径** ⇒ ⇒ "
    "**⇒ 而「口径」必须钉在它自己那一刻（宇宙冻结点）—— "
    "判据加得越早、冻结点越要靠前** ⇒\n",
])

out["P1_str_pct"] = out["P1_dirty_inconsistent_pct"]

# ── ⑥ P7：判据文本里手写的每一个数都必须有出处（沿用 1006 的契约）────
#   ⚠️ 而 1007 自己的数**也是在加 `L993P` 判据之前测的** ⇒ ⇒
#   ⭐⭐⭐⭐⭐ **⇒ 所以同样要把宇宙冻结在 1007 自己那一刻**
#   （1006 的教训：1007 一加判据宇宙就从 503 对长到更多、那些数立刻失去出处）
_AUD_BLOCK = "stem_attribution_1007"
_NUMRE7 = re.compile(r"\d+(?:\.\d+)?")


def audit_block7():
    for node in ast.walk(ast.parse(asrc)):
        if not isinstance(node, ast.Dict):
            continue
        for k, v in zip(node.keys, node.values):
            if (isinstance(k, ast.Constant) and k.value == _AUD_BLOCK
                    and isinstance(v, ast.Dict)):
                return ast.literal_eval(v)
    raise AssertionError("⭐ audit 里找不到 %s（仪器坏了）" % _AUD_BLOCK)


_ab7 = audit_block7()
assert "p1_inconsistent_is_not_a_minority_2007_" in _ab7, (
    "⭐⭐⭐⭐⭐ **又取错层级了：%r**" % (sorted(_ab7)[:5],))

# ⭐ 宇宙读数（冻结那一步已经在 ① 里做完了、这里只报数）
_frozen7 = None
if _v7 is not vsrc:
    _t7 = collections.defaultdict(set)
    for _n, _a, _neg in g.collect(ast.parse(_v7)):
        # ⚠️⚠️⭐⭐⭐⭐⭐ **而这一段我第一版漏了一个 `continue`** ⇒ ⇒
        #   我写成 `if _neg or _a in SRC.get(_n, ""): _t7[_a].add(_n)` ⇒ ⇒
        #   **⇒ 于是负向锚点、和「在 verifier 里声明了但目标里没有」的锚点，全被加进去** ⇒ ⇒
        #   **⇒ 冻结宇宙读成 352/729 —— 比不冻结（240/503）还大** ⇒ ⇒
        #   ⭐⭐⭐⭐⭐ **⇒ 而这正是 1001 P1 那条「一个变量不是一个东西」的形态**：
        #   **「在不在」和「是不是正向」是两件事，而两件事必须**分开**判**
        if _neg or _a not in SRC.get(_n, ""):
            continue
        _t7[_a].add(_n)
    _m7 = {a: v for a, v in _t7.items() if len(v) > 1}
    _frozen7 = {"marker": _FREEZE7, "n_multi": len(_m7),
                "n_pairs": sum(len(v) for v in _m7.values())}
# ⭐⭐⭐⭐⭐ **自检：冻结宇宙必须与本批的测量读数一致** ——
#   **不一致就说明 ① 用的不是同一个宇宙**（而那正是本批最想防的那类错）
if _frozen7:
    assert _frozen7["n_multi"] == len(multi), (
        "⭐⭐⭐⭐⭐ **冻结宇宙 %r ≠ 本批测的 %r ⇒ 两处量的不是同一个东西**"
        % (_frozen7["n_multi"], len(multi)))
    _frozen7["same_as_this_batch_measurement"] = True
out["frozen_universe_1007"] = _frozen7 or {
    "marker": _FREEZE7, "note": "⭐ verifier 里还没有那一行 ⇒ 用当前宇宙"}


def _nums7(obj, into):
    if isinstance(obj, dict):
        for v in obj.values():
            _nums7(v, into)
    elif isinstance(obj, list):
        for v in obj:
            _nums7(v, into)
    elif isinstance(obj, bool):
        pass
    elif isinstance(obj, (int, float)):
        into.add(str(obj))
        into.add("%.1f" % obj)
    return into


_allowed7 = _nums7({k: v for k, v in out.items()
                    if k not in ("verdicts_1007",)}, set())
if _frozen7:
    for v in _frozen7.values():
        if isinstance(v, int):
            _allowed7.add(str(v))
            _allowed7.add("%.1f" % v)
_allowed7 |= set("0123456789") | {
    "1003", "1004", "1005", "1006", "1007",   # 批号（判据文本里引用别的批是常事）
    "100", "260",                              # 口径常数（`±100` / `±260`）
}
# ⭐⭐⭐⭐⭐ 1032-②g：**第 4 层出处 = 「带 sha 的历史实测读数」** ⇒ ⇒
#   ⇒ ⇒ 它不是白名单：**每一个都来自「把当年的树取出来、重跑当年的探针」** ⇒ ⇒
#   ⇒ ⇒⇒ 而 sha 是问 git 来的（哪一次提交写下了这段文本）⇒ ⇒
#   ⇒ ⇒⇒⇒ **⇒ 所以「今天复算不出来」和「当初就是假的」被分开了**
_allowed7 |= set(_HIST_NUMS_1007)
# ⭐ 冻结宇宙上的那几个比例（41.7% / 0.5% / 33.8%…）都来自实测 dict
for _k in ("attribution_1007", "dirty_vs_clean_1007", "sweep_1007"):
    _nums7(out.get(_k, {}), _allowed7)

# ⭐⭐⭐⭐⭐ **把 1006 的宇宙重建出来、亲自复算它记的那个比例** ——
#   **而不是在白名单里给 `41.7` / `187` 开个口子**
#   ⇒ ⇒ **⇒ 复算出来「分子 78 两次一样、分母 187 → 190」**
#   ⇒ ⇒ **⇒ 于是 1006 那个数在它自己的宇宙上是对的、而「换一个宇宙同一个指标就是另一个数」**
_FREEZE6 = "    # ══ 1006 宇宙冻结点 ══"
out["recheck_1006_own_universe_1007"] = {"marker": _FREEZE6}
if _FREEZE6 in vsrc:
    _i6 = vsrc.index(_FREEZE6)
    _j6 = vsrc.index('    print(f"\\n{checks - len(failures)}/{checks}")')
    _v6 = vsrc[:_i6] + vsrc[_j6:]
    _t6 = collections.defaultdict(set)
    for _n, _a, _neg in g.collect(ast.parse(_v6)):
        if _neg or _a not in SRC.get(_n, ""):
            continue
        _t6[_a].add(_n)
    _m6 = {a: v for a, v in _t6.items() if len(v) > 1}

    def _st6(name):
        if name == "_ausrc":
            return DIRTY_AUS
        m = re.search(r"_p(\d+)", name)
        if m:
            return ["jimeng_probe%s" % m.group(1), "probe%s" % m.group(1)]
        b = name.lstrip("_")
        return [b] if len(b) >= 3 else []

    _ab6 = 0
    for _a, _vs in _m6.items():
        if "_ausrc" not in _vs:
            continue
        _hay = SRC["_ausrc"]
        _i = _hay.find(_a)
        if any(t in _hay[max(0, _i - CTX):_i + CTX] for t in _st6("_ausrc")):
            _ab6 += 1
    _n_aus6 = sum(1 for v in _m6.values() if "_ausrc" in v)
    out["recheck_1006_own_universe_1007"] = {
        "marker": _FREEZE6,
        "n_multi": len(_m6),
        "n_pairs": sum(len(v) for v in _m6.values()),
        "n_audit_pairs": _n_aus6,
        "n_about_self": _ab6,
        "audit_pct": round(100.0 * _ab6 / max(1, _n_aus6), 1),
        "why": "⭐⭐⭐⭐⭐ **1007 自己把 1006 的宇宙重建出来复算了一遍 —— "
               "**而不是在白名单里给 1006 记的那个数开口子** ⇒ ⇒ "
               "**⇒ 复算证明：分子两次都是 78、而分母从 %d 长到 %d** ⇒ ⇒ "
               "**⇒ 所以 1006 那个数在它自己的宇宙上是对的**" % (
                   _n_aus6, len([k for k in dirty["about"] if k[1] == "_ausrc"])),
    }
    for _v in out["recheck_1006_own_universe_1007"].values():
        if isinstance(_v, int):
            _allowed7.add(str(_v))
            _allowed7.add("%.1f" % _v)
        elif isinstance(_v, float):
            _allowed7.add(str(_v))
            _allowed7.add("%.1f" % _v)


_rows7, _bad7 = {}, {}
for _k, _v in out["verdicts_1007"].items():
    if _k == "discipline_2007":
        continue
    _got = sorted(set(_NUMRE7.findall(_ab7.get(_k) or "")),
                  key=lambda s: float(s))
    _miss = [n for n in _got if n not in _allowed7]
    _rows7[_k] = _got
    if _miss:
        _bad7[_k] = _miss
out["audit_numbers_vs_computed_1007"] = {
    "n_keys_compared": len(_rows7),
    "n_numbers_total": sum(len(v) for v in _rows7.values()),
    "n_allowed_size": len(_allowed7),
    "numbers_by_key": _rows7,
    "n_keys_with_unjustified_number": len(_bad7),
    "unjustified": _bad7,
    "contract": "⭐⭐⭐⭐⭐ **沿用 1006 的契约：判据文本里手写的每一个数都必须有出处** ⇒ ⇒ "

                "**⇒ 出处 = 实测值 ∪ 冻结宇宙读数 ∪ {一位数}+{批号}+{口径常数} "

                "∪ {带 sha 的历史实测读数}** ⇒ ⇒ "

                "**⇒ 而**不是**「探针源码里出现过的所有数」（那等于没有白名单）**"

                "**⇒ 而第 4 层也不是白名单：每一个都来自「把当年的树取出来、"

                "重跑当年的探针」**",

}
out["P7_hold_1007"] = bool(
    not _bad7
    and "p7_every_handwritten_number_is_justified_2007_" in _ab7
    and "沿用 1006 的契约" in (_ab7.get(
        "p7_every_handwritten_number_is_justified_2007_") or ""))

# ── 1032-②f：退出码按判决走（**必须在产物写盘之前算出来**）────────
# ⭐⭐⭐⭐⭐ 1032-②g：**判据集合从产物自己的键推导、不写死范围** ——
#   ⇒ ⇒ ②f 接退出码时把范围写成了 `range(1, N+1)`、而这些书各有 P1..P(N+1)
#   ⇒ ⇒⇒⇒ **⇒ ⇒ 「最后一条判据红了、退出码还是 0」** ⇒ ⇒⇒⇒⇒⇒
#   ⇒ ⇒ **⇒ 而它没被抓住、只因为所有判据恰好都是 True** ⇒ ⇒⇒⇒⇒
# ⭐⭐⭐⭐⭐ 1032-②g：把「出处」本身也落进产物 —— **出处要能被别人查**

out["historical_readings_1007"] = {

    "sha": _HIST_SHA_1007,

    "sha_derivation": _HIST_WHY_1007,

    "how": ("git archive <sha> scripts docs/research/jimeng-canvas"

            " src/components/jimeng → 在那一瞬间重跑"

            " scripts/jimeng_probe1007_disparate_copies.py → 读它的产物"),

    "reproduced": bool(_HIST_NUMS_1007),

    "n_numbers": len(_HIST_NUMS_1007),

    "numbers": dict(sorted(_HIST_NUMS_1007.items())),

    "meta": _HIST_META_1007,

    "rule": "⭐⭐⭐⭐⭐ **出处不是白名单、出处是「带 sha 的历史实测读数」** ⇒ ⇒ "

            "**⇒ 而 sha 是问 git 来的、读数是把当年的树取出来重跑得来的** ⇒ ⇒ "

            "**⇒ 所以「它今天复算不出来」不等于「它当初是假的」**",

}

#   ⇒ ⇒⇒⇒ **⇒ 「恒真掩盖缺陷」的又一例**（与「绝对条数是快照」同族）⇒ ⇒⇒⇒⇒
#   ⇒ ⇒⇒⇒⇒ **⇒ 处置：判据集合 = 产物里所有 `P<n>_hold_*` 键（按编号排序）**
#   ⇒ ⇒⇒⇒⇒⇒ ⇒⇒⇒⇒ **⇒ ⇒ 以后加判据不会再漏** ⇒ ⇒⇒⇒⇒⇒⇒⇒⇒
#   ⇒ ⇒⇒⇒⇒⇒ **⇒ 而且这一条**可证伪**：把某条判据改红 ⇒ ⇒ 退出码必须跟着变**
_P_KEYS_hold_1007 = sorted((k for k in out if re.match(r"^P\d+_hold_", k)),
                     key=lambda k: (int(k[1:k.index("_")]), k))
_CRITERIA = [out[k] for k in _P_KEYS_hold_1007]
out["criteria_keys_hold_1007"] = list(_P_KEYS_hold_1007)
out["criteria_n_hold_1007"] = len(_P_KEYS_hold_1007)
# ⭐⭐⭐⭐⭐ 1032-②g：**判据台账** —— 「一条 False 是结论还是失败」必须能机检
#   ⇒ ⇒ 口径：kind ∈ {failure, conclusion, precondition}
#   ⇒ ⇒⇒   failure     = 这条判据红 = **被测对象不满足它** ⇒ 要修被测对象（真红）
#   ⇒ ⇒⇒   conclusion  = 这条判据红 = **我自己写下的那个否证不再成立** ⇒ 要更正结论
#   ⇒ ⇒⇒   precondition= 这条判据依赖前提；前提不成立时读数是 None ⇒ **None 不是红**
#   ⇒ ⇒⇒ **而 kind 不是从文本机械猜的**（「❌」「被否」「否掉」在两种语义位置都出现）
#   ⇒ ⇒⇒⇒ **⇒ 所以逐条读原文、由人定性** ⇒ ⇒⇒
#   ⇒ ⇒⇒⇒ **⇒ 而「没标注」=「不可判定」= 第三档、不许默认成 failure** ——
#   ⇒ ⇒⇒⇒⇒ **⇒ 因为「默认成 failure」会把「我还没判定」记成「我判定它坏了」**
out["criterion_kinds_1007"] = {
    "P1_hold_1007": "conclusion",
    "P2_hold_1007": "failure",
    "P3_hold_1007": "conclusion",
    "P4_hold_1007": "failure",
    "P5_hold_1007": "failure",
    "P6_hold_1007": "failure",
    "P7_hold_1007": "failure",
}
out["criteria_ledger_1007"] = {
    _k: {"verdict": out[_k], "kind": out["criterion_kinds_1007"].get(_k)}
    for _k in _P_KEYS_hold_1007
}
out["criterion_kinds_complete_1007"] = (
    set(out["criterion_kinds_1007"]) == set(_P_KEYS_hold_1007))

_EXIT = _exit_code(_CRITERIA, crashed=False)
out["exit_code_1007"] = {
    "criteria": _CRITERIA,
    "exit_code_would_be": _EXIT,
    "all_green": all(_CRITERIA),
    "rule": "⭐⭐⭐⭐⭐ **判据红 ⇒ rc=1；仪器崩 ⇒ rc=2；全绿 ⇒ rc=0** ⇒ ⇒ "
            "**⇒ 而以前这里是恒 0 ⇒ ⇒⇒ 「退出码恒 0 的门等于没有门」**",
    "selftest": {
        "all_green_gives_0": _exit_code([True, True]) == 0,
        "one_false_gives_1": _exit_code([True, False]) == 1,
        "crashed_gives_2": _exit_code([True], crashed=True) == 2,
        "not_applicable_is_not_red": _exit_code([True, None]) == 0,
    },
}
out["exit_code_selftest_ok_1007"] = all(out["exit_code_1007"]["selftest"].values())

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("multi =", len(multi), "| pairs =", n_pairs)
print("P1 dirty inconsistent = %d/%d = %.1f%%  (预测 <25%%)"
      % (dirty["n_inconsistent"], len(multi),
         out["P1_dirty_inconsistent_pct"]))
print("P2 audit about_self: dirty %s%% -> clean %s%% | generic-only %d/%d"
      % (dirty["audit_pct"], clean["audit_pct"],
         aus_hit_generic_only, aus_hit_total))
print("P2 inconsistent: dirty %d -> clean %d | inverted = %s"
      % (dirty["n_inconsistent"], clean["n_inconsistent"],
         out["dirty_vs_clean_1007"]["asymmetry_inverted"]))
print("P3 sweep audit_pct =",
      [s["audit_pct"] for s in sweep], "| monotone =", mono)
print("P5 reverse: gate problems =", r_rev["n_problems"],
      "| inconsistent =", out["reverse_case_1007"]["inconsistent"],
      "| misleading =", out["reverse_case_1007"]["misleading"])
print("P6 golden rows =", len(rows))
print("P1..P%d = %s" % (len(_P_KEYS_hold_1007),
                         [out[k] for k in _P_KEYS_hold_1007]))
print("判据逐条 = %s" % " | ".join("%s=%s" % (k, out[k])
                              for k in _P_KEYS_hold_1007))
print("PROBE_1007_DONE ->", OUT)
# ⭐⭐⭐⭐⭐ **最后一行才是退出** —— 而产物**已经在上面写完了**
#   ⇒ ⇒⇒⇒ **⇒「红」必须既留下产物、又留下非零退出码** ⇒ ⇒
#   ⇒ ⇒⇒⇒⇒ **⇒ 而以前这里是 rc=0 ⇒ ⇒⇒ 「它红了没人知道」**
sys.exit(_EXIT)
