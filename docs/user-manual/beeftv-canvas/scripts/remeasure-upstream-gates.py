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


def main():
    names = measured_gates()
    print("哨兵 ref = %s" % SENTINEL)
    print("逐道实测 %d 道闸（各两遍，最坏 %d 秒/遍）\n" % (len(names), TIMEOUT))
    rows = []
    for i, name in enumerate(names, 1):
        a = run(name, None)
        b = run(name, SENTINEL)
        row = {"gate": name, "normal": a, "sentinel": b,
               "changed": a["rc"] != b["rc"], "unusable": None}
        if a["rc"] != 0:
            # **红基线上的行不是证据**（纪律 367②）：两种成因被搅成一种
            row["unusable"] = "正常那一遍 rc=%s（**在红基线上量的行证明不了任何事**）" % a["rc"]
            row["changed"] = None
        rows.append(row)
        print("[%2d/%2d] %-34s 正常 rc=%-4s → 哨兵 rc=%-4s %s"
              % (i, len(names), name, a["rc"], b["rc"],
                 "变了" if row["changed"] else ("**作废（红基线）**" if row["unusable"] else "")))
        sys.stdout.flush()
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump({"measured_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                       "sentinel": SENTINEL, "rows": rows,
                       "fingerprints": {n: sha256_of(os.path.join(SD, n)) for n in names}},
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
    print("落盘：%s（含 %d 个指纹）" % (OUT, len(names)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())