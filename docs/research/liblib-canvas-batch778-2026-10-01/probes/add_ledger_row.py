#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""往台账追加 Batch 778 一行。

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
BATCH = 778

ROW = (
    "| Batch 778 | "
    "**`Cmd+Z` 在检查器控件上的早退是「按设计」还是「缺陷」** —— 777 的 D1d "
    "只回答了两个问题里的一个（桌的分支够不够得着），且样本是 **n=1 的 range "
    "滑杆**（它的 `fovInput` 臂 = `[data-director-camera-fov]` = "
    "`DirectorInspector.tsx:1646` 的 `type=\"range\"`）⟹ 我 778 规划时把"
    "「只测了 range」误当成「只有 range 是真空」 | ★ **规划假设的前半被否掉、"
    "后半被反转。** 拆成 Q-doc / Q-native 两个独立问题后："
    "**Q-doc 两族都够不着**（守卫 `DirectorDesk.tsx:487` 早于 Cmd+Z `:506`，"
    "且判据 `:475-480` 只看 tagName、**不看 `type`**）⟹ `delWhileFocused` "
    "两族**完全同构**（道具没回来、`past` 1→1、`future` 0→0、`lastCommand` "
    "连 `UNDO` 都不出现）⟹ **D1d 范围没有被收窄，是全部 53 个控件** —— "
    "**input 的文本撤销栈里没有「删了一个对象」这件事**；"
    "**Q-native 只有 range 是死键**（`native` 臂 number `7.5→4.8` 回退、"
    "range `48→48` 不回退，两族 `lastCommand` 都停在原处 ⟹ 桌的键处理"
    "**根本没被触到**）⟹ **26 个** range 族滑杆是死键且零反馈（缺陷 D1f）。"
    "**被反转的是修法授权**：`docAfterBlur` 两族都 `future` 0→1 ⟹ 一次 blur "
    "提交占掉**唯一**的撤销槽 ⟹ 守卫在 number 族上是**承重墙**，整体去掉会让"
    "number 用户输入后按 `Cmd+Z` **撤掉上一个文档动作**（数据错）⟹ "
    "**修法必须按控件类型分流**，而分流判据**同仓已有先例**"
    "（`useDirectorGestureBoundary.ts:82-90` 的 `onPointerUp` 已按 "
    "`type === \"number\"` 分派）。**更正 C778-1**；教训 R123–R128。"
    "验收 69/69、阴性对照 12/12（含 4 条**改源码**的静态对照）。"
    "**本批未改 `src/`**；★ **真的执行了破坏性删除**（用户目标允许有副作用的 "
    "CRUD），但每格开头清 localStorage ⟹ 不留残留；未用 `--no-verify`，"
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
