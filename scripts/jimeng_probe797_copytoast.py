"""batch 797 取证（补）：源站「复制项目」点下后到底有没有可见反馈（toast）。

上一次采样等了 2.6s，没抓到任何浮层 —— 可能是 toast 已消失、也可能本来就
静默。本脚本在点击后**高频轮询**页面新增文本/浮层，尽量把反馈抓准，
避免复刻时凭空发明一个 toast。

安全边界：只点「复制项目」（不在 BILLED_ACTIONS 内），不外发剪贴板内容。
"""

URL = (
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create"
)

page.set_viewport_size({"width": 1680, "height": 826})
page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
page.wait_for_timeout(11_000)

# 在页面里装一个高频采样器：记录 body 文本的新增片段与新出现的浮层
page.evaluate(
    """() => {
  window.__seen = new Set();
  window.__events = [];
  const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
  window.__poll = setInterval(() => {
    try {
      const vis = (el) => { const r = el.getBoundingClientRect();
        if (r.width < 1 || r.height < 1) return false;
        for (let p = el; p; p = p.parentElement) {
          const s = getComputedStyle(p);
          if (s.visibility === 'hidden' || s.display === 'none') return false;
        }
        return true; };
      const SEL = '[role="alert"],[role="status"],[class*="toast" i],[class*="Toast" i],'
                + '[class*="message" i],[class*="Message" i],[class*="snackbar" i],'
                + '[class*="tip" i],[class*="hint" i],[class*="notice" i]';
      for (const el of document.querySelectorAll(SEL)) {
        if (!vis(el)) continue;
        const t = norm(el.innerText);
        if (!t) continue;
        const key = (el.className||'').toString().slice(0,50) + '|' + t.slice(0,40);
        if (window.__seen.has(key)) continue;
        window.__seen.add(key);
        const r = el.getBoundingClientRect();
        window.__events.push({ at: Date.now(), text: t.slice(0,120),
          cls: (el.className||'').toString().replace(/\\s+/g,' ').slice(0,90),
          rect: {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)} });
      }
    } catch (e) { /* 忽略 */ }
  }, 120);
}"""
)

page.locator('[aria-label="更多"], [aria-label="More"]').first.click(timeout=15_000)
page.wait_for_timeout(1000)
page.get_by_text("复制项目", exact=False).first.click(timeout=15_000)

page.wait_for_timeout(4000)
events = page.evaluate("() => { clearInterval(window.__poll); return window.__events; }")
print("捕获到的浮层/toast 事件数:", len(events))
for e in events:
    print(f"  {e['rect']} cls={e['cls'][:70]}")
    print(f"    TEXT: {e['text']!r}")

page.screenshot(path="/tmp/jimeng-794/source-copy-poll.png")
print("shot -> /tmp/jimeng-794/source-copy-poll.png")
