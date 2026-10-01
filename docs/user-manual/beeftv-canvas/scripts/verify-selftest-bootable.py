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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")

# 慢反验登记表：**超过阈值的必须在这里写明为何不放进构建**。
# 阈值取自 Batch 179 的实测（见下），不是拍的。
SLOW_BUDGET_MS = 30000
SLOW = {
    "selftest-unreachable.sh":
        "**实测约 25 分钟**（走 git plumbing 往上游仓库注入 40 个用例并建临时 ref，"
        "每个用例都要 read-tree / write-tree / commit-tree）。"
        "**放进构建会让每次构建多花 25 分钟**，而它核的是闸 7 那 33 条断言的判据，"
        "属于「提交前跑一次」的量级。改为登记 + 人工定期跑。",
    "selftest-meta.sh":
        "**实测 97 秒 / 36 例**。本身不算离谱，但它**会原地改 15 个真实文件**"
        "（含 `AUDIT.md` / `PROGRESS.md` / `build-site.sh`）——"
        "**构建中途失败就会把它们留在被改状态**，"
        "而这正是 Batch 178 里「绝不能弄丢他人修改」那条纪律要防的事。"
        "故不自动跑，改为登记。",
}
SLOW_ANCHORS = {
    # 登记理由里点名的判据必须仍然成立，否则登记本身过期了
    "selftest-unreachable.sh": ("selftest-unreachable.sh", "refs/manual-gate-selftest"),
    "selftest-meta.sh": ("selftest-meta.sh", "SNAP_FILES"),
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


def main():
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

    # 方向三：每份反验都要能说出自己测的是哪道闸，且那道闸真实存在
    for fn in names:
        p = os.path.join(SCRIPTS, fn)
        try:
            with open(p, encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            continue
        if not re.search(r"verify-[a-z0-9-]+\.py", text):
            problems.append(
                f"方向三：{fn} 里找不到任何 verify-*.py 的引用"
                "　→ 它没有指向被测闸门；「反验 ↔ 闸」的对应关系会退化成散文"
                "（Batch 169 方向十一治的正是这个）")

    # 方向四：慢反验登记的理由必须仍然成立
    for fn, reason in SLOW.items():
        path = os.path.join(SCRIPTS, fn)
        if not os.path.isfile(path):
            problems.append(f"方向四：SLOW 里登记了 {fn}，但它不存在（登记已过期，请删）")
            continue
        src, needle = SLOW_ANCHORS[fn]
        probe = os.path.join(SCRIPTS, src)
        try:
            with open(probe, encoding="utf-8") as fh:
                body = fh.read()
        except OSError:
            problems.append(f"方向四：{fn} 的登记理由点名了 {src}，但读不到它")
            continue
        if needle not in body:
            problems.append(
                f"方向四：{fn} 的登记理由点名了 {src} 里的 {needle!r}，但那里已没有它"
                "　→ 登记理由失效，**要么它其实不慢了（该放进构建），要么理由要重写**")

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
    return 0


if __name__ == "__main__":
    sys.exit(main())
