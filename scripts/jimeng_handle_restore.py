#!/usr/bin/env python3
"""Batch 805 收尾 A：复原源站画布 + 抓「视频节点选中态」的真实像素。

两件事：

1. **复原**。探针的落点选择前几轮一直点在节点中心附近，而源站画布上
   4~6 个音频节点几乎完全叠在视频节点上；连续几轮点选在源站被判定为
   连击，**凭空多出「音频 5」「音频 6」两个节点**。原始基线（探针一首次
   测量）是「视频 1 + 音频 1..4」。这里把多出来的节点选中删掉，删完核对
   节点清单回到基线。删除是还原操作，不是新建，不触发任何计费。

2. **抓像素**。computed style 一直显示源站 + 钮 `bg=透明 / border=透明 /
   pointer-events:none`，这与「用户能看见并点击它」矛盾。与其继续猜
   CSS，不如直接截选中态的图看真实像素（脚本会顺带报该区域的最常见颜色）。

用法:
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
        scripts/jimeng_handle_restore.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

NODES = """() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const b = n.getBoundingClientRect();
  return { aria: n.getAttribute('aria-label'), selected: n.classList.contains('selected'),
           rect: { x: Math.round(b.x), y: Math.round(b.y),
                   w: Math.round(b.width), h: Math.round(b.height) } };
})"""

OUT = Path("docs/research/jimeng-canvas-batch805-2026-10-03")


def shot(pg, path: Path, clip: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pg.screenshot(path=str(path), clip=clip)


def dominant(pg, clip: dict) -> list:
    """截一小块，返回出现最多的颜色（用来判「+ 钮到底有没有底色」）。"""
    import io

    from PIL import Image

    buf = pg.screenshot(clip=clip)
    im = Image.open(io.BytesIO(buf)).convert("RGBA")
    c = Counter(im.getdata())
    return [[list(rgb), n] for rgb, n in c.most_common(6)]


def main() -> int:
    # jimeng_headless.py run 注入的全局是 page（不是 pg）
    pg = globals().get("page")
    if pg is None:
        raise SystemExit("请经 jimeng_headless.py run 调用本脚本")
    url = "https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create"
    pg.goto(url, wait_until="domcontentloaded")
    pg.wait_for_timeout(6500)
    for _ in range(14):
        pg.keyboard.press("Meta+0")
        pg.wait_for_timeout(120)
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(800)

    before = pg.evaluate(NODES)
    print("清理前节点:", json.dumps(before, ensure_ascii=False))

    # 只删基线之外的节点：基线 = 视频 1 + 音频 1..4
    baseline = {"视频 node: 视频 1", "音频 node: 音频 1", "音频 node: 音频 2",
                "音频 node: 音频 3", "音频 node: 音频 4"}
    extra = [n for n in before if n["aria"] not in baseline]
    print("多出的节点:", [n["aria"] for n in extra])

    if extra:
        # 先点第一个（选中），再 Shift 加选其余，最后 Delete
        first = extra[0]
        pg.mouse.click(first["rect"]["x"] + 20, first["rect"]["y"] + 20)
        pg.wait_for_timeout(900)
        for n in extra[1:]:
            pg.keyboard.down("Shift")
            pg.mouse.click(n["rect"]["x"] + 20, n["rect"]["y"] + 20)
            pg.keyboard.up("Shift")
            pg.wait_for_timeout(700)
        sel = [n["aria"] for n in pg.evaluate(NODES) if n["selected"]]
        print("删除前选中:", sel)
        pg.keyboard.press("Delete")
        pg.wait_for_timeout(1500)
        pg.keyboard.press("Backspace")
        pg.wait_for_timeout(1200)

    after = pg.evaluate(NODES)
    print("清理后节点:", json.dumps(after, ensure_ascii=False))
    ok = {n["aria"] for n in after} == baseline
    print("复原核对:", "PASS —— 回到基线" if ok else f"FAIL —— 仍多出 {[n['aria'] for n in after if n['aria'] not in baseline]}")

    # ---- 抓「视频节点选中」的真实像素 ----
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(600)
    vid = next((n for n in after if n["aria"] == "视频 node: 视频 1"), None)
    if not vid:
        print("找不到视频节点，跳过截图")
        return 0 if ok else 1
    r = vid["rect"]
    # 落点：视频卡片左上角空白处（音频节点都压在中间，见探针二 blocked=0 的解）
    pg.mouse.click(r["x"] + 46, r["y"] + 19)
    pg.wait_for_timeout(1600)
    sel = [n["aria"] for n in pg.evaluate(NODES) if n["selected"]]
    print("截图前选中:", sel)
    if sel != ["视频 node: 视频 1"]:
        print("未能选中视频节点，跳过截图")
        return 0 if ok else 1

    # 左侧 + 钮：源站实测圆心在节点左缘外 21px、垂直居中
    lx, ly = r["x"] - 21, r["y"] + r["h"] / 2
    clip = {"x": max(0, lx - 60), "y": max(0, ly - 45),
            "width": 200, "height": 90}
    shot(pg, OUT / "804-source-plus-left.png", clip)
    print("左侧 + 钮区域主色:", json.dumps(dominant(pg, clip), ensure_ascii=False))

    # 右侧 + 钮
    rx = r["x"] + r["w"] + 21
    clip_r = {"x": min(1512 - 200, rx - 100), "y": max(0, ly - 45),
              "width": 200, "height": 90}
    shot(pg, OUT / "804-source-plus-right.png", clip_r)
    print("右侧 + 钮区域主色:", json.dumps(dominant(pg, clip_r), ensure_ascii=False))

    # 整节点上下文
    shot(pg, OUT / "804-source-video-selected.png",
         {"x": max(0, r["x"] - 70), "y": max(0, r["y"] - 30),
          "width": min(760, 1512 - max(0, r["x"] - 70)), "height": 380})

    # 复原：取消选中
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(600)
    print("最终节点数:", len(pg.evaluate(NODES)))
    return 0 if ok else 1


main()
