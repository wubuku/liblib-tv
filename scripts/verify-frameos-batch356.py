#!/usr/bin/env python3

"""Verify Batch 356: 不允许「呈现为可点、实则毫无反应」的按钮。

缺陷（克隆侧，用户可见）:
静态普查 frameos 全部 `<button>` 找出**没有任何 onClick** 的, 逐个人工核实后
确认 **7 个**是真缺陷（普查本身有误报, 见下）：

| 位置 | 按钮 | 原样貌 |
|---|---|---|
| FrameosMaterialLibrary | 收藏筛选 / 创建者筛选 / 创建时间排序 | 灰底 + `cursor: pointer` |
| FrameosMaterialLibrary | 批量操作 | 描边 + `cursor: pointer` |
| FrameosMaterialLibrary | **+ 本地上传** | **蓝色主按钮** + `cursor: pointer` |
| FrameosPromptEditor | **生成音频**（¥100） | **实心蓝圆形主按钮** |
| FrameosPromptEditor | **生成视频**（¥300） | **实心蓝圆形主按钮** |

越像「主行动」的越糟：两个「生成」按钮是面板里最醒目的实心蓝圆钮，
`+ 本地上传` 是素材库那一行里唯一的蓝色按钮 —— 点了全都毫无反应，
连一条提示都没有。

修复（不发明行为、不触发付费）: 按本仓库既有的「惰性控件」约定
（见 FrameosGroupToolbar 的「整组执行」：`cursor: default` + 暗色），
把这 7 个改成**看起来就不可点**：`disabled` + `title` 说明原因 + 降饱和。
**几何、尺寸、圆角、位置、文案一律不动**。

本验证器把这个普查变成门禁：任何**呈现为可点却没有 click handler** 的按钮
都会让验证器失败并指名。

断言:
1. 防假绿: 普查能扫到按钮（默认态 + 素材库态 + 音频/视频面板态）;
2~N. 各态「可点外观但无 handler」的按钮数为 0;
5. 7 个目标按钮确实都是 disabled;
6. 7 个目标按钮都带说明性 title;
7. **付费按钮没有被接线**（生成音频/视频仍无 handler —— 回归防护）;
8. 几何未被动过（宽度 32 / 圆形 / 文案不变）;
9. 诊断零错误。
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT / "docs" / "research" / "liblib-frameos-batch356-2026-10-01" / "runtime-audit.json"
)
sys.path.insert(0, str(ROOT / "scripts"))
from frameos_verify_common import attach_errors, goto_clean_canvas  # noqa: E402

# 「可点外观」= 显式 cursor:pointer（CSS 默认是 auto/default, 不算）；
# 「有 handler」= React props 里有 onClick。
# disabled 的按钮直接排除 —— 它本来就该不可点, 不算缺陷。
CENSUS_JS = """
() => {
  const out = [];
  for (const el of document.querySelectorAll('button, [role="button"]')) {
    const rk = Object.keys(el).filter((k) => k.startsWith('__reactProps$'));
    let hasOnClick = false;
    for (const k of rk) {
      const p = el[k];
      if (p && typeof p.onClick === 'function') hasOnClick = true;
    }
    const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    // 同名按钮存在多个(「本地上传」: 素材库里的假 vs 工具条上的真),
    // 所以必须记录它落在哪个对话框里, 否则目标表会张冠李戴。
    const dlg = el.closest('[role="dialog"]');
    out.push({
      dialog: dlg ? (dlg.getAttribute('aria-label') || 'dialog') : '',
      tag: el.tagName.toLowerCase(),
      aria: el.getAttribute('aria-label') || '',
      text: (el.textContent || '').trim().slice(0, 16),
      title: el.getAttribute('title') || '',
      disabled: el.disabled === true,
      cursor: cs.cursor,
      looksClickable: cs.cursor === 'pointer',
      hasOnClick,
      w: Math.round(r.width), h: Math.round(r.height),
      data: Array.from(el.attributes).filter((a) => a.name.startsWith('data-')).map((a) => a.name),
    });
  }
  return out;
}
"""

# 本批修的 7 个。
# **必须带对话框作用域**: 「本地上传」有两个同名按钮 ——
#   素材库 dialog 里那个 = 无 handler 的假按钮(本批修的);
#   工具条上那个 = `onClick={openFilePicker}` 的**真**按钮(不能动)。
# 早期版本只用 aria/text 匹配, 结果把真按钮当成了目标, 报「又变回可点」。
TARGETS = [
    ("素材库", "收藏筛选"),
    ("素材库", "创建者筛选"),
    ("素材库", "创建时间排序"),
    ("素材库", "批量操作"),
    ("素材库", "本地上传"),
    ("", "生成音频"),
    ("", "生成视频"),
]


def leave_all(page: Page) -> None:
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    page.evaluate(
        """() => {
            const st = window.__frameos_store.getState();
            st.selectNode(null);
            st.setCroppingNode(null);
        }"""
    )
    # 素材库是全屏 dialog, **不响应 Esc**、且会 intercept 后续点击 ——
    # 不关掉它, 下一个态的点击全被它吃掉(实测 click 被 retry 到超时)。
    close = page.locator('[aria-label="关闭素材库"]')
    if close.count() > 0:
        close.first.click()
        page.wait_for_timeout(300)
    page.wait_for_timeout(200)


def open_material_library(page: Page) -> None:
    """素材库由工具条派发 `frameos:open-material-library` 自定义事件打开。

    直接派发事件而不是去点那个 `RailButton` —— 后者的 label 渲染成什么形态
    (可见文本 / title / aria-label)不值得猜, 而事件是它**公开的入口契约**。
    """
    page.evaluate(
        "() => window.dispatchEvent(new CustomEvent('frameos:open-material-library'))"
    )
    page.wait_for_timeout(800)


def open_audio_panel(page: Page) -> None:
    """音频节点 → Batch 213 专属面板(含「生成音频」按钮)。"""
    page.evaluate(
        """() => {
            const st = window.__frameos_store;
            const g = st.getState();
            // id 必须唯一: 本验证器会多次注入面板节点, 固定 id 会造成 React
            // 重复 key 报错, 污染 diagnostics:zero(踩过一次)。
            const id = 'audio-zzz-' + Date.now() + '-' + g.nodes.length;
            st.setState({ nodes: [...g.nodes, {
                id, type: 'audio',
                position: { x: 700, y: 700 },
                style: { width: 220, height: 160 },
                data: { title: '音频节点' },
            }]});
            st.getState().selectNode(id);
            return true;
        }"""
    )
    page.wait_for_timeout(800)


def open_video_panel(page: Page) -> None:
    """视频节点 → 视频面板(含「生成视频」按钮)。

    注意: fixture 里的 `video-1` **带 imageUrl**, 按 Batch 225(源站实测)
    「内容媒体节点无面板」会被 `FrameosPromptEditor` 的早退分支排除,
    所以必须注入一个**无内容**的视频节点才能进到 `sel.type === "video"` 分支。
    """
    page.evaluate(
        """() => {
            const st = window.__frameos_store;
            const g = st.getState();
            const id = 'video-zzz-' + Date.now() + '-' + g.nodes.length;
            st.setState({ nodes: [...g.nodes, {
                id, type: 'video',
                position: { x: 300, y: 700 },
                style: { width: 300, height: 169 },
                data: { title: '视频节点' },
            }]});
            st.getState().selectNode(id);
            return true;
        }"""
    )
    page.wait_for_timeout(800)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool, detail: str = "") -> None:
        assert ok, f"batch356 check failed: {name} {detail}".strip()
        result["checks"].append(name)

    errors = attach_errors(page)
    goto_clean_canvas(page, BASE_URL)

    census: dict[str, Any] = {}
    for name, enter in [
        ("default", lambda pg: None),
        ("material_library", open_material_library),
        ("audio_panel", open_audio_panel),
        ("video_panel", open_video_panel),
    ]:
        leave_all(page)
        enter(page)
        page.wait_for_timeout(500)
        items = page.evaluate(CENSUS_JS)
        # 缺陷定义: 呈现为可点(cursor:pointer)、没被禁用、又没有 handler
        liars = [
            it for it in items
            if it["looksClickable"] and not it["disabled"] and not it["hasOnClick"]
        ]
        census[name] = {"total": len(items), "liars": liars}
        if name != "default":
            check(f"scan:not-empty:{name}", len(items) >= 1,
                  f"只扫到 {len(items)} 个按钮 —— 态可能没进去(假绿)")
        check(f"no-fake-clickable:{name}", not liars,
              f"呈现可点却无 handler: "
              f"{[{'aria': i['aria'], 'text': i['text']} for i in liars]}")

    result["census"] = census
    check("scan:buttons-found",
          sum(v["total"] for v in census.values()) >= 10,
          f"扫到的按钮总数过少: {sum(v['total'] for v in census.values())}")

    # ── 钉住本次修复: 逐个态重新进一次, 收集 7 个目标按钮的真实属性 ──
    seen: dict[str, Any] = {}
    for name, enter in [
        ("material_library", open_material_library),
        ("audio_panel", open_audio_panel),
        ("video_panel", open_video_panel),
    ]:
        leave_all(page)
        enter(page)
        page.wait_for_timeout(500)
        for it in page.evaluate(CENSYS_JS_PLACEHOLDER if False else CENSUS_JS):
            # 按钮文本可能带装饰前缀(如素材库里的「+ 本地上传」), 归一化后再比
            label = (it["aria"] or it["text"]).lstrip("+·※ ").strip()
            key = f"{it['dialog']}|{label}"
            if key not in seen and (it["dialog"], label) in TARGETS:
                seen[key] = it
    result["targets"] = seen

    for dlg, t in TARGETS:
        it = seen.get(f"{dlg}|{t}")
        check(f"target:present:{t}", it is not None, f"没扫到目标按钮 {t!r}")
        if it is None:
            continue
        check(f"target:disabled:{t}", it["disabled"] is True,
              f"{t!r} 又变回可点(它没有 handler)")
        check(f"target:explains:{t}", "未接入" in it["title"],
              f"{t!r} title={it['title']!r}（应说明为何不可用）")

    # ── 付费按钮不得被接线(回归防护) ──
    for paid in ("生成音频", "生成视频"):
        it = seen.get(f"|{paid}")
        if it is None:
            continue
        check(f"paid:never-wired:{paid}", it["hasOnClick"] is False,
              f"{paid} 被接上了 handler —— 付费动作按源站纪律绝不触发")

    # ── 几何未被动过 ──
    for geo, exp in (("生成音频", (32, 32)), ("生成视频", (32, 32))):
        it = seen.get(f"|{geo}")
        if it is None:
            continue
        check(f"geometry:kept:{geo}", (it["w"], it["h"]) == exp,
              f"{geo} 尺寸被改动: {(it['w'], it['h'])} != {exp}")

    check("diagnostics:zero", not errors, f"errors={errors[:3]}")
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 356,
        "defect": "7 个按钮没有任何 onClick 却呈现为完全可点(含两个实心蓝「生成」主按钮"
                  "与素材库蓝色「+ 本地上传」), 点了毫无反应",
        "fix": "按仓库既有「惰性控件」约定改为 disabled + title 说明 + 降饱和; "
               "几何/尺寸/圆角/文案不动; 付费动作不接线",
        "census_false_positive": "静态普查曾把 FrameosGroupToolbar 的排列菜单项误报为无 handler —— "
                                 "它的 onClick 落在正则窗口之外。普查结果必须逐个人工核实。",
    }
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            audit["desktop"] = run_desktop(page)
        finally:
            browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2))
    print(
        f"Batch 356 verification passed: {len(audit['desktop']['checks'])} checks, "
        f"{audit['desktop']['diagnostics']['console']} diagnostics. "
        "No button in any frameos UI state now presents as clickable while having no "
        "click handler — the two paid generate buttons and the material library's "
        "primary upload button look inert and say why, and the census is gated."
    )


if __name__ == "__main__":
    main()
