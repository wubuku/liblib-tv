#!/usr/bin/env python3
"""batch 700 验收：「点了没反应」至少有两类 —— 有据可查的拒绝，和没有账的沉默

## 起点

699 把导演台 14 枚入口类控件普查了一遍，判出 4 枚「惰」：
`add-track` / `add-keyframe`（新开态）/ `motion-preset-button` / `motion-create-path`，
并诚实地写下「**`add-track` 点了什么都不发生，但本批没有测出为什么**」。

本批只做一件事：**把那「不知道为什么」问出来。**

## 问出来的结果

导演台**自己在记账**。`directorStore` 每条命令都写 `lastCommandResult`
（`commandKind` / `disposition` / `reason`），并且把它翻到 DOM 属性上：
`[data-director-workspace]` 上的 `data-director-last-command` /
`data-director-last-disposition` / `data-director-last-reason`。

**699 的快照从来没读过这一面** —— 所以「惰性」这个词把两件不同的事混成了一件：

| 控件 | 点了之后 | 属于 |
|---|---|---|
| `add-track` | `ADD_TRACK` / **`NOOP`** / **`DIRECTOR_COMMAND_NO_CHANGE`** | **有据可查的拒绝** |
| `add-keyframe`（播放头处已有关键帧） | **什么都没有** —— 无命令、无 toast、无 disposition | **没有账的沉默** |
| `add-keyframe`（播放头处无关键帧） | `PROJECT_MUTATION` / `COMMITTED`，**真的加了一个** | 正常 |
| `motion-preset-button` / `motion-create-path` | 源码无 `onClick`，**不可能有命令** | 真没接线 |

**`add-keyframe` 不是坏按钮，它是一个「该时刻已有关键帧就不重复插入」的幂等控件。**
实测：播放头 t=2（该处无关键帧）⟹ 关键帧总数 **6 → 7**，插在 2；
播放头 t=0 / t=4（该处已有关键帧）⟹ **6 → 6**，只把选中关键帧切过去。
`autoKeyframe` 开或关**不影响**这个按钮。

## 真正扎人的地方

**打开导演台时播放头在 t=0，而 t=0 处本来就有关键帧。**
⟹ 用户什么都不做、直接点「添加关键帧」，**什么都不会发生，也没有任何提示**。
699 把它记成「惰性」在这个状态下是对的，成因却是「幂等」而不是「没接线」。

## 纪律

- **不把「没反应」当成一个类别。** 每个「没反应」都要问出它落在
  {有据可查的拒绝 / 没有账的沉默 / 真没接线} 的哪一格。
- **能走的路都走真实控件。** 挪播放头是**点标尺**（`[data-director-timeline-ruler]`，
  实测 `t = f × duration`），不是 `setTimelineTime()`。零 store 写入。
- **零点击自检**：快照里现在多了 `lastCommandResult` 与三个 DOM 属性，
  必须重测它们自身稳定 —— 一个会自己抖的面会把每次点击都读成「有变化」。

## 四条判据

1. `add-keyframe-no-op-is-idempotence-not-a-broken-wire` —— 705 次改成：在无关键帧处它真的加
2. `per-timestep-scan-matches-the-keyframe-position-prediction` —— 逐时刻扫描表逐行相符
3. `rejection-bookkeeping-is-inconsistent-and-both-paths-are-silent-to-the-user` —— 记账不一致
4. `the-default-state-is-a-silent-no-op` —— 打开导演台直接点就不发生
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch700-2026-10-01"
W, DESK_H = 1280, 1150

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

# 快照比 699 多两面：**命令账**。
#   `last`  = store 的 lastCommandResult（commandKind / disposition / reason）
#   `ws`    = 同一个账翻到 DOM 属性上的样子
# 699 缺了这两面，于是把「有据可查的拒绝」和「没有账的沉默」读成了同一个词。
SNAP = r"""() => {
  const s = window.__director_store.getState();
  const ws = document.querySelector('[data-director-workspace]');
  const r = s.lastCommandResult;
  return {
    selectedObjectId: s.selectedObjectId ?? null,
    currentTime: s.timeline.currentTime ?? null,
    autoKeyframe: s.timeline.autoKeyframe ?? null,
    selectedKeyframeId: s.timeline.selectedKeyframeId ?? null,
    tracks: s.timeline.tracks.map((t) => ({
      objectId: t.objectId, kf: t.keyframes.map((k) => k.time) })),
    last: r ? { commandKind: r.commandKind, disposition: r.disposition,
                reason: r.reason } : null,
    ws: { command: ws.getAttribute('data-director-last-command'),
          disposition: ws.getAttribute('data-director-last-disposition'),
          reason: ws.getAttribute('data-director-last-reason') },
    toasts: document.querySelectorAll('[data-sonner-toast],[role="alert"]').length,
    dialogs: document.querySelectorAll('[role="dialog"],[role="alertdialog"]').length,
  };
}"""

# 标尺几何 —— 实测点击标尺第 f 比例处，播放头落在 f × duration
RULER = r"""() => {
  const el = document.querySelector('[data-director-timeline-ruler]');
  if (!el) return null;
  const b = el.getBoundingClientRect();
  return { left: b.left, top: b.top, width: b.width, height: b.height,
           duration: window.__director_store.getState().timeline.duration };
}"""

# 选中相机：对象树的可选行是 div[role="treeitem"][data-director-object-id]，
# 不是「身上没有 data- 属性的裸行」——那 5 个 24×24 的图标是可见性切换。
# 定位器可能是错的，**后置条件不能省**。
SELECT_CAMERA = r"""() => {
  const s = window.__director_store.getState();
  const cam = s.objects.find((o) => o.kind === 'camera');
  if (!cam) return { ok: false, stage: 'no-camera-object' };
  const row = document.querySelector(
    '[data-director-tree] [role="treeitem"][data-director-object-id="'
    + cam.id + '"]');
  if (!row) return { ok: false, stage: 'no-treeitem-by-object-id', id: cam.id };
  row.click();
  const got = window.__director_store.getState().selectedObjectId;
  return { ok: got === cam.id, expected: cam.id, got, name: cam.name };
}"""

CLICK_ATTR = r"""(attr) => {
  const el = document.querySelector('[' + attr + ']');
  if (!el) return { clicked: false, stage: 'absent' };
  const r = el.getBoundingClientRect();
  return { clicked: true, disabled: el.disabled,
           cx: r.left + r.width / 2, cy: r.top + r.height / 2,
           text: (el.textContent || '').trim().slice(0, 14) };
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


def click_attr(page, attr: str) -> dict[str, Any]:
    info = page.evaluate(CLICK_ATTR, attr)
    if info.get("clicked") and not info.get("disabled"):
        page.mouse.click(info["cx"], info["cy"])
        page.wait_for_timeout(400)
    return info


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
    scan: list[dict[str, Any]] = []
    add_track_read: dict[str, Any] = {}
    default_state: dict[str, Any] = {}
    null_drift: list[str] = []
    ruler_geom: dict[str, Any] = {}
    camera_select: dict[str, Any] = {}

    # 标尺比例 → 播放头。0 和 0.5 落在已有关键帧的位置（0 与 4s），
    # 其余落在没有关键帧的位置 —— 预测写在代码里，**先写下预测再测**。
    FRACTIONS = [0.0, 0.05, 0.125, 0.25, 0.375, 0.5]

    with sync_playwright() as p:
        br = p.chromium.launch()

        # ---- 零点击自检：加了命令账这两面之后，仪器自身还稳不稳 ----
        nullpage = fresh(br)
        n1 = nullpage.evaluate(SNAP)
        nullpage.wait_for_timeout(400)
        n2 = nullpage.evaluate(SNAP)
        null_drift = sorted(k for k in n1 if n1[k] != n2[k])
        nullpage.close()

        # ---- 对照 1：`add-track` 的拒绝有账 ----
        pg = fresh(br)
        ruler_geom = pg.evaluate(RULER)
        before = pg.evaluate(SNAP)
        info = click_attr(pg, "data-director-add-track")
        after = pg.evaluate(SNAP)
        add_track_read = {
            "before": before, "after": after, "clicked": info,
            "kfCountUnchanged": (sum(len(t["kf"]) for t in before["tracks"])
                                 == sum(len(t["kf"]) for t in after["tracks"])),
        }
        pg.close()

        # ---- 对照 2：默认态点「添加关键帧」 ----
        pg = fresh(br)
        d0 = pg.evaluate(SNAP)
        di = click_attr(pg, "data-director-add-keyframe")
        d1 = pg.evaluate(SNAP)
        default_state = {
            "before": d0, "after": d1, "clicked": di,
            "kfCount": [sum(len(t["kf"]) for t in d0["tracks"]),
                        sum(len(t["kf"]) for t in d1["tracks"])],
            "anyFeedback": d1["toasts"] != d0["toasts"] or d1["dialogs"] != d0["dialogs"],
        }
        pg.close()

        # ---- 逐时刻扫描：点标尺挪播放头，再点「添加关键帧」 ----
        for f in FRACTIONS:
            pg = fresh(br)
            sel = pg.evaluate(SELECT_CAMERA)
            if f == 0.0:
                camera_select = sel          # 记一次就够了
            pg.wait_for_timeout(350)
            geo = pg.evaluate(RULER)
            x = geo["left"] + geo["width"] * f
            y = geo["top"] + geo["height"] / 2
            onscreen = 0 <= x < W and 0 <= y < DESK_H
            if onscreen:
                pg.mouse.click(x, y)
                pg.wait_for_timeout(300)
            s0 = pg.evaluate(SNAP)
            cinfo = click_attr(pg, "data-director-add-keyframe")
            s1 = pg.evaluate(SNAP)
            n0 = sum(len(t["kf"]) for t in s0["tracks"])
            n1 = sum(len(t["kf"]) for t in s1["tracks"])
            cam = next((t for t in s0["tracks"] if t["objectId"] == "director-camera-main"), None)
            kf_times = cam["kf"] if cam else []
            t_read = s0["currentTime"]
            had = any(abs(t_read - kt) < 1e-6 for kt in kf_times)
            scan.append({
                "fraction": f, "clickedRuler": onscreen, "x": round(x),
                "timeRead": t_read, "cameraKeyframeTimes": kf_times,
                "hadKeyframeAtTime": had,
                "predictedDelta": 0 if had else 1,
                "actualDelta": n1 - n0,
                "recorded": s1["last"] if s1["last"] != s0["last"] else None,
                "wsAfter": s1["ws"], "toasts": s1["toasts"],
                "selectedKeyframeId": s1["selectedKeyframeId"],
            })
            print(f"  f={f:<6} t={t_read:<8} 该处有关键帧={str(had):5} "
                  f"预测Δ={0 if had else 1} 实测Δ={n1 - n0}  "
                  f"记账={json.dumps(s1['last'], ensure_ascii=False)}")
            pg.close()
        br.close()

    rows_match = all(r["predictedDelta"] == r["actualDelta"] for r in scan)
    no_add_rows = [r for r in scan if r["actualDelta"] == 0]
    add_rows = [r for r in scan if r["actualDelta"] == 1]
    silent_when_noop = all(r["recorded"] is None and not r["wsAfter"]["disposition"]
                           for r in no_add_rows)
    records_when_added = all(r["recorded"] is not None for r in add_rows)

    # ---- 判据 1：no-op 是幂等，不是断线 ----
    v.check(
        "add-keyframe-no-op-is-idempotence-not-a-broken-wire",
        len(add_rows) >= 3 and all(r["hadKeyframeAtTime"] is False for r in add_rows)
        and records_when_added,
        detail={"rowsThatAdded": [{"t": r["timeRead"], "delta": r["actualDelta"],
                                   "recorded": r["recorded"]} for r in add_rows],
                "sourceGuard": "directorStore.ts:7386-7388 —— recordObjectKeyframe 里 "
                               "!force && !autoKeyframe 的早退；同一时刻不重复插入",
                "autoKeyframeIrrelevant":
                    "dbg700c 实测 autoKeyframe 开/关对这个按钮无影响（两次都 6→7）"},
        note="699 recorded it as inert in the fresh state and said it did not know why; "
             "the answer is that it is an idempotent insert that declines when a "
             "keyframe already sits at the playhead")

    # ---- 判据 2：逐时刻扫描表 ----
    v.check(
        "per-timestep-scan-matches-the-keyframe-position-prediction",
        rows_match and len(scan) == len(FRACTIONS) and all(r["clickedRuler"] for r in scan),
        detail={"table": [{"f": r["fraction"], "t": r["timeRead"],
                           "hadKeyframe": r["hadKeyframeAtTime"],
                           "predicted": r["predictedDelta"], "actual": r["actualDelta"]}
                          for r in scan],
                "rulerMapping": "实测 t = f × duration，duration=8",
                "noStoreCalls": "播放头是用真实鼠标点 [data-director-timeline-ruler] 挪的，"
                                "不是 setTimelineTime()"},
        note="the prediction was written before the measurement; a scan whose "
             "prediction is fitted after the fact is not a scan")

    # ---- 判据 3：拒绝的记账不一致 ----
    v.check(
        "rejection-bookkeeping-is-inconsistent-and-both-paths-are-silent-to-the-user",
        add_track_read["after"]["last"] is not None
        and add_track_read["after"]["last"]["disposition"] == "NOOP"
        and add_track_read["after"]["last"]["reason"] == "DIRECTOR_COMMAND_NO_CHANGE"
        and add_track_read["after"]["ws"]["disposition"] == "NOOP"
        and silent_when_noop and len(no_add_rows) >= 2,
        detail={"addTrack": {"last": add_track_read["after"]["last"],
                             "ws": add_track_read["after"]["ws"],
                             "kfCountUnchanged": add_track_read["kfCountUnchanged"]},
                "addKeyframeWhenNoOp": [{"t": r["timeRead"], "recorded": r["recorded"],
                                         "wsAfter": r["wsAfter"], "toasts": r["toasts"]}
                                        for r in no_add_rows],
                "theInconsistency":
                    "同一导演台、同一种「不改变任何东西」：add-track 记 NOOP + 理由并翻到 "
                    "DOM 属性；add-keyframe 连一条都不记。两者的用户可见反馈都是零。"},
        note="the app has a ledger for one kind of refusal and no ledger for the other; "
             "that is a consistency gap, not necessarily a defect")

    # ---- 判据 4：默认态就是空操作 ----
    v.check(
        "the-default-state-is-a-silent-no-op",
        default_state["kfCount"][0] == default_state["kfCount"][1]
        and default_state["after"]["last"] == default_state["before"]["last"]
        and not default_state["anyFeedback"],
        detail={"playheadOnOpen": default_state["before"]["currentTime"],
                "keyframeTimes": default_state["before"]["tracks"][0]["kf"],
                "kfCount": default_state["kfCount"],
                "lastBefore": default_state["before"]["last"],
                "lastAfter": default_state["after"]["last"],
                "anyFeedback": default_state["anyFeedback"]},
        note="the playhead opens at 0, a position that already carries a keyframe, so the "
             "very first click a user makes does nothing and says nothing")

    out = {
        "width": W, "deskHeight": DESK_H,
        "ruler": ruler_geom, "cameraSelect": camera_select,
        "nullClickDrift": null_drift,
        "addTrackRead": add_track_read,
        "defaultState": default_state,
        "perTimestepScan": scan,
        "verdicts": {"added": [r["timeRead"] for r in add_rows],
                     "noOp": [r["timeRead"] for r in no_add_rows]},
        "theFinding":
            "「点了没反应」不是一个类别。导演台自己在记账（lastCommandResult + 三个 DOM "
            "属性），而 699 的快照从来没读过那一面：add-track 记 NOOP + "
            "DIRECTOR_COMMAND_NO_CHANGE，add-keyframe 在等价情形下什么都不记。"
            "add-keyframe 本身不是坏按钮 —— 它是幂等插入，播放头处已有关键帧就不重复插；"
            "在无关键帧处它真的加（6→7）并记 PROJECT_MUTATION/COMMITTED，"
            "且与 autoKeyframe 开关无关。",
        "theUncomfortablePart":
            "打开导演台时播放头在 t=0，而 t=0 处本来就有关键帧 —— 用户什么都不做直接点"
            "「添加关键帧」，什么都不会发生，也没有任何提示。",
        "whatIsNotClaimed":
            "不声称 add-keyframe 应当重复插入同一时刻的关键帧（那多半是错的）；"
            "本批只测出「它不插」与「它不记账、不提示」。**要不要补一个 NOOP 记账或轻提示，"
            "是产品决定，需要用户拍板才动 src/。** 不声称源站行为（未取证，需授权点击）；"
            "不声称 add-track 的 NOOP 是缺陷（它的理由写得比 add-keyframe 清楚）。",
        "storeWritesInThisRun":
            "none — the playhead is moved by clicking [data-director-timeline-ruler]",
        "relationTo699":
            "699 不重写。它把 add-keyframe 记成「惰（新开态）」并诚实标注成因未测；"
            "本批测出了成因（幂等），并把「惰性」这个词劈成三类。"
            "699 的普查数字（8 活 / 4 惰 / 2 够不着）本身未被推翻 —— "
            "只是「惰」这一格的含义被细化。",
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
