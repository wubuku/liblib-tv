"""Jimeng clone batch 830-trackcanvas verifier — 补上源站那枚 canvas，解开 829-a。

批 820 的注释一直写着「内层 `timeline-track-canvas` 是 `min-w-full`」，但复刻里
**从来没有这个元素** —— 刻度尺与片段轨道是滚动容器的直接孩子。批 829 对表时发现
源站刻度/片段比其它元素再往右 6px，本批把源站那层 canvas 按实测补出来。

### 829-a 的答案：`min-w-full` 在源站设计系统里是 `calc(100% - 6px)`

829 记下的「矛盾」是：canvas 实测宽 1126，容器 1132，而 canvas 类名带 `min-w-full`
（若按 `min-width:100%` 理解，canvas 至少该 1132）。

实测 `getComputedStyle(canvas).minWidth` = **`calc(100% - 6px)`** —— 矛盾不存在。
那 6px 的 `margin-left` 正是在 min-width 里被**补偿**掉的：

    margin-left(6) + min-width(100% − 6) = 100%      既不溢出也不留缝

⚠️ 补一句更准的机制（本批 verifier 的反向自检逼出来的）：**宽度从 1132 缩到 1126，
主要是 block 的 auto 宽度被 `margin-left:6px` 挤掉的**；`min-width:calc(100% - 6px)`
起的是**下限保证**作用（内容再窄也不会小于 1126）。两个机制指向同一个数，所以抽掉
margin 后宽度回到 1132 —— 两个属性缺一不可，各自的作用还不一样。

**我当时错在假设了工具类的字面含义。** `min-w-full` 读起来像 `min-width:100%`，
但在源站那套设计系统里它带了这 6px 补偿。所以「反推出来的值要连同它的前提一起
复核」这条教训（§41）在这里又应验了一次：错的不只是数值，还有**对工具语义的假设**。

源站结构（实测）：

    滚动容器 [67,67,1132,139]  overflow:hidden
      └ canvas [73,67,1126,139]  display:flex / flex-col / margin-left:6px
                               min-width:calc(100% - 6px)
          ├ 刻度尺 [73, 67,1126, 27]
          └ 片段行 [73,100,1126, 84]      ← 尺下方 6px 间隙（canvas 的 gap）

### 顺带订正：投放区是**满宽**，不是 1113

台账 §27.5（批 818）记「投放区 `[73,100,1113,84]`」。本次新鲜实测投放区
`[73,100,**1126**,84]`，与片段行同宽同位，源站片段行 `padding: 0px/0px`。
两次新鲜读数（829、830）都是满宽。差的 13 恰是 §41 里那条同样错掉的「13px」。
故复刻去掉片段行的 `px-3`（源站零内边距），投放区随之变满宽。

⚠️ **保持不动**的一项：片段自身的 12px 左内缩（`left: 12 + …`）。源站片段矩形
未取证（fixture 媒体长期不加载，源站那条时间线一直是空的），改它等于拿一个猜的数
换另一个猜的数 ⇒ OPEN_QUESTION 830-a。

### 契约

  ① canvas 存在，且 min-width 恰为 `calc(100% - 6px)`、margin-left 恰为 6px
  ② 四个矩形逐项对上源站绝对值：canvas / 刻度尺 / 片段行 / 投放区
  ③ 尺与片段行之间**恰好** 6px 间隙（不是碰巧：源站是 flex-col + gap）
  ④ 空态无多余滚动余量（6 + (100%−6) = 100% 的直接推论）
  ⑤ 反向自检：抽掉 canvas 的 ml-6，三处必须精确回到 x=67 / 宽 1132
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "research" / "jimeng-canvas-batch830-2026-10-04"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
VIEWPORT = {"width": 1512, "height": 950}

HYDRATED = """() => { const el = document.getElementById('__next')
  || document.body.firstElementChild || document.body;
  return Object.keys(el).some(k => k.startsWith('__reactFiber$')); }"""

SOURCE = {
    "scroll":     [67, 67, 1132, 139],
    "canvas":     [73, 67, 1126, 139],
    "ruler":      [73, 67, 1126, 27],
    "clipTrack":  [73, 100, 1126, 84],
    "addClip":    [73, 100, 1126, 84],
}

SNAP = r"""() => {
  const node = document.querySelector('[data-testid="timeline-node"]');
  if (!node) return { err: 'no timeline node' };
  const q = (t) => node.querySelector('[data-testid="' + t + '"]');
  const canvas = q('timeline-track-canvas');
  if (!canvas) return { err: 'no canvas（批 830 新增的那层）' };
  const nr = node.getBoundingClientRect();
  const rd = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
    return [Math.round(r.x - nr.x), Math.round(r.y - nr.y),
            Math.round(r.width), Math.round(r.height)]; };
  const cs = getComputedStyle(canvas);
  const scroll = q('timeline-track-scroll');
  const ruler = q('timeline-ruler');
  const clip = q('timeline-clip-track');
  return {
    err: null,
    canvas: rd(canvas), ruler: rd(ruler), clipTrack: rd(clip),
    addClip: rd(q('timeline-add-clip')), scroll: rd(scroll),
    canvasMinWidth: cs.minWidth, canvasMarginLeft: cs.marginLeft,
    canvasDisplay: cs.display, canvasFlexDir: cs.flexDirection,
    canvasRowGap: cs.rowGap,
    scrollClientW: scroll ? scroll.clientWidth : null,
    scrollScrollW: scroll ? scroll.scrollWidth : null,
    rulerBottom: ruler ? Math.round(ruler.getBoundingClientRect().bottom - nr.y) : null,
    clipTop: clip ? Math.round(clip.getBoundingClientRect().top - nr.y) : null,
  };
}"""

TOGGLE_ML = """(on) => { const c = document.querySelector(
  '[data-testid="timeline-track-canvas"]');
  c.style.marginLeft = on ? '0px' : ''; }"""


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
            check("已归 100% 缩放", zt == "100%", f"zoom={zt!r}")
            if zt != "100%":
                print("\n  未归一成功，几何断言无意义 —— 直接中止")
                return 1

            # ⚠️ 顺序：先插入时间线节点，再等壳（壳在插入前不存在）。
            pg.get_by_label("时间线", exact=True).first.click()
            pg.wait_for_selector('[data-testid="timeline-track-canvas"]', timeout=30000)
            pg.wait_for_timeout(1000)

            d = pg.evaluate(SNAP)
            if d.get("err"):
                print(f"\n  {d['err']}")
                return 1
            EVIDENCE.mkdir(parents=True, exist_ok=True)
            (EVIDENCE / "clone-trackcanvas.json").write_text(
                __import__("json").dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

            print("\n— ① canvas 自身的三个关键值 —")
            check("canvas min-width = calc(100% - 6px)（源站实测：6px 边距在此被补偿）",
                  d["canvasMinWidth"] == "calc(100% - 6px)", repr(d["canvasMinWidth"]))
            check("canvas margin-left = 6px", d["canvasMarginLeft"] == "6px",
                  repr(d["canvasMarginLeft"]))
            check("canvas 是 flex 列容器（源站 display:flex / flex-direction:column）",
                  d["canvasDisplay"] == "flex" and d["canvasFlexDir"] == "column",
                  f'{d["canvasDisplay"]}/{d["canvasFlexDir"]}')

            print("\n— ② 四个矩形逐项对源站绝对值 —")
            for key, label in (("scroll", "滚动容器"), ("canvas", "canvas"),
                               ("ruler", "刻度尺"), ("clipTrack", "片段行"),
                               ("addClip", "投放区")):
                want = SOURCE[key]
                check(f"{label} {want}", d[key] == want, f'实得 {d[key]}')

            print("\n— ③ 尺与片段行之间恰好 6px 间隙 —")
            gap = d["clipTop"] - d["rulerBottom"]
            check("刻度尺底 → 片段行顶 = 6px（源站 flex-col + gap，不是碰巧）",
                  gap == 6, f'gap={gap}（尺底 {d["rulerBottom"]} → 行顶 {d["clipTop"]}）')

            print("\n— ④ 空态无多余滚动余量（6 + (100%−6) = 100% 的推论）—")
            check("滚动容器 scrollWidth − clientWidth ≤ 1",
                  d["scrollScrollW"] - d["scrollClientW"] <= 1,
                  f'scrollW={d["scrollScrollW"]} clientW={d["scrollClientW"]}')

            print("\n— ⑤ 反向自检：抽掉 ml-6，三处必须精确回退 —")
            pg.evaluate(TOGGLE_ML, True)
            pg.wait_for_timeout(300)
            off = pg.evaluate(SNAP)
            pg.evaluate(TOGGLE_ML, False)
            pg.wait_for_timeout(300)
            back = pg.evaluate(SNAP)
            # 期望值取**批 829 之后**的数（容器 1132），不是 829 之前的 1133 ——
            # 829 补了壳的 1px 边框，容器已从 1133 收成 1132。
            # 顺带把机制说明白：宽度从 1132 缩到 1126，**主要是 block 的 auto 宽度
            # 被 margin-left 挤掉 6px**；`min-width: calc(100% - 6px)` 起的是
            # **下限保证**作用（内容再窄也不会小于 1126）。两个机制指向同一个数，
            # 所以抽掉 margin 后宽度回到 1132 而不是 1126。
            was = {"canvas": [67, 67, 1132, 139], "ruler": [67, 67, 1132, 27],
                   "clipTrack": [67, 100, 1132, 84]}
            drift = {k: off[k] for k in was if off[k] != was[k]}
            check("无 ml-6 时三处精确回到 x=67 / 宽 1133（证明 ② 确由这 6px 推出）",
                  not drift, f'仍为 {drift or "（全部吻合）"}')
            check("恢复后 canvas 仍 x=73（临时改动没留下痕迹）",
                  back["canvas"][0] == 73, f'{back["canvas"]}')

            check("页面无运行时错误", not errs, str(errs[:2]))
        finally:
            b.close()

    print(f"\n{'PASS' if not failures else 'FAIL'} — {checks - len(failures)}/{checks}")
    for f in failures:
        print("  · " + f)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
