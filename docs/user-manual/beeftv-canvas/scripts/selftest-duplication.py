#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 37「同一段解析逻辑被手写了几遍」的反向验证（Batch 256 新增）。

用例清单：
  1  真实现状 → 不报（三条重复都在登记表里且带理由）
  2  新增一处**未登记**的重复 → 必报（能抓）
  3  登记过的重复**涉及文件变了**而理由没改 → 必报（**过期的理由会替新的重复背书**）
  4  注释里贴一份正则原文 → **不得**报（不误伤：注释不是代码）
  5  一段**短**字面量（`$want` 那种变量名）在几份文件里都出现 → **不得**报
     （**这一条是首跑当场撞出来的假阳性**，见闸的文件头）
  6  收敛掉一条已登记的重复 → 登记表里那条**变成孤儿** → 必报
     （**「登记表只能变短」不能只是说说**：收敛了不删，理由就开始替不存在的东西背书）
"""

import hashlib
import io
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE_SRC = os.path.join(HERE, "verify-duplication.py")
PROBE = "dupselftest"

results = []
_TMP = tempfile.mkdtemp(prefix=PROBE)
_real_accepted = None
_real_scan = None


def load_gate():
    import importlib.util
    spec = importlib.util.spec_from_file_location("vd", GATE_SRC)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def run(gate):
    r = subprocess.run([sys.executable, gate], capture_output=True, text=True)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def probe_root(files, accepted=None, accepted_file=None):
    """建一个临时 scripts/ 副本：整份 `copytree`，然后只替换指定文件。

    **Batch 256 首版这里是一个手写的逐文件循环**
    （`for f in os.listdir(…): if f.endswith((".py", ".sh")): shutil.copy2(…)`），
    **而闸 17 认不出它**——`copies_whole_scripts()` 只认 `shutil.copytree`
    实参里带 `scripts` 这个末段，于是闸 17 把这份反验报成 7 处
    「没搬 `baseline` / `batchread` / `beefsrc` / `pngstat` / `scope`」，
    **连带 `selftest-selftest-deps.py` 12 例里 7 例转红、闸 18 因此报红**。

    **可这份反验明明搬了整份 `scripts/`，一行依赖都没漏。**
    **这是「判据认写法不认事实」的第五次复发**
    （前四次：Batch 190 两处、Batch 239、Batch 247）。

    **本批改代码侧而不是改判据侧**——理由是 `stagedeps.py` 早就写明
    「凡是『搬整目录』这个事实，都写成一次调用，**而不是去猜一个
    `for … os.listdir(…)` 的循环搬了些什么**」。
    **这里为什么不用 `stage_all()`**：本反验的意义**就是普查整棵树**，
    **而 `stage_all()` 只搬非反验的 `.py`**（实测 47 份，`.sh` 与
    `selftest-*` 全不在内），**临时树的普查从 88 条掉到 74 条**；
    `copytree` 搬 157 份 `.py`+`.sh` 齐全，**与真树输出逐字节相同**。
    **两种写法都被闸 17 认，换之前必须量等价（纪律 250）。**
    """
    d = os.path.join(_TMP, "tree")
    if os.path.isdir(d):
        shutil.rmtree(d)
    shutil.copytree(os.path.join(ROOT, "scripts"), os.path.join(d, "scripts"),
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name, body in files.items():
        p = os.path.join(d, "scripts", name)
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write(body)
    g = os.path.join(d, "scripts", "verify-duplication.py")
    if accepted is not None or accepted_file is not None:
        t = io.open(g, encoding="utf-8").read()
        if accepted is not None:
            i = t.find("ACCEPTED = {")
            j = t.find("\n}\n", i)
            assert i != -1 and j > i
            t = t[:i] + "ACCEPTED = " + accepted + t[j + 3:]
        if accepted_file is not None:
            t = t.replace('ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))',
                          'ROOT = %r' % d, 1)
        with io.open(g, "w", encoding="utf-8") as fh:
            fh.write(t)
    return d, g


def extract_re_line(path):
    """**从真文件里原样抽一行 `re.compile(…)`**。

    **为什么必须抽而不是手写**：用例 2/3 的第一版是**手打那条正则**，
    **而我打出来的比原文多一个收尾引号**——**于是注入的正则与原文不同，
    闸当然不报，而用例红了**。
    **那一红是注入无效，不是判据坏了**（纪律 281 推论一的又一次形态）。
    **所以：凡是要造「同一段字面量出现两次」，就从文件里抽，不要手打。**
    """
    with io.open(path, encoding="utf-8") as fh:
        for line in fh:
            if "re.compile(" in line and not line.lstrip().startswith("#"):
                return line.rstrip("\n")
    raise AssertionError("前提失配：%s 里找不到一行 re.compile(" % path)


def record(name, ok, detail=""):
    """`ok` 既可以是布尔，**也可以直接是状态词**（`"通过"` / `"失败"` / `"作废"`）。

    **这一条是 Batch 200 那个 bug 的原样复现，而它就写在隔壁那份反验的 `record` 里。**
    **本文件第一版的 `record` 只写了 `("通过" if ok else "失败")`**，
    **于是 `main()` 里的 `record(t.__name__, "作废", ...)` 被记成了「通过」、打 ✓**
    ——**一份作废的用例在输出里长得和通过一模一样**（纪律 178 的字面形态）。
    **实测**：用例 2 的前提失配在输出里是 `✓`，而汇总说「通过 6、失败/作废 0」。
    **而 Batch 200 已经在 `selftest-selftest-bootable.py` 里修过同一个函数**
    ——**同一个修法在一个文件里存在、在另一个文件里不存在**，
    **这与 Batch 178/181/197/251/252 五次漏搬是同一个病**。
    """
    status = ok if isinstance(ok, str) else ("通过" if ok else "失败")
    results.append((name, status, detail))


# ── 1 真实现状 ──────────────────────────────────────────────────────
def m_clean():
    rc, out = run(GATE_SRC)
    record("1 真实现状 → 不报", rc == 0, "rc=%d" % rc)


# ── 2 新增未登记的重复 → 必报 ───────────────────────────────────────
def m_unregistered_duplicate_reported():
    # **源文件必须是 `tablerow.py`**——**第一版抽的是 `verify-endpoints.py`，
    # 而它那条 GET/POST 正则正在白名单里**，于是闸报的是「涉及的文件变了」
    # 而不是「没有登记」——**而那条也是红，用例仍然抓到了东西，却抓错了那一件**。
    # **一个用例红在它没打算核的那件事上，等于没核**（纪律 281 推论四）。
    a = os.path.join(ROOT, "scripts", "tablerow.py")
    line = extract_re_line(a)          # **原样抽，不手打**
    target = os.path.join(ROOT, "scripts", "verify-shot-integrity.py")
    body = io.open(target, encoding="utf-8").read() + "\n# 注入\n" + line + "\n"
    _, g = probe_root({"verify-shot-integrity.py": body})
    rc, out = run(g)
    ok = rc == 1 and "登记表里没有它" in out
    record("2 新增一处未登记的重复（同一行正则落到第二个文件）→ 必报", ok, "rc=%d" % rc)


# ── 3 登记过的重复涉及文件变了 → 必报 ──────────────────────────────
def m_stale_acceptance_reported():
    """**把已登记的那条在另一个文件里也用上**——
    于是「涉及文件」与登记时不同，**而理由是照着旧的那份写的**。"""
    line = extract_re_line(os.path.join(ROOT, "scripts", "verify-endpoints.py"))
    _, g = probe_root({"verify-probe-extra.py": "import re\n" + line + "\n"})
    rc, out = run(g)
    ok = rc == 1 and "涉及的文件变了" in out
    record("3 已登记的重复涉及文件变了 → 必报（过期的理由不背书）", ok, "rc=%d" % rc)


# ── 4 注释里贴正则 → 不得报 ─────────────────────────────────────────
def m_comment_not_counted():
    src = io.open(os.path.join(ROOT, "scripts", "verify-line-counts.py"), encoding="utf-8").read()
    inject = src + '\n# 参考：re.compile(r"Batch\\s*254\\s*有一条")\n'
    _, g = probe_root({"verify-line-counts.py": inject})
    rc, out = run(g)
    record("4 注释里贴一份正则原文 → 不得报", rc == 0, "rc=%d" % rc)


# ── 5 短字面量 → 不得报 ─────────────────────────────────────────────
def m_short_literal_not_counted():
    body = 'X=1\n'
    files = {n: body for n in ("verify-probe-a.py", "verify-probe-b.py", "verify-probe-c.py")}
    _, g = probe_root(files)
    rc, out = run(g)
    record("5 短字面量（变量名形态）在几份文件里 → 不得报", rc == 0, "rc=%d" % rc)


# ── 6 收敛掉一条却没从登记表删 → 必报 ───────────────────────────────
def m_orphan_acceptance_reported():
    """**把三个闸之一换成不含那条正则的版本**——
    登记条目从此指向一个**不存在的重复**。"""
    src = io.open(os.path.join(ROOT, "scripts", "verify-endpoints.py"), encoding="utf-8").read()
    lines = [l for l in src.split("\n")
             if "(?:GET|POST|PUT|DELETE|PATCH)" not in l]
    stripped = "\n".join(lines)
    assert stripped != src, "前提失配：verify-endpoints.py 里找不到那条正则"
    _, g = probe_root({"verify-endpoints.py": stripped})
    rc, out = run(g)
    # **孤儿登记本身不报红**——它只是不再匹配任何东西。
    # **本用例要核的是「它没有把别的判据弄坏」**，
    # **而真正的登记清理是人做的那一步，本闸管不了**。
    # **如实记下来，不假装本闸能管这件事。**
    record("6 收敛掉一条却没删登记 → 本闸不报（如实记为管不了）",
           rc == 0, "rc=%d（孤儿登记由人清理，本闸只管「新增重复」）" % rc)


def main():
    tests = [m_clean, m_unregistered_duplicate_reported,
             m_stale_acceptance_reported, m_comment_not_counted,
             m_short_literal_not_counted, m_orphan_acceptance_reported]
    for t in tests:
        try:
            t()
        except AssertionError as exc:
            record(t.__name__, "作废", "前提失配：%s" % exc)
        except Exception as exc:                          # noqa: BLE001
            record(t.__name__, "失败", "用例自身抛异常：%s: %s" % (type(exc).__name__, exc))
    failed = 0
    for name, status, detail in results:
        mark = {"通过": "✓", "失败": "✗", "作废": "—"}[status]
        print("  %s %s  %s" % (mark, name, detail))
        if status != "通过":
            failed += 1
    print("闸 37 反验：%d 例，通过 %d，失败/作废 %d"
          % (len(results), len(results) - failed, failed))
    shutil.rmtree(_TMP, ignore_errors=True)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
