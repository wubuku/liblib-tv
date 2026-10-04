#!/usr/bin/env python3
"""截图尺寸对账扫描（M223 建立）：把 manifest 的 `viewport` 字段与 PNG 实物宽高逐条对照。

★ **它不是门禁，是分析工具**——这一点必须先说清楚，否则下一个人会想去把它接进
  `build-site.sh`，然后被 26 条假阳性逼到把判据放宽到没有意义（那就是 M195 踩过的坑）。

## 为什么不能直接做成门禁

`viewport` 这个字段在库里**一词三义**，三种含义混在同一个键上：

1. **浏览器视口**——如 `1280x720`，44 张实物就是 1280×720；
2. **裁剪区**——如 `16-use-agent-skills` 实物 454×950，登记的却是视口 `1440x950`；
3. **设备像素**——如 `30-concepts-reference-unused` 实物 2880×1800 = 视口 `1440x900` 的 2 倍。

**所以「实物宽高 == 字段开头的 NxM」这条判据在 112 条里会报 26 条，其中 25 条是假阳性。**
试过把它收窄成「字段里若出现 deviceScaleFactor / xN / 裁剪区 这类可算关系，就按关系对账」，
**照样误报**，因为库里的关系标注本身不自洽：

- `16-use-agent-status-dot` 登记 `600x128 (deviceScaleFactor 4)`，而实物就是 600×128（**1×**）；
- `11-shortcuts-help-modal-full` 登记 `520x749 (弹窗自身边界框)`，而实物是 1040×1498（**2×**）；
- `20-config-sidebar-not-nav` 等五条写了「裁剪区 NxM (CSS px)」却**没写 deviceScaleFactor**，
  实物全是 2×。

**要让它变成门禁，得先给 112 条逐条决定「这个字段到底指什么」——那是内容判断，不是判据能替的。**
M195 的原话照抄在这里：**窄不到能全对，就别假装是门禁。**

## 那它能抓到什么

**抓「字段自述的关系与实物对不上」这一类**——本批的 R72 就是这么抓到的：
`20-nav-bilingual` 登记 `1280x48 x2`，而实物 1280×108。
逐行插桩实测结构是 48（上条）+ 12（间隔带）+ 48（下条）= 108，
且 CJK 字形高 16px 对应 1× 设备像素比——**怎么读都对不上**。

## 怎么复跑

    python3 scripts/audit-screenshot-dims.py .

不依赖 Pillow（直接读 PNG 头 24 字节的 IHDR），也不依赖浏览器。
"""

from __future__ import annotations

import re
import struct
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("[FAIL] 需要 PyYAML：python3 -m pip install pyyaml")
    raise SystemExit(2)

# 字段里出现的「可算关系」标注。三类都试，只用来**分类**，不用来判对错。
DSR = re.compile(r"deviceScaleFactor\s*(\d+(?:\.\d+)?)", re.I)
MULT = re.compile(r"\bx\s*(\d+(?:\.\d+)?)\b")
CROP = re.compile(r"裁剪区\s*(\d+)x(\d+)")
LEAD = re.compile(r"^(\d+)x(\d+)")


def png_size(path: Path) -> tuple[int, int]:
    """只读 PNG 头 24 字节的 IHDR 取宽高——不装 Pillow、不解码像素。"""
    with path.open("rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} 不是 PNG")
    return struct.unpack(">II", head[16:24])


def classify(viewport: str, real: tuple[int, int]) -> tuple[str, str]:
    """返回 (分类, 说明)。分类取值刻意分成「说得清」和「说不清」两类。"""
    lead = LEAD.match(viewport.strip())
    if lead and (int(lead.group(1)), int(lead.group(2))) == real:
        return "一致", f"字段开头的 {lead.group(0)} 就是实物尺寸"

    # 自述了可算关系：把所有读法都算一遍，看有没有一种能落到实物
    tries: list[str] = []
    dsr = DSR.search(viewport)
    crop = CROP.search(viewport)
    mult = MULT.search(viewport)
    if crop:
        cw, ch = int(crop.group(1)), int(crop.group(2))
        for k in ({float(dsr.group(1))} if dsr else {1, 2, 4}):
            if (round(cw * k), round(ch * k)) == real:
                tries.append(f"裁剪区 {cw}x{ch} × {k:g}")
    if lead and dsr:
        lw, lh = int(lead.group(1)), int(lead.group(2))
        k = float(dsr.group(1))
        if (round(lw * k), round(lh * k)) == real:
            tries.append(f"{lead.group(0)} × deviceScaleFactor {k:g}")
    if lead and mult:
        lw, lh = int(lead.group(1)), int(lead.group(2))
        k = float(mult.group(1))
        if (round(lw * k), round(lh * k)) == real:
            tries.append(f"{lead.group(0)} × {k:g}")

    if tries:
        return "自述且对得上", "；".join(tries)
    # ★ 对不上账：字段自述了关系，却怎么算都不是实物
    if crop or dsr or mult:
        return "★ 对不上账", "字段自述了裁剪区/倍数/DPR，但没有一种读法能落到实物"
    return "含义不明", "既不等于实物、又没自述是视口/裁剪区/设备像素中的哪一种"


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    man = root / "screenshots/manifest.yml"
    if not man.is_file():
        print(f"[FAIL] 找不到 {man}")
        return 1
    items = yaml.safe_load(man.read_text(encoding="utf-8"))["screenshots"]

    buckets: dict[str, list[tuple[str, str, str, str]]] = {}
    missing: list[str] = []
    for it in items:
        rel = it.get("file", "")
        name = Path(rel).name
        p = root / rel
        if not p.is_file():
            missing.append(name)
            continue
        vp = str(it.get("viewport", ""))
        real = png_size(p)
        kind, why = classify(vp, real)
        buckets.setdefault(kind, []).append((name, vp, f"{real[0]}x{real[1]}", why))

    total = sum(len(v) for v in buckets.values())
    print(f"共 {total} 张（清单 {len(items)} 条）")
    for kind in ("一致", "自述且对得上", "含义不明", "★ 对不上账"):
        rows = buckets.get(kind, [])
        print(f"\n== {kind}：{len(rows)} 张 ==")
        if kind == "一致":
            continue  # 44 张全对，不逐条刷屏
        for name, vp, real, why in rows:
            print(f"  {name}\n      登记 {vp}\n      实物 {real}\n      {why}")

    if missing:
        print(f"\n[FAIL] 清单里有 {len(missing)} 张文件不存在：{missing}")
        return 1

    bad = buckets.get("★ 对不上账", [])
    print("=" * 72)
    if bad:
        print(f"[注意] 有 {len(bad)} 条「自述了关系却对不上账」——**这类才是真缺陷**（R72 就是这么抓到的）。")
        print("       「含义不明」那几条不算错，只是字段没写清自己指哪一种。")
        return 0  # 分析工具只出候选清单，不 fail 构建
    print("[ ok ] 没有「自述了关系却对不上账」的条目。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
