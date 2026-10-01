#!/usr/bin/env python3
"""Verify Batch 366: 分镜脚本编辑器的每行「···」操作菜单是死的, 且从未被任何门禁验证过。

## 怎么找到的

Batch 364 建的覆盖普查(`probe_liblib_batch364_coverage.py`)用 `data-*` 标记
覆盖率衡量「这个面有没有被验证过」。PARTIAL 名单里 `StoryboardScriptEditor`
漏了 `storyboard-row-menu`, 逐个核实时发现它不是「边缘标记」:

```tsx
<button type="button" data-storyboard-row-menu
  aria-label={`镜头${row.shot}操作`}
  className="rounded px-1.5 text-[#8c8c8c] hover:bg-white/[0.06]">···</button>
```

**无 onClick、无 disabled, 却带 `hover:bg-white/[0.06]`** —— 用户悬停看到它
变亮, 点下去什么都不发生。它是分镜表格每一行最右端的操作入口(「···」),
视觉上明确在邀请点击。

**更值得记的一点**: 它是该组件里**唯一**带 `data-*` 标记的 `<button>`
(其余按钮都没标记, 普查统计不到)。所以「标记覆盖率」这个判据在这里
**低估**了组件的控件数 —— 我第一反应是「只有 1 个按钮, 影响很小」,
实际上这个组件有几十个按钮, 只是它们没有标记。
> 判据的**上界**同样要验证。标记覆盖率能说「哪些没被验证」, 不能说
> 「标记少 = 控件少」。

## 为什么之前没人发现

`storyboard-row-menu` 不在任何门禁的引用列表里。而打开这个编辑器的路径
不平凡: 需要「添加节点 → script → script-new」新建一个剧本生成节点, 再点
「自己编写分镜脚本」—— 默认 fixture 里没有这样的节点, 所以大多数门禁
连编辑器都进不去。

**探针必须真的走到那一步**。若中途任何一步失败, 一律报「跳过」而不是
「0 问题」—— 那是 360 立下的规矩, 也是本批能拿到真结论的前提。

## 修法: 与 358/359/360/364 同策, 不发明

源站行为未采样(人机验证仍阻塞), 行操作菜单(复制/删除/重排)的具体项也没有
源站事实。**不擅自发明菜单**, 按既定处置让 UI 停止撒谎: 去掉悬停骗人反馈 +
`cursor: default` + `title` 说明 + `data-inert` 自证惰性。几何与文案不动。

## 断言

1. 防假零: 编辑器**必须真的打开**且**真的有行**(打不开/无行直接红);
2. 行操作按钮**真的存在**, 不可见即红;
3. 惰性必须**自证**: `data-inert` + 非空 `title` + `cursor: default`;
4. 同一行的其他交互(单元格输入)**未受影响** —— 不过度拦截;
5. 诊断零错误。
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT = ROOT / "docs" / "research" / "liblib-batch366-2026-10-01" / "runtime-audit.json"

EDITOR = "[data-storyboard-editor]"
ROW_MENU = "[data-storyboard-row-menu]"
CELL_INPUT = "[data-storyboard-cell-input]"


def open_storyboard_editor(page: Page) -> bool:
    """走完整路径打开分镜脚本编辑器。返回是否真的打开。

    默认 fixture 里没有剧本生成节点, 必须「添加节点 → script → script-new」
    新建一个, 再点「自己编写分镜脚本」。任一步失败就返回 False,
    **由调用方报「跳过」而不是「0 问题」**。
    """
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(1600)
    page.keyboard.press("Alt+Shift+F")
    page.wait_for_timeout(600)

    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(400)
    panel = page.locator('[data-liblib-overlay="add-node"]')
    if panel.count() == 0:
        return False
    panel.locator("[data-add-node-entry='script']").click()
    page.wait_for_timeout(300)
    panel.locator("[data-add-node-entry='script-new']").click()
    page.wait_for_timeout(800)

    node = page.locator(".react-flow__node-script-generator").first
    if node.count() == 0:
        return False
    self_write = node.locator("[data-script-generator-attempt='自己编写分镜脚本']")
    if self_write.count() == 0:
        return False
    self_write.click()
    page.wait_for_timeout(1000)
    return page.locator(EDITOR).count() > 0


def main() -> int:
    audit: dict[str, object] = {"checks": [], "errors": {"console": [], "page": [], "request": []}}
    checks: list[dict[str, object]] = audit["checks"]  # type: ignore[assignment]
    errs: dict[str, list] = audit["errors"]  # type: ignore[assignment]

    def check(name: str, ok: bool, detail: object = None) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("console", lambda m: m.type == "error" and errs["console"].append(m.text))
        page.on("pageerror", lambda e: errs["page"].append(str(e)))
        page.on("requestfailed", lambda r: errs["request"].append(r.url))

        # ---- 1. 防假零: 编辑器必须真的打开 ----
        if not open_storyboard_editor(page):
            check("editor:really-opens", False, "未能打开分镜脚本编辑器(不是 0 问题)")
            browser.close()
            return report(audit)
        check("editor:really-opens", True)

        menus = page.locator(ROW_MENU)
        count = menus.count()
        check("row-menu:exists", count >= 1, f"count={count}")
        check("row-menu:visible", count >= 1 and menus.first.is_visible(), count)

        if count >= 1:
            info = page.evaluate(
                """(sel) => {
                  const el = document.querySelector(sel);
                  if (!el) return null;
                  const cs = getComputedStyle(el);
                  // 直接问浏览器「悬停时背景会不会变」, 而不是只查 cursor ——
                  // 第一版只断 cursor, 而 cursor 本来就是 default, 判据恒绿,
                  // 抓不住「把 hover:bg-* 加回去」这种回归。
                  const probe = (rules) => {
                    for (const sheet of rules) {
                      let list; try { list = sheet.cssRules; } catch { continue; }
                      for (const r of list) {
                        if (r.selectorText && el.matches(r.selectorText)
                            && /:hover/.test(r.selectorText)
                            && /background/.test(r.style.cssText)) {
                          return r.style.cssText.slice(0, 120);
                        }
                      }
                    }
                    return null;
                  };
                  return {
                    aria: el.getAttribute('aria-label'),
                    title: el.getAttribute('title'),
                    inert: el.getAttribute('data-inert'),
                    cursor: cs.cursor,
                    disabled: el.disabled === true,
                    text: (el.textContent || '').trim(),
                    hoverBackground: probe(document.styleSheets),
                    ownClass: el.getAttribute('class') || '',
                  };
                }""",
                ROW_MENU,
            )
            audit["rowMenu"] = info

            # ---- 2. 惰性必须自证 ----
            check("row-menu:declared-inert", (info or {}).get("inert") == "true", (info or {}).get("inert"))
            check("row-menu:has-explanatory-title",
                  bool(((info or {}).get("title") or "").strip()), (info or {}).get("title"))
            check("row-menu:no-hover-affordance",
                  (info or {}).get("cursor") == "default", (info or {}).get("cursor"))
            # 悬停时背景不得变化 —— 判据直接看样式表, 不用 cursor 当代理
            check("row-menu:no-hover-background-rule",
                  (info or {}).get("hoverBackground") is None, (info or {}).get("hoverBackground"))
            check("row-menu:class-has-no-hover",
                  "hover:" not in ((info or {}).get("ownClass") or ""), (info or {}).get("ownClass"))
            check("row-menu:not-disabled",
                  (info or {}).get("disabled") is False, (info or {}).get("disabled"))

        # ---- 3. 不过度拦截: 同一行的单元格输入仍可用 ----
        # 注意 `data-storyboard-cell-input` 只在**编辑态**出现
        # (`StoryboardScriptEditor.tsx:56` 的 `if (editing)`), 默认是只读文本。
        # 所以必须先点单元格进入编辑, 再断言输入框存在且能打字 ——
        # 第一版直接找 input 拿到 0 个, 差点误判成「编辑器坏了」。
        cells = page.locator(CELL_INPUT)
        if cells.count() == 0:
            page.locator("[data-storyboard-cell]").first.click()
            page.wait_for_timeout(300)
            cells = page.locator(CELL_INPUT)
        check("cells:still-editable", cells.count() >= 1, f"cells={cells.count()}")
        if cells.count() >= 1:
            cells.first.fill("冒烟")
            page.wait_for_timeout(200)
            after = cells.first.input_value()
            check("cells:typing-works", after == "冒烟", f"-> {after!r}")

        AUDIT.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(AUDIT.parent / "storyboard-editor.png"))
        browser.close()

    return report(audit)


def report(audit: dict) -> int:
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    failed = [c for c in audit["checks"] if not c["ok"]]  # type: ignore[union-attr]
    errs = audit["errors"]
    noisy = [e for e in list(errs["console"]) + list(errs["page"])  # type: ignore[index]
             if "ERR_ABORTED" not in e and "WebSocket" not in e]
    if failed:
        print(f"Batch 366: {len(audit['checks']) - len(failed)}/{len(audit['checks'])} checks passed")  # type: ignore[arg-type]
        print("FAILED:", json.dumps(failed, ensure_ascii=False, indent=1))
    if noisy:
        print("DIAGNOSTICS:", json.dumps(noisy[:5], ensure_ascii=False, indent=1))
    if failed or noisy:
        return 1
    print(f"Batch 366 verification passed: {len(audit['checks'])} checks. "  # type: ignore[arg-type]
          "The per-shot '···' menu in the storyboard script editor is now declared "
          "inert with an explanatory title, and the row's cell input still works.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
