#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""副本树绿构建的**承重核对**——一份实现，带自检与自测。

**为什么它该进仓库，而不是每批手抄一遍**：
Batch 311–320 的绿构建 wrapper 里各有一组「搭完树当场核对」，
**十批十份、每份手抄**。而这一组核对恰恰是**这个项目里抓到缺陷最多的代码**：
它先后抓到过非幂等编辑留下的重复插入、表格被劈成第 5 格、批次行漏叠加、
闸清单表行序错位、方向计数悄悄变成 0……

**而它自己的缺陷率是全项目最高的**。2026-10-07 一天之内，
**同一批里三条承重核对有两条第一次写就写错了**：
  ① 「副本树有没有第 50/51 例」用了 `grep -q "^50)"`，
     而用例行以 `run_file_case "50)` 开头 —— **它在用例明明在文件里（683/687 行）
     的情况下报「没有」，把构建拦下了**。**拦下总比放过好，但一条恒假的承重核对
     比没有更坏**：它会把人训练成「这条总报红，忽略它」。
  ② 「本批改了哪些文件都叠了吗」写成 bash 内嵌 heredoc，
     **`${FILES[@]}` 在那种位置只传得进去第一个元素**，
     **而报错长到看不出是哪一条对不上**——离真实原因太远的诊断比没有诊断更费时间。
  ③ 第一版把「KNOWN_WIP 里当前没有改动的条目」这条提示**说反了**：
     它遍历的是「在 `changed` 里、且不在 `mine` 里」的条目，
     **也就是「确实有改动」的那些**，却打印「当前没有改动（同事可能已经提交/撤销）」。
     **说反的那一半恰恰是排除名单是否仍然有效这条信息**，
     **而排除名单一旦悄悄过期，下一批会把同事的 WIP 当成「本批漏叠加」而报错**。

**所以本脚本照纪律 355 的形状写**：形态归一化是**一个**函数、
**内部当场用已知答案自检**；整套核对另有一个 `--self-test`
（**一正一负两个已知答案样本**，纪律 350：判别式没被两个样本验过就只是写法）。

**它不检查什么（如实说明）**：
  · **不跑构建**（那是 wrapper 的事，4 分钟）；
  · **不核批次专用的断言**（「副本树的方向十三必须报 34/10」那种每批不同）——
    **把它们塞进来会让这个脚本每批都要改，于是它又回到「手抄」的状态**。
"""
import argparse
import os
import subprocess
import sys

REPO_DEFAULT = "/Users/yangjiefeng/Documents/wubuku/liblib-tv"


# ── 形态归一化：一个函数 + 当场自检（纪律 355） ──────────────────────────
def norm_rel(path):
    """任意一种写法 → 相对仓库根的规范路径（无 `./`、无重复斜线、无尾斜线）。"""
    b = path.strip().replace("\\", "/")
    while b.startswith("./"):
        b = b[2:]
    while "//" in b:
        b = b.replace("//", "/")
    b = b.rstrip("/")
    assert b, "空路径"
    return b


#: **当场自检**：一组已知答案（**这四个是 2026-10-07 当天真的栽过的形态**）。
#: **它不是仪式**——本函数的第一版把自检写成 `norm_rel._probe(...)`，
#: **而函数对象上的属性在模块里取不到，当场 `AttributeError`**；
#: 写成下面这几行 assert 之后，它才真的在验「变换本身」而不是在验「属性存在」。
for _raw, _want in [
    ("./docs/x.md", "docs/x.md"),
    ("docs//x.md", "docs/x.md"),
    ("docs/sub/", "docs/sub"),
    ("  docs/x.md  ", "docs/x.md"),
]:
    _got = norm_rel(_raw)
    assert _got == _want, ("归一化自检失败", _raw, _got, _want)
#: **幂等**：归一化两次必须与一次相同
assert norm_rel(norm_rel("./a//b/")) == "a/b"
print("形态归一化自检：4 个已知答案 + 幂等，全过")


def read_list(path):
    with open(path, encoding="utf-8") as fh:
        return [norm_rel(ln) for ln in fh if ln.strip()]


def git_changed(repo, sub):
    """`git status --porcelain -- <sub>` → **{规范相对路径: 状态码}**。

    **porcelain 格式是「两位状态 + 一个空格 + 路径」**，
    而第一版按前 3 字符切之后又对 `??` 行**再切一次**，把首字符也切掉了
    （`ocs/user-manual/…`）——**当时那份报错没有任何一处指向真正的原因**。

    **返回状态码而不是只返回路径，是因为下面两条检查必须分开**：
      · ` M` = **已入库**但被改 → **副本树里应该有** HEAD 版（那正是我们要的隔离）；
      · `??` = **未跟踪**（新文件） → **副本树里绝不该有**，因为它没进过任何提交。
    **第二版把两者混成一条「副本树里出现了同事的文件」，于是在真仓库上立刻误报 3 处**
    （`10-tasks/README.md` 等三个已入库文件）——
    **而那三个文件恰恰是必须出现在副本树里的**。
    """
    out = subprocess.run(["git", "-C", repo, "status", "--porcelain", "--", sub],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError("git status 失败：%s" % out.stderr.strip())
    paths = {}
    for line in out.stdout.split("\n"):
        if len(line) < 4:
            continue
        status = line[:2].strip()
        p = line[3:].strip()
        if p.startswith('"') and p.endswith('"'):
            p = p[1:-1]
        paths[norm_rel(p)] = status
    return paths


def run_gate(out_dir, sub, script):
    r = subprocess.run([sys.executable, "scripts/" + script], cwd=os.path.join(out_dir, sub),
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def preflight(repo, sub, out, files, wip, run_tables_gate=True):
    """返回 (问题列表, 信息行列表)。**信息行与问题行必须分开**——
    2026-10-07 第一版把两者混在一个列表里，于是「说反」的错误没人当场发现。"""
    problems, notes = [], []
    mine = set(files)
    wip_set = set(wip)
    changed = git_changed(repo, sub)
    changed_set = set(changed)

    # ① 漏叠加：本批改了却不在 FILES 里（减去显式排除的同事 WIP）
    missing = sorted(p for p in changed_set if p not in mine and p not in wip_set)
    for p in missing:
        problems.append("本批改了却不在 FILES 里 → 副本树会跑上一批的版本：%s" % p)
    if not missing:
        notes.append("工作区 %d 处改动全部落在 FILES（%d 项）或 KNOWN_WIP（%d 项）里"
                     % (len(changed), len(mine), len(wip_set)))

    # ② KNOWN_WIP 的有效性——**方向必须对**：在 `changed` 里的是「仍然有改动」，
    #    不在的才是「同事可能已经提交/撤销」
    still_dirty = sorted(wip_set & changed_set)
    stale = sorted(wip_set - changed_set)
    for p in still_dirty:
        how = "未跟踪的新文件" if changed[p] == "??" else "已入库文件被改"
        notes.append("KNOWN_WIP 生效中：%s 仍是同事的%s（已排除，不算漏叠加）"
                     % (p, how))
    for p in stale:
        notes.append("⚠ KNOWN_WIP 条目 %s 当前**没有**改动——同事可能已提交/撤销。"
                     "**排除名单一旦过期，下一批会把它当成「本批漏叠加」而报错**" % p)

    # ③ 逐文件：副本树必须逐字节等于工作区
    for p in sorted(mine):
        src, dst = os.path.join(repo, p), os.path.join(out, p)
        if not os.path.exists(dst):
            problems.append("副本树里没有 %s" % p)
            continue
        a = subprocess.run(["cmp", "-s", src, dst]).returncode
        if a != 0:
            problems.append("副本树与工作区的 %s 不一致" % p)

    # ④ 副本树里绝不能出现同事的**未跟踪**文件
    #    （**已入库但被改的文件，副本树里必须有 HEAD 版**——那正是隔离的目的。
    #     第二版没分这两者，在真仓库上立刻误报 3 处。）
    for p in sorted(wip_set & changed_set):
        if changed[p] != "??":
            continue
        if os.path.exists(os.path.join(out, p)):
            problems.append("副本树里出现了同事的**未跟踪**文件 %s —— 叠加写错了" % p)

    # ⑤ 闸 8（表格结构）：0.5 秒，而它在本项目里至少抓到过三处我自己写坏的表格
    if run_tables_gate:
        rc, out_text = run_gate(out, sub, "verify-tables.py")
        if rc != 0:
            problems.append("副本树上闸 8 rc=%d：%s" % (rc, out_text.strip().split("\n")[0]))
        else:
            notes.append("副本树上闸 8 通过（表格结构）")

    return problems, notes


# ── 自测：一正一负两个已知答案样本（纪律 350） ──────────────────────────
def self_test():
    """**不碰真仓库**：在临时目录里造两棵极小的树。

    负样本 = FILES 覆盖全部改动 → 必须 0 问题；
    正样本 = 漏掉一个文件 + 同事 WIP 过期 → 必须恰好报出那两个问题。
    **两个样本都有已知答案，这一组判别式才算被验过。**
    """
    import tempfile
    import shutil
    base = tempfile.mkdtemp(prefix="preflight-selftest.")
    repo, sub = os.path.join(base, "repo"), "sub"
    os.makedirs(os.path.join(repo, sub, "scripts"))
    subprocess.run(["git", "-C", repo, "init", "-q"], check=True)
    subprocess.run(["git", "-C", repo, "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", repo, "config", "user.name", "t"], check=True)
    # 一个被跟踪的闸脚本（闸 8 要能跑）
    with open(os.path.join(repo, sub, "scripts", "verify-tables.py"), "w",
              encoding="utf-8") as fh:
        fh.write("import sys\nprint('ok')\nsys.exit(0)\n")
    # 两个本批文件（会被改脏）
    for name in ("mine-a.md", "mine-b.md"):
        with open(os.path.join(repo, sub, name), "w", encoding="utf-8") as fh:
            fh.write("x\n")
    #: **已入库但被同事改了的文件**——它在 `git archive HEAD` 里**本来就该有**。
    #: **必须有这个夹具**，否则判据④（副本树里绝不能出现未跟踪文件）
    #: 就没有「不误伤」的那一半：**2026-10-07 真仓库上正是这条误报了 3 处**
    #: （`10-tasks/README.md` 等三个已入库文件），而**那三个恰恰必须出现在副本树里**。
    with open(os.path.join(repo, sub, "wip-tracked.md"), "w", encoding="utf-8") as fh:
        fh.write("t\n")
    subprocess.run(["git", "-C", repo, "add", "-A"], check=True)
    subprocess.run(["git", "-C", repo, "commit", "-qm", "base"], check=True)
    # **同事的未跟踪 WIP 必须在提交之后建**——
    # 第一版把它写在 commit 之前，于是它进了 `HEAD`、`git archive` 也带上它，
    # **副本树里就「出现了同事的文件」**，负样本当场判失败。
    # **而那个失败是对的**：判据抓到了「副本树里混进了不该有的文件」，
    # **错的是夹具的搭法**——**这正是自测该有的样子：负样本失败时，
    # 先怀疑夹具，再怀疑判据**（纪律 344）。
    with open(os.path.join(repo, sub, "wip.md"), "w", encoding="utf-8") as fh:
        fh.write("w\n")
    # wip-tracked.md 被改脏 ⇒ 状态是 ` M`（**已入库**），副本树里**应当有** HEAD 版
    with open(os.path.join(repo, sub, "wip-tracked.md"), "w", encoding="utf-8") as fh:
        fh.write("t-edited\n")
    # 把 mine-b 改脏
    with open(os.path.join(repo, sub, "mine-b.md"), "w", encoding="utf-8") as fh:
        fh.write("changed\n")
    # wip.md 保持 untracked ⇒ 它在 changed 里，却不该在 `git archive HEAD` 里

    out = os.path.join(base, "out")
    #: **`tar -C` 要的是已存在的目录**——第一版忘了建，
    #: 报出来的是 `tar: could not chdir to …/out`，
    #: **而真实原因是「目标目录没建」**，离得很远（纪律 157 同族）。
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(base, "a.tar"), "wb") as fh:
        subprocess.run(["git", "-C", repo, "archive", "HEAD", sub], check=True, stdout=fh)
    subprocess.run(["tar", "-xf", os.path.join(base, "a.tar"), "-C", out], check=True)
    for name in ("mine-a.md", "mine-b.md"):
        with open(os.path.join(repo, sub, name)) as s, \
                open(os.path.join(out, sub, name), "w") as d:
            d.write(s.read())

    files = [os.path.join(sub, "mine-a.md"), os.path.join(sub, "mine-b.md")]
    #: **`??`（未跟踪）与 ` M`（已入库但被改）两种状态都要在名单里**——
    #: 它们在判据①②里待遇相同，在判据④里**必须分开**。
    wip = [os.path.join(sub, "wip.md"), os.path.join(sub, "wip-tracked.md")]

    # 负样本：两个本批文件都叠了 → 0 问题。
    # **它同时是判据④的「不误伤」那一半**：`wip-tracked.md`（` M`）
    # 此刻**就在副本树里**（HEAD 版），若判据④不按状态码分开就会误报。
    p1, n1 = preflight(repo, sub, out, files, wip)
    assert not p1, ("负样本本该 0 问题，却报了：%s" % p1)
    assert any("KNOWN_WIP 生效中" in x and "未跟踪的新文件" in x for x in n1), n1
    assert any("KNOWN_WIP 生效中" in x and "已入库文件被改" in x for x in n1), n1

    # 正样本①：FILES 漏掉 mine-b → 必须点名它
    p2, _ = preflight(repo, sub, out, files[:1], wip)
    assert len(p2) == 1 and "mine-b.md" in p2[0], p2

    # 正样本②：把同事的 WIP 从名单里去掉 → 必须报「漏叠加」并点名它们
    p3, _ = preflight(repo, sub, out, files, [])
    assert len(p3) == 2, p3
    assert any("wip.md" in x for x in p3) and any("wip-tracked.md" in x for x in p3), p3

    # 正样本③：排除名单过期（同事已撤销）→ 必须出「⚠ 名单失效」那条提示，
    # **而且它必须是 notes 而不是 problems**——失效本身不该让构建失败。
    # **必须把仍在生效的 WIP 一起留着**——第一版只写 `wip_stale = ["sub/gone.md"]`，
    # **把 wip.md 从名单里挤掉了，于是它变成「漏叠加」**，
    # **而我要验的那条（名单失效）根本没被单独验到**。
    wip_stale = [os.path.join(sub, "gone.md")] + wip
    p4, n4 = preflight(repo, sub, out, files, wip_stale)
    assert not p4, p4
    assert any("没有**改动" in x and "gone.md" in x for x in n4), n4

    # 正样本④：判据④的「能抓」那一半——**同事的未跟踪文件被叠进了副本树**
    # （模拟叠加脚本写错，把整个工作区 cp 过去那种手滑）→ 必须点名它。
    # **注意这里只能 cp 未跟踪的 wip.md**：`wip-tracked.md` 本来就在副本树里，
    # **而那是对的**，判据④按状态码分开正是不许把它当成同一件事。
    shutil.copyfile(os.path.join(repo, sub, "wip.md"), os.path.join(out, sub, "wip.md"))
    p5, _ = preflight(repo, sub, out, files, wip)
    assert len(p5) == 1 and "wip.md" in p5[0] and "未跟踪" in p5[0], p5
    #: 反向再确认一次：**删掉这个多余文件后就恢复 0 问题**——
    #: 否则上面那条可能只是「碰巧报了别的东西」
    os.remove(os.path.join(out, sub, "wip.md"))
    p6, _ = preflight(repo, sub, out, files, wip)
    assert not p6, p6

    shutil.rmtree(base, ignore_errors=True)
    print("自测 6 个样本全过：负样本 0 问题（且 ` M` 的 WIP 在副本树里**不**误报）；"
          "正样本①漏叠加、正样本②名单漏了 WIP、"
          "正样本③名单过期（走 notes 不走 problems）、"
          "正样本④副本树混进未跟踪文件（抓得到，且拿掉就恢复 0 问题）")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=REPO_DEFAULT)
    ap.add_argument("--sub", default="docs/user-manual/beeftv-canvas")
    ap.add_argument("--out", help="副本树根目录")
    ap.add_argument("--files", help="一行一个相对路径：本批要叠加的文件")
    ap.add_argument("--wip", help="一行一个相对路径：同事的未提交 WIP（显式排除）")
    ap.add_argument("--no-gate", action="store_true", help="不跑闸 8")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        self_test()
        return 0
    if not (a.out and a.files and a.wip):
        ap.error("需要 --out --files --wip（或用 --self-test）")

    problems, notes = preflight(a.repo, a.sub, a.out, read_list(a.files),
                                read_list(a.wip), run_tables_gate=not a.no_gate)
    for n in notes:
        print("  ℹ " + n)
    for p in problems:
        print("  ✗ " + p)
    if problems:
        print("承重核对失败（%d 处），不跑构建" % len(problems))
        return 1
    print("承重核对通过：%d 条信息、0 处问题" % len(notes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
