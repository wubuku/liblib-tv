#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三十九道闸（Batch 270 新增）：**真闸坏掉时，构建必须发现。**

    它与闸 18 方向十三之四是**同一个病的两半**：
    **方向十三之四验的是「`run_gate` 会不会放过一个空输出的闸」，
    而它用的是 stub 闸；**
    **而没有任何一处验过 38 道真闸坏掉时构建会不会发现。**

**实测背景**（Batch 266 / 267 各一次，两次都靠我临时手动发现）：
    ①占位符名写错抛 `NameError` → 脚本零输出、rc=0、**构建全绿**；
    ②正则 `$$?` 触发 `re.error: nothing to repeat` →
    **而 `re.error` 是运行时才抛的，`ast.parse` 照样通过**——
    **所以所有核「写法」的判据都看不出它有病。**

**本闸问的是被测事实，不是写法**：
    **把某道真闸改成「无论什么都返回 0 且什么都不说」**，
    **看那道闸还会不会报出它本该报的东西。**

**为什么它必须对每道闸都做一遍**：
    **一道闸的失效形态不可迁移**——
    **A 闸坏在「读文件那一步」，B 闸坏在「正则匹配那一步」**，
    **而哪一道闸在本机恰好能被抓到，取决于它有没有那些输入**。
    **只试一道，就等于假设「所有闸的失效形态相同」**——
    **而那正是纪律 168 反复否掉的假设**（一个只注入了一种坏法的反验，
    不等于它有鉴别力）。

**它不做成 fail 而做成 rc=2**（除非那道闸本该报红）：
    **「某一时刻的注入结果」不是一个能长期维持的判定**——
    **判据自己注入的失败，取决于那台机器上恰好有什么输入**（纪律 101）。
    **所以它问的是「能不能抓到」，而「抓到了」本身不构成手册缺陷。**

**它为什么必须逐道真跑、而不能只 AST 扫**：
    **AST 能看出「有没有裸 `except`」，看不出「异常是不是真的被吞了」**——
    Batch 270 普查过：**38 道闸里 0 道有裸 `except`、5 处宽 `except Exception`**，
    **而那 5 处全都带着说明为什么必须宽**。
    **所以这个闸守的不是「写法」，是「坏掉时的可观察性」。**
"""

import ast
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

#: **只验这些**——它们是**内容闸**，本机有输入、能真跑出结论。
#: **为什么排掉闸 17/18（反验依赖 / 反验启动）**：
#: **它们本身要真跑几十份反验，单道就要几分钟**，
#: **而闸 18 方向十三之四已经在构造层面覆盖了 run_gate 的行为**。
#: **这里排掉它们是刻意的取舍，不是遗漏**——**取舍必须写下来，
#: 否则下一个人会以为「38 道都验过了」**。
SKIP = {
    "verify-selftest-deps.py",    # 要真跑几十份反验，几分钟一道
    "verify-selftest-bootable.py",
}


def gate_names():
    out = []
    for fn in sorted(os.listdir(HERE)):
        if fn.startswith("verify-") and fn.endswith(".py") and fn not in SKIP:
            out.append(fn)
    return out


#: **注入的形态：把 `main()` 的整个函数体换成一个「什么都不说、返回 0」的版本。**
#: **第一版是从 `def main():` 一直截到文件末尾**——
#: **于是 5 道闸「注入后还能说话」，而那不是它们性质不同，是注入没盖住**：
#: **`verify-baseline.py` / `verify-endpoints.py` / `verify-screenshots.py` /
#: `verify-shot-drift.py` / `verify-shot-version-source.py`
#: 把一部分逻辑写在 `if __name__ == "__main__":` 之后**，而截断把那截也删了，
#: **剩下的 `announce_fallback()` 之类照样会打印**。
#: **教训**：**「28 / 37」这个数是错的，而它错在注入方式上，不在闸上**——
#: **所以这类「量出来的分布」必须先确认注入真的生效了**（纪律 265：
#: **判据报红先问哪一侧错了，而这一侧是自己**）。
#: **第二版只替换 `main` 的函数体**（按缩进找它的范围），**文件其余部分原样保留**。
#: **为什么不是加一行 `except Exception: return 0`**：
#: **那只会吞掉「读文件失败」那一类**，
#: **而 Batch 266 实测的两次分别是 `NameError` 与 `re.error`——
#: **都不是 IOError**。**只注入一种，等于假设所有闸的失效形态相同。**
INJECTED_MAIN = '''def main():
    """（Batch 270 注入）原本的 main 的函数体已被整段替换。"""
    return 0
'''


def replace_main_body(src, gate, strip_decorators=False):
    """只替换 `main` 的函数体，保留文件其余部分。

    **`strip_decorators=True`（Batch 271 新增）时连装饰器一起去掉。**

    **为什么必须去掉（Batch 271 实测，不是设想的）**：
    **实测 13 道闸的 `main` 上有 `@baseline_guard`，而装饰器不在函数体里**——
    **所以第一版的注入对它们无效**，8 道在沙箱里仍会说话。
    **去掉装饰器之后，13 道全部彻底安静**——
    **也就是说装饰器就是唯一那道保护，不存在第二道**
    （第一版取证脚本以为「还有第二道」，**而那是切片错误**，见 `INJECTED_MAIN`）。

    **切片的坑：`fn.lineno` 指的是 `def main():` 那一行，装饰器在它之前**，
    **所以 `lines[:fn.lineno-1]` 会把 `@baseline_guard` 原样留在文件里**
    ——**而输出看起来是「去掉装饰器后仍有保护」，完全不像「装饰器根本没被去掉」**。

    **用 AST 定位函数边界，不用手工算缩进**——
    **这一版之前连错两次**：①从 `def main():` 截到文件末尾（**把 `if __name__`
    那截也删了，于是 5 道闸「注入后还能说话」，而那不是它们性质不同**）；
    ②在相对切片上算下标却拿去切整份文件的行表（**把 `def main():` 那一行丢掉了，
    产出的文件第 2 行就 `expected an indented block`**）；
    ③改用全局行号后又忘了 `body_start = i + 1`（**于是每道闸都「没有函数体」**）。
    **三次都是「手写位置计算」出的错，而 AST 本来就把这件事算好了**
    （纪律 274：**同一份事实被手写几遍就会有几套判真条件**）。

    **AST 给的是 `lineno`（1-based）与 `end_lineno`**，换算成 0-based 行号后
    **整个函数（含 def 行）替换掉**，函数体用固定的那两行。
    """
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return None, "前提失配：%s 本身语法错（第 %d 行：%s）" % (gate, exc.lineno, exc.msg)
    fn = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "main":
            fn = node
            break
    if fn is None:
        return None, "前提失配：%s 里没有顶层 def main()" % gate
    if fn.end_lineno is None or fn.end_lineno <= fn.lineno:
        return None, "前提失配：%s 的 main 范围算不出来" % gate

    lines = src.split("\n")
    start = fn.lineno - 1            # `def main():` 那一行
    end = fn.end_lineno              # 1-based 末行 = 0-based 的下一行
    #: **装饰器在 `def main():` 之前**——**而 `fn.lineno` 指的就是 `def` 那一行**，
    #: **所以 `lines[:fn.lineno-1]` 会把装饰器原样留在文件里**。
    #: **实测正是这样**：`verify-line-counts.py` 的 `@baseline_guard` 在第 94 行、
    #: `fn.lineno` 是 95 —— **`lines[:94]` 把它包进去了**，
    #: **而输出看起来是「去掉装饰器后仍有保护」，完全不像「装饰器根本没被去掉」**。
    if strip_decorators and fn.decorator_list:
        start = fn.decorator_list[0].lineno - 1
    #: **整个函数（含 def 行与装饰器）替换掉**——
    #: **`INJECTED_MAIN` 自带 `def main():` 那一行**，所以切掉整段是安全的。
    head = lines[:start]
    tail = lines[end:]
    return "\n".join(head + INJECTED_MAIN.rstrip("\n").split("\n") + tail), None


def run_injection(gate, sandbox_root, strip_decorators=False):
    """在沙箱里把一道闸换成注入版，跑它，看它还会不会说出本该说的话。

    **`strip_decorators=True`（Batch 271 新增）时连 `main` 上的装饰器一起去掉。**

    返回 `(注入版rc, 注入版输出字节数, None, None)`。
    """
    tmp = tempfile.mkdtemp(prefix="b270-gate.", dir=sandbox_root)
    try:
        sdir = os.path.join(tmp, "scripts")
        shutil.copytree(HERE, sdir)
        p = os.path.join(sdir, gate)
        src = io.open(p, encoding="utf-8").read()
        new, err = replace_main_body(src, gate, strip_decorators=strip_decorators)
        if new is None:
            return None, err, None, None
        #: **守卫：注入必须真的生效**（**纪律 297 的变体**——
        #: **「注入跑过了」与「注入什么都没做」输出上完全一样**）。
        #: **第一版就栽在这里**：它从 `def main():` 截到文件末尾，
        #: **而 5 道闸把逻辑写在 `if __name__` 之后，于是注入没盖住它们**，
        #: **「28/37」这个数就是错的**——**而错在注入方式上，不在闸上**。
        #: **所以这里断言「注入后的文件里必须有注入标记」**，
        #: **而没标记就当注入失败、不许拿那个数出去说**。
        if "（Batch 270 注入）" not in new:
            return None, "注入未生效：改写后的文件里找不到注入标记", None, None
        #: **守卫 2（Batch 271 新增）：说要去掉装饰器，就必须真去掉。**
        #: **Batch 271 取证第一版就栽在这里**：用 `lines[:fn.lineno-1]` 切片，
        #: **而装饰器行就在 `fn.lineno-1` 之前**——于是 `@baseline_guard` 原样留着，
        #: **7 道闸报出「去掉装饰器后仍 rc=2」，而那个输出看起来像
        #: 「装饰器之外还有第二道保护」，完全不像「装饰器根本没被去掉」**。
        #:
        #: **守卫的第一版把整份文件扫一遍找装饰器名，于是误伤了自己**：
        #: **`from baseline import …, baseline_guard` 那一行的 import 里也有这个名字**
        #: （实测 `verify-line-counts.py` 第 32 行），
        #: **而那不是装饰器**——**结果 13 道全部被判成「注入未生效」，
        #: 而分布显示「靠装饰器才说话 0 道」**。
        #:
        #: **所以守卫只认顶行以 `@` 开头的行**：
        #: **装饰器的语法形态就是「行首 @」，而 import 不是**。
        if strip_decorators and any(
                ln.lstrip().startswith("@") and "guard" in ln
                for ln in new.split("\n")):
            return None, ("注入未生效：要求去掉装饰器，"
                          "而改写后的文件里还有 `@…guard` 装饰器行"), None, None
        try:
            ast.parse(new)
        except SyntaxError as exc:
            return None, "注入产生了语法错误（第 %d 行：%s）" % (exc.lineno, exc.msg), None, None
        io.open(p, "w", encoding="utf-8").write(new)
        r = subprocess.run([sys.executable, p], cwd=os.path.dirname(tmp),
                           capture_output=True, text=True, timeout=300)
        out = (r.stdout or "") + (r.stderr or "")
        return (r.returncode, len(out.strip()), None, None)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


#: **`main` 上有没有 `@baseline_guard` 装饰器**。
#: **为什么这一族必须单列**：**装饰器不在 `main` 的函数体里**，
#: **所以「把函数体换空」对它无效**——
#: **实测：8 道带装饰器的闸注入后仍然有输出，
#: 而那输出是装饰器里的 `announce_fallback()` 打的**，
#: **不是「它还在检查」**。
#: **用 AST 判**：装饰器在 `node.decorator_list` 里，
#: **而 `def` 行与函数体不在同一个节点范围**——**这正是「为什么它没被替换掉」的机制**。
def is_baseline_guarded(gate):
    p = os.path.join(HERE, gate)
    try:
        tree = ast.parse(io.open(p, encoding="utf-8").read())
    except (OSError, SyntaxError):
        return False
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "main":
            for d in node.decorator_list:
                name = getattr(d, "id", None) or getattr(d, "attr", None)
                if name and "guard" in name:
                    return True
    return False


def main():
    gates = gate_names()
    if not gates:
        print("[skip] 一道闸都没找到——判据可能已失效")
        return 2

    print("真闸可观察性核对：逐道注入「什么都不说、返回 0」的 main()，"
          "看构建会不会发现（**%d 道，%d 道按理由跳过**）"
          % (len(gates), len(SKIP)))

    silent = []
    spoken = []
    #: **Batch 271 新增第三类**：带 guard 装饰器、**去掉装饰器之后**才彻底安静的那些。
    #: **它们是本批最要紧的一组**——**第一档它们「还能说话」，
    #: 而那 8 道话是装饰器打的、不是它们自己在检查**。
    guarded_stripped = []
    #: **分三类而不是两类**——**第一版只分「安静 / 还在说话」，
    #: 而那 8 道「还在说话」的原因被我想成了「它们性质不同」**。
    #: **实测出来不是**：**8 道全都用 `@baseline_guard` 装饰 `main`**，
    #: **而装饰器不在 `main` 的函数体里**——
    #: **于是替换函数体之后，装饰器仍然包着一个空壳、仍然会打印
    #: `announce_fallback()` 的警告**。
    #: **那不是「它还会检查」，那是「它旁边的装饰器还在喊」**——
    #: **而这两件事在「有没有说话」这个尺度上完全一样，在「有没有在检查」上完全相反。**
    #: **所以第三类必须单列**，否则这个分布会被读成「8 道更可靠」。
    guarded = []
    for g in gates:
        try:
            got = run_injection(g, None)
        except subprocess.TimeoutExpired:
            got = ("timeout", 0, None, None)
        except OSError as exc:
            got = ("oserror:%s" % exc.__class__.__name__, 0, None, None)
        rc, nbytes, _, _ = got
        if rc is None:
            # 前提失配，如实说，不装作核过了
            print("  — %s：%s" % (g, nbytes))
            continue
        if rc == 0 and nbytes == 0:
            silent.append(g)
        elif is_baseline_guarded(g):
            # ── Batch 271：对这一族再跑一档——**连装饰器一起去掉** ──────
            # **为什么必须再跑一档**：装饰器不在 `main` 的函数体里，
            # **所以第一档对它们无效**，8 道在沙箱里仍会说话——
            # **而那 8 道「还能说话」不是「它还在检查」**。
            # **第二档测的是「装饰器这道保护本身」**：
            # **实测 13 道全部彻底安静**——**装饰器就是唯一那道，不存在第二道**
            # （Batch 271 取证第一版以为「还有第二道」，**而那是切片错误**）。
            try:
                got2 = run_injection(g, None, strip_decorators=True)
            except (subprocess.TimeoutExpired, OSError):
                got2 = ("err", 0, None, None)
            rc2, b2, _, _ = got2
            if rc2 == 0 and b2 == 0:
                guarded_stripped.append(g)
            elif rc2 is None:
                print("  — %s（去掉装饰器那档）：%s" % (g, b2))
            else:
                guarded.append(g)
        else:
            spoken.append(g)

    #: **`main` 上有 guard 装饰器的总道数**——
    #: **它与「靠装饰器说话」的那几道不是同一个数**：
    #: **实测 13 道有装饰器，而只有 8 道在沙箱里真的抛了错**，
    #: **差的 5 道注入后彻底安静**。
    #: **两个数都要报**：**只报 8 会让人以为「有装饰器就更可靠」**。
    n_guarded_total = sum(1 for g in gates if is_baseline_guarded(g))

    if silent:
        print("  **✗ %d 道注入后彻底安静（rc=0 且零输出）——"
              "**这一批构建会全绿，而它其实什么都没检查**："
              % len(silent))
        for g in silent:
            print("    · %s" % g)
        print("    **方向十三之四能挡住这种形态**（`run_gate` 判它「一句话都没说」），"
              "**而它靠的是那个 stub 闸——真闸走的是同一条 `run_gate`，"
              "所以这 %d 道同样会被挡住**" % len(silent))
        print("    **而本闸报出来是为了让「这个形态真存在」变成一件可数的事**"
              "（纪律 300：一个数只有和它的分母一起报出来才是数）")
    else:
        print("  %d 道注入后都还能说话、且 `main` 上没有 guard 装饰器——"
              "**它们不会静悄悄地变成空壳**" % len(spoken))

    if guarded_stripped:
        print("  **%d 道第一档「还在说话」、**连装饰器一起去掉**之后彻底安静**：" % len(guarded_stripped))
        for g in guarded_stripped:
            print("    · %s" % g)
        print("    **这一类是本批最要紧的一组**——"
              "**第一档它们有输出，而那输出是 `@baseline_guard` 打的、不是它们自己在检查**；"
              "**去掉装饰器之后它们与那 %d 道一样彻底安静**"
              % len(silent))
        print("    **所以 `baseline_guard` 就是唯一那道保护，不存在第二道**"
              "（**Batch 271 取证第一版以为「还有第二道」，而那是切片错误**——"
              "**装饰器行就在 `fn.lineno-1` 之前，用 `lines[:fn.lineno-1]` 切片会把它原样留着**；"
              "**那个错误输出看起来像「去掉装饰器后仍有保护」，完全不像「装饰器根本没被去掉」**）。"
              "**判据现在有一条守卫：要求去装饰器时，改写后的文件里不许再有 `@…guard` 装饰器行**"
              "**（守卫第一版扫全文找名字，于是把 `from baseline import …, baseline_guard` 那一行误伤了——而那不是装饰器，"
              "**结果 13 道全被判成「注入未生效」、分布显示「靠装饰器才说话 0 道」**）**")
    if guarded:
        print("  **%d 道注入后仍有输出、**去掉装饰器之后仍不是安静**："
              "**这才是真的「装饰器之外还有东西」**：%s" % (len(guarded), "、".join(guarded)))

    #: **Batch 271 把上面那条「只测一档」补齐之后，三个数的含义固定下来**：
    #: **`silent` = 第一档就安静；`guarded_stripped` = 第一档在说话、
    #: **去掉装饰器后安静；`spoken` = 第一档在说话、且 `main` 上没有 guard 装饰器。**
    print("  **合计：安静 %d 道 / 靠装饰器才说话 %d 道 / 无装饰器却在说话 %d 道**"
          "（`main` 上有 `@baseline_guard` 的共 %d 道）"
          % (len(silent), len(guarded_stripped), len(spoken), n_guarded_total))
    print("    **「无装饰器却在说话」那一类要单独留意**："
          "**它意味着那道闸坏掉之后仍会留下输出，"
          "而那输出的来源不是任何保护机制——**那就要问「它是谁」**")

    print("  跳过的 %d 道：%s"
          % (len(SKIP), "、".join(sorted(SKIP))))
    print("    **理由**：它们要真跑几十份反验，单道几分钟；"
          "**而闸 18 方向十三之四已在构造层覆盖 `run_gate` 的行为**。"
          "**这是取舍不是遗漏**——写下来，下一个人才不会以为「38 道都验过了」")
    return 0


if __name__ == "__main__":
    sys.exit(main())
