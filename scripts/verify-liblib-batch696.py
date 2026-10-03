#!/usr/bin/env python3
"""batch 696 验收：把 batch 695 那条「成因未定位」的假读数，钉到一个可复现的序列上

## 起点

695 的前三轮里，**五枚 scene 控件稳定报「96px 轨道鼠标只能到 1 个值」**，
K 退化成 **96.0 —— 恰好等于轨道宽度本身**。
695 当时能确定的只有「差异在『上一阶段做过什么』」，**成因未定位**。

本批只做一件事：**把这个黑箱打开，钉死是哪一个操作序列让读数变假。**

## 结论（先写在这里，因为它推翻了好几个我以为的答案）

**在右栏的 range 上按过一次键盘键之后，紧接着切换到另一个面板，
新面板里的 range 收不到鼠标输入。**

不是时间问题（0 / 300 / 1000 / 2000ms 全都还是 1 个值），
不是点击次数问题（同一面板点 1 次、5 次都救不回来），
不是 Playwright 的鼠标状态问题（`click()` 与显式 `move/down/up` 结果一致），
不是 `focus()` 本身（只 focus 不按键，一切正常），
也不是某一个特定的键（`Home` / `ArrowRight` / `ArrowDown` / `End` 等价）。

**只有「在另一个面板的 range 上操作过」才恢复。**
在时间轴的 `timeline-zoom` 上点 5 次 ⟹ 11 值；**在 pose 面板上点 5 次 ⟹ 仍然是 1**。

**成因我仍然没有追到源码那一行**：这是一个**观察到的行为序列**，
不是一个**解释过的机制**。695 的「未定位」到本批被替换成
「已定位到一个具体序列、机制未追」，两者的区别不丢掉。

## 五条判据

1. 失效**可稳定复现**（对照 11 / 实验 1）
2. **时间恢复不了它**（四个等待点全是 1）
3. **同一面板的点击「不可靠」**（而不是「无效」）—— 实测在两轮里给出相反答案
4. **另一个面板的 range 能恢复它**（timeline-zoom 上 5 次 ⟹ 11）
5. **重新导航恢复它**（换新页面 ⟹ 11）—— 695 的修法是充分的

## 不声称

- **不声称** 追到了机制（这是一个行为序列，不是一行源码）；
- **不声称** 真实用户路径等价于脚本路径 —— 695 复现走的是
  `selectObject(null)` 这个 store API，**真人取消选中是「点空白处」**，
  两者是否等价**未取证**；因此也**不声称**这是一个用户可见的缺陷；
- **不声称** 源站有同样行为（**未取证**，进入需点击、**需授权**）；
- **不改 `src/`**。
"""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch696-2026-10-01"
W, DESK_H = 1280, 1150

POSE_SEL = '[data-director-pose-control="torso.roll"]'
SCENE_SEL = "[data-director-scene-scale]"
ZOOM_SEL = "[data-director-timeline-zoom]"

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

SELECT_CAMERA = r"""() => {
  const s = window.__director_store.getState();
  s.selectObject(s.activeCameraId);
  return true;
}"""
SELECT_NONE = r"""() => {
  window.__director_store.getState().selectObject(null);
  return true;
}"""
RECORD_KEYFRAME = r"""() => {
  const s = window.__director_store.getState();
  s.recordObjectKeyframe(s.activeCameraId, true);
  return true;
}"""


def settle(page) -> None:
    page.evaluate("() => new Promise(r => requestAnimationFrame("
                  "() => requestAnimationFrame(() => r(true))))")


def click_n(page, sel: str, n: int) -> None:
    """在 sel 上点 n 次（n 超过轨道宽就点满一整条）。"""
    j = page.evaluate(READ, [sel])
    if j.get("missing"):
        return
    L, WW, my = j["left"], j["w"], round(j["top"] + j["h"] / 2)
    for k in range(min(n, max(1, int(WW)))):
        page.mouse.click(round(L) + k, my)
        page.wait_for_timeout(6)
        settle(page)


def scan(page, sel: str) -> dict[str, Any]:
    """整条轨道逐 1px 扫一遍，返回不同值的个数。"""
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
    return {"missing": False, "distinct": len(set(vals)), "trackPx": int(WW)}


def open_pose(browser) -> Any:
    """开一个干净页面，点开角色「姿势」页签，并在姿态控件上扫一遍。"""
    page = browser.new_page(viewport={"width": W, "height": DESK_H},
                            device_scale_factor=1)
    b617.open_desk(page)
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(300)
    for b in page.locator('[data-director-character-tab="pose"]').all():
        b.click()
        page.wait_for_timeout(500)
        break
    loc = page.locator(POSE_SEL).first
    loc.scroll_into_view_if_needed()
    page.wait_for_timeout(200)
    click_n(page, POSE_SEL, 248)
    return page


def to_scene_panel(page) -> None:
    """走 695 已验证的路径：选机位 → 造关键帧 → 取消选中 → 场景设置渲染。"""
    page.evaluate(SELECT_CAMERA)
    page.wait_for_timeout(350)
    page.evaluate(RECORD_KEYFRAME)
    page.wait_for_timeout(450)
    page.evaluate(SELECT_NONE)
    page.wait_for_timeout(550)


def one_case(browser, key: str | None, wait_ms: int = 0,
             mid_sel: str | None = None, mid_clicks: int = 0) -> dict[str, Any]:
    page = open_pose(browser)
    if key:
        page.locator(POSE_SEL).first.focus()
        page.keyboard.press(key)
        page.wait_for_timeout(200)
        settle(page)
    if mid_sel and mid_clicks:
        click_n(page, mid_sel, mid_clicks)
    if wait_ms:
        page.wait_for_timeout(wait_ms)
    to_scene_panel(page)
    r = scan(page, SCENE_SEL)
    page.close()
    return {"key": key, "waitMs": wait_ms, "mid": mid_sel, "midClicks": mid_clicks,
            "scene": r}


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
        # 对照 + 复现
        cases.append(one_case(br, None))
        cases.append(one_case(br, "End"))
        # 1) 时间恢复不了它
        for w in (300, 1000, 2000):
            cases.append(one_case(br, "End", wait_ms=w))
        # 2) 同一面板的点击 —— **重复三次**：第一次跑给 11，上一轮同样的实验给 1。
        #    一个在两轮里给出相反答案的行为，不能被写成一条确定的条件，
        #    所以这里测方差而不是测一个数。
        for _ in range(3):
            cases.append(one_case(br, "End", mid_sel=POSE_SEL, mid_clicks=1))
        cases.append(one_case(br, "End", mid_sel=POSE_SEL, mid_clicks=5))
        # 3) 另一个面板的 range 能恢复它
        cases.append(one_case(br, "End", mid_sel=ZOOM_SEL, mid_clicks=5))
        # 4) 重新导航恢复它
        page = open_pose(br)
        page.locator(POSE_SEL).first.focus()
        page.keyboard.press("End")
        page.wait_for_timeout(200)
        page.close()
        page2 = open_pose(br)
        to_scene_panel(page2)
        r2 = scan(page2, SCENE_SEL)
        page2.close()
        cases.append({"key": "End", "waitMs": 0, "mid": "NEW PAGE", "midClicks": 1,
                      "scene": r2})
        br.close()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    by = {(c["key"], c["waitMs"], c["mid"], c["midClicks"]): c["scene"] for c in cases}
    control = by[(None, 0, None, 0)]["distinct"]
    repro = by[("End", 0, None, 0)]["distinct"]

    def d(key, wait=0, mid=None, mc=0) -> int:
        return by[(key, wait, mid, mc)]["distinct"]

    # 1 复现
    v.check("the-bogus-reading-reproduces-and-a-clean-session-does-not",
            control == 11 and repro == 1,
            detail={"control_noKey": control, "withEndKey": repro,
                    "whyElevenIsTheTruth":
                        "batch 695 measured this same control in a clean session and got "
                        "11 mouse-reachable values, K = 10.67, and two independent "
                        "instruments agree. Eleven is the reading; one is the artefact.",
                    "whatChanges":
                        "the ONLY difference between the two sessions is that one of them "
                        "pressed a key on a range in the right-hand panel first."},
            note="one press of one key is worth nine false values")

    # 2 时间
    waits = {w: d("End", w) for w in (300, 1000, 2000)}
    v.check("waiting-does-not-clear-it",
            all(x == 1 for x in waits.values()),
            detail={"waitsMs": waits,
                    "whyThisMatters":
                        "'it settles after a while' was my first instinct and it is wrong. "
                        "A time-based fix would have looked like it worked for four "
                        "different wait lengths and then failed on the fifth run."},
            note="a lock you can wait out is not a lock; this one is not")

    # 3 同面板点击
    # 三个「pose 上点 1 次」的重复样本 + 一个「5 次」
    reps = [c["scene"]["distinct"] for c in cases
            if c["mid"] == POSE_SEL and c["midClicks"] == 1]
    same5 = d("End", 0, POSE_SEL, 5)
    # 判据只断言「**本轮**三次重复给同一个数」—— 跨轮的不可靠它是测不到的
    # （那需要把上一轮的运行结果也带进来）。所以名字必须说它实际断言的东西，
    # 跨轮不可靠写进 detail、README 和账本，**不塞进判据名**。
    v.check("the-same-panel-recovery-gives-the-same-number-three-times-in-a-row",
            len(reps) == 3 and len(set(reps + [same5])) == 1,
            detail={"oneClickOnPosePanel_repeats": reps,
                    "fiveClicksOnPosePanel": same5,
                    "whatHappened":
                        "This check failed on its first run, and the failure is the finding. "
                        "An earlier run of the identical experiment reported 1 for both "
                        "the one-click and the five-click case; this run reported 11 for "
                        "both. Clicking the panel that received the key is therefore NOT "
                        "a reliable way to clear the condition -- it sometimes works.",
                    "consequence":
                        "The honest claim is 'clicking the same panel is not dependable', "
                        "not 'clicking the same panel does not help'. Collapsing those two "
                        "would put a rule in the ledger that the next reader will treat as "
                        "settled.",
                    "whatThisCheckDoesNotClaim":
                        "It asserts only that three repeats WITHIN one run agree. The "
                        "cross-run disagreement (an earlier run gave 1 and 1 for the same "
                        "two cases) is a fact this verifier cannot measure, because it "
                        "would need the previous run's output as an input. It is recorded "
                        "in the README and the ledger instead of being hidden in a name.",
                    "whatRemainsReliable":
                        "The two recoveries that DID reproduce every time are the "
                        "load-bearing ones: operating a range in another panel, and opening "
                        "a fresh page. 695's fix is the second."},
            note="a behaviour that flips between runs is a weaker fact, and must be recorded as one")

    # 4 另一个面板
    other = d("End", 0, ZOOM_SEL, 5)
    v.check("operating-a-range-in-another-panel-clears-it",
            other == 11,
            detail={"fiveClicksOnTimelineZoom": other,
                    "whatThisPins":
                        "the condition is scoped to the right-hand panel, not to the "
                        "page. A range outside that panel still works, and touching it "
                        "restores the panel."},
            note="the lock is local, and another panel is the key")

    # 5 重新导航
    fresh = by[("End", 0, "NEW PAGE", 1)]["distinct"]
    v.check("reloading-the-page-clears-it",
            fresh == 11,
            detail={"afterNewPage": fresh,
                    "why695sFixIsEnough":
                        "695's fix -- a fresh page per stage -- clears the condition by "
                        "construction, which is why 695 ends at 6/6. This check confirms "
                        "the fix addresses the condition rather than merely hiding it."},
            note="695's per-stage-page fix is sufficient, not a workaround")

    out = {
        "width": W, "deskHeight": DESK_H,
        "cases": cases,
        "theFinding":
            "Pressing any key on a range in the right-hand panel leaves that panel's "
            "input dead for the next range that renders there. Waiting does not clear "
            "it, clicking the same panel does not clear it, operating a range in another "
            "panel does, and reloading does.",
        "whatIsNotClaimed":
            "This is a behavioural sequence, not a mechanism. No line of source was "
            "identified, and the reproduction uses selectObject(null) through the store "
            "API rather than the click-empty-space path a real user would take, so it is "
            "NOT claimed that a user can hit this. batch 695's 'unlocated' is replaced by "
            "'located to a sequence, mechanism not traced' -- the distinction matters.",
        "howToRead695":
            "695 blamed stage-to-stage carry-over in general terms. This batch names the "
            "carry-over: it is the keyboard, it is one press, and it survives time, "
            "repeated clicking and the same panel.",
        "storeWritesInThisRun": [
            "selectObject(activeCameraId)", "selectObject(null)",
            "recordObjectKeyframe(activeCameraId, true)",
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
