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
import ast
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


def read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def write(p, t):
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(t)


#: **三态，不能只有两态**——**Batch 288 实测踩到：`record(name, "作废", …)`
#: 里那个非空字符串是**真值**，于是「作废」被记成「通过」**——
#: **一个前提不成立的用例报成绿的，与它根本没跑在退出码上分不开**。
#: **所以 `ok` 只接布尔，状态由 `state` 说，不许借用 `ok` 传**。
_STATES = ("通过", "失败", "作废")


def record(name, ok, detail="", state=None):
    if state is None:
        state = "通过" if ok else "失败"
    assert state in _STATES, "状态只能是 %s，收到 %r" % ("、".join(_STATES), state)
    results.append((name, state, detail))


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


def _slow_count():
    """**慢反验的份数，从闸 18 的源码现算**（`ast`，不执行对方）。"""
    src = os.path.join(HERE, "verify-selftest-bootable.py")
    tree = ast.parse(read(src))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "SLOW" for t in node.targets):
            if isinstance(node.value, ast.Dict):
                return len(node.value.keys)
    raise AssertionError("前提失配：读不出 SLOW 名单")


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
    target = os.path.join(tmp, "scripts", ZERO)
    pre = subprocess.run(
        ["git", "show", "675a8c7f:docs/user-manual/beeftv-canvas/scripts/" + ZERO],
        capture_output=True, text=True, cwd=REPO)
    if pre.returncode == 0:
        #: **有 git 历史就用真的那一份**——**理由是它不是自己造的形状**。
        write(target, pre.stdout)
        how = "真历史 675a8c7f"
    else:
        #: **没有 git 历史（方向十六的沙箱、任何脱离仓库的运行）就退回「删掉合计行」**——
        #: **而那造出来的是同一个形状**：一份没有合计输出点的慢反验。
        #: **本条不许因为「拿不到真历史」就作废**——**作废在退出码上与失败难以分辨**，
        #: **而这里两件事要核的其实完全一样**。
        cur = read(target)
        new = re.sub(r'^\s*print\("零输入体检反验[^\n]*\n', "", cur, count=1, flags=re.M)
        assert new != cur, "前提失配：合计那行没找到，删不掉"
        assert "零输入体检反验" not in new, "前提失配：删了一行还剩合计行"
        write(target, new)
        how = "**真历史取不到（%s），已退回「删掉合计行」——同一个形状**" % (
            (pre.stderr or "").strip().splitlines() or [""])[0][:40]
    expect("能抓·%s 无合计行" % how, tmp, 1, must=[ZERO, "没有合计输出点"])


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
    # **份数必须现算，不能写死**——**Batch 288 把 SLOW 从 5 份加到 6 份，
    # 而这一例的期望串还写着「5 份」，于是它在上线首跑时红了**。
    # **一个把当前值抄进期望值的断言，在那个值变化的那一天必然红**，
    # **而它红的原因与它要核的东西毫无关系**——**白让人去查判据**。
    n = _slow_count()
    expect("不误伤·%d 份慢反验原样" % n, tmp, 0,
           must=["%d 份慢反验都装得上体" % n], must_not=["✗ 查出"])


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
            record(t.__name__, False, "前提失配：%s" % exc, state="作废")
        except Exception as exc:                        # noqa: BLE001
            record(t.__name__, False, "%s: %s" % (type(exc).__name__, exc), state="失败")
    ok = sum(1 for _n, s, _d in results if s == "通过")
    bad = sum(1 for _n, s, _d in results if s == "失败")
    void = sum(1 for _n, s, _d in results if s == "作废")
    #: **结果必须在收尾自检之前打出来**——**Batch 288 上线首跑就撞上了 Batch 209 那个坑**：
    #: 台账自检在只有 `scripts/` 的沙箱里读不到 `AUDIT-RULES.md`，
    #: 抛的是 **`FileNotFoundError` 而我只接了 `AssertionError`**，
    #: **于是已经跑完的 7 例结果一行都没打印**——
    #: **「7 例全过」与「一份报告都没交出来」在退出码上都是非 0，肉眼分不开**（Batch 209）。
    #: **所以顺序是这一处的实质，不是排版**：自检是附加项，它没有资格吞掉主结果。
    for name, state, detail in results:
        print("  %s %s  %s" % ({"通过": "✓", "失败": "✗", "作废": "—"}[state], name, detail))
    print("闸 42 反验：%d 例，通过 %d" % (len(results), ok))
    # ── 收尾自检（**不占例名额**，且接住一切异常）────────────────────────────
    try:
        check_own_ledger_row()
        print("  ✓ 台账自检（不占例名额）  对应关系表里本反验那一行的例数与本轮真跑数一致")
    except AssertionError as exc:
        print("  — 台账自检（不占例名额）  %s" % exc)
    except Exception as exc:                            # noqa: BLE001
        #: **沙箱里没有手册正文时它必须安静**——**方向十六的沙箱只搬 `scripts/`**，
        #: **而一个「读不到台账」不是「台账对不上」**（纪律 156：没核 ≠ 核过）。
        print("  — 台账自检（本轮不适用）  读不到手册正文：%s: %s"
              % (type(exc).__name__, exc))
    return 1 if (bad or void) else 0


if __name__ == "__main__":
    sys.exit(main())
