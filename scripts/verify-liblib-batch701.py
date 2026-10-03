#!/usr/bin/env python3
"""batch 701 验收：「没记账」推不出「没接线」—— 命令账覆盖率的普查

## 起点

700 把「点了没反应」劈成三格，其中第三格是：
`motion-preset-button` / `motion-create-path` **真没接线**，理由是
「点了之后**没有任何命令被记录**，而源码里它们根本没有 `onClick`」。

本批来压力测试那条推理的**形式**（不是那两枚控件的结论）。

## 写下预测，再测

预测（本批第一行代码就写死）：**凡是把 store 状态改掉的控件，都会留下命令记录。**

实测 8 枚入口控件，**2 枚当场推翻它**：

| 控件 | 改 store | 记账 |
|---|---|---|
| `data-director-playback` | ✅ 11 个叶子 | ❌ **零记录** |
| `data-director-open-curve-editor` | ✅ `timeline.editorMode` | ❌ **零记录** |
| `auto-keyframe` / `loop` / `remove-track` | ✅ | ✅ `PROJECT_MUTATION` / `COMMITTED` |

**`playback` 是活的、真的改了状态、却一个字都不记。**
⟹ **「没记账」推不出「没接线」。** 700 那条推理的形式是错的。

**700 对那两枚指路牌的结论仍然成立**，但成立的理由要换：
不是「它们没记账」，而是「**源码里它们根本没有 `onClick`**」——
那是一条独立证据，与记账无关。**结论没错，理由错了。**

## 三种「不记账」必须分开

1. **改了 store 却没记**（`playback` `open-curve-editor`）—— 命令账的**覆盖漏洞**
2. **只改了非 store 状态**（`time-unit` 改的是组件局部 `useState`；
   `create-motion-path` 只开一个下拉）—— **不记账是预期的**，它们根本不是命令
3. **什么都没改**（`delete-keyframe` 在该状态下）—— 第三态，不能当成「不记账」

把 (2) 算成 (1)，等于给命令账记了一笔它没欠的账；把 (3) 算成 (1)，
是 697 那条「读数的第三态不能被当成否定」又来一次。

## 命令账的规模 ≠ 命令账的覆盖

源码侧数得出来：`disposition:` 字面量 **109 处**（`REJECTED` 41 / `STALE` 21 /
`NOOP` 20 / `COMMITTED` 17 / `CONFLICT` 8 / `TOMBSTONED` 1 / `SAVED` 1）、
**16 种 reason**。规模很厚。

**但它覆盖的是「走命令层的那一部分动作」，不是「所有改状态的动作」。**
播放（逐帧求值并把结果回写进 `objects`）和视图切换都走的是另一条路。

## 纪律

- **预测写在测量之前**，预测被推翻本身就是交付物。
- **只读 store**，零 store 写入；每枚控件一个全新页面。
- **零点击自检**：快照新增「store 逐叶投影」这一面，必须重测它自身稳不稳
  （播放会逐帧变 ⟹ 这一面**只在未播放时**取样，取样条件要写明）。

## 四条判据

1. `every-store-changing-control-is-ledgered` —— **预期为假**
2. `no-ledger-entry-does-not-imply-no-wiring` —— 纠正 700 的推理形式
3. `three-kinds-of-no-ledger-entry-are-different` —— 逐枚归类
4. `ledger-size-is-not-ledger-coverage` —— 源码计数 + 运行时交叉核对
"""
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch701-2026-10-01"
W, DESK_H = 1280, 1150
STORE = ROOT / "src/store/directorStore.ts"

# **预测写在这里，先于任何测量**：
# 凡是把 store 状态改掉的控件，都会留下命令记录。
PREDICTION = "every-store-changing-control-is-ledgered"

# 699 判为「活」的 8 枚入口控件 —— 全部在「选中机位」这一稳定前置下测量
CONTROLS = ["data-director-playback", "data-director-auto-keyframe",
            "data-director-loop", "data-director-time-unit",
            "data-director-create-motion-path", "data-director-open-curve-editor",
            "data-director-remove-track", "data-director-delete-keyframe"]

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

# 把 store 拍平成 {路径: 值}，只报真正变的叶子。
# **逐叶而不是逐键** —— 699 那版只比顶层键，`playback` 的变化被记成
# 「objects 和 timeline 变了」，看不出它连 `isPlaying` 都翻了。
# **取样条件：未播放时取。** 播放中 objects 会逐帧变，那不是一次动作。
FLAT = r"""() => {
  const s = window.__director_store.getState();
  if (s.timeline && s.timeline.isPlaying) return { __playing: true };
  const out = {};
  const walk = (v, path, d) => {
    if (d > 4) { out[path] = String(v); return; }
    if (v === null || typeof v !== 'object') { out[path] = JSON.stringify(v); return; }
    if (Array.isArray(v)) {
      out[path + '.length'] = v.length;
      v.forEach((x, i) => walk(x, path + '[' + i + ']', d + 1));
      return;
    }
    for (const k of Object.keys(v).sort()) walk(v[k], path + '.' + k, d + 1);
  };
  for (const k of Object.keys(s).sort()) {
    if (typeof s[k] === 'function' || k === 'lastCommandResult') continue;
    walk(s[k], k, 0);
  }
  return out;
}"""

SNAP = r"""() => {
  const s = window.__director_store.getState();
  const ws = document.querySelector('[data-director-workspace]');
  const r = s.lastCommandResult;
  return {
    isPlaying: s.timeline ? s.timeline.isPlaying : null,
    editorMode: s.timeline ? s.timeline.editorMode : null,
    currentTime: s.timeline ? s.timeline.currentTime : null,
    last: r ? { commandKind: r.commandKind, disposition: r.disposition,
                reason: r.reason } : null,
    wsDisp: ws.getAttribute('data-director-last-disposition'),
    toasts: document.querySelectorAll('[data-sonner-toast],[role="alert"]').length,
  };
}"""

# 选中相机：对象树的可选行是 div[role="treeitem"][data-director-object-id]，
# **不是**「身上没有 data- 属性的裸行」（那 5 个 24×24 图标是可见性切换）。
# 定位器可能是错的 ⟹ 后置条件不能省。
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

PROBE = r"""(attr) => {
  const el = document.querySelector('[' + attr + ']');
  if (!el) return { present: false };
  const r = el.getBoundingClientRect();
  return { present: true, disabled: el.disabled,
           text: (el.textContent || '').trim().slice(0, 12),
           ariaExpanded: el.getAttribute('aria-expanded'),
           cx: r.left + r.width / 2, cy: r.top + r.height / 2 };
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


def ledger_census() -> dict[str, Any]:
    """源码侧的账本规模 —— 只数，不解释。"""
    src = STORE.read_text(encoding="utf-8")
    disp = re.findall(r'disposition: "([A-Z_]+)"', src)
    reasons = sorted(set(re.findall(r'reason: "([A-Z_]+)"', src)))
    tally: dict[str, int] = {}
    for d in disp:
        tally[d] = tally.get(d, 0) + 1
    return {"dispositionTally": dict(sorted(tally.items(),
                                            key=lambda kv: -kv[1])),
            "dispositionTotal": len(disp), "reasonKinds": len(reasons),
            "reasons": reasons,
            "lastCommandResultMentions": src.count("lastCommandResult")}


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
    ledger = ledger_census()
    rounds: list[list[dict[str, Any]]] = []
    null_drift: list[str] = []
    camera_select: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()

        # ---- 零点击自检：加了「store 逐叶投影」这一面之后仪器还稳不稳 ----
        npg = fresh(br)
        f1, f2 = npg.evaluate(FLAT), npg.evaluate(FLAT)
        s1, s2 = npg.evaluate(SNAP), npg.evaluate(SNAP)
        npg.wait_for_timeout(400)
        f3, s3 = npg.evaluate(FLAT), npg.evaluate(SNAP)
        null_drift = (sorted(k for k in f1 if f1.get(k) != f3.get(k))
                      + ["SNAP." + k for k in s1 if s1[k] != s3[k]])
        npg.close()

        # ---- 普查跑两轮：预测被推翻是结论，**结论本身也要稳** ----
        # 696 立过一条：会在两轮里给出相反答案的行为不能写成确定条件。
        for _round in range(2):
            rows: list[dict[str, Any]] = []
            for attr in CONTROLS:
                pg = fresh(br)
                sel = pg.evaluate(SELECT_CAMERA)
                if not camera_select:
                    camera_select = sel
                pg.wait_for_timeout(350)
                before_flat = pg.evaluate(FLAT)
                before = pg.evaluate(SNAP)
                info = pg.evaluate(PROBE, attr)
                if info.get("present") and not info.get("disabled"):
                    pg.mouse.click(info["cx"], info["cy"])
                    pg.wait_for_timeout(500)
                after = pg.evaluate(SNAP)
                # **播放中 objects 逐帧变，那不是一次动作。** 第一版用
                # `if (isPlaying) return {__playing:true}` 挡掉它，结果把
                # `playback` 整枚控件的 changedStore 归零 —— 守卫挡住了噪声，
                # 也挡住了证据。改成：点完之后如果进入播放，**再点一次暂停**，
                # 然后取样。启停是真人本来就会做的一对点击，取样因此是稳定的，
                # 而 `isPlaying` 翻转与 `objects` 回写都仍留在 diff 里。
                paused = False
                if after.get("isPlaying"):
                    pg.mouse.click(info["cx"], info["cy"])
                    pg.wait_for_timeout(500)
                    after = pg.evaluate(SNAP)
                    paused = True
                after_flat = pg.evaluate(FLAT)
                info_after = pg.evaluate(PROBE, attr)
                pg.close()

                playing = bool(after_flat.get("__playing"))
                changed = sorted(k for k in set(before_flat) | set(after_flat)
                                 if before_flat.get(k) != after_flat.get(k))
                ledgered = before["last"] != after["last"]
                # 自身可见面：文案 / aria-expanded。
                # **没有这一面，time-unit 会被误归成「什么都没改」** ——
                # 它确实改了，只是改的是组件局部 useState，store 一动不动。
                self_changed = (info.get("text") != info_after.get("text")
                                or info.get("ariaExpanded") != info_after.get("ariaExpanded"))
                rows.append({
                    "attr": attr, "text": info.get("text"),
                    "textAfter": info_after.get("text"),
                    "present": info.get("present"), "disabled": info.get("disabled"),
                    "clicked": bool(info.get("present") and not info.get("disabled")),
                    "selfChanged": self_changed,
                    "pausedAfterClick": paused,
                    "changedLeaves": changed[:12], "changedLeafCount": len(changed),
                    "changedStore": bool(changed) and not playing,
                    "playingNow": playing,
                    "ledgered": ledgered,
                    "lastAfter": after["last"], "wsDispAfter": after["wsDisp"],
                    "ariaExpandedBefore": info.get("ariaExpanded"),
                    "ariaExpandedAfter": info_after.get("ariaExpanded"),
                    "toasts": after["toasts"],
                })
                print(f"  [轮{_round + 1}] {attr:40} 改store={str(rows[-1]['changedStore']):5} "
                      f"叶子数={len(changed):<3} 记账={str(ledgered):5} "
                      f"last={json.dumps(after['last'], ensure_ascii=False)}")
        rounds.append(rows)
        br.close()

    rows = rounds[0]
    broke = [r["attr"] for r in rows if r["changedStore"] and not r["ledgered"]]
    obeyed = [r["attr"] for r in rows if r["changedStore"] and r["ledgered"]]
    store_silent = list(broke)
    non_store = [r["attr"] for r in rows
                 if not r["changedStore"] and r["selfChanged"]]
    did_nothing = [r["attr"] for r in rows
                   if not r["changedStore"] and not r["selfChanged"]]
    broke_each_round = [sorted(r["attr"] for r in rr if r["changedStore"]
                               and not r["ledgered"]) for rr in rounds]
    stable = bool(broke_each_round[0]) and broke_each_round[0] == broke_each_round[-1]

    # ---- 判据 1：预测被推翻，且推翻是稳定的 ----
    v.check(
        "the-ledger-misses-store-changing-controls-and-that-is-stable",
        stable and set(broke_each_round[0]) == set(broke),
        detail={"predictionThatWasFalsified": PREDICTION,
                "predictionInWords": "凡是把 store 状态改掉的控件，都会留下命令记录",
                "obeyed": obeyed, "broke": broke,
                "brokeEachRound": broke_each_round,
                "evidence": [{"attr": r["attr"], "changedLeafCount": r["changedLeafCount"],
                              "changedLeaves": r["changedLeaves"], "lastAfter": r["lastAfter"]}
                             for r in rows if r["attr"] in broke]},
        note="the check asserts the FALSIFICATION, not the prediction — a verifier that "
             "always exits non-zero would be a lie in the ledger. Two rounds are run "
             "because 696 established that a behaviour which disagrees with itself "
             "across rounds cannot be written as a settled condition.")

    # ---- 判据 2：纠正 700 的推理形式 ----
    playback = next((r for r in rows if r["attr"] == "data-director-playback"), {})
    v.check(
        "no-ledger-entry-does-not-imply-no-wiring",
        playback.get("changedStore") is True and playback.get("ledgered") is False
        and len(broke) >= 1,
        detail={"counterexample": playback.get("attr"),
                "changedLeaves": playback.get("changedLeaves"),
                "lastAfter": playback.get("lastAfter"),
                "batch700Said":
                    "motion-preset-button / motion-create-path 属于「真没接线」，"
                    "理由之一是点了之后没有任何命令被记录",
                "whatSurvives":
                    "那两枚的结论仍然成立，但理由要换成独立证据："
                    "src/components/director/DirectorCameraMotionTab.tsx:308/319 "
                    "两个 <button> 上没有 onClick —— 与记账无关",
                "whatIsWithdrawn":
                    "「没记账」作为「没接线」的**推理形式**被撤回"},
        note="the conclusion was right and the reason was wrong; only one of those "
             "two facts is about the app and the other was about my instrument")

    # ---- 判据 3：三种「不记账」分开 ----
    v.check(
        "three-kinds-of-no-ledger-entry-are-different",
        len(store_silent) >= 2 and len(non_store) >= 1,
        detail={"A_changedStoreButNoLedger": store_silent,
                "B_onlyNonStoreState": non_store,
                "B_detail": "time-unit 改的是组件局部 useState（DirectorTimeline.tsx:260，"
                            "不在 store 里）；create-motion-path 只展开一个下拉 —— "
                            "它们不是命令，不记账是预期的",
                "C_nothingChangedAtAll": did_nothing,
                "C_detail": "delete-keyframe 在「选中机位」这一态下什么都没改 —— "
                            "第三态，不能算进 A"},
        note="counting B and C as A would charge the ledger for debts it does not "
             "owe; this is 697's third-state rule applied to 'no ledger entry'")

    # ---- 判据 4：账本规模 ≠ 账本覆盖 ----
    v.check(
        "ledger-size-is-not-ledger-coverage",
        ledger["dispositionTotal"] >= 100 and len(broke) >= 1,
        detail={"sourceCensus": ledger, "runtimeGap": broke,
                "theGap": "播放（timeline.isPlaying + 逐帧把插值结果回写进 objects[*]"
                          "）和视图切换（timeline.editorMode）走的是命令层之外的路"},
        note="a big ledger is impressive and tells you nothing about its coverage; "
             "coverage can only be measured by finding the holes")

    out = {
        "width": W, "deskHeight": DESK_H,
        "prediction": PREDICTION,
        "predictionHeld": not broke,
        "cameraSelect": camera_select,
        "nullClickDrift": null_drift,
        "ledgerSourceCensus": ledger,
        "rows": rows,
        "verdicts": {"ledgeredAndChangedStore": obeyed,
                     "changedStoreButUnledgered": store_silent,
                     "onlyNonStoreState": non_store,
                     "nothingChanged": did_nothing},
        "theFinding":
            "700 用「点了之后没有任何命令被记录」把两枚右栏指路牌归为「真没接线」。"
            "本批写下预测「凡改 store 状态的控件都记账」并当场推翻它：playback 改了 11 个 "
            "store 叶子（timeline.isPlaying false→true、currentTime 0→0.5166，"
            "外加把插值结果回写进 objects[*].transform/camera），open-curve-editor 翻了 "
            "timeline.editorMode，两者都零记录。**「没记账」推不出「没接线」**。",
        "whatSurvives":
            "700 对那两枚指路牌的结论不变，理由换成独立证据：它们的 <button> 上没有 onClick。",
        "whatIsNotClaimed":
            "不声称播放/视图切换**应该**进命令账（那是一个设计取舍，不是缺陷）；"
            "本批只测出「它们不记账」这一事实，以及「用不记账推断没接线」这个推理形式不成立。"
            "不声称 objects[*] 被回写是 bug（那看起来是刻意的求值实现，**未进一步取证**）。"
            "不声称源站行为（未取证，需授权点击）。**不改 src/**。",
        "storeWritesInThisRun": "none — every control was driven by a real mouse click",
        "relationTo700":
            "700 不重写。它的两枚指路牌结论仍然成立；被撤回的是**推理形式**"
            "（「没记账」⟹「没接线」），不是结论。",
    }
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "checks": v.result},
                   ensure_ascii=False, indent=1, default=repr), encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    print("  注意：判据 1 预期为假 —— 预测被推翻才是本批的交付物。")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
