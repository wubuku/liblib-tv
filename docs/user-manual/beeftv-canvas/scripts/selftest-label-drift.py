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
from beefsrc import resolve_src, explain
import sys
import tempfile
from stagedeps import child_env
#: **Batch 272 新增的这条 import 是上面那段修复的一部分**：
#: 夹具的底从 `origin/main` 换成**手册声明的基线提交**，
#: 而那个提交只能从 `declared_baseline()` 拿——**它是「手册照哪版写的」的唯一一份实现**
#: （纪律 274）。**这里不自己写死 `bcc3b05`**：
#: 写死一份，基线升版时它就会静悄悄过期，而夹具仍然绿。
from baseline import declared_baseline, BaselineError

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE = os.path.join(HERE, "verify-label-drift.py")
#: **Batch 197：路径解析收敛到 `beefsrc` 单一来源**（原先硬编码绝对路径，
#: 而闸与这份反验各有一份，于是反验可能在一个仓上注入、闸却在另一个仓上核）。
SRC, _FB = resolve_src()
if SRC is None:
    raise SystemExit("找不到可用的 BeefTV 源码仓：设 BEEFTV_SRC。候选：\n" + explain())
TMPREF = "refs/manual-selftest-label-drift"
#: **基线例输出里那句话的措辞**。**它原先写「真实 origin/main」——而底在 Batch 272 换成基线提交之后，那句话就成了假的**。
#: **测试输出里的标签也是断言的一部分**：一个说错的标签会让人以为
#: 「这条用例验的是 origin/main」，而它验的不是（纪律 307 推论二）。
TAG_BASELINE = "手册声明的基线提交那一棵树（**Batch 272 改的底**——原先是 `origin/main`，**而闸 6 本体读的是基线提交**，两个调用方看的是两个世界）"

PASS = VOID = FAIL = 0


def build_ref(files):
    """以**手册声明的取证基线提交**那棵树为底，叠加 files（{路径: 内容}），造一个合成 ref。

    ⚠️ **必须以真实树为底**：闸 6 有**反向**检查——登记表的每一条都必须仍在上游存在，
    否则报「登记已失效，请清理登记」。若只放两三个文件，27 条登记会全部「消失」，
    闸门判 rc=1 ——**那是闸门判对了，是我第一版测试设计错了**
    （第一版因此让三条「不误伤」用例全部误判为失败）。

    **Batch 272 改了一处底：原先这里写死 `origin/main^{tree}`。**
    **而闸 6 本体走 `baseline.resolve_ref()`，默认读的是手册声明的基线提交**
    （本树是 v1.6.22 / `bcc3b05`）。**于是两个调用方看的是两个不同的世界**：

      · 闸 6 读基线 → v1.7.3 才有的标签在那里不存在 → 27 条登记全部有效 → 闸绿；
      · 本反验读 `origin/main`（v1.7.3）→ 多出两处分歧 → **未登记** → rc=1。

    **而登记表是全局的一份，两个方向都查**，所以**没有任何登记状态能让两边同时绿**：
    实测把 `openai` / `gemini` 两条登记进去，闸 6 立刻改报「登记已失效 2」——
    **这不是「二选一」，是这份夹具与这道闸的前提本来就没对齐**。

    **修法是让夹具的底回到闸默认读的那个 ref**，而不是去改登记表：
    **登记表记的是「在这个 ref 上有哪些分歧」，换个 ref 去问它，答的就不是同一件事**
    （纪律 107，与闸 14 那条 `FLOATING_REF_EXEMPT` 同一族理由）。
    **为什么用声明的提交而不是 `resolve_ref()`**：闸 18 方向五之二会设 `BEEFTV_REF`
    去重放本反验，**若底也跟着环境变量走，重放时底就变成了被改过的那棵树**——
    **夹具必须对环境免疫**，否则「反向验证」验的是另一件事。
    """
    idx = tempfile.mktemp(prefix="beef-label-selftest.")
    try:
        env = {**os.environ, "GIT_INDEX_FILE": idx}
        try:
            base_commit = declared_baseline()[1]
        except BaselineError as exc:
            raise SystemExit("读不到手册声明的取证基线：%s——**夹具的底就是它**，读不到就造不出合成 ref" % exc)
        base = subprocess.run(["git", "rev-parse", base_commit + "^{tree}"], cwd=SRC,
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
        commit = subprocess.run(["git", "commit-tree", tree, "-p", base_commit],
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
                           env=child_env(ROOT, BEEFTV_REF=TMPREF))
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
    base = subprocess.run([sys.executable, GATE], cwd=ROOT, capture_output=True, text=True, env=child_env(ROOT))
    if base.returncode == 0:
        print("  ✓ 基线：%s 通过（%s）"
              % (TAG_BASELINE, base.stdout.strip().split("\n")[-1][:70]))
        globals()["PASS"] = globals()["PASS"] + 1
    else:
        print("  ✗ 基线：%s 应当通过，rc=%d" % (TAG_BASELINE, base.returncode))
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
