#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 18「反验启动核对」的反向验证（Batch 179）。

用例清单：
  1  现状全绿                              → 不报
  2  反验语法坏掉                          → 必报（方向一，**它连启动都做不到**）
  3  注入夹具语法坏掉                      → 必报（方向一；夹具坏了，调用它的用例会作废）
  4  shell 反验语法坏掉                    → 必报（方向一，`bash -n`）
  5  反验 import 一个不存在的本地模块      → 必报（方向二）
  6  **注入夹具不得被当成反验**            → 必须不报（**上线首跑就误报过 58 处**）
  7  真实现状                              → 不报

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
    results.append((name, "通过" if ok else "失败", detail))


def sandbox():
    tmp = tempfile.mkdtemp(prefix="beef-bootable-selftest.")
    shutil.copytree(SCRIPTS, os.path.join(tmp, "scripts"))
    shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-selftest-bootable.py"))
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
        m = re.search(r"^from baseline import[^\n]*$", t, re.M)
        assert m, "前提失配：verify-feature-flags.py 里找不到真实的 `from baseline import` 行"
        write(p, t[:m.start()] + "from nosuchmodule import resolve_ref" + t[m.end():])
        after = read(p)
        assert "from nosuchmodule import" in after, "注入未生效：真实 import 行没被改"
        assert re.search(r"^from baseline import", after, re.M) is None, \
            "注入未生效：baseline 的 import 还在"
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


def main():
    tests = [m_clean, m_broken_selftest_syntax, m_broken_fixture_syntax,
             m_broken_shell, m_missing_local_module, m_fixture_not_treated_as_selftest,
             m_real_selftest_detected, m_slow_entry_under_budget, m_slow_not_registered,
             m_never_measured, m_comment_is_not_invocation]
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
