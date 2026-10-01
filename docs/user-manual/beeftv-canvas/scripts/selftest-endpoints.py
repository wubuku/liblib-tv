#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三道闸（verify-endpoints.py）改判据后的反向验证。

Batch 165 把判据从「脚本里的誊抄副本」改成「解析 `20-reference.md` 正文」。
新判据带来三类**以前不可能发生**的失败，必须逐类钉住：

  能抓 4 条：
    1) 现存表里的端点上游没有 → 必须报「声明存在但上游没有注册」
    2) 已下线表里的端点上游**有** → 必须报「已下线却在生产路由里注册了」
       （这条正是本批的核心洞：跨产品导入那对曾经完全没人看）
    3) 删掉一张表的小节锚点 → 必须 **rc=2 未能核对**，而**不是**「那张表没东西所以通过」
    4) 把一张表清空 → 必须 **rc=2**，解析器退化不能被当成「0 条不一致 → 全部通过」
  不误伤 2 条：
    5) 往现存表加一条上游确有注册的新端点 → 必须照旧通过
    6) 只动用途说明文字（端点本身不动）→ 必须照旧通过

⚠️ 第 3、4 条是本闸最要紧的两条：**它们守的是「闸门有没有真的在查」**。
若解析器某天因为表格改版而退化，最危险的结果不是报错，而是**静悄悄地全部通过**——
那正是 Batch 157 的「工具失败被当成零命中」，只是这次发生在判据自己身上。

每条注入都用 `assert` 钉死锚点：锚点失配即判**作废**，不进 PASS 也不进 FAIL
（Batch 162 的空转检测，此处从源头避开）。
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE = os.path.join(HERE, "verify-endpoints.py")
BASELINE = os.path.join(HERE, "baseline.py")
REF_REL = "20-reference.md"

PASS = VOID = FAIL = 0


def run(desc, want, expect_fail=True, want_rc=1, transform=None):
    global PASS, VOID, FAIL
    base = open(os.path.join(ROOT, REF_REL), encoding="utf-8").read()
    text = base
    if transform is not None:
        try:
            text = transform(base)
        except AssertionError as exc:
            print("  ✗ %s：锚点未命中，注入空转 → **本用例作废**（%s）" % (desc, exc))
            VOID += 1
            return

    tmp = tempfile.mkdtemp(prefix="beef-endp-selftest.")
    try:
        os.makedirs(os.path.join(tmp, "scripts"))
        # **必须连同 baseline.py 一起复制**（Batch 178 修，闸 17 抓出）：
        # 自 Batch 175 起被测闸门会 `from baseline import resolve_ref`；
        # 临时目录里没有它 → 闸门启动即 ModuleNotFoundError，**每一例都失败**，
        # **而 build-site.sh 仍然全绿**——反验坏掉不产生任何构建期信号。
        shutil.copy(BASELINE, os.path.join(tmp, "scripts", "baseline.py"))
        shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-endpoints.py"))
        with open(os.path.join(tmp, REF_REL), "w", encoding="utf-8") as fh:
            fh.write(text)
        r = subprocess.run([sys.executable, os.path.join("scripts", "verify-endpoints.py")],
                           cwd=tmp, capture_output=True, text=True)
        out = r.stdout + r.stderr
        if expect_fail and r.returncode == 0:
            print("  ✗ %s：闸门本应报错，却通过了" % desc); FAIL += 1
        elif expect_fail and r.returncode != want_rc:
            print("  ✗ %s：退出码 %d，期望 %d；实际：" % (desc, r.returncode, want_rc))
            print("      " + out.strip().split("\n")[-1][:120]); FAIL += 1
        elif expect_fail and want not in out:
            print("  ✗ %s：报错了但不是 [%s]；实际：" % (desc, want))
            print("      " + out.strip().split("\n")[-1][:120]); FAIL += 1
        elif not expect_fail and r.returncode != 0:
            print("  ✗ %s：本应放行却报错（误伤，rc=%d）：%s" % (desc, r.returncode, out.strip()[:150]))
            FAIL += 1
        else:
            print("  ✓ %s" % desc); PASS += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def t_live_missing(s):
    a = "| `GET /tasks` | 任务列表（分页/过滤） |"
    assert a in s, "锚点未命中：找不到 GET /tasks 那一行"
    return s.replace(a, "| `GET /api/绝对不存在的端点-xyz` | 反验注入：上游没有这个 |", 1)


def t_retired_registered(s):
    a = "| `POST /agent/runs` | **已下线**——旧内置 Agent 已从产品运行面退场 |"
    assert a in s, "锚点未命中：找不到 /agent/runs 那一行"
    # /tasks 上游确有注册——把它塞进「已下线」表，应被判「已下线却注册了」
    return s.replace(a, "| `POST /api/tasks` | 反验注入：上游确实注册了 /tasks |", 1)


def t_missing_anchor(s):
    a = "### 已下线端点"
    assert a in s, "锚点未命中：找不到「### 已下线端点」小节"
    out = s.replace(a, "### 下线端点（反验注入：真把锚点换掉）", 1)
    # 第一版注入写成「### 已下线端点（反验注入…）」——**它仍然包含原锚点**，
    # 子串判断照样命中，闸门正常通过，用例判「本应报错却通过了」。
    # 断言必须验的是「改完之后锚点真的不见了」，而不是「改之前它在」。
    assert a not in out.split("### v1.6.14 运行时核对新增")[0], \
        "注入无效：改完之后锚点仍在，锚点失配未被制造出来"
    return out


def t_empty_table(s):
    a = "**仍然存在：**"
    assert a in s, "锚点未命中：找不到「**仍然存在：**」"
    # 保留小节标题与下一个小节锚点，把中间整张表清空
    start = s.index(a) + len(a)
    end = s.index("### 已下线端点", start)
    return s[:start] + "\n（本表被反验注入清空）\n\n" + s[end:]


def t_benign_new_endpoint(s):
    a = "| `GET /health/live` · `/health/ready` · `/health/startup` |"
    assert a in s, "锚点未命中：找不到 health 那一行"
    return s.replace(a, a + "\n| `POST /api/tasks/:id/retry` | 反验注入：上游确有注册的新条目 |", 1)


def t_benign_prose(s):
    a = "任务列表（分页/过滤）"
    assert a in s, "锚点未命中：找不到 /tasks 的用途说明"
    return s.replace(a, "任务列表（分页/过滤）。反验注入：只改用途文字，端点本身不动", 1)


def main():
    r = subprocess.run([sys.executable, GATE], cwd=ROOT, capture_output=True, text=True)
    if r.returncode == 0:
        print("  ✓ 基线：真实手册通过（%s）" % r.stdout.strip().split("\n")[0][:70])
        globals()["PASS"] = globals()["PASS"] + 1
    else:
        print("  ✗ 基线：真实手册应当通过，rc=%d：%s" % (r.returncode, r.stdout.strip()[:150]))
        globals()["FAIL"] = globals()["FAIL"] + 1

    run("1) 现存表的端点上游没有（必须报）", "声明存在但上游没有注册", transform=t_live_missing)
    run("2) 已下线表的端点上游有（必须报）", "已下线却在生产路由里注册了", transform=t_retired_registered)
    run("3) 小节锚点失配（必须 rc=2 未能核对）", "缺少小节锚点", want_rc=2, transform=t_missing_anchor)
    run("4) 表被清空 / 解析退化（必须 rc=2，不能静默通过）", "解析出 0 条端点", want_rc=2, transform=t_empty_table)
    run("5) 不误伤：加一条上游确有注册的新端点（必须放行）", "全部与上游相符",
        expect_fail=False, transform=t_benign_new_endpoint)
    run("6) 不误伤：只改用途说明文字（必须放行）", "全部与上游相符",
        expect_fail=False, transform=t_benign_prose)

    print("=== 结果：通过 %d / 失败 %d / 作废 %d ===" % (PASS, FAIL, VOID))
    return 1 if (FAIL or VOID) else 0


if __name__ == "__main__":
    sys.exit(main())
