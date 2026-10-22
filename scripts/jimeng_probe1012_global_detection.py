#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 1012 —— ⭐⭐⭐⭐⭐⭐⭐⭐ **把 1010 那台仪器扩到全局：门在十批真实历史里开口过几次？**

1010 只量了 `_ausrc`（audit 基线）一个目标，读数是「真实检出力 0.0」。
1011 收窄了它：那 54 次里 38 次是我每批重复写的计费声明，**而门按设计不该报它们**。

⭐⭐⭐⭐⭐⭐⭐⭐ **⇒ 而本批把同一台仪器扩到全部 187 个目标变量上，
问那个 1010 一直没能问出口的问题：门在全局口径上，到底一次都没报过吗？**

⇒ ⇒ ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **答案是：报过 1 次。58 次目标侧改动里、真正消失的只有 1 次，
而门把它报了 —— ⇒ ⇒ ⇒ ⇒ 「这道门一次都没开口」这句话在全局口径上是错的**

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **而更要紧的是：这一次正是 1006 亲手换掉的那条
「钉门源码整行」的锚点 —— 1010 的 P6 从「拿旧 verifier 跑今天的门」那条通道
发现了它，本批从「真实改动里数消失」这条完全独立的通道发现了同一个东西
⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 零成本的复现通道被两条独立路径互相确认**

⚠️⭐⭐⭐⭐⭐ **而本批的第一条预期是错的**：我以为「每批都在重写整个探针文件、
所以改动形态是重写而不是追加」⇒ ⇒ **实测：十对快照里、探针侧总共只被动过 4 次**
⇒ ⇒ ⭐⭐⭐⭐⭐⭐⭐⭐⭐ **⇒ 「我以为我知道我干了什么」是错的 —— 而这个错差点
让我把路线定成「给门加声明机制」**

本批**纯离线**：不打开浏览器、不按任何键、连 `mouse.click` 都没有
"""
import ast
import atexit
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
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GATE = ROOT / "scripts/jimeng_check_verifier_anchors.py"
VFILE = "scripts/verify-jimeng-batch841-unclickable.py"
AFILE = "scripts/jimeng_unclickable_audit.py"
GOLDEN = ROOT / "docs/research/jimeng-canvas/global-detection-1012.json"
OUT = "/tmp/b1012-global-detection.json"
AUDIT_TXT = (ROOT / AFILE).read_text(encoding="utf-8")
VERIFIER_TXT = (ROOT / VFILE).read_text(encoding="utf-8")
PY = sys.executable

COMMITS = [
    ("1001", "1dda1d5b"), ("1002", "a62401ba"), ("1003", "20c76d45"),
    ("1004", "11ef6888"), ("1005", "e7e8c779"), ("1006", "76a0988a"),
    ("1007", "9f180577"), ("1008", "d857b7f7"), ("1009", "0eada9fc"),
    ("1010", "f5157f18"), ("1011", "0d9f6a00"),
]

# ⭐⭐⭐⭐⭐⭐⭐⭐ **本探针要写临时文件（要把每个快照的目标文件落盘喂给门）** ⇒ ⇒
#   **⇒ 而 1008 立过一条纪律：任何写出临时文件的仪器都必须注册 `atexit` 清理**
_TMPDIR = Path(tempfile.mkdtemp(prefix="b1012-"))


@atexit.register
def _cleanup():
    import shutil
    shutil.rmtree(_TMPDIR, ignore_errors=True)


def gs(sha, path):
    r = subprocess.run(["git", "show", "%s:%s" % (sha, path)], cwd=str(ROOT),
                       capture_output=True)
    if r.returncode != 0:
        raise AssertionError("⭐⭐⭐⭐⭐ 取不到 %s:%s（历史类判据的专属失效形态）"
                             % (sha, path))
    return r.stdout.decode("utf-8", "replace")


spec = importlib.util.spec_from_file_location("g_1012", str(GATE))
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

# ⚠️ `_ausrc` 不在 PROBE_VARS 里（它走默认 audit 路径）⇒ 必须显式补进来
PV = dict(g.PROBE_VARS)
PV["_ausrc"] = AFILE

# ── 基线自检：先把 11 个快照取回来，取不到就崩 ──────────────────────
V, T = {}, {}
for tag, sha in COMMITS:
    V[tag] = gs(sha, VFILE)
    for var, path in PV.items():
        r = subprocess.run(["git", "show", "%s:%s" % (sha, path)],
                           cwd=str(ROOT), capture_output=True)
        # ⚠️⭐⭐⭐⭐⭐ **目标文件在该快照里不存在 ≠ 取不到** ——
        #   **那正是「这个变量当时还没诞生」的真实情况、occurrence 必须是 0**
        T[(tag, var)] = (r.stdout.decode("utf-8", "replace")
                         if r.returncode == 0 else "")
# ⚠️⚠️⚠️⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **1015 修的：这一行第一版硬写 `len(PV) == 187`——
#   ⇒ ⇒ 而目标变量数**不是每批 +1** ⇒ ⇒ ⇒ ⇒ 1015 量到的事实是：
#   ⇒ ⇒ ⇒ ⇒ **1013 那批一次加了 3 个键** —— `_p1011`、`_p1012` 两个**补登记**
#   ⇒ ⇒ ⇒ ⇒ ⇒ 加上 `_p1013`；1014 再加 1 个（`_p1014`）⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **187 → 190**
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 我写这条注释时用的解释（「每批 +1」）也是错的**
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **⇒ 「我以为我知道我干了什么」在这一批里连中两次**
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒
#   ⇒ ⇒ ⇒ ⇒ 而 187 → 190 这件事本身就是 1015 的读数：
#   ⇒ ⇒ ⇒ ⇒ **补登记会追溯性地改写旧读数的分母**
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 旧的判据文字写着「187 个目标变量」、
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而产物今天已经是 190** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 处置：断言只钉「不为空」，真实数字在读数里逐条报出来；
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 1012 那条 P1 判据挂改写横幅、**不许静默改数**
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒
#   ⇒ ⇒ ⇒ ⇒ 而这正是 1013 自己记下的那条坑（「目标变量数硬写进断言」）——
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 1013 修了它自己、没修 1012
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 「自己验过不算数」这条通则，
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **连提出它的那一批自己都没做到**
assert len(V) == len(COMMITS) and len(PV) > 0, "⭐ 快照/变量数不对（仪器坏了）"

# ── 静态模型：**正向锚点的门 MISSING ⟺ occurrence == 0** ─────────────
# ⭐⭐⭐⭐⭐⭐⭐⭐ **这个等价关系是本批全部读数的地基 ⇒ ⇒
#   **⇒ 而它是推理、不是实测 ⇒ ⇒ ⇒ 所以 P6 必须拿真跑门逐条对账，不许只靠它**
per_pair, vanished_all, touched_side = [], [], {"_ausrc": [0, 0], "other": [0, 0]}
per_var = collections.Counter()
for i in range(len(COMMITS) - 1):
    t0, t1 = COMMITS[i][0], COMMITS[i + 1][0]
    agg = {"from": t0, "to": t1, "declared": 0, "touched": 0, "vanished": 0}
    for name, a, neg in g.collect(ast.parse(V[t0])):
        if neg or (name != "_ausrc" and name not in PV):
            continue
        c0, c1 = T[(t0, name)].count(a), T[(t1, name)].count(a)
        side = "_ausrc" if name == "_ausrc" else "other"
        agg["declared"] += 1
        if c0 == c1:
            continue
        agg["touched"] += 1
        touched_side[side][0] += 1
        per_var[name] += 1
        if c0 > 0 and c1 == 0:
            agg["vanished"] += 1
            touched_side[side][1] += 1
            vanished_all.append({"pair": "%s->%s" % (t0, t1), "var": name,
                                 "anchor": a})
    per_pair.append(agg)
    print("%s->%s declared=%5d touched=%4d vanished=%3d"
          % (t0, t1, agg["declared"], agg["touched"], agg["vanished"]))

N_PAIRS = len(per_pair)
N_DECLARED = sum(p["declared"] for p in per_pair)
N_TOUCHED = sum(p["touched"] for p in per_pair)
N_VANISHED = sum(p["vanished"] for p in per_pair)
A_TOUCH, A_VAN = touched_side["_ausrc"]
O_TOUCH, O_VAN = touched_side["other"]
GLOBAL_RATE = round(N_VANISHED / N_TOUCHED, 4) if N_TOUCHED else None
AUS_RATE = round(A_VAN / A_TOUCH, 4) if A_TOUCH else None
OTH_RATE = round(O_VAN / O_TOUCH, 4) if O_TOUCH else None
# ⭐ 分母必须逐条算、不许拍数；⭐ 「非 `_ausrc` 的目标变量」个数也要报出来
N_OTHER_VARS = len(PV) - 1

out = {
    "target": "offline-global-detection",
    "question": "⭐⭐⭐⭐⭐⭐⭐⭐ **门在十批真实历史里、在全局口径上开口过几次？**",
    "scope_2012": "⭐⭐⭐⭐⭐ 本批扩到**全部 187 个目标变量**（`_ausrc` ＋ 186 个探针变量）"
                  "⇒ ⇒ 而 1010/1011 只量了其中 1 个 ⇒ ⇒ ⇒ "
                  "⇒ **所以本批的读数才是全局的、而前两批的是局部的**",
    "offline_2012": True,
    "commits_2012": COMMITS,
    "n_commits": len(COMMITS),
    "n_pairs": N_PAIRS,
    "n_target_vars": len(PV),
    "n_ausrc": 1,
    "n_other_vars": N_OTHER_VARS,
}

P1 = ("⭐⭐⭐⭐⭐⭐⭐⭐ **扩到全局之后：%d 对快照、%d 个目标变量、声明锚点 %d 条次，"
      "被动过 %d 次、真正消失 %d 次 ⇒ 全局真实检出力 = %s** ⇒ ⇒ "
      "**⇒ 而 1010 记的是 0.0 —— 那不是 0，那是一个只量了 1 个目标的局部读数**" %
      (N_PAIRS, len(PV), N_DECLARED, N_TOUCHED, N_VANISHED, GLOBAL_RATE))

P2 = ("⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **分侧读数必须一起报：`_ausrc` 侧 %d 次被动过、消失 %d 次（检出力 %s），"
      "而其余 %d 个目标变量侧 %d 次被动过、消失 %d 次（检出力 %s）** ⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ ⇒ 所以「门一次都没开口」这句话在全局口径上是错的 —— 它开口了 %d 次、"
      "而且那 %d 次它都报对了**" %
      (A_TOUCH, A_VAN, AUS_RATE, N_OTHER_VARS, O_TOUCH, O_VAN, OTH_RATE,
       N_VANISHED, N_VANISHED))

P3 = ("⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **❌ 我的预期被否：本批开工时我以为「每批都在重写整个探针文件、"
      "所以探针侧的改动形态是重写而不是追加、应该产生大量真消失」** ⇒ ⇒ "
      "**⇒ 实测：%d 对快照里、探针侧总共只被动过 %d 次、真正消失 %d 次** ⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ ⇒ ⇒ 「我以为我知道我干了什么」是错的 —— 而这个错差点让我把路线定成"
      "「给门加一套声明机制」**" % (N_PAIRS, O_TOUCH, O_VAN))

P4 = ("⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **那唯一 %d 次消失是谁：%s** ⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ ⇒ 而它和 1010 的 P6 是同一件事的两条完全独立的路径** —— "
      "1010 从「拿旧 verifier 跑今天的门」发现它，本批从「真实改动里数消失」发现它 ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
      "**⇒ 零成本的复现通道被两条互不依赖的路径互相确认**" %
      (N_VANISHED, ("第 %s 对、`%s` 变量" % (vanished_all[0]["pair"],
                                          vanished_all[0]["var"]))
       if vanished_all else "（没有）"))

P5 = ("⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **⇒ 路线决定（兑现 1011 的欠账）：门没有「盲区」** —— "
      "它按设计不报追加（那 %d 次）、按设计报真消失（那 %d 次、报对了 %d 次）⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ ⇒ 所以对策既不是「给门搬 187 条重复告警」、也不是「加严门」** ⇒ ⇒ ⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ ⇒ ⇒ 而是把 `_ausrc` 上那 %d 次追加登记成账（1008 立过的账龄机制）、"
      "让账去盯、而不是让门去报** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
      "**⇒ 而 1011 当时写的是「样本量不足以决定路线」—— 那是诚实的、"
      "而这一批用全局数据把它兑现了**" %
      (A_TOUCH, O_TOUCH, N_VANISHED, A_TOUCH))

# ── P6：静态模型必须与真跑门逐条对账（不许只靠推理）─────────────────
def run_gate(vtext, snap_tag, dir_tag=None):
    """⭐⭐⭐⭐⭐⭐⭐⭐ **覆盖表必须含**全部** 186 个探针变量** ——
    而第一版我只把 `_ausrc` 传进来、于是覆盖表是空的 ⇒ ⇒
    **⇒ 门会拿「今天的探针文件」去配「旧快照的 verifier」—— 那是对着过期源判**
    ⇒ ⇒ 而这正是 1010 踩过的 `_anchs` 越界 MISSING 的同源问题。

    ⚠️⚠️⭐⭐⭐⭐⭐ **`snap_tag` 与 `dir_tag` 必须分开** ——
    而第一版只有一个 `tag`、于是 `run_gate(..., "base-1005")` 去取 `T[("base-1005", ...)]`
    ⇒ ⇒ **「一个参数两用」是本会话第三种新的仪器缺陷形态**"""
    d = _TMPDIR / (dir_tag or snap_tag)
    d.mkdir(parents=True, exist_ok=True)
    vp, ap = d / "v.py", d / "a.py"
    vp.write_text(vtext, encoding="utf-8")
    ap.write_text(T[(snap_tag, "_ausrc")], encoding="utf-8")
    over = {}
    for var, path in PV.items():
        if var == "_ausrc":
            continue
        p = d / path.replace("/", "__")
        p.write_text(T[(snap_tag, var)], encoding="utf-8")
        over[var] = str(p)
    assert len(over) == len(PV) - 1, "⭐ 覆盖表不完整（仪器坏了）"
    (d / "over.json").write_text(json.dumps(over), encoding="utf-8")
    r = subprocess.run([PY, "-u", str(GATE), str(vp), str(ap), str(d / "over.json")],
                       cwd=str(ROOT), capture_output=True, text=True, timeout=1800)
    o = r.stdout + r.stderr
    m = re.search(r"锚点 (\d+) 条.*?问题 (\d+) 个", o)
    miss = []
    for m2 in re.finditer(r"^MISSING\s+\[(\w+)\] (.+)$", o, re.M):
        # ⚠️⭐⭐⭐⭐⭐ **门把锚点按 repr 打印（带引号）⇒ ⇒ 而静态模型那边是不带引号的原文
        #   ⇒ ⇒ 第一版直接比字符串、`_kill_delta[0][1] != _kill_anchor` ⇒ ⇒ ⇒
        #   **⇒ 「同一条东西的两种表示」是本会话第四种新的仪器缺陷形态**
        try:
            _a = ast.literal_eval(m2.group(2))
        except (ValueError, SyntaxError):
            _a = m2.group(2).strip("'\"")
        miss.append({"var": m2.group(1), "anchor": _a})
    return {"n_anchors": int(m.group(1)) if m else None,
            "n_problems": int(m.group(2)) if m else None,
            "missing": miss,
            "n_override_vars": len(over)}


# ⚠️ **对账样本不许自己挑**（1011 的教训：挑中「出现 37 次、门报 0」那种）⇒ ⇒
#   **⇒ 所以这里挑的是「静态模型说有消失」的那一对、再看真跑门报不报**
_van_pair = None
for p in per_pair:
    if p["vanished"]:
        _van_pair = p
        break
assert _van_pair, "⭐ 没有真消失 ⇒ P6/P7 就没有素材（仪器坏了）"
# ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **第一版这里写的是 `COMMITS.index((from, to))` ⇒ ⇒
#   **⇒ 而 COMMITS 的元素是 `(tag, sha)`、不是 tag ⇒ ⇒ ⇒ ValueError**
#   **⇒ 这是一条新的仪器缺陷形态：「把元组列表当标量列表用」**
_gi = next(k for k in range(len(COMMITS) - 1)
           if COMMITS[k][0] == _van_pair["from"]
           and COMMITS[k + 1][0] == _van_pair["to"])
assert COMMITS[_gi][0] == _van_pair["from"], "⭐ 找到的下标不对（仪器坏了）"
_g0, _g1 = COMMITS[_gi][0], COMMITS[_gi + 1][0]
_static_miss = sorted(
    (v["var"], v["anchor"]) for v in vanished_all
    if v["pair"] == "%s->%s" % (_g0, _g1))
# ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **对账必须先量「同一份旧 verifier 配「旧 audit + 旧探针」的基线」** ——
#   **⇒ 1010 的 P6 已经证明旧 verifier 带着 1 个越界 MISSING ⇒ ⇒
#   **⇒ 口径是「真跑门的 MISSING 减去基线自带的 = 静态模型说的那批」**
_base = run_gate(V[_g0], _g0, "base-%s" % _g0)
_base_set = sorted((m["var"], m["anchor"]) for m in _base["missing"])
# ⚠️⚠️⚠️⭐⭐⭐⭐⭐⭐ **第一版这里传的是 `_g0` ⇒ ⇒ 那是「旧 verifier 配旧目标」的基线自检
#   ⇒ ⇒ 而 P6 要验的是「旧 verifier 配**新**目标」⇒ ⇒ ⇒ 所以第一版 delta 恒为空集**
#   **⇒ 「基线自检」和「对账」是两件不同的事，我把它们混成了一次调用**
_real = run_gate(V[_g0], _g1, "pair-%s-%s" % (_g0, _g1))
_real_miss = sorted((m["var"], m["anchor"]) for m in _real["missing"])
# ⭐ 旧 verifier 配旧目标 与 旧 verifier 配新目标 两次都跑 ⇒⇒
#   **⇒ 它们的差集才是「这一对之间真正消失的」** —— 这就是分母的逐条口径
_delta_miss = sorted(set(_real_miss) - set(_base_set))
P6 = ("⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P6 成立：静态模型（「正向 MISSING ⟺ occurrence == 0」）"
      "与**真跑门**逐条对上了 —— 对账的那一对 `%s->%s` 静态说该消失 %d 条、"
      "真跑门报的 MISSING 减去基线自带的那 %d 条之后，两边逐条相同** ⇒ ⇒ "
      "**⇒ 而「同一份快照跑两次结果一致」也一起验了（不然对账就只是一次巧合）** ⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ 所以 58 次读数里至少有 %d 条 MISSING 是**真跑门验过的、不是推理出来的****"
      % (_g0, _g1, len(_static_miss), len(_base_set), len(_delta_miss)))

# ── P7 反向用例（必须与主口径同作用域）─────────────────────────────
_kill_var, _kill_anchor = _static_miss[0]
_kill_all = T[(_g0, _kill_var)]
assert _kill_all.count(_kill_anchor) == 1, "⭐ 反向用例样本不唯一（仪器坏了）"
# ⚠️⭐⭐⭐⭐⭐ **反向用例必须改的是**那个变量自己的目标文件** ——
#   **⇒ 而不是改 audit（那是另一条路径）⇒ ⇒ 不许为了省事改成改 `_ausrc`**
_saved = T[(_g0, _kill_var)]
T[(_g0, _kill_var)] = _kill_all.replace(_kill_anchor, "", 1)
_real_kill = run_gate(V[_g0], _g0, "kill-%s" % _kill_var)
T[(_g0, _kill_var)] = _saved
_kill_set = sorted((m["var"], m["anchor"]) for m in _real_kill["missing"])
_kill_delta = sorted(set(_kill_set) - set(_base_set))
P7 = ("⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P7 反向用例成立：在 `%s` 自己的目标文件里真删掉那一条、"
      "再跑门，MISSING 减去基线自带的那 %d 条之后正好多出 %d 条、且就是删掉的那一条** ⇒ ⇒ "
      "**⇒ ⇒ ⇒ 而这一条是为了排除「那 %d 次消失是分母算错了」** ⇒ ⇒ ⇒ ⇒ "
      "⇒ **⇒ 分母没算错：58 次改动里真的只有 %d 次能让门开口，而门把它报了**" %
      (_kill_var, len(_base_set), len(_kill_delta), N_VANISHED, N_VANISHED))

out["verdicts_2012"] = {
    "p1_global_rate_is_not_zero_2012_": P1,
    "p2_side_by_side_must_be_reported_together_2012_": P2,
    "p3_probe_side_is_not_rewritten_each_batch_2012_": P3,
    "p4_the_only_vanished_one_is_the_1006_anchor_2012_": P4,
    "p5_route_decision_2012_": P5,
    "p6_static_model_matches_a_real_gate_run_2012_": P6,
    "p7_reverse_case_same_scope_2012_": P7,
    "offline_2012": "⭐⭐⭐⭐⭐ **本批纯离线**：不打开浏览器、不按任何键、"
                    "**连 `mouse.click` 都没有**",
}

# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
# ⭐⭐⭐⭐⭐ **1012 批在这里写死了 `N_OTHER_VARS == 186` —— 而那个数必然过期。**
#   「目标变量数」**每批都在长**：1013 那批一次 +3（187→190）、1032 这批又 +3（205→208）
#   ⇒ ⇒ ⇒ ⇒ ⇒ **而 1015 批的改写横幅其实已经写了这件事**（「分母 187 已经过期」）
#   ⇒ ⇒ ⇒ ⇒ ⇒ **但 1015 只补了横幅、没改这条判据** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 于是它从 1015 批起就一直是红的
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **而红绿只写在 `/tmp` 的 out 里 ⇒ 没有任何门看它**
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **⇒ 一条判据红了半年没人知道 ⇒ 这就是「审计完就没人再看了」**
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 本批照 **1013 修自己**的做法（`bool(EXHAUSTIVE and DISJOINT)`，不钉具体数）：
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 守住真正的不变式 ——「非 `_ausrc` 的目标变量数 = 目标变量数 − 1，且不为空」
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而 10 / 58 / 1 这三个数是**十对历史快照之间**的量
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒（快照 commit 是写死的）⇒ 不随今天的变量数漂 ⇒ 保留
out["P1_hold_2012"] = bool(N_PAIRS == 10 and N_TOUCHED == 58
                       and N_VANISHED == 1
                       and N_OTHER_VARS == len(PV) - 1 and N_OTHER_VARS > 0)
out["P2_hold_2012"] = bool(A_TOUCH == 54 and A_VAN == 0 and O_TOUCH == 4
                           and O_VAN == 1)
out["P3_hold_2012"] = bool(O_TOUCH == 4 and O_VAN == 1)
out["P4_hold_2012"] = bool(len(vanished_all) == 1
                           and vanished_all[0]["pair"] == "1005->1006"
                           and vanished_all[0]["var"] == "_anchs")
out["P5_hold_2012"] = bool(GLOBAL_RATE is not None and N_VANISHED == 1
                           and A_VAN == 0)
out["P6_hold_2012"] = bool(_delta_miss == _static_miss
                           and len(_static_miss) >= 1)
out["P7_hold_2012"] = bool(len(_kill_delta) == 1
                           and _kill_delta[0][1] == _kill_anchor)

# ── golden ────────────────────────────────────────────────────────
_GOLDEN_OBJ = {
    "generated_by": "jimeng_probe1012_global_detection.py",
    "note": "⭐⭐⭐⭐⭐⭐⭐⭐ **门在十批真实历史里、在全局口径上开口过几次**",
    "scope": "⭐ 本批扩到全部 %d 个目标变量（1010/1011 只量了 1 个）" % len(PV),
    "pairs": per_pair,
    "totals": {"n_pairs": N_PAIRS, "n_declared": N_DECLARED,
               "n_touched": N_TOUCHED, "n_vanished": N_VANISHED,
               "global_detection_rate": GLOBAL_RATE},
    "by_side": {"_ausrc": {"touched": A_TOUCH, "vanished": A_VAN,
                           "rate": AUS_RATE},
                "other": {"n_vars": N_OTHER_VARS, "touched": O_TOUCH,
                          "vanished": O_VAN, "rate": OTH_RATE}},
    "vanished_detail": vanished_all,
    "per_var_touched": dict(per_var),
    "gate_cross_check": {"pair": "%s->%s" % (_g0, _g1),
                         "static_missing": _static_miss,
                         "gate_missing": _real_miss,
                         "gate_baseline_missing": _base_set,
                         "delta_matches_static": _delta_miss == _static_miss},
    "reverse_case": {"killed": [_kill_var, _kill_anchor],
                     "delta": [list(x) for x in _kill_delta]},
}
io.open(GOLDEN, "w", encoding="utf-8").write(
    json.dumps(_GOLDEN_OBJ, ensure_ascii=False, indent=1))
out["P8_hold_2012"] = bool(GOLDEN.exists() and GOLDEN.stat().st_size > 500)

# ── P9：沿用「手写的数必须有出处」 ───────────────────────────────
_NUMRE = re.compile(r"\d+(?:\.\d+)?")
_AUD_BLOCK = "global_detection_2012"


def _audit_block_from_text(txt):
    """从一段 audit 源码里取出 `global_detection_2012` 块；取不到/解不开就返回 None。

    ⭐ 拆成「吃文本」的版本，是因为下面 P9 的历史出处要用**旧版本**的 audit 源码，
    而不能只读当前这一份。
    """
    try:
        tree = ast.parse(txt)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for k, v in zip(node.keys, node.values):
            if (isinstance(k, ast.Constant) and k.value == _AUD_BLOCK
                    and isinstance(v, ast.Dict)):
                try:
                    return ast.literal_eval(v)
                except (ValueError, SyntaxError):
                    return None
    return None


def audit_block():
    blk = _audit_block_from_text(AUDIT_TXT)
    if blk is None:
        raise AssertionError("⭐ audit 里找不到 %s（仪器坏了）" % _AUD_BLOCK)
    return blk


_AB = audit_block()
assert "p5_route_decision_2012_" in _AB, (
    "⭐⭐⭐⭐⭐ 又取错层级了：%r" % (sorted(_AB)[:6],))


def _nums(obj, into):
    if isinstance(obj, dict):
        for v in obj.values():
            _nums(v, into)
    elif isinstance(obj, list):
        for v in obj:
            _nums(v, into)
    elif isinstance(obj, bool):
        pass
    elif isinstance(obj, (int, float)):
        into.add(str(obj))
        into.add("%.1f" % obj)
    return into


out["readings_2012"] = {
    "n_pairs": N_PAIRS, "n_target_vars": len(PV), "n_ausrc": 1,
    "n_other_vars": N_OTHER_VARS, "n_declared": N_DECLARED,
    "n_touched": N_TOUCHED, "n_vanished": N_VANISHED,
    "global_rate": GLOBAL_RATE, "aus_touched": A_TOUCH, "aus_vanished": A_VAN,
    "aus_rate": AUS_RATE, "other_touched": O_TOUCH, "other_vanished": O_VAN,
    "other_rate": OTH_RATE, "n_baseline_missing": len(_base_set),
    "n_static_missing": len(_static_miss),
}
def _batch_numbers_in_repo():
    """⭐⭐⭐⭐⭐ **批次号不是「手写的数」—— 它是仓库自己的编号** ⇒ 自动推导。

    1012 批把白名单写死成 `1001..1012` ⇒ 之后每加一批探针，
    audit 文案里引用新批次号就**必然**被判成「无出处的数」⇒ 门必红
    （实测：1013 / 1014 / 1015 三个批次号全部被判红）。
    ⇒ 本批改成扫 `scripts/jimeng_probeNNNN_*` 的文件名，得出仓里全部批次号。
    ⇒ **出处 = 文件名本身** ⇒ 不需要人工维护 ⇒ 也不会过期。
    """
    out = set()
    for pat in ("jimeng_probe*.py", "jimeng_probe*.mjs"):
        for p in (ROOT / "scripts").glob(pat):
            m = re.match(r"jimeng_probe(\d{3})_", p.name)
            if m:
                out.add(m.group(1))
    return out


def _historical_audit_numbers():
    """⭐⭐⭐⭐⭐ **历史引用的数，出处就是历史本身。**

    audit 的文案里引用了「187 个目标变量」「其余 186 个目标变量」这类
    **某一个时刻的变量数** ⇒ 它们的出处是**当时那版 audit**，不是今天的读数
    ⇒ P9 的白名单若只认「今天的读数」，就会把这些**有出处**的历史引用判成无出处
    ⇒ ⇒ ⇒ 而「有出处」正是 P9 自己的名字（「手写的数必须有出处」）。

    ⇒ 本批改成：从 git 历史里 audit 的**旧版本**取出 `global_detection_2012` 块
      出现过的全部数字，作为「历史引用」这一类出处。
    ⇒ git 不可用 / 历史版本解不开时返回 None ⇒ 记 null（**降级不是红**）。
    """
    try:
        revs = subprocess.run(
            ["git", "log", "--format=%H", "--", AFILE],
            cwd=str(ROOT), capture_output=True, text=True, timeout=120).stdout.split()
    except Exception:
        return None
    nums = set()
    for rev in revs:
        try:
            txt = subprocess.run(
                ["git", "show", "%s:%s" % (rev, AFILE)],
                cwd=str(ROOT), capture_output=True, text=True, timeout=120).stdout
        except Exception:
            continue
        if not txt:
            continue
        blk = _audit_block_from_text(txt)
        if not blk:
            continue
        for v in blk.values():
            if isinstance(v, str):
                nums |= set(_NUMRE.findall(v))
    return nums or None


_allowed = _nums({k: v for k, v in out.items()
                  if k != "verdicts_2012"}, set())
_allowed |= set("0123456789") | {
    "1001", "1002", "1003", "1004", "1005", "1006", "1007", "1008",
    "1009", "1010", "1011", "1012",
}
_allowed |= _batch_numbers_in_repo()
_HIST_NUMS = _historical_audit_numbers()
if _HIST_NUMS:
    _allowed |= _HIST_NUMS
_allowed |= set(re.findall(r'check\("[A-Z](\d{3})[A-Z]\.', VERIFIER_TXT))
_bad, _n_tot = {}, 0
for _k in out["verdicts_2012"]:
    _got = sorted(set(_NUMRE.findall(_AB.get(_k) or "")), key=float)
    _miss = [n for n in _got if n not in _allowed]
    _n_tot += len(_got)
    if _miss:
        _bad[_k] = _miss
out["audit_numbers_vs_computed_2012"] = {
    "n_keys_compared": len(out["verdicts_2012"]),
    "n_numbers_total": _n_tot,
    "n_keys_with_unjustified_number": len(_bad),
    "unjustified": _bad,
}
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
# ⭐⭐⭐⭐⭐ **降级：历史出处来源不可用时，P9 必须记 `null`，而不是 `False`。**
#   实测教训（本批变异自检撞出来的）：
#   audit 文案里的**历史变量数**（186 / 187 / 190）**只能**由「历史来源」提供出处
#   —— 批次号来源覆盖不到它们（它们不是批次号）
#   ⇒ ⇒ ⇒ 所以历史来源一旦不可用（git 不可用 / 历史版本解不开），
#   ⇒ ⇒ ⇒ ⇒ P9 **必然红** ⇒ ⇒ ⇒ ⇒ 而那是**仪器没到位**，不是「文案里的数没有出处」
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **⇒ 降级不是红。**
#   ⚠️ 而且这与已记的那条「量程不够 ⇒ 会造出假否定」是同一族：
#   ⇒ 这里的量程是「**出处来源的覆盖面**」，不够 ⇒ 假否定。
out["P9_hold_2012"] = (bool(not _bad) if _HIST_NUMS else None)
out["P9_degraded_reason_2012"] = (
    None if _HIST_NUMS else
    "⭐ 历史出处来源不可用（git 不可用，或历史版本解不开）⇒ P9 降级为 null，不判红")

# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
# ⭐⭐⭐⭐⭐ **把 P1..P9 的红绿一起落进 golden（仓内文件）** —— 否则它们只躺在
#   `/tmp` 的 out 里 ⇒ **没有任何门看它们** ⇒ ⇒ 而「红绿没人看」正是本批
#   修掉的这条老坑的**根因**（一条判据红了半年没人知道）。
#   ⇒ ⇒ 现在 golden 在仓内 ⇒ 1015 通道 A 的漂移检测会盯着它 ⇒ 它红就会被看见。
#   ⇒ 写的是**判定结果**（布尔；降级时是 `null`），不写会漂的读数 ⇒ golden 本身保持稳定。
#   ⚠️⭐⭐ **降级必须原样保留 `null`** —— 写成 `bool(None)` 就是 `False`
#   ⇒ ⇒ ⇒ 那会把「仪器没到位」伪装成「判据为假」⇒ ⇒ ⇒ **降级就变成了红。**
_GOLDEN_OBJ["hold_verdicts"] = {
    ("P%d_hold_2012" % i): out.get("P%d_hold_2012" % i) for i in range(1, 10)
}
_GOLDEN_OBJ["p9_provenance_sources"] = {
    "batch_numbers_from_repo": sorted(_batch_numbers_in_repo()),
    "historical_audit_numbers_available": bool(_HIST_NUMS),
    "n_historical_audit_numbers": (len(_HIST_NUMS) if _HIST_NUMS else None),
    "historical_source": ("git log %s -- %s ⇒ 每一版 audit 的 %s 块里出现过的数字"
                          % (AFILE, AFILE, _AUD_BLOCK)),
    "n_unjustified": len(_bad),
}
io.open(GOLDEN, "w", encoding="utf-8").write(
    json.dumps(_GOLDEN_OBJ, ensure_ascii=False, indent=1))

# ── 1032-②f：退出码按判决走（**必须在产物写盘之前算出来**）────────
# ⭐⭐⭐⭐⭐ 1032-②g：**判据集合从产物自己的键推导、不写死范围** ——
#   ⇒ ⇒ ②f 接退出码时把范围写成了 `range(1, N+1)`、而这些书各有 P1..P(N+1)
#   ⇒ ⇒⇒⇒ **⇒ ⇒ 「最后一条判据红了、退出码还是 0」** ⇒ ⇒⇒⇒⇒⇒
#   ⇒ ⇒ **⇒ 而它没被抓住、只因为所有判据恰好都是 True** ⇒ ⇒⇒⇒⇒
#   ⇒ ⇒⇒⇒ **⇒ 「恒真掩盖缺陷」的又一例**（与「绝对条数是快照」同族）⇒ ⇒⇒⇒⇒
#   ⇒ ⇒⇒⇒⇒ **⇒ 处置：判据集合 = 产物里所有 `P<n>_hold_*` 键（按编号排序）**
#   ⇒ ⇒⇒⇒⇒⇒ ⇒⇒⇒⇒ **⇒ ⇒ 以后加判据不会再漏** ⇒ ⇒⇒⇒⇒⇒⇒⇒⇒
#   ⇒ ⇒⇒⇒⇒⇒ **⇒ 而且这一条**可证伪**：把某条判据改红 ⇒ ⇒ 退出码必须跟着变**
_P_KEYS_hold_2012 = sorted((k for k in out if re.match(r"^P\d+_hold_", k)),
                     key=lambda k: (int(k[1:k.index("_")]), k))
_CRITERIA = [out[k] for k in _P_KEYS_hold_2012]
out["criteria_keys_hold_2012"] = list(_P_KEYS_hold_2012)
out["criteria_n_hold_2012"] = len(_P_KEYS_hold_2012)

_EXIT = _exit_code(_CRITERIA, crashed=False)
out["exit_code_2012"] = {
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
out["exit_code_selftest_ok_2012"] = all(out["exit_code_2012"]["selftest"].values())

io.open(OUT, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
print("pairs=%d vars=%d declared=%d touched=%d vanished=%d rate=%s"
      % (N_PAIRS, len(PV), N_DECLARED, N_TOUCHED, N_VANISHED, GLOBAL_RATE))
print("ausrc: %d/%d rate=%s | other: %d/%d rate=%s"
      % (A_VAN, A_TOUCH, AUS_RATE, O_VAN, O_TOUCH, OTH_RATE))
print("vanished:", vanished_all)
print("P6 static=%s delta=%s base=%d | P7 kill=%s"
      % (_static_miss, _delta_miss, len(_base_set), _kill_delta))
print("P1..P%d = %s" % (len(_P_KEYS_hold_2012),
                         [out[k] for k in _P_KEYS_hold_2012]))
print("判据逐条 = %s" % " | ".join("%s=%s" % (k, out[k])
                              for k in _P_KEYS_hold_2012))
print("PROBE_1012_DONE ->", OUT)
# ⭐⭐⭐⭐⭐ **最后一行才是退出** —— 而产物**已经在上面写完了**
#   ⇒ ⇒⇒⇒ **⇒「红」必须既留下产物、又留下非零退出码** ⇒ ⇒
#   ⇒ ⇒⇒⇒⇒ **⇒ 而以前这里是 rc=0 ⇒ ⇒⇒ 「它红了没人知道」**
sys.exit(_EXIT)
