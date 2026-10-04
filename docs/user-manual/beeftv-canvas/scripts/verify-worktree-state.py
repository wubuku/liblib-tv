#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三十八道闸（Batch 268 新增）：**工作区未提交改动报告**。

    它**不判定对错**——它只回答一个问题：
    **此刻构建读到的手册，与已提交的那一份，差在哪里。**

**为什么需要它**（**实测出来的，不是设想的**）：
Batch 267 收尾时真树构建 rc=1，纪律 280 的 pre-commit 钩子拦住了提交。
**而那两处红的来源根本不是本批**——是**工作区里别人未提交的注入实验**
（`10-tasks/README.md` 把链接文字改成「素材库（错的）」、
`asset-library.md` 首行插一句 HTML 注释）。
**判断这件事花了三轮对照**：

    ① 先怀疑自己的改动 → 在副本树里把文件换回 HEAD → 反验层「HEAD 3 例红、本批 2 例红」；
    ② 闸本体层「HEAD 4 处、真树 3 处」→ **两次跑还不稳定**；
    ③ 最后在真树连跑两次，**恒为同一处红**，才敢下结论。

**③ 是对的，① 和 ② 都是绕路**——
**而绕路的原因很简单：那台机器上没有任何东西会说「工作区脏了」**。
**本闸把那句话说出来。**

**它为什么必须区分「手册树内」与「手册树外」**：
**树外的改动不影响任何一道闸**（它们既不被扫、也不进产物），
**而树内的改动会实打实地改掉构建读到的手册**——
**Batch 267 那一次，正是树内的两处**。

**它为什么不做成 fail**：
**工作区脏不是缺陷，同事正在改东西是正常状态**——
**报成不一致会把人引去「修」一个别人正在进行的工作**。
**所以 rc=0，而内容必须打在构建日志里**（纪律 300 推论一：
**一个数只有和它的分母一起报出来才是数**）。
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _repo_root():
    """手册目录向上找 `.git`——**与 `buildrecord.repo_root()` 同一个约定**，
    而这里**刻意自己实现一遍而不是 import 它**：
    **闸与共享模块耦合越紧，它自己坏掉时越难定位**
    （Batch 266 实测：判据崩了却 rc=0 是同一族最糟的形态）。
    """
    d = ROOT
    for _ in range(6):
        if os.path.isdir(os.path.join(d, ".git")):
            return d
        d = os.path.dirname(d)
    return None


def porcelain_paths(repo):
    """`git status --porcelain` 的路径集合（分已跟踪/未跟踪两类）。

    **为什么分开**：**未跟踪文件不参与 `git checkout` 式的还原**，
    **而 Batch 267 的判据对照必须靠还原——**一个未跟踪的注入留在树上，
    对照就会得出错误结论**。
    """
    try:
        r = subprocess.run(["git", "-C", repo, "status", "--porcelain"],
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        return None, "调不动 git：%s" % exc
    if r.returncode != 0:
        return None, "git status 返回 %d：%s" % (r.returncode, (r.stderr or "").strip()[:120])
    tracked, untracked = set(), set()
    for line in (r.stdout or "").split("\n"):
        if len(line) < 4:
            continue
        code, path = line[:2], line[3:].strip()
        # 重命名写成 `old -> new`，取后者
        if " -> " in path:
            path = path.split(" -> ")[-1].strip()
        path = path.strip('"')
        if code == "??":
            untracked.add(path)
        else:
            tracked.add(path)
    return (tracked, untracked), None


#: **手册树内一处改动该归到哪一类**。
#: **分类的依据是「闸怎么读它」，不是「扩展名是什么」**——
#: **`screenshots/manifest.yml` 与 `20-reference.md` 都是内容，
#: 而前者被截图族判据读、后者被基线族判据读，受影响的面完全不同**。
#: **而 `.py` / `.sh` 单独成类**：它们不是内容、**是判据本身**，
#: **改坏它们的症状与改坏内容完全不同——闸会崩掉，而 rc 可能仍是 0**
#: （Batch 266 实测两次、Batch 267 实测一次，纪律 301）。
def _expand_untracked(repo, manual_dir, manual_prefix, untracked):
    """**把被 git 折叠成目录的未跟踪路径展开成真实文件列表**。

    **这是 Batch 269 实测出来的一个真缺陷，不是设想**：
    `git status --porcelain` 对**整个未跟踪目录只打一条**——
    实测建了 `10-tasks/README.md` 与 `10-tasks/asset-library.md` 两个文件，
    它报的是 `docs/user-manual/beeftv-canvas/10-tasks/`，**末尾带 `/`、没有扩展名**。
    **后果**：`_classify()` 按扩展名分类，**目录没有扩展名 → 全部落进「未归类」**，
    **于是「按类别缩小范围」这一步在最常见的情形下失效**——
    **而同事的注入实验恰好总是落在一个新目录里**（Batch 267/268 两次都是）。
    **修法**：对以 `/` 结尾的路径**走一遍目录树**，把它下面的真实文件取出来。

    **为什么不在报告里保留目录形式**：**分类要按真实文件**，
    **而 `git add -A` / `git checkout` 用哪个都能work**——
    **所以展开只用于分类，点名那几行仍按 git 自己的口径**（纪律 274：
    **判据照抄 git 的口径，不要自己再发明一套**）。
    """
    out = set()
    for p in untracked:
        if not p.endswith("/"):
            out.add(p)
            continue
        full = os.path.join(repo, p)
        for dirpath, _dirnames, filenames in os.walk(full):
            for fn in filenames:
                out.add(os.path.relpath(os.path.join(dirpath, fn), repo)
                        .replace(os.sep, "/"))
    return out


def _classify(path, manual_prefix):
    rel = path[len(manual_prefix):] if path.startswith(manual_prefix) else path
    ext = os.path.splitext(rel)[1].lower()
    if ext in (".py", ".sh"):
        return "判据脚本"
    if ext in (".yml", ".yaml"):
        return "截图登记册"
    if ext == ".mjs":
        return "站点配置"
    if ext == ".md":
        #: **第一版写的是 `rel.startswith("10-tasks/")`——那是错的**：
        #: **`10-tasks/` 下 29 页里只有 `README.md` 是索引，其余都是普通内容页**，
        #: **而把它们全归成「索引」会让读者以为「动了索引」——
        #: **于是去找索引文字那一族判据，而真正该找的是页内标题那一族**。
        #: **分类的价值全在「这一步能让人少找一族判据」，归错就正好把价值抵掉。**
        base = os.path.basename(rel)
        if base in ("README.md", "index.md") and rel.count("/") >= 1:
            return "正文页·索引"
        return "正文页·内容"
    if ext in (".json", ".txt", ".css"):
        return "其他资源"
    return "未归类"


def main():
    repo = _repo_root()
    if repo is None:
        print("[未能核对] 从手册目录向上找不到 .git——**无法判断工作区状态**")
        return 2

    got, err = porcelain_paths(repo)
    if got is None:
        print("[未能核对] %s" % err)
        return 2
    tracked, untracked = got

    manual_prefix = os.path.relpath(ROOT, repo).replace(os.sep, "/") + "/"
    in_manual = sorted(p for p in (tracked | untracked) if p.startswith(manual_prefix))
    outside = sorted(p for p in (tracked | untracked) if not p.startswith(manual_prefix))

    if not tracked and not untracked:
        print("工作区核对：手册树与树外**都没有未提交改动**"
              "　→ **构建读到的就是已提交的那一份**，红了就一定与已提交内容有关")
        return 0

    print("工作区核对：**有未提交改动，共 %d 处**"
          "（已跟踪 %d + 未跟踪 %d）——"
          "**构建读到的手册未必等于已提交的那一份**"
          % (len(tracked) + len(untracked), len(tracked), len(untracked)))

    if in_manual:
        print("  **其中 %d 处落在手册树内**（%s/）——**它们会实打实改掉构建读到的内容**："
              % (len(in_manual), manual_prefix.rstrip("/")))
        for p in in_manual[:20]:
            kind = "未跟踪" if p in untracked else "已跟踪"
            print("    · [%s] %s" % (kind, p))
        if len(in_manual) > 20:
            print("    · ……还有 %d 处" % (len(in_manual) - 20))
        print("    **所以「构建红」在归因给任何改动之前，必须先排掉这些**"
              "（Batch 267 实测：真树构建 rc=1，两处红的来源是工作区里"
              "**别人未提交的注入实验**，而判断这件事花了三轮对照）")
        print("    **最快的分辨办法**：把工作区还原成 HEAD（"
              "`git status --porcelain` 为空）再跑一次构建——"
              "**两次都红的才是真缺陷，只有工作区红的不是**")
        # ── Batch 269：把「脏在哪一类」也算出来 ────────────────────────
        # **上一版只说「脏」，而读者真正要回答的是「这几处会不会让我判错归因」**。
        # **Batch 268 实测的那一组就是最好的例子**：树内 2 处都是 `.md`，
        # **而它们让 `verify-meta.py`、`verify-link-labels.py`
        # 与 `selftest-link-labels.sh` 三个入口同时变红**——
        # **也就是说，判「构建红是不是我的改动」时，能立刻缩小范围的不是那 2 个文件名，
        # 而是「它们是正文页」这个事实**。
        by_kind = {}
        for p in sorted(_expand_untracked(repo, ROOT, manual_prefix, in_manual)):
            by_kind.setdefault(_classify(p, manual_prefix), []).append(p)
        print("    **按类别分（这才是缩小范围的那一步）**：")
        for kind in sorted(by_kind):
            ps = by_kind[kind]
            print("      · %-14s %d 处%s"
                  % (kind, len(ps),
                     ("：%s" % "、".join(os.path.basename(x) for x in ps[:3]))
                     if len(ps) <= 3 else "：%s 等" % os.path.basename(ps[0])))
        print("      **未跟踪的目录已展开成真实文件再分类**——"
              "`git status --porcelain` 对整个未跟踪目录只打一条、"
              "**而那一条没有扩展名、按扩展名分类会全部落进「未归类」**"
              "（Batch 269 实测：同事的注入实验两次都落在新目录里，"
              "**所以这正是最常见的情形**）")
        print("      **`.md` 正文页那一类影响面最大**——"
              "索引文字、页内标题、表格、链接文字四族判据都读它；"
              "**`.py` / `.sh` 那一类改的是判据本身**，"
              "**改坏了会让闸崩掉而 rc 仍是 0**（Batch 266/267 实测，纪律 301）")
    else:
        print("  手册树内**没有**未提交改动——"
              "**所以构建读到的就是已提交的那一份，红了一定与已提交内容有关**")

    if outside:
        print("  另有 %d 处落在手册树外（**不参与构建、也不被任何闸扫到**）："
              % len(outside))
        for p in outside[:8]:
            print("    · %s" % p)
        if len(outside) > 8:
            print("    · ……还有 %d 处" % (len(outside) - 8))
    return 0


if __name__ == "__main__":
    sys.exit(main())
