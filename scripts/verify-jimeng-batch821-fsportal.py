"""Jimeng clone batch 821-fsportal verifier — 全屏编辑器逃出节点，读数才是视口绝对值。

本批的起因是一条**被证伪的假设**。批 820/821 草稿里我写过：

    「全屏编辑器是 `fixed inset-0`，不受画布缩放影响 ⇒ 宽度是视口绝对值，
     可直接照搬源站」

821 实测把这句话打掉了。浮层当时挂在 `.timeline-node` 里，而 React Flow 给
每个节点加 `transform`；**任何带 transform 的祖先都会收编 `position: fixed`**
（fixed 的包含块变成那个 transform 元素），于是 `inset-0` 只铺满了**节点**：

    浮层 [156,372,1200,207]   ← 节点的盒子，不是 1512×950 视口
    资产栏 [156,428,360,24]   ← 被压成 24 高
    底栏 218 高溢出，盖住资产栏标签 → 批 813 的点击被 `timeline-fullscreen-toolbar` 拦掉

所以「照搬源站的视口绝对坐标」这条路此前**根本没成立**：复刻在 1200×207 的盒子里
摆 218 高的底栏，源站的每一条矩形都对不上，只能靠「看起来差不多」蒙混。

修法是 `createPortal(…, document.body)`（沿用 `JimengVideoPreview.tsx` 的既有写法）。
本 verifier 的第一条断言就是**这个前提本身**：`parentElement === BODY`。
只要有人把浮层挪回节点里，第 1 条立刻红 —— 后面所有矩形断言也就自动失去意义。

Contract (SOURCE_FACT 2026-10-04 登录态，1512×950 视口，**视口绝对坐标**)：

  浮层        [0,0,1512,950]  parentElement = BODY
  顶栏        导出 [1380,12,76,36]  关闭 [1464,12,36,36]
  资产栏      [12,60,360,652]
  预览壳      [380,60,1120,652]
  播放头读数  y=680（壳底 712 往上 32）
  底栏        section [12,720,1488,218] r12
    把手      [12,**704**,1488,24]   ← 骑在内容区与底栏之间那道 8px 缝上
    工具条    [12,720,1488,44]
      编辑工具 [20,728,208,28]      6 枚各 28×28，gap 8 ⇒ 168+40=208
      播放控件 [1304,728,188,28]    28+28+**92**+28 + 3×4 = 188 ⇒ span 宽 92
    轨道区    [12,756,1488,182]
      刻度     [64,764,1428,18]     9px，00:00…01:10（15 格 5s），21.4px/s
      视觉轨   [12,786,1488,56]
        静音   [20,800,28,28]
        投放区 [64,786,56,56]
      播放头   [64,764,1,174]       从刻度顶拉到区块底

⚠️ 把手 y=704 比底栏顶边 720 还高 16px：源站这枚是**跨缝**的，不是底栏第一行。
   复刻照此实现（section `pt-36` + 把手 `-top-4` + 工具条绝对定位），
   这样轨道区回到正常流正好落在 756 —— 不需要任何负 margin。

⚠️ 判据一律落在**运行时契约**上，不做源码字符串断言。缩放那一组断言的是
   「读数变了 **且** 刻度间距同步变」两个信号同时成立，而不是去 grep
   `FS_RULER_PX_PER_SEC * fsZoom` 在不在 —— 那种判据换个变量名就假失败。
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "research" / "jimeng-canvas-batch821-2026-10-04"
SRC = ROOT / "src" / "components" / "jimeng" / "nodes" / "JimengTimelineNode.tsx"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
VIEWPORT = {"width": 1512, "height": 950}
HYDRATED = """() => { const el = document.getElementById('__next')
  || document.body.firstElementChild || document.body;
  return Object.keys(el).some(k => k.startsWith('__reactFiber$')); }"""

PROBE = r"""() => {
  const o = document.querySelector('[data-testid="timeline-fullscreen"]');
  if (!o) return { err: 'no fullscreen overlay' };
  const box = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
    return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; };
  const by = (s) => o.querySelector(s);
  const byLabel = (lb) => o.querySelector('[aria-label="' + lb + '"]');
  const ruler = by('[data-testid="timeline-fullscreen-ruler"]');
  // 直接子元素才是刻度单元；不加 `> ` 会连每格里的线/字一起命中（n=45 而非 15）
  const ticks = [...ruler.querySelectorAll(':scope > span')];
  const assets = by('[data-testid="timeline-fs-assets"]');
  const scroll = by('[data-testid="timeline-fullscreen-track-scroll"]');
  const zoomSpan = by('[data-testid="timeline-fullscreen-zoom"]');
  const tab = o.querySelector('[data-testid="timeline-fs-source-画布资产"]');
  const tabHit = (() => { if (!tab) return null; const r = tab.getBoundingClientRect();
    const m = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
    return m ? m.tagName + '|' + (m.getAttribute('data-testid') || m.className.toString().slice(0, 40)) : null; })();
  const node = document.querySelector('[class*="rf__node-timeline"]');
  // 判据落在**机制**上，不落在 React Flow 的类名上 —— 那个类名带挂载时间戳
  // （`rf__node-timeline-1790848167914`），不是契约。真正的机制是：
  // 祖先链上只要有一个非 `none` 的 transform，`position: fixed` 就被收编。
  // 浮层在 body 下时这段循环一次都不跑（直接父级就是 body）。
  const tfAncestors = (() => { const out = []; let e = o.parentElement;
    while (e && e !== document.body) {
      const t = getComputedStyle(e).transform;
      if (t && t !== 'none') out.push(e.tagName + ':' + t.slice(0, 24));
      e = e.parentElement; }
    return out; })();
  return {
    err: null,
    parent: o.parentElement ? o.parentElement.tagName : null,
    overlay: box(o),
    tfAncestors: tfAncestors,
    insideNode: node ? node.contains(o) : null,
    export: box(by('[data-testid="timeline-fullscreen-export"]')),
    close: box(byLabel('Close timeline editor')),
    assets: box(assets),
    previewShell: (() => { const s = assets && assets.nextElementSibling;
      return s ? box(s) : null; })(),
    playheadTextY: (() => { const t = by('[data-testid="timeline-fs-playhead"]');
      return t ? box(t) : null; })(),
    workspace: box(by('[data-testid="timeline-fullscreen-workspace"]')),
    handle: box(by('[data-testid="timeline-fullscreen-workspace-resize-handle"]')),
    toolbar: box(by('[data-testid="timeline-fullscreen-toolbar"]')),
    editTools: box(by('[data-testid="timeline-fullscreen-editing-tools"]')),
    playback: box(by('[data-testid="timeline-fullscreen-playback-controls"]')),
    zoomSpanW: zoomSpan ? Math.round(zoomSpan.getBoundingClientRect().width) : null,
    zoomText: zoomSpan ? zoomSpan.textContent.trim() : null,
    zoomTag: zoomSpan ? zoomSpan.tagName : null,
    trackScroll: box(scroll),
    scrollW: scroll ? scroll.scrollWidth : null,
    clientW: scroll ? scroll.clientWidth : null,
    ruler: box(ruler),
    rulerLabels: ticks.map(t => t.textContent.trim().split('\n').pop().trim()),
    rulerGaps: ticks.slice(1).map((t, i) =>
      Math.round(t.getBoundingClientRect().x - ticks[i].getBoundingClientRect().x)),
    visualTrack: box(by('[data-testid="timeline-fullscreen-visual-track"]')),
    mute: box(by('[data-testid="timeline-fullscreen-mute-button"]')),
    drop: box(byLabel('添加素材到时间线')),
    playhead: box(by('[data-testid="timeline-fullscreen-playhead"]')),
    tabHit: tabHit,
    editToolNames: [...o.querySelectorAll('[aria-label]')]
      .map(e => e.getAttribute('aria-label'))
      .filter(l => ['撤销', '重做', '分割', '向左剪裁', '向右剪裁', '删除'].includes(l)),
    playCtlNames: ['关闭自动吸附', '缩小视图', '放大视图']
      .filter(l => !!byLabel(l)),
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

    # ---- 源码级：只查「浮层确实挂在 body 上」这一条会反复被踩的约定 ----
    # 其余全部走运行时断言（见文件头：判据不落在实现形状上）。
    src = SRC.read_text(encoding="utf-8")
    print("— 源码 —")
    check("createPortal 自 react-dom 引入",
          'import { createPortal } from "react-dom";' in src, "导入缺失")
    check("浮层挂载目标是 document.body",
          "document.body," in src and "createPortal(" in src, "未见 portal 挂载点")

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

            pg.get_by_label("时间线", exact=True).first.click()
            pg.wait_for_selector('[data-testid="timeline-fullscreen-trigger"]', timeout=30000)
            pg.wait_for_timeout(1200)
            pg.locator('[data-testid="timeline-fullscreen-trigger"]').first.click()
            pg.wait_for_selector('[data-testid="timeline-fullscreen-workspace"]', timeout=20000)
            pg.wait_for_timeout(1000)

            d = pg.evaluate(PROBE)
            if d.get("err"):
                check("全屏编辑器已打开", False, d["err"])
                return 1
            check("全屏编辑器已打开", True)

            print("\n— 前提：浮层真的是视口级的（本批的全部地基）—")
            check("浮层 parentElement 是 BODY（逃出了节点的 transform 祖先）",
                  d["parent"] == "BODY", f'parent={d["parent"]!r}')
            check("浮层祖先链上无任何 transform（否则 `fixed` 会被收编 —— "
                  "这正是本批那个 bug 的机制）",
                  d["tfAncestors"] == [], str(d["tfAncestors"]))
            check("浮层铺满视口 [0,0,1512,950]",
                  d["overlay"] == [0, 0, VIEWPORT["width"], VIEWPORT["height"]],
                  str(d["overlay"]))
            if d["parent"] != "BODY" or d["overlay"] != [0, 0, VIEWPORT["width"], VIEWPORT["height"]]:
                print("\n  视口级前提不成立 ⇒ 下面每条矩形都是节点内坐标，"
                      "与源站不可比 —— 直接中止（别让假失败淹没真问题）")
                return 1

            print("\n— 顶栏 —")
            check("导出钮 76×36 @[1380,12]", d["export"] == [1380, 12, 76, 36], str(d["export"]))
            check("关闭钮 36×36 @[1464,12]", d["close"] == [1464, 12, 36, 36], str(d["close"]))

            print("\n— 中部：资产栏 + 预览壳 —")
            check("资产栏 [12,60,360,652]", d["assets"] == [12, 60, 360, 652], str(d["assets"]))
            check("预览壳 [380,60,1120,652]",
                  d["previewShell"] == [380, 60, 1120, 652], str(d["previewShell"]))
            check("播放头读数落在 y=680（壳底 712 往上 32）",
                  bool(d["playheadTextY"]) and d["playheadTextY"][1] == 680,
                  str(d["playheadTextY"]))
            # 批 813 的点击曾被底栏工具条拦掉 —— 这条是那条回归的直接看门狗
            check("资产栏筛选标签可点（命中自身，不被工具条遮挡）",
                  (d["tabHit"] or "").endswith("timeline-fs-source-画布资产"), str(d["tabHit"]))

            print("\n— 底栏：section / 把手 / 工具条 —")
            check("底栏 section [12,720,1488,218]",
                  d["workspace"] == [12, 720, 1488, 218], str(d["workspace"]))
            check("把手 [12,**704**,1488,24]（跨在 8px 缝上，比底栏顶边高 16）",
                  d["handle"] == [12, 704, 1488, 24], str(d["handle"]))
            check("工具条 [12,720,1488,44]", d["toolbar"] == [12, 720, 1488, 44], str(d["toolbar"]))
            check("编辑工具 [20,728,208,28]", d["editTools"] == [20, 728, 208, 28], str(d["editTools"]))
            check("播放控件 [1304,728,188,28]",
                  d["playback"] == [1304, 728, 188, 28], str(d["playback"]))
            check("编辑工具六枚实名逐字对上",
                  d["editToolNames"] == ["撤销", "重做", "分割", "向左剪裁", "向右剪裁", "删除"],
                  str(d["editToolNames"]))
            check("播放控件四件中的三枚实名",
                  d["playCtlNames"] == ["关闭自动吸附", "缩小视图", "放大视图"],
                  str(d["playCtlNames"]))

            print("\n— 轨道区 —")
            check("轨道区 [12,756,1488,182]", d["trackScroll"] == [12, 756, 1488, 182],
                  str(d["trackScroll"]))
            check("刻度 [64,764,1428,18]", d["ruler"] == [64, 764, 1428, 18], str(d["ruler"]))
            check("视觉轨 [12,786,1488,56]", d["visualTrack"] == [12, 786, 1488, 56],
                  str(d["visualTrack"]))
            check("静音钮 [20,800,28,28]", d["mute"] == [20, 800, 28, 28], str(d["mute"]))
            check("投放区 [64,786,56,56]", d["drop"] == [64, 786, 56, 56], str(d["drop"]))
            check("播放头 [64,764,1,174]", d["playhead"] == [64, 764, 1, 174], str(d["playhead"]))
            check("刻度 00:00…01:10（15 格 5s）",
                  d["rulerLabels"][:1] == ["00:00"] and d["rulerLabels"][-1:] == ["01:10"]
                  and len(d["rulerLabels"]) == 15,
                  f'{d["rulerLabels"][:2]}…{d["rulerLabels"][-1:]} n={len(d["rulerLabels"])}')
            check("刻度 ≈21.4px/s（**≠** 内嵌表面的 32.1，两表面各自定值）",
                  bool(d["rulerGaps"]) and all(abs(g / 5 - 21.4) <= 1.6 for g in d["rulerGaps"]),
                  str(d["rulerGaps"][:4]))
            check("70s 窗口溢出 ⇒ 轨道区真的有横向滚动（刻度不产生内在宽度，"
                  "靠绝对定位的溢出撑开）",
                  bool(d["scrollW"]) and d["scrollW"] > d["clientW"],
                  f'scrollW={d["scrollW"]} clientW={d["clientW"]}')

            print("\n— 「Timeline zoom」是活的读数，不是空壳 —")
            # span 宽 92 是由总宽 188 倒推的（188 − 3×28 − 3×4 = 92），
            # 但源站那枚 span 的**文案没取到**。复刻按缩放读数实现（OPEN_QUESTION 821-a），
            # 判据是「读数变 且 刻度间距同步变」两个信号同时成立。
            check("zoom 是 span 而非按钮（源站如此）", d["zoomTag"] == "SPAN", str(d["zoomTag"]))
            check("zoom span 宽 92（188 总宽倒推）", d["zoomSpanW"] == 92, str(d["zoomSpanW"]))
            check("初始读数 100%", d["zoomText"] == "100%", str(d["zoomText"]))
            gap0 = d["rulerGaps"][0] if d["rulerGaps"] else 0
            pg.get_by_label("放大视图", exact=True).first.click()
            pg.wait_for_timeout(500)
            t1 = pg.locator('[data-testid="timeline-fullscreen-zoom"]').inner_text().strip()
            g1 = pg.evaluate("""() => { const t=[...document.querySelectorAll(
                '[data-testid="timeline-fullscreen-ruler"] > span')];
              return Math.round(t[1].getBoundingClientRect().x - t[0].getBoundingClientRect().x); }""")
            check("放大 → 读数 110%", t1 == "110%", f"got {t1!r}")
            check("放大 → 刻度间距同步 ×1.1（读数与几何不是两套各说各话）",
                  abs(g1 / gap0 - 1.1) < 0.04, f"gap {gap0}→{g1}")
            pg.get_by_label("缩小视图", exact=True).first.click()
            pg.wait_for_timeout(400)
            t2 = pg.locator('[data-testid="timeline-fullscreen-zoom"]').inner_text().strip()
            check("缩小 → 读数回到 100%", t2 == "100%", f"got {t2!r}")
            for _ in range(20):
                pg.get_by_label("放大视图", exact=True).first.click()
            pg.wait_for_timeout(600)
            t3 = pg.locator('[data-testid="timeline-fullscreen-zoom"]').inner_text().strip()
            check("放大封顶 200%（连点 20 次不越界）", t3 == "200%", f"got {t3!r}")
            for _ in range(30):
                pg.get_by_label("缩小视图", exact=True).first.click()
            pg.wait_for_timeout(600)
            t4 = pg.locator('[data-testid="timeline-fullscreen-zoom"]').inner_text().strip()
            check("缩小封底 50%（连点 30 次不越界）", t4 == "50%", f"got {t4!r}")
            pg.get_by_label("放大视图", exact=True).first.click()
            pg.wait_for_timeout(400)

            print("\n— 原有行为没被本批打断 —")
            mute = pg.locator('[data-testid="timeline-fullscreen-mute-button"]')
            m0 = mute.get_attribute("aria-label")
            mute.click()
            pg.wait_for_timeout(350)
            m1 = mute.get_attribute("aria-label")
            check("静音钮可切（aria-label 互翻）", m0 != m1 and m1 == "取消静音", f"{m0!r}→{m1!r}")
            mute.click()
            pg.wait_for_timeout(300)
            add = pg.get_by_label("添加素材到时间线", exact=True).first
            add.click()
            pg.wait_for_timeout(400)
            check("投放区仍能加片段（不是死按钮）",
                  "添加" not in pg.locator('[data-testid="timeline-fs-asset-empty"]').inner_text(),
                  pg.locator('[data-testid="timeline-fs-asset-empty"]').inner_text()[:40])
            pg.screenshot(path=str(EVIDENCE / "clone-fullscreen-821.png"))
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(800)
            check("Escape 关闭全屏编辑器",
                  pg.locator('[data-testid="timeline-fullscreen"]').count() == 0, "浮层仍在")
            check("浮层关闭后不在 body 上留残根",
                  pg.evaluate("() => !document.querySelector('body > [data-testid=\"timeline-fullscreen\"]')"),
                  "body 下仍有浮层")
            check("无未捕获页面错误", not errs, "; ".join(errs[:3]))
        finally:
            b.close()

    print()
    if failures:
        print(f"FAIL batch821-fsportal — {checks} 项中 {len(failures)} 项失败")
        for f in failures:
            print("  -", f)
        return 1
    print(f"PASS batch821-fsportal — {checks} 项断言全通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
