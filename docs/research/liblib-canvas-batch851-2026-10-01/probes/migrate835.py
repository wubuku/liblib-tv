#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 851 第二步：迁移 **batch 835 的属性增量账**（`S2`）。

## ★ 为什么需要迁移（★ 这不是回归事故，是**真实的期望变更**）

★ 835 的 `S2` 比的是「748 基线 ⟶ **工作区当前**」的**净增属性名**，
   且每一条都必须**归属到具体批次**、并逐条反查「它最早出现在哪个 commit」。

★ 本批在 `DirectorViewport.tsx` 的视口 `<section>` 上新增了三个 `data-` 属性
   （`data-director-view-position`／`-target`／`-fov`）⟹ ⟹
   它们被算成净增 ⟹ ⟹ 而 `EXPECTED_ADDED` 只登记到 batch 834 ⟹ ⟹ 判据翻红。

★ ★ 这正是 835 那条判据**设计上的本意**（「净增必须逐条归属到具体批次」）
   ⟹ ⟹ 判据自己把漂移抓住了 ⟹ ⟹ 正解是**迁移它**，不是绕过它。

## ★ 迁移做什么

1. `EXPECTED_ADDED` 加一条归属「batch 851 导演台视图类快捷键」，含那三个属性名
2. `ATTR_COMMITS` 追加本批的 commit（**必须排在最后** ⟹ ⟹ 「最早出现」的遍历顺序才对）
3. 判据文本里的批次覆盖从 4 个改成 5 个、属性名个数从 22 改成 25

## 用法

    python3 migrate835.py <本批的 commit hash>
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "scripts/verify-liblib-batch835.py"


def rep(text, old, new, label, count=1):
    n = text.count(old)
    assert n == count, "★ %s：命中 %d 次（期望 %d）\n---\n%s" % (label, n, count, old[:200])
    print("  ✓", label)
    return text.replace(old, new, 1)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    commit = sys.argv[1].strip()
    # ★ 自证：那个 commit 必须真的在仓库里
    r = subprocess.run(["git", "cat-file", "-e", "%s^{commit}" % commit],
                       cwd=str(ROOT), capture_output=True)
    if r.returncode != 0:
        print("★ commit %s 不存在" % commit)
        return 1

    p = SCRIPT
    s = p.read_text(encoding="utf-8")
    print("迁移 scripts/verify-liblib-batch835.py（batch 851）")

    # 1) EXPECTED_ADDED 加一条
    s = rep(s, '''    "batch 834 时间轴引导 5 步": [
        "data-director-timeline-guide-bubble", "data-director-timeline-guide-count",
        "data-director-timeline-guide-icon", "data-director-timeline-guide-next",
        "data-director-timeline-guide-overlay", "data-director-timeline-guide-ring",
        "data-director-timeline-guide-skip", "data-director-timeline-guide-target",
    ],
}''',
'''    "batch 834 时间轴引导 5 步": [
        "data-director-timeline-guide-bubble", "data-director-timeline-guide-count",
        "data-director-timeline-guide-icon", "data-director-timeline-guide-next",
        "data-director-timeline-guide-overlay", "data-director-timeline-guide-ring",
        "data-director-timeline-guide-skip", "data-director-timeline-guide-target",
    ],
    # ★ Batch 851：导演台视图类快捷键 ⟹ ⟹ 视口上暴露当前相机位姿的三个 data- 属性
    "batch 851 导演台视图类快捷键": [
        "data-director-view-position", "data-director-view-target",
        "data-director-view-fov",
    ],
}''', "1) EXPECTED_ADDED 加一条")

    # 2) ATTR_COMMITS 追加本批（必须排最后）
    s = rep(s, '''        ("8074234d", "batch 834 时间轴引导 5 步"),
    ]''',
'''        ("8074234d", "batch 834 时间轴引导 5 步"),
        # ★ Batch 851（★ 必须排在最后 ⟹ ⟹ 「最早出现在哪个 commit」的遍历顺序才对）
        ("%s", "batch 851 导演台视图类快捷键"),
    ]''' % commit, "2) ATTR_COMMITS 追加本批")

    # 3a) 判据：归因批次覆盖
    s = rep(s, '''        "归因批次覆盖 825/831/832/834": sorted(EXPECTED_ADDED) == [
            "batch 825 跟随横幅", "batch 831 帮助→快捷键面板",
            "batch 832 添加机位·机位预设面板", "batch 834 时间轴引导 5 步"],''',
'''        "归因批次覆盖 825/831/832/834/851": sorted(EXPECTED_ADDED) == [
            "batch 825 跟随横幅", "batch 831 帮助→快捷键面板",
            "batch 832 添加机位·机位预设面板", "batch 834 时间轴引导 5 步",
            "batch 851 导演台视图类快捷键"],''', "3a) 归因批次覆盖")

    # 3b) 文档字符串里的个数
    s = rep(s, "⟹ 净增 **22 个属性名**", "⟹ 净增 **25 个属性名**", "3b) 文档字符串·净增个数")
    # ★ 这句在**文档字符串**与 **S2 判据文本**里各有一处 ⟹ ⟹ 一次替换两处
    s = rep(s, "净增的属性名**恰好是那 22 个**，",
            "净增的属性名**恰好是那 25 个**，", "3c) 恰好那 22 个（两处）", count=2)
    s = rep(s, "且每一个都归属到 825/831/832/834 四个批次之一",
            "且每一个都归属到 825/831/832/834/851 五个批次之一",
            "3d) 文档字符串·四个批次之一")
    s = rep(s, "S2  **增量账**：748 基线 ⟶ HEAD 净增恰好 22 个属性名，且每个都归属到",
            "S2  **增量账**：748 基线 ⟶ HEAD 净增恰好 25 个属性名，且每个都归属到",
            "3e) 概览行·净增个数")

    p.write_text(s, encoding="utf-8")
    print("\n已写入 %s" % SCRIPT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
