"""Batch 353 只读探针: Batch 347 的可寻址门禁只普查了 3 种 UI 态, 其余态是否有盲区?

Batch 347 在三种 UI 态(默认 / 帮助开 / 选中节点)下枚举所有可交互元素
(button/[role=button]/a[href]/input/textarea/select/[tabindex]), 要求每个都有
稳定钩子(data-* / aria-label / title / id), 缺一个就红。门禁当时 38 个元素、
4 个盲区, 修完 85/85 通过。

但那 3 种态**碰不到**的东西: 裁剪态、分组态、节点搜索面板、模板面板,
以及 `FrameosGenerationOverlay`(整个组件零 `data-frameos-*`)。
本探针只读地扫这些态, 看盲区有多少、在哪。

与门禁用**同一把尺子**(同一份 ENUMERATE_JS 逻辑)。
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from playwright.sync_api import sync_playwright  # noqa: E402

from frameos_verify_common import attach_errors, goto_clean_canvas  # noqa: E402

ENUMERATE_JS = """
() => {
  const sel = 'button, [role="button"], a[href], input, textarea, select, [tabindex]';
  const nodes = Array.from(document.querySelectorAll(sel));
  const describe = (el) => {
    const dataKeys = Array.from(el.attributes)
      .filter((a) => a.name.startsWith('data-'))
      .map((a) => a.name);
    const aria = el.getAttribute('aria-label') || '';
    const title = el.getAttribute('title') || '';
    const id = el.id || '';
    const hooks = [...dataKeys];
    if (aria) hooks.push('aria-label=' + aria);
    if (title) hooks.push('title=' + title);
    if (id) hooks.push('#' + id);
    return { tag: el.tagName.toLowerCase(), text: (el.textContent || '').trim().slice(0, 24),
             aria, title, id, dataKeys, hasHook: hooks.length > 0, hooks };
  };
  const all = nodes.map(describe);
  const blind = all.filter((d) => !d.hasHook);
  return { total: all.length, withHook: all.length - blind.length, blind: blind.length,
           blindItems: blind.map((d) => ({
             tag: d.tag, text: d.text || d.aria || d.title || '(无任何文字)' })) };
}
"""


def scan(page):
    return page.evaluate(ENUMERATE_JS)


def main() -> int:
    report = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        errs = attach_errors(page)
        goto_clean_canvas(page)

        # ── 态 1: 裁剪态 ──
        page.locator('.react-flow__node[data-id="image-1"]').click()
        page.wait_for_timeout(600)
        page.get_by_label("裁剪", exact=True).first.click()
        page.wait_for_selector("[data-frameos-crop-rect]", timeout=8000)
        page.wait_for_timeout(400)
        report["crop"] = scan(page)
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        # ── 态 2: 分组态(先造一个分组) ──
        page.evaluate(
            """() => {
                const st = window.__frameos_store;
                const ids = st.getState().nodes.slice(0, 2).map((n) => n.id);
                st.getState().createGroup(ids);
                return true;
            }"""
        )
        page.wait_for_timeout(700)
        report["group"] = scan(page)
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        # ── 态 3: 节点搜索面板 ──
        page.keyboard.press("Meta+f")
        page.wait_for_timeout(600)
        report["node_search"] = scan(page)
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        # ── 态 4: 模板面板 ──
        page.get_by_label("模板", exact=True).first.click()
        page.wait_for_timeout(600)
        report["template_panel"] = scan(page)
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        # ── 态 5: 生成浮窗(mock 时钟压到 2s, 机制与时长无关) ──
        pane = page.locator(".react-flow__pane")
        box = pane.bounding_box()
        pane.dblclick(position={"x": box["width"] * 0.2, "y": box["height"] * 0.75})
        page.wait_for_selector("[data-frameos-pane-addnode-type]", timeout=8000)
        page.locator('[data-frameos-pane-addnode-type="image"]').click()
        page.wait_for_timeout(500)
        page.locator(".react-flow__node").last.click()
        page.wait_for_timeout(500)
        page.get_by_label("生成", exact=True).first.click()
        page.wait_for_timeout(300)
        page.evaluate(
            """() => {
                const s = window.__frameos_store.getState();
                window.__frameos_store.setState({
                  currentGeneration: { ...s.currentGeneration, durationMs: 20000 },
                });
            }"""
        )
        page.wait_for_timeout(600)
        report["generation"] = scan(page)
        report["errors"] = errs
        browser.close()

    out = Path(__file__).resolve().parent.parent / "docs/research/liblib-frameos-batch353-2026-10-01"
    out.mkdir(parents=True, exist_ok=True)
    (out / "census.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))

    print(f"{'状态':<16}{'总数':>6}{'有钩子':>8}{'盲区':>6}")
    for k, v in report.items():
        if not isinstance(v, dict) or "total" not in v:
            continue
        print(f"{k:<16}{v['total']:>6}{v['withHook']:>8}{v['blind']:>6}")
        for it in v["blindItems"][:8]:
            print(f"    - <{it['tag']}> {it['text']!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
