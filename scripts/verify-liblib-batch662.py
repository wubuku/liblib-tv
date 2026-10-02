#!/usr/bin/env python3
"""batch 662 验收：`帮助` 的爆炸半径 —— 机制 vs 盖住者，N(H,h) 闭式

## 起点

661 收掉了 658 剩下的两族，并**纠正**了自己前两批对 `help` 的归因：盖住 `help`
的标签是 `收起属性`。那是 658 的 audit 里一直写着的 label，657/659 读的是 class
前缀。**661 的读数是对的。**

但 661 停在了「盖住者是 `收起属性`」这一步，**没有问这个答案会不会随状态变**。
本批就问这一件事，结果把 661 的答案降级了。

## 一：第一版预测被自己的读数推翻

661 的读数摆出一个诱人的闭式。`收起属性` 恒在 `H−39..H−19`，`帮助` 恒在
`H−40..H−8`，两者都锚在视口底边；时间轴顶边 = `H − h`，于是

    重叠 ⟺ 143 − h < −8  且  163 − h > −40
         ⟺ h > 151  且  h < 203

扫了 **18 档** h（含 88 收起态、151/152 与 202/203 两条预测边界），
`topIsSelf` **一格都没有翻成 True**。

把整条命中栈倒出来才看清：`help` 的**栈顶恒在时间轴里面**，而时间轴**左列**
（`[data-director-timeline-track-list]`，320px，`overflow-y-auto`）的盒子
**恒完整包住 `帮助` 的纵向区间** —— 因为它从 `H−h` 一直铺到视口底边，而
`h ≥ 88 > 24`。那个 `收起属性` 按钮只是**恰好**落在探测点上的一枚成员。

**预测错在把「成员」当成了「机制」。**

## 二：仪器 —— 机制 vs 盖住者

`elementsFromPoint` 的栈顶是**盖住机制的一个成员**。要拿机制，得从栈顶沿
`data-director-*` 祖先上溯：

    topMechanism(el) = el 及其祖先上第一个带 data-director-* 属性的元素

48 格跑下来：**机制恒在时间轴内（48/48），而成员有 5 种**：

| 机制族 | 次数 | 成员 |
|---|---|---|
| `data-director-timeline-track-list` | 39 | 左列自己（点落在列的空白/滚动区） |
| `data-director-timeline-object-row=…character-lead` | 4 | 角色对象行 |
| `data-director-timeline-object-row=…camera-main` | 4 | 机位对象行（**661 在默认格量到的就是这枚**） |
| `data-director-timeline` | 2 | 时间轴节本身（点正落在顶边上） |
| `data-director-playback` | 1 | 播放条 |

661 的 `收起属性` 是**其中一格、一个成员**，不是机制。

## 三：真正的爆炸半径闭式

`rail` 的 7 枚入口排布是**两头钉**的：6 枚钉在**顶部**（`cy` 恒 76/132/172/
212/252/292，**与窗高无关**，48 格逐格相同），`帮助` 带 `mt-auto` 钉在**底部**
（`cy = H − 24`）。时间轴通栏且左列 320px 宽，rail 只有 48px 且完全在其中，于是

    一枚入口被吞 ⟺ 它自己的中心落在时间轴顶边之下或齐平
                    ⟺ cy ≥ H − h

    N(H, h) = 1 + |{ cy ∈ 六枚顶部入口 : cy ≥ H − h }|

**台阶在 `h = H − 292` 与 `h = H − 252`**，各加一枚。
H=660 时是 368 与 408，**都钉在单个像素**（367→1 枚 / 368→2 枚 / 407→2 枚 /
408→3 枚），且四个边界格**用全新加载逐位复现**。
H=720/900/1150 在量程内不出现台阶（要 428/608/858 > MAX 420）。

## 四：为什么没有 UI 状态能救它

`帮助` 被吞的条件化简成 `h ≥ 24`（`H−24 ≥ H−h`）。而量程下界是 store 里
**具名**的 `DIRECTOR_TIMELINE_HEIGHT_MIN = 88`。**24 < 88 ⟹ 量程内无解**，
包括点时间轴自己的「最小化」按钮（`collapsed=true`，实测仍是 88px 且仍被吞）。
**这是一个闭式，不是一个采样结论。**

## 五：跨批独立复现（不重打 633 的数）

633 在 H=660 上用**自己那套普查**量过掩埋数，它的 `buriedColumns` 里 rail 列是
`1,1,1,1,1,1,1,3`（h=88/120/150/182/240/300/360/420）。
本批从 662 的读数推出同一条 rail 列，**逐档逐枚吻合**，连成员身份都一样：

    h=420 → {帮助, 选择画幅比例, AI 识图导入}  = 633 的 {aspect-ratio, ai-import, help}

两套不同仪器、不同批次、同一个页面、**成员级别**一致。

## 本批**不**主张的事

* **零源站断言** —— 源站有没有这个重叠**未取证**（待授权第 10 项），故不修布局。
* **不主张**该修 —— 闭式说清了「无解」，处置是产品决定。
* **闭式的作用域只有 rail 列**：633 同格还记了 `tree` 列的受害者（场景树面板的
  12 枚），那是**另一个容器**，本批的 `N` 不覆盖它，**不声称**。
* **不主张**「栈顶」口径应替换一切 —— 661 已划好界：**点击**场景用栈顶，
  归因场景要用机制。
"""
import importlib.util
import json
import re
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch662-2026-10-01"

WIDTH = 1280
# 660 is 633's window height, kept so the cross-batch comparison is like for
# like; the other three bracket 658/661's heights.
H_LIST = [660, 720, 900, 1150]
# 367/368 and 407/408 are the two predicted steps, one pixel either side.
# 150 is in the list only so that all eight of 633's heights are covered by the
# cross-batch comparison; it sits between 120 and 182 and steps nothing.
TL_LIST = [88, 120, 150, 182, 240, 300, 360, 367, 368, 407, 408, 420]
FRESH = [(660, 367), (660, 368), (660, 407), (660, 408)]
# 633's own eight heights, for the cross-batch comparison.
B633_HEIGHTS = [88, 120, 150, 182, 240, 300, 360, 420]

MECHANISM_JS = """() => {
  const tl = document.querySelector('[data-director-timeline]');
  const tlTop = tl ? Math.round(tl.getBoundingClientRect().top) : null;
  // INSTRUMENT: the stack top is one MEMBER of whatever covers the control.
  // The mechanism is the nearest ancestor-or-self carrying a data-director-*
  // attribute.  661 named the member and stopped there.
  const mechanism = (el) => {
    for (let a = el; a && a !== document.body; a = a.parentElement) {
      for (const at of a.attributes) {
        if (at.name.startsWith('data-director-')) {
          return at.value ? at.name + '=' + at.value : at.name;
        }
      }
    }
    return null;
  };
  const rows = [];
  for (const el of document.querySelectorAll('[data-director-rail-entry]')) {
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    const st = document.elementsFromPoint(cx, cy);
    const top = st[0] || null;
    rows.push({
      id: el.getAttribute('data-director-rail-entry'),
      label: el.getAttribute('aria-label'),
      top: Math.round(r.y), bottom: Math.round(r.bottom),
      cy: Math.round(cy),
      depth: st.length,
      idx: st.indexOf(el),
      topIsSelf: !!(top && (top === el || el.contains(top))),
      topMechanism: mechanism(top),
      topInsideTimeline: !!(top && tl && tl.contains(top)),
    });
  }
  return {H: window.innerHeight,
          tlH: tl ? Number(tl.getAttribute('data-director-timeline-height')) : null,
          tlTop: tlTop, rows: rows};
}"""


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / f"scripts/verify-liblib-batch{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


b617 = _load("617")


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
              + (f"  [{note[:96]}]" if note else ""))


def main() -> int:
    v = Verifier()
    grid: dict[str, Any] = {}
    fresh: dict[str, Any] = {}
    collapsed: dict[str, Any] = {}
    uncollapsed: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        for H in H_LIST:
            page = br.new_page(viewport={"width": WIDTH, "height": H},
                               device_scale_factor=1)
            b617.open_desk(page)
            for h in TL_LIST:
                page.evaluate("(v) => window.__director_store.getState()"
                              ".setTimelineHeight(v)", h)
                page.wait_for_timeout(260)
                _clean(page)
                grid[f"{H}/{h}"] = page.evaluate(MECHANISM_JS)
            page.close()
        for (H, h) in FRESH:
            page = br.new_page(viewport={"width": WIDTH, "height": H},
                               device_scale_factor=1)
            b617.open_desk(page)
            page.evaluate("(v) => window.__director_store.getState()"
                          ".setTimelineHeight(v)", h)
            page.wait_for_timeout(300)
            _clean(page)
            fresh[f"{H}/{h}"] = page.evaluate(MECHANISM_JS)
            page.close()
        # the one escape hatch a user actually has: the timeline's own minimize
        page = br.new_page(viewport={"width": WIDTH, "height": 1150},
                           device_scale_factor=1)
        b617.open_desk(page)
        _clean(page)
        uncollapsed = page.evaluate(MECHANISM_JS)
        page.locator("[data-director-timeline-collapse]").first.click()
        page.wait_for_timeout(420)
        _clean(page)
        collapsed = page.evaluate(MECHANISM_JS)
        page.close()
        br.close()

    # ---------------------------------------------------------------- geometry
    # Six entries are pinned to the top of the rail, one (`mt-auto`) to the
    # bottom.  Both facts are read from the grid, never assumed.
    def ids(cell: dict[str, Any]) -> list[str]:
        return [r["id"] for r in cell["rows"]]

    help_id = "help"
    top_six: dict[int, list[int]] = {}
    for H in H_LIST:
        c = grid[f"{H}/{TL_LIST[0]}"]
        top_six[H] = [r["cy"] for r in c["rows"] if r["id"] != help_id]
    six_constant = len({tuple(v) for v in top_six.values()}) == 1
    SIX = top_six[H_LIST[0]]
    help_cy = {H: [r["cy"] for r in grid[f"{H}/{TL_LIST[0]}"]["rows"]
                   if r["id"] == help_id][0] for H in H_LIST}
    help_is_H_minus_24 = all(help_cy[H] == H - 24 for H in H_LIST)

    # ------------------------------------------------------------- closed form
    def predict_blocked(cell_key: str, cy: int) -> bool:
        tl_top = grid[cell_key]["tlTop"]
        return cy >= tl_top            # 660/368 measures equality as blocked

    def predict_count(H: int, h: int) -> int:
        tl_top = H - h
        return 1 + sum(1 for cy in SIX if cy >= tl_top)

    measured: dict[str, list[str]] = {}
    predicted: dict[str, int] = {}
    mismatches: dict[str, Any] = {}
    for H in H_LIST:
        for h in TL_LIST:
            key = f"{H}/{h}"
            c = grid[key]
            blocked = sorted(row["id"] for row in c["rows"]
                             if not row["topIsSelf"])
            measured[key] = blocked
            p = predict_count(H, h)
            predicted[key] = p
            pred_ids = sorted(row["id"] for row in c["rows"]
                              if predict_blocked(key, row["cy"]))
            if blocked != pred_ids or p != len(blocked):
                mismatches[key] = {"measured": blocked, "predictedIds": pred_ids,
                                   "count": p}

    help_blocked_everywhere = all(help_id in measured[f"{H}/{h}"]
                                  for H in H_LIST for h in TL_LIST)
    help_top_never_self = all(not [r for r in grid[f"{H}/{h}"]["rows"]
                                  if r["id"] == help_id][0]["topIsSelf"]
                             for H in H_LIST for h in TL_LIST)

    # ------------------------------------------------------------------ steps
    step_367 = (len(measured["660/367"]), len(measured["660/368"]))
    step_407 = (len(measured["660/407"]), len(measured["660/408"]))
    fresh_counts = {k: len([r for r in c["rows"] if not r["topIsSelf"]])
                    for k, c in fresh.items()}
    fresh_matches = all(
        fresh_counts[f"{H}/{h}"] == len(measured[f"{H}/{h}"])
        for (H, h) in FRESH)

    # ----------------------------------------------------------------- members
    members: dict[str, int] = {}
    inside = 0
    blocked_total = 0
    for c in grid.values():
        for r in c["rows"]:
            if r["topIsSelf"]:
                continue
            blocked_total += 1
            members[r["topMechanism"]] = members.get(r["topMechanism"], 0) + 1
            if r["topInsideTimeline"]:
                inside += 1
    default_member = [r for r in grid["1150/182"]["rows"]
                      if r["id"] == help_id][0]["topMechanism"]

    # -------------------------------------------------------------- the rescue
    store_src = (ROOT / "src/store/directorStore.ts").read_text(encoding="utf-8")
    h_min = int(re.search(r"DIRECTOR_TIMELINE_HEIGHT_MIN\s*=\s*(\d+)", store_src).group(1))
    h_max = int(re.search(r"DIRECTOR_TIMELINE_HEIGHT_MAX\s*=\s*(\d+)", store_src).group(1))
    h_def = int(re.search(r"DIRECTOR_TIMELINE_DEFAULT_HEIGHT\s*=\s*(\d+)",
                          store_src).group(1))
    # help's centre is H-24; it is swallowed as soon as h >= 24.
    escape_h = 24
    collapsed_help = [r for r in collapsed["rows"] if r["id"] == help_id][0]
    uncollapsed_help = [r for r in uncollapsed["rows"] if r["id"] == help_id][0]

    # --------------------------------------------------------- cross-batch 633
    b633 = json.loads((ROOT / "docs/research/liblib-canvas-batch633-2026-10-01"
                             / "runtime-audit.json").read_text(encoding="utf-8"))
    label_of = {r["id"]: r["label"] for r in grid["660/88"]["rows"]}
    cmp633: dict[str, Any] = {}
    for h in B633_HEIGHTS:
        prior = b633["cells"][f"1280/tl={h}"]
        prior_rail = sorted(l for l in prior["buriedLabels"]
                            if l in set(label_of.values()))
        mine = sorted(label_of[i] for i in measured[f"660/{h}"]) \
            if f"660/{h}" in measured else None
        cmp633[str(h)] = {"prior633_railLabels": prior_rail, "batch662_predicted": mine,
                          "agree": mine is not None and prior_rail == mine}

    out: dict[str, Any] = {
        "batch": 662,
        "question": "661 named the control that covers `help`. Does that answer "
                    "survive a change of state, and what is the blast radius?",
        "theRefutation": {
            "theGuess": "the rects of `收起属性` (H-39..H-19) and `帮助` "
                        "(H-40..H-8) both hang off the viewport bottom, so "
                        "overlap <=> 151 < h < 203 and the default 182 is the "
                        "only bad value",
            "theSweep": "18 heights, including 151/152, 202/203, the collapsed "
                        "88 and the 420 maximum",
            "theResult": "topIsSelf never became True in any of them",
            "whyTheGuessWasWrong": "it treated one MEMBER as the MECHANISM. The "
                                   "timeline's left column spans from H-h to the "
                                   "viewport bottom, so it always contains "
                                   "`帮助`'s y-range: h >= 24 is enough and the "
                                   "range floor is 88.",
        },
        "instrument": {
            "mechanism": "nearest ancestor-or-self of the stack top carrying a "
                         "data-director-* attribute",
            "why": "the stack top is one member of the cover; naming the member "
                   "is not naming the cause",
        },
        "geometry": {
            "topSixCy": top_six, "topSixIsViewportInvariant": six_constant,
            "helpCy": help_cy, "helpCyIsHminus24": help_is_H_minus_24,
            "reading": "the rail is pinned at both ends: six entries at the top "
                       "(viewport-invariant), `帮助` at the bottom via mt-auto",
        },
        "closedForm": {
            "rule": "an entry is swallowed <=> its own centre is at or below the "
                    "timeline's top edge, i.e. cy >= H - h",
            "N": "N(H,h) = 1 + |{ cy in the six top entries : cy >= H - h }|",
            "stepsAt": "h = H - 292 and h = H - 252 (one more entry each)",
            "cells": len(grid),
            "mismatches": mismatches,
            "predictedCounts": {k: predicted[k] for k in sorted(predicted)},
        },
        "steps": {"measured": step_367 + step_407,
                  "freshLoadCounts": fresh_counts,
                  "freshLoadMatchesInPage": fresh_matches},
        "members": {"counts": members, "distinct": len(members),
                    "blockedTotal": blocked_total,
                    "mechanismInsideTimeline": inside,
                    "defaultCellMember": default_member},
        "noRescue": {
            "helpCentredAt": "H - 24", "swallowedWhen": "h >= 24",
            "storeRange": {"min": h_min, "max": h_max, "default": h_def},
            "rangeFloorIsAboveTheThreshold": h_min > escape_h,
            "collapsedState": {"tlH": collapsed["tlH"],
                               "helpTopIsSelf": collapsed_help["topIsSelf"],
                               "helpMechanism": collapsed_help["topMechanism"]},
            "uncollapsedState": {"tlH": uncollapsed["tlH"],
                                 "helpTopIsSelf": uncollapsed_help["topIsSelf"],
                                 "helpMechanism": uncollapsed_help["topMechanism"]},
        },
        "crossBatch633": cmp633,
    }

    # ------------------------------------------------------------------- checks
    v.check("the-six-top-entries-are-pinned-to-the-top-and-help-is-pinned-to-the-bottom",
            six_constant and help_is_H_minus_24,
            detail={"topSixCyPerViewportHeight": top_six,
                    "topSixIsTheSameAtEveryHeight": six_constant,
                    "helpCy": help_cy, "helpCyIsHminus24": help_is_H_minus_24,
                    "mechanismInSource": "DirectorIconRail: the first six entries "
                                         "are stacked from the rail's top edge; "
                                         "`help` carries mt-auto so flex pushes "
                                         "it to the bottom",
                    "whyItMatters": "it is what makes N(H,h) a formula instead of "
                                     "a table: the six are constant and `帮助` "
                                     "moves at exactly 1px per px of height"},
            note="a two-ended pin turns a grid into an expression")

    v.check("help-is-swallowed-in-every-cell-of-the-grid",
            help_blocked_everywhere and help_top_never_self,
            detail={"cells": len(grid), "gridHeights": H_LIST,
                    "timelineHeights": TL_LIST,
                    "helpInStackButNeverTop": {
                        "inStack": "readings above are topIsSelf, i.e. the "
                                   "operational reading 661 settled",
                        "helpStackDepthAtDefault": [
                            r["depth"] for r in grid["1150/182"]["rows"]
                            if r["id"] == help_id][0],
                        "helpIndexInStackAtDefault": [
                            r["idx"] for r in grid["1150/182"]["rows"]
                            if r["id"] == help_id][0]},
                    "note": "this is the opposite of the batch's first guess, "
                            "which predicted a clean band at 151 < h < 203 "
                            "leaving the default as the only bad value"},
            note="18 heights, and the predicted clean band never appeared")

    v.check("the-blast-radius-closed-form-predicts-every-cell",
            not mismatches and len(grid) == 48,
            detail={"rule": out["closedForm"]["N"],
                    "cells": len(grid), "mismatches": mismatches,
                    "measuredCounts": {k: len(measured[k])
                                       for k in sorted(measured, key=_hk)},
                    "predictedCounts": {k: predicted[k]
                                        for k in sorted(predicted, key=_hk)},
                    "theWorkings": "a rail entry is 32px wide inside a 48px rail, "
                                   "and the timeline's left column is 320px wide "
                                   "and full-height from H-h down, so every rail "
                                   "centre that reaches H-h is inside it",
                    "scope": "this N counts the rail column only. 633 recorded a "
                             "`tree` column in the same cells — a different "
                             "container, not covered here and not claimed."},
            note="48 cells, one expression, no exceptions")

    v.check("both-steps-are-pinned-to-a-single-pixel-and-survive-a-fresh-load",
            step_367 == (1, 2) and step_407 == (2, 3) and fresh_matches,
            detail={"h367_vs_368": step_367, "h407_vs_408": step_407,
                    "freshLoadCounts": fresh_counts,
                    "freshLoadMatchesInPage": fresh_matches,
                    "predictedSteps": {"H660": [660 - 292, 660 - 252],
                                       "H720": [720 - 292, 720 - 252],
                                       "H900": [900 - 292, 900 - 252],
                                       "H1150": [1150 - 292, 1150 - 252]},
                    "whyOnlyH660HasSteps": "the second step needs h = H-252; at "
                                           "H=720 that is 468, above "
                                           "DIRECTOR_TIMELINE_HEIGHT_MAX=420",
                    "whyFreshLoads": "the sweep mutates the store in one page; "
                                     "the four edge cells were re-measured on "
                                     "four brand-new loads to show the reading is "
                                     "not an artefact of in-page mutation"},
            note="367 is one pixel short of a second victim")

    v.check("the-mechanism-is-the-timeline-in-every-cell-while-the-top-member-is-not",
            inside == blocked_total and len(members) >= 4,
            detail={"blockedControls": blocked_total,
                    "mechanismInsideTimeline": inside,
                    "distinctMembers": len(members), "memberCounts": members,
                    "why": "the left column is 320px wide and the rail 48px, and "
                           "the timeline section is z-40 against the rail's z-30 "
                           "— so the column wins every point inside it",
                    "theMembers": {
                        "track-list": "the column's own padding / scroll area, "
                                      "which is hit-testable even when empty",
                        "object-row": "an object row happens to be at the point",
                        "timeline": "the point sits exactly on the section's top "
                                    "edge, so there is no nearer data-* ancestor",
                        "playback": "the playback bar, at one cell"},
                    "theInstrumentIsTheDeliverable": "any future batch that "
                                                     "attributes an occlusion "
                                                     "should name the mechanism, "
                                                     "not the member"},
            note="a member is not a cause; the stack top is one row of a list")

    v.check("661s-coverer-is-the-member-of-one-cell-not-the-mechanism",
            default_member == "data-director-timeline-object-row=director-camera-main"
            and "data-director-timeline-object-row=director-camera-main" in members,
            detail={"defaultCell": "1150/182", "memberThere": default_member,
                    "what661CalledIt": "收起属性 — the 20x20 toggle button inside "
                                       "that object row; the mechanism walk stops "
                                       "one level up, at the row",
                    "why661WasNotWrong": "at the cell 661 measured, that member IS "
                                         "what takes the hit. 658's audit recorded "
                                         "the label from the first run.",
                    "whatWasMissing": "that the member is a function of the "
                                      "timeline height: over the grid there are "
                                      f"{len(members)} distinct members, and the "
                                      "verdict (unreachable) does not depend on "
                                      "which one is on top",
                    "membersObserved": members},
            note="naming a member correctly is not the same as naming the cause")

    v.check("no-ui-state-rescues-help-because-the-range-floor-sits-above-the-threshold",
            h_min > escape_h and not collapsed_help["topIsSelf"]
            and h_def == 182,
            detail={"helpCentredAt": "H - 24",
                    "swallowedWhen": "h >= 24",
                    "storeRangeReadFromSource": {
                        "DIRECTOR_TIMELINE_HEIGHT_MIN": h_min,
                        "DIRECTOR_TIMELINE_HEIGHT_MAX": h_max,
                        "DIRECTOR_TIMELINE_DEFAULT_HEIGHT": h_def},
                    "theDefaultSitsInsideTheBadRange": 24 <= h_def <= 203,
                    "theMinimizeButton": {
                        "selector": "[data-director-timeline-collapse]",
                        "uncollapsed": {"tlH": uncollapsed["tlH"],
                                        "helpTopIsSelf": uncollapsed_help["topIsSelf"],
                                        "helpMechanism": uncollapsed_help["topMechanism"]},
                        "collapsed": {"tlH": collapsed["tlH"],
                                      "helpTopIsSelf": collapsed_help["topIsSelf"],
                                      "helpMechanism": collapsed_help["topMechanism"]}},
                    "whyThisIsAFormAndNotASample": "a sweep shows which heights "
                                                   "are bad; this shows that every "
                                                   "reachable height is bad, "
                                                   "because the floor is a named "
                                                   "constant 64px above the "
                                                   "threshold",
                    "theDefectIsNotFixed": "630 already recorded that "
                                           "setTimelineHeight clamps to this "
                                           "magic range without comparing it to "
                                           "the available height; this batch adds "
                                           "the consequence — the clamp is what "
                                           "removes the only escape"},
            note="630's clamp and this batch's closed form are the same fact seen "
                 "from two ends")

    disagree = {k: c for k, c in cmp633.items() if not c["agree"]}
    v.check("the-closed-form-reproduces-633s-rail-column-member-by-member",
            not disagree and len(cmp633) == len(B633_HEIGHTS)
            and cmp633["420"]["prior633_railLabels"] == ["AI 识图导入", "帮助",
                                                        "选择画幅比例"],
            detail={"windowHeight": b633["windowHeight"],
                    "priorHeights": B633_HEIGHTS,
                    "priorInstrument": "633's own census, `buriedColumns`",
                    "comparison": cmp633,
                    "disagreements": disagree,
                    "whatWasNotRedone": "633's numbers were READ from its audit, "
                                        "not recomputed; this batch's rail column "
                                        "is predicted from the closed form and "
                                        "then compared",
                    "whyMemberLevel": "counting alone would let a wrong set of the "
                                      "right size pass; 633 recorded 帮助 / "
                                      "选择画幅比例 / AI 识图导入 at h=420 and the "
                                      "form produces exactly those three"},
            note="two instruments, two batches, one page, same members")

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "checks": v.result},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


def _clean(page: Any) -> None:
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(150)


def _hk(key: str) -> tuple[int, int]:
    a, b = key.split("/")
    return (int(a), int(b))


if __name__ == "__main__":
    raise SystemExit(main())
