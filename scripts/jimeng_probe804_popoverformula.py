"""batch 804 取证：源站「节点摘要」弹层的**高度公式**与点击行为。

batch 803 复刻侧把弹层高度钉死 92px（当时源站只有 1 个节点）。本批源站画布
已有 4 个节点，实测弹层 132px —— 说明高度是**内容驱动**的。本脚本拆出内部
结构（行高 / 内外边距 / 分隔 / 底部入口）以反推公式，并观察点条目后的行为。

安全边界：只点弹层内的节点条目与「查看项目信息」，均为选中/导航，
不在 scripts/jimeng_auth.py 的 BILLED_ACTIONS 内。
"""

import json

URL = (
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create"
)

page.set_viewport_size({"width": 1680, "height": 826})
page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
page.wait_for_timeout(11_000)

page.locator('[data-testid="canvas-node-summary-trigger"]').click(timeout=15_000)
page.wait_for_timeout(1500)

struct = page.evaluate(
    """() => {
  const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
  // 弹层：宽约 200、位于触发钮下方的那个 dialog（源站 aria 为 null，按几何认）
  const cands = [...document.querySelectorAll('[role="dialog"]')].filter((el) => {
    const r = el.getBoundingClientRect();
    return r.width > 150 && r.width < 260 && r.height > 40;
  });
  const el = cands[0];
  if (!el) return { error: 'popover not found', n: cands.length };
  const r = el.getBoundingClientRect();
  const s = getComputedStyle(el);
  const kids = [...el.children].map((c) => {
    const cr = c.getBoundingClientRect();
    const cs = getComputedStyle(c);
    return { tag: c.tagName, cls: (c.className||'').toString().replace(/\\s+/g,' ').slice(0,70),
             h: Math.round(cr.height), y: Math.round(cr.y - r.y),
             text: norm(c.innerText).slice(0,60),
             font: cs.fontSize + '/' + cs.lineHeight,
             maxH: cs.maxHeight, overflow: cs.overflowY,
             rows: [...c.children].map((g) => {
               const gr = g.getBoundingClientRect();
               return { h: Math.round(gr.height), text: norm(g.innerText).slice(0,24) };
             }) };
  });
  return { rect: {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)},
           style: { padding: s.padding, radius: s.borderRadius, bg: s.backgroundColor, z: s.zIndex },
           kids };
}"""
)
print("=== 弹层结构 ===")
print(json.dumps(struct, ensure_ascii=False, indent=2)[:2600])

# 点第一个条目（按几何找，不依赖 aria）
clicked = False
rows = page.locator('[role="dialog"] >> css=div').filter(has_text="视频 1")
try:
    box = page.evaluate(
        """() => {
      const cands = [...document.querySelectorAll('[role="dialog"]')].filter((el) => {
        const r = el.getBoundingClientRect();
        return r.width > 150 && r.width < 260 && r.height > 40;
      });
      if (!cands.length) return null;
      const el = cands[0];
      // 取正文里第一个非「查看项目信息」的条目
      for (const c of el.querySelectorAll('*')) {
        const t = (c.innerText||'').trim();
        if (t && t !== '查看项目信息' && c.children.length === 0) {
          const r = c.getBoundingClientRect();
          return { x: r.x + r.width/2, y: r.y + r.height/2, text: t };
        }
      }
      return null;
    }"""
    )
    if box:
        before = page.evaluate("() => getComputedStyle(document.querySelector('.react-flow__viewport')).transform")
        nsel_before = page.evaluate(
            "() => [...document.querySelectorAll('.react-flow__node.selected')].map(n=>n.getAttribute('data-id'))"
        )
        page.mouse.click(box["x"], box["y"])
        page.wait_for_timeout(1800)
        after = page.evaluate("() => getComputedStyle(document.querySelector('.react-flow__viewport')).transform")
        nsel_after = page.evaluate(
            "() => [...document.querySelectorAll('.react-flow__node.selected')].map(n=>n.getAttribute('data-id'))"
        )
        still_open = page.evaluate(
            """() => [...document.querySelectorAll('[role="dialog"]')].some(el=>{
                 const r=el.getBoundingClientRect(); return r.width>150&&r.width<260&&r.height>40;})"""
        )
        print("\n=== 点击条目 ===")
        print(f"  点击目标: {box['text']!r}")
        print(f"  视口 before: {before}")
        print(f"  视口 after : {after}")
        print(f"  视口变化  : {before != after}")
        print(f"  选中节点 before: {nsel_before} -> after: {nsel_after}")
        print(f"  弹层仍开着  : {still_open}")
        clicked = True
except Exception as e:  # noqa: BLE001
    print("点击失败:", str(e)[:200])

if not clicked:
    print("（未完成点击观测）")
page.screenshot(path="/tmp/jimeng-804-source-after-click.png")
