#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 776 探针 A —— **「D1 的两处必须一起改」这个断言成立吗？**

## 为什么验一句**挂在拍板项里**的话

763 挂起的第一优先项写的是：

> `useDirectorGestureBoundary` 的 Escape 分支加 `if (!activeRef.current) return;`
> + `onFocus` 不再 `begin()` —— **两处必须一起改**

这句话是整个 D1 修法的**授权依据**，却**从来没有证据**。它由两条推论组成：

- **推论一**：方向 (a)（Escape 加 `activeRef` 守卫）单独改是**空操作**。
  理由是 `onFocus: begin` ⟹ 焦点一落手势就 active ⟹ 守卫恒不触发。
- **推论二**：方向 (b)（`onFocus` 不再 `begin`）单独改也是**空操作**。
  理由是 `onKeyDown` 的 Escape 分支（`:93-98`）**无条件**
  `preventDefault()` + `stopPropagation()` ⟹ 桌的 window 阶梯永远看不到 Escape。

两条都成立才需要「一起改」。**任一条被否证，授权范围就能缩小** ——
这是能在动 `src/` 之前把这条拍板项从「信我」变成「有读数」的唯一办法。
本批**不注入、不改 `src/`**：两条推论都可以**从现码直接测出来**。

## 关键：推论二可以**不用注入**就证出来

Escape 分支调 `cancel()`（`:96`）会把活动手势清掉，**但焦点不动**。
于是「**第一次 Escape 之后**」正好落在

> 焦点仍在 gesture 控件上、但 `activeGesture` 已为空

这个状态 —— 而它**正是拟议修法 (a) 会放行的状态**。
所以本实验的第 2、第 3 次按压，**所处的世界就是「方向 (b) 单独改」的世界**
（永远没有活动手势）。若那两次按压什么都没做 ⟹ **(b) 单独改是空操作**，
而且是**直接观测**，不是推理。

## 同一批读数还顺带否证了推论一

第 1 次 Escape 之后的状态既已可达且「无手势」，则修法 (a) 的守卫**会**放行
⟹ (a) 单独改**不是**空操作，它把「按 N 次都不生效的死键」变成「按第 2 次生效」。
⟹ **「两处必须一起改」作为授权依据不成立。**

## 读数为什么不被污染

1. **手势状态用只读属性读**：`DirectorDesk.tsx:889` 的
   `data-director-active-gesture={history.activeGesture?.gestureId ?? ""}`
   —— 桌根上直接暴露，**不需要改 `src/` 也不需要 store 句柄**。
2. ★ **聚焦后必须等 React 重渲染再读**（`wait 450ms`）。第一版在同一次
   `evaluate` 里 `.focus()` 完立刻读属性 ⟹ 读到**更新前**的值 ⟹
   「onFocus 不起手势」—— 差一步就把拍板项的理由给否了。
   **`.focus()` 是同步的，React 更新不是。**
3. **用户可见的后果是主读数**，不是 `defaultPrevented`：
   字段的 React handler 会 `stopPropagation()` ⟹ 挂在 window 的间谍
   **收不到事件** ⟹ `dp` 读不出来（**「读不到」本身是证据**，R100 同族）。
   所以主读数取「导出面板有没有关」「桌有没有关」。
4. **对照臂必须落在真的能聚焦、且不挂 gesture handler 的元素上**：
   桌内 `[data-director-panels-toggle]`（116 个候选之一）。
   第一版对照臂用 `[data-director-tree]`，`isActive: False` —— 焦点压根没落上，
   那样只证明了「阶梯在工作」，**没有证明「焦点位置是自变量」**。
5. 每个 gesture 格都**自证落点**：`focusOk`（焦点确实在目标元素上）
   与 `gestureBefore`（聚焦前手势为空）都记进 raw。

## 格子

| 上下文 | 前置 | 族 | 元素 | `input type` |
| --- | --- | --- | --- | --- |
| 道具 | 默认标签页 | `xf` | 首、末（9 个中） | number |
| 角色 | **切到「姿势」标签页** | `xf` | 首、末 | number |
| 角色 | **切到「姿势」标签页** | `pose` | 首、末 | range |
| 相机 | 默认标签页 | `xf` | 首、末（**12** 个中） | number |
| 相机 | 默认标签页 | `fov` | 单个 | range |
| 相机 | **先点预设路径造一条** | `panchor` | 首、末 | number |
| 相机 | **先点预设路径造一条** | `ptransform` | 首、末 | number |
| 桌内 | —— | 对照（非 gesture） | 1 | —— |

★ **「前置」这一列是本批抓到的自己的错**（775 的 R104 在本批复现）：
  第一版只在三个**默认**上下文里枚举 ⟹ `pose` 与两族路径控件**全记成 0**，
  读起来像「这三族不存在」，而真实原因是**姿态面板卡在 `characterTab === "pose"`
  后面**（`DirectorInspector.tsx:2339`）、**路径控件是 `paths.map` 逐条渲染**
  （`:1041`/`:1173`，相机没有路径就没有控件）。
  **「少测」与「不存在」在产物里长得一模一样** ⟹ 现在把前置做到位，
  并且把「开了前置仍是 0」单独记成一条 `FAILED` 而不是悄悄跳过。
## 探针教训（本批抓自己的）

- **R111** —— ★**同步的 `.focus()` 之后必须等 React 重渲染再读 DOM 属性。**
  第一版在同一次 `evaluate` 里 `.focus()` 完立刻读
  `data-director-active-gesture` ⟹ 读到**更新前**的值 ⟹ 得出
  「`onFocus` 不起手势」—— 差一步就把 D1 拍板项的**理由**给否了。
  **「看起来是机制发现」的第一嫌疑，应当是自己的测量时序。**
- **R112** —— ★**「少测」与「不存在」在产物里长得一模一样**（775 的 R104 在本批复现）。
  姿态族与两族路径控件原本**全记成 0**，而真实原因是它们分别卡在
  `characterTab === "pose"`（`DirectorInspector.tsx:2339`）、`paths.map`
  （`:1041`）与 `selectedAnchor.type !== "vertex"`（`:1189`）后面。
  补上前置后：姿态 **25** 个、路径变换 **9** 个、路径锚点 **6** 个 ——
  **代价是 31 个被我差点记成「不存在」的控件。**
- **R113** —— ★**「点不动」是个没有鉴别力的失败信息**。本批连踩三次：
  ① 拿**菜单面板**的选择器当**触发器**（真触发器是时间轴的
  `[data-director-track-draw-trail]`，`DirectorTimeline.tsx:1677`）；
  ② `SCAN_CLICK` **不滚动** ⟹ 元素在检查器的 `overflow-y-auto` 折叠区外就点不到；
  ③ 锚点类型按钮的取值我**猜**成 `smooth`，而源码里是
  `vertex`/`symmetric`/`asymmetric`（`:1141-1144`）。
  三次都表现为同一句话「点不动」，而三个原因完全不同。
- **R114** —— ★**`if not x != "true"` 是优先级陷阱**：Python 里**比较先于 `not`**，
  于是 `if not x != "true"` 解析成 `if (not x) != "true"` ⟹ **成功反而报错**。
  它的可怕之处在于「手动复现成功、函数却报失败」，两者不一致时
  **先怀疑判据，再怀疑机制**。
"""
import json
import pathlib
import sys
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
# ★ 跨批 import 774 的探针基础设施（桌的开启/对象树点击/间谍/扫描点击），
#   不是抄一份 —— 抄一份的话任何改动都会让跨批对比悄悄失去前提。
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch774-2026-10-01" / "probes"))
import dbg774a as A  # noqa: E402

OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/research/"
    "liblib-canvas-batch776-2026-10-01/raw/vb776a.json")

PRESSES = 3
MAX_TRIES = 3
#: 聚焦后等 React 重渲染的时长。★ 不可省（见文件头第 2 条）。
SETTLE_FOCUS_MS = 450
#: 每次按压后的观察间隔
SETTLE_KEY_MS = 550

#: 五族 —— `data-*` 归属与 `input type` 全部**从源码现读**：
#:   `useDirectorGestureBoundary` 的 5 个 `{...gesture}` 展开处
#:   DirectorInspector.tsx :183(number) :838(number) :894(number)
#:                          :1361(range)  :1655(range)
FAMILIES = [
    ("xf", "[data-director-transform-field]", "number"),
    ("panchor", "[data-director-path-anchor-handle-axis]", "number"),
    ("ptransform", "[data-director-path-transform-axis]", "number"),
    ("pose", "[data-director-pose-control]", "range"),
    ("fov", "[data-director-camera-fov]", "range"),
]

CONTEXTS = [
    ("prop", "director-prop-mug", None),
    ("character", "director-character-lead", None),
    # 角色要切到「姿势」标签页，否则 `pose` 族是 0（CharacterPoseInspector
    # 卡在 `characterTab === "pose"`，DirectorInspector.tsx:2339）
    ("character-pose", "director-character-lead", "pose"),
    ("camera", A.CAM, None),
    # 路径族卡在**运动路径数据**上：PathTransformFields/PathTupleFields 是
    # `paths.map` 逐条渲染（:1041/:1173）⟹ 相机没有路径就没有控件。
    # 所以先点预设路径造一条（`createMotionPath`，DirectorTimeline.tsx:1575）。
    ("camera-path", A.CAM, "__makepath__"),
]

#: 预设路径的按钮（一次点击即 `createMotionPath(preset)`）
PATH_PRESET_SEL = '[data-director-motion-path-preset="line"]'
#: ★ 打开路径菜单的**触发器**是时间轴上那个「绘制轨迹」按钮
#:   （`togglePathMenu`，DirectorTimeline.tsx:601；按钮在 :1677），
#:   **不是**菜单面板自己 `[data-director-motion-path-menu]`。
#:   第一版拿面板当触发器 ⟹ 「点不动」—— 而「点不动」长得像「这条路走不通」。
PATHMENU_TRIGGER = '[data-director-track-draw-trail]'

#: 对照臂：桌内、真的能聚焦、**不挂** gesture handler 的元素
CONTROL_SEL = "[data-director-panels-toggle]"

GESTURE = """()=>{const d=document.querySelector('[data-director-active-gesture]');
  return d? (d.getAttribute('data-director-active-gesture') || '') : null;}"""

EXPORT_TRIGGER = """()=>{const t=document.querySelector('[data-director-export-trigger]');
  if(!t) return {err:'no trigger'};
  if(t.disabled) return {err:'disabled'};
  const r=t.getBoundingClientRect();
  return {pt:[r.x+r.width/2, r.y+r.height/2]};}"""

EXPORT_STATE = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
  return {present: !!(d && d.querySelector('[data-director-export-panel]'))};}"""

CENSUS = """(fams)=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
  if(!d) return {err:'no desk'};
  const out=[];
  for(const [id,sel,want] of fams){
    const els=[...d.querySelectorAll(sel)];
    const live=els.filter(e=>!e.disabled);
    const first=live[0]||null;
    out.push({id:id, total:els.length, live:live.length,
      type: first? first.getAttribute('type') : null, wantType:want,
      hasRect: !!(first && first.getBoundingClientRect().width>0
                  && first.getBoundingClientRect().height>0)});}
  return out;}"""

FOCUS = """(sel)=>{const e=document.querySelector(sel);
  if(!e) return {err:'no el'};
  if(e.disabled) return {err:'disabled'};
  let ok=false;
  try{ e.focus({preventScroll:true}); ok=document.activeElement===e; }catch(err){
    return {err:'focus threw: '+err};}
  return {ok:ok, type:e.getAttribute('type')};}"""

FOCUS_NTH = """(a)=>{const [sel,n]=a;
  const d=document.querySelector('[role="dialog"][aria-modal="true"]');
  if(!d) return {err:'no desk'};
  const live=[...d.querySelectorAll(sel)].filter(e=>!e.disabled);
  const e=live[n]; if(!e) return {err:'no live el at '+n, liveN:live.length};
  let ok=false; try{ e.focus({preventScroll:true});
    ok=document.activeElement===e; }catch(err){ return {err:'threw'};}
  return {ok:ok, idx:n, liveN:live.length, type:e.getAttribute('type'),
    isGestureFamily:true};}"""


def _goto_tab(pg, tab):
    """切到指定标签页。返回 (ok, 说明)。

    ★ 这一步是**775 的 R104** 在本批的复现：姿态族原本记成 0，
      读起来像「这一族不存在」，而真实原因是**我没开那个标签页**。
      **「少测」和「不存在」在产物里长得一模一样。**
    """
    if not tab:
        return True, "默认标签页"
    d = pg.evaluate("""(tab)=>{const b=document.querySelector(
        '[data-director-character-tab="'+tab+'"]'); return !!b;}""", tab)
    if not d:
        return False, "找不到角色标签页 %r" % tab
    s = pg.evaluate(A.SCAN_CLICK, '[data-director-character-tab="%s"]' % tab)
    if not s.get("pt"):
        return False, "角色标签页 %r 点不动" % tab
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(600)
    on = pg.evaluate("""(tab)=>{const b=document.querySelector(
        '[data-director-character-tab="'+tab+'"]');
        return b? b.getAttribute('aria-pressed') : null;}""", tab)
    return (on == "true"), "aria-pressed=%r" % on


def _make_path(pg):
    """用预设路径造一条运动路径，让路径族控件有数据可渲染。

    ★ 造路径是**建数据**，不是「点提交」—— 边界里禁的是付费/真实生图生视频，
      这里只是在本地项目里加一条路径，而 `fresh()` 每格开头会清 localStorage。
    """
    s = pg.evaluate(A.SCAN_CLICK, PATHMENU_TRIGGER)
    if not s.get("pt"):
        return False, "路径菜单触发器点不动（时间轴上没找到「绘制轨迹」）"
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(600)
    # 自证菜单真的开了 —— 否则下一步的「预设按钮点不动」会被误读成
    # 「按钮不存在」，而真实原因是「菜单没开」
    if not pg.evaluate("""()=>!!document.querySelector(
        '[data-director-motion-path-menu]');"""):
        return False, "点了触发器但路径菜单没开（cameraFollowActive 会让 toggle 早退）"
    p = pg.evaluate(A.SCAN_CLICK, PATH_PRESET_SEL)
    if not p.get("pt"):
        return False, "预设路径按钮点不动（菜单没开？）"
    pg.mouse.click(p["pt"][0], p["pt"][1])
    pg.wait_for_timeout(800)
    return True, "已点预设路径 line"


def _selfcheck(pg, ctx, oid, tab):
    """桌开 + 选中落位 + 标签页/路径数据就位。返回 (ok, 失败原因)。"""
    r = A.fresh(pg)
    if r.get("FAILED"):
        return False, "导演台没开"
    if oid:
        A.click_tree_row(pg, oid)
        A.settle(pg)
        sel = (pg.evaluate(A.TREE) or {}).get("selectedIds") or []
        if oid not in sel:
            return False, "选中没落在 %s（实为 %r）" % (oid, sel)
    if tab == "__makepath__":
        ok, why = _make_path(pg)
        if not ok:
            return False, "造不出运动路径：%s" % why
        # 锚点族（`PathTupleFields`，:1173）还多一道前置：必须**选中一个锚点**
        # （`:1134` 的 `{selectedAnchor ? …}`）⟹ 点属性页锚点列表里的第一项。
        # ★ `SCAN_CLICK` **不滚动**（它要求 `elementFromPoint` 命中），
        #   而锚点列表在检查器的 `overflow-y-auto` 里常常在折叠区外 ⟹
        #   不先 `scrollIntoView` 就会得到「点不到」，而「点不到」
        #   长得像「这条路走不通」。
        pg.evaluate("""()=>{const e=document.querySelector(
            '[data-director-path-anchor-list]');
          if(e) e.scrollIntoView({block:'center'});}""")
        pg.wait_for_timeout(350)
        n_opt = pg.evaluate("""()=>{const l=document.querySelector(
            '[data-director-path-anchor-list]');
          return l? l.querySelectorAll('[data-director-path-anchor-option]').length : -1;}""")
        if n_opt <= 0:
            return False, ("路径造出来了，但锚点列表里没有可选项（实测 %d 个）"
                           % n_opt)
        a = pg.evaluate(A.SCAN_CLICK,
                        '[data-director-path-anchor-list] '
                        '[data-director-path-anchor-option]')
        if not a.get("pt"):
            return False, ("锚点列表里有 %d 项但点不到（多半是没滚进视野，"
                           "SCAN_CLICK 不滚动）" % n_opt)
        pg.mouse.click(a["pt"][0], a["pt"][1])
        pg.wait_for_timeout(600)
        if not pg.evaluate("""()=>!![...document.querySelectorAll(
            '[data-director-path-anchor-option]')]
            .find(b=>b.getAttribute('aria-pressed')==='true');"""):
            return False, "点了锚点但 aria-pressed 没变（锚点没被选中）"
        # ★ 还要再切**锚点类型**：handle 那两支的门槛是
        #   `selectedAnchor.type !== "vertex"`（:1189），而默认类型就是 vertex
        #   ⟹ 不切类型，`kind="handle"` 的 PathTupleFields 根本不渲染（:1191/:1207）。
        pg.evaluate("""()=>{const e=document.querySelector(
            '[data-director-path-anchor-type-option="symmetric"]');
          if(e) e.scrollIntoView({block:'center'});}""")
        pg.wait_for_timeout(300)
        t = pg.evaluate(A.SCAN_CLICK,
                        '[data-director-path-anchor-type-option="symmetric"]')
        if not t.get("pt"):
            return False, "锚点类型按钮点不到（多半是没滚进视野）"
        pg.mouse.click(t["pt"][0], t["pt"][1])
        pg.wait_for_timeout(600)
        # ★ 括号不能省：Python 里**比较先于 not**，
        #   `if not x != "true"` 会被解析成 `if (not x) != "true"` ——
        #   于是「成功」（x == "true" ⟹ not x 为 False）反而走进错误分支。
        #   第一版就写成 `not ... !=`，结果手动复现成功、函数却报失败。
        pressed = pg.evaluate("""()=>{const b=document.querySelector(
            '[data-director-path-anchor-type-option="symmetric"]');
          return b? b.getAttribute('aria-pressed') : null;}""")
        if pressed != "true":
            return False, "点了锚点类型但 aria-pressed=%r" % pressed
        n_pan = pg.evaluate("""()=>document.querySelectorAll(
            '[data-director-path-anchor-handle-axis]').length;""")
        if n_pan == 0:
            return False, "锚点类型已切但 panchor 仍 0 个控件"
    else:
        ok, why = _goto_tab(pg, tab)
        if not ok:
            return False, why
    g = pg.evaluate(GESTURE)
    if g is None:
        return False, "桌根没有 data-director-active-gesture（读数方法不成立）"
    if g != "":
        return False, "起始手势非空（%r）—— 本格不是干净起点" % g[:14]
    return True, None


def run_cell(pg, ctx, oid, tab, fam, sel, nth, is_control):
    """一格：开导出面板 → 聚焦目标 → 连按 Escape ×3 → 每次记三个读数。"""
    R = {"ctx": ctx, "family": fam, "nth": nth, "isControl": bool(is_control)}
    ok, why = _selfcheck(pg, ctx, oid, tab)
    if not ok:
        R["FAILED"] = why
        return R
    e = pg.evaluate(EXPORT_TRIGGER)
    if not e.get("pt"):
        R["FAILED"] = "导出触发器打不开：%s" % e.get("err")
        return R
    pg.mouse.click(e["pt"][0], e["pt"][1])
    pg.wait_for_timeout(700)
    R["exportOpenBefore"] = pg.evaluate(EXPORT_STATE).get("present")
    if not R["exportOpenBefore"]:
        R["FAILED"] = "点了但导出面板没出现"
        return R
    R["gestureBeforeFocus"] = pg.evaluate(GESTURE)
    f = (pg.evaluate(FOCUS, CONTROL_SEL) if is_control
         else pg.evaluate(FOCUS_NTH, [sel, nth]))
    R["focus"] = f
    if f.get("err"):
        R["FAILED"] = "聚焦失败：%s" % f["err"]
        return R
    if not f.get("ok"):
        R["FAILED"] = "★ 焦点没落在目标元素上 —— 这一格不是有效读数"
        return R
    pg.wait_for_timeout(SETTLE_FOCUS_MS)          # ★ 等 React 重渲染
    R["gestureAfterFocus"] = pg.evaluate(GESTURE)
    R["isGestureElement"] = (R["gestureAfterFocus"] != "")
    R["presses"] = []
    for i in range(1, PRESSES + 1):
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(SETTLE_KEY_MS)
        st = pg.evaluate(EXPORT_STATE)
        desk = pg.evaluate(A.DESK)
        focusStill = pg.evaluate(
            """(a)=>{const [sel,n,ctl]=a;
               const d=document.querySelector('[role="dialog"][aria-modal="true"]');
               if(!d) return null;
               const e= ctl ? d.querySelector(sel)
                 : [...d.querySelectorAll(sel)].filter(x=>!x.disabled)[n];
               return e? document.activeElement===e : null;}""",
            [CONTROL_SEL if is_control else sel, nth, is_control])
        R["presses"].append({
            "n": i, "gesture": pg.evaluate(GESTURE),
            "exportPresent": st.get("present"), "deskOpen": desk.get("open"),
            "focusStill": focusStill})
    return R


def run_census(pg, R):
    """普查：**每个上下文都把标签页与路径数据开到位**再枚举五族。

    ★ 第一版只在三个默认上下文里枚举 ⟹ `pose`/两族路径控件全记成 0，
      而它们其实是**标签页/数据**后面着的（R104）。**「少测」与「不存在」
      在产物里长得一模一样** ⟹ 这里把前置做到位，并把「0 个」与
      「开了前置仍是 0 个」分开记（`precondition` 字段）。
    """
    R["census"] = []
    for ctx, oid, tab in CONTEXTS:
        ok, why = _selfcheck(pg, ctx, oid, tab)
        if not ok:
            R["census"].append({"ctx": ctx, "precondition": tab or "default",
                                "FAILED": why})
            continue
        rows = pg.evaluate(CENSUS, [[i, s, t] for i, s, t in FAMILIES])
        for row in rows:
            row["ctx"] = ctx
            row["precondition"] = tab or "default"
            # ★ 「没找到」要能区分「族不存在」与「我找错了地方」：
            #   存在 ⟹ 必须自证有面积、类型与源码一致；0 个 ⟹ 记 0 但**不静默跳过**。
            row["selfJustified"] = bool(
                row["live"] == 0
                or (row["hasRect"] and row["type"] == row["wantType"]))
            R["census"].append(row)


def run_round(pg, R):
    R["rows"] = []
    R["census"] = []
    run_census(pg, R)
    live = {}

    def count(sel):
        if sel not in live:
            live[sel] = pg.evaluate(
                """(sel)=>{const d=document.querySelector(
                     '[role="dialog"][aria-modal="true"]');
                   return d? [...d.querySelectorAll(sel)].filter(e=>!e.disabled).length : 0;}""",
                sel)
        return live[sel]

    XF = "[data-director-transform-field]"
    plan = []
    for ctx, oid, tab in CONTEXTS:
        if ctx == "prop":
            plan.append((ctx, oid, tab, "xf", XF))
        elif ctx == "camera":
            plan.append((ctx, oid, tab, "xf", XF))
            plan.append((ctx, oid, tab, "fov", "[data-director-camera-fov]"))
        elif ctx == "character-pose":
            plan.append((ctx, oid, tab, "pose", "[data-director-pose-control]"))
        elif ctx == "camera-path":
            plan.append((ctx, oid, tab, "panchor",
                         "[data-director-path-anchor-handle-axis]"))
            plan.append((ctx, oid, tab, "ptransform",
                         "[data-director-path-transform-axis]"))
    rows = []
    for ctx, oid, tab, fam, sel in plan:
        ok, why = _selfcheck(pg, ctx, oid, tab)
        n = count(sel) if ok else 0
        if not ok:
            rows.append({"ctx": ctx, "family": fam, "nth": 0,
                         "isControl": False, "FAILED": why, "tries": 1})
            continue
        if n == 0:
            rows.append({"ctx": ctx, "family": fam, "nth": 0,
                         "isControl": False, "tries": 1,
                         "FAILED": "开了前置（%s）后该族仍 0 个 —— "
                                   "记为未到达，不静默跳过" % (tab or "default")})
            continue
        # 取首、末两个可用元素：只测首个会漏掉「只有某些轴挂了 handler」
        for nth in sorted({0, n - 1}):
            r, tries = None, 0
            while tries < MAX_TRIES:
                tries += 1
                try:
                    r = run_cell(pg, ctx, oid, tab, fam, sel, nth, False)
                except Exception as e:  # noqa: BLE001
                    r = {"ctx": ctx, "family": fam, "nth": nth,
                         "isControl": False,
                         "FAILED": "%s: %s" % (type(e).__name__, str(e)[:150])}
                if not r.get("FAILED"):
                    break
                pg.wait_for_timeout(900 * tries)
            r["tries"] = tries
            if tries > 1:
                r["retried"] = True
            rows.append(r)
    r, tries = None, 0
    while tries < MAX_TRIES:
        tries += 1
        try:
            r = run_cell(pg, "desk", None, None, "control", CONTROL_SEL, 0, True)
        except Exception as e:  # noqa: BLE001
            r = {"ctx": "desk", "family": "control", "nth": 0,
                 "isControl": True,
                 "FAILED": "%s: %s" % (type(e).__name__, str(e)[:150])}
        if not r.get("FAILED"):
            break
        pg.wait_for_timeout(900 * tries)
    r["tries"] = tries
    if tries > 1:
        r["retried"] = True
    rows.append(r)
    R["rows"] = rows


def summarize(R):
    print("  普查：")
    for c in R.get("census") or []:
        if c.get("FAILED"):
            print("   %-10s %s FAILED %s" % (c["ctx"], c.get("id", "—"),
                                              c["FAILED"]))
            continue
        print("   %-14s %-10s 前置=%-12s 共 %2d / 可用 %2d  type=%-7s 自证=%s"
              % (c["ctx"], c["id"], c.get("precondition", "?"),
                 c["total"], c["live"], c["type"], c["selfJustified"]))
    for r in R.get("rows") or []:
        tag = "对照" if r.get("isControl") else "实验"
        if r.get("FAILED"):
            print("   %s %-10s %-8s #%-2d FAILED(试 %s): %s"
                  % (tag, r["ctx"], r["family"], r["nth"], r.get("tries"),
                     r["FAILED"][:52]))
            continue
        ps = r.get("presses") or []
        seq = " | ".join(
            "手%s→%s/桌%s" % ("空" if not p["gesture"] else "有",
                             "开" if p["exportPresent"] else "关",
                             "开" if p["deskOpen"] else "关") for p in ps)
        print("   %s %-10s %-8s #%-2d 聚焦后手势=%-3s 落点ok=%-5s %s"
              % (tag, r["ctx"], r["family"], r["nth"],
                 "有" if r.get("isGestureElement") else "空",
                 (r.get("focus") or {}).get("ok"), seq))


def main():
    res = {"batch": 776, "probe": "a",
           "question": "拍板项 763 里的「D1 的两处必须一起改」这个断言成立吗？",
           "whyItMatters": "这句话是 D1 修法的**授权依据**，却从来没有证据。"
                           "它由两条推论组成：(a) Escape 加 activeRef 守卫、"
                           "(b) onFocus 不再 begin()。两条都成立才需要一起改，"
                           "**任一条被否证，授权范围就能缩小**。",
           "noInjection": "★ **本批没有任何注入**，也**没有改 src/**。两条推论"
                          "都能从现码直接测：Escape 分支的 cancel() 清手势却不动焦点，"
                          "于是「第一次 Escape 之后」就是「方向 (b) 单独改」的世界。",
           "readings": "手势状态用只读属性 `data-director-active-gesture`"
                       "（DirectorDesk.tsx:889）读；主读数是**用户可见的后果**"
                       "（导出面板/桌有没有关），不是 defaultPrevented —— "
                       "字段的 handler 会 stopPropagation，window 上的间谍**收不到**，"
                       "「读不到」本身是证据。",
           "landmarks": ["DirectorDesk.tsx:889 只读手势属性",
                         "useDirectorGestureBoundary.ts:79 onFocus: begin",
                         "useDirectorGestureBoundary.ts:92-98 Escape 分支无条件吞键",
                         "useDirectorGestureBoundary.ts:82-90 onPointerUp 对 number 提前 return",
                         "directorStore.ts:3580-3592 begin 成功返回 COMMITTED"],
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
