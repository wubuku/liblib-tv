#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三十九道闸（`verify-gate-alive.py`）的反向验证。

    **五例，三类分布各钉一例，外加两例守卫**：

    · **基线**：干净的一组小闸 → 必须报出「安静」那一类；
    · **不误伤**：带 `@baseline_guard` 装饰器的闸 → **必须被单列**，
      **不能算进「还在说话」**；
    · **能抓**：一个 `main` 之后还有代码的闸 → 注入必须**只动函数体**、
      **不能把那截也删掉**；
    · **守卫 1**：锚点不在场时必须报「前提失配」，不许拿 0 充数；
    · **守卫 2**：注入产出的文件必须仍然语法可解析——
      **而这一例是本批真踩到的**（见下面 `m_injection_must_be_syntactic`）。

**为什么要这么多守卫**：Batch 270 那道闸的注入连错三版
（截到文件末尾 / 丢 `def` 行 / 全局行号算错），
**而三次的输出形态都像「跑过了」**——
**所以「注入真的生效」与「注入什么都没做」必须能被机器区分**。
"""

import io
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.join(HERE, "verify-gate-alive.py")
results = []


def record(name, ok, detail=""):
    results.append((name, "通过" if ok else "失败", detail))


def write_gate(d, name, body, decorator=False):
    """造一道最小闸：`main` 的形态由调用方给。

    **夹具里必须有一份真的 `baseline.py`**——
    **第一版从真 `baseline` import `announce_fallback` 而没造那个模块**，
    **于是被造的闸在 import 阶段就崩掉、闸判据一道都没验到就 rc=2**，
    **而那个输出看起来像「判据坏了」**。
    **它也是「夹具不该向现实借素材」的又一次应验**：
    **借来的那个模块带了真实实现与真实依赖，而夹具要的只是「有一个会打印的东西」。

    **Batch 271：装饰器必须从 `baseline` 模块 import，不能在夹具闸里自己定义。**
    **第一版把 `def baseline_guard(...)` 直接写在夹具闸里**，
    **于是它与真树形状不同（真树 13 道全部是 `from baseline import … baseline_guard`）**，
    **而判据把它归到了别处**——
    **实测「靠装饰器才说话」那一句就断言不到**。
    **夹具必须复刻真实形状**（纪律 265）。
    """
    s = "scripts"
    d = os.path.join(d, s)
    os.makedirs(d, exist_ok=True)
    bp = os.path.join(d, "baseline.py")
    if not os.path.isfile(bp):
        with open(bp, "w", encoding="utf-8") as fh:
            fh.write(
                "def announce_fallback(*a, **k):\n"
                "    print('[兜底] 用例夹具自造的 announce_fallback')\n"
                "\n"
                "def baseline_guard(fn):\n"
                "    def w(*a, **k):\n"
                "        announce_fallback()\n"
                "        return fn(*a, **k)\n"
                "    return w\n")
    deco = "@baseline_guard\n" if decorator else ""
    src = (
        "import sys\n"
        "\n"
        "from baseline import announce_fallback, baseline_guard\n"
        "\n"
        "%s"
        "def main():\n"
        "%s"
        "\n"
        "if __name__ == '__main__':\n"
        "    sys.exit(main())\n" % (deco, body)
    )
    with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
        fh.write(src)
    return os.path.join(d, name)


def run_gate(d):
    r = subprocess.run([sys.executable, os.path.join(d, "scripts", "verify-gate-alive.py")],
                       cwd=d, capture_output=True, text=True, timeout=300)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def fixture(gates):
    """`gates` = [(文件名, 函数体, 是否带装饰器)]

    **被测的闸必须一起搬进夹具树**——
    **第一版忘了搬，于是 `run_gate` 找不到它、五例一起 rc=2**，
    **而那个输出看起来像「判据坏了」，不像「夹具少搬了一个文件」**
    （纪律 279 推论三：**「加」在闸那边、「记」得在反验那边**）。
    """
    d = tempfile.mkdtemp(prefix="b270-fixture.")
    for name, body, deco in gates:
        write_gate(d, name, body, deco)
    # 真闸必须有一道，否则判据会说「一道都没找到」
    write_gate(d, "verify-dummy.py", "    print('真闸在说话')\n    return 0\n")
    shutil.copy(GATE, os.path.join(d, "scripts", "verify-gate-alive.py"))
    return d


def m_plain_gates_go_silent():
    """基线：没有装饰器的闸注入后彻底安静 → 必须被归进「安静」那一类。"""
    d = fixture([("verify-plain.py", "    print('检查了')\n    return 0\n", False)])
    try:
        rc, out = run_gate(d)
        ok = rc == 0 and "注入后彻底安静" in out and "verify-plain.py" in out
        record("1 无装饰器的闸注入后安静→必须被归进「安静」类", ok, f"rc={rc}")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def m_guarded_must_not_be_counted_as_speaking():
    """**不误伤那一侧，也是最容易写坏的一半**。

    **带 `@baseline_guard` 的闸第一档仍有输出**——
    **而那输出是装饰器打的，不是「它还在检查」**。
    **Batch 270 第一版把它算进「还在说话」，那个分布会被读成「8 道更可靠」——
    而事实是「没有一道真闸靠自身逻辑在坏掉后还能被发现」**。

    **Batch 271 把口径改了三档**（安静 / 靠装饰器才说话 / 无装饰器却在说话），
    **所以这一例的断言也随口径改**——
    **而它钉的那件事没变：这类闸必须被单列，且**要能说出「去掉装饰器之后它也安静」**。
    """
    d = fixture([("verify-guarded.py", "    print('检查了')\n    return 0\n", True)])
    try:
        rc, out = run_gate(d)
        ok = (rc == 0
              and "第一档「还在说话」" in out
              and "去掉装饰器" in out
              and "verify-guarded.py" in out
              and "靠装饰器才说话 1 道" in out)
        record("2 带 guard 装饰器的闸必须单列，且要说清去掉装饰器后也安静",
               ok, f"rc={rc}")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def m_injection_only_touches_body():
    """**注入必须只动 `main` 的函数体**——`if __name__` 那截要原样保留。

    **第一版从 `def main():` 截到文件末尾，于是那截被一起删了**，
    **而 5 道真闸把逻辑写在 `if __name__` 之后**——
    **它们「注入后还能说话」是假象，注入根本没盖住它们**。
    **这一例造一道「逻辑写在 `if __name__` 之后」的闸，它必须被算成安静**
    （**因为装饰器之外的那截若真会说话，说明注入没生效**）。
    """
    d = tempfile.mkdtemp(prefix="b270-body.")
    try:
        sdir = os.path.join(d, "scripts")
        os.makedirs(sdir, exist_ok=True)
        src = (
            "import sys\n"
            "\n"
            "\n"
            "def helper():\n"
            "    print('这一行在 main 之外')\n"
            "\n"
            "\n"
            "def main():\n"
            "    print('检查了')\n"
            "    return 0\n"
            "\n"
            "if __name__ == '__main__':\n"
            "    helper()\n"
            "    sys.exit(main())\n"
        )
        with open(os.path.join(sdir, "verify-outside.py"), "w", encoding="utf-8") as fh:
            fh.write(src)
        write_gate(d, "verify-dummy.py", "    print('真闸在说话')\n    return 0\n")
        shutil.copy(GATE, os.path.join(d, "scripts", "verify-gate-alive.py"))
        rc, out = run_gate(d)
        # helper() 在 __main__ 里跑 → 它会说话 → 这一道不属于「安静」
        ok = rc == 0 and "verify-outside.py" not in out.split("彻底安静")[-1]
        record("3 main 之外还有代码时，注入只动函数体、不删那截", ok, f"rc={rc}")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def m_missing_anchor_is_not_zero():
    """**锚点不在场必须报「前提失配」，不许拿 0 充数**——
    **「没有可验的对象」与「验过了、没发现」返回同一个 0，就是纪律 101。**"""
    d = tempfile.mkdtemp(prefix="b270-anchor.")
    try:
        sdir = os.path.join(d, "scripts")
        os.makedirs(sdir, exist_ok=True)
        # 一道**没有 main** 的闸
        with open(os.path.join(sdir, "verify-nomain.py"), "w", encoding="utf-8") as fh:
            fh.write("import sys\nprint('我只是打印')\nsys.exit(0)\n")
        write_gate(d, "verify-dummy.py", "    print('真闸在说话')\n    return 0\n")
        shutil.copy(GATE, os.path.join(d, "scripts", "verify-gate-alive.py"))
        rc, out = run_gate(d)
        ok = rc == 0 and "前提失配" in out and "verify-nomain.py" in out
        record("4 没有 def main() 时必须报「前提失配」而不是算成安静", ok, f"rc={rc}")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def m_injection_must_be_syntactic():
    """**守卫：注入产出的文件必须仍然语法可解析**——**这一例是本批真踩到的**。

    **第二版注入把 `def main():` 那一行一起丢掉了**，
    **产出的文件第 2 行就 `expected an indented block`**，
    **而若没有这道守卫，37 道闸会一起报「注入未生效」**
    **——而那个输出看起来像「判据坏了」，不像「注入坏了」。**
    """
    d = fixture([("verify-ok.py", "    print('检查了')\n    return 0\n", False)])
    try:
        rc, out = run_gate(d)
        ok = rc == 0 and "注入产生了语法错误" not in out
        record("5 注入必须产出语法合法的文件（本批真踩到过）", ok, f"rc={rc}")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def m_guard_check_must_not_misfire_on_import():
    """**Batch 271 实测撞到并当场修掉的一个假阴性来源**。

    **守卫的第一版是「改写后的文件里不许再出现 `baseline_guard` 这个名字」**——
    **而 `from baseline import resolve_ref, BaselineError, module_ref, baseline_guard`
    那一行的 import 里也有这个名字**（实测 `verify-line-counts.py` 第 32 行），
    **而那不是装饰器**。
    **后果**：**13 道全被判成「注入未生效」**，
    **而分布显示「靠装饰器才说话 0 道」**——
    **这个输出看起来像「那 8 道不需要装饰器」，完全不像「守卫把全树判成了失败」**。

    **这一例造的正是那个形状**：一道 `main` 上有装饰器、**而 import 行里也带装饰器名**的闸，
    **它必须被归进「靠装饰器才说话」，不能被判成「注入未生效」**。
    """
    d = tempfile.mkdtemp(prefix="b271-import.")
    try:
        sdir = os.path.join(d, "scripts")
        os.makedirs(sdir, exist_ok=True)
        # **夹具的 baseline.py 必须真的有 baseline_guard**（造闸函数会写）
        write_gate(d, "verify-guard.py", "    print('检查了')\n    return 0\n", True)
        # 在 import 行里也带上装饰器名（真树 13 道全是这个形状）
        p = os.path.join(sdir, "verify-guard.py")
        t = io.open(p, encoding="utf-8").read()
        t = t.replace(
            "from baseline import announce_fallback",
            "from baseline import announce_fallback, baseline_guard")
        io.open(p, "w", encoding="utf-8").write(t)
        write_gate(d, "verify-dummy.py", "    print('真闸在说话')\n    return 0\n")
        shutil.copy(GATE, os.path.join(sdir, "verify-gate-alive.py"))
        rc, out = run_gate(d)
        #: **不能断言「输出里没有『注入未生效』四个字」**——
        #: **判据的解释文案里就写着那四个字**（讲守卫第一版误伤的那段），
        #: **第一版断言就是这么写的，于是恒假**。
        #: **要钉的是事实：没有任何一行以「— 文件名：注入未生效」的形态报出**。
        import re as _re
        reported = _re.search(r"^ *— \S+：注入未生效", out, _re.M)
        ok = (rc == 0 and reported is None
              and "靠装饰器才说话 1 道" in out)
        record("6 守卫不许把 import 行里的装饰器名误判成装饰器还在", ok, f"rc={rc}")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main():
    for t in (m_plain_gates_go_silent, m_guarded_must_not_be_counted_as_speaking,
              m_injection_only_touches_body, m_missing_anchor_is_not_zero,
              m_injection_must_be_syntactic, m_guard_check_must_not_misfire_on_import):
        try:
            t()
        except AssertionError as exc:
            record(t.__name__, "作废", "前提失配：%s" % exc)
    failed = 0
    for name, status, detail in results:
        print("  %s %s  %s" % ({"通过": "✓", "失败": "✗", "作废": "—"}[status],
                               name, detail))
        if status != "通过":
            failed += 1
    print("闸 39 反验：%d 例，通过 %d，失败/作废 %d"
          % (len(results), len(results) - failed, failed))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
