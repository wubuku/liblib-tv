#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二十七道闸（verify-query-params.py）的反向验证。

一道只会「通过」的闸门等于没有闸门。这里用 6 个用例成对证明它**真能抓到**（2 个）
与**不会误伤**（4 个）——后者更要紧：判据一旦把「本来正确的写法」报成问题，
它会逼着人把对的东西改成歪的。

  能抓 2 条：
    1) 手册里的参数名上游没有读点（`?readonly=1` 改成 `?readOnly=1`）
       —— 这正是**读者会照着敲、然后静默失效**的形态
    2) 手册声明的取值个数与上游字面量个数对不上（`fixture=<10 种>` → `<12 种>`）
  不误伤 3 条：
    3) **`?apiKey=…` 必须放行**——上游是 `searchParams.has("apiKey")` 而不是 `.get`。
       **本闸第一版只认 `get`，实测把它报成「上游查不到」**，而它明明被读了。
       **判据把「另一种读法」当成「没读过」，就会逼着人改对的东西。**
    4) 围栏代码块里的参数名不得被扫到（那里是示例，不是让读者敲的）
    5) 省略号形态（`?baseUrl=…`）必须正常识别
  边界 1 条：
    6) **给取值不在内联比较里的参数（`mode`）加可数声明，必须 rc=0 并说「部分核对」**
       —— **抽不出字面量只说明本方向失效，不说明手册写错了**（纪律 160：
       「未能核对」与「不一致」必须返回不同的结果）。

  基线 1 条：真实手册必须通过。

⚠️ 每条注入都用 `assert` 钉死锚点：锚点失配即判**作废**（VOID++），
**作废会让退出码非零**——Batch 225 实测过 `selftest-meta.sh` 在
「注入未命中锚点」分支漏了 `VOID++`，后果是用例静默消失、闸门在干净树上
跑绿、报告上却写着 ✓。**「用例没跑起来」和「用例通过」必须长得不一样。**

依赖模块要**连同闸脚本一起搬进临时树**（Batch 178/181/197 三次实测：
少搬一个 `baseline.py` / `batchread.py` / `beefsrc.py`，
该反验的每一例都会失败，而 build-site.sh 仍然全绿）。

⚠️ 搬运必须写成**每个依赖一行显式 `shutil.copy`、文件名写死在目标路径里**
（见 `build_tree` 的注释）：写成循环虽然搬是搬到了，闸 15 的方向一却判成「没搬」。
**修法是照既定写法改，不是放宽判据。**
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE = os.path.join(HERE, "verify-query-params.py")
# 反验要改的那一页（`20-reference.md` 是参数表所在处）
TARGET = "20-reference.md"
TARGET_REL = os.path.join(ROOT, TARGET)

PASS = FAIL = VOID = 0


def build_tree():
    """临时树：scripts/（闸 + 依赖）+ 手册正文页。**上游不必搬**——
    `beefsrc` 解析的是同级 BeefTV 仓，与手册树无关。

    ⚠️ **两个依赖必须各自一行显式 `shutil.copy`，且文件名写死在目标路径里**——
    写成 `for d in DEPS: shutil.copy(..., os.path.join(tmp, "scripts", d))`
    行为完全一样（搬是搬到了），可**闸 15 的方向一靠 `ast.unparse` 看调用点的实参**，
    循环变量里没有那个名字 → 判据判成「没搬」。
    实测本批首版就是这么写的，构建直接 FAIL。
    **修法是照 `selftest-scope.py` 的既定写法改成显式两行，不是放宽判据**——
    闸 15 存在的理由正是「依赖没搬 → 反验每例都失败，而构建仍然全绿」
    （Batch 178 实测 34 例跨 3 个批次全坏），**放宽它就是拆掉那道闸**。
    """
    tmp = tempfile.mkdtemp(prefix="beef-qp-selftest.")
    os.makedirs(os.path.join(tmp, "scripts"))
    os.makedirs(os.path.join(tmp, "10-tasks"))
    shutil.copy(os.path.join(HERE, "baseline.py"), os.path.join(tmp, "scripts", "baseline.py"))
    shutil.copy(os.path.join(HERE, "beefsrc.py"), os.path.join(tmp, "scripts", "beefsrc.py"))
    shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-query-params.py"))
    for f in ("00-quickstart.md", "20-reference.md", "30-concepts.md", "90-troubleshooting.md"):
        p = os.path.join(ROOT, f)
        if os.path.isfile(p):
            shutil.copy(p, os.path.join(tmp, f))
    for name in sorted(os.listdir(os.path.join(ROOT, "10-tasks"))):
        if name.endswith(".md"):
            shutil.copy(os.path.join(ROOT, "10-tasks", name),
                        os.path.join(tmp, "10-tasks", name))
    return tmp


def run(desc, want_sub, want_rc=1, expect_fail=True, transform=None, page=TARGET):
    """跑一次闸；`transform` 返回注入后的文本，抛 AssertionError 即作废。"""
    global PASS, FAIL, VOID
    tmp = build_tree()
    try:
        rel = page if page.startswith("10-tasks/") or page in (
            "00-quickstart.md", "20-reference.md",
            "30-concepts.md", "90-troubleshooting.md") else os.path.join("10-tasks", page)
        target = os.path.join(tmp, rel)
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

        #: **Batch 260**：`baseline.py` / `scope.py` 让 `BEEFTV_MANUAL_ROOT`
        #: **优先于 `__file__` 推断**，而本闸的 `ROOT` 是 `dirname(HERE)`——
        #: **不设它就凑巧对，设错了就整棵读错**（实测见纪律 289 / 闸 17 方向一之二）。
        #: **沙箱自己就是这一轮的手册根**。
        r = subprocess.run([sys.executable, os.path.join("scripts", "verify-query-params.py")],
                           cwd=tmp, capture_output=True, text=True,
                                   env={**os.environ, "BEEFTV_MANUAL_ROOT": tmp})
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
def t_param_typo(base):
    # **必须挑一个全库只出现一次的参数**：第一版改的是 `20-reference.md` 里的
    # `readonly=1`，而 `readonly` 在 `readonly-canvas.md` 与 `90-troubleshooting.md`
    # 里还有两处 —— 参数名仍然存在于手册，闸门当然不报。
    # **而「闸门没报」在这里有两种可能：判据失灵，或者根本没触发。**
    # `tab` 全库只出现一次（`asset-library.md` 的 `tab=history`），改掉它参数就真的消失了。
    # 原文是行内代码包住整条路径 `/assets?tab=history`，锚点要照抄那个形态
    old = "`/assets?tab=history`"
    assert old in base, "锚点未命中: %s" % old
    # 上游只有 tab，tabs 查不到 —— 读者照敲就是静默失效，没有任何报错
    return base.replace(old, "`/assets?tabs=history`", 1)


def t_count_wrong(base):
    m = re.search(r"`fixture=<(\d+) 种>`", base)
    assert m, "锚点未命中：找不到 fixture=<N 种> 的可数声明"
    return base.replace(m.group(0), "`fixture=<%d 种>`" % (int(m.group(1)) + 2), 1)


# ── 不误伤 ────────────────────────────────────────────────────
def t_apikey_kept(base):
    """**什么都不改**：手册里 `?apiKey=…` 原样保留，上游是 `has` 读法，必须放行。"""
    assert "apiKey" in base, "前提失配：手册里没有 apiKey"
    return base


def t_codeblock_param(base):
    """把一个上游没有的参数名塞进围栏代码块——那里是示例，不是让读者敲的。"""
    marker = "::: tip 「只读不写」的参数不等于「进不去」"
    assert marker in base, "锚点未命中: %s" % marker
    return base.replace(marker, "```\n?nosuchparam=1\n```\n\n" + marker, 1)


def t_ellipsis_kept(base):
    """省略号形态原样保留（`?baseUrl=…`）——第一版的正则会在这里出错。"""
    assert "baseUrl=…" in base, "前提失配：手册里没有 baseUrl=…"
    return base


# ── 边界：抽不出字面量 ≠ 手册写错 ──────────────────────────────
def t_mode_count_claim(base):
    marker = "::: tip 「只读不写」的参数不等于「进不去」"
    assert marker in base, "锚点未命中: %s" % marker
    # 给 mode 加一个可数声明。它的取值不在内联比较里（在 requestedCreationMode 里），
    # 闸门抽不出字面量 —— **此时必须说「部分核对」并放行，而不是报「手册写错了」**。
    return base.replace(marker, "全站另有 `mode=<5 种>` 取值。\n\n" + marker, 1)


def main():
    global PASS, FAIL, VOID
    print("=== 能抓 ===")
    run("1) 参数名上游没有读点（tab=history → tabs=history）", "没有", want_rc=1,
        transform=t_param_typo, page="10-tasks/asset-library.md")
    run("2) 可数声明与上游字面量个数不符（10 种 → 12 种）",
        "上游与它比较的字面量", want_rc=1, transform=t_count_wrong)

    print("=== 不误伤 ===")
    run("3) `?apiKey=…` 原样保留（上游是 has 而非 get 读法）", "个参数名在上游均有读点",
        want_rc=0, expect_fail=False, transform=t_apikey_kept)
    run("4) 围栏代码块里的参数名（示例，不是让读者敲的）", "个参数名在上游均有读点",
        want_rc=0, expect_fail=False, transform=t_codeblock_param)
    run("5) 省略号形态 `?baseUrl=…`", "个参数名在上游均有读点",
        want_rc=0, expect_fail=False, transform=t_ellipsis_kept)

    print("=== 边界：抽不出字面量 ≠ 手册写错 ===")
    run("6) mode 加可数声明（取值在 helper 里，抽不出字面量）", "本闸核不了",
        want_rc=0, expect_fail=False, transform=t_mode_count_claim)

    print("=== 基线：真实手册应当通过 ===")

    #: **Batch 260 同族第二处**（纪律 289 推论二）：这一条跑的是**真树**，
    #: **而它同样要显式指回真树**——调用者若把那个变量指向别处，
    #: **这一条就会拿一个错误的根去核真树**。**只修沙箱那一处，它仍然红。**
    r = subprocess.run([sys.executable, GATE], cwd=ROOT, capture_output=True, text=True,
                                                       env={**os.environ, "BEEFTV_MANUAL_ROOT": ROOT})
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
