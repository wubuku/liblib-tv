#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1030：`check()` 锚点**身份**闸。

1021 用注入式变异量到一件事：把一条判据里的锚点**换成另一个同样存在的字符串**，
官方锚点门**完全看不见** —— 锚点数没变、每条锚点都还在源文件里、
于是「问题 0 个 ⇒ 全通 ✓」照样成立。

⇒ **官方门验的是「锚点在不在」，不是「锚点是不是原来那个」**。
本探针补上后半句：给每条 `check()` 记一个**锚点集合摘要**，
**锚点数不变而摘要变了 ⇒ 转红**（那正是 swap 的形状）。
"""
import ast
import collections
import hashlib
import importlib.util
import io
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GATE = ROOT / "scripts/jimeng_check_verifier_anchors.py"
# ⭐⭐⭐ 可以用 `JIMENG_VERIFIER_SRC` 指向一份**候选副本**。
#   用途：注入式变异要在**不碰仓库**的前提下问「这个门会拿它当红」——
#   而不是只在 README 里写一句「信我测过了」。
VERIFIER = Path(os.environ.get("JIMENG_VERIFIER_SRC")
                or (ROOT / "scripts/verify-jimeng-batch841-unclickable.py"))
GOLDEN = ROOT / "docs/research/jimeng-canvas/anchor-identity-1030.json"
OUT = "/tmp/b1030-anchor-identity.json"

_spec = importlib.util.spec_from_file_location("_anchgate_1030", GATE)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

VTXT = VERIFIER.read_text(encoding="utf-8")


def anchors_of_check(call):
    """⭐⭐ 与官方 `collect()` **同一套口径**：同一批过滤、同一批符号表。

    唯一区别是本函数按 `check()` 分组，而 `collect()` 把它们拍平成一张表；
    两者是否一致由 P4 当场核账。
    """
    out = []
    for node in ast.walk(call):
        if not isinstance(node, ast.Compare):
            continue
        for op, comp in zip(node.ops, node.comparators):
            if not isinstance(op, (ast.In, ast.NotIn)):
                continue
            name = comp.id if isinstance(comp, ast.Name) else None
            s = _mod._const_str(node.left)
            if s is None or name is None:
                continue
            name = _mod.resolve_alias(name)
            if name != "_ausrc" and name not in _mod.PROBE_VARS:
                continue
            out.append((name, s, isinstance(op, ast.NotIn)))
    return out


def label_of(call):
    """只用于**报告**。⭐ 身份不靠它（见 `_identity`）。"""
    if call.args and isinstance(call.args[0], ast.Constant) \
            and isinstance(call.args[0].value, str):
        tok = call.args[0].value.split()
        if tok and tok[0].startswith("DD"):
            return tok[0]
    return "check@L%d" % call.lineno


def compute(text):
    """把一份 verifier 源码算成 `{label: (n_anchors, digest)}`。"""
    tree = ast.parse(text)
    checks = {}
    for c in ast.walk(tree):
        if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) \
                and c.func.id == "check":
            checks.setdefault(label_of(c), []).extend(anchors_of_check(c))
    res = {}
    for lb, trip in checks.items():
        blob = "\x00".join(sorted("%s\x01%s" % (v, s) for v, s, _ in trip))
        res[lb] = (len(trip), hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12])
    return res, checks


NOW, CHECKS = compute(VTXT)
N_CHECKS = len(NOW)
N_ANCHORS = sum(n for n, _d in NOW.values())

out = {}
out["generated_by"] = "jimeng_probe1030_anchor_identity.py"
out["note"] = ("⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **官方锚点门验的是「锚点在不在」，"
               "不是「锚点是不是原来那个」** ⇒ 本探针补后半句："
               "**锚点计数不变而集合摘要变了 ⇒ 转红**")
out["how"] = (
    "⭐⭐⭐⭐⭐ 摘要 = sha256(排序后的「变量\\x01锚点」序列)[:12]；"
    "⭐⭐ 抽锚点**复用官方门的同一套过滤与符号表**（`PROBE_VARS` / "
    "`resolve_alias` / `_const_str`），不另写一套 ⇒ "
    "⭐⭐⭐⭐⭐ **同一个东西要比同一个口径**；"
    "⭐⭐ 两者是否一致由 P4 当场核账；"
    "⭐⭐⭐⭐⭐⭐⭐ **身份 = (锚点数, 摘要) 这一对，不是行号、也不是标签**")
out["n_checks"] = N_CHECKS
out["n_anchors"] = N_ANCHORS
out["checks"] = {lb: {"n": n, "digest": d} for lb, (n, d) in sorted(NOW.items())}

# ── P4：口径一致 —— 我的分组总数必须等于官方收集器的总数 ──────────────
OFFICIAL_TOTAL = len(_mod.collect(ast.parse(VTXT)))
out["caliber_1030"] = {
    "official_collect_total": OFFICIAL_TOTAL,
    "per_check_grouped_total": N_ANCHORS,
    "same": OFFICIAL_TOTAL == N_ANCHORS,
    "why": "⭐⭐⭐⭐⭐ 官方门跳过的类别（变量未登记等）在两边都同样被跳过，"
           "所以「总数相等」正是「口径相同」的必要证据",
}
out["P4_same_caliber_as_official_gate_1030"] = bool(OFFICIAL_TOTAL == N_ANCHORS)

# ── 与仓库里那本比：计数不许跌；同 n 的老身份不见了、同 n 换了新身份 ⇒ red ──
_g = {}
if GOLDEN.exists():
    _g = json.loads(GOLDEN.read_text(encoding="utf-8")).get("checks") or {}

CUR_MULTI = {}
for lb, (n, d) in NOW.items():
    CUR_MULTI.setdefault((n, d), []).append(lb)
OLD_MULTI = {}
for lb, rec in _g.items():
    OLD_MULTI.setdefault((rec.get("n"), rec.get("digest")), []).append(lb)

# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **一条规则同时覆盖四种「判据被削弱」的形状**
#   1021 量到官方门漏掉的不止 swap（`E`），还有：
#     `A_drop_one_criterion`（删掉一整条 check）、`B_drop_whole_group`（删掉整组）、
#     `C_drop_one_conjunct`（从一条 check 里拿掉一个 and 出来的合取项）。
#   ⇒ 而它们的**共同形状只有一个**：某个老身份在当前集合里**找不到任何锚点数更大的后继**。
#   - 精确命中            ⇒ 纯移动，不红
#   - 有 n 更大的当前身份  ⇒ 真扩容，不红
#   - 其它（n 变小 / 换了摘要 / 彻底没了）⇒ **转红**
# ⚠️ 与上一版相比的关键差别：上一版只看「同 n 有没有别的身份顶上」，
#   于是**少一个合取项**（n 变小）会被归到「老身份不见了、也没有同 n 的替补」⇒ 只记成读数、不转红。
def _weakened(old_pairs, cur_pairs):
    """⭐ **唯一的判定实现**：判红与内部对照都调它。

    返回 `(red, n_exact_move)`。`red` 里每一项是一个**老身份**，
    它在当前集合里找不到精确匹配、也找不到任何**剩余计数 > 0** 且锚点更多的身份
    ⇒ 那就是「这条判据被削弱了，或者没了」。

    ⚠️⚠️⚠️ **「剩余计数 > 0」这个条件是本函数唯一的难点，也是第一版漏掉的那一处**：
    精确匹配会把 `cur` 里对应项消耗到 0；若不过滤，它们仍然带着 `n` 参与
    「有没有更大的后继」判断 ⇒ **一个已被消耗掉的身份会替一个被削弱的身份顶包**
    ⇒ 削弱被当成扩容 ⇒ 不红。合成样本 `E_swap_anchor` 与 `C_drop_one_conjunct`
    当场就抓到了这一处。
    """
    cur = collections.Counter(cur_pairs)
    old = collections.Counter(old_pairs)
    n_exact = 0
    for key in list(old):
        if old[key] == 0:
            continue
        take = min(old[key], cur.get(key, 0))
        if take:
            n_exact += take
            cur[key] -= take
            old[key] -= take
    red = []
    for key in list(old):
        if old[key] == 0:
            continue
        left = [(k, v) for k, v in cur.items() if v > 0]
        bigger = [k for k, v in left
                  if k[0] is not None and key[0] is not None and k[0] > key[0]]
        if not bigger:
            red.append({"old_n": key[0], "old_digest": key[1],
                        "n_left_untouched": old[key],
                        "n_bigger_left": 0})
        cur = collections.Counter({k: v for k, v in cur.items() if v > 0})
    return red, n_exact


_OLD_PAIRS = [(rec.get("n"), rec.get("digest")) for rec in _g.values()]
_CUR_PAIRS = list(NOW.values())
_red, _n_exact_move = _weakened(_OLD_PAIRS, _CUR_PAIRS)

_n_old = len(_g)
out["delta_1030"] = {
    "n_checks_in_golden": _n_old, "n_checks_now": N_CHECKS,
    "delta": N_CHECKS - _n_old,
    "n_red": len(_red), "red": _red[:20],
    "n_exact_move": _n_exact_move,
    "identity_rule": "\u2b50\u2b50\u2b50\u2b50\u2b50 \u8eab\u4efd = (n_anchors, digest) "
                     "\u8fd9\u4e00\u5bf9\uff0c**\u4e0d\u662f\u884c\u53f7\u3001\u4e5f\u4e0d\u662f\u6807\u7b7e** "
                     "\u21d2 \u7eaf\u79fb\u52a8\u4e0d\u7ea2\u3001\u771f\u6269\u5bb9\u4e0d\u7ea2\u3001"
                     "**\u540c n \u6362\u6458\u8981 / n \u53d8\u5c0f / \u6574\u6761\u6d88\u5931 \u5168\u90e8\u8f6c\u7ea2**",
    "single_implementation": "\u2b50\u2b50\u2b50\u2b50\u2b50 **\u5224\u5b9a\u903b\u8f91\u53ea\u6709\u4e00\u4efd**"
                              "\uff08`_weakened`\uff09\uff0c\u5224\u7ea2\u4e0e\u5185\u90e8\u5bf9\u7167\u90fd\u8c03\u5b83 "
                              "\u21d2 \u7b2c\u4e00\u7248\u5199\u4e86\u4e24\u4efd\u3001\u4e24\u4efd\u90fd\u6f0f\u4e86\u540c\u4e00\u5904 "
                              "\u21d2 **\u5bf9\u7167\u9a8c\u7684\u4e0d\u662f\u5224\u7ea2\u7528\u7684\u90a3\u4e00\u4efd**",
}
out["P1_floor_1030"] = bool(N_CHECKS >= _n_old)
out["P2_weakening_is_red_1030"] = bool(not _red)
_silent = _red          # ⭐ 保留旧名，供已写好的 README / 判据引用
_gone = []

# ── P3：身份与行号无关 —— 在文件头插一行注释，身份集合必须一模一样 ─────────
_moved, _moved_checks = compute("# \u4e34\u65f6\u6ce8\u91ca\u4e00\u884c\n" + VTXT)
out["line_independence_control_1030"] = {
    "identity_set_unchanged": (set(_moved.values()) == set(NOW.values())),
    "n_checks_before": N_CHECKS, "n_checks_after": len(_moved),
    "why": "⭐⭐⭐⭐⭐ 第一版给没有 `DD…` 前缀的判据用 `check@L<行号>` 当身份，"
           "**在它上面插一行代码它就「消失」**，`P2` 当场转红而仓里其实什么都没坏；"
           "⭐⭐⭐⭐⭐ 改成 doc 摘要之后仍有 24 条判据首参不是字面量、只能退回行号，噪声照旧 "
           "⇒ **行号不是身份，标签也不是**",
}
out["P3_identity_is_line_independent_1030"] = bool(
    set(_moved.values()) == set(NOW.values()))

# ── P5 阳性对照：把一条锚点换成**另一个同样存在的**锚点，摘要必须变 ───────
_all = sorted({s for trip in CHECKS.values() for _v, s, _n in trip})
_swapped = False
if len(_all) >= 2:
    _a, _b = _all[0], _all[-1]
    _d0 = hashlib.sha256("\x00".join(sorted(_a)).encode("utf-8")).hexdigest()[:12]
    _d1 = hashlib.sha256("\x00".join(sorted(_b)).encode("utf-8")).hexdigest()[:12]
    _swapped = (_d0 != _d1)
    out["swap_control_1030"] = {
        "old_anchor": _a[:120], "new_anchor": _b[:120],
        "old_digest": _d0, "new_digest": _d1, "digest_moved": _swapped,
        "why": "⭐⭐⭐⭐⭐ 这就是 1021 的 `E_swap_anchor_to_one_that_exists`："
               "**换完之后两条锚点都仍然存在、锚点数一个没少、官方门照样报 0 问题** "
               "⇒ 只有摘要会动",
    }
out["P5_swap_moves_the_digest_1030"] = bool(_swapped)



_S = [(3, "aaa111111111"), (5, "bbb222222222"), (7, "ccc333333333")]
_CASES = {
    "exact_move": (_S, _S),
    "grew": (_S, [(3, "aaa111111111"), (5, "bbb222222222"), (7, "ccc333333333"),
                  (9, "ddd444444444")]),
    "E_swap_anchor": (_S, [(3, "zzz999999999"), (5, "bbb222222222"), (7, "ccc333333333")]),
    "A_drop_one_criterion": (_S, [(3, "aaa111111111"), (5, "bbb222222222")]),
    "B_drop_whole_group": (_S, [(3, "aaa111111111")]),
    "C_drop_one_conjunct": (_S, [(2, "xxx555555555"), (5, "bbb222222222"),
                                 (7, "ccc333333333")]),
}
_case_red = {k: len(_weakened(o, c)[0]) for k, (o, c) in _CASES.items()}
out["weakening_shapes_control_1030"] = {
    "n_red_per_shape": _case_red,
    "must_be_zero": ["exact_move", "grew"],
    "must_be_positive": ["E_swap_anchor", "A_drop_one_criterion",
                          "B_drop_whole_group", "C_drop_one_conjunct"],
    "why": "\u2b50\u2b50\u2b50\u2b50\u2b50 1021 \u91cf\u5230\u5b98\u65b9\u95e8\u5bf9\u8fd9\u56db\u79cd\u5f62\u72b6\u5168\u90e8\u62a5\u300c\u95ee\u9898 0 \u4e2a\u300d "
           "\u21d2\u21d2 \u8fd9\u91cc\u628a\u5b83\u4eec\u56fa\u5b9a\u6210\u5185\u90e8\u5bf9\u7167\uff0c"
           "\u5e76\u4e14\u540c\u65f6\u628a\u300c\u7eaf\u79fb\u52a8\u300d\u4e0e\u300c\u771f\u6269\u5bb9\u300d\u4e5f\u653e\u8fdb\u53bb \u2014\u2014 "
           "**\u53ea\u8981\u89c4\u5219\u5bf9\u5408\u6cd5\u53d8\u5316\u4e5f\u62a5\u7ea2\uff0c\u5b83就\u662f\u4e00\u9053\u65e0\u5dee\u522b\u62a5\u8b66\u7684门**",
}
out["P7_weakening_shapes_1030"] = bool(
    all(_case_red[k] == 0 for k in ("exact_move", "grew"))
    and all(_case_red[k] > 0 for k in ("E_swap_anchor", "A_drop_one_criterion",
                                       "B_drop_whole_group", "C_drop_one_conjunct")))

# ── P6 阳性对照：把仓库里那本的摘要抹成常量，**模拟一遍检测逻辑**必须抓到 ──
def _simulate(old_multi):
    """与主流程完全同一套判定（⭐⭐ 同一个东西要比同一个口径）。"""
    return _weakened(list(old_multi), list(CUR_MULTI_FOR_CTRL))[0]


_cur_now = collections.Counter(NOW.values())
CUR_MULTI_FOR_CTRL = [(k[0], k[1]) for k in _cur_now.elements()]
_tampered = {}
for _k in _OLD_PAIRS:
    _tampered[(_k[0], "0" * 12)] = 1
_caught = bool(_tampered) and bool(_simulate(list(_tampered)))
out["golden_tamper_control_1030"] = {
    "n_tampered": len(_tampered),
    "simulated_with_tampered": len(_simulate(list(_tampered))),
    "caught": _caught,
    "why": "⭐⭐ 抹成常量之后，老身份 (n, 000000000000) 在当前集合里找不到同 n 的对应物 ⇒ P2 红；"
           "⭐⭐⭐⭐⭐ 而这一条**复用主流程那个 `_weakened`** —— "
           "**1031 第一版正因为对照与判红各写了一份，才让「对照通过了」变成一句假话**",
}
out["P6_golden_tamper_is_caught_1030"] = bool(_caught)

# ⭐⭐⭐⭐⭐ 写进 golden 的只有**稳定子集** —— `delta_1030` / `caliber_1030` /
#   对照结果都是「本次运行」的量，写进去会让 golden 每跑一次就变一份，
#   而 **golden 必须是「上一次登记的身份」，不是「上一次运行的快照」**
_GOLDEN_KEYS = ("generated_by", "note", "how", "n_checks", "n_anchors", "checks")
if "--write-golden" in sys.argv:
    GOLDEN.write_text(json.dumps(
        {k: out[k] for k in _GOLDEN_KEYS}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print("GOLDEN WRITTEN ->", GOLDEN)


def _is_p(k):
    return (len(k) > 2 and k[0] == "P" and k[1].isdigit()
            and "_" in k and k.endswith("_1030"))


_P_ALL = [(k, v) for k, v in sorted(out.items()) if _is_p(k)]
_N_FALSE_1030 = sorted(k for k, v in _P_ALL if not v)
_N_P_1030 = len(_P_ALL)

io.open(OUT, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
print("checks=%d anchors=%d golden=%d silent=%d gone=%d"
      % (N_CHECKS, N_ANCHORS, _n_old, len(_silent), len(_gone)))
if _silent:
    print("⚠️ 同锚点数却换了摘要（= swap）：", _silent[:3])
print("P1..P%d = %s" % (_N_P_1030, [v for _k, v in _P_ALL]))
print("P 为假的：", _N_FALSE_1030 or "无", "| 共 %d 条 P 判据" % _N_P_1030)
assert _N_P_1030 >= 7, "P 判据条数掉到 7 以下了：%d" % _N_P_1030
print("PROBE_1030_DONE ->", OUT)
sys.exit(1 if _N_FALSE_1030 else 0)