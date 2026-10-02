#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第十八道闸：反验必须能被启动，且启动失败要报出来（Batch 179 新增）。

**这道闸看守的是「哨兵有没有上线」**——Batch 178 踩的那个坑的通用解法。

**问题回顾（Batch 178 的实测）**：7 份反验、34 例跨三个批次全部失效，
而 `build-site.sh` 十七道闸一直全绿。因为**反验不在构建路径上**：
闸门本体在真实目录里跑得好好的，只有反验在临时目录里 import 失败。
**「反验坏了」不产生任何构建期信号，它只是安静地不再说话。**

**为什么不能简单地「把反验都加进构建」**（这是本闸的设计前提，必须先量过）：

  · `selftest-unreachable.sh` 走 git plumbing 往**上游仓库**注入并建临时 ref，
    **实测约 25 分钟**——放进每次构建不可接受；
  · `selftest-meta.sh` **实测 97 秒**（36 例）——勉强可接受，但它会
    **原地改 15 个真实文件**（含 `AUDIT.md` / `PROGRESS.md` / `build-site.sh`），
    构建中途失败就会把它们留在被改状态；
  · 其余 10 份 python 反验 1–10 秒不等，**可以直接进构建**。

**所以本闸不跑用例，只验「启动」**——即：用例开始之前那些必须成立的条件。
Batch 178 的 34 例失败**全部发生在启动阶段**（import 失败、找不到手册根），
**没有一例是用例逻辑本身出错**。因此：

  方向一：**每份反验都必须真的能被解释器加载**（语法正确、shebang 合法、
    shell 反验 `bash -n` 通过）。**语法坏掉的反验连启动都做不到。**
  方向二：**反验依赖的本地模块必须能被找到**——这正是 Batch 178 的根因，
    闸 17 核的是「有没有搬运」，本闸核的是「**在真实环境下能不能 import**」。
    **两道闸互补：闸 17 看反验的源码，本闸看真实 import。**
  方向三：**每份反验必须声明它自测的是哪道闸**，且该闸脚本真实存在。
    **没有这条，「反验与闸门的对应关系」就只是散文**——而 Batch 169 已经证明
    散文会过期（方向十一就是为了治它才建的）。
  方向四：**耗时超过阈值的反验必须登记在案**，并写明为何不放进构建。
    **「慢」是一个会悄悄变化的性质**：今天 97 秒，明天上游一大就可能变成 10 分钟。
    **不登记，它就会在某天悄悄越过可接受的界线。**

**刻意不做的事**：本闸**不跑任何用例**。跑用例是 `bash scripts/selftest-*.sh`
的事，那是提交前的动作；**构建期只保证「它至少能启动」**。
**把「能启动」与「跑得对」分开，是这道闸能放进每次构建的前提。**

退出码：0 全部可启动；1 有反验起不来；2 未能核对（找不到 scripts 目录 / 抽出 0 份反验）。
"""

import ast
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baseline import announce_fallback  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")

# 慢反验登记表。
#
# **Batch 180 改的正是这个表**。原样写着「阈值取自实测，不是拍的」——
# **而那个 `SLOW_BUDGET_MS = 30000` 全文件只出现这一次，从没被任何判据读过**：
# 方向四只核「登记了的还在不在」，**从不核「有没有该登记的漏登记了」**。
# **注释在撒谎，而没人发现**——因为注释不产生任何信号。
# 这是纪律 112（「用会变的量当论据之前，先想清楚谁来看着它」）的完整形态：
# **量确实存在，但没有任何机制看着它，于是它等于不存在。**
#
# 改法不是「把 30 改成别的数」——**任何硬编码的秒数都会重蹈覆辙**。
# 改成**由事实推导**：每份慢反验**自己声明实测耗时**，判据核
#  ① 声明的耗时必须真的超过阈值（否则它其实不慢，该从表里删掉）；
#  ② 阈值本身写在表里、且**必须与实测分档对得上**（见 SLOW_BUDGET_SEC）。
# **判据锚的是「谁慢、慢多少」这个可测事实，而不是一个我拍出来的数。**
SLOW_BUDGET_SEC = 30
SLOW = {
    "selftest-zero-input.py": {
        # **Batch 202 把这个数字的来历写清楚，因为它此前一直没人核**
        # （方向四a 只核「是不是正数、是不是 > 30」，**从不核它等于实测值**——
        # 一个从未被核对过的常数，注释里却写着「实测」，见纪律 191）。
        # **82s 是 Batch 202 实施当时的一次快照，不是可复现的值**：
        # 同一天同机交错重测，同一套 25 道闸得 **62.3s / 32.5s**，
        # 单 `verify-unreachable.py` 得 **20.6s / 17.2s**——
        # **绝对值 2 倍漂，连比值都在 1.9～3.0 之间漂**（本机同时有别人的构建在跑）。
        # 所以这里能确定的只有**量级**：「它确实越过 30 秒阈值」，
        # 而 82 这个具体数字**只当历史快照看**。
        # **两次变慢的原因都是同一个，且都不是它多做了什么**：
        # Batch 197 给 `beefsrc` 加了可用的兜底 → 方向三里 7 道闸**回落到真仓把整道闸跑完**；
        # Batch 202 把原本 rc=2 的 2 道闸也接上兜底 → **它们于是也真的跑完了**。
        "seconds": 82,           # 历史快照（方向四a 只看它 > 30，不看它准不准）
        "why": "**它变慢不是因为多了检查，是因为被它核的那些闸不再秒退**——"
        "Batch 197 给 `beefsrc` 加了可用的兜底之后，方向三里 `BEEFTV_SRC` 指向非仓的 7 道闸"
        "**回落到真仓把整道闸跑完**；Batch 202 把原本 rc=2 的 2 道闸也接上兜底，"
        "**它们于是也真的跑完了**。已越过 30 秒阈值（**量级可信，具体秒数不可信，见左侧注释**）。"
        "登记 + 提交前跑——**与另外三份慢反验同一类必要成本**："
        "它核的是「全部闸在两个极端下各自会说什么」，而那只能靠逐道真跑。"
        "**两次变慢都不是它多做了什么，而是被它核的那些闸真的开始做事了。**",
        "anchor": ("selftest-zero-input.py", "def direction_three"),
    },
    # **Batch 208 补登记的两条**：它们此前都在 `SELFTEST_COSTS` 里写着**低报的秒数**
    # （`selftest-quote-punct.py` 登记 11 秒、实测 37.1 秒），于是方向四d
    # 「超过阈值却没登记为慢」**永远看不见它们**——**判据核的正是那个错的数**。
    "selftest-quote-punct.py": {
        "seconds": 38,           # 实测（Batch 208：37.1/30.6 秒，**两次取大**）
        "why": "**它此前登记的是 11 秒，而实测 37.1 秒**——"
               "**低报的方向是唯一危险的那个**：方向四d 用这个数判「你登记为不慢，"
               "到底是不是真的不慢」，而**错的正是这个数本身**，于是判据无从发现。"
               "它是闸 22（引号文案标点漂移）的反验，"
               "而闸 22 要把**四份手册的 900 段引号**逐条回上游语料里找字面出处。",
        "anchor": ("selftest-quote-punct.py", "def m_missing_comma_must_report"),
    },
    "selftest-screenshots-literals.py": {
        "seconds": 31,           # 实测（Batch 208：30.1/24.3 秒，**两次取大**；**恰压 30 秒线，如实记**）
        "why": "**与上一条同一个病**：登记 23 秒、实测 30.1 秒，**刚好越过阈值**。"
               "**这一条是「阈值型守卫」为什么必须取保守方向的最好例子**——"
               "差 0.1 秒，而判据看到的是 23。",
        "anchor": ("selftest-screenshots-literals.py", "def run(manifest_text"),
    },
    "selftest-selftest-bootable.py": {
        # **Batch 209 重测：155.2 秒与 116.0 秒**（两次取大，纪律 204：漂的时候倒向安全那侧）。
        # 此前登记 **68 秒**，而**那个 68 是在用例 9/10 已经作废的状态下测的**——
        # 见下面 why 的最后一段，这是本条最要紧的地方。
        "seconds": 156,
        "why": "每一例都要 `copytree` 整份 `scripts/`（87 个文件）进沙箱再跑一遍闸 18，"
               "**而闸 18 现在还会在沙箱里重放慢反验的夹具前提**。"
               "已越过 30 秒阈值，**放进构建会让每次构建多花三分之一时间**。"
               "登记 + 提交前跑——**这与 `selftest-meta.sh` 是同一类必要成本**："
               "它核的是「反验本身还能不能用」，而反验不在构建路径上。"
               "**登记值此前低报了 88 秒，而低报的方向是唯一危险的那个**（纪律 204）："
               "**「作废的用例」会让反验跑得更快、验得更少**——"
               "用例 9/10 的注入锚点被 Batch 208 那次例行数据刷新弄失效之后，"
               "它们每次都在断言处直接返回，**一秒的闸都不跑**。"
               "**换句话说：那两条用例正是「让这份耗时登记值变好看」的原因。**"
               "已改锚键（锚键不锚值），两条重新真跑，登记值按新实测据实上调。",
        "anchor": ("selftest-selftest-bootable.py", "m_slow_feature_missing"),
    },
    "selftest-unreachable.sh": {
        "seconds": 1500,          # 实测约 25 分钟（Batch 179）
        "why": "走 git plumbing 往上游仓库注入 40 个用例并建临时 ref，"
               "每个用例都要 read-tree / write-tree / commit-tree。"
               "**放进构建会让每次构建多花 25 分钟**。改为登记 + 提交前跑。",
        "anchor": ("selftest-unreachable.sh", "refs/manual-gate-selftest"),
    },
    "selftest-meta.sh": {
        "seconds": 97,            # 实测（Batch 179）
        # **Batch 182 修正了它的登记理由**。原理由写「97 秒 + 会原地改 15 个文件」，
        # 把**风险**当成了**原因**——而实测下来它的安全机制其实是齐的：
        #   · 每例前 `restore`
        #   · `trap 'restore' EXIT`
        #   · 每例核对 15 个文件的 md5 未变（注入空转即作废）
        # **它真的必须原地跑**：它核的是**真实仓**的登记表与侧栏配置，
        # 搬到副本仓就核不到真东西了。**所以 97 秒是必要成本，不是可以优化掉的浪费。**
        "why": "**必须原地跑**——它核的是真实仓的登记表/侧栏/索引，"
               "搬到副本仓就核不到真东西。97 秒是**必要成本**。"
               "安全机制已齐（每例前 restore + trap EXIT + md5 核对），"
               "中途被打断也会还原，不存在「留下脏文件」的实际风险。",
        "anchor": ("selftest-meta.sh", "SNAP_FILES"),
    },



}


# **实测耗时登记表**（Batch 180 新增）。单位：秒，单次实测（含进程启动）。
#
# **为什么需要这张表**：方向四d 要核「没登记为慢的反验，实测是否真的不超过阈值」。
# 而**判据在构建期无法知道谁慢**——除非有人把秒数写进来。
# 于是这里要求：**「我没登记它慢」必须是一个有据的说法，而不是「我没量过它」。**
# 这正是纪律 112 的正面用法：与其指望「量小到大有人在看」，
# 不如**让「没量过」本身成为一个可被看见的状态**。
#
# **怎么维护**：新增反验时跑一次 `time python3 scripts/selftest-<名>.py`，
# 把秒数填进来。**故意留空的值会让构建失败**——
# 因为「空着」和「量过但很快」在账面上长得一模一样，而只有后者是有意义的。
SELFTEST_COSTS = {
    "selftest-baseline.py": 0.7,
    "selftest-batch-rows.py": 0.1,
    "selftest-beefsrc.py": 0.3,
    "selftest-deadlinks.py": 0.2,
    "selftest-encoding.py": 0.2,
    "selftest-endpoints.py": 0.8,
    "selftest-error-copy.py": 0.8,
    "selftest-exclusions.py": 1.6,
    "selftest-feature-flags.py": 0.4,
    "selftest-label-drift.py": 1.9,
    "selftest-ledger-refs.py": 0.3,
    "selftest-line-counts.py": 4.8,
    "selftest-quote-punct.py": 37.1,
    "selftest-runtime-policy.py": 1.0,
    "selftest-scope.py": 0.4,
    "selftest-screenshots-literals.py": 30.1,
    "selftest-screenshots.py": 0.7,
    "selftest-selftest-bootable.py": 156.0,   # Batch 209 重测：155.2 / 116.0 秒（**两次取大**）
    "selftest-selftest-deps.py": 0.7,
    "selftest-shortcuts.py": 0.7,
    "selftest-shot-drift.py": 10.0,
    "selftest-shot-pixels.py": 7.1,
    "selftest-shot-version.py": 0.8,
    "selftest-tables.sh": 0.8,
    "selftest-zero-input.py": 42.1,
}


# 注入夹具的命名形态：`selftest-<闸>-fix-<序号>-<说明>.py`。
# **它们不是反验**——只是 stdin→stdout 的文本变换器，被反验调用一次。
# 上线首跑时我把 58 份夹具全当成反验、报出 58 处「没有指向被测闸门」——
# **这正是「把两类同名文件当成一类」的错误**。它们的名字都叫 `selftest-*`，
# 光看前缀分不出来，**必须靠 `fix-` 这个中段**。
# （纪律 109：分类判据要锚可观测事实。这里可观测的事实就是文件名里的 `fix-`。）
FIXTURE_RE = re.compile(r"^selftest-(?:[a-z0-9]+-)?fix-[a-z0-9]+-")

# 标准库：这些 import 不需要在本仓 scripts/ 下存在
STDLIB = set("""abc argparse ast base64 collections contextlib copy csv dataclasses datetime
difflib enum errno filecmp fnmatch functools glob hashlib io itertools json logging math mimetypes
os pathlib platform random re shlex shutil subprocess sys tempfile textwrap time typing unittest
urllib uuid warnings""".split())


def _looks_third_party(mod):
    """这个名字像不像第三方库。

    **为什么这里必须收紧**（反验用例 5 上线首跑就漏报了）：第一版写的是
    「不以下划线开头就算第三方」——于是注入的 `nosuchmodule` 被放过。
    但本仓**不装任何第三方依赖**，所以凡是能 import 成功的非标准库必然是本仓自己的模块；
    剩下那些 import 不了的，**几乎总是笔误而不是库**。
    **判据取严：只放过明确的内置/特殊名，其余一律要求文件存在。**
    误伤一个真第三方库的成本，远小于放过一个笔误——
    **因为笔误的代价是「反验静默失效」，而误报的代价只是多写一个 STDLIB 条目。**
    """
    return mod in ("__future__", "builtins")



def _extract_fn(src, name):
    """把 `build-site.sh` 里的某个 shell 函数**原样抠出来**。

    **为什么不 source 整份脚本**：一 source 它就真的开始建站。
    抠到**行首的单个 `}`** 为止；单行函数（`fail`）就地结束。
    **抠不出来就抛**——让用例作废，而不是拿一个空串继续跑：
    作废的反验比失败的反验更危险，因为它连报红都不报（纪律 178）。
    """
    # **空白不能写死**：`log()` 在脚本里写成 `log()  {`（两个空格），
    # 而 `fail()` 是单行体——两种形态都得抠得出来。
    m = re.search(r"\n%s\(\)\s*\{" % re.escape(name), src)
    assert m, "build-site.sh 里找不到函数 %s" % name
    start = m.start()
    head_end = src.find("\n", start + 1)
    head = src[start + 1:head_end]
    if head.rstrip().endswith("}"):
        return head + "\n"
    end = src.find("\n}\n", head_end)
    assert end > head_end, "函数 %s 找不到行首的收尾花括号" % name
    return src[start + 1:end + 3]


def _run_gate_probe(stub_rc):
    """**把 `build-site.sh` 的真 `run_gate` 抠出来跑一遍**，问它一道指定退出码的闸会怎样。

    **为什么不 grep 判写法**：`out="$(...)"` 后面跟不跟 `|| rc=$?` 是写法，
    而「闸失败时构建到底说不说话」是事实（纪律 171）。
    **行为可判、写法不可判**，所以这里用真函数 + stub 闸真跑一遍。
    返回 `(rc, 输出)`；输出含 ANSI 颜色码，判断时只找中文文案。
    """
    with open(os.path.join(ROOT, "build-site.sh"), encoding="utf-8") as fh:
        src = fh.read()
    fns = "".join(_extract_fn(src, n) + "\n\n" for n in ("log", "ok", "warn", "fail", "run_gate"))
    tmp = tempfile.mkdtemp(prefix="run-gate-probe.")
    try:
        os.makedirs(os.path.join(tmp, "scripts"), exist_ok=True)
        with open(os.path.join(tmp, "scripts", "stub.py"), "w", encoding="utf-8") as fh:
            fh.write("import sys\nprint('闸的输出：某某与手册对不上')\n"
                     "print('第二行')\nsys.exit(%d)\n" % stub_rc)
        probe = ('set -euo pipefail\nTS="00:00:00"\n' + fns + 'run_gate "stub.py" "试闸"\n')
        p = os.path.join(tmp, "probe.sh")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(probe)
        r = subprocess.run(["bash", p], cwd=tmp, capture_output=True, text=True, timeout=60)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


#: `$var` 后面**紧跟**一个非 ASCII 字符（Batch 205）。
#: **为什么要盯这个**：macOS 自带的 bash 3.2 在 UTF-8 locale 下
#: 会把那些字节算进变量名，于是报「`desc?: unbound variable`」——
#: **而 `desc` 明明上一行刚 `local` 过**。实测同一份脚本、同一台机器，
#: `LC_CTYPE=C.UTF-8` 时 0/5 通过，不设时 5/5 通过。
#: **这不是编码问题，是变量名边界问题**；`${var}` 是唯一可靠写法。
UNSAFE_VAR_RE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")


def _shell_files():
    out = [os.path.join(ROOT, "build-site.sh")]
    for fn in sorted(os.listdir(SCRIPTS)):
        if fn.endswith(".sh"):
            out.append(os.path.join(SCRIPTS, fn))
    return [p for p in out if os.path.isfile(p)]


def _locale_breaks_it():
    """**这个判据在本机真的成立吗**——用一段最小样例自己问一遍 bash。

    **样例必须带 `set -u`**：不设它时 `$desc：` 只是被切成一个不存在的变量名、
    展开成空串，**照样 rc=0 打印出来**——第一版探针就漏了它，
    于是它自报「本机实测不复现」，**而真实脚本全都有 `set -u`，一设就炸**。
    **一个不忠实的探针，会让判据给出「它不存在」这个错误结论**（纪律 176 的变体：
    结论错，而理由也对不上）。


    **不这么做的话，这条判据就是一条 superstition**：
    它断言「这种写法会炸」，而本批只在一台机器的一个 bash 上量过一次。
    所以现场跑：设 `LC_CTYPE=C.UTF-8` 执行 `$v：`，**看它是不是真的会报未绑定**。
    返回 `(会不会坏, bash 版本第一行)`——**两样都写进报红信息里**。
    """
    code = ("set -u" + "\n"
            'f() { local desc="值"; echo "$desc：后面"; }' + "\n"
            "f" + "\n")
    try:
        # **errors="replace" 不是可选的**：这条路径上 bash 吐出来的就是坏字节
        # （变量名被切坏之后，错误信息里带着切剩的字节），
        # 而子进程解码失败会让判据自己崩掉——**判据崩了比判据红更难看**。
        r = subprocess.run(["bash", "-c", code], capture_output=True, text=True,
                           errors="replace",
                           env=dict(os.environ, LC_CTYPE="C.UTF-8"), timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None, "?"
    broke = "unbound variable" in ((r.stdout or "") + (r.stderr or ""))
    ver = subprocess.run(["bash", "--version"], capture_output=True, text=True,
                         errors="replace")
    return broke, ((ver.stdout or "").split("\n") or ["?"])[0]


def _build_invokes(fn):
    """build-site.sh **真的执行**了这份反验吗（注释里提到不算）。

    **只看代码、不看注释**（方向四c 上线首跑就误报，Batch 180）：
    `build-site.sh` 的注释里正写着 `selftest-unreachable.sh` 与 `selftest-meta.sh`
    的名字和实测秒数——那是**给人看的说明**，而字面匹配把它们当成了调用。
    **注释不是调用点**，与闸 7「URL 写出点只看代码不看注释」同源。
    """
    path = os.path.join(ROOT, "build-site.sh")
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().split("\n")
    except OSError:
        return False
    for line in lines:
        if line.lstrip().startswith("#"):
            continue
        if fn in line:
            return True
    return False


#: 反验引用的同层文件名（`selftest-*.py|sh` 与 `verify-*.py`）。
#: **刻意不匹配 glob 形态**：`selftest-*.py`、`selftest-fix-*-fixture.py` 里
#: 那个 `*` 不在字符类里，所以**通配写法不会被当成一个真实文件名**。
DANGLING_RE = re.compile(r"\b((?:selftest|verify)-[A-Za-z0-9._-]+\.(?:py|sh))\b")


def _code_only(path):
    """只留真正会被执行到的字面量：Python 用 AST 剥注释与文档字符串，shell 剥 `#` 注释。

    **与 `verify-meta.py` 的同名函数同一套做法**（方向十一的「驱动按事实判定」
    就靠它）。**重复而不共用是有意的**：闸之间互相 import 会让任一方坏掉时
    另一方跟着起不来——**那正是 Batch 178 记的那次失效**。
    """
    src = open(path, encoding="utf-8", errors="ignore").read()
    if path.endswith(".py"):
        tree = ast.parse(src)
        docs = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef,
                                 ast.AsyncFunctionDef, ast.ClassDef)):
                b = getattr(node, "body", None)
                if b and isinstance(b[0], ast.Expr) and \
                        isinstance(b[0].value, ast.Constant) and \
                        isinstance(b[0].value.value, str):
                    docs.add(id(b[0].value))
        return "\n".join(n.value for n in ast.walk(tree)
                         if isinstance(n, ast.Constant) and isinstance(n.value, str)
                         and id(n) not in docs)
    return "\n".join(re.sub(r"#.*$", "", ln) for ln in src.split("\n"))


def _deleted_sibling_names():
    """`scripts/` 下**历史上删掉过、现在已不在场**的文件名集合。

    **取不到就返回 `None`（核不了），而不是空集合（没有问题）**——
    纪律 203：一个不记账的「跳过」会让「没查」看起来像「查了没成」。

    **为什么用 git 删除历史，而不是「这个名字看着像不像夹具」**：
    第一版按名字收窄（只认 `selftest-fix-*`）也试过，实测**漏掉真事故**——
    事故那个名字是 `selftest-fix-2-…`，能认出来，可判据一旦这么写，
    下一个被删的夹具换个命名就又漏了。**「删过」是事实，「像什么」是约定**（纪律 101）。
    """
    r = subprocess.run(
        ["git", "-C", ROOT, "log", "--diff-filter=D", "--name-only", "--format=",
         "--", "scripts"],
        capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return None
    return {os.path.basename(ln.strip()) for ln in r.stdout.split("\n")
            if ln.strip() and ln.strip().endswith((".py", ".sh"))}


def is_fixture(fn):
    return bool(FIXTURE_RE.match(fn))


def selftests():
    """只返回**真正的反验**，排除注入夹具。"""
    out = []
    for fn in sorted(os.listdir(SCRIPTS)):
        if not fn.startswith("selftest-"):
            continue
        if not (fn.endswith(".py") or fn.endswith(".sh")):
            continue
        if is_fixture(fn):
            continue
        out.append(fn)
    return out


def fixture_count():
    return sum(1 for fn in os.listdir(SCRIPTS)
               if fn.startswith("selftest-") and is_fixture(fn))


def _imported_modules(path):
    """这份反验**真的 import 了**哪些顶层模块名。

    **为什么是 import 而不是「文本里出现过这个名字」**（Batch 198 实测的两次假阴性）：
    第一版按文本匹配，**模块 docstring 与 `print()` 里的一句说明就足以骗过它**——
    实测把 `import beefsrc` 整行删掉、文档一字不改，判据照样报绿。
    收窄到「剥掉注释与文档字符串后，**AST 里真的有一条 import 语句**」才抓得住。
    这与方向三原有的闸名判据是同一类收紧：**认事实，不认写法**。
    """
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            tree = ast.parse(fh.read())
    except (OSError, SyntaxError):
        return set()
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                out.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            out.add(node.module.split(".")[0])
    return out


def _shared_modules():
    """`scripts/` 下**不是闸、也不是反验**，且**至少被一道闸 import 过**的本地模块。

    **为什么要现算而不是列名单**：名单是人维护的，会与现实脱节，
    而脱节的方向永远是「多了一条没人管的名字」或「少了一条真被依赖的模块」。
    事实判据只有一条：**它被某道闸 import**——
    **被闸依赖的模块坏掉，影响面就是它依赖它的那些闸**，这个影响面是算得出来的。
    """
    out = set()
    try:
        files = os.listdir(SCRIPTS)
    except OSError:
        return out
    gates = [f for f in files if f.startswith("verify-") and f.endswith(".py")]
    bodies = []
    for g in gates:
        try:
            with open(os.path.join(SCRIPTS, g), encoding="utf-8") as fh:
                bodies.append(fh.read())
        except OSError:
            continue
    for f in files:
        if not f.endswith(".py") or f.startswith(("verify-", "selftest-")):
            continue
        mod = f[:-3]
        pat = re.compile(r"^\s*(?:import\s+%s\b|from\s+%s\s+import)" % (re.escape(mod), re.escape(mod)),
                         re.M)
        if any(pat.search(b) for b in bodies):
            out.add(mod)
    return out


def _unreachable_cases():
    """`selftest-unreachable.sh` 的 `(说明, 上游路径, 夹具, 特征)` 四元组。

    **用 `shlex` 而不是正则**（Batch 201 实测）：那个脚本里
    `feature` 参数**单双引号混用**（用例 21/23 写的是 `'inGroup("more")'`），
    正则只能认出 20 个用例，而实际有 34 个——
    **少认 14 个还报得很绿，正是判据认写法而不认事实的形态**。
    `shlex` 走的是 shell 自己的词法，两种引号一视同仁。
    """
    import shlex as _shlex
    out = []
    for line in open(os.path.join(SCRIPTS, "selftest-unreachable.sh"),
                     encoding="utf-8"):
        st = line.strip()
        if not (st.startswith("run_case ") or st.startswith("run_pass_case ")):
            continue
        argv = _shlex.split(st)
        if len(argv) >= 5:
            # **第 6 个实参是这条用例指向的断言 id**（Batch 207 补取）——
            # 它本来就在命令行上，只是没人取，于是「用例指向的断言还在不在闸里」无从问起。
            out.append((argv[1], argv[2], argv[3].replace("$HERE", SCRIPTS), argv[4],
                        argv[5] if len(argv) >= 6 else ""))
    return out


def _registered_assertions():
    """闸 7 的登记表里**真正登记着**的断言 id 集合。

    **只认代码，不认注释**（与方向四c 同一纪律）：`canvas-library-no-import-entry`
    在 `verify-unreachable.py` 里**只剩一行注释**——
    上游修好之后断言被删了，**可那条注释还留着**。
    纯字面匹配会把它算成「还在」，于是 Batch 207 这条判据第一次跑就报绿。
    """
    path = os.path.join(SCRIPTS, "verify-unreachable.py")
    out = set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            st = line.strip()
            if not st or st.startswith("#"):
                continue
            for m in re.finditer(r'"([a-z0-9][a-z0-9-]*)"', st):
                out.add(m.group(1))
    return out


def _slow_fixture_triples(script_name):
    """从慢反验脚本里抽出 `(目标文件, 夹具)` 三元组。

    **刻意只抽注入夹具这一步，不跑闸**：一个用例会不会作废，
    取决于「夹具能不能命中它的锚点」，而这一步**不跑任何闸**——
    实测 23 个三元组重放一遍只要 **0.6 秒**，而整个慢反验要 97 秒（快 160 倍）。
    """
    import re as _re
    text = open(os.path.join(SCRIPTS, script_name), encoding="utf-8").read()
    return [(_t.replace("$HERE", SCRIPTS), _f.replace("$HERE", SCRIPTS))
            for _t, _f in _re.findall(
                r'run_file_(?:case|pass_case)\s+"[^"]*"\s*\\?\s*\n?\s*"([^"]+)"\s+"([^"]+)"',
                text)]


def main():
    announce_fallback()
    if not os.path.isdir(SCRIPTS):
        print(f"[skip] 找不到 {SCRIPTS}，跳过反验启动核对")
        return 2
    names = selftests()
    if not names:
        print("[skip] scripts/ 下没有找到任何反验——判据可能已失效")
        return 2

    problems = []
    py_ok = sh_ok = fx_ok = 0
    # **夹具也要过语法检查**：它们语法坏了，被调用的反验同样起不来/判定作废，
    # 而 Batch 178 那一类失效恰恰是「没人跑所以没人知道」。
    for fn in sorted(os.listdir(SCRIPTS)):
        if not (fn.startswith("selftest-") and is_fixture(fn) and fn.endswith(".py")):
            continue
        try:
            with open(os.path.join(SCRIPTS, fn), encoding="utf-8") as fh:
                ast.parse(fh.read())
            fx_ok += 1
        except SyntaxError as exc:
            problems.append(
                f"方向一：注入夹具 {fn} 语法错误，调用它的反验会作废该用例：{exc}")

    for fn in names:
        p = os.path.join(SCRIPTS, fn)
        if fn.endswith(".py"):
            # 方向一：语法必须能被解释器接受（能启动的前提）
            try:
                with open(p, encoding="utf-8") as fh:
                    ast.parse(fh.read())
                py_ok += 1
            except SyntaxError as exc:
                problems.append(f"方向一：{fn} 语法错误，反验根本起不来：{exc}")
                continue
            # 方向二：它 import 的本地模块必须真实存在且能 import
            try:
                with open(p, encoding="utf-8") as fh:
                    tree = ast.parse(fh.read())
            except OSError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and not node.level and node.module:
                    mod = node.module.split(".")[0]
                    if mod in STDLIB or _looks_third_party(mod):
                        continue
                    if not os.path.isfile(os.path.join(SCRIPTS, mod + ".py")):
                        problems.append(
                            f"方向二：反验 import 了 `{mod}`，但 scripts/{mod}.py 不存在"
                            "　→ 反验**起不来且没有任何其他信号**")
                        continue
                    r = subprocess.run(
                        [sys.executable, "-c",
                         "import sys; sys.path.insert(0, %r); import %s" % (SCRIPTS, mod)],
                        capture_output=True, text=True)
                    if r.returncode != 0:
                        problems.append(
                            f"方向二：反验 import 的本地模块 {mod} **在真实环境里也 import 不了**："
                            f"{(r.stderr or '').strip().splitlines()[-1][:90]}")
        else:
            # 方向一：shell 反验必须通过 `bash -n`（只查语法，不执行）
            r = subprocess.run(["bash", "-n", p], capture_output=True, text=True)
            if r.returncode != 0:
                problems.append(
                    f"方向一：{fn} 没通过 `bash -n`，反验起不来："
                    f"{(r.stderr or '').strip()[:90]}")
                continue
            sh_ok += 1

    # 方向二之二：**被测闸门** import 的本地模块必须真的能 import。
    # 现场数据（Batch 179 实测）：**没有任何一份反验自己 import 本地模块**——
    # 它们只是把闸门**复制**进临时目录。所以 Batch 178 那 34 例的失败面
    # 并不在「反验起不来」，而在「**反验复制过去的闸门起不来**」。
    # **第一版判据核错了对象**：它去查反验的 import，于是既漏报了真问题、
    # 又让人以为闸 18 已经覆盖了 Batch 178 那次失效。**核错对象等于没核。**
    for gate_fn in sorted(os.listdir(SCRIPTS)):
        if not (gate_fn.startswith("verify-") and gate_fn.endswith(".py")):
            continue
        path = os.path.join(SCRIPTS, gate_fn)
        try:
            with open(path, encoding="utf-8") as fh:
                gtree = ast.parse(fh.read())
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(gtree):
            if isinstance(node, ast.ImportFrom) and not node.level and node.module:
                mod = node.module.split(".")[0]
                if mod in STDLIB or _looks_third_party(mod):
                    continue
                if not os.path.isfile(os.path.join(SCRIPTS, mod + ".py")):
                    problems.append(
                        f"方向二之二：闸门 {gate_fn} import 了 `{mod}`，但 scripts/{mod}.py 不存在"
                        "　→ **任何**跑它的反验都会起不来（Batch 178 实测 34 例）")
                    continue
                r = subprocess.run(
                    [sys.executable, "-c",
                     "import sys; sys.path.insert(0, %r); import %s" % (SCRIPTS, mod)],
                    capture_output=True, text=True)
                if r.returncode != 0:
                    problems.append(
                        f"方向二之二：闸门 {gate_fn} 依赖的本地模块 {mod} import 不了："
                        f"{(r.stderr or '').strip().splitlines()[-1][:90]}")

    # 方向三：每份反验都要能说出自己测的是哪道闸（或哪个被闸依赖的共享模块）
    #
    # **Batch 198 扩了「或哪个共享模块」**：本批给 `beefsrc.py` 配反验时撞上的——
    # `beefsrc` 是 15 道闸共同依赖的路径解析模块，**它不是闸，也不对应任何一道闸**，
    # 而原判据只认 `verify-*.py`，于是它报「找不到被测闸门」。
    # 扩法的关键是**那个集合是算出来的、不是名单**：
    # 「`scripts/` 下不是 verify-/selftest- 的 .py，且**至少被一道闸 import 过**」——
    # **`beefsrc` 改坏时 15 道闸一起失效，这就是「它值得有反验」的事实依据**，
    # 而不是一个我随手维护的白名单（那正是纪律 101 的形态）。
    # 认闸名、认模块名都是「按写法判定」的老毛病；**判据认的仍然是事实**。
    shared = _shared_modules()
    for fn in names:
        p = os.path.join(SCRIPTS, fn)
        try:
            with open(p, encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            continue
        if re.search(r"verify-[a-z0-9-]+\.py", text):
            continue
        if shared & _imported_modules(p):
            continue
        problems.append(
            f"方向三：{fn} 里找不到任何 verify-*.py 的引用，"
            f"也没有提到被闸依赖的共享模块（现有：{'、'.join(sorted(shared)) or '无'}）"
            "　→ 它没有指向被测对象；「反验 ↔ 闸」的对应关系会退化成散文"
            "（Batch 169 方向十一治的正是这个）")

    # 方向四：慢反验登记表**双向**自证（Batch 180 改）
    #
    # **原来只有一个方向**：核「登记了的，理由是否仍成立」。
    # 漏掉的是「**该登记的没登记**」——于是 `SLOW_BUDGET_MS` 那个阈值
    # **从来没被读过**，却在上方注释里写着「取自实测，不是拍的」。
    # **注释在撒谎，而撒谎不产生任何信号。**
    #
    # 改成三个方向：
    #   ④a 登记项确实存在，且**声明的耗时真的超过阈值**（否则它其实不慢，该删）；
    #   ④b 登记理由点名的判据仍在上游（原有那条，保留）；
    #   ④c **反向**：每份反验若被 build-site.sh 自动调用，就**不该**出现在慢表里
    #       （能自动跑还登记成「只能手动跑」，说明登记过期了）。
    # **④c 是可静态判的**：build-site.sh 里出现了它的名字就是「会自动跑」。
    for fn, info in SLOW.items():
        path = os.path.join(SCRIPTS, fn)
        if not os.path.isfile(path):
            problems.append(f"方向四a：SLOW 里登记了 {fn}，但它不存在（登记已过期，请删）")
            continue
        # ④a：声称慢，就得真的超过阈值
        secs = info.get("seconds")
        if not isinstance(secs, (int, float)) or secs <= 0:
            problems.append(
                f"方向四a：{fn} 的登记里没有正的 seconds 字段"
                "　→ 判据无法核「它到底慢不慢」，等于这张表不受任何约束")
        elif secs <= SLOW_BUDGET_SEC:
            problems.append(
                f"方向四a：{fn} 登记为慢反验（{secs}s），但没超过阈值 {SLOW_BUDGET_SEC}s"
                "　→ 它其实不慢（或阈值该调了），请从表里删掉或更新实测值")
        src, needle = info["anchor"]
        probe = os.path.join(SCRIPTS, src)
        try:
            with open(probe, encoding="utf-8") as fh:
                body = fh.read()
        except OSError:
            problems.append(f"方向四b：{fn} 的登记理由点名了 {src}，但读不到它")
            continue
        if needle not in body:
            problems.append(
                f"方向四b：{fn} 的登记理由点名了 {src} 里的 {needle!r}，但那里已没有它"
                "　→ 登记理由失效，**要么它其实不慢了（该放进构建），要么理由要重写**")
        # ④c：能被构建自动调用的反验，不该登记成「只能手动跑」
        # **只认真正执行的代码，不认注释**（上线首跑就误报，Batch 180）：
        # `build-site.sh` 的注释里**正写着**这两个反验的名字与实测秒数
        # （那是给人看的说明），而纯字面匹配把它们当成了「已被自动调用」。
        # **注释不是调用点**——与闸 7「URL 写出点只看代码不看注释」同一条纪律。
        if _build_invokes(fn):
            problems.append(
                f"方向四c：{fn} 已登记为「慢、只能手动跑」，"
                "但 build-site.sh **真的执行**了它（注释里提到不算）"
                "　→ 登记与现实脱节；要么去掉登记，要么把它从构建里拿掉，二者必须一致")

    # ④d（**本批新增，也是最重要的一条**）：反向核对**没有漏登记**。
    # 为什么这条只能靠人工跑：判据无法在构建期知道谁慢——
    # **除非有人把实测值写进来**。所以本闸要求：
    # **凡是在 SLOW 里没登记、也没被 build-site.sh 自动调用的反验，
    # 必须在 `SELFTEST_COSTS` 里留下一条实测耗时**。
    # 换句话说：**「我没登记它慢」必须是一个有据的说法，而不是「我没量过它」。**
    # 这正是纪律 112 的正面用法：**与其要求量小到大有人在看，
    # 不如让「没量过」本身成为一个可被看见的状态。**
    known = set(SLOW)
    auto = set(fn for fn in names if _build_invokes(fn))
    for fn in sorted(set(names) - known - auto):
        cost = SELFTEST_COSTS.get(fn)
        if cost is None:
            problems.append(
                f"方向四d：反验 {fn} 既没登记为慢、也没被构建自动调用，"
                "**且 `SELFTEST_COSTS` 里没有它的实测耗时**"
                "　→ 「我没登记它慢」现在等于「我没量过它」；"
                "跑一次（多数只需几秒到几十秒）把秒数填进去即可")
        elif cost > SLOW_BUDGET_SEC:
            problems.append(
                f"方向四d：反验 {fn} 实测 {cost}s，**超过阈值 {SLOW_BUDGET_SEC}s 却没登记为慢**"
                "　→ 这正是原判据漏掉的那一整类：新反验变慢时无人提醒")

    # ── 方向五（Batch 200）：慢反验的注入夹具**必须还能命中它的锚点** ──
    #
    # **为什么需要它**（Batch 198 实测到的形态）：
    # `selftest-meta.sh` 跑出来是「通过 34 / 失败 0 / **作废 2**」——
    # 而作废的两条是**方向十一最要紧的两条**。作废的成因是夹具的锚点断言失配，
    # 而那一步**不跑闸、只要 0.6 秒**。**没人跑慢反验，于是没人知道那两条用例
    # 早就在「什么都不验」的状态里待了很久**（纪律 178）。
    # 本方向让这件事进构建：**97 秒的东西里，只有 0.6 秒那一段与「有没有在验」有关。**
    #
    # **边界必须写清楚**：
    #   · **只查前提，不查结果**——「夹具能不能命中锚点」≠「用例会不会通过」；
    #   · **只覆盖 `selftest-meta.sh`**——`selftest-unreachable.sh` 的注入目标是
    #     **上游仓里那个 ref 上的文件**（它先走 git plumbing 造合成 ref），
    #     重放成本与 97 秒那一段同量级，**本方向不覆盖，如实记在这里**。
    # **目标文件不在场就跳过，而不是报问题**——前提无法评估 ≠ 判为失败
    # （闸 9 方向一已经负责「基本输入存在性」）。这一条也是反验沙箱能用的前提：
    # 沙箱只搬 `scripts/`，根目录的 `AUDIT-RULES.md` 本来就不在里面。
    fx_checked, fx_skipped, fx_void = 0, 0, []
    for target, fixer in _slow_fixture_triples("selftest-meta.sh"):
        if not os.path.isfile(fixer) or not os.path.isfile(target):
            fx_skipped += 1
            continue
        try:
            with open(target, encoding="utf-8") as fh:
                r = subprocess.run([sys.executable, fixer], stdin=fh,
                                   capture_output=True, text=True, timeout=30)
        except OSError as exc:
            fx_void.append((os.path.basename(fixer), str(exc)[:60]))
            continue
        fx_checked += 1
        if r.returncode != 0:
            tail = (r.stderr or "").strip().splitlines()
            fx_void.append((os.path.basename(fixer),
                            (tail[-1] if tail else "无输出")[:70]))
    if not _slow_fixture_triples("selftest-meta.sh"):
        problems.append(
            "方向五：**从 `selftest-meta.sh` 里抽不出任何注入夹具三元组**——"
            "要么它的用例调用格式变了，要么整份脚本被清空"
            "　→ **「一个都没检查」与「全部都检查了」必须长得不一样**（纪律 156/159）")
    for fixer, why in fx_void:
        problems.append(
            f"方向五：慢反验的夹具 `{fixer}` **已经打不中它的锚点**（{why}）——"
            "用到它的用例会**作废**，而作废的输出说的是「前提不成立」，"
            "**它不算通过也不算失败**"
            "　→ 用例正在「什么都不验」：锚点多半是文件里某段被改写的文本，"
            "**要么改夹具的锚，要么改那段文本**")

    # ── 方向五之二（Batch 201）：第二份慢反验的两个作废条件 ──────────────
    #
    # **它比方向五多一个条件**：`selftest-unreachable.sh` 的每条用例有
    # **两个**会作废的点（脚本里各有一行 `VOID=$((VOID+1))`）：
    #   ① **合成 ref 失败**——夹具处理不了目标文件；
    #   ② **合成 ref 里找不到「修复特征」**——夹具跑了，但它没真的注入那个特征。
    # **两个都不需要那套 git plumbing**：`build_ref` 的内容来自
    # `git show origin/main:<path> | python3 <夹具>`，
    # **而 plumbing 只是为了产出一个 commit**——前提校验用不到它。
    # 实测 34 个用例重放一遍 **2.1 秒**，而整个慢反验约 25 分钟（快 700 倍）。
    #
    # **刻意用 `origin/main` 而不是手册声明的基线**：慢反验自己就是从
    # `origin/main` 造合成 ref 的，**用别的 ref 重放就答不上
    # 「我下次真跑它会不会作废」这个问题**。代价是上游一动这条方向就可能变红，
    # **而那正是它该说的话**（上游改了路径 → 那条用例会作废 → 去改夹具）。
    # **上游取不到就跳过，不是失败**——前提无法评估 ≠ 判为失败。
    ur_checked, ur_skipped, ur_void = 0, 0, []
    _cases = _unreachable_cases()
    if not _cases:
        problems.append(
            "方向五之二：**从 `selftest-unreachable.sh` 里一个用例都解析不出来**——"
            "要么调用格式变了，要么脚本被清空"
            "　→ **「一个都没检查」与「全部都检查了」必须长得不一样**（纪律 156/159）")
    _up = None
    try:
        sys.path.insert(0, SCRIPTS)
        import beefsrc
        _up, _ = beefsrc.resolve_src()
    except Exception:                                    # noqa: BLE001
        _up = None
    if _up is None:
        ur_skipped = len(_cases)
    else:
        registered = _registered_assertions()
        _gone = 0
        _labels = 0
        for desc, path, fixer, feature, assertion in _cases:
            # **第四个参数不一定是指向登记表的 id**（Batch 207 实测）：
            # 34 条里有若干条写的是**闸 7 输出里那句中文标签**（如「9 个参数零写出」，
            # 它来自扫描型检查，根本不在 REGISTRY 里）。**把它们一律当成 id 去核，
            # 就会造出 3 条假阳性**——而假阳性会让人学会忽略这条判据（纪律 166）。
            # 所以：**形态不是 id 的就跳过，并如实报出跳过了几条**——
            # **判据核不了的东西必须说出来，而不是装作核过了。**
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", assertion or ""):
                _labels += 1
                # **必须计入「跳过」**（Batch 207 当场修的记账漏洞）：
                # 不计的话汇总行会写成「30/33 成立、**0 个跳过**」，
                # **读起来像 3 条前提不成立**——而它们只是本判据核不了。
                # **一个不记账的跳过，会让「没查」看起来像「查了没成」。**
                ur_skipped += 1
                continue
            if assertion not in registered:
                # **前提成立、夹具跑得通，可这条用例永远不可能过**——
                # 因为它指向的断言**已经不在闸的登记表里了**。
                # 症状是「闸门**未**报失效」，**读起来像闸坏了**，
                # 而真相是「被测的东西被删了，而用例没跟着删」。
                _gone += 1
                ur_void.append((desc[:26],
                                "它指向的断言 `%s` 已不在 `verify-unreachable.py` 的登记表里" % assertion))
                continue
            if not os.path.isfile(fixer):
                ur_void.append((desc[:26], "夹具文件不存在"))
                continue
            show = subprocess.run(["git", "-C", _up, "show", "origin/main:" + path],
                                 capture_output=True, text=True, errors="replace")
            if show.returncode != 0:
                ur_void.append((desc[:26], "读不到 origin/main:%s" % path))
                continue
            r = subprocess.run([sys.executable, fixer], input=show.stdout,
                               capture_output=True, text=True, errors="replace",
                               timeout=30)
            if r.returncode != 0:
                tail = (r.stderr or "").strip().splitlines()
                ur_void.append((desc[:26],
                                "夹具失败：" + (tail[-1] if tail else "?")[:50]))
                continue
            ur_checked += 1
            if feature not in r.stdout:
                ur_void.append((desc[:26],
                                "变换结果里找不到「修复特征」[%s]" % feature[:24]))
    if _gone:
        print("方向五之二：%d 条用例指向的断言**已从闸里删掉**——"
              "前提成立、夹具跑得通，而它们永远不可能过。" % _gone)
        print("  → **删用例，别改闸**：断言没了是因为上游真的修了，"
              "把它加回闸等于把一条已经失效的声明重新立起来。")
    if _labels:
        print("  （另有 %d 条用例的第四个参数是**中文标签**而不是登记表 id，"
              "本判据核不了它们——**如实报出，不装作核过了**）" % _labels)
    for desc, why in ur_void:
        problems.append(
            f"方向五之二：慢反验 `{desc}` 的前提已不成立（{why}）——"
            "**这条用例会作废，而作废的用例什么都不验却不算失败**（纪律 178）"
            "　→ 上游 `origin/main` 改了这段内容或路径：要么改夹具的锚，"
            "要么把该用例移到不再成立的位置")

    # 方向十五（**Batch 209 新增**）：反验引用的**被删掉的**同层文件必须清干净。
    #
    # **背景是一次实测事故，不是推演**：Batch 207 删掉了注入夹具
    # `selftest-fix-2-import-entry.py`，写在账本里的理由是
    # 「**它只被这一条用**」——**而这个理由从来没被核过**：
    # 闸 18 自己的反验 `selftest-selftest-bootable.py` 也引用它。
    # 于是那条用例一跑就 `FileNotFoundError`，
    # 而**反验不在构建路径上**（闸 18 明确写下的设计前提），**账面全绿**。
    # Batch 209 第一次真跑那份反验就撞上了，**而且撞出来的形态比 Batch 207 那次更隐蔽**：
    # 那份反验的 `main()` 只接 `AssertionError`，别的异常一路抛到解释器顶端，
    # 于是**已经跑完的 19 例结果一行都没打印**，整份报告只剩一行 Traceback——
    # **「20 例全过」与「一份报告都没交出来」在退出码上都是非 0，肉眼分不开。**
    #
    # ── **第一版被判据自己的数据推翻，这里必须写下来** ──
    # 第一版核的是「反验代码里引用的每个同层文件名都得在场」。
    # **它一次跑出 10 条，其中 9 条是假的**：注入夹具**本来就该**引用现场不存在的名字
    # （`write(os.path.join(tmp, "scripts", "selftest-orphan.py"))` 是把文件**造出来**，
    #  `s.replace('verify-tables.py', 'verify-foo.py')` 是往**别的文件的内容里**注入字符串，
    #  而 `| scripts/verify-injected.py（并不存在） |` 是**写进手册的表格文本**）。
    # **假阳性率 9/10 的判据不能上线**（纪律 166：首跑全红同样不是证据）。
    #
    # ── **收窄的依据是一个量出来的分界，不是拍脑袋** ──
    # 逐个查那 10 个名字在 git 历史里的下落，结果是**分得干干净净的**：
    # **10 个里只有 1 个真的存在过**（`selftest-fix-2-import-entry.py`，正是事故主角），
    # **其余 9 个从未存在过**——它们是注入夹具**带进来**的名字，不是**丢掉的**引用。
    # 于是判据收窄成「**只报曾经存在过、现在不在场的名字**」：
    # **它精确对准这次事故的形态（被删的引用），实测假阳性 0/9。**
    # **代价也要写清楚**：引用一个**从未存在过**的错名字（打错字、写错版本号）本方向看不见。
    # **判据的盲区要自己写出来，否则下游会把它当成事实**（纪律 196）。
    dang = _deleted_sibling_names()
    _st = [f for f in os.listdir(SCRIPTS)
           if f.startswith("selftest-") and f.endswith((".py", ".sh"))]
    if dang is None:
        # 取不到就是**核不了**，不是「没有问题」——**如实报出，不装作核过了**（纪律 203）
        print("方向十五：[skip] 本手册目录不在 git 检出里（或读不到删除历史），"
              "**核不了「被删掉的引用」**——如实报出，不装作核过了")
    else:
        _hits = 0
        for fn in sorted(_st):
            path = os.path.join(SCRIPTS, fn)
            try:
                body = _code_only(path)
            except (OSError, SyntaxError):
                continue
            for ref in sorted(set(DANGLING_RE.findall(body)) & dang):
                _hits += 1
                problems.append(
                    f"方向十五：{fn} 引用了 `{ref}`，而它**已经被删掉**"
                    "　→ 反验不在构建路径上，引用一个被删掉的文件**只有真跑它才会炸**，"
                    "而炸起来常常是「整份报告只剩一行 Traceback」（Batch 209 实测）"
                    "　→ 删它之前先确认「只被这一处用」：**这句话 Batch 207 写过、"
                    "也从没被核过**，而它就是那次漏网的直接原因")
        if _hits == 0:
            print("  方向十五：%d 份反验与注入夹具的代码里"
                  "**没有引用指向任何一个被删掉的同层文件**"
                  "（`scripts/` 下历史上删过 %d 个文件）"
                  "　→ **看不见的形态也要说清楚**：引用一个**从未存在过**的错名字"
                  "本方向抓不到（判据认的是「删过」这个事实，不是名字长得像不像）"
                  % (len(_st), len(dang)))

    # 方向十三（**Batch 204 新增**）：**闸的失败必须真的被说出来**。
    # 背景是实测出来的：`run_gate` 原来写成 `out="$(python3 ...)"; rc=$?`，
    # 而在 `set -e` 下这一行会让整份构建脚本当场退出——
    # `rc=$?` 与三段分支**一行都执行不到**，`$out` 也随退出被丢掉。
    # 于是闸 21 报红时，构建**只留下一个 rc=1，日志停在闸 20，再无一句话**。
    # **一个从不执行的报错分支，比没有报错分支更坏**：它让人以为构建是透明的。
    # 这里**行为可判**：抠出真函数、配 stub 闸真跑一遍，三种退出码各问一次。
    _try = _run_gate_probe
    rc1, out1 = _try(1)
    if rc1 != 1 or "核对不一致" not in out1 or "试闸" not in out1 or "闸的输出" not in out1:
        problems.append(
            "方向十三：闸报「不一致」时，构建**没有把它说出来**（rc=%d）"
            "　→ `run_gate` 里的 `out=\"$(...)\"` 少了 `|| rc=$?`，"
            "`set -e` 会让它当场退出，三段分支永远执行不到；"
            "**闸名与闸的输出都会一起被丢掉**" % rc1)
    rc2, out2 = _try(2)
    if rc2 != 1 or "未能核对" not in out2 or "核对不一致" in out2:
        problems.append(
            "方向十三：闸报「未能核对」时，构建**没说清楚**（rc=%d）"
            "　→ 退出码 2 **不得**被说成「核对不一致」——那会把人引去手册里"
            "找根本不存在的问题（Batch 160 立这个码的理由）" % rc2)
    # **成功路径不检查闸名**：`ok "$out"` 只打闸自己的输出，
    # 闸名只出现在 `warn`/`fail` 两条分支里——**这是既有设计，不是缺陷**，
    # 而判据要按事实写：第一版这里也查了「试闸」，于是 rc=0 正常却报红。
    # **判据把「没检查过的事实」当成失败，等于自己制造假阳性。**
    rc0, out0 = _try(0)
    if rc0 != 0 or "闸的输出" not in out0 or "[ FAIL " in out0:
        problems.append(
            "方向十三：闸 rc=0 时，构建**没有正常收下它的输出**（rc=%d）——"
            "这一支是**不误伤**：修 run_gate 时最容易把成功路径也弄坏" % rc0)

    # 方向十四（**Batch 205 新增**）：**shell 脚本里不得有会在 UTF-8 locale 下炸掉的变量展开**。
    # 背景是实测事故：三份 shell 反验共 33 处 `$var：`，
    # 在 `LC_CTYPE=C.UTF-8` 下 `set -u` 直接报「`desc?: unbound variable`」——
    # **而 `desc` 上一行刚 `local` 过**。同一台机器、不设那个变量时它们全绿，
    # **所以「默认环境下看不出来」正是它藏了这么久的原因**。
    broke, bashver = _locale_breaks_it()
    why = ("**本机实测会坏**（%s，LC_CTYPE=C.UTF-8）" % bashver if broke
           else "**本机 bash 实测不复现**（%s）——仍然按最坏情况要求写 `${}`，"
                "因为出事的是别人的机器" % bashver)
    for path in _shell_files():
        rel = os.path.relpath(path, ROOT)
        with open(path, encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                if line.lstrip().startswith("#"):
                    continue
                for m in UNSAFE_VAR_RE.finditer(line):
                    j = m.end()
                    if j < len(line) and ord(line[j]) > 127:
                        problems.append(
                            "方向十四：`%s` 第 %d 行的 `$%s` 后面紧跟一个非 ASCII 字符"
                            "（%r）——%s"
                            "　→ 改成 `${%s}`：中文全角标点紧跟变量时，"
                            "UTF-8 locale 下的 bash 会把那些字节算进变量名"
                            % (rel, n, m.group(1), line[j], why, m.group(1)))
                        break

    checked = py_ok + sh_ok
    if problems:
        print("反验启动核对：%d 份反验中有 %d 处问题" % (len(names), len(problems)))
        for p in problems:
            print("  ✗ " + p)
        print("→ **反验不在构建路径上，它坏了不会让构建变红**——"
              "所以「它至少能启动」这件事必须由构建来保证（Batch 178 实测 34 例静默失效）")
        return 1

    print("反验启动核对通过：%d 份反验全部可启动"
          "（python %d 份语法可解析且本地依赖可 import、shell %d 份通过 bash -n）"
          % (checked, py_ok, sh_ok))
    print("  另有 %d 份注入夹具（selftest-*-fix-*.py）语法可解析" % fx_ok)
    print("  慢反验 %d 份已登记（%s）——提交前手动跑"
          % (len(SLOW), "、".join(sorted(SLOW))))
    print("  shell 变量展开核对（方向十四）：%d 个 shell 脚本里"
          "**没有「`$var` 紧跟非 ASCII 字符」**（本机 %s）"
          % (len(_shell_files()), "实测会坏" if broke else "实测不复现"))
    print("  构建出口核对（方向十三）：闸 rc=0/1/2 三种结局**都被真跑了一遍**"
          "（rc=1 报「不一致」、rc=2 报「未能核对」而不是「不一致」、rc=0 正常收下）")
    print("  慢反验前提核对（方向五/五之二，**只查前提不查结果**）："
          "`selftest-meta.sh` %d 个夹具锚点、%d 个因目标不在场跳过；"
          "`selftest-unreachable.sh` %d/%d 个用例前提成立、%d 个跳过"
          % (fx_checked, fx_skipped, ur_checked, len(_cases), ur_skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
