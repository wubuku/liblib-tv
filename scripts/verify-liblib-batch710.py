#!/usr/bin/env python3
"""batch 710 验收：关台重开到底丢不丢 —— 先证明 709 测的是「另一个节点」

## 起点

709 测出「第一次关台重开丢全部已提交内容、第二次起全留」这个不对称，
并诚实地写下「用户路径未取证」。本批把那个未取证项做完，结论是：
**709 测的根本不是同一个节点。**

## 决定性读数：`data-director-source-node-id`

| 阶段 | `sourceNode` | `projectId` | `history.past` |
|---|---|---|---|
| 仪器开的台 | `n-…bbzko0`（`addNode` 建的那个） | `…-1` | 1 |
| 关台 → **按钮**重开 | **`b-bTLLuU4w5q`（fixture 那个）** | `…-3` | 0 |
| 再关 → 再按钮重开 | `b-bTLLuU4w5q` | `…-3` | 1 |

全页只有一个 `[data-open-director]` 按钮，祖先链上的 `data-director-node-id` 是
`b-bTLLuU4w5q`；`addNode` 建出来的节点**根本没有渲染节点卡**（react-flow 只渲染视口内的节点）。

⟹ **709 的「第一次丢、第二次留」= 第一次重开打开了另一个节点，第二次起一直开同一个。**
**709 的五条判据全部作废** —— 不是读数错，是**测的不是那个东西**。
这比「读数对、理由错」更重一档：读数和结论都不能留。

## 本批用同一个节点重做

**全程只用 `b-bTLLuU4w5q`**（它既有节点卡、也有按钮 ⟹ 开台和关台都能走真实控件），
并在每一步断言 `sourceNode` 没变 —— 前提不成立就不算数。

## 四条预测

- **P1** 全程 `sourceNode` 相同（前提断言）
- **P2** 同节点关台重开**保留**已提交内容与历史
- **P3** 开着手势关台，未提交的改动被丢弃
- **P4** 关台后**刷新页面**再重开，已提交内容丢失（持久化只在内存）

**P3 与 P4 都被推翻，而且推翻的方向相反**：同一个节点关台重开时，
手势的改动**被提交了**（不是丢弃）；刷新页面时**内容留住、只有历史没留住**。

## 判据

1. `every-step-of-this-batch-stays-on-the-same-source-node`
2. `closing-and-reopening-the-same-node-keeps-committed-work-and-history`
3. `closing-with-an-open-gesture-commits-it-instead-of-discarding-it`
4. `a-page-reload-keeps-committed-content-but-drops-the-history`
5. `retraction-of-709-the-close-then-button-reopen-switched-nodes`
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch710-2026-10-01"
W, DESK_H = 1280, 1150
RENAME_TO = "改名试试710"

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

PREDICTIONS = {
    "P1": "全程 sourceNode 相同（本批的前提断言）",
    "P2": "同节点关台重开保留已提交内容与历史",
    "P3": "开着手势关台，未提交的改动被丢弃",
    "P4": "关台后刷新页面再重开，已提交内容丢失",
}

READ = r"""() => {
  const w = document.querySelector('[data-director-workspace]');
  const s = window.__director_store.getState();
  const cam = s.objects.find((o) => o.kind === 'camera');
  const btn = document.querySelector('[data-open-director]');
  const card = btn ? btn.closest('[data-director-node-id]') : null;
  return {
    deskOpen: !!w,
    sourceNode: w ? w.getAttribute('data-director-source-node-id') : null,
    projectId: w ? w.getAttribute('data-director-project-id') : null,
    buttonOwner: card ? card.getAttribute('data-director-node-id') : null,
    pastLen: (s.history.past || []).length,
    pastKinds: (s.history.past || []).map((e) => e.commandKind),
    active: s.history.activeGesture ? s.history.activeGesture.commandKind : null,
    last: s.lastCommandResult
      ? s.lastCommandResult.commandKind + '/' + s.lastCommandResult.disposition
      : null,
    fov: cam ? cam.camera.fov : null,
    names: s.objects.map((o) => o.name),
  };
}"""

SEL_CAMERA = r"""() => {
  const s = window.__director_store.getState();
  const c = s.objects.find((o) => o.kind === 'camera');
  const row = document.querySelector('[data-director-tree] [role="treeitem"]'
    + '[data-director-object-id="' + c.id + '"]');
  if (row) row.click();
  return !!row;
}"""


class Instrument(Exception):
    pass


def read(page: Page) -> dict[str, Any]:
    return page.evaluate(READ)


def card_node_id(page: Page) -> str:
    """有节点卡（也就有按钮）的那个 script-execution 节点 —— 不硬编码 id"""
    d = page.evaluate(
        "() => { const c = document.querySelector('[data-open-director]')"
        " && document.querySelector('[data-open-director]')"
        ".closest('[data-director-node-id]');"
        " return c ? c.getAttribute('data-director-node-id') : null; }")
    if not d:
        raise Instrument("这一页没有带节点卡的 script-execution 节点")
    return d


def open_via_store(page: Page, node_id: str) -> None:
    """和真实按钮**同一个函数**（`openDirectorDesk(nodeId, canvasId)`），
    只为了第一次开台 —— 之后每次重开都走真实按钮。"""
    page.evaluate("""(id) => {
      const s = window.__libtv_store.getState();
      window.__libtv_ui_store.getState().openDirectorDesk(id, s.activeCanvasId);
    }""", node_id)
    page.locator("[data-director-workspace]").wait_for(state="visible", timeout=30_000)
    page.wait_for_timeout(1_800)
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(300)
    page.evaluate(SEL_CAMERA)
    page.wait_for_timeout(500)


def close_via_button(page: Page) -> None:
    page.locator("[data-close-director]").first.click()
    page.locator("[data-director-workspace]").wait_for(state="detached", timeout=15_000)
    page.wait_for_timeout(800)


def reopen_via_button(page: Page) -> None:
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


def boot(browser: Any) -> tuple[Page, str]:
    page = browser.new_page(viewport={"width": W, "height": DESK_H},
                            device_scale_factor=1)
    page.goto(f"{b617.BASE_URL}/?batch70=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__libtv_ui_store "
        "&& window.__director_store)", timeout=60_000)
    return page, card_node_id(page)


def arm_same_node_roundtrip(browser: Any) -> dict[str, Any]:
    page, node_id = boot(browser)
    open_via_store(page, node_id)
    a = read(page)
    rename(page)
    b = read(page)
    close_via_button(page)
    c = read(page)
    reopen_via_button(page)
    d = read(page)
    page.close()
    return {"nodeId": node_id, "open": a, "renamed": b, "closed": c, "reopened": d}


def arm_open_gesture(browser: Any) -> dict[str, Any]:
    page, node_id = boot(browser)
    open_via_store(page, node_id)
    a = read(page)
    arrow_keys(page, 3)
    b = read(page)
    close_via_button(page)
    reopen_via_button(page)
    c = read(page)
    page.close()
    return {"nodeId": node_id, "open": a, "gesture": b, "reopened": c}


def arm_reload(browser: Any) -> dict[str, Any]:
    page, node_id = boot(browser)
    open_via_store(page, node_id)
    rename(page)
    a = read(page)
    close_via_button(page)
    page.reload()
    page.wait_for_timeout(3_000)
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    after_reload_cards = page.evaluate(
        "() => Array.from(document.querySelectorAll('[data-director-node-id]'))"
        ".map((n) => n.getAttribute('data-director-node-id'))")
    reopen_via_button(page)
    b = read(page)
    page.close()
    return {"nodeId": node_id, "renamed": a, "afterReload": b,
            "cardsAfterReload": after_reload_cards}


def arm_709_style(browser: Any) -> dict[str, Any]:
    """照 709 的样子开台：617 仪器 addNode 出来的节点。
    页面上唯一的按钮属于**另一个**节点 ⟹ 关台后按按钮重开会换节点。"""
    page = browser.new_page(viewport={"width": W, "height": DESK_H},
                            device_scale_factor=1)
    b617.open_desk(page)          # 617 的开台：addNode + openDirectorDesk(nodes.at(-1))
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(300)
    page.evaluate(SEL_CAMERA)
    page.wait_for_timeout(500)
    opened = read(page)
    card = page.evaluate(
        "() => { const c = document.querySelector('[data-open-director]')"
        " && document.querySelector('[data-open-director]')"
        ".closest('[data-director-node-id]');"
        " return c ? c.getAttribute('data-director-node-id') : null; }")
    close_via_button(page)
    closed = read(page)
    reopen_via_button(page)
    reopened = read(page)
    page.close()
    return {"openedSourceNode": opened["sourceNode"], "buttonOwnerId": card,
            "opened": opened, "closed": closed, "reopened": reopened,
            "namesKept": RENAME_TO in reopened["names"]}


def check_1(t: dict[str, Any]) -> None:
    ids = {t["open"]["sourceNode"], t["renamed"]["sourceNode"],
           t["reopened"]["sourceNode"]}
    assert len(ids) == 1, f"全程不是同一个节点：{ids}"
    assert t["open"]["buttonOwner"] == t["nodeId"], t["open"]
    assert t["reopened"]["sourceNode"] == t["nodeId"], t["reopened"]


def check_2(t: dict[str, Any]) -> None:
    assert RENAME_TO in t["renamed"]["names"], t["renamed"]
    assert t["renamed"]["pastLen"] == 1, t["renamed"]
    r = t["reopened"]
    assert RENAME_TO in r["names"], f"同节点重开竟然丢了已提交内容：{r}"
    assert r["pastLen"] == 1, f"同节点重开连历史都没了：{r}"
    assert r["projectId"] == t["renamed"]["projectId"], (t["renamed"], r)


def check_3(t: dict[str, Any]) -> None:
    """第一版断言「未提交的手势改动被丢弃」，被这一格推翻 ——
    同一个节点关台再重开，fov 仍是 46，而且**多了一条 camera-fov 历史条目**。
    ⟹ 关台不是丢弃手势，是**把��提交了**（`closeSession` 快照的是当前文档，
    而手势的改动早就写在 store 里了）。709 那一格读到 fov 43 是因为它读的是另一个节点。"""
    assert t["open"]["fov"] == 43, t["open"]
    assert t["gesture"]["fov"] == 46, t["gesture"]
    assert t["gesture"]["active"] == "camera-fov", t["gesture"]
    assert t["gesture"]["pastLen"] == 0, t["gesture"]
    r = t["reopened"]
    assert r["fov"] == 46, f"未提交的手势改动竟然没留下：{r}"
    assert r["pastLen"] == 1 and r["pastKinds"] == ["camera-fov"], r


def check_4(t: dict[str, Any]) -> None:
    """P4 猜的是「刷新页面丢内容」，实测是**内容留住、只有历史没留住**。
    ⟹ 持久化带的是文档、不带 history（`rememberDirectorHistory` 只在内存）。"""
    assert RENAME_TO in t["renamed"]["names"], t["renamed"]
    r = t["afterReload"]
    assert RENAME_TO in r["names"], f"刷新后内容竟然没留住：{r}"
    assert r["pastLen"] == 0, f"刷新后历史竟然还在：{r}"
    assert r["sourceNode"] == t["nodeId"], \
        f"刷新后打开的不是同一个节点，那这条就不算数：{r}"


def check_5(t: dict[str, Any]) -> None:
    """撤回 709 的证据：**用 709 那台仪器**（617 的 addNode）开台时，
    开的节点和页面上唯一那个按钮所属的节点**不是同一个**，
    于是「关台后按按钮重开」重开的是另一个节点 —— 709 那个不对称就是这么来的。
    本批其余各臂刻意**避开**这个陷阱（全程用按钮所属的那个节点）。"""
    assert t["openedSourceNode"] != t["buttonOwnerId"], (
        "709 式仪器这一格没能复现节点切换，撤回 709 的证据不足", t)


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {"predictions": PREDICTIONS}
    failures: list[str] = []
    got: dict[str, Any] = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, fn in (("same_node", arm_same_node_roundtrip),
                         ("open_gesture", arm_open_gesture),
                         ("reload", arm_reload),
                         ("instrument_style", arm_709_style)):
            try:
                got[name] = fn(browser)
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{name}: {exc}")
                got[name] = {}
        browser.close()
    results.update(got)
    checks = [
        ("every-step-of-this-batch-stays-on-the-same-source-node",
         lambda: check_1(got.get("same_node", {}))),
        ("closing-and-reopening-the-same-node-keeps-committed-work-and-history",
         lambda: check_2(got.get("same_node", {}))),
        ("closing-with-an-open-gesture-commits-it-instead-of-discarding-it",
         lambda: check_3(got.get("open_gesture", {}))),
        ("a-page-reload-keeps-committed-content-but-drops-the-history",
         lambda: check_4(got.get("reload", {}))),
        ("retraction-of-709-the-close-then-button-reopen-switched-nodes",
         lambda: check_5(got.get("instrument_style", {}))),
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
