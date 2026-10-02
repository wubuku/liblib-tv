#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""截图四方对账闸：源目录 screenshots/ ↔ manifest.yml ↔ 已发布页面引用 ↔ dist 产物。

背景（Batch 94）：17-light-mode.png 出现在库内目录、登记在 manifest、还被
task-inventory.yml 当作 organize-canvas 的运行时实证引用着，但发布页面早已不再
引用它——重写该页时图片被「替换」而非「补入」。单看任意一侧都发现不了：
  · 只数库内文件 → 48 张，数量正常
  · 只看 manifest  → 48 条，登记齐全
  · 只看 dist      → 47 张，数字对不上但说不清缺的是哪张、为什么
只有把「库内 / 登记 / 引用 / 打包」四方摊平比对，才能定位到「证据在库但读者
看不到」这一类缺陷。本脚本即为该闸门，构建时由 build-site.sh 步骤 6 调用。

退出码：0 一致；1 存在不一致。
"""

import os
import re
import sys
import glob

# Batch 167：手册根目录由脚本自身位置推导，**不再依赖 cwd**。
# 此前 SHOT_DIR / DIST / glob 的模式全是**裸相对路径**——换个目录运行，扫到的就是
# 那个目录下的东西（实测：从手册根跑 rc=0，从空目录跑 rc=2）。
# 它原本是**失败安全**的（不会误判通过），但「失败模式安全」不等于「写法正确」：
# 同一个脚本换个位置就换了个答案，这个行为本身就说不清它到底查了什么。
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(ROOT, "screenshots")
DIST = os.path.join(ROOT, ".vitepress", "dist")
MANIFEST = os.path.join(SHOT_DIR, "manifest.yml")

# 内部账本：允许引用截图但不属于对外发布内容，不计入「发布页引用」
INTERNAL = re.compile(
    r"(task-inventory|PROGRESS|AUDIT-RULES|AUDIT|FINAL-REPORT|SOURCE_OBSERVATIONS|manifest)"
    r"|^PUBLISH"
)

# 形如 screenshots/*.png 的通配写法（PUBLISH.md 的入库清单）不是真实引用，跳过
GLOB_REF = re.compile(r"[*?\[\]]")


def collect():
    files = {
        f
        for f in os.listdir(SHOT_DIR)
        if f.lower().endswith(".png")
    }

    with open(MANIFEST, encoding="utf-8") as fh:
        raw = fh.read()
    man = set(re.findall(r"-\s*file:\s*screenshots/([^\s]+\.png)", raw))
    # **Batch 214 新增两样**。原先 `man` 是 `set(...)`，**而集合会把重复折叠**——
    # 于是「同一条登记两次」在四方对账里**根本不是一个概念**：
    # 实测两种形态（整条重复 / 重复但 visible_text 写成别的）闸门**都报绿**。
    man_list = re.findall(r"-\s*file:\s*screenshots/([^\s]+\.png)", raw)
    # 逐条记录拆出来，才能问「这条的取证字段齐不齐」
    recs = re.findall(r"-\s+file:\s*(\S+)(.*?)(?=\n\s*-\s+file:|\Z)", raw, re.S)

    referenced = set()
    for p in glob.glob(os.path.join(ROOT, "**", "*.md"), recursive=True):
        if "node_modules" in p or ".vitepress" in p:
            continue
        if INTERNAL.search(os.path.basename(p)):
            continue
        with open(p, encoding="utf-8", errors="ignore") as fh:
            body = fh.read()
        for name in re.findall(r"screenshots/([^\s)\"'>]+\.png)", body):
            if GLOB_REF.search(name):
                continue
            referenced.add(os.path.basename(name))

    dist = set()
    for root, _, fs in os.walk(DIST):
        for f in fs:
            if f.lower().endswith(".png"):
                # 产物文件名带内容哈希，还原原名后比对
                dist.add(re.sub(r"\.[A-Za-z0-9_-]{8}\.png$", ".png", f))

    return files, man, referenced, dist, man_list, recs


def main():
    if not os.path.isdir(SHOT_DIR):
        print(f"[skip] 未找到 {SHOT_DIR}/，跳过截图对账")
        return 2
    if not os.path.isdir(DIST):
        print(f"[skip] 未找到 {DIST}/（尚未构建），跳过截图对账")
        return 2

    files, man, referenced, dist, man_list, recs = collect()
    problems = []

    def report(label, items, hint):
        if not items:
            return
        for x in sorted(items):
            problems.append(f"[{label}] {x}  {hint}")

    report("未登记", files - man, "← 库内有图但 manifest 没登记，账本对不上")
    report("空登记", man - files, "← manifest 登记的图库内不存在")
    report("孤儿图", files - referenced, "← 证据在库但没有任何发布页展示，读者看不到")
    report("缺图", referenced - files, "← 页面引用了但库内没有该文件")
    report("未打包", files - dist, "← 库内有图但构建产物里没有")

    # **Batch 214：重复登记**。四方对账其余五条全是**集合差**，
    # **而集合天生看不见重复**——这一条不属于那五类，只能另问。
    dups = {n for n in man_list if man_list.count(n) > 1}
    for n in sorted(dups):
        report_dup = "← **同一张图在 manifest 里登记了 %d 次**" % man_list.count(n)
        problems.append(f"[重复登记] {n}  {report_dup}")

    # **Batch 214：取证字段齐全**。实测删掉任一条记录的 `visible_text` 或 `alt`，
    # 闸 2 报绿——**而 `visible_text` 正是闸 10 唯一的判据输入**：
    # 它的正则 `visible_text:\s*'([^']*)'` 匹配不到就**什么都不查**，
    # **于是一条没有该字段的记录，对闸 10 而言等于不存在**。
    # **这七个别处声明过的字段**（`AUDIT.md` 那句「全部带 …」），**从来没有任何闸核过**。
    NEED = ("task_id", "step", "route", "captured_at", "verified_locator",
            "visible_text", "alt", "sha256")
    for path_name, body in recs:
        miss = [f for f in NEED
                if not re.search(r"^\s*%s:\s*'?.+?'?\s*$" % f, body, re.M)]
        if miss:
            problems.append(
                f"[缺字段] {path_name}  ← 这条记录没有 {'、'.join(miss)}"
                "　→ `visible_text` 是闸 10 唯一的判据输入，缺了它这条记录等于不存在")

    if problems:
        print(f"截图四方对账不一致：库内 {len(files)} 张 / manifest {len(man_list)} 条"
              f"（唯一 {len(man)} 个）/ 发布页引用 {len(referenced)} 张 / dist {len(dist)} 张")
        for p in problems:
            print("  " + p)
        return 1

    print(f"截图四方一致：库内 {len(files)} 张 / manifest {len(man_list)} 条"
          f"（**唯一 {len(man)} 个、无重复**）/ 发布页引用 {len(referenced)} 张 / dist {len(dist)} 张；"
          f"{len(recs)} 条记录的 8 个取证字段齐全")
    return 0


if __name__ == "__main__":
    sys.exit(main())
