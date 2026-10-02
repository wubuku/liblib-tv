#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 25 `verify-shot-pixels.py` 的反向验证（Batch 191 新增）。

**必须成对**：既有「能抓到」的用例，也有「不该误伤」的用例。只测前者，
判据可以靠恒真通过全部用例（Batch 189 纪律 152）。

**样本全部由 `pngstat` 现场造，不碰真截图**——真截图是几十个批次积累下来的证据，
改坏了没法还原，而「用 `assert` 钉死注入」这条纪律要求注入必须可撤销。

六例：

  1. **能抓**：纯黑图（2759 字节）→ 方向一必报。**这正是本批在真图上实测过的那个洞**：
     把 `08-prompt-editor.png` 换成同尺寸纯黑图，闸 2 / 16 / 23 全部 rc=0。
  2. **能抓**：**顶部纯色、下方有噪点**的大图（字节够大、过不了方向一）→ 方向二必报。
     **这一例不能省**：只测用例 1 的话，方向二整条分支一次都没被执行过，
     而它恰恰是本批新增的唯一一条新逻辑（Batch 181「阈值从没被读过」的翻版）。
  3. **能抓**：manifest 为空 → **必须 rc=2**，不能报「0 张全部有内容」。
     **这是本批真实踩过的那个洞**：第一版路径拼错，67 张一张没打开却 rc=0。
  4. **不误伤**：颜色数刚好在阈值**之上**的图 → 必须放过（阈值是 40，造 60 色）。
  5. **不误伤**：主色占比刚好在阈值**之下**、但颜色数很少的图 → 必须放过
     （造「白底 + 3 个方块」：颜色数 < 40 但主色 < 95%，**两条都不该命中**）。
     **用例 4/5 一起量出本闸的假阳性边界**，而它们比任何口头说明都有用。
  6. **不误伤**：真实 67 张 → rc=0（这一例跑真实数据，约 5 秒）。

**用例 5 是本批最要紧的一条**：它钉住的是「不要把颜色数阈值当成唯一判据」。
一张大面积留白 + 少量元素的合法界面图，**颜色数本来就少**——
方向二之所以还留了「主色占比 ≤ 95%」这一条，就是为它准备的。

退出码：0 全部通过；1 有用例失败。
"""

import glob
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE = "verify-shot-pixels.py"

sys.path.insert(0, HERE)
import pngstat   # noqa: E402

MIN_BYTES_PER_PIXEL = 0.008
MIN_COLORS = 40
MAX_TOP_SHARE = 0.95


def noisy_tail_png(width, height, solid_rows, rgb):
    """顶部 `solid_rows` 行纯色、其余行是确定性噪点——**字节够大但像素退化**。"""
    line = bytes(rgb) * width
    rows = [line] * solid_rows
    seed = 12345
    while len(rows) < height:
        buf = bytearray(width * 3)
        for i in range(0, len(buf), 3):
            seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
            buf[i] = (seed >> 16) & 0xFF
            buf[i + 1] = (seed >> 8) & 0xFF
            buf[i + 2] = seed & 0xFF
        rows.append(bytes(buf))
    return pngstat.build_png(width, height, rows)


def rich_top_png(width, height, ncolors):
    """顶部就是 `ncolors` 种颜色的图——用来卡「颜色数阈值」的两侧。"""
    rows = []
    for y in range(height):
        buf = bytearray(width * 3)
        for x in range(width):
            k = (x + y) % ncolors
            buf[x * 3] = (k * 37) & 0xFF
            buf[x * 3 + 1] = (k * 91) & 0xFF
            buf[x * 3 + 2] = (k * 53) & 0xFF
        rows.append(bytes(buf))
    return pngstat.build_png(width, height, rows)


def sparse_png(width, height, nblocks):
    """白底 + 少量方块：颜色数 < MIN_COLORS，但主色占比远低于阈值、压缩比也不低。

    **尺寸要够大**：第一版用 400×150、压缩比 0.0078，**被方向一先抓走了**——
    于是这一例测的其实是方向一，而不是它要测的方向二。
    **每一条用例都该只考验它名字里的那个判据**，否则「它过了」说明不了任何事
    （Batch 189 纪律 152：反验的形状必须复现真实缺陷，而不是它的简化版）。
    """
    rows = []
    for y in range(height):
        buf = bytearray(b"\xff" * (width * 3))
        for b in range(nblocks):
            x0 = (b * 61) % (width - 50)
            y0 = (b * 47) % (height - 50)
            for yy in range(y0, y0 + 50):
                for xx in range(x0, x0 + 50):
                    buf[xx * 3] = (b * 61) & 0xFF
                    buf[xx * 3 + 1] = (b * 29) & 0xFF
                    buf[xx * 3 + 2] = (b * 83) & 0xFF
        rows.append(bytes(buf))
    return pngstat.build_png(width, height, rows)


def make_tree(root, shots):
    """搭一棵最小手册树：`scripts/`（闸 + 模块）与 `screenshots/`（图 + manifest）。"""
    os.makedirs(os.path.join(root, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(root, "screenshots"), exist_ok=True)
    # **显式搬、目标路径写死文件名**，不用 `for name in (GATE, "pngstat.py")`：
    # 循环搬运对闸 17 是**静态不可判定**的——模块名只是元组里的一个字符串，
    # AST 看不到它和 copy 动作的关系，于是闸 17 报成「没搬」。
    # **本批已经在 `selftest-scope.py` 上吃过一次这个亏**（Batch 190 纪律 154），
    # 换个文件又写了一遍。**判据认写法，而写法是可以自己管住的。**
    shutil.copy(os.path.join(HERE, GATE), os.path.join(root, "scripts", GATE))
    shutil.copy(os.path.join(HERE, "pngstat.py"), os.path.join(root, "scripts", "pngstat.py"))
    lines = ["screenshots:", ""]
    for fname, data in shots.items():
        with open(os.path.join(root, "screenshots", fname), "wb") as fh:
            fh.write(data)
        lines.append("  - file: screenshots/%s" % fname)
        lines.append("    captured_version: v1.6.14")
        lines.append("")
    with open(os.path.join(root, "screenshots", "manifest.yml"), "w",
              encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def run(root):
    env = dict(os.environ)
    env["BEEFTV_MANUAL_ROOT"] = root
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    p = subprocess.run([sys.executable, os.path.join(root, "scripts", GATE)],
                       capture_output=True, text=True, env=env)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main():
    failures = []
    tmp = tempfile.mkdtemp(prefix="shotpixels-selftest-")
    try:
        def case(name, want_rc, want_in, shots, tree=None):
            d = os.path.join(tmp, name)
            os.makedirs(d, exist_ok=True)
            if tree == "real":
                shutil.copytree(os.path.join(ROOT, "screenshots"),
                                os.path.join(d, "screenshots"))
                os.makedirs(os.path.join(d, "scripts"), exist_ok=True)
                shutil.copy(os.path.join(HERE, GATE), os.path.join(d, "scripts", GATE))
                shutil.copy(os.path.join(HERE, "pngstat.py"),
                            os.path.join(d, "scripts", "pngstat.py"))
            else:
                make_tree(d, shots)
            rc, out = run(d)
            ok = (rc == want_rc) and (want_in in out)
            print("  %s 用例 %-22s rc=%d（期望 %d）%s"
                  % ("✅" if ok else "❌", name, rc, want_rc,
                     "" if ok else "\n      " + out.strip().replace("\n", "\n      ")))
            if not ok:
                failures.append(name)

        # 1 —— 能抓：纯黑图
        case("black-image", 1, "方向一",
             {"a.png": pngstat.solid_png(1280, 720, (0, 0, 0))})

        # 2 —— 能抓：字节够大（过得了方向一）但顶部纯色 → 只有方向二能抓
        noisy = noisy_tail_png(1440, 900, 60, (17, 17, 17))
        f = pngstat.features(noisy, max_rows=40)
        nratio = len(noisy) / float(1440 * 900)
        assert nratio >= MIN_BYTES_PER_PIXEL, \
            "前提失配：噪点图每像素 %.5f 字节（< %.3f），它会被方向一先抓走，测的就不是方向二了" \
            % (nratio, MIN_BYTES_PER_PIXEL)
        assert f["colors"] < MIN_COLORS, \
            "前提失配：噪点图顶部 %d 色 ≥ %d，方向二抓不到它" % (f["colors"], MIN_COLORS)
        case("noisy-tail", 1, "方向二", {"b.png": noisy})

        # 3 —— 能抓：manifest 为空必须 rc=2，**不能报「0 张全部有内容」**
        case("empty-manifest", 2, "未能核对", {})

        # 4 —— 不误伤：颜色数刚过阈值
        rich = rich_top_png(640, 240, MIN_COLORS + 20)
        rf = pngstat.features(rich, max_rows=40)
        rratio = len(rich) / float(640 * 240)
        assert rratio >= MIN_BYTES_PER_PIXEL, \
            "前提失配：这张样本每像素 %.5f 字节（< %.3f），它会被方向一抓走" \
            % (rratio, MIN_BYTES_PER_PIXEL)
        assert rf["colors"] > MIN_COLORS, "前提失配：造出 %d 色" % rf["colors"]
        assert rf["top_share"] <= MAX_TOP_SHARE, "前提失配：主色 %.3f 超阈值" % rf["top_share"]
        case("rich-top", 0, "全部有内容", {"c.png": rich})

        # 5 —— 不误伤：**颜色数少但主色占比不高**的合法图（白底 + 少量方块）
        sp = sparse_png(800, 300, 16)
        sf = pngstat.features(sp, max_rows=40)
        sratio = len(sp) / float(800 * 300)
        assert sratio >= MIN_BYTES_PER_PIXEL, \
            "前提失配：这张样本每像素 %.5f 字节（< %.3f），它会被方向一抓走，测的就不是方向二了" \
            % (sratio, MIN_BYTES_PER_PIXEL)
        assert sf["colors"] < MIN_COLORS, "前提失配：这例本该颜色数 < %d，实得 %d" % (MIN_COLORS, sf["colors"])
        assert sf["top_share"] <= MAX_TOP_SHARE, "前提失配：主色 %.3f 超了" % sf["top_share"]
        assert sf["top_share"] <= MAX_TOP_SHARE, \
            "前提失配：主色 %.4f 已过阈值，这一例本就该被抓" % sf["top_share"]
        case("sparse-ok", 0, "全部有内容", {"d.png": sp})

        # 6 —— 不误伤：真实 67 张
        case("real-shots", 0, "全部有内容", None, tree="real")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    if failures:
        print("❌ %d/6 例失败：%s" % (len(failures), "、".join(failures)))
        return 1
    print("✅ 6/6 例通过（能抓 3 / 不误伤 2 / rc=2 1）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
