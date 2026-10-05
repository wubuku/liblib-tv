#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 782 探针 A —— 静态普查说「Escape 主人分两种：排他的与不排他的」，
**运行时到底是不是这样？**

## 静态普查（`census782.py`）给出的三样

| 键 | 主人数 | 排他的（`stopImmediatePropagation`） |
| --- | --- | --- |
| `Meta+c`/`Meta+v`/`Meta+z`/`Meta+y`/`Delete`/`Backspace` | **1**（`DirectorDesk:570`，且**唯一看 `type`**） | 0 |
| `Escape` | **9** | **3**（`DirectorPhoneVcamPanel:294`、`DirectorViewport:2711/2748`，全在 **capture** 相位） |
| `Tab` | 1（`useDirectorFocusContainment:174`） | 0（`stopPropagation`，且桌面端那个实例没开） |

⟹ 预测：**capture 相位那 3 个主人激活时，冒泡相位的 6 个 Escape 主人
（含 `DirectorDesk` 的阶梯）会一个都跑不到。**

## 三个臂，一个对照

| 臂 | 前置（让谁的主人激活） | 预测 |
| --- | --- | --- |
| ★ `captureOwner` | 打开**模型库**（`DirectorViewport:2748` 是 capture+pD+**sIP**） | 模型库关；★ **桌的阶梯跑不到** ⟹ 导出面板/桌**都不动** |
| `bubbleOwner` | 打开**路径菜单**（`DirectorTimeline:570/594` 是 bubble、**不**排他） | 菜单关；★ **桌的阶梯照跑** ⟹ 导出面板**也**关（一次按压多主并发） |
| `none` | 什么都不开（对照） | 阶梯跑完：第 1 次关导出面板、第 2 次关桌 |

★ `none` 臂是**鉴别力对照**：没有它，「阶梯没跑」可能只是「导出面板本来就没开」。

## 承重读数

- `cap` / `win`（沿用 779 的判别器）：确认按键送达、事件到达 window 相位
- `lastCommand`：桌侧有没有产生命令
- `exportPanel` / `deskOpen` / **目标浮层的开合** ⟹ 判「谁的主人跑了」
"""
import json
import pathlib
import sys
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch774-2026-10-01" / "probes"))
import dbg774a as A  # noqa: E402

OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/research/"
    "liblib-canvas-batch782-2026-10-01/raw/vb782a.json")

CAM = A.CAM
TREE_BTN = "[data-director-panels-toggle]"
EXPORT_TRIGGER = "[data-director-export-trigger]"
EXPORT_PANEL = "[data-director-export-panel]"
MODEL_TRIGGER = "[data-director-model-library-trigger]"
MODEL_PANEL = "[data-director-model-library-panel]"
PATH_TRIGGER = '[data-director-track-draw-trail="director-track-camera-main"]'
PATH_PANEL = "[data-director-motion-path-menu]"
SETTLE = 500
PRESSES = 2
MAX_TRIES = 3
#: (臂, 目标浮层的开合选择器, 打开它的触发器, 按什么键)
ARMS = [
    {"id": "captureOwner", "trigger": MODEL_TRIGGER, "panel": MODEL_PANEL},
    {"id": "bubbleOwner", "trigger": PATH_TRIGGER, "panel": PATH_PANEL},
    {"id": "none", "trigger": None, "panel": None},
]
ARM_IDS = [a["id"] for a in ARMS]

LISTEN = """()=>{const w=window;
 if(!w.__b782){
   w.__b782={cap:0, win:0, keys:[]};
   document.addEventListener('keydown',(e)=>{w.__b782.cap++;},true);
   window.addEventListener('keydown',(e)=>{w.__b782.win++;},false);
 }
 return {installed:true};}"""

READ = """()=>{const b=window.__b782; if(!b) return {err:'no'};
 const r={cap:b.cap, win:b.win}; b.cap=0; b.win=0; return r;}"""

ST = """(panelSel)=>{const q=(n)=>{const e=document.querySelector('['+n+']');
  return e?(e.getAttribute(n)||''):null;};
 const ae=document.activeElement;
 return {targetOpen: panelSel ? !!document.querySelector(panelSel) : null,
   exportOpen: !!document.querySelector('[data-director-export-panel]'),
   deskOpen: !!document.querySelector('[role="dialog"][aria-modal="true"]'),
   lastCommand:q('data-director-last-command'),
   gesture:q('data-director-active-gesture'),
   focusTag:ae?ae.tagName:null,
   focusType:ae?ae.getAttribute('type'):null};}"""

FOCUS = """(s)=>{const e=document.querySelector(s);
 if(!e) return {err:'no el'};
 if(e.disabled) return {err:'disabled'};
 e.focus({preventScroll:true});
 return {ok:document.activeElement===e, type:e.getAttribute('type')};}"""


def _click(pg, sel):
    s = pg.evaluate(A.SCAN_CLICK, sel)
    if not s.get("pt"):
        return False
    pg.mouse.click(s["pt"][0], s["pt"][1])
    A.settle(pg)
    return True


def run_cell(pg, arm):
    R = {"arm": arm["id"], "presses": []}
    r = A.fresh(pg)
    if r.get("FAILED"):
        R["FAILED"] = "导演台没开"
        return R
    A.click_tree_row(pg, CAM)
    A.settle(pg)
    # ★ 导出面板**始终**开着 ⟹ 桌的阶梯 `:557` 那档永远有目标
    if not _click(pg, EXPORT_TRIGGER):
        R["FAILED"] = "★ 导出面板没打开 ⟹ 不是有效读数"
        return R
    st0 = pg.evaluate(ST, None)
    if not st0.get("exportOpen"):
        R["FAILED"] = "导出面板没开"
        return R
    # 目标浮层（若有）
    if arm["trigger"]:
        if not _click(pg, arm["trigger"]):
            R["FAILED"] = "★ 目标触发器点不动：%s" % arm["trigger"]
            return R
        st1 = pg.evaluate(ST, arm["panel"])
        if not st1.get("targetOpen"):
            R["FAILED"] = ("★ 目标浮层没打开（%s）⟹ 这一格不是有效读数"
                           % arm["panel"])
            return R
    pg.evaluate(LISTEN)
    f = pg.evaluate(FOCUS, TREE_BTN)
    A.settle(pg)
    R["focus"] = f
    if f.get("err") or not f.get("ok"):
        R["FAILED"] = "桌内落点聚焦失败：%s" % (f.get("err") or "未落上")
        return R
    R["stateBefore"] = pg.evaluate(ST, arm["panel"])
    for i in range(PRESSES):
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(SETTLE + 150)
        R["presses"].append({"n": i + 1, "read": pg.evaluate(READ),
                             "state": pg.evaluate(ST, arm["panel"])})
    return R


def run_round(pg, R):
    R["rows"] = []
    for arm in ARMS:
        r, tries = None, 0
        while tries < MAX_TRIES:
            tries += 1
            try:
                r = run_cell(pg, arm)
            except Exception as e:  # noqa: BLE001
                r = {"arm": arm["id"],
                     "FAILED": "%s: %s" % (type(e).__name__, str(e)[:150])}
            if not r.get("FAILED"):
                break
            pg.wait_for_timeout(900 * tries)
        r["tries"] = tries
        if tries > 1:
            r["retried"] = True
        R["rows"].append(r)


def summarize(R):
    for r in R.get("rows") or []:
        if r.get("FAILED"):
            print("   %-14s FAILED(试 %s): %s"
                  % (r["arm"], r.get("tries"), r["FAILED"][:56]))
            continue
        s0 = r["stateBefore"]
        print("   %-14s 起点 目标浮层=%-5s 导出面板=%s 桌=%s"
              % (r["arm"], s0.get("targetOpen"), s0.get("exportOpen"),
                 s0.get("deskOpen")))
        for p in r["presses"]:
            s = p["state"]
            print("        第%d次 cap=%s win=%s ｜ 目标浮层=%-5s 导出面板=%-5s "
                  "桌=%-5s lastCommand=%s"
                  % (p["n"], p["read"].get("cap"), p["read"].get("win"),
                     s.get("targetOpen"), s.get("exportOpen"),
                     s.get("deskOpen"), s.get("lastCommand") or "(空)"))


def main():
    res = {
        "batch": 782, "probe": "a",
        "question": "静态普查说 Escape 主人分两种（3 个 capture 相位的**排他**、"
                    "6 个冒泡的**不排他**）—— 运行时到底是不是这样？",
        "prediction": "★ **capture 相位那 3 个主人激活时，冒泡相位的 6 个 Escape "
                      "主人（含 `DirectorDesk` 的阶梯）会一个都跑不到**；"
                      "而**不排他**的主人开着时，一次按压会被多个主人同时处理。",
        "arms": [
            {"id": "captureOwner",
             "why": "`DirectorViewport:2748`（模型库）是 capture+pD+**sIP** ⟹ "
                    "预测：模型库关，而**桌的阶梯跑不到**"},
            {"id": "bubbleOwner",
             "why": "`DirectorTimeline:570/594`（路径菜单）是 bubble、**不**排他 ⟹ "
                    "预测：菜单关，而**桌的阶梯照跑**（导出面板也关）"},
            {"id": "none", "why": "★ **鉴别力对照**：什么都不开 ⟹ 阶梯跑完"},
        ],
        "loadBearing": "`cap`/`win` 确认按键送达与事件到达 window；"
                       "**目标浮层的开合**判「谁的主人跑了」；"
                       "**导出面板/桌的开合**判「阶梯跑没跑」；"
                       "`lastCommand` 兜底。",
        "rounds": [],
    }
    with sync_playwright() as p:
        br = p.chromium.launch()
        ctx = br.new_context(viewport={"width": 1440, "height": 1000})
        pg = ctx.new_page()
        try:
            for i in range(2):
                R = {}
                res["rounds"].append(R)
                print("round %d" % (i + 1))
                run_round(pg, R)
                summarize(R)
        finally:
            OUT.parent.mkdir(parents=True, exist_ok=True)
            try:
                br.close()
            except Exception:  # noqa: BLE001
                pass
            OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1),
                           encoding="utf-8")
            print("（已落盘）")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
