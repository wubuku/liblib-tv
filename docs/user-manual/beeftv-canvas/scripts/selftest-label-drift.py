#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第六道闸（verify-label-drift.py）的反向验证。

**本闸此前是十道闸里唯一一道完全没有反向验证的**（Batch 167 普查：全部 selftest
脚本里对它的提及数为 0）。根因很具体：**它的 ref 写死成 `origin/main`**，
连「造一个合成 ref 去注入」都做不到——闸门的能力**从来没被验证过**。
Batch 167 补上 `BEEFTV_REF` 覆盖，本文件就是那之后的第一次验证。

合成 ref 用**最小树**（只放两三个 web/src 下的文件），不重建整棵树——
闸 7 的反验每例要 `read-tree` 全树、约 90 秒；这里只需几秒。

  能抓 1：同一个 value 在两个文件里被叫成不同名字、且不在登记表 → 必须报
  不误伤 3：
    · 同一 value 在两个文件里**叫法一致** → 必须放行
    · 同一 value 不同叫法但**都在同一个文件里** → 必须放行（跨文件过滤）
    · 同一 value 不同叫法、但**已在 CLASSIFIED 登记表里** → 必须放行

⚠️ 用完必须删掉临时 ref——它在 BeefTV 仓的 .git 里，留在那儿会被 `git gc` 之外的东西看到。
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE = os.path.join(HERE, "verify-label-drift.py")
SRC = os.environ.get("BEEFTV_SRC", "/Users/yangjiefeng/Documents/glanderness/BeefTV")
TMPREF = "refs/manual-selftest-label-drift"

PASS = VOID = FAIL = 0


def build_ref(files):
    """以 origin/main 的树为底，叠加 files（{路径: 内容}），造一个合成 ref。

    ⚠️ **必须以真实树为底**：闸 6 有**反向**检查——登记表的每一条都必须仍在上游存在，
    否则报「登记已失效，请清理登记」。若只放两三个文件，27 条登记会全部「消失」，
    闸门判 rc=1 ——**那是闸门判对了，是我第一版测试设计错了**
    （第一版因此让三条「不误伤」用例全部误判为失败）。
    """
    idx = tempfile.mktemp(prefix="beef-label-selftest.")
    try:
        env = {**os.environ, "GIT_INDEX_FILE": idx}
        base = subprocess.run(["git", "rev-parse", "origin/main^{tree}"], cwd=SRC,
                              capture_output=True, text=True, check=True).stdout.strip()
        subprocess.run(["git", "read-tree", base], cwd=SRC, env=env,
                       capture_output=True, text=True, check=True)
        for path, content in files.items():
            blob = subprocess.run(["git", "hash-object", "-w", "--stdin"], cwd=SRC, input=content,
                                  capture_output=True, text=True, check=True).stdout.strip()
            subprocess.run(["git", "update-index", "--add", "--cacheinfo", f"100644,{blob},{path}"],
                           cwd=SRC, env=env, capture_output=True, text=True, check=True)
        tree = subprocess.run(["git", "write-tree"], cwd=SRC, env=env,
                              capture_output=True, text=True, check=True).stdout.strip()
        commit = subprocess.run(["git", "commit-tree", tree, "-p",
                                 subprocess.run(["git", "rev-parse", "origin/main"], cwd=SRC,
                                                capture_output=True, text=True, check=True).stdout.strip()],
                                cwd=SRC, input="label drift selftest",
                                capture_output=True, text=True, check=True).stdout.strip()
        subprocess.run(["git", "update-ref", TMPREF, commit], cwd=SRC, capture_output=True, text=True, check=True)
        return commit
    finally:
        try:
            os.remove(idx)
        except OSError:
            pass


def run(desc, files, expect_fail=True, want=None):
    global PASS, VOID, FAIL
    commit = None
    try:
        commit = build_ref(files)
        r = subprocess.run([sys.executable, GATE], cwd=ROOT, capture_output=True, text=True,
                           env={**os.environ, "BEEFTV_REF": TMPREF})
        out = r.stdout + r.stderr
        if expect_fail and r.returncode == 0:
            print("  ✗ %s：闸门本应报错，却通过了" % desc); FAIL += 1
        elif expect_fail and want and want not in out:
            print("  ✗ %s：报错了但不是 [%s]；实际：%s" % (desc, want, out.strip()[-160:])); FAIL += 1
        elif not expect_fail and r.returncode != 0:
            print("  ✗ %s：本应放行却报错（误伤，rc=%d）：%s" % (desc, r.returncode, out.strip()[-200:]))
            FAIL += 1
        else:
            print("  ✓ %s" % desc); PASS += 1
    except subprocess.CalledProcessError as exc:
        print("  ✗ %s：合成 ref 失败，前提不成立，**本用例作废**（%s）" % (desc, exc)); VOID += 1
    finally:
        if commit:
            subprocess.run(["git", "update-ref", "-d", TMPREF], cwd=SRC, capture_output=True)


def main():
    base = subprocess.run([sys.executable, GATE], cwd=ROOT, capture_output=True, text=True)
    if base.returncode == 0:
        print("  ✓ 基线：真实 origin/main 通过（%s）" % base.stdout.strip().split("\n")[-1][:70])
        globals()["PASS"] = globals()["PASS"] + 1
    else:
        print("  ✗ 基线：真实 origin/main 应当通过，rc=%d" % base.returncode)
        globals()["FAIL"] = globals()["FAIL"] + 1

    # 能抓：跨文件分歧且未登记
    run("1) 同一 value 跨文件叫法不同且未登记（必须报）", {
        "web/src/a/panel.ts": 'const x = { value: "selftest_drift", label: "旧的说法" };\n',
        "web/src/b/list.ts": 'const y = { value: "selftest_drift", label: "新的说法" };\n',
    }, expect_fail=True, want="selftest_drift")

    # 不误伤 1：跨文件但叫法一致
    run("2) 不误伤：跨文件叫法一致（必须放行）", {
        "web/src/a/panel.ts": 'const x = { value: "selftest_same", label: "同一个说法" };\n',
        "web/src/b/list.ts": 'const y = { value: "selftest_same", label: "同一个说法" };\n',
    }, expect_fail=False)

    # 不误伤 2：分歧全在同一文件内（跨文件过滤必须生效）
    run("3) 不误伤：分歧都在同一文件内（必须放行）", {
        "web/src/a/solo.ts": ('const a = { value: "selftest_solo", label: "说法一" };\n'
                              'const b = { value: "selftest_solo", label: "说法二" };\n'),
    }, expect_fail=False)

    # 不误伤 3：分歧已登记（用 CLASSIFIED 里已有的 value 造一个跨文件形态）
    run("4) 不误伤：分歧已在登记表内（必须放行）", {
        "web/src/a/p1.ts": 'const x = { value: "inpaint", label: "局部修改" };\n',
        "web/src/b/p2.ts": 'const y = { value: "inpaint", label: "完全不同的另一种叫法" };\n',
    }, expect_fail=False)

    print("=== 结果：通过 %d / 失败 %d / 作废 %d ===" % (PASS, FAIL, VOID))
    return 1 if (FAIL or VOID) else 0


if __name__ == "__main__":
    sys.exit(main())
