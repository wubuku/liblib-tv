#!/usr/bin/env python3
"""liblib 节点编辑面「交互谎言」双类普查探针 (Batch 359 侦察)

Batch 358 普查的是**画布外框**的 16 个态(工具条、面板、抽屉)。节点一被选中,
浮出来的是另一整片界面: 图片节点的浮动工具条(十来个动作)、图片编辑面板、
标注模式工具条、视频片段节点的编辑面板……**这片面一次都没普查过**,
而 frameos batch 350 那个「裁剪宽高静默丢弃输入」就正是在节点级编辑态里。

两类同时查:
  ① 静默丢弃输入: 启用、无 readonly/disabled、又无 onChange/onInput;
  ② 点了没反应:   启用、无 handler、也没祖先接线、也没自证惰性
     (判据与 batch358 一致, 例外须带 data-inert + title)。

用法: python scripts/probe_liblib_batch359_node_surfaces.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
OUT = ROOT / "docs" / "research" / "liblib-batch359-2026-10-01" / "node-census.json"

# 画布外框的 UI 态清单(与 verify-liblib-batch358 一致), 门禁要一起查输入控件
PRIMARY_PANELS = [
    "move", "toolbox", "material", "character", "history",
    "tutorial", "style-library", "effects-library",
]
TOGGLES = [
    ("asset", "toggleAssetPanel"),
    ("shortcuts", "toggleShortcutsPanel"),
    ("share", "toggleSharePanel"),
    ("agent", "toggleAgent"),
    ("zoom_menu", "toggleZoomMenu"),
    ("add_node", "toggleAddNodePanel"),
    ("user_menu", "toggleUserMenu"),
]
DEAD_STATES = {"user_menu"}   # toggleUserMenu 全项目无人调用, 已知死状态

# 扫描器(两合一): 收「输入控件」与「可交互元素」两类
SCAN_JS = """
() => {
  const out = { inputs: [], controls: [] };
  for (const el of document.querySelectorAll('input, textarea, [contenteditable="true"]')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    const rk = Object.keys(el).filter((k) => k.startsWith('__reactProps$'));
    let onChange = false, onInput = false;
    for (const k of rk) {
      const p = el[k];
      if (!p) continue;
      if (typeof p.onChange === 'function') onChange = true;
      if (typeof p.onInput === 'function') onInput = true;
    }
    out.inputs.push({
      tag: el.tagName.toLowerCase(), type: el.getAttribute('type') || '',
      placeholder: (el.getAttribute('placeholder') || '').slice(0, 26),
      aria: el.getAttribute('aria-label') || '',
      value: (el.value !== undefined ? String(el.value) : '').slice(0, 18),
      disabled: el.disabled === true, readOnly: el.readOnly === true,
      ariaDisabled: el.getAttribute('aria-disabled') || '',
      inert: el.getAttribute('data-inert') || '',
      title: el.getAttribute('title') || '',
      onChange, onInput,
      data: Array.from(el.attributes).filter((a) => a.name.startsWith('data-') || a.name === 'data-testid')
                  .map((a) => a.name + (a.value ? '=' + a.value : '')),
    });
  }
  for (const el of document.querySelectorAll('button, [role="button"], a[href]')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    const rk = Object.keys(el).filter((k) => k.startsWith('__reactProps$'));
    let hasOnClick = false, hasChange = false;
    for (const k of rk) {
      const p = el[k];
      if (!p) continue;
      if (typeof p.onClick === 'function') hasOnClick = true;
      if (typeof p.onChange === 'function' || typeof p.onInput === 'function') hasChange = true;
    }
    const isLabel = el.tagName === 'LABEL';
    let labelWired = false;
    if (isLabel) {
      const inner = el.querySelector('input, select, textarea');
      if (inner) {
        for (const k of Object.keys(inner).filter((x) => x.startsWith('__reactProps$'))) {
          const ip = inner[k];
          if (ip && (typeof ip.onClick === 'function' || typeof ip.onChange === 'function'
              || typeof ip.onInput === 'function')) labelWired = true;
        }
      }
    }
    const wired = hasOnClick || hasChange || labelWired;
    const cs = getComputedStyle(el);
    // ⚠️ 又踩了 batch358 的第 5 条, 而且是在我自己批评过它之后:
    // 这里写的是「两头都不占就跳过」, 而 Tailwind 下 <button> 的 computed cursor
    // 是 `default` 不是 `pointer` —— 于是**没有 handler 的按钮在判定之前就被丢掉**,
    // 死控件判据根本没有机会触发(变异测试红在了下游的 annotate:opened 上)。
    // 「启用却无 handler 的按钮」按定义就是这类缺陷本身, 不能被过滤器预先滤掉。
    // 所以: 凡是自称控件的元素一律收, 不看 cursor。
    const declaresControl = el.tagName === 'BUTTON'
      || el.getAttribute('role') === 'button'
      || el.hasAttribute('data-testid')
      || el.hasAttribute('aria-label');
    if (!declaresControl && !wired && cs.cursor !== 'pointer') continue;
    // 祖先接线豁免只对**布局容器**成立, 对**自称控件的元素**不成立。
    // 反例(ImageToolbar): 工具条容器上是 `onClick={(e) => e.stopPropagation()}` ——
    // 阻止冒泡, 什么也不做。若无差别豁免, 「自己被摘掉 onClick 的动作按钮」会被
    // 判成已接线, 死控件判据根本不触发。
    let wiredByAncestor = false;
    if (!wired && !isLabel && !declaresControl) {
      for (let a = el.parentElement; a; a = a.parentElement) {
        for (const k of Object.keys(a).filter((x) => x.startsWith('__reactProps$'))) {
          const ap = a[k];
          if (ap && (typeof ap.onClick === 'function' || typeof ap.onChange === 'function'
              || typeof ap.onInput === 'function')) { wiredByAncestor = true; break; }
        }
        if (wiredByAncestor) break;
      }
    }
    out.controls.push({
      tag: el.tagName.toLowerCase(),
      aria: el.getAttribute('aria-label') || '',
      text: (el.textContent || '').trim().slice(0, 18),
      title: el.getAttribute('title') || '',
      inert: el.getAttribute('data-inert') || '',
      ariaDisabled: el.getAttribute('aria-disabled') || '',
      disabled: el.disabled === true,
      cursor: cs.cursor, wired, wiredByAncestor,
      data: Array.from(el.attributes).filter((a) => a.name.startsWith('data-') || a.name === 'data-testid')
                  .map((a) => a.name + (a.value ? '=' + a.value : '')),
    });
  }
  return out;
}
"""


def inert(it: dict[str, Any]) -> bool:
    return it.get("inert") == "true" and bool(it.get("title"))


def classify(snap: dict[str, Any]) -> dict[str, Any]:
    silent = [
        it for it in snap["inputs"]
        if not it["disabled"] and not it["readOnly"] and it["ariaDisabled"] != "true"
        and not it["onChange"] and not it["onInput"]
    ]
    dead = [
        it for it in snap["controls"]
        if not it["disabled"] and not it["wired"] and not it["wiredByAncestor"] and not inert(it)
    ]
    return {
        "inputs": len(snap["inputs"]),
        "controls": len(snap["controls"]),
        "silentDiscard": [
            {"tag": i["tag"], "type": i["type"], "ph": i["placeholder"], "aria": i["aria"]}
            for i in silent
        ],
        "deadControls": [
            {"tag": c["tag"], "aria": c["aria"], "text": c["text"], "data": c["data"][:2]}
            for c in dead
        ],
    }


def close_all(page: Page) -> None:
    page.evaluate(
        """() => { const ui = window.__libtv_ui_store.getState();
                   if (ui.closeAllPanels) ui.closeAllPanels(); }"""
    )
    page.wait_for_timeout(250)


def click_node(page: Page, node_id: str) -> bool:
    loc = page.locator(f'.react-flow__node[data-id="{node_id}"]')
    if loc.count() == 0:
        return False
    # 页面内派发点击: 画布节点可能在视口外(react-flow 的 viewport transform),
    # Playwright 的真实点���会直接抛 "Element is outside of the viewport"。
    # 既有验证器(verify-liblib-batch53 的 click_toolbar_button)也是这么绕的。
    loc.first.evaluate("(el) => el.click()")
    page.wait_for_timeout(700)
    return True


def run(page: Page) -> dict[str, Any]:
    page.goto(BASE_URL, wait_until="networkidle")
    # ⚠️ 必须显式等画布节点出现, 不能只靠固定 sleep。
    # 有一轮 `wait_for_timeout(1500)` 没等到 hydration, node_ids 拿到空数组,
    # 探针「跑完」并报 **0 问题 / 0 死控件** —— 那是**假零**。
    # 普查工具最危险的失败模式不是报错, 是安静地什么都没测。
    page.wait_for_selector(".react-flow__node", timeout=30000)
    page.wait_for_timeout(600)

    states: dict[str, Any] = {}
    states["__default__"] = classify(page.evaluate(SCAN_JS))

    # 找出画布上现有的节点, 按类型挑代表性的
    node_ids = page.evaluate(
        """() => Array.from(document.querySelectorAll('.react-flow__node'))
             .map(n => n.getAttribute('data-id')).filter(Boolean)"""
    )
    states["_nodeIds"] = node_ids
    if not node_ids:
        raise AssertionError("画布上一个节点都没有 —— 探针没测到任何东西, 不能据此报「无问题」")

    for nid in node_ids:
        close_all(page)
        if not click_node(page, nid):
            continue
        snap = page.evaluate(SCAN_JS)
        label = f"node:{nid[:14]}"
        states[label] = classify(snap)
        states[label]["_ids"] = {
            "testids": sorted({
                d.split("=")[1] for c in snap["controls"] for d in c["data"]
                if d.startswith("data-testid=")
            })[:14]
        }
        # 图片节点再进标注模式。
        # ⚠️ 这里踩过一次: 一律用 `el.click()` 页面内派发, 结果**标注模式根本没打开**
        # (该态的 testid 集合是空的, 控件数反而从 ~50 掉到 39 —— 节点工具条没了,
        # 标注工具条没出来)。工具条带 scale transform, 页面内派发点不动它。
        # 照 verify-liblib-batch53 的 open_annotate: 先量盒, 在视口外才退回派发。
        ann = page.locator('[data-testid="image-toolbar-annotate"]')
        if ann.count() > 0:
            try:
                ann.first.click(force=True, timeout=4000)
            except Exception:  # noqa: BLE001
                ann.first.evaluate("(el) => el.click()")
            page.wait_for_timeout(1000)
            # 防假绿: 标注态必须真的出现标注工具条, 否则这一态等于没测
            opened = page.locator("[data-image-annotate-toolbar]").count() > 0
            snap2 = page.evaluate(SCAN_JS)
            st2 = classify(snap2)
            st2["_annotateOpened"] = opened
            states[label + ":annotate"] = st2
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
    return states


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            states = run(page)
        finally:
            browser.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(states, ensure_ascii=False, indent=2))

    tot_s = tot_d = 0
    for name, st in states.items():
        if name.startswith("_"):
            continue
        s, d = st["silentDiscard"], st["deadControls"]
        tot_s += len(s)
        tot_d += len(d)
        tag = (f"  标注工具条已打开={st.get('_annotateOpened')}"
               if ":annotate" in name else "")
        if not s and not d:
            print(f"=== {name}: inputs={st['inputs']} controls={st['controls']}"
                  f" — 无问题{tag}")
            continue
        print(f"\n=== {name}: inputs={st['inputs']} controls={st['controls']}")
        for i in s:
            print(f"   静默丢弃 <{i['tag']} type={i['type']!r}> ph={i['ph']!r} aria={i['aria']!r}")
        for c in d:
            print(f"   点了没反应 <{c['tag']}> aria={c['aria']!r} text={c['text']!r} data={c['data']}")
    print(f"\n合计: 静默丢弃 {tot_s} / 死控件 {tot_d}  ->  {OUT}")


if __name__ == "__main__":
    main()
