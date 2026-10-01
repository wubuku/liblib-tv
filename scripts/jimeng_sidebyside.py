#!/usr/bin/env python3
"""Batch 807 取证：源站 vs 复刻 的**并排像素比对**，用来找下一批该修什么。

为什么需要它：台账里的候选清单（右簇 1px、生成素材栏…）是上一轮规划时
列的，源站线上此后又动过几次。与其按旧清单猜下一个 batch，不如把两侧
同一状态的整屏截下来并排放大看，**让差异自己指出目标**。

比对的两个区域选「锚在视口边角、与内容无关」的固定条带，这样两侧画布
视口/缩放不同也不影响对齐：
  - 顶栏 y∈[0,64)
  - 左栏 x∈[0,72)
两段各存一份并排拼图（源站在左、复刻在右），供人眼判读；同时输出
逐列亮度剖面的差异排名，给「哪一列开始不一样」一个可复核的数字。

用法:
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
        scripts/jimeng_sidebyside.py
"""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image

SOURCE = (
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create"
)
CLONE = "http://localhost:4317/jimeng/canvas/demo"
OUT = Path("docs/research/jimeng-canvas-batch807-2026-10-03")
VW, VH = 1680, 826


def grab(pg, url: str) -> Image.Image:
    pg.goto(url, wait_until="domcontentloaded")
    pg.wait_for_timeout(9000 if "jimeng.jianying" in url else 3000)
    for _ in range(14):
        pg.keyboard.press("Meta+0")
        pg.wait_for_timeout(110)
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(900)
    return Image.open(io.BytesIO(pg.screenshot())).convert("RGB")


def side_by_side(a: Image.Image, b: Image.Image, box, gap: int = 8) -> Image.Image:
    ca, cb = a.crop(box), b.crop(box)
    w, h = ca.size
    out = Image.new("RGB", (w * 2 + gap, h), (255, 0, 255))
    out.paste(ca, (0, 0))
    out.paste(cb, (w + gap, 0))
    return out


def col_profile(im: Image.Image, box, axis: str = "x"):
    c = im.crop(box).convert("L")
    px = c.load()
    w, h = c.size
    if axis == "x":
        return [max(px[x, y] for y in range(h)) for x in range(w)]
    return [max(px[x, y] for x in range(w)) for y in range(h)]


def diff_report(pa, pb, label: str) -> None:
    n = min(len(pa), len(pb))
    rows = [(abs(pa[i] - pb[i]), i, pa[i], pb[i]) for i in range(n)]
    rows.sort(reverse=True)
    bad = [r for r in rows if r[0] > 12]
    print(f"\n[{label}] 长度 {n}，显著差异位 {len(bad)} 个（阈值 12/255）")
    for d, i, x, y in rows[:14]:
        print(f"   pos {i:4d}: 源 {x:3d} vs 复刻 {y:3d}  (Δ{d})")


def main() -> int:
    pg = globals()["page"]
    OUT.mkdir(parents=True, exist_ok=True)
    src = grab(pg, SOURCE)
    clo = grab(pg, CLONE)
    src.save(OUT / "807-source-full.png")
    clo.save(OUT / "807-clone-full.png")
    print(f"源站 {src.size} / 复刻 {clo.size}")

    regions = {
        "topbar": ((0, 0, VW, 64), "x"),
        "rail": ((0, 64, 72, VH), "y"),
    }
    for name, (box, axis) in regions.items():
        im = side_by_side(src, clo, box)
        # 放大 2 倍便于判读
        im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
        im.save(OUT / f"807-{name}-sbs.png")
        diff_report(
            col_profile(src, box, axis), col_profile(clo, box, axis), name
        )
    print(f"\n并排图写入 {OUT}")
    return 0


main()
