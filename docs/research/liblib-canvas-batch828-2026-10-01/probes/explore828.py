#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 828 探索探针：第一次开台**走真实按钮**，关台重开后工作还在不在。

★ 起因：batch 709 的第 5 条判据原来说「真实按钮点了没反应」⟹
  那个「没反应」的真因是**页面不 hydration**（batch 827 查实）⟹
  ⟹ 「第一次关台丢工作」到底是不是**用户可见**的缺陷，现在可以取证了。
"""
import json
import sys

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
W, H = 1920, 1080
RENAME_TO = "Batch 828 改名"

READ = """() => {
  const s = window.__director_store.getState();
  const h = s.history; const r = s.lastCommandResult;
  const w = document.querySelector('[data-director-workspace]');
  const cam = s.objects.find((o) => o.kind === 'camera');
  return {
    deskOpen: !!w,
    projectId: w ? w.getAttribute('data-director-project-id') : null,
    pastLen: (h.past || []).length,
    pastKinds: (h.past || []).map((e) => e.commandKind),
    last: r ? r.commandKind + '/' + r.disposition : null,
    fovStore: cam ? cam.camera.fov : null,
    names: s.objects.map((o) => o.name),
    objectsLen: s.objects.length,
  };
}"""

SEL_CAMERA = r"""() => {
  const s = window.__director_store.getState();
  const c = s.objects.find((o) => o.kind === 'camera');
  const row = document.querySelector('[data-director-tree] [role="treeitem"]'
    + '[data-director-object-id="' + c.id + '"]');
  if (!row) return { ok: false, stage: 'no-row' };
  row.click();
  return { ok: window.__director_store.getState().selectedObjectId === c.id };
}"""


def read(page):
    return page.evaluate(READ)


def main():
    out = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": W, "height": H},
                                device_scale_factor=1)
        page.goto(f"{BASE}/?batch828=1", wait_until="networkidle", timeout=90_000)
        page.wait_for_function(
            "() => Boolean(window.__libtv_store && window.__libtv_ui_store "
            "&& window.__director_store)", timeout=60_000)

        # ★ 建节点仍然用 store 后门（batch 823：画布的「新建节点」纯 UI 入口至今没找到）
        page.evaluate("""() => {
          const s = window.__libtv_store.getState();
          s.addNode("script-execution", { title: "Batch 828" });
        }""")
        page.wait_for_timeout(1_500)
        page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
        page.mouse.move(5, 5)
        page.wait_for_timeout(300)

        out["按钮数"] = page.locator("[data-open-director]").count()
        out["按钮可见"] = page.locator("[data-open-director]").first.is_visible() \
            if out["按钮数"] else False

        # ★★ 第一次开台：**真实按钮**
        page.locator("[data-open-director]").first.click()
        page.locator("[data-director-workspace]").wait_for(state="visible", timeout=30_000)
        page.wait_for_timeout(1_800)
        page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
        out["第一次开台后"] = read(page)
        out["第一次开台选中相机"] = page.evaluate(SEL_CAMERA)
        page.wait_for_timeout(500)

        # 改名（真实 UI：点名字 → 填 → Tab）
        el = page.locator("[data-director-object-name]").first
        el.click()
        page.wait_for_timeout(200)
        el.fill(RENAME_TO)
        el.press("Tab")
        page.wait_for_timeout(800)
        out["改名后"] = read(page)

        # 关台（真实按钮）
        page.locator("[data-close-director]").first.click()
        page.locator("[data-director-workspace]").wait_for(state="detached", timeout=15_000)
        page.wait_for_timeout(1000)
        out["关台后"] = read(page)

        # ★★ 重开（真实按钮）
        page.locator("[data-open-director]").first.click()
        page.locator("[data-director-workspace]").wait_for(state="visible", timeout=30_000)
        page.wait_for_timeout(1_800)
        page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
        out["重开后"] = read(page)

        # 第二轮：再改名 → 关 → 重开（看第二次是否保留）
        page.mouse.click(640, 900)
        page.wait_for_timeout(600)
        page.evaluate(SEL_CAMERA)
        page.wait_for_timeout(500)
        el = page.locator("[data-director-object-name]").first
        el.click()
        page.wait_for_timeout(200)
        el.fill(RENAME_TO + " 2")
        el.press("Tab")
        page.wait_for_timeout(800)
        out["第二轮改名后"] = read(page)
        page.locator("[data-close-director]").first.click()
        page.locator("[data-director-workspace]").wait_for(state="detached", timeout=15_000)
        page.wait_for_timeout(1000)
        page.locator("[data-open-director]").first.click()
        page.locator("[data-director-workspace]").wait_for(state="visible", timeout=30_000)
        page.wait_for_timeout(1_800)
        out["第二轮重开后"] = read(page)

        browser.close()

    print(json.dumps(out, ensure_ascii=False, indent=1))
    with open("/tmp/liblib_batch828_explore.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
