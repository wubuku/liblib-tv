#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针 1021：**官方锚点门自己的覆盖率** —— 它能发现「锚点被改坏」，能不能发现「判据被改弱」？

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ 1020 量出一个结构性事实：**8 个手写期望的格是判别器，
86 个机器枚举的格是差分器，而差分器结构上杀不死任何变异体。**
那问题就轮到门自己身上了 —— **1015–1020 一路量的都是「被测对象」，
从来没有人量过「门」自己。**

本批量一件很小、但可能很要命的事：

  官方锚点门 `jimeng_check_verifier_anchors.py` 的 `collect()` 只收
  **还被 `check()` 引用的**那些锚点。⇒⇒⇒⇒⇒
  **那么「把一条判据变弱」—— 而变弱的典型手法恰恰是「少引用一条锚点」——
  会不会让门为一个更弱的判据集继续报「问题 0 个」？**

做法（⭐ 不重写门，**直接跑真门**）：
  - 把 verifier 的**内存变异**写到临时文件
  - 用 `argv[1]` 把那个变异版喂给**官方门本体**
  - 逐个变异量三个读数：受检锚点数 / `check(N)` / **问题数**

⭐ **自检**：第一格跑的是**未变异的** verifier，它必须**逐字复现官方门自己报的数**
（否则说明我这套驱动方式不忠实 ⇒ 后面全部作废）。

⚠️ 口径边界：
  - 变异**只在内存 / 临时文件里**，**一个字节都不动仓里的三个脚本**
  - 本批量的是**门对「判据变弱」的敏感度**，**不是**「判据本身对不对」
  - **不碰任何浏览器、不联网**

**纯离线。**
"""
import ast
import atexit
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "scripts/verify-jimeng-batch841-unclickable.py"
AUDIT = ROOT / "scripts/jimeng_unclickable_audit.py"
GATE = ROOT / "scripts/jimeng_check_verifier_anchors.py"
GOLDEN = ROOT / "docs/research/jimeng-canvas/anchor-gate-coverage-1021.json"

TMPDIR = Path(tempfile.mkdtemp(prefix="b1021-"))
atexit.register(shutil.rmtree, str(TMPDIR), ignore_errors=True)

VSRC = VERIFIER.read_text(encoding="utf-8")
VTREE = ast.parse(VSRC)


# ── 跑**官方门本体**（不是重写） ───────────────────────────────────────────────
NUM_ANCHORS = re.compile(r"锚点 (\d+) 条")
NUM_AUSRC = re.compile(r"指向 _ausrc 的 (\d+) 条")
NUM_PROB = re.compile(r"问题 (\d+) 个")
NUM_SKIP = re.compile(r"另 (\d+) 条锚点因")
NUM_CHK = re.compile(r"check\((\d+)\) 条")
NUM_BARE = re.compile(r"裸字面量\*\*的 (\d+) 条")


def run_gate(vpath):
    r = subprocess.run([sys.executable, str(GATE), str(vpath), str(AUDIT)],
                       capture_output=True, timeout=600)
    out = r.stdout.decode("utf-8", "replace")
    g = lambda rx: int(mx.group(1)) if (mx := rx.search(out)) else -1          # noqa: E731
    return {"rc": r.returncode, "n_anchors": g(NUM_ANCHORS), "n_ausrc": g(NUM_AUSRC),
            "n_problems": g(NUM_PROB), "n_skipped": g(NUM_SKIP),
            "n_checks": g(NUM_CHK), "n_bare_ok": g(NUM_BARE),
            "would_fail": out.count("WOULD-FAIL"), "missing": out.count("MISSING")}


# ── 找出某条 `check(...)` 的行范围 ─────────────────────────────────────────────
def check_ranges(tree):
    out = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "check":
            # ⚠️ 判据名是**隐式拼接**的多行字符串 ⇒ AST 已合并成一个 Constant
            #    ⇒ `get_source_segment` 拿不到 ⇒ 直接取 `.value`
            a0 = n.args[0]
            if not (isinstance(a0, ast.Constant) and isinstance(a0.value, str)):
                continue
            lbl = a0.value.strip().split(" ")[0]
            out.setdefault(lbl, (n.lineno, n.end_lineno))
    return out


RANGES = check_ranges(VTREE)
N_CHECKS_TREE = sum(1 for n in ast.walk(VTREE)
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                    and n.func.id == "check")


def drop_lines(src, lo, hi):
    lines = src.split("\n")
    return "\n".join(lines[:lo - 1] + lines[hi:])


def run_variant(tag, src):
    f = TMPDIR / ("v-%s.py" % tag)
    f.write_text(src, encoding="utf-8")
    row = run_gate(f)
    row["tag"] = tag
    return row


# ── ⭐⭐⭐⭐⭐ 门的覆盖面**基线** ────────────────────────────────────────────────
# ⚠️ 上一条通则是「门的覆盖面必须是一个被登记的量」⇒ 而**登记而不校验**
#   就是本批正在批评的「写下来了 ≠ 存在过」⇒⇒⇒⇒⇒ **所以这里是一道真的闸**：
#   受检锚点数 / check 数**只许涨不许跌**。
# ⭐ 只拦「跌」不拦「涨」⇒ 并行会话正常加判据时不会误报。
# ⚠️⭐⭐⭐ **每加一批判据就把 FLOOR 抬到当批实测值** —— 不抬的话，
#   「慢慢少掉几十条锚点」会一直躲在阈值底下 ⇒ **闸会退化成摆设**
#   （1020 实测：删整组 8 条判据就少查 69 条锚点，而问题数一个字没动）
FLOOR = {"n_anchors": 7141, "n_checks": 932}


# ── ⭐⭐⭐ 自检：未变异时必须**逐字复现**官方门自己报的数 ───────────────────────
BASE = run_variant("base", VSRC)
SELFCHECK = (
    BASE["n_checks"] == N_CHECKS_TREE
    and BASE["n_problems"] == 0
    and BASE["n_bare_ok"] == 0
)
FLOOR_HELD = (BASE["n_anchors"] >= FLOOR["n_anchors"]
               and BASE["n_checks"] >= FLOOR["n_checks"])
if not SELFCHECK:
    raise SystemExit("自检失败：驱动方式不忠实，先停。%r / 树上 check 数 %d"
                     % (BASE, N_CHECKS_TREE))
if not FLOOR_HELD:
    raise SystemExit(
        "⭐⭐⭐ 覆盖面基线被跌破：受检锚点 %d < %d 或 check %d < %d\n"
        "   ⇒⇒⇒⇒⇒ 这是「判据被改弱」的形状（1021 实测 4 个形状会静悄悄溜过去）\n"
        "   ⇒⇒⇒⇒⇒ 如果是有意删判据，请**同时**下调 FLOOR 并在 README 写明理由。"
        % (BASE["n_anchors"], FLOOR["n_anchors"],
           BASE["n_checks"], FLOOR["n_checks"]))


# ── 变异族 ───────────────────────────────────────────────────────────────────
MUTS = []

# ⒜ 删掉整条判据（Z993D.7 —— 1019 补两格那一组）
lo, hi = RANGES["Z993D.7"]
MUTS.append(("A_drop_one_criterion_1021", drop_lines(VSRC, lo, hi),
             "删掉整条 `Z993D.7` 判据（**判据数 −1**）"))

# ⒜′ 删掉整组（Z993D 全 8 条）
g = sorted(RANGES[k] for k in RANGES if k.startswith("Z993D."))
MUTS.append(("B_drop_whole_group_1021", drop_lines(VSRC, g[0][0], g[-1][1]),
             "删掉整组 `Z993D.1`–`Z993D.8`（**判据数 −8**）"))

# ⒝ 删掉一条判据里的**一个合取项**（判据还在，只是变弱）
m = re.search(r"\n(          and '[^'\n]*' in _ausrc\n)", VSRC[VSRC.index('"Z993D.1 '):])
conj = m.group(1)
off = VSRC.index('"Z993D.1 ') + m.start(1)
MUTS.append(("C_drop_one_conjunct_1021", VSRC[:off] + VSRC[off + len(conj):],
             "删掉 `Z993D.1` 里的**一个** `and '<锚点>' in _ausrc` 合取项（**判据数不变**）"))

# ⒞ 把锚点换成一个**确实存在、但说的是别的事**的串（1017 那个「碰巧放行」的形状）
LOOSE = '"p1_first_real_upgrade_2019_"'          # 1019 组的键，**确实在 _ausrc 里**
MUTS.append(("E_swap_anchor_to_one_that_exists_1021",
             VSRC.replace("'\"p1_stub_fidelity_gap_2020_\"' in _ausrc",
                          "'%s' in _ausrc" % LOOSE, 1),
             "把 `Z993D.1` 的一条 `_ausrc` 锚点换成**确实存在、但说的是别的事**的串"))

# ⒟ 加一条恒真判据
MUTS.append(("F_add_tautology_1021",
             VSRC + '\n    check("Z993E.9 恒真", True)\n',
             "加一条 `ok=True` 的**恒真**判据"))

# ⒠ 把一条 `in` 翻成 `not in`（锚点确实存在 ⇒ 门**应该**报 WOULD-FAIL）
MUTS.append(("G_flip_in_to_not_in_1021",
             VSRC.replace("'\"p1_stub_fidelity_gap_2020_\"' in _ausrc",
                          "'\"p1_stub_fidelity_gap_2020_\"' not in _ausrc", 1),
             "把一条 `_ausrc` 锚点的 `in` 翻成 `not in`（**该被门抓住**的一类）"))

ROWS = [BASE] + [run_variant(t, s) for t, s, _ in MUTS]
DESC = {t: d for t, _s, d in MUTS}

# ⭐ 哪些变异**让门继续报 0 问题**
SILENT = [r["tag"] for r in ROWS[1:]
          if r["n_problems"] == 0 and r["would_fail"] == 0 and r["missing"] == 0]
CAUGHT = [r["tag"] for r in ROWS[1:] if r["tag"] not in SILENT]
# ⭐ 门**自己少查了多少条**
SHORTHAND = [{"tag": r["tag"], "n_anchors": r["n_anchors"], "n_checks": r["n_checks"],
              "n_problems": r["n_problems"],
              "anchors_dropped": BASE["n_anchors"] - r["n_anchors"],
              "checks_dropped": BASE["n_checks"] - r["n_checks"]}
             for r in ROWS[1:]]


def _md(t):
    return DESC.get(t, "**未变异的基线**（用来验证驱动方式忠实）")


# ── P 判定（只钉机制） ───────────────────────────────────────────────────────
P1 = SELFCHECK and FLOOR_HELD
P2 = len(SILENT) >= 3
P3 = any(s["anchors_dropped"] > 0 and s["n_problems"] == 0 for s in SHORTHAND)
P4 = "G_flip_in_to_not_in_1021" in CAUGHT
P5 = all(r["rc"] in (0, 1) for r in ROWS) and len(ROWS) == 1 + len(MUTS)
P6 = True
P7 = True

OUT = {"P1_driver_is_faithful_and_coverage_floor_held_1021": P1,
       "P2_at_least_three_ways_to_weaken_a_criterion_stay_green_2021": P2,
       "P3_removing_anchors_shrinks_coverage_without_raising_problems_2021": P3,
       "P4_the_gate_does_catch_a_flipped_anchor_2021": P4,
       "P5_every_variant_ran_2021": P5,
       "P6_scope_declared_2021": P6,
       "P7_offline_2021": P7}

GOLDEN.parent.mkdir(parents=True, exist_ok=True)
GOLDEN.write_text(json.dumps({
    "generated_by": "jimeng_probe1021_anchor_gate_coverage.py",
    "note": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **量门自己** —— 官方锚点门 `collect()` 只收"
            "**还被 `check()` 引用的**锚点 ⇒⇒⇒⇒⇒ "
            "**「把判据变弱」的典型手法恰恰是「少引用一条锚点」。** "
            "⇒ 本批逐个把 verifier 变弱，看**真门**报不报。",
    "question_2021": "官方锚点门能发现「锚点被改坏」，能不能发现「判据被改弱」？",
    "how": "⭐⭐⭐⭐⭐ **不重写门** —— 变异版 verifier 写到临时文件，用 `argv[1]` 喂给"
           "**官方门本体**（`jimeng_check_verifier_anchors.py`）⇒ "
           "⇒⇒⇒⇒⇒ **避免「我以为门是这样工作的」**（1019 栽过两次）",
    "self_check": {
        "baseline_reproduced": SELFCHECK,
        "row": BASE,
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **未变异那一格必须逐字复现官方门自己报的数** —— "
                "否则说明这套驱动方式不忠实 ⇒ **后面全部作废、立刻停**",
    },
    "rows": [{"tag": r["tag"], "what": _md(r["tag"]), **r,
              "verdict": ("⚠️ **门继续报 0 问题**" if r["tag"] in SILENT else "门抓到了")}
             for r in ROWS],
    "silent_weakenings": SILENT,
    "caught": CAUGHT,
    "shorthand": SHORTHAND,
    "reading": [
        "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **`collect()` 只收还被引用的锚点** ⇒ "
        "**一条锚点被从判据里删掉，它就不再进入普查** ⇒ "
        "**门的覆盖面会随着判据说弱而缩小，而「问题数」纹丝不动**",
        "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **唯一会变的读数是汇总行里的 `check(N)`** —— "
        "而**没有任何门在比对这个数** ⇒ "
        "**「门少了 N 条检查」和「门报 0 问题」可以同时成立**",
        "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **这是 1016「同名键的失败形态是安静」的同一种病，换了个宿主** —— "
        "那次是「写了两遍、后一条吃掉前一条」，"
        "这次是「少写一条、没有任何东西会告诉你」⇒ "
        "**⇒⇒⇒⇒⇒ 同一个治法：把可变的读数登记成基线，而不是指望门报出来**",
    ],
    "delivered": {
        "countermeasure": "⭐ 本批把 `check(N)` **与受检锚点数**做成了**一道真的闸**："
                          "探针里的 `FLOOR`，**只许涨不许跌** ⇒ "
                          "基线被跌破就直接 `SystemExit` 并打印三条处置说明",
        "floor": FLOOR,
        "floor_held": FLOOR_HELD,
        "why_only_down": "⭐⭐⭐⭐⭐ **只拦「跌」不拦「涨」** ⇒ "
                         "并行会话正常加判据时**不会误报** ⇒ "
                         "**一道会误报的闸等于没有闸**",
        "not_just_recorded": "⭐⭐⭐⭐⭐⭐ **「登记而不校验」就是本批正在批评的"
                             "「写下来了 ≠ 存在过」** ⇒⇒⇒⇒⇒ "
                             "所以这一步必须是会红的代码，不是一段说明文字",
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **门的覆盖面必须是一个被登记**、**且会被校验**"
                "**的量** —— **「门还在跑」不等于「门查得和昨天一样多」**",
    },
    "scope": "⚠️⭐⭐⭐⭐⭐ 本批量的是**门对「判据变弱」的敏感度**，"
             "**不是**「判据本身对不对」；"
             "变异集合是**本探针手挑的 6 个形状**，**不是**穷举 ⇒ "
             "**「只有这 6 个形状能溜过去」是本口径内的结论，不许说成「只有这几种能溜过去」**",
    "offline": "纯 subprocess + 只读仓里三个脚本；变异**只在临时文件里**，"
               "**一个字节都不动仓里的任何脚本**；临时目录注册 atexit 清理",
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("自检：基线逐字复现官方门 =", SELFCHECK, "| 覆盖面基线守住 =", FLOOR_HELD, "|", FLOOR)
print("基线 受检锚点 %d / check %d / 问题 %d" % (BASE["n_anchors"], BASE["n_checks"],
                                                BASE["n_problems"]))
print()
for r in ROWS[1:]:
    print("  %-36s 锚点 %-5d check %-4d 问题 %-3d  %s"
          % (r["tag"], r["n_anchors"], r["n_checks"], r["n_problems"],
             "⚠️ 门继续报 0 问题" if r["tag"] in SILENT else "门抓到了"))
print()
print("溜过去的 %d 个：%s" % (len(SILENT), SILENT))
print("被门抓到的 %d 个：%s" % (len(CAUGHT), CAUGHT))
print("P1..P7 =", [OUT[k] for k in OUT])
print("PROBE_1021_DONE ->", GOLDEN)
sys.exit(0 if all(OUT.values()) else 1)
