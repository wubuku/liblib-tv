#!/usr/bin/env python3
"""batch 706 验收：手势的原子性 —— 悬手势归谁、一次交互并成几条、`Cmd+Z` 在输入框里去哪了

## 起点

704 记下一条读数：`shot-end` 填越界值 9 按 `Tab` 之后，
`activeGesture` **一直开着**（「不自动收」），账上写 `GESTURE_BEGIN` / `COMMITTED`。
705 补上另一半：12 枚 `transform:*` 数字框提交后账上一律记 `GESTURE_COMMIT`。

于是本批 originally 的问题写得很具体：
**「悬着手势时做第二次编辑，撤销一次能撤掉什么、
悬着手势的 baseline 会不会被写进后来那次真实编辑的撤销条目。」**

## 五条预测（写死在代码里，先于任何测量）

- **P1** 活手势在手时，第 1 次 `Cmd+Z` 会先取消手势（回滚文档）再撤上一条
- **P2** `Escape` 在活手势上把值回滚，而且账上分得清「回滚了」和「什么都没发生」
- **P3** 悬着手势是「那次**被拒**的编辑」留下的
- **P4** 一次聚焦内 N 次方向键会并成 1 条撤销条目（手势机制本来就是为了这个）
- **P5** 悬着手势的 baseline 会被写进后来那次真实编辑的撤销条目

## 结果：四条预测被推翻，方向各不相同

| 预测 | 结果 |
|---|---|
| **P1** | **推翻**。按键**根本没进** `undoDirector`；它做的是别的事（见判据 4、5） |
| **P2** | **一半**。回滚成立（43→46→43），但账上写 `GESTURE_CANCEL` / `NOOP` / `projectChanged: false` ⟹ **分不清** |
| **P3** | **推翻**。手势归 `camera-fov`，**被接受的值和根本不填都留**，反向 `Tab` 才不留 |
| **P4** | **成立**。3 次改值 → 1 条，覆盖恰好 2 个字段 |
| **P5** | **推翻**。9 次测量里没有任何一条条目跨到无关字段 |

**P4 成立 ⟹ 手势的原子性是对的，本批的原始担心不成立**（这是被推翻的预测，不是缺陷）。

## 本批最值钱的一条：`Cmd+Z` 在输入框里不是撤销

焦点在任一输入框内时 `Cmd+Z` **到不了** `undoDirector` ——
`DirectorDesk.tsx:484` 的 `if (isEditable) return;` 排在修饰键分支**之前**。
但它也不是「什么都没发生」：**浏览器自己的表单撤销**接管了这次按键。

实测到的完整链条（探针 f，六行读数）：

1. 改名已提交（`nameStore = 改名试试F706`），`Tab` 走到 `camera-switch`
2. 点 `shot-end` 按 `Tab` → 焦点落在 fov 滑块，开出 `camera-fov` 手势，按一次 `ArrowRight`（fov 43→44）
3. 按 `Cmd+Z` —— 此刻 **`nameDom` 变成原名、`nameStore` 还是新名**、焦点跳到 `object-name`、手势被**提交**成一条 `camera-fov` 条目
4. 点画布 → **改名被静默回退**，并且**为这次回退新写了一条 `UPDATE_OBJECT` / `COMMITTED` 条目**

**用户什么都没对那个名字框做，改名却消失了，历史里还多了一条「编辑」。**
对照臂（不发 `Cmd+Z`，只点画布）证明回退不是画布点击本身造成的。

## 顺带纠正 704（读数全部存活，两处归属要换）

704 的表格里 `shot-end` 那一行写「填 9 → `GESTURE_BEGIN` / `COMMITTED` → 留下悬手势」。
**手势不是 `shot-end` 留下的，是 `Tab` 把焦点交给下一枚手势字段时它自己的 `onFocus` 开的。**
四条臂的证据：被拒的 9、被接受的 6、什么都不填 —— 三条都留下同一个 `camera-fov` 手势；
只有 `Shift+Tab`（焦点直接离开面板、落到 `body`）不留。

## 六条判据

1. `the-open-gesture-belongs-to-the-next-focusable-slider-not-to-the-rejected-edit`
2. `three-arrow-presses-collapse-into-one-entry-covering-only-the-two-fields-touched`
3. `escape-on-a-live-gesture-reverts-the-document-yet-is-ledgered-as-noop`
4. `cmd-z-inside-a-focused-input-never-reaches-undo`
5. `cmd-z-inside-a-focused-input-stages-a-reverse-edit-that-the-next-click-commits`
6. `ledger-ownership-flips-with-timing`

## 纪律

- 每格一个全新页面；全部用真实键盘/鼠标事件。
- 判「有没有变」用**全 store 逐叶投影**；判「条目覆盖了什么」用**条目的 before/after 逐叶差**。
- **零 store 写入**；不改 `src/`。
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch706-2026-10-01"
W, DESK_H = 1280, 1150

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

PREDICTIONS = {
    "P1": "活手势在手时第 1 次 Cmd+Z 会先取消手势再撤上一条",
    "P2": "Escape 在活手势上回滚值，且账上分得清回滚与无事发生",
    "P3": "悬着手势是那次被拒的编辑留下的",
    "P4": "一次聚焦内 N 次方向键并成 1 条撤销条目",
    "P5": "悬着手势的 baseline 会被写进后来那次真实编辑的撤销条目",
}

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
    if (k === 'history' || k === 'lastCommandResult') continue;
    walk(s[k], k, 0);
  }
  return o;
}"""

# 条目读面：每条历史条目的 before/after 到底差在哪几个字段
SPANS = r"""() => {
  const h = window.__director_store.getState().history;
  const flat = (v, p, d, o) => {
    if (d > 8) { o[p] = String(v); return; }
    if (v === null || typeof v !== 'object') { o[p] = JSON.stringify(v); return; }
    if (Array.isArray(v)) { v.forEach((x, i) => flat(x, p + '[' + i + ']', d + 1, o)); return; }
    for (const k of Object.keys(v).sort()) flat(v[k], p + '.' + k, d + 1, o);
  };
  const spans = (before, after) => {
    if (before === undefined || after === undefined) return ['UNDEFINED_DOC'];
    const a = {}; const b = {};
    flat(before, '', 0, a); flat(after, '', 0, b);
    return Object.keys(a).concat(Object.keys(b).filter((k) => !(k in a)))
      .filter((k, i, arr) => arr.indexOf(k) === i)
      .filter((k) => a[k] !== b[k]).sort();
  };
  const g = h.activeGesture;
  return {
    pastLen: (h.past || []).length,
    futureLen: (h.future || []).length,
    active: g ? { commandKind: g.commandKind, fieldScope: g.fieldScope } : null,
    past: (h.past || []).map((e, i) => ({ i, kind: e.commandKind,
      span: spans(e.before, e.after) })),
  };
}"""

LAST = r"""() => {
  const r = window.__director_store.getState().lastCommandResult;
  return r ? { commandKind: r.commandKind, disposition: r.disposition,
    reason: r.reason, projectChanged: r.projectChanged,
    historyEntries: r.historyEntries } : null;
}"""

FIELDS = r"""() => {
  const s = window.__director_store.getState();
  const ae = document.activeElement;
  const pick = (sel) => document.querySelector(sel);
  const cam = s.objects.find((o) => o.kind === 'camera');
  return {
    focus: ae ? (ae.getAttributeNames()
      .filter((n) => n.startsWith('data-director')).sort().join(',') || ae.tagName)
      : 'none',
    fovDom: (pick('[data-director-camera-fov]') || {}).value,
    nameDom: (pick('[data-director-object-name]') || {}).value,
    shotDom: (pick('[data-director-shot-end]') || {}).value,
    fovStore: cam ? cam.camera.fov : null,
    nameStore: cam ? cam.name : null,
    shotEndStore: s.shots[0] ? s.shots[0].endTime : null,
  };
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


def snap(page: Page, label: str) -> dict[str, Any]:
    return {"label": label, "flat": page.evaluate(FLAT),
            "spans": page.evaluate(SPANS), "last": page.evaluate(LAST),
            "fields": page.evaluate(FIELDS)}


def fresh(browser: Any) -> Page:
    page = browser.new_page(viewport={"width": W, "height": DESK_H},
                            device_scale_factor=1)
    b617.open_desk(page)
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(300)
    ok = page.evaluate(SELECT_CAMERA)
    assert ok["ok"], f"选不中机位：{ok}"
    page.wait_for_timeout(500)
    return page


def tab_into_fov(page: Page) -> None:
    """真实键盘路径：点 shot-end 再按 Tab（704 发现的入口，判据 1 要验的就是它）"""
    el = page.locator("[data-director-shot-end]").first
    el.click()
    page.wait_for_timeout(200)
    el.press("Tab")
    page.wait_for_timeout(500)


def fill_field(page: Page, selector: str, value: str, submit: str = "Tab") -> None:
    el = page.locator(selector).first
    el.click()
    page.wait_for_timeout(200)
    el.fill(value)
    page.wait_for_timeout(300)
    if submit:
        el.press(submit)
        page.wait_for_timeout(600)


# ---------------------------------------------------------------- 判据 1
def criterion_1(browser: Any) -> dict[str, Any]:
    """悬着手势归谁所有：四条臂"""
    arms: dict[str, Any] = {}
    for name, submit, value in (("rejected-9", "Tab", "9"),
                                ("accepted-6", "Tab", "6"),
                                ("no-value", "Tab", None),
                                ("shift-tab", "Shift+Tab", "6")):
        page = fresh(browser)
        el = page.locator("[data-director-shot-end]").first
        el.click()
        page.wait_for_timeout(250)
        if value is not None:
            el.fill(value)
            page.wait_for_timeout(250)
        el.press(submit)
        page.wait_for_timeout(700)
        s = snap(page, name)
        arms[name] = {
            "active": s["spans"]["active"],
            "focus": s["fields"]["focus"],
            "pastLen": s["spans"]["pastLen"],
            "pastKinds": [e["kind"] for e in s["spans"]["past"]],
            "shotEndStore": s["fields"]["shotEndStore"],
            "last": s["last"],
        }
        page.close()
    return arms


def check_1(arms: dict[str, Any]) -> None:
    # 三条正向臂：手势归 camera-fov，焦点在 fov 滑块上
    for name in ("rejected-9", "accepted-6", "no-value"):
        a = arms[name]
        assert a["active"] and a["active"]["commandKind"] == "camera-fov", (
            f"{name}: 手势归属不是 camera-fov，而是 {a['active']}")
        assert a["focus"] == "data-director-camera-fov", (
            f"{name}: 焦点不在 fov 滑块上，而是 {a['focus']}")
    # 被拒的那条：一条叶子都没变、历史没长（复现 704 的读数）
    assert arms["rejected-9"]["shotEndStore"] == 8, arms["rejected-9"]
    assert arms["rejected-9"]["pastLen"] == 0, arms["rejected-9"]
    # 被接受的那条：值落了、有一条 UPDATE_SHOT（复现 704 的读数）
    assert arms["accepted-6"]["shotEndStore"] == 6, arms["accepted-6"]
    assert arms["accepted-6"]["pastKinds"] == ["UPDATE_SHOT"], arms["accepted-6"]
    # 反向 Tab：焦点直接离开面板落到 body，于是没有手势
    assert arms["shift-tab"]["active"] is None, arms["shift-tab"]
    assert arms["shift-tab"]["focus"].lower() == "body", arms["shift-tab"]


# ---------------------------------------------------------------- 判据 2
def criterion_2(browser: Any) -> dict[str, Any]:
    """一次聚焦内 N 次方向键并成几条、每条覆盖什么"""
    out: dict[str, Any] = {}
    page = fresh(browser)
    steps = [snap(page, "keyboard/S0")]
    tab_into_fov(page)
    steps.append(snap(page, "keyboard/S1 Tab 进 fov"))
    for i in (1, 2, 3):
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(320)
        steps.append(snap(page, f"keyboard/S1+{i}"))
    page.mouse.click(640, 900)
    page.wait_for_timeout(800)
    steps.append(snap(page, "keyboard/S2 点画布收尾"))
    out["keyboard"] = steps
    page.close()

    page = fresh(browser)
    m = [snap(page, "mouse/S0")]
    page.locator("[data-director-camera-fov]").first.click()
    page.wait_for_timeout(600)
    m.append(snap(page, "mouse/S1 点 range（跳值+pointerup 提交）"))
    for _ in range(3):
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(300)
    m.append(snap(page, "mouse/S2 再 3 次方向键"))
    page.mouse.click(640, 900)
    page.wait_for_timeout(800)
    m.append(snap(page, "mouse/S3 点画布收尾"))
    out["mouse"] = m
    page.close()
    return out


def check_2(data: dict[str, Any]) -> None:
    kb = data["keyboard"]
    # 3 次方向键期间：值一路在变，账上一条都不长
    values = [s["fields"]["fovStore"] for s in kb]
    assert values[1] == 43 and values[-1] == 46, values
    for s in kb[1:-1]:
        assert s["spans"]["pastLen"] == 0, s["label"]
        assert s["spans"]["active"] and s["spans"]["active"]["commandKind"] == "camera-fov", \
            s["label"]
    final = kb[-1]
    assert final["spans"]["pastLen"] == 1, final["label"]
    entry = final["spans"]["past"][0]
    assert entry["kind"] == "camera-fov", entry
    # 覆盖范围必须恰好是这次交互碰过的两个字段
    assert entry["span"] == [".objects[4].camera.fov",
                             ".timeline.tracks[1].keyframes[0].value.fov"], entry["span"]
    # 鼠标臂：一次点击一条、方向键那一组再来一条，各覆盖同样两个字段
    ms = data["mouse"]
    assert [s["spans"]["pastLen"] for s in ms] == [0, 1, 1, 2], \
        [s["label"] + ":" + str(s["spans"]["pastLen"]) for s in ms]
    for e in ms[-1]["spans"]["past"]:
        assert e["kind"] == "camera-fov", e
        assert e["span"] == [".objects[4].camera.fov",
                             ".timeline.tracks[1].keyframes[0].value.fov"], e["span"]


# ---------------------------------------------------------------- 判据 3
def criterion_3(browser: Any) -> dict[str, Any]:
    page = fresh(browser)
    steps = [snap(page, "S0")]
    tab_into_fov(page)
    for _ in range(3):
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(300)
    steps.append(snap(page, "S1 活手势 + 3 次方向键"))
    page.keyboard.press("Escape")
    page.wait_for_timeout(800)
    steps.append(snap(page, "S2 Escape"))
    page.close()
    return steps


def check_3(steps: list[dict[str, Any]]) -> None:
    base, live, after = steps
    assert base["fields"]["fovStore"] == 43, base["fields"]
    assert live["fields"]["fovStore"] == 46, live["fields"]
    # 值精确回到基线
    assert after["fields"]["fovStore"] == 43, after["fields"]
    # 文档内容全部回到基线；**选择态不回滚** —— 取消只还原文档快照，
    # 不还原 `selectedKeyframeId`。第一版判据断言「所有叶子都回滚」，
    # 被这一条推翻；这里断言真实形状并把它记成读数。
    changed = {k for k in set(base["flat"]) | set(live["flat"])
               if base["flat"].get(k) != live["flat"].get(k)}
    reverted = {k for k in changed if base["flat"].get(k) == after["flat"].get(k)}
    not_reverted = sorted(changed - reverted)
    assert "authoredObjects[4].camera.fov" in reverted, sorted(changed)
    assert "objects[4].camera.fov" in reverted, sorted(changed)
    assert not_reverted == ["timeline.selectedKeyframeId"], not_reverted
    # 账上分不清：写的是 NOOP + projectChanged:false
    last = after["last"]
    assert last["commandKind"] == "GESTURE_CANCEL", last
    assert last["disposition"] == "NOOP", last
    assert last["projectChanged"] is False, last
    assert after["spans"]["pastLen"] == 0, after["label"]


# ---------------------------------------------------------------- 判据 4
def criterion_4(browser: Any) -> dict[str, Any]:
    """Cmd+Z 在输入框内到不了 undo：两条输入框臂 + 一条 body 对照臂"""
    out: dict[str, Any] = {}
    for arm in ("fov-gesture", "name-field", "body"):
        page = fresh(browser)
        if arm == "fov-gesture":
            tab_into_fov(page)
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(350)
        elif arm == "name-field":
            page.locator("[data-director-object-name]").first.click()
            page.wait_for_timeout(350)
        before = snap(page, f"{arm}/S0")
        page.keyboard.press("Meta+z")
        page.wait_for_timeout(700)
        after1 = snap(page, f"{arm}/S1 第 1 次")
        page.keyboard.press("Meta+z")
        page.wait_for_timeout(700)
        after2 = snap(page, f"{arm}/S2 第 2 次")
        out[arm] = [before, after1, after2]
        page.close()
    return out


def check_4(data: dict[str, Any]) -> None:
    for arm in ("fov-gesture", "name-field"):
        b, a1, a2 = data[arm]
        assert a1["spans"] == b["spans"], (arm, "第 1 次按压改变了 history")
        assert a2["spans"] == b["spans"], (arm, "第 2 次按压改变了 history")
        assert a1["flat"] == b["flat"], (arm, "第 1 次按压改变了 store")
        assert a2["last"] == b["last"], (arm, "账上多了一条命令")
        assert a1["fields"]["focus"] == b["fields"]["focus"], (arm, "焦点被挪走了")
    # 对照臂：焦点不在输入框时，Cmd+Z 确实进了处理器
    b, a1, _ = data["body"]
    assert "object-name" not in b["fields"]["focus"] and \
        "camera-fov" not in b["fields"]["focus"], b["fields"]
    assert a1["last"] is not None and a1["last"]["commandKind"] == "UNDO", \
        ("body 对照臂没进处理器", a1["last"])


# ---------------------------------------------------------------- 判据 5
def criterion_5(browser: Any) -> dict[str, Any]:
    """Cmd+Z 把旧值塞进另一个字段，下一次点击把它提交掉"""
    out: dict[str, Any] = {}
    page = fresh(browser)
    steps = [snap(page, "S0")]
    fill_field(page, "[data-director-object-name]", "改名试试706")
    tab_into_fov(page)
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(350)
    steps.append(snap(page, "S1 焦点进 fov + 1 次方向键"))
    page.keyboard.press("Meta+z")
    page.wait_for_timeout(800)
    steps.append(snap(page, "S2 按 Cmd+Z"))
    page.mouse.click(640, 900)
    page.wait_for_timeout(900)
    steps.append(snap(page, "S3 点画布"))
    page.close()
    out["with-undo"] = steps

    page = fresh(browser)
    ctl = [snap(page, "S0")]
    fill_field(page, "[data-director-object-name]", "改名试试706")
    ctl.append(snap(page, "S1 改名后"))
    page.mouse.click(640, 900)
    page.wait_for_timeout(900)
    ctl.append(snap(page, "S2 只点画布（不发 Cmd+Z）"))
    page.close()
    out["control"] = ctl
    return out


def check_5(data: dict[str, Any]) -> None:
    _, s1, s2, s3 = data["with-undo"]
    # 改名确实提交过
    assert s1["fields"]["nameStore"] == "改名试试706", s1["fields"]
    assert s2["fields"]["nameStore"] == "改名试试706", s2["fields"]
    # 按下 Cmd+Z 的那一刻：DOM 里已经是旧名，store 里还是新名
    assert s2["fields"]["nameDom"] != "改名试试706", s2["fields"]
    assert s2["fields"]["nameStore"] == "改名试试706", s2["fields"]
    # 焦点被挪到那个字段，手势被顺手提交成一条条目
    assert s2["fields"]["focus"] == "data-director-object-name", s2["fields"]
    assert s2["spans"]["active"] is None, s2["spans"]
    assert [e["kind"] for e in s2["spans"]["past"]] == ["UPDATE_OBJECT", "camera-fov"], \
        s2["spans"]
    # 下一次点击：改名被静默回退，而且为这次回退新写了一条条目
    assert s3["fields"]["nameStore"] != "改名试试706", s3["fields"]
    assert s3["spans"]["pastLen"] == 3, s3["spans"]
    assert s3["last"]["commandKind"] == "UPDATE_OBJECT", s3["last"]
    assert s3["last"]["disposition"] == "COMMITTED", s3["last"]
    # 对照臂：同样的画布点击，没有 Cmd+Z 就什么都不会发生
    _, c1, c2 = data["control"]
    assert c1["fields"]["nameStore"] == "改名试试706", c1["fields"]
    assert c2["fields"]["nameStore"] == "改名试试706", c2["fields"]
    assert c2["spans"]["pastLen"] == 1, c2["spans"]


# ---------------------------------------------------------------- 判据 6
def criterion_6(browser: Any) -> dict[str, Any]:
    page = fresh(browser)
    el = page.locator("[data-director-shot-end]").first
    el.click()
    page.wait_for_timeout(250)
    steps = [snap(page, "S0 刚聚焦")]
    el.fill("6")
    page.wait_for_timeout(450)
    steps.append(snap(page, "S1 填完 6（还没提交）"))
    el.press("Tab")
    page.wait_for_timeout(700)
    steps.append(snap(page, "S2 按 Tab"))
    page.close()
    return steps


def check_6(steps: list[dict[str, Any]]) -> None:
    s0, s1, s2 = steps
    # 填完还没提交：账上一条都没有
    assert s1["last"] is None, s1["last"]
    assert s1["spans"]["pastLen"] == 0, s1["spans"]
    assert s1["fields"]["shotEndStore"] == 8, s1["fields"]
    # 提交之后：条目是 shot 自己的 UPDATE_SHOT，但账上最后一条已经变成 fov 的手势
    assert s2["spans"]["pastLen"] == 1, s2["spans"]
    entry = s2["spans"]["past"][0]
    assert entry["kind"] == "UPDATE_SHOT", entry
    assert entry["span"] == [".shots[0].endTime"], entry["span"]
    assert s2["fields"]["shotEndStore"] == 6, s2["fields"]
    assert s2["last"]["commandKind"] == "GESTURE_BEGIN", s2["last"]
    assert s2["last"]["disposition"] == "COMMITTED", s2["last"]


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            a1 = criterion_1(browser)
            results["criterion_1"] = a1
            check_1(a1)
            results["criterion_1_pass"] = True
        except Exception as exc:  # noqa: BLE001 - harness 缺陷也要进审计
            results["criterion_1_pass"] = False
            results["criterion_1_error"] = str(exc)
        for idx, (fn, chk) in enumerate((
                (criterion_2, check_2), (criterion_3, check_3),
                (criterion_4, check_4), (criterion_5, check_5),
                (criterion_6, check_6)), start=2):
            try:
                data = fn(browser)
                results[f"criterion_{idx}"] = data
                chk(data)
                results[f"criterion_{idx}_pass"] = True
            except Exception as exc:  # noqa: BLE001 - harness 缺陷也要进审计
                results[f"criterion_{idx}_pass"] = False
                results[f"criterion_{idx}_error"] = str(exc)
        browser.close()

    results["predictions"] = PREDICTIONS
    results["summary"] = {
        "criterion_1_the_open_gesture_belongs_to_the_next_focusable_slider":
            results.get("criterion_1_pass", False),
        "criterion_2_three_arrow_presses_collapse_into_one_entry_covering_two_fields":
            results.get("criterion_2_pass", False),
        "criterion_3_escape_reverts_the_document_yet_is_ledgered_as_noop":
            results.get("criterion_3_pass", False),
        "criterion_4_cmd_z_inside_a_focused_input_never_reaches_undo":
            results.get("criterion_4_pass", False),
        "criterion_5_cmd_z_stages_a_reverse_edit_that_the_next_click_commits":
            results.get("criterion_5_pass", False),
        "criterion_6_ledger_ownership_flips_with_timing":
            results.get("criterion_6_pass", False),
    }
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1, default=str))

    failed = [k for k, v in results["summary"].items() if not v]
    for k, v in results["summary"].items():
        print(("PASS " if v else "FAIL ") + k)
    for i in range(1, 7):
        err = results.get(f"criterion_{i}_error")
        if err:
            print(f"  判据 {i} 详情: {err[:500]}")
    print(f"\n{len(results['summary']) - len(failed)}/{len(results['summary'])} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
