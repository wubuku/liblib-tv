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
  6  **循环搬运**、但常量里没有目标模块        → 必报（**钉「凡是循环就算」是错的**）
  7  **循环搬运**、且常量里确实有目标模块      → 不得报（**本批真修掉的那个假阳性**）

**用例 2 是本文件的核心**：它复现的正是 Batch 178 静悄悄坏了三个批次的那一类回归。

**用例 6/7 是同一个病第三次复发的那一对**（Batch 239）。本批给新闸 34 写反验时用了
`for dep in DEPS: shutil.copy(...)` 这种循环搬运，闸 17 上线首跑就报
「没有把 `pngstat` / `scope` 复制进临时 scripts/」——**而它搬得清清楚楚**。
Batch 190 已经在同一处修过两次（变量赋值链 → 参数形状 → 目标路径里的字面量），
**第三次复发在「实参里是个循环变量」上**。**6/7 必须成对**：
只钉 7 的话，修法会滑成「凡是循环就算」，那会让任何 `for x in anything:` 都通过（纪律 260）。
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
        #
        # **Batch 262：夹具必须自己钉死那个变量**（第一版这里没加，
        # **于是判据升级后用例 4 转红**）。
        # **先量过再判**：这不是误伤——
        # `BEEFTV_MANUAL_ROOT=/tmp` 下实测 `verify-baseline.py` **rc=2**
        # （`未找到 20-reference.md`，**整棵读错**），
        # **而不设与指向真树时都是 rc=0**。
        # **所以真正的新认知是：「不搬闸」不等于「不需要钉死变量」**——
        # 旧口径以前跳过这一类，是因为它把「搬没搬闸」当成了前置条件，
        # **而闸会不会读那个变量，取决于它跑不跑，与它被搬没搬无关**。
        write(os.path.join(tmp, "scripts", "selftest-inplace.py"),
              "import os, sys, subprocess\n"
              "from baseline import resolve_ref\n"
              "from stagedeps import child_env\n"
              "HERE = os.path.dirname(os.path.abspath(__file__))\n"
              "def main():\n"
              "    r = subprocess.run([sys.executable, os.path.join(HERE, 'verify-baseline.py')],\n"
              "                       capture_output=True, text=True,\n"
              "                       env=child_env(os.path.dirname(HERE)))\n"
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


# ── 6/7 循环搬运（Batch 239）——收紧与放宽必须成对 ────────────────────
#: 一份**只搬循环、常量里没有目标模块**的最小反验源码。
#: 判据对它必须仍然报「没搬」——**「凡是循环就算」是错的**（纪律 260）。
_LOOP_TPL = '''# -*- coding: utf-8 -*-
import os, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEPS = (%(deps)s)


def run():
    d = tempfile.mkdtemp(prefix="x.")
    os.makedirs(os.path.join(d, "scripts"), exist_ok=True)
    shutil.copy(os.path.join(HERE, "verify-shot-pixels.py"),
                os.path.join(d, "scripts", "verify-shot-pixels.py"))
    for dep in DEPS:
        shutil.copy(os.path.join(HERE, dep), os.path.join(d, "scripts", dep))
    return 0


if __name__ == "__main__":
    sys.exit(run())
'''


def _loop_case(name, deps, want_rc, want_in):
    """在一棵临时副本仓上放一份循环搬运的反验，再跑闸 17。"""
    tmp = tempfile.mkdtemp(prefix="beef-deps-selftest-loop.")
    try:
        shutil.copytree(os.path.join(ROOT, "scripts"), os.path.join(tmp, "scripts"))
        shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-selftest-deps.py"))
        src = _LOOP_TPL % {"deps": deps}
        write(os.path.join(tmp, "scripts", "selftest-loop-demo.py"), src)
        r = subprocess.run([sys.executable, os.path.join(tmp, "scripts", "verify-selftest-deps.py")],
                           cwd=tmp, capture_output=True, text=True)
        out = (r.stdout or "") + (r.stderr or "")
        good = (r.returncode == want_rc) and (want_in in out)
        record(name, good, f"rc={r.returncode}（期望 {want_rc}）")
        if not good:
            print("      " + out.strip().replace("\n", "\n      "))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def m_loop_copy_without_the_module():
    """能抓：循环搬了，**但常量里没有目标模块** → 必须报。"""
    check_anchor()
    # **示例闸选 `verify-shot-pixels.py` 是有理由的**：它的本地依赖闭包**恰好只有
    # `pngstat` 一个**（`local_closure('verify-shot-pixels') == ['pngstat', ...]`），
    # **所以这一对用例的成败不会被别的依赖搅浑**。
    _loop_case("6 循环里没搬那个模块→必报",
               '"other.py",', 1, "没有把它复制进临时 scripts/")


def m_loop_copy_with_the_module():
    """不误伤：循环搬的常量里**确实有**目标模块 → 不得报。

    **这正是 Batch 239 上线首跑的实况**：`selftest-shot-integrity.py` 写的是
    `for dep in DEPS: shutil.copy(...)`，判据却报它没搬 `pngstat` / `scope`。
    **假阳性落在一条刚上线的反验上，而下一个人多半会去改反验而不是改判据。**
    """
    check_anchor()
    _loop_case("7 循环里搬了那个模块→不得报",
               '"pngstat.py",', 0, "反验依赖核对通过")


def _copytree_case(name, copytree_line, want_rc, want_in):
    """Batch 247 新增的一对：`copytree` 到底搬的是不是 `scripts/`。

    **为什么必须成对**：Batch 247 修的那处判据扩的是「`copytree` 搬了整份
    `scripts/` 就等于依赖都在」。**如果只测「搬了 scripts/ → 不报」这一侧，
    那条判据写成「凡是有 copytree 就算」也能全过**——
    而那会把「搬了另一个目录」当成搬了 scripts/，**依赖照样不在**。
    **左边那一例是这道判据的鉴别力。**
    """
    check_anchor()
    tmp = tempfile.mkdtemp(prefix="beef-deps-selftest-ctree.")
    try:
        shutil.copytree(os.path.join(ROOT, "scripts"), os.path.join(tmp, "scripts"))
        shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-selftest-deps.py"))
        target = os.path.join(tmp, "scripts", "selftest-feature-flags.py")
        t = read(target)
        new = re.sub(r'^\s*shutil\.copy\(BASELINE,[^\n]*\n', "", t, count=1, flags=re.M)
        assert new != t, "注入未生效：baseline 搬运那行没找到"
        new = new.replace("import shutil", "import shutil", 1)
        new = new.replace("def main(", copytree_line + "\ndef main(", 1)
        write(target, new)
        r = subprocess.run([sys.executable, os.path.join(tmp, "scripts", "verify-selftest-deps.py")],
                           cwd=tmp, capture_output=True, text=True)
        out = (r.stdout or "") + (r.stderr or "")
        record(name, r.returncode == want_rc and want_in in out, f"rc={r.returncode}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def m_copytree_other_dir_still_reports():
    """能抓：搬的是**别的目录**（`docs/`），不算搬了 `scripts/` → 必须报。"""
    _copytree_case(
        "8 copytree 搬的是别的目录→必报（不是「凡有 copytree 就算」）",
        'def _elsewhere():\n    shutil.copytree(os.path.join(ROOT, "docs"), os.path.join(os.getcwd(), "docs"))',
        1, "baseline")


def m_copytree_scripts_dir_passes():
    """不误伤：搬的**就是整份 `scripts/`** → 不得报。

    **这正是 Batch 247 的实况**：`selftest-retracted-claims.py` 写的是
    `shutil.copytree(os.path.join(ROOT, "scripts"), dst, ignore=...)`，
    旧判据要求第一个实参是裸单词、第二个实参里直接出现 `scripts`，
    **于是把一份确实搬了整份 scripts/ 的反验报成「没搬」**，
    闸 18 当场把闸 17 的反验判红（4 例失败）。
    """
    _copytree_case(
        "9 copytree 搬的是整份 scripts/→不得报（Batch 247 实况）",
        'def _everywhere():\n    shutil.copytree(os.path.join(ROOT, "scripts"), os.path.join(os.getcwd(), "scripts-all"))',
        0, "反验依赖核对通过")


def _stage_gate_case(name, stage_line, want_rc, want_in):
    """Batch 253 新增的一对：`stage_gate(...)` 到底搬的是不是那个闸。

    **为什么必须成对**：`stage_gate()` 把整个闭包都搬走，
    **所以「实参里写的那个闸名对不对」是它唯一的失手方式**——
    写 `stage_gate(tmp, "verify-别的闸")` 而被测闸是 `verify-feature-flags`，
    **它就把另一个闸的依赖搬了，而被测闸自己的依赖一个没搬**。
    **只测「闸名对得上 → 不报」的话，那条判据写成「凡有 stage_gate 就算」也能全过**，
    **而那正是本批要消灭的那类假绿**（Batch 190 修过三次同源的错）。
    **实测的鉴别力在右边那一条，不在左边**——而这与本函数注释第一版写的相反，
    **第一版把「改前实测 rc=0」当成事实写下来了，实测是 rc=1**：
    改前的判据**不认识 `stage_gate`**，于是走「没认出来 → 按老路逐个核 `baseline` → 报」，
    **而那条老路恰好是对的**。**换句话说左边那条在改前是「碰巧报对」的假通过。**
    **这一条是鉴别力用例设计里最容易搞反的地方**：
    「能抓」方向看着该有鉴别力，**其实鉴别力在「不误伤」那侧**——
    因为「漏报」只有在判据**多做**了什么的时候才看得见，
    而「多认了一种搬运方式」这件事在改前**表现为误报，不表现为漏报**。
    **注释里写「改前实测 rc=0」而实际是 rc=1，等于给下一个人一条假事实**
    （Batch 248 的教训：会让人去改不存在的东西，比漏报更贵）。
    """
    check_anchor()
    tmp = tempfile.mkdtemp(prefix="beef-deps-selftest-stage.")
    try:
        shutil.copytree(os.path.join(ROOT, "scripts"), os.path.join(tmp, "scripts"))
        shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-selftest-deps.py"))
        target = os.path.join(tmp, "scripts", "selftest-feature-flags.py")
        t = read(target)
        # 删掉显式的 baseline 搬运（换成 stage_gate 的前提）
        new = re.sub(r'^\s*shutil\.copy\(BASELINE,[^\n]*\n', "", t, count=1, flags=re.M)
        assert new != t, "注入未生效：baseline 搬运那行没找到"
        new = new.replace("def main(", stage_line + "\ndef main(", 1)
        write(target, new)
        r = subprocess.run([sys.executable, os.path.join(tmp, "scripts", "verify-selftest-deps.py")],
                           cwd=tmp, capture_output=True, text=True)
        out = (r.stdout or "") + (r.stderr or "")
        record(name, r.returncode == want_rc and want_in in out, f"rc={r.returncode}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def m_stage_gate_wrong_gate_still_reports():
    """能抓：`stage_gate` 搬的是**别的闸** → 那个闸的依赖不在 → 必须报。"""
    _stage_gate_case(
        "10 stage_gate 搬的是另一个闸→必报（不是「凡有 stage_gate 就算」）",
        'def _stage():\n    from stagedeps import stage_gate\n'
        '    stage_gate(tmp, "verify-quota-tables")',
        1, "baseline")


def m_stage_gate_right_gate_passes():
    """不误伤：`stage_gate` 搬的**就是被测闸** → 闭包全齐 → 不得报。"""
    _stage_gate_case(
        "11 stage_gate 搬的就是被测闸→不得报（闭包自动齐备）",
        'def _stage():\n    from stagedeps import stage_gate\n'
        '    stage_gate(tmp, "verify-feature-flags")',
        0, "反验依赖核对通过")


def m_transport_count_is_reported():
    """不误伤：闸 17 必须把「**还有几份靠人记**」这个数报出来。

    **Batch 254 新增。** 这不是一条「抓缺陷」的判据，是一条**把进度变成可数的事**的判据：
    `stagedeps` 落地之后，24 份反验里只有 1 份真的用上了自动算闭包，
    **而剩下 23 份每加一个本地 import 就得人记一次**——
    Batch 178/181/197/251/252 **五次漏搬全部发生在这一类反验上**。
    **这个事实此前不在任何输出里**，于是「还剩多少」只存在于某个人的记忆里。

    **为什么只报不拦**：一次性改 20 多份反验的出错面远大于它省下的事，
    **而「还剩 23 份」一旦写进构建日志，它就从「没人知道」变成「下一个人接手的起点」**
    （纪律 272：把「有几份」变成一件可数的事）。
    **这条用例钉的是「那个数必须出现」，不是「那个数必须是 0」。**
    """
    check_anchor()
    tmp = tempfile.mkdtemp(prefix="beef-deps-selftest-count.")
    try:
        shutil.copytree(os.path.join(ROOT, "scripts"), os.path.join(tmp, "scripts"))
        shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-selftest-deps.py"))
        r = subprocess.run([sys.executable, os.path.join(tmp, "scripts", "verify-selftest-deps.py")],
                           cwd=tmp, capture_output=True, text=True)
        out = (r.stdout or "") + (r.stderr or "")
        ok = (r.returncode == 0 and "份已用 `stagedeps` 自动算闭包" in out
              and "份仍在手写 `shutil.copy` 清单" in out)
        record("12 「还有几份靠人记搬运」必须被报出来（可数的事）", ok, f"rc={r.returncode}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 13/14 方向一之二：真跑了闸，就必须告诉它手册根在哪（Batch 260）──
def _env_fixture(tmp, mode):
    """造一份反验：它把一个**闭包会用到 `baseline`** 的闸搬进临时树。

    **四种形态共用同一份搬运**（所以除那一件事外，其余全部合规）：

    | `mode` | 那几次 `subprocess` | 期望 | 用例 |
    |---|---|---|---|
    | `no_env` | 跑一次，**不传 `env=`** | 必报 | 13 |
    | `text_only` | **只当文本读**，从不执行 | 不得报 | 14 |
    | `partial` | 跑两次：**一次钉死、一次不传** | 必报 | 15 |
    | `pinned` | 跑两次，**两次都钉死** | 不得报 | 16 |

    **前两种是 Batch 260 立的**（那一对问的是「能不能分清『搬了』与『跑了』」）。

    **后两种是 Batch 262 加的，因为它们才是真实缺口的形状**：
    旧判据只问「**这份反验的源码里有没有出现过** `BEEFTV_MANUAL_ROOT`」，
    而 `partial` 那一份的变量名**在钉死的那一次里出现过**——
    于是被判成合规，**而它跑真树那一次真的会读错整棵树**
    （实测三份在 `BEEFTV_MANUAL_ROOT=/tmp` 下 rc=1，闸却一直 rc=0）。

    **而 `pinned` 那一对钉住的是判据的另一半**：
    **判据必须认 `child_env(…)` 这个共享构造函数**——
    **收敛之后源码里已经没有那个变量的字面量了，
    只认字面量的判据会把每一处合规的收敛都报成缺陷**（预演实测报了 4 份，全是合规的）。
    """
    shutil.copytree(os.path.join(ROOT, "scripts"), os.path.join(tmp, "scripts"))
    shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-selftest-deps.py"))
    newgate = os.path.join(tmp, "scripts", "verify-newfangled.py")
    write(newgate, "import os, sys\nfrom baseline import resolve_ref\n"
                   "def main():\n    return resolve_ref() and 0\n"
                   "if __name__ == '__main__':\n    sys.exit(main())\n")
    #: **方向一（依赖搬运）必须先满足**——否则 rc=1 是它报的，
    #: **这一对就分不出「是新判据报的」还是「是老判据报的」**。
    #: **一对用例只差一件事的前提是：除那一件事外，其余全部合规。**
    body = ("    tmp = tempfile.mkdtemp()\n"
            "    os.makedirs(os.path.join(tmp, 'scripts'))\n"
            "    shutil.copy(GATE, os.path.join(tmp, 'scripts', 'verify-newfangled.py'))\n"
            "    shutil.copy(BASE, os.path.join(tmp, 'scripts', 'baseline.py'))\n"
            "    shutil.copy(BEEFSRC, os.path.join(tmp, 'scripts', 'beefsrc.py'))\n")
    head = ("import os, sys, shutil, tempfile, subprocess\n"
            "from stagedeps import child_env\n"
            "HERE = os.path.dirname(os.path.abspath(__file__))\n"
            "GATE = os.path.join(HERE, 'verify-newfangled.py')\n"
            "BASE = os.path.join(HERE, 'baseline.py')\n"
            "BEEFSRC = os.path.join(HERE, 'beefsrc.py')\n"
            "def main():\n")
    one = ("    r = subprocess.run([sys.executable, os.path.join('scripts', "
           "'verify-newfangled.py')],\n"
           "                       cwd=tmp, capture_output=True, text=True%s)\n"
           "    sys.exit(0 if r.returncode == 0 else 1)\n")
    if mode in ("no_env", "text_only"):
        head = head.replace("from stagedeps import child_env\n", "")
    if mode == "no_env":
        body += one % ""
    elif mode == "text_only":
        body += ("    with open(os.path.join(tmp, 'scripts', 'verify-newfangled.py'),\n"
                 "              encoding='utf-8') as fh:\n"
                 "        assert 'baseline' in fh.read()\n"
                 "    sys.exit(0)\n")
    elif mode == "partial":
        #: **钉死的那一次放前面**——**它就是让旧判据放行的原因**：
        #: 变量名出现在这份反验的源码里，而后面那一次**什么都没传**。
        #:
        #: **而这一处必须用「字面量」形态，不能用 `child_env(…)`**（第一版就是用了它）：
        #: **夹具要复刻真实缺陷的形状**——
        #: 实测转红的那三份用的正是 `{**os.environ, "BEEFTV_MANUAL_ROOT": …}`，
        #: **而旧口径恰恰放过它**。
        #: **用 `child_env` 写的话源码里根本没有那个变量的字面量，旧口径照样会报**——
        #: **那一对就分不出新旧，而「鉴别力验证」验的其实是「我写的那一种」。**
        head = head.replace("from stagedeps import child_env\n", "")
        body += one % (', env={**os.environ, "BEEFTV_MANUAL_ROOT": tmp}')
        body += one % ""
    elif mode == "pinned":
        body += one % ", env=child_env(tmp)"
        body += one % ", env=child_env(tmp)"
    else:
        raise AssertionError("未知的 mode：%r" % mode)
    write(os.path.join(tmp, "scripts", "selftest-newfangled.py"),
          head + body + "if __name__ == '__main__':\n    sys.exit(main())\n")




def m_missing_env_reported():
    """**能抓那一侧**：真跑了一个会用 `baseline` 的闸，却没告诉它手册根在哪。"""
    check_anchor()
    tmp = tempfile.mkdtemp(prefix="beef-deps-env-miss.")
    try:
        _env_fixture(tmp, "no_env")
        r = subprocess.run([sys.executable, os.path.join(tmp, "scripts", "verify-selftest-deps.py")],
                           cwd=tmp, capture_output=True, text=True)
        out = (r.stdout or "") + (r.stderr or "")
        ok = (r.returncode == 1 and "✗ 方向一之二" in out
              and "BEEFTV_MANUAL_ROOT" in out and "selftest-newfangled.py" in out)
        record("13 真跑会用 baseline 的闸却没设 BEEFTV_MANUAL_ROOT → 必报", ok, f"rc={r.returncode}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def m_text_only_staging_not_reported():
    """**不误伤那一侧**：搬运一模一样，**只是从不执行那个闸** → 不得报。

    **这一条钉住的是判据的边界，不是它的强度**：
    **第一版口径按「搬了闸」算，于是把 `selftest-duplication.py` 误报成缺陷**
    ——**而那份实测 6/6 通过、什么事也没有**。
    **一个会误报的判据，下一个人会去把正确的写法改错**（纪律 260）。
    """
    check_anchor()
    tmp = tempfile.mkdtemp(prefix="beef-deps-env-text.")
    try:
        _env_fixture(tmp, "text_only")
        r = subprocess.run([sys.executable, os.path.join(tmp, "scripts", "verify-selftest-deps.py")],
                           cwd=tmp, capture_output=True, text=True)
        out = (r.stdout or "") + (r.stderr or "")
        #: **盯 `✗ 方向一之二` 这一行，而不是在全文里找「方向一之二」**——
        #: **闸的通过语里就印着「（方向一之二）」**
        #: （「N 份反验真跑会用 baseline/scope 的闸，都已给子进程设 …」），
        #: **第一版断言 `"方向一之二" not in out` 于是恒假**，
        #: **而闸其实一点问题都没报**（rc=0）。
        #: **这与 Batch 255 那次「断言 C0 不在输出里、而通过语写着「无 C0 控制字符」」
        #: 是同一个坑：拿一句散文当判别式，散文会自己走进那个子串里。**
        ok = r.returncode == 0 and "✗ 方向一之二" not in out
        record("14 只把闸当文本扫、从不执行 → 不得报（「搬了」≠「跑了」）",
               ok, f"rc={r.returncode}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def m_partial_pins_reported():
    """**能抓那一侧（Batch 262）**：一次钉死、一次不传 → 那一次必须被点名。

    **这一份是旧判据真的看不见的东西**：
    变量名**在这份反验的源码里出现过**（钉死的那一次），
    于是旧判据判它合规，**而它跑真树那一次会读错整棵树**。
    **实测同一份夹具：旧判据 rc=0、新判据 rc=1**（`/tmp/b262_cmp.py` 跑过）。
    """
    check_anchor()
    tmp = tempfile.mkdtemp(prefix="beef-deps-env-partial.")
    try:
        _env_fixture(tmp, "partial")
        r = subprocess.run([sys.executable, os.path.join(tmp, "scripts", "verify-selftest-deps.py")],
                           cwd=tmp, capture_output=True, text=True)
        out = (r.stdout or "") + (r.stderr or "")
        ok = (r.returncode == 1 and "✗ 方向一之二" in out
              and "selftest-newfangled.py" in out and "没有 `env=`" in out)
        record("15 一次钉死一次没钉（源码里有那个变量名）→ 仍必须报",
               ok, f"rc={r.returncode}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def m_all_pinned_not_reported():
    """**不误伤那一侧（Batch 262）**：每一次都钉死 → 不得报。

    **它钉的是判据认不认得 `child_env(…)`**：
    收敛之后那些源码里**再也没有那个变量的字面量**了——
    **只认字面量的判据会把每一处合规的收敛都报成缺陷**，
    **而下一个人会去把正确的写法改回手写字面量**（纪律 260）。
    **实测：判据若只认字面量，这一份会被误报**。
    """
    check_anchor()
    tmp = tempfile.mkdtemp(prefix="beef-deps-env-pinned.")
    try:
        _env_fixture(tmp, "pinned")
        r = subprocess.run([sys.executable, os.path.join(tmp, "scripts", "verify-selftest-deps.py")],
                           cwd=tmp, capture_output=True, text=True)
        out = (r.stdout or "") + (r.stderr or "")
        ok = r.returncode == 0 and "✗ 方向一之二" not in out
        record("16 每一次都钉死（写成共享的 child_env）→ 不得报",
               ok, f"rc={r.returncode}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _open_write_fixture(tmp, with_deps):
    """造一份反验：它把一个**闭包会用到 `baseline`** 的闸**用 `open().write()` 搬进临时树**。

    `with_deps=True`  → 依赖用 `shutil.copy` 搬齐
    `with_deps=False` → **一个 `shutil.copy` 都不写**

    **为什么专门造这种写法**（Batch 264 实测出来的）：
    `selftest-shot-version-source.py` 的 `copy_gate()` 用
    `open(…/scripts/<闸名>, "w").write(src)` 搬闸——**因为它要把 `OFF_TASK` 免检表清空**，
    **而 `shutil.copy` 做不到「搬过去再改」**。
    **而 `copies_gate_into_tmp()` 只认 `shutil.copy` / `stage_gate` / `stage_all` / `copytree`**，
    **于是这份反验被整份跳过**——
    **实测后果**：闸 17 在它 13 例里 11 例转红（`ModuleNotFoundError`）时**一声不吭**。
    **那是假阴性：坏掉了没人知道，而闸报得很绿。**

    **而夹具自己必须把那个变量钉死**（`env=child_env(d)`）：
    **方向一之二会在方向一之前报它**，
    **第一版夹具没钉，用例 17 的「绿」是方向一之二给的绿、不是方向一的**
    （纪律 262 推论一：**一对用例只差一件事的前提是其余全部合规**）。
    **这一对用例要钉的正是那个缺口**：
    17 只差「有没有搬齐依赖」这一件事，**而它们搬闸的方式是全新的**——
    **所以旧判据下 17 必红（它整份跳过了），新判据下 17 与 18 都绿**。
    """
    shutil.copytree(os.path.join(ROOT, "scripts"), os.path.join(tmp, "scripts"))
    shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-selftest-deps.py"))
    write(os.path.join(tmp, "scripts", "verify-newfangled.py"),
          "import os, sys\nfrom baseline import resolve_ref\n"
          "def main():\n    return resolve_ref() and 0\n"
          "if __name__ == '__main__':\n    sys.exit(main())\n")
    #: **两个依赖都要搬**——`baseline` 自己 import `beefsrc`，
    #: **而闭包不是第一层**（Batch 205 实测：只看第一层，4 份反验 0/5、0/6、0/5、0/4 全红而构建全绿）。
    #: **第一版只搬了 `baseline`，闸报出两条而不是零条**——
    #: **用例红在「没搬 beefsrc」上，而它要核的是「有没有搬齐」**（纪律 281 推论四）。
    deps = (('    shutil.copy(os.path.join(HERE, BASELINE),\n'
             "                os.path.join(d, 'scripts', 'baseline.py'))\n"
             '    shutil.copy(os.path.join(HERE, BEEFSRC),\n'
             "                os.path.join(d, 'scripts', 'beefsrc.py'))\n")
            if with_deps else "")
    body = (
        "import os, sys, shutil, subprocess, tempfile\n"
        "from stagedeps import child_env\n"
        "HERE = os.path.dirname(os.path.abspath(__file__))\n"
        "GATE = os.path.join(HERE, 'verify-newfangled.py')\n"
        "BASELINE = 'baseline.py'\n"
        "BEEFSRC = 'beefsrc.py'\n"
        "def main():\n"
        "    d = tempfile.mkdtemp()\n"
        "    os.makedirs(os.path.join(d, 'scripts'))\n"
        "    src = open(os.path.join(HERE, GATE), encoding='utf-8').read()\n"
        "    with open(os.path.join(d, 'scripts', 'verify-newfangled.py'), 'w',\n"
        "              encoding='utf-8') as f:\n"
        "        f.write(src)\n"                       # **搬闸：写文本**
        + deps +
        "    r = subprocess.run([sys.executable, os.path.join(d, 'scripts',\n"
        "                                            'verify-newfangled.py')],\n"
        "                       cwd=d, capture_output=True, text=True,\n"
        "                       env=child_env(d))\n"
        "    sys.exit(0 if r.returncode == 0 else 1)\n"
    )
    write(os.path.join(tmp, "scripts", "selftest-openwrite.py"),
          body + "if __name__ == '__main__':\n    sys.exit(main())\n")


def m_open_write_missing_dep_reported():
    """**能抓那一侧**：`open().write()` 搬闸、依赖没搬 → 判据必须报出来。

    **旧判据下这一例必红**：`copies_gate_into_tmp()` 认不出这种搬法，
    **整份反验被跳过 → rc=0 → 而用例期望 rc=1**。
    **新判据下它绿**——**这一红一绿就是本次升级的全部鉴别力**。
    """
    check_anchor()
    tmp = tempfile.mkdtemp(prefix="beef-deps-openwrite-miss.")
    try:
        _open_write_fixture(tmp, with_deps=False)
        r = subprocess.run([sys.executable, os.path.join(tmp, "scripts", "verify-selftest-deps.py")],
                           cwd=tmp, capture_output=True, text=True)
        out = (r.stdout or "") + (r.stderr or "")
        ok = (r.returncode == 1 and "✗ 方向一" in out
              and "baseline" in out and "selftest-openwrite.py" in out)
        record("17 用 open().write() 搬闸、依赖没搬 → 必报（旧判据整份跳过它）",
               ok, f"rc={r.returncode}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def m_open_write_with_deps_not_reported():
    """**不误伤那一侧**：同样用 `open().write()` 搬闸，依赖搬齐了 → 不得报。

    **它钉的是「认得这种搬法之后不要顺手把别的也报出来」**：
    **一份反验为了搬闸而改用 `open().write()`，不该因此被整份核出新的红**。
    """
    check_anchor()
    tmp = tempfile.mkdtemp(prefix="beef-deps-openwrite-ok.")
    try:
        _open_write_fixture(tmp, with_deps=True)
        r = subprocess.run([sys.executable, os.path.join(tmp, "scripts", "verify-selftest-deps.py")],
                           cwd=tmp, capture_output=True, text=True)
        out = (r.stdout or "") + (r.stderr or "")
        ok = r.returncode == 0 and "selftest-openwrite.py" not in out
        record("18 用 open().write() 搬闸、依赖搬齐 → 不得报", ok, f"rc={r.returncode}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _sh_fixture(tmp, body):
    """造一份 `.sh` 反验夹具，`body` 是它除 shebang 外的全部内容。

    **Batch 266**：`scripts/` 下有 4 份 `.sh` 反验，而闸 17 那个
    `selftests` 列表**只收 `.py`**——**所以它们从来没被核过**。
    **判据新增「方向三」：每份 `.sh` 必须落在 S1/S2/S3 之一**，
    **而哪一种都不属于就是「注入直接打在真树上」，必须报。**
    """
    shutil.copytree(os.path.join(ROOT, "scripts"), os.path.join(tmp, "scripts"))
    shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-selftest-deps.py"))
    write(os.path.join(tmp, "scripts", "selftest-probe.sh"),
          "#!/usr/bin/env bash\n" + body)
    return tmp


def _run_gate(tmp):
    r = subprocess.run([sys.executable, os.path.join(tmp, "scripts", "verify-selftest-deps.py")],
                       cwd=tmp, capture_output=True, text=True)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


#: **`$` 在夹具文本里到处都要用**，而它不能直接写进 shell 单引号串的拼接里
#: ——所以同一个模块级常量，两侧各留一份（Batch 266 实测：这个占位符漏了一处，
#: **而漏的那一处只在真树之外的副本里才暴露，闸自己察觉不到**）。
DOLLAR = chr(36)

#: **三份合规夹具各一具**——**形态是实测出来的，不是设计出来的**（纪律 265：
#: **判据要照着「现场已经有什么」定，照着理想形态定会把它判红**）。
#: **本批判据的前两版就是这么错的：都只认一种，于是四份全红。**
SH_FORMS = {
    "S1 搬闸": 'HERE="' + DOLLAR + '(cd "' + DOLLAR + '(dirname "' + DOLLAR + '{BASH_SOURCE[0]}")" && pwd)\n'
               'WORK="$(mktemp -d)"\n'
               'cp "' + DOLLAR + 'HERE/verify-tables.py" "' + DOLLAR + 'WORK/scripts/"\n'
               'mkdir -p "' + DOLLAR + 'WORK/scripts"\n'
               'cp "' + DOLLAR + 'HERE/tablerow.py" "' + DOLLAR + 'WORK/scripts/"\n'
               'python3 "' + DOLLAR + 'WORK/scripts/verify-tables.py" "' + DOLLAR + 'WORK"\n',
    "S2 搬数据": 'HERE="' + DOLLAR + '(cd "' + DOLLAR + '(dirname "' + DOLLAR + '{BASH_SOURCE[0]}")" && pwd)\n'
                 'ROOT="$(dirname "' + DOLLAR + 'HERE")"\n'
                 'WORK="$(mktemp -d)"\n'
                 'GATE="' + DOLLAR + 'HERE/verify-tables.py"\n'
                 'cp "' + DOLLAR + 'ROOT/20-reference.md" "' + DOLLAR + 'WORK/"\n'
                 'python3 "' + DOLLAR + 'GATE" "' + DOLLAR + 'WORK"\n',
    "S3 快照回滚": 'HERE="' + DOLLAR + '(cd "' + DOLLAR + '(dirname "' + DOLLAR + '{BASH_SOURCE[0]}")" && pwd)\n'
                   'SNAP="$(mktemp -d)"\n'
                   'cp "' + DOLLAR + 'HERE/verify-tables.py" "$SNAP/"\n'
                   'git hash-object -w /dev/null >/dev/null\n'
                   'python3 "' + DOLLAR + 'SNAP/verify-tables.py"\n',
}


def _sh_form_case(label, expect_in_output):
    """不误伤那一侧：这份 `.sh` 合规 → 闸必须 rc=0，**且必须说出它属于哪一种形态**。

    **第一版断言写成「`方向三` 不在输出里」——而那条是错的**：
    **判据成功时正是要把形态打进「视野外」那一段的**，
    **所以这条断言恒假，三个用例全红**（实测 rc=0、闸根本没报）。
    **正确的不误伤是三件事同时成立**：rc=0、**没有 `✗ 方向三`**、**且认出了形态**——
    **第三条最要紧**：一个「什么都没核」的闸同样会 rc=0，
    **而它 rc=0 的原因与「核过了且合规」在输出上完全一样**（纪律 300 推论一）。
    """
    def run():
        check_anchor()
        tmp = tempfile.mkdtemp(prefix="beef-deps-sh-")
        try:
            _sh_fixture(tmp, SH_FORMS[label])
            rc, out = _run_gate(tmp)
            ok = (rc == 0 and "✗ 方向三" not in out
                  and "selftest-probe.sh" in out and "视野外" in out)
            record(f"19-21 `.sh` 落在「{label}」→ 不得报，且必须认出这个形态",
                   ok, f"rc={rc}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return run


def m_sh_no_form_reported():
    """**必须成对的能抓那一侧**：一种形态都不属于 → 必须报。

    **它复刻的是真缺陷的形状**：一份 `.sh` 反验**既不搬闸、也不搬数据、也不造合成输入**，
    **那么它的每一次注入都直接改真树上的手册**——
    **而闸会红、红的是别人的手册，反验自己不留痕。**
    **这比不写反验更糟**，因为「有个反验在看着这个闸」这句话仍然是成立的。
    """
    check_anchor()
    tmp = tempfile.mkdtemp(prefix="beef-deps-sh-bad.")
    try:
        _sh_fixture(tmp,
                    'HERE="' + DOLLAR + '(cd "' + DOLLAR + '(dirname "' + DOLLAR + '{BASH_SOURCE[0]}")" && pwd)\n'
                    'ROOT="$(dirname "' + DOLLAR + 'HERE")"\n'
                    'python3 -c "'
                    + DOLLAR + 'f=open(\"' + DOLLAR + 'ROOT/PROGRESS.md\",\"a\");'
                      'f.write(\"x\");f.close()"\n')
        rc, out = _run_gate(tmp)
        ok = (rc == 1 and "✗ 方向三" in out and "selftest-probe.sh" in out
              and "真树" in out)
        record("22 `.sh` 三种形态都不属于 → 必报（注入直接打在真树上）",
               ok, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    tests = [m_clean, m_missing_baseline_copy, m_gate_imports_missing_module,
             m_no_false_positive, m_rename_pattern_breaks,
             m_loop_copy_without_the_module, m_loop_copy_with_the_module,
             m_copytree_other_dir_still_reports, m_copytree_scripts_dir_passes,
             m_stage_gate_wrong_gate_still_reports, m_stage_gate_right_gate_passes,
             m_transport_count_is_reported,
             m_missing_env_reported, m_text_only_staging_not_reported,
             m_partial_pins_reported, m_all_pinned_not_reported,
             m_open_write_missing_dep_reported, m_open_write_with_deps_not_reported,
             _sh_form_case("S1 搬闸", False), _sh_form_case("S2 搬数据", False),
             _sh_form_case("S3 快照回滚", False), m_sh_no_form_reported]
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
