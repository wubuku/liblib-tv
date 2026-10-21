#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 824 探针 —— 「新建节点」的**纯 UI 链路**，给 811/812/814/815 的后门找替身

## ★ 这批要回答什么

811／812／814／815 四批的起点节点（脚本节点、图片节点……）**全部**是用
`window.__libtv_store.addNodeAtPosition(...)` 这个**后门**造的
（`canvasStore.ts:4344` 挂的，源站产品里根本不存在）。
⟹ ★★ **那四批测的东西，用户到底做不做得出来？** 本批去问。

★ batch 823 的教训已经写在前面：那份探针报「`[data-add-node-entry]`
一个都没有」，⟹ 差点被读成「产品没有新建节点的入口」
⟹ ★ 实际入口是**左栏「添加节点」**（`LeftSidebar.tsx:153`，渲染成
`button[aria-label="添加节点"]`）⟹ ★ **又是探针没找对**。

## ★ 本批的硬约束

1. ★ **零 store 写调用**：所有 store 访问只经 `RO()` 这个只读入口
   （验收器用**正则扫探针源码**自证）。
2. ★ **每步记「入口候选数」**：走不通时能区分「产品没有」与「探针没找到」。
3. ★ **绝对读数**：节点数、节点类型、坐标 —— 不靠「面板弹出来了」当结论。
4. ★ **真实鼠标**：点按钮用 `mouse.click`（产生 pointerdown），
   不用 `click()` 之外的程序化路径。

## ★ 顺带要回答的

★ 815 测出「七个派生动作连点三次会叠成三份、逐像素重叠」——
★ 那个结论**依赖 `addNodeAtPosition` 造出来的起点** ⟹ 本批要问：
**纯 UI 建出来的节点，派生动作的行为是不是一样的？**
"""
import json
import os
import pathlib
import sys
import time
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch774-2026-10-01" / "probes"))
import dbg774a as A  # noqa: E402

OUT = pathlib.Path(os.environ.get("VB824_OUT") or
                   (HERE.parent / "raw" / "vb824a.json"))

# ★★ 唯一的 store 只读入口。验收器扫源码自证：禁止任何 action 形式调用。
RO = """()=>{const S=window.__libtv_store.getState();
  const c=(S.canvases||[]).find(x=>x.id===S.activeCanvasId)||null;
  const nodes=(c&&c.nodes)||[];
  return {画布id:S.activeCanvasId,
          '★ 节点数':nodes.length,
          '★ 节点类型':nodes.map(n=>n.type||n.kind||null),
          '★ 新节点':nodes.slice(-4).map(n=>({
            id:n.id,type:n.type||n.kind||null,
            x:n.position?Math.round(n.position.x):null,
            y:n.position?Math.round(n.position.y):null,
            w:n.width||null,h:n.height||null})),
          '★ 选中节点':(S.selectedNodeIds||[]).slice(),
          '★ 边数':((c&&c.edges)||[]).length};}"""

# ★ 入口候选普查：把「这个入口存不存在」变成一个**可数**的读数
PROBE = """(sel)=>{
  const visible=(e)=>{const r=e.getBoundingClientRect();
    if(r.width===0&&r.height===0)return false;
    const cs=getComputedStyle(e);
    return cs.visibility!=='hidden'&&cs.display!=='none'
      && Number(cs.opacity||'1')>0;};
  const all=Array.from(document.querySelectorAll(sel));
  const vis=all.filter(visible);
  return {选择器:sel, 全部个数:all.length, 可见个数:vis.length,
          可见文字:vis.slice(0,12).map(e=>(e.textContent||'').trim()
            .replace(/\\s+/g,' ').slice(0,24)),
          可见标签:vis.slice(0,12).map(e=>(e.getAttribute('aria-label')
            ||e.getAttribute('title')||''))};}"""

ADD_BTN = 'button[aria-label="添加节点"]'

# ★★ 枚举每个条目的 **data 属性值**（不只是文字）
ENTRIES = """()=>Array.from(document.querySelectorAll('[data-add-node-entry]')).map(e=>({
  value:e.getAttribute('data-add-node-entry'),
  文本:(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,24),
  矩形:(()=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};})()}))"""


def cand(pg, sel):
    return pg.evaluate(PROBE, sel)


def safe_click(pg, sel):
    """★ 全程容错：找不到就记 'not-found'，**绝不抛异常**。"""
    try:
        el = pg.query_selector(sel)
    except Exception as exc:                                    # noqa: BLE001
        return {"结果": "error", "详情": str(exc)[:120]}
    if not el:
        return {"结果": "not-found", "选择器": sel}
    try:
        if el.is_disabled():
            return {"结果": "disabled", "选择器": sel,
                    "aria": el.get_attribute("aria-label")}
        el.click()
        return {"结果": "clicked", "选择器": sel}
    except Exception as exc:                                    # noqa: BLE001
        return {"结果": "click-error", "详情": str(exc)[:120]}


def real_click(pg, sel):
    """★ 真实鼠标点击（产生 pointerdown）—— 823 的教训：
    `select_option` 那种程序化路径**不产生 pointerdown**，算不得「纯 UI」。"""
    el = pg.query_selector(sel)
    if not el:
        return {"结果": "not-found", "选择器": sel}
    try:
        if el.is_disabled():
            return {"结果": "disabled", "选择器": sel}
        bb = el.bounding_box()
        if not bb:
            return {"结果": "no-box", "选择器": sel}
        pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
        return {"结果": "clicked", "选择器": sel, "矩形": bb}
    except Exception as exc:                                    # noqa: BLE001
        return {"结果": "click-error", "详情": str(exc)[:120]}


def run(b):
    out = {"步骤": [], "操作": {}}
    pg = b.new_page()
    pg.set_default_timeout(25000)
    try:
        pg.goto(A.BASE, wait_until="domcontentloaded")
        pg.wait_for_timeout(3200)

        # ── A0 起点
        c0 = pg.evaluate(RO)
        out["步骤"].append({
            "步骤": "A0·刚打开画布",
            "读数": c0,
            "★ 「添加节点」按钮候选": cand(pg, ADD_BTN),
            "★ 所有可见按钮（前 30）": cand(
                pg, 'button[aria-label], button[title]')})

        # ── A1 ★ 纯 UI 点左栏「添加节点」
        r1 = real_click(pg, ADD_BTN)
        out["操作"]["A1 点击添加节点"] = r1
        pg.wait_for_timeout(900)
        c1 = pg.evaluate(RO)
        entries = cand(pg, "[data-add-node-entry]")
        out["步骤"].append({
            "步骤": "A1·★ 点左栏「添加节点」",
            "读数": c1,
            "★ 点击": r1,
            "★ 面板条目候选": entries})

        # ── A2 枚举面板里**所有**条目（先看事实，不猜）
        sub = cand(pg, "[data-add-node-submenu]")
        out["步骤"].append({
            "步骤": "A2·★ 面板里有哪些条目／子菜单",
            "★ 条目候选": entries,
            "★ 子菜单候选": sub})

        # ── A3 ★★ 枚举每个条目的 **data 属性值**，再点「脚本」那条
        #   ★ 第一版猜了 `[data-add-node-submenu="script"]` 与
        #   `[data-add-node-entry="script-new"]` ⟹ 两个都 **not-found** ⟹
        #   ★ 「脚本」是**直接条目**、不是子菜单 ⟹ **先读属性再点**。
        ents = pg.evaluate(ENTRIES)
        out["步骤"].append({
            "步骤": "A3·★★ 枚举面板条目的 **data 属性值**",
            "★ 条目": ents})
        script_val = None
        for e in ents:
            if "脚本" in e["文本"]:
                script_val = e["value"]
                break
        out["操作"]["A3 脚本条目的 value"] = script_val

        # ── A4 ★★★ 纯 UI 建一个脚本节点：**顺序**是关键
        #   ★ 第一版顺序错了：直接找 `[data-add-node-entry="script-new"]` ⟹
        #   not-found ⟹ ★ **差点把「新建节点没有纯 UI 入口」写成结论**。
        #   ★ 真因（`AddNodePanel.tsx:206`）：**「脚本」这一条是
        #   `entry.action === "script"`** ⟹ 它的 onClick **只展开子菜单**
        #   （`setScriptSubmenuOpen`）、**不建节点** ⟹ 所以「点它节点数不变」
        #   是**正确行为**，不是糊弄点。
        #   ★ 正确顺序：左栏「添加节点」→ 点「脚本」（展开子菜单）
        #   → 点「新建脚本」⟹ **节点数 +1**。
        n_before = pg.evaluate(RO)["★ 节点数"]
        types_before = pg.evaluate(RO)["★ 节点类型"]
        real_click(pg, ADD_BTN)
        pg.wait_for_timeout(800)
        r4a = real_click(pg, '[data-add-node-entry="script"]')
        pg.wait_for_timeout(900)
        subs = pg.evaluate("""()=>Array.from(document.querySelectorAll(
            '[data-add-node-submenu]')).map(e=>({
          value:e.getAttribute('data-add-node-submenu'),
          文本:(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,24),
          矩形:(()=>{const r=e.getBoundingClientRect();
            return {x:Math.round(r.x),y:Math.round(r.y),
                    w:Math.round(r.width),h:Math.round(r.height)};})()}))""")
        out["步骤"].append({
            "步骤": "A4·★★★ 点「脚本」**展开子菜单**（★ 它本来就不建节点）",
            "★ 点击": r4a, "★ 展开后的子菜单": subs})
        # ★★★ 探针返工（**第三次**栽在选择器上）：
        #   第二版我找 `[data-add-node-submenu="script-new"]` ⟹ not-found
        #   ⟹ ★ 真因是**属性名拼错**：**子菜单容器**是
        #   `data-add-node-submenu="script"`，而**容器里的条目**是
        #   `data-add-node-entry="script-new"`（`AddNodePanel.tsx:248`）。
        #   ⟹ ★★ 纪律：**先枚举、再点**（A3 做了，A4b 忘了）。
        sub_entries = pg.evaluate("""()=>Array.from(document.querySelectorAll(
            '[data-add-node-submenu] [data-add-node-entry]')).map(e=>({
          value:e.getAttribute('data-add-node-entry'),
          文本:(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,24),
          矩形:(()=>{const r=e.getBoundingClientRect();
            return {x:Math.round(r.x),y:Math.round(r.y),
                    w:Math.round(r.width),h:Math.round(r.height)};})()}))""")
        out["步骤"][-1]["★ 子菜单内部的条目"] = sub_entries
        new_val = None
        for e in sub_entries:
            if "NEW" in e["文本"] or "脚本" in e["文本"]:
                new_val = e["value"]
                break
        out["操作"]["A4 新建脚本条目的 value"] = new_val
        r4 = real_click(pg, '[data-add-node-entry="%s"]' % new_val) if new_val \
            else {"结果": "not-found", "说明": "子菜单里没枚举到条目"}
        out["操作"]["A4 点新建脚本"] = r4
        pg.wait_for_timeout(1600)
        c4 = pg.evaluate(RO)
        out["步骤"].append({
            "步骤": "A4b·★★★ 点「新建脚本」⟹ **节点数真的 +1**？",
            "★ 点击": r4,
            "★ 节点数（点之前）": n_before,
            "★ 节点数（点之后）": c4["★ 节点数"],
            "★ 多了": c4["★ 节点数"] - n_before,
            "★ 类型（点之前）": types_before,
            "★ 类型（点之后）": c4["★ 节点类型"],
            "读数": c4})


        # ── A5 ★ 纯 UI 建出来的节点**类型**是不是脚本？
        out["步骤"].append({
            "步骤": "A5·★ 新建出来的节点类型",
            "★ 节点类型": c4["★ 节点类型"],
            "★ 新节点": c4["★ 新节点"]})

        # ── A6 ★ 再建一个 ⟹ **位置**是不是叠在一起？
        #   （815 的结论是「派生节点三份逐像素重叠」⟹ 那是 `addDerivedNode`
        #     的性质；这里验的是**纯 UI 新建**的位置是不是也固定）
        real_click(pg, ADD_BTN)
        pg.wait_for_timeout(700)
        real_click(pg, '[data-add-node-submenu="script"]')
        pg.wait_for_timeout(600)
        real_click(pg, '[data-add-node-entry="script-new"]')
        pg.wait_for_timeout(1400)
        c6 = pg.evaluate(RO)
        out["步骤"].append({
            "步骤": "A6·★ 纯 UI 连续新建两个 ⟹ 位置一样吗",
            "读数": c6,
            "★ 最后两个节点": c6["★ 新节点"][-2:]})

        # ── A7 ★★ 关键：纯 UI 建出来的节点，**派生动作**行为是不是 815 那样？
        #   815 的结论依赖后门造的起点 ⟹ 本批验「纯 UI 起点」下是否一致
        n7 = pg.evaluate(RO)["★ 节点数"]
        # 选中刚建的脚本节点（点它的 DOM 中心）
        target = pg.evaluate("""()=>{
          const els=Array.from(document.querySelectorAll(
            '.react-flow__node'));
          const e=els[els.length-1];
          if(!e)return null;
          const r=e.getBoundingClientRect();
          return {id:e.getAttribute('data-id'),
                  x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)};}""")
        out["操作"]["A7 目标节点"] = target
        if target:
            pg.mouse.click(target["x"], target["y"])
        pg.wait_for_timeout(800)
        c7 = pg.evaluate(RO)
        out["步骤"].append({
            "步骤": "A7·★★ 点刚建的节点 ⟹ 选中了？",
            "读数": c7,
            "★ 选中节点": c7["★ 选中节点"]})

        # ── A8 ★★ clone 的**画布右键菜单**里有没有「添加节点」？
        #   ★ 源站第一手事实：右键菜单里有「添加节点」（178×32，
        #   位于菜单第三项）⟹ 这是本批要对照的那一格。
        pg.mouse.click(1200, 640)
        pg.wait_for_timeout(700)
        pg.mouse.click(1200, 640, button="right")
        pg.wait_for_timeout(1200)
        menu = pg.evaluate("""()=>{
          const visible=(e)=>{const r=e.getBoundingClientRect();
            if(r.width===0&&r.height===0)return false;
            const cs=getComputedStyle(e);
            return cs.visibility!=='hidden'&&cs.display!=='none'
              && Number(cs.opacity||'1')>0;};
          const out=[];
          for(const e of Array.from(document.querySelectorAll(
              'button,[role=menuitem],[role=menu] li,[role=menu] button'))){
            if(!visible(e))continue;
            const r=e.getBoundingClientRect();
            out.push({文本:(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,26),
                      aria:e.getAttribute('aria-label')||'',
                      role:e.getAttribute('role')||'',
                      矩形:{x:Math.round(r.x),y:Math.round(r.y),
                            w:Math.round(r.width),h:Math.round(r.height)}});}
          return out;}""")
        # ★★ 判据收紧：第一版的选择器匹配了**全页** button ⟹ 左栏那个
        #   「添加节点」也被算进去 ⟹ 判据是**假的**。⟹ 只取**右下角**那一簇。
        menu_items = [m for m in menu
                      if m["矩形"]["x"] >= 1100 and m["矩形"]["y"] >= 640]
        out["步骤"].append({
            "步骤": "A8·★★ **画布右键菜单**里有哪些项（★ 对照源站的「添加节点」）",
            "★ 右下角那一簇（=右键菜单）": menu_items,
            "★ 有「添加节点」吗": any("添加节点" in m["文本"] for m in menu_items),
            "★ 菜单项文本": [m["文本"] for m in menu_items]})

        # ── A9 ★★ clone 的**底部工具条**有没有源站那个白底加号？
        bottom = pg.evaluate("""()=>{
          const visible=(e)=>{const r=e.getBoundingClientRect();
            if(r.width===0&&r.height===0)return false;
            const cs=getComputedStyle(e);
            return cs.visibility!=='hidden'&&cs.display!=='none';};
          const out=[];
          for(const e of Array.from(document.querySelectorAll('button,a,[role=button]'))){
            if(!visible(e))continue;
            const r=e.getBoundingClientRect();
            if(r.y<700)continue;                 // ★ 只看底部
            out.push({文本:(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,20),
                      aria:e.getAttribute('aria-label')||'',
                      矩形:{x:Math.round(r.x),y:Math.round(r.y),
                            w:Math.round(r.width),h:Math.round(r.height)}});}
          return out;}""")
        out["步骤"].append({
            "步骤": "A9·★★ clone 底部工具条（★ 源站那里有个白底加号）",
            "★ 底部可点元素": bottom})

        return out
    except Exception as exc:                                    # noqa: BLE001
        out["★ 异常"] = {"类型": type(exc).__name__, "详情": str(exc)[:300]}
        return out
    finally:
        pg.close()


def main():
    out = {"★ 探针自身失败": None}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        try:
            out = run(br)
        except Exception as exc:                                # noqa: BLE001
            out = {"★ 探针自身失败": {"类型": type(exc).__name__,
                                       "详情": str(exc)[:400]}}
        finally:
            br.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print("步数", len(out.get("步骤", [])))


if __name__ == "__main__":
    main()
