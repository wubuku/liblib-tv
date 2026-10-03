#!/usr/bin/env python3
"""batch 708 验收：18 个「到不了」的格子里浏览器自己做了什么（instead-of 全表）

## 起点

707 建了一张可达性全表：焦点在可编辑控件上时 6 个快捷键全部到不了导演台。
但那 18 格只判了「**应用没动**」，**没判浏览器自己做了什么** ——
而 706 已经证明在一种状态下浏览器会接管那次按键。

**「到不了」和「什么也没发生」是两句话。** 本批补上表里缺的「instead of」那一列。

## 六条预测（写死在代码里，先于任何测量）

- **P1** `Backspace` 在文本框里删一个字符，`Delete` 在文本框里什么也不做
- **P2** `Backspace` / `Delete` 在滑块与下拉里什么也不做
- **P3** `Escape` 在文本框/下拉里什么也不做，在滑块里取消手势
- **P4** `Meta+z` 的 hijack **不是滑块特有**：三个可编辑焦点都会中招
- **P5** `Meta+Shift+z` / `Meta+y` 是 hijack 的镜像（redo 同样会被浏览器接管）
- **P6** hijack 之后字段 DOM 与 store 不同步，而账上看不出发生过任何事

## 结果：五条成立，一条被推翻

- **P1–P4、P6 成立。**
- **P5 被推翻**：**两枚 redo 键在 36 格里一次都没有 hijack。**
  ⟹ 用户能触发浏览器那次静默回退，**却没有任何键能把它撤回来** ——
  陷阱是单向的。这是本批最值钱的一条。

## 全表（36 格 = 3 可编辑焦点 × 6 键 × 2 前置状态，每格全新页面）

| 前置状态 ＼ 焦点 | `Meta+z` | `Meta+Shift+z` | `Meta+y` | `Delete` | `Backspace` | `Escape` |
|---|---|---|---|---|---|---|
| **干净** 文本框 | 什么也没做 | 什么也没做 | 什么也没做 | **什么也没做** | **删一个字符** | 什么也没做 |
| **干净** 滑块 | 什么也没做 | 什么也没做 | 什么也没做 | 什么也没做 | 什么也没做 | **取消手势** |
| **干净** 下拉 | 什么也没做 | 什么也没做 | 什么也没做 | 什么也没做 | 什么也没做 | 什么也没做 |
| **键入过·中途没点画布** 文本框 | **hijack（就地）** | 什么也没做 | 什么也没做 | 什么也没做 | 删一个字符 | 什么也没做 |
| **键入过·中途没点画布** 滑块 | **hijack（焦点跳走 + 关手势）** | 什么也没做 | 什么也没做 | 什么也没做 | 什么也没做 | **取消手势** |
| **键入过·中途没点画布** 下拉 | **hijack（焦点跳走）** | 什么也没做 | 什么也没做 | 什么也没做 | 什么也没做 | 什么也没做 |

**「干净」那一列 18 格里有 17 格真的什么也没发生** ——
唯一例外是文本框里的 `Backspace`（浏览器正常删字符，良性且符合预期）。
**浏览器真正越俎代庖的只有 `Meta+z` 那一列的 3 格。**

## 顺带纠正 707 的一处收窄

707 的 hijack 子普查**只测了滑块那一列**，于是把触发条件写成「键入过 且 中途没点过非可编辑表面」。
那两条**都仍然成立**，但形状随焦点位置变：

- **文本框聚焦**：浏览器就地撤销**焦点所在那个字段** ⟹ 焦点不动，用户看见自己的编辑凭空消失，
  而 **store 里还是新值**。
- **滑块 / 下拉聚焦**：浏览器撤销的是**另一个字段** ⟹ **焦点被挪到那个字段**，
  滑块那一列还顺手把手势提交掉。

**三种焦点下共同的读数是：字段 DOM 与 store 不同步，而账上没有任何 `UNDO`。**

## 六条判据

1. `backspace-deletes-a-character-in-a-text-field-while-delete-does-nothing`
2. `delete-and-backspace-do-nothing-in-a-slider-or-a-select`
3. `escape-does-nothing-in-text-and-select-but-cancels-the-gesture-in-a-slider`
4. `the-form-undo-hijack-hits-all-three-editable-focus-types-not-just-sliders`
5. `neither-redo-key-hijacks-in-any-cell-so-the-trap-is-one-way`
6. `after-the-hijack-the-dom-is-out-of-sync-with-the-store-and-no-undo-is-ledgered`

## 纪律

- 每格一个全新页面；真实键盘事件；零 store 写入；不改 `src/`。
- 判「浏览器做了什么」要读 **DOM 值 + 选区 + 文档级 selection**，不能只读 store ——
  本批的核心现象**只发生在 DOM 上**，只读 store 的话它等于没发生。
- 每格断言焦点真的到位；到位不了就报错，不产出一格读数（707 立的那条）。
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch708-2026-10-01"
W, DESK_H = 1280, 1150

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

PREDICTIONS = {
    "P1": "Backspace 在文本框里删一个字符，Delete 在文本框里什么也不做",
    "P2": "Backspace / Delete 在滑块与下拉里什么也不做",
    "P3": "Escape 在文本框/下拉里什么也不做，在滑块里取消手势",
    "P4": "Meta+z 的 hijack 不是滑块特有：三个可编辑焦点都会中招",
    "P5": "Meta+Shift+z / Meta+y 是 hijack 的镜像",
    "P6": "hijack 之后 DOM 与 store 不同步，而账上看不出发生过任何事",
}

READ = r"""() => {
  const s = window.__director_store.getState();
  const h = s.history; const r = s.lastCommandResult;
  const ae = document.activeElement;
  const q = (x) => document.querySelector(x);
  const n = q('[data-director-object-name]');
  const f = q('[data-director-camera-fov]');
  return {
    pastLen: (h.past || []).length, futureLen: (h.future || []).length,
    active: h.activeGesture ? h.activeGesture.commandKind : null,
    last: r ? r.commandKind + '/' + r.disposition : null,
    focus: ae ? (ae.getAttributeNames()
      .filter((k) => k.startsWith('data-director')).sort().join(',') || ae.tagName)
      : 'none',
    editable: ae ? !!(ae.isContentEditable || ['INPUT','TEXTAREA','SELECT']
      .includes(ae.tagName)) : false,
    nameDom: n ? n.value : null,
    nameSel: n ? [n.selectionStart, n.selectionEnd] : null,
    nameStore: (s.objects.find((o) => o.id === s.selectedObjectId) || {}).name,
    fovDom: f ? f.value : null,
    fovStore: ((s.objects.find((o) => o.kind === 'camera') || {}).camera || {}).fov,
    objectsLen: s.objects.length,
    selectedText: (function () {
      const a = window.getSelection();
      return a ? String(a) : '';
    })(),
  };
}"""

SEL_CAMERA = r"""() => {
  const s = window.__director_store.getState();
  const c = s.objects.find((o) => o.kind === 'camera');
  document.querySelector('[data-director-tree] [role="treeitem"][data-director-object-id="'
    + c.id + '"]').click();
  return window.__director_store.getState().selectedObjectId === c.id;
}"""

FOCI = ("text-input", "range", "select")
KEYS = ("Meta+z", "Meta+Shift+z", "Meta+y", "Delete", "Backspace", "Escape")
VARIANTS = ("clean", "typed-no-canvas")
FOCUS_EXPECT = {
    "text-input": "data-director-object-name",
    "range": "data-director-camera-fov",
    "select": "data-director-camera-switch",
}
TRACKED = ("nameDom", "nameStore", "nameSel", "fovDom", "fovStore",
           "objectsLen", "selectedText")
TYPED_NAME = "改名试试708AB"


class Instrument(Exception):
    pass


def read(page: Page) -> dict[str, Any]:
    return page.evaluate(READ)


def fresh(browser: Any) -> Page:
    page = browser.new_page(viewport={"width": W, "height": DESK_H},
                            device_scale_factor=1)
    b617.open_desk(page)
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(300)
    if not page.evaluate(SEL_CAMERA):
        raise Instrument("选不中机位")
    page.wait_for_timeout(500)
    return page


def rename(page: Page) -> None:
    el = page.locator("[data-director-object-name]").first
    el.click()
    page.wait_for_timeout(200)
    el.fill(TYPED_NAME)
    el.press("Tab")
    page.wait_for_timeout(600)


def set_focus(page: Page, focus: str) -> None:
    if focus == "text-input":
        page.locator("[data-director-object-name]").first.click()
        page.wait_for_timeout(350)
    elif focus == "select":
        page.locator("[data-director-camera-switch]").first.click()
        page.wait_for_timeout(350)
    elif focus == "range":
        el = page.locator("[data-director-shot-end]").first
        el.click()
        page.wait_for_timeout(200)
        el.press("Tab")
        page.wait_for_timeout(500)
    else:
        raise ValueError(focus)


def cell(browser: Any, variant: str, focus: str, key: str) -> dict[str, Any]:
    page = fresh(browser)
    if variant == "typed-no-canvas":
        rename(page)          # 707 隔离出的前置条件：键入过，且中途不点非可编辑表面
    set_focus(page, focus)
    before = read(page)
    if FOCUS_EXPECT[focus] not in before["focus"]:
        raise Instrument(f"{variant}/{focus}/{key}: 焦点没到位 {before['focus']}")
    page.keyboard.press(key)
    page.wait_for_timeout(900)
    after = read(page)
    page.close()
    changed = sorted(k for k in TRACKED if before[k] != after[k])
    hijack = "nameDom" in changed and before["nameDom"] is not None \
        and after["nameDom"] is not None
    return {"variant": variant, "focus": focus, "key": key,
            "focusBefore": before["focus"], "focusAfter": after["focus"],
            "focusMoved": before["focus"] != after["focus"],
            "gestureBefore": before["active"], "gestureAfter": after["active"],
            "gestureClosed": bool(before["active"]) and not after["active"],
            "historyDelta": (after["pastLen"] - before["pastLen"],
                             after["futureLen"] - before["futureLen"]),
            "appCommandRan": before["last"] != after["last"],
            "lastBefore": before["last"], "lastAfter": after["last"],
            "changed": changed, "domReverted": hijack,
            "nameDom": [before["nameDom"], after["nameDom"]],
            "nameStore": [before["nameStore"], after["nameStore"]],
            "fovDom": [before["fovDom"], after["fovDom"]]}


def census(browser: Any) -> list[dict[str, Any]]:
    out = []
    for variant in VARIANTS:
        for focus in FOCI:
            for key in KEYS:
                c = cell(browser, variant, focus, key)
                out.append(c)
                print(f"[{variant:14s}][{focus:11s}] {key:12s} "
                      f"DOM回退={str(c['domReverted']):5s} "
                      f"变了={str(c['changed']):40s} 焦点动={str(c['focusMoved']):5s} "
                      f"手势关={str(c['gestureClosed']):5s} "
                      f"应用命令={str(c['appCommandRan']):5s} 账={c['lastAfter']}")
    return out


def check_1(table: dict[tuple[str, str, str], dict[str, Any]]) -> None:
    for variant in VARIANTS:
        bs = table[(variant, "text-input", "Backspace")]
        assert "nameDom" in bs["changed"] and "nameSel" in bs["changed"], bs
        assert bs["nameDom"][1] == bs["nameDom"][0][:-1], bs   # 真的少了一个字符
        dl = table[(variant, "text-input", "Delete")]
        assert dl["changed"] == [], dl


def check_2(table: dict[tuple[str, str, str], dict[str, Any]]) -> None:
    for variant in VARIANTS:
        for focus in ("range", "select"):
            for key in ("Delete", "Backspace"):
                c = table[(variant, focus, key)]
                assert c["changed"] == [], (variant, focus, key, c)


def check_3(table: dict[tuple[str, str, str], dict[str, Any]]) -> None:
    for variant in VARIANTS:
        for focus in ("text-input", "select"):
            c = table[(variant, focus, "Escape")]
            assert c["changed"] == [] and not c["appCommandRan"], (variant, focus, c)
        c = table[(variant, "range", "Escape")]
        assert c["gestureBefore"] == "camera-fov", c
        assert c["gestureAfter"] is None and c["gestureClosed"], c
        assert c["lastAfter"] == "GESTURE_CANCEL/NOOP", c
        assert c["changed"] == [], c


def check_4(table: dict[tuple[str, str, str], dict[str, Any]]) -> None:
    for focus in FOCI:
        c = table[("typed-no-canvas", focus, "Meta+z")]
        assert c["domReverted"], (focus, c)
        assert c["nameStore"][0] == c["nameStore"][1], (focus, c)
    for focus in FOCI:
        c = table[("clean", focus, "Meta+z")]
        assert not c["domReverted"], (focus, c)
    # 文本框里就地撤销（焦点不动），滑块/下拉里焦点被挪走
    assert not table[("typed-no-canvas", "text-input", "Meta+z")]["focusMoved"]
    for focus in ("range", "select"):
        assert table[("typed-no-canvas", focus, "Meta+z")]["focusMoved"], focus
    assert table[("typed-no-canvas", "range", "Meta+z")]["gestureClosed"]


def check_5(table: dict[tuple[str, str, str], dict[str, Any]]) -> None:
    hits = [k for k, c in table.items()
            if k[2] in ("Meta+Shift+z", "Meta+y") and c["domReverted"]]
    assert hits == [], f"redo 键也 hijack 了：{hits}"


def check_6(table: dict[tuple[str, str, str], dict[str, Any]]) -> None:
    for focus in FOCI:
        c = table[("typed-no-canvas", focus, "Meta+z")]
        assert c["nameDom"][0] != c["nameDom"][1], (focus, c)
        assert c["nameStore"][0] == c["nameStore"][1], (focus, c)
        assert c["lastAfter"] != "UNDO/COMMITTED", (focus, c)
        assert c["historyDelta"] in ((0, 0), (1, 0)), (focus, c)


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {"predictions": PREDICTIONS}
    failures: list[str] = []
    table: dict[tuple[str, str, str], dict[str, Any]] = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            cells = census(browser)
            results["census"] = cells
            table = {(c["variant"], c["focus"], c["key"]): c for c in cells}
        except Exception as exc:  # noqa: BLE001
            failures.append(f"census: {exc}")
        browser.close()

    checks = [
        ("backspace-deletes-a-character-in-a-text-field-while-delete-does-nothing",
         lambda: check_1(table)),
        ("delete-and-backspace-do-nothing-in-a-slider-or-a-select", lambda: check_2(table)),
        ("escape-does-nothing-in-text-and-select-but-cancels-the-gesture-in-a-slider",
         lambda: check_3(table)),
        ("the-form-undo-hijack-hits-all-three-editable-focus-types-not-just-sliders",
         lambda: check_4(table)),
        ("neither-redo-key-hijacks-in-any-cell-so-the-trap-is-one-way", lambda: check_5(table)),
        ("after-the-hijack-the-dom-is-out-of-sync-with-the-store-and-no-undo-is-ledgered",
         lambda: check_6(table)),
    ]
    summary: dict[str, bool] = {}
    for name, fn in checks:
        try:
            fn()
            summary[name] = True
        except Exception as exc:  # noqa: BLE001
            summary[name] = False
            failures.append(f"{name}: {exc}")
    results["summary"] = summary
    results["failures"] = failures
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1, default=str))
    for name, ok in summary.items():
        print(("PASS " if ok else "FAIL ") + name)
    for f in failures:
        print("  ->", f[:500])
    print(f"\n{sum(1 for v in summary.values() if v)}/{len(summary)} 通过")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
