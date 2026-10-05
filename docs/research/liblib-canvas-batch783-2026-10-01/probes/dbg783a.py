#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 783 探针 A —— 11 个 `Escape` 主人「**能不能同时活着**」

## 782 数出了 11 个主人，但没数它们**能否同时激活**
而这才决定 Escape 的真实行为：同时活着时，一次按压会关掉几个？

## 静态读源码得到的**承重预测**

`DirectorTimeline.tsx` 里有两个 Escape 主人，**同文件、相邻两个 `useEffect`**：

| 主人 | 门 | 相位 | 阻断 |
| --- | --- | --- | --- |
| `:570` | `if (pathMenuLeft === null) return;` | bubble | **不**阻断 |
| `:594` | `if (presetPanelLeft === null) return;` | bubble | **不**阻断 |

两个状态变量**互相独立**，两个 `useEffect` 之间**零交叉守卫**
⟹ **静态上没有任何东西保证它们不同时活着。**

★ 那唯一的互斥机制是什么？**不是状态守卫，是 `pointerdown` 外点关闭** ——
`:569` 的 `window.addEventListener("pointerdown", close)`。

⟹ **由此得到一条可falsify的预测：**

- **鼠标激活**第二个面板时会产生 `pointerdown` ⟹ 第一个被外点关闭
  ⟹ **两者互斥**（但互斥的不是 Escape，是鼠标）
- ★ **键盘激活**（`Enter`/`Space` 按在按钮上）**不产生 `pointerdown`**
  ⟹ **两者可以同时开着** ⟹ 而它们都是 bubble、**不阻断**
  ⟹ **一次 Escape 会把两个都关掉**

## 这为什么直接改变 D8 的授权文本

D8 要改的**正是这两个**（`:570/594` → capture + pD + **sIP**）。
若两者同时开着，改完之后**先注册的那个** `sIP` 掉整条链，
**另一个永远关不掉** ⟹ D8 会把「一次关两个」变成「**一个关不掉**」。

## 三个臂

| 臂 | 前置 | 预测 |
| --- | --- | --- |
| ★ `bothByMouse` | 点开路径菜单 → **鼠标点**预设触发器 | ★ **不会**同时开（外点 `pointerdown` 关掉了第一个） |
| ★★ `bothByKeyboard` | 点开路径菜单 → **键盘** `Enter` 激活预设触发器 | ★★ **会**同时开 ⟹ 一次 Escape **两个都关** |
| `pathOnly`（对照） | 只点开路径菜单 | 关掉它；**判别力对照** |
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
    "liblib-canvas-batch783-2026-10-01/raw/vb783a.json")
BASE = A.BASE
CAM = A.CAM
SETTLE = 260
PRESSES = 1
ROUNDS = 2
RETRY = 3

PATH_TRIGGER = '[data-director-track-draw-trail="%s"]' % A.CAM_ID \
    if hasattr(A, "CAM_ID") else \
    '[data-director-track-draw-trail="director-track-camera-main"]'
PATH_PANEL = "[data-director-motion-path-menu]"
PRESET_TRIGGER = "[data-director-camera-preset-trigger]"
EXPORT_TRIGGER = "[data-director-export-trigger]"
TREE_BTN = "[data-director-panels-toggle]"

ARMS = [
    # path → preset，鼠标激活
    {"id": "bothByMouse", "order": ["path", "preset"], "via": "mouse"},
    # path → preset，**键盘**激活（键盘不产生 pointerdown ⟹ 专测那条假设）
    {"id": "bothByKeyboard", "order": ["path", "preset"], "via": "keyboard"},
    # ★ 反向：preset → path。互斥若只在一个方向显式，这个臂会测出来
    {"id": "reverseByMouse", "order": ["preset", "path"], "via": "mouse"},
    # 只开路径菜单（**判别力对照**）
    {"id": "pathOnly", "order": ["path"], "via": "none"},
]
ARM_IDS = [a["id"] for a in ARMS]

LISTEN = """()=>{const w=window;
 if(!w.__b783){
   w.__b783={cap:0, win:0};
   document.addEventListener('keydown',(e)=>{w.__b783.cap++;},true);
   window.addEventListener('keydown',(e)=>{w.__b783.win++;},false);
 }
 return {installed:true};}"""

READ = """()=>{const b=window.__b783; if(!b) return {err:'no'};
 const r={cap:b.cap, win:b.win}; b.cap=0; b.win=0; return r;}"""

# ★ 预设面板**没有**自己的 data 属性（`:1371` 只判 `presetPanelLeft !== null`）
#   ⟹ 用触发器的 `aria-expanded` 判它的开合 —— 那是它自己的 ARIA 契约，
#   比「我猜一个 class 名」可靠。
ST = """()=>{const t=document.querySelector('[data-director-camera-preset-trigger]');
 const ae=document.activeElement;
 return {pathOpen: !!document.querySelector('[data-director-motion-path-menu]'),
   presetExpanded: t ? t.getAttribute('aria-expanded') : null,
   presetOpen: t ? t.getAttribute('aria-expanded') === 'true' : null,
   exportOpen: !!document.querySelector('[data-director-export-panel]'),
   deskOpen: !!document.querySelector('[role="dialog"][aria-modal="true"]'),
   focusTag: ae?ae.tagName:null,
   focusIsPreset: ae ? (ae.getAttribute('data-director-camera-preset-trigger')!==null) : false};}"""

FOCUS = """(s)=>{const e=document.querySelector(s);
 if(!e) return {err:'no el'};
 if(e.disabled) return {err:'disabled'};
 e.focus({preventScroll:true});
 return {ok:document.activeElement===e};}"""


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
    # 导出面板**始终**开着 ⟹ 桌的阶梯那档永远有目标，
    # ⟹ 「两个 Timeline 主人关掉了」与「阶梯跑到了」可以区分开
    if not _click(pg, EXPORT_TRIGGER):
        R["FAILED"] = "★ 导出面板没打开 ⟹ 不是有效读数"
        return R
    # 第 1 个：按臂指定的顺序（`reverseByMouse` 是**预设面板先开**）
    first = arm["order"][0]
    _sel = PATH_TRIGGER if first == "path" else PRESET_TRIGGER
    if not _click(pg, _sel):
        R["FAILED"] = "★ 第 1 个触发器点不动：%s" % first
        return R
    R["afterFirst"] = pg.evaluate(ST)
    if not R["afterFirst"].get("pathOpen" if first == "path"
                               else "presetOpen"):
        R["FAILED"] = "★ 第一个面板没打开 ⟹ 不是有效读数"
        return R
    # 第 2 个
    if len(arm["order"]) > 1:
        second = arm["order"][1]
        sel = PATH_TRIGGER if second == "path" else PRESET_TRIGGER
        want = "pathOpen" if second == "path" else "presetOpen"
        if arm["via"] == "keyboard":
            f = pg.evaluate(FOCUS, sel)
            R["secondFocus"] = f
            if f.get("err") or not f.get("ok"):
                R["FAILED"] = "★ %s 聚焦失败：%s" % (second, f.get("err") or "未落上")
                return R
            pg.keyboard.press("Enter")
            pg.wait_for_timeout(SETTLE)
        else:
            if not _click(pg, sel):
                R["FAILED"] = "★ %s 触发器点不动（可能被 disabled）" % second
                return R
        R["secondVia"] = arm["via"]
        R["afterSecond"] = pg.evaluate(ST)
        if not R["afterSecond"].get(want):
            R["FAILED"] = "★ 第二个面板（%s）没打开 ⟹ 不是有效读数" % second
            return R
    else:
        R["secondVia"] = "none"
    pg.evaluate(LISTEN)
    # 把焦点挪到桌内的中性落点（**不产生 pointerdown** ⟹ 面板不会被外点关掉）
    f2 = pg.evaluate(FOCUS, TREE_BTN)
    R["focus"] = f2
    if f2.get("err") or not f2.get("ok"):
        R["FAILED"] = "桌内落点聚焦失败：%s" % (f2.get("err") or "未落上")
        return R
    R["stateBefore"] = pg.evaluate(ST)
    for i in range(PRESSES):
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(SETTLE + 150)
        R["presses"].append({"n": i + 1, "read": pg.evaluate(READ),
                             "state": pg.evaluate(ST)})
    return R


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rounds = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for rd in range(ROUNDS):
            rows = []
            for arm in ARMS:
                cell = None
                for t in range(RETRY):
                    pg = b.new_page()
                    pg.set_default_timeout(15000)
                    try:
                        pg.goto(BASE, wait_until="domcontentloaded")
                        A.settle(pg)
                        out = run_cell(pg, arm)
                    except Exception as e:  # noqa: BLE001
                        out = {"arm": arm["id"],
                               "FAILED": "%s: %s" % (type(e).__name__, e)}
                    finally:
                        try:
                            pg.close()
                        except Exception:  # noqa: BLE001
                            pass
                    out["tries"] = t + 1
                    out["retried"] = t > 0
                    if not out.get("FAILED"):
                        cell = out
                        break
                    cell = out
                rows.append(cell)
            rounds.append({"round": rd + 1, "rows": rows})
            print("round %d 完成" % (rd + 1), flush=True)
        b.close()
    OUT.write_text(json.dumps({"batch": 783, "arms": ARM_IDS, "presses":
                               PRESSES, "rounds": rounds},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
