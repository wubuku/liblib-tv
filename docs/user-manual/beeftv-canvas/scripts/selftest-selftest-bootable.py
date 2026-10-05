#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 18「反验启动核对」的反向验证（Batch 179）。

用例清单：
  1  现状全绿                              → 不报
  2  反验语法坏掉                          → 必报（方向一，**它连启动都做不到**）
  3  注入夹具语法坏掉                      → 必报（方向一；夹具坏了，调用它的用例会作废）
  4  shell 反验语法坏掉                    → 必报（方向一，`bash -n`）
  5  反验 import 一个不存在的本地模块      → 必报（方向二）
  6  慢反验夹具打不中锚点                → 必报（方向五，Batch 200）
  7  一个夹具都抽不出来                  → 必报（方向五，**「没检查」≠「全通过」**）
  8  慢反验夹具跑不通                    → 必报（方向五之二，合成 ref 失败那一支）
  9  慢反验夹具没注入特征                → 必报（方向五之二，**与上一条是不同形态**）
  6  **注入夹具不得被当成反验**            → 必须不报（**上线首跑就误报过 58 处**）
  7  真实现状                              → 不报
  8  shell 里出现 `$var：`（UTF-8 locale 下会炸） → 必报（方向十四，Batch 205）
  9  shell 里出现 `${var}：`（任何 locale 都安全）  → 必须不报（**不误伤**）
  8  构建出口哑了（少一个 `|| rc=$?`）        → 必报（方向十三，Batch 204）
  9  构建出口能把三种退出码说清楚             → 必须不报（**不误伤**）
  10  `未能核对` 被说成 `核对不一致`          → 必报（方向十三，**第三个形态**）

**用例 6 是本文件的核心**：闸 18 上线首跑时把 58 份 `selftest-*-fix-*.py`
**注入夹具**当成了反验，报出 58 处「没有指向被测闸门」——
**两类文件的名字都以 `selftest-` 开头，光看前缀分不出来。**
反验必须把这条钉住，否则下一个人会以为「把夹具也登记成反验」是正解。
"""

import ast
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
from stagedeps import child_env

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(ROOT, "scripts", "verify-selftest-bootable.py")
SCRIPTS = os.path.join(ROOT, "scripts")
BUILD = os.path.join(ROOT, "build-site.sh")

results = []

#: 注入锚点**只锚键，不锚值**。
#: 原式写的是整段字面量 `'"selftest-shot-version.py": 2.0,'`——
#: **而那个 `2.0` 是一个会被例行重测刷新的测量值**：Batch 208 把 25 个
#: `SELFTEST_COSTS` 数字全按实测换过一遍（`2.0` → `0.8`），
#: 于是本反验的用例 9 与用例 10 **从那一刻起注入全部失效**，
#: 两条都记成「作废」——**而作废的用例什么都不验却不算通过**（纪律 178/202）。
#: **一次例行的数据刷新，静悄悄废掉了两条守卫方向的用例。**
#: 键名是结构事实（「这份反验在耗时表里有一行」），**刷新数据不会动它**。
COST_KEY = '"selftest-shot-version.py":'


def read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def write(p, t):
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(t)


def run_in(tmp):
    #: **Batch 260**：`verify-selftest-bootable.py` 的依赖闭包里有 `baseline`，
    #: **而 `baseline` 让 `BEEFTV_MANUAL_ROOT` 优先于 `__file__` 推断**——
    #: 不设它时凑巧对（都指向真树），**而它被别人设了就整棵读错**
    #: （闸 17 方向一之二；纪律 289）。**沙箱自己就是这一轮的手册根。**
    e = child_env(tmp)
    r = subprocess.run([sys.executable, os.path.join(tmp, "scripts", "verify-selftest-bootable.py")],
                       cwd=tmp, capture_output=True, text=True, env=e)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def record(name, ok, detail=""):
    """`ok` 既可以是布尔，也可以直接是状态词（`"通过"` / `"失败"` / `"作废"`）。

    **Batch 200 修一个当场抓到的形态**：原来 `main()` 作废一条用例时调的是
    `record(t.__name__, "作废", ...)`，而 `record` 把第二个参数当布尔用——
    **非空字符串恒为真，于是「作废」被记成「通过」，输出里打的是 ✓**。
    实测：方向二那条（`m_missing_local_module`）前提失配，
    输出却是 `✓ m_missing_local_module 前提失配：注入未生效…`——
    **一条什么都没验的用例，在这份「守纪律 178 的反验」里长得和通过一模一样。**
    纪律 178 说的正是这个形态，而它当时就写在这份反验的输出里。
    """
    status = ok if isinstance(ok, str) else ("通过" if ok else "失败")
    results.append((name, status, detail))


def sandbox():
    tmp = tempfile.mkdtemp(prefix="beef-bootable-selftest.")
    shutil.copytree(SCRIPTS, os.path.join(tmp, "scripts"))
    shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-selftest-bootable.py"))
    # **Batch 204：方向十三与方向四c 都要读 `build-site.sh`**（闸唯一的出口）。
    # 沙箱里没有它，方向十三会在**每一个**用例里报「抠不出函数」——
    # 于是不是新加的三条变红，而是全部用例一起变红。
    shutil.copy(BUILD, os.path.join(tmp, "build-site.sh"))
    return tmp


def sandbox_full(break_selftest=None, exit_code=1):
    """**完整**的手册树副本（外加 git init）——方向十六的真跑前提。

    **为什么需要它，而 `sandbox()` 不够**：`sandbox()` 只 copytree `scripts/`，
    **沙箱里没有任务台账、没有任务页、没有真截图**。实测在那种沙箱里真跑 21 份反验，
    `selftest-exclusions.py` / `shot-drift` / `shot-pixels` 三份**因为环境缺口而失败**——
    **而那正是判据最坏的一种错：拿环境的缺口冒充「反验坏了」**。
    实测完整副本 **15.2 MB、拷贝 0.3 秒**，方向十六 21/21 全绿。
    """
    tmp = tempfile.mkdtemp(prefix="beef-bootable-full.")
    for f in os.listdir(ROOT):
        if f in ("node_modules", ".vitepress", "dist", ".git"):
            continue
        src = os.path.join(ROOT, f)
        dst = os.path.join(tmp, f)
        (shutil.copytree if os.path.isdir(src) else shutil.copy)(src, dst)
    _git_init(tmp)
    if break_selftest:
        p = os.path.join(tmp, "scripts", break_selftest)
        t = read(p)
        # **让它崩**——形态与 Batch 207 那次 `FileNotFoundError` 一致：
        # 方向一只保证「能启动」，而崩掉的那份**方向一照样报绿**。
        #
        # **第一版把它追加到文件末尾，用例 23 立刻报红而闸是绿的**——
        # 那些反验都以 `sys.exit(main())` 收尾，**追加的那行永远执行不到**。
        # **这就是「注入必须落在判据真的读的那条路径上」**（Batch 155/157 的原话），
        # 只是这次踩的是自己的注入。修法：插在 `if __name__` **之前**，
        # 那是模块体真正会走到的位置；**并 assert 钉死锚点**。
        anchor = "\nif __name__ =="
        i = t.find(anchor)
        assert i != -1, "前提失配：%s 里找不到 `if __name__` 入口" % break_selftest
        write(p, t[:i] + "\nraise SystemExit(%d)  # Batch 210 用例 23 / Batch 276 用例 31 注入\n"
              % exit_code + t[i:])
    return tmp


def check_anchor():
    t = read(GATE)
    assert "FIXTURE_RE" in t, "前提失配：闸 18 里找不到夹具分类判据"
    assert "SLOW = {" in t, "前提失配：闸 18 里找不到慢反验登记表"
    assert "SELFTEST_COSTS = {" in t, "前提失配：闸 18 里找不到实测耗时表"
    assert "_build_invokes" in t, "前提失配：闸 18 里找不到「只认代码不认注释」的判据"
    assert "_deleted_sibling_names" in t, "前提失配：闸 18 里找不到方向十五「被删掉的引用」判据"
    assert "方向十六" in t, "前提失配：闸 18 里找不到方向十六「真跑反验」判据"
    #: **Batch 275 撤掉过一条断言，理由必须留在原地**：
    #: 本批曾在这里加 `assert "SLOW_COST_RATIO" in t`（断言新方向存在），
    #: **实测结果是鉴别力对照组彻底作废**——`check_anchor()` 是**所有共用用例**
    #: 都会走的前置断言，而**改前闸恰恰没有方向四e**，
    #: 于是 30 例里 28 例「前提失配」、只有 2 例通过。
    #: **而那个结果什么都没证明**：作废的用例根本没跑到被测行为上，
    #: **「锚点断言挡住了对照组」与「判据抓到了缺陷」在报告上长得一模一样**。
    #: **所以这里的规矩是：只允许断言「改前改后都有的东西」——
    #: 新方向在不在，交给新用例自己的断言去发现**（注入不生效会报「失败」，
    #: **而「失败」才是鉴别力实验要的那个信号**，「作废」不是）。


def check_gap_anchor():
    """**26/27 专用的锚点检查——刻意不放进 `check_anchor()`。**

    **为什么刻意分开**（Batch 254 实测出来的）：`check_anchor()` 是**所有**用例的公共前提，
    在这里加一条 `env_gap` 的断言，会让**改前的闸上每一条用例都作废**，
    而不是一个红。**那样就看不出「鉴别力只来自新判据」**——
    **全部一起作废与只有新用例红，在报告上完全一样**（Batch 251 记过同一件事：
    鉴别力必须证明「抽掉新判据只让该红的红，其余仍全过」）。
    所以：**公共锚点归公共，新增判据的锚点归新增判据。**
    """
    t = read(GATE)
    assert "env_gap" in t, ("前提失配：闸 18 里找不到「上游不可用」的环境缺口标记 "
                           "`env_gap`——26/27 验的就是它")
    assert "return (None, False)" in t, \
        "前提失配：闸 18 里找不到那句「resolve_src 不抛异常」的事实依据"


# ── 1 现状 ──────────────────────────────────────────────────────────
def m_clean():
    check_anchor()
    #: **Batch 260 同族第三处**：这一条跑的是**真树**，**它同样要显式指回真树**——
    #: 调用者若把那个变量指向别处，**这一条就会拿一个错误的根去核真树**，
    #: **而症状与改之前一模一样**（纪律 289 推论二）。
    e = child_env(ROOT)
    r = subprocess.run([sys.executable, GATE], cwd=ROOT, capture_output=True, text=True, env=e)
    record("1 真实现状→不报", r.returncode == 0, f"rc={r.returncode}")


# ── 2 反验语法坏掉 ──────────────────────────────────────────────────
def m_broken_selftest_syntax():
    check_anchor()
    tmp = sandbox()
    try:
        p = os.path.join(tmp, "scripts", "selftest-line-counts.py")
        t = read(p)
        write(p, t + "\ndef broken(:\n")
        rc, out = run_in(tmp)
        record("2 反验语法坏掉→必报", rc == 1 and "语法错误" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 3 夹具语法坏掉 ─────────────────────────────────────────────────
def m_broken_fixture_syntax():
    check_anchor()
    tmp = sandbox()
    try:
        p = os.path.join(tmp, "scripts", "selftest-meta-fix-25-coverage-empty-cell.py")
        t = read(p)
        write(p, t + "\ndef broken(:\n")
        rc, out = run_in(tmp)
        record("3 注入夹具语法坏掉→必报", rc == 1 and "注入夹具" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 4 shell 反验语法坏掉 ────────────────────────────────────────────
def m_broken_shell():
    check_anchor()
    tmp = sandbox()
    try:
        p = os.path.join(tmp, "scripts", "selftest-tables.sh")
        t = read(p)
        write(p, t + "\nif [ 1 -eq 1 ; then\n")
        rc, out = run_in(tmp)
        record("4 shell 反验语法坏掉→必报", rc == 1 and "bash -n" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 5 被测闸门 import 一个不存在的本地模块 → 必报 ───────────────────
def m_missing_local_module():
    """注入点选**闸门**而不是反验。

    第一版注入的是 `selftest-feature-flags.py` 里的
    `from baseline import` —— 可那句**在注释里**（Batch 178 把真实 import 改掉了），
    注入脚本因此什么都没改，而断言查的是注入脚本自己写进去的 `nosuchmodule`
    字符串，**照样通过**。**断言查的不是被改后的真实状态**（Batch 166 的教训）。
    现场数据也纠正了设计：**没有任何一份反验 import 本地模块**，
    它们只是把闸门复制进临时目录——**失败面在闸门那一侧**。
    """
    check_anchor()
    tmp = sandbox()
    try:
        p = os.path.join(tmp, "scripts", "verify-feature-flags.py")
        t = read(p)
        # **必须全替换而不是只改第一行**——Batch 200 实测：
        # 原式用 `re.search(...).start()/.end()` 只切掉**第一处**匹配，
        # 而 Batch 197 给 `verify-feature-flags.py` 加了**第二行**
        # `from baseline import SRC as _BEEFSRC`（路径解析收敛到单一来源），
        # 于是断言「baseline 的 import 还在」成立——**这条用例从 Batch 197 起
        # 一直在作废**，而 `record` 把「作废」显示成 ✓，**两层一起把它藏住了**。
        after, n = re.subn(r"^from baseline import[^\n]*$",
                           "from nosuchmodule import resolve_ref", t, flags=re.M)
        assert n >= 1, "前提失配：verify-feature-flags.py 里找不到 `from baseline import` 行"
        write(p, after)
        after = read(p)
        assert "from nosuchmodule import" in after, "注入未生效：真实 import 行没被改"
        assert re.search(r"^from baseline import", after, re.M) is None, \
            "注入未生效：还有 baseline 的 import 残留"
        rc, out = run_in(tmp)
        record("5 闸门 import 不存在的模块→必报", rc == 1 and "nosuchmodule" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 6 注入夹具不得被当成反验（上线首跑误报过 58 处）────────────────
def m_fixture_not_treated_as_selftest():
    check_anchor()
    tmp = sandbox()
    try:
        # 造一份「什么 verify-*.py 都不引用」的夹具：若它被当成反验，方向三必报
        write(os.path.join(tmp, "scripts", "selftest-brandnew-fix-99-orphan.py"),
              "import sys\ns = sys.stdin.read()\nsys.stdout.write(s)\n")
        rc, out = run_in(tmp)
        record("6 夹具被误当反验→必须不报", rc == 0, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 7 无 `fix-` 中段的真反验仍须被识别 ─────────────────────────────
def m_real_selftest_detected():
    check_anchor()
    tmp = sandbox()
    try:
        # 一份**真的**反验（无 fix- 段）却什么都不引用 → 方向三必须报
        write(os.path.join(tmp, "scripts", "selftest-orphan.py"),
              "import sys\nsys.exit(0)\n")
        rc, out = run_in(tmp)
        record("7 真反验缺指向→必报", rc == 1 and "selftest-orphan.py" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 8 慢反验登记成「不慢」（seconds 低于阈值）→ 必报 ─────────────────
def m_slow_entry_under_budget():
    check_anchor()
    tmp = sandbox()
    try:
        p = os.path.join(tmp, "scripts", "verify-selftest-bootable.py")
        t = read(p)
        #: **Batch 275 改锚点**：原锚是 `'"seconds": 97,'`，
        #: 而 Batch 275 把 meta.sh 的登记值据实改成 **101**（实测 100.8，低报要修）——
        #: **锚点锚着一个会被例行更新的数字，于是这条用例差点又一次静默空跑**
        #: （`str.replace` 不中时静默返回原串，用例却仍报通过；纪律 107）。
        new = t.replace('"seconds": 101,', '"seconds": 3,', 1)
        assert new != t, "注入未生效：seconds 没被改小"
        write(p, new)
        rc, out = run_in(tmp)
        record("8 登记为慢但不慢→必报", rc == 1 and "没超过阈值" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 9 漏登记的慢反验 → 必报（**方向四d，本批新增**）─────────────────
def m_slow_not_registered():
    check_anchor()
    tmp = sandbox()
    try:
        p = os.path.join(tmp, "scripts", "verify-selftest-bootable.py")
        t = read(p)
        # 造一份实测 999 秒、却没进 SLOW 的反验
        new, k = re.subn(re.escape(COST_KEY) + r"\s*[\d.]+,", COST_KEY + " 999,", t, count=1)
        assert k == 1, "注入未生效：没找到耗时条目 %s（k=%d）" % (COST_KEY, k)
        write(p, new)
        rc, out = run_in(tmp)
        record("9 变慢却没登记→必报", rc == 1 and "却没登记为慢" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 10 「没量过」必须可见（**方向四d 的另一半**）────────────────────
def m_never_measured():
    check_anchor()
    tmp = sandbox()
    try:
        p = os.path.join(tmp, "scripts", "verify-selftest-bootable.py")
        t = read(p)
        #: **锚点必须锚到「值是秒数的那一行」**（`SELFTEST_COSTS` 的条目形如
        #: `"selftest-x.py": 2.0,`），**而不是「键名相同的头一行」**。
        #: **本批新增的 `TREE_WRITE_EXEMPT` 里就有同名键且排在前面**——
        #: 于是 `count=1` 删掉的是豁免项的第一行，**而那一项是三行的
        #: → 闸当场 `SyntaxError` → rc=1**，
        #: **而用例要的是「报缺实测耗时」：两个条件一个都不满足，
        #: 报告上却只是一条红，看起来像判据坏了。**
        #: **同一个键名在一份文件里出现两次，是这个项目反复踩的那一类**
        #: （纪律 107 的升级版：**锚点不只要稳定，还要唯一**）。
        m = re.search(r"^\s*" + re.escape(COST_KEY) + r"\s*[\d.]+,[^\n]*\n", t, re.M)
        assert m, "注入未生效：闸里找不到 `%s` 的耗时条目" % COST_KEY
        #: **这个键在闸里一共出现几次，如实报进 detail**——
        #: **它现在 >1 是事实而不是错误**（豁免表本来就要列同一批文件名），
        #: **而哪天有人再加一个同名结构，这条 detail 就是预警**。
        same_key = len(re.findall(r"^\s*" + re.escape(COST_KEY) + r"[^\n]*\n", t, re.M))
        write(p, t[:m.start()] + t[m.end():])
        rc, out = run_in(tmp)
        record("10 缺实测耗时→必报", rc == 1 and "没有它的实测耗时" in out,
               "rc=%d 同名键在闸里出现 %d 次（只认值是秒数的那一行）" % (rc, same_key))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 11 注释里提到 ≠ 真调用（方向四c）─────────────────────────────────
def m_comment_is_not_invocation():
    check_anchor()
    tmp = sandbox()
    try:
        # 在**真实的** build-site.sh 副本注释里写上某个反验名 → 不得报「已被自动调用」
        bp = os.path.join(tmp, "build-site.sh")
        with open(bp, "a", encoding="utf-8") as fh:
            fh.write("\n# 顺带提一句 selftest-meta.sh 这个名字\n")
        rc, out = run_in(tmp)
        record("11 注释提到≠调用→必须不报", rc == 0, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 12 慢反验夹具打不中锚点 → 必报（方向五，Batch 200 新增）─────────────
def m_fixture_anchor_missed():
    check_anchor()
    assert "_slow_fixture_triples" in read(GATE), "前提失配：闸 18 里找不到方向五的抽取函数"
    tmp = sandbox()
    try:
        # **这正是 Batch 198 撞上的形态**：作废的用例什么都不验，却不算失败。
        # 改**夹具自己的锚点**：把 `fix-34` 里的 `^\|\s*6\s` 换成 `^\|\s*99\s`，
        # 于是它再也打不中任何一行。**不改根目录那些文件**——沙箱只搬 `scripts/`，
        # 而方向五对「目标不在场」是**跳过**而不是报错。
        # 沙箱只搬 `scripts/`，**而方向五的目标是根目录那些文件**——
        # 没有它们，方向五会「一个都跳过」并安静地报绿（**那正是它要防的形态**）。
        # 所以这里显式补一份进来。
        for extra in ("AUDIT-RULES.md", "README.md", "PROGRESS.md", "AUDIT.md"):
            src_p = os.path.join(ROOT, extra)
            if os.path.isfile(src_p):
                shutil.copy(src_p, os.path.join(tmp, extra))
        fx = os.path.join(tmp, "scripts", "selftest-meta-fix-34-missing-selftest.py")
        t = read(fx)
        assert r"^\|\s*6\s" in t, "前提失配：fix-34 的锚点形态变了"
        with open(fx, "w", encoding="utf-8") as fh:
            fh.write(t.replace(r"^\|\s*6\s", r"^\|\s*99\s", 1))
        rc, out = run_in(tmp)
        record("12 夹具打不中锚点→必报", rc == 1 and "方向五" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 13 一个夹具都抽不出来 → 必须 rc=1（**「没检查」≠「全通过」**）──────
def m_no_fixture_triples():
    check_anchor()
    tmp = sandbox()
    try:
        for extra in ("AUDIT-RULES.md", "README.md", "PROGRESS.md", "AUDIT.md"):
            src_p = os.path.join(ROOT, extra)
            if os.path.isfile(src_p):
                shutil.copy(src_p, os.path.join(tmp, extra))
        sm = os.path.join(tmp, "scripts", "selftest-meta.sh")
        t = read(sm)
        assert "run_file_case" in t, "前提失配：脚本里没有 run_file_case"
        with open(sm, "w", encoding="utf-8") as fh:
            fh.write(t.replace("run_file_pass_case", "run_fpc")
                      .replace("run_file_case", "run_fc"))
        rc, out = run_in(tmp)
        record("13 抽不出夹具→必报", rc == 1 and "方向五" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 14 慢反验夹具处理不了目标 → 必报（方向五之二，**合成 ref 失败那一支**）──
def m_slow_fixture_crashes():
    check_anchor()
    assert "_unreachable_cases" in read(GATE), "前提失配：闸 18 里找不到方向五之二的解析器"
    tmp = sandbox()
    try:
        fx = os.path.join(tmp, "scripts", "selftest-fix-1-setsort.py")
        t = read(fx)
        with open(fx, "w", encoding="utf-8") as fh:
            fh.write("import sys\nraise SystemExit(3)\n" + t)
        rc, out = run_in(tmp)
        record("14 慢反验夹具跑不通→必报", rc == 1 and "方向五之二" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 15 夹具没注入特征 → 必报（方向五之二，**找不到修复特征那一支**）───────
def m_slow_feature_missing():
    check_anchor()
    tmp = sandbox()
    try:
        # **Batch 209 换了这份夹具**：原来写的是 `selftest-fix-2-import-entry.py`，
        # 而 Batch 207 把它连同它的用例一起删了——理由写着「它只被这一条用」，
        # **而这个理由从没被核过：本条用例也在用它**。
        # 于是从 Batch 207 起，本反验跑到这一例就 `FileNotFoundError`，
        # **整份报告一行都没交出来**（`main()` 只接 `AssertionError`）。
        # 闸 18 的方向十五就是为这件事建的。
        fx = os.path.join(tmp, "scripts", "selftest-fix-4-workspace-mode.py")
        # **锚点必须先 assert 钉死**：Batch 205 起的规矩——
        # 注入用的那份夹具不在场时，要报「前提失配」而不是崩在半路。
        assert os.path.isfile(fx), "前提失配：注入用的夹具 %s 不在场" % os.path.basename(fx)
        t = read(fx)
        i = t.index("sys.stdout.write")
        # 改成**恒等变换**：它跑得动，却什么也没注入。
        # **这一支与上一支是不同的形态**——只测「夹具会崩」的话，
        # 「夹具安静地什么都不做」照样能混过去。
        with open(fx, "w", encoding="utf-8") as fh:
            fh.write(t[:i] + "sys.stdout.write(text)\n")
        rc, out = run_in(tmp)
        record("15 慢反验夹具没注入特征→必报", rc == 1 and "方向五之二" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 16/17/18 构建出口（方向十三，Batch 204）──────────────────────────
# **方向十三问的是行为，不是写法**：闸失败时构建说不说话。
# 所以反验也不能去 grep「有没有 `|| rc=$?`」——那是在测写法。
# 这里把 `build-site.sh` 改回**那个会静默中止的写法**，方向十三必须报出来。
_OLD_RUN_GATE = 'out="$(python3 "scripts/$script" 2>&1)" || rc=$?\n'
_NEW_RUN_GATE = 'out="$(python3 "scripts/$script" 2>&1)"; rc=$?\n'


def m_run_gate_silent():
    check_anchor()
    tmp = sandbox()
    try:
        p = os.path.join(tmp, "build-site.sh")
        t = read(p)
        assert t.count(_OLD_RUN_GATE) == 1, "前提失配：build-site.sh 里那个 `|| rc=$?` 不见了"
        write(p, t.replace(_OLD_RUN_GATE, _NEW_RUN_GATE))
        rc, out = run_in(tmp)
        record("16 构建出口哑了→必报", rc == 1 and "方向十三" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def m_run_gate_reports():
    """**不误伤的那一半**：修 `run_gate` 时最容易顺手把成功路径也弄坏。"""
    check_anchor()
    tmp = sandbox()
    try:
        rc, out = run_in(tmp)
        record("17 出口能报（不误伤）→必须不报", rc == 0, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def m_run_gate_confuses_codes():
    """**第三个形态**：`未能核对` 被说成 `核对不一致`——Batch 160 专门立 rc=2 就是防这个。"""
    check_anchor()
    tmp = sandbox()
    try:
        p = os.path.join(tmp, "build-site.sh")
        t = read(p)
        old = '  if [ "$rc" -eq 2 ]; then\n'
        assert t.count(old) == 1, "前提失配：build-site.sh 里找不到 rc=2 分支"
        write(p, t.replace(old, "  if false; then\n"))
        rc, out = run_in(tmp)
        record("18 未能核对被说成不一致→必报",
               rc == 1 and "方向十三" in out and "未能核对" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 19/20 shell 变量展开（方向十四，Batch 205）──────────────────────
# **判据问的是「这份脚本会不会在某种 locale 下炸掉」，不是「写法好不好」**。
# 所以反验两支都做：把坏写法放进去必须报，把好写法放进去必须不报。
_BAD_LINE = '  echo "  ✓ $desc：这一行在 UTF-8 locale 下会炸"\n'
_GOOD_LINE = '  echo "  ✓ ${desc}：这一行任何 locale 下都安全"\n'


def m_shell_unsafe_var():
    check_anchor()
    tmp = sandbox()
    try:
        p = os.path.join(tmp, "scripts", "selftest-tables.sh")
        t = read(p)
        write(p, t + _BAD_LINE)
        rc, out = run_in(tmp)
        record("19 shell 里 `$var：` →必报", rc == 1 and "方向十四" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def m_shell_safe_var():
    """**不误伤那一半**：`${var}：` 紧跟中文全角标点是安全的，**不许报**。

    **这一支不是凑数**：判据如果分不清「`$var：` 坏」与「`${var}：` 好」，
    那它要么一直报红、要么只认写法——**两个都不叫判据**。
    """
    check_anchor()
    tmp = sandbox()
    try:
        p = os.path.join(tmp, "scripts", "selftest-tables.sh")
        t = read(p)
        write(p, t + _GOOD_LINE)
        rc, out = run_in(tmp)
        record("20 shell 里 `${var}：` →必须不报", rc == 0, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 21/22 悬空引用（方向十五，**Batch 209**）────────────────────────
# **沙箱必须自己是一个 git 检出**：方向十五问的是「这个文件**被删过**」，
# 而「被删过」这件事只有 git 知道。**不 init 的话它会走 [skip] 分支**，
# 而 [skip] 出来的 rc=0 与「核过且没问题」的 rc=0 **在退出码上分不开**——
# 所以用例必须**看得见它真的跑了**（见下面 22 的断言）。
def _git(tmp, *args):
    return subprocess.run(["git", "-C", tmp, *args], capture_output=True, text=True)


def _git_init(tmp):
    who = ["-c", "user.email=selftest@local", "-c", "user.name=selftest"]
    for argv in (("init", "-q"), ("add", "-A"),
                 (*who, "commit", "-qm", "base")):
        r = _git(tmp, *argv)
        assert r.returncode == 0, "前提失配：沙箱 git %s 失败：%s" % (
            argv[0], (r.stderr or "").strip()[:80])


def m_deleted_fixture_ref():
    check_anchor()
    tmp = sandbox()
    try:
        victim = "selftest-fix-1-setsort.py"
        path = os.path.join(tmp, "scripts", victim)
        assert os.path.isfile(path), "前提失配：待删的夹具不在场"
        _git_init(tmp)
        os.remove(path)
        _git(tmp, "add", "-A")
        _git(tmp, "-c", "user.email=selftest@local", "-c", "user.name=selftest",
             "commit", "-qm", "delete")
        rc, out = run_in(tmp)
        record("21 反验引用被删掉的夹具→必报",
               rc == 1 and "方向十五" in out and victim in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def m_live_fixture_ref_not_reported():
    check_anchor()
    tmp = sandbox()
    try:
        _git_init(tmp)
        rc, out = run_in(tmp)
        # **不误伤这一半必须同时证明「跑了」和「没报」**：
        # 只断言 rc == 0 的话，方向十五走 [skip] 分支也是 rc=0，
        # **那条路等于没测**。所以要看见它自己打出的「一个都没有」。
        record("22 反验引用的夹具都在场→不报",
               rc == 0 and "没有引用指向任何一个被删掉的同层文件" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 23/24 真跑反验（方向十六，**Batch 210**）────────────────────────
# **这两条各要 ~35 秒**（真跑 21 份反验），是这份反验里最贵的两条。
# **贵的理由要写出来**：它们换来的是「反验坏了会让构建变红」这件事有守卫，
# 而 **Batch 209 实测有两条用例作废了整整一个批次而闸 18 全绿**。
def m_broken_selftest_caught():
    check_anchor()
    victim = "selftest-endpoints.py"
    tmp = sandbox_full(break_selftest=victim)
    try:
        rc, out = run_in(tmp)
        record("23 反验真跑不过→必报",
               rc == 1 and "方向十六" in out and victim in out and "真跑没跑通" in out,
               f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def m_clean_fleet_not_reported():
    check_anchor()
    tmp = sandbox_full()
    try:
        rc, out = run_in(tmp)
        # **不误伤这一半必须同时证明「跑了」和「没报」**：
        # 只断言 rc == 0 的话，方向十六走 [skip] 分支（树不完整）也是 rc=0，
        # **那条路等于没测**。所以要看见它自己打出的那行汇总。
        n, bad = _fleet_in_sandbox(out)
        record("24 沙箱里跑不通的**只有**那 3 份环境缺口→不得有多余的",
               rc == 1 and n > 0 and bad == KNOWN_ENV_GAPS,
               f"rc={rc} 真跑={n} 跑不通={sorted(bad) or '无'}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 26/27 上游不可用 → 必须报「未能核对」（Batch 254）────────────────
#: **这一对是本批最该留下来的东西，因为它记的是一次「结论被自己的实验推翻」**。
#: 我先给闸 18 加判据、三次注入（删 `beefsrc.py` / 改坏它语法 /
#: 让 `resolve_src` 抛异常）**三次都是整个脚本崩掉加 Traceback**，
#: 于是判「这条降级路径在真树上不可达」并撤回了判据。
#: **那个结论是错的**：三次注入**全部打在「抛异常」那一支上**，
#: 而 `beefsrc.resolve_src()` **一个候选都不成立时是 `return (None, False)`——
#: 它不抛异常**，于是 `baseline.py` 第 66 行照样过、脚本活着走到那个 `try`、
#: `_up = None`、**全部 33 个用例被跳过**。
#: **所以下面两条里，「注入的形态」本身就是被验的东西。**

_NO_SUCH_REPO = "/tmp/beef-bootable-no-such-repo-b254"

#: **闸 18 那句 `全部跳过` 的固定措辞**——26 靠它认出闸真的走到了降级分支，
#: 而不是别的什么输出了 rc=2。**用措辞当断言，比用 rc 当断言强**：
#: rc=2 这道闸有别的来源（Batch 204 方向十三/四c 缺 `build-site.sh`），
#: **只断言 rc 会让这条用例在前提失配时也通过。**
_GAP_MARK = "一个候选都不成立时是"


#: **沙箱里必然跑不通的 3 份，及其原因**（Batch 254 实测）。
#:
#: **用例 24 原来断言「沙箱全绿」——而这个前提从来就不可能成立**：
#: `sandbox_full()` 有意排除 `.vitepress/`，它给副本树造的又是一次性的假 git 历史，
#: 于是实测是「真跑 32 份非慢反验，**29** 份 rc=0」：
#: `selftest-current-version.py` / `selftest-shot-version.py` 读不到
#: `.vitepress/config.mjs`；`selftest-shot-version-source.py` 要的那个锚点提交
#: 在假历史里根本不存在。
#:
#: **一份前提不可能成立的用例会一直红，而没人看见**——
#: `selftest-selftest-bootable.py` 不在构建路径上
#: （登记为 SLOW，且方向十六为防无限递归把自己从真跑名单里硬排除了）。
#: **修法不是把这三条从断言里放过去，而是把它们钉成「已知且仅此这三条」**——
#: **于是「沙箱里多了一份跑不通的」会立刻变红，「少了一份」也会。**
#: **这个集合会过期，而过期是好事**：哪天 `sandbox_full()` 补上 `.vitepress/`，
#: 这条用例会红并告诉人「该改期望值了」，**而不是让一个旧的期望继续成立**。
KNOWN_ENV_GAPS = {
    "selftest-current-version.py",
    "selftest-shot-version.py",
    "selftest-shot-version-source.py",
}


def _fleet_in_sandbox(out):
    """**返回 (真跑份数, 跑不通的名单)——两个数都不写死。**

    **写死数字的坏处已经实测过一次**：原用例 24 硬编码「真跑 21 份非慢反验，
    21 份 rc=0」，而队伍早长到 32 份。**而队伍规模不是这条用例该管的事**
    （同族：`SLOW.seconds`、对应关系表的「例数」——
    **一个从未被核对的数字，和一个核了但会过期的数字，是两个不同的问题**）。

    **反面教材就在本函数的第一版**：那个反向引用是穿过两层 Python 字符串写进来的，
    **`\\1` 被解成了 U+0001**——文件里躺着一个控制字符，正则永远匹配不上，
    **而 Python 照常编译通过、闸 20 也照常报绿**（它只查 U+FFFD 与 NUL）。
    **所以这一版是直接写在本文件里的，没有经过任何中间字符串层。**
    """
    m = re.search(r"真跑 (\d+) 份非慢反验，(\d+) 份 rc=0", out)
    n = int(m.group(1)) if m else 0
    bad = set(re.findall(r"反验 `([^`]+)` \*\*真跑没跑通\*\*", out))
    return n, bad


def run_in_env(tmp):
    """**清掉 `BEEFTV_SRC`** 再跑——它排在候选表第一位，
    开发者 shell 里设着它的话，注入会被它整个盖过去，
    **而那条用例会以「闸报了」的形态通过，而它其实什么都没验**（纪律 178）。"""
    #: **Batch 260 同一条**（`run_in` 那处的同族）：`baseline` 认那个变量，
    #: **而这里已经在建 env 了，顺手把它指回这棵树**——
    #: **两处只改一处，那一处仍然会读错树**（纪律 289 推论二）。
    e = child_env(tmp, BEEFTV_SRC='')
    r = subprocess.run([sys.executable, os.path.join(tmp, "scripts", "verify-selftest-bootable.py")],
                       cwd=tmp, capture_output=True, text=True, env=e)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _env_gap_tree(patch_it):
    """**同一棵树、同一个 harness，只改 `FALLBACK_ABS` 一个变量。**
    26 与 27 成对靠的就是这一点——**不误伤那一侧必须与能抓那一侧只差这一个变量**，
    否则它证明不了「26 是注入造成的」。"""
    tmp = sandbox_full()
    p = os.path.join(tmp, "scripts", "beefsrc.py")
    t = read(p)
    m = re.search(r'^FALLBACK_ABS\s*=\s*"([^"]+)"', t, re.M)
    assert m, "前提失配：beefsrc.py 里找不到 FALLBACK_ABS"
    if patch_it:
        assert m.group(1) != _NO_SUCH_REPO, "前提失配：兜底路径与注入目标相同，注入无效"
        t2 = t[:m.start(1)] + _NO_SUCH_REPO + t[m.end(1):]
        assert t2 != t, "注入未生效：FALLBACK_ABS 没被改"
        write(p, t2)
    return tmp


def _env_gap_holds(tmp):
    """**前提自检**：在副本树里 `resolve_src()` 必须真的返回 `(None, False)`。

    **不成立就让用例作废，不许硬跑出一个结论**（纪律 178）：
    27 那一侧要求它返回**非 None**——
    **如果这台机器上 `candidates()` 的兄弟路径恰好有 BeefTV，
    26 的注入会「什么都没改」而闸照样报 0/2**，
    **那时一个没验过任何东西的用例会打勾。**"""
    e = dict(os.environ)
    e["BEEFTV_SRC"] = ""
    r = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0, 'scripts'); import beefsrc; "
         "print(beefsrc.resolve_src()[0])"],
        cwd=tmp, capture_output=True, text=True, env=e)
    return r.stdout.strip(), (r.stderr or "")


def m_upstream_absent_reported():
    check_gap_anchor()
    tmp = _env_gap_tree(True)
    try:
        got, err = _env_gap_holds(tmp)
        assert got == "None", ("前提失配：副本树里 resolve_src() 返回 %r 而不是 None"
                               "——注入没生效（stderr: %s）" % (got, err.strip()[:60]))
        rc, out = run_in_env(tmp)
        record("25 上游不可用→必须报「全部跳过」且 rc=2",
               rc == 2 and _GAP_MARK in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 27 只有一个抄本 → 必报（**方向四e 第一支，Batch 275 新增**）───────
# ── 31 一份反验返回 2 → 必须报「未能核对」，不得说它坏了（方向十六第三类）──
def m_unverified_not_reported_as_broken():
    check_anchor()
    tmp = sandbox_full(break_selftest="selftest-endpoints.py", exit_code=2)
    try:
        rc, out = run_in(tmp)
        #: **两个断言缺一不可**：只核「报了未能核对」的话，
        #: 一个**把 rc=2 也塞进 `problems`** 的写法照样能通过（它会两条都印）；
        #: **而那正是本批要治的误诊**——它把「这一轮没法核它」说成「它坏了」。
        #: **断言必须指名到注入的那一份**——第一版写的是「输出里不许出现
        #: 「真跑没跑通」」，**而沙箱里有 3 份反验本来就必然跑不通**
        #: （`current-version` / `shot-version` / `shot-version-source`，
        #: 它们要上游的检出），**所以那一句会误伤**——
        #: **一道会误伤的断言会把人引去改判据，而它测的东西其实是对的**
        #: （Batch 249 ⑫ 的同一个形态）。
        record("31 反验 rc=2 → 报未能核对且不得说它坏了",
               "本轮未能核对（rc=2" in out
               and "反验 `selftest-endpoints.py` **真跑没跑通**" not in out
               and "selftest-endpoints.py" in out,
               f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _break_asset_library_h1(tmp):
    """让 `10-tasks/asset-library.md` 的**首行不再是 H1**。

    **形状照抄同事那处注入**（他在首行插了一句 HTML 注释，于是首行不再是 H1），
    **不是我们编的**——而这正是实测里让夹具 46/47 失配的那个形态。

    **⚠️ Batch 276 实测踩到：第一版写的是「去掉首行的 `# `」，
    **而那等于假设该页首行就是 H1**——
    **而那正是同事改掉的那一行，于是这条用例在真工作区上直接作废**。
    **同一个病第三次从同一个地方长出来：连新写的用例都在假设工作区是干净的。**
    **改法是「前置一行」而不是「改写首行」**：它对首行原本长什么样没有假设，
    **而实测两种写法都能让夹具失配**。
    """
    p = os.path.join(tmp, "10-tasks", "asset-library.md")
    s = read(p)
    before = s
    s = "<!-- Batch 276 注入：首行不是 H1，真 H1 在第 2 行 -->\n" + s
    assert s != before, "前提失配：注入没有改变文件"
    assert not s.split("\n", 1)[0].startswith("# "), "前提失配：注入后首行仍是 H1"
    write(p, s)
    return p


# ── 32 夹具失配 + 目标文件有未提交改动 → 前提不成立，不是夹具坏了（方向五）──
def m_fixture_stale_target_not_reported():
    check_anchor()
    tmp = sandbox_full()
    try:
        _break_asset_library_h1(tmp)          # 改完**不提交** → 那个文件是脏的
        rc, out = run_in(tmp)
        #: **判据落在「那条问题有没有出现」上，而不是落在 rc 上**——
        #: 沙箱里改了手册页，别的地方也可能红，**rc 不是这条性质的证据**。
        record("32 目标文件脏 → 夹具失配降级为「前提不成立」",
               "有未提交改动" in out and "已经打不中它的锚点" not in out,
               f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 33 夹具失配 + 目标文件干净 → 照旧报「夹具坏了」（**方向五的不误伤那一半**）──
def m_fixture_broken_clean_target_reported():
    check_anchor()
    tmp = sandbox_full()
    try:
        _break_asset_library_h1(tmp)
        #: **与用例 32 同一处注入，唯一的差别是把它提交掉**——
        #: 于是目标文件干净、夹具是真的坏了，**必须照旧报出来**。
        #: **没有这一条，「树脏了就全降级」也能让 32 变绿**，
        #: **而那种写法会把 23 个夹具的真失效一起盖住**。
        who = ["-c", "user.email=selftest@local", "-c", "user.name=selftest"]
        for argv in (("add", "-A"), (*who, "commit", "-qm", "h1 removed")):
            r = _git(tmp, *argv)
            assert r.returncode == 0, "前提失配：沙箱 git %s 失败" % argv[0]
        rc, out = run_in(tmp)
        record("33 目标文件干净 → 夹具失配必须照旧报出",
               rc == 1 and "已经打不中它的锚点" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def m_slow_cost_single_copy():
    check_anchor()
    tmp = sandbox()
    try:
        p = os.path.join(tmp, "scripts", "verify-selftest-bootable.py")
        t = read(p)
        #: **锚点必须选在改前改后都存在的那一行**——否则对照组里这条会「作废」
        #: （`assert k == 1` 失败）而不是「红」，**而作废的用例根本没验到目标性质**
        #: （Batch 272 记过：注入成功、结果很强、却没测到想测的东西）。
        #: meta.sh / unreachable.sh 的实测条目是本批新加的，**改前闸里没有**，
        #: 所以这里用改前就有的 quote-punct。
        new, k = re.subn(r'^\s*"selftest-quote-punct\.py":\s*37\.1,[^\n]*\n', "", t,
                         count=1, flags=re.M)
        assert k == 1, "注入未生效：没找到 quote-punct 的实测条目（k=%d）" % k
        assert '"selftest-quote-punct.py": 37.1' not in new, \
            "注入未生效：条目还在（正则吞掉了别的行）"
        write(p, new)
        rc, out = run_in(tmp)
        record("27 慢表只有一个抄本→必报", rc == 1 and "方向四e" in out
               and "只有一个抄本" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 28 两个抄本差得说不通 → 必报（方向四e 第二支）────────────────────
def m_slow_cost_ledger_disagrees():
    check_anchor()
    tmp = sandbox()
    try:
        p = os.path.join(tmp, "scripts", "verify-selftest-bootable.py")
        t = read(p)
        #: **Batch 275 订正注入方向（本条第一版测不到它想测的东西）**：
        #: 第一版把实测那一份改成 5 秒去拉大比值，**而 5 秒低于 30 秒阈值**，
        #: 于是判据在比值那一支之前就被「实测已掉到阈值之下」接管并 `continue`——
        #: **它报的压根不是比值那条**，而用例的输出与真失败**长得一样**。
        #: **这就是 Batch 249 ⑫ 记过的「用例测不到它想测的东西」。
        #: **④e-2 只在「实测仍高于阈值、但离声明值差 3 倍以上」时才可达**——
        #: 因为实测一旦 ≤ 30 就归 ④e-3。**所以要拉大比值，只能把声明值抬上去。**
        new, k = re.subn(r'"seconds": 38,', '"seconds": 400,', t, count=1)
        assert k == 1, "注入未生效：没找到 quote-punct 的 seconds（k=%d）" % k
        write(p, new)
        rc, out = run_in(tmp)
        #: **断言必须落在判据真说的那句上**（纪律：判据输出里出现了某个词，
        #: 不等于它判了这件事）。四e-2 那条报的是「**抄了两遍**」，不是「两个抄本」。
        record("28 两处登记差 10.8 倍→必报", rc == 1 and "方向四e" in out
               and "抄了两遍" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 29 实测那侧掉到阈值以下 → 必报（方向四e 第三支，**最要紧的一支**）──
def m_slow_but_measured_fast():
    check_anchor()
    tmp = sandbox()
    try:
        p = os.path.join(tmp, "scripts", "verify-selftest-bootable.py")
        t = read(p)
        #: **这条治的正是本批的起因**：SLOW 说它慢，而实测说它不慢。
        #: **而方向四a 看不见这一支**——它读的是 `seconds`（38 > 30，报绿）。
        new, k = re.subn(r'"selftest-quote-punct\.py": 37\.1,',
                         '"selftest-quote-punct.py": 20.0,', t, count=1)
        assert k == 1, "注入未生效：没找到 quote-punct 的实测条目（k=%d）" % k
        write(p, new)
        rc, out = run_in(tmp)
        record("29 慢表说慢而实测不慢→必报", rc == 1 and "方向四e" in out
               and "已在阈值之下" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 30 留余量是合法的（**方向四e 的不误伤那一半**）──────────────────
def m_slow_cost_margin_allowed():
    check_anchor()
    tmp = sandbox()
    try:
        p = os.path.join(tmp, "scripts", "verify-selftest-bootable.py")
        t = read(p)
        #: 把 `seconds` 从 38 抬到 80（实测仍 37.1）→ **比值 2.16 倍，仍在 3 倍之内**。
        #: **「预算上限刻意偏大」是这张表写明的用法**（纪律 204：漂的时候倒向安全那侧），
        #: **而一道会误报的守卫比没有守卫更坏**——它会让人去把合法的余量改小，
        #: **于是下一次漂就没有余量了。**
        new, k = re.subn(r'"seconds": 38,', '"seconds": 80,', t, count=1)
        assert k == 1, "注入未生效：没找到 quote-punct 的 seconds（k=%d）" % k
        write(p, new)
        rc, out = run_in(tmp)
        record("30 差 2.16 倍是合法余量→不许报", rc == 0 and "方向四e" not in out,
               f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def m_upstream_present_not_reported():
    check_gap_anchor()
    tmp = _env_gap_tree(False)
    try:
        got, err = _env_gap_holds(tmp)
        assert got != "None", ("前提失配：没注入却已经取不到上游（%r）——"
                               "这台的候选表与判据假设不符，用例作废而不是硬跑" % got)
        rc, out = run_in_env(tmp)
        # **不误伤这一半同时要证明「跑了」和「没报」**（同用例 24 的理由）：
        # 只断言 `_GAP_MARK not in out` 的话，闸在 [skip] 分支上也「没报」。
        n, bad = _fleet_in_sandbox(out)
        record("26 上游在场→跑不通的仍**只有**那 3 份，且不得出现「全部跳过」",
               rc == 1 and n > 0 and bad == KNOWN_ENV_GAPS and _GAP_MARK not in out,
               f"rc={rc} 真跑={n} 跑不通={sorted(bad) or '无'}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── Batch 278：方向四f（`cost_split`）的四例 ──────────────────────────────
#: **注入形态为什么是「SLOW 字面量之后的一条赋值」而不是「往条目里追加一个键」**：
#: 见本文件顶部那段说明——**追加会被同名键的「后者覆盖前者」顶掉**，
#: **而那个失败长得像「判据没生效」**。**赋值在执行顺序上永远晚于字面量，与键的先后无关。**
_INJ_ANCHOR = r'^(# \*\*实测耗时登记表\*\*（Batch 180 新增）。单位：秒，单次实测（含进程启动）。)$'


def _inject_cost_split(t, statement):
    """在 SLOW 字面量之后插一条赋值，**并 assert 钉死它真的落上了**。

    **为什么用回调而不是替换串**：`re.sub` 的替换串会解释 `\n` 等转义，
    而这里替换串里全是反斜杠——**用回调就没有第二次解释**（Batch 291 家族）。
    """
    new, k = re.subn(
        _INJ_ANCHOR,
        lambda m: statement + "\n" + m.group(1),
        t, count=1, flags=re.M)
    assert k == 1, "注入未生效：没找到实测耗时登记表那行注释（k=%d）" % k
    assert statement in new, "注入未生效：插进去的那一行不在改后的源码里"
    return new


def m_cost_split_anchor_absent():
    """能抓①：`cost_split` 的锚点指向一段**源文件里没有的**步骤 → 必须报。

    **为什么这一支最要紧**：成本归属指向一个不存在的步骤，
    **等于这个数字没有归属**——而下一个人读到它只会以为「已经量过了」。
    """
    check_anchor()
    tmp = sandbox()
    try:
        p = os.path.join(tmp, "scripts", "verify-selftest-bootable.py")
        new = _inject_cost_split(
            read(p),
            'SLOW["selftest-quote-punct.py"]["cost_split"] = '
            '{"def 这一段根本不存在()": 38.0}  # Batch 278 用例 34 注入')
        write(p, new)
        rc, out = run_in(tmp)
        record("34 `cost_split` 锚点不在场→必报",
               rc == 1 and "方向四f" in out and "没有这一段" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def m_cost_split_sum_off():
    """能抓②：段和与 `seconds` 差 1316 倍 → 必须报。

    **锚点这一支刻意用**存在**的步骤名**（`def run(env=None):` 真在 quote-punct 里），
    **这样报的只可能是段和那一支**——两支混在一起时用例就测不准自己想测的东西
    （Batch 275 的用例 28 记过：注入方向选错，判据在另一支先 `continue`，
    **而输出与真失败长得一样**）。
    """
    check_anchor()
    tmp = sandbox()
    try:
        p = os.path.join(tmp, "scripts", "verify-selftest-bootable.py")
        new = _inject_cost_split(
            read(p),
            'SLOW["selftest-quote-punct.py"]["cost_split"] = '
            '{"def run(env=none)": 50000.0}  # Batch 278 用例 35 注入')
        write(p, new)
        rc, out = run_in(tmp)
        record("35 段和与 `seconds` 差 1316 倍→必报",
               rc == 1 and "方向四f" in out and "段和" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def m_cost_split_absent():
    """能抓③：某条 SLOW **没有** `cost_split` → 必须报。

    **空字典 `{}` 与「键根本不在」在判据里是同一件事**（`if not _split`），
    **而实测那个键在不在场是读源码——用空字典注入就不用去碰那条源码**，
    **于是这一支只测判据，不掺任何别的东西**。
    """
    check_anchor()
    tmp = sandbox()
    try:
        p = os.path.join(tmp, "scripts", "verify-selftest-bootable.py")
        new = _inject_cost_split(
            read(p),
            'SLOW["selftest-quote-punct.py"]["cost_split"] = {}  # Batch 278 用例 36 注入')
        write(p, new)
        rc, out = run_in(tmp)
        record("36 某条 SLOW 没有 `cost_split`→必报",
               rc == 1 and "方向四f" in out and "没有 `cost_split`" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def m_cost_split_clean_not_reported():
    """**不误伤**：五条登记全部合规时，一条都不许报。

    **这一例与前三例同样重要**：④f 是本批新增的判据，
    **而一个永远会报的判据比没有判据更坏**——它会让人学会忽略它
    （本项目的保守侧是「照报」，**但照报的前提是报的东西真的不对**）。

    **⚠️ 前提断言为什么不用「树上有 5 条 `cost_split`」**（本批真踩）：
    第一版数的是闸源码里 `"cost_split": {` 的出现次数，**而在改前闸上那是 0 条**
    ——于是本例在对照组里**「作废」而不是「绿」**（Batch 277 踩过：前提失配的用例
    根本没验到目标性质，而它自己看起来像一条正常的红）。
    **改成核闸自己的输出**：「慢反验 5 份已登记」那一句由方向五产出，
    **改前改后逐字相同**，而它成立就说明 `SLOW` 非空、④f 的循环至少走过 5 次
    ——**这正是「④f 真的跑了」的可观测证据**（纪律 300 推论四：
    一个因为数据源空掉而永远沉默的判据，同样会 rc=0）。
    """
    check_anchor()
    tmp = sandbox()
    try:
        rc, out = run_in(tmp)
        assert "慢反验 5 份已登记" in out, (
            "前提失配：闸没走到 SLOW 那一段，④f 根本没被执行——"
            "**本例会因为「它没跑」而假绿**")
        n_slow = read(os.path.join(tmp, "scripts", "verify-selftest-bootable.py")
                      ).count('"cost_split": {')
        record("37 五条登记全合规→一条都不许报",
               rc == 0 and "方向四f" not in out,
               f"rc={rc} 闸内 {n_slow} 条 cost_split")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 38–40 构建墙钟的机制链（**Batch 280，方向四g**）────────────────────
#
# **三条用例的注入锚点是本批才出现的，所以它们刻意不 `assert` 锚点**——
# **而这不是偷懒，理由是鉴别力验证实测出来的**：
# 锚点在改前闸那棵树上**根本不存在**，而 `assert` 落空会让用例记成**「作废」**
# （Batch 277/278 各踩过一次）。**作废的含义是「前提不成立、这条什么都没验」**，
# 于是在对照组里它看起来像一条正常的红，**而实际上它连自己测的是什么都没说**。
# **所以改成钉判据的输出**：`传给记录脚本` / ``交给 `write_record``` 这两个词
# **只在对应那一环真的断了时才会出现在报告里**——
# **于是「注入静默没生效」会让用例变红，而不是让它假绿**（纪律 107）。
# **而改前闸没有方向四g，输出里根本没有这两个词，于是三条在对照组里是红而不是作废**，
# **这正是新方向应有的鉴别力形态**。
def m_build_secs_flag_removed():
    """能抓①：`build-site.sh` 不把墙钟传给记录脚本 → 必报。

    **注入形态刻意选 `--secs` → `--secz` 而不是整行删掉**：
    删行会让 shell 的续行结构变样，而**判据读的是 `re.sub` 压平之后的文本**，
    **形状一变它就可能因为「续行没了」而报另一个错**——
    **那样这条用例验的就不是「传参」而是「续行」了**。
    改一个字母则保留全部结构，只让那个接点真的断掉。
    """
    check_anchor()
    tmp = sandbox()
    try:
        p = os.path.join(tmp, "build-site.sh")
        t = read(p)
        new = t.replace('--secs "${BEEF_SECS}"', '--secz "${BEEF_SECS}"', 1)
        applied = new != t
        write(p, new)
        rc, out = run_in(tmp)
        record("38 墙钟没传给记录脚本→必报",
               rc == 1 and "方向四g" in out and "传给记录脚本" in out,
               "rc=%d 注入%s生效" % (rc, "" if applied else "**没**"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def m_build_secs_not_forwarded():
    """能抓②：记录脚本收了 `--secs` 却没交给 `write_record` → 必报。

    **这一环最容易被漏**：参数声明在、值也拿到了，
    **而少写一个实参时 argparse 与 Python 都不报错**——
    **`write_record` 的 `secs` 默认 `None`，于是它照常写下一个空的 `secs=`**
    （Batch 280 给 `write_record` 的注释里就写着这个形态）。
    **而一个空值读起来像真值**——**这就是这一环必须单独有判据的原因**。
    """
    check_anchor()
    tmp = sandbox()
    try:
        p = os.path.join(tmp, "scripts", "record-build-result.py")
        t = read(p)
        new = t.replace(
            "buildrecord.write_record(batch, n_ok, n_warn, n_fail, a.counts, a.secs)",
            "buildrecord.write_record(batch, n_ok, n_warn, n_fail, a.counts)", 1)
        applied = new != t
        write(p, new)
        rc, out = run_in(tmp)
        record("39 记录脚本没把 `a.secs` 交给 `write_record`→必报",
               rc == 1 and "方向四g" in out and "交给 `write_record`" in out,
               "rc=%d 注入%s生效" % (rc, "" if applied else "**没**"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def m_build_secs_mechanism_clean():
    """**不误伤**：七个接点全在时，方向四g 一条都不许报。

    **和 Batch 279 那条一样重要**：④g 是本批新增的方向，
    **而一个永远会报的判据比没有判据更坏**——它会让人学会忽略它。

    **⚠️ 这里刻意不 `assert`「④g 的绿行出现了」**——
    **那行只在新闸里有，于是本例在对照组上会「作废」而不是「绿」**（Batch 278 踩过）。
    **改成两段式**：**断言只问「没报」**（改前改后都成立），
    **而「④g 到底跑没跑」放进 detail 里**——
    **于是对照组上它是绿（那正是它该有的样子：不误伤），
    而实验组那一行 detail 会明写「绿行在场」**，
    **读的人不必再猜这一条是「验过了」还是「压根没执行」**。
    **前提断言核的是方向五那句「慢反验 5 份已登记」——改前改后逐字相同**，
    **它成立就说明闸至少走到了它有数据的那一段**。

    **⚠️ 而「没报」这一条第一版就写错了（本批真踩）**：
    我写的是 `rc == 0 and "方向四g" not in out`——
    **而方向四g 在一切正常时会打印一行绿行**（含上一次绿构建记录的 `secs=`），
    **所以那个条件永远为假，本例从第一版起就不可能通过**。
    **这与 Batch 279 那两条红是同一个病：断言没落在判据真说的那句上**——
    **方向四f 通过时一声不吭，方向四g 通过时会说话**，
    **而我把两者当成了同一种形状。**
    **改成核「报问题的那两句」在不在**（`这条链上断了` / `方向四g：读不到`），
    **它们只在判据真的报问题时才出现**——
    **而绿行照旧打进 detail，所以「④g 跑没跑」这件事仍然看得见。**
    """
    check_anchor()
    tmp = sandbox()
    try:
        rc, out = run_in(tmp)
        assert "慢反验 5 份已登记" in out, (
            "前提失配：闸没走到 SLOW 那一段——**本例会因为「它没跑」而假绿**")
        _bad = [w for w in ("这条链上断了", "方向四g：读不到") if w in out]
        record("40 墙钟机制七环都在→一条都不许报",
               rc == 0 and not _bad,
               "rc=%d ④g 绿行%s在场%s"
               % (rc, "" if "方向四g：" in out else "**不**",
                  ("　报了 %s" % _bad) if _bad else ""))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 41–43 构建墙钟之外的另一半：反验不许写真册树（**Batch 281，方向十九**）────
#
# **为什么这两条「能抓 / 不误伤」只要 2 秒而不是 155 秒**：
# 方向十九长在方向十六的真跑循环里，**而方向十六一跑就是 39 份、151 秒**。
# **照默认配置跑一遍当然最真，可是一条用例 151 秒意味着这份反验多出 5 分钟**——
# **判据的代价必须先量**（Batch 278 那条 `cost_split` 就是这么来的）。
# **做法：把注入闸的 `names` 缩成一份**（`names = ["selftest-batch-rows.py"]`）。
# **这不会让方向十九失效**——**它问的是「这一份动没动手册树」，
# 而一份就够回答**；**而方向十六的其余 38 份由另外那些用例与每次真构建覆盖**。
# **⚠️ 这条缩窄必须写在这里**：**它意味着本对用例验的是方向十九的报告逻辑，
# 不是「39 份一起跑时它还成立」**——后者由每次真构建守着。
_ONE = "selftest-batch-rows.py"
_FLEET_ANCHOR = "    names = selftests()"


def _pin_fleet(t):
    """把注入闸的真跑名单缩成一份。**锚点必须在改前改后都在**——
    `names = selftests()` 这行从 Batch 179 就在，与本批无关。"""
    assert _FLEET_ANCHOR in t, "前提失配：闸里找不到 `%s`" % _FLEET_ANCHOR.strip()
    return t.replace(_FLEET_ANCHOR,
                     '    names = ["%s"]  # Batch 281 用例 41/42 注入' % _ONE, 1)


def m_tree_write_reported():
    """能抓①：一份**没登记豁免**的反验改了手册树 → 方向十九必须点名它。

    **注入是「把豁免表里那一条删掉」**，而不是「造一份会写树的反验」——
    **因为真有一份会写树的**：`selftest-batch-rows.py` 实测改写 `PROGRESS.md`
    （Batch 281 普查，`73 份里 26 份`）。
    **用现成的那一份而不是新造一份**：新造的反验要多写一个文件、多注册一行映射，
    **而它验的性质与现成那份完全一样**。
    """
    check_anchor()
    tmp = sandbox_full()
    try:
        p = os.path.join(tmp, "scripts", "verify-selftest-bootable.py")
        t = _pin_fleet(read(p))
        new, k = re.subn(r'^    "%s": .*\n' % re.escape(_ONE), "", t, count=1, flags=re.M)
        assert k == 1, "注入未生效：豁免表里没有 `%s` 那一行（k=%d）" % (_ONE, k)
        write(p, new)
        rc, out = run_in_env(tmp)
        record("41 改了手册树又没登记豁免→必报",
               rc == 1 and "方向十九" in out and "真跑期间改动了手册树里的文件" in out
               and _ONE in out,
               "rc=%d" % rc)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def m_tree_write_exempt_not_reported():
    """**不误伤**：同一份反验、同样改了手册树，**但它登记在豁免表里** → 一条都不许报。

    **与 Batch 280 用例 40 同一个坑的另一个版本**：上一批踩的是
    「断言写了 `方向四g` 不许出现在输出里，而闸正常时会打印方向四g 的绿行」。
    **本例的对应形态是**：方向十九**无论报不报都会打一行汇总**，
    **所以断言必须问「报问题的那句在不在」，不能问「方向十九在不在」**。
    **而两者只差几个字，差的是这句话会不会被写错方向。**

    **⚠️ `rc=1` 在本例是预期的，不是缺陷**：注入把 `names` 缩成一份之后，
    方向十一 / 方向十七那些按名单逐条核的方向必然对不上而报错。
    **所以本例断言的是「方向十九那句在不在」，而不是 `rc == 0`**——
    **在别的方向因为注入而报错的场合要求 rc=0，等于要求注入不生效**
    （而它恰恰要生效）。
    """
    check_anchor()
    tmp = sandbox_full()
    try:
        p = os.path.join(tmp, "scripts", "verify-selftest-bootable.py")
        write(p, _pin_fleet(read(p)))
        rc, out = run_in_env(tmp)
        #: **这里刻意不 `assert`「方向十九跑过了」**（与 Batch 280 用例 40 同一条纪律）：
        #: **改前闸根本没有这个方向**，而 assert 落空会把本例在对照组上记成**「作废」**——
        #: **而「作废」的意思是「前提不成立、这条什么都没验」**。
        #: **可这里前提是成立的**：**判据不存在时它当然不会误报，那正是不误伤**。
        #: **所以断言只问「报问题的那句在不在」**（改前改后都成立），
        #: **而「方向十九到底跑没跑」放进 detail**——
        #: **于是读的人不必猜这一条是「验过了」还是「压根没执行」**。
        #: **detail 原来写的是 `_ONE in out`，而汇总行只报两个数、不列名字**——
        #: **于是它在「豁免表里有它」的时候也打印「豁免表里没有它」**，
        #: **一行 detail 说了假话，而它就印在那条通过的用例后面**。
        #: **改成直接读注入闸的源码**：这句话要说的就是表里有没有那一条。
        in_table = ('"%s"' % _ONE) in read(p)
        record("42 改了手册树但已登记豁免→一条都不许报",
               "真跑期间改动了手册树里的文件" not in out,
               "rc=%d 豁免表里%s它；方向十九%s执行"
               % (rc, "有" if in_table else "**没有**",
                  "" if "方向十九：" in out else "**没**"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def m_exempt_reasons_not_empty():
    """豁免表里每一条都要有理由，**一条空的都不许**。

    **这一条不跑闸**（它只读闸的源码），**所以它几乎不要钱**，
    **而它守着的是这张表唯一的刹车**：
    **一张只列名字的豁免表，下一个人只会照着它继续加**
    ——**而「为什么这份必须写真册树」正是该不该加它的唯一依据**（纪律 305）。
    """
    check_anchor()
    t = read(GATE)
    m = re.search(r"TREE_WRITE_EXEMPT = \{", t)
    if not m:
        #: **改前闸没有这张表，而本例第一版会把它记成「作废」**——
        #: **而「空集合上每一条都有理由」是恒真的**，0 条就是 0 条空理由。
        #: **如实报成「本轮 0 条」而不是「前提失配」**：
        #: **「作废」的意思是「前提不成立、这条什么都没验」，
        #: 而这里前提是成立的——它就是一张空表**（这一条是对照组能读懂本批的地方）。
        record("43 豁免表 0 条（改前闸没有这张表）", True, "表不存在，空集合恒真")
        return
    body = t[m.end():]
    body = body[:body.index("\n}")]
    empty = re.findall(r'^    "[^"]+":\s*",?\s*$', body, re.M)
    n = len(re.findall(r'^    "[^"]+":', body, re.M))
    record("43 豁免表 %d 条每条都有理由" % n,
           n > 0 and not empty,
           "空理由 %d 条" % len(empty))


def check_own_ledger_row():
    """本反验**自己核自己那一行**的「例数」——因为方向十七够不到它。

    **为什么够不到**：方向十六为了防无限递归，把本文件从真跑名单里硬排除了。
    **而这一行恰恰是全表最容易过期的**：20 → 22 → 24，**两个批次各动一次**。
    **放在用例列表外面**是有意的——它是**收尾自检**，不占用用例名额，
    **否则就会变成「例数包含它自己」的自指**。
    """
    path = os.path.join(ROOT, "AUDIT-RULES.md")
    t = read(path)
    m = re.search(r"###\s*闸\s*→\s*反验的对应关系[^\n]*\n(.*?)(?=\n###|\n##\s)", t, re.S)
    assert m, "前提失配：找不到「闸 → 反验的对应关系」小节"
    me = os.path.basename(__file__)
    for line in m.group(1).split("\n"):
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) >= 3 and c[1].strip("`") == me:
            assert c[2].isdigit(), "前提失配：表里本反验那行的例数不是整数 [%s]" % c[2]
            assert int(c[2]) == len(results), (
                "对应关系表登记 %s 例，而本轮真跑 %d 例" % (c[2], len(results)))
            return True
    raise AssertionError("对应关系表里没有认领 %s 的那一行" % me)


def main():
    tests = [m_clean, m_broken_selftest_syntax, m_broken_fixture_syntax,
             m_broken_shell, m_missing_local_module, m_fixture_not_treated_as_selftest,
             m_real_selftest_detected, m_slow_entry_under_budget, m_slow_not_registered,
             m_never_measured, m_comment_is_not_invocation,
             m_fixture_anchor_missed, m_no_fixture_triples,
             m_slow_fixture_crashes, m_slow_feature_missing,
             m_run_gate_silent, m_run_gate_reports, m_run_gate_confuses_codes,
             m_shell_unsafe_var, m_shell_safe_var,
             m_deleted_fixture_ref, m_live_fixture_ref_not_reported,
             m_broken_selftest_caught, m_clean_fleet_not_reported,
             m_upstream_absent_reported, m_upstream_present_not_reported,
             m_unverified_not_reported_as_broken,
             m_fixture_stale_target_not_reported,
             m_fixture_broken_clean_target_reported,
             m_slow_cost_single_copy, m_slow_cost_ledger_disagrees,
             m_slow_but_measured_fast, m_slow_cost_margin_allowed,
             m_cost_split_anchor_absent, m_cost_split_sum_off,
             m_cost_split_absent, m_cost_split_clean_not_reported,
             m_build_secs_flag_removed, m_build_secs_not_forwarded,
             m_build_secs_mechanism_clean,
             m_tree_write_reported, m_tree_write_exempt_not_reported,
             m_exempt_reasons_not_empty]
    for t in tests:
        try:
            t()
        except AssertionError as exc:
            record(t.__name__, "作废", f"前提失配：{exc}")
        except Exception as exc:  # noqa: BLE001
            # **Batch 209 加的。原来只接 `AssertionError`——**
            # **而实测那次事故是 `FileNotFoundError`**：它一路抛到解释器顶端，
            # 于是**已经跑完的 19 例结果一行都没打印**，整份报告只剩一行 Traceback。
            # **「20 例全过」与「一份报告都没交出来」在退出码上都是非 0，肉眼分不开。**
            # 记成「失败」而不是「作废」：**用例自己崩了是它自己的问题，
            # 而「作废」的含义是「前提不成立、这条什么都没验」**——两者混起来，
            # 下一个人会以为只是锚点过期，去改夹具，而真正的问题在反验本体。
            record(t.__name__, "失败",
                   f"用例自身抛异常：{type(exc).__name__}: {exc}")
    failed = 0
    for name, status, detail in results:
        mark = {"通过": "✓", "失败": "✗", "作废": "—"}[status]
        print(f"  {mark} {name}  {detail}")
        if status != "通过":
            failed += 1
    print(f"闸 18 反验：{len(results)} 例，通过 {len(results) - failed}，失败/作废 {failed}")
    # 收尾自检（**不占用例名额**，理由见 check_own_ledger_row 的注释）
    try:
        check_own_ledger_row()
        print("  ✓ 本反验自己那一行的「例数」与本轮真跑数一致")
    except AssertionError as exc:
        failed += 1
        print(f"  ✗ {exc}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
