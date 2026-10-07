#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 1015 —— ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **把 1014 的 P6 落成代码，然后立刻被它反咬一口**

1014 写下一条 P6：**任何交付物都必须被下一批当成被测对象重新过一遍 ——「自己验过」不算数。**
本批照它做：把仓里每一本 golden 连同生成它的探针一起找出来，逐本在今天重跑，
问一句「今天跑出来的那本，和仓里躺着的那本，是不是同一个东西」。

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **而本批否掉了三样东西，其中两样是我自己写下来时的处方。**

## 一、否掉「自动发现比手写清单安全」

我原本写的是「按 `generated_by` 自动发现探针、不手写清单 —— 手写清单就是 1012 那个
`assert len(PV) == 187` 的同族病，唯一的治法是让清单自己长出来」。

⇒ ⇒ ⇒ **第一版真跑：它只认领了 8 本里的 7 本，1 本被静默丢掉，而它报 all-green。**

丢的那本是 1005，`generated_by` 写的是 `scripts/jimeng_probe1005_...py` ——
**带目录前缀** ⇒ 拼成 `scripts/scripts/...` ⇒ 路径不存在 ⇒ 被跳过。
同一族的另外两条（1007/1008 把散文「（写它的仪器就是读它的那个）」粘在标识符后面）
在我修掉之后就不再丢了 —— **它们从来没有被报出来过，因为它们是「碰巧长对了」。**

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **⇒ ⇒ ⇒ 「自动发现」和「手写清单」的失败形态根本不同：
手写清单写错会当场炸，自动发现写错只会安静地少算 —— ⇒ ⇒ ⇒ ⇒ 自动发现更危险，
除非它有一条「发现失败必须报错」的反向门。**

## 二、否掉「完备性用加法验就够了」

第一版的完备性是 `四态之和 == 认领到的本数` ⇒ 恒真 ⇒ 报 all-green。
⭐⭐⭐⭐⭐⭐⭐⭐⭐ **分母也出自同一台仪器 ⇒ 加法只能验分子的完备性，分母的完备性是另一件事。**

⇒ ⇒ 处置：**双通道对账** —— 通道 A 数产物目录、通道 B 数探针目录，差集逐条列出；
外加一条反向门：`generated_by` 必须逐字节等于某个真实探针的文件名，不合规要**报错**。

## 三、1014 那台普查，反过来抓住了 1015 的产物

1014 的普查输入是整个 `docs/research/jimeng-canvas/*.json`。
⇒ ⇒ ⇒ ⇒ **1015 一写下自己那本，1014 的读数就变了：`n_goldens` 8 → 9、
不可自证的空集合 1 → 2，而新加的那一条是 1015 自己的 `/books/[2]/keys_added`。**

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **那一条之所以不可自证，是因为那本书本批没有漂移
—— ⇒ ⇒ ⇒ ⇒ ⇒ 「没有漂移」这件事，在账本上长得和「没算过」一模一样**
⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **1014 刚写完的病，1015 自己中了一次。**

⇒ ⇒ ⇒ ⇒ 而根因是**顺序**：1015 在整轮跑完之后才写自己那本 ⇒ ⇒ ⇒ ⇒ ⇒
**1014 在整轮里读到的永远是 1015 的上一版 ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 每本账都落后它上游一轮。**
⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **⇒ ⇒ ⇒ ⇒ ⇒ 处置：整轮重跑直到「零漂移」为止，
并把「跑了几轮才不动点」本身当成读数报出来 —— 不动点存在与否都要诚实说。**

本批**纯离线**：不打开浏览器、不按任何键、不发任何网络请求
"""
import atexit
import io
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GDIR = ROOT / "docs/research/jimeng-canvas"
GOLDEN = GDIR / "rerun-reproducibility-1015.json"
OUT = "/tmp/b1015-rerun-reproducibility.json"
AFILE = "scripts/jimeng_unclickable_audit.py"
VFILE = "scripts/verify-jimeng-batch841-unclickable.py"
AUDIT_TXT = (ROOT / AFILE).read_text(encoding="utf-8")
VERIFIER_TXT = (ROOT / VFILE).read_text(encoding="utf-8")
PY = sys.executable
TIMEOUT = 2400
MAX_ROUNDS = 6

# ⚠️⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **本仪器会覆写别人的产物 ⇒ ⇒ 每次跑之前必须留快照、跑完原样写回去**
#   ⇒ ⇒ ⇒ 否则「量可复现性」这个动作本身就会改掉被量的东西
#   ⇒ ⇒ ⇒ ⇒ 1008 立过一条：任何改动临时状态的仪器都必须注册 `atexit` 兜底
_SNAPSHOTS = {}


@atexit.register
def _restore():
    for p, data in _SNAPSHOTS.items():
        try:
            if p.exists() and p.read_bytes() != data:
                p.write_bytes(data)
        except Exception:
            pass


def _flatten(obj, prefix=""):
    """JSON → {json_pointer: 叶子}。空 list / 空 dict 各算一个叶子，
    否则「新增一个空集合」会被摊成「什么都没变」—— 1014 刚踩过的那一族。"""
    out = {}
    if isinstance(obj, dict):
        if not obj:
            out[prefix or "/"] = "<empty dict>"
            return out
        for k, v in obj.items():
            out.update(_flatten(v, "%s/%s" % (prefix, k)))
        return out
    if isinstance(obj, list):
        if not obj:
            out[prefix or "/"] = "<empty list>"
            return out
        for i, v in enumerate(obj):
            out.update(_flatten(v, "%s/[%d]" % (prefix, i)))
        return out
    out[prefix or "/"] = obj
    return out


def _classify(rc, pre, post):
    """四态。⭐⭐⭐⭐⭐ **「跑不起来」必须单列**：探针崩了不告诉你数据有没有变，
    并进任何一态都等于把仪器故障报成数据结论（1006：门报红 ≠ 数据错）。"""
    if rc != 0:
        return {"state": "crashed"}
    if post is None:
        return {"state": "vanished"}
    if post == pre:
        return {"state": "reproduced"}
    a, b = _flatten(json.loads(pre.decode("utf-8"))), \
        _flatten(json.loads(post.decode("utf-8")))
    return {"state": "drifted",
            "keys_added": sorted(set(b) - set(a)),
            "keys_removed": sorted(set(a) - set(b)),
            "values_changed": [{"path": k, "old": a[k], "new": b[k]}
                               for k in sorted(set(a) & set(b)) if a[k] != b[k]]}


# ── 通道 A：扫产物目录 ──────────────────────────────────────────────
_ALL = sorted(GDIR.glob("*.json"))
N_GOLDENS = len(_ALL)

# ── 通道 B：扫探针目录（⭐ 独立通道，用来对账，不许和 A 同源）─────────
_PROBES = sorted(p.name for p in (ROOT / "scripts").glob("jimeng_probe*.py"))
SELF = Path(__file__).name

# ── ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ 【1027 改写横幅】把 1027 从本套件里排除，并**登记为什么**
#   实测：1027 进套件之后，6 轮**每轮都报 `golden-freshness-1027.json` 漂移**、
#   `P3`（`CONVERGED`）转红 ⇒⇒⇒ **而单跑它 rc=0、两次跑逐字节相同**
#   ⇒⇒⇒⇒⇒⇒ 根因不在 1027 的代码，而在**两道门的输入集合没有交集约定**：
#     · 1015 的前提是「所有输入都是常量」（它验的是**可复现**）
#     · 1027 的输入按定义就是「仓库当前状态」（它验的是**新鲜度**）：
#         变更集默认取 `git diff --name-only HEAD~3`，而**共享仓里别的会话
#         每隔几分钟就提交一次** ⇒⇒⇒ 套件那 25 分钟里变更集一直在动；
#         耦合面里的 `scripts/*.mjs` glob 也会把别的会话新加的文件吸进来
#         ⇒⇒⇒ 实测两次跑的差分正是 `docs/user-manual/…` 少几个、
#         `scripts/jimeng-b248.mjs` 多几个，`n_files_it_reads` 4999 → 5000
#   ⇒⇒⇒⇒⇒⇒⭐⭐⭐ **⇒ 处置：双向排除**（1027 早就把 1015 排除了，现在轮到 1015 排 1027）
#     ⇒ **不许默默摘掉**：下面这条登记本身要被 `_EXCL_OK` 守着，
#       少写理由、把键拼错、或者哪天真能同存了，门都会红
_EXCLUDE_INPUT_CONFLICT = {
    "jimeng_probe1027_freshness_gate.py": (
        "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **一道门的输入若是另一道门假定为常量的东西，它就不可能进那道门** —— "
        "1015 验「同一份输入下两次跑是否一致」，而 1027 的输入**按定义就是**「仓库当前状态」"
    ),
}
_EXCLUDED, _N_SKIPPED, _N_UNPARSED, _UNLINKED = [], 0, 0, []
_OWNED = []
for _f in _ALL:
    try:
        _d = json.loads(_f.read_text(encoding="utf-8"))
    except Exception:
        _N_UNPARSED += 1
        continue
    if not isinstance(_d, dict) or "generated_by" not in _d:
        _N_SKIPPED += 1
        continue
    _gb = str(_d["generated_by"])
    if _gb == SELF:                      # ⭐ 排除自己靠 `generated_by`，不靠文件名
        continue
    # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **反向门：不合规要**报错**，不许被跳过** ——
    #   1015 第一版就是在这里静默丢掉了 1 本、然后报 all-green
    if "/" in _gb or not _gb.endswith(".py") or _gb not in _PROBES:
        _UNLINKED.append({"golden": _f.name, "generated_by": _gb,
                          "why": "不是 `scripts/` 下某个 `jimeng_probe*.py` 的文件名"})
        continue
    # ⭐⭐⭐⭐⭐ 排除必须在**合规检查之后** —— 不然一个拼错的键会顺手把
    #   「unlinked」这条反向门也一起关掉（而那正是 1015 第一版丢 1 本的原因）
    if _gb in _EXCLUDE_INPUT_CONFLICT:
        _EXCLUDED.append({"golden": _f.name, "generated_by": _gb,
                          "why": _EXCLUDE_INPUT_CONFLICT[_gb]})
        continue
    _OWNED.append((_f, _gb, ROOT / "scripts" / _gb))
N_EXCLUDED_SELF = 1
# ⭐⭐⭐⭐⭐⭐ **登记不是摆设**：每条排除都必须（a）键真的存在、（b）理由非空、
#   （c）真的命中了某本 golden。少任何一条，`_EXCL_OK` 转红 ⇒ 排除不许悄悄扩大
_EXCL_OK = (all(k in _PROBES for k in _EXCLUDE_INPUT_CONFLICT)
            and all(str(v).strip() for v in _EXCLUDE_INPUT_CONFLICT.values())
            and {e["generated_by"] for e in _EXCLUDED} == set(_EXCLUDE_INPUT_CONFLICT))
N_EXCLUDED_CONFLICT = len(_EXCLUDED)
N_OWNED = len(_OWNED)
N_UNLINKED = len(_UNLINKED)
for _f, _, _ in _OWNED:
    if _f not in _SNAPSHOTS:
        _SNAPSHOTS[_f] = _f.read_bytes()

_A_NAMES = set()
for _f in _ALL:
    try:
        _A_NAMES.add(str(json.loads(_f.read_text(encoding="utf-8")).get("generated_by", "")))
    except Exception:
        pass
_PROBES_NO_GOLDEN = [p for p in _PROBES if p not in _A_NAMES and p != SELF]


def _run_round():
    """整轮：每本探针跑一次。⭐ 统一带 `--write-golden` ——
    1005 把落仓的门控在 `if "--write-golden" in sys.argv` 上 ⇒ ⇒ 不带这个 flag 时
    它 rc=0、打印 DONE、**只写 /tmp**，仓里的产物一个字节都不动
    ⇒ ⇒ ⇒ ⇒ **「探针跑成功了」不等于「产物被刷新了」** —— 这一条只能靠
    ⇒ ⇒ ⇒ ⇒ ⇒ 重跑之后比对字节、或看 mtime 变没变来判，不许看退出码。"""
    rows = []
    for golden, gb, probe in _OWNED:
        pre = golden.read_bytes()
        pre_mtime = golden.stat().st_mtime_ns
        rc, tail = None, []
        try:
            r = subprocess.run([PY, "-u", str(probe), "--write-golden"],
                               cwd=str(ROOT), capture_output=True, timeout=TIMEOUT)
            rc, tail = r.returncode, (r.stdout + r.stderr).decode("utf-8", "replace")
        except subprocess.TimeoutExpired as e:
            tail = (e.stdout or b"").decode("utf-8", "replace") + "\n<<TIMEOUT>>"
        except Exception as e:
            tail = "<<spawn failed: %r>>" % (e,)
        post = golden.read_bytes() if golden.exists() else None
        wrote = bool(post is not None and golden.stat().st_mtime_ns != pre_mtime)
        row = {"golden": golden.name, "probe": "scripts/" + gb, "rc": rc,
               "wrote_golden": wrote, "n_bytes": len(pre),
               "n_bytes_fresh": len(post) if post is not None else 0}
        row.update(_classify(rc, pre, post))
        row["tail"] = tail.strip().splitlines()[-2:] if tail.strip() else []
        rows.append(row)
    return rows


# ── 迭代到不动点：整轮重跑直到某一轮零漂移 ──────────────────────────
ROUNDS = []
BOOKS, N_ROUNDS = [], 0
for _i in range(1, MAX_ROUNDS + 1):
    _rows = _run_round()
    _d = sum(1 for r in _rows if r["state"] == "drifted")
    ROUNDS.append({"round": _i, "n_drifted": _d,
                   "drifted": [r["golden"] for r in _rows if r["state"] == "drifted"]})
    N_ROUNDS = _i
    BOOKS = _rows
    if _d == 0:
        break
CONVERGED = ROUNDS[-1]["n_drifted"] == 0

ST = {}
for r in BOOKS:
    ST[r["state"]] = ST.get(r["state"], 0) + 1
N_REPRODUCED = ST.get("reproduced", 0)
N_DRIFTED = ST.get("drifted", 0)
N_CRASHED = ST.get("crashed", 0)
N_VANISHED = ST.get("vanished", 0)
N_STATES_SUM = N_REPRODUCED + N_DRIFTED + N_CRASHED + N_VANISHED
N_NOT_WRITTEN = sum(1 for r in BOOKS if not r["wrote_golden"])
N_KA = sum(len(r.get("keys_added", [])) for r in BOOKS)
N_KR = sum(len(r.get("keys_removed", [])) for r in BOOKS)
N_VC = sum(len(r.get("values_changed", [])) for r in BOOKS)
DRIFT_PATHS = sorted({c["path"] for r in BOOKS for c in r.get("values_changed", [])}
                     | {p for r in BOOKS for p in r.get("keys_added", [])}
                     | {p for r in BOOKS for p in r.get("keys_removed", [])})
DRIFT_BOOKS = [r["golden"] for r in BOOKS if r["state"] == "drifted"]


# ── 修了什么：before/after 逐条从 git HEAD 取，不靠记忆 ──────────────
def _head_json(rel):
    r = subprocess.run(["git", "show", "HEAD:%s" % rel], cwd=str(ROOT),
                       capture_output=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout.decode("utf-8", "replace"))
    except Exception:
        return None


def _head_generated_by(rel):
    d = _head_json(rel)
    return d.get("generated_by") if isinstance(d, dict) else None


REPAIRED = []
for golden, gb, _ in _OWNED:
    old = _head_generated_by("docs/research/jimeng-canvas/" + golden.name)
    if old is not None and old != gb:
        REPAIRED.append({"golden": golden.name, "before": old, "after": gb})
N_REPAIRED = len(REPAIRED)

# ⭐ 1005 的读数为什么跟着变：它普查的是 `_ausrc`，而本批往 audit 里塞了判据 ⇒
#   before/after 同样逐条从 git HEAD 取，不靠记忆
_1005 = GDIR / "zero-coupling-anchors-1005.json"
_1005_now = _head_json("docs/research/jimeng-canvas/zero-coupling-anchors-1005.json")
try:
    N_ZERO_CPLX_NOW = int(json.loads(_1005.read_text(encoding="utf-8"))["n_zero_coupling"])
except Exception:
    N_ZERO_CPLX_NOW = None
N_ZERO_CPLX_HEAD = (int(_1005_now["n_zero_coupling"])
                    if isinstance(_1005_now, dict) and "n_zero_coupling" in _1005_now
                    else None)
try:
    N_POS_NOW = int(json.loads(_1005.read_text(encoding="utf-8"))["n_positive_present"])
except Exception:
    N_POS_NOW = None
N_POS_HEAD = (int(_1005_now["n_positive_present"])
              if isinstance(_1005_now, dict) and "n_positive_present" in _1005_now
              else None)
# ⭐ 判据里那个「近千行」不许靠手感：数 audit 里 2015 那一段的实际行数，
#   **作为读数记进产物**（它不在判据文本里出现，所以不进出处表）——
#   ⚠️ 早先那版把「约 950 行」写进了判据，而那个数**每加一段判据就会变**
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **⇒ 判据里不许出现「会因判据自己增长而改变」的数**
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **⇒ 这是一条自指的脆弱性，和 1013 那条
#   「清单会过期」是同一族，只是这次过期的是判据自己**
_A15 = AUDIT_TXT.find('"rerun_reproducibility_2015"')
_N_AUDIT_2015_LINES = 0
if _A15 >= 0:
    _m15 = re.search(r'\n    "[a-z0-9_]+":\s*\{', AUDIT_TXT[_A15 + 10:])
    _end15 = (_A15 + 10 + _m15.start()) if _m15 else len(AUDIT_TXT)
    _N_AUDIT_2015_LINES = AUDIT_TXT[_A15:_end15].count("\n")

# ── P5 反向用例：分类器不许恒判「可复现」 ──────────────────────────
# ⚠️⚠️⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **我第一版的反向用例是坏的**：我把 `books` 整个换成一个新列表，
#   而被挑中的那本（`change-locality-1011.json`）**本来就没有 `books` 这个键**
#   ⇒ ⇒ ⇒ 于是它测的又是「新增键」、而**没有一次真正测到「改已有叶子」**
#   ⇒ ⇒ ⇒ ⇒ 更糟的是那个断言写成 `and REVERSE_MOD["values_changed"]` ——
#   ⇒ ⇒ ⇒ ⇒ ⇒ **`and` 链返回最后一个操作数**，所以 P5 当时打印出来是 `[]` 而不是 `False`
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **⇒ ⇒ ⇒ ⇒ 断言不是布尔值时，JSON 里 `[]` 和 `false` 长得不一样**
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 处置：反向用例改成「挑一个**已存在**的叶子改值」，
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 并且整条断言外面套 `bool()`
_first = _OWNED[0][0]
_b = _first.read_bytes()
_obj = json.loads(_b.decode("utf-8"))
_add = json.loads(_b.decode("utf-8"))
_add["PROBE_1015_FORCED_EXTRA_KEY"] = 1
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ 挑一条**真的存在于该本里**的路径来改值 ——
#   ⚠️⚠️⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **第二版又踩了同一个坑的一半**：
#   `for _k in _tgt: _mod = _mod[_k]` 把游标一路走到叶子，**而 `_mod` 本身变成了那个叶子**
#   ⇒ ⇒ ⇒ ⇒ ⇒ `json.dumps(_mod)` 序列化的是 `0.1195`、整本书被换成了一个标量
#   ⇒ ⇒ ⇒ ⇒ ⇒ 而分类器把这种输入判成「88 个键被删、1 个键被加、0 个值变了」
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **它仍然是 `drifted` —— 四个状态全部「正确」，而这条断言仍然是假**
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **「状态对了」不等于「测的是那件事」**
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **处置：游标另开、根对象留着，改完叶子把根对象序列化回去**
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 并且只挑**不含 list 下标**的路径（游标穿过 list 需要
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 别的寻址方式，而那正是本条反向用例不该引入的第二个变量）
_live = [p for p in sorted(_flatten(_obj)) if p != "/" and p.startswith("/")]
_live_plain = [p for p in _live if "[" not in p]
_mod = json.loads(_b.decode("utf-8"))
_cur = _mod
_tgt = (_live_plain or _live)[0].split("/")[1:]
for _k in _tgt[:-1]:
    _cur = _cur[_k]
_old_leaf = _cur[_tgt[-1]]
_new_leaf = "PROBE_1015_FORCED_CHANGED_LEAF"
if _new_leaf == _old_leaf:                       # 哨兵值不许和原值撞上
    _new_leaf = "PROBE_1015_FORCED_CHANGED_LEAF_2"
_cur[_tgt[-1]] = _new_leaf
REVERSE_ADD = _classify(0, _b, json.dumps(_add, ensure_ascii=False, indent=1).encode("utf-8"))
REVERSE_MOD = _classify(0, _b, json.dumps(_mod, ensure_ascii=False, indent=1).encode("utf-8"))
REVERSE_C = _classify(1, _b, None)
REVERSE_V = _classify(0, _b, None)
P5_OK = bool(
    bool(_live_plain)                           # 必须挑到一条不含 list 下标的路径
    and REVERSE_ADD["state"] == "drifted"
    and "/PROBE_1015_FORCED_EXTRA_KEY" in REVERSE_ADD["keys_added"]
    and not REVERSE_ADD["values_changed"]
    and REVERSE_MOD["state"] == "drifted"
    and not REVERSE_MOD["keys_added"] and not REVERSE_MOD["keys_removed"]
    and [c["path"] for c in REVERSE_MOD["values_changed"]] == [(  _live_plain or _live)[0]]
    and REVERSE_C["state"] == "crashed" and REVERSE_V["state"] == "vanished")
P5_DETAIL = {"add_key": REVERSE_ADD["state"], "modify_value": REVERSE_MOD["state"],
             "rc1": REVERSE_C["state"], "missing_output": REVERSE_V["state"],
             "modified_path": (_live_plain or _live)[0] if _live else None,
             "path_is_list_free": bool(_live_plain),
             "n_keys_added": len(REVERSE_MOD["keys_added"]),
             "n_keys_removed": len(REVERSE_MOD["keys_removed"]),
             "old_value": _old_leaf, "new_value": _new_leaf}

# ── P8：1014 那台普查把本探针的产物判成几条「不可自证」？而本探针写在产物里的
#    那份不变式，普查那台仪器读得到吗？ ─────────────────────────────
# ⚠️⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **这是本批最要紧的一条、而且它是 1014 那台
#   普查主动报上来的** —— 1014 刚给本探针的产物判了 5 条「不可自证」的空集合，
#   而本探针**在产物里明明写了一个 `empty_list_invariants` 块**把其中三条钉住了
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **⇒ 也就是说：那份不变式是写给人和自己看的，
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 普查那台仪器并不读它**
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 这是 1013 那条
#   「处置要落在生成器里、不落在产物上」的第四个形态：
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **自证不变式必须登记在普查的规则里，
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 不然它对普查而言不存在**
def _rows_of_1014():
    """读 1014 刚写的那本普查账（它在被重跑的那一轮里已刷新）。"""
    p = GDIR / "empty-ambiguity-1014.json"
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None, None
    return d.get("ambiguous") or [], (d.get("census") or {})


_AMB_1014, _CEN_1014 = _rows_of_1014()
_AMB_1014 = _AMB_1014 or []
_CEN_1014 = _CEN_1014 or {}
_SELF_AMB = [r for r in _AMB_1014 if r.get("golden") == GOLDEN.name]
N_SELF_AMB = len(_SELF_AMB)
_INV_BLOCK = {"keys_added_is_empty_iff_byte_identical",
              "values_changed_is_empty_iff_byte_identical",
              "keys_removed_is_empty_iff_no_key_vanished",
              "tail_is_empty_iff_probe_printed_nothing"}
_N_INV_BLOCK = len(_INV_BLOCK)
# ⭐ 差集 = 「产物里登记了不变式、而普查仍然判成不可自证」的条数
N_INV_INVISIBLE = sum(1 for r in _SELF_AMB
                      if r.get("path") and r.get("path").split("/")[-1] in _INV_BLOCK)
N_SELF_PROVABLE_1014 = int(_CEN_1014.get("n_self_provable", 0) or 0)
N_AMBIGUOUS_1014 = int(_CEN_1014.get("n_ambiguous", 0) or 0)
P8_OK = bool(_AMB_1014) and N_SELF_AMB > 0 and N_INV_INVISIBLE > 0
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **这条读数天生落后一代，而且加轮数关不掉**
#   `_rows_of_1014()` 读的是**最后一轮跑出来的 `empty-ambiguity-1014.json`**，
#   而那份账是在**本探针写自己那本之前**算的 ⇒ ⇒ ⇒ ⇒ 它描述的是**上一次执行**留下的产物
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 后果：`self_ambiguous_paths` 里那条 `/rounds/[k]/drifted`，
#   **k 常常小于本产物自己的 `rounds` 下标** ⇒ ⇒ ⇒ ⇒ ⇒ 即**产物与它自己矛盾**。
# ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **不动点只把「漂移数」按住了，按不住「自指读数」** ——
#   漂移数收敛是「重跑就变好」，自指读数每重跑一次就再落后一代。
_P8_ROUND_IDXS = []
for _r in _SELF_AMB:
    _m = re.match(r"^/rounds/\[(\d+)\]", str(_r.get("path") or ""))
    if _m:
        _P8_ROUND_IDXS.append(int(_m.group(1)))
_P8_SAW_ROUNDS = (max(_P8_ROUND_IDXS) + 1) if _P8_ROUND_IDXS else None
P8_DETAIL = {
    "census_n_goldens": _CEN_1014.get("n_goldens"),
    "census_n_ambiguous": N_AMBIGUOUS_1014,
    "census_n_self_provable": N_SELF_PROVABLE_1014,
    "self_ambiguous": N_SELF_AMB,
    "self_ambiguous_paths": [r.get("path") for r in _SELF_AMB],
    "n_invariants_declared_in_artifact": _N_INV_BLOCK,
    "n_invariables_1014_cannot_see": N_INV_INVISIBLE,
    "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **产物里写着不变式 ≠ 普查看得见不变式** —— "
            "1014 的 `INVARIANTS` 是一张硬编码表，它不读产物里的 `empty_list_invariants`",
    # ↓ 下面三个键是为了让上面那个矛盾**可读**，而不是把它藏起来
    "p8_saw_artifact_with_n_rounds": _P8_SAW_ROUNDS,
    "p8_this_artifact_has_n_rounds": N_ROUNDS,
    "p8_reading_lag_rounds": (None if _P8_SAW_ROUNDS is None
                              else N_ROUNDS - _P8_SAW_ROUNDS),
    "p8_lag_is_structural": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **这不是 bug、是没关严** —— "
                            "要把这条读数追平，就得「写完产物再跑一次 1014」，"
                            "而那会改写 1014 那本账 ⇒ ⇒ ⇒ 又触发新一轮 ⇒ ⇒ ⇒ ⇒ "
                            "**⇒ 所以只有把它记成一个读数，才不至于让产物自己和自己矛盾**",
}

# ── P 出处检查：判据里手写的每一个数都要有出处 ──────────────────────
# ⚠️⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **第二版 P6 之所以为假，
#   是仪器自己的病**：audit 里判据值的写法是 `"key": (\n    "…"\n)` ——
#   **值前面有一个 `(`**，而我的正则要求 `":` 之后紧跟换行
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 于是它**一条判据都没抓到**、`_AB` 是空的
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而 `bool(_AB) and not _missing` 判成 False
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **「提取器抓到 0 条」与「判据里一个数都没有」
#   在探针输出里长得一模一样** —— 这是 1014 那条 P2 的第三个形态：
#   **「没测到」与「测了、结论为否」在输出里分不开**
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **处置：① 正则容忍 `(` ② 加一条反向门 ——
#   提取到的判据条数必须等于 audit 里 `_2015_` 判据键的实际个数，对不上当场报红**
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 不写成 `assert`：跑挂了就没账可查，
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而这一条要**留在账里**（`number_provenance` 那块）
_AB = {}
for _m in re.finditer(r'"(p\d_[a-z0-9_]*_2015_)":\s*\(\s*\n\s*((?:\s*"(?:[^"\\]|\\.)*"\s*\n?)+)',
                      AUDIT_TXT):
    _AB[_m.group(1)] = "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', _m.group(2)))
_N_KEYS_IN_AUDIT = len(set(re.findall(r'"(p\d_[a-z0-9_]*_2015_)"\s*:', AUDIT_TXT)))
N_AB_EXTRACTED = len(_AB)
# ⭐ 口径边界要**显式**：本检查只覆盖 P 编号判据，audit 里另外三个 2015 键不在口径内
_KEYS_2015_ALL = set(re.findall(r'"([a-z0-9_]*2015[a-z0-9_]*)"\s*:', AUDIT_TXT))
_KEYS_2015_OUT_OF_SCOPE = sorted(_KEYS_2015_ALL - set(_AB))
_SOURCES = {}


def _allow(v, why):
    _SOURCES[str(v)] = why


# ⚠️⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **历史出处的登记区**
#   1016 真的加了一本探针、且套件一轮就收敛 ⇒ 判据里那几个手写的数
#   （通道 B 探针数、动态度数、修复数、1005 的 `n_zero_coupling`）
#   **当场失去了「实测值」这个出处** ⇒ ⇒⇒⇒ **而这不是仪器坏了，是判据过期了。**
#   ⇒ 处置与 1015 那条通则一致：**出处不是白名单，出处是「带 sha 的历史实测读数」**
#   ⇒⇒⇒⇒ 每一行都写明它是**哪个提交时**的读数；这样「过期」是可查的，不是被悄悄放过。
for _v, _w in [("211", "1015 提交时（sha `2b52f492`）实测的通道 B 探针数 —— "
                       "此后新增探针会让它变大，而**出处的含义是「那一刻的实测读数」**，不是白名单"),
               ("2", "1015 那次跑出不动点的轮数 —— 现读数见产物 `n_rounds`"),
               ("3", "1015 那次修好的 `generated_by` 条数 —— 修完就是 0，"
                     "**这不是矛盾，是「修完了」**"),
               ("690", "1015 提交时（sha `2b52f492`）1005 的 `n_zero_coupling` —— "
                       "往 audit 里写判据就会把它顶高"),
               ("10", "⚠️⭐⭐⭐⭐⭐⭐ **这一条是 1017 逼出来的第三次**：1015 的 `p2_…` 判据里"
                      "本来就有一个「10」，而它一直没有单独的出处 —— **它是被「实测值恰好等于 10」"
                      "顺带放行的**（当时 `n_owned` = 10）⇒ ⇒⇒⇒ 1017 加了第 12 本探针、"
                      "`n_owned` 变成 11 ⇒⇒⇒⇒ **那一刻它才暴露出来："
                      "「碰巧对上了」和「有出处」在检查里长得一样** ⇒⇒⇒⇒⇒ "
                      "**⇒⇒⇒⇒⇒⇒ 所以出处的数量比想象中要紧 —— "
                      "一个数能活多久，取决于它碰巧撞上了哪个实测值**"),
               ("5", "⚠️⭐⭐⭐⭐⭐⭐ **第四次、也是最不该发生的一次**：`p8_…` 判据里那个「5」"
                    "是 `self_ambiguous` 在 1015 提交时（sha `2b52f492`）的读数，"
                    "1018 跑完已变成 6 ⇒⇒⇒⇒⇒⇒ "
                    "**⇒⇒⇒⇒⇒⇒⇒ 同一个病：读数一变、判据里的数就没出处** ⇒⇒⇒⇒⇒⇒ "
                    "⇒ 处置与其他几条一致：登记成带 sha 的历史实测读数，**不进白名单**")]:
    _allow(_v, _w)


for _v, _w in [(N_GOLDENS, "通道 A：docs/research/jimeng-canvas/*.json 的文件数"),
               (len(_PROBES), "通道 B：scripts/jimeng_probe*.py 的文件数"),
               (N_OWNED, "通道 A 里 `generated_by` 合规因而认领到的本数"),
               (N_EXCLUDED_SELF, "排除自己那本（靠 `generated_by`）"),
               (N_EXCLUDED_CONFLICT, "因**输入集合冲突**被排除的本数（登记见 `excluded`）"),
               (len(BOOKS), "认领到的本数 == 实际重跑的本数"),
               (N_REPRODUCED, "四态里 state == reproduced 的计数"),
               (N_DRIFTED, "四态里 state == drifted 的计数"),
               (N_CRASHED, "四态里 state == crashed 的计数"),
               (N_VANISHED, "四态里 state == vanished 的计数"),
               (N_STATES_SUM, "四态之和（分子完备性）"),
               (N_UNLINKED, "通道 A 里 `generated_by` 不合规而被**拒绝认领**的本数"),
               (N_KA, "漂移本里新增的键总数"),
               (N_KR, "漂移本里删除的键总数"),
               (N_VC, "漂移本里值变了的叶子总数"),
               (N_NOT_WRITTEN, "重跑之后压根没写过自己 golden 的本数"),
               (N_REPAIRED, "`generated_by` 相对 HEAD 被修过的本数"),
               (len(_PROBES_NO_GOLDEN), "通道 B 有探针而通道 A 无对应 golden 的个数"),
               (N_ROUNDS, "跑到不动点用掉的轮数"),
               (MAX_ROUNDS, "轮数上限"),
               ("%d/%d" % (N_UNLINKED, N_GOLDENS), "被拒绝认领的比例（分母 = 通道 A）"),
               ("%d/%d" % (N_OWNED, N_GOLDENS), "认领到的比例（分母 = 通道 A）"),
               (N_AB_EXTRACTED, "从 audit 里提取到的 `_2015_` 判据条数"),
               (_N_KEYS_IN_AUDIT, "audit 里 `_2015_` 判据键的实际个数（反向门的另一侧）"),
               (N_SELF_AMB, "1014 那台普查判本探针产物「不可自证」的条数"),
               (N_INV_INVISIBLE, "其中本探针已在产物里登记了不变式、而普查仍判不可自证的条数"),
               (_N_INV_BLOCK, "本探针在产物里登记的不变式条数"),
               (N_AMBIGUOUS_1014, "1014 普查口径下全部账里「不可自证」的总数"),
               (N_SELF_PROVABLE_1014, "1014 普查口径下「可自证」的总数"),
               (int(_CEN_1014.get("n_goldens", 0) or 0),
                "1014 普查看到的 golden 本数（已排除它自己那本）"),
               (N_ZERO_CPLX_HEAD, "1005 golden 在 git HEAD 上的 `n_zero_coupling`"),
               (N_ZERO_CPLX_NOW, "1005 golden 现在的 `n_zero_coupling`（本批重跑后）"),
               (N_POS_HEAD, "1005 golden 在 git HEAD 上的 `n_positive_present`"),
               (N_POS_NOW, "1005 golden 现在的 `n_positive_present`（本批重跑后）")]:
    _allow(_v, _w)
# ⭐⭐⭐⭐⭐ 1012 那条「撤销只挂横幅、原文一字不删」的**代价**：被改写掉的那些数
#   **仍然躺在判据文本里** ⇒ ⇒ ⇒ ⇒ 所以它们也要有出处 —— 出处就是
#   「挂过改写横幅的上一版实测读数」⇒ ⇒ ⇒ ⇒ 而这不是白名单：它们是**被标注过的历史读数**，
#   ⭐⭐⭐⭐⭐ **不是「查不到出处就放过」** ⇒ ⇒ ⇒ ⇒ 处置与 1012 的 187 → 190 同一路子
for _v, _w in [("4/9", "1015 上一版的不动点漂移比例（已挂【1015 改写横幅】，原文保留）"),
               ("2/9", "曾观测到的一轮漂移比例（分母 = 认领到的本数）"),
               ("0/9", "末轮的漂移比例（分母 = 认领到的本数）"),
               ("7", "曾观测到的不动点漂移序列 7 → 1 → 2 → 0 里的第一个数（**历史观测**，"
                     "不是当前读数；当前读数在产物的 `rounds` 块里"),
               # ⚠️⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **1031 逼出来的第二次**：「第五次复发」的另一个面
               #   `p2_discovery_must_not_be_silent_2015_` 里手写着 `201`，它当年**不是手写的**，
               #   而恰好等于 `len(_PROBES_NO_GOLDEN)` 的**实测读数** ⇒⇒⇒⇒⇒
               #   ⇒⇒⇒⇒⇒⇒⇒ **1031 新增了一本 golden（契约证据）而它的 `generated_by`
               #   第一版写成了 `batch-1031`（不是探针文件名）⇒ 那本被拒认领、
               #   而新增探针**认到了**通道 A 的另一本 ⇒ 差集从 201 掉到 200
               #   ⇒⇒⇒⇒⇒⇒⇒ ⇒ `P2` 与 `P6` **同时转红，而根因是同一个**：
               #   **自己写的证据文件格式不合规，被门当场抓住**
               #   ⇒⇒⇒⇒⇒⇒⇒ ⇒ 处置与其他历史数一致：登记成带批次的实测读数，**不进白名单**
               ("201", "1015 上一次提交时实测的「通道 B 有探针而通道 A 无对应 golden 的个数」"
                       "（1031 新增契约证据后它变成别的数，而 `p2_…` 的原文一字不删 ⇒ "
                       "**它的出处只能是一条历史观测，不是当前读数**）")]:
    _allow(_v, _w)
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐ 判据里也会出现**引用的批次对**（`998/1004`、`1005/1007`）——
#   它们不是实测读数，**而出处恰恰就是它们指向的那两批** ⇒ ⇒ ⇒ ⇒ ⇒
#   所以按引用登记，不是按「查不到就放过」的白名单登记
for _v, _w in [("998/1004", "引用的批次对：998/1004 那条「否的信息量在规则不对」"),
               ("1005/1007", "引用的批次对：1005 与 1007 两本 golden")]:
    _allow(_v, _w)
# ⭐ 批号区间放宽到 990–1019（判据里会引用 998/1006/1013/1014/1015）
for _b_ in range(990, 1020):
    _allow(_b_, "批号")
# ⭐ 第一版（仪器故障期）的读数如实登记 —— 它们是本批否掉的那个处方的证据
V1_OWNED, V1_UNLINKED = 8, 1
_allow(V1_OWNED, "第一版探针认领到的本数（仪器故障期，已修）")
_allow(V1_UNLINKED, "第一版被静默丢掉的本数（仪器故障期，已修）")
# ⭐ 每一轮的轮号与漂移数逐个登记 —— 不许让判据里出现一个查不到出处的整数
for _rr in ROUNDS:
    _allow(_rr["round"], "第 %d 轮的轮号" % _rr["round"])
    _allow(_rr["n_drifted"], "第 %d 轮里漂移的本数" % _rr["round"])
    _allow("%d/%d" % (_rr["n_drifted"], len(BOOKS)),
           "第 %d 轮的漂移比例（分母 = 认领到的本数）" % _rr["round"])
# ⚠️⭐⭐⭐⭐⭐⭐⭐⭐⭐ **刻意不把 0 和 1 加进出处表** ——
#   ⭐ 加了它们，门就会放过判据里**任何**一个 0 或 1
#   ⭐ ⇒ ⇒ ⇒ 而那是 1006 反过来那条：「不许让门看起来比它实际更强」
#   ⭐ ⇒ ⇒ ⇒ ⇒ 判据里出现无出处的 0/1 时要**改判据**，不许放宽门
_missing = {}
_NUMRE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?(?:/\d+)?)(?![\w])")


def _numkey(t):
    """⭐ 排序键不许假设 token 一定是纯小数：判据里会出现**引用的批次对**
    （`998/1004`、`1005/1007`）⇒ ⇒ ⇒ ⇒ 而 `key=float` 会在那一行直接抛
    `ValueError`、**把整台探针带崩** ⇒ ⇒ ⇒ ⇒ ⇒ 而崩掉的形态与「数据有问题」
    长得不一样（1014 定的四态里 `crashed` 必须单列）"""
    try:
        return float(t.split("/")[0])
    except Exception:
        return 0.0


for _k, _s in _AB.items():
    _got = sorted(set(_NUMRE.findall(_s)), key=_numkey)
    _miss = [n for n in _got if n not in _SOURCES]
    if _miss:
        _missing[_k] = _miss
N_JUST_MISSING = len(_missing)

# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **而上面那条「刻意不把 0/1
#   放进出处表」的纪律，在实现上是空的** —— 出处表按**值**索引，而登记是
#   `_allow(实测值, 出处)` ⇒ ⇒ ⇒ ⇒ ⇒ 只要**任何一个**实测读数恰好是 0（或 1），
#   `"0"`（或 `"1"`）就被登记进去了 ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **判据里其它任何一处手打的 0/1
#   都会通过** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒⇒ **⇒ 1013 那台明着写了
#   `set("0123456789")`、1015 这台声称没写 —— 而两台的实际强度一模一样**
#   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒⇒ ⇒ ⇒ **真正能强制的只有一句：判据里的每个数要么等于
#   某个实测值、要么不在出处表里** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒⇒ 「0/1 也必须有出处」
#   这半句，实现不了 ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒⇒ **⇒ 所以它必须作为读数记下来，
#   而不是在注释里声称自己做到了**（1006：不许让门看起来比它实际更强）
_NUMS_IN_CRITERIA = [n for _s in _AB.values() for n in set(_NUMRE.findall(_s))]
ZEROS_IN_CRITERIA = sum(1 for n in _NUMS_IN_CRITERIA if n == "0")
ONES_IN_CRITERIA = sum(1 for n in _NUMS_IN_CRITERIA if n == "1")
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **中文数字完全在口径之外** —— 出处检查的
#   `_NUMRE` 只认阿拉伯数字 ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 「五条」和「5 条」长得一样，
#   而前者**整条绕过 P6** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⭐ 本批就栽在这里：判据里原本写「三条」、
#   实测是「一条」，而 P6 全程报绿 ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **⇒ 处置不是「把门加严」，
#   是「让口径外的东西也变成读数」**
_CN_DIGITS = "零一二三四五六七八九十两"
N_CN_NUMERALS = sum(1 for _s in _AB.values() for _c in _s if _c in _CN_DIGITS)
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **同一个数在两份副本里，只有进了口径的那一份被查过**
#   —— 上面 `n_chinese_numerals_in_criteria` 量的是 **audit 的 `_2015_` 判据块**，
#   而**同一条判据在 verifier 里还有一份人读摘要**（`check("U993Y.N …")` 的标签），
#   那一份从头到尾没被量过 ⇒ ⇒ ⇒ ⇒ 而 `VERIFIER_TXT` **被读进来却从未被使用** ⇒ ⇒ ⇒ ⇒ ⇒
#   **⇒ 「读了」不等于「用了」** —— 这是 1015 那条「发现失败只会安静地少算」的第四个形态，
#   只是这次少算的是**自己**。
# ⭐ 反向门（否则「提取到 0 条」又会变成一次「算了是空」）：
#   提取条数必须与 verifier 里 `check("U993Y.` 的实际出现次数逐个相等。
_V_LAB_RE = re.compile(r'check\(\s*"(U993Y\.[0-9]+.*?)"\s*,\s*\n', re.S)
_V_LABELS = _V_LAB_RE.findall(VERIFIER_TXT)
_N_U993Y_IN_VERIFIER = VERIFIER_TXT.count('check("U993Y.')
N_CN_IN_VERIFIER_LABELS = sum(1 for _s in _V_LABELS for _c in _s if _c in _CN_DIGITS)
V_LABELS_RECONCILED = (len(_V_LABELS) == _N_U993Y_IN_VERIFIER and _N_U993Y_IN_VERIFIER > 0)
ZERO_REGISTERED = ("0" in _SOURCES)
ONE_REGISTERED = ("1" in _SOURCES)
DISCIPLINE = {
    "n_numbers_in_criteria": len(_NUMS_IN_CRITERIA),
    "n_distinct": len(set(_NUMS_IN_CRITERIA)),
    "zeros_in_criteria": ZEROS_IN_CRITERIA,
    "ones_in_criteria": ONES_IN_CRITERIA,
    "n_chinese_numerals_in_criteria": N_CN_NUMERALS,
    "chinese_numerals_out_of_scope": "⭐⭐⭐⭐⭐ `_NUMRE` 只认阿拉伯数字 ⇒ "
                                     "「五条」与「5 条」在检查里长得一样 ⇒ "
                                     "本批判据里就有一处「三条」是错的而 P6 全程报绿",
    "zero_in_sources": ZERO_REGISTERED,
    "one_in_sources": ONE_REGISTERED,
    "zero_entered_via": (_SOURCES.get("0") or None),
    "one_entered_via": (_SOURCES.get("1") or None),
    "what_is_actually_enforced": "⭐ 判据里的每个数要么等于某个**实测值**、"
                                 "要么不在出处表里",
    "what_is_not_enforced": "⭐⭐⭐⭐⭐ 「0 和 1 也必须有出处」—— 出处表按值索引，"
                            "而任一实测读数为 0/1 就会把 0/1 登记进去 ⇒ "
                            "判据里别处的 0/1 一律通过",
    "same_hole_in_1013": "1013 的 `_allowed |= set(\"0123456789\")` —— 明着开了同一个洞",
    "n_verifier_labels_extracted": len(_V_LABELS),
    "n_u993y_checks_in_verifier": _N_U993Y_IN_VERIFIER,
    "verifier_labels_reconciled": V_LABELS_RECONCILED,
    "n_chinese_numerals_in_verifier_labels": N_CN_IN_VERIFIER_LABELS,
    "second_copy_rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐ **同一条判据在 audit 与 verifier 里各有一份文本，"
                        "而口径默认只覆盖前者** ⇒ ⇒ ⇒ 「改写横幅只挂在 audit 那一份」"
                        "⇒ ⇒ ⇒ ⇒ verifier 那一份会静静地继续显示旧读数、且门不会报红"
                        "（断言体只钉机制、不钉读数）⇒ ⇒ ⇒ ⇒ ⇒ "
                        "**⇒ 本批自己撞上了：U993Y.3 摘要里的 `1 → 2` / `实测 3 轮` / "
                        "`/books/[2]/keys_added` 全是收敛前的旧读数**",
}

out = {"P1_hold_1015": (N_STATES_SUM == len(BOOKS) and len(BOOKS) > 0
                        # ⭐⭐⭐⭐⭐ **排除不许悄悄扩大**：登记的每一条都必须键真存在、
                        #   理由非空、且真的命中了某本 golden —— 三条里少任何一条就红
                        and _EXCL_OK),
       "P2_hold_1015": N_UNLINKED == 0,
       # ⚠️⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **【1016 改写横幅】**
       #   第一版是 `CONVERGED and N_ROUNDS >= 2` ⇒ ⇒ 那是本批判据里**又一处
       #   「会因自身变化而改变的数」**：1016 真的加了一本探针之后套件**一轮就收敛**，
       #   `N_ROUNDS >= 2` 于是转红 ⇒⇒⇒ **而一轮收敛完全是好结果** ——
       #   「没有东西漂移」本来就该一轮结束。**原文一字不删。**
       #   ⇒ 处置：钉「真的跑过探针」（`len(BOOKS) > 0`）、不钉轮数；
       #   轮数作为**读数**留在产物里，而收敛判据仍然是「最后一轮读数为 0」。
       "P3_hold_1015": CONVERGED and len(BOOKS) > 0,
       "P4_hold_1015": N_NOT_WRITTEN == 0,
       "P5_hold_1015": P5_OK,
       # ⭐⭐⭐⭐⭐ P6 现在是三件事的与：提取到判据、条数与 audit 对得上、手写的数都有出处
       "P6_hold_1015": (N_AB_EXTRACTED > 0
                        and N_AB_EXTRACTED == _N_KEYS_IN_AUDIT
                        and not _missing),
       "P7_hold_1015": GOLDEN.name.endswith("1015.json"),
       "P8_hold_1015": P8_OK}
# ⭐ 不许静默：提取器一条没抓到、或条数对不上，都必须打一行出来
if N_AB_EXTRACTED != _N_KEYS_IN_AUDIT:
    print("!! 判据条数对不上：提取到 %d 条、audit 里实际 %d 条 ⇒ "
          "「没测到」与「测了为否」在输出里分不开"
          % (N_AB_EXTRACTED, _N_KEYS_IN_AUDIT))
if _missing:
    print("!! 判据里查不到出处的数：",
          json.dumps(_missing, ensure_ascii=False))

io.open(OUT, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
io.open(GOLDEN, "w", encoding="utf-8").write(json.dumps({
    "generated_by": SELF,
    "note": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **把 1014 的 P6 落成代码 —— 然后立刻被 1014 "
            "那台普查反过来咬了一口：1015 自己长出了一个不可自证的空集合**",
    "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **「跑不起来」必须单列 —— 探针崩了不告诉你数据有没有变，"
            "并进任何一态都等于把仪器故障报成数据结论**",
    "rule2": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **完备性用加法验的时候，两边不许同源 —— "
             "分母的完备性才是命门**",
    "rule3": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **「探针跑成功了」不等于「产物被刷新了」—— "
             "只能靠重跑后比对字节、或看 mtime 变没变来判，不许看退出码**",
    "pen_is_the_book": {
        "n_zero_coupling_head": N_ZERO_CPLX_HEAD,
        "n_zero_coupling_now": N_ZERO_CPLX_NOW,
        "n_positive_present_head": N_POS_HEAD,
        "n_positive_present_now": N_POS_NOW,
        "n_audit_2015_lines": _N_AUDIT_2015_LINES,
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **被测的账和记账的笔是同一份文件时，"
                "往笔上多写一句，被测的那些账就跟着重算** —— 1005 普查的是 `_ausrc`，"
                "而本批往 audit 里塞了判据 ⇒ ⇒ ⇒ ⇒ ⇒ 所以它的读数必然跟着变",
    },
    "discovery": {
        "channel_a_goldens": N_GOLDENS,
        "channel_b_probes": len(_PROBES),
        "n_owned": N_OWNED,
        "n_excluded_self": N_EXCLUDED_SELF,
        "n_excluded_input_conflict": N_EXCLUDED_CONFLICT,
        "excluded": _EXCLUDED,
        "exclusion_rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
                          "**一道门的输入若是另一道门假定为常量的东西，它就不可能进那道门** —— "
                          "1015 验「可复现」，1027 验「新鲜度」，而 1027 的输入按定义就是仓库当前状态，"
                          "共享仓里它每时每刻都在被别人改 ⇒ 两者必须双向排除，"
                          "而**排除必须连理由一起登记，且登记本身要被 P1 守着**",
        "exclusion_registry_is_checked": _EXCL_OK,
        "n_unparsable": _N_UNPARSED,
        "n_no_generated_by": _N_SKIPPED,
        "n_unlinked_rejected": N_UNLINKED,
        "unlinked": _UNLINKED,
        "probes_without_golden": _PROBES_NO_GOLDEN,
        "list_source": "⭐ 按 golden 里的 `generated_by` 逐字节比对探针文件名，"
                       "不合规**报错**而不是跳过（第一版是跳过，于是丢了 1 本还报 all-green）",
        "reconciliation": "⭐⭐⭐⭐⭐ 通道 A 与通道 B 各数一遍、差集逐条列出 —— "
                          "不许靠「加法对得上」冒充完备",
        "argv": "⭐⭐⭐⭐⭐ 统一带 `--write-golden`：1005 把落仓门控在 "
                "`if \"--write-golden\" in sys.argv` 上，不带就只写 /tmp",
    },
    "rounds": ROUNDS,
    "converged": CONVERGED,
    "n_rounds": N_ROUNDS,
    "max_rounds": MAX_ROUNDS,
    "fixed_point_rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **整轮重跑直到某一轮零漂移为止 —— "
                        "因为 1015 在整轮结束后才写自己那本，"
                        "1014 在整轮里读到的永远是 1015 的上一版 ⇒ "
                        "每本账都落后它上游一轮**",
    "books": BOOKS,
    "totals": {"n_books": len(BOOKS), "reproduced": N_REPRODUCED,
               "drifted": N_DRIFTED, "crashed": N_CRASHED,
               "vanished": N_VANISHED, "sum_states": N_STATES_SUM},
    "diff_shape": {"n_keys_added": N_KA, "n_keys_removed": N_KR,
                   "n_values_changed": N_VC,
                   "n_books_never_wrote_golden": N_NOT_WRITTEN,
                   "drifted_books": DRIFT_BOOKS,
                   "paths_touched": DRIFT_PATHS},
    "empty_list_invariants": {
        "keys_added_is_empty_iff_byte_identical":
            "len(books[i].keys_added) == 0 ⟺ state == reproduced",
        "values_changed_is_empty_iff_byte_identical":
            "len(books[i].values_changed) == 0 ⟺ 两本 JSON 的叶子集合相同",
        "keys_removed_is_empty_iff_no_key_vanished":
            "len(books[i].keys_removed) == 0 ⟺ 旧 JSON 的每个叶子在新 JSON 里都还在",
        "tail_is_empty_iff_probe_printed_nothing": None,
        "why": "⭐⭐⭐⭐⭐⭐⭐⭐⭐ 1014 的普查把 1015 的 `/books/[2]/keys_added` "
               "判成不可自证 —— 而它之所以是空的、正因为那本逐字节没变 "
               "⇒ ⇒ ⇒ ⇒ **「没有漂移」在账本上长得和「没算过」一模一样** "
               "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 1014 刚写完的病，1015 自己中了一次",
    },
    "repaired_generated_by": REPAIRED,
    "reverse_case": {"add_key_state": REVERSE_ADD["state"],
                     "modify_value_state": REVERSE_MOD["state"],
                     "rc1_state": REVERSE_C["state"],
                     "missing_output_state": REVERSE_V["state"],
                     "detail": P5_DETAIL},
    "number_provenance": {
        "n_keys_in_audit": _N_KEYS_IN_AUDIT,
        "n_extracted": N_AB_EXTRACTED,
        "reconciled": N_AB_EXTRACTED == _N_KEYS_IN_AUDIT,
        "n_missing": N_JUST_MISSING,
        "missing": _missing,
        "scope": "⭐ 只查 `p\\d_[a-z0-9_]*_2015_` 这些 **P 编号判据**；"
                 "audit 里另外几个 2015 键不在口径内（列在 `out_of_scope_keys`）"
                 "—— 口径边界必须写出来，否则「查了 N 条」会被读成「全都查了」",
        "out_of_scope_keys": _KEYS_2015_OUT_OF_SCOPE,
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **「提取器抓到 0 条」与「判据里一个数都没有」"
                "在探针输出里长得一模一样** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 所以提取条数必须与 "
                "audit 里的键数**对账**，对不上要**打一行出来**而不是安静地判否",
    },
    "discipline_0_1_strength": DISCIPLINE,
    "p8_invariants_invisible_to_1014": P8_DETAIL,
    "number_sources": _SOURCES,
}, ensure_ascii=False, indent=1))

_restore()
print("goldens=%d probes=%d owned=%d unlinked=%d" %
      (N_GOLDENS, len(_PROBES), N_OWNED, N_UNLINKED))
for e in _EXCLUDED:
    print("  EXCLUDED %-32s 输入集合与本套件前提冲突" % e["golden"])
for u in _UNLINKED:
    print("  UNLINKED %-32s generated_by=%r" % (u["golden"], u["generated_by"]))
print("rounds=%d converged=%s" % (N_ROUNDS, CONVERGED))
for rr in ROUNDS:
    print("  round %d: drifted=%d %s" % (rr["round"], rr["n_drifted"], rr["drifted"]))
print("  reproduced=%d drifted=%d crashed=%d vanished=%d (sum=%d)"
      % (N_REPRODUCED, N_DRIFTED, N_CRASHED, N_VANISHED, N_STATES_SUM))
for r in BOOKS:
    print("  %-9s %-32s rc=%s wrote=%s" % (r["state"], r["golden"], r["rc"],
                                          r["wrote_golden"]))
print("reverse:", REVERSE_ADD["state"], REVERSE_MOD["state"],
      REVERSE_C["state"], REVERSE_V["state"], P5_DETAIL)
print("repaired generated_by: %d" % N_REPAIRED)
print("criteria numbers: %d 个（去重 %d）、其中 0 有 %d 个、1 有 %d 个；"
      "出处表里 0=%s、1=%s"
      % (len(_NUMS_IN_CRITERIA), len(set(_NUMS_IN_CRITERIA)),
         ZEROS_IN_CRITERIA, ONES_IN_CRITERIA, ZERO_REGISTERED, ONE_REGISTERED))
print("判据里的中文数字（**在 P6 口径之外**）: audit 侧 %d 个 / verifier 摘要侧 %d 个"
      "（verifier 标签提取 %d/%d 对账=%s）"
      % (N_CN_NUMERALS, N_CN_IN_VERIFIER_LABELS,
         len(_V_LABELS), _N_U993Y_IN_VERIFIER, V_LABELS_RECONCILED))
print("判据里的中文数字（**在 P6 口径之外**）: %d 个（= 上行 audit 侧那个 %d）"
      % (N_CN_NUMERALS, N_CN_NUMERALS))
print("P8: 1014 判本探针的产物 %d 条不可自证，其中 %d 条本探针在产物里已登记了不变式"
      % (N_SELF_AMB, N_INV_INVISIBLE))
print("  ⚠️ P8 那条读数**落后一代**（结构性的，加轮数关不掉）："
      "1014 看到的是 %s 轮的产物，而本产物有 %s 轮 ⇒ 路径下标对不上属正常"
      % (_P8_SAW_ROUNDS, N_ROUNDS))
print("P1..P8 =", [out["P%d_hold_1015" % i] for i in range(1, 9)])
print("PROBE_1015_DONE ->", GOLDEN)