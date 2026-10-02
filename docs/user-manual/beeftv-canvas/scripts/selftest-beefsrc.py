#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`beefsrc.py` 的反向验证（Batch 198 新增）。

**为什么一个没有闸的模块也要有反验**：Batch 197 把「BeefTV 源码仓在哪」
从 13 道闸各自抄的一份收敛成 `scripts/beefsrc.py` 单一来源——
**15 道闸 + `baseline.py` + 2 份反验现在全靠它**。
而它自己**不受任何一道闸检查**：改坏 `is_repo()` 或候选顺序，
构建照样全绿，只是 13 道闸在悄悄换地方读上游。
**Batch 190 建 `scope.py` 时配了 5 例，本批按同一规矩补上。**

**六例**：

  1. **能抓**：一个**普通目录**（没有 `.git`）必须被判假 ——
     **这正是旧写法 `isdir(c/"backend")` 会放过的那类**；
  2. **能抓**：一个**裸库**（`git init --bare`）必须被判真 ——
     旧写法两种都判假（裸库既没有 `backend/` 也没有 `.git` 目录）；
  3. **能抓（本批最要紧的一例）**：**git worktree 必须被判真**——
     worktree 里 `.git` 是一个**文件**，实测旧写法
     `isdir(c/".git")` 必然判假，于是用户显式指定的 `BEEFTV_SRC`
     **被静默忽略**、改用兜底那份，而闸一声不吭还报绿（Batch 197 纪律 172）。
     **本例由临时树里现造的 worktree 支撑，判真标准是 `git rev-parse --git-dir`；
     任何人把 `is_repo()` 改回 `isdir(".git")` 都会在这里红。**
  4. **能抓**：`BEEFTV_SRC` 指向一个**不是仓**的路径时，
     `resolve_src()` 必须**明确标出走了兜底**（第二个返回值为真）——
     **静默降级比直接失败更坏，因为它还报绿**；
  5. **不误伤（本批的假阳性量尺）**：`BEEFTV_SRC` 指向一个**真仓**时，
     第二个返回值必须为**假**——**不能逢回落就喊回落**，
     否则那句 `[兜底]` 会变成又一句没人看的日志；
  6. **候选顺序**：`BEEFTV_SRC` 必须压过相对兄弟路径与硬编码兜底 ——
     **顺序即优先级**，写反了会让用户的显式指定失效。

**这六例全部用临时树里现造的仓，不碰真 BeefTV 检出。**
用例 3 的 worktree 建在临时树里、用完即删——**不往真仓注册 worktree**。

退出码：0 全部通过；1 有用例失败。
"""

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import beefsrc                                                    # noqa: E402

failures = []


def case(name, fn):
    try:
        ok, why = fn()
    except Exception as exc:                                      # noqa: BLE001
        ok, why = False, "%s: %s" % (type(exc).__name__, exc)
    print("  %s %-34s %s" % ("✅" if ok else "❌", name, why))
    if not ok:
        failures.append(name)


def git(*args, cwd=None):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def make_repo(path, bare=False):
    """造一个最小真仓：有 `.git`，`rev-parse --git-dir` 成功。"""
    os.makedirs(path, exist_ok=True)
    if bare:
        assert git("init", "--bare", "-q", path).returncode == 0
        return path
    assert git("init", "-q", path).returncode == 0
    with open(os.path.join(path, "README.md"), "w", encoding="utf-8") as fh:
        fh.write("# demo\n")
    git("add", "-A", cwd=path)
    git("-c", "user.email=a@b", "-c", "user.name=t",
        "commit", "-qm", "init", cwd=path)
    return path


def main():
    root = tempfile.mkdtemp(prefix="beefsrc-selftest-")
    # 相对兄弟路径与硬编码兜底**都指向真机上的 BeefTV**，
    # 所以凡是要断言「回落」或「不回落」的用例，都得先把它们从候选表里摘掉——
    # 否则用例测的是本机的目录布局，不是被测逻辑。
    real_abs = beefsrc.FALLBACK_ABS
    print("`beefsrc` 反验：6 例（3 能抓 + 1 兜底标记 + 1 不误伤 + 1 候选顺序）")
    try:
        # 1 —— 普通目录不是仓（旧写法 isdir("backend") 会放过它）
        plain = os.path.join(root, "plain")
        os.makedirs(os.path.join(plain, "backend"), exist_ok=True)
        case("plain-dir-not-a-repo",
             lambda: (False, "没误判成仓") if beefsrc.is_repo(plain)
             else (True, "有 backend/ 的普通目录仍被判假"))

        # 2 —— 裸库算仓（旧写法两种都判假：既无 backend/ 也无 .git 目录）
        bare = make_repo(os.path.join(root, "bare.git"), bare=True)
        case("bare-repo-accepted",
             lambda: (True, "裸库被接受") if beefsrc.is_repo(bare)
             else (False, "裸库被判假——旧写法必然犯这个错"))

        # 3 —— **worktree**：.git 是文件，isdir(".git") 必然判假
        wt = os.path.join(root, "wt")
        repo = make_repo(os.path.join(root, "repo"))
        r = git("worktree", "add", "-q", "--detach", wt, "HEAD", cwd=repo)
        assert r.returncode == 0, r.stderr
        try:
            dotgit_is_file = os.path.isfile(os.path.join(wt, ".git"))
            assert dotgit_is_file, "构造失败：worktree 里 .git 不是文件"
            case("worktree-accepted",
                 lambda: (True, "worktree 被接受（.git 是文件，isdir 必然判假）")
                 if beefsrc.is_repo(wt) else (False, "**worktree 被判假**——"
                                              "isdir(c/'.git') 写法会正好在这里红"))
        finally:
            git("worktree", "remove", "--force", wt, cwd=repo)

        # 4 —— BEEFTV_SRC 不是仓 → 必须明确标出走了兜底
        beefsrc.FALLBACK_ABS = make_repo(os.path.join(root, "fallback.git"))
        os.environ["BEEFTV_SRC"] = os.path.join(root, "plain")
        src, fb = beefsrc.resolve_src()
        case("fallback-is-announced",
             lambda: (True, "回落已标记：%s" % src) if fb
             else (False, "回落了却没标记——**静默降级比直接失败更坏**"))

        # 5 —— 不误伤：BEEFTV_SRC 指向真仓时不得喊回落
        good = make_repo(os.path.join(root, "good"))
        os.environ["BEEFTV_SRC"] = good
        src2, fb2 = beefsrc.resolve_src()
        case("no-false-fallback",
             lambda: (True, "未误报回落") if not fb2
             else (False, "**BEEFTV_SRC 指定的就是它，却仍被标成回落**"))

        # 6 —— 候选顺序：BEEFTV_SRC 压过兜底
        case("env-wins-over-fallback",
             lambda: (True, "采用了 BEEFTV_SRC 指定的 %s" % src2)
             if os.path.abspath(src2) == os.path.abspath(good)
             else (False, "选了 %s 而不是用户指定的 %s" % (src2, good)))
    finally:
        os.environ["BEEFTV_SRC"] = os.environ.get("BEEFTV_SRC", "")
        beefsrc.FALLBACK_ABS = real_abs
        shutil.rmtree(root, ignore_errors=True)

    print()
    if failures:
        print("❌ %d/6 例失败：%s" % (len(failures), "、".join(failures)))
        return 1
    print("✅ 6/6 例通过（3 能抓 + 1 兜底标记 + 1 不误伤 + 1 候选顺序）")
    print("   —— 判真标准是 `git rev-parse --git-dir`；把它改回 `isdir(\".git\")` 会在用例 3 红。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
