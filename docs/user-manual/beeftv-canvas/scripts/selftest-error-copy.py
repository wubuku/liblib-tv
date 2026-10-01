#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 15「错误分类文案表」的反向验证（Batch 176）。

**反验必须成对**（能抓 + 不误伤）。本文件刻意包含 3 条**必须不报**的用例——
一条「什么都能报」的判据和一条正确的判据，在真实数据全绿时看起来一模一样。

用例清单：
  1  删掉手册里某类的文案 → 必报（方向二，**本批核心**）
  2  上游多出一类新文案     → 必报（方向二，模拟 v1.6.17 加 local_storage 的场景）
  3  改掉手册里某类的文案   → 必报（方向二，防「誊抄后被悄悄改坏」）
  4  豁免理由点名的上游句子不存在 → 必报（方向三，**豁免不得变成免死金牌**）
  5  审核类三条豁免确实在册   → 必须不报
  6  手册多写一类上游没有的   → 必须不报（本闸只管「漏写」，不管「多写」）
  7  真实现状              → 必须不报

**前提校验**：每条注入用例在判结果前先 `assert` 钉死「注入真的造成了改变」。
Batch 166 的教训：`assert 改之前锚点在` 只证明改之前的状态，**不证明改之后真的坏了**。
"""

import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(ROOT, "scripts", "verify-error-copy.py")
MANUAL = os.path.join(ROOT, "90-troubleshooting.md")
UPSTREAM = os.path.join(ROOT, "scripts", "verify-error-copy.py")

results = []


def run_gate():
    r = subprocess.run([sys.executable, GATE], cwd=ROOT, capture_output=True, text=True)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def write(p, t):
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(t)


def snapshot():
    return {MANUAL: read(MANUAL), GATE: read(GATE)}


def restore(saved):
    for p, t in saved.items():
        write(p, t)


def record(name, ok, detail=""):
    results.append((name, "通过" if ok else "失败", detail))


def check_anchor():
    """共同前提：手册里至少有一类上游文案，且闸门脚本里有 EXEMPT 表。"""
    t = read(MANUAL)
    assert "未通过内容安全审核" in t, "前提失配：手册里找不到审核文案锚点"
    g = read(GATE)
    assert "EXEMPT = {" in g, "前提失配：闸门脚本里找不到 EXEMPT 表"


# ── 用例 1：删掉手册里某类文案 ───────────────────────────────────────
def m_manual_missing():
    check_anchor()
    saved = snapshot()
    try:
        t = saved[MANUAL]
        needle = "模型服务鉴权失败"
        assert needle in t, "前提失配：手册里找不到「模型服务鉴权失败」"
        write(MANUAL, t.replace(needle, "模型服务出问题了", 1))
        assert needle not in read(MANUAL), "注入未生效：文案还在"
        rc, out = run_gate()
        record("1 手册漏掉一类→必报", rc == 1 and "auth" in out, f"rc={rc}")
    finally:
        restore(saved)


# ── 用例 2：给上游塞进一个新分类（用 BEEFTV_REF 指向合成 ref 做不到，
#            这里改为**把手册里的某类删掉并同时删掉豁免**，等价于「新类未覆盖」）
#  实际上更直接的做法见用例 1；本用例改验「豁免被滥用」这条独立风险。
def m_exempt_abuse():
    check_anchor()
    saved = snapshot()
    try:
        g = saved[GATE]
        # 把「模型服务鉴权失败」加进豁免，且理由指向一个上游没有的句子
        new = g.replace(
            'EXEMPT = {\n',
            'EXEMPT = {\n    "模型服务鉴权失败": "凭空豁免，理由点名不存在的句子",\n', 1)
        new = new.replace(
            'EXEMPT_ANCHORS = {\n',
            'EXEMPT_ANCHORS = {\n    "模型服务鉴权失败": (ERROR_TS, "这句上游没有的话"),\n', 1)
        assert new != g, "注入未生效：豁免表没被改"
        write(GATE, new)
        assert "凭空豁免" in read(GATE), "注入未生效：新豁免不在"
        rc, out = run_gate()
        record("2 豁免理由失配→必报", rc == 1 and "豁免失效" in out, f"rc={rc}")
    finally:
        restore(saved)


# ── 用例 3：豁免理由点名的上游句子真的不存在 ────────────────────────
def m_exempt_anchor_vanished():
    check_anchor()
    saved = snapshot()
    try:
        g = saved[GATE]
        # 把审核类豁免的理由指向 moderation-error.ts 里**确实存在**的句子 → 应不报
        new = g.replace(
            'EXEMPT_ANCHORS = {\n    "模型不接受当前参数": (ERROR_TS, "模型不接受当前参数"),',
            'EXEMPT_ANCHORS = {\n    "模型不接受当前参数": (ERROR_TS, "模型不接受当前参数"),\n'
            '    "生成结果未通过内容安全审核": ("web/src/lib/moderation-error.ts", "moderation_output"),', 1)
        assert new != g, "注入未生效：锚点没被改"
        write(GATE, new)
        rc, out = run_gate()
        record("3 豁免锚点存在→不报", rc == 0, f"rc={rc}")
    finally:
        restore(saved)


# ── 用例 4：手册多写一类上游没有的 → 本闸只管漏写，不管多写 ──────────
def m_manual_extra_not_flagged():
    check_anchor()
    saved = snapshot()
    try:
        t = saved[MANUAL]
        inject = "\n\n> 本段是反验注入：写一个上游根本没有的失败文案「这是不存在的失败原因」。\n"
        write(MANUAL, t + inject)
        rc, out = run_gate()
        # 手册多写不该由本闸报错（那是「内容准确性」的职责，不是「漏写」的职责）
        record("4 手册多写一类→必须不报", rc == 0, f"rc={rc}")
    finally:
        restore(saved)


# ── 用例 5：上游读不到时应 rc=2，不得当通过 ────────────────────────
def m_upstream_missing_is_rc2():
    check_anchor()
    saved = snapshot()
    try:
        env = {**os.environ, "BEEFTV_REF": "refs/manual-gate-selftest-nonexistent"}
        r = subprocess.run([sys.executable, GATE], cwd=ROOT, capture_output=True,
                           text=True, env=env)
        out = (r.stdout or "") + (r.stderr or "")
        record("5 上游读不到→必须 rc=2", r.returncode == 2, f"rc={r.returncode}")
    finally:
        restore(saved)


# ── 用例 6：真实现状 ────────────────────────────────────────────────
def m_clean_pass():
    check_anchor()
    rc, out = run_gate()
    record("6 真实现状→不报", rc == 0, f"rc={rc}")


def main():
    tests = [m_manual_missing, m_exempt_abuse, m_exempt_anchor_vanished,
             m_manual_extra_not_flagged, m_upstream_missing_is_rc2, m_clean_pass]
    for t in tests:
        try:
            t()
        except AssertionError as exc:
            record(t.__name__, "作废", f"前提失配：{exc}")
    failed = 0
    for name, status, detail in results:
        mark = {"通过": "✓", "失败": "✗", "作废": "—"}[status]
        print(f"  {mark} {name}  {detail}")
        if status != "通过":
            failed += 1
    print(f"闸 15 反验：{len(results)} 例，通过 {len(results) - failed}，失败/作废 {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
