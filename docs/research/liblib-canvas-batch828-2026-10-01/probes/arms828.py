#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 828 三臂对照：第一次关台重开到底丢不丢工作。

臂 A（用户路径）：真实按钮开 ＋ 真实按钮重开
臂 B（后门路径）：后门开 ＋ 后门重开
臂 C（709 的混搭）：后门开 ＋ 真实按钮重开

★ 三臂唯一的变量是「开台用哪条路径」⟹ 若 A 不丢而 C 丢 ⟹ 709 那次测到的是
  「两条路径混搭」的产物，不是产品缺陷。
"""
import json

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
W, H = 1920, 1080
RENAME_TO = "Batch 828 改名"

READ = """() => {
  const s = window.__director_store.getState();
  const h = s.history;
  const w = document.querySelector('[data-director-workspace]');
  const cam = s.objects.find((o) => o.kind === 'camera');
  return {
    deskOpen: !!w,
    projectId: w ? w.getAttribute('data-director-project-id') : null,
    pastLen: (h.past || []).length,
    names: s.objects.map((o) => o.name),
    fovStore: cam ? cam.camera.fov : null,
    nodeId: window.__libtv_ui_store.getState().activeDirectorNodeId,
    canvasId: window.__libtv_ui_store.getState().activeDirectorCanvasId,
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

BACKDOOR_OPEN = """() => {
  const s = window.__libtv_store.getState();
  const node = s.getActiveCanvas().nodes.at(-1);
  window.__libtv_ui_store.getState()
    .openDirectorDesk(node.id, s.activeCanvasId);
}"""


def clean(page):
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(300)
    page.evaluate(SEL_CAMERA)
    page.wait_for_timeout(500)


def read(page):
    return page.evaluate(READ)


def open_real(page):
    page.locator("[data-open-director]").first.click()
    page.locator("[data-director-workspace]").wait_for(state="visible", timeout=30_000)
    page.wait_for_timeout(1_800)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")


def open_backdoor(page):
    page.evaluate(BACKDOOR_OPEN)
    page.locator("[data-director-workspace]").wait_for(state="visible", timeout=30_000)
    page.wait_for_timeout(1_800)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")


def close_desk(page):
    page.locator("[data-close-director]").first.click()
    page.locator("[data-director-workspace]").wait_for(state="detached", timeout=15_000)
    page.wait_for_timeout(1_000)


def rename(page, text):
    el = page.locator("[data-director-object-name]").first
    el.click()
    page.wait_for_timeout(200)
    el.fill(text)
    el.press("Tab")
    page.wait_for_timeout(800)


def arm(browser, first, again, label):
    page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
    page.goto(f"{BASE}/?batch828=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__libtv_ui_store "
        "&& window.__director_store)", timeout=60_000)
    page.evaluate("""() => {
      const s = window.__libtv_store.getState();
      s.addNode("script-execution", { title: "Batch 828" });
    }""")
    page.wait_for_timeout(1_500)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(300)

    rec = {"label": label, "第一次开台路径": first, "重开路径": again}
    rec["开台前"] = read(page)

    if first == "real":
        open_real(page)
    else:
        open_backdoor(page)
    clean(page)
    rec["第一次开台后"] = read(page)

    rename(page, RENAME_TO)
    rec["改名后"] = read(page)

    close_desk(page)
    rec["关台后"] = read(page)

    if again == "real":
        open_real(page)
    else:
        open_backdoor(page)
    clean(page)
    rec["重开后"] = read(page)

    page.close()
    return rec


def main():
    out = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        out.append(arm(browser, "real", "real", "A 用户路径（真实按钮→真实按钮）"))
        out.append(arm(browser, "backdoor", "backdoor", "B 后门路径（后门→后门）"))
        out.append(arm(browser, "backdoor", "real", "C 709 的混搭（后门→真实按钮）"))
        out.append(arm(browser, "real", "backdoor", "D 反混搭（真实按钮→后门）"))
        browser.close()

    with open("/tmp/liblib_batch828_arms.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    for rec in out:
        print("====", rec["label"])
        for k in ("开台前", "第一次开台后", "改名后", "关台后", "重开后"):
            v = rec[k]
            print(f"  {k:12} desk={v['deskOpen']} project={v['projectId']} "
                  f"past={v['pastLen']} node={v['nodeId']} "
                  f"改名在={'Batch 828 改名' in v['names']}")


if __name__ == "__main__":
    main()
