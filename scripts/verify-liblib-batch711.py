#!/usr/bin/env python3
"""batch 711 验收：刷新页面到底带走了什么 —— 一次全叶投影的前后差集

## 起点

710 留下一条硬读数：**同一个节点上，刷新页面是「内容留住、历史没留住」**。
但那条只说了两件事，本批要问的是**完整的边界**：还有哪些东西跟着刷新走了、哪些没跟。

做法是 699–710 一直在用的那条：**判「有没有变」用全 store 逐叶投影**，
一次投影 → 关台 → 刷新 → 重开 → 再投影，**差集就是持久化的完整边界**。

## 五条预测（写死在代码里，先于任何测量）

- **P1** 文档内容（对象名、fov、轨道、镜头时长）**过**刷新
- **P2** `history` 整个**不过**刷新
- **P3** 播放头与 zoom **不过**刷新（它们是 `timeline` 下的 store 状态，不是文档）
- **P4** 选区与选中轨**不过**刷新
- **P5** 时间轴的折叠态**不过**刷新

## 结果：三条成立、两条被推翻、两条落在第三态

- **P1、P2、P5 成立。** 2 条历史条目 × 196 枚叶子**整棵子树消失**（不是变成 0 条）；
  折叠态 `true → false`、时间轴高度 `88 → 182`。
- **P4 被推翻**：选区（`selectedObjectId` / `selectedObjectIds`）与
  `selectedTrackId` **原样回来** —— 刷新前是角色（`director-character-lead`），
  刷新后还是角色。**应用把「你当时选中了谁」记进了持久化。**
- **P3 落在第三态**：点标尺之后播放头**根本没动**（刷新前 `playheadTime` 就是 0），
  zoom 簇只有一枚按钮、点完 `zoom` 仍是 44。
  ⟹ **我没能造出差异**，这两项**记成未取证**，不记成「过」也不记成「不过」。
- **另有两项记成不适用**：`captures` 与 `localModelLibrary` 全程都是 0 条，
  我没有真实控件能造出样本 ⟹ **0 → 0 是第三态，不是「它们也过刷新」**。

## 判据

1. `every-step-stays-on-the-same-source-node`
2. `document-content-survives-the-reload`
3. `the-whole-history-subtree-does-not-survive-the-reload`
4. `the-selection-and-selected-track-survive-the-reload`
5. `the-timeline-collapse-state-does-not-survive-the-reload`
6. `the-session-identity-is-rebuilt-on-reload`
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch711-2026-10-01"
W, DESK_H = 1280, 1150
RENAME_TO = "改名试试711"
CHARACTER = "director-character-lead"

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

PREDICTIONS = {
    "P1": "文档内容（对象名、fov、轨道、镜头时长）过刷新",
    "P2": "history 整个不过刷新",
    "P3": "播放头与 zoom 不过刷新",
    "P4": "选区与选中轨不过刷新",
    "P5": "时间轴的折叠态不过刷新",
}

FLAT = r"""() => {
  const s = window.__director_store.getState();
  const o = {};
  const walk = (v, p, d) => {
    if (d > 5) { o[p] = String(v); return; }
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

SCALARS = r"""() => {
  const s = window.__director_store.getState();
  const t = s.timeline || {};
  const tl = document.querySelector('[data-director-timeline]');
  const cam = s.objects.find((o) => o.kind === 'camera');
  return {
    names: s.objects.map((o) => o.name),
    fov: cam && cam.camera ? cam.camera.fov : null,
    pastLen: (s.history.past || []).length,
    futureLen: (s.history.future || []).length,
    generation: s.generation,
    sessionId: s.sessionId,
    selectedObjectId: s.selectedObjectId,
    selectedObjectIds: (s.selectedObjectIds || []).slice(),
    selectedTrackId: t.selectedTrackId,
    selectedKeyframeId: t.selectedKeyframeId,
    playheadTime: t.playheadTime !== undefined ? t.playheadTime : t.currentTime,
    zoom: t.zoom,
    duration: t.duration,
    editorMode: t.editorMode,
    isPlaying: t.isPlaying,
    isCollapsed: tl ? tl.getAttribute('data-director-timeline-collapsed') : null,
    timelineHeightAttr: tl ? tl.getAttribute('data-director-timeline-height') : null,
    shotEnd: s.shots[0] ? s.shots[0].endTime : null,
    tracks: (t.tracks || []).map((x) => x.id),
    localModelLibraryLen: (s.localModelLibrary || []).length,
    capturesLen: (s.captures || []).length,
    lastCommandResult: s.lastCommandResult ? 'SET' : 'null',
  };
}"""

ID = r"""() => {
  const w = document.querySelector('[data-director-workspace]');
  const btn = document.querySelector('[data-open-director]');
  const card = btn ? btn.closest('[data-director-node-id]') : null;
  return {
    deskOpen: !!w,
    sourceNode: w ? w.getAttribute('data-director-source-node-id') : null,
    buttonOwner: card ? card.getAttribute('data-director-node-id') : null,
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

SEL_CHARACTER = r"""(id) => {
  const row = document.querySelector('[data-director-tree] [role="treeitem"]'
    + '[data-director-object-id="' + id + '"]');
  if (!row) return { ok: false, stage: 'no-row' };
  row.click();
  const s = window.__director_store.getState();
  return { ok: s.selectedObjectId === id, selected: s.selectedObjectId };
}"""


class Instrument(Exception):
    pass


def boot(browser: Any) -> tuple[Page, str]:
    page = browser.new_page(viewport={"width": W, "height": DESK_H},
                            device_scale_factor=1)
    page.goto(f"{b617.BASE_URL}/?batch70=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__libtv_ui_store "
        "&& window.__director_store)", timeout=60_000)
    # 710 立的硬规矩：节点 id 从按钮 closest() 读，不硬编码，
    # 且只用**页面上真有节点卡**的那个节点（否则重开时点的是另一个节点）
    node_id = page.evaluate(
        "() => { const b = document.querySelector('[data-open-director]');"
        " const c = b && b.closest('[data-director-node-id]');"
        " return c ? c.getAttribute('data-director-node-id') : null; }")
    if not node_id:
        raise Instrument("这一页没有带节点卡的 script-execution 节点")
    page.evaluate("""(id) => {
      const s = window.__libtv_store.getState();
      window.__libtv_ui_store.getState().openDirectorDesk(id, s.activeCanvasId);
    }""", node_id)
    page.locator("[data-director-workspace]").wait_for(state="visible", timeout=30_000)
    page.wait_for_timeout(1_800)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(300)
    page.evaluate(SEL_CAMERA)
    page.wait_for_timeout(500)
    return page, node_id


def close_via_button(page: Page) -> None:
    page.locator("[data-close-director]").first.click()
    page.locator("[data-director-workspace]").wait_for(state="detached", timeout=15_000)
    page.wait_for_timeout(800)


def reopen_via_button(page: Page) -> None:
    page.locator("[data-open-director]").first.click()
    page.locator("[data-director-workspace]").wait_for(state="visible", timeout=30_000)
    page.wait_for_timeout(1_800)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
    # 刻意**不**调 SEL_CAMERA：选区与选中轨是本批要测的读数，
    # 探针自己动它们就等于把结论顶掉
    page.wait_for_timeout(500)


def make_changes(page: Page) -> dict[str, Any]:
    done: dict[str, Any] = {}
    el = page.locator("[data-director-object-name]").first
    el.click()
    page.wait_for_timeout(200)
    el.fill(RENAME_TO)
    el.press("Tab")
    page.wait_for_timeout(600)
    done["rename"] = True

    shot = page.locator("[data-director-shot-end]").first
    shot.click()
    page.wait_for_timeout(200)
    shot.press("Tab")
    page.wait_for_timeout(500)
    for _ in range(3):
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(280)
    page.mouse.click(640, 900)
    page.wait_for_timeout(800)
    done["fov"] = page.evaluate("() => window.__director_store.getState()"
                                ".objects.find((o) => o.kind === 'camera').camera.fov")

    page.evaluate(SEL_CAMERA)
    page.wait_for_timeout(400)
    done["selectCharacter"] = page.evaluate(SEL_CHARACTER, CHARACTER)
    page.wait_for_timeout(400)

    ruler = page.locator("[data-director-timeline-ruler]").first
    box = ruler.bounding_box()
    if box:
        page.mouse.click(box["x"] + box["width"] * 0.75, box["y"] + box["height"] / 2)
        page.wait_for_timeout(600)
    st = page.evaluate(SCALARS)
    done["playheadAfterRulerClick"] = st["playheadTime"]
    zc = page.locator("[data-director-timeline-zoom-cluster] [data-director-timeline-zoom]")
    done["zoomButtonCount"] = zc.count()
    if zc.count():
        zc.nth(0).click()
        page.wait_for_timeout(500)
    done["zoomAfterClick"] = page.evaluate(SCALARS)["zoom"]

    col = page.locator("[data-director-timeline-collapse]").first
    if col.count():
        col.click()
        page.wait_for_timeout(600)
    done["isCollapsed"] = page.evaluate(SCALARS)["isCollapsed"]
    return done


def run(browser: Any) -> dict[str, Any]:
    page, node_id = boot(browser)
    id_open = page.evaluate(ID)
    changes = make_changes(page)
    before_id = page.evaluate(ID)
    before_sc = page.evaluate(SCALARS)
    before_flat = page.evaluate(FLAT)
    close_via_button(page)
    page.reload()
    page.wait_for_timeout(3_000)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
    reopen_via_button(page)
    after_id = page.evaluate(ID)
    after_sc = page.evaluate(SCALARS)
    after_flat = page.evaluate(FLAT)
    page.close()
    keys = sorted(set(before_flat) | set(after_flat))
    return {
        "nodeId": node_id, "idOpen": id_open, "idBefore": before_id,
        "idAfter": after_id, "changes": changes,
        "beforeScalars": before_sc, "afterScalars": after_sc,
        "lostLeaves": [k for k in keys if k in before_flat and k not in after_flat],
        "gainedLeaves": [k for k in keys if k not in before_flat and k in after_flat],
        "changedLeaves": [k for k in keys if k in before_flat and k in after_flat
                          and before_flat[k] != after_flat[k]],
        "sameLeafCount": len([k for k in keys if k in before_flat and k in after_flat
                              and before_flat[k] == after_flat[k]]),
    }


def check_1(r: dict[str, Any]) -> None:
    ids = {r["idOpen"]["sourceNode"], r["idBefore"]["sourceNode"],
           r["idAfter"]["sourceNode"]}
    assert len(ids) == 1, f"全程不是同一个节点：{ids}"
    assert r["idAfter"]["sourceNode"] == r["nodeId"], r["idAfter"]


def check_2(r: dict[str, Any]) -> None:
    b, a = r["beforeScalars"], r["afterScalars"]
    assert RENAME_TO in b["names"] and RENAME_TO in a["names"], (b["names"], a["names"])
    assert b["fov"] == 46 and a["fov"] == 46, (b["fov"], a["fov"])
    for k in ("duration", "editorMode", "isPlaying", "shotEnd", "tracks", "zoom"):
        assert a[k] == b[k], (k, b[k], a[k])


def check_3(r: dict[str, Any]) -> None:
    b, a = r["beforeScalars"], r["afterScalars"]
    assert b["pastLen"] >= 2, f"备料不足：刷新前只有 {b['pastLen']} 条历史"
    assert a["pastLen"] == 0, a["pastLen"]
    # 整棵子树消失，而不只是长度变 0
    past_leaves = [k for k in r["lostLeaves"] if k.startswith("history.past[")]
    assert len(past_leaves) >= 300, f"消失的历史叶子只有 {len(past_leaves)} 枚"
    assert all(not k.startswith("history.past[") for k in r["gainedLeaves"])


def check_4(r: dict[str, Any]) -> None:
    b, a = r["beforeScalars"], r["afterScalars"]
    # 备料：刷新前确实选中了角色（不是默认值）
    assert b["selectedObjectId"] == CHARACTER, b["selectedObjectId"]
    assert b["selectedTrackId"] and b["selectedTrackId"] != "", b["selectedTrackId"]
    # 刷新后原样回来 —— P4 就是被这一格推翻的
    assert a["selectedObjectId"] == b["selectedObjectId"], (b, a)
    assert a["selectedObjectIds"] == b["selectedObjectIds"], (b, a)
    assert a["selectedTrackId"] == b["selectedTrackId"], (b, a)


def check_5(r: dict[str, Any]) -> None:
    b, a = r["beforeScalars"], r["afterScalars"]
    assert b["isCollapsed"] == "true", f"备料不足：折叠没生效 {b['isCollapsed']}"
    assert a["isCollapsed"] == "false", a["isCollapsed"]
    assert b["timelineHeightAttr"] != a["timelineHeightAttr"], (b, a)


def check_6(r: dict[str, Any]) -> None:
    b, a = r["beforeScalars"], r["afterScalars"]
    assert a["generation"] == (b["generation"] or 0) + 1, (b["generation"], a["generation"])
    assert a["sessionId"] != b["sessionId"], (b["sessionId"], a["sessionId"])
    assert b["lastCommandResult"] == "SET" and a["lastCommandResult"] == "null", (b, a)


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
            failures.append(f"run: {exc}")
            got["run"] = {}
        browser.close()
    results.update(got)
    checks = [
        ("every-step-stays-on-the-same-source-node", lambda: check_1(got.get("run", {}))),
        ("document-content-survives-the-reload", lambda: check_2(got.get("run", {}))),
        ("the-whole-history-subtree-does-not-survive-the-reload", lambda: check_3(got.get("run", {}))),
        ("the-selection-and-selected-track-survive-the-reload", lambda: check_4(got.get("run", {}))),
        ("the-timeline-collapse-state-does-not-survive-the-reload", lambda: check_5(got.get("run", {}))),
        ("the-session-identity-is-rebuilt-on-reload", lambda: check_6(got.get("run", {}))),
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
