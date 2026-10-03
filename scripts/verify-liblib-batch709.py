#!/usr/bin/env python3
"""batch 709 验收：导演台的历史与手势活多久 —— 关掉再打开还能不能撤？

## 起点

706–708 把「一次会话内的撤销」测透了：手势怎么并条目、`Cmd+Z` 哪些格到不了、
到不了的格子里浏览器做了什么。**但那三批全部在同一个会话里。**
用户真正会问的是跨会话的问题：**在台里改了东西、关掉导演台、回来还能不能撤？**

## 五条预测（写死在代码里，先于任何测量）

- **P1** 关台再重开后 `history.past` 归零，之后按 `Cmd+Z` 记 `UNDO` / `NOOP`
- **P2** 归零的原因是**换了一个 projectId**（不是「历史被清空」）
- **P3** 连开关两次会**每次**都归零（不是只丢一次）
- **P4** 开着手势（改了值没提交）时关台，未提交的改动被丢弃
- **P5** 已提交的内容在关台重开后**保留**

## 结果：P1、P2、P4 成立；**P3 与 P5 都被推翻，而推翻的方式很奇怪**

- **P4 成立且是本批最扎实的一条**：滑块上按了几下方向键、没点画布就关台，
  改动**被丢弃**（fov 46 → 43），一条历史都没留下。
- **P1、P2 成立**：第一次关台重开后 `history.past` 归零、projectId 变、
  按 `Cmd+Z` 记 `UNDO` / `NOOP`。
- **P3 被推翻**：第二次关台重开**什么都没丢** —— 连 `history.past` 里那一条都还在，
  projectId **一字不变**。
- **P5 被推翻**：已提交内容在**第一次**关台重开后丢失（改名回退、fov 回 43），
  刷新页面后重开也丢；**只有第二次及以后的关台重开才保留**。

## 本批最重要的一行：「第一次关台丢工作」**不能当成用户可见的缺陷**

第一次开台走的是 617 仪器的 `openDirectorDesk(node.id, canvasId)` store 调用。
我读了两处源码，确认**真实按钮调的是同一个函数**、参数也相同
（`ScriptExecutionNode.tsx:57` 的 onClick 只多一个 `event.stopPropagation()`），
所以「开台路径不同」这个解释站不住。

但我**两次尝试让第一次开台走真实按钮都没成功**：
在一个从未开过导演台的节点上，点 `[data-open-director]` 按钮之后导演台没有打开
（按钮点得到、就是没开台；刷新页面后仍然如此，而 A5 证明「关过台再刷新」之后同一个按钮是能开的）。
⟹ **用户路径未取证**，本批不把「第一次关台丢工作」写成缺陷。

**一个不对称摆在账上、没人能解释它的时候，正确做法是把它记成未取证，而不是记成缺陷。**

## 判据

1. `closing-the-desk-discards-an-uncommitted-gesture-change`
2. `the-first-close-and-reopen-loses-everything-committed-including-history`
3. `the-second-close-and-reopen-loses-nothing-not-even-the-history-entry`
4. `a-page-reload-then-reopen-behaves-like-the-first-close`
5. `the-open-button-does-nothing-on-a-node-that-never-had-a-director-session`
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch709-2026-10-01"
W, DESK_H = 1280, 1150
BASE_URL = "http://127.0.0.1:4317"
RENAME_TO = "改名试试709"

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

PREDICTIONS = {
    "P1": "关台再重开后 history.past 归零，之后 Cmd+Z 记 UNDO/NOOP",
    "P2": "归零的原因是换了一个 projectId",
    "P3": "连开关两次会每次都归零",
    "P4": "开着手势关台，未提交的改动被丢弃",
    "P5": "已提交的内容在关台重开后保留",
}

READ = r"""() => {
  const s = window.__director_store.getState();
  const h = s.history; const r = s.lastCommandResult;
  const w = document.querySelector('[data-director-workspace]');
  const cam = s.objects.find((o) => o.kind === 'camera');
  return {
    deskOpen: !!w,
    projectId: w ? w.getAttribute('data-director-project-id') : null,
    pastLen: (h.past || []).length,
    pastKinds: (h.past || []).map((e) => e.commandKind),
    active: h.activeGesture ? h.activeGesture.commandKind : null,
    last: r ? r.commandKind + '/' + r.disposition : null,
    lastReason: r ? r.reason : null,
    fovStore: cam ? cam.camera.fov : null,
    names: s.objects.map((o) => o.name),
    objectsLen: s.objects.length,
  };
}"""

SEL_CAMERA = r"""() => {
  const s = window.__director_store.getState();
  const c = s.objects.find((o) => o.kind === 'camera');
  const row = document.querySelector('[data-director-tree] [role="treeitem"]'
    + '[data-director-object-id="' + c.id + '"]');
  if (!row) return { ok: false, stage: 'no-row' };
  row.click();
  return { ok: window.__director_store.getState().selectedObjectId === c.id };
}"""


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
    page.evaluate(SEL_CAMERA)
    page.wait_for_timeout(500)
    return page


def close_desk(page: Page) -> None:
    page.locator("[data-close-director]").first.click()
    page.locator("[data-director-workspace]").wait_for(state="detached", timeout=15_000)
    page.wait_for_timeout(800)


def open_desk(page: Page) -> None:
    page.locator("[data-open-director]").first.click()
    page.locator("[data-director-workspace]").wait_for(state="visible", timeout=30_000)
    page.wait_for_timeout(1_800)
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.evaluate(SEL_CAMERA)
    page.wait_for_timeout(500)


def rename(page: Page) -> None:
    el = page.locator("[data-director-object-name]").first
    el.click()
    page.wait_for_timeout(200)
    el.fill(RENAME_TO)
    el.press("Tab")
    page.wait_for_timeout(600)


def arrow_keys(page: Page, n: int) -> None:
    el = page.locator("[data-director-shot-end]").first
    el.click()
    page.wait_for_timeout(200)
    el.press("Tab")
    page.wait_for_timeout(500)
    for _ in range(n):
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(300)


def arm_uncommitted_gesture(browser: Any) -> dict[str, Any]:
    page = fresh(browser)
    s0 = read(page)
    arrow_keys(page, 3)
    s1 = read(page)
    close_desk(page)
    open_desk(page)
    s2 = read(page)
    page.close()
    return {"s0": s0, "s1": s1, "s2": s2}


def arm_two_cycles(browser: Any) -> dict[str, Any]:
    page = fresh(browser)
    rename(page)
    a = read(page)
    close_desk(page)
    open_desk(page)
    b = read(page)
    page.mouse.click(640, 900)
    page.wait_for_timeout(600)
    page.evaluate(SEL_CAMERA)
    page.wait_for_timeout(500)
    rename(page)
    c = read(page)
    close_desk(page)
    open_desk(page)
    d = read(page)
    page.close()
    return {"afterRename1": a, "afterCycle1": b, "afterRename2": c, "afterCycle2": d}


def arm_reload(browser: Any) -> dict[str, Any]:
    page = fresh(browser)
    rename(page)
    a = read(page)
    close_desk(page)
    page.reload()
    page.wait_for_timeout(3_000)
    open_desk(page)
    b = read(page)
    page.mouse.click(640, 900)
    page.wait_for_timeout(600)
    page.keyboard.press("Meta+z")
    page.wait_for_timeout(700)
    c = read(page)
    page.close()
    return {"afterRename": a, "afterReloadReopen": b, "afterUndo": c}


def arm_open_button(browser: Any) -> dict[str, Any]:
    """从未开过导演台的节点上点真实按钮 —— 两次独立尝试"""
    out = []
    for attempt in (1, 2):
        page = browser.new_page(viewport={"width": W, "height": DESK_H},
                                device_scale_factor=1)
        page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle", timeout=90_000)
        page.wait_for_function(
            "() => Boolean(window.__libtv_store && window.__libtv_ui_store "
            "&& window.__director_store)", timeout=60_000)
        page.evaluate("""() => {
          const s = window.__libtv_store.getState();
          s.addNode("script-execution", { title: "Batch 709" });
        }""")
        page.wait_for_timeout(1_500)
        if attempt == 2:
            page.reload()
            page.wait_for_timeout(3_000)
        has_btn = page.locator("[data-open-director]").count() > 0
        opened = False
        if has_btn:
            page.locator("[data-open-director]").first.click()
            try:
                page.locator("[data-director-workspace]").wait_for(
                    state="visible", timeout=8_000)
                opened = True
            except Exception:  # noqa: BLE001
                opened = False
        out.append({"attempt": attempt, "hasButton": has_btn, "opened": opened,
                    "reloadedFirst": attempt == 2})
        page.close()
    return {"attempts": out}


def check_1(a: dict[str, Any]) -> None:
    assert a["s0"]["fovStore"] == 43, a["s0"]
    assert a["s1"]["fovStore"] == 46, a["s1"]
    assert a["s1"]["active"] == "camera-fov", a["s1"]
    assert a["s1"]["pastLen"] == 0, a["s1"]
    # 关台丢弃未提交的手势：fov 回到基线
    assert a["s2"]["fovStore"] == 43, a["s2"]
    assert a["s2"]["pastLen"] == 0, a["s2"]


def check_2(t: dict[str, Any]) -> None:
    assert RENAME_TO in t["afterRename1"]["names"], t["afterRename1"]
    assert t["afterRename1"]["pastLen"] == 1, t["afterRename1"]
    b = t["afterCycle1"]
    assert RENAME_TO not in b["names"], b
    assert b["pastLen"] == 0, b
    assert b["projectId"] != t["afterRename1"]["projectId"], \
        "projectId 没变，那「归零」的原因就不是换项目"


def check_3(t: dict[str, Any]) -> None:
    c, d = t["afterRename2"], t["afterCycle2"]
    assert RENAME_TO in c["names"] and c["pastLen"] == 1, c
    # 第二次关台重开：名字在、历史那条也在、projectId 一字不变
    assert RENAME_TO in d["names"], d
    assert d["pastLen"] == 1, d
    assert d["pastKinds"] == ["UPDATE_OBJECT"], d
    assert d["projectId"] == c["projectId"], (c["projectId"], d["projectId"])


def check_4(r: dict[str, Any]) -> None:
    assert RENAME_TO in r["afterRename"]["names"], r["afterRename"]
    b = r["afterReloadReopen"]
    assert RENAME_TO not in b["names"], b
    assert b["pastLen"] == 0, b
    assert r["afterUndo"]["last"] == "UNDO/NOOP", r["afterUndo"]


def check_5(a: dict[str, Any]) -> None:
    for rec in a["attempts"]:
        assert rec["hasButton"] is True, rec
        assert rec["opened"] is False, rec


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {"predictions": PREDICTIONS}
    failures: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        got: dict[str, Any] = {}
        for name, fn in (("uncommitted_gesture", arm_uncommitted_gesture),
                         ("two_cycles", arm_two_cycles),
                         ("reload", arm_reload),
                         ("open_button", arm_open_button)):
            try:
                got[name] = fn(browser)
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{name}: {exc}")
                got[name] = {}
        browser.close()
    results.update(got)
    checks = [
        ("closing-the-desk-discards-an-uncommitted-gesture-change",
         lambda: check_1(got.get("uncommitted_gesture", {}))),
        ("the-first-close-and-reopen-loses-everything-committed-including-history",
         lambda: check_2(got.get("two_cycles", {}))),
        ("the-second-close-and-reopen-loses-nothing-not-even-the-history-entry",
         lambda: check_3(got.get("two_cycles", {}))),
        ("a-page-reload-then-reopen-behaves-like-the-first-close",
         lambda: check_4(got.get("reload", {}))),
        ("the-open-button-does-nothing-on-a-node-that-never-had-a-director-session",
         lambda: check_5(got.get("open_button", {}))),
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
        print("  ->", f[:400])
    print(f"\n{sum(1 for v in summary.values() if v)}/{len(summary)} 通过")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
