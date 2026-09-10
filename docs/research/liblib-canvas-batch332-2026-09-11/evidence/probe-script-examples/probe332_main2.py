import json, os, re, time
from playwright.sync_api import sync_playwright

OUT = "/tmp/probe332_log2.json"
SHOTS = "/tmp/probe332_shots2"
os.makedirs(SHOTS, exist_ok=True)
LOG = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "models": {}}

MODELS = [
    "Wan 2.6", "Wan 2.2", "Kling 3.0", "Kling 2.6", "Kling 2.5",
    "Kling O1", "Pixverse V5.5", "Hailuo 2.3 Fast", "OmniHuman 1.5",
    "Hailuo 2.3", "Wan 2.7", "Vidu Q2 Pro", "Vidu Q2 Turbo",
    "Happy Horse 1.1", "Minimax H3", "Wan 3.0", "Vidu Q2",
    "Pixverse V5", "Kling O3",
]

CHIP_RE = re.compile(r"([0-9:]+)\s*·\s*([^·\s]+)\s*·\s*([0-9.]+s)\s*·\s*([0-9]+)个\s*(?:·\s*)?([0-9]+)")

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

JS_NODE_CENTER = """() => {
    const n = document.querySelector('.react-flow__node');
    if (!n) return null;
    const r = n.getBoundingClientRect();
    return { x: r.x + Math.min(r.width/2, 220), y: Math.max(60, r.y + 40) };
}"""

JS_FIND_ROW = """(name) => {
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
}"""

JS_SCROLL_ROW = """(name) => {
    const cands = [...document.querySelectorAll('body *')].filter(el => {
        const t = (el.innerText || '').trim();
        return t === name && el.children.length === 0;
    });
    if (!cands.length) return false;
    cands[0].scrollIntoView({ block: 'center' });
    return true;
}"""

JS_READ_FOOTER = """() => {
    const n = document.querySelector('.react-flow__node');
    if (!n) return null;
    const txt = (n.innerText || '').replace(/\\n/g, ' ');
    const trig = document.querySelector('.react-flow__node span.text-fg-default');
    return {
        trigger: trig ? (trig.innerText || '').trim() : null,
        raw: txt.slice(0, 500),
    };
}"""

def native_click(page, x, y):
    page.mouse.move(x, y)
    page.wait_for_timeout(110)
    page.mouse.down()
    page.wait_for_timeout(55)
    page.mouse.up()

def parse(read):
    m = CHIP_RE.search(read["raw"] or "")
    if not m:
        return None
    return {"ratio": m.group(1), "res": m.group(2), "dur": m.group(3), "count": m.group(4), "credits": m.group(5)}

def ensure_node_selected(page):
    t = page.evaluate(JS_TRIGGER)
    if t:
        return t
    c = page.evaluate(JS_NODE_CENTER)
    if c:
        native_click(page, c["x"], c["y"])
        page.wait_for_timeout(700)
    return page.evaluate(JS_TRIGGER)

def read_model(page, model, entry):
    trig = ensure_node_selected(page)
    if not trig:
        entry["error"] = "trigger not found after recovery"
        return False
    native_click(page, trig["x"], trig["y"])
    page.wait_for_timeout(900)
    row = None
    for attempt in range(3):
        row = page.evaluate(JS_FIND_ROW, model)
        if row and 40 <= row["y"] <= 815:
            break
        page.evaluate(JS_SCROLL_ROW, model)
        page.wait_for_timeout(550)
        row = page.evaluate(JS_FIND_ROW, model)
        if row and 40 <= row["y"] <= 815:
            break
        page.wait_for_timeout(400)
    if not row:
        entry["error"] = "row missing"
        page.keyboard.press("Escape"); page.wait_for_timeout(400)
        return False
    if not (40 <= row["y"] <= 815):
        entry["error"] = f"row offscreen y={row['y']}"
        page.keyboard.press("Escape"); page.wait_for_timeout(400)
        return False
    native_click(page, row["x"], row["y"])
    page.wait_for_timeout(900)
    # wait for trigger == model and credits stable
    last_credits = None
    final = None
    for _ in range(12):
        r = page.evaluate(JS_READ_FOOTER)
        chip = parse(r)
        if r["trigger"] == model and chip:
            if last_credits == chip["credits"]:
                final = (r, chip)
                break
            last_credits = chip["credits"]
        page.wait_for_timeout(350)
    if not final:
        r = page.evaluate(JS_READ_FOOTER)
        chip = parse(r)
        final = (r, chip)
    entry["read"] = final[0]
    entry["chip"] = final[1]
    shot = f"{SHOTS}/{model.replace(' ', '_')}.png"
    page.screenshot(path=shot)
    entry["shot"] = shot
    return True

def save(log):
    with open(OUT, "w") as f:
        json.dump(log, f, ensure_ascii=False, indent=1)

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next(pg for pg in ctx.pages if "liblib.tv" in pg.url)
    page.bring_to_front()
    page.wait_for_timeout(600)
    for model in MODELS:
        entry = {"name": model}
        try:
            ok = read_model(page, model, entry)
        except Exception as e:
            entry["error"] = str(e)[:200]
            ok = False
        LOG["models"][model] = entry
        save(LOG)
        status = entry.get("error") or json.dumps(entry.get("chip"), ensure_ascii=False)
        print(f"{model:18} -> {status}", flush=True)
    browser.close()
print("DONE")
