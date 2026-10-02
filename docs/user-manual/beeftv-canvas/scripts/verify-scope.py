#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二十四道闸：**发布范围只有一个来源**（Batch 190 新增）。

背景：闸 22 `verify-quote-punct.py` 的文件头写着「**判据的输入范围必须等于发布范围**」，
而它的 `PAGES` 清单里躺着 **`PUBLISH.md`**——被 `.vitepress/config.mjs` 的 `srcExclude`
显式排除、**根本不会出现在站点上**的内部资料。那句话在代码里是假的。

**为什么没人发现**（三层，每一层都值得单独记住）：

  · `PUBLISH.md` 确实能被闸 22 扫到，所以「闸 22 跑过了」这句话是真的——
    **只是它扫的东西里有一份读者根本读不到**；
  · 闸 1（死链）只核 `.md` 链接，而错误的路径写在 ```bash 代码块里，不是链接；
  · 闸 22 只查「」里的界面文案标点，而 `PUBLISH.md` 全篇只有 **1 段**引号（「本页目录」），
    归一化后匹配不上任何上游文案——**扫了等于没扫**。

**判据的形状是被两版探针逼出来的，不是一开始就想好的**：

  第一版「核所有闸源码里出现的 .md 文件名」→ 11 个闸里 **8 个「越界」**，
  逐个读原文后**全是假阳性**：闸 19/21/23 本来就该扫 `AUDIT.md`/`PROGRESS.md`
  （账本闸的输入就是账本），闸 9 本来就该排除内部资料（它管的正是发布面）。
  **判据把不相干的东西报成异常，人就会学会忽略它**（Batch 142 闸 8 第一版、
  Batch 185 闸 22 第一版，同一课）。

  第二版收窄到「值是 md 文件名的列表字面量」→ 4 个常量，**只有 `PAGES` 有问题**，
  但又暴露出 `EXTRA_SCAN_FILES`（闸 9 的 1 个元素子集）会被「必须等于排除集」误伤——
  **「一个清单是完整副本还是子集」在散文级代码里无法机械判定**，
  再猜下去就是第三版噪音。

  **第三版把判断降到一句不可能有歧义的话**：一份清单里的每个文件，
  要么会被发布，要么不会发布。**一份清单不可能既装「不发布的」又装「发布的」**——
  这就是**混装**，不需要知道它自称是读者页清单还是排除集。

三个方向：

  · 方向一：**混装**（同一份 md 清单里同时出现排除项与发布项）即报；
    另有「清单里有手册树根本不存在的文件」——那是拼错的文件名，与发布面无关。
  · 方向二：`srcExclude` 每一项都必须**命中至少一个真实文件**。
    写错一个名字的排除项不会让站点多发布什么——它只会**静悄悄地不起作用**，
    而使用它的人以为内部资料已经被挡住了。
  · 方向三：**自检**，拿手册树里**每一个** `.md` 走一遍归属判定，
    断言它们**不重不漏**地被分成发布/排除两堆。判定器退化时 rc=2「未能核对」，
    **不能让判据在分类器读空时安静地全绿**（纪律 101）。

输入范围：`scripts/` 下**闸门**（`verify-*.py`）与共用模块的**模块顶层** md 列表字面量。
刻意排除 `selftest-*`：反验里的清单是**故意注入的夹具**，它们指向内部资料正是本批要找的形状，
把夹具当生产代码核，闸会在自己身上响。

退出码：0 一致；1 有不自洽；2 未能核对（读不到 config.mjs / 树里 0 个 .md）。
"""

import ast
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scope   # noqa: E402

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
ROOT = scope.ROOT


def scan_gate_lists():
    """抽出每个闸门模块顶层的「.md 文件名列表」常量。

    用 AST 而不是正则：**正则分不清「一个清单」和「散落在三处的三个文件名」**，
    而本闸的全部意义就是只认清单（第一版假阳性的根源）。
    """
    found = []
    for name in sorted(os.listdir(SCRIPTS)):
        if not name.endswith(".py"):
            continue
        if name.startswith("selftest-") or name == os.path.basename(__file__):
            continue
        path = os.path.join(SCRIPTS, name)
        try:
            with open(path, encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=path)
        except (OSError, SyntaxError) as exc:
            raise scope.ScopeError("读不了 %s：%s" % (name, exc))
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            try:
                val = ast.literal_eval(node.value)
            except (ValueError, SyntaxError):
                continue
            if not isinstance(val, (list, tuple, set)):
                continue
            vals = [v for v in val if isinstance(v, str)]
            if not vals or not all(v.endswith(".md") for v in vals):
                continue
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            found.append((name, targets[0] if targets else "?", vals))
    return found


def main():
    problems = []
    try:
        excluded = scope.excluded_basenames()
        published = scope.published_md()
        everything = scope.all_md()
        items = scope.exclude_items()
    except scope.ScopeError as exc:
        print("未能核对：%s" % exc)
        return 2
    if not everything:
        print("未能核对：手册树里一个 .md 都没有（判据的输入读空了）")
        return 2

    # ---- 方向一：清单不许混装，也不许点名不存在的文件 ----
    gate_lists = scan_gate_lists()
    for script, const, vals in gate_lists:
        missing = sorted({v for v in vals if scope.classify(v) == scope.ABSENT})
        if missing:
            problems.append(
                "方向一：%s 的 `%s` 里点名了手册树里不存在的文件：%s"
                % (script, const, "、".join(missing)))
        hit_exc = sorted({v for v in vals if scope.classify(v) == scope.EXCLUDED})
        hit_pub = sorted({v for v in vals if scope.classify(v) == scope.PUBLISHED})
        if hit_exc and hit_pub:
            problems.append(
                "方向一：%s 的 `%s` **混装**了——同一份清单里既有被 srcExclude 排除的文件"
                "（%s），又有会发布的文件（%s）。一份清单不可能既装不发布的又装发布的："
                "前者多半是抄 `srcExclude` 时抄错了目标（抄成了读者页清单？）"
                % (script, const, "、".join(hit_exc), "、".join(hit_pub)))

    # ---- 方向二：srcExclude 每一项都得命中真实文件 ----
    present = scope.walk_basenames()
    for item in items:
        tail = item[3:] if item.startswith("**/") else item
        tail = tail.rsplit("/", 1)[-1]
        if tail not in present:
            problems.append(
                "方向二：srcExclude 的 `%s` 在手册树里一个文件都没命中——"
                "**写错的排除项不会让站点多发布什么，只会静悄悄地不起作用**，"
                "而用它的人以为内部资料已经被挡住了" % item)

    # ---- 方向三：自检，分类必须不重不漏 ----
    buckets = {scope.EXCLUDED: set(), scope.PUBLISHED: set(), scope.ABSENT: set()}
    for name in sorted(everything):
        buckets[scope.classify(name)].add(name)
    if buckets[scope.ABSENT]:
        problems.append(
            "方向三（自检）：手册树里这些 .md 既没被判成发布也没被判成排除：%s"
            % "、".join(sorted(buckets[scope.ABSENT])))
    if buckets[scope.EXCLUDED] & buckets[scope.PUBLISHED]:
        problems.append("方向三（自检）：同一份文件同时落在发布与排除两堆里")
    if buckets[scope.EXCLUDED] | buckets[scope.PUBLISHED] != everything:
        problems.append("方向三（自检）：两堆并起来不等于手册树的全部 .md——判定器漏了东西")

    if problems:
        print("发布范围不自洽（%d 项）：" % len(problems))
        for p in problems:
            print("  · " + p)
        print()
        print("事实源：%s" % scope.describe())
        print("修法：发布范围只有一个来源——`.vitepress/config.mjs` 的 `srcExclude`；"
              "闸门要判断某个文件发不发布，引用 `scope.classify()`，不要手写清单。")
        return 1
    print("发布范围一致：%s" % scope.describe())
    return 0


if __name__ == "__main__":
    sys.exit(main())
