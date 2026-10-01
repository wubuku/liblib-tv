#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 14「取证基线自洽」的反向验证（Batch 175）。

**反验必须成对**（纪律：能抓 + 不误伤）。只做正向的话，
一个「什么都能通过」的判据会被记成 4/4 通过——本文件刻意包含 2 条**必须不报**的用例。

用例清单：
  1  基线声明缺失（删掉「### 取证基线」小节）        → 必报（方向一/二）
  2  基线只有版本没有提交                            → 必报（方向一）
  3  提交号写成上游不存在的值                        → 必报（方向二）
  4  README 适用版本与基线不一致                      → 必报（方向三）
  5  某闸把 ref 写死回浮动的 origin/main             → 必报（方向四，**本批核心**）
  6  闸门脚本里**注释/docstring**提到 origin/main     → **必须不报**（方向四的豁免）
  7  baseline.py 自身提到 origin/main                → **必须不报**（豁免文件）
  8  真实上游下全绿                                  → 不报（不误伤现状）

**前提校验**：每条注入用例在判结果前，先用 assert 钉死「注入真的造成了破坏」。
Batch 166 的教训：`assert 改之前锚点在` 只证明改之前的状态，不证明改之后真的坏了；
**锚点失配的用例一律记「作废」而不是「通过」**。
"""

import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(ROOT, "scripts", "verify-baseline.py")
REFERENCE = "20-reference.md"
README = "README.md"

results = []


def run_gate(cwd, env=None):
    e = dict(os.environ)
    e.update(env or {})
    r = subprocess.run([sys.executable, os.path.join(cwd, "scripts", "verify-baseline.py")],
                       cwd=cwd, capture_output=True, text=True, env=e)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def read(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as fh:
        return fh.read()


def write(p, text):
    with open(os.path.join(ROOT, p), "w", encoding="utf-8") as fh:
        fh.write(text)


def snapshot():
    """把会被注入的文件按内容存档，测试后原样还原。"""
    names = [REFERENCE, README, "scripts/verify-feature-flags.py"]
    return {n: read(n) for n in names}


def restore(saved):
    for n, t in saved.items():
        write(n, t)


def record(name, ok, detail=""):
    results.append((name, "通过" if ok else "失败", detail))


def check_baseline_anchor():
    """所有注入用例的共同前提：基线小节确实存在且可解析。"""
    text = read(REFERENCE)
    assert "### 取证基线" in text, "前提失配：20-reference.md 里找不到「### 取证基线」锚点"
    assert re.search(r"^-\s*\*\*版本\*\*[：:]", text, re.M), "前提失配：基线小节缺「版本」字段"
    assert re.search(r"^-\s*\*\*提交\*\*[：:]", text, re.M), "前提失配：基线小节缺「提交」字段"


# ── 用例 1：删掉基线小节 ──────────────────────────────────────────────
def m_missing_baseline_section():
    check_baseline_anchor()
    saved = snapshot()
    try:
        text = saved[REFERENCE]
        i = text.index("### 取证基线")
        j = text.index("\n## ", i)
        write(REFERENCE, text[:i] + text[j:])
        after = read(REFERENCE)
        assert "### 取证基线" not in after, "注入未生效：小节标题仍在"
        rc, out = run_gate(ROOT)
        record("1 基线声明缺失→必报", rc == 1 and "取证基线" in out,
               f"rc={rc}")
    finally:
        restore(saved)


# ── 用例 2：只有版本没有提交 ─────────────────────────────────────────
def m_missing_commit_field():
    check_baseline_anchor()
    saved = snapshot()
    try:
        text = saved[REFERENCE]
        new = re.sub(r"^-\s*\*\*提交\*\*[：:].*\n", "", text, count=1, flags=re.M)
        assert new != text, "注入未生效：提交字段行没被删掉"
        write(REFERENCE, new)
        assert not re.search(r"^-\s*\*\*提交\*\*[：:]", read(REFERENCE), re.M), \
            "注入未生效：提交字段仍在"
        rc, out = run_gate(ROOT)
        record("2 基线缺提交字段→必报", rc == 1 and "提交" in out, f"rc={rc}")
    finally:
        restore(saved)


# ── 用例 3：提交号不存在 ─────────────────────────────────────────────
def m_commit_not_exist():
    check_baseline_anchor()
    saved = snapshot()
    try:
        text = saved[REFERENCE]
        new = re.sub(r"^-\s*\*\*提交\*\*[：:]\s*`?([0-9a-f]{7,40})`?",
                     "- **提交**：`deadbee1`", text, count=1, flags=re.M)
        assert new != text, "注入未生效：提交号没被替换"
        write(REFERENCE, new)
        assert "deadbee1" in read(REFERENCE), "注入未生效：新提交号不在"
        rc, out = run_gate(ROOT)
        record("3 提交号不存在→必报", rc == 1 and "不存在" in out, f"rc={rc}")
    finally:
        restore(saved)


# ── 用例 4：README 与基线版本不一致 ─────────────────────────────────
def m_readme_version_mismatch():
    saved = snapshot()
    try:
        text = saved[README]
        m = re.search(r"(适用版本[：:]\s*BeefTV\s*`?)v\d+\.\d+\.\d+", text)
        assert m, "前提失配：README 里找不到适用版本行"
        new = text[:m.start()] + m.group(1) + "v1.6.99" + text[m.end():]
        write(README, new)
        assert "v1.6.99" in read(README), "注入未生效：README 版本没改"
        rc, out = run_gate(ROOT)
        record("4 README 版本不一致→必报", rc == 1 and "方向三" in out, f"rc={rc}")
    finally:
        restore(saved)


# ── 用例 5：把某闸的 ref 写死回浮动 origin/main（本批核心）──────────
def m_gate_reverts_to_floating_ref():
    saved = snapshot()
    try:
        target = "scripts/verify-feature-flags.py"
        text = saved[target]
        m = re.search(r'^REF\s*=.*$', text, re.M)
        assert m, "前提失配：verify-feature-flags.py 里找不到 REF 赋值行"
        new = text[:m.start()] + 'REF = "origin/main"' + text[m.end():]
        write(target, new)
        assert 'REF = "origin/main"' in read(target), "注入未生效：REF 没被写成浮动 ref"
        rc, out = run_gate(ROOT)
        record("5 闸门写死浮动 ref→必报", rc == 1 and "方向四" in out, f"rc={rc}")
    finally:
        restore(saved)


# ── 用例 6：注释/docstring 里提到 origin/main —— 必须**不报** ────────
def m_comment_mention_not_flagged():
    saved = snapshot()
    try:
        target = "scripts/verify-feature-flags.py"
        text = saved[target]
        inject = ('\n# 历史说明：本闸过去把 ref 写死成 origin/main（浮动），'
                  'Batch 175 起改用 baseline.resolve_ref()。\n'
                  'def _doc_probe():\n'
                  '    """这里提到 origin/main 只是文档字符串，不参与 ref 解析。"""\n'
                  '    return None\n')
        write(target, text + inject)
        rc, out = run_gate(ROOT)
        ok = rc == 0 and "方向四" not in out
        record("6 注释/docstring 提及→必须不报", ok, f"rc={rc}")
    finally:
        restore(saved)


# ── 用例 7：baseline.py 自身提到 origin/main —— 必须不报 ─────────────
def m_baseline_module_exempt():
    saved = snapshot()
    try:
        text = read("scripts/baseline.py")
        assert "origin/main" in text, "前提失配：baseline.py 里没有 origin/main 字样可豁免"
        rc, out = run_gate(ROOT)
        record("7 baseline.py 自身提及→必须不报", rc == 0 and "方向四" not in out, f"rc={rc}")
    finally:
        restore(saved)


# ── 用例 8：现状全绿，不误伤 ────────────────────────────────────────
def m_clean_pass():
    check_baseline_anchor()
    rc, out = run_gate(ROOT)
    record("8 真实现状→不报", rc == 0, f"rc={rc}")


def main():
    tests = [m_missing_baseline_section, m_missing_commit_field, m_commit_not_exist,
             m_readme_version_mismatch, m_gate_reverts_to_floating_ref,
             m_comment_mention_not_flagged, m_baseline_module_exempt, m_clean_pass]
    failed = 0
    for t in tests:
        try:
            t()
        except AssertionError as exc:
            record(t.__name__, "作废", f"前提失配：{exc}")
    for name, status, detail in results:
        mark = {"通过": "✓", "失败": "✗", "作废": "—"}[status]
        print(f"  {mark} {name}  {detail}")
        if status != "通过":
            failed += 1
    print(f"闸 14 反验：{len(results)} 例，通过 {len(results) - failed}，失败/作废 {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
