"""Jimeng clone batch 825-fsedits verifier — 全屏编辑器的六枚工具从桩变成真动作。

批 821 把全屏编辑器修成了真正的视口级浮层，批 823/824 又给它补了锚点。
到 825 才看清它**功能上**是空的：底栏那六枚编辑工具

    撤销 / 重做 / 分割 / 向左剪裁 / 向右剪裁 / 删除

每枚的 onClick 都是 `pushToast(mockMsg(\`${t.label}（时间线编辑工具）\`))` ——
一个纯桩。更根本的是，**轨道上一个片段都没渲染**，所以就算接上动作，
用户也不知道自己在动什么。本批把三件事做成一套：

  ① 轨道按**同一套世界坐标映射**渲染片段（`52 + t × 21.4 × zoom`）
  ② 播放头可定位（点轨道 / 点刻度尺），读数随之变化
  ③ 六枚工具作用于**播放头所在的那一片段**

⚠️ 本 verifier 断言的**行为**全部可在运行时观察到，不去 grep 源码变量名。
   片段在全屏轨道里的**尺寸不是源站实测值** —— 源站那个 fixture 的媒体全没
   加载，轨道上根本没有片段可量（台账 §31）。所以几何只断言两件事：
   - 空轨时投放区落在源站实测的 x=64（821 的读数，回归不破）
   - 片段/播放头/刻度三者的横坐标由**同一个式子**算出（用缩放联动验证：
     放大 10% → 片段宽度与刻度间距**同时** ×1.1）

🔴 本批抓到的**真缺陷**（不是判据错）：store 的 `updateNodeData` 根本不往
撤销栈里记快照（对比 `renameNode` 会 `past.push`）。于是按了「撤销」撤掉的是
很久之前的别的动作 —— 实测在时间线节点上点一下「撤销」，**把节点本身的创建
撤掉了**，浮层随之消失（探针表现为「重做按钮定位不到」）。
修法不是让 `updateNodeData` 记历史（它被文本节点**逐字输入**调用，那样按一次
撤销只能退一个字），而是新增 `updateNodeDataUndoable` 专供低频语义动作。
本 verifier 的「撤销不伤节点」一条就是这道疤的看门狗。
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "research" / "jimeng-canvas-batch825-2026-10-04"
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
  const clips = [...o.querySelectorAll('[data-testid="timeline-fullscreen-clip"]')].map((e) => {
    const r = e.getBoundingClientRect();
    return { x: Math.round(r.x), w: Math.round(r.width), label: e.textContent.trim(),
             inlineW: e.style.width, inlineL: e.style.left }; });
  const ruler = o.querySelector('[data-testid="timeline-fullscreen-ruler"]');
  const ticks = [...ruler.querySelectorAll(':scope > span')];
  const tool = (lb) => o.querySelector('[data-testid="timeline-fullscreen-tool-' + lb + '"]');
  return {
    err: null,
    playhead: box(o.querySelector('[data-testid="timeline-fullscreen-playhead"]')),
    drop: box(o.querySelector('[data-testid="timeline-fullscreen-drop"]')),
    time: (o.querySelector('[data-testid="timeline-fs-playhead-time"]') || {}).textContent || '',
    clips: clips,
    rulerGap: ticks.length > 1
      ? Math.round(ticks[1].getBoundingClientRect().x - ticks[0].getBoundingClientRect().x) : null,
    undoDisabled: tool('撤销') ? tool('撤销').disabled : null,
    redoDisabled: tool('重做') ? tool('重做').disabled : null,
    muteLabel: (o.querySelector('[data-testid="timeline-fullscreen-mute-button"]') || {})
      .getAttribute('aria-label'),
    nodeAlive: !!document.querySelector('[data-testid="timeline-shell"]'),
    toast: [...document.querySelectorAll('[data-testid*="toast"], [role="status"]')]
      .map((e) => e.textContent.trim()).join(' | '),
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

            pg.get_by_label("时间线", exact=True).first.click()
            pg.wait_for_selector('[data-testid="timeline-fullscreen-trigger"]', timeout=30000)
            pg.wait_for_timeout(1000)
            pg.locator('[data-testid="timeline-fullscreen-trigger"]').first.click()
            pg.wait_for_selector('[data-testid="timeline-fullscreen-workspace"]', timeout=20000)
            pg.wait_for_timeout(900)

            def snap() -> dict:
                d = pg.evaluate(SNAP)
                if d.get("err"):
                    print(f"\n  浮层消失：{d['err']}（这正是 825 修的那个真缺陷的表现）")
                return d

            def tool(label: str) -> str:
                loc = pg.locator(f'[data-testid="timeline-fullscreen-tool-{label}"]')
                if loc.is_disabled():
                    return "disabled"
                loc.click()
                pg.wait_for_timeout(650)
                return "clicked"

            print("\n— 空轨：几何与初始态 —")
            d0 = snap()
            check("播放头仍在源站读数 [64,764,1,174]",
                  d0["playhead"] == [64, 764, 1, 174], str(d0["playhead"]))
            check("空轨投放区落在源站实测的 x=64、56×56",
                  d0["drop"] and d0["drop"][0] == 64 and d0["drop"][2:] == [56, 56], str(d0["drop"]))
            check("轨道初始无片段", d0["clips"] == [], str(d0["clips"]))
            check("播放头读数初始 00:00:00", d0["time"] == "00:00:00", repr(d0["time"]))
            check("重做初始禁用（还没有可重做的东西）", d0["redoDisabled"] is True, str(d0["redoDisabled"]))
            check("撤销初始可用（建节点入过栈）", d0["undoDisabled"] is False, str(d0["undoDisabled"]))

            print("\n— 加片段：轨道真渲染出片段 —")
            pg.locator('[data-testid="timeline-fullscreen-drop"]').click()
            pg.wait_for_timeout(650)
            d1 = snap()
            check("投放区加出第 1 个片段", len(d1["clips"]) == 1, str(d1["clips"]))
            check("第 1 段落在 x=64（与投放区同一起点）",
                  bool(d1["clips"]) and d1["clips"][0]["x"] == 64, str(d1["clips"][:1]))
            # 5s × 21.4px/s = 107 —— 用**关系**断言（缩放联动），不写死像素
            gap0 = d0["rulerGap"]
            check("片段宽度与刻度间距同源（107 ≈ 5s × 21.4）",
                  bool(d1["clips"]) and abs(d1["clips"][0]["w"] / gap0 - 1.0) < 0.03,
                  f'w={d1["clips"][0]["w"] if d1["clips"] else None} gap={gap0}')
            check("投放区自动让到片段之后（不再压在片段上）",
                  bool(d1["drop"]) and bool(d1["clips"])
                  and d1["drop"][0] >= d1["clips"][0]["x"] + d1["clips"][0]["w"],
                  f'drop@{d1["drop"]} clip@{d1["clips"][:1]}')
            check("**点投放区不会挪动播放头**（点击不穿透到轨道定位）",
                  d1["playhead"] == d0["playhead"], f'{d0["playhead"]}→{d1["playhead"]}')

            pg.locator('[data-testid="timeline-fullscreen-drop"]').click()
            pg.wait_for_timeout(650)
            d2 = snap()
            check("投放区加出第 2 个片段（不再是「只能有一段」）", len(d2["clips"]) == 2,
                  str(d2["clips"]))
            check("两段首尾相接（第二段起点 = 第一段终点）",
                  len(d2["clips"]) == 2
                  and abs((d2["clips"][0]["x"] + d2["clips"][0]["w"]) - d2["clips"][1]["x"]) <= 1,
                  str(d2["clips"]))

            print("\n— 静音钮：也不该挪播放头 —")
            pg.locator('[data-testid="timeline-fullscreen-mute-button"]').click()
            pg.wait_for_timeout(500)
            d2b = snap()
            check("静音可切（aria-label 互翻）", d2b["muteLabel"] == "取消静音", str(d2b["muteLabel"]))
            check("**点静音不挪播放头**（同一条不穿透契约）",
                  d2b["playhead"] == d2["playhead"], f'{d2["playhead"]}→{d2b["playhead"]}')
            pg.locator('[data-testid="timeline-fullscreen-mute-button"]').click()
            pg.wait_for_timeout(400)

            print("\n— 定位播放头：读数与几何同步 —")
            c0 = d2["clips"][0]
            pg.mouse.click(c0["x"] + c0["w"] // 2, 814)
            pg.wait_for_timeout(550)
            d3 = snap()
            check("读数不再是 00:00:00", d3["time"] != "00:00:00", repr(d3["time"]))
            check("播放头横向跟着走（落进第 1 段范围内）",
                  d3["playhead"][0] > c0["x"] and d3["playhead"][0] < c0["x"] + c0["w"],
                  f'ph@{d3["playhead"][0]} clip[{c0["x"]},{c0["x"] + c0["w"]})')

            print("\n— 四枚剪辑工具：从桩变成真动作 —")
            acts = tool("分割")
            d4 = snap()
            check("分割可点", acts == "clicked", acts)
            check("分割后 3 段（第 1 段一分为二）", len(d4["clips"]) == 3, str(d4["clips"]))
            check("分割有反馈且说明了切点", "分成两段" in d4["toast"] and d3["time"] in d4["toast"],
                  repr(d4["toast"][:70]))
            w_before = d4["clips"][0]["w"]
            acts = tool("向右剪裁")
            d5 = snap()
            check("向右剪裁可点", acts == "clicked", acts)
            check("剪裁后该段变窄（且不增宽）",
                  len(d5["clips"]) == 3 and d5["clips"][0]["w"] <= w_before,
                  f'{w_before}→{d5["clips"][0]["w"] if d5["clips"] else None}')
            check("剪裁有反馈", "终点收到" in d5["toast"], repr(d5["toast"][:70]))

            # 剪裁后播放头可能落到所有片段之外，先重新定位再测删除
            cc = d5["clips"][0]
            pg.mouse.click(cc["x"] + cc["w"] // 2, 814)
            pg.wait_for_timeout(500)
            snap()
            n_before = len(d5["clips"])
            acts = tool("删除")
            d6 = snap()
            check("删除可点", acts == "clicked", acts)
            check("删除后少一段", len(d6["clips"]) == n_before - 1, str(d6["clips"]))
            check("删除有反馈", "移除" in d6["toast"], repr(d6["toast"][:70]))
            check("删除后播放头归零", d6["time"] == "00:00:00", repr(d6["time"]))

            print("\n— 撤销 / 重做：只撤剪辑动作，不伤节点 —")
            acts = tool("撤销")
            d7 = snap()
            check("撤销可点", acts == "clicked", acts)
            check("撤销后片段回来了", len(d7["clips"]) == n_before, str(d7["clips"]))
            check("撤销后「重做」变为可用", d7["redoDisabled"] is False, str(d7["redoDisabled"]))
            check("🔴 撤销**没有撤掉时间线节点本身**（825 抓到的真缺陷的看门狗）",
                  d7.get("nodeAlive") is True, f'nodeAlive={d7.get("nodeAlive")}')
            check("浮层仍在（没被连带撤掉）",
                  pg.locator('[data-testid="timeline-fullscreen"]').count() == 1, "浮层没了")
            acts = tool("重做")
            d8 = snap()
            check("重做可点", acts == "clicked", acts)
            check("重做后删除被重新应用", len(d8["clips"]) == n_before - 1, str(d8["clips"]))
            check("重做后「重做」重新禁用", d8["redoDisabled"] is True, str(d8["redoDisabled"]))

            print("\n— 缩放联动：片段 / 刻度 / 播放头必须是同一个式子 —")
            base_gap = d8["rulerGap"]
            pg.get_by_label("放大视图", exact=True).first.click()
            pg.wait_for_timeout(600)
            d9 = snap()
            check("放大后刻度间距 ×1.1", abs(d9["rulerGap"] / base_gap - 1.1) < 0.04,
                  f'{base_gap}→{d9["rulerGap"]}')

            # ⚠️ 比例只能在**非退化**的片段上断言。0 长的片段命中宽度下限，
            #   下限本来就不随缩放变（那是设计），拿它算比例必然假失败。
            #   这条判据第一版就是踩了这个坑：挑了 clips[0]，而它恰好是被
            #   剪成 0 长的那段，于是「18→18」被判成缺陷 —— 差点去改产品。
            #   正确的做法是挑**最长**的那段（它一定没撞下限）。
            def widest(snap: dict) -> dict | None:
                return max(snap["clips"], key=lambda c: c["w"]) if snap["clips"] else None

            w0, w1 = widest(d8), widest(d9)
            check("放大后片段宽度**同步** ×1.1（不是各走各的）",
                  bool(w0) and bool(w1) and abs(w1["w"] / w0["w"] - 1.1) < 0.06,
                  f'{w0} → {w1}')

            # 「行内宽度 = 渲染宽度」：一条通用契约。写死一个下限却不改样式，
            # 行内可以写 2px 而实际渲染 18px（border-box 下盒子窄于
            # padding+border）—— 样式在说谎，靠肉眼看两个 clip 分不出来。
            for tag, dd in (("放大前", d8), ("放大后", d9)):
                lying = [c for c in dd["clips"]
                         if abs(c["w"] - float(c["inlineW"].rstrip("px"))) > 1]
                check(f"{tag}每段的行内宽度都等于渲染宽度（样式不说谎）",
                      not lying, f'说谎的段: {lying}')
            check("读数仍是 100→110%",
                  pg.locator('[data-testid="timeline-fullscreen-zoom"]').inner_text().strip() == "110%",
                  pg.locator('[data-testid="timeline-fullscreen-zoom"]').inner_text().strip())

            pg.screenshot(path=str(EVIDENCE / "clone-fullscreen-825.png"))
            check("无未捕获页面错误", not errs, "; ".join(errs[:3]))
        finally:
            b.close()

    print()
    if failures:
        print(f"FAIL batch825-fsedits — {checks} 项中 {len(failures)} 项失败")
        for f in failures:
            print("  -", f)
        return 1
    print(f"PASS batch825-fsedits — {checks} 项断言全通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
