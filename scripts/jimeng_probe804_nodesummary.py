"""batch 804 取证：源站顶栏「节点摘要」弹层点节点后的**真实行为**。

batch 803 复刻侧已实现「点节点 → 选中 + 视口聚焦」，但那是按合理推测写的
（CLONE_DECISION）。本脚本去源站确认：点弹层里的节点条目后，源站是否真的
选中该节点、视口是否平移聚焦、弹层是否收起。这决定复刻侧的行为是否需要调整。

安全边界：只点「节点 N」与弹层里的节点条目，均为纯导航/选中，不在
scripts/jimeng_auth.py 的 BILLED_ACTIONS 内，不提交任何生成任务。
"""

import json

URL = (
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create"
)

page.set_viewport_size({"width": 1680, "height": 826})
page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
page.wait_for_timeout(11_000)


def state(tag: str) -> dict:
    return page.evaluate(
        """(tag) => {
      const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
      const nodes = [...document.querySelectorAll('.react-flow__node')].map((n) => {
        const r = n.getBoundingClientRect();
        return { id: (n.getAttribute('data-id')||'').slice(0,28),
                 selected: n.classList.contains('selected'),
                 x: Math.round(r.x), y: Math.round(r.y),
                 w: Math.round(r.width), h: Math.round(r.height),
                 text: norm(n.innerText).slice(0,40) };
      });
      const vp = document.querySelector('.react-flow__viewport');
      const dlg = [...document.querySelectorAll('[role="dialog"]')]
        .filter((el) => { const r = el.getBoundingClientRect(); return r.width>1 && r.height>1; })
        .map((el) => { const r = el.getBoundingClientRect();
          return { aria: el.getAttribute('aria-label'),
                   rect: {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)},
                   text: norm(el.innerText).slice(0,80) }; });
      return { tag,
        viewportTransform: vp ? getComputedStyle(vp).transform : null,
        nodes, dialogs: dlg };
    }""",
        tag,
    )


out = {}
out["before"] = state("before")

# 打开「节点摘要」弹层
trigger = page.locator('[data-testid="canvas-node-summary-trigger"]')
if trigger.count() == 0:
    print("未找到节点摘要触发器")
else:
    trigger.click(timeout=15_000)
    page.wait_for_timeout(1200)
    out["opened"] = state("after-open-trigger")
    dlg = out["opened"]["dialogs"]
    print("=== 打开后可见弹层 ===")
    for d in dlg:
        print(f"  aria={d['aria']!r} {d['rect']} text={d['text']!r}")

    # 点弹层里的节点条目
    clicked = False
    for d in dlg:
        items = page.locator(f'[role="dialog"][aria-label="{d["aria"]}"]').locator(
            '[role="menuitem"], button, li'
        )
        n = items.count()
        print(f"  dialog {d['aria']!r} 内可点条目数: {n}")
        if n:
            label = items.first.inner_text().strip()
            items.first.click(timeout=15_000)
            print(f"  已点击条目: {label!r}")
            clicked = True
            break
    page.wait_for_timeout(2000)
    out["after_click"] = state("after-click-item")
    if not clicked:
        out["after_click"] = {"tag": "after-click-item", "skipped": True}
    page.screenshot(path="/tmp/jimeng-804-source-node-summary-click.png")

print(json.dumps(out, ensure_ascii=False, indent=2)[:4000])
