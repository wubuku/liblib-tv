"""Jimeng clone batch 827-fsassets verifier — 资产栏从装饰接成真浏览器。

批 825 把全屏时间线做成了可编辑的，但**资产栏还是个装饰**：

- 三个来源页签（已导入资产 / 画布资产 / 全部）与三个类型页签（图片 / 视频 / 音频）
  点了**只切一个 class**，不产出任何结果；
- 那个「资产」框里显示的其实是**时间线的片段列表**
  （`clips.map(c => c.label).join(" / ")`）—— 名不副实。

本批让它成为一个真浏览器：列出画布上的媒体节点，点一下就加进轨道，于是
「资产 → 轨道 → 剪辑」闭环（825 的六枚工具才真正有东西可切）。

⚠️ 三个来源页签的**内容语义没有源站依据**（源站那个 fixture 的媒体全没加载，
没量到过），所以这是**复刻自有的语义决策**，不写成 SOURCE_FACT：

    画布资产   = 画布上的全部媒体节点
    已导入资产 = 其中**还没被加进这条时间线**的那些
    全部       = 全部媒体节点

三个页签因此各有可分辨的含义，而不是三个同义按钮。

⚠️ 本 verifier 的期望值**从 DOM 现推**，不写死资产名/个数 ——
默认画布的节点集是 fixture 决定的（并行 session 也会动它），写死就会变成
「别人的改动一落地我就假失败」。判据落在**关系**上：
「点图片页签 ⇒ 列表里每行都是图片」而不是「列表里恰好有 2 行」。
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "research" / "jimeng-canvas-batch827-2026-10-04"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
VIEWPORT = {"width": 1512, "height": 950}
HYDRATED = """() => { const el = document.getElementById('__next')
  || document.body.firstElementChild || document.body;
  return Object.keys(el).some(k => k.startsWith('__reactFiber$')); }"""

SNAP = r"""() => {
  const o = document.querySelector('[data-testid="timeline-fullscreen"]');
  if (!o) return { err: 'no overlay' };
  const box = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
    return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; };
  const list = o.querySelector('[data-testid="timeline-fs-asset-empty"]');
  // 注意前缀：容器是 `timeline-fs-asset-empty`、提示是 `…-hint`，
  // 资产行才是 `…-asset-row-`。用短前缀会把那两个一起选中。
  const rows = [...o.querySelectorAll('[data-testid^="timeline-fs-asset-row-"]')];
  return {
    err: null,
    assets: box(o.querySelector('[data-testid="timeline-fs-assets"]')),
    listExists: !!list,
    listText: list ? list.textContent.trim() : null,
    hint: (o.querySelector('[data-testid="timeline-fs-asset-hint"]') || {})
      .textContent.trim(),
    rows: rows.map((e) => ({
      testid: e.getAttribute('data-testid'),
      title: (e.querySelector('span') || {}).textContent || '',
      kind: (e.querySelectorAll('span')[1] || {}).textContent || '',
    })),
    clips: [...o.querySelectorAll('[data-testid="timeline-fullscreen-clip"]')]
      .map((e) => e.textContent.trim()),
    overlayText: o.textContent,
  };
}"""


def main() -> int:
    failures: list[str] = []
    checks = 0

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(f"{name}: {detail}")
        print(f"  [{'ok ' if ok else 'FAIL'}] {name}{'' if ok else ' — ' + detail}")

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_context(viewport=VIEWPORT, locale="zh-CN").new_page()
        errs: list[str] = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        try:
            pg.goto(f"{BASE_URL}/jimeng/canvas/demo", wait_until="domcontentloaded")
            pg.wait_for_selector('[data-testid="canvas-fixed-toolbar"]', timeout=60000)
            for _ in range(12):
                if pg.evaluate(HYDRATED):
                    break
                pg.wait_for_timeout(1000)
            else:
                check("复刻已 hydrate", False, "读到 SSR 骨架，其余断言全部无意义")
                return 1
            check("复刻已 hydrate", True)
            zt = ""
            for _ in range(8):
                pg.keyboard.press("Meta+1")
                pg.wait_for_timeout(500)
                zt = pg.locator('[data-testid="canvas-zoom-percent"]').first.inner_text().strip()
                if zt == "100%":
                    break
            check("已归 100% 缩放（重试至信号成立）", zt == "100%", f"zoom={zt!r}")
            if zt != "100%":
                print("\n  未归一成功，后续几何断言无意义 —— 直接中止")
                return 1

            # 造两个媒体节点，保证资产栏有货可列（默认 fixture 的节点集不由我定）
            for label in ("图片", "视频"):
                pg.get_by_label(label, exact=True).first.click()
                pg.wait_for_timeout(900)
            pg.get_by_label("时间线", exact=True).first.click()
            pg.wait_for_selector('[data-testid="timeline-fullscreen-trigger"]', timeout=30000)
            pg.wait_for_timeout(1000)
            pg.locator('[data-testid="timeline-fullscreen-trigger"]').first.click()
            pg.wait_for_selector('[data-testid="timeline-fs-assets"]', timeout=20000)
            pg.wait_for_timeout(900)

            def snap() -> dict:
                d = pg.evaluate(SNAP)
                if d.get("err"):
                    print(f"\n  浮层消失：{d['err']}")
                return d

            print("\n— 资产栏是个真浏览器 —")
            d0 = snap()
            check("资产栏几何未动 [12,60,360,652]", d0["assets"] == [12, 60, 360, 652],
                  str(d0["assets"]))
            check("列表容器恒在（821 依赖它，元素若被条件渲染会直接超时）",
                  d0["listExists"] is True, str(d0["listExists"]))
            check("默认页签（图片）下列出了资产行", len(d0["rows"]) >= 1,
                  f'{len(d0["rows"])} 行')
            check("每行都标了自己的类型", all(r["kind"] in ("图片", "视频", "音频")
                                                for r in d0["rows"]),
                  str([r["kind"] for r in d0["rows"]]))
            check("默认「图片」页签 ⇒ 每行都是图片",
                  all(r["kind"] == "图片" for r in d0["rows"]),
                  str([(r["title"], r["kind"]) for r in d0["rows"]]))
            # 813 逐条断言过这两句，必须始终在浮层里（见 821 遗留约束）
            check("浮层含「没有媒体可供预览」或已列出资产（空态文案机制在）",
                  "没有媒体可供预览" in d0["overlayText"] or len(d0["rows"]) > 0,
                  repr(d0["listText"][:40] if d0["listText"] else None))
            check("拖放提示单独成行且恒在（813 断言其中一句）",
                  d0["hint"] == "将文件拖至此处添加", repr(d0["hint"]))

            print("\n— 页签真的在筛 —")
            pg.locator('[data-testid="timeline-fs-kind-视频"]').click()
            pg.wait_for_timeout(600)
            dv = snap()
            check("切到「视频」⇒ 每行都是视频", all(r["kind"] == "视频" for r in dv["rows"]),
                  str([(r["title"], r["kind"]) for r in dv["rows"]]))
            check("切页签后行数确实变了（筛是有效的，不是恒等）",
                  len(dv["rows"]) != len(d0["rows"]) or not dv["rows"],
                  f'图片 {len(d0["rows"])} 行 → 视频 {len(dv["rows"])} 行')
            pg.locator('[data-testid="timeline-fs-kind-音频"]').click()
            pg.wait_for_timeout(600)
            da = snap()
            check("切到没有对应资产的「音频」⇒ 落到空态文案",
                  len(da["rows"]) == 0 and "没有媒体可供预览" in (da["listText"] or ""),
                  f'{len(da["rows"])} 行 / {da["listText"]!r}')
            pg.locator('[data-testid="timeline-fs-kind-图片"]').click()
            pg.wait_for_timeout(600)

            print("\n— 点资产真的加进轨道 —")
            target = d0["rows"][0]
            pg.locator(f'[data-testid="{target["testid"]}"]').click()
            pg.wait_for_timeout(700)
            d1 = snap()
            check("点资产后轨道出现片段", len(d1["clips"]) >= 1, str(d1["clips"]))
            check("片段名就是那个资产名（不是「片段 N」）",
                  target["title"] in d1["clips"], f'{target["title"]!r} vs {d1["clips"]}')

            print("\n— 「已导入资产」= 还没被加进来的那些 —")
            pg.locator('[data-testid="timeline-fs-source-已导入资产"]').click()
            pg.wait_for_timeout(600)
            d2 = snap()
            check("已导入资产页签里不再出现刚加过的那条",
                  all(target["title"] not in r["title"] for r in d2["rows"]),
                  str([r["title"] for r in d2["rows"]]))
            pg.locator('[data-testid="timeline-fs-source-画布资产"]').click()
            pg.wait_for_timeout(600)
            d3 = snap()
            check("「画布资产」页签里它又出现了（两个页签语义确实不同）",
                  any(target["title"] in r["title"] for r in d3["rows"]),
                  str([r["title"] for r in d3["rows"]]))
            check("「画布资产」行数 ≥「已导入资产」行数",
                  len(d3["rows"]) >= len(d2["rows"]),
                  f'画布 {len(d3["rows"])} / 已导入 {len(d2["rows"])}')

            print("\n— 与投放区是同一套动作（812：同一动作一条行为）—")
            before = len(snap()["clips"])
            pg.locator('[data-testid="timeline-fullscreen-drop"]').click()
            pg.wait_for_timeout(700)
            d4 = snap()
            check("投放区仍能加片段", len(d4["clips"]) == before + 1,
                  f'{before} → {len(d4["clips"])}')
            check("无未捕获页面错误", not errs, "; ".join(errs[:3]))
            pg.screenshot(path=str(EVIDENCE / "clone-fullscreen-827-assets.png"))
        finally:
            b.close()

    print()
    if failures:
        print(f"FAIL batch827-fsassets — {checks} 项中 {len(failures)} 项失败")
        for f in failures:
            print("  -", f)
        return 1
    print(f"PASS batch827-fsassets — {checks} 项断言全通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
