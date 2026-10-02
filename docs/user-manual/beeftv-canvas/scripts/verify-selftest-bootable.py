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
import subprocess
import sys

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
    "selftest-selftest-bootable.py": {
        "seconds": 34,           # 历史快照（Batch 201：13 例时 20.8s，加 2 例后 33.6s；Batch 202 同场复核 42.8s——**同样漂，见上一条**）
        "why": "每一例都要 `copytree` 整份 `scripts/`（87 个文件）进沙箱再跑一遍闸 18，**而闸 18 现在还会在沙箱里重放慢反验的夹具前提**。33.6 秒已越过 30 秒阈值，**放进构建会让每次构建多花三分之一时间**。登记 + 提交前跑——**这与 `selftest-meta.sh` 是同一类必要成本**：它核的是「反验本身还能不能用」，而反验不在构建路径上。",
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
    "selftest-baseline.py": 1.6,
    # Batch 198：`beefsrc` 反验（6 例），实测 0.29s——临时树里现造仓与 worktree
    "selftest-beefsrc.py": 0.4,
    "selftest-batch-rows.py": 0.4,  # Batch 183：闸 19，实测 0.39/0.39/0.45s
    "selftest-deadlinks.py": 0.6,
    "selftest-encoding.py": 0.4,    # Batch 183：闸 20，实测 0.42/0.39/0.42s
    "selftest-endpoints.py": 1,   # Batch 181：闸 3 改批量读后 43s → 1s
    "selftest-error-copy.py": 1.6,
    "selftest-exclusions.py": 5,  # Batch 187：加理由完整性方向并加到 6 例后实测 4.3/4.8s
    "selftest-feature-flags.py": 0.4,
    "selftest-label-drift.py": 4,  # Batch 182：闸 6 改批量读后 105s → 4s
    "selftest-ledger-refs.py": 1.2,  # Batch 184：闸 21，实测 1.18/1.26/0.66s
    "selftest-line-counts.py": 11.8,
    "selftest-runtime-policy.py": 0.7,
    "selftest-quote-punct.py": 11,  # Batch 185：闸 22，实测 9.4/11.0s（6 例各跑一遍全量核对）
    "selftest-screenshots-literals.py": 23.5,
    "selftest-screenshots.py": 0.6,
    "selftest-selftest-bootable.py": 34,  # Batch 201：再加方向五之二的 2 例后实测 33.6s
    "selftest-selftest-deps.py": 0.6,
    "selftest-scope.py": 0.3,   # Batch 190：闸 24，实测 0.23/0.21/0.27s（5 例，各起一棵临时树）
    "selftest-shortcuts.py": 1.3,
    "selftest-shot-version.py": 2.0,
    "selftest-shot-drift.py": 23,   # Batch 189：闸 23，实测 19.4/23.1s（7 例，每例两棵树）
    "selftest-shot-pixels.py": 10,  # Batch 191：闸 25，实测 9.39/9.39s（6 例，用例 6 真图全解 4s）
    "selftest-tables.sh": 2.0,
    "selftest-zero-input.py": 9.4,  # Batch 196：加方向三（手册树正常但上游仓不可用，跑在真实树上）后实测 9.4s
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
            out.append((argv[1], argv[2], argv[3].replace("$HERE", SCRIPTS), argv[4]))
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
        for desc, path, fixer, feature in _cases:
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
    for desc, why in ur_void:
        problems.append(
            f"方向五之二：慢反验 `{desc}` 的前提已不成立（{why}）——"
            "**这条用例会作废，而作废的用例什么都不验却不算失败**（纪律 178）"
            "　→ 上游 `origin/main` 改了这段内容或路径：要么改夹具的锚，"
            "要么把该用例移到不再成立的位置")

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
    print("  慢反验前提核对（方向五/五之二，**只查前提不查结果**）："
          "`selftest-meta.sh` %d 个夹具锚点、%d 个因目标不在场跳过；"
          "`selftest-unreachable.sh` %d/%d 个用例前提成立、%d 个跳过"
          % (fx_checked, fx_skipped, ur_checked, len(_cases), ur_skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
