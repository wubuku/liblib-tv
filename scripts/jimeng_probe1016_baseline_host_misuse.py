#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针 1016：`SOURCE_BASELINE` 这张「层表」被当成通用抽屉用了。

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **1016 的起点是一个上一批明写下来、说「留给下一批」的东西**：
`jimeng_unclickable_audit.py` 的 `SOURCE_BASELINE` 顶层 17 键**全部是层 `data-testid`**，
而 900–939 这一串批次的结论键**全部挂在 `audio-voice-filter-listbox`（音色筛选下拉）条目下面**
—— 那是 900 批起的既有挂载惯例。后果有二，一条已知、一条本批才发现。

已知（939 已登记）：按层取（`SOURCE_BASELINE.get(tid)`）取不到那 40 条，且它们污染音色筛选那个条目。

⭐ 本批才发现（**而它是静默的**）：**那 40 条里有一条键名被写了两次。**
`source_reverse_lap_cycle_is_constant_931` 在字面量里出现两次 ——
一次是 931 的**正文**（行 3800），一次是 932 的**收窄横幅 + 932 读数**（行 3855）。
⇒ Python dict 字面量**保留最后一条** ⇒ **931 的正文永远取不到**，
整表 dump 进读数文件时 dump 的也是求值后的 dict ⇒ **那条正文从来没进过任何产物。**

⇒⇒⇒ 而被吃掉的那条的横幅原话是「**原文保留在这里当历史记录、不许删**」
⇒⇒⇒ **意图是保留、机制是同名覆盖，而机制静默赢了。**

**本探针纯离线：只读仓里两个文件 + `git show HEAD:`，不开浏览器、不联网。**
"""
import ast
import collections
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = "scripts/jimeng_unclickable_audit.py"
GOLDEN = ROOT / "docs/research/jimeng-canvas/baseline-host-misuse-1016.json"

# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **before 必须钉在固定 sha 上，不许读 HEAD**
#   第一版写的是 `git show HEAD:…` ⇒ ⇒ **那是一次性的**：本批的处置一旦提交，
#   HEAD 里就没有那个重复键了 ⇒ ⇒ ⇒ P3 会**永远变成 False**，探针从此一直 rc=1。
#   ⇒⇒⇒ **这就是 1015 那条「判据里不许出现会因判据自身变化而改变的数」在时间轴上的形态** ——
#   不是「重算一遍变一变」，是**处置本身把证据擦掉了**。
# ⇒ 处置：钉一个常量 sha，并要求它**必须是 HEAD 的祖先**，否则报错而不是读别的东西。
BEFORE_SHA = "2b52f492"          # 1016 处置落地之前的那个提交

BATCH_RE = re.compile(r"(?:^|_)9\d\d(?:_|$)")


# ── 取 `SOURCE_BASELINE` 的字面量（不 import 审计模块：它顶层就跑东西） ──────────
def _dict_node(text):
    t = ast.parse(text)
    for n in ast.walk(t):
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Dict):
            for tt in n.targets:
                if isinstance(tt, ast.Name) and tt.id == "SOURCE_BASELINE":
                    return n.value
    return None


def _val(node):
    if isinstance(node, ast.Constant):
        return node.value
    return None


def survey(text):
    """把 SOURCE_BASELINE 摊平成 {层: [(键名, 行号, 字面量类型)]}。"""
    root = _dict_node(text)
    out = {}
    dup = []
    for k, v in zip(root.keys, root.values):
        layer = k.value
        entries = []
        if isinstance(v, ast.Dict):
            for kk, vv in zip(v.keys, v.values):
                name = kk.value
                entries.append({"key": name, "line": kk.lineno, "kind": _type_name(vv)})
        else:
            entries.append({"key": None, "line": v.lineno, "kind": _type_name(v)})
        c = collections.Counter(e["key"] for e in entries if e["key"])
        for name, times in c.items():
            if times > 1:
                lines = [e["line"] for e in entries if e["key"] == name]
                dup.append({"layer": layer, "key": name, "times": times, "lines": lines})
        out[layer] = entries
    return out, dup


def _type_name(node):
    if isinstance(node, ast.Constant):
        return type(node.value).__name__
    return type(node).__name__


def _git_show(rev):
    r = subprocess.run(["git", "show", "%s:%s" % (rev, AUDIT)],
                       cwd=ROOT, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def _is_ancestor(sha):
    r = subprocess.run(["git", "merge-base", "--is-ancestor", sha, "HEAD"],
                       cwd=ROOT, capture_output=True, text=True)
    return r.returncode == 0


# ── 普查 ───────────────────────────────────────────────────────────────────────
CUR_TEXT = (ROOT / AUDIT).read_text(encoding="utf-8")
CUR, DUP_CUR = survey(CUR_TEXT)
BEFORE_PINNED_OK = _is_ancestor(BEFORE_SHA)
HEAD_TEXT = _git_show(BEFORE_SHA) if BEFORE_PINNED_OK else None
HEAD, DUP_HEAD = survey(HEAD_TEXT) if HEAD_TEXT else ({}, [])

LAYERS = sorted(CUR)
N_LAYERS = len(LAYERS)
PER_LAYER = {lay: len(CUR[lay]) for lay in LAYERS}
MEDIAN_KEYS = sorted(PER_LAYER.values())[len(PER_LAYER) // 2]
MAX_LAYER, MAX_KEYS = max(PER_LAYER.items(), key=lambda kv: kv[1])

# 那批错挂的 9xx 结论键
MISP = []
for lay in LAYERS:
    for e in CUR[lay]:
        if e["key"] and BATCH_RE.search(e["key"]):
            MISP.append({"layer": lay, "key": e["key"], "line": e["line"]})
N_MISP = len(MISP)
MISP_LAYERS = sorted({m["layer"] for m in MISP})

# ⭐ before：HEAD 那版里被判成「不可达」的那条
DEAD_KEY = "source_reverse_lap_cycle_is_constant_931"
DEAD_LINES_HEAD = sorted(e["line"] for lay in HEAD
                         for e in HEAD.get(lay, [])
                         if e["key"] == DEAD_KEY)
HEAD_LAYER = "audio-voice-filter-listbox"
# HEAD 那版里，这一层的字面量写了 104 条键，但有两条同名 ⇒ 实际只有 103 条可达
HEAD_WRITTEN = len(HEAD.get(HEAD_LAYER, []))
HEAD_REACHABLE = HEAD_WRITTEN - sum(d["times"] - 1 for d in DUP_HEAD if d["layer"] == HEAD_LAYER)

# ── 反向用例：同名键到底是不是静默后覆盖前 ─────────────────────────────────────
REVERSE_DUP = {"keep_me": "第一次写的", "keep_me": "第二次写的"}
REVERSE_LAST_WINS = REVERSE_DUP["keep_me"] == "第二次写的"
REVERSE_SILENT = True  # 语言层面没有任何警告/异常：这一条由下面的「构造不抛错」来钉
_reverse_construction_ok = True
try:
    {"a": 1, "a": 2}
except Exception:                                       # pragma: no cover
    _reverse_construction_ok = False

# ── P 判定 ───────────────────────────────────────────────────────────────────
P1 = (N_LAYERS == 17 and MAX_KEYS > MEDIAN_KEYS * 4)
P2 = (len(DUP_CUR) == 0)                                # 处置：现在没有重复键了
P3 = (BEFORE_PINNED_OK and len(DUP_HEAD) == 1
      and DUP_HEAD[0]["key"] == DEAD_KEY
      and DUP_HEAD[0]["layer"] == HEAD_LAYER
      and len(DEAD_LINES_HEAD) == 2)                    # before 必须真的有两行同名
P4 = (HEAD_REACHABLE == HEAD_WRITTEN - 1)               # 少可达的那一条，正是被吃掉的那条
P5 = bool(REVERSE_LAST_WINS and REVERSE_SILENT and _reverse_construction_ok)
# ⭐ 第一版这里写的是「错挂的 9xx 键 = 40、且全部挂在音色筛选层」
#   —— **那是照抄 939 那条散文的预期，不是实测**，探针当场报假：
#   实测 **43 条 / 3 个宿主**：40 条在音色筛选层，另外 3 条已经各自落在语义正确的宿主上
#   （939 的 `src_context_menu_unreachable_by_tab_939` → `canvas-context-menu`；
#   940/941 → `topbar-history-menu`）⇒ ⇒ **939 那条处置确实生效了，只是没人记过这件事。**
MISP_BY_LAYER = collections.Counter(m["layer"] for m in MISP)
N_MISP_DEBT = MISP_BY_LAYER.get(HEAD_LAYER, 0)
N_MISP_ELSEWHERE = N_MISP - N_MISP_DEBT

P6 = (N_MISP == 43 and N_MISP_DEBT == 40 and N_MISP_ELSEWHERE == 3
      and MISP_BY_LAYER.get("canvas-context-menu", 0) >= 1)
P7 = DEAD_KEY in {e["key"] for lay in CUR for e in CUR[lay]}   # 处置后 931 正文可达
P8 = True

OUT = {"P1_host_is_a_drawer_1016": P1,
       "P2_no_duplicate_keys_now_1016": P2,
       "P3_duplicate_existed_at_head_1016": P3,
       "P4_one_key_was_unreachable_at_head_1016": P4,
       "P5_same_name_last_wins_is_silent_1016": P5,
       "P6_misplaced_9xx_keys_measured_1016": P6,
       "P7_original_is_reachable_now_1016": P7,
       "P8_hold_1016": P8}

GOLDEN_OBJ = {
    "generated_by": "jimeng_probe1016_baseline_host_misuse.py",
    "note": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **`SOURCE_BASELINE` 是「层表」，"
            "却被当成通用抽屉用** —— 900–939 的结论键全挂在音色筛选下拉那一条下面，"
            "而其中一条**键名被写了两次**，后一条把 931 的正文整个吃掉了。",
    "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **顶层键 = 层 testid，不是通用命名空间** —— "
            "凡不是「这一层的实测读数」的东西挂进去，按层取就取不到、"
            "而它又污染那一个条目的语义",
    "rule2": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **Python dict 字面量里的同名键是静默后覆盖前** —— "
             "不抛错、不告警、没有任何一行代码会告诉你有一条被吃了；"
             "而「保留原文」的惯用写法（同一条记录里再补一段收窄说明）"
             "**恰好就是同名写入** ⇒ 意图与机制直接打架，机制静默赢了",
    "before_sha": BEFORE_SHA,
    "before_sha_is_ancestor_of_head": BEFORE_PINNED_OK,
    "before_rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **before 钉在固定 sha 上、"
                   "不许读 HEAD** —— 第一版读的是 `git show HEAD:…`，"
                   "而本批的处置一旦提交、HEAD 里就没有那个重复键了 ⇒ "
                   "**处置本身会把证据擦掉、P3 会永远变成 False** ⇒ "
                   "⇒ 「会因判据自身变化而改变的数」在时间轴上的形态："
                   "不是「重算变一变」，是**证据被处置抹掉** ⇒ 钉 sha + 要求它是 HEAD 的祖先",
    "n_layers": N_LAYERS,
    "per_layer_key_counts": PER_LAYER,
    "median_keys_per_layer": MEDIAN_KEYS,
    "max_layer": MAX_LAYER,
    "max_layer_keys": MAX_KEYS,
    "misplaced_9xx_keys": MISP,
    "n_misplaced_9xx_keys": N_MISP,
    "n_misplaced_9xx_keys_in_voice_filter": N_MISP_DEBT,
    "n_misplaced_9xx_keys_elsewhere": N_MISP_ELSEWHERE,
    "misplaced_by_layer": dict(MISP_BY_LAYER),
    "misplaced_layers": MISP_LAYERS,
    "misplaced_policy": "⚠️ **本批只记账、不搬**：实测按层取的唯一消费点是 "
                        "`SOURCE_BASELINE.get(tid)`，而那 40 条从未被按层读过 ⇒ "
                        "错位是**语义污染**而非读数错误 ⇒ 搬它属于纯大改、零读数收益 ⇒ "
                        "按 1012 那条 P5 的处置路线，登记成账而不是现在动它",
    "duplicate_now": DUP_CUR,
    "duplicate_at_head": DUP_HEAD,
    "dead_key_at_head": {
        "key": DEAD_KEY,
        "layer": HEAD_LAYER,
        "lines": DEAD_LINES_HEAD,
        "written_at_head": HEAD_WRITTEN,
        "reachable_at_head": HEAD_REACHABLE,
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐ **字面量写了 104 条、实际只有 103 条可达** —— "
                "少的那一条不是被删了，是**被同名的后一条顶掉了**，"
                "而它自己的横幅写着「原文保留在这里当历史记录、不许删」",
        "fix": "**改名**（`source_reverse_lap_cycle_narrowed_by_932`）、一个字不删",
    },
    "reverse_case": {
        "dict_literal": "{'keep_me': '第一次写的', 'keep_me': '第二次写的'}",
        "value_read_back": REVERSE_DUP["keep_me"],
        "last_wins": REVERSE_LAST_WINS,
        "raised_nothing": _reverse_construction_ok,
        "rule": "⭐⭐⭐⭐⭐ **同名键的失败形态是「安静」**：不抛错、不告警、"
                "不改变任何一条已有的门 ⇒ 要抓它只能靠**对键名本身去重**",
    },
    "consumer": {
        "only_read_site": "`SOURCE_BASELINE.get(tid)`（`jimeng_unclickable_audit.py` 按层查）",
        "whole_table_dumped": True,
        "dump_site": "读数文件里的 `source_baseline` 字段（dump 的是求值后的 dict）",
        "rule": "⭐⭐⭐⭐⭐⭐ **所以被顶掉的那条不只是取不到、它也从来没进过任何产物** —— "
                "「写下来了」在这个结构里不等于「存在过」",
    },
}

GOLDEN.parent.mkdir(parents=True, exist_ok=True)
GOLDEN.write_text(json.dumps(GOLDEN_OBJ, ensure_ascii=False, indent=2) + "\n",
                  encoding="utf-8")

print("层数=%d（每层子键数 中位数=%d，最多=%s 的 %d）" % (N_LAYERS, MEDIAN_KEYS, MAX_LAYER, MAX_KEYS))
print("错挂的 9xx 结论键=%d 条（音色筛选层 %d + 其它 %d，宿主 %s）"
      % (N_MISP, N_MISP_DEBT, N_MISP_ELSEWHERE, dict(MISP_BY_LAYER)))
print("重复键 now=%d / at HEAD=%d" % (len(DUP_CUR), len(DUP_HEAD)))
for d in DUP_HEAD:
    print("  HEAD 重复：%s.%s ×%d 行 %s" % (d["layer"], d["key"], d["times"], d["lines"]))
print("before sha=%s（是 HEAD 祖先=%s）；那层：写了 %d 条、实际可达 %d 条（差 %d）"
      % (BEFORE_SHA, BEFORE_PINNED_OK, HEAD_WRITTEN, HEAD_REACHABLE, HEAD_WRITTEN - HEAD_REACHABLE))
print("931 正文现在可达=%s" % P7)
print("反向用例：同名键 last_wins=%s、不抛错=%s" % (REVERSE_LAST_WINS, _reverse_construction_ok))
P_ORDER = ["host_is_a_drawer_1016",
           "no_duplicate_keys_now_1016",
           "duplicate_existed_at_head_1016",
           "one_key_was_unreachable_at_head_1016",
           "same_name_last_wins_is_silent_1016",
           "misplaced_9xx_keys_measured_1016",
           "original_is_reachable_now_1016",
           "hold_1016"]
print("P1..P8 =", [OUT["P%d_%s" % (i + 1, n)] for i, n in enumerate(P_ORDER)])
print("PROBE_1016_DONE ->", GOLDEN)
sys.exit(0 if all(OUT.values()) else 1)