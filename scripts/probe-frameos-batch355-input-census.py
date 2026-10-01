"""Batch 355 只读探针: frameos 里「启用着、收下输入、什么都不做」的表单控件。

Batch 350 在裁剪态发现同族缺陷: 宽高是非受控输入且从无代码读取, 用户填的数字
被静默丢弃、节点毫无变化, 而 UI 弹了确认。

这里是普查版: 把 frameos 全部**启用的** input/textarea 列出来, 逐个判断
  A) 受控(value + onChange 都在)      → 正常
  B) 无 value 但有 onChange            → 正常(非受控但有本地 state)
  C) 既无 value 也无 onChange/readOnly  → **静默丢弃输入的假可用控件**

C 类是缺陷: 控件看起来能用, 收下输入, 然后什么都不发生。
本探针只读观测, 不改任何产品代码。
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from playwright.sync_api import sync_playwright  # noqa: E402

from frameos_verify_common import attach_errors, goto_clean_canvas  # noqa: E402

# React 受控输入的痕迹: DOM 上会挂 __reactProps$*, 从中读 onChange/value
CLASSIFY_JS = """
() => {
  const sel = 'input, textarea';
  const out = Array.from(document.querySelectorAll(sel)).map((el) => {
    const rk = Object.keys(el).filter((k) => k.startsWith('__reactProps$'));
    let hasOnChange = false, hasValue = false, isControlled = false;
    for (const k of rk) {
      const props = el[k];
      if (!props) continue;
      hasOnChange = hasOnChange || typeof props.onChange === 'function';
      if ('value' in props) { hasValue = true; isControlled = props.value !== undefined; }
    }
    return {
      tag: el.tagName.toLowerCase(),
      disabled: el.disabled === true,
      readOnly: el.readOnly === true,
      placeholder: (el.placeholder || '').slice(0, 30),
      aria: el.getAttribute('aria-label') || '',
      data: Array.from(el.attributes).filter((a) => a.name.startsWith('data-')).map((a) => a.name),
      hasOnChange, hasValue, isControlled,
      domValue: (el.value || '').slice(0, 30),
    };
  });
  return out;
}
"""

# 各 UI 态: (名字, 进入函数)
def enter_crop(page):
    page.locator('.react-flow__node[data-id="image-1"]').click()
    page.wait_for_timeout(600)
    page.get_by_label("裁剪", exact=True).first.click()
    page.wait_for_selector("[data-frameos-crop-rect]", timeout=8000)


def enter_assets(page):
    page.locator("[data-frameos-assets-button]").first.click()
    page.wait_for_selector("[data-frameos-project-assets-panel]", timeout=8000)


def enter_generative_node(page):
    """加一个无媒体内容的生成节点 —— 主面板(含提示词框)只对这类节点渲染。"""
    pane = page.locator(".react-flow__pane")
    box = pane.bounding_box()
    pane.dblclick(position={"x": box["width"] * 0.2, "y": box["height"] * 0.75})
    page.wait_for_selector("[data-frameos-pane-addnode-type]", timeout=8000)
    page.locator('[data-frameos-pane-addnode-type="image"]').click()
    page.wait_for_timeout(500)
    page.locator(".react-flow__node").last.click()
    page.wait_for_timeout(600)


def leave_all(page):
    """退出所有可能打开的面板/浮层, 让每个态都从干净起点进入。"""
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    page.evaluate(
        """() => {
            const st = window.__frameos_store.getState();
            st.setCroppingNode(null);
            if (st.isProjectAssetsPanelOpen) st.toggleProjectAssetsPanel();
            st.selectNode(null);
        }"""
    )
    page.wait_for_timeout(300)


def main() -> int:
    report = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        errs = attach_errors(page)
        goto_clean_canvas(page)

        for name, enter in [
            ("default", lambda pg: None),
            ("assets_panel", enter_assets),
            ("crop", enter_crop),
            ("generative_panel", enter_generative_node),
        ]:
            leave_all(page)
            enter(page)
            page.wait_for_timeout(400)
            items = page.evaluate(CLASSIFY_JS)
            silent = [
                it for it in items
                if not it["disabled"] and not it["readOnly"] and not it["hasOnChange"]
            ]
            report[name] = {"all": items, "silently_discarding": silent}
        report["errors"] = errs
        browser.close()

    out = Path(__file__).resolve().parent.parent / "docs/research/liblib-frameos-batch355-2026-10-01"
    out.mkdir(parents=True, exist_ok=True)
    (out / "input-census.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))

    total_silent = 0
    for name, v in report.items():
        if not isinstance(v, dict) or "silently_discarding" not in v:
            continue
        n_all = len(v["all"])
        n_bad = len(v["silently_discarding"])
        total_silent += n_bad
        print(f"[{name}] 输入控件 {n_all} 个, 静默丢弃输入 {n_bad} 个")
        for it in v["silently_discarding"]:
            print(f"    - <{it['tag']}> aria={it['aria']!r} ph={it['placeholder']!r} data={it['data']}")
    print(f"\n合计静默丢弃输入的控件: {total_silent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
