#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 19「批次账本行完整性」的反向验证（Batch 183）。

用例清单：
  1  批次表里再登记一次已存在的批次号   → 必报（方向一，本闸要抓的那件事）
  2  **跨表同号不得误报**              → 用真实文件里天然存在的样本，不注入
  3  批次号形态非法                    → 必报（方向二）
  4  读不到批次表（删掉小节标题）      → 必须 rc=2「未能核对」，不得当成通过
  5  真实现状                          → 不报
  6  数据行少一列（删掉状态格）        → 必报（方向三，Batch 216 新增）
  7  数据行多一列                      → **不得**报（多列归闸 8，钉住分工边界）
  8  表头自己少一列                    → 必报（表头缺列会让所有「少列」判断失去参照）

**用例 2 是本文件最要紧的一条，而且它不需要注入**：
`PROGRESS.md` 里**批次表之外**还有一张表，它有一行编号 `18`，而批次表里也有
`| 18 |`（Batch 18「可达升级两例」）。**闸 19 第一版就是全文件扫 `| 数字 |` 行，
于是它把这个天然样本报成了重复**——而那正是判据作者（我）自己写反了作用域。
现在这一例直接吃真实文件：**只要闸 19 的作用域又扩大到全文件，它立刻就会红。**

**用例 7 单独存在的理由**：它钉的是一道**分工边界**。批次表一行少列归本闸、
多列归闸 8（`verify-tables.py`）——两边合起来才覆盖「列数不对」的全部方向。
用例 6 保证本闸不是「什么都没查」，用例 7 保证它也**不是把闸 8 的活抢过来做**：
抢活不会立刻出错，但会让同一条缺陷在两处各报一次，而**两处报的行号与措辞不一样**，
下一个来查的人得先判断该信哪个。**分工没人守，半年后就只剩一个判据、另一半覆盖悄悄没了。**

**用例 8 单独存在的理由**：本闸的「少列」判据拿表头列数当参照，而表头列数是
**算出来的**（这样这张表哪天加一列也不会误报）。可一旦表头自己被删成一列，
判据会安静地拿 1 当参照、于是每一行都「不缺列」——**判据不会错，它只是再也不成立**。
这类自检不能省：Batch 215 的同款是纪律的批次标注整个删掉，判据当时报绿，
后来靠成对验证才发现「没写」和「写错」被混为一谈。

**用例 4 单独存在的理由**：`0 一致 / 1 不一致 / 2 未能核对` 三段退出码里，
「读不到」若返回 0，就等于**把手册删坏这件事报成一切正常**（Batch 168 起立的底线）。
"""

import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(ROOT, "scripts", "verify-batch-rows.py")
PROGRESS = os.path.join(ROOT, "PROGRESS.md")
SECTION = "## Batch 计划与状态"
ROW_RE = re.compile(r"^\|\s*([^|]*?)\s*\|")
# **必须与被验的闸用同一套切分**（Batch 216）：Batch 143 那行内容里有 `\\|\\|`
# 与带竖线的代码片段，用朴素 split("|") 数出来的列数与闸不一致，
# 于是「注入没生效」的断言会给出与真相相反的结论——**用例自己量错就等于没量**。
SPLIT = re.compile(r"(?<!\\)\|")

results = []


def run():
    r = subprocess.run([sys.executable, GATE], cwd=ROOT, capture_output=True, text=True)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def read():
    with io.open(PROGRESS, encoding="utf-8") as fh:
        return fh.read()


def write(t):
    with io.open(PROGRESS, "w", encoding="utf-8") as fh:
        fh.write(t)


def record(name, ok, detail=""):
    results.append((name, "通过" if ok else "失败", detail))


def check_anchor():
    t = read()
    assert SECTION in t, "前提失配：PROGRESS.md 里没有批次小节标题"
    assert "| 181 |" in t, "前提失配：批次表里找不到 181 行，账本结构变了"
    # 天然样本：批次表外必须真的有和批次表重号的行，否则用例 2 就测不到东西
    lines = t.split("\n")
    sec = lines.index(SECTION)
    start = next(i for i in range(sec, len(lines))
                 if ROW_RE.match(lines[i]) and ROW_RE.match(lines[i]).group(1) == "Batch")
    end = next(i for i in range(start + 1, len(lines)) if not lines[i].startswith("|"))
    inside = {ROW_RE.match(l).group(1) for l in lines[start + 2:end]
              if ROW_RE.match(l) and re.fullmatch(r"\d+[a-z]?", ROW_RE.match(l).group(1))}
    outside = {ROW_RE.match(l).group(1) for l in lines[end:]
               if ROW_RE.match(l) and re.fullmatch(r"\d+[a-z]?", ROW_RE.match(l).group(1))}
    cross = inside & outside
    assert cross, "前提失配：批次表外已没有与批次表重号的行，用例 2 失去意义"


def locate_batch_table_lines(lines):
    sec = lines.index(SECTION)
    start = next(i for i in range(sec, len(lines))
                 if ROW_RE.match(lines[i]) and ROW_RE.match(lines[i]).group(1) == "Batch")
    end = next(i for i in range(start + 1, len(lines)) if not lines[i].startswith("|"))
    return start, end


# ── 1 重复登记同一批次号 → 必报 ──────────────────────────────────────
def m_duplicate_must_report():
    check_anchor()
    orig = read()
    try:
        lines = orig.split("\n")
        start, end = locate_batch_table_lines(lines)
        victim = next(l for l in lines[start + 2:end] if l.startswith("| 181 |"))
        assert victim, "找不到 181 行"
        dup = "| 181 | 注入的重复登记（这行必须被判出来） | ✅ 完成 |"
        lines.insert(end - 1, dup)
        write("\n".join(lines))
        after = read()
        assert after.count("| 181 |") == 2, "前提失配：注入没生效（同一批次号仍只出现一次）"
        rc, out = run()
        ok = rc == 1 and "181" in out and "不止一次" in out
        record("1 重复批次号 → 必报", ok, f"rc={rc}")
    finally:
        write(orig)


# ── 2 跨表同号**不得**误报（吃真实文件里的天然样本，不注入）─────────
def m_cross_table_must_not_report():
    check_anchor()
    rc, out = run()
    # 判据若扫全文件，必然会把批次表外的 `18` 报成重复
    ok = rc == 0 and "不止一次" not in out
    record("2 跨表同号 → 不得误报（真实天然样本）", ok, f"rc={rc}")


# ── 3 批次号形态非法 → 必报 ──────────────────────────────────────────
def m_bad_shape_must_report():
    check_anchor()
    orig = read()
    try:
        lines = orig.split("\n")
        start, end = locate_batch_table_lines(lines)
        # 必须是**真的**越界形态：小写后缀只允许一位，`18cc` 越界；
        # 而 `18c` 反而是合法的（第一版这里就挑错了例子，判据报 0 是对的、
        # 错的是用例——**用例自己写错时，判据的沉默会被误当成判据坏了**）。
        lines.insert(end - 1, "| 18cc | 形态非法的批次号（小写后缀只允许一位） | ✅ 完成 |")
        write("\n".join(lines))
        after = read()
        assert "| 18cc |" in after, "前提失配：注入没生效"
        rc, out = run()
        ok = rc == 1 and "形态非法" in out
        record("3 批次号形态非法 → 必报", ok, f"rc={rc}")
    finally:
        write(orig)


# ── 4 读不到批次表 → 必须 rc=2，不得当成通过 ────────────────────────
def m_unreadable_must_be_rc2():
    check_anchor()
    orig = read()
    try:
        write(orig.replace(SECTION, "## Batch 计划与状态（被反验临时改名的标题）"))
        rc, out = run()
        ok = rc == 2 and "未能核对" in out
        record("4 读不到批次表 → 必须 rc=2 未能核对", ok, f"rc={rc}")
    finally:
        write(orig)


# ── 5 真实现状 ──────────────────────────────────────────────────────
def m_clean_pass():
    check_anchor()
    rc, out = run()
    record("5 真实现状 → 不报", rc == 0, f"rc={rc}")


# ── 6 数据行少一列 → 必报（Batch 216 新方向）─────────────────────────
def m_short_row_must_report():
    check_anchor()
    orig = read()
    try:
        lines = orig.split("\n")
        start, end = locate_batch_table_lines(lines)
        i = next(i for i in range(start + 2, end) if lines[i].startswith("| 181 |"))
        cells = SPLIT.split(lines[i].strip()[1:-1])
        assert len(cells) == 3, f"前提失配：181 行是 {len(cells)} 列，不是 3（账本结构变了）"
        lines[i] = "|" + "|".join(c[:] for c in cells[:2]) + "|"
        write("\n".join(lines))
        after = read().split("\n")[i]
        assert len(SPLIT.split(after.strip()[1:-1])) == 2, "前提失配：注入没生效"
        rc, out = run()
        ok = rc == 1 and "只有 2 列" in out and "181" in out
        record("6 数据行少一列 → 必报", ok, f"rc={rc}")
    finally:
        write(orig)


# ── 7 数据行多一列 → **不得**报（分工边界：多列归闸 8）────────────────
def m_extra_col_must_not_report():
    check_anchor()
    orig = read()
    try:
        lines = orig.split("\n")
        start, end = locate_batch_table_lines(lines)
        i = next(i for i in range(start + 2, end) if lines[i].startswith("| 181 |"))
        lines[i] = lines[i].rstrip() + " 多余的一格 |"
        write("\n".join(lines))
        after = read().split("\n")[i]
        assert len(SPLIT.split(after.strip()[1:-1])) == 4, "前提失配：注入没生效"
        rc, out = run()
        ok = rc == 0 and "只有" not in out
        record("7 数据行多一列 → 不得报（多列归闸 8）", ok, f"rc={rc}")
    finally:
        write(orig)


# ── 8 表头自己少一列 → 必报（参照没了，判据静悄悄失效）──────────────
def m_short_header_must_report():
    check_anchor()
    orig = read()
    try:
        lines = orig.split("\n")
        start, end = locate_batch_table_lines(lines)
        assert lines[start] == "| Batch | 内容 | 状态 |", "前提失配：表头不是预期的三列"
        lines[start] = "| Batch | 内容 |"
        write("\n".join(lines))
        rc, out = run()
        ok = rc == 1 and "表头" in out
        record("8 表头少一列 → 必报", ok, f"rc={rc}")
    finally:
        write(orig)


def main():
    tests = [m_duplicate_must_report, m_cross_table_must_not_report,
             m_bad_shape_must_report, m_unreadable_must_be_rc2, m_clean_pass,
             m_short_row_must_report, m_extra_col_must_not_report,
             m_short_header_must_report]
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
    print(f"闸 19 反验：{len(results)} 例，通过 {len(results) - failed}，失败/作废 {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
