#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 833：源站**只读为主的**补充探针 —— 点完一枚机位预设之后，
**左侧的机位预设面板还在不在**？

★ 为什么要补这一条：
  clone 的实现是「点完预设，面板**不关**」⟹ 但 batch 832/833 的源站采集里
  **没有证据**支持这一点（点完就切回场景视图删机位了，过程被覆盖掉了）
  ⟹ ★ 不补这一条，就只能把它写成 clone 的**自选行为**，不能声称与源站一致。

★ 副作用控制：本探针只点**一枚**预设 ⟹ 最多新建 1 台机位
  ⟹ 立刻**按名字删掉**并**复验少了一台** ⟹ 收尾再**全新 context 复验**场景树。

★ 落盘：raw/source-833-preset-panel-stays.json
"""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from presets833 import (  # noqa: E402
    COOKIE, URL, DUMP_NEWNAME, back_to_scene, delete_camera, open_desk,
    tree_cameras,
)

OUT = (pathlib.Path(__file__).resolve().parent.parent
       / "raw" / "source-833-preset-panel-stays.json")

# ★ 左侧资源栏当前是哪个视图：预设面板（15 枚格子）还是场景树？
DUMP_LEFT = """()=>{
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  const grid=Array.from(document.querySelectorAll('div.grid')).find(g=>{
    const r=g.getBoundingClientRect();
    return vis(g)&&r.x<200&&r.width>100&&r.height>200;});
  const cells=grid?grid.querySelectorAll('button').length:0;
  const tree=Array.from(document.querySelectorAll('span')).filter(vis)
    .map(s=>(s.textContent||'').trim())
    .filter(t=>/^机位\\s*\\d+$/.test(t));
  return {presetCells:cells, treeNames:[...new Set(tree)],
          treeInDom:tree.length>0};
}"""


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {}
    log = out.setdefault("删除日志", [])
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            ctx.add_cookies([{
                "name": c["name"], "value": c["value"], "domain": c["domain"],
                "path": c.get("path", "/"), "expires": c.get("expires", -1),
                "httpOnly": c.get("httpOnly", False),
                "secure": c.get("secure", False),
                "sameSite": c.get("sameSite", "Lax"),
            } for c in cookies])
            page = ctx.new_page()
            page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
            page.wait_for_timeout(12_000)
            open_desk(page)
            try:
                out["①点开面板前"] = page.evaluate(DUMP_LEFT)
                nav = page.locator("nav").filter(
                    has=page.locator("button[aria-label='场景']")).first
                nav.locator("button[aria-label='添加机位']").first.click()
                page.wait_for_timeout(2_200)
                out["②面板打开后"] = page.evaluate(DUMP_LEFT)

                grid = page.locator("div.grid.min-h-0.flex-1").first
                cells = grid.locator("button")
                label = (cells.nth(0).inner_text() or "").strip().split("\n")[-1]
                cells.nth(0).click()
                page.wait_for_timeout(2_400)
                out["③点完第 1 枚后"] = page.evaluate(DUMP_LEFT)
                out["③点的那枚"] = label
                out["③新建机位名"] = page.evaluate(DUMP_NEWNAME)
                page.screenshot(path="/tmp/liblib_source_833_panelstay.png")
            except Exception as exc:  # noqa: BLE001
                out["异常"] = repr(exc)[:400]
            try:
                name = out.get("③新建机位名")
                out["④删除是否成功"] = delete_camera(page, log, name)
            except Exception as exc:  # noqa: BLE001
                out["④删除是否成功"] = False
                log.append("删除异常：%r" % (exc,)[:120])
            back_to_scene(page)
            out["⑤末次树"] = tree_cameras(page)
            try:
                page.locator("[aria-label='关闭']:visible").first.click()
                page.wait_for_timeout(2_500)
            except Exception:
                pass
            ctx.close()
            br.close()
    finally:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        print("已落盘：", OUT)
        for k in ("①点开面板前", "②面板打开后", "③点完第 1 枚后"):
            print("  %s: %s" % (k, json.dumps(out.get(k), ensure_ascii=False)))
        print("  ③新建机位名:", out.get("③新建机位名"))
        print("  ④删除是否成功:", out.get("④删除是否成功"))
        print("  ⑤末次树:", out.get("⑤末次树"))


if __name__ == "__main__":
    main()
