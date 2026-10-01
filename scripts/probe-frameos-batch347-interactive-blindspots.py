#!/usr/bin/env python3

"""Batch 347 探针：运行时普查「交互盲区」——有多少可点元素无法被测试寻址。

背景（Batch 345/346 连踩两次的元缺陷）:
Batch 345 发现 toast 元素只有内联样式、没有任何标识 → 「UI 是否谎报成功」
根本测不了。Batch 346 在帮助面板行上**又踩了一次**同样的坑。
同一个元缺陷在两个批次里连踩两次，说明「补可测性」不该靠临场想起。

本探针把这件事从「临场想起」变成**一次可复现的测量**:
在真实运行的画布上枚举所有可点元素，统计其中**没有任何稳定钩子**
（无 data-frameos-* / 无 aria-label / 无 id / 无 title）的比例。

盲区不等于缺陷，但它决定了「下一次 UI 撒谎时我们能不能抓到」。

用法: ~/.venvs/liblib-harness/bin/python scripts/probe-frameos-batch347-interactive-blindspots.py
"""

import json
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from frameos_verify_common import attach_errors, goto_clean_canvas  # noqa: E402

BASE_URL = "http://localhost:4317"

# 枚举所有可点元素及其「钩子」情况
ENUMERATE_JS = """
() => {
  const sel = 'button, [role="button"], a[href], input, textarea, select, [tabindex]';
  const nodes = Array.from(document.querySelectorAll(sel));
  const describe = (el) => {
    const text = (el.textContent || '').trim().slice(0, 24);
    const aria = el.getAttribute('aria-label') || '';
    const title = el.getAttribute('title') || '';
    const dataKeys = Array.from(el.attributes)
      .filter((a) => a.name.startsWith('data-'))
      .map((a) => a.name);
    const id = el.id || '';
    // 稳定钩子: 测试能用它精确定位这个元素
    const hooks = [];
    if (dataKeys.length) hooks.push(...dataKeys);
    if (aria) hooks.push('aria-label=' + aria);
    if (title) hooks.push('title=' + title);
    if (id) hooks.push('#' + id);
    return {
      tag: el.tagName.toLowerCase(),
      text,
      aria,
      title,
      id,
      dataKeys,
      hasHook: hooks.length > 0,
      hooks,
      disabled: el.disabled === true,
    };
  };
  const all = nodes.map(describe);
  const blind = all.filter((d) => !d.hasHook);
  // 按「组件归属」粗分: 沿最近的带 data-frameos-* 的祖先找
  const owner = (el) => {
    let p = el;
    while (p && p !== document.body) {
      for (const a of p.attributes || []) {
        if (a.name.startsWith('data-frameos-') && a.name !== 'data-frameos-toast'
            && a.name !== 'data-frameos-help-row') return a.name;
      }
      p = p.parentElement;
    }
    return '(no owner hook)';
  };
  const blindWithOwner = blind.map((d) => {
    const el = document.querySelectorAll('button,[role="button"],a[href],input,textarea,select,[tabindex]')
      .item(0); // placeholder, 真实 owner 在下方用 index 关联
    return d;
  });
  return {
    total: all.length,
    withHook: all.length - blind.length,
    blind: blind.length,
    blindRatio: all.length ? Math.round((blind.length / all.length) * 100) : 0,
    blindSamples: blind.slice(0, 40).map((d) => ({
      tag: d.tag, text: d.text, aria: d.aria, title: d.title,
    })),
  };
}
"""


def main() -> int:
    out: dict = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 950})
        errors = attach_errors(page)
        goto_clean_canvas(page, BASE_URL)

        # 基础态（默认打开的 UI）
        out["default"] = page.evaluate(ENUMERATE_JS)

        # 打开帮助面板再量一次（含面板自身的元素）
        page.keyboard.press("?")
        page.wait_for_timeout(500)
        out["with_help"] = page.evaluate(ENUMERATE_JS)
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        # 选中一个节点, 让节点浮动工具条出现
        page.evaluate(
            """() => {
              const st = window.__frameos_store;
              st.getState().selectNode(st.getState().nodes[0].id);
              return true;
            }"""
        )
        page.wait_for_timeout(600)
        out["with_node_selected"] = page.evaluate(ENUMERATE_JS)

        out["consoleErrors"] = errors
        browser.close()

    print("=== batch347 交互盲区普查 ===")
    for key in ("default", "with_help", "with_node_selected"):
        s = out[key]
        print(f"[{key:<20}] 可点元素 {s['total']:>3}  有稳定钩子 {s['withHook']:>3}  "
              f"盲区 {s['blind']:>3}  ({s['blindRatio']}%)")
    print("\n盲区样本(前 12):")
    for d in out["default"]["blindSamples"][:12]:
        label = d["text"] or d["aria"] or d["title"] or "(无任何文字)"
        print(f"  <{d['tag']}> {label!r}")
    if out["consoleErrors"]:
        print(f"console errors: {out['consoleErrors']}")
    print("\n=== 判定 ===")
    print(json.dumps({
        "default_blind": out["default"]["blind"],
        "default_total": out["default"]["total"],
        "default_blind_ratio_pct": out["default"]["blindRatio"],
        "help_blind": out["with_help"]["blind"],
        "node_selected_blind": out["with_node_selected"]["blind"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
