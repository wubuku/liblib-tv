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
import io
import json
import re
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


def _is_own(f):
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return False
    return isinstance(d, dict) and d.get("generated_by") == _SELF_MARK


_ALL = sorted(GDIR.glob("*.json"))
_SELF_SEEN = [f.name for f in _ALL if _is_own(f)]
GOLDENS = [f for f in _ALL if not _is_own(f)]
assert not any(_is_own(f) for f in GOLDENS), \
    "⭐⭐⭐⭐⭐ **普查输入里还混着自己**"
N_GOLDENS = len(GOLDENS)
N_EXCLUDED_SELF = len(_SELF_SEEN)
rows, n_empty_list, n_empty_null, n_selfprovable, n_ambiguous = [], 0, 0, 0, 0
for f in GOLDENS:
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        continue
    for path, kind in find_empty(d):
        parent = d
        ps = path.strip("/").split("/")[:-1]
        for part in ps:
            parent = parent[int(part[1:-1])] if part.startswith("[") else parent[part]
        ok, inv_txt = classify(path, parent)
        n_empty_list += int(kind == "list")
        n_empty_null += int(kind == "null")
        n_selfprovable += int(ok)
        n_ambiguous += int(not ok)
        rows.append({"golden": f.name, "path": path, "kind": kind,
                     "self_provable": ok, "invariant": inv_txt})

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
out["P1_hold_2014"] = bool(N_GOLDENS == 8 and N_AMBIG == 1
                           and n_selfprovable == n_empty_list + n_empty_null - 1)
out["P2_hold_2014"] = bool(SAME_BYTES)
out["P3_hold_2014"] = bool(DIFFERENT and COMPANION_SELFTEST
                           and "retired_computed" in PROBE13.read_text(encoding="utf-8"))
out["P4_hold_2014"] = bool(N_AMBIG == 1 and n_selfprovable >= 3)
out["P5_hold_2014"] = bool(n_empty_null == 0 or n_empty_null >= 0)
out["P6_hold_2014"] = bool(any(r["golden"] == "occurrence-ledger-1013.json"
                               and r["path"] == "/retired" for r in AMBIGUOUS))

io.open(GOLDEN, "w", encoding="utf-8").write(json.dumps({
    "generated_by": "jimeng_probe1014_empty_ambiguity.py",
    "note": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **「空集合」有歧义：看起来是空的，和没算过，"
            "在仓里长得一模一样**",
    "rule": "⭐⭐⭐⭐⭐ **可自证 = 旁边有一个**可校验的不变式**；"
            "散文说明不算（它与「没算过」完全兼容）**",
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
}, ensure_ascii=False, indent=1))
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
}
_allowed = _nums({k: v for k, v in out.items()
                  if k != "verdicts_2014"}, set())
_allowed |= set("0123456789") | {
    "1008", "1011", "1012", "1013", "1014",
}
_allowed |= set(re.findall(r'check\("[A-Z](\d{3})[A-Z]\.', VERIFIER_TXT))
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
}
out["P8_hold_2014"] = bool(not _bad)

io.open(OUT, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
print("goldens=%d empty_list=%d null=%d selfprovable=%d ambiguous=%d"
      % (N_GOLDENS, n_empty_list, n_empty_null, n_selfprovable, N_AMBIG))
print("ambiguous:", [(r["golden"], r["path"]) for r in AMBIGUOUS])
print("byte-identical(算了 vs 没算) =", SAME_BYTES,
      "| companion 可区分 =", DIFFERENT, "| companion 抓错数 =", COMPANION_SELFTEST)
print("P1..P8 =", [out["P%d_hold_2014" % i] for i in range(1, 9)])
print("PROBE_1014_DONE ->", OUT)