#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第十七道闸：反验的临时仓必须带齐被测闸门的本地依赖（Batch 178 新增）。

**这道闸看守的是「反验本身还能不能跑」**——而它坏掉时，**构建是全绿的**。

**为什么需要它（Batch 178 的实测，这是本轮最贵的一次）**：

Batch 175 让 8 道闸改为 `from baseline import resolve_ref`（共用取证基线解析）。
**但 4 份反验是把被测闸门 `shutil.copy` 进临时目录再跑的**，那份临时目录里
**没有 `baseline.py`** —— 于是：

  · `selftest-line-counts` 5 例全失败、`selftest-runtime-policy` 6 例全失败、
    `selftest-feature-flags` 5 例全失败、`selftest-screenshots-literals` 4 例全失败；
  · **20 例，跨 3 个批次（175/176/177）全坏**；
  · 而 `build-site.sh` **十六道闸全绿**——因为闸门本体在真实目录里跑得好好的。

**为什么没人发现**：反验不在构建路径上。**「反验坏了」不产生任何构建期信号**，
只有专门去跑它才看得见——而上一批跑它还是三个批次前的事。
**这比判据失效更隐蔽：判据失效会红，反验失效只是安静地不再说话。**

修的过程还暴露了**第二层**：`baseline.py` 自己用 `dirname(dirname(__file__))`
推断手册根，在临时目录里同样指错，抛「读不到 20-reference.md」。
**一个被多处 import 的模块，它「定位自己所在仓」的假设必须在被搬运时仍然成立。**

**本闸两个方向**：

  方向一：**凡是把闸门复制进临时目录的反验，被测闸门 import 的每个本地模块
    都必须被一并复制。** 判据用 AST 抽 `import X`（`X` 不带点、不在标准库、
    且 `scripts/X.py` 真实存在），再核反验的源码里有没有提到它。
    **本闸不判「运行时真的成功」**——那要跑一遍，太慢；它判**静态上有没有搬运**，
    而静态足以抓住 Batch 178 这一类。

  方向二：**被搬运的本地模块不得自己用 `__file__` 推断仓根**，
    除非它同时支持 `BEEFTV_MANUAL_ROOT` 之类的外部注入。
    **这一条专治「搬过去了、但它找错了家」**——也就是上面说的第二层。

**为什么不直接跑一遍所有反验**：最慢的那份要 25 分钟（`selftest-unreachable.sh`），
放进每次构建不可接受；而**这类回归恰恰是「反验能抓、构建抓不到」的**，
所以要的是一个**构建期就能跑的静态等价物**。

退出码：0 全部自洽；1 有不自洽；2 未能核对（找不到 scripts 目录 / 抽出 0 份反验）。
"""

import ast
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")

# 标准库与第三方：出现在这些名单里的 import 不需要被搬进临时仓
STDLIB = set("""abc argparse ast base64 collections contextlib copy csv dataclasses datetime
difflib enum errno filecmp fnmatch functools glob hashlib io itertools json logging math mimetypes
os pathlib platform random re shlex shutil subprocess sys tempfile textwrap time typing unittest
urllib uuid warnings""".split())


def local_imports(path):
    """返回该脚本 import 的**本地模块名**（即 scripts/ 下真实存在的 .py）。"""
    try:
        with open(path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
    except (OSError, SyntaxError):
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


def copies_gate_into_tmp(text):
    """这份反验是否会把闸门脚本复制进临时目录。

    **Batch 190 修第二处按写法判定**：原式是
    `re.search(r"shutil\.copy\w*\(\s*\w+\s*,", text)`——要求 `shutil.copy(` 后面
    **紧跟一个单词再跟逗号**。于是一份写成
    `shutil.copy(os.path.join(HERE, name), …)`（**循环搬运多份文件**）的反验
    **整份被静悄悄跳过**。本批的 `selftest-scope.py` 正是这个写法：
    改完上面那处之后闸 17 仍报「12 份」，比实际少一份，而它报得**很绿**。

    **判据认的必须是动作而不是写法**：「用了 `shutil.copy*` 且建了临时目录」
    才是它想问的那件事，**参数写成单个变量还是表达式，与它无关**。
    这与本闸方向一里那句老话同源——**判据要认事实，不要认写法**。
    """
    return bool(re.search(r"shutil\.copy\w*\(", text)) and \
        bool(re.search(r"tempfile\.mkdtemp", text))


def independent_gate_names(text, scripts_dir):
    """这份反验**作为独立字符串常量**引用了哪些 `verify-*.py`，且它们真实存在。

    **为什么要用 AST 而不是正则**（Batch 190 实测的反面）：
    正则扫全文会把**注入夹具里伪造的闸门名**一并算进来。实测三处假阳性全是这个形状：

      · `selftest-selftest-deps.py` 的用例 3 在**一个大字符串常量**里写
        `GATE = os.path.join(HERE, 'verify-newfangled.py')`，那是要**注入给假反验看的文本**；
      · 同一份反验的用例 4 在大字符串里提到 `verify-baseline.py`，测的是「不搬闸门的反验不该被扫」；
      · `selftest-selftest-bootable.py` 真的 `os.path.join(tmp, "scripts", "verify-feature-flags.py")`，
        但它读那个文件是为了断言内容，**不是搬运它**。

    AST 能把前两类分开：**值恰好等于 `"verify-xxx.py"` 的独立常量**才算，
    作为更大字符串的一部分出现的不算。**判据要认的是「这个闸门被搬了」，
    不是「这几个字符出现在文件里」**——与方向一的 `moved` 判据同一条纪律。
    """
    names = set()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return names
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            v = node.value
            if re.fullmatch(r"verify-[a-z0-9-]+\.py", v) and \
                    os.path.exists(os.path.join(scripts_dir, v)):
                names.add(v)
    return names


def copies_whole_scripts(text):
    """这份反验是不是 `copytree` 搬了**整个** `scripts/` 目录。

    搬整目录时，被测闸门的每一个本地依赖**必然都在**临时目录里——
    **而按闸门逐个去核搬运语句会把它报成「没搬」**。实测
    `selftest-selftest-bootable.py` 就是这个形态：它 `copytree(SCRIPTS, tmp/scripts)`，
    于是 `baseline.py` 早就在那儿了，可按文件核的判据报它没搬。
    **判据必须能说出「它已经整体搬过了」这句话，而不只是「某个文件搬过了」。**
    """
    return bool(re.search(r"copytree\w*\(\s*\w+\s*,\s*[^)]*scripts", text))


def copies_module_into_scripts(text, module):
    """这个本地模块有没有被搬进某次 `shutil.copy*` 调用的目标里。

    **Batch 190 修第三处按写法判定**：原式用正则找
    `copy(单词, …含 scripts… 且以 "xxx.py" 结尾)`——**要求模块名以字面量出现在目标路径中**。
    于是 `shutil.copy(os.path.join(HERE, name), os.path.join(tmp, "scripts", name))`
    （**循环搬多份文件**）被报成「没搬」。实测本批的 `selftest-scope.py` 正撞在这上面。

    修法：**解析每个 `shutil.copy*` 调用的实参**，看模块名在不在这条搬运动作里。
    **「这个文件有没有被搬」是行为，「目标路径里有没有写着它的名字」是写法**——
    循环搬运时名字写在变量里，而搬运照样发生了。
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if not (isinstance(f, ast.Attribute) and f.attr.startswith("copy")
                and isinstance(f.value, ast.Name) and f.value.id == "shutil"):
            continue
        args = list(node.args) + [k.value for k in node.keywords]
        for a in args:
            try:
                if module + ".py" in ast.unparse(a):
                    return True
            except Exception:
                pass
    return False


def main():
    if not os.path.isdir(SCRIPTS):
        print(f"[skip] 找不到 {SCRIPTS}，跳过反验依赖核对")
        return 2

    selftests = sorted(f for f in os.listdir(SCRIPTS)
                       if f.startswith("selftest-") and f.endswith(".py"))
    problems = []
    checked = 0
    for fn in selftests:
        p = os.path.join(SCRIPTS, fn)
        try:
            with open(p, encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            continue
        if not copies_gate_into_tmp(text):
            continue
        # 这份反验搬了哪些闸门脚本——见 independent_gate_names 的 docstring：
        # **只用 AST 认独立字符串常量**，否则注入夹具里伪造的闸门名会被当成真搬运。
        gate_names = sorted(independent_gate_names(text, SCRIPTS))
        if not gate_names:
            # **Batch 197 实测出来的假阴性**：`independent_gate_names` 遇 `SyntaxError`
            # 直接 `return names`（空集），于是这份反验被 `continue` 整份跳过——
            # **而本闸报出的份数会跟着变小，且它报得很绿**。
            # 实测：我把 3 份反验插坏（缩进错 → IndentationError），
            # 本闸的「N 份反验会把闸门复制进临时目录」**从 15 掉到 12，rc 仍是 0**。
            # 这是纪律 156 的又一次：判据报出的「它核了几项」少了 3，而没人看得出来。
            # 闸 18 能抓到「反验语法坏掉」，但**它修不了本闸自己那个少掉的数字**。
            try:
                ast.parse(text)
            except SyntaxError as exc:
                problems.append(
                    f"方向一：`{fn}` 看起来会把闸门复制进临时目录，"
                    f"**但它语法错误（{exc.msg}，第 {exc.lineno} 行），本闸已整份跳过它**——"
                    "于是本闸报出的「份数」会少算它，而 rc 仍可能是 0"
                    "　→ 这就是「一个都没检查」与「全部都检查了」长得一样。"
                    "语法本身由闸 18 负责，但**少算的份数只有本闸自己能看见**")
            continue
        # 整目录搬运：依赖必然齐备，不逐个核（否则会误报）
        if copies_whole_scripts(text):
            checked += 1
            continue
        checked += 1
        for gname in gate_names:
            deps = local_imports(os.path.join(SCRIPTS, gname))
            if deps is None:
                problems.append(f"方向一：读不了 scripts/{gname}")
                continue
            for d in sorted(deps):
                # **必须核「有真实的搬运动作」，而不是「文本里提到过这个名字」**
                # （反验用例 2 上线首跑就抓到这个：原判据是 `if d in text: continue`，
                #  而反验里那行 `BASELINE = os.path.join(HERE, "baseline.py")`
                #  **本身就含有 "baseline" 这个子串**——于是把搬运语句删掉，
                #  判据照样说「搬过了」。**判据把自己的准备工作当成了证据。**
                #
                # **Batch 190 修第三处「按写法判定」**：收紧后的正则要求模块名
                # 以**字面量**出现在搬运语句的目标路径里，于是
                # `shutil.copy(os.path.join(HERE, name), os.path.join(tmp,"scripts",name))`
                # 这种**循环搬多份文件**的写法被报成「没搬」——而它搬得清清楚楚。
                # **「搬没搬」是行为，「目标路径里有没有写着它的名字」是写法**。
                # 改用 AST 解析每条 `shutil.copy*` 的实参（见 copies_module_into_scripts）。
                #
                # 本闸 Batch 190 一共修掉**三处同源**的写法依赖：
                # ①认定「被测闸门是谁」靠变量赋值链；②认定「会不会复制」靠参数形状；
                # ③认定「搬没搬」靠目标路径里的字面量。**三处都是同一个病：
                # 判据认的是写法，而它该认的是事实。**
                if copies_module_into_scripts(text, d):
                    continue
                problems.append(
                    f"方向一：{fn} 把 {gname} 复制进临时目录跑，"
                    f"但被测闸门 import 了本地模块 `{d}`，而反验**没有把它复制进临时 scripts/**"
                    "　→ 临时目录里 import 失败，**该反验的每一例都会失败**，"
                    "**而 build-site.sh 仍然全绿**（Batch 178 实测：34 例跨 3 个批次全坏）")

    if checked == 0:
        print("[skip] 没有反验把闸门复制进临时目录——判据可能已失效，请先确认")
        return 2

    if problems:
        print("反验依赖核对：%d 处不自洽" % len(problems))
        for p in problems:
            print("  ✗ " + p)
        return 1

    print("反验依赖核对通过：%d 份反验会把闸门复制进临时目录，"
          "其被测闸门的本地依赖均已一并搬运" % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
