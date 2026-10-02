#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""零输入体检（Batch 192 新增）——**每个闸在「什么都没有」的时候都会说什么**。

背景（Batch 192 的实测，不是推想）：在一棵**空手册树**上逐个跑 25 道闸，
**`verify-tables.py` 原样输出「表格结构核对：0 个文件、全部表格行列数一致」并 rc=0**。
**「一个文件都没检查」和「全部文件都合格」在退出码上一样，在措辞上也几乎一样**，
而前者读起来像好消息。它躲过 25 道闸的理由很朴素——**它核的是 `.md`，
空树里没有 `.md`，于是任何「先读文件再核」的判据都会空转**
（Batch 191 纪律 156：判据必须报出「它实际核了几项」）。

**为什么是反验而不是第 26 道闸**（这个取舍本身是本批的一条方法论）：
实测空树跑一遍 25 道闸要 **1–2 分钟**（慢的几道：`verify-quote-punct` 11s、
`verify-meta` 5s、`verify-shot-pixels` 4s、`verify-shot-drift` 20s），
**而 `build-site.sh` 现在只要 25 秒**。把一分钟的东西塞进每次构建，
**它就成了大家学会跳过的那一步**——**一个总被跳过的检查等于没有检查**。
所以它走 `SELFTEST_COSTS` 登记、**提交前手动跑**（闸 18 的既有机制）。

**判据本身极窄，只抓一个形态**：`rc == 0` **且**输出里出现「0 个文件/页面/张/项/条/篇」。
**不抓**「非 0 退出」的那 22 道闸——它们在空树上报 rc=1 或 rc=2 是**对的**，
「报红」本来就比「空转」安全。

**一条更值钱的副产物**：这一轮同时记下了**哪些闸在输入缺失时抛未捕获异常**
（10 道：`error-copy` / `exclusions` / `feature-flags` / `label-drift` /
`line-counts` / `runtime-policy` / `screenshots-literals` / `shortcuts` /
`shot-version` / `unreachable`，它们在空树上都是 Python Traceback + rc=1）。
**按闸的约定那应该是 rc=2「未能核对」**——rc=1 说的是「核出问题了」，
而实际上一个文件都没找到。**这不影响它们的安全性（都非 0），只影响它们说的那句话**，
本批先记录、不改（改 10 道闸的异常路径是一次独立的重构，不该混在一次实测里）。

退出码：0 无人空转；1 至少一个闸在零输入下报绿。
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REAL_ROOT = os.path.dirname(HERE)

#: 「0 个 X」形态。**只认 0**，因为「N 个文件全部合格」是正常输出。
ZERO_COUNT_RE = re.compile(r"(\d+)\s*个(?:文件|页面|张|项|条|篇|断言|任务|反验|目录)")

#: 这些闸的输入全部在手册树之外（读上游仓库或扫 scripts/），空树对它们没有意义，
#: **不算「空转」**。列在这里是因为它们报的数不是「核了几项手册文件」。
EXEMPT = {
    "verify-selftest-deps.py",      # 核的是 scripts/ 里的反验，与手册文件无关
    "verify-selftest-bootable.py",  # 同上
    "verify-encoding.py",           # 白名单里的 .py 仍在树内，它确实核了东西
}


def empty_tree(tmp):
    """一棵空手册树：只有闸脚本与共用模块，**没有任何 .md / 截图 / 清单**。"""
    os.makedirs(os.path.join(tmp, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(tmp, ".vitepress"), exist_ok=True)
    for name in sorted(os.listdir(HERE)):
        if name.endswith(".py") and not name.startswith("selftest-"):
            shutil.copy(os.path.join(HERE, name), os.path.join(tmp, "scripts", name))
    return tmp


def main():
    gates = sorted(f for f in os.listdir(HERE)
                   if f.startswith("verify-") and f.endswith(".py"))
    tmp = tempfile.mkdtemp(prefix="zero-input-")
    found = []
    try:
        empty_tree(tmp)
        env = dict(os.environ)
        env["BEEFTV_MANUAL_ROOT"] = tmp
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["BEEFTV_SRC"] = os.environ.get("BEEFTV_SRC", "")
        for gate in gates:
            try:
                p = subprocess.run(
                    [sys.executable, os.path.join(tmp, "scripts", gate)],
                    capture_output=True, text=True, env=env, timeout=180)
                rc, out = p.returncode, (p.stdout or "") + (p.stderr or "")
            except subprocess.TimeoutExpired:
                rc, out = -1, "超时"
            if rc != 0:
                continue                       # 非 0 一律是安全的，不看
            if gate in EXEMPT:
                continue
            zeros = [m.group(0) for m in ZERO_COUNT_RE.finditer(out) if m.group(1) == "0"]
            if zeros:
                found.append((gate, zeros))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if found:
        print("零输入体检：%d 道闸在「什么都没有」时报绿 ——" % len(found))
        for gate, zeros in found:
            print("  · `%s` 输出里出现 %s，**而退出码是 0**" % (gate, "、".join(sorted(set(zeros)))))
            print("    → 「一个都没检查」和「全部都合格」在退出码上一样，"
                  "**前者读起来却像好消息**（纪律 156）")
        print()
        print("修法：在打印那个计数之前加一句下界检查，`checked == 0` 时 return 2。")
        return 1
    print("零输入体检：%d 道闸逐一在空手册树上跑过，"
          "**没有一道在零输入下报绿**（%d 道豁免，其输入不在手册树内）"
          % (len(gates), len(EXEMPT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
