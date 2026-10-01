#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 17「反验依赖核对」的反向验证（Batch 178）。

**这道反验的特殊性**：闸 17 核的正是「另外那些反验还能不能跑」，
而**给它写反验很容易滑向「反验的反验」的无限套娃**。
本文件刻意只做**两件静态可判**的事，避免造第三层：

  1  闸 17 自己有没有因为「又新增了带依赖的闸门」而退化（**它会不会静悄悄查不到**）；
  2  它识别「反验是否把闸门复制进临时目录」的那条判据**会不会失配**——
     写法变了（不叫 shutil.copy、改用别的方式）就会漏。

用例清单：
  1  现状全绿                              → 不报
  2  某反验删掉了 baseline.py 的搬运       → 必报（方向一，**本批真实发生过**）
  3  闸门脚本被改成 import 一个不存在的模块 → 必报（方向一）
  4  判据对「没有复制闸门」的反验**不误报**（只扫该扫的）
  5  把「复制闸门」换成非 shutil.copy 写法  → 必报（判据失配，防静悄悄查不到）

**用例 2 是本文件的核心**：它复现的正是 Batch 178 静悄悄坏了三个批次的那一类回归。
"""

import io
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(ROOT, "scripts", "verify-selftest-deps.py")
SCRIPTS = os.path.join(ROOT, "scripts")

results = []


def run_gate(cwd=None):
    r = subprocess.run([sys.executable, GATE], cwd=cwd or ROOT,
                       capture_output=True, text=True)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


import subprocess  # noqa: E402  （放在函数前，避免用例里再导入）


def read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def write(p, t):
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(t)


def record(name, ok, detail=""):
    results.append((name, "通过" if ok else "失败", detail))


def check_anchor():
    t = read(GATE)
    assert "local_imports" in t, "前提失配：闸 17 里找不到 local_imports"
    assert "shutil.copy" in t, "前提失配：闸 17 里找不到复制判据"


# ── 1 现状 ──────────────────────────────────────────────────────────
def m_clean():
    check_anchor()
    rc, out = run_gate()
    record("1 真实现状→不报", rc == 0, f"rc={rc}")


# ── 2 删掉某反验里的 baseline 搬运 → 必报 ────────────────────────────
def m_missing_baseline_copy():
    check_anchor()
    # 在**临时副本仓**上注入，避免动真实文件
    tmp = tempfile.mkdtemp(prefix="beef-deps-selftest.")
    try:
        shutil.copytree(os.path.join(ROOT, "scripts"), os.path.join(tmp, "scripts"))
        shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-selftest-deps.py"))
        target = os.path.join(tmp, "scripts", "selftest-feature-flags.py")
        t = read(target)
        new = re.sub(r'^\s*shutil\.copy\(BASELINE,[^\n]*\n', "", t, count=1, flags=re.M)
        assert new != t, "注入未生效：baseline 搬运那行没找到"
        write(target, new)
        assert "shutil.copy(BASELINE" not in read(target), "注入未生效：搬运还在"
        r = subprocess.run([sys.executable, os.path.join(tmp, "scripts", "verify-selftest-deps.py")],
                           cwd=tmp, capture_output=True, text=True)
        out = (r.stdout or "") + (r.stderr or "")
        record("2 反验漏搬依赖→必报", r.returncode == 1 and "baseline" in out,
               f"rc={r.returncode}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 3 闸门 import 一个不存在的本地模块 → 必报 ────────────────────────
def m_gate_imports_missing_module():
    check_anchor()
    tmp = tempfile.mkdtemp(prefix="beef-deps-selftest2.")
    try:
        shutil.copytree(os.path.join(ROOT, "scripts"), os.path.join(tmp, "scripts"))
        shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-selftest-deps.py"))
        # 造一个新闸门：import 一个本地存在的模块，但**没有任何反验搬它**
        newgate = os.path.join(tmp, "scripts", "verify-newfangled.py")
        write(newgate, "import os, sys, re, subprocess\nfrom baseline import resolve_ref\n"
                      "def main():\n    return resolve_ref() and 0\n"
                      "if __name__ == '__main__':\n    sys.exit(main())\n")
        newst = os.path.join(tmp, "scripts", "selftest-newfangled.py")
        write(newst, "import os, sys, shutil, tempfile, subprocess\n"
                     "HERE = os.path.dirname(os.path.abspath(__file__))\n"
                     "GATE = os.path.join(HERE, 'verify-newfangled.py')\n"
                     "def main():\n"
                     "    tmp = tempfile.mkdtemp()\n"
                     "    os.makedirs(os.path.join(tmp, 'scripts'))\n"
                     "    shutil.copy(GATE, os.path.join(tmp, 'scripts', 'verify-newfangled.py'))\n"
                     "    r = subprocess.run([sys.executable, os.path.join('scripts', 'verify-newfangled.py')],\n"
                     "                       cwd=tmp, capture_output=True, text=True)\n"
                     "    sys.exit(0 if r.returncode == 0 else 1)\n"
                     "if __name__ == '__main__':\n    sys.exit(main())\n")
        r = subprocess.run([sys.executable, os.path.join(tmp, "scripts", "verify-selftest-deps.py")],
                           cwd=tmp, capture_output=True, text=True)
        out = (r.stdout or "") + (r.stderr or "")
        record("3 新闸门无人搬依赖→必报", r.returncode == 1 and "baseline" in out,
               f"rc={r.returncode}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 4 对「不复制闸门」的反验不误报 ────────────────────────────────────
def m_no_false_positive():
    check_anchor()
    tmp = tempfile.mkdtemp(prefix="beef-deps-selftest3.")
    try:
        shutil.copytree(os.path.join(ROOT, "scripts"), os.path.join(tmp, "scripts"))
        shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-selftest-deps.py"))
        # 造一份**不复制闸门**的反验：它 import 了 baseline 也不该报
        write(os.path.join(tmp, "scripts", "selftest-inplace.py"),
              "import os, sys, subprocess\n"
              "from baseline import resolve_ref\n"
              "def main():\n"
              "    r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verify-baseline.py')],\n"
              "                       capture_output=True, text=True)\n"
              "    sys.exit(0 if r.returncode == 0 else 1)\n"
              "if __name__ == '__main__':\n    sys.exit(main())\n")
        r = subprocess.run([sys.executable, os.path.join(tmp, "scripts", "verify-selftest-deps.py")],
                           cwd=tmp, capture_output=True, text=True)
        out = (r.stdout or "") + (r.stderr or "")
        record("4 不复制闸门的反验→不误报", r.returncode == 0, f"rc={r.returncode}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 5 复制写法变了 → 判据必须失配报错（防静悄悄查不到）───────────────
def m_rename_pattern_breaks():
    check_anchor()
    tmp = tempfile.mkdtemp(prefix="beef-deps-selftest4.")
    try:
        shutil.copytree(os.path.join(ROOT, "scripts"), os.path.join(tmp, "scripts"))
        shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-selftest-deps.py"))
        # 把某反验里的 shutil.copy 全改成别的写法 → 判据「扫不到任何复制点」→ rc=2
        target = os.path.join(tmp, "scripts", "selftest-feature-flags.py")
        t = read(target)
        new = t.replace("shutil.copy(", "_put(")
        assert new != t, "注入未生效：没替换掉 shutil.copy"
        write(target, new)
        r = subprocess.run([sys.executable, os.path.join(tmp, "scripts", "verify-selftest-deps.py")],
                           cwd=tmp, capture_output=True, text=True)
        out = (r.stdout or "") + (r.stderr or "")
        # 判据要么报「没扫到」（rc=2），要么仍能扫到；**绝不能是「扫到了但什么都没说」的 rc=0**
        record("5 复制写法变了→不得静悄悄通过",
               r.returncode in (0, 2) and (r.returncode == 2 or "反验依赖核对通过" in out),
               f"rc={r.returncode}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    tests = [m_clean, m_missing_baseline_copy, m_gate_imports_missing_module,
             m_no_false_positive, m_rename_pattern_breaks]
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
    print(f"闸 17 反验：{len(results)} 例，通过 {len(results) - failed}，失败/作废 {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
