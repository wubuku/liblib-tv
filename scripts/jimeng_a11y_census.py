#!/usr/bin/env python3
"""跨站**无障碍语义普查**：把「有哪些可交互控件、叫什么、在哪」拉成两张表再对拍。

Batch 816 用。选题思路照 batch 807-topleft §17.1「让像素指出下一个 batch」，
这里换成让**语义**指出：批 801/812/813/814 的真缺口全是这一类
（`Add tags` 实名、`Rename {标题}`、右键菜单 7 项），像素对拍一个都看不出来。

为什么不用 `page.accessibility.snapshot()`：它给的是 role 化的语义树，
会把「按钮文案折行」「两个同 role 兄弟」这类结构差异压平。批 808 刚吃过
「判据够不着 ≠ 控件没反应」的亏（§18.1），这里宁可取原始属性。

读数契约（SOURCE_FACT 级别的注意点）：
- **不做缩放归一化**：本探针比的是「有哪些控件、叫什么」这个集合，
  位置只作参考。跨站几何比较必须先归一化，那是另一条铁律（§22.1）。
- 只收**可见且可命中**的元素：0 尺寸 / `display:none` / `visibility:hidden` /
  `opacity<0.05` / `aria-hidden` 子树一律跳过。
- name 取 `aria-label` → `title` → `innerText` 逐级回落，并记下回落层级，
  这样「源站有 aria-label 而复刻只有 innerText」这种半对齐会自己冒出来。

用法：
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_a11y_census.py
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_a11y_census.py --diff
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import jimeng_auth as auth  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

SRC = (
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create"
)
# ⚠️ 必须用 `localhost`，**不能**写 `127.0.0.1`。两者是不同 origin，而
# `next dev` 对非 localhost 主机的请求会让 React **完全不 hydrate** ——
# 页面只剩 SSR 静态 HTML：节点不渲染、`defaultViewport` 不生效、所有交互
# 失效，且**零报错、零警告**（实测 2026-10-04，见台账 §27）。
# 后果不是"读不到"，是**读到一份降级页面**，据此得出的"复刻缺失 X"
# 全是假象。本仓库所有 verifier 用的都是 localhost，本脚本原先写错。
CLONE = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317") + "/jimeng/canvas/demo"
OUT = Path(__file__).resolve().parent.parent / "docs/research/jimeng-canvas-batch816-2026-10-03"

# hydrate 探针：React 接管后会在根 DOM 节点上挂 `__reactFiber$*` / `__reactProps$*`。
# 普查/验收**在读任何复刻侧数字之前**必须先过这一关，否则量的是 SSR 骨架。
HYDRATED = """() => {
  const el = document.getElementById('__next')
          || document.body.firstElementChild
          || document.body;
  return Object.keys(el).some(k => k.startsWith('__reactFiber$'))
      && Object.keys(el).some(k => k.startsWith('__reactProps$'));
}"""

# 计入普查的标签：可交互元素 + 少量语义容器（浮层/菜单/工具条）
SELECTOR = (
    "button, [role='button'], [role='menuitem'], [role='tab'], [role='switch'], "
    "[role='checkbox'], [role='radio'], [role='combobox'], [role='textbox'], "
    "input, select, textarea, [contenteditable='true'], "
    "[role='menu'], [role='listbox'], [role='dialog'], [role='toolbar'], "
    "a[href], summary"
)

CENSUS = r"""(sel) => {
  const norm = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const rows = [];
  for (const el of document.querySelectorAll(sel)) {
    // aria-hidden / hidden 子树整体跳过：它们对 AT 不可见，算进去是普查假象
    if (el.closest('[aria-hidden="true"]')) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    if (parseFloat(cs.opacity) < 0.05) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    if (cs.pointerEvents === 'none') continue;

    const aria = el.getAttribute('aria-label');
    const title = el.getAttribute('title');
    const text = norm(el.innerText);
    let name = '', via = '';
    if (aria) { name = norm(aria); via = 'aria-label'; }
    else if (title) { name = norm(title); via = 'title'; }
    else if (text) { name = text.slice(0, 80); via = 'text'; }
    else {
      const al = el.getAttribute('aria-labelledby');
      if (al) {
        const t = document.getElementById(al.split(/\\s+/)[0]);
        if (t) { name = norm(t.innerText).slice(0, 80); via = 'aria-labelledby'; }
      }
    }

    rows.push({
      tag: el.tagName.toLowerCase(),
      type: el.getAttribute('type') || '',
      role: el.getAttribute('role') || '',
      testid: el.getAttribute('data-testid') || '',
      name, nameVia: via,
      // 半对齐信号：源站用 aria-label 命名而复刻靠文本，名字可能对但无障碍层不一致
      disabled: el.hasAttribute('disabled') || el.getAttribute('aria-disabled') === 'true',
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      radius: cs.borderRadius,
      bg: cs.backgroundColor,
    });
  }
  rows.sort((a, b) => (a.box[1] - b.box[1]) || (a.box[0] - b.box[0]));
  return rows;
}"""


def census(page, url: str, tag: str, settle_ms: int) -> list[dict]:
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(settle_ms)
    if tag == "source":
        # 归 100% 再读：位置读数才可比（只比存在性也保持一致口径）
        page.keyboard.press("Meta+1")
        page.wait_for_timeout(700)
    else:
        # 复刻侧先过 hydrate 闸门。**不是防御性编程，是必需的**：非 localhost
        # 主机拿到的页面只有 SSR 骨架，普查会把"没渲染"读成"产品缺失"。
        for _ in range(12):
            if page.evaluate(HYDRATED):
                break
            page.wait_for_timeout(1000)
        else:
            raise SystemExit(
                f"复刻侧未 hydrate（{CLONE}）。读下去只会得到一份 SSR 骨架，"
                "所有'复刻缺失'结论都是假象 —— 换 localhost 再来。详见台账 §27。"
            )
    return page.evaluate(CENSUS, SELECTOR)


def diff(src: list[dict], clone: list[dict]) -> None:
    def key(r: dict) -> str:
        return (r["nameVia"] and r["name"] or "") or f'<{r["tag"]} {r["testid"]}>'

    s_names = {key(r) for r in src}
    c_names = {key(r) for r in clone}
    missing = sorted(s_names - c_names)
    extra = sorted(c_names - s_names)

    print(f"\n源站 {len(src)} 个 / 复刻 {len(clone)} 个；名字去重后 "
          f"{len(s_names)} vs {len(c_names)}")

    print(f"\n=== 复刻缺失（源站有、复刻没有）{len(missing)} ===")
    for m in missing:
        print("  -", m)
    print(f"\n=== 复刻多出（源站没有）{len(extra)} ===")
    for e in extra:
        print("  +", e)

    # 半对齐：同名但命名通道不同
    half = []
    s_by = {key(r): r for r in src}
    c_by = {key(r): r for r in clone}
    for n in sorted(s_names & c_names):
        if s_by[n]["nameVia"] != c_by[n]["nameVia"]:
            half.append((n, s_by[n]["nameVia"], c_by[n]["nameVia"]))
    print(f"\n=== 半对齐：同名但命名通道不同 {len(half)} ===")
    for n, a, b in half:
        print(f"  ~ {n}  源站={a} 复刻={b}")

    # testid 覆盖：源站有 testid 而复刻没有（自动化锚点缺失）
    s_tid = {r["testid"] for r in src if r["testid"]}
    c_tid = {r["testid"] for r in clone if r["testid"]}
    print(f"\n=== testid 差集 ===")
    print("  复刻缺 testid:", sorted(s_tid - c_tid) or "（0）")
    print("  复刻多 testid:", sorted(c_tid - s_tid) or "（0）")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--diff", action="store_true", help="只对拍已存下的读数")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    src_f, clone_f = out / "census-source.json", out / "census-clone.json"

    if args.diff and src_f.exists() and clone_f.exists():
        diff(json.loads(src_f.read_text()), json.loads(clone_f.read_text()))
        return 0

    with sync_playwright() as p:
        # 复用 jimeng_auth 的登录态 + CONTEXT_OPTIONS（视口 1512×950 在其中）
        b, ctx, page = auth.open_headless(p)

        src = census(page, SRC, "source", 9000)
        print(f"源站读数 {len(src)} 个")
        src_f.write_text(json.dumps(src, ensure_ascii=False, indent=1))

        clone = census(page, CLONE, "clone", 6000)
        print(f"复刻读数 {len(clone)} 个")
        clone_f.write_text(json.dumps(clone, ensure_ascii=False, indent=1))

        b.close()

    diff(src, clone)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
