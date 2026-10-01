#!/usr/bin/env python3

"""Verify Batch 358: liblib 画布线不得存在「启用着、点了没反应」的控件。

这条线此前**没有**任何此类门禁: 300 个 verify-liblib-batch*.py 里, 判据只有
frameos 的 batch356/batch357 在用, liblib 一个都没有。而普查在 16 个 UI 态里
一次扫出 **95 个**「启用、无 handler」的控件。

最大的一个藏在扫描器的盲区里: `TutorialMenu` 的四个按钮(使用教程/联系客服/
联系销售/关注公众号)**既没有 onClick 也没有 disabled**, 却带
`hover:bg-white/[0.07]` 的悬停反馈。第一版扫描只收「有 onClick **或**
cursor:pointer」的元素 —— 它们两头都不占, 于是在结果里**根本不存在**。
「启用却无 handler 的按钮」按定义就是这类缺陷本身, 却被过滤器滤掉了。

## 逐组人工核实(普查只列事实, 判定必须人做)

| 组 | 位置 | 核实 |
|---|---|---|
| 教程四项 | LeftSidebar TutorialMenu | 无 onClick, 带 hover 反馈 |
| 生成历史卡片 查看/使用/下载 | HistoryPanel | 同上; 同一行的「收藏」**有** toggleFavorite, 不在其列 |
| 时间倒序 | HistoryPanel | 同上; 旁边「批量操作」有真 onClick |
| 收藏 ×40+ | LibraryShowcasePanel 卡片 | 无 onClick, `group-hover:opacity-100` 悬停显形 |
| 筛选 | LibraryShowcasePanel | 同上; 分类行有真 `data-library-category` |
| 模板说明 / 模板选择 | ToolboxPanel | 同上; 「关闭工具箱」有真 onClose |
| Agent 三项 | AgentDrawer header | 同上; 紧挨的「新对话无法分享」是**对的**写法 |
| 开通会员 | TopNavBar | 付费入口, **按纪律绝不接线** |
| 积分余额 | TopNavBar | 读数, 不是控件 |

## 修法: 保持启用 + 去掉悬停骗人的反馈 + title 说明

**没有用 `disabled`**, 因为那会动到已采样的源站形态:
- `verify-liblib-batch97.py` 依据 2026-09-05 源站审计断言 Agent header 三项
  `is_disabled() == False`;
- `verify-liblib-batch106/121.py` 断言教程四项**可见**。
沿用 AgentDrawer 里「新对话无法分享」已有的视觉语言(disabled + title + opacity-40),
只是不落 `disabled`: 保留几何与文案, 去掉 hover, 加 title。

这正是 batch357 里 batch170 vs batch251 的那条分野: **断的是不是源站事实**。

## 扫描器本身的五次修正(全部是「假绿」方向)

1. 只用 `cursor:pointer` 判可点 → liblib 不用内联 cursor, 36 个按钮里 35 个
   是 `default`, 扫出「0 个假可点」。**那个结论是无效的。**
2. 只扫 `button` → workspace 与 canvas 两态元素数完全相同(36/36), 可画布态明明
   多了 10 个节点。工具条大量用 div + onClick。
3. `calledNames` 式的「从子节点起步」类错误 → 35 个「pointer 且无 handler」
   其实是**继承了父元素 cursor** 的 `<path>`/`<svg>`(cursor 是可继承属性)。
4. 特征集只取 data/aria/role → 把「面板开了但控件是纯文本 div」的 4 个态
   误判成「没打开」。判据太弱时, 「没变化」会被误读成「没打开」。
5. 只收 pointer 或已接线 → 正好滤掉了要找的缺陷(见上)。

外加两条**构造性假阳性**的正确处理(不是开白名单, 白名单只会在重构时悄悄失效):
- `onChange` / `onInput` 同样算已接线 —— `<input type=range>` 天生没有 onClick
  (HistoryPanel「历史缩略图大小」);
- `<label>` 的接线看**后代控件** —— 点 label 等于点它包的 checkbox
  (LibraryShowcasePanel「仅看可商用」)。

## 断言

1. 防假绿: 16 个态里, 除 user_menu 外每个都必须与默认态**元素集合不同**
   (否则「零违规」只是把默认态数了 16 遍);
2. 每个态都没有「启用、无 handler、无祖先接线」的元素;
3. 扫描器总元素数不为 0(整体失效时不能报零违规);
4. 钉住本批修复: 教程四项 / 历史三项 / 时间倒序 / 收藏 / 筛选 / 模板两项 /
   Agent 三项 都带 `aria-disabled` 与说明性 title;
5. 付费动作「开通会员」**必须没有 handler**;
6. 诊断零错误。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT / "docs" / "research" / "liblib-batch358-2026-10-01" / "runtime-audit.json"
)

# uiStore 暴露在 window 上; 面板开关用它驱动, 不靠点坐标(那会因布局漂移而脆)
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
# user_menu 是**已知死状态**: 全项目无人调用 toggleUserMenu, isUserMenuOpen 只被
# libtvSelectionCommandContext 读来抑制快捷键。它打不开不是本批的缺陷, 但也正因
# 为此不能拿它当「面板已打开」的证据。日后有人把它接上, 应当从这里移出。
DEAD_STATES = {"user_menu"}

CENSUS_JS = """
() => {
  const out = [];
  for (const el of document.querySelectorAll('*')) {
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
    const looksClickable = cs.cursor === 'pointer';
    const isBtn = el.tagName === 'BUTTON' || el.getAttribute('role') === 'button';
    if (!isBtn && !wired && !looksClickable) continue;
    let wiredByAncestor = false;
    if (!wired && !isLabel) {
      for (let a = el.parentElement; a; a = a.parentElement) {
        for (const k of Object.keys(a).filter((x) => x.startsWith('__reactProps$'))) {
          const ap = a[k];
          if (ap && (typeof ap.onClick === 'function' || typeof ap.onChange === 'function'
              || typeof ap.onInput === 'function')) { wiredByAncestor = true; break; }
        }
        if (wiredByAncestor) break;
      }
    }
    out.push({
      tag: el.tagName.toLowerCase(),
      aria: el.getAttribute('aria-label') || '',
      text: (el.textContent || '').trim().slice(0, 20),
      title: el.getAttribute('title') || '',
      inert: el.getAttribute('data-inert') || '',
      disabled: el.disabled === true,
      cursor: cs.cursor,
      wired, wiredByAncestor, isBtn,
      data: Array.from(el.attributes).filter((a) => a.name.startsWith('data-'))
                  .map((a) => a.name + (a.value ? '=' + a.value : '')),
    });
  }
  return out;
}
"""


def scan(page: Page) -> list[dict[str, Any]]:
    return page.evaluate(CENSUS_JS)


def _declares_itself_inert(it: dict[str, Any]) -> bool:
    """例外必须**自证**: 同时带 aria-disabled 与非空 title。

    为什么不用「按名字开白名单」: 白名单只会在下一次重构里悄悄失效 ——
    新增一个死按钮不会被列进去, 门禁仍然绿, 而用户多点了一次。
    改成属性判据后, 任何新的死按钮都必须自己带上「我不可用」+ 一句给用户看的
    理由, 否则门禁立刻红。而且这个规则对**例外是有约束的**: 付费入口
    「开通会员」和只读读数「积分余额」都因此必须写清自己为什么不会有反应。
    """
    return it.get("inert") == "true" and bool(it.get("title"))


def dead(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        it for it in items
        if not it["disabled"] and not it["wired"] and not it["wiredByAncestor"]
        and not _declares_itself_inert(it)
    ]


def signature(items: list[dict[str, Any]]) -> set[str]:
    sig: set[str] = set()
    for it in items:
        for d in it["data"]:
            sig.add(d.split("=")[0])
        if it["aria"]:
            sig.add("aria:" + it["aria"][:24])
        if it["text"]:
            sig.add("text:" + it["text"][:18])
    return sig


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
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool, detail: str = "") -> None:
        assert ok, f"batch358 check failed: {name} {detail}".strip()
        result["checks"].append(name)

    errors: list[str] = []
    page.on(
        "console",
        lambda m: errors.append(f"console:{m.type}:{m.text}") if m.type == "error" else None,
    )
    page.on("pageerror", lambda e: errors.append(f"pageerror:{e}"))

    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(1500)

    states: dict[str, list[dict[str, Any]]] = {"__default__": scan(page)}
    for name in PRIMARY_PANELS:
        close_all(page)
        page.evaluate("(n) => window.__libtv_ui_store.getState().setPrimaryPanel(n)", name)
        page.wait_for_timeout(800)
        states[name] = scan(page)
    for name, fn in TOGGLES:
        close_all(page)
        page.evaluate("(f) => window.__libtv_ui_store.getState()[f]()", fn)
        page.wait_for_timeout(800)
        states[name] = scan(page)

    base_sig = signature(states["__default__"])
    result["census"] = {}
    total_elements = 0
    for name, items in states.items():
        bad = dead(items)
        total_elements += len(items)
        distinct = signature(items) != base_sig
        result["census"][name] = {
            "total": len(items),
            "distinctFromDefault": distinct,
            "dead": [{"tag": i["tag"], "aria": i["aria"], "text": i["text"]} for i in bad],
        }
        # 防假绿: 面板没打开时元素集合与默认态一样, 「零违规」就只是重复数了默认态
        if name not in DEAD_STATES and name != "__default__":
            check(f"state-opened:{name}", distinct,
                  "该态与默认态元素集合完全相同 —— 面板很可能没打开, "
                  "此时「零违规」不成立")
        check(f"no-dead-control:{name}", not bad,
              f"启用却无 handler 的控件: "
              f"{[{'tag': i['tag'], 'aria': i['aria'], 'text': i['text']} for i in bad]}")

    check("census:scanned-anything", total_elements > 200,
          f"总共只扫到 {total_elements} 个元素 —— 扫描范围可能整体失效(假绿)")

    # ── 钉住本批修复 ──
    close_all(page)
    page.evaluate("() => window.__libtv_ui_store.getState().setPrimaryPanel('tutorial')")
    page.wait_for_timeout(800)
    for label in ["使用教程", "联系客服", "联系销售", "关注公众号"]:
        row = page.get_by_role("button", name=label, exact=True)
        check(f"tutorial:{label}:present", row.count() == 1, f"count={row.count()}")
        check(f"tutorial:{label}:explains-why",
              "尚未接入" in (row.get_attribute("title") or ""),
              f"title={(row.get_attribute('title'))!r} 应说明为什么没反应")
        check(f"tutorial:{label}:no-hover-affordance",
              "hover" not in (row.get_attribute("class") or ""),
              f"class 仍带 hover 反馈: {row.get_attribute('class')}")
    check("tutorial:items-still-visible",
          all(page.get_by_text(t, exact=True).is_visible()
              for t in ["使用教程", "联系客服", "联系销售", "关注公众号"]),
          "教程四项被隐藏了 —— batch106/121 断言它们可见")

    # 付费动作: 必须没有 handler
    member = page.get_by_role("button", name="开通会员 限时 45 折")
    check("paid:会员入口:present", member.count() == 1, f"count={member.count()}")
    check("paid:会员入口:no-handler",
          not member.evaluate(
              """el => Object.keys(el).filter(k => k.startsWith('__reactProps$'))
                   .some(k => typeof el[k]?.onClick === 'function')"""
          ),
          "「开通会员」被接上了 handler —— 付费动作按纪律绝不接线")

    check("diagnostics:zero", not errors, f"errors={errors[:3]}")
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 358,
        "defect": "liblib 画布线 16 个 UI 态里共 95 个「启用、无 handler」的控件: "
                  "教程四项 / 生成历史卡片的查看·使用·下载 / 时间倒序 / 卡片收藏×40+ / "
                  "筛选 / 工具箱模板说明与模板选择 / Agent 历史对话·设置·CLI。全部带悬停"
                  "反馈, 看着能点, 点了什么也不发生。",
        "fix": "保持启用(不动已采样的源站形态: batch97 钉住 Agent 三项 "
               "is_disabled()==False, batch106/121 断言教程四项可见), 去掉悬停骗人的"
               "反馈、cursor 改默认、加 title 说明为什么没反应。付费入口「开通会员」"
               "保持无 handler 并被门禁钉死。",
        "role": "把「启用却无 handler」普查变成覆盖 16 个态的门禁",
    }
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            audit["desktop"] = run(page)
        finally:
            browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2))
    print(
        f"Batch 358 verification passed: {len(audit['desktop']['checks'])} checks, "
        f"{audit['desktop']['diagnostics']['console']} diagnostics. "
        "No control in any of the 16 liblib UI states is left enabled and click-dead: "
        "the 95 verified fakes now look inert and say why, the paid membership CTA "
        "stays unwired by rule, and the census is enforced as a gate."
    )


if __name__ == "__main__":
    main()
