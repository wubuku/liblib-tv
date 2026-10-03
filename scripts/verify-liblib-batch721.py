#!/usr/bin/env python3
"""batch 721 验收：720 的「加模型关台重开就没了」是比错了对象

## 起点

720 测出：路线 A（只加模型）关台重开后 `objects` 从 6 掉回 5，饮料瓶没了；
路线 B（只改名）活着；路线 C（先改名再加速）六个全在。720 明写「不声称成因」，
把「定位 `closeSession`/`persistence.save` 对不同改动类型的处理」留给下一批。

本批顺着这条线走，结果**问题出在探针自己身上**：720 的 `reopen()` 点的是
`document.querySelector('[data-open-director]')` —— DOM 顺序的**第一枚**按钮，
而 `open_desk()` 开的是它自己 `addNode` 造的 `script-execution-<ts>` 节点。
**这两个不是同一个节点。** 720 的路线 A 因此读的是另一个项目的对象表。

## 决定性读数

### 撤回：模型没有丢

| 读数 | 值 |
|---|---|
| 加模型 + 改名后关台 | `objects` 6、`past` 0 |
| **按 nodeId 精确重开同一个节点** | **`objects` 6、`authored` 6、`past` 2** |
| 该节点的持久化记录 | **6 个对象**，含「饮料瓶」（`primitive: "library"`） |
| **720 点的那枚按钮归属** | **`b-bTLLuU4w5q`（fixture 种子节点），不是 nodeX** |
| 点它之后读到的 | `objects` **5**、**另一个 `projectId`**、`generation` 从 1 起 |

⟹ 720 路线 A 的「丢了」= 读了另一个节点。**第三档作废：测的不是那个东西。**

### 「重开」其实有三个，从来被当成一个

| # | 操作 | `objects` | `past` | `projectId` | `generation` |
|---|---|---|---|---|---|
| 1 | 关台 → **同页**重开同一节点 | **6（留住）** | **2（留住）** | 不变 | **+1** |
| 2 | **整页刷新** → 重开 | 记录还在（6），**但节点卡没了、台开不起来** | — | — | — |
| 3 | 打开**另一个**节点 | **5** | 0 | **另一个** | 从 1 起 |

**② 是本批的新发现**：`openDirectorDesk(nodeX, canvasId)` 在刷新后等 15 秒
`[data-director-workspace]` 都没出现，且 `nodeX` 不在刷新后的节点列表里（回到 10 枚种子节点）。

### `past` 不住在 localStorage 里

| 时刻 | `objects` | `past` | localStorage 记录 |
|---|---|---|---|
| 开台 | 5 | 0 | — |
| 加模型 | 6 | 1 | — |
| 再改名 | 6 | 2 | — |
| 关台 | 6 | **0** | **6 个对象，无 `history` 键** |
| 同页重开 | 6 | **2** | 同一条记录，一字未动 |
| 刷新后 | — | — | **与刷新前逐字段相同**（只有 `generation`、`savedAt` 变） |

记录的 `document` 有 12 个键（`schemaVersion / projectId / owner / scene / objects /
groups / shots / activeCameraId / timeline / outputPreferences / resourceRefs /
captureDescriptors`），**没有 `history`**。
⟹ `past` 回来靠的是 `directorStore.ts:1940` 的模块级 `Map`（`directorHistoryByProject`），
刷新即清。**这收窄了 711 的「history 不入持久化」**：
准确说法是「**history 不入 localStorage，只活在内存注册表；同页关台重开能撤销，刷新后不能**」。

### 每次重开的记账

| 字段 | 开台 #1 | 同页重开 #2 |
|---|---|---|
| `projectId` | `director-project-…-1` | **同一个** |
| `sessionId` | `…-2` | **`…-3`（新铸）** |
| `generation` | 1 | **2** |
| 记录里的 `generation` | 1 | **2** |

⟹ `generation` 是「这份项目被打开过第几次」，不是全局计数器；跨节点互不干扰。

### 画布本身不落盘（静态）

`src/store/canvasStore.ts` 里 `localStorage` / `sessionStorage` / `indexedDB` /
`persist` / `subscribe` / `STORAGE_KEY` **命中 0**（`persistence` 是节点数据上的另一个字段）。
`frameosStore.ts` 与 `directorStore.ts` 都有 `localStorage.setItem`，**只有画布 store 没有**。
⟹ 刷新后画布回到 10 枚种子节点，`addNode` 造出来的节点整个消失 —— 与导演台无关，是画布级行为。
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch721-2026-10-01"
W, H = 1280, 1150

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

PREDICTIONS = {
    "batch": 721,
    "retracts": "batch 720 的「只加模型关台重开后消失」",
    "hypothesis": "720 的 reopen() 点的是 DOM 顺序第一枚 [data-open-director]，"
                  "而 open_desk() 开的是它 addNode 造的另一个节点",
    "predicted": [
        "按 nodeId 精确重开：objects 仍是 6，past 回到 2",
        "DOM 顺序第一枚按钮归属另一个节点（b-…），点它读到 5 个对象与另一个 projectId",
        "该节点的 localStorage 记录含 6 个对象、primitive 含 library、且没有 history 键",
        "刷新后记录逐字段不变，但那个节点卡不存在了，台开不起来",
        "刷新前后画布节点列表 = 10 枚种子节点，addNode 造的节点不在其中",
    ],
    "sourceFacts": [
        "src/store/directorStore.ts:1940 directorHistoryByProject 是模块级 Map",
        "src/store/directorStore.ts:3289 closeSession 先 rememberDirectorHistory",
        "src/store/canvasStore.ts 无任何 localStorage / persist / subscribe",
    ],
}

READ_JS = r"""() => {
  const s = window.__director_store.getState();
  const q = (sel) => document.querySelector(sel);
  return {
    deskOpen: !!q('[data-director-workspace]'),
    objects: s.objects ? s.objects.length : null,
    authored: s.authoredObjects ? s.authoredObjects.length : null,
    names: s.objects ? s.objects.map((o) => o.name || o.kind) : null,
    past: s.history && s.history.past ? s.history.past.length : null,
    future: s.history && s.history.future ? s.history.future.length : null,
    generation: s.generation === undefined ? 'ABSENT' : s.generation,
    projectId: s.projectId === undefined ? 'ABSENT' : s.projectId,
    sessionId: s.sessionId === undefined ? 'ABSENT' : s.sessionId,
  };
}"""

BTNS_JS = r"""() => [...document.querySelectorAll('[data-open-director]')].map((b) => {
  const host = b.closest('[data-director-node-id]');
  const r = b.getBoundingClientRect();
  return {
    nodeId: host ? host.getAttribute('data-director-node-id') : null,
    x: Math.round(r.x), y: Math.round(r.y),
    w: Math.round(r.width), h: Math.round(r.height),
  };
})"""

RECORD_JS = r"""(want) => {
  for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i);
    if (k.indexOf(want) === -1) continue;
    const v = JSON.parse(localStorage.getItem(k));
    const d = v.document || v;
    return {
      key: k,
      topKeys: Object.keys(v),
      docKeys: Object.keys(d),
      nObjects: Array.isArray(d.objects) ? d.objects.length : null,
      names: Array.isArray(d.objects) ? d.objects.map((o) => o.name) : null,
      primitives: Array.isArray(d.objects)
        ? d.objects.map((o) => o.primitive || o.kind) : null,
      generation: v.generation, projectId: v.projectId, savedAt: v.savedAt,
      hasHistoryKey: Object.prototype.hasOwnProperty.call(d, 'history')
        || Object.prototype.hasOwnProperty.call(v, 'history'),
    };
  }
  return 'NO_RECORD';
}"""

NODE_IDS_JS = (
    "() => window.__libtv_store.getState().getActiveCanvas().nodes.map((n) => n.id)")


def read(page: Page) -> dict[str, Any]:
    return page.evaluate(READ_JS)


def record(page: Page, node_id: str) -> Any:
    return page.evaluate(RECORD_JS, node_id)


def strip(page: Page) -> None:
    page.evaluate("() => { for (const el of document.querySelectorAll"
                  "('nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(500)


def add_model(page: Page) -> dict[str, Any]:
    page.evaluate(r"""() => {
      const btn = [...document.querySelectorAll('button')]
        .find((b) => b.getAttribute('aria-label') === '模型库');
      if (!btn) return null; const r = btn.getBoundingClientRect();
      window.__ml = {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width)};
    }""")
    geo = page.evaluate("() => window.__ml")
    assert geo, "找不到「模型库」按钮"
    page.mouse.click(geo["x"] + geo["w"] / 2, geo["y"] + 16)
    page.wait_for_timeout(650)
    ok = page.evaluate("() => { const c = document.querySelector"
                       "('[data-director-model-library-card]'); if (!c) return false;"
                       "c.focus(); return document.activeElement === c; }")
    assert ok, "卡片没拿到焦点"
    page.keyboard.press("Enter")
    page.wait_for_timeout(700)
    return read(page)


def rename_object(page: Page, name: str) -> dict[str, Any]:
    ok = page.evaluate("""() => {
      const el = document.querySelector('[data-director-object-name]');
      if (!el) return false; el.focus(); return document.activeElement === el;}""")
    assert ok, "对象名字段没拿到焦点"
    page.keyboard.press("Meta+a")
    page.wait_for_timeout(120)
    page.keyboard.type(name)
    page.wait_for_timeout(250)
    page.keyboard.press("Enter")
    page.wait_for_timeout(600)
    return read(page)


def close_desk(page: Page) -> dict[str, Any]:
    page.mouse.move(400, 600)
    page.wait_for_timeout(200)
    panel = page.evaluate(r"""() => {
      const b = [...document.querySelectorAll('button')]
        .find((x) => x.getAttribute('aria-label') === '关闭模型库');
      if (!b) return null; const r = b.getBoundingClientRect();
      return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width),
              h: Math.round(r.height)};}""")
    if panel:
        page.mouse.click(panel["x"] + panel["w"] / 2, panel["y"] + panel["h"] / 2)
        page.wait_for_timeout(600)
    page.keyboard.press("Escape")
    page.wait_for_timeout(900)
    g = read(page)
    if g["deskOpen"]:
        cb = page.evaluate(r"""() => {
          const b = document.querySelector('[data-close-director]');
          if (!b) return null; const r = b.getBoundingClientRect();
          return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width),
                  h: Math.round(r.height)};}""")
        page.mouse.click(cb["x"] + cb["w"] / 2, cb["y"] + cb["h"] / 2)
        page.wait_for_timeout(900)
        g = read(page)
    assert g["deskOpen"] is False, g
    return g


def open_by_node_id(page: Page, node_id: str) -> dict[str, Any]:
    """只认这一枚按钮：节点 id 必须逐字相等。找不到就报错，绝不退回「第一个」。"""
    b = page.evaluate("""(want) => {
      const hit = [...document.querySelectorAll('[data-open-director]')].find((x) => {
        const h = x.closest('[data-director-node-id]');
        return h && h.getAttribute('data-director-node-id') === want;
      });
      if (!hit) return null;
      const r = hit.getBoundingClientRect();
      return {x: Math.round(r.x), y: Math.round(r.y),
              w: Math.round(r.width), h: Math.round(r.height)};
    }""", node_id)
    assert b, "页面上没有属于 %s 的那枚按钮" % node_id
    page.mouse.click(b["x"] + b["w"] / 2, b["y"] + b["h"] / 2)
    page.wait_for_timeout(1100)
    g = read(page)
    assert g["deskOpen"] is True, g
    return g


def open_programmatically(page: Page, node_id: str,
                          canvas_id: str) -> dict[str, Any]:
    """节点卡已经不在页面上时，用 UI store 走同一条路径试一次（不是直接写导演台 store）。"""
    page.evaluate("""([n, c]) => window.__libtv_ui_store.getState()
        .openDirectorDesk(n, c)""", [node_id, canvas_id])
    try:
        page.locator("[data-director-workspace]").wait_for(
            state="visible", timeout=15_000)
    except Exception:
        return {"deskOpen": False, "note": "节点卡不在，台没开起来"}
    page.wait_for_timeout(1_800)
    return read(page)


def static_facts() -> dict[str, Any]:
    out: dict[str, Any] = {}
    store = (ROOT / "src/store/canvasStore.ts").read_text(encoding="utf-8")
    out["canvasStoreTokens"] = {
        tok: len(re.findall(tok, store)) for tok in
        ("localStorage", "sessionStorage", "indexedDB", r"\bpersist\b",
         r"\bsubscribe\b", "STORAGE_KEY")}
    peers: dict[str, int] = {}
    for f in ("frameosStore.ts", "directorStore.ts", "canvasStore.ts"):
        t = (ROOT / "src/store" / f).read_text(encoding="utf-8")
        peers[f] = len(re.findall(r"localStorage\.setItem", t))
    out["setItemPerStore"] = peers
    ds = (ROOT / "src/store/directorStore.ts").read_text(encoding="utf-8")
    out["historyByProjectIsModuleMap"] = bool(
        re.search(r"directorHistoryByProject\s*=\s*new Map", ds))
    out["closeSessionRemembersHistory"] = bool(re.search(
        r"closeSession:[\s\S]{0,600}?rememberDirectorHistory", ds))
    return out


def run(browser: Any) -> dict[str, Any]:
    page = browser.new_page(viewport={"width": W, "height": H},
                            device_scale_factor=1)
    r: dict[str, Any] = {"static": static_facts()}
    b617.open_desk(page)
    strip(page)
    node_x = page.evaluate(
        "() => window.__libtv_store.getState().getActiveCanvas().nodes.at(-1).id")
    canvas_id = page.evaluate(
        "() => window.__libtv_store.getState().activeCanvasId")
    r["nodeX"] = node_x
    r["seedNodeIds"] = page.evaluate(NODE_IDS_JS)
    r["open1"] = read(page)

    # 720 的 reopen() 就是这一枚：DOM 顺序第一枚按钮
    btns = page.evaluate(BTNS_JS)
    first = btns[0]
    r["firstBtn"] = first
    r["firstBtnIsNodeX"] = first["nodeId"] == node_x

    r["afterRename"] = rename_object(page, "改名探针")
    # 先改名再加模型：加完模型之后第一个 [data-director-object-name]
    # 会换成新加的那个对象（见 firstNameFieldBefore/After），所以顺序要固定
    r["afterAdd"] = add_model(page)
    r["firstNameFieldAfterAdd"] = page.evaluate(
        "() => { const e = document.querySelector('[data-director-object-name]');"
        " return e ? e.value : null; }")
    r["closed"] = close_desk(page)
    r["recordAfterClose"] = record(page, node_x)

    # 重开 ①：同一个 nodeId
    r["reopenSameNode"] = open_by_node_id(page, node_x)
    r["closedAgain"] = close_desk(page)

    # 重开 ③：720 点的那枚按钮，归属的其实是另一个节点
    r["otherNodeId"] = first["nodeId"]
    r["openOtherNode"] = open_by_node_id(page, first["nodeId"])
    r["closedOther"] = close_desk(page)
    r["recordAfterOtherClose"] = record(page, first["nodeId"])

    # 重开 ②：整页刷新，内存 Map 与画布节点一起没
    page.reload(wait_until="networkidle", timeout=90_000)
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__libtv_ui_store"
        " && window.__director_store)", timeout=60_000)
    strip(page)
    r["nodeIdsAfterReload"] = page.evaluate(NODE_IDS_JS)
    r["nodeXSurvivedReload"] = node_x in r["nodeIdsAfterReload"]
    r["recordAfterReload"] = record(page, node_x)
    r["btnsAfterReload"] = page.evaluate(BTNS_JS)
    r["reopenAfterReload"] = open_programmatically(page, node_x, canvas_id)
    page.close()
    return r


def check_1(r: dict[str, Any]) -> None:
    """撤回 720：按 nodeId 精确重开同一个节点，六个对象与撤销栈都还在。"""
    n, a, c = r["afterRename"], r["afterAdd"], r["reopenSameNode"]
    assert n["objects"] == 5 and n["past"] == 1, n
    assert n["names"][0] == "改名探针", n["names"]
    assert a["objects"] == 6 and a["past"] == 2, a
    assert "饮料瓶" in a["names"], a["names"]
    # 加完模型之后第一个 [data-director-object-name] 换成了新加的那个对象
    assert r["firstNameFieldAfterAdd"] == "饮料瓶", r["firstNameFieldAfterAdd"]
    assert c["objects"] == 6, c
    assert c["authored"] == 6, c
    assert c["past"] == 2, c
    assert c["names"] == a["names"], (c["names"], a["names"])


def check_2(r: dict[str, Any]) -> None:
    """720 点的那枚按钮归属另一个节点；打开它读到 5 个对象与另一个 projectId。"""
    assert r["firstBtnIsNodeX"] is False, r["firstBtn"]
    assert r["otherNodeId"] != r["nodeX"], r["otherNodeId"]
    o = r["openOtherNode"]
    assert o["objects"] == 5, o
    assert "改名探针" not in o["names"], o["names"]
    assert "饮料瓶" not in o["names"], o["names"]
    assert o["projectId"] != r["reopenSameNode"]["projectId"], (
        o["projectId"], r["reopenSameNode"]["projectId"])
    assert o["generation"] == 1, o


def check_3(r: dict[str, Any]) -> None:
    """被改过的那个节点，持久化记录里有六个对象（含 library）且根本没有 history 键。"""
    rec = r["recordAfterClose"]
    assert rec != "NO_RECORD", rec
    assert rec["nObjects"] == 6, rec
    assert "饮料瓶" in rec["names"], rec["names"]
    assert "library" in rec["primitives"], rec["primitives"]
    assert rec["hasHistoryKey"] is False, rec
    assert "history" not in rec["docKeys"], rec["docKeys"]


def check_4(r: dict[str, Any]) -> None:
    """刷新前后同一条记录逐字段相同，只有 generation 与 savedAt 变。"""
    a, b = r["recordAfterClose"], r["recordAfterReload"]
    assert b != "NO_RECORD", b
    for k in ("topKeys", "docKeys", "nObjects", "names", "primitives", "projectId"):
        assert a[k] == b[k], "%s: %s != %s" % (k, a[k], b[k])
    assert b["generation"] == a["generation"] + 1, (a["generation"], b["generation"])
    assert b["savedAt"] != a["savedAt"], (a["savedAt"], b["savedAt"])
    assert b["hasHistoryKey"] is False, b


def check_5(r: dict[str, Any]) -> None:
    """「重开」有三层：同页留住 past；刷新后节点卡没了台开不起来；换节点是另一份项目。"""
    assert r["closed"]["past"] == 0, r["closed"]
    assert r["reopenSameNode"]["past"] == 2, r["reopenSameNode"]
    assert r["nodeXSurvivedReload"] is False, r["nodeIdsAfterReload"]
    assert r["reopenAfterReload"]["deskOpen"] is False, r["reopenAfterReload"]
    assert [b["nodeId"] for b in r["btnsAfterReload"]] == [r["otherNodeId"]]


def check_6(r: dict[str, Any]) -> None:
    """每次重开：projectId 不变、generation +1、sessionId 新铸。"""
    o, c = r["open1"], r["reopenSameNode"]
    assert c["projectId"] == o["projectId"], (o["projectId"], c["projectId"])
    assert o["generation"] == 1 and c["generation"] == 2, (o, c)
    assert c["sessionId"] != o["sessionId"], (o["sessionId"], c["sessionId"])


def check_7(r: dict[str, Any]) -> None:
    """画布 store 不落盘：只有 frameos/director 写 localStorage；history 在模块级 Map。"""
    s = r["static"]
    assert sum(s["canvasStoreTokens"].values()) == 0, s["canvasStoreTokens"]
    assert s["setItemPerStore"]["canvasStore.ts"] == 0, s["setItemPerStore"]
    assert s["setItemPerStore"]["frameosStore.ts"] > 0, s["setItemPerStore"]
    assert s["setItemPerStore"]["directorStore.ts"] > 0, s["setItemPerStore"]
    assert s["historyByProjectIsModuleMap"] is True, s
    assert s["closeSessionRemembersHistory"] is True, s


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {"predictions": PREDICTIONS}
    failures: list[str] = []
    got: dict[str, Any] = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            got["run"] = run(browser)
        except Exception as exc:  # noqa: BLE001
            failures.append("run: %s" % exc)
            got["run"] = {}
        browser.close()
    results.update(got)
    checks = [
        ("the-model-add-survives-closing-and-reopening-the-same-node",
         lambda: check_1(got.get("run", {}))),
        ("the-button-720-clicked-belongs-to-a-different-node",
         lambda: check_2(got.get("run", {}))),
        ("the-persisted-record-carries-six-objects-and-has-no-history-key",
         lambda: check_3(got.get("run", {}))),
        ("the-persisted-record-is-unchanged-across-a-reload-except-generation-and-saved-at",
         lambda: check_4(got.get("run", {}))),
        ("reopen-comes-in-three-layers-not-one",
         lambda: check_5(got.get("run", {}))),
        ("reopening-keeps-project-id-bumps-generation-and-mints-a-new-session-id",
         lambda: check_6(got.get("run", {}))),
        ("the-canvas-store-never-persists-nodes",
         lambda: check_7(got.get("run", {}))),
    ]
    summary: dict[str, bool] = {}
    for name, fn in checks:
        try:
            fn()
            summary[name] = True
        except Exception as exc:  # noqa: BLE001
            summary[name] = False
            failures.append("%s: %s" % (name, exc))
    results["summary"] = summary
    results["failures"] = failures
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1, default=str),
        encoding="utf-8")
    for name, ok in summary.items():
        print(("PASS " if ok else "FAIL ") + name)
    for f in failures:
        print("  ->", f[:400])
    print("\n%d/%d 通过" % (sum(1 for v in summary.values() if v), len(summary)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
