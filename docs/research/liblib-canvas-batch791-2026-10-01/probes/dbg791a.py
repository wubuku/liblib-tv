#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 791 探针 —— 「双击空白画布开添加节点面板」这条入口到底通不通

## 承重事实（来自 batch 758，本批要**重新确认**而不是直接引用）

`src/app/page.tsx` 在画布容器上注册了一个 `dblclick` 监听器，
但注册在**冒泡**阶段；而 React Flow 在 pane 处 `stopPropagation` 掉了
`dblclick`。758 实测的事件路径是：

    容器**捕获** 1 → pane 冒泡 1 → **断**

⟹ 挂在容器上等冒泡的那个监听器**永远收不到**。

★ 758 是旧读数，改 `src/` 前必须先确认**缺陷还在**（`pre` / `post`
用**同一份**测量代码，差异只能来自 `src/`）。

## 三条入口分开量

| 臂 | 入口 | 作用 |
| --- | --- | --- |
| ★ 处理臂 | **双击空白画布** | 就是坏掉的那条 |
| ★ 阳性对照一 | **`Tab` 键** | 同一个面板的另一条入口（`page.tsx:1360`） |
| ★ 阳性对照二 | **左栏按钮双击** | 758 用过的那条 |

★ 没有阳性对照，「入口坏了」与「我的双击没送到」无法区分（755 的 R18 / 758 的 R24）。

## 顺带读事件相位

不只数面板条目，还要读**事件走到了哪一相位** ⟹ 「收不到」这个机制说法
是被读出来的，不是抄 758 的。

## 格数

3 臂 × 2 轮 × {pre, post} = 每次运行 6 格
"""
import json
import pathlib
import sys
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch774-2026-10-01" / "probes"))
import dbg774a as A  # noqa: E402

PHASE = sys.argv[1] if len(sys.argv) > 1 else "pre"
assert PHASE in ("pre", "post"), "★ 阶段只能是 pre / post，收到 %r" % PHASE

OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/research/"
    "liblib-canvas-batch791-2026-10-01/raw/vb791a-%s.json" % PHASE)

ENTRY = "[data-add-node-entry]"

#: ★ 找一块**真的是空白画布**的点：pane 的 rect 内、且 elementFromPoint 落在 pane 上
FIND_PANE_POINT = """()=>{
  const pane=document.querySelector('.react-flow__pane');
  if(!pane) return {FAILED:'没有 pane'};
  const r=pane.getBoundingClientRect();
  for(let f=0.06; f<=0.94; f+=0.04)
    for(let g=0.06; g<=0.94; g+=0.04){
      const x=Math.round(r.left+r.width*f), y=Math.round(r.top+r.height*g);
      if(x<2||y<2||x>innerWidth-2||y>innerHeight-2) continue;
      const e=document.elementFromPoint(x,y);
      // ★ 必须是 pane **自己**，不能在任何节点上
      if(e && e.closest && e.closest('.react-flow__pane')===pane)
        return {pt:[x,y], isPane:true, tag:e.tagName,
                nodeUnder: !!e.closest('.react-flow__node')};
    }
  return {FAILED:'pane 内找不到空白点'};}"""

#: ★ 事件相位计数器：容器捕获 / 容器冒泡 / window 捕获
INSTALL_COUNTERS = """(containerSel)=>{
  window.__b791={cap:0, bub:0, winCap:0, paneBub:0};
  const c=document.querySelector(containerSel);
  if(!c) return {ok:false, why:'容器没找到'};
  c.addEventListener('dblclick',()=>{window.__b791.cap++;},true);
  c.addEventListener('dblclick',()=>{window.__b791.bub++;},false);
  window.addEventListener('dblclick',()=>{window.__b791.winCap++;},true);
  const p=document.querySelector('.react-flow__pane');
  if(p) p.addEventListener('dblclick',()=>{window.__b791.paneBub++;},false);
  return {ok:true, containerTag:c.tagName};}"""

READ_COUNTERS = "()=>window.__b791||null"

COUNT_ENTRIES = "()=>document.querySelectorAll('%s').length" % ENTRY

CONTAINER_SEL = None  # 运行时探测


def boot(pg):
    pg.goto(A.BASE, wait_until="domcontentloaded")
    pg.evaluate(A.CLEAR_LS, A.LS_KEY)
    pg.set_viewport_size({"width": 1440, "height": 1000})
    pg.goto(A.BASE, wait_until="networkidle")
    pg.wait_for_selector(".react-flow__node", timeout=25000)
    pg.wait_for_timeout(1200)


def close_panel(pg):
    """★ 关掉面板并**确认**真的关了（不靠假设）。"""
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(320)
    return pg.evaluate(COUNT_ENTRIES)


def probe_container(pg):
    """★ 找出画布容器（`.react-flow` 那一层），别写死选择器。"""
    return pg.evaluate("""()=>{
      const pane=document.querySelector('.react-flow__pane');
      if(!pane) return null;
      let n=pane.parentElement;
      while(n && !n.className.toString().includes('react-flow'))
        n=n.parentElement;
      const c = n || pane.parentElement;
      c.setAttribute('data-b791-container','1');
      return c.tagName+'.'+c.className.toString().slice(0,60);}""")


def arm_dblclick_pane(pg):
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(300)
    before = pg.evaluate(COUNT_ENTRIES)
    pt = pg.evaluate(FIND_PANE_POINT)
    if pt.get("FAILED"):
        return {"arm": "dblclickPane", "FAILED": pt["FAILED"], "before": before}
    pg.evaluate(INSTALL_COUNTERS, "[data-b791-container]")
    pg.mouse.dblclick(pt["pt"][0], pt["pt"][1])
    pg.wait_for_timeout(420)
    after = pg.evaluate(COUNT_ENTRIES)
    counters = pg.evaluate(READ_COUNTERS)
    return {"arm": "dblclickPane", "point": pt["pt"], "pointIsPane": pt.get("isPane"),
            "nodeUnderPoint": pt.get("nodeUnder"),
            "before": before, "after": after,
            "panelOpened": after > 0, "counters": counters}


def arm_tab(pg):
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(300)
    before = pg.evaluate(COUNT_ENTRIES)
    pg.keyboard.press("Tab")
    pg.wait_for_timeout(420)
    after = pg.evaluate(COUNT_ENTRIES)
    return {"arm": "tabKey", "before": before, "after": after,
            "panelOpened": after > 0}


def arm_sidebar_dblclick(pg):
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(300)
    before = pg.evaluate(COUNT_ENTRIES)
    s = pg.evaluate("""(ent)=>{
      // ★ 阳性对照二的入口是左栏的「添加节点」工具按钮
      //   （`LeftSidebar.tsx:153` 的 `<ToolButton label="添加节点">`），
      //   **不是**面板里的 `data-add-node-entry`（那是面板打开后才有的）。
      const b=[...document.querySelectorAll('button')]
        .find(x=>(x.textContent||'').trim().includes('添加节点'));
      if(!b) return {missing:true};
      const r=b.getBoundingClientRect();
      if(!r.width||!r.height) return {zero:true};
      return {pt:[Math.round(r.left+r.width/2),
                  Math.round(r.top+r.height/2)],
              label:(b.textContent||'').trim().slice(0,12)};}""", ENTRY)
    if not s.get("pt"):
        return {"arm": "sidebarDblclick", "FAILED": "左栏找不到入口按钮",
                "before": before, "probe": s}
    pg.mouse.dblclick(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(420)
    after = pg.evaluate(COUNT_ENTRIES)
    return {"arm": "sidebarDblclick", "label": s.get("label"),
            "before": before, "after": after, "panelOpened": after > 0}


def arm_context_menu(pg):
    """★ 阳性对照二：右键菜单里的「添加节点」
    （`page.tsx:1592-1596` → `CanvasContextMenu.tsx:122`
    的 `data-canvas-context-item="添加节点"`）。

    ★ 原本的第二对照是「左栏按钮双击」（758 用过），但第一版探针**找不到**
      那个按钮：`ToolButton` 的 label 不是 button 的 textContent，
      运行时把 x<200 的可交互节点全列了一遍也没有它 ⟹ 入口选错，
      不是入口坏。⟹ 换成有精确锚点、代码路径有记录的那一条。
    """
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(300)
    before = pg.evaluate(COUNT_ENTRIES)
    pt = pg.evaluate(FIND_PANE_POINT)
    if pt.get("FAILED"):
        return {"arm": "contextMenu", "FAILED": pt["FAILED"], "before": before}
    pg.mouse.click(pt["pt"][0], pt["pt"][1], button="right")
    pg.wait_for_timeout(420)
    item = pg.evaluate("""()=>{const b=document.querySelector(
        '[data-canvas-context-item="添加节点"]');
      if(!b) return {missing:true};
      const r=b.getBoundingClientRect();
      return {pt:[Math.round(r.left+r.width/2),
                  Math.round(r.top+r.height/2)]};}""")
    if not item.get("pt"):
        return {"arm": "contextMenu", "FAILED": "右键菜单里没有「添加节点」",
                "before": before, "item": item}
    pg.mouse.click(item["pt"][0], item["pt"][1])
    pg.wait_for_timeout(420)
    after = pg.evaluate(COUNT_ENTRIES)
    return {"arm": "contextMenu", "before": before, "after": after,
            "panelOpened": after > 0}


def arm_dblclick_node(pg):
    """★ **回归臂**：双击**节点**（不是空白画布）⟹ 面板**不该**开。

    ★ 这是本批修复最关键的回归风险：监听器改成**捕获**阶段之后，
      容器内**所有**双击都会经过它（包括节点上的），只有
      `target.closest(".react-flow__pane")` 这道闸挡着。
      ⟹ 必须实测这道闸还在，不能靠「代码里写着呢」。
    """
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(300)
    before = pg.evaluate(COUNT_ENTRIES)
    node = pg.evaluate("""()=>{
      const ns=[...document.querySelectorAll('.react-flow__node')]
        .filter(n=>{const r=n.getBoundingClientRect();
          return r.width>40 && r.height>40
            && r.left>2 && r.top>2
            && r.right<innerWidth-2 && r.bottom<innerHeight-2;});
      const n=ns[0]; if(!n) return {missing:true};
      const r=n.getBoundingClientRect();
      return {pt:[Math.round(r.left+r.width/2),
                  Math.round(r.top+r.height/2)],
              id:n.getAttribute('data-id')};}""")
    if not node.get("pt"):
        return {"arm": "dblclickNode", "FAILED": "找不到可双击的节点",
                "before": before, "node": node}
    pg.mouse.dblclick(node["pt"][0], node["pt"][1])
    pg.wait_for_timeout(420)
    after = pg.evaluate(COUNT_ENTRIES)
    return {"arm": "dblclickNode", "point": node["pt"],
            "nodeId": node.get("id"),
            "before": before, "after": after,
            "panelOpened": after > 0}


ARMS = [("dblclickPane", arm_dblclick_pane),
        ("dblclickNode", arm_dblclick_node),
        ("tabKey", arm_tab),
        ("contextMenu", arm_context_menu)]


def main():
    rounds = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        for rd in range(2):
            rows = []
            for name, fn in ARMS:
                cell, tries = None, 0
                for t in range(3):
                    pg = b.new_page()
                    pg.set_default_timeout(15000)
                    tries = t + 1
                    try:
                        boot(pg)
                        c = probe_container(pg)
                        if not c:
                            cell = {"arm": name, "FAILED": "找不到画布容器"}
                        else:
                            cell = fn(pg)
                            cell["container"] = c
                    except Exception as e:      # noqa: BLE001
                        cell = {"arm": name,
                                "FAILED": "%s: %s" % (type(e).__name__, e)}
                    finally:
                        try:
                            pg.close()
                        except Exception:       # noqa: BLE001
                            pass
                    if not cell.get("FAILED"):
                        break
                cell["tries"] = tries
                rows.append(cell)
                if cell.get("FAILED"):
                    msg = "FAILED:%s" % cell["FAILED"]
                else:
                    extra = ""
                    if cell.get("counters"):
                        k = cell["counters"]
                        extra = " | 容器捕获=%d 容器冒泡=%d pane冒泡=%d" % (
                            k.get("cap", -1), k.get("bub", -1), k.get("paneBub", -1))
                    msg = "条目 %d → %d%s" % (cell["before"], cell["after"], extra)
                print("  r%d %-16s %s" % (rd + 1, name, msg), flush=True)
            rounds.append({"round": rd + 1, "rows": rows})
        b.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"batch": 791, "phase": PHASE, "rounds": rounds},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
