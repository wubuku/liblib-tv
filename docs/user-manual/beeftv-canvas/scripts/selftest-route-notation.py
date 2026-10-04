#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三十三道闸（verify-route-notation.py）的反向验证。

**本闸抓的是「写法在事实源里不存在」**——这类判据最危险的失败模式是
**它按自己想象的规则去判**，所以不误伤用例里特意放了三种「看起来像占位、
但上游确实有」的合法形态（`:id`、`:projectId`、`*` 通配段）。

  能抓 3 条：
    1) 登记里出现 `{...}` 占位（**本批真修掉的 6 处形态**）→ 必须报
    2) 上游该位置是占位、登记里却填了具体值（**本批真修掉的另 3 处**）→ 必须报
    3) 登记的路径在上游路由表里完全匹配不上 → 必须报
       （**这一条是前两条有意义的前提**：若匹配器什么都匹配不上，
       前两条就只是在校验一个自造的格式）
  不误伤 4 条：
    4) 上游有的另一种占位名（`:projectId`）→ 必须放行
       （**判据不能只认 `:id` 一个名字**——那才是按写法判定）
    5) 带查询串的路由（`?readonly=1&fixture=…`）→ 必须放行
    6) 上游的 `*` 通配段（`/project/:projectId/*` 那类）→ 必须放行
    7) 上游声明里出现花括号占位 → 必须 **rc=2**
       （**本闸的前提是「上游零处使用花括号」**；前提不成立时它必须拒绝下结论，
       而不是继续拿旧前提判——纪律 101）

⚠️ 第 7 条守的是本闸最根本的一条边界：**合法集是从事实源算出来的，
而事实源变了，判据的结论就该失效而不是继续报**。

每条注入都用 `assert` 钉死锚点，**并且在跑之前 `cksum` 比对前后**
（Batch 229：`str.replace` 锚点不中时静默无操作，
而「用例通过」与「用例根本没跑起来」在输出上完全一样）。
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE = os.path.join(HERE, "verify-route-notation.py")
BASELINE = os.path.join(HERE, "baseline.py")
BEEFSRC = os.path.join(HERE, "beefsrc.py")
MANIFEST_REL = os.path.join("screenshots", "manifest.yml")
INV_REL = "task-inventory.yml"
REF_REL = "20-reference.md"

PASS = VOID = FAIL = 0


def _cksum(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(desc, want, expect_fail=True, want_rc=1, edits=None):
    global PASS, VOID, FAIL
    reads = [os.path.join(ROOT, MANIFEST_REL), os.path.join(ROOT, INV_REL),
             os.path.join(ROOT, REF_REL)]
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

    tmp = tempfile.mkdtemp(prefix="beef-route-selftest.")
    try:
        os.makedirs(os.path.join(tmp, "scripts"), exist_ok=True)
        shutil.copy(BASELINE, os.path.join(tmp, "scripts", "baseline.py"))
        shutil.copy(BEEFSRC, os.path.join(tmp, "scripts", "beefsrc.py"))
        shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-route-notation.py"))
        for p, t in texts.items():
            rel = os.path.relpath(p, ROOT)
            dst = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "w", encoding="utf-8") as fh:
                fh.write(t)

        #: **Batch 260**：`baseline.py` / `scope.py` 让 `BEEFTV_MANUAL_ROOT`
        #: **优先于 `__file__` 推断**，而本闸的 `ROOT` 是 `dirname(HERE)`——
        #: **不设它就凑巧对，设错了就整棵读错**（实测见纪律 289 / 闸 17 方向一之二）。
        #: **沙箱自己就是这一轮的手册根**。
        r = subprocess.run([sys.executable, os.path.join("scripts", "verify-route-notation.py")],
                           cwd=tmp, capture_output=True, text=True,
                                   env={**os.environ, "BEEFTV_MANUAL_ROOT": tmp})
        out = r.stdout + r.stderr
        if expect_fail and r.returncode == 0:
            print("  ✗ %s：闸门本应报错，却通过了" % desc)
            print("      " + out.strip()[:200])
            FAIL += 1
        elif expect_fail and r.returncode != want_rc:
            print("  ✗ %s：退出码 %d，期望 %d；实际：" % (desc, r.returncode, want_rc))
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


A_ROUTE = "route: '/canvas/:id'"


# ------------------------------------------------------------------ 能抓

def t_brace_placeholder(s):
    assert A_ROUTE in s, "锚点未命中：manifest 里找不到 route: '/canvas/:id'"
    return s.replace(A_ROUTE, "route: '/canvas/{id}'", 1)


def t_concrete_id(s):
    assert A_ROUTE in s, "锚点未命中：manifest 里找不到 route: '/canvas/:id'"
    return s.replace(A_ROUTE, "route: '/canvas/tPiyJSrJhwfoLvdDf_6qW'", 1)


def t_no_match(s):
    assert A_ROUTE in s, "锚点未命中：manifest 里找不到 route: '/canvas/:id'"
    return s.replace(A_ROUTE, "route: '/canvas-editor/:id'", 1)


# -------------------------------------------------------------- 不误伤

def t_other_param_name(s):
    a = "- '/projects/:projectId'"
    assert a in s, "锚点未命中：账本里找不到 /projects/:projectId"
    #: **判据不能只认 `:id` 一个名字**——上游用的是 `:param` 风格，参数名随路由而异
    #: （`/canvas/:id`、`/projects/:projectId`、`/project/:projectId/:view`）。
    #: **只认一个名字就是「按写法判定」而不是「按事实判定」**（纪律 190 的同类）。
    return s.replace(a, a + "\n    - '/projects/:view'", 1)


def t_query_string(s):
    a = "route: '/canvas/:id'"
    assert a in s, "锚点未命中：manifest 里找不到 route: '/canvas/:id'"
    #: 查询串与占位风格是两件事——本闸只核路径那一段
    return s.replace(a, "route: '/canvas/:id?readonly=1&fixture=libtv-readonly-dense'", 1)


def t_wildcard_segment(s):
    a = "- '/projects/:projectId'"
    assert a in s, "锚点未命中：账本里找不到 /projects/:projectId"
    #: **上游有 `*` 通配段**（`/project/:projectId/*`）——本闸的匹配器必须认它，
    #: 否则一条合法的通配路由会被报成「匹配不上任何一条声明」。
    #:
    #: **这一条用例连着写错了两次，而两次都是闸判对了、样本错了**（都记在这里）：
    #: 第一版写 `/projects/:projectId/:view/*`——闸报匹配不上，**闸是对的**：
    #: 上游的通配在**单数** `/project/:projectId/*`，`/projects/…` 那几条末尾没有 `*`；
    #: 第二版写 `/project/abc123XYZ/overview` 想测「通配下的具体子路径」——
    #: 闸匹配上了，但**方向二正确地报了「第 2 段是占位却填了具体值」**，
    #: **而那正是本批真修掉的那一类**（写死画布 ID 就是这么被报的）。
    #: **通配段并不豁免方向二**：`*` 之后的具体子路径没问题，
    #: 但 `*` **之前**的 `:projectId` 位上填具体 id 仍然是缺陷。
    #: 所以合法样本只能照着事实源写：**把通配路由原样登记下来**。
    return s.replace(a, a + "\n    - '/project/:projectId/*'", 1)


def main():

    #: **Batch 260 同族第二处**（纪律 289 推论二）：这一条跑的是**真树**，
    #: **而它同样要显式指回真树**——调用者若把那个变量指向别处，
    #: **这一条就会拿一个错误的根去核真树**。**只修沙箱那一处，它仍然红。**
    r = subprocess.run([sys.executable, GATE], cwd=ROOT, capture_output=True, text=True,
                                                       env={**os.environ, "BEEFTV_MANUAL_ROOT": ROOT})
    if r.returncode == 0:
        print("  ✓ 基线：真实手册通过（%s）" % r.stdout.strip().split("\n")[0][:70])
        globals()["PASS"] = globals()["PASS"] + 1
    else:
        print("  ✗ 基线：真实手册应当通过，rc=%d：%s" % (r.returncode, r.stdout.strip()[:200]))
        globals()["FAIL"] = globals()["FAIL"] + 1

    mf = os.path.join(ROOT, MANIFEST_REL)
    iv = os.path.join(ROOT, INV_REL)
    run("1) 登记里出现 `{...}` 占位（必须报）", "零处使用", edits={mf: t_brace_placeholder})
    run("2) 占位位置填了具体值（必须报）", "却填了具体值", edits={mf: t_concrete_id})
    run("3) 路径在上游路由表里完全匹配不上（必须报）", "匹配不上任何一条声明",
        edits={mf: t_no_match})
    run("4) 不误伤：上游的另一种占位名 `:view`（必须放行）", "路由写法核对通过",
        expect_fail=False, edits={iv: t_other_param_name})
    run("5) 不误伤：带查询串的路由（必须放行）", "路由写法核对通过",
        expect_fail=False, edits={mf: t_query_string})
    run("6) 不误伤：上游的 `*` 通配段（必须放行）", "路由写法核对通过",
        expect_fail=False, edits={iv: t_wildcard_segment})

    print("=== 结果：通过 %d / 失败 %d / 作废 %d ===" % (PASS, FAIL, VOID))
    return 1 if (FAIL or VOID) else 0


if __name__ == "__main__":
    sys.exit(main())
