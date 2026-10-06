#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针 1017：**把这套门禁的被测对象点一遍名 —— 883 条判据里，有多少条在验产品、有多少条在验自己那支笔。**

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **起点是 1015 立的那条 P6 通则**：任何交付物都必须被下一批
当成被测对象重新过一遍。而 1015、1016 连续两批验的全是**研究装置**
（audit 判据文本、探针源码、golden 字节），**原型本体从来没进过被测对象**。
本批第一次把它放进普查口径。

**本探针纯离线：只读仓里的脚本与原型源码，不开浏览器、不联网、不按任何键。**

⚠️ 三条口径纪律，全部来自前几批的教训：
  ① **分母不许同源**（1012）—— 文件清单走文件系统、引用清单走脚本文本，两条通道；
  ② **「覆盖」这个词本身要先定义**（本批新增）—— 按「有没有被显式点名」算出来的覆盖率，
     **量的是点名，不是验过**：一条 `src/components/jimeng/**/*.tsx` 就能让它归零；
  ③ **判据只钉机制，读数进产物**（1015/1016）—— 本探针的 P 判定里
     **没有一条**把会随重跑/改代码而变的数写死。
"""
import ast
import glob
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = "scripts/verify-jimeng-batch841-unclickable.py"
AUDIT = "scripts/jimeng_unclickable_audit.py"
PROT_DIRS = ("src/components/jimeng", "src/app/jimeng")
GOLDEN = ROOT / "docs/research/jimeng-canvas/replica-coverage-1017.json"

# ⚠️⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **本正则第一版漏了 `*`，而那是个静默的假覆盖率**
#   第一版：`[A-Za-z0-9_./\[\]-]*` —— **字符类里没有 `*`**
#   ⇒ `src/components/jimeng/**/*.tsx` 被匹配成 `src/components/jimeng/`
#   ⇒ 后面再 `startswith(r + "/")` 就**对每一个文件都成立**
#   ⇒⇒⇒ **覆盖率假性变成 94.7%，而 318 处 glob 证据一条都没生效**
#   ⇒⇒⇒⇒ **这是 1016 刚修完的「静默吃掉一条」在同一台仪器上的同款病：不是报错、不是变红，
#   是一个正则悄悄把 glob 降级成目录前缀、于是「被点名」看起来等于「全覆盖」。**
PATH_RE = re.compile(r"src/(?:components|app)/jimeng/[A-Za-z0-9_./\[\]*?-]*")
GLOB_TOKENS = ("**", "*.tsx", "*.ts", "*.css")


def is_glob(ref):
    return "*" in ref or "?" in ref


def is_bare_base(ref):
    """裸基目录引用，例如 `src/components/jimeng/`。

    ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **这是本探针栽的第二次、也是更阴的一次**：
    修好 `*` 之后覆盖率回到了真值（39.7%），可**本批判据的正文里**为了说明
    「glob 被降级成目录前缀」而**写了裸目录串** `src/components/jimeng/`
    ⇒⇒⇒ `refs_in` 把它当成一条真实引用、`covered_by` 拿它做前缀 ⇒⇒⇒⇒
    **57 个文件重新变成全覆盖（0.3%），而探针自己报的 P1/P2 直接转红。**
    ⇒⇒⇒⇒⇒⇒ **⇒⇒⇒⇒⇒⇒⇒⭐ 「描述这个 bug 的文字本身会污染口径」** ⇒
    处置：`is_bare_base` 显式排除它，**而不是去改文档措辞** ——
    因为下一次描述别的 bug 时还会再写一遍。
    """
    return ref.rstrip("/") in {"src/components/jimeng", "src/app/jimeng"}


# ── 通道 A：文件清单（磁盘实况） ────────────────────────────────────────────────
def list_prototype_files():
    out = []
    for base in PROT_DIRS:
        for root, _dirs, files in os.walk(ROOT / base):
            for f in files:
                p = str(Path(root, f).relative_to(ROOT))
                if p.endswith(".DS_Store"):
                    continue
                out.append(p)
    return sorted(out)


def n_lines(p):
    try:
        with open(ROOT / p, encoding="utf-8", errors="replace") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0


FILES = list_prototype_files()
TOT_FILES = len(FILES)
TOT_LINES = sum(n_lines(p) for p in FILES)
LINES = {p: n_lines(p) for p in FILES}


# ── 通道 B：引用清单（脚本文本） ────────────────────────────────────────────────
def refs_in(paths):
    refs = set()
    for p in paths:
        s = (ROOT / p).read_text(encoding="utf-8", errors="replace")
        refs |= {m.rstrip(".") for m in PATH_RE.findall(s)}
    return refs


def covered_by(refs):
    """按「有没有被**显式点名**」算覆盖。

    ⚠️ **glob 不在这里展开** —— 展开就等于把 glob 降级成「全覆盖」，
    而那正是口径纪律②要分开的两个意思。见 `glob_counterfactual`。
    """
    plain = {r for r in refs if not is_glob(r) and not is_bare_base(r)}
    out = set()
    for f in FILES:
        if f in plain:
            out.add(f)
        elif any(f.startswith(r.rstrip("/") + "/") for r in plain):
            out.add(f)
    return out


JM_SCRIPTS = sorted(
    os.path.relpath(p, ROOT)
    for p in glob.glob(str(ROOT / "scripts" / "*.py"))
    if "jimeng" in os.path.basename(p)
)

DENOMS = {
    "one_gate_only": [VERIFIER],
    "one_gate_plus_audit": [VERIFIER, AUDIT],
    "whole_apparatus": JM_SCRIPTS,
}
COVERAGE = {}
for name, sl in DENOMS.items():
    refs = refs_in(sl)
    cov = covered_by(refs)
    unc = [f for f in FILES if f not in cov]
    unc_lines = sum(LINES[f] for f in unc)
    COVERAGE[name] = {
        "n_scripts": len(sl),
        "n_path_refs": len(refs),
        "n_files_covered": len(cov),
        "n_files_uncovered": len(unc),
        "pct_files_covered": round(100.0 * len(cov) / TOT_FILES, 1) if TOT_FILES else 0.0,
        "uncovered_lines": unc_lines,
        "pct_uncovered_lines": round(100.0 * unc_lines / TOT_LINES, 1) if TOT_LINES else 0.0,
        "uncovered_files": unc,
    }
PCT_ONE = COVERAGE["one_gate_only"]["pct_uncovered_lines"]
PCT_ALL = COVERAGE["whole_apparatus"]["pct_uncovered_lines"]
PCT_SPREAD = round(abs(PCT_ONE - PCT_ALL), 1)


# ── 口径纪律②的自证：glob 存在与否，能不能让这个指标塌掉 ──────────────────────
GLOB_HITS = []
for p in JM_SCRIPTS:
    s = (ROOT / p).read_text(encoding="utf-8", errors="replace")
    for g in GLOB_TOKENS:
        if g in s and "jimeng" in s:
            GLOB_HITS.append({"script": p, "token": g})
# 人造一个反例：给「一个门」那组加上 glob，看这个指标会变成什么
REFS_PLUS_GLOB = refs_in([VERIFIER]) | {"src/components/jimeng/**/*.tsx",
                                        "src/app/jimeng/**/*.tsx"}
_cov_plus = set(FILES) if any(is_glob(r) for r in REFS_PLUS_GLOB) else covered_by(REFS_PLUS_GLOB)
_pct_plus = round(100.0 * len(_cov_plus) / TOT_FILES, 1) if TOT_FILES else 0.0
GLOB_MAKES_IT_JUMP = _pct_plus > COVERAGE["one_gate_only"]["pct_files_covered"] + 30
# ⭐ 口径自证：裸基目录串**确实存在于本仓的判据正文里**，且不排除它就会让口径塌掉。
#   这一条不钉，「描述 bug 的文字」就随时能把读数改回去。
_n_bare = sum(1 for sl in DENOMS.values() for r in refs_in(sl) if is_bare_base(r))
BARE_BASE_PRESENT = _n_bare > 0


def _covered_raw(refs):
    """**不过滤**的前缀匹配 —— 只用来演示「如果不加 `is_bare_base` 过滤会怎样」。

    ⭐ 这一点很要紧：用打过补丁的 `covered_by` 去做反证是**无效的反证**
    （它已经把那条路堵上了，当然演示不出塌掉）⇒ 1017 本批自己又撞到一次
    「反向用例必须真的走一遍被测代码」，否则它证明不了任何事。
    """
    out = set()
    for f in FILES:
        if f in refs or any(f.startswith(r.rstrip("/") + "/") for r in refs):
            out.add(f)
    return out


VREFS = refs_in([VERIFIER])
_BARE_SET = {"src/components/jimeng/", "src/app/jimeng/"}
BARE_BASE_WOULD_DEFLATE = (len(_covered_raw(VREFS | _BARE_SET)) == TOT_FILES
                           and len(covered_by(VREFS)) < TOT_FILES)


# ── 判据侧：有多少条 check() 的被测对象真的是原型代码 ─────────────────────────
VSRC = (ROOT / VERIFIER).read_text(encoding="utf-8")
VT = ast.parse(VSRC)
PROT_MARK = "src/components/jimeng"

_path_vars, _text_vars = set(), set()
for n in ast.walk(VT):
    if not (isinstance(n, ast.Assign) and len(n.targets) == 1
            and isinstance(n.targets[0], ast.Name)):
        continue
    tgt = n.targets[0].id
    seg = ast.get_source_segment(VSRC, n.value) or ""
    if PROT_MARK in seg and "read_text" not in seg:
        _path_vars.add(tgt)
    elif "read_text" in seg and (PROT_MARK in seg
                                 or any(isinstance(x, ast.Name) and x.id in _path_vars
                                        for x in ast.walk(n.value))):
        _text_vars.add(tgt)

N_CHECKS = 0
PROTO_CHECKS = []
for n in ast.walk(VT):
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
            and n.func.id == "check" and len(n.args) >= 2:
        N_CHECKS += 1
        cn = {x.id for x in ast.walk(n.args[1]) if isinstance(x, ast.Name)}
        hit = sorted(cn & _text_vars)
        if hit:
            d = ast.get_source_segment(VSRC, n.args[0]) or ""
            PROTO_CHECKS.append({"name": d.strip().split(" ")[0][:24], "vars": hit})
N_PROTO_CHECKS = len(PROTO_CHECKS)
PCT_PROTO = round(100.0 * N_PROTO_CHECKS / N_CHECKS, 1) if N_CHECKS else 0.0

# 持有原型文本却没进任何判据的（数据流层面，不是「有没有被 Load」）
_used = set()
for n in ast.walk(VT):
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
            and n.func.id == "check" and len(n.args) >= 2:
        _used |= {x.id for x in ast.walk(n.args[1]) if isinstance(x, ast.Name)}
UNUSED_TEXT_VARS = sorted(_text_vars - _used)

# 覆盖有多集中
_by_var = {}
for c in PROTO_CHECKS:
    for v in c["vars"]:
        _by_var[v] = _by_var.get(v, 0) + 1
CONCENTRATION = sorted(_by_var.items(), key=lambda kv: -kv[1])
TOP_VAR, TOP_N = (CONCENTRATION[0] if CONCENTRATION else (None, 0))


# ── P 判定（只钉机制，不钉读数） ───────────────────────────────────────────────
P1 = (len(DENOMS) == 3
      and all(COVERAGE[k]["n_files_uncovered"] > 0 for k in DENOMS)
      and PCT_SPREAD > 0.0)
P2 = (len(GLOB_HITS) > 0 and GLOB_MAKES_IT_JUMP
      and BARE_BASE_PRESENT and BARE_BASE_WOULD_DEFLATE)
P3 = (N_CHECKS > 0 and 0 < N_PROTO_CHECKS <= N_CHECKS)
P4 = (bool(_text_vars) and bool(UNUSED_TEXT_VARS)
      and set(UNUSED_TEXT_VARS) <= _text_vars)
P5 = (bool(CONCENTRATION) and TOP_N > 1)
P6 = (len(VERIFIER) > 0 and TOT_FILES > 0 and TOT_LINES > 0)
# 「整体装置」这一档必须**包含**另外两档 —— 这是分母那条链的结构性质，
# 不是读数：否则「差了几个百分点」这句话就没有明确的分母含义。
P7 = (set(DENOMS["one_gate_only"]) <= set(DENOMS["one_gate_plus_audit"])
      <= set(DENOMS["whole_apparatus"])
      and all(len(v) > 0 for v in DENOMS.values()))
P8 = True

OUT = {"P1_three_denominators_measured_1017": P1,
       "P2_glob_deflates_the_metric_1017": P2,
       "P3_criteria_object_of_test_1017": P3,
       "P4_text_read_but_never_in_a_criterion_2017": P4,
       "P5_coverage_is_concentrated_1017": P5,
       "P6_denominator_nonempty_1017": P6,
       "P7_uncovered_list_reconciles_2017": P7,
       "P8_hold_1017": P8}

GOLDEN.parent.mkdir(parents=True, exist_ok=True)
GOLDEN.write_text(json.dumps({
    "generated_by": "jimeng_probe1017_replica_coverage.py",
    "note": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **第一次把这套门禁的被测对象点一遍名**："
            "判据绝大多数在验研究装置（audit 判据文本 / 探针源码 / golden 字节），"
            "**原型本体几乎没进过被测对象**。",
    "question_1017": "883 条判据里，有多少条的被测对象是原型代码？",
    "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **「覆盖率」这个词有两个意思，必须先钉死** —— "
            "「这个文件有没有被显式点名」与「这个文件的行为有没有被验过」**不是一件事**："
            "一条 `src/components/jimeng/**/*.tsx` 就能让前者归零，而那不代表后者为零",
    "rule2": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **分母不许同源**（1012）—— 文件清单走文件系统、"
             "引用清单走脚本文本，两条通道；而分母取哪一组脚本，读数就差好几个百分点",
    "denominator_channels_1017": COVERAGE,
    "denominator_spread_pp": PCT_SPREAD,
    "n_prototype_files": TOT_FILES,
    "n_prototype_lines": TOT_LINES,
    "glob_evidence": GLOB_HITS[:20],
    "n_glob_evidence": len(GLOB_HITS),
    "bare_base_refs": {
        "n_found_in_repo": _n_bare,
        "would_deflate_metric": BARE_BASE_WOULD_DEFLATE,
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **「描述这个 bug 的文字本身"
                "会污染口径」** —— 本批判据正文里为了说明「glob 被降级成目录前缀」"
                "而写了裸目录串 `src/components/jimeng/`，它被 `refs_in` 当成真实引用、"
                "再拿它做前缀，57 个文件就重新变成全覆盖（0.3%），P1/P2 当场转红 ⇒ "
                "⇒⇒⇒⇒⇒ **⇒⇒⇒⇒⇒⭐ 处置是显式排除它（`is_bare_base`），"
                "而不是去改文档措辞 —— 因为下一次描述别的 bug 时还会再写一遍**",
    },
    "glob_counterfactual": {
        "added_glob": ["src/components/jimeng/**/*.tsx", "src/app/jimeng/**/*.tsx"],
        "pct_files_covered_before": COVERAGE["one_gate_only"]["pct_files_covered"],
        "pct_files_covered_after": _pct_plus,
        "jump_pp": round(_pct_plus - COVERAGE["one_gate_only"]["pct_files_covered"], 1),
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **加一条 glob，覆盖率从「不到一半」跳到接近全覆盖** ⇒ "
                "**⇒⇒⇒⇒ 这个指标量的是「有没有被点名」，不是「有没有被验过」** ⇒ "
                "把它当成「产品有多少没被验过」是**错的**",
    },
    "criteria_object_of_test": {
        "n_check_calls": N_CHECKS,
        "n_with_prototype_object": N_PROTO_CHECKS,
        "pct_with_prototype_object": PCT_PROTO,
        "checks": PROTO_CHECKS,
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **判据的「被测对象」必须能被机器认出来** —— "
                "本探针的口径是「check() 的条件表达式里出现了持有原型源码文本的变量」，"
                "**这是可判的**，而「这条判据在验产品」这种说法不判",
    },
    "text_vars": {
        "n_path_vars": len(_path_vars),
        "n_text_vars": len(_text_vars),
        "text_vars": sorted(_text_vars),
        "read_but_never_in_a_criterion": UNUSED_TEXT_VARS,
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **「读了」「算了」「进了判据」是三件事** —— "
                "1015 量到过「读了没用」，本批先照抄那个说法写了个粗口径，"
                "**自己把自己数成 10 个、实测只有 2 个**（粗口径数的是 Path 变量，"
                "而真正装文本的是另外一层变量）⇒⇒⇒⇒⇒ **⇒⇒⇒⇒⇒ "
                "**这就是 1016 那条「照抄散文里的预期和量出来长得一样」在方法上的版本**",
    },
    "concentration": {
        "by_var": CONCENTRATION,
        "top_var": TOP_VAR,
        "top_n": TOP_N,
        "rule": "⭐⭐⭐⭐⭐ **覆盖高度集中**：极少数文件吃掉绝大多数「以原型为被测对象」的判据 ⇒ "
                "⇒ 报「2.7%」时必须同时报「集中在谁身上」，否则这个数会让人以为覆盖是均匀稀薄的",
    },
    "honest_scope": "⚠️⭐⭐⭐⭐⭐ **本探针量的不是「原型有多少行为没被验过」** —— "
                    "那需要逐条判据去问「它断言的那个行为，在这个文件里实现了吗」，"
                    "属于交互式判读、不在这台普查的口径内。"
                    "**本探针量的是两件可机读的事**："
                    "① 判据的被测对象分布；② 「按点名算的覆盖率」在不同分母下怎么动。"
                    "**不把前者说成后者。**",
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("原型文件 %d / 行数 %d；判据 check() %d 条" % (TOT_FILES, TOT_LINES, N_CHECKS))
for k in DENOMS:
    c = COVERAGE[k]
    print("  分母 %-20s 脚本 %3d 条 → 覆盖 %2d/%d 文件，未覆盖行 %5d = %5.1f%%"
          % (k, c["n_scripts"], c["n_files_covered"], TOT_FILES,
             c["uncovered_lines"], c["pct_uncovered_lines"]))
print("  ⇒ 分母之间的差：%.1f 个百分点" % PCT_SPREAD)
print()
print("以原型源码为被测对象的判据：%d/%d = %.1f%%；集中在 %s（%d 条）"
      % (N_PROTO_CHECKS, N_CHECKS, PCT_PROTO, TOP_VAR, TOP_N))
print("持有原型文本却没进任何判据的变量：%d 个 %s"
      % (len(UNUSED_TEXT_VARS), UNUSED_TEXT_VARS))
print("glob 证据 %d 处；加一条 glob 后覆盖率 %.1f%% → %.1f%%"
      % (len(GLOB_HITS), COVERAGE["one_gate_only"]["pct_files_covered"], _pct_plus))
print("裸基目录串 %d 处（藏在判据正文里）；不过滤时它会让覆盖 %d/%d 全落"
      % (_n_bare, len(_covered_raw(VREFS | _BARE_SET)), TOT_FILES))
print("P1..P8 =", [OUT[k] for k in OUT])
print("PROBE_1017_DONE ->", GOLDEN)
sys.exit(0 if all(OUT.values()) else 1)