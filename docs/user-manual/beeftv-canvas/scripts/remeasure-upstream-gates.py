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
import subprocess
import sys
import time

MAN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SD = os.path.join(MAN, "scripts")
OUT = os.path.join(SD, "upstream-gates-sentinel.json")
SENTINEL = "zzz-not-a-real-ref-9f3a"
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


def load_prev():
    """读上一份落盘矩阵（读不出来就算没有——**一份坏数据不该让重测拒绝干活**）。"""
    if not os.path.exists(OUT):
        return None
    try:
        d = json.load(open(OUT, encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
    return d if isinstance(d, dict) and isinstance(d.get("rows"), list) else None


def main(argv=None):
    full = "--full" in (argv if argv is not None else sys.argv[1:])
    names = measured_gates()
    td = tree_digest()
    sh, shared_names = shared_digest()
    prev = load_prev()
    prev_rows = {r.get("gate"): r for r in (prev or {}).get("rows", []) if isinstance(r, dict)}
    prev_fps = (prev or {}).get("fingerprints") or {}
    # **复用条件三条同时成立**：共享摘要没变、手册内容摘要没变、这一行自己的指纹没变。
    # **少一条就是「拿旧数据冒充新数据」**（纪律 368①）
    reusable = bool(prev) and not full \
        and prev.get("shared_digest") == sh and prev.get("tree_digest") == td \
        and prev.get("sentinel") == SENTINEL
    if prev and not reusable and not full:
        why = []
        if prev.get("sentinel") != SENTINEL:
            why.append("哨兵 ref 换了")
        if prev.get("shared_digest") != sh:
            why.append("scripts/ 下有文件变了（共享实现 / 反验 / 夹具）")
        if prev.get("tree_digest") != td:
            why.append("手册内容变了")
        print("上一份矩阵**不能复用**（%s）→ 本次全量重测" % "、".join(why))
    if full:
        print("--full：强制全量重测")
    print("哨兵 ref = %s" % SENTINEL)
    print("内容摘要 = %s…（%d 个文件）" % (td[:16], len(content_files())))
    print("共享摘要 = %s…（%d 个文件）" % (sh[:16], len(shared_names)))
    print("逐道实测 %d 道闸（各两遍，最坏 %d 秒/遍）\n" % (len(names), TIMEOUT))
    rows = []
    n_reuse = 0
    for i, name in enumerate(names, 1):
        fp = sha256_of(os.path.join(SD, name))
        old = prev_rows.get(name)
        if reusable and old is not None and prev_fps.get(name) == fp and not old.get("unusable"):
            # **复用**：这一行的一切输入（自己的源码 / 共享实现 / 手册内容）都没变
            row = dict(old, gate=name, measured_at=old.get("measured_at", "?"), reused=True)
            n_reuse += 1
        else:
            a = run(name, None)
            b = run(name, SENTINEL)
            row = {"gate": name, "normal": a, "sentinel": b,
                   "changed": a["rc"] != b["rc"], "unusable": None,
                   "measured_at": time.strftime("%Y-%m-%d %H:%M:%S"), "reused": False}
            if a["rc"] != 0:
                # **红基线上的行不是证据**（纪律 367②）：两种成因被搅成一种
                row["unusable"] = "正常那一遍 rc=%s（**在红基线上量的行证明不了任何事**）" % a["rc"]
                row["changed"] = None
        rows.append(row)
        tag = "（复用 %s）" % row["measured_at"] if row["reused"] else ""
        if row["unusable"]:
            mark = "**作废（红基线）**"
        elif row["changed"]:
            mark = "变了"
        else:
            mark = ""
        print("[%2d/%2d] %-34s 正常 rc=%-4s → 哨兵 rc=%-4s %s%s"
              % (i, len(names), name, row["normal"]["rc"], row["sentinel"]["rc"], mark, tag))
        sys.stdout.flush()
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump({"measured_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                       "sentinel": SENTINEL, "rows": rows,
                       "mode": "full" if (full or not reusable) else "incremental",
                       "reused": [r["gate"] for r in rows if r["reused"]],
                       "tree_digest": td, "shared_digest": sh,
                       "fingerprints": {r["gate"]: sha256_of(os.path.join(SD, r["gate"]))
                                        for r in rows}},
                      fh, ensure_ascii=False, indent=1)

    usable = [r for r in rows if not r["unusable"]]
    changed = [r["gate"] for r in usable if r["changed"]]
    to2 = [r["gate"] for r in usable if r["sentinel"]["rc"] == 2]
    bad = [r for r in rows if r["unusable"]]
    print("\n==== 汇总 ====")
    print("共 %d 道：**%d 道 rc 变了**（其中 %d 道变为 2）；**复用 %d 行 / 重跑 %d 行**"
          % (len(rows), len(changed), len(to2), n_reuse, len(rows) - n_reuse))
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
    print("落盘：%s（%d 个指纹 / 内容摘要 %s… / 共享摘要 %s…）"
          % (OUT, len(names), td[:12], sh[:12]))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())