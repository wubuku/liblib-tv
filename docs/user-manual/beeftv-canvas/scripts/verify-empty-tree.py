#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 41「空手册树体检」——**每一道闸在「什么都没有」的时候会说什么**。

**为什么它是一道闸，而不再只是 `selftest-zero-input.py` 的方向一**（Batch 279）：
`selftest-zero-input.py` 整个文件因为方向三太慢（实测 190～202 秒）被登记进 `SLOW`，
而 **SLOW 的含义是「构建从不跑它」**——于是**方向一也跟着一起从构建里消失了**。
**而方向一恰恰是便宜的那一半**：

  · **Batch 278 分段实测三次**（副本树 / 40 道闸 / 同一台机器）：
    方向一/二（空手册树）**6.63 / 5.27 / 5.37 秒**，
    方向三（正常树 + `BEEFTV_SRC` 指向非仓）**195.27 / 190.96 / 191.07 秒**，
    **方向三占 96.7% / 97.3% / 97.3%**。

  · **本批实测的洞**：把 `verify-tables.py` 里 Batch 191 加的
    「`checked == 0` → rc=2」守卫摘掉（退回 2026 年的历史形态），
    它在空树上原样输出「**表格结构核对：0 个文件、全部表格结构一致**」并 **rc=0**，
    **而完整构建 86 ok / 0 warn / 0 FAIL、rc=0——一道闸都没发现它**。
    **这正是纪律 156 说的那个形态**（「一个都没检查」与「全部都合格」在退出码上一样），
    **而它躲过了当时的全部 25 道闸**。
    **本闸在同一个注入上 rc=1 并点名 `verify-tables.py`**（实测，见纪律 314）。

  · **代价**：实测 **5.6 秒**。`build-site.sh` 约 25 秒，**加上它约 31 秒**——
    **而当初那份「不进构建」的理由写的是「实测 5.3s，远低于 build 的 25s」，
    那份理由早就作废了**（纪律 288：过期的理由比没有理由更坏）。

**本闸只做方向一/二那一半**：在一棵**空手册树**上逐道跑闸，抓两件事——
  · **报绿**：`rc == 0` 且输出里出现「0 个 X」（纪律 156）；
  · **崩溃**：`rc == 1` 且输出里有 `Traceback` / `Error:`
    ——rc=1 意为「核过，且核出不一致」，**而异常泄漏意味着本轮根本没开始核**。

**方向三（正常树 + 上游坏）仍在 `selftest-zero-input.py` 里**，因为它必须在
**真实手册树**上跑，代价是 190～202 秒——**那半件事的性质决定了它只能登记慢反验**。

**本闸对整棵手册树只读**：所有写入都发生在 `tempfile.mkdtemp()` 出来的目录里，
**不碰真树**（而 `selftest-zero-input.py` 的方向三还需要一道只读前提自检，
因为它跑在真树上；**本闸不需要那道前提，这正是它便宜的原因之一**）。

**判据本身收在 `emptytree.py`**（Batch 279 收敛）：`ZERO_COUNT_RE` / `EXEMPT` /
`empty_tree()` 三样与那份反验**逐字共用**——**闸 37 判据重复实测抓到过
`ZERO_COUNT_RE` 出现在两个文件里**，而**两处都工作正常，所以没有任何行为会报它**。
**`run_gates()` 刻意没收进去**：两边问的**不是同一件事**（纪律 296 的切面）。

**必须排除自己**：本闸会在空树上跑「全部闸」，**而它自己也在那棵树里**——
不排除就是无限递归（与闸 18 把 `selftest-selftest-bootable.py` 硬排除同源）。

退出码：0 没有闸空转也没有闸把异常当成「核出不一致」；
        1 至少一道闸在空树上报绿，或把异常当成了「核出不一致」；
        2 本轮一道闸都没跑（前提不成立，**不装作核过了**——纪律 101）。
"""
import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emptytree                                             # noqa: E402
from stagedeps import child_env, stage_all                  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SELF = os.path.basename(__file__)

#: **豁免 = 共享的那三道 + 本闸自己**。**自己必须排除**（见模块 docstring）。
EXEMPT = set(emptytree.EXEMPT) | {SELF}

#: 单份闸的上限（秒）。**实测这一轮里每道闸都在 1 秒上下**（空树上闸多半秒退），
#: 300 是三个数量级的余量——**它的作用是「某一份卡死」而不是「机器慢」**，
#: **而这两件事必须分开**（超时单列成一类，不并进「崩溃」，纪律 311）。
PER_GATE_TIMEOUT = 300.0


def run_gates(gates, script_dir, env):
    """逐个跑闸，返回 `(崩溃, 报绿, 超时)` 三个名单。

    **判据（与 `selftest-zero-input.py` 方向一/二同一套，只是多了超时那一支）**：
      · **崩溃**：`rc == 1` 且输出里有 `Traceback` / `Error:`；
      · **报绿**：`rc == 0` 且输出里出现「0 个 X」；
      · **超时**：单份超过 `PER_GATE_TIMEOUT`。
    其余一律不看：`rc == 2`（未能核对）是对的，`rc == 1` 无异常是真的核出了不一致。
    """
    crashed, found, timeouts = [], [], []
    for gate in gates:
        if gate in EXEMPT:
            continue
        try:
            p = subprocess.run(
                [sys.executable, os.path.join(script_dir, gate)],
                capture_output=True, text=True, env=env,
                timeout=PER_GATE_TIMEOUT)
            rc, out = p.returncode, (p.stdout or "") + (p.stderr or "")
        except subprocess.TimeoutExpired:
            timeouts.append((gate, PER_GATE_TIMEOUT))
            continue
        if rc == 1 and ("Traceback" in out or "Error:" in out):
            tail = next((l.strip() for l in reversed(out.split("\n"))
                         if l.strip() and not l.strip().startswith("File \"")), "")
            crashed.append((gate, tail[:90]))
            continue
        if rc != 0:
            continue
        zeros = [m.group(0) for m in emptytree.ZERO_COUNT_RE.finditer(out)
                 if m.group(1) == "0"]
        if zeros:
            found.append((gate, zeros))
    return crashed, found, timeouts


def main():
    gates = sorted(f for f in os.listdir(HERE)
                   if f.startswith("verify-") and f.endswith(".py"))
    todo = [g for g in gates if g not in EXEMPT]
    if not gates:
        print("[skip] scripts/ 下没有找到任何闸——判据可能已失效")
        return 2
    if not todo:
        print("[skip] 全部闸都在豁免表里，本轮一道闸都没跑——"
              "**不拿「豁免表变大了」冒充「都核过了」**")
        return 2

    t0 = time.time()
    tmp = tempfile.mkdtemp(prefix="empty-tree-gate.")
    try:
        emptytree.empty_tree(tmp, stage_all)
        env = child_env(tmp, PYTHONDONTWRITEBYTECODE="1")
        crashed, found, timeouts = run_gates(todo, os.path.join(tmp, "scripts"), env)
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    cost = time.time() - t0

    for gate, secs in timeouts:
        print("空手册树体检：`%s` **超过 %.0f 秒没回来**" % (gate, secs))
        print("  · **超时单列，不并进「崩溃」**——卡死与抛异常要修的东西完全不同")
        print("    → 先确认它是不是在空树上真去做事（那本来就该慢），"
              "再谈它该不该登记为慢")
        print()
    for gate, tail in crashed:
        print("空手册树体检：`%s` 把异常当成了「核出不一致」（rc=1，最后一行：%s）"
              % (gate, tail))
        print("  · rc=1 意为「核过且核出不一致」，**而实际是本轮根本没开始核**"
              "——两种说法把排查引向完全不同的方向")
        print("  · 修法：把异常转成 rc=2。`baseline_guard` 装饰器就是为这件事加的")
        print()
    for gate, zeros in found:
        print("空手册树体检：`%s` **rc=0** 而输出里有 %s"
              % (gate, "、".join(sorted(set(zeros)))))
        print("  · 「一个都没检查」和「全部都合格」在退出码上一样，"
              "**而前者读起来却像好消息**（纪律 156）")
        print("  · 修法：计数为 0 时 rc=2，别让它按「全部合格」通过")
        print()

    if crashed or found or timeouts:
        return 1
    print("空手册树体检：%d 道闸在一棵空手册树上各跑一遍 —— " % len(todo))
    print("  · 没有一道在零输入下报绿（`rc=0` + 「0 个 X」），"
          "也没有一道把异常当成了「核出不一致」")
    print("  · %d 道豁免（不含本闸自己那份递归排除）：%s"
          % (len(EXEMPT), "、".join(sorted(EXEMPT))))
    print("  · 实测 %.1fs（含建空树与搬运；"
          "**Batch 278 同一份计时里这一半是 5～7 秒**）" % cost)
    return 0


if __name__ == "__main__":
    sys.exit(main())
