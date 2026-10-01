"""batch 795 取证（候选）：源站「与 AI 对话」抽屉的默认态与 z 层级。

要回答两个问题：
  1. 源站该抽屉**默认展开**吗？（复刻 batch 398 记为「常驻/默认开」，
     但 2026-10-01 的顶栏快照里只见到「与 AI 对话」控件，没有展开的抽屉。）
  2. 抽屉展开后会不会遮住顶栏右簇？源站的 z 层级如何？
     （复刻抽屉 inset-y-3 z-40 会盖住顶栏分享/更多/积分三钮。）

安全边界：只点「与 AI 对话」这一个入口，不输入、不发送，不触发任何计费动作。
「发送消息」在 scripts/jimeng_auth.py 的 BILLED_ACTIONS 里，本脚本绝不点击。
"""

import json

URL = (
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create"
)

page.set_viewport_size({"width": 1680, "height": 826})
page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
page.wait_for_timeout(11_000)


def probe(tag: str) -> dict:
    return page.evaluate(
        """(tag) => {
      const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
      const rect = (el) => { const r = el.getBoundingClientRect();
        return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; };
      const zOf = (el) => {
        for (let p = el; p; p = p.parentElement) {
          const z = getComputedStyle(p).zIndex;
          if (z && z !== 'auto') return z;
        }
        return 'auto';
      };
      // 抽屉：找带「与 AI 对话」可访问名的 aside/dialog，或右下方宽面板
      const drawers = [...document.querySelectorAll('aside,[role="dialog"],[role="complementary"]')]
        .filter((el) => { const r = el.getBoundingClientRect();
          return r.width > 200 && r.height > 200 && r.x > 700; })
        .map((el) => ({ aria: el.getAttribute('aria-label'), cls: (el.className||'').toString().slice(0,80),
                        z: zOf(el), rect: rect(el), text: norm(el.innerText).slice(0, 90) }));
      // 顶栏三个控件命中测试：中心点最上层元素是谁
      const hit = (sel) => {
        const el = document.querySelector(sel);
        if (!el) return { sel, missing: true };
        const r = el.getBoundingClientRect();
        const top = document.elementFromPoint(r.x + r.width/2, r.y + r.height/2);
        return { sel, rect: rect(el), z: zOf(el),
                 topTag: top ? top.tagName.toLowerCase() : null,
                 topAria: top ? (top.getAttribute('aria-label') || (top.closest('[aria-label]')?.getAttribute('aria-label'))) : null,
                 selfHit: top ? !!top.closest('[data-testid="canvas-share-trigger"],[data-testid="canvas-commerce-entry"],[data-testid="canvas-more-trigger"]') : false };
      };
      const entry = [...document.querySelectorAll('button,[role="button"]')]
        .map((e) => ({ e, t: norm(e.innerText), a: e.getAttribute('aria-label') || '' }))
        .find((x) => x.t.includes('与 AI 对话') || x.a.includes('与 AI 对话'));
      return { tag, drawers, entryFound: !!entry,
               entry: entry ? { text: entry.t, aria: entry.a, rect: rect(entry.e), z: zOf(entry.e) } : null,
               hits: [hit('[data-testid="canvas-share-trigger"]'),
                      hit('[data-testid="canvas-more-trigger"]'),
                      hit('[data-testid="canvas-commerce-entry"]')] };
    }""",
        tag,
    )


before = probe("before")
print("=== 载入后（未点任何东西）===")
print(json.dumps(before, ensure_ascii=False, indent=2)[:2600])

if before.get("entry"):
    # 点开抽屉
    # 该入口只有 aria-label、没有可见文本，get_by_text 命中不到
    page.locator('[aria-label="与 AI 对话"]').first.click(timeout=15_000)
    page.wait_for_timeout(3000)
    after = probe("after-open")
    print("\n=== 点开「与 AI 对话」后 ===")
    print(json.dumps(after, ensure_ascii=False, indent=2)[:3200])
    page.screenshot(path="/tmp/jimeng-794/source-agent-open.png")
    print("\nshot -> /tmp/jimeng-794/source-agent-open.png")
else:
    print("\n未找到「与 AI 对话」入口")
