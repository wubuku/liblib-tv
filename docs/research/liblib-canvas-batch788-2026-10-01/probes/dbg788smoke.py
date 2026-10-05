#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 788 冒烟探针 —— **先验四个判别式**（773 立的纪律）

C787-2 说「往模型库加条目会取消正在进行的运镜绘制」，但 787 **没跑浏览器**。
本探针先只验一件事：**默认数据下能不能造出 `motionPathDraft`**，
造不出的话整批就是「结构上不可判」，得先说清而不是硬凑结论。

| 判别式 | 怎么验 | 不成立意味着 |
| --- | --- | --- |
| ① 导演台能开 | `[role=dialog][aria-modal=true]` | 探针环境不对 |
| ② 路径菜单能开 | 点 `[data-director-track-draw-trail]` ⟹ `[data-director-motion-path-menu]` 出现 | 入口变了 |
| ③ **草稿能造出来** | 点 `[data-director-motion-path-draw-tool="pencil"]` ⟹ `data-director-viewport-gizmo-disabled="true"` | ★ 整批不可判 |
| ④ 模型库能开、条目能点 | `[data-director-model-library-panel]` + `[data-director-model-library-preview-add]` | 入口变了 |

★ 读数用的是 `DirectorViewport.tsx:420` 的
`data-director-viewport-gizmo-disabled={disabled}`，而 `:2559-2560` 的
`viewportGizmoDisabled = timeline.motionPathDraft !== null || phoneVcamRecording`
⟹ **它就是 `motionPathDraft !== null` 的 DOM 读数**（录制未开 ⟹ 不会混淆）。
"""
import json
import pathlib
import sys
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch774-2026-10-01" / "probes"))
import dbg774a as A  # noqa: E402

OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/research/"
    "liblib-canvas-batch788-2026-10-01/raw/smoke788.json")
#: ★ 属性值是 `cameraTrack.id`（**轨道 id**）⟹ 不能用相机对象 id。
#:   第一版写死 `"director-camera-main"` ⟹ 命中 0 个 ⟹ 差点判成「结构上不可判」。
#:   ⟹ 改成「属性存在」选择器。
DRAW = "[data-director-track-draw-trail]"
MENU = "[data-director-motion-path-menu]"
TOOL = '[data-director-motion-path-draw-tool="pencil"]'
LIB_TRIGGER = "[data-director-model-library-trigger]"
LIB_PANEL = "[data-director-model-library-panel]"
LIB_ADD = "[data-director-model-library-preview-add]"
GIZMO = "[data-director-viewport-gizmo-disabled]"


def click(pg, sel):
    s = pg.evaluate(A.SCAN_CLICK, sel)
    if not s.get("pt"):
        return False
    pg.mouse.click(s["pt"][0], s["pt"][1])
    A.settle(pg)
    return True


def read(pg):
    return pg.evaluate("""(giz)=>{
      const g=document.querySelector(giz);
      return {gizmo: g ? g.getAttribute('data-director-viewport-gizmo-disabled') : null,
        menu: !!document.querySelector('[data-director-motion-path-menu]'),
        libPanel: !!document.querySelector('[data-director-model-library-panel]'),
        toolCount: document.querySelectorAll('[data-director-motion-path-draw-tool]').length,
        toolDisabled: (()=>{const t=document.querySelector('[data-director-motion-path-draw-tool="pencil"]');
          return t ? t.disabled : null;})(),
        addLabel: (()=>{const a=document.querySelector('[data-director-model-library-preview-add]');
          return a ? a.getAttribute('aria-label') : null;})()};
    }""", GIZMO)


def main():
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        pg = b.new_page()
        pg.set_default_timeout(15000)
        out = {}
        try:
            A.fresh(pg)
            out["deskOpen"] = bool(pg.evaluate(
                "()=>!!document.querySelector('[role=\"dialog\"][aria-modal=\"true\"]')"))
            out["drawBtn"] = pg.evaluate(
                "(s)=>document.querySelectorAll(s).length", DRAW)
            out["drawBtnId"] = pg.evaluate(
                "(s)=>{const e=document.querySelector(s);"
                "return e?e.getAttribute(s.slice(1,-1)):null;}", DRAW)
            out["before"] = read(pg)

            out["clickedDraw"] = click(pg, DRAW)
            out["afterDraw"] = read(pg)
            out["clickedTool"] = click(pg, TOOL)
            out["afterTool"] = read(pg)

            out["clickedLib"] = click(pg, LIB_TRIGGER)
            out["afterLib"] = read(pg)
            out["clickedAdd"] = click(pg, LIB_ADD)
            out["afterAdd"] = read(pg)
        except Exception as e:  # noqa: BLE001
            out["FAILED"] = "%s: %s" % (type(e).__name__, e)
        finally:
            pg.close()
            b.close()
    out["judgments"] = {
        "① deskOpen": bool(out.get("deskOpen")),
        "② 路径菜单能开": bool(out.get("afterDraw", {}).get("menu")),
        "③ ★ 草稿能造出来": out.get("afterTool", {}).get("gizmo") == "true",
        "④ 模型库能开": bool(out.get("afterLib", {}).get("libPanel")),
        "④ 模型库条目能点": out.get("clickedAdd") is True,
        "★ 加条目后草稿消失（待判）":
            out.get("afterTool", {}).get("gizmo") == "true"
            and out.get("afterAdd", {}).get("gizmo") != "true",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))
    print("\n★ 判别式：", json.dumps(out["judgments"], ensure_ascii=False))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
