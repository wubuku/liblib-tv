"""Jimeng clone batch 818-timelinestem verifier — 时间线节点骨架按源站重做。

Contract (SOURCE_FACT 2026-10-04 登录态，**100% 缩放**，坐标相对壳左上角)：

  壳            1200×207  r8  bg rgb(32,32,32)
  工具条        [1,1,1198,66]
    时钟        [566,22,123,24]  fs **18**  「00:00」/「/」/「00:00」三段
    导出时间线  [1013,13,42,42]  r8
    全屏编辑    [1061,13,126,42] r8  标签纯白
  左槽          [1,67,66,139]  静音 [13,121,42,42] r6
  刻度尺        [73,67,1126,27]  00:00…00:30 step 5s  fs **13.5**
  片段轨道      [73,100,1126,84]
    投放区      [73,100,1113,84] r6 **实底 rgba(255,255,255,0.04)**
                空态标签 19.5px

⚠️ 本 verifier 的几何断言全部是**相对锚点**（相对壳左上角 / 相邻控件右缘），
不是绝对坐标 —— 节点在画布上的落点由插入位置决定。批 807-topleft §17.4 记过
「控件矩形 ≠ 容器矩形」的坑，这里同理：右簇三枚的 x 会随左簇宽度浮动。

⚠️ **不**断言的项，以及原因（每条都是"未实测/有意偏离"，不是漏写）：

  1. 刻度**时间窗口**：源站 00:00→00:30 跨 963px = 32.1px/s，铺在 1126px 轨道上
     只占 85.5% ⇒ 源站可见窗口 ≈35.1s。复刻把 30s 拉满全宽（百分比模型）。
     源站的 px/s 是否随缩放/时长变化**未取证**，本批不猜，列 OPEN_QUESTION 818-a。
  2. 左槽宽度 128 vs 源站 66：**有意偏离**。batch 813 记录过槽若只有 48/96
     会被左侧连接手柄命中盒整个吞掉（Playwright 报 handle intercepts pointer
     events，用户同样点不到）。保持 128。
  3. 「导入」「删除时间线」两枚：**有意保留**。源站工具条没有它们（源站左端
     那两枚是无 role/无 aria/无 tabindex 的裸 div，见台账 §27.5），但复刻的
     「删除」是批 805 建立的真功能，删掉等于主动删功能。
  4. 时钟**宽度**：源站 123 vs 复刻按字体度量约 116。差的是字体不是布局
     （batch 798 分享按钮同款），只断言字号不断言宽度。

颜色断言经 canvas 像素归一（`oklab()` vs `rgba()` 记法不同，直接字符串比必假
失败——本项目老坑，见批 810-dock 文件头）。
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "research" / "jimeng-canvas-batch818-2026-10-03"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
VIEWPORT = {"width": 1512, "height": 950}
HYDRATED = """() => { const el = document.getElementById('__next')
  || document.body.firstElementChild || document.body;
  return Object.keys(el).some(k => k.startsWith('__reactFiber$')); }"""

PROBE = r"""() => {
  const cv = document.createElement('canvas'); cv.width = cv.height = 1;
  const ctx = cv.getContext('2d', { willReadFrequently: true });
  const toRGB = (css) => { ctx.clearRect(0,0,1,1); ctx.fillStyle = '#000';
    ctx.fillStyle = css; ctx.fillRect(0,0,1,1);
    const d = ctx.getImageData(0,0,1,1).data; return [d[0],d[1],d[2]]; };
  const toA = (css) => { ctx.clearRect(0,0,1,1); ctx.fillStyle = '#000';
    ctx.fillStyle = css; ctx.fillRect(0,0,1,1);
    return ctx.getImageData(0,0,1,1).data[3] / 255; };
  const node = document.querySelector('[data-testid="timeline-node"]');
  if (!node) return { err: 'no timeline node' };
  const shell = node.querySelector('[data-testid="timeline-shell"]');
  const sr = shell.getBoundingClientRect();
  const rel = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
    return [Math.round(r.x - sr.x), Math.round(r.y - sr.y),
            Math.round(r.width), Math.round(r.height)]; };
  const q = (t) => node.querySelector(`[data-testid="${t}"]`);
  const rd = (e) => { if (!e) return null; const cs = getComputedStyle(e);
    return { rel: rel(e), radius: parseFloat(cs.borderTopLeftRadius) || 0,
             bgAlpha: toA(cs.backgroundColor), fs: parseFloat(cs.fontSize) || 0 }; };
  const clock = q('timeline-time');
  return {
    shell: { size: [Math.round(sr.width), Math.round(sr.height)],
             radius: parseFloat(getComputedStyle(shell).borderTopLeftRadius) || 0,
             rgb: toRGB(getComputedStyle(shell).backgroundColor) },
    toolbar: rd(q('timeline-toolbar')),
    gutter: rd(q('timeline-track-gutter')),
    exportBtn: rd(q('timeline-export-trigger')),
    fullscreen: rd(q('timeline-fullscreen-trigger')),
    mute: rd(q('timeline-mute-button')),
    ruler: rd(q('timeline-ruler')),
    clipTrack: rd(q('timeline-clip-track')),
    addClip: rd(q('timeline-add-clip')),
    clock: clock ? { rel: rel(clock), fs: parseFloat(getComputedStyle(clock).fontSize) || 0 } : null,
    desc: (() => { const s = [...node.querySelectorAll('span')]
        .find(x => x.children.length === 0 && /visual track/.test(x.textContent || ''));
      return s ? (s.textContent || '').trim() : null; })(),
    // 空态投放区里不得再有虚线框（源站是实底）
    addClipBorderStyle: (() => { const b = q('timeline-add-clip');
      if (!b) return null; const cs = getComputedStyle(b);
      return { style: cs.borderTopStyle,
               width: parseFloat(cs.borderTopWidth) || 0 }; })(),
    addClipText: (() => { const b = q('timeline-add-clip');
      return b ? (b.innerText || '').replace(/\s+/g, ' ').trim() : null; })(),
    addClipLabelFs: (() => { const b = q('timeline-add-clip');
      if (!b) return null;
      const s = [...b.querySelectorAll('span')].find(x => /添加素材/.test(x.textContent || ''))
            || [...b.childNodes].find(n => n.nodeType === 3);
      return s ? parseFloat(getComputedStyle(s.nodeType === 3 ? b : s).fontSize) : null; })(),
  };
}"""

# 源站（rel 壳左上角, 100% 缩放）
TICK_STEP = 5

WANT = {
    "exportBtn":   (42, 42, 8),
    "fullscreen":  (42, 126, 8),     # (高, 宽, 圆角) —— 别把宽高写反
    "mute":        (42, 42, 6),
    "addClip":     (84, None, 6),      # 宽度随槽宽浮动，只断言高与圆角
    "ruler":       (27, None, None),
    "clipTrack":   (84, None, None),
    "toolbar":     (66, None, None),
}


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
            # batch 817 的 hydrate 闸门：不读到降级页
            for _ in range(12):
                if pg.evaluate(HYDRATED):
                    break
                pg.wait_for_timeout(1000)
            else:
                check("复刻已 hydrate", False, "读到 SSR 骨架，其余断言全部无意义")
                return 1
            check("复刻已 hydrate", True)
            # 几何断言必须在 100% 缩放下做（批 812 §22.1 教训）。
            # ⚠️ **不要只按一次 ⌘1 就往下走** —— 实测它有时不生效（快捷键监听
            # 尚未挂上），读数会整批乘 0.73，产出一堆**假失败**（876×151、
            # 42→31、27→20…）。压到真实信号上：重试直到 zoom 标签读 100%。
            zt = ""
            for _ in range(8):
                pg.keyboard.press("Meta+1")
                pg.wait_for_timeout(500)
                zt = pg.locator('[data-testid="canvas-zoom-percent"]').first.inner_text().strip()
                if zt == "100%":
                    break
            check("已归 100% 缩放（重试至信号成立）", zt == "100%", f"zoom={zt!r}")
            if zt != "100%":
                print("\n  未归一成功，后续几何断言无意义 —— 直接中止（别让假失败淹没真问题）")
                return 1

            pg.get_by_label("时间线", exact=True).first.click()
            pg.wait_for_selector('[data-testid="timeline-shell"]', timeout=30000)
            pg.wait_for_timeout(1200)
            d = pg.evaluate(PROBE)
            if d.get("err"):
                check("时间线节点存在", False, d["err"])
                return 1

            print("\n— 壳 —")
            check("壳 1200×207", d["shell"]["size"] == [1200, 207], str(d["shell"]["size"]))
            check("壳 r8", d["shell"]["radius"] == 8, f'{d["shell"]["radius"]}px')
            check("壳底色 rgb(32,32,32)", d["shell"]["rgb"] == [32, 32, 32], str(d["shell"]["rgb"]))

            print("\n— 控件尺寸与圆角（相对锚点）—")
            for key, (h, w, r) in WANT.items():
                got = d.get(key)
                if not got:
                    check(f"{key} 存在", False, "未找到")
                    continue
                gw, gh, gr = got["rel"][2], got["rel"][3], got["radius"]
                check(f"{key} 高 {h}", gh == h, f"{gh}")
                if w is not None:
                    check(f"{key} 宽 {w}", gw == w, f"{gw}")
                if r is not None:
                    check(f"{key} r{r}", gr == r, f"{gr}px")

            print("\n— 右簇三枚的相对排布 —")
            # 全屏编辑右缘与壳右缘的间距（源站：1200 - (1061+126) = 13）
            fs_rel = d["fullscreen"]["rel"]
            check("全屏编辑距壳右缘 13px", 1200 - (fs_rel[0] + fs_rel[2]) == 13,
                  f'{1200 - (fs_rel[0] + fs_rel[2])}px')
            # 导出 与 全屏编辑 之间 6px（源站 1061-1013-42 = 6）
            ex_rel = d["exportBtn"]["rel"]
            check("导出与全屏编辑间距 6px",
                  fs_rel[0] - (ex_rel[0] + ex_rel[2]) == 6,
                  f'{fs_rel[0] - (ex_rel[0] + ex_rel[2])}px')

            print("\n— 时钟 —")
            check("时钟 18px", d["clock"] and d["clock"]["fs"] == 18,
                  str(d["clock"] and d["clock"]["fs"]))
            check("时钟行高 24", d["clock"] and d["clock"]["rel"][3] == 24,
                  str(d["clock"] and d["clock"]["rel"][3]))

            print("\n— 刻度 —")
            ruler = d["ruler"]
            check("刻度尺 27 高", ruler["rel"][3] == 27, f'{ruler["rel"][3]}')
            ticks = pg.evaluate("""() => {
              const r = document.querySelector('[data-testid="timeline-ruler"]');
              return [...r.children].map(c => {
                const s = [...c.querySelectorAll('span')].find(x => /\\d/.test(x.textContent||''));
                return { txt: (s?.textContent||'').trim(),
                         fs: s ? parseFloat(getComputedStyle(s).fontSize) : 0,
                         x: s ? Math.round(s.getBoundingClientRect().x) : 0 };
              });
            }""")
            labels = [t["txt"] for t in ticks]
            check("刻度 00:00…00:30 step 5s",
                  labels == ["00:00", "00:05", "00:10", "00:15", "00:20", "00:25", "00:30"],
                  str(labels))
            check("刻度字号 13.5px", all(t["fs"] == 13.5 for t in ticks),
                  str(sorted({t["fs"] for t in ticks})))
            # 判据落在「相邻刻度的像素间距」上 —— 那是契约；不要断言绝对 x，
            # 它随左侧槽宽浮动（复刻槽 128 vs 源站 66，§28.4 有意偏离）。
            # 同理"右侧留白"必须用**同坐标系**：ticks 的 x 是屏幕绝对坐标，
            # ruler_rel[2] 是相对壳的宽度，直接相减是拿苹果减橘子（我犯过）。
            ruler_rel = d["ruler"]["rel"]
            gaps = [round(ticks[i + 1]["x"] - ticks[i]["x"]) for i in range(len(ticks) - 1)]
            pps = [g / TICK_STEP for g in gaps]
            check("刻度步长 ≈32.1px/s（5s 间隔约 160px）",
                  all(abs(p - 32.1) <= 1.2 for p in pps), f"每档 {pps}")
            span = ticks[-1]["x"] - ticks[0]["x"]          # 00:00 → 00:30 的跨度
            check("刻度不铺满轨道（右侧留白 ≈ 窗口 - 30s）",
                  ruler_rel[2] - span > 20,
                  f"轨道宽 {ruler_rel[2]} − 跨度 {span} = 留白 {ruler_rel[2] - span}px")

            print("\n— 空态投放区 —")
            check("投放区文案", d["addClipText"] == "添加素材到时间线", repr(d["addClipText"]))
            check("投放区**实底**（非虚线框）",
                  d["addClipBorderStyle"] and d["addClipBorderStyle"]["width"] == 0,
                  f'border={d["addClipBorderStyle"]}')
            check("投放区底色 white/4", abs(d["addClip"]["bgAlpha"] - 0.04) < 0.006,
                  f'alpha={d["addClip"]["bgAlpha"]:.3f}')
            check("投放区标签 19.5px", d["addClipLabelFs"] == 19.5, str(d["addClipLabelFs"]))

            print("\n— 节点无障碍名 —")
            check("节点描述 span 存在", d["desc"] is not None)
            # 尾句随选中态变（插入后即选中），只断言**稳定前缀**，
            # 尾句另用行为断言：取消选中后应翻成 "Not selected."
            prefix = "时间线: 1 visual track, 0 audio tracks, 0 clips."
            check("描述含 1 visual track / 0 audio tracks / 0 clips",
                  bool(d["desc"]) and d["desc"].startswith(prefix), repr(d["desc"]))
            check("尾句是合法形式之一",
                  bool(d["desc"]) and d["desc"].endswith((" Not selected.", " Selected.")),
                  repr(d["desc"]))
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(700)
            d2 = pg.evaluate(PROBE)
            check("取消选中后尾句翻成 Not selected.",
                  d2["desc"] == f"{prefix} Not selected.", repr(d2["desc"]))

            print("\n— 回归 —")
            check("无 pageerror", not errs, "; ".join(errs[:2]))
            pg.screenshot(path=str(EVIDENCE / "clone-timeline-818.png"))
        finally:
            b.close()

    print()
    if failures:
        print(f"FAIL batch818-timelinestem — {checks} 项中 {len(failures)} 项失败")
        for f in failures:
            print("  -", f)
        return 1
    print(f"PASS batch818-timelinestem — {checks} 项断言全通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
