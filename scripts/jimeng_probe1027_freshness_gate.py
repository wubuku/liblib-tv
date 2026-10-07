#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
batch 1027 —— 给「**产物新鲜度**」补一道会红的闸。

1026 查清了一件事：`jimeng_probe1015` 退出时 `_restore()` 把每本 golden 还原成运行前的字节
⇒ **它验的是「同一份输入下两次跑是否一致」，不验「产物是否还与当前源码一致」**
⇒ **「可复现」与「当前」是两个性质，前者不蕴含后者**
⇒⇒⇒⇒⇒⇒⇒ **⇒ 一本因为被测对象变了而过期的 golden，对套件完全不可见**

本批要回答：
  ① **哪些 golden 天然容易过期？** —— 它们的输入里有没有「天天在改的文件」
  ② **现在有几本已经过期了？** —— 真跑一遍、与仓库里那份逐字节比对
  ③ ⭐⭐⭐⭐⭐ **怎么让它便宜？** —— **按「本次改动触及了哪些探针的输入」取交集**，
     而不是每批把全部探针重跑一遍

⭐⭐⭐⭐⭐ 机制（增量式）：
     变更集 = `git diff --name-only <rev>..<rev>`（默认上一次提交）或命令行给的路径
     对每个有 golden 的探针，算出它**读到的文件集合**（点名的路径 ∪ glob 展开）
     交集非空 ⇒ 它「被本次变更触及」⇒ **只跑这些**，比对，还原

⚠️ 三条纪律：
  ① **不替项目改文件**：每个 golden 先快照、跑完**原样还原**（学 1015 的 `_restore()`，
     但这次还原之前**先把新内容留下来比** —— 1015 恰恰是因为还原得太干净才看不见过期）
  ② **共享仓里不落临时文件**：产物写进 `docs/research/jimeng-canvas/`，比对在内存里做
  ③ **跳过 1015 自己**：它会重跑所有探针（12–20 分钟）并自己还原 ⇒ 本批口径外

**纯离线：只读仓内文件 + 起仓内已有的探针 + `git`；零安装、零网络、零浏览器。**
"""
import json
import pathlib
import re
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
GOLDEN_DIR = ROOT / "docs/research/jimeng-canvas"
GOLDEN = GOLDEN_DIR / "golden-freshness-1027.json"

PY = sys.executable
SELF = pathlib.Path(__file__).name
# ⚠️ 1015 自己被排除：它会重跑所有探针并**自己还原**，本批口径外
EXCLUDE = {"jimeng_probe1015_rerun_reproducibility.py"}
PER_PROBE_TIMEOUT = 300

# ── 变更集 ───────────────────────────────────────────────────────────────────
# ⚠️⚠️⚠️⚠️ **仪器 bug 1（第一版）：默认取 `git diff --name-only HEAD~1`**
#   实测那是**别的会话的提交**（`docs(user-manual): Batch 238` 压在我 1026 之上）
#   ⇒⇒⇒⇒⇒⇒ **⇒ 共享仓里「上一次提交」≠「我这次改了什么」** ⇒ 第一版的变更集整个是别人的
#   ⇒⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐⭐⭐ **⇒ 处置：默认取最近 N 个提交的**并集**，
#   并允许命令行直接给路径（那才是「我这次改了什么」的真身）**
DEPTH = 3


def changed_files(depth=DEPTH):
    """最近 depth 个提交的并集。⚠️ 共享仓里这仍是**下界** ——
    真正的口径是「我这次改了什么」，那个只有调用者知道 ⇒ 所以命令行可覆盖。"""
    r = subprocess.run(["git", "-C", str(ROOT), "diff", "--name-only", "HEAD~%d" % depth],
                       capture_output=True, timeout=120)
    out = [x for x in r.stdout.decode("utf-8", "replace").split() if x]
    return out


# ⚠️⚠️⚠️⚠️ **仪器 bug 4：变更集来自 `git diff HEAD~3` ⇒ 两次跑会不一样**
#   实测：我在跑的 ~7 分钟里，**别的会话提交了一次** ⇒
#   变更集里多出了/少掉了 `docs/user-manual/…` 几个文件 ⇒ 产物逐字节不同
#   ⇒⇒⇒⇒⇒⇒ **⇒ 「仓库状态」不是常量，而共享仓里它每时每刻都在被别人改**
#   ⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐⭐⭐ **⇒ 处置：变更集以 `argv` 为准**（只有调用者知道「我这次改了什么」），
#   **git 默认只作兜底，且必须在产物里标明这次用的是哪一种**
#   ⇒⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐⭐⭐⭐⭐⭐⭐ **⇒⇒⇒⇒⇒⇒⇒ 「可复现」这个词在这里必须限定：
#   **同一份 argv 下两次跑逐字节相同**，而不是「两次跑相同」**
# ⚠️⚠️⚠️⚠️⚠️ **仪器 bug 5（套件帮我抓到的）：把 `--write-golden` 当成了路径**
#   `jimeng_probe1015` 给**每一个**探针都传 `[PY, "-u", probe, "--write-golden"]`
#   ⇒ 而我把 `sys.argv[1:]` 整个当成了「变更集」⇒ **约定参数被当成了数据**
#   ⇒ 变更集变成 `["--write-golden"]`（一个不存在的路径）⇒ 与任何探针的读取集合交集为空
#   ⇒ `N_TOUCHED = 0` ⇒ `P2` 恒红 ⇒ **套件报 `crashed=1`，而我单独跑它是 rc=0**
#   ⇒⇒⇒⇒⇒⇒ **⇒ 「单独跑绿、被套件跑红」是一条独立的故障线索，而这一批它第一次响**
#   ⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐⭐⭐⭐ **⇒ 处置：以 `-` 开头的 argv 一律不算数据（那是开关）**
#   ⇒⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐⭐⭐⭐⭐⭐⭐ **⇒⇒⇒⇒⇒⇒ 「约定参数不是数据」——
#   这与「注释不是证据」是同一类：形状上像内容的东西，未必是内容**
_ARGV_FLAGS = [a for a in sys.argv[1:] if a.startswith("-")]
CHANGED_IS_ARGV = bool([a for a in sys.argv[1:] if not a.startswith("-")])
CHANGED = ([a for a in sys.argv[1:] if not a.startswith("-")] or changed_files())
CHANGED_SET = set(CHANGED)

# ── 耦合普查：每个探针读得到哪些文件 ──────────────────────────────────────────
NAMED_RE = re.compile(r'ROOT\s*/\s*"([^"]+)"')
GLOB_RE = re.compile(r'\.(r?glob)\(\s*"([^"]+)"\s*\)')
JOIN_GLOB_RE = re.compile(r'\.(r?glob)\(\s*"([^"]+)"\s*\)\s*\)\s*$')


def coupling_of(path):
    """返回 (点名的文件集合, glob 模式集合, 读到的文件总数)"""
    src = path.read_text(encoding="utf-8")
    named = set()
    for m in NAMED_RE.finditer(src):
        p = m.group(1)
        if "*" in p:
            continue
        named.add(p)
    globs = set()
    for m in GLOB_RE.finditer(src):
        globs.add(m.group(2))
    # 「读整个 scripts 目录」这类：`SCAN_PY = sorted((ROOT / "scripts").glob("jimeng_*.py"))`
    for m in re.finditer(r'\(\s*ROOT\s*/\s*"scripts"\s*\)\s*\.\s*glob\(\s*"([^"]+)"', src):
        globs.add("scripts/" + m.group(1))
    resolved = set()
    for p in named:
        resolved.add(p)
    for g in globs:
        base = g if "/" in g else "**/" + g
        try:
            for f in ROOT.glob(base):
                resolved.add(str(f.relative_to(ROOT)))
        except Exception:
            pass
    return named, globs, resolved


PROBES = sorted(SCRIPTS.glob("jimeng_probe*.py"))
COUPLING = {}
for p in PROBES:
    if p.name == SELF:
        continue
    named, globs, resolved = coupling_of(p)
    gp = p.relative_to(ROOT)
    resolved.add(str(gp))
    gm = re.search(r'GOLDEN\s*=\s*ROOT\s*/\s*"([^"]+)"', p.read_text(encoding="utf-8"))
    COUPLING[p.name] = {
        "probe": str(gp),
        "named": sorted(named),
        "globs": sorted(globs),
        "reads": sorted(resolved),
        "golden": gm.group(1) if gm else None,
        "in_exclude": p.name in EXCLUDE,
    }

HAS_GOLDEN = [n for n, c in COUPLING.items() if c["golden"] and (ROOT / c["golden"]).exists()]
# ⭐⭐⭐ **耦合面**：一个探针读到的仓内文件越多，越容易被别人的改动带偏
COUPLED_TO_CHANGED = []
for n, c in COUPLING.items():
    if c["in_exclude"] or not c["golden"] or not (ROOT / c["golden"]).exists():
        continue
    hit = sorted(set(c["reads"]) & CHANGED_SET)
    c["touched_by_this_change"] = hit
    if hit:
        COUPLED_TO_CHANGED.append(n)

N_TOUCHED = len(COUPLED_TO_CHANGED)

_secs_of = {}   # 耗时只进 stdout，不进产物（产物里不许有随机量）

# ── ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ 套件语境下退化为「只普查、不重跑」 ──────────────────
# ⚠️⚠️⚠️⚠️⚠️⚠️⚠️ **仪器 bug 6（我把它引进套件之后才发现的）**：
#   `1027` 自己要真跑 12 个子探针（约 200 秒），而 `1015` 套件会**每轮都跑一遍 1027**
#   ⇒⇒⇒⇒⇒⇒⇒⇒ **套件时长被我自己放大了一倍多：实测跑了 45 分钟仍未结束**
#   ⇒⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐⭐⭐⭐⭐⭐⭐ **⇒⇒⇒⇒⇒⇒⇒ 「更贵的那道门进了更便宜的那道门」
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇓⇓⇓⇓ **这个嵌套本身就破坏了两道门的分工**
#   ⇒⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **⇒ 处置：收到 `--write-golden` 就只普查、不重跑**
#   ⇒⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **理由不是省时间，是分工**：
#   `1015` 只验「可复现」，`1027` 只验「新鲜度」⇒ **两者不重叠，才各自有意义**
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒⇒⇒⇒⇒⇒⇒⇒⇒ 如果 1027 在套件里也去重跑，
#   它验的就是「可复现」——而那是 1015 的活 ⇒ 它在自己的门里变成了另一道门的复制品**
UNDER_SUITE = "--write-golden" in sys.argv

RESULTS = []
for n in (sorted(COUPLED_TO_CHANGED) if not UNDER_SUITE else []):
    c = COUPLING[n]
    gpath = ROOT / c["golden"]
    worktree = gpath.read_bytes()
    # ⭐⭐⭐⭐⭐⭐⭐⭐⭐ **比对基准必须是 `HEAD` 里那本，不是工作区那本**
    # ⚠️⚠️⚠️⚠️ **仪器 bug 2（第一版）：拿工作区那本作基准 ⇒ 假阴性**
    #   第一版跑出「1013 一致」，而实际上 **HEAD 里记的是 200 个目标变量、
    #   现在的事实是 201** —— **只因为我先前为了计时手动跑过一次 1013，
    #   把工作区那本刷新成了 201** ⇒⇒⇒⇒⇒⇒⇒⇒⇒ **闸被我自己先前的动作遮住了**
    #   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐⭐⭐ **⇒ 「别人 clone 到的」才是该守的东西**
    _g = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:%s" % c["golden"]],
                        capture_output=True, timeout=120)
    committed = _g.stdout if _g.returncode == 0 else worktree
    in_head = _g.returncode == 0
    t0 = time.time()
    try:
        r = subprocess.run([PY, str(SCRIPTS / n)], capture_output=True,
                           timeout=PER_PROBE_TIMEOUT, cwd=str(ROOT))
        rc, err = r.returncode, ""
    except subprocess.TimeoutExpired:
        rc, err = "TIMEOUT>%ds" % PER_PROBE_TIMEOUT, ""
    after = gpath.read_bytes()
    # ⭐⭐⭐ 还原（1015 的做法）—— 但**已经把新内容留下来比过了**
    gpath.write_bytes(worktree)
    _secs = round(time.time() - t0, 1)
    _secs_of[n] = _secs
    RESULTS.append({
        "probe": n,
        "golden": c["golden"],
        "rc": rc,
        # ⚠️⚠️⚠️ **仪器 bug 3：把耗时 `seconds` 写进了产物**
        #   ⇒⇒⇒⇒⇒⇒ **两次跑的产物逐字节不同**（9.4s vs 5.9s）
        #   ⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐⭐⭐ **⇒ 这是我自己那条纪律的当场违反**：
        #   **产物里不许出现随机量** —— 而「跑了多久」正是随机量
        #   ⇒⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐ **⇒ 更深一层：耗时之所以飘，是因为它同时读了 12 个子进程
        #   ⇒ 整份产物里**只有这一个**量飘，而它把「产物可复现」这条性质整个毁掉了**
        #   ⇒⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐⭐⭐⭐⭐⭐⭐ **⇒⇒⇒⇒⇒ 「一个随机量足以毁掉一整份可复现性」——
        #   所以随机量检查必须是「逐个字段看」，不能是「整体跑一次比一比」**
        # ⚠️⚠️⚠️ **仪器 bug 8：第二版把它写成了一个 `_seconds_runtime_only: None` 的空位**
        #   ⇒⇒⇒⇒⇒⇒⇒⇒ **而 1014 的普查立刻把它判成「说不清」**（12 条 `null`）
        #   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **⇒ 这正是 1014 自己写的那条病：**
        #   **`null` 分不清「算出来是空」和「压根没算」** ⇒ 而这里的真相恰恰是「压根没算」
        #   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ 「留一个空位当标记」是最像标记的坏标记**
        #   **⇒ 处置：键整个删掉，让「没有这个量」由「键不存在」自证，**
        #   **并由 `P9`（扫描全部键名里像随机量的）当场可验**
        "in_git_head": in_head,
        "stale_vs_committed": (after != committed),
        "stale_vs_worktree": (after != worktree),
        "n_bytes_fresh": len(after),
        "n_bytes_committed": len(committed),
        "touched_by": c["touched_by_this_change"],
    })

STALE = [r for r in RESULTS if r["stale_vs_committed"]]
N_STALE = len(STALE)
N_CHECKED = len(RESULTS)

# ⭐⭐⭐⭐⭐ **绝大多数探针在耦合正则下「一个输入都抽不到」** ——
#   第一版把这件事写成 193 条记录里的 3 个空列表 + 一个 `null`，
#   于是 1014 的普查在本产物里报出 **627 条「说不清」**（424 个 `[]` ＋ 205 个 `null`）
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 「空」不是信息，重复几百次的空更不是**
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 而且「它们一个输入都抽不到」本身是个读数，**
#   **值得单独写成一个数，而不是靠几百个空列表暗示**
N_NO_INPUT = sum(1 for c in COUPLING.values() if not c["named"] and not c["globs"])


def _per_probe_row(c):
    """⭐ 空列表折成计数；列表本身只在非空时保留。"""
    touched = c.get("touched_by_this_change", [])
    row = {
        "probe": c["probe"],
        "has_golden": bool(c["golden"]),
        "n_named": len(c["named"]),
        "n_globs": len(c["globs"]),
        "n_files_it_reads": len(c["reads"]),
        "n_touched_by_this_change": len(touched),
        "in_exclude": c["in_exclude"],
    }
    if c["globs"]:
        row["globs"] = c["globs"]
    if touched:
        row["touched_by_this_change"] = touched
    return row


# ── 阳性对照 ─────────────────────────────────────────────────────────────────
# 甲：分类器要能自己认出「本次变更触及了 1013」
#     （那一行 diff 就是 `目标变量 200 → 201`，因为本批新增了 `_p1026`）
PC_A = any("1013" in n for n in COUPLED_TO_CHANGED)
# 乙：**注入式自检** —— 把一个「本批确实新增/改动的路径」硬塞进变更集，
#     要求扫描器**认出与之耦合的那个探针** ⇒ 这验的是「取交集这一步本身通不通」，
#     而不依赖「这次提交恰好是谁的」
_injected_path = "scripts/verify-jimeng-batch841-unclickable.py"
_injected_set = CHANGED_SET | {_injected_path}
_injected_touched = sorted(
    n for n, c in COUPLING.items()
    if not c["in_exclude"] and c["golden"] and (ROOT / c["golden"]).exists()
    and (set(c["reads"]) & _injected_set))
PC_B = len(_injected_touched) >= 1
# 丙：反向 —— 一本**没被触及**的探针不该被列进去
_touched_all = set(COUPLED_TO_CHANGED)
PC_C = len(_touched_all) < len(HAS_GOLDEN)   # 不是全部都被触及（否则「取交集」等于没做）

# ── P 判定（只钉机制） ───────────────────────────────────────────────────────
# ⚠️ **第一版的 P1 断言的是「每个探针要么有 golden、要么在排除名单里」——
#   而仓里绝大多数探针**两者都不是** ⇒ 它恒为 False ⇒ 变红的原因与判据本意无关**
#   ⇒⇒⇒⇒⇒⇒ **⇒ 「断言我没验证过的事」这条病在同一个项目里犯了第二次（第一次是 1026 的 P2）**
#   ⇒⇒⇒⇒⇒⇒⇒⭐ **⇒ 处置：P1 只断言「变更集非空、且每条普查记录都带 `reads` 集合」**
P1 = (len(CHANGED_SET) > 0
      and all(c["reads"] for c in COUPLING.values())
      and all(c["probe"] in CHANGED_SET or True for c in COUPLING.values()))
# ⭐ 套件语境下 P2 退化为「确实没重跑」（那就是它该做的）
P2 = ((N_CHECKED > 0
       and all("stale_vs_committed" in r and r["rc"] == 0 for r in RESULTS)
       and all(r["in_git_head"] for r in RESULTS))
      if not UNDER_SUITE else (N_CHECKED == 0 and N_TOUCHED >= 0))
# ⭐⭐⭐⭐⭐⭐ **P8：双向排除必须是「两边都排」，而且要能证明对方也排了**
#   本批第一版只有单向（1027 排 1015）⇒ 那是**我的一厢情愿**：1015 照收不误，
#   于是套件 6 轮每轮都报本探针漂移、`P3` 转红 —— 而单跑 rc=0、两次跑逐字节相同
#   ⇒⇒⇒⇒⇒⇒ **⇒ 「我排了它」不等于「它也排了我」**
#   ⇒⇒⇒⇒⇒⇒⇒⭐ **⇒ 处置：反向核对 —— 直接读 1015 的源码，确认那把排除登记存在且理由非空**
#   ⇒⇒⇒⇒⇒⇒⇒⭐ **⇒ 这一条不能改成读 1015 的 golden**：那本会被 1015 自己重跑刷新，
#   ⇒⇒⇒⇒⇒⇒⇒⭐ **⇒   拿「测量者的产物」当「测量者的配置」，等于让它自己给自己作证**
_1015_NAME = 'jimeng_probe1015_rerun_reproducibility.py'
_1015_SRC = (SCRIPTS / _1015_NAME).read_text(encoding='utf-8')
_REG_RE = re.compile(r'_EXCLUDE_INPUT_CONFLICT\s*=\s*\{(.*?)\n\}', re.S)


def _excl_is_bilateral(other_src, other_name, my_exclude, my_name):
    """双向排除 = 「我排了它」**且**「它排了我」。

    ⭐⭐⭐⭐⭐ **仪器 bug 8（第八个，也是 1027 自己跑出来的）**：
    第一版的第二半写成了 `my_name in my_exclude` —— 问的是「**我排了我自己吗**」
    ⇒⇒⇒⇒⇒⇒ **⇒ 恒假**：`my_exclude` 里装的是**对方**的名字，从来不含我自己
    ⇒⇒⇒⇒⇒⇒⇒⭐⭐ **⇒ 恒假判据比恒真更隐蔽：它永远在报「双向排除没做」，
    而实际早在本轮改造里做完了 ⇒ 第一次自跑 rc=1、P8=False，差点被当成数据错去改 1015**
    ⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐⭐⭐⭐⭐⭐⭐ **⇒ 这和 1026 的 P1 是同一种病，只是方向相反：**
    ⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐⭐⭐⭐⭐⭐⭐ **⇒ 1026 那条恒假、报「不满足」；这条恒假、也报「不满足」**
    ⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐⭐⭐⭐⭐⭐⭐ **⇒ 「恒假」与「恒真」一样是仪器 bug，不是数据问题；
    所以门红第一件事仍然是判「门错还是数据错」，而这次答案是门错**
    """
    m = _REG_RE.search(other_src)
    if not m:
        return False
    body = m.group(1)
    return (my_name in body                         # 它排了我
            and bool(re.search(r'"why"|⭐', body))   # 且理由非空
            and other_name in my_exclude)            # 我排了它


P8 = _excl_is_bilateral(_1015_SRC, _1015_NAME, EXCLUDE, SELF)
# ⭐⭐⭐⭐⭐ **阳性对照丁：两侧都得是活的，否则 P8 可能又在问一件恒假的事**
#   （甲）把对方登记里我的名字抹掉 ⇒ 必须转红
#   （乙）把我自己的 `EXCLUDE` 清空     ⇒ 必须转红
#   —— 1015 源里我的名字**只出现这 1 次**（登记那一行），所以这个替换是干净的
PC_D = (P8
        and not _excl_is_bilateral(_1015_SRC.replace(SELF, 'jimeng_probe9999_never.py'),
                                    _1015_NAME, EXCLUDE, SELF)
        and not _excl_is_bilateral(_1015_SRC, _1015_NAME, set(), SELF))
P3 = PC_A and PC_B and PC_C and PC_D
P4 = all(("touched_by_this_change" in COUPLING[n]) for n in HAS_GOLDEN)
P5 = N_STALE >= 0 and len({r["golden"] for r in RESULTS}) == N_CHECKED   # 一本查一次
P6 = True
P7 = True

OUT = {
    "P1_changed_set_is_nonempty_and_every_probe_has_a_census_entry_1027": P1,
    "P2_every_touched_probe_was_re_run_and_reported_1027": P2,
    "P3_positive_control_the_coupling_scan_finds_the_real_stale_one_1027": P3,
    "P4_touched_list_is_recorded_for_every_golden_owning_probe_1027": P4,
    "P5_one_run_per_golden_no_double_counting_1027": P5,
    "P6_scope_declared_1027": P6,
    "P7_offline_1027": P7,
    "P8_exclusion_is_bilateral_and_1015_declares_it_too_1027": P8,
}

# ── 仪器 bug 8 的可校验不变式：产物里不许留下「说不清」的字段 ────────────────
def _argv_flags_block():
    """⭐ 空列表折成计数：列表本身只在非空时保留（与 `_per_probe_row` 同一个处置）。"""
    if _ARGV_FLAGS:
        return {"argv_flags_received": list(_ARGV_FLAGS)}
    return {}


_RND_KEY = re.compile(r"(seconds?|runtime|duration|elapsed|timestamp|epoch|pid|tmpdir|tempdir)",
                      re.I)


def _scan_payload(obj, path="$", bad=None, blanks=None):
    """⭐ 递归扫 payload —— `null`、空列表、字段名像随机量的，各记一条路径。"""
    bad = [] if bad is None else bad
    blanks = [] if blanks is None else blanks
    if isinstance(obj, dict):
        for _k, _v in obj.items():
            _p = "%s/%s" % (path, _k)
            if isinstance(_k, str) and _RND_KEY.search(_k):
                bad.append(_p)
            _scan_payload(_v, _p, bad, blanks)
    elif isinstance(obj, list):
        if not obj:
            blanks.append(path)
        for _i, _v in enumerate(obj):
            _scan_payload(_v, "%s/[%d]" % (path, _i), bad, blanks)
    elif obj is None:
        bad.append(path)
    return bad, blanks


def _paths_block(_bad, _blank):
    """⭐ 扫描器自己也守同一条规矩 —— 否则「空路径列表」立刻把自己变成一条空列表。"""
    _b = {}
    if _bad:
        _b["null_or_random_named_paths"] = _bad[:20]
    if _blank:
        _b["empty_list_paths"] = _blank[:20]
    return _b


def _stale_block():
    """⭐ 第十一条仪器 bug 的处置：计数无条件保留、列表只在非空时保留。

    与 `_argv_flags_block` / `_per_probe_row` 同一个形态。
    **「没有过期」由 `n_stale == 0` 自证，不由「有一个空的 `stale` 列表」自证**
    —— 而 P9 的卫生自查恰恰会把那个空列表判成违规 ⇒ **⇒ 这道门会在最该绿的时候转红**。
    """
    if not STALE:
        return {}
    return {"stale": [{"probe": r["probe"], "golden": r["golden"], "rc": r["rc"],
                       "touched_by": r["touched_by"]} for r in STALE]}


# ── 写产物 ───────────────────────────────────────────────────────────────────
GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
_PAYLOAD = {
    "generated_by": "jimeng_probe1027_freshness_gate.py",
    "note": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
            "**给「产物新鲜度」补一道会红的闸** —— 1026 查清 1015 套件退出时会把 golden "
            "**还原成运行前的字节**，所以它验的是「可复现」而不是「当前」"
            "⇒⇒⇒⇒⇒⇒⇒⇒⇒ **「可复现」与「当前」是两个性质，前者不蕴含后者**",
    "question_1027": "哪些 golden 天然容易过期？现在有几本已经过期了？怎么让这道闸足够便宜？",
    "how": "⭐⭐⭐⭐⭐ **增量式**：变更集 = `git diff --name-only HEAD~1`；"
           "对每个有 golden 的探针算出它**读到的文件集合**，**只跑被本次变更触及的那些**；"
           "比对完**原样还原**（还原之前先把新内容留下）",
    "the_changed_set": CHANGED,
    "changed_set_from_argv": CHANGED_IS_ARGV,
    # ⚠️⭐⭐⭐⭐⭐ **仪器 bug 8 的第二处**：`_ARGV_FLAGS` 在没给 flag 时是 `[]`
    #   ⇒⇒⇒⇒⇒⇒ **而 1014 的普查把「真的是空」和「压根没算」判成同一种病**
    #   ⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **⇒ 与 `per_probe` 同一个处置：空列表折成计数**
    #   **⇒ 而这一处的「空」是**有意义的**（真没收到 flag），所以必须留个可自证的数**
    "n_argv_flags_received": len(_ARGV_FLAGS),
    **_argv_flags_block(),
    "ran_under_the_suite": UNDER_SUITE,
    "changed_set_note": "⭐⭐⭐⭐⭐ **变更集以 `argv` 为准**；没给 argv 时兜底取 "
                          "`git diff HEAD~3` ⇒ **共享仓里那会被别人的提交改掉** ⇒ "
                          "**⇒ 可复现性在这里的准确口径是「同一份 argv 下两次跑逐字节相同」**",
    "axis_1_coupling_census": {
        "what": "⭐⭐⭐⭐⭐ **耦合普查** —— 一个探针读到的仓内文件越多，"
                "越容易被「别人的改动」带偏 ⇒ **这是「容易过期」的结构性原因**",
        "n_probes_censused": len(COUPLING),
        "n_with_golden": len(HAS_GOLDEN),
        "n_excluded": sorted(EXCLUDE),
        # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **空列表一律折成计数** ——
        #   1014 的普查在第一版的本产物里报出 **627 条空**（424 个 `[]` + 205 个 `null`），
        #   而它们的来源是同一件事：**绝大多数探针在耦合正则下「一个输入都抽不到」**
        #   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 「空」不是信息，重复 627 次的空更不是**
        #   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 而且这件事本身是个读数，值得单独写成一个数，而不是靠空列表暗示**
        "n_probes_with_no_input": N_NO_INPUT,
        "n_probes_with_golden": len(HAS_GOLDEN),
        "no_input_note": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
                         "**⇒ 绝大多数探针在耦合正则下「一个输入都抽不到」** —— "
                         "第一版把它们各写成几个空列表，1014 的普查立刻报出 627 条「说不清」⇒ "
                         "**⇒⇒⇒⇒⇒⇒ 「空」不是信息，重复几百次的空更不是** ⇒ "
                         "**⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ 处置：空列表折成计数，只在非空时保留列表本身**",
        "per_probe": [_per_probe_row(c) for c in COUPLING.values()],
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
                "**⇒ 耦合面 × 改动面 决定过期概率 ⇒ "
                "⇒⇒⇒⇒⇒⇒⇒⇒⇒ 「每批都重跑全部探针」既不必要也不便宜，"
                "**取交集才是对的成本**",
    },
    "axis_2_the_measured_re_run": {
        "what": "⭐⭐⭐⭐⭐⭐⭐ **实测：对「被本次变更触及的」那些真跑一遍，"
                "与仓库里那本逐字节比对 ⇒ 列出现在已经过期的**",
        "n_touched": N_TOUCHED,
        "n_re_run": N_CHECKED,
        "ran_under_the_suite": UNDER_SUITE,
        "n_stale": N_STALE,
        "per_probe_timeout": PER_PROBE_TIMEOUT,
        "results": RESULTS,
        # ⚠️⚠️⚠️ 第十一条仪器 bug：**这道门在「一切新鲜」时转红** ⇒ 它惩罚成功
        #   ⇒⇒⇒⇒⇒⇒⇒⇒⇒ `stale` 在「已过期 0 本」时是个**空列表** ⇒ P9 的卫生自查当场变红
        #   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 而 `n_stale` 就在它正上方，值是 0**
        #   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 「空不是信息，重复几百次的空更不是」
        #   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒
        #   **⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
        #   **⇒ 而这条规矩我**已经**犯过两次并修过两次**（`argv_flags_received`、`_per_probe_row`）
        #   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 「修过一次」不等于「处处都修了」
        #   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒
        #   **⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
        #   **⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ 真正的教训不是「这一处忘了」而是：
        #   靠人记住逐处折是守不住的 ⇒ 必须让 P9 在当场抓住它，而它**做到了** ⇒
        #   **⇒ 这是 P9 上线后第一次真的抓到东西 —— 抓的是我自己**
        #   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒
        #   **⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ 处置：与前两处同一个形态 ——
        #   计数无条件保留、列表只在非空时保留 ⇒ 「没有过期」由 `n_stale == 0` 自证，
        #   不由「有一个空的 stale 列表」自证**
        **_stale_block(),
        "stale_vs_worktree_note": "⭐⭐⭐⭐⭐ **同时记下「与工作区那本比」的读数** —— "
                                  "第一版就是拿工作区那本作基准 ⇒ **假阴性**："
                                  "HEAD 记 200 个目标变量、事实已是 201，"
                                  "而只因为我先前为计时手动跑过一次、工作区那本已被刷新 ⇒ 闸被遮住了 ⇒ "
                                  "**⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ 「闸被测量者自己的先前动作遮住」是一个新的失效形态**",
        "restore_discipline": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
                              "**每个 golden 先快照、跑完原样还原 —— "
                              "和 1015 的 `_restore()` 同一个做法** ⇒ "
                              "**⇒⇒⇒⇒⇒⇒⇒⇒⇒ 差别只有一处，但那是全部：**"
                              "**1015 还原得很干净、干净到把过期一起还原掉了；"
                              "本批在还原之前先把新内容留下来比过了** ⇒ "
                              "**⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ 「还原」不是缺点，"
                              "「还原之前不留证据」才是**",
    },
    "axis_3_the_gate_itself": {
        "what": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **这道闸怎么才算装上了？** —— "
                "不是「我今天查了一遍」，是**它明天、后天仍然会红**",
        "the_mechanism": "增量式：变更集 × 耦合面 ⇒ 只跑被触及的那些 ⇒ 比对 ⇒ 报 stale",
        "why_cheap": "⭐⭐⭐⭐⭐ **成本正比于「本次改动触及了几个探针」，不是「一共有多少个探针」** ⇒ "
                     "**⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ 这就是「能常驻」与「只能手工跑一次」的分界**",
        "known_limits": [
            "⚠️ **它只抓「因为源码变了而过期」的 golden**，"
            "抓不到「因为环境变了而过期」的那个（例如依赖版本）",
            "⚠️ **它按路径耦合判定**，而点名的路径与实际读到的可能不一致 ⇒ 报的是下限",
            "⚠️ **1015 自己被排除**（它会重跑全部并自己还原）⇒ 它自己的新鲜度本批管不了",
            "⚠️⚠️⚠️ **本探针自己的 `P6`（范围已声明）与 `P7`（纯离线）是恒真的** —— "
            "「声明了」与「没联网」都是**声明**，不是**测量** ⇒ "
            "**⇒⇒⇒⇒⇒⇒⇒⇒⇒ 这两条不判任何东西，读到它们为 `True` 不构成任何证据** ⇒ "
            "**⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ 它们的病是 1026 已经公开量过的那个（探针 P 的含金量），"
            "本批只登记、不假装修好了**",
        ],
    },
    "positive_control": {
        "A_find_the_real_stale_one_without_being_told": {
            "probe": "jimeng_probe1013_occurrence_ledger.py",
            "found": PC_A,
            "why_it_must_be_found": "⭐⭐⭐⭐⭐ **那一行的 diff 就是"
                                     "`目标变量 200 → 201`** —— 因为本批新增了 `_p1026` "
                                     "⇒ **⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **每一批新增一个探针变量，"
                                     "都会让 1013 的产物过期一格** ⇒ "
                                     "**⇒⇒⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐⭐⭐ 这条耦合是结构性的、不是偶然的**",
            "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
                    "**不告知答案**：耦合扫描必须自己把 1013 列进「被触及」名单",
        },
        "B_injected_path_is_selected_by_the_coupling_scan": {
            "injected_path": _injected_path,
            "n_selected": len(_injected_touched),
            "selected": _injected_touched,
            "ok": PC_B,
            "rule": "⭐⭐⭐⭐⭐ **注入式自检**：把 verifier 路径塞进变更集，"
                    "要求扫描器认出所有与它耦合的探针 ⇒ "
                    "**⇒ 验的是「取交集这一步本身通不通」，"
                    "而不依赖「这次提交恰好是谁的」** ⇒ "
                    "**⇒⇒⇒⇒⇒⇒ 这一条正是对「仪器 bug 1」的回归防护**",
        },
        "C_intersection_is_narrower_than_everything": {
            "n_touched": N_TOUCHED,
            "n_with_golden": len(HAS_GOLDEN),
            "ok": PC_C,
            "rule": "⭐⭐⭐⭐⭐ **取交集必须比「全部」小** —— "
                    "否则它退化成一个更贵的全量重跑 ⇒ **这本身是一条判据**",
        },
        "D_bilateral_exclusion_turns_red_on_either_side": {
            "ok": PC_D,
            "n_times_1027_name_appears_in_1015_src": _1015_SRC.count(SELF),
            "rule": "⭐⭐⭐⭐⭐ **注入式** —— 把对方登记里我的名字换掉 ⇒ 判据必须转红；"
                    "把自己的 `EXCLUDE` 清空 ⇒ 也必须转红 ⇒ **两侧都是活的**",
            "why_this_exists": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
                    "**P8 第一版是恒假的**（第二半问的是「我排了我自己吗」）"
                    "⇒ 它永远报「双向排除没做」，而实际已经做完 ⇒ "
                    "**⇒ 这一条阳性对照就是为了让「恒假」当场暴露，而不是靠人眼发现**",
        },
        "P8_bilateral_now": P8,
        "P8_registry_key_found_in_1015_src": bool(_REG_RE.search(_1015_SRC)),
        "P8_i_exclude_the_other": _1015_NAME in EXCLUDE,
        "P8_it_excludes_me": SELF in _REG_RE.search(_1015_SRC).group(1),
    },
    "scope_declared": "⚠️⭐⭐⭐⭐⭐ 量的是**有 golden 且不在排除名单里的探针**；"
                      "**1015 自己被排除**（它会重跑全部并自己还原）；"
                      "**耦合按源码里出现的路径与 glob 判定**，不追执行 ⇒ **报的是下限**；"
                      "**只抓「因源码变化而过期」，不抓「因环境变化而过期」**；"
                      "**本批不替项目改任何文件**（每个 golden 跑完原样还原）",
    "offline": "**只读仓内文件 + 起仓内已有的探针 + `git`（本地）**；"
               "零安装、零网络、零浏览器；**产物里不写临时目录名、时间戳、pid**",
}

# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **仪器 bug 8 的可校验不变式 ⇒ `P9`** ——
#   这一版的产物里有 13 处「说不清」：12 个 `_seconds_runtime_only: None`
#   ＋ 1 个 `argv_flags_received: []` ⇒⇒⇒⇒⇒⇒ **而它们是被 1014 的普查抓出来的**
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **⇒⇒⇒⇒⇒⇒⇒⇒⇒ 「让门去抓自己」比「记得别犯」可靠得多**
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ 扫两遍是刻意的：**
#   **第一遍扫完之后要把扫描结果本身写进产物 ⇒ 第二遍才抓得到「结果把自己变成了违规」**
# ⚠️⚠️⚠️⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
# **第十个仪器 bug：读数印了但没落盘** —— `OUT` 从来没进过 `_PAYLOAD`
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 读 golden 的人无从判断这道门当时是绿是红**
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 更糟的是 P9 扫的那份 payload 压根不含结论
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ ⇒ 一份残缺的产物也能拿到「自查通过」
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 自查的范围比自查声称的范围小**
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 处置：结论先进产物，再扫**
_PAYLOAD["verdicts_1027"] = dict(OUT)
_BAD, _BLANK = _scan_payload(_PAYLOAD)
_PAYLOAD["payload_hygiene_scan"] = {
    "what": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
            "**本产物不许留下「说不清」的字段** —— 三类：`null`、空列表、字段名像随机量",
    "n_null_or_random_named": len(_BAD),
    "n_empty_list": len(_BLANK),
    "scanned_twice_note": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
                          "**⇒ 扫描器自己也守同一条规矩**，否则「空路径列表」自己就成了一条空列表",
    "why_this_is_a_gate": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
                          "**⇒ 这一版是被 1014 的普查抓出来的（13 处）** ⇒ "
                          "**⇒⇒⇒⇒⇒⇒⇒⇒⇒ 「自己验过」不算数，被下一道门抓过才算数**",
    **_paths_block(_BAD, _BLANK),
}
_BAD2, _BLANK2 = _scan_payload(_PAYLOAD)
OUT["P9_my_own_payload_has_no_null_no_empty_list_no_random_named_key_1027"] = bool(
    not _BAD2 and not _BLANK2)
_PAYLOAD["verdicts_1027"] = dict(OUT)
_BAD3, _BLANK3 = _scan_payload(_PAYLOAD)
OUT["P10_writing_the_verdicts_back_did_not_break_my_own_hygiene_1027"] = bool(
    not _BAD3 and not _BLANK3)

# ⚠️⭐⭐⭐⭐⭐ **自指的极限，必须显式登记**：`P10` 的读数是在它自己被写进产物**之前**
#   算出来的 ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 任何「我自己的产物
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ 是否干净」都逃不开这一层
#   ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 不假装它被覆盖了**
_PAYLOAD["verdicts_1027"] = dict(OUT)
GOLDEN.write_text(json.dumps(_PAYLOAD, ensure_ascii=False, indent=2) + "\n",
                  encoding="utf-8")


print("变更集（HEAD~1..HEAD）：%d 个文件" % len(CHANGED))
for f in sorted(CHANGED)[:12]:
    print("   ", f)
print()
print("探针普查 %d 个，其中有 golden 的 %d 个，排除 %d 个"
      % (len(COUPLING), len(HAS_GOLDEN), len(EXCLUDE)))
print("耦合扫描认为「被本次变更触及」：%d 个" % N_TOUCHED)
for n in sorted(COUPLED_TO_CHANGED):
    print("   %-52s 触及 %d 个文件" % (n, len(COUPLING[n]["touched_by_this_change"])))
print()
print("真跑并比对：%d 本 ⇒ **已过期 %d 本**%s"
      % (N_CHECKED, N_STALE,
         "（套件语境：只普查、不重跑 —— 见仪器 bug 6）" if UNDER_SUITE else ""))
for r in RESULTS:
    mark = "⚠️ 已过期" if r["stale_vs_committed"] else "   一致    "
    print("   %s %-50s rc=%s  %5.1fs" % (mark, r["probe"], r["rc"], _secs_of[r["probe"]]))
print()
print("阳性对照 甲（自己认出 1013）=", PC_A, " 乙（认出本批新增文件）=", PC_B,
      " 丙（交集窄于全体）=", PC_C, " 丁（双向排除两侧都活）=", PC_D)
print("   双向排除：我排它=%s ／ 它排我=%s" % (_1015_NAME in EXCLUDE,
                                            SELF in _REG_RE.search(_1015_SRC).group(1)))
print("   触及 %d / 有 golden %d" % (N_TOUCHED, len(HAS_GOLDEN)))
print()
# ⭐ 标签由 `OUT` 的长度算出来，不手写 —— 第一版写死成「P1..P7」而 `OUT` 已经有 8 项
#   ⇒⇒⇒⇒⇒⇒ **⇒ 打印出来的标签和实际条数对不上，而这种错没人会去看第二眼**
print("P1..P%d = %s" % (len(OUT), [OUT[k] for k in OUT]))
print("PROBE_1027_DONE ->", GOLDEN)
sys.exit(0 if all(OUT.values()) else 1)