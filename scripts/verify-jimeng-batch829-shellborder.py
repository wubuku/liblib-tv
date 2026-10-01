"""Jimeng clone batch 829-shellborder verifier — 壳那 1px 边框，一个根因对齐五处。

批 828 把左槽改回源站的 66 之后，源站/复刻逐项对表暴露出一个**系统性的 1px 偏移**：

    元素        源站                 复刻(改之前)
    工具条      [1, 1,1198, 66]      [0, 0,1200, 66]
    轨道行      [1,67,1198,139]      [0,66,1200,141]
    左槽        [1,67,  66,139]      [0,66,  66,141]
    静音钮      [13,121, 42, 42]     [12,120, 42, 42]
    滚动容器    [67,67,1132,139]     [67,66,1133,141]

八处差全部落在 ±1 / ±2，看起来像八个独立的小错。**其实只有一个根因**：源站壳
带一圈 `1px solid rgba(255,255,255,0.04)` 的边框，于是内容整体内缩 1px。
补上边框，上面五处一次全中（宽 1200→1198 是左右各让 1；行高 141→139 是上下各让 1）。

取证过程值得记一笔：**这个 1px 不在任何子元素上**。逐个查过去，槽、轨道行、
视口、canvas 的 `border` 与 `padding` **全是 0**，只有壳这一层是 1px —— 所以它是
壳自己的边框，不是「谁的内边距」。颜色也是实测的 `rgba(255,255,255,0.04)`，
不是猜的。

### 顺带订正批 828 的一条假 SOURCE_FACT

批 828 据台账 §27.5 写了「源站槽与轨道之间有一枚**独立**的 1px 分隔元素
`timeline-node-track-divider [66,67,1,139]`」并照着做进了复刻。**源站没有它**：

- 源站轨道行的**直接子元素只有两个** —— 左槽 `[1,67,66,139]` 与视口
  `[67,67,1132,139]`，中间没有任何 1px 元素（槽内也没有）；
- 槽的底色 `color(srgb 0.12549 ×3)` = rgb(32,32,32)，**与壳同色** ⇒ 那条线上
  根本没有可见分隔线。

所以 `[66,67,1,139]` 是**我们**给「槽与轨道的边界」起的名字，不是源站的 testid
（源站全站用类名，无一个 testid）。本批已把那枚自造元素删掉。

### 本 verifier 的契约

  ① 壳：1px 边框 + 颜色 rgba(255,255,255,0.04) + r8 + 底色 rgb(32,32,32)
  ② 由这 1px 派生出来的五处逐项对上源站绝对矩形
  ③ **不再有**自造的分隔元素（828 的假事实订正）
  ④ 反向自检：把壳的边框临时去掉，五处必须**同时**偏移回 0/1200/1200/141 ——
     证明这五条真的是由边框推出来的，不是碰巧对上

⚠️ **故意不对齐、只记录**的两项（源站自身数据不自洽，本批不猜）：
源站刻度/投放区比这五条再往右 6px（canvas `margin-left: 6px`，实测），
而源站 canvas 实测宽 1126、其容器 1132 —— `min-w-full` 本该让 canvas ≥1132。
两个数自相矛盾，说明源站那里还有一层没量到。复刻当前是 0px 内缩，
差 6~7px，列入 OPEN_QUESTION 829-a，留给专门一批。
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "research" / "jimeng-canvas-batch829-2026-10-04"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
VIEWPORT = {"width": 1512, "height": 950}

HYDRATED = """() => { const el = document.getElementById('__next')
  || document.body.firstElementChild || document.body;
  return Object.keys(el).some(k => k.startsWith('__reactFiber$')); }"""

# 源站实测（batch 829 取证，源站与复刻均在 100% 缩放下，相对节点左缘）
SOURCE = {
    "shell":   [0, 0, 1200, 207],
    "toolbar": [1, 1, 1198, 66],
    "row":     [1, 67, 1198, 139],
    "gutter":  [1, 67, 66, 139],
    "scroll":  [67, 67, 1132, 139],
    "mute":    [13, 121, 42, 42],
    # 故意不对齐的两项，只记录
    "ruler":    [73, 67, 1126, 27],
    "clipTrack": [73, 100, 1126, 84],
}

SNAP = r"""() => {
  const node = document.querySelector('[data-testid="timeline-node"]');
  if (!node) return { err: 'no timeline node' };
  const q = (t) => node.querySelector('[data-testid="' + t + '"]');
  const shell = q('timeline-shell');
  const gutter = q('timeline-track-gutter');
  if (!shell || !gutter) return { err: 'no shell/gutter' };
  const nr = node.getBoundingClientRect();
  const rd = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
    return [Math.round(r.x - nr.x), Math.round(r.y - nr.y),
            Math.round(r.width), Math.round(r.height)]; };
  const cs = getComputedStyle(shell);
  const row = gutter.parentElement;
  // 颜色**在页内归一化**再交给 Python 比数字，不做字符串相等。
  // 本仓老坑（批 810-dock 文件头）：同一个白色，Tailwind 记成
  // `oklab(0.999994 0.0000455678 0.0000200868 / 0.04)`，源站记成
  // `rgba(255,255,255,0.04)`，直接字符串比必假失败。
  const norm = (c) => {
    const m = /oklab\(\s*([\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*(?:\/\s*([\d.]+))?\s*\)/.exec(c);
    if (m) return { form: 'oklab', L: +m[1], a: +m[2], b: +m[3], alpha: m[4] === undefined ? 1 : +m[4] };
    const r2 = /rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:[,\/]\s*([\d.]+))?\s*\)/.exec(c);
    if (r2) return { form: 'rgb', L: +r2[1], a: +r2[2], b: +r2[3],
                     alpha: r2[4] === undefined ? 1 : +r2[4] };
    return { form: 'unknown', raw: c };
  };
  return {
    err: null,
    shell: rd(shell),
    shellBorder: [cs.borderTopWidth, cs.borderRightWidth,
                  cs.borderBottomWidth, cs.borderLeftWidth],
    shellBorderColor: norm(cs.borderTopColor),
    shellBorderColorRaw: cs.borderTopColor,
    shellRadius: parseFloat(cs.borderTopLeftRadius) || 0,
    shellBg: cs.backgroundColor,
    toolbar: rd(q('timeline-toolbar')),
    row: rd(row),
    gutter: rd(gutter),
    scroll: rd(q('timeline-track-scroll')),
    mute: rd(q('timeline-mute-button')),
    ruler: rd(q('timeline-ruler')),
    clipTrack: rd(q('timeline-clip-track')),
    dividerExists: !!q('timeline-node-track-divider'),
  };
}"""

# 临时去掉壳边框（只动内联样式，用完恢复）
TOGGLE_BORDER = """(on) => { const s = document.querySelector(
  '[data-testid="timeline-shell"]');
  s.style.borderWidth = on ? '0px' : ''; }"""


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
            check("已归 100% 缩放（绝对矩形要在同一坐标系里比）", zt == "100%", f"zoom={zt!r}")
            if zt != "100%":
                print("\n  未归一成功，几何断言无意义 —— 直接中止")
                return 1

            # ⚠️ 顺序：先插入时间线节点，再等它的壳（壳在插入前不存在）。
            pg.get_by_label("时间线", exact=True).first.click()
            pg.wait_for_selector('[data-testid="timeline-track-gutter"]', timeout=30000)
            pg.wait_for_timeout(1000)

            d = pg.evaluate(SNAP)
            if d.get("err"):
                print(f"\n  {d['err']}")
                return 1
            EVIDENCE.mkdir(parents=True, exist_ok=True)
            (EVIDENCE / "clone-shell-after.json").write_text(
                __import__("json").dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

            print("\n— ① 壳自身 —")
            check("壳 1200×207 r8 底色 rgb(32,32,32)", d["shell"] == SOURCE["shell"]
                  and d["shellRadius"] == 8 and d["shellBg"] == "rgb(32, 32, 32)",
                  f'{d["shell"]} r={d["shellRadius"]} bg={d["shellBg"]}')
            check("壳四边都是 1px 边框", all(b == "1px" for b in d["shellBorder"]),
                  str(d["shellBorder"]))
            # 颜色在页内已归一化（rgba 与 oklab 两条路都折成 L/a/b/alpha），
            # 这里只比数字：必须是白色、alpha 恰为 0.04。
            bc = d["shellBorderColor"]
            is_white = (bc.get("form") == "oklab" and abs(bc.get("L", 0) - 1) <= 0.01
                        and abs(bc.get("a", 9)) <= 0.01 and abs(bc.get("b", 9)) <= 0.01) or (
                       bc.get("form") == "rgb" and bc.get("L") == 255
                        and bc.get("a") == 255 and bc.get("b") == 255)
            check("边框色 = 白 @ alpha 0.04（实测源站值 rgba(255,255,255,0.04)，非推断）",
                  is_white and abs(bc.get("alpha", -1) - 0.04) <= 0.001,
                  f'{d["shellBorderColorRaw"]!r} → {bc}')

            print("\n— ② 由这 1px 派生出来的五处，逐项对源站绝对矩形 —")
            for key, label in (("toolbar", "工具条"), ("row", "轨道行"),
                               ("gutter", "左槽"), ("scroll", "滚动容器"),
                               ("mute", "静音钮")):
                want = SOURCE[key]
                got = d[key]
                check(f"{label} {want}", got == want, f'实得 {got}')

            print("\n— ③ 订正 828 的假 SOURCE_FACT —")
            check("自造的 timeline-node-track-divider 已删除（源站本就没有）",
                  d["dividerExists"] is False, f'仍存在={d["dividerExists"]}')

            print("\n— ④ 反向自检：抽掉边框，五处必须**同时**偏移回改前的样子 —")
            pg.evaluate(TOGGLE_BORDER, True)
            pg.wait_for_timeout(300)
            off = pg.evaluate(SNAP)
            pg.evaluate(TOGGLE_BORDER, False)
            pg.wait_for_timeout(300)
            back = pg.evaluate(SNAP)
            was = {"toolbar": [0, 0, 1200, 66], "row": [0, 66, 1200, 141],
                   "gutter": [0, 66, 66, 141], "mute": [12, 120, 42, 42]}
            drift = {k: off[k] for k in was if off[k] != was[k]}
            check("无边框时四处精确回到改前值（证明 ② 确由边框推出）", not drift,
                  f'仍为 {drift or "（全部吻合）"}')
            check("恢复边框后壳仍是 1px（临时改动没留下痕迹）",
                  all(x == "1px" for x in back["shellBorder"]), str(back["shellBorder"]))

            print("\n— 记录项：故意不对齐的两项（OPEN_QUESTION 829-a）—")
            for key, label in (("ruler", "刻度尺"), ("clipTrack", "投放区所在行")):
                want, got = SOURCE[key], d[key]
                print(f"  [跳过] {label} 源站 {want} / 复刻 {got} —— 差 "
                      f"{[g - w for g, w in zip(got, want)]}")

            check("页面无运行时错误", not errs, str(errs[:2]))
        finally:
            b.close()

    print(f"\n{'PASS' if not failures else 'FAIL'} — {checks - len(failures)}/{checks}")
    for f in failures:
        print("  · " + f)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
