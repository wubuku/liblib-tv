#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断：1280×1150 视口下，为什么 [data-director-object-name] 不存在？"""
import json

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:4317"

SEL_CAMERA = """() => {
  const s = window.__director_store.getState();
  const c = s.objects.find((o) => o.kind === 'camera');
  const row = document.querySelector('[data-director-tree] [role="treeitem"]'
    + '[data-director-object-id="' + c.id + '"]');
  if (!row) return { ok: false, stage: 'no-row' };
  row.click();
  return { ok: window.__director_store.getState().selectedObjectId === c.id };
}"""

PROBE = """() => {
  const tree = document.querySelector('[data-director-tree]');
  const items = document.querySelectorAll('[data-director-tree] [role="treeitem"]');
  const names = document.querySelectorAll('[data-director-object-name]');
  const ws = document.querySelector('[data-director-workspace]');
  const cam = window.__director_store.getState().objects.find((o) => o.kind === 'camera');
  const row = cam ? document.querySelector('[data-director-tree] [role="treeitem"]'
    + '[data-director-object-id="' + cam.id + '"]') : null;
  return {
    treeExists: !!tree,
    treeItems: items.length,
    nameFields: names.length,
    camId: cam ? cam.id : null,
    camRowExists: !!row,
    camRowText: row ? (row.textContent || '').slice(0, 30) : null,
    selectedObjectId: window.__director_store.getState().selectedObjectId,
    workspaceClass: ws ? ws.className : null,
    innerWidth: window.innerWidth, innerHeight: window.innerHeight,
  };
}"""


def run(width, height):
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        page = br.new_page(viewport={"width": width, "height": height},
                           device_scale_factor=1)
        page.goto(f"{BASE_URL}/?diag709=1", wait_until="networkidle", timeout=90_000)
        page.wait_for_function(
            "() => Boolean(window.__libtv_store && window.__libtv_ui_store "
            "&& window.__director_store)", timeout=60_000)
        page.wait_for_timeout(800)
        nid = page.evaluate("""() => {
          const nodes = window.__libtv_store.getState().getActiveCanvas().nodes
            .filter((n) => n.type === 'script-execution');
          return nodes.length === 1 ? nodes[0].id : null;
        }""")
        page.locator('.react-flow__node[data-id="%s"] [data-open-director]' % nid).first.click()
        page.locator("[data-director-workspace]").wait_for(state="visible", timeout=30_000)
        page.wait_for_timeout(1_800)
        page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
        page.mouse.move(5, 5)
        page.wait_for_timeout(300)
        before = page.evaluate(PROBE)
        sel = page.evaluate(SEL_CAMERA)
        page.wait_for_timeout(800)
        after = page.evaluate(PROBE)
        br.close()
        return {"viewport": [width, height], "before": before, "sel": sel, "after": after}


if __name__ == "__main__":
    for w, h in ((1280, 1150), (1920, 1080)):
        print(json.dumps(run(w, h), ensure_ascii=False, indent=1))
