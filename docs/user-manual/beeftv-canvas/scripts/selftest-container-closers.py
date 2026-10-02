#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二十八道闸（verify-container-closers.py）的反向验证。

这道闸的判据方向是**反的**——它只抓「多一个闭合符」，故意不管「少一个」。
所以它的反验比一般闸更关键：**两个方向都得钉住，而放行的那一侧正是本批差点搞砸的那一侧。**

  能抓 1 条：
    1) 插入一个没有容器可关的 `:::` → 必须报，且报出行号
  不误伤 3 条：
    2) **少一个闭合符（现状那两处）必须放行** —— 本批自己就是差点在这里「修」出事：
       补闭合符会让 `:::` 作为正文出现在页面上（实测），而闸门若报它「不配对」，
       就会有人照着去补。**一个会把正确的东西报成缺陷的判据，比没有判据更糟。**
    3) 容器嵌在列表项里（`- ::: warning …` / 缩进的 `  :::`）必须正常识别
       —— 第一版探针要求行首就是 `:::`，把 6 个正常页面报成不配对
    4) 围栏代码块里的 `:::` 不得被扫到

  基线 1 条：真实手册必须通过，且**必须说出少闭合那两处**（否则就是「什么都没说」）。

⚠️ 每条注入都用 `assert` 钉死锚点：锚点失配即判**作废**（VOID++），
作废会让退出码非零——Batch 225 实测过漏掉 `VOID++` 的后果：
用例静默消失、闸门在干净树上跑绿、报告上却写着 ✓。
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE = os.path.join(HERE, "verify-container-closers.py")

PASS = FAIL = VOID = 0


def build_tree():
    """临时树：`scripts/`（闸脚本）+ 全部正文页。**本闸不读上游**，不必搬任何依赖。"""
    tmp = tempfile.mkdtemp(prefix="beef-cc-selftest.")
    os.makedirs(os.path.join(tmp, "scripts"))
    os.makedirs(os.path.join(tmp, "10-tasks"))
    shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-container-closers.py"))
    for f in ("00-quickstart.md", "20-reference.md", "30-concepts.md", "90-troubleshooting.md"):
        p = os.path.join(ROOT, f)
        if os.path.isfile(p):
            shutil.copy(p, os.path.join(tmp, f))
    for name in sorted(os.listdir(os.path.join(ROOT, "10-tasks"))):
        if name.endswith(".md"):
            shutil.copy(os.path.join(ROOT, "10-tasks", name),
                        os.path.join(tmp, "10-tasks", name))
    return tmp


def run(desc, want_sub, want_rc=1, expect_fail=True, transform=None, page=None):
    global PASS, FAIL, VOID
    tmp = build_tree()
    try:
        target = os.path.join(tmp, page) if page else os.path.join(tmp, "20-reference.md")
        if transform is not None:
            base = open(target, encoding="utf-8").read()
            try:
                text = transform(base)
            except AssertionError as exc:
                print("  ✗ %s：锚点未命中，注入空转 → **本用例作废**（%s）" % (desc, exc))
                VOID += 1
                return
            with open(target, "w", encoding="utf-8") as fh:
                fh.write(text)
        r = subprocess.run([sys.executable, os.path.join("scripts", "verify-container-closers.py")],
                           cwd=tmp, capture_output=True, text=True)
        out = r.stdout + r.stderr
        if r.returncode != want_rc:
            print("  ✗ %s：退出码 %d，期望 %d；实际：" % (desc, r.returncode, want_rc))
            print("      " + out.strip()[:300].replace("\n", "\n      "))
            FAIL += 1
        elif want_sub and want_sub not in out:
            print("  ✗ %s：输出里没有 [%s]；实际：" % (desc, want_sub))
            print("      " + out.strip()[:300].replace("\n", "\n      "))
            FAIL += 1
        else:
            verb = "正确报出" if expect_fail else "**未误报**"
            print("  ✓ %s：闸门%s [%s]（退出码 %d）" % (desc, verb, want_sub, r.returncode))
            PASS += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 能抓 ──────────────────────────────────────────────────────
def t_extra_closer(base):
    m = re.search(r"^:::\s*$", base, re.M)
    assert m, "锚点未命中：找不到一整行只有 ::: 的闭合符"
    return base[:m.start()] + ":::\n" + base[m.start():]


# ── 不误伤 ────────────────────────────────────────────────────
def t_keep_missing(base):
    """**什么都不改**：保留现状里少闭合的那一处，闸门必须放行。

    这条是本闸最要紧的一条。本批自己差点在这里出事：看到「7 开 6 闭」就补了闭合符，
    重建后 diff 才发现**每一页都多出了读者可见的字面 `:::`**。
    闸门若把「少闭合」报成问题，就会有人照着去补——**判据的方向错了，危害比缺陷本身大**。
    """
    assert re.search(r"^:::\s*$", base, re.M), "前提失配：连闭合符都没有"
    return base


def t_nested_in_list(base):
    """容器嵌在列表项里：`- ::: tip X` / 缩进的 `  :::`。必须正常识别、不报多余。"""
    marker = "::: tip 「只读不写」的参数不等于「进不去」"
    assert marker in base, "锚点未命中: %s" % marker
    return base.replace(marker, "- ::: tip 嵌在列表项里的容器\n  这一行是它的内容。\n  :::\n\n" + marker, 1)


def t_fenced_colons(base):
    """围栏代码块里的 `:::` 不得被扫到（那是示例文本，不是容器）。"""
    marker = "::: tip 「只读不写」的参数不等于「进不去」"
    assert marker in base, "锚点未命中: %s" % marker
    return base.replace(marker, "```\n:::\n:::\n:::\n```\n\n" + marker, 1)


def main():
    global PASS, FAIL, VOID
    print("=== 能抓 ===")
    run("1) 多出一个没有容器可关的 :::（必须报）", "没有容器可关",
        want_rc=1, transform=t_extra_closer)

    print("=== 不误伤 ===")
    run("2) 少一个闭合符（本批差点「修」出缺陷的那一侧，必须放行）", "没有多余的闭合符",
        want_rc=0, expect_fail=False, transform=t_keep_missing)
    run("3) 容器嵌在列表项里（必须放行）", "没有多余的闭合符",
        want_rc=0, expect_fail=False, transform=t_nested_in_list)
    run("4) 围栏代码块里的 :::（必须放行）", "没有多余的闭合符",
        want_rc=0, expect_fail=False, transform=t_fenced_colons)

    print("=== 基线：真实手册应当通过，且必须说出少闭合那两处 ===")
    r = subprocess.run([sys.executable, GATE], cwd=ROOT, capture_output=True, text=True)
    out = r.stdout + r.stderr
    if r.returncode != 0:
        print("  ✗ 基线：真实手册应当通过，rc=%d：%s" % (r.returncode, out.strip()[:200]))
        FAIL += 1
    elif "少**了闭合符" not in out:
        print("  ✗ 基线：通过了，却**没有说出少闭合那两处**——"
              "「有意不管」也要说出来，否则读者会以为它没看见")
        print("      " + out.strip()[:250])
        FAIL += 1
    else:
        print("  ✓ 基线：真实手册通过，并如实说明了少闭合的两处是有意不管")
        PASS += 1

    print("=== 结果：通过 %d / 失败 %d / 作废 %d ===" % (PASS, FAIL, VOID))
    return 1 if (FAIL or VOID) else 0


if __name__ == "__main__":
    sys.exit(main())
