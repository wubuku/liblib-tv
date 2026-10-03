#!/usr/bin/env python3
"""batch 723 验收：画布普查 —— 10 张卡只有 1 枚按钮，而那枚被默认视口切出屏

## 起点

画布是复刻的另一半，却一直只被「当作导演台的舞台」顺带看过：
导演台一开就把画布盖住，所有读数都发生在台里。
本批不开台，第一次把画布本身列全。

## 决定性读数（`/?batch70=1`，1280×1150，不开导演台）

### 种子节点：10 枚、5 种类型、11 条连线

| 类型 | 枚数 | 标题 |
|---|---|---|
| `storyboard-group` | 2 | 分镜图 · 第一集：咖啡馆对峙-图片组 / 视频组 · …-视频组 |
| `image` | 5 | —（无 `title`） |
| `script` | 1 | 剧本 |
| `script-execution` | 1 | 第一集：咖啡馆对峙 |
| `video` | 1 | —（无 `title`） |

`src/app/page.tsx:143-157` 注册了 **13** 种节点类型 ⟹ **8 种已注册但 fixture 里一枚都没有**。

### 10 张卡里只有 1 枚按钮

| 卡 | 尺寸 @ | 按钮数 |
|---|---|---|
| `g-245IDFh8sB` 分镜图片组 | 226×238 @(527,606) | **0** |
| `g-EFbbHpwq5w` 分镜视频组 | 380×242 @(665,254) | **0** |
| `t-9j2MoccxBj` 剧本 | 184×105 @(**−527**,195) | **0** |
| `i-1FQ9tErTcC` 图片 | 325×184 @(**−514**,404) | **0** |
| `i-lBzmo67AHv` 图片 | 325×184 @(**−368**,751) | **0** |
| `i-dnwoZQ7jsG` 图片 | 368×184 @(**−368**,961) | **0** |
| `i-vxeeCnxySa` 图片 | 368×184 @(**−368**,1172) | **0** |
| **`b-bTLLuU4w5q` 导演台** | 184×184 @(**−22**,162) | **1**（`打开导演台 →` 166×19 @**−13**,162） |
| `i-YDfWhFlthe` 图片 | 327×184 @(247,103) | **0** |
| `v-UGQZzZOpbv` 视频 | 327×184 @(698,287) | **0** |

⟹ **九张卡零控件**：图片、分镜组、剧本、视频都不能在卡上打开、编辑或删除。

### 顺带闭合一条反复出现的读数

前面几十批记的 `[data-open-director]` 几何恒为 **`x = −13, y = 319, w = 166, h = 19`** ——
那不是「按钮被放在负坐标」，而是**它所在的卡 `x = −22`、卡宽 184**，
默认视口把这张卡切掉了 22px，按钮左缘随之出屏 13px。
**每一次「点那枚按钮」其实都点在半出屏的元素上**，只是 Playwright 允许点。

### 画布外壳：34 枚按钮分五簇

| 簇 | 位置 | 枚数 | 清单 |
|---|---|---|---|
| 顶栏 | y≈16 | **8** | 项目菜单 / 画布 2 / 工作流 / 故事板 / 发布与分享 / 开通会员 限时 45 折 / 积分余额 / Agent |
| 底部坞 | y≈1098 | **8** | 添加节点 / 移动 / 打开工具箱 / 素材库 / 角色库 / 生成历史 / 快捷键 / 教程 |
| 左下控制 | y≈1104 | **6** | 资产管理 / 整理画布，Option+Shift+F / 切换小地图 / 隐藏节点连线 / 网格吸附 / 缩放选项 |
| **连线删除手柄** | 散布 | **11** | 全部 `aria-label="删除连线"`，**各 8×8** |
| 杂项 | @(645,9) | 1 | `取消 ESC` 55×16（中心命中 `div`，不是自己） |

### 11 枚连线删除手柄：中心点命中自己 **0 枚**

| 结果 | 枚数 | 说明 |
|---|---|---|
| 中心命中自己 | **0** | — |
| 命中别的元素 | **7** | 6 枚被 `path`（连线本体）盖住、1 枚被 `div` 盖住 |
| 出屏（`elementFromPoint` 返回 null） | **4** | x 全为负（−110 / −15 / −15 / −37） |

11 条连线 ↔ 11 枚手柄，**一一对应**。

## 不声称

- **不声称 8×8 的手柄是缺陷** —— 源站画布未测，且「中心点被连线本体盖住」
  可能是有意的视觉取舍。**需要一次源站 A/B 才能定性。**
- **不声称九张卡「应该有」按钮** —— 源站的图片/分���组卡上有什么控件未测。
- **不声称默认视口是错的** —— 只测出「它把唯一有控件的那张卡切掉 22px」。

## 方法论

1. **一半的产物不能只在被另一半盖住的时候测** —— 导演台一开画布就没了，
   于是「画布上有什么」这个问题一直被回避。**先关掉上层再普查下层。**
2. **反复出现的怪读数要去追根** —— `openBtn x = −13` 出现过几十批，
   一直记成「坐标为负」；追到卡片层才发现是**视口把卡切了**，
   **同一个数字的含义在上一层和下一层完全不同**。
3. **命中测试要按「中心点命中谁」读，不要只读「在不在屏内」** ——
   11 枚手柄有 7 枚在屏内，中心点却全部被别的元素占住。
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
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch723-2026-10-01"
BASE = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
W, H = 1280, 1150

STORE_JS = r"""() => {
  const s = window.__libtv_store.getState();
  const c = s.getActiveCanvas();
  const types = {};
  for (const n of c.nodes) types[n.type] = (types[n.type] || 0) + 1;
  return {
    canvasId: s.activeCanvasId, canvasName: c.name,
    zoomTopLevel: s.zoom === undefined ? 'ABSENT' : s.zoom,
    n: c.nodes.length, types,
    nodes: c.nodes.map((n) => ({
      id: n.id, type: n.type,
      x: n.position ? n.position.x : null, y: n.position ? n.position.y : null,
      hasTitle: !!(n.data && (n.data.title || n.data.name))})),
    nEdges: c.edges ? c.edges.length : 0,
  };
}"""

CARDS_JS = r"""() => {
  const out = [];
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const r = n.getBoundingClientRect();
    const id = n.getAttribute('data-id');
    const btns = [...n.querySelectorAll('button, [role="button"]')].map((b) => {
      const br = b.getBoundingClientRect();
      const cx = br.x + br.width / 2, cy = br.y + br.height / 2;
      const hit = document.elementFromPoint(cx, cy);
      return {
        label: b.getAttribute('aria-label') || b.getAttribute('title')
          || (b.textContent || '').trim().slice(0, 20),
        w: Math.round(br.width), h: Math.round(br.height),
        x: Math.round(br.x), y: Math.round(br.y),
        onScreen: cx >= 0 && cx <= window.innerWidth
          && cy >= 0 && cy <= window.innerHeight,
        hitSelf: hit === b || (hit && b.contains(hit)),
        hitTag: hit ? hit.tagName.toLowerCase() : null,
      };
    });
    out.push({
      id, w: Math.round(r.width), h: Math.round(r.height),
      x: Math.round(r.x), y: Math.round(r.y),
      text: (n.textContent || '').trim().slice(0, 24),
      nBtns: btns.length, btns,
    });
  }
  return out;
}"""

CHROME_JS = r"""() => {
  const out = [];
  for (const b of document.querySelectorAll('button')) {
    if (b.closest('.react-flow__node')) continue;
    const r = b.getBoundingClientRect();
    if (r.width === 0) continue;
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    const hit = document.elementFromPoint(cx, cy);
    out.push({
      label: b.getAttribute('aria-label') || b.getAttribute('title')
        || (b.textContent || '').trim().slice(0, 22),
      w: Math.round(r.width), h: Math.round(r.height),
      x: Math.round(r.x), y: Math.round(r.y),
      onScreen: cx >= 0 && cx <= window.innerWidth
        && cy >= 0 && cy <= window.innerHeight,
      hitSelf: hit === b || (hit && b.contains(hit)),
      hitTag: hit ? hit.tagName.toLowerCase() : null,
    });
  }
  return out;
}"""


def static_facts() -> dict[str, Any]:
    page_tsx = (ROOT / "src/app/page.tsx").read_text(encoding="utf-8")
    block = re.search(r"const nodeTypes = \{(.*?)\};", page_tsx, re.S)
    assert block, "在 src/app/page.tsx 里找不到 nodeTypes 注册表"
    registered = re.findall(r"^\s*[\"']?([A-Za-z0-9_-]+)[\"']?\s*:", block.group(1),
                            re.M)
    return {"registeredNodeTypes": registered, "nRegistered": len(registered)}


def run(browser: Any) -> dict[str, Any]:
    page = browser.new_page(viewport={"width": W, "height": H},
                            device_scale_factor=1)
    r: dict[str, Any] = {"static": static_facts()}
    page.goto(f"{BASE}/?batch70=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__director_store)",
        timeout=60_000)
    page.evaluate("() => { for (const el of document.querySelectorAll"
                  "('nextjs-portal')) el.remove(); }")
    page.mouse.move(W - 4, 4)
    page.wait_for_timeout(1_500)
    r["store"] = page.evaluate(STORE_JS)
    r["cards"] = page.evaluate(CARDS_JS)
    r["chrome"] = page.evaluate(CHROME_JS)
    page.close()
    return r


def check_1(r: dict[str, Any]) -> None:
    """种子节点 10 枚、5 种类型、11 条连线。"""
    s = r["store"]
    assert s["n"] == 10, s["n"]
    assert s["types"] == {"storyboard-group": 2, "image": 5, "script": 1,
                          "script-execution": 1, "video": 1}, s["types"]
    assert s["nEdges"] == 11, s["nEdges"]
    assert s["zoomTopLevel"] == "ABSENT", s["zoomTopLevel"]
    titles = {n["id"]: n["hasTitle"] for n in s["nodes"]}
    assert titles["t-9j2MoccxBj"] is True, titles
    assert titles["b-bTLLuU4w5q"] is True, titles
    assert sum(1 for v in titles.values() if v is False) == 6, titles


def check_2(r: dict[str, Any]) -> None:
    """10 张卡逐一枚举，id 与 store 一一对应，零多零少。"""
    s = {n["id"] for n in r["store"]["nodes"]}
    c = [x["id"] for x in r["cards"]]
    assert len(c) == 10, c
    assert set(c) == s, (sorted(set(c) ^ s))
    assert len(set(c)) == len(c), c


def check_3(r: dict[str, Any]) -> None:
    """十张卡里只有一枚按钮，长在导演台卡上；其余九张零控件。"""
    cards = r["cards"]
    with_btn = [x for x in cards if x["nBtns"] > 0]
    assert len(with_btn) == 1, [x["id"] for x in with_btn]
    only = with_btn[0]
    assert only["id"] == "b-bTLLuU4w5q", only["id"]
    assert only["nBtns"] == 1, only
    assert only["btns"][0]["label"] == "打开导演台 →", only["btns"][0]
    assert (only["btns"][0]["w"], only["btns"][0]["h"]) == (166, 19), only["btns"][0]
    assert sum(x["nBtns"] for x in cards) == 1, sum(x["nBtns"] for x in cards)


def check_4(r: dict[str, Any]) -> None:
    """默认视口把那张卡切掉 22px，按钮左缘随之出屏 13px —— 闭合前面几十批的 x=−13。"""
    card = [x for x in r["cards"] if x["id"] == "b-bTLLuU4w5q"][0]
    assert (card["w"], card["x"]) == (184, -22), card
    b = card["btns"][0]
    assert b["x"] == -13, b
    assert b["x"] < 0, b
    # 卡片左缘在屏外，按钮左缘也在屏外，且两者相距 9px（按钮内缩）
    assert card["x"] - b["x"] == -9, (card["x"], b["x"])
    assert card["x"] + card["w"] > 0, card  # 但卡片右半仍在屏内


def check_5(r: dict[str, Any]) -> None:
    """画布外壳 34 枚按钮分五簇：顶栏 8 / 底部坞 8 / 左下 6 / 连线手柄 11 / 杂项 1。"""
    ch = r["chrome"]
    assert len(ch) == 34, len(ch)
    handles = [b for b in ch if b["label"] == "删除连线"]
    assert len(handles) == 11, len(handles)
    top = [b for b in ch if 16 <= b["y"] <= 18]
    dock = [b for b in ch if b["y"] == 1098]
    left = [b for b in ch if b["y"] == 1104]
    other = [b for b in ch
             if b not in handles and b not in top
             and b not in dock and b not in left]
    assert (len(top), len(dock), len(left)) == (8, 8, 6), (
        len(top), len(dock), len(left))
    assert len(other) == 1, other
    assert other[0]["label"] == "取消 ESC", other
    assert (other[0]["w"], other[0]["h"]) == (55, 16), other
    assert r["store"]["nEdges"] == len(handles)


def check_6(r: dict[str, Any]) -> None:
    """11 枚连线删除手柄各 8×8，中心点命中自己 0 枚：7 枚被盖、4 枚出屏。"""
    handles = [b for b in r["chrome"] if b["label"] == "删除连线"]
    assert {b["w"] for b in handles} == {8}, {b["w"] for b in handles}
    assert {b["h"] for b in handles} == {8}, {b["h"] for b in handles}
    assert sum(1 for b in handles if b["hitSelf"]) == 0, [
        b for b in handles if b["hitSelf"]]
    offscreen = [b for b in handles if not b["onScreen"]]
    covered = [b for b in handles if b["onScreen"] and not b["hitSelf"]]
    assert len(offscreen) == 4, offscreen
    assert len(covered) == 7, covered
    assert all(b["x"] < 0 for b in offscreen), offscreen
    assert all(b["hitTag"] is not None for b in covered), covered


def check_7(r: dict[str, Any]) -> None:
    """注册 13 种节点类型，fixture 只用到 5 种 ⟹ 8 种零出现。"""
    st = r["static"]
    reg = st["registeredNodeTypes"]
    assert st["nRegistered"] == 13, reg
    used = set(r["store"]["types"])
    assert used <= set(reg), sorted(used - set(reg))
    unused = sorted(set(reg) - used)
    assert len(unused) == 8, unused
    r["static"]["unusedRegisteredTypes"] = unused


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
        ("ten-seed-nodes-of-five-types-and-eleven-edges",
         lambda: check_1(got.get("run", {}))),
        ("every-store-node-renders-exactly-one-card",
         lambda: check_2(got.get("run", {}))),
        ("nine-of-ten-cards-carry-no-control-at-all",
         lambda: check_3(got.get("run", {}))),
        ("the-default-viewport-clips-the-only-card-that-has-a-control",
         lambda: check_4(got.get("run", {}))),
        ("thirty-four-shell-buttons-in-five-clusters",
         lambda: check_5(got.get("run", {}))),
        ("all-eleven-edge-delete-handles-are-8x8-and-none-hit-itself",
         lambda: check_6(got.get("run", {}))),
        ("thirteen-node-types-are-registered-but-eight-never-appear",
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
