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


def check_anchor():
    t = read(GATE)
    assert "FIXTURE_RE" in t, "前提失配：闸 18 里找不到夹具分类判据"
    assert "SLOW = {" in t, "前提失配：闸 18 里找不到慢反验登记表"
    assert "SELFTEST_COSTS = {" in t, "前提失配：闸 18 里找不到实测耗时表"
    assert "_build_invokes" in t, "前提失配：闸 18 里找不到「只认代码不认注释」的判据"


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
        new = t.replace('"selftest-shot-version.py": 2.0,',
                        '"selftest-shot-version.py": 999,', 1)
        assert new != t, "注入未生效：耗时没被改成 999"
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
        new = t.replace('"selftest-shot-version.py": 2.0,', '', 1)
        assert new != t, "注入未生效：耗时条目没被删"
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
        fx = os.path.join(tmp, "scripts", "selftest-fix-2-import-entry.py")
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


def main():
    tests = [m_clean, m_broken_selftest_syntax, m_broken_fixture_syntax,
             m_broken_shell, m_missing_local_module, m_fixture_not_treated_as_selftest,
             m_real_selftest_detected, m_slow_entry_under_budget, m_slow_not_registered,
             m_never_measured, m_comment_is_not_invocation,
             m_fixture_anchor_missed, m_no_fixture_triples,
             m_slow_fixture_crashes, m_slow_feature_missing,
             m_run_gate_silent, m_run_gate_reports, m_run_gate_confuses_codes,
             m_shell_unsafe_var, m_shell_safe_var]
    for t in tests:
        try:
            t()
        except AssertionError as exc:
            record(t.__name__, "作废", f"前提失配：{exc}")
    failed = 0
    for name, status, detail in results:
        mark = {"通过": "✓", "失败": "✗", "作废": "—"}[status]
        print(f"  {mark} {name}  {detail}")
        if status != "通过":
            failed += 1
    print(f"闸 18 反验：{len(results)} 例，通过 {len(results) - failed}，失败/作废 {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
