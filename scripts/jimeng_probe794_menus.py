"""batch 794 取证：源站顶栏「更多」「分享」「项目」「节点 2」四个触发器各自打开什么。

安全边界：只点这四个**纯导航/弹层**触发器，均不在 scripts/jimeng_auth.py 的
BILLED_ACTIONS 清单里，不提交任何生成任务、不消耗积分。每次点击后立即
抓结构并用 Escape 收起，避免状态叠加。

只读探索：不输入文本、不确认任何提交类按钮。
"""

import json

URL = (
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create"
)

page.set_viewport_size({"width": 1680, "height": 826})
page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
page.wait_for_timeout(10_000)


def read_overlays() -> dict:
    """抓当前可见的浮层：菜单项、对话框、toast。"""
    return page.evaluate(
        """() => {
      const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
      const vis = (el) => {
        const r = el.getBoundingClientRect();
        if (r.width < 1 || r.height < 1) return false;
        for (let p = el; p; p = p.parentElement) {
          const s = getComputedStyle(p);
          if (s.visibility === 'hidden' || s.display === 'none') return false;
        }
        return true;
      };
      const SEL = '[role="menu"], [role="menuitem"], [role="dialog"], [role="listbox"], [role="radio"], [class*="popover" i], [class*="dropdown" i], [class*="modal" i], [class*="sheet" i]';
      const seen = new Set();
      const out = [];
      for (const el of document.querySelectorAll(SEL)) {
        if (!vis(el)) continue;
        const t = norm(el.innerText);
        if (!t || t.length > 600) continue;
        const key = (el.getAttribute('role') || '') + '|' + (el.className || '').toString().slice(0, 60) + '|' + t.slice(0, 40);
        if (seen.has(key)) continue;
        seen.add(key);
        const r = el.getBoundingClientRect();
        out.push({
          role: el.getAttribute('role') || '',
          cls: (el.className || '').toString().replace(/\\s+/g, ' ').slice(0, 90),
          rect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
          text: t.slice(0, 400),
        });
      }
      // 菜单项逐条列出（更接近真实契约）
      const items = [...document.querySelectorAll('[role="menuitem"]')]
        .filter(vis)
        .map((el) => {
          const r = el.getBoundingClientRect();
          return {
            text: norm(el.innerText).slice(0, 40),
            aria: el.getAttribute('aria-label'),
            rect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
          };
        });
      return { overlays: out, menuItems: items };
    }"""
    )


def click_and_read(selector: str, label: str, settle: int = 2500) -> dict:
    el = page.locator(selector).first
    if el.count() == 0:
        return {"error": "trigger not found", "selector": selector}
    el.click(timeout=15_000)
    page.wait_for_timeout(settle)
    data = read_overlays()
    page.screenshot(path=f"/tmp/jimeng-794/{label}.png")
    # 收场：Escape 收起浮层，保证下一个触发器在干净态下被观察
    page.keyboard.press("Escape")
    page.wait_for_timeout(1200)
    return data


result = {}
for key, sel, label in [
    ("more", 'button[aria-label="更多"]', "more"),
    ("share", '[data-testid="canvas-share-trigger"]', "share"),
    ("project", '[data-testid="canvas-project-trigger"]', "project"),
    ("nodeSummary", '[data-testid="canvas-node-summary-trigger"]', "nodesummary"),
    ("title", '[data-testid="canvas-project-title-trigger"]', "title"),
]:
    result[key] = click_and_read(sel, label)
    print(f"===== {key} =====")
    print(json.dumps(result[key], ensure_ascii=False, indent=2)[:3000])
    print(flush=True)

print("===== SUMMARY =====")
for k, v in result.items():
    if v.get("error"):
        print(f"{k}: {v['error']}")
    else:
        mi = v.get("menuItems") or []
        ov = v.get("overlays") or []
        print(f"{k}: menuItems={len(mi)} overlays={len(ov)}")
        for i in mi[:14]:
            print(f"    - {i['text']!r} {i['rect']}")
        if not mi:
            for o in ov[:3]:
                print(f"    ~ {o['role']} {o['rect']} {o['text'][:160]!r}")
