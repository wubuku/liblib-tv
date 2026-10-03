#!/usr/bin/env python3
"""batch 731 验收：换一条独立通道读 `data-inert` —— 无障碍树里的 role 与可及名

## 起点

730 用 DOM 通道证明：46 处 `data-inert` **一处都没挡住可聚焦性**（43/43 `focus()`
成功、43/43 聚焦时焦点环变化、Tab 停靠重数 === 挂载重数）。

但 730 的 README 顺手写了一句 **「纯图标按钮会得到空的可及名」**，
并把 `video-card` 里那两枚（既无 `aria-label` 也无可见文字）当成证据。
那句话**没有被测过**，是推断。本批去测它 —— 而且用一条**独立通道**：
不看 DOM 属性，直接读浏览器自己算出来的**无障碍树**（CDP `Accessibility.getPartialAXTree`）。

## 口径

- **静态**：同 730 —— 扫 `src/**/*.tsx`，排除 `app/frameos`/`components/frameos`/
  `components/jimeng`；先抹注释再匹配开标签。
- **运行时**：clone `http://localhost:4317`，1280×1150，导演台**全程关着**，
  同样 7 个视图、同样 43 枚挂载。零 store 写入。
- **无障碍树**：CDP `Accessibility.enable` + 对每个 `button[data-inert]`
  的 `backendNodeId` 取 `getPartialAXTree(fetchRelatives=False)`，
  读它的 `role` / `name` / `ignored` / `ignoredReasons` / `properties`。

## 决定性读数

### ① AX 树逐条复现 730 的 DOM 读数：43 枚全是 `role=button`、`ignored=false`、`focusable=true`

独立通道给出同一结论 ⟹ 730 那格不是探针的错觉。

### ② **AX 树里没有 `disabled`**：未接线与已接线的 `properties` **逐字相同**

`{"focusable": true, "invalid": "false"}` —— 两边都是这个。
⟹ **屏幕阅读器面前，「已接线」和「未接线」是同一种东西**：
role 相同、状态相同、没有任何「这个不能点」的信号。

### ③ 可及名会**兜底到 `title`** ⟹ 推翻 730 的「纯图标按钮可及名为空」

那两枚既无 `aria-label` 又无可见文字的按钮，AX name 是
**「该功能在克隆侧尚未接入」/「该设置在克隆侧尚未接入」** —— 不是空，是 `title`。

⟹ **730 的「纯图标按钮会得到空的可及名」错了**：该说的是
**「可及名会变成失败说明句」**，而且这两条 title 是**泛指**的
（「该功能」「该设置」），连是哪个功能都没说。

### ④ `title` 只在「既无 `aria-label` 又无文字」时才参与命名 —— 其余不受污染

43 枚里 22 种身份，只有 **2 种**的可及名是失败说明句；
其余 20 种的名字是正常功能名（来自 `aria-label` 或可见文字）。
⟹ 「补 `title`」这一步是对的，它兜住了命名；**代价集中在纯图标那一小撮**。

## 不声称

- **不声称静态的 19 处无 `aria-label` 里有多少是纯图标** —— 分类需要求值 JSX 表达式
  （`.map()` 的 `{label}`、`{generationSettings}`、`{mode ?? "默认模式"}`），
  正则分类会把「带文字」的判成「纯图标」（本批实测过），**故不在静态侧分类**。
- **不声称 AX 树等同于真实屏幕阅读器的播报** —— 这里读的是浏览器算出的
  `role`/`name`/`properties`，不是 NVDA/VoiceOver 的实际输出。
- **不声称 46 处 `data-inert` 都是「未接线」** —— 沿用 729。
- **不声称这构成可及性缺陷的裁决** —— 本批只报告「这条通道上留下了什么」。

## 新增待拍板

1. **730 待拍板 2 收窄** —— 原话「纯图标按钮会得到空的可及名」**作废**；
   改成「**可及名会变成失败说明句，且这两条 title 是泛指的**」。
   要不要给纯图标按钮补 `aria-label`（哪怕名字也写成功能名）？**需改 `src/`，等授权。**
2. **43 枚里 0 枚在 AX 树里有 `disabled`** —— 与 730 待拍板 1（补 `aria-disabled`）
   合并：`data-inert` 在**两条通道**上都没留下「不能点」的语义。**需改 `src/`，等授权。**
3. **两条泛指 title 要不要写具体**（「该功能」→「全屏录制」之类）——
   与 729 的「三枚芯片 toast 逐字相同」是同一族问题：**未接线控件给用户的说明彼此无法区分**。

## 方法论

1. **换一个通道复验上一批的结论** —— 730 用 DOM，731 用无障碍树；
   两条通道在 `role`/`focusable` 上逐条吻合，才敢说 730 那格不是错觉。
2. **顺手写下的话也是结论，也要被测** —— 730 的「纯图标按钮会得到空的可及名」
   是推断，本批一测就错 ⟹ **写进 README 的推断要标明它没被测过**。
3. **静态不要分类 JSX 表达式** —— `.map()` 的 `{label}`、`{mode ?? "默认模式"}`
   只有运行时知道；正则分类会把带文字的判成纯图标。**该交给运行时就交给运行时。**
4. **`title` 是兜底，不是命名** —— 有 `aria-label` 或可见文字时 `title` 不参与命名；
   所以「补 `title`」的代价集中在纯图标那一小撮 ⟹ **说「加 title 就有了名字」是不完整的**。
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
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch731-2026-10-01"
BASE = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
W, H = 1280, 1150

sys.path.insert(0, str(ROOT / "scripts"))

ENUM = r"""() => [...document.querySelectorAll('button[data-inert]')].map((el, i) => {
  const ov = el.closest('[data-liblib-overlay]');
  return {i, aria: el.getAttribute('aria-label') || '',
          title: el.getAttribute('title') || '',
          text: (el.textContent || '').trim().slice(0, 24),
          ownerOverlay: ov ? ov.getAttribute('data-liblib-overlay') : null}; })"""

WIRED = r"""(sels) => sels.map(s => { const el = document.querySelector(s);
  if (!el) return {sel: s, missing: true};
  return {sel: s, tag: el.tagName, aria: el.getAttribute('aria-label') || '',
          text: (el.textContent || '').trim().slice(0, 24),
          disabled: el.getAttribute('disabled') !== null,
          ariaDisabled: el.getAttribute('aria-disabled'),
          dataInert: el.getAttribute('data-inert')}; })"""

WIRED_SELECTORS = ['[aria-label="教程"]', '[aria-label="项目菜单"]',
                   '[data-viewport-menu-trigger="zoom"]', '[aria-label="添加节点"]']

FAILURE_NAME = re.compile(r"尚未接入|暂不可用|不提供|无可点操作|clone 不触发|为付费")


def mask_comments(src: str) -> str:
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


EXCLUDED = ("src/app/frameos", "src/components/frameos", "src/components/jimeng")
TAG_RE = re.compile(r"<button\b([^>]*)>", re.S)


def static_facts() -> dict[str, Any]:
    per_file: dict[str, int] = {}
    sites: list[dict[str, Any]] = []
    for path in sorted((ROOT / "src").rglob("*.tsx")):
        rel = str(path.relative_to(ROOT))
        if any(rel == x or rel.startswith(x + "/") for x in EXCLUDED):
            continue
        src = path.read_text(encoding="utf-8")
        masked = mask_comments(src)
        n = len(re.findall(r'data-inert="true"', src))
        if n:
            per_file[rel] = n
        for m in TAG_RE.finditer(masked):
            attrs = m.group(1)
            if "data-inert" not in attrs:
                continue
            # title 的值可能是含嵌套花括号的 JSX 表达式
            # （title={`${label}在克隆侧尚未接入`}），所以只取到空白为止的那一串
            t = re.search(r'title=[^\s>]+', attrs)
            sites.append({
                "file": rel, "line": src[:m.start()].count("\n") + 1,
                "hasAriaLabel": "aria-label=" in attrs,
                # title 可能是 JSX 表达式（如 title={`${label}在克隆侧尚未接入`}），
                # 所以这里只断言**属性在不在**，不去求值它的内容
                "hasTitle": t is not None,
                "titleAttr": t.group(0) if t else None,
            })
    no_aria = [{"file": s["file"], "line": s["line"], "titleAttr": s["titleAttr"]}
               for s in sites if not s["hasAriaLabel"]]
    return {"nInert": sum(per_file.values()), "nInertFiles": len(per_file),
            "inertByFile": per_file, "nSites": len(sites),
            "withAriaLabel": len(sites) - len(no_aria), "withoutAriaLabel": len(no_aria),
            "noAriaLabelSites": no_aria}


def ax_for(cdp: Any, node_ids: list[int]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for nid in node_ids:
        try:
            bid = cdp.send("DOM.describeNode", {"nodeId": nid})["node"]["backendNodeId"]
            tree = cdp.send("Accessibility.getPartialAXTree",
                            {"backendNodeId": bid, "fetchRelatives": False})
        except Exception as exc:  # noqa: BLE001
            out.append({"error": str(exc)[:120]})
            continue
        nodes = tree.get("nodes", [])
        own = next((n for n in nodes if n.get("role")), nodes[0] if nodes else None)
        if own is None:
            out.append({"error": "empty AX tree"})
            continue
        props = {}
        for p in own.get("properties", []) or []:
            props[p.get("name")] = p.get("value", {}).get("value")
        out.append({
            "role": (own.get("role") or {}).get("value"),
            "name": (own.get("name") or {}).get("value"),
            "ignored": own.get("ignored"),
            "ignoredReasons": [r.get("name") for r in (own.get("ignoredReasons") or [])],
            "props": {k: v for k, v in props.items()
                      if k in ("disabled", "focusable", "focused", "hidden", "invalid", "readonly")},
        })
    return out


def collect(page: Page, cdp: Any) -> dict[str, Any]:
    root = cdp.send("DOM.getDocument", {"depth": -1})["root"]["nodeId"]
    ids = cdp.send("DOM.querySelectorAll",
                   {"nodeId": root, "selector": "button[data-inert]"})["nodeIds"]
    elems = page.evaluate(ENUM)
    ax = ax_for(cdp, ids)
    rows = [{**e, "ax": a} for e, a in zip(elems, ax)]
    wired = page.evaluate(WIRED, WIRED_SELECTORS)
    wids: list[int] = []
    for w in wired:
        if w.get("missing"):
            continue
        got = cdp.send("DOM.querySelector", {"nodeId": root, "selector": w["sel"]})
        if got.get("nodeId"):
            wids.append(got["nodeId"])
    wax = ax_for(cdp, wids)
    wmap: dict[str, Any] = {}
    i = 0
    for w in wired:
        if w.get("missing"):
            continue
        wmap[w["sel"]] = {**w, "ax": wax[i]}
        i += 1
    return {"rows": rows, "wired": wmap}


def name_source(row: dict[str, Any]) -> str:
    ax_name = (row["ax"].get("name") or "").strip()
    if row["aria"].strip():
        return "aria-label" if ax_name == row["aria"].strip() else "aria-label?"
    if row["text"].strip():
        return "content" if ax_name == row["text"].strip() else "content?"
    if row["title"].strip():
        return "title" if ax_name == row["title"].strip() else "title?"
    return "empty"


def open_canvas(page: Page) -> None:
    page.goto(f"{BASE}/?batch70=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal'))"
                  " el.remove(); }")
    page.mouse.move(W - 4, 4)
    page.wait_for_timeout(1_400)


def select_node_of_type(page: Page, typ: str) -> None:
    nid = page.evaluate("""(t) => { const g = window.__libtv_store.getState().getActiveCanvas();
      const n = g.nodes.find(x => x.type === t); return n ? n.id : null; }""", typ)
    page.evaluate("""(id) => { const n = document.querySelector(
      '.react-flow__node[data-id="' + CSS.escape(id) + '"]');
      if (n) { n.dispatchEvent(new MouseEvent('mousedown', {bubbles:true, clientX:0, clientY:0}));
               n.dispatchEvent(new MouseEvent('mouseup', {bubbles:true, clientX:0, clientY:0}));
               n.click(); } }""", nid)
    page.wait_for_timeout(900)


def run(browser: Any) -> dict[str, Any]:
    page = browser.new_page(viewport={"width": W, "height": H})
    cdp = page.context.new_cdp_session(page)
    cdp.send("Accessibility.enable")
    out: dict[str, Any] = {"views": {}}
    open_canvas(page)
    for label, view in ((None, "canvas"), ("打开工具箱", "toolbox"),
                        ("生成历史", "history"), ("教程", "tutorial")):
        if label:
            page.evaluate("""(l) => { const b = document.querySelector('[aria-label="' + l + '"]');
              if (b) b.click(); }""", label)
            page.wait_for_timeout(700)
        out["views"][view] = collect(page, cdp)
    page.evaluate("""() => { const b = [...document.querySelectorAll('button')]
      .find(x => (x.textContent || '').trim() === 'Agent'); if (b) b.click(); }""")
    page.wait_for_timeout(700)
    out["views"]["agent"] = collect(page, cdp)
    for typ, view in (("image", "image-card"), ("video", "video-card")):
        open_canvas(page)
        select_node_of_type(page, typ)
        out["views"][view] = collect(page, cdp)
    page.close()
    return out


def _views(r: dict[str, Any]) -> dict[str, Any]:
    return r.get("run", {}).get("views", {})


def _identities(r: dict[str, Any]) -> dict[tuple, dict[str, Any]]:
    """跨视图去重：同一枚按钮在多个视图里出现，只留一份。"""
    ident: dict[tuple, dict[str, Any]] = {}
    for d in _views(r).values():
        for row in d["rows"]:
            key = (row["aria"], row["title"], row["text"])
            if key not in ident:
                ident[key] = row
    return ident


def check_1(r: dict[str, Any]) -> None:
    """静态与 730 同一口径：46 处 / 16 文件，其中 **19 处没有 `aria-label`**。"""
    s = r["static"]
    assert s["nInert"] == 46, s["nInert"]
    assert s["nInertFiles"] == 16, s["nInertFiles"]
    assert s["nSites"] == 46, s["nSites"]
    assert s["withAriaLabel"] == 27, s["withAriaLabel"]
    assert s["withoutAriaLabel"] == 19, s["withoutAriaLabel"]
    assert all(x["titleAttr"] for x in s["noAriaLabelSites"]), \
        [x for x in s["noAriaLabelSites"] if not x["titleAttr"]]


def check_2(r: dict[str, Any]) -> None:
    """AX 树逐条复现 730 的 DOM 读数：43 枚全是 `role=button` / `ignored=false` / `focusable`。"""
    total = 0
    bad: list[Any] = []
    for v, d in _views(r).items():
        for row in d["rows"]:
            total += 1
            ax = row["ax"]
            if (ax.get("role") != "button" or ax.get("ignored") is not False
                    or ax.get("props", {}).get("focusable") is not True):
                bad.append((v, row["aria"], ax))
    assert not bad, bad[:3]
    assert total == 43, total
    r["axTotals"] = {"instances": total}


def check_3(r: dict[str, Any]) -> None:
    """**AX 树里没有 `disabled`** —— 未接线与已接线的 `properties` 逐字相同。"""
    inert_props = set()
    for d in _views(r).values():
        for row in d["rows"]:
            inert_props.add(json.dumps(row["ax"].get("props", {}), sort_keys=True))
    assert len(inert_props) == 1, inert_props
    inert_props_json = inert_props.pop()
    assert "disabled" not in inert_props_json, inert_props_json
    wired = _views(r)["canvas"]["wired"]
    assert wired, "no wired control buttons found"
    for sel, w in wired.items():
        assert json.dumps(w["ax"].get("props", {}), sort_keys=True) == inert_props_json, \
            (sel, w["ax"].get("props"))
    assert all(w["dataInert"] is None for w in wired.values()), wired
    r["propsShared"] = {"inert": inert_props_json,
                        "wired": {k: v["ax"].get("props") for k, v in wired.items()}}


def check_4(r: dict[str, Any]) -> None:
    """**推翻 730**：可及名兜底到 `title`，**没有一枚是空的**。"""
    ident = _identities(r)
    empties = [k for k, row in ident.items() if not (row["ax"].get("name") or "").strip()]
    assert not empties, empties
    fallback = {k: row for k, row in ident.items()
                if not row["aria"].strip() and not row["text"].strip()}
    assert len(fallback) == 2, sorted(fallback)
    for k, row in fallback.items():
        assert row["ax"]["name"] == row["title"], (k, row["ax"]["name"], row["title"])
    r["nameFallback"] = {
        "identities": len(ident),
        "emptyNames": len(empties),
        "titleFallback": {f"{k[2] or k[1]}": row["ax"]["name"] for k, row in fallback.items()},
    }


def check_5(r: dict[str, Any]) -> None:
    """`title` 只在「既无 `aria-label` 又无文字」时兜底 —— 其余 20 种身份的名字是功能名。"""
    ident = _identities(r)
    sources: dict[str, int] = {}
    for k, row in ident.items():
        s = name_source(row)
        sources[s] = sources.get(s, 0) + 1
    assert sources.get("title") == 2, sources
    assert sources.get("title?") is None and sources.get("content?") is None \
        and sources.get("aria-label?") is None, sources
    failure = {k: row["ax"]["name"] for k, row in ident.items()
               if FAILURE_NAME.search(row["ax"].get("name") or "")}
    assert len(failure) == 2, failure
    for name in failure.values():
        assert name.startswith("该"), name
    r["nameSources"] = sources
    r["failureSentenceNames"] = sorted(failure.values())


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
        ("19-of-the-46-data-inert-sites-carry-no-aria-label", check_1),
        ("ax-tree-reproduces-the-dom-readings-for-all-43-instances", check_2),
        ("no-disabled-in-the-ax-tree-and-wired-buttons-are-byte-identical", check_3),
        ("accessible-names-fall-back-to-title-instead-of-being-empty", check_4),
        ("title-fallback-is-confined-to-two-icon-only-buttons", check_5),
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
