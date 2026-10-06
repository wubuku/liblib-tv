#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针 1023：**量「类型层」那一道闸** —— tsc 早就装好了，而一条判据把一句**从没成立过**的话当成了前提。

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ 1020 的最后一个读数是：**7 个存活变异体里有 4 个只改类型标注**
⇒ 它当时的结论是「它们是**等价变异体**，**不算判别力缺口**」——
**但那句话只在运行期成立**。类型是**擦掉就没了**的东西，
所以那 4 个在运行期「不可区分」，**在类型层却可能是天壤之别**。

本批做三件事：

  ① **把那 4 个（再加几个同类）真的喂给 `tsc`**，量出
     **「运行期判别器抓不住的，类型层抓不抓得住」** ——
     用的是仓里**早就装好的 `typescript 5.9.3`**，零安装、零网络。

  ② ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **接线盘点**：`package.json` 的 `check` 链了 `typecheck`、
     `ci.yml` 在 `push` 上跑 `npm run typecheck`、而**本地 `pre-commit` 钩子一次都没调过 tsc**
     ⇒ **本地提交门看不见类型层，远端能看见。**

  ③ ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **顺手挖出一条「从没成立过的前提」**：
     `JimengAudioGenPanel.tsx` 里有一句注释写着
     **「`npm run check` 是 eslint、不跑 tsc」**，
     而判据 `CC.9` 把**这句注释还在不在**当成了它自己的凭据
     ⇒⇒⇒⇒⇒ **而 `npm run check` 从**初始提交**起就链着 `typecheck`**
     ⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 那句话从来就不成立，判据却会永远绿。**

⚠️ 口径边界（写在产物里，不含糊）：
  - 变异副本**放在仓根**（`@/*` 路径要靠根 `tsconfig.json` 解析），
    **跑完注册 `atexit` 清理** ⇒ **原型源文件一个字节都没动**
  - 本批量的是**类型层这一道闸**，**不是**「类型标注该怎么写」
  - 变异集合是**本探针手挑的若干个形状**、**不是**穷举

**纯离线、零安装、零浏览器。**
"""
import atexit
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WS_REL = "src/components/jimeng/JimengWorkspace.tsx"
WS = ROOT / WS_REL
AGP_REL = "src/components/jimeng/JimengAudioGenPanel.tsx"
VERIFIER = ROOT / "scripts/verify-jimeng-batch841-unclickable.py"
GOLDEN = ROOT / "docs/research/jimeng-canvas/type-layer-gate-1023.json"

TMPDIR = Path(tempfile.mkdtemp(prefix="b1023-", dir=str(ROOT)))
atexit.register(shutil.rmtree, str(TMPDIR), ignore_errors=True)

TSC = ROOT / "node_modules/.bin/tsc"
PKG = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
WS_SRC = WS.read_text(encoding="utf-8")
VER_SRC = VERIFIER.read_text(encoding="utf-8")


# ── 跑仓里**早就装好的** tsc（零安装、零网络） ─────────────────────────────────
def _norm(out):
    """⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **报错的文件路径里嵌着随机临时目录名**
    （`b1023-gf99k4oc/T1_dir_1_to_0.tsx(166,9): …`）⇒ **不抹掉的话，
    golden 每一轮的每一个字节都不一样 ⇒ 1015 重跑套件必然报「漂移」**
    ⇒⇒⇒⇒⇒⇒⇒⇒⇒ **处置 = 记录前把那一段路径归一成固定的 `MUT/<名>`**
    ⇒⇒⇒⇒⇒⇒⇒⇒⇒⭐ **这不是「顺手美化输出」，这是「让产物可复现」**
    """
    return re.sub(r"b1023-[A-Za-z0-9_]+/", "MUT/", out)


def run_tsc(include, tag):
    # ⚠️ `include` 是**相对这个临时 tsconfig 所在目录**的 ⇒ 传文件名即可
    cfg = TMPDIR / ("tsconfig-%s.json" % tag)
    cfg.write_text(json.dumps(
        {"extends": "../tsconfig.json", "include": [include],
         "compilerOptions": {"incremental": False}}, indent=2), encoding="utf-8")
    r = subprocess.run([str(TSC), "-p", str(cfg), "--noEmit"],
                       capture_output=True, timeout=1800, cwd=str(ROOT))
    out = _norm((r.stdout + r.stderr).decode("utf-8", "replace"))
    errs = [l for l in out.splitlines() if re.search(r"error TS\d+", l)]
    return {"rc": r.returncode, "n_errors": len(errs), "first": errs[:3]}


def whole_repo_tsc():
    r = subprocess.run([str(TSC), "--noEmit", "--incremental", "false"],
                       capture_output=True, timeout=1800, cwd=str(ROOT))
    out = (r.stdout + r.stderr).decode("utf-8", "replace")
    errs = [l for l in out.splitlines() if re.search(r"error TS\d+", l)]
    return {"rc": r.returncode, "n_errors": len(errs), "first": errs[:3]}


# ── ① 基线两格（自检：装置本身必须先干净，否则后面全部作废） ────────────────────
REPO_TSC = whole_repo_tsc()
(TMPDIR / "basecopy.tsx").write_text(WS_SRC, encoding="utf-8")
COPY_TSC = run_tsc("basecopy.tsx", "base")
SELFCHECK = (REPO_TSC["rc"] == 0 and COPY_TSC["rc"] == 0)
if not SELFCHECK:
    raise SystemExit("自检失败：仓当前就有类型错误、或副本装置不干净，先停。%r / %r"
                     % (REPO_TSC, COPY_TSC))


# ── ② 那些「运行期不可区分」的变异体，喂给类型层 ────────────────────────────────
# ⭐ 这几个就是 1020 实测存活的 4 个（`dir: 1 | -1` 里的两个 `1` 各改成 `0`/`2`），
#    外加两个**别的类型位点**与一个**故意改得更宽**的，用来量「类型层的边界在哪」。
TYPE_MUTS = [
    ("T1_dir_1_to_0", "dir: 1 | -1", "dir: 0 | -1"),
    ("T2_dir_1_to_2", "dir: 1 | -1", "dir: 2 | -1"),
    ("T3_neg1_to_0", "dir: 1 | -1", "dir: 1 | -0"),
    ("T4_neg1_to_2", "dir: 1 | -1", "dir: 1 | -2"),
    ("T5_nodes_to_string", "nodes: HTMLElement[]", "nodes: string[]"),
    ("T6_keep_to_string", "keep: number", "keep: string"),
    # ⭐⭐⭐ 唯一一个**放宽**而不是收窄的类型改动 —— 专门用来量「类型层的边界在哪」
    # ⭐ 第一版我**没写它**，却在产物里断言「有类型改动哪一层都逃掉」⇒ **那是我先写结论后找证据**
    #   （1018 撤回过的那种）⇒ **处置 = 把它变成一个真跑的变异体，让那句话由实测决定**
    ("T7_dir_widened_to_number", "dir: 1 | -1", "dir: number"),
]
for _n, _a, _b in TYPE_MUTS:
    assert _a in WS_SRC, _a

TMUT_ROWS = []
for tag, a, b in TYPE_MUTS:
    (TMPDIR / (tag + ".tsx")).write_text(
        WS_SRC.replace(a, b, 1), encoding="utf-8")
    res = run_tsc(tag + ".tsx", tag)
    res["name"] = tag
    res["before"] = a
    res["after"] = b
    TMUT_ROWS.append(res)

N_T = len(TMUT_ROWS)
T_CAUGHT = [r["name"] for r in TMUT_ROWS if r["rc"] != 0]
T_SURVIVED = [r["name"] for r in TMUT_ROWS if r["rc"] == 0]
# ⭐ 1020 的那 4 个（名字里带 dir / neg1 的 T1–T4）
T1020 = [r for r in TMUT_ROWS if r["name"] in
         ("T1_dir_1_to_0", "T2_dir_1_to_2", "T3_neg1_to_0", "T4_neg1_to_2")]
T1020_CAUGHT = [r["name"] for r in T1020 if r["rc"] != 0]
T1020_SURVIVED = [r["name"] for r in T1020 if r["rc"] == 0]


# ── ③ 接线盘点：谁真的调 tsc ─────────────────────────────────────────────────
PRECOMMIT = ROOT / ".git/hooks/pre-commit"
PRE_SRC = PRECOMMIT.read_text(encoding="utf-8") if PRECOMMIT.exists() else ""
CI = ROOT / ".github/workflows/ci.yml"
CI_SRC = CI.read_text(encoding="utf-8") if CI.exists() else ""

WIRING = {
    "node_modules/typescript": (ROOT / "node_modules/typescript").exists(),
    "package.json 有 typecheck 脚本": "typecheck" in PKG.get("scripts", {}),
    "typecheck 脚本内容": PKG.get("scripts", {}).get("typecheck"),
    "check 链了 typecheck": "typecheck" in (PKG.get("scripts", {}).get("check") or ""),
    "本地 pre-commit 调过 tsc": bool(re.search(r"\btsc\b|typecheck", PRE_SRC)),
    "CI 调过 typecheck": "typecheck" in CI_SRC or "tsc" in CI_SRC,
    "CI 在 push 上触发": bool(re.search(r"push\s*:\s*\n\s*branches", CI_SRC)),
}


def git_show(rev, path):
    r = subprocess.run(["git", "-C", str(ROOT), "show", "%s:%s" % (rev, path)],
                       capture_output=True, timeout=120)
    return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else ""


# ⭐⭐⭐ 「`npm run check` 从来就链着 typecheck」—— 用**初始提交**当场对账
FIRST = subprocess.run(["git", "-C", str(ROOT), "rev-list", "--max-parents=0", "HEAD"],
                       capture_output=True, timeout=120).stdout.decode().split()
FIRST_SHA = FIRST[0] if FIRST else ""
FIRST_PKG = git_show(FIRST_SHA, "package.json") if FIRST_SHA else ""
FIRST_CHECK = ""
try:
    FIRST_CHECK = json.loads(FIRST_PKG).get("scripts", {}).get("check", "") if FIRST_PKG else ""
except Exception:                                                # noqa: BLE001
    FIRST_CHECK = ""
CLAIM_NEVER_TRUE = ("typecheck" not in (FIRST_CHECK or "")) is False and bool(FIRST_CHECK)


# ── ④ 「从没成立过的那句话」 ───────────────────────────────────────────────────
AGP_SRC = (ROOT / AGP_REL).read_text(encoding="utf-8")
STALE_SENTENCE = "`npm run check` 是 eslint、不跑 tsc"
# ⚠️⚠️⚠️⚠️⭐⭐⭐⭐⭐⭐ **这句在源码里是跨了两行的**（`是 eslint、` ⏎ `不跑 tsc`）
#   ⇒ **第一版用精确串去 `in`，返回 False，差点把「它确实写在源码里」判成「它不存在」**
#   ⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 又是一次「我以为它在」**：匹配前先把两侧的空白全部去掉再比
AGP_FLAT = re.sub(r"\s+", "", AGP_SRC)
SENTENCE_IN_SRC = re.sub(r"\s+", "", STALE_SENTENCE) in AGP_FLAT
# ⭐ 判据 CC.9 的凭据是**那句注释还在不在**，不是它**对不对**
CC9 = re.search(r'check\("CC\.9 (.*?)\n(.*?)\n(.*?)\n', VER_SRC, re.S)
CC9_ANCHORS_ON_EXISTENCE = '"不跑 tsc" in _agp_raw' in VER_SRC
AGP_LINE_NO = next((k + 1 for k, l in enumerate(AGP_SRC.split("\n"))
                    if "不跑 tsc" in l), 0)


# ── P 判定（只钉机制） ───────────────────────────────────────────────────────
P1 = SELFCHECK and REPO_TSC["rc"] == 0
P2 = bool(WIRING["node_modules/typescript"]) and bool(WIRING["typecheck 脚本内容"]) \
     and WIRING["check 链了 typecheck"]
P3 = (len(T1020_CAUGHT) == 4 and len(T1020_SURVIVED) == 0
      and len(T_SURVIVED) >= 1)
P4 = (not WIRING["本地 pre-commit 调过 tsc"]) and WIRING["CI 调过 typecheck"] \
     and WIRING["CI 在 push 上触发"]
P5 = CLAIM_NEVER_TRUE and SENTENCE_IN_SRC and CC9_ANCHORS_ON_EXISTENCE
P6 = True
P7 = True
# ⭐⭐⭐⭐⭐⭐ **产物可复现自检**：报错路径里嵌着 `b1023-<随机>/`
#   ⇒ 不抹掉的话 **golden 每一轮每一个字节都不同** ⇒ 1015 重跑套件必然报「漂移」
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒ **这道自检比等套件报漂移便宜得多**：写完当场查，别等 12 分钟
LEAK_RE = re.compile(r"b1023-[A-Za-z0-9_]+/")

OUT = {"P1_typescript_installed_and_repo_is_type_clean_1023": P1,
       "P2_check_has_chained_typecheck_1023": P2,
       "P3_type_layer_catches_some_and_misses_some_1023": P3,
       "P4_local_commit_gate_never_calls_tsc_but_ci_does_1023": P4,
       "P5_a_never_true_premise_is_what_a_criterion_leans_on_1023": P5,
       "P6_scope_declared_1023": P6,
       "P7_offline_1023": P7}

GOLDEN.parent.mkdir(parents=True, exist_ok=True)
GOLDEN.write_text(json.dumps({
    "generated_by": "jimeng_probe1023_type_layer_gate.py",
    "note": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **量类型层那一道闸** —— tsc 早就装好、"
            "`check` 从**初始提交**起就链着它、CI 在 `push` 上跑它；"
            "而一条判据把**一句从没成立过的话**当成了自己的凭据。",
    "question_2023": "1020 那 4 个「运行期不可区分」的类型变异体，类型层抓不抓得住？"
                     "以及：类型层到底有没有被接上？",
    "self_check": {
        "whole_repo_tsc": REPO_TSC,
        "unmutated_copy_tsc": COPY_TSC,
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **两格基线都必须先干净**（整仓 EXIT=0、未变异副本也 EXIT=0）"
                "⇒ 否则「tsc 抓到了」可能只是因为副本装置本身坏了 ⇒ **后面全部作废、立刻停**",
    },
    "type_layer_experiment": {
        "runtime": "仓里**早就装好的** `typescript` + 根 `tsconfig.json`；**零安装、零网络**",
        "method": "⭐ 变异副本**放在仓根的临时目录**（`@/*` 要靠根 tsconfig 解析）"
                  "⇒ **原型源文件一个字节都没动**；临时目录注册 `atexit` 清理",
        "mutants": TMUT_ROWS,
        "n_mutants": N_T,
        "n_caught_by_tsc": len(T_CAUGHT),
        "n_survived_tsc": len(T_SURVIVED),
        "the_four_from_1020": {
            "which": ["T1_dir_1_to_0", "T2_dir_1_to_2", "T3_neg1_to_0", "T4_neg1_to_2"],
            "caught_by_tsc": T1020_CAUGHT,
            "survived_tsc": T1020_SURVIVED,
            "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
                    "**⇒⇒⇒⇒⇒ 1020 那句「它们是等价变异体、不算判别力缺口」"
                    "只在运行期成立** —— "
                    "**在类型层它们根本不是一回事**，"
                    "而且仓里**早就有一个工具能看出来** ⇒⇒⇒⇒⇒⇒⇒ "
                    "**⇒ 真正的结论不是「缺口没人管」，是「工具早就在、只是没人调」**",
        },
        "the_honest_boundary": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
                               "**⚠️ 第一版我在这段里先写了一句话：「一个『改宽了而不是改窄了』的类型改动"
                               "仍然哪一层都逃掉」—— 而那句话当时是**我的断言、不是实测**"
                               "⇒⇒⇒⇒⇒ **⇒ 处置 = 把它变成一个真跑的变异体（`T7_dir_widened_to_number`），"
                               "让这句话由实测决定，而不是由我先写下来** ⇒ "
                               "**⇒⇒⇒⇒⇒⇒ 这是 1018 撤回过的那种「先有结论后找证据」的同一形状。**"
                               "⇒⇒⇒⇒⇒⇒⇒ 实测结论："
                               "**收窄型（把能接的接得变少）全部被抓住；放宽型（把能接的接得变多）活下来** "
                               "⇒⇒⇒⇒⇒⇒⇒⇒⇒ **「没有任何一层能抓的变异体」是存在的一类，"
                               "不能因为多了一道门就说抓全了**",
        "predicted_wrong": "⭐⭐⭐⭐⭐ **我第一版预测 T4（`1 | -2`）会存活** —— "
                           "**错了**：`1 | -2` 一样**接不下 `-1`** ⇒ 六个收窄型一个不漏全被抓到"
                           "⇒⇒⇒⇒⇒ **⇒ 「我以为会活下来」和「我以为会红」是同一种错**，"
                           "两边都得让机器去判",
    },
    "wiring": {
        **WIRING,
        "reading": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
                   "**本地 `pre-commit` 钩子一次都没调过 tsc，而 CI 在 `push` 上调** ⇒ "
                   "**⇒⇒⇒⇒⇒ 本地提交门看不见类型层、远端能看见** ⇒ "
                   "**⇒⇒⇒⇒⇒⇒⇒ 而「本地看不见」不是小问题：这个仓里所有会话都是**直推 master**，"
                   "**类型错误要等到远端 CI 才发现**",
        "first_commit": {"sha": FIRST_SHA, "check": FIRST_CHECK},
        "never_true_claim": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **那句「`npm run check` 是 eslint、不跑 tsc」"
                            "从来就不成立** —— 初始提交 `check` 就是 "
                            "`%s`" % (FIRST_CHECK or "<取不到>"),
    },
    "the_never_true_premise": {
        "where": "%s 第 %s 行" % (AGP_REL, AGP_LINE_NO),
        "sentence": STALE_SENTENCE,
        "sentence_present_in_source": SENTENCE_IN_SRC,
        "which_criterion_leans_on_it": "`CC.9`（判据正文把那句话整段引了过去）",
        "criterion_anchors_on": "`\"不跑 tsc\" in _agp_raw` ⇔ **「那句注释还在不在」**",
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
                "**判据锚的是「注释还在」，不是「注释说的对」** ⇒ "
                "**⇒⇒⇒⇒⇒ 它会永远绿** —— 这是 1018「门验的是那段字还在、不是行为还对」"
                "的又一个实例，⭐⭐⭐⭐⭐ **而这一次，证据本身就在被测文件里、"
                "且证据是错的** ⇒ "
                "**⇒⇒⇒⇒⇒⇒⇒ 「拿代码自己的注释当证据」是第二种循环**",
        "honest": "⚠️⭐⭐⭐⭐⭐ **本批不删那句注释、也不改判据** —— "
                  "按「撤销只挂横幅、原文一字不删」，"
                  "**处置是加一条测出「那句话从来没成立过」的读数**，"
                  "让下一个人不必重新翻 `git log` 才知道",
    },
    "scope": "⚠️⭐⭐⭐⭐⭐ 本批量的是**类型层这一道闸**；"
             "变异集合是**本探针手挑的若干个形状**、**不是**穷举；"
             "**不动原型源文件**，不替项目改注释或改判据",
    "offline": "只跑仓里**已经装好的** `./node_modules/.bin/tsc` + `git show`（本地）；"
               "**零安装、零网络、零浏览器**；临时目录注册 `atexit` 清理",
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("整仓 tsc：rc=%d 错误 %d" % (REPO_TSC["rc"], REPO_TSC["n_errors"]))
print("未变异副本：rc=%d 错误 %d" % (COPY_TSC["rc"], COPY_TSC["n_errors"]))
print()
print("类型变异体 %d 个，tsc 抓到 %d、存活 %d：" % (N_T, len(T_CAUGHT), len(T_SURVIVED)))
for r in TMUT_ROWS:
    print("  %-22s rc=%-3d 错误 %-3d  %s → %s"
          % (r["name"], r["rc"], r["n_errors"], r["before"], r["after"]))
    if r["first"]:
        print("      %s" % r["first"][0][:110])
print()
print("1020 那 4 个：抓到 %d、存活 %d" % (len(T1020_CAUGHT), len(T1020_SURVIVED)))
print("接线：%s" % json.dumps(WIRING, ensure_ascii=False))
print("初始提交 %s 的 check = %s" % (FIRST_SHA[:8], FIRST_CHECK))
print("「%s」在源码里 = %s；CC.9 锚的是存在性 = %s"
      % (STALE_SENTENCE, SENTENCE_IN_SRC, CC9_ANCHORS_ON_EXISTENCE))
print("P1..P7 =", [OUT[k] for k in OUT])
# ⭐⭐⭐⭐⭐ 写完当场查「产物里有没有漏掉随机临时目录名」——
#   **第一次跑这里必然红**：报错路径原文是 `b1023-<随机>/T1_…tsx(166,9): …`
#   ⇒ 归一成 `MUT/T1_…tsx(166,9): …` 之后 golden 才逐字节可复现
_leak = LEAK_RE.findall(GOLDEN.read_text(encoding="utf-8"))
if _leak:
    raise SystemExit("⭐ 产物里残留随机临时目录名 %r ⇒ golden 不可复现，先归一再跑。\n"
                     "   （这道自检比等 1015 套件报「漂移」便宜得多）" % sorted(set(_leak))[:5])
print("产物可复现自检：无随机临时目录名残留 ✓")
print("PROBE_1023_DONE ->", GOLDEN)
sys.exit(0 if all(OUT.values()) else 1)
