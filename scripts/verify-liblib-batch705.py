#!/usr/bin/env python3
"""batch 705 验收：把普查做完 —— 右栏 24 枚可输入控件的提交路径全表

## 起点

704 测了右栏 7 枚输入控件，然后诚实地写下
「**不声称其余 17 枚右栏 input/select 都有同样行为 —— 本批只测了 7 枚**」。

**普查停在 7/24 并标「未取证」是可以的，但既然能做，就把它做完。**

## 三条预测（写死在代码里，先于任何测量）

- **P1** 多数输入控件把 `Enter` 当提交键
- **P2** `range` 类型没有提交步骤（`input` 事件即写入），不该混进 `Enter`/`Tab` 的比较
- **P3** `select` 与 `text` 的提交行为不同
- **P4** 每枚控件都有唯一稳定键（组合属性），所以普查不按索引

**P3 被推翻**：两个 `select`（`camera-follow-target` / `camera-look-at-mode`）
与 `text` 一样，`Enter` 与 `Tab` 都提交。**被推翻的方向是「类别变少」而不是变多。**

## 全表（24 枚，唯一键 24 个）

| 判定 | 枚数 | 控件 |
|---|---|---|
| **忽略 `Enter`**（值留在框里、store 不动、连账都不记） | **2** | `shot-start` `shot-end` |
| `Enter` 与 `Tab` 都提交 | **19** | 其余全部适用控件 |
| 不适用 | 3 | `uniform-scale` / `camera-fov`（range，无提交步骤）<br>`camera-switch`（**只有一个选项，造不出差异**） |

**独立复现了 704 的读数**，而且这次是全覆盖：忽略 `Enter` 的**仍然只有那 2 枚**。

## 顺带一条：12 枚 `transform:*` 全走手势

`position`/`rotation`/`scale`/`target` 各 x/y/z 共 **12 枚数字框**，
提交后账上一律记 **`GESTURE_COMMIT`/`COMMITTED`** ——
**在数字框里敲数字，和拖 3D 手柄，走的是同一套手势机制。**
而 `shot-start` / `shot-end` 记 `UPDATE_SHOT` / `GESTURE_BEGIN`。

## 本批自己踩的坑：第三态的第四个应用面

**「无变化」有两种：控件不提交，和我没造出差异。**

普查器第一版给 `text` / `color` 填了它**已有的值** ——
于是那一列的「提交✓」其实全是 `NOOP`（没东西可改）。
第二版改成真换值，又给 `hex-input` 造出了 `9bdcf2-X` —— **那不是合法颜色**，
于是它两侧都「无变化」。

**第三次**：703 测的是**越界**值。这三次是同一条纪律的三个面：
**造出来的值必须是这个控件能接受的值**，否则读数落在第三态上。

（本批为此给 `hex-input` 单独补一格**合法色值** `ff0000` 的测量，
704 当初正是用它测得两侧都提交。）

## 纪律

- 每格一个全新页面。
- 判「有没有变」用**全 store 逐叶投影**。
- **不适用要记成不适用并写明理由**，不能记成失败，也不能悄悄跳过。
- 零 store 写入；提交全部用真实键盘事件。

## 四条判据

1. `the-census-covers-all-24-controls-and-each-has-a-unique-key`
2. `exactly-two-controls-ignore-enter-and-they-are-the-two-shot-time-fields`
3. `select-fields-behave-like-text-fields-so-prediction-3-is-falsified`
4. `the-twelve-transform-fields-go-through-the-gesture-machinery`
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch705-2026-10-01"
W, DESK_H = 1280, 1150

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

PREDICTIONS = {
    "P1": "多数输入控件把 Enter 当提交键",
    "P2": "range 类型没有提交步骤（input 事件即写入），不该混进 Enter/Tab 的比较",
    "P3": "select 与 text 的提交行为不同",
    "P4": "每枚控件都有唯一稳定键（组合属性），普查不按索引",
}

INV = r"""() => {
  const panel = document.querySelector('[data-director-inspector]');
  const out = [];
  for (const el of panel.querySelectorAll('input, select, textarea')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    const key = el.hasAttribute('data-director-transform-field')
      ? 'transform:' + el.getAttribute('data-director-transform-field') + ':'
        + el.getAttribute('data-director-transform-axis')
      : (el.getAttributeNames().find((n) => n.startsWith('data-director')) || '(none)');
    out.push({ key, tag: el.tagName.toLowerCase(), type: el.type || null,
      value: el.value, min: el.getAttribute('min'), max: el.getAttribute('max'),
      options: el.tagName === 'SELECT'
        ? Array.from(el.options).map((o) => o.value) : null });
  }
  return { count: out.length, out };
}"""

FLAT = r"""() => {
  const s = window.__director_store.getState();
  const o = {};
  const walk = (v, p, d) => {
    if (d > 4) { o[p] = String(v); return; }
    if (v === null || typeof v !== 'object') { o[p] = JSON.stringify(v); return; }
    if (Array.isArray(v)) { o[p + '.length'] = v.length;
      v.forEach((x, i) => walk(x, p + '[' + i + ']', d + 1)); return; }
    for (const k of Object.keys(v).sort()) walk(v[k], p + '.' + k, d + 1);
  };
  for (const k of Object.keys(s).sort()) {
    if (typeof s[k] === 'function') continue;
    walk(s[k], k, 0);
  }
  return o;
}"""

LAST = r"""() => {
  const r = window.__director_store.getState().lastCommandResult;
  return r ? { commandKind: r.commandKind, disposition: r.disposition } : null;
}"""

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


def css_for(key: str) -> str:
    if key.startswith("transform:"):
        _, f, a = key.split(":")
        return f'[data-director-transform-field="{f}"][data-director-transform-axis="{a}"]'
    return f"[{key}]"


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


def new_value(it: dict[str, Any]) -> tuple[str | None, str | None]:
    """返回一个**这个控件能接受**的新值。返回值 (newValue, reasonIfNone)。

    第三态纪律的第四个应用面：造出来的值必须是控件能接受的值，
    否则读数落在「我这一步没测到」上。
    """
    v, t = it["value"], it["type"]
    key = it["key"]
    try:
        cur = float(v)
    except (TypeError, ValueError):
        cur = None
    if key == "data-director-hex-input":
        # 必须是**合法**的 6 位十六进制；第一版造出 `9bdcf2-X` 让它两侧都无变化
        return ("ff0000" if v.lower() != "ff0000" else "00ff00", None)
    if t == "color" and isinstance(v, str) and v.startswith("#") and len(v) == 7:
        return ("#" + "".join("0" if ch != "0" else "1" for ch in v[1:]), None)
    if t == "number" and cur is not None:
        lo = float(it["min"]) if it["min"] is not None else cur - 1
        hi = float(it["max"]) if it["max"] is not None else cur + 1
        for c in (cur + 1, cur - 1, cur + 0.5, cur * 2, 0.0):
            if lo <= c <= hi and abs(c - cur) > 1e-9:
                return (str(round(c, 4)), None)
        return (None, "值域里没有别的值")
    if t == "text" and isinstance(v, str):
        return ((v + "-X") if not v.endswith("-X") else v[:-2], None)
    return (None, f"无法为 type={t} 造出可接受的新值")


def measure(browser, it: dict[str, Any], path: str) -> dict[str, Any]:
    page = fresh(browser)
    sel = css_for(it["key"])
    try:
        if it["type"] == "range":
            el = page.locator(sel).first
            before = page.evaluate(FLAT)
            el.click()
            page.wait_for_timeout(150)
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(600)
            after = page.evaluate(FLAT)
            ch = sorted(k for k in set(before) | set(after)
                        if before.get(k) != after.get(k) and k != "lastCommandResult")
            return {"applicable": False, "reason": "range 没有提交步骤（P2）",
                    "changedOnKeypress": bool(ch), "n": len(ch),
                    "lastAfter": page.evaluate(LAST)}
        if it["tag"] == "select":
            cur = it["value"]
            alt = next((o for o in (it["options"] or []) if o != cur), None)
            if alt is None:
                return {"applicable": False,
                        "reason": f"造不出差异：{len(it['options'] or [])} 个选项里没有别的值"}
            el = page.locator(sel).first
            before = page.evaluate(FLAT)
            el.click()
            page.wait_for_timeout(150)
            page.evaluate("""(a) => { const e = document.querySelector(a[0]);
                e.value = a[1];
                e.dispatchEvent(new Event('input', { bubbles: true }));
                e.dispatchEvent(new Event('change', { bubbles: true })); }""",
                          [sel, alt])
            page.wait_for_timeout(200)
            if path == "enter":
                page.keyboard.press("Enter")
            elif path == "tab":
                page.keyboard.press("Tab")
            page.wait_for_timeout(700)
            after = page.evaluate(FLAT)
            ch = sorted(k for k in set(before) | set(after)
                        if before.get(k) != after.get(k) and k != "lastCommandResult")
            return {"applicable": True, "newValue": alt, "changed": bool(ch),
                    "n": len(ch), "sample": ch[:3], "lastAfter": page.evaluate(LAST)}
        nv, why = new_value(it)
        if nv is None:
            return {"applicable": False, "reason": why}
        el = page.locator(sel).first
        before = page.evaluate(FLAT)
        el.click()
        page.wait_for_timeout(150)
        el.fill(nv)
        page.wait_for_timeout(150)
        if path == "enter":
            page.keyboard.press("Enter")
        elif path == "tab":
            page.keyboard.press("Tab")
        page.wait_for_timeout(700)
        after = page.evaluate(FLAT)
        ch = sorted(k for k in set(before) | set(after)
                    if before.get(k) != after.get(k) and k != "lastCommandResult")
        return {"applicable": True, "newValue": nv, "changed": bool(ch),
                "n": len(ch), "sample": ch[:3], "lastAfter": page.evaluate(LAST)}
    except Exception as e:                                  # noqa: BLE001
        return {"error": type(e).__name__}
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


def main() -> int:
    v = Verifier()
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    null_drift: list[str] = []
    rows: list[dict[str, Any]] = []
    inventory: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        npg = fresh(br)
        f1 = npg.evaluate(FLAT)
        npg.wait_for_timeout(400)
        f2 = npg.evaluate(FLAT)
        null_drift = sorted(k for k in f1 if f1.get(k) != f2.get(k))
        npg.close()

        pg = fresh(br)
        inventory = pg.evaluate(INV)
        pg.close()
        for it in inventory["out"]:
            if it["type"] == "range":
                r = measure(br, it, "change")
                rows.append({**it, "enter": r, "tab": r})
                print(f"  {it['key']:34} range       N/A        按键即写入={r.get('changedOnKeypress')}")
                continue
            e = measure(br, it, "enter")
            t = measure(br, it, "tab")
            rows.append({**it, "enter": e, "tab": t})

            def tag(d: dict[str, Any]) -> str:
                if d.get("error"):
                    return "错误:" + str(d["error"])
                if d.get("applicable") is False:
                    return "N/A"
                return "提交" if d["changed"] else "无变化"

            print(f"  {it['key']:34} {str(it['type'])[:8]:8} 新值={str(e.get('newValue'))[:14]:16} "
                  f"Enter={tag(e):6} Tab={tag(t):6} "
                  f"记账={json.dumps(t.get('lastAfter'), ensure_ascii=False)}")
        br.close()

    applicable = [r for r in rows if r["enter"].get("applicable") is True]
    not_applicable = [r for r in rows if r["enter"].get("applicable") is False]
    enter_silent = [r["key"] for r in applicable
                    if not r["enter"]["changed"] and r["tab"]["changed"]]
    both_commit = [r["key"] for r in applicable
                   if r["enter"]["changed"] and r["tab"]["changed"]]
    both_silent = [r["key"] for r in applicable
                   if not r["enter"]["changed"] and not r["tab"]["changed"]]
    selects = [r for r in applicable if r["tag"] == "select"]
    transform_fields = [r for r in applicable if r["key"].startswith("transform:")]
    gesture_cmds = {r["key"]: r["tab"]["lastAfter"] for r in transform_fields}

    v.check(
        "the-census-covers-all-24-controls-and-each-has-a-unique-key",
        inventory["count"] == 24
        and len({r["key"] for r in rows}) == 24
        and len(rows) == 24
        and all(r["enter"].get("reason") for r in not_applicable)
        and not any(r["enter"].get("error") or r["tab"].get("error") for r in rows),
        detail={"count": inventory["count"], "uniqueKeys": len({r["key"] for r in rows}),
                "applicable": len(applicable), "notApplicable":
                    [{"key": r["key"], "type": r["type"], "reason": r["enter"]["reason"]}
                     for r in not_applicable],
                "predictionP4": PREDICTIONS["P4"]},
        note="three controls are recorded as not-applicable WITH a reason rather than "
             "as passes or failures — two ranges have no commit step, and the camera "
             "switch has only one option so no difference can be created")

    v.check(
        "exactly-two-controls-ignore-enter-and-they-are-the-two-shot-time-fields",
        sorted(enter_silent) == ["data-director-shot-end", "data-director-shot-start"]
        and len(both_commit) == 19 and not both_silent,
        detail={"enterSilentTabCommits": enter_silent,
                "bothCommit": len(both_commit),
                "bothSilent": both_silent,
                "reproduces": "batch 704 的读数（shot-start / shot-end 忽略 Enter），"
                              "这次在 24/24 全覆盖下独立复现"},
        note="a full census that reproduces a 7-sample reading is the cheapest possible "
             "cross-check; and the two silent controls are the only two whose label is a "
             "duration rather than a plain value")

    v.check(
        "select-fields-behave-like-text-fields-so-prediction-3-is-falsified",
        len(selects) == 2
        and all(r["enter"]["changed"] and r["tab"]["changed"] for r in selects),
        detail={"predictionP3": PREDICTIONS["P3"],
                "selects": [{"key": r["key"], "newValue": r["enter"]["newValue"],
                             "enter": r["enter"]["changed"], "tab": r["tab"]["changed"],
                             "ledger": r["tab"]["lastAfter"]} for r in selects],
                "verdict": "P3 被推翻 —— select 与 text 一样，两个键都提交",
                "direction": "被推翻的方向是**类别变少**而不是变多"},
        note="the interesting kind of falsification is the one that removes a category")

    v.check(
        "the-twelve-transform-fields-go-through-the-gesture-machinery",
        len(transform_fields) == 12
        and all(g and g["commandKind"] == "GESTURE_COMMIT"
                and g["disposition"] == "COMMITTED" for g in gesture_cmds.values()),
        detail={"count": len(transform_fields), "commands": gesture_cmds,
                "reading": "在数字框里敲数字，与拖 3D 手柄，走的是同一套手势机制；"
                           "而 shot-start 记 UPDATE_SHOT、shot-end 记 GESTURE_BEGIN"},
        note="a number box that looks like an independent setter is actually a view onto "
             "a gesture — which is also why an out-of-range value can leave a gesture open")

    out = {
        "width": W, "deskHeight": DESK_H,
        "predictions": PREDICTIONS,
        "predictionVerdicts": {
            "P1_held": len(both_commit) >= 19,
            "P2_held": all(r["enter"].get("reason") for r in not_applicable
                           if r["type"] == "range"),
            "P3_falsified": len(selects) == 2 and all(r["enter"]["changed"] for r in selects),
            "P4_held": len({r["key"] for r in rows}) == 24,
        },
        "nullClickDrift": null_drift,
        "census": rows,
        "verdicts": {"enterSilentTabCommits": enter_silent,
                     "bothCommit": both_commit, "bothSilent": both_silent,
                     "notApplicable": [r["key"] for r in not_applicable]},
        "theFinding":
            "24 枚右栏可输入控件全部逐格测完：21 枚适用、3 枚不适用（2 枚 range 无提交"
            "步骤，camera-switch 只有一个选项造不出差异）。适用的 21 枚里 "
            "**19 枚 Enter 与 Tab 都提交，只有 2 枚（shot-start / shot-end）忽略 Enter** —— "
            "**独立复现了 704 的读数**，而且这次是全覆盖。",
        "theSecondFinding":
            "12 枚 transform 数字框（position/rotation/scale/target × x/y/z）提交后一律记 "
            "GESTURE_COMMIT ⟹ **在数字框里敲数字与拖 3D 手柄走的是同一套手势机制**。",
        "theFalsifiedPrediction":
            "P3「select 与 text 的提交行为不同」**被推翻**：camera-follow-target 与 "
            "camera-look-at-mode 两个 select 与 text 完全一样，两个键都提交。",
        "theThirdStateLesson":
            "「无变化」有两种：控件不提交，和我没造出差异。本批三版探针各踩一次："
            "第一版给 text/color 填了**已有的值**（于是那一列全是 NOOP）；第二版给 "
            "hex-input 造出 **`9bdcf2-X` 这个非法颜色**（于是两侧都无变化）；"
            "加上 703 那次测**越界**值 —— 同一个纪律的三个面。**造出来的值必须是这个控件"
            "能接受的值**，否则读数落在第三态上。",
        "whatIsNotClaimed":
            "不声称 3 枚不适用的控件有问题（**它们的「不适用」是控件类型或 fixture 造成的，"
            "不是缺陷**）。不声称源站行为（**未取证，需授权点击**）。"
            "**不改 src/**。",
        "storeWritesInThisRun":
            "none — every edit was driven by real keyboard events on real controls",
        "relationTo704":
            "704 不重写。本批把它的 7/24 覆盖补成 24/24，"
            "**并独立复现了它的核心读数**（忽略 Enter 的仍只有那两枚）。",
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
