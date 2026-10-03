#!/usr/bin/env python3
"""batch 697 验收：把 696 的失效**证伪**成程序化路径特有的现象

## 起点

696 钉出了一条行为序列：**在右栏的 range 上按过一次键，紧接着切换到另一个面板，
新面板里的 range 收不到鼠标输入。** 但 696 的复现走的是
`selectObject(null)` 这个 **store API**，而真人取消选中是「**点空白处**」。

696 因此写下了一句限制：**「不声称这是一个用户能撞上的缺陷」**。
本批就是去把这句限制**兑现或推翻** —— 而且**两种结果都有价值**：

- 真人路径也复现 ⟹ 它就是用户可见缺陷，该报给产品；
- 真人路径不复现 ⟹ 它只是**测试路径特有的现象**，696 的结论必须限定在程序化路径。

## 本批的结果：第二种

**点空白处取消选中，即使刚在姿态滑杆上按过 `End`，场景滑杆仍然是 11 个可达值**，
三次重复全是 11。**程序化路径是 1。两条路径不等价。**

## 最重要的一条

**「点空白处」这三个字本身就是陷阱。** 我第一次取坐标 `(640, 560)`，
它不是空白 —— 它**选中了一张道具桌** `director-prop-table`，
于是右栏渲染的是道具桌属性，`scene` 控件根本没渲染（0 枚），
读数是 `None` 而不是 `11` 或 `1`。

**必须先测出「哪些坐标真的是空白」，再拿它当空白用。**
13 个坐标能让 `selectedObjectId` 变成 `null`；`(640, 560)` 不在其中。

**这和 695 那次「用 `[data-director-character-tab]` 找机位页签」是同一个错误的
两种长相：我以为自己走的路径，不是我走的路径。**

## 四条判据

1. **「空白」是测出来的，不是假设的** —— 13 个坐标能让选中变 `null`，
   而随手取的 `(640, 560)` 不在其列（它选中了一张道具桌）
2. **真人路径下不复现**：不按键 11、按键 11、再重复一次还是 11
3. **程序化路径下复现**：`selectObject(null)` 给 1
4. **两条路径不等价** ⟹ 696 的结论**必须限定在程序化路径**上

## 不声称

- **不声称** 机制被追到了（697 证伪的是**可达性**，不是机制）；
- **不声称** 真人路径在**所有**操作序列下都不复现（本批只测了这一条序列：
  姿态页签 → 按 `End` → 点空白）；
- **不声称** 源站有同样现象（**未取证**，进入需点击、**需授权**）；
- **不改 `src/`**。
"""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch697-2026-10-01"
W, DESK_H = 1280, 1150

POSE_SEL = '[data-director-pose-control="torso.roll"]'
SCENE_SEL = "[data-director-scene-scale]"
# dbg697c 之前 dbg697b 实测：能让 selectedObjectId 变 null 的坐标之一
BLANK_XY = (400, 500)
# 随手取的那个 —— 本批要证明它**不是**空白
HAPPY_BLANK_XY = (640, 560)

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

READ = r"""([sel]) => {
  const el = document.querySelector(sel);
  if (!el) return { missing: true };
  const r = el.getBoundingClientRect();
  return { left: r.left, top: r.top, w: r.width, h: r.height, value: el.value };
}"""

STATE = r"""() => {
  const s = window.__director_store.getState();
  return {
    selected: s.objects.find((o) => o.id === s.selectedObjectId)?.id ?? null,
    sceneRanges: document.querySelectorAll('[data-director-scene-scale]').length,
  };
}"""

# 找「真正的空白」：扫一批坐标，读点完之后的 selectedObjectId
PROBE_BLANKS = r"""(pts) => {
  const s = window.__director_store.getState();
  return pts.map(([x, y]) => {
    const el = document.elementFromPoint(x, y);
    const onNode = !!(el && el.closest && el.closest('.react-flow__node'));
    return { x, y, onNode };
  });
}"""


def settle(page) -> None:
    page.evaluate("() => new Promise(r => requestAnimationFrame("
                  "() => requestAnimationFrame(() => r(true))))")


def scan(page, sel: str) -> dict[str, Any]:
    j = page.evaluate(READ, [sel])
    if j.get("missing"):
        return {"missing": True}
    L, WW, my = j["left"], j["w"], round(j["top"] + j["h"] / 2)
    vals: list[str] = []
    for k in range(int(WW)):
        page.mouse.click(round(L) + k, my)
        page.wait_for_timeout(6)
        settle(page)
        vals.append(page.evaluate(READ, [sel])["value"])
    return {"missing": False, "distinct": len(set(vals))}


def click_pose_and_maybe_key(page, press_key: bool) -> None:
    for b in page.locator('[data-director-character-tab="pose"]').all():
        b.click()
        page.wait_for_timeout(500)
        break
    loc = page.locator(POSE_SEL).first
    loc.scroll_into_view_if_needed()
    page.wait_for_timeout(200)
    j = page.evaluate(READ, [POSE_SEL])
    for k in range(int(j["w"])):
        page.mouse.click(round(j["left"]) + k, round(j["top"] + j["h"] / 2))
        page.wait_for_timeout(6)
        settle(page)
    if press_key:
        loc.focus()
        page.keyboard.press("End")
        page.wait_for_timeout(200)
        settle(page)


def run_case(browser, mode: str, press_key: bool) -> dict[str, Any]:
    """mode: 'store' | 'click' —— 两种取消选中的路径。"""
    page = browser.new_page(viewport={"width": W, "height": DESK_H},
                            device_scale_factor=1)
    b617.open_desk(page)
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(300)
    before = page.evaluate(STATE)
    click_pose_and_maybe_key(page, press_key)
    if mode == "store":
        page.evaluate("() => window.__director_store.getState().selectObject(null)")
        page.wait_for_timeout(650)
    else:
        page.mouse.click(*BLANK_XY)
        page.wait_for_timeout(700)
    st = page.evaluate(STATE)
    r = scan(page, SCENE_SEL)
    page.close()
    return {"mode": mode, "pressKey": press_key, "before": before,
            "after": st, "scene": r}


def probe_blanks(browser) -> dict[str, Any]:
    """判据 1 用：把「空白」测出来。"""
    page = browser.new_page(viewport={"width": W, "height": DESK_H},
                            device_scale_factor=1)
    b617.open_desk(page)
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(300)
    pts = [[x, y] for y in (300, 500, 700, 900) for x in (200, 400, 640, 800, 950)]
    geom = page.evaluate(PROBE_BLANKS, pts)
    truly_blank: list[list[int]] = []
    picked_up: list[dict[str, Any]] = []
    for p in geom:
        x, y = p["x"], p["y"]
        page.mouse.click(x, y)
        page.wait_for_timeout(200)
        st = page.evaluate(STATE)
        if st["selected"] is None:
            truly_blank.append([x, y])
        elif p["onNode"]:
            picked_up.append({"xy": [x, y], "selected": st["selected"]})
    happy = page.evaluate(PROBE_BLANKS, [list(HAPPY_BLANK_XY)])[0]
    happy_state = None
    page.mouse.click(*HAPPY_BLANK_XY)
    page.wait_for_timeout(400)
    happy_state = page.evaluate(STATE)
    page.close()
    return {"probed": len(geom), "trulyBlank": truly_blank,
            "pickedUpANode": picked_up[:6],
            "blankXY": list(BLANK_XY), "blankIsTrulyBlank": list(BLANK_XY) in truly_blank,
            "happyBlankXY": list(HAPPY_BLANK_XY), "happyOnNode": happy["onNode"],
            "happyActuallySelected": happy_state["selected"],
            "happySceneRanges": happy_state["sceneRanges"]}


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


def main() -> int:
    v = Verifier()
    cases: list[dict[str, Any]] = []

    with sync_playwright() as p:
        br = p.chromium.launch()
        blanks = probe_blanks(br)
        cases.append(run_case(br, "click", False))   # 真人路径，不按键（对照）
        cases.append(run_case(br, "click", True))    # 真人路径，按键
        cases.append(run_case(br, "click", True))    # 重复
        cases.append(run_case(br, "store", True))    # 程序化路径，按键
        br.close()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    click_nokey = cases[0]["scene"]
    click_key = [c["scene"] for c in cases[1:3]]
    store_key = cases[3]["scene"]

    def val(d: dict[str, Any]) -> Any:
        return None if d.get("missing") else d["distinct"]

    # 1 空白是测出来的
    v.check("blank-space-is-measured-not-assumed",
            blanks["blankIsTrulyBlank"]
            and len(blanks["trulyBlank"]) >= 10
            and blanks["happySceneRanges"] == 0
            and blanks["happyActuallySelected"] is not None,
            detail={"trulyBlankCount": len(blanks["trulyBlank"]),
                    "trulyBlank": blanks["trulyBlank"][:14],
                    "theCoordinateIAssumedWasBlank": {
                        "xy": blanks["happyBlankXY"],
                        "actuallySelected": blanks["happyActuallySelected"],
                        "sceneRangesRendered": blanks["happySceneRanges"]},
                    "whyThisIsNotATrivialCheck":
                        "My first attempt clicked (640, 560) believing it was empty space. "
                        "It selected a prop table, so the right panel rendered the prop's "
                        "properties and the scene sliders were not in the DOM at all. The "
                        "reading was None -- neither 11 nor 1 -- and a None would have been "
                        "read as 'not reproduced', which is the wrong conclusion.",
                    "lesson":
                        "The same mistake as batch 695's wrong tab attribute: the path I "
                        "believed I was taking is not the path I was taking. Both times a "
                        "silent no-op masqueraded as a negative result."},
            note="assume nothing about where you are standing")

    # 2 真人路径不复现
    v.check("a-user-clicking-empty-space-does-not-hit-it",
            all(val(x) == 11 for x in [click_nokey] + click_key),
            detail={"control_noKey": val(click_nokey),
                    "afterEndKey_repeats": [val(x) for x in click_key],
                    "afterDeselectState": cases[1]["after"]},
            note="the user path is clean")

    # 3 程序化路径复现
    v.check("the-store-api-path-still-does",
            val(store_key) == 1,
            detail={"selectObject_null": val(store_key),
                    "batch696SaidThis": "696 measured exactly this and called the cause "
                                        "'unlocated'. 697 does not locate it either; it "
                                        "removes the possibility that anyone can reach it."},
            note="the two paths are not interchangeable")

    # 4 不等价
    v.check("the-programmatic-path-and-the-user-path-are-not-the-same-thing",
            val(store_key) == 1 and val(click_nokey) == 11,
            detail={"storeApi": val(store_key), "userClick": val(click_nokey),
                    "whatThisMeans":
                        "Calling selectObject(null) through the store bypasses whatever "
                        "the real interaction path does to reset the panel. Whatever 696 "
                        "measured is a property of HOW THE TEST DRIVES THE APP, not a "
                        "property of the app.",
                    "whatItDoesNotMean":
                        "It does not prove the app is correct. A user could still reach a "
                        "similar state by some other sequence that this batch did not try. "
                        "What it does mean is that the specific sequence 696 pinned is NOT "
                        "evidence of a user-visible defect, and batch 696's wording is "
                        "corrected here to say so without rewriting 696.",
                    "howToAvoidIt":
                        "Prefer driving the real control over the store whenever a store "
                        "call is standing in for something a user would click. When the "
                        "store is unavoidable, say so in the check's detail."},
            note="a store call standing in for a click is a claim, not a shortcut")

    out = {
        "width": W, "deskHeight": DESK_H,
        "cases": cases, "blanks": blanks,
        "theFinding":
            "Batch 696's dead-input condition reproduces through "
            "selectObject(null) and does NOT reproduce when a user clicks empty space. "
            "The two deselect paths are not equivalent, so 696's sequence is a property "
            "of the test harness rather than something a user can walk into.",
        "whatIsNotClaimed":
            "This falsifies reachability, not a mechanism. It also does not claim the user "
            "path is safe in every sequence -- only that this one sequence is clean.",
        "relationTo696":
            "696 already wrote 'not claimed to be a defect a user can hit'. This batch "
            "turns that sentence from a caveat into a measurement. 696 is not rewritten.",
        "storeWritesInThisRun": [
            "selectObject(null)  [in the programmatik case only]",
        ],
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
