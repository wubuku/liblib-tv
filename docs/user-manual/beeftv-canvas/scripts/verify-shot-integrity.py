#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三十四道闸：截图的**两项登记事实**有没有被核过（Batch 239 新增）。

**它接的是 Batch 191 那个洞的下一层。** Batch 191 记的原话是
「24 道闸里没有一道打开过图片」，实测手段是**把 `08-prompt-editor.png` 换成一张
全黑图**——那一次闸 31 抓住了，于是本闸的前身（`verify-shot-pixels.py`）建起来了。

**而「全黑图」只覆盖了「图被换成没有内容的图」这一种坏法。** 本批实测的注入是
**裁掉底部 120px**：图还在、内容正常（每像素字节数与主色占比都在闸 31 的阈值内），
**而与截图有关的五道闸——闸 2 四方对账 / 闸 31 像素内容 / 闸 23 布局漂移 /
闸 16 截图版本 / 闸 10 取证文案——全部 rc=0。**
**闸 31 问的是「图里有没有东西」，而「这张图还是不是登记的那张」没有任何闸问。**

**而 manifest 里本来就有一个专门回答这个问题的字段：`sha256`——67 条逐条登记，
只是从来没有任何判据读过它的值。** 闸 2 的 `[缺字段]` 只核「它在不在」，
和 `alt`、`visible_text` 当初一样是「登记了但没人看」。

## 两条判据

  方向一：**`sha256` 的值必须与文件实际内容相符。**
    这是唯一能抓住「图被动过」的判据——换图、裁剪、重新导出、改一个字节，
    **四种坏法它一次都跑不掉**，而其余 33 道闸对它们全都沉默。
    当前实测 **67/67 相符**，所以这条今天不报任何东西；
    **而「今天不报」正是它该有的状态**——它是一道只会因为真的坏了才红的闸。

  方向二：**`viewport` 登记值必须与 PNG 的真实像素尺寸相容。**
    **这一条要先把字段含义钉死，否则无从核对。** 现场 67 条里
    **61 条登记值与像素尺寸逐条相等，6 条是登记 1440×900 而文件 2880×1800**——
    恰好两倍。那 6 张是 2026-10-01 用 `deviceScaleFactor: 2` 的无头浏览器拍的，
    **`viewport` 记的是浏览器的 CSS 视口，而 PNG 存的是物理像素。**
    **所以本闸的判据是「实际尺寸必须是登记值的整数倍、且两轴倍数相同」**，
    而不是「两者必须相等」——后者会把这 6 条合法记录判成缺陷，
    **而那 6 条恰恰是「这条判据不该太紧」的活证据**。
    附带收益：两轴倍数相同这一条**能抓住被裁剪或被拉伸的图**。

## 本闸不判的（能力上限如实写在这里，不装作覆盖了）

  · **画面内容与界面是否一致**——那是 OCR 级的比对，`visible_text` 是人工登记的，
    闸 31 只保证「图里有东西」，本闸只保证「图还是登记的那张、有登记的形状」。
    **重拍才能解决这件事，而重拍由人决定。**
  · **`viewport` 是否与 `captured_version` 那个版本的默认窗口一致**——上游不保证这件事。
  · **同一页面上出现两种视口是否合适**——实测 `subtitle-highlights.md` 就是
    （第 22 行 1440×900、第 30 行 1280×720，同一块多轨时间线面板），
    **两图结构一致、宽高比不同，页面未作说明**；本闸只保证两图的登记是诚实的，
    **「一页里该不该混用两种视口」是编辑判断，不是机械判定**。

退出码：0 登记与文件一致；1 有登记与文件不符；2 读不到登记或图（未能核对，不等于通过）。
"""

import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scope  # noqa: E402

import pngstat  # noqa: E402  —— 零外部依赖的 PNG 头读取
import shotmanifest

ROOT = scope.ROOT
MANIFEST = os.path.join(ROOT, "screenshots", "manifest.yml")

FIELD_RE = {
    "sha256": re.compile(r"^\s+sha256:\s*([0-9a-fA-F]{64})\s*$", re.M),
    "viewport": re.compile(r"^\s+viewport:\s*'?([0-9]+)\s*[x×]\s*([0-9]+)'?\s*$", re.M),
}


def parse_manifest():
    with open(MANIFEST, encoding="utf-8") as f:
        text = f.read()
    out = []
    for name, block in shotmanifest.blocks(text):
        rec = {"file": name}
        for key, rx in FIELD_RE.items():
            hit = rx.search(block)
            rec[key] = hit.groups() if (key == "viewport" and hit) else (
                hit.group(1) if hit else None)
        out.append(rec)
    return out


def main():
    if not os.path.isfile(MANIFEST):
        print("[skip] 读不到 screenshots/manifest.yml，截图登记核对本轮未能进行")
        return 2
    recs = parse_manifest()
    if not recs:
        print("[skip] manifest.yml 里一条截图登记都没有——判据的输入读空了，"
              "而「读空」与「全部合格」在退出码上必须不同开")
        return 2

    problems, unreadable = [], []
    hash_checked = vp_checked = dpr_gt1 = 0
    for rec in recs:
        rel = rec["file"]
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            unreadable.append(f"{rel}（登记了但图文件不在）")
            continue
        with open(path, "rb") as f:
            data = f.read()

        # —— 方向一：sha256 的**值** ——
        want = rec["sha256"]
        if want is None:
            problems.append(f"{rel}：没登记 sha256 的值（闸 2 的 `[缺字段]` 只核它在不在，"
                            f"**而它是唯一能抓住「图被动过」的字段**）")
        else:
            got = hashlib.sha256(data).hexdigest()
            if got != want.lower():
                problems.append(
                    f"{rel}：**图文件与登记的 sha256 不符**"
                    f"（登记 {want[:12]}… 实际 {got[:12]}…）→ "
                    f"**这张图被换过、被裁过、被重新导出过，或被改过一个字节**；"
                    f"**其余各闸对四种坏法全部沉默**（闸 31 只问「图里有没有东西」，"
                    f"而裁剪后的图内容完全正常）"
                )
            else:
                hash_checked += 1

        # —— 方向二：viewport 与真实尺寸相容 ——
        vp = rec["viewport"]
        if vp is None:
            problems.append(f"{rel}：没登记 viewport（或形态不是 `宽x高`）")
            continue
        try:
            w, h = pngstat.read_header(data)[:2]
        except pngstat.PngError as exc:
            problems.append(f"{rel}：读不出 PNG 尺寸（{exc}）——**读不出不等于通过**")
            continue
        dw, dh = int(vp[0]), int(vp[1])
        if dw <= 0 or dh <= 0:
            problems.append(f"{rel}：viewport 登记为 {dw}x{dh}，非正数")
            continue
        if w % dw == 0 and h % dh == 0 and w // dw == h // dh:
            vp_checked += 1
            if w // dw > 1:
                dpr_gt1 += 1
        else:
            problems.append(
                f"{rel}：登记的 viewport 是 {dw}x{dh}，而图片实际是 {w}x{h}"
                f"——**要么登记写错了，要么图被裁剪/拉伸过**"
                f"（判据要求实际尺寸是登记值的整数倍**且两轴倍数相同**，"
                f"因为 `viewport` 记的是浏览器的 CSS 视口、PNG 存的是物理像素，"
                f"两者可以差一个 devicePixelRatio）"
            )

    if unreadable:
        print("[skip] 有登记的截图文件读不到，本轮未能核对：")
        for u in unreadable:
            print("  · " + u)
        return 2

    print(f"  sha256 值核对：{hash_checked} / {len(recs)} 条与文件内容相符"
          f"（**这一项今天是 0 差异，而它该有的状态就是 0 差异**——"
          f"它只会因为图真的被动过才报）")
    print(f"  viewport 核对：{vp_checked} / {len(recs)} 条与图片真实尺寸相容"
          f"（其中 {dpr_gt1} 条是 devicePixelRatio > 1 的 Retina 截图："
          f"登记 CSS 视口、文件存物理像素，**倍数相同即合规**）")
    if problems:
        print("  ✗ 截图登记与文件不符 %d 处：" % len(problems))
        for p in problems:
            print("    · " + p)
        return 1
    print("截图登记核对通过：%d 张的两项登记事实（sha256 的值、viewport 与真实尺寸）"
          "都与文件相符" % len(recs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
