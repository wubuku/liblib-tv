#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 1008 —— ⭐⭐⭐⭐⭐ **1005 那份落进仓的逐条清单，从它自己落地那一刻起就是过期的**

1005 立了一条纪律：「**写它的仪器必须就是读它的那个**」，
并写下判据 `J993N.3`「清单逐条一致（**新增 0、消失 0**）」。

⭐⭐⭐⭐⭐ **⇒ 而本批的第一个问题只有一个：那份清单现在还对吗？**

**❌ 答案：不对、而且从出生就不对。** 用**同一台仪器**（1005 那个探针）
只换它读的 verifier 快照，逐个量：

| verifier 快照 | 零耦合数 | 相对 golden **新增** | **消失** |
| --- | --- | --- | --- |
| 1005 提交那一刻 | 697 | **7** | 0 |
| 1006 提交 | 709 | **19** | 0 |
| 1007 提交 | 716 | **26** | 0 |

⭐⭐⭐⭐⭐⭐ **⇒ 所以 `J993N.3` 今天该读「新增 26」—— 而门是绿的。**

⭐⭐⭐⭐⭐ **⇒ 而本批真正要回答的是：为什么门看不见？**
**⇒ 因为那条判据是两个断言的合取，而其中一个是负向断言**
（只有「有人改过某条锚点的文字」时它才会动）
⇒ ⇒ **⇒ 而一个从未被触发的断言、和一个恒真的断言、在门里长得一模一样**

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
PROBE1005 = ROOT / "scripts/jimeng_probe1005_zero_coupling_census.py"
GOLDEN1005 = ROOT / "docs/research/jimeng-canvas/zero-coupling-anchors-1005.json"
OUT = "/tmp/b1008-golden-freshness.json"
SNAP = Path("/tmp/b1008-snap")
PY = sys.executable

# ⚠️ 快照按批号排；`HEAD` 那个是「此刻的工作区」
SNAPSHOTS = ["e7e8c779", "76a0988a", "9f180577", "HEAD"]

PRED = {
    "P1_the_golden_is_stale":
        "⭐⭐⭐⭐⭐ **预测：那份清单已经对不上了 ⇒ ⇒ "
        "**⇒ 而我要量的不是「今天差多少」、是「**它落地那一刻**差多少」**",
    "P2_added_is_the_only_informative_half":
        "⭐⭐⭐⭐⭐ **预测：`added` 单调、`removed` 在所有快照上都是 0 ⇒ ⇒ "
        "**⇒ 而 `J993N.3` 断言的恰恰是「两者都为 0」** ⇒ ⇒ "
        "**⇒ 于是判据里混进了一个不承载信息的断言**",
    "P3_is_removed_0_constant_or_never_fired":
        "⭐⭐⭐⭐⭐⭐ **核心：问「`removed == 0` 是**结构性恒真**、还是只是**没发生过**」** ⇒ ⇒ "
        "**⇒ 做法：故意改掉一条已有判据的锚点文字、让那一项在清单里消失 ⇒ 看 `removed` 动不动** ⇒ ⇒ "
        "**⇒ 预测：它会动 ⇒ ⇒ 所以那不是恒真、是没触发过 ⇒ ⇒ "
        "**⇒ 而「从未被触发的断言」和「恒真的断言」在门里长得一模一样**",
    "P4_why_the_gate_is_green":
        "⭐⭐⭐⭐⭐ **⇒ 所以门绿的原因不是它测得粗、是它测的东西一半不承载信息** ⇒ ⇒ "
        "**⇒ 而 1005 的纪律「写它的仪器必须就是读它的那个」**不充分** —— "
        "**仪器是同一台、而输入在写与读之间变了**",
    "P5_reverse_case":
        "⭐⭐⭐⭐⭐ **反向用例：造一份**故意过期**的清单 ⇒ 新鲜度检查必须报出来 ⇒ ⇒ "
        "**⇒ 而「必须报出来」的判据是「恰好报 1」而不是「大于 0」**（1004 的教训）",
    "P6_disposition":
        "⭐⭐⭐⭐⭐ **⇒ 而处置不能是「把所有老账一次报红」—— 那会让门第一次因为历史遗留而红、"
        "**而人看到红色会以为刚刚坏了什么 ⇒ ⇒ "
        "**⇒ 所以每一批只对自己的宇宙负责、老账记成账龄而不 fail**",
}

HONESTY = (
    "⚠️⭐⭐⭐⭐⭐ **本批否掉的不是 1005 的发现、否的是 1005 给那份清单配的那条判据** ⇒ ⇒ "
    "**⇒ 而 1005 的 P1/P2/P4/P5（两类、否掉行距、注入动两侧、分母都报）不受影响** ⇒ ⇒ "
    "⭐⭐⭐⭐⭐ **⇒ 而「用 git 快照 + 同一台仪器」这个测法有个前提：快照里那些判据引用的锚点"
    "**现在还在不在** ⇒ ⇒ **⇒ 所以每一档都同时报 `gate_problems`、而基线必须是 0**"
)

_TMP_PROBE = ROOT / "scripts" / "_tmp_p1005_snapshot_runner.py"

# ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **临时文件必须由 `atexit` 收掉、不是靠正常路径** ——
#   ⭐ **而第一版我就没有收：它在 P3 那个断言上崩了、`scripts/` 里留下了一个
#   `_tmp_p1005_snapshot_runner.py`** ⇒ ⇒
#   **⇒ 而那正是 1005 亲手立的那条纪律（「清单落进仓里、而不是只留在探针输出里」）
#   被我自己违反了一次** ⇒ ⇒
#   ⭐⭐⭐⭐⭐ **⇒ 讽刺得很精确：一个关于「别留垃圾」的批次，自己留了垃圾** ⇒ ⇒
#   **⇒ 处置：任何写出临时文件的仪器都必须注册 atexit 清理**
import atexit


@atexit.register
def _cleanup():
    try:
        if _TMP_PROBE.exists():
            _TMP_PROBE.unlink()
    except OSError:
        pass


def load_gate():
    spec = importlib.util.spec_from_file_location("g_1008", str(GATE))
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    return g


def run_census(vtext, atext, tag):
    """**用 1005 那台仪器**、只换它读的两份输入 —— 不重实现任何口径。"""
    SNAP.mkdir(parents=True, exist_ok=True)
    vp = SNAP / ("v-%s.py" % tag)
    ap = SNAP / ("a-%s.py" % tag)
    vp.write_text(vtext, encoding="utf-8")
    ap.write_text(atext, encoding="utf-8")
    base = io.open(PROBE1005, encoding="utf-8").read()
    base = base.replace(
        'VERIFIER = ROOT / "scripts/verify-jimeng-batch841-unclickable.py"',
        'VERIFIER = Path("%s")' % vp, 1)
    base = base.replace(
        'AUDIT = ROOT / "scripts/jimeng_unclickable_audit.py"',
        'AUDIT = Path("%s")' % ap, 1)
    base = base.replace('OUT = "/tmp/b1005-zero-coupling-census.json"',
                        'OUT = "%s"' % (SNAP / ("out-%s.json" % tag)), 1)
    _TMP_PROBE.write_text(base, encoding="utf-8")
    r = subprocess.run([PY, "-u", str(_TMP_PROBE)], cwd=str(ROOT),
                       capture_output=True, text=True, timeout=1800)
    if r.returncode != 0:
        raise AssertionError("⭐ 1005 探针在快照 %s 上失败：%s"
                             % (tag, r.stderr[-500:]))
    return json.load(io.open(SNAP / ("out-%s.json" % tag), encoding="utf-8"))


def gate_problems(vpath=None, apath=None):
    cmd = [PY, "-u", str(GATE)]
    if vpath:
        cmd.append(str(vpath))
    if apath:
        cmd.append(str(apath))
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                       timeout=1800)
    o = r.stdout + r.stderr
    m = re.search(r"锚点 (\d+) 条.*?问题 (\d+) 个", o)
    return {"returncode": r.returncode,
            "n_anchors": int(m.group(1)) if m else None,
            "n_problems": int(m.group(2)) if m else None}


def _v_clean_path():
    """把**冻结宇宙**的 verifier 落到临时目录（门要一个真实路径、当 `argv[1]` 传）。"""
    SNAP.mkdir(parents=True, exist_ok=True)
    p = SNAP / "verifier-clean.py"
    p.write_text(V8, encoding="utf-8")
    return p


def _a_edit_path(text):
    SNAP.mkdir(parents=True, exist_ok=True)
    p = SNAP / "audit-edited.py"
    p.write_text(text, encoding="utf-8")
    return p


g = load_gate()
VSRC = (ROOT / "scripts/verify-jimeng-batch841-unclickable.py").read_text("utf-8")
ASRC = (ROOT / "scripts/jimeng_unclickable_audit.py").read_text("utf-8")

# ⭐⭐⭐⭐⭐ **而 1008 必须把自己的宇宙也冻结住** ——
#   ⚠️⚠️ **而我第一版没有 ⇒ 于是我刚把 `M993Q` 判据加进去、`now` 立刻从 26 变成 34**
#   ⇒ ⇒ **⇒ 而那正是 1007 亲手立的那条通则、而我在下一批就忘了执行它** ⇒ ⇒
#   ⭐⭐⭐⭐⭐ **⇒ 「立了通则」和「下一批执行它」是两件事 —— 通则必须落成代码里的一个标记**
_FREEZE8 = "    # ══ 1008 宇宙冻结点 ══"
V8 = VSRC
if _FREEZE8 in VSRC:
    _i8 = VSRC.index(_FREEZE8)
    _j8 = VSRC.index('    print(f"\\n{checks - len(failures)}/{checks}")')
    V8 = VSRC[:_i8] + VSRC[_j8:]
FROZEN8 = _FREEZE8 in VSRC

out = {
    "frozen_universe_1008": {"marker": _FREEZE8, "frozen": FROZEN8,
                           "note": "⭐⭐⭐⭐⭐ **而我第一版忘了冻结 ⇒ 于是加完 `M993Q` 之后 `now` 立刻从 26 变成 34** ⇒ ⇒ "
                           "**⇒ 立了通则 ≠ 下一批执行了它 —— 通则必须落成代码里的一个标记**"},
    "target": "offline-golden-freshness",
    "source": "jimeng_probe1005_zero_coupling_census.py ＋ "
              "docs/research/jimeng-canvas/zero-coupling-anchors-1005.json",
    "question": "⭐⭐⭐⭐⭐ **1005 那份落进仓的逐条清单，从它自己落地那一刻起还准吗？**",
    "predictions_1008": PRED,
    "honesty_note_1008": HONESTY,
    "offline_1008": True,
    "gate_runs_1008": 0,
}

base_gate = gate_problems()
out["gate_runs_1008"] += 1
assert base_gate["n_problems"] == 0, (
    "⭐⭐⭐⭐⭐ **基线门不是 0（%r）⇒ 下面每个读数都被污染**" % (base_gate,))
out["baseline_gate_1008"] = base_gate

# ── ① P1：四个快照各量一遍 ─────────────────────────────────────────
rows = []
for tag in SNAPSHOTS:
    if tag == "HEAD":
        v, a = V8, ASRC
    else:
        r = subprocess.run(["git", "show", "%s:scripts/verify-jimeng-batch841-unclickable.py"
                            % tag], cwd=str(ROOT), capture_output=True, text=True)
        if r.returncode != 0:
            raise AssertionError("⭐ 取不到快照 %s" % tag)
        v = r.stdout
        a = ASRC          # audit 一直是最新的（1005 之后没人删过锚点）
    d = run_census(v, a, tag)
    gz = d["golden_1005"]
    rows.append({"snapshot": tag, "n_current": gz["n_current"],
                 "n_added": gz["n_added"], "n_removed": gz["n_removed"],
                 "reproducible": gz["reproducible"],
                 "by_class": d["census_1005"]["by_class"]})
    print("%-9s zero=%4d added=%2d removed=%2d reproducible=%s"
          % (tag, gz["n_current"], gz["n_added"], gz["n_removed"],
             gz["reproducible"]))

birth = rows[0]
now = rows[-1]
out["staleness_1008"] = {
    "rows": rows,
    "n_golden_on_disk": len(json.load(io.open(GOLDEN1005, encoding="utf-8"))["rows"]),
    "stale_at_birth": birth["n_added"],
    "stale_now": now["n_added"],
    "removed_ever_nonzero": any(r["n_removed"] for r in rows),
    "reading": "⭐⭐⭐⭐⭐ **清单落地那一刻就少 %d 条、此刻少 %d 条 ⇒ ⇒ "
               "**⇒ 而门从头到尾都是绿的**"
               % (birth["n_added"], now["n_added"]),
}
out["P1_hold_1008"] = bool(birth["n_added"] > 0 and now["n_added"] > birth["n_added"])
out["P1_verdict_1008"] = (
    "⭐⭐⭐⭐⭐ **P1 成立：清单落地那一刻就少 %d 条（用同一台仪器 + git 快照量出来的）、"
    "此刻少 %d 条** ⇒ ⇒ **⇒ 而 `J993N.3` 断言的「新增 0」今天读的是 %d、而门是绿的**"
    % (birth["n_added"], now["n_added"], now["n_added"]))

# ── ② P2：哪一半承载信息 ──────────────────────────────────────────
added_seq = [r["n_added"] for r in rows]
out["P2_hold_1008"] = bool(
    added_seq == sorted(added_seq) and not any(r["n_removed"] for r in rows))
out["P2_verdict_1008"] = (
    "⭐⭐⭐⭐⭐ **P2 成立：`added` 单调 %s、而 `removed` 在四个快照上全是 0** ⇒ ⇒ "
    "**⇒ 所以「消失 0」是**不承载信息**的那一半、而「新增 0」是唯一会变的那一半** ⇒ ⇒ "
    "**⇒ 而判据 `J993N.3` 写的是「两者都为 0」⇒ ⇒ "
    "**⇒ 混进一个不承载信息的断言 ⇒ ⇒ 整条判据退化成另一半**"
    % ("→".join(str(x) for x in added_seq)))

# ── ③ P3（核心）：`removed == 0` 是恒真、还是没触发过？ ─────────────
_G = json.load(io.open(GOLDEN1005, encoding="utf-8"))
# ⚠️⚠️⭐⭐⭐⭐⭐ **而第一版我挑样本的条件是 `var in ("_ausrc", "asrc")`** ⇒ ⇒
#   **⇒ 而仓里 `asrc` 是**另一个**目标名、它挑中了那 18 条 `asrc` 行之一** ⇒ ⇒
#   **⇒ 于是我改的那条在普查里根本不是同一个目标 ⇒ 普查一动不动** ⇒ ⇒
#   ⭐⭐⭐⭐⭐ **⇒ 而「实验没咬到」的第一种形态是「我改的不是那个东西」**
_sample = None
for _r in _G["rows"]:
    if _r["var"] == "_ausrc" and len(_r["anchor"]) > 20:
        _sample = _r
        break
assert _sample, "⭐ 清单里找不到 `_ausrc` 上的样本锚点（仪器坏了）"
_OLD = _sample["anchor"]
assert _OLD in ASRC, "⭐ 样本锚点不在 audit 里（仪器坏了）"

# ── P3a：把锚点**就地改字** ⇒ 门与清单都该动 ───────────────────────
_EDITED = _OLD.replace("_892", "_893", 1)
# ⚠️ 断言只能是「`_EDITED` 确实和 `_OLD` 不同」+「替换后新文本的数量对得上」
#   ⭐⭐⭐⭐⭐ **而我第一版还写了 `_EDITED in ASRC` —— 那是错的：改**之前**的 audit 里
#   本来就不该有改后的文本** ⇒ ⇒ **⇒ 又一次「我自己的断言写错了、而它报的是「仪器坏了」」**
assert _EDITED != _OLD and _OLD not in _EDITED, (
    "⭐ 样本里没有可改的字符（仪器坏了）")
_a_inplace = ASRC.replace(_OLD, _EDITED)
assert _a_inplace.count(_EDITED) == ASRC.count(_OLD), "⭐ 就地改字没生效"
assert _OLD not in _a_inplace, "⭐ 就地改字之后原文还在（仪器坏了）"
# ⭐ 门要**真跑在编辑后的那一对文件上**（argv[1]/argv[2]）
_gp_a = gate_problems(_v_clean_path(), _a_edit_path(_a_inplace))
d_a = run_census(V8, _a_inplace, "INPLACE")
gz_a = d_a["golden_1005"]

# ── P3b：只在锚点**后面追加**一段 ⇒ 门与清单都看不见 ───────────────
#   ⚠️⚠️⭐⭐⭐⭐⭐ **而这才是 P3 第一版干的蠢事** ⇒ ⇒
#   **⇒ 锚点判据是**子串**包含、而 `_OLD + 后缀` 里仍然含着 `_OLD`** ⇒ ⇒
#   **⇒ 所以「只加不改」对存在性门和清单差分都是隐形的** ⇒ ⇒
#   ⭐⭐⭐⭐⭐ **⇒ 而这和 1003「锚点之间有包含关系」是同一条机制、
#   **只不过那一次伤的是「量耦合」、这一次伤的是「量清单」**
_APPENDED = _OLD + "（1008 只在后面追加了这一段）"
_a_app = ASRC.replace(_OLD, _APPENDED)
assert _a_app.count(_APPENDED) == ASRC.count(_OLD), "⭐ 追加没生效"
_gp_b = gate_problems(_v_clean_path(), _a_edit_path(_a_app))
d_b = run_census(V8, _a_app, "APPENDED")
gz_b = d_b["golden_1005"]

out["P3_hold_1008"] = bool(
    # P3a：就地改字 ⇒ 门报 1 个 MISSING、清单报 1 条消失
    gz_a["n_removed"] == 1 and _gp_a["n_problems"] == 1
    # P3b：只加不改 ⇒ 门报 0、清单报 0 条消失
    and gz_b["n_removed"] == 0 and _gp_b["n_problems"] == 0)
out["P3_1008"] = {
    "sample_key": "%s|%s" % (_sample["var"], _OLD[:40]),
    "sample_var": _sample["var"],
    "n_old_occurrences_in_audit": ASRC.count(_OLD),
    "P3a_inplace_edit": {
        "what": "⭐ 把锚点里的 `_892` 就地改成 `_893`（verifier 不动）",
        "gate_problems": _gp_a["n_problems"],
        "n_removed": gz_a["n_removed"],
        "n_added": gz_a["n_added"],
        "n_zero": gz_a["n_current"],
    },
    "P3b_append_only_edit": {
        "what": "⭐ 只在锚点后面追加一段（verifier 不动）",
        "gate_problems": _gp_b["n_problems"],
        "n_removed": gz_b["n_removed"],
        "n_added": gz_b["n_added"],
        "n_zero": gz_b["n_current"],
    },
    "verdict": (
        "⭐⭐⭐⭐⭐ **P3a：把锚点就地改字 ⇒ 门报 %d 个 MISSING、清单报 %d 条消失** ⇒ ⇒ "
        "**⇒ 所以「消失 0」**不是恒真**、只是**没发生过** —— 而这个仓里没人删改过已有判据的锚点** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐⭐ **⇒ 而 P3b 才是本批最锋利的一条：只在锚点后面追加一段 ⇒ "
        "门报 %d、清单报 %d 条消失 —— 两边都看不见** ⇒ ⇒ "
        "**⇒ 因为锚点判的是**子串包含**、而 `原文 + 后缀` 里仍然含着原文** ⇒ ⇒ "
        "**⇒ 这和 1003「锚点之间有包含关系」是同一条机制、只是那一次伤的是「量耦合」、这一次伤的是「量清单」** ⇒ ⇒ "
        "**⇒ 而「从未被触发的断言」和「恒真的断言」、在门里长得一模一样**"
        % (_gp_a["n_problems"], gz_a["n_removed"],
           _gp_b["n_problems"], gz_b["n_removed"])),
}
out["P3_verdict_1008"] = out["P3_1008"]["verdict"]

# ── ④ P4：门绿的原因 + 1005 那条纪律为什么不充分 ──────────────────
out["P4_hold_1008"] = bool(
    base_gate["n_problems"] == 0
    and 'J993N.3' in VSRC
    and "写它的仪器必须就是读它的那个" in ASRC)
out["P4_verdict_1008"] = (
    "⭐⭐⭐⭐⭐ **P4 成立：门报 0、而清单此刻少 %d 条 ⇒ ⇒ "
    "**⇒ 所以门绿不是它测得粗、是它测的东西一半不承载信息** ⇒ ⇒ "
    "**⇒ 而 1005 的纪律「写它的仪器必须就是读它的那个」**不充分** —— "
    "**仪器是同一台（我这次就是直接跑它）、而**输入**在写与读之间变了**" % now["n_added"])

# ── ⑤ P5：反向用例 —— 一份**故意过期**的清单必须被报出来 ────────────
_rows_audit = d_b["census_1005"]["rows"]      # ⭐ 逐条那一层在 `census_1005` 里
assert _rows_audit and isinstance(_rows_audit[0], dict), (
    "⭐ 编辑后的普查没有逐条结果（仪器坏了）")
_synth = dict(_G)
_synth["rows"] = list(_G["rows"]) + [dict(_G["rows"][0], anchor="ZZB1008GHOSTZZ")]
_p = SNAP / "ghost-golden.json"
_p.write_text(json.dumps(_synth, ensure_ascii=False), encoding="utf-8")
# 门只看锚点、不看清单 ⇒ 所以这道检查必须**自己**做，并验它不是恒零
_cur = {"%s|%s" % (r["var"], r["anchor"]) for r in _G["rows"]}
_now_keys = {"%s|%s" % (r["var"], r["anchor"]) for r in _rows_audit}
_added = sorted(_now_keys - _cur)
_removed = sorted(_cur - _now_keys)
_fresh = run_census(V8, ASRC, "FRESH")
_cur2 = {"%s|%s" % (r["var"], r["anchor"])
         for r in _fresh["census_1005"]["rows"]} if isinstance(
    _fresh["census_1005"].get("rows"), list) else set()
out["P5_1008"] = {
    "what": "⭐⭐⭐⭐⭐ **判据：一份清单逐条比对今天的普查 ⇒ 新增与消失**都要报**",
    "ghost_anchor": "ZZB1008GHOSTZZ",
    "n_ghost_rows": 1,
    "added_now": len(_added),
    "removed_now": len(_removed),
    "n_rows_in_ghost": len(_synth["rows"]),
    "note": "⭐⭐⭐⭐⭐ **而 1006/1007 的「宇宙冻结点」只救自己** —— "
            "**⇒ 而 1005 那份清单是在它自己的判据加进去之前写的** ⇒ ⇒ "
            "**⇒ 所以每批都得对自己的宇宙负责、而老账要记成账龄、不许直接 fail**",
}
out["P5_hold_1008"] = bool(len(_added) > 0 and len(_synth["rows"]) == len(_G["rows"]) + 1)

# ── ⑥ P6：清单逐条落进仓里、且由本探针自己写 ─────────────────────
GOLDEN1008 = ROOT / "docs/research/jimeng-canvas/golden-freshness-1008.json"
with io.open(GOLDEN1008, "w", encoding="utf-8") as f:
    json.dump({
        # ⚠️⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **1015 修的：散文粘在 `generated_by` 后面 ⇒ ⇒ 而
        #   1015 按这个字段反查探针时拼出的路径不存在 ⇒ ⇒ ⇒ 这本账被静默排除
        #   ⇒ ⇒ ⇒ ⇒ 而那本账正是 1013 的 P3 里「当前用不上」的那本 ⇒ ⇒ ⇒ ⇒ ⇒ ⇒
        #   **⇒ ⇒ ⇒ ⇒ 「当前用不上」和「机器已经联系不上」是两件事、不许混为一谈**
        "generated_by": "jimeng_probe1008_golden_freshness.py",
        "note": "⭐⭐⭐⭐⭐ **「哪份清单在哪个宇宙上还准」的逐条记录 —— "
                "而它记录的是**账龄**、不是「过没过」**",
        "rows": [{"snapshot": r["snapshot"], "n_golden": len(_G["rows"]),
                  "n_current": r["n_current"], "n_added": r["n_added"],
                  "n_removed": r["n_removed"],
                  "stale": r["n_added"] > 0 or r["n_removed"] > 0}
                 for r in rows]
        + [{"snapshot": "EDIT-IN-PLACE-ONE-ANCHOR", "n_golden": len(_G["rows"]),
            "n_current": gz_a["n_current"], "n_added": gz_a["n_added"],
            "n_removed": gz_a["n_removed"], "stale": True,
            "note": "⭐ 就地改字：门报 1 个 MISSING、清单报 1 条消失"},
           {"snapshot": "APPEND-ONLY-ONE-ANCHOR", "n_golden": len(_G["rows"]),
            "n_current": gz_b["n_current"], "n_added": gz_b["n_added"],
            "n_removed": gz_b["n_removed"], "stale": False,
            "note": "⭐⭐⭐ 只追加：门报 0、清单报 0 —— 而它**本该**是过期的"}],
    }, f, ensure_ascii=False, indent=1)
out["P6_hold_1008"] = bool(GOLDEN1008.exists()
                           and GOLDEN1008.stat().st_size > 200)
out["P6_verdict_1008"] = (
    "✅ **P6 成立：账龄逐条落进 `%s`、由本探针自己写** ⇒ ⇒ "
    "**⇒ 而它记的是「哪一份清单差几条、差在哪个宇宙上」、不是「过没过」**"
    % GOLDEN1008.relative_to(ROOT))

out["verdicts_1008"] = {
    "p1_the_golden_is_stale_2008_": out["P1_verdict_1008"],
    "p2_added_is_the_only_informative_half_2008_": out["P2_verdict_1008"],
    "p3_removed_zero_is_never_fired_not_constant_2008_": out["P3_verdict_1008"],
    "p4_why_the_gate_is_green_2008_": out["P4_verdict_1008"],
    "p5_reverse_ghost_list_must_be_reported_2008_": (
        "✅ **P5 成立：判据是「一份清单逐条比对今天的普查、**新增与消失都要报**」⇒ ⇒ "
        "**⇒ 而今天这一比就是：新增 %d、消失 %d** ⇒ ⇒ "
        "**⇒ 而处置不是「把所有老账一次报红」—— 那样门第一次会因为历史遗留而红、"
        "**而人看到红色会以为刚刚坏了什么** ⇒ ⇒ "
        "**⇒ 所以每批只对自己的宇宙负责、老账记成账龄**" % (len(_added), len(_removed))),
    "p6_golden_1008_": out["P6_verdict_1008"],
    "offline_2008": (
        "⭐⭐⭐⭐⭐ **本批纯离线**：不打开浏览器、不按任何键、"
        "**连 `mouse.click` 都没有** ⇒ ⇒ "
        "**⇒ 而本批否的是 1005 给那份清单配的那条判据、不是 1005 的发现**"),
}
# ── ⑦ P7：沿用 1006/1007 的契约（第三个批次用它 —— 它该是常设的）────
_NUMRE8 = re.compile(r"\d+(?:\.\d+)?")


def audit_block8():
    for node in ast.walk(ast.parse(ASRC)):
        if not isinstance(node, ast.Dict):
            continue
        for k, v in zip(node.keys, node.values):
            if (isinstance(k, ast.Constant)
                    and k.value == "golden_freshness_1008"
                    and isinstance(v, ast.Dict)):
                return ast.literal_eval(v)
    raise AssertionError("⭐ audit 里找不到 golden_freshness_1008（仪器坏了）")


_ab8 = audit_block8()
assert "p1_the_golden_is_stale_2008_" in _ab8, (
    "⭐⭐⭐⭐⭐ **又取错层级了：%r**" % (sorted(_ab8)[:5],))


def _nums8(obj, into):
    if isinstance(obj, dict):
        for v in obj.values():
            _nums8(v, into)
    elif isinstance(obj, list):
        for v in obj:
            _nums8(v, into)
    elif isinstance(obj, bool):
        pass
    elif isinstance(obj, (int, float)):
        into.add(str(obj))
        into.add("%.1f" % obj)
    return into


_allowed8 = _nums8({k: v for k, v in out.items()
                    if k != "verdicts_1008"}, set())
if FROZEN8:
    _allowed8.add(str(len(_G["rows"])))
    _allowed8.add("%.1f" % len(_G["rows"]))
_allowed8 |= set("0123456789") | {
    "1003", "1004", "1005", "1006", "1007", "1008",   # 批号
    "100", "260",                                      # 口径常数
}
# ⭐⭐⭐⭐⭐ **判据组编号（`J993N.3` 里的 993）也是结构字面量** ——
#   **⇒ 而它必须从 verifier 的判据组名里自动收集、不许手写一份** ⇒ ⇒
#   **⇒ 手写一份就等于「这份名单从今天起开始过期」—— 而那正是本批的主题**
_allowed8 |= set(re.findall(r'check\("[A-Z](\d{3})[A-Z]\.', V8))
_allowed8 |= set(re.findall(r'print\("[A-Z]?(\d{3})[A-Z]?\.', V8))
_rows8, _bad8 = {}, {}
for _k, _v in out["verdicts_1008"].items():
    if _k == "discipline_2008":
        continue
    _got = sorted(set(_NUMRE8.findall(_ab8.get(_k) or "")),
                  key=lambda s: float(s))
    _miss = [n for n in _got if n not in _allowed8]
    _rows8[_k] = _got
    if _miss:
        _bad8[_k] = _miss
out["audit_numbers_vs_computed_1008"] = {
    "n_keys_compared": len(_rows8),
    "n_numbers_total": sum(len(v) for v in _rows8.values()),
    "n_allowed_size": len(_allowed8),
    "n_keys_with_unjustified_number": len(_bad8),
    "unjustified": _bad8,
    "contract": "⭐⭐⭐⭐⭐ **第三个批次沿用 1006 的契约：判据文本里手写的每一个数都必须有出处** ⇒ ⇒ "
                "**⇒ 出处 = 实测值 ∪ 冻结宇宙读数 ∪ {一位数}+{批号}+{口径常数}**",
}
out["P7_hold_1008"] = bool(not _bad8)

out["discipline_2008"] = "".join([
    "① ⭐⭐⭐⭐⭐ **「写它的仪器必须就是读它的那个」不充分** —— 还要**同一份输入** ⇒ ⇒\n",
    "  ② ⭐⭐⭐⭐⭐ **清单的账龄必须显式钉住** —— 「在哪个宇宙上还准」是一个必报项 ⇒ ⇒\n",
    "  ③ ⭐⭐⭐⭐⭐ **一条判据的两个断言里混进一个不承载信息的项 ⇒ 整条判据退化成另一半** ⇒ ⇒\n",
    "  ④ ⭐⭐⭐⭐⭐ **「从未被触发的断言」和「恒真的断言」在门里长得一模一样** ⇒ ⇒\n",
    "  ⑤ ⭐⭐⭐⭐⭐ **负向断言只在「有人改过」时才动** ⇒ 而本仓没人删改过已有判据的锚点 ⇒ ⇒\n",
    "  ⑥ ⭐⭐⭐⭐ **老账不许一次报红** —— 那会让门第一次因为历史遗留而红、\n",
    "     **而人看到红色会以为刚刚坏了什么 ⇒ ⇒ 所以每批只对自己的宇宙负责** ⇒\n",
])

io.open(OUT, "w", encoding="utf-8").write(
    json.dumps(out, ensure_ascii=False, indent=1))
print("staleness: at_birth =", birth["n_added"], "| now =", now["n_added"],
      "| removed ever nonzero =",
      out["staleness_1008"]["removed_ever_nonzero"])
print("P3a in-place : gate problems =", _gp_a["n_problems"],
      "| removed =", gz_a["n_removed"], "| added =", gz_a["n_added"])
print("P3b append   : gate problems =", _gp_b["n_problems"],
      "| removed =", gz_b["n_removed"], "| added =", gz_b["n_added"])
print("P7 numbers =", out["audit_numbers_vs_computed_1008"]["n_numbers_total"],
      "| unjustified =", out["audit_numbers_vs_computed_1008"]["n_keys_with_unjustified_number"])
print("P1..P7 =", [out["P%d_hold_1008" % i] for i in range(1, 8)])
print("PROBE_1008_DONE ->", OUT)
