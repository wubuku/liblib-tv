#!/usr/bin/env python3
"""batch 846 复刻侧探针：**Esc 关掉浮层之后，焦点回到哪**。

源站基线（`jimeng_probe846_focustrap2.py`，登录态 1512×950，每项各自重开层测）：

  · 右键菜单   canvas-context-menu       Esc 关掉，焦点落在「添加素材到时间线」
                                          —— **不回触发器**
  · 搜索面板   canvas-feature-panel      Esc 关掉，焦点回到 `canvas-panel-launcher`
                                          （**搜索**触发器）✓
  · 时间线全屏 timeline-fullscreen-editor Esc 关掉，焦点落在 `rf__wrapper`
                                          （画布 root，tabindex=0）—— 非触发器

注意源站**只有搜索面板做到了焦点归位**，另两层都没有。所以这一格的分档是
「层与层之间不一样」，不是一条统一判据 —— 记下来的是**事实对照**，不急着判缺陷。

口径与源站探针一致：每个测量**从重开的层起手**（Esc 是破坏性的，串着跑只有
第一个准）。复刻跑在 4317。
"""

import json

import jimeng_auth as auth  # noqa: F401  （与源站探针保持同一种运行方式）
from playwright.sync_api import sync_playwright

# URL 与 scripts/jimeng_unclickable_audit.py 一致（`/jimeng` 那一版进的是
# 门户页，浮层压根不存在 —— 「没打开」是前置态没成立，不是结果）
BASE = "http://localhost:4317"
URL = f"{BASE}/jimeng/canvas/demo"

FOCUS_JS = """() => {
  const a = document.activeElement;
  if (!a || a === document.body) return {who: 'body'};
  const r = a.getBoundingClientRect();
  return {who: a.tagName + '/' + ((a.getAttribute('data-testid')
            || a.getAttribute('aria-label')
            || (a.className || '').toString().replace(/\\s+/g, ' ').slice(0, 34))
            || (a.innerText || '').trim().slice(0, 14)),
          al: (a.getAttribute('aria-label') || '').trim().slice(0, 26),
          tid: a.getAttribute('data-testid') || '',
          w: Math.round(r.width), h: Math.round(r.height)};
}"""

LAYERS = [
    # (名字, 浮层 testid, 开层方式)
    ("顶栏·搜索", "jimeng-search-overlay", "search"),
    ("画布右键菜单", "canvas-context-menu", "context"),
    ("视频全屏预览", "video-fullscreen-preview", "fullscreen"),
]


def main() -> int:
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1680, "height": 1050})
        page = ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(9000)

        def in_layer(tid):
            return page.evaluate("""(tid) => {
              const l = document.querySelector(`[data-testid="${tid}"]`);
              return !!(l && l.contains(document.activeElement));
            }""", tid)

        def open_layer(kind):
            page.keyboard.press("Escape")
            page.wait_for_timeout(600)
            if page.locator('[data-testid="jimeng-search-overlay"]').count():
                return
            if kind == "search":
                btn = page.locator('button[aria-label="搜索"]')
                if not btn.count():
                    return
                btn.first.click(timeout=6000)
                page.wait_for_timeout(800)
            elif kind == "context":
                spot = page.evaluate("""() => {
                  for (const [x, y] of [[840, 700], [820, 740], [860, 660]]) {
                    const e = document.elementFromPoint(x, y);
                    if (!e) continue;
                    if (e.closest('[data-id]')) continue;
                    if (!e.closest('.react-flow__pane, .react-flow__renderer'))
                      continue;
                    return {x, y};
                  }
                  return null;
                }""")
                if not spot:
                    return
                page.mouse.click(spot["x"], spot["y"], button="right")
                page.wait_for_timeout(900)
            elif kind == "fullscreen":
                node = page.evaluate("""() => {
                  const n = document.querySelector('[data-id^=rf__node-video]');
                  if (!n) return null;
                  const r = n.getBoundingClientRect();
                  return {x: Math.round(r.x + r.width/2),
                          y: Math.round(r.y + r.height/2)};
                }""")
                if not node:
                    return
                page.mouse.click(node["x"], node["y"])
                page.wait_for_timeout(1200)
                btn = page.locator('button[aria-label="全屏预览"]')
                if not btn.count():
                    return
                btn.first.click(timeout=6000)
                page.wait_for_timeout(1800)

        out = {}
        for name, tid, kind in LAYERS:
            open_layer(kind)
            if not page.locator(f'[data-testid="{tid}"]').count():
                out[name] = {"skipped": "这一层没打开（前置态没成立）"}
                continue
            at_open = page.evaluate(FOCUS_JS)
            at_open["in"] = in_layer(tid)
            # Esc 之前**不**按 Tab / 方向键 —— 那些是破坏性的，会污染这一栏
            before = page.evaluate(FOCUS_JS)
            before["in"] = in_layer(tid)
            page.keyboard.press("Escape")
            page.wait_for_timeout(1000)
            after = page.evaluate(FOCUS_JS)
            after["in"] = in_layer(tid)
            closed = page.locator(f'[data-testid="{tid}"]').count() == 0
            out[name] = {"at_open": at_open, "before": before,
                         "after": after, "layer_closed": closed}

        print("\n\n===== 复刻：Esc 焦点归位（口径同源站探针）=====")
        for name, tid, kind in LAYERS:
            r = out[name]
            print("=" * 74)
            print(f"【{name}】tid={tid!r}")
            if r.get("skipped"):
                print("  SKIPPED:", r["skipped"])
                continue
            print("  开层瞬间焦点:", json.dumps(r["at_open"], ensure_ascii=False)[:210])
            print("  Esc 前焦点  :", json.dumps(r["before"], ensure_ascii=False)[:210])
            print("  Esc 后焦点  :", json.dumps(r["after"], ensure_ascii=False)[:210])
            print(f"  层关掉了={r['layer_closed']}")
        with open("/tmp/b846-clone-esc.json", "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print("\n明细 /tmp/b846-clone-esc.json")
        ctx.close()
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
