#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 784 探针 A —— 「`sIP` 主人 + `bubble` 主人」**同时开着**时会怎样？

## 782/783 测过的都是「`sIP` 主人单独活着」或「两个 bubble 主人」

| 批 | 臂 | 组合 | 测到 |
| --- | --- | --- | --- |
| 782 批 | `captureOwner` | 模型库(`sIP`) **单独** | 模型库关；**阶梯跑不到** |
| 782 批 | `bubbleOwner` | 路径菜单(bubble) + 导出面板 | 两个都关（并发） |
| 783 批 | 四臂 | 两个时间轴面板 | 互斥（打开者里的交叉写入） |

⟹ **「一个 `sIP` 主人和一个 bubble 主人同时活着」这个格子，从来没被测过。**

## ★ 本批的承重预测（从源码逐行推出）

选一对**在不同组件、不同相位**的主人：

| 主人 | 相位 | 阻断 | 门状态 | 外点关闭？ |
| --- | --- | --- | --- | --- |
| `DirectorObjectTree.tsx:213` | bubble | **不**阻断 | `contextMenu` | ★ `window.addEventListener("mousedown", close)`（`:205`） |
| `DirectorViewport.tsx:2748` | **capture** | **`sIP`** | `modelLibraryOpen` | 有 `pointerdown`（`:2735`） |

★ 关键：右键菜单的关闭监听挂在 **`mousedown`** 上，而模型库触发器是
`<button type="button" onClick>`（`DirectorViewport.tsx:3568-3574`）——
**键盘 `Enter` 激活按钮只产生 `click`，不产生 `mousedown`/`pointerdown`**。

⟹ 由此得到**两条可 falsify 的预测**：

1. **鼠标**激活模型库 ⟹ 它的 `mousedown` 触发树的 `close` ⟹ **不会**同时开着
2. ★ **键盘**激活模型库 ⟹ **没有任何 pointer 事件** ⟹ **两个都开着**

## ★★ 而一旦共活，预测的是一个**新形态的伤害**

模型库那个主人是 **capture + `sIP`** ⟹ 它的 `sIP` 会把**整条链**截断
（782 已实测：那条臂 `cap=0`、阶梯跑不到）⟹ **树那个 bubble 主人的
`window` 监听器根本不会跑** ⟹

> **一次 Escape 只关掉模型库，右键菜单留在原地；要按第二次才关得掉。**

⟹ 这不是 D8（时间轴那两个菜单）的事 —— **这是「`sIP` 与 bubble 共活」的一般形态**，
而 782/783 的臂**一次都没落进这个格子**。若测到，D8a 的范围要**扩大**。

## 四个臂，两个按压（第二次是刻意的：要测「一次关不掉」）

| 臂 | 前置 | 预测 |
| --- | --- | --- |
| ★ `ctxThenLibMouse` | 右键树行 → **鼠标点**模型库触发器 | **不会**同时开（`mousedown` 关掉了右键菜单） |
| ★★ `ctxThenLibKeyboard` | 右键树行 → **键盘 `Enter`** 激活触发器 | ★★ **两个都开** |
| `ctxOnly`（对照） | 只右键 | 第 1 次关掉 |
| `libOnly`（对照） | 只点触发器 | 第 1 次关掉，且阶梯也跑（判别力） |
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
    "liblib-canvas-batch784-2026-10-01/raw/vb784a.json")
BASE = A.BASE
CAM = A.CAM
SETTLE = 260
PRESSES = 2          # ★ 第二次是刻意的：测「一次关不掉」
ROUNDS = 2
RETRY = 3

CTX_MENU = "[data-director-tree-context-menu]"
LIB_TRIGGER = "[data-director-model-library-trigger]"
LIB_PANEL = "[data-director-model-library-panel]"
EXPORT_TRIGGER = "[data-director-export-trigger]"
TREE_BTN = "[data-director-panels-toggle]"

ARMS = [
    {"id": "ctxThenLibMouse", "order": ["ctx", "lib"], "via": "mouse"},
    {"id": "ctxThenLibKeyboard", "order": ["ctx", "lib"], "via": "keyboard"},
    {"id": "ctxOnly", "order": ["ctx"], "via": "none"},
    {"id": "libOnly", "order": ["lib"], "via": "none"},
]
ARM_IDS = [a["id"] for a in ARMS]

LISTEN = """()=>{const w=window;
 if(!w.__b784){
   w.__b784={cap:0, win:0};
   document.addEventListener('keydown',(e)=>{w.__b784.cap++;},true);
   window.addEventListener('keydown',(e)=>{w.__b784.win++;},false);
 }
 return {installed:true};}"""

READ = """()=>{const b=window.__b784; if(!b) return {err:'no'};
 const r={cap:b.cap, win:b.win}; b.cap=0; b.win=0; return r;}"""

# ★ 右键菜单**没有** aria-expanded ⟹ 用它自己的 `data-*` 判；
#   模型库**有** `aria-expanded` ⟹ 用它自己的 ARIA 契约判（比猜 class 名可靠）
ST = """()=>{const t=document.querySelector('[data-director-model-library-trigger]');
 return {ctxOpen: !!document.querySelector('[data-director-tree-context-menu]'),
   libOpen: t ? t.getAttribute('aria-expanded') === 'true' : null,
   exportOpen: !!document.querySelector('[data-director-export-panel]'),
   deskOpen: !!document.querySelector('[role="dialog"][aria-modal="true"]')};}"""

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


# ★ 树行的真实选择器是 `[data-director-object-id]`，**不是**我一开始猜的
#   `data-director-object-row`；而 `dbg774a` 里也**没有** `MUG` 常量。
#   ⟹ 右键自带命中扫描（照 `A.click_tree_row` 的做法，但按**右键**），
#   目标用 `A.CAM`（已由 774–783 证明存在，且相机行**没有**「删除」项）。
HIT = """(id)=>{const t=document.querySelector('[data-director-tree]');
  const r=t&&t.querySelector('[data-director-object-id="'+id+'"]');
  if(!r) return {missing:true};
  const b=r.getBoundingClientRect();
  for(let f=0.12; f<=0.88; f+=0.08)
    for(let g=0.12; g<=0.88; g+=0.08){
      const x=Math.round(b.x+b.width*f), y=Math.round(b.y+b.height*g);
      if(x<2||y<2||x>innerWidth-2||y>innerHeight-2) continue;
      const e=document.elementFromPoint(x,y);
      if(e&&e.closest&&e.closest('[data-director-object-id="'+id+'"]')===r)
        return {pt:[x,y]};}
  return {noHit:true};}"""


def _right_click(pg, oid):
    s = pg.evaluate(HIT, oid)
    if not s.get("pt"):
        return False
    pg.mouse.click(s["pt"][0], s["pt"][1], button="right")
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
    # 导出面板**始终**开着 ⟹ 阶梯那档永远有目标，
    # ⟹ 「模型库那个 sIP 切断整条链」与「阶梯跑了」可以区分开
    if not _click(pg, EXPORT_TRIGGER):
        R["FAILED"] = "★ 导出面板没打开 ⟹ 不是有效读数"
        return R

    def open(which, via):
        if which == "ctx":
            # ★ 右键相机行（`A.CAM`，774–783 已证明存在；相机行**没有**
            #   「删除」项，而道具行有 —— 虽然我从不点菜单项，但少一个
            #   「万一点到就真删了」的面更稳）
            if not _right_click(pg, A.CAM):
                return "★ 右键目标点不动（相机行）"
            return None
        if via == "keyboard":
            f = pg.evaluate(FOCUS, LIB_TRIGGER)
            R["secondFocus"] = f
            if f.get("err") or not f.get("ok"):
                return "★ 模型库触发器聚焦失败：%s" % (f.get("err") or "未落上")
            pg.keyboard.press("Enter")
            pg.wait_for_timeout(SETTLE)
            return None
        if not _click(pg, LIB_TRIGGER):
            return "★ 模型库触发器点不动"
        return None

    for idx, which in enumerate(arm["order"]):
        via = arm["via"] if idx else "mouse"
        err = open(which, via)
        if err:
            R["FAILED"] = err
            return R
        st = pg.evaluate(ST)
        R["after%d" % (idx + 1)] = st
        key = {"ctx": "ctxOpen", "lib": "libOpen"}[which]
        if st.get(key) is not True:
            R["FAILED"] = "★ 第 %d 个（%s）没打开 ⟹ 不是有效读数" % (idx + 1,
                                                                   which)
            return R
    # ★ 记录**共活**判定（两个都开着 = 共活）
    both = arm["order"] == ["ctx", "lib"] and all(
        R["after%d" % (i + 1)].get(k) is True
        for i, k in enumerate(("ctxOpen", "libOpen")))
    R["coLive"] = bool(both)
    pg.evaluate(LISTEN)
    # 把焦点挪到桌内中性落点（**不产生 pointer 事件** ⟹ 面板不会被外点关掉）
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
                    cell = out
                    if not out.get("FAILED"):
                        break
                rows.append(cell)
            rounds.append({"round": rd + 1, "rows": rows})
            print("round %d 完成" % (rd + 1), flush=True)
        b.close()
    OUT.write_text(json.dumps({"batch": 784, "arms": ARM_IDS,
                               "presses": PRESSES, "rounds": rounds},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
