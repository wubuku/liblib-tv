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

**方向三试过又撤掉了（Batch 195）**：纪律 164 说「输出要报条数而不只报范围」，
本批想把它做成常驻检查。**先普查**：全树只有 **3 行**输出带「X..Y」范围
（闸 21 两行 + 闸 9 一行），**三行都同时报了条数**——**纪律 164 没有第二个受害者**。
然后写判据，**鉴别力验证没通过**：把闸 21 的方向二输出注入成「只报范围」的写法，
**判据没抓到**。根因是粒度不对——同一行里还有「41 个 .md、130 处纪律编号引用」，
**「整行有没有量词」根本判不出真假**；改成「量词数字必须等于范围端点」也不行，
因为**条数（159）与编号范围（1..165）本来就是两个不同的量**，它们不该相等。
再收窄到「范围前 15 字符内要有量词」能过，但**那已经是在拟合闸 21 一行的写法**。
**结论：这个形态机械不可判定**——「只报范围」的成因是**文案习惯**而不是逻辑错误，
所以它只能靠人记（纪律 164 留在条文里），**建不成判据**。
**又一次「判据的上线第一次跑要过鉴别力验证」**：
如果只看「首跑全绿」，方向三会带着一个恒真的内核进账本。

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
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REAL_ROOT = os.path.dirname(HERE)

#: 「0 个 X」形态。**只认 0**，因为「N 个文件全部合格」是正常输出。
ZERO_COUNT_RE = re.compile(r"(\d+)\s*个(?:文件|页面|张|项|条|篇|断言|任务|反验|目录)")

#: **闸必须只读**（Batch 196 方向三的前提，见 `check_readonly()`）。
#: 方向一在临时树上跑，怎么写都无所谓；**方向三在真实手册树上跑**，
#: 一道闸若有了写操作，体检就会把「先 nuked 再检查」变成事实。
#: 这个前提不能靠「我记得闸都是只读的」——**它必须自己核**。
WRITE_RE = re.compile(
    r"""open\(\s*[^)]*?["'][wax+]"""
    r"""|os\.remove\(|os\.unlink\(|os\.rmdir\(|shutil\.rmtree\("""
    r"""|os\.makedirs\(|os\.mkdir\("""
    r"""|\.write_text\(|\.write_bytes\(""")


def check_readonly(gates):
    """**闸必须只读**——方向三跑在真实手册树上，这是它的安全前提。

    实测（Batch 196）：25 道闸全部无写操作，所以这个前提今天成立。
    **但「今天成立」和「永远成立」是两回事**——将来某道闸顺手加个
    `open(..., "w")`，体检就会在真实手册树上执行它。

    所以这里**主动核**：有写操作就 **rc=2「未能核对」**并拒绝开跑。
    **判据的边界就该写在判据里**，不让人以为它覆盖了它没覆盖的东西。
    """
    dirty = []
    for gate in gates:
        path = os.path.join(HERE, gate)
        with open(path, encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                if WRITE_RE.search(line):
                    dirty.append("%s:%d" % (gate, n))
    return dirty

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
    # **显式再搬一次 `beefsrc`**（Batch 201，闸 17 方向一抓到的）：
    # 上面那个循环其实已经把所有非反验的 `.py` 都搬了，**但闸 17 判的是
    # 「有没有一条看得见的搬运动作」**——循环写法静态不可判定，
    # 它会把「搬过了」报成「没搬」（Batch 190/194 同款：判据认写法不认事实）。
    # **这里不改成新契约机制**（那本身是腐烂点），而是照 Batch 197 的规矩
    # **把写法改成可判定的**：显式一条、目标路径写死文件名。
    shutil.copy(os.path.join(HERE, "beefsrc.py"),
                os.path.join(tmp, "scripts", "beefsrc.py"))
    return tmp


def run_gates(gates, script_dir, env, skip=()):
    """逐个跑闸，返回 `(崩溃, 报绿)` 两个名单。

    **判据（两个方向共用，极窄）**：
      · **崩溃**：`rc == 1` 且输出里有 `Traceback` / `Error:`
        —— rc=1 在本项目约定里意为「核过，且核出不一致」，
        **而异常泄漏意味着本轮根本没开始核**（Batch 193 实测的形态）。
      · **报绿**：`rc == 0` 且输出里出现「0 个 X」
        —— 「一个都没检查」和「全部都合格」在退出码上一样，
        **前者读起来却像好消息**（纪律 156）。
    其余一律不看：`rc == 2`（未能核对）是对的，`rc == 1` 无异常是真的核出了不一致。
    """
    crashed, found = [], []
    for gate in gates:
        if gate in skip:
            continue
        try:
            p = subprocess.run(
                [sys.executable, os.path.join(script_dir, gate)],
                capture_output=True, text=True, env=env, timeout=180)
            rc, out = p.returncode, (p.stdout or "") + (p.stderr or "")
        except subprocess.TimeoutExpired:
            rc, out = -1, "超时"
        if rc == 1 and ("Traceback" in out or "Error:" in out):
            tail = next((l.strip() for l in reversed(out.split("\n"))
                         if l.strip() and not l.strip().startswith("File \"")), "")
            crashed.append((gate, tail[:90]))
            continue
        if rc != 0:
            continue
        zeros = [m.group(0) for m in ZERO_COUNT_RE.finditer(out) if m.group(1) == "0"]
        if zeros:
            found.append((gate, zeros))
    return crashed, found


def report(label, crashed, found, scene):
    if crashed:
        print("%s：%d 道闸在「%s」时把异常当成了「核出不一致」——" % (label, len(crashed), scene))
        for gate, tail in crashed:
            print("  · `%s` 以 rc=1 退出，最后一行是：%s" % (gate, tail))
            print("    → rc=1 意为「核过且核出不一致」，**而实际是本轮根本没开始核**。"
                  "两种说法把排查引向完全不同的方向")
        print("    → 修法：把异常转成 rc=2。`baseline_guard` 装饰器就是为这件事加的"
              "（盖住任意深度的调用点，try 写在 main 里会漏）。")
        print()
    if found:
        print("%s：%d 道闸在「%s」时报绿 ——" % (label, len(found), scene))
        for gate, zeros in found:
            print("  · `%s` 输出里出现 %s，**而退出码是 0**"
                  % (gate, "、".join(sorted(set(zeros)))))
            print("    → 「一个都没检查」和「全部都合格」在退出码上一样，"
                  "**前者读起来却像好消息**（纪律 156）")
        print()


def direction_one(gates):
    """**手册树为空**：一个 .md / 截图 / 清单都没有。"""
    tmp = tempfile.mkdtemp(prefix="zero-input-")
    try:
        empty_tree(tmp)
        env = dict(os.environ)
        env["BEEFTV_MANUAL_ROOT"] = tmp
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["BEEFTV_SRC"] = os.environ.get("BEEFTV_SRC", "")
        return run_gates(gates, os.path.join(tmp, "scripts"), env, skip=EXEMPT)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def direction_three(gates):
    """**手册树正常，`BEEFTV_SRC` 指向一个不是仓的路径**。

    ── **Batch 201 更正这个方向的自我描述**（原来写的是「上游仓不可用」）──
    **Batch 197 把「BeefTV 在哪」收敛成 `beefsrc` 单一来源、并给它加了可用的兜底之后，
    「上游不可用」这个场景就不存在了**：`BEEFTV_SRC` 指向垃圾路径时，
    各闸会**回落到候选表里的真仓、把它整个跑完、并报 rc=0**。
    实测后果有两条，都得记下来：
      · **它测的东西变了**：不再是「上游没了会怎样」，
        而是「**`BEEFTV_SRC` 指向非仓时会回落到真仓并继续核**」——
        **这恰好是纪律 172 关心的那件事**（静默降级 vs 明确说明）；
      · **它慢了 3.5 倍**：实测 **9.4s → 33.2s**。原因是 7 道自带 `CANDIDATES` 的闸
        **不再快速 rc=2**，而是真跑一遍——单 `verify-unreachable.py` 就占 **16.8s**。
        **这不是回归，是它终于在真的做事**；代价是它已越过 30 秒阈值、
        必须登记为慢反验（闸 18 方向四d 当场拦过一次）。
    **原描述（保留作为它被写下来时的样子）**：

    这是方向一的**另一个极端**，与 Batch 193 同源而**至今没被测过**：
    方向一测的是「手册这边什么都没有」，方向三测的是「手册这边什么都有，
    **但它要核的那个上游不在**」。

    **为什么不能复制手册树**（方向一可以，方向三不行）：
    方向三的整个前提是「手册树**正常**」——复制出来的树天然无法同时
    满足「正常」与「隔离」。所以它**只能跑在真实手册树上**，
    于是「闸必须只读」从一句约定升级成**判据自己核的前提**（`check_readonly()`）。

    **实测 5.3s**，比方向一那 1.2s 慢一点，但**远低于 `build-site.sh` 的 25s**——
    原因是闸在基线不可解析时**提前退出**，并不真去读上游。
    """
    scratch = tempfile.mkdtemp(prefix="zero-input-")
    bad = os.path.join(scratch, "上游仓不在这里")   # **故意不创建**
    try:
        env = dict(os.environ)
        env["BEEFTV_MANUAL_ROOT"] = REAL_ROOT
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["BEEFTV_SRC"] = bad
        return run_gates(gates, HERE, env)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def main():
    gates = sorted(f for f in os.listdir(HERE)
                   if f.startswith("verify-") and f.endswith(".py"))

    # 方向三的安全前提：闸必须只读。**先核前提，再跑体检**——
    # 顺序反了就等于在真实手册树上执行一段还没被允许的代码。
    dirty = check_readonly(gates)
    if dirty:
        print("零输入体检（方向三）**拒绝开跑**：%d 处写操作出现在闸里 ——" % len(dirty))
        for where in dirty[:10]:
            print("  · %s" % where)
        print("    → 方向三跑在**真实手册树**上（它的前提就是「手册树正常」），"
              "闸若可写，体检会先改再核。")
        print("    → 要么把写操作挪出闸（闸应当只读），要么给方向三单独复制一份手册树。")
        return 2

    t0 = time.time()
    c1, f1 = direction_one(gates)
    c3, f3 = direction_three(gates)
    cost = time.time() - t0

    report("零输入体检（方向一/二）", c1, f1, "手册树为空")
    report("零输入体检（方向三）", c3, f3, "手册树正常但上游仓不可用")

    if f1 or c1 or f3 or c3:
        return 1
    print("零输入体检：%d 道闸在两个极端下各跑一遍 —— " % len(gates))
    print("  · 方向一/二（手册树为空）：没有一道在零输入下报绿，"
          "也没有一道把异常当成「核出不一致」；%d 道豁免，其输入不在手册树内"
          % len(EXEMPT))
    print("  · 方向三（手册树正常、`BEEFTV_SRC` 指向非仓）：没有一道报绿，"
          "也没有一道把异常当成「核出不一致」")
    print("  · 实测 %.1fs（含「闸只读」前提自检 %d 处写操作 = 0）" % (cost, len(dirty)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
