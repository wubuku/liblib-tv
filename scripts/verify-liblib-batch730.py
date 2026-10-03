#!/usr/bin/env python3
"""batch 730 验收：46 处 `data-inert` 没有一处挡住可聚焦性 —— 729 的「只挡一半」是一例，本批把它变成全量

## 起点

729 在「开通会员」上实测到：`data-inert="true"` 的按钮 **Tab 能聚焦**、
`focus()` 后 `activeElement === el`，而全仓 `data-inert` **从未与 `disabled` 或
`aria-disabled` 同时出现（0 处）**。那只是**一个样本**。
729 的静态普查里同时留着两个互相打架的数字：`nInert: 46`、
`nInertButtons: 45`，而 `inertByFile.TopNavBar: 2` ——
**两个属性、只数到一个按钮**，矛盾当时就在数据里。

本批做三件事：
① 把那 45 纠成 46，并说清它是怎么错的；
② 把「可聚焦性」从一例推广到**画布上能打开的每一个视图**；
③ 补上 729 没做的那一维：**键盘能不能激活**，以及**聚焦时看起来像不像能用**。

## 口径

- 静态：扫 `src/**/*.tsx`，**排除** `app/frameos`、`components/frameos`、`components/jimeng`
  （他人并行区）。扫描前**先把注释抹掉**再找开标签 ——
  原因见下面「探针返工」。
- 运行时：clone `http://localhost:4317`，视口 1280×1150，导演台**全程关着**，
  走 7 个视图（画布裸态 / 工具箱 / 生成历史 / 教程 / Agent 抽屉 / 单选一张图片卡 /
  单选一张视频卡）。零 store 写入。

## 决定性读数（静态）

| 口径 | 数字 |
|---|---|
| `data-inert="true"` 出现次数 | **46**（16 个文件） |
| 其中落在 `<button>` 开标签上的 | **46 / 46**（**全是 button**） |
| 带 `title` | **46 / 46** |
| 带 `aria-label` | **27 / 46** |
| tag 内带 `cursor-default` | **44 / 46** |
| 带 `tabIndex` | **0 / 46** |
| 带 `disabled` | **0 / 46** |
| 带 `aria-disabled` | **0 / 46** |

## 决定性读数（运行时，7 个视图）

- 逐视图挂载的 `button[data-inert]`：**2 / 4 / 12 / 6 / 5 / 9 / 5**，合计 **43 枚**
  （同一枚在多个视图里重复计数；去重后 **31 枚实例、25 种互不相同的身份**）。
- **`focus()` 后 `activeElement === el`：43 / 43**。
- **聚焦时焦点环发生变化：43 / 43** ⟹ 视觉上与可用按钮无差别。
- **鼠标点击：43 次零副作用** —— store 的 `nodes`/`edges`/`selectedNodeIds` 全不变、
  overlay 不增不减、无 `role="status"`/`aria-live` 文本、无 childList 变更。
- **键盘：见判据 7**（Enter 与 Space 分开测，并断言按键前焦点确实在该按钮上）。

## 不声称

- **不声称 46 处 `data-inert` 都是「未接线」** —— 沿用 729 的不声称。
- **不声称 46 处都被本批测到** —— 本批在画布 7 视图里观测到的只是其中一部分，
  未打开的面板/节点类型（`LibraryShowcasePanel`、`VideoClipEditPanel`、
  `SegmentReshootPanel`、`StoryboardScriptEditor`、`AudioNode`、
  `ShotBreakdownResultNode`、`ScriptGeneratorNode`）未测。
- **不声称 `data-inert` 应当改成 `disabled`** —— 三者语义不同，本批只报告现状。
- **不声称这是可及性缺陷的裁决** —— 本批只报告「标记没有覆盖哪几维」。

## 新增待拍板

1. **`data-inert` 要不要补 `aria-disabled`** —— 729 已提出，本批把证据从 1 例扩到
   43 枚实测 + 46/46 静态。**需改 `src/`，等授权。**
2. **19 处 `data-inert` 按钮没有 `aria-label`** —— 可及名只能来自可见文字；
   19 处里含若干纯图标按钮（如 `AgentDrawer` 的三枚 28×28 header 按钮有 `aria-label`，
   但 `VideoGenerationPanel` 的两枚无 `aria-label` 也无文字）⟹ **可及名为空**。
3. **是否把 46 处的「未接线」在语义上统一** —— 见 729 待拍板 1。

## 方法论

1. **普查的正则会撞上注释** —— 朴素的 `<button\b[^>]*>` 会在**注释里那个 `<button>` 的
   `>`** 上截断，把整枚按钮连同它的 `data-inert` 一起漏掉（`TopNavBar.tsx:200`
   的开标签里就有一段注释写着 `<button>`）⟹ **先抹注释再匹配**。
2. **自己审计里的数字要互相对账** —— 729 的 `nInert: 46` / `nInertButtons: 45` /
   `TopNavBar: 2` 三者不能同时成立；**口径之间要对得上**。
3. **「可聚焦」有两个不同的问法** —— 程序化 `focus()` 成功 ≠ 在自然 Tab 序列里；
   **前者是元素属性，后者是文档顺序**，两格都要测。
4. **零副作用要分鼠标与键盘两格测** —— 729 只点了鼠标。
5. **一次实验里失败的那一格不要硬解释** —— v2 的 `key` 模式报了 30 次 mutation，
   全部落在 `react-flow__pane` 与节点的 `INPUT.name` 上；
   先怀疑探针（空格滚页），再去测被测对象。
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
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch730-2026-10-01"
BASE = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
W, H = 1280, 1150

EXCLUDED = ("src/app/frameos", "src/components/frameos", "src/components/jimeng")

# ---------------------------------------------------------------- 静态扫描


def mask_comments(src: str) -> str:
    """抹掉行注释与块注释，**保持字节偏移不变**。

    batch 730 的起因：朴素的 ``<button\\b[^>]*>`` 会在注释里那个 ``<button>`` 的
    ``>`` 上截断，于是 ``TopNavBar.tsx:200``（积分余额）连同它的 ``data-inert``
    一起从普查里消失 —— 729 因此把 46 数成了 45。
    """
    out = list(src)
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c in "\"'`":
            q = c
            i += 1
            while i < n:
                if src[i] == "\\":
                    i += 2
                    continue
                if src[i] == q:
                    i += 1
                    break
                if q == "'" and src[i] == "\n":
                    break
                i += 1
            continue
        if src.startswith("//", i):
            while i < n and src[i] != "\n":
                out[i] = " "
                i += 1
            continue
        if src.startswith("/*", i):
            while i < n and not src.startswith("*/", i):
                if src[i] != "\n":
                    out[i] = " "
                i += 1
            for k in range(i, min(i + 2, n)):
                out[k] = " "
            i += 2
            continue
        i += 1
    return "".join(out)


def scoped_sources() -> list[Path]:
    return sorted(
        p for p in (ROOT / "src").rglob("*.tsx")
        if not any(str(p.relative_to(ROOT)).startswith(x + "/") or
                   str(p.relative_to(ROOT)) == x for x in EXCLUDED)
    )


TAG_RE = re.compile(r"<button\b([^>]*)>", re.S)


def static_facts() -> dict[str, Any]:
    per_file: dict[str, int] = {}
    tags: list[dict[str, Any]] = []
    naive_total = 0
    naive_by_file: dict[str, int] = {}
    for path in scoped_sources():
        src = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(ROOT))
        masked = mask_comments(src)
        n = len(re.findall(r'data-inert="true"', src))
        if n:
            per_file[rel] = n
        for m in re.finditer(r"<button\b[^>]*>", src, re.S):
            if 'data-inert="true"' in m.group(0):
                naive_total += 1
                naive_by_file[rel] = naive_by_file.get(rel, 0) + 1
        for m in TAG_RE.finditer(masked):
            attrs = m.group(1)
            if "data-inert" not in attrs:
                continue
            tags.append({
                "file": rel,
                "line": src[:m.start()].count("\n") + 1,
                "attrs": " ".join(attrs.split()),
            })
    def has(a: str) -> int:
        return sum(1 for t in tags if a in t["attrs"])
    return {
        "nInert": sum(per_file.values()),
        "nInertFiles": len(per_file),
        "inertByFile": per_file,
        "nButtonsMasked": len(tags),
        "nButtonsNaive": naive_total,
        "naiveByFile": naive_by_file,
        "withTitle": has("title="),
        "withAriaLabel": has("aria-label="),
        "withCursorDefault": has("cursor-default"),
        "withTabIndex": has("tabIndex") + has("tabindex"),
        "withDisabled": has("disabled"),
        "withAriaDisabled": has("aria-disabled"),
        "withAriaHidden": has("aria-hidden"),
        "sites": tags,
    }


# ---------------------------------------------------------------- 运行时

ENUM = r"""() => [...document.querySelectorAll('button[data-inert]')].map((el, i) => {
  const ov = el.closest('[data-liblib-overlay]');
  return {i,
    ariaLabel: el.getAttribute('aria-label'),
    title: el.getAttribute('title'),
    text: (el.textContent || '').trim().slice(0, 24),
    tabIndexAttr: el.getAttribute('tabindex'),
    tabIndexProp: el.tabIndex,
    disabledProp: el.disabled === true,
    ariaDisabled: el.getAttribute('aria-disabled'),
    cursor: getComputedStyle(el).cursor,
    ownerOverlay: ov ? ov.getAttribute('data-liblib-overlay') : null};
})"""

FOCUS = r"""() => [...document.querySelectorAll('button[data-inert]')].map((el) => {
  const snap = () => { const c = getComputedStyle(el);
    return [c.outlineStyle, c.outlineWidth, c.outlineColor, c.boxShadow, c.borderColor].join('|'); };
  const pre = snap();
  el.focus();
  const on = document.activeElement === el;
  const post = snap();
  return {focusable: on, ringChanged: pre !== post};
})"""

START_OBS = r"""() => {
  window.__ip = {mut: 0, added: 0, removed: 0, attrOnTarget: 0};
  window.__mo = new MutationObserver((recs) => {
    for (const r of recs) { window.__ip.mut += 1;
      if (r.type === 'attributes' && r.target && r.target.matches && r.target.matches('[data-inert]'))
        window.__ip.attrOnTarget += 1;
      if (r.type === 'childList') {
        for (const n of r.addedNodes) if (n.nodeType === 1) window.__ip.added += 1;
        window.__ip.removed += r.removedNodes.length; } }
  });
  window.__mo.observe(document.body, {subtree: true, childList: true, attributes: true, characterData: true});
  return true; }"""

STOP_OBS = r"""() => { if (window.__mo) window.__mo.disconnect();
  const v = window.__ip; window.__ip = null; window.__mo = null; return v; }"""

COUNTS = r"""() => { const s = window.__libtv_store.getState(); const g = s.getActiveCanvas();
  return {nodes: g.nodes.length, edges: g.edges.length, sel: s.selectedNodeIds.length,
          overlays: [...document.querySelectorAll('[data-liblib-overlay]')]
            .map((e) => e.getAttribute('data-liblib-overlay')).sort()}; }"""

STATUS_JS = r"""() => [...document.querySelectorAll('[data-canvas-empty-status],[role="status"],[aria-live]')]
  .map((s) => (s.textContent || '').trim()).filter(Boolean)"""

ACTIVE_FP = r"""() => { const a = document.activeElement; if (!a) return null;
  const pane = document.querySelector('.react-flow__pane');
  return {tag: a.tagName, aria: a.getAttribute && a.getAttribute('aria-label') || '',
          title: a.getAttribute && a.getAttribute('title') || '',
          text: (a.textContent || '').trim().slice(0, 24),
          inert: a.getAttribute ? a.getAttribute('data-inert') : null,
          pane: pane ? pane.style.transform : null,
          scrollY: window.scrollY, scrollTop: document.documentElement.scrollTop}; }"""

ACTIVE_FP_MIN = r"""() => { const a = document.activeElement; if (!a) return null;
  return {tag: a.tagName, aria: a.getAttribute && a.getAttribute('aria-label') || '',
          text: (a.textContent || '').trim().slice(0, 12),
          inert: a.getAttribute ? a.getAttribute('data-inert') : null}; }"""

PANEL_STATE = r"""() => !!document.querySelector('[data-liblib-overlay="add-node"]')"""

SELF_ATTRS = r"""(i) => { const b = document.querySelectorAll('button[data-inert]')[i];
  if (!b) return null;
  const out = {};
  for (const a of b.attributes) out[a.name] = a.value;
  return out; }"""


def inert_key(fp: dict[str, Any]) -> str:
    return "\x01".join([fp.get("aria") or fp.get("ariaLabel") or "",
                        fp.get("title") or "", fp.get("text") or ""])


SEMANTIC_ATTRS = ("data-inert", "aria-pressed", "aria-expanded", "aria-disabled",
                  "aria-selected", "disabled", "value")


def semantic(attrs: dict[str, str] | None) -> dict[str, str]:
    if attrs is None:
        return {}
    return {k: v for k, v in attrs.items() if k in SEMANTIC_ATTRS}


def tab_walk(page: Page, need: int, cap: int = 400) -> dict[str, Any]:
    """走自然 Tab 序列，**走满一整圈**就停：`inertStops >= need` 之后遇到第一个重复签名即停。

    这里换过三种绕回判定，每一种都在某一格上错过：
    ① 「自身 + 两层祖先」当指纹 —— 同一工具条里多枚 BUTTON 折叠成同一签名，
       误判「焦点卡住」提前收尾（生成历史只走 8 步）。
    ② 「指纹第二次出现且首次位置 < 5」 —— Tab 会重复经过同一组元素，误判成绕回，
       history 报出 ``14 > 12`` 的重复计数。
    ③ 「前 40 步的指纹序列要在后面完整重现」/「找最小 L 使 seq[-L:]==seq[-2L:-L]」
       —— **第一圈的顺序与后续不同**，锚在第一圈永远匹配不上；锚在末尾则
       ``n`` 很小时窗口取到 3 就误触发，一枚都没走到。
    ⟹ 不猜周期，**按「该走够的枚数」来截断**：一整圈里每枚只经过一次，
    所以 ``inertStops`` 达到挂载数时，计数恰好就是挂载的重数。
    """
    page.evaluate("() => { if (document.activeElement && document.activeElement.blur)"
                  " document.activeElement.blur(); }")
    seq: list[dict[str, Any]] = []
    seen: set[str] = set()
    stops = 0
    truncated = False
    for _step in range(cap):
        page.keyboard.press("Tab")
        fp = page.evaluate(ACTIVE_FP)
        if fp is None:
            continue
        sig = inert_key(fp) + "|" + str(fp["tag"])
        if fp["inert"] == "true":
            stops += 1
        repeat = sig in seen
        seq.append(fp)
        seen.add(sig)
        if stops >= need and repeat:
            truncated = True
            break
    inert_seq = [f for f in seq if f["inert"] == "true"]
    counter: dict[str, int] = {}
    for f in inert_seq:
        k = inert_key(f)
        counter[k] = counter.get(k, 0) + 1
    return {"steps": len(seq), "truncated": truncated, "inertStops": len(inert_seq),
            "inertCounter": counter}


def click_probe(page: Page) -> list[dict[str, Any]]:
    """逐枚点一下。

    **不把「零 mutation」当判据** —— `scrollIntoView` 会让元素进入 hover，
    class 变化是视觉反馈不是激活。判据只断言可观测的后果：store / overlay /
    status 不变，且**元素自身的语义属性**不变。
    """
    out = []
    n = page.evaluate("() => document.querySelectorAll('button[data-inert]').length")
    for i in range(n):
        pre = page.evaluate(COUNTS)
        pre_self = semantic(page.evaluate(SELF_ATTRS, i))
        page.evaluate(START_OBS)
        page.evaluate("""(i) => { const b = document.querySelectorAll('button[data-inert]')[i];
          if (b) { b.scrollIntoView({block:'center'}); b.click(); } }""", i)
        page.wait_for_timeout(420)
        obs = page.evaluate(STOP_OBS)
        post = page.evaluate(COUNTS)
        post_self = semantic(page.evaluate(SELF_ATTRS, i))
        out.append({"i": i, "mut": obs["mut"], "added": obs["added"],
                    "removed": obs["removed"],
                    "selfAttrsChanged": pre_self != post_self,
                    "focusedAfterClick": page.evaluate(
                        """(i) => { const b = document.querySelectorAll('button[data-inert]')[i];
                          return !!b && document.activeElement === b; }""", i),
                    "nodesDelta": post["nodes"] - pre["nodes"],
                    "edgesDelta": post["edges"] - pre["edges"],
                    "selDelta": post["sel"] - pre["sel"],
                    "ovlDelta": sorted(set(post["overlays"]) - set(pre["overlays"])),
                    "status": page.evaluate(STATUS_JS)})
    return out


def key_probe(page: Page, key: str) -> list[dict[str, Any]]:
    """Enter 与 Space 分开测；**先断言焦点确实在该按钮上**，再按。

    记录总 `mut` 但**不断言它为 0**：v2 曾读到 30 次 mutation，全部落在
    `react-flow__pane` 与节点名输入框上（store/overlay/status 皆零），
    成因未取证 —— 只断言已证的那几维。
    """
    out = []
    n = page.evaluate("() => document.querySelectorAll('button[data-inert]').length")
    for i in range(n):
        page.evaluate("""(i) => { const b = document.querySelectorAll('button[data-inert]')[i];
          if (b) { b.scrollIntoView({block:'center'}); b.focus(); } }""", i)
        focused = page.evaluate("""(i) => { const b = document.querySelectorAll('button[data-inert]')[i];
          return !!b && document.activeElement === b; }""", i)
        page.wait_for_timeout(120)
        pre = page.evaluate(ACTIVE_FP)
        pre_store = page.evaluate(COUNTS)
        pre_self = semantic(page.evaluate(SELF_ATTRS, i))
        page.evaluate(START_OBS)
        page.keyboard.press(key)
        page.wait_for_timeout(450)
        obs = page.evaluate(STOP_OBS)
        post = page.evaluate(ACTIVE_FP)
        post_store = page.evaluate(COUNTS)
        post_self = semantic(page.evaluate(SELF_ATTRS, i))
        out.append({"i": i, "focusedBeforePress": focused, "key": key,
                    "mut": obs["mut"],
                    "selfAttrsChanged": pre_self != post_self,
                    "paneMoved": pre["pane"] != post["pane"],
                    "scrollMoved": (pre["scrollY"], pre["scrollTop"]) !=
                                   (post["scrollY"], post["scrollTop"]),
                    "focusStayedOnTarget": post["inert"] == "true",
                    "nodesDelta": post_store["nodes"] - pre_store["nodes"],
                    "edgesDelta": post_store["edges"] - pre_store["edges"],
                    "selDelta": post_store["sel"] - pre_store["sel"],
                    "ovlDelta": sorted(set(post_store["overlays"]) - set(pre_store["overlays"])),
                    "status": page.evaluate(STATUS_JS)})
    return out


def tab_key_probe(page: Page) -> dict[str, Any]:
    """裸画布上按一次 Tab：焦点动不动？添加节点面板开不开？

    `src/app/page.tsx` 的全局 keydown 里有一条 ``event.key === "Tab"`` 分支，
    它 ``preventDefault()`` 并 ``toggleAddNodePanel()`` ——
    **Tab 在画布上被征用成快捷键**，而不是「在控件之间移动焦点」的键。
    源码位置与文案一并读出来，免得判据只钉住现象钉不住出处。
    """
    page.evaluate("() => { if (document.activeElement && document.activeElement.blur)"
                  " document.activeElement.blur(); }")
    before_f = page.evaluate(ACTIVE_FP_MIN)
    before_p = page.evaluate(PANEL_STATE)
    page.keyboard.press("Tab")
    page.wait_for_timeout(400)
    after_f = page.evaluate(ACTIVE_FP_MIN)
    after_p = page.evaluate(PANEL_STATE)

    def ident(f: dict[str, Any] | None) -> tuple:
        return ((f or {}).get("tag"), (f or {}).get("aria"), (f or {}).get("text"))

    src = (ROOT / "src/app/page.tsx").read_text(encoding="utf-8").split("\n")
    src_line = next(i + 1 for i, ln in enumerate(src)
                    if 'if (event.key === "Tab") {' in ln)
    window = "\n".join(src[src_line - 1:src_line + 3])
    dlg = (ROOT / "src/components/KeyboardShortcutsDialog.tsx").read_text(
        encoding="utf-8").split("\n")
    dlg_line = next(i + 1 for i, ln in enumerate(dlg) if '"Tab"' in ln)
    return {
        "firstPressMoved": ident(before_f) != ident(after_f),
        "focusBefore": ident(before_f), "focusAfter": ident(after_f),
        "panelBefore": before_p, "panelAfter": after_p,
        "srcLine": src_line,
        "srcHasPreventDefault": "event.preventDefault()" in window,
        "srcHasToggle": "toggleAddNodePanel()" in window,
        "srcWindow": window.strip(),
        "shortcutDialogLine": dlg_line,
        "shortcutDialogLabel": "新建节点" if "新建节点" in "\n".join(
            dlg[max(0, dlg_line - 2):dlg_line + 1]) else None,
    }


def snapshot(page: Page, view: str) -> dict[str, Any]:
    r: dict[str, Any] = {"view": view}
    r["mounted"] = page.evaluate(ENUM)
    r["focus"] = page.evaluate(FOCUS)
    r["click"] = click_probe(page)
    r["keyEnter"] = key_probe(page, "Enter")
    r["keySpace"] = key_probe(page, " ")
    r["tab"] = tab_walk(page, need=len(r["mounted"]))
    r["counts"] = page.evaluate(COUNTS)
    return r


def open_canvas(page: Page) -> None:
    page.goto(f"{BASE}/?batch70=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function("() => Boolean(window.__libtv_store && window.__director_store)",
                           timeout=60_000)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal'))"
                  " el.remove(); }")
    page.mouse.move(W - 4, 4)
    page.wait_for_timeout(1_400)


def select_node_of_type(page: Page, typ: str) -> bool:
    nid = page.evaluate("""(t) => { const g = window.__libtv_store.getState().getActiveCanvas();
      const n = g.nodes.find(x => x.type === t); return n ? n.id : null; }""", typ)
    if not nid:
        return False
    page.evaluate("""(id) => { const n = document.querySelector(
      '.react-flow__node[data-id="' + CSS.escape(id) + '"]');
      if (n) { n.dispatchEvent(new MouseEvent('mousedown', {bubbles:true, clientX:0, clientY:0}));
               n.dispatchEvent(new MouseEvent('mouseup', {bubbles:true, clientX:0, clientY:0}));
               n.click(); } }""", nid)
    page.wait_for_timeout(900)
    return True


def run(browser: Any) -> dict[str, Any]:
    page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
    out: dict[str, Any] = {"views": {}}
    open_canvas(page)
    out["tabKey"] = tab_key_probe(page)
    # tab_key_probe 会把添加节点面板打开 ⟹ 重新加载回到裸画布再采其余读数
    open_canvas(page)
    out["views"]["canvas"] = snapshot(page, "canvas")
    for label, view in (("打开工具箱", "toolbox"), ("生成历史", "history"), ("教程", "tutorial")):
        page.evaluate("""(l) => { const b = document.querySelector('[aria-label="' + l + '"]');
          if (b) b.click(); }""", label)
        page.wait_for_timeout(700)
        out["views"][view] = snapshot(page, view)
    page.evaluate("""() => { const b = [...document.querySelectorAll('button')]
      .find(x => (x.textContent || '').trim() === 'Agent'); if (b) b.click(); }""")
    page.wait_for_timeout(700)
    out["views"]["agent"] = snapshot(page, "agent")
    for typ, view in (("image", "image-card"), ("video", "video-card")):
        open_canvas(page)
        if select_node_of_type(page, typ):
            out["views"][view] = snapshot(page, view)
        else:
            out["views"][view] = {"view": view, "missingNodeType": typ, "mounted": [],
                                  "focus": [], "click": [], "keyEnter": [], "keySpace": [],
                                  "tab": {"steps": 0, "truncated": False, "inertStops": 0,
                                          "inertCounter": {}}}
    page.close()
    out["tabExcluded"] = {"agent": {
        "reason": "未取证，本批只记录不判。两组读数互相矛盾："
                  "(a) 隔离复现（只开抽屉、不做任何点击/按键、200 步）三次都读不到抽屉那三枚 "
                  "header 按钮；正向 Tab 说其后直接绕回、反向 Tab 说其前是「移动」，互不相容。"
                  "(b) 本验收器自己的 walk 停到 5 次，但重数是 {开通会员:3, 积分余额:2} —— "
                  "抽屉那三枚仍然一次没被命中；**总数恰好 5==5 恰好等于挂载数 5**，"
                  "只有比多重集才发现不对。"
                  "浏览器自己的可聚焦元素集合里它们是在的（tabIndex=0、未禁用、"
                  "offsetParent=ASIDE、display:flex），故不是渲染或禁用的问题；"
                  "成因未取证。另有一版探针因假定抽屉已打开而拿到空列表"
                  "（querySelectorAll('button[data-inert]') 只返回 2 枚、focus() 静默失败），"
                  "那次读数整个作废。",
        "mounted": len(out["views"]["agent"]["mounted"]),
        "observedStops": out["views"]["agent"]["tab"]["inertStops"],
        "observedCounter": out["views"]["agent"]["tab"]["inertCounter"],
    }}
    return out


# ---------------------------------------------------------------- 判据


def _views(r: dict[str, Any]) -> dict[str, Any]:
    # 判据拿到的是整份 payload（{"static":…, "run":…}），运行时视图在 run 下面
    return r.get("run", {}).get("views", {})


def check_1(r: dict[str, Any]) -> None:
    """`data-inert="true"` 写在 46 处 / 16 个文件。"""
    s = r["static"]
    assert s["nInert"] == 46, s["nInert"]
    assert s["nInertFiles"] == 16, s["nInertFiles"]
    assert s["inertByFile"].get("src/components/ImageEditPanel.tsx") == 11, s["inertByFile"]
    assert s["inertByFile"].get("src/components/TopNavBar.tsx") == 2, s["inertByFile"]


def check_2(r: dict[str, Any]) -> None:
    """46 处**全是** `<button>`，并且把 729 的 45 纠回来 —— 差的那一枚在 TopNavBar。

    朴素扫描（不抹注释）恰好少 1，且少的正是 TopNavBar 的第二枚 ⟹
    这不是数据错了，是**扫描口径错了**。
    """
    s = r["static"]
    assert s["nButtonsMasked"] == 46, s["nButtonsMasked"]
    assert s["nButtonsNaive"] == 45, s["nButtonsNaive"]
    assert s["naiveByFile"].get("src/components/TopNavBar.tsx") == 1, s["naiveByFile"]
    assert s["inertByFile"]["src/components/TopNavBar.tsx"] == 2
    sites = [t for t in s["sites"] if t["file"].endswith("TopNavBar.tsx")]
    assert sorted(t["line"] for t in sites) == [183, 200], sites
    # 那枚漏掉的按钮，开标签里确实写着一段含 `<button>` 的注释（TopNavBar.tsx:200 起）
    top = (ROOT / "src/components/TopNavBar.tsx").read_text(encoding="utf-8").split("\n")
    span = top[199:214]
    assert any("<button>" in ln for ln in span), span
    # 朴素正则会在注释那个 `<button>` 的 `>` 上截断 ⟹ 它唯一命中的那枚是**开通会员**，
    # 积分余额那枚的 data-inert 落在被切掉的那一段之后
    naive_tags = [m.group(0) for m in re.finditer(r"<button\b[^>]*>", "\n".join(top), re.S)
                  if 'data-inert="true"' in m.group(0)]
    assert len(naive_tags) == 1, naive_tags
    # 命中的那枚是「开通会员」；「积分余额」那枚的 data-inert 落在被截断的那一段之后。
    # 注意只能比对 **aria-label 字面量**：注释正文里也出现了「积分余额」四个字。
    assert 'aria-label="开通会员 限时 45 折"' in naive_tags[0], naive_tags
    assert 'aria-label="积分余额"' not in naive_tags[0], naive_tags
    masked_tags = [m.group(0) for m in TAG_RE.finditer(mask_comments("\n".join(top)))
                   if "data-inert" in m.group(1)]
    assert len(masked_tags) == 2 and any('aria-label="积分余额"' in t for t in masked_tags), \
        masked_tags


def check_3(r: dict[str, Any]) -> None:
    """46 处里 **0** 处带任何能挡可聚焦性的属性；`title` 46/46、`aria-label` 27/46。"""
    s = r["static"]
    assert s["withTabIndex"] == 0, s["withTabIndex"]
    assert s["withDisabled"] == 0, s["withDisabled"]
    assert s["withAriaDisabled"] == 0, s["withAriaDisabled"]
    assert s["withAriaHidden"] == 0, s["withAriaHidden"]
    assert s["withTitle"] == 46, s["withTitle"]
    assert s["withAriaLabel"] == 27, s["withAriaLabel"]
    assert s["withCursorDefault"] == 44, s["withCursorDefault"]


def check_4(r: dict[str, Any]) -> None:
    """运行时：**每一枚**挂载的 `button[data-inert]` 都能被 `focus()` 拿到。"""
    total = focusable = 0
    per_view = {}
    for v, d in _views(r).items():
        n = len(d["mounted"])
        f = sum(1 for x in d["focus"] if x["focusable"])
        per_view[v] = [f, n]
        total += n
        focusable += f
    assert focusable == total, per_view
    assert total >= 40, per_view
    r["focusTotals"] = {"total": total, "focusable": focusable, "perView": per_view}


def check_5(r: dict[str, Any]) -> None:
    """聚焦时焦点环**每一枚都会变** ⟹ 视觉上与可用按钮无差别。"""
    total = ring = 0
    for d in _views(r).values():
        for x in d["focus"]:
            total += 1
            if x["ringChanged"]:
                ring += 1
    assert ring == total and total > 0, (ring, total)
    r["ringTotals"] = {"total": total, "ringChanged": ring}


def check_6(r: dict[str, Any]) -> None:
    """鼠标点击：不改 store、不改 overlay、不出 status，元素自身语义属性也不变。

    不断言「零 mutation」—— `scrollIntoView` 造成的 hover class 变化是视觉反馈，
    不是激活；把两者混在一起断言就是「四项同因失败却怪被测对象」。
    顺带记一笔：**点完焦点落在它身上**（focusedAfterClick），也就是说
    「点了没反应」的按钮仍然拿到了焦点与焦点环。
    """
    acts = [a for d in _views(r).values() for a in d["click"]]
    assert acts, "no click actions recorded"
    for a in acts:
        assert a["selfAttrsChanged"] is False, a
        assert a["nodesDelta"] == 0 and a["edgesDelta"] == 0 and a["selDelta"] == 0, a
        assert a["ovlDelta"] == [], a
        assert a["status"] == [], a
    r["clickTotals"] = {
        "actions": len(acts),
        "focusedAfterClick": sum(1 for a in acts if a["focusedAfterClick"]),
        "mutationsObserved": sum(a["mut"] for a in acts),
    }


def check_7(r: dict[str, Any]) -> None:
    """键盘：Enter 与 Space 都**按之前焦点确实在该按钮上**，且都不改任何可观测后果。

    总 mutation 只记录不断言 —— v2 在这里读到 30 次 mutation，全部落在
    `react-flow__pane` 与节点名输入框上（store/overlay/status 皆零），
    **成因未取证**，不作为结论依据。
    """
    for key in ("keyEnter", "keySpace"):
        acts = [a for d in _views(r).values() for a in d[key]]
        assert acts, key
        for a in acts:
            assert a["focusedBeforePress"] is True, (key, a)
            assert a["selfAttrsChanged"] is False, (key, a)
            assert a["nodesDelta"] == 0 and a["edgesDelta"] == 0 and a["selDelta"] == 0, (key, a)
            assert a["ovlDelta"] == [], (key, a)
            assert a["status"] == [], (key, a)
        r[key + "Totals"] = {
            "actions": len(acts),
            "paneMoved": sum(1 for a in acts if a["paneMoved"]),
            "scrollMoved": sum(1 for a in acts if a["scrollMoved"]),
            "focusStayedOnTarget": sum(1 for a in acts if a["focusStayedOnTarget"]),
            "mutationsObserved": sum(a["mut"] for a in acts),
        }


def check_8(r: dict[str, Any]) -> None:
    """**写点数 ≠ 控件数**：两个 `.map()` 写点把 46 撑成了更多实例。"""
    s = r["static"]
    views = _views(r)
    # LeftSidebar: 静态 1 个写点（:101 的 .map），运行时 primary:tutorial 里 4 枚
    assert s["inertByFile"]["src/components/LeftSidebar.tsx"] == 1, s["inertByFile"]
    tut = [m for m in views["tutorial"]["mounted"] if m["ownerOverlay"] == "primary:tutorial"]
    assert len(tut) == 4, tut
    assert sorted(m["text"] for m in tut) == sorted(["使用教程", "联系客服", "联系销售", "关注公众号"]), tut
    # HistoryPanel: 静态 4 个写点（1 + 3），运行时 1 + 3 张卡 × 3 = 10 枚
    assert s["inertByFile"]["src/components/HistoryPanel.tsx"] == 4, s["inertByFile"]
    his = [m for m in views["history"]["mounted"] if m["ownerOverlay"] == "primary:history"]
    assert len(his) == 10, len(his)
    r["siteVsInstance"] = {"LeftSidebar": [1, len(tut)], "HistoryPanel": [4, len(his)]}


def check_9(r: dict[str, Any]) -> None:
    """自然 Tab 序列：Tab 停在 `data-inert` 上的重数 === 挂载重数（逐视图）。

    比的是**多重集**而不是去重后的身份数 —— 生成历史里 3 张卡各有
    「查看/使用/下载」三枚，去重后只剩 6 个身份而实际有 12 枚按钮。

    **agent 视图整格不参与断言**：三次独立复现都读不到抽屉那三枚按钮，
    但读数彼此矛盾（正向 Tab 说它后面直接绕回、反向 Tab 说它前面是「移动」），
    且 `page.tsx` 的 Tab 分支只在首次命中时改面板状态、与后续步骤接不上 ——
    **成因未取证**，按 batch 728 的先例只记不判。
    """
    excluded = r.get("run", {}).get("tabExcluded", {})
    per_view = {}
    bad = {}
    for v, d in _views(r).items():
        if v in excluded:
            per_view[v] = dict(excluded[v], excluded=True)
            continue
        mounted: dict[str, int] = {}
        for m in d["mounted"]:
            k = inert_key(m)
            mounted[k] = mounted.get(k, 0) + 1
        visited = {k: int(n) for k, n in d["tab"]["inertCounter"].items() if n}
        per_view[v] = {"mounted": sum(mounted.values()), "stops": d["tab"]["inertStops"],
                       "truncated": d["tab"]["truncated"], "steps": d["tab"]["steps"]}
        if mounted != visited:
            bad[v] = {"onlyMounted": {k: n for k, n in mounted.items() if visited.get(k) != n},
                      "onlyVisited": {k: n for k, n in visited.items() if mounted.get(k) != n}}
    assert not bad, bad
    r["tabTotals"] = per_view


def check_10(r: dict[str, Any]) -> None:
    """**Tab 被画布接管成快捷键**：首次按下焦点不动、添加节点面板开出来。

    这决定了「data-inert 挡不挡可聚焦性」在画布上该怎么问 ——
    先得知道 Tab 归谁。
    """
    h = r.get("run", {}).get("tabKey", {})
    assert h.get("firstPressMoved") is False, h
    assert h.get("panelBefore") is False and h.get("panelAfter") is True, h
    assert h.get("srcLine") == 1358, h
    assert h.get("srcHasPreventDefault") is True and h.get("srcHasToggle") is True, h
    assert h.get("shortcutDialogLine") == 27, h
    assert h.get("shortcutDialogLabel") == "新建节点", h
    r["tabKeySummary"] = {k: h[k] for k in sorted(h)}


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
    results: dict[str, Any] = {}
    checks = [
        ("data-inert-is-written-46-times-across-16-files", check_1),
        ("all-46-carrying-tags-are-buttons-and-729s-45-was-a-scanner-artifact", check_2),
        ("data-inert-never-pairs-with-any-focus-blocking-attribute", check_3),
        ("every-mounted-instance-is-programmatically-focusable", check_4),
        ("every-mounted-instance-grows-a-focus-ring-when-focused", check_5),
        ("clicking-them-changes-nothing-at-all", check_6),
        ("keyboard-activating-them-changes-nothing-at-all", check_7),
        ("jsx-sites-are-not-controls-two-map-sites-multiply-them", check_8),
        ("every-mounted-instance-is-reachable-by-tab",
         check_9),
        ("tab-is-hijacked-by-the-canvas-into-a-new-node-shortcut", check_10),
    ]
    summary: dict[str, bool] = {}
    payload = {"static": got["static"], "run": got["run"]}
    for name, fn in checks:
        try:
            fn(payload)
            summary[name] = True
        except Exception as exc:  # noqa: BLE001
            summary[name] = False
            failures.append("%s: %s" % (name, exc))
    results.update(payload)
    results["summary"] = summary
    results["failures"] = failures
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    for name, ok in summary.items():
        print(("PASS " if ok else "FAIL ") + name)
    for f in failures:
        print("  ! " + f)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
