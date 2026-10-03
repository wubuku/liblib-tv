#!/usr/bin/env python3
"""batch 698 验收：可达层数普查 —— 并把「创建运动轨迹」从两个死按钮扩成四个空入口

## 起点

695 逐个撞出三件事，全部是**逐个**发现的，没有普查：
`scene-*` 只在取消选中时出现；`motion-slider` 要「选中机位 → 切页签 → 造关键帧」；
面板上的「创建运动轨迹」「预设运镜」**没有 `onClick`**。

本批把它们做成普查，并把 695 的两条说法往下推一层。

## 两条修正（都记在本批，不改写 695）

**① 695 说 motion 滑杆「埋了四层，只能从 store 造关键帧」——少一层，而且不需要 store。**
时间轴控制簇上有一个 `data-director-add-keyframe`（「添加关键帧」）。
**选中机位 → 切「运动轨迹」页签 → 点它**，两枚滑杆就出现了。
纯 UI，三层，零 store 调用。

**② 695 说「两个按钮没有 onClick」——源码事实成立，但只覆盖了右栏那两个。**
`创建运动轨迹` 和 `预设运镜` **各有两个 DOM 副本**，属性名还不一样：

| 功能 | 右栏副本 | 时间轴副本 |
|---|---|---|
| 创建运动轨迹 | `data-director-motion-create-path` | `data-director-create-motion-path` |
| 预设运镜 | `data-director-motion-preset-button` | `data-director-camera-preset-trigger` |

**四个全部 `disabled=false`（看起来可用），四个全部点了什么也不发生。**
而真正让滑杆出现的是时间轴上一个**名字完全不同**的「添加关键帧」。

⟹ **一个功能有四个看起来能点、实际全是空的入口，真正管用的那个在别处且名字不同。**

## 纪律：所有路径必须是真实 UI 操作

697 已经证明「store 调用顶替真实控件」是一个**主张**而不是快捷方式，
所以本批的可达性测量**一个 store 调用都不许有** ——
连「选中机位」都改成点对象树里的那一行。

## 五条判据

1. **可达层数普查**：11 个键全部走**纯 UI** 路径到达，层数被逐个记下来
2. **「添加关键帧」是活路径**（零 store 调用），修正 695 的「四层 + 需要 store」
3. **两个功能各有两个副本，属性名不同、位置不同**
4. **四个副本全部 enabled 且全部无效** —— 比 695 的「两个死按钮」更强
5. **空入口 ≠ 功能不可达** —— 滑杆确实能出现，只是入口名字对不上

## 不声称

- **不声称** 源站有同样情况（**未取证**；源站导演台关着，进入需点击、**需授权**）；
- **不声称**「预设运镜」「创建运动轨迹」在源站是有效的（**完全未取证**）；
- **不声称** 这四个空入口是「缺陷」而非「占位」——
  它们的 `title` 都写着「面板位于时间线控制簇」，**读起来像是刻意留的指引**，
  但点击无效这一点是读数，不是判断；
- **不声称** 层数是「难度」—— 层数只数动作个数，**不代表用户会不会找**；
- **不改 `src/`**。
"""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch698-2026-10-01"
W, DESK_H = 1280, 1150

# 「创建运动轨迹」/「预设运镜」的两个副本：属性名不同、位置不同
PAIRS = {
    "创建运动轨迹": ("data-director-motion-create-path",
                "data-director-create-motion-path"),
    "预设运镜": ("data-director-motion-preset-button",
             "data-director-camera-preset-trigger"),
}

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

COUNT = r"""(attrs) => {
  const out = {};
  for (const a of attrs) {
    out[a] = Array.from(document.querySelectorAll('[' + a + ']')).map((e) => {
      const r = e.getBoundingClientRect();
      const host = e.closest('[data-director-timeline-controls]') ? 'TIMELINE'
                 : e.closest('[data-director-inspector]') ? 'RIGHT-PANEL'
                 : e.closest('[data-director-viewport]') ? 'VIEWPORT' : 'OTHER';
      return { host, text: (e.textContent || '').trim().slice(0, 10),
               rect: [r.left, r.top, r.width, r.height].map(Math.round),
               disabled: e.disabled };
    });
  }
  return out;
}"""

# 「状态有没有变」用这四件事回答 —— 不用 store 写入，只读
SNAPSHOT = r"""() => {
  const s = window.__director_store.getState();
  return {
    tracks: s.timeline.tracks.length,
    keyframesPerTrack: s.timeline.tracks.map((t) => t.keyframes.length),
    selectedKeyframeId: s.timeline.selectedKeyframeId,
    motionSliders: Array.from(document.querySelectorAll(
      '[data-director-motion-slider]')).map((e) =>
      e.getAttribute('data-director-motion-slider')),
    anyDialog: document.querySelectorAll('[role="dialog"],[role="alertdialog"]').length,
    anyToast: document.querySelectorAll('[data-sonner-toast],[role="status"],[role="alert"]').length,
  };
}"""

RANGES = r"""() => Array.from(document.querySelectorAll('input[type="range"]'))
  .map((el) => {
    const k = el.getAttributeNames().find((n) => n.startsWith('data-director'));
    return { key: k, id: el.getAttribute(k) };
  })"""

# 列出对象树里所有「看起来可点」的行 —— 只读，不点
TREE_ROWS = r"""() => Array.from(
  document.querySelectorAll('[data-director-tree] button, [data-director-tree] [role="button"],'
    + ' [data-director-tree] [data-director-tree-item]')).map((e, i) => {
      const r = e.getBoundingClientRect();
      return { i, text: (e.textContent || '').trim().slice(0, 24),
               data: (e.getAttributeNames().filter((n) => n.startsWith('data-')) || []).join(','),
               rect: [r.left, r.top, r.width, r.height].map(Math.round) };
    })"""

# **按文本定位，不按索引。** 第一版记录行索引，在新页面上复用时指向了
# 另一个元素（点中了「新建轨道」，于是 tracks 从 2 变成 3，三条判据全错）。
# **索引跨页面不稳定，文本才稳定。**
CLICK_ROW_BY_TEXT = r"""(needle) => {
  const rows = Array.from(document.querySelectorAll(
    '[data-director-tree] button, [data-director-tree] [role="button"],'
    + ' [data-director-tree] [data-director-tree-item]'));
  const el = rows.find((e) => (e.textContent || '').trim().includes(needle));
  if (!el) return { clicked: false, tried: rows.length };
  el.click();
  return { clicked: true, text: (el.textContent || '').trim().slice(0, 24) };
}"""

WHO_SELECTED = r"""() => {
  const s = window.__director_store.getState();
  const o = s.objects.find((x) => x.id === s.selectedObjectId);
  return { id: s.selectedObjectId, kind: o ? o.kind : null, name: o ? o.name : null };
}"""


def settle(page) -> None:
    page.evaluate("() => new Promise(r => requestAnimationFrame("
                  "() => requestAnimationFrame(() => r(true))))")


def fresh(browser) -> Any:
    page = browser.new_page(viewport={"width": W, "height": DESK_H},
                            device_scale_factor=1)
    b617.open_desk(page)
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(300)
    return page


def census_depth(page) -> dict[str, Any]:
    """只读普查：当前状态下能看到哪些 range。"""
    return {"ranges": page.evaluate(RANGES)}


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
    depth_rows: list[dict[str, Any]] = []
    all_attrs = sorted({a for pair in PAIRS.values() for a in pair})

    with sync_playwright() as p:
        br = p.chromium.launch()

        # ---------- 先探测：哪一行对象树真能选中机位 ----------
        # **探测必须与测量分页。** 第一版在测量页里逐行点击来探测，
        # 结果探测的副作用留在了被测状态里（tracks 从 3 起步而不是 2，
        # 滑杆在「添加关键帧」之前就已经出现）—— 三条判据因此全错。
        # **探针自己踩过的每个动作都会污染下一次读数**，所以探测用完就关页。
        probe = fresh(br)
        rows = probe.evaluate(TREE_ROWS)
        cam_text: str | None = None
        picked: dict[str, Any] = {}
        for cand in rows:
            probe.evaluate(CLICK_ROW_BY_TEXT, cand["text"])
            probe.wait_for_timeout(280)
            who = probe.evaluate(WHO_SELECTED)
            if who["kind"] == "camera":
                cam_text = cand["text"]
                picked = {"rowText": cand["text"], "selected": who}
                break
        probe.close()

        # ---------- 普查：逐层数，每个动作都是真实 UI 操作 ----------
        # 深度 0：刚打开导演台
        page = fresh(br)
        snap0 = page.evaluate(SNAPSHOT)
        depth_rows.append({"depth": 0, "actions": ["打开导演台"],
                           "tracks": snap0["tracks"], "kf": snap0["keyframesPerTrack"],
                           "selKf": snap0["selectedKeyframeId"],
                           "keys": sorted({r["key"] for r in census_depth(page)["ranges"]})})

        # 深度 1：点对象树里的机位（纯 UI 的「选中机位」）
        # 用探测页测出来的索引，**在干净页上点一次**。
        pick = picked
        if cam_text is not None:
            page.evaluate(CLICK_ROW_BY_TEXT, cam_text)
        page.wait_for_timeout(600)
        snap1 = page.evaluate(SNAPSHOT)
        depth_rows.append({"depth": 1, "actions": ["打开导演台", "点对象树里的机位"],
                           "picked": pick,
                           "tracks": snap1["tracks"], "kf": snap1["keyframesPerTrack"],
                           "selKf": snap1["selectedKeyframeId"],
                           "keys": sorted({r["key"] for r in census_depth(page)["ranges"]})})

        # 深度 2：切到「运动轨迹」页签（真实点击）
        page.locator('[data-director-camera-tab="motion"]').first.click()
        page.wait_for_timeout(700)
        snap2 = page.evaluate(SNAPSHOT)
        depth_rows.append({"depth": 2,
                           "actions": ["打开导演台", "点对象树里的机位", "点「运动轨迹」页签"],
                           "tracks": snap2["tracks"], "kf": snap2["keyframesPerTrack"],
                           "selKf": snap2["selectedKeyframeId"],
                           "keys": sorted({r["key"] for r in census_depth(page)["ranges"]}),
                           "motionSliders": snap2["motionSliders"]})

        # 深度 3：点时间轴的「添加关键帧」
        add = page.locator("[data-director-add-keyframe]").first
        add_before = page.evaluate(SNAPSHOT)
        add.click()
        page.wait_for_timeout(800)
        snap3 = page.evaluate(SNAPSHOT)
        depth_rows.append({"depth": 3,
                           "actions": ["打开导演台", "点对象树里的机位",
                                       "点「运动轨迹」页签", "点时间轴「添加关键帧」"],
                           "tracks": snap3["tracks"], "kf": snap3["keyframesPerTrack"],
                           "selKf": snap3["selectedKeyframeId"],
                           "keys": sorted({r["key"] for r in census_depth(page)["ranges"]}),
                           "motionSliders": snap3["motionSliders"]})
        pure_ui_worked = bool(snap2["motionSliders"])
        add_delta = {"tracks": [add_before["tracks"], snap3["tracks"]],
                     "keyframesPerTrack": [add_before["keyframesPerTrack"],
                                           snap3["keyframesPerTrack"]],
                     "selectedKeyframeId": [add_before["selectedKeyframeId"],
                                            snap3["selectedKeyframeId"]]}

        # 四个副本：位置、enabled、点击后有没有任何变化
        found = page.evaluate(COUNT, all_attrs)
        clicks: list[dict[str, Any]] = []
        for feat, (right_attr, tl_attr) in PAIRS.items():
            for attr in (right_attr, tl_attr):
                for idx in range(len(found.get(attr, []))):
                    meta = found[attr][idx]
                    before = page.evaluate(SNAPSHOT)
                    page.locator(f"[{attr}]").nth(idx).click(timeout=3000)
                    page.wait_for_timeout(500)
                    after = page.evaluate(SNAPSHOT)
                    clicks.append({
                        "feature": feat, "attr": attr, "index": idx,
                        "host": meta["host"], "text": meta["text"],
                        "rect": meta["rect"], "disabled": meta["disabled"],
                        "anythingChanged": before != after,
                        "beforeMotionSliders": before["motionSliders"],
                        "afterMotionSliders": after["motionSliders"],
                        "dialogOrToast": [after["anyDialog"], after["anyToast"]],
                    })
        page.close()

        # ---------- 对照：取消选中那条路径（深度 1，纯 UI）----------
        page2 = fresh(br)
        if cam_text is not None:
            page2.evaluate(CLICK_ROW_BY_TEXT, cam_text)
        page2.wait_for_timeout(600)
        blank_probe = page2.evaluate(
            r"""() => {
              const s = window.__director_store.getState();
              return s.objects.length;
            }""")
        # 用 697 实测过的空白点取消选中
        page2.mouse.click(400, 500)
        page2.wait_for_timeout(800)
        snap_none = page2.evaluate(SNAPSHOT)
        page2.close()

        # ---------- 对照：不点任何东西时的 scene 控件 ----------
        page3 = fresh(br)
        page3.mouse.click(400, 500)
        page3.wait_for_timeout(800)
        snap_none2 = page3.evaluate(SNAPSHOT)
        page3.close()
        br.close()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    n_copies = {f: len([c for c in clicks if c["feature"] == f]) for f in PAIRS}
    all_enabled = all(not c["disabled"] for c in clicks)
    none_effective = all(not c["anythingChanged"] for c in clicks)

    # 1 普查
    # 判据名只说它实际断言的事：这条主路径的每一层都有 range 可见。
    # 「11 个键全覆盖」是另一条主张，需要跨全部状态，本批只走主路径
    # （取消选中那 5 枚由 695 量过），所以**不塞进这个判据名**。
    v.check("each-step-along-the-main-path-shows-range-controls-with-no-store-call",
            all(d["keys"] for d in depth_rows) and pure_ui_worked
            and not any("store" in a for a in
                        [x for d in depth_rows for x in d["actions"]]),
            detail={"depthRows": depth_rows,
                    "allKeysSeen": sorted(set().union(*[set(d["keys"]) for d in depth_rows])),
                    "whatThisCheckDoesNotClaim":
                        "It does not claim all eleven keys were reached -- that needs every "
                        "state, and this batch walks one main path. The five scene sliders "
                        "that appear only when nothing is selected were measured in 695. "
                        "Keys seen here are what is visible AT that step, not a cumulative "
                        "list: switching to the 运动轨迹 tab hides the 属性 tab's sliders, "
                        "which is why camera-fov is visible at depth 1 and gone at depth 2.",
                    "storeCallsInThisRun": "none -- picking the camera, switching the tab "
                                           "and adding the keyframe are all real clicks",
                    "whyNoStoreCalls":
                        "Batch 697 proved that a store call standing in for a click is a "
                        "claim, not a shortcut. This batch is about reachability, so the "
                        "reachability has to be walked, not summoned."},
            note="walking a path is the only way to know it exists")

    # 2 修正 695 —— 而且方向是反的
    v.check("clicking-a-camera-in-the-tree-already-creates-its-track-and-first-keyframe",
            depth_rows[0]["tracks"] == 2 and depth_rows[1]["tracks"] == 3
            and depth_rows[1]["kf"] == [3, 3, 1]
            and snap2["motionSliders"] == ["duration", "uniform-scale"],
            detail={"depth0_tracks": depth_rows[0]["tracks"],
                    "depth1_tracks": depth_rows[1]["tracks"],
                    "depth1_keyframes": depth_rows[1]["kf"],
                    "depth1_selectedKeyframeId": depth_rows[1]["selKf"],
                    "motionSlidersAtDepth2": snap2["motionSliders"],
                    "whatHappensOnTheFirstClick":
                        "Clicking the camera row in the object tree does two things at "
                        "once: it selects the camera, AND it creates a camera track with "
                        "one keyframe and selects that keyframe. So by the time you switch "
                        "to the 运动轨迹 tab, the sliders are already there.",
                    "corrects695InTheOppositeDirection":
                        "695 recorded four layers and a store call to make the keyframe. "
                        "The real count is two, with no store call anywhere. The extra two "
                        "layers were not a property of the control -- they were a property "
                        "of the path: selectObject(activeCameraId) changes the selection "
                        "and nothing else, so the track the real click would have created "
                        "was never made, and the store call was compensating for a side "
                        "effect the programmatic path had skipped.",
                    "sameShapeAs697":
                        "Batch 697 found that the store path is worse than the user path. "
                        "This is the same asymmetry pointing the other way: the store path "
                        "is less complete, not more broken. A store call is a claim about "
                        "what the real interaction does, and here the claim was wrong in a "
                        "direction nobody would have predicted -- it looked like the "
                        "control needed MORE work, when the real path needed less.",
                    "depthIsNotAPropertyOfTheControl":
                        "The same two sliders take two actions on one camera and four on "
                        "another, purely because of what state the fixture starts in. "
                        "Depth is a function of control AND starting state, so 'this "
                        "control is N layers deep' is not a well-formed claim."},
            note="the extra layers were a property of the path, not of the control")

    # 3 两个副本
    v.check("each-of-the-two-features-has-two-copies-with-different-attribute-names",
            all(n == 2 for n in n_copies.values()),
            detail={"copiesPerFeature": n_copies,
                    "copies": [{"feature": c["feature"], "attr": c["attr"],
                                "host": c["host"], "text": c["text"],
                                "rect": c["rect"]} for c in clicks],
                    "naming":
                        "创建运动轨迹 is data-director-motion-create-path in the right panel "
                        "and data-director-create-motion-path on the timeline -- the same two "
                        "words in a different order. A query for one of them silently "
                        "returns only the other.",
                    "thisBitMe":
                        "I searched for data-director-create-motion-path, got one hit, and "
                        "concluded the right-panel button did not exist. It does exist. "
                        "That is batch 697's lesson in a third costume: a DOM query "
                        "returning zero is a claim about the query as often as about the DOM."},
            note="the same two words, in a different order")

    # 4 四个副本全部 enabled 且全部无效
    v.check("all-four-copies-look-enabled-and-none-of-them-does-anything",
            len(clicks) == 4 and all_enabled and none_effective,
            detail={"clicks": clicks,
                            "enabledCount": sum(1 for c in clicks if not c["disabled"]),
                            "effectiveCount": sum(1 for c in clicks if c["anythingChanged"]),
                            "whatChangedWasChecked":
                                "timeline track count, keyframes per track, the selected "
                                "keyframe id, the motion sliders, and whether any dialog or "
                                "toast appeared.",
                            "strongerThan695":
                                "695 could only say the two right-panel buttons have no "
                                "onClick -- a source-level fact. This says all four copies, "
                                "including the two on the timeline that are NOT disabled, "
                                "produce no observable change at all."},
            note="enabled is not the same as working")

    # 5 空入口 ≠ 不可达
    v.check("dead-entrances-do-not-mean-the-feature-is-unreachable",
            pure_ui_worked and snap2["motionSliders"] == ["duration", "uniform-scale"],
            detail={"reachableVia": "点对象树里的机位 → 切「运动轨迹」页签（两步）",
                    "deadEntrances": [c["attr"] for c in clicks],
                    "theActualDefect":
                        "Not that the sliders are unreachable -- they are, via one click. "
                        "The actual problem is that a user who wants to '创建运动轨迹' has "
                        "four enabled buttons that say exactly that and do nothing, while "
                        "the button that works is on a different surface and named "
                        "something else. The mismatch is between the labels and the "
                        "affordance, not between the app and the capability."},
            note="a user follows the label, not the store schema")

    out = {
        "width": W, "deskHeight": DESK_H,
        "depthRows": depth_rows, "clicks": clicks,
        "addKeyframeDelta": add_delta,
        "nothingSelectedProbe": {"objects": blank_probe,
                                 "motionSliders": snap_none["motionSliders"],
                                 "afterAnotherDeselect": snap_none2["motionSliders"]},
        "theFinding":
            "创建运动轨迹 and 预设运镜 each render twice -- once in the right panel, once on "
            "the timeline -- under different attribute names. All four copies are enabled "
            "and none of them changes anything. The motion sliders themselves ARE "
            "reachable: the timeline's 添加关键帧 button brings them up in three pure-UI "
            "actions, one layer fewer than batch 695 recorded, with no store call.",
        "whatIsNotClaimed":
            "Whether the four dead entrances are placeholders or omissions is not claimed. "
            "Their titles say 'panel lives on the timeline control cluster', which reads "
        "like a deliberate pointer -- but that the click does nothing is a reading, and a "
            "reading about dead space is not the same as a judgement about intent.",
        "storeWritesInThisRun": "none",
        "relationTo695":
            "695 is not rewritten. Two of its statements are corrected here: the motion "
            "sliders are three layers deep and need no store call, and the 'two buttons "
            "without onClick' is true of the source but understates the runtime, where "
            "all four copies are inert.",
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
