#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三十六道闸（verify-retracted-claims.py）的反向验证。

  能抓 3 条：
    1) 把一条**已撤回的说法**写进某个闸的**可执行文本** → 必须报，并点名是哪一条登记
    2) 把登记表清空 → 必须 **rc=2**（「零输入不许报绿」，纪律 156）
    3) 让某个闸脚本语法坏掉 → 必须 **rc=1**（**读不懂不等于干净**）
  不误伤 3 条：
    4) 把同一条说法写进**注释**里 → 必须放行
    5) 把同一条说法写进 **docstring** 里 → 必须放行
    6) 什么都不改（真实手册的 36 个闸脚本）→ 必须放行

**为什么 4/5 这两条不误伤用例比能抓那几条更要紧**：
本闸的全部价值在于「被撤回的说法只能活在能写清它已被推翻的地方」。
**若它连注释和 docstring 都报，整棵树会立刻被误报淹没**（实测那 17 处合法引述
有 15 处在文档语境里），**而一个天天误报的闸，下一批就会把它的结论整个忽略掉**。

**鉴别力**：把「剥掉 docstring 与整行注释」这一步摘掉再跑用例 1，
用例 1 会**报出另外十几处假命中**（实测 12 处里 10 处是假的）——
**那条判据的鉴别力来自它剥得干净，不是来自它的正则。**

⚠️ 注入一律用 `assert` 钉死锚点，锚点失配即判**作废**（VOID++），
作废让退出码非零（Batch 225 实测过漏掉 `VOID++` 的后果：
用例静默消失、闸门在干净树上跑绿、报告却写 ✓）。
本闸不读上游，临时树只需一份 `scripts/` 的副本。
"""

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE = "verify-retracted-claims.py"
#: 拿来注入的那句话——它同时是**登记表里的一条**与**真实的被撤回说法**。
#: 选它是因为它短、判别正则只匹配「断言这个说法」的行（见闸的文件头）。
LEAK = "表头行尾必须有竖线"
ROW_ID = "行尾竖线是表格行规范形态"
#: 拿来做载体的闸：**不能是本闸自己**（往自己身上注入会被登记表的豁免逻辑放过，
#: 那是另一条判据，用例 5 已经在量它）。
VICTIM = "verify-line-counts.py"

PASS = FAIL = VOID = 0


def build_tree():
    """整份 `scripts/` 拷进临时目录——本闸要读的是**闸脚本自己**。"""
    tmp = tempfile.mkdtemp(prefix="beef-rc-selftest.")
    dst = os.path.join(tmp, "scripts")
    shutil.copytree(os.path.join(ROOT, "scripts"), dst,
                    ignore=shutil.ignore_patterns("__pycache__"))
    return tmp, dst


def run(desc, want_sub="", want_rc=1, expect_fail=True, transform=None):
    global PASS, FAIL, VOID
    tmp, scripts = build_tree()
    try:
        if transform is not None:
            try:
                transform(scripts)
            except AssertionError as exc:
                print("  ✗ %s：锚点未命中，注入空转 → **本用例作废**（%s）" % (desc, exc))
                VOID += 1
                return
        r = subprocess.run([sys.executable, os.path.join("scripts", GATE), tmp],
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
            print("  ✓ %s：闸门%s [%s]（退出码 %d）"
                  % (desc, verb, want_sub or "-", r.returncode))
            PASS += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _victim_text(scripts):
    p = os.path.join(scripts, VICTIM)
    assert os.path.isfile(p), "载体闸不存在：%s" % VICTIM
    return p, io_read(p)


def io_read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def io_write(p, s):
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(s)


def t_leak_into_code(scripts):
    """把已撤回的说法写进**可执行文本**——那一句会被 print 出去给人看。

    **为什么用模块级赋值而不是插进某个函数**：第一版把 `print(...)` 塞在
    `def main(` 之后，而 `def main(` 后面往往还跟着参数（`def main(root=None):`），
    **锚点只取到前半截，新代码被插进签名中间**（Batch 241 在表格插入上踩过同一个坑）。
    报错是 `unmatched ')'`——**用例红了，可红的原因与它要测的东西无关**。
    模块级赋值既是可执行文本，又不碰任何签名。
    """
    p, text = _victim_text(scripts)
    io_write(p, text + '\n\n_LEAK_NOTE = "%s"\n' % LEAK)


def t_empty_registry(scripts):
    """把登记表清空 → 必须 rc=2。**清空一张表不会让任何东西变干净。**"""
    p = os.path.join(scripts, GATE)
    text = io_read(p)
    start = text.index("_RETRACTED = [")
    end = text.index("\n]\n", start) + 3
    io_write(p, text[:start] + "_RETRACTED = []\n" + text[end:])


def t_syntax_broken(scripts):
    """闸脚本语法坏掉 → 必须 rc=1：**读不懂不等于干净**。"""
    p, text = _victim_text(scripts)
    io_write(p, text + "\ndef (  <<< 故意写坏\n")


def t_leak_into_comment(scripts):
    """同一条说法写进**注释** → 必须放行（注释是引述被撤回说法的地方）。"""
    p, text = _victim_text(scripts)
    io_write(p, text + "\n# 曾经以为「%s」，Batch 246 实测那是假的\n" % LEAK)


def t_leak_into_docstring(scripts):
    """同一条说法写进 **docstring** → 必须放行。"""
    p, text = _victim_text(scripts)
    io_write(p, text + '\n\n\ndef _retracted_quote():\n    """%s —— 这个理由在 Batch 246 被真渲染器证伪。"""\n' % LEAK)


def main():
    global PASS, FAIL, VOID
    print("=== 能抓 ===")
    run("1) 已撤回的说法写进可执行文本（必须报，并点名是哪一条登记）",
        ROW_ID, want_rc=1, transform=t_leak_into_code)
    run("2) 登记表被清空（必须 rc=2，不能按「没有假话」通过）",
        "登记表是空的", want_rc=2, transform=t_empty_registry)
    run("3) 某个闸脚本语法坏掉（读不懂不等于干净，必须报）",
        "解析失败", want_rc=1, transform=t_syntax_broken)

    print("=== 不误伤 ===")
    run("4) 同一条说法写进注释并标明已证伪（必须放行）",
        "零处泄漏", want_rc=0, expect_fail=False, transform=t_leak_into_comment)
    run("5) 同一条说法写进 docstring（必须放行）",
        "零处泄漏", want_rc=0, expect_fail=False, transform=t_leak_into_docstring)
    run("6) 什么都不改（36 个真实闸脚本，必须放行）",
        "零处泄漏", want_rc=0, expect_fail=False)

    print("=== 基线：真实手册应当通过 ===")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", GATE)],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode == 0:
        print("  ✓ 基线：真实手册通过（%s）" % r.stdout.strip().split("\n")[0][:70])
        PASS += 1
    else:
        print("  ✗ 基线：真实手册应当通过，rc=%d：%s" % (r.returncode, r.stdout.strip()[:200]))
        FAIL += 1

    print("=== 结果：通过 %d / 失败 %d / 作废 %d ===" % (PASS, FAIL, VOID))
    return 1 if (FAIL or VOID) else 0


if __name__ == "__main__":
    sys.exit(main())
