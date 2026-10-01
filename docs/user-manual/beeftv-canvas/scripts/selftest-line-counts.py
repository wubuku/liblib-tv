#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第十一道闸（`verify-line-counts.py`）的反向验证。

**它为什么必须有反验**：本闸的判据是「手册声明的行数 == 上游实修行数」。
这类判据**天生容易单边**：只要有一条路径读不到，就可能整轮什么都不判——
而 `0 条不符` 会被读成「全部通过」（Batch 157 的老毛病，纪律 101）。
所以 5 例里有 **2 例专治退化**（读不到必须是 rc=2，不能是 0 也不是 1）。

  能抓 1：
    1) 声明行数改错 1 → rc=1
  未能核对 3（都必须是 rc=2，**绝不是 0**）：
    2) 整个快照小节被删 → rc=2
    3) 路径指向已改名的目录 → rc=2
    4) 路径读不到、而声明行数恰好是 0 → **仍 rc=2**（不被那个 0 骗成「相符」）
  不误伤 1：
    5) 只改「用途」列的措辞 → 必须通过

**用例 4 是这组里最该在的一条**：路径失效时实测拿不到数，
如果实现顺手返回 0，那么「声明 0 行」就会**恰好相符**——
**一个坏路径被当成一个正确答案**，而账面全绿。
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.join(HERE, "verify-line-counts.py")
BASELINE = os.path.join(HERE, "baseline.py")
MANUAL = os.path.join(os.path.dirname(HERE), "20-reference.md")

PASS = VOID = FAIL = 0

SECTION_RE = re.compile(r"###\s*上游源码行数快照")


def build(mutate=None):
    """搭一个临时的「手册根」：scripts/verify-line-counts.py + 20-reference.md。"""
    tmp = tempfile.mkdtemp(prefix="beef-linecount-selftest.")
    os.makedirs(os.path.join(tmp, "scripts"))
    # **必须连同 baseline.py 一起复制**（Batch 178 修）：
    # 自 Batch 175 起，被测闸门会 `from baseline import resolve_ref`，
    # 而本反验把闸门**单独**复制进临时目录 —— 于是临时目录里没有 baseline.py，
    # 闸门启动即 ModuleNotFoundError，**每一例都失败**。
    # 更糟的是它**静悄悄坏了三个批次**：闸门本体的 `run_gate` 仍全绿，
    # 没人跑反验就发现不了。**「被测对象多了一个依赖，反验就得跟着搬」**——
    # 而这类回归恰好是「反验能抓、构建抓不到」的那一类。
    shutil.copy(BASELINE, os.path.join(tmp, "scripts", "baseline.py"))
    shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-line-counts.py"))
    text = open(MANUAL, encoding="utf-8").read()
    if mutate:
        text = mutate(text)
    with open(os.path.join(tmp, "20-reference.md"), "w", encoding="utf-8") as fh:
        fh.write(text)
    return tmp


def run(desc, want_rc, mutate=None, want=None):
    global PASS, VOID, FAIL
    tmp = build(mutate)
    try:
        # baseline.py 用 BEEFTV_MANUAL_ROOT 定位手册根（Batch 178）：
        # 临时目录里没有 20-reference.md，不传就会抛 BaselineError。
        env={**os.environ, "BEEFTV_MANUAL_ROOT": tmp}
        r = subprocess.run([sys.executable, os.path.join("scripts", "verify-line-counts.py")],
                           cwd=tmp, env=env, capture_output=True, text=True,)
        out = r.stdout + r.stderr
        if r.returncode != want_rc:
            print("  ✗ %s：退出码 %d 期望 %d；实际：%s"
                  % (desc, r.returncode, want_rc, out.strip()[-160:]))
            FAIL += 1
        elif want and want not in out:
            print("  ✗ %s：输出里找不到 [%s]；实际：%s" % (desc, want, out.strip()[-160:]))
            FAIL += 1
        else:
            print("  ✓ %s" % desc)
            PASS += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def m_wrong_count(text):
    """把 canvas 那一行的行数改成 1（真值 17009）。"""
    new, n = re.subn(r"(\| `web/src/pages/canvas` \| )\d+( \|)", r"\g<1>1\g<2>", text, count=1)
    assert n == 1, "锚点未命中：找不到 canvas 那一行"
    assert new != text
    return new


def m_drop_section(text):
    m = SECTION_RE.search(text)
    assert m, "锚点未命中：找不到快照小节标题"
    start = m.start()
    nxt = re.search(r"\n##\s", text[m.end():])
    assert nxt, "锚点未命中：找不到小节结尾"
    return text[:start] + text[m.end() + nxt.start():]


def m_bad_path(text):
    new, n = re.subn(r"\| `web/src/pages/tasks` \|", "| `web/src/pages/renamed-away` |",
                     text, count=1)
    assert n == 1, "锚点未命中：找不到 tasks 那一行"
    return new


def m_bad_path_zero(text):
    """路径失效 + 声明行数 0 —— 用来证明「读不到」不会被那个 0 骗成相符。"""
    new = m_bad_path(text)
    new2, n = re.subn(r"(\| `web/src/pages/renamed-away` \| )\d+( \|)", r"\g<1>0\g<2>", new, count=1)
    assert n == 1, "锚点未命中：改不了那一行的行数"
    return new2


def m_remark_only(text):
    """只改「用途」列的措辞，路径与行数一律不动。"""
    new, n = re.subn(r"(\| `web/src/pages/canvas` \| \d+ \| )画布工作区是最大的页面目录( \|)",
                     r"\g<1>反验注入：只改用途措辞\g<2>", text, count=1)
    assert n == 1, "锚点未命中：找不到 canvas 那一行"
    return new


def main():
    run("1) 声明行数改错（必须报 rc=1）", 1, m_wrong_count, "与上游不符")
    run("2) 整个快照小节被删（必须 rc=2 未能核对，不是 0）", 2, m_drop_section, "未能进行")
    run("3) 路径指向已改名的目录（必须 rc=2，不是 1 也不是 0）", 2, m_bad_path, "[skip]")
    run("4) 路径失效而声明恰好是 0 行（**仍必须 rc=2**，不被 0 骗成相符）",
        2, m_bad_path_zero, "[skip]")
    run("5) 不误伤：只改「用途」列的措辞（必须通过）", 0, m_remark_only, "逐一相符")

    print("=== 结果：通过 %d / 失败 %d / 作废 %d ===" % (PASS, FAIL, VOID))
    return 1 if (FAIL or VOID) else 0


if __name__ == "__main__":
    sys.exit(main())
