"""968b 纯读：复刻 out 段第 17 个停靠点 `NEXTJS-PORTAL` 到底是什么。

⛔ 纯读：不点、不按键、不 reload、不写 prototype。
"""
import json

import playwright.sync_api as pw

URL = "http://localhost:4317/jimeng/canvas/demo"
OUT = "/tmp/b968b-nextjsportal.json"

JS = """() => {
  const els = Array.from(document.querySelectorAll('nextjs-portal'));
  return {
    n: els.length,
    detail: els.map((e) => {
      const r = e.getBoundingClientRect();
      return {
        tag: e.tagName,
        ti: e.getAttribute('tabindex'),
        has_tabindex: e.hasAttribute('tabindex'),
        aria: e.getAttribute('aria-label'),
        parent_tag: e.parentElement ? e.parentElement.tagName : null,
        n_children: e.childElementCount,
        inner_html_head: (e.innerHTML || '').slice(0, 160),
        rect: [Math.round(r.x), Math.round(r.y),
               Math.round(r.width), Math.round(r.height)],
        is_focusable: e.tabIndex >= 0,
        body_last_child_tag: document.body.lastElementChild
          ? document.body.lastElementChild.tagName : null,
      };
    }),
  };
}"""

with pw.sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_context(viewport={"width": 1512, "height": 1200}).new_page()
    page.goto(URL, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(7000)
    out = {"question": "复刻 out 段第 17 个停靠点 `NEXTJS-PORTAL` 是"
                         "**复刻自己的实现**还是 **Next.js 开发态注入的**？",
           "pure_read": True}
    out["raw"] = page.evaluate(JS)
    b.close()

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(json.dumps(out, ensure_ascii=False, indent=2))
