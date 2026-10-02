#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二十五道闸：截图**像素**有没有内容（Batch 191 新增）。

背景：**24 道闸里没有一道打开过图片。** 逐条查过——
闸 2 核四方对账（库内 / manifest / 发布页引用 / dist，**全是文件与引用关系**）、
闸 10 核 `visible_text` 的**字符串**在上游存在、闸 16 核 manifest 的 `captured_version` 字段、
闸 23 核 `visible_text` 的区分度与源码行。**四道闸都在读 manifest 里那几个字符串，
而 manifest 里的 `visible_text` 是当初拍图时人工登记的——图本身换成任何一张都照样过。**

**这个洞是实测出来的，不是推想的**：把 `08-prompt-editor.png` 换成一张
**1280×720 的全黑图**（文件名不变，于是四方对账每一侧都仍成立），
**闸 2 照样 rc=0「截图四方一致：库内 / manifest / 发布页引用 / dist 均为 67 张」。**
而纯色 PNG 只有 2759 字节，原图 23798 字节——**一个连人眼都能看出来的差别，
24 道闸一道都没看见。** 于是本闸专管这一件事：**图文件在，图里有没有东西。**

**两个方向的阈值都是实测出来的，不是拍的**（67 张全部量过）：

| 指标 | 实测最小/最大 | 本闸阈值 | 纯色图实测 |
|---|---|---|---|
| 每像素字节数 | 最小 **0.01365**（`55-readonly-libtv-chrome`） | **< 0.008 报** | **0.00299** |
| 主色占比（前 40 行） | 最高 **89.78%**（`55`，且有 217 色） | **> 95% 报** | **100%** |
| （唯一颜色数） | 最小 **79**（`47`/`48`/`49` 三张并列） | 不参与判定，只随报告输出 | **1** |

**方向一为什么按「每像素字节数」而不是「总字节数」**——这是反验用例 4/5 逼出来的：
第一版用绝对阈值 8000 字节，于是反验里一张 **320×120 的正常图（997 字节）被误报**。
**总字节数把「图本来就小」和「图被压扁了」混成了一件事**，
而这两件事要修的地方完全不同。换成每像素字节数后小图按小图的标准判、大图按大图的标准判，
而它**只需要读文件头 64 字节，仍然是零成本**。

**余量是刻意留的**：最紧的一处是主色占比，实测最高 89.78% 而阈值 95%——
**只有 5.2 个百分点的距离**，所以这一条只当「几乎纯色」用，不当「界面简单」用。
**判据离实测分布越近越灵敏，而越灵敏越容易在某天误伤一张合法的图**（Batch 142 闸 8 第一版）。

**只解顶部 40 行，这件事必须论证而不是默认**（代价：全量解 400 行要 45 秒，
会让构建慢一倍）：
  · 对「**整图退化**」——纯色 / 全白 / 加载失败 / 截图截在渲染前——**顶部是充分的**，
    **这类图任何一行都退化**；
  · 但它对「**这张图拍的是不是正确的界面**」**没有分辨力**，那需要 OCR，
    超出零依赖的范围。**这条边界写在文件头，不让人误以为它什么都管。**
  · 顺带一个实测事实：**顶部对深色 UI 的分辨力低得惊人**——
    `47-subtitle-timeline-srt-clip` / `48-subtitle-clip-edit-panel` / `49-subtitle-edit-dialog`
    三张**不同的界面**，顶部 40 行的颜色分布**完全相同**（79 色 / 主色 78.65%）。
    **所以绝不能拿顶部特征当「界面指纹」**，那会把这三张判成同一张。

**零外部依赖**（`pngstat.py` 手写 PNG 解码）：判据一旦 import 一个装不上的包，
报出来的是 `ImportError` 崩掉——**而崩溃不是「未能核对」**（纪律 101）。

三个方向：
  · 方向一：**文件字节数**（零成本，先用它把明显不正常的挑出来）；
  · 方向二：**唯一颜色数 + 主色占比**（解顶部 40 行，两条都过才放行）；
  · 方向三：**自检探针**——自己造一张纯色 PNG 喂给 `pngstat.features()`，
    若它没把那张图判成退化，说明解码链路坏了 → rc=2「未能核对」。
    **不能让判据在解码器退化时安静地全绿**（纪律 101，与闸 22/23 同源）。

输入范围：`screenshots/manifest.yml` 里登记的截图（与闸 2 / 16 / 23 同一份，
**判据的输入范围必须等于发布范围**）。

退出码：0 全部有内容；1 有退化图；2 未能核对（manifest 读不到 / PNG 解不开）。
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pngstat   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "screenshots", "manifest.yml")
SHOTS = os.path.join(ROOT, "screenshots")

# 采样行数。**不要为了「更全」而调大**：400 行要 45 秒（实测），构建会慢一倍；
# 而本闸要抓的是整图退化，40 行对它是充分的（见文件头）。
SAMPLE_ROWS = 40

# 两个阈值，全部来自 67 张实测（见文件头的表）。**改动阈值必须重新量全量分布。**
MIN_BYTES_PER_PIXEL = 0.008
MIN_COLORS = 40
MAX_TOP_SHARE = 0.95
# `MIN_COLORS` **不再参与判定**（方向二最终只看主色占比，见 main() 里的注释），
# 它只作为输出里的那个数存在——让人一眼看出这张图有几种颜色。

_ENTRY_RE = re.compile(r"file:\s*(\S+\.png)")


def manifest_files():
    try:
        with open(MANIFEST, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        raise pngstat.PngError("读不到 screenshots/manifest.yml：%s" % exc)
    names = _ENTRY_RE.findall(text)
    if not names:
        raise pngstat.PngError("manifest.yml 里一条截图登记都没有——判据的输入读空了")
    return names


def selfcheck():
    """方向三：自己造一张纯色图，确认解码链路把它认成退化。"""
    probe = pngstat.features(pngstat.solid_png(640, 360, (0, 0, 0)),
                             max_rows=SAMPLE_ROWS)
    if probe["colors"] > MIN_COLORS or probe["top_share"] <= MAX_TOP_SHARE:
        raise pngstat.PngError(
            "自检失败：造出来的纯色图被算成 %d 色 / 主色 %.2f%%，"
            "它本该落在阈值之下（<%d 色 且 >%.0f%%）。**解码链路已经坏了**"
            % (probe["colors"], probe["top_share"] * 100, MIN_COLORS, MAX_TOP_SHARE * 100))
    return probe


def main():
    try:
        selfcheck()
        names = manifest_files()
    except pngstat.PngError as exc:
        print("未能核对：%s" % exc)
        return 2

    # manifest 里的 `file:` 写的是**相对手册根**的路径（`screenshots/01-home.png`）。
    # **按原样解析，不要再拼一次 `screenshots/`**——第一版拼了，于是 67 张一张都没打开，
    # 而它报的是「0 张全部有内容」并 rc=0（见下面的 checked 守卫）。
    paths = [os.path.join(ROOT, n) for n in names]

    # **本闸最重要的一行守卫**（Batch 191 首跑就撞上）：
    # 上面那次「67 张一张没打开却 rc=0」的教训是——
    # **「一个都没检查」和「全部检查通过」在退出码与措辞上完全一样**，
    # 而后者读起来像好消息。**判据必须报出「我实际检查了几项」，
    # 并在任何一项打不开时停下来，而不是让它悄悄从计数里消失。**
    missing = [n for n, p in zip(names, paths) if not os.path.exists(p)]
    if missing:
        print("未能核对：manifest 登记的 %d 张里有 %d 张打不开：%s"
              % (len(names), len(missing), "、".join(missing[:5])
                 + ("…" if len(missing) > 5 else "")))
        print("　→ 缺失本身由闸 2（四方对账）负责报；**本闸不能因此跳过后继续，**"
              "否则它会在一张都没检查的情况下报绿。")
        return 2

    problems = []
    checked = 0
    for name, path in zip(names, paths):
        checked += 1
        size = os.path.getsize(path)
        try:
            with open(path, "rb") as fh:
                head = fh.read(64)
            w, h, _d, _c, _i = pngstat.read_header(head)
        except (pngstat.PngError, OSError) as exc:
            problems.append("未能核对：`%s` 读不出尺寸——%s" % (name, exc))
            continue
        if w * h == 0:
            problems.append("未能核对：`%s` 尺寸是 %dx%d（零像素）" % (name, w, h))
            continue
        # **方向一按「每像素字节数」而不是「总字节数」判**——这是反验用例 4/5 逼出来的。
        # 第一版用绝对字节数 8000，于是反验里一张 **320×120 的正常图（997 字节）被误报**：
        # **总字节数把「图本来就小」和「图被压扁了」混成了一件事**。
        # 换成每像素字节数之后，小图按小图的标准判、大图按大图的标准判：
        #   实测 67 张   最小 **0.01365**（`55-readonly-libtv-chrome`）中位 0.105
        #   纯黑 1280×720  **0.00299**　　纯白 1440×900 约 0.004
        # 阈值 0.008 对两侧都留了余量，而**它只需要读文件头 64 字节，仍然是零成本**。
        ratio = size / float(w * h)
        if ratio < MIN_BYTES_PER_PIXEL:
            problems.append(
                "方向一：`%s` 是 %dx%d、%d 字节，即**每像素 %.5f 字节**（阈值 %.3f）——"
                "**实测最省的合法界面图是 %.5f**（`55-readonly-libtv-chrome`），"
                "而纯色图 1280×720 只有 %.5f。这么扁的 PNG 装不下界面"
                % (name, w, h, size, ratio, MIN_BYTES_PER_PIXEL, 0.01365, 0.00299))
            continue                      # 压缩比已经不正常，不必再花时间解码
        try:
            with open(path, "rb") as fh:
                f = pngstat.features(fh.read(), max_rows=SAMPLE_ROWS)
        except (pngstat.PngError, OSError) as exc:
            problems.append("未能核对：`%s` 解不开——%s" % (name, exc))
            continue
        # **方向二最终只留一个条件：主色占比 > 95%**——这一轮砍了两刀，每刀都有数据：
        #  ①第一版是 `颜色数 < 40 **或** 主色 > 95%`，反验里一张「白底 + 16 个色块」
        #    的合法图（17 色）被误报——**「颜色少」不是退化**，
        #    大面积留白 + 少量元素的界面本来就色少；
        #  ②改成 `颜色数 < 40 **且** 主色 > 80%` 之后发现：**这个形态在真实图里
        #    几乎不存在**。最接近的一张 `55-readonly-libtv-chrome` 主色 89.78%，
        #    但它有 **217 种颜色**（文字抗锯齿产生的大量灰阶），
        #    而要同时做到「色数 < 40」又「压缩比不低」，只能靠**没有抗锯齿的纯色块**——
        #    那种图在现实里就是退化图，**它已经被主色 > 95% 那条抓走了**。
        #    **为一个现实中罕见的形态留一条分支，不如砍掉它**：
        #    状态空间少一个，误报就少一类（Batch 139/141/142 的同一课）。
        # `f["colors"]` 仍被取用——**输出里带着它**，人一眼能看出这张图有几种颜色，
        # 而 `MIN_COLORS` 作为**报告里那个数**（不是判据）也就没变成死变量。
        if f["top_share"] > MAX_TOP_SHARE:
            problems.append(
                "方向二：`%s` 顶部 %d 行里 **%.1f%% 的像素是同一种颜色**、"
                "全部只有 **%d 种颜色**（阈值 %.0f%%）——图文件在，图里几乎没有界面。"
                "实测最高的合法图是 89.8%% / 217 色（`55`），"
                "而闸 2 / 10 / 16 / 23 读的都是 manifest 里那几个字符串，**四道闸都会照样通过**"
                % (name, f["rows"], f["top_share"] * 100, f["colors"], MAX_TOP_SHARE * 100))

    assert checked == len(names), "内部矛盾：登记 %d 张、实际检查 %d 张" % (len(names), checked)

    if problems:
        unverified = [p for p in problems if p.startswith("未能核对")]
        if unverified and len(unverified) == len(problems):
            print("未能核对：%d 张截图的像素读不出来" % len(unverified))
            for p in problems:
                print("  · " + p)
            return 2
        print("截图像素核对：%d 项退化（%d 张已核对）" % (len(problems), checked))
        for p in problems:
            print("  · " + p)
        print()
        print("修法：重新截图。**这不是「重跑构建」能解决的**——"
              "闸 2 / 10 / 16 / 23 都只读 manifest 里的字符串，"
              "**图换成空白它们一样绿**。")
        return 1

    print("截图像素核对：%d 张全部有内容（每像素字节数与主色占比均在阈值内；"
          "像素统计只看顶部 %d 行）" % (checked, SAMPLE_ROWS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
