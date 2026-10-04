#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 41 `verify-empty-tree.py` 的反向验证（Batch 279）。

**四例，三支 + 一条前提守卫**：
  1) **能抓**：造一道「空树上 rc=0 且输出里有『0 个文件』」的假闸 → 闸 41 必须点名报它；
  2) **不误伤**：真实现状（干净沙箱）→ 一条都不许报；
  3) **能抓（rc 语义）**：把豁免表扩大到「全部闸」→ 闸 41 必须 rc=2
     **而不是 rc=0**——「本轮一道都没跑」与「都核过了」在退出码上必须分开（纪律 101）；
  4) **前提守卫**：闸 41 必须把自己排除在豁免表外，**否则它在空树上会无限递归**
     ——**而这一条不能用「跑一次看看」来测**：不排除的后果是**测试自己挂住**。

**鉴别力怎么来的（新闸没有「改前」可比）**：靠**同一份判据，注入红 / 不注入绿**这一对
（用例 1 与用例 2）。**只跑用例 2 是不够的**——一个什么都没抓的判据也是 rc=0。
"""
import ast
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stagedeps import child_env  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE = os.path.join(HERE, "verify-empty-tree.py")
BUILD = os.path.join(ROOT, "build-site.sh")

results = []


def read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def write(p, t):
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(t)


def record(name, ok, detail=""):
    results.append((name, "通过" if ok else "失败", detail))


def sandbox():
    """闸 41 只需要 `scripts/`——它自己建空树、自己搬运，不读手册正文。"""
    tmp = tempfile.mkdtemp(prefix="empty-tree-selftest.")
    shutil.copytree(HERE, os.path.join(tmp, "scripts"))
    shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-empty-tree.py"))
    return tmp


def run_in(tmp):
    #: **Batch 260 的同款前提**：`baseline` 让 `BEEFTV_MANUAL_ROOT` 优先于 `__file__` 推断，
    #: **不钉死它就可能整棵读错**（闸 17 方向一之二；纪律 289）。**沙箱自己就是手册根。**
    env = child_env(tmp)
    r = subprocess.run(
        [sys.executable, os.path.join(tmp, "scripts", "verify-empty-tree.py")],
        cwd=tmp, capture_output=True, text=True, env=env, timeout=600)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


#: **假闸的正文**：它**照抄 Batch 191 实测到的那句话**——
#: 「表格结构核对：0 个文件、全部表格结构一致」+ rc=0。
#: **而这不是随手编的**：那是 `verify-tables.py` 在守卫被摘掉时的**原样输出**，
#: **实测记录在纪律 314 里**。**夹具要够真，不要够真到能通过**（纪律 265）。
FAKE_GATE = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""夹具：一道在空手册树上空转却报绿的闸（Batch 279 用例 1）。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
n = len([f for f in os.listdir(os.path.dirname(HERE)) if f.endswith(".md")])
print("表格结构核对：%d 个文件、全部表格结构一致" % n)
sys.exit(0)
'''


def m_vacuous_gate_reported():
    """能抓①：造一道空转闸，闸 41 必须点名报它。"""
    tmp = sandbox()
    try:
        fake = os.path.join(tmp, "scripts", "verify-zzz-vacuous-fixture.py")
        write(fake, FAKE_GATE)
        assert os.path.isfile(fake), "前提失配：夹具没写出来"
        rc, out = run_in(tmp)
        record("1 空转闸 → 必报且点名",
               rc == 1 and "verify-zzz-vacuous-fixture.py" in out
               and "0 个文件" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def m_clean_not_reported():
    """不误伤：真实现状一条都不许报。

    **前提守卫钉在用例 4**：闸 41 必须把自己排除在豁免表外。
    **而这一条必须在跑之前钉**——**不排除的后果是本用例自己挂住**，
    **「测试挂住」与「测试红」是两种完全不同的信号，而后者才有人看**。
    """
    _self_excluded()
    tmp = sandbox()
    try:
        rc, out = run_in(tmp)
        n = 0
        m = re.search(r"体检：(\d+) 道闸在一棵空手册树上", out)
        if m:
            n = int(m.group(1))
        #: **同时核「它确实核了若干道」**——**一个因为豁免表变大而永远沉默的闸
        #: 同样会 rc=0**（纪律 300 推论四：不误伤的前提是它真的跑了）。
        #: **断言第二版（本批真踩）**：第一版写的是「输出里没有 `rc=0`」——
        #: **而闸 41 的汇总行里本来就写着 ``rc=0``**（它在解释自己查的是哪种形态），
        #: **于是这条断言恒假、而它长得像「判据误伤了」**。
        #: **正确的判别是「有没有一条以发现前缀 `空手册树体检：\`` 开头的行」**——
        #: **汇总行以「空手册树体检：N 道闸…」开头，而每一条发现以「空手册树体检：\`某闸\`` 开头**。
        found_lines = re.findall(r"^空手册树体检：`", out, re.M)
        record("2 真实现状 → 一条都不许报",
               rc == 0 and n > 0 and not found_lines,
               f"rc={rc} 核了 {n} 道 发现 {len(found_lines)} 条")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def m_all_exempt_is_rc2():
    """能抓②：豁免表扩到「全部闸」→ 必须 rc=2，**不能 rc=0**。

    **「一道都没跑」与「都核过了」在退出码上必须分开**（纪律 101）——
    **而这一支最容易写成 rc=0**：那正是 Batch 191 那个洞的形状。
    """
    tmp = sandbox()
    try:
        p = os.path.join(tmp, "scripts", "verify-empty-tree.py")
        t = read(p)
        anchor = "EXEMPT = set(emptytree.EXEMPT) | {SELF}"
        new, k = re.subn(re.escape(anchor),
                         lambda m: m.group(0) + "\nEXEMPT |= {g for g in os.listdir(HERE) "
                                                 "if g.startswith('verify-')}",
                         t, count=1)
        assert k == 1, "注入未生效：没找到 EXEMPT 那一行（k=%d）" % k
        assert new != t, "注入未生效：文件没变"
        write(p, new)
        rc, out = run_in(tmp)
        #: **断言落在判据真说的那句上**（纪律：判据输出里出现了某个词，
        #: 不等于它判了这件事）——闸 41 的原话是「本轮**一道闸都没跑**」。
        record("3 全部闸都豁免 → 必须 rc=2",
               rc == 2 and "一道闸都没跑" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _self_excluded():
    """闸 41 必须把自己排除在豁免表外，**否则它在空树上会无限递归**。

    **为什么不能用「跑一次看看」**：不排除的后果不是「红」，而是**进程不回来**。
    **与闸 18 把 `selftest-selftest-bootable.py` 硬排除同源**，
    **而那一条是代码里写死的，不是靠运行发现的。**
    """
    t = read(GATE)
    m = re.search(r"^EXEMPT = .*$", t, re.M)
    assert m, "前提失配：闸 41 里找不到 EXEMPT 那一行"
    line = m.group(0)
    assert "SELF" in line, "前提失配：豁免表那一行没有 SELF —— 闸 41 会无限递归"
    assert "emptytree.EXEMPT" in line, \
        "前提失配：豁免表没有引用 emptytree.EXEMPT —— 收敛被回退了"
    return True


def check_own_ledger_row():
    """本反验核自己在对应关系表里那一行的「例数」——**方向十七够不到它**。

    **为什么够不到**：闸 18 的方向十六跑的是反验，而本文件是**闸 41 的反验**；
    闸 41 在 `build-site.sh` 里是**闸**不是反验，**所以闸 41 的反验不在方向十七的覆盖里**
    （`run_gates` 只跑 `selftest-*`）。
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
    for t in (m_vacuous_gate_reported, m_clean_not_reported, m_all_exempt_is_rc2):
        try:
            t()
        except AssertionError as exc:
            record(t.__name__, "作废", "前提失配：%s" % exc)
        except Exception as exc:                        # noqa: BLE001
            record(t.__name__, "失败", "%s: %s" % (type(exc).__name__, exc))
    try:
        check_own_ledger_row()
    except AssertionError as exc:
        record("台账自检", "作废", str(exc))

    ok = sum(1 for _n, s, _d in results if s == "通过")
    bad = sum(1 for _n, s, _d in results if s == "失败")
    void = sum(1 for _n, s, _d in results if s == "作废")
    for name, state, detail in results:
        print("  %s %s  %s" % ({"通过": "✓", "失败": "✗", "作废": "—"}[state], name, detail))
    print("通过 %d / 失败 %d / 作废 %d" % (ok, bad, void))
    return 1 if (bad or void) else 0


if __name__ == "__main__":
    sys.exit(main())
