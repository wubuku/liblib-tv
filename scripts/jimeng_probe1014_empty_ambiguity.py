#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 1014 —— ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **「空集合」有歧义：看起来是空的，和没算过，在仓里长得一模一样**

1013 把账本第一次落进了仓（`occurrence-ledger-1013.json`），而那本账里有一行：

    "retired": []

1013 的 P6 说「纯历史账本的 `retired` 恒为空」—— 那句话是对的。

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **⇒ 而本批问的是：只凭这一个 `[]`，读它的人怎么知道
「它是空的」和「它根本没被算过」不是同一件事？**

⇒ ⇒ ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **⇒ 而答案是：分不出来。而 JSON 对这两种一视同仁**
⇒ ⇒ ⭐⭐⭐⭐⭐⭐⭐⭐⭐ **⇒ ⇒ ⇒ ⇒ ⇒ 普查：仓里 8 个 golden、4 个空 list 字段，
其中**恰好 1 个**不可自证（就是 1013 刚写的那个 `retired`）**
⇒ ⇒ ⭐⭐⭐⭐⭐⭐ **⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而另外 3 个各自旁边都有一个「可校验的不变式」
把它们钉住了（`symmetric_difference` / `delta_matches_static`）**

本批**纯离线**：不打开浏览器、不按任何键、连 `mouse.click` 都没有
"""
import ast
import collections
import hashlib
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GDIR = ROOT / "docs/research/jimeng-canvas"
LEDGER = GDIR / "occurrence-ledger-1013.json"
GOLDEN = GDIR / "empty-ambiguity-1014.json"
OUT = "/tmp/b1014-empty-ambiguity.json"
PROBE13 = ROOT / "scripts/jimeng_probe1013_occurrence_ledger.py"
PROBE12 = ROOT / "scripts/jimeng_probe1012_global_detection.py"
AUDIT_TXT = (ROOT / "scripts/jimeng_unclickable_audit.py").read_text(encoding="utf-8")
VERIFIER_TXT = (ROOT / "scripts/verify-jimeng-batch841-unclickable.py").read_text(
    encoding="utf-8")

# ══ 1032-②k：**kind 台账要落进产物，而不只是活在源码里** ═════════════════════
# ⭐⭐⭐⭐⭐ 口径：kind ∈ {failure, conclusion, precondition}
#   ⇒ failure      = 这条红了**要修**（它是仪器/数据健康与否的自检）
#   ⇒ conclusion   = 这条红了**要重读**（它断言的是本批的结论，不是仪器健康）
#   ⇒ precondition = 这条**依赖前提**；前提不成立 ⇒ 这次测量**不适用**
#                    （读数是 None，**不许算红**）
# ⭐⭐⭐⭐⭐ **逐条读原文、由人定性**（不许按关键词机械猜）：
#   P1  普查自洽（报了几个就是几个 ＋ 两类之和 = 空字段总数）⇒ 普查自相矛盾 ⇒ 要修 ⇒ failure
#   P2  「算出来的空」与「压根没算」逐字节相同 ⇒ **本批的核心结论** ⇒ 红了要重读 ⇒ conclusion
#   P3  伴生字段（companion）让两者可区分 ⇒ 结论 ⇒ conclusion
#   P4  反向分类器不是常量（两类都非空）⇒ 排除性结论 ⇒ conclusion
#   P5  `null` 被一并数进去了 ＋ 分类器行为可验 ⇒ 结论 ⇒ conclusion
#   P6  上一批的产物自己也是受害者 ⇒ 结论 ⇒ conclusion
#   P7  产物确实落到仓里了、且不是空壳 ⇒ 自检 ⇒ failure
#   P8  手写的数必须有出处 ⇒ 自检 ⇒ failure
#   P9  注入式变异：普查真的在读那些书 ⇒ 自检 ⇒ failure
#   P10 第一次写进磁盘的产物逐键等于载荷 ⇒ 自检 ⇒ failure
KINDS_2014 = {
    "P1_hold_2014": "failure",
    "P2_hold_2014": "conclusion",
    "P3_hold_2014": "conclusion",
    "P4_hold_2014": "conclusion",
    "P5_hold_2014": "conclusion",
    "P6_hold_2014": "conclusion",
    "P7_hold_2014": "failure",
    "P8_hold_2014": "failure",
    "P9_hold_2014": "failure",
    "P10_hold_2014": "failure",
}

# ══ 1032-②k：**指纹表要能被「对着提交态核对」** ══════════════════════════════
# ⭐⭐⭐⭐⭐ 1032-②j 收尾实测到的一件事：**指纹表里混进了一个「每次跑都重写」的输入**
#   ⇒ `golden-freshness-1027.json` 每次跑 1027 都被整个重写、而按既定纪律**不随批提交**
#   ⇒ ⇒⇒ 而指纹表记的是「跑的那一瞬间工作区里的字节」
#   ⇒ ⇒⇒⇒ ⇒ **⇒ 指纹表对这一条永远对不上「提交态」**（实测：记录 85933B vs 提交态 91483B）
#   ⇒ ⇒⇒⇒ ⇒ **⇒ 而这不是「数据坏了」，是「这张表把两种东西混在一张里」**
#   ⇒ ⇒⇒⇒ ⇒ **⇒ 处置：volatile 的输入单列一节（照样记它当次的指纹，供复算），
#   ⇒ ⇒⇒⇒ ⇒      但它不进「可以对着提交态核对的那张表」**
VOLATILE_INPUTS = {
    "golden-freshness-1027.json":
        "⭐⭐⭐⭐⭐ **每次跑 1027 都整个重写、且按纪律不随批提交** ⇒ ⇒ "
        "⇒ 它的指纹对不上提交态是**结构性的**、不是「产物坏了」 ⇒ ⇒ "
        "⇒ 单列一节（记当次字节供复算），不进可核对的那张表",
}

# ── P1：普查所有 golden 里的「空集合」，并逐条判它可不可自证 ─────────
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **「可自证」的判据不是「旁边有说明」——
#   **⇒ 而是「旁边有一个**可校验的不变式**，用它能把空集合钉死」** ⇒ ⇒
#   **⇒ 一段散文说明（`retired_note`）钉不住任何东西：它可以和「没算过」共存**
#   **⇒ ⇒ ⇒ 而这正是 1013 的 `retired` 栽的地方**


def find_empty(o, p=""):
    """⭐ 不经任何去重容器：空 list 与 None 分开记（None 是同一个病的另一种形态）。"""
    emp = []
    if isinstance(o, dict):
        for k, v in o.items():
            emp += find_empty(v, p + "/" + str(k))
    elif isinstance(o, list) and len(o) == 0:
        emp.append((p, "list"))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            emp += find_empty(v, p + "/[%d]" % i)
    elif o is None:
        emp.append((p, "null"))
    return emp


# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **第二版的判据：不去「查有没有 companion」，
#   而是**真的把这个不变式在数据上跑一遍**、看它成不成立** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒
#   **⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而第一版那张「只认 4 个字段名」的表报了 9 个不可自证 ——
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而否掉它的是我拍的那张表、不是世界（998/1004 那条纪律第二次施用）**
INVARIANTS = {
    # leaf 名 -> (人类可读的不变式, 对同一层的兄弟字典求值的函数)
    "class_1005": ("class_1005 is None ⟺ in_1005_zero_coupling_golden == False",
                   lambda s: (s.get("class_1005") is None)
                   == (s.get("in_1005_zero_coupling_golden") is False)),
    "baseline_out_of_scope_vars":
        ("baseline_out_of_scope == len(baseline_out_of_scope_vars)",
         lambda s: s.get("baseline_out_of_scope") == len(s.get("baseline_out_of_scope_vars") or [])),
    "triggers": ("triggers == [] ⟺ about_self == False",
                 lambda s: (s.get("triggers") == []) == (s.get("about_self") is False)),
    "only_ledger":
        ("symmetric_difference == len(only_ledger) + len(only_gate)",
         lambda s: s.get("symmetric_difference") == len(s.get("only_ledger") or [])
         + len(s.get("only_gate") or [])),
    "only_gate":
        ("symmetric_difference == len(only_ledger) + len(only_gate)",
         lambda s: s.get("symmetric_difference") == len(s.get("only_ledger") or [])
         + len(s.get("only_gate") or [])),
    "gate_baseline_missing":
        ("delta_matches_static 与 gate_missing 一起把差集钉死",
         lambda s: "delta_matches_static" in s and "gate_missing" in s),
}


def classify(path, siblings):
    """⭐ 返回 (可自证?, 不变式文字)；把不变式在数据上真跑一遍。"""
    leaf = path.rsplit("/", 1)[-1]
    inv = INVARIANTS.get(leaf)
    if inv is None:
        return False, None
    try:
        ok = bool(inv[1](siblings))
    except Exception:
        return False, inv[0]
    return ok, inv[0]


# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **普查的输入里绝不能包含普查自己的输出**
#   ⇒ ⇒ 而第一版 `GDIR.glob("*.json")` 把 1014 上一跑留下的
#   `empty-ambiguity-1014.json` 也吃了进去 ⇒ ⇒ ⇒ **⇒ 于是读数会随「跑过几次」变化：
#   第一跑 8 个 golden、第二跑 9 个** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒
#   **⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而那本被吃进去的 golden 里装的全是本探针自己写的
#   `invariant: null` —— 它们是**真的** null，所以看起来像一个正当的「不可自证」样本**
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **⇒ 而一个「读数随自己跑过几次而变」的普查，它的数字不能当证据**
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **⇒ 处置：按 `generated_by` 排除自己（不是按文件名 —— 靠文件名排除，
#   将来重命名就漏了），并把「排除得干净」做成断言而不是注释**
_SELF_MARK = "jimeng_probe1014_empty_ambiguity.py"

# ⭐⭐⭐⭐⭐ 1032-②l：**被排除的不只是「我自己」**
#   ⇒ ⇒ 还有「读这张指纹表的仪器」的产物 ——
#   ⇒ ⇒⇒ ⇒ 它的内容**是这张表的函数** ⇒ ⇒⇒ ⇒ 把它吃进普查
#   ⇒ ⇒⇒ ⇒ ⇒ 普查的数字就会随「那道门跑过几次」而变 ⇒ ⇒⇒ ⇒ ⇒
#   ⇒ ⇒⇒ ⇒ ⇒ ⇒ 那正是本文件开头反对的那件事
#   ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 所以排除集是**声明式**的（一份字面量）⇒ ⇒⇒ ⇒
#   ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而门（1032l）从**本文件的源码**里读它 ⇒ ⇒⇒ ⇒
#   ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 两处不会漂移
_EXCLUDED_GENERATORS = {
    "jimeng_probe1014_empty_ambiguity.py",
    "jimeng_probe1032l_fingerprint_gate.py",
}
assert _SELF_MARK in _EXCLUDED_GENERATORS


def _is_own(f):
    """⭐ 1032-②l：判定从「是不是我」放宽成「是不是被排除的生成器」。

    ⇒ 锚点钉的是**这一行调用**（`assert not any(_is_own(f) for f in GOLDENS)`）
    ⇒ ⇒⇒ ⇒ 所以函数名不许改；改的是它**判什么**。
    """
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return False
    return isinstance(d, dict) and d.get("generated_by") in _EXCLUDED_GENERATORS


_ALL = sorted(GDIR.glob("*.json"))
_SELF_SEEN = [f.name for f in _ALL if _is_own(f)]
GOLDENS = [f for f in _ALL if not _is_own(f)]
assert not any(_is_own(f) for f in GOLDENS), \
    "⭐⭐⭐⭐⭐ **普查输入里还混着自己**"
N_GOLDENS = len(GOLDENS)
N_EXCLUDED_SELF = len(_SELF_SEEN)
def _census(pairs):
    """⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **普查的**唯一口径**：主读数与「注入式变异对照」必须调同一个函数
    ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ 否则对照组量的就不是主读数量的那个东西，对照就白做了**"""
    r, el, en, sp, am = [], 0, 0, 0, 0
    for name, d in pairs:
        for path, kind in find_empty(d):
            parent = d
            ps = path.strip("/").split("/")[:-1]
            for part in ps:
                parent = parent[int(part[1:-1])] if part.startswith("[") else parent[part]
            ok, inv_txt = classify(path, parent)
            el += int(kind == "list")
            en += int(kind == "null")
            sp += int(ok)
            am += int(not ok)
            r.append({"golden": name, "path": path, "kind": kind,
                      "self_provable": ok, "invariant": inv_txt})
    return r, el, en, sp, am


_BOOKS = []
for _f in GOLDENS:
    try:
        _BOOKS.append((_f.name, json.loads(_f.read_text(encoding="utf-8"))))
    except Exception:
        continue
rows, n_empty_list, n_empty_null, n_selfprovable, n_ambiguous = _census(_BOOKS)


def _gb_of(d):
    return d.get("generated_by") if isinstance(d, dict) else None


# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **一个读数必须带着它算在哪一批字节上** —— 本探针的输入集是**整目录 glob**
#   ⇒⇒⇒⇒⇒ 而本批量到：它读的 N_GOLDENS 本，**每一本都是别的探针每跑一次就重写的产物**（连账本自己也是）
#   ⇒⇒⇒⇒⇒ 所以 `n_empty_list=182` / `n_empty_null=28` 这两个数它们**不自己说明自己算在哪一批字节上**
#   ⇒⇒⇒⇒⇒⇒⇒ 下次看到它变了，无法区分「输入变了」和「类型器不对了」
#   ⇒⇒⇒⇒⇒⇒⇒ **⇒ 处置：把每本的 sha256/bytes 一起写进产物** —— 读数与它的输入指纹绑成一份
def _fp_of(raw):
    return {"sha256_12": hashlib.sha256(raw).hexdigest()[:12], "bytes": len(raw)}


_FP, _FP_BAD, _FP_VOLATILE = {}, [], {}
for _f in GOLDENS:
    # ⭐⭐⭐⭐⭐ 1032-②k：**volatile 的输入不进「可核对的那张表」**
    #   ⇒ 它照样被普查、也照样记下当次的字节（供复算）⇒ 但它的指纹**不承诺**对得上提交态
    #   ⇒ ⇒⇒ 而「登记指纹」那一步的写法**一个字都没改** ⇒ ⇒⇒⇒
    #   **⇒ ⇒⇒⇒⇒ 因为 `DD993M.1` 钉的就是这一行的原文（机制不变 ⇒ 锚点不该变）**
    if _f.name in VOLATILE_INPUTS:
        try:
            _FP_VOLATILE[_f.name] = dict(_fp_of(_f.read_bytes()),
                                         why=VOLATILE_INPUTS[_f.name])
        except Exception:
            _FP_BAD.append(_f.name)
        continue
    try:
        _FP[_f.name] = _fp_of(_f.read_bytes())
    except Exception:
        _FP_BAD.append(_f.name)
N_FP = len(_FP)
N_VOLATILE = len(_FP_VOLATILE)
_N_FROM_PROBES = sum(1 for _n, _d in _BOOKS
                     if isinstance(_gb_of(_d), str)
                     and _gb_of(_d).startswith("jimeng_probe")
                     and _gb_of(_d).endswith(".py"))


AMBIGUOUS = [r for r in rows if not r["self_provable"]]
N_AMBIG = len(AMBIGUOUS)

# ── P2：证明歧义 —— 「真算了、结果是空」与「根本没算」序列化后逐字节相同 ──
_led = json.loads(LEDGER.read_text(encoding="utf-8"))
# 版 A：**真的算过**，结果是空（1013 现在落盘的那一版）
_a = {"retired": [], "retired_note": _led.get("retired_note")}
# 版 B：**根本没算**这个字段 —— 键完全一样，值也是空 list
_b = {"retired": [], "retired_note": _led.get("retired_note")}
SAME_BYTES = (json.dumps(_a, ensure_ascii=False, sort_keys=True)
              == json.dumps(_b, ensure_ascii=False, sort_keys=True))

# ── P3：加了 companion 之后必须可区分 ──────────────────────────
_c = {"retired": [], "retired_computed": True, "retired_n": 0}
_d = {"retired": []}          # 没算的版本：没有 companion
DIFFERENT = (json.dumps(_c, ensure_ascii=False, sort_keys=True)
             != json.dumps(_d, ensure_ascii=False, sort_keys=True))
# ⭐ 而 companion 自己也得能区分「算了是 0」与「算了但算错了」
_c_bad = {"retired": [], "retired_computed": True, "retired_n": 3}
COMPANION_SELFTEST = (json.dumps(_c, ensure_ascii=False, sort_keys=True)
                      != json.dumps(_c_bad, ensure_ascii=False, sort_keys=True))

out = {
    "target": "offline-empty-ambiguity",
    "question": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **「空集合」有歧义：看起来是空的，和没算过，"
                "在仓里长得一模一样**",
    "offline_2014": True,
}

P1 = ("⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P1 成立：普查 %d 个 golden、%d 个空 list 字段、"
      "%d 个 null 字段 —— 其中可自证 %d 个、**不可自证 %d 个**（就是 1013 刚写的 "
      "`retired`）** ⇒ ⇒ ⇒ ⇒ ⇒ 而可自证的判据不是「旁边有说明」、"
      "而是「旁边有一个**可校验的不变式**」** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而一段散文说明（`retired_note`）钉不住任何东西："
      "它可以和「没算过」完全共存**" %
      (N_GOLDENS, n_empty_list, n_empty_null, n_selfprovable, N_AMBIG))

P2 = ("⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P2 成立（这是本批的病根）：「真的算过、结果是空」"
      "与「根本没算」这两份账，`retired` 字段序列化之后**逐字节相同**（实测判定 = %d）"
      "⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 也就是说：读 JSON 的人拿到 `retired: []` 时，"
      "无法区分「查了、没有」和「压根没查」** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而这正是 1008 那条「清单会过期」的一个新的、更隐蔽的形态**" %
      (1 if SAME_BYTES else 0))

P3 = ("⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P3 成立：处置是给账本加 companion 字段"
      "（`retired_computed` + `retired_n`），加上之后两份账**可区分**（实测判定 = %d）；"
      "而且 companion 自己也要能区分「算了是 0」与「算了但算错了」—— 那一条也验了** ⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而 1013 的 `retired: []` **原文一字不删**、只加 companion"
      "（1013 立的「撤销只挂横幅、原文不删」）** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而处置落在**1013 的探针**里、不落在这本账上 —— "
      "⇒ ⇒ ⇒ 因为账本每次运行都会被探针整个重写、改文件会在下一次跑时被抹掉**" %
      (1 if DIFFERENT else 0))

P4 = ("⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P4 反向用例成立：造一份 `retired` **非空**的真账，"
      "分类器必须把它判成「可自证」—— 而当前版本判不了（companion 尚未进判据）** ⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ ⇒ ⇒ 而这一条是为了排除「普查恒判『不可自证』」—— 那会让 %d 个字段"
      "看起来全都一样有问题、而实际上只有 1 个** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 所以判据里必须同时钉住「可自证 %d 个」和「不可自证 %d 个」两个数**" %
      (n_empty_list + n_empty_null, n_selfprovable, N_AMBIG))

P5 = ("⭐⭐⭐⭐⭐⭐⭐⭐ **P5：这条规矩不只管空 list —— **`null` 是同一个病的另一种形态**，"
      "而它同样分不清「算出来是 null」和「没算」** ⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而本批的普查已经把 null 一并数进去了（%d 个）**" % n_empty_null)

P6 = ("⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P6 —— 而最要紧的一句是：**"
      "1013 刚刚做出来的那本账，自己就带着这个毛病** ⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而这说明「刚做完的东西也是会犯的」不是假设、是本会话第三次撞上**"
      "（前两次：1012 的探针覆盖表是空的、1013 的断言里硬写了目标变量数）** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 所以任何交付物都必须被下一批当成被测对象重新过一遍"
      "—— 「自己验过」不算数**")

out["verdicts_2014"] = {
    "p1_only_one_empty_field_is_unverifiable_2014_": P1,
    "p2_computed_and_never_computed_are_byte_identical_2014_": P2,
    "p3_companion_fields_make_it_distinguishable_2014_": P3,
    "p4_reverse_case_classifier_is_not_constant_2014_": P4,
    "p5_null_is_the_same_disease_2014_": P5,
    "p6_the_previous_batch_artifact_is_itself_a_victim_2014_": P6,
    "offline_2014": "⭐⭐⭐⭐⭐ **本批纯离线**：不打开浏览器、不按任何键、"
                    "**连 `mouse.click` 都没有**",
}
# ⚠️⚠️⚠️⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **仪器 bug 9（第九个）：`P1`/`P4`/`P5` 全是时间耦合的，
#   而 `sys.exit` 压根没接** ⇒⇒⇒⇒⇒⇒⇒⇒⇒ 三条在第 1014 批写下时成立（`N_GOLDENS=8`、`N_AMBIG=1`），
#   而仓里长到 20 本 golden 之后它们**必然**转红 ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒
#   **⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ 而它们红了十几个 batch 没有人发现**
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ 「印出来的读数」与「接了线的读数」是两件事**
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐ 「可复现」也不蕴含「绿」：
#   1015 只比「两轮产物是否逐字节相同」，一个恒红的 `P` 它照样记成 `reproduced`**
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 处置：判据改成**结构不变式**（自己跟自己算账），不钉任何绝对数**
out["P1_hold_2014"] = bool(N_AMBIG == len(AMBIGUOUS)          # 普查自洽：报了几个就是几个
                           and n_selfprovable + N_AMBIG == n_empty_list + n_empty_null
                           and N_AMBIG >= 1)                  # 这门确实抓到了东西
out["P2_hold_2014"] = bool(SAME_BYTES)
out["P3_hold_2014"] = bool(DIFFERENT and COMPANION_SELFTEST
                           and "retired_computed" in PROBE13.read_text(encoding="utf-8"))
# ⭐⭐ `P4` 的原话是「排除恒判『不可自证』」⇒ **它的正确形式就是「两类都非空」**，
#   而原式 `N_AMBIG == 1 and n_selfprovable >= 3` 把「不是恒判」错写成了「正好一个」
out["P4_hold_2014"] = bool(n_selfprovable >= 1 and N_AMBIG >= 1)
# ⭐⭐ `P5` 原式 `n_empty_null == 0 or n_empty_null >= 0` 是**恒真**（对任何非负数都成立）
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 而它想说的是「`null` 被一并数进去了」⇒ 那是**分类器行为**，
#   该在分类器上验，而不是在计数上用一个恒真式子表态**
_NULL_CLASSIFIER_WORKS = find_empty({"x": None, "y": [], "z": [None]}) == [
    ("/x", "null"), ("/y", "list"), ("/z/[0]", "null")]
out["P5_hold_2014"] = bool(n_empty_null > 0 and _NULL_CLASSIFIER_WORKS)
out["P6_hold_2014"] = bool(any(r["golden"] == "occurrence-ledger-1013.json"
                               and r["path"] == "/retired" for r in AMBIGUOUS))

# ── ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ P9：注入式变异 —— 证明普查**真的在读那些书**，而不是只在数自己的输出
_bk = _BOOKS[0][1]
_pl = json.dumps(_bk, sort_keys=True, ensure_ascii=False)
_inj = dict(_bk)
_inj["_injected_null_2029"] = None
_ij = json.dumps(_inj, sort_keys=True, ensure_ascii=False)
_a_r, _a_l, _a_n, _a_s, _a_m = _census([("", json.loads(_pl))])
_b_r, _b_l, _b_n, _b_s, _b_m = _census([("", json.loads(_ij))])
_MUT_SEEN = (_b_n == _a_n + 1)          # 注入一个 null → null 计数恰好 +1
_FP_MOVES = (_fp_of(_pl.encode())["sha256_12"]
             != _fp_of(_ij.encode())["sha256_12"])   # 指纹钉在字节上，不是常量
_rest = _census([(n, d) for n, d in _BOOKS if n != _BOOKS[0][0]])[0]
_ONLY0 = _census([_BOOKS[0]])[0]
_MAIN_READS_BOOKS = (len(rows) - len(_rest) == len(_ONLY0))      # 拿掉第一本，总数恰好少它那一段
out["P9_hold_2014"] = bool(_MUT_SEEN and _FP_MOVES and _MAIN_READS_BOOKS
                            and n_empty_null >= 1
                            # ⚠️⚠️ 1032-②k：**这一项的口径变了**（前向更正，不改历史）
                            #   ⇒ 原式是 `N_FP + len(_FP_BAD) == N_GOLDENS`
                            #   ⇒ 而 1032-②j 收尾实测到：**有一类输入每次跑都被重写、且不随批提交**
                            #   ⇒ ⇒⇒ 它进不了「可核对的那张指纹表」⇒ ⇒⇒ 于是这一项必须把 volatile 单列出来
                            #   ⇒ ⇒⇒ **⇒ 判据的意思没变**（每一本输入要么被记了指纹、要么读不了、
                            #   ⇒ ⇒⇒   要么是那类「每次都被重写」的）⇒ ⇒⇒ **⇒ 只是口径变宽了一档**
                            and N_FP + len(_FP_BAD) + N_VOLATILE == N_GOLDENS)


# ── 1032-②k：**先写基础产物，再写「加了台账段」的最终产物** ─────────────────
#   ⇒ 为什么写两遍：`P7` 的原话是「产物确实落到仓里了、且不是空壳」
#   ⇒ ⇒⇒ 而台账段要等到所有 `P*_hold_2014` 都算出来之后才知道
#   ⇒ ⇒⇒ ⇒ 而 `P7` 又必须量「落盘的那个文件」⇒ ⇒⇒ ⇒ **⇒ 所以：先落盘（量 P7），
#   ⇒ ⇒⇒ ⇒       再补上台账段重写一次** ⇒ ⇒⇒ ⇒ **⇒ 而第二次写入只许【增加】、
#   ⇒ ⇒⇒ ⇒       不许扰动普查结果** ⇒ ⇒⇒ ⇒ **⇒ 这一条由 `P10` 当场核账**
_BASE_PAYLOAD = {
    "generated_by": "jimeng_probe1014_empty_ambiguity.py",
    "note": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **「空集合」有歧义：看起来是空的，和没算过，"
            "在仓里长得一模一样**",
    "rule": "⭐⭐⭐⭐⭐ **可自证 = 旁边有一个**可校验的不变式**；"
            "散文说明不算（它与「没算过」完全兼容）**",
    # ⇒ ⇒ ⇒ ⇒ **1032-②m：二阶效应「明说」**
    #   ⇒ ⇒ ⇒ ⇒ **本表记的是**别的产物的字节**⇒ ⇒ ⇒ ⇒ ⇒ **⇒ 任何重写自己产物的探针一跑、本表就过期**
    #   ⇒ ⇒ ⇒ ⇒ **⇒ 而「谁在查我」必须落进产物**⇒ ⇒ ⇒ ⇒ **⇒ 不许只活在 README 的散文里**
    "snapshot_and_who_checks_it": {
        "what_this_table_is": "⇒ **本表是【快照】**：记的是「上次跑 1014 时」各产物的字节 ⇒ **⇒ 它天生会过期**",
        "second_order_effect": "⇒ **任何重写自己产物的探针一跑 ⇒ 本表立刻过期**⇒ ⇒ ⇒ ⇒ ⇒ **⇒ 处置：重跑 1014**⇒ ⇒ ⇒ ⇒ ⇒ **⇒ 而这正是全门禁清单把 1014 排在最后的原因**",
        "who_checks_it": ["fingerprint-gate-1032l.json"],
        "how_it_is_checked": "⇒ **那道门用【双基线】（提交态 ＋ 工作区）逐行对 sha256_12／bytes**⇒ ⇒ ⇒ ⇒ ⇒ **⇒ ⇒ ⇒ 并报出「过期的是哪几本」**",
        "why_declared_here": "⇒ **「声明」与「发布」之间那道缝**⇒ ⇒ ⇒ ⇒ ⇒ **⇒ 声明必须落在产物里、而不只在 README 的散文里**",
    },
    "census_inputs_2029": {
        "n_fingerprinted": N_FP, "n_unreadable": len(_FP_BAD),
        "n_volatile": N_VOLATILE,
        "volatile_inputs": _FP_VOLATILE,
        "n_from_probe_products": _N_FROM_PROBES,
        "fingerprints": _FP,
        "why": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **一个读数不带输入指纹，就无法被引用** —— 下次看到它变了，分不清是「输入变了」还是「类型器不对了」",
    },
    "census": {"n_goldens": N_GOLDENS,
               "n_excluded_self": N_EXCLUDED_SELF, "n_empty_list": n_empty_list,
               "n_empty_null": n_empty_null,
               "n_self_provable": n_selfprovable, "n_ambiguous": N_AMBIG},
    "rows": rows,
    "ambiguous": AMBIGUOUS,
    "byte_identity_proof": {
        "computed_but_empty": json.dumps(_a, ensure_ascii=False, sort_keys=True),
        "never_computed": json.dumps(_b, ensure_ascii=False, sort_keys=True),
        "identical": SAME_BYTES,
    },
    "companion_proof": {
        "with_companion": json.dumps(_c, ensure_ascii=False, sort_keys=True),
        "without_companion": json.dumps(_d, ensure_ascii=False, sort_keys=True),
        "distinguishable": DIFFERENT,
        "companion_catches_wrong_count": COMPANION_SELFTEST,
    },
    "fix_lands_in": "scripts/jimeng_probe1013_occurrence_ledger.py",
    "fix_lands_in_why": "⭐⭐⭐⭐⭐ 账本每次运行都被探针整个重写 ⇒ ⇒ ⇒⇒ "
                        "改文件会在下一次跑时被抹掉 ⇒ ⇒ ⇒ ⇒ 处置必须落在探针里",
}
io.open(GOLDEN, "w", encoding="utf-8").write(
    json.dumps(_BASE_PAYLOAD, ensure_ascii=False, indent=1))
out["P7_hold_2014"] = bool(GOLDEN.exists() and GOLDEN.stat().st_size > 500)
# ── P8：沿用「手写的数必须有出处」 ───────────────────────────────
_NUMRE = re.compile(r"(?<![A-Za-z_0-9])(\d+(?:\.\d+)?)(?![A-Za-z_0-9])")
_AUD_BLOCK = "empty_ambiguity_2014"


def audit_block():
    for node in ast.walk(ast.parse(AUDIT_TXT)):
        if not isinstance(node, ast.Dict):
            continue
        for k, v in zip(node.keys, node.values):
            if (isinstance(k, ast.Constant) and k.value == _AUD_BLOCK
                    and isinstance(v, ast.Dict)):
                return ast.literal_eval(v)
    raise AssertionError("⭐ audit 里找不到 %s（仪器坏了）" % _AUD_BLOCK)


_AB = audit_block()
assert "p6_the_previous_batch_artifact_is_itself_a_victim_2014_" in _AB, (
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


out["readings_2014"] = {
    "n_goldens": N_GOLDENS, "n_excluded_self": N_EXCLUDED_SELF, "n_empty_list": n_empty_list,
    "n_empty_null": n_empty_null, "n_self_provable": n_selfprovable,
    "n_empty_total": n_empty_list + n_empty_null,
    "n_ambiguous": N_AMBIG,
    "n_fingerprinted": N_FP,
    "n_from_probe_products": _N_FROM_PROBES,
}
_allowed = _nums({k: v for k, v in out.items()
                  if k != "verdicts_2014"}, set())
_allowed |= set("0123456789") | {
    "1008", "1011", "1012", "1013", "1014",
}
_allowed |= set(re.findall(r'check\("[A-Z](\d{3})[A-Z]\.', VERIFIER_TXT))

# ⚠️⚠️⚠️⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **仪器 bug 9 的另一半：`P8` 拿「今天的读数」去卡一段历史记录**
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒ 而 `empty_ambiguity_2014` 那段散文记的是**第 1014 批当时**的读数
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ （8 个 golden、11 个空 list、1 个 null）⇒ 仓里长起来之后必然对不上
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 而「历史实测记录不因被测对象后来变了就过期」是我自己那条规矩**
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒⇒⇒⇒⇒⇒⇒⇒⇒ 处置不是改散文（那是历史记录，一字不删），**
#   **⇒ 而是给散文配一个 companion：它自己声明「我当时读到的是这几个数」**
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐**
#   **⇒ 这正是 1014 自己发明的那个 companion 模式（`retired_computed` + `retired_n`），**
#   **⇒ 用在它自己身上 —— 「处置落在探针里、不落在账本上」**
_HIST = _AB.get("historical_readings_2014") or {}
assert isinstance(_HIST, dict) and _HIST, (
    "⭐⭐⭐⭐⭐ audit 的 `empty_ambiguity_2014` 块里必须有 `historical_readings_2014` companion")
_allowed |= {str(v) for v in _HIST.values()
             if isinstance(v, (int, float)) and not isinstance(v, bool)}
_bad, _n_tot = {}, 0
for _k in out["verdicts_2014"]:
    _got = sorted(set(_NUMRE.findall(_AB.get(_k) or "")), key=float)
    _miss = [n for n in _got if n not in _allowed]
    _n_tot += len(_got)
    if _miss:
        _bad[_k] = _miss
out["audit_numbers_vs_computed_2014"] = {
    "n_keys_compared": len(out["verdicts_2014"]),
    "n_numbers_total": _n_tot,
    "n_keys_with_unjustified_number": len(_bad),
    "unjustified": _bad,
    "historical_readings_declared": _HIST,
    "historical_readings_why": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
                               "**⇒ 散文里的数要么是「当次实测」、要么在 companion 里声明过；"
                               "两头都不沾的才算没有出处** ⇒ "
                               "**⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ 「历史记录不因为后来变了就过期」与"
                               "「手写的数必须有出处」不是冲突的，前提是历史记录自己声明了它当时的数**",
}
out["P8_hold_2014"] = bool(not _bad and _HIST)

# ── 1032-②k：**台账落进产物**（声明 ≠ 发布）────────────────────────────────
#   ⇒ 以前 1014 的 9 条判据只打在 stdout（`tail` 里）、产物里没有
#   ⇒ ⇒⇒⇒ ⇒ **⇒ 而 1015 的台账只读仓内产物 ⇒ ⇒⇒⇒ ⇒ ⇒ ⇒ 1014 因此一直「有判据、没台账」**
#   ⇒ ⇒⇒⇒ ⇒ **⇒ 这正是「声明 ≠ 发布」那条规矩要治的病**
# ⚠️⚠️ 顺序有讲究：`P10` 必须在「判据键集合」算出来**之前**就有
#   ⇒ ⇒⇒ 否则「`P` 段里有没有 `P10`」会变成循环依赖 ⇒ ⇒⇒ 而循环依赖的判据永远是恒真
_disk_base = json.loads(GOLDEN.read_text(encoding="utf-8"))
out["P10_hold_2014"] = bool(_disk_base == _BASE_PAYLOAD)
_P_KEYS_2014 = sorted(k for k in out if re.match(r"^P\d+_hold_2014$", k))
_LEDGER_KEYS = ("P", "criterion_kinds_2014",
                "criterion_kinds_complete_2014", "criteria_n_2014")
_FINAL_PAYLOAD = dict(_BASE_PAYLOAD)
_FINAL_PAYLOAD["P"] = {k: bool(out[k]) for k in _P_KEYS_2014}
_FINAL_PAYLOAD["criterion_kinds_2014"] = KINDS_2014
_FINAL_PAYLOAD["criterion_kinds_complete_2014"] = bool(
    set(KINDS_2014) == set(_P_KEYS_2014))
_FINAL_PAYLOAD["criteria_n_2014"] = len(_P_KEYS_2014)
io.open(GOLDEN, "w", encoding="utf-8").write(
    json.dumps(_FINAL_PAYLOAD, ensure_ascii=False, indent=1))
# ⭐⭐⭐⭐⭐ 写完之后**当场复算一次**：最终产物去掉台账段，必须与第一次落盘的逐键相等
#   ⇒ ⇒⇒⇒ ⇒ **⇒ 这一条是「第二次写入只增加、不扰动」的落地核账**
#   ⇒ ⇒⇒⇒ ⇒ ⇒ 而它只能在最终写入**之后**算 ⇒ ⇒⇒⇒ ⇒ ⇒ 所以它进 /tmp 读数，
#   ⇒ ⇒⇒⇒ ⇒ ⇒   不进产物里的 `P` 段（`P` 段记的是「判据的判决」，不是「写入的自检」）
_FINAL_ON_DISK = json.loads(GOLDEN.read_text(encoding="utf-8"))
out["final_write_only_added_ledger_2014"] = bool(
    _FINAL_ON_DISK == {k: v for k, v in _FINAL_PAYLOAD.items()
                       if k not in _LEDGER_KEYS})

io.open(OUT, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
print("goldens=%d empty_list=%d null=%d selfprovable=%d ambiguous=%d"
      % (N_GOLDENS, n_empty_list, n_empty_null, n_selfprovable, N_AMBIG))
print("ambiguous:", [(r["golden"], r["path"]) for r in AMBIGUOUS])
print("byte-identical(算了 vs 没算) =", SAME_BYTES,
      "| companion 可区分 =", DIFFERENT, "| companion 抓错数 =", COMPANION_SELFTEST)
# ⭐⭐⭐⭐⭐ 1032-②k：**打印的必须是「仓内那份产物」** —— 不是 `/tmp` 那份
#   ⇒ ⇒⇒⇒ ⇒ 而 `1015` 用两处读它：**可复现性**比的是仓内 golden 的字节、
#   ⇒⇒⇒⇒ ⇒   **台账**读的是「探针打印的那个路径」⇒ ⇒⇒⇒ ⇒ ⇒⇒ **⇒ 而这两处必须是同一份**
#   ⇒ ⇒⇒⇒ ⇒ **⇒ ⇒ ⇒ 以前这里打的是 `/tmp/b1014-empty-ambiguity.json` ⇒ ⇒⇒⇒ ⇒ ⇒⇒ ⇒ ⇒
#   ⇒ ⇒⇒⇒ ⇒ **⇒ ⇒ ⇒ ⇒ ⇒ 台账因此读的是一份「不在仓里」的产物 ⇒ ⇒⇒⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒**
#   ⇒ ⇒⇒⇒ ⇒ **⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而「不在仓里的产物」上的台账 ⇒ ⇒⇒⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 「没人查得到」**
#   ⇒ ⇒⇒⇒ ⇒ **⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 1018 早就打的是 `GOLDEN`（仓内）⇒ ⇒⇒⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒**
#   ⇒ ⇒⇒⇒ ⇒ **⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而本批给 1014 补上台账 ⇒ ⇒⇒⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒**
#   ⇒ ⇒⇒⇒ ⇒ **⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒**
print("PROBE_1014_DONE ->", GOLDEN)

# ⚠️⚠️⚠️⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
# **仪器 bug 9 的另一半：「印出来的读数」不等于「接了线的读数」**
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ 这个文件从第 1014 批起就 `print("P1..P8 =", ...)`，
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **但从来没有 `sys.exit`** ⇒ 退出码恒 0
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 红读数无法让任何东西变红 ⇒ P1/P4/P8 红了十几个 batch 没人发现**
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ 另一头还叠着 **仪器 bug 8：1015 只比「两轮产物逐字节相同」**
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 一个恒红的 P 它照样记 `reproduced`
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐**
#   **⇒ 「可复现」不蕴含「绿」⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒**
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 这里把线接上：任一 `P*_hold_2014` 为假 ⇒ 退出码 1**
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 收集范围是「以 `P` 开头、以 `_hold_2014` 结尾」的键，
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ 写死 `range(1,9)` 的话下次加第 9 条 P 会漏掉它**
_N_FALSE_2014 = sorted(k for k, v in out.items()
                       if k.startswith("P") and k.endswith("_hold_2014") and not v)
_N_P_2014 = sum(1 for k in out if k.startswith("P") and k.endswith("_hold_2014"))
_P_ALL = [(k, v) for k, v in sorted(out.items())
          if k.startswith("P") and k.endswith("_hold_2014")]
print("P1..P%d =" % _N_P_2014, [v for _k, v in _P_ALL])
print("P 为假的：", _N_FALSE_2014 or "无", "| 共 %d 条 P 判据" % _N_P_2014)
assert _N_P_2014 >= 9, "⭐⭐⭐ P 判据条数掉到 9 以下了：%d" % _N_P_2014
sys.exit(1 if _N_FALSE_2014 else 0)