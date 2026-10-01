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

SHOT_DIR = "screenshots"
DIST = ".vitepress/dist"
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
        man = set(
            re.findall(r"-\s*file:\s*screenshots/([^\s]+\.png)", fh.read())
        )

    referenced = set()
    for p in glob.glob("**/*.md", recursive=True):
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

    return files, man, referenced, dist


def main():
    if not os.path.isdir(SHOT_DIR):
        print(f"[skip] 未找到 {SHOT_DIR}/，跳过截图对账")
        return 2
    if not os.path.isdir(DIST):
        print(f"[skip] 未找到 {DIST}/（尚未构建），跳过截图对账")
        return 2

    files, man, referenced, dist = collect()
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

    if problems:
        print(f"截图四方对账不一致：库内 {len(files)} 张 / manifest {len(man)} 条 / "
              f"发布页引用 {len(referenced)} 张 / dist {len(dist)} 张")
        for p in problems:
            print("  " + p)
        return 1

    print(f"截图四方一致：库内 / manifest / 发布页引用 / dist 均为 {len(files)} 张")
    return 0


if __name__ == "__main__":
    sys.exit(main())
