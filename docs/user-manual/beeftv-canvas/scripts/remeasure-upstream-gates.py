#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Batch 331：把「哪些闸真读上游」从一张手工标记表改成一次**实测**，并定期重测。

## 这份工具治的是什么病（纪律 364 + 365 的联合产物）

`verify-upgrade-drift.py` 原本靠 `UPSTREAM_MARKERS` 一张**手工痕迹清单**扫闸。
Batch 329 实测它**漏了 `module_ref(`**（写法演化）→ 少扫 4 道；
Batch 330 又实测出**它至少多算 2 道**（`verify-meta` / `verify-baseline`
自身不读上游 ref，只是源码里出现了 `git_grep` / `beefsrc` / `resolve_ref` 这些**字样**），
**而本闸自己也被算进去**（源码里那句 `print()` 提到了那个变量名），
以及**它结构上抓不到 1 道**（`verify-empty-tree` 靠跑别的闸**间接**依赖 ref，源码里没有任何痕迹）。

**而「一道闸读的是不是上游那个 ref、能不能被 `BEEFTV_REF` 控制」，
是运行时的事实，不是源码里有什么字面量。**

## 判据：哨兵 ref（Batch 330 立的量法）

设一个**不存在的 ref**：
  · **真读那个 ref、且受 `BEEFTV_REF` 控制**的闸 → 必须表现为「读不到」→ **rc 变**（正常是 2）；
  · **不读、或读法不受它控制**的闸 → **rc 必须不变**。

**而本工具只报「rc 变了」这一侧，不报「rc 没变」那一侧**——
因为「rc 没变」有两种完全不同的成因：
  ① 它真的不读上游；
  ② 它读了、然后**静默降级**成 rc=0（**那种闸平时绿、真上游坏了也绿**，是本项目最危险的一类）。
**这两种在 rc 上分不出来，所以这一侧必须逐条定性，而工具不替它猜**（纪律 364⑥）。

## 为什么落盘、而不是每次现场跑

44 道闸各跑两遍，最坏 30 分钟——**不能进构建**。
所以：**重测是本工具的活，比对才是闸的活**
（与 `remeasure-gate-registry.py` / 闸 44 同一套分工，纪律 356）。

**而这份矩阵会过期——Batch 330 已经演示过一次**：
它是在 `resolve_ref()` 加上存在性校验**之前**跑的，
修完之后 `verify-exclusions` 与 `verify-shot-version` 从「rc 不变」变成了 **rc=2**。
**所以「谁在什么时候跑的」必须记进落盘文件**，
**而任何拿它当现状的东西，都得先看那个时间戳。**
**指纹表（`fingerprints`）就是那个时间戳的机器可读形态**——
闸 45 逐个核它，**任何一个闸在实测之后被改过就报 rc=2**。

## 三条「量之前先问」的规矩（纪律 367，三条都是本批撞出来的）

**① 判据要的键，产出它的工具必须真的写。**
本工具**第一版没写 `fingerprints`**，而闸 45 要求它
（那是「矩阵过期了没有」的锚点）——于是闸 45 恒 rc=2。
**那不是闸坏了，是闸在正确工作**：矩阵缺新鲜度锚点，本轮就核不了。
**两处对不上的时候，先怀疑产出那一侧，而不是把判据放宽。**

**② 在红基线上量出来的东西不是证据。**
本工具**第一版是在脏工作区跑的**（同事有未提交的 WIP），
四道闸的「正常」那一遍已经是 rc=1，于是量出 `1 → 1`。
**而 rc 相同有两种成因**（纪律 365：真不读 / 读了但静默降级），
**红基线把两种成因搅成一种**——那种行连「证明不了任何事」都算不上，
**它会被下游当成证据**。
所以：正常那一遍非 0 的行一律标 `unusable`、**排除出证据**，
而闸 45 见到 unusable 行**报 rc=2**（**证据不完整 ≠ 没发现问题**，纪律 101 同款）。
**处置是在一棵全绿的树里重测**——本批就是这么做的（副本树）。
**顺带一条现实约束**：这份实测**依赖手册树的内容**（闸读的是手册文件），
**所以在有他人未提交 WIP 的工作区里量出来的矩阵，别人根本复现不出来**。

**⑤「过期了没有」要按「变化能从哪些地方传进来」列全，而四条一起上（纪律 368）**：
原先只逐行记闸自己源码的 sha256，**于是改手册正文不会让矩阵过期**——
**而闸读的就是手册正文**（闸 1 / 2 / 6 / 9 / 22 / 23 … 全都读它），
**改一行正文就可能改掉某道闸的 rc，而它自己的文件一个字节没动**。
所以现在多落两类摘要：`tree_digest`（手册内容）与 `shared_digest`
（`scripts/` 下**除闸自己与这份矩阵之外的一切**——
**共享实现、反验、夹具、其它工具全在里面，而闸 18 在构建里真跑每一份反验**）。
**实测两份摘要各 0.07 秒 / 0.02 秒，所以闸每次跑都算得起。**
**而这一刀也顺带给出了复用规则**：三个条件同时成立才复用一行
（闸自己指纹没变 + 两份摘要都没变），
**于是「加一道闸」「改一道闸」不必全量重测，而「改手册正文」必须全量——不是嫌慢，是那条路上复用就是撒谎。**

**⓪而「全绿」这个前提自己也有前置条件（本批第三次重测才撞上，纪律 367⑦）**：
`verify-deadlinks.py`（闸 1）与 `verify-screenshots.py`（闸 2）**读的是 `dist/`**，
而 dist 不在时它们**返回 rc=2「跳过」**——
**rc=2 不是 0，于是在一棵「干净但没构建过」的树里，整份实测作废**。
**处置：先 `npx vitepress build` 把站点建出来，再量。**
**不要改成跑 `build-site.sh`**——那一遍会顺带跑闸，
而闸 45 读的正是即将被重测掉的那份矩阵，**它必然报红**。

**③ 判据读的那份实测，不能被它自己量。**
`verify-upstream-gates.py`（闸 45）读的**就是**本工具的输出，
量它等于让它读一份**写到一半**的文件——
第一版就是这么记下一条 `2 → 2` 的坏行，**而坏行会一直躺在落盘文件里骗人**。
所以它自己**不在测量范围里**，闸 45 发现自己不在矩阵里时会**明说**（不判红）。
**「测哪些闸」这个枚举只写一份**（`measured_gates()`，闸 45 用 importlib 调它）——
**同一个概念两份实现，迟早会有一份过期，而过期的正是没人重测的那份**（纪律 355）。
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time

MAN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SD = os.path.join(MAN, "scripts")
OUT = os.path.join(SD, "upstream-gates-sentinel.json")
SENTINEL = "zzz-not-a-real-ref-9f3a"
# **漂移参照**：一个**真实存在**、但内容与基线不同的 ref。
# **它的作用是把「两次 rc 相同」这一侧拆开**（纪律 364⑥ 一直说这一侧不作数）：
#   · 哨兵 rc 变了 → **真读，且读不到时会响**；
#   · 哨兵 rc 没变、而漂移 ref 下 rc 变了 → **它读到了真实漂移，却在「读不到」时沉默**
#     ← **这就是本项目反复说「最危险」的那一类，而它此前只有名字、没有名单**；
#   · 两边都没变 → **没有反应**（注意：这**推不出「它不读」**，见下面那句）
DRIFT_REF = "origin/main"
TIMEOUT = 300

# 下面两个**不被测量**，理由不同，所以分开写——
# **分开写不是讲究，是它们各自都会让人上钩**（纪律 367③）
NOT_MEASURED = (
    # 它是**痕迹清单的来源**，不是被核对的对象：自己核自己没有意义
    "verify-upgrade-drift.py",
    # 它是本实测的**消费者**：量它等于让它读一份写到一半的矩阵
    "verify-upstream-gates.py",
)


def measured_gates(sd=None):
    """本工具测哪些闸——**闸 45 用 importlib 调的就是这一个函数**，
    所以「覆盖检查」不会因为两处各写一遍排除名单而对不上（纪律 355）。"""
    sd = sd or SD
    return sorted(n for n in os.listdir(sd)
                  if n.startswith("verify-") and n.endswith(".py")
                  and n not in NOT_MEASURED
                  and n != os.path.basename(__file__))


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


# 摘要要略过的目录：**产物与依赖**（它们不是「这棵树的一部分」，
# 而闸 1 / 闸 2 恰恰要读 `dist/`——**所以 dist 不进摘要，闸 2 的结论就不受构建产物影响**）
SKIP_DIRS = {".git", "node_modules", "dist", "__pycache__", ".vitepress"}

# **「这棵树」这个集合本身也要挑，而这一条是实测出来的**（纪律 368⑦）：
# 副本树 113 个内容文件、仓库 114 个，**差的那一个是 `screenshots/.DS_Store`**——
# **它是 macOS Finder 写的、git 不跟踪、而「在 Finder 里点过这个目录」就会变**。
# **所以它进了 `tree_digest` 的话，那道判据的红与「谁碰过这个文件夹」绑定**——
# **而一个天天因为环境噪声红的守卫，等于没有守卫**（纪律 156 的变体：
# 一个恒红的判据会被人当成环境问题绕过去）。
# **为什么是列文件名而不是「问 git 要跟踪列表」**：副本树把 `.git` 软链到真仓库，
# **`git ls-files` 在那里会列出真仓库的文件（而它们在副本树里并不存在）**——
# **实测出来的，不是想出来的。**
# **而这份名单漏了一种噪声的失效方向是「响」不是「静」**：新噪声进来 → 摘要变 → rc=2，
# **它不会让一道真不一致溜过去**，所以名单不全的代价是「偶尔白跑一次重测」。
NOISE_FILES = {".DS_Store", "Thumbs.db", "desktop.ini", ".Spotlight-V100"}

SELF_NAME = os.path.basename(__file__)
MATRIX_NAME = os.path.basename(OUT)


def _digest_of_files(pairs):
    """对一组 `(相对路径, 绝对路径)` 求摘要——**路径也进哈希**，
    因为「同一个文件换了名」与「文件没变」在内容摘要上长得一样。"""
    h = hashlib.sha256()
    for rel, path in pairs:
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(sha256_of(path).encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()


def content_files(root=None):
    """手册**内容**文件（不含 `scripts/`、不含产物与依赖）。
    **默认参数是必须的**：`main()` 要打印「这份摘要覆盖了几个文件」，
    而第一版把它写成必填 —— 于是**一跑就 TypeError**（Batch 332 实测，
    **而且是副本树里那遍才暴露出来**：真树上我先跑的是 `tree_digest()`，没走 `main()`）。"""
    root = root or MAN
    out = []
    for r, ds, fs in os.walk(root):
        ds[:] = sorted(d for d in ds if d not in SKIP_DIRS)
        rel_dir = os.path.relpath(r, root)
        if rel_dir == ".":
            rel_dir = ""
        if rel_dir.split(os.sep)[0] == "scripts":
            continue
        for f in sorted(fs):
            if f.endswith(".pyc") or f in NOISE_FILES or f.startswith("._"):
                continue
            p = os.path.join(r, f)
            out.append((os.path.join(rel_dir, f).replace(os.sep, "/"), p))
    return sorted(out)


def tree_digest(root=None):
    """手册内容的摘要——**「这份实测是在哪棵内容树上量的」**（纪律 367⑥）。
    实测 114 个文件 / 15.8 MB，**0.07 秒**，所以闸每次跑都算得起。"""
    return _digest_of_files(content_files(root or MAN))


def shared_digest(sd=None):
    """`scripts/` 下**除闸自己与这份矩阵之外**的一切文件的摘要。

    **为什么是「除闸自己与这份矩阵之外的一切」**（纪律 368）：
    **判据的「过期了没有」必须按「变化能从哪些地方传进来」列全**，而实测列出来是四条：
      ① **闸自己的源码** → 逐行记 sha256（`fingerprints`）；
      ② **共享实现**（`baseline.py` / `headingkey.py` / `scope.py` …）——
         改一个 `resolve_ref()`，**所有**闸的读法都变了，而它们自己的文件一个字节没动；
      ③ **反验与夹具**（`selftest-*.py` / `selftest-fix-*.py` / `*.sh`）——
         **闸 18 在构建里真跑每一份**，改一份就改闸 18 的 rc；
      ④ **手册内容**（`tree_digest`）——闸读的就是那些 `.md` 与截图。
    **而「除闸自己与这份矩阵之外的一切」这一刀，正好把 ②③ 一次性圈住**：
    **列全的代价是零，漏一条的代价是「拿旧数据冒充新数据」**。
    **矩阵自己必须排除**——它进自己的摘要就是自指。
    """
    sd = sd or SD
    out = []
    for n in sorted(os.listdir(sd)):
        if n == MATRIX_NAME or not os.path.isfile(os.path.join(sd, n)):
            continue
        if n.startswith("verify-") and n.endswith(".py"):
            continue  # ① 逐行 sha256 已覆盖
        out.append(("scripts/" + n, os.path.join(sd, n)))
    return _digest_of_files(out), [r for r, _ in out]


def ref_exists(ref):
    """漂移参照**必须真的存在**——**它不存在的话，26 道闸会一起 rc=2，
    而那一列会被误读成「26 道都在对「读不到」沉默」**，那是最坏的一种假红。
    **所以先问它存不存在，问不到就不跑第三遍**（纪律 330 的同款处置）。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("bl_probe", os.path.join(SD, "baseline.py"))
    m = importlib.util.module_from_spec(spec)
    # **必须先把 `scripts/` 挂进 `sys.path`**——`baseline.py` 里有 `import beefsrc`，
    # **而它那个 import 是同层相对导入**（纪律 226 那个坑：importlib 单独 exec 一个文件
    # 不会把它的兄弟模块放进搜索路径）。第一版就栽在这里，症状是
    # 「一跑就 ModuleNotFoundError: beefsrc」，而报错信息里完全没有线索指向真正的处置。
    sys.path.insert(0, SD)
    try:
        spec.loader.exec_module(m)
        return bool(m.commit_exists(ref))
    except Exception:  # noqa: BLE001
        return False
    finally:
        sys.path.remove(SD)


def classify(row, drift_ok):
    """把一行归到三类之一。**而第三类必须写成「没有反应」而不是「真不读」**——
    「两次都绿」推不出「它不读」（纪律 365⑦ 的原话：也可能是读了但比的东西与 ref 无关）。"""
    if row.get("changed"):
        return "A 真读且响（哨兵下 rc 变）"
    if not drift_ok:
        return "— 未测（漂移参照不存在）"
    if (row.get("drift") or {}).get("rc") not in (0, None):
        return "B 未变但对真实漂移有反应 ← **读到了却在「读不到」时沉默**"
    return "C 未变且对真实漂移无反应（**这推不出「它不读**」）"


def run(name, env_ref):
    env = dict(os.environ)
    if env_ref is None:
        env.pop("BEEFTV_REF", None)
    else:
        env["BEEFTV_REF"] = env_ref
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, os.path.join(SD, name)],
                           cwd=MAN, env=env, capture_output=True, text=True,
                           timeout=TIMEOUT)
        return {"rc": p.returncode,
                "tail": (p.stdout or p.stderr).strip().split("\n")[-1:],
                "sec": round(time.time() - t0, 1)}
    except subprocess.TimeoutExpired:
        return {"rc": None, "tail": ["<timeout>"], "sec": TIMEOUT}


def main(argv=None):
    """**这里曾经有一段「按文件粒度复用没变过的行」的逻辑，Batch 333 把它撤掉了。**

    **它撤掉的理由是可注入证明的**（纪律 369）：
    复用条件是「这一行自己的闸源码没变 + 两类摘要没变」，
    **而实测证明闸与闸之间有依赖**——只把 `verify-tables.py` docstring 的
    「第八道闸」改成「第九道闸」（**只改那一行**），**闸 9 `verify-meta` 就从 rc=0 变成 rc=1**
    （它核「闸脚本自称与真实闸号一致」，**而它读的是别的闸的源码**）。
    **于是在那个规则下，闸 9 那一行会被原样留下——记着「正常那一遍 rc=0」，
    而实际已经是 rc=1**：**一行「看着是实测、其实是过期」的数据，
    而且它的失效形态正是本项目最怕的那一类：不是报错，是照旧参与判断。**
    **而 `scripts/` 下的闸文件若并进共享摘要，复用就永远不成立**
    （任何一道闸的改动都会让全部行作废）——**所以那不是「复用」，那是「一个永远不触发的分支」**。
    **结论：这份实测只能全量重测（355 秒），而这条结论是被注入量出来的，不是想出来的。**
    """
    names = measured_gates()
    td = tree_digest()
    sh, shared_names = shared_digest()
    drift_ok = ref_exists(DRIFT_REF)
    print("哨兵 ref = %s（不存在，用来抓「读不到」）" % SENTINEL)
    print("漂移参照 = %s（%s，用来抓「读到了却对读不到沉默」）"
          % (DRIFT_REF, "存在" if drift_ok else "**不存在 → 第三遍不跑**"))
    print("内容摘要 = %s…（%d 个文件）" % (td[:16], len(content_files())))
    print("共享摘要 = %s…（%d 个文件）" % (sh[:16], len(shared_names)))
    print("逐道实测 %d 道闸（各两遍，最坏 %d 秒/遍）\n" % (len(names), TIMEOUT))
    rows = []
    for i, name in enumerate(names, 1):
        a = run(name, None)
        b = run(name, SENTINEL)
        row = {"gate": name, "normal": a, "sentinel": b,
               "changed": a["rc"] != b["rc"], "unusable": None,
               "measured_at": time.strftime("%Y-%m-%d %H:%M:%S")}
        if a["rc"] != 0:
            # **红基线上的行不是证据**（纪律 367②）：两种成因被搅成一种
            row["unusable"] = "正常那一遍 rc=%s（**在红基线上量的行证明不了任何事**）" % a["rc"]
            row["changed"] = None
        elif drift_ok and not row["changed"]:
            # **只给「哨兵下没变」的那些加第三遍**——实测这 26 道合计 68 秒，
            # **而闸 18（242 秒）恰好在「变了」那一侧**，所以这一遍几乎不要钱
            row["drift"] = run(name, DRIFT_REF)
        row["class"] = classify(row, drift_ok)
        rows.append(row)
        if row["unusable"]:
            mark = "**作废（红基线）**"
        elif row["changed"]:
            mark = "变了"
        else:
            mark = "**%s**" % row["class"].split("（")[0]
            if "drift" in row:
                mark += "（漂移 rc=%s）" % row["drift"]["rc"]
        print("[%2d/%2d] %-34s 正常 rc=%-4s → 哨兵 rc=%-4s %s"
              % (i, len(names), name, row["normal"]["rc"], row["sentinel"]["rc"], mark))
        sys.stdout.flush()
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump({"measured_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                       "sentinel": SENTINEL, "rows": rows,
                       "tree_digest": td, "shared_digest": sh,
                       "fingerprints": {r["gate"]: sha256_of(os.path.join(SD, r["gate"]))
                                        for r in rows}},
                      fh, ensure_ascii=False, indent=1)

    usable = [r for r in rows if not r["unusable"]]
    changed = [r["gate"] for r in usable if r["changed"]]
    to2 = [r["gate"] for r in usable if r["sentinel"]["rc"] == 2]
    bad = [r for r in rows if r["unusable"]]
    print("\n==== 汇总 ====")
    print("共 %d 道：**%d 道 rc 变了**（其中 %d 道变为 2）"
          % (len(rows), len(changed), len(to2)))
    print("**这一侧是「真读了那个 ref」的证据**；")
    print("**「rc 没变」这一侧不作数**——它可能是「不读」，也可能是「读了然后静默降级」，")
    print("**而本工具不替它猜**（逐道分类仍然是人的活，纪律 364⑥）。")
    if bad:
        print("\n✗ **本次实测不构成证据：有 %d 道是在红基线上量的**" % len(bad))
        for r in bad:
            print("     · %s —— %s" % (r["gate"], r["unusable"]))
        print("   处置是**在一棵全绿的树里重跑本工具**（本批用副本树），")
        print("   **不是把那些行删掉**——删掉就是在假装那几道量过了。")
    else:
        print("全部 %d 行的正常基线都是 rc=0，**没有一行作废**。" % len(rows))
    buckets = {}
    for r in usable:
        buckets.setdefault(r["class"], []).append(r["gate"])
    print("\n---- 三分类（纪律 364⑥ 那一侧从「不作数」变成有数）----")
    for k in sorted(buckets):
        print("  %-46s %2d 道" % (k, len(buckets[k])))
    if buckets.get("B 未变但对真实漂移有反应 ← **读到了却在「读不到」时沉默**"):
        print("  → B 类是**本项目最坏的一类**（平时绿、真上游坏了也绿），闸 45 对它判红")
    print("落盘：%s（%d 个指纹 / 内容摘要 %s… / 共享摘要 %s…）"
          % (OUT, len(names), td[:12], sh[:12]))
    return 1 if bad else 0


# ── Batch 337：落盘矩阵的形状核对搬进本工具 ────────────────────────────
# **为什么搬**（纪律 371 的第二次应验）：那段核对原先只活在 `/tmp` 的绿构建 wrapper 里，
# **十一句判据里有两处硬编码**——「45 行 / 45 指纹」与「18 道真读」。
# **实测代价就是本批自己付的**：Batch 336 加了闸 46，矩阵变成 45 行，
# **wrapper 仍写着 44 → 绿构建跑到第 11 分钟才报「覆盖不是 44/44」**。
# **而 `/tmp` 会被清理、下一个批次不会去看上一批的 wrapper**（纪律 156 的同型）。
#
# **搬进来之后，那两处硬编码一个都不需要了**：
#   · 行数用 `measured_gates()` **当场自算**——而它本来就是枚举闸的唯一事实源
#     （纪律 355：枚举只写一份，闸 45 也是 importlib 调它）；
#   · A 类数改成**从 `20-reference.md` 现场抽那个数再与矩阵比对**，
#     于是「参考页写死的 18」从一个「每批要记得手改的数」变成**机械可核的登记**。
#     **而这一条比原来那条更强**：原来只核「A == 18」，现在核的是
#     **「参考页说的 A 与这次实测的 A 是同一个数」**——**参考页改错了也报**。
REF_A_RE = re.compile(r"A\s*(\d+)\s*道")
#: 闸 45 自己——**矩阵里量它就是自指**（纪律 367③：判据读的那份实测不能被它自己量）。
SELF_GATE = "verify-upstream-gates.py"


def verify_shape(data, expect_rows, ref_a, path="<夹具>"):
    """核落盘矩阵的形状。**返回问题列表，空列表即相符**。

    **刻意做成纯函数**（`data` / 期望值都从外面进）：这样自检探针能造一份
    **夹具**去测它，而不必去改真实矩阵——**探针与判据共用一段拼装逻辑的话，
    那不叫独立**（Batch 335 记过「判据对、样本错」那类坑）。

    `expect_rows` 由调用方用 `measured_gates()` 当场算，`ref_a` 由调用方从参考页抽；
    **本函数自己一个数都不硬编码**。
    """
    problems = []
    if not isinstance(data, dict) or not isinstance(data.get("rows"), list):
        return ["矩阵结构读不出来（`rows` 不是列表）"]
    rows, fps = data["rows"], data.get("fingerprints")
    if not isinstance(fps, dict):
        return ["矩阵缺 `fingerprints` 或它不是字典"]

    bad = [r.get("gate") for r in rows if r.get("unusable")]
    if bad:
        problems.append("有作废行：%s" % bad)
    if not (len(rows) == len(fps) == expect_rows):
        problems.append("覆盖不是 %d/%d —— 实测 %d 行 / %d 个指纹，而 `%s` 下的闸是 %d 道"
                        % (expect_rows, expect_rows, len(rows), len(fps),
                           os.path.basename(SD), expect_rows))
    if SELF_GATE in {r.get("gate") for r in rows}:
        problems.append("矩阵里量了闸 45 自己（自指，纪律 367③）")
    missing_class = [r.get("gate") for r in rows if not r.get("class")]
    if missing_class:
        problems.append("有行没有 `class` —— 三分类（纪律 370）少了一类：%s" % missing_class)
    missing_ts = [r.get("gate") for r in rows if not r.get("measured_at")]
    if missing_ts:
        problems.append("有行没有自己的 `measured_at`（纪律 368④）：%s" % missing_ts)

    a_cnt = len([r for r in rows if r.get("changed") is True])
    b_cnt = len([r for r in rows if str(r.get("class", "")).startswith("B")])
    c_cnt = len(rows) - a_cnt - b_cnt
    if a_cnt + b_cnt + c_cnt != len(rows):
        problems.append("三分类之和 %d ≠ 行数 %d" % (a_cnt + b_cnt + c_cnt, len(rows)))
    if b_cnt:
        problems.append("B 类（读到却在读不到时沉默）%d 道 —— 闸 45 会判红，不猜" % b_cnt)
    #: **A 类数与参考页现场抽出来的那个数必须相等**——**这一条替代了原先硬写的 18**。
    if a_cnt != ref_a:
        problems.append("实测 A 类 %d 道，而参考页写的是 A %d 道 —— "
                        "**这两处必须同时改**（改一个不改另一个，读者看到的与实测就对不上）"
                        % (a_cnt, ref_a))
    for k in ("tree_digest", "shared_digest"):
        if not data.get(k):
            problems.append("矩阵缺 `%s` —— 纪律 368 的三类 freshness 少了一类" % k)
    #: **纪律 369**：复用分支已撤掉，落盘里也就不该再有 `mode` / `reused`——
    #: **留着它们等于宣称「这份矩阵是增量更新过的」，而那份文件再没有那种逻辑了**。
    for k in ("mode", "reused"):
        if k in data:
            problems.append("矩阵里还有 `%s` 字段 —— 复用逻辑已撤掉（纪律 369），这是残留" % k)
    return problems


def _self_test():
    """自检：正反两支。**反验是本工具的一部分**（纪律 350：判别式没被样本验过就只是写法）。"""
    good = {"rows": [{"gate": "a.py", "changed": True, "class": "A", "measured_at": "t"},
                     {"gate": "b.py", "changed": False, "class": "C", "measured_at": "t"}],
            "fingerprints": {"a.py": "x", "b.py": "y"},
            "tree_digest": "d", "shared_digest": "s"}
    p = verify_shape(good, 2, 1, "正向")
    if p:
        print("  ✗ 自检：一份自洽夹具被判为 %s —— **判据比声称的严**" % p)
        return 1
    print("  ok   自检：一份自洽夹具通过（2 行 / A 1 道）")
    # 反向 ①：A 类数与参考页对不上（**这正是原先那处硬编码 18 要抓的东西**）
    p = verify_shape(good, 2, 18, "反向")
    if not any("参考页写的是 A 18" in x for x in p):
        print("  ✗ 自检：A 类数与参考页不符却没报 —— **判据在这条上不成立**")
        return 1
    print("  ok   自检：A 类数与参考页不符必报（反向探针命中）")
    # 反向 ②：行数少一行
    p = verify_shape(good, 3, 1, "反向")
    if not any("覆盖不是" in x for x in p):
        print("  ✗ 自检：覆盖不足却没报")
        return 1
    # 反向 ③：量了闸 45 自己
    bad = dict(good, rows=good["rows"] + [{"gate": SELF_GATE, "changed": False,
                                           "class": "C", "measured_at": "t"}],
               fingerprints=dict(good["fingerprints"], **{SELF_GATE: "z"}))
    p = verify_shape(bad, 3, 1, "反向")
    if not any("自指" in x for x in p):
        print("  ✗ 自检：量了闸 45 自己却没报")
        return 1
    print("  ok   自检：覆盖不足 / 自指 / A 类数不符，三支反向探针全命中")
    return 0


def verify(path=None):
    """`--verify`：读落盘矩阵核形状。**rc 三段**：0 相符 / 1 不符 / 2 未能核对。"""
    path = path or OUT
    if _self_test():
        print("[skip] 自检没过，判据自身不可用，本轮未能核对")
        return 2
    if not os.path.exists(path):
        print("[skip] 读不到矩阵 %s —— 没量过不等于形状对" % path)
        return 2
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        print("[skip] 矩阵读不出来（%s），本轮未能核对" % exc)
        return 2
    ref = os.path.join(os.path.dirname(SD), "20-reference.md")
    try:
        with open(ref, encoding="utf-8") as fh:
            m = REF_A_RE.search(fh.read())
    except OSError as exc:
        print("[skip] 读不到参考页 %s（%s），本轮未能核对" % (ref, exc))
        return 2
    if not m:
        print("[skip] 参考页里抽不出「A N 道」——**措辞变了就核不了**，本轮未能核对"
              "（读不出来不等于通过，纪律 101）")
        return 2
    ref_a = int(m.group(1))
    rows = data.get("rows") or []
    a_cnt = len([r for r in rows if r.get("changed") is True])
    b_cnt = len([r for r in rows if str(r.get("class", "")).startswith("B")])
    print("    矩阵：%s，%d 行 / %d 个指纹 / A %d / B %d / C %d"
          % (data.get("measured_at"), len(rows), len(data.get("fingerprints") or {}),
             a_cnt, b_cnt, len(rows) - a_cnt - b_cnt))
    problems = verify_shape(data, len(measured_gates()), ref_a, path)
    if problems:
        print("落盘矩阵形状核对：%d 处不符" % len(problems))
        for x in problems:
            print("  ✗ " + x)
        return 1
    print("  ok   落盘矩阵形状：%d 行 / %d 指纹 / A %d（与参考页同一个数）/ B 0 / 0 行作废，"
          "不含闸 45 自己，无 mode·reused 残留"
          % (len(rows), len(data.get("fingerprints") or {}), ref_a))
    return 0


if __name__ == "__main__":
    #: **整个入口包在 try 里**：第一版没有包，于是 `REF_A_RE = re.compile(...)`
    #: 因为忘了 `import re` 直接抛 `NameError`，而 **Python 对未捕获异常的退出码是 1
    #: ——在 `--verify` 的语义里 1 是「核出形状不符」，而真实含义是「判据自己没跑起来」**。
    #: **同一个批次里这件事已经栽过一次**：Batch 336 那道新闸写完 docstring 第一段就是
    #: 「任何异常都收成 rc=2，不许它走 1」，**转头在这个工具里又让异常走了 1**。
    #: **所以「知道一条纪律」与「写代码时遵守它」是两件事**——
    #: **而唯一能保证后者的办法是让入口自己兜住**，因为人不会每次都记得。
    #: 判据的「说谎」比判据的「崩溃」更难发现：崩溃会留 traceback，说谎只留一个退出码。
    try:
        if "--verify" in sys.argv:
            rest = sys.argv[1:]
            sys.exit(verify(rest[0] if rest and not rest[0].startswith("-") else None))
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException as exc:                    # noqa: BLE001 —— 入口兜底即 rc=2
        print("[skip] 工具自身抛 %s（%s）——**没跑起来不等于形状对**（纪律 101）"
              % (type(exc).__name__, exc), file=sys.stderr)
        sys.exit(2)