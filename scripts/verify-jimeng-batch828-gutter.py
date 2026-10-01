"""Jimeng clone batch 828-gutter verifier — 左槽回到源站的 66，并查穿一条站不住的「有意偏离」。

批 818 把时间线节点按源站重做，唯独左槽写了 `w-32`（128）而不是源站的 66。
台账 §27（批 813）给的理由是：

    「槽若只有 48/96 会被左侧连接手柄命中盒整个吞掉，Playwright 报
      handle intercepts pointer events，用户同样点不到」

本批把这条查穿了，**三处都不对**：

  1. **拦截者认错了。** 吃掉点击的不是 `jimeng-connect-*` 那枚加号钮，而是
     React Flow **自带的** 60×120 隐形热区（`JimengConnectHandles` 的 `HOT_ZONE`，
     inline `left:-30` / `width:60`）。槽宽 48 时 `elementFromPoint(钮心)` 返回的是
     `DIV.react-flow__handle react-flow__handle-left`。
  2. **单位错了。** 「44×88」是**渲染**尺寸 —— 该节点 zoom≈0.727，60×120 CSS px
     缩放而来。批 813 拿它当世界像素使。热区在 CSS 坐标下恒为 **-30..+30**，
     与 zoom 无关（「往里吞 30px」的结论碰巧对，单位错）。
  3. **两个余量数都错。** 钮 42 宽、槽内居中 ⇒ 钮心 = 槽宽/2，距热区右缘余量
     = 槽宽/2 − 30：

         48 → **−6**   挡死（实测命中 DIV.react-flow__handle）
         66 →   3     可点（实测 aria-pressed false→true）  ← 源站值
         96 →  18
         128 → 34

     原文的「128 时余量 ~14px」「96 时只剩 1px」都对不上。

源站 66 落在 3px 余量上，照样可点；源站静音钮钮心在节点坐标 34，距 806 取证的
热区右缘（30）也是 3px —— 这 3px 是**源站布局自带的**，不是复刻引入的。故回到 66。

⚠️ 「源站手柄热区 = 60 宽、−30 起」本批**拿到了源站实测值**，不再是推断：
壳的直接子元素里那枚 `react-flow__handle react-flow__handle-left …` 实测
`[-30, 44, 60, 120]`（相对节点左缘）。这**印证**批 806 凭类名/transform 做的
推断，OPEN_QUESTION 828-a 就此关闭。源站静音钮钮心在节点坐标 34 ⇒ 距热区
右缘（30）余量 4px；复刻因壳少 1px 内缩，钮心在 33 ⇒ 余量 3px（批 818 遗留的
1px 差，见台账 §40）。**结论：66 槽 + 3px 余量可点，128 的「有意偏离」撤销。**

本 verifier 的契约（最后一条是**反向自检**，用来证明契约不是空断言）：

  ① 槽宽 = 66                       源站 [1,67,66,139]
     且槽与轨道之间**没有**独立分隔元素 —— 源站轨道行的直接子元素只有槽与视口
     两个，槽底色与壳同色，本就没有可见分隔线。（批 829 订正：批 828 曾据台账
     自造了一枚 `timeline-node-track-divider` 并写成源站事实，已删。）
  ② 静音钮相对槽左缘 = [12,54,42,42] r6
     —— 54 这个 y 是源站**写死**的（包裹层类名 `absolute top-[54px]`），
     不是居中算出来的；复刻此前是 y=8，差 46px
  ③ 钮心必须落在**热区右缘之外**，且真点一次 aria-pressed 必须翻
     读行为（elementFromPoint）而不只读几何：几何对了但被盖住也算失败
  ④ 反向自检：临时把槽压到 48，钮心**必须**被热区吃掉；恢复后**必须**又能点。
     跑不到这两步说明 ③ 是空断言

⚠️ 期望值全部在 **100% 缩放** 下取（先按 Meta+1 归一）。热区走 inline style，
与 zoom 无关；槽/钮走 class 驱动的 CSS px，100% 下两者才在同一坐标系里。
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "research" / "jimeng-canvas-batch828-2026-10-04"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
VIEWPORT = {"width": 1512, "height": 950}

HYDRATED = """() => { const el = document.getElementById('__next')
  || document.body.firstElementChild || document.body;
  return Object.keys(el).some(k => k.startsWith('__reactFiber$')); }"""

# 一次读齐：几何（相对槽左缘 / 节点左缘）+ 热区 inline style + 钮心命中链
SNAP = r"""() => {
  const node = document.querySelector('[data-testid="timeline-node"]');
  const g = node && node.querySelector('[data-testid="timeline-track-gutter"]');
  const div = node && node.querySelector('[data-testid="timeline-node-track-divider"]');
  const m = node && node.querySelector('[data-testid="timeline-mute-button"]');
  if (!g || !m) return { err: 'no gutter/mute' };
  const gr = g.getBoundingClientRect(), mr = m.getBoundingClientRect();
  const nr = node.getBoundingClientRect();
  const dr = div ? div.getBoundingClientRect() : null;

  // 热区：left 侧那枚。走 inline style（left:-30 / width:60），
  // **不受节点 zoom 影响**，所以是 CSS 坐标下的真实范围。
  const hz = [...node.querySelectorAll('.react-flow__handle')]
      .map(e => ({ left: e.style.left, right: e.style.right, w: e.style.width }))
      .filter(h => h.left);   // 只取 left 侧那枚（右侧用 right 定位）

  const who = (x, y) => { const e = document.elementFromPoint(x, y); if (!e) return null;
    return { tag: e.tagName, cls: (typeof e.className === 'string' ? e.className : '').slice(0, 48),
             inMute: !!e.closest('[data-testid="timeline-mute-button"]'),
             inHandle: !!e.closest('.react-flow__handle') }; };
  const cx = mr.x + mr.width / 2, cy = mr.y + mr.height / 2;

  return {
    err: null,
    gutterW: Math.round(gr.width),
    gutterRelNode: [Math.round(gr.x - nr.x), Math.round(gr.y - nr.y),
                    Math.round(gr.width), Math.round(gr.height)],
    // 批 829：源站轨道行的直接子元素**只有**槽与视口两个，中间无 1px 元素
    divider: div ? { relX: Math.round(dr.x - gr.x - gr.width),
                     w: Math.round(dr.width), h: Math.round(dr.height),
                     bg: getComputedStyle(div).backgroundColor } : null,
    gutterNextIsScroll: g.nextElementSibling
      ? g.nextElementSibling.getAttribute('data-testid') : null,
    gutterRight: Math.round(gr.x + gr.width),
    muteRelGutter: [Math.round(mr.x - gr.x), Math.round(mr.y - gr.y),
                    Math.round(mr.width), Math.round(mr.height)],
    muteRelNode: Math.round(mr.x - nr.x),
    muteCenter: Math.round((mr.x - gr.x) + mr.width / 2),
    muteRadius: parseFloat(getComputedStyle(m).borderTopLeftRadius) || 0,
    hotZone: hz[0] || null,
    centerHit: who(cx, cy),
  };
}"""

# 临时改槽宽（仅内联样式，不碰 React 树），用完立刻恢复
SET_W = """(w) => { const g = document.querySelector(
  '[data-testid="timeline-track-gutter"]');
  if (w === null) g.style.width = ''; else g.style.width = w + 'px'; }"""


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
            check("已归 100% 缩放（热区与槽宽要在同一坐标系里比）", zt == "100%", f"zoom={zt!r}")
            if zt != "100%":
                print("\n  未归一成功，几何断言无意义 —— 直接中止")
                return 1

            # ⚠️ 顺序：先插入时间线节点，再等它的壳。壳在插入前**不存在**，
            #    先 wait_for_selector(shell) 会死等（我踩过）。
            pg.get_by_label("时间线", exact=True).first.click()
            pg.wait_for_selector('[data-testid="timeline-track-gutter"]', timeout=30000)
            pg.wait_for_timeout(1000)

            d = pg.evaluate(SNAP)
            if d.get("err"):
                print(f"\n  {d['err']}")
                return 1
            EVIDENCE.mkdir(parents=True, exist_ok=True)
            (EVIDENCE / "gutter-hit-snapshot.json").write_text(
                __import__("json").dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

            print("\n— ① 槽宽与相邻结构 —")
            check("左槽宽 = 66（源站 [1,67,66,139]；此前 w-32=128）", d["gutterW"] == 66,
                  f'gutterW={d["gutterW"]}')
            # 批 829 订正：源站轨道行**只有**槽与视口两个孩子，中间没有 1px 元素；
            # 槽底色与壳同色 ⇒ 那条线上本来就没有可见分隔线。本批已删掉复刻自造的那枚。
            check("槽与轨道之间**没有**独立分隔元素（源站轨道行只有槽 + 视口两个孩子）",
                  d["divider"] is None and d["gutterNextIsScroll"] == "timeline-track-scroll",
                  f'divider={d["divider"]} next={d["gutterNextIsScroll"]!r}')
            check("轨道紧贴槽右缘，无间隙（源站视口 x=67 = 槽 1+66）",
                  d["gutterNextIsScroll"] == "timeline-track-scroll",
                  f'槽右缘={d["gutterRight"]}')

            print("\n— ②③ 静音钮几何 + 行为（钮心必须躲开热区）—")
            # 源站实测（batch828 取证，source-gutter.json）：
            #   槽 [1,67,66,139]，槽内**只有**静音钮 [13,121,42,42] r6，
            #   包裹层类名 `inline-flex absolute top-[54px] inset-x-0 mx-auto`
            #   ⇒ 相对槽左缘 = [12, 54, 42, 42]（x 与 y 都是源站确证值）
            check("静音钮相对槽左缘 [12,54,42,42]（源站 13−1 / 121−67）",
                  d["muteRelGutter"] == [12, 54, 42, 42], str(d["muteRelGutter"]))
            check("静音钮圆角 r6", d["muteRadius"] == 6, str(d["muteRadius"]))
            # 源站手柄热区**首次实测**（batch828 取证，壳直接子元素）：
            #   [-30, 44, 60, 120] `react-flow__handle react-flow__handle-left …`
            # ⇒ 60 宽、自节点左缘 −30 起 ⇒ 覆盖 -30..+30。这**印证**批 806
            #    凭类名/transform 做的推断（台账 §40：828-a 就此关闭）。
            hz = d["hotZone"] or {}
            check("左侧热区 inline style = left:-30 / width:60（与源站实测 [-30,·,60,120] 同）",
                  hz.get("left") in ("-30px", "-30") and hz.get("w") in ("60px", "60"),
                  str(hz))
            # 槽 66 ⇒ 钮心 33；热区右缘 30 ⇒ 余量 3px。3 > 0 才算躲开。
            # （源站因壳有 1px 内缩，钮心在节点坐标 34 ⇒ 余量 4px，差 1px 属批 818 遗留。）
            margin = d["muteCenter"] - 30
            check("钮心在热区右缘之外（66 槽 ⇒ 余量 3px）", margin > 0,
                  f'钮心={d["muteCenter"]} 余量={margin}')
            check("钮心命中的是静音钮自身，不是热区",
                  bool(d["centerHit"]) and d["centerHit"]["inMute"]
                  and not d["centerHit"]["inHandle"],
                  str(d["centerHit"]))

            print("\n— ④ 真点一次 —")
            btn = pg.locator('[data-testid="timeline-mute-button"]').first
            before = btn.get_attribute("aria-pressed")
            bb = btn.bounding_box()
            try:
                pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
                perr = None
            except Exception as e:  # noqa: BLE001
                perr = str(e)[:160]
            pg.wait_for_timeout(400)
            after = btn.get_attribute("aria-pressed")
            check("钮心真点得中：aria-pressed 翻转", perr is None and after != before,
                  f'{before} → {after} err={perr}')
            check("翻转后无障碍名同步为「取消静音」",
                  btn.get_attribute("aria-label") == "取消静音",
                  repr(btn.get_attribute("aria-label")))

            print("\n— ⑤ 反向自检：把槽压到 48，钮心**必须**被热区吃掉 —")
            pg.evaluate(SET_W, 48)
            pg.wait_for_timeout(250)
            d48 = pg.evaluate(SNAP)
            pg.evaluate(SET_W, None)
            pg.wait_for_timeout(250)
            dback = pg.evaluate(SNAP)
            check("48 槽 ⇒ 钮心落进热区（余量 −6），命中 react-flow__handle",
                  bool(d48.get("centerHit")) and d48["centerHit"]["inHandle"]
                  and not d48["centerHit"]["inMute"],
                  f'余量={d48.get("muteCenter", 0) - 30} hit={str(d48.get("centerHit"))[:90]}')
            check("恢复后钮心又能点（证明 ④ 不是空断言）",
                  bool(dback.get("centerHit")) and dback["centerHit"]["inMute"]
                  and not dback["centerHit"]["inHandle"],
                  str(dback.get("centerHit"))[:90])
            check("恢复后槽宽回到 66（临时改宽没留下痕迹）", dback.get("gutterW") == 66,
                  f'gutterW={dback.get("gutterW")}')
            check("页面无运行时错误", not errs, str(errs[:2]))
        finally:
            b.close()

    print(f"\n{'PASS' if not failures else 'FAIL'} — {checks - len(failures)}/{checks}")
    for f in failures:
        print("  · " + f)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
