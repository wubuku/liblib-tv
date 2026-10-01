#!/usr/bin/env python3
"""Batch 364 探针: 普查 PictureEditPanel —— 一个有交互却从未被任何门禁验证过的面。

## 怎么找到它的

写了 `probe_liblib_batch364_coverage.py`: 取每个画布组件源码里的 `data-*`
标记, 看有没有 liblib 门禁引用过。结果 **UNCOVERED = 0**(判据经阳性/阴性
双向自检), 但 **PARTIAL = 10**, 其中 `PictureEditPanel` 漏了 4 个标记:

    picture-edit-close  picture-edit-mark-id
    picture-edit-mark-selected  picture-edit-mark-time

后两个尤其可疑: 「标记帧的选中态 + 时间显示」是一整块**有状态的交互**,
却没有任何门禁碰过。batch359/360 的节点面普查扫了 `ImageEditPanel` /
`VideoGenerationPanel`, 独独漏了它 —— 同目录下最容易漏的一个。

> 第一版判据是「组件名在门禁里出现过没」, 报出 30 个未覆盖, 里面赫然包括
> `ImageEditPanel` —— 而它明明被完整扫过。**判据错了结论就全错**: 门禁靠
> `data-*` 定位元素, 不靠组件名。改用标记覆盖率后真相才出来。

## 判据与 batch359/360 完全一致

复用 `probe_liblib_batch359_node_surfaces.py` 的 `SCAN_JS` / `classify` /
`close_all`, 判据不维护第二份实现:
- **死控件** —— 自称可点(`<button>`/`role=button`/`aria-label`/`data-testid`)
  却没有自己的 handler, 却带悬停反馈;
- **静默丢弃** —— 点了把输入丢掉且不给任何反馈;
- **交互谎言** —— 声明惰性的控件还带 `hover:` 暗示(360 加的判据)。

## 打开路径

`VideoNode` 渲染 `PictureEditPanel`, 条件是
`status === "ready" && activeTool === "picture-edit" && pictureEditMode`。
入口是 `VideoProcessingToolbar` 里的 `data-video-picture-edit-menu-trigger`
**悬停**出菜单(hover menu, 不是点击), 选一项即进入。

**打不开就直接报「跳过」, 不报「0 问题」** —— 那是 360 立下的规矩。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from playwright.sync_api import Page, sync_playwright  # noqa: E402

from probe_liblib_batch359_node_surfaces import (  # noqa: E402
    SCAN_JS,
    classify,
    close_all,
)

URL = "http://localhost:4317"
OUT = ROOT / "docs" / "research" / "liblib-batch364-2026-10-01" / "picture-edit-census.json"

# 悬停菜单里的候选项 —— 源站/实现上都可能随版本变, 全试一遍, 别假设。
# 第一版只写了 `data-picture-edit-action`, 实测**一个都没匹配上**, 面板打不开;
# 真实标记是 `data-video-picture-edit-action`(`VideoProcessingToolbar.tsx:254`
# 的 `ToolbarMenuItem`)。**选择器写错时探针必须报「跳过」而不是「0 问题」** ——
# 它确实是这么报的, 所以这个错误是可见的, 没变成假零。
MENU_ITEM_SELECTORS = [
    '[data-video-picture-edit-action]',
    '[data-video-picture-edit-menu-item]',
    '[role="menuitem"]',
]


def open_picture_edit(page: Page) -> bool:
    """打开 PictureEditPanel。返回是否真的打开了。

    关键: 入口是 **hover** 菜单(不是 click), 且面板要求
    `status === "ready"` + `pictureEditMode` 非空。

    踩坑: 菜单项用 Playwright 的 `click()` 会因为**移动鼠标**而触发容器的
    `onMouseLeave` -> 菜单先被关掉, 于是点了个寂寞。改用
    `evaluate("(el)=>el.click()")`: 不移动鼠标, 直接派发 click, React 的
    onClick 照样收到(它只关心事件本身, 不关心坐标)。
    """
    trigger = page.locator("[data-video-picture-edit-menu-trigger]")
    if trigger.count() == 0:
        return False
    trigger.first.hover()
    page.wait_for_timeout(360)
    for sel in MENU_ITEM_SELECTORS:
        items = page.locator(sel)
        if items.count() == 0:
            continue
        for i in range(items.count()):
            try:
                items.nth(i).evaluate("(el) => el.click()")
            except Exception:
                continue
            page.wait_for_timeout(450)
            if page.locator("[data-picture-edit-close]").count() > 0:
                return True
            close_all(page)
            trigger.first.hover()
            page.wait_for_timeout(300)
    return page.locator("[data-picture-edit-close]").count() > 0


def prepare_canvas(page: Page) -> bool:
    """选中一个视频节点并整理画布, 让工具条可见。

    **踩了三个坑才走到这里**, 都记下来:

    1. `evaluate("(el)=>el.click()")` 选节点时 **React Flow 收不到选中态** ——
       它的 onClick 依赖 pointer 事件链, 合成 click 走不到那套判断,
       `VideoProcessingToolbar` 不出现(实测 trigger count=0)。改真实鼠标点击。
    2. 节点确实选中了(store 显示 `nodeIds: ["v-UGQZzZOpbv"]`), 但
       `NodeToolbar` 仍是 0 —— 因为 fixture 里那个视频节点
       **`status: "failed"`**, 而工具条要求 `status === "ready"`。
    3. 所以不能只「选中现有节点」, 得先让某个视频节点进入 ready。
       产品内的正常路径是分镜板的「待确认」卡片点确认
       (`StoryboardBoard.tsx:368` -> `setVideoStatus(nodeId, "ready")`),
       但 fixture 没有 pending 视频节点, 于是直接用 store 的
       `updateNodeData` 置位 —— 与那条 UI 路径落到**同一个状态**。
    4. 置 ready 还不够: `selectPictureEdit` 有一道**时长守卫**
       (`VideoNode.tsx:338-347`) —— 源视频必须 3~15 秒, 否则只弹一行提示
       `源视频时长需在 3~15 秒之间` 然后 return, 面板永远不开。
       fixture 的视频时长不在区间内, 所以菜单点得开、面板进不去。
       同样用 `updateNodeData` 把时长置到合法值(与产品内「改视频时长」等价)。

    「面板进不去」这件事本身是可达性事实, 不是探针故障: 当前 fixture 的
    视频节点全是 failed 且时长不在 3~15 秒区间, 所以这段编辑面在默认画布上
    **根本走不到**。这正是它从未被任何门禁扫到的原因。
    """
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(1800)
    page.keyboard.press("Alt+Shift+F")
    page.wait_for_timeout(700)

    # status -> ready (产品内等价路径: 分镜板「确认」按钮)
    # durationSeconds -> 6s (产品内等价路径: 改视频时长; 守卫要求 3~15 秒)
    promoted = page.evaluate(
        """() => {
          const s = window.__libtv_store.getState();
          const canvas = s.canvases.find((c) => c.id === s.activeCanvasId);
          const video = (canvas?.nodes || []).find((n) => n.id?.startsWith('v-'));
          if (!video) return null;
          s.updateNodeData(video.id, { status: 'ready', durationSeconds: 6 });
          return video.id;
        }"""
    )
    if promoted is None:
        return False
    page.wait_for_timeout(500)

    videos = page.locator('.react-flow__node[data-id^="v-"]')
    if videos.count() == 0:
        return False
    node = videos.first
    box = node.bounding_box()
    if box is None:
        return False
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.wait_for_timeout(150)
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.wait_for_timeout(800)
    return page.locator("[data-video-picture-edit-menu-trigger]").count() > 0


def main() -> int:
    result: dict[str, object] = {"states": {}, "errors": []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("console", lambda m: m.type == "error" and result["errors"].append(f"console:{m.text}"))

        prepared = prepare_canvas(page)
        result["prepared"] = prepared
        if not prepared:
            result["states"]["picture-edit"] = {
                "__skipped__": "未能选中带视频工具条的节点, 未测(不是 0 问题)"
            }
        else:
            close_all(page)
            opened = open_picture_edit(page)
            if not opened:
                result["states"]["picture-edit"] = {
                    "__skipped__": "PictureEditPanel 未打开, 未测(不是 0 问题)"
                }
            else:
                result["states"]["picture-edit"] = classify(page.evaluate(SCAN_JS))
                # 标记帧交互: 逐个点 mark, 看选中态与时间是否变
                marks = page.locator("[data-picture-edit-mark-id]")
                picked: list[dict[str, object]] = []
                for i in range(min(marks.count(), 4)):
                    m = marks.nth(i)
                    try:
                        m.click(timeout=2500)
                    except Exception:
                        continue
                    page.wait_for_timeout(220)
                    picked.append(page.evaluate(
                        """() => {
                          const sel = document.querySelectorAll(
                            '[data-picture-edit-mark-selected="true"]');
                          const t = document.querySelector(
                            '[data-picture-edit-mark-time]');
                          return {
                            selectedCount: sel.length,
                            time: t ? t.getAttribute('data-picture-edit-mark-time') : null,
                          };
                        }"""
                    ))
                result["markInteraction"] = picked
        page.screenshot(path=str(ROOT / "docs" / "research" / "liblib-batch364-2026-10-01" / "picture-edit.png"))
        browser.close()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    st = result["states"].get("picture-edit", {})
    if "__skipped__" in st:
        print(f"SKIPPED: {st['__skipped__']}")
    else:
        print(f"controls={st.get('controls')} silentDiscard={st.get('silentDiscard')} "
              f"deadControls={st.get('deadControls')} lyingAffordance={st.get('lyingAffordance')}")
        if st.get("deadControls"):
            print("DEAD:", json.dumps(st["deadControls"], ensure_ascii=False))
        if st.get("lyingAffordance"):
            print("LYING:", json.dumps(st["lyingAffordance"], ensure_ascii=False))
    print("markInteraction:", json.dumps(result.get("markInteraction"), ensure_ascii=False))
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
