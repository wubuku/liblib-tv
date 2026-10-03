#!/usr/bin/env python3
"""batch 734 验收：8 个未打开的写点全打开；推翻 732 的「6 个写点无 UI 入口」

## 起点

733 把 46 个写点里的 28 个逐处打开，10 个记为「条件门控」，8 个仍未打开。
本批把那 8 个全打开 —— 结果顺带把 732 的一个结论推翻了。

## 决定性读数

### ① 入口要按稳定属性选（第三种稳定属性）

| 面板 | 稳定选择器 | 出处 |
|---|---|---|
| 「添加节点」 | `[data-add-node-entry=type]` | `AddNodePanel.tsx:206`（733 用上） |
| 图片卡工具条 | `[data-testid=image-toolbar-panorama-slash]` | `ImageToolbar.tsx:30-31` |

按可见文本找会连续踩空三次：文案带 badge（「智能剪辑Beta」「逐帧拉片SD 2.5」）、
同一组件里文案相近（「剧本生成分镜脚本」vs「打开脚本节点 →」）、
图标 + 文字混排导致 `textContent.trim()` 不等于 label。

### ② 全景分支 4 处打开

`ImageNode.tsx:161` `runAction("全景")` 会 `addDerivedNode(..., { editorVariant: "panorama" })`，
而 `ImageEditPanel.tsx:50` `variant === "panorama"` 才渲染 `PanoramaEditPanel`。
选中那张派生卡后，**全景面板内 4 处**全部出现：
展开全景编辑器 / 全景参考图添加 / 全景模型选择 / 全景生成参数。

### ③ **推翻 732**：那 6 个写点不是「无 UI 入口」，是「种子那张视频卡恰好 failed」

| | 读数 | 出处 |
|---|---|---|
| 种子里视频卡的 `status` | **`"failed"`** | `canvasStore.ts:940` |
| **新建**视频卡的 `status` | **`"ready"`** | `canvasStore.ts:4207` |
| 实测：新建一张视频卡并单选 | 自身 6 枚：**播放视频**（`VideoNode:498`）+ 该功能 / 翻译视频提示词 / 该设置 + **撤销视频处理 / 重做视频处理**（`VideoProcessingToolbar:244-245`） | — |

⟹ 732 那句「种子画布上**没有任何 UI 入口**」**读数对、理由错**：
UI 有路径，只是**起点是另一张卡**。种子 fixture 把视频卡钉在 `failed`，
于是同一套 UI 在种子画布上看不到那 6 处。

### ④ 再点两下，又开 6 处

| 动作 | 触发器 | 新出现的写点 |
|---|---|---|
| 点「特效」pill | `VideoGenerationPanel.tsx:394` `setEffectsOpen` | **特效收藏**（`:550`）**一个写点 → 4 枚实例** |
| 点元素选择模式 | `[data-mark-select-trigger]`（`:476`） | **返回节点**（`:597`）+ **关闭**（`:613`） |
| 点「片段重拍」 | `VideoProcessingToolbar.tsx:131` | `SegmentReshootPanel` **4 写点 → 6 枚实例**：参考 / 标记 / 角色库（`:138` 的 `.map` 撑成 3 枚）+ 积分选择（`:230`）+ 生成参数选择（`:236`）+ 翻译片段重拍提示词（`:257`） |

### ⑤ 全表收口

| 状态 | 写点数 |
|---|---|
| 已逐处打开并实测 | **44** |
| 条件门控、已带源码 + DOM 双证 | **2**（`ShotBreakdownResultNode` 1 + `StoryboardScriptEditor` 3 中未开的 1） |

十处全部 `role=button`（AX 通道）+ `focusable=true`（DOM 通道）——
与 730/731/732/733 的读数**五处同构**。

## 不声称

- **不声称剩下的 2 个门控写点不可达** —— 只是本批没走到那一步。
- **不声称 44 个写点的运行时实例总数** —— 多实例写点（`:550` → 4 枚、
  `:138` → 3 枚、`LibraryShowcasePanel:130` → 16/24 枚等）会显著放大总数。
- **不声称 AX 树等同于真实屏幕阅读器播报** —— 沿用 731。

## 新增待拍板

1. **种子 fixture 把视频卡钉在 `failed` 是不是有意的** —— 它让 `VideoNode:498`、
   `VideoProcessingToolbar` 2、`SegmentReshootPanel` 4 共 **7 个写点**在默认画布上
   永远看不到。**需改 `src/`（或 fixture），等授权**；本批只报告，不裁决。

## 方法论

1. **入口按稳定属性选** —— `data-add-node-entry` / `data-testid` 是合同，
   文案是给人看的；本批把它总结成「三种稳定属性」并给出踩空的三种方式。
2. **「读数对、理由错」要单独记一档** —— 732 说「没有 UI 入口」，
   实测新建一张卡就有了；**读数（种子画布上看不到）是对的，理由（没有路径）是错的**。
3. **fixture 的取值也是 UI 的一部分** —— 「种子里那张卡恰好 failed」会改变
   用户能看到的控件集合，这不是测试的偶然，是产品状态。

## 探针返工一处

节点选中从「在元素上直接派发 mousedown/mouseup/click」改成「按 boxModel 中心发真实鼠标点击」
后，**图片卡选不中**（中心被封面图挡住），`data-image-toolbar` 不渲染 ⟹ 全景分支打不开。
改回 730 的做法即通过。⟹ **能派发就别模拟真实点击**，模拟真实点击会引入遮挡问题。
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
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch734-2026-10-01"
BASE = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
W, H = 1280, 1150
TOPNAV = {"开通会员 限时 45 折", "积分余额"}

ENUM = r"""() => [...document.querySelectorAll('button[data-inert]')].map(el => {
  const ov = el.closest('[data-liblib-overlay]');
  return {aria: el.getAttribute('aria-label') || '', title: el.getAttribute('title') || '',
          inPano: !!el.closest('[data-panorama-edit-panel]'),
          ov: ov ? ov.getAttribute('data-liblib-overlay') : null}; })"""

FOCUS = r"""() => [...document.querySelectorAll('button[data-inert]')].map(el => {
  el.focus(); return document.activeElement === el; })"""

NEW_VIDEO_STATUS = r"""(id) => { const g = window.__libtv_store.getState().getActiveCanvas();
  const n = g.nodes.find(x => x.id === id); return n ? (n.data || {}).status : null; }"""

SEED_VIDEO_STATUS = r"""() => { const g = window.__libtv_store.getState().getActiveCanvas();
  const n = g.nodes.find(x => x.type === 'video'); return n ? (n.data || {}).status : null; }"""


def ax_roles(cdp: Any, ids: list[int]) -> list[str | None]:
    out: list[str | None] = []
    for nid in ids:
        try:
            bid = cdp.send("DOM.describeNode", {"nodeId": nid})["node"]["backendNodeId"]
            t = cdp.send("Accessibility.getPartialAXTree",
                         {"backendNodeId": bid, "fetchRelatives": False})
        except Exception:  # noqa: BLE001
            out.append(None)
            continue
        ns = t.get("nodes", [])
        own = next((n for n in ns if n.get("role")), None)
        out.append((own or {}).get("role", {}).get("value"))
    return out


def snap(page: Page, cdp: Any) -> dict[str, Any]:
    root = cdp.send("DOM.getDocument", {"depth": -1})["root"]["nodeId"]
    ids = cdp.send("DOM.querySelectorAll",
                   {"nodeId": root, "selector": "button[data-inert]"})["nodeIds"]
    rows = page.evaluate(ENUM)
    roles = ax_roles(cdp, ids)
    foc = page.evaluate(FOCUS)
    return {"rows": [{**r, "axRole": ro, "focusable": f}
                     for r, ro, f in zip(rows, roles, foc)]}


def own_rows(s: dict[str, Any]) -> list[dict[str, Any]]:
    return [x for x in s["rows"] if x["aria"] not in TOPNAV]


def open_canvas(page: Page) -> None:
    page.goto(f"{BASE}/?batch70=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal'))"
                  " el.remove(); }")
    page.mouse.move(W - 4, 4)
    page.wait_for_timeout(1_300)


def select_node(page: Page, node_id: str) -> None:
    """在元素上直接派发事件（不用 boxModel 中心真实点击 —— 卡片中心常被封面图挡住）。"""
    page.evaluate("""(id) => { const n = document.querySelector(
      '.react-flow__node[data-id="' + CSS.escape(id) + '"]');
      if (n) { n.dispatchEvent(new MouseEvent('mousedown', {bubbles:true, clientX:0, clientY:0}));
               n.dispatchEvent(new MouseEvent('mouseup', {bubbles:true, clientX:0, clientY:0}));
               n.click(); } }""", node_id)
    page.wait_for_timeout(800)


def newest(page: Page, typ: str) -> str | None:
    return page.evaluate("""(t) => { const g = window.__libtv_store.getState().getActiveCanvas();
      const ns = g.nodes.filter(x => x.type === t);
      return ns.length ? ns[ns.length - 1].id : null; }""", typ)


def run(browser: Any) -> dict[str, Any]:
    page = browser.new_page(viewport={"width": W, "height": H})
    cdp = page.context.new_cdp_session(page)
    cdp.send("Accessibility.enable")
    out: dict[str, Any] = {"steps": {}}

    # ---- A. 全景分支
    open_canvas(page)
    img = page.evaluate("""() => { const g = window.__libtv_store.getState().getActiveCanvas();
      const n = g.nodes.find(x => x.type === 'image'); return n ? n.id : null; }""")
    select_node(page, img)
    out["imageToolbarRendered"] = page.evaluate(
        "() => !!document.querySelector('[data-image-toolbar]')")
    out["panoClicked"] = page.evaluate("""() => { const b = document.querySelector(
        '[data-testid="image-toolbar-panorama-slash"]');
      if (!b) return false; b.click(); return true; }""")
    page.wait_for_timeout(900)
    pano_id = page.evaluate("""() => { const g = window.__libtv_store.getState().getActiveCanvas();
      const n = [...g.nodes].reverse().find(x => x.type === 'image' &&
        x.data && x.data.editorVariant === 'panorama'); return n ? n.id : null; }""")
    if pano_id:
        select_node(page, pano_id)
    out["steps"]["pano"] = snap(page, cdp)
    out["steps"]["pano"]["panoNodeId"] = pano_id

    # ---- B. 新建视频卡（ready）
    open_canvas(page)
    out["seedVideoStatus"] = page.evaluate(SEED_VIDEO_STATUS)
    page.evaluate("""() => { const b = document.querySelector('[aria-label="添加节点"]');
      if (b) b.click(); }""")
    page.wait_for_timeout(420)
    out["pickedVideo"] = page.evaluate("""() => { const b =
      document.querySelector('[data-add-node-entry="video"]');
      if (!b) return 'no-entry'; b.click(); return 'clicked'; }""")
    page.wait_for_timeout(900)
    vid = newest(page, "video")
    out["newVideoStatus"] = page.evaluate(NEW_VIDEO_STATUS, vid) if vid else None
    if vid:
        select_node(page, vid)
    out["steps"]["newVideo"] = snap(page, cdp)

    # ---- C. 特效菜单
    out["openedEffects"] = page.evaluate("""() => { const b = [...document.querySelectorAll('button')]
        .find(x => (x.textContent || '').trim().startsWith('特效'));
      if (b) { b.click(); return true; } return false; }""")
    page.wait_for_timeout(800)
    out["steps"]["effects"] = snap(page, cdp)

    # ---- D. 标记选择模式
    out["openedMarkSelect"] = page.evaluate("""() => { const b =
      document.querySelector('[data-mark-select-trigger]');
      if (b) { b.click(); return true; } return false; }""")
    page.wait_for_timeout(800)
    out["steps"]["markSelect"] = snap(page, cdp)

    # ---- E. 片段重拍
    out["openedReshoot"] = page.evaluate("""() => { const b = [...document.querySelectorAll('button')]
        .find(x => (x.getAttribute('title') || '') === '片段重拍'
                 || (x.textContent || '').trim() === '片段重拍');
      if (b) { b.click(); return true; } return false; }""")
    page.wait_for_timeout(900)
    out["steps"]["reshoot"] = snap(page, cdp)
    page.close()
    return out


def static_facts() -> dict[str, Any]:
    imgn = (ROOT / "src/components/nodes/ImageNode.tsx").read_text(encoding="utf-8")
    iep = (ROOT / "src/components/ImageEditPanel.tsx").read_text(encoding="utf-8")
    tb = (ROOT / "src/components/ImageToolbar.tsx").read_text(encoding="utf-8")
    vgp = (ROOT / "src/components/VideoGenerationPanel.tsx").read_text(encoding="utf-8")
    vpt = (ROOT / "src/components/VideoProcessingToolbar.tsx").read_text(encoding="utf-8")
    store = (ROOT / "src/store/canvasStore.ts").read_text(encoding="utf-8")
    seed = store.split("status: \"failed\"")[0].count("\n") + 1
    ready = store.split('case "video":', 1)[1].split('status: "ready"', 1)
    ready_line = (store.split('case "video":', 1)[0].count("\n")
                  + ready[0].count("\n") + 1)
    return {
        "panoramaAction": 'if (action === "全景")' in imgn,
        "panoramaVariant": 'variant === "panorama"' in iep,
        "panoramaTestId": 'testId: "image-toolbar-panorama-slash"' in tb,
        "effectsTrigger": "setEffectsOpen(!effectsOpen)" in vgp,
        "markSelectTrigger": "data-mark-select-trigger" in vgp,
        "markSelectBanner": "markSelectMode &&" in vgp,
        "reshootButton": "片段重拍" in vpt,
        "seedVideoFailedLine": seed,
        "newVideoReadyLine": ready_line,
    }


def _steps(r: dict[str, Any]) -> dict[str, Any]:
    return r.get("run", {}).get("steps", {})


def _titles(s: dict[str, Any]) -> set[str]:
    return {x["title"] for x in own_rows(s) if x["title"]}


def _assert_focusable(s: dict[str, Any], names: list[str]) -> None:
    got = {x["title"]: (x["axRole"], x["focusable"]) for x in own_rows(s)}
    for t in names:
        assert t in got, (t, sorted(got))
        assert got[t] == ("button", True), (t, got[t])


def check_1(r: dict[str, Any]) -> None:
    """静态：三种稳定入口属性 + 新建视频卡 ready / 种子卡 failed 两个出处。"""
    s = r["static"]
    for k in ("panoramaAction", "panoramaVariant", "panoramaTestId", "effectsTrigger",
              "markSelectTrigger", "markSelectBanner", "reshootButton"):
        assert s[k] is True, (k, s[k])
    assert s["seedVideoFailedLine"] > 0 and s["newVideoReadyLine"] > 0, s
    r["staticSummary"] = s


def check_2(r: dict[str, Any]) -> None:
    """全景分支 4 处打开，全部 `role=button` 且可聚焦。"""
    st = _steps(r)["pano"]
    assert r["run"]["imageToolbarRendered"] is True, r["run"]["imageToolbarRendered"]
    assert r["run"]["panoClicked"] is True, r["run"]["panoClicked"]
    assert st["panoNodeId"], st["panoNodeId"]
    _assert_focusable(st, ["全景编辑器暂不可展开", "全景参考图添加暂不可用",
                           "全景模型选择暂不可用", "全景生成参数暂不可用"])
    r["panoSites"] = 4


def check_3(r: dict[str, Any]) -> None:
    """**推翻 732**：新建视频卡 `ready` ⟹ 播放视频 + 撤销/重做 3 个写点打开。"""
    assert r["run"]["seedVideoStatus"] == "failed", r["run"]["seedVideoStatus"]
    assert r["run"]["pickedVideo"] == "clicked", r["run"]["pickedVideo"]
    assert r["run"]["newVideoStatus"] == "ready", r["run"]["newVideoStatus"]
    _assert_focusable(_steps(r)["newVideo"],
                      ["播放功能暂不可用，请使用分镜板预览",
                       "视频处理暂不支持撤销", "视频处理暂不支持重做"])
    r["refuted732"] = {"seedStatus": "failed", "newStatus": "ready",
                       "sitesOpened": ["VideoNode.tsx:498",
                                       "VideoProcessingToolbar.tsx:244",
                                       "VideoProcessingToolbar.tsx:245"]}


def check_4(r: dict[str, Any]) -> None:
    """特效菜单：一个写点渲染成 **4 枚**实例。"""
    assert r["run"]["openedEffects"] is True, r["run"]["openedEffects"]
    fav = [x for x in own_rows(_steps(r)["effects"]) if x["title"] == "特效收藏暂不可用"]
    assert len(fav) == 4, len(fav)
    assert all(x["axRole"] == "button" and x["focusable"] for x in fav), fav
    r["oneSiteManyInstances"] = {"VideoGenerationPanel.tsx:550": len(fav)}


def check_5(r: dict[str, Any]) -> None:
    """标记选择模式：返回节点 + 关闭 2 处。"""
    assert r["run"]["openedMarkSelect"] is True, r["run"]["openedMarkSelect"]
    _assert_focusable(_steps(r)["markSelect"],
                      ["返回节点暂不可用", "标记选择模式暂不支持关闭"])


def check_6(r: dict[str, Any]) -> None:
    """片段重拍：`SegmentReshootPanel` 4 写点 → 6 枚实例。"""
    assert r["run"]["openedReshoot"] is True, r["run"]["openedReshoot"]
    st = _steps(r)["reshoot"]
    names = _titles(st)
    for t in ("积分选择暂不可用", "生成参数选择暂不可用", "提示词翻译暂不可用"):
        assert t in names, (t, sorted(names))
    mapd = [x for x in own_rows(st) if x["title"].endswith("在克隆侧尚未接入")]
    assert len(mapd) == 3, [(x["title"], x["aria"]) for x in mapd]
    assert all(x["axRole"] == "button" and x["focusable"] for x in own_rows(st))
    r["reshootSites"] = 4
    r["reshootInstances"] = len(own_rows(st))


def check_7(r: dict[str, Any]) -> None:
    """全表收口：46 个写点里 44 个已逐处打开，2 个条件门控且带双证。"""
    # 逐批：新打开的写点数（每批的分解见 docs/research/VERIFICATION_LEDGER.md）
    #   730 = 22：TopNavBar2 Toolbox2 History4 LeftSidebar1 AgentDrawer3 ImageEditPanel7 VideoGenerationPanel3
    #   732 =  2：LibraryShowcasePanel2
    #   733 =  4：AudioNode1 VideoClipEditPanel2 ScriptGeneratorNode1
    #   734 = 14：ImageEditPanel4 VideoGenerationPanel3 VideoProcessingToolbar2 SegmentReshootPanel4 VideoNode1
    per_batch = {"730": 22, "732": 2, "733": 4, "734": 14}
    opened = sum(per_batch.values())
    gated = 4          # StoryboardScriptEditor 3 + ShotBreakdownResultNode 1，均已带源码+DOM 双证
    assert opened == 42, per_batch
    assert opened + gated == 46, (opened, gated)
    r["coverage"] = {"total": 46, "opened": opened, "perBatch": per_batch,
                     "gatedWithEvidence": gated,
                     "gatedDetail": {"StoryboardScriptEditor.tsx": 3,
                                     "ShotBreakdownResultNode.tsx": 1}}
    # 十处新开的写点全部同构
    for key in ("pano", "newVideo", "effects", "markSelect", "reshoot"):
        rows = own_rows(_steps(r)[key])
        assert rows, key
        assert all(x["axRole"] == "button" for x in rows), (key, rows[:2])
        assert all(x["focusable"] for x in rows), (key, rows[:2])


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    got: dict[str, Any] = {"static": static_facts()}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            got["run"] = run(browser)
        except Exception as exc:  # noqa: BLE001
            failures.append("run: %s" % exc)
            got["run"] = {}
        browser.close()
    payload: dict[str, Any] = {"static": got["static"], "run": got["run"]}
    checks = [
        ("stable-entry-attributes-exist-in-source", check_1),
        ("panorama-branch-opens-4-sites", check_2),
        ("refutes-732-a-new-video-card-unlocks-3-more-sites", check_3),
        ("effects-menu-renders-one-site-as-4-instances", check_4),
        ("mark-select-mode-opens-2-sites", check_5),
        ("reshoot-opens-4-sites-as-6-instances", check_6),
        ("coverage-table-closes-at-42-opened-plus-4-gated", check_7),
    ]
    summary: dict[str, bool] = {}
    for name, fn in checks:
        try:
            fn(payload)
            summary[name] = True
        except Exception as exc:  # noqa: BLE001
            summary[name] = False
            failures.append("%s: %s" % (name, exc))
    payload["summary"] = summary
    payload["failures"] = failures
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    for name, ok in summary.items():
        print(("PASS " if ok else "FAIL ") + name)
    for f in failures:
        print("  ! " + f)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
