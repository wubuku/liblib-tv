#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三十八道闸（`verify-worktree-state.py`）的反向验证。

    **它守的是一条纪律的机器化**（纪律 303）：
    **「构建红」的归因必须先排掉工作区里未提交的改动。**

**四例，两个方向**：

    · **基线**：工作区就是 HEAD 之外还干净 → 报「没有未提交改动」；
    · **不误伤 3**：树外有改动 → 仍然 rc=0，**且明确说「不影响任何一道闸」**；
    · **能抓 1**：**手册树内有改动 → 必须点名是哪几个文件**，且 rc 仍是 0
      （**它不判定对错**，工作区脏不是缺陷）。

**为什么能抓那一侧不能写成 rc=1**：
**同事正在改东西是正常状态**，而报成不一致会把人引去「修」一个别人正在进行的工作
（纪律 300）。**这一条要在用例里钉死，否则下一个维护者很可能顺手把它改成 fail。**

**夹具怎么造**：**不碰真树**——在临时目录里建一个 `git init` 的仓，
**把手册目录摆成 `<仓>/docs/user-manual/beeftv-canvas/` 的形状**，
**因为 `verify-worktree-state.py` 是从自己所在目录向上找 `.git` 的**（纪律 302：
**副本树只能验同一棵树上改前改后的差别**，而本闸问的正是「这棵树脏不脏」，
**在临时仓里问是唯一诚实的做法**）。
"""

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.join(HERE, "verify-worktree-state.py")
results = []


def record(name, ok, detail=""):
    results.append((name, "通过" if ok else "失败", detail))


def git(repo, *args):
    return subprocess.run(["git", "-C", repo] + list(args),
                          capture_output=True, text=True)


def fixture():
    """造一棵临时的仓：`docs/user-manual/beeftv-canvas/` 里只放闸脚本本身。"""
    repo = tempfile.mkdtemp(prefix="beef-wt-fixture.")
    manual = os.path.join(repo, "docs", "user-manual", "beeftv-canvas")
    os.makedirs(os.path.join(manual, "scripts"))
    shutil.copy(GATE, os.path.join(manual, "scripts", "verify-worktree-state.py"))
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "t@example.invalid")
    git(repo, "config", "user.name", "fixture")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "init")
    return repo, manual


def run_gate(manual):
    r = subprocess.run([sys.executable,
                        os.path.join(manual, "scripts", "verify-worktree-state.py")],
                       cwd=manual, capture_output=True, text=True, timeout=60)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def m_clean():
    """基线：刚提交完、工作区干净 → 必须说出「没有未提交改动」。"""
    repo, manual = fixture()
    try:
        rc, out = run_gate(manual)
        ok = rc == 0 and "没有未提交改动" in out and "已提交的那一份" in out
        record("1 工作区干净→必须说「与已提交的那一份一致」", ok, f"rc={rc}")
    finally:
        shutil.rmtree(repo, ignore_errors=True)


def m_outside_not_flagged():
    """**不误伤**：改动落在手册树外 → 仍然 rc=0，且说清「不参与构建」。

    **这是最容易写坏的一半**：把「树外有改动」也报成需要处理，
    **就会有人去动同事的代码**。
    """
    repo, manual = fixture()
    try:
        outside = os.path.join(repo, "somewhere-else", "notes.md")
        os.makedirs(os.path.dirname(outside), exist_ok=True)
        with open(outside, "w", encoding="utf-8") as fh:
            fh.write("# 同事的笔记\n")
        rc, out = run_gate(manual)
        #: **`somewhere-else/` 而不是 `notes.md`——第一版断言写的是文件名，于是红了。**
        #: **而红的原因不是判据错了**：`git status --porcelain` **对整个未跟踪目录只打一条**，
        #: 路径是**目录本身**、末尾带 `/`，**不会展开成里面的每个文件**。
        #: **判据照抄 git 的口径是对的**（**而自己再展开一遍就是第二套口径**，纪律 274），
        #: **要改的是断言**。
        ok = (rc == 0 and "手册树内**没有**未提交改动" in out
              and "不参与构建" in out and "somewhere-else" in out)
        record("2 改动只在树外→不得说手册被污染", ok, f"rc={rc}")
    finally:
        shutil.rmtree(repo, ignore_errors=True)


def m_inside_named_and_rc0():
    """**能抓那一侧**：手册树内有改动 → **必须点名文件**，**且 rc 仍是 0**。

    **rc=0 这一点和点名一样重要**——**点名是给归因用的**，
    **而 rc=1 会把它变成一道「工作区必须干净」的闸**，
    **那会让同事无法在同一个工作区里干活**。
    """
    repo, manual = fixture()
    try:
        target = os.path.join(manual, "10-tasks", "README.md")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as fh:
            fh.write("# 任务指南\n\n somebody 改了一行\n")
        rc, out = run_gate(manual)
        #: **路径同样按 git 的口径是目录**（`.../10-tasks/`），
        #: **断言只认目录名**——**而这正是要它认的那一层**：
        #: **读者要能据此去还原，而还原的对象就是一个目录。**
        ok = (rc == 0 and "落在手册树内" in out and "10-tasks" in out
              and "必须先排掉这些" in out)
        record("3 手册树内有改动→必须点名且 rc 仍为 0（工作区脏不是缺陷）",
               ok, f"rc={rc}")
    finally:
        shutil.rmtree(repo, ignore_errors=True)


def m_untracked_separated():
    """**未跟踪要单独标出来**——**因为它不参与还原**。

    **而判据对照靠的就是还原**：一个未跟踪的注入留在树上，
    **「HEAD 版 vs 工作区版」的对照就会得出错误结论**（Batch 267 走过这条路）。
    **这一例钉的是「未跟踪文件在报告里能被认出来」。**
    """
    repo, manual = fixture()
    try:
        fresh = os.path.join(manual, "50-new.md")
        with open(fresh, "w", encoding="utf-8") as fh:
            fh.write("# 全新文件\n")
        rc, out = run_gate(manual)
        ok = rc == 0 and "[未跟踪]" in out and "50-new.md" in out
        record("4 未跟踪文件必须单独标出（它不参与还原）", ok, f"rc={rc}")
    finally:
        shutil.rmtree(repo, ignore_errors=True)


def m_unreadable_is_rc2():
    """**rc=2 不是「通过」**——判据自己读不到状态时必须说「未能核对」。"""
    repo, manual = fixture()
    try:
        # 把闸挪到一棵**没有 .git 的**树上：向上找 6 层都找不到
        deep = os.path.join(manual, "a", "b", "c", "d", "e", "f", "g")
        os.makedirs(deep, exist_ok=True)
        lonely = os.path.join(deep, "verify-worktree-state.py")
        shutil.copy(GATE, lonely)
        r = subprocess.run([sys.executable, lonely], cwd=deep,
                           capture_output=True, text=True, timeout=60)
        out = (r.stdout or "") + (r.stderr or "")
        ok = r.returncode == 2 and "未能核对" in out
        record("5 判据自己读不到状态→必须 rc=2 而不是放行", ok, f"rc={r.returncode}")
    finally:
        shutil.rmtree(repo, ignore_errors=True)


def m_classified_by_reader_not_ext():
    """**Batch 269 新增**：树内改动**必须按「闸怎么读它」分类，而不只是列文件名**。

    **而分类的价值全在「让人少找一族判据」**：
    改 `10-tasks/README.md`（索引）要找索引文字那一族，
    改 `10-tasks/asset-library.md`（内容页）要找页内标题那一族，
    **改 `scripts/verify-x.py` 则是改判据本身——症状完全不同**
    （闸崩掉而 rc 可能仍是 0，纪律 301）。
    **列文件名不提供这三者的区别**，**所以这一例钉的是「必须分」而不是「必须列」**。
    """
    repo, manual = fixture()
    try:
        for rel in ("10-tasks/README.md", "10-tasks/asset-library.md",
                    "scripts/verify-demo.py"):
            p = os.path.join(manual, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("改了一行\n")
        rc, out = run_gate(manual)
        ok = (rc == 0 and "按类别分" in out
              and "正文页·索引" in out and "正文页·内容" in out
              and "判据脚本" in out)
        record("6 树内改动必须按「闸怎么读它」分类（列文件名不够）", ok, f"rc={rc}")
    finally:
        shutil.rmtree(repo, ignore_errors=True)


def m_task_page_not_mislabelled_as_index():
    """**不许把 `10-tasks/` 下的 29 页全当成索引**。

    **第一版分类条件写的是 `rel.startswith("10-tasks/")`——于是每一页都成了「索引」**，
    **而这个归错恰好把分类的价值抵掉**：
    **读者以为「动了索引」，于是去找索引文字那一族判据，
    而真正该找的是页内标题那一族。**
    """
    repo, manual = fixture()
    try:
        p = os.path.join(manual, "10-tasks", "asset-library.md")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write("# 普通内容页\n")
        rc, out = run_gate(manual)
        ok = (rc == 0 and "正文页·内容" in out
              and "正文页·索引" not in out)
        record("7 10-tasks/ 下的普通页不许被归成「索引」", ok, f"rc={rc}")
    finally:
        shutil.rmtree(repo, ignore_errors=True)


def main():
    for t in (m_clean, m_outside_not_flagged, m_inside_named_and_rc0,
              m_untracked_separated, m_unreadable_is_rc2,
              m_classified_by_reader_not_ext, m_task_page_not_mislabelled_as_index):
        try:
            t()
        except AssertionError as exc:
            record(t.__name__, "作废", f"前提失配：{exc}")
    failed = 0
    for name, status, detail in results:
        print("  %s %s  %s" % ({"通过": "✓", "失败": "✗", "作废": "—"}[status],
                               name, detail))
        if status != "通过":
            failed += 1
    print("闸 38 反验：%d 例，通过 %d，失败/作废 %d"
          % (len(results), len(results) - failed, failed))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
