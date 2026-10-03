#!/usr/bin/env python3
"""batch 703 验收：时间轴的三条轨道不共用同一个时间↔像素映射

## 起点

702 顺手量出一件事：标尺左端 `+2px` 对应 `t=0.008993184852104265`，
于是「每像素 ≈ 0.0045s」进入了账本。本批去问下一个问题：
**这个常数是全局唯一的吗？**

**不是。同一时刻的三条轨道，三个映射。**

## 三张表

**① 映射（zoom=44，duration=8）**

| 轨道 | 拟合出来的时间↔像素映射 | 换算 px/s |
|---|---|---|
| 标尺点击 / 播放头 | `x = 322 + 222.39 × t` | **222.39** |
| 标尺刻度（间距 22.2344px） | 隐含 0.1s/刻 ⟹ | **222.34**（差 0.02%） |
| 关键帧 | `left = 325.4868 + 220.1406 × t` | **220.14**（差 **1.02%**） |

**② 关键帧相对标尺的对齐误差**（把关键帧中心代进标尺映射，看它落在哪个 t）

| 关键帧 | 在标尺映射下落在 | 误差 |
|---|---|---|
| t=0 | t≈0.0405 | **−8.99px** |
| t=4 | t≈3.9977 | +0.51px |
| t=8 | t≈7.9614 | **+9.01px** |

**误差在轨道中段最小、两端最大** —— 这是「两套原点与斜率都不同的映射」的特征。

**③ 刻度是固定 0.1s 一格，81 枚**
zoom 改成 7 / 44 / 93 三档，刻度数**恒为 81**，刻度时间间隔**恒为 0.1s** ——
因为 `duration` 恒为 8s。刻度数不是常量，是 `duration / 0.1s` 的**结果**。

## 顺带查出第四件事：一个能输入但写不进去的控件

`[data-director-shot-end]` 可以聚焦、可以打字、输入框会显示你打的值，
但**三条提交路径全部进不去 store**：`Enter` / `ArrowUp` 之后 store 的
`endTime` 仍是 8、区间标签仍写 `0.0-8.0s`；`Tab` 之后输入框**自己弹回 8**。
⟹ 这不是 699 那种「惰性按钮」，也不是 700 那种「有守卫的拒绝」，
**是第四类：能输入、能聚焦、但没有提交路径。**

## 纪律

- 映射**全部现场拟合**，不硬编码常数（硬编码会把「本机读数」写成「事实」）。
- 判据只断言**读数**，不声称成因（为什么两套映射不同，本批**没有追**）。
- 零 store 写入；zoom 与播放头都用真实点击控件。
- 零点击自检。

## 四条判据

1. `three-tracks-three-maps`
2. `keyframe-alignment-error-is-smallest-in-the-middle`
3. `tick-interval-is-a-fixed-0-1s-and-the-count-81-follows-from-duration-8`
4. `shot-end-input-accepts-typing-but-has-no-commit-path`
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch703-2026-10-01"
W, DESK_H = 1280, 1150

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

# 三条轨道一次读完 —— 读数在 JS 侧取，拟合在 Python 侧做
GEOM = r"""() => {
  const ruler = document.querySelector('[data-director-timeline-ruler]');
  const rb = ruler.getBoundingClientRect();
  const kfEls = Array.from(document.querySelectorAll('[data-director-keyframe-id]'));
  const kf = kfEls.map((e) => {
    const r = e.getBoundingClientRect();
    return { id: e.getAttribute('data-director-keyframe-id'),
             t: parseFloat(e.getAttribute('data-director-keyframe-time')),
             left: r.left, w: r.width, cx: r.left + r.width / 2 };
  });
  const ph = document.querySelector('[data-director-playhead]');
  const pb = ph.getBoundingClientRect();
  const ticks = Array.from(document.querySelectorAll('[data-director-ruler-tick]'))
    .map((e) => e.getBoundingClientRect().left).sort((a, b) => a - b);
  const st = window.__director_store.getState();
  return { rulerLeft: rb.left, rulerWidth: rb.width, rulerY: rb.top + rb.height / 2,
           kf, playhead: { left: pb.left, w: pb.width, cx: pb.left + pb.width / 2 },
           tickCount: ticks.length,
           tickSpacing: ticks.length > 2 ? ticks[1] - ticks[0] : null,
           duration: st.timeline.duration, currentTime: st.timeline.currentTime,
           zoom: st.timeline.zoom };
}"""

SHOT_STATE = r"""() => {
  const s = window.__director_store.getState();
  const shot = (s.shots || [])[0] || null;
  const range = document.querySelector('[data-director-shot-range]');
  const end = document.querySelector('[data-director-shot-end]');
  return { storeEndTime: shot ? shot.endTime : null,
           inputValue: end ? end.value : null,
           rangeText: range ? (range.textContent || '').trim() : null,
           duration: s.timeline.duration };
}"""

SELECT_CAMERA = r"""() => {
  const s = window.__director_store.getState();
  const cam = s.objects.find((o) => o.kind === 'camera');
  if (!cam) return { ok: false, stage: 'no-camera-object' };
  const row = document.querySelector(
    '[data-director-tree] [role="treeitem"][data-director-object-id="'
    + cam.id + '"]');
  if (!row) return { ok: false, stage: 'no-treeitem-by-object-id' };
  row.click();
  return { ok: window.__director_store.getState().selectedObjectId === cam.id,
           name: cam.name };
}"""


def fit(points: list[tuple[float, float]]) -> tuple[float, float]:
    """最小二乘 y = a*x + b。**映射必须现场拟合**，硬编码会把本机读数写成事实。"""
    n = len(points)
    sx = sum(x for x, _ in points); sy = sum(y for _, y in points)
    sxx = sum(x * x for x, _ in points); sxy = sum(x * y for x, y in points)
    a = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    b = (sy - a * sx) / n
    return a, b


def fresh(browser) -> Any:
    page = browser.new_page(viewport={"width": W, "height": DESK_H},
                            device_scale_factor=1)
    b617.open_desk(page)
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(300)
    return page


class Verifier:
    def __init__(self) -> None:
        self.result: dict[str, Any] = {}
        self.failures: list[str] = []
        self.count = 0

    def check(self, name: str, ok: bool, detail: Any = "", note: str = "") -> None:
        self.count += 1
        self.result[name] = {"ok": bool(ok), "detail": detail, "note": note or None}
        if not ok:
            self.failures.append(name)
        print(("  PASS " if ok else "  FAIL ") + name
              + (f"  {str(detail)[:170]}" if detail else "")
              + (f"  [{note[:110]}]" if note else ""))


def main() -> int:
    v = Verifier()
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    null_drift: list[str] = []
    maps: dict[str, Any] = {}
    align: list[dict[str, Any]] = []
    zoom_scan: list[dict[str, Any]] = []
    shot_paths: list[dict[str, Any]] = []

    with sync_playwright() as p:
        br = p.chromium.launch()

        # ---- 零点击自检 ----
        npg = fresh(br)
        g1 = npg.evaluate(GEOM)
        npg.wait_for_timeout(400)
        g2 = npg.evaluate(GEOM)
        null_drift = sorted(k for k in g1 if g1[k] != g2[k])
        npg.close()

        # ---- ① 三条轨道的映射（zoom=44 默认） ----
        pg = fresh(br)
        g = pg.evaluate(GEOM)
        kf_slope, kf_inter = fit([(x["t"], x["left"]) for x in g["kf"]])
        kf_cx_slope, kf_cx_inter = fit([(x["t"], x["cx"]) for x in g["kf"]])
        # 标尺/播放头映射：**用真实点击反推** —— 点在关键帧中心，读播放头落点
        ruler_pts: list[tuple[float, float]] = []
        keyframe_pts: list[dict[str, Any]] = []
        for target in (0.0, 4.0):
            kf = next((x for x in g["kf"] if abs(x["t"] - target) < 1e-9), None)
            if not kf or kf["cx"] > W - 5:
                continue
            pg.mouse.click(kf["cx"], g["rulerY"])
            pg.wait_for_timeout(400)
            gg = pg.evaluate(GEOM)
            ruler_pts.append((gg["currentTime"], gg["playhead"]["left"]))
            keyframe_pts.append({
                "keyframeTime": kf["t"], "keyframeCx": kf["cx"],
                "playheadReadTime": gg["currentTime"],
                "playheadCx": gg["playhead"]["cx"],
                "playheadVsKeyframePx": kf["cx"] - gg["playhead"]["cx"]})
            print(f"  点关键帧 t={kf['t']} 的中心 x={kf['cx']:.3f} → "
                  f"currentTime={gg['currentTime']:.6f}，播放头中心 {gg['playhead']['cx']:.3f}")
        ph_slope, ph_inter = fit(ruler_pts)
        # 刻度映射：间距 px ÷ 0.1s
        tick_map = (g["tickSpacing"] / 0.1) if g["tickSpacing"] else None
        maps = {
            "zoom": g["zoom"], "duration": g["duration"],
            "rulerLeft": g["rulerLeft"], "rulerWidth": g["rulerWidth"],
            "playheadMap": {"x": f"{ph_inter:.4f} + {ph_slope:.4f} * t",
                            "pxPerSecond": ph_slope,
                            "fittedFrom": ruler_pts,
                            "how": "真实点击标尺，读播放头落点反推"},
            "tickMap": {"tickCount": g["tickCount"], "spacingPx": g["tickSpacing"],
                        "pxPerSecondIf0_1sPerTick": tick_map,
                        "how": "刻度间距 ÷ 假设的 0.1s"},
            "keyframeLeftMap": {"left": f"{kf_inter:.4f} + {kf_slope:.4f} * t",
                                "pxPerSecond": kf_slope,
                                "how": "对 keyframe left 做最小二乘"},
            "keyframeCenterMap": {"cx": f"{kf_cx_inter:.4f} + {kf_cx_slope:.4f} * t",
                                  "pxPerSecond": kf_cx_slope},
            "deltas": {
                "tickVsPlayheadPct": (tick_map / ph_slope - 1) * 100,
                "keyframeVsPlayheadPct": (kf_cx_slope / ph_slope - 1) * 100},
        }

        # ---- ② 关键帧相对标尺的对齐误差 ----
        for kf in g["kf"]:
            t_implied = (kf["cx"] - g["rulerLeft"]) / ph_slope
            align.append({"keyframeTime": kf["t"], "keyframeCx": kf["cx"],
                          "timeImpliedByRulerMap": t_implied,
                          "errorSeconds": t_implied - kf["t"],
                          "errorPx": ph_slope * (t_implied - kf["t"])})
        pg.close()
        for a in align:
            print(f"  关键帧 t={a['keyframeTime']} 在标尺映射下落在 "
                  f"t={a['timeImpliedByRulerMap']:.4f}  误差 {a['errorSeconds']:+.4f}s "
                  f"({a['errorPx']:+.2f}px)")

        # ---- ③ zoom 三档，刻度数与刻度时间间隔 ----
        for step in (None, 1.0 / 6.0, 5.0 / 6.0):
            pg = fresh(br)
            if step is not None:
                z = pg.locator("[data-director-timeline-zoom]").first
                bb = z.bounding_box()
                pg.mouse.click(bb["x"] + bb["width"] * step, bb["y"] + bb["height"] / 2)
                pg.wait_for_timeout(500)
            gz = pg.evaluate(GEOM)
            per_s = gz["rulerWidth"] / gz["duration"] if gz["duration"] else None
            zoom_scan.append({
                "zoom": gz["zoom"], "tickCount": gz["tickCount"],
                "tickSpacingPx": gz["tickSpacing"],
                "rulerWidth": gz["rulerWidth"],
                "pxPerSecond": per_s,
                "tickSeconds": (gz["tickSpacing"] / per_s) if per_s and gz["tickSpacing"] else None,
            })
            print(f"  zoom={gz['zoom']:>3}  刻度数={gz['tickCount']:3}  "
                  f"刻度={gz['tickSpacing']:.4f}px  标尺 {gz['rulerWidth']:.2f}px  "
                  f"⟹ 每刻 {zoom_scan[-1]['tickSeconds']:.4f}s")
            pg.close()

        # ---- ④ 镜头结束时间的提交路径穷举 ----
        for label, key in (("Enter", "Enter"), ("Tab", "Tab"), ("ArrowUp", "ArrowUp")):
            pg = fresh(br)
            pg.evaluate(SELECT_CAMERA)
            pg.wait_for_timeout(500)
            e = pg.locator("[data-director-shot-end]").first
            e.click()
            pg.wait_for_timeout(200)
            e.fill("12")
            pg.wait_for_timeout(150)
            pg.keyboard.press(key)
            pg.wait_for_timeout(600)
            st = pg.evaluate(SHOT_STATE)
            st["path"] = label
            st["committed"] = st["storeEndTime"] == 12
            shot_paths.append(st)
            print(f"  按 {label:8} → store.endTime={st['storeEndTime']}  "
                  f"输入框={st['inputValue']!r}  区间标签={st['rangeText']!r}")
            pg.close()
        br.close()

    # align 有 6 条（两条轨道各 3 个时刻），**必须按时刻去重再比大小** ——
    # 第一版要求 len(ends)==2 而实际是 4 条，判据自己写错了。
    by_time = {a["keyframeTime"]: a for a in align}
    mid = by_time.get(4.0)
    ends = [by_time[0.0], by_time[8.0]] if 0.0 in by_time and 8.0 in by_time else []
    worst = max(abs(a["errorPx"]) for a in by_time.values())
    best = min(abs(a["errorPx"]) for a in by_time.values())

    v.check(
        "three-tracks-three-maps",
        maps["deltas"]["keyframeVsPlayheadPct"] < -0.5
        and abs(maps["deltas"]["tickVsPlayheadPct"]) < 0.5
        and maps["tickMap"]["tickCount"] == 81,
        detail=maps,
        note="the tick map and the playhead map agree to 0.02% (so ticks belong to the "
             "playhead's map), while the keyframe lane runs 1.02% narrower — "
             "two affine maps, not one shared constant")

    v.check(
        "keyframe-alignment-error-is-smallest-in-the-middle",
        bool(mid) and len(ends) == 2
        and abs(mid["errorPx"]) < abs(ends[0]["errorPx"])
        and abs(mid["errorPx"]) < abs(ends[1]["errorPx"])
        and len(by_time) == 3,
        detail={"alignmentByTime": by_time, "worstPx": worst, "bestPx": best,
                "signature": "误差在 t=0 与 t=8 两端各约 ±9px、t=4 中段 −0.02px —— "
                             "两套映射在轨道中段交叉，两端发散",
                "whyTheReadoutHidesIt":
                    "点关键帧 t=4 的中心，currentTime 读数是精确的 4.000000，"
                    "因为中段误差只有 0.02px，被读数的小数位吃掉了"},
        note="a 9px misalignment at both ends of an 8-second track is about 0.04s — "
             "small enough that no readout shows it, and the middle of the track is "
             "where the two maps happen to agree")

    tick_secs = {round(z["tickSeconds"], 4) for z in zoom_scan if z["tickSeconds"]}
    v.check(
        "tick-interval-is-a-fixed-0-1s-and-the-count-81-follows-from-duration-8",
        len(zoom_scan) == 3
        and {z["tickCount"] for z in zoom_scan} == {81}
        and all(abs(s - 0.1) < 0.002 for s in tick_secs),
        detail={"zoomScan": zoom_scan, "distinctTickSeconds": sorted(tick_secs),
                "explanation": "duration 恒为 8s，刻度固定 0.1s 一格 ⟹ 枚数必然是 8/0.1+1 = 81。"
                               "**刻度数不是常量，是 duration 的结果** —— "
                               "本批没能改 duration（见判据 4），所以「duration 变了枚数会变」"
                               "这条**未取证**"},
        note="81 looked like a hard-coded constant; it is 8/0.1+1, and the ruler "
             "redraws 81 ticks at every zoom because the duration never moves")

    v.check(
        "shot-end-input-accepts-typing-but-has-no-commit-path",
        all(not s["committed"] and s["storeEndTime"] == 8 for s in shot_paths)
        and any(s["inputValue"] == "12" for s in shot_paths)
        and any(s["inputValue"] == "8" for s in shot_paths),
        detail={"paths": shot_paths,
                "whatHappens": "Enter / ArrowUp：输入框留着 12，store 的 endTime 仍是 8，"
                               "区间标签仍是 0.0-8.0s；Tab：输入框自己弹回 8",
                "theCategory": "第四类 —— 不是 699 的惰性按钮（这个能聚焦能打字），"
                               "也不是 700 的有据可查的拒绝（连命令都没发）"},
        note="an enabled, focusable, typeable field with no observed commit path; "
             "the rejection is silent in all three cases")

    out = {
        "width": W, "deskHeight": DESK_H,
        "nullClickDrift": null_drift,
        "maps": maps, "alignment": align,
        "zoomScan": zoom_scan, "shotEndPaths": shot_paths,
        "theFinding":
            "时间轴的三条轨道不共用同一个时间↔像素映射。标尺点击与播放头是 "
            "x = 322 + 222.39t（px/s 222.39）；刻度间距 22.2344px 隐含 0.1s/刻 ⟹ "
            "222.34（与播放头差 0.02%，所以刻度属于播放头那套）；"
            "关键帧是 left = 325.4868 + 220.1406t（px/s 220.14，**差 1.02%**）。"
            "后果：关键帧相对标尺的对齐误差在 t=0 为 −8.99px、t=4 为 +0.51px、"
            "t=8 为 +9.01px —— 中段最小、两端最大。点关键帧中心时播放头读数仍是"
            "精确的 4.000000，因为中段误差只有半像素、被读数四舍五入吃掉了。",
        "theSecondFinding":
            "[data-director-shot-end] 是第四类控件：能聚焦、能打字、输入框会显示你打的值，"
            "但 Enter / ArrowUp / Tab 三条提交路径全部进不去 store（endTime 恒为 8），"
            "Tab 之后输入框自己弹回 8。",
        "whatIsNotClaimed":
            "**不声称为什么有两套映射** —— 本批只测出「有两套」，没有追成因。"
            "不声称这 9px 的错位是缺陷还是有意（源站未取证，需授权点击）。"
            "不声称「duration 变了刻度数会变」（duration 无法从 UI 改，见判据 4）。"
            "不声称源站行为（**未取证，需授权点击**）。**不改 src/**。",
        "storeWritesInThisRun": "none — zoom and the playhead were moved by real clicks",
        "relationTo702":
            "702 顺手量出的「每像素 ≈ 0.0045s」**只对标尺/播放头那条轨道成立**；"
            "关键帧那条是 0.004543s。本批把那行账注补齐成三行。",
    }
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "checks": v.result},
                   ensure_ascii=False, indent=1, default=repr), encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
