#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 22「手册正文引号文案标点漂移」的反向验证（Batch 185）。

用例清单：
  1  注入一处标点漂移（把正确文案改成少一个逗号）   → 必报
  2  注入一处**括号**漂移                            → 必报
  3  **不误伤**：手册自己的术语（「画布文件夹」这类两词撞出来的）→ 不得报
  4  **不误伤**：`/` 与 `→` 并列两个独立文案的写法    → 不得报
  5  自检探针失配（ref 指到没有该文案的版本）        → 必须 rc=2「未能核对」
  6  真实现状                                        → 不报

**用例 3 是本闸第一版真实误报过的一条**：第一版把**整份语料**归一化后做子串匹配，
于是「画布文件夹」也能在上游对上（某处「画布」后面紧接着出现「文件夹」）——
**一条根本没有标点可漂移的纯文字被报成标点漂移**。修法是归一化比对落在
**源码的字符串字面量集合**上（字面量内部不会出现拼接）。用例 3 钉住这个修法。

**用例 5 单独存在的理由**：判据的方向二拿一条**只存在于 backend 的**已知文案当探针，
若它在上游语料里找不到，说明语料读取或 ref 出了问题。**此时必须 rc=2**——
**不能让判据在一个空语料上安静地全绿**（纪律 101：解析器退化必须表现为失败，不是通过）。
"""

import io
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(ROOT, "scripts", "verify-quote-punct.py")
README = os.path.join(ROOT, "README.md")
CONCEPTS = os.path.join(ROOT, "30-concepts.md")
DRIFT_BASE = "视频已生成，但暂时无法取回"     # 上游逐字原文
INJECTED = "视频已生成但暂时无法取回"        # 少一个逗号 —— 本闸要抓的形态

results = []


def read(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def write(p, t):
    with io.open(p, "w", encoding="utf-8") as fh:
        fh.write(t)


def run(env=None):
    e = dict(os.environ)
    e.update(env or {})
    r = subprocess.run([sys.executable, GATE], cwd=ROOT, capture_output=True, text=True, env=e)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def record(name, ok, detail=""):
    results.append((name, "通过" if ok else "失败", detail))


def check_anchor():
    t = read(README)
    assert DRIFT_BASE in t, "前提失配：README.md 里找不到上游逐字原文 %s" % DRIFT_BASE
    c = read(CONCEPTS)
    assert "画布文件夹" in c, "前提失配：30-concepts.md 里找不到「画布文件夹」样本"


# ── 1 少一个逗号 → 必报 ─────────────────────────────────────────────
def m_missing_comma_must_report():
    check_anchor()
    orig = read(README)
    try:
        write(README, orig.replace(DRIFT_BASE, INJECTED))
        assert INJECTED in read(README), "前提失配：注入没生效"
        rc, out = run()
        ok = rc == 1 and "标点漂移" in out
        record("1 少一个逗号 → 必报", ok, f"rc={rc}")
    finally:
        write(README, orig)


# ── 2 多一个括号 → 必报 ─────────────────────────────────────────────
def m_extra_paren_must_report():
    check_anchor()
    orig = read(README)
    try:
        injected = DRIFT_BASE.replace("，尚未", "（尚未")
        bad = "本地任务保存失败（尚未提交生成）"
        write(README, orig.replace(DRIFT_BASE, bad))
        assert bad in read(README), "前提失配：注入没生效"
        rc, out = run()
        ok = rc == 1 and "标点漂移" in out
        record("2 多一个括号 → 必报", ok, f"rc={rc}")
    finally:
        write(README, orig)


# ── 3 手册自己的术语不得误报（两词撞出来的纯文字）────────────────────
def m_own_term_must_not_report():
    check_anchor()
    rc, out = run()
    ok = rc == 0 and "画布文件夹" not in out
    record("3 手册自己的术语 → 不得误报（第一版真实误报过）", ok, f"rc={rc}")


# ── 4 `/` 与 `→` 并列写法不得误报 ────────────────────────────────────
def m_joined_writing_must_not_report():
    check_anchor()
    # 样本**跨全部页面**找：`/` 写法在 90-troubleshooting.md、`→` 在 README/快速开始。
    # 第一版只在 README 里找，于是这一例**作废**——而作废必须计入失败，
    # 否则「不误伤」那一半就等于没测（Batch 178：反验静悄悄失效只产生沉默）。
    pages = ["README.md", "00-quickstart.md", "20-reference.md",
             "30-concepts.md", "90-troubleshooting.md", "PUBLISH.md"]
    all_text = "".join(read(os.path.join(ROOT, x)) for x in pages)
    assert re.search(r"「[^」]*→[^」]*」", all_text), "前提失配：全部页面里找不到 → 并列样本"
    assert re.search(r"「[^」]*\u002f[^」]*」", all_text), "前提失配：全部页面里找不到 / 并列样本"
    rc, out = run()
    ok = rc == 0
    record("4 「/」「→」并列写法 → 不得误报", ok, f"rc={rc}")


# ── 5 自检探针失配 → 必须 rc=2 ──────────────────────────────────────
def m_probe_mismatch_must_be_rc2():
    check_anchor()
    # 指到一个早于该文案的版本：backend 里那条是后加的，
    # 探针应当找不到 → 判据必须说「未能核对」而不是「全部通过」
    rc, out = run(env={"BEEFTV_REF": "be409634"})
    ok = rc == 2 and "未能核对" in out
    record("5 自检探针失配 → 必须 rc=2 未能核对", ok, f"rc={rc}")


# ── 6 真实现状 ──────────────────────────────────────────────────────
def m_clean_pass():
    check_anchor()
    rc, out = run()
    record("6 真实现状 → 不报", rc == 0, f"rc={rc}")


def main():
    tests = [m_missing_comma_must_report, m_extra_paren_must_report,
             m_own_term_must_not_report, m_joined_writing_must_not_report,
             m_probe_mismatch_must_be_rc2, m_clean_pass]
    for t in tests:
        try:
            t()
        except AssertionError as exc:
            record(t.__name__, "作废", f"前提失配：{exc}")
    failed = 0
    for name, status, detail in results:
        mark = {"通过": "✓", "失败": "✗", "作废": "—"}[status]
        print(f"  {mark} {name}  {detail}")
        # **「作废」必须计入失败**——它意味着这一例什么都没测，
        # 而反验一旦在某处空转，报出来的是「通过」，不是「我没测」（纪律 102）
        if status != "通过":
            failed += 1
    print(f"闸 22 反验：{len(results)} 例，通过 {len(results) - failed}，失败/作废 {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
