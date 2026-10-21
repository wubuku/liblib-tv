#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断：方向键手势的焦点到底在哪个元素上？什么操作会让它失焦（从而提交手势）？"""
import json
import pathlib

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:4317"
VIEWPORT = {"width": 1920, "height": 1080}

ACTIVE = """() => {
  const a = document.activeElement;
  if (!a) return null;
  const d = {};
  for (const k of a.attributes || []) {
    if (k.name.startsWith('data-') || k.name === 'class' || k.name === 'role'
        || k.name === 'id' || k.name === 'type') d[k.name] = k.value;
  }
  return {tag: a.tagName, text: (a.textContent || '').slice(0, 40), attrs: d};
}"""

STATE = """() => {
  const s = window.__director_store.getState();
  const cam = s.objects.find((o) => o.kind === 'camera');
  const r = s.lastCommandResult;
  return {
    fov: cam ? cam.camera.fov : null,
    pastLen: (s.history.past || []).length,
    pastKinds: (s.history.past || []).map((e) => e.commandKind),
    active: s.history.activeGesture ? s.history.activeGesture.commandKind : null,
    last: r ? r.commandKind + '/' + r.disposition : null,
  };
}"""

SEED = """() => {
  const nodes = window.__libtv_store.getState().getActiveCanvas().nodes
    .filter((n) => n.type === 'script-execution');
  return nodes.length === 1 ? nodes[0].id : null;
}"""


def main():
    out = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        page = br.new_page(viewport=VIEWPORT, device_scale_factor=1)
        page.goto(f"{BASE_URL}/?diag828h=1", wait_until="networkidle", timeout=90_000)
        page.wait_for_function(
            "() => Boolean(window.__libtv_store && window.__libtv_ui_store "
            "&& window.__director_store)", timeout=60_000)
        page.wait_for_timeout(800)
        nid = page.evaluate(SEED)
        out["node"] = nid
        page.locator('.react-flow__node[data-id="%s"] [data-open-director]' % nid).first.click()
        page.locator("[data-director-workspace]").wait_for(state="visible", timeout=30_000)
        page.wait_for_timeout(1_800)
        page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
        page.mouse.move(5, 5)
        page.wait_for_timeout(300)

        page.evaluate("""() => {
          const s = window.__director_store.getState();
          const c = s.objects.find((o) => o.kind === 'camera');
          const row = document.querySelector('[data-director-tree] [role="treeitem"]'
            + '[data-director-object-id="' + c.id + '"]');
          if (row) row.click();
        }""")
        page.wait_for_timeout(800)
        out["开台后"] = {"active": page.evaluate(ACTIVE), "state": page.evaluate(STATE)}

        # 复刻 828 探针的手势动作
        el = page.locator("[data-director-shot-end]").first
        el.click()
        page.wait_for_timeout(300)
        out["点了shot-end"] = {"active": page.evaluate(ACTIVE)}
        el.press("Tab")
        page.wait_for_timeout(500)
        out["Tab之后"] = {"active": page.evaluate(ACTIVE), "state": page.evaluate(STATE)}
        for _ in range(3):
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(300)
        out["三下方向键"] = {"active": page.evaluate(ACTIVE), "state": page.evaluate(STATE)}

        # 失焦方式 A：点画布空白处
        page.mouse.click(640, 900)
        page.wait_for_timeout(1_000)
        out["点画布空白"] = {"active": page.evaluate(ACTIVE), "state": page.evaluate(STATE)}

        # 失焦方式 B：再按一次 Tab（键盘移动焦点一定会 blur）
        page.keyboard.press("Tab")
        page.wait_for_timeout(1_000)
        out["再按Tab"] = {"active": page.evaluate(ACTIVE), "state": page.evaluate(STATE)}

        # 失焦方式 C：点标题文字
        page.locator("[data-director-workspace] h1").first.click()
        page.wait_for_timeout(1_000)
        out["点标题"] = {"active": page.evaluate(ACTIVE), "state": page.evaluate(STATE)}

        # 失焦方式 D：点「关闭」按钮（即 closeWorkspace 的入口）
        page.locator("[data-close-director]").first.click()
        page.wait_for_timeout(1_500)
        out["点关闭"] = {"active": page.evaluate(ACTIVE), "state": page.evaluate(STATE)}

        page.close()
        br.close()
    pathlib.Path("/tmp/diag828h.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in out.items():
        if isinstance(v, dict):
            print(k, json.dumps(v, ensure_ascii=False))
        else:
            print(k, v)


if __name__ == "__main__":
    main()
