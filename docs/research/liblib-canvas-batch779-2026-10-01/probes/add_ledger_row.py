#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""往台账追加 Batch 779 一行。

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
BATCH = 779

ROW = (
    "| Batch 779 | "
    "**验 776 授权修法 (a) 的依据本身** —— 776 测到「第 2/3 次 Escape 毫无作用」"
    "并据此更正 C776-1 为「只改 (a) = 按两次；两处都改 = 按一次」，"
    "**授权 (a) 可单独做**；但它**从没问第 2/3 次到底被谁吞掉** | ★ "
    "**机制归属对、推论错 ⟹ (a) 不能单独做。** 判别器：window 上晚注册 keydown "
    "监听器 + 一个 **capture 相位**的 document 监听器（capture 任何 "
    "`stopPropagation` 都拦不住 ⟹ `cap` 是「按键真的送达了」的正向对照）。"
    "**第一道吞嘴** = hook `:94-95` 的无条件 preventDefault+stopPropagation："
    "gesture 臂 6/6 次按压 `win=0`（事件**从没到达 window**）⟹ 776 的归属正确；"
    "**第二道吞嘴** = 桌 `:487` 的 isEditable 守卫：hook 对非 Escape 键**只** "
    "`begin()` 不 stopPropagation（`:99-107`）⟹ 改按 `Meta+z`，3/3 次**到达了 "
    "window** 而 `lastCommand` **始终不是 `UNDO`** ⟹ **桌的 `:487` 把它吞了**。"
    "⟹ 修法 (a) 只动第一道 ⟹ 第 2 次按压从「被 hook 吞」变成「被 `:487` 吞」⟹ "
    "**对用户可见行为净为零**。★ 而且**「两处」是三个问题**：桌的阶梯 `:553` "
    "**自己就有一档 `activeGesture`** ⟹ 即使前两处都改完，第 1 次按压**仍然只"
    "取消手势**、不会关掉导出面板 ⟹ 「按一次就关掉面板」需要第三个**产品决定**"
    "（有活动手势时 Escape 要不要也关层）。**更正 C779-1、C779-2**；"
    "与 778 独立汇合：修法必须**按控件类型分流**。缺陷 D1g（中-高·授权依据缺陷）；"
    "教训 R129–R133。验收见下、阴性对照 11/11（含 5 条**改源码**的静态对照）。"
    "**本批未改 `src/`**，无注入，不涉及删除；未用 `--no-verify`，"
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
