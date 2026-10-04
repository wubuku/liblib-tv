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
from stagedeps import CHILD_ENV_FN, local_closure, local_imports


def writes_gate_into_tmp(text):
    """这份反验有没有用 `open(…, "w").write(…)` 把**闸**写进临时 `scripts/`。

    **Batch 265 新增这一支**，而它是**「判据认写法不认事实」的第 5 次复发**
    （前四次：Batch 190 的两处、239、247）。

    **实测出来的后果**（Batch 264）：`selftest-shot-version-source.py` 的
    `copy_gate()` 用 `open(os.path.join(d, "scripts", GATE), "w")` + `f.write(src)` 搬闸
    ——**因为它要把 `OFF_TASK` 免检表清空，而 `shutil.copy` 做不到「搬过去再改」**——
    **而 `copies_gate_into_tmp()` 只认 `shutil.copy` / `stage_gate` / `stage_all` / `copytree`**，
    **于是那份反验被整份跳过**：实测它 **13 例里 11 例转红**（`ModuleNotFoundError`），
    **而闸一声不吭、报得很绿**。**漏报比误报危险——误报有人去改，漏报一路绿到缺陷真的发作。**

    **判据问的是「目标路径是不是临时 `scripts/` 下那个闸名」，不问写法**：
    `open().write()` 与 `shutil.copy` 达到**同一个事实**。

    **为什么要求路径里出现真正的闸名**（而不仅是有 `open(…"scripts"…, "w")`）：
    **反验里往 `scripts/` 写东西的地方很多**——写夹具反验自己、写注入用的假闸。
    **只按「往 scripts 写」判，会把本闸自己那份反验也算成搬闸**
    （它的 `_env_fixture` 天天往 `tmp/scripts/` 写夹具文件）。
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    consts = _module_consts(tree)

    def is_gate(b):
        return (isinstance(b, str) and b.startswith("verify-") and b.endswith(".py")
                and os.path.isfile(os.path.join(SCRIPTS, b)))

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        f = node.func
        if not ((isinstance(f, ast.Name) and f.id == "open")
                or (isinstance(f, ast.Attribute) and f.attr == "open")):
            continue
        path = ast.unparse(node.args[0])
        if '"scripts"' not in path and "'scripts'" not in path:
            continue
        mode = ast.unparse(node.args[1]) if len(node.args) > 1 else ""
        if '"w' not in mode and "'w" not in mode:
            continue
        # ① 路径里直接写着闸名的字面量
        for sub in ast.walk(node.args[0]):
            if isinstance(sub, ast.Constant) and is_gate(os.path.basename(sub.value or "")):
                return True
        # ② 路径里写的是模块级常量（`os.path.join(d, "scripts", GATE)`）
        for cn, cv in consts.items():
            if cn in path and is_gate(os.path.basename(cv)):
                return True
    return False


def _called_names(text):
    """这份源码里**真的被调用**的点分名（AST；语法坏掉时返回空集）。

    **Batch 279 新增。** 它替代 `copies_gate_into_tmp()` 里那三条全文正则——
    **而那三条会把注释与字符串字面量当成代码**。

    **实测的缺陷**：`selftest-zero-input.py` 的 `READONLY_EXEMPT` 里有一个
    **字符串键** `'shutil.copytree(HERE, sdir)'`（Batch 274 给闸 39 登记豁免时写的），
    `re.search(r"shutil\.copy\w*\(", text)` **命中了它**——
    于是一份**根本不搬闸**的反验被划进搬闸群体，
    闸 17 转而去核它的依赖搬运，**报出 5 条假红**。
    **而这个缺陷是先前就有的**，一直被 `stagedeps.stage_all()` 掩盖着；
    **把那份反验的 `empty_tree()` 删掉才把它露出来**。

    **为什么这一处值得单独写一个函数**：同一份文件里
    `writes_gate_into_tmp()` 早就是 AST 的（Batch 265 写的），
    `staged_gates()` / `independent_gate_names()` 也是——
    **两种口径并存，差的就是这一处**，而**混着用的后果不是「慢一点」，
    是「一份反验被划进错误的群体，而它自己完全不知道」**。

    **语法坏掉时返回空集**（不回退到全文正则）：
    理由与 `writes_gate_into_tmp()` 一致——**解析不了是「核不到」不是「核过了」**，
    而那份文件的语法另有闸 18 方向一负责。
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set()
    names = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if isinstance(f, ast.Name):
            names.add(f.id)
        elif isinstance(f, ast.Attribute):
            names.add(ast.unparse(f))
    return names


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
    called = _called_names(text)
    has_copy = any(n.rsplit(".", 1)[-1].startswith("copy") for n in called)
    has_staged = any(n.rsplit(".", 1)[-1] in ("stage_all", "stage_gate")
                     for n in called)
    #: **Batch 265 补的这一支**：`open(…"scripts"…, "w")` 也是搬闸。
    #: **它不要求同时出现 `tempfile.mkdtemp`**——
    #: **而 `selftest-shot-version-source.py` 用的是 `tempfile.mkdtemp(prefix=…)`，认得**；
    #: **但一旦哪天换成别的建目录方式，那一支又会落空**——
    #: **所以这一支只看「往临时 scripts/ 写了闸」这个事实本身**。
    has_mkdtemp = any("mkdtemp" in n for n in called)
    return ((has_copy or has_staged or writes_gate_into_tmp(text)) and has_mkdtemp)


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


#: **Batch 260 新增。** 哪两个本地模块**会认那个环境变量**：
#: `baseline.py` 与 `scope.py` 都写成
#: `os.environ.get("BEEFTV_MANUAL_ROOT") or <按 __file__ 推断>`——
#: **变量优先于文件位置**（Batch 178 加它的理由就是为了让搬过树的闸能指回原处）。
#: 而绝大多数闸自己的 `ROOT` 是 `dirname(HERE)`，**它只认自己所在的位置**。
#: **两种约定并存，就出现一个没人管的组合**：反验把闸搬进临时树再真跑它，
#: **却没告诉它「手册根是你自己那棵树」**——
#: 变量没设时凑巧对（都指向真树），**变量被别人设了就整棵读错**。
ROOT_ENV = "BEEFTV_MANUAL_ROOT"
#: **认这个变量的本地模块**：闭包里出现它们，闸就可能被指到别的树上去。
ENV_AWARE_MODULES = ("baseline", "scope")



def _string_of(node):
    """求一个表达式的「字面量那一截」。

    **闸名在反验里几乎从不直接写成字面量**，实测本树上全是
    `GATE = os.path.join(HERE, "verify-exclusions.py")`——
    **只认 `ast.Constant` 的话模块级常量表是空的，于是这一类全部判不出闸名**
    （本模块第一版就是这么写的，而它报出「0 处」，看起来像「全都合规」）。
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "join"):
        return "".join(filter(None, (_string_of(a) for a in node.args)))
    return None


def _module_consts(tree):
    """模块级 `NAME = <一段字符串>` → {NAME: 那段字符串}。"""
    out = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name):
            v = _string_of(n.value)
            if v:
                out[n.targets[0].id] = v
    return out


def calls_pinning_root(text):
    """**每一次**跑 env-aware 闸的子进程调用，那一次都得把手册根钉死送进去。
    **前置条件是「真跑」而不是「搬了」**（Batch 260 立的，Batch 262 保留）：
    `selftest-duplication.py` 把三个闸搬进临时树，**但只把它们当文本扫**、从不执行，
    **什么事也没有**——**而第一版口径按「搬了」算，于是把这一份误报成缺陷**。
    **只有真跑才会读到那个环境变量**，所以问的必须是「跑了」不是「搬了」。


    返回 `(缺陷列表, 这份反验真跑过的 env-aware 闸)`。
    **缺陷列表为空**且第二个值非空 = 每一处都合规；
    **两个都空** = 这份反验压根没真跑那种闸，**不归这个方向管**。

    **为什么要升级口径（Batch 262）**：
    原判据只问「**这份反验的源码里有没有出现过** `BEEFTV_MANUAL_ROOT`」——
    **而写成 `e = {**os.environ, "BEEFTV_MANUAL_ROOT": …}` 的那几份，
    它们的变量名出现在「沙箱」那一次调用里**，
    于是**「跑真树」那几次完全不传 env 的调用被判成合规**。
    实测三份在 `BEEFTV_MANUAL_ROOT=/tmp` 下 rc=1
    （`读不到 /tmp/20-reference.md`），**而闸一直报 rc=0**。
    **判据问的是「有没有写过」，被测行为是「每一次调用送没送进去」**
    （纪律 176 同族：判据问得比它需要回答的浅一层）。

    **推论一**：**只升级这一半还不行**。收敛之后那些源码里
    **再也没有那个变量的字面量了**（都变成 `child_env(…)`），
    **旧口径会把本批刚做完的 32 处收敛全报成缺陷**——
    实测预演报了 4 份，全是合规的。
    **两种各自正确的约定并存时，洞在组合里，不在任何一边**（纪律 290 推论三）：
    一个是「那个键该集中在一处设」，另一个是「判据认那个键的字面量」，
    **单看都无懈可击，合起来就成了「收敛即违规」**。
    所以认法必须**两者都认**。

    **推论二**：**认法只有一份**——构造函数名从 `stagedeps` 里读，
    **不在本文件里再写死一遍**（见 `CHILD_ENV_FN` 上面那段话）。

    **推论三**：**还要追一格**。`env=env` 那种「先赋值再传」是合规的，
    **而它占了这些反验的大多数**——不追这一格，预演把 4 份合规的报成了缺陷。
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return [], set()
    consts = _module_consts(tree)
    binds = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name):
            binds.setdefault(n.targets[0].id, []).append(ast.unparse(n.value))
    pins = (CHILD_ENV_FN + "(", ROOT_ENV)
    hits, ran = [], set()
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in ("run", "Popen", "call",
                                       "check_call", "check_output")):
            continue
        seg = ast.unparse(node)
        #: **闸名有两条来路，漏掉任何一条都是假阴性**（真缺陷不被报）：
        #:   ① 实参里**直接写着** `"…/verify-x.py"`；
        #:   ② 实参里写的是模块级常量 `GATE`，值由 `os.path.join(HERE, "verify-x.py")` 拼出来。
        #: **第一版只写了 ②**——于是闸 17 自己的反验夹具（它用 ①）整批落空，
        #: 用例 13 与 15 双双报绿，**而闸当时确实有缺陷**。
        #: **鉴别力验证的夹具只用了 ②，所以没照出来**：
        #: **注入用的形态必须覆盖被测代码认得的那几种，否则验证验的是「我写的那一种」。**
        gate = None
        for a in list(node.args) + [k.value for k in node.keywords]:
            for sub in ast.walk(a):
                if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                    b = os.path.basename(sub.value)
                    if b.startswith("verify-") and b.endswith(".py") \
                            and os.path.isfile(os.path.join(SCRIPTS, b)):
                        gate = b[:-3]
                        break
            if gate:
                break
        if not gate:
            #: **这一步必须确认「这一次调用真的引用了那个常量」**——
            #: 不确认的话，**同一文件里任何一句 `subprocess.run(["git", …])` 都会被配上 GATE**
            #: （`selftest-label-drift.py` 实测：那四处全是 git 命令，
            #: **git 不认那个变量，给它钉死纯属自己编出来的行为变更**）。
            for cn, cv in consts.items():
                b = os.path.basename(cv)
                if b.startswith("verify-") and b.endswith(".py") and cn in seg \
                        and os.path.isfile(os.path.join(SCRIPTS, b)):
                    gate = b[:-3]
                    break
        if not gate:
            continue
        if not (set(ENV_AWARE_MODULES) & set(local_closure(gate))):
            continue
        ran.add(gate)
        envk = [k for k in node.keywords if k.arg == "env"]
        if not envk:
            hits.append((node.lineno, gate, f"**没有 `env=`**"))
            continue
        e = ast.unparse(envk[0].value).strip()
        if any(p in e for p in pins) or \
                any(any(p in b for p in pins) for b in binds.get(e, [])):
            continue
        hits.append((node.lineno, gate,
                     f"`env={e}` **送进去的键里没有 `{ROOT_ENV}`**"
                     f"（设了别的键不等于钉死了手册根）"))
    return hits, ran


def env_not_pointed_back(selftests):
    """返回 (缺陷列表, 已合规份数)。

    **判据问的是每一次调用**（`calls_pinning_root`），
    **不是「这份反验的源码里有没有出现过那个变量名」**——
    **后者会把「跑真树那几次不传 env」判成合规**（Batch 262 实测三份因此转红而闸报绿）。

    **前置条件也一并放宽**：原来要求「先把闸搬进临时树」，
    **而「跑真树」那几次根本不搬**——
    **搬没搬与要不要钉死是两件事**：**闸会读那个变量，是因为它跑了，不是因为它被搬过**。
    「只把闸当文本扫、从不执行」的那些（`selftest-duplication.py`）仍然不归这个方向管。
    """
    problems, ok_n = [], 0
    for fn in selftests:
        p = os.path.join(SCRIPTS, fn)
        try:
            with open(p, encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            continue
        hits, ran = calls_pinning_root(text)
        if not ran:
            continue
        if not hits:
            ok_n += 1
            continue
        bad = "；".join("第 %d 行那次（跑 %s）%s" % (ln, g, why) for ln, g, why in hits)
        problems.append(
            f"方向一之二：{fn} 真跑 {'、'.join(sorted(ran))}，"
            f"而那些闸的依赖闭包里 {'/'.join(ENV_AWARE_MODULES)} "
            f"**认 `{ROOT_ENV}`**——**{bad}**"
            "　→ 那个变量没设时凑巧对（都指向真树），"
            "**而它被别人设了（例如这份反验本身被另一份反验调用）就整棵读错**。"
            f"**实测 Batch 259：`{fn}` 这一族在变量指向别处时整份反验转红**，"
            f"而指向真树时**全绿**——**正好是最容易骗过人的那一种**。"
            f"　→ 修法：起子进程时 `env={CHILD_ENV_FN}(<它自己那棵树>)`"
            f"（要顺手多设别的键就写成 `{CHILD_ENV_FN}(<树>, 键=值)`）")
    return problems, ok_n


#: **`$` 不能直接写进正则 raw string 的拼接位**——写进去就不是字符串了，
#: **而它不在拼接位、只写在字符串里又是合法的**（docstring 里那两处就是）
#: （Batch 266 实测：三种写法各踩一次，最后走模块级常量）。
DOLLAR = chr(36)


def sh_gate_form(text):
    """这份 `.sh` 反验属于**哪一种形态**，认不出来返回 `""`（空 = 不合法）。

    **Batch 266 新增，实测前后改了两次。** 第一版只认「搬数据文件」一种，
    **结果四份 `.sh` 全红**——**而实测它们明明都合规**：
    **`cp "$ROOT/20-reference.md"` 在 `selftest-tables.sh` 里写得清清楚楚**
    （纪律：判据报红先问「哪一侧错了」，而这一侧就是我）。
    **所以先把形态量全，再写判据**——**四份 `.sh` 分三类，不是一类**：

    **S1 搬闸**：把闸本身与依赖 `cp` 进临时 `scripts/`，跑临时树里那份。
    实测 `selftest-link-labels.sh`：
    `cp "$HERE/verify-link-labels.py" "$WORK/scripts/"` +
    `cp "$HERE/headingkey.py" "$WORK/scripts/"`——**它搬的是「被跑的代码」**。

    **S2 搬数据**：闸**不搬**，按**真树绝对路径**跑（`GATE="$HERE/verify-tables.py"`），
    临时树只提供被改的 `.md`（闸的 `root` 取 `sys.argv[1]`）。
    实测 `selftest-tables.sh`：`mkdir -p "$WORK/scripts"` 建了目录，
    **却一个 `scripts/` 里的东西都没搬**，而闸照跑不误——
    **因为闸的 `sys.path` 指向真树那份 `scripts/`，`from tablerow import …` 找得到。**
    **它搬的是「被核对的数据」。**

    **S3 造合成输入**：**完全不碰真树**——
    要么在 `git` 对象层造（`selftest-unreachable.sh` 用 `hash-object` / `commit-tree`
    造临时 ref，**头里明写「不改工作树、不动任何现有分支」**），
    要么做快照回滚（`selftest-meta.sh` 的 `cp "$f" "$SNAP/$f"` + 退出时还原）。
    **它们改的是「输入的来源」，不是工作树**。

    **三种形态互斥吗？不。** 一份反验可以既搬闸又搬数据；
    **判据只问「它的注入打在哪里」，而那三种落点都是安全的**。

    **返回空串 = 哪种都不属于**：**那它的每一次注入都直接打在真树上**——
    **闸会红，红的是别人的手册，而反验自己不留痕**。
    **那比不写反验更糟**，因为「有一个反验在看着这个闸」这句话仍然是成立的。
    """
    # **路径一律写成 `$VAR`（shell 里 `$VAR` 后面跟 `/` 不会歧义）——
    # 判据要认的正是这个写法，而 `[\n]*` 之后接 `$` 在正则里是合法的**。
    # 第一版写成 `$$?` 而 `?` 量的是前一个 `$`——**于是正则变成「nothing to repeat」**，
    # **而 `re.error` 是运行时才抛的，AST 解析照样通过**（纪律 224 的又一次）。
    q = re.escape(DOLLAR)         # 正则里的字面 $

    # S1：把闸本身 cp 进临时树（`cp "$HERE/verify-x.py" "$WORK/scripts/"`）
    if re.search(r'\bcp\s+"?' + q + r'HERE/verify-[a-z0-9-]+\.py[^\n]*' + q + r'WORK', text):
        return "S1 搬闸（闸与依赖都 cp 进临时 scripts/，跑临时树里那份）"

    # S2：闸按真树绝对路径跑 + 把被核对的手册文件搬进临时树
    # **三支不是互斥的 elif**——**第一版写成互斥的，结果
    # `selftest-meta.sh` 命中了 `GATE="$HERE/…"` 就 `return ""`，**
    # **而它其实还写着 `cp "$f" "$SNAP/$f"` 的快照回滚**。
    # **一份反验完全可能同时具备两种落点，而「任一落点安全」就够**（下面 S3 那支）。
    gate_abs = re.search(r'GATE="?' + q + r'HERE/verify-[a-z0-9-]+\.py', text)
    if gate_abs and re.search(r'\bcp\s+[^\n]*' + q + r'ROOT/', text):
        return ("S2 搬数据（闸按真树绝对路径跑、临时树只提供被改的 .md；"
                "闸的 sys.path 指向真树 scripts/，它的本地依赖照样找得到）")

    # S3：不碰工作树，注入打在 git 对象层或快照回滚上
    if re.search(r'\b(hash-object|commit-tree|mktree|update-index)\b', text):
        return "S3 造合成输入（git plumbing 造临时 ref，不改工作树）"
    if re.search(r'\bcp\s+[^\n]*' + q + r'SNAP', text):
        return "S3 快照回滚（先备份被注入的文件，退出时还原）"
    return ""


def sh_reports_form(problems, shell_tests):
    """把 `.sh` 反验的形态逐条核一遍，并把结论带出去。"""
    forms = {}
    for fn in shell_tests:
        try:
            with open(os.path.join(SCRIPTS, fn), encoding="utf-8") as fh:
                text = fh.read()
        except OSError as exc:
            problems.append(f"方向三：`{fn}` **读不到**（{exc}）——"
                            f"**本闸已整份跳过它，于是它既没被核、也没被说**")
            continue
        form = sh_gate_form(text)
        if not form:
            problems.append(
                f"方向三：`{fn}` **既不搬闸、也不搬被核对的数据、也不造合成输入**——"
                "**那么它的每一次注入都直接打在真树上**，"
                "**闸会红、红的是别人的手册，而反验自己不留痕**"
                "　→ 这比不写反验更糟："
                "**「有一个反验在看着这个闸」这句话仍然是成立的**")
            continue
        forms[fn] = form
    return forms


def main():
    if not os.path.isdir(SCRIPTS):
        print(f"[skip] 找不到 {SCRIPTS}，跳过反验依赖核对")
        return 2

    selftests = sorted(f for f in os.listdir(SCRIPTS)
                       if f.startswith("selftest-") and f.endswith(".py"))
    #: **Batch 266 新增：`scripts/` 下不止 `.py`，还有 `.sh`。**
    #: **而本闸从头到尾只扫 `.py`**——**所以 `.sh` 反验是本闸的视野外**，
    #: **而它们一个都不是「不搬闸的反验」**（Batch 262 实测过那种）：
    #: **`selftest-tables.sh` 明写「只复制被改的三个文件 + 目录骨架，够闸门跑即可」**，
    #: 它 `mkdir -p "$WORK/scripts"` 建了目录、**却一个 `scripts/` 里的东西都没搬**，
    #: **而闸仍然能跑**——因为闸是**按绝对路径**跑的（`GATE="$HERE/verify-tables.py"`），
    #: `sys.path` 指向**真树那份 scripts/**，所以 `from tablerow import …` 找得到。
    #: **这是第二种形态，与「搬闸进临时树」互斥但同样成立。**
    #: **为什么必须把它报出来**：**Batch 265 修的正是「判据少认一支」**，
    #: **而这里连「有几种形态」都没被量过**——**本闸报出的「26 份」听上去像全部，
    #: 实际 `scripts/` 下有 29 份 `selftest-*`**，
    #: **而差的那 3 份既没被核、也没被说**（纪律 300 推论一）。
    shell_tests = sorted(f for f in os.listdir(SCRIPTS)
                         if f.startswith("selftest-") and f.endswith(".sh"))
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

    # ── 方向三（Batch 266）：本闸的视野外有什么，必须说出来 ──────────
    sh_forms = sh_reports_form(problems, shell_tests)

    # ── 方向一之二（Batch 260）：真跑了闸，就得告诉它手册根在哪 ──────
    env_problems, env_ok = env_not_pointed_back(selftests)
    problems.extend(env_problems)

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
    print("  手册根指回：%d 份反验真跑会用 `baseline`/`scope` 的闸，"
          "**都已给子进程设 `%s`**（方向一之二）" % (env_ok, ROOT_ENV))
    if shell_tests:
        #: **鉴别力实测出来的**：摘掉 `sh_reports_form` 的调用之后，
        #: 这个分支**照样会印出「视野外：另有 4 份」这个标题，只是下面一行形态都没有**——
        #: **而「有标题、没内容」正是纪律 300 推论四那个形状**：
        #: **一个什么都没核的闸，看起来和核过了的闸一模一样。**
        #: **所以两个数必须一起印，缺一个就当成没核过**：
        if len(sh_forms) != len(shell_tests):
            missing = sorted(set(shell_tests) - set(sh_forms))
            print("  **视野外：另有 %d 份 `.sh` 反验，其中 %d 份认出了形态、"
                  "%d 份没认出来**（`selftests` 只收 `.py`）：%s"
                  % (len(shell_tests), len(sh_forms),
                     len(shell_tests) - len(sh_forms), "、".join(missing)))
        else:
            print("  **视野外：另有 %d 份 `.sh` 反验不被上面两个方向核**"
                  "（`selftests` 只收 `.py`）——"
                  "**「没被核」与「核过且合规」在输出上完全一样**，"
                  "**所以下面必须逐条列出形态，而不能只报一个份数**：" % len(shell_tests))
        for fn in sorted(sh_forms):
            print("    · %s → %s" % (fn, sh_forms[fn]))
        print("    **S1 搬的是「被跑的代码」、S2 搬的是「被核对的数据」、"
              "S3 造的是「合成的输入」——三者互不替代，"
              "而共同点是：注入没有一处直接打在真树上**。"
              "**这一族在方向一之前从未被量过**（方向三）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
