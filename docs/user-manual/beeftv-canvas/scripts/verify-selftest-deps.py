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

# **Batch 253：`local_imports` / `local_closure` 已搬走，这里改成 import。**
# 「一个闸门的本地依赖闭包是什么」**是同一个概念在两侧各有一份实现**：
# 搬运侧是 `stagedeps.stage_gate()`，判据侧是本模块。
# **纪律 274 推论一：判据之间有共享概念时，那个概念只能有一份实现。**
# 合成一份的理由不是洁癖：**两边对某一种 import 形态的理解一旦不同，
# 判据就会判「齐了」而闸在临时目录里起不来**——
# 而那正是「反验每一例都失败、构建全绿」那条老路（Batch 178）。
# 合并前实测两份实现对 4 个闸门的闭包**逐条相同**（verify-meta / verify-exclusions /
# verify-version-coverage / verify-line-counts），**行为一字未变**。
from stagedeps import local_closure, local_imports


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
    # **Batch 253 补第三种搬运方式**：`stagedeps.stage_all()` / `stage_gate()`
    # **一个 `shutil.copy` 都不写**（搬运藏在被调用的函数里），
    # 于是只认 `shutil.copy` 的判据会**把这份反验整份跳过**——
    # 而本闸报出的「N 份反验」会跟着变小、**rc 仍然是 0**。
    # **实测就发生在本批**：`selftest-zero-input.py` 改用 `stage_all()` 之后，
    # 本闸的份数从 24 掉到 23，**没有任何一行报错**。
    # **这正是纪律 156 说的那种失效**：「一个都没检查」与「全部都检查了」长得一样。
    # **所以判据里凡是「这份反验做了 X」的前提条件，都必须跟着搬运手段一起更新。**
    has_copy = bool(re.search(r"shutil\.copy\w*\(", text))
    has_staged = bool(re.search(r"\bstage_(?:all|gate)\s*\(", text))
    return (has_copy or has_staged) and bool(re.search(r"tempfile\.mkdtemp", text))


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

    **⚠️ Batch 247 修第四处按写法判定——同一个病第四次在同一处复发。**
    原式是 `copytree\w*\(\s*\w+\s*,\s*[^)]*scripts`：它要求
      ① 第一个实参是**一个裸单词**（模块级常量名）；
      ② 第二个实参里**直接出现 `scripts` 这几个字母**。
    于是 `shutil.copytree(os.path.join(ROOT, "scripts"), dst, ignore=...)`
    这种同样搬了整份 `scripts/` 的写法被判成「没搬」——
    **而 `selftest-retracted-claims.py`（Batch 247 新增）正是这个形态**，
    闸 18 当场把闸 17 的反验判红（4 例失败）。**前三次分别见 Batch 190 的两处
    与 Batch 239 的一处，四次的病完全一样：判据认的是写法，而它该认的是事实。**

    改法：解析每条 `copytree` 调用的**两个位置实参**，
    看其中有没有 `"scripts"` 这个**路径末段字面量**——
    **源或目标任一侧写着它就算**，因为 `copytree(A, B)` 搬的是 A 底下的一切，
    而 A 是 `…/scripts` 与 B 是 `…/scripts` 都能保证「整份 scripts 到了临时目录」。
    **仍然不是「凡是有 copytree 就算」**：源与目标都不含 `scripts` 时照样不认
    （那会把「搬了另一个目录」当成搬了 scripts/，而依赖同样不在）。
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        fname = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
        if not fname.startswith("copytree"):
            continue
        for arg in node.args[:2]:
            for sub in ast.walk(arg):
                if isinstance(sub, ast.Constant) and sub.value == "scripts":
                    return True
    return False


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
    # **Batch 239 补第三条路径：循环搬运。** 上面的实参里若是个变量
    # （`os.path.join(HERE, dep)`），模块名不在其中，于是
    # `for dep in DEPS: shutil.copy(..., os.path.join(d, "scripts", dep))`
    # 这种**搬得清清楚楚**的写法被报成「没搬」——**同一个病第三次在同一处复发**
    # （前两次见上面 Batch 190 的注释）。
    # **收紧到只有一种形态算数**：循环的可迭代对象是**模块级常量**，
    # 且那个常量的元素里**确实写着这个模块名**。
    # **「凡是循环就算」是错的**——那会让任何 `for x in anything:` 都通过。
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False

    # 模块级常量：名字 → 元素列表（只认字面量组成的 tuple / list）
    consts = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        tgt = node.targets[0]
        if not isinstance(tgt, ast.Name):
            continue
        try:
            val = ast.literal_eval(node.value)
        except Exception:
            continue
        if isinstance(val, (tuple, list)) and all(isinstance(x, str) for x in val):
            consts[tgt.id] = list(val)

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

    # —— 循环搬运：先认出「这个 copy 调用在哪个 for 循环里」——
    want = module + ".py"
    for loop in [n for n in ast.walk(tree) if isinstance(n, ast.For)]:
        it = loop.iter
        # **只认「可迭代对象是一个模块级常量的名字」这一种**：
        # `for dep in DEPS` 认；`for dep in glob("*.py")` 不认——
        # 后者搬的东西判据无从知道，**判不出来的事不许当通过**。
        if not (isinstance(it, ast.Name) and it.id in consts):
            continue
        if not any(want in s for s in consts[it.id]):
            continue
        targets = {n.id for n in ast.walk(loop.target) if isinstance(n, ast.Name)}
        if not targets:
            continue
        for node in ast.walk(loop):
            if not isinstance(node, ast.Call):
                continue
            f = node.func
            if not (isinstance(f, ast.Attribute) and f.attr.startswith("copy")
                    and isinstance(f.value, ast.Name) and f.value.id == "shutil"):
                continue
            args = list(node.args) + [k.value for k in node.keywords]
            for a in args:
                # 实参里出现了循环变量 → 这一次搬运按该常量的元素走
                if any(isinstance(x, ast.Name) and x.id in targets
                       for x in ast.walk(a)):
                    return True
    return False


def staged_gates(text):
    """这份反验用 `stage_gate(...)` 搬了**哪些闸**。

    **Batch 253 新增。** `stagedeps.stage_gate(tmp, "verify-foo")` 会解析
    `verify-foo` 的本地依赖闭包并全搬走——
    **所以「它搬了那个闸的依赖」这件事，只需要认出实参里写着那个闸名。**
    **为什么这一条是必需的而不是锦上添花**：
    `stage_gate()` 本身一个 `shutil.copy` 都不写（它把搬运藏进被调用的函数里），
    **于是本模块上面那套「解析 copy 调用」的判据会判它「什么都没搬」**——
    **而它搬得比任何显式写法都全**。**判据比搬运手段窄，闸就误报。**

    **只认实参里的字符串字面量**：变量、拼接、推导出来的闸名一律不认——
    **判不出来的事不许当通过**（与下面循环搬运那条同一条规矩）。
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set()
    out = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        name = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
        if name != "stage_gate":
            continue
        for a in node.args:
            if isinstance(a, ast.Constant) and isinstance(a.value, str) \
                    and a.value.startswith("verify-"):
                out.add(a.value)
    return out


def stages_whole_scripts(text):
    """这份反验有没有用 `stagedeps.stage_all()` 搬**整个** `scripts/`。

    **Batch 253 新增**，与 `staged_gates()` 成对：
    `stage_all()` 搬的是全部非反验的 `.py`，**依赖必然齐备**，
    所以对用它的那份反验**不逐个核依赖**——**与 `copies_whole_scripts()` 同等待遇**。
    **为什么要单独写一个而不是复用 `copies_whole_scripts()`**：
    后者认的是 `copytree` 实参里有没有 `scripts` 字样（**写法**），
    前者认的是**一次语义明确的调用**（**事实**）——
    **Batch 190 在这一处修过三次同源的错，本批不引入第四个写法依赖。**
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        name = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
        if name == "stage_all":
            return True
    return False


def main():
    if not os.path.isdir(SCRIPTS):
        print(f"[skip] 找不到 {SCRIPTS}，跳过反验依赖核对")
        return 2

    selftests = sorted(f for f in os.listdir(SCRIPTS)
                       if f.startswith("selftest-") and f.endswith(".py"))
    problems = []
    checked = 0
    #: **Batch 254 新增：把「还有几份靠人记搬运清单」变成可数的事。**
    #: `stagedeps.stage_gate()` / `stage_all()` 之后，「该搬哪些」已经是算出来的，
    #: **而还在手写 `shutil.copy` 清单的那些份，每加一个本地 import 就得人记一次**——
    #: Batch 178/181/197/251/252 **五次漏搬全部发生在这一类反验上**。
    #: **本闸只把数字报出来，不报「必须全部迁移」**：
    #: 一次性改 20 多份反验的出错面远大于它省下的事，**而「还剩 23 份」这件事
    #: 一旦写进构建日志，它就从「没人知道」变成「下一个人接手的起点」**
    #: （纪律 272：把「有几份」变成一件可数的事）。
    staged_n = 0
    for fn in selftests:
        p = os.path.join(SCRIPTS, fn)
        try:
            with open(p, encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            continue
        if not copies_gate_into_tmp(text):
            continue
        if staged_gates(text) or stages_whole_scripts(text):
            staged_n += 1
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
        if copies_whole_scripts(text) or stages_whole_scripts(text):
            checked += 1
            continue
        checked += 1
        # **Batch 253**：`stage_gate()` 搬的是**闭包**，所以对**用 stage_gate 搬过的闸**
        # 不再逐个核依赖——**它搬得比任何显式写法都全，而逐个核只会误报**。
        # **但闸名必须对得上**：给 `stage_gate` 写的是 `verify-别的闸` 而被测闸是本闸，
        # **那它什么都没搬**——**所以判据认的是「实参里写着哪个闸名」，
        # 不是「文件里出现过 stage_gate 这几个字」**。
        staged = staged_gates(text)
        for gname in gate_names:
            if local_imports(os.path.join(SCRIPTS, gname)) is None:
                problems.append(f"方向一：读不了 scripts/{gname}")
                continue
            # **两侧必须同一个形式**：`gate_names` 里的名字**带 `.py`**
            # （它来自 `independent_gate_names`，那边找的是 `"verify-xxx.py"`），
            # 而 `stage_gate(tmp, "verify-xxx")` 的实参**不带后缀**。
            # **本条判据第一版直接拿 `gname in staged` 比，于是恒假**——
            # **反验用例 11 上线首跑就抓到它**（期望放行却报 rc=1）。
            # **这类「两侧形式不一致」的错误一次都不会自己显形**：
            # 判据的默认行为是「没认出来 → 继续按老路逐个核 → 报」，
            # **而那条老路恰好是对的**，所以只有「本该放行」的那一侧才看得出错。
            if gname[:-3] in staged:
                continue
            # **闭包，不是第一层**（Batch 205）：被测闸的直接依赖 + 那些依赖自己的依赖
            deps = local_closure(gname[:-3]) - {gname[:-3]}
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
    print("  搬运方式：**%d 份已用 `stagedeps` 自动算闭包**、"
          "另有 %d 份仍在手写 `shutil.copy` 清单"
          "　→ **后者每加一个本地 import 就得人记一次**，"
          "而 Batch 178/181/197/251/252 **五次漏搬全部发生在这一类上**；"
          "**本闸不要求它们必须迁移**（一次改 20 多份的出错面更大），"
          "**但这个数从此写在构建日志里，而不是记在某个人的脑子里**"
          % (staged_n, checked - staged_n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
