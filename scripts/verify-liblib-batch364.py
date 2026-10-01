#!/usr/bin/env python3
"""Verify Batch 364: 视频节点封面的「播放视频」按钮是死的 —— 同一功能两处实现只接了一半。

## 怎么找到的

Batch 361 给了并发 runner, 首次跑出可信全局图(297 passed / 14 failed, 剩余
全部属导演台并行 session)。**画布本体全绿**之后就没有可查的红了, 于是转向
「还没被验证过的地方」。

写了 `probe_liblib_batch364_coverage.py`: 取每个画布组件源码里的 `data-*`
标记, 看有没有 liblib 门禁引用过。

**第一版判据错了**: 我用「组件名在门禁里出现过没有」, 报出 30 个未覆盖,
里面赫然包括 `ImageEditPanel` —— 而它明明被 batch359 的节点面普查完整扫过。
**判据错了结论就全错**: 门禁靠 `data-*` 定位元素, 不靠组件名。
改用标记覆盖率后: UNCOVERED = 0(经阳性/阴性双向自检), PARTIAL = 10,
其中 `PictureEditPanel` 漏了 4 个 —— 含 `picture-edit-mark-selected`,
那是一整块「标记帧选中态 + 时间显示」的有状态交互, 从没被验证过。

于是写 `probe_liblib_batch364_picture_edit.py` 打开它 —— **打开它花了四步**,
每一步都是可达性事实:

1. `evaluate("(el)=>el.click()")` 选节点 → **React Flow 收不到选中态**
   (它的 onClick 依赖 pointer 事件链), 工具条不出现。改真实鼠标点击。
2. 节点确实选中了(store: `nodeIds: ["v-UGQZzZOpbv"]`), 但 `NodeToolbar` 仍 0
   —— fixture 里那个视频节点 **`status: "failed"`**, 工具条要求 `"ready"`。
3. 置 ready 还不够: 菜单选「主体消除」后面板不开 —— `selectPictureEdit` 有
   **时长守卫**, 源视频必须 3~15 秒(`VideoNode.tsx:338-347`)。
4. 前两处用 Playwright 的 `click()` 会**移动鼠标**触发菜单容器的
   `onMouseLeave` -> 菜单先被关掉, 点了个寂寞。改 `evaluate(el=>el.click())`。

**这四步本身就是结论的一部分**: 这段编辑面在默认 fixture 上**根本走不到**。
不是「懒得测」, 是「走不到, 所以任何门禁都碰不到它」。

## 抓到的缺陷: 一个从未被任何门禁发现的死控件

`src/components/nodes/VideoNode.tsx:490`:

```tsx
<button type="button" aria-label="播放视频"
  className="... size-14 ... hover:bg-black/70">
  <Play size={22} />
</button>
```

**无 onClick、无 disabled, 却带 `hover:bg-black/70`** —— 用户悬停看到它变亮,
点下去什么都不发生。它是视频节点封面上最大的那个圆形播放钮(56px),
视觉上最像「点了会播视频」。

**决定性对照 —— 同一功能两处实现, 只接了一半**:

| 位置 | 标记 | onClick |
|---|---|---|
| `StoryboardBoard.tsx:78` | `data-storyboard-play` | **有** —— `onPlay?.()` 打开灯箱 |
| `VideoNode.tsx:490` | 无 | **无** |

连 `grep -rl '播放视频' scripts/verify-liblib-*.py` 都是**空** ——
这个控件从未被任何门禁提及过。

## 修法: 与 358/359/360 同策, 不发明

源站行为未采样(源站人机验证仍阻塞), 且**不涉及付费/生成** —— 播放已有视频
不花钱。故不擅自接线, 按既定处置: 保持外观 + 去掉悬停骗人反馈 + `title` 说明
+ `data-inert` 标记。**几何与文案一律不动**(batch612 钉住的尺寸不动)。

`aria-disabled` 不用(会被 Playwright `is_disabled()` 算作禁用, 与既有门禁冲突,
见 batch358)。

## 断言

1. 防假零: 视频节点**必须真的被创建出来**, 且**真的进入 ready/合法时长**;
2. `picture-edit` 面板**必须真的打开**(打不开直接红, 不许报 0 问题);
3. 视频节点封面**无死控件**;
4. 视频编辑面**无静默丢弃、无死控件、无交互谎言**;
5. 惰性控件必须**自证**(`data-inert` + 非空 `title`), 不按名字开白名单;
6. **不误伤** `StoryboardBoard` 那个有 handler 的同名按钮;
7. 付费/只读既有约定不被破坏(诊断零错误);
8. 覆盖下界: 至少扫到 30 个控件。
"""

from __future__ import annotations

import json
import os
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

URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT = ROOT / "docs" / "research" / "liblib-batch364-2026-10-01" / "runtime-audit.json"

# 「视频节点封面的播放按钮」—— 判据**按位置**而不是按名字, 因为
# StoryboardBoard 里有一个**同名且有 handler** 的按钮, 按名字判会误伤。
DEAD_PLAY_SELECTOR = '.react-flow__node button[aria-label="播放视频"]'
STORYBOARD_PLAY_SELECTOR = '[data-storyboard-play]'
MIN_CONTROLS = 30


def promote_video(page: Page) -> str | None:
    """把第一个视频节点置为 ready + 合法时长, 返回其 id。

    为什么必须这么造: fixture 的视频节点是 `status: "failed"` 且时长不在
    3~15 秒, 于是 (a) VideoProcessingToolbar 不渲染(要求 ready),
    (b) selectPictureEdit 直接 return(时长守卫)。**这段面在默认画布上
    根本走不到** —— 这正是它从未被任何门禁扫到的原因。
    产品内的等价路径: 分镜板「待确认」卡片点确认 -> setVideoStatus(ready)。
    """
    return page.evaluate(
        """() => {
          const s = window.__libtv_store.getState();
          const canvas = s.canvases.find((c) => c.id === s.activeCanvasId);
          const video = (canvas?.nodes || []).find((n) => n.id?.startsWith('v-'));
          if (!video) return null;
          s.updateNodeData(video.id, { status: 'ready', durationSeconds: 6 });
          return video.id;
        }"""
    )


def select_video_node(page: Page) -> bool:
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(1800)
    page.keyboard.press("Alt+Shift+F")
    page.wait_for_timeout(700)
    if promote_video(page) is None:
        return False
    page.wait_for_timeout(400)
    node = page.locator('.react-flow__node[data-id^="v-"]').first
    box = node.bounding_box()
    if box is None:
        return False
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    # 真实鼠标点击: React Flow 的选中依赖 pointer 事件链, 合成 click 收不到
    page.mouse.move(cx, cy)
    page.wait_for_timeout(150)
    page.mouse.click(cx, cy)
    page.wait_for_timeout(800)
    return page.locator("[data-video-picture-edit-menu-trigger]").count() > 0


def open_picture_edit(page: Page) -> bool:
    trigger = page.locator("[data-video-picture-edit-menu-trigger]").first
    trigger.hover()
    page.wait_for_timeout(360)
    # 用 JS click 而非 Playwright click: 后者移动鼠标会触发容器的
    # onMouseLeave, 菜单先被关掉。
    items = page.locator("[data-video-picture-edit-action]")
    for i in range(items.count()):
        try:
            items.nth(i).evaluate("(el) => el.click()")
        except Exception:
            continue
        page.wait_for_timeout(450)
        if page.locator("[data-picture-edit-close]").count() > 0:
            return True
        close_all(page)
        trigger.hover()
        page.wait_for_timeout(300)
    return page.locator("[data-picture-edit-close]").count() > 0


def main() -> int:
    audit: dict[str, object] = {
        "checks": [],
        "errors": {"console": [], "page": [], "request": []},
    }
    checks: list[dict[str, object]] = audit["checks"]  # type: ignore[assignment]

    def check(name: str, ok: bool, detail: object = None) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("console", lambda m: m.type == "error" and audit["errors"]["console"].append(m.text))  # type: ignore[union-attr]
        page.on("pageerror", lambda e: audit["errors"]["page"].append(str(e)))  # type: ignore[union-attr]
        page.on("requestfailed", lambda r: audit["errors"]["request"].append(r.url))  # type: ignore[union-attr]

        # ---- 1. 视频节点必须真的进到 ready + 合法时长 ----
        selected = select_video_node(page)
        check("video-node:reachable-and-ready", selected,
              "未能把视频节点置为 ready 并选中工具条")
        if not selected:
            page.screenshot(path=str(AUDIT.parent / "unreachable.png"))
            browser.close()
            return report(audit)

        # ---- 2. 视频节点封面的播放按钮 ----
        close_all(page)
        page.wait_for_timeout(300)
        play = page.locator(DEAD_PLAY_SELECTOR)
        count = play.count()
        check("video-node:play-button-exists", count >= 1, f"count={count}")
        audit["videoPlayButton"] = page.evaluate(
            """(sel) => {
              const el = document.querySelector(sel);
              if (!el) return null;
              const cs = getComputedStyle(el);
              return {
                hasOnClickAttr: el.hasAttribute('onclick'),
                title: el.getAttribute('title'),
                inert: el.getAttribute('data-inert'),
                cursor: cs.cursor,
                hoverRule: Array.from(document.styleSheets).some(() => false),
                w: el.getBoundingClientRect().width,
              };
            }""",
            DEAD_PLAY_SELECTOR,
        )

        # ---- 3. 惰性控件必须自证: data-inert + 非空 title ----
        info = audit["videoPlayButton"] or {}
        check("video-play:declared-inert", info.get("inert") == "true", info.get("inert"))
        check("video-play:has-explanatory-title", bool((info.get("title") or "").strip()), info.get("title"))
        check("video-play:no-hover-affordance", info.get("cursor") == "default", info.get("cursor"))

        # ---- 4. 反向: 不误伤 StoryboardBoard 那个有 handler 的同名按钮 ----
        sb = page.locator(STORYBOARD_PLAY_SELECTOR)
        sb_count = sb.count()
        audit["storyboardPlay"] = {
            "count": sb_count,
            "inert": sb.first.get_attribute("data-inert") if sb_count else None,
        }
        check("storyboard-play:not-marked-inert", sb_count == 0 or audit["storyboardPlay"]["inert"] is None,
              audit["storyboardPlay"])

        # ---- 5. picture-edit 面板必须真的打开 ----
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(1500)
        select_video_node(page)
        opened = open_picture_edit(page)
        check("picture-edit:really-opened", opened, "面板未打开(不是 0 问题)")
        audit["pictureEdit"] = None
        if opened:
            snap = classify(page.evaluate(SCAN_JS))
            audit["pictureEdit"] = snap
            check("picture-edit:control-floor", snap.get("controls", 0) >= MIN_CONTROLS,
                  f"controls={snap.get('controls')}")
            check("picture-edit:no-silent-discard", not snap.get("silentDiscard"), snap.get("silentDiscard"))
            check("picture-edit:no-dead-control", not snap.get("deadControls"), snap.get("deadControls"))
            check("picture-edit:no-lying-affordance", not snap.get("lyingAffordance"),
                  snap.get("lyingAffordance"))

        page.screenshot(path=str(AUDIT.parent / "picture-edit.png"))
        browser.close()

    return report(audit)


def report(audit: dict) -> int:
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    failed = [c for c in audit["checks"] if not c["ok"]]  # type: ignore[union-attr]
    errs = audit["errors"]
    noisy = [e for e in list(errs["console"]) + list(errs["page"])  # type: ignore[index]
             if "ERR_ABORTED" not in e and "WebSocket" not in e]
    check_ok = not failed and not noisy
    print(f"Batch 364: {len(audit['checks']) - len(failed)}/{len(audit['checks'])} checks passed")  # type: ignore[arg-type]
    if failed:
        print("FAILED:", json.dumps(failed, ensure_ascii=False, indent=1))
    if noisy:
        print("DIAGNOSTICS:", json.dumps(noisy[:5], ensure_ascii=False, indent=1))
    if not check_ok:
        return 1
    print("Video node's cover play button is now declared inert with a title, "
          "and the picture-edit panel is reachable and clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
