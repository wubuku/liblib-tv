import json, re
from playwright.sync_api import sync_playwright

CHIP_RE = re.compile(r"([^·\s]+)\s*·\s*([^·\s]+)\s*·\s*([0-9.]+s)\s*·\s*([0-9]+)个\s*(?:·\s*)?([0-9]+|-)")

def native_click(page, x, y):
    page.mouse.move(x, y); page.wait_for_timeout(110)
    page.mouse.down(); page.wait_for_timeout(55); page.mouse.up()

def ensure_footer(page):
    ok = page.evaluate("""() => {
        const n = document.querySelector('.react-flow__node');
        return !!n && /文生视频|图生视频/.test(n.innerText || '');
    }""")
    if ok:
        return True
    c = page.evaluate("""() => {
        const n = document.querySelector('.react-flow__node');
        if (!n) return null;
        const r = n.getBoundingClientRect();
        return { x: r.x + Math.min(r.width/2, 180), y: r.y + 30 };
    }""")
    if not c:
        return False
    native_click(page, c["x"], c["y"])
    page.wait_for_timeout(800)
    return True

def read(page):
    raw = page.evaluate("""() => {
        const n = document.querySelector('.react-flow__node');
        return (n && n.innerText || '').replace(/\\n/g, ' ');
    }""")
    m = CHIP_RE.search(raw)
    return m.groups() if m else None

def open_settings(page):
    if not ensure_footer(page):
        return False
    chip = page.evaluate("""() => {
        const b = [...document.querySelectorAll('.react-flow__node button')].find(b => /个/.test(b.innerText || '') && /·/.test(b.innerText || ''));
        if (!b) return null;
        const r = b.getBoundingClientRect();
        return { x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2) };
    }""")
    if not chip:
        return False
    native_click(page, chip["x"], chip["y"])
    page.wait_for_timeout(900)
    return True

def click_option(page, text):
    opt = page.evaluate("""(t) => {
        const els = [...document.querySelectorAll('body *')].filter(el => {
            const x = (el.innerText || '').trim();
            const r = el.getBoundingClientRect();
            return x === t && r.width > 0 && r.height > 10 && r.height < 60 && el.children.length === 0;
        });
        if (!els.length) return null;
        const r = els[els.length - 1].getBoundingClientRect();
        return { x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2) };
    }""", text)
    if not opt:
        return False
    native_click(page, opt["x"], opt["y"])
    page.wait_for_timeout(1100)
    return True

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next(pg for pg in ctx.pages if "liblib.tv" in pg.url)
    page.bring_to_front()
    page.set_viewport_size({"width": 1920, "height": 1150})
    page.wait_for_timeout(800)
    results = {}
    for label, reso, dur in [("480P/5s", "480P", None), ("720P/5s", "720P", None), ("720P/10s", None, "10s"), ("back to 5s", None, "5s")]:
        if not open_settings(page):
            results[label] = "settings open failed"; continue
        ok = True
        if reso:
            ok = click_option(page, reso)
        if ok and dur:
            ok = click_option(page, dur)
        if not ok:
            results[label] = "option missing"
            page.keyboard.press("Escape"); page.wait_for_timeout(400)
            continue
        page.wait_for_timeout(700)
        results[label] = read(page)
        page.keyboard.press("Escape"); page.wait_for_timeout(500)
    print(json.dumps(results, ensure_ascii=False, indent=1))
    browser.close()
