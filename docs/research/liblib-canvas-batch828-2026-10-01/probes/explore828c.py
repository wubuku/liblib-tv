#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 828 探索③：同一个节点上的完整生命周期（关台重开 / 刷新重开 / 撤销）。"""
import json

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
W, H = 1920, 1080
RENAME_TO = "Batch 828 改名"

READ = """() => {
  const s = window.__director_store.getState();
  const h = s.history; const r = s.lastCommandResult;
  const w = document.querySelector('[data-director-workspace]');
  const cam = s.objects.find((o) => o.kind === 'camera');
  const ui = window.__libtv_ui_store.getState();
  return {
    deskOpen: !!w,
    projectId: w ? w.getAttribute('data-director-project-id') : null,
    pastLen: (h.past || []).length,
    pastKinds: (h.past || []).map((e) => e.commandKind),
    last: r ? r.commandKind + '/' + r.disposition : null,
    fovStore: cam ? cam.camera.fov : null,
    names: s.objects.map((o) => o.name),
    nodeId: ui.activeDirectorNodeId,
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


def btn_for(node_id):
    return '.react-flow__node[data-id="%s"] [data-open-director]' % node_id


def read(page):
    return page.evaluate(READ)


def clean(page):
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(300)
    page.evaluate(SEL_CAMERA)
    page.wait_for_timeout(500)


def open_node(page, node_id, via):
    if via == "real":
        page.locator(btn_for(node_id)).first.click()
    else:
        page.evaluate("""(nid) => {
          const s = window.__libtv_store.getState();
          window.__libtv_ui_store.getState().openDirectorDesk(nid, s.activeCanvasId);
        }""", node_id)
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


def setup(browser, add_node):
    page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
    page.goto(f"{BASE}/?batch828=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__libtv_ui_store "
        "&& window.__director_store)", timeout=60_000)
    if add_node:
        page.evaluate("""() => {
          const s = window.__libtv_store.getState();
          s.addNode("script-execution", { title: "Batch 828" });
        }""")
        page.wait_for_timeout(1_500)
        page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
        page.mouse.move(5, 5)
        page.wait_for_timeout(300)
    nid = page.evaluate("""() => {
      const nodes = window.__libtv_store.getState().getActiveCanvas().nodes;
      return nodes.filter((n) => n.type === 'script-execution').at(-1).id;
    }""")
    return page, nid


def arm_user_path(browser):
    page, nid = setup(browser, add_node=False)
    rec = {"node": nid}
    open_node(page, nid, "real")
    clean(page)
    rec["开台后"] = read(page)
    rename(page, RENAME_TO)
    rec["改名后"] = read(page)
    close_desk(page)
    rec["关台后"] = read(page)
    open_node(page, nid, "real")
    clean(page)
    rec["重开后"] = read(page)
    page.mouse.click(640, 900)
    page.wait_for_timeout(500)
    page.keyboard.press("Meta+z")
    page.wait_for_timeout(800)
    rec["重开后撤销"] = read(page)
    page.close()
    return rec


def arm_same_node_backdoor_then_real(browser):
    page, nid = setup(browser, add_node=True)
    rec = {"node": nid}
    open_node(page, nid, "backdoor")
    clean(page)
    rec["开台后"] = read(page)
    rename(page, RENAME_TO)
    rec["改名后"] = read(page)
    close_desk(page)
    rec["关台后"] = read(page)
    open_node(page, nid, "real")
    clean(page)
    rec["重开后"] = read(page)
    page.close()
    return rec


def arm_reload_same_node(browser):
    page, nid = setup(browser, add_node=False)
    rec = {"node": nid}
    open_node(page, nid, "real")
    clean(page)
    rename(page, RENAME_TO)
    rec["改名后"] = read(page)
    close_desk(page)
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(3_000)
    rec["刷新后"] = read(page)
    open_node(page, nid, "real")
    clean(page)
    rec["刷新后重开"] = read(page)
    page.close()
    return rec


def main():
    out = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        out["A 用户路径·同节点"] = arm_user_path(browser)
        out["E 后门开·同节点真实按钮重开"] = arm_same_node_backdoor_then_real(browser)
        out["F 刷新·同节点"] = arm_reload_same_node(browser)
        browser.close()
    with open("/tmp/liblib_batch828_same.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    for k, rec in out.items():
        print("====", k, "node=", rec["node"])
        for kk, v in rec.items():
            if kk == "node":
                continue
            print(f"  {kk:10} desk={v['deskOpen']} project={v['projectId']} past={v['pastLen']} "
                  f"last={v['last']} 改名在={'Batch 828 改名' in v['names']}")


if __name__ == "__main__":
    main()
