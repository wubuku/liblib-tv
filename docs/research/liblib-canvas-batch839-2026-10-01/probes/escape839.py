#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 839 诊断：到底是谁在 Escape 时关掉了**面板**。

★ 现象：clone 的「查看角色资产」→ 资产视图打开 ⟹ 按 Esc ⟹ **资产视图和整个面板都没了**。
★ 期望：Esc 只关资产视图（clone 决策）。

★ 本脚本只做定位：
  1. 在页面里装三个监听器（capture-window / bubble-window / document），
     记录每次 keydown 的 `defaultPrevented` ＋ 各自的顺序；
  2. 读 `uiStore.activePrimaryPanel`（面板开 ⟹ 它是 "character"）；
  3. 按 Esc 前后各读一次。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path("/tmp/b839-escape-diag.json")

INSTRUMENT = """() => {
  window.__b839_log = [];
  window.__b839_mark = 'X-' + Date.now();
  window.__b839_unload = 0;
  window.addEventListener('beforeunload', () => { window.__b839_unload++; });
  const tag = (e) => e.type + '/' + (e.eventPhase === 1 ? 'capture' :
                    e.eventPhase === 3 ? 'bubble' : 'at') + '/' + e.key;
  window.addEventListener('keydown', (e) => {
    window.__b839_log.push({who:'window-capture', tag:tag(e),
      prevented:e.defaultPrevented, target:(e.target&&e.target.tagName)||''});
  }, true);
  window.addEventListener('keydown', (e) => {
    window.__b839_log.push({who:'window-bubble', tag:tag(e),
      prevented:e.defaultPrevented});
  });
  document.addEventListener('keydown', (e) => {
    window.__b839_log.push({who:'document-bubble', tag:tag(e),
      prevented:e.defaultPrevented});
  });
  return true;
}"""

STATE = """() => {
  const u = window.__libtv_store && window.__libtv_store.getState
    ? window.__libtv_store.getState() : null;
  return {
    有面板: Boolean(document.querySelector('[data-character-studio]')),
    有资产视图: Boolean(document.querySelector('[data-character-studio-asset-view]')),
    activePrimaryPanel: u ? u.activePrimaryPanel : '(读不到 uiStore)',
    页面标记还在: typeof window.__b839_mark === 'string',
    beforeunload次数: window.__b839_unload,
    日志: window.__b839_log || [],
  };
}"""


def main():
    out = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport={"width": 1920, "height": 1080}, locale="zh-CN")
        pg = ctx.new_page()
        pg.goto(BASE + "/?batch839esc=1", wait_until="domcontentloaded")
        pg.wait_for_timeout(3000)
        pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
        pg.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
        pg.evaluate("""() => {
          const b=[...document.querySelectorAll('button')].find(
            e=>e.getAttribute('aria-label')==='角色造型室');
          if(b)b.click();}""")
        pg.wait_for_timeout(1200)
        pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
        pg.evaluate("""() => {
          const t=[...document.querySelectorAll('[data-character-studio-tab]')]
            .find(e=>e.getAttribute('data-character-studio-tab')==='official');
          if(t)t.click();}""")
        pg.wait_for_timeout(600)
        pg.evaluate("""() => {
          const c=document.querySelector('[data-character-strip-card]');
          if(c)c.click();}""")
        pg.wait_for_timeout(500)
        bb = pg.evaluate("""() => {
          const e=document.querySelector('[data-character-studio-view-assets]');
          if(!e)return null; const r=e.getBoundingClientRect();
          return {x:r.x,y:r.y,w:r.width,h:r.height};}""")
        if bb:
            pg.mouse.move(bb["x"] + bb["w"] / 2, bb["y"] + bb["h"] / 2)
            pg.wait_for_timeout(700)
            pg.mouse.click(bb["x"] + bb["w"] / 2, bb["y"] + bb["h"] / 2)
            pg.wait_for_timeout(800)
        pg.evaluate(INSTRUMENT)
        out["按Esc前"] = pg.evaluate(STATE)
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(800)
        out["按Esc后"] = pg.evaluate(STATE)
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
