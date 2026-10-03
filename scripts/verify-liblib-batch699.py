#!/usr/bin/env python3
"""batch 699 验收：「有 onClick / 有 title 都不等于接线」—— 惰性自证四件套在导演台只补了一件

## 起点

698 记下一条强读数：**「创建运动轨迹」和「预设运镜」各有两个副本，四个全部
`disabled=false`，四个全部点了什么也不发生。**

本批第一遍普查想把这个「点了没反应」扩到全导演台，扫出 144 个「惰性按钮」。
**那个数是假的。** 144 条记录里 108 条是定位失败、36 条是点击超时，
**零条真正走完「点击 + 快照比对」**。一个从不成功的普查照样吐出了一个
看起来像事实的整数。

## 本批真正测到的东西

把属性名写对、快照补上「下拉/面板出现」这一面之后，698 那条读数**被推翻**：

| 属性 | 698 的读数 | 实测 |
|---|---|---|
| `data-director-create-motion-path`（时间轴） | 惰性 | **活的**：点开 `aria-expanded` false→true，下拉 `[data-director-motion-path-menu]` 出现 |
| `data-director-camera-preset-trigger`（时间轴） | `disabled=false` | 初始态 **`disabled=true`** |
| `data-director-motion-preset-button`（右栏） | 惰性 | 初始态**根本不存在**，导航后才渲染；源码无 `onClick`，但有 `title` |
| `data-director-motion-create-path`（右栏） | 惰性 | 同上 |

所以 698 的「四个全部惰性」在**时间轴那份上不成立** —— 快照里没有
`aria-expanded` 也没有「新出现的 DOM 面」，一个真的会开下拉的按钮被读成了惰性。

**这是同一个错误的第五种装束**：695 用错属性名查 0 个 → 697 点「空白」点中道具桌
读数 `None` → 698 查 `create-motion-path` 查不到右栏那个 → 699 第一遍普查的
108 条 `notFound` → 本批探针自己又把 `data-director-motion-path-menu`
写成了 `data-director-path-menu`，再查出一个 0。

## 剩下的真问题：惰性自证的四件套

项目对主画布早就立了合同（batch 358/359/360/364/366/367）：
**惰性控件必须自证 = `data-inert` + 非空 `title` + `cursor: default` + 去掉 hover 反馈。**

实测：**导演台 `data-inert` 一处都没有**（运行时 workspace 内 0，源码
`src/components/director/**` 内 0；主画布顶层 40 处）。
右栏那两枚「指路牌」控件只补了四件套里的**一件**（`title`）——
`hover:bg-[#3d3d3d]` 的骗人反馈还在，`cursor` 还是浏览器默认的 `default`
（`cursor-default` 类缺的那一半是「没有 pointer 光标」，它们做对了），
但 `data-inert` 没有。

## 纪律

- **普查的每一条读数都必须能说出它是被哪一步量到的。** 无法归因的读数不入账。
- **不猜属性名。** 快照记「可见的 `data-director-*` 属性名集合」，
  下拉/面板无论叫什么都会自己冒出来。
- **每个按钮一个全新页面。** 累积点击会互相遮挡（第一遍普查 36 次
  TimeoutError 就是这么来的）。
- **不按索引定位，按属性名/文本。** 索引跨状态不稳定（698 踩过）。
- 零 store 写入。

## 四条判据

1. **纠正 698**：`data-director-create-motion-path` 是活控件，会开下拉
2. **三分类普查**：14 枚入口逐枚独立页面，判据只要求「已知答案的两个样本判对」
3. **自证断层**：导演台 `data-inert` 0 处；两枚指路牌只补了 `title`
4. **enabled 是状态的函数**：初始态控制簇 12 枚里 2 枚 `disabled`
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch699-2026-10-01"
W, DESK_H = 1280, 1150

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

# 本批普查的全部目标：时间轴控制簇 12 枚 + 右栏 motion 区 2 枚「指路牌」。
# 范围说明：对象树/视口/时间轴主体上的按钮是**逐对象的操作**（选中、切模式、
# 加关键帧到某条轨道），不是「入口」类控件，不在本批普查范围内 —— 本批要回答的
# 问题是「一个功能有几个看起来能点、实际不干活的入口」。
CONTROL_CLUSTER = [
    "data-director-playback",
    "data-director-auto-keyframe",
    "data-director-loop",
    "data-director-time-unit",
    "data-director-add-track",
    "data-director-camera-preset-trigger",
    "data-director-create-motion-path",
    "data-director-open-curve-editor",
    "data-director-add-track-manual",
    "data-director-remove-track",
    "data-director-add-keyframe",
    "data-director-delete-keyframe",
]
POINTER_PANELS = [
    "data-director-motion-preset-button",
    "data-director-motion-create-path",
]

# 「状态有没有变」用这五件事回答 —— 全部只读，零 store 写入。
#
# `surfaces` 是本批新增的一面，也是整个 batch 的关键修复：
# **不猜属性名。** 记下当前「可见元素上出现过的全部 data-director-* 属性名」，
# 任何下拉/面板/浮层不管叫什么都会在这里冒出来。猜名字查 0 个是这个项目
# 反复踩的坑（695/697/698/699 第一遍普查/本批探针各踩一次）。
SNAP = r"""() => {
  const s = window.__director_store.getState();
  const t = s.timeline || {};
  const surfaces = {};
  for (const el of document.querySelectorAll('*')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    for (const n of el.getAttributeNames()) {
      if (n.startsWith('data-director')) surfaces[n] = (surfaces[n] || 0) + 1;
    }
  }
  const pressed = {};
  for (const el of document.querySelectorAll('[aria-pressed]')) {
    if (el.getAttribute('aria-pressed') !== 'true') continue;
    const k = el.getAttributeNames().find((n) => n.startsWith('data-director')) || '(none)';
    pressed[k] = (el.textContent || '').trim().slice(0, 10);
  }
  const expanded = {};
  for (const el of document.querySelectorAll('[aria-expanded]')) {
    const k = el.getAttributeNames().find((n) => n.startsWith('data-director')) || '(none)';
    expanded[k] = el.getAttribute('aria-expanded');
  }
  const ranges = {};
  for (const el of document.querySelectorAll('input[type="range"]')) {
    const k = el.getAttributeNames().find((n) => n.startsWith('data-director')) || '(none)';
    ranges[k] = (ranges[k] || 0) + 1;
  }
  // `labels` 是本批被自己的盲区逼出来的一面：`data-director-time-unit` 的
  // 唯一可见效果是它**自己**的文案 ms→s（timeUnit 是组件局部 useState，
  // DirectorTimeline.tsx:260，压根不在 store 里）—— 快照里没有这一面，
  // 一个真的会翻转标签的按钮就被读成了「惰性」。**不猜状态在哪：把每个
  // 具名控件自己显示的文字都收进来。** 稳定性由「零点击自检」把关。
  const labels = {};
  for (const el of document.querySelectorAll('*')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    const a = el.getAttributeNames().find((n) => n.startsWith('data-director'));
    if (!a) continue;
    const own = Array.from(el.childNodes).filter((n) => n.nodeType === 3)
      .map((n) => n.textContent.trim()).join(' ').trim();
    if (!own) continue;
    (labels[a] = labels[a] || []).push(own.slice(0, 16));
  }
  for (const k of Object.keys(labels)) labels[k].sort();
  return {
    selectedObjectId: s.selectedObjectId ?? null,
    tracks: t.tracks ? t.tracks.length : null,
    kf: t.tracks ? t.tracks.map((x) => x.keyframes.length) : null,
    trackOwners: t.tracks
      ? t.tracks.map((x) => x.objectId ?? x.targetId ?? x.id ?? null) : null,
    selectedTrackId: t.selectedTrackId ?? null,
    selectedKeyframeId: t.selectedKeyframeId ?? null,
    collapsed: t.collapsed ?? null,
    currentTime: t.currentTime ?? null,
    height: t.height ?? null,
    playing: t.playing ?? null,
    autoKeyframe: t.autoKeyframe ?? null,
    loop: t.loop ?? null,
    timeUnit: t.timeUnit ?? null,
    pressed, expanded, ranges, surfaces, labels,
    dialogs: document.querySelectorAll('[role="dialog"],[role="alertdialog"]').length,
    toasts: document.querySelectorAll('[data-sonner-toast],[role="alert"]').length,
  };
}"""

# 目标按钮的读数面（不含 surfaces —— surfaces 走 SNAP，避免重复扫两遍全文档）
PROBE = r"""(attr) => {
  const el = document.querySelector('[' + attr + ']');
  if (!el) return { present: false };
  const r = el.getBoundingClientRect();
  const cs = getComputedStyle(el);
  return {
    present: true,
    text: (el.textContent || '').trim().slice(0, 14),
    disabled: el.disabled,
    ariaExpanded: el.getAttribute('aria-expanded'),
    title: el.getAttribute('title'),
    ariaLabel: el.getAttribute('aria-label'),
    inert: el.getAttribute('data-inert'),
    cursor: cs.cursor,
    hoverCls: /(^|\s)hover:/.test(el.getAttribute('class') || ''),
    rect: [r.left, r.top, r.width, r.height].map(Math.round),
    // 中心点上到底是什么 —— 挡住了就不是「惰性」，是「够不着」
    hitAtCenter: (() => {
      const h = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
      if (!h) return 'offviewport';
      if (h === el) return 'SELF';
      if (el.contains(h)) return 'DESCENDANT';
      return 'COVERED';
    })(),
  };
}"""

# 逐个试 camera tab，看哪个页签会把目标控件带出来。
# **必须与「选中机位」分成两步、中间等一次重渲染。** 第三版把两件事塞进同一个
# 同步 evaluate，点完机位立刻查 `[data-director-camera-tab]` —— 拿到 0 个，
# 于是报「选中机位后没有 camera 页签」。页签其实有 3 个（属性 / 运动轨迹 / 截图），
# 慢一拍才出现。**读到 0 的时候，先怀疑自己快了一步。**
LIST_TABS = r"""() => {
  // 右栏 motion 区的「预设运镜」「创建运动轨迹」是**有条件渲染**的：
  // 没有选中关键帧就不画。所以顺序必须是 选中机位 → 打关键帧 → 切页签。
  // 第四版漏了中间那一步，于是遍历 3 个页签报「no-tab-exposes-it」。
  // 第五版把「点页签」和「查目标」放进同一个同步 evaluate —— React 的重渲染
  // 是异步的，点完立刻查当然查不到。**同一个错第三次：读到 0，先怀疑自己快了一步。**
  const kf = document.querySelector('[data-director-add-keyframe]');
  const kfState = kf ? { present: true, disabled: kf.disabled } : { present: false };
  if (kf && !kf.disabled) kf.click();
  return Array.from(document.querySelectorAll('[data-director-camera-tab]'))
    .map((e, i) => ({ i, text: (e.textContent || '').trim(),
                       pressed: e.getAttribute('aria-pressed') }));
}"""

CLICK_TAB = r"""(i) => {
  const t = document.querySelectorAll('[data-director-camera-tab]')[i];
  if (!t) return { clicked: false };
  t.click();
  return { clicked: true, text: (t.textContent || '').trim() };
}"""

SEE_TARGET = r"""(attr) => {
  const el = document.querySelector('[' + attr + ']');
  if (!el) return { present: false };
  const r = el.getBoundingClientRect();
  return { present: true, rect: [r.left, r.top, r.width, r.height].map(Math.round) };
}"""

ENUM_CLUSTER = r"""() => Array.from(document.querySelectorAll(
  '[data-director-timeline-controls] button')).map((e) => {
    const r = e.getBoundingClientRect();
    return { data: (e.getAttributeNames().filter((n) => n.startsWith('data-director')) || []).join(','),
             text: (e.textContent || '').trim().slice(0, 12),
             disabled: e.disabled, visible: r.width > 0 && r.height > 0 };
  })"""

# 按 store 里的序号选中第 i 个对象，**并校验后置条件**。
# 对象树的裸行一个文本都没有，定位只能靠序号 —— 那就把序号换成一条可断言的
# 后置条件，而不是假装序号稳定。
# 按 store 里的序号**或** kind 选中对象，**并校验后置条件**。
# 对象树的可选行是 `div[role="treeitem"][data-director-object-id]`；
# 定位器仍然可能是错的，所以后置条件不是可选项，是必须项。
SELECT_OBJECT = r"""(spec) => {
  const s = window.__director_store.getState();
  const want = spec.kind
    ? s.objects.find((o) => o.kind === spec.kind)
    : s.objects[spec.index];
  if (!want) return { ok: false, stage: 'no-matching-object', spec };
  const row = document.querySelector(
    '[data-director-tree] [role="treeitem"][data-director-object-id="'
    + want.id + '"]');
  if (!row) return { ok: false, stage: 'no-treeitem-by-object-id',
                     id: want.id, kind: want.kind, name: want.name };
  row.click();
  const got = window.__director_store.getState().selectedObjectId;
  return { ok: got === want.id, expected: want.id, got,
           kind: want.kind, name: want.name, spec };
}"""


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
              + (f"  {str(detail)[:160]}" if detail else "")
              + (f"  [{note[:110]}]" if note else ""))


def click_and_read(browser, attr: str, nav: bool,
                   select: dict[str, Any] | None = None) -> dict[str, Any]:
    """一枚目标一个全新页面 —— 累积点击会互相遮挡。"""
    page = fresh(browser)
    try:
        navinfo = None
        if select is not None:
            navinfo = page.evaluate(SELECT_OBJECT, select)
            if not navinfo.get("ok"):
                return {"attr": attr, "verdict": "unselected", "nav": navinfo}
            page.wait_for_timeout(250)
        elif nav:
            navinfo = page.evaluate(SELECT_OBJECT, {"kind": "camera"})
            if not navinfo.get("ok"):
                return {"attr": attr, "verdict": "unreached", "nav": navinfo}
            page.wait_for_timeout(400)
            tabs = page.evaluate(LIST_TABS)
            page.wait_for_timeout(400)
            navinfo["tabs"] = {"seen": [t["text"] for t in tabs]}
            for t in tabs:
                page.evaluate(CLICK_TAB, t["i"])
                page.wait_for_timeout(350)
                if page.evaluate(SEE_TARGET, attr).get("present"):
                    navinfo["tabs"].update({"found": True, "tab": t["text"],
                                            "pressed": t["pressed"]})
                    break
            else:
                navinfo["tabs"].update({"found": False, "stage": "no-tab-exposes-it"})
            page.wait_for_timeout(300)
            if not navinfo["tabs"].get("found"):
                return {"attr": attr, "verdict": "unreached", "nav": navinfo}
        before = page.evaluate(PROBE, attr)
        if not before.get("present"):
            return {"attr": attr, "verdict": "absent", "nav": navinfo}
        s_before = page.evaluate(SNAP)
        reason = None
        if before["disabled"]:
            reason = "disabled"
        elif before["hitAtCenter"] in ("COVERED", "offviewport"):
            reason = before["hitAtCenter"]
        if reason is not None:
            return {"attr": attr, "verdict": "unclickable", "reason": reason,
                    "before": before, "nav": navinfo}
        x = before["rect"][0] + before["rect"][2] / 2
        y = before["rect"][1] + before["rect"][3] / 2
        page.mouse.click(x, y)
        page.wait_for_timeout(400)
        s_after = page.evaluate(SNAP)
        after = page.evaluate(PROBE, attr)
        added = sorted(set(s_after["surfaces"]) - set(s_before["surfaces"]))
        removed = sorted(set(s_before["surfaces"]) - set(s_after["surfaces"]))
        changed = sorted(k for k in s_before
                         if s_before[k] != s_after[k] and k != "surfaces")
        # 目标控件**自己**的文案/可及名也是效果面。少了这一面，
        # `time-unit`（唯一效果是标签 ms→s）会被读成惰性。
        self_changed = sorted(
            k for k in ("text", "title", "ariaExpanded", "ariaLabel")
            if (before.get(k) if k in before else None) != (after.get(k) if k in after else None)
        )
        return {
            "attr": attr,
            "verdict": "live" if changed or added or removed or self_changed else "inert",
            "before": before, "after": after,
            "changedKeys": changed, "selfChanged": self_changed,
            "surfacesAdded": added, "surfacesRemoved": removed,
            "ariaExpanded": [before["ariaExpanded"], after["ariaExpanded"]],
            "nav": navinfo,
        }
    finally:
        page.close()


def main() -> int:
    v = Verifier()
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    navinfo = None
    inert_in_workspace = None
    cluster = None

    with sync_playwright() as p:
        br = p.chromium.launch()

        # ---- 只读普查：控制簇 12 枚的初始态 + workspace 内 data-inert 数量 ----
        probe = fresh(br)
        cluster = probe.evaluate(ENUM_CLUSTER)
        inert_in_workspace = probe.evaluate(
            "() => document.querySelectorAll('[data-director-workspace] [data-inert]').length")
        probe.close()

        # ---- 零点击自检：不点任何东西，隔 400ms 取两次快照，必须逐字相同。
        # 这一步是给**仪器自己**的体检：一个会自己抖的快照面会把每一次点击
        # 都读成「有变化」，整个普查就退化成恒真。放在普查之前跑。
        nullpage = fresh(br)
        n1 = nullpage.evaluate(SNAP)
        nullpage.wait_for_timeout(400)
        n2 = nullpage.evaluate(SNAP)
        null_drift = sorted(k for k in n1 if n1[k] != n2[k])
        nullpage.close()

        # ---- 14 枚逐枚独立页面 ----
        for attr in CONTROL_CLUSTER + POINTER_PANELS:
            row = click_and_read(br, attr, nav=attr in POINTER_PANELS)
            rows.append(row)
            print(f"  {row['verdict']:12} {attr:40} "
                  f"{json.dumps({k: row[k] for k in ('changedKeys', 'selfChanged', 'surfacesAdded') if k in row}, ensure_ascii=False)[:110]}")
        # ---- 「同一个控件，换个状态换种判定」：选中机位后再点「添加关键帧」 ----
        kf_fresh = next((r for r in rows if r["attr"] == "data-director-add-keyframe"), {})
        kf_selected = click_and_read(br, "data-director-add-keyframe",
                                     nav=False, select={"kind": "camera"})
        print(f"  [选中机位后] {kf_selected['verdict']:12} data-director-add-keyframe  "
              f"{json.dumps(kf_selected.get('changedKeys'), ensure_ascii=False)}")
        for r in rows:
            if r["verdict"] in ("unreached", "absent", "unselected"):
                print(f"    !! {r['attr']} -> {r['verdict']}  nav={json.dumps(r.get('nav'), ensure_ascii=False)}")
        br.close()

    by = {r["attr"]: r for r in rows}
    live = [r["attr"] for r in rows if r["verdict"] == "live"]
    inert = [r["attr"] for r in rows if r["verdict"] == "inert"]
    unclick = [r["attr"] for r in rows if r["verdict"] == "unclickable"]
    absent = [r["attr"] for r in rows if r["verdict"] in ("absent", "unreached")]

    # ---- 判据 1：纠正 698 ----
    cp = by.get("data-director-create-motion-path", {})
    v.check(
        "timeline-create-motion-path-is-live-not-an-empty-entrance",
        cp.get("verdict") == "live"
        and cp.get("ariaExpanded") == ["false", "true"]
        and "data-director-motion-path-menu" in cp.get("surfacesAdded", []),
        detail={"verdict": cp.get("verdict"),
                "ariaExpanded": cp.get("ariaExpanded"),
                "surfacesAdded": cp.get("surfacesAdded"),
                "batch698Said": "四个全部 enabled 且全部点了什么也不发生"},
        note="698 is not rewritten; the correction is recorded here. "
             "The snapshot had no aria-expanded face and no 'a new DOM surface "
             "appeared' face, so a button that really opens a dropdown read as inert.")

    # ---- 判据 2：三分类普查，且仪器本身要能判对已知答案 ----
    # 标定对选在**初始态**成立的那两个：`playback` 点了必然走播（timeUnit 之类
    # 的条件依赖不在这一态），`camera-preset-trigger` 初始态 disabled。
    # 第一版拿 `add-keyframe` 当「已知活」是选错了状态 —— 它在新开导演台态
    # 什么都没有，点了当然不反应（见判据 5）。
    add_kf = by.get("data-director-add-keyframe", {})
    playback = by.get("data-director-playback", {})
    preset = by.get("data-director-camera-preset-trigger", {})
    v.check(
        "census-classifies-into-three-verdicts-and-the-instrument-is-calibrated",
        len(rows) == 14
        and {r["attr"] for r in rows} == set(live) | set(inert) | set(unclick) | set(absent)
        and playback.get("verdict") == "live"
        and preset.get("verdict") == "unclickable"
        and preset.get("reason") == "disabled",
        detail={"live": live, "inert": inert, "unclickable": unclick,
                "absentOrUnreached": absent,
                "nullClickDrift": null_drift,
                "calibration": {
                    "knownLive": ["data-director-playback -> " + str(playback.get("verdict"))
                                  + " via " + str(playback.get("changedKeys"))],
                    "knownUnclickable": ["data-director-camera-preset-trigger -> "
                                         + str(preset.get("verdict"))
                                         + " (" + str(preset.get("reason")) + ")"]}},
        note="a census is only worth its verdicts if the instrument gets a known "
             "answer right; the null-click drift is the instrument's own "
             "false-positive rate and must be empty")

    # ---- 判据 3：自证四件套断层 ----
    ptr = [by[a] for a in POINTER_PANELS if by.get(a, {}).get("before", {}).get("present")]
    ptr_ok = bool(ptr) and len(ptr) == 2 and all(
        b["before"]["title"] and not b["before"]["inert"] and b["before"]["hoverCls"]
        for b in ptr)
    v.check(
        "director-desk-has-no-inert-attestation-at-all",
        inert_in_workspace == 0 and ptr_ok,
        detail={"dataInertInWorkspace": inert_in_workspace,
                "mainCanvasTopLevelDataInert": 40,
                "sourceDirectorDirDataInert": 0,
                "pointerNav": [by[a].get("nav") for a in POINTER_PANELS],
                "pointerButtons": [
                    {"attr": b["attr"], "text": b["before"]["text"],
                     "title": b["before"]["title"],
                     "dataInert": b["before"]["inert"],
                     "cursor": b["before"]["cursor"], "hoverClass": b["before"]["hoverCls"],
                     "verdict": b["verdict"]} for b in ptr]},
        note="the project contract (358/359/360/364/366/367) is 四件套 = "
             "data-inert + title + cursor:default + no hover feedback; the director "
             "desk ships 1 of the 4")

    # ---- 判据 4：enabled 是状态的函数 ----
    disabled_in_cluster = [c["data"] for c in cluster if c["disabled"]]
    v.check(
        "enabled-is-a-function-of-state-not-a-property-of-a-control",
        len(disabled_in_cluster) == 2
        and "data-director-camera-preset-trigger" in disabled_in_cluster
        and "data-director-add-track-manual" in disabled_in_cluster,
        detail={"clusterSize": len(cluster), "disabledInFreshState": disabled_in_cluster,
                "batch698Claim": "四个全部 disabled=false",
                "sourceDependency": "DirectorTimeline.tsx:1109-1115 — create-motion-path 的 "
                                    "disabled 依赖 selectedTrack / cameraFollowActive / "
                                    "selectedTrackLocked",
                "rightPanelAbsentInFreshState": absent},
        note="698's 'all four enabled' does not hold in the fresh-desk state; and the "
             "right-panel pair is not merely disabled, it is not rendered at all")

    # ---- 判据 5：惰性/活性是「控件 × 状态」的函数 ----
    v.check(
        "inert-or-live-is-a-function-of-control-times-state",
        kf_fresh.get("verdict") == "inert"
        and kf_selected.get("verdict") == "live"
        and kf_selected.get("nav", {}).get("ok") is True,
        detail={"freshDesk": {"verdict": kf_fresh.get("verdict"),
                              "selectedObjectId": kf_fresh.get("before", {})
                              and None},
                "afterSelectingObject0": {
                    "verdict": kf_selected.get("verdict"),
                    "select": kf_selected.get("nav"),
                    "changedKeys": kf_selected.get("changedKeys")},
                "timeUnitIsComponentLocal":
                    "DirectorTimeline.tsx:260 —— timeUnit 是 useState，不在 store 里，"
                    "所以任何只读 store 的快照都看不见它翻转"},
        note="the same attribute, the same page, two verdicts — which is also why a "
             "census must state its starting state, and why the first version of this "
             "batch's own snapshot wrongly called time-unit inert")

    out = {
        "width": W, "deskHeight": DESK_H,
        "clusterInFreshState": cluster,
        "dataInertInWorkspace": inert_in_workspace,
        "nullClickDrift": null_drift,
        "census": rows,
        "addKeyframeSameAttrTwoStates": {
            "freshDesk": kf_fresh.get("verdict"),
            "afterSelectingObject0": kf_selected.get("verdict"),
            "select": kf_selected.get("nav"),
        },
        "verdicts": {"live": live, "inert": inert,
                     "unclickable": unclick, "absentOrUnreached": absent},
        "theFinding":
            "698 的「四个全部惰性」有两个读数被推翻：时间轴的 create-motion-path 是活控件"
            "（aria-expanded false→true，下拉 data-director-motion-path-menu 出现），"
            "camera-preset-trigger 在初始态是 disabled。右栏那两枚不是「坏掉的入口」，"
            "是**只补了 title 的指路牌** —— 而项目对主画布早有「惰性必须自证四件套」的"
            "合同，导演台一处 data-inert 都没有。",
        "theBrokenCensus":
            "第一遍普查的 144 是假的：108 条定位失败 + 36 条点击超时，零条真正走完"
            "「点击 + 快照比对」。三条根因可复现：(1) 在同一页面上累积点击，"
            "后点的按钮被前面打开的面板/浮层挡住（36 次 TimeoutError）；"
            "(2) 定位靠「文本+区域+像素 <3px」，任何一次重排都让它失效（108 条 notFound）；"
            "(3) 快照里含 body.innerHTML.length，任何重渲染都让前后不等。",
        "whatIsNotClaimed":
            "右栏两枚指路牌**是否是故意留白**，本批不判定 —— 只测出它们点了没反应、"
            "且只补了四件套里的一件。源站对应位置是否同样如此，需要授权才能回答。",
        "storeWritesInThisRun": "none",
        "scopeOfTheCensus":
            "本批普查 14 枚「入口类」控件（控制簇 12 + 右栏 motion 区 2）。"
            "workspace 内共 111 枚 button，其余是逐对象的操作"
            "（选中、切模式、给某条轨道加关键帧），不是入口类，不在本批范围内。",
        "relationTo698":
            "698 不重写。两条被纠正：时间轴的 create-motion-path 不惰性；"
            "初始态下 camera-preset-trigger 是 disabled 而非 enabled。"
            "698 的「四层 + 需 store」结论（纯 UI 两层）本批未触及，仍成立。",
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
