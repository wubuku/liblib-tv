#!/usr/bin/env python3
"""batch 707 验收：输入框聚焦时导演台里哪些命令到不了 —— 4 焦点 × 6 快捷键全表

## 起点

706 查出一件事：焦点在任一输入框内时 `Cmd+Z` **到不了** `undoDirector`
（`DirectorDesk.tsx:484` 的 `if (isEditable) return;` 排在修饰键分支之前），
而且在一种特定状态下**浏览器的表单撤销会顶替这次按键** ——
把旧值塞进另一个字段的 DOM、把焦点挪过去、顺手把开着的手势提交成一条条目。

706 只测了 `Cmd+Z` 一条、一个焦点位置。**一条读数不是一张表。**

## 五条预测（写死在代码里，先于任何测量）

- **P1** 6 个全局快捷键在**任何**可编辑控件聚焦时都到不了（同一道 `isEditable` 早退）
- **P2** 6 个在面板聚焦时**全部**到得了
- **P3** `Meta+Shift+z` 与 `Meta+y` 是同一动作的别名（两枚 redo 键位）
- **P4** `Delete` 与 `Backspace` 共用一个分支
- **P5** 706 那条「浏览器表单撤销顶替」的触发条件是「文档表单历史里有过键入」

## 结果

- **P1、P2、P3、P4 全部成立** ⟹ 可达性完全由「焦点在不在可编辑控件上」决定，
  **18 个「到不了」的格、6 个「到得了」的格，一条例外都没有漏。**
- **唯一的例外不是漏网，是另一套处理器**：`range` 聚焦时 `Escape` **能到** ——
  到的是手势边界（`GESTURE_CANCEL`），不是导演台（导演台还开着）。
- **P5 被推翻**：触发条件比 706 写的窄，而且**是两个变量的与** ——
  必须**键入过**（不键入那臂不 hijack）**且**焦点是**键盘**走到滑块的、
  **中途没点过非可编辑表面**（点画布那两臂都不 hijack）。
  **方向键按不按都无所谓** —— 这一格 706 没测过。
  ⟹ **706 的读数全部存活，但它对触发条件的描述要收窄成「与」。**

## 本批自己踩的坑：普查器的备料错了两次，而且两次都伪装成读数

1. **`set_focus("panel")` 点 treeitem 并不把焦点拿过去**（`role="treeitem"` 不可聚焦）
   ⟹ 头三行 undo/redo 的焦点其实还在可编辑控件上，那三格是「我没造出差异」。
2. **`Delete` 备料改用「可删对象」后，选中让 `shot-end` 字段消失**
   ⟹ range 那一列直接 Timeout。**读面不存在，不是控件惰性。**
   最后一版改用**被守卫保护的机位当备料**：`REJECTED` 本身就证明按键到了，
   不需要真删东西（也就不需要换选中、不会让字段消失）。
3. **`focus_panel` 的最后一步会重新选回机位** —— 我自己把这个副作用忘了两次，
   直到补充格删掉的是机位（理由 `DIRECTOR_LAST_CAMERA_REQUIRED`）才暴露出来。
4. **四条预测写下来了，但普查器的「设焦点」没有断言** ⟹ 前三条坑全部是
   「仪器没到位」伪装成「控件到不了」。本版每格都断言焦点真的到位，
   不到位就**报错**而不是产出一格读数（仪器未到位 ≠ 读数）。

## 纪律

- 每格一个全新页面；全部真实键盘/鼠标事件；零 store 写入；不改 `src/`。
- 剪贴板类键（`Cmd+C` / `Cmd+V`）**记成不适用**：它们会写系统剪贴板，
  属外部可见状态变更，未获授权。方向键**不测**：源码里没有任何方向键绑定 ——
  那是「无绑定」，不是「到不了」，两回事。
- 判「命令到没到」用**账上最后一条命令是否变化**，不只看 store。

## 七条判据

1. `every-shortcut-is-blocked-while-any-editable-control-has-focus`
2. `all-six-shortcuts-reach-the-desk-when-the-focus-is-on-the-panel`
3. `delete-and-backspace-share-one-command-branch`
4. `the-two-redo-keys-are-aliases`
5. `the-browser-form-undo-hijack-needs-a-prior-text-edit-and-no-canvas-click-in-between`
6. `escape-reaches-the-gesture-boundary-not-the-desk-while-a-slider-has-focus`
7. `delete-on-a-deletable-object-actually-deletes-so-rejected-is-not-always-rejected`
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch707-2026-10-01"
W, DESK_H = 1280, 1150

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

PREDICTIONS = {
    "P1": "6 个全局快捷键在任何可编辑控件聚焦时都到不了",
    "P2": "6 个在面板聚焦时全部到得了",
    "P3": "Meta+Shift+z 与 Meta+y 是同一动作的别名",
    "P4": "Delete 与 Backspace 共用一个分支",
    "P5": "浏览器表单撤销的触发条件是「文档表单历史里有过键入」（706 的说法）",
}

READ = r"""() => {
  const s = window.__director_store.getState();
  const h = s.history; const r = s.lastCommandResult;
  const ae = document.activeElement;
  const q = (sel) => document.querySelector(sel);
  return {
    pastLen: (h.past || []).length,
    futureLen: (h.future || []).length,
    active: h.activeGesture ? h.activeGesture.commandKind : null,
    last: r ? { commandKind: r.commandKind, disposition: r.disposition,
      reason: r.reason, historyEntries: r.historyEntries } : null,
    focus: ae ? (ae.getAttributeNames()
      .filter((n) => n.startsWith('data-director')).sort().join(',') || ae.tagName)
      : 'none',
    editable: ae ? !!(ae.isContentEditable || ['INPUT','TEXTAREA','SELECT']
      .includes(ae.tagName)) : false,
    objectsLen: s.objects.length,
    nameDom: (q('[data-director-object-name]') || {}).value,
    nameStore: (s.objects.find((o) => o.id === s.selectedObjectId) || {}).name,
    fovDom: (q('[data-director-camera-fov]') || {}).value,
    fovStore: ((s.objects.find((o) => o.kind === 'camera') || {}).camera || {}).fov,
    deskOpen: !!q('[data-director-workspace]'),
  };
}"""

SELECT_BY_ID = r"""(id) => {
  const s = window.__director_store.getState();
  const target = id || (s.objects.find((o) => o.kind === 'camera') || {}).id;
  if (!target) return { ok: false, stage: 'no-id' };
  const row = document.querySelector('[data-director-tree] [role="treeitem"]'
    + '[data-director-object-id="' + target + '"]');
  if (!row) return { ok: false, stage: 'no-row', id: target };
  row.click();
  const after = window.__director_store.getState();
  return { ok: after.selectedObjectId === target
    || after.selectedObjectIds.indexOf(target) >= 0, id: target,
    locked: !!(s.objects.find((o) => o.id === target) || {}).locked };
}"""

FOCI = ("text-input", "range", "select", "panel")
KEYS = ("Meta+z", "Meta+Shift+z", "Meta+y", "Delete", "Backspace", "Escape")
EDITABLE_FOCI = ("text-input", "range", "select")
FOCUS_EXPECT = {
    "text-input": ("data-director-object-name", True),
    "range": ("data-director-camera-fov", True),
    "select": ("data-director-camera-switch", True),
    "panel": ("data-director-workspace", False),
}
NOT_APPLICABLE = [
    "Cmd+C / Cmd+V：会写系统剪贴板，属外部可见状态变更，未获授权",
    "方向键：源码里没有任何方向键绑定 —— 那是「无绑定」不是「到不了」",
]


class Instrument(Exception):
    """仪器没到位。宁可报错，也不要让第三态伪装成读数。"""


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
    ok = page.evaluate(SELECT_BY_ID, None)
    if not ok["ok"]:
        raise Instrument(f"选不中机位：{ok}")
    page.wait_for_timeout(500)
    return page


def focus_panel(page: Page, reselect: str | None = None) -> None:
    """点画布把焦点交给面板（`role="treeitem"` 不可聚焦，点它不动焦点）；
    点画布空白会取消选中、右栏随之卸载，所以再点一次 treeitem 把选中恢复回来。

    注意最后那一步会**重新选中**（默认机位）—— 这个副作用本批踩了两次。
    """
    page.mouse.click(640, 900)
    page.wait_for_timeout(500)
    page.evaluate(SELECT_BY_ID, reselect)
    page.wait_for_timeout(400)


def focus_by_name(page: Page, focus: str) -> None:
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
    elif focus == "panel":
        focus_panel(page)
    else:
        raise ValueError(focus)


def assert_focus(page: Page, focus: str) -> dict[str, Any]:
    r = read(page)
    want, want_editable = FOCUS_EXPECT[focus]
    if want not in r["focus"]:
        raise Instrument(f"{focus}: 焦点没到位，实际 {r['focus']}")
    if r["editable"] != want_editable:
        raise Instrument(f"{focus}: editable 期望 {want_editable}，实际 {r['editable']}")
    return r


def rename(page: Page) -> None:
    el = page.locator("[data-director-object-name]").first
    el.click()
    page.wait_for_timeout(200)
    el.fill("改名试试707")
    el.press("Tab")
    page.wait_for_timeout(600)


def cell(browser: Any, focus: str, key: str) -> dict[str, Any]:
    page = fresh(browser)
    prep = "none"
    if key in ("Meta+z", "Meta+Shift+z", "Meta+y"):
        rename(page)
        prep = "rename"
        focus_panel(page)          # 备料的撤销/重做必须在非可编辑焦点下发生
        assert_focus(page, "panel")
        if key != "Meta+z":
            page.keyboard.press("Meta+z")
            page.wait_for_timeout(700)
            if read(page)["futureLen"] < 1:
                raise Instrument(f"{key}: 备料那次撤销没生效")
            prep = "rename+undo"
    if key in ("Delete", "Backspace"):
        # 备料用**被守卫保护的机位**：命令会跑并记 REJECTED，
        # 而 REJECTED 本身就证明按键到了导演台，不需要真删东西。
        prep = "select-guarded-camera"
        page.evaluate(SELECT_BY_ID, None)
        page.wait_for_timeout(400)
    focus_by_name(page, focus)
    before = assert_focus(page, focus)
    page.keyboard.press(key)
    page.wait_for_timeout(900)
    after = read(page)
    page.close()
    return {"focus": focus, "key": key, "prep": prep,
            "editable": before["editable"],
            "beforeLast": before["last"], "afterLast": after["last"],
            "historyDelta": (after["pastLen"] - before["pastLen"],
                             after["futureLen"] - before["futureLen"]),
            "focusBefore": before["focus"], "focusAfter": after["focus"],
            "gestureBefore": before["active"], "gestureAfter": after["active"],
            "objectsBefore": before["objectsLen"], "objectsAfter": after["objectsLen"],
            "nameDom": [before["nameDom"], after["nameDom"]],
            "nameStore": [before["nameStore"], after["nameStore"]],
            "deskOpenAfter": after["deskOpen"],
            "commandRan": before["last"] != after["last"]}


def census(browser: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for focus in FOCI:
        for key in KEYS:
            c = cell(browser, focus, key)
            out.append(c)
            print(f"[{focus:11s}] {key:12s} prep={c['prep']:20s} "
                  f"账={(c['afterLast'] or {}).get('commandKind')}/"
                  f"{(c['afterLast'] or {}).get('disposition')}/"
                  f"{(c['afterLast'] or {}).get('reason')} "
                  f"命令={str(c['commandRan']):5s} 历史Δ={c['historyDelta']} "
                  f"焦点动={c['focusBefore'] != c['focusAfter']} "
                  f"手势 {c['gestureBefore']}->{c['gestureAfter']} "
                  f"对象 {c['objectsBefore']}->{c['objectsAfter']} "
                  f"台还开={c['deskOpenAfter']}")
    return out


def pick(browser: Any) -> dict[str, list[dict[str, Any]]]:
    table = {(c["focus"], c["key"]): c for c in census(browser)}
    return table


# ---------------------------------------------------------------- 子普查
HIJACK_ARMS = (
    # (臂名, 改名?, 方向键?, 中途点画布?, 期望 hijack)
    ("rename+arrow+no-canvas", True, True, False, True),
    ("rename+no-arrow+no-canvas", True, False, False, True),
    ("rename+arrow+canvas-click", True, True, True, False),
    ("no-rename+arrow+no-canvas", False, True, False, False),
    ("rename+arrow+canvas+back", True, True, True, False),
)


def hijack_arms(browser: Any) -> list[dict[str, Any]]:
    """706 说触发条件是「文档表单历史里有过键入」。本批测五个状态，看它到底有多窄。

    隔离出来的变量不是「有没有键入」一个，而是两个：
    **键入过**（`no-rename` 那臂不 hijack）**且**
    **焦点是键盘走到滑块的、中间没点过非可编辑表面**（`canvas-click` 那两臂不 hijack）。
    方向键按不按都无所谓（`no-arrow` 那臂照样 hijack）—— 这一条 706 也没测过。
    """
    out = []
    for name, do_rename, do_arrow, do_canvas, expect in HIJACK_ARMS:
        page = fresh(browser)
        if do_rename:
            rename(page)
        if do_canvas:
            focus_panel(page)
        focus_by_name(page, "range")
        if do_arrow:
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(350)
        if name.endswith("canvas+back"):
            focus_panel(page)          # 方向键之后点画布，再走回滑块
            focus_by_name(page, "range")
        before = assert_focus(page, "range")
        page.keyboard.press("Meta+z")
        page.wait_for_timeout(900)
        after = read(page)
        page.close()
        rec = {"arm": name, "expectHijack": expect,
               "renamed": do_rename, "arrowed": do_arrow,
               "canvasClickInBetween": do_canvas,
               "focusBefore": before["focus"], "focusAfter": after["focus"],
               "focusMoved": before["focus"] != after["focus"],
               "nameDom": [before["nameDom"], after["nameDom"]],
               "nameStore": [before["nameStore"], after["nameStore"]],
               "fovDom": [before["fovDom"], after["fovDom"]],
               "gestureBefore": before["active"], "gestureAfter": after["active"],
               "historyDelta": (after["pastLen"] - before["pastLen"],
                                after["futureLen"] - before["futureLen"]),
               "afterLast": after["last"]}
        out.append(rec)
        print(f"[{name:26s}] 期望hijack={str(expect):5s} 实测焦点动={rec['focusMoved']} "
              f"nameDom {rec['nameDom']} nameStore {rec['nameStore']} "
              f"账={(rec['afterLast'] or {}).get('commandKind')}/"
              f"{(rec['afterLast'] or {}).get('disposition')} 历史Δ={rec['historyDelta']}")
    return out


def delete_works(browser: Any) -> dict[str, Any]:
    """补充格：面板焦点 + 真正可删的对象，Delete 确实删得掉 ——
    证明 REJECTED 不是「这个键永远被拒」，而是「机位受守卫保护」。"""
    page = fresh(browser)
    picked = page.evaluate(
        r"""() => {
          const s = window.__director_store.getState();
          const o = s.objects.find((x) => x.kind !== 'camera');
          const row = document.querySelector('[data-director-tree] [role="treeitem"]'
            + '[data-director-object-id="' + o.id + '"]');
          row.click();
          const after = window.__director_store.getState();
          return { id: o.id, name: o.name,
            selected: after.selectedObjectId === o.id
              || after.selectedObjectIds.indexOf(o.id) >= 0 };
        }""")
    page.wait_for_timeout(400)
    if not picked["selected"]:
        raise Instrument(f"补充格：备料没选中 {picked}")
    focus_panel(page, reselect=picked["id"])
    before = assert_focus(page, "panel")
    page.keyboard.press("Delete")
    page.wait_for_timeout(900)
    after = read(page)
    page.close()
    return {"picked": picked, "objectsBefore": before["objectsLen"],
            "objectsAfter": after["objectsLen"], "afterLast": after["last"],
            "historyDelta": (after["pastLen"] - before["pastLen"],
                             after["futureLen"] - before["futureLen"])}


# ---------------------------------------------------------------- 判据
def check_1(table: dict[tuple[str, str], dict[str, Any]]) -> None:
    for focus in EDITABLE_FOCI:
        for key in KEYS:
            c = table[(focus, key)]
            if focus == "range" and key == "Escape":
                continue          # 判据 6 单独验这一格
            assert not c["commandRan"], (
                f"{focus}/{key}: 可编辑焦点下竟然有命令跑了 {(c['afterLast'] or {})}")
            assert c["historyDelta"] == (0, 0), (
                f"{focus}/{key}: 历史被改了 {c['historyDelta']}")


def check_2(table: dict[tuple[str, str], dict[str, Any]]) -> None:
    z = table[("panel", "Meta+z")]
    assert z["afterLast"]["commandKind"] == "UNDO", z["afterLast"]
    assert z["historyDelta"] == (-1, 1), z["historyDelta"]
    for key in ("Meta+Shift+z", "Meta+y"):
        c = table[("panel", key)]
        assert c["afterLast"]["commandKind"] == "REDO", (key, c["afterLast"])
        assert c["historyDelta"] == (1, -1), (key, c["historyDelta"])
    for key in ("Delete", "Backspace"):
        c = table[("panel", key)]
        assert c["afterLast"]["commandKind"] == "DELETE_OBJECTS", (key, c["afterLast"])
        assert c["afterLast"]["disposition"] == "REJECTED", (key, c["afterLast"])
        assert c["afterLast"]["reason"] == "DIRECTOR_LAST_CAMERA_REQUIRED", \
            (key, c["afterLast"])
    esc = table[("panel", "Escape")]
    assert esc["deskOpenAfter"] is False, esc


def check_3(table: dict[tuple[str, str], dict[str, Any]]) -> None:
    d = table[("panel", "Delete")]
    b = table[("panel", "Backspace")]
    assert d["afterLast"] == b["afterLast"], (d["afterLast"], b["afterLast"])
    assert d["historyDelta"] == b["historyDelta"], (d, b)
    for focus in EDITABLE_FOCI:
        assert table[(focus, "Delete")]["afterLast"] == \
            table[(focus, "Backspace")]["afterLast"], focus


def check_4(table: dict[tuple[str, str], dict[str, Any]]) -> None:
    a = table[("panel", "Meta+Shift+z")]
    y = table[("panel", "Meta+y")]
    assert a["afterLast"] == y["afterLast"], (a["afterLast"], y["afterLast"])
    assert a["historyDelta"] == y["historyDelta"], (a, y)


def check_5(arms: list[dict[str, Any]]) -> None:
    got = {a["arm"]: a for a in arms}
    for name, _, _, _, expect in HIJACK_ARMS:
        a = got[name]
        if expect:
            # 焦点被挪到那个名字框、它的 DOM 值退回原名、而 store 还没跟上，
            # 顺手开着的手势被提交
            assert a["focusMoved"], a
            assert a["focusAfter"] == "data-director-object-name", a
            assert a["nameDom"][0] != a["nameDom"][1], a
            assert a["nameStore"][0] == a["nameStore"][1], a
            assert a["gestureAfter"] is None, a
        else:
            assert not a["focusMoved"], a
            assert a["nameDom"][0] == a["nameDom"][1], a
            assert a["historyDelta"] == (0, 0), a
    # 触发条件是两个变量的与：键入过 **且** 中途没点过非可编辑表面。
    # 方向键按不按都不影响 —— 这一格 706 没测过。
    for a in arms:
        should = a["renamed"] and not a["canvasClickInBetween"]
        assert a["expectHijack"] == should, a


def check_6(table: dict[tuple[str, str], dict[str, Any]]) -> None:
    c = table[("range", "Escape")]
    assert c["gestureBefore"] == "camera-fov", c
    assert c["gestureAfter"] is None, c
    assert c["afterLast"]["commandKind"] == "GESTURE_CANCEL", c["afterLast"]
    assert c["afterLast"]["disposition"] == "NOOP", c["afterLast"]
    assert c["deskOpenAfter"] is True, c
    # 同一个键、同一个「到不了全局处理器」的形状，但到的是另一套处理器：
    # 面板聚焦时 Escape 关掉整个导演台，滑块聚焦时它只取消手势。
    assert table[("panel", "Escape")]["deskOpenAfter"] is False


def check_7(sup: dict[str, Any]) -> None:
    assert sup["objectsAfter"] == sup["objectsBefore"] - 1, sup
    assert sup["afterLast"]["commandKind"] == "DELETE_OBJECTS", sup
    assert sup["afterLast"]["disposition"] == "COMMITTED", sup
    assert sup["historyDelta"][0] == 1, sup


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {"predictions": PREDICTIONS,
                               "not_applicable": NOT_APPLICABLE}
    failures: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            cells = census(browser)
            results["census"] = cells
            table = {(c["focus"], c["key"]): c for c in cells}
        except Exception as exc:  # noqa: BLE001
            failures.append(f"census: {exc}")
            table = {}
        try:
            arms = hijack_arms(browser)
            results["hijack_arms"] = arms
        except Exception as exc:  # noqa: BLE001
            failures.append(f"hijack_arms: {exc}")
            arms = []
        try:
            sup = delete_works(browser)
            results["delete_works"] = sup
        except Exception as exc:  # noqa: BLE001
            failures.append(f"delete_works: {exc}")
            sup = {}
        browser.close()

    checks = [
        ("every-shortcut-is-blocked-while-any-editable-control-has-focus",
         lambda: check_1(table)),
        ("all-six-shortcuts-reach-the-desk-when-the-focus-is-on-the-panel",
         lambda: check_2(table)),
        ("delete-and-backspace-share-one-command-branch",
         lambda: check_3(table)),
        ("the-two-redo-keys-are-aliases", lambda: check_4(table)),
        ("the-browser-form-undo-hijack-needs-a-prior-text-edit-and-no-canvas-click-in-between",
         lambda: check_5(arms)),
        ("escape-reaches-the-gesture-boundary-not-the-desk-while-a-slider-has-focus",
         lambda: check_6(table)),
        ("delete-on-a-deletable-object-actually-deletes",
         lambda: check_7(sup)),
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
