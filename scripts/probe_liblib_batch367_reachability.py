#!/usr/bin/env python3
"""Batch 367 探针: 9 个源码候选, 逐个用浏览器证实**是否真的可触达**。

## 为什么源码普查不够

`probe_liblib_batch367_dead_buttons.py` 只报「源码里没有 handler」, 这**不等于**
「用户在界面上会被骗」: 面板可能根本没被渲染, 控件可能压根不在视口里。
batch 360 立下的规矩在这里继续适用: **打不开就报「跳过」, 不报「0 问题」**。

## 第一版探针 7/8 跳过 —— 教训比结果重要

第一版的入口选择器全是**猜**的, 结果只有 undo/redo 命中。逐个回源码核对后发现
每一处都猜错了, 而错法各不相同:

| 候选 | 我猜的 | 真实入口 |
|---|---|---|
| 片段重拍 | `[data-video-tool='reshoot']` | 根本没有这种标记; 是 `ToolbarButton label="片段重拍"`, 靠文本找 |
| 去字幕说明 | 往节点 data 写 `subtitleMode` | `subtitleMode` 是**从 activeTool 派生**的, 写 node data 一点用没有 |
| 参考选择横幅 | `data-reference-select-trigger` | 那个开关的是 refSelectMode; 「关闭」在 **`markSelectMode`** 横幅里, 入口是 `data-mark-select-trigger` |
| 添加节点 | `Alt+Shift+S` | 真实路径是**双击画布空白**; 菜单项是 `data-add-node-entry` |
| 准备资产 | 找 tab 标记 | 不是 tab, 是 `data-storyboard-next="assets"` 那颗「下一步」 |

> **教训: 入口必须从源码挖, 不能猜。** 猜出来的选择器命中不了时, 探针会
> 报「跳过」, 而「跳过」很容易被下一步当成「没问题」——
> 7 个跳过看起来像 7 个干净的面, 实际是 7 个**没测的面**。
> 所以本探针把 `__skipped__` 做成必须人工复核的显式信号, 并在结尾汇总。

另外第一版还踩了 **stale state**: 调完 `addNodeAtPosition` 之后仍用调用前
捕获的 `const s = ...getState()` 去读画布 —— zustand 的 state 是不可变快照,
旧引用永远是旧的, 于是「节点没找到」。必须**重新 getState()**。

## 本探针要回答的三类问题

1. **够不着** —— 面板在默认 fixture 下打不开。这类不改代码, 只记录。
2. **够得着且确实是死的** —— 用户能看到、能点到、点了什么都不发生。
   这类才按 batch358/359/360/364/366 的既有处置做惰性自证。
3. **够得着但我判据错了** —— `SubtitleErasePanel` 的「查看框选去字幕说明」
   源码上没有 `onClick`, 看着像死控件; 但它是个 **hover 目标**: 旁边的说明浮层
   靠 `group-hover:visible` 显现。探针会**主动验证浮层真的会出来** ——
   出来就证明它有行为, 是**普查误报, 不能改**。
   「无 handler = 死控件」这个假设, 在 hover 目标面前是错的。

## 视口

用 1680×1050(与本线截图一致)。1440 下 undo/redo 会被工具条挤出视口
(`inViewport: false`), 拿那种状态谈「用户点得到吗」是不诚实的。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from playwright.sync_api import Page, sync_playwright  # noqa: E402

URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
OUT = ROOT / "docs" / "research" / "liblib-batch367-2026-10-01" / "reachability.json"
VIEWPORT = {"width": 1680, "height": 1050}

SKIPPED = "__skipped__"
ERROR = "__error__"

# 采集一个候选控件的运行时事实。只读, 不点 —— 点不点由定性阶段决定。
PROBE_JS = """
(el) => {
  const cs = getComputedStyle(el);
  const r = el.getBoundingClientRect();
  const on = (n) => el.getAttribute(n);
  return {
    visible: r.width > 0 && r.height > 0 && cs.visibility !== "hidden" && cs.opacity !== "0",
    rect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
    inViewport: r.top >= 0 && r.left >= 0 && r.bottom <= innerHeight && r.right <= innerWidth,
    title: on("title"),
    inert: on("data-inert"),
    disabled: el.disabled === true,
    cursor: cs.cursor,
    ariaLabel: on("aria-label"),
  };
}
"""


def reset_canvas(page: Page) -> None:
    """回到干净的默认画布 —— 每个候选独立尝试, 避免上一个的残留状态误导下一个。"""
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(2000)


def promote_video_node(page: Page) -> str | None:
    """把某个视频节点置成 ready + 合法时长, 让 VideoProcessingToolbar 出现。

    VideoNode 的工具条条件是 `status === "ready" && !subtitleMode &&
    activeTool !== "picture-edit"`; 时长 3~15 秒是 picture-edit 的守卫。
    产品内等价路径: 分镜板「确认」按钮 / 改视频时长。
    """
    node_id = page.evaluate(
        """() => {
          const s = window.__libtv_store.getState();
          const canvas = s.canvases.find((c) => c.id === s.activeCanvasId);
          const video = (canvas?.nodes || []).find((n) => n.id?.startsWith('v-'));
          if (!video) return null;
          s.updateNodeData(video.id, { status: 'ready', durationSeconds: 6 });
          return video.id;
        }"""
    )
    page.wait_for_timeout(500)
    return node_id


def node_in_viewport(page: Page, selector: str) -> "object | None":
    """挑第一个**真的在视口里**的节点, 返回它的 bounding_box。

    第一版直接用 `.first`, 结果 5 个图片节点有 4 个在视口**左侧外面**
    (x = -514 / -368...), 鼠标点了个空气, 选中态一直是 `[]`。
    **「点不到」被误读成「面板没渲染」** —— 而「点不到」和「不存在」是两回事。

    顺带记一笔: `store.setViewport({...})` 改不动 React Flow 实例的视口
    (节点坐标纹丝不动), 所以「拉远一点再看」这条退路是不通的, 只能挑对的节点。
    """
    loc = page.locator(selector)
    vp = page.viewport_size or {"width": 1680, "height": 1050}
    for i in range(loc.count()):
        box = loc.nth(i).bounding_box()
        if box is None:
            continue
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        if 0 <= cx <= vp["width"] and 0 <= cy <= vp["height"]:
            return box
    return None


def select_video_node(page: Page) -> bool:
    """**真实鼠标点击**选中视频节点。

    `evaluate(el => el.click())` 选不中: React Flow 的 onClick 依赖 pointer
    事件链, 合成 click 走不到那套判断, 面板不出现(实测 selection 仍为空)。
    """
    loc = page.locator('.react-flow__node[data-id^="v-"]')
    if loc.count() == 0:
        return False
    box = loc.first.bounding_box()
    if box is None:
        return False
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(cx, cy)
    page.wait_for_timeout(150)
    page.mouse.click(cx, cy)
    page.wait_for_timeout(900)
    return page.evaluate(
        "() => (window.__libtv_store.getState().selectedNodeIds || []).length === 1"
    )


def hover_menu_pick(page: Page, trigger_sel: str, item_sel: str) -> bool:
    """hover 菜单 -> 用 evaluate 点菜单项。

    普通 `click()` 会移动鼠标, 触发容器的 `onMouseLeave` 把菜单关掉, 于是
    点了个寂寞(见 ToolbarMenu 的 onMouseLeave)。`evaluate` 不动鼠标,
    React 的 onClick 照样收到。
    """
    trigger = page.locator(trigger_sel)
    if trigger.count() == 0:
        return False
    trigger.first.hover()
    page.wait_for_timeout(380)
    items = page.locator(item_sel)
    if items.count() == 0:
        return False
    items.first.evaluate("(el) => el.click()")
    page.wait_for_timeout(500)
    return True


def inspect(page: Page, selector: str, label: str, context: str = "") -> dict[str, object]:
    loc = page.locator(selector)
    if loc.count() == 0:
        hint = f"；上下文: {context}" if context else ""
        return {SKIPPED: f"选择器 {selector} 在当前状态下不存在{hint}"}
    out: dict[str, object] = {}
    for i in range(min(loc.count(), 4)):
        try:
            facts = loc.nth(i).evaluate(PROBE_JS)
        except Exception as exc:  # noqa: BLE001
            facts = {ERROR: f"{type(exc).__name__}: {exc}"}
        facts["selector"] = selector
        out[f"{label}[{i}]" if i else label] = facts
    return out


# ---------------------------------------------------------------- 各候选的打开路径


def probe_image_edit(page: Page) -> dict[str, object]:
    """PanoramaEditPanel 的「展开全景编辑器」。

    `ImageEditPanel.tsx:50` 按 `variant` 分支, 死按钮在 **`variant === "panorama"`**
    的 `PanoramaEditPanel` 里。默认 fixture 的图片节点是 empty/prompt/referenced,
    所以光「选中图片节点」**根本看不到它** —— 第一版就是这么判成「不存在」的,
    差点把一个真死控件当成误报放过去。

    真实路径: 选中图片节点 -> 工具条点「全景」(`data-testid="image-toolbar-panorama-slash"`)
    -> 派生出一个 `editorVariant: "panorama"` 的新节点 -> 选中它。
    """
    reset_canvas(page)
    box = node_in_viewport(page, '.react-flow__node[data-id^="i-"]')
    if box is None:
        return {SKIPPED: "视口内没有任何图片节点(4/5 个都在左侧外面), 未测"}
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(cx, cy)
    page.wait_for_timeout(180)
    page.mouse.click(cx, cy)
    page.wait_for_timeout(900)
    sel = page.evaluate("() => window.__libtv_store.getState().selectedNodeIds || []")
    if not sel:
        return {SKIPPED: f"图片节点没选中(选中态={sel}), 未测"}
    pano = page.locator('[data-testid="image-toolbar-panorama-slash"]')
    if pano.count() == 0:
        return {SKIPPED: "图片工具条上找不到「全景」, 未测"}
    pano.first.evaluate("(el) => el.click()")
    page.wait_for_timeout(1000)
    ids = page.evaluate(
        """() => {
          const s = window.__libtv_store.getState();
          const c = s.canvases.find((x) => x.id === s.activeCanvasId);
          return (c?.nodes || [])
            .filter((n) => n.data?.editorVariant === 'panorama')
            .map((n) => n.id);
        }"""
    )
    if not ids:
        return {SKIPPED: "点了「全景」但没派生出 panorama 节点, 未测"}
    node = page.locator(f'.react-flow__node[data-id="{ids[0]}"]')
    pb = node.bounding_box()
    if pb is None:
        return {SKIPPED: "panorama 节点无几何, 未测"}
    page.mouse.move(pb["x"] + pb["width"] / 2, pb["y"] + pb["height"] / 2)
    page.wait_for_timeout(180)
    page.mouse.click(pb["x"] + pb["width"] / 2, pb["y"] + pb["height"] / 2)
    page.wait_for_timeout(900)
    return inspect(
        page,
        'button[aria-label="展开全景编辑器"]',
        "expand-panorama",
        f"已选中 panorama 节点 {ids[0]}",
    )


def probe_segment_reshoot(page: Page) -> dict[str, object]:
    """SegmentReshootPanel: 需 `activeTool === 'reshoot'`。

    入口是 VideoProcessingToolbar 里那颗**没有 data-标记**的「片段重拍」按钮
    —— 第一版猜的 `[data-video-tool='reshoot']` 根本不存在。
    """
    reset_canvas(page)
    promote_video_node(page)
    if not select_video_node(page):
        return {SKIPPED: "未能选中视频节点, 未测"}
    btn = page.locator('button:has-text("片段重拍")')
    if btn.count() == 0:
        return {SKIPPED: "工具条上找不到「片段重拍」按钮, 未测"}
    btn.first.click()
    page.wait_for_timeout(700)
    return inspect(
        page,
        'button[aria-label="翻译片段重拍提示词"]',
        "translate-prompt",
        "已点「片段重拍」",
    )


def probe_subtitle_help(page: Page) -> dict[str, object]:
    """SubtitleErasePanel: 需 status ready + activeTool === 'subtitle-region'。

    `subtitleMode` 是**从 activeTool 派生**的(`VideoNode.tsx:168-173`),
    往 node data 写 `subtitleMode` 完全无效 —— 这是第一版的错法。
    真实路径: hover「智能去字幕」-> 选「框选去字幕」。
    """
    reset_canvas(page)
    promote_video_node(page)
    if not select_video_node(page):
        return {SKIPPED: "未能选中视频节点, 未测"}
    if not hover_menu_pick(
        page, "[data-video-subtitle-menu-trigger]", '[data-video-subtitle-mode="region"]'
    ):
        return {SKIPPED: "未能通过 hover 菜单切到「框选去字幕」, 未测"}
    result = inspect(page, "[data-subtitle-erase-help]", "subtitle-help", "已切到框选去字幕")
    loc = page.locator("[data-subtitle-erase-help]")
    if loc.count() == 0:
        result["tooltipProbe"] = {SKIPPED: "按钮没出现, 浮层无从验证"}
        return result
    loc.first.hover()
    page.wait_for_timeout(500)
    # 浮层是 button 的兄弟 span, 靠 group-hover 显现
    result["tooltipProbe"] = page.evaluate(
        """() => {
          const btn = document.querySelector('[data-subtitle-erase-help]');
          const panel = btn?.parentElement?.querySelector('span.pointer-events-none');
          if (!panel) return { found: false };
          const cs = getComputedStyle(panel);
          const r = panel.getBoundingClientRect();
          return {
            found: true,
            visible: cs.visibility !== 'hidden' && cs.opacity !== '0' && r.height > 0,
            opacity: cs.opacity,
            visibility: cs.visibility,
            text: (panel.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 70),
          };
        }"""
    )
    return result


def probe_storyboard_assets(page: Page) -> dict[str, object]:
    """StoryboardScriptEditor 的「准备资产」步。

    真实路径: 点侧栏 `button[aria-label="添加节点"]` 开 AddNodePanel
    -> `data-add-node-entry="script"`(点它只是**开子菜单**, 不建节点)
    -> 子菜单里的 `data-add-node-entry="script-new"`(建出 script-generator 节点)
    -> 面板上再点「自己编写分镜脚本」才打开编辑器
    -> 点「下一步：准备资产」(`data-storyboard-next="assets"`)。
    资产页**不是 tab**, 没有 tab 标记。

    第一版用「双击画布空白」开面板, 实测**打不开**(dblclick 落点被别的元素吃掉,
    `isAddNodePanelOpen` 始终 false)。改用侧栏那颗按钮 —— 它是产品里真正的
    「添加节点」入口, 双击只是快捷方式。
    第一版还漏了「自己编写分镜脚本」这一步, 于是 `script-new` 建出节点后
    就直接去找编辑器, 自然找不到。
    """
    reset_canvas(page)
    opener = page.locator('button[aria-label="添加节点"]')
    if opener.count() == 0:
        return {SKIPPED: "侧栏找不到「添加节点」按钮, 未测"}
    opener.first.click()
    page.wait_for_timeout(700)
    if page.locator("[data-add-node-entry]").count() == 0:
        return {SKIPPED: "AddNodePanel 未打开, 未测"}
    main_script = page.locator('[data-add-node-entry="script"]')
    if main_script.count() == 0:
        return {SKIPPED: "主菜单里没有「脚本」入口, 未测"}
    main_script.first.evaluate("(el) => el.click()")
    page.wait_for_timeout(600)
    new_script = page.locator('[data-add-node-entry="script-new"]')
    if new_script.count() == 0:
        return {SKIPPED: "脚本子菜单没开, 未测"}
    new_script.first.evaluate("(el) => el.click()")
    page.wait_for_timeout(1100)
    write = page.locator('button:has-text("自己编写分镜脚本")')
    if write.count() == 0:
        return {SKIPPED: "script-generator 面板没出「自己编写分镜脚本」, 未测"}
    write.first.evaluate("(el) => el.click()")
    page.wait_for_timeout(900)
    if page.locator("[data-storyboard-editor]").count() == 0:
        return {SKIPPED: "分镜脚本编辑器未打开, 未测"}
    nxt = page.locator('[data-storyboard-next="assets"]')
    if nxt.count() == 0:
        return {SKIPPED: "编辑器里找不到「下一步：准备资产」, 未测"}
    nxt.first.evaluate("(el) => el.click()")
    page.wait_for_timeout(600)
    return inspect(page, "[data-storyboard-asset-add]", "asset-add", "已到准备资产步")


def probe_effects_favorite(page: Page) -> dict[str, object]:
    """特效库里的「收藏」——`data-effects-trigger` 开库, 再 hover 卡片让心形浮现。"""
    reset_canvas(page)
    promote_video_node(page)
    if not select_video_node(page):
        return {SKIPPED: "未能选中视频节点, 未测"}
    trig = page.locator("[data-effects-trigger]")
    if trig.count() == 0:
        return {SKIPPED: "找不到「特效」pill(data-effects-trigger), 未测"}
    trig.first.click()
    page.wait_for_timeout(700)
    if page.locator("[data-effects-gallery]").count() == 0:
        return {SKIPPED: "特效库未打开, 未测"}
    card = page.locator("[data-effects-card]")
    if card.count() == 0:
        return {SKIPPED: "特效库里没有卡片, 未测"}
    card.first.hover()
    page.wait_for_timeout(500)
    return inspect(page, '[data-effects-gallery] button[aria-label="收藏"]', "favorite", "已开库并 hover 卡片")


def probe_mark_select_close(page: Page) -> dict[str, object]:
    """标记选择模式的横幅「关闭」。

    第一版接的是 `data-reference-select-trigger`, 它开的是 **refSelectMode**;
    「关闭」在 **markSelectMode** 横幅里, 入口是 `data-mark-select-trigger`。
    """
    reset_canvas(page)
    promote_video_node(page)
    if not select_video_node(page):
        return {SKIPPED: "未能选中视频节点, 未测"}
    trig = page.locator("[data-mark-select-trigger]")
    if trig.count() == 0:
        return {SKIPPED: "找不到「标记」pill(data-mark-select-trigger), 未测"}
    trig.first.click()
    page.wait_for_timeout(700)
    if page.locator("[data-mark-select-banner]").count() == 0:
        return {SKIPPED: "标记选择横幅未出现, 未测"}
    return inspect(
        page,
        '[data-mark-select-banner] button[aria-label="关闭"]',
        "banner-close",
        "横幅已出现",
    )


def probe_video_undo_redo(page: Page) -> dict[str, object]:
    """VideoProcessingToolbar 的撤销/重做。

    同工具条的对照物: 「下载视频封面」是 `<a download>`(真实行为),
    「展开视频」有 onClick 设 lastAction。只有这两个既无 handler 又带 hover。
    """
    reset_canvas(page)
    promote_video_node(page)
    if not select_video_node(page):
        return {SKIPPED: "未能选中视频节点, 未测"}
    if page.locator("[data-video-picture-edit-menu-trigger]").count() == 0:
        return {SKIPPED: "视频工具条未出现, 未测"}
    return {
        "undo": inspect(page, 'button[aria-label="撤销视频处理"]', "undo", "工具条在"),
        "redo": inspect(page, 'button[aria-label="重做视频处理"]', "redo", "工具条在"),
        "control-download": inspect(page, 'a[aria-label="下载视频封面"]', "download", "对照组"),
        "control-expand": inspect(page, 'button[aria-label="展开视频"]', "expand", "对照组"),
    }


def probe_shot_breakdown_music(page: Page) -> dict[str, object]:
    """分镜拆解的音乐维度结果节点。

    产品内路径: 分镜拆解节点勾「音乐」维度 -> 点开始 -> 右侧生成结果节点。
    这里调同一个 store action `completeShotBreakdown`, 落到同一状态。

    **踩坑**: 第一版调完 `addNodeAtPosition` 后仍用调用前捕获的
    `const s = ...getState()` 读画布 —— zustand state 是不可变快照, 旧引用永远
    是旧的, 于是永远「节点没找到」。必须重新 getState()。

    **落点也得挑**: 源节点放 x=1200 时, 生成的音乐结果节点正好落在屏幕
    x≈341(视口内); 放 x=-200 时按钮在 x≈-395 —— **渲染出来了但用户在屏幕上
    看不到**。`visible: true` 与 `inViewport: true` 必须一起看, 只看前者
    会把「画布外」当成「够得着」。
    """
    reset_canvas(page)
    created = page.evaluate(
        """() => {
          const get = () => window.__libtv_store.getState();
          const nodes = () => {
            const s = get();
            const c = s.canvases.find((x) => x.id === s.activeCanvasId);
            return c?.nodes || [];
          };
          let source = nodes().find((n) => n.type === 'shot-breakdown');
          if (!source) {
            get().addNodeAtPosition('shot-breakdown', { x: 1200, y: 0 }, {});
            source = nodes().find((n) => n.type === 'shot-breakdown');
          }
          if (!source) return { ok: false, why: '加不进分镜拆解节点' };
          get().completeShotBreakdown(source.id, ['music']);
          const made = nodes().find(
            (n) => n.type === 'shot-breakdown-result' && n.data?.category === 'music'
          );
          return { ok: !!made, why: made ? '' : 'completeShotBreakdown 没产出音乐结果节点' };
        }"""
    )
    if not created.get("ok"):
        return {SKIPPED: f"{created.get('why')}, 未测"}
    page.wait_for_timeout(1000)
    return inspect(
        page,
        '[data-shot-breakdown-category="music"] button[aria-label="播放 BGM"]',
        "play-bgm",
        "音乐结果节点已生成",
    )


PROBES = {
    "image-edit/expand-panorama": probe_image_edit,
    "segment-reshoot/translate-prompt": probe_segment_reshoot,
    "subtitle-erase/help (误报嫌疑)": probe_subtitle_help,
    "storyboard-assets/add": probe_storyboard_assets,
    "video-gen/favorite": probe_effects_favorite,
    "video-gen/banner-close": probe_mark_select_close,
    "video-toolbar/undo-redo": probe_video_undo_redo,
    "shot-breakdown/play-bgm": probe_shot_breakdown_music,
}


def main() -> int:
    report: dict[str, object] = {"url": URL, "viewport": VIEWPORT, "results": {}}
    skipped: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport=VIEWPORT)
        page.on("pageerror", lambda e: report.setdefault("pageerrors", []).append(str(e)))
        for name, fn in PROBES.items():
            try:
                result = fn(page)
            except Exception as exc:  # noqa: BLE001
                result = {ERROR: f"{type(exc).__name__}: {exc}"}
            report["results"][name] = result
            # 跳过必须显式汇总 —— 「跳过」很容易在下一步被当成「没问题」
            if any(k == SKIPPED for k in result) or SKIPPED in result:
                skipped.append(name)
            print(f"── {name}")
            print(json.dumps(result, ensure_ascii=False, indent=2)[:1600])
        browser.close()

    report["summary"] = {
        "totalProbes": len(PROBES),
        "skipped": skipped,
        "skippedCount": len(skipped),
        "note": "skipped 不等于 0 问题; 它表示这个面本次没测到, 必须人工复核",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n探针 {len(PROBES)} 项, 跳过 {len(skipped)} 项: {skipped}")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
