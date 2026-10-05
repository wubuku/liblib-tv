#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""往台账追加 Batch 780 一行。

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
BATCH = 780

ROW = (
    "| Batch 780 | "
    "**验 D1d 严重度的前提** —— 777 写「刚在输入框里改完数、**顺手删个对象**"
    "是很自然的落点」，但它的探针**用的是鼠标点行删除按钮**（R119 就是为此立的）"
    "⟹ 那句「顺手」**从来没被测过** | ★ **预测成立 ⟹ 「顺手」不成立，"
    "D1d 严重度由「中-高」下调为「中」。** 源码说 `Delete`/`Backspace` 的处理在 "
    "`DirectorDesk.tsx:517`，**排在 `:487` 那道 `isEditable` 守卫之后**。"
    "**gesture 臂 8/8 次**（2 族 × 2 键 × 2 次按压）：`cap=1, win=1` ⟹ 事件"
    "**到达了 window**，而对象数 **5→5**、`past` 仍=0、`lastCommand` 停在 "
    "`GESTURE_BEGIN` ⟹ **桌的 `:487` 把它吞了、什么都没删**；"
    "★ **对照臂 2/2 次**在非输入落点上**真的删掉**（5→4、`DELETE_OBJECTS`、"
    "`past` 0→1）⟹ 判别力成立，「删不掉」不是探针删不动。"
    "⟹ 真实序列是**键入 → 鼠标点删除按钮 → 点回控件 → `Cmd+Z`**，四步且刻意。"
    "★ **顺带把 `:487` 的放行判据定成一张有证据的矩阵**："
    "**不是「控件类型」，是「该键在该类型上有没有原生兜底」** —— "
    "`Escape` 两族都无兜底 ⟹ 都该放行（779）；`Meta+z` 与 `Delete/Backspace` "
    "在 number 有兜底（文本撤销 / 删字符，778 已证 `:487` 是承重墙）、"
    "在 range 没有 ⟹ **只 range 该放行**。⟹ **D1f 与本批合并**（同一守卫、"
    "同样 26 个滑杆、两种键）。★ `Meta+c`/`Meta+v` **本批未测** ⟹ 不进矩阵。"
    "**更正 C780-1、C780-2**；教训 R134–R137。验收见下、阴性对照 7/7。"
    "**本批未改 `src/`**，无注入；★ gesture 臂**没有真的删除**，"
    "唯一的破坏性操作是对照臂那一次。未用 `--no-verify`，未跑别人的 "
    "build-site.sh |"
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
