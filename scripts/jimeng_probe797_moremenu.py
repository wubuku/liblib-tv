"""batch 797 取证：源站顶栏「更多」→ 项目信息 / 复制项目 两个动作的实际行为。

batch 795 复刻了菜单外观（200×84 / 两项 192×36 / 文案逐字），但两个动作
目前是**空实现**（无回调）。本脚本采样源站点它们之后发生什么。

安全边界：
  - 「项目信息」「复制项目」都不在 scripts/jimeng_auth.py 的 BILLED_ACTIONS 里，
    不提交生成任务、不消耗积分。
  - 「复制项目」若写剪贴板属只读副作用，不外发。
  - 不点任何确认/提交类按钮；弹出一层就抓结构，Escape 收场。
"""

import json

URL = (
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create"
)

page.set_viewport_size({"width": 1680, "height": 826})
page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
page.wait_for_timeout(11_000)


def snapshot(tag: str) -> dict:
    return page.evaluate(
        """(tag) => {
      const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
      const vis = (el) => { const r = el.getBoundingClientRect();
        if (r.width < 1 || r.height < 1) return false;
        for (let p = el; p; p = p.parentElement) {
          const s = getComputedStyle(p);
          if (s.visibility === 'hidden' || s.display === 'none') return false;
        }
        return true; };
      const SEL = '[role="dialog"],[role="menu"],[class*="popover" i],[class*="modal" i],'
                + '[class*="sheet" i],[class*="drawer" i],[class*="toast" i],[class*="message" i]';
      const seen = new Set(); const overlays = [];
      for (const el of document.querySelectorAll(SEL)) {
        if (!vis(el)) continue;
        const t = norm(el.innerText);
        if (!t || t.length > 500) continue;
        const key = (el.getAttribute('role')||'') + '|' + t.slice(0, 40);
        if (seen.has(key)) continue;
        seen.add(key);
        const r = el.getBoundingClientRect();
        overlays.push({ role: el.getAttribute('role') || '',
                        cls: (el.className||'').toString().replace(/\\s+/g,' ').slice(0,80),
                        rect: {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)},
                        text: t.slice(0, 400) });
      }
      return { tag, overlays,
               dialogs: [...document.querySelectorAll('[role="dialog"]')].filter(vis).length };
    }""",
        tag,
    )


out = {}

# ── 项目信息 ──
page.locator('[aria-label="更多"], [aria-label="More"]').first.click(timeout=15_000)
page.wait_for_timeout(1200)
out["menu_open"] = snapshot("menu-open")
page.get_by_text("项目信息", exact=False).first.click(timeout=15_000)
page.wait_for_timeout(2600)
out["after_项目信息"] = snapshot("after-project-info")
page.screenshot(path="/tmp/jimeng-794/source-project-info.png")
page.keyboard.press("Escape")
page.wait_for_timeout(1500)
out["after_esc"] = snapshot("after-esc")

# ── 复制项目（读剪贴板，不外发）──
try:
    page.locator('[aria-label="更多"], [aria-label="More"]').first.click(timeout=15_000)
    page.wait_for_timeout(1200)
    page.get_by_text("复制项目", exact=False).first.click(timeout=15_000)
    page.wait_for_timeout(2600)
    out["after_复制项目"] = snapshot("after-copy-project")
    try:
        clip = page.evaluate("() => navigator.clipboard.readText().catch(() => null)")
    except Exception as e:  # noqa: BLE001
        clip = f"<unreadable: {str(e)[:80]}>"
    out["clipboard"] = (clip or "")[:200]
    page.screenshot(path="/tmp/jimeng-794/source-copy-project.png")
except Exception as e:  # noqa: BLE001
    out["copy_error"] = str(e)[:200]

print(json.dumps(out, ensure_ascii=False, indent=2)[:6000])
