#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""往台账追加 Batch 781 一行。

★ 三条硬规则（每条都踩过坑）：
  1. **行首是 `| Batch 778 |`** —— 不是裸数字 ⟹ 不会被 pre-commit 的
     `added_batch_numbers()`（正则 `^\\+\\|\\s*(\\d+)[a-z]?\\s*\\|`）认成批次号。
  2. **恰好 4 个竖线**（3 列）。
  3. **0 个 U+FFFD**（台账历史里有 9 处，**不动**；新行写盘前必须 assert 为 0）。
★ 追加时 `sep` 不能省：末行可能有换行也可能没有，兜底两种情况。
"""
import pathlib
import re
import sys

LEDGER = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv"
                      "/docs/research/VERIFICATION_LEDGER.md")
FFFD = "�"
BATCH = 781

ROW = (
    "| Batch 781 | "
    "**补上 780 矩阵的最后一行**（`Meta+c`/`Meta+v`，780 显式标注为"
    "「本批未测」）并回答一个更要紧的问题：**按 780 的判据放行，会不会引入"
    "新伤害**？ | ★ **① 最后一行测出来了**：gesture 臂 8/8 次事件**到达 "
    "window** 而 `lastCommand` 既不是 `COPY_SELECTION` 也不是 "
    "`PASTE_CLIPBOARD` ⟹ `:487` 照样吞 ⟹ 那一行不再是「凭判据推出来的」。"
    "★ **② 放行安全**：`copyDirectorSelection` 只写**内部** "
    "`clipboard: DirectorClipboardPacketV1`（`:3941`），而**扫了 director 面 "
    "28 个文件，`navigator.clipboard`/`writeText`/`readText` 命中 0 处** ⟹ "
    "**放行不会碰系统剪贴板** ⟹ 矩阵里**不存在**那一列。★ 该搜索**必须带作用域**"
    "：`app/frameos/` 与 `components/jimeng/` 里都有 `navigator.clipboard`，"
    "全仓搜会得到**完全相反**的结论而否掉一个正确的修法。★ **更正 C781-2："
    "我预测「静默的死键（live 区无任何文案）」被否掉** —— 实测 live 区是"
    "**占位文案「无命令反馈」**，且 `lastCommand`/`lastDisp` **都是陈旧值**；"
    "对照臂 `Meta+v` 是 `NOOP` 且给**真实消息** ⟹ 桌**有**拒绝反馈通道，"
    "**差异在「命令有没有产生」而不是「有没有通道」**。★ **D1f 键种清单补全为 4 个**；"
    "C/V 该不该放行属**新增功能**而非修缺陷 ⟹ 单列为产品决定。验收见下、"
    "阴性对照 10/10（含 1 条**注入假文件**验「带作用域搜索」+ 3 条改源码）。"
    "**本批未改 `src/`**，无注入，**不做任何破坏性操作**；未用 `--no-verify`，"
    "未跑别人的 build-site.sh |"
)


def main():
    txt = LEDGER.read_text(encoding="utf-8")
    existing = [ln for ln in txt.split("\n")
                if re.match(r"^\|\s*Batch\s+%d\s*\|" % BATCH, ln)]
    if existing:
        print("Batch %d 行已存在（%d 行），不重复追加" % (BATCH, len(existing)))
        return 0
    # ── 写盘前自检 ──
    assert ROW.count("|") == 4, "竖线数 %d，应恰好 4" % ROW.count("|")
    assert FFFD not in ROW, "新行含 %d 个 U+FFFD" % ROW.count(FFFD)
    assert not re.match(r"^\+\|\s*\d+[a-z]?\s*\|", ROW), \
        "行首是裸数字 ⟹ 会被 pre-commit 的 added_batch_numbers 认成批次号"
    assert ROW.startswith("| Batch %d |" % BATCH), "行首形状不对"
    # ── 追加：`sep` 兜底「末行有/无换行」两种情况 ──
    sep = "" if txt.endswith("\n") else "\n"
    LEDGER.write_text(txt + sep + ROW + "\n", encoding="utf-8")
    # ── 落盘后复读自检 ──
    after = LEDGER.read_text(encoding="utf-8")
    got = [ln for ln in after.split("\n")
           if re.match(r"^\|\s*Batch\s+%d\s*\|" % BATCH, ln)]
    assert len(got) == 1, "追加后匹配到 %d 行" % len(got)
    assert got[0].count("|") == 4, "落盘后竖线数 %d" % got[0].count("|")
    assert FFFD not in got[0], "落盘后含 U+FFFD"
    print("已追加 Batch %d：%d 字符 / %d 竖线 / 0 个 U+FFFD"
          % (BATCH, len(got[0]), got[0].count("|")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
