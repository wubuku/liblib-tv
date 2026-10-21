#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 833 clone 侧探针：点某枚机位预设后，**新建的机位**是不是按该枚语义建的。

★ 读数口径与源站**完全一致**：两边都跑 probes/reader833.py 的**规则 R**
  （按字段标题分组）⟹ 两边输出 {位置,旋转,注视,FOV} ⟹ 可逐字比对。
  ⟹ ★ 不再用「把 number 输入拼起来再切片」——clone 的 Inspector **多一行「缩放」**，
     切片索引会整体错位（这正是本批要修的第二个坑）。

★ ★ 机位数的读法：走 **store**（`window.__director_store.getState()`），
  而不是读 DOM 文本 —— ★ 因为点开预设面板后**左侧栏切成了预设视图**，
  场景树**根本不在 DOM 里** ⟹ 读 DOM 恒为 0（假读数）。

★ 纪律：clone 是本地 mock ⟹ 可以随便点；但每枚测完**立刻删掉新建的那台**，
  并**复验**机位数少了一台 ⟹ 保持 clone 干净。
"""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from reader833 import READ_PROPS_JS, semantics_from_js  # noqa: E402

BASE = "http://localhost:4317"
OUT = (pathlib.Path(__file__).resolve().parent.parent
       / "raw" / "clone-833-camera-preset-semantics.json")
SHOTS = pathlib.Path("/tmp/liblib_clone_desk833")

# ★ 左侧资源栏当前是哪个视图（预设面板 15 枚格子 / 场景树）
DUMP_LEFT = """()=>{
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  const cells=document.querySelectorAll('[data-director-camera-preset]').length;
  const tree=document.querySelector('[data-director-tree]');
  return {presetCells:cells, treeInDom:Boolean(tree),
          treeText:tree?((tree.innerText||'').slice(0,40)):''};
}"""

# ★ 机位数 / 新建机位 id —— 走 store，不读 DOM
DUMP_CAM = """()=>{
  const s=window.__director_store.getState();
  const cams=s.authoredObjects.filter(o=>o.kind==='camera');
  return {count:cams.length, active:s.activeCameraId,
          names:cams.map(c=>c.name)};
}"""

# ★ 删掉当前选中的那台机位（= 刚点预设新建的那台）⟹ 返回删除后的机位数
DROP_ACTIVE = """()=>{
  const s=window.__director_store.getState();
  const id=s.activeCameraId;
  if(!id) return {ok:false, reason:'没有选中机位', count:0};
  s.deleteDirectorEntity({kind:'DELETE_OBJECT', objectId:id});
  const after=window.__director_store.getState().authoredObjects
    .filter(o=>o.kind==='camera').length;
  return {ok:true, dropped:id, count:after};
}"""


def main():
    out = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        page = br.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(f"{BASE}/?batch833=1", wait_until="networkidle", timeout=90_000)
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
        page.wait_for_timeout(2_000)
        page.evaluate(
            "() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
        SHOTS.mkdir(exist_ok=True)

        out["⓪基线机位"] = page.evaluate(DUMP_CAM)
        # 点 rail「添加机位」⟹ 机位预设面板
        page.locator("[data-director-rail-entry='add-camera']").click()
        page.wait_for_timeout(1_500)
        out["①面板打开"] = page.evaluate(
            "()=>({panels:document.querySelectorAll("
            "'[data-director-camera-preset-panel]').length,"
            "presets:document.querySelectorAll('[data-director-camera-preset]').length})")

        results = []
        log = []
        labels = page.evaluate(
            "()=>Array.from(document.querySelectorAll('[data-director-camera-preset]'))"
            ".map(e=>e.getAttribute('data-director-camera-preset'))")
        for i, label in enumerate(labels):
            before = page.evaluate(DUMP_CAM)
            page.locator("[data-director-camera-preset='%s']" % label).click()
            page.wait_for_timeout(1_600)
            js = page.evaluate(READ_PROPS_JS)
            after = page.evaluate(DUMP_CAM)
            left = page.evaluate(DUMP_LEFT)
            try:
                sem = semantics_from_js(js)
            except Exception as exc:  # noqa: BLE001
                sem = {"错误": repr(exc)[:200]}
            results.append({
                "idx": i, "label": label,
                "前机位数": before.get("count"), "后机位数": after.get("count"),
                "后机位名": after.get("names"),
                "语义": sem,
                "点完后左侧": left,
            })
            print("  #%2d %-14s 机位 %s → %s  位置=%s 旋转=%s 注视=%s FOV=%s"
                  % (i, label, before.get("count"), after.get("count"),
                     sem.get("位置"), sem.get("旋转"), sem.get("注视"), sem.get("FOV")))
            # ★ 清掉这台 ⟹ 保持 clone 干净 ⟹ 并复验少了一台
            drop = page.evaluate(DROP_ACTIVE)
            log.append("删 #%d %s：%s → %s 台 %s"
                       % (i, label, after.get("count"), drop.get("count"),
                          "✔" if drop.get("count") == after.get("count") - 1 else "✘"))
            page.wait_for_timeout(700)
        out["②逐枚"] = results
        out["③删除日志"] = log
        out["④末次机位"] = page.evaluate(DUMP_CAM)
        page.screenshot(path=str(SHOTS / "833_after.png"))
        br.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已落盘：", OUT)
    print("末次机位：", out["④末次机位"])


if __name__ == "__main__":
    main()
