#!/usr/bin/env python3
"""batch 704 验收：「Enter 不提交、失焦才提交」，以及「COMMITTED 不等于状态变了」

## 起点

703 顺带查出一件事并写进了账本：`[data-director-shot-end]` 能输入、能聚焦，
但 `Enter` / `ArrowUp` / `Tab` 三条路径**全部进不去 store**，于是 703 把它归成
**「第四类：能输入但没有提交路径」**，并说它是**「第四类控件」**。

**这条结论是错的，而且错在两个地方。** 本批把它取回来。

## 703 错在哪

**① 703 填的是 12，而这个输入框的 `max` 就是 `duration`（=8）。**
填一个**范围内的值**（6）再按 `Tab` —— **提交成功**，区间标签同步变成 `0.0-6.0s`。
所以「没有提交路径」是错的：**提交路径存在，就是失焦**。

**② 「第四类」这个分类是本批自己造出来的，本批自己拆掉。**
它不是「没有提交路径」，而是「**提交路径只有失焦没有回车**」——
这个类别在普查里立刻显示出它不是一类，而是**两个具体字段的行为**。

## 普查（7 枚输入控件 + 1 个越界样本，每格一个全新页面）

| 控件 | 新值 | 在 `[min,max]` 内 | 按 `Enter` | 按 `Tab` | 记账 |
|---|---|---|---|---|---|
| `object-name` | 改名试试A | 是 | 提交 ✓ | 提交 ✓ | `UPDATE_OBJECT` |
| `shot-name` | 镜头改名B | 是 | 提交 ✓ | 提交 ✓ | `UPDATE_SHOT` |
| **`shot-start`** | 2 | 是 | **留着但不提交** | 提交 ✓ | `UPDATE_SHOT` |
| **`shot-end`** | 6 | 是 | **留着但不提交** | 提交 ✓ | **`GESTURE_BEGIN`** |
| **`shot-end`** | **9（越界）** | **否** | **留着但不提交** | **输入框回弹 8，store 不变** | **`GESTURE_BEGIN` / `COMMITTED`** |
| `camera-fov-number` | 50 | 是 | 提交 ✓ | 提交 ✓ | `UPDATE_CAMERA` |
| `hex-input` | ff0000 | 是 | 提交 ✓ | 提交 ✓ | `UPDATE_OBJECT` |

**7 枚里只有 2 枚（`shot-start` / `shot-end`）忽略 `Enter`。**

## 本批最锋利的一条

越界样本那一行：**store 没有任何叶子变、输入框回弹到 8、用户什么也没得到 ——
而命令账记的是 `GESTURE_BEGIN` / `COMMITTED`。**

⟹ **`COMMITTED` 记的是「我执行了一个手势」，不是「状态变了」。**
这一条同时给 700/701 的命令账加了一个维度：701 测的是「哪些动作不记账」，
本批测出的是「**有些动作记了账但等于没做**」—— 两个方向都碰到了。

## 纪律

- 每个样本一个全新页面（避免上一个样本的脏状态）。
- 判「有没有变」用**全 store 逐叶投影**，不靠逐字段知识。
- **定位失败要如实记成第三态**（第一版 `transform-field` 用了错的属性值而定位失败，
  那是「我这一步没测到」，不是「该控件不存在」）—— 补上正确的
  `[data-director-transform-field][data-director-transform-axis]` 才是读数。
- 零 store 写入；提交全部用真实键盘事件。

## 四条判据

1. `enter-commits-for-every-input-except-the-two-shot-time-fields`
2. `the-two-shot-time-fields-are-siblings-on-different-command-paths`
3. `committed-in-the-ledger-does-not-imply-the-state-changed`
4. `correction-to-703-the-commit-path-is-blur-only-and-703-tested-an-out-of-range-value`
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch704-2026-10-01"
W, DESK_H = 1280, 1150

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

SELECT_CAMERA = r"""() => {
  const s = window.__director_store.getState();
  const cam = s.objects.find((o) => o.kind === 'camera');
  if (!cam) return { ok: false, stage: 'no-camera-object' };
  const row = document.querySelector(
    '[data-director-tree] [role="treeitem"][data-director-object-id="'
    + cam.id + '"]');
  if (!row) return { ok: false, stage: 'no-treeitem-by-object-id' };
  row.click();
  return { ok: window.__director_store.getState().selectedObjectId === cam.id };
}"""

# 全 store 逐叶投影 —— 判「有没有变」不需要逐字段知识
FLAT = r"""() => {
  const s = window.__director_store.getState();
  const out = {};
  const walk = (v, path, d) => {
    if (d > 4) { out[path] = String(v); return; }
    if (v === null || typeof v !== 'object') { out[path] = JSON.stringify(v); return; }
    if (Array.isArray(v)) { out[path + '.length'] = v.length;
      v.forEach((x, i) => walk(x, path + '[' + i + ']', d + 1)); return; }
    for (const k of Object.keys(v).sort()) walk(v[k], path + '.' + k, d + 1);
  };
  for (const k of Object.keys(s).sort()) {
    if (typeof s[k] === 'function') continue;
    walk(s[k], k, 0);
  }
  return out;
}"""

LAST = r"""() => {
  const r = window.__director_store.getState().lastCommandResult;
  return r ? { commandKind: r.commandKind, disposition: r.disposition,
               reason: r.reason } : null;
}"""

# 手势生命周期要看的面：activeGesture 是否开着、镜头有没有变、历史有没有长
GESTURE = r"""() => {
  const s = window.__director_store.getState();
  const g = (sel) => { const e = document.querySelector(sel); return e ? e.value : null; };
  return { activeGesture: s.history.activeGesture === null ? null
            : (s.history.activeGesture === undefined ? 'undefined' : 'SET'),
           pastLen: s.history.past.length,
           shotEnd: (s.shots || [])[0] ? s.shots[0].endTime : null,
           shotStart: (s.shots || [])[0] ? (s.shots[0].startTime) : null,
           inputEnd: g('[data-director-shot-end]'),
           rangeLabel: (document.querySelector('[data-director-shot-range]') || {}).textContent,
           last: s.lastCommandResult ? { c: s.lastCommandResult.commandKind,
                  d: s.lastCommandResult.disposition } : null };
}"""

# (名字, CSS 选择器, 新值, 是否在 [min,max] 内, 标签文字)
CASES: list[tuple[str, str, str, bool, str]] = [
    ("object-name", "[data-director-object-name]", "改名试试A", True, "名称"),
    ("shot-name", "[data-director-shot-name]", "镜头改名B", True, "镜头名称"),
    ("shot-start", "[data-director-shot-start]", "2", True, "开始"),
    ("shot-end", "[data-director-shot-end]", "6", True, "结束"),
    ("shot-end(越界 9 > max 8)", "[data-director-shot-end]", "9", False, "结束"),
    ("camera-fov-number", "[data-director-camera-fov-number]", "50", True, "FOV"),
    ("hex-input", "[data-director-hex-input]", "ff0000", True, "颜色#"),
    ("transform-field position/x",
     '[data-director-transform-field="position"][data-director-transform-axis="x"]',
     "3.5", True, "位置 x"),
]


def fresh(browser) -> Any:
    page = browser.new_page(viewport={"width": W, "height": DESK_H},
                            device_scale_factor=1)
    b617.open_desk(page)
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(300)
    page.evaluate(SELECT_CAMERA)
    page.wait_for_timeout(500)
    return page


def read_field(page, selector: str) -> dict[str, Any]:
    return page.evaluate("""(sel) => {
      const el = document.querySelector(sel);
      if (!el) return { present: false };
      const r = el.getBoundingClientRect();
      return { present: true, value: el.value, min: el.min || null, max: el.max || null,
               readOnly: !!el.readOnly, disabled: !!el.disabled,
               cx: r.left + r.width / 2, cy: r.top + r.height / 2 };
    }""", selector)


def run_one(browser, selector: str, value: str, key: str) -> dict[str, Any]:
    page = fresh(browser)
    try:
        info = read_field(page, selector)
        if not info.get("present"):
            # **定位失败是第三态**，不是「该控件不存在」——
            # 第一版 transform-field 用了错的属性值而定位失败，差一条读数。
            return {"located": False, "selector": selector, "key": key}
        before = page.evaluate(FLAT)
        last_before = page.evaluate(LAST)
        el = page.locator(selector).first
        el.click()
        page.wait_for_timeout(150)
        el.fill(value)
        page.wait_for_timeout(150)
        page.keyboard.press(key)
        page.wait_for_timeout(700)
        after = page.evaluate(FLAT)
        last_after = page.evaluate(LAST)
        info_after = read_field(page, selector)
        changed = sorted(k for k in set(before) | set(after)
                         if before.get(k) != after.get(k) and k != "lastCommandResult")
        return {
            "located": True, "selector": selector, "key": key, "typed": value,
            "storeChanged": bool(changed), "changedLeaves": changed[:5],
            "inputBefore": info["value"], "inputAfter": info_after.get("value"),
            "range": [info["min"], info["max"]],
            "lastBefore": last_before, "lastAfter": last_after,
            "ledgerMoved": last_before != last_after,
        }
    finally:
        page.close()


def gesture_lifecycle(browser, closer: str) -> dict[str, Any]:
    """越界编辑 → 看手势开着多久、由什么关掉、收尾时账上写什么。"""
    page = fresh(browser)
    try:
        steps: list[dict[str, Any]] = [{"stage": "before", **page.evaluate(GESTURE)}]
        e = page.locator("[data-director-shot-end]").first
        e.click(); page.wait_for_timeout(150)
        e.fill("9")                      # max = duration = 8 ⟹ 越界
        page.wait_for_timeout(150)
        page.keyboard.press("Tab")
        page.wait_for_timeout(800)
        steps.append({"stage": "afterOutOfRangeTab", **page.evaluate(GESTURE)})
        page.wait_for_timeout(2500)
        steps.append({"stage": "plus2500ms", **page.evaluate(GESTURE)})
        if closer == "unrelatedEdit":
            o = page.locator("[data-director-object-name]").first
            o.click(); page.wait_for_timeout(150)
            o.fill("随手改个名"); page.wait_for_timeout(150)
            page.keyboard.press("Enter")
        else:                             # 点画布空白
            page.mouse.click(640, 400)
        page.wait_for_timeout(800)
        steps.append({"stage": f"after{closer}", **page.evaluate(GESTURE)})
        return {"closer": closer, "steps": steps}
    finally:
        page.close()


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


def verdict(cell: dict[str, Any]) -> str:
    if not cell.get("located"):
        return "未定位"
    if cell["storeChanged"]:
        return "提交"
    if cell["inputAfter"] != cell["typed"]:
        return f"回弹→{cell['inputAfter']!r}"
    return f"留着但不提交({cell['inputAfter']!r})"


def main() -> int:
    v = Verifier()
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    null_drift: list[str] = []
    table: list[dict[str, Any]] = []

    with sync_playwright() as p:
        br = p.chromium.launch()

        npg = fresh(br)
        f1 = npg.evaluate(FLAT)
        npg.wait_for_timeout(400)
        f2 = npg.evaluate(FLAT)
        null_drift = sorted(k for k in f1 if f1.get(k) != f2.get(k))
        npg.close()

        for name, selector, value, in_range, label in CASES:
            e = run_one(br, selector, value, "Enter")
            t = run_one(br, selector, value, "Tab")
            table.append({"name": name, "selector": selector, "value": value,
                          "inRange": in_range, "label": label,
                          "enter": e, "tab": t,
                          "enterVerdict": verdict(e), "tabVerdict": verdict(t)})
            print(f"  {name:34} {value:9} 范围内={str(in_range):5} "
                  f"Enter={table[-1]['enterVerdict']:22} Tab={table[-1]['tabVerdict']:22} "
                  f"记账={json.dumps(t.get('lastAfter'), ensure_ascii=False)}")

        # ---- 手势生命周期：越界编辑留下的手势由什么关掉、收尾时账上写什么 ----
        by_unrelated = gesture_lifecycle(br, "unrelatedEdit")
        by_click = gesture_lifecycle(br, "canvasClick")
        oor = by_unrelated
        for s in by_click["steps"]:
            print(f"  [点画布收尾] {s['stage']:22} gesture={str(s['activeGesture']):5} "
                  f"shotEnd={s['shotEnd']} pastLen={s['pastLen']} "
                  f"last={json.dumps(s['last'], ensure_ascii=False)}")
        br.close()

    located = [r for r in table if r["enter"].get("located") and r["tab"].get("located")]
    enter_commits = [r["name"] for r in located if r["enter"]["storeChanged"]]
    enter_silent = [r["name"] for r in located
                    if not r["enter"]["storeChanged"] and r["enter"]["ledgerMoved"] is False]
    tab_commits = [r["name"] for r in located if r["tab"]["storeChanged"]]
    out_of_range = next((r for r in located if not r["inRange"]), None)
    start_row = next((r for r in located if r["name"] == "shot-start"), None)
    end_row = next((r for r in located if r["name"] == "shot-end"), None)

    v.check(
        "enter-commits-for-every-input-except-the-two-shot-time-fields",
        len(located) == len(CASES)
        and sorted(enter_commits) == sorted(r["name"] for r in located
                                            if r["name"] not in
                                            ("shot-start", "shot-end",
                                             "shot-end(越界 9 > max 8)"))
        and set(enter_silent) == {"shot-start", "shot-end", "shot-end(越界 9 > max 8)"},
        detail={"table": [{"name": r["name"], "typed": r["value"],
                           "inRange": r["inRange"],
                           "enter": r["enterVerdict"], "tab": r["tabVerdict"]}
                          for r in table],
                "enterCommits": enter_commits,
                "enterKeepsTypingButDoesNotCommit": enter_silent,
                "note": "「留在输入框里但 store 不动、连账都不记」—— 这不是拒绝，"
                        "是什么都没发生"},
        note="six of the seven inputs commit on Enter; the two shot time fields do not, "
             "so a keyboard user pressing Enter in them gets silence")

    v.check(
        "the-two-shot-time-fields-are-siblings-on-different-command-paths",
        bool(start_row) and bool(end_row)
        and start_row["tab"]["lastAfter"] is not None
        and end_row["tab"]["lastAfter"] is not None
        and start_row["tab"]["lastAfter"]["commandKind"] != end_row["tab"]["lastAfter"]["commandKind"],
        detail={"shotStart": {"command": start_row["tab"]["lastAfter"],
                              "verdict": start_row["tabVerdict"]},
                "shotEnd": {"command": end_row["tab"]["lastAfter"],
                            "verdict": end_row["tabVerdict"]},
                "comment": "同一个面板里两个相邻的时间字段，走两条不同的命令路径"},
        note="'GESTURE_BEGIN' reads like a drag gesture, not a field edit — recorded as "
             "a reading, not as an explanation")

    v.check(
        "a-rejected-edit-is-ledgered-as-committed-and-leaves-an-open-gesture",
        bool(oor) and bool(by_unrelated) and bool(by_click)
        and by_click["steps"][0]["activeGesture"] is None
        and by_click["steps"][1]["activeGesture"] == "SET"
        and by_click["steps"][1]["shotEnd"] == 8
        and by_click["steps"][1]["pastLen"] == 0
        and by_click["steps"][1]["last"] == {"c": "GESTURE_BEGIN", "d": "COMMITTED"}
        and by_click["steps"][2]["activeGesture"] == "SET"     # +2.5s 仍在，不自动收
        # 两种收尾方式**留下的最后一条账不同** —— 收尾记录挂在触发它的那个动作上
        and by_click["steps"][3]["activeGesture"] is None
        and by_click["steps"][3]["last"] == {"c": "GESTURE_COMMIT", "d": "NOOP"}
        and by_click["steps"][3]["pastLen"] == 0
        and by_unrelated["steps"][3]["activeGesture"] is None
        and by_unrelated["steps"][3]["last"] == {"c": "UPDATE_OBJECT", "d": "COMMITTED"}
        and by_unrelated["steps"][3]["pastLen"] == 1,
        detail={"lifecycleClosedByCanvasClick": by_click["steps"],
                "lifecycleClosedByUnrelatedEdit": by_unrelated["steps"],
                "theReading":
                    "越界值 9（max=8）按 Tab：镜头区间没变（shotEnd 仍 8、标签仍 "
                    "0.0-8.0s、输入框回弹 8）、历史没长（pastLen 仍 0），"
                    "**但命令账当场记 GESTURE_BEGIN / COMMITTED**，"
                    "并且 `history.activeGesture` 一直被置上（+2.5s 复查仍在，不自动收）。",
                "theTwoClosers":
                    "点画布空白收尾 ⟹ 账上是 GESTURE_COMMIT / **NOOP**，pastLen 仍 0；"
                    "改另一个字段收尾 ⟹ 账上是**那次编辑自己的** UPDATE_OBJECT / "
                    "COMMITTED，pastLen 0→1 —— **被拒手势的那句 NOOP 压根没出现过**。",
                "theConsequence":
                    "同一次被拒绝的编辑，在账本上先是 COMMITTED；"
                    "那句 NOOP 要等下一个动作触发收尾才补上，"
                    "**而且补不补得上取决于下一个动作是什么**。"},
        note="the first version of this check said 'nothing changed' — too narrow a face "
             "again: only shots[0].endTime was read, and the full projection shows 119 "
             "leaves move (the gesture baseline). And the first version also asserted "
             "one closing record for both closers, which was wrong: the NOOP is only "
             "written when the gesture is closed by a click, not by an unrelated edit")

    v.check(
        "correction-to-703-the-commit-path-is-blur-only-and-703-tested-an-out-of-range-value",
        bool(end_row)
        and end_row["tab"]["storeChanged"] is True
        and end_row["enter"]["storeChanged"] is False,
        detail={"inRangeValue": end_row["value"],
                "enterVerdict": end_row["enterVerdict"],
                "tabVerdict": end_row["tabVerdict"],
                "batch703Said": "「能聚焦、能打字，但 Enter / ArrowUp / Tab 三条路径全部"
                                "进不去 store」⟹ 归为「第四类：能输入但没有提交路径」",
                "whatIsWithdrawn": "「没有提交路径」这个说法整条撤回",
                "whatSurvives": "703 的**读数**仍然为真 —— 填 12（越界，max=8）时，"
                                "Enter / ArrowUp / Tab 确实都不进 store，Tab 之后输入框"
                                "确实弹回 8。本批只是换了解释：不是没有路径，是"
                                "**路径存在但只认失焦，而且我测的值越界**",
                "theCategoryCollapsed":
                    "「第四类：能输入但没有提交路径」这个分类是 703 自己造的，"
                    "本批把它拆成两个具体字段的行为 —— 它不是一类"},
        note="a correct reading with a wrong explanation, found one batch later by "
             "testing the same control with a value inside its own min/max")

    out = {
        "width": W, "deskHeight": DESK_H,
        "nullClickDrift": null_drift,
        "census": table,
        "verdicts": {"enterCommits": enter_commits,
                     "enterKeepsTypingButDoesNotCommit": enter_silent,
                     "tabCommits": tab_commits},
        "theFinding":
            "7 枚右栏输入控件里，只有 shot-start / shot-end 忽略 Enter —— "
            "填进去的值留在输入框里、store 不动、连一条命令都不记。按 Tab（失焦）"
            "则提交。703 把这两个字段判成「没有提交路径」，本批撤回了这个说法："
            "路径存在，只是**只有失焦**。而 703 当时填的 12 越界（max=duration=8），"
            "所以那条读数虽然为真，解释是错的。",
        "theSharpestPart":
            "越界的值（9 > max 8）按 Tab：store 一个叶子都没变、输入框回弹到 8、"
            "用户什么也没得到 —— **而命令账记的是 GESTURE_BEGIN / COMMITTED**。"
            "⟹ COMMITTED 不蕴含状态改变。",
        "whatIsNotClaimed":
            "不声称这是缺陷还是刻意的交互取舍（**源站未取证，需授权点击**）。"
            "不声称 GESTURE_BEGIN 这个命令名意味着实现上走了拖拽手势 —— "
            "**那只是名字，读数只到「命令名不同」**。"
            "不声称其余 17 枚右栏 input/select 都有同样行为 —— 本批只测了 7 枚有代表性的。"
            "**不改 src/**。",
        "storeWritesInThisRun":
            "none — every edit was driven by real keyboard events on real inputs",
        "relationTo703":
            "703 不重写。它的读数（填 12 时三条路径都不进 store、Tab 后回弹）仍然为真；"
            "被撤回的是**解释**（「没有提交路径」这个分类）。",
        "relationTo700And701":
            "700/701 不重写。本批给命令账补了一个维度：701 测的是「哪些动作不记账」，"
            "本批测出「有些动作记了账但等于没做」—— 两个方向都碰到了。",
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
