#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 828 探索②：画布上到底有几个「打开导演台」按钮、各属哪个节点；
以及刷新页面后哪些节点还在。"""
import json

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
    page.goto(f"{BASE}/?batch828=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__libtv_ui_store "
        "&& window.__director_store)", timeout=60_000)

    def buttons():
        return page.evaluate("""() => {
          const out=[];
          for(const b of document.querySelectorAll('[data-open-director]')){
            const host=b.closest('.react-flow__node');
            out.push({nodeId: host?host.getAttribute('data-id'):null,
                      hostTag: host?host.tagName:null});
          }
          return out;}""")

    print("初始按钮:", json.dumps(buttons(), ensure_ascii=False))
    print("初始节点:", page.evaluate(
        """() => window.__libtv_store.getState().getActiveCanvas().nodes
             .map(n=>({id:n.id, type:n.type, title:n.data&&n.data.title}))"""))

    page.evaluate("""() => {
      const s = window.__libtv_store.getState();
      s.addNode("script-execution", { title: "Batch 828" });
    }""")
    page.wait_for_timeout(1_500)
    print("加节点后按钮:", json.dumps(buttons(), ensure_ascii=False))
    print("加节点后节点:", page.evaluate(
        """() => window.__libtv_store.getState().getActiveCanvas().nodes
             .map(n=>({id:n.id, type:n.type, title:n.data&&n.data.title}))"""))

    page.reload(wait_until="networkidle")
    page.wait_for_timeout(3_000)
    print("刷新后按钮:", json.dumps(buttons(), ensure_ascii=False))
    print("刷新后节点:", page.evaluate(
        """() => window.__libtv_store.getState().getActiveCanvas().nodes
             .map(n=>({id:n.id, type:n.type, title:n.data&&n.data.title}))"""))
    browser.close()
