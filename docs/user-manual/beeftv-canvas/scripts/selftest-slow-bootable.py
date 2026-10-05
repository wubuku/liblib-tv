#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 42 `verify-slow-bootable.py` 的反向验证（Batch 287）。

**七例，五支能抓 + 一支 rc 语义 + 一支不误伤**：

  1) **能抓（历史证据）**：把 `selftest-zero-input.py` 回退成 `675a8c7f`（Batch 286 修复前）
     → 闸 42 必须 rc=1 并点名「源码里没有合计输出点」。
     **这一条用的是真实发生过的坏状态**，不是新造的：`675a8c7f` 那份文件一个合计行都没有，
     **而它当时正是「rc=2 拒绝开跑」的那一份**——**「报不出合计」是拒绝开跑的签名**。
  2) **能抓（装体·py）**：给一份 `.py` 注入语法错 → 必须点名文件与行号；
  3) **能抓（装体·sh）**：给一份 `.sh` 注入语法错 → 必须点名文件与行号；
  4) **能抓（标签）**：从一份 `.sh` 的合计句里删掉「失败」→ 必须报「缺 失败」；
  5) **能抓（对象消失）**：把名单里那份文件删掉 → 必须报「登了却不存在」；
  6) **能抓（rc 语义）**：把闸 18 的 `SLOW = {` 改名 → 闸 42 必须 **rc=2 而不是 rc=1**。
     **「读不出要核的名单」不是「查出问题」，是「根本没得查」**（纪律 101）。
  7) **不误伤**：五份原样 → 一条都不许报，rc=0。

**为什么 7 条里 6 条是能抓**：新闸没有「改前」可比（Batch 279 立的规矩），
**只验「不误伤」等于没验**——一个什么都没抓的判据也是 rc=0。
**而第 1 条特意用真历史而不是新造**：Batch 286 那份 rc=2 的产物还在，
**一个自己造出来的坏状态只能证明判据认得自己造的那个形状**。
"""
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
GATE = os.path.join(HERE, "verify-slow-bootable.py")
ZERO = "selftest-zero-input.py"

results = []
#: **收尾自检不进 `results`**——它是收尾自检不是用例，
#: 进了就是「例数包含它自己」的自指（Batch 286 在 `selftest-zero-input.py`
#: 上刚为同一件事立过规矩，**而本批自己又差点犯**）。
notes = []


def read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def write(p, t):
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(t)


def record(name, ok, detail=""):
    results.append((name, "通过" if ok else "失败", detail))


def sandbox():
    """闸 42 只读 `scripts/`（SLOW 名单来自同目录的闸 18 源码）——不读手册正文。

    **⚠️ Batch 287 首跑被闸 17「反验依赖」判红，而它对的是一件对的事**：
    这段原本写成 `dst = os.path.join(tmp, "scripts")` 再 `copytree(HERE, dst)`，
    **而闸 17 的 `copies_whole_scripts()` 只在 `copytree` 的前两个实参里找 `"scripts"`**
    ——**拆到上一行它就看不见了，于是报「4 处不自洽」**。

    **本批按既有写法改自己的代码，不去动那条判据**：
    **它有 4 份反验在用，而为一处新代码去改一条共用判据，
    正是纪律 284 说的「新增一条问题的爆炸半径不等于它自己那一条」**。
    **而判据这一侧确实有第五处「认写法不认事实」**（`copies_whole_scripts()`
    的注释里已自认四次）——**本批据实记账，单独占一个批次去改它**，
    **不假装这一次就把它关上了**。
    """
    tmp = tempfile.mkdtemp(prefix="slow-bootable-selftest.")
    shutil.copytree(HERE, os.path.join(tmp, "scripts"),
                    ignore=shutil.ignore_patterns("__pycache__"))
    return tmp


def run_in(tmp):
    return subprocess.run([sys.executable, os.path.join(tmp, "scripts",
                                                        os.path.basename(GATE))],
                          capture_output=True, text=True, cwd=tmp)


def edit_one(path, old, new):
    """**锚点必须改前改后都存在且唯一**——否则对照组是「作废」而不是「红」
    （纪律：注入必须落在真会被执行到的位置上）。"""
    s = read(path)
    assert s.count(old) == 1, "前提失配：锚点在 %s 里出现 %d 次" % (os.path.basename(path),
                                                                 s.count(old))
    write(path, s.replace(old, new, 1))


def expect(tag, tmp, want_rc, must=(), must_not=()):
    pr = run_in(tmp)
    out = pr.stdout + pr.stderr
    ok = pr.returncode == want_rc
    detail = ""
    for w in must:
        if w not in out:
            ok, detail = False, "缺 %r" % w
    for w in must_not:
        if w in out:
            ok, detail = False, "不该出现 %r" % w
    hits = [ln.strip() for ln in out.splitlines() if ln.startswith("  · ")]
    record(tag, ok, detail or ("  ".join(hits)[:150] if hits else ""))
    shutil.rmtree(tmp, ignore_errors=True)


# ── 1) 能抓（历史证据）：回退到 Batch 286 修复前 ──────────────────────────
def m_no_total_reported():
    tmp = sandbox()
    pre = subprocess.run(
        ["git", "show", "675a8c7f:docs/user-manual/beeftv-canvas/scripts/" + ZERO],
        capture_output=True, text=True, cwd=REPO)
    assert pre.returncode == 0, "前提失配：取 675a8c7f 的旧版本失败（%s）" % pre.stderr[:120]
    write(os.path.join(tmp, "scripts", ZERO), pre.stdout)
    expect("能抓·回退到 675a8c7f（无合计行）", tmp, 1,
           must=[ZERO, "没有合计输出点"])


# ── 2) 能抓（装体·py）────────────────────────────────────────────────────
def m_py_syntax_reported():
    tmp = sandbox()
    edit_one(os.path.join(tmp, "scripts", "selftest-quote-punct.py"),
             "def main():", "def main(:")
    expect("能抓·.py 语法错", tmp, 1, must=["selftest-quote-punct.py", "语法错"])


# ── 3) 能抓（装体·sh）────────────────────────────────────────────────────
def m_sh_syntax_reported():
    tmp = sandbox()
    edit_one(os.path.join(tmp, "scripts", "selftest-unreachable.sh"),
             'echo "=== 基线：真实 origin/main 应当通过 ==="',
             'echo "=== 基线：真实 origin/main 应当通过 ==="\nif true; then')
    expect("能抓·.sh 语法错", tmp, 1, must=["selftest-unreachable.sh", "bash -n 失败"])


# ── 4) 能抓（标签）───────────────────────────────────────────────────────
def m_dropped_label_reported():
    tmp = sandbox()
    edit_one(os.path.join(tmp, "scripts", "selftest-meta.sh"),
             'echo "=== 结果：通过 $PASS / 失败 $FAIL / 作废 $VOID ==="',
             'echo "=== 结果：通过 $PASS / $FAIL / 作废 $VOID ==="')
    expect("能抓·合计删掉「失败」标签", tmp, 1, must=["selftest-meta.sh", "缺 失败"])


# ── 5) 能抓（对象消失）───────────────────────────────────────────────────
def m_missing_file_reported():
    tmp = sandbox()
    os.remove(os.path.join(tmp, "scripts", "selftest-quote-punct.py"))
    expect("能抓·名单里那份文件不在了", tmp, 1,
           must=["selftest-quote-punct.py", "文件不在"])


# ── 6) 能抓（rc 语义）：读不出名单必须是 rc=2 ────────────────────────────
def m_unreadable_slow_is_rc2():
    tmp = sandbox()
    edit_one(os.path.join(tmp, "scripts", "verify-selftest-bootable.py"),
             "SLOW = {", "SLOW_RENAMED = {")
    expect("能抓·SLOW 读不出来 → rc=2", tmp, 2, must=["前提不成立"])


# ── 7) 不误伤 ───────────────────────────────────────────────────────────
def m_clean_not_reported():
    tmp = sandbox()
    expect("不误伤·五份原样", tmp, 0,
           must=["5 份慢反验都装得上体"], must_not=["✗ 查出"])


def check_own_ledger_row():
    """本反验核自己在对应关系表里那一行的「例数」。

    **为什么够不到方向十七**：方向十六跑的是反验，**闸 42 的反验不在方向十七的覆盖里**——
    方向十七核的是「反验自己报的合计」，而它是被反验的闸 42 背后的东西（与
    `selftest-empty-tree.py` 同一形状）。
    """
    t = read(os.path.join(ROOT, "AUDIT-RULES.md"))
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
    for t in (m_no_total_reported, m_py_syntax_reported, m_sh_syntax_reported,
              m_dropped_label_reported, m_missing_file_reported,
              m_unreadable_slow_is_rc2, m_clean_not_reported):
        try:
            t()
        except AssertionError as exc:
            record(t.__name__, "作废", "前提失配：%s" % exc)
        except Exception as exc:                        # noqa: BLE001
            record(t.__name__, "失败", "%s: %s" % (type(exc).__name__, exc))
    try:
        check_own_ledger_row()
        notes.append("✓ 台账自检  对应关系表里本反验那一行的例数与本轮真跑数一致")
    except AssertionError as exc:
        notes.append("— 台账自检（**不占例名额**）  %s" % exc)

    ok = sum(1 for _n, s, _d in results if s == "通过")
    bad = sum(1 for _n, s, _d in results if s == "失败")
    void = sum(1 for _n, s, _d in results if s == "作废")
    for name, state, detail in results:
        print("  %s %s  %s" % ({"通过": "✓", "失败": "✗", "作废": "—"}[state], name, detail))
    for nline in notes:
        print("  %s" % nline)
    print("闸 42 反验：%d 例，通过 %d" % (len(results), ok))
    return 1 if (bad or void) else 0


if __name__ == "__main__":
    sys.exit(main())
