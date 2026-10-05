#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 777 探针 A —— **删除之后用户有没有出路？**

## 上一批挂着什么

763 挂起的 D1 有**两半**。776 结清了前半句（Escape 死键与它的修法依据），
后半句至今**零读数**：

> 导演台删除破坏性且跨 reload 持久化，却无「未保存/重置」提示

这句话把三件事捆在一起，而它们**可以互相独立地真或假**：

1. 删除**破坏性**吗？（不可逆？）
2. 删除**跨 reload 持久化**吗？
3. 有**「未保存/重置」提示**吗？

把它们捆成一句的后果是：即使「可撤销」成立，「无提示」仍然成立 ——
**用户看不到出路，不等于出路不存在。** 本批把它们**拆开**测，
因为「不可逆」与「无入口」是两种严重度完全不同的缺陷。

## ★ 方法学上最要紧的一条：落点必须在删除**之后**设置

第一版把「焦点在检查器输入框」当落点，但**删除动作本身把焦点移走了**
（点的是树工具条上的删除按钮）⟹ 按 Cmd+Z 时焦点根本不在输入框 ⟹
「两种落点结果相同」是我的**实验设计失败**，不是机制。

第二版又踩了一次：删掉的就是**当前选中对象** ⟹ 检查器字段随之消失 ⟹
「焦点在输入框」这一臂根本没成立（`err: no el`）。

⟹ 第三版用**按行删除按钮** `[data-director-delete-object="<id>"]` ——
它带 `event.stopPropagation()`（`DirectorObjectTree.tsx:537-538`）⟹
**不改选中** ⟹ 被选中相机的 FOV 滑杆在删除之后**仍在屏上**，
「撤销时焦点在输入框」才成为一格真正的读数。

★ **落点的定义是「删除之后用户所在的地方」，不是「删除之前」。**

## 读数

| 读数 | 怎么读 | 说明 |
| --- | --- | --- |
| 可撤销性 | 对象是否回到 `objectIds`、`history-future` | **用户可见**的后果 |
| 是否进历史 | `data-director-history-past`（桌根只读属性） | 决定「理论可不可撤销」 |
| 提示 | 桌内 `[role=status]/[role=alert]/[aria-live]` 的文本 + 撤销类按钮计数 | ★ 桌里有一块**常驻的命令反馈面板**（`DirectorDesk.tsx:1008`），而 `getDirectorCommandFeedback` 对 `COMMITTED` **返回 `null`** ⟹ 成功删除后它显示占位文案「无命令反馈」 |
| 跨 reload 持久化 | **普通 reload**（★ **不能用 `fresh()`**，它会清 localStorage） | `fresh()` 清库会重置项目，那测的是另一件事 |

★ 读属性时**别把选择器当属性名**传给 `getAttribute`（第一版这么写 ⟹
永远读到空串，而「空串」看起来像「历史是空的」）。
## 探针教训（本批抓自己的）

- **R119** —— ★**落点必须设在「动作之后」，不是「动作之前」。**
  第一版把「焦点在检查器输入框」当落点，但**删除动作自己把焦点移走了**
  （点的是树工具条上的删除按钮）⟹「两种落点结果相同」是**实验设计失败**，
  不是机制。第二版删掉的又正好是**当前选中对象** ⟹ 检查器字段随之消失 ⟹
  那一臂根本没成立。第三版改用**按行删除按钮**（`stopPropagation()` ⟹
  不改选中）才让输入框在删除后留在屏上。
- **R120** —— ★**两格若实测落在同一个元素上，它们就是同一格。**
  「对象树」臂的落点 `[data-director-tree]` **不可聚焦** ⟹ 焦点掉到 `BODY`
  ⟹ 它与「body」臂**完全重复**。合并它们等于把「非输入框焦点」只测了一次
  却报成两次。⟹ 现在补一个**真的能聚焦的非输入控件**作独立臂，
  并在探针里**自证**「这一格与 body 臂不重复」，重复就记 FAILED 而不是照报。
- **R121** —— ★**读属性时别把选择器当属性名**：`getAttribute('[data-x]')`
  永远返回 `null` ⟹ 读到空串 ⟹ 而**空串看起来像「历史是空的」**。
  另一条同族：这些属性挂在 `role="dialog"` **元素本身**上，
  而 `d.querySelector()` **只搜后代** ⟹ 第二版读成「读数方法不成立」。
- **R122** —— ★**「可撤销」与「有入口」是两种不同的缺陷。**
  763 那句「删除破坏性且跨 reload 持久化，却无『未保存/重置』提示」把三件事
  捆在一起，于是「Cmd+Z 确实能撤销」会把「无提示」一起放过。
  本批把它们**拆成三个独立读数**再合议。
"""
import json
import pathlib
import sys
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
# ★ 跨批 import 774 的探针基础设施（桌的开启、对象树点击、扫描点击）
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch774-2026-10-01" / "probes"))
import dbg774a as A  # noqa: E402

OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/research/"
    "liblib-canvas-batch777-2026-10-01/raw/vb777a.json")

MUG = "director-prop-mug"          # 被删的对象（道具，可删）
CAM = A.CAM                          # 选中的对象（相机，**不可删**，
                                    #  它的 FOV 滑杆用来承载「输入框焦点」）
FOV = "[data-director-camera-fov]"
TREE = "[data-director-tree]"
#: ★ 第三臂要落在一个**真的能聚焦、且不是输入框**的桌内控件上。
#:   原本的 `tree` 臂落点是 `[data-director-tree]`，而它**不可聚焦**
#:   （775 已记过：treeContainer 落点只能把焦点放到容器上，而容器没有 tabindex）
#:   ⟹ 实测焦点掉到 `BODY` ⟹ 「tree」与「body」**不是两格**，只是同一格。
#:   合并它们等于把「非输入框焦点」这一类**只测了一次**，却报成两次。
DESK_BTN = "[data-director-panels-toggle]"
DEL_ROW = '[data-director-delete-object="%s"]' % MUG
SETTLE = 600
MAX_TRIES = 3

# ★ 属性要用**属性名**读，不是选择器（第一版把选择器传进 getAttribute）
# ★ 且必须从 `document` 查：`data-director-history-past` 挂在
#   `role="dialog"` 那个元素**本身**上，而 `d.querySelector` **只搜后代**
#   ⟹ 第二版读成「读数方法不成立」。顺带记下它挂在哪个元素上，供自证。
STATE = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 const at=(n)=>{const e=document.querySelector('['+n+']');
   return e? {v:(e.getAttribute(n)||''),
     onDialog: !!(d && e===d),
     inDesk: !!(d && d.contains(e))} : null;};
 const g=(n)=>{const r=at(n); return r? r.v : null;};
 const ae=document.activeElement;
 const live=[...(d?d.querySelectorAll('[role="status"],[role="alert"],[aria-live]'):[])]
   .map(e=>(e.textContent||'').trim()).filter(Boolean);
 const undoish=[...(d?d.querySelectorAll('button,a,[role="button"]'):[])].filter(e=>
   /撤销|还原|恢复|已删除|重新添加/.test((e.textContent||'')
     +(e.getAttribute('aria-label')||'')+(e.getAttribute('title')||'')));
 return {past:g('data-director-history-past'),
   future:g('data-director-history-future'),
   pastOnDialog:(at('data-director-history-past')||{}).onDialog,
   pastInDesk:(at('data-director-history-past')||{}).inDesk,
   lastCommand:g('data-director-last-command'),
   lastDisposition:g('data-director-last-disposition'),
   lastReason:g('data-director-last-reason'),
   focusTag: ae? ae.tagName : null,
   focusType: ae? ae.getAttribute('type') : null,
   focusInInput: !!(ae && (ae.tagName==='INPUT'||ae.tagName==='TEXTAREA'
     ||ae.tagName==='SELECT')),
   liveTexts: live,
   undoishCount: undoish.length,
   undoishLabels: undoish.slice(0,4).map(e=>(e.textContent||'')
     .trim().slice(0,12)),
   dialogsInDesk: d? d.querySelectorAll('[role="dialog"]').length : 0};}"""

FOCUS_SEL = """(a)=>{const [sel,mode]=a;
  const d=document.querySelector('[role="dialog"][aria-modal="true"]');
  if(!d) return {err:'no desk'};
  let el=null;
  if(mode==='body'){ el=document.body; }
  else { el=d.querySelector(sel); }
  if(!el) return {err:'no el for '+mode};
  if(el.disabled) return {err:'disabled'};
  let ok=false;
  try{ el.focus({preventScroll:true}); ok=document.activeElement===el; }
  catch(e){ return {err:'focus threw'};}
  return {ok:ok, tag:el.tagName, type:el.getAttribute('type')};}"""

DESK_PRESENT = """()=>{const d=document.querySelector(
    '[role="dialog"][aria-modal="true"]');
  return {open: !!d && !!d.querySelector('[data-director-tree]')};}"""

OPEN_DESK = """()=>{const s=document.querySelector('[data-open-director]');
  if(!s) return {err:'no trigger'};
  const r=s.getBoundingClientRect();
  return {pt:[r.x+r.width/2, r.y+r.height/2]};}"""


def _selfcheck(pg):
    r = A.fresh(pg)
    if r.get("FAILED"):
        return False, "导演台没开"
    st = pg.evaluate(STATE)
    if st.get("past") is None:
        return False, "桌根没有 data-director-history-past（读数方法不成立）"
    if st.get("past") != "0" or st.get("future") != "0":
        return False, "起始历史非干净（past=%s future=%s）—— 这一格不是有效读数" % (
            st.get("past"), st.get("future"))
    return True, None


def _delete_mug(pg):
    """用**按行删除按钮**删道具 —— 它 `stopPropagation()` ⟹ 不改选中 ⟹
    被选中相机的字段在删除后仍在屏上（这是让「输入框焦点」成为一格的前提）。"""
    s = pg.evaluate(A.SCAN_CLICK, DEL_ROW)
    if not s.get("pt"):
        return False, "按行删除按钮点不动（%r）" % s
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(SETTLE + 200)
    return True, None


def run_cell(pg, landing):
    """删道具 → **删除之后**设落点 → 按 Cmd+Z → 量能不能撤销。"""
    R = {"landing": landing}
    ok, why = _selfcheck(pg)
    if not ok:
        R["FAILED"] = why
        return R
    A.click_tree_row(pg, CAM)
    A.settle(pg)
    sel = (pg.evaluate(A.TREE) or {}).get("selectedIds") or []
    if CAM not in sel:
        R["FAILED"] = "相机没选中（选中=%r）" % sel
        return R
    R["selected"] = sel
    R["before"] = pg.evaluate(STATE)
    R["objectsBefore"] = len((pg.evaluate(A.TREE) or {}).get("objectIds") or [])
    ok, why = _delete_mug(pg)
    if not ok:
        R["FAILED"] = why
        return R
    ids = (pg.evaluate(A.TREE) or {}).get("objectIds") or []
    R["objectsAfterDelete"] = len(ids)
    R["mugGone"] = MUG not in ids
    R["afterDelete"] = pg.evaluate(STATE)
    R["selectionKept"] = CAM in ((pg.evaluate(A.TREE) or {}).get("selectedIds") or [])
    if not R["mugGone"]:
        R["FAILED"] = "★ 删除后道具还在 —— 这一格不是有效读数"
        return R
    if not R["selectionKept"]:
        R["FAILED"] = "★ 按行删除改选了 —— 「输入框留在屏上」的前提没了"
        return R
    # ── 删除**之后**才设落点
    selmap = {"fovInput": FOV, "tree": TREE, "body": "body",
              "deskButton": DESK_BTN}
    modemap = {"fovInput": "input", "tree": "sel", "body": "body",
               "deskButton": "sel"}
    f = pg.evaluate(FOCUS_SEL, [selmap[landing], modemap[landing]])
    R["focus"] = f
    if f.get("err"):
        R["FAILED"] = "落点放不进去：%s" % f["err"]
        return R
    pg.wait_for_timeout(500)
    R["atLanding"] = pg.evaluate(STATE)
    if not R["atLanding"].get("focusInInput") and landing == "fovInput":
        R["FAILED"] = "★ 焦点没落在输入框上（实测 tag=%s type=%s）" % (
            R["atLanding"].get("focusTag"), R["atLanding"].get("focusType"))
        return R
    # ★ 自证「这一格与 body 那一格**不是同一格**」：非输入框的两臂里，
    #   `tree` 与 `deskButton` 都必须真的把焦点放在一个**具体的桌内元素**上；
    #   若实测焦点是 BODY ⟹ 它与 body 臂重复 ⟹ 记为无效而不是当成两格。
    R["landingIsDistinct"] = bool(
        R["atLanding"].get("focusTag")
        and R["atLanding"].get("focusTag") != "BODY")
    if landing in ("tree", "deskButton") and not R["landingIsDistinct"]:
        R["FAILED"] = ("★ 落点不可聚焦（焦点掉到 BODY）⟹ 与 body 臂**是同一格**，"
                       "不能当成两格报")
    pg.keyboard.press("Meta+z")
    pg.wait_for_timeout(SETTLE + 200)
    ids2 = (pg.evaluate(A.TREE) or {}).get("objectIds") or []
    R["afterUndo"] = pg.evaluate(STATE)
    R["objectsAfterUndo"] = len(ids2)
    R["mugBack"] = MUG in ids2
    R["undone"] = R["mugBack"]
    return R


def run_census(pg, R):
    """普查：**删除入口**全清单 + **有没有任何删除/撤销提示**。

    ★ 普查也必须自证：「没找到提示」必须能区分
      「桌里确实没有」与「我没找到那些元素」⟹ 所以先证明桌在、
      再证明提示区**存在但为空**（而不是压根没渲染）。
    """
    R["census"] = {}
    ok, why = _selfcheck(pg)
    if not ok:
        R["census"] = {"FAILED": why}
        return
    A.click_tree_row(pg, CAM)
    A.settle(pg)
    c = pg.evaluate("""()=>{const d=document.querySelector(
        '[role="dialog"][aria-modal="true"]');
      if(!d) return {err:'no desk'};
      const at=(s)=>d.querySelectorAll(s).length;
      return {deskOk:true,
        rowDelete:at('[data-director-delete-object]'),
        selToolbarDelete:at('[data-director-selection-action="delete"]'),
        treeCtxMenu:at('[data-director-tree-context-menu]'),
        treeCtxActions:at('[data-director-tree-context-action]'),
        liveRegions:at('[role="status"],[role="alert"],[aria-live]'),
        liveWithText:[...d.querySelectorAll('[role="status"],[role="alert"],[aria-live]')]
          .map(e=>(e.textContent||'').trim()).filter(Boolean),
        undoish:[...d.querySelectorAll('button,a,[role="button"]')].filter(e=>
          /撤销|还原|恢复|已删除|重新添加/.test((e.textContent||'')
            +(e.getAttribute('aria-label')||'')+(e.getAttribute('title')||'')))
          .map(e=>(e.getAttribute('aria-label')||e.textContent||'').trim().slice(0,14)),
        feedbackPanel: !!d.querySelector('[data-director-command-feedback], '
          +'[data-director-last-command]')};}""")
    R["census"] = c
    # ── 删除后**立刻**看有没有任何提示（这一格必须与撤销格分开读）
    before = pg.evaluate(STATE)
    ok, why = _delete_mug(pg)
    if not ok:
        R["feedback"] = {"FAILED": why}
        return
    pg.wait_for_timeout(400)
    R["feedback"] = {"before": before, "after": pg.evaluate(STATE)}


def run_persist(pg, R):
    """跨 reload 持久化 —— ★ **不能用 `fresh()`**（它会清 localStorage）。"""
    ok, why = _selfcheck(pg)
    if not ok:
        R["persist"] = {"FAILED": why}
        return
    A.click_tree_row(pg, CAM)
    A.settle(pg)
    ok, why = _delete_mug(pg)
    if not ok:
        R["persist"] = {"FAILED": why}
        return
    ids = (pg.evaluate(A.TREE) or {}).get("objectIds") or []
    R["persist"] = {"beforeReload": {"n": len(ids), "mug": MUG in ids},
                    "state": pg.evaluate(STATE)}
    pg.evaluate("()=>{window.location.reload();}")
    pg.wait_for_timeout(3000)
    try:
        pg.wait_for_selector(".react-flow__node", timeout=25000)
    except Exception:  # noqa: BLE001
        R["persist"]["FAILED"] = "reload 后画布没回来"
        return
    s = pg.evaluate(OPEN_DESK)
    if not s.get("pt"):
        R["persist"]["FAILED"] = "reload 后开桌按钮点不动"
        return
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(2500)
    ids2 = (pg.evaluate(A.TREE) or {}).get("objectIds") or []
    R["persist"]["afterReload"] = {"n": len(ids2), "mug": MUG in ids2,
                                   "state": pg.evaluate(STATE)}


def run_round(pg, R):
    R["rows"] = []
    R["census"] = {}
    R["feedback"] = {}
    R["persist"] = {}
    run_census(pg, R)
    for landing in ("fovInput", "tree", "body", "deskButton"):
        r, tries = None, 0
        while tries < MAX_TRIES:
            tries += 1
            try:
                r = run_cell(pg, landing)
            except Exception as e:  # noqa: BLE001
                r = {"landing": landing,
                     "FAILED": "%s: %s" % (type(e).__name__, str(e)[:150])}
            if not r.get("FAILED"):
                break
            pg.wait_for_timeout(900 * tries)
        r["tries"] = tries
        if tries > 1:
            r["retried"] = True
        R["rows"].append(r)
    run_persist(pg, R)


def summarize(R):
    c = R.get("census") or {}
    if c.get("FAILED"):
        print("  普查 FAILED: %s" % c["FAILED"])
    else:
        print("  普查：按行删除 %d 个｜选择工具条删除 %d 个｜树右键菜单 %d 个"
              "（动作 %d）｜live 区 %d 个（其中有文字 %d）｜撤销类控件 %d 个 %r"
              % (c.get("rowDelete", 0), c.get("selToolbarDelete", 0),
                 c.get("treeCtxMenu", 0), c.get("treeCtxActions", 0),
                 c.get("liveRegions", 0), len(c.get("liveWithText") or []),
                 len(c.get("undoish") or []), c.get("undoish") or []))
    for r in R.get("rows") or []:
        if r.get("FAILED"):
            print("   %-10s FAILED(试 %s): %s" % (r["landing"], r.get("tries"),
                                                 r["FAILED"][:52]))
            continue
        print("   %-10s 删后 past=%-2s 焦点=%-6s(输入框=%-5s) → Cmd+Z: "
              "道具回来=%-5s past=%-2s future=%-2s"
              % (r["landing"], (r.get("afterDelete") or {}).get("past"),
                 (r.get("atLanding") or {}).get("focusTag"),
                 (r.get("atLanding") or {}).get("focusInInput"),
                 r.get("mugBack"), (r.get("afterUndo") or {}).get("past"),
                 (r.get("afterUndo") or {}).get("future")))
    f = R.get("feedback") or {}
    if f.get("after"):
        print("  删除后的提示：live=%r 撤销类控件=%d（%r）"
              % (f["after"].get("liveTexts"), f["after"].get("undoishCount"),
                 f["after"].get("undoishLabels")))
    p = R.get("persist") or {}
    if p.get("afterReload"):
        print("  跨 reload：删后 %d 个 → reload 后 %d 个，道具还在=%s，past=%s"
              % (p["beforeReload"]["n"], p["afterReload"]["n"],
                 p["afterReload"]["mug"], p["afterReload"]["state"].get("past")))
    elif p.get("FAILED"):
        print("  跨 reload FAILED: %s" % p["FAILED"])


def main():
    res = {"batch": 777, "probe": "a",
           "question": "「导演台删除破坏性且跨 reload 持久化，却无『未保存/重置』提示」"
                       "—— 这句捆了三件事，本批把它们拆开测",
           "whyItMatters": "★ 「不可逆」与「无入口」是两种严重度完全不同的缺陷。"
                           "把它们捆成一句，会让「可撤销」成立时把「无提示」"
                           "一起放过 —— 而**用户看不到出路，不等于出路不存在**。",
           "landingRule": "★ **落点必须在删除之后设置**。第一版把落点设在删除"
                          "**之前** ⟹ 删除动作自己把焦点移走了；第二版删掉的"
                          "就是选中对象 ⟹ 检查器字段随之消失。⟹ 第三版改用"
                          "**按行删除按钮**（`stopPropagation()` ⟹ 不改选中）"
                          "⟹ 相机 FOV 滑杆在删除后仍在屏上。",
           "readings": "★ 可撤销性取**用户可见**后果（对象是否回来、"
                       "`history-future`）；`history-past` 用**属性名**读"
                       "（第一版把选择器传进 `getAttribute` ⟹ 永远读到空串，"
                       "而空串看起来像「历史是空的」）。"
                       "★ 跨 reload 持久化**不能用 `fresh()`** —— 它清 localStorage，"
                       "那测的是另一件事。",
           "feedbackSurface": "桌里有**常驻命令反馈面板**（`DirectorDesk.tsx:1008`），"
                              "而 `getDirectorCommandFeedback` 对 `COMMITTED` "
                              "返回 `null` ⟹ 成功删除后它显示占位文案「无命令反馈」。",
           "rounds": []}
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
