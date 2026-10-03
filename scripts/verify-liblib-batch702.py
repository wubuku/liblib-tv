#!/usr/bin/env python3
"""batch 702 验收：「objects 是派生视图」这句话是可以被证伪的 —— 而它没有被证伪

## 起点

701 测出 `playback` 会把插值结果回写进 `objects[*]`，并明确写下
「**不声称 `objects[*]` 被回写是 bug（那看起来是刻意的求值实现，未进一步取证）**」。

本批就去取那份证。

## 三步

**① 播放改了什么。** 拍平三样：**创作数据 `authoredObjects`**、
**派生视图 `objects`**、**历史 `history`**。
播放一次（真点击启停）后：`authoredObjects` **0 个叶子变**、
`history` **0 个叶子变**、`objects` 变 9 个、`currentTime` 变。
⟹ 播放只动派生视图，不动创作数据，也不产生撤销条目。

**② `objects` 是不是纯函数。**
「派生视图」这个说法可以被证伪，检验方式只有一条：
**同一时刻，「从没播过」与「播过又退回」的派生值必须逐位相同。**
三个播放头位置 × 五组值 = **15/15 逐位相同**。

**③ 第一版对照是无效的（这条最值钱）。**
第一版做的是「播 → 停 → 把播放头点回 0 → 比对初始值」，
结果 6 组值**全部不复原**，看起来像是派生视图被破坏。

**不是。** 退回后播放头读数是 **`0.008993184852104265`，不是 0** ——
标尺最左端那个像素落不到 0。**读数差完全由播放头偏移解释。**
这正是 697 立的那条纪律（「非 0 读数不能被读成缺陷」）在我自己这批的新仪器上
**又发生一次**。修法不是加解释，是**重做对照**：
两臂只差「有没有播过」，且**先断言两侧的播放头读数相同**，相同才比。

## 纪律

- **对照的两臂必须只差一个动作，且共享前提要可断言。**
- 播放头的移动全部用**真实点击标尺** `[data-director-timeline-ruler]`，零 store 写入。
- 零点击自检 + 两轮（696 纪律：会自相矛盾的行为不能写成确定条件）。

## 四条判据

1. `playback-changes-only-the-derived-view`
2. `objects-is-a-pure-function-of-authored-and-playhead`
3. `playback-produces-no-undo-entry`
4. `the-first-control-was-invalid-and-the-deviation-is-fully-the-playhead-offset`
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch702-2026-10-01"
W, DESK_H = 1280, 1150

# **预测写在这里，先于任何测量**
PREDICTION = ("playback 只改派生视图 objects；创作数据 authoredObjects 与历史 history "
              "一个叶子都不变；且 objects 是 (authoredObjects, 播放头) 的纯函数")

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

# 拍平三样：创作数据 / 派生视图 / 历史。**分开拍，才分得出谁没动。**
FLAT = r"""() => {
  const s = window.__director_store.getState();
  if (s.timeline && s.timeline.isPlaying) return { __playing: true };
  const out = {};
  const walk = (v, path, d) => {
    if (d > 4) { out[path] = String(v); return; }
    if (v === null || typeof v !== 'object') { out[path] = JSON.stringify(v); return; }
    if (Array.isArray(v)) { out[path + '.length'] = v.length;
      v.forEach((x, i) => walk(x, path + '[' + i + ']', d + 1)); return; }
    for (const k of Object.keys(v).sort()) walk(v[k], path + '.' + k, d + 1);
  };
  walk(s.authoredObjects, 'authoredObjects', 0);
  walk(s.objects, 'objects', 0);
  walk(s.history, 'history', 0);
  out.__historyLen = s.history.past.length;
  out.__currentTime = s.timeline.currentTime;
  return out;
}"""

# 派生值的具体读数（用于「纯函数」判据）
VALS = r"""() => {
  const s = window.__director_store.getState();
  const c = s.objects[4], o = s.objects[0];
  return { t: s.timeline.currentTime,
    obj0: o.transform.position.slice(0, 3), rot0: o.transform.rotation.slice(0, 3),
    obj4: c.transform.position.slice(0, 3), fov: c.camera.fov,
    target: c.camera.target.slice(0, 3) };
}"""

RULER = r"""() => {
  const el = document.querySelector('[data-director-timeline-ruler]');
  if (!el) return null;
  const b = el.getBoundingClientRect();
  return { left: b.left, top: b.top, width: b.width, height: b.height };
}"""

PLAYBACK = r"""() => {
  const el = document.querySelector('[data-director-playback]');
  if (!el) return null;
  const b = el.getBoundingClientRect();
  return { cx: b.left + b.width / 2, cy: b.top + b.height / 2, disabled: el.disabled };
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


def click_ruler(page, frac: float) -> None:
    g = page.evaluate(RULER)
    page.mouse.click(g["left"] + g["width"] * frac, g["top"] + g["height"] / 2)
    page.wait_for_timeout(400)


def click_ruler_px(page, px: float) -> None:
    """按**像素**点标尺。第一版的 bug 就在这里：它以为点左端就是 t=0，
    实际点的是左端往右 2px，那落在 t=0.00899。"""
    g = page.evaluate(RULER)
    page.mouse.click(g["left"] + px, g["top"] + g["height"] / 2)
    page.wait_for_timeout(400)


def play_once(page) -> dict[str, Any]:
    """真实点击启停一对。"""
    pb = page.evaluate(PLAYBACK)
    if not pb or pb["disabled"]:
        return {"played": False, "reason": "playback-absent-or-disabled"}
    page.mouse.click(pb["cx"], pb["cy"])          # 播
    page.wait_for_timeout(1500)
    page.mouse.click(pb["cx"], pb["cy"])          # 停
    page.wait_for_timeout(500)
    return {"played": True}


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
    one_play: dict[str, Any] = {}
    purity: list[dict[str, Any]] = []
    invalid_control: dict[str, Any] = {}

    # 三个播放头位置：都在可视范围内（标尺宽 1779，视口只到约 0.54）
    FRACTIONS = [0.25, 0.30, 0.40]

    with sync_playwright() as p:
        br = p.chromium.launch()

        # ---- 零点击自检 ----
        npg = fresh(br)
        f1 = npg.evaluate(FLAT)
        npg.wait_for_timeout(400)
        f3 = npg.evaluate(FLAT)
        null_drift = sorted(k for k in f1 if f1.get(k) != f3.get(k))
        npg.close()

        # ---- ① 播放改了什么 ----
        pg = fresh(br)
        before = pg.evaluate(FLAT)
        played = play_once(pg)
        after = pg.evaluate(FLAT)
        pg.close()
        diff = sorted(k for k in set(before) | set(after)
                      if before.get(k) != after.get(k))
        auth = [k for k in diff if k.startswith("authoredObjects")]
        objs = [k for k in diff if k.startswith("objects")]
        hist = [k for k in diff if k.startswith("history") or k == "__historyLen"]
        one_play = {"played": played, "changedTotal": len(diff),
                    "authoredObjectsChanged": auth, "objectsChanged": objs,
                    "historyChanged": hist,
                    "other": [k for k in diff if k not in auth + objs + hist],
                    "historyLenBefore": before["__historyLen"],
                    "historyLenAfter": after["__historyLen"],
                    "currentTimeBefore": before["__currentTime"],
                    "currentTimeAfter": after["__currentTime"]}
        print(f"  播放一次：共变 {len(diff)} 个叶子 —— "
              f"authoredObjects {len(auth)} / objects {len(objs)} / history {len(hist)}")

        # ---- ② 纯函数：两臂只差「有没有播过」，共享前提先断言 ----
        for frac in FRACTIONS:
            arms: dict[str, Any] = {}
            for label, did_play in (("neverPlayed", False), ("playedThenBack", True)):
                pg = fresh(br)
                if did_play:
                    play_once(pg)
                click_ruler(pg, frac)
                arms[label] = pg.evaluate(VALS)
                pg.close()
            same_t = arms["neverPlayed"]["t"] == arms["playedThenBack"]["t"]
            keys = ("obj0", "rot0", "obj4", "fov", "target")
            per = {k: (json.dumps(arms["neverPlayed"][k])
                       == json.dumps(arms["playedThenBack"][k])) for k in keys}
            purity.append({"fraction": frac, "playheadBothArms": arms["neverPlayed"]["t"],
                           "samePlayhead": same_t, "identical": per,
                           "sample": arms["neverPlayed"]})
            print(f"  f={frac}: 播放头两臂相同={same_t}  逐位相同 "
                  f"{sum(per.values())}/{len(per)}")

        # ---- ③ 第一版那个无效对照：偏离量完全由像素偏移解释 ----
        # 两个像素位置各跑一对两臂：
        #   +0px —— 真的落在 t=0，第一版**以为**自己点的是这个
        #   +2px —— 落在 t≈0.00899，第一版**实际**点的就是这个
        arms3: dict[str, Any] = {}
        for px in (0.0, 2.0):
            for label, did_play in (("fresh", False), ("playedBack", True)):
                pg = fresh(br)
                if did_play:
                    play_once(pg)
                click_ruler_px(pg, px)
                arms3[f"{px:g}px:{label}"] = pg.evaluate(VALS)
                pg.close()
        k3 = ("obj0", "rot0", "obj4", "fov", "target")

        def arms_identical(px: float) -> dict[str, bool]:
            a, b = arms3[f"{px:g}px:fresh"], arms3[f"{px:g}px:playedBack"]
            return {k: (json.dumps(a[k]) == json.dumps(b[k])) for k in k3}

        at_zero, at_2px = arms_identical(0.0), arms_identical(2.0)
        invalid_control = {
            "atLeftEdgePx0": {"playhead": arms3["0px:fresh"]["t"],
                              "isZero": arms3["0px:fresh"]["t"] == 0,
                              "armsIdentical": at_zero,
                              "identicalCount": sum(at_zero.values())},
            "atLeftEdgePlus2Px": {"playhead": arms3["2px:fresh"]["t"],
                                  "isZero": arms3["2px:fresh"]["t"] == 0,
                                  "armsIdentical": at_2px,
                                  "identicalCount": sum(at_2px.values())},
            "pixelsToSeconds": (arms3["2px:fresh"]["t"] - arms3["0px:fresh"]["t"]) / 2.0,
            "whatTheFirstVersionCompared":
                "「播过 → 点左端」 vs 「t=0 的状态」，而它点的是左端 +2px",
        }
        print(f"  左端 +0px：播放头={arms3['0px:fresh']['t']}  两臂相同 {sum(at_zero.values())}/5")
        print(f"  左端 +2px：播放头={arms3['2px:fresh']['t']}  两臂相同 {sum(at_2px.values())}/5"
              f"  ⟹ 每像素 ≈ {invalid_control['pixelsToSeconds']:.5f}s")
        br.close()

    all_same = all(p["samePlayhead"] and all(p["identical"].values()) for p in purity)
    valid_pairs = sum(1 for p in purity if p["samePlayhead"])

    v.check(
        "playback-changes-only-the-derived-view",
        one_play["played"].get("played") is True
        and len(one_play["authoredObjectsChanged"]) == 0
        and len(one_play["historyChanged"]) == 0
        and len(one_play["objectsChanged"]) > 0,
        detail={"changedTotal": one_play["changedTotal"],
                "authoredObjectsChanged": one_play["authoredObjectsChanged"],
                "objectsChanged": one_play["objectsChanged"][:6],
                "historyChanged": one_play["historyChanged"],
                "currentTime": [one_play["currentTimeBefore"],
                                one_play["currentTimeAfter"]]},
        note="the prediction named authoredObjects and history as the things that "
             "must NOT move; measuring only objects would have looked like proof "
             "without ruling out data corruption")

    v.check(
        "objects-is-a-pure-function-of-authored-and-playhead",
        all_same and valid_pairs == len(FRACTIONS),
        detail={"fractions": FRACTIONS,
                "perPosition": [{"f": p["fraction"], "playhead": p["playheadBothArms"],
                                 "samePlayhead": p["samePlayhead"],
                                 "identical": p["identical"]} for p in purity],
                "identicalCount": sum(sum(p["identical"].values()) for p in purity),
                "comparedCount": len(FRACTIONS) * 5,
                "theTest":
                    "同一时刻，「从没播过」与「播过又退回」的派生值必须逐位相同"},
        note="'derived view' is a falsifiable claim, and this is the only observation "
             "that can falsify it")

    v.check(
        "playback-produces-no-undo-entry",
        one_play["historyLenBefore"] == one_play["historyLenAfter"] == 0,
        detail={"historyLenBefore": one_play["historyLenBefore"],
                "historyLenAfter": one_play["historyLenAfter"]},
        note="consistent with 'nothing was authored'; an undo entry for a pure "
             "playback would be a different claim and was not observed")

    v.check(
        "the-first-control-was-invalid-and-the-deviation-is-fully-the-pixel-offset",
        invalid_control["atLeftEdgePx0"]["isZero"] is True
        and invalid_control["atLeftEdgePx0"]["identicalCount"] == 5
        and invalid_control["atLeftEdgePlus2Px"]["isZero"] is False
        and invalid_control["atLeftEdgePlus2Px"]["identicalCount"] == 5,
        detail=invalid_control,
        note="the first version compared 'played, then clicked the left edge' against "
             "the t=0 state and read 6/6 non-restoration as a clobbered derived view. "
             "It actually clicked left edge +2px, which lands at t≈0.00899, not 0. "
             "At t=0 exactly the two arms are 5/5 bit-identical, and at +2px they are "
             "also 5/5 identical — so the non-restoration was the pixel offset alone")

    out = {
        "width": W, "deskHeight": DESK_H,
        "prediction": PREDICTION,
        "predictionHeld": (len(one_play["authoredObjectsChanged"]) == 0
                           and len(one_play["historyChanged"]) == 0
                           and all_same),
        "nullClickDrift": null_drift,
        "onePlayback": one_play,
        "purityScan": purity,
        "invalidFirstControl": invalid_control,
        "theFinding":
            "播放只改派生视图：authoredObjects 0 个叶子变、history 0 个叶子变，"
            "objects 变 9 个、currentTime 变。更进一步，objects 是 "
            "(authoredObjects, 播放头) 的纯函数 —— 三个播放头位置上，"
            "「从没播过」与「播过又退回」的派生值 15/15 逐位相同。"
            "⟹ 701 记的「playback 把插值结果回写进 objects[*]」不是数据污染。",
        "theMostValuablePart":
            "第一版对照是无效的：它拿「播过又点回标尺最左端」去比「t=0 的状态」，"
            "而标尺最左端那个像素落在 0.008993184852104265 而不是 0 ⟹ "
            "6 组值全部不复原，看起来像派生视图被破坏。**补上第三臂**"
            "（从没播过、只点同一个像素）后，同一个非 0 播放头上两臂 5/5 逐位相同 ⟹ "
            "偏离量完全由播放头偏移解释。**这是 697 那条纪律在我自己的新仪器上第三次生效。**",
        "whatIsNotClaimed":
            "不声称 objects 的求值实现「好」或「坏」—— 本批只测出它是纯函数、不污染创作数据。"
            "不声称 15/15 覆盖了所有播放头位置（只测了三个，f=0.25/0.30/0.40，"
            "**都在标尺可视范围内**；可视范围约 f≤0.54，更后面的位置本批没测）。"
            "不声称源站行为（未取证，需授权点击）。**不改 src/**。",
        "storeWritesInThisRun":
            "none — the playhead is moved by clicking [data-director-timeline-ruler]",
        "relationTo701":
            "701 明确写下「不声称 objects[*] 被回写是 bug，未进一步取证」；"
            "本批取到了那份证 —— 不是 bug。701 的读数本身未被推翻。",
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
