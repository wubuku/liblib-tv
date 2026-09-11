#!/usr/bin/env python3
"""Source recovery probe (BLOCKED_SOURCE re-test trigger).

Run: ~/.venvs/liblib-harness/bin/python scripts/probe-source-recovery.py
Output line `RECOVERY: menu-opens` = source model menu recovered
(proceed with BLOCKED_SOURCE sampling per
docs/research/LIBTV_SOURCE_FRESHNESS_REINSPECTION.md §10.3);
`RECOVERY: still-broken` = keep waiting. Requires the CDP browser on
port 9222 with the logged-in liblib.tv session (user-approved).

Probes: reload canvas -> create a fresh video node via the add-node
menu -> click the model trigger up to 3 times -> check for the
`Seedance 2.5` menu row text.
"""

import json
from playwright.sync_api import sync_playwright

def native_click(page, x, y):
    page.mouse.move(x, y); page.wait_for_timeout(110)
    page.mouse.down(); page.wait_for_timeout(55); page.mouse.up()

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next(pg for pg in ctx.pages if "liblib.tv" in pg.url)
    page.bring_to_front()
    page.goto("https://www.liblib.tv/canvas?spaceId=7709759&projectId=a860e1da8e9e4504bececda022386429", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(20000)
    page.set_viewport_size({"width": 1920, "height": 1150})
    page.wait_for_timeout(1500)
    c = page.evaluate("""() => {
        const ns = document.querySelectorAll('.react-flow__node');
        const n = ns[ns.length - 1];
        if (!n) return null;
        const r = n.getBoundingClientRect();
        return { x: r.x + Math.min(r.width/2, 180), y: r.y + 30 };
    }""")
    if c:
        native_click(page, c["x"], c["y"]); page.wait_for_timeout(1200)
    opened = False
    for attempt in range(3):
        trig = page.evaluate("""() => {
            const ns = document.querySelectorAll('.react-flow__node');
            const n = ns[ns.length - 1];
            if (!n) return null;
            const spans = [...n.querySelectorAll('span')].filter(s => (s.className || '').toString().includes('text-fg-default'));
            for (const s of spans) {
                const t = (s.innerText || '').trim();
                if (!t || t.includes('·')) continue;
                let el = s;
                for (let i = 0; i < 4 && el; i++) {
                    el = el.parentElement;
                    if (el && el.tagName === 'BUTTON') {
                        const r = el.getBoundingClientRect();
                        if (r.width > 30) return { x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2) };
                    }
                }
            }
            return null;
        }""")
        if not trig:
            page.wait_for_timeout(1500); continue
        native_click(page, trig["x"], trig["y"])
        page.wait_for_timeout(1700)
        if page.evaluate("() => document.body.innerText.includes('Seedance 2.5')"):
            opened = True; break
        native_click(page, trig["x"], trig["y"])
        page.wait_for_timeout(1700)
        if page.evaluate("() => document.body.innerText.includes('Seedance 2.5')"):
            opened = True; break
    print("RECOVERY:", "menu-opens" if opened else "still-broken", flush=True)
    browser.close()
