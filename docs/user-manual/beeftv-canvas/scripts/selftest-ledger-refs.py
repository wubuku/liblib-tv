#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 21「账本交叉引用完整性」的反向验证（Batch 184）。

用例清单：
  1  环境记录声明一个批次表没有的批次号   → 必报（方向一）
  2  引用一个不存在的纪律编号              → 必报（方向二）
  3  **中文叙述与斜杠列举不得误报**        → 「纪律一百四十」「纪律 128/129/130」
  4  **散文里的假阳性样本不得误报**        → 真实文件天然样本，**不吃注入**
  5  **缺号不得误报**（环境记录实测缺 29/31）
  6  真实现状                            → 不报
  7  **非 AUDIT.md、标题不含「环境记录」三字的批次声明 → 必报**（Batch 216 放开的部分）
  8  **正文行里的 Batch N 不得误报**（Batch 216 钉住的边界：放开到正文行是 1 真 3 假）

**用例 4 是本文件最要紧的一条，而且它不吃注入**。本批探针共报出 12 个「悬空引用」，
逐个读原文后**只剩 2 个是真的**。剩下 10 个假阳性里，有两类就躺在真实文件里：

  · `PROGRESS.md` 的「**第六道闸 24 → 26 条**」——那是**断言条数**不是闸号；
  · `AUDIT.md` 的「**Batch 299 源站采样**」——那是**别的仓**（jimeng）的批次编号。

**只要判据的扫描面稍微大一点（去扫散文里的「闸 N」或「Batch N」），它立刻就会红。**
所以用例 4 吃真实文件：作用域一旦扩大，它当场就抓。

**用例 7 与用例 8 是一对，缺一不可（Batch 216）**。本批把方向一从
「`AUDIT.md` 里以『环境记录』三字开头的标题」放开成「全手册任意标题」，
**上线首跑就抓到 Batch 7 与 Batch 9 两处真漏登记**——它们的标题分别是
`## Gate B 回走记录（Batch 7，…）` 与 `## v1.5.9 → v1.6.6 增量审计（Batch 9，…）`，
**都是货真价实的环境记录，只是标题没照标准格式写**。

  · **用例 7 证明「放开」真的生效**：它往 `SOURCE_OBSERVATIONS.md`（不是 AUDIT.md）
    注入一个标题里**不含「环境记录」三字**的批次声明。旧判据对这一处是瞎的。
  · **用例 8 证明「没有放过头」**：实测把扫描面继续扩到**正文行**是 **1 真 3 假**
    ——真的那条是 Batch 55（后续三个批次反复写「替代 Batch 55 未遂的视觉取证」，
    而批次表里确实没有它），假的三个是 `Batch 299` / `Batch 288`（**别的仓 jimeng**
    的编号）与 `Batch 999`（Batch 215 记叙「把某条纪律的标注改成 Batch 999」时
    **谈论一个字符串**）。**3:1 的假阳性率就是不能上**，
    所以 Batch 55 是人工读的——**账本里如实写着这件事，不假装有守卫**。

**用例 8 的真正作用是防「好心」**：下一个人看到真缺陷是人工补的，
很可能顺手把判据扩到正文行去「自动化」，而那一天构建就会因为
`Batch 299` 这种叙述里的引用而红。**假失败比漏报更坏**（纪律 210）。

**用例 5 单独存在的理由**：环境记录编号**实测缺 29 与 31**，而**缺号不是错误**——
批次数与记录数本来就不必一一对应。**判据过严同样是错**
（Batch 139/141/142 的同一课），所以「不判连续」必须由反验钉住，否则下一个人
会好心加上连续性检查，然后有一天构建开始因为缺号而红。
"""

import io
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(ROOT, "scripts", "verify-ledger-refs.py")
PROGRESS = os.path.join(ROOT, "PROGRESS.md")
AUDIT = os.path.join(ROOT, "AUDIT.md")
RULES = os.path.join(ROOT, "AUDIT-RULES.md")
OBS = os.path.join(ROOT, "SOURCE_OBSERVATIONS.md")

results = []


def read(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def write(p, t):
    with io.open(p, "w", encoding="utf-8") as fh:
        fh.write(t)


def run(gate=GATE):
    r = subprocess.run([sys.executable, gate], capture_output=True, text=True)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def record(name, ok, detail=""):
    results.append((name, "通过" if ok else "失败", detail))


def check_anchor():
    t = read(PROGRESS)
    assert "## Batch 计划与状态" in t, "前提失配：PROGRESS.md 里没有批次小节"
    a = read(AUDIT)
    assert "## 环境记录" in a, "前提失配：AUDIT.md 里没有环境记录"
    r = read(RULES)
    assert re_discipline(r), "前提失配：AUDIT-RULES.md 里没有纪律条目"
    o = read(OBS)
    assert "（Batch 9，" in o, "前提失配：SOURCE_OBSERVATIONS.md 里没有「（Batch 9，」样本"


def re_discipline(text):
    import re
    return re.findall(r"^\d+\.\s+\*\*", text, re.M)


# ── 1 环境记录声明未登记的批次 → 必报 ────────────────────────────────
def m_unregistered_batch_must_report():
    check_anchor()
    orig = read(AUDIT)
    try:
        write(AUDIT, orig + "\n## 环境记录一百四十一（Batch 9999，2026-10-02，注入用例）\n\n- 注入\n")
        after = read(AUDIT)
        assert "Batch 9999" in after, "前提失配：注入没生效"
        rc, out = run()
        ok = rc == 1 and "9999" in out and "方向一" in out
        record("1 环境记录声明未登记的批次 → 必报", ok, f"rc={rc}")
    finally:
        write(AUDIT, orig)


# ── 2 引用不存在的纪律编号 → 必报 ────────────────────────────────────
def m_dangling_discipline_must_report():
    check_anchor()
    orig = read(PROGRESS)
    try:
        write(PROGRESS, orig + "\n这一行引用了纪律 9999，这条纪律并不存在。\n")
        after = read(PROGRESS)
        assert "纪律 9999" in after, "前提失配：注入没生效"
        rc, out = run()
        ok = rc == 1 and "9999" in out and "方向二" in out
        record("2 引用不存在的纪律编号 → 必报", ok, f"rc={rc}")
    finally:
        write(PROGRESS, orig)


# ── 3 中文叙述与斜杠列举不得误报 ─────────────────────────────────────
def m_chinese_narration_must_not_report():
    check_anchor()
    orig = read(PROGRESS)
    try:
        extra = ("\n叙述里说纪律一百四十、纪律一百三十八，"
                 "还有纪律 128/129/130 与纪律 101 的又一次应验——这些都不是悬空引用。\n")
        write(PROGRESS, orig + extra)
        rc, out = run()
        ok = rc == 0
        record("3 中文叙述/斜杠列举 → 不得误报", ok, f"rc={rc}")
    finally:
        write(PROGRESS, orig)


# ── 4 散文里的假阳性样本不得误报（真实天然样本，不吃注入）────────────
def m_prose_false_positives_must_not_report():
    check_anchor()
    p = read(PROGRESS)
    a = read(AUDIT)
    # 天然样本必须真的在文件里，否则这一例测了个空
    assert "第六道闸 24 → 26 条" in p, "前提失配：PROGRESS.md 里没有「第六道闸 24 → 26 条」样本"
    assert "Batch 299" in a, "前提失配：AUDIT.md 里没有「Batch 299」样本"
    rc, out = run()
    ok = rc == 0
    record("4 散文假阳性样本 → 不得误报（真实天然样本）", ok, f"rc={rc}")


# ── 5 缺号不得误报 ──────────────────────────────────────────────────
def m_numbering_gap_must_not_report():
    check_anchor()
    orig = read(AUDIT)
    try:
        # 造一条编号跳号的记录：缺号是常态，判据不得因此报红
        write(AUDIT, orig + "\n## 环境记录一百四十二（Batch 12，2026-10-02，注入的跳号记录）\n\n- 注入\n")
        rc, out = run()
        ok = rc == 0
        record("5 环境记录编号缺号 → 不得误报", ok, f"rc={rc}")
    finally:
        write(AUDIT, orig)


# ── 7 非 AUDIT.md、标题不含「环境记录」的批次声明 → 必报 ───────────────
def m_arbitrary_title_must_report():
    check_anchor()
    orig = read(OBS)
    try:
        write(OBS, orig + "\n## 注入用例小节（Batch 9998，2026-10-02，注入）\n\n- 注入\n")
        after = read(OBS)
        assert "（Batch 9998，" in after, "前提失配：注入没生效"
        rc, out = run()
        ok = rc == 1 and "9998" in out and "SOURCE_OBSERVATIONS.md" in out
        record("7 任意标题声明未登记批次 → 必报", ok, f"rc={rc}")
    finally:
        write(OBS, orig)


# ── 8 正文行里的 Batch N 不得误报（钉住「不扫正文行」这条边界）──────
def m_prose_batch_must_not_report():
    check_anchor()
    orig = read(OBS)
    try:
        write(OBS, orig + "\n这里在正文里提到 Batch 9998，只是在叙述，不是一次登记。\n")
        rc, out = run()
        ok = rc == 0 and "9998" not in out
        record("8 正文行里的 Batch N → 不得误报", ok, f"rc={rc}")
    finally:
        write(OBS, orig)


# ── 6 真实现状 ──────────────────────────────────────────────────────
def m_clean_pass():
    check_anchor()
    rc, out = run()
    record("6 真实现状 → 不报", rc == 0, f"rc={rc}")


def main():
    tests = [m_unregistered_batch_must_report, m_dangling_discipline_must_report,
             m_chinese_narration_must_not_report, m_prose_false_positives_must_not_report,
             m_numbering_gap_must_not_report, m_clean_pass,
             m_arbitrary_title_must_report, m_prose_batch_must_not_report]
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
    print(f"闸 21 反验：{len(results)} 例，通过 {len(results) - failed}，失败/作废 {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
