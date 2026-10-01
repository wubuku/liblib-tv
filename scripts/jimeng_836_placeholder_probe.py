"""batch 836 取证：占位符里那枚 24×24 的 `@` 钮，点它会发生什么。

复刻的 `canvas-agent-composer-placeholder-mention` 是一枚**纯装饰**的 @ 钮
（无 onClick）—— 810 只断言了它存在（count==1），没断言它做不做任何事，
于是它一直在那儿装样子。源站同位置的 `canvas-agent-composer-placeholder-mention`
@[1428,784] 24×24，al=「引用参考」。点它开不开面板、开的是哪个，都得先量。

顺带把占位符那段的**逐字结构**取下来：源站是 contenteditable，placeholder 里
居然能塞一枚**活的** @ 钮（810 早就发现源站 composer 是 contenteditable DIV，
而当时的指纹只扫 input/textarea，够不着它）。这一条决定了复刻能不能照抄
「placeholder 里带按钮」。

⚠ 只点不消耗积分的控件，绝不点「发送」。

用法：
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
        scripts/jimeng_836_placeholder_probe.py
"""

from __future__ import annotations

import json
from pathlib import Path

OUT_DIR = Path("docs/research/jimeng-canvas-batch836-2026-10-04")
URL = (
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create"
)

# 面板里所有 testid（用于「点了之后多了什么」）
TIDS_JS = """() => [...document.querySelectorAll('[data-testid]')]
  .map((el) => { const b = el.getBoundingClientRect();
    return el.getAttribute('data-testid') + '@' + [b.x, b.y, b.width, b.height]
      .map(Math.round).join(','); })
  .filter((s) => s.includes('agent') || s.includes('prompt') || s.includes('composer'))"""

# 占位符那一段：逐个文本节点 + 元素
PLACEHOLDER_JS = """() => {
  const btn = document.querySelector('[data-testid="canvas-agent-composer-placeholder-mention"]');
  if (!btn) return { error: '占位符 @ 钮不存在' };
  const box = btn.closest('[data-testid="prompt-composer"]') || btn.parentElement;
  const out = [];
  const walk = document.createTreeWalker(box, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = walk.nextNode())) {
    const t = (n.nodeValue || '').trim();
    if (!t) continue;
    const p = n.parentElement;
    const b = p.getBoundingClientRect();
    const cs = getComputedStyle(p);
    out.push({ tag: p.tagName, text: t, tid: p.getAttribute('data-testid') || '',
               cls: String(p.className || '').slice(0, 40), color: cs.color, fontSize: cs.fontSize,
               rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)] });
  }
  const bb = btn.getBoundingClientRect();
  return {
    nodes: out,
    mention_btn: { al: btn.getAttribute('aria-label'), tag: btn.tagName,
                   rect: [Math.round(bb.x), Math.round(bb.y), Math.round(bb.width), Math.round(bb.height)],
                   cursor: getComputedStyle(btn).cursor },
    composer: (() => { const c = box.getBoundingClientRect();
      return [Math.round(c.x), Math.round(c.y), Math.round(c.width), Math.round(c.height)]; })(),
  };
}"""


def main() -> int:
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    for _ in range(24):
        if not page.evaluate("() => document.body.innerText.includes('Loading canvas')"):
            break
        page.wait_for_timeout(2000)
    page.wait_for_timeout(2500)
    page.click('[data-testid="canvas-sidecar-launcher"]')
    page.wait_for_timeout(1500)

    before = set(page.evaluate(TIDS_JS))
    placeholder = page.evaluate(PLACEHOLDER_JS)
    page.screenshot(path=str(OUT_DIR / "source-placeholder.png"))

    page.click('[data-testid="canvas-agent-composer-placeholder-mention"]')
    page.wait_for_timeout(1200)
    after = set(page.evaluate(TIDS_JS))
    body_after = page.evaluate("() => document.body.innerText.replace(/\\s+/g, ' ').slice(0, 400)")
    page.screenshot(path=str(OUT_DIR / "source-placeholder-clicked.png"))

    report = {
        "viewport": page.viewport_size,
        "placeholder": placeholder,
        "tids_before": sorted(before),
        "tids_after": sorted(after),
        "new_tids": sorted(after - before),
        "gone_tids": sorted(before - after),
        "body_after": body_after,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "source-placeholder-probe.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("占位符文本节点：")
    for n in (placeholder.get("nodes") or []):
        print(f"   <{n['tag']}> {n['text']!r} {n['color']} {n['fontSize']} {n['rect']}")
    print("占位符 @ 钮：", placeholder.get("mention_btn"))
    print("composer 盒：", placeholder.get("composer"))
    print("点它之后新增的 testid：", report["new_tids"])
    print("点它之后消失的 testid：", report["gone_tids"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
