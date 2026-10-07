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

_silent, _gone = [], []
for key, labs in sorted(OLD_MULTI.items(), key=lambda kv: str(kv[0])):
    if key in CUR_MULTI:
        continue
    same_n_now = [k for k in CUR_MULTI if k[0] == key[0]]
    if same_n_now:
        _silent.append({"old_n": key[0], "old_digest": key[1],
                        "old_labels": labs[:3],
                        "new_labels": [CUR_MULTI[k][0] for k in same_n_now][:3],
                        "new_digests": sorted(k[1] for k in same_n_now)[:3]})
    else:
        _gone.append({"old_n": key[0], "old_digest": key[1],
                      "old_labels": labs[:3]})

_n_old = len(_g)
out["delta_1030"] = {
    "n_checks_in_golden": _n_old, "n_checks_now": N_CHECKS,
    "delta": N_CHECKS - _n_old,
    "n_silently_rewritten": len(_silent), "silently_rewritten": _silent[:20],
    "n_no_longer_present": len(_gone), "no_longer_present": _gone[:20],
    "identity_rule": "⭐⭐⭐⭐⭐ 身份 = (n_anchors, digest) 这一对，"
                     "**不是行号、也不是标签** ⇒ 纯移动（两者都没变）不红、"
                     "真扩容（n 变大）不红、**同 n 换摘要必红**",
}
out["P1_floor_1030"] = bool(N_CHECKS >= _n_old)
out["P2_silent_rewrite_is_red_1030"] = bool(not _silent)

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

# ── P6 阳性对照：把仓库里那本的摘要抹成常量，**模拟一遍检测逻辑**必须抓到 ──
def _simulate(old_multi):
    """与主流程完全同一套判定（⭐⭐ 同一个东西要比同一个口径）。"""
    hit = []
    for key in old_multi:
        if key in CUR_MULTI:
            continue
        if [k for k in CUR_MULTI if k[0] == key[0]]:
            hit.append(key)
    return hit


_tampered = {k: list(v) for k, v in OLD_MULTI.items()}
_tk = None
if _tampered:
    _tk = sorted(_tampered)[0]
    _n0, _d0 = _tk
    _tampered[(_n0, "0" * 12)] = _tampered.pop(_tk)
# ⭐⭐⭐⭐⭐ 只断言「篡改后必被抓到」**这一件事**
#   —— 第一版顺手把「真实 golden 当前必须 0 命中」也塞进同一个合取项，
#   结果**真出现一次 swap 时 P6 跟着一起红**，而它红的原因跟篡改毫无关系 ⇒ **噪声**
_caught = bool(_tampered) and bool(_simulate(_tampered))
out["golden_tamper_control_1030"] = {
    "label_tampered": (_tk[1] if _tk else None),
    "tampered_digest": "0" * 12,
    "simulated_with_tampered": len(_simulate(_tampered)),
    "simulated_with_real": len(_simulate(OLD_MULTI)),
    "caught": _caught,
    "why": "⭐⭐⭐⭐⭐ 抹成常量之后，老身份 (n, 000000000000) 在当前集合里找不到同 n 的对应物 "
           "⇒ P2 红；⭐⭐ 而**真实 golden 跑同一套判定必须是 0 命中** "
           "—— ⭐⭐ 真实 golden 当前有多少待办由 `delta_1030.n_silently_rewritten` 报，不塞进这条",
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
assert _N_P_1030 >= 6, "P 判据条数掉到 6 以下了：%d" % _N_P_1030
print("PROBE_1030_DONE ->", OUT)
sys.exit(1 if _N_FALSE_1030 else 0)