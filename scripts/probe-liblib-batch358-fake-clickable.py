#!/usr/bin/env python3
"""liblib 画布线「假可点按钮」运行时普查探针 (Batch 358 侦察)

判据与 frameos batch356 一致, 但那套判据在 liblib 这条线上**一个都没有** ——
300 个 verify-liblib-batch*.py 里没有一条查「可点外观却没有 handler」。

静态扫描先给出 56 个 `<button>` 没有 onClick 也没有 disabled, 但那**不能直接当
结论**: 样式大多来自共享的 btnStyle 常量, 静态看不见计算后的 cursor, 而且其中
必然混着装饰性元素。Batch 355/356 的教训是「普查结果必须逐个人工核实」。

所以判据只能落在运行时:
  looksClickable = 计算样式 cursor === 'pointer'   (显式可点; CSS 默认 auto/default 不算)
  disabled       = 元素禁用
  hasOnClick     = React props 上挂了函数   (__reactProps$)
三者同时成立 = 呈现为可点、没被禁用、又没有 handler = **假可点**。

用法: python scripts/probe-liblib-batch358-fake-clickable.py [--json]
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
OUT = ROOT / "docs" / "research" / "liblib-batch358-2026-10-01" / "census.json"

CENSUS_JS = """
() => {
  const out = [];
  // 不限 button: 画布这类 UI 大量用 div/span + onClick 做事,
  // 只扫 button 会把**整条工具条**漏掉(实测 workspace 与 canvas 两态的 button
  // 数完全相同 36/36, 但 canvas 态明明多了 10 个节点和整套工具条)。
  // 所以这里扫「所有带 click handler 或呈现为可点」的元素。
  for (const el of document.querySelectorAll('*')) {
    const rk = Object.keys(el).filter((k) => k.startsWith('__reactProps$'));
    let hasOnClick = false;
    // onChange / onInput 同样算「已接线」: <input type=range> 和 checkbox 天生
    // 由 change 驱动, 没有 onClick。两个已核实的假阳性正是这样被扫出来的 ——
    //   HistoryPanel 的「历史缩略图大小」(range + onChange setZoom)
    //   LibraryShowcasePanel 的「仅看可商用」(<label> 包 checkbox + onChange)
    // 正确的修法是**认它**, 不是开白名单: 白名单只会在下次重构时悄悄失效。
    let hasChange = false;
    for (const k of rk) {
      const p = el[k];
      if (!p) continue;
      if (typeof p.onClick === 'function') hasOnClick = true;
      if (typeof p.onChange === 'function' || typeof p.onInput === 'function') hasChange = true;
    }
    // <label> 的可点性**来自它包裹/指向的表单控件**: 点 label 等于点那个
    // checkbox。label 自己没有 onClick 是正常的, 不该算死控件 ——
    // LibraryShowcasePanel 的「仅看可商用」就是这种: <label> 包着
    // <input type=checkbox onChange={setCommercialOnly}>。
    // 所以 label 的接线状态要看后代控件, 不是看自己。
    const isLabel = el.tagName === 'LABEL';
    let labelWired = false;
    if (isLabel) {
      const inner = el.querySelector('input, select, textarea');
      if (inner) {
        const ik = Object.keys(inner).filter((k) => k.startsWith('__reactProps$'));
        for (const k of ik) {
          const ip = inner[k];
          if (!ip) continue;
          if (typeof ip.onClick === 'function' || typeof ip.onChange === 'function'
              || typeof ip.onInput === 'function') labelWired = true;
        }
      }
    }
    const wired = hasOnClick || hasChange || labelWired;
    const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;   // 不可见的不算
    const looksClickable = cs.cursor === 'pointer';
    // ⚠️⚠️ 最大的一个测法缺口, 而且它正好藏住了要找的缺陷。
    //
    // 前几版只收「有 onClick **或** cursor:pointer」的元素。第一版在 tutorial 态
    // 报「面板没打开」, 手工去读代码才发现 LeftSidebar.tsx:81 的 TutorialMenu
    // 渲染了 4 个 **完全没有 onClick、也没 disabled** 的 <button>:
    //     ["使用教程","联系客服","联系销售","关注公众号"].map(label =>
    //       <button className="... hover:bg-white/[0.07]">{label}</button>)
    // 它们有 hover 反馈、没有 cursor、没有 handler —— 前两个条件都不满足,
    // 于是在扫描里**根本不存在**。而「启用却无 handler 的按钮」按定义就是
    // 这类缺陷本身, 却被我的过滤器滤掉了。
    //
    // 所以: **凡是 <button> / [role=button] 一律收**, 不管它长什么样;
    // 对非按钮元素仍然要求 pointer 或有 handler (否则整页每个 div 都进来)。
    const isBtn = el.tagName === 'BUTTON' || el.getAttribute('role') === 'button';
    if (!isBtn && !wired && !looksClickable) continue;
    // ⚠️ `cursor` 是**可继承**属性: 一个没有 handler 的 <svg>/<span> 嵌在可点的
    // 父元素里, 计算样式照样是 pointer。第一版把这类子节点全算成候选 ——
    // 画布态一度冒出 35 个「pointer 且无 handler」, 全都没有 aria / 文案 / data,
    // 正是这个假象。所以: 自己没 handler 时, 若祖先里有挂了 handler 的,
    // 就不算独立控件 (handler 挂在父级是 React 的常规写法)。
    let wiredByAncestor = false;
    if (!wired && !isLabel) {
      for (let a = el.parentElement; a; a = a.parentElement) {
        const ak = Object.keys(a).filter((k) => k.startsWith('__reactProps$'));
        for (const k of ak) {
          const ap = a[k];
          if (ap && typeof ap.onClick === 'function') { wiredByAncestor = true; break; }
        }
        if (wiredByAncestor) break;
      }
    }
    const dlg = el.closest('[role="dialog"]');
    out.push({
      scope: dlg ? (dlg.getAttribute('aria-label') || dlg.className || 'dialog').slice(0, 40) : '',
      tag: el.tagName.toLowerCase(),
      role: el.getAttribute('role') || '',
      aria: el.getAttribute('aria-label') || '',
      text: (el.textContent || '').trim().slice(0, 20),
      title: el.getAttribute('title') || '',
      inert: el.getAttribute('data-inert') || '',
      isBtn,
      disabled: el.disabled === true || el.getAttribute('aria-disabled') === 'true',
      cursor: cs.cursor,
      looksClickable,
      hasOnClick,
      hasChange,
      labelWired,
      wired,
      wiredByAncestor,
      cls: (el.className && el.className.baseVal !== undefined
              ? el.className.baseVal : String(el.className || '')).slice(0, 60),
      w: Math.round(r.width), h: Math.round(r.height),
      data: Array.from(el.attributes).filter((a) => a.name.startsWith('data-'))
                  .map((a) => a.name + (a.value ? '=' + a.value : '')),
    });
  }
  return out;
}
"""


def scan(page: Page) -> list[dict[str, Any]]:
    return page.evaluate(CENSUS_JS)


def fake(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """候选 = 启用着、却没有 handler 的可交互元素。

    ⚠️ 第一版这里要求 `cursor === 'pointer'` 才算候选, 结果 36 个按钮里 35 个是
    `default`, 扫出「0 个假可点」。**那个结论是无效的**: liblib 这条线不用内联
    `cursor: pointer`（frameos 用), 所以「可点外观」这个代理在��条线上根本不成立 ——
    判据不成立时「零命中」既可能是干净, 也可能是压根没测到。
    这正是 Batch 349/352/355 反复教的「先验证测量方法本身」。
    所以这里退一步: 把**所有**启用且无 handler 的元素都列出来, 人工逐个判定。
    cursor 仍然记下来 (作为人工判定时的参考), 但不再当筛子。
    """
    return [
        it for it in items
        if not it["disabled"] and not it["wired"] and not it.get("wiredByAncestor")
        and not _declares_itself_inert(it)
    ]


def _hist(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for it in items:
        out[it[key]] = out.get(it[key], 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


PRIMARY_PANELS = [
    "move", "toolbox", "material", "character", "history",
    "tutorial", "style-library", "effects-library",
]
# uiStore 里除 primary panel 之外的独立开关
TOGGLES = [
    ("asset", "toggleAssetPanel"),
    ("shortcuts", "toggleShortcutsPanel"),
    ("share", "toggleSharePanel"),
    ("agent", "toggleAgent"),
    ("zoom_menu", "toggleZoomMenu"),
    ("add_node", "toggleAddNodePanel"),
    ("user_menu", "toggleUserMenu"),
]


def close_all(page: Page) -> None:
    page.evaluate(
        """() => {
            const ui = window.__libtv_ui_store.getState();
            if (ui.closeAllPanels) ui.closeAllPanels();
            else ui.setPrimaryPanel(null);
        }"""
    )
    page.wait_for_timeout(250)


def run(page: Page) -> dict[str, Any]:
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(1500)

    states: dict[str, Any] = {"__default__": scan(page)}

    for name in PRIMARY_PANELS:
        close_all(page)
        try:
            page.evaluate(
                "(n) => window.__libtv_ui_store.getState().setPrimaryPanel(n)", name
            )
            page.wait_for_timeout(900)
            states[name] = scan(page)
        except Exception as exc:  # noqa: BLE001
            states[name] = {"__error__": str(exc)[:200]}

    for name, fn in TOGGLES:
        close_all(page)
        try:
            page.evaluate(
                "(f) => window.__libtv_ui_store.getState()[f]()", fn
            )
            page.wait_for_timeout(900)
            states[name] = scan(page)
        except Exception as exc:  # noqa: BLE001
            states[name] = {"__error__": str(exc)[:200]}

    out: dict[str, Any] = {"base": BASE_URL, "states": {}}
    base_sig = _signature(states.get("__default__", []))
    for name, raw in states.items():
        if isinstance(raw, dict) and "__error__" in raw:
            out["states"][name] = {"error": raw["__error__"]}
            continue
        items = raw["items"] if isinstance(raw, dict) else raw
        sig = _signature(items)
        new_bits = sorted(sig - base_sig)
        out["states"][name] = {
            "total": len(items),
            # 防假绿: 面板没打开时, 元素集合与默认态**完全一样**,
            # 「0 个启用但无 handler」就只是默认态的结论被重复数了 16 遍。
            # 所以显式记下这个态相对默认态**新增了什么**。
            "distinctFromDefault": sig != base_sig,
            "newHooks": new_bits[:8],
            "cursorHistogram": _hist(items, "cursor"),
            "enabledNoHandler": fake(items),
            "items": items,
        }
    return out


def _signature(items: list[dict[str, Any]]) -> set[str]:
    sig: set[str] = set()
    for it in items:
        for d in it["data"]:
            sig.add(d.split("=")[0])
        if it["aria"]:
            sig.add("aria:" + it["aria"][:24])
        if it["role"]:
            sig.add("role:" + it["role"])
        # 文本也要算进特征。第一版只取 data/aria/role, 结果 move / material /
        # tutorial / user_menu 四个态被判成「与默认态完全相同」——
        # 但它们的元素数确实变了(+2), 说明面板**开了**, 只是里面的控件是
        # 没有 data/aria 的纯文本 div, 特征集看不见。
        # **判据太弱时, 「没变化」会被误读成「没打开」**, 与测量方法失效同源。
        if it["text"]:
            sig.add("text:" + it["text"][:18])
    return sig


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            result = run(page)
        finally:
            browser.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    for name, st in result["states"].items():
        print(f"\n=== {name}: 共 {st['total']} 个可交互元素, "
              f"{len(st['enabledNoHandler'])} 个启用但无 handler ===")
        is_base = name == "__default__"
        flag = ""
        if not is_base and not st.get("distinctFromDefault"):
            flag = "   ⚠️ 与默认态完全相同(面板可能没打开)"
        elif is_base:
            flag = "   (基线态)"
        print(f"    cursor 分布: {st['cursorHistogram']}{flag}")
        if st.get("newHooks"):
            print(f"    相对默认态新增: {st['newHooks'][:5]}")
        for it in st["enabledNoHandler"]:
            print(f"  <{it['tag']}> aria={it['aria']!r} text={it['text']!r} "
                  f"scope={it['scope']!r} cursor={it['cursor']} "
                  f"cls={it['cls'][:34]!r} data={it['data'][:2]}")
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
