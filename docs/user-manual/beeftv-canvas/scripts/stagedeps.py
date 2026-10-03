#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把被测闸门连同它的**本地依赖闭包**搬进反验的临时目录（Batch 253）。

**它解决的是一个被记了五次、修了五次的洞。**
反验要在临时目录里跑被测闸，**而临时目录里必须先有那个闸 import 的每一个本地模块**，
否则闸一启动就 `ModuleNotFoundError`，**那份反验的每一例都失败，
而 `build-site.sh` 仍然全绿**（反验不在构建路径上，Batch 178 实测 34 例跨 3 批全坏）。
五次同形状的漏搬：

| 批次 | 漏掉的模块 | 谁抓到的 |
|---|---|---|
| Batch 178 | `baseline` | 闸 17 |
| Batch 181 | `batchread` | 闸 17 |
| Batch 197 | `beefsrc` | 闸 17 |
| Batch 251 | `headingkey`（闸 5） | 闸 17 |
| Batch 252 | `headingkey`（闸 32） | 闸 17 |

**五次都是闸 17 报出来的，而闸 17 报出来之后靠的是人记得去补那一行。**
**本模块要做的 就是把那一行从「人记」变成「算出来」。**

**为什么搬运逻辑要放在这里，而不是让 24 份反验各写各的**：
「一个闸门的本地依赖闭包是什么」是**一个概念**，而纪律 274 推论一说
**判据之间有共享概念时，那个概念只能有一份实现**——
一份实现放在搬运侧（这里）、一份放在判据侧（`verify-selftest-deps.py`），
**那么只要两边对某一种 import 形态的理解不同，判据就会判「齐了」而闸其实起不来。**
所以**闸 17 也从这里 import**，不自己再写一遍。

**搬完立刻验证能 import，用子进程做。**
理由是这一条必须验证「真的能 import」，**而 AST 只能算出闭包、算不出「能不能 import」**——
**Batch 205 的教训正是「判据问的层级比它需要回答的浅一层」**：
第一版只看一层依赖，于是 `baseline` → `beefsrc` 的第二层没人看。
**而真 import 一次就把这件事验掉了，且它对「闭包算错了」也敏感**。
**用子进程而不是在本进程里 exec**：被测闸的顶层代码会真的跑起来
（它会 import yaml、会算 ROOT），**在反验进程里跑等于让反验替闸门付副作用**。
子进程里失败只会拿到一个非零退出码，**干净、可预期**。
"""

import ast
import os
import shutil
import subprocess
import sys

#: 本模块所在目录 = `scripts/`。反验 import 它时 `sys.path[0]` 就是这里，
#: 所以 24 份反验**不需要**把本模块也搬进临时目录。
HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = HERE

#: 标准库：出现在这份名单里的 import 不需要被搬进临时仓。
#: **与 `verify-selftest-deps.py` 原先那份逐字相同**——因为现在是同一份实现了。
STDLIB = set("""abc argparse ast base64 collections contextlib copy csv dataclasses datetime
difflib enum errno filecmp fnmatch functools glob hashlib io itertools json logging math mimetypes
os pathlib platform random re shlex shutil subprocess sys tempfile textwrap time typing unittest
urllib uuid warnings""".split())


def local_imports(path):
    """返回该脚本 import 的**本地模块名**（即 `scripts/` 下真实存在的 `.py`）。"""
    try:
        with open(path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                names.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level:          # 相对 import
                continue
            if node.module:
                names.add(node.module.split(".")[0])
    out = set()
    for n in names:
        if n in STDLIB:
            continue
        if os.path.isfile(os.path.join(SCRIPTS, n + ".py")):
            out.add(n)
    return out


def local_closure(gate_name, _seen=None):
    """**递归**求出被测闸门及其（本地）依赖的闭包，含闸门自身。

    **递归是 Batch 205 用 4 份红透的反验换来的**：
    `verify-line-counts.py` 直接 import 的是 `baseline`，
    而 `baseline.py` 自己 `import beefsrc`——**第二层没人看**，
    于是那 4 份反验 0/5、0/6、0/5、0/4 全红而构建全绿。
    当时那道判据报绿，是因为它问「被测闸 import 了什么」，
    答「baseline」，而反验**确实**搬了 `baseline.py`。
    **它问的层级比它需要回答的浅一层**（纪律 176：判据本身没错的那种缺陷）。

    入参是**不带 `.py` 的模块名**。用访问集合防死循环（`baseline` ↔ `beefsrc` 之类）。
    """
    seen = set() if _seen is None else _seen
    if gate_name in seen:
        return seen
    seen.add(gate_name)
    path = os.path.join(SCRIPTS, gate_name + ".py")
    if not os.path.isfile(path):
        return seen
    for dep in (local_imports(path) or ()):
        local_closure(dep, seen)
    return seen


def stage_gate(tmp, gate_name, extra=(), verify=True):
    """把 `gate_name` 连同它的本地依赖闭包搬进 `tmp/scripts/`，返回搬过去的模块名。

    `extra` 是**不属于闭包但反验自己也要带的东西**（页面、manifest、配置），
    那些不是 import 出来的，`local_closure` 算不到——**这一条写在参数说明里，
    不留在代码里当免责**（能力上限要么被接住，要么写进文件头）。

    `verify=True` 时**立刻用子进程试一次真 import**，失败抛 `RuntimeError`。
    **为什么必须验**：静态闭包只说明「按 AST 算该有的都有」，
    **而 Batch 205 那个洞的本质是「算的那一层不够」**——
    **真 import 一次是对「算错了」最直接的检验**，
    且它连「算出来的那份在临时目录里能否被找到」一起验了。
    """
    mods = sorted(local_closure(gate_name))
    dst = os.path.join(tmp, "scripts")
    os.makedirs(dst, exist_ok=True)
    missing = [m for m in mods if not os.path.isfile(os.path.join(SCRIPTS, m + ".py"))]
    if missing:
        raise RuntimeError(
            f"要搬的模块在 scripts/ 下不存在：{missing}——"
            f"**这说明闭包是从一份过期的 scripts/ 算出来的**")
    for m in mods:
        shutil.copy(os.path.join(SCRIPTS, m + ".py"), os.path.join(dst, m + ".py"))
    if verify:
        # **只验依赖，不验被测闸本身**：反验的常规操作就是**故意把闸改坏**
        # （塞语法错误、改坏正则），**而那不是搬运失败**——
        # 把它算进 `stage_gate` 会让「用例 3 注入 SyntaxError」这一类用例
        # 在**搬运阶段**就抛 RuntimeError，**用例根本跑不到自己要验的那一步**。
        # **这条是本模块第一版就踩的**：它把被测闸也放进 import 列表，
        # 结果「改坏闸」的反验全在 empty/prepare 阶段崩掉。
        _assert_importable(tmp, [m for m in mods if m != gate_name])
    return mods


def _assert_importable(tmp, mods):
    """在 `tmp/scripts` 上跑一次真 import，失败抛错（子进程，完全隔离）。"""
    if not mods:
        return
    code = "import " + ", ".join(mods)
    r = subprocess.run([sys.executable, "-c", code], cwd=os.path.join(tmp, "scripts"),
                       capture_output=True, text=True)
    if r.returncode != 0:
        tail = (r.stderr or r.stdout or "").strip().split("\n")[-1]
        raise RuntimeError(
            f"搬完了却 import 不起来（{', '.join(mods)}）：{tail}\n"
            f"  → **这说明闭包算得不够**。要么某个模块的 import 形态是 "
            f"`local_imports()` 认不出来的，要么它自己又依赖了别的东西。"
            f"**先修 `local_imports()`，不要在反验里手工补搬运。**")


def _copy_all_modules(tmp):
    """把 `scripts/` 下**所有**非反验的 `.py` 搬进 `tmp/scripts/`，返回搬过去的模块名。

    **有的反验要跑很多道闸**（`selftest-zero-input.py` 遍历候选表里的每一道），
    那种反验搬的是**整个目录**而不是某一个闸的闭包。
    **这一条要单独提供，是因为「搬整个目录」与「搬某个闸的闭包」在判据侧
    长得不一样**——而判据比搬运手段窄就会误报
    （Batch 190 修过三次同源的「判据认写法不认事实」，这里不再重复那个错）：
    **所以凡是「搬整目录」这个事实，都写成一次 `stage_all()` 调用**，
    判据认这一次调用，**而不是去猜一个 `for … os.listdir(…)` 的循环搬了些什么**。
    """
    dst = os.path.join(tmp, "scripts")
    os.makedirs(dst, exist_ok=True)
    mods = []
    for name in sorted(os.listdir(SCRIPTS)):
        if name.endswith(".py") and not name.startswith("selftest-"):
            shutil.copy(os.path.join(SCRIPTS, name), os.path.join(dst, name))
            mods.append(name[:-3])
    return mods


def stage_all(tmp, verify=True):
    """搬**整个** `scripts/`（不含反验自己），并验它们能不能一起 import。

    **验的时候排除被测闸是做不到的**——这一份搬的是全部，所以「被测闸」是运行时才知道的。
    **因此 `verify=True` 有一处明确的例外**：调用方**自己**改了某个闸的内容之后
    （而那正是反验用例的常规操作），再调它就会报 SyntaxError。
    **用法**：搬完之后要改闸，就调 `stage_all(tmp, verify=False)`，
    **改完的闸起不起得来由闸自己负责**——那不是搬运的职责。
    """
    mods = _copy_all_modules(tmp)
    if verify:
        _assert_importable(tmp, mods)
    return mods


if __name__ == "__main__":        # 手动自检：python3 scripts/stagedeps.py verify-foo
    for name in sorted(local_closure(sys.argv[1] if len(sys.argv) > 1 else "verify-meta")):
        print(name)
