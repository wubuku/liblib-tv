#!/usr/bin/env python3
"""batch 709 验收器 —— 导演台的历史与手势活多久 —— 关掉再打开还能不能撤？

★★★ Batch 828 更正（2026-10-21）：**本脚本原来断言的 4 条里有 3 条是假的，
而它一直是绿的** ⟹ ★★ 它**绿在「测的不是那个东西」上**。

## ★ 原脚本错在哪（三个缺陷叠在一起）

1. `fresh()` 走 617 仪器的 `addNode` + `openDirectorDesk(nodes.at(-1).id)` ⟹
   开的是**后门新建**的那个节点；而 `open_desk()` 用
   `page.locator("[data-open-director]").first` ⟹ 点的是**页面上唯一渲染出
   节点卡的那个**（种子节点 `b-bTLLuU4w5q`）⟹ ⟹ **两次开台不是同一个节点**。
2. 后门造的节点**根本不渲染节点卡**（react-flow 只渲染视口内的节点）⟹
   页面上 `.first` **永远**不是它 ⟹ 原脚本恒定地复现那个假象。
3. batch 827 查实：709 当时还**连真实按钮都点不动**（真因是**页面不 hydration**
   —— Next 16 默认拦截来自 `127.0.0.1` 的 dev 资源）⟹ 它把账记成
   「用户路径未取证」。

★ 后果：判据 1/2/4 断言的「关台丢工作」是**换节点**的必然结果 ⟹ **假**；
判据 3 断言的「第二次关台重开什么都不丢」是**同节点**的真实读数 ⟹ **对**。
★ 也就是说：**一条会持续把假结论钉成「事实」的门禁** ⟹ 828 修掉它。

## ★ 本脚本现在的做法（batch 828）

- **全程一个节点**：种子节点（页面上真有节点卡）；按钮**按 node id 定位**
  （`.react-flow__node[data-id="<id>"] [data-open-director]`），**绝不 `.first`**；
- **每一步都断言 `data-director-source-node-id` 没变**（前提判据，先于功能判据）；
- **先证明页面 hydration 了**（batch 827 的教训：页面不 hydration 时读数一律作废）；
- 期望值按 828 的实测重写：关台**保留**已提交内容与历史、方向键手势被
  **提交**成一条 `camera-fov` 条目、刷新页面**内容留住但历史归零**。

## ★ 判据名的对应（旧名 → 新名，见 batch 828 README §4）

| 旧名（709） | 新名（828 改写后） |
| --- | --- |
| `closing-the-desk-discards-an-uncommitted-gesture-change` | `closing-the-desk-commits-the-open-gesture-instead-of-discarding-it` |
| `the-first-close-and-reopen-loses-everything-committed-including-history` | `closing-and-reopening-the-same-node-keeps-committed-work-and-history` |
| `the-second-close-and-reopen-loses-nothing-not-even-the-history-entry` | `a-second-close-and-reopen-also-keeps-everything` |
| `a-page-reload-then-reopen-behaves-like-the-first-close` | `a-page-reload-keeps-committed-content-but-drops-the-history` |
| `the-open-button-opens-the-desk-on-a-node-that-never-had-a-director-session` | 同名（未改） |

★ 另**新增两条前提判据**（709 完全没有）：
`the-page-is-hydrated-before-any-reading-is-taken`、
`every-step-stays-on-the-same-source-node`。

## ★ 本脚本的产物

`runtime-audit.json`（709 原产物）**保持不动** —— 它是历史记录。
本脚本现在写到 **`runtime-audit-828-correction.json`**，并在 stdout 打印
两者的路径，避免有人把旧产物当成现行结论。
"""
import copy
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch709-2026-10-01"
LEGACY_AUDIT = AUDIT_DIR / "runtime-audit.json"
AUDIT_OUT = AUDIT_DIR / "runtime-audit-828-correction.json"
W, DESK_H = 1280, 1150
BASE_URL = "http://localhost:4317"
RENAME_TO = "改名试试709"

PREDICTIONS = {
    "P1": "关台再重开后 history.past 归零，之后 Cmd+Z 记 UNDO/NOOP",
    "P2": "归零的原因是换了一个 projectId",
    "P3": "连开关两次会每次都归零",
    "P4": "开着手势关台，未提交的改动被丢弃",
    "P5": "已提交的内容在关台重开后保留",
}
# ★★ Batch 828：以上五条是 709 **写死在代码里**的预测。828 的实测把它们
#   全部推翻 —— 推翻的理由不是「读数变了」，而是「**测的不是同一个节点**」。
#   这里保留原文（不可重写的历史），把现行结论写在 PREDICTIONS_828 里。
PREDICTIONS_828 = {
    "Q1": "★ 前提：页面已 hydration ⟹ 否则读数一律作废（batch 827 的教训）",
    "Q2": "★ 前提：每一步的 data-director-source-node-id 都是同一个节点",
    "Q3": "关台时开着方向键手势 ⟹ 手势被**提交**成一条 camera-fov 条目（不是丢弃）",
    "Q4": "同一个节点关台重开 ⟹ **保留**已提交内容与历史（projectId 一字不变）",
    "Q5": "第二次关台重开 ⟹ 同样**保留**（709 观测到的那条是对的）",
    "Q6": "刷新页面再重开 ⟹ **内容留住、历史归零**（709 说「内容也丢」是错的）",
    "Q7": "从未开过导演台的节点上点真实按钮 ⟹ 导演台能打开",
}

READ_HYDRATION = r"""() => {
  const b = document.querySelector('[data-open-director]');
  if (!b) return {found: false};
  const keys = Object.keys(b).filter((k) => k.startsWith('__react'));
  return {found: true, keys: keys,
          hasOnClick: keys.some((k) => typeof b[k].onClick === 'function')};
}"""

READ = r"""() => {
  const s = window.__director_store.getState();
  const h = s.history; const r = s.lastCommandResult;
  const w = document.querySelector('[data-director-workspace]');
  const cam = s.objects.find((o) => o.kind === 'camera');
  return {
    deskOpen: !!w,
    projectId: w ? w.getAttribute('data-director-project-id') : null,
    sourceNode: w ? w.getAttribute('data-director-source-node-id') : null,
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

# ★★ 唯一的「新建节点」入口：画布的「新建节点」纯 UI 入口至今没找到
#   （batch 823 已记）⟹ 这里只用它**多造一个节点**当对照，不参与测量对象。
ADD_NODE = r"""() => {
  const s = window.__libtv_store.getState();
  s.addNode('script-execution', { title: 'Batch 709 对照' });
}"""


def read(page: Page) -> dict[str, Any]:
    return page.evaluate(READ)


def btn_for(node_id: str) -> str:
    """★ 按**节点 id** 定位按钮 ⟹ 绝不 `.first`（`.first` 会命中另一个节点）。"""
    return '.react-flow__node[data-id="%s"] [data-open-director]' % node_id


def fresh(browser: Any) -> tuple[Page, str]:
    """★ 返回 (page, node_id)：**种子节点**（页面上真有节点卡的那个）。

    ★ 828 更正：709 的 `fresh()` 走 617 仪器开后门节点 ⟹ 而重开用 `.first`
      ⟹ 两次根本不是同一个节点 ⟹ 整批作废（batch 710 已定性）。
    """
    page = browser.new_page(viewport={"width": W, "height": DESK_H},
                            device_scale_factor=1)
    page.goto(f"{BASE_URL}/?batch709c=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__libtv_ui_store "
        "&& window.__director_store)", timeout=60_000)
    page.wait_for_timeout(800)
    node_id = page.evaluate("""() => {
      const nodes = window.__libtv_store.getState().getActiveCanvas().nodes
        .filter((n) => n.type === 'script-execution');
      return nodes.length === 1 ? nodes[0].id : null;
    }""")
    if not node_id:
        raise AssertionError("画布上的 script-execution 节点不唯一")
    # ★ 后门多造一个节点 ⟹ 用来证明「换节点」才是变量（S6/S7 那类对照）
    page.evaluate(ADD_NODE)
    page.wait_for_timeout(1_200)
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(300)
    return page, node_id


def open_desk(page: Page, node_id: str) -> None:
    """★ 真实按钮，**按 node id** 定位。"""
    page.locator(btn_for(node_id)).first.click()
    page.locator("[data-director-workspace]").wait_for(state="visible", timeout=30_000)
    page.wait_for_timeout(1_800)
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    # ★ 选中相机**必须成功** —— 否则改名输入框压根不出现，而「等 30 秒找不到元素」
    #   这条错会把真正的错因（树还没渲染）盖住 ⟹ 这里显式重试并断言。
    page.wait_for_function(
        "() => document.querySelectorAll('[data-director-tree] [role=\"treeitem\"]').length > 0",
        timeout=20_000)
    sel: dict[str, Any] = {"ok": False}
    for _ in range(20):
        sel = page.evaluate(SEL_CAMERA)
        if sel.get("ok"):
            break
        page.wait_for_timeout(300)
    if not sel.get("ok"):
        raise AssertionError("选中相机失败：%s" % sel)
    page.wait_for_selector("[data-director-object-name]", timeout=20_000)
    page.wait_for_timeout(300)


def close_desk(page: Page) -> None:
    page.locator("[data-close-director]").first.click()
    page.locator("[data-director-workspace]").wait_for(state="detached", timeout=15_000)
    page.wait_for_timeout(800)


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


def arm_gesture(browser: Any) -> dict[str, Any]:
    """Q3：开着方向键手势关台 ⟹ 手势被**提交**（不是丢弃）。"""
    page, nid = fresh(browser)
    open_desk(page, nid)
    s0 = read(page)
    arrow_keys(page, 3)
    s1 = read(page)
    close_desk(page)
    s2 = read(page)
    open_desk(page, nid)
    s3 = read(page)
    page.close()
    return {"node": nid, "s0": s0, "s1": s1, "s2": s2, "s3": s3}


def arm_two_cycles(browser: Any) -> dict[str, Any]:
    """Q4/Q5：同一个节点，连开关两次。"""
    page, nid = fresh(browser)
    open_desk(page, nid)
    rename(page)
    a = read(page)
    close_desk(page)
    open_desk(page, nid)
    b = read(page)
    page.mouse.click(640, 900)
    page.wait_for_timeout(600)
    page.evaluate(SEL_CAMERA)
    page.wait_for_timeout(500)
    rename(page)
    c = read(page)
    close_desk(page)
    open_desk(page, nid)
    d = read(page)
    page.close()
    return {"node": nid, "afterRename1": a, "afterCycle1": b,
            "afterRename2": c, "afterCycle2": d}


def arm_reload(browser: Any) -> dict[str, Any]:
    """Q6：刷新页面后重开 ⟹ 内容留住、历史归零。"""
    page, nid = fresh(browser)
    open_desk(page, nid)
    rename(page)
    a = read(page)
    close_desk(page)
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(3_000)
    open_desk(page, nid)
    b = read(page)
    page.mouse.click(640, 900)
    page.wait_for_timeout(600)
    page.keyboard.press("Meta+z")
    page.wait_for_timeout(700)
    c = read(page)
    page.close()
    return {"node": nid, "afterRename": a, "afterReloadReopen": b, "afterUndo": c}


def arm_open_button(browser: Any) -> dict[str, Any]:
    """Q7：从未开过导演台的节点上点真实按钮 —— 两次独立尝试。"""
    out = []
    for attempt in (1, 2):
        page = browser.new_page(viewport={"width": W, "height": DESK_H},
                                device_scale_factor=1)
        page.goto(f"{BASE_URL}/?batch709c=1", wait_until="networkidle", timeout=90_000)
        page.wait_for_function(
            "() => Boolean(window.__libtv_store && window.__libtv_ui_store "
            "&& window.__director_store)", timeout=60_000)
        page.wait_for_timeout(800)
        nid = page.evaluate("""() => {
          const nodes = window.__libtv_store.getState().getActiveCanvas().nodes
            .filter((n) => n.type === 'script-execution');
          return nodes.length === 1 ? nodes[0].id : null;
        }""")
        if attempt == 2:
            page.reload(wait_until="networkidle")
            page.wait_for_timeout(3_000)
        has_btn = page.locator(btn_for(nid)).count() > 0
        opened = False
        if has_btn:
            page.locator(btn_for(nid)).first.click()
            try:
                page.locator("[data-director-workspace]").wait_for(
                    state="visible", timeout=8_000)
                opened = True
            except Exception:  # noqa: BLE001
                opened = False
        out.append({"attempt": attempt, "node": nid, "hasButton": has_btn,
                    "opened": opened, "reloadedFirst": attempt == 2})
        page.close()
    return {"attempts": out}


# ── 判据（纯函数：吃读数吐断言）───────────────────────────────────────────────
def check_hydration(got: dict[str, Any]) -> None:
    """Q1 前提：页面**已 hydration**（否则读数一律作废）。"""
    assert got["hydration"]["found"] is True, got["hydration"]
    assert got["hydration"]["hasOnClick"] is True, got["hydration"]


def check_same_node(got: dict[str, Any]) -> None:
    """Q2 前提：每一步的 `data-director-source-node-id` 都是**同一个**节点。"""
    stages = {
        "uncommitted_gesture": ("s0", "s1", "s2", "s3"),
        "two_cycles": ("afterRename1", "afterCycle1", "afterRename2", "afterCycle2"),
        "reload": ("afterRename", "afterReloadReopen", "afterUndo"),
    }
    for arm, keys in stages.items():
        nid = got[arm]["node"]
        for k in keys:
            stage = got[arm][k]
            if stage.get("deskOpen"):
                # ★ 台开着 ⟹ `data-director-source-node-id` 必须就是那个节点
                assert stage["sourceNode"] == nid, (arm, k, stage, nid)
            else:
                # ★ 台关着 ⟹ 台面元素不存在 ⟹ 读数**必然**是 null（不是 null 就是 bug）
                assert stage["sourceNode"] is None, (arm, k, stage)


def check_gesture_committed(got: dict[str, Any]) -> None:
    """Q3：开着方向键手势关台 ⟹ 手势被**提交**成一条 `camera-fov` 条目。"""
    g = got["uncommitted_gesture"]
    assert g["s0"]["fovStore"] == 43, g["s0"]
    assert g["s1"]["fovStore"] == 46, g["s1"]
    assert g["s1"]["active"] == "camera-fov", g["s1"]
    assert g["s1"]["last"] == "UPDATE_CAMERA/COMMITTED", g["s1"]
    assert g["s1"]["pastLen"] == 0, g["s1"]
    # 关台**不是**丢弃手势 ⟹ 重开后 fov 保留 46、且多了一条 camera-fov
    assert g["s3"]["fovStore"] == 46, g["s3"]
    assert g["s3"]["pastLen"] == 1, g["s3"]
    assert g["s3"]["pastKinds"] == ["camera-fov"], g["s3"]
    assert g["s3"]["projectId"] == g["s0"]["projectId"], (g["s0"], g["s3"])


def check_keeps_work(got: dict[str, Any]) -> None:
    """Q4：同一个节点关台重开 ⟹ **保留**已提交内容与历史。"""
    t = got["two_cycles"]
    assert RENAME_TO in t["afterRename1"]["names"], t["afterRename1"]
    assert t["afterRename1"]["pastLen"] == 1, t["afterRename1"]
    b = t["afterCycle1"]
    assert RENAME_TO in b["names"], b
    assert b["pastLen"] == 1, b
    assert b["pastKinds"] == ["UPDATE_OBJECT"], b
    assert b["projectId"] == t["afterRename1"]["projectId"], \
        "projectId 变了 ⟹ 那「保留」就不是同一份工作"


def check_second_cycle(got: dict[str, Any]) -> None:
    """Q5：第二次关台重开 ⟹ 同样保留（709 观测到的那条是对的）。"""
    t = got["two_cycles"]
    c, d = t["afterRename2"], t["afterCycle2"]
    assert RENAME_TO in c["names"] and c["pastLen"] == 1, c
    assert RENAME_TO in d["names"], d
    assert d["pastLen"] == 1, d
    assert d["pastKinds"] == ["UPDATE_OBJECT"], d
    assert d["projectId"] == c["projectId"], (c["projectId"], d["projectId"])


def check_reload(got: dict[str, Any]) -> None:
    """Q6：刷新页面 ⟹ **内容留住、历史归零**（709 说「内容也丢」是错的）。"""
    r = got["reload"]
    assert RENAME_TO in r["afterRename"]["names"], r["afterRename"]
    b = r["afterReloadReopen"]
    assert RENAME_TO in b["names"], b
    assert b["pastLen"] == 0, b
    assert b["projectId"] == r["afterRename"]["projectId"], (r["afterRename"], b)
    # 历史没了 ⟹ Cmd+Z 只能是 NOOP（**不是** 709 说的那样「内容也丢」）
    assert r["afterUndo"]["last"] == "UNDO/NOOP", r["afterUndo"]


def check_open_button(got: dict[str, Any]) -> None:
    """Q7：真实按钮在从未开过导演台的节点上**能**开台。"""
    for rec in got["open_button"]["attempts"]:
        assert rec["hasButton"] is True, rec
        assert rec["opened"] is True, rec


# ── 阴性对照：每条**只**翻它自己那一条 ────────────────────────────────────────
def neg_hydration(got: dict[str, Any]) -> dict[str, Any]:
    c = copy.deepcopy(got)
    c["hydration"]["hasOnClick"] = False
    return c


def neg_same_node(got: dict[str, Any]) -> dict[str, Any]:
    c = copy.deepcopy(got)
    c["two_cycles"]["afterCycle1"]["sourceNode"] = "另一个节点"
    return c


def neg_gesture_discarded(got: dict[str, Any]) -> dict[str, Any]:
    c = copy.deepcopy(got)
    c["uncommitted_gesture"]["s3"]["fovStore"] = 43
    return c


def neg_lost_work(got: dict[str, Any]) -> dict[str, Any]:
    c = copy.deepcopy(got)
    c["two_cycles"]["afterCycle1"]["pastLen"] = 0
    return c


def neg_second_cycle(got: dict[str, Any]) -> dict[str, Any]:
    c = copy.deepcopy(got)
    c["two_cycles"]["afterCycle2"]["pastLen"] = 0
    return c


def neg_reload_lost(got: dict[str, Any]) -> dict[str, Any]:
    c = copy.deepcopy(got)
    c["reload"]["afterReloadReopen"]["names"] = [
        n for n in c["reload"]["afterReloadReopen"]["names"] if n != RENAME_TO]
    return c


def neg_open_button(got: dict[str, Any]) -> dict[str, Any]:
    c = copy.deepcopy(got)
    c["open_button"]["attempts"][0]["opened"] = False
    return c


CHECKS = [
    ("the-page-is-hydrated-before-any-reading-is-taken", check_hydration),
    ("every-step-stays-on-the-same-source-node", check_same_node),
    ("closing-the-desk-commits-the-open-gesture-instead-of-discarding-it",
     check_gesture_committed),
    ("closing-and-reopening-the-same-node-keeps-committed-work-and-history",
     check_keeps_work),
    ("a-second-close-and-reopen-also-keeps-everything", check_second_cycle),
    ("a-page-reload-keeps-committed-content-but-drops-the-history", check_reload),
    ("the-open-button-opens-the-desk-on-a-node-that-never-had-a-director-session",
     check_open_button),
]

NEGATIVES = [
    ("N1 把 hydration 读数改成 not-hydrated ⟹ Q1 翻红", 0, neg_hydration),
    ("N2 把某一步的 sourceNode 改成另一个节点 ⟹ Q2 翻红", 1, neg_same_node),
    ("N3 把手势臂重开后的 fov 改成基线 43 ⟹ Q3 翻红", 2, neg_gesture_discarded),
    ("N4 把第一次关台重开的 pastLen 改成 0 ⟹ Q4 翻红", 3, neg_lost_work),
    ("N5 把第二次关台重开的 pastLen 改成 0 ⟹ Q5 翻红", 4, neg_second_cycle),
    ("N6 把刷新臂的名字里去掉那次改名 ⟹ Q6 翻红", 5, neg_reload_lost),
    ("N7 把按钮臂的 opened 改成 False ⟹ Q7 翻红", 6, neg_open_button),
]


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {
        "predictions_709": PREDICTIONS,
        "predictions_828": PREDICTIONS_828,
        "correction": "batch 828：709 的判据 1/2/4 测的不是同一个节点 ⟹ 结论作废",
    }
    failures: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        got: dict[str, Any] = {}
        # ★ 前提读数单独拿一个页面
        hp = browser.new_page(viewport={"width": W, "height": DESK_H})
        hp.goto(f"{BASE_URL}/?batch709c=1", wait_until="networkidle", timeout=90_000)
        hp.wait_for_function(
            "() => Boolean(window.__libtv_store && window.__libtv_ui_store "
            "&& window.__director_store)", timeout=60_000)
        hp.wait_for_timeout(1_000)
        got["hydration"] = hp.evaluate(READ_HYDRATION)
        hp.close()
        for name, fn in (("uncommitted_gesture", arm_gesture),
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
    # ★ 臂失败要**当场**报出来（否则后面负控的 KeyError 会把真正的错因盖掉）
    for name, fn in (("uncommitted_gesture", arm_gesture),
                     ("two_cycles", arm_two_cycles),
                     ("reload", arm_reload),
                     ("open_button", arm_open_button)):
        if not got.get(name):
            print("!! 臂失败：%s" % name)
            for f in failures:
                if f.startswith(name + ":"):
                    print("   ->", f[:600])

    summary: dict[str, bool] = {}
    for name, fn in CHECKS:
        try:
            fn(got)
            summary[name] = True
        except Exception as exc:  # noqa: BLE001
            summary[name] = False
            failures.append(f"{name}: {exc}")
    results["summary"] = summary

    # ★ 阴性对照：每条**只**翻它自己那一条（读的字段互不重叠）
    neg_report = []
    for label, idx, builder in NEGATIVES:
        try:
            c2 = builder(got)
        except Exception as exc:  # noqa: BLE001
            neg_report.append({"name": label, "期望翻红": CHECKS[idx][0],
                               "实际翻红": [], "ok": False,
                               "错误": "负控构造失败：%s" % exc})
            failures.append(f"{label} → 负控构造失败：{exc}")
            continue
        turned = []
        for name, fn in CHECKS:
            try:
                fn(c2)
            except Exception:  # noqa: BLE001
                turned.append(name)
        ok = turned == [CHECKS[idx][0]]
        neg_report.append({"name": label, "期望翻红": CHECKS[idx][0],
                           "实际翻红": turned, "ok": ok})
        if not ok:
            failures.append(f"{label} → 实际翻红 {turned}")
    results["阴性对照"] = neg_report
    results["failures"] = failures

    AUDIT_OUT.write_text(
        json.dumps(results, ensure_ascii=False, indent=1, default=str))
    for name, ok in summary.items():
        print(("PASS " if ok else "FAIL ") + name)
    for n in neg_report:
        print(("PASS " if n["ok"] else "FAIL ") + n["name"]
              + " → 实际翻红 " + ",".join(n["实际翻红"]))
    for f in failures:
        print("  ->", f[:400])
    print("\n%d/%d 通过" % (sum(1 for v in summary.values() if v), len(summary)))
    print("产物：%s" % AUDIT_OUT.relative_to(ROOT))
    print("历史产物（未改动，保留 709 当时的读数）：%s"
          % (LEGACY_AUDIT.relative_to(ROOT) if LEGACY_AUDIT.exists() else "（无）"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
