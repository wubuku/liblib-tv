#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 43 `verify-rank-claims.py` 的反向验证（Batch 301）。

**九例：五支能抓 + 一支 rc 语义 + 两支不误伤 + 一条基线前提守卫**。

**为什么五支里没有一支是「新造一个坏闸」**：闸 43 判的是**手册正文里的断言**，
不是别的闸，所以它的能抓用例必须**真的去改手册内容页与快照表**——
**而那些正是方向十九（真跑期间改动手册树）要报的东西**。
所以本反验的沙箱带**整棵手册树的内容页**，注入全部发生在临时树上，
**真树一个字节都不动**（闸 18 的方向十九实测过：真跑期间真树指纹变化会报出来）。

  0) **基线前提守卫**：未注入 → 必须 rc=0 且 0 条 ✗。
     **没有它，「所有用例都红」与「判据根本没跑」在结果上长得一样。**
  1) **能抓·对照集**：把「前两名是…与…」整段删掉 → 必须 rc=1 并点名
     「没有写出它的对照集」。**这一条是 Batch 300 那处真错的形状**
     （`model-channels.md` 的「第三大」就属于这一类）。
  2) **能抓·名次**：把「体量第三大」改成「体量第二大」 → 必须报出「实测第 3」。
  3) **能抓·对照集点名**：把 `projects` 换成 `assets` → 必须报出「实测前2名是 canvas、projects」。
  4) **能抓·指针失效**：把快照表第三列的文件名改成一个不存在的 → 必须报「方向三」。
  5) **能抓·裸文件名**：把快照表第三列的 `10-tasks/create-workspace.md` 写成裸
     `create-workspace.md` → 必须报「实际在 `10-tasks/…`」——
     **这是本批在真树上真抓到的那个，不是造出来的**。
  6) **rc 语义**：把自检探针用的那段路径删掉 → 必须 **rc=2 而不是 rc=1**。
     **「读不出要比的东西」不是「查出问题」，是「根本没得查」**（纪律 101）。
  7) **不误伤**：改一个与序关系无关的措辞 → 必须 rc=0。
  8) **不误伤**：加一句**引用历史**（「原先这里写的是「体量第三大的页面目录」」）→ 必须 rc=0，
     且**「引用历史」计数必须 +1** —— **它既不该被当成活断言，也不该被静默丢掉**。

**「注入没打中」判用例失败，不判通过**：每个 `edit_one` 都断言锚点在改前改后
**各出现且只出现一次**，打不中当场抛错（纪律：漂亮的 0 是一个探针故障）。
"""

import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

from stagedeps import child_env

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE = "verify-rank-claims.py"
INTERNAL = {"AUDIT.md", "AUDIT-RULES.md", "PROGRESS.md", "FINAL-REPORT.md",
            "SOURCE_OBSERVATIONS.md"}
SKIP_DIRS = {".git", "node_modules", ".vitepress", "dist", ".agents", ".claude",
             "screenshots", "__pycache__"}
_STATES = ("通过", "失败", "作废")
results = []


def record(name, ok, detail="", state=None):
    if state is None:
        state = "通过" if ok else "失败"
    assert state in _STATES, "状态只能是 %s，收到 %r" % ("、".join(_STATES), state)
    results.append((name, state, detail))


def read(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def write(p, s):
    with io.open(p, "w", encoding="utf-8") as fh:
        fh.write(s)


def sandbox():
    """临时树 = `scripts/` 整份 + **手册树里全部 `.md`（账本除外）**。

    **为什么必须带内容页**：闸 43 判的是正文里的断言，而它的 `ROOT` 是从
    `__file__` 推出来的（`dirname(dirname(__file__))`）——**所以临时树上
    `scripts/` 的上一级就得是那棵带内容页的手册树**。

    **为什么不能用 `copytree` 搬整棵手册树**：实测 **132M**，而其中
    `node_modules` **99M** + `.vitepress` **16M** + `screenshots` **12M** = **127M**
    **与判据要读的 41 份 `.md` 毫无关系**。搬 127M 去验一份 41 文件的树，
    **代价与被验物不成比例**。

    **⚠️ `scripts/` 那一步必须一行写完**：`copytree(HERE, os.path.join(tmp,"scripts"))`
    ——拆成上一行 `dst = ...` 再 `copytree(HERE, dst)`，闸 17 的
    `copies_whole_scripts()` 只在前两个实参里找 `"scripts"`，于是报「不自洽」。
    **本文件按既有写法改自己的代码，不去动那条判据**（纪律 284：
    闸 17 有 4 份反验在用，为一处新代码去改它是更大的爆炸半径）。
    """
    tmp = tempfile.mkdtemp(prefix="rank-claims-selftest.")
    shutil.copytree(HERE, os.path.join(tmp, "scripts"),
                    ignore=shutil.ignore_patterns("__pycache__"))
    for dp, dn, fns in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for fn in sorted(fns):
            if not fn.endswith(".md") or fn in INTERNAL:
                continue
            src = os.path.join(dp, fn)
            rel = os.path.relpath(src, ROOT)
            dst = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
    return tmp


def run_in(tmp):
    # **⚠️ 闸 17「反验依赖」方向一之二首跑就把这一份判红，而它对的是一件对的事**：
    # 闸 43 的依赖闭包里 `baseline` **认 `BEEFTV_MANUAL_ROOT`**，而第一版起子进程时
    # 压根没设它——**现在凑巧对（都指向真树），而它被别人设了就整棵读错**。
    # **实测过的后果就是 Batch 259 那一族**：反验「以闸报错的形态通过，
    # 而它其实什么都没验」（纪律 178）。
    # **按既有写法改自己的代码，不动那条判据**（纪律 284）。
    env = child_env(tmp)          # **沙箱自己就是这一轮的手册根**
    r = subprocess.run([sys.executable, os.path.join(tmp, "scripts", GATE)],
                       capture_output=True, text=True, cwd=tmp, env=env)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def edit_one(path, old, new):
    """**锚点必须改前改后都存在且唯一**——打不中当场抛错，不许静默当通过。

    **唯一性由 `count(old) == 1` 保证，而「替换是否真的发生」由 `out != s` 保证。**
    第一版还加了一条 `old not in out`——**而「新串包含旧串」是插入式注入的常态**
    （用例 8 就是往句尾追加一句引用历史），**于是那条断言恒假，
    把一条本来能过的用例判成了失败**。
    **它是被收尾自检接住报出来的，不是自己发现的**——
    这正是「收尾自检必须接住一切异常」这条纪律第一次派上用场。
    """
    s = read(path)
    n = s.count(old)
    assert n == 1, "前提失配：锚点在 %s 里出现 %d 次（应为 1）" % (
        os.path.basename(path), n)
    out = s.replace(old, new, 1)
    assert out != s, "注入没有生效——判该用例失败"
    write(path, out)


def xfail(rc, out, want, case):
    """rc 必须等于 1 且输出含 `want`。"""
    if rc != 1:
        record(case, False, "期望 rc=1，实测 rc=%d；输出末尾：%s"
               % (rc, out.strip().split("\n")[-1][:110]))
        return False
    if want not in out:
        record(case, False, "rc=1 但输出里没有「%s」" % want)
        return False
    record(case, True, "rc=1 且点名「%s」" % want)
    return True


def xpass(rc, out, case, extra_ok=None):
    ok = (rc == 0 and "✗" not in out)
    if ok and extra_ok:
        ok = extra_ok(out)
    record(case, ok, "期望 rc=0 且 0 条 ✗，实测 rc=%d" % rc)


def main():
    tmp = sandbox()
    cw = os.path.join(tmp, "10-tasks", "create-workspace.md")
    ref = os.path.join(tmp, "20-reference.md")
    orig = {p: read(p) for p in (cw, ref)}

    def restore():
        for p, s in orig.items():
            write(p, s)

    # 0) 基线前提守卫
    rc, out = run_in(tmp)
    xpass(rc, out, "0 基线：未注入必须 rc=0 且 0 条 ✗")

    # 1) 能抓·对照集缺失
    restore()
    edit_one(cw, "；前两名是画布工作区 `canvas` 与项目工作区 `projects`", "")
    rc, out = run_in(tmp)
    xfail(rc, out, "没有写出它的对照集", "1 能抓·删掉对照集")

    # 2) 能抓·名次写错
    restore()
    edit_one(cw, "体量第三大的页面目录", "体量第二大的页面目录")
    rc, out = run_in(tmp)
    xfail(rc, out, "实测第 3", "2 能抓·名次写错（声称第 2）")

    # 3) 能抓·对照集点名换人
    restore()
    edit_one(cw, "项目工作区 `projects`", "素材工作区 `assets`")
    rc, out = run_in(tmp)
    xfail(rc, out, "实测前2名是 canvas、projects", "3 能抓·对照集换人")

    # 4) 能抓·指针指向不存在的文件
    restore()
    edit_one(ref, "`10-tasks/model-channels.md`「渠道设置」",
             "`10-tasks/no-such-page.md`「渠道设置」")
    rc, out = run_in(tmp)
    xfail(rc, out, "方向三", "4 能抓·快照表指针失效")

    # 5) 能抓·裸文件名（**本批在真树上真抓到的那个**）
    restore()
    edit_one(ref, "`10-tasks/create-workspace.md`「体量第三大的页面目录」",
             "`create-workspace.md`「体量第三大的页面目录」")
    rc, out = run_in(tmp)
    xfail(rc, out, "实际在", "5 能抓·快照表指针是裸文件名")

    # 6) rc 语义：探针文本被删 → rc=2 而不是 rc=1
    restore()
    edit_one(cw, "`web/src/pages/create`", "那个页面")
    rc, out = run_in(tmp)
    if rc == 2:
        record("6 rc 语义：探针没了必须 rc=2", True, "rc=2「未能核对」")
    else:
        record("6 rc 语义：探针没了必须 rc=2", False,
               "期望 rc=2，实测 rc=%d——**读不出要比的东西不是「查出问题」**"
               % rc)

    # 7) 不误伤：与序关系无关的措辞
    restore()
    edit_one(cw, "页面本身是**免费的**", "页面本身**不花钱**")
    rc, out = run_in(tmp)
    xpass(rc, out, "7 不误伤：改无关措辞")

    # 8) 不误伤：引用历史；且引用计数必须 +1
    restore()
    rc0, out0 = run_in(tmp)
    m0 = re.search(r"引用历史 \*\*(\d+)\*\* 条", out0)
    restore()
    edit_one(cw, "而本手册此前对它只有路由表里的一行。",
             "而本手册此前对它只有路由表里的一行。原先这里写的是「体量第三大的页面目录」。")
    rc, out = run_in(tmp)
    m1 = re.search(r"引用历史 \*\*(\d+)\*\* 条", out)
    if not m1:
        record("8 不误伤：引用历史既不算活断言、也不该静默丢掉", False,
               "输出里读不出「引用历史 N 条」——**静默排除的类别就是 Batch 225 "
               "踩过的那个坑**")
    elif int(m1.group(1)) != (int(m0.group(1)) + 1 if m0 else None):
        record("8 不误伤：引用历史既不算活断言、也不该静默丢掉", False,
               "引用历史计数没跟着 +1（%s → %s）"
               % (m0.group(1) if m0 else "?", m1.group(1)))
    else:
        xpass(rc, out, "8 不误伤：引用历史", extra_ok=lambda o: True)

    # ---- 收尾自检：**先打自检、再出结论**，且必须接住一切异常 ----
    restore()
    rc_end, out_end = run_in(tmp)
    assert rc_end == 0, "收尾自检：还原后必须 rc=0，实测 %d\n%s" % (rc_end, out_end[-400:])
    n = len(results)
    assert n == 9, "收尾自检：用例数应为 9，实测 %d" % n
    bad = [r for r in results if r[1] == "失败"]
    void = [r for r in results if r[1] == "作废"]
    # **合计行的形态不是随意的**：闸 18 方向十七的 `TALLY_PATS[0]` 认的是
    # `通过 N / 失败 N / 作废 N` 这个**顺序**，而第一版写成了「通过 / 作废 / 失败」，
    # **于是绿构建当场判红「解析不出合计」**。
    # **那不是「解析不到」的宽容——那正是这一条判据存在的理由**：
    # 一份反验的例数如果读不出来，**对应关系表里那一列就永远没有真值**。
    print("=" * 68)
    for name, st, detail in results:
        print("  [%s] %-46s %s" % (st, name, detail[:70]))
    print("=" * 68)
    print("闸 43 反验：通过 %d / 失败 %d / 作废 %d = %d"
          % (n - len(bad) - len(void), len(bad), len(void), n))
    print("收尾自检过了：还原后 rc=0，用例数 9，无异常外泄")
    return 1 if bad else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:               # 收尾必须接住一切异常
        print("[反验框架异常] %s: %s" % (type(exc).__name__, exc))
        print("已跑完 %d 例：" % len(results))
        for name, st, detail in results:
            print("  [%s] %s — %s" % (st, name, detail[:70]))
        sys.exit(1)