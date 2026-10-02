#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二十道闸：文本文件的编码完整性（Batch 183 新增）。

背景（Batch 183）：修 Batch 182 账本时，在 `AUDIT-RULES.md` 第 1299 行撞见
`顺带说明为什么方向四a（非␣␣的必须真超过阈值）`——**两个 U+FFFD 替换字符**。
全树扫了一遍，同类损坏共 **3 处**，分别出自 **Batch 133 / 170 / 181**：

  · `scripts/selftest-unreachable.sh` 第 4 行（`# 三处修正，都是被自己的失败教会␣␣：`）
  · `scripts/selftest-unreachable-fix-33-fixture-writer.py` 第 8 行
  · `AUDIT-RULES.md` 第 1299 行

**三处都在注释与文档里，没有一处损坏代码**——所以 18 道闸全绿、脚本照常运行、
构建照常成功。**这就是它能静躺 50 个批次的原因**：这种损坏
**不产生任何错误信号，它只是让一小段字变得不可读**，而那句话周围的字都还正常，
读的人只会当成排版跳过去。

值得注意的是后两处**在验证设施里**——一份反验驱动脚本、一份注入夹具的说明。
**看守器自己的注释也会烂，而看守器不会报告自己烂。**

判据两个方向，外加一条廉价但可靠的：

  1. **必须是合法 UTF-8**（解码失败即报）。本手册全是 UTF-8，不存在别的编码，
     所以「解不出来」只可能意味着文件坏了。
  2. **不得含 U+FFFD 替换字符**（方向一抓不到它：带 U+FFFD 的文件**是**合法 UTF-8，
     解码成功得很——`EF BF BD` 就是 U+FFFD 自己的合法编码。**文件可以完全合法，
     同时内容已经被替换过了**，这是这一类损坏最唬人的地方）。
  3. **不得含 NUL 字节**（`\x00`）。它同样解码得出来，同样不报错，
     而它出现在文本文件里只可能是截断或写坏的产物。

**为什么用扩展名白名单，而不用「试着解码一次」**（本闸最容易写错的一处）：
`screenshots/.DS_Store` 里有一个 `0x80` 字节，**试解码会把它报成坏 UTF-8**——
而那是个二进制文件，`.gitignore` 早就管了它，它坏不坏与本手册无关。
**判据把不相干的东西报成异常，人就会学会忽略它**。
**还有一处同类陷阱，本闸第一版就踩了**：判据源码里若直接写死 U+FFFD 这个字面量，
**它会在自己身上触发**（闸 20 上线首跑报的就是这个文件）。修法**不是把自己排除掉**——
那等于给判据开一道后门，文件别处坏了照样看不见；而是**改用 `\ufffd` 转义写法**，
让源码里根本不出现那个字面量，于是检查保持统一、且不留任何豁免。（Batch 142 闸 8 第一版
「必须等于表头列数」把 40+ 行正常历史行全报成异常，同一条教训）。
所以输入范围用白名单写死，并在文件头显式声明。

跳过 `node_modules` / `.vitepress` / `.git`：它们是依赖与构建产物，
不是本手册的内容，**判据的输入范围必须等于发布范围**（拿内部产物充数 → 恒真）。

退出码：0 全部文本文件编码完好；1 有损坏；2 读不到应核的文件（未能核对，不等于通过）。
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 输入范围**用白名单写死**，理由见文件头「为什么用扩展名白名单」。
TEXT_EXT = {".md", ".py", ".sh", ".yml", ".yaml", ".json"}
SKIP_DIRS = {".git", "node_modules", ".vitepress", "dist"}


def text_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if os.path.splitext(fn)[1].lower() in TEXT_EXT:
                yield os.path.join(dirpath, fn)


def main():
    problems = []
    scanned = 0
    for path in text_files():
        scanned += 1
        rel = os.path.relpath(path, ROOT)
        try:
            with open(path, "rb") as fh:
                raw = fh.read()
        except OSError as exc:
            problems.append((rel, f"读不到：{exc}"))
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            problems.append((rel, f"不是合法 UTF-8：{exc}"))
            continue
        n_fffd = text.count("\ufffd")
        if n_fffd:
            lines = [i for i, l in enumerate(text.split("\n"), 1) if "\ufffd" in l]
            where = "、".join(f"第{i}行" for i in lines[:5])
            more = f"（共 {len(lines)} 行）" if len(lines) > 5 else ""
            problems.append((rel, f"含 {n_fffd} 个 U+FFFD 替换字符：{where}{more}"))
        if "\x00" in text:
            problems.append((rel, f"含 {text.count(chr(0))} 个 NUL 字节（文本文件里只可能是写坏了）"))

    print(f"编码核对：{scanned} 个文本文件（扩展名白名单 {sorted(TEXT_EXT)}）")
    if problems:
        for rel, msg in problems:
            print(f"  ✗ {rel}：{msg}")
        print(f"编码完整性核对：{len(problems)} 个文件有问题")
        return 1
    print("编码完整性核对通过：全部文本文件是合法 UTF-8，无替换字符、无 NUL 字节")
    return 0


if __name__ == "__main__":
    sys.exit(main())
