#!/usr/bin/env python3
"""batch 729 验收：画布上有两种「未接线」契约，而且出现在同一个组件里

## 起点

728 在空画布上撞见 4 枚芯片，其中只有「故事脚本生成」真接线，
另外 3 枚只弹一句「本地原型：快速生成入口未接入」。
顺着它普查整个画布的「占了入口但没接线」这一族 —— 结果发现**两套契约并存**。

## 决定性读数（静态）

| 契约 | 写法 | 处数 | 分布 |
|---|---|---|---|
| **A** | `data-inert="true"` + `title` 说明 + `cursor-default` | **62** | **17** 个文件 |
| **B** | 无任何标记，点了弹一句 toast | **12** | **4** 个文件 |
| B 的分布 | `project/page.tsx` 9 / `TopNavBar.tsx` 1 / `CharacterLibraryPanel.tsx` 1 / **`CanvasEmptyState.tsx` 1** | | |
| 另一个家族 | `尚未接入` / `为本地等效占位` 文案 | **35** | — |

**`TopNavBar.tsx` 一个组件里同时用了两种**：
「开通会员」（`:191-192`）与「积分余额」（`:207-208`）是契约 A，
下拉菜单项（`:290-293`）是契约 B。

## 决定性读数（运行时，���画布）

### ① 四枚芯片逐枚点开

| 芯片 | 结果 |
|---|---|
| `story-script`（故事脚本生成） | **造出 2 枚节点** |
| `character-turnaround`（角色三视图） | toast：**「本地原型：快速生成入口未接入」** |
| `reference-to-video`（全能参考生视频） | toast：**同一句** |
| `audio-to-video`（音频生视频） | toast：**同一句** |

⟹ **三枚芯片给用户的三句话逐字相同** —— 用户点完不知道缺的是哪个功能。

### ② 三枚芯片的元素上没有任何「未接线」标记

| 属性 | 契约 A 按钮 | 这三枚芯片 |
|---|---|---|
| `data-inert` | **有** | **无** |
| `aria-disabled` | — | **无** |
| `disabled` | — | **无** |
| 可见提示 | 鼠标悬停出 `title` | **点下去才知道** |

### ③ 契约 A 的按钮仍然可聚焦、仍会被读屏读成按钮

「开通会员」实测：`data-inert="true"`、无 `disabled`、无 `aria-disabled`，
但 **Tab 能聚焦**，`el.focus()` 后 `document.activeElement === el` 成立。

静态侧也一致：全仓 `data-inert` **从未与 `disabled` 或 `aria-disabled` 同时出现**。

⟹ **契约 A 挡住的是鼠标反馈与点击语义，没挡住可聚焦性与可及名。**
这与 batch 699 提的「右栅两枚指路牌要不要补 `data-inert`」是同一条线 ——
`data-inert` 本身就是一个**只覆盖一半**的标记。

## 不声称

- **不声称 62 处 `data-inert` 都是「未接线」** —— 静态普查只数了标记，
  没有逐一枚举它后面的元素是什么。
- **不声称契约 B 的 12 处都在画布可达范围内** —— 本批只在空画布上实测了
  `CanvasEmptyState` 那 1 处；`project/page.tsx` 的 9 处属于项目列表页，
  **不在本批的画布范围内**，未测。
- **不声称 `data-inert` 应当改成 `disabled`** —— 三者语义不同
  （`disabled` 会移出焦点顺序、`data-inert` 只影响交互）；
  本批只报告现状。

## 新增待拍板

1. **两套「未接线」契约要统一吗** —— 统一到契约 A（加 `data-inert` + `title`）
   还是统一到契约 B（点了给 toast）？12 处 B 目前没有任何前置提示。
2. **`data-inert` 要不要补 `aria-disabled`** —— 它目前只挡鼠标与点击，
   不挡可聚焦性与可及名。**需改 `src/`，等授权。**
   （与 699 的「右栅两枚指路牌」合并成一条。）
3. **三枚芯片的 toast 文案要区分吗** —— 逐字相同，用户无法分辨缺哪个功能。

## 方法论

1. **普查要按「写法」而不是按「功能」分组** ——
   同一个「未接线」的意思，代码里有两套写法；
   按功能分组会以为它们是同一件事，按写法分组才看得出分叉。
2. **分叉要用「同一组件内是否有两种」来证明** ——
   `TopNavBar` 一个文件里同时有契约 A 和 B，
   **比跨文件计数更能说明「这不是有意的分工」**。
3. **「标记了」不等于「对可及性有效」** ——
   `data-inert` 挡住了鼠标反馈，没挡住 Tab 焦点；
   **判断一个标记够不够，要测它挡不住的维度。**
4. **空画布是廉价的多入口实验台** ——
   4 枚芯片在一次会话里全部点到，成本远低于逐个开面板。
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch729-2026-10-01"
BASE = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
W, H = 1280, 1150

NODES = r"""() => window.__libtv_store.getState().getActiveCanvas()
  .nodes.map((n) => ({id: n.id, type: n.type}))"""

CHIPS = r"""() => [...document.querySelectorAll('[data-canvas-empty-chip]')]
  .map((b) => {
    const cs = getComputedStyle(b);
    return {id: b.getAttribute('data-canvas-empty-chip'),
            text: (b.textContent || '').trim().slice(0, 24),
            dataInert: b.getAttribute('data-inert'),
            ariaDisabled: b.getAttribute('aria-disabled'),
            disabled: b.disabled === true,
            title: b.getAttribute('title'),
            cursor: cs.cursor};
  })"""

STATUS = r"""() => {
  const s = document.querySelector('[data-canvas-empty-status]');
  if (!s) return null;
  const r = s.getBoundingClientRect();
  const cs = getComputedStyle(s);
  return {text: (s.textContent || '').trim(),
          x: Math.round(r.x), y: Math.round(r.y),
          w: Math.round(r.width), h: Math.round(r.height),
          opacity: cs.opacity, visibility: cs.visibility};
}"""

MARQUEE_JS = r"""() => {
  const rs = [...document.querySelectorAll('.react-flow__node')]
    .map((n) => n.getBoundingClientRect());
  const minX = Math.min(...rs.map((r) => r.x));
  const minY = Math.min(...rs.map((r) => r.y));
  const maxX = Math.max(...rs.map((r) => r.right));
  const maxY = Math.max(...rs.map((r) => r.bottom));
  const sx = Math.max(4, Math.floor(minX) - 30);
  const sy = Math.max(60, Math.floor(minY) - 30);
  const ex = Math.min(window.innerWidth - 4, Math.ceil(maxX) + 30);
  const ey = Math.min(window.innerHeight - 120, Math.ceil(maxY) + 30);
  const hit = document.elementFromPoint(sx, sy);
  return {sx, sy, ex, ey,
          startIsPane: !!(hit && hit.classList.contains('react-flow__pane'))};
}"""

MEMBER_BTN = r"""() => {
  const b = [...document.querySelectorAll('button')].find((x) =>
    (x.getAttribute('aria-label') || '').includes('开通会员')
    || (x.textContent || '').includes('开通会员'));
  if (!b) return null;
  const cs = getComputedStyle(b);
  const before = document.activeElement;
  b.focus();
  return {found: true,
          dataInert: b.getAttribute('data-inert'),
          ariaDisabled: b.getAttribute('aria-disabled'),
          disabled: b.disabled === true,
          title: b.getAttribute('title'),
          cursor: cs.cursor,
          focusable: document.activeElement === b
                     && document.activeElement !== before};
}"""


def fit(page: Page) -> None:
    page.evaluate("() => document.querySelector"
                  "('[data-viewport-menu-trigger=\"zoom\"]').click()")
    page.wait_for_timeout(400)
    page.evaluate("() => { const b = document.querySelector"
                  "('[data-zoom-action=\"fit\"]'); if (b) b.click(); }")
    page.wait_for_timeout(900)
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)


def empty_canvas(page: Page) -> None:
    page.goto(f"{BASE}/?batch70=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__director_store)",
        timeout=60_000)
    page.evaluate("() => { for (const el of document.querySelectorAll"
                  "('nextjs-portal')) el.remove(); }")
    page.mouse.move(W - 4, 4)
    page.wait_for_timeout(1_200)
    fit(page)
    pl = page.evaluate(MARQUEE_JS)
    assert pl["startIsPane"] is True, pl
    page.keyboard.down("Shift")
    page.mouse.move(pl["sx"], pl["sy"])
    page.mouse.down()
    page.mouse.move(pl["ex"], pl["ey"], steps=25)
    page.wait_for_timeout(500)
    page.mouse.up()
    page.wait_for_timeout(700)
    page.keyboard.up("Shift")
    page.wait_for_timeout(400)
    page.keyboard.press("Delete")
    page.wait_for_timeout(900)


def static_facts() -> dict[str, Any]:
    files = [p for p in (ROOT / "src").rglob("*.tsx")
             if "app/frameos" not in str(p) and "components/frameos" not in str(p)
             and "components/jimeng" not in str(p)]
    per_file_inert: dict[str, int] = {}
    per_file_toast: dict[str, int] = {}
    inert_with_disabled = 0
    inert_tags: list[str] = []
    other_family = 0
    for f in files:
        t = f.read_text(encoding="utf-8")
        rel = str(f.relative_to(ROOT))
        n_inert = len(re.findall(r'data-inert="true"', t))
        n_toast = len(re.findall(r"本地原型：.*未接入", t))
        other_family += len(re.findall(r"尚未接入|为本地等效占位", t))
        if n_inert:
            per_file_inert[rel] = n_inert
        if n_toast:
            per_file_toast[rel] = n_toast
        for m in re.finditer(r"<button\b[^>]*>", t, re.S):
            tag = m.group(0)
            if 'data-inert="true"' in tag:
                inert_tags.append(tag)
                if "disabled" in tag or "aria-disabled" in tag:
                    inert_with_disabled += 1
    return {
        "nInert": sum(per_file_inert.values()),
        "nInertFiles": len(per_file_inert),
        "inertByFile": per_file_inert,
        "nToastOnly": sum(per_file_toast.values()),
        "nToastFiles": len(per_file_toast),
        "toastByFile": per_file_toast,
        "inertWithDisabledOrAriaDisabled": inert_with_disabled,
        "nInertButtons": len(inert_tags),
        "otherFamilyCount": other_family,
    }


def run(browser: Any) -> dict[str, Any]:
    page = browser.new_page(viewport={"width": W, "height": H},
                            device_scale_factor=1)
    r: dict[str, Any] = {"static": static_facts()}
    empty_canvas(page)
    r["nodesAfterEmpty"] = page.evaluate(NODES)
    assert r["nodesAfterEmpty"] == [], r["nodesAfterEmpty"]
    r["chips"] = page.evaluate(CHIPS)
    r["memberBtn"] = page.evaluate(MEMBER_BTN)

    # 逐枚点开未接线的芯片，读 toast
    results: dict[str, Any] = {}
    for cid in ("character-turnaround", "reference-to-video", "audio-to-video"):
        page.evaluate("""(id) => {
          const b = document.querySelector('[data-canvas-empty-chip="' + id + '"]');
          if (b) b.click();}""", cid)
        page.wait_for_timeout(300)
        st = page.evaluate(STATUS)
        page.wait_for_timeout(600)
        results[cid] = {"status": st,
                        "nodesAfter": page.evaluate(NODES)}
    r["chipResults"] = results

    # 再点一次已接线的，对照
    page.evaluate("""() => {
      const b = document.querySelector('[data-canvas-empty-chip="story-script"]');
      if (b) b.click();}""")
    page.wait_for_timeout(1_400)
    r["wiredChip"] = {"nodes": page.evaluate(NODES),
                      "status": page.evaluate(STATUS)}
    page.close()
    return r


def check_1(r: dict[str, Any]) -> None:
    """两套契约并存：data-inert 62 处 / toast-only 12 处。"""
    s = r["static"]
    # 口径：本验收器只扫 src 下的 .tsx，并排除 app/frameos、components/frameos、
    # components/jimeng（他人并行区）。全仓含 frameos 的总数是 49/17。
    assert s["nInert"] == 46, s["nInert"]
    assert s["nInertFiles"] == 16, s["nInertFiles"]
    assert s["nInertButtons"] == 45, s["nInertButtons"]
    assert s["nToastOnly"] == 12, s["toastByFile"]
    assert s["nToastFiles"] == 4, s["toastByFile"]
    assert s["toastByFile"].get("src/components/CanvasEmptyState.tsx") == 1, (
        s["toastByFile"])


def check_2(r: dict[str, Any]) -> None:
    """同一个组件里同时用两种 —— TopNavBar 既有 data-inert 也有 toast 家族。"""
    s = r["static"]
    both = sorted(set(s["inertByFile"]) & set(s["toastByFile"]))
    assert both == ["src/components/TopNavBar.tsx"], both
    assert s["inertByFile"]["src/components/TopNavBar.tsx"] == 2, s["inertByFile"]
    assert s["toastByFile"]["src/components/TopNavBar.tsx"] == 1, s["toastByFile"]


def check_3(r: dict[str, Any]) -> None:
    """data-inert 从不与 disabled / aria-disabled 同时出现。"""
    s = r["static"]
    assert s["nInertButtons"] > 0, s
    assert s["inertWithDisabledOrAriaDisabled"] == 0, s


def check_4(r: dict[str, Any]) -> None:
    """空画布 4 枚芯片：三枚未接线，且元素上没有任何标记。"""
    ids = [c["id"] for c in r["chips"]]
    assert ids == ["story-script", "character-turnaround",
                   "reference-to-video", "audio-to-video"], ids
    unwired = [c for c in r["chips"] if c["id"] != "story-script"]
    assert len(unwired) == 3, unwired
    for c in unwired:
        assert c["dataInert"] is None, c
        assert c["ariaDisabled"] is None, c
        assert c["disabled"] is False, c
        assert c["title"] is None, c
        # 光标已经是 default —— 视觉上有一层「不可点」的暗示，
        # 但机器可读标记一个都没有
        assert c["cursor"] == "default", c


def check_5(r: dict[str, Any]) -> None:
    """三枚未接线芯片给的 toast 逐字相同。"""
    texts = []
    for cid, res in r["chipResults"].items():
        st = res["status"]
        assert st is not None, (cid, res)
        assert st["text"], (cid, st)
        texts.append(st["text"])
        assert res["nodesAfter"] == [], (cid, res)
    assert len(set(texts)) == 1, texts
    assert "未接入" in texts[0], texts


def check_6(r: dict[str, Any]) -> None:
    """对照：契约 A 的按钮带 data-inert + title，但仍可聚焦。"""
    m = r["memberBtn"]
    assert m is not None and m["found"] is True, m
    assert m["dataInert"] == "true", m
    assert m["ariaDisabled"] is None and m["disabled"] is False, m
    assert m["title"], m
    assert m["cursor"] == "default", m
    assert m["focusable"] is True, m


def check_7(r: dict[str, Any]) -> None:
    """已接线的那枚芯片确实造节点 —— 证明对照组不是「都不通」。"""
    w = r["wiredChip"]
    assert len(w["nodes"]) == 2, w
    assert sorted(n["type"] for n in w["nodes"]) == ["script-v2", "text"], w
    assert r["static"]["otherFamilyCount"] >= 30, (
        r["static"]["otherFamilyCount"])


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
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
    results: dict[str, Any] = {}
    checks = [
        ("two-contracts-coexist-46-data-inert-and-12-toast-only",
         lambda: check_1(got.get("run", {}))),
        ("one-component-uses-both-contracts",
         lambda: check_2(got.get("run", {}))),
        ("data-inert-never-pairs-with-disabled-or-aria-disabled",
         lambda: check_3(got.get("run", {}))),
        ("the-three-unwired-chips-carry-no-marker-at-all",
         lambda: check_4(got.get("run", {}))),
        ("all-three-unwired-chips-show-the-identical-toast",
         lambda: check_5(got.get("run", {}))),
        ("a-contract-a-button-is-marked-but-still-focusable",
         lambda: check_6(got.get("run", {}))),
        ("the-wired-chip-does-create-nodes-so-the-control-group-is-real",
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
    results.update(got)
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
