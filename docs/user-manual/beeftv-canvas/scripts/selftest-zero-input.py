#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""零输入体检（Batch 192 新增）——**每个闸在「什么都没有」的时候都会说什么**。

背景（Batch 192 的实测，不是推想）：在一棵**空手册树**上逐个跑 25 道闸，
**`verify-tables.py` 原样输出「表格结构核对：0 个文件、全部表格行列数一致」并 rc=0**。
**「一个文件都没检查」和「全部文件都合格」在退出码上一样，在措辞上也几乎一样**，
而前者读起来像好消息。它躲过 25 道闸的理由很朴素——**它核的是 `.md`，
空树里没有 `.md`，于是任何「先读文件再核」的判据都会空转**
（Batch 191 纪律 156：判据必须报出「它实际核了几项」）。

**为什么是反验而不是第 26 道闸**（这个取舍本身是本批的一条方法论）——
**⚠️ Batch 280：这段理由的两个数都站不住，而取舍本身如今有了新形状。**

原写：「实测空树跑一遍 25 道闸要 **1–2 分钟**（慢的几道：`verify-quote-punct` 11s、
`verify-meta` 5s、`verify-shot-pixels` 4s、`verify-shot-drift` 20s），
**而 `build-site.sh` 现在只要 25 秒**。把一分钟的东西塞进每次构建，
**它就成了大家学会跳过的那一步**——**一个总被跳过的检查等于没有检查**。」

**① 「只要 25 秒」实测是 251 秒（4 分 11 秒，Batch 280 计时），低了 10 倍。**
这个数被抄进全树 8 处，**而 Batch 279 建闸 41 时的「5.4 秒 vs 25 秒」就出自它**——
**过期的理由比没有理由更坏**（纪律 288）：没有理由会引人发问，过期理由像现行决定。
**构建的真实耗时现在有每次刷新的真值**：`.git/beeftv-build-record` 的 `secs=`，
由 `build-site.sh` 自己写（闸 18 方向四g 核那三件事在不在）。

**② 「1–2 分钟」也已不是本文件今天的量级，而今天贵的是方向三**（Batch 278 分段实测三次）：

  · 方向一/二（空手册树）  **6.63 / 5.27 / 5.37 秒**
  · 方向三（本方向）        **195.27 / 190.96 / 191.07 秒**（占 **96.7% ～ 97.3%**）
  · 整份                    **202.02 / 196.36 / 196.56 秒**

Batch 192 那个「1–2 分钟」是**当时的实测**；**我不为它今天的量级给原因**——
没重测过的东西不写理由（纪律 244），**只登记今天测到的**。

**③ 取舍的新形状**：便宜的那一半**已提成第 41 道闸进了构建**（实测 5.4～5.6 秒，Batch 279），
留在本文件里的是慢的那一半。**而「它俩一起被排除」本身曾是个缺陷**——
`SLOW` 的含义是「构建从不跑它」，于是便宜的 5 秒被慢的 195 秒连带买票（Batch 279 已修）。
**本文件今天不进构建的理由是那 195～202 秒，不是「一分钟 vs 25 秒」。**
所以它走 `SELFTEST_COSTS` 登记（现登记 240 秒）、**提交前手动跑**（闸 18 的既有机制）。

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

import ast
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

import emptytree                                             # noqa: E402
from stagedeps import child_env                              # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REAL_ROOT = os.path.dirname(HERE)

#: **Batch 279 收敛**：这个正则收进 `emptytree.py` 了——
#: 闸 37「判据重复」实测抓到它**逐字出现在闸 41 与本文件里**，
#: 而**两处都工作正常，所以没有任何行为会报它**（纪律 274：
#: **共享概念只能有一份实现**）。**只认 0**，因为「N 个文件全部合格」是正常输出。
ZERO_COUNT_RE = emptytree.ZERO_COUNT_RE

#: **闸必须只读**（Batch 196 方向三的前提，见 `check_readonly()`）。
#: 方向一在临时树上跑，怎么写都无所谓；**方向三在真实手册树上跑**，
#: 一道闸若有了写操作，体检就会把「先 nuked 再检查」变成事实。
#: 这个前提不能靠「我记得闸都是只读的」——**它必须自己核**。
#: **写操作的入口**（Batch 204 从正则换成 AST，理由见 `check_readonly` 的说明）。
#: 第一版是逐行正则 `open\(\s*[^)]*?["'][wax+]`，而 `[^)]*?` **跨不过一个 `)`**——
#: `open(os.path.join(tmp, "x"), "w")` 这种最常见的写法它**完全看不见**。
#: **一道看不见 `open(f(...), "w")` 的只读判据，等于没有这道判据。**
WRITE_FUNCS = {
    # 删除 / 建目录
    "remove", "unlink", "rmdir", "removedirs", "makedirs", "mkdir",
    "rmtree", "copyfile", "copy2", "copytree", "move", "rename", "chmod",
    # 写文件
    "write_text", "write_bytes",
}
#: `open(...)` 的第 2 个实参（mode）里出现这些字母就算写。
WRITE_MODE_CHARS = "wax+"


def _call_name(node):
    """取一个调用点被调用的名字（`open` / `os.remove` / `Path.write_text` 的末段）。"""
    f = node.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return None


def _is_write_call(node):
    """这个调用是不是一次写操作（**认事实：被调什么、第几个实参是什么**）。"""
    name = _call_name(node)
    if name is None:
        return False
    if name in WRITE_FUNCS:
        return True
    if name == "open" and len(node.args) >= 2:
        mode = node.args[1]
        # 只在 mode 是**字面量**时判；算出来的 mode 静态不可知，**如实不算**
        # （声称覆盖了它其实没覆盖的，比不覆盖更坏）。
        if isinstance(mode, ast.Constant) and isinstance(mode.value, str):
            return any(c in mode.value for c in WRITE_MODE_CHARS)
    return False


def write_calls(path):
    """返回 `{行号: 那一行的源码}`，只含**判定为写操作的调用点**。

    **返回源码而不只是行号**，是因为豁免表按源码内容认人（见 `READONLY_EXEMPT`）——
    **行号会被上方任何一次编辑顶掉，源码内容不会。**

    **语法坏掉就抛**，不返回空字典：那会让一道坏掉的闸
    在方向三眼里变成一道干净的闸（纪律 178 的同款：查不了 ≠ 查过了没问题）。
    """
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    lines = text.split("\n")
    tree = ast.parse(text, filename=path)
    return {n.lineno: lines[n.lineno - 1].strip()
            for n in ast.walk(tree)
            if isinstance(n, ast.Call) and _is_write_call(n)}


#: **逐行**豁免，不是逐个文件放行（Batch 204）。
#: **按文件列 = 整份文件随便写**——那等于把一道闸变回可写，
#: 而方向三跑的正是**真实手册树**；**按行列 = 只放过这几行**，
#: 同一份闸里**新增任何一行写操作都会立刻重新变红**。
#: 每条都写清「为什么这一行可以写」——**没有理由的豁免等于没有豁免**。
#: **键是那一行的源码子串，不是行号**（Batch 205 实测后改的）。
#: 第一版用行号，结果**在它上方加 3 行注释，4 条豁免就集体错位**——
#: 症状是「4 处写操作突然没被登记 + 4 条豁免突然失效」，
#: **读起来像判据坏了，其实只是有人在上方写了几行字。**
#: **行号不是稳定标识，源码内容才是。**
READONLY_EXEMPT = {
    "verify-selftest-bootable.py": {
        'os.makedirs(os.path.join(tmp, "scripts"), exist_ok=True)':
            "方向十三：在 `tempfile.mkdtemp()` 出来的临时目录里建 `scripts/`"
            "（**不在手册树里**——`mkdtemp` 落在系统临时目录）",
        'os.path.join(tmp, "scripts", "stub.py"), "w"':
            "方向十三：往那个临时目录写 stub 闸脚本"
            "（**这一行老正则看不见**——`[^)]?` 跨不过 `os.path.join(...)` 里那个 `)`，"
            "所以第一版豁免表照着正则的输出建，**漏的正是它**）",
        'with open(p, "w", encoding="utf-8") as fh:':
            "方向十三：往那个临时目录写探针脚本",
        'shutil.rmtree(tmp, ignore_errors=True)':
            "方向十三：删掉那个临时目录",
    },
    #: **Batch 274 补登的闸 39 三行**——**这三条不是「我看了一眼觉得没事」**，
    #: **是先把三行的上下文读出来验过的**（纪律 244：不许给没验过的东西写理由）：
    #:   · `run_injection(g, None)` —— **两处调用都传 `None`**（实测第 260 / 281 行），
    #:     所以 `tempfile.mkdtemp(prefix="b270-gate.", dir=None)` 落在**系统临时目录**，
    #:     **不在手册树里**；
    #:   · `shutil.copytree(HERE, sdir)` —— `HERE` 是**被读的**真 `scripts/`，
    #:     `sdir = os.path.join(tmp, "scripts")` 是**临时目录里的**副本；
    #:   · `io.open(p, "w", …).write(new)` —— `p = os.path.join(sdir, gate)`，
    #:     **写的是临时副本，不是真闸**；注入完 `finally` 里 `rmtree(tmp)` 删掉。
    #: **为什么这类写操作值得登记、而不是「把闸改成只读」**：
    #: **「把闸改只读」在这道闸身上做不到**——**它的全部功能就是「复制一份、改坏、跑、删掉」**
    #:（纪律 305：判据问被测行为，而「把闸注入成坏样子再跑」这个行为必然要写文件）。
    #: **所以登记是它诚实的形态，而不是绕过**。
    #: **而它藏了三个批次才报出来（270 → 274）**，因为
    #: **`selftest-zero-input.py` 本身在 SLOW 里、构建从不跑它**
    #: ——**那正是「例数这一列的覆盖缺口」第一次真的咬人**（纪律 309）。
    "verify-gate-alive.py": {
        'shutil.copytree(HERE, sdir)':
            "把真 `scripts/` **复制**到临时目录（`HERE` 是被读的）——"
            "**两处调用都传 `sandbox_root=None`，`mkdtemp` 落在系统临时目录**",
        'io.open(p, "w", encoding="utf-8").write(new)':
            "把**注入后的副本**写回临时目录（`p` 在 `tmp` 底下）——"
            "**这道闸的全部功能就是「复制一份、改坏、跑」**，不写文件做不到",
        'shutil.rmtree(tmp, ignore_errors=True)':
            "删掉那个临时目录（`finally` 里）",
    },
    #: **Batch 279 补登的闸 41 一行**。**先核实再登记**（纪律 244）：
    #: `verify-empty-tree.py:122` 是 `tmp = tempfile.mkdtemp(prefix="empty-tree-gate.")`，
    #: `:129` 是 `finally: shutil.rmtree(tmp, ignore_errors=True)`——
    #: **`tmp` 落在系统临时目录，不在手册树里**，而**本闸对整棵手册树只读**
    #: （所有写入都发生在那个 `mkdtemp` 出来的目录里）。
    #: **为什么它需要写权限**（与闸 39 同款，纪律 305）：
    #: **这道闸的全部功能就是「建一棵空树、往里搬闸、逐道跑、删掉」**，
    #: **不写文件做不到**。
    #: **而它比闸 39 更便宜的原因之一正在这里**：闸 39 要在**真 scripts/ 旁边**建沙箱，
    #: 于是 `selftest-zero-input.py` 的方向三需要一道「闸必须只读」的前提自检；
    #: **本闸只碰临时树，那道前提对它不适用**。
    "verify-empty-tree.py": {
        'shutil.rmtree(tmp, ignore_errors=True)':
            "删掉 `tempfile.mkdtemp(prefix=\"empty-tree-gate.\")` 出来的临时目录"
            "（`finally` 里）——**不在手册树内**，本闸对真树只读",
    },
}


def check_readonly(gates):
    """**闸必须只读**——方向三跑在真实手册树上，这是它的安全前提。

    实测（Batch 196）：25 道闸全部无写操作，所以这个前提今天成立。
    **但「今天成立」和「永远成立」是两回事**——将来某道闸顺手加个
    `open(..., "w")`，体检就会在真实手册树上执行它。

    所以这里**主动核**：有写操作就 **rc=2「未能核对」**并拒绝开跑。
    **判据的边界就该写在判据里**，不让人以为它覆盖了它没覆盖的东西。

    **「先核前提再执行」的顺序不能动**（Batch 204）：
    有人提过改用「跑完再比对手册树有没有变」——那是**跑完之后**才发现，
    而方向三跑的就是真实手册树，**先核才安全**。
    所以豁免走**逐行登记**，不走事后 diff。

    **豁免双向可检**：登记的那一行若已不是写操作，报「例外已失效，请删掉」——
    **一条过期的豁免会让真写操作悄悄重新变红**，那比没有豁免更坏。

    **本判据的边界（Batch 204 实测后写下来的）**：
      · 判的是**调用点**：调用哪个函数、第几个实参是什么——由语法树说了算，
        **不由行里的字符顺序说了算**（第一版按行正则，`[^)]*?` 跨不过 `)`，
        `open(os.path.join(tmp, "x"), "w")` 会被**完全放过**）；
      · `open` 的 mode **只认字面量**，算出来的 mode 静态不可知，**如实不算**；
      · **子进程里的写看不见**（`subprocess` 调外部程序改文件），
        **判据覆盖不到的地方必须说出来，而不是让人以为它全覆盖**。
    """
    dirty = []
    for gate in gates:
        path = os.path.join(HERE, gate)
        allow = READONLY_EXEMPT.get(gate, {})
        hit = write_calls(path)
        used = set()
        for n, src in sorted(hit.items()):
            match = next((k for k in allow if k in src), None)
            if match is None:
                dirty.append("%s:%d 出现了不在豁免表里的写操作：%s"
                             % (gate, n, src[:60]))
            else:
                used.add(match)
        for k in sorted(set(allow) - used):
            dirty.append("%s 的只读豁免**已失效**（源码里已没有含 %r 的写操作行）"
                         "　→ 请删掉这条登记：留着它，下一个人会以为那一行仍然被放过"
                         % (gate, k))
    return dirty

#: 这些闸的输入全部在手册树之外（读上游仓库或扫 scripts/），空树对它们没有意义，
#: **Batch 279 删掉本文件里的 `EXEMPT` 别名**——它原本只被方向一/二用
#: （`run_gates(..., skip=EXEMPT)`），而那一半搬成了闸 41。
#: **留着它就是一份没人读的常量**，而**这个文件通篇在治的病之一
#: 就是「账本上有一项、实际没人用」**。
#: **判据本体在 `emptytree.py`**（闸 41 从那里读）。


#: 兜底声明里的落点。**只认共用措辞的那一种形态**——Batch 202 之后
#: 15 道闸都走 `baseline.announce_fallback()`，所以这一行是全项目唯一的形态。
#: （在那之前还有两道闸手写措辞，而它们能过方向三之三**纯属巧合**：
#: 判据认的是 `[兜底]` 这个字符串，而它们恰好写了同样的字符串。）
#: **路径里可能有空格**，所以用 `(.+?)` 松配 + 行尾锚，**不用 `\S+`**——
#: 用户把仓放在 `/Users/Some One/BeefTV` 下是合法的。
FALLBACK_PATH_RE = re.compile(r"改用候选表里的 (.+?)\s*$", re.M)


def read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()




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
    crashed, found, silent, announced = [], [], [], {}
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
        # 方向三之三：**在「`BEEFTV_SRC` 指向非仓」这一次运行里，
        # 凡是碰过上游解析的闸都必然走了兜底**——那么它就必须说出来。
        # 判据不问「它是不是真走了兜底」（那要问解析器），
        # **只问「它说了没有」**：说了就一定走了，没说就有可能是静默降级。
        if _touches_upstream(gate) and "[兜底]" not in out:
            silent.append(gate)
        # 方向三之四的原料：**它读的是哪一份**。原样存字符串，
        # **不在这里判对错**——对错要跨全部 15 道一起看（`check_announced`）。
        m = FALLBACK_PATH_RE.search(out)
        if m:
            announced[gate] = m.group(1)
        elif "[兜底]" in out:
            # **说了却没给出落点**——这比「没说」还糟：它占了说明的位置。
            announced[gate] = None
    return crashed, found, silent, announced


def _touches_upstream(gate):
    """这道闸会不会去解析上游仓（**认事实：它 import 了 `baseline` / `beefsrc`**）。

    **为什么要先判「碰没碰过上游」**：方向三里另一些闸的输入全在手册树内
    （11 道正当 rc=0），**它们压根没解析过上游，也就无所谓有没有说明**——
    要求它们打印 `[兜底]` 是判据在说假话（纪律 166：首跑全绿不是证据，
    首跑全红同样不是）。
    """
    src = read(os.path.join(HERE, gate))
    return bool(re.search(r"^\s*(?:import\s+(?:baseline|beefsrc)\b"
                          r"|from\s+(?:baseline|beefsrc)\s+import)", src, re.M))


def _is_checkout(path):
    """这个路径能不能当 git 检出用（**判据自己问 git，不向解析器问答案**）。

    **为什么不直接问 `beefsrc.resolve_src()`**：那等于让被核对象给自己打分——
    它说「我落在真仓上」，判据再问它「你落在真仓上了吗」，答的一直是同一句话。
    判据要的是一个**独立**的事实：`git -C <path> rev-parse --git-dir` 成不成立。
    **用的判真标准与 `beefsrc` 是同一条**（Batch 197），但执行者是判据自己。
    """
    if not path:
        return False
    try:
        p = subprocess.run(["git", "-C", path, "rev-parse", "--git-dir"],
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return False
    return p.returncode == 0


def check_announced(announced):
    """方向三之四：**说了还不够，说的落点得站得住**（判据两条都不向解析器要答案）。

    方向三之三只问「说了没有」，**而说了的东西本身可能是错的，且错得毫无声响**。
    两条要查的：
      · **一致性**：同一个环境下，15 道闸说的落点必须**完全相同**。
        不相同就说明其中某几道还在自己解析上游——**「BeefTV 在哪」在闸里
        曾经有 4 种写法**（Batch 197），这里防的是它长出第 5 种；
      · **真检出**：落点必须**自己就能当 git 检出用**。一道闸报出一个
        不存在的目录，读者照样会以为它核过了。

    **为什么这两条不能合成一条**：「都不一样」和「都一样但都不存在」
    是两个长得一样、方向相反的失灵方式（纪律 185）。
    """
    problems = []
    by_path = {}
    for gate, path in sorted(announced.items()):
        if path is None:
            problems.append("%s 打了 `[兜底]` 却没有报出落点 —— **说了等于没说**（纪律 189）"
                            % gate)
        else:
            by_path.setdefault(path, []).append(gate)
    if len(by_path) > 1:
        for path, gs in sorted(by_path.items()):
            problems.append("%s 说自己核的是 `%s`"
                            % ("、".join("`%s`" % g for g in gs), path))
        problems.append("    → **同一个环境下各闸读的不是同一份检出**。"
                        "「BeefTV 在哪」在闸里曾经有 4 种写法（Batch 197），别再长出第 5 种")
    for path in sorted(by_path):
        if not _is_checkout(path):
            problems.append("落点 `%s` 自己就不是一个可用的 git 检出"
                            "（`git -C <p> rev-parse --git-dir` 失败）" % path)
    return problems


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

    **⚠️ Batch 278：紧接上面那段原描述里的耗时与理由，两处都已被实测否证。**
    **原话保留在下面，是为了让人看见它是怎么错的**——
    **而它错的方式恰恰是最坏的那一种：它是一份仍然读起来像现行决定的依据。**

    原写：「**实测 5.3s**，比方向一那 1.2s 慢一点，但**远低于 `build-site.sh` 的 25s**
    ——原因是闸在基线不可解析时**提前退出**，并不真去读上游。」

    **① 前提作废**：`beefsrc` 在 Batch 197 拿到了可用的兜底，于是本方向里
    `BEEFTV_SRC` 指向非仓的那些闸**不再秒退，而是回落到真仓把整道闸跑完**
    ——**上面 Batch 197 那段已经写明了后果（9.4s → 33.2s），
    而这一句原描述一直留在原地没跟着改**。

    **② 它指错了半边**：今天贵的是**本方向**，不是方向一。
    **Batch 278 分段实测**（副本树 / 40 道闸 / 同一台机器 / 三次）：

      · 方向一/二（空手册树）      **6.63 / 5.27 / 5.37 秒**
      · 方向三（本方向）            **195.27 / 190.96 / 191.07 秒**（占 **96.7% / 97.3% / 97.3%**）
      · 只读前提自检               0.10 / 0.11 / 0.11 秒
      · 合计                        **202.02 / 196.36 / 196.56 秒**

    **三次的比例几乎不动（96.7% / 97.3% / 97.3%）**——
    **而这台机器的绝对值实测会漂（本文件 `SLOW` 条目里就记着「2 倍漂」），
    所以下面这句话说的是比例，而比例恰好是稳的那一半。**

    **所以那份论证的正确版本几乎是反过来的**：
    当初抓到真缺陷的**空树那半只要 5～7 秒**（而它正是 Batch 191/192
    抓到 `verify-tables.py`「0 个文件 rc=0」的那一半），
    **本方向是 `build-site.sh` 时长的 7～8 倍**。
    「整份文件只做反验、不进构建」这个**结论仍然成立**，
    **但它当年给的理由指向了另一半，而读者只会读到那个理由**。

    **这两份抄本也一起过期了**：`SLOW.seconds` 与 `SELFTEST_COSTS` 都登记 190，
    互相印证、方向四e 报绿，**而实测 196～202 秒**——
    **这是纪律 310「同一个量被抄了两遍，而两遍一起过期」的第三个实例**，
    **也正是方向四e 注释里自己写下的那个盲区**（它抓不到两遍一起错）。
    Batch 278 据实订正，并新增**方向四f**：
    **成本必须能落到源文件里真实存在的步骤上**（`cost_split`），
    **于是下一次重测有一个可以逐段落笔的位置，而写错的那一段会立刻报「锚点不在场」。**
    """
    scratch = tempfile.mkdtemp(prefix="zero-input-")
    bad = os.path.join(scratch, "上游仓不在这里")   # **故意不创建**
    try:
        env = child_env(REAL_ROOT, PYTHONDONTWRITEBYTECODE='1', BEEFTV_SRC=bad)
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
        print("零输入体检（方向三）**拒绝开跑**：%d 处闸里出现了不该有的写操作"
              "或已失效的只读豁免 ——" % len(dirty))
        for where in dirty[:10]:
            print("  · %s" % where)
        print("    → 方向三跑在**真实手册树**上（它的前提就是「手册树正常」），"
              "闸若可写，体检会先改再核。")
        print("    → 要么把写操作挪出闸（闸应当只读），"
              "要么按**行**登记进 `READONLY_EXEMPT` 并写清理由，"
              "要么给方向三单独复制一份手册树。")
        return 2

    t0 = time.time()
    c3, f3, silent, announced = direction_three(gates)
    wrong = check_announced(announced)
    cost = time.time() - t0

    report("零输入体检（方向三）", c3, f3, "手册树正常、`BEEFTV_SRC` 指向非仓")

    if silent:
        print("零输入体检（方向三之三）：%d 道闸**走了兜底却一声不吭**——" % len(silent))
        for gate in silent:
            print("  · `%s` 在 `BEEFTV_SRC` 指向非仓时输出了结果，"
                  "**而它 import 了 `baseline`/`beefsrc`、必然回落到候选表里的真仓**"
                  % gate)
            print("    → **静默降级比直接失败更坏，因为它还报绿**（纪律 172）："
                  "读者无从知道它核的不是 `BEEFTV_SRC` 指定的那一份")
        print("    → 修法：在 `main()` 开头调 `baseline.announce_fallback()`。"
              "**措辞只写一份**——15 道碰上游解析的闸共用同一个函数，"
              "它自己从调用栈认出调用者是哪道闸")
        print()

    if wrong:
        print("零输入体检（方向三之四）：%d 道闸**说了落点，但落点站不住**——" % len(wrong))
        for line in wrong:
            print("  · %s" % line)
        print("    → 方向三之三只问「说了没有」；**说错了同样没人拦**，"
              "因为一道闸报出一个不存在的目录时，读起来仍然像「它核过了」")
        print("    → 修法：落点只从 `baseline.announce_fallback()` 出，"
              "并且**它必须是一个真的 git 检出**——判据自己跑 `git -C <p> rev-parse --git-dir` "
              "去核，**不向 `beefsrc` 要答案**（那等于让被核对象给自己打分）")
        print()

    if f3 or c3 or silent or wrong:
        return 1
    #: **Batch 279 修掉一条「报出一件没做的事」**：方向一/二搬成闸 41 之后，
    #: 汇总行原来还写着「%d 道闸在两个极端下各跑一遍」并报告方向一/二——
    #: **而本文件已经不跑它了**。
    #: **这是纪律 300 推论四那个形状的另一种写法**：
    #: 「一句话都没说」会被判未能核对，**而「说了一件没做的事」连判据都没有**——
    #: **它读起来像好消息，而它是假的**。
    #: **所以下面必须只报本文件真跑过的那一个极端。**
    print("零输入体检：%d 道闸在「手册树正常、`BEEFTV_SRC` 指向非仓」这一个极端下各跑一遍 —— "
          % len(gates))
    print("  · 方向三：没有一道报绿，也没有一道把异常当成「核出不一致」；"
          "**方向一/二（空手册树）已搬成闸 41 `verify-empty-tree.py`，每次构建都跑**"
          "（实测 5.4 秒）——**它不在本文件里，所以也不在本文件的耗时里**")
    print("  · 方向三之三：**碰过上游解析的闸，走了兜底都明说了**（纪律 172）")
    print("  · 方向三之四：**说了的落点跨 %d 道闸完全一致，且它自己就是一个可用的 git 检出**"
          % len(announced))
    print("  · 实测 %.1fs（含「闸只读」前提自检 %d 处写操作 = 0）" % (cost, len(dirty)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
