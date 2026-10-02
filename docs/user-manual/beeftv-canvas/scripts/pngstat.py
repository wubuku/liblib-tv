#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PNG 像素统计（Batch 191 新增）——**零外部依赖**地读出一张图的尺寸与颜色分布。

**为什么不用 Pillow**：判据一旦依赖装不上的东西，报出来的是 `ImportError` 崩掉，
**而崩溃不是「未能核对」**（纪律 101：解析器退化必须表现为失败，而不是通过——
更不能表现为「构建挂在一个第三方包没装上」）。本仓的共用模块
（`baseline.py` / `batchread.py` / `scope.py`）一律零外部依赖，
反验在任何环境都跑得起来——**这条比「少写 200 行」重要**。

**格式范围是量出来的，不是猜的**：本手册 67 张截图实测**全部**是
**8-bit、非隔行**，颜色类型只有 **RGB(2) 66 张**与 **RGBA(6) 1 张**。
所以本模块只实现这几条路径，遇到别的组合**抛 `PngError` 而不是猜**——
**解码出错必须让判据红，不许它悄悄按「全白」处理**。

**为什么要自己解滤波**（这一段是性能的全部来源）：PNG 每行开头一个字节是
filter 类型，其后是**预测值**，真实像素要逐行反滤波还原。实测前 40 行的 filter
分布是 **Paeth 71.3% / Sub 15.0% / Up 9.9% / Average 3.8%**——
**Paeth 依赖同行左侧像素，无法向量化**，而它是绝大多数。
纯 Python 逐像素解完 67 张的**前 40 行**要约 **5 秒**（实测 4.9s）。
为了省时间去解整张（400 行）要 **45 秒**（实测），那会让构建慢一倍，
**所以本模块支持 `max_rows`：只解顶部若干行**。

**但 `max_rows` 的取值不是随手定的**，判据侧的论证见 `verify-shot-pixels.py`：
顶部采样对「**整图退化**」（纯色 / 全白 / 加载失败）**是充分的**——
这类图**任何一行都退化**；而它对「界面是否正确」**没有分辨力**，
那需要 OCR，超出零依赖的范围。**这条边界必须写在判据里，不能让人误以为它什么都管。**

**顺带记一个实测事实，它是本模块存在的理由之一**：顶部 40 行的颜色分布
**分不开不同的界面**——`47`/`48`/`49` 三张字幕相关截图的顶部**完全相同**
（79 色 / 主色 78.65%）。所以任何拿顶部特征当「界面指纹」的用法都会错。
"""

import struct
import zlib
from collections import Counter


class PngError(RuntimeError):
    """不是可支持的 PNG，或已损坏。调用方应把它当成 rc=2「未能核对」。"""


PNG_SIG = b"\x89PNG\r\n\x1a\n"

#: 颜色类型 → 每像素字节数
_BPP = {0: 1, 2: 3, 3: 1, 6: 4}
#: 本模块承诺支持的子集。实测本手册 67 张全落在 (8, 2) 与 (8, 6)。
_SUPPORTED_TYPES = (0, 2, 3, 6)


def _chunks(data):
    """逐个吐出 (类型, 负载)。"""
    if data[:8] != PNG_SIG:
        raise PngError("不是 PNG（签名不对）")
    pos = 8
    while pos + 8 <= len(data):
        ln = int.from_bytes(data[pos:pos + 4], "big")
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        if len(body) < ln:
            raise PngError("PNG 在 %r 块处被截断" % typ)
        yield typ, body
        pos += 12 + ln
        if typ == b"IEND":
            return
    raise PngError("PNG 没有 IEND 块（文件被截断？）")


def read_header(data):
    """从**原始字节**读出 `(宽, 高, 位深, 颜色类型, 是否隔行)`。"""
    for typ, body in _chunks(data):
        if typ == b"IHDR":
            if len(body) < 13:
                raise PngError("IHDR 块太短")
            w = int.from_bytes(body[0:4], "big")
            h = int.from_bytes(body[4:8], "big")
            return w, h, body[8], body[9], body[12]
        if typ == b"IDAT":
            break
    raise PngError("PNG 里找不到 IHDR 块")


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def _unfilter(raw, w, h, bpp, max_rows):
    """逐行反滤波，最多处理 `max_rows` 行。返回 `(行数, 每行 bytes)`。"""
    stride = w * bpp
    prev = bytearray(stride)
    rows = []
    off = 0
    limit = min(max_rows, h)
    for _ in range(limit):
        if off + 1 + stride > len(raw):
            break
        ft = raw[off]
        line = bytearray(raw[off + 1:off + 1 + stride])
        off += 1 + stride
        if ft == 0:
            pass
        elif ft == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif ft == 2:
            # Up 与同行无关，可以向量化（实测只占 9.9%，但省下来的都是纯 Python 循环）
            line = bytearray((x + y) & 0xFF for x, y in zip(line, prev))
        elif ft == 3:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif ft == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + _paeth(a, b, c)) & 0xFF
        else:
            raise PngError("未知的 filter 类型 %d" % ft)
        rows.append(bytes(line))
        prev = line
    return rows


def features(data, max_rows=40):
    """解一张 PNG 的前 `max_rows` 行，返回颜色分布特征。

    返回 `{'width', 'height', 'rows', 'pixels', 'colors', 'top_share'}`：
      · `colors`   —— 采样范围内出现过的**不同颜色**个数；
      · `top_share`—— 出现最多的那种颜色占采样像素的比例（0..1）。

    **为什么颜色按三元组计而不管 alpha**：RGBA 的 alpha 几乎全 255，
    把它算进去只会让「不同颜色」虚高，**判据过宽比过严坏**——
    它会让真退化的图也混过去。
    """
    w, h, depth, ctype, interlace = read_header(data)
    if depth != 8:
        raise PngError("位深 %d 不支持（本模块只实现 8-bit，范围是实测出来的）" % depth)
    if interlace != 0:
        raise PngError("隔行 PNG 不支持（本手册实测 67 张全部非隔行）")
    if ctype not in _SUPPORTED_TYPES:
        raise PngError("颜色类型 %d 不支持" % ctype)
    bpp = _BPP[ctype]

    idat = bytearray()
    for typ, body in _chunks(data):
        if typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            break
    if not idat:
        raise PngError("PNG 里没有 IDAT（像素数据）")

    try:
        raw = zlib.decompress(bytes(idat))
    except zlib.error as exc:
        raise PngError("IDAT 解压失败（文件已损坏）：%s" % exc)

    rows = _unfilter(raw, w, h, bpp, max_rows)
    if not rows:
        raise PngError("一行都没解出来（PNG 高度为 0 或数据不足）")

    # 用 Counter 而不是 dict：统计这段是纯 Python 热循环，
    # **Counter 的计数走 C**。实测同样 67 张 6.1s → 5.0s（省的是这一段，不是反滤波）。
    counts = Counter()
    for line in rows:
        if ctype in (2, 6):
            step = 3 if ctype == 2 else 4
            counts.update(zip(line[0::step], line[1::step], line[2::step]))
        else:                       # 灰度 / 索引色：按灰度值当颜色
            counts.update(zip(line, line, line))
    total = sum(counts.values())
    top = max(counts.values())
    return {"width": w, "height": h, "rows": len(rows), "pixels": total,
            "colors": len(counts), "top_share": top / total if total else 1.0}


def build_png(width, height, rows):
    """由**逐行的 RGB 字节**造一张 PNG 的原始字节。

    给反验用：判据的输入必须能被随意造出来（纯色图、顶部纯色下方有噪点的图、
    颜色数刚好在阈值上下的图），否则「能抓」那一半就只能靠改真手册来验。
    **造样本和读样本放在同一个模块里，是因为它们共用同一套 PNG 约定**——
    约定只写一遍，就不会出现「读的那边支持 5 种 filter、造的那边只支持 3 种」。
    """
    raw = bytearray()
    n = 0
    for line in rows:
        if len(line) != width * 3:
            raise PngError("每行必须是 %d 字节（RGB），实得 %d" % (width * 3, len(line)))
        raw.append(0)                                   # filter = None
        raw += line
        n += 1
    if n == 0:
        raise PngError("至少要一行")
    def chunk(typ, body):
        return (struct.pack(">I", len(body)) + typ + body
                + struct.pack(">I", zlib.crc32(typ + body) & 0xFFFFFFFF))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (PNG_SIG + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def solid_png(width, height, rgb):
    """造一张**纯色** PNG 的原始字节。"""
    line = bytes(rgb) * width
    return build_png(width, height, [line] * height)
