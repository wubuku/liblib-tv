#!/usr/bin/env python3
"""量一张 PNG 里某条水平亮带的左右边界——用来核 alt 文本里的「整条 N 像素宽」。

**为什么需要它（M202）**：手册有 59 张截图的 alt 文本里带可数断言，其中一条是
「整条 **1285 像素**宽」。M160 早就把「靠像素认按钮」判成不可靠做法并写进了账本，
所以看到这条断言时第一反应是「它多半过期了」——**但那是印象，不是读数。**

真去量才发现它是对的，而且**我第一遍量出来的数是错的**：
按亮度阈值 40 量最亮那一行（按钮行）得 **1256**，比 alt 说的 1285 少 29；
换阈值 18、量容器竖直中点那一行（第 46 行）得 **1286**——
**两个数都不是 1285，但都不是「alt 写错了」**：
1256 是按钮行、1286 是容器外沿，alt 记的是容器。
**一次测量只证明一件事**：不先说清量的是哪一层，数字对不上就会被当成错误。

**所以这个工具会同时打印多行、多阈值**，让人自己看清「哪一层是多少」，
而不是只吐一个数然后等人猜。

用法：
    python3 scripts/measure-screenshot-width.py screenshots/04-edit-nodes-toolbar-labels-on.png
    python3 scripts/measure-screenshot-width.py <png> [阈值，默认 40]

只依赖标准库（zlib + struct 手写 PNG 解码），不装任何东西。
只读——**不修改任何图片**。
"""

from __future__ import annotations

import struct
import sys
import zlib
from pathlib import Path


def read_png(path: Path):
    """解一张 8 位 RGB/RGBA 的 PNG，返回 (宽, 高, 通道数, 每行的字节数组)。"""
    b = path.read_bytes()
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"不是 PNG：{path}")
    pos, idat, w, h, nch = 8, b"", None, None, None
    while pos < len(b):
        ln = struct.unpack(">I", b[pos:pos + 4])[0]
        typ = b[pos + 4:pos + 8]
        data = b[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, depth, color = struct.unpack(">IIBB", data[:10])
            if depth != 8 or color not in (2, 6):
                raise SystemExit(f"只支持 8 位 RGB/RGBA，本图 depth={depth} color={color}")
            nch = 3 if color == 2 else 4
        elif typ == b"IDAT":
            idat += data
        elif typ == b"IEND":
            break
        pos += 12 + ln
    raw = zlib.decompress(idat)
    stride = w * nch
    rows, prev, p = [], bytearray(stride), 0
    for _ in range(h):
        f = raw[p]; p += 1
        line = bytearray(raw[p:p + stride]); p += stride
        if f == 1:
            for i in range(nch, stride):
                line[i] = (line[i] + line[i - nch]) & 0xFF
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif f == 3:
            for i in range(stride):
                a = line[i - nch] if i >= nch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif f == 4:
            for i in range(stride):
                a = line[i - nch] if i >= nch else 0
                b2 = prev[i]
                c = prev[i - nch] if i >= nch else 0
                pp = a + b2 - c
                pa, pb, pc = abs(pp - a), abs(pp - b2), abs(pp - c)
                pr = a if (pa <= pb and pa <= pc) else (b2 if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        rows.append(line)
        prev = line
    return w, h, nch, rows


def longest_run(xs: list[int]) -> tuple[int, int] | None:
    """在亮像素下标里找最长的一段连续区间（允许 3 像素的断裂，容忍抗锯齿噪点）。"""
    if not xs:
        return None
    best = (xs[0], xs[0]); s = p = xs[0]
    for x in xs[1:]:
        if x - p > 3:
            if p - s > best[1] - best[0]:
                best = (s, p)
            s = x
        p = x
    if p - s > best[1] - best[0]:
        best = (s, p)
    return best


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"找不到文件：{path}")
        return 1
    w, h, nch, rows = read_png(path)
    print(f"{path.name}  {w} × {h}（{nch} 通道）")
    print("★ 同一个东西有多层：按钮行、容器外沿、裁剪留边——**先说清量的是哪一层**。\n")
    for thr in (18, 24, 30, 40, 60):
        hits = []
        for y in range(h):
            r = rows[y]
            lit = [x for x in range(w)
                   if (r[x * nch] + r[x * nch + 1] + r[x * nch + 2]) / 3 > thr]
            run = longest_run(lit)
            if run:
                hits.append((run[1] - run[0] + 1, y, run))
        if not hits:
            continue
        width, y, (lo, hi) = max(hits)
        print(f"  阈值 {thr:3d}：最宽处在第 {y:3d} 行，x={lo} → {hi}，"
              f"宽 **{width}** 像素（左边距 {lo}、右边距 {w - 1 - hi}）")
    print("\n  左边距与右边距接近时，说明这条亮带是被居中的容器，数字可以直接和 alt 对账；")
    print("  两边距差很多时，先确认量的是不是同一层——**别急着判定 alt 写错了**。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
