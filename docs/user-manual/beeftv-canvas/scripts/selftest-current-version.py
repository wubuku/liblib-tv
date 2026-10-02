#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三十一道闸（verify-current-version.py）的反向验证。

**本闸的覆盖面只有一种形态、且全库只有 1 处命中**，所以反验的重点不是
「它抓不抓得到那 1 处」，而是**「它会不会去抓它不该抓的那几十处」**——
手册里带版本号的括注约 50 处，绝大多数是**功能引入版本**或**证据出处**。
**这一族判据的失败模式几乎必然是过宽**，而不是过窄。

  能抓 3 条：
    1) 把「当前 v1.6.22」改成过期版本 → 必须报「没有指向取证基线」
    2) 另一页里新增一处「当前 vX.Y.Z」（证明它不是只认那一个文件）
    3) 基线升版后不改正文（把注入的版本设成比基线新的形态）→ 必须报
  不误伤 4 条：
    4) 功能引入版本：`（v1.6.7 起解禁）` → 必须放行
    5) 证据出处：`（v1.6.14 实测）` → 必须放行
    6) **不带版本号的「当前版本」**（`在当前版本不存在`，全库几十处）→ 必须放行
    7) 被 `srcExclude` 排除的内部资料里写「当前 v1.6.16」→ 必须放行
       （**判据的输入范围必须等于发布范围**，闸 22 纪律 191；内部资料读者看不到）

⚠️ 第 7 条守的是本闸最容易犯的一个错：为了「查得全」把 `SOURCE_OBSERVATIONS.md`
也扫进去。**那两份文件被 `config.mjs` 的 `srcExclude` 排除、根本不会出现在站点上**，
而它们恰恰留着**故意不改**的过期记录（那是按批次留下的证据，闸 22 记的就是这件事）。

每条注入都用 `assert` 钉死锚点，**并且在跑之前 `cksum` 比对前后**：
`str.replace` 锚点不中时**静默无操作**，而「用例通过」与「用例什么都没做」
在输出上完全一样（Batch 229 的 6 个注入用例里 3 个在空跑）。
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE = os.path.join(HERE, "verify-current-version.py")
BASELINE = os.path.join(HERE, "baseline.py")
BEEFSRC = os.path.join(HERE, "beefsrc.py")
SCOPE = os.path.join(HERE, "scope.py")
CONFIG_DIR = ".vitepress"
QUICKSTART = os.path.join("00-quickstart.md")
INTERNAL = "SOURCE_OBSERVATIONS.md"

PASS = VOID = FAIL = 0


def _cksum(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _snapshot(dst):
    """把被测闸门真正要读的东西按同样的相对路径搬进沙箱。"""
    os.makedirs(os.path.join(dst, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(dst, CONFIG_DIR), exist_ok=True)
    #: 闸门 import `scope` 与 `baseline`，而 `baseline` 自己 `import beefsrc`——
    #: 少搬任何一个都会 ModuleNotFoundError，**每一例都失败而 build-site.sh 仍全绿**（闸 17 的由来）。
    shutil.copy(BASELINE, os.path.join(dst, "scripts", "baseline.py"))
    shutil.copy(BEEFSRC, os.path.join(dst, "scripts", "beefsrc.py"))
    shutil.copy(SCOPE, os.path.join(dst, "scripts", "scope.py"))
    shutil.copy(GATE, os.path.join(dst, "scripts", "verify-current-version.py"))
    shutil.copy(os.path.join(ROOT, CONFIG_DIR, "config.mjs"),
                os.path.join(dst, CONFIG_DIR, "config.mjs"))
    #: **`20-reference.md` 必须搬**：基线是从它的「取证基线」小节**读出来**的（纪律 107），
    #: 少搬它则闸门连「当前该是哪个版本」都不知道，rc=2 而每一例都判失败。
    shutil.copy(os.path.join(ROOT, "20-reference.md"),
                os.path.join(dst, "20-reference.md"))


def run(desc, want, expect_fail=True, edits=None):
    """edits: {相对路径: 函数(原文字符串) -> 新文字符串}"""
    global PASS, VOID, FAIL
    reads = [os.path.join(ROOT, "20-reference.md"),
             os.path.join(ROOT, QUICKSTART),
             os.path.join(ROOT, INTERNAL)]
    base = {p: open(p, encoding="utf-8").read() for p in reads}
    texts = dict(base)

    if edits:
        try:
            for path, fn in edits.items():
                texts[path] = fn(texts[path])
        except AssertionError as exc:
            print("  ✗ %s：锚点未命中，注入空转 → **本用例作废**（%s）" % (desc, exc))
            VOID += 1
            return
        changed = [p for p in edits if _cksum(texts[p]) != _cksum(base[p])]
        if not changed:
            print("  ✗ %s：注入前后内容逐字相同 → **本用例作废**（静默空转）" % desc)
            VOID += 1
            return

    tmp = tempfile.mkdtemp(prefix="beef-curver-selftest.")
    try:
        _snapshot(tmp)
        for p, t in texts.items():
            dst = os.path.join(tmp, os.path.relpath(p, ROOT))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "w", encoding="utf-8") as fh:
                fh.write(t)
        r = subprocess.run([sys.executable, os.path.join("scripts", "verify-current-version.py")],
                           cwd=tmp, capture_output=True, text=True)
        out = r.stdout + r.stderr
        if expect_fail and r.returncode == 0:
            print("  ✗ %s：闸门本应报错，却通过了" % desc)
            print("      " + out.strip()[:200])
            FAIL += 1
        elif expect_fail and r.returncode != 1:
            print("  ✗ %s：退出码 %d，期望 1；实际：" % (desc, r.returncode))
            print("      " + out.strip()[:200])
            FAIL += 1
        elif expect_fail and want not in out:
            print("  ✗ %s：报错了但不是 [%s]；实际：" % (desc, want))
            print("      " + out.strip()[:200])
            FAIL += 1
        elif not expect_fail and r.returncode != 0:
            print("  ✗ %s：本应放行却报错（误伤，rc=%d）：%s"
                  % (desc, r.returncode, out.strip()[:200]))
            FAIL += 1
        else:
            print("  ✓ %s" % desc)
            PASS += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ------------------------------------------------------------------ 能抓

def t_stale_current(s):
    a = "但**当前 v1.6.22 客户端里打不开**"
    assert a in s, "锚点未命中：找不到「当前 v1.6.22 客户端里打不开」"
    return s.replace(a, "但**当前 v1.6.16 客户端里打不开**", 1)


def t_new_page_claim(s):
    a = "## 本版没有的功能（别白找）"
    assert a in s, "锚点未命中：找不到「## 本版没有的功能（别白找）」"
    return s.replace(a, a + "\n\n反验注入：这一节说**当前 v1.6.20 客户端**里也没有那个入口。", 1)


def t_future_version(s):
    a = "但**当前 v1.6.22 客户端里打不开**"
    assert a in s, "锚点未命中：找不到「当前 v1.6.22 客户端里打不开」"
    #: **比基线更新的写法也必须报**——只查「比基线旧」的话，
    #: 写了一个还不存在的版本反而会放行，**而那比过期更糟**（读者按它去等一个没发布的版本）。
    return s.replace(a, "但**当前 v1.9.9 客户端里打不开**", 1)


# -------------------------------------------------------------- 不误伤

def t_feature_intro_version(s):
    a = "**可用的本地推理入口是「深度动作捕捉」**"
    assert a not in s, "前置条件不符：这段文字不在 quickstart 上"
    return s + "\n（v1.6.7 起解禁）\n"


def t_evidence_version(s):
    a = "但**当前 v1.6.22 客户端里打不开**"
    assert a in s, "锚点未命中：找不到「当前 v1.6.22 客户端里打不开」"
    #: 证据出处与功能引入版本**都不带「当前」**，判据不该管它们——
    #: 而它们恰恰是全库约 50 处带版本号括注里的绝大多数。
    return s.replace(a, a + "（v1.6.14 实测）", 1)


def t_current_without_version(s):
    a = "但**当前 v1.6.22 客户端里打不开**"
    assert a in s, "锚点未命中：找不到「当前 v1.6.22 客户端里打不开」"
    #: **全库几十处「在当前版本不存在」都不带版本号**——
    #: 它们指的是「读者手上那一个」，不是基线，**判据一抓就是误伤**。
    return s.replace(a, "但**在当前版本**里打不开", 1)


def t_internal_doc_stale(s):
    a = "## v1.6.16 取证对象说明（Batch 130 起持续适用）"
    assert a in s, "锚点未命中：找不到 SOURCE_OBSERVATIONS 的那节标题"
    #: **内部资料被 `srcExclude` 排除、读者看不到，而它保留的过期记录是有意的**
    #: （那是按批次留下的证据）。判据若把它扫进来就会误报——**输入范围必须等于发布范围**。
    return s.replace(a, a + "\n\n反验注入：这一节说**当前 v1.6.16 客户端**的界面表现。", 1)


def main():
    r = subprocess.run([sys.executable, GATE], cwd=ROOT, capture_output=True, text=True)
    if r.returncode == 0:
        print("  ✓ 基线：真实手册通过（%s）" % r.stdout.strip().split("\n")[0][:70])
        globals()["PASS"] = globals()["PASS"] + 1
    else:
        print("  ✗ 基线：真实手册应当通过，rc=%d：%s" % (r.returncode, r.stdout.strip()[:200]))
        globals()["FAIL"] = globals()["FAIL"] + 1

    q = os.path.join(ROOT, QUICKSTART)
    run("1) 「当前」指向过期版本（必须报）", "没有指向取证基线",
        edits={q: t_stale_current})
    run("2) 另一处新增「当前 vX.Y.Z」（必须报，证明不是只认一个文件）", "没有指向取证基线",
        edits={q: t_new_page_claim})
    run("3) 「当前」指向比基线更新的版本（必须报，不能只查「更旧」）", "没有指向取证基线",
        edits={q: t_future_version})
    run("4) 不误伤：功能引入版本「（v1.6.7 起解禁）」（必须放行）", "「当前版本」核对通过",
        expect_fail=False, edits={q: t_feature_intro_version})
    run("5) 不误伤：证据出处「（v1.6.14 实测）」（必须放行）", "「当前版本」核对通过",
        expect_fail=False, edits={q: t_evidence_version})
    run("6) 不误伤：不带版本号的「在当前版本」（必须放行）", "「当前版本」核对通过",
        expect_fail=False, edits={q: t_current_without_version})
    run("7) 不误伤：被排除的内部资料里写「当前 v1.6.16」（必须放行）", "「当前版本」核对通过",
        expect_fail=False, edits={os.path.join(ROOT, INTERNAL): t_internal_doc_stale})

    print("=== 结果：通过 %d / 失败 %d / 作废 %d ===" % (PASS, FAIL, VOID))
    return 1 if (FAIL or VOID) else 0


if __name__ == "__main__":
    sys.exit(main())
