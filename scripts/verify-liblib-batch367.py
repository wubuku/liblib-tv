#!/usr/bin/env python3
"""Verify Batch 367: 画布本体里 7 处「自称可点却没有接线, 也没自证惰性」的控件。

## 怎么找到的

Batch 366 的教训是: `data-*` **标记覆盖率会低估**组件的控件数
(`StoryboardScriptEditor` 几十个按钮只有一个带标记)。所以 batch 367 先补了一个
**不依赖标记**的判据 —— `probe_liblib_batch367_dead_buttons.py` 直接扫源码里的
`<button>`, 看它是否「自称可点」(有 `aria-label`/`data-testid`/`role="button"`)
却同时满足「无 onXxx / 无 disabled / 无 data-inert」。

**那个普查工具自己先出了两个洞**, 都是靠阳性对照抓出来的:

1. 它用 `COMPONENTS.glob("*.tsx")` —— **非递归**。于是 `src/components/nodes/`
   (16 个 tsx, **画布本体核心**: VideoNode / ImageNode / ShotBreakdownResultNode
   都在这儿) 整片没被扫。而 batch 364 亲手修掉的「播放视频」死控件就在
   `nodes/VideoNode.tsx` —— **上一批已经证明这条线有这类缺陷, 普查却对它失明**。
2. 跨线判定 `part.startswith("Jimeng")` 撞上小写目录名 `jimeng/`, 于是把 42 个
   并行 session 的文件全当成本线候选报了出来。误报跨线比漏报更糟: 它会诱导
   后续去改别人的 WIP。

> **教训: 判据的下界必须在「你以为覆盖的每个目录」上分别验证, 不能只在顶层验一次。**

## 第二道闸: 源码普查只报候选, 可触达性必须浏览器实测

`probe_liblib_batch367_reachability.py` 逐个走到那 7 处, 采运行时事实。
第一版 8 项里**跳过 7 项** —— 因为入口选择器全是猜的。逐个回源码核对后,
每一处都猜错了, 而错法各不相同: `subtitleMode` 是从 `activeTool` 派生的
(往 node data 写完全无效); 「关闭」在 `markSelectMode` 横幅而不在
`refSelectMode`; 4/5 个图片节点在视口**左侧外面**, 点了个空气;
`visible: true` 但 `inViewport: false` 的按钮渲染了但用户在屏幕上**看不到**。

> **教训: 「跳过」极易在下一步被当成「没问题」。** 7 个跳过看起来像 7 个干净的
> 面, 实际是 7 个**没测的面**。所以本门禁把「走不到」直接判红, 不给假零的机会。

## 一个反例: 普查也会误报

`SubtitleErasePanel.tsx:472` 的「查看框选去字幕说明」没有 onClick, 看着是标准
死控件。但浏览器实测: 悬停它, 旁边的使用说明浮层 `opacity` 变 1、文案完整 ——
**它是有行为的 hover 目标, 不是死控件**。所以:
- 普查只给它打 `hoverTarget` 标签**照常上报**(过滤掉会让人学不到东西);
- 本门禁**断言它没有被改成 inert**, 且浮层仍然能弹出来 —— 防止「批量修死控件」
  顺手把一个好控件改坏。

## 修法: 与 358/359/360/364/366 同策, 不发明

源站行为全部未采样(人机验证阻塞), 撤销栈/资产新增/收藏/全景展开/BGM 试听
都没有源站事实。按既定处置让 UI 停止撒谎: 去掉悬停骗人反馈 + `cursor: default`
+ `title` 说明 + `data-inert` 自证惰性。**几何与文案一律不动。**

## 断言

1. **防假零**: 7 处必须**真的走到**, 走不到直接红;
2. 每个控件 `data-inert="true"` + 非空 `title` + `cursor: default` + **无 hover 类**;
3. **几何未变**: class 尺寸 token 精确比对 + 运行时 rect 落在实测带宽内;
4. **反向断言**: 能用的 hover 控件没被改 inert, 且浮层仍会弹;
5. **对照组未被误伤**: 同工具条上真能用的「展开视频」「下载视频封面」行为不变;
6. 源码普查里**非 hoverTarget** 的候选数为 0;
7. 诊断零错误。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from playwright.sync_api import Page, sync_playwright  # noqa: E402

import probe_liblib_batch367_dead_buttons as CENSUS  # noqa: E402
import probe_liblib_batch367_reachability as REACH  # noqa: E402

URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT = ROOT / "docs" / "research" / "liblib-batch367-2026-10-01" / "verify.json"
VIEWPORT = REACH.VIEWPORT

# 探针名 -> 该面必须出现的惰性控件 (aria-label -> 源码里的尺寸 token)
#
# `class_size` 是**精确契约**: 我承诺「几何不动」, 所以尺寸 token 必须原样保留。
# `rect` 是运行时实测值(含画布 zoom 0.526 的缩放), 留 ±3px 只为吸收渲染取整,
# 不是给「偷偷改小一号」留口子 —— 那会被 class_size 精确挡住。
EXPECTED_INERT: dict[str, dict[str, tuple[int, int]]] = {
    "image-edit/expand-panorama": {"展开全景编辑器": {"class_size": ("size-7",), "rect": (28, 28)}},
    "segment-reshoot/translate-prompt": {"翻译片段重拍提示词": {"class_size": ("size-8",), "rect": (32, 32)}},
    "storyboard-assets/add": {
        "新增角色资产": {"class_size": ("h-[190px]", "w-[195px]"), "rect": (195, 190)},
        "新增场景资产": {"class_size": ("h-[190px]", "w-[195px]"), "rect": (195, 190)},
        "新增道具资产": {"class_size": ("h-[190px]", "w-[195px]"), "rect": (195, 190)},
    },
    "video-gen/favorite": {"收藏": {"class_size": ("size-6",), "rect": (24, 24)}},
    "video-gen/banner-close": {"关闭": {"class_size": (), "rect": (10, 24)}},
    "video-toolbar/undo-redo": {
        "撤销视频处理": {"class_size": ("size-8",), "rect": (32, 32)},
        "重做视频处理": {"class_size": ("size-8",), "rect": (32, 32)},
    },
    "shot-breakdown/play-bgm": {"播放 BGM": {"class_size": ("size-6",), "rect": (13, 13)}},
}

# 不该被改 inert 的 hover 目标 —— 改了就说明「批量修死控件」误伤了真控件
HOVER_TARGET_PROBE = "subtitle-erase/help (误报嫌疑)"
HOVER_TARGET_SELECTOR = "[data-subtitle-erase-help]"

RECT_TOLERANCE = 3


def walk_facts(node: object):
    """从探针的嵌套返回值里把所有 PROBE_JS 事实记录捞出来。"""
    if isinstance(node, dict):
        if "ariaLabel" in node and "inViewport" in node:
            yield node
        for value in node.values():
            yield from walk_facts(value)
    elif isinstance(node, list):
        for item in node:
            yield from walk_facts(item)


def collect_errors(page: Page) -> dict[str, list[str]]:
    errors: dict[str, list[str]] = {"console": [], "page": []}
    page.on("console", lambda m: m.type == "error" and errors["console"].append(m.text))
    page.on("pageerror", lambda e: errors["page"].append(str(e)))
    return errors


def check_class_size(page: Page, selector: str, tokens: tuple[str, ...]) -> str:
    class_name = page.locator(selector).first.get_attribute("class") or ""
    missing = [t for t in tokens if t not in class_name]
    return "" if not missing else f"尺寸 token 丢失: {missing} (class={class_name[:120]})"


def run() -> dict:
    checks: list[dict[str, object]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport=VIEWPORT)
        errors = collect_errors(page)

        for probe_name, expectations in EXPECTED_INERT.items():
            result = REACH.PROBES[probe_name](page)
            facts = list(walk_facts(result))

            # 断言 1: 防假零 —— 走不到就是红, 不是「跳过」
            if REACH.SKIPPED in result:
                add(
                    f"{probe_name}:reachable",
                    False,
                    f"没走到这个面, 按 360 的规矩判红而不是跳过: {result[REACH.SKIPPED]}",
                )
                for label in expectations:
                    add(f"{probe_name}:{label}:inert", False, "面板没打开, 无法验证")
                continue
            add(f"{probe_name}:reachable", True, f"采到 {len(facts)} 个控件")

            by_label: dict[str, list[dict]] = {}
            for fact in facts:
                by_label.setdefault(str(fact.get("ariaLabel")), []).append(fact)

            for label, spec in expectations.items():
                seen = by_label.get(label, [])
                # 断言 1 的下界: 该面至少要有一个这个控件
                if not seen:
                    add(f"{probe_name}:{label}:present", False, "面打开了但控件不存在")
                    continue
                add(f"{probe_name}:{label}:present", True, f"找到 {len(seen)} 个")
                for fact in seen:
                    where = f"{probe_name}/{label}@{fact['rect']['x']},{fact['rect']['y']}"
                    # 断言: 可见且在视口内 —— 渲染了但用户看不到, 等于没修
                    add(
                        f"{where}:in-viewport",
                        bool(fact["visible"]) and bool(fact["inViewport"]),
                        f"visible={fact['visible']} inViewport={fact['inViewport']} rect={fact['rect']}",
                    )
                    # 断言 2: 惰性自证三件套
                    add(
                        f"{where}:inert",
                        fact["inert"] == "true",
                        f"data-inert={fact['inert']!r}",
                    )
                    add(
                        f"{where}:title",
                        bool(fact["title"]) and str(fact["title"]).strip() != "",
                        f"title={fact['title']!r}",
                    )
                    add(
                        f"{where}:cursor",
                        fact["cursor"] == "default",
                        f"cursor={fact['cursor']!r}",
                    )
                    # 不落 disabled / aria-disabled: Playwright is_disabled() 会
                    # 把它当禁用, 且撞既有门禁
                    add(
                        f"{where}:not-disabled",
                        fact["disabled"] is False,
                        f"disabled={fact['disabled']}",
                    )
                    # 断言 2 的一半: 悬停骗人反馈必须去掉。
                    # **逐实例查**: 「收藏」在特效库里有 4 个实例, 用全局
                    # querySelector 只会看到第一个 —— 4 次断言会得到 4 个相同结论,
                    # 「只有 3 个带 hover」这种漏检就被吃掉了。返回逐个布尔。
                    hovers = page.evaluate(
                        """(sel) => Array.from(document.querySelectorAll(sel))
                            .map((el) => /\\bhover:/.test(el.className))""",
                        f'[aria-label="{label}"]',
                    )
                    add(
                        f"{where}:class-has-no-hover",
                        bool(hovers) and not any(hovers),
                        f"{len(hovers)} 个实例, className 含 hover: 的 = {hovers}",
                    )
                    # 断言 3: 几何未变
                    selector = f'[aria-label="{label}"]'
                    size_err = check_class_size(page, selector, spec["class_size"])
                    add(f"{where}:size-token-kept", not size_err, size_err)
                    want_w, want_h = spec["rect"]
                    got_w, got_h = fact["rect"]["w"], fact["rect"]["h"]
                    geom_ok = (
                        abs(got_w - want_w) <= RECT_TOLERANCE
                        and abs(got_h - want_h) <= RECT_TOLERANCE
                    )
                    add(
                        f"{where}:rect-unchanged",
                        geom_ok,
                        f"实测 {got_w}x{got_h}, 期望 {want_w}x{want_h} (容差 ±{RECT_TOLERANCE}px)",
                    )

            # 断言 5: 对照组别被误伤 —— 同工具条上真能用的控件行为不变
            if probe_name == "video-toolbar/undo-redo":
                expand = by_label.get("展开视频", [])
                if not expand:
                    add("control-group:expand-present", False, "对照组「展开视频」不见了")
                else:
                    add("control-group:expand-present", True, "")
                    add(
                        "control-group:expand-not-inert",
                        all(f["inert"] is None for f in expand),
                        f"「展开视频」有 handler, 不该被标 inert: {[f['inert'] for f in expand]}",
                    )
                add(
                    "control-group:download-is-anchor",
                    page.locator('a[aria-label="下载视频封面"][download]').count() > 0,
                    "「下载视频封面」应仍是 <a download>",
                )
                # 真点一次「展开视频」, 确认 handler 还活着
                page.locator('button[aria-label="展开视频"]').first.evaluate("(el) => el.click()")
                page.wait_for_timeout(400)
                acted = page.evaluate(
                    """() => {
                      const el = document.querySelector('button[aria-label="展开视频"]');
                      const bar = el?.closest('div');
                      return (bar?.textContent || '').includes('已打开预览');
                    }"""
                )
                add(
                    "control-group:expand-still-works",
                    bool(acted),
                    "点了「展开视频」应出现「已打开预览」反馈",
                )

        # 断言 4: 反向断言 —— 能用的 hover 控件没被改坏
        hover_result = REACH.PROBES[HOVER_TARGET_PROBE](page)
        if REACH.SKIPPED in hover_result:
            add("hover-target:reachable", False, f"没走到去字幕说明: {hover_result[REACH.SKIPPED]}")
        else:
            add("hover-target:reachable", True, "")
            facts = list(walk_facts(hover_result))
            help_facts = [f for f in facts if f["inert"] is not None]
            add(
                "hover-target:not-marked-inert",
                not help_facts,
                f"「查看框选去字幕说明」是有行为的 hover 目标, 不该被标 inert: "
                f"{[f['ariaLabel'] for f in help_facts]}",
            )
            tip = hover_result.get("tooltipProbe", {})  # type: ignore[union-attr]
            add(
                "hover-target:tooltip-still-works",
                bool(tip.get("visible")),
                f"说明浮层应仍能悬停弹出, 实测 {json.dumps(tip, ensure_ascii=False)[:160]}",
            )
            add(
                "hover-target:button-has-no-title-gate",
                page.locator(HOVER_TARGET_SELECTOR).count() > 0,
                "控件本身不该被改",
            )

        AUDIT.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(AUDIT.parent / "verify-last-probe.png"))
        browser.close()

    # 断言 6: 源码普查里非 hoverTarget 的候选, 必须**只落在**「够不着」的只读白名单里。
    #
    # Batch 368 更新: 原来这里是「必须为 0」, 因为 367 的普查口径只收
    # 「自称可点」(有 aria-label / data-testid / role=button) 的按钮 ——
    # 而 batch 368 证明那个口径**漏掉了两类**: 没有任何标记的裸 `<button>`,
    # 以及有 `data-*` 但不是 `data-testid` 的。口径放宽后普查如实多报出 5 个。
    #
    # 这 5 个是**够不着**的, 不是骗人的(定性见 batch368 README):
    # - `CameraConfigDialog.tsx` 4 处: **全仓库无人 import**, 连 director 也没引用,
    #   是死代码, 用户永远看不到;
    # - `VideoGenerationPanel.tsx` 的 pill 兜底分支: 5 个 pill 全有 `hasMenu` 或
    #   专门分支, 这行是给不存在的 label 留的, 当前不可达。
    #
    # 断言的**意图**没变 ——「不许出现会骗用户的死控件」; 变的是口径更准之后,
    # 「够不着」与「骗人」必须分开记。白名单按**文件+行**写死, 不按文件名开口子:
    # 新增一个候选就红, 少一个也红。
    ALLOWED_UNREACHABLE = {
        ("CameraConfigDialog.tsx", 102),
        ("CameraConfigDialog.tsx", 140),
        ("CameraConfigDialog.tsx", 178),
        ("CameraConfigDialog.tsx", 216),
        ("VideoGenerationPanel.tsx", 499),
    }
    residual: list[str] = []
    unreachable: list[str] = []
    for path in sorted((ROOT / "src" / "components").rglob("*.tsx")):
        rel = path.relative_to(ROOT / "src" / "components")
        if CENSUS.is_cross_line(rel):
            continue
        for hit in CENSUS.scan(path):
            if hit["hoverTarget"]:
                continue
            key = (str(rel), int(hit["line"]))
            token = f"{rel}:{hit['line']} {hit['aria']!r}"
            if key in ALLOWED_UNREACHABLE:
                unreachable.append(token)
            else:
                residual.append(token)
    add(
        "source-census:no-reachable-dead-buttons",
        not residual,
        f"普查残余应只落在只读白名单 {sorted(ALLOWED_UNREACHABLE)}; 实际多出: {residual}",
    )
    # 白名单也不能被无声删掉 —— 少一个说明有人「顺手清理」了死代码, 那要人来定
    add(
        "source-census:unreachable-allowlist-intact",
        len(unreachable) == len(ALLOWED_UNREACHABLE),
        f"白名单 {len(ALLOWED_UNREACHABLE)} 项, 实际命中 {len(unreachable)} 项: {unreachable}",
    )

    noisy = [
        e
        for e in list(errors["console"]) + list(errors["page"])
        if "ERR_ABORTED" not in e and "WebSocket" not in e
    ]
    return {"checks": checks, "errors": errors, "noisy": noisy}


def report(audit: dict) -> int:
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    failed = [c for c in audit["checks"] if not c["ok"]]
    if failed:
        print(f"Batch 367: {len(audit['checks']) - len(failed)}/{len(audit['checks'])} checks passed")
        print("FAILED:", json.dumps(failed, ensure_ascii=False, indent=1))
    if audit["noisy"]:
        print("DIAGNOSTICS:", json.dumps(audit["noisy"][:5], ensure_ascii=False, indent=1))
    if failed or audit["noisy"]:
        return 1
    print(
        f"Batch 367 verification passed: {len(audit['checks'])} checks. "
        "Seven dead affordances now declare themselves inert (data-inert + title + "
        "cursor:default, no hover), geometry and copy unchanged; the working "
        "'view frame-erase help' hover target was left alone and still reveals its tooltip."
    )
    return 0


def main() -> int:
    return report(run())


if __name__ == "__main__":
    raise SystemExit(main())
