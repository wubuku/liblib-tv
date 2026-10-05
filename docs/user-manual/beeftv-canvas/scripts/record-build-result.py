#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**把一次构建的结果记下来**（Batch 255 新增）。**由 `build-site.sh` 在走到末尾时调用。**

**为什么需要它**：Batch 252/253 的构建实测各有一个 `[ FAIL ]` 且都停在闸 18，
**闸 19 到 36 与全部文档闸一次都没运行**，而我照常提交了，
批次行里写的验收结论是「构建仍全绿」（纪律 280）。
`fail()` 是 `exit 1`，**所以「能走到 `build-site.sh` 的末尾」本身就是 rc=0 的证明**——
**本脚本只在这个时刻被调用，于是它记下的每一个数字都不需要人转述。**

用法：
    python3 scripts/record-build-result.py --counts 82,0,0
    python3 scripts/record-build-result.py --check      # 只检查，不写

**`--check` 是给钩子与反验用的**：它跑 `buildrecord.check()`，
读到 `git diff --cached` 的内容，核「本次新增的批次号 ≤ 记录里的批次号」。

**为什么数字由 `build-site.sh` 的计数器给，而不是从日志里数**（Batch 255 实测）：
第一版从日志正则数 `[ ok ]`，**而真格式是 `[  ok  HH:MM:SS]`**——
`^\[\s*ok\s*\]` 要求 `]` 紧跟 `ok`，于是三段全部数成 0，
**而它 rc=0 照常写下了一个 `0 ok / 0 warn / 0 FAIL` 的记录文件**。
**一个自洽的假数比没有数更坏**，所以生产路径改成「函数自己数自己」，
**日志解析只留在反验里当独立旁证**（它数出来的数必须与计数器相等）。

退出码：`0` 放行 / `1` 有问题 / `2` 未能核对。
**`2` 的场合只有两个**：批次表里解析不出任何纯数字批次号；
**传进来的 `ok` 是 0**——**那几乎只能是调用方自己坏了，而不是「这次构建没输出」**。
"""

import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import buildrecord  # noqa: E402


def parse_counts(text):
    """`--counts ok,warn,fail` → `(ok, warn, fail)`。**任何一处解析不出来就抛 `ValueError`。**"""
    parts = [p.strip() for p in str(text).split(",")]
    if len(parts) != 3:
        raise ValueError("要三个数（ok,warn,fail），收到 %d 个：%r" % (len(parts), text))
    return tuple(int(p) for p in parts)


def staged_diff(repo):
    r = subprocess.run(["git", "-C", repo, "diff", "--cached"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None, "git diff --cached 失败：%s" % ((r.stderr or "").strip()[:80])
    return r.stdout, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--counts", help="`ok,warn,fail` 三个数，由 build-site.sh 的计数器给")
    #: **Batch 280 新增**：`--secs` 是这次构建的墙钟（秒），
    #: **由 `build-site.sh` 用 `date +%s` 实测**——
    #: **本项目那份手抄的「25 秒」已经低了 10 倍**（纪律 244）。
    ap.add_argument("--secs", default=None, help="本次构建墙钟（秒）")
    ap.add_argument("--check", action="store_true", help="只检查，不写记录")
    a = ap.parse_args()
    repo = buildrecord.repo_root()

    if a.check:
        diff, err = staged_diff(repo)
        if diff is None:
            print("[未能核对] %s" % err)
            return 2
        problems = buildrecord.check(diff)
        if problems:
            print("构建记录核对：%d 处问题" % len(problems))
            for p in problems:
                print("  ✗ " + p)
            return 1
        print("构建记录核对通过：本次提交没有超出上一次全绿构建覆盖的批次")
        return 0

    if not a.counts:
        print("[未能核对] 没有 --counts——**不得凭印象写数字**")
        return 2
    try:
        n_ok, n_warn, n_fail = parse_counts(a.counts)
    except ValueError as exc:
        print("[未能核对] --counts 解析失败：%s" % exc)
        return 2
    batch = buildrecord.newest_batch()
    if batch is None:
        print("[未能核对] 批次表里解析不出任何纯数字批次号——**不得当成 0**")
        return 2
    if n_fail:
        print("[未能核对] 传进来 fail=%d——**这一条路径只应在构建走到末尾时被调用**" % n_fail)
        return 2
    if n_ok == 0:
        # **「读到 0 行」必须与「全部都没有」长得不一样**（纪律 156/159）。
        # **一次正常的构建至少会打出十几行 `[ ok ]`**，
        # **而 0 唯一的来源是调用方自己坏了**——
        # **本模块第一版就是这样写下 `0 ok / 0 warn / 0 FAIL` 而 rc=0 的。**
        print("[未能核对] 传进来 ok=0——**这几乎只能是调用方坏了，"
              "不是「这次构建没输出」**；**拒绝写记录**（写下去的是一个自洽的假数）")
        return 2
    p = buildrecord.write_record(batch, n_ok, n_warn, n_fail, a.counts, a.secs)
    print("全绿构建已记录：Batch %d，%d ok / %d warn / %d FAIL → %s"
          % (batch, n_ok, n_warn, n_fail, p))
    return 0


if __name__ == "__main__":
    sys.exit(main())
