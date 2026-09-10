import json, os, re, time
from playwright.sync_api import sync_playwright

OUT = "/tmp/probe332_log5.json"
SHOTS = "/tmp/probe332_shots5"
os.makedirs(SHOTS, exist_ok=True)
CHIP_RE = re.compile(r"([^·\s]+)\s*·\s*([^·\s]+)\s*·\s*([0-9.]+s)\s*·\s*([0-9]+)个\s*(?:·\s*)?([0-9]+|-)")
CHIP_RE_OMNI = re.compile(r"(自适应)\s*·\s*([0-9]+)个\s*(?:·\s*)?([0-9]+|-)")
LOG = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "models": {}}

PLAN = [
    ("OmniHuman 1.5", False, False, 0),
    ("Hailuo 2.3", True, True, 0),
    ("Hailuo 2.3 Fast", True, True, 0),
    ("Kling 2.6", False, True, 1),
    ("Hailuo 2.3 Fast", True, True, 1),
    ("Happy Horse 1.1", True, True, 0),
    ("Happy Horse 1.0", True, True, 0),
    ("Wan 3.0", True, True, 0),
    ("Wan 2.7", True, True, 0),
    ("Pixverse V5", True, True, 0),
    ("Vidu Q2 Pro", True, True, 0),
    ("Vidu Q2", True, True, 1),
    ("Minimax H3 Max", False, True, 0),
    ("Seedance 1.0 Pro", False, True, 0),
    ("Seedance 1.0 Lite", False, True, 0),
]

JS_TRIGGER = """() => {
    const spans = [...document.querySelectorAll('.react-flow__node span.text-fg-default')];
    for (const s of spans) {
        const t = (s.innerText || '').trim();
        if (!t) continue;
        let el = s;
        for (let i = 0; i < 4 && el; i++) {
            el = el.parentElement;
            if (el && el.tagName === 'BUTTON') {
                const r = el.getBoundingClientRect();
                if (r.width > 30 && r.height > 20) return { x: r.x + r.width/2, y: r.y + r.height/2, label: t };
            }
        }
    }
    return null;
}"""

def native_click(page, x, y):
    page.mouse.move(x, y); page.wait_for_timeout(110)
    page.mouse.down(); page.wait_for_timeout(55); page.mouse.up()

def ensure_footer(page):
    for _ in range(3):
        ok = page.evaluate("""() => {
            const n = document.querySelector('.react-flow__node');
            return !!n && (n.innerText || '').length > 120;
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
        page.wait_for_timeout(900)
    return False

def read(page):
    if not ensure_footer(page):
        return None, ""
    raw = page.evaluate("""() => {
        const n = document.querySelector('.react-flow__node');
        return (n && n.innerText || '').replace(/\\n/g, ' ');
    }""")
    m = CHIP_RE.search(raw) or CHIP_RE_OMNI.search(raw)
    return (m.groups() if m else None), raw

def open_settings(page):
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
    page.wait_for_timeout(1200)
    return True

def select_model(page, model, entry):
    if not ensure_footer(page):
        entry["error"] = "no node/footer"
        return False
    trig = page.evaluate(JS_TRIGGER)
    if not trig:
        entry["error"] = "trigger not found"
        return False
    native_click(page, trig["x"], trig["y"])
    page.wait_for_timeout(1000)
    row = None
    for attempt in range(3):
        row = page.evaluate("""(name) => {
            const cands = [...document.querySelectorAll('body *')].filter(el => {
                const t = (el.innerText || '').trim();
                const r = el.getBoundingClientRect();
                return r.width > 0 && t === name && el.children.length === 0 && r.width < 250;
            });
            if (!cands.length) return null;
            let el = cands[0];
            while (el) {
                const r = el.getBoundingClientRect();
                if (r.height >= 40 && r.height <= 62 && r.width >= 300 && r.width <= 400) {
                    return { x: r.x + r.width/2, y: r.y + r.height/2 };
                }
                el = el.parentElement;
            }
            return null;
        }""", model)
        if row and 40 <= row["y"] <= 1120:
            break
        page.evaluate("""(name) => {
            const cands = [...document.querySelectorAll('body *')].filter(el => (el.innerText || '').trim() === name && el.children.length === 0);
            if (cands.length) cands[0].scrollIntoView({ block: 'center' });
        }""", model)
        page.wait_for_timeout(600)
    if not row:
        entry["error"] = "row missing"
        return False
    native_click(page, row["x"], row["y"])
    page.wait_for_timeout(1000)
    last = None
    for _ in range(12):
        chip, _raw = read(page)
        trig2 = page.evaluate("""() => {
            const s = document.querySelector('.react-flow__node span.text-fg-default');
            return s ? (s.innerText || '').trim() : null;
        }""")
        if trig2 == model and chip:
            if last == chip[-1]:
                return True
            last = chip[-1]
        page.wait_for_timeout(350)
    chip, _ = read(page)
    entry["warn_trigger"] = page.evaluate("""() => {
        const s = document.querySelector('.react-flow__node span.text-fg-default');
        return s ? (s.innerText || '').trim() : null;
    }""")
    return bool(chip)

def save(log):
    with open(OUT, "w") as f:
        json.dump(log, f, ensure_ascii=False, indent=1)

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next(pg for pg in ctx.pages if "liblib.tv" in pg.url)
    page.bring_to_front()
    page.set_viewport_size({"width": 1920, "height": 1150})
    page.wait_for_timeout(800)
    for model, w720, w5s, pas in PLAN:
        key = f"{model}#p{pas}" if pas else model
        entry = {"name": model, "pass": pas}
        try:
            if select_model(page, model, entry):
                norms = []
                if w720:
                    if open_settings(page) and click_option(page, "720P"):
                        norms.append("720P")
                if w5s:
                    if open_settings(page) and click_option(page, "5s"):
                        norms.append("5s")
                entry["normalize"] = norms
                chip, raw = read(page)
                page.wait_for_timeout(700)
                chip2, _ = read(page)
                entry["chip"] = chip
                entry["chip_second"] = chip2
                entry["stable"] = chip == chip2 and chip is not None
                entry["raw_tail"] = raw[-160:]
                shot = f"{SHOTS}/{key.replace(' ', '_')}.png"
                page.screenshot(path=shot)
                entry["shot"] = shot
        except Exception as e:
            entry["error"] = (entry.get("error") or "") + "|" + str(e)[:140]
        LOG["models"][key] = entry
        save(LOG)
        print(f"{key:22} -> {json.dumps(entry.get('chip'), ensure_ascii=False)} stable={entry.get('stable')} norm={entry.get('normalize')} {entry.get('error','')}", flush=True)
    browser.close()
print("DONE")
