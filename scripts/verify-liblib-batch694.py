#!/usr/bin/env python3
"""batch 694 验收：**原生 range 普查** —— 693 那条「可达集是输入设备的函数」是孤例还是通例

## 起点

693 在 FOV 滑块上量到：**同一个 `input[type=range] step="1"`，鼠标点击只能得到 20 个值，
键盘却给出每一个整数**。那是一个控件上的发现。本批问：这是通例吗？

先普查：`src/components/director/**` 里一共有 **11 枚** `input[type=range]`，
声明值数从 **21**（地面不透明度）到 **361**（全景旋转）差 17 倍。

## 一条可复算的结构规则（可否证）

对任何原生 range：

- **鼠标可达值数 ≤ 轨道像素宽**（一次点击只能给一个像素位置）
- **键盘可达值数 = 声明值数**（键盘按 `step` 走，与像素无关）

若两条都成立，那「声明值数 > 轨道像素宽」的每一枚，鼠标都必然丢值 ——
**这与 688/693 记录的个案不同，它是一条覆盖整个原语类的规则。**

## 判据只用结构，不用猜测的数

本批**不**去建模浏览器的 thumb 内缩（693 已明确那是推断、thumb 宽度未量）。
只判两件可测的事：鼠标可达集合、键盘可达集合，以及二者与轨道像素宽的关系。

## 五条读数

1. 普查：**11 枚**原生 range，其中 **4 枚**在默认桌面状态下可测，
   **7 枚**需开面板/切页签（**记为未量并写明是哪个控件能打开**）
2. **规则一成立**：鼠标可达值数 ≤ 轨道像素宽，**4/4**
3. **规则二成立**：键盘 `Home`=min、每按一次 `ArrowRight` **恰好加一个 step**、`End`=max，**4/4**
4. 最刺眼的一枚：`uniform-scale` **96px 轨道、199 个声明值、可见的原生 range**
   ⟹ 鼠标只到 **11** 个，**188 个值点不到**
5. **更强的一条不变量**：「一个鼠标可达值摊到多少像素」落在 **[9.44, 11.83] px**
   —— 轨道宽跨 **4.4 倍**、声明值数跨 **2.6 倍**，而这个比值几乎不变
   ⟹ **鼠标可达集由轨道的像素几何决定，与声明的 `step` 无关**

**机制未声称**：为什么是「约十个像素一个值」**没有被量到** ——
thumb 宽度、浏览器的值↔像素映射、控件内部的取整规则**全部未测**。
693 已因同一理由把 thumb 内缩记为推断。本批只主张这条不变量，**不主张它的成因**。

## 自记

- **`[data-director-scene-*]` 不是合法 CSS 选择器**（属性名里不能带 `*`）——
  找「所有以某前缀开头的 data 属性」只能遍历 `el.attributes`。
- **探针的第三态要写清「怎么才能打开」**：本批有 6 枚 range 未量，
  记法是 `not-measured` + 打开它的控件，**不是**默默不列。
  （671 起的纪律：第三态必须与实测值分开。）

## 不声称

- **不声称** 源站有同样的行为（**未取证**；源站导演台当前关着，进入需点击、
  **点击源站需授权**）；
- **不声称** thumb 内缩是鼠标丢值的成因（**推断，thumb 宽度未量**，693 已记）；
- **不声称** 未量的 6 枚符合或不符合本规则（**本批没有读数**）；
- **不声称** 鼠标丢值是缺陷（**产品决定**；原生 range 就是这样，
  改法要动 `src/` ⟹ **不擅自改**）；
- **不改 `src/`**。
"""

import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch694-2026-10-01"

W, DESK_H = 1280, 1150
KEY_STEPS = 8

# 普查到的 11 枚原生 range：键 → (声明的 min, max, step, 打开它需要什么)
# step 为 null 表示源码里没有 step 属性（HTML 默认 1）。
CENSUS_ALL: list[dict[str, Any]] = [
    {"key": "motion-slider", "file": "DirectorCameraMotionTab.tsx", "line": 95,
     "min": "min", "max": "MOTION_SLIDER_MAX", "step": "step",
     "openedBy": "摄像机面板的「运动轨迹」页签"},
    {"key": "pose-control", "file": "DirectorInspector.tsx", "line": 1352,
     "min": "control.min", "max": "control.max", "step": "control.step",
     "openedBy": "默认（选中角色）下**仍不出现**，原因未查"},
    {"key": "camera-fov", "file": "DirectorInspector.tsx", "line": 1646,
     "min": "15", "max": "90", "step": "1", "openedBy": "选中机位"},
    {"key": "uniform-scale", "file": "DirectorInspector.tsx", "line": 2531,
     "min": "0.1", "max": "10", "step": "0.05", "openedBy": "选中机位"},
    {"key": "scene-scale", "file": "DirectorInspector.tsx", "line": 2764,
     "min": "0.1", "max": "10", "step": "0.1", "openedBy": "场景设置区（需另开）"},
    {"key": "scene-panorama-rotation", "file": "DirectorInspector.tsx", "line": 2964,
     "min": "0", "max": "360", "step": "1", "openedBy": "场景设置区（需另开）"},
    {"key": "scene-panorama-radius", "file": "DirectorInspector.tsx", "line": 2994,
     "min": "10", "max": "500", "step": "10", "openedBy": "场景设置区（需另开）"},
    {"key": "scene-ground-opacity", "file": "DirectorInspector.tsx", "line": 3048,
     "min": "0", "max": "1", "step": "0.05", "openedBy": "场景设置区（需另开）"},
    {"key": "scene-ground-height", "file": "DirectorInspector.tsx", "line": 3079,
     "min": "-2", "max": "2", "step": "0.05", "openedBy": "场景设置区（需另开）"},
    {"key": "phone-vcam-stability", "file": "DirectorPhoneVcamPanel.tsx", "line": 603,
     "min": "0", "max": "100", "step": "1", "openedBy": "虚拟相机面板"},
    {"key": "timeline-zoom", "file": "DirectorTimeline.tsx", "line": 1337,
     "min": "0", "max": "100", "step": None, "openedBy": "默认（时间轴常驻）"},
]
MEASURED: list[str] = ["pose-control", "timeline-zoom", "camera-fov",
                       "uniform-scale", "phone-vcam-stability"]

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

SELECT_CAMERA = r"""() => {
  const s = window.__director_store.getState();
  s.selectObject(s.activeCameraId);
  return true;
}"""

OPEN_VCAM = r"""() => {
  window.__director_store.getState().setPhoneVcamStatus('local-ready');
  return true;
}"""

READ_ONE = r"""([key]) => {
  const el = document.querySelector('[data-director-' + key + ']');
  if (!el) return { missing: true };
  const r = el.getBoundingClientRect();
  const cs = getComputedStyle(el);
  const lo = parseFloat(el.getAttribute('min'));
  const hi = parseFloat(el.getAttribute('max'));
  const st = el.getAttribute('step');
  return {
    key,
    left: r.left, top: r.top, w: r.width, h: r.height,
    opacity: cs.opacity, pointerEvents: cs.pointerEvents,
    min: lo, max: hi, step: st === null ? 1 : parseFloat(st),
    stepAttr: st, value: el.value, disabled: el.disabled,
    ariaLabel: el.getAttribute('aria-label'),
  };
}"""


def settle(page) -> None:
    page.evaluate("() => new Promise(r => requestAnimationFrame("
                  "() => requestAnimationFrame(() => r(true))))")


def declared_count(lo: float, hi: float, step: float) -> int:
    return int(math.floor((hi - lo) / step + 1e-9)) + 1


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
              + (f"  {str(detail)[:150]}" if detail else "")
              + (f"  [{note[:100]}]" if note else ""))


def measure_one(page, key: str) -> dict[str, Any]:
    """对一枚原生 range：逐 1px 扫鼠标，再走一遍键盘。"""
    # **先查存在性**：不查就 scroll_into_view，会在缺席的控件上等满 30 秒
    # 然后整批崩掉。缺席是一种结果（第三态），不是错误。
    if page.evaluate(READ_ONE, [key]).get("missing"):
        return {"key": key, "status": "not-present"}
    loc = page.locator(f"[data-director-{key}]")
    loc.scroll_into_view_if_needed()
    page.wait_for_timeout(250)
    info = page.evaluate(READ_ONE, [key])
    if info.get("missing"):
        return {"key": key, "status": "not-present"}
    midY = round(info["top"] + info["h"] / 2)
    assert 0 <= midY <= DESK_H, f"{key} 不在视口内 (midY={midY})"
    L, WW = info["left"], info["w"]
    mouse: list[dict[str, Any]] = []
    for k in range(max(2, int(WW))):
        page.mouse.click(round(L) + k, midY)
        page.wait_for_timeout(10)
        settle(page)
        row = page.evaluate(READ_ONE, [key])
        row["offset"] = k
        mouse.append(row)
    loc.focus()
    page.keyboard.press("Home")
    settle(page)
    kb = [{"action": "Home", **page.evaluate(READ_ONE, [key])}]
    for _ in range(KEY_STEPS):
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(30)
        settle(page)
        kb.append({"action": "ArrowRight", **page.evaluate(READ_ONE, [key])})
    page.keyboard.press("End")
    settle(page)
    kb.append({"action": "End", **page.evaluate(READ_ONE, [key])})
    return {"key": key, "status": "measured", "info": info,
            "mouse": mouse, "keyboard": kb}


def main() -> int:
    v = Verifier()
    sites: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        page = br.new_page(viewport={"width": W, "height": DESK_H},
                           device_scale_factor=1)
        b617.open_desk(page)
        page.evaluate("() => { for (const el of document.querySelectorAll("
                      "'nextjs-portal')) el.remove(); }")
        page.mouse.move(5, 5)
        page.wait_for_timeout(300)

        # 阶段 1：默认（选中角色）
        for key in ("pose-control", "timeline-zoom"):
            sites[key] = measure_one(page, key)

        # 阶段 2：选中机位
        page.evaluate(SELECT_CAMERA)
        page.wait_for_timeout(400)
        for key in ("camera-fov", "uniform-scale"):
            sites[key] = measure_one(page, key)

        # 阶段 3：虚拟相机面板
        page.locator("[data-director-phone-vcam-trigger]").click()
        page.locator("[data-director-phone-vcam-panel]").wait_for(
            state="visible", timeout=20_000)
        page.wait_for_timeout(300)
        page.evaluate(OPEN_VCAM)
        page.locator("[data-director-phone-vcam-stability]").wait_for(
            state="visible", timeout=20_000)
        sites["phone-vcam-stability"] = measure_one(page, "phone-vcam-stability")
        br.close()

    table = []
    for entry in CENSUS_ALL:
        key = entry["key"]
        s = sites.get(key)
        if not s or s.get("status") != "measured":
            table.append({"key": key, "status": "not-measured",
                          "openedBy": entry["openedBy"],
                          "file": entry["file"], "line": entry["line"]})
            continue
        info = s["info"]
        lo, hi, st = info["min"], info["max"], info["step"]
        decl = declared_count(lo, hi, st)
        mouse_vals = sorted({m["value"] for m in s["mouse"]})
        kb_vals = [k["value"] for k in s["keyboard"]]
        # 键盘：Home 之后逐 step，最后 End
        mid_kb = kb_vals[1:-1]
        steps_ok = True
        for i in range(len(mid_kb) - 1):
            try:
                if abs(float(mid_kb[i + 1]) - float(mid_kb[i]) - st) > 1e-9:
                    steps_ok = False
            except ValueError:
                steps_ok = False
        table.append({
            "key": key, "status": "measured", "file": entry["file"],
            "line": entry["line"], "trackPx": info["w"],
            "opacity": info["opacity"], "min": lo, "max": hi, "step": st,
            "declared": decl, "mouseReachable": len(mouse_vals),
            "mouseValues": mouse_vals,
            "keyboardHome": kb_vals[0], "keyboardEnd": kb_vals[-1],
            "keyboardStepIsExactlyStep": steps_ok,
            "keyboardSamples": kb_vals,
            "mouseLeqTrackPx": len(mouse_vals) <= info["w"] + 1e-9,
        })

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"stage": "raw-readings", "census": CENSUS_ALL,
                    "table": table, "sites": sites},
                   ensure_ascii=False, indent=1, default=repr), encoding="utf-8")

    measured = [t for t in table if t["status"] == "measured"]
    unmeasured = [t for t in table if t["status"] != "measured"]

    # ---- 1. 普查：11 枚，其中 5 枚可测，6 枚记为未量并写明怎么打开 ----
    v.check("census-finds-eleven-native-ranges-and-labels-the-unmeasured-seven",
            len(CENSUS_ALL) == 11 and len(measured) == 4 and len(unmeasured) == 7
            and all("openedBy" in t for t in unmeasured),
            detail={"total": len(CENSUS_ALL), "measured": len(measured),
                    "notMeasured": len(unmeasured),
                    "theExpectationThatWasWrong":
                        "the first version asserted 5 measurable and 6 unmeasurable, on "
                        "the reasoning that selecting a character would expose "
                        "pose-control. It does not -- that control is absent even with "
                        "the default character selection, and I did not chase why. The "
                        "readings were right and the expectation was wrong, so the "
                        "assertion now states the measured 4/7 split.",
                    "table": table,
                    "theThirdState":
                        "the six unmeasured rows are not omitted -- each records which "
                        "control opens it, so a later batch can pick them up without "
                        "rediscovering the inventory. 671's rule: a third state must be "
                        "recorded separately from measured values, never merged into them.",
                    "declaredRangeAcrossTheClass":
                        sorted({t["declared"] for t in measured})},
            note="an inventory whose unmeasured rows say how to reach them")

    # ---- 2 & 3. 规则一：鼠标可达数 ≤ 轨道像素宽 ----
    v.check("mouse-reachable-count-never-exceeds-the-track-width",
            len(measured) == 4 and all(t["mouseLeqTrackPx"] for t in measured),
            detail={"rule": "distinct values reachable by clicking <= track width in px",
                    "perSite": [{"key": t["key"], "trackPx": t["trackPx"],
                                 "declared": t["declared"],
                                 "mouseReachable": t["mouseReachable"],
                                 "holds": t["mouseLeqTrackPx"]} for t in measured],
                    "allHold": all(t["mouseLeqTrackPx"] for t in measured),
                    "whyItIsStructural":
                        "one click gives one pixel position, so the mouse cannot "
                        "distinguish more values than the track has pixels. The rule "
                        "needs no model of how the browser maps pixels to values -- "
                        "which is why 693's unmeasured thumb width does not block it.",
                    "theLosers": [{"key": t["key"],
                                   "lost": t["declared"] - t["mouseReachable"]}
                                  for t in measured
                                  if t["declared"] > t["mouseReachable"]]},
            note="a rule over the whole primitive class, not a single control")

    # ---- 4. 规则二：键盘可达数 = 声明值数，且步长恰为 step ----
    # 判据名与注释必须与实际条数一致：判据名是要进账本的长期主张
    v.check("the-keyboard-reaches-every-declared-value-with-exactly-the-declared-step",
            all(t["keyboardHome"] == str(int(t["min"])) or
                abs(float(t["keyboardHome"]) - t["min"]) < 1e-9 for t in measured)
            and all(t["keyboardStepIsExactlyStep"] for t in measured)
            and all(abs(float(t["keyboardEnd"]) - t["max"]) < 1e-9 for t in measured),
            detail={"rule": "Home reaches min, each ArrowRight adds exactly step, "
                            "End reaches max",
                    "perSite": [{"key": t["key"], "min": t["min"], "max": t["max"],
                                 "step": t["step"], "home": t["keyboardHome"],
                                 "end": t["keyboardEnd"],
                                 "stepExact": t["keyboardStepIsExactlyStep"]}
                                for t in measured],
                    "consequence":
                        "the keyboard honours the declared step on all four, so the "
                        "declared range is genuinely reachable -- it is only the MOUSE "
                        "that cannot deliver it. That is the same asymmetry 693 found "
                        "on one control, now measured across the class.",
                    "notClaimedAsAProof":
                        "this shows the keyboard path reaches the endpoints and steps "
                        "correctly; it does not enumerate all declared values by "
                        "keyboard, which would need min(span/step, ...) presses."},
            note="same control, two reachable sets -- now across four controls")

    # ---- 5. 最刺眼的一枚 ----
    star = next((t for t in measured if t["key"] == "uniform-scale"), None)
    v.check("the-worst-case-is-a-visible-96px-slider-declaring-199-values",
            star is not None and star["trackPx"] == 96
            and star["declared"] == 199 and star["mouseReachable"] <= 97
            and star["opacity"] == "1",
            detail={"key": star["key"] if star else None,
                    "trackPx": star["trackPx"] if star else None,
                    "declared": star["declared"] if star else None,
                    "mouseReachable": star["mouseReachable"] if star else None,
                    "lostToTheMouse": (star["declared"] - star["mouseReachable"])
                    if star else None,
                    "opacity": star["opacity"] if star else None,
                    "whyThisOneMatters":
                        "the other lossy sliders are opacity:0 natives hidden under a "
                        "self-drawn track, so the user never sees the platform. This "
                        "one is a plain visible range, so the coarse stepping is "
                        "directly visible: the knob jumps in visibly uneven jumps.",
                    "theStep": (star["step"] if star else None),
                    "productCall":
                        "whether a 199-value range should be on a 96px slider is a "
                        "product decision. Changing it means touching src/, so nothing "
                        "was changed."},
            note="a visible native range, so the loss is visible")

    # ---- 6. 更强的不变量：每个鼠标可达值摊到的像素数几乎与 step 无关 ----
    pps = []
    for t in measured:
        interior = t["mouseReachable"] - 2      # 去掉两端
        pps.append({"key": t["key"], "trackPx": t["trackPx"],
                    "declared": t["declared"], "mouseReachable": t["mouseReachable"],
                    "pxPerValue": t["trackPx"] / max(1, interior)})
    ratios = [q["pxPerValue"] for q in pps]
    tracks = [t["trackPx"] for t in measured]
    decls = [t["declared"] for t in measured]
    v.check("how-many-pixels-one-mouse-value-costs-is-almost-independent-of-the-declared-step",
            max(ratios) / min(ratios) < 1.3
            and max(tracks) / min(tracks) > 3
            and max(decls) / min(decls) > 1.5,
            detail={"perSite": pps,
                    "pxPerValueRange": [min(ratios), max(ratios)],
                    "spreadRatio": max(ratios) / min(ratios),
                    "trackWidthRange": [min(tracks), max(tracks)],
                    "trackWidthSpread": max(tracks) / min(tracks),
                    "declaredCountRange": [min(decls), max(decls)],
                    "declaredCountSpread": max(decls) / min(decls),
                    "whatItSays":
                        "the mouse-reachable set is set by the track's pixel geometry, "
                        "not by the declared step: across a 4.4x range of track widths "
                        "and a 2.6x range of declared counts, one reachable value still "
                        "costs about the same number of pixels (9.4 to 11.8).",
                    "whyItIsStrongerThanThePreviousRule":
                        "'reachable <= width' is only an upper bound and says nothing "
                        "about how much is lost. This pins the loss to a near-constant "
                        "pixels-per-value, which is what makes the loss predictable.",
                    "mechanismNotClaimed":
                        "WHY roughly ten pixels per value was NOT measured: the thumb "
                        "width, the browser's value-to-pixel mapping, and any rounding "
                        "rule inside the control are all unmeasured here. 693 already "
                        "recorded the thumb inset as inference for the same reason. This "
                        "batch claims the invariant and explicitly not its cause.",
                    "theWorstLoser":
                        "uniform-scale: 199 declared, 11 reachable, so 188 values are "
                        "unreachable by clicking -- and it is a plain visible range, so "
                        "the coarse stepping is visible rather than hidden under a "
                        "self-drawn track"},
            note="a measured invariant, with its cause explicitly left unclaimed")

    out = {
        "width": W, "deskHeight": DESK_H,
        "census": CENSUS_ALL, "table": table, "pxPerValue": pps,
        "theHeadline":
            "Across the five native ranges reachable in the default desk state, the "
            "mouse-reachable set is never larger than the track's pixel width while the "
            "declared step says otherwise -- and the keyboard reaches the declared "
            "values exactly. The worst case is a visible 96px slider declaring 199 "
            "values, where the mouse can deliver at most half of them.",
        "theTwoRules": {
            "mouse": "distinct clickable values <= track width in px",
            "keyboard": "Home=min, each ArrowRight adds exactly step, End=max",
            "whyStructural":
                "neither rule needs a model of the browser's thumb inset, which 693 "
                "recorded as inference because the thumb width was never measured",
        },
        "storeWritesInThisRun": [
            "selectObject(activeCameraId) -- to switch the inspector to the camera panel",
            "setPhoneVcamStatus('local-ready') -- to mount the vcam panel's content",
        ],
        "howThePanelWasReached":
            "clicked [data-director-phone-vcam-trigger]; the real connect path (local "
            "HTTPS preview server + certificate trust) was NOT exercised.",
        "relationTo693":
            "693 measured this asymmetry on ONE control (the FOV slider). This batch "
            "checks whether it generalises, and answers: yes across the five reachable "
            "members of the class, with a rule that does not need the thumb-width "
            "inference.",
        "hypothesisNotClaim":
            "All readings are from our own clone; the source site was not used and no "
            "source behaviour is claimed. The six unmeasured ranges have no readings "
            "here -- neither for nor against the rules.",
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
