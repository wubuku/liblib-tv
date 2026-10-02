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
    r = subprocess.run([sys.executable, os.path.join(tmp, "scripts", "verify-selftest-bootable.py")],
                       cwd=tmp, capture_output=True, text=True)
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


def sandbox_full(break_selftest=None):
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
        write(p, t[:i] + "\nraise SystemExit(1)  # Batch 210 用例 23 注入\n" + t[i:])
    return tmp


def check_anchor():
    t = read(GATE)
    assert "FIXTURE_RE" in t, "前提失配：闸 18 里找不到夹具分类判据"
    assert "SLOW = {" in t, "前提失配：闸 18 里找不到慢反验登记表"
    assert "SELFTEST_COSTS = {" in t, "前提失配：闸 18 里找不到实测耗时表"
    assert "_build_invokes" in t, "前提失配：闸 18 里找不到「只认代码不认注释」的判据"
    assert "_deleted_sibling_names" in t, "前提失配：闸 18 里找不到方向十五「被删掉的引用」判据"
    assert "方向十六" in t, "前提失配：闸 18 里找不到方向十六「真跑反验」判据"


# ── 1 现状 ──────────────────────────────────────────────────────────
def m_clean():
    check_anchor()
    r = subprocess.run([sys.executable, GATE], cwd=ROOT, capture_output=True, text=True)
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
        new = t.replace('"seconds": 97,', '"seconds": 3,', 1)
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
        new, k = re.subn(r"^\s*" + re.escape(COST_KEY) + r"[^\n]*\n", "", t, count=1,
                         flags=re.M)
        assert k == 1, "注入未生效：耗时条目 %s 没删掉（k=%d）" % (COST_KEY, k)
        write(p, new)
        rc, out = run_in(tmp)
        record("10 缺实测耗时→必报", rc == 1 and "没有它的实测耗时" in out, f"rc={rc}")
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
        record("24 21 份反验真跑全绿→不报",
               rc == 0 and "真跑 21 份非慢反验，21 份 rc=0" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


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
             m_broken_selftest_caught, m_clean_fleet_not_reported]
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
