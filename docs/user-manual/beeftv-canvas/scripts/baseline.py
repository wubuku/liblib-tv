#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""取证基线（Batch 175 新增）——所有读上游源码的闸门共用**同一个**版本对象。

**这个文件为什么存在（Batch 175 的实测，不是假想问题）**：

手册正文声明「适用 v1.6.16」，正文是照 **v1.6.16** 写的。而在此之前，8 道读源码的
闸门各自把上游 ref 写死成 **`origin/main`**（浮动的）。两者会静悄悄地分家：

  · 上游从 v1.6.16 走到 v1.6.22（实测 27 个提交、223 个文件有差异），
  · 闸门却还在按新版本核对**照旧版本写的正文**，
  · 于是红灯亮起，而**红灯的含义被搞反了**。

实测抓到两处：`web/src/pages/canvas` 行数 17009→17122，以及「选择镜头模板」文案
在上游被删（`canvas-director-template-modal.tsx` 整个文件在 v1.6.22 已不存在）。
**这两条在 v1.6.16 上都是绿的**——手册没写错，是上游走了。

**为什么这个混淆很危险**：红灯只有一种修法（改手册正文），于是人会去改正文，
**把照 v1.6.16 写的内容改成 v1.6.22 的样子**——手册从此不再对应任何一个真实版本。
「上游走了」和「手册错了」这两件事的修法**正好相反**：
前者该做的是**重做一轮增量对账并升版**，后者才是改正文。

**本模块的约定**：

  · `BEEFTV_REF` 环境变量**优先**——反向验证需要指向合成 ref，这是 Batch 163
    之后所有 selftest 的既有做法，不能破坏。
  · 否则用**手册自己声明的版本**（`20-reference.md` 的「取证基线」小节）。
  · 读不到声明时**不猜**，抛 `BaselineError` 让调用方返回 rc=2「未能核对」——
    宁可报「无法核对」，也不静悄悄地退回浮动 `origin/main`（Batch 157 的教训：
    工具失败被当成零命中，是同一类错误的另一种形态）。

**基线声明写在手册里而不是代码里**，理由和闸 3 相同：被核对的文件必须是唯一真值。
基线改了只需改手册，不必碰 8 个脚本；而「基线声明与 README 的适用版本是否一致」
由闸 14 双向对账。

**`BEEFTV_MANUAL_ROOT` 为什么存在**（Batch 178 加）：
反向验证会把被测闸门**复制进临时目录**再运行，而闸门会 import 本模块。
本模块原先用 `dirname(dirname(__file__))` 推断手册根——**在临时目录里就指错了**，
于是 `resolve_ref()` 抛 `BaselineError: 读不到 20-reference.md`，
**反验的每一例都失败，而闸门本体的构建检查全绿**。
（同一批还有第二层：反验只复制了闸门脚本、没复制本模块，直接 ModuleNotFoundError。
**两层都静悄悄坏了三个批次**——因为「反验坏了」不会让构建变红，只有专门去跑它才看得见。）
**教训**：一个被多处 import 的模块，它的「定位自己所在仓」的假设**必须在被搬运时仍然成立**。
用环境变量显式传入是最省事、也最不容易被误删的做法。
"""

import functools
import os
import sys
import re
import subprocess

import beefsrc
from beefsrc import resolve_src

ROOT = os.environ.get("BEEFTV_MANUAL_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFERENCE = os.path.join(ROOT, "20-reference.md")

#: 上游仓路径。**Batch 197：从 `beefsrc.resolve_src()` 取，不再单点读环境变量。**
#: 原先这里是 `os.environ.get("BEEFTV_SRC", <硬编码>)`——**没有任何校验**，
#: 于是 `BEEFTV_SRC` 指向不存在的路径时，该路径被原样塞进 `git -C <path>`，
#: 报错说「基线提交在 <你设的路径> 里不存在」，
#: **而真正的原因多半是「那不是一个仓」**（Batch 196 实测 12 道闸都这么说）。
#: 而 7 道闸各自带着一张 `CANDIDATES` 表、判真条件还不一样，
#: **同一个 `BEEFTV_SRC` 在不同闸里会解析成不同的仓**——同一份事实被手写了 4 遍。
SRC, _SRC_IS_FALLBACK = resolve_src()

# 手册里「取证基线」小节声明的两个字段。改动这里 = 改手册的取证对象。
_FIELD_RE = re.compile(r"^-\s*\*\*(版本|提交)\*\*[：:]\s*`?([^`\s]+)`?\s*$")


class BaselineError(RuntimeError):
    """读不到基线声明、或声明的提交在上游不存在。调用方应返回 rc=2。"""


def declared_baseline():
    """从 `20-reference.md` 的「取证基线」小节读出 (版本, 提交)。

    **刻意锚在「小节标题 + 紧邻的两个字段」上**，而不是全文搜「v1.6.」：
    手册里到处都是版本号（每页的适用版本行、增量说明），全文搜必然抓到一堆，
    那就是 Batch 133「判据锚的是誊抄副本」的翻版。
    """
    try:
        with open(REFERENCE, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        raise BaselineError(f"读不到 {os.path.basename(REFERENCE)}：{exc}")

    # **按标题文字定位，不认死级别**（Batch 232）。
    # 原实现写死 `text.find("### 取证基线")`——于是「把这一节从 H3 改成 H2」这种
    # **纯结构修正**会让 15 道读基线的闸同时报「未能核对」。
    # 而那次改动本身是对的：`20-reference.md` 的第一个小节是顶层小节、
    # 本页其余 7 个顶层小节全是 H2，**它没有任何 H2 父级却写成 H3**，
    # 在页内目录里被降级（闸 29 就是为它建的）。
    #
    # **修法是让锚点不依赖级别，而不是放弃结构修正**——同 Batch 225 那次一样：
    # 锚点该按「这是哪个小节」定位，不该按「它是第几级 #」定位。
    m = re.search(r"^(#{1,6})[ \t]*取证基线[ \t]*$", text, re.M)
    if not m:
        raise BaselineError(
            "20-reference.md 里找不到「取证基线」小节——手册没有声明它照哪个版本取证")
    level = len(m.group(1))
    tail = text[m.end():]
    # 段落到「下一个**同级或更浅**的标题」为止（原实现只认 `\n### `，
    # 小节是 H2 时会一路吃到页尾，把后面的字段也算进来）
    nxt = re.search(r"^#{1,%d}[ \t]" % level, tail, re.M)
    section = text[m.start(): m.end() + (nxt.start() if nxt else len(tail))]

    version = commit = None
    for line in section.splitlines():
        m = _FIELD_RE.match(line.strip())
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if key == "版本":
            version = val
        elif key == "提交":
            commit = val
    if not version or not commit:
        raise BaselineError(
            "「取证基线」小节里没有同时声明「版本」和「提交」两个字段")
    return version, commit


def resolve_ref():
    """闸门真正该读的上游 ref。

    优先级：`BEEFTV_REF`（反向验证用）> 手册声明的提交。
    读不到声明 → `BaselineError`，**绝不**静悄悄退回 `origin/main`。
    """
    override = os.environ.get("BEEFTV_REF")
    if override:
        return override
    if SRC is None:
        # **Batch 197 新增的这一支**。原先没有它，于是 `commit_exists` 会拿
        # `None` 当路径去跑 `git -C None`，而错误信息说的是「基线提交不存在」——
        # **一个仓都没找到，却报成「提交号写错了」**，排查方向直接跑偏。
        raise BaselineError(
            "找不到可用的 BeefTV 源码仓：设 `BEEFTV_SRC` 指向一个 git 检出"
            "（普通检出与 worktree 都行）。候选与判真结果：\n" + beefsrc.explain())
    _version, commit = declared_baseline()
    if not commit_exists(commit):
        raise BaselineError(
            f"手册声明的取证基线提交 {commit} 在 {SRC} 里不存在"
            "（上游可能已 gc 掉该对象、提交号写错了，"
            "**或者你 shallow clone 过——浅克隆只有最近一次提交的历史**）")
    return commit


def commit_exists(rev):
    if SRC is None:
        return False
    r = subprocess.run(["git", "-C", SRC, "rev-parse", "--verify", "--quiet", rev + "^{commit}"],
                       capture_output=True, text=True)
    return r.returncode == 0


def announce_fallback(gate_label=None):
    """**走了兜底就把这件事说出来**——纪律 172（Batch 202 补齐）。

    **Batch 197 只实现了一半**：那 7 道自带 `CANDIDATES` 的闸在自己的 `find_source()`
    里打了 `[兜底]`，而**另外 6 道从本模块取 `SRC` 的闸一句都不说**——
    实测它们在 `BEEFTV_SRC` 指向非仓时 **rc=0、输出是一句干净的「核对通过」**，
    **而核的是用户没指定的另一份检出**。**静默降级比直接失败更坏，因为它还报绿。**

    所以这句话**集中放在这里**：15 道碰上游解析的闸共用一个措辞、一个判断，
    **而不是每道闸各写一遍**（那又是一次「同一份事实被手写多遍」）。
    **闸必须在自己的输出里留下「我读的是哪一份」的痕迹**，
    否则「核过」与「核的是你指定的那份」在结果里长得一模一样。
    """
    if not _SRC_IS_FALLBACK:
        return
    if gate_label is None:
        # **从调用栈认出调用者是哪道闸**——这样 15 道闸一句名字都不用写。
        # 「每道闸把自己的名字报出来」这件事如果靠传参，就多了一份要维护的清单；
        # **而调用者自己的模块名本来就是它，不用问第二个人**。
        # **用调用者的文件名，不用 `__name__`**：闸是以 `python3 verify-xxx.py`
        # 跑的，于是每道闸的 `__name__` **全都是 `__main__`**——
        # 实测第一版就是这么写的，输出一排「[兜底] __main__ 未采用…」，
        # **说了等于没说，因为它没说是哪道闸说的**。
        # `co_filename` 才是它自己的身份，而那本来就是它，不用问第二个人。
        try:
            gate_label = os.path.basename(sys._getframe(1).f_code.co_filename)
        except Exception:                                # noqa: BLE001
            gate_label = "某道闸"
    print(f"[兜底] {gate_label} 未采用 BEEFTV_SRC 指定的路径（它不是一个 git 检出），"
          f"改用候选表里的 {SRC}")


def describe():
    """给闸门输出用的一行说明：当前按哪个版本取证。"""
    version, commit = declared_baseline()
    return f"{version}（{commit}）"


#: 模块级 `module_ref()` 攒下的「拿不到基线」异常，由 `@baseline_guard` 转成 rc=2。
#: **它存在的原因是实测出来的**（Batch 193）：10 道闸里有 7 道把
#: `REF = os.environ.get("BEEFTV_REF") or resolve_ref()` 写在**模块级**——
#: 那行在 `import` 时就执行，**远在 `main()` 与装饰器之前**，
#: 所以第一版的 `@baseline_guard` 对它们完全无效（实测改完仍剩 7 道 rc=1）。
_PENDING = []


def module_ref():
    """给闸在**模块级**算基线用：拿不到就把异常存下来，由 `@baseline_guard` 转成 rc=2。

    **为什么不直接 `resolve_ref()`**——因为模块级的异常在 import 阶段就抛出去了，
    那一刻 `main()` 还没被调用，任何装饰器和 try 都接不住。
    而闸把 `REF` 写成模块级是有原因的：**它下面十几个函数都要用**，
    改成传参会让每一处都变（`REF` 在 `verify-feature-flags.py` 之类处被引用十几次）。

    **为什么不在这里直接 `sys.exit(2)`**：模块导入期退出，会让
    「这个文件 import 不了」和「这个闸跑不出结论」变成同一件事——
    **而闸 18 正要靠 import 成功与否来判断反验夹具是否语法可解析**。
    所以这里只记录，退出交给 `main` 的入口。
    """
    try:
        return resolve_ref()
    except BaselineError as exc:
        _PENDING.append(exc)
        return None


def baseline_guard(fn):
    """把闸门 `main()` 整个包起来：拿不到基线就 rc=2「未能核对」。

    **这个装饰器为什么存在（Batch 193 实测，不是设想的）**：
    本模块的 docstring 写着「读不到声明时**不猜**，抛 `BaselineError`
    **让调用方返回 rc=2**『未能核对』」——**而 Batch 193 实测发现 10 道闸
    一个都没实现那半句**。

    实测：在一棵空手册树（没有 `20-reference.md`）上跑这 10 道闸，
    它们**全部抛未捕获的 `BaselineError` 并以 rc=1 退出**——
    而 rc=1 在本项目的约定里意为「**核过，且核出问题了**」。
    **实际发生的事是「一个文件都没找到，本轮根本没开始核」。**
    两种说法把排查引向完全不同的方向：
      · rc=1 → 「去手册里找哪里写错了」；
      · rc=2 → 「去查基线声明读不到 / 上游在不在」。

    **它接两处**（第一版只接住了一处，实测漏了 7 道）：
      · `module_ref()` 在**模块级**攒下的异常（import 阶段发生的）；
      · `main()` 运行途中抛出的 `BaselineError`（任意深度，`verify-shortcuts.py`
        的调用点在第二层函数 `bindings()` 里，**try 写在 main 里盖不住**）。

    **它不会盖住别的东西**：只捕 `BaselineError`，其它异常照旧冒泡
    （那属于判据自己的 bug，该在构建里炸出来而不是被这里吃掉）。
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        pending = _PENDING[0] if _PENDING else None
        try:
            if pending is not None:
                raise pending
            return fn(*args, **kwargs)
        except BaselineError as exc:
            print("[未能核对] %s" % exc)
            print("  → 本闸本轮没有核对任何断言。**这不是「核对通过」，也不是「核出不一致」**——"
                  "它说的是「取证基线读不到」，修法在手册的「取证基线」小节或上游仓，不在正文。")
            return 2
    return wrapper


def upstream_tip():
    """上游 origin/main 顶端，用于闸 14 报告「基线落后几个版本」。失败返回 None。"""
    r = subprocess.run(["git", "-C", SRC, "rev-parse", "--verify", "--quiet", "origin/main^{commit}"],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None
